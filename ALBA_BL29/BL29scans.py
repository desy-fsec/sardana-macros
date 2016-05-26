#!/usr/bin/env python

"""
Specific scan macros for beamline Alba BL29
"""

import numpy
import PyTango

from sardana.macroserver.macro import Macro, Type, ParamRepeat
from sardana.macroserver.scan import SScan


class ascanp(Macro):
    """
    ascan of energy with 2 different ID polarizations per energy.
    It will perform a regular scan of ID and mono and will move the polarity to
    2 different positions for each energy point
    This is really a mesh, but since we still don't have the energy pseudo for
    controlling both ID and mono energy we have to write this particular macro.
    Please don't use in the future when the energy pseudo is available.
    """

    mono_name = 'energy_mono'
    id_energy_name = 'ideu71_motor_energy'
    id_polarization_name = 'ideu71_motor_polarization'

    param_def = [
        [
            'energy_start',
            Type.Float,
            None,
            'energy1 to measure for each point'],
        [
            'energy_end',
            Type.Float,
            None,
            'energy2 to measure for each point (set to <=0 if not desired)'],
        [
            'intervals',
            Type.Float,
            None,
            'number of intervals'],
        [
            'polarization1',
            Type.Float,
            None,
            'energy1 to measure for each point'],
        [
            'polarization2',
            Type.Float,
            None,
            'energy2 to measure for each point (set to <=0 if not desired)'],
        [
            'integ_time',
            Type.Float,
            None,
            'integration time'],
    ]

    def prepare(self, energy_start, energy_end, intervals,
                polarization1, polarization2, integ_time, *regions, **opts):
        self.name = self.__class__.__name__
        self.energy_start = energy_start
        self.energy_end = energy_end
        self.intervals = intervals
        self.polarization1 = polarization1
        self.polarization2 = polarization2
        self.integ_time = integ_time

        motor_mono = self.getMoveable(self.mono_name)
        motor_id_energy = self.getMoveable(self.id_energy_name)
        motor_id_polarization = self.getMoveable(self.id_polarization_name)
        moveables = [motor_mono, motor_id_energy, motor_id_polarization]

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
        polarizations = [self.polarization1, self.polarization2]

        point_id = 0
        positions = numpy.linspace(self.energy_start, self.energy_end,
                                   self.intervals+1)
        point_id = 0
        for position in positions:
            for polarization in polarizations:
                step['positions'] = [position, position, polarization]
                step['point_id'] = point_id
                point_id += 1
                yield step


class rscan(Macro):
    """rscan.
    Do an absolute scan of the specified motor with different number of
     intervals for each region.
    It uses the gscan framework.

    NOTE: Due to a ParamRepeat limitation, integration time has to be
    specified before the regions.
    """

    hints = {'scan': 'rscan'}
    env = ('ActiveMntGrp',)

    param_def = [
        ['motor',      Type.Motor,   None, 'Motor to move'],
        ['integ_time', Type.Float,   None, 'Integration time'],
        ['start_pos',  Type.Float,   None, 'Start position'],
        ['step_region',
         ParamRepeat([
                        'next_pos',
                        Type.Float,
                        None,
                        'next position'],
                     [
                        'region_nr_intervals',
                        Type.Float,
                        None,
                        'Region number of intervals']),
         None, 'List of tuples: (next_pos, region_nr_intervals']
    ]

    def prepare(self, motor, integ_time, start_pos, *regions, **opts):
        self.name = self.__class__.__name__
        self.integ_time = integ_time
        self.start_pos = start_pos
        self.regions = regions
        self.regions_count = len(self.regions) / 2

        generator = self._generator
        moveables = [motor]
        env = opts.get('env', {})
        constrains = []
        self._gScan = SScan(self, generator, moveables, env, constrains)

    def _generator(self):
        step = {}
        step["integ_time"] = self.integ_time

        point_id = 0
        region_start = self.start_pos
        for r in range(len(self.regions)):
            region_stop, region_nr_intervals = \
                self.regions[r][0], self.regions[r][1]
            positions = numpy.linspace(region_start,
                                       region_stop, region_nr_intervals+1)
            if region_start != self.start_pos:
                # positions must be calculated from the start to the end of the
                # region but after the first region, the 'start' point must not
                # be repeated
                positions = positions[1:]
            for p in positions:
                step['positions'] = [p]
                step['point_id'] = point_id
                point_id += 1
                yield step
            region_start = region_stop

    def run(self, *args):
        for step in self._gScan.step_scan():
            yield step


