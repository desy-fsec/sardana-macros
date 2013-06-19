import time
import PyTango, taurus
from sardana.macroserver.macro import *

COUNTERS = ["bl04/io/ibl0403-dev2-ctr0",
            "bl04/io/ibl0403-dev2-ctr1",
            "bl04/io/ibl0403-dev2-ctr2", 
            "bl04/io/ibl0403-dev2-ctr3",
            "bl04/io/ibl0403-dev2-ctr4",
            "bl04/io/ibl0403-dev2-ctr5",
            "bl04/io/ibl0403-dev2-ctr6",
            "bl04/io/ibl0403-dev2-ctr7",
            "bl04/io/ibl0403-dev3-ctr0",
            "bl04/io/ibl0403-dev3-ctr1",
            "bl04/io/ibl0403-dev3-ctr2",
            "bl04/io/ibl0403-dev3-ctr3",
            "bl04/io/ibl0403-dev3-ctr4",
            "bl04/io/ibl0403-dev3-ctr5"]

TRIGGER = "bl04/io/ibl0403-dev3-ctr6"
TRIGGER_DEVICE = "bl04/io/ibl0403-dev3"
TRIGGER_SOURCE = "/Dev3/PFI12"
TRIGGER_DESTINATION = "/Dev3/RTSI0"

MNT_GRP = "mad"

class PrepareGating(Macro):

    param_def = []

    def run(self, *args, **kwargs):
        dev = taurus.Device(TRIGGER_DEVICE)
        dev.ConnectTerms([TRIGGER_SOURCE, TRIGGER_DESTINATION, "DoNotInvertPolarity"])

class CleanupGating(Macro):

    param_def = []

    def run(self, *args, **kwargs):
        dev = taurus.Device(TRIGGER_DEVICE)
        dev.DisconnectTerms([TRIGGER_SOURCE, TRIGGER_DESTINATION])

class PrepareMaster(Macro):

    param_def = []

    def run(self, *args, **kwargs):
        timerChannel = taurus.Device(TRIGGER)
        if timerChannel.State() != PyTango.DevState.STANDBY:
            timerChannel.Stop()
        timerChannel.getAttribute("InitialDelayTime").write(0)
        timerChannel.getAttribute("SampleMode").write("Finite")
        timerChannel.getAttribute("SampleTimingType").write("Implicit")
        timerChannel.getHWObj().write_attribute("SampPerChan", long(1))
        timerChannel.getAttribute("IdleState").write("Low")        
        timerChannel.getAttribute("LowTime").write(0.0000001)        

class PrepareSlaves(Macro):
    
    param_def = []

    def run(self, *args, **kwargs):
        for channelName in COUNTERS:
            channel = taurus.Device(channelName)
            if channel.State() != PyTango.DevState.STANDBY:
                channel.Stop()
            channel.getAttribute("PauseTriggerType").write("DigLvl")
            channel.getAttribute("PauseTriggerWhen").write("Low")
            channel.getAttribute("PauseTriggerSource").write(TRIGGER_DESTINATION)

class PrepareCountersForStepScanning(Macro):

    param_def = []

    def run(self, *args, **kwargs):
        self.execMacro("PrepareMaster")
        self.execMacro("PrepareSlaves")
        self.execMacro("PrepareGating")