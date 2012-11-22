from sardana.macroserver.macro import Macro, Type
import taurus
import math as m
import time

# self.info() = output in blue    
# self.error() = output in red
# self.output() = output in black



class mvaperz_old(Macro):
    '''
    mv aperz, provisionally until problems with movement are solved
    mvaperz in/out/number
    '''
    param_def = [ [ 'mode', Type.String, '', 'out, in, or position']
                ]
    def run(self, mode):
        #is the movement safe?
        eps = taurus.Device('bl13/ct/eps-plc-01')
        limit = 1
        while eps['ln2cover'].value == 0: 
           self.info("WARNING: waiting for the LN2 cover to be removed")
           limit = limit + 1
           time.sleep(0.5)
           if limit > 30:
              print "ERROR: There is an error with the LN2 cover"
              return
        if eps['ln2cover'].value == 0:
            self.info('LN2 cover must be open to actuate aperz')
            return

        
        aperz = self.getMoveable('aperz')
        mode = mode.upper()
        low_critical_pos = -85
        if mode == 'OUT':
            if aperz.getPosition() > low_critical_pos:
                aperz.write_attribute('frequency',400000)
                self.execMacro('mv aperz %f' %low_critical_pos)
            aperz.write_attribute('frequency',50000)
            # Go to negative limit switch
            self.execMacro('mv aperz -97')
            return
        elif mode == 'IN':
            if aperz.getPosition() < low_critical_pos:
                aperz.write_attribute('frequency',50000)
                self.execMacro('mv aperz %f' %low_critical_pos)
            aperz.write_attribute('frequency',400000)
            self.execMacro('mv aperz 0')
            return
        elif not mode.isalpha():
            finalpos = float(mode)
            if finalpos<low_critical_pos and aperz.getPosition()<=low_critical_pos:
                aperz.write_attribute('frequency',50000)
                self.execMacro('mv aperz %f' %finalpos)
            elif finalpos>=low_critical_pos and aperz.getPosition()>=low_critical_pos:
                aperz.write_attribute('frequency',400000)
                self.execMacro('mv aperz %f' %finalpos)
            elif finalpos>=low_critical_pos and aperz.getPosition()<=low_critical_pos:
                aperz.write_attribute('frequency',50000)
                self.execMacro('mv aperz %f' %low_critical_pos)
                aperz.write_attribute('frequency',400000)
                self.execMacro('mv aperz %f' %finalpos)
            elif finalpos<=low_critical_pos and aperz.getPosition()>=low_critical_pos:
                aperz.write_attribute('frequency',400000)
                self.execMacro('mv aperz %f' %low_critical_pos)
                aperz.write_attribute('frequency',50000)
                self.execMacro('mv aperz %f' %finalpos)
        else:
            self.info('syntax is mvaperz in/out/<absolute position>\naperz position is %f' % aperz.getPosition())
         
                  


