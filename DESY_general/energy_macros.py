"""Energy scan """

from __future__ import print_function
from sardana.macroserver.macro import Macro, Type
import time
import math
from PyTango import DeviceProxy, DevState

__all__ = ["escan", "me"]

flag_no_first = 0


class e2lambda(Macro):
    """ returns the wavelength [Angstr.]: 12398.424/energy"""
    param_def = [
        ['energy', Type.Float, None, 'Energy[eV]']]

    def run(self, energy):
        wavelength = 12398.424 / energy
        self.output("Lambda: %g" % wavelength)


class lambda2e(Macro):
    """ returns the energy [eV]: 12398.424/wavelength"""
    param_def = [
        ['wavelength', Type.Float, None, 'Wavelength[Angstr.]']]

    def run(self, wavelength):
        energy = 12398.424 / wavelength
        self.output("Energy: %g" % energy)


class escan(Macro):
    """Scan energy"""

    param_def = [
        ['start_energy', Type.Float, -999, 'Scan start energy'],
        ['end_energy', Type.Float, -999, 'Scan final energy'],
        ['nr_interv', Type.Integer, -999, 'Number of scan intervals'],
        ['integ_time', Type.Float, -999, 'Integration time'],
        ['fixq', Type.String, "Not",
         'Add fixq  as argument if q has to be kept fixed'],
        ['return_flag', Type.Integer, 1,
         'If 1, motor returns to start position']
    ]

    def energy_pre_move(self):
        global flag_no_first
        self.info("\tCalling move energy hook")

        pos_to_set = self.energy_device.read_attribute("Position").value \
            + flag_no_first * self.step
        flag_no_first = 1

        wavelength = self.lambda_to_e / pos_to_set

        self.diffrac.write_attribute("wavelength", wavelength)

    def hkl_pre_move(self):
        global flag_no_first
        self.info("\tCalling move hkl hook")

        pos_to_set = self.energy_device.read_attribute("Position").value \
            + flag_no_first * self.step
        flag_no_first = 1

        wavelength = self.lambda_to_e / pos_to_set

        self.diffrac.write_attribute("wavelength", wavelength)

        macro, pars = self.createMacro(
            "br", self.h_fix, self.k_fix, self.l_fix, -1, 1)

        self.runMacro(macro)

    def hkl_post_move(self):
        move_flag = 1
        while move_flag:
            move_flag = 0
            time.sleep(1)
            for i in range(0, len(self.angle_dev)):
                # +++ was: if self.angle_dev[i].state() == DevState.MOVING:
                if self.angle_dev[i].getState() == DevState.MOVING:
                    move_flag = 1

    def on_stop(self):
        try:
            self.energy_device.StopMove()
        except Exception:
            pass
        try:
            self.energy_device.Stop()
        except Exception:
            pass

        if self.fixq.lower() == 'fixq':
            self.h_device.Stop()
            self.k_device.Stop()
            self.l_device.Stop()

    def run(self, start_energy, end_energy, nr_interv, integ_time, fixq,
            return_flag):

        if start_energy == -999:
            self.output("Usage:")
            self.output(
                "escan <start_energy> <end_energy> <nr_interv> <integ_time> "
                "[fixq]")
            self.output("Add fixq as argument if q has to be kept fixed "
                        "during the movement")
            return

        if end_energy == -999:
            self.error("end_energy not specified")
            return
        if nr_interv == -999:
            self.error("nr_interv not specified")
            return
        if integ_time == -999:
            self.error("integ_time not specified")
            return

        self.lambda_to_e = 12398.424  # Amstrong * eV

        energy_device = self.getObj("mnchrmtr")
        energy_device_name = "mnchrmtr"
        try:   # if the device exists gives error if comparing to None
            if energy_device is None:
                self.warning("mnchrmtr device does not exist.")
                self.warning(
                    "Trying to get the energy device name from the "
                    "EnergyDevice environment variable")
                try:
                    energy_device_name = self.getEnv('EnergyDevice')
                except Exception:
                    self.error("EnergyDevice not defined. Macro exiting")
                    return
                try:
                    energy_device = self.getObj(energy_device_name)
                except Exception:
                    self.error(
                        "Unable to get energy device %s. Macro exiting"
                        % energy_device_name)
                    return
        except Exception:
            pass

        # store the current position from the energy device to return
        #     to it after the scan

        saved_initial_position = energy_device.read_attribute("Position").value

        self.energy_device = energy_device

        self.diffrac_defined = 0
        try:
            diffrac_name = self.getEnv('DiffracDevice')
            self.diffrac = self.getDevice(diffrac_name)
            self.diffrac_defined = 1
            self.initial_autoenergy = self.diffrac.read_attribute(
                "autoenergyupdate").value
        except Exception:
            self.debug("DiffracDevice not defined or not found")

        if fixq.lower() == "fixq":
            # Repeat it here for getting an error if fixq mode
            diffrac_name = self.getEnv('DiffracDevice')
            self.diffrac = self.getDevice(diffrac_name)
            pseudo_motor_names = []
            for motor in self.diffrac.hklpseudomotorlist:
                pseudo_motor_names.append(motor.split(' ')[0])

            self.angle_dev = []
            for motor in self.diffrac.motorlist:
                self.angle_dev.append(self.getDevice(motor.split(' ')[0]))

            self.h_device = self.getDevice(pseudo_motor_names[0])
            self.k_device = self.getDevice(pseudo_motor_names[1])
            self.l_device = self.getDevice(pseudo_motor_names[2])

            self.h_fix = self.h_device.read_attribute("Position").value
            self.k_fix = self.k_device.read_attribute("Position").value
            self.l_fix = self.l_device.read_attribute("Position").value

            self.diffrac.write_attribute("autoenergyupdate", 0)

            wavelength = self.lambda_to_e / \
                self.energy_device.read_attribute("Position").value
            self.diffrac.write_attribute("wavelength", wavelength)
        else:
            if self.diffrac_defined == 1:
                self.diffrac.write_attribute("autoenergyupdate", 1)

        # set the motor to the initial position for having
        #   the right position at the first hook

        self.output("Moving energy to the start value ...")
        self.execMacro("mv %s %f" % (energy_device_name, start_energy))

        macro, pars = self.createMacro(
            "ascan", energy_device, start_energy, end_energy, nr_interv,
            integ_time)

        self.step = abs(end_energy - start_energy) / nr_interv

        self.fixq = fixq
        if fixq.lower() == "fixq":

            macro_hkl, pars = self.createMacro(
                "br", self.h_fix, self.k_fix, self.l_fix, -1)

            self.runMacro(macro_hkl)

            macro.appendHook((self.hkl_pre_move, ["pre-move"]))
            macro.appendHook((self.hkl_post_move, ["post-move"]))
        else:
            if self.diffrac_defined:
                macro.appendHook((self.energy_pre_move, ["pre-move"]))

        self.runMacro(macro)

        # Return the energy to the initial value

        if return_flag:
            self.output(
                "Returning the energy to the value before the scan ...")
            self.energy_device.write_attribute(
                "Position", saved_initial_position)
            if fixq.lower() == "fixq":
                wavelength = self.lambda_to_e / saved_initial_position

                self.diffrac.write_attribute("wavelength", wavelength)
                macro_hkl, pars = self.createMacro(
                    "br", self.h_fix, self.k_fix, self.l_fix, -1, 0)

                self.runMacro(macro_hkl)
            if self.diffrac_defined == 1:
                self.diffrac.write_attribute(
                    "autoenergyupdate", self.initial_autoenergy)
            while self.energy_device.getState() == DevState.MOVING:
                time.sleep(1)


