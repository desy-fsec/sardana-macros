from sardana.macroserver.macro import Type, Macro, Hookable
from sardana.macroserver.scan import SScan
from sardana.macroserver.macros.scan import ascan, getCallable, UNCONSTRAINED
import taurus
import PyTango
from numpy import linspace, sqrt
import time

EV2REVA = 0.2624682843


class BL22ContScan(object):
    """
    Class to implement the continuous scan methods. 
    """
    
    adlinks = ['bl22/ct/adc-ibl2202-01', 'bl22/ct/adc-ibl2202-02']
    masterTriggerName = "bl22/io/ibl2202-dev1-ctr0"    
    mem_overload = 1000000
    min_itime = 0.5
    pmacName = "pmac"
    motName = "energy"
    bragg_Name = "oh_dcm_bragg"
    


    def _check_parameters(self, itime, nr_triggers, speed_check=True):
        stime = itime * nr_triggers
        if speed_check:
            if itime < self.min_itime:
                raise Exception(('You must use a higher integration time '
                                 '(integration time = scanTime/nrOfTriggers).'
                                 ' The minimum value is 0.5'))
        else:
            self.warning('The speed verification is desactive')

        mem = nr_triggers * stime
        if mem > self.mem_overload:
            raise Exception(('You can not send this scan, because there is not '
                             'enough memory. The combination of the nrOfTrigger'
                             '*scanTime < 1000000'))
    
    def getNrOfPoints(self, e0, e1, deltaE):
        nr_points, modulo = divmod(abs(e0 - e1), deltaE)
        if modulo != 0:
            nr_points += 1
                
        return int(nr_points)

    def energy_bragg_encoder(self, energy_values):
        """
        :param energy_values: Array with the energy values
        :return: Array with the bragg encoder values
        """

        energy_motor = taurus.Device('pm/dcm_energy_ctrl/1')  # energy
        bragg_motor = taurus.Device('motor/dcm_pmac_ctrl/1')  # oh_dcm_bragg
        pmac = taurus.Device('bl22/ct/pmaceth-01')

        # Translations from  degrees to raw counts. Getting an offset between
        # position and encoder register (offset = 2683367)
        stepPerUnit = bragg_motor.read_attribute('step_per_unit').value
        braggMotorOffset = bragg_motor.read_attribute('offset').value
        braggMotorOffsetEncCounts = braggMotorOffset * stepPerUnit
        braggPosCounts = float(pmac.SendCtrlChar("P").split()[0])
        encRegCounts = float(pmac.GetMVariable(101))
        offset = braggPosCounts - encRegCounts + braggMotorOffsetEncCounts

        # Transform from energy to bragg angle, the first motor is bragg the
        # second on is the perpendicular
        maxCounts = 2**23  # encoder register 24 bits overflow

        calc_bragg = lambda energy: energy_motor.CalcAllPhysical([energy])[0]
        calc_enc = lambda bragg: (bragg * stepPerUnit) - offset

        enc_values = []
        for energy in energy_values:
            # transform energy to bragg angle
            bragg = calc_bragg(energy)
            enc = calc_enc(bragg)
            if enc > maxCounts:
                enc_value = enc - 2 * maxCounts
            elif enc < - maxCounts:
                enc_value = enc + 2 * maxCounts
            else:
                enc_value = enc
                enc_values.append(int(enc_value))
        return enc_values


    def _pre_configure_hook(self):
        self.debug("preConfigure entering...")
       
        if self.flg_pmac:
            self.debug('Configuring Pmac...')
            pmac = taurus.Device(self.pmacName)
            if self.flg_time_trigger:
                self.debug('Pmac capture trigger mode')
                # select the capture program
                pmac.SetPVariable([4077, 1])
                # configuring position capture control
                pmac.SetIVariable([7012, 2])
                # configuring position capture flag select
                pmac.SetIVariable([7013, 3])
                # after enabling position capture, M117 is set to 1, forcing readout
                # of M103, to reset it, so PLC0 won't copy outdated data
                pmac.GetMVariable(103)
            else:
                self.debug('Pmac generate trigger mode')
                # select the compare program
                pmac.SetPVariable([4077, 2])
                # prepare encoder table
                energy_values = linspace(self.startPos, self.finalPos,
                                         self.nrOfTriggers)
                enc_values = self.energy_bragg_encoder(energy_values)
                first_point_register_a = enc_values[0]
                if (self.startPos < self.finalPos):
                    direction = 0
                    first_point_register_b = first_point_register_a + 5
                else:
                    direction = 1
                    first_point_register_b = first_point_register_a - 5
                pmac.SetPVariable([4075, direction])
                pmac.SetPVariable([4078, self.nrOfTriggers])
                start_buffer = int(pmac.GetPVariable(4076))
                end_buffer = start_buffer + self.nrOfTriggers
                for p_reg, value in zip(range(start_buffer, end_buffer), enc_values):
                    pmac.SetPVariable([p_reg, value])

                # Configure the PLC0:
                # first point on the compare register A&B
                # set auto-increment to 0 to avoid the eneble of the compare circuit
                # set output to start on Low Level
                # update the signal output

                pmac.SetMVariable([108, first_point_register_a])
                pmac.SetMVariable([109, first_point_register_b])
                pmac.SetMVariable([110, 0])
                pmac.SetMVariable([112, 0])
                pmac.SetMVariable([111, 1])
   
            # enabling plc0 execution
            pmac.SetIVariable([5, 3])
        
        if self.run_startup:
            self.startup()
        
        if self.wait_fe:
            try:
                self.execMacro('waitFE')
            except Exception as e:
                self.error('There was an exception with the waitFE macro: '
                           '%s' % e)
                raise RuntimeError()

    def _post_configure_hook(self):
        self.debug('postConfigure entering...')
        if self.flg_pmac: 
            self.debug('Setting Pmac starting delay...')
            dev = PyTango.DeviceProxy('bl22/io/ibl2202-dev1-ctr0')
            if self.flg_time_trigger:
                delay = dev.read_attribute('InitialDelayTime').value
                total_delay = delay + self.pmac_dt
                #dev.write_attribute('InitialDelayTime', total_delay)
            else:
                tota_delay = 0
                dev.write_attribute('InitialDelayTime', total_delay)
    
    def _pre_strat_hook(self):
        self.debug('preStart entering....')
        if self.flg_pmac:
            if not self.config_PID:
                self.info('Did not config bragg PID')
                return
            bragg = taurus.Device(self.bragg_Name)
            self.info(bragg.velocity)
            # TODO Load from file the configuration
            
            self.info('Configuring bragg PID....')
            pmac = taurus.Device(self.pmacName)
            #Kp I130
            pmac.SetIVariable([130, 30000])
            #Kd I131
            pmac.SetIVariable([131, 375])
            #Kvff I132
            pmac.SetIVariable([132, 30000])
            #K1 I133
            pmac.SetIVariable([133, 5000])
            #IM I134
            pmac.SetIVariable([134, 0])
            #Kaff I135
            pmac.SetIVariable([135, 3500])

    def _post_move_hook(self):
        self.debug('postMove entering....')
        if self.flg_pmac:
            self.info('load PID default config')
            self.execMacro('configpmac')
            self.flg_post_move = True

    def _post_cleanup_hook(self):
        self.debug("postCleanup entering...")
        if self.flg_pmac:
            pmac = taurus.Device(self.pmacName)
            if self.flg_time_trigger:
                # setting position capture control to its default value
                pmac.SetIVariable([7012, 1])
                # setting position capture flag select to its default value
                pmac.SetIVariable([7013, 0])
            # disabling plc0 execution
            pmac.SetIVariable([5, 2])

    def startup(self):
        """
        Method to configure the Adlink and the Ni660X for the
        continuous scan
        """
        self.debug('Configuring Adlink...')
        for adlink in self.adlinks:
            adc = taurus.Device(adlink)
            if adc.State() != PyTango.DevState.STANDBY:
                adc.Stop()

        self.debug('Configuring NI660X...')
        
        output_signals = ['/DEV1/C0O', '/DEV1/C0A',
                          '/DEV1/C1O', '/DEV1/C1A', '/DEV1/RTSI0']
        self.ni_connect_channels(output_signals)
        self.ni_config_counter('continuous')


        self.info("qExafs startup is done")


    def cleanup(self):
        self.debug('Restore Default Measurement Group')
        mg = self.getEnv('DefaultMG')
        self.setEnv('ActiveMntGrp', mg)
        
        self.debug('Configuring Adlink...')
        for adlink in self.adlinks:
            adc = taurus.Device(adlink)
            if adc.State() != PyTango.DevState.STANDBY:
                adc.Stop()
            else:
                adc.Init()
                # in case of stopping acq, state is alredy STANDBY, but it does
                # not allow starting new acq @todo in DS
            adc.getAttribute("TriggerSources").write("SOFT")
            adc.getAttribute("TriggerMode").write(0)
            adc.getAttribute("TriggerInfinite").write(0)

        # in case of aborting qExafs macro, seems that there is an exception in
        # aborting adlink device,
        # to be sure stopping trigger lines if they were not stopped.
        self.debug('Configuring NI660X...')
        output_signals = ['/DEV1/C0O', '/DEV1/C0A',
                          '/DEV1/C1O', '/DEV1/C1A', '/DEV1/RTSI0']
        self.ni_connect_channels(output_signals)
        self.ni_config_counter('step')

        self.info("qExafs cleanup is done")
    
            

    def run_scan(self, motor, start_pos, end_pos, nr_trigger, int_time, 
                 speed_check, wait_fe, config_pid, run_startup=True, 
                 run_cleanup=True, pmac_delay=0.01, acq_time=99, 
                 nr_repeat=1, back_forth=False):
        
        self._check_parameters(int_time, nr_trigger, speed_check)
        try:
            self.run_startup = run_startup
            self.run_cleanup = run_cleanup
            self.pmac_dt = pmac_delay
            self.config_PID = config_pid
            self.flg_post_move = False
            self.wait_fe = wait_fe
        
        
            if back_forth:
                nr_repeat *= 2

            for i in range(nr_repeat):
                scan_macro, pars = self.createMacro("ascanct_ni", motor,
                                                    start_pos, end_pos,
                                                    nr_trigger, int_time,
                                                    acq_time)
                scan_macro.hooks = [(self._pre_configure_hook, 
                                     ["pre-configuration"]),
                                    (self._post_configure_hook,
                                     ["post-configuration"]),
                                    (self._post_cleanup_hook,
                                     ["post-cleanup"]),
                                    (self._pre_strat_hook,
                                     ["pre-start"]),
                                    (self._post_move_hook,
                                     ["post-move"])]
                self.debug("Running %d repetition" % i)
                self.runMacro(scan_macro)
                if back_forth:
                    self.debug("Swapping start with end")
                    start_pos, end_pos = end_pos, start_pos
                        
                    
        except Exception as e:
            self.error('Exception: %s' % e)
            self.cleanup()

        finally:
            if self.run_cleanup:
                self.execMacro('qExafsCleanup')
            if self.flg_pmac and not self.flg_post_move:
                self._post_move_hook()
    
    def run_qexafs(self, start_pos, end_pos, nr_trigger, scan_time, speed_check, 
              wait_fe, config_pid, time_mode=True):

        self.flg_pmac = True
        self.flg_time_trigger = time_mode
        
        mg = self.getEnv('ContScanMG')
        self.setEnv('ActiveMntGrp', mg)
        self.execMacro('feauto 1')
       
        motor = self.getMoveable(self.motName)
        
        int_time = scan_time / nr_trigger
        
        
        self.run_scan(motor, start_pos, end_pos, nr_trigger, int_time,
                      speed_check, wait_fe, config_pid)


    def run_qexafse(self,  e0, e1, deltaE, int_time, speed_lim, wait_fe):
        pass


    def run_cascan(self, motor, start_pos, end_pos, nr_trigger, int_time,
               speed_check, wait_fe):

        self.flg_pmac = False
        self.flg_time_trigger = True

        mg = self.getEnv('CascanMG')
        self.setEnv('ActiveMntGrp', mg)
        self.execMacro('feauto 1')
        
       
        self.run_scan(motor, start_pos, end_pos, nr_trigger, int_time,
                      speed_check, wait_fe, config_pid=False);
        
        
    def run_cdscan(self, motor, start_pos, end_pos, nr_trigger, int_time,
               speed_check, wait_fe):
        pos = motor.position
        start_pos += pos
        end_pos += pos
        self.cascan(motor, start_pos, end_pos, nr_trigger, int_time,
                    speed_check, wait_fe)
        self.info('Moving %s to %s' %(motor, pos))
        self.execMacro( 'mv %s %s' % (motor, pos))


