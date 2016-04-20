from sardana.macroserver.macro import Macro, Type
import math as m
import numpy as np
import taurus
import undulator
from bl13constants import *

# self.info() = output in blue    
# self.error() = output in red
# self.output() = output in black


#Gamma = 2.955/EMASS  #2.965 inf point
#kadjust_offset = 1.2
#kadjust_slope = 1.021
#kadjust_harm = -0.05

#Gamma = 2.963/EMASS  #2.965 inf point
#kadjust_offset = 1.7
#kadjust_slope = 1.021
#kadjust_harm = -0.05

# adjust E to get 2/3 intensity at E 13.5720 ugap 7159.0 harm 7  (k=1.40000)
Gamma = 2.955/EMASS
kadjust_offset = 1.4
kadjust_slope = 1.021
kadjust_harm = -0.05
# working set, centered #7, E curtes al #5, E llarges al #9
#Gamma = 2.96/EMASS
#kadjust_offset = 1.532
#kadjust_slope = 1.02



class scanEgap(Macro):
    '''Scan Energy and gap.
    Selects automatically harmonic with minimum allowed gap, unless specified
    Can choose 'InfPoint or Peak'. 'Peak' still not available.
    '''

    param_def = [ [ 'E_0', Type.Float, None, 'init E in keV'],
                  [ 'E_1', Type.Float, None, 'final E in keV'],
                  [ 'harmonic', Type.Float, 7, 'harmonic to surf'],
                  [ 'npoints', Type.Float, 0, 'number of scan points']
                ]

    def run(self, E_0, E_1, harmonic, npoints):
    
        '''Scans the undulator gap for a given energy
        
        Takes the shift between actual E and the harmonic, and surfs E with that shift 

        '''
        LambdaU = bl13constants.LambdaU/1000 # LambdaU in mm

        tolerancegap = 2.           # Tolerance of gap, in um
        a2 = +0.0005087060
        a1 = -0.1592998865 
        a0 = m.exp(1.4508580534)

        Energy_0 = taurus.Device("E").position
        
        gap_0 = taurus.Device("ugap").position
        K_0 = undulator.Ktheo_fromugap(gap_0/(LambdaU*1E6))
        wavelength1K_0 = (1+.5*K_0**2)*(LambdaU*1E10)/2/Gamma**2
        print wavelength1K_0
        energyK_0 = HCKEVA/wavelength1K_0
        energyKh_0 = harmonic*energyK_0
        # E shift from exact harmonic
        Eshift = Energy_0 - energyKh_0 
        print Eshift, ' = ', Energy_0, ' - ', energyKh_0
        Energy = np.linspace(E_0, E_1, npoints+1)
        lastE_ugapchange = E_0
        lastgap = gap_0
        
        KphotonE = gapphotonE = []
        for photonE in Energy:
            energyharm = photonE-Eshift
            k = (np.sqrt(4.0*HCEVA*ANGS*Gamma**2/(LambdaU*(energyharm/harmonic*1000.))-2.0))
            KphotonE.append(k)
            gap = 1000*(-a1 - np.sqrt(a1**2 + 4.0*a2*np.log(k/a0)))/(2.0*a2) 
            gapphotonE.append(gap)        
            if abs(gap-lastgap) > tolerancegap:
                #move gap
                lastgap = gap
                lastE_ugapchange = photonE
                macro_cmd1 = 'mv ugap %.1f E %.4f' % (gap, photonE)
                macro_cmd2 = 'Do   : E %.4f ugap %.1f K = %f' % (photonE, gap, k)
#                self.execMacro(macro_cmd1)
                print macro_cmd1
                print macro_cmd2
            else:
                # do not move gap
                macro_cmd2 = 'No mv: E %.4f ugap %.1f K = %f' % (photonE, gap, k)
                print macro_cmd2

        for epoint in Energy:
            print '%f\t%f' %(epoint, epoint)
                
                



