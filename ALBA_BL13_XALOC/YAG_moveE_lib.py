#2016

import time
import numpy
#import PIL.Image
import PyTango
import taurus
import diftab
import transmission
import diffractometer
#from bl13constants import OAV_CENTER_X_PX, OAV_CENTER_Y_PX

from sardana.macroserver.macro import Macro, Type
from bl13constants import OAV_BW_device_name

#ScaleFactorX = 100/68.2
#ScaleFactorY = 100./68.7

class YAG_moveE(Macro):
    """
    Macro to change the E and realign the beam and the sample by moving diffractometer table
    The macro zooms the image, corrects transmission, moves E and aligns the beam
    IT ASSUMES THAT YAG SCREEN IS AT SAMPLE POSITION
    Changes of mirror stripes Rh<->Ir may be included. Correction in diftab is done, but stripes are not effectively changed!
    """
    param_def = [ 
                  [ 'Efinal', Type.Float, -9, 'Final Photon Energy in keV'],
                  [ 'StripesCorrection', Type.String, 'NO', 'YES / NO'],
                  [ 'mode', Type.String, 'FAST', 'FAST / COMPLETE']
                ]

    def run(self, Efinal, StripesCorrection, mode):
        self.info('YAG_MoveE: 2016 version')
        mode=mode.upper()
        StripesCorrection=StripesCorrection.upper()
        if mode!='FAST' and mode!='COMPLETE':
            self.info('align mode %s not recognized. It should be FAST or COMPLETE', mode)
            return
        if StripesCorrection!='YES' and StripesCorrection!='NO':
            self.info('StripesCorrection flag %s not recognized. It should be YES or NO', StripesCorrection)
            return

        E = self.getMoveable("E")
        #diftabx = self.getMoveable("diftabx")
        #diftabz = self.getMoveable("diftabz")
        #iba_dev = taurus.Device('bl13/eh/oav-01-iba')
        falcon_dev = taurus.Device(OAV_BW_device_name)
        zoom = taurus.Device('ioregister/eh_zoom_tangoior_ctrl/1')
        #eps = taurus.Device('bl13/ct/eps-plc-01')
        #var = taurus.Device('bl13/ct/variables')
        #blight = self.getDevice('tango://blight')
        mbattrans = self.getMoveable("mbattrans")
        vfmstripe = self.getMoveable("vfmstripe")
        hfmstripe = self.getMoveable("hfmstripe")

        if Efinal==-9:
            Efinal = E.getAttribute('Position').read().value
        
        #falcon_dev.write_attribute('ColorMode', False)
        
        Einit = E.getAttribute('Position').read().value
        DE = Efinal-Einit
        (mvdiftabx, mvdiftabz, stripeRhIr_x, stripeRhIr_z)=diftab.getdiftab_E(Einit,Efinal)
        if StripesCorrection=='YES':
            mvdiftabx+=stripeRhIr_x
            mvdiftabz+=stripeRhIr_z
        self.info('YAG_MOVEE: Calculated change: E to %.4f keV (DE=%.4f keV)' %(Efinal,DE))
        if abs(mvdiftabx)>0.001 and abs(mvdiftabx)<0.1:
            strXmove = ' diftabx %.5f' %mvdiftabx
            self.info('YAG_MOVEE: Calculated change: move rel. diftabx %f mm' %mvdiftabx)
        else: strXmove = ''
        if abs(mvdiftabz)>0.0005 and abs(mvdiftabz)<0.3:
            strYmove = ' diftabz %.5f' %mvdiftabz
            self.info('YAG_MOVEE: Calculated change: move rel. diftabz %f mm' %mvdiftabz)
        else: strYmove = ''
        movecommand = 'mvr Eugap %.5f' %DE
        movecommand = movecommand+strXmove+strYmove
        if Efinal>16.0: self.warning('YAG_MOVEE: Calculated change: move rel. diftabx %f mm' %mvdiftabx)
        if StripesCorrection=='YES' and stripeRhIr_x!=0.: self.info('YAG_MOVEE: Horiztal Stripe Correction  diftabx %f mm' %stripeRhIr_x)
        if StripesCorrection=='YES' and stripeRhIr_z!=0.: self.info('YAG_MOVEE: Vertical Stripe Correction  diftabz %f mm' %stripeRhIr_z)

        # INITIAL E
        #LOW ZOOM ALIGNMENT
        if mode=='COMPLETE':
            diffractometer.movewaitzoom(9)
            #self.execMacro('autofocus')
            transmission.YAG_mbat_adjust(210,100)
            self.info('YAG_MOVEE: ALIGNING at low  Zoom: finding beam and steering diftab...')
            self.execMacro('YAG_align diftab')

        #ALIGNMENT AND CONDITIONING AT INITIAL E
        self.info('YAG_MOVEE: ALIGNING: zooming in to maximum')
        #self.execMacro('mv mbattrans 25')
        diffractometer.movewaitzoom(12)
        
        self.info('YAG_MOVEE: Finding correct MBAT attenuation and autofocusing')
        transmission.YAG_mbat_adjust(230,100)
        self.info('YAG_MOVEE: ALIGNING: finding beam and steering diftab')
        self.execMacro('YAG_align diftab')
        self.info('YAG_MOVEE: Beam set up at initial Energy  %.5f keV: DONE' %Einit)


        #MOVING E AND DIFTAB
        self.info('YAG_MOVEE: MOVING %s' %movecommand)
        self.execMacro(movecommand)
        Ecurrent = E.getAttribute('Position').read().value
        self.info('YAG_MOVEE: Current Photon Energy = %.5f keV  (foreseen %.5f keV)' %(Ecurrent,Efinal) )

        if DE<0.002:
            self.info('YAG_MOVEE: Specified Energy change is %.2f eV (<2 eV)' %(DE*1000))
            self.info('YAG_MOVEE: Not realigning after Energy change')

        else:
            #ALIGNMENT AND CONDITIONING AT FINAL E
            self.info('YAG_MOVEE: FINAL ALIGNMENT')
            transmission.YAG_mbat_adjust(230,50)
            self.info('YAG_MOVEE: ALIGNING: finding beam and steering diftab')
            self.execMacro('YAG_align diftab')
            self.info('YAG_MOVEE: Beam set up at final Energy  %.5f keV: DONE' %Ecurrent)
        
        self.info('YAG_MOVEE: COMPLETED')


#        zoommot = self.getMoveable("zoommot")
#        time.sleep(.5)
#        while zoommot.read_attribute('State').value==PyTango.DevState.MOVING:
#            time.sleep(.1)


