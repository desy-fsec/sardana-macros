import time
from sardana.macroserver.macro import * 
from sardana.util.tree import BranchNode, LeafNode, Tree

class repeat(Hookable, Macro):
    """This macro executes as many repetitions of it's body hook macros as specified by nr parameter.
       If nr parameter has negative value, repetitions will be executed until you stop repeat macro."""

    #hints = { 'allowsHooks': ('body', 'break', 'continue') }
    hints = { 'allowsHooks': ('body',) }
    
    param_def = [
       ['nr', Type.Integer, None, 'Nr of iterations' ]
    ]
    
    def prepare(self, nr):
        #self.breakHooks = self.getHooks("break")
        #self.continueHooks = self.getHooks("continue")
        self.bodyHooks = self.getHooks("body")
    
    def __loop(self):
        self.checkPoint()
        for bodyHook in self.bodyHooks:
            bodyHook()
        
    def run(self, nr):
        if nr < 0:            
            while True: 
                self.__loop()
        else:
            for i in range(nr):
                self.__loop()
                progress = ((i+1)/float(nr))*100
                yield progress
                
class dwell(Macro):
    """This macro waits for a time amount specified by dtime parameter. (python: time.sleep(dtime))"""
    
    param_def = [
       ['dtime', Type.Float, None, 'Dwell time in seconds' ]
    ]
    
    def run(self, dtime):
        while dtime> 0:
            self.checkPoint()
            
            if dtime > 1:
                time.sleep(1)
                dtime = dtime - 1 
            else:
                time.sleep(dtime)
                dtime = 0
                
                
class set_user_pos_pm(Macro):
    """
    This macro set the position of a pseudomotor by changing the offset of its 
    motors. 
    """
    
    param_def =[['pm', Type.PseudoMotor, None, 'Pseudo motor name' ],
                ['pos', Type.Float, None, 'Position which will set']]
    
   
    def set_pos(self, moveable, pos):
        moveable_type = moveable.getType()
        if moveable_type == "PseudoMotor":
            moveables_names = moveable.elements                
            values = moveable.calcphysical(pos)
            sub_moveables = [(self.getMoveable(name), value) \
                             for name, value in zip(moveables_names, values)]
            for sub_moveable, value in sub_moveables:
                self.set_pos(sub_moveable, value)
        elif moveable_type == "Motor":
            m = moveable.getName()
            self.execMacro('set_user_pos %s %f' %(m,pos))
    
    def run(self, pm, pos):
        self.set_pos(pm, pos)
        
    