class cdscan(Macro, BL22ContScan):
    """
    Macro to execute the continuous scan.
    """
    
    param_def = [["motor", Type.Moveable, None, "Motor"],
                 ["startPos", Type.Float, None, "Starting position"],
                 ["endPos", Type.Float, None, "Ending pos value"],
                 ["nrOfTriggers", Type.Integer, None, "Nr of triggers"],
                 ["inttime", Type.Float, None, "Integration time per point"],

                 ["speedLim", Type.Boolean, True, ("Active the verification "
                                                   "of the speed and "
                                                   "integration time")],
                 ["waitFE", Type.Boolean, True, ("Active the waiting for "
                                                 "opening of Front End")]]
    
    def run(self, motor, startPos, finalPos, nrOfTriggers, intTime, 
            speedLim, wait_fe):
        self.run_cdscan(motor, startPos, finalPos, nrOfTriggers, intTime, 
                        speedLim, wait_fe)
        
         

class cascan(Macro, BL22ContScan):
    """
    Macro to execute the continuous scan.
    """

    env = ('CascanMG',)
   
    hints = {}

    param_def = [["motor", Type.Moveable, None, "Motor"],
                 ["startPos", Type.Float, None, "Starting position"],
                 ["endPos", Type.Float, None, "Ending pos value"],
                 ["nrOfTriggers", Type.Integer, None, "Nr of triggers"],
                 ["inttime", Type.Float, None, "Integration time per point"],

                 ["speedLim", Type.Boolean, True, ("Active the verification "
                                                   "of the speed and "
                                                   "integration time")],
                 ["waitFE", Type.Boolean, True, ("Active the waiting for "
                                                 "opening of Front End")]]

  
    def run(self, motor, startPos, finalPos, nrOfTriggers, intTime, speedLim, wait_fe):
        self.run_cascan(motor, startPos, finalPos, nrOfTriggers, intTime, 
                        speedLim, wait_fe)

        
            
