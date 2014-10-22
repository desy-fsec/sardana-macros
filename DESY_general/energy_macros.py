#!/bin/env python

"""Energy scan """

from __future__ import print_function

__all__ = ["escan"]

import os
from sardana.macroserver.macro import *
import time

from PyTango import *
 
flag_no_first = 0

class escan(Macro):
    """Scan energy"""
    
    param_def = [ 
        ['start_energy',  Type.Float,  -999, 'Scan start energy'],
        ['end_energy',  Type.Float,   -999, 'Scan final energy'],
        ['nr_interv',  Type.Integer, -999, 'Number of scan intervals'],
        ['integ_time', Type.Float,   -999, 'Integration time'],
        ['fixq', Type.String, "Not", 'Add fixq  as argument if q has to be kept fixed']
        ]
    

    def hkl_pre_move(self):
        global flag_no_first
        self.info("\tCalling move hkl hook")
    
        pos_to_set = self.energy_motor.Position + flag_no_first * self.step
        flag_no_first = 1
        

        self.output(str(pos_to_set))

        wavelength = self.lambda_to_e/(self.energy_motor.Position + self.step)
 
        
        #self.diffrac.wavelength = wavelength

        #macro,pars = self.createMacro("br", self.h_value, self.k_value, self.l_value)

        #self.runMacro(macro)


    def hkl_post_move(self):      
        move_flag = 1
        #while move_flag:
        #    move_flag = 0
        #    time.sleep(1)
        #    for i in range(0,len(self.angle_dev)):
        #        if self.angle_dev[i] == PyTango.DevState.MOVING:
        #            move_flag = 1
        

    def run(self,  start_energy, end_energy, nr_interv, integ_time, fixq):
        
        if start_energy == -999:
            self.output("Usage:")
            self.output("escan start_energy end_energy nr_interv integ_time [fixq]")
            self.output("Add fixq as argument if q has to be kept fixed during the scan")
            return

        try:
            energy_motor_name = self.getEnv('EnergyMotorName')
        except:
            energy_motor_name = "energy_motor"

        energy_motor = self.getObj(energy_motor_name)

        # set the motor to the initial position for having the right position at the first hook

        self.output("Moving energy to the start value ...")
        self.execMacro("mv %s %f" % (energy_motor_name, start_energy))

        macro,pars = self.createMacro("ascan", energy_motor, start_energy, end_energy, nr_interv, integ_time)

        self.step = abs(end_energy - start_energy)/nr_interv

        self.energy_motor = energy_motor

        if fixq == "fixq":
            self.lambda_to_e = 12398.424 # Amstrong * eV
            #diffrac_name = self.getEnv('DiffracDevice')
            #self.diffrac = self.getDevice(diffrac_name)
            pseudo_motor_names = []
            #for motor in self.diffrac.hklpseudomotorlist:
            #    pseudo_motor_names.append(motor.split(' ')[0])
            
            #h_device = self.getDevice(pseudo_motor_names[0])
            #k_device = self.getDevice(pseudo_motor_names[1])
            #l_device = self.getDevice(pseudo_motor_names[2])

            #self.h_fix = h_device.Position
            #self.k_fix = k_device.Position
            #self.l_fix = l_device.Position

            macro.hooks = [ (self.hkl_pre_move, ["pre-move"]), (self.hkl_post_move, ["post-move"]), ] 

        self.runMacro(macro)

