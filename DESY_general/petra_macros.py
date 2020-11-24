#!/usr/bin/env python

"""
Macros related to the petra current
"""
import PyTango
import time
from sardana.macroserver.macro import Macro, Type

__all__ = ["wait_for_petra"]


class wait_for_petracurrent(Macro):
    """wait for beam current above a limit """

    param_def = [
        ['current_limit', Type.Float, 1, 'Limit for checking petra current']]

    def run(self, current_limit):
        try:
            petra_device_name = self.getEnv('PetraDevice')
            try:
                petra_current_name = self.getEnv('PetraCurrent')
            except Exception:
                self.info("PetraCurrent environment not defined. "
                          "Using BeamCurrent")
                petra_current_name = "BeamCurrent"
        except Exception:
            self.info("PetraDevice environment not defined. "
                      "Using petra/globals/keyword as petra device")
            petra_device_name = "petra/globals/keyword"
            petra_current_name = "BeamCurrent"

        try:
            petra_device = PyTango.DeviceProxy(petra_device_name)
        except Exception:
            self.warning(
                "Not able to create proxy to petra device %s. "
                "Not current check is done" % petra_device_name)
            return

        petra_current = petra_device.read_attribute(
            petra_current_name).value

        while petra_current < current_limit:
            self.checkPoint()
            time.sleep(0.5)
            petra_current = petra_device.read_attribute(
                petra_current_name).value


class wait_for_petra(Macro):
    """ wait for machine state: Betrieb-> experimente """

    def run(self):

        try:
            petra_device_name = self.getEnv('PetraDevice')
        except Exception:
            self.info("PetraDevice environment not defined. "
                      "Using petra/globals/keyword as petra device")
            petra_device_name = "petra/globals/keyword"

        try:
            petra_device = PyTango.DeviceProxy(petra_device_name)
        except Exception:
            self.warning(
                "Not able to create proxy to petra device %s. "
                "Not current check is done" % petra_device_name)
            return

        machine_state = petra_device.MachineStateText

        while machine_state.find("Betrieb->Experimente") == -1:
            self.checkPoint()
            time.sleep(0.5)
            machine_state = petra_device.MachineStateText
