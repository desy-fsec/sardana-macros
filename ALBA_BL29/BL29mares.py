#!/usr/bin/env python

"""
Specific Alba BL29 MARES (RSXS end station) utility macros
"""

import PyTango

import threading
import time
import os
import xmlrpclib
import socket

from sardana.macroserver.macro import Macro, Type


__all__ = ['mares_sample_temp_control', 'mares_shutter', 'mares_ccd']


class mares_sample_temp_control(Macro):
    """
    Macro for setting/getting MARES sample temperature control parameters.

    This macro is used to set or get all the parameters for controlling the
    MARES end station sample temperature.

    For GETTING the parameters, provide the macro with pairs consisting in the
    string get + param_name. You can also simply provide 'get all' and all the
    parameters will be retrieved. Also note that running the macro without
    parameters is equivalent to running it with \'get all\'. For example:
        mares_sample_temp_control get setpoint
        mares_sample_temp_control get all
        mares_sample_temp_control (same as previous one)

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
        ['name_value', [
            ['param_name',  Type.String, 'get', 'parameter name'],
            ['param_value', Type.String, 'all', 'parameter value']],
            None, 'List of pairs: param_name, param_value']
    ]

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
            'control_type': None,
            'range':        None,
            'rate':         None,
            'setpoint':     None,
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

    def prepare(self, pairs):
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

    def run(self, pairs):
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
            rv = []
            if value == 'all':
                for param in sorted(self.data.keys()):
                    self.output('%s: %s' % (param, str(self.data[param])))
                    rv.append(self.data[param])
            else:
                self.output('%s: %s' % (value, str(self.data[value])))
                rv.append(self.data[value])
            return rv

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


class mares_shutter(Macro):
    """
    Macro for opening/closing/checking MARES CCD shutter.
    """

    actions = ('open', 'close', '')
    DELTA = 0.01
    AO_NUMBER_SAMPLES = 'ChannelSamplesPerTrigger'
    AO_SAMPLE_RATE_ATTR = 'SampleRate'
    AO_SAMPLE_RATE = 1000  # default is 1000 samples/sec (0.001 resolution)
    AO_CCD_CH = 'C00_ChannelValues'
    AO_SHUTTER_CH = 'C01_ChannelValues'
    AO_SHUTTER_VOLT = 'C01_LastValue'

    param_def = [
        ['action', Type.String, '',  'action to perform %s: if empty then the '
            'current state will be returned' % str(actions)],
        ['hold',   Type.Float,  0.0, 'optional time to hold action and then '
            'return to previous state'],
        ['delay',  Type.Float,  0.0, 'optional time to wait before performing'
            ' requested action: note that if the action is meant to be '
            'permanent then hold parameter must be set to 0']
    ]

    result_def = [
        ['voltage', Type.Float, None, 'The control voltage output']
    ]

    env_vars = [
        'device',  # AO device name
        'open_voltage',  # opened voltage
        'close_voltage',  # closed voltage
    ]

    def get_state(self, voltage):
        if abs(voltage - self.open_voltage) < self.DELTA:
            state = self.actions[0]
            voltage = self.open_voltage
        elif abs(voltage - self.close_voltage) < self.DELTA:
            state = self.actions[1]
            voltage = self.close_voltage
        else:
            state = 'unknown'
        return state, voltage

    def prepare(self, action, hold, delay):
        """Check hardware and retrieve parameters"""
        # check environment and Adlink AO card
        try:
            for var_name in self.env_vars:
                setattr(self, var_name, self.getEnv(var_name))
            dev_name = self.getEnv('device')
            self.dev = PyTango.DeviceProxy(dev_name)
            self.dev.state()
        except Exception, e:
            msg = 'Check that environment is setup and Adlink AO device is up'
            self.debug('%s: %s' % (msg, str(e)))
            raise Exception(msg)

        self.action = action.lower()
        if self.action not in self.actions:
            msg = 'Invalid action %s. Valid ones: %s' % (self.action,
                                                         str(self.actions))
            raise Exception(msg)

    def run(self, action, hold, delay):
        try:
            action == action.lower()
            if action == self.actions[-1]:  # user is only requesting state
                final_state = ''  # we are only checking, not setting
            else:
                # setup and start adlink ao
                self.setup_ao(action, hold, delay)
                self.dev.command_inout('Start')

                # wait for adlink to stop or timeout
                state = self.dev.state()
                start = time.time()
                timeout = False
                while (state == PyTango.DevState.RUNNING) and not timeout:
                    time.sleep(0.1)
                    state = self.dev.state()
                    timeout = ((time.time() - start) > (hold + delay + 1))
                if timeout:
                    msg = 'Timeout while waiting for Adlink AO. Please check!'
                    self.debug(msg)
                    raise Exception(msg)

                # takes some time to go to set value (why?)
                time.sleep(0.2)

                # find out the final expected state for checking later
                final_state = action
                if hold > 0:
                    idx = self.actions.index(action)
                    reverse_action = self.actions[(idx+1) % 2]
                    final_state = reverse_action

            # read final voltage and state and check that it is as expected
            voltage_now = self.dev.read_attribute(self.AO_SHUTTER_VOLT).value
            current_state, voltage = self.get_state(voltage_now)
            if current_state in self.actions[:-1]:
                if final_state != '' and current_state != final_state:
                    msg = ('Shutter is %s: expected to be %s'
                           % (current_state, final_state))
                    self.error(msg)
                else:
                    msg = 'Shutter is %s' % current_state
                    self.output(msg)
            else:
                msg = 'Shutter state unknown: control voltage is %f' % voltage
                self.error(msg)
        finally:
            # always try to leave hardware
            state = self.dev.state()
            if state != PyTango.DevState.STANDBY:
                self.dev.command_inout('Stop')

        return voltage

    def setup_ao(self, action, hold, delay):
        state = self.dev.state()
        if state != PyTango.DevState.STANDBY:
            msg = ('Adlink AO device is in %s state: it was expected to be in '
                   '%s. Going on, but note that this was unexpected!'
                   % (str(state), str(PyTango.DevState.STANDBY)))
            self.error(msg)
            self.dev.command_inout('Stop')
        # set sample rate
        self.debug('Setting AO sample rate to %.5f' % self.AO_SAMPLE_RATE)
        self.dev.write_attribute(self.AO_SAMPLE_RATE_ATTR, self.AO_SAMPLE_RATE)

        # on/off voltages
        if action == self.actions[0]:
            on_voltage = self.open_voltage
            off_voltage = self.close_voltage
        else:
            on_voltage = self.close_voltage
            off_voltage = self.open_voltage

        # calculate how many points are necessary for the waveform (1 last
        # point is necessary to set last value since it will be the value that
        # will be set in ouput when waveform is finished)
        waveform = []
        if delay > 0:
            points = int(delay * self.AO_SAMPLE_RATE)
            waveform.extend([off_voltage for i in range(points)])
        if hold > 0:
            points = int(hold * self.AO_SAMPLE_RATE)
            waveform.extend([on_voltage for i in range(points)])
            waveform.append(off_voltage)  # 1 last value to set down again
        else:
            waveform.append(on_voltage)  # this value will be kept forever

        # set number of samples: it must be done before writing the waveforms
        # or these will be cropped to number of samples
        self.debug('Setting AO number of points to %d' % len(waveform))
        self.dev.write_attribute(self.AO_NUMBER_SAMPLES, len(waveform))

        # preserve ccd trigger value as it was
        last_value = self.dev.read_attribute(self.AO_CCD_CH).value[-1]
        ccd_waveform = [last_value for i in range(len(waveform))]

        # set shutter and ccd trigger waveforms
        self.dev.write_attribute(self.AO_SHUTTER_CH, waveform)
        self.dev.write_attribute(self.AO_CCD_CH, ccd_waveform)


class mares_ccd(Macro):
    """
    Macro for image acquisition and parameters getting/setting of XCAM CCD.
    Note that this macro will never switch ON/OFF the CCD chip, so you should
    make sure that it is ON before acquiring an image
    Examples of usage:
        - mares_ccd seq_trigger_mode sw:
            sets trigger to software (free run)
        - mares_ccd seq_trigger_mode hw_trig:
            sets trigger to external trigger signal
        - mares_ccd acquire 2.001:
            acquire an image with 2.001 sec of integration and store it in a
            file named scan_dir/scan_file+scan_id.img (where scan_dir,
            scan_file and scan_id are got from environment)
        - mares_ccd acquire 2.001 /tmp/test.img:
            acquire an image with 2.001 sec of integration and store it in a
            file named \"/tmp/test.img\"
        - mares_ccd seq_adc_delay:
            print and return the value of seq_adc_delay
    """

    # Before using this macro you have to correctly setup many components:
    #
    # 1) XCAM control box is ON and connected to its XCAM control PC. This is
    #    a windows PC in which the XCAM proprietary software is installed or
    #    our own built windows DLL has been installed (see *)
    #
    # 2) The necessary Alba software is up and running on XCAM control PC:
    #    - xcamserver.py: simple RPC server to execute binaries (see *)
    #    - xcamgrab: program to load configuration and grab image (see *)
    #    - xcamparam: program get/set config (used only to power on/off see *)
    #
    # 3) The XCAM control PC is correctly configured. In order to properly
    #    interact with this macro some configuration is necessary:
    #    - xcamserver.py must be started at boot (you can use Task Scheduler)
    #    - A shared network drive must be mounted in both the XCAM PC and the
    #      PC running the macro. In XCAM PC this can be done using Task
    #      Scheduler at boot and without the need of any user log on by
    #      running a "net use z: \servername\sharedfolder /persistent:yes"
    #      command using Task Scheduler. Just add a sheduled task, insert
    #      "system" in the "run as" field and set the task to run (or to a
    #      batch file) this simple command:
    #        net use z: \servername\sharedfolder /persistent:yes
    #
    # 4) The network drive used by XCAM control PC must be accesible to the
    #    machine running the macro
    #
    # 5) Some macro parameters must be correctly configured:
    #    - windows_path: this will translate the path naming between the XCAM
    #      control PC and the linux machine running the macro
    #      e.g. ['L:', '/beamlines/bl29', ''], where first is the windows
    #      network drive in XCAM PC, the second value is the location where it
    #      is mounted on linux and the third an optional windows path
    #    - config_file: this is the file from where the xcamgrab program will
    #      load the Alba configuration and hence it must be accesible to the
    #      macro
    #
    # * software for controlling XCAM CCD developed at ALBA and the XCAM
    #   proprietary DLL source code is located here:
    #     https://gitcomputing.cells.es/ctnda/XCAM

    AO_CCD_CH = 'C00_ChannelValues'
    AO_SHUTTER_CH = 'C01_ChannelValues'
    AO_SAMPLE_RATE = 'SampleRate'
    AO_NUMBER_SAMPLES = 'ChannelSamplesPerTrigger'

    fname_seq = 0  # sequential number for auto built file name
    fname_base = ''  # last used filename
    power = False  # power status (False: off or unknown, True: on or ignore)

    env_vars = [
        'device',  # AO device name
        'shutter_opened_voltage',
        'shutter_closed_voltage',
        'ccd_trig_voltage',
        'ccd_idle_voltage',
        'ccd_server',
        'windows_path',  # list with windows drive, linux_path, windows_path
        'config_file',  # config file location used by xcam grab program
        'shutter_ratio'
    ]

    # parameters
    env_parameters = {
        'shutter_ratio':  None,  # % of time the shutter will be opened
    }
    special_parameters = {
        'power': None,  # power status (False: off/unknown, True: on/ignore)
    }
    # { parameter name: {parameter number: tanslation}, ... }
    sequencer_parameters = {
        'seq_adc_delay':        {0:  None},
        'seq_int_minus_delay':  {1:  None},
        'seq_plus_delay':       {2:  None},
        'seq_int_time':         {3:  None},
        'seq_serial_t':         {4:  None},
        'seq_parallel_t':       {5:  None},
        'seq_clk_rst_delay':    {6:  None},
        'seq_bin_rows':         {9:  None},
        'seq_numcols':          {10: None},
        'seq_numrows':          {11: None},
        'seq_frame_time':       {15: None},
        'seq_frame_units':      {64: {'0.1': 0, '0.01': 1}},
        'seq_trigger_mode':     {65: {'hw_trig': 0,
                                      'hw_gate': 1,
                                      'sw': 3,
                                      'sw_delay': 4}},
    }
    parameters = env_parameters.copy()
    parameters.update(special_parameters)
    parameters.update(sequencer_parameters)

    param_def = [
        ['parameter', Type.String,  '', '\"acquire\" or param to get/set:'
            '\n\t\t- %s%s'
            % ('\n\t\t- '.join(sorted(parameters.keys())), '\n')],
        ['value', Type.String,  '', 'integration time in sec (if acquiring)'
            ', parameter value (if setting) or empty (if getting). '
            'When setting values some parameters admit only certain values:\n'
            '\t\t- seq_frame_units: 0.1, 0.01\n'
            '\t\t- seq_trigger_mode: hw_trig, hw_gate, sw, sw_delay\n'],
        ['file_name', Type.String,  '', 'optional file name to save image '
            'when acquiring (default name is built from environment '
            'otherwise)'],
    ]

    interactive = True

    class worker(threading.Thread):

        def __init__(self, parent, server, args):
            threading.Thread.__init__(self)
            self.parent = parent
            self.server = server
            self.results = []
            self.args = args

        def run(self):
            self.parent.debug('Worker thread args: %s' % self.args)
            proxy = xmlrpclib.ServerProxy(self.server)
            self.results = proxy.execute(self.args)
            self.parent.debug('Worker thread results: %s' % self.results)

    def prepare(self, parameter, value, fname):
        # check Adlink AO card and environment params
        try:
            for var_name in self.env_vars:
                setattr(self, var_name, self.getEnv(var_name))
            dev_name = self.getEnv('device')
            self.dev = PyTango.DeviceProxy(dev_name)
            self.dev.state()
        except Exception, e:
            self.debug(str(e))
            msg = ('Check that environment is setup %s and Adlink AO device is'
                   ' up' % str(self.env_vars))
            raise Exception(msg)

        # build file name if necessary, check that location is writable (we
        # assume that external grab program is run as the same user as the
        # macro) and convert file name to windows format
        if parameter.lower() == 'acquire':
            scan_dir = self.getEnv('ScanDir')
            # if no name got then automatically build it from environment
            if fname == '':
                scan_file = self.getEnv('ScanFile')
                if type(scan_file) == list:  # multiple file save (spec + h5)
                    scan_file = scan_file[0]
                scan_file = scan_file.split('.')[0]
                fname_base = '%s/%s' % (scan_dir, scan_file)
                if fname_base != self.fname_base:  # first run or user changed
                    files = [f for f in os.listdir(scan_dir)
                             if os.path.isfile(os.path.join(scan_dir, f))]
                    sequentials = []
                    for f in files:
                        if f.startswith(scan_file):
                            f = f.strip(scan_file)
                            s = ''.join(x for x in f if x.isdigit())
                            if len(s) > 0:
                                sequentials.append(int(s))
                    if len(sequentials) > 0:
                        self.fname_seq = max(sequentials) + 1
                    else:
                        self.fname_seq = 1
                    self.fname_base = fname_base
                fname = '%s%03d.raw' % (self.fname_base, self.fname_seq)
                self.fname = fname
            # check if file exists and if it is writable
            if os.path.isfile(fname) or not os.access(scan_dir, os.W_OK):
                msg = ('File %s already exists or it is not writable!' % fname)
                self.debug(msg)
                raise Exception(msg)
            # convert to windows format (server running on a windows machine)
            try:
                self.debug('%s: %s' % (self.windows_path,
                                       type(self.windows_path)))
                drive, linux_path, windows_path = self.windows_path
            except Exception, e:
                msg = 'Invalid windows_path property'
                self.debug('%s:\n%s' % (msg, str(e)))
                raise Exception(msg)
            self.fname_unix = fname
            fname = '%s%s' % (drive, fname)
            fname = fname.replace(linux_path, windows_path)
            self.debug(fname)
            fname = fname.replace('/', '\\')
            self.fname = fname
            self.debug(self.fname)

            # build and test proxy to CCD server
            try:
                proxy = xmlrpclib.ServerProxy(self.ccd_server)
                socket.setdefaulttimeout(10)
                proxy.system.listMethods()  # do a test call
            except Exception, e:
                socket.setdefaulttimeout(None)  # set global socket to defaults
                msg = 'Unable to connect to CCD server'
                self.debug('%s:\n%s' % (msg, str(e)))
                raise Exception(msg)

    def run(self, parameter, value, fname):
        if parameter.lower() == 'acquire':
            value = float(value)
            self.acquire_image(value)
        elif parameter.lower() in self.parameters.keys():
            self.parameter(parameter, value)
            msg = '%s: %s' % (parameter, str(self.parameter(parameter)))
            self.output(msg)
        elif parameter == '':
            for param in sorted(self.parameters.keys()):
                msg = '%s: %s' % (param, str(self.parameter(param)))
                self.output(msg)
        else:
            msg = 'Unknown parameter %s\n' % parameter
            self.debug(msg)
            raise Exception(msg)

    def parameter(self, param, value=''):
        """get or set parameter"""
        # check parameter name
        param = param.lower()
        if param not in self.parameters.keys():
            msg = 'Invalid parameter %s' % param
            self.debug(msg)
            raise Exception(msg)

        # param in environment parameter (should have already been read)
        if param in self.env_parameters.keys():
            if value == '':
                value = getattr(self, param)
            else:
                env_param = '%s.%s' % (self.__class__.__name__, param)
                self.setEnv(env_param, value)
                setattr(self, param, value)
            return value

        # special parameter
        if param == 'power':
            if value == '':
                value = getattr(self.__class__, param)
            else:
                proxy = xmlrpclib.ServerProxy(self.ccd_server)
                rc, output = proxy.execute(['xcamparam',
                                            param, str(int(value))])
                if rc != 0:
                    msg = 'Error setting %s! Details:\n%s' % (param, output)
                    self.error(msg)
                    raise Exception(msg)
                setattr(self.__class__, param, bool(value))
            return value

        # read configuration from file
        try:
            param_code = str(self.parameters[param].keys()[0])
            if not os.path.exists(self.config_file):
                mode = 'w+'
            else:
                mode = 'r'
            with open(self.config_file, mode) as f:
                config = f.readlines()
        except Exception, e:
            msg = 'Invalid configuration file %s' % self.config_file
            self.debug('%s:\n%s' % (msg, str(e)))
            raise Exception(msg)

        # get parameter
        if value == '':
            found = False
            for line in config:
                if line.startswith(param_code):
                    try:
                        value = int(line.split()[1])
                        # translate value to user units if necessary
                        param_code = int(param_code)
                        if self.parameters[param][param_code] is not None:
                            vals = self.parameters[param][param_code].values()
                            i = vals.index(value)
                            key = self.parameters[param][param_code].keys()[i]
                            value = key
                        found = True
                    except Exception, e:
                        raise
                        msg = ('Error getting value from %s:\n%s'
                               % (line, str(e)))
                        self.debug(msg)
                    break
            if not found:
                msg = ('Param %s not found in config file %s'
                       % (param, self.config_file))
                self.error(msg)
                value = None
        # set parameter
        else:
            # translate value if necessary
            if self.parameters[param].values()[0] is not None:  # param valid
                try:
                    value = self.parameters[param].values()[0][value.lower()]
                    valid = True
                except:
                    valid = False  # invalid parameter
                if not valid:
                    msg = 'Invalid parameter value: %s' % value
                    self.debug(msg)
                    raise Exception(msg)
            # set parameter in config file
            try:
                text = '%s\t%s\n' % (param_code, value)
                for idx, line in enumerate(config):
                    if line.startswith(param_code):
                        config[idx] = text
                        break
                else:
                    config.append(text)  # this parameter was not yet in file
                with open(self.config_file, 'w') as f:
                    f.writelines(config)
            except Exception, e:
                msg = 'Invalid configuration file %s' % self.config_file
                self.debug('%s:\n%s' % (msg, str(e)))
                raise Exception(msg)
        return value

    def acquire_image(self, integration):
        try:
            # get frame units and set frame_time accordingly
            try:
                frame_units = self.parameter('seq_frame_units')
                units = float(frame_units)
            except Exception, e:
                msg = 'Unable to retrieve frame units'
                self.debug('%s: %s' % (msg, str(e)))
                raise Exception(msg)
            frames = int(integration / units)
            self.parameter('seq_frame_time', frames)

            # get trigger mode
            trig_mode = self.parameter('seq_trigger_mode')
            trig_modes = (
                self.parameters['seq_trigger_mode'].values()[0].keys())
            if trig_mode not in trig_modes:
                msg = 'Unknown trigger mode: %s' % str(trig_mode)
                raise Exception(msg)
            if trig_mode.startswith('hw'):  # grab with external trigger
                hw_trig = True
            else:
                hw_trig = False

            # check if power is on or ignored
            if not getattr(self.__class__, 'power'):
                answer = ''
                while not answer.lower() in ('y', 'n'):
                    self.warning('Power is OFF or in UNKNOWN state.')
                    answer = self.input(
                                'Do you want to switch ON? (y/[n]): ',
                                timeout=30,
                                default_value='n')
                    if answer == 'y':  # switch on ccd
                        proxy = xmlrpclib.ServerProxy(self.ccd_server)
                        rc, output = proxy.execute(['xcamparam', 'power', '1'])
                        if rc != 0:
                            msg = 'Error setting ON! Details:\n%s' % output
                            self.error(msg)
                            raise Exception(msg)
                    self.warning('Power status will be IGNORED from now on')
                setattr(self.__class__, 'power', True)
                self.output('OK. Press enter for prompt')

            # grab image
            self.info('Grabbing image into %s ...' % self.fname)
            grab_thread = None
            # grab with external trigger: since the call to the proxy will not
            # return (it is waiting for the trigger) and we have to start the
            # adlink AO to provide that trigger we need to make the call to
            # the proxy in a thread
            if hw_trig:
                # setup Adlink AO hardware
                self.info('Configuring AO device ...')
                self.setup_ao(units, frames)
                # start threaded grab
                grab_thread = self.worker(self, self.ccd_server,
                                          ['xcamgrab', self.fname])
                grab_thread.daemon = False
                self.debug('Thread: %s' % str(grab_thread))
                # before grabbing check that lock file is not present
                lock_dir = os.path.dirname(self.config_file)
                lock_file = lock_dir + '/lock.lck'
                if os.path.exists(lock_file):  # probably previous grab hanged
                    os.remove(lock_file)
                # start grabbing
                grab_thread.start()
                start = time.time()
                self.debug('Waiting for lock file %s' % lock_file)
                timeout = False
                while not os.path.exists(lock_file) and not timeout:
                    os.listdir(lock_dir)  # necessary for refreshing: why?
                    time.sleep(0.1)
                    timeout = ((time.time() - start) > 10)
                if timeout:
                    msg = 'Timeout while waiting for lock file. Please check!'
                    self.debug(msg)
                    raise Exception(msg)
                # wait a while while grabbing really starts
                sleep_time = 0
                time.sleep(sleep_time)
            # grab with software free run: simply call proxy and wait
            else:
                proxy = xmlrpclib.ServerProxy(self.ccd_server)
                rc, output = proxy.execute(['xcamgrab', self.fname])
                if rc != 0:
                    msg = 'Error grabbing image! Details:\n%s' % output
                    self.error(msg)
                    raise Exception(msg)
                else:
                    self.fname_seq += 1

            # start AO and wait until it finishes (only if external trigger)
            if hw_trig:
                if grab_thread is not None and grab_thread.is_alive():
                    # trigger
                    msg = 'Triggering and waiting for image to be taken ...'
                    self.info(msg)
                    self.dev.command_inout('Start')
                    state = self.dev.state()
                    start = time.time()
                    timeout = False
                    while (state == PyTango.DevState.RUNNING) and not timeout:
                        time.sleep(0.1)
                        state = self.dev.state()
                        timeout = ((time.time() - start) > (integration + 1))
                    if timeout:
                        msg = 'Timeout while waiting for triggers'
                        self.debug(msg)
                        raise Exception(msg)
                    # wait for image file to exist
                    while not os.path.exists(self.fname_unix) and not timeout:
                        os.listdir(os.path.dirname(self.fname_unix))  # why?
                        time.sleep(0.1)
                        timeout = ((time.time() - start) > integration + 5)
                    if timeout:
                        msg = ('Timeout waiting for %s. Please check!' %
                               self.fname_unix)
                        self.debug(msg)
                        raise Exception(msg)
                    grab_thread.join(10)  # give it 30 seconds to finish
                    if grab_thread.is_alive():  # thread did not finish
                        msg = 'Grab thread did not finish when expected'
                        grab_thread.kill()
                        raise Exception(msg)
                else:
                    msg = 'Grab thread finished before expected. Please check'
                    if (grab_thread is not None and
                            len(grab_thread.results) > 1):
                        msg += ':\n%s' % str(grab_thread.results[1])
                    raise Exception(msg)
        except:
            raise
        # always turn off device
        finally:
            try:
                msg = 'Stopping AO device'
                if self.dev.state() != PyTango.DevState.STANDBY:
                    self.dev.command_inout('Stop')
            except Exception, e:
                msg = ('Error stopping AO device. Please check, since shutter'
                       ' may be open')
                self.debug('%s. Details:\n%s' % (msg, str(e)))

    def setup_ao(self, frame_unit, frames):
        """
        Setup and check Adlink AO device to trigger 2 waveforms for hardware
        synchronization of:
            - CCD shutter: this must be a gate signal which should take as
                long as the integration time
            - CCD acquisition trigger: this is a trigger signal which must be
                hardware synchronized with the previous one

        CCD shutter requires precise waveform duration. We do this by imposing
        to user a resolution of 1 msec, then set the sample rate of the AO to
        that value and finally write the appropriate waveforms for both
        channels
        """
        # check that Adlink AO state is as expected
        state = self.dev.state()
        if state != PyTango.DevState.STANDBY:
            msg = ('Adlink AO device is in %s state: it should be in %s. '
                   'Result may be wrong!'
                   % (str(state), str(PyTango.DevState.STANDBY)))
            self.error(msg)
            self.dev.command_inout('Stop')

        # set sample rate
        sample_rate = int(1 / frame_unit)
        self.debug('Setting AO sample rate to %d' % sample_rate)
        self.dev.write_attribute(self.AO_SAMPLE_RATE, sample_rate)

        # calculate how many points are necessary for the waveform (1 last
        # point is necessary to set 0 again: otherwise last value is hold)
        points = frames + 1
        self.debug('Number of points %d' % points)
        # set number of samples: it must be done before writing the waveforms
        # or these will be cropped to number of samples
        self.debug('Setting AO number of points to %d' % points)
        self.dev.write_attribute(self.AO_NUMBER_SAMPLES, points)

        # compute and write shutter waveform
        active = int(points * self.shutter_ratio)  # shutter opened only ratio
        opened = [self.shutter_opened_voltage for i in range(active)]
        closed = [self.shutter_closed_voltage for i in range(points-active)]
        self.debug('AO shutter ch %s %d elements: %s' % (self.AO_SHUTTER_CH,
                   len(opened+closed), str(opened+closed)))
        self.dev.write_attribute(self.AO_SHUTTER_CH, opened + closed)

        # compute and write trigger waveform
        waveform = [self.ccd_trig_voltage for i in range(points-1)]
        waveform.append(self.ccd_idle_voltage)
        self.debug('AO shutter ch %s %d elements: %s' % (self.AO_CCD_CH,
                   len(waveform), str(waveform)))
        self.dev.write_attribute(self.AO_CCD_CH, waveform)
