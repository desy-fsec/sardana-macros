"""Energy scan """

from __future__ import print_function

__all__ = ["escan", "me"]

import os
from sardana.macroserver.macro import *
import time

from PyTango import *
 
flag_no_first = 0

class e2lambda(Macro):
    """ returns the wavelength 12398.424/Energy"""
    param_def = [ 
        ['energy',  Type.Float,  None, 'Energy[eV]'],
        ]

    def run(self,  energy):
        wavelength = 12398.424/energy
        self.output( "Lambda: %g" % wavelength)

class escan(Macro):
    """Scan energy"""
    
    param_def = [ 
        ['start_energy',  Type.Float,  -999, 'Scan start energy'],
        ['end_energy',  Type.Float,   -999, 'Scan final energy'],
        ['nr_interv',  Type.Integer, -999, 'Number of scan intervals'],
        ['integ_time', Type.Float,   -999, 'Integration time'],
        ['fixq', Type.String, "Not", 'Add fixq  as argument if q has to be kept fixed' ]
        ]
    

    def hkl_pre_move(self):
        global flag_no_first
        self.info("\tCalling move hkl hook")
    
        pos_to_set = self.energy_motor.Position + flag_no_first * self.step
        flag_no_first = 1

        wavelength = self.lambda_to_e/(self.energy_motor.Position + self.step)
        
        self.diffrac.write_attribute("wavelength", wavelength)

        macro,pars = self.createMacro("br", self.h_value, self.k_value, self.l_value)

        self.runMacro(macro)
        
    def hkl_post_move(self):      
        move_flag = 1
        while move_flag:
            move_flag = 0
            time.sleep(1)
            for i in range(0,len(self.angle_dev)):
                if self.angle_dev[i] == PyTango.DevState.MOVING:
                    move_flag = 1
        

    def run(self,  start_energy, end_energy, nr_interv, integ_time, fixq):
        
        if start_energy == -999:
            self.output("Usage:")
            self.output("escan <start_energy> <end_energy> <nr_interv> <integ_time> [fixq]")
            self.output("Add fixq as argument if q has to be kept fixed during the movement")
            return

        try:
            energy_device = self.getObj("mnchrmtr")
            energy_device_name = "mnchrmtr"
        except:
            self.warning("mnchrmtr device does not exist.")
            self.warning("Trying to get the energy device name from the EnergyDevice environment variable")
            try:
                energy_device_name = self.getEnv('EnergyDevice')
            except:
                self.error("EnergyDevice not defined. Macro exiting")
                return
            try:
                energy_device = self.getObj(energy_device_name)
            except:
                self.error("Unable to get energy device %s. Macro exitin" % energy_device_name)
                return
                

        # set the motor to the initial position for having the right position at the first hook

        self.output("Moving energy to the start value ...")
        self.execMacro("mv %s %f" % (energy_device_name, start_energy))

        macro,pars = self.createMacro("ascan", energy_device, start_energy, end_energy, nr_interv, integ_time)

        self.step = abs(end_energy - start_energy)/nr_interv

        self.energy_device = energy_device

        if fixq == "fixq":
            self.lambda_to_e = 12398.424 # Amstrong * eV
            diffrac_name = self.getEnv('DiffracDevice')
            self.diffrac = self.getDevice(diffrac_name)
            pseudo_motor_names = []
            for motor in self.diffrac.hklpseudomotorlist:
                pseudo_motor_names.append(motor.split(' ')[0])
            
            h_device = self.getDevice(pseudo_motor_names[0])
            k_device = self.getDevice(pseudo_motor_names[1])
            l_device = self.getDevice(pseudo_motor_names[2])

            self.h_fix = h_device.Position
            self.k_fix = k_device.Position
            self.l_fix = l_device.Position

            macro.hooks = [ (self.hkl_pre_move, ["pre-move"]), (self.hkl_post_move, ["post-move"]), ] 

        self.runMacro(macro)


class me(Macro):
    """Move energy. Diffractometer wavelength is set"""

    
    param_def = [ 
        ['energy',  Type.Float,  -999, 'Energy to set']
        ]

    def run(self,  energy):

        if energy == -999:
            self.output("Usage:")
            self.output("me <energy>")
            self.output("Move energy. Diffractometer wavelength is set")
            return

        try:
            energyfmb_device = self.getObj("mnchrmtr")
            energyfmb_device_name = "mnchrmtr"
        except:
            self.warning("mnchrmtr device does not exist.")
            self.warning("Trying to get the fmb device name from the EnergyFMB environment variable")
            try:
                energyfmb_device_name = self.getEnv('EnergyFMB')
            except:
                self.error("EnergyFMB not defined. Macro exiting")
                return
            try:
                energyfmb_device = self.getObj(energyfmb_device_name)
            except:
                self.error("Unable to get fmb device %s. Macro exiting" % energyfmb_device_name)
                return

        try:
            energy_device = self.getObj("mnchrmtr")
            energy_device_name = "mnchrmtr"
        except:
            self.warning("mnchrmtr device does not exist.")
            self.warning("Trying to get the energy device name from the EnergyDevice environment variable")
            try:
                energy_device_name = self.getEnv('EnergyDevice')
            except:
                self.error("EnergyDevice not defined. Macro exiting")
                return
            try:
                energy_device = self.getObj(energy_device_name)
            except:
                self.error("Unable to get energy device %s. Macro exiting" % energy_device_name)
                return

        fmb_tango_device = DeviceProxy(energyfmb_device.TangoDevice)
        try:
            fmb_tango_device.write_attribute("PseudoChannelCutMode", 0)
        except:
            pass

        diffrac_name = self.getEnv('DiffracDevice')
        diffrac_device = self.getDevice(diffrac_name)
        lambda_to_e = 12398.424 # Amstrong * eV
        wavelength = lambda_to_e/energy        
        diffrac_device.write_attribute("wavelength", wavelength)

        self.execMacro("mv", energy_device, energy)