class qExafs(Macro, BL22ContScan):
    """
    Macro to execute the quick Exafs experiment.
    """

    env = ('ContScanMG',)

    hints = {}

    param_def = [["startPos", Type.Float, None, "Starting position"],
                 ["endPos", Type.Float, None, "Ending pos value"],
                 ["nrOfTriggers", Type.Integer, None, "Nr of triggers"],
                 ["scanTime", Type.Float, None, "Scan time"],

                 ["speedLim", Type.Boolean, True, ("Active the verification "
                                                   "of the speed and "
                                                   "integration time")],
                 ["waitFE", Type.Boolean, True, ("Active the waiting for "
                                                 "opening of Front End")],
                 
                 ["configPID", Type.Boolean, True, ("Active the configuration"
                                                 " of the bragg PID ")]]


    def run(self, startPos, finalPos, nrOfTriggers, scanTime, speedLim, wait_fe,
            config_PID):

        self.run_qexafs(startPos, finalPos, nrOfTriggers,scanTime,speedLim, wait_fe,
                        config_PID)




class qExafsStartup(Macro, BL22ContScan):
    """
    The macro configures the Adlink and the Ni660X for the
    continuous scan
    """

    

    def run(self):
        self.startup()


class qExafsCleanup(Macro, BL22ContScan):
    
    def run(self):
        self.cleanup()









