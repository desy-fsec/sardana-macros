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
from sardana.macroserver.macro import Type, Macro, macro, ParamRepeat, ViewOption, iMacro

import PyTango

import numpy as np

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

class wm_encoder(Macro):
    """ Show motor position from encoder readout """
    
    param_def = [
        ['motor', Type.Moveable, None, 'Motor name']
    ]

    def run(self, motor):
        try:
            motor_td = PyTango.DeviceProxy(motor.TangoDevice)
        except:
            self.output("Not tango device outside Pool")
            return
        try:
            self.table_opts = {}
            self.execMacro('_wm',motor, **self.table_opts)
            encoder_pos = motor_td.PositionEncoder
            self.output("Encoder " + str(encoder_pos))
        except:
            self.output("Not posible to read encoder position")
            
      
        
        
class tw(iMacro):
    """
    tw - tweak motor by variable delta
    """

    param_def = [
        ['motor', Type.Moveable, "test", 'Motor to move'],
        ['delta',   Type.Float, -999, 'amount to tweak']
    ]

    def run(self, motor, delta):
        if delta != -999:
            self.output(
                "Indicate direction with + (or p) or - (or n) or enter")
            self.output(
                "new step size. Type something else (or ctrl-C) to quit.")
            self.output("")
            if np.sign(delta) == -1:
                a = "-"
            if np.sign(delta) == 1:
                a = "+"
            while a in ('+', '-', 'p', 'n'):
                pos = motor.position
                a = self.input("%s = %s, which way? " % (
                    motor, pos), default_value=a, data_type=Type.String)
                try:
                    a1 = float(a)
                    check = "True"
                except:
                    check = "False"

                if a == "p" and np.sign(delta) < 0:
                    a = "+"
                    delta = -delta
                if a == "n" and np.sign(delta) > 0:
                    a = "-"
                    delta = -delta
                if a == "+" and np.sign(delta) < 0:
                    delta = -delta
                if a == "-" and np.sign(delta) > 0:
                    delta = -delta

                if check == "True":
                    delta = float(a1)
                    if np.sign(delta) == -1:
                        a = "-"
                    if np.sign(delta) == 1:
                        a = "+"
                pos += delta
                self.mv(motor, pos)

        else:
            self.output("usage: tw motor delta")

