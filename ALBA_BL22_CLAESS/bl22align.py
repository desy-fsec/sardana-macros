import ConfigParser
from sardana.macroserver.macro import Macro, Type
import time

BL_ENERGY_CONFIG = {'2.4keV': 'en < 5.6 and en >= 2.4',
                    '5.6keV': 'en < 7.6 and en >= 5.6',
                    '7.6keV' : 'en < 14 and en >= 7.6' ,
                    '14keV': 'en < 35 and en >= 14',
                    '35keV': 'en < 62.5 and en >=35'}

CLEAR_111_ENERGY_CONFIG = {'6keV': 'en <= 13 and en >= 6'}

CLEAR_311_ENERGY_CONFIG = {'6keV': 'en <= 14 and en >= 6.4'}

class ConfigAling(object):
    """
    Class Helper to read the configuration file.
    """

    def printConfig(self):
        equation = BL_ENERGY_CONFIG[self.config]
        self.output('Use the %r configuration: (%r)' % (self.config, equation))
        
    def initConfig(self, energy, config_range, config_path):
        self.config_file = ConfigParser.RawConfigParser()
        self.config_file.read(config_path)
        self.config_path = config_path
        

        try:
            self.energy =  energy / 1000.0 # to use keV
        except Exception as e:
            raise ValueError('The energy should be: clear or a number')

        if self.energy > 62.5 or self.energy < 2.4:
            msg = 'Value out of range [2400, 62500]'
            raise ValueError(msg)
        for configuration, equation in config_range.items():
            if eval(equation,{'en': self.energy}):
                self.config = configuration
                break
        else:
            msg = 'There is not configuration for this energy'
            raise ValueError(msg)

        self.motors_cal = self._tolist(self.config_file.get('general',
                                                            'equation'))
        
    def _tolist(self, data):
        data = data.replace('\n', ' ')
        data = data.replace(',', ' ')
        return data.split()

    def get_cmds_mov(self, instrument):
        cmds = []
        cmd = 'mv'
        motors = self.get_motors(instrument)
        all_motors = self.config_file.get(instrument, 'all') == 'True'

        for motor in motors:
            pos = self.config_file.get(self.config, motor)
            if motor in self.motors_cal:
                equation = pos
                if motor == 'oh_dcm_xtal2_pitch':
                    pos = self.calc_xtal2_pitch()
                else:
                    pos = eval(equation,{'en': self.energy})
            cmd += ' %s %s' % (motor, pos)
            if not all_motors:
                cmds.append(cmd)
                cmd = 'mv'
        if all_motors:
            cmds.append(cmd)
        return cmds

    def calc_xtal2_pitch(self):
        equation = self.config_file.get(self.config, 'oh_dcm_xtal2_pitch')
        d = float(self.config_file.get(self.config, 'xtal2_pitch_d'))
        pos = eval(equation, {'en': self.energy, 'd': d})
        return pos

    def save_xtal2_pitch(self):
        old_pos = self.calc_xtal2_pitch()
        dev = self.getDevice('oh_dcm_xtal2_pitch')
        new_pos = dev.read_attribute('position').value
        new_d = new_pos - old_pos
        self.config_file.set(self.config, 'xtal2_pitch_d', new_d)


    def get_motors(self, instrument):
        return self._tolist(self.config_file.get(instrument, 'motors'))

    def get_instruments(self):
        return self._tolist(self.config_file.get('general','instruments'))

    def get_element(self, element):
        return self.config_file.get(self.config, element)

    def get_ioregisters(self):
        return self._tolist(self.config_file.get('general','ioregisters'))
        
    def save_file(self, filename):
        """
        :param filename: New file name to save the current configuration.
        """
        with open(filename,'w') as f:
            self.config_file.write(f)

    def create_bkp(self):
        self.info('Creating backup file...')
        path, filename = self.config_path.rsplit('/', 1)
        t = '{0}/bkp_{1}_{2}'
        nfilename = t.format(path,time.strftime('%Y%m%d_%H%M%S'), filename)
        self.save_file(nfilename)
        self.info('Created file: %s' % nfilename)

    def update_config(self):
        self.create_bkp()
        self.info('Updating configuration....')
        ior = self.get_ioregisters()

        for element in self.config_file.options(self.config):
            if element == 'xtal2_pitch_d':
                continue
            if element in self.motors_cal:
                if element == 'oh_dcm_xtal2_pitch':
                    self.save_xtal2_pitch()
                continue
            if element in ior:
                attr = 'value'
            else:
                attr = 'position'
            dev = self.getDevice(element)
            rvalue = dev.read_attribute(attr).value
            self.config_file.set(self.config, element, rvalue)
        self.save_file(self.config_path)
        self.info(self.config_file.items(self.config))