###############################################################################
# Continuous scans
###############################################################################

class escanct(Macro):
    """
    Energy continuous scan.
    """

    # @todo:would not be necessary if getMotor() worked with other pools motors
    ID_DB = 'alba03:10000/'

    GR_VEL = [294.98525073746316]
    GR_ACC = [0.29981099999999999]
    GR_DEC = [0.29981099999999999]

    ID_PHASE_VEL = [1000, 1000]
    ID_PHASE_ACC = [0.1, 0.1]
    ID_PHASE_DEC = [0.1, 0.1]

    # PLG reduced ID z speeds from 400 to 200 to avoid ID taper problems
    ID_GAP_VEL = [200.0, 200.0, 200.0, 200.0]
    ID_GAP_ACC = [0.1, 0.1, 0.1, 0.1]
    ID_GAP_DEC = [0.1, 0.1, 0.1, 0.1]

    param_def = [
        ['energy_start', Type.Float,   None,
            'start energy'],
        ['energy_final', Type.Float,   None,
            'end energy'],
        ['nr_of_points', Type.Integer, None,
            'number of points'],
        ['integ_time',   Type.Float,   None,
            'integration time'],
        ['move_id',      Type.Boolean, True,
            'move ID energy motor: if set to false only the mono will be moved'
            ' and antiphase and lock_phase parameters will be ignored ('
            'optional True/False, default True)'],
        ['antiphase',    Type.Boolean, False,
            'use antiphase mode (optional True/False, default False)'],
        ['lock_phase',   Type.Boolean, True,
            'move ID phase motors to mid position and do not move during the '
            'scan: in this case only ID gap motors will be moved (optional '
            'True/False, default True)'],
        ]

    env_params = {
        'motor_name': None,  # main motor to scan (usually 'energy_mono')
        'id_energy_names': None,  # list of ID energy names (phase, antiphase)
        'id_phase_name': None,  # name of ID phase pseudomotor
        'id_phase_names': None,  # list of ID phase physical motors
        'id_gap_name': None,  # ID gap motor name
        'id_gap_names': None,  # list of ID gap and taper physical motors
        'gr_name': None,  # name of grating pitch motor
        'doors': None,  # list of doors to allow executing this scan
        'meas': None,   # list of meas to use on each of the allowed doors (set
                        # empty string '' to use env ActiveMntGrp)
        'pos_channel': PyTango.DeviceProxy,  # position channel
        'enc_resolution': None,  # position encoder resolution
        'sample_clock': None,  # clock to be used in counting card
        'phase_min_speed': None,  # min speed for phase motors (35 is ok)
        'TriggerDevice': None,  # just to check that it is define
    }

    def prepare(self, start, final, nr_of_points,
                integ_time, move_id, antiphase, lock_phase, **opts):
        # get arguments
        self.name = self.__class__.__name__
        self.start_pos = start
        self.final_pos = final
        self.nr_of_points = nr_of_points
        self.integ_time = integ_time
        self.move_id = move_id
        self.lock_phase = lock_phase
        self.antiphase = antiphase

        # get macro parameters from environment
        try:
            self.door_name = self.getDoorName().lower()
            # get parameters
            for param_name in self.env_params.keys():
                if not hasattr(self, param_name):
                    value = self.getEnv(
                                param_name,
                                door_name=self.door_name, macro_name=self.name)
                    type_ = self.env_params[param_name]
                    if type_ is not None:
                        value = type_(value)
                    setattr(self, param_name, value)
            self.doors = [door.lower() for door in self.doors]

            # check we got all necessary (debug only)
            for param_name in self.env_params.keys():
                value = getattr(self, param_name)
                self.debug('%s: %s' % (param_name, value))

            # determine which energy motor to use
            self.id_energy_name = self.id_energy_names[int(self.antiphase)]

            # check measurement groups and doors are correctly specified
            if len(self.doors) != len(self.meas):
                msg = 'You must specify measurement group to be used for each'\
                      ' door (set it to \'\' to use environment one)'
                self.error(msg)
                raise Exception(msg)
            try:
                index = self.doors.index(self.door_name)
                self.meas_name = self.meas[index]
                if index == 0:
                    self.main_door = True
                else:
                    self.main_door = False
            except ValueError:
                msg = 'Measurement group not defined for current door'
                self.error(msg)
                raise Exception(msg)

        except Exception, e:
            self.error('Error while getting environment: %s' % str(e))
            raise

        try:
            if self.move_id and self.lock_phase:
                # calculate ID gap and phase displacement (only if move_id)
                idev = PyTango.DeviceProxy(self.ID_DB+self.id_energy_name)
                id_gap_start, id_phase_start = \
                    idev.CalcAllPhysical([self.start_pos])
                id_gap_final, id_phase_final = \
                    idev.CalcAllPhysical([self.final_pos])
                self.id_phase_middle = (id_phase_final + id_phase_start) / 2.0
                self.id_gap_start = id_gap_start
                self.id_gap_final = id_gap_final
                self.id_phase_start = id_phase_start
                self.id_phase_final = id_phase_final
                self.debug('Gap (start,end): %f, %f'
                           % (id_gap_start, id_gap_final))
                self.debug('Phase (start,end): %f, %f'
                           % (id_phase_start, id_phase_final))
                self.debug('Phase (middle): %f'
                           % self.id_phase_middle)
        except Exception, e:
            msg = 'Error while computing gap positions'
            self.error('%s: %s' % (msg, str(e)))
            raise Exception(msg)

    def preConfigure(self):
        self.debug('preConfigure entering...')
        # since sardana channels when written are also read, SampleClockSource
        # can not be read after writing - probably bug in the ds
        ct_device_name = self.pos_channel['channelDevName'].value
        ct_device = PyTango.DeviceProxy(ct_device_name)
        ct_device['SampleClockSource'] = self.sample_clock
        ct_device['SampleTimingType'] = 'SampClk'
        ct_device['ZIndexEnabled'] = False
        # @todo: for some reason PulsesPerRevolution only admits int
        ct_device['PulsesPerRevolution'] = int(self.enc_resolution)
        ct_device['Units'] = 'Ticks'

    def preStart(self):
        self.debug('preStart entering...')

        # initializations
        gr_motor = PyTango.DeviceProxy(self.gr_name)
        initial_position = gr_motor['EncEncin'].value
        self.debug('initial_position: %f' % initial_position)
        self.pos_channel['InitialPosition'] = initial_position

        # if we are told not to move the ID then quit now
        if not self.move_id:
            return

        # in case we were told not to move the phase motor then move it to mid
        # position and then do not move it again during the scan
        if self.lock_phase:
            speeds = self.ID_PHASE_VEL  # max speed and acc for this movement
            accelerations = self.ID_PHASE_ACC
            decelerations = self.ID_PHASE_DEC
            for motor_name, speed, acceleration, deceleration in zip(
                    self.id_phase_names, speeds, accelerations, decelerations):
                motor = PyTango.DeviceProxy(self.ID_DB+motor_name)
                motor.write_attribute('velocity', speed)
                motor.write_attribute('acceleration', acceleration)
                motor.write_attribute('deceleration', deceleration)
            self.debug('Moving phase to middle pos: %f' % self.id_phase_middle)
            macro = 'mv %s %f' % (self.id_phase_name, self.id_phase_middle)
            self.execMacro(macro)
        # in case we are told to move the phase motor it is possible that
        # scanct preparations had set a extremely low and unreachable speed for
        # the phase physical motors: in this case we have to set these speeds
        # to a minimum
        else:
            for phase_motor_name in self.id_phase_names:
                phase_mot = PyTango.DeviceProxy(self.ID_DB+phase_motor_name)
                speed = phase_mot.read_attribute('velocity').value
                if speed < self.phase_min_speed:
                    msg = 'Velocity of %s motor too low (%f). Setting to %f'\
                             % (phase_motor_name, speed, self.phase_min_speed)
                    self.warning(msg)
                    acc = phase_mot.read_attribute('acceleration').value
                    phase_mot.write_attribute('velocity', self.phase_min_speed)
                    phase_mot.write_attribute('acceleration', acc)

    def postScan(self):
        self.debug('postScan entering...')

    def run(self, *args, **kwarg):

        try:
            # backup and set trigger device measurement group if necessary
            if self.meas_name != '':
                key = 'ActiveMntGrp'
                if not self.main_door:  # if using main door use global meas
                    key_set = '.'.join([self.door_name, key])
                else:
                    key_set = key
                meas_back = self.getEnv(key, door_name=self.door_name)
                self.debug('Setting env %s to %s' % (key_set, self.meas_name))
                self.setEnv(key_set, self.meas_name)

            # build scan
            if self.move_id and not self.lock_phase:
                scan_params = [
                    'a2scanct',
                    self.motor_name, self.start_pos, self.final_pos,
                    self.id_energy_name, self.start_pos, self.final_pos,
                    self.nr_of_points, self.integ_time]
            elif self.move_id and self.lock_phase:
                scan_params = [
                    'a2scanct',
                    self.motor_name, self.start_pos, self.final_pos,
                    self.id_gap_name, self.id_gap_start, self.id_gap_final,
                    self.nr_of_points, self.integ_time]
            else:
                scan_params = [
                    'ascanct',
                    self.motor_name, self.start_pos, self.final_pos,
                    self.nr_of_points, self.integ_time]
            scanct, pars = self.createMacro(scan_params)

            # set necessary hooks
            scanct.hooks = [(self.preConfigure, ['pre-configuration']),
                            (self.preStart, ['pre-start']),
                            (self.postScan, ['post-scan'])]
            # run scan
            self.runMacro(scanct)

        # cleanup actions
        finally:
            if self.meas_name != '':
                self.debug('Restoring env %s to %s' % (key_set, meas_back))
                self.setEnv(key_set, meas_back)

            # restore all necessary motor speeds and accelerations
            motors = [self.gr_name]  # gr_pitch will always be restored
            speeds = self.GR_VEL
            accelerations = self.GR_ACC
            decelerations = self.GR_DEC
            if self.move_id:  # ID phases and gaps restored only if moved
                motors.extend([self.ID_DB+mot for mot in self.id_phase_names])
                speeds.extend(self.ID_PHASE_VEL)
                accelerations.extend(self.ID_PHASE_ACC)
                decelerations.extend(self.ID_PHASE_DEC)
                motors.extend([self.ID_DB+mot for mot in self.id_gap_names])
                speeds.extend(self.ID_GAP_VEL)
                accelerations.extend(self.ID_GAP_ACC)
                decelerations.extend(self.ID_GAP_DEC)
            for motor, speed in zip(motors, speeds):
                mot = PyTango.DeviceProxy(motor)
                mot.write_attribute('velocity', speed)
                self.debug('%s speed restored: %f' % (motor, speed))
            for motor, acceleration in zip(motors, accelerations):
                mot = PyTango.DeviceProxy(motor)
                mot.write_attribute('acceleration', acceleration)
                self.debug('%s accel restored: %f' % (motor, acceleration))
            for motor, deceleration in zip(motors, decelerations):
                mot = PyTango.DeviceProxy(motor)
                mot.write_attribute('deceleration', deceleration)
                self.debug('%s decel restored: %f' % (motor, deceleration))

            # move phase: for some reason if you don't do this then phase and
            # gap drift a little after each scan, finally resulting in a big
            # drift after some scans
            if self.move_id:
                #  @todo: use motor API when it works
                #  id_phase = self.getMotor(self.id_phase_name)
                id_phase = PyTango.DeviceProxy(self.ID_DB+self.id_phase_name)
                if (id_phase.read_attribute('position').value -
                        self.id_phase_middle) < 0.1:
                    self.execMacro('mv %s %f' % (self.id_phase_name,
                                                 self.id_phase_final))
                else:
                    self.execMacro('mv %s %f' % (self.id_phase_name,
                                                 self.id_phase_start))
                    self.execMacro('mv %s %f' % (self.id_gap_name,
                                                 self.id_gap_start))


