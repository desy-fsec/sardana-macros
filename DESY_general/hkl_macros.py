
"""
    Macro library containning diffractometer related macros for the macros 
    server Tango device server as part of the Sardana project.
    
"""
import time
import math
import numpy as np 
import getpass
import os

import re

from sardana.macroserver.macro import *

class _diffrac:
    """Internal class used as a base class for the diffractometer macros"""

    env = ('DiffracDevice',)
    
    def prepare(self):

        self.prepared = False
        
        dev_name = self.getEnv('DiffracDevice')
        self.diffrac = self.getDevice(dev_name)

        try:
            dev_name = self.getEnv('Psi')
            self.psidevice = self.getDevice(dev_name)
        except:
            pass

        motorlist = self.diffrac.motorlist
        
        pseudo_motor_names = []
        for motor in self.diffrac.hklpseudomotorlist:
            pseudo_motor_names.append(motor.split(' ')[0])
            
        self.h_device = self.getDevice(pseudo_motor_names[0])
        self.k_device = self.getDevice(pseudo_motor_names[1])
        self.l_device = self.getDevice(pseudo_motor_names[2])

        motor_list = self.diffrac.motorlist

        self.nb_motors = len(motor_list)

        try:
            self.angle_names = self.diffrac.motorroles
        except: # Only for compatibility
            self.angle_names = []
            if self.nb_motors == 4:
                self.angle_names.append("omega")
                self.angle_names.append("chi")
                self.angle_names.append("phi")
                self.angle_names.append("theta")
            elif self.nb_motors == 6:
                self.angle_names.append("mu")
                self.angle_names.append("omega")
                self.angle_names.append("chi")
                self.angle_names.append("phi")
                self.angle_names.append("gamma")
                self.angle_names.append("delta")

        if self.nb_motors == 4:
            self.labelmotor = {'Omega': "omega", 'Chi': "chi", 'Phi': "phi", 'Theta': "theta"}
        elif self.nb_motors == 6:
            self.labelmotor = {'Mu': "mu", 'Theta': "omega", 'Chi': "chi", 'Phi': "phi", 'Gamma': "gamma", 'Delta': "delta"}

        prop = self.diffrac.get_property(['DiffractometerType'])        
        for v in prop['DiffractometerType']:       
            self.type = v
        
        self.angle_device_names = {}
        i = 0
        for motor in motor_list:
            self.angle_device_names[self.angle_names[i]] = motor.split(' ')[0]
            i = i + 1

        self.prepared = True

    def on_stop(self):
        
        for angle in self.angle_names:
            angle_dev = self.getDevice(self.angle_device_names[angle])
            angle_dev.Stop()

    def check_collinearity(self,h0,k0,l0,h1,k1,l1):

        print h0
        cpx = k0*l1-l0*k1  
        cpy = l0*h1-h0*l1  
        cpz = h0*k1-k0*h1
        cp_square = math.sqrt(cpx*cpx+cpy*cpy+cpz*cpz)

        collinearity = False

        if cp_square < 0.01:
            collinearity = True

        return collinearity

    def get_hkl_ref0(self):

        reflections = []
        try:
            reflections = self.diffrac.reflectionlist
        except:
            pass
    
        hkl = []
        if reflections != None:
            for i in range(1,4):
                hkl.append(reflections[0][i])
        
        return hkl

    def get_hkl_ref1(self):

        reflections = []
        try:
            reflections = self.diffrac.reflectionlist
        except:
            pass

        hkl = []
        if reflections != None:
            if len(reflections) > 1:
                for i in range(1,4):
                    hkl.append(reflections[1][i])
        
        return hkl

    def fl(self,ch,
           regx = re.compile(
            '(?<![\d.])'
            '(?![1-9]\d*(?![\d.])|\d*\.\d*\.)'
            '0*(?!(?<=0)\.)'
            '([\d.]+?)'
            '\.?0*'
            '(?![\d.])'
            ),
           repl = lambda mat: mat.group(mat.lastindex)
           if mat.lastindex!=3
           else '0' + mat.group(3)  ):
        mat = regx.search(ch)
        if mat:
            return regx.sub(repl,ch) 
        

class br(Macro, _diffrac):
    """The br macro is used to move the diffractometer to the reciprocal space 
    coordinates given by H, K and L. If a fourth parameter is given, the combination
    of angles to be set is the correspondig to the given index. The index of the
    angles combinations are then changed."""


    param_def = [
       ['H', Type.Float, None, "H value"],
       ['K', Type.Float, None, "K value"],
       ['L', Type.Float, None, "L value"],
       ['AnglesIndex', Type.Integer, -1, "Angles index"],
       ['FlagNotBlocking', Type.Integer,  0, "If 1 not block. Return without finish movement"]
    ]

    def prepare(self, H, K, L, AnglesIndex, FlagNotBlocking):
        _diffrac.prepare(self)
        
    def run(self, H, K, L, AnglesIndex, FlagNotBlocking):
        if not self.prepared:
            return

        if AnglesIndex != -1:
            sel_tr = AnglesIndex
        else:
            sel_tr =  self.diffrac.selectedtrajectory


        hkl_values = [H, K, L]
        self.diffrac.write_attribute("computetrajectoriessim",hkl_values)

        angles_list = self.diffrac.trajectorylist[sel_tr] 
        
        i = 0
        for angle in self.angle_names:
            angle_dev = self.getDevice(self.angle_device_names[angle])
            angle_dev.write_attribute("Position",angles_list[i])
            i = i + 1
            self.checkPoint()
        
        self.checkPoint()

        if FlagNotBlocking == 0:
            self.execMacro('blockprintmove', 0)

    def on_stop(self):
        _diffrac.on_stop(self)
        

class ubr(Macro, _diffrac):
    """
        ubr H K L
    """

    param_def = [
        [ "hh", Type.Float, -999, "H position" ],
        [ "kk", Type.Float, -999, "K position" ],
        [ "ll", Type.Float, -999, "L position" ],
        ['AnglesIndex', Type.Integer, -1, "Angles index"]
        ]

    def prepare(self, hh, kk, ll, AnglesIndex):
        _diffrac.prepare(self)
    
    def run( self, hh,kk,ll, AnglesIndex):

        if ll != -999:        
            br, pars = self.createMacro("br", hh, kk, ll, AnglesIndex, 1)
            self.runMacro(br)
            self.execMacro('blockprintmove', 1)
        else:
            self.output( "usage:  ubr H K L [Trajectory]")

    def on_stop(self):
        _diffrac.on_stop(self)
           
