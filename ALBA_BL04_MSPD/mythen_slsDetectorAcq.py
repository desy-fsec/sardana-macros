import time
import os
import Queue
import PyTango
import taurus
import math
import taurus

from sardana.macroserver.macro import Macro, Type, ParamRepeat
from sardana.taurus.core.tango.sardana.pool import StopException
from macro_utils.slsdetector import SlsDetectorGet, SlsDetectorPut, \
    SlsDetectorAcquire, SlsDetectorProgram, MythenReadoutTime
from macro_utils.macroutils import MntGrpController, SoftShutterController, \
    MoveableController

ERROR_PARAMETER = "It was not able to retrieve the desired parameter"
MYTHEN_DS = 'bl04/ct/slsdetectormythen'


def splitStringIntoLines(string, delimeter):
    '''Splits string into lines.'''

    splitted_lines = []
    lines = string.split(delimeter)
    for line in lines:
        if len(line) != 0:
            splitted_lines.append(line)
    return splitted_lines


def selectPulseResolution(expTime, readTime):
    highTimes = [25e-9, 100e-9,
                 20e-6]  # [25ns, 100ns, 20us]; [80MHz, 20MHz, 100kHz]
    maxLowTimes = [53.687091162499996, 214.74836464999998, 42949.67294]

    period = expTime + readTime

    for ht, mlt in zip(highTimes, maxLowTimes):
        lt = period - ht
        if lt < mlt:
            return ht, lt
    raise Exception("Too high exposure time. Max is 42949 seconds.")


def mythenAcquireSlsDS(macro):
    full_cmd = 'sls_detector_acquire'
    slsDetectorDS = taurus.Device(MYTHEN_DS)
    slsDetectorDS.ExecAsync(full_cmd)
    full_out = []
    full_err = []
    while True:
        out = slsDetectorDS.read_attribute('stdOutput').value
        err = slsDetectorDS.read_attribute('stdError').value
        if out == None:
            out = []
        if err == None:
            err = []

        out_new = list(set(out) - set(full_out))
        err_new = list(set(err) - set(full_err))
        full_out = out
        full_err = err
        if len(out_new) > 0:
            macro.debug("outLine: " + str(out_new))
        if len(err_new) > 0:
            macro.debug("errLine: " + str(err_new))
        lenOutLine = len(out_new)
        lenErrLine = len(err_new)
        time.sleep(0.1)
        # if lenOutLine != 0:
        #    macro.output(outLine)
        # if lenErrLine != 0:
        #    macro.error(errLine)

        if slsDetectorDS.state() == PyTango.DevState.ON and lenOutLine == 0 \
                and lenErrLine == 0:
            break


class MythenBase(object):
    ATTRS = ['stdOutput', 'stdError']

    def __init__(self, full_cmd=None, macro=None):
        self.full_cmd = full_cmd
        if self.full_cmd is not None:
            try:
                self.cmd = self.full_cmd.split()[1]
            except:
                self.cmd = None
        self.macro = macro
        self.listener = None
        self.listener_state = None
        self.slsDetectorDS = taurus.Device(MYTHEN_DS)

    def ExecSynch(self, full_cmd=None):
        if full_cmd is not None:
            self.full_cmd = full_cmd
            self.cmd = self.full_cmd.split()[1]

        val = self._execCommand()
        return val

    def _execCommand(self):
        val = None

        self.slsDetectorDS.ExecSync(self.full_cmd)

        errLine = self.slsDetectorDS.read_attribute('stdError').value
        outLine = self.slsDetectorDS.read_attribute('stdOutput').value

        if errLine is None:
            errLine = []
        if outLine is None:
            outLine = []
        lenOutLine = len(outLine)
        lenErrLine = len(errLine)
        if lenOutLine != 0:
            for line in outLine:
                if self.cmd in line:
                    # example of output: "threshold 10015"
                    try:
                        val = self.splitResult(line)
                    except Exception as e:
                        self.error("Could not parse '%s' output: %s" % (
                            self.full_cmd, line))
                        raise e
                else:
                    self.macro.output(line)
        if lenErrLine != 0:
            self.macro.error(errLine)

        if val is None:
            raise Exception("It was not able to retrieve %r." % self.cmd)
        return val

    def subcribeState(self, listener):
        if listener is not None:
            self.listener_state = listener
            a = taurus.Attribute(MYTHEN_DS + '/State')
            a.addListener(listener)

    def acquire(self, listener=None):
        if listener is not None:
            self.listener = listener
            for attr in self.ATTRS:
                a = taurus.Attribute(MYTHEN_DS + '/' + attr)
                a.addListener(listener)
        self.slsDetectorDS.ExecAsync(self.full_cmd)

    def disconnectListeners(self):
        try:
            if self.listener is not None:
                for attr in self.ATTRS:
                    a = taurus.Attribute(MYTHEN_DS + '/' + attr)
                    a.removeListener(self.listener)
                self.listener = None

            if self.listener_state is not None:
                a = taurus.Attribute(MYTHEN_DS + '/state')
                a.removeListener(self.listener_state)
                self.listener_state = None
        except Exception as e:
            self.macro.warning(e)

    def state(self):
        state = self.slsDetectorDS.state()
        return state

    def splitResult(self, outLine):
        return self.evaluate(outLine.split()[1])

    def evaluate(self, s):

        # Evaluate if the result is integer, float or string.
        try:
            return eval(s)
        except Exception as e:
            return s

    def abort(self):
        self.slsDetectorDS.Abort()
        self.disconnectListeners()

    def read_output(self):
        return self.slsDetectorDS.read_attribute('stdOutput').value

    def read_error(self):
        return self.slsDetectorDS.read_attribute('stdError').value


