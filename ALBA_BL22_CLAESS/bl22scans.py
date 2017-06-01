from sardana.macroserver.macro import Type, Macro, Hookable
from sardana.macroserver.scan import SScan
from sardana.macroserver.macros.scan import ascan, getCallable, UNCONSTRAINED
import taurus
import PyTango
from numpy import sqrt


PMAC_REGISTERS = {'MotorDir': 4080, 'StartBuffer': 4081, 'RunProgram': 4082,
                  'NrTriggers': 4083, 'Index': 4084, 'StartPos': 4085,
                  'PulseWidth': 4086, 'AutoInc': 4087}

EV2REVA = 0.2624682843
c = 299792458
h = 4.13566727*10**(-15)
aSi = 5.43102088*10**(-10) # Simo macro su spec
overflow_pmac = 8388608

class BL22ContScan(object):
    """
    Class to implement the continuous scan methods. 
    """
    
    mem_overload = 1000000
    min_itime = 0.005
    motName = "energy"
    braggName = "oh_dcm_bragg"
    pmac = taurus.Device('pmac')
    pmacName = 'pmac'
    nitriggerName = 'triggergate/ni_tg_ctrl/1'
    pmac_ctr = taurus.Device('controller/dcmturbopmaccontroller/dcm_pmac_ctrl')
    perp = taurus.Device('oh_dcm_perp')

    def _check_parameters(self, itime, nr_triggers, speed_check=True):
        stime = itime * nr_triggers
        if speed_check:
            if itime < self.min_itime:
                raise Exception(('You must use a higher integration time.'
                                 'The minimum value is %r' % self.min_itime))
        else:
            self.warning('The speed verification is not active')

        mem = nr_triggers * stime
        if mem > self.mem_overload:
            raise Exception(('You can not send this scan, because there is not '
                             'enough memory. The combination of the nrOfTrigger'
                             '*scanTime < 1000000'))


    def _pre_configure_hook(self):
        self.debug("preConfigure entering...")
        if self.flg_pmac:
            self.debug('Configuring Pmac...')
            #TODO configure the NI to wait the external trigger
            if self.flg_time_trigger:
                energy_motor = self.getMoveable(self.motName)
                bragg_motor = self.getMoveable(self.braggName)
                bragg_spu = bragg_motor.read_attribute('step_per_unit').value
                bragg_offset = (bragg_motor.read_attribute('offset').value) * bragg_spu
                bragg_pos = float(self.pmac.SendCtrlChar("P").split()[0])
                bragg_enc = float(self.pmac.GetMVariable(101))
                th1 = energy_motor.CalcAllPhysical([self.startPos])[0]
                offset = bragg_pos - bragg_enc + bragg_offset

                start_enc = (th1*bragg_spu) - offset
                if start_enc > overflow_pmac:
                    start_enc = start_enc - 2 * overflow_pmac
                elif start_enc < -overflow_pmac:
                    start_enc = start_enc + 2 * overflow_pmac
                
                if (self.startPos < self.finalPos):
                    self.direction = long(0)
                else:
                    self.direction = long(1)
                self.pmac.SetPVariable([PMAC_REGISTERS['MotorDir'], self.direction])
                self.pmac.SetPVariable([PMAC_REGISTERS['StartPos'], long(start_enc)])

                # Configure the Ni660XTrigger
                ni_tg = self.getDevice(self.nitriggerName)
                self.info(ni_tg.state())
                ni_tg.stop()
                ni_tg['slave'] = True
                ni_tg['retriggerable'] = False

        if self.wait_fe:
            try:
                self.execMacro('waitFE')
            except Exception as e:
                self.error('There was an exception with the waitFE macro: '
                           '%s' % e)
                raise RuntimeError()

    def _pre_strat_hook(self, final_pos):
        self.debug('preStart entering....')
        if self.flg_pmac:
            self.info('Configure ctrl')
            bragg = taurus.Device(self.braggName)

            # Modified the CTScan to save the final position as object variable
            bragg_offset = bragg['offset'].value
            bragg_sign = bragg['sign'].value
            perp_offset = self.perp['offset'].value
            perp_sign = self.perp['sign'].value

            bragg_final, perp_final = final_pos
            bragg_dial = bragg_sign* bragg_final - bragg_offset
            perp_dial = perp_sign * perp_final - perp_offset

            self.pmac_ctr['NextPosition'] = [bragg_dial, perp_dial]
            self.pmac_ctr['UseqExafs'] = True

            if not self.config_PID:
                self.info('Did not config bragg PID')
                return
            
            self.info(bragg.velocity)
            #TODO verify calculation of the start position on gscan
            # We need to move relative the bragg to solve the problem.
            if self.direction:
                self.execMacro('mvr oh_dcm_bragg -0.005')
            else:
                self.execMacro('mvr oh_dcm_bragg 0.005')                

            
            self.info('Configuring bragg PID....')

            # TODO Load from file the configuration
            #Kp I130
            self.pmac.SetIVariable([130, 30000])
            #Kd I131
            self.pmac.SetIVariable([131, 375])
            #Kvff I132
            self.pmac.SetIVariable([132, 30000])
            #K1 I133
            self.pmac.SetIVariable([133, 5000])
            #IM I134
            self.pmac.SetIVariable([134, 0])
            #Kaff I135
            self.pmac.SetIVariable([135, 3500])



    def _post_move_hook(self):
        self.debug('postMove entering....')
        if self.flg_pmac:
            self.info('load PID default config')
            self.execMacro('configpmac')

            # Configure the Ni660XTrigger to default
            ni_tg = self.getDevice(self.nitriggerName)
            self.info(ni_tg.state())
            ni_tg.stop()
            ni_tg['slave'] = False
            ni_tg['retriggerable'] = False
            
            self.flg_post_move = True
    
    def run_scan(self, motor, start_pos, end_pos, nr_trigger, int_time, 
                 speed_check, wait_fe, config_pid, nr_repeat=1, 
                 back_forth=False):
        
        self._check_parameters(int_time, nr_trigger, speed_check)
        try:
            self.config_PID = config_pid
            self.flg_post_move = False
            self.wait_fe = wait_fe
            
            if back_forth:
                nr_repeat *= 2

            for i in range(nr_repeat):
                scan_macro, pars = self.createMacro("ascanct", motor,
                                                    start_pos, end_pos,
                                                    nr_trigger, int_time)
                scan_macro.hooks = [(self._pre_configure_hook, 
                                     ["pre-configuration"]),
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
            
        finally:
            # if self.run_cleanup:
            #    self.execMacro('qExafsCleanup') 
            if self.flg_pmac and not self.flg_post_move:
                self._post_move_hook()
    
    def run_qexafs(self, start_pos, end_pos, nr_trigger, int_time, speed_check, 
              wait_fe, config_pid, time_mode=True, mythen=False):

                                            
        self.startPos = start_pos
        self.finalPos = end_pos
        self.nrOfTriggers = nr_trigger

        self.flg_pmac = True
        self.flg_time_trigger = time_mode

        if mythen:
            mg = self.getEnv('ContqMythenMG')
        else:
            mg = self.getEnv('ContScanMG')
        self.setEnv('ActiveMntGrp', mg)
        self.execMacro('feauto 1')
       
        motor = self.getMoveable(self.motName)
       
        self.run_scan(motor, start_pos, end_pos, nr_trigger, int_time,
                      speed_check, wait_fe, config_pid)





#*******************************************************************************
# Continuous Scan Macros
#*******************************************************************************

class qExafs(Macro, BL22ContScan):
    """
    Macro to execute the quick Exafs experiment.
    """

    env = ('ContScanMG',)

    hints = {}

    param_def = [["startPos", Type.Float, None, "Starting position"],
                 ["endPos", Type.Float, None, "Ending pos value"],
                 ["nrOfTriggers", Type.Integer, None, "Nr of triggers"],
                 ["intTime", Type.Float, None, "Integration time per point"],

                 ["speedLim", Type.Boolean, True, ("Active the verification "
                                                   "of the speed and "
                                                   "integration time")],
                 ["waitFE", Type.Boolean, True, ("Active the waiting for "
                                                 "opening of Front End")],
                 
                 ["configPID", Type.Boolean, True, ("Active the configuration"
                                                 " of the bragg PID ")]]


    def run(self, startPos, finalPos, nrOfTriggers, intTime, speedLim, wait_fe,
            config_PID):
        
        self.run_qexafs(startPos, finalPos, nrOfTriggers,intTime,speedLim, 
                        wait_fe, config_PID)

class qMythen(Macro, BL22ContScan):
    """
    Macro to execute the quick Exafs experiment.
    """

    env = ('ContqMythenMG',)

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
        
        self.run_qexafs(startPos, finalPos, nrOfTriggers,scanTime,speedLim,
                        wait_fe, config_PID, mythen=True)



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


