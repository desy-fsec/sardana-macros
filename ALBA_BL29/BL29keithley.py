#!/usr/bin/env python

"""
Specific Alba BL29 util macros for managing the Keithley 428
"""

__all__=['k428']

import PyTango

from sardana.macroserver.macro import Macro, Type, ParamRepeat
from sardana.macroserver.scan import SScan


class k428(Macro):
    """
    Macro for getting/setting Keithley K428 electrometers parameters
    and/or running its commands.

    For GETTING the parameters, specify the keithley name (or \"all\" to get
    info from all the keithleys) followed by the \"get\" keyword followed by the
    list of parameters you want to get or the special keyword \"all\"
    if you want to get all the parameters.
    For example:
        k428 keithley_name get gain risetime
        k428 all get all

    For SETTING the parameters, specify the keithley name (or \"all\" to set
    value(s) into all the keithleys) followed by the \"set\" keyword followed by
    list of pairs consisting of a pair formed by param_name + param_value.
    For example:
        k428 keithley_name set Gain 9
        k428 all set Gain 10 RiseTime 100

    For RUNNING a command,  specify the keithley name (or \"all\" to run command
    in all the keithleys) followed by the \"run\" keyword followed by the list
    of commands you want to run (note that no parameters are necessary for commands).
    For example:
        k428 keithley_name AutoFilterOff
        k428 all run PerformZeroCorrect AutoFilterOn

    For INFO on which electrometer name corresponds to which physical electrometer
    type the \"info\" keyword:
        k428 info

    Note that keywords, parameters names, command names and parameter values
    are caseless.
    """

    keithleys = {
        'i1_sample_tey' : 'BL29/CT/K428-0',
        'i2_KB_tey'     : 'BL29/CT/K428-1',
        'i0_diode'      : 'BL29/CT/K428-2'
    }

    param_def = [
        ['keithley_name', Type.String, None, str(['all']+sorted(keithleys.keys()))],
        ['operation', Type.String, None, 'Operation to perform [get/set/run/info]'],
        ['param_list', ParamRepeat(['param',  Type.String, None, 'pair(s) of (parameter + value) or command(s)']), '', '']
    ]

    
    def prepare_keithleys(self,keithley_name):
        """"""
        if keithley_name.lower() == 'all':
            ids = sorted(self.keithleys.keys())
        elif keithley_name.lower() not in self.keithleys.keys():
            raise Exception('Invalid keithley_name %s' % keithley_name)
        else:
            ids = [keithley_name.lower()]

        self.devs = {}
        for id in ids:
            dev_name = self.keithleys[id]
            try:
                self.devs[id] = PyTango.DeviceProxy(dev_name)
                self.devs[id].state()
            except:
                raise Exception('Keithley %d seems to be unreachable. Please check its tango device (%s) state' % (id, dev_name))

    def prepare(self, keithley_id, operation, *param_list):
        """Check that the Keithley(s) is(are) reachable"""
        self.prepare_keithleys(keithley_id)

    def run(self, keithley_id, operation, *param_list):
        result = {}
        for key in self.devs.keys():
            dev = self.devs[key]
            dev_result = {}
            if operation.lower() == 'get':
                if 'all' in [param.lower() for param in param_list]:
                    param_list = dev.get_attribute_list()
                for param in param_list:
                    value = dev.read_attribute(param).value
                    dev_result[param] = value
                    self.output('Keithley %s %s: %s' % (str(key), param, str(value)))
            elif operation.lower() == 'set':
                params = list(param_list)
                if (len(params) % 2) != 0:
                    raise Exception('Invalid parameter list: %s' % str(param_list))
                while len(params) > 1:
                    value = params.pop()
                    param = params.pop()
                    dev.write_attribute(param,int(value)) #we are lucky that all writable attributes are DevLong
                    self.output('Keithley %s %s %s correctly set' % (str(key), param, value))
            elif operation.lower() == 'run':
                for cmd in param_list: #we are lucky that all commands are paramless
                    dev.command_inout(cmd)
                    self.output('Command %s correctly run' % cmd)
            elif operation.lower() == 'info':
                dev_result = dev.name()
                self.output('Keithley %s is attached to %s' % (str(key), str(dev_result)))
            else:
                raise Exception('Unknown operation: %s' % operation)
            if len(param_list) > 1:
                self.output('\n')
            result[key] = dev_result

        return result


#class k428_test(Macro):
    #"""Test results given by k428 macro"""
    #def run(self):
        #mac, _ = self.createMacro('k428','all', 'get', 'all')
        #mac, _ = self.createMacro('k428','all', 'info')
        #mac, _ = self.createMacro('k428','all', 'set', 'gain','10')
        #mac, _ = self.createMacro('k428','all', 'run', 'autofilteron')
        #result = self.runMacro(mac)
        #self.output('%s\n\n\n%s' % (str(mac), str(result)))
