"""Macros for interacting with Lima devices"""

from __future__ import print_function
from sardana.macroserver.macro import Macro, Type

__all__ = ["lima_create_RoI2Counter", "lima_create_RoI2Spectrum"]

# import PyTango


class _lima_create_roi(Macro):
    """Create pool device for Lima RoI (counter or spectrum)"""
    param_def = [
        ['tangodevice_name', Type.String, None,
         'Name of the calculation device'],
        ['ctrl_type', Type.String, None, 'Type of element to create'],
        ['poolctrl_name', Type.String, None, 'Name of the Pool Controller'],
        ['newroi_name', Type.String, None, 'Name of the new RoI'],
        ['x', Type.Integer, None, 'x coord. of the RoI origin'],
        ['y', Type.Integer, None, 'y coord. of the RoI origin'],
        ['width', Type.Integer, None, 'width of the RoI'],
        ['height', Type.Integer, None, 'height of the RoI']
    ]

    def run(self, tangodevice_name, ctrl_type, poolctrl_name, newroi_name,
            x, y, width, height):

        calculation_device = self.getDevice(tangodevice_name)

        roi_ids = calculation_device.addNames([newroi_name])

        roi_id = roi_ids[0]

        roi = []
        roi.append(int(roi_id))
        roi.append(int(x))
        roi.append(int(y))
        roi.append(int(width))
        roi.append(int(height))
        calculation_device.setRois(roi)

        pools = self.getPools()
        pool = pools[0]

        args = []
        args.append(str(ctrl_type))
        args.append(str(poolctrl_name))
        args.append(str(roi_id))
        args.append(str(newroi_name))
        self.output(args)
        pool.CreateElement(args)


class lima_create_RoI2Counter(Macro):
    """Create new RoI for getting a counter value"""
    param_def = [
        ['roi2counter_ctrlname', Type.String, None,
         'Name of the Pool Controller'],
        ['newroi_name', Type.String, None, 'Name of the new RoI'],
        ['x', Type.Integer, None, 'x coord. of the RoI origin'],
        ['y', Type.Integer, None, 'y coord. of the RoI origin'],
        ['width', Type.Integer, None, 'width of the RoI'],
        ['height', Type.Integer, None, 'height of the RoI']
    ]

    def run(self, roi2counter_ctrlname, newroi_name, x, y, width, height):

        roi2counter_devicename = self.getEnv('RoI2CounterDeviceName')

        tmp_macro, pars = self.createMacro(
            "_lima_create_roi", roi2counter_devicename,
            "CTExpChannel", roi2counter_ctrlname, newroi_name,
            x, y, width, height)

        self.runMacro(tmp_macro)


class lima_create_RoI2Spectrum(Macro):
    """Create new RoI for getting a spectrum"""
    param_def = [
        ['roi2spectrum_ctrlname', Type.String, None,
         'Name of the Pool Controller'],
        ['newroi_name', Type.String, None, 'Name of the new RoI'],
        ['x', Type.Integer, None, 'x coord. of the RoI origin'],
        ['y', Type.Integer, None, 'y coord. of the RoI origin'],
        ['width', Type.Integer, None, 'width of the RoI'],
        ['height', Type.Integer, None, 'height of the RoI']
    ]

    def run(self, roi2spectrum_ctrlname, newroi_name, x, y, width, height):

        roi2spectrum_devicename = self.getEnv('RoI2SpectrumDeviceName')

        tmp_macro, pars = self.createMacro(
            "_lima_create_roi", roi2spectrum_devicename,
            "OneDExpChannel", roi2spectrum_ctrlname, newroi_name,
            x, y, width, height)

        self.runMacro(tmp_macro)
