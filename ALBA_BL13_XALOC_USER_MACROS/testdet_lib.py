from sardana.macroserver.macro import Macro, Type
import taurus
import os
import time
#from cbfread import *
import detector

class testdet(Macro):
    ''' This macro is used to check if the bstop is corretly placed: 1=OK 0=OK -1=UNKNOWN (either the FE, SLOWSHU OR PSHU COULD NOT BE OPENED)'''

    result_def = [ [ 'result', Type.String, '0', 'Result 1=OK 0=NOT OK -1=UNKNOWN'] ]


    def run(self):
       
       # define variables and devices
       eps = taurus.Device('bl13/ct/eps-plc-01')
       pilatusdet = taurus.Device('bl13/eh/pilatusspecific')
       mbattrans = self.getMoveable("mbattrans")
       testdir = '/beamlines/bl13/commissioning/testimages'
       result = 0 
       fault = 1
#
       self.info('Performing a safety test image with the detector')

       # set mbattrans to 1/10 of its original value
       mbattransorig = mbattrans.getPosition()
       testmbattrans = 1 
       self.info('Current MBAT transmission is %s It will be set to %s' % (mbattransorig,testmbattrans))
       try:self.execMacro('mv mbattrans %s' %testmbattrans)
       except: pass


       self.info('collect 1 frame 80ms exposure')
       pilatusdet.sendCamserverCmd('setroi 0')
       pilatusdet.sendCamserverCmd('ni 1')
       pilatusdet.sendCamserverCmd('imgpath /beamlines/bl13/commissioning/testimages')
       pilatusdet.sendCamserverCmd('expp 0.08')
       self.info('remove initial file')
       if not mbattrans.getPosition() < 5.: 
           self.error('ERROR: Could not change the mbat transmission')
           return
       if os.path.exists('/beamlines/bl13/commissioning/testimages/test_01.cbf'): 
          os.remove('/beamlines/bl13/commissioning/testimages/test_01.cbf')

#      open FE
       if not eps['fe_open'].value == True:
          self.info('Opening the FE')
          self.execMacro('fe open')
          for trials in range(50):
              if eps['fe_open'].value == True: 
                 break
              time.sleep(0.2)
       if not eps['fe_open'].value == True:
          self.error('ERROR: cannot open FE')
          fault = -1


#      open safety shutter
       if not eps['pshu'].value == 1:
          self.info('Opening the safety shutter')
          self.execMacro('act pshu open')
          for trials in range(50):
              if eps['pshu'].value == 1: 
                 break
              time.sleep(0.2)
       if not eps['pshu'].value == 1: 
          self.error('ERROR: cannot open PSHU')
          fault = -1


#      remove backlight 
       self.info('Remove backlight')
       self.execMacro('act backlight out')
       for trials in range(50):
           if eps['backlight'].value == 1: 
              break
           time.sleep(0.2)
       if not eps['backlight'].value == 1:
          self.error('ERROR: cannot remove the backlight')
          fault = -1

#      open slow shutter
       self.info('Open slow shutter')
       self.execMacro('act slowshu out')
#       for trials in range(50):
#           if eps['slowshu'].value == 1: 
#              break
#           time.sleep(0.2)
       if not eps['slowshu'].value == 1:
          self.error('ERROR: cannot open slowshu')
          fault = -1


#      open fast shutter
       self.info('Open fast shutter')
       self.execMacro('ni660x_shutter_open_close open')
#      expose image
       pilatusdet.sendCamserverCmd('exposure test_01.cbf')
       self.info('Test image taken')
       time.sleep(0.08)

#      close fast & slow shutters
       self.info('Close fast & slow shutters')
       self.execMacro('ni660x_shutter_open_close close')
       self.execMacro('act slowshu in')

#      check that image exists & get max count
       self.info('Test that the image exists')
       for trials in range(400):
           if os.path.exists('/beamlines/bl13/commissioning/testimages/test_01.cbf'): 
              self.info('file exists')
              break
           time.sleep(0.2)
       if not os.path.exists('/beamlines/bl13/commissioning/testimages/test_01.cbf'): 
           fault = -1
       if os.path.exists('/beamlines/bl13/commissioning/testimages/test_01.cbf'): 
           cbfmax, cbfmin, cbfmean = detector.cbfread('/beamlines/bl13/commissioning/testimages/test_01.cbf')
           self.info('Maximum counts in test frame %s' %cbfmax) 

#      test max counts
       if cbfmax > 1048576:
          result = 0 
       elif cbfmax < 1048576:
          result = 1

#      change mbattrans to original values
       self.info('Changing mbattrans back to its original value %s' %mbattransorig)
       self.execMacro('mv mbattrans %s' %mbattransorig)
       currentmbattrans = mbattrans.getPosition()
       self.info('Current MBAT transmission is %s' % (currentmbattrans))
       finalresult = result*fault
       return str(result*fault)


