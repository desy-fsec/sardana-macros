import time
import os
import Queue
import PyTango
import taurus
import math
import taurus
# import ff_mythen
# from trigger import Trigger, TimeBase
# from taurus.core.util import SafeEvaluator


from sardana.macroserver.macro import Macro, Type, ParamRepeat
from sardana.taurus.core.tango.sardana.pool import StopException
from macro_utils.slsdetector import SlsDetectorGet, SlsDetectorPut, \
    SlsDetectorAcquire, SlsDetectorProgram, MythenReadoutTime
from macro_utils.macroutils import MntGrpController, SoftShutterController, \
    MoveableController

ERROR_PARAMETER = "It was not able to retrieve the desired parameter"
MYTHEN_DS = 'bl04/ct/subprocessMythen'


def splitStringIntoLines(string, delimeter):
    '''Splits string into lines.'''

    splitted_lines = []
    lines = string.split(delimeter)
    for line in lines:
        if len(line) != 0:
            splitted_lines.append(line)
    return splitted_lines


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
            raise Exception("It was not able to retrieve %r."% self.cmd)
        return val

    def subcribeState(self, listener):
        if listener is not None:
            self.listener_state = listener
            a = taurus.Attribute(MYTHEN_DS + '/State')
            a.addListener(listener)

    def ExecAsync(self, listener=None):
        if listener is not None:
            self.listener = listener
            for attr in self.ATTRS:
                a = taurus.Attribute(MYTHEN_DS + '/' + attr)
                a.addListener(listener)
        self.slsDetectorDS.ExecAsync(self.full_cmd)

    def acquire(self, listener=None):
        self.ExecAsync(listener=listener)

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


class __mythen_getThreshold(Macro):
    """Gets mythen threshold."""

    result_def = [['threshold', Type.Integer, None, 'Threshold']]

    def run(self, *args, **kwargs):
        cmd = 'threshold'
        full_cmd = 'sls_detector_get %s' % cmd
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


class __mythen_setThreshold(Macro):
    """Sets mythen threshold."""

    param_def = [['threshold', Type.Integer, None, 'Threshold']]
    result_def = [['threshold', Type.Integer, None, 'Threshold']]

    def run(self, *args, **kwargs):
        cmd = 'threshold'
        val = str(args[0])
        full_cmd = 'sls_detector_put %s %s' % (cmd, val)
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


class __mythen_getIndex(Macro):
    """Gets index of the next output file."""

    result_def = [
        ['index', Type.Integer, None, 'Index of the next output file']]

    def run(self, *args, **kwargs):
        cmd = 'index'
        full_cmd = 'sls_detector_get %s' % cmd
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


class __mythen_setIndex(Macro):
    """Sets new index for the output file."""

    param_def = [['index', Type.Integer, None,
                  'New index of the next output file']]
    result_def = [['index', Type.Integer, None,
                   'Index of the next output file']]

    def run(self, *args, **kwargs):
        cmd = 'index'
        val = str(args[0])
        full_cmd = 'sls_detector_put %s %s' % (cmd, val)
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


class __mythen_getOutFileName(Macro):
    """Gets name of the next output file."""

    result_def = [
        ['outFileName', Type.String, None, 'Name of the next output file']]

    def run(self, *args, **kwargs):
        cmd = 'fname'
        full_cmd = 'sls_detector_get %s' % cmd
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


class __mythen_setOutFileName(Macro):
    """Sets name of the next output file."""

    param_def = [
        ['outFileName', Type.String, None, 'New name of the next output file']]
    result_def = [
        ['outFileName', Type.String, None, 'Name of the next output file']]

    def run(self, *args, **kwargs):
        cmd = 'fname'
        val = str(args[0])
        full_cmd = 'sls_detector_put %s %s' % (cmd, val)
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


class __mythen_getOutDir(Macro):
    """Gets name of the output directory."""

    result_def = [
        ['outDir', Type.String, None, 'Name of the output directory']]

    def run(self, *args, **kwargs):
        cmd = 'outdir'
        full_cmd = 'sls_detector_get %s' % cmd
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


class __mythen_setOutDir(Macro):
    """Sets name of the output directory."""

    param_def = [
        ['outDir', Type.String, None, 'New name of the output directory']]
    result_def = [
        ['outDir', Type.String, None, 'Name of the output directory']]

    def run(self, *args, **kwargs):
        cmd = 'outdir'
        val = str(args[0])
        full_cmd = 'sls_detector_put %s %s' % (cmd, val)
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


