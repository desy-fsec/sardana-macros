"""
    Set of macros for BL24 - CIRCE
"""

from sardana.macroserver.macro import Macro, macro, Type

class zeroOrderRel(Macro):
    """
        The purpouse of this macro is to move both, grating and mirror of
        monochromator with the same angle. 
        For doing this the first step will be set both motors at the same
        angle, and then move the motors at the same time.
        As a convention we will move the mirror in the first step of the macro
        for fix the same angle in both motors.
    """
    param_def = [ ['gratingMotor', Type.Motor, None, 'Grating Motor'],
                  ['mirrorMotor', Type.Motor, None, 'Mirror Motor'],
                  ['relPos', Type.Float, None, 'relative position to move'],
                ]

    def prepare(self, gratingMotor, mirrorMotor, relPos):
        pass

    def run(self, gratingMotor, mirrorMotor, relPos):
        #First we fix the grating and move the mirror
        grPos = gratingMotor.getPosition()
        mirrorMotor.move(grPos)

        #is this really needed??
        #wait until movement is finished
        isMoving = True
        while(isMoving):
            if str(mirrorMotor.getState()) == 'MOVING':
                isMoving = True
            else:
                isMoving = False

        #Now both motors have the same angle and we can move it in parallel
        macroString = 'umvr GRPIT %d M2PIT %d'%(relPos, relPos)
        self.execMacro(macroString)
        
@macro([['motor', Type.Motor, None, 'Motor to show position']])                
def showPos(self,motor):
    pos = motor.getPosition()
    state = motor.getState()
    self.info('Position = %d'%pos)
    self.info('State = %s'%state)
    if str(state) == 'ON':
        self.info('State is ON')
        pos = pos +1000
        motor.move(pos)
        self.info('Moving')
        pos = pos +1000
        motor.move(pos)
        
    else:
        self.info('Wrong state')
    self.info('New Position %d'%pos)