class scangap(Macro):
    '''Scan Energy surfing the harmonic.
    If Energy and ugap not given, current values are taken from Pool
    '''

    param_def = [ [ 'DE', Type.Float, None, 'step in keV'],
                  [ 'harmonic', Type.Float, -1, 'harmonic to surf'],
                  [ 'Energy', Type.Float, -1, 'Energy to be used, keV'],
                  [ 'ugap', Type.Float, -1, 'undulator gap in um']
                ]

    def run(self, DE, harmonic, Energy, gap_0):
    
        '''to calculate the undulator gap for a given energy
        
        If harmonic = -1 or is not given, takes the nearest
        If no Energy, gap values given, use values from Pool
        '''
        LambdaU = bl13constants.LambdaU/1000 # LambdaU in mm

        if Energy == -1:
            Energy = taurus.Device("E").position
        if gap_0 == -1:
            gap_0 = taurus.Device("ugap").position
        print 'Scanning Energy\nharmonic = %i, energy shift %f keV\nEnergy=%f keV\tugap=%f um\n' %(harmonic, DE, Energy, gap_0)
        # Parameters K -> gap
        a2 = +0.0005087060
        a1 = -0.1592998865 
        a0 = m.exp(1.4508580534)
        gap_0mm = gap_0/1000.             #gap  in mm
        gapN = (gap_0/1000.)/(LambdaU*1000.)     #ugap in um, gapN = Normalized gap
        Kgap_0 = undulator.Ktheo_fromugap(gapN)
        # Parameters gap -> K
        k6 = +1.558
        k5 = -6.5607
        k4 = +11.183
        k3 = -9.8504
        k2 = +4.8059
        k1 = -4.4219
        k0 = +1.5195
#       Kgap_0 = m.exp(k6*gapN**6 + k5*gapN**5 + k4*gapN**4 + k3*gapN**3+ k2*gapN**2 + k1*gapN + k0)

        # Calculate the corresponding K for the new E
        if harmonic == -1: 
            Ktrial = []
            GAPtrial = []
            for harmonic in range(1,17):
                energy1 = Energy/harmonic
                Ktrial.append(np.real(np.sqrt(4.0*HCEVA*ANGS*Gamma**2/(LambdaU*energy1)-2.0)))
                lastHarm = len(Ktrial)-1
                GAPtrial.append( (-a1 - np.sqrt(a1**2 + 4.0*a2*np.log(Ktrial[lastHarm]/a0)))/(2.0*a2) )        
                print 'harmonic %i\tEnergy1=%.3f keV\tugap=%.1f um\tK=%f' % (harmonic, energy1/1000., GAPtrial[lastHarm]*1000, Ktrial[lastHarm] )
                # Must now implement a method to take the lowest harmonic with GAPtrial>= 5700.
                # Then, redefine harmonic
  
        wavelength1_0 = (1+.5*Kgap_0**2)*(LambdaU*1E10)/2/Gamma**2
        energy1_0 = HCKEVA/wavelength1_0
        
        # Now apply shift in Energy DE
        energy1 = energy1_0 + DE/harmonic
        Kgap = np.real(np.sqrt(4.*HCEVA*ANGS*Gamma**2/(LambdaU*energy1*1000.)-2.))
        GAP =  1000*(-a1 - np.sqrt(a1**2 + 4.*a2*np.log(Kgap/a0)))/(2.*a2)       
        
 
        print 'wavelength=%f\tEnergy=%f' % (wavelength1_0, energy1_0)
        print 'Kgap_0  = %f\tKgap  = %f' % (Kgap_0, Kgap)
        print 'gap_0  = %f\tGAP  = %f' % (gap_0, GAP)
 
        energy1 = Energy/harmonic
        K = np.real(np.sqrt(4.*HCEVA*ANGS*Gamma**2/(LambdaU*energy1)-2.))
        GAP =  (-a1 - np.sqrt(a1**2 + 4.*a2*np.log(K/a0)))/(2.*a2)       



