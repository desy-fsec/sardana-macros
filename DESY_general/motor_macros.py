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

"""Additional macros for motors"""


__all__ = ["wg"]

__docformat__ = 'restructuredtext'


import datetime
from sardana.macroserver.macro import Type, Macro, macro, ParamRepeat, ViewOption
import PyTango

class wg(Macro):
    """Show motor positions of a list of motors"""

    param_def = [
        ['motors',
            ParamRepeat(['motor', Type.Moveable, None, 'motor']),
            None, 'List of motors'],
        ]

    def prepare(self, *motors, **opts):
        self.all_motors = motors[0:]
        self.table_opts = {}
    
    def run(self, *motors):
        nr_motors = len(self.all_motors)
        if nr_motors == 0:
            self.output('No motor defined')
            return
        
        show_dial = self.getViewOption(ViewOption.ShowDial)
        if show_dial:
            self.output('Current positions (user, dial) on %s'%datetime.datetime.now().isoformat(' '))
        else:
            self.output('Current positions (user) on %s'%datetime.datetime.now().isoformat(' '))
        self.output('')
        
        self.execMacro('_wm',*self.all_motors, **self.table_opts)