class edscanct(escanct):
    """
    Energy continuous scan specifying energy delta per point
    """

    param_def = [
        ['energy_start', Type.Float,   None,
            'start energy'],
        ['energy_final', Type.Float,   None,
            'end energy'],
        ['delta_e',      Type.Float,   None,
            'delta energy to increase for each point'],
        ['integ_time',   Type.Float,   None,
            'integration time'],
        ['move_id',      Type.Boolean, True,
            'move ID energy motor: if set to false only the mono will be moved'
            ' and antiphase and lock_phase parameters will be ignored ('
            'optional True/False, default True)'],
        ['antiphase',    Type.Boolean, False,
            'use antiphase mode (optional True/False, default False)'],
        ['lock_phase',   Type.Boolean, True,
            'move ID phase motors to mid position and do not move during the '
            'scan: in this case only ID gap motors will be moved (optional '
            'True/False, default True)'],
        ]

    def prepare(self, energy_start, energy_final, delta_e, integ_time,
                move_id, antiphase, lock_phase, **kwargs):
        # dirty hack to get environment parameters from the parent
        class_name = self.__class__.__name__
        # we can do this because we use single inheritance (be careful!)
        self.__class__.__name__ = self.__class__.__mro__[1].__name__
        # call parent's prepare
        points = int((energy_final - energy_start) / delta_e)
        args = [energy_start, energy_final, points, integ_time,
                move_id, antiphase, lock_phase]
        super(self.__class__, self).prepare(*args, **kwargs)
        self.__class__.__name__ = class_name  # restore our class name
        self.name = self.__class__.__name__


