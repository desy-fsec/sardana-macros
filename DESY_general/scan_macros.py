"""
    Macro library containning scan related macros
"""

import time

from sardana.macroserver.macro import *


class lup(Macro):
    """Line-up scan:
    Like dscan, a relative motor scan of one motor.    
    """ 

    param_def = [
        ['motor',      Type.Moveable,   "None", 'Moveable to move'],
        ['rel_start_pos',  Type.Float,   -999, 'Scan start position'],
        ['rel_final_pos',  Type.Float,   -999, 'Scan final position'],
        ['nr_interv',  Type.Integer, -999, 'Number of scan intervals'],
        ['integ_time', Type.Float,   -999, 'Integration time']
        ]    

    
    def run(self,motor,rel_start_pos,rel_final_pos,nr_interv,integ_time):

        if ((integ_time != -999)):
            motor_pos = motor.getPosition()
            scan=self.dscan( motor, rel_start_pos, rel_final_pos, nr_interv, integ_time)
        else:
            self.output( "Usage:   lup motor start end intervals time")
          
class timescan(Macro):
    """timescan:
    
    Scan of dummy motor, just reading out the counters   
    """ 

    param_def = [
       ['start_pos',  Type.Float,   -999, 'Scan start position'],
       ['final_pos',  Type.Float,   -999, 'Scan final position'],
       ['nr_interv',  Type.Integer, -999, 'Number of scan intervals'],
       ['integ_time', Type.Float,   -999, 'Integration time']
       ]    

    
    def run(self,start_pos,final_pos,nr_interv,integ_time):
  
        if ((integ_time != -999)):       
            scan=self.ascan( "exp_dmy01", start_pos, final_pos, nr_interv, integ_time)
        else:
            self.output( "Usage:   timescan start stop intervals time")
            


class scan_loop(Macro):

 
    param_def = [
       ['motor',      Type.Moveable,   None, 'Moveable to move'],
       ['start_pos',  Type.Float,   None, 'Scan start position'],
       ['final_pos',  Type.Float,   None, 'Scan final position'],
       ['nr_interv',  Type.Integer, None, 'Number of scan intervals'],
       ['integ_time', Type.Float,   None, 'Integration time'],
       ['nb_loops',   Type.Integer, -1, 'Nb of loops (optional)']
    ]


    def run(self, motor, start_pos, final_pos, nr_interv, integ_time, nb_loops):

        if nb_loops > 0:
            for i in range(0, nb_loops):
              self.execMacro('ascan', motor.getName(), start_pos, final_pos, nr_interv, integ_time)
        else:
            while 1:
                self.execMacro('ascan', motor.getName(), start_pos, final_pos, nr_interv, integ_time)

