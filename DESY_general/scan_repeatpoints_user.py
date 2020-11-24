# #############################################################################
# #
# # This file is part of Sardana
# #
# # http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
# #
# # Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
# #
# # Sardana is free software: you can redistribute it and/or modify
# # it under the terms of the GNU Lesser General Public License as published by
# # the Free Software Foundation, either version 3 of the License, or
# # (at your option) any later version.
# #
# # Sardana is distributed in the hope that it will be useful,
# # but WITHOUT ANY WARRANTY; without even the implied warranty of
# # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# # GNU Lesser General Public License for more details.
# #
# # You should have received a copy of the GNU Lesser General Public License
# # along with Sardana.  If not, see <http://www.gnu.org/licenses/>.
# #
# #############################################################################

"""
    Macro library containning user macros using  the scan_repeat macro.

   Available Macros are:
                     ascan_repeat_example
"""

# import os
# import copy
# import datetime

# import numpy


# from sardana.macroserver.msexception import UnknownEnv
from sardana.macroserver.macro import Type, Macro
# from sardana.macroserver.scan import *
# from sardana.util.motion import Motor, MotionPath


__all__ = ["ascan_repeat_example"]

__docformat__ = 'restructuredtext'

rep_counter = 0


class HookPars:
    pass


def hook_pre_acq(self, hook_pars):
    global rep_counter

    self.output(str(rep_counter))
    # Implement actions depending on the rep_counter value:
    #    0 -> first time of this position, 1 -> second time ...

    if rep_counter < (hook_pars.nb_repeat - 1):
        rep_counter = rep_counter + 1
    else:
        rep_counter = 0


class ascan_repeat_example(Macro):

    param_def = [
       ['motor',      Type.Moveable,   None, 'Moveable to move'],
       ['start_pos', Type.Float,   None, 'Scan start position'],
       ['final_pos', Type.Float,   None, 'Scan final position'],
       ['nr_interv', Type.Integer, None, 'Number of scan intervals'],
       ['integ_time', Type.Float,   None, 'Integration time'],
       ['nb_repeat', Type.Integer, None, 'Number of repetitions per point']
    ]

    def run(self, motor, start_pos, final_pos, nr_interv, integ_time,
            nb_repeat):

        macro, pars = self.createMacro(
            'ascan_repeat', motor, start_pos,
            final_pos, nr_interv, integ_time, nb_repeat)

        # parameters for scan hook function
        hook_pars = HookPars()
        hook_pars.nb_repeat = nb_repeat

        def f():
            return hook_pre_acq(self, hook_pars)

        macro.hooks = [
            (f, ["pre-acq"]),
        ]

        self.runMacro(macro)