class monoscanct(escanct):
    """
    Monochromator continuous scan
    """

    param_def = [
        ['energy_start', Type.Float,   None,
            'start energy'],
        ['energy_final', Type.Float,   None,
            'end energy'],
        ['nr_of_points', Type.Integer, None,
            'number of points'],
        ['integ_time',   Type.Float,   None,
            'integration time'],
        ]

    def prepare(self, *args, **kwargs):
        """
        This scan is the same as the escanct with 1 difference:
        - ID is not moved in under any condition
        """
        # dirty hack to get environment parameters from the parent
        class_name = self.__class__.__name__
        # we can do this because we use single inheritance (be careful!)
        self.__class__.__name__ = self.__class__.__mro__[1].__name__
        # call parent's prepare, but since this is a grating only scan then
        # avoid moving the ID
        move_id = False
        antiphase = False
        lock_phase = False
        args = list(args)
        args.extend([move_id, antiphase, lock_phase])
        super(self.__class__, self).prepare(*args, **kwargs)
        self.__class__.__name__ = class_name  # restore our class name
        self.name = self.__class__.__name__

        # get energy motor name from our own environment parameters
        try:
            param_name = 'motor_name'
            self.motor_name = self.getEnv(param_name, door_name=self.door_name,
                                          macro_name=self.name)
        except Exception, e:
            self.error('Error while getting environment: %s' % str(e))
            raise


