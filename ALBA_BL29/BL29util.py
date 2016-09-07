#!/usr/bin/env python

"""
Utility macros specifically developed for Alba BL29 Boreas beamline
"""

import PyTango

from sardana.macroserver.macro import Macro, Type, ParamRepeat

__all__ = ['femto', 'k428', 'speak']


class femto(Macro):
    # this macro substitutes the femto macro defined in BLmares.py: the later
    # was designed to change the gain of only 1 femto (which was controlled by
    # using DIO signals of the EPS)
    """
    Macro for getting/setting femto(s) gain(s)

    For GETTING the gain value, specify the femto number (or \"all\" to get
    info from all the femtos).
    For example:
        femto femto_id
        femto all

    For SETTING the gain, specify the femto number (or \"all\" to set the same
    gain in all the femtos) followed by the gain value to set (allowed 4-13,
    meaning 1e4-1e13).
    For example:
        femto femto_id 13
        femto all 4
    """

    dio_name = 'BL29/CT/DIO-IBL2902-DO'

    gain_range = range(4, 13+1)

    femtos = {
        '1': [0x0001, 0x0004, 0x0010, 0x0040],
        '2': [0x0002, 0x0008, 0x0020, 0x0080],
        '3': [0x0100, 0x0400, 0x1000, 0x4000],
        '4': [0x0200, 0x0800, 0x2000, 0x8000],
    }

    param_def = [
        ['femto_id', Type.String, None, str(['all'] + sorted(femtos.keys()))],
        ['gain', Type.String, '',
            'if setting, gain value to set %s' % str(gain_range)],
    ]

    def prepare(self, femto_id, gain=None):
        """"""
        femto_id == femto_id.lower()
        if femto_id not in self.femtos.keys() and femto_id != 'all':
            msg = 'Unknown femto: %s' % femto_id
            raise Exception(msg)

        # check gain
        try:
            if gain != '' and int(gain) not in self.gain_range:
                raise Exception()
        except:  # conversion int(gain) failed or raised by us
            msg = 'Invalid gain: %s' % gain
            raise Exception(msg)

        # check DIO interface
        try:
            self.dio = PyTango.DeviceProxy(self.dio_name)
            if self.dio.state() == PyTango.DevState.FAULT:
                msg = 'DIO port is FAULT'
                raise Exception(msg)
            buffer = self.dio.read_attribute('Buffer00').value
            if len(set(buffer)) != 1:
                msg = 'All items in Buffer00 of DIO %s were expected to be '\
                      'equal' % self.dio_name
                raise Exception(msg)
            if self.dio.read_attribute('OutputMode').value != 0:
                msg = 'DIO OutputMode is not 0'
                raise Exception(msg)
        except Exception, e:
            if isinstance(e, PyTango.DevFailed):
                desc = str(e[0].desc)
                msg = 'DIO port %s is not ready: %s' % (self.dio_name, desc)
                raise Exception(msg)
            else:
                raise

    def run(self, femto_id, gain=None):
        """"""
        if femto_id.lower() == 'all':
            femtos = sorted(self.femtos.keys())
        else:
            femtos = list(femto_id)

        buffer = self.dio.read_attribute('Buffer00').value
        mask = buffer[0]
        if gain == '':  # get gain
            out = []
            for femto in femtos:
                gain = 0x0
                bits = self.femtos[femto]
                for idx, bit in enumerate(bits):
                    if bit & mask:
                        gain |= (1 << idx)
                gain += self.gain_range[0]
                out.append(gain)
                self.output('Femto %s gain: %d' % (femto, gain))
            if self.dio.state() != PyTango.DevState.RUNNING:
                self.warning('DIO card is not running: no femto control')
                out = [self.gain_range[0] for i in range(len(femtos))]
            return out
        else:  # set gain
            gain = int(gain) - self.gain_range[0]  # subtract offset
            for femto in femtos:
                bits = self.femtos[femto]
                for idx, bit in enumerate(bits):
                    if (1 << idx) & gain:
                        mask |= bit
                    else:
                        mask &= ~bit
            buffer = [mask for i in range(len(buffer))]
            self.debug('Buffer: %s' % str(buffer))
            self.dio.write_attribute('Buffer00', buffer)
            self.dio.command_inout('Output', [0, 0])


