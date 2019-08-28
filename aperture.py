from sardana.macroserver.macro import Macro, Type
import time
from epsf import *
from bl13constants import pentaaperpos_X as px
from bl13constants import pentaaperpos_Z as pz
from bl13constants import APERZ_OUT_POSITION

from PyTango import DeviceProxy
#from bl13constants import (pentaaperpos_X, pentaaperpos_Z
from bl13constants import pentaaper_postolerance_X, pentaaper_postolerance_Z
from sardana.macroserver.macro import Macro


class move_aperture(Macro):
    """
    Select the aperture from the pentaperture controller (2 motors)
    Possible values:
        out: remove aperture from beam trajectory
        5: 5um aperture
        10: 10um aperture
        20: 20um aperture
        30: 30um aperture
        50: 50um aperture
    """
    param_def = [
        [ 'mode', Type.String, '20', 'Options: out, 5, 10, 20, 30, 50']
        ]

    def run(self,mode):

       mode = mode.lower()

       aperz_status=str(taurus.Device('motor/eh_ipap_ctrl/12').state())
       aperx_status=str(taurus.Device('motor/eh_ipap_ctrl/11').state())
       if aperx_status=='ALARM' or aperz_status=='ALARM':
            self.error('Motors in alarm, stopping')
            return

       # REMOVE LN2 COVER
       if epsf('read','ln2cover')[2] != 1:
           self.info('APERTURE: Remove the LN2 cover')
           self.execMacro('act ln2cover out')
           limit = 1
           while epsf('read','ln2cover')[2] != 1:
               self.info("APERTURE WARNING: waiting for the LN2 cover to be"
                         "removed")
               limit = limit + 1
               if limit > 50:
                   self.error("APERTURE ERROR: Error with the LN2 cover")
                   return
               time.sleep(.5)
       self.execMacro('turn aperx on')
       aperx = self.getMoveable('aperx')
       self.execMacro('turn aperz on')
       aperz = self.getMoveable('aperz')
       for iter in range(20):
          if (aperx.getAttribute('PowerOn').read().value and
              aperz.getAttribute('PowerOn').read().value):
              break
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


class aperture_update_configuration(Macro):
    """
    Category: Configuration

    Macro intended to send tha calibration (dynamic attribute) to the
    penta aperture pseudo motor (aperture). The calibration is constructed
    by importing the list of values and tolerances of each pseudomotor from
    a python module (bl13constants). The calibration is validated against
    the existent labels (available pseudo positions) of the pseudomotor.
    It is MANDATORY to restart the pool to apply the changes after applying
    the new calibration.
    """

    def motor_fuzzy_positions_list(self, pos, tol):
        flist = []
        for value, res in zip(pos, tol):
            min = value - res
            max = value + res
            p = [min, value, max]
            flist.append(p)
        return flist

    #param_def = [[]]

    def prepare(self):
        self.aperture = DeviceProxy('aperture')
        self.vars = DeviceProxy('bl13/ct/variables')
        # Read values from file and check consistency with existent labels
        xpos = self.vars.pentaaperpos_X
        xtol = pentaaper_postolerance_X
        zpos = self.vars.pentaaperpos_Z
        ztol = pentaaper_postolerance_Z
        npos = self.aperture.nlabels

        lxpos = len(xpos)
        lxtol = len(xtol)
        lzpos = len(zpos)
        lztol = len(ztol)

        size = [lxpos, lxtol, lzpos, lztol]
        self.debug('x_pos (%s) = %s' % (lxpos, xpos))
        self.debug('x_tol (%s) = %s' % (lxtol, xtol))
        self.debug('z_pos (%s) = %s' % (lzpos, zpos))
        self.debug('z_tol (%s) = %s' % (lztol, ztol))

        # If the values are consistent, build the calibration
        if all(npos == x for x in size):
            self.calib = []
            self.calib.append(self.motor_fuzzy_positions_list(xpos, xtol))
            self.calib.append(self.motor_fuzzy_positions_list(zpos, ztol))
            self.debug('Calibration:')
            self.debug(repr(self.calib))
        else:
            raise Exception('Invalid data to build a calibration.')

    def run(self):
        self.info('Sending calibration to aperture.')
        try:
            self.info(str(self.calib))
            self.aperture.write_attribute('calibration', str(self.calib))
            msg = '[done]'
            self.info(msg)
        except:
            raise Exception('Calibration cannot be sent to aperture.')
