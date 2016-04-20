from sardana.macroserver.macro import Macro, Type
import taurus
import diagnostics

class flux(Macro):

    '''flux: macro to find photon flux of the beamline
    diodes are: detector, sample, all
    Only calibrated is detector diode
    '''

    param_def = [ 
                  [ 'diodename', Type.String, '', 'diode name']
                ]

    def run(self,diodename):
       dictdiode={'sample':'bl13/di/emet-06-diodes','detector':'bl13/di/emet-06-diodes'}
       diodename = diodename.lower()


       if diodename == 'sample' or diodename == 'all' or diodename == '':
           name = 'sample'
           diodeflux = diagnostics.samplediode.Flux()
           msg = 'Flux at %s diode is %.3e ph/s (to be trusted if E=12.658keV)' %(name, diodeflux[0])
           self.info(msg)
           msg = 'Normalized Flux at %s diode is %.3e ph/s/250mA' %(name, diodeflux[1])
           self.info(msg)


       if diodename == 'detector' or diodename == 'all' or diodename == '':
           name = 'detector'
           diodeflux = diagnostics.detectordiode.Flux()
           msg = 'Flux at %s diode is %.3e ph/s' %(name, diodeflux[0])
           self.info(msg)
           msg = 'Normalized Flux at %s diode is %.3e ph/s/250mA' %(name, diodeflux[1])
           self.info(msg)

