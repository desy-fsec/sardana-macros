# RB 2014.11.11
# - Moved funcion readbeamvars to diffractometer, renamed to readbeamvarsOAV
# - Moved ScaleFactorX and ScaleFactorY to bl13constants

import sys
import math
import time
import copy
import numpy
import PIL.Image
import PyTango
import taurus
import bl13constants
import diffractometer 

from sardana.macroserver.macro import Macro, Type
from bl13constants import OAV_BW_device_name

ScaleFactorX = bl13constants.ScaleFactorX # 100/68.2
ScaleFactorY = bl13constants.ScaleFactorY #100./68.7

ScaleFactorX = 1.0
ScaleFactorY = 1.0

YAGZ_YAG_POSITION = 0.0

OAV_CENTER_X_PX = bl13constants.OAV_CENTER_X_PX
OAV_CENTER_Y_PX = bl13constants.OAV_CENTER_Y_PX
#OAV_CENTER_X_PX = 384
#OAV_CENTER_Y_PX = 288


class YAG_align(Macro):
    """
    Macro to align the beam using the OAV and a YAG screen at sample position
    NOALIGN just gives the misalignment
    DIFTAB moves diftabx and diftabz to center the beam at the camera center
    ALL same as DIFTAB, plus autofocusing and adjusting mbat for zooms 8 and 12 
    """
    param_def = [ 
                  [ 'alignmode', Type.String, 'NOALIGN', 'NOALIGN / DIFTAB / ALL']
                ]

#    TITLE = 'Grab FWHM Beam'
#    ICON = 'ellipse_shape.png'

    def run(self, alignmode):
        alignmode=alignmode.upper()
        if alignmode!='NOALIGN' and alignmode!='DIFTAB' and alignmode!='ALL':
            self.info('YAG_ALIGN: align mode %s not recognized. It should be NOALIGN or DIFTAB', alignmode)
            return

        try:
            self.execMacro('YAG_findbeam')
            #(XFitCenter,YFitCenter,XFitFWHM,YFitFWHM) = self.readbeamvars()
            (XFitCenter,YFitCenter,XFitFWHM,YFitFWHM) = diffractometer.readbeamvarsOAV()
            

            self.info('YAG_ALIGN: Beam misalignment is: Dx=%f um;\tDz=%f um' %(XFitCenter, -YFitCenter))
        except Exception,e:
            self.warning('YAG_ALIGN: Beam could not be fitted: %s' % str(e))
            return
            
            
        if alignmode=='NOALIGN':
            return

            
        if alignmode=='DIFTAB':
            Xmove = ScaleFactorX*XFitCenter/1000.
            Ymove = -ScaleFactorY*YFitCenter/1000.
            #Ymove = ScaleFactorY*YFitCenter/1000.
            if abs(Xmove)>0.001 and abs(Xmove)<0.1: strXmove = ' diftabx %f' %Xmove
            else: strXmove = ''
            if abs(Ymove)>0.0005 and abs(Ymove)<0.1: strYmove = ' diftabz %f' %Ymove
            else: strYmove = ''
            if any((strXmove,strYmove)):
                diftabmove = 'mvr'+strXmove+strYmove
                self.info('YAG_ALIGN: diftab moving: '+diftabmove)
                self.execMacro(diftabmove)
                time.sleep(2)
            else:
                self.warning('YAG_ALIGN: diftab NOT moving: Too small or too large diftabx AND diftabz movement')
            self.execMacro('YAG_findbeam')
            #(XFitCenter,YFitCenter,XFitFWHM,YFitFWHM) = self.readbeamvars()
            (XFitCenter,YFitCenter,XFitFWHM,YFitFWHM) = diffractometer.readbeamvarsOAV()
            self.info('YAG_ALIGN: Beam misalignment is: Dx=%f um;\tDz=%f um' %(XFitCenter, -YFitCenter))

            
        if alignmode=='ALL':
            self.info('YAG_ALIGN: doing complete alignment')
            # Get original values
            mbattrans = self.getMoveable("mbattrans")
            zoomdev = taurus.Device('ioregister/eh_zoom_tangoior_ctrl/1')
            mbattrans_initvalue = mbattrans.getAttribute('Position').read().value
            zoom_initvalue = zoomdev.read_attribute('value').value
            # Do alignment
            self.execMacro('YAG_moveE -9 NO complete')
            # Return to original values
            self.execMacro('mv mbattrans %f' %round(mbattrans_initvalue))
            zoomdev.write_attribute('value',zoom_initvalue)
            
            
        self.info('YAG_ALIGN: COMPLETED')
        time.sleep(0.3)


