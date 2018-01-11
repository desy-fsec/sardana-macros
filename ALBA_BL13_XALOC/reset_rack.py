from sardana.macroserver.macro import Macro, Type
import taurus
from epsf import *

class reset_rack(Macro):

    '''This macro is used to reset racks icebl1301 and icebl1302'''

    param_def = [ 
                  [ 'rack', Type.String, None, 'rack: icebl1301, icebl1302, all']         
                ]

    def run(self,rack):
        rack = rack.lower()
        if rack == 'icebl1301':
            #self.info('RESET_MACRO: Resetting rack icebl1301')
            #self.info('RESET_MACRO: Crate 0')
            self.execMacro('ipap_reset_motor foilb1')
            #self.info('RESET_MACRO: Crate 1')
            self.execMacro('ipap_reset_motor s3r')
            #self.info('RESET_MACRO: Crate 2')
            self.execMacro('ipap_reset_motor vfmbenb')
            #self.info('RESET_MACRO: Crate 3')
            self.execMacro('ipap_reset_motor hfmbenb')
            #self.info('RESET_MACRO: Crate 4')
            self.execMacro('ipap_reset_motor bpm4x')
            return
            
        if rack == 'icebl1302':
            #self.info('RESET_MACRO: Resetting rack icebl1302')
            #self.info('RESET_MACRO: Crate 0')
            self.execMacro('ipap_reset_motor centx')
            #self.info('RESET_MACRO: Crate 1')
            self.execMacro('ipap_reset_motor bstopz')
            #self.info('RESET_MACRO: Crate 2')
            self.execMacro('ipap_reset_motor cryodist')
            #self.info('RESET_MACRO: Crate 3')
            self.execMacro('ipap_reset_motor dettaby')
            #self.info('RESET_MACRO: Crate 4')
            self.execMacro('ipap_reset_motor s4vg')  
            return
            
        if rack == 'all':
            self.info('RESET_MACRO: Resetting rack icebl1301')
            self.info('RESET_MACRO: Crate 0')
            self.execMacro('ipap_reset_motor foilb1')
            self.info('RESET_MACRO: Crate 1')
            self.execMacro('ipap_reset_motor s3r')
            self.info('RESET_MACRO: Crate 2')
            self.execMacro('ipap_reset_motor vfmbenb')
            self.info('RESET_MACRO: Crate 3')
            self.execMacro('ipap_reset_motor hfmbenb')
            self.info('RESET_MACRO: Crate 4')
            self.execMacro('ipap_reset_motor bpm4x')    
            self.info('RESET_MACRO: Resetting rack icebl1302')
            self.info('RESET_MACRO: Crate 0')
            self.execMacro('ipap_reset_motor centx')
            self.info('RESET_MACRO: Crate 1')
            self.execMacro('ipap_reset_motor bstopz')
            self.info('RESET_MACRO: Crate 2')
            self.execMacro('ipap_reset_motor cryodist')
            self.info('RESET_MACRO: Crate 3')
            self.execMacro('ipap_reset_motor dettaby')
            self.info('RESET_MACRO: Crate 4')
            self.execMacro('ipap_reset_motor s4vg')  
            return
       