#*****************************************************************************************************************
# OLD
#*****************************************************************************************************************

    

def getNrOfPoints(e0, e1, deltaE):
    nr_points, modulo = divmod(abs(e0 - e1), deltaE)
    if modulo != 0:
        nr_points += 1

    return int(nr_points)


class qExafsE(Macro):
    """
    Macro to run the qExafs experiment using the energy resolution.

    """
    param_def = [["E0", Type.Float, None, "Starting energy"],
                 ["E1", Type.Float, None, "Ending energy"],
                 ["deltaE", Type.Float, None, "Energy resolution"],
                 ["intTime", Type.Float, 0.5, "Integration time by point"],

                 ["speedLim", Type.Boolean, True, ("Active the verification "
                                                   "of the speed and "
                                                   "integration time")],
                 ["waitFE", Type.Boolean, True, ("Active the waiting for "
                                                 "opening of Front End")]]

    def run(self, e0, e1, deltaE, int_time, speed_lim, wait_fe):
        try:
            nr_points = getNrOfPoints(e0, e1, deltaE)
            scan_time = nr_points * int_time
            qExafsScan, pars = self.createMacro('qExafs', e0, e1, nr_points,
                                                scan_time, speed_lim, wait_fe,
                                                True, False)
            self.runMacro(qExafsScan)
        finally:
            self.execMacro('qExafsCleanup')


