import math as m
import numpy
import taurus
import bl13constants
import detector

from sardana.macroserver.macro import Macro, Type

DETSAMDIS_NEGATIVE_SOFT_LIMIT = 123.5
DETECTOR_PIX_SIZE = .172

class resolutiondet(Macro):
    """
    Macro to calculate the resolution limit of the detector at a given distance of the detector,
    the wavelength and the offset of the detector, in mm
    """
    param_def = [ 
                  [ 'detsamdispos', Type.Float, -1, 'distance sample to detector, detsamdis'],
                  [ 'energyinput', Type.Float, -1, 'Photon Energy'],
                  [ 'detectoroffset', Type.Float, 0, 'vertical offset of the detector from current position (mm)']
                ]


    def run(self, detsamdispos, energyinput, detectoroffset):
            
            # if 0, take the minimum
            if detsamdispos < DETSAMDIS_NEGATIVE_SOFT_LIMIT:
                detsamdispos = DETSAMDIS_NEGATIVE_SOFT_LIMIT
            #if negative, take current value
            if detsamdispos < -0.01:
	        detsamdis = self.getMoveable("detsamdis")
                detsamdispos = detsamdispos.getAttribute('Position').read().value
            self.info('RESOLUTIONDET: Assumed detector-sample distance: %f mm' %(detsamdispos))
            if detsamdispos == DETSAMDIS_NEGATIVE_SOFT_LIMIT:
	        self.info('RESOLUTIONDET: This is the minimum detector-sample distance avaliable')

            if energyinput < .1:
	        energy = self.getMoveable("E")
                energyinput = energy.getAttribute('Position').read().value
            wavelengthvalue = bl13constants.HCKEVA/energyinput
            self.info('RESOLUTIONDET: Assumed energy (wavelength): %.3f keV (%.4f A)' %(energyinput, wavelengthvalue))

            
            var = taurus.Device('bl13/ct/variables') 
            beamx, beamy = var['beamx'].value, var['beamy'].value
            
#            if detectoroffset == 0:
#                resol_complete = detector.resdetdis(detsamdispos,'resolution','edge',wavelengthvalue)
#	        resol_edge = detector.resdetdis(detsamdispos,'resolution','edge',wavelengthvalue)

#	    elif detectoroffset != 0:
	    var = taurus.Device('bl13/ct/variables') 
            beamx, beamy = var['beamx'].value, var['beamy'].value
            self.info('RESOLUTIONDET: Assumed vert detector offset: %.3f mm (%.2f pix)' %(detectoroffset, detectoroffset/DETECTOR_PIX_SIZE))
            beamy += detectoroffset/DETECTOR_PIX_SIZE
            vector_complete = DETECTOR_PIX_SIZE*(min(beamx,2463-beamx,beamy,2527-beamy))
            vector_edge     = DETECTOR_PIX_SIZE*((max(beamx,2463-beamx))**2+(max(beamy,2527-beamy))**2)**0.5
            vector_side     = DETECTOR_PIX_SIZE*(max(beamx,2463-beamx,beamy,2527-beamy))
            resol_complete  = wavelengthvalue/(2*m.sin(0.5*m.atan(vector_complete/detsamdispos)))
            sinthetalambda_c= m.sin(0.5*m.atan(vector_complete/detsamdispos))/wavelengthvalue
            resol_edge      = wavelengthvalue/(2*m.sin(0.5*m.atan(vector_edge/detsamdispos)))
            sinthetalambda_e= m.sin(0.5*m.atan(vector_edge/detsamdispos))/wavelengthvalue
            resol_side      = wavelengthvalue/(2*m.sin(0.5*m.atan(vector_side/detsamdispos)))
            sinthetalambda_s= m.sin(0.5*m.atan(vector_side/detsamdispos))/wavelengthvalue

            self.info('RESOLUTIONDET: Maximum resolution (at the detector corner): %.3f A\t\t (sinTheta/lambda = %.4f)' %(resol_edge,sinthetalambda_e))
            self.info('RESOLUTIONDET: Complete resolution (complete shell in detector): %.3f A\t (sinTheta/lambda = %.4f)' %(resol_complete,sinthetalambda_c))
	    if detectoroffset != 0:
                self.info('RESOLUTIONDET: SIDE Maximum resolution (at the middle of the side): %.3f A\t (sinTheta/lambda = %.4f)' %(resol_side,sinthetalambda_s))

