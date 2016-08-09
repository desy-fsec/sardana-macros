#!/usr/bin/env python

"""
Specific Alba BL29 MARES (RSXS end station) utility macros
"""

import PyTango

from sardana.macroserver.macro import Macro, Type, ParamRepeat

__all__ = ['mares_sample_temp_control']


class mares_sample_temp_control(Macro):
    """
    Macro for setting/getting MARES sample temperature control parameters.

    This macro is used to set or get all the parameters for controlling the
    MARES end station sample temperature.

    For GETTING the parameters, provide the macro with pairs consisting in the
    string get + param_name. You can also simply provide 'get all' and all the
    parameters will be retrieved. For example:
        mares_sample_temp_control get setpoint
        mares_sample_temp_control get all

    For SETTING the parameters, these are passed as pairs consisting on
    param_name + param_value. For example, to set the temperature setpoint, you
    can use:
        mares_sample_temp_control setpoint 33.3

    The parameter names and their possible values are:
    - state -> The hardware controller state. Please note that only 2 states
    are availabe when setting the value:
        * on
        * off
    - setpoint -> the value is a float number
    - control_type -> possible values are (upper/lower case is ignored):
        * Off
        * Manual
        * PID
        * Table
        * RampWithTable
        * RampWithPID
    - range -> possible values are (upper/lower case is ignored):
        * Low
        * Mid
        * Hi
    - rate -> the value is a float number: this is the ramp rate that will be
    used to go to setpoint temperature. NOTE that this parameter is ONLY used
    when control_type is set to RampWithTable or RampWithPID

    ************ IMPORTANT NOTES!!! PLEASE READ CAREFULLY!!! ************

    1) Note that setpoint parameter may mean 2 different things:
        a) Output power if controller is in manual mode
        b) Temperature target in K in any other case

    2) Hence, in order to avoid possible errors, if you want to set output
    power manually you have to explicitly specify that you want to set the
    controller to manual mode (even if it is already in that mode). Otherwise,
    the setpoint parameter will be assumed to be a temperature setpoint, and
    hence the macro will check that the controller IS NOT in manual mode, and
    will complain if it is.

    3) Note that setting the state (hardware controller state) to 'off' will
    completely disable the hardware equipment, and hence it will not regulate
    temperature or power at all.
    """

    param_def = [
        ['name_value',
         ParamRepeat(['param_name',  Type.String, None, 'parameter name'],
                     ['param_value', Type.String, None, 'parameter value']),
         None, 'List of tuples: (param_name, param_value)']
    ]