class grscanct(escanct):
    """
    Grating continuous scan
    """

    param_def = [
        ['start', Type.Float,   None,
            'start position'],
        ['end', Type.Float,   None,
            'final energy'],
        ['nr_of_points', Type.Integer, None,
            'number of points'],
        ['integ_time',   Type.Float,   None,
            'integration time'],
        ]

    def prepare(self, *args, **kwargs):
        """
        This scan is the same as the escanct with 2 differences:
        - It will scan the grating pitch motor instead of energy motor
        - ID is not moved in under any condition
        """
        # dirty hack to get environment parameters from the parent
        class_name = self.__class__.__name__
        # we can do this because we use single inheritance (be careful!)
        self.__class__.__name__ = self.__class__.__mro__[1].__name__
        # call parent's prepare, but since this is a grating only scan avoid
        # moving the ID
        move_id = False
        antiphase = False
        lock_phase = False
        args = list(args)
        args.extend([move_id, antiphase, lock_phase])
        super(self.__class__, self).prepare(*args, **kwargs)
        self.__class__.__name__ = class_name  # restore our class name
        self.name = self.__class__.__name__

        # get grating pitch motor name from our own environment parameters
        try:
            param_name = 'motor_name'
            self.motor_name = self.getEnv(param_name, door_name=self.door_name,
                                          macro_name=self.name)
        except Exception, e:
            self.error('Error while getting environment: %s' % str(e))
            raise


class timescanct(escanct):
    """
    time continuous scan
    """

    param_def = [
        ['nr_of_points', Type.Integer, None,
            'number of points'],
        ['integ_time',   Type.Float,   None,
            'integration time'],
        ]

    def prepare(self, *args, **kwargs):
        """
        This scan is the same as the escanct with 2 differences:
        - It will use a dummy motor instead of energy motor
        - ID is not moved in under any condition
        """
        # dirty hack to get environment parameters from the parent
        class_name = self.__class__.__name__
        # we can do this because we use single inheritance (be careful!)
        self.__class__.__name__ = self.__class__.__mro__[1].__name__
        points = args[0]
        integ_time = args[1]
        start = 0
        end = 100
        move_id = False
        antiphase = False
        lock_phase = False
        args = [start, end, points, integ_time, move_id, antiphase, lock_phase]
        super(self.__class__, self).prepare(*args, **kwargs)
        self.__class__.__name__ = class_name  # restore our class name
        self.name = self.__class__.__name__

        # get dummy motor name from our own environment parameters
        try:
            param_name = 'motor_name'
            self.motor_name = self.getEnv(param_name, door_name=self.door_name,
                                          macro_name=self.name)
        except Exception, e:
            self.error('Error while getting environment: %s' % str(e))
            raise

    def postScan(self):
        self.debug('postScan entering...')
        motor = PyTango.DeviceProxy(self.motor_name)
        motor.write_attribute('velocity', 1e4)
        motor.write_attribute('acceleration', 1e-3)
        motor.write_attribute('position', self.start_pos)
