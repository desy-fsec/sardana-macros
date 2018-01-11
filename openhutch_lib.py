# RB 9 Nov. 2015: removed reset of omegaz
# 

from sardana.macroserver.macro import Macro, Type
import taurus
import time
import math 
from epsf import *
from bl13constants.bl13constants import OMEGA_VELOCITYFAST
from bl13constants.bl13constants import YAGZ_OUT_POSITION, BSTOPZ_OUT_POSITION


class openhutch(Macro):

    '''
           To safely open the hutch:
           removes the backlight, closes the slowshutter, closes the safety shutter,
           removes the beamstop, moves detector to safe distance 
    '''

    def run(self):
       # DEFINE DEVICES
       eps = taurus.Device('bl13/ct/eps-plc-01')
       flight_dev = taurus.Device('tango://flight')
       blight_dev = taurus.Device('tango://blight')
       bstopz = self.getMoveable("bstopz")
       aperz = self.getMoveable("aperz")
       omega = self.getMoveable("omega")
       yagz = self.getMoveable("yagz")
       #omegaz = self.getMoveable("omegaz")

       # SWITCH OFF FRONT & BACK LIGHT
       flight_dev.write_attribute('Value', 0)
       blight_dev.write_attribute('Value', 0)

       self.info("OPEN HUTCH: Starting Open Experimental Hutch")
       
       # REMOVE fluodet
       self.execMacro('act distfluo out')
       # set move_omega to False until distfluo is out
       move_omega = False 
       limit = 1
       while epsf('read','distfluo')[2] != 1:
          self.info("OPEN HUTCH: waiting for the distfluo to be removed")
          limit = limit + 1
          if limit > 2:
             self.error("OPEN HUTCH ERROR: There is an error with the distfluo translation table")
             move_omega = False 
             break
          time.sleep(1)

       if epsf('read','distfluo')[2] == 1: move_omega = True


       # MOVE OMEGA BACK TO 0 if distfluo is not in (to avoid collisions bet. mk3 and fluodet) 
       if move_omega:
          omega.write_attribute('velocity',OMEGA_VELOCITYFAST)
          time.sleep(0.3)
          omega.write_attribute('position',0)

       # reset omegaz 
       #omegaz.write_attribute('position',0)

       # MOVE DETECTOR TO SAFE POSITION 
       self.info('OPEN HUTCH: Check the position of the detector')
       self.execMacro('turn dettaby on')
       dettaby = self.getMoveable("dettaby")
       dettabypos = dettaby.getPosition()
       if dettabypos < 100:
           self.info('OPEN HUTCH: Move the detector to a safe position')
           try:
              dettaby.write_attribute('position',100)
           except:
              self.error('OPEN HUTCH ERROR: Cannot actuate the dettaby')
              return


       # CLOSE DETECTOR COVER 
       self.info('OPEN HUTCH: Close the detector cover')
       self.execMacro('act detcover in')

       # DIODESAMP OUT 
       #self.info('OPEN HUTCH: Diodesamp out')
       #self.execMacro('act diodesamp out')
       #YAGZ OUT
       if yagz.getPosition()> YAGZ_OUT_POSITION + 0.1 :
           self.info('OPEN HUTCH: Removing yagz from the beam')
           yagz.write_attribute('position',YAGZ_OUT_POSITION)
       else:
           self.info('OPEN HUTCH: yagz detected to be out')
           
        
       # CLOSE FAST SHUTTER
       self.execMacro('ni660x_shutter_open_close close') 


       # CLOSE THE SLOW SHUTTER
       self.info('OPEN HUTCH: Slow shutter in')
       try: 
          self.execMacro('act slowshu in') 
       except:
          self.error('OPEN HUTCH ERROR: Cannot actuate the slowshu')
          return


       # REMOVE LN2 COVER
       #self.execMacro('act ln2cover out') 


       # REMOVE BACKLIGHT
       self.info('OPEN HUTCH: Backlight out')
       self.execMacro('act backlight out')



       
       # unzoom 
       zoommot = self.getMoveable("zoommot")
       zoommot.pos = zoommot.getPosition()
       if math.fabs(zoommot.pos-0.044) > 0.05:
          if not zoommot.getAttribute('PowerOn').read().value: self.execMacro('turn zoommot on')
          self.info('OPEN HUTCH: Move zoom to 0.5')
          zoommot.write_attribute('position',0.044)
 
 
       # MOVE BSTOPZ OUT
       if epsf('read','ln2cover')[2] == 1:
           self.info('OPEN HUTCH: Remove bstopz')
           self.execMacro('turn bstopz on')
           lim1 = bstopz.getAttribute('StatusLim-').read().value
           try: 
              if not lim1:
                 self.info('OPEN HUTCH: Moving bstopz')
                 bstopz.write_attribute('position',BSTOPZ_OUT_POSITION)
              elif lim1:
                 self.info('OPEN HUTCH: Bstopz is at the lim-')
           except:
              self.error('OPEN HUTCH ERROR: Cannot move bstopz')
              return

       # MOVE APERZ OUT
           current_aperz_pos = aperz.getPosition()
           if current_aperz_pos>-94:
              self.info('OPEN HUTCH: Remove aperz')
              self.execMacro('turn aperz on')
              self.execMacro('mvaperz out')

       if aperz.getPosition() > -94 or bstopz.getPosition() > -94: 
          self.info('OPEN HUTCH: Wait 10 s')
