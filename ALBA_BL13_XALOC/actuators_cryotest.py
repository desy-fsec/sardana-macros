from sardana.macroserver.macro import Macro, Type
import taurus
from datetime import *
import time
import math as m
from pyIcePAP import EthIcePAP


# self.info() = output in blue    
# self.error() = output in red
# self.output() = output in black


class actcryotest(Macro):
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
        ice = EthIcePAP('icebl1302')
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
           cryodist.write_attribute('velocity',2)
           self.execMacro('turn cryodist on')
           ice.sendWriteCommand('21:shcfg 0 0')
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
           ice.sendWriteCommand('21:shcfg 800 -600')
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




















































