from sardana.macroserver.macro import Macro
import taurus
import os
from datetime import datetime

# self.info() = output in blue    
# self.error() = output in red
# self.output() = output in black


class set_env(Macro):
    '''
           Sets automatically the ScanDir and ScanFile to today's date
    '''
    def run(self):
        t = datetime.now()
        dir="/beamlines/bl13/commissioning/"+t.strftime("%Y%m%d")
        self.execMacro('senv ScanDir %s' % dir) 
        file=t.strftime("%Y%m%d")+".h5"
        self.execMacro('senv ScanFile %s' % file) 
        if not os.path.exists(dir):
           os.makedirs(dir)
        self.execMacro('lsenv') 
        









































