class k428(Macro):
    """
    Macro for getting/setting Keithley K428 electrometers parameters and/or
    running its commands.

    For GETTING the parameters, specify the keithley number (or \"all\" to get
    info from all the keithleys) followed by the \"get\" keyword followed by
    the list of parameters you want to get or the special keyword \"all\"
    if you want to get all the parameters.
    For example:
        k428 keithley_number get gain risetime
        k428 all get all

    For SETTING the parameters, specify the keithley number (or \"all\" to set
    value(s) into all the keithleys) followed by the \"set\" keyword followed
    by list of pairs consisting of a pair formed by param_name + param_value.
    For example:
        k428 keithley_number set Gain 9
        k428 all set Gain 10 RiseTime 100

    For RUNNING a command,  specify the keithley number (or \"all\" to run
    command in all the keithleys) followed by the \"run\" keyword followed by
    the list of commands you want to run (note that no parameters are necessary
    for commands).
    For example:
        k428 keithley_number AutoFilterOff
        k428 all run PerformZeroCorrect AutoFilterOn

    For INFO on which electrometer number corresponds to which physical
    electrometer type the keithley number (or \"all\") followed by the \"info\"
    keyword:
        k428 all info

    Note that keywords, parameters names, command names and parameter values
    are caseless.
    """

    keithleys = {
        '1': 'BL29/CT/K428-1',
        '2': 'BL29/CT/K428-2',
        '3': 'BL29/CT/K428-3',
    }

    param_def = [
        ['keithley_number', Type.String, None,
            str(['all'] + sorted(keithleys.keys()))],
        ['operation', Type.String, None,
            'Operation to perform [get/set/run/info]'],
        ['param_list', ParamRepeat([
            'param',
            Type.String,
            None,
            'pair(s) of (parameter + value) or '
            'command(s)']), '', '']
    ]

    def prepare_keithleys(self, keithley_id):
        """"""
        if keithley_id.lower() == 'all':
            ids = sorted(self.keithleys.keys())
        elif keithley_id.lower() not in self.keithleys.keys():
            raise Exception('Invalid keithley_id %s. Valid ones are: %s' %
                            (keithley_id, str(sorted(self.keithleys.keys()))))
        else:
            ids = [keithley_id.lower()]

        self.devs = {}
        for id in ids:
            dev_name = self.keithleys[id]
            try:
                self.devs[id] = PyTango.DeviceProxy(dev_name)
                self.devs[id].state()
            except:
                raise Exception('Keithley %d seems to be unreachable. Please '
                                'check its tango device (%s) state' %
                                (id, dev_name))

    def prepare(self, keithley_id, operation, *param_list):
        """Check that the Keithley(s) is(are) reachable"""
        self.prepare_keithleys(keithley_id)

    def run(self, keithley_id, operation, *param_list):
        result = {}
        for key in sorted(self.devs.keys()):
            dev = self.devs[key]
            dev_result = {}
            if operation.lower() == 'get':
                if 'all' in [param.lower() for param in param_list]:
                    param_list = dev.get_attribute_list()
                for param in param_list:
                    value = dev.read_attribute(param).value
                    dev_result[param] = value
                    self.output('Keithley %s %s: %s' %
                                (str(key), param, str(value)))
            elif operation.lower() == 'set':
                params = list(param_list)
                if (len(params) % 2) != 0:
                    raise Exception('Invalid parameter list: %s'
                                    % str(param_list))
                while len(params) > 1:
                    value = params.pop()
                    param = params.pop()
                    # we are lucky that all writable attributes are DevLong
                    dev.write_attribute(param, int(value))
                    self.output('Keithley %s %s %s correctly set' %
                                (str(key), param, value))
            elif operation.lower() == 'run':
                # we are lucky that all commands are paramless
                for cmd in param_list:
                    dev.command_inout(cmd)
                    self.output('Command %s correctly run' % cmd)
            elif operation.lower() == 'info':
                dev_result = dev.name()
                self.output('Keithley %s is attached to %s' %
                            (str(key), str(dev_result)))
            else:
                raise Exception('Unknown operation: %s' % operation)
            if len(param_list) > 1:
                self.output('\n')
            result[key] = dev_result

        return result


class speak(Macro):
    """
    Speaks the requested text using software synthesized speech
    """

    SPEAK_DEV = 'BL29/CT/VOICE'

    param_def = [
        ['words', ParamRepeat(['word',  Type.String, None, 'one word']), [''],
            'words forming the phrase to be played']
    ]

    def run(self, *words):
        speech = ' '.join(words)
        self.output(speech)
        speech_dev = PyTango.DeviceProxy(self.SPEAK_DEV)
        speech_dev.command_inout('Play_Sequence', speech)