class __mythen_getExpTime(Macro):
    """Gets exposure time."""

    result_def = [['expTime', Type.String, None, 'Exposure time [s]']]

    def run(self, *args, **kwargs):
        cmd = 'exptime'
        full_cmd = 'sls_detector_get %s' % cmd
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        self.mythen_obj.splitResult = self.splitResult
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass

    def splitResult(self, outLine):
        try:
            expTime = float(outLine.split()[1])
        except Exception as e:
            self.error("Could not parse '%s' output: %s" % (
            " ".self.slsDetectorProgram.args, outLine))
            raise e
        return expTime


class __mythen_setExpTime(Macro):
    """Sets exposure time."""

    param_def = [['expTime', Type.String, None, 'New exposure time [s]']]
    result_def = [['expTime', Type.String, None, 'Exposure time [s]']]

    def run(self, *args, **kwargs):
        cmd = 'exptime'
        val = str(args[0])
        full_cmd = 'sls_detector_put %s %s' % (cmd, val)
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


class __mythen_getFlatFieldDir(Macro):
    """Gets name of the flat field directory."""

    result_def = [['flatFieldDir', Type.String, None,
                   'Name of the flat field directory']]

    def run(self, *args, **kwargs):
        cmd = 'ffdir'
        full_cmd = 'sls_detector_get %s' % cmd
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


class __mythen_setFlatFieldDir(Macro):
    """Sets name of the flat filed directory."""

    param_def = [['flatFieldDir', Type.String, None,
                  'New name of the flat field directory']]
    result_def = [['flatFieldDir', Type.String, None,
                   'Name of the flat field directory']]

    def run(self, *args, **kwargs):
        cmd = 'ffdir'
        val = str(args[0])
        full_cmd = 'sls_detector_put %s %s' % (cmd, val)
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


class __mythen_getFlatFieldFile(Macro):
    """Gets name of the flat field correction file.
       'none' - flat field correction is disabled"""

    result_def = [
        ['flatFieldFile', Type.String, None, 'Name of the flat field file']]

    def run(self, *args, **kwargs):
        cmd = 'flatfield'
        full_cmd = 'sls_detector_get %s' % cmd
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


class __mythen_setFlatFieldFile(Macro):
    """Sets name of the flat field correction file.
       'none' - disables flat field correction"""

    param_def = [['flatFieldFile', Type.String, None,
                  'New name of the flat field file']]
    result_def = [
        ['flatFieldFile', Type.String, None, 'Name of the flat field file']]

    def run(self, *args, **kwargs):
        cmd = 'flatfield'
        val = str(args[0])
        full_cmd = 'sls_detector_put %s %s' % (cmd, val)
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


class __mythen_setPositions(Macro):
    """Sets positions."""

    param_def = [['positions', ParamRepeat(
        ['position', Type.Float, None, 'Position to be moved'], min=0), None,
                  'Positions']]
    result_def = [['positions', Type.String, None, 'Position to be moved']]

    def run(self, *args, **kwargs):
        cmd = 'positions'
        positions = args[0]
        nrOfPositions = len(positions)
        positions = " ".join(str(s) for s in positions)

        full_cmd = 'sls_detector_put %s %s %s' % (cmd, nrOfPositions,
                                                  positions)
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        self.mythen_obj.splitResult = self.splitResult
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass

    def splitResult(self, outLine):

        # example of output: "positions 2 -10.00000 -20.00000"
        positions = None
        try:
            _positions = outLine.split()
            nrOfPositions = int(_positions[1])
            if nrOfPositions > 0:
                positions = _positions[2:]
                self.output(positions)
                positions = map(float, positions)
            else:
                positions = []
        except Exception as e:
            self.error("Could not parse '%s' output: %s" % (self.full_cmd,
                                                            outLine))
            raise e

        if positions is None:
            raise Exception("It was not able to retrieve positions.")
        # self.output(positions)
        return repr(positions)


