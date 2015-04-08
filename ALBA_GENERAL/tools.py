import time
from sardana.macroserver.macro import * 
from sardana.util.tree import BranchNode, LeafNode, Tree
import taurus

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

class PSHU(object):
    OPEN_VALUE = 1
    CLOSE_VALUE = 0 
    def initPSHU(self):
        try:
            sh_attr_name = self.getEnv('PSHU_ATTR')
            self.attr = taurus.Attribute(sh_attr_name)

        except Exception, e:
            msg = ('The macro use the enviroment variable PSHU_ATTR which has '
                   'the attribute name of the EPS to open the shutter.\n%s' % e)
            raise RuntimeError(msg)
    
    @property
    def state(self):
        return self.attr.read().value
    
    def _writeValue(self, value):
        self.attr.write(value)
        while self.state != value:
            time.sleep(0.1)
            self.checkPoint()
            
    def open(self):
        if self.state:
            self.info('The photon shutter was open')
            return
        self.info('Opening photon shutter...')
        self._writeValue(self.OPEN_VALUE)
        self.info('The photon shutter is open')
 
    def close(self):
        if not self.state:
            self.info('The photon shutter was closed')
            return
        self.info('Closing photon shutter...')
        self._writeValue(self.CLOSE_VALUE)
        self.info('The photon shutter is closed')
 
    
class shopen(Macro, PSHU):
    """
    This macro open the photon shutter. 
    
    Other macros: shclose, shstate
    """
    def run(self):
        self.initPSHU()
        self.open()
    
class shclose(Macro, PSHU):
    """
    This macro close the photon shutter. 
    
    Other macros: shopen, shstate
    """
    def run(self):
        self.initPSHU()
        self.close()

class shstate(Macro, PSHU):
    """
    This macro show the photon shutter state. 
    
    Other macros: shopen, shclose
    """
    def run(self):
        self.initPSHU()
        state = self.state
        st_msg = 'closed'
        if state == self.OPEN_VALUE:
            st_msg = 'open'
            
        self.info('The photon shutter is ' + st_msg)
        