class MoveBeamline(ConfigAling):
    """
    Class Helper to execute the flow of the movement of the beamline. 
    """
    
    energy_name = 'energy'
    
    def runMoveBeamline(self, energy, config_env, config_range, retries):
        try:
            config_path = self.getEnv(config_env)
            self.initConfig(energy, config_range, config_path)
            self.printConfig()
            self.execMacro('feclose')
            
            self.info('Configuring filters...')
            for ior in self.get_ioregisters():
                wvalue = int(self.get_element(ior))
                dev_ior = self.getDevice(ior)
                dev_ior.write_attribute('value', wvalue)
                for i in range(retries):
                    rvalue = dev_ior.read_attribute('value').value
                    time.sleep(5)
                    if rvalue == wvalue:
                        break
                else:
                    msg = 'Is was not possible to set the filter {0} to {1}'
                    self.error(msg.format(ior, wvalue))

            # Load motor position from the configuration except table_z
            self.info('Moving motors....')
            for instrument in self.get_instruments():
                if instrument in ['table_z','eh_slits']:
                    continue
                for cmd in self.get_cmds_mov(instrument):
                    for i in range(retries):
                        self.execMacro(cmd)

            # after the load config the energy is in keV
            eng = self.energy*1000.0 
            self.info('Moving energy to: %f' % eng)
            self.execMacro('mv energy %f' % eng)
            self.setEnv('LastBlConfig', self.config)
            try:
                self.execMacro('feopen')
            except:
                self.error('There was not possible to open de front end')

            self.info('Moving table_z....')
            for cmd in self.get_cmds_mov('table_z'):
                for i in range(retries):
                    self.execMacro(cmd)
            
            self.info('Moving eh_slits...')
            for cmd in self.get_cmds_mov('eh_slits'):
                for i in range(retries):
                    try:
                        self.execMacro(cmd)
                    except Exception as e:
                        self.error('Error with the eh_slit motor %s' % e)
            
        except Exception as e:
            self.error('Exception with alignment: %s' % e)

    def runSaveConfig(self, config_env, config_range):
        config_path = self.getEnv(config_env)
        mot_energy = self.getDevice(self.energy_name)
        energy = mot_energy.read_attribute('position').value
        self.info('Saving at %r eV' % energy)
        self.initConfig(energy, config_range, config_path)
        self.update_config()

    def runMoveMono(self, energy, config_env, config_range, retries):
        try:
            config_path = self.getEnv(config_env)
            self.initConfig(energy, config_range, config_path)
            last_config = self.getEnv('LastBlConfig')
            self.config = last_config
            self.printConfig()
            motors = self.get_motors('mono')
            self.info('Moving motors except oh_dcm_z and energy')
            for motor in motors:
                pos = self.config_file.get(self.config, motor)
                if motor in self.motors_cal:
                    equation = pos
                    if motor == 'oh_dcm_xtal2_pitch':
                        pos = self.calc_xtal2_pitch()
                    else:
                        pos = eval(equation,{'en': self.energy})
                if motor == 'oh_dcm_z':
                    new_dcm_z = pos
                    continue

                self.execMacro('mv %s %s' % (motor, pos))
            self.info('Moving oh_dcm_z and energy')
            dev = self.getDevice('oh_dcm_z')
            current_dcm_z = dev.read_attribute('position').value
            energy = self.energy*1000
            if current_dcm_z > new_dcm_z:
                cmd1 = 'mv energy %s' % energy
                cmd2 = 'mv oh_dcm_z %s' % new_dcm_z
            else:
                cmd1 = 'mv oh_dcm_z %s' % new_dcm_z
                cmd2 = 'mv energy %s' % energy

            self.execMacro(cmd1)
            self.execMacro(cmd2)

        except Exception as e:
            self.error('Exception with alignment: %s' % e)