class __mythen_getPositions(Macro):
    """Gets positions."""

    result_def = [['positions', Type.String, None, 'Positions to move']]

    def run(self, *args, **kwargs):
        cmd = 'positions'

        full_cmd = 'sls_detector_get %s' % cmd
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        self.mythen_obj.splitResult = self.splitResult
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass

    def splitResult(self, outLine):

        positions = None

        if "positions" in outLine:
            # example of output: "positions 2 -1.600000 -1.950000"
            _positions = outLine.split()
            nrOfPositions = _positions[1]
            if nrOfPositions > 0:
                positions = _positions[2:]
                try:
                    positions = map(float, positions)
                except Exception as e:
                    self.error("Could not parse '%s' output: %s" % (
                        self.full_cmd, outLine))
                    raise e
            else:
                positions = []
        else:
            self.output(outLine)

        if positions is None:
            raise Exception("It was not able to retrieve positions.")
        return repr(positions)

class __mythen_getStatus(Macro):
    """Gets mythen status. Return values:
       running - detector is acquiring
       error - detector is in error state
       transmitting - detector is transmitting data
       idle - detector is waiting for commands
       finished - unknown @todo
       waiting - unknown @todo"""

    result_def =  [['status', Type.String, None, 'Detector status']]

    def run(self, *args, **kwargs):
        cmd = 'status'
        full_cmd = 'sls_detector_get %s' % cmd
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s."% full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


class __mythen_getTiming(Macro):
    """Gets timing mode. Return values:
       auto - software timing
       gating - hardware gating
       trigger - hardware trigger
       complementary - unknown @todo"""

    result_def =  [['mode', Type.String, None, 'Configured timing mode']]

    def run(self, *args, **kwargs):
        cmd = 'timing'
        full_cmd = 'sls_detector_get %s' % cmd
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


class __mythen_setTiming(Macro):
    """Sets timing mode. Return values:
       auto - software timing
       gating - hardware gating
       trigger - hardware trigger
       complementary - unknown @todo"""

    param_def =  [['mode', Type.String, None, 'New timing mode']]
    result_def = [['mode', Type.String, None, 'Timing Mode']]

    def run(self, *args, **kwargs):
        cmd = 'timing'
        val = str(args[0])
        full_cmd = 'sls_detector_put %s %s' % (cmd, val)
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s."% full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


class __mythen_getExtSignal(Macro):
    """Gets external signal configuration. Return values:
       off - acquisition of software trigger
       gate_in_active_high - acquisition while signal is high
       gate_in_active_low - acquision while signal is low
       trigger_in_rising_edge - acquisition starts when transition from low to high
       trigger_in_falling_edge - acquistion start when transition from high to low
       ro_trigger_in_rising_edge - unknown
       ro_trigger_in_falling_edge - unknown
       gate_out_active_high - generates high signal while acquiring
       gate_out_active_low - generates low signal while acquiring
       trigger_out_rising_edge - generates transition form low to high when acquisition starts
       trigger_out_falling_edge - generates transition form high to low when acquisition starts
       ro_trigger_out_rising_edge - unknown,
       ro_trigger_out_falling_edge - unknown"""

    param_def = [['channelNr', Type.Integer, None, 'Channel nr']]
    result_def = [['mode', Type.String, None, 'Configured mode ']]

    def run(self, *args, **kwargs):
        cmd = 'extsig'
        full_cmd = 'sls_detector_get %s' % cmd
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        # example of output: "extsig:0 gate_in_active_high"
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


class __mythen_setExtSignal(Macro):
    """Sets external signal configuration. Return values:
       off - acquisition of software trigger
       gate_in_active_high - acquisition while signal is high
       gate_in_active_low - acquision while signal is low
       trigger_in_rising_edge - acquisition starts when transition from low to high
       trigger_in_falling_edge - acquistion start when transition from high to low
       ro_trigger_in_rising_edge - unknown
       ro_trigger_in_falling_edge - unknown
       gate_out_active_high - generates high signal while acquiring
       gate_out_active_low - generates low signal while acquiring
       trigger_out_rising_edge - generates transition form low to high when acquisition starts
       trigger_out_falling_edge - generates transition form high to low when acquisition starts
       ro_trigger_out_rising_edge - unknown,
       ro_trigger_out_falling_edge - unknown"""

    param_def = [['channelNr', Type.Integer, None, 'Channel nr'],
                 ['mode', Type.String, None, 'Mode']]

    def run(self, *args, **kwargs):
        cmd = 'extsig'
        channel = str(args[0])
        mode = str(args[1])
        full_cmd = 'sls_detector_put %s %s %s' % (cmd, channel, mode)
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