class ca(Macro, _diffrac):
    """Calculate motor positions for given H K L according to the current
    operation mode (trajectory 0)."""
    
    param_def = [
       ['H', Type.Float, None, "H value for the azimutal vector"],
       ['K', Type.Float, None, "K value for the azimutal vector"],
       ['L', Type.Float, None, "L value for the azimutal vector"],
    ]    
    
    def prepare(self, H, K , L):
        _diffrac.prepare(self)    
    
    def run(self, H, K, L):
        if not self.prepared:
            return

        hkl_values = [H, K, L]

        self.diffrac.write_attribute("computetrajectoriessim",hkl_values)

        angles_list = self.diffrac.trajectorylist[0]
        self.output("Trajectory 0 (more trajectories by caa H K L)")
        self.output("")

        try:
            self.output("%s %7.5f" % ("Azimuth (Psi) = ",self.psidevice.Position))
        except:
            self.warning("Not able to read psi. Check if environment Psi is defined")

        self.output("%s %7.5f" % ("Wavelength = ", self.diffrac.WaveLength))
        self.output("")

        str_pos = {}
        i = 0
        for name in self.angle_names:
            str_pos[name] = "%7.5f" % angles_list[i]
            i = i + 1

        self.output("%10s %11s %12s %11s %10s %11s" %("Delta","Theta","Chi","Phi","Mu","Gamma"))
        self.output("%10s %11s %12s %11s %10s %11s" % 
                    (str_pos[self.labelmotor["Delta"]], str_pos[self.labelmotor["Theta"]], str_pos[self.labelmotor["Chi"]], str_pos[self.labelmotor["Phi"]], str_pos[self.labelmotor["Mu"]], str_pos[self.labelmotor["Gamma"]]))

                           
class caa(Macro, _diffrac):
    """Calculate motor positions for given H K L according to the current
    operation mode (all trajectories)"""
    
    param_def = [
       ['H', Type.Float, None, "H value for the azimutal vector"],
       ['K', Type.Float, None, "K value for the azimutal vector"],
       ['L', Type.Float, None, "L value for the azimutal vector"],
    ]    
    
    def prepare(self, H, K , L):
        _diffrac.prepare(self)    
    
    def run(self, H, K, L):
        if not self.prepared:
            return

        hkl_values = [H, K, L]

        self.diffrac.write_attribute("computetrajectoriessim",hkl_values)
        
        for i in range(0, len(self.diffrac.trajectorylist)):
            angles_list = self.diffrac.trajectorylist[i]
            self.output("")
            self.output("Trajectory %2d " % i)

            self.output("H K L =  %9.5f %9.5f %9.5f " %
                        (self.h_device.position,self.k_device.position,
                         self.l_device.position))

            try:
                self.output("Azimuth (Psi) = %7.5f" % (self.psidevice.Position))
            except:
                self.warning("Not able to read psi. Check if environment Psi is defined")
            self.output("Wavelength =  %7.5f" % (self.diffrac.WaveLength))
            self.output("")

            str_pos1 = "%7.5f" % angles_list[5]
            str_pos2 = "%7.5f" % angles_list[1]
            str_pos3 = "%7.5f" % angles_list[2]
            str_pos4 = "%7.5f" % angles_list[3]
            str_pos5 = "%7.5f" % angles_list[0] 
            str_pos6 = "%7.5f" % angles_list[4] 
        
            self.output("%10s %11s %12s %11s %10s %11s" %("Delta","Theta","Chi","Phi","Mu","Gamma"))
            self.output("%10s %11s %12s %11s %10s %11s" % 
                        (str_pos1, str_pos2, str_pos3, str_pos4, str_pos5, str_pos6))


class pa(Macro, _diffrac):
    """Prints information about the active diffractometer."""
 
      
    suffix = ("st","nd","rd","th")

    def prepare(self):
        _diffrac.prepare(self)
        
    def run(self):
        if not self.prepared:
            return
      
        str_type = "Eulerian 6C"
        if self.type == 'E4CV':
            str_type = "Eulerian 4C Vertical"       
        elif self.type == 'E4CH':
            str_type = "Eulerian 4C Horizontal"       
        elif self.type == 'K6C':
            str_type = "Kappa 6C"       
        elif self.type == 'K4CV':
            str_type = "Kappa 4C Vertical"
            
        self.output("%s Geometry, %s" % (str_type, self.diffrac.enginemode))
        #self.output("Sector %s" % "[ToDo]")
        self.output("")

        reflections = self.diffrac.reflectionlist
        
        nb_ref = 0
        if reflections != None:
            for ref in reflections:
                if nb_ref < len(self.suffix): sf = self.suffix[nb_ref]
                else: sf = self.suffix[3]
                self.output("  %d%s Reflection (index %d): " % (nb_ref+1, sf, ref[0]))
                #self.output("    Affinement, Relevance : %d %d" % (ref[4], ref[5]))
                if len(ref) > 10:
                    self.output("    %s %s %s %s %s %s: %s %s %s %s %s %s" % (self.angle_names[5],self.angle_names[1],self.angle_names[2],self.angle_names[3],self.angle_names[4],self.angle_names[0], _diffrac.fl(self,str(ref[11])), _diffrac.fl(self,str(ref[7])), _diffrac.fl(self,str(ref[8])), _diffrac.fl(self,str(ref[9])), _diffrac.fl(self,str(ref[10])), _diffrac.fl(self,str(ref[6]))))
                else:
                    self.output("    %s %s %s %s: %s %s %s %s" % (self.angle_names[0],self.angle_names[1],self.angle_names[2],self.angle_names[3], _diffrac.fl(self,str(ref[6])), _diffrac.fl(self,str(ref[7])), _diffrac.fl(self,str(ref[8])), _diffrac.fl(self,str(ref[9]))))
                nb_ref = nb_ref + 1
                self.output(" %33s  %s %s %s" % ("H K L =", _diffrac.fl(self,str(ref[1])), _diffrac.fl(self,str(ref[2])), _diffrac.fl(self,str(ref[3]))))
                self.output("") 
                    
       
#        self.output("")
        self.output("  Lattice Constants (lengths / angles):")
        self.output("%32s = %s %s %s / %s %s %s" % ("real space", self.diffrac.a, 
                                                    self.diffrac.b, self.diffrac.c, _diffrac.fl(self,str(self.diffrac.alpha)), 
                                                    _diffrac.fl(self,str(self.diffrac.beta)), _diffrac.fl(self,str(self.diffrac.gamma))))

        self.output("")
        self.output("  Azimuthal reference:")
        self.output("%34s %s %s %s " %
                    ("H K L =",_diffrac.fl(self,str(self.diffrac.psirefh)), _diffrac.fl(self,str(self.diffrac.psirefk)), _diffrac.fl(self,str(self.diffrac.psirefl))))

        self.output("")
        self.output("  Lambda = %s" %(self.diffrac.WaveLength))
  
        lst = self.diffrac.ubmatrix
        self.output( "  UB-Matrix")
        self.output( "  %15g %15g %15g" % (lst[0][0], lst[0][1], lst[0][2]))
        self.output( "  %15g %15g %15g" % (lst[1][0], lst[1][1], lst[1][2]))
        self.output( "  %15g %15g %15g" % (lst[2][0], lst[2][1], lst[2][2]))
  