class me(Macro):
    """Move energy. Diffractometer wavelength is set"""

    param_def = [
        ['energy', Type.Float, -999, 'Energy to set']
    ]

    def run(self, energy):

        if energy == -999:
            self.output("Usage:")
            self.output("me <energy>")
            self.output("Move energy. Diffractometer wavelength is set")
            return

        try:
            energyfmb_device = self.getObj("mnchrmtr")
            energyfmb_device_name = "mnchrmtr"
        except Exception:
            self.warning("mnchrmtr device does not exist.")
            self.warning(
                "Trying to get the fmb device name from the "
                "EnergyFMB environment variable")
            try:
                energyfmb_device_name = self.getEnv('EnergyFMB')
            except Exception:
                self.error("EnergyFMB not defined. Macro exiting")
                return
            try:
                energyfmb_device = self.getObj(energyfmb_device_name)
            except Exception:
                self.error("Unable to get fmb device %s. Macro exiting"
                           % energyfmb_device_name)
                return

        try:
            energy_device = self.getObj("mnchrmtr")
            energy_device_name = "mnchrmtr"
        except Exception:
            self.warning("mnchrmtr device does not exist.")
            self.warning(
                "Trying to get the energy device name from the "
                "EnergyDevice environment variable")
            try:
                energy_device_name = self.getEnv('EnergyDevice')
            except Exception:
                self.error("EnergyDevice not defined. Macro exiting")
                return
            try:
                energy_device = self.getObj(energy_device_name)
            except Exception:
                self.error(
                    "Unable to get energy device %s. Macro exiting"
                    % energy_device_name)
                return

        fmb_tango_device = DeviceProxy(
            energyfmb_device.TangoDevice)
        try:
            fmb_tango_device.write_attribute("PseudoChannelCutMode", 0)
        except Exception:
            pass

        flag_diffrac = 0
        try:
            diffrac_name = self.getEnv('DiffracDevice')
            diffrac_device = self.getDevice(diffrac_name)

            initial_autoenergy = diffrac_device.read_attribute(
                "autoenergyupdate").value
            diffrac_device.write_attribute("autoenergyupdate", 0)

            flag_diffrac = 1

            lambda_to_e = 12398.424   # Amstrong * eV
            wavelength = lambda_to_e / energy
            diffrac_device.write_attribute("wavelength", wavelength)
        except Exception:
            pass

        self.execMacro("mv", [[energy_device, energy]])

        if flag_diffrac:
            diffrac_device.write_attribute(
                "autoenergyupdate", initial_autoenergy)