class __mythen_getNrOfTriggers(Macro):
    """Gets nr of triggers. """

    result_def = [['NrOfTriggers', Type.Integer, None, 'Nr of triggers']]

    def run(self, *args, **kwargs):
        cmd = 'cycles'
        full_cmd = 'sls_detector_get %s' % cmd
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        self.mythen_obj.splitResult = self.splitResult

        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass

    def splitResult(self, outLine):

        # example of output: "cycles 2.000000000"
        nrOfTriggers = None
        try:
            nrOfTriggers = int(float(outLine.split()[1]))
        except Exception as e:
            self.error("Could not parse '%s' output: %s" % (
            self.slsDetectorProgram.args, outLine))
            raise e
        if nrOfTriggers is None:
            raise Exception("It was not able to retrieve NrOfTriggers.")
        return nrOfTriggers


class __mythen_setNrOfTriggers(Macro):
    """Gets nr of triggers. """

    param_def = [['NrOfTriggers', Type.Integer, None, 'Nr of triggers']]
    result_def = [['NrOfTriggers', Type.Integer, None, 'Nr of triggers']]

    def run(self, *args, **kwargs):
        cmd = 'cycles'
        val = str(args[0])
        full_cmd = 'sls_detector_put %s %s' % (cmd, val)
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        self.mythen_obj.splitResult = self.splitResult
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass

    def splitResult(self, outLine):
        nrOfFramesPerTrigger = None
        # example of output: "frames 2.000000000"
        try:
            nrOfFramesPerTrigger = int(float(outLine.split()[1]))
        except Exception as e:
            self.error("Could not parse '%s' output: %s" % (self.full_cmd,
                                                            outLine))
            raise e

        if nrOfFramesPerTrigger is None:
            raise Exception(
                "It was not able to retrieve NrOfFramsePerTrigger.")
        return nrOfFramesPerTrigger


class __mythen_getNrOfFramesPerTrigger(Macro):
    """Gets nr of frames per trigger. """

    result_def = [['NrOfFramesPerTrigger', Type.Integer, None,
                   'Nr of frames per trigger']]

    def run(self, *args, **kwargs):
        cmd = 'frames'
        full_cmd = 'sls_detector_get %s' % cmd
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        self.mythen_obj.splitResult = self.splitResult
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass

    def splitResult(self, outLine):

        nrOfFramesPerTrigger = None
        # example of output: "frames 2.000000000"
        try:
            nrOfFramesPerTrigger = int(float(outLine.split()[1]))
        except Exception as e:
            self.error("Could not parse '%s' output: %s" % (self.full_cmd,
                                                            outLine))
            raise e

        if nrOfFramesPerTrigger is None:
            raise Exception(
                "It was not able to retrieve NrOfFramsePerTrigger.")
        return nrOfFramesPerTrigger


class __mythen_setNrOfFramesPerTrigger(Macro):
    """Gets nr of frames per trigger. """

    param_def = [['NrOfFramesPerTrigger', Type.Integer, None,
                  'Nr of frames per trigger']]

    result_def = [['NrOfFramesPerTrigger', Type.Integer, None,
                   'Nr of frames per trigger']]

    def run(self, *args, **kwargs):
        cmd = 'frames'
        val = str(args[0])
        full_cmd = 'sls_detector_put %s %s' % (cmd, val)
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        self.mythen_obj.splitResult = self.splitResult
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass

    def splitResult(self, outLine):

        val = None
        # example of output: "frames 2.000000000"
        try:
            val = int(float(outLine.split()[1]))
        except Exception as e:
            self.error("Could not parse '%s' output: %s" % (self.full_cmd,
                                                            outLine))
            raise e

        if val is None:
            raise Exception(
                "It was not able to retrieve NrOfFramsePerTrigger.")
        return val


class __mythen_getNrOfGates(Macro):
    """Gets nr of frames per trigger. """

    result_def = [['NrOfGates', Type.Integer, None, 'Nr of gates']]

    def run(self, *args, **kwargs):
        cmd = 'gates'
        full_cmd = 'sls_detector_get %s' % cmd
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        self.mythen_obj.splitResult = self.splitResult
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass

    def splitResult(self, outLine):
        val = None
        # example of output: "frames 2.000000000"
        try:
            val = int(float(outLine.split()[1]))
        except Exception as e:
            self.error("Could not parse '%s' output: %s" % (self.full_cmd,
                                                            outLine))
            raise e

        if val is None:
            raise Exception(
                "It was not able to retrieve NrOfFramsePerTrigger.")
        return val