class __mythen_acquire(Macro):
    """
    Acquires images with mythen detector. If positions are set it will go
    to positions and acquire one frame per position.
    """

    result_def = [
        ['OutFile', Type.String, None, 'Full path to the output file'],
        ['Positions', Type.String, None,
         'Positions where acquisition took place']]

    POSITION_STR = 'Current position is'
    MOTOR_NAME = 'pd_mc'

    FILTERS = ['Current position is', ' %']

    def _obtainPositionFromLine(self, line):
        '''parse output/error lines for existence of current positions'''

        position = None
        if line is not None:
            if self.POSITION_STR in line:
                str_parts = line.split(self.POSITION_STR)
                position_str = str_parts[1]
                try:
                    position = float(position_str)
                except ValueError as e:
                    self.debug('Position present in the positions string line '
                               'had an invalid literal.')
        return position

    # def _splitStringIntoLines(self, string):
    #     '''split string into lines'''
    #     lines = []
    #     cr_splitted_strings = splitStringIntoLines(string, '\r')
    #     for string in cr_splitted_strings:
    #         nl_splitted_lines = splitStringIntoLines(string, '\n')
    #         lines.extend(nl_splitted_lines)
    #     return lines

    def _isInfoLine(self, line):
        """filters output/error line for existence of interesting info"""
        if line is not None:
            for filter in self.FILTERS:
                if filter in line:
                    return True
        return False

    def prepare(self, *args, **kwargs):
        self.output_acq = []
        self.error_acq = []
        self.mythen_process_state = None
        self.acquired = False
        full_cmd = 'sls_detector_acquire'
        self.mythen_obj = MythenBase(full_cmd, macro=self)

    def acqListener(self, s, t, v):

        if t == taurus.core.taurusbasetypes.TaurusEventType.Config:
            return

        if s in self.fakeevents:
            if v.value is not None:
                self.output_acq.append(v.value)
        else:
            self.fakeevents.append(s)

    def stateListener(self, s, t, v):

        # self.warning(v.value)
        if t == taurus.core.taurusbasetypes.TaurusEventType.Config:
            return

        if s not in self.fakeevents:
            self.fakeevents.append(s)
        else:
            if v.value is not None:
                if v.value == PyTango.DevState.RUNNING:
                    self.acquired = True
                self.mythen_process_state = v.value

    def run(self, *args, **kwargs):
        self.fakeevents = []

        positions_str = self.execMacro('__mythen_getPositions').getResult()
        positions = eval(positions_str)
        positions_len = len(positions)
        current_positions = []
        self.getMotion([self.MOTOR_NAME])
        motor = self.getMotor(self.MOTOR_NAME)
        if positions_len != 0:
            is_motor_powered = motor.read_attribute('poweron').value
            if not is_motor_powered:
                raise Exception('Motor: %s is powered off.' % self.MOTOR_NAME)
            self.warning("Motor: %s will move to %s" % (
                self.MOTOR_NAME, repr(positions)))
        try:
            self.mythen_obj.subcribeState(self.stateListener)
            self.mythen_obj.acquire(listener=self.acqListener)
            self.mythen_obj.state()
            while True:
                self.checkPoint()

                if len(self.output_acq) > 0:
                    while self.output_acq:
                        line = self.output_acq.pop(0)
                        self.debug('StdOut: %s' % line)
                        # filtering output lines
                        # if self._isInfoLine(line):
                        #     self.output(line.strip())
                        # obtaining current positions
                        if positions_len != 0:
                            position = self._obtainPositionFromLine(line)
                            if position != None:
                                current_positions.append(position)

                if len(self.error_acq) > 0:
                    while self.error_acq:
                        line = self.error_acq.pop(0)
                        self.debug('StdErr: %s' % line)
                        # self.error(line.strip())

                # self.mythen_obj.state()
                if self.mythen_process_state == PyTango.DevState.ON and \
                        self.acquired:
                    self.error(self.mythen_process_state)
                    self.debug("slsDetectorDS has finished.")
                    break
                else:
                    time.sleep(0.02)
        finally:

            # This sleep is to avoid Tango 7 issue:
            # https://sourceforge.net/p/tango-cs/bugs/659/
            # note, delete and test it with Tango 8 or above
            time.sleep(0.06)
            self.mythen_obj.disconnectListeners()

        outDir = self.execMacro("__mythen_getOutDir").getResult()
        outFileName = self.execMacro("__mythen_getOutFileName").getResult()
        outIndex = self.execMacro("__mythen_getIndex").getResult()
        outPath = outDir + "/" + outFileName + "_" + str(outIndex - 1) + ".dat"

        if positions_len != len(current_positions):
            self.warning('Number of the positions reported by' +
                         ' sls_detector_acquire does not correspond to' +
                         ' number of the requested positions.')

        if len(current_positions) == 0:
            current_positions.append(motor.position)
            self.warning(current_positions)

        return_positions_str = repr(current_positions)
        return outPath, return_positions_str

    def on_abort(self):
        self.output("mythen_acquire: on_abort() entering...")
        full_cmd = 'sls_detector_put status stop'
        self.mythen_obj.ExecSynch(full_cmd=full_cmd)

        self.mythen_obj.Abort()

        self.output(self.mythen_obj.read_output())
        self.error(self.mythen_obj.read_error())