class wh(Macro, _diffrac):
    """wh - where, principal axes and reciprocal space
        
    Prints the current reciprocal space coordinates (H K L) and the user 
    positions of the principal motors. Depending on the diffractometer geometry, 
    other parameters such as the angles of incidence and reflection (ALPHA and 
    BETA) and the incident wavelength (LAMBDA) may be displayed.""" 

    def prepare(self):
        _diffrac.prepare(self)
    
    def run(self):
        if not self.prepared:
            return
       
        self.output("")
        self.output("Engine: %s" % self.diffrac.engine)
        self.output("")
        self.output("Mode: %s" % self.diffrac.enginemode)
        
        self.output("")
        self.output("%s %s %3s %9.5f %9.5f %9.5f " %
                    ("H","K","L = ",self.h_device.position,self.k_device.position,self.l_device.position))

        if self.diffrac.psirefh == -999:
            self.output("")
        else:
            self.output("%8s %9.5f %9.5f %9.5f " % 
                        ("Ref   = ",self.diffrac.psirefh,self.diffrac.psirefk,self.diffrac.psirefl))
     
            psirefh_in = self.diffrac.psirefh    
            psirefk_in = self.diffrac.psirefk    
            psirefl_in = self.diffrac.psirefl
            engine_restore = self.diffrac.engine
            mode_restore   = self.diffrac.enginemode
     
            self.diffrac.write_attribute("engine", "psi")
     
            psirefh_psi = self.diffrac.psirefh
            psirefk_psi = self.diffrac.psirefk
            psirefl_psi = self.diffrac.psirefl
        
            self.diffrac.write_attribute("engine", engine_restore)
            self.diffrac.write_attribute("enginemode", mode_restore)

            if psirefh_in != psirefh_psi or psirefk_in != psirefk_psi or psirefl_in != psirefl_psi:
                self.warning("Psiref vector missmatch. Calculated value corresponds to:")
                self.warning("%8s %9.5f %9.5f %9.5f " % 
                            ("Ref   = ",psirefh_psi,psirefk_psi,psirefl_psi))
                self.warning("Use setaz for setting it consistently")
            
        try:
            self.output("%s %7.5f" % ("Azimuth (Psi - calculated) = ",self.psidevice.Position))
        except:
            self.warning("Not able to read psi. Check if environment Psi is defined")


        parameter_names = self.diffrac.modeparametersnames

        if parameter_names != None:
            i = 0
            for par in parameter_names:
                if par == "psi":
                    parameter_values = self.diffrac.modeparametersvalues
                    self.info("%s %7.5f" % ("Azimuth (Psi - set) = ",parameter_values[i]))
                i = i + 1   

        self.output("%s %7.5f" % ("Wavelength = ", self.diffrac.WaveLength))
        self.output("")

        str_pos1 = "%7.5f" % self.getDevice(self.angle_device_names[self.labelmotor["Delta"]]).Position
        str_pos2 = "%7.5f" % self.getDevice(self.angle_device_names[self.labelmotor["Theta"]]).Position
        str_pos3 = "%7.5f" % self.getDevice(self.angle_device_names[self.labelmotor["Chi"]]).Position
        str_pos4 = "%7.5f" % self.getDevice(self.angle_device_names[self.labelmotor["Phi"]]).Position
        str_pos5 = "%7.5f" % self.getDevice(self.angle_device_names[self.labelmotor["Mu"]]).Position
        str_pos6 = "%7.5f" % self.getDevice(self.angle_device_names[self.labelmotor["Gamma"]]).Position
        
        self.output("%10s %11s %12s %11s %10s %11s" %("Delta","Theta","Chi","Phi","Mu","Gamma"))
        self.output("%10s %11s %12s %11s %10s %11s" % 
                    (str_pos1, str_pos2, str_pos3, str_pos4, str_pos5, str_pos6))


class freeze(Macro, _diffrac):
    """ Set psi value for psi constant modes """
    
    param_def = [
       ['parameter', Type.String, None, "Parameter to freeze"],
       ['value',     Type.Float,  None, "Value to be frozen"]
    ]    
   
    def prepare(self, parameter, value):
        _diffrac.prepare(self)
        
    def run(self, parameter, value):
        if not self.prepared:
            return   
        
        if parameter == "psi":
            engine_restore = self.diffrac.engine
            mode_restore   = self.diffrac.enginemode
            
            if mode_restore != "psi_constant_vertical" and mode_restore != "psi_constant_horizontal":
                self.warning("Psi frozen to set value. But current mode is not set to psi_constant_vertical or psi_constant_horizontal ")
            
            
            self.diffrac.write_attribute("engine", "hkl")
            self.diffrac.write_attribute("enginemode", "psi_constant_vertical")
            parameter_values = self.diffrac.modeparametersvalues
            parameter_values[3] = value
            self.diffrac.write_attribute("modeparametersvalues", parameter_values)
            self.diffrac.write_attribute("enginemode", "psi_constant_horizontal")
            parameter_values = self.diffrac.modeparametersvalues
            parameter_values[3] = value
            self.diffrac.write_attribute("modeparametersvalues", parameter_values)
            
            self.diffrac.write_attribute("engine", engine_restore)
            self.diffrac.write_attribute("enginemode", mode_restore)
            

        else:
            self.warning("Only implemented for parameter psi. Nothing done")


class setmode(Macro, _diffrac):
    """Set operation mode.""" 
    
    param_def = [
       ['new_mode', Type.Integer, -1, "Mode to be set"]
    ]    
   
    interactive=True 

    def prepare(self, new_mode):
        _diffrac.prepare(self)
    
    def run(self, new_mode):
        if not self.prepared:
            return

        modes = self.diffrac.enginemodelist

        if new_mode == -1:
            self.output("Available modes:")
            imode = 1
            old_mode=self.diffrac.read_attribute("enginemode").value
            for mode in modes:
                if mode==old_mode:
                    def_mode=imode
                self.output(" %d -> %s " % (imode, mode))
                imode = imode + 1
            old_mode=self.diffrac.read_attribute("enginemode").value
            self.output("")
            a=self.input("Your choice?",default_value=def_mode)
            imode=1
            for mode in modes:
                if imode==int(a):
                    def_mode=imode
                imode = imode + 1

            self.diffrac.write_attribute("enginemode",modes[def_mode - 1])
            self.output("")
            self.output("Now using %s mode" % modes[def_mode - 1])
            return



        if new_mode > len(modes):
            self.output("Wrong index mode -> only from 1 to %d allowed:" % len(modes))
            imode = 1
            for mode in modes:
                self.output(" %d -> %s " % (imode, mode))
                imode = imode + 1
            return
        else:
            self.diffrac.write_attribute("enginemode",modes[new_mode - 1])
            self.output("Now using %s mode" % modes[new_mode - 1])

            self.execMacro('savecrystal') 
            