class __mythen_setNrOfGates(Macro):
    """Gets nr of frames per trigger. """

    param_def = [['NrOfGates', Type.Integer, None, 'Nr of gates']]
    result_def = [['NrOfGates', Type.Integer, None, 'Nr of gates']]

    def run(self, *args, **kwargs):
        cmd = 'gates'
        val = str(args[0])
        full_cmd = 'sls_detector_put %s %s' % (cmd, val)
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        self.mythen_obj.splitResult = self.splitResult
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass

    def splitResult(self, outLine):
        val = None
        # example of output: "gates 2.000000000"
        try:
            val = int(float(outLine.split()[1]))
        except Exception as e:
            self.error("Could not parse '%s' output: %s" % (self.full_cmd,
                                                            outLine))
            raise e

        if val is None:
            raise Exception("It was not able to retrieve NrOfGates.")
        return val


class __mythen_getBinSize(Macro):
    """Gets binning size."""

    result_def = [['binsize', Type.Float, None, 'Binning size']]

    def run(self, *args, **kwargs):
        cmd = 'binsize'
        full_cmd = 'sls_detector_get %s' % cmd
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


class __mythen_setBinSize(Macro):
    """Sets binning size."""

    param_def = [['binSize', Type.String, None, 'Binning size']]
    result_def = [['binsize', Type.Float, None, 'Binning size']]


    def run(self, *args, **kwargs):
        cmd = 'binsize'
        val = str(args[0])
        full_cmd = 'sls_detector_put %s %s' % (cmd, val)
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


class __mythen_getDr(Macro):
    """Gets dynamic range."""

    result_def = [['dr', Type.Integer, None, 'Dynamic range']]

    def run(self, *args, **kwargs):
        cmd = 'dr'
        full_cmd = 'sls_detector_get %s' % cmd
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        mrt = MythenReadoutTime()
        readOutTime = mrt[val]
        self.info('ReadOutTime = %f sec' % (readOutTime))
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


class __mythen_setDr(Macro):
    """Sets dynamic range."""

    param_def = [['dr', Type.String, None, 'Dynamic range']]
    result_def = [['dr', Type.Integer, None, 'Dynamic range']]

    def run(self, *args, **kwargs):
        cmd = 'dr'
        val = str(args[0])
        full_cmd = 'sls_detector_put %s %s' % (cmd, val)
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


class __mythen_getSettings(Macro):
    """Gets settings."""

    result_def = [['settings', Type.String, None, 'Settings']]

    def run(self, *args, **kwargs):
        cmd = 'settings'
        full_cmd = 'sls_detector_get %s' % cmd
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


class __mythen_setSettings(Macro):
    """Sets settings."""

    param_def = [['settings', Type.String, None, 'Settings type']]

    def run(self, *args, **kwargs):
        cmd = 'settings'
        val = str(args[0])
        full_cmd = 'sls_detector_put %s %s' % (cmd, val)
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


class __mythen_getScan0Prec(Macro):
    """Gets mythen threshold."""

    result_def = [['parval', Type.Integer, None, 'Threshold']]

    def run(self, *args, **kwargs):
        cmd = 'scan0prec'
        full_cmd = 'sls_detector_get %s' % cmd
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


class __mythen_setScan0Prec(Macro):
    """Gets mythen threshold."""

    param_def = [['parval', Type.Integer, None, 'Parameter to set']]
    result_def = [['parval', Type.Integer, None, 'Parameter to set']]

    def run(self, *args, **kwargs):
        cmd = 'scan0prec'
        val = str(args[0])
        full_cmd = 'sls_detector_put %s %s' % (cmd, val)
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass




class __mythen_getScan0Script(Macro):
    """Gets mythen Scan0Script."""

    result_def =  [['parval',Type.String, None, 'Threshold']]

    def run(self, *args, **kwargs):
        cmd = 'scan0script'
        full_cmd = 'sls_detector_get %s' % cmd
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


