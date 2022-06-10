# #############################################################################
#
# This file is part of Sardana
#
# http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
#
# Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
#
# Sardana is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sardana is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Sardana.  If not, see <http://www.gnu.org/licenses/>.
#
# #############################################################################

"""
    Macro library containning scan macros reapiting points
    for the macros server Tango device server as part of the Sardana project.

   Available Macros are:
                     ascan_repeat
"""

import copy
import numpy

# from taurus.console import Alignment
# from taurus.console.list import List
# from taurus.console.table import Table

# from sardana.macroserver.msexception import UnknownEnv
from sardana.macroserver.macro import Type, Macro, Hookable
from sardana.macroserver.scan import HScan, SScan, MoveableDesc
from sardana.util.motion import MotionPath
# from sardana.util.motion import Motor, MotionPath
# from sardana.util.tree import BranchNode, LeafNode, Tree


__all__ = ["ascan_repeat", "dscan_repeat", "a2scan_repeat", "a3scan_repeat"]
__docformat__ = 'restructuredtext'

UNCONSTRAINED = "unconstrained"

StepMode = 's'
# TODO: change it to be more verbose e.g. ContinuousSwMode
ContinuousMode = 'c'
ContinuousHwTimeMode = 'ct'
HybridMode = 'h'


def getCallable(repr):
    '''returns a function .
    Ideas: repr could be an URL for a file where the function is contained,
    or be evaluable code, or a pickled function object,...

    In any case, the return from it should be a callable of the form:
    f(x1,x2) where x1, x2 are points in the moveable space and the return value
    of f is True if the movement from x1 to x2 is allowed. False otherwise'''
    if repr == UNCONSTRAINED:
        return lambda x1, x2: True
    else:
        return lambda: None


class aNscanRepeat(Hookable):

    hints = {
        'scan': 'aNscanRepeat',
        'allowsHooks':
        ('pre-scan', 'pre-move', 'post-move', 'pre-acq', 'post-acq',
         'post-step', 'post-scan')
    }
    # env = ('ActiveMntGrp',)

    """N-dimensional scan. This is **not** meant to be called by the user,
    but as a generic base to construct
           ascan_repeat, a2scan_repeat, a3scan_repeat,..."""
    def _prepare(self, motorlist, startlist, endlist, scan_length, integ_time,
                 nb_repeat, mode=StepMode, **opts):

        self.motors = motorlist
        self.starts = numpy.array(startlist, dtype='d')
        self.finals = numpy.array(endlist, dtype='d')
        self.mode = mode
        self.integ_time = integ_time
        self.nb_repeat = nb_repeat
        self.opts = opts
        if len(self.motors) == self.starts.size == self.finals.size:
            self.N = self.finals.size
        else:
            raise ValueError(
                'Moveablelist, startlist and endlist must all be same length')

        moveables = []
        for m, start, final in zip(self.motors, self.starts, self.finals):
            moveables.append(
                MoveableDesc(
                    moveable=m, min_value=min(start, final),
                    max_value=max(start, final)))
        moveables[0].is_reference = True

        env = opts.get('env', {})
        constrains = [
            getCallable(cns)
            for cns in opts.get('constrains', [UNCONSTRAINED])]
        extrainfodesc = opts.get('extrainfodesc', [])

        # Hooks are not always set at this point.
        # We will call getHooks later on in the scan_loop
        # self.pre_scan_hooks = self.getHooks('pre-scan')
        # self.post_scan_hooks = self.getHooks('post-scan'

        if mode == StepMode:
            self.nr_interv = scan_length
            self.nr_points = self.nr_interv+1
            self.interv_sizes = (self.finals - self.starts) / self.nr_interv
            self.name = opts.get('name', 'a%iscan_repeat' % self.N)
            self._gScan = SScan(self, self._stepGenerator, moveables, env,
                                constrains, extrainfodesc)
        elif mode == HybridMode:
            self.nr_interv = scan_length
            self.nr_points = self.nr_interv+1
            self.interv_sizes = (self.finals - self.starts) / self.nr_interv
            self.name = opts.get('name', 'a%iscanh_repeat' % self.N)
            self._gScan = HScan(
                self, self._stepGenerator, moveables, env, constrains,
                extrainfodesc)
        else:
            raise ValueError('invalid value for mode %s' % mode)

    def _stepGenerator(self):
        step = {}
        step["integ_time"] = self.integ_time
        step["pre-move-hooks"] = self.getHooks('pre-move')
        step["post-move-hooks"] = self.getHooks('post-move')
        step["pre-acq-hooks"] = self.getHooks('pre-acq')
        step["post-acq-hooks"] = self.getHooks('post-acq') \
            + self.getHooks('_NOHINTS_')
        step["post-step-hooks"] = self.getHooks('post-step')

        point_id = 0
        for point_no in range(self.nr_points):
            for rep in range(self.nb_repeat):
                step["positions"] = self.starts + point_no * self.interv_sizes
                step["point_id"] = point_id
                point_id = point_id + 1
                yield step

    def run(self, *args):
        for step in self._gScan.step_scan():
            yield step

    @property
    def data(self):
        return self._gScan.data

    def getTimeEstimation(self):
        gScan = self._gScan
        mode = self.mode
        it = gScan.generator()
        v_motors = gScan.get_virtual_motors()
        curr_pos = gScan.motion.readPosition()
        total_time = 0.0
        if mode == StepMode:
            # calculate motion time
            max_step0_time, max_step_time = 0.0, 0.0
            # first motion takes longer, all others should be "equal"
            step0 = next( it)
            for v_motor, start, stop, length in zip(
                    v_motors, curr_pos, step0['positions'], self.interv_sizes):
                path0 = MotionPath(v_motor, start, stop)
                path = MotionPath(v_motor, 0, length)
                max_step0_time = max(max_step0_time, path0.duration)
                max_step_time = max(max_step_time, path.duration)
            motion_time = max_step0_time + self.nr_interv * max_step_time
            # calculate acquisition time
            acq_time = self.nr_points * self.integ_time
            total_time = motion_time + acq_time

        elif mode == ContinuousMode:
            total_time = gScan.waypoint_estimation()
        # TODO: add time estimation for ContinuousHwTimeMode
        return total_time

    def getIntervalEstimation(self):
        mode = self.mode
        if mode == StepMode:
            return self.nr_interv
        elif mode == ContinuousMode:
            return self.nr_waypoints