class __mythen_softscan(Macro, MoveableController,
                        SoftShutterController):  # , MntGrpController):

    param_def = [['motor', Type.Motor, None, 'Motor to scan'],
                 ['start_pos', Type.Float, None, 'Start position'],
                 ['end_pos', Type.Float, None, 'End position'],
                 ['time', Type.Float, None, 'Count time']]

    def checkParams(self, args):
        self.debug("__mythen_sofscan.checkParams(%s) entering..." % repr(args))
        motor = args[0]
        motName = motor.name
        allowedMotors = ["pd_mc"]
        if motName not in allowedMotors:
            raise Exception("Wrong motor. Allowed motors are: %s." %
                            repr(allowedMotors))
        self.debug("__mythen_softscan.checkParams(%s) leaving..." % repr(args))

    def prepare(self, *args):
        self.debug("__mythen_softscan. preparing entering...")
        self.checkParams(args)

        self.motor = args[0]
        self.start_pos = args[1]
        self.end_pos = args[2]
        self.count_time = args[3]
        self.acqTime = self.count_time

        # backup of the position and set empty posiiton
        macro_tmp = "__mythen_getPositions"
        self.pos_bck = self.execMacro(macro_tmp).getResult()
        self.execMacro("__mythen_setPositions")
        # backup timing
        macro_tmp = "__mythen_getTiming"
        self.timing_bck = self.execMacro(macro_tmp).getResult()
        self.execMacro("__mythen_setTiming  auto")
        # Prepare Shuttter
        SoftShutterController.init(self)
        self.prepareShutter()
        # Prepare Motor
        MoveableController.init(self, self.motor)
        const_vel_time = self.count_time
        self.prepareMotion(const_vel_time, self.start_pos, self.end_pos)

    def run(self, *args, **kwargs):
        self.debug("__mythen_softscan. run entering...")
        count_time = args[3]
        try:
            self.moveToPrestart()
            self.openShutter()
            # self.info("starting AcqMntGrp  ...")
            # self.acquireMntGrp()

            self.moveToPostend()
            self.info("Waiting, movement and acquisition in progress...")
            self.execMacro('__mythen_setExpTime', count_time)
            self.execMacro(
                "__mythen_take True %f %f" % (self.start_pos, self.end_pos))

            # sleep_time = self.accTime
            # time.sleep(sleep_time)
            # self.openShutter()
            # outFileName = self.execMacro("mythen_acquire").getResult()
            # self.info("Data stored: %s" % outFileName)

            # self.waitMntGrp()
            # self.closeShutter()
            # time.sleep(sleep_time)

        finally:

            self.info("Cleanup...")
            self.closeShutter()
            # cleanup to False because we don't need that motor return
            # to start position
            self.cleanup(False)

    def on_abort(self):
        self.debug("__mythen_softscan.on_abort() entering...")
        self.info("on_abort() entering...")
        self.closeShutter()
        self.cleanup()


