from sardana.macroserver.macro import Macro, Type
import taurus
import time
from epsf import *
from bl13constants.bl13constants import YAGZ_OUT_POSITION, YAGZ_DIODE_POSITION, YAGY_SAFETYPOSITION
import diagnostics

class flux_measure(Macro):

    '''flux_measure: macro to measure automatically the flux
    2015.05.10 - Now actuating the DUSP (yagy, yagz) and not diodesamp. See deprecated macro flux_measure_diodesamp'''

    param_def = [ 
                  [ 'writeflux', Type.String, '0', '0/1 write flux at sample to beamline variables FLUXLAST, FLUXLASTNORM and FLUXLASTTIME']
                ]
                
    def run(self, writeflux):
      
        # DEFINE DEVICES 
        bstopz = self.getMoveable("bstopz")
        yagy = self.getMoveable("yagy")
        yagz = self.getMoveable("yagz")
        mbattrans = self.getMoveable("mbattrans")
        eps = taurus.Device('bl13/ct/eps-plc-01')
        blight = self.getDevice('tango://blight')
        try:
            bstopz.pos = bstopz.getPosition()
            yagy_posinit = yagy.getPosition()
            yagz.pos = yagz.getPosition()
            transmission_val_init = mbattrans.getAttribute('Position').read().value
        except:
            msg = 'FLUX_MEASURE: Problem in reading some motor positions, could be yagy, yagz, bstopz or mbattrans'
            self.error(msg)
            raise Exception(msg)
        writeflux = writeflux.lower()
        sample_moved_yagy = False
        
        # CLOSE DETECTOR COVER
        self.info('FLUX_MEASURE: Close the detector cover')
        self.execMacro('act detcover in')
        limit = 0
        while eps['detcover'].value != 0: 
            self.warning('FLUX_MEASURE: Waiting for the det cover to be IN')
            limit = limit + 1
            if limit > 30:
                self.error('FLUX_MEASURE ERROR: Cannot close the det cover')
                return
            time.sleep(0.3)
               
        # REMOVE LN2 COVER
        self.info('FLUX_MEASURE: Remove the LN2 cover')
        if epsf('read','ln2cover')[2] != 1:
	  #self.warning('FLUX_MEASURE WARNING: LN2 cover is IN')
           self.execMacro('act ln2cover out')
          #  for trials in range(20):
           #  if epsf('read','ln2cover')[2] == 1:
            #    break
           #  time.sleep(.2)
        limit = 1
        while epsf('read','ln2cover')[2] != 1: #or eps['ln2cover'].quality != PyTango._PyTango.AttrQuality.ATTR_VALID:
           self.info("FLUX_MEASURE WARNING: waiting for the LN2 cover to be removed")
           limit = limit + 1
           if limit > 50:
              self.error("FLUX_MEASURE ERROR: There is an error with the LN2 cover")
              return
           time.sleep(0.5)

        # SET BACK LIGHT OUT 
        if epsf('read','backlight')[2] != 1: 
           self.execMacro('act backlight out')              
           for trials in range(50):
               if epsf('read','backlight')[2] == 1:
                  break
               time.sleep(0.2)

        # CHECK THAT THE BACKLIGHT IS OFF, IF IT GIVES AN EXCEPTION THE MACRO SHOULD STOP HERE
        if blight['Value'].value != '0': blight.write_attribute('Value', 0) 

        self.info('FLUX_MEASURE: 100% transmission')
        self.execMacro('mv mbattrans 100')

        time.sleep(1)
       
        self.info('FLUX_MEASURE: Opening shutters')
        try:
            self.execMacro('openbeam exp')
        except:
            self.error('FLUX_MEASURE: Problem in opening shutters')
            return

        self.info('FLUX_MEASURE: Inserting yagdiode')
        try:
            self.execMacro('act yagdiode in')
        except:
            self.error('FLUX_MEASURE: Cant move yagdiode in. Aborting...')
            return
        
        # FLUX MEASUREMENT
        time.sleep(1)
        if writeflux == '1':
            self.info('FLUX_MEASURE: Flux measurement and writing to variables')
            self.execMacro('flux sample 1')
        
        if writeflux == '0' or writeflux == '':
            self.info('FLUX_MEASURE: Flux measurement only')
            self.execMacro('flux sample')
        
        current_bstopz_pos = bstopz.getPosition()
        if abs(current_bstopz_pos)<3:
            self.warning("FLUX_MEASURE: Warning: Beam stop and colimator are in place") 
        else:
            self.warning("FLUX_MEASURE: Warning: Beam stop and colimator are NOT in place")

       
        self.info('FLUX_MEASURE: closing fast shutter')
        self.execMacro('ni660x_shutter_open_close close')
        
        # CHANGE TRANSMISSION TO INITIAL VALUE
        self.info('FLUX_MEASURE: Move transmission to %d' %int(transmission_val_init))
        self.execMacro('mv mbattrans %d' %int(transmission_val_init))
       
        # CLOSE THE SLOW SHUTTER
        self.info('FLUX_MEASURE: closing slow shutter')
        try: 
            self.execMacro('act slowshu in') 
        except:
            self.error('FLUX_MEASURE ERROR: Cannot actuate the slowshu')
            return
        
        # CLOSE THE SAFETY SHUTTER 
        self.info('FLUX_MEASURE: Safety shutter in')
        if epsf('read','pshu')[2] != 0:
            try:
                self.execMacro('act pshu close')
                time.sleep(3)
            except:
                self.error('FLUX_MEASURE ERROR: Cannot actuate the safety shutter')
                return   
             
        self.info('FLUX_MEASURE: removing yagdiode')
        try:
            self.execMacro('act yagdiode out')
        except:
            self.error('FLUX_MEASURE: Cant move yagdiode out. Sample might be out of center (check omegay and omegaz)')
            return
      

