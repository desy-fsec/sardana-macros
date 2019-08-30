# Latest changes:
# RB 20170130: incorporate DUSP to allow the sample to move out-of-the way and allow both positions for YAG and DIODE

from sardana.macroserver.macro import Macro, Type
import taurus
from datetime import *
import time
import math as m
from pyIcePAP import EthIcePAP
from bl13constants import CRYO_OUT_POS, CRYO_IN_POS, YAGY_SAFETYPOSITION, YAGZ_OUT_POSITION, YAGZ_DIODE_POSITION, YAGZ_YAG_POSITION, BSTOPX_YAG_POSITION
from bl13constants import MBATFOILNAMES
from bl13constants import BSZ_SAFE_POSITION, BSR_OUT_POSITION
from bl13constants.bl13controls import CRYO_ACTUATOR_FAR
import bl13check


# self.info() = output in blue    
# self.error() = output in red
# self.output() = output in black


class fe(Macro):
    '''
    Open or close the front end or get its status

    Parameters:
            mode : open/close
    '''
    param_def = [ [ 'mode', Type.String, 'OPEN', 'One of open, close, or status']
                ]
    def run(self, mode):
        # define devices, variables, dictionaries
        eps = taurus.Device('bl13/ct/eps-plc-01')
        bstopx = self.getMoveable('bstopx')
        bstopz = self.getMoveable('bstopz')
        mode = mode.upper()
        dicts={'True':'ready','False':'not ready'}
        dicto={0:'close',1:'open'}
        # check mode
        if mode not in ['CLOSE', 'OPEN','STATUS', '']:
            self.error('mode should be one of: open, close, status ')
            return
        # open procedures
        elif mode == 'OPEN' :
              #cond_bstop = m.fabs(bstopz.getPosition()) > 0.05 and m.fabs(bstopz.getPosition()) > 0.05
              #cond_shutters =  eps['slowshu'].value == 1 and eps['detcover'].value == 1 and eps['pshu'].value == 1 
              #if cond_shutters and cond_bstop:
              #    self.error('ERROR: it is unsafe to open the FE') 
              try:
                  if not eps['OPEN_FE'].value:
                      eps['OPEN_FE'] = True
                  elif eps['OPEN_FE'].value:
                      self.warning('FE WARNING: FE is already open')
                  for trials in range(100):
                      if eps['fe_open'].value == True:
                          break
                      time.sleep(.2)
                  if eps['fe_open'].value == False:
                      self.error['FE ERROR: Cannot open front end']
              except: 
                  self.error('FE ERROR: Cannot open the FE')
        # close procedures
        elif mode == 'CLOSE' :
              try:     
                  if not eps['CLOSE_FE'].value:
                      eps['CLOSE_FE'] = True 
                  elif eps['CLOSE_FE'].value:
                      self.warning('FE WARNING: FE is already closed')
                  for trials in range(100):
                      if eps['fe_open'].value == False:
                          break
                      time.sleep(.2)
                  if eps['fe_open'].value == True:
                      self.error['FE ERROR: Cannot close front end']
              except:
                  self.error('FE ERROR: Cannot close the FE')
        self.info('FE: FE is %s' % dicto[eps['fe_open'].value])
        self.info('FE: BL ready is %s' % dicts[str(eps['BL_READY'].value)])

class wbat(Macro):
    '''
    Set wbat filters 

    Parameters:
            mode : open/close/status 
    '''
    param_def = [ [ 'mode', Type.String, '', 'out,1,2,3']
                ]
    def run(self, mode):
        eps = taurus.Device('bl13/ct/eps-plc-01')
        mode = mode.upper()
        if mode != '': 
            try:
                if eps['wbat'].value != dicts[mode]:
                    eps['wbat'] = dicts[mode]
                elif eps['wbat'].value == dicts[mode]:
                    self.warning('WBAT: Wbat is already at %s' %dicts[mode])
            except:
                self.warning('WBAT: Invalid mode, it should be 1=empty,2,3,4')
        self.info("WBAT: Wbat is in position %s " % str(eps['wbat'].value)) 
        

