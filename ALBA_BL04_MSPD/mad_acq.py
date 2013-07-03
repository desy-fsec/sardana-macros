import time
import PyTango, taurus
from sardana.macroserver.macro import *
from macro_utils.mad26acq import COUNTERS
from macro_utils.mad26acq import PrepareCountersForStepScanning as PrepareCountersForStepScanningFunction
from macro_utils.macroutils import SoftShutterController

MNT_GRP = "mad"

class InitCounters(Macro):
  
    param_def = []
    
    def run(self, *args, **kwargs):
        InitCounters() 

class PrepareCountersForStepScanning(Macro):

    param_def = []

    def run(self, *args, **kwargs):
        PrepareCountersForStepScanningFunction()


class mad_ct(Macro, SoftShutterController):
    
    param_def = [["time", Type.Float, 1.0, "Acq time"]]

    def prepare(self, *args, **kwargs):  
        SoftShutterController.init(self)  
                 
    def run(self, *args, **kwargs):
        time = args[0]
        oldMntGrp = self.getEnv("ActiveMntGrp")
        self.setEnv("ActiveMntGrp", MNT_GRP)
        PrepareCountersForStepScanningFunction()
            
        try:
            self._fsShutter = self.getEnv("_fsShutter")
        except UnknownEnv, e:
            self._fsShutter = 0
            
        try:
            if self._fsShutter == 1:
                SoftShutterController.openShutter(self)
            self.execMacro("ct", time)
        finally:
            self.setEnv("ActiveMntGrp", oldMntGrp)
            if self._fsShutter == 1:
                SoftShutterController.closeShutter(self)

class mad_ascan(Macro, SoftShutterController):
    
    param_def = [ ['motor',      Type.Moveable,  None, 'Moveable to move'],
              ['start_pos',  Type.Float,   None, 'Scan start position'],
              ['final_pos',  Type.Float,   None, 'Scan final position'],
              ['nr_interv',  Type.Integer, None, 'Number of scan intervals'],
              ['integ_time', Type.Float,   None, 'Integration time']
             ]
    
    def prepare(self, *args, **kwargs):  
        SoftShutterController.init(self)       
        
         
    def run(self, *args, **kwargs):
        mot = args[0]
        StartPos =  args[1]
        EndPos   =  args[2]
        Npts      = args[3]
        intTim    = args[4]      
        args = (mot.name,StartPos,EndPos,Npts,intTim)
        oldMntGrp = self.getEnv("ActiveMntGrp")
        self.setEnv("ActiveMntGrp", MNT_GRP)
        PrepareCountersForStepScanningFunction()
        
        try:
            self._fsShutter = self.getEnv("_fsShutter")
        except UnknownEnv, e:
            self._fsShutter = 0
        
        try:
            if self._fsShutter == 1:
                SoftShutterController.openShutter(self)
            self.execMacro('ascan', *args)
        finally: 
            self.execMacro("senv", "ActiveMntGrp", oldMntGrp)
            if self._fsShutter == 1:
                SoftShutterController.closeShutter(self)