class flux(Macro):

    '''flux: macro to find photon flux of the beamline
    diodes are: detector, sample, all
    Writes the flux sample diode on Variables (FLUXLAST, FLUXLASTNORM, FLUXLASTTIME) if requested
    '''

    param_def = [ 
                  [ 'diodename', Type.String, 'all', 'diode name: sample, detector, all'],
                  [ 'writeflux', Type.String, 'nowrite', '0/1 write flux at sample to beamline variables FLUXLAST, FLUXLASTNORM and FLUXLASTTIME']
                ]

    def run(self,diodename,writeflux):
       dictdiode={'sample':'bl13/di/emet-06-diodes','detector':'bl13/di/emet-06-diodes'}
       diodename = diodename.lower()
       writeflux = writeflux.lower()
       if writeflux == 'yes' or writeflux == 'y' or writeflux == 'write' or writeflux == '1':
           writeflux == '1'
       

       # Initial Conditions
#       diosamdev = taurus.Device('expchan/eh_emetdiodes_ctrl/2')
#       idiodesamp = diosamdev.getAttribute('value').read().value
       diosamdev = taurus.Device('bl13/di/emet-06-diodes')
       idiodesamp = diosamdev.getAttribute('i1').read().value
       mA = 1000.
       minimumdiodecurrent = 3E-5 #range MUST BE 1mA
       mbattrans = self.getMoveable("mbattrans")
       E = self.getMoveable("E")
       ugap = self.getMoveable("ugap")
       Eugap = self.getMoveable("Eugap")
       transmission = mbattrans.getAttribute('Position').read().value
       energy = E.getAttribute('Position').read().value
       msg = 'FLUX: Photon Energy is %.4f keV\nFLUX: MBAT transmission is set at %.2f%%' %(energy, transmission)
       #msg += 'FLUX: The ugap is %f, tune is %f' % (ugap.getAttribute('Position').read().value, Eugap.getAttribute('tune').read().value)
       self.info(msg)
       
       # Sample Diode
       if diodename == 'sample' or diodename == 'all' or diodename == '':
           name = 'sample'
           
           #JJ 2016.09.22 aparently the diode needs some time to be placed, adjust range, whatever might be. Set to 2 seconds arbitrarily
           time.sleep(2.)
           diodeflux = diagnostics.samplediode.Flux()
           msg = 'FLUX Old Calib: Flux at %s diode is %.3e ph/s (valid in 7<E<12.658 keV)' %(name, diodeflux[0])
           self.info(msg)
           fluxnorm = diodeflux[1]  #*100./transmission
           msg = 'FLUX Old Calib: Normalized Flux at %s diode is %.3e ph/s/250mA at 100%% MBAT transmission' %(name, fluxnorm)
           self.info(msg)

           # 20160302 JJ New Calibration / TESTING
           diodeflux = diagnostics.samplediode.Flux_new()
           msg = 'FLUX NEW CALIB: Flux at %s diode is %.3e ph/s (valid in 7<E<12.658 keV)' %(name, diodeflux[0])
           self.info(msg)
           fluxnorm = diodeflux[1]  #*100./transmission
           msg = 'FLUX NEW CALIB: Normalized Flux at %s diode is %.3e ph/s/250mA at 100%% MBAT transmission' %(name, fluxnorm)
           self.info(msg)
           self.warning('FLUX: Current at %s diode is %.2e mA (range=%s, minimum: +%.1e mA)' %(name, idiodesamp*mA,diosamdev.range_ch1,minimumdiodecurrent*mA))

           if idiodesamp >= minimumdiodecurrent:
               fluxlast = diodeflux[0]
               fluxlastnorm = fluxnorm
               
           

       # Detector Diode
       if diodename == 'detector' or diodename == 'all' or diodename == '':
           name = 'detector'
           diodeflux = diagnostics.detectordiode.Flux()
           msg = 'FLUX: Flux at %s diode is %.3e ph/s' %(name, diodeflux[0])
           self.info(msg)
           fluxnorm = diodeflux[1]
           msg = 'FLUX: Normalized Flux at %s diode is %.3e ph/s/250mA at 100%% MBAT transmission' %(name, fluxnorm)
           self.info(msg)

       if writeflux!='1': return

       # Do not write in Variables is sample current is not high enough
       if idiodesamp<minimumdiodecurrent and writeflux == '1' and diodename !='detector':
           writeflux = 'NO'
           msg = 'FLUX: Current at Sample diode is %.2e mA (minimum: +%.1e mA). Writing to Variables is denied' %(idiodesamp*mA, minimumdiodecurrent*mA)
           self.warning(msg)
           self.warning('FLUX: Probably sample Diode is not in place, or there is too much attenuation')
           return

       # Write to Variables
       if diodename == 'detector':
           self.warning('FLUX: %s diode is not writtable to Variables' %diodename)
       elif diodename == 'sample' or diodename == 'all' or diodename == '':
           vars = taurus.Device('bl13/ct/Variables')
           vars.write_attribute('fluxlast',fluxlast)
           vars.write_attribute('fluxlastnorm',fluxlastnorm)
           vars.write_attribute('fluxlasttime',time.asctime())
           self.info('FLUX: Flux on sample diode written in bl13/ct/Variables')
#          vars['fluxlast']=fluxlast
#          vars['fluxlastnorm']=fluxlastnorm

