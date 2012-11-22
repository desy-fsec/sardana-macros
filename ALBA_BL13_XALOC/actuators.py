from sardana.macroserver.macro import Macro, Type
import taurus
from datetime import *
import time
import math as m
from pyIcePAP import EthIcePAP


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
        eps = taurus.Device('bl13/ct/eps-plc-01')
        bstopx = self.getMoveable('bstopx')
        bstopz = self.getMoveable('bstopz')
        mode = mode.upper()
        dicts={'True':'ready','False':'not ready'}
        dicto={0:'close',1:'open'}
        if mode not in ['CLOSE', 'OPEN','STATUS', '']:
            self.error('mode should be one of: open, close, status ')
            return
        elif mode == 'OPEN' :
              #cond_bstop = m.fabs(bstopz.getPosition()) > 0.05 and m.fabs(bstopz.getPosition()) > 0.05
              #cond_shutters =  eps['slowshu'].value == 1 and eps['detcover'].value == 1 and eps['pshu'].value == 1 
              #if cond_shutters and cond_bstop:
              #    self.error('ERROR: it is unsafe to open the FE') 
              try:
                  eps['OPEN_FE'] = True
                  for trials in range(100):
                      if eps['fe_open'].value == True:
                          break
                      time.sleep(.2)
                  if eps['fe_open'].value == False:
                      self.error['ERROR: cannot open front end']
              except: 
                  self.warning('Cannot open the FE')
        elif mode == 'CLOSE' :
              try:     
                  eps['CLOSE_FE'] = True 
                  for trials in range(100):
                      if eps['fe_open'].value == False:
                          break
                      time.sleep(.2)
                  if eps['fe_open'].value == True:
                      self.error['ERROR: cannot close front end']
              except:
                  self.warning('Cannot close the FE')
        self.info('FE is %s' % dicto[eps['fe_open'].value])
        self.info('BL ready is %s' % dicts[str(eps['BL_READY'].value)])

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
                eps['wbat'] = dicts[mode]
            except:
                self.warning('invalid mode, it should be 1=empty,2,3,4')
        self.info("wbat is in position %s " % str(eps['wbat'].value)) 
        



class act(Macro):
    '''
    Open/close or set in/out any pneumatic actuator
    Get the status of the actuator 
    '''
    param_def = [ [ 'axis', Type.String, '', 'Valve to actuate: ex. pshu'],
                  [ 'mode', Type.String, '', 'One of open/out, close/in, status']
                ]
    def run(self, axis, mode):
        eps = taurus.Device('bl13/ct/eps-plc-01')
        blight = self.getMoveable('tango://blight') 
        bstopz = self.getMoveable('bstopz')
        aperz = self.getMoveable('aperz')
        kappa = self.getMoveable('kappa')
        cryodist = self.getMoveable('cryodist')
        #ice = EthIcePAP('icebl1302')
        mode = mode.upper()
        dicts={1:'out',0:'in'}
        if axis == 'cryodist': 
           if mode not in ['IN','OUT', 'FAR','STATUS']:
              self.error('mode should be one of: in, out, far')
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
           cryodist.write_attribute('velocity',2.0)
           self.execMacro('turn cryodist on')
           #ice.sendWriteCommand('21:shcfg 0 0')
           if mode == 'IN':
              self.execMacro('mv cryodist 0')
              limit = 1
              while not eps['cry_in'].value:
                 limit = limit + 1
                 time.sleep(2)
                 if limit > 60:
                    self.error('ERROR: cryodist did not finish the movement')
                    return
           if mode == 'OUT':
              self.execMacro('mv cryodist 9')
              limit = 1
              while not eps['cry_out'].value:
                 limit = limit + 1
                 time.sleep(2)
                 if limit > 60:
                    self.error('ERROR: cryodist did not finish the movement')
                    return
           if mode == 'FAR':
              self.execMacro('mv cryodist 96')
              limit = 1     
              while not eps['cry_far'].value:
                 limit = limit + 1
                 time.sleep(2)
                 if limit > 60:
                    self.error('ERROR: cryodist did not finish the movement')
                    return
           cryodist.write_attribute('velocity',initcryodistvelocity)
           #ice.sendWriteCommand('21:shcfg 1200 -1200')
           return
        if axis == 'cryodist':
           return
        if mode not in ['CLOSE', 'OPEN','IN','OUT', 'STATUS']:
            self.error('mode should be one of: open/out, close/in')
            return
        elif mode == 'OPEN' or mode == 'OUT':
              try:
                  eps[axis] = 1
              except: 
                  self.warning('Axis %s cannot be actuated' % axis)
                  return
        elif mode == 'CLOSE' or mode == 'IN':
              try: 
                 if axis == 'ln2cover':
                    lim1 = aperz.getPosition() < -93 
                    lim2 = bstopz.getPosition() < -93 
                    lim3 = eps['backlight'].value == 1
                    if not (lim1 and lim2 and lim3):
                       self.error('ERROR: Either bstopz, aperz, backlight are in')
                       self.info('bstopz < -96 %s' % lim1)
                       self.info('aperz < -96  %s' % lim2)
                       self.info('Lim - backlight is %s' % lim3)
                       return
                 if axis == 'backlight' and eps['ri2'].value:
                       self.error('ERROR: cannot set the backlight in because the robot is in RI2')
                       return
                 if axis == 'diodesamp' and eps['ri2'].value:
                       self.error('ERROR: cannot set the sample diode in because the robot is in RI2')
                       return
                 if axis == 'distfluo': 
                       if eps['ri2'].value:
                          self.error('ERROR: cannot set the fluo det in because the robot is in RI2')
                          return
                       if m.fabs(kappa.getPosition()) > 0.01 and not kappa.getAttribute('StatusLim-').read().value: 
                          self.error('ERROR: cannot set the fluo det in because kappa != 0')
                          return
                 eps[axis] = 0
                 if axis == 'backlight':
                    blight['Value'] = 0
              except:
                  self.warning('Axis %s cannot be actuated' % axis)
                  return
        elif mode == 'STATUS' or mode == '':
              state=dicts[eps[axis].value]
              self.info('%s is %s' % (axis,state))


