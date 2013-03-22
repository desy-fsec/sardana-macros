#!/usr/bin/env python

"""
Specific Alba BL29 XMCD end station util macros
"""

import PyTango
import time

#@todo: REMOVE ParamRepeat when fixed bug:
#    https://sourceforge.net/tracker/?func=detail&atid=484769&aid=3608704&group_id=57612
from sardana.macroserver.macro import Macro, Type, ParamRepeat


class xmcd_4kpot_set_refill(Macro):
    """
    Macro for controlling XMCD 4K pot refill mode.

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
        ['requested_mode', Type.String, None,  'Mode to set: %s.' % str(modes.keys())],
        ['sleep_time',     Type.Float,  0.0,   'Sleep time (in seconds) after setting requested_mode. Default is 0.0 if not specified.'],
        ['final_mode',     Type.String, 'Off', 'The pump will be left in this mode after sleep_time expires. If not specified and sleep_time > 0.0, Off is assumed.'],
    ]

    def prepare(self, requested_mode, sleep_time, final_mode):
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


class xmcd_sample_temp_control(Macro):
    """
    Macro for setting/getting XMCD sample temperature control parameters.

    This macro is used to set or get all the parameters for controlling the
    XMCD end station sample temperature.

    For GETTING the parameters, provide the macro with pairs consisting in the
    string get + param_name. You can also simply provide 'get all' and all the
    parameters will be retrieved. For example:
        xmcd_sample_temp_control get setpoint
        xmcd_sample_temp_control get all

    For SETTING the parameters, these are passed as pairs consisting on
    param_name + param_value. For example, to set the temperature setpoint, you
    can use:
        xmcd_sample_temp_control setpoint 33.3

    The parameter names and their possible values are:
    - state -> The hardware controller state. Please note that only 2 states are
    availabe when setting the value:
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

    2) Hence, in order to avoid possible errors, if you want to set output power
    manually you have to explicitly specify that you want to set the controller
    to manual mode (even if it is already in that mode). Otherwise, the setpoint
    parameter will be assumed to be a temperature setpoint, and hence the macro
    will check that the controller IS NOT in manual mode, and will complain if
    it is.

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
#    https://sourceforge.net/tracker/?func=detail&atid=484769&aid=3608704&group_id=57612
#    param_def = [
#        [ 'param_value', [ [ 'param_name',  Type.String, None, 'parameter name' ],
#                           [ 'param_value', Type.String, None, 'parameter value'],
#                           { 'min' : 1, 'max' : 4 } ],
#         None, 'List of param_name/param_value pairs']
#    ]

    ctrl_dev = 'XMCD/CT/TC'
    ctrl_attr_output = 'Loop1Output'
    ctrl_attr_range = 'Loop1Range'
    ctrl_attr_rate = 'Loop1Rate'
    ctrl_attr_setpoint = 'Loop1SetPoint'
    ctrl_attr_type = 'Loop1Type'
    ctrl_attr_state = 'State'

    control_types = ['Off', 'PID', 'Manual', 'Table', 'RampWithPID', 'RampWithTable']
    ranges = ['Low', 'Mid', 'Hi']

    control_types_hw = ['off', 'pid', 'man', 'table', 'rampp', 'rampt']

    data = {
        'setpoint' : None,
        'control_type' : None,
        'range' : None,
        'rate' : None,
        'state' : None
    }

    allowed_commands = ('on', 'off')

    def to_usr(self, value):
        """"""
        control_types = [type.lower() for type in self.control_types]
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
        #check parameters if provided
        self.data = {
            'setpoint'     : None,
            'control_type' : None,
            'range'        : None,
            'rate'         : None,
            'state'        : None
        }
        control_types = [type.lower() for type in self.control_types]
        ranges = [range.lower() for range in self.ranges]
        for param_name, param_value in pairs:
            param_value = param_value.lower()
            #check param name
            if not (param_name in self.data.keys()):
                msg = 'Invalid parameter %s. Valid parameters are: %s' % (str(param_name), str(self.data.keys()))
                self.output(msg)
                raise Exception(msg)
            #check param value
            if param_name == 'setpoint':
                self.data[param_name] = param_value
            elif param_name == 'control_type':
                if not (param_value in control_types):
                    msg = 'Invalid parameter control_type: %s Valid values are %s' % (param_value, str(self.control_types))
                    self.output(msg)
                    raise Exception(msg)
                self.data[param_name] = param_value
            elif param_name == 'range':
                if not (param_value in ranges):
                    msg = 'Invalid parameter range: %s Valid values are %s' % (param_value, str(self.ranges))
                    self.output(msg)
                    raise Exception(msg)
                self.data[param_name] = param_value
            elif param_name == 'rate':
                self.data[param_name] = param_value
            elif param_name == 'state':
                if not (param_value in self.allowed_commands):
                    msg = 'Invalid parameter state: %s Valid values are %s' % (param_value, str(self.allowed_commands))
                    self.output(msg)
                    raise Exception(msg)
                self.data[param_name] = param_value
            else:
                msg = 'Unknown parameter: %s' % str(param_name)
                self.output(msg)
                raise Exception(msg)

        #and finally check logic between parameters and translate them to hw params
        #NOTE that the order in which the ha params are appended to the list are
        #important in case of setting temperature/manual_value
        setpoint = self.data['setpoint']
        control_type = self.data['control_type']
        range = self.data['range']
        rate = self.data['rate']
        state = self.data['state']
        if control_type != None:
            hw_params.append([self.ctrl_attr_type, self.to_hw(control_type)])
        if range != None:
            hw_params.append([self.ctrl_attr_range, range])
        if rate != None:
            hw_params.append([self.ctrl_attr_rate, float(rate)])
        if setpoint != None:
            if control_type == None:
                actual_control_type = self.dev.read_attribute(self.ctrl_attr_type).value
                actual_control_type = actual_control_type.lower()
                if actual_control_type == 'man':
                    msg = 'You requested setting a temperature target, but the controller is in manual mode'
                    self.output(msg)
                    raise Exception(msg)
                hw_params.append([self.ctrl_attr_setpoint, float(setpoint)])
            elif control_type == 'manual':
                hw_params.append([self.ctrl_attr_output, float(setpoint)])
            else:
                hw_params.append([self.ctrl_attr_setpoint, float(setpoint)])
        #special treament for 'state'
        if state != None:
            hw_params.append(['state', state])

        return hw_params

    def prepare(self, *pairs, **opts):
        """Check hardware"""
        #check temperature controller state
        msg = ''
        try:
            self.dev = PyTango.DeviceProxy(self.ctrl_dev)
            if self.dev.state() == PyTango.DevState.FAULT:
                msg = 'Temperature controller is FAULT. Please check.'
        except Exception, e:
            msg = 'Unknown error while accessing temperature controller'
        if msg != '':
            self.error(msg)
            raise Exception(msg)

    def run(self, *pairs, **opts):
        """Set requested parameters and check that they were correctly set in the hardware"""
        #lower case for easiest management
        control_types = [type.lower() for type in self.control_types]
        ranges = [range.lower() for range in self.ranges]

        #getting parameters requested
        param, value = pairs[0]
        if param.lower() == 'get':
            if not (value.lower() in self.data.keys()) and value.lower()!= 'all':
                msg = 'Invalid parameter: %s' % str(value)
                self.output(msg)
                raise Exception(msg)
            try:
                control_type = self.dev.read_attribute(self.ctrl_attr_type).value
                self.data['control_type'] = self.to_usr(control_type)
                if control_type.lower() == 'man':
                    setpoint = self.dev.read_attribute(self.ctrl_attr_output).value
                else:
                    setpoint = self.dev.read_attribute(self.ctrl_attr_setpoint).value
                self.data['setpoint'] = setpoint
                self.data['range'] = self.dev.read_attribute(self.ctrl_attr_range).value.capitalize()
                self.data['rate'] = self.dev.read_attribute(self.ctrl_attr_rate).value
                self.data['state'] = self.dev.read_attribute(self.ctrl_attr_state).value
            except Exception, e:
                msg = 'Error while getting controller parameters'
                self.output(msg)
                raise Exception(msg)
            if value == 'all':
                for param in sorted(self.data.keys()):
                    self.output('%s: %s' % (param, str(self.data[param])))
            else:
                self.output('%s: %s' % (value, str(self.data[value])))
            return

        #check and get requested parameters to really set in the hardware
        hw_params = self.extract_and_check_params(pairs)
        #apply the requested parameters in the hardware
        for param_name, param_value in hw_params:
            try:
                if param_name == 'state': #this needs a special treatment (see below)
                    self.dev.command_inout(param_value)
                else:
                    param_name = param_name.lower()
                    self.dev.write_attribute(param_name, param_value)
            except:
                msg = 'Error while writing parameter %s with %s value' % (param_name, str(param_value))
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
                if readback.lower()!= param_value.lower():
                    msg = 'Readback value read from instrument %s differs from the set value %s' % (str(readback), str(param_value))
                    self.error(msg)
                    raise Exception(msg)
            elif type(readback) == float:
                #If param is outsetpoint, the attr writen value must be set, not the read value 
                if param_name.lower() == self.ctrl_attr_output.lower() :
                    readback = self.dev.read_attribute(param_name).w_value
                if abs(readback-param_value) > 1e-5:
                    msg = 'Readback value read from instrument %s differs from the set value %s' % (str(readback), str(param_value))
                    self.error(msg)
                    raise Exception(msg)
            else:
                msg = 'Unexpected type (%s) for param %s' % (str(type(readback)), param_name)
                self.output(msg)
                raise Exception(msg)
        except Exception, e:
            msg = 'Error while checking written parameter %s with %s value' % (param_name, str(param_value))
            self.output(msg)
            raise Exception(msg)