class getmode(Macro, _diffrac):
    """Get operation mode."""
    
    def prepare(self):
        _diffrac.prepare(self)
        
    def run(self):
        if not self.prepared:
            return
        
        self.output(self.diffrac.enginemode)



class setlat(Macro, _diffrac):
    """Set the crystal lattice parameters a, b, c, alpha, beta, gamma.
       for the currently active diffraction pseudo motor controller."""  
 
    param_def = [
       ['a', Type.Float, -999, "Lattice 'a' parameter"],
       ['b', Type.Float, -999, "Lattice 'b' parameter"],
       ['c', Type.Float, -999, "Lattice 'c' parameter"],
       ['alpha', Type.Float, -999, "Lattice 'alpha' parameter"],
       ['beta',  Type.Float, -999, "Lattice 'beta' parameter"],
       ['gamma', Type.Float, -999, "Lattice 'gamma' parameter"]
    ] 

    hints = { 'interactive' : 'True' }
    interactive=True

    def prepare(self, a, b, c, alpha, beta, gamma):
        _diffrac.prepare(self)
    
    def run(self, a, b, c, alpha, beta, gamma):
        if not self.prepared:
            return
       
        if gamma == -999:
            a=self.diffrac.a
            b=self.diffrac.b
            c=self.diffrac.c
            alpha=self.diffrac.alpha
            beta=self.diffrac.beta
            gamma=self.diffrac.gamma
            self.output("")
            self.output("Enter real space lattice parameters:")
            a=self.input(" Lattice a?", default_value=a,data_type=Type.String)
            b=self.input(" Lattice b?", default_value=b,data_type=Type.String)
            c=self.input(" Lattice c?", default_value=c,data_type=Type.String)
            alpha=self.input(" Lattice alpha?", default_value=alpha,data_type=Type.String)
            beta=self.input(" Lattice beta?", default_value=beta,data_type=Type.String)
            gamma=self.input(" Lattice gamma?", default_value=gamma,data_type=Type.String)
            self.output("") 
            self.diffrac.write_attribute("a", float(a))
            self.diffrac.write_attribute("b", float(b))
            self.diffrac.write_attribute("c", float(c))
            self.diffrac.write_attribute("alpha", float(alpha))
            self.diffrac.write_attribute("beta",float(beta))
            self.diffrac.write_attribute("gamma", float(gamma))
        else:
            self.diffrac.write_attribute("a", a)
            self.diffrac.write_attribute("b", b)
            self.diffrac.write_attribute("c", c)
            self.diffrac.write_attribute("alpha", alpha)
            self.diffrac.write_attribute("beta", beta)
            self.diffrac.write_attribute("gamma", gamma) 
  
        self.execMacro('compute_u')

class or0(Macro, _diffrac):
    """Set primary orientation reflection.""" 
    
    param_def = [
       ['H', Type.Float, None, "H value"],
       ['K', Type.Float, None, "K value"],
       ['L', Type.Float, None, "L value"],
    ]
    
    def prepare(self, H, K, L):
        _diffrac.prepare(self)
    
    def run(self, H, K, L):
        if not self.prepared:
            return

        # Check collinearity

        hkl_ref1 = _diffrac.get_hkl_ref1(self)
        if len(hkl_ref1) > 1:
            check = _diffrac.check_collinearity(self, H, K, L, hkl_ref1[0], hkl_ref1[1], hkl_ref1[2])
            if check:
                self.warning("Can not orient: or0 %9.5f %9.5f %9.5f are parallel to or1" % (H, K, L))
                return
                             
        values = []                 
        values.append(0)        
        values.append(H)        
        values.append(K)
        values.append(L)
        self.diffrac.write_attribute("AddReflectionWithIndex", values) 

        self.execMacro('compute_u')

class or1(Macro, _diffrac):
    """Set secondary orientation reflection.""" 

    param_def = [
       ['H', Type.Float, None, "H value"],
       ['K', Type.Float, None, "K value"],
       ['L', Type.Float, None, "L value"],
    ]
    
    def prepare(self, H, K, L):
        _diffrac.prepare(self)
    
    def run(self, H, K, L):
        if not self.prepared:
            return

        # Check collinearity

        hkl_ref0 = _diffrac.get_hkl_ref0(self)
        if len(hkl_ref0) > 1:
            check = _diffrac.check_collinearity(self, hkl_ref0[0], hkl_ref0[1], hkl_ref0[2], H, K, L)
            if check:
                self.warning("Can not orient: or0 is parallel to or1 %9.5f %9.5f %9.5f" % (H, K, L))
                return

        values = []                 
        values.append(1)        
        values.append(H)        
        values.append(K)
        values.append(L)
        self.diffrac.write_attribute("AddReflectionWithIndex", values) 
 
        self.execMacro('compute_u')

class setor0(Macro, _diffrac):
    """Set primary orientation reflection choosing hkl and angle values""" 
    
    param_def = [
       ['H', Type.Float, -999, "H value"],
       ['K', Type.Float, -999, "K value"],
       ['L', Type.Float, -999, "L value"],
       ['mu', Type.Float, -999, "Mu value"],
       ['theta', Type.Float, -999, "Theta value"],
       ['chi', Type.Float, -999, "Chi value"],
       ['phi', Type.Float, -999, "Phi value"],
       ['gamma', Type.Float, -999, "Gamma value"],
       ['delta', Type.Float, -999, "Delta value"],
    ]
    

    hints = { 'interactive' : 'True' }
    interactive=True

    def prepare(self, H, K, L, mu, theta, chi, phi, gamma, delta):
        _diffrac.prepare(self)
    
    def run(self, H, K, L, mu, theta, chi, phi, gamma, delta):
        if not self.prepared:
            return
                
        setorn, pars= self.createMacro("setorn", 0, H, K, L, mu, theta, chi, phi, gamma, delta)

        self.runMacro(setorn)

