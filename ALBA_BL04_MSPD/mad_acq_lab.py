import time
import PyTango, taurus
from sardana.macroserver.macro import *

COUNTERS = ["zreszela/io/ictlael01-dev1-ch1",
            "zreszela/io/ictlael01-dev1-ch2",
            "zreszela/io/ictlael01-dev1-ch3",
            "zreszela/io/ictlael01-dev1-ch4",
            "zreszela/io/ictlael01-dev1-ch5",
           ]

TRIGGER = "zreszela/io/ictlael01-dev1-ch6"
TRIGGER_DEVICE = "zreszela/io/ictlael01-dev1"
TRIGGER_SOURCE = "/Dev1/PFI12"
TRIGGER_DESTINATION = "/Dev1/RTSI0"

MNT_GRP = "counters"

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
        
class InitCounters(Macro):
    
    param_def = []
    
    def run(self, *args, **kwargs):
        for channelName in COUNTERS:
            channel = taurus.Device(channelName)
            channel.Init()    

class mad_ct(Macro):
    
    param_def = [["time", Type.Float, 1.0, "Acq time"]]

    def run(self, *args, **kwargs):
        time = args[0]
        oldMntGrp = self.getEnv("ActiveMntGrp")
        self.setEnv("ActiveMntGrp", MNT_GRP)
        self.execMacro("PrepareCountersForStepScanning")
        try:
            self.execMacro("ct", time)
        finally:
            self.setEnv("ActiveMntGrp", oldMntGrp)

class mad_ascan(Macro):
    
    param_def = [ ['motor',      Type.Moveable,  None, 'Moveable to move'],
              ['start_pos',  Type.Float,   None, 'Scan start position'],
              ['final_pos',  Type.Float,   None, 'Scan final position'],
              ['nr_interv',  Type.Integer, None, 'Number of scan intervals'],
              ['integ_time', Type.Float,   None, 'Integration time']
             ]

    def run(self, *args, **kwargs):
        mot = args[0]
        StartPos =  args[1]
        EndPos   =  args[2]
        Npts      = args[3]
        intTim    = args[4]      
        args = (mot.name,StartPos,EndPos,Npts,intTim)
        oldMntGrp = self.getEnv("ActiveMntGrp")
        self.setEnv("ActiveMntGrp", MNT_GRP)
        self.execMacro("PrepareCountersForStepScanning")
        try:
            self.execMacro('ascan', *args)
        finally: 
            self.execMacro("senv", "ActiveMntGrp", mntGrp)
