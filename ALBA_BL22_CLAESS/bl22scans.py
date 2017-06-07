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


# Function to detect the sardana version
def is_sardana_new():
    try:
        import sardana.pool.poolsynchronization
        return True
    except ImportError:
        return False


class BL22qExafs(object):
    """
    Class to implement the continuous scan methods. 
    """
    
    mem_overload = 1000000
    min_itime = 0.005
    energy_name = "energy"
    bragg_name = "oh_dcm_bragg"
    perp_name = 'oh_dcm_perp'
    pmac_name = 'pmac'
    pmac_ctrl_name = 'controller/dcmturbopmaccontroller/dcm_pmac_ctrl'
    adlinks_names = ['bl22/ct/adc-ibl2202-01', 'bl22/ct/adc-ibl2202-02']
    ni_trigger_name = 'bl22/io/ibl2202-dev1-ctr0'
    sard_trigger_name = 'triggergate/ni_tg_ctrl/1'

    def __init__(self, macro):
        self.sardana_new = is_sardana_new()
        self.macro = macro
        self.pmac = taurus.Device(self.pmac_name)
        self.pmac_ctrl = taurus.Device(self.pmac_ctrl_name)
        self.energy = taurus.Device(self.energy_name)
        self.perp = taurus.Device(self.perp_name)
        self.bragg = taurus.Device(self.bragg_name)
        self.sard_trigger = None
        self.ni_trigger = None
        self.adlinks = None
        self.flg_post_move = False
        self.int_time = None
        self.nr_of_triggers = None
        self.scan_start_pos = None
        self.scan_end_pos = None
        self.config_PID = True
        self.wait_fe = True
        self.flg_cleanup = False

        if self.sardana_new:
            self.sard_trigger = taurus.Device(self.sard_trigger_name)
        else:
            self.adlinks = []
            for adlink_name in self.adlinks_names:
                self.adlinks.append(taurus.Device(adlink_name))
            self.ni_trigger = taurus.Device(self.ni_trigger_name)

    def check_parameters(self, speed_check=True):
        scan_time = self.int_time * self.nr_of_triggers
        if speed_check:
            if self.int_time < self.min_itime:
                raise Exception(('You must use a higher integration time.'
                                 'The minimum value is %r' % self.min_itime))
        else:
            self.warning('The speed verification is not active')

        mem = self.nr_of_triggers * scan_time
        if mem > self.mem_overload:
            raise Exception(('You can not send this scan, because there is not '
                             'enough memory. The combination of the nrOfTrigger'
                             '*scanTime < 1000000'))

    def prepare_pmac_plc0(self):
        self.macro.info('Configuring Pmac...')
        # Configure the start trigger from the pmac. This should be moved to
        # the pmac trigger controller.
        bragg_spu = self.bragg['step_per_unit'].value
        bragg_offset = self.bragg['offset'].value
        bragg_pos = float(self.pmac.SendCtrlChar("P").split()[0])
        bragg_enc = float(self.pmac.GetMVariable(101))

        th1 = self.energy.CalcAllPhysical([self.scan_start_pos])[0]
        offset_counts = bragg_pos - bragg_enc + (bragg_offset * bragg_spu)

        start_enc = (th1 * bragg_spu) - offset_counts
        if start_enc > overflow_pmac:
            start_enc = start_enc - 2 * overflow_pmac
        elif start_enc < -overflow_pmac:
            start_enc = start_enc + 2 * overflow_pmac

        if (self.scan_start_pos < self.scan_end_pos):
            self.direction = long(0)
        else:
            self.direction = long(1)
        self.pmac.SetPVariable([PMAC_REGISTERS['MotorDir'], self.direction])
        self.pmac.SetPVariable([PMAC_REGISTERS['StartPos'], long(start_enc)])

        if not self.sardana_new:
            # configuring position capture control
            self.pmac.SetIVariable([7012, 2])
            # configuring position capture flag select
            self.pmac.SetIVariable([7013, 3])
            # after enabling position capture, M117 is set to 1, forcing readout
            # of M103, to reset it, so PLC0 won't copy outdated data
            self.pmac.GetMVariable(103)
            # enabling plc0 execution
            self.pmac.SetIVariable([5, 3])

    def prepare_couters(self):
        self.macro.info('Preparing counters...')
        if not self.sardana_new:
            self.macro.debug('Configuring Adlink...')
            for adlink in self.adlinks:
                if adlink.State() != PyTango.DevState.STANDBY:
                    adlink.Stop()
            self.macro.ni_config_counter('continuous')

    def prepare_trigger(self):
        self.macro.info('Preparing triggers...')
        if self.sardana_new:
            # Configure the Ni660XTrigger
            ni_state = self.sard_trigger.state()
            if ni_state != PyTango.DevState.ON:
                self.sard_trigger.stop()
            self.sard_trigger['slave'] = True
            self.sard_trigger['retriggerable'] = False
        else:
            output_signals = ['/DEV1/C0O', '/DEV1/C0A',
                              '/DEV1/C1O', '/DEV1/C1A', '/DEV1/RTSI0']
            self.ni_connect_channels(output_signals)
            # Channel 0 source
            self.ni_trigger['StartTriggerSource'] = '/Dev1/PFI39'
            self.ni_trigger['StartTriggerType'] = 'DigEdge'

    def prepare_pmac_motors(self, final_pos=None):
        self.macro.info('Preparing Bragg and Perp')
        if self.sardana_new:
            # Configure motor protection Sardana Bug
            bragg_offset = self.bragg['offset'].value
            bragg_sign = self.bragg['sign'].value
            perp_offset = self.perp['offset'].value
            perp_sign = self.perp['sign'].value

            bragg_final, perp_final = final_pos
            bragg_dial = bragg_sign * bragg_final - bragg_offset
            perp_dial = perp_sign * perp_final - perp_offset

            self.pmac_ctrl['NextPosition'] = [bragg_dial, perp_dial]
            self.pmac_ctrl['UseqExafs'] = True

        # TODO verify calculation of the start position on gscan
        # We need to move relative the bragg to solve the problem.
        if self.direction:
            self.macro.execMacro('mvr oh_dcm_bragg -0.005')
        else:
            self.macro.execMacro('mvr oh_dcm_bragg 0.005')

        if self.config_PID:
            self.macro.setPID('new')


    def pre_configure_hook(self):
        self.prepare_pmac_plc0()
        self.prepare_couters()
        self.prepare_trigger()

        if self.wait_fe:
            try:
                self.waitFE()
            except Exception as e:
                raise RuntimeError( 'There was an exception with the waitFE '
                                    'macro: %s' % e)

    def pre_start_hook(self, final_pos=None):
        self.prepare_pmac_motors(final_pos)

    def post_move_hook(self):
        self.macro.setPID('old')
        self.flg_post_move = True

    def cleanup(self):
        self.macro.debug('Restore Default Measurement Group')
        mg = self.macro.getEnv('DefaultMG')
        self.macro.setEnv('ActiveMntGrp', mg)

        if self.sardana_new:
            ni_state = self.sard_trigger.state()
            if ni_state != 'ON':
                self.sard_trigger.stop()
            self.sard_trigger['slave'] = False
            self.sard_trigger['retriggerable'] = False
        else:
            for adlink in self.adlinks:
                if adlink.State() != PyTango.DevState.STANDBY:
                    adlink.Stop()
                else:
                    adlink.Init()
                adlink.getAttribute("TriggerSources").write("SOFT")
                adlink.getAttribute("TriggerMode").write(0)
                adlink.getAttribute("TriggerInfinite").write(0)

            output_signals = ['/DEV1/C0O', '/DEV1/C0A',
                              '/DEV1/C1O', '/DEV1/C1A', '/DEV1/RTSI0']
            self.macro.ni_connect_channels(output_signals)
            self.macro.ni_config_counter('step')

        self.macro.restorePmac()

        self.macro.info("qExafs cleanup is done")
        self.flg_cleanup = True

    def run_scan(self, start_pos, end_pos, nr_of_trigger, int_time,
                 speed_check, wait_fe, config_pid, nr_repeat=1, 
                 back_forth=False):

        self.scan_start_pos = start_pos
        self.scan_end_pos = end_pos
        self.nr_of_triggers = nr_of_trigger
        self.int_time = int_time
        self.config_PID = config_pid
        self.check_parameters(speed_check)
        self.wait_fe = wait_fe
        if back_forth:
            nr_repeat *= 2

        if self.sardana_new:
            macro_name = 'ascanct'
        else:
            macro_name = 'ascanct_ni'

        try:
            for i in range(nr_repeat):
                self.flg_post_move = False
                self.flg_cleanup = False
                scan_macro, pars = self.macro.createMacro(macro_name,
                                                          self.energy_name,
                                                          start_pos, end_pos,
                                                          nr_of_trigger,
                                                          int_time)

                scan_macro.hooks = [(self.pre_configure_hook,
                                     ["pre-configuration"]),
                                    (self.post_configure_hook,
                                     ["post-configuration"]),
                                    (self.pre_start_hook,
                                     ["pre-start"]),
                                    (self.post_move_hook,
                                     ["post-move"]),
                                    (self.cleanup,
                                     ["post-cleanup"]),]

                self.macro.debug("Running %d repetition" % i)
                self.macro.runMacro(scan_macro)
                if back_forth:
                    self.macro.debug("Swapping start with end")
                    start_pos, end_pos = end_pos, start_pos

        except Exception as e:
            self.macro.error('Exception: %s' % e)
            
        finally:
            if not self.flg_cleanup:
                self.cleanup()

    def run_qexafs(self, start_pos, end_pos, nr_trigger, int_time, speed_check, 
                   wait_fe, config_pid, mythen=False):

        if mythen:
            mg = self.macro.getEnv('ContqMythenMG')
        else:
            mg = self.macro.getEnv('ContScanMG')
        self.macro.setEnv('ActiveMntGrp', mg)
        self.macro.execMacro('feauto 1')

        self.run_scan(start_pos, end_pos, nr_trigger, int_time, speed_check,
                      wait_fe, config_pid)


# ******************************************************************************
#                          Continuous Scan Macros
# ******************************************************************************

class qExafs(Macro):
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

        qexafs = BL22qExafs(self)
        qexafs.run_qexafs(startPos, finalPos, nrOfTriggers, intTime, speedLim,
                          wait_fe, config_PID)


class qMythen(Macro):
    """
    Macro to execute the quick Exafs experiment.
    """

    env = ('ContqMythenMG',)

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

    def run(self, startPos, finalPos, nrOfTriggers, intTime, speedLim,
            wait_fe, config_pid):

        qexafs = BL22qExafs(self)
        qexafs.run_qexafs(startPos, finalPos, nrOfTriggers, intTime, speedLim,
                          wait_fe, config_pid, mythen=True)


class qExafsCleanup(Macro):
    """
    Macro to cleanup the system after a qExafs scan.
    """
    def run(self):
        qexafs = BL22qExafs(self)
        qexafs.cleanup()


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