class setor1(Macro, _diffrac):
    """Set secondary orientation reflection choosing hkl and angle values"""
    
    param_def = [
       ['H', Type.Float, -999, "H value"],
       ['K', Type.Float, -999, "K value"],
       ['L', Type.Float, -999, "L value"],
       ['mu', Type.Float, -999, "Mu value"],
       ['theta', Type.Float, -999, "Theta value"],
       ['chi', Type.Float, -999, "Chi value"],
       ['phi', Type.Float, -999, "Phi value"],
       ['gamma', Type.Float, -999, "Gamma value"],
       ['delta', Type.Float, -999, "Delta value"],
    ]
    

    hints = { 'interactive' : 'True' }
    interactive=True 
    
    def prepare(self, H, K, L, mu, theta, chi, phi, gamma, delta):
        _diffrac.prepare(self)
    
    def run(self, H, K, L, mu, theta, chi, phi, gamma, delta):
        if not self.prepared:
            return
                
        setorn, pars= self.createMacro("setorn", 1, H, K, L, mu, theta, chi, phi, gamma, delta)

        self.runMacro(setorn)

class setorn(Macro, _diffrac):
    """Set orientation reflection indicated by the index.""" 
    
    param_def = [
        ['ref_id', Type.Integer, None, "reflection index (starting at 0)"],
        ['H', Type.Float, -999, "H value"],
        ['K', Type.Float, -999, "K value"],
        ['L', Type.Float, -999, "L value"],
        ['mu', Type.Float, -999, "Mu value"],
        ['theta', Type.Float, -999, "Theta value"],
        ['chi', Type.Float, -999, "Chi value"],
        ['phi', Type.Float, -999, "Phi value"],
        ['gamma', Type.Float, -999, "Gamma value"],
        ['delta', Type.Float, -999, "Delta value"],
        ]
    

    hints = { 'interactive' : 'True' }
    interactive=True
 
    
    def prepare(self, ref_id, H, K, L, mu, theta, chi, phi, gamma, delta):
        _diffrac.prepare(self)
    
    def run(self, ref_id, H, K, L, mu, theta, chi, phi, gamma, delta):
        if not self.prepared:
            return
              
        if delta == -999:
            reflections = []
            try:
                reflections = self.diffrac.reflectionlist
            except:
                pass
            tmp_ref = {}
            hkl_names = ["h", "k", "l"]
            if reflections != None:
                if len(reflections) > ref_id:
                    for i in range(1,4):
                        tmp_ref[hkl_names[i-1]] = reflections[ref_id][i]
                    for i in range(6,12):
                        tmp_ref[self.angle_names[i-6]] = reflections[ref_id][i]
                else:
                    for i in range(0,3):
                        tmp_ref[hkl_names[i]] = 0
                    for i in range(0, 6):
                        tmp_ref[self.angle_names[i]] = 0                                   
            else:
                for i in range(0,3):
                    tmp_ref[hkl_names[i]] = 0
                for i in range(0, 6):
                    tmp_ref[self.angle_names[i]] = 0


            self.output("")
            if ref_id == 0:
                ref_txt = "primary-reflection"
            elif ref_id ==1:
                ref_txt = "secondary-reflection"
            else:
                ref_txt = "reflection " + str(ref_id)
                
  

            self.output("Enter %s angles" % ref_txt) 
            delta=float(self.input(" Delta?", default_value=tmp_ref["delta"],data_type=Type.String))
            theta=float(self.input(" Theta? ", default_value=tmp_ref["omega"],data_type=Type.String))
            chi=float(self.input(" Chi?", default_value=tmp_ref["chi"],data_type=Type.String))
            phi=float(self.input(" Phi?", default_value=tmp_ref["phi"],data_type=Type.String))
            gamma=float(self.input(" Gamma?", default_value=tmp_ref["gamma"],data_type=Type.String))
            mu=float(self.input(" Mu?", default_value=tmp_ref["mu"],data_type=Type.String))
           

            self.output("")
            self.output("Enter %s HKL coordinates"  % ref_txt) 
            H=float(self.input(" H?", default_value=tmp_ref["h"],data_type=Type.String))
            K=float(self.input(" K?", default_value=tmp_ref["k"],data_type=Type.String))
            L=float(self.input(" L?", default_value=tmp_ref["l"],data_type=Type.String))
            self.output("")

        
        # Check collinearity

        if ref_id == 0:
            hkl_ref = _diffrac.get_hkl_ref1(self)
        if ref_id == 1:
            hkl_ref = _diffrac.get_hkl_ref0(self)
        if ref_id < 2:
            if len(hkl_ref) > 1:
                check = _diffrac.check_collinearity(self, hkl_ref[0], hkl_ref[1], hkl_ref[2], H, K, L)
                if check:
                    self.warning("Can not orient: ref0 is parallel to ref1 %9.5f %9.5f %9.5f" % (H, K, L))
                    return

        # Set reflection

        values = []                 
        values.append(ref_id)        
        values.append(H)        
        values.append(K)
        values.append(L)
        
        self.diffrac.write_attribute("AddReflectionWithIndex", values)

        # Adjust angles

        self.angle_values = {"mu": mu, "omega": theta, "chi": chi, "phi": phi, "gamma": gamma, "delta": delta}   
      
        values = []
        values.append(ref_id)

        for angle_name in self.angle_names:
            values.append(self.angle_values[angle_name])

        self.diffrac.write_attribute("AdjustAnglesToReflection", values)

        # Recompute u

        self.execMacro('compute_u')

        


class setaz(Macro, _diffrac):
    """ Set hkl values of the psi reference vector"""

    param_def = [
        ['PsiH', Type.Float, -999, "H value of psi reference vector"],
        ['PsiK', Type.Float, -999, "K value of psi reference vector"],
        ['PsiL', Type.Float, -999, "L value of psi reference vector"],
        ]
    interactive=True

    def prepare(self, PsiH, PsiK, PsiL):
        _diffrac.prepare(self)

    def run(self, PsiH, PsiK, PsiL):
        if not self.prepared:
            return
        engine_restore = self.diffrac.engine
        mode_restore   = self.diffrac.enginemode

        if PsiL == -999:
            self.diffrac.write_attribute("engine", "hkl")
            self.diffrac.write_attribute("enginemode", "psi_constant_vertical")
            azh=self.diffrac.read_attribute("psirefh").value
            azk=self.diffrac.read_attribute("psirefk").value
            azl=self.diffrac.read_attribute("psirefl").value
            self.output("")
            self.output("Enter azimuthal reference H K L:")
            a1=self.input(" Azimuthal H?", default_value=azh,data_type=Type.String)
            a2=self.input(" Azimuthal K?", default_value=azk,data_type=Type.String)
            a3=self.input(" Azimuthal L?", default_value=azl,data_type=Type.String)
            PsiH=float(a1)
            PsiK=float(a2)
            PsiL=float(a3)


        self.diffrac.write_attribute("engine", "hkl")
        self.diffrac.write_attribute("enginemode", "psi_constant_vertical")
        self.diffrac.write_attribute("psirefh", PsiH)
        self.diffrac.write_attribute("psirefk", PsiK)
        self.diffrac.write_attribute("psirefl", PsiL)
        self.diffrac.write_attribute("enginemode", "psi_constant_horizontal")
        self.diffrac.write_attribute("psirefh", PsiH)
        self.diffrac.write_attribute("psirefk", PsiK)
        self.diffrac.write_attribute("psirefl", PsiL)
        self.diffrac.write_attribute("engine", "psi")
        self.diffrac.write_attribute("psirefh", PsiH)
        self.diffrac.write_attribute("psirefk", PsiK)
        self.diffrac.write_attribute("psirefl", PsiL)

        self.diffrac.write_attribute("engine", engine_restore)
        self.diffrac.write_attribute("enginemode", mode_restore)
        self.execMacro('savecrystal') 

