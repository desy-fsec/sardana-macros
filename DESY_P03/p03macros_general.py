#!/bin/env python

"""General Macros P03"""

from __future__ import print_function

__all__ = ["p03_fshclose", "p03_fshopen", "p03_lasin", "p03_lasout", "p03_create_mg_shutter"]

import os
import PyTango
from sardana.macroserver.macro import *
import time

class _p03_fsh_close_open(Macro):
    """Close/Open fast shutter"""

    param_def = [
        ['action', Type.Integer, None, '0 -> close, 1 -> open'],
        ['check_petra_current', Type.Integer, None, '1 if check petra current']
        ]

    def run(self, action, check_petra_current):

        if action:
            self.output("Open fast shutter")
        else:
            self.output("Close fast shutter")

        if check_petra_current:
            self.output("Check PETRAIII current")

            # A CounterTimer can be used if the PETRA current is integrated as counter in Sardana
            # Without this integration, the Tango Device is used:
            
            petra_device = PyTango.DeviceProxy("petra/globals/keyword") 
            petra_current = petra_device.BeamCurrent

            if petra_current < 1:
                self.output("PETRAIII current is to low -- Injection?")
                return
                

        self.output("Check shutter status")

        # It is assumed that a MeasurementGroup for the shutter, called mg_shutter, is already created
        # Counter -> exp_vfc03, timer -> exp_t01
            
        try:
            mg_shutter = self.getMeasurementGroup("mg_shutter")
            mg_shutter.write_attribute("IntegrationTime",0.01)
        except:
            self.output("Shutter MG not defined. Create it with p03_create_mg_shutter")
            return

        mg_shutter.Start()

        counter = self.getCounterTimer("exp_vfc03")

        while mg_shutter.State() == PyTango.DevState.MOVING:
            time.sleep(0.001)

        value = counter.Value

        self.output("value is %d " % value)

        perform_action = 0
        if action:
            if value > 2000:
                perform_action = 1
        else:
            if value < 2000:
                perform_action = 1

        if perform_action:

            ioreg = self. getIORegister("exp_oreg01")

            if action:
                self.output("opening shutter")  
                tmp_macro, pars= self.createMacro("write_ioreg", ioreg, 0)
            else:
                self.output("closing shutter")  
                tmp_macro, pars= self.createMacro("write_ioreg", ioreg, 1)

            self.runMacro(tmp_macro)

            mg_shutter.Start()    
            while mg_shutter.State() == PyTango.DevState.MOVING:
                time.sleep(0.001)
            value = counter.Value
                
            self.output("value is %d " % value)
        else:
            if action:
                self.output("shutter is already open")
            else:
                self.output("shutter is already closed")



class p03_fshclose(Macro):
    """Close fast shutter"""

    def run(self):

        tmp_macro, pars= self.createMacro("_p03_fsh_close_open", 0, 1)

        self.runMacro(tmp_macro)
        


class p03_fshopen(Macro):
    """Open fast shutter"""

    def run(self):

        tmp_macro, pars= self.createMacro("_p03_fsh_close_open", 1, 1)

        self.runMacro(tmp_macro)          

class p03_lasin(Macro):
    """Move laser in"""

    def run(self):

        # Check shutter status and open it if close
        tmp_macro, pars= self.createMacro("_p03_fsh_close_open", 1, 0)

        self.runMacro(tmp_macro)

        ioreg = self. getIORegister("exp_oreg02")

        self.output("Moving laser in")

        tmp_macro, pars= self.createMacro("write_ioreg", ioreg, 0)

        self.runMacro(tmp_macro)

class p03_lasout(Macro):
    """Move laser out"""

    def run(self):

        ioreg = self. getIORegister("exp_oreg02")

        self.output("Moving laser out")

        tmp_macro, pars= self.createMacro("write_ioreg", ioreg, 1)

        self.runMacro(tmp_macro)

        # Check shutter status and close it if open
        tmp_macro, pars= self.createMacro("_p03_fsh_close_open", 0, 0)

        self.runMacro(tmp_macro)


class p03_create_mg_shutter(Macro):
    """Create measurement group for getting shutter status (mg_shutter)"""

    def run(self):

        self.output("Creating mg_shutter")

        pools = self.getPools()
        pool = pools[0]

        args = []
        args.append("mg_shutter")
        args.append("exp_t01")
        args.append("exp_vfc03")

        pool.CreateMeasurementGroup(args)

        self.output("Done")
