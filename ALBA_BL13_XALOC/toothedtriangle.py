import os
import numpy

from sardana.macroserver.macro import *
from sardana.macroserver.scan import *

class ToothedTriangle(Macro):
    """ToothedTriangle macro implemented with the gscan framework.
    It performs nr_cycles cycles, each consisting of two stages: the first half
    of the cycle it behaves like the ascan macro (from start_pos to stop_pos in
    nr_interv+1 steps).For the second half of the cycle it steps back until
    it undoes the first half and is ready for the next cycle.
    At each step, nr_samples acquisitions are performed.
    The total number of points in the scan is nr_interv*2*nr_cycles*nr_samples+1"""

    hints = { 'scan' : 'ToothedTriangle', 'allowsHooks':('pre-move', 'post-move', 'pre-acq', 'post-acq') }
    env = ('ActiveMntGrp',)

    param_def = [
       ['motor',      Type.Motor,   None, 'Motor to move'],
       ['start_pos',  Type.Float,   None, 'start position'],
       ['final_pos',  Type.Float,   None, 'position after half cycle'],
       ['nr_interv',  Type.Integer, None, 'Number of intervals in half cycle'],
       ['integ_time', Type.Float,   None, 'Integration time'],
       ['nr_cycles',  Type.Integer, None, 'Number of cycles'],
       ['nr_samples', Type.Integer, 1 , 'Number of samples at each point']
    ]

    def prepare(self, motor, start_pos, final_pos, nr_interv, integ_time,
                nr_cycles, nr_samples, **opts):
        
        self.start_pos = start_pos
        self.final_pos = final_pos
        self.nr_interv = nr_interv
        self.integ_time = integ_time
        self.nr_cycles = nr_cycles
        self.nr_samples = nr_samples
        self.opts = opts
        cycle_nr_points = self.nr_interv+1 + (self.nr_interv+1)-2
        self.nr_points = cycle_nr_points*nr_samples*nr_cycles+nr_samples
        
        self.interv_size = ( self.final_pos - self.start_pos) / nr_interv
        self.name='ToothedTriangle'
        
        generator=self._generator
        moveables = []
        moveable = MoveableDesc(moveable=motor, is_reference=True,
                                min_value=min(start_pos,final_pos),
                                max_value=max(start_pos,final_pos))
        moveables=[moveable]
        env=opts.get('env',{})
        constrains=[]
        extrainfodesc=[ColumnDesc(name='cycle', dtype='int64', shape=(1,)),
                       ColumnDesc(name='interval', dtype='int64', shape=(1,)),
                       ColumnDesc(name='sample', dtype='int64', shape=(1,))] #!!!
                
        self._gScan=SScan(self, generator, moveables, env, constrains, extrainfodesc) #!!!
  

    def _generator(self):
        step = {}
        step["integ_time"] =  self.integ_time
        step["post-acq-hooks"] = []
        step["post-step-hooks"] = []
        step["check_func"] = []
        extrainfo = {"cycle":None, "interval":None, "sample":None, } 
        step['extrainfo'] = extrainfo
        halfcycle1=range(self.nr_interv+1)
        halfcycle2=halfcycle1[1:-1]
        halfcycle2.reverse()
        intervallist=halfcycle1+halfcycle2
        point_no=0
        for cycle in xrange(self.nr_cycles):
            extrainfo["cycle"] = cycle
            for interval in intervallist:
                extrainfo["interval"] = interval
                step["positions"] = numpy.array([self.start_pos + (interval) * self.interv_size] ,dtype='d')
                for sample in xrange(self.nr_samples):
                    extrainfo["sample"] = sample
                    step["point_id"] = point_no 
                    yield step
                    point_no+=1
                    
        #last step for closing the loop
        extrainfo["interval"] = 0
        step["positions"] = numpy.array([self.start_pos] ,dtype='d')
        for sample in xrange(self.nr_samples):
            extrainfo["sample"] = sample
            step["point_id"] = point_no 
            yield step
            point_no+=1
    
    def run(self,*args):
        for step in self._gScan.step_scan():
            yield step
    
    @property
    def data(self):
        return self._gScan.data
