
import time
from sardana.macroserver.macro import *

#class kbMove(Macro):

    #param_def = [
        #['motor', Type.Moveable, None, 'Motor to move'],
        #['position', Type.Float, None, 'Position to move'],
    #]

    #def run(self,motor, position):
        #while(True):
            #self.execMacro('umvr HPIT 20000 HX 40000')
            #time.sleep(180)


@macro()
def kbMoveH(self):
    index=0
    while(index < 4):
        index = index +1
        self.execMacro('umvr HPIT 20000 HX 40000')
        self.output('Iteration number: %d'%index)
        time.sleep(180)


@macro([["motor", Type.String, None, "Motor to move"],
        ["increment", Type.Integer, None, "Increment to move"],
        ["intervals", Type.Integer, None, "Number of intervals"]
        ])
def kbMoveOnlyOneMotor(self, motor, increment, intervals):
    index=0
    while(index < intervals):
        index = index +1
        self.execMacro('umvr %s %d'%(motor,increment))
        self.output('Iteration number: %d'%index)
        time.sleep(180)
        

@macro()
def kbMoveV(self):
    index=0
    while(True):
        index = index +1
        self.execMacro('umvr VPIT -20000 VX -40000')
        self.output('Iteration number: %d'%index)
        time.sleep(180)
        

@macro([["motor1", Type.String, None, "Motor to move"],
        ["increment1", Type.Integer, None, "Increment to move"],
        ["motor2", Type.String, None, "Motor to move"],
        ["increment2", Type.Integer, None, "Increment to move"]
        ])
def kbStress(self,motor1, increment1, motor2, increment2):
    #motor1= HPIT hpitPos=20000
    #motor2= HX hxPos=40000
    for i in range(2):
        moveKBHtoLimit(self,0,1,motor1,increment1,motor2,increment2,i)
        moveKBHtoLimit(self,0,-1,motor1,increment1,motor2,increment2,i)
    self.output('Macro finished correctly.')

def moveKBHtoLimit(self,index,inc,motor1,increment1,motor2,increment2,i):
    incr1 = inc*increment1
    incr2 = inc*increment2
    while(index < 7):
        if index < 5: self.execMacro('umvr %s %s %s %s'%(motor1,incr1,motor2,incr2))
        else: self.execMacro('umvr %s %s'%(motor1,incr1))
        index = index + 1
        self.output('Iteration number: %d'%index)
        self.output('Cicle number %d finished.'%i)
        time.sleep(180)

@macro([["motor1", Type.String, None, "Motor to move"],
        ["increment1", Type.Integer, None, "Steps to move in each increment"],
        ["iterations", Type.Integer, None, "Iterations to move"]
        ])
def kbStressOneMotor(self,motor1, increment1, iterations):
    #motor1= HPIT hpitPos=20000
    #motor2= HX hxPos=40000
    for i in range(2):
        moveKBHtoLimitOneMotor(self,0,1,motor1,increment1,iterations,i)
        moveKBHtoLimitOneMotor(self,0,-1,motor1,increment1,iterations,i)
    self.output('Macro has finished correctly.')
def moveKBHtoLimitOneMotor(self,index,direction,motor1,increment1,iterations,i):
    incr1 = direction*increment1
    while(index < iterations):
        self.execMacro('umvr %s %s'%(motor1,incr1))
        index = index + 1
        self.output('Iteration number: %d'%index)
        self.output('Cicle number %d finished.'%i)
        time.sleep(180)
        
    
@macro()
def kbMove2(self):
    index=0
    while(True):
        index = index +1
        self.execMacro('umvr HPIT -20000 HX -40000')
        self.output('Iteration number: %d'%index)
        time.sleep(180)


@macro([["motor1", Type.String, None, "Motor to move"],
        ["increment1", Type.Integer, None, "Increment to move"],
        ["motor2", Type.String, None, "Motor to move"],
        ["increment2", Type.Integer, None, "Increment to move"]
        ])
def kbStress2(self,motor1, increment1, motor2, increment2):
    #motor1= HPIT hpitPos=20000
    #motor2= HX hxPos=40000
    for i in range(2):
        moveKBHtoLimit(self,0,1,motor1,increment1,motor2,increment2)
        moveKBHtoLimit(self,0,-1,motor1,increment1,motor2,increment2)
        self.output('Iteration number %d finished.'%i)
    self.output('Macro finished correctly.')

def moveKBHtoLimit2(self,index,inc,motor1,increment1,motor2,increment2):
    incr1 = inc*increment1
    incr2 = inc*increment2
    while(index < 7):
        if index < 5: self.execMacro('umvr %s %s %s %s'%(motor1,incr1,motor2,incr2))
        else: self.execMacro('umvr %s %s'%(motor1,incr1))
        index = index + 1
        self.output('Iteration number: %d'%index)
        time.sleep(180)
        