class compute_u(Macro, _diffrac):
    """ Compute U matrix with reflections 0 and 1 """
       
    def prepare(self):
        _diffrac.prepare(self)
    
    def run(self):
        if not self.prepared:
            return
   
        reflections = self.diffrac.reflectionlist
        if reflections != None:
            if len(reflections) > 1:
                self.output("Computing U with reflections 0 and 1")
                values = []                 
                values.append(0)        
                values.append(1)
                self.diffrac.write_attribute("ComputeU", values)
                self.execMacro('savecrystal')
            else:
                self.warning("U can not be computed. Only one reflection")
        else:
            self.warning("U can not be computed. No reflection")

class add_reflection(Macro, _diffrac):
    """ Add reflection at the botton of reflections list """
           
    param_def = [
       ['H', Type.Float, None, "H value"],
       ['K', Type.Float, None, "K value"],
       ['L', Type.Float, None, "L value"],
       ['affinement', Type.Float, -999., "Affinement"]
    ]

    def prepare(self, H, K, L, affinement):
        _diffrac.prepare(self)
    
    def run(self, H, K, L, affinement):
        if not self.prepared:
            return
     

        values = []                         
        values.append(H)        
        values.append(K)
        values.append(L)
        if affinement != -999.:
            values.append(affinement)
        
        self.diffrac.write_attribute("AddReflection", values)     
        
    
class affine(Macro, _diffrac):
    """Affine current crystal"""
    
    def prepare(self):
        _diffrac.prepare(self)
    
    def run(self):
        if not self.prepared:
            return

        self.diffrac.write_attribute("AffineCrystal", 0)

class or_swap(Macro, _diffrac):
    """Swap values for primary and secondary vectors."""

    def prepare(self):
        _diffrac.prepare(self)

    def run(self):
        if not self.prepared:
            return

        self.diffrac.write_attribute("SwapReflections01", 0)
        self.output("Orientation vectors swapped.")
        self.execMacro('compute_u')

class newcrystal(Macro, _diffrac):
    """ Create a new crystal (if it does not exist) and select it. """

    param_def = [
        ['crystal_name',  Type.String, "", 'Name of the crystal to add and select']
        ]

    interactive=True

    def prepare(self, crystal_name):
        _diffrac.prepare(self)

    def run(self, crystal_name):
        if not self.prepared:
            return

        crystal_list = self.diffrac.crystallist

        to_add = 1
        i=1
        if crystal_name == "":
            crystal_name=self.diffrac.crystal
            self.output("Available crystals:")
            for crystal in crystal_list:
                self.output("(%s) %s" %(i,crystal))
                if crystal_name == crystal:
                    iselname=crystal
                i=i+1
            a=self.input("New crystal?", default_value=iselname,data_type=Type.String)
            try:
                a1=int(a)
                i=1
                for crystal in crystal_list:
                    if a1 == i:
                        a=crystal
                    i=i+1
                if a1>i-1:
                    a=iselname
            except:
                pass

            if a != iselname:
                crystal_name=a
            else:
                crystal_name=iselname

        for crystal in crystal_list:
            if crystal_name == crystal:
                to_add = 0

        if to_add:
            self.diffrac.write_attribute("addcrystal", crystal_name)

        self.diffrac.write_attribute("crystal", crystal_name)

        self.output("")
        self.output("Crystal selected: %s " % crystal_name)

        if to_add:
            a=self.input(" Lattice a?", default_value=5.43,data_type=Type.String)
            b=self.input(" Lattice b?", default_value=5.43,data_type=Type.String)
            c=self.input(" Lattice c?", default_value=5.43,data_type=Type.String)
            alpha=self.input(" Lattice alpha?", default_value=90,data_type=Type.String)
            beta=self.input(" Lattice beta?", default_value=90,data_type=Type.String)
            gamma=self.input(" Lattice gamma?", default_value=90,data_type=Type.String)
            self.output("")
            self.diffrac.write_attribute("a", float(a))
            self.diffrac.write_attribute("b", float(b))
            self.diffrac.write_attribute("c", float(c))
            self.diffrac.write_attribute("alpha", float(alpha))
            self.diffrac.write_attribute("beta",float(beta))
            self.diffrac.write_attribute("gamma", float(gamma)) 
    

class hscan(Macro, _diffrac):
    "Scan h axis"

    param_def = [
        ['start_pos',  Type.Float,   None, 'Scan start position'],
        ['final_pos',  Type.Float,   None, 'Scan final position'],
        ['nr_interv',  Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float,   None, 'Integration time'],
    ]

    def prepare(self, start_pos, final_pos, nr_interv, integ_time):
        _diffrac.prepare(self)
        
     
    def run(self, start_pos, final_pos, nr_interv, integ_time):
        
        ascan, pars= self.createMacro("ascan", self.h_device, start_pos, final_pos, nr_interv, integ_time)

        self.runMacro(ascan)

    def on_stop(self):
        _diffrac.on_stop(self)

class kscan(Macro, _diffrac):
    "Scan k axis"

    param_def = [
        ['start_pos',  Type.Float,   None, 'Scan start position'],
        ['final_pos',  Type.Float,   None, 'Scan final position'],
        ['nr_interv',  Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float,   None, 'Integration time'],
    ]

    def prepare(self, start_pos, final_pos, nr_interv, integ_time):
        _diffrac.prepare(self)
        
     
    def run(self, start_pos, final_pos, nr_interv, integ_time):
        
        ascan, pars= self.createMacro("ascan", self.k_device, start_pos, final_pos, nr_interv, integ_time)

        self.runMacro(ascan) 

    def on_stop(self):
        _diffrac.on_stop(self)    
    
