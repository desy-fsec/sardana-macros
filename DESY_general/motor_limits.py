#!/bin/env python

"""Change motor limits for Hasy motors"""

from __future__ import print_function

__all__ = ["hasy_set_lim"]

import PyTango
from sardana.macroserver.macro import *
from sardana.macroserver.macro import macro

class hasy_set_lim(Macro):
    """Sets the software limits on the specified motor"""
    param_def = [
        ['motor', Type.Moveable, None, 'Motor name'],
        ['low',   Type.Float, None, 'lower limit'],
        ['high',   Type.Float, None, 'upper limit']
    ]

    def run(self, motor, low, high):
        
        set_lim, pars= self.createMacro("set_lim", motor, low, high)
        self.runMacro(set_lim)

        name = motor.getName()
        motor_device = PyTango.DeviceProxy(name)
        motor_device.UnitLimitMax = high
        motor_device.UnitLimitMin = low

class hasy_adjust_limits(Macro):
    """Sets Pool motor limits to the values in the Tango Device"""

    def prepare(self, **opts):
        self.all_motors = self.findObjs('.*', type_class=Type.Moveable)
       
    def run(self):
        nr_motors = len(self.all_motors)
        if nr_motors == 0:
            self.output('No motor defined')
            return
    
        for motor in self.all_motors:
            name = motor.getName()
            motor_device = PyTango.DeviceProxy(name)
            try:
                high = motor_device.UnitLimitMax
                low  = motor_device.UnitLimitMin

                set_lim, pars= self.createMacro("set_lim", motor, low, high)
                self.runMacro(set_lim)
            except:
                pass
            

        