class YAG_findbeam(Macro):
    """
    Macro to find the beam using a YAG screen and the OAV
    Stores new coordinates in variables
    """
    param_def = []

#    TITLE = 'Grab FWHM Beam'
#    ICON = 'ellipse_shape.png'

#    @ProtectTaurusMessageBox(msg='An error occurred trying to grab FWHM beam.')
    def run(self):
        try:
            iba_dev = taurus.Device('bl13/eh/oav-01-iba')

            if str(iba_dev.state()).lower() != 'running': 
               try:iba_dev.start()
               except:
                  print "OAV ERROR: cannot start oav-iba"
                  return
            iba_dev.write_attribute('autoroithreshold', 1)
            #iba_dev.Process()
            x_proj_fit_converged = iba_dev.read_attribute('XProjFitConverged').value
            y_proj_fit_converged = iba_dev.read_attribute('YProjFitConverged').value
            if not x_proj_fit_converged or not y_proj_fit_converged:
                error_msg = 'ImageBeamAnalizer can not fit the beam.'
                error_msg += '\nXProjFitConverged: %s' % str(x_proj_fit_converged)
                error_msg += '\nYProjFitConverged: %s' % str(y_proj_fit_converged)
                raise Exception(error_msg)
            x_proj_fit_center = iba_dev.read_attribute('XProjFitCenter').value
            x_proj_fit_fwhm = iba_dev.read_attribute('XProjFitFWHM').value
            y_proj_fit_center = iba_dev.read_attribute('YProjFitCenter').value
            y_proj_fit_fwhm = iba_dev.read_attribute('YProjFitFWHM').value
            
            # UPDATE BL13VARS
            vars = taurus.Device('bl13vars')
            img_center_x = taurus.Attribute('bl13/ct/variables/ImageCenterX')
            img_center_y = taurus.Attribute('bl13/ct/variables/ImageCenterY')
            icx = img_center_x.read().value
            icy = img_center_y.read().value

            # IN ORDER TO RESPECT THE BEAM
            # THE NEW VALUE SHOULD BE BASED RESPECT THE CENTER OF THE IMAGE
            x_proj_fit_center_from_center = x_proj_fit_center - (icx*vars.oav_pixelsize_x)
            y_proj_fit_center_from_center = y_proj_fit_center - (icy*vars.oav_pixelsize_y)
            
            vars.write_attribute('XProjFitCenterFromCenter', x_proj_fit_center_from_center)
            vars.write_attribute('XProjFitFWHM', x_proj_fit_fwhm)
            vars.write_attribute('YProjFitCenterFromCenter', y_proj_fit_center_from_center)
            vars.write_attribute('YProjFitFWHM', y_proj_fit_fwhm)
            time.sleep(1)
            
        except Exception,e:
            self.info('Error in YAG_findbeam macro: %s' % str(e) )