class dNscanRepeat(aNscanRepeat):
    '''same as aNscan but it interprets the positions as being relative to the
    current positions and upon completion, it returns the motors to their
    original positions'''

    hints = copy.deepcopy(aNscanRepeat.hints)
    hints['scan'] = 'dNscanRepeat'

    def _prepare(self, motorlist, startlist, endlist, scan_length,
                 integ_time, nb_repeat, mode=StepMode, **opts):
        self._motion = self.getMotion([m.getName() for m in motorlist])
        self.originalPositions = numpy.array(self._motion.readPosition())
        starts = numpy.array(startlist, dtype='d') + self.originalPositions
        finals = numpy.array(endlist, dtype='d') + self.originalPositions
        aNscanRepeat._prepare(self, motorlist, starts, finals, scan_length,
                              integ_time,  nb_repeat, mode=mode, **opts)

    def do_restore(self):
        self.info("Returning to start positions... NOT CALLED")
        # self._motion.move(self.originalPositions)

    def on_stop(self):
        self.info("Returning to start positions...in ONSTOP")
        self._motion.move(self.originalPositions)


class ascan_repeat(aNscanRepeat, Macro):
    """Do an absolute scan of the specified motor.
    ascan scans one motor, as specified by motor. The motor starts at the
    position given by start_pos and ends at the position given by final_pos.
    The step size is (start_pos-final_pos)/nr_interv.
    The number of data points collected
    will be nr_interv+1. Count time is given by time which if positive,
    specifies seconds and if negative, specifies monitor counts. """

    param_def = [
       ['motor',      Type.Moveable,   None, 'Moveable to move'],
       ['start_pos', Type.Float,   None, 'Scan start position'],
       ['final_pos', Type.Float,   None, 'Scan final position'],
       ['nr_interv', Type.Integer, None, 'Number of scan intervals'],
       ['integ_time', Type.Float,   None, 'Integration time'],
       ['nb_repeat', Type.Integer, None, 'Number of repetitions per point']
    ]

    def prepare(self, motor, start_pos, final_pos, nr_interv, integ_time,
                nb_repeat,
                **opts):
        self._prepare(
            [motor], [start_pos], [final_pos], nr_interv,
            integ_time, nb_repeat,  **opts)


