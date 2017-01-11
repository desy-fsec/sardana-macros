#!/usr/bin/env python

"""
Specific scan macros for HECTOR (XMCD) end station of beamline Alba BL29
"""

import time
import numpy
import PyTango

from sardana.macroserver.macro import Macro, Type, ParamRepeat, Hookable
from sardana.macroserver.scan import SScan
from sardana.macroserver.scan.gscan import ScanException
from sardana.taurus.core.tango.sardana.pool import Ready


class magscanc(Macro, Hookable):
    """magscanc.
    Do a pseudo continuous scan of the magnetic field while switching the
    energy motor between two different energies. The measures are continuously
    taken at each of the two energy points until the field reaches the final
    target field
    """

    hints = {
        'scan': 'magscanc',
        'allowsHooks': (
            'pre-scan',
            'pre-move',
            'post-move',
            'pre-acq',
            'post-acq',
            'post-step',
            'post-scan')}
    env = ('ActiveMntGrp',)

    param_def = [
        ['motor_energy', Type.Moveable, None, 'Energy motor'],
        ['energy1',      Type.Float,    None, 'energy1 to measure for each '
                                              'point'],
        ['energy2',      Type.Float,    None, 'energy2 to measure for each '
                                              'point (set to <=0 if not '
                                              'desired)'],
        ['motor_magnet', Type.Moveable, None, 'Magnet to scan'],
        ['start_field',  Type.Float,    None, 'Start position'],
        ['end_field',    Type.Float,    None, 'Start position'],
        ['integ_time',   Type.Float,    None, 'Integration time'],
        ['ramp_rate',    Type.Float,    0.0,  'Optional ramp rate to apply to '
                                              'the power supply in Tesla/min '
                                              '(current value will be used if '
                                              'not specified)'],
    ]

    def prepare(self, motor_energy, energy1, energy2, magnet_motor,
                start_field, end_field, integ_time, ramp_rate, **opts):
        self.energy1 = energy1
        self.energy2 = energy2
        self.energies = [energy1, energy2]
        self.field_start = start_field
        self.field_end = end_field
        self.integ_time = integ_time
        self.motor_energy = motor_energy
        self.motor_magnet = magnet_motor
        if ramp_rate > 0.0:
            # ramp rate is in Tesla/min, but the motor understands Tesla/second
            self.motor_magnet.setVelocity(ramp_rate / 60.0)

        self.env = opts.get('env', {})
        constrains = []

        self.moveables = [self.motor_energy, self.motor_magnet]
        self._gScan = SScan(self, self._generator, self.moveables,
                            self.env, constrains)
        self._gScan.scan_loop = self.scan_loop

    def run(self, *args, **kwargs):
        for step in self._gScan.step_scan():
            yield step

    def scan_loop(self):
        self._extra_columns = []

        if hasattr(self, 'getHooks'):
            for hook in self.getHooks('pre-scan'):
                hook()

        self._sum_motion_time = 0
        self._sum_acq_time = 0

        self.env['startts'] = time.time()
        stop = False
        yield 0.0
        # go to start positions and start magnet move
        i = 0
        self.stepUp(i)
        # continue measuring until final field is reached
        while not stop:
            # allow scan to be stopped between points
            self.checkPoint()
            i += 1
            stop = self.stepUp(i)

        if hasattr(self, 'getHooks'):
            for hook in self.getHooks('post-scan'):
                hook()

        yield 100.0

        self.env['motiontime'] = self._sum_motion_time
        self.env['acqtime'] = self._sum_acq_time

    def stepUp(self, step_number):
        # if this is the first step, move to initial positions both motors
        if step_number == 0:
            motion = self.getMotion(self.moveables)
            positions = [self.energy1, self.field_start]
        else:
            motion = self.motor_energy
            positions = [self.energies[step_number % 2]]
        mg = self.getEnv('ActiveMntGrp')
        startts = self.env['startts']

        # pre-move hooks
        if hasattr(self, 'getHooks'):
            for hook in self.getHooks('pre-move-hooks'):
                hook()

        # Move
        self.debug("[START] motion")
        move_start_time = time.time()
        try:
            state, positions = motion.move(positions)
            self._sum_motion_time += time.time() - move_start_time
        except:
            raise
        self.debug("[ END ] motion")

        curr_time = time.time()
        dt = curr_time - startts

        # if this is the first step, then start magnet movement
        if step_number == 0:
            # self.motor_magnet.startMove(0) doesn't set motor state to moving
            self.motor_magnet._start(self.field_end)

        # post-move hooks
        if hasattr(self, 'getHooks'):
            for hook in self.getHooks('post-move-hooks'):
                hook()

        # allow scan to be stopped between motion and data acquisition
        self.checkPoint()

        if state != Ready:
            m = "Scan aborted after problematic motion: " \
                "Motion ended with %s\n" % str(state)
            raise ScanException({'msg': m})

        # pre-acq hooks
        if hasattr(self, 'getHooks'):
            for hook in self.getHooks('pre-acq-hooks'):
                hook()

        positions = list(positions)
        positions.append(self.motor_magnet.getPosition())
        # Acquire data
        self.debug("[START] acquisition")
        mnt_grp = self.getObj(mg, type_class=Type.MeasurementGroup)
        state, data_line = mnt_grp.count(self.integ_time)
        for ec in self._extra_columns:
            data_line[ec.getName()] = ec.read()
        self.debug("[ END ] acquisition")
        self._sum_acq_time += self.integ_time

        # post-acq hooks
        if hasattr(self, 'getHooks'):
            for hook in self.getHooks('post-acq-hooks'):
                hook()

        # Add final moveable positions
        data_line['point_nb'] = step_number
        data_line['timestamp'] = dt
        for i, m in enumerate(self._gScan.moveables):
            data_line[m.moveable.getName()] = positions[i]

        self._gScan.data.addRecord(data_line)

        # post-step hooks
        if hasattr(self, 'getHooks'):
            for hook in self.getHooks('post-step-hooks'):
                hook()

        return (self.motor_magnet.getState() == Ready) and \
               (step_number % 2 == 1)

    def _generator(self):
        """Useless, but required by gscan"""
        step = {}
        step["integ_time"] = self.integ_time
        step['positions'] = [self.energy1]
        step['point_id'] = 0
        yield step


