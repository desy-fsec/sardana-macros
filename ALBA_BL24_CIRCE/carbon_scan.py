from sardana.macroserver.macro import Macro, Type, Hookable
from sardana.macroserver.scan import SScan
import ConfigParser
import time
import math
import numpy as np
import os

class CarbonExperiment(object):
    """
    Class to implement the scan and calibration of the Carbon Experiment.
    In Capitals, the beamline constants that need to be configured.

    * The location of the calibration files is specified by a Sardana
    environment variable called DIR_CALIB_FILES.

    """
    # --- Calibration directory files environment variable ---
    DIR_CALIB_FILES = 'CarbonCalibDir'

    # --- Polarizations dictionary ---
    POLARIZATION = {'LH': 0,
                    'LV': math.pi/2.0 - 1e-6,
                    'CP': math.pi/4.0,
                    'CN': -math.pi/4.0
                    }
    # --- Integration time ---
    INT_TIME = 0.2

    # --- Measurement group ---
    MEASUREMENT_GROUP = 'brfma_kb_izeroa'

    # --- Motor names ---
    ID_NAME = 'ideu62_motor_energy'
    ENERGY_NAME = 'Energy'
    POLARIZATION_NAME = 'ideu62_motor_polarization'

    # --- First mesh parameters ---
    # finding the Energy at which flux is minimum
    # (while optimzing at each step the ID)
    ENERGY_MESH_RANGE_REL = [-1, 1]# [-5, 5]
    ENERGY_MESH_DELTA = 0.2 # 0.1
    ID_MESH_RANGE = [295, 310] #[290, 320]
    ID_MESH_DELTA = 1 #1

    # --- Second mesh parameters ---
    ID_SCAN_RANGE = [410, 290]#[410, 290]
    ID_DELTA = 5
    # --------------------------------------------------------

    def _init(self, simulation, plzn):
        self.max_drain_current = []
        self.ref_drain_current = 0
        self.prev_mg = None
        self.calib_path = None

        if simulation:
            self.set_simulation_mode()
            self.load_calib(plzn, True)
        else:
            self.load_calib(plzn)

        self.create_bkp()

        self.set_measurement_group()

        name_list = [self.ID_NAME, self.ENERGY_NAME, self.POLARIZATION_NAME]
        for name in name_list:
            obj = self.getObj(name)
            if not obj:
                raise RuntimeError('object %s not defined' % self.ID_NAME)

    def set_simulation_mode(self):
        """
        Set constant values to dummy parameters for testing purposes.
        @return:
        """
        # --- SIMULATION TEST PARAMETERS ---
        self.ID_NAME = 'dm_id_energy'
        self.ENERGY_NAME = 'dm_mono_energy'
        self.POLARIZATION_NAME = 'dm_polarization'

        # --- First mesh parameters ---
        self.ENERGY_MESH_RANGE_REL = [-0.6, 0.6]# [-1, 1]
        self.ENERGY_MESH_DELTA = 0.2# 0.5
        self.ID_MESH_RANGE = [290, 320]#[280, 310]
        self.ID_MESH_DELTA = 6 #2

        # --- Second mesh parameters ---
        self.ID_SCAN_RANGE = [340,280] #[390,280] #[1, 0]
        self.ID_DELTA = 6 #2 #0.1

        # --- Measurement group for testing ---
        self.MEASUREMENT_GROUP = 'dummy_mg'
        self.warning("Running in SIMULATION mode!")

    def load_calib(self, plzn, simulation=False):
        """
        Loads the current configuration file for the given polarization.
        @param plzn: polarization label (the value must be one of the keys from
        the POLARIZATION dictionary.
        @simulation: only for testing purposes
        @return: None
        """
        try:
            path = str(self.getEnv(self.DIR_CALIB_FILES))
        except Exception as e:
            raise e

        if not os.path.isdir(path):
            msg = 'path %s does not exists!' % path
            msg += '\nDefine path in Environment variable %s' %\
                   self.DIR_CALIB_FILES
            raise RuntimeError(msg)

        if simulation:
            t = '{0}/test_calib_{1}.cfg'
        else:
            t = '{0}/calib_{1}.cfg'
        calib_path = t.format(path, plzn)
        self.calib_file = ConfigParser.RawConfigParser()
        self.calib_file.read(calib_path)
        self.calib_path = calib_path
        self.output('* Loading calibration table %s' % self.calib_path)

    def get_lookup_table(self, plzn):

        msg = "Loading lookup table from %s" % self.calib_path
        self.debug(msg)
        # get energy and id_energy values
        try:
            tab_energy = self.calib_file.get(plzn, 'energy')
            tab_id_energy = self.calib_file.get(plzn, 'id_energy')
        except Exception as e:
            raise e

        self.tab_energy = map(float, tab_energy.split(','))
        self.tab_id_energy = map(float, tab_id_energy.split(','))
        self.tab_e_max = np.max(self.tab_energy)
        self.tab_e_min = np.min(self.tab_energy)

        msg = 'Lookup table range is [%g, %g]' % (self.tab_e_min, self.tab_e_max)
        self.debug(msg)

        return self.tab_energy, self.tab_id_energy

    def get_corrected_id_energy(self, energy):

        if energy > self.tab_e_max or energy < self.tab_e_min:
            msg = 'Requested energy %g is out of lookup table range [%g, %g].' % (energy, self.tab_e_min, self.tab_e_max)
            raise ValueError(msg)
        else:
            return np.interp(energy, self.tab_energy, self.tab_id_energy)

    def create_bkp(self):
        """
        Creates a backup of the current calibration file loaded ONLY if it is
        not an empty configuration.
        @return: None
        """
        if len(self.calib_file.sections()):
            self.output('Creating backup file...')
            path, filename = self.calib_path.rsplit('/', 1)
            t = '{0}/bkp_{1}_{2}'
            nfilename = t.format(path, time.strftime('%Y%m%d_%H%M%S'), filename)
            self.save_calib(nfilename)
            self.output('Created file: %s' % nfilename)
        else:
            msg = 'Calibration file does not exist or empty. Skipping backup!'
            self.warning(msg)

    def save_calib(self, filename):
        """
        Saves the current calibration to a file
        :param filename: New file name to save the current calibration
        """
        with open(filename,'w') as f:
            self.calib_file.write(f)

    def write_calibration(self, plzn):
        """
        Writes the current calibration to the calib file
        @param plzn: polaritzation
        @return: None
        """
        # remove section and values under section
        self.calib_file.remove_section(plzn)
        # rewrite the file with (section and) new values
        self.calib_file.add_section(plzn)
        energy_str = ','.join(self.energy_values)
        id_str = ','.join(self.id_energy_values)
        self.calib_file.set(plzn, 'energy', energy_str)
        self.calib_file.set(plzn, 'id_energy', id_str)

    def _get_range(self, start, end, delta, report=True):
        """
        Function that returns a series of equidistant values with its delta.
        @param start: First point of the series
        @param end: Last point of the series
        @param delta: Desired delta (this might change)
        @return: A list with the series and the real delta.
        """
        steps = round(abs(end - start) / delta)

        if end > start:
            values, step = np.linspace(start, end, steps + 1, retstep=True)
        else:
            values, step = np.linspace(end, start, steps + 1, retstep=True)
            values = list(reversed(values))
        if report:
            self.debug('\tvalues: %s' % values)
            self.debug('\tdelta: %f (request was %f)' % (step, delta))
        return values, step

    def _simulated_value(self):
        import time
        import math
        return abs(math.cos(math.radians(time.time() * 5 % 360)))

    def _x2(self, x0):
        def f(x):
            return 1-(x - x0)*(x + x0)
        return f

    def simulate_current(self, mono_energy, id_energy):
        carbon_energy = 299.87
        current = 1000+ abs(mono_energy-carbon_energy)*10 - (id_energy-300)*10
        return current

    def set_measurement_group(self):
        try:
            self.output('* Setting active mesurement group: %s' % self.MEASUREMENT_GROUP)
            self.prev_mg = self.getEnv('ActiveMntGrp')
            self.setEnv('ActiveMntGrp', self.MEASUREMENT_GROUP)
        except Exception as e:
            msg = 'Error while switching measurement group from %s to %s' % (self.prev_mg, self.MEASUREMENT_GROUP) 
            raise ValueError('%s\n%s' % (msg, e))

    def restore_measurement_group(self):
        try:
            self.output('* Restoring active mesurement group: %s' % self.prev_mg)
            self.setEnv('ActiveMntGrp', self.prev_mg)
        except Exception as e:
            msg = 'Error while switching measurement group from %s to %s' % (self.MEASUREMENT_GROUP, self.prev_mg)   
            raise ValueError('%s\n%s' % (msg, e))


    def create_calib_table(self, start_energy, end_energy, delta_energy,
                           ref_energy, plzn, channel, simulation=False):
        """
        Creates the calibration table for the CarbonExperiment and stores it in
        a text file. The energy range specified as input parameters defines
        the region where the calibration is calculated.

        This method is intended to be used as a main function in a Sardana
        macro.

        @param start_energy: Initial monocromator energy
        @param end_energy: Final monocromator energy
        @param delta_energy: Resolution in energy
        @param ref_energy: Energy reference
        @param plzn: Polarization (MUST BE one of the POLARIZATION dictionary)
        @param channel: Experimental Sardana channel for current readings.
        @param simulation: Flag to run in simulation mode for testing.
        @return: None
        """
        self._init(simulation, plzn)

