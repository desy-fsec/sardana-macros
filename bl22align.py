import ConfigParser
from sardana.macroserver.macro import Macro, Type
import time

class ConfigAling(object):
    """
    Class Helper to read the configuration file.
    """

    def initConfig(self, str_energy, config_path):
        self.config_file = ConfigParser.RawConfigParser()
        self.config_file.read(config_path)
        self.config_path = config_path
        
        # Select configuration: 
        if str_energy.lower() == 'clear':
            self.config = 'clear'
            self.energy = 7 #7kev 
            self.execMacro('mv energy %s' % 7000)
        else:
            
            try:
                self.energy =  float(str_energy) / 1000 # to use keV
            except Exception as e:
                raise ValueError('The energy should be: clear or a number')

            if self.energy > 62.5 or self.energy < 2.4:
                msg = 'Value out of range [2400, 62500]'
                raise ValueError(msg)
            elif self.energy >= 35:
                self.config = '35keV'
            elif self.energy >= 14:
                self.config = '14keV'
            elif self.energy >= 7:
                self.config = '7keV'
            elif self.energy >= 2.4:
                self.config = '2.4keV'
        
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
                pos = eval(equation,{'en': self.energy})
            cmd += ' %s %s' % (motor, pos)
            if not all_motors:
                cmds.append(cmd)
                cmd = 'mv'
        if all_motors:
            cmds.append(cmd)
        return cmds

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
            if element in self.motors_cal:
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


class mvblE(Macro, ConfigAling):
    """
    Macro to align the beamline to a specific energy. The macro move different
    elements: Monochromator, VFM, VCM, sample table, others.

    The macro need the an environment variable (BeamlineEnergyConfig) with
    the configuration of the beamline for different energies.
    """


    param_def = [['energy', Type.String, None, 'Beamline energy in eV'],
                 ['retries', Type.Integer, 3, 
                  'Number of retries to move the motors']]

    
                   
    def run(self, energy, retries):
        try:
            config_path = self.getEnv('BeamlineEnergyConfig')
            self.initConfig(energy, config_path)
            
            self.execMacro('feclose')
            if energy.lower() != 'clear':
                self.execMacro('mv energy %s' % energy)

            self.info('Configuring filters...')
            for ior in self.get_ioregisters():
                wvalue = int(self.get_element(ior))
                dev_ior = self.getDevice(ior)
                dev_ior.write_attribute('value', wvalue)
                for i in range(retries):
                    rvalue = dev_ior.read_attribute('value')
                    time.sleep(5)
                    if rvalue == wvalue:
                        break
                else:
                    msg = 'Is was not possible to set the filter {0} to {1}'
                    self.error(msg.format(ior, wvalue))

            # Load motor position from the configuration except table_z
            self.info('Moving motors....')
            for instrument in self.get_instruments():
                if instrument == 'table_z':
                    continue
                for cmd in self.get_cmds_mov(instrument):
                    for i in range(retries):
                        self.execMacro(cmd)
            
            self.execMacro('mv energy %f' % energy)
            # It will be possible whit the new EPS configuration. 
            self.execMacro('feopen')

            self.info('Moving table_z....')
            for cmd in self.get_cmds_mov('table_z'):
                for i in range(retries):
                    self.execMacro(cmd)
            
                    
        except Exception as e:
            self.error('Exception with alignment: %s' % e)


class saveblE(Macro, ConfigAling):
    """
    Macro to save a configuration of the beamline for one of the fort ranges.
    """

    energy_name = 'energy'

    def run(self):
        config_path = self.getEnv('BeamlineEnergyConfig')
        mot_energy = self.getDevice(self.energy_name)
        energy = mot_energy.read_attribute('position').value
        self.initConfig(energy, config_path)
        self.update_config()
