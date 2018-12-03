#!/usr/bin/env python

"""
Specific scan macros for MARES (RSXS) end station of beamline Alba BL29
"""

import numpy

from sardana.macroserver.macro import Macro, Type
from sardana.macroserver.scan import SScan
from sardana.macroserver.scan.gscan import ScanException


class qzscan(Macro):
    """
    This will perform a constant qz scan. User must provide 3 values for sample
    position, detector position and energy which determine the target value of
    qz. The macro will then scan at the requested energies but keeping the
    target qz value by setting the sample and detector positions appropriately.
    """

    sample_motor_name = 'energy_mono'

    hints = {
        'scan': 'qzscan',
        'allowsHooks': (
            'pre-scan',
            'pre-move',
            'post-move',
            'pre-acq',
            'post-acq',
            'post-step',
            'post-scan'
        )
    }

    param_def = [
        ['sample0',      Type.Float, None, 'sample motor position for example '
                                           'energy'],
        ['detector0',    Type.Float, None, 'detector motor position for '
                                           'example energy'],
        ['energy0',      Type.Float, None, 'example energy'],
        ['energy_start', Type.Float, None, 'start energy'],
        ['energy_end',   Type.Float, None, 'end energy'],
        ['intervals',    Type.Float, None, 'number of intervals'],
        ['integ_time',   Type.Float, None, 'Integration time'],
    ]

    def prepare(self, sample0, detector0, energy0, energy_start,
                energy_end, intervals, integ_time, **opts):
        self.sample0 = sample0
        self.detector0 = detector0
        self.energy0 = energy0
        self.energy_start = energy_start
        self.energy_end = energy_end
        self.intervals = intervals
        self.integ_time = integ_time

        # get macro variables from global environment
        env_prefix = 'Macros.%s.' % self.__class__.__name__
        environment = self.getGlobalEnv()
        try:
            motor_energy_name = environment[
                '%s%s' % (env_prefix, 'motor_energy_name')]
            motor_energyid_name = environment[
                '%s%s' % (env_prefix, 'motor_energyid_name')]
            motor_sample_name = environment[
                '%s%s' % (env_prefix, 'motor_sample_name')]
            motor_detector_name = environment[
                '%s%s' % (env_prefix, 'motor_detector_name')]
        except KeyError, e:
            msg = 'Unable to recover motor names from environment. Please '\
                  'define %s* environment variables' % env_prefix
            raise ScanException({'msg': msg})
        except Exception, e:
            msg = 'Unexpected exception while trying to recover motor names '\
                  'from environment:\n%s' % str(e)
            raise ScanException({'msg': msg})

        # get moveables
        try:
            motor_energy = self.getMoveable(motor_energy_name)
            motor_energyid = self.getMoveable(motor_energyid_name)
            motor_sample = self.getMoveable(motor_sample_name)
            motor_detector = self.getMoveable(motor_detector_name)
            moveables = [motor_energy, motor_energyid,
                         motor_sample, motor_detector]
        except Exception, e:
            msg = 'Unable to access motors %s and/or %s' % \
                  (motor_sample_name, motor_detector_name)
            self.error(msg)
            raise ScanException({'msg': msg})

        # build scan
        self.build_scan(moveables, opts)

    def build_scan(self, moveables, opts):
        """The scan will start at the moment you create the _gScan variable and
        hence we have to define this extra method if we want child classes to
        reuse the prepare method"""
        # build scan
        generator = self._generator
        env = opts.get('env', {})
        constrains = []
        self._gScan = SScan(self, generator, moveables, env, constrains)

    def run(self, *args, **kwargs):
        for step in self._gScan.step_scan():
            yield step

    def _generator(self):
        step = {}
        step['integ_time'] = self.integ_time
        point_id = 0
        energies = numpy.linspace(self.energy_start,
                                  self.energy_end, self.intervals+1)
        if 0.0 in energies:
            msg = 'One of the energies in the scan would be 0.0'
            self.error(msg)
            raise ScanException({'msg': msg})
        point_id = 0
        for energy in energies:
            sample_position = self.get_sample_at_qfix(energy)
            detector_position = self.get_detector_at_qfix(energy)
            step['positions'] = [energy, energy,
                                 sample_position, detector_position]
            step['point_id'] = point_id
            point_id += 1
            yield step

    def get_sample_at_qfix(self, energy):
        """
        Given the 3 user provided values for sample position, detector position
        and energy (which determine a value of qz) and a new target energy this
        function returns the position to which sample should be moved to in
        order to keep qz constant
        """
        sample = 180.0/numpy.pi * \
            numpy.arcsin(
                (self.energy0/energy) * numpy.sin(self.sample0*numpy.pi/180.0)
            )
        return sample

    def get_detector_at_qfix(self, energy):
        """
        Given the 3 user provided values for sample position, detector position
        and energy (which determine a value of qz) and a new target energy this
        function returns the position to which detector should be moved to in
        order to keep qz constant
        """
        detector = \
            180.0/numpy.pi * numpy.arcsin(
                (self.energy0/energy) *
                numpy.sin(self.sample0*numpy.pi/180.0)
            ) \
            + \
            180.0/numpy.pi * numpy.arcsin(
                (self.energy0/energy) *
                numpy.sin(numpy.pi/180.0*(self.detector0-self.sample0))
            )
        return detector


