from sardana.macroserver.macro import Macro, Type
import taurus
import time

class openhutch(Macro):

    '''
           To safely open the hutch:
           removes the backlight, closes the slowshutter, closes the safety shutter,
           removes the beamstop, moves detector to safe distance 
    '''

    def run(self):
       # DEFINE DEVICES
       eps = taurus.Device('bl13/ct/eps-plc-01')
       bstopz = self.getMoveable("bstopz")
       aperz = self.getMoveable("aperz")
       omega = self.getMoveable("omega")

      # MOVE OMEGA BACK TO 0 
       omega.write_attribute('position',0)

      # MOVE DETECTOR TO SAFE POSITION 
       self.info('Move detector to a safe position')
       self.execMacro('turn dettaby on')
       dettaby = self.getMoveable("dettaby")
       dettabypos = dettaby.getPosition()
       if dettabypos < 200:
           try:
              dettaby.write_attribute('position',200)
           except:
              self.error('ERROR: Cannot actuate the dettaby')
              return


      # CLOSE DETECTOR COVER 
       self.info('Close the detector cover')
       self.execMacro('act detcover in')

       # CLOSE FAST SHUTTER
       self.execMacro('ni660x_shutter_open_close close') 


       # CLOSE THE SLOW SHUTTER
       self.info('Slow shutter in')
       try: eps['slowshu'] = 0
       except:
          self.error('ERROR: Cannot actuate the slowshu')
          return


       # REMOVE LN2 COVER
       #self.execMacro('act ln2cover out') 


       # REMOVE fluodet 
       self.execMacro('act distfluo out') 


       # REMOVE BACKLIGHT
       self.info('Backlight out')
       self.execMacro('act backlight out')



       # unzoom 
       self.info('Move zoom to 0.5')
       self.execMacro('turn zoommot on')
       zoommot = self.getMoveable("zoommot")
       zoommot.write_attribute('position',0.5)
 
 
       # MOVE BSTOPZ OUT
       if eps['ln2cover'].value == 1:
           self.info('Remove bstopz')
           self.execMacro('turn bstopz on')
           lim1 = bstopz.getAttribute('StatusLim-').read().value
           try: 
              if not lim1:
                 self.info('Moving bstopz')
                 bstopz.write_attribute('position',-96.0)
              elif lim1:
                 self.info('Bstopz is at the lim-')
           except:
              self.error('ERROR: Cannot move bstopz')
              return

       # MOVE APERZ OUT
           current_aperz_pos = aperz.getPosition()
           if current_aperz_pos>-94:
              self.info('Remove aperz')
              self.execMacro('turn aperz on')
              self.execMacro('mvaperz out')

       if aperz.getPosition() > -94 or bstopz.getPosition() > -94: 
          self.info('wait 4 s')
          time.sleep(4)

       # check that the robot is idle
       limit = 1
       while not eps['idl'].value:
          self.warning("WARNING: the robot is still running or is OFF")
          limit = limit + 1
          time.sleep(1)
          if limit > 40:
             if eps['rah'].value:
                 self.warning("WARNING: There is an error with the robot, the robot is not idle but at home")
                 break
             if not eps['rah'].value:
                 self.error("WARNING: There is a problem with the robot, not idle or at home | or OFF")
                 self.error("WARNING: Should press abort before pressing open hutch")
                 break
                 #return


       # CLOSE THE SAFETY SHUTTER 
       self.info('Safety shutter in')
       if not eps['pshu'].value == 0:
          try:
             self.execMacro('act pshu in')
             time.sleep(10)
          except:
             self.error('ERROR: Cannot actuate the safety shutter')
             return


       # CHECK THAT THE SAFETY SHUTTER IS REALLY CLOSED
       if eps['pshu'].value == 0:
          self.info('The safety shutter is closed')
       else:
          self.error('ERROR:The safety shutter is still open or status is not readable')
          return


       # CHECK POSITION BSTOP AND APER 
       limit = 1
       while bstopz.getPosition() > -94.9: 
          current_bstopz_pos = bstopz.getPosition()
          self.warning("WARNING: waiting for the bstopz to be removed. Current position = %s" % current_bstopz_pos )
          limit = limit + 1
          time.sleep(1)
          if limit > 40:
             self.error("ERROR: There is an error with the bstopz")
             return
       limit = 1
       while aperz.getPosition() > -94.9: 
          self.warning("WARNING: waiting for the aperz to be removed")
          limit = limit + 1
          time.sleep(1)
          if limit > 40:
             self.error("ERROR: There is an error with the aperz")
             return
       limit = 1
       while eps['backlight'].value == 0:
          self.warning("WARNING: waiting for the backlight to be removed")
          limit = limit + 1
          time.sleep(1)
          if limit > 40:
             self.error("ERROR: There is an error with the backlight")
             return
       limit = 1
       while eps['diodesamp'].value == 0:
          self.warning("WARNING: waiting for the diodesamp to be removed")
          limit = limit + 1
          time.sleep(1)
          if limit > 40:
             self.error("ERROR: There is an error with the diodesamp")
       if bstopz.getPosition() < -94.9 and aperz.getPosition() < -94.9:
          self.execMacro('act ln2cover in')
       self.info('End of Open Hutch')

       

        



            

       

 