class __mythen_setScan0Script(Macro):
    """Gets mythen Scan0Script."""

    param_def =  [['parval',Type.String, None, 'Parameter to set']]
    result_def =  [['parval',Type.String, None, 'Parameter to set']]

    SCRIPTS_ALLOW = ['position','threshold', 'energy', 'trimbits']


    def prepare(self, *args, **kwargs):
        parval = args[0]
        parval = parval.lower()
        if parval not in self.SCRIPTS_ALLOW:
            s = str(self.SCRIPTS_ALLOW)
            msg = 'The type %s is not Allowed, try: %s'%(parval, s)
            self.error(msg)
            raise ValueError

    def run(self, *args, **kwargs):
        cmd = 'scan0script'
        val = str(args[0])
        full_cmd = 'sls_detector_put %s %s' % (cmd, val)
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s."% full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


class __mythen_getScan1Script(Macro):
    """Gets mythen Scan0Script."""

    result_def =  [['parval',Type.String, None, 'Threshold']]

    def run(self, *args, **kwargs):
        cmd = 'scan1script'
        full_cmd = 'sls_detector_get %s' % cmd
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass

class __mythen_setScan1Script(Macro):
    """Gets mythen Scan1Script."""

    param_def = [['parval',Type.String, None, 'Parameter to set']]
    result_def = [['parval',Type.String, None, 'Parameter to set']]

    SCRIPTS_ALLOW = ['position', 'threshold', 'energy', 'trimbits', 'none']


    def prepare(self, *args, **kwargs):
        parval = args[0]
        parval = parval.lower()
        if parval not in self.SCRIPTS_ALLOW:
            s = str(self.SCRIPTS_ALLOW)
            msg = 'The type %s is not Allowed, try: %s' %(parval, s)
            self.error(msg)
            raise ValueError

    def run(self, *args, **kwargs):
        cmd = 'scan1script'
        val = str(args[0])
        full_cmd = 'sls_detector_put %s %s' % (cmd, val)
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s."% full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


class __mythen_getAngcallog(Macro):
    """Gets mythen AngCalLog."""

    result_def =  [['parval',Type.Integer, None, 'Threshold']]

    def run(self, *args, **kwargs):
        cmd = 'angcallog'
        full_cmd = 'sls_detector_get %s' % cmd
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass

class __mythen_setAngcallog(Macro):
    """Sets mythen AngCalLog."""

    param_def = [['parval',Type.Integer, None, 'Parameter to set']]
    result_def = [['parval',Type.Integer, None, 'Parameter to set']]

    def run(self, *args, **kwargs):
        cmd = 'angcallog'
        val = str(args[0])
        full_cmd = 'sls_detector_put %s %s' % (cmd, val)
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s."% full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass




class __mythen_getScan0Range(Macro):
    """Gets mythen Scan0Range."""

    result_def =  [['parval',Type.String, None, 'par value']]

    def run(self, *args, **kwargs):
        cmd = 'scan0range'
        full_cmd = 'sls_detector_get %s' % cmd
        self.mythen_obj = MythenBase(full_cmd, macro=self)

        # use the custom splitResult
        self.mythen_obj.splitResult = self.splitResult
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s."% full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


    def splitResult(self, outLine):
        _parval = outLine.split()
        nrparval = _parval[1]
        if nrparval > 0 :
           parval = _parval[2:]
           try:
             parval = map(float,parval)
           except Exception as e:
             self.error("Could not parse '%s' output: %s" % (
                 self.slsDetectorProgram.args, outLine))
             raise e
        else :
            parval = []

        return repr(parval)


class __mythen_setScan0Range(Macro):
    """Sets mythen Scan0Range."""

    param_def = [['positions', ParamRepeat(['position', Type.Float, None,
                                            'Position to be moved'], min=0),
                  None, 'Positions']]
    result_def =  [['parval',Type.String, None, 'Parameter to set']]

    def run(self, *args, **kwargs):
        cmd = 'scan0script'
        positions = map(str, args)
        positions = ' '.join(str(s) for s in positions)

        self.nrpositions = len(positions)
        full_cmd = 'sls_detector_put %s %s' % (cmd, positions)
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        self.mythen_obj.splitResult = self.splitResult
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass

    def splitResult(self, outLine):
        _parval = outLine.split()
        nrparval = _parval[1]
        if nrparval > 0:
            parval = _parval[2:]
            try:
                parval = map(float, parval)
            except Exception as e:
                self.error("Could not parse '%s' output: %s" % (
                self.full_cmd, outLine))
                raise e
        else:
            parval = []

        return repr(parval)