class qxqzscan(qzscan):
    """
    This will perform a constant qx qz scan. User must provide 3 values for
    sample position, detector position and energy which determine the target
    value of qx and qz. The macro will then scan at the requested energies but
    keeping the target qx and qz values by setting the sample and detector
    positions appropriately.
    """

    sample_motor_name = 'energy_mono'

    hints = {
        'scan': 'qxqzscan',
        'allowsHooks': (
            'pre-scan',
            'pre-move',
            'post-move',
            'pre-acq',
            'post-acq',
            'post-step',
            'post-scan'
        )
    }

    param_def = [
        ['sample0',      Type.Float, None, 'sample motor position for example '
                                           'energy'],
        ['detector0',    Type.Float, None, 'detector motor position for '
                                           'example energy'],
        ['energy0',      Type.Float, None, 'example energy'],
        ['energy_start', Type.Float, None, 'start energy'],
        ['energy_end',   Type.Float, None, 'end energy'],
        ['intervals',    Type.Float, None, 'number of intervals'],
        ['integ_time',   Type.Float, None, 'Integration time'],
    ]

    # h*c (h = 4.1357e-15 eV*s, c = 2.997925e17 nm/s)
    HC = 4.1357e-15 * 2.997925e17

    def prepare(self, sample0, detector0, energy0, energy_start, energy_end,
                intervals, integ_time, **opts):
        super(qxqzscan, self).prepare(sample0, detector0, energy0,
                                      energy_start, energy_end, intervals,
                                      integ_time, **opts)

    def build_scan(self, moveables, opts):
        # define extra variables
        wave_length = self.HC / self.energy0
        k0 = 2 * numpy.pi / wave_length
        self.offset = self.detector0 - self.sample0
        self.qx_fixed = k0 * (numpy.cos(
                                numpy.pi/180.0*(self.detector0-self.sample0)) -
                              numpy.cos(
                                numpy.pi/180.0*self.sample0))
        self.qz_fixed = k0 * (numpy.sin(
                                numpy.pi/180.0*(self.detector0-self.sample0)) +
                              numpy.sin(
                                numpy.pi/180.0*self.sample0))

        # build scan
        generator = self._generator
        env = opts.get('env', {})
        constrains = []
        self._gScan = SScan(self, generator, moveables, env, constrains)

    def get_sample_at_qfix(self, energy):
        """
        Given the 3 user provided values for sample position, detector position
        and energy (which determine a value of qx and qz) and a new target
        energy this function returns the position to which sample should be
        moved to in order to keep qx and qz constant
        """
        wave_length = self.HC / energy
        k0 = 2 * numpy.pi / wave_length
        sample = 0.5 * (numpy.pi/180.0 *
                        numpy.arccos(
                            1.0 -
                            0.5 * (numpy.power(self.qx_fixed, 2) +
                                   numpy.power(self.qz_fixed, 2)) /
                            numpy.power(k0, 2)
                        ) + self.offset)
        return sample

    def get_detector_at_qfix(self, energy):
        """
        Given the 3 user provided values for sample position, detector position
        and energy (which determine a value of qx and qz) and a new target
        energy this function returns the position to which detector should be
        moved to in order to keep qx and qz constant
        """
        wave_length = self.HC / energy
        k0 = 2 * numpy.pi / wave_length
        detector = 180.0 / numpy.pi * numpy.arccos(
                                        1.0 -
                                        0.5 * (numpy.power(self.qx_fixed, 2) +
                                               numpy.power(self.qz_fixed, 2)) /
                                        numpy.power(k0, 2))
        return detector