class YAG_prepare(Macro):
    """
    Macro to prepare EH to use a YAG screen to center the beam
    """
    param_def = [ 
                  [ 'alignmode', Type.String, 'NOALIGN', 'NOALIGN / DIFTAB']
                ]

    def run(self, alignmode):
        alignmode=alignmode.upper()
        if alignmode!='NOALIGN' and alignmode!='DIFTAB':
            self.info('YAG_prepare: align mode %s not recognized. It should be NOALIGN or DIFTAB', alignmode)
            return

        # DEFINE DEVICES AND VARIABLES
        eps = taurus.Device('bl13/ct/eps-plc-01')
        var = taurus.Device('bl13/ct/variables')
        blight = self.getDevice('tango://blight')
        flight = self.getDevice('tango://flight')
        mbattrans = self.getMoveable("mbattrans")
        zoom = taurus.Device('ioregister/eh_zoom_tangoior_ctrl/1')
        zoommot = self.getMoveable("zoommot")
        dettaby = self.getMoveable("dettaby")
        yagz = self.getMoveable("yagz")
        #iba_dev = taurus.Device('bl13/eh/oav-01-iba')
        falcon_dev = taurus.Device(OAV_BW_device_name)


        #CONDITIONING IMAGE
        #falcon_dev.write_attribute('ColorMode', 0)
        

        # Remove ln2cover so yag can go up
        self.info('YAG_prepare: removing ln2cover')
        self.execMacro('act ln2cover out')
        
        # move away the cryodist
        #self.info('YAG_prepare: moving cryodist to FAR position')
        #self.execMacro('act cryodist far')
   
        # REMOVE THE DETECTOR COVER 
        self.info('YAG_prepare: Placing the detector cover')
        if not eps['detcover'].value == 0: 
            self.execMacro('act detcover in')              

        # REMOVE & TURN OFF BACKLIGHT
        self.info('YAG_prepare: Removing and turning off backlight')
        blight.write_attribute('Value', 0)
        if not eps['backlight'].value == 1: 
            self.execMacro('act backlight out')              

        # REMOVE & TURN OFF FRONTLIGHT 
        self.info('YAG_prepare: Turning off front light')
        flight.write_attribute('Value', 0)

        # CHECK PREVIOUS ELEMENTS
        for trials in range(50):
            if eps['detcover'].value == 0 and eps['backlight'].value == 1 and eps['ln2cover'].value == 1:
                self.info('YAG_prepare: OK: Det cover is IN; backlight and ln2cover are OUT; cryodist is FAR') 
                break
            time.sleep(0.2)
            self.error('ERROR removing elements. Det cover: %i, backlight: %i, ln2cover: %i' % 
                       (eps['detcover'].value, eps['backlight'].value, eps['ln2cover'].value) )
            raise

        # move yag in and sample out if it is present.
        self.execMacro('act yag in')
        
        #ATTENUATION
        self.info('Attenuation set to 5. Change it if needed')
        self.execMacro('mv mbattrans 5')

        # OPEN PSHU, SLOW SHUTTER, FAST SHUTTER
        if eps['pshu'].value == 0:
            self.info('Opening the safety shutter')
            self.execMacro('act pshu open')              
        if eps['slowshu'].value == 0:
            self.info('Opening the slow shutter')
            self.execMacro('act slowshu open')
        self.execMacro(['ni660x_shutter_open_close','open'])

        #self.info('***\nYou should now see the (probably defocused) beam at the YAG screen')
        #self.info('RB 20141119: you won\'t see it, because oav needs to be adjusted, it looses connection to oav-01-iba')
        #self.info('If you do not see it, probably YAG screen is not intercepting the beam')
        #self.info('Other causes of failure: no SR beam, FE closed, beam too misaligned\n***')

        #FOCUS
        # NOT OPTIMIZED AT ALL, need some modifications........
        #self.info('ALIGNING at Zoom 6')
        #zoom.write_attribute('value',6)
        #time.sleep(.5)
        #while zoommot.read_attribute('State').value==PyTango.DevState.MOVING:
        #    time.sleep(.1)
        #time.sleep(.5)
        #self.execMacro('autofocus')
        #self.info('adjust diftab')
        #time.sleep(.1)
        #self.execMacro('YAG_align diftab')
        #self.info('Attenuation set to 20. Change it if needed')
        #self.execMacro('mv mbattrans 20')
        #self.info('moving to zoom 12')
        #zoom.write_attribute('value',12)
        #time.sleep(.5)
        #while zoommot.read_attribute('State').value==PyTango.DevState.MOVING:
        #    time.sleep(.1)
        #time.sleep(.5)
        #self.execMacro('autofocus')
        #self.info('FINAL ALIGNMENT')
        #time.sleep(.1)
        #self.execMacro('YAG_align diftab')
        #time.sleep(.5)

