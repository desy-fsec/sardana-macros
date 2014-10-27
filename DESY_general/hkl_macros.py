"""
    Macro library containning diffractometer related macros for the macros 
    server Tango device server as part of the Sardana project.
    
"""
import time

from sardana.macroserver.macro import *

class _diffrac:
    """Internal class used as a base class for the diffractometer macros"""

    env = ('DiffracDevice',)
    
    def prepare(self):

        self.prepared = False
        
        dev_name = self.getEnv('DiffracDevice')
        self.diffrac = self.getDevice(dev_name)

        dev_name = self.getEnv('Psi')
        self.psidevice = self.getDevice(dev_name)

        motorlist = self.diffrac.motorlist
        
        pseudo_motor_names = []
        for motor in self.diffrac.hklpseudomotorlist:
            pseudo_motor_names.append(motor.split(' ')[0])
            
        self.h_device = self.getDevice(pseudo_motor_names[0])
        self.k_device = self.getDevice(pseudo_motor_names[1])
        self.l_device = self.getDevice(pseudo_motor_names[2])

        motor_list = self.diffrac.motorlist

        self.nb_motors = len(motor_list)        
        self.angle_names = []
        
        if self.nb_motors == 4:
            self.angle_names.append("omega")
            self.angle_names.append("chi")
            self.angle_names.append("phi")
            self.angle_names.append("theta")
        elif self.nb_motors == 6:
            self.angle_names.append("mu")
            self.angle_names.append("th")
            self.angle_names.append("chi")
            self.angle_names.append("phi")
            self.angle_names.append("gamma")
            self.angle_names.append("delta")

        prop = self.diffrac.get_property(['DiffractometerType'])        
        for v in prop['DiffractometerType']:       
            self.type = v
        
        self.angle_device_names = {}
        i = 0
        for motor in motor_list:
            self.angle_device_names[self.angle_names[i]] = motor.split(' ')[0]
            i = i + 1

        self.prepared = True

    def on_abort(self):
        
        for angle in self.angle_names:
            angle_dev = self.getDevice(self.angle_device_names[angle])
            angle_dev.Stop()

class br(Macro, _diffrac):
    """The br macro is used to move the diffractometer to the reciprocal space 
    coordinates given by H, K and L. If a fourth parameter is given, the combination
    of angles to be set is the correspondig to the given index. The index of the
    angles combinations are then changed."""


    param_def = [
       ['H', Type.Float, None, "H value"],
       ['K', Type.Float, None, "K value"],
       ['L', Type.Float, None, "L value"],
       ['AnglesIndex', Type.Integer, -1, "Angles index"]
    ]

    def prepare(self, H, K, L, AnglesIndex):
        _diffrac.prepare(self)
        
    def run(self, H, K, L, AnglesIndex):
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

        self.execMacro('printmove')

