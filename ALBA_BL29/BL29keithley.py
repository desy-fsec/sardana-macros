#!/usr/bin/env python

"""
Specific Alba BL29 util macros for managing the Keithley 428
"""

import PyTango

from sardana.macroserver.macro import Macro, Type, ParamRepeat
from sardana.macroserver.scan import SScan


class k428(object):

    keithleys = {
        0 : 'BL29/CT/K428-0',
        1 : 'BL29/CT/K428-1'
    }

    params_rw = {
        'gain'       : int,
        'bypass'     : int,
    }

    params_ro = {
        'overloaded' : int
    }

    @staticmethod
    def check_keithley(keithley_id):
        """"""
        if keithley_id not in k428.keithleys.keys():
            raise Exception('Invalid keithley_id %d' % keithley_id)

        dev_name = k428.keithleys[keithley_id]
        try:
            dev = PyTango.DeviceProxy(dev_name)
            dev.state()
        except:
            raise Exception('Keithley %d seems to be unreachable. Please check its tango device (%s) state' % (keithley_id, dev_name))

        return dev

    @staticmethod
    def check_params(dev, param_names, check_rw=False):
        """"""
        valid_params = k428.params_rw
        if not check_rw: #check that all param_names are writable
            valid_params.update(k428.params_ro)

        for param_name in param_names:
            if param_name.lower() not in valid_params.keys():
                return (False, param_name)
        return (True,'')


class k428set(Macro):
    """
    Keithley 428 parameters configuring macro.
    """

    param_def = [
        ['keithley_id', Type.Integer,  None, 'Keithley number'],
        ['name_value',
         ParamRepeat(['param_name',  Type.String, None, 'parameter name'],
                     ['param_value', Type.String, None, 'parameter value']),
         None, 'List of tuples: (param_name, param_value)']
    ]

    def prepare(self, keithley_id, *pairs, **opts):
        """Check that the Keithley is reachable"""
        #check keithley
        self.dev = k428.check_keithley(keithley_id)

    def run(self, keithley_id, *pairs):
        #check param_names
        param_names = [pair[0] for pair in pairs]
        param_values = [pair[1] for pair in pairs]
        ok, param_wrong = k428.check_params(self.dev, param_names, check_rw=True)
        if not ok:
            self.output('parameter %s is not recognized or not writable' % param_wrong)
            return False

        #write parameters and check they were correctly written
        data = {}
        for param_name, param_value in zip(param_names, param_values):
            param_value = k428.params_rw[param_name](param_value)
            self.dev.write_attribute(param_name, param_value)
            param_value_rb = self.dev.read_attribute(param_name).value
            if param_value != param_value_rb:
                msg = 'parameter %s setvalue (%s) was not correctly set in instrument (readback %s)' % (param_name, str(param_value), str(param_value_rb))
                self.output(msg)
                return False
            self.output('%s %s correctly set in instrument' % (param_name, str(param_value)))
            data[param_name] = param_value

        #@todo: remove this comment as soon as this call is supported
        #self.setData(data)
        return True


class k428get(Macro):
    """
    Keithley 428 parameters retrieving macro.
    """

    param_def = [
        ['keithley_id', Type.Integer, None, 'Keithley number'],
        ['param_names', ParamRepeat(['param_name',  Type.String, None, 'parameter name']), None, 'list of parameters names']
    ]

    def prepare(self, keithley_id, *param_names, **opts):
        """Check that the Keithley is reachable"""
        #check keithley
        self.dev = k428.check_keithley(keithley_id)

    def run(self, keithley_id, *param_names):
        #check param_names
        ok, param_wrong = k428.check_params(self.dev, param_names)
        if not ok:
            self.output('parameter %s is not recognized' % param_wrong)
            return False

        #get parameters and return
        data = {}
        for param_name in param_names:
            data[param_name] = self.dev.read_attribute(param_name).value
            self.output('%s: %s' % (param_name, str(data[param_name])))

        #@todo: remove this comment as soon as this call is supported
        #self.setData(data)
        return True
