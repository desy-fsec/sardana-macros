from sardana.macroserver.macro import Macro, Type
import taurus

class camserver(Macro):
    ''' This macro is used to send a command to the camserver
        mostly to set the energy of the detector with ex.:
        camserver "setenergy 12658" to set the energy to 12.658 keV
    '''

    param_def = [ 
                  [ 'command', Type.String, None, 'Command to send to the camserver of the PILATUS 6M']
                ]

    def run(self, command):
       # define devices
       pilatusdet = taurus.Device('bl13/eh/pilatusspecific')

       # print parameters 
       self.info(' command %s\n' %(command))

       # send command to camserver 
       pilatusdet.sendCamserverCmd('%s' % command)

