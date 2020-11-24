#!/usr/bin/env python

"""
Macros related to petra3undulator
"""
import PyTango
from sardana.macroserver.macro import Macro, Type

__all__ = ["set_harmonic"]


class set_harmonic(Macro):
    """set new harmonic value"""

    param_def = [
        ['harmonic', Type.Integer, None, 'Harmonic value to set']]

    def run(self, harmonic):
        undulator_device_name = "energy_und"
        try:
            undulator_device_name = self.getEnv('UndulatorDevice')
        except Exception:
            pass

        try:
            undulator_device = PyTango.DeviceProxy(undulator_device_name)
        except Exception:
            self.error(
                "Not able to create proxy to undulator device %s."
                % undulator_device_name)
            self.info(
                "\nSet the name of the Pool undulator device in the "
                "Spock environment variable UndulatorDevice, ex.:\n\n"
                "   senv UndulatorDevice undulator")
            return

        undulator_tango_device = PyTango.DeviceProxy(
            undulator_device.TangoDevice)

        try:
            undulator_tango_device.write_attribute("Harmonic", harmonic)
        except Exception:
            self.error(
                "Unable to set harmonic in Tango Undulator device %s" %
                undulator_device.TangoDevice)
            return

        # Read limits for updating them in sardana

        undulator_device.UnitLimitMin
        undulator_device.UnitLimitMax

        try:
            current_position = undulator_tango_device.read_attribute(
                "Position").value
        except Exception:
            self.error("Unable to read current undulator position")
            return

        try:
            undulator_device.write_attribute("Position", current_position)
        except Exception:
            self.error("Unable to set Position to undulator device")
            return