class mbat(Macro):
    '''
   mbat in/close, out/open, status
   Actuate any of the mbat foils:
   7AL,14AL,25AL,50AL,100AL,200AL,500AL,FE,NI,ZN,AU,ZR
   mbat all   gives you the status of all the actuators
'''
    param_def = [ [ 'foil', Type.String, '', 'Mbat foil to actuate, all gives status of all mbats'],
                  [ 'mode', Type.String, '', 'One of open/out, close/in, status']
                ]
    def run(self, foil, mode):
        eps = taurus.Device('bl13/ct/eps-plc-01')
        foil = foil.upper()
        mode = mode.upper()
        mode_val = 0
        dictf={'7AL':'mbat16','14AL':'mbat15','25AL':'mbat14','50AL':'mbat13',
               '100AL':'mbat12','200AL':'mbat11','500AL':'mbat26','FE':'mbat25',
               'NI':'mbat24','ZN':'mbat23','AU':'mbat22','ZR':'mbat21'}
        dicts={0:'out',1:'in'}
        list_foils = ['7AL', '14AL','25AL','50AL','100AL','200AL','500AL','FE','NI','ZN','AU','ZR']
        if foil == 'ALL':
           for a in list_foils:
                state=dicts[eps[dictf[a]].value]
                self.info('%s is %s' %(a,state)) 
           return     
        if foil not in list_foils:
           self.error('Unknown foil') 
           return
        if mode not in ['CLOSE', 'OPEN','IN','OUT', 'STATUS']:
            self.error('mode should be one of: open, close ')
            return
        elif mode == 'OPEN' or mode == 'OUT':
              try:
                  eps[dictf[foil]] = 0 
                  state=dicts[eps[dictf[foil]].value]
                  self.info('%s is state %s' %(foil,state))
              except:
                  self.warning('Axis %s cannot be actuated' % foil)
        elif mode == 'CLOSE' or mode == 'IN':
              try:
                  eps[dictf[foil]] = 1 
                  state=dicts[eps[dictf[foil]].value]
                  self.info('%s is state %s' %(foil,state))
              except:
                  self.warning('Axis %s cannot be actuated' % foil)
                  return
        elif mode == 'STATUS':
              state=dicts[eps[dictf[foil]].value]
              self.info('Foil %s is %s' % (foil,state))
               
 










































