class planemagscan(Macro):
    """
    Plane magnet scan.
    It will perform a plane scan on both Bx and By fields
    """

    mono_pseudomotor_name = 'energy_mono'
    id_pseudomotor_name = 'ideu71_motor_energy'

    xmcd_ct_dev_name = 'XMCD/CT/VM'

    dummy_name = 'dummy_mot01'

    # bx_name = 'dummy_mot02'
    # by_name = 'dummy_mot03'
    bx_name = 'magnet_x'
    by_name = 'magnet_y'

    param_def = [
        ['move_id',    Type.Boolean,  False, 'move also the insertion device, '
                                             'not only the monochromator'],
        ['integ_time', Type.Float,    None,  'integration time'],
        ['energy1',    Type.Float,    None,  'energy1 to measure for each '
                                             'point'],
        ['energy2',    Type.Float,    None,  'energy2 to measure for each '
                                             'point (set to <=0 if not desired'
                                             ')'],

        ['angle',         Type.Float,    None,  'Axis coordinates rotation '
                                                'angle (degrees)'],
        ['bias',          Type.Float,    None,  'Field value orthogonal to '
                                                'movement'],

        ['start_pos',  Type.Float,    None,  'start position'],
        ['step_region', ParamRepeat(
            ['next_pos',            Type.Float, None, 'next position'],
            ['region_nr_intervals', Type.Float, None, 'Region number of '
                                                      'intervals']),
         None, 'List of tuples: (next_pos, region_nr_intervals']
    ]

    def prepare(self, move_id, integ_time, energy1, energy2, angle, bias,
                start_pos, *regions, **opts):
        self.name = self.__class__.__name__
        self.move_id = move_id
        self.integ_time = integ_time
        self.energy1 = energy1
        self.energy2 = energy2

        self.angle = angle
        self.bias = bias

        self.start_pos = start_pos
        self.regions = regions

        # SAFETY PROTECTION 1
        # CHECK BY RAMP RATE
        xmcd_dev = PyTango.DeviceProxy(self.xmcd_ct_dev_name)
        xmcd_dev.write_attribute('ByRampRate', 0.6)
        by_ramprate = xmcd_dev.read_attribute('ByRampRate').value
        if by_ramprate > 0.65:
            raise Exception('oups, by ramp rate is %f' % by_ramprate)

        # SAFETY PROTECTION 2
        # CHECK MAXIMUM POSITION
        region_start = self.start_pos
        for region in range(len(self.regions)):
            region_stop, region_nr_intervals = \
                self.regions[region][0], self.regions[region][1]
            positions = numpy.linspace(region_start,
                                       region_stop, region_nr_intervals+1)
            for position in positions:
                if numpy.sqrt(position**2 + self.bias ** 2) >= 2:
                    raise Exception('MACRO CAN NOT BE EXECUTED, %f position is'
                                    ' forbidden' % position)
            region_start = region_stop

        motor_mono = self.getMoveable(self.mono_pseudomotor_name)
        motor_id = self.getMoveable(self.id_pseudomotor_name)

        motor_dummy = self.getMoveable(self.dummy_name)
        motor_bx = self.getMoveable(self.bx_name)
        motor_by = self.getMoveable(self.by_name)

        moveables = [motor_mono]
        if move_id:
            moveables.append(motor_id)
        moveables.append(motor_dummy)
        moveables.append(motor_bx)
        moveables.append(motor_by)

        generator = self._generator
        env = opts.get('env', {})
        constrains = []
        self._gScan = SScan(self, generator, moveables, env, constrains)

    def run(self, *args):
        for step in self._gScan.step_scan():
            yield step

    def _generator(self):
        step = {}
        step['integ_time'] = self.integ_time
        energies = [self.energy1]
        if self.energy2 > 0:
            energies.append(self.energy2)

        point_id = 0
        region_start = self.start_pos
        for region in range(len(self.regions)):
            region_stop, region_nr_intervals = \
                self.regions[region][0], self.regions[region][1]
            positions = numpy.linspace(region_start,
                                       region_stop, region_nr_intervals+1)
            if region_start != self.start_pos:
                # positions must be calculated from the start to the end of the
                # region but after the first region, the 'start' point must not
                # be repeated
                positions = positions[1:]
            for position in positions:
                for energy in energies:
                    step['positions'] = [energy]
                    if self.move_id:  # only if we also have to move the ID
                        step['positions'].append(energy)

                    position_bx = \
                        self.bias * numpy.cos(numpy.radians(self.angle)) + \
                        numpy.sin(numpy.radians(self.angle)) * position
                    position_by = \
                        -1 * self.bias * numpy.sin(numpy.radians(self.angle)) \
                        + numpy.cos(numpy.radians(self.angle)) * position

                    # DUMMY POSITION (SAME AS regmagscan)
                    step['positions'].append(position)
                    # Position for BX
                    step['positions'].append(position_bx)
                    # Position for BY
                    step['positions'].append(position_by)

                    step['point_id'] = point_id
                    point_id += 1
                    yield step
            region_start = region_stop


