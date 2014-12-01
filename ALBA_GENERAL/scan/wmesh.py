##############################################################################
##
## This file is part of Sardana
##
## http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
##
## Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
## 
## Sardana is free software: you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
## 
## Sardana is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
## 
## You should have received a copy of the GNU Lesser General Public License
## along with Sardana.  If not, see <http://www.gnu.org/licenses/>.
##
##############################################################################


from sardana.macroserver.macro import macro, Macro, Type
import datetime as dt


class wmesh(Macro):
    """2d grid scan  .
    The wmesh scan adds a dwell function as a pre-acq hook. This hook waits
    a certain waiting time at each mesh point. This waiting time is corrected
    by the time expended between the post and pre acquisition stages. If this
    expended time (et) is larger than the requested waiting time, the macro skips
    the dwell and raises a warning message.
    """

    param_def = [
       ['motor1',      Type.Moveable,   None, 'First motor to move'],
       ['m1_start_pos',Type.Float,   None, 'Scan start position for first motor'],
       ['m1_final_pos',Type.Float,   None, 'Scan final position for first motor'],
       ['m1_nr_interv',Type.Integer, None, 'Number of scan intervals'],
       ['motor2',      Type.Moveable,   None, 'Second motor to move'],
       ['m2_start_pos',Type.Float,   None, 'Scan start position for second motor'],
       ['m2_final_pos',Type.Float,   None, 'Scan final position for second motor'],
       ['m2_nr_interv',Type.Integer, None, 'Number of scan intervals'],
       ['integ_time',  Type.Float,   None, 'Integration time'],
       ['bidirectional',   Type.Boolean, False, 'Save time by scanning s-shaped'],
       ['waiting_time',Type.Float, None, 'Waiting time beetween post-acq and pre-acq hookplaces']
    ]

    def __init__(self, *args, **kwargs ):
        super(wmesh, self).__init__(*args, **kwargs)
        self.hooks = []
        self.wt = 0
        self.ts_pre_acq = dt.datetime.now()
        self.ts_post_acq = self.ts_pre_acq

    
    def _hook_start_chrono(self):

        self.debug("post-acq hook: _hook_start_chrono")
        self.ts_post_acq = dt.datetime.now()


    def _hook_stop_chrono(self):

        self.debug("pre-acq hook: _hook_stop_chrono")
        tdwell = self.wt
        et = 0.0
        
        self.ts_pre_acq = dt.datetime.now()
        #delta = (self.ts_pre_acq - self.ts_post_acq).total_seconds() #Only python 2.7
        delta = self.ts_pre_acq - self.ts_post_acq
        et = delta.microseconds/float(10**6) + (delta.seconds + delta.days*24*3600)
        self.debug("Elapsed time = %s [s]" % (et))
        tdwell = self.wt - et

        if tdwell < 0:
            self.warning("[warning] negative dwell time (elapsed time = %s), dwell time skipped." % et)
            tdwell = 0.0

        self.debug("waiting time = %s [s]"% (self.wt))
        self.debug("elapsed time = %s [s]" % (et))
        self.debug("dwell time   = %s [s]" % (tdwell))

        self.execMacro("dwell", tdwell)
        self.ts_post_acq = dt.datetime.now()


    def _setHooks(self):

 #       hook_start = (self._hook_start_chrono, ["post-acq"])
        hook_stop = (self._hook_stop_chrono, ["pre-acq"])

#        self.hooks.append(hook_start)
        self.hooks.append(hook_stop)


    def prepare(self, m1, m1_start_pos, m1_final_pos, m1_nr_interv,
                m2, m2_start_pos, m2_final_pos, m2_nr_interv,
                integ_time, bidirectional, waiting_time):

        self.wt = waiting_time
        self.mesh_macro, _ = self.createMacro("mesh",m1, m1_start_pos, m1_final_pos, m1_nr_interv,
                                              m2, m2_start_pos, m2_final_pos, m2_nr_interv,
                                              integ_time, bidirectional)
    
    def run(self, *args):
        
        self._setHooks()
        self.mesh_macro.hooks = self.hooks
        self.runMacro(self.mesh_macro)

