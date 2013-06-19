import time
import PyTango, taurus
from sardana.macroserver.macro import *
from macro_utils.mad26acq import COUNTERS, PrepareCountersForStepScanning

MNT_GRP = "mad"

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
        PrepareCountersForStepScanning()
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
        PrepareCountersForStepScanning()
        try:
            self.execMacro('ascan', *args)
        finally: 
            self.execMacro("senv", "ActiveMntGrp", oldMntGrp)
