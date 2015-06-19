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

"""
    Macro library containing an example of an scan macro with a check condition   
"""

__all__ = ["ascan_checkcondition_example"]

__docformat__ = 'restructuredtext'

import os


from sardana.macroserver.macro import *
from sardana.macroserver.scan import *

import sys
sys.path.append("/usr/share/pyshared/sardana/sardana-macros/DESY_general") 
from scan_checkifrepetition import aNscanCheck

class ascan_checkcondition_example(aNscanCheck, Macro): 
    """Do an absolute scan of the specified motor checking a condition for
     repeating points. """

    param_def = [
       ['motor',      Type.Moveable,   None, 'Moveable to move'],
       ['start_pos',  Type.Float,   None, 'Scan start position'],
       ['final_pos',  Type.Float,   None, 'Scan final position'],
       ['nr_interv',  Type.Integer, None, 'Number of scan intervals'],
       ['integ_time', Type.Float,   None, 'Integration time']
    ]

    def prepare(self, motor, start_pos, final_pos, nr_interv, integ_time, 
                **opts):
        self._prepare([motor], [start_pos], [final_pos], nr_interv, integ_time,  **opts)
 
    def check_condition(self):

        check_flag = 0

        # Define here your condition.
        # Set check_flag to 1 if the condition requires repetion of the point

        return check_flag
