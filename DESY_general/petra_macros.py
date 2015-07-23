#!/usr/bin/env python

"""
Macros related to the petra current
"""

__all__ = ["wait_for_petra",
	   ]

import PyTango, os, sys
import time
from sardana.macroserver.macro import *
from sardana.macroserver.macro import macro


class wait_for_petra(Macro):
    """display the general_functions.py file """
    
    param_def = [
	    ['current_limit', Type.Float, 1, 'Limit for checking petra current'],
	    ]

    def run(self, current_limit):
                        
	    try:
		    petra_device_name = self.getEnv('PetraDevice')
                    try:
                        petra_current_name = self.getEnv('PetraCurrent')
                    except:
                        self.info("PetraCurrent environment not defined. Using BeamCurrent")
                        petra_current_name = "BeamCurrent"
	    except:
		    self.info("PetraDevice environment not defined. Using petra/globals/keyword as petra device")
		    petra_device_name = "petra/globals/keyword"
                    petra_current_name = "BeamCurrent"

	    try:
		    petra_device = PyTango.DeviceProxy(petra_device_name)
	    except:
		    self.warning("Not able to create proxy to petra device %s. Not current check is done" % petra_device_name)
		    return


            petra_current = petra_device.read_attribute(petra_current_name).value

            while petra_current < current_limit:
		    self.checkPoint()
		    time.sleep(0.5)
		    petra_current = petra_device.read_attribute(petra_current_name).value
