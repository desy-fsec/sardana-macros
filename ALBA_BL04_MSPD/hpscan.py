import PyTango
import taurus
import time
from sardana.macroserver.macro import Macro, Type
from macro_utils.macroutils import SoftShutterController

MARCCD_DELAY = 0.27


class hpascan(Macro, SoftShutterController):
    """newfile [numor] [numor file] [ numor file directory]"""
    param_def = [ ['motor',      Type.Moveable,  None, 'Moveable to move'],
       		  ['start_pos',  Type.Float,   None, 'Scan start position'],
       		  ['final_pos',  Type.Float,   None, 'Scan final position'],
       		  ['nr_interv',  Type.Integer, None, 'Number of scan intervals'],
       		  ['integ_time', Type.Float,   None, 'Integration time']
    		 ]
    
    
    def prepare(self, *args, **kwargs):  
        SoftShutterController.init(self) 

    def run(self, *args, **kwargs):
        
        try:
            self._fsShutter = self.getEnv("_fsShutter")
        except UnknownEnv, e:
            self._fsShutter = 0        
        
        try:
            if self._fsShutter == 1:
                SoftShutterController.openShutter(self)
                
            mot = args[0]
            StartPos =  args[1]
            EndPos   =  args[2]
            Npts      = args[3]
            intTim    = args[4]      
            args = (mot.name,StartPos,EndPos,Npts,intTim)

            mot.move(StartPos)
            #self.execMacro('fsopen') 
            wait =1.
            self.info("sleep time %.2f " %wait)
            time.sleep(wait)# added to avoid lower count at 1st point because of fs opening 
   	    self.execMacro('ascan', *args)
        finally: 
            #self.execMacro('fsclose') 
            if self._fsShutter == 1:
                SoftShutterController.closeShutter(self)

class hpdscan(Macro, SoftShutterController):
    """newfile [numor] [numor file] [ numor file directory]"""
    param_def = [ ['motor',      Type.Moveable,  None, 'Moveable to move'],
       		  ['start_pos',  Type.Float,   None, 'Scan start position'],
       		  ['final_pos',  Type.Float,   None, 'Scan final position'],
       		  ['nr_interv',  Type.Integer, None, 'Number of scan intervals'],
       		  ['integ_time', Type.Float,   None, 'Integration time']
    		 ]
    
    
    def prepare(self, *args, **kwargs):  
        SoftShutterController.init(self) 

    def run(self, *args, **kwargs):
        try:
            self._fsShutter = self.getEnv("_fsShutter")
        except UnknownEnv, e:
            self._fsShutter = 0
            
	try:
            if self._fsShutter == 1:
                SoftShutterController.openShutter(self)
            mot = args[0]
            StartPos =  args[1]
            EndPos   =  args[2]
            Npts      = args[3]
            intTim    = args[4]
            

            currentPos = mot.read_attribute("position").value
            StartPos = currentPos + StartPos
            EndPos = currentPos + EndPos
            args = (mot.name,StartPos,EndPos,Npts,intTim)
    	    self.execMacro('hpascan', *args)
	finally:    
            if self._fsShutter == 1:
                SoftShutterController.closeShutter(self)
            mot.move(currentPos)