class mvblE(Macro, MoveBeamline):
    """
    Macro to align the beamline to a specific energy. The macro move different
    elements: Monochromator, VFM, VCM, sample table, others.

    The macro need the an environment variable (BeamlineEnergyConfig) with
    the configuration of the beamline for different energies.
    """


    param_def = [['energy', Type.Float, None, 'Beamline energy in eV'],
                 ['retries', Type.Integer, 3, 
                  'Number of retries to move the motors']]

    
                   
    def run(self, energy, retries):
        self.info('Enter mvblE')
        self.runMoveBeamline(energy, 'BeamlineEnergyConfig', BL_ENERGY_CONFIG,
                             retries)


class mvE(Macro, MoveBeamline):
    """
    Macro to align the mono to a specific energy. The macro move different
    motor of the mono. The sign of the oh_dcm_z movement determines if the
    macro moves first the energy or the high of the mono.

    The macro need the an environment variable (BeamlineEnergyConfig) with
    the configuration of the beamline for different energies.
    """

    param_def = [['energy', Type.Float, None, 'Beamline energy in eV'],
                 ['retries', Type.Integer, 3,
                  'Number of retries to move the motors']]

    def run(self, energy, retries):
        self.info('Enter mvE')
        self.runMoveMono(energy, 'BeamlineEnergyConfig', BL_ENERGY_CONFIG,
                             retries)


class saveblE(Macro, MoveBeamline):
    """
    Macro to save a configuration of the beamline for one of the fort ranges.
    """

    def run(self):
        self.runSaveConfig('BeamlineEnergyConfig', BL_ENERGY_CONFIG )

def selectCrystal(macro_obj, crystal):
    if crystal.lower() not in ['si111', 'si311']:
        macro_obj.error('The cystal should be si111/si311')
        raise RuntimeError()    
       
    if crystal.lower() == 'si111':
        config_env = 'Clear111BeamlineEnergyConfig'
        config_range = CLEAR_111_ENERGY_CONFIG
    else:
        config_env = 'Clear311BeamlineEnergyConfig'
        config_range = CLEAR_311_ENERGY_CONFIG

    return config_env, config_range


class mvblEc(Macro, MoveBeamline):
    """
    Macro to align the beamline to a specific energy. The macro move different
    elements: Monochromator, VFM, VCM, sample table, others.

    The macro need the an environment variable (BeamlineEnergyConfig) with
    the configuration of the beamline for different energies.
    """


    param_def = [['energy', Type.Float, None, 'Beamline energy in eV'],
                 ['crystal', Type.String, None, 'Monochromator crystal'],
                 ['retries', Type.Integer, 3, 
                  'Number of retries to move the motors']]

    
                   
    def run(self, energy, crystal, retries):
                
        config_env, config_range = selectCrystal(self, crystal)

        self.runMoveBeamline(energy, config_env, config_range, retries)


class mvEc(Macro, MoveBeamline):
    """
    Macro to align the mono to a specific energy. The macro move different
    motor of the mono. The sign of the oh_dcm_z movement determines if the
    macro moves first the energy or the high of the mono.

    The macro need the an environment variables Clear311BeamlineEnergyConfig
    and Clear111BeamlineEnergyConfig with the configuration of the beamline
    for different energies by using the CLEAR.
    """


    param_def = [['energy', Type.Float, None, 'Beamline energy in eV'],
                 ['crystal', Type.String, None, 'Monochromator crystal'],
                 ['retries', Type.Integer, 3,
                  'Number of retries to move the motors']]

    def run(self, energy, crystal, retries):
        config_env, config_range = selectCrystal(self, crystal)

        self.runMoveMono(energy, config_env, config_range, retries)


class saveblEc(Macro, MoveBeamline):
    """
    Macro to save a configuration of the beamline for one of the ranges.
    """
    param_def = [['crystal', Type.String, None, 'Monochromator crystal']]

    def run(self, crystal):

        config_env, config_range = selectCrystal(self, crystal)
        self.runSaveConfig(config_env, config_rangels)
        