class __mythen_getAngConv(Macro):
    """Gets the constants used for angular convertion."""

    result_def = [['fnOut', Type.String, "", '[Filename to print the result]']]

    def run(self, *args, **kwargs):
        cmd = 'angconv'
        full_cmd = 'sls_detector_get %s' % cmd
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


class __mythen_getBadChannels(Macro):
    """Gets the bad channels."""

    result_def = [
        ['filename', Type.String, "", 'Filename to print the result']]

    def run(self, *args, **kwargs):
        cmd = 'badchannels'
        full_cmd = 'sls_detector_get %s' % cmd
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


class __mythen_setBadChannels(Macro):
    """Gets the bad channels."""

    param_def = [['newFileName', Type.String, None, 'Bad channel file name']]
    result_def = [['ackFileName', Type.String, None,
                   'Acknowledged bad channel file name']]

    def prepare(self, *args, **kwargs):
        self.badChannelFilename = args[0]
        if self.badChannelFilename != 'none':
            if not os.path.isfile(self.badChannelFilename):
                raise Exception(
                    'File %s does not exist.' % self.badChannelFilename)

    def run(self, *args, **kwargs):
        cmd = 'badchannels'
        val = str(args[0])
        full_cmd = 'sls_detector_put %s %s' % (cmd, val)
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


class __mythen_getGlobalOff(Macro):
    """Gets the global offset used for angular conversion."""

    result_def = [['globaloff', Type.Float, None, 'Global Offset']]

    def run(self, *args, **kwargs):
        cmd = 'globaloff'
        full_cmd = 'sls_detector_get %s' % cmd
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


class __mythen_setGlobalOff(Macro):
    """Gets the global offset used for angular conversion."""

    param_def = [['globaloff', Type.Float, 0, 'Global Offset']]
    result_def = [['globaloff', Type.Float, None, 'Global Offset']]

    def run(self, *args, **kwargs):
        cmd = 'globaloff'
        val = str(args[0])
        full_cmd = 'sls_detector_put %s %s' % (cmd, val)
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass


class __mythen_setConfig(Macro):
    """Sets configuration from file."""

    param_def = [
        ['confFileName', Type.String, '/homelocal/opbl04/bl04mythen.conf',
         'Configuration file name']]

    def prepare(self, *args, **kwargs):
        confFileName = args[0]
        if not os.path.isfile(confFileName):
            raise Exception('File %s does not exist.' % confFileName)

    def run(self, *args, **kwargs):
        cmd = 'config'
        confFileName = args[0]

        full_cmd = 'sls_detector_put %s %s' % (cmd, confFileName)
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        self.mythen_obj.ExecAsync()
        time.sleep(.1)
        slsDetectorDS =  self.mythen_obj.slsDetectorDS
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
            lenOutLine = len(out_new)
            lenErrLine = len(err_new)

            if lenOutLine > 0:
                self.output(str(out_new))
            if lenErrLine > 0:
                self.error(str(err_new))

            time.sleep(0.1)
            if slsDetectorDS.state() == PyTango.DevState.ON and lenOutLine == 0 \
                    and lenErrLine == 0:
                break

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass




class __mythen_getEncallog(Macro):
    """Gets mythen Encallog."""

    result_def =  [['parval',Type.Integer, None, 'Threshold']]

    def run(self, *args, **kwargs):
        cmd = 'encallog'

        full_cmd = 'sls_detector_get %s' % cmd
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s." % full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass



class __mythen_setEncallog(Macro):

    param_def = [['parval',Type.Integer, None, 'Parameter to set']]
    result_def = [['parval',Type.Integer, None, 'Parameter to set']]

    def run(self, *args, **kwargs):
        cmd = 'encallog'
        val = str(args[0])
        full_cmd = 'sls_detector_put %s %s' % (cmd, val)
        self.mythen_obj = MythenBase(full_cmd, macro=self)
        val = self.mythen_obj.ExecSynch()
        if val is None:
            raise Exception("It was not able to retrieve %s."% full_cmd)
        return val

    def abort(self):
        try:
            self.mythen_obj.abort()
        except Exception as e:
            pass

