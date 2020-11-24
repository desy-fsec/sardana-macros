"""Change motor limits for Hasy motors"""

import PyTango
from PyTango import Except
from sardana.macroserver.macro import Macro, Type, ViewOption

__all__ = ["hasy_set_lim", "hasy_adjust_limits"]


class hasy_set_lim(Macro):
    """Sets the software limits on the specified motor"""
    param_def = [
        ['motor', Type.Moveable, None, 'Motor name'],
        ['low', Type.Float, None, 'lower limit'],
        ['high', Type.Float, None, 'upper limit']
    ]

    def run(self, motor, low, high):

        limits_changed = 1

        name = motor.getName()
        motor_device = PyTango.DeviceProxy(name)
        try:
            motor_device.UnitLimitMax = high
            motor_device.UnitLimitMin = low
        except Exception:
            limits_changed = 0
            self.info("UnitLimitMin/UnitLimitMax has not be written. "
                      "They probably only readable (ex. many VmExecutors)")
            self.info("Limits not changed")

        if limits_changed == 1:
            set_lim, pars = self.createMacro("set_lim", motor, low, high)
            self.runMacro(set_lim)


class hasy_adjust_limits(Macro):
    """Sets Pool motor limits to the values in the Tango Device"""

    def prepare(self, **opts):
        self.all_motors = self.findObjs('.*', type_class=Type.Moveable)

    def run(self):
        nr_motors = len(self.all_motors)
        if nr_motors == 0:
            self.output('No motor defined')
            return

        for motor in self.all_motors:
            name = motor.getName()
            motor_device = PyTango.DeviceProxy(name)
            try:
                high = motor_device.UnitLimitMax
                low = motor_device.UnitLimitMin

                # do not set attribute configuration limits
                #   if UnitLimitMax/~Min can not be written
                adjust_limits = 1
                try:
                    motor_device.UnitLimitMax = high
                    motor_device.UnitLimitMin = low
                except Exception:
                    adjust_limits = 0
                    self.info(
                        "Limits for motor %s not adjusted. "
                        "UnitLimitMax/~Min only readable" % name)
                if adjust_limits == 1:
                    set_lim, pars = self.createMacro(
                        "set_lim", motor, low, high)
                    self.runMacro(set_lim)
            except Exception:
                self.warning(
                    "Limits for motor %s not adjusted. "
                    "Error reading UnitLimitMax/~Min" % name)


class hasy_wm(Macro):
    """Show motor position and limits (UnitLimitMin/~Max)"""

    param_def = [
        ['motor', Type.Moveable, None, 'Motor name'],
    ]

    def run(self, motor):

        show_ctrlaxis = self.getViewOption(ViewOption.ShowCtrlAxis)
        pos_format = self.getViewOption(ViewOption.PosFormat)

        name = motor.getName()
        motor_device = PyTango.DeviceProxy(name)
        try:
            high = motor_device.UnitLimitMax
            low = motor_device.UnitLimitMin
            pos = motor_device.Position
            self.output("")
            if show_ctrlaxis:
                axis_nb = getattr(motor, "axis")
                ctrl_name = self.getController(motor.controller).name
                ca_name = " (" + ctrl_name + "." + str(axis_nb) + ")"
                name = name + ca_name
            self.output("    %s     " % name)
            self.output("")
            if pos_format != -1:
                fmt = '%c.%df' % ('%', pos_format)
                lowstr = fmt % low
                self.output("UnitLimitMin: %s " % lowstr)
                posstr = fmt % pos
                self.output("Current     : %s " % posstr)
                highstr = fmt % high
                self.output("UnitLimitMax: %s " % highstr)
            else:
                self.output("UnitLimitMin: %f " % low)
                self.output("Current     : %f " % pos)
                self.output("UnitLimitMax: %f " % high)

        except PyTango.DevFailed as e:
            Except.print_exception(e)
            self.warning("Not able to read motor position or limits")
