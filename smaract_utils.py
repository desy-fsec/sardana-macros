import time
from sardana.macroserver.macro import Macro, Type
from taurus import Device
import PyTango

DEV_STATE_ALARM = PyTango._PyTango.DevState.ALARM
DEV_STATE_ON = PyTango._PyTango.DevState.ON

class smaract_homming(Macro):
    """
    Macro to do a homing of the smaract controller. It executes a find
    reference command in the smaract device server and set the register of the
    icepap controller to synchronize them.

    The macro uses three environment variables: Direction (forward/backward),
    NrSteps (number of steps to touch the limit) and MaxError (maximum error
    of the position after the homing)
    """

    param_def = [['motor', Type.Motor, None, 'smaract motor']]

    def _wait(self):
        time.sleep(0.2)
        self.checkPoint()

    def run(self, motor):
        encoder_source = motor.encodersource
        dev_name, attr = encoder_source.rsplit('/', 1)
        if attr.lower() != 'position':
            msg = ('The motor should have the encoder source connected to the '
                   'device server of the smaract')
            raise ValueError(msg)

        direction = self.getEnv('Direction')
        nr_steps = self.getEnv('NrSteps')
        max_error = self.getEnv('MaxError')

        # Move the motor to the limit
        motor.write_attribute('Position', nr_steps)
        while motor.read_attribute('State').value != DEV_STATE_ALARM:
            self._wait()

        # Find the reference mark
        dev = Device(dev_name)
        dev.write_attribute('SafeDirection', direction)
        dev.command_inout('FindReferenceMark')
        while motor.read_attribute('State').value != DEV_STATE_ON:
            self._wait()

        pos = abs(motor.read_attribute('Position').value)
        if pos >= max_error:
            raise RuntimeError('The homing failed!!. You should do it by hand')

