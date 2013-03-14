#!/usr/bin/env python

"""
Specific Alba BL29 XMCD end station util macros
"""

import PyTango
import time

from sardana.macroserver.macro import Macro, Type


class pot4k_set_refill(Macro):
    """
    4K pot refill mode control macro.

    This macro is used to set the refill mode of the 4K pot of XMCD end station.
    It also allows to optionally sleep for a given time (in seconds) after setting
    the requested mode and also optionally switch the pump to a given final
    value. This final value will be assumed to be Off if not specified and
    sleep_time > 0.0

    Important notes!!!!!
    1) If the macro is stopped or aborted, it will try to switch the pump OFF,
    but this is not guaranteed: you should check pump status in these cases.
    2) Take into account that this is software and hence liable to get hanged:
    this means that the pump will be left in the requested_mode in this case.
    """

    ctrl_dev = 'XMCD/CT/HDI'
    ctrl_attr = 'RelayX'

    modes = { 'Off' : 0, 'On' : 1, 'Auto' : 2 }

    param_def = [
        ['requested_mode', Type.String,   None, 'Mode to set: %s.' % str(modes.keys())],
        ['sleep_time', Type.Float,  0.0, 'Sleep time (in seconds) after setting requested_mode. Default is 0.0 if not specified.'],
        ['final_mode', Type.String,  'Off', 'The pump will be left in this mode after sleep_time expires. If not specified and sleep_time > 0.0, Off is assumed.'],
    ]

    def prepare(self, requested_mode, sleep_time, final_mode, *pairs, **opts):
        """Check that the helium controller is reachable and ready"""
        #check helium controller
        try:
            self.dev = PyTango.DeviceProxy(self.ctrl_dev)
            if self.dev.state() == PyTango.DevState.FAULT:
                msg = 'Helium controller is FAULT'
                self.error(msg)
                raise Exception(msg)
        except:
            msg = 'Unknown error accessing helium controller'
            self.error(msg)
            raise Exception(msg)


    def run(self, requested_mode, sleep_time, final_mode):
        """Set requested mode and check that it is correctly set in the hardware"""

        #check requested mode
        requested_mode = requested_mode.capitalize()
        if not (requested_mode in (self.modes.keys())):
            msg = 'Invalid mode: %s. Valid modes are: %s' % (requested_mode, str(self.modes.keys()))
            self.error(msg)
            raise Exception(msg)

        #write requested mode and check that it was correctly set
        #write also final_mode if requested
        msg = ''
        try:
            #write and check requested mode
            self.output('Switching pump to %s' % requested_mode)
            mode_set = self.modes[requested_mode]
            self.dev.write_attribute(self.ctrl_attr, mode_set)
            mode_got = self.dev.read_attribute(self.ctrl_attr).value
            if (mode_set != mode_got):
                msg = 'Requested mode was not correctly set in the instrument. Please check!'
                self.error(msg)
                raise Exception(msg)

            #wait for sleep_time if requested
            if (sleep_time > 0):
                self.output('Sleeping for %.3f seconds' % sleep_time)
                while (sleep_time > 1):
                    time.sleep(1)
                    if self.isStopped() or self.isAborted():
                        return False
                    sleep_time=sleep_time-1
                time.sleep(sleep_time)

            #leave the pump as requested
            final_mode = final_mode.capitalize()
            if (final_mode != requested_mode):
                #Do not set final mode to off
                if (final_mode == 'Off') and (sleep_time == 0):
                    return True
                self.output('Switching pump to %s' % final_mode)
                mode_final = self.modes[final_mode]
                self.dev.write_attribute(self.ctrl_attr, mode_final)
                mode_got = self.dev.read_attribute(self.ctrl_attr).value
                if (mode_got != mode_final):
                    msg = 'Error switching pump to %s. Please check!' % final_mode
                    self.error(msg)
                    raise Exception(msg)
        except Exception, e:
            if msg == '':
                self.error('Unknown error while trying to set refill mode')
            raise

        return True

    def on_abort(self):
       self.emergency_stop()

    def on_stop(self):
       self.emergency_stop()

    def emergency_stop(self):
        """Switch pump off in case of emergency"""
        self.dev.write_attribute(self.ctrl_attr, self.modes['Off'])
