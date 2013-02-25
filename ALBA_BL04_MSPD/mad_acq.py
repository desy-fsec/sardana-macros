import time
import taurus
from sardana.macroserver.macro import *

DEV2_CHANNELS = ["bl04/io/ibl0403-dev2-ctr0",
                 "bl04/io/ibl0403-dev2-ctr1",
                 "bl04/io/ibl0403-dev2-ctr2", 
                 "bl04/io/ibl0403-dev2-ctr3",
                 "bl04/io/ibl0403-dev2-ctr4",
                 "bl04/io/ibl0403-dev2-ctr5",
                 "bl04/io/ibl0403-dev2-ctr6",
                 "bl04/io/ibl0403-dev2-ctr7"]

DEV3_CHANNELS = ["bl04/io/ibl0403-dev3-ctr0",
                 "bl04/io/ibl0403-dev3-ctr1",
                 "bl04/io/ibl0403-dev3-ctr2",
                 "bl04/io/ibl0403-dev3-ctr3",
                 "bl04/io/ibl0403-dev3-ctr4",
                 "bl04/io/ibl0403-dev3-ctr5"]
                 
MAD_MNT_GRP = "mad"

class PrepareGating(Macro):

    param_def = []

    def run(self, *args, **kwargs):
        dev = taurus.Device("bl04/io/ibl0403-dev3")
        dev.ConnectTerms(["/Dev3/PFI12", "/Dev3/RTSI0", "DoNotInvertPolarity"])

class CleanupGating(Macro):

    param_def = []

    def run(self, *args, **kwargs):
        dev = taurus.Device("bl04/io/ibl0403-dev3")
        dev.DisconnectTerms(["/Dev3/PFI12", "/Dev1/RTSI0"])

class PrepareMaster(Macro):

    param_def = []

    def run(self, *args, **kwargs):
        activeMntGrpName = self.getEnv("ActiveMntGrp")
        mntGrp = taurus.Device(activeMntGrpName)
        timerName = mntGrp.getAttribute("ElementList").read().value[0]
        self.debug(timerName)
        timer = taurus.Device(timerName)
        timerChannelName = timer.getAttribute("channelDevName").read().value
        timerChannel = taurus.Device(timerChannelName)
        timerChannel.getAttribute("InitialDelayTime").write(4)
        timerChannel.getAttribute("SampleMode").write("Finite")
        timerChannel.getAttribute("SampleTimingType").write("Implicit")
        timerChannel.getHWObj().write_attribute("SampPerChan", long(1))
        timerChannel.getAttribute("IdleState").write("Low")        
        timerChannel.getAttribute("LowTime").write(0.0000001)        

class PrepareSlaves(Macro):
    
    param_def = []

    def run(self, *args, **kwargs):
        #activeMntGrpName = self.getEnv("ActiveMntGrp")
        #mntGrp = taurus.Device(activeMntGrpName)
        #counterNames = mntGrp.getAttribute("ElementList").read().value[1:]
        #self.debug(counterNames)
        
        #counters = []
        #for counterName in counterNames:
            #self.debug("counterName: %s" % counterName)
            #counters.append(taurus.Device(counterName))
        #self.debug(len(counters))
        #channels = []
        #for counter in counters:
            #channelName = counter.getAttribute("channelDevName").read().value
            #self.debug("channelName: %s" % channelName)
            #channels.append(taurus.Device(channelName))
        channels = []
        for channelName in DEV2_CHANNELS:
            channels.append(taurus.Device(channelName))

        for channel in channels:
            self.debug(repr(channel))
            channel.getAttribute("PauseTriggerType").write("DigLvl")
            channel.getAttribute("PauseTriggerWhen").write("Low")
            channel.getAttribute("PauseTriggerSource").write("/Dev2/RTSI0")

        channels = []
        for channelName in DEV3_CHANNELS:
            channels.append(taurus.Device(channelName))

        for channel in channels:
            self.debug(repr(channel))
            channel.getAttribute("PauseTriggerType").write("DigLvl")
            channel.getAttribute("PauseTriggerWhen").write("Low")
            channel.getAttribute("PauseTriggerSource").write("/Dev3/RTSI0")

class StartTestCount(Macro):

    param_def = []

    def run(self, *args, **kwargs):
        ch0 = taurus.Device("bl04/io/ibl0403-dev2-ctr0")
        ch1 = taurus.Device("bl04/io/ibl0403-dev2-ctr1")
        channels = [ch0, ch1]
        for channel in channels:
            channel.getAttribute("HighTicks").write(400000)
            channel.getAttribute("LowTicks").write(400000)
            channel.getAttribute("SampleMode").write("Cont")
        for channel in channels:
            channel.start()


