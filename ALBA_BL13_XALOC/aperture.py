from sardana.macroserver.macro import Macro, Type
import taurus
import time
from epsf import *

from bl13constants import pentaaperpos_X as px
from bl13constants import pentaaperpos_Z as pz
from bl13constants import APERZ_OUT_POSITION
#from bl13constants import offset_x as offsetx
#from bl13constants import offset_z as offsetz




       #self.info('%s'%aperx.status())



class aperture(Macro):

    '''aperture: macro to select the aperture of choice from the pentaperture
    mode: 5: 5um aperture, 10: 10um aperture, 20: 20um aperture, 30: 30um aperture, 50: 50um aperture)'''

    param_def = [ 
        [ 'mode', Type.String, '20', 'Options: out, 5, 10, 20, 30, 50']
        ]

    def run(self,mode):

       eps = taurus.Device('bl13/ct/eps-plc-01')
       mode = mode.lower()
       
       
       aperz_status=str(taurus.Device('motor/eh_ipap_ctrl/12').state())
       aperx_status=str(taurus.Device('motor/eh_ipap_ctrl/11').state())
       #self.info('The status of aperz is %s'%aperz_status)
       #self.info('The status of aperx is %s'%aperx_status)
       if aperx_status=='ALARM' or aperz_status=='ALARM':
            self.info('Motors in alarm, stopping')
            #return

       #offset_z = -0.60475
       #offset_x = -0.074418
       
        # REMOVE LN2 COVER
       if epsf('read','ln2cover')[2] != 1:
           self.info('APERTURE: Remove the LN2 cover')
           self.execMacro('act ln2cover out')
           limit = 1
           while epsf('read','ln2cover')[2] != 1: #or eps['ln2cover'].quality != PyTango._PyTango.AttrQuality.ATTR_VALID:
               self.info("APERTURE WARNING: waiting for the LN2 cover to be removed")
               limit = limit + 1
               if limit > 50:
                   self.error("APERTURE ERROR: There is an error with the LN2 cover")
                   return
               time.sleep(.5)
       self.execMacro('turn aperx on')
       aperx = self.getMoveable('aperx')
       self.execMacro('turn aperz on')
       aperz = self.getMoveable('aperz')
       for iter in range(20):
          if aperx.getAttribute('PowerOn').read().value and aperz.getAttribute('PowerOn').read().value: break
          time.sleep(.2)
       if not aperx.getAttribute('PowerOn').read().value:
           self.info('aperx motor could not be Powered On')
           return
       if not aperz.getAttribute('PowerOn').read().value:
           self.info('aperz motor could not be Powered On')
           return

       aperz_status=str(taurus.Device('motor/eh_ipap_ctrl/12').state())
       aperx_status=str(taurus.Device('motor/eh_ipap_ctrl/11').state())
       self.info('The status of aperz is %s'%aperz_status)
       self.info('The status of aperx is%s'%aperx_status)

       if mode not in ['out','5', '10','20', '30', '50']:
            self.error('mode should be one of: out 5, 10, 20, 30, 50')
            return
            
       elif mode == 'out':
           self.info('Removing aperture...')
           self.execMacro('mv aperx 0.0')
           self.execMacro('mv aperz %f' % APERZ_OUT_POSITION)
            
       elif mode == '20':
           self.info('APERTURE: Moving to 20um aperture')
           #self.execMacro('mvaperz 0 aperx 0')
           #self.execMacro('mv aperx 0')
           self.execMacro('mv aperz %f' %pz[3])
           self.execMacro('mv aperx %f' %px[3])
           return
           
       elif mode == '5':
           self.info('APERTURE: Moving to 5um aperture')
           #self.execMacro('mvaperz 2.425')
           #self.execMacro('mv aperx 0.05')
           self.execMacro('mv aperz %f'%pz[5])
           self.execMacro('mv aperx %f'%px[5])
           return
           
       elif mode == '10':
           self.info('APERTURE: Moving to 10um aperture')
           #self.execMacro('mvaperz 1.2211')
           #self.execMacro('mv aperx 0.031')
           self.execMacro('mv aperz %f' %pz[4])
           self.execMacro('mv aperx %f' %px[4])
           return
           
       elif mode == '30':
           self.info('APERTURE: Moving to 30um aperture')
           #self.execMacro('mvaperz -1.174')
           #self.execMacro('mv aperx -0.004')
           self.execMacro('mv aperz %f' %pz[2])
           self.execMacro('mv aperx %f' %px[2])
           return
           
       elif mode == '50':
           self.info('APERTURE: Moving to 50um aperture')
           #self.execMacro('mvaperz -2.38512')
           #self.execMacro('mv aperx -0.03')
           self.execMacro('mv aperz %f' %pz[1])
           self.execMacro('mv aperx %f' %px[1])
           return           

           
           
           
           
           
           
           
           
           
           
           
           
           
           
           
           
           
           
           
           
           
           
           
           
           
           
           
           
           
    