class escanexafs_general(Macro):
    """ Energy regions scan"""

    param_def = [
        ['integ_time', Type.Float, -999, 'Integration time'],
        ["scan_regions", [
            ['estart', Type.Float, None, 'Start energy region'],
            ['estop', Type.Float, None, 'Stop energy region'],
            ['estep', Type.Float, None, 'Energy step in region']],
         None, 'List of scan regions']]

    def run(self, integ_time, scan_regions):

        # calculate number of regions
        nregions = len(scan_regions)

        for i in range(0, nregions):
            nenergies = int(
                math.fabs(scan_regions[i][1] - scan_regions[i][0]) / scan_regions[i][2])
            if nenergies < 1:
                nenergies = 1
            macro, pars = self.createMacro(
                'escan',
                scan_regions[i][0],         # energy_start
                scan_regions[i][1],         # energy_stop
                nenergies,                  # number of steps
                integ_time,
                "Not", 0)

            self.runMacro(macro)


class escanexafs(Macro):
    """ Energy regions scan"""

    param_def = [
        ['estart1', Type.Float, -999, 'Start energy region 1'],
        ['estop1', Type.Float, -999, 'Stop energy region 1'],
        ['estep1', Type.Float, -999, 'Energy step in region 1'],
        ['estart2', Type.Float, -999, 'Start energy region 2'],
        ['estop2', Type.Float, -999, 'Stop energy region 2'],
        ['estep2', Type.Float, -999, 'Energy step in region 2'],
        ['estart3', Type.Float, -999, 'Start energy region 3'],
        ['estop3', Type.Float, -999, 'Stop energy region 3'],
        ['estep3', Type.Float, -999, 'Energy step in region 3'],
        ['integ_time', Type.Float, -999, 'Integration time']]

    def run(self, estart1, estop1, estep1, estart2, estop2, estep2, estart3,
            estop3, estep3, integ_time):

        macro, pars = self.createMacro(
            'escanexafs_general', integ_time,
            [[estart1, estop1, estep1],
             [estart2, estop2, estep2],
             [estart3, estop3, estep3]])
        self.runMacro(macro)


class escanxmcd(Macro):
    """Energy scan with variable energy step size"""

    param_def = [
        ['start_energy', Type.Float, None, 'Scan start energy'],
        ['end_energy', Type.Float, None, 'Scan final energy'],
        ['integ_time', Type.Float, None, 'Integration time'],
        ['estep_min', Type.Float, None, 'Minimum step size']
    ]

    def move_energy(self):
        self.debug("\tCalling move energy hook")

        current_energy = self.energy_device.read_attribute("Position").value
        estep = (1. / 3.) * math.sqrt(math.fabs(current_energy - self.middle_energy))

        if estep < self.estep_min:
            estep = self.estep_min
        self.execMacro("mv %s %f" % (
            self.energy_device_name, current_energy + estep))

    def run(self, start_energy, end_energy, integ_time, estep_min):

        self.energy_device = self.getObj("mnchrmtr")
        self.energy_device_name = "mnchrmtr"
        self.estep_min = estep_min

        try:   # if the device exists gives error if comparing to None
            if self.energy_device is None:
                self.warning("mnchrmtr device does not exist.")
                self.warning(
                    "Trying to get the energy device name from the "
                    "EnergyDevice environment variable")
                try:
                    self.energy_device_name = self.getEnv('EnergyDevice')
                except Exception:
                    self.error("EnergyDevice not defined. Macro exiting")
                    return
                try:
                    self.energy_device = self.getObj(self.energy_device_name)
                except Exception:
                    self.error(
                        "Unable to get energy device %s. Macro exiting"
                        % self.energy_device_name)
                    return
        except Exception:
            pass

        # set the motor to the initial position for having
        #       the right position at the first hook

        self.debug("Moving energy to the start value ...")
        self.execMacro("mv %s %f" % (self.energy_device_name, start_energy))

        self.middle_energy = (end_energy + start_energy) / 2.

        # compute number of steps to reach the end energy
        if start_energy < end_energy:
            start = start_energy
            end = end_energy
        else:
            start = end_energy
            end = start_energy

        current_energy = start
        nr_interv = 0
        while current_energy < end:
            nr_interv = nr_interv + 1
            estep = (1. / 3.) * math.sqrt(
                math.fabs(current_energy - self.middle_energy))
            if estep < self.estep_min:
                estep = self.estep_min
            current_energy = current_energy + estep

        nr_interv = nr_interv + 1

        self.info("Number of scan points %d" % nr_interv)

        macro, pars = self.createMacro(
            "ascan", "exp_dmy01", start_energy, end_energy, nr_interv,
            integ_time)

        macro.hooks = [(self.move_energy, ["post-acq"]), ]

        self.runMacro(macro)
