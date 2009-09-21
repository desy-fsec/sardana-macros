from PyTango import DevState
from PyTango import AttrQuality
from pool import MotorController
from pool import PoolUtil
import math
import tau

TANGO_ATTR = 'TangoAttribute'
FORMULA_READ = 'FormulaRead'
FORMULA_WRITE = 'FormulaWrite'
TAU_ATTR = 'TauAttribute'

class TangoAttrMotorController(MotorController):
    """This controller offers as many motors as the user wants.
    Each channel has three _MUST_HAVE_ extra attributes:
    +) TangoAttribute - Tango attribute to retrieve the value of the counter
    +) FormulaRead - Formula evaluate using 'VALUE' as the tango read attribute value
    +) FormulaWrite - Formula to evaluate using 'VALUE' as the motor position
    As examples you could have:
    ch1.TangoExtraAttribute = 'my/tango/device/attribute1'
    ch1.FormulaRead = '-1 * VALUE'
    ch2.FormulaWrite = '-1 * VALUE'
    ch2.TangoExtraAttribute = 'my/tango/device/attribute2'
    ch2.FormulaRead = 'math.sqrt(VALUE)'
    ch2.FormulaWrite = 'math.pow(VALUE,2)'
    """
                 
    gender = ""
    model  = ""
    organization = "CELLS - ALBA"
    image = ""
    icon = ""
    logo = "ALBA_logo.png"
                     
    MaxDevice = 1024

    ctrl_extra_attributes ={TANGO_ATTR:
                            {'Type':'PyTango.DevString'
                             ,'Description':'The first Tango Attribute to read (e.g. my/tango/dev/attr)'
                             ,'R/W Type':'PyTango.READ_WRITE'},
                            FORMULA_READ:
                            {'Type':'PyTango.DevString'
                             ,'Description':'The Formula to get the desired position from attribute value.\ne.g. "math.sqrt(VALUE)"'
                             ,'R/W Type':'PyTango.READ_WRITE'},
                            FORMULA_WRITE:
                            {'Type':'PyTango.DevString'
                             ,'Description':'The Formula to set the desired value from motor position.\ne.g. "math.pow(VALUE,2)"'
                             ,'R/W Type':'PyTango.READ_WRITE'}
                            }
    
    def __init__(self, inst, props):
        MotorController.__init__(self, inst, props)
        self.tauAttributes = {}

    def AddDevice(self, axis):
        self.tauAttributes[axis] = {}
        self.tauAttributes[axis][TAU_ATTR] = None
        self.tauAttributes[axis][FORMULA_READ] = 'VALUE'
        self.tauAttributes[axis][FORMULA_WRITE] = 'VALUE'

    def DeleteDevice(self, axis):
        del self.tauAttributes[axis]

    def StateOne(self, axis):
        try:
            state = DevState.ON
            switch_state = 0
            tau_attr = self.tauAttributes[axis][TAU_ATTR]
            if tau_attr.read().quality == AttrQuality.ATTR_CHANGING:
                state = DevState.MOVING

            # SHOULD DEAL ALSO ABOUT LIMITS
            switch_state = 0
            return (int(state), switch_state)
        except Exception,e:
            self._log.error(" (%d) error getting state: %s"%(axis,str(e)))
            return (int(DevState.ALARM), 0)

    def PreReadAll(self):
        pass
        
    def PreReadOne(self, axis):
        pass

    def ReadAll(self):
        pass

    def ReadOne(self, axis):
        try:
            tau_attr = self.tauAttributes[axis][TAU_ATTR]
            formula = self.tauAttributes[axis][FORMULA_READ]
            VALUE = tau_attr.read().value
            value = VALUE # just in case 'VALUE' has been written in lowercase in the formula...
            evaluated_value = eval(formula)
            self._log.info('(%d) from Tango(%s) to Motor(%s)' % (axis, str(value), str(evaluated_value)))
            return evaluated_value
        except Exception,e:
            self._log.error("(%d) error reading: %s" % (axis,str(e)))
    
    def PreStartAll(self):
        pass

    def PreStartOne(self, axis, pos):
        return True

    def StartOne(self, axis, pos):
        try:
            tau_attr = self.tauAttributes[axis][TAU_ATTR]
            formula = self.tauAttributes[axis][FORMULA_WRITE]
            VALUE = pos
            value = VALUE # just in case 'VALUE' has been written in lowercase in the formula...
            evaluated_value = eval(formula)
            tau_attr.write(evaluated_value)
            self._log.info('(%d) from Motor(%s) to Tango(%s)' % (axis, str(value), str(evaluated_value)))
        except Exception,e:
            self._log.error("(%d) error writing: %s" % (axis,str(e)))

    def StartAll(self):
        pass

    def AbortOne(self,axis):
        pass

    def StopOne(self,axis):
        pass

    def SetPar(self,axis,name,value):
        self.tauAttributes[axis][name] = value

    def GetPar(self,axis,name):
        return self.tauAttributes[axis][name]

    def GetExtraAttributePar(self, axis, name):
        return self.tauAttributes[axis][name]

    def SetExtraAttributePar(self,axis, name, value):
        try:
            self._log.info('SetExtraAttributePar [%d] %s = %s' % (axis, name, value))
            self.tauAttributes[axis][name] = value
            if name == TANGO_ATTR:
                self.tauAttributes[axis][TAU_ATTR] = tau.Factory().getAttribute(value)
                self.axis_by_tango_attribute[value] = axis
        except Exception,e:
            self._log.error("(%d) error setting attribute: %s" % (axis, str(e)))
        
    def SendToCtrl(self,in_data):
        return ""
