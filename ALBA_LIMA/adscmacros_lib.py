"""
    Macros for data acquisition with ADSC specific DS
"""

import PyTango
import time

#from macro import Macro, Type
from sardana.macroserver.macro import Macro, Type

class adsc_takebg(Macro):
    """Take background images."""

    param_def =  [['dev',Type.String, None, 'Device name or alias'],
                  ['Texp',Type.Float, None, 'Exposure time for BG images']]

    def run(self,dev,Texp):
        adsc = PyTango.DeviceProxy(dev+'_custom')
        adsc.takeDarks(Texp)
        
        while True:
            status = self.execMacro('lima_status',dev)
            state, acq = status.getResult().split()
            time.sleep(0.5)
            if acq != 'Running' and acq != 'Configuration' :
                break

        self.info(acq)