class __mythen_timeResolved(Macro, MntGrpController):
    param_def = [['time', Type.Float, None, 'Total experiment time'],
                 ['expTime', Type.Float, None, 'Exposure time per frame']]

    MYTHEN_TRIG_DEVICE = ['bl04/io/ibl0403-dev2-ctr1', 'CICountEdgesChan',
                          'MythenTrigger']
    EXT_TRIG_DEVICE = ['bl04/io/ibl0403-dev2-ctr2', 'COPulseChanTime',
                       'ExternalTrigger']
    MASTER_TRIG_DEVICE = ['bl04/io/ibl0403-dev2-ctr4', 'COPulseChanTime',
                          'MasterTrigger']

    def _configNi(self, *args, **kwargs):
        # prepare ni application type
        self.execMacro('ni_app_change %s ' % ' '.join(self.MYTHEN_TRIG_DEVICE))
        self.execMacro('ni_app_change %s ' % ' '.join(self.EXT_TRIG_DEVICE))
        self.execMacro('ni_app_change %s ' % ' '.join(self.MASTER_TRIG_DEVICE))

        MntGrpController.init(self, self)
        experimentTime = args[0]
        self.exposureTime = args[1]

        # checking if multiple positions are configured
        # if yes, exiting
        positionsStr = self.execMacro("__mythen_getPositions").getResult()
        positions = SafeEvaluator().eval(positionsStr)
        self.debug("Positions: %s" % repr(positions))
        if len(positions) > 0:
            raise Exception(
                "Time resolved experiment is not possible with multiple positions.")

        # calculating nr of frames which mythen will be able to gather
        # during the experiment time
        dr = self.execMacro("__mythen_getDr").getResult()
        self.debug("dr: %d" % dr)
        mrt = MythenReadoutTime()
        self.readoutTime = mrt[dr]
        self.debug("readoutTime: %f" % self.readoutTime)
        timePerFrame = self.exposureTime + self.readoutTime
        self.nrOfFrames = int(math.floor(experimentTime / timePerFrame))
        self.debug("nrOfFrames: %d" % self.nrOfFrames)

        # calculating trigger pulse characteristics
        ht, lt = selectPulseResolution(self.exposureTime, self.readoutTime)

        # configuring mythen detector
        self.execMacro("__mythen_setTiming", 'trigger')
        self.execMacro("__mythen_setExtSignal", 2, "trigger_in_rising_edge")
        self.execMacro("__mythen_setNrOfTriggers", 1)
        self.execMacro("__mythen_setNrOfFramesPerTrigger", self.nrOfFrames)
        self.execMacro("__mythen_setExpTime", self.exposureTime)
        self.execMacro('__mythen_setPositions')
        self.firstIndex = self.execMacro("__mythen_getIndex").getResult()
        self.debug('FirstIndex = %d' % self.firstIndex)

        # configuring mythen trigger
        self.mythenTrigger = taurus.Device(self.MYTHEN_TRIG_DEVICE[0])
        self.mythenTrigger.write_attribute("IdleState", "Low")
        self.mythenTrigger.write_attribute("SampleTimingType", "Implicit")
        # ("SampPerChan", long(self.nrOfFrames)) is not necessary only need 1 trigger
        self.mythenTrigger.write_attribute("SampPerChan",
                                           long(self.nrOfFrames))
        # self.mythenTrigger.write_attribute("SampPerChan", long(1))
        self.mythenTrigger.write_attribute("InitialDelayTime",
                                           0)  # sec (obligatory delay is 2 ticks)
        self.mythenTrigger.write_attribute("HighTime", ht)  # sec
        self.mythenTrigger.write_attribute("LowTime", lt)  # sec
        self.mythenTrigger.write_attribute("StartTriggerSource", "/Dev1/PFI12")
        self.mythenTrigger.write_attribute("StartTriggerType", "DigEdge")

        # configuring external trigger
        self.externalTrigger = taurus.Device(self.EXT_TRIG_DEVICE[0])
        self.externalTrigger.write_attribute("IdleState", "Low")
        self.externalTrigger.write_attribute("SampleTimingType", "Implicit")
        # self.externalTrigger.write_attribute("SampPerChan", long(1))
        # ("SampPerChan", long(self.nrOfFrames)) is not necessary only need 1 trigger
        self.externalTrigger.write_attribute("SampPerChan",
                                             long(self.nrOfFrames))
        self.externalTrigger.write_attribute("InitialDelayTime",
                                             0)  # sec (obligatory delay is 2 ticks)
        self.externalTrigger.write_attribute("HighTime", 1)  # sec
        self.externalTrigger.write_attribute("LowTime", 1)  # sec
        self.externalTrigger.write_attribute("StartTriggerSource",
                                             "/Dev1/PFI12")
        self.externalTrigger.write_attribute("StartTriggerType", "DigEdge")

        # configuring master trigger
        self.masterTrigger = PyTango.DeviceProxy(self.MASTER_TRIG_DEVICE[0])
        self.masterTrigger.write_attribute("IdleState", "Low")
        self.masterTrigger.write_attribute("SampleTimingType", "Implicit")
        self.masterTrigger.write_attribute("SampPerChan", long(1))
        self.masterTrigger.write_attribute("InitialDelayTime",
                                           0)  # sec (obligatory delay is 2 ticks)
        self.masterTrigger.write_attribute("HighTime", 0.001)  # sec
        self.masterTrigger.write_attribute("LowTime", 0.001)  # sec

    def _restoreNi(self):
        self.execMacro('ni_default %s' % self.MYTHEN_TRIG_DEVICE[0])
        self.execMacro('ni_default %s' % self.EXT_TRIG_DEVICE[0])
        self.execMacro('ni_default %s' % self.MASTER_TRIG_DEVICE[0])

    def run(self, *args, **kwargs):
        import threading
        try:
            self._configNi(*args, **kwargs)

            self._event = threading.Event()

            # callback function to set Event
            def done(job_ret):
                self._event.set()

            self.mntGrpAcqTime = 0.1
            MntGrpController.prepareMntGrp(self)
            MntGrpController.acquireMntGrp(self)
            MntGrpController.waitMntGrp(self)
            firstMntGrpResults = MntGrpController.getMntGrpResults(self)

            self.getManager().add_job(mythenAcquireSlsDS, done, self)

            # self.execMacro("mythen_acquire")
            # waiting for detector till it arms
            while True:
                self.checkPoint()
                time.sleep(0.1)
                status = self.execMacro("__mythen_getStatus").getResult()
                if status == "running":
                    break
            self.debug("mythen waiting for trigger")

            self.externalTrigger.start()
            self.mythenTrigger.start()
            self.masterTrigger.start()
            self._event.wait()
            self.debug("Mythen end acq")
        finally:

            # Aborting
            status = self.execMacro("__mythen_getStatus").getResult()
            if status == "running":
                self.execMacro('__mythen_abortAcq')
            self.externalTrigger.stop()
            self.mythenTrigger.stop()
            self.masterTrigger.stop()
            self.execMacro("__mythen_setTiming", 'auto')
            self.execMacro("__mythen_setNrOfFramesPerTrigger", 0)
            self._restoreNi()

        MntGrpController.acquireMntGrp(self)
        MntGrpController.waitMntGrp(self)
        lastMntGrpResults = MntGrpController.getMntGrpResults(self)

        # generating timestamps
        outDir = self.execMacro("__mythen_getOutDir").getResult()
        outFileName = self.execMacro("__mythen_getOutFileName").getResult()
        lastIndex = self.execMacro("__mythen_getIndex").getResult()
        self.debug('lastIndex = %d' % lastIndex)

        acquiredFrames = lastIndex - self.firstIndex
        if acquiredFrames != 1:
            raise Exception(
                "Nr of acquired images does not correspond to requested value.")

        parFile = outDir + "/" + outFileName + "_" + str(
            self.firstIndex) + "-" + str(lastIndex - 1) + ".par"
        try:
            pFile = open(parFile, "w")
            pFile.write(firstMntGrpResults + "\n")
            for i in range(self.nrOfFrames):
                fileNames = outDir + "/" + outFileName + "_" + str(
                    self.firstIndex + i) + ".{raw,dat}"
                timestamp = i * (self.exposureTime + self.readoutTime)
                line = "%s : %f" % (fileNames, timestamp)
                pFile.write(line + '\n')
                self.output(line)
            extraHeader = self.execMacro("_mythpar").getResult()
            pFile.write(extraHeader + '\n')
            pFile.write('LastMngGrpResult:' + '\n')
            pFile.write(lastMntGrpResults)
        except Exception as e:
            self.error(e)
            pFile.close()
            self.output(parFile)


