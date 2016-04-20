from sardana.macroserver.macro import Macro, Type
import taurus
import time

class powder(Macro):

    '''
           This macro is used to collect a diffraction dataset 
    '''

    param_def = [ 
                  [ 'prefix', Type.String, None, 'Filename prefix'],
                  [ 'userexpt', Type.Float, None, 'Exposure time in seconds'],
                  [ 'dir', Type.String, '', 'Directory']
                ]

    def run(self,prefix,userexpt,dir):



       # DEFINE DEVICES
       eps = taurus.Device('bl13/ct/eps-plc-01')
       pilatusdet = taurus.Device('bl13/eh/pilatusspecific')
       pilatusdet.sendCamserverCmd('ni 1')
       pilatusdet.sendCamserverCmd('expt %s' % userexpt)
       pilatusdet.sendCamserverCmd('imgpath %s' % dir)
       pilatusdet.sendCamserverCmd('expt %s' % userexpt)
       self.execMacro('mv bstopx 0')
       self.execMacro('mv bstopz 0')
       eps['slowshu'] = 1
       pilatusdet.sendCamserverCmd('exposure %s.tif' % prefix)
       time.sleep(userexpt)
       eps['slowshu'] = 0

 
            

       

 




