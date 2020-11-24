"""Macros for creating Pool elements"""

from __future__ import print_function
import os
from sardana.macroserver.macro import Macro, Type

__all__ = ["create_motor_controller", "create_motor"]


class _create_controller(Macro):
    """Create pool controller"""
    param_def = [
        ['ctrl_type', Type.String, None,
         'Type of controller'],
        ['ctrl_filename', Type.String, None,
         'Name of the file with the controller class'],
        ['ctrl_classname', Type.String, None,
         'Name of the controller class'],
        ['ctrl_name', Type.String, None,
         'Name of the controller to create'],
        ["property_pairs",
         [['property_name', Type.String, None,
           'controller property name'],
          ['property_value', Type.String, None,
           'controller property value']],
         "", 'List of property pairs']]

    def run(self, ctrl_type, ctrl_filename, ctrl_classname, ctrl_name,
            property_pairs):

        pools = self.getPools()
        pool = pools[0]

        args = []
        args.append(str(ctrl_type))
        args.append(str(ctrl_filename))
        args.append(str(ctrl_classname))
        args.append(str(ctrl_name))
        if len(property_pairs[0]) > 0:
            for i in range(0, len(property_pairs)):
                args.append(str(property_pairs[i][0]))
                args.append(str(property_pairs[i][1]))

        pool.CreateController(args)


class _create_element(Macro):
    """Create a pool element"""
    param_def = [
        ['elem_type', Type.String, None, 'Type of the element'],
        ['ctrl_name', Type.String, None,
         'Name of the controller for the element'],
        ['axis_number', Type.Integer, None, 'Axis number of the element'],
        ['elem_name', Type.String, None, 'Name of the element to create']]

    def run(self, elem_type, ctrl_name, axis_number, elem_name):

        pools = self.getPools()
        pool = pools[0]

        args = []
        args.append(str(elem_type))
        args.append(str(ctrl_name))
        args.append(str(axis_number))
        args.append(str(elem_name))

        for arg in args:
            self.output(arg)
        pool.CreateElement(args)


class create_motor_controller(Macro):
    """Create a motor controller"""
    param_def = [
        ['ctrl_name', Type.String, None, 'Name of the Pool Controller'],
        ['root_device_name', Type.String, None,
         'Common name of the motors to be controlled']
    ]

    def run(self, ctrl_name, root_device_name):

        tango_host = os.getenv('TANGO_HOST')

        tmp_macro, pars = self.createMacro(
            "_create_controller", "Motor", "HasyMotorCtrl.py",
            "HasyMotorCtrl", ctrl_name,
            [["RootDeviceName", root_device_name],
             ["TangoHost", tango_host]])

        self.runMacro(tmp_macro)


class create_motor(Macro):
    """Create a motor"""
    param_def = [
        ['motor_name', Type.String, None,
         'Name of the motor to create'],
        ['axis_number', Type.Integer, None,
         'Axis number of the motor'],
        ['ctrl_name', Type.String, None,
         'Name of the controller for this motor']
    ]

    def run(self, motor_name, axis_number, ctrl_name):

        tmp_macro, pars = self.createMacro(
            "_create_element", "Motor",
            ctrl_name, str(axis_number), motor_name)

        self.runMacro(tmp_macro)
