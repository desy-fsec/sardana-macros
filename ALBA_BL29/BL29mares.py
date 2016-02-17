#!/usr/bin/env python

"""
Specific Alba BL29 MARES (RSXS end station) utility macros
"""


__all__=['femto', 'mvsdc']


import PyTango
import time

from sardana.macroserver.macro import Macro, Type


class femto(Macro):
    """
    Macro to get/set the femto gain value

    For GETTING the gain value simply run the macro without parameters

    For SETTING the gain value run the macro with the target gain value. These values
    can range from 4 (which means 1e4) to 13 (which means 1e13): any other value
    will simply be ignored by the hardware.
    The macro will check that the set value had been correctly written in the
    hardware for some time and will show an error message if target value is not
    correctly set in the hardware after that time
    On success, the macro will return the target gain value. On failure it will
    return 0 
    """

    RANGE = range(4,13+1)
    ATTRIBUTE_NAME = 'BL29/CT/EPS-PLC-01/EX_AMP_EH02_01_GAIN_A'
    TIMEOUT = 15

    param_def = [
        ['gain', Type.Integer, 0, 'Gain to set (4..13: meaning 1e4..1e13)']
    ]

    def prepare(self, gain, *args, **kwargs):
        if (gain != 0) and not (gain in self.RANGE):
            self.error('Invalid gain: %d. Valid values are %s. Set value will be ignored by the hardware.' %(gain, str(self.RANGE)))

    def run(self, gain, *args, **kwargs):
        attr = PyTango.AttributeProxy(self.ATTRIBUTE_NAME)
        if gain in self.RANGE:
            self.output('Setting gain value...')
            attr.write(gain)
            self.output('Checking gain value...')
            gain_now = attr.read().value
            start = time.time()
            timeout = False
            while gain_now!=gain and not timeout:
                time.sleep(0.2)
                gain_now = attr.read().value
                if time.time() - start > self.TIMEOUT:
                    timeout = True
            if timeout:
                self.error('Timeout while checking if value was correctly set to hardware')
            if gain_now!=gain:
                self.error('Gain read from hardware %d is not the target value %d. Please check!' % (gain_now, gain))
        elif gain==0:
            gain_now = attr.read().value
            self.output('Femto gain %d' % gain_now)
            return gain_now
        else:
            return 0


class mvsdc(Macro):
    """
    Simple macro for moving a smaract SDC controller
    """

    BAUDRATE = 115200
    LF = 0xA
    VOLTAGE = 4090
    FREQUENCY = 200
    RC_OK = ':E0,0'

    param_def = [
        ['axis',     Type.Integer, None, 'axis to move (0 is special command to set tty port)'],
        ['position', Type.Integer, None, 'position (if axis parameter is 0 then this is the axis id to which to set serial device name )'],
        ['port',     Type.String,  '',   'optional (for configuration only) if axis is 0 then this is the serial device name to communicate to with the given axis '],
    ]

    def run(self, axis, position, port, *args, **kwargs):
        #prepare environment
        env_prefix = 'Macros.%s.' % self.__class__.__name__
        environment = self.getGlobalEnv()

        try:
            axes = environment['%s%s' % (env_prefix, 'axes')]
        except KeyError, e:
            axes = {}
        except Exception, e:
            self.error('Unexpected exception while getting environment: %s' % str(e))
            raise

        if axis==0:
            axis_env = int(position)
            if axis_env <= 0:
                self.error('environment axis id must be >0')
                return
            axes[axis_env] = port
            self.output('Setting environment: %s' % str(axes))
            self.setEnv('%s%s' % (env_prefix, 'axes'), axes)
            return -1

        #check if axis is defined in environment
        try:
            serial_name = axes[axis]
        except KeyError, e:
            self.error('Axis %s does not exist' % str(axis))
            return -1

        #check if axis is accessible
        try:
            serial = PyTango.DeviceProxy(serial_name)
            serial.command_inout('DevSerFlush',2)
            #read version just to check that we can communicate with the SDC
            serial.command_inout('DevSerWriteString',':GIV')
            serial.command_inout('DevSerWriteChar',[self.LF])
            version = serial.command_inout('DevSerReadLine')
            if len(version) == 0:
                raise Exception('Unable to read version number')
        except Exception, e:
            self.error('Unable to communicate with SDC controller')
            return -1

        #move motor
        try:
            cmd = ':MST0,%d,%d,%d' % (position, self.VOLTAGE, self.FREQUENCY)
            serial.command_inout('DevSerWriteString',cmd)
            serial.command_inout('DevSerWriteChar',[self.LF])
            rc = serial.command_inout('DevSerReadLine')
            if rc.strip() != self.RC_OK:
                self.error('SDC return code (expected 0): %d' % self.RC_OK)
                return -1
        except Exception, e:
            self.error('Error while executing move command in SDC: %s' % str(e))
            return -1

        return 0