class act(Macro):
    '''
    Open/close or set in/out any pneumatic actuator
    Get the status of the actuator 
    '''
    param_def = [ [ 'axis', Type.String, '', 'Valve to actuate: ex. pshu'],
                  [ 'mode', Type.String, 'status', 'One of open/out, close/in, status']
                ]
    def run(self, axis, mode):
        # check status of the robot
        try:
           cats = taurus.Device('bl13/eh/cats')
           cats_running = 'True'
        except:
           cats_running = 'False'
        # set variables, devices, motors, dictionaries
        limit_trials = 10
        eps = taurus.Device('bl13/ct/eps-plc-01')
        blight = taurus.Device('tango://blight') 
        bstopz = self.getMoveable('bstopz')
        bstopx = self.getMoveable('bstopx')
        omegay = self.getMoveable('omegay')
        omegaz = self.getMoveable('omegaz')
        # RB 20190311: REVERT changes introduced becuase of moveable bs dismount
        #bsz = self.getMoveable('bsz')
        #bsx = self.getMoveable('bsx')
        #bsr = self.getMoveable('bsr')
        aperz = self.getMoveable('aperz')
        kappa = self.getMoveable('kappa')
        cryodist = self.getMoveable('cryodist')
        #yagy = self.getMoveable('yagy')
        #yagz = self.getMoveable('yagz')
        #ice = EthIcePAP('icebl1302')
        mode = mode.upper()
        dicts={1:'out',0:'in'}
        dicto={'True':'Near','False':'Far'}

        # special case of cryodist
        if axis == 'cryodist': 
           if mode not in ['IN','OUT', 'FAR','NEAR','STATUS']:
              self.error('mode should be one of: in, out, far, near, status')
              return
           if mode == 'STATUS':
              position = cryodist.getPosition()
              if eps['cry_in'].value: 
                 self.info('The cryostream is in the IN position')
                 return
              elif eps['cry_out'].value: 
                 self.info('The cryostream is in the OUT position')
                 return
              elif eps['cry_far'].value: 
                 self.info('The cryostream is in the FAR position')
                 return
              else:
                 self.info('The cryostream is at %s' % position)
                 return
           initcryodistvelocity = cryodist.getVelocity()
           #cryodist.write_attribute('velocity',2.0)
           #cryodist.write_attribute('velocity',8.55)
           self.execMacro('turn cryodist on')
           #ice.sendWriteCommand('21:shcfg 0 0')
           if mode == 'IN':
              #self.execMacro('mv cryodist -0.5')   14-10-2014
              act_command = 'mv cryodist %f' %CRYO_IN_POS
              self.execMacro(act_command)
              limit = 1
              while not eps['cry_in'].value:
                 limit = limit + 1
                 time.sleep(1)
                 if limit > 60:
                    self.error('ACT ERROR: cryodist did not finish the movement')
                    return
           if mode == 'OUT':
              #self.execMacro('mv cryodist 9')
              act_command = 'mv cryodist %f' %CRYO_OUT_POS
              self.execMacro(act_command)
              limit = 1
              while not eps['cry_out'].value:
                 limit = limit + 1
                 time.sleep(1)
                 if limit > 60:
                    self.error('ACT ERROR: cryodist did not finish the movement')
                    return
           if mode == 'FAR':
              if m.fabs(bstopz.getPosition())<20:
                 self.error('ACT ERROR: Cannot actuate cryodist NEAR/FAR because the bstop is in place. Hint: mv bstopz -95') 
                 return
              #self.execMacro('mv cryodist 73.5')
              limit = 1     
              #while not eps['cry_far'].value:
              #limit = limit + 1
              #time.sleep(1)
              #if limit > 60:
              #self.error('ACT ERROR: cryodist did not finish the movement')
              #return
              #cryodist.write_attribute('velocity',initcryodistvelocity)
              ##ice.sendWriteCommand('21:shcfg 1200 -1200')
              while limit < limit_trials:
                 try:
                     if eps[CRYO_ACTUATOR_FAR].value != 1:# In NEAR position, the value is 0, in FAR, it's 1
                        eps[CRYO_ACTUATOR_FAR] = 1
                     elif eps[CRYO_ACTUATOR_FAR].value == 1:
                        state=dicto[str(eps['CRY_FAR'].value)]
                        self.warning('ACT WARNING: %s is already %s' % (axis,state))
                     # IF THE PREVIOUS COMMAND WORKED, BREAK THE WHILE LOOP
                     break
                 except: 
                     self.warning('ACT WARNING: Pneumatic actuator can not be actuated for %s times (eps dev variable CRYO_ACTUATOR_FAR)' % (limit))
                 time.sleep(0.1)
                 limit = limit + 1
                 return
           if mode == 'NEAR':
              if m.fabs(bstopz.getPosition())<20:
                 self.error('ACT ERROR: Cannot actuate cryodist NEAR/FAR because the bstop is in place. Hint: mv bstopz -95') 
                 return
              limit = 1     
              while limit < limit_trials:
                 try:
                     if eps[CRYO_ACTUATOR_FAR].value != 0: # In NEAR position, the value is 0, in FAR, it's 1
                        eps[CRYO_ACTUATOR_FAR] = 0
                     elif eps[CRYO_ACTUATOR_FAR].value == 0:
                        state=dicto[str(eps['CRY_FAR'].value)]
                        self.warning('ACT WARNING: %s is already %s' % (axis,state))
                     # IF THE PREVIOUS COMMAND WORKED, BREAK THE WHILE LOOP
                     break
                 except: 
                     self.warning('ACT WARNING: Pneumatic actuator can not be actuated for %s times (eps dev variable CRYO_ACTUATOR_FAR)' % (limit))
                     #self.warning('ACT WARNING: Axis %s cannot be actuated the %s time' % (axis,limit))
                 time.sleep(0.1)
                 limit = limit + 1
                 return
        if axis == 'cryodist': return

        # special case diodesamp 
        if axis == 'yagdiode' or axis == 'yag': 
           if mode not in ['IN','OUT', 'STATUS']:
               self.error('ACT ERROR: Mode should be one of: in, out, status')
               return
           
           if eps.ByPassDUSP == False and eps['SOM'].value:
               eps.CmdEnableByPassDUSP()
               while eps.ByPassDUSP == False:
                   time.sleep(0.01)

           self.execMacro('turn yagz on')
           self.execMacro('turn bstopx on')
           
           if mode == 'IN':
              if not bl13check.is_yag_in_allowed():
                  self.error('ACT ERROR: the yag cannot be inserted. Make sure the moveable beamstop is out of the way and the ln2cover is open')
                  return
              if axis == 'yagdiode': 
                  yagy_targetpos = YAGY_SAFETYPOSITION
                  yagz_targetpos = YAGZ_DIODE_POSITION
                  bstopx_targetpos = 0
              elif axis == 'yag': 
                  yagy_targetpos = 0
                  yagz_targetpos = YAGZ_YAG_POSITION
                  bstopx_targetpos = BSTOPX_YAG_POSITION
              self.debug( 'yagy_targetpos %f yagz_targetpos %f bstopx_targetpos %f' % (yagy_targetpos, yagz_targetpos, bstopx_targetpos))
              if cats_running and cats['do_PRO8_RI2'].value: 
                  self.error('ACT ERROR: cannot set the sample diode in because the robot is in RI2')
                  return
              # check for sample on magnet
              if eps['SOM'].value and eps['DI_DISET_EH01_02_LIM_DI'].value == False: # if som and the yagz is down, move sample
                  try:
                      self.info('Sample detected, moving it to a safe place')
                      self.execMacro('mvr omegay -1.5 omegaz 1.5')
                  except:
                      self.error('Could not move sample motors, dusp movement aborted')
                      return
                  
              self.execMacro('mv yagy %f yagz %f bstopx %f' % (yagy_targetpos,yagz_targetpos, bstopx_targetpos))
              return
              
           if mode == 'OUT':
              if eps['DI_DISET_EH01_02_LIM_DI'].value == False: 
                  self.warning('ACT WARNING: %s is already %s' % (axis,mode))
                  return

              limit = 0
              self.execMacro('mv yagy %f yagz %f bstopx %f' % (0,YAGZ_OUT_POSITION,0))
              self.execMacro('act slowshu close')
              while eps['DI_DISET_EH01_02_LIM_DI'].value == True: 
                  limit = limit + 1
                  time.sleep(0.2)
                  if limit > 20:
                      self.error('ACT ERROR: diodesamp could not be actuated: yagz did not reach final position in time. Hint: motor might be off. CHECK YOUR SAMPLE!')
                      return
                      
              # check for sample on magnet
              if eps['SOM'].value:
                  self.info('Sample detected, moving it back to center')
                  self.execMacro('mvr omegay 1.5 omegaz -1.5')
              return
      
        # all other actuators      
        if mode not in ['CLOSE', 'OPEN','IN','OUT', 'STATUS']:
            self.error('ACT ERROR: mode should be one of: open/out, close/in')
            return

        # setting any remaining actuator to OUT 
        elif mode == 'OPEN' or mode == 'OUT':
              # special case ln2cover, make sure the ln2shower is off
              if axis == 'ln2cover':
                  if not bl13check.is_ln2cover_open_allowed():
                      self.error('ACT ERROR: ln2cover in not allowed: ln2shower on?')
                      return

              # special case slowshu: make sure that bstop is in if detcover is out
              if axis == 'slowshu':
                 lim1 = m.fabs(bstopz.getPosition()) > 0.05 or m.fabs(bstopx.getPosition()) > 0.05 
                 lim2 = eps['detcover'].value != 0
                 try:
                    lim3 = m.fabs(bsz.getPosition()) > 0.5 or m.fabs(bsx.getPosition()) > 0.2
                 except:
                    lim3 = True
                 if lim1 and lim2 and lim3:
                    self.error('ACT ERROR: Cannot actuate slowshu because one of the bstops have to be IN if the detcover is OUT') 
                    return
              limit = 1
              while limit < limit_trials:
                 try:
                     if eps[axis].value != 1:
                        eps[axis] = 1
                     elif eps[axis].value == 1:
                        state=dicts[eps[axis].value]
                        self.warning('ACT WARNING: %s is already %s' % (axis,state))
                     # IF THE PREVIOUS COMMAND WORKED, BREAK THE WHILE LOOP
                     break
                 except: 
                     self.warning('ACT WARNING: Axis %s cannot be actuated the %s time' % (axis,limit))
                 time.sleep(0.1)
                 limit = limit + 1
              # special case backlight: turn it off after removing it
              if axis == 'backlight':
                 limit = 1
                 while limit < limit_trials:
                    try:
                       blight.write_attribute('Value', 0) 
                       break
                    except:
                       self.warning('ACT WARNING: trying to turn off the backlight, trial number %s' % limit)
                       time.sleep(0.1)
                    limit = limit + 1
              # CHECK THAT THE BACKLIGHT IS OFF, IF IT GIVES AN EXCEPTION THE MACRO SHOULD STOP HERE
              if blight['Value'].value != 0: 
                 blight.write_attribute('Value', 0) 
                 return

        # setting any remaining actuator to IN 
        elif mode == 'CLOSE' or mode == 'IN':
              try: 
                 # special case ln2cover, make sure aperz, bstopz and backlight are OUT
                 if axis == 'ln2cover':
                    if not bl13check.is_ln2cover_close_allowed():
                       self.error('ACT ERROR: Either bstopz, aperz, yagz or backlight are IN')
                       return

                 # special case of back light
                 if axis == 'backlight':
                     # RB 20190311: REVERT changes introduced becuase of moveable bs dismount
                     #if bsr.getPosition() < BSR_OUT_POSITION:
                     #    self.execMacro('mv bsr %f' % BSR_OUT_POSITION)
                     if not bl13check.is_blight_in_allowed():
                         self.error('ACT ERROR: cannot set the backlight in')
                         return
                 
                 # special case diodesamp
                 # SHOULD NOT ALLOW THE DIODESAMP UP IF THE ROBOT IS RUNNING AND THE ROBOT IS IN RI2, REGARDLESS OF THE TYPE OF TOOL
                 #if axis == 'diodesamp' and cats_running and cats['do_PRO8_RI2'].value: 
                 #      self.error('ACT ERROR: cannot set the sample diode in because the robot is in RI2')
                 #      return

                 # special case distfluo
                 # SHOULD NOT ALLOW THE DISTFLUO UP IF THE ROBOT IS RUNNING AND THE ROBOT IS IN RI2, AND FOR NOW REGARDLESS OF THE TYPE OF TOOL
                 # WE HAVE TO CHECK THAT A PLATE CANNOT CLASH WITH THE FLUO DET 
                 if axis == 'distfluo': 
                       if cats_running and cats['do_PRO8_RI2'].value: 
                          self.error('ACT ERROR: cannot set the fluo det in because the robot is in RI2')
                          return
                       #if m.fabs(kappa.getPosition()) > 0.01 and not kappa.getAttribute('StatusLimNeg').read().value: 
                       #   self.error('ACT ERROR: cannot set the fluo det in because kappa != 0')
                       #   return
                       if not bl13check.is_distfluo_in_allowed(): 
                          self.error('ACT ERROR: cannot set the fluo det in because kappa is in the way. Hint: move omega to 270 in OAV')
                          return
                 limit = 1
                 while limit < limit_trials:
                     try:
                         if eps[axis].value != 0:
                            eps[axis] = 0
                         elif eps[axis].value == 0:
                            state=dicts[eps[axis].value]
                            self.warning('ACT WARNING: %s is already %s' % (axis,state))
                         # IF THE PREVIOUS COMMAND WORKED, BREAK THE WHILE LOOP
                         break
                     except: 
                         self.warning('ACT WARNING: Axis %s cannot be actuated the %s time' % (axis,limit))
                         return
                     time.sleep(0.1)
                     limit = limit + 1
                 if limit == limit_trials: self.error('ACT ERROR: the element could not be actuated, maybe impeded by EPS')

                 # Special case backlight: turn it on after inserting it
                 if axis == 'backlight':
                    limit = 1
                    while limit < 5:
                        try:
                            blight['Value'] = 1
                            break
                        except:
                            self.warning('ACT WARNING: trying to turn on the backlight, trial number %s' % limit)
                        time.sleep(0.1)
                        limit = limit + 1
                    # CHECK THAT THE BACKLIGHT IS OFF, IF IT GIVES AN EXCEPTION THE MACRO SHOULD STOP HERE
                    #if blight['Value'].value != 0: blight['Value'] = 1
              except Exception as e:
                  self.warning('ACT WARNING: Axis %s cannot be actuated\n%s' % (axis, str(e)))
                  return
        elif mode == 'STATUS' or mode == '':
              state=dicts[eps[axis].value]
              self.info('ACT: %s is %s' % (axis,state))