#    @todo: replace DEPRECATED old style when bug solved:
#    https://sourceforge.net/p/sardana/tickets/65/
#    @todo: see new style param repeat
#    http://www.sardana-controls.org/en/stable/devel/howto_macros/\
#    macros_general.html#repeat-parameters
#    param_def = [
#        [ 'param_value', [
#             [ 'param_name',  Type.String, None, 'parameter name' ],
#             [ 'param_value', Type.String, None, 'parameter value'],
#               { 'min' : 1, 'max' : 4 } ],
#         None, 'List of param_name/param_value pairs']
#    ]

    ctrl_dev = 'MARES/CT/TC'
    ctrl_attr_output = 'Loop1Output'
    ctrl_attr_range = 'Loop1Range'
    ctrl_attr_rate = 'Loop1Rate'
    ctrl_attr_setpoint = 'Loop1SetPoint'
    ctrl_attr_type = 'Loop1Type'
    ctrl_attr_state = 'State'

    control_types = ['Off', 'PID', 'Manual', 'Table',
                     'RampWithPID', 'RampWithTable']
    ranges = ['Low', 'Mid', 'Hi']

    control_types_hw = ['off', 'pid', 'man', 'table', 'rampp', 'rampt']

    data = {
        'setpoint':     None,
        'control_type': None,
        'range':        None,
        'rate':         None,
        'state':        None
    }

    allowed_commands = ('on', 'off')

    def to_usr(self, value):
        """"""
        value = value.lower()
        if value in self.control_types_hw:
            return self.control_types[self.control_types_hw.index(value)]
        else:
            return None

    def to_hw(self, value):
        """"""
        control_types = [type.lower() for type in self.control_types]
        value = value.lower()
        if value in control_types:
            return self.control_types_hw[control_types.index(value)]
        else:
            return None

    def extract_and_check_params(self, pairs):
        """"""

        hw_params = []
        # check parameters if provided
        self.data = {
            'setpoint':     None,
            'control_type': None,
            'range':        None,
            'rate':         None,
            'state':        None,
        }
        control_types = [type.lower() for type in self.control_types]
        ranges = [range.lower() for range in self.ranges]
        for param_name, param_value in pairs:
            param_value = param_value.lower()
            # check param name
            if not (param_name in self.data.keys()):
                msg = 'Invalid parameter %s. Valid parameters are: %s' % \
                      (str(param_name), str(self.data.keys()))
                self.output(msg)
                raise Exception(msg)
            # check param value
            if param_name == 'setpoint':
                self.data[param_name] = param_value
            elif param_name == 'control_type':
                if not (param_value in control_types):
                    msg = 'Invalid parameter control_type: %s Valid values ' \
                          'are %s' % (param_value, str(self.control_types))
                    self.output(msg)
                    raise Exception(msg)
                self.data[param_name] = param_value
            elif param_name == 'range':
                if not (param_value in ranges):
                    msg = 'Invalid parameter range: %s Valid values are %s' % \
                          (param_value, str(self.ranges))
                    self.output(msg)
                    raise Exception(msg)
                self.data[param_name] = param_value
            elif param_name == 'rate':
                self.data[param_name] = param_value
            elif param_name == 'state':
                if not (param_value in self.allowed_commands):
                    msg = 'Invalid parameter state: %s Valid values are %s' % \
                          (param_value, str(self.allowed_commands))
                    self.output(msg)
                    raise Exception(msg)
                self.data[param_name] = param_value
            else:
                msg = 'Unknown parameter: %s' % str(param_name)
                self.output(msg)
                raise Exception(msg)

        # and finally check logic between parameters and translate them to hw
        # NOTE that the order in which the ha params are appended to the list
        # are important in case of setting temperature/manual_value
        setpoint = self.data['setpoint']
        control_type = self.data['control_type']
        range = self.data['range']
        rate = self.data['rate']
        state = self.data['state']
        if control_type is not None:
            hw_params.append([self.ctrl_attr_type, self.to_hw(control_type)])
        if range is not None:
            hw_params.append([self.ctrl_attr_range, range])
        if rate is not None:
            hw_params.append([self.ctrl_attr_rate, float(rate)])
        if setpoint is not None:
            if control_type is None:
                actual_control_type = \
                    self.dev.read_attribute(self.ctrl_attr_type).value
                actual_control_type = actual_control_type.lower()
                if actual_control_type == 'man':
                    msg = 'You requested setting a temperature target, but '\
                        'the controller is in manual mode'
                    self.output(msg)
                    raise Exception(msg)
                hw_params.append([self.ctrl_attr_setpoint, float(setpoint)])
            elif control_type == 'manual':
                hw_params.append([self.ctrl_attr_output, float(setpoint)])
            else:
                hw_params.append([self.ctrl_attr_setpoint, float(setpoint)])
        # special treament for 'state'
        if state is not None:
            hw_params.append(['state', state])

        return hw_params

    def prepare(self, *pairs, **opts):
        """Check hardware"""
        # check temperature controller state
        msg = ''
        try:
            self.dev = PyTango.DeviceProxy(self.ctrl_dev)
            if self.dev.state() == PyTango.DevState.FAULT:
                msg = 'Temperature controller is FAULT. Please check.'
        except Exception:
            msg = 'Unknown error while accessing temperature controller'
        if msg != '':
            self.error(msg)
            raise Exception(msg)

    def run(self, *pairs, **opts):
        """Set requested parameters and check that they were correctly set in
        the hardware"""
        # getting parameters requested
        param, value = pairs[0]
        param, value = param.lower(), value.lower()
        if param == 'get':
            if not (value in self.data.keys()) and value != 'all':
                msg = 'Invalid parameter: %s' % str(value)
                self.output(msg)
                raise Exception(msg)
            try:
                control_type = \
                    self.dev.read_attribute(self.ctrl_attr_type).value
                self.data['control_type'] = self.to_usr(control_type)
                if control_type.lower() == 'man':
                    setpoint = \
                        self.dev.read_attribute(self.ctrl_attr_output).value
                else:
                    setpoint = \
                        self.dev.read_attribute(self.ctrl_attr_setpoint).value
                self.data['setpoint'] = setpoint
                self.data['range'] = \
                    self.dev.read_attribute(self.ctrl_attr_range).value
                self.data['range'] = self.data['range'].capitalize()
                self.data['rate'] = \
                    self.dev.read_attribute(self.ctrl_attr_rate).value
                self.data['state'] = \
                    self.dev.read_attribute(self.ctrl_attr_state).value
            except Exception:
                msg = 'Error while getting controller parameters'
                self.output(msg)
                raise Exception(msg)
            if value == 'all':
                for param in sorted(self.data.keys()):
                    self.output('%s: %s' % (param, str(self.data[param])))
            else:
                self.output('%s: %s' % (value, str(self.data[value])))
            return

        # check and get requested parameters to really set in the hardware
        hw_params = self.extract_and_check_params(pairs)
        # apply the requested parameters in the hardware
        for param_name, param_value in hw_params:
            try:
                # this needs a special treatment (see below)
                if param_name == 'state':
                    self.dev.command_inout(param_value)
                else:
                    param_name = param_name.lower()
                    self.dev.write_attribute(param_name, param_value)
            except:
                msg = 'Error while writing parameter %s with %s value' % \
                      (param_name, str(param_value))
                self.output(msg)
                raise Exception(msg)
            self.check_readback(param_name, param_value)

    def check_readback(self, param_name, param_value):
        """check that all parameters were correctly set in the hardware"""
        try:
            param_name = param_name.lower()
            if param_name == 'state':
                readback = str(self.dev.read_attribute(param_name).value)
            else:
                readback = self.dev.read_attribute(param_name).value
            if type(readback) == str:
                if readback.lower() != param_value.lower():
                    msg = 'Readback value read from instrument %s differs '\
                          'from the set value %s' %\
                          (str(readback), str(param_value))
                    self.error(msg)
                    raise Exception(msg)
            elif type(readback) == float:
                # If param is outsetpoint, the attr writen value must be set,
                # not the read value
                if param_name.lower() == self.ctrl_attr_output.lower():
                    readback = self.dev.read_attribute(param_name).w_value
                if abs(readback-param_value) > 1e-5:
                    msg = 'Readback value read from instrument %s differs '\
                          'from the set value %s' % \
                          (str(readback), str(param_value))
                    self.error(msg)
                    raise Exception(msg)
            else:
                msg = 'Unexpected type (%s) for param %s' % \
                      (str(type(readback)), param_name)
                self.output(msg)
                raise Exception(msg)
        except Exception:
            msg = 'Error while checking written parameter %s with %s value' % \
                  (param_name, str(param_value))
            self.output(msg)
            raise Exception(msg)