class qSpectrum(Macro):
    """
    Macro to run the qExafs experiment using the energy resolution.

    """
    param_def = [["E1", Type.Float, None, "first energy (eV)"],
                 ["E2", Type.Float, None, "second energy (eV)"],
                 ["E3", Type.Float, None, "third energy (eV)"],
                 ["E4", Type.Float, None, "fourth energy (eV)"],
                 ["E0", Type.Float, None, "edge energy (eV)"],
                 ["deltaE1", Type.Float, None, "Energy resolution (eV)"],
                 ["deltaE2", Type.Float, None, "Energy resolution (eV)"],
                 ["deltaK", Type.Float, None,
                  "K resolution (A^-1) between first and second point"],
                 ['filename', Type.String, None, "filename to extract data"],
                 ["intTime", Type.Float, 0.5, "Integration time by point"],
                 ["speedLim", Type.Boolean, True, ("Active the verification "
                                                   "of the speed and "
                                                   "integration time")],
                 ["waitFE", Type.Boolean, True, ("Active the waiting for "
                                                 "opening of Front End")]]
    mem_overload = 1000000

    def run(self, e1, e2, e3, e4, e0, deltaE1, deltaE2, deltaK, filename,
            int_time, speed_lim, wait_fe):

        try:
            run_cleanup = True

            # First region
            nr_points1 = getNrOfPoints(e1, e2, deltaE1)
            scan_time1 = nr_points1 * int_time
            mem_1 = nr_points1 * scan_time1
            # Run the startup but not the cleanup
            qExafsScan1, pars = self.createMacro('qExafs', e1, e2, nr_points1,
                                                 scan_time1, speed_lim, wait_fe,
                                                 True, False)

            if mem_1 > self.mem_overload:
                raise Exception(('You can not send this scan, because there is '
                                 'not enough memory. The deltaE1 is too '
                                 'small'))

            # Second region
            nr_points2 = getNrOfPoints(e2, e3, deltaE2)
            scan_time2 = nr_points2 * int_time
            mem_2 = nr_points2 * scan_time2
            # Don't run the startup and the cleanup
            qExafsScan2, pars = self.createMacro('qExafs', e2, e3, nr_points2,
                                                 scan_time2, speed_lim, wait_fe,
                                                 False, False)

            if mem_2 > self.mem_overload:
                raise Exception(('You can not send this scan, because there is '
                                 'not enough memory. The deltaE2 is too '
                                 'small'))

            # Third region
            h2_2me = 1.505e-18  # Constans h2/2me = 1.505 eVnm2
            e3_e0 = abs(e3 - e0)
            deltaE3 = (sqrt(e3_e0) - (deltaK * 1e10) * (
                sqrt(h2_2me))) ** 2 - e3_e0
            deltaE3 = abs(deltaE3)
            nr_points3 = getNrOfPoints(e3, e4, deltaE3)
            scan_time3 = nr_points3 * int_time
            mem_3 = nr_points3 * scan_time3
            # Run the cleanup but not the startup
            qExafsScan3, pars = self.createMacro('qExafs', e3, e4, nr_points3,
                                                 scan_time3, speed_lim, wait_fe,
                                                 False, True)

            if mem_3 > self.mem_overload:
                raise Exception(('You can not send this scan, because there is '
                                 'not enough memory. The deltaK is too '
                                 'small'))

            # Show the estimate time of the spectrum
            total_time = (scan_time1 + scan_time2 + scan_time3) / 60.0
            msg = 'The estimated time of the spectrum is %f min.' % total_time
            self.info(msg)

            self.runMacro(qExafsScan1)
            self.runMacro(qExafsScan2)
            self.runMacro(qExafsScan3)
            run_cleanup = False
            fname = '%s/%s.dat' % (self.getEnv('ScanDir'), filename)
            self.execMacro('extractlastexafs %s 3 none' % (fname))

        finally:
            if run_cleanup:
                self.execMacro('qExafsCleanup')