class __mythen_fastTake(Macro, MntGrpController):
    param_def = [
        ['expTime', Type.Float, None, 'Exposure time per frame'],
        ['frames', Type.Integer, None, 'Total number of Frames']
    ]

    # NI channels to read values while the Mythen is acquiring
    MONITOR_CHANNEL = 'bl04/io/ibl0403-dev2-ctr0'  # i14
    MONITOR_CHANNEL_GATE = '/Dev2/PFI38'  # i14 Gate
    MONITOR_CHANNEL_SOURCE = '/Dev2/PFI39'  # i14 Source
    MOTOR_NAME = 'pd_mc'

    def _configureChannel(self):
        self.monitorChannel.Init()
        self.monitorChannel.write_attribute("SourceTerminal",
                                            self.MONITOR_CHANNEL_SOURCE)
        self.monitorChannel.write_attribute("SampleClockSource",
                                            self.MONITOR_CHANNEL_GATE)
        self.monitorChannel.write_attribute("DataTransferMechanism",
                                            "Interrupts")
        self.monitorChannel.write_attribute("SampPerChan",
                                            long(self.nrOfFrames))
        self.monitorChannel.write_attribute("SampleclockRate", 100.0)

    def prepare(self, *args, **kwargs):
        MntGrpController.init(self, self)
        self.nrOfFrames = args[1]
        self.exposureTime = args[0]

        self.monitorChannel = taurus.Device(self.MONITOR_CHANNEL)
        #        self.monitorChannel.set_timeout_millis(10000)
        self.monitorChannel.Stop()

        self.debug("nrOfFrames: %d" % self.nrOfFrames)

        # configuring mythen detector

        self.execMacro("__mythen_setTiming", 'auto')
        self.execMacro("__mythen_setNrOfFramesPerTrigger", self.nrOfFrames)
        self.execMacro("__mythen_setExpTime", self.exposureTime)
        self.execMacro('__mythen_setPositions')
        self.execMacro('__mythen_setExtSignal 0 gate_out_active_high')

        self.firstIndex = self.execMacro("__mythen_getIndex").getResult()
        self.debug('FirstIndex = %d' % self.firstIndex)

        # To calculate the readOutTime
        dr = self.execMacro('__mythen_getDr').getResult()
        mrt = MythenReadoutTime()
        self.readOutTime = mrt[dr]

    def run(self, *args, **kwargs):

        self._configureChannel()
        total_time = self.nrOfFrames * (self.exposureTime + self.readOutTime)
        self.output('Collecting %s Frames of %f sec (+ %f readoutTime)' % (
            self.nrOfFrames, self.exposureTime, self.readOutTime))
        self.output('Overall time : %f sec' % (total_time))

        # why?
        import threading
        self._event = threading.Event()

        # callback function to set Event

        def done(job_ret):
            self._event.set()

            # Start the Monitor channel

        self.monitorChannel.Start()
        self.debug("Monitor channel State %s", self.monitorChannel.State())

        # Start to take frames in Mythen
        self.getManager().add_job(mythenAcquireSlsDS, done, self)

        try:
            self._event.wait()
            self.debug("Mythen end acq")

            # Read the Values of the NI
            monitorValueList = self.monitorChannel.read_attribute(
                'PulseWidthBuffer').value

            monitorValueList = list(monitorValueList)
            self.info('MonitorValuePerFrame: %s' % monitorValueList)

        finally:

            # Aborting

            status = self.execMacro("__mythen_getStatus").getResult()
            if status == "running":
                self.execMacro("__mythen_abortAcq")
            self.execMacro("__mythen_setNrOfFramesPerTrigger", 0)
            self.monitorChannel.Stop()
            position = self.execMacro("__mythen_getPositions").getResult()

        self.mntGrpAcqTime = 0.1
        MntGrpController.prepareMntGrp(self)
        MntGrpController.acquireMntGrp(self)
        MntGrpController.waitMntGrp(self)
        lastMntGrpResults = MntGrpController.getMntGrpResults(self)

        # generating timestamps
        outDir = self.execMacro("__mythen_getOutDir").getResult()
        outFileName = self.execMacro("__mythen_getOutFileName").getResult()
        lastIndex = self.execMacro("__mythen_getIndex").getResult()
        self.debug('lastIndex = %d' % lastIndex)

        acquiredFrames = lastIndex - self.firstIndex
        if acquiredFrames != 1:
            raise Exception(
                "Nr of acquired images does not correspond to requested value.")

        parFileName = outDir + "/" + outFileName + "_" + str(
            lastIndex - 1) + ".par"
        self.info(parFileName)
        try:
            motor = taurus.Device(self.MOTOR_NAME)
            position = motor.read_attribute('position').value
            parFile = open(parFileName, "w")
            parFile.write("# imon %d " % monitorValueList[0])
            if lastMntGrpResults != None:
                parFile.write(lastMntGrpResults)

            parFile.write('\nMonitor = %d' % monitorValueList[0])
            parFile.write('\nIsMon = %s' % monitorValueList)
            line = ('\nIsPos = %s' % ([round(position, 6)] * self.nrOfFrames))
            parFile.write(line)
            parFile.write('\nMythen_fastTake Pos: %s' % (position))

            extraHeader = self.execMacro("_mythpar").getResult()
            parFile.write(extraHeader)
            self.info("Metadata stored: %s" % parFileName)
        except Exception as e:
            self.error("Error while writing par file.")
            raise e
        finally:
            parFile.close()
        return outFileName, position, monitorValueList


