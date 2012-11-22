from sardana.macroserver.macro import Macro, Type
import taurus

class mvs(Macro):
    """Move motor(s) to the specified position(s)"""

    param_def = [
        ['motor', Type.String, None, 'Motor to move'],
        ['pos',   Type.Float, None, 'Position to move to']
    ]

    def run(self, motor, pos):
        eps = taurus.Device('bl13/ct/eps-plc-01') 
        self.info("Starting %s movement to %s", motor, pos)
        if motor in ['bstopz','aperz'] and eps['ln2cover'].value != 1: 
           self.error('ERROR: cannot move %s because the LN2 cover is in',  motor)
           return
        else:
           self.execMacro('mv', motor,pos)