class mvEgap(Macro):
    '''Move Energy and gap.
    Selects automatically harmonic with minimum allowed gap, unless specified
    Can choose 'InfPoint or Peak'. 'Peak' still not available.
    '''

    param_def = [ [ 'E', Type.Float, None, 'Energy in keV'],
                  [ 'harmonic', Type.Float, 0, 'harmonic to surf'],
                  [ 'position', Type.String, 'InfPoint', 'InfPoint or Peak at harmonic']
                 ]

    def run(self, Energy, harmonic, position):
    
        '''to calculate the undulator gap for a given energy
        
        If harmonic <1, takes the nearest
        If no Energy, gap values given, use values from Pool
        '''
        LambdaU = bl13constants.LambdaU/1000. # LambdaU in mm

        Energy_0 = taurus.Device("E").position
        gap_0 = taurus.Device("ugap").position
        
        self.output('Initial: harm = %i\tEnergy=%.4f keV\tugap=%.2f um' \
            %(harmonic, Energy_0, gap_0))

        # Parameters K -> gap
        a2 = +0.0005087060
        a1 = -0.1592998865 
        a0 = m.exp(1.4508580534)
        gap_0mm = gap_0/1000.             #gap  in mm
        gapN = (gap_0/1000.)/(LambdaU*1000.)     #ugap in um, gapN = Normalized gap

        # Calculate the corresponding K for the new E
        if harmonic < 1: 
            Ktrial = []
            GAPtrial = []
            energy1trial = []
            for harmonic in range(1,20):      # range(1,20) if also even harmonics are to be calculated
                energy1trial.append (1000*Energy/harmonic)
                lastHarm = len(energy1trial)-1
                Ktrial.append( (np.sqrt(4.0*HCEVA*ANGS*Gamma**2/(LambdaU*energy1trial[lastHarm])-2.0)))
                GAPtrial.append( (-a1 - np.sqrt(a1**2 + 4.0*a2*np.log(Ktrial[lastHarm]/a0)))/(2.0*a2) )        
                #GAPtrial.append( (-a1 - np.sqrt(a1**2 + 4.0*a2*np.log(Ktrial[lastHarm]/a0)))/(2.0*a2) )        
                self.output('harmonic #%i\tE_1 = %.4f keV\tugap=%.2f um\tK=%.5f' % (harmonic, energy1trial[lastHarm]/1000., GAPtrial[lastHarm]*1000, Ktrial[lastHarm] ))
            # Take the lowest harmonic with GAPtrial>= 5700.
            # Then, redefine harmonic
            GAPallowed = list(filter((lambda gapu: gapu>XALOCmingap/1000.), GAPtrial))
            minimumindex = GAPtrial.index( GAPallowed[len(GAPallowed)-1] )
            harmonic = 2*(minimumindex/2) + 1    # Change to minimumindex + 1 if also even harmonics are to be considered
  
        # Calculating final conditions
        energy1 = Energy/harmonic
        Kgap = np.real(np.sqrt(4.*HCEVA*ANGS*Gamma**2/(LambdaU*energy1)-2.))

        self.info('Theoretical Conditions (6th deg polinomial fit)')
        GAP_THEO = undulator.ugaptheo_fromK6(Kgap)
        self.output('harmonic #%i\tE_1 = %.4f keV\tugap=%.2f um\tK=%.5f' % (harmonic, energy1, GAP_THEO, Kgap ))

        Kgap = kadjust_offset + kadjust_slope*(1.+kadjust_harm*(harmonic-7.)/7.)*(Kgap-kadjust_offset)

        #GAP =  1000.*(-a1 - np.sqrt(a1**2 + 4.*a2*np.log(Kgap/a0)))/(2.*a2)       
        #self.info('Practical Conditions')
        #self.output('harmonic #%i\tE_1 = %.4f keV\tugap=%.2f um\tK=%.5f' % (harmonic, energy1, GAP, Kgap ))

        self.info('Practical Conditions (6th deg polinomial fit)')
        GAP = undulator.ugaptheo_fromK6(Kgap)
        self.output('harmonic #%i\tE_1 = %.4f keV\tugap=%.2f um\tK=%.5f' % (harmonic, energy1, GAP, Kgap ))
   
        macro_cmd1 = 'mv E %.4f ugap %.2f' % (Energy, GAP_THEO)
        macro_cmd2 = 'mvr E %.4f ugap %.2f' % (Energy-Energy_0, GAP_THEO - gap_0)
        self.output(macro_cmd2)
        self.output(macro_cmd1)