class ubr(Macro):
    """
        ubr H K L
    """

    param_def = [
        [ "hh", Type.Float, -999, "H position" ],
        [ "kk", Type.Float, -999, "K position" ],
        [ "ll", Type.Float, -999, "L position" ]
        ]

    
    def run( self, hh,kk,ll):

        if ll != -999:        
            br, pars = self.createMacro("br", hh, kk, ll)
            self.runMacro(br)
        else:
            self.output( "usage:  ubr H K L [Trajectory]")
           
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

        self.output("%s %7.5f" % ("Azimuth (Psi) = ",self.psidevice.Position))
        self.output("%s %7.5f" % ("Wavelength = ", self.diffrac.WaveLength))
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

            
            self.output("Azimuth (Psi) = %7.5f" % (self.psidevice.Position))
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
        
        if self.type == 'E6C':
            str_type = "Eulerian 6C"        
        elif self.type == 'E4CV':
            str_type = "Eulerian 4C Vertical"
            
        self.output("%s Geometry, %s" % (str_type, self.diffrac.enginemode))
        self.output("Sector %s" % "[ToDo]")
        self.output("")

        reflections = self.diffrac.reflectionlist
        
        nb_ref = 0
        if reflections != None:
            for ref in reflections:
                if nb_ref < len(self.suffix): sf = self.suffix[nb_ref]
                else: sf = self.suffix[3]
                self.output("  %d%s Reflection (index %d): " % (nb_ref+1, sf, ref[0]))
                self.output("  H K L : %10.4f %10.4f %10.4f" % ref[1], ref[2], ref[3])
                self.output("  Affinement, Relevance : %d %d" % ref[4], ref[5])
                if len(ref) > 10:
                    self.output("mu theta chi phi gamma delta: %10.4f %10.4f %10.4f %10.4f %10.4f %10.4f" % ref[6], ref[7], ref[8], ref[9], ref[10], ref[11])
                else:
                    self.output("ommega chi phi theta: %10.4f %10.4f %10.4f %10.4f" % ref[6], ref[7], ref[8], ref[9])
                nb_ref = nb_ref + 1
                    
       
        self.output("  Lattice Constants (lengths / angles):")
        self.output("%24s = %s %s %s / %s %s %s" % ("real space", self.diffrac.a, 
                                                    self.diffrac.b, self.diffrac.c, self.diffrac.alpha, 
                                                    self.diffrac.beta, self.diffrac.gamma))
  
        
        self.output("  Azimuthal Reference:")
        self.output("")
        self.output("%24s = %s" %("[ToDo]","[ToDo]"))
        self.output("")
        self.output("%24s = %s" %("Lambda",self.diffrac.WaveLength))
        self.output("")
        self.output(" Cut Points:")
        self.output("    [ToDo]")

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
        self.output("%s %s %3s %9.5f %9.5f %9.5f " %
                    ("H","K","L = ",self.h_device.position,self.k_device.position,self.l_device.position))

        if self.diffrac.psirefh == -999:
            self.output("")
        else:
            self.output("%8s %9.5f %9.5f %9.5f " % 
                        ("Ref   = ",self.diffrac.psirefh,self.diffrac.psirefk,self.diffrac.psirefl))
            
        self.output("%s %7.5f" % ("Azimuth (Psi) = ",self.psidevice.Position))
        self.output("%s %7.5f" % ("Wavelength = ", self.diffrac.WaveLength))
        self.output("")

        str_pos1 = "%7.5f" % self.getDevice(self.angle_device_names['delta']).Position
        str_pos2 = "%7.5f" % self.getDevice(self.angle_device_names['th']).Position
        str_pos3 = "%7.5f" % self.getDevice(self.angle_device_names['chi']).Position
        str_pos4 = "%7.5f" % self.getDevice(self.angle_device_names['phi']).Position
        str_pos5 = "%7.5f" % self.getDevice(self.angle_device_names['mu']).Position
        str_pos6 = "%7.5f" % self.getDevice(self.angle_device_names['gamma']).Position
        
        self.output("%10s %11s %12s %11s %10s %11s" %("Delta","Theta","Chi","Phi","Mu","Gamma"))
        self.output("%10s %11s %12s %11s %10s %11s" % 
                    (str_pos1, str_pos2, str_pos3, str_pos4, str_pos5, str_pos6))

class diffrac_setmode(Macro, _diffrac):
    """Set operation mode.""" 
    
    param_def = [
       ['new_mode', Type.Integer, -1, "Mode to be set"]
    ]    
   
    def prepare(self, new_mode):
        _diffrac.prepare(self)
        
    def run(self, new_mode):
        if not self.prepared:
            return   
        
        modes = self.diffrac.enginemodelist
        
        if new_mode == -1:
            self.output("Available modes:") 
            imode = 1
            for mode in modes:
                self.output(" %d -> %s " % (imode, mode))
                imode = imode + 1
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

class diffrac_getmode(Macro, _diffrac):
    """Get operation mode."""
    
    def prepare(self):
        _diffrac.prepare(self)
        
    def run(self):
        if not self.prepared:
            return
        
        self.output(self.diffrac.enginemode)



