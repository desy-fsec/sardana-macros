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
                  [ 'dir', Type.String, '', 'Directory'],
                  [ 'type', Type.String, '', 'Type']
                ]

    def run(self,prefix,userexpt,dir,type):



       # DEFINE DEVICES
       type=type.lower()
       eps = taurus.Device('bl13/ct/eps-plc-01')
       pilatusdet = taurus.Device('bl13/eh/pilatusspecific')
       pilatusdet.sendCamserverCmd('ni 1')
       pilatusdet.sendCamserverCmd('expt %s' % userexpt)
       pilatusdet.sendCamserverCmd('imgpath %s' % dir)
       pilatusdet.sendCamserverCmd('expt %s' % userexpt)
       if userexpt > 900:
          self.error('POWDER: exposure > 900 s')
          return
       self.execMacro('act detcover out')
       limit = 1
       while eps['detcover'].value != 1:
          time.sleep(5) 
          self.info('POWDER: waiting for detcover out')
          limit = limit + 1
          if limit > 20: break
       self.execMacro('mv bstopx 0')
       self.execMacro('mv bstopz 0')
       self.execMacro('ni660x_shutter_open_close open')
       eps['slowshu'] = 1
       if type == 'tif': pilatusdet.sendCamserverCmd('exposure %s.tif' % prefix)
       if type == 'cbf': pilatusdet.sendCamserverCmd('exposure %s.cbf' % prefix)
       time.sleep(userexpt)
       self.execMacro('ni660x_shutter_open_close close')
       eps['slowshu'] = 0
       self.execMacro('act detcover in')

 
            

class expose_with_cover(Macro):

    '''
           This macro is used to collect a diffraction dataset
    '''

    param_def = [
                  [ 'prefix', Type.String, None, 'Filename prefix'],
                  [ 'userexpt', Type.Float, None, 'Exposure time in seconds'],
                  [ 'dir', Type.String, '', 'Directory'],
                  [ 'type', Type.String, '', 'Type']
                ]

    def run(self,prefix,userexpt,dir,type):



       # DEFINE DEVICES
       type=type.lower()
       eps = taurus.Device('bl13/ct/eps-plc-01')
       pilatusdet = taurus.Device('bl13/eh/pilatusspecific')
       pilatusdet.sendCamserverCmd('ni 1')
       pilatusdet.sendCamserverCmd('expt %s' % userexpt)
       pilatusdet.sendCamserverCmd('imgpath %s' % dir)
       pilatusdet.sendCamserverCmd('expt %s' % userexpt)
       self.execMacro('act detcover in')
       self.info('EXPOSE_WITH_COVER: Remember to remove the fast shutter')
       limit = 1
       while eps['detcover'].value != 0:
          time.sleep(5)
          self.info('EXPOSE_WITH_COVER: waiting for detcover in')
          limit = limit + 1
          if limit > 20: break
       #self.execMacro('ni660x_shutter_open_close open')
       eps['slowshu'] = 1
       if type == 'tif': pilatusdet.sendCamserverCmd('exposure %s.tif' % prefix)
       if type == 'cbf': pilatusdet.sendCamserverCmd('exposure %s.cbf' % prefix)
       time.sleep(userexpt)
       #self.execMacro('ni660x_shutter_open_close close')
       eps['slowshu'] = 0
      

 