class lscan(Macro, _diffrac):
    "Scan l axis"

    param_def = [
        ['start_pos',  Type.Float,   None, 'Scan start position'],
        ['final_pos',  Type.Float,   None, 'Scan final position'],
        ['nr_interv',  Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float,   None, 'Integration time'],
    ]

    def prepare(self, start_pos, final_pos, nr_interv, integ_time):
        _diffrac.prepare(self)
        
     
    def run(self, start_pos, final_pos, nr_interv, integ_time):
        
        ascan, pars= self.createMacro("ascan", self.l_device, start_pos, final_pos, nr_interv, integ_time)

        self.runMacro(ascan) 

    def on_stop(self):
        _diffrac.on_stop(self)

    
class hklscan(Macro, _diffrac):
    "Scan h k l axes"

    param_def = [
        ['h_start_pos',  Type.Float,   None, 'Scan h start position'],
        ['h_final_pos',  Type.Float,   None, 'Scan h final position'],
        ['k_start_pos',  Type.Float,   None, 'Scan k start position'],
        ['k_final_pos',  Type.Float,   None, 'Scan k final position'],
        ['l_start_pos',  Type.Float,   None, 'Scan l start position'],
        ['l_final_pos',  Type.Float,   None, 'Scan l final position'],
        ['nr_interv',  Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float,   None, 'Integration time'],
    ]

    def prepare(self, h_start_pos, h_final_pos, k_start_pos, k_final_pos, l_start_pos, l_final_pos, nr_interv, integ_time):
        _diffrac.prepare(self)
        
     
    def run(self, h_start_pos, h_final_pos, k_start_pos, k_final_pos, l_start_pos, l_final_pos, nr_interv, integ_time):
        
        a3scan, pars= self.createMacro("a3scan", self.h_device, h_start_pos, h_final_pos, self.k_device, k_start_pos, k_final_pos, self.l_device, l_start_pos, l_final_pos, nr_interv, integ_time)

        self.runMacro(a3scan) 

class th2th(Macro):
    """th2th - scan:
    
    Relative scan around current position in del and th with d_th=2*d_delta    
    """ 

    param_def = [
       ['rel_start_pos',  Type.Float,   -999, 'Scan start position'],
       ['rel_final_pos',  Type.Float,   -999, 'Scan final position'],
       ['nr_interv',  Type.Integer, -999, 'Number of scan intervals'],
       ['integ_time', Type.Float,   -999, 'Integration time']
       ]    

    
    def run(self,rel_start_pos,rel_final_pos,nr_interv,integ_time):
        
        if ((integ_time != -999)):       
            motor_del = self.getObj("del") 
            motor_th = self.getObj("th") 
            pos_del = motor_del.getPosition()
            pos_th =  motor_th.getPosition()
            scan=self.d2scan( motor_del, rel_start_pos, rel_final_pos, 
                              motor_th, rel_start_pos/2, rel_final_pos/2, 
                              nr_interv, integ_time )
        else:
            self.output( "Usage:   th2th tth_start_rel tth_stop_rel intervals time")


count_scan = 1

class HookPars:
    pass

def hook_pre_move(self, hook_pars):
    global count_scan

    self.execMacro('freeze', 'psi', hook_pars.psi_save + count_scan*hook_pars.angle_interv)
    self.execMacro('ubr', hooks_par.h, hooks_par.k, hooks_par.l)

    count_scan = count_scan + 1

class luppsi(Macro, _diffrac):
    """psi scan:
    
    Relative scan psi angle    
    """ 

    param_def = [
       ['rel_start_angle',  Type.Float,   -999, 'Relative start scan angle'],
       ['rel_final_angle',  Type.Float,   -999, 'Relative final scan angle'],
       ['nr_interv',  Type.Integer, -999, 'Number of scan intervals'],
       ['integ_time', Type.Float,   -999, 'Integration time']
       ]    

    def prepare(self, H, K, L, AnglesIndex):
        _diffrac.prepare(self)

    def run(self,rel_start_angle,rel_final_angle,nr_interv,integ_time):
        if not self.prepared:
            return
        
        global count_scan 
        count_scan = 1

        if ((integ_time != -999)):   
            self.diffrac.write_attribute("engine", "hkl") 
            self.diffrac.write_attribute("enginemode", "psi_constant_vertical")
            h = self.h_device.position
            k = self.k_device.position
            l = self.l_device.position

            psi_positions = []
            
            psi_save = self.psidevice.Position

            angle_interv = abs(rel_final_angle - rel_start_angle)/nr_interv
            
            # Construct scan macro

            self.output(self.psidevice.alias())
            psi_motor  = self.getMotor(self.psidevice.alias())
            self.output(psi_motor)
   
            macro,pars = self.createMacro('dscan %s %f %f %d %f ' % 
                                          (self.psidevice.alias(), rel_start_angle, rel_final_angle, nr_interv, integ_time))


            # Parameters for scan hook function

            hook_pars = HookPars()
            hook_pars.psi_save = psi_save
            hook_pars.angle_interv = angle_interv
            hook_pars.h = h
            hook_pars.k = k
            hook_pars.l = l
            f = lambda : hook_pre_move(self, hook_pars)
            macro.hooks = [
                (f, ["pre-move"]),
                ]

            # Start the scan

            self.runMacro(macro)

            
            # Return to start position

            self.info("Return to start position " + str(psi_save))
            self.execMacro('freeze', 'psi', psi_save)
            self.execMacro('ubr', h, k, l)
            self.psidevice.write_attribute("Position", psi_save)
                
        else:
            self.output( "Usage:  luppsi rel_startangle  rel_stopangle n_intervals time")


class luppsi_debug(Macro, _diffrac):
    """psi scan:
    
    Relative scan psi angle    
    """ 

    param_def = [
       ['rel_start_angle',  Type.Float,   -999, 'Relative start scan angle'],
       ['rel_final_angle',  Type.Float,   -999, 'Relative final scan angle'],
       ['nr_interv',  Type.Integer, -999, 'Number of scan intervals'],
       ['integ_time', Type.Float,   -999, 'Integration time']
       ]    
  

    def prepare(self, H, K, L, AnglesIndex):
        _diffrac.prepare(self)

    
    def run(self,rel_start_angle,rel_final_angle,nr_interv,integ_time):
        if not self.prepared:
            return
        
        if ((integ_time != -999)):   
            self.diffrac.write_attribute("engine", "hkl") 
            self.diffrac.write_attribute("enginemode", "psi_constant_vertical")
            h = self.h_device.position
            k = self.k_device.position
            l = self.l_device.position
            
            psi_positions = []
            
            psi_save = self.psidevice.Position

            angle_interv = abs(rel_final_angle - rel_start_angle)/nr_interv

            for i in range(0,nr_interv+1):
                self.info("Moving psi to " + str(psi_save + (i+1)*angle_interv))
                self.execMacro('freeze', 'psi', psi_save + (i+1)*angle_interv)
                self.execMacro('ubr', h, k, l)
            
            # Return to start position
            
            self.info("Return to start position " + str(psi_save))
            self.execMacro('freeze', 'psi', psi_save)
            self.execMacro('ubr', h, k, l)
                
        else:
            self.output( "Usage:  luppsi_debug rel_startangle  rel_stopangle n_intervals time")
                      