class diffrac_setlat(Macro, _diffrac):
    """Set the crystal lattice parameters a, b, c, alpha, beta, gamma.
       for the currently active diffraction pseudo motor controller."""  
    
    param_def = [
       ['a', Type.Float, None, "Lattice 'a' parameter"],
       ['b', Type.Float, None, "Lattice 'b' parameter"],
       ['c', Type.Float, None, "Lattice 'c' parameter"],
       ['alpha', Type.Float, None, "Lattice 'alpha' parameter"],
       ['beta',  Type.Float, None, "Lattice 'beta' parameter"],
       ['gamma', Type.Float, None, "Lattice 'gamma' parameter"]
    ]

    hints = { 'interactive' : 'True' }

    def prepare(self, a, b, c, alpha, beta, gamma):
        _diffrac.prepare(self)
    
    def run(self, a, b, c, alpha, beta, gamma):
        if not self.prepared:
            return
        
        self.diffrac.write_attribute("a", a)        
        self.diffrac.write_attribute("b", b)        
        self.diffrac.write_attribute("c", c)        
        self.diffrac.write_attribute("alpha", alpha)        
        self.diffrac.write_attribute("beta", beta)        
        self.diffrac.write_attribute("gamma", gamma)
     
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

        values = []                 
        values.append(0)        
        values.append(H)        
        values.append(K)
        values.append(L)
        self.diffrac.write_attribute("AddReflectionWithIndex", values) 


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

        values = []                 
        values.append(1)        
        values.append(H)        
        values.append(K)
        values.append(L)
        self.diffrac.write_attribute("AddReflectionWithIndex", values) 

class setor0(Macro, _diffrac):
    """Set primary orientation reflection. Alternative to or0""" 
    
    def prepare(self):
        _diffrac.prepare(self)
    
    def run(self):
        if not self.prepared:
            return
              
        H = self.h_device.position
        K = self.k_device.position
        L = self.l_device.position

        values = []                 
        values.append(0)        
        values.append(H)        
        values.append(K)
        values.append(L)
        
        self.diffrac.write_attribute("AddReflectionWithIndex", values)

class setor1(Macro, _diffrac):
    """Set secondary orientation reflection. Alternative to or1""" 
    
    def prepare(self):
        _diffrac.prepare(self)
    
    def run(self):
        if not self.prepared:
            return
              
        H = self.h_device.position
        K = self.k_device.position
        L = self.l_device.position

        values = []                 
        values.append(1)        
        values.append(H)        
        values.append(K)
        values.append(L)
        
        self.diffrac.write_attribute("AddReflectionWithIndex", values)

class setorn(Macro, _diffrac):
    """Set orientation reflection indicated by the index.""" 
    
    param_def = [
        ['i', Type.Integer, None, "reflection index (starting at 0)"],
    ]
 
    
    def prepare(self):
        _diffrac.prepare(self)
    
    def run(self):
        if not self.prepared:
            return
              
        H = self.h_device.position
        K = self.k_device.position
        L = self.l_device.position

        values = []                 
        values.append(i)        
        values.append(H)        
        values.append(K)
        values.append(L)
        
        self.diffrac.write_attribute("AddReflectionWithIndex", values)


class or_swap(Macro, _diffrac):
    """Swap values for primary and secondary vectors."""
    
    def prepare(self):
        _diffrac.prepare(self)
    
    def run(self):
        if not self.prepared:
            return

        self.diffrac.write_attribute("SwapReflections01", 0)

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
            

class printmove(Macro,_diffrac):


    def prepare(self):
        _diffrac.prepare(self)
        
    def run(self):
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
            self.output("H = %7.5f  K = %7.5f L = %7.5f" % (self.h_device.position, self.k_device.position, self.l_device.position)) 
            self.flushOutput()
            time.sleep(1.0)
        self.output("H = %7.5f  K = %7.5f L = %7.5f" % (self.h_device.position, self.k_device.position, self.l_device.position)) 
        self.flushOutput()
  
