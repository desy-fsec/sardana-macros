import time
import PyTango

from sardana.macroserver.macro import Macro, Type
from macro_utils.icepap import *
from macro_utils.motors import moveToHardLim

class coll_homing(Macro):
    
    """ 
    This macro does homing of vertical motor of 2nd coll (BL04-MSPD).
    It will start looking for homing position into positive direction.
    In case of successfully homing macro returns True, in all other cases it return False.
    """
    
    result_def = [
        ['homed',  Type.Boolean, None, 'Motor homed state']
    ]

    MOT_NAME = 'coll_z'
    
    HOMING_DIR = 1    

    def prepare(self, *args, **opts):
        self.mot = self.getObj(self.MOT_NAME, type_class=Type.Motor)
        if self.mot.Limit_switches[1]:
            raise Exception('Motor %s is already at home position. Homing procedure can not be started.' % self.mot.alias())

    def run(self, *args, **opts):        
        try:
            mot_info_dict = create_motor_info_dict(self.mot, self.HOMING_DIR)
            info_dicts = [mot_info_dict]
            res = home(self, info_dicts)
            if res == True:
                self.info('2nd collimator successfully homed.')
            elif res == False:
                self.error('2nd collimator homing failed.')
                return False
            else: 
                self.error('Unknown error. Please contact responsible control engineer.')
            return res
        except Exception, e:
            self.error(repr(e))
            raise e