class regmagscan(Macro):
    """
    Region magnet scan.
    It will perform a region scan on a specific magnet and will also set the
    energy of the mono to the specified value. Optionally, it will also set the
    insertion device energy value to the same one as the one set for the mono.
    For each point there will one measurement at the specified energy1 and
    optionally another at specified energy2
    """

    mono_pseudomotor_name = 'energy_mono'
    id_pseudomotor_name = 'ideu71_motor_energy'

    param_def = [
        ['move_id',    Type.Boolean,  False, 'move also the insertion device, '
                                             'not only the monochromator'],
        ['magnet',     Type.Moveable, None,  'magnet to scan'],
        ['integ_time', Type.Float,    None,  'integration time'],
        ['energy1',    Type.Float,    None,  'energy1 to measure for each '
                                             'point'],
        ['energy2',    Type.Float,    None,  'energy2 to measure for each '
                                             'point (set to <=0 if not desired'
                                             ')'],
        ['start_pos',  Type.Float,    None,  'start position'],
        ['step_region',
         ParamRepeat(
            ['next_pos',            Type.Float, None, 'next position'],
            ['region_nr_intervals', Type.Float, None, 'Region number of '
                                                      'intervals']),
         None, 'List of tuples: (next_pos, region_nr_intervals']
    ]

    def prepare(self, move_id, magnet, integ_time, energy1, energy2,
                start_pos, *regions, **opts):
        self.name = self.__class__.__name__
        self.move_id = move_id
        self.magnet = magnet
        self.integ_time = integ_time
        self.energy1 = energy1
        self.energy2 = energy2
        self.start_pos = start_pos
        self.regions = regions

        motor_mono = self.getMoveable(self.mono_pseudomotor_name)
        motor_id = self.getMoveable(self.id_pseudomotor_name)
        moveables = [motor_mono]
        if move_id:
            moveables.append(motor_id)
        moveables.append(magnet)

        # move ID to middle position
        if self.energy2 > 0:
            e_middle = float(self.energy1 + self.energy2) / 2.0
        else:
            e_middle = self.energy1
        if not move_id:
            self.execMacro('umv %s %f' % (self.id_pseudomotor_name, e_middle))

        generator = self._generator
        env = opts.get('env', {})
        constrains = []
        self._gScan = SScan(self, generator, moveables, env, constrains)

    def run(self, *args):
        for step in self._gScan.step_scan():
            yield step

    def _generator(self):
        step = {}
        step['integ_time'] = self.integ_time
        energies = [self.energy1]
        if self.energy2 > 0:
            energies.append(self.energy2)

        point_id = 0
        region_start = self.start_pos
        for region in range(len(self.regions)):
            region_stop, region_nr_intervals = \
                self.regions[region][0], self.regions[region][1]
            positions = numpy.linspace(region_start,
                                       region_stop, region_nr_intervals+1)
            if region_start != self.start_pos:
                # positions must be calculated from the start to the end of
                # the region but after the first region, the 'start' point must
                # not be repeated
                positions = positions[1:]
            for position in positions:
                for energy in energies:
                    step['positions'] = [energy]
                    if self.move_id:  # only if we also have to move the ID
                        step['positions'].append(energy)
                    step['positions'].append(position)
                    step['point_id'] = point_id
                    point_id += 1
                    yield step
            region_start = region_stop
