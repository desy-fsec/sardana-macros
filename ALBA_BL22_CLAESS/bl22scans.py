import math

from sardana.macroserver.macro import Type, Macro, Hookable
from sardana.macroserver.scan import SScan
from sardana.macroserver.macros.scan import ascan, getCallable, UNCONSTRAINED
import taurus
import PyTango
from math import sqrt

EV2REVA = 0.2624682843


class constKscan(Macro, Hookable):
    """"""

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
            if point_id == 0: first_pos = pos
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


class qExafs(Macro):
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
        # configuring position capture control
        pmac.SetIVariable([7012, 2])
        # configuring position capture flag select
        pmac.SetIVariable([7013, 3])
        # after enabling position capture, M117 is set to 1, forcing readout
        # of M103, to reset it, so PLC0 won't copy outdated data
        pmac.GetMVariable(103)
        # enabling plc0 execution
        pmac.SetIVariable([5, 3])
        if self.run_startup:
            self.execMacro('qExafsStartup')
        if self.wait_fe:
            self.execMacro('waitFE')

    def postConfigure(self):
        self.debug('postConfigure entering...')
        self.debug('Setting Pmac starting delay...')
        dev = PyTango.DeviceProxy('bl22/io/ibl2202-dev1-ctr0')
        delay = dev.read_attribute('InitialDelayTime').value
        total_delay = delay + self.pmac_dt
        dev.write_attribute('InitialDelayTime', total_delay)

    def postCleanup(self):
        self.debug("postCleanup entering...")
        pmac = taurus.Device(self.pmacName)
        # setting position capture control to its default value
        pmac.SetIVariable([7012, 1])
        # setting position capture flag select to its default value
        pmac.SetIVariable([7013, 0])
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

        try:
            for i in range(nrOfRepeats):
                quickScanPosCapture, pars = self.createMacro("ascanct_ni",
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
                self.execMacro('qExafsCleanup')


class qExafsStartup(Macro):
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

        for trigger in self.slave_triggers:
            dev = PyTango.DeviceProxy(trigger)
            dev["StartTriggerSource"] = self.timer_trigger
            dev["StartTriggerType"] = "DigEdge"

        for ni_count in self.counters:
            dev_proxy = PyTango.DeviceProxy(ni_count)
            dev_proxy.write_attribute("SampleClockSource", self.timer_trigger)
            dev_proxy.write_attribute('SampleTimingType', "SampClk")
            if self.counters.index(ni_count) > 4:
                dev_proxy.write_attribute("DataTransferMechanism", 'Interrupts')

        self.info("qExafs startup is done")


class qExafsCleanup(Macro):
    param_def = []
    adlinks = ['bl22/ct/adc-ibl2202-01', 'bl22/ct/adc-ibl2202-02']
    triggers = ['bl22/io/ibl2202-dev1-ctr0', 'bl22/io/ibl2202-dev1-ctr2',
                'bl22/io/ibl2202-dev1-ctr4']
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
        ni_devs = self.triggers + self.counters
        for ni_dev in ni_devs:
            dev = taurus.Device(ni_dev)
            dev.init()
        #             if dev.State() != PyTango.DevState.STANDBY:
        #                 dev.Stop()

        dev = PyTango.DeviceProxy(self.ni_devName)
        dev.ConnectTerms([self.timer_PFI, self.timer_trigger,
                          "DoNotInvertPolarity"])

        dev_timer = PyTango.DeviceProxy(self.master_timer)
        dev_timer.write_attribute('InitialDelayTime', 0)
        dev_timer.write_attribute('LowTime', 0.001)
        dev_timer.write_attribute('SampPerChan', long(1))

        for ni_count in self.counters:
            dev_proxy = PyTango.DeviceProxy(ni_count)
            dev_proxy.write_attribute("PauseTriggerType", "DigLvl")
            dev_proxy.write_attribute('PauseTriggerSource', self.timer_trigger)
            dev_proxy.write_attribute("PauseTriggerWhen", "Low")

        self.info("qExafs cleanup is done")


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

class ascanE(Macro):
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
        macro_ascan, _ = self.createMacro('ascan',motor, start_pos, final_pos,
                                       nr_interv,integ_time)

        macro_ascan.hooks = [(self.pre_acquisition, ["pre-acq"]),]

        self.runMacro(macro_ascan)