class aEscan(Macro):
    """
    Macro to run a step scan. The macro verifies if the front end is open before
    to measure in each point.
    """
    param_def = [['motor', Type.Moveable, None, 'Moveable to move'],
                 ['start_pos',  Type.Float,   None, 'Scan start position'],
                 ['final_pos',  Type.Float,   None, 'Scan final position'],
                 ['nr_interv',  Type.Integer, None, 'Number of scan intervals'],
                 ['integ_time', Type.Float,   None, 'Integration time']]

    def pre_acquisition(self):
        self.execMacro('waitFE')

    def prepare(self, *args):
        mg = self.getEnv('DefaultMG')
        self.setEnv('ActiveMntGrp', mg)

    def run(self, motor, start_pos, final_pos, nr_interv, integ_time):
        macro_ascan, _ = self.createMacro('ascan', motor, start_pos, final_pos,
                                          nr_interv, integ_time)

        macro_ascan.hooks = [(self.pre_acquisition, ["pre-acq"]), ]

        self.runMacro(macro_ascan)


###############################################################################
# Trigger by position
###############################################################################

class qExafsPos(Macro):
    """
    Macro to execute the quick Exafs experiment.
    """

    env = ('ContScanMG',)
    motName = "energy"
    # motName = "oh_dcm_bragg"
    pmacName = "pmac"

    masterTriggerName = "bl22/io/ibl2202-dev1-ctr0"

    mem_overload = 1000000
    hints = {}

    param_def = [["startPos", Type.Float, None, "Starting position"],
                 ["endPos", Type.Float, None, "Ending pos value"],
                 ["nrOfTriggers", Type.Integer, None, "Nr of triggers"],
                 ["scanTime", Type.Float, None, "Scan time"],

                 ["speedLim", Type.Boolean, True, ("Active the verification "
                                                   "of the speed and "
                                                   "integration time")],
                 ["waitFE", Type.Boolean, True, ("Active the waiting for "
                                                 "opening of Front End")],

                 ["runStartup", Type.Boolean, True, 'run qExasfStartup'],
                 ["runCleanup", Type.Boolean, True, 'run qExasfCleanup'],

                 ["pmacDelay", Type.Float, 0.01, ("Delay to run the motion "
                                                  "of the speed and "
                                                  "integration time")],

                 ["acqTime", Type.Float, 99, ("Acquisition time per trigger. "
                                              "Expressed in percentage of time"
                                              " per trigger (scanTime/"
                                              "nrOfTriggers)")],
                 ["nrOfRepeats", Type.Integer, 1, "NrOfRepeats"],
                 ["backAndForth", Type.Boolean, False, ('Scan in both'
                                                        'directions')]]

    def preConfigure(self):
        self.debug("preConfigure entering...")
        self.debug('Configuring Pmac...')
        pmac = taurus.Device(self.pmacName)
        # select the compare program
        pmac.SetPVariable([4077, 2])
        # prepare encoder table
        energy_values = linspace(self.startPos, self.finalPos,
                                 self.nrOfTriggers)
        enc_values = energy_bragg_encoder(energy_values)
        first_point_register_a = enc_values[0]
        if (self.startPos < self.finalPos):
            direction = 0
            first_point_register_b = first_point_register_a + 5
        else:
            direction = 1
            first_point_register_b = first_point_register_a - 5
        pmac.SetPVariable([4075, direction])
        pmac.SetPVariable([4078, self.nrOfTriggers])
        start_buffer = int(pmac.GetPVariable(4076))
        end_buffer = start_buffer + self.nrOfTriggers
        for p_reg, value in zip(range(start_buffer, end_buffer), enc_values):
            pmac.SetPVariable([p_reg, value])

        # Configure the PLC0:
        # first point on the compare register A&B
        # set auto-increment to 0 to avoid the eneble of the compare circuit
        # set output to start on Low Level
        # update the signal output

        pmac.SetMVariable([108, first_point_register_a])
        pmac.SetMVariable([109, first_point_register_b])
        pmac.SetMVariable([110, 0])
        pmac.SetMVariable([112, 0])
        pmac.SetMVariable([111, 1])

        # enabling plc0 execution
        pmac.SetIVariable([5, 3])
        if self.run_startup:
            self.execMacro('qExafsStartupPos')
        if self.wait_fe:
            self.execMacro('waitFE')

    def postConfigure(self):
        self.debug('postConfigure entering...')
        self.debug('Setting Pmac starting delay...')
        dev = PyTango.DeviceProxy('bl22/io/ibl2202-dev1-ctr0')
        delay = dev.read_attribute('InitialDelayTime').value
        total_delay = 0
        dev.write_attribute('InitialDelayTime', delay)

    def postCleanup(self):
        self.debug("postCleanup entering...")
        pmac = taurus.Device(self.pmacName)
        # disabling plc0 execution
        pmac.SetIVariable([5, 2])

    def prepare(self, *args, **kwargs):
        # self.mg_bck = self.getEnv('ActiveMntGrp')
        mg = self.getEnv('ContScanMG')
        self.setEnv('ActiveMntGrp', mg)

    def run(self, startPos, finalPos, nrOfTriggers, scanTime, speedLim, wait_fe,
            run_startup, run_cleanup, pmac_delay, acqTime, nrOfRepeats,
            backAndForth):
        moveable = self.getMoveable(self.motName)
        int_time = scanTime / nrOfTriggers
        self.pmac_dt = pmac_delay
        if speedLim:
            if int_time < 0.5:
                raise Exception(('You must use a higher integration time '
                                 '(integration time = scanTime/nrOfTriggers).'
                                 ' The minimum value is 0.5'))
        else:
            self.warning('The speed verification is desactive')

        mem = nrOfTriggers * scanTime
        if mem > self.mem_overload:
            raise Exception(('You can not send this scan, because there is not '
                             'enough memory. The combination of the nrOfTrigger'
                             '*scanTime < 1000000'))

        self.run_startup = run_startup
        self.run_cleanup = run_cleanup
        self.wait_fe = wait_fe

        self.startPos = startPos
        self.finalPos = finalPos
        self.nrOfTriggers = nrOfTriggers
        try:
            for i in range(nrOfRepeats):
                quickScanPosCapture, pars = self.createMacro("ascanct",
                                                             moveable,
                                                             startPos,
                                                             finalPos,
                                                             nrOfTriggers,
                                                             int_time,
                                                             acqTime)
                quickScanPosCapture.hooks = [(self.preConfigure,
                                              ["pre-configuration"]),
                                             (self.postConfigure,
                                              ["post-configuration"]),
                                             (self.postCleanup,
                                              ["post-cleanup"])]
                self.debug("Running %d repetition" % i)
                self.runMacro(quickScanPosCapture)
                if backAndForth:
                    self.debug("Swapping start with end")
                    temp = startPos
                    startPos = finalPos
                    finalPos = temp

        finally:
            if self.run_cleanup:
                mg = self.getEnv('DefaultMG')
                self.setEnv('ActiveMntGrp', mg)
                self.execMacro('qExafsCleanupPos')