#        if simulation:
#            self.load_calib(plzn, True)
#        else:
#            self.load_calib(plzn)
#
#        self.create_bkp()

        try:
            #########################
            # --- FIRST MESH SCAN ---
            #########################
            # --- set experimental channel
            if not simulation:
                self.output('* Setting current channel: %s' % channel)
                self.chn = self.getDevice(channel)
            else:
                self.warning('* Real channel values bypassed!')

            # --- set the polarization
            self.output('* Setting %s polarization.' % plzn)
            self.plzn = str(plzn).upper()
            self.current_values = []

            try:
                pol_pos = self.POLARIZATION[self.plzn]
                self.execMacro('mv %s %f' % (self.POLARIZATION_NAME, pol_pos))
            except Exception as e:
                self.error(e)
                raise e

            # --- set initial position to reference energy
            self.output('* Setting initial reference energy: %s' % ref_energy)
            self.execMacro('mv %s %f' % (self.ENERGY_NAME, ref_energy))

            # --- calculate monochromator scan range
            self.info('\n*** Starting Scan around reference energy ***')
            #self.debug('Energy (mono) scan range:')
            energy_start = ref_energy + self.ENERGY_MESH_RANGE_REL[0]
            energy_end = ref_energy + self.ENERGY_MESH_RANGE_REL[1]
            energy_delta = self.ENERGY_MESH_DELTA
            energy_range, step_energy = self._get_range(energy_start,
                                                        energy_end,
                                                        energy_delta)
            # --- calculate insertion device scan range
            #self.debug('IDEnergy (ID) scan range:')
            id_range, step_id = self._get_range(self.ID_MESH_RANGE[0],
                                                self.ID_MESH_RANGE[1],
                                                self.ID_MESH_DELTA)

            # --- start custom mesh
            for idx_e, e in enumerate(energy_range):
                self.execMacro('mv %s %f' %(self.ENERGY_NAME, e))
                self.info('\n* Scanning ID at constant Energy %s *' % e)
                # id_range, step_id = self._get_range(e,
                                                #e+20,
                                                #self.ID_MESH_DELTA)
                for idx_i, i in enumerate(id_range):
                    self.execMacro('mv %s %f' %(self.ID_NAME, i))

                    # --- ct measurement
                    
                    if not simulation:
                        self.mnt_grp = self.getObj(self.MEASUREMENT_GROUP,
                                                   type_class=Type.MeasurementGroup)
                        _, _ = self.mnt_grp.count(self.INT_TIME)
                        # self.execMacro('ct %s' % self.INT_TIME)
                        value = self.chn.value
                    else:              
                        value = self.simulate_current(e,i)
                    self.current_values.append(value)
                    self.output('Energy = %s, ID_Energy = %s, Intensity = %g' %
                              (e, i, value))
                m = max(self.current_values)
                self.max_drain_current.append(m)
                self.output('>> Maximum drain current is %g' % m)
                del self.current_values[:]

            # --- reporting reference drain current
            self.ref_drain_current = min(self.max_drain_current)
            self.output('\n* New reference drain current: %g' %
                      self.ref_drain_current)

            # --- reporting new energy reference
            idx_ref = self.max_drain_current.index(self.ref_drain_current)
            self.new_ref_energy = energy_range[idx_ref]
            self.output('* New reference Energy is %s (initial guess was %s)\n' %
                      (self.new_ref_energy, ref_energy))


            ##########################
            # --- SECOND MESH SCAN ---
            ##########################
            # --- setup constants
            self.id_energy_values = []
            self.energy_values = []
            self.delta_max = self.ref_drain_current*1000
            self.prev_delta = self.delta_max
            self.info('*** Starting calibration ***')
            # --- calculate monocromator scan range
            energy_range, step_energy = self._get_range(start_energy,
                                                        end_energy,
                                                        delta_energy)
            #self.output('Energy range: %s, step: %s' % (energy_range, step_energy))

            # --- calculate insertion device scan range
            id_range, step_id = self._get_range(self.ID_SCAN_RANGE[0],
                                                self.ID_SCAN_RANGE[1],
                                                self.ID_DELTA)
            # --- start custom mesh

            self.warning('Target drain current (reference): %g' %
                      self.ref_drain_current)
            for idx_e, e in enumerate(energy_range):
                self.execMacro('mv %s %f' %(self.ENERGY_NAME, e))

                self.info('\n* Search at Energy %s *' % e)
                self.output('%20s\t%20s\t%20s' % ('id_energy',
                                                'current measured',
                                                'delta'))
                self.output(20*'-'+'\t'+20*'-'+'\t'+20*'-')
                import random
                x0 = random.random()
                #self.output('Creating x^2 centered at %s' % x0)
                f = self._x2(x0)

                ######## Lucia method #####
                Micha = True
                if Micha != True: ## Lucia's way
                    id_energy_to_be_fit = []
                    delta_to_be_fit = []
                ###########################
                for idx_i, i in enumerate(id_range):
                    if Micha != True: ## Lucia's way
                        id_energy_to_be_fit.append(i)

                    
                    self.execMacro('mv %s %f' %(self.ID_NAME, i))
                    # --- ct measurement
                    if not simulation:
                        self.mnt_grp = self.getObj(self.MEASUREMENT_GROUP,
                                                   type_class=Type.MeasurementGroup)
                        _, _ = self.mnt_grp.count(self.INT_TIME)
                        #self.execMacro('ct %s' % self.INT_TIME)
                        value = self.chn.value
                    else:
                        value = self.simulate_current(e,i)
                    #self.output('current measured: %s' % value)
                    if Micha == True:
                        # --- searching drain current value closest to maximum
                        # IMPORTANT: we can assume without error that the current
                        # values are constantly increasing up to a maximum.
                        # This fact simplifies the search.
                        delta = abs(value - self.ref_drain_current)
                        #self.debug('delta = %s' % delta)
                        self.output('%20g\t%20g\t%20g' % (i, value, delta))
                        if delta > self.prev_delta:
                            self.id_energy_values.append(str(id_range[idx_i - 1]))
                            self.energy_values.append(str(energy_range[idx_e]))
                            self.prev_delta = self.delta_max
                            self.output(68*'-')
                            msg = 'Energy %s: Minimum delta found at ID_Energy %s'
                            self.output(msg % (self.energy_values[-1],
                                            self.id_energy_values[-1]))
                            self.refinement(e, simulation)
                            break
                        else:
                            self.prev_delta = delta 
                    else: ## Lucia's way
                        delta = value - self.ref_drain_current
                        self.output('%20g\t%20g\t%20g' % (i, value, delta))
                        delta_to_be_fit.append(delta)
                
                if Micha != True: ## Lucia's way
                    self.energy_values.append(str(energy_range[idx_e]))
                    self.refinementLucia( id_energy_to_be_fit, delta_to_be_fit)
                
            # --- store and save tha calibration to a file
            self.write_calibration(str(plzn).upper())
            self.warning('\nSaving calibration to %s\n' % self.calib_path)
            self.save_calib(self.calib_path)
            self.output('[DONE]')

        except Exception as e:
            self.error(e)

        finally:
            # Revert here any beamline variable to its initial value.
            self.restore_measurement_group()

    def refinementLucia(self,refined_id_energy, refined_values): ## Lucia's way
        # Lineal fit to find the best id_current that matches the ref_drain_current
        np_id_energies = np.array(refined_id_energy)
        np_currents = np.array(refined_values)
        pf = np.polyfit(np_currents,np_id_energies,1)
        #self.output("FIT %f, %f" %(pf[0], pf[1]))
        a = round(pf[1],2)
        best_id_energy = str(a) #str(pf[1])
        self.id_energy_values.append(best_id_energy)
        ## Overwrite the rough value with the best value
        #self.id_energy_values[-1] =  best_id_energy
        msg = 'Minimum delta for Mono Energy %s found at ID Energy %s'
        self.output(msg % (self.energy_values[-1],
                         self.id_energy_values[-1]))

    def refinement(self, mono_energy, simulation):
        refined_id_energy = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        refined_values = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

        central_id_energy = float(self.id_energy_values[-1])
        for index in range(21):
            id_energy = central_id_energy + 0.5*(index-10)
            self.execMacro('mv %s %f' %(self.ID_NAME, id_energy))
            refined_id_energy[index] = id_energy

            if not simulation:
                self.mnt_grp = self.getObj(self.MEASUREMENT_GROUP,
                                           type_class=Type.MeasurementGroup)
                _, _ = self.mnt_grp.count(self.INT_TIME)
                # self.execMacro('ct %s' % self.INT_TIME)
                value = self.chn.value
                #self.output("chn value %s" %str(value))
            else:
                value = self.simulate_current(mono_energy,id_energy)

            refined_values[index] = float(value) - float(self.ref_drain_current)
            
            self.output("Refinement: %f, %.3e" %(id_energy, refined_values[index]))

        # Lineal fit to find the best id_current that matches the ref_drain_current
        np_id_energies = np.array(refined_id_energy)
        np_currents = np.array(refined_values)
        pf = np.polyfit(np_currents,np_id_energies,1)
        #self.output("FIT %f, %f" %(pf[0], pf[1]))
        a = round(pf[1],2)
        best_id_energy = str(a) #str(pf[1])
        # Overwrite the rough value with the best value
        self.id_energy_values[-1] =  best_id_energy
        msg = 'Refined Energy %s: Minimum delta found at ID_Energy %s'
        self.output(msg % (self.energy_values[-1],
                         self.id_energy_values[-1]))

    def prepare_carbon_scan(self, simulation, plzn):
        # Load calibration table
        self.load_calib(plzn, simulation)

        e_array, e_id_array = self.get_lookup_table(plzn)
        self.debug('energy: %s\n id_energy: %s' % (e_array, e_id_array))

        # Set Polarization
        self.output('* Setting %s polarization.' % plzn)
        self.plzn = str(plzn).upper()

        try:
            pol_pos = self.POLARIZATION[self.plzn]
            self.execMacro('mv %s %f' % (self.POLARIZATION_NAME, pol_pos))
        except Exception as e:
            self.error(e)
            raise e