### TEST!!!
### REMOVE IF MOVEABLE BEAM STOP IS NOT USED
       #bsy = self.getMoveable("bsy")
       #bsy.pos = bsy.getPosition()
       #if bsy.pos < 50:
       #   self.info('OPEN HUTCH: Removing moveable beam stop motor bsy! - provisional')
       #   time.sleep(2)
       #   bsy.write_attribute('position',140.0)


       if aperz.getPosition() > -94 or bstopz.getPosition() > -94: 
          self.info('OPEN HUTCH: Wait 8 s')
          time.sleep(10)

       # check the status of the robot 
       try:
           cats = taurus.Device('bl13/eh/cats')
           #Asking the state to receive Exception if the DS is not running.
           cats_state = cats.state()
           cats_running = 'True'
           self.info("OPEN HUTCH: the device server of the robot is running")
       except:
           cats_running = 'False'
           self.warning("OPEN HUTCH WARNING: the device server of the robot is not running") 
 
       # if the robot is running
       # never read CATS attributes from the PLC, read them directly from the robot

       if cats_running:
           limit = 1
           while not cats['do_PRO5_IDL'].value:
              self.warning("OPEN HUTCH WARNING: the robot is not idle, waiting %s of 80 seconds" % limit)
              time.sleep(1)
              limit = limit + 1
              if limit > 80: break
           time.sleep(1)
           if not cats['do_PRO6_RAH'].value: 
               self.error("OPEN HUTCH ERROR: There is a problem with the robot, not idle nor at home")
               self.error("OPEN HUTCH ERROR: TRY CLICKING THE *ON BUTTON* IN THE CATS APPLICATION")
           elif cats['do_PRO6_RAH'].value and not cats['do_PRO5_IDL']: 
                 self.warning("OPEN HUTCH WARNING: There is an error with the robot, the robot is not idle but at home")
                 self.warning("OPEN HUTCH WARNING: Sending an abort command to the robot")
                 try: cats.command_inout('send_op_cmd', 'abort')
                 except: 
                    self.error("OPEN HUTCH ERROR: Could not abort the CATS trajectory")
                    self.error("OPEN HUTCH ERROR: You need to interlock the experimental hutch and click open hutch again")


       # CLOSE THE SAFETY SHUTTER 
       self.info('OPEN HUTCH: Safety shutter in')
       if epsf('read','pshu')[2] != 0:
          try:
             self.execMacro('act pshu in')
             time.sleep(10)
          except:
             self.error('OPEN HUTCH ERROR: Cannot actuate the safety shutter')
             return


       # CHECK THAT THE SAFETY SHUTTER IS REALLY CLOSED
       if epsf('read','pshu')[2] == 0:
          self.info('OPEN HUTCH: The safety shutter is closed')
       else:
          self.error('OPEN HUTCH ERROR:The safety shutter is still open or status is not readable')
          return


       # CHECK POSITIONS OF BSTOP, APER, BACKLIGHT, DIODESAMP 
       limit = 1
       while bstopz.getPosition() > -94.9: 
          current_bstopz_pos = bstopz.getPosition()
          self.warning("OPEN HUTCH WARNING: waiting for the bstopz to be removed. Current position = %s" % current_bstopz_pos )
          limit = limit + 1
          time.sleep(1)
          if limit > 40:
             self.error("ERROR: There is an error with the bstopz")
             return
       limit = 1
       while aperz.getPosition() > -94.9: 
          self.warning("OPEN HUTCH WARNING: waiting for the aperz to be removed")
          limit = limit + 1
          time.sleep(1)
          if limit > 40:
             self.error("OPEN HUTCH ERROR: There is an error with the aperz")
             return
       limit = 1
       while epsf('read','backlight')[2] == 0:
          self.warning("OPEN HUTCH WARNING: waiting for the backlight to be removed")
          limit = limit + 1
          time.sleep(1)
          if limit > 40:
             self.error("OPEN HUTCH ERROR: There is an error with the backlight")
             return
#       limit = 1
       #limit = 0
       #while yagz.getAttribute('StatusMoving').read().value:
           #limit+=1
           #self.warning('OPEN HUTCH: Waiting for the sample diode to be IN... #%d' %limit)
           #time.sleep(1)
           #if limit > 9:
               #self.warning('FLUX_MEASURE: Either yagz still seem to be still moving... ABORTING')
               #return
       #self.info('FLUX_MEASURE: yagz moved to %.3f mm' %(yagz.getPosition() ) )

#       while epsf('read','diodesamp')[2] == 0:
#          self.warning("OPEN HUTCH WARNING: waiting for the diodesamp to be removed")
#          limit = limit + 1
#          time.sleep(1)
#          if limit > 40:
#             self.error("OPEN HUTCH ERROR: There is an error with the diodesamp")
       if bstopz.getPosition() < -94.9 and aperz.getPosition() < -94.9 and yagz.getPosition() < YAGZ_OUT_POSITION+0.3:
          self.execMacro('act ln2cover in')
       self.info('OPEN HUTCH: End of Open Hutch')

       

        



            

       

 




