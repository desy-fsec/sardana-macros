import time
from sardana.macroserver.macro import Macro, Type
from taurus import Device
from pyIcePAP import EthIcePAP
import PyTango

DEV_STATE_ALARM = PyTango.DevState.ALARM
DEV_STATE_MOVING = PyTango.DevState.MOVING
DEV_STATE_ON = PyTango.DevState.ON
IPAP_TIMEOUT = 1
NR_STEPS = 1000

SEQUENCE = { "forward": 0,
             "backward": 1}

class homing_sdc_test1(Macro):
    """
    Category: Configuration

    This macro performs a homing of a given SDC smaract motor controller acting
    as slave of an IcePAP driver. The hardware access is performed via Tango DS
    (smaractds).

    The homing procedure includes different stages:

        1.- Move the physical motor to one of the limit switches defined in the
        system (by default, the negative limit). Once the limit switch is,
        reached the smaract controller command FindReferenceMark is executed.
        This will find for the reference mark according to the searching
        sequence requested. Check that the FRM command has let a
        PhysicalPositionKnown flag set to True.

        2.- At this point, we can restore the previous Sardana parameters:
            .- offset.
            .- software limits.

    """

    param_def = [['motor', Type.Motor, None, 'smaract sdc motor'],
                 ['direction', Type.String, "forward", 'forward/backward'],
                 ['search_sequence', Type.String, "forward", 'searching sequence'],
                 ['rate', Type.Float, 0.5, 'Rate for homing velocity'],
                ]

    def _wait(self):
        time.sleep(0.2)
        self.checkPoint()

    def run(self, motor, direction, search_sequence, rate):

	# Initialize parameters
        direction = str(direction).lower()
        motion = self.getMotion([motor])
        rate = float(rate)

        # Get sardana motor configuration:
        # encoder_source, device_name, attribute name, software limits
        # offset, velocity and sign
        encoder_source = motor.encodersource
        dev_name, attr = encoder_source.rsplit('/', 1)
        if attr.lower() != 'position':
            msg = ('The motor should have the encoder source connected to the '
                   'device server of the smaract')
            raise ValueError(msg)
        pos_cfg = motor.get_attribute_config(attr)
        min_pos = pos_cfg.min_value
        max_pos = pos_cfg.max_value

        offset = float(motor.offset)
        velocity = float(motor.velocity)
        sign = int(motor.sign)
        
        info_msg = 'Motor %s accessed via %s\n' % (motor, dev_name) 
        info_msg += 'Software limits = [%s, %s]\n' % (min_pos, max_pos)
        info_msg += 'Velocity = %s\n' % velocity
        info_msg += 'Sign = %s' % sign
        self.info(info_msg)
        
        # Unset software limits
        pos_cfg.min_value = 'Not specified'
        pos_cfg.max_value = 'Not specified'
	motor.set_attribute_config(pos_cfg)
        self.info('Unsetting software limits [%s, %s]...' % (min_pos, max_pos))

        # Move the motor to the requested limit
        # [home, upper, lower]
        if direction == "forward":
            limit = -1
        elif direction == "backward":
            limit = 1

        # Searching the hardware limit by small incremental movements.
        # Position increment = 1 second at rate(%) velocity
        self.info(type(sign))
        self.info(type(velocity))
        self.info(type(rate))
        delta = sign*velocity*rate
        while not motor.limit_switches[limit]:
            new_pos = motor.position + limit*delta
            motion.move(new_pos)
            self.debug(motor.position)
            self._wait()

        # Find the guide reference mark
        self.info('Finding reference mark in the smaract')
        smaract_ds = Device(dev_name)
        smaract_ds.SetSafeDirection([0, SEQUENCE[search_sequence]])
        # This will also set the smaract position to 0
        smaract_ds.FindReferenceMark(0)
        #while motor.read_attribute('State').value != DEV_STATE_ON:
        while smaract_ds.GetStatus(0) != "Holding":
            self._wait()

#        pos = int(motor.read_attribute('Position').value)

        # Set the icepap indexer to 0
        self.info('Setting the icepap indexer and encoder registers to 0')
        ctrl_name = motor.getControllerName()
        ctrl = Device(ctrl_name)
        properties = ctrl.get_property(['Host', 'Port'])
        ipap_port = properties['Port'][0]
        ipap_host = properties['Host'][0]
        motor_axis = motor.getAxis()
        self.info('Connecting to icepap %s on port %s' % (ipap_host, ipap_port))
        ipap = EthIcePAP(ipap_host, ipap_port, IPAP_TIMEOUT)
        time.sleep(1)
        ipap.setPosition(motor_axis, 0)
        # Applying previous offset
        self.info('Reseting user position...')
        self.execMacro('set_user_pos %s %s' %  (motor, -offset))
        self.info('Restoring original offset %d' % offset)
        motor.offset = offset

        self.info('Restoring original software limits [%s, %s]...' % (min_pos, max_pos))
        pos_cfg.min_value = min_pos
        pos_cfg.max_value = max_pos
	motor.set_attribute_config(pos_cfg)