class CalibrateCarbonScan(CarbonExperiment, Macro):
    """
    Category: Calibration

    Creates the calibration file for the CarbonExperiment macro.
    """
    param_def = [['startenergy', Type.Float, None, 'Initial scan energy'],
                 ['endenergy', Type.Float, None, 'Final scan energy'],
                 ['deltaenergy', Type.Float, None, 'Increment energy'],
                 ['refenergy', Type.Float, None, 'Reference energy'],
                 ['plzn', Type.String, '', 'Polarization: LH, LV, CP, CN'],
                 ['channel', Type.String, '', 'Drain current channel'],
                 ['simulation', Type.Boolean, '', 'Simulation mode for testing']
                 ]

    def prepare(self, *args, **kargs):
        # --- selecting the measurement group
        self.output('######################################')
        self.output('###    Carbon Calibration Macro    ###')
        self.output('######################################')

#        self.set_measurement_group()

    def run(self, *args, **kargs):
        self.create_calib_table(*args, **kargs)

    def on_abort(self, *args, **kargs):
        # Revert here any beamline variable to its initial value.
        self.restore_measurement_group()

class CarbonScan(CarbonExperiment, Macro, Hookable):
    """
    Category: experiment

    Performs a carbon scan experiment. Monochromator scan in which
    the id energy is corrected according to a calibration table.
    """
    param_def = [['start_pos', Type.Float, None, 'Initial scan position'],
                 ['final_pos', Type.Float, None, 'Final scan position'],
                 ['nr_interv', Type.Integer, None, 'Number of scan intervals'],
                 ['integ_time', Type.Float, None, 'Integration time'],
                 ['plzn', Type.String, '', 'Polarization: LH, LV, CP, CN'],
                 ['simulation', Type.Boolean, '', 'Simulation mode for testing']
                 ]

    def prepare(self, *args, **kargs):
        # --- selecting the measurement group
        self.output('###############################')
        self.output('###    Carbon Scan Macro    ###')
        self.output('###############################')
        
        simulation = args[5]
        if simulation:
            self.set_simulation_mode()

        self.set_measurement_group()
        
        env = kargs.get('env', {})

        self.start_pos = args[0]
        self.final_pos = args[1]
        self.nr_intervals = args[2]
        self.int_time = args[3]
        plzn = args[4]

        self.prepare_carbon_scan(simulation, plzn)

        self.motors = [self.getMoveable(self.ENERGY_NAME), self.getMoveable(self.ID_NAME)]
        self._gScan = SScan(self, self._generator, self.motors, env)

    def _generator(self):
        #### Only if the macro need any hook(s) ###
        step = dict()
        step["pre-move-hooks"] = self.getHooks('pre-move')
        step["post-move-hooks"] = self.getHooks('post-move')
        step["pre-acq-hooks"] = self.getHooks('pre-acq')
        step["post-acq-hooks"] = self.getHooks('post-acq') +\
                                 self.getHooks('_NOHINTS_')
        step["post-step-hooks"] = self.getHooks('post-step')
        step["check_func"] = []
        ############################################

        point_id = 0
        step["integ_time"] = self.int_time

        # Generate all the motor scan positions
        scan_pos = np.linspace(self.start_pos, self.final_pos,
                               self.nr_intervals + 1)

        for motor_scan_pos in scan_pos:
            # Populate dictionary with position value and point index
            step["positions"] = [motor_scan_pos,
                                 self.get_corrected_id_energy(motor_scan_pos)]
            step["point_id"] = point_id
            yield step
            point_id += 1

    def myPostMoveHook(self):
        self.output("... ... ... myPostMoveHook ... ... ...")
        self.execMacro("peemGetSingleImage 0")


    def run(self, *args):
        try:
            for step in self._gScan.step_scan():
                yield step
                self.hooks = [(self.myPostMoveHook, ['post-move'])]
            self.output('[DONE]')
        finally:
            self.restore_measurement_group()
    
    @property
    def data(self):
        return self._gScan.data

    def on_abort(self, *args, **kargs):
        # Revert here any beamline variable to its initial value.
        self.restore_measurement_group()