class YAG_autoalign(Macro):
    ''' This macro aims to automate YAG usage, using YAG_prepare to inser the DUSP YAG
        It does the following:
          - Prepare the beamline for save YAG usage (using the YAG_prepare macro). If a sample is in the way, it is removed automatically
          - Change the energy to the desired energy (input parameter) using the YAG_moveE macro with NO and COMPLETE options
          - Do multiple rounds (max of 5) of YAG aligns using the YAG_align macro with ALL option
          - Measure the flux using the flux_measure macro, with option 1
    '''
    
    ### TODO: Is energy float or double of what??
    param_def = [ 
                  [ 'setEnergy', Type.Float, -9, 'Desired E in keV, -9 for current E']
                ]


    def run(self, setEnergy):
        # Set devices
        varis = taurus.Device('bl13vars')
        E = self.getMoveable("E")
        mbattrans = self.getMoveable("mbattrans")
        falcon_dev = taurus.Device(OAV_BW_device_name)
        self.cats_dev = PyTango.DeviceProxy('bl13/eh/cats')
        
        # Save initial values
        transmis = mbattrans.position
        #falcm = falcon_dev.ColorMode
        
        # initial checks:
        if varis.machinecurrent < bl13constants.SR_topup_mincurrent:
            ### TODO: check the value type of vars.machinecurrent
            self.info('YAG_autoalign: The storage ring current (%f) is to low!',varis.machinecurrent)
            return
        if setEnergy < bl13constants.BL13_E_min and setEnergy > bl13constants.BL13_E_max: 
            self.info('YAG_autoalign: The desired energy of %f keV is outside the operation range of the beamline (5-22 keV)', setEnergy)
            return
        # Stripe not fully supported, warning...
        if setEnergy<6.0: 
            self.warning('The desired energy might require a change of stripe, which is not supported yet, check!!')
        #if not self.cats_dev['di_PRI4_SOM'].value == False:
	#    self.info('YAG_autoalign: There is a sample on the magnet, remove that first')
	#    return
            
        # Prepare the beamline for YAG use: remove lights, put beamstop etc
        try: self.execMacro('YAG_prepare')
        except Exception,e:
            self.error('YAG_autoalign: ERROR in YAG_autoalign: the beamline could not be prepared. Error: %s' % str(e) ) 
            return
            
        # Set the desired energy and move the diftab to lookup table position, set zoom, do initial YAG_align
        try: self.execMacro(('YAG_moveE %s NO COMPLETE' % setEnergy))
        except Exception,e:
            self.error('YAG_autoalign: ERROR in YAG_autoalign running YAG_moveE. Error: %s' % str(e) ) 
            return

        # Check if the YAG_moveE alignment was good enough
        YAG_stably_aligned = False
        YAG_align_tries = 1
        # Do a dummy YAG_align and check value boundaries
        self.execMacro('YAG_findbeam')
        (newXFC,newYFC,newXFWHM,newYFWHM) = diffractometer.readbeamvarsOAV()
        newXFC*=ScaleFactorX
        newYFC*=-ScaleFactorY
        self.debug('YAG_autoalign DEBUG: shifts in diftabx is %8.3f and diftabz is %8.3f' %(newXFC,newYFC))
        if newXFC > bl13constants.OAV_xbeam_maxmisalign: strXmove = '%s' % newXFC
        else: strXmove=''
        if newYFC > bl13constants.OAV_ybeam_maxmisalign: strYmove = '%s' % newYFC
        else: strYmove=''
        # A while loop to do multiple rounds of YAG_align until the shift is close to zero
        if any((strXmove,strYmove)):
            self.info('YAG_autoalign: alignment not complete. Manual YAG_align diftab cycles should work')
        while not YAG_stably_aligned and YAG_align_tries<5:
            if any((strXmove,strYmove)): 
                # Next do a YAG_align to finalize alignment
                self.info('Moving diftabx by %s and diftaby %s',strXmove,strYmove)
                self.execMacro('YAG_align', 'ALL')
                YAG_align_tries+=1
            else: YAG_stably_aligned=True
            self.execMacro('YAG_findbeam')
            (newXFC,newYFC,newXFWHM,newYFWHM) = diffractometer.readbeamvarsOAV()
            newXFC*=ScaleFactorX
            newYFC*=-ScaleFactorY
            if newXFC > bl13constants.OAV_xbeam_maxmisalign: strXmove = 'diftabx %s' % newXFC
            else: strXmove=''
            if newYFC > bl13constants.OAV_ybeam_maxmisalign: strYmove = 'diftaby %s' % newYFC
            else: strYmove=''

        # Return beamline to original status
        try:
            self.execMacro('mv mbattrans %f' % (transmis))
            #falcon_dev.write_attribute('ColorMode', falcm)
        except Exception,e: 
            self.info('YAG_autoalign: Cant reset parameters, error: %s' % str(e) )
        
        # flux_measure removes the YAG using act yagdiode out, thus returning the sample to its 0 position, if any
        self.execMacro('flux_measure 1')