class savecrystal(Macro,_diffrac):
        
    def prepare(self):
        _diffrac.prepare(self)
        
    def run(self):
        if not self.prepared:
            return

        self.diffrac.write_attribute("SaveCrystal", 1)
                

class load_crystal(Macro, _diffrac):
    """
         load_crystal  - loads crystal information from file
    """

    param_def = [
        ]

    interactive=True

    def prepare(self):
        _diffrac.prepare(self)

    def run( self):
        if not self.prepared:
            return
        active_dir = ""
        try:
            files = os.listdir('/home/'+getpass.getuser()+'/crystals/')
            active_dir = '/home/'+getpass.getuser()+'/crystals/'
        except:
            self.output("Directory for loading files /home/%s/crystals does not exist" % getpass.getuser())
            newdir=self.input("Type new directory")
            try:
                files = os.listdir(newdir)
                active_dir = newdir
            except:
                self.output("New directory %s not found" % newdir)
                return

        res = filter(lambda x: x.endswith('.txt'), files)
        i=1
        for filename in res:

            filename=filename.split('.')[0]
            self.output("(%s) %s" % (i,filename))
            i=i+1
        a0=self.input("Your choice? ")
        try:
            a1=int(a0)
            i=1
            for filename in res:
                if i == int(a0) and i<len(res)+1:
                    file=filename
                i=i+1
            if a1<len(res)+1:
                self.output("")
                self.output("File to load %s" % active_dir+file)
            else:
                self.output("Input out of range!")
 
 
            self.diffrac.write_attribute("loadcrystal", active_dir+file)
            self.diffrac.read_attribute("loadcrystal")
       
        except:
            if a0!="":
                self.output("Wrong input!")
            else:
                self.output("An input file has to be given. Nothing done")




class lattice_cal(Macro, _diffrac):
    """
        lattice_cal - calibrate lattice parameters a, b or c to current 2theta value
    """

    param_def = [
        [ "parameter", Type.String, "", "Parameter" ],
        ]
    interactive=True

    def prepare(self,parameter):
        _diffrac.prepare(self)

    def run( self,parameter):
        if parameter != "":
            if parameter=="a" or parameter=="b" or parameter=="c":
                if parameter == "a":
                    a0=self.diffrac.a
                    self.output("Old lattice parameter %s = %s" % (parameter,a0))
                    h0=self.h_device.position
                    h1=round(h0)
                    a1=h1/h0*a0
                    self.output("New lattice parameter %s = %s" % (parameter,a1))
                    self.diffrac.write_attribute("a", a1)
                if parameter == "b":
                    a0=self.diffrac.b
                    self.output("Old lattice parameter %s = %s" % (parameter,a0))
                    h0=self.k_device.position
                    h1=round(h0)
                    a1=h1/h0*a0
                    self.output("New lattice parameter %s = %s" % (parameter,a1))
                    self.diffrac.write_attribute("b", a1)
                if parameter == "c":
                    a0=self.diffrac.c
                    self.output("Old lattice parameter %s = %s" % (parameter,a0))
                    h0=self.l_device.position
                    h1=round(h0)
                    a1=h1/h0*a0
                    self.output("New lattice parameter %s = %s" % (parameter,a1))
                    self.diffrac.write_attribute("c", a1)

                self.execMacro('compute_u')


            else:
                self.output("Lattice parameter a, b or c")


        else:
            self.output( "Calibration of lattice parameters a, b or c to current 2theta value")
            self.output( "usage:  lattice_cal parameter")





class tw(Macro):
    """
    tw - tweak motor by variable delta
    """

    param_def = [
        ['motor', Type.Moveable, "test", 'Motor to move'],
        ['delta',   Type.Float, -999, 'amount to tweak']
        ]
    interactive=True


    def run( self,motor,delta):
        if delta != -999:
            self.output("Indicate direction with + (or p) or - (or n) or enter")
            self.output("new step size. Type something else (or ctrl-C) to quit.")
            self.output("")
            if np.sign(delta)==-1:
                a="-"
            if np.sign(delta)==1:
                a="+"
            while a in ('+','-','p','n'):
                pos=motor.position
                a=self.input("%s = %s, which way? " % (motor,pos),default_value=a,data_type=Type.String)
                try:
                    a1=float(a)
                    check="True"
                except:
                    check="False"

                if a =="p" and np.sign(delta)<0:
                    a="+"
                    delta=-delta
                if a=="n" and np.sign(delta)>0:
                    a="-"
                    delta=-delta
                if a =="+" and np.sign(delta)<0:
                    delta=-delta
                if a=="-" and np.sign(delta)>0:
                    delta=-delta

                if check=="True":
                    delta = float(a1)
                    if np.sign(delta)==-1:
                        a="-"
                    if np.sign(delta)==1:
                        a="+"
                pos+=delta
                self.mv(motor,pos)


        else:
            self.output("usage: tw motor delta")

class blockprintmove(Macro,_diffrac):


    param_def = [
        ['flagprint', Type.Integer, 0, '1 for printing']
        ]

    def prepare(self, flagprint):
        _diffrac.prepare(self)
        
    def run(self, flagprint):
        if not self.prepared:
            return     
        moving = 1
        tmp_dev = {}
        for angle in self.angle_names:
            tmp_dev[angle] = self.getDevice(self.angle_device_names[angle])
        while(moving):
            moving = 0
            for angle in self.angle_names:
                if tmp_dev[angle].state() == 6:
                    moving = 1
            if flagprint == 1:
                self.outputBlock(" %7.5f  %7.5f  %7.5f" % (self.h_device.position, self.k_device.position, self.l_device.position)) 
                self.flushOutput()
            self.checkPoint()
            time.sleep(1.0)
        if flagprint == 1:
            self.outputBlock(" %7.5f  %7.5f  %7.5f" % (self.h_device.position, self.k_device.position, self.l_device.position)) 
            self.flushOutput()
  
    def on_stop(self):
        _diffrac.on_stop(self)