class __mythen_take(Macro, MntGrpController):
    result_def = [
        ['OutFile', Type.String, None, 'Full path to the output file'],
        ['nrOfPositions', Type.Integer, None, 'Number of positions'],
        ['positions', Type.String, None, 'List of positions'],
        ['monitors', Type.String, None, 'Monitors']
    ]
    param_def = [
        ['softscan', Type.Boolean, False, 'It use in mythen_softscan'],
        ['startpos', Type.String, '', 'start position'],
        ['endpos', Type.String, '', 'end position']]

    MONITOR_CHANNEL = 'bl04/io/ibl0403-dev2-ctr0'  # i14
    MONITOR_CHANNEL_GATE = '/Dev2/PFI38'  # i14 Gate
    MONITOR_CHANNEL_SOURCE = '/Dev2/PFI39'  # i14 Source

    def _configureChannel(self):
        positions = self.execMacro("mythen_getPositions").getResult()
        self.spc = len(eval(positions))

        # SEP6 implementation
        self.monitorChannel.Init()
        self.monitorChannel.write_attribute("SourceTerminal",
                                            self.MONITOR_CHANNEL_SOURCE)
        self.monitorChannel.write_attribute("SampleClockSource",
                                            self.MONITOR_CHANNEL_GATE)
        self.monitorChannel.write_attribute("DataTransferMechanism",
                                            "Interrupts")

        if self.spc < 1:
            self.spc = 1
        self.monitorChannel.write_attribute("SampPerChan", long(self.spc))
        self.monitorChannel.write_attribute("SampleclockRate", 100.0)


        # OLD implementation
        # self.spc = long(len(eval(positions)))
        # if self.spc > 1:
        #    channel.write_attribute("SourceTerminal",self.MONITOR_CHANNEL_SOURCE)
        #    channel.write_attribute("SampleClockSource",self.MONITOR_CHANNEL_GATE)
        #    channel.write_attribute("SampPerChan", self.spc)
        #    channel.write_attribute("SampleclockRate", 100.0)
        # else:
        #    channel.write_attribute("PauseTriggerType", "DigLvl")
        #    channel.write_attribute("PauseTriggerWhen", "Low")
        #    channel.write_attribute("PauseTriggerSource", self.MONITOR_CHANNEL_GATE)

    def _count(self, count_time):
        '''Executes a count of the measurement group. It returns results
           or in case of exception None'''
        #        self.mntGrpAcqTime = count_time
        MntGrpController.setAcqTime(self, count_time)
        try:
            MntGrpController.prepareMntGrp(self)
            MntGrpController.acquireMntGrp(self)
        except Exception as e:
            self.warning('Exception while using measurement group')
            self.debug(e)
            return None
        finally:
            MntGrpController.waitMntGrp(self)
        results = MntGrpController.getMntGrpResults(self)
        return results

    def prepare(self, *args, **kwargs):
        MntGrpController.init(self, self)
        self.monitorChannel = PyTango.DeviceProxy(self.MONITOR_CHANNEL)
        self.monitorChannel.Stop()

        # preparing Mythen to generate gate while acquiring
        self.execMacro("__mythen_setExtSignal 0 gate_out_active_high")

    def run(self, *args, **kwargs):

        t0 = time.time()

        # 170202
        Temps = []
        tempsOut = ''
        Temp0 = ''
        snap = self.getEnv("_snap")
        if 'blower' in snap:
            Temps = ["blowerT", "blowerSP"]
            Temp0 = " T0 %.2f" % (taurus.Device(Temps[0]).value)
        if 'cryo' in snap:
            # Temps = ["cryoT","cryoSP"]
            Temps = ["cryoT", "cryoSP", "tc1"]
            Temp0 = " T0 %.2f" % (taurus.Device(Temps[0]).value)
        if 'julabo' in snap:
            Temps = ["julaboT", "julaboSP"]
            Temp0 = " T0 %.2f" % (taurus.Device(Temps[0]).value)
        if 'dyna' in snap:
            Temps = ["dynTa", "dynSP1"]
            Temp0 = " T0 %.2f" % (taurus.Device(Temps[0]).value)
        if 'elchem' in snap:
            acq_time = 0.1  ##FF18Sep2017  put 0.1 but used to be 0.05 in June 2017
            mnt_grp = 'adlink_simple'
            env_grp = 'adlinks'
            try:
                Temp0 = ''
                # a = self.execMacro('ct_custom %r %s' % (acq_time,
                # mnt_grp))
                # a = a.data
                # Temp0 = " ".join("%s %s" % tup for tup in a['data'])
                chVolt = self.execMacro(
                    'ct_custom %r %s' % (0.1, mnt_grp)).data
                self.debug("chVolt %s" % repr(chVolt))
                Vnow = [float(chVolt['data'][1][1]),
                        float(chVolt['data'][2][1]),
                        float(chVolt['data'][3][1]),
                        float(chVolt['data'][4][1])]
                Vname = [chVolt['data'][1][0], chVolt['data'][2][0],
                         chVolt['data'][3][0], chVolt['data'][4][0]]
                Vwas = self.getEnv(env_grp)
                self.error("Vwas %s" % repr(Vwas))
                self.error("Vnow %s" % repr(Vnow))
                for _v in range(len(Vwas)):
                    Vdiff = Vnow[_v] - Vwas[_v]
                    # Vis = float(chVolt['data'][_v][1])
                    # Vdiff = Vis - Vwas[_v]
                    Voff = 2.
                    if abs(Vdiff) > 1.95:
                        self.error("_v %d Vwas %.3f Vis %.3f Vdiff %.3f" % (
                            _v, Vwas[_v], Vnow[_v], Vdiff))
                        # Vnow[_v] += Vdiff/abs(Vdiff)*Voff
                        Vnow[_v] += (-1.) * Vdiff / abs(Vdiff) * Voff
                        sign, offset = self.execMacro("adlink_getFormula",
                                                      Vname[_v]).getResult()
                        newOffset = float(offset) - Vdiff / abs(Vdiff) * Voff
                        # self.execMacro("adlink_setFormula %s %f" %(Vname[_v], newOffset))
                        self.execMacro(
                            "adlink_setFormula %s %f" % (Vname[_v], newOffset))
                self.setEnv('adlinks', Vnow)
                #    Temp0 = " ".join("%s_end %s" % tup for tup in Vnow)
                res = [None] * (len(Vname) + len(Vnow))
                res[::2] = Vname
                res[1::2] = Vnow
                self.error(res)
                Temp0 = " ".join("%s " % tup for tup in res)
                # Temp0 = " ".join("%s %s" % tup for tup in chVolt['data'])
                self.warning(Temp0)

            except Exception as e:
                self.error('Error on take data in measurement Group, %r' % e)
                pass


                # Temps = ["adlink_ch00","adlink_ch01","adlink_ch02",
                # "adlink_ch03"]
                # Temp0 = " T00 %.2f,T01 %.2f,T02 %.2f,T03 %.2f"%(
                # taurus.Device(Temps[0]).value,taurus.Device(Temps[
                # 1]).value,taurus.Device(Temps[2]).value,taurus.Device(Temps[3]).value)

        softscan = args[0]
        startpos = args[1]
        endpos = args[2]

        try:

            self._configureChannel()
            self.monitorChannel.Start()
            outFileName, positions = self.execMacro(
                "__mythen_acquire").getResult()
            nrOfPositions = len(eval(positions))
            self.debug(nrOfPositions)

            # SEP6 Implementation
            monitorValueList = self.monitorChannel.read_attribute(
                'PulseWidthBuffer').value
            self.debug(monitorValueList)
            monitorValueList = list(monitorValueList)

            self.info('MonitorValuePerPosition: %s' % monitorValueList)
        except Exception as e:
            self.error('Exception during acquisition')
            self.warning(e)
            raise e
        finally:
            self.monitorChannel.Stop()
            # self._restoreChannel(self.monitorChannel)

        self.info("Data stored: %s" % outFileName)
        self.warning(
            'In mythen_take : Elapsed time : %.4f sec' % (time.time() - t0))
        t1 = time.time()

        # FF 12Dec2016 Modif to get rid of the ct in mythen_take
        try:
            countsOut = ''
            try:
                countsOut = "Iring %.2f mocoIn %.4e mocoOut %.4f" % (
                    taurus.Device('icurr').value,
                    taurus.Device('mocoIn').value,
                    taurus.Device('mocoOut').value)
                self.debug("%s" % (countsOut))
            except:
                msg = 'It was not able to read Iring  mocoIn  mocoOut Attributes'
                self.error(msg)

            # Temps  = []
            #            tempsOut = ''
            #            if 'blower' in self.getEnv("_snap") : Temps = ["blowerT","blowerSP"]
            #            if 'cryo' in self.getEnv("_snap") : Temps = ["cryoT","cryoSP"]
            for _t in Temps:
                tempsOut = tempsOut + " %s %.2f" % (t, taurus.Device(_t).value)
            tempsOut = tempsOut + Temp0

            # if 'elchem' in snap:
            if 'DONT EXECUTE elchem' in snap:

                acq_time = 0.05
                mnt_grp = 'adlink_simple'
                try:
                    Temp0 = ''
                    a = self.execMacro('ct_custom %r %s' % (acq_time, mnt_grp))
                    # a = a.getData()
                    a = a.data
                    Temp0 = " ".join("%s %s" % tup for tup in a['data'])
                    #  Temp0 = " ".join("%s_1 %s" % tup for tup in a['data'])
                    #  Temp0 = " ".join("%s_1 %s" % tup for tup in a['data'])
                    tempsOut = tempsOut + Temp0

                except:
                    self.error('Error on take data in measurement Group')
                    pass

            self.debug("%s" % (tempsOut))
        except Exception as e:
            self.debug(e)
            msg = 'It was not able to read the attributes'
            self.error(msg)
            msg = 'Attributes data will be skipped in the par file'
            self.info(msg)
        self.warning(
            'Elapsed time to get Attributes: %.4f sec' % (time.time() - t1))

        self.warning(
            'In mythen_take : Elapsed time : %.4f sec' % (time.time() - t0))
        parFileName = outFileName[:-3] + "par"
        try:
            parFile = open(parFileName, "w")
            # imon as an average
            parFile.write("# imon %d %s %s " % (
                int(sum(monitorValueList) / nrOfPositions), countsOut,
                tempsOut))

            # only the first value
            # parFile.write("# imon %d " % monitorValueList[0])
            # if mnt_grp_results != None:
            #    parFile.write(mnt_grp_results)

            parFile.write('\nMonitor = %d' % monitorValueList[0])
            parFile.write('\nIsMon = %s' % monitorValueList)
            if not softscan:
                parFile.write('\nIsPos = %s' % positions)
            else:
                parFile.write(
                    '\nMythenSoftScan Pos: %s, %s' % (startpos, endpos))

            extraHeader = self.execMacro("_mythpar").getResult()
            parFile.write(extraHeader)
            self.info("Metadata stored: %s" % parFileName)
        except Exception as e:
            self.error("Error while writing par file.")
            raise e
        finally:
            parFile.close()
        monitors = monitorValueList
        self.warning(
            'In mythen_take : Elapsed time : %.4f sec' % (time.time() - t0))

        return outFileName, nrOfPositions, str(positions), str(monitors)


