from sardana.macroserver.macro import Macro, Type
import taurus

class set_pos_change_dial(Macro):
    """Sets the USER position of the motor to the specified value (by changing DIAL and keeping OFFSET)"""
    
    param_def = [
        ['motor', Type.Motor, None, 'Motor name'],
        ['pos',   Type.Float, None, 'Position to move to']
        ]
    
    def run(self, motor, pos):
        self.execMacro('set_pos %s %s' % (motor, pos))

class set_pos_change_offset(Macro):
    """Sets the USER position of the motor to the specified value (by changing OFFSET and keeping DIAL)"""
    
    param_def = [
        ['motor', Type.Motor, None, 'Motor name'],
        ['pos',   Type.Float, None, 'Position to move to']
        ]
    
    def run(self, motor, pos):
        name = motor.getName()
        old_pos = motor.getPosition(force=True)
        offset_attr = motor.getAttribute('Offset')
        old_offset = offset_attr.read().value
        new_offset = pos - (old_pos - old_offset)
        offset_attr.write(new_offset)
        self.output("%s reset from %.4f (offset %.4f) to %.4f (offset %.4f)" % (name, old_pos, old_offset, pos, new_offset))
