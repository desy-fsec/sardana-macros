import time
from sardana.macroserver.macro import Macro, Type
from taurus import Device
from pyIcePAP import EthIcePAP
import PyTango

DEV_STATE_ALARM = PyTango._PyTango.DevState.ALARM
DEV_STATE_MOVING = PyTango._PyTango.DevState.MOVING
DEV_STATE_ON = PyTango._PyTango.DevState.ON
IPAP_TIMEOUT = 1
NR_STEPS = 1000

class smaract_sdc_homing(Macro):
    """
    Macro to do a homing of the smaract controller. It executes a find
    reference command in the smaract device server and set the register of the
    icepap controller to synchronize them.

    The macro uses three environment variables: Direction (forward/backward),
    NrSteps (number of steps to touch the limit) and MaxError (maximum error
    of the position after the homing)
    """

    param_def = [['motor', Type.Motor, None, 'smaract motor'],
                 ['positive_limit', Type.Boolean, True, ('move to the '
                                                         'positive limit')]]

    def _wait(self):
        time.sleep(0.2)
        self.checkPoint()

    def run(self, motor, positive_limit):
        encoder_source = motor.encodersource
        dev_name, attr = encoder_source.rsplit('/', 1)
        if attr.lower() != 'position':
            msg = ('The motor should have the encoder source connected to the '
                   'device server of the smaract')
            raise ValueError(msg)

        # Move the motor to the limit
        nr_steps = NR_STEPS
        direction = 'backward'
        if not positive_limit:
            nr_steps = -1 * NR_STEPS
            direction = 'forward'

        self.info('Moving to the limit')
        while motor.read_attribute('State').value != DEV_STATE_ALARM:
            current_pos = motor.read_attribute('Position').value
            next_pos = current_pos + nr_steps
            motor.write_attribute('Position', next_pos)
            while motor.read_attribute('State').value == DEV_STATE_MOVING:
                self._wait()

        # Find the reference mark
        self.info('Finding reference mark in the smaract')
        dev = Device(dev_name)
        dev.write_attribute('SafeDirection', direction)
        dev.command_inout('FindReferenceMark')
        while motor.read_attribute('State').value != DEV_STATE_ON:
            self._wait()

        pos = int(motor.read_attribute('Position').value)

        # Set the icepap indexer
        self.info('Setting the icepap indexer')
        ctrl_name = motor.getControllerName()
        ctrl = Device(ctrl_name)
        properties = ctrl.get_property(['Host', 'Port'])
        ipap_port = properties['Port'][0]
        ipap_host = properties['Host'][0]
        motor_axis = motor.getAxis()

        ipap = EthIcePAP(ipap_host, ipap_port, IPAP_TIMEOUT)
        ipap.setEncoder(motor_axis, pos)
        set_pos = self.createMacro('set_user_pos', motor, 0)
        self.runMacro(set_pos)

# util functions
def isSmaractMCSMotor(macro, motor):
    '''Checks if pool motor belongs to the SmaractMCSController'''

    controllers = macro.getControllers()
    ctrl_name = motor.controller
    controller_obj = controllers[ctrl_name]
    return isSmaractMCSController(macro, controller_obj)

def isSmaractMCSController(macro, controller):
    '''Checks if pool controller is of type SmaractMCSController'''

    if isinstance(controller, str):
        controller_name = controller
        controllers = macro.getControllers()
        controller_obj = controllers[controller_name]
    else:
        controller_obj = controller
    controller_class_name = controller_obj.getClassName()
    if controller_class_name != "SmaractMCSController":
        return False
    return True



class smaract_mcs_homing(Macro):
    """
    Macro to do a homing of the smaract MCS controller. It executes a find
    reference command in the smaract device server and sets the upper and lower
    limits of the controller according to the last values stored in the tango
    database. The values for the limits are accessed via the PySmaractDS.

    """

    param_def = [['motor', Type.Motor, None, 'smaract motor'],
                 ['direction', Type.String, None, 'search direction: {forward, backward}' ]]

    def run(self, motor, direction):

        if direction == 'forward':
            self.direction = 0
        elif direction == 'backward':
            self.direction = 1
        else:
            raise Exception('Invalid direction. Possible values are: {forward, backward}')

        # Check if motor is an axis of a smaract MCS controller
        if not isSmaractMCSMotor(self, motor):
            raise Exception('This is not a valid MCS Smaract motor controller.')

        self.debug('motor; %s' % repr(motor))

        # Get axis number:
        self.debug('axis %s' % motor.axis)

        # Get the pool and controller objects
        pool = motor.getPoolObj()
        ctrlName = motor.getControllerName()
        self.debug('Pool: %s, Controller: %s' % (repr(pool), ctrlName))

        # Sent a homming command to controller from pool:
        # The HM_CMD are defined in the Smaract MCS controller
        HM_CMD = 'home_linial_single: %s %s' % (motor.axis, self.direction)
        ans = pool.SendToController([ctrlName , HM_CMD])

        if ans == "READY":
            self.info(ans)
        else:
            self.error(ans)