class mbat(Macro):
    '''
   mbat in/close, out/open, status
   Actuate any of the mbat foils:
   7AL,14AL,25AL,50AL,100AL,200AL,500AL,FE,NI,ZN,AU,ZR
   mbat all   gives you the status of all the actuators
'''
    param_def = [ [ 'foil', Type.String, 'all', 'Mbat foil to actuate, all gives status of all mbats'],
                  [ 'mode', Type.String, 'status', 'One of open/out, close/in, status']
                ]
    def run(self, foil, mode):
        # define devices, dictionaries
        eps = taurus.Device('bl13/ct/eps-plc-01')
        foil = foil.upper()
        mode = mode.upper()
        mode_val = 0
#        dictf={'7AL':'mbat16','14AL':'mbat15','25AL':'mbat14','50AL':'mbat13',
#               '100AL':'mbat12','200AL':'mbat11','500AL':'mbat26','FE':'mbat25',
#               'NI':'mbat24','ZN':'mbat23','AU':'mbat22','ZR':'mbat21'}
        # 2014.05.07 JJ - AU and FE actuators were interchanged!
        # 2016.11.22 RB introduce bl13constants definition of mbattrans foils
        dictf=MBATFOILNAMES
        list_foils = MBATFOILNAMES.keys()
        dicts={0:'out',1:'in'}
        #list_foils = ['7AL', '14AL','25AL','50AL','100AL','200AL','500AL','FE','NI','ZN','AU','ZR']

        # command ALL
        if foil == 'ALL':
           for a in list_foils:
                state=dicts[eps[dictf[a]].value]
                self.info('MBAT: %s is %s' %(a,state)) 
           return     

        # check foil is in the list
        if foil not in list_foils:
           self.error('MBAT ERROR: Unknown foil') 
           return

        # check mode is correct
        if mode not in ['CLOSE', 'OPEN','IN','OUT', 'STATUS']:
            self.error('MBAT ERROR: Mode should be one of: open, close ')
            return

        # set foil OUT
        elif mode == 'OPEN' or mode == 'OUT':
              try:
                  if eps[dictf[foil]].value != 0:
                      eps[dictf[foil]] = 0 
                  elif eps[dictf[foil]].value == 0:
                      self.warning('MBAT WARNING: foil %s is already out' %foil)
                  for iter in range(50):
		    time.sleep(0.4)
		    if eps[dictf[foil]].quality!=3: break 
                  state=dicts[eps[dictf[foil]].value]
                  self.info('MBAT: %s is state %s' %(foil,state))
              except:
                  self.warning('MBAT WARNING: Axis %s cannot be actuated' % foil)

        # set foil IN
        elif mode == 'CLOSE' or mode == 'IN':
              try:
                  if eps[dictf[foil]].value != 1: 
                      eps[dictf[foil]] = 1 
                  elif eps[dictf[foil]].value == 1:
                      self.warning('MBAT WARNING: foil %s is already in' %foil)
                  for iter in range(50):
		    time.sleep(0.4)
		    if eps[dictf[foil]].quality!=3: break 
                  state=dicts[eps[dictf[foil]].value]
                  self.info('MBAT: %s is state %s' %(foil,state))
              except:
                  self.error('MBAT ERROR: Axis %s cannot be actuated' % foil)
                  return

        # query foil STATUS
        elif mode == 'STATUS':
              state=dicts[eps[dictf[foil]].value]
              self.info('MBAT: Foil %s is %s' % (foil,state))
               
 
class close_slowshu(Macro):

    ''' close_slowshu: macro to close the slow shutter manually from the controlator widget '''

    param_def = [
                  
                ]

    def run(self):
        eps = taurus.Device('bl13/ct/eps-plc-01')

        self.info('CLOSE_SLOWSHU: Closing slow shutter')

        limit = 1
        while limit < 10:
            try:
                eps.write_attribute('slowshu', 0)
                break
            except:
                self.error('CLOSE_SLOWSHU ERROR: Cannot actuate the slowshu')
            limit = limit + 1










































































