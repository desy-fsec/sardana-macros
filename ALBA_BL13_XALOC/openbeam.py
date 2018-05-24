from sardana.macroserver.macro import Macro, Type
import taurus
import time

class openbeam(Macro):

    '''openbeam: macro to open to beam parts of the beamline
    task: exp: opens the fast shutter - com: closes fast shutter and moves it 3.25 mm (the hole)
    '''

    param_def = [ 
                  [ 'task', Type.String, 'com', 'Type of task to be done at the BL. Options: exp/com'],
                  [ 'mode', Type.String, 'eh', 'part of the beamline to be opened to beam. Options: eh']
                ]

    def run(self,task,mode):

       mode = mode.lower()
       task = task.lower()
       eps = taurus.Device('bl13/ct/eps-plc-01')

       if eps['fe_open'].value is False:
           self.info('OPENBEAM: opening front end')
           self.execMacro('fe open') 
       else:
           self.info('OPENBEAM: front end already open')


       if mode == 'oh':
           self.info('OPENBEAM: OH: MOVING EUGAP to 12000!')
           self.execMacro('mv ugap 12000')
           return



       if mode == 'eh':
           self.info('OPENBEAM: checking EH elements: Photon shutter, Fast shutter and Slow shutter')
           self.execMacro('act detcover in')
           limit = 1
           while eps['detcover'].value != 0: 
               self.info('OPENBEAM WARNING: Waiting for the det cover to be IN')
               limit = limit + 1
               if limit > 10:
                   self.error('OPENBEAM ERROR: Cannot close the det cover')
                   return
               time.sleep(1)
           
           if eps['pshu'].value == 0:
               self.info('OPENBEAM: opening photon shutter')
               self.execMacro('act pshu open')
           else:
               self.info('OPENBEAM: photon shutter already open')
           
           if eps['slowshu'].value == 0:
               self.info('OPENBEAM: opening Slow shutter')
               self.execMacro('act slowshu open')
           else:
               self.info('OPENBEAM: slow shutter already open')
           #self.execMacro('ni660x_shutter_open_close open')

       if task == 'exp':
           self.info('OPENBEAM: opening fast shutter')
           self.execMacro('ni660x_shutter_open_close open')
           self.info('OPENBEAM: WARNING: fast shutter is open, do not leave it open during a long time')
       
       elif task =='com':
           mvfshuzcmd = 'mv fshuz 3.25'
           self.info('OPENBEAM: closing fast shutter, and removing it from the beam path: %s' %mvfshuzcmd)
           self.execMacro('ni660x_shutter_open_close close')
           self.execMacro(mvfshuzcmd)
           self.info('OPENBEAM: WARNING! To collect data move the fast shutter to the beam path by command: mv fshuz 0')
           