class __mythen_timeResolvedAUTO(Macro, MntGrpController):
    param_def = [['time', Type.Float, None, 'Total experiment time'],
                 ['expTime', Type.Float, None, 'Exposure time per frame']]

    def prepare(self, *args, **kwargs):
        MntGrpController.init(self, self)
        self.experimentTime = args[0]
        self.exposureTime = args[1]

        # checking if multiple positions are configured
        # if yes, exiting
        positionsStr = self.execMacro("__mythen_getPositions").getResult()
        positions = SafeEvaluator().eval(positionsStr)
        self.debug("Positions: %s" % repr(positions))
        if len(positions) > 0:
            raise Exception(
                "Time resolved experiment is not possible with multiple positions.")

        # calculating nr of frames which mythen will be able to gather

        # during the experiment time

        dr = self.execMacro("__mythen_getDr").getResult()
        self.debug("dr: %d" % dr)
        mrt = MythenReadoutTime()
        self.readoutTime = mrt[dr]
        self.debug("readoutTime: %f" % self.readoutTime)
        timePerFrame = self.exposureTime + self.readoutTime
        self.nrOfFrames = int(math.floor(self.experimentTime / timePerFrame))
        self.debug("nrOfFrames: %d" % self.nrOfFrames)

        # configuring mythen detector

        self.execMacro("__mythen_setTiming", 'auto')
        # self.execMacro("mythen_setExtSignal", 2, "trigger_in_rising_edge")

        # self.execMacro("mythen_setNrOfTriggers", 1)

        self.execMacro("__mythen_setNrOfFramesPerTrigger", self.nrOfFrames)
        self.execMacro("__mythen_setExpTime", self.exposureTime)
        self.execMacro('__mythen_setPositions')
        self.firstIndex = self.execMacro("mythen_getIndex").getResult()
        self.debug('FirstIndex = %d' % self.firstIndex)

    def run(self, *args, **kwargs):
        import threading
        self._event = threading.Event()

        # callback function to set Event

        def done(job_ret):
            self._event.set()

        self.mntGrpAcqTime = 0.1
        MntGrpController.prepareMntGrp(self)
        MntGrpController.acquireMntGrp(self)
        MntGrpController.waitMntGrp(self)
        firstMntGrpResults = MntGrpController.getMntGrpResults(self)

        self.getManager().add_job(mythenAcquireSlsDS, done, self)

        # self.execMacro("mythen_acquire")
        # waiting for detector till it arms

        while True:
            self.checkPoint()
            time.sleep(0.1)
            status = self.execMacro("__mythen_getStatus").getResult()
            if status == "running":
                break
        self.debug("mythen waiting for trigger")

        try:
            # self.externalTrigger.start()
            # self.mythenTrigger.start()

            # self.masterTrigger.start()

            self._event.wait()
            self.debug("Mythen end acq")
        finally:

            # Aborting
            status = self.execMacro("__mythen_getStatus").getResult()
            if status == "running":
                self.execMacro('__mythen_abortAcq')

            # self.externalTrigger.stop()
            # self.mythenTrigger.stop()

            # self.masterTrigger.stop()
            # self.execMacro("mythen_setTiming", 'auto')
            self.execMacro("__mythen_setNrOfFramesPerTrigger", 0)

        MntGrpController.acquireMntGrp(self)
        MntGrpController.waitMntGrp(self)
        lastMntGrpResults = MntGrpController.getMntGrpResults(self)

        # generating timestamps
        outDir = self.execMacro("__mythen_getOutDir").getResult()
        outFileName = self.execMacro("__mythen_getOutFileName").getResult()
        lastIndex = self.execMacro("__mythen_getIndex").getResult()
        self.debug('lastIndex = %d' % lastIndex)

        acquiredFrames = lastIndex - self.firstIndex
        if acquiredFrames != 1:
            raise Exception(
                "Nr of acquired images does not correspond to requested value.")

        parFile = outDir + "/" + outFileName + "_" + str(
            self.firstIndex) + "-" + str(lastIndex - 1) + ".par"
        try:
            pFile = open(parFile, "w")
            pFile.write(firstMntGrpResults + "\n")
            for i in range(self.nrOfFrames):
                fileNames = outDir + "/" + outFileName + "_" + str(
                    self.firstIndex + i) + ".{raw,dat}"
                timestamp = i * (self.exposureTime + self.readoutTime)
                line = "%s : %f" % (fileNames, timestamp)
                pFile.write(line + '\n')
                self.output(line)
            extraHeader = self.execMacro("_mythpar").getResult()
            pFile.write(extraHeader + '\n')
            pFile.write('LastMngGrpResult:' + '\n')
            pFile.write(lastMntGrpResults)
        except Exception as e:
            self.error(e)
            pFile.close()
            self.output(parFile)