class StopTestCount(Macro):

    param_def = []

    def run(self, *args, **kwargs):
        ch2 = taurus.Device("bl04/io/ibl0403-dev2-ctr0")
        ch3 = taurus.Device("bl04/io/ibl0403-dev2-ctr1")
        channels = [ch2, ch3]
        for channel in channels:
            channel.stop()

class PrepareScan(Macro):

    param_def = []

    def run(self, *args, **kwargs):
        self.execMacro("PrepareMaster")
        self.execMacro("PrepareSlaves")
        self.execMacro("PrepareGating")

class InitCounters(Macro):

    param_def = []

    def run(self, *args, **kwargs):
        ni660x_timer = taurus.Device("it")
        ni660x_timer.getAttribute("channelDevName").write("bl04/io/ibl0403-dev3-ctr6")
        ni660x_ch0 = taurus.Device("i1")
        ni660x_ch0.getAttribute("channelDevName").write("bl04/io/ibl0403-dev2-ctr0")
        ni660x_ch1 = taurus.Device("i2")
        ni660x_ch1.getAttribute("channelDevName").write("bl04/io/ibl0403-dev2-ctr1")
        ni660x_ch2 = taurus.Device("i3")
        ni660x_ch2.getAttribute("channelDevName").write("bl04/io/ibl0403-dev2-ctr2")
        ni660x_ch3 = taurus.Device("i4")
        ni660x_ch3.getAttribute("channelDevName").write("bl04/io/ibl0403-dev2-ctr3")
        ni660x_ch4 = taurus.Device("i5")
        ni660x_ch4.getAttribute("channelDevName").write("bl04/io/ibl0403-dev2-ctr4")
        ni660x_ch5 = taurus.Device("i6")
        ni660x_ch5.getAttribute("channelDevName").write("bl04/io/ibl0403-dev2-ctr5")
        ni660x_ch6 = taurus.Device("i7")
        ni660x_ch6.getAttribute("channelDevName").write("bl04/io/ibl0403-dev2-ctr6")
        ni660x_ch6 = taurus.Device("i8")
        ni660x_ch6.getAttribute("channelDevName").write("bl04/io/ibl0403-dev2-ctr7")
        ni660x_ch6 = taurus.Device("i9")
        ni660x_ch6.getAttribute("channelDevName").write("bl04/io/ibl0403-dev3-ctr0")
        ni660x_ch6 = taurus.Device("i10")
        ni660x_ch6.getAttribute("channelDevName").write("bl04/io/ibl0403-dev3-ctr1")
        ni660x_ch6 = taurus.Device("i11")
        ni660x_ch6.getAttribute("channelDevName").write("bl04/io/ibl0403-dev3-ctr2")
        ni660x_ch6 = taurus.Device("i12")
        ni660x_ch6.getAttribute("channelDevName").write("bl04/io/ibl0403-dev3-ctr3")
        ni660x_ch6 = taurus.Device("i13")
        ni660x_ch6.getAttribute("channelDevName").write("bl04/io/ibl0403-dev3-ctr4")
        ni660x_ch6 = taurus.Device("i14")
        ni660x_ch6.getAttribute("channelDevName").write("bl04/io/ibl0403-dev3-ctr5")
        

class CreateCounters(Macro):

    param_def = []

    def run(self, *args, **kwargs):
        self.execMacro("defelem", "it", "mad26_ct_ctrl", 1)
        time.sleep(1)
        for i in range(14):
            self.execMacro("defelem", "i%d" % i, "mad26_ct_ctrl", i+2)
            time.sleep(1)

class mad_ct(Macro):
    
    param_def = [["time", Type.Float, 1.0, "Acq time"]]

    def run(self, *args, **kwargs):
        time = args[0]
        mntGrp = self.getEnv("ActiveMntGrp")
        self.execMacro("senv", "ActiveMntGrp", MAD_MNT_GRP)
        self.execMacro("PrepareMaster")
        self.execMacro("PrepareSlaves")
        self.execMacro("PrepareGating")
        try:
            self.execMacro("ct", time)
        finally:
            self.execMacro("CleanupGating")
            self.execMacro("senv", "ActiveMntGrp", mntGrp)

class mad_ascan(Macro):
    """newfile [numor] [numor file] [ numor file directory]"""
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
        mntGrp = self.getEnv("ActiveMntGrp")
	self.execMacro("senv", "ActiveMntGrp", MAD_MNT_GRP)
        self.execMacro("PrepareMaster")
        self.execMacro("PrepareSlaves")
        self.execMacro("PrepareGating")
        try:
            self.execMacro('ascan', *args)
        finally: 
            self.execMacro('CleanupGating') 
            self.execMacro("senv", "ActiveMntGrp", mntGrp)