class a2scan_repeat(aNscanRepeat, Macro):
    """two-motor scan.
    a2scan scans two motors, as specified by motor1 and motor2.
    Each motor moves the same number of intervals with starting and ending
    positions given by start_pos1 and final_pos1, start_pos2 and final_pos2,
    respectively.
    The step size for each motor is (start_pos-final_pos)/nr_interv.
    The number of data points collected will be nr_interv+1.
    Count time is given by time which if positive, specifies seconds and
    if negative, specifies monitor counts."""
    param_def = [
       ['motor1',      Type.Moveable,   None, 'Moveable 1 to move'],
       ['start_pos1', Type.Float,   None, 'Scan start position 1'],
       ['final_pos1', Type.Float,   None, 'Scan final position 1'],
       ['motor2',      Type.Moveable,   None, 'Moveable 2 to move'],
       ['start_pos2', Type.Float,   None, 'Scan start position 2'],
       ['final_pos2', Type.Float,   None, 'Scan final position 2'],
       ['nr_interv', Type.Integer, None, 'Number of scan intervals'],
       ['integ_time', Type.Float,   None, 'Integration time'],
       ['nb_repeat', Type.Integer, None, 'Number of repetitions per point']
    ]

    def prepare(self, motor1, start_pos1, final_pos1, motor2, start_pos2,
                final_pos2, nr_interv, integ_time, nb_repeat,
                **opts):
        self._prepare(
            [motor1, motor2],
            [start_pos1, start_pos2],
            [final_pos1, final_pos2],
            nr_interv, integ_time, nb_repeat, **opts)


class a3scan_repeat(aNscanRepeat, Macro):
    """three-motor scan .
    a3scan scans three motors, as specified by motor1, motor2 and motor3.
    Each motor moves the same number of intervals with starting and ending
    positions given by start_pos1 and final_pos1, start_pos2 and final_pos2,
    start_pos3 and final_pos3, respectively.
    The step size for each motor is (start_pos-final_pos)/nr_interv.
    The number of data points collected will be nr_interv+1.
    Count time is given by time which if positive, specifies seconds and
    if negative, specifies monitor counts."""
    param_def = [
       ['motor1', Type.Moveable, None, 'Moveable 1 to move'],
       ['start_pos1', Type.Float, None, 'Scan start position 1'],
       ['final_pos1', Type.Float, None, 'Scan final position 1'],
       ['motor2', Type.Moveable, None, 'Moveable 2 to move'],
       ['start_pos2', Type.Float, None, 'Scan start position 2'],
       ['final_pos2', Type.Float, None, 'Scan final position 2'],
       ['motor3', Type.Moveable, None, 'Moveable 3 to move'],
       ['start_pos3', Type.Float, None, 'Scan start position 3'],
       ['final_pos3', Type.Float, None, 'Scan final position 3'],
       ['nr_interv', Type.Integer, None, 'Number of scan intervals'],
       ['integ_time', Type.Float, None, 'Integration time'],
       ['nb_repeat', Type.Integer, None, 'Number of repetitions per point']
    ]

    def prepare(self, m1, s1, f1,  m2, s2, f2, m3, s3, f3, nr_interv,
                integ_time, nb_repeat, **opts):
        self._prepare([m1, m2, m3], [s1, s2, s3], [f1, f2, f3], nr_interv,
                      integ_time, nb_repeat, **opts)


class dscan_repeat(dNscanRepeat, Macro):
    """motor scan relative to the starting position.
    dscan scans one motor, as specified by motor. If motor motor is at a
    position X before the scan begins, it will be scanned from X+start_pos
    to X+final_pos. The step size is (start_pos-final_pos)/nr_interv.
    The number of data points collected will be nr_interv+1. Count time is
    given by time which if positive, specifies seconds and if negative,
    specifies monitor counts. """

    param_def = [
       ['motor', Type.Moveable, None, 'Moveable to move'],
       ['start_pos', Type.Float, None, 'Scan start position'],
       ['final_pos', Type.Float, None, 'Scan final position'],
       ['nr_interv', Type.Integer, None, 'Number of scan intervals'],
       ['integ_time', Type.Float, None, 'Integration time'],
       ['nb_repeat', Type.Integer, None, 'Number of repetitions per point']
    ]

    def prepare(self, motor, start_pos, final_pos, nr_interv, integ_time,
                nb_repeat, **opts):
        self._prepare([motor], [start_pos], [final_pos], nr_interv,
                      integ_time,  nb_repeat, **opts)