#       self.execMacro(macro_cmd1)
#       self.output() = macro_cmd



class mvrEgap(Macro):
    '''Move Energy surfing the harmonic.
    Default harmonic is #7
    If Energy and ugap not given, current values are taken from Pool
    '''

    param_def = [ [ 'DE', Type.Float, None, 'step in keV'],
                  [ 'harmonic', Type.Float, 7, 'harmonic to surf'],
                  [ 'Energy', Type.Float, -1, 'Energy to be used, keV'],
                  [ 'ugap', Type.Float, -1, 'undulator gap in um']
                ]


    def run(self, DE, harmonic, Energy, gap_0):
    
        '''to calculate the undulator gap for a given energy
        
        If harmonic = -1, takes the nearest
        If no Energy, gap values given, use values from Pool
        '''
        
        LambdaU = bl13constants.LambdaU/1000 # LambdaU in mm

        if Energy == -1:
            Energy = taurus.Device("E").position

        if gap_0 == -1:
            gap_0 = taurus.Device("ugap").position
        print 'Moving E. Initial conditions\nharmonic = %i, energy shift %.4f keV\nEnergy=%.4f keV\tugap=%.1f um\n' \
            %(harmonic, DE, Energy, gap_0)

        # Parameters K -> gap
        a2 = +0.0005087060
        a1 = -0.1592998865 
        a0 = m.exp(1.4508580534)
        gap_0mm = gap_0/1000.             #gap  in mm
        gapN = (gap_0/1000.)/(LambdaU*1000.)     #ugap in um, gapN = Normalized gap
        Kgap_0 = getKgap(gapN)

        # Calculate the corresponding K for the new E
        if harmonic == -1: 
            Ktrial = []
            GAPtrial = []
            for harmonic in range(1,17):
                energy1 = Energy/harmonic
                Ktrial.append(np.real(np.sqrt(4.0*HCEVA*ANGS*Gamma**2/(LambdaU*energy1)-2.0)))
                lastHarm = len(Ktrial)-1
                GAPtrial.append( (-a1 - np.sqrt(a1**2 + 4.0*a2*np.log(Ktrial[lastHarm]/a0)))/(2.0*a2) )        
                print 'harmonic %i\tEnergy1=%.3f keV\tugap=%.1f um\tK=%f' % (harmonic, energy1/1000., GAPtrial[lastHarm]*1000, Ktrial[lastHarm] )
                # Must now implement a method to take the lowest harmonic with GAPtrial>= 5700.
                # Then, redefine harmonic
  
        wavelength1_0 = (1+.5*Kgap_0**2)*(LambdaU*1E10)/2/Gamma**2
        energy1_0 = HCKEVA/wavelength1_0
        
        # Now apply shift in Energy DE
        energy1 = energy1_0 + DE/harmonic
        Energy = Energy + DE
        Kgap = np.real(np.sqrt(4.*HCEVA*ANGS*Gamma**2/(LambdaU*energy1*1000.)-2.))
        GAP =  1000*(-a1 - np.sqrt(a1**2 + 4.*a2*np.log(Kgap/a0)))/(2.*a2)       
        
        print 'wavelength=%f\tEnergy=%f' % (wavelength1_0, energy1_0)
        print 'Calculated\nKgap_0  = %f\tFinal Kgap  = %f' % (Kgap_0, Kgap)
        print 'gap_0  = %f\tFinal GAP  = %f\n' % (gap_0, GAP)
 
        macro_cmd1 = 'umv ugap %f E %f' % (GAP, Energy)
        macro_cmd2 = 'umvr ugap %f E %f' % (GAP-gap_0, DE)
        print macro_cmd1
        print macro_cmd2
#       self.execMacro(macro_cmd1)
#       self.output() = macro_cmd






#    self.info('\nharmonic %i\tEnergy=%f keV\tugap=%f um\n' % (harmonic, energy/1000, GAP*1000)

#    macro_cmd1 = 'mv ugap %f E %f' % (energy, GAP)
    # self.execMacro(macro_cmd1)
#    self.output() = macro_cmd








