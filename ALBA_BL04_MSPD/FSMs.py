import PyTango
from sardana.macroserver.macro import Macro, Type
from macro_utils.motors import moveToHardLim
from macro_utils.icepap import *

class fsm_m_homing(Macro):
    """ 
    This macro does homing of FSM_M of BL04-MSPD.
    Homing procedure is done in 2 steps:

    1. Move motor to its positive limit.
       
    2. When it reaches extream, Icepap homing routine is started in negative direction. 
       Whenever motor is stopped by a STOP command, a limit switch or an alarm condition, 
       homing routine is stop immediately.

    In case of successful homing macro returns True, in all other cases it return False
    """
    
    result_def = [
        ['homed',  Type.Boolean, None, 'Motor homed state']
    ]

    FSM_NAME = 'fsm_m_z'
   
    FSM_HOMING_DIR = -1

    def prepare(self, *args, **opts):
        self.fsm = self.getObj(self.FSM_NAME, type_class=Type.Motor)

        fsm_pos = PyTango.AttributeProxy(self.FSM_NAME + '/position')
        fsm_pos_conf = fsm_pos.get_config()

        #here we mask software limits, to allow reaching hardware limits
        self.debug('Masking software limits...')
        self.old_fsm_max = fsm_pos_conf.max_value
        fsm_pos_conf.max_value = '9.999E+003'
        fsm_pos.set_config(fsm_pos_conf)
        

    def run(self, *args, **opts):        
        try:
            info_dict = {self.FSM_NAME:(self.fsm, 999, 1)}
            motorsOnLim = moveToHardLim(self, info_dict.values())
            if len(motorsOnLim) != 1 or motorsOnLim[0] != self.FSM_NAME:
                self.error("%s motor didn't get to it's positive limit. Homing failed.", self.fsm.alias())
                return False
            fsm_info = create_motor_info_dict(self.fsm, self.FSM_HOMING_DIR)
            res = home(self, [fsm_info])
            if res:
                self.info('FSM successfully homed.')
                return True
            else: 
                self.error('FSM homing failed.')
                return False
        finally:
            #@TODO: uncomment this line when fixed serialization problem
            #self.debug('Unmasking software limits...')
            fsm_pos = PyTango.AttributeProxy(self.FSM_NAME + '/position')
            fsm_pos_conf = fsm_pos.get_config()
            fsm_pos_conf.max_value = self.old_fsm_max
            fsm_pos.set_config(fsm_pos_conf)