class qExafsStartupPos(Macro):
    """
    The macro configures the Adlink and the Ni660X for the
    continuous scan
    """

    adlinks = ['bl22/ct/adc-ibl2202-01', 'bl22/ct/adc-ibl2202-02']
    slave_triggers = ['bl22/io/ibl2202-dev1-ctr2', 'bl22/io/ibl2202-dev1-ctr4']
    counters = ['bl22/io/ibl2202-dev1-ctr6', 'bl22/io/ibl2202-dev1-ctr7',
                'bl22/io/ibl2202-dev2-ctr0', 'bl22/io/ibl2202-dev2-ctr1',
                'bl22/io/ibl2202-dev2-ctr2', 'bl22/io/ibl2202-dev2-ctr3',
                'bl22/io/ibl2202-dev2-ctr4', 'bl22/io/ibl2202-dev2-ctr5',
                'bl22/io/ibl2202-dev2-ctr6', 'bl22/io/ibl2202-dev2-ctr7']

    ni_devName = 'bl22/io/ibl2202-dev1'
    timer_trigger = '/Dev1/RTSI0'
    timer_PFI = '/Dev1/PFI36'
    master_timer = 'bl22/io/ibl2202-dev1-ctr0'

    def run(self):
        self.debug('Configuring Adlink...')
        for adlink in self.adlinks:
            adc = taurus.Device(adlink)
            if adc.State() != PyTango.DevState.STANDBY:
                adc.Stop()

        self.debug('Configuring NI660X...')
        ni_devs = self.slave_triggers + self.counters + [self.master_timer]
        for ni_dev in ni_devs:
            self.debug(ni_dev)
            dev = taurus.Device(ni_dev)
            dev.init()

        dev = PyTango.DeviceProxy(self.ni_devName)
        dev.ConnectTerms([self.timer_PFI, self.timer_trigger,
                          "DoNotInvertPolarity"])

        dev = PyTango.DeviceProxy(self.master_timer)
        dev["StartTriggerSource"] = '/Dev1/PFI39'
        dev["StartTriggerType"] = "DigEdge"

        for trigger in self.slave_triggers:
            dev = PyTango.DeviceProxy(trigger)
            dev["StartTriggerSource"] = self.timer_trigger
            dev["StartTriggerType"] = "DigEdge"

        for ni_count in self.counters:
            dev_proxy = PyTango.DeviceProxy(ni_count)
            dev_proxy.write_attribute("SampleClockSource", self.timer_trigger)
            dev_proxy.write_attribute('SampleTimingType', "SampClk")
            if self.counters.index(ni_count) > 4:
                dev_proxy.write_attribute(
                    "DataTransferMechanism", 'Interrupts')

        self.info("qExafs startup is done")




class constKscan(Macro, Hookable):
    """
    """

    param_def = [
        ['motor', Type.Moveable, None, 'Motor to move'],
        ['start_pos', Type.Float, None, 'Scan start position'],
        ['final_pos', Type.Float, None, 'Scan final position'],
        ['edge_pos', Type.Float, None, 'Edge position'],
        ['step_size_k', Type.Float, None, 'Scan step size k'],
        ['start_integ_time', Type.Float, None, 'Start integration time'],
        ['pow_integ_time', Type.Float, None, 'Power integration time']
    ]

    def __calc_pos(self, i, edge_pos, step_size_k):
        pos = edge_pos + (i * step_size_k) ** 2 / EV2REVA
        return pos

    def prepare(self, *args, **opts):
        motor = args[0]
        start_pos = args[1]
        final_pos = args[2]
        edge_pos = args[3]
        step_size_k = args[4]

        # precalculate positions to get know nr of scan points
        self.nr_points, i = 0, 1
        while True:
            pos = self.__calc_pos(i, edge_pos, step_size_k)
            i += 1
            if pos < start_pos:
                continue
            elif pos > final_pos:
                break
            self.nr_points += 1

        generator = self._generator
        moveables = [motor]
        env = opts.get('env', {})
        constrains = [getCallable(cns) for cns in
                      opts.get('constrains', [UNCONSTRAINED])]

        self.pre_scan_hooks = self.getHooks('pre-scan')
        self.post_scan_hooks = self.getHooks('post-scan')
        self._gScan = SScan(self, generator, moveables, env, constrains)

    def _generator(self):
        args = self.getParameters()
        start_pos = args[1]
        final_pos = args[2]
        edge_pos = args[3]
        step_size_k = args[4]
        start_integ_time = args[5]
        pow_integ_time = args[6]

        step = {}
        step["pre-move-hooks"] = self.getHooks('pre-move')
        step["post-move-hooks"] = self.getHooks('post-move')
        step["pre-acq-hooks"] = self.getHooks('pre-acq')
        step["post-acq-hooks"] = self.getHooks('post-acq') + self.getHooks(
            '_NOHINTS_')
        step["post-step-hooks"] = self.getHooks('post-step')

        step["check_func"] = []

        point_id, i = 0, 1
        while True:
            pos = self.__calc_pos(i, edge_pos, step_size_k)
            i += 1
            if pos < start_pos:
                continue
            elif pos > final_pos:
                break
            if point_id == 0:
                first_pos = pos
            t = start_integ_time * ((pos - edge_pos) / (
                first_pos - edge_pos)) ** (pow_integ_time * 0.5)
            step["positions"] = [pos]
            step["integ_time"] = t
            step["point_id"] = point_id
            yield step
            point_id += 1

    def run(self, *args):
        for step in self._gScan.step_scan():
            yield step

    @property
    def data(self):
        return self._gScan.data

