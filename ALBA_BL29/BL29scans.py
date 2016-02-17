#!/usr/bin/env python

"""
Specific scan macros for Alba BL29
"""

import time
import numpy
import PyTango

from sardana.macroserver.macro import Macro, Type, ParamRepeat, Hookable
from sardana.macroserver.scan import SScan
from sardana.macroserver.scan.gscan import ScanException
from sardana.taurus.core.tango.sardana.pool import Ready



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
        ['move_id',    Type.Boolean,  False, 'move also the insertion device, not only the monochromator'],
        ['magnet',     Type.Moveable, None,  'magnet to scan'],
        ['integ_time', Type.Float,    None,  'integration time'],
        ['energy1',    Type.Float,    None,  'energy1 to measure for each point'],
        ['energy2',    Type.Float,    None,  'energy2 to measure for each point (set to <=0 if not desired)'],
        ['start_pos',  Type.Float,    None,  'start position'],
        ['step_region',
         ParamRepeat(['next_pos',            Type.Float, None, 'next position'],
                     ['region_nr_intervals', Type.Float, None, 'Region number of intervals']),
         None, 'List of tuples: (next_pos, region_nr_intervals']
    ]

    def prepare(self, move_id, magnet, integ_time, energy1, energy2, start_pos, *regions, **opts):
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

        #move ID to middle position
        if self.energy2 > 0:
            e_middle=float(self.energy1+self.energy2)/2.0
        else:
            e_middle=self.energy1
        if move_id == False:
            self.execMacro('umv '+self.id_pseudomotor_name+' %f' %e_middle)

        generator=self._generator
        env=opts.get('env',{})
        constrains=[]
        self._gScan=SScan(self, generator, moveables, env, constrains)

    def run(self,*args):
        for step in self._gScan.step_scan():
            yield step

    def _generator(self):
        step = {}
        step['integ_time'] =  self.integ_time
        energies = [self.energy1]
        if self.energy2 > 0:
            energies.append(self.energy2)

        point_id = 0
        region_start = self.start_pos
        for region in range(len(self.regions)):
            region_stop, region_nr_intervals = self.regions[region][0], self.regions[region][1]
            positions = numpy.linspace(region_start, region_stop, region_nr_intervals+1)
            if region_start != self.start_pos:
                # positions must be calculated from the start to the end of the region
                # but after the first region, the 'start' point must not be repeated
                positions = positions[1:]
            for position in positions:
                for energy in energies:
                    step['positions'] = [energy]
                    if self.move_id: #only if we also have to move the insertion device
                        step['positions'].append(energy)
                    step['positions'].append(position)
                    step['point_id'] = point_id
                    point_id += 1
                    yield step
            region_start = region_stop


class ascanp(Macro):
    """
    ascan of energy with 2 different ID polarizations per energy.
    It will perform a regular scan of ID and mono and will move the polarity to 2 different positions for each energy point
    This is really a mesh, but since we still don't have the energy pseudo for controlling both ID and mono energy
    we have to write this particular macro.
    Please don't use in the future when the energy pseudo is available.
    """

    mono_name = 'energy_mono'
    id_energy_name = 'ideu71_motor_energy'
    id_polarization_name = 'ideu71_motor_polarization'

    param_def = [
        ['energy_start',  Type.Float,    None,  'energy1 to measure for each point'],
        ['energy_end',    Type.Float,    None,  'energy2 to measure for each point (set to <=0 if not desired)'],
        ['intervals',     Type.Float,    None,  'number of intervals'],
        ['polarization1', Type.Float,    None,  'energy1 to measure for each point'],
        ['polarization2', Type.Float,    None,  'energy2 to measure for each point (set to <=0 if not desired)'],
        ['integ_time',    Type.Float,    None,  'integration time'],
    ]

    def prepare(self, energy_start, energy_end, intervals, polarization1, polarization2, integ_time, *regions, **opts):
        self.name          = self.__class__.__name__
        self.energy_start  = energy_start
        self.energy_end    = energy_end
        self.intervals = intervals
        self.polarization1 = polarization1
        self.polarization2 = polarization2
        self.integ_time    = integ_time

        motor_mono = self.getMoveable(self.mono_name)
        motor_id_energy = self.getMoveable(self.id_energy_name)
        motor_id_polarization = self.getMoveable(self.id_polarization_name)
        moveables = [motor_mono, motor_id_energy, motor_id_polarization]

        generator=self._generator
        env=opts.get('env',{})
        constrains=[]
        self._gScan=SScan(self, generator, moveables, env, constrains)

    def run(self,*args):
        for step in self._gScan.step_scan():
            yield step

    def _generator(self):
        step = {}
        step['integ_time'] =  self.integ_time
        polarizations = [self.polarization1, self.polarization2]

        point_id = 0
        positions = numpy.linspace(self.energy_start, self.energy_end, self.intervals+1)
        point_id = 0
        for position in positions:
            for polarization in polarizations:
                step['positions'] = [position, position, polarization]
                step['point_id'] = point_id
                point_id += 1
                yield step


class rscan(Macro):
    """rscan.
    Do an absolute scan of the specified motor with different number of intervals for each region.
    It uses the gscan framework.

    NOTE: Due to a ParamRepeat limitation, integration time has to be
    specified before the regions.
    """

    hints = {'scan' : 'rscan'}
    env = ('ActiveMntGrp',)

    param_def = [
        ['motor',      Type.Motor,   None, 'Motor to move'],
        ['integ_time', Type.Float,   None, 'Integration time'],
        ['start_pos',  Type.Float,   None, 'Start position'],
        ['step_region',
         ParamRepeat(['next_pos',  Type.Float,   None, 'next position'],
                     ['region_nr_intervals',  Type.Float,   None, 'Region number of intervals']),
         None, 'List of tuples: (next_pos, region_nr_intervals']
    ]

    def prepare(self, motor, integ_time, start_pos, *regions, **opts):
        self.name='rscan'
        self.integ_time = integ_time
        self.start_pos = start_pos
        self.regions = regions
        self.regions_count = len(self.regions)/2

        generator=self._generator
        moveables=[motor]
        env=opts.get('env',{})
        constrains=[]
        self._gScan=SScan(self, generator, moveables, env, constrains)

    def _generator(self):
        step = {}
        step["integ_time"] =  self.integ_time

        point_id = 0
        region_start = self.start_pos
        for r in range(len(self.regions)):
            region_stop, region_nr_intervals = self.regions[r][0], self.regions[r][1]
            positions = numpy.linspace(region_start, region_stop, region_nr_intervals+1)
            if region_start != self.start_pos:
                # positions must be calculated from the start to the end of the region
                # but after the first region, the 'start' point must not be repeated
                positions = positions[1:]
            for p in positions:
                step['positions'] = [p]
                step['point_id'] = point_id
                point_id += 1
                yield step
            region_start = region_stop

    def run(self,*args):
        for step in self._gScan.step_scan():
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

    #bx_name = 'dummy_mot02'
    #by_name = 'dummy_mot03'
    bx_name = 'magnet_x'
    by_name = 'magnet_y'

    param_def = [
        ['move_id',    Type.Boolean,  False, 'move also the insertion device, not only the monochromator'],
        ['integ_time', Type.Float,    None,  'integration time'],
        ['energy1',    Type.Float,    None,  'energy1 to measure for each point'],
        ['energy2',    Type.Float,    None,  'energy2 to measure for each point (set to <=0 if not desired)'],

        ['angle',         Type.Float,    None,  'Axis coordinates rotation angle (degrees)'],
        ['bias',          Type.Float,    None,  'Field value orthogonal to movement'],

        ['start_pos',  Type.Float,    None,  'start position'],
        ['step_region',
         ParamRepeat(['next_pos',            Type.Float, None, 'next position'],
                     ['region_nr_intervals', Type.Float, None, 'Region number of intervals']),
         None, 'List of tuples: (next_pos, region_nr_intervals']

    ]

    def prepare(self, move_id, integ_time, energy1, energy2, angle, bias, start_pos, *regions, **opts):
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
            raise Exception('oups, by ramp rate is %f'%by_ramprate)

        # SAFETY PROTECTION 2
        # CHECK MAXIMUM POSITION
        region_start = self.start_pos
        for region in range(len(self.regions)):
            region_stop, region_nr_intervals = self.regions[region][0], self.regions[region][1]
            positions = numpy.linspace(region_start, region_stop, region_nr_intervals+1)
            for position in positions:
                if numpy.sqrt(position**2 + self.bias ** 2) >= 1:
                    raise Exception('MACRO CAN NOT BE EXECUTED, %f position is forbidden' % position)
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

        generator=self._generator
        env=opts.get('env',{})
        constrains=[]
        self._gScan=SScan(self, generator, moveables, env, constrains)

    def run(self,*args):
        for step in self._gScan.step_scan():
            yield step

    def _generator(self):
        step = {}
        step['integ_time'] =  self.integ_time
        energies = [self.energy1]
        if self.energy2 > 0:
            energies.append(self.energy2)

        point_id = 0
        region_start = self.start_pos
        for region in range(len(self.regions)):
            region_stop, region_nr_intervals = self.regions[region][0], self.regions[region][1]
            positions = numpy.linspace(region_start, region_stop, region_nr_intervals+1)
            if region_start != self.start_pos:
                # positions must be calculated from the start to the end of the region
                # but after the first region, the 'start' point must not be repeated
                positions = positions[1:]
            for position in positions:
                for energy in energies:
                    step['positions'] = [energy]
                    if self.move_id: #only if we also have to move the insertion device
                        step['positions'].append(energy)

                    position_bx = self.bias * numpy.cos(numpy.radians(self.angle)) + numpy.sin(numpy.radians(self.angle)) * position
                    position_by = -1 * self.bias * numpy.sin(numpy.radians(self.angle)) + numpy.cos(numpy.radians(self.angle)) * position

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


class magscanc(Macro, Hookable):
    """magscanc.
    Do a pseudo continuous scan of the magnetic field while switching the energy motor between
    two different energies. The measures are continuously taken at each of the two energy points
    until the field reaches the final target field
    """


    hints = { 'scan' : 'magscanc', 'allowsHooks': ('pre-scan', 'pre-move', 'post-move', 'pre-acq', 'post-acq', 'post-step', 'post-scan') }
    env = ('ActiveMntGrp',)

    param_def = [
        ['motor_energy', Type.Moveable, None, 'Energy motor'],
        ['energy1',      Type.Float,    None, 'energy1 to measure for each point'],
        ['energy2',      Type.Float,    None, 'energy2 to measure for each point (set to <=0 if not desired)'],
        ['motor_magnet', Type.Moveable, None, 'Magnet to scan'],
        ['start_field',  Type.Float,    None, 'Start position'],
        ['end_field',    Type.Float,    None, 'Start position'],
        ['integ_time',   Type.Float,    None, 'Integration time'],
        ['ramp_rate',    Type.Float,    0.0,  'Optional ramp rate to apply to the power supply in Tesla/min (current value will be used if not specified)'],
    ]

    def prepare(self, motor_energy, energy1, energy2, magnet_motor, start_field, end_field, integ_time, ramp_rate, **opts):
        self.energy1 = energy1
        self.energy2 = energy2
        self.energies = [energy1, energy2]
        self.field_start = start_field
        self.field_end = end_field
        self.integ_time = integ_time
        self.motor_energy = motor_energy
        self.motor_magnet = magnet_motor
        if ramp_rate > 0.0:
            self.motor_magnet.setVelocity(ramp_rate / 60.0) #ramp rate is in Tesla/min, but the motor understands Tesla/second

        self.env=opts.get('env',{})
        constrains=[]

        self.moveables = [self.motor_energy, self.motor_magnet]
        self._gScan=SScan(self, self._generator, self.moveables, self.env, constrains)
        self._gScan.scan_loop = self.scan_loop

    def run(self, *args, **kwargs):#motor_energy, energy1, energy2, magnet_motor, start_field, end_field, integ_time, ramp_rate):
        for step in self._gScan.step_scan():
            yield step

    def scan_loop(self):
        self._extra_columns = []

        if hasattr(self, 'getHooks'):
            for hook in self.getHooks('pre-scan'):
                hook()

        self._sum_motion_time = 0
        self._sum_acq_time = 0

        self.env['startts'] =  time.time()
        stop = False
        yield 0.0
        #go to start positions and start magnet move
        i = 0
        self.stepUp(i)
        #continue measuring until final field is reached
        while not stop:
            # allow scan to be stopped between points
            self.checkPoint()
            i+=1
            stop = self.stepUp(i)

        if hasattr(self, 'getHooks'):
            for hook in self.getHooks('post-scan'):
                hook()

        yield 100.0

        self.env['motiontime'] = self._sum_motion_time
        self.env['acqtime'] = self._sum_acq_time

    def stepUp(self,step_number):
        #if this is the first step, move to initial positions both motors
        if step_number == 0:
            motion = self.getMotion(self.moveables)
            positions = [self.energy1, self.field_start]
        else:
            motion = self.motor_energy
            positions = [self.energies[step_number%2]]
        mg = self.getEnv('ActiveMntGrp')
        startts = self.env['startts']

        #pre-move hooks
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

        #if this is the first step, then start magnet movement
        if step_number==0:
            self.motor_magnet._start(self.field_end) #self.motor_magnet.startMove(0) doesn't set motor state to moving

        #post-move hooks
        if hasattr(self, 'getHooks'):
            for hook in self.getHooks('post-move-hooks'):
                hook()

        # allow scan to be stopped between motion and data acquisition
        self.checkPoint()

        if state != Ready:
            m = "Scan aborted after problematic motion: " \
                "Motion ended with %s\n" % str(state)
            raise ScanException({ 'msg' : m })

        #pre-acq hooks
        if hasattr(self, 'getHooks'):
            for hook in self.getHooks('pre-acq-hooks'):
                hook()

        positions=list(positions)
        positions.append(self.motor_magnet.getPosition())
        # Acquire data
        self.debug("[START] acquisition")
        mnt_grp = self.getObj(mg,type_class=Type.MeasurementGroup)
        state, data_line = mnt_grp.count(self.integ_time)
        for ec in self._extra_columns:
            data_line[ec.getName()] = ec.read()
        self.debug("[ END ] acquisition")
        self._sum_acq_time += self.integ_time

        #post-acq hooks
        if hasattr(self, 'getHooks'):
            for hook in self.getHooks('post-acq-hooks'):
                hook()

        # Add final moveable positions
        data_line['point_nb'] = step_number
        data_line['timestamp'] = dt
        for i, m in enumerate(self._gScan.moveables):
            data_line[m.moveable.getName()] = positions[i]

        self._gScan.data.addRecord(data_line)

        #post-step hooks
        if hasattr(self, 'getHooks'):
            for hook in self.getHooks('post-step-hooks'):
                hook()

        return (self.motor_magnet.getState()==Ready) and (step_number%2==1)

    def _generator(self):
        """Useless, but required by gscan"""
        step = {}
        step["integ_time"] =  self.integ_time
        step['positions'] = [self.energy1]
        step['point_id'] = 0
        yield step



################################################################################
# Continuous scans
################################################################################

class energy_scanct(Macro):
    energy_name = 'energy_mono'
    id_energy_names = ['ideu71_motor_energy', 'ideu71_energy_plus']
    gr_name = 'gr_pitch'
    mg_name = 'bl29_cont_sdd'
    mg_name = 'bl29_cont'
    pos_channel_name = 'energy_mono_ct'
    encoder_resolution = 1
    sample_clock = "/Dev1/PFI36"
    trigger_device = 'bl29/ct/ni-ibl2902-00'
    # allow to run on main and admin doors
    allowed_doors = ['bl29/door/01', 'bl29/door/02']

    param_def = [
        ['energy_start',Type.Float, None,'start energy'],
        ['energy_final',Type.Float, None,'end energy'],
        ['nr_of_points',Type.Integer,None,'number of points'],
        ['integ_time', Type.Float, None,'integration time for each point'],
        ['antiphase', Type.Boolean, False,'use antiphase mode (optional True/False, False by default)'],
        ]

    def getActiveMntGrpVarName(self):
        return 'ActiveMntGrp'

    def getTriggerDeviceVarName(self):
        return 'TriggerDevice'

    def validate(self):
        '''Validates if macro is correctly called e.g. if it is called 
        on the right door
        '''
        door_name = self.getDoorName().lower()
        if door_name not in self.allowed_doors:
            msg = '%s can not run on door %s' % (self.name, door_name)
            raise RuntimeError(msg)

    def prepare(self, start, final, nr_of_points, integ_time, antiphase, **opts):
        self.name = self.__class__.__name__
        self.validate()
        self.start_pos = start
        self.final_pos = final
        self.nr_of_points = nr_of_points
        self.integ_time = integ_time
        self.id_energy_name = self.id_energy_names[int(antiphase)]
        motor_energy = self.getMoveable(self.energy_name)
        motor_id_energy = self.getMoveable(self.id_energy_name)
        moveables = [motor_energy, motor_id_energy]

    def preConfigure(self):
        self.debug("preConfigure entering...")
        self.pos_channel = PyTango.DeviceProxy(self.pos_channel_name)

        #since sardana channels when written are also read, 
        #SampleClockSource can not be read after writing - probably bug in the ds 

        counterDevName = self.pos_channel['channelDevName'].value
        counterDev = PyTango.DeviceProxy(counterDevName)
        counterDev['SampleClockSource'] = self.sample_clock
        counterDev['SampleTimingType'] = 'SampClk'
        counterDev['ZIndexEnabled'] = False
        counterDev['PulsesPerRevolution'] = self.encoder_resolution
        counterDev['Units'] = 'Ticks'

    def preStart(self):
        self.debug('preStart entering...')
        gr_motor = PyTango.DeviceProxy(self.gr_name)
        initial_position = gr_motor['EncEncin'].value
        self.debug('initial_position = %f' % initial_position)
        self.pos_channel['InitialPosition'] = initial_position
        y_motors = ['alba03:10000/ideu71_motor_y1', 'alba03:10000/ideu71_motor_y2']
        for y_motor in y_motors:
            y = PyTango.DeviceProxy(y_motor)
            vel = y.read_attribute('velocity').value
            if vel < 35:
                msg = ('Velocity of %s motor is %f and is too low.' +
                       ' Setting it to 35') % (y_motor,vel)
                self.warning(msg)
                accT = y.read_attribute('acceleration').value
                y.write_attribute('velocity', 35)
                y.write_attribute('acceleration',accT)

    def run(self, *arg, **kwarg):
        old_mg = self.getEnv('ActiveMntGrp', door_name=self.getDoorName())
        old_trigger_device = self.getEnv('TriggerDevice', door_name=self.getDoorName())
        self.debug('Setting trigger device to %s' % self.trigger_device)
        self.setEnv(self.getTriggerDeviceVarName(), self.trigger_device)
        self.debug('Setting measurement group to %s' % self.mg_name)
        self.setEnv(self.getActiveMntGrpVarName(), self.mg_name)
        try:
            a2scanct, pars = self.createMacro(['a2scanct',
                                              self.energy_name, 
                                              self.start_pos,
                                              self.final_pos,
                                              self.id_energy_name, 
                                              self.start_pos,
                                              self.final_pos,
                                              self.nr_of_points,
                                              self.integ_time])

            a2scanct.hooks = [ (self.preConfigure, ['pre-configuration']),
                               (self.preStart, ['pre-start']) ]

            self.runMacro(a2scanct)
        finally:
            self.setEnv(self.getActiveMntGrpVarName(), old_mg)
            self.setEnv(self.getTriggerDeviceVarName(), old_trigger_device)
            motors = ['alba03:10000/ideu71_motor_y1', 
                      'alba03:10000/ideu71_motor_y2', 
                      'alba03:10000/ideu71_motor_z1', 
                      'alba03:10000/ideu71_motor_z2', 
                      'alba03:10000/ideu71_motor_z3', 
                      'alba03:10000/ideu71_motor_z4', 
                      'gr_pitch']
            #speeds = [ 1000, 1000, 400.0, 400.0, 400.0, 400.0, 294.98525073746316 ]
            speeds = [ 1000, 1000, 200.0, 200.0, 200.0, 200.0, 294.98525073746316 ] #PLG reduced ID speeds to 200 to avoid ID taper problems
            accelerations = [ 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.29981099999999999 ]
            decelerations = accelerations
            for motor, speed in zip(motors, speeds):
                m = PyTango.DeviceProxy(motor)
                m.write_attribute('velocity',speed)
            for motor, acceleration in zip(motors, accelerations):
                m = PyTango.DeviceProxy(motor)
                m.write_attribute('acceleration',acceleration)
            for motor, deceleration in zip(motors, decelerations):
                m = PyTango.DeviceProxy(motor)
                m.write_attribute('deceleration',deceleration)


class energy_scanct_mares(energy_scanct):
    energy_name = 'energy_mono'
    id_energy_names = ['ideu71_motor_energy', 'ideu71_energy_plus']
    gr_name = 'gr_pitch'
    mg_name = 'bl29_cont_mares'
    pos_channel_name = 'energy_mono_ct'
    encoder_resolution = 1
    sample_clock = '/Dev1/PFI28'
    trigger_device = 'bl29/ct/ni-ibl2902-02'
    # allow to run on mares and admin doors
    allowed_doors = ['bl29/door/03', 'bl29/door/02']

    def getActiveMntGrpVarName(self):
        return 'bl29/door/03.ActiveMntGrp'

    def getTriggerDeviceVarName(self):
        return 'bl29/door/03.TriggerDevice'


class energy_gap_scanct(Macro):

    energy_name = 'energy_mono'
    id_db = 'alba03:10000'
    id_energy_names = ['ideu71_motor_energy', 'ideu71_energy_plus']
    id_phase_name = 'ideu71_motor_phase' # pm/ideu71_pseudomotor_y/1
    id_gap_name = 'ideu71_motor_gap' # pm/ideu71_pseudomotor_z/1
    gr_name = 'gr_pitch'
    mg_name = 'bl29_cont'
    pos_channel_name = 'energy_mono_ct'
    encoder_resolution = 1
    sample_clock = "/Dev1/PFI36"

    param_def = [
        ['energy_start',Type.Float, None,'start energy'],
        ['energy_final',Type.Float, None,'end energy'],
        ['nr_of_points',Type.Integer,None,'number of points'],
        ['integ_time', Type.Float, None,'integration time for each point'],
        ['antiphase', Type.Boolean, False,'use antiphase mode (optional True/False, False by default)'],
        ]

    def prepare(self, start, final, nr_of_points, integ_time, antiphase, **opts):
        self.name = self.__class__.__name__
        self.start_pos = start
        self.final_pos = final
        self.nr_of_points = nr_of_points
        self.integ_time = integ_time
        self.id_energy_name = self.id_energy_names[int(antiphase)]
        motor_energy = self.getMoveable(self.energy_name)
        motor_id_energy = self.getMoveable(self.id_energy_name)
        moveables = [motor_energy, motor_id_energy]
        # calculate gap and phase displacement
        id_energy_name = self.id_energy_names[0]
        id_energy_full_name = '/'.join([self.id_db, id_energy_name])
        id_energy = PyTango.DeviceProxy(id_energy_full_name)
        self.id_gap_start_pos, id_phase_start_pos = id_energy.CalcAllPhysical([start])
        self.id_gap_final_pos, id_phase_final_pos = id_energy.CalcAllPhysical([final])

        #if (id_phase_final_pos>0) & (id_phase_start_pos>0):
            #sig = +1
        #elif (id_phase_final_pos<0) & (id_phase_start_pos<0):
            #sig = -1
        #elif id_phase_final_pos>id_phase_start_pos:
            #sig = +1
        #else:
            #sig = -1
        self.id_phase_middle = (id_phase_final_pos + id_phase_start_pos) / 2.0
        self.debug('gap_start = %f; gap_finish = %f' % (self.id_gap_start_pos, self.id_gap_final_pos))
        self.debug('phase_start = %f; phase_finish = %f' % (id_phase_start_pos, id_phase_final_pos))
        self.debug('phase_middle = %f' % self.id_phase_middle)

    def preConfigure(self):
        self.debug("preConfigure entering...")
        self.pos_channel = PyTango.DeviceProxy(self.pos_channel_name)

        #since sardana channels when written are also read,
        #SampleClockSource can not be read after writing - probably bug in the ds

        counterDevName = self.pos_channel['channelDevName'].value
        counterDev = PyTango.DeviceProxy(counterDevName)
        counterDev['SampleClockSource'] = self.sample_clock
        counterDev['SampleTimingType'] = 'SampClk'
        counterDev['ZIndexEnabled'] = False
        counterDev['PulsesPerRevolution'] = self.encoder_resolution
        counterDev['Units'] = 'Ticks'


    def preStart(self):
        self.debug('preStart entering...')
        gr_motor = PyTango.DeviceProxy(self.gr_name)
        initial_position = gr_motor['EncEncin'].value
        self.debug('initial_position = %f' % initial_position)
        self.pos_channel['InitialPosition'] = initial_position
        y_motors = ['alba03:10000/ideu71_motor_y1', 'alba03:10000/ideu71_motor_y2']
        # move phase to the middle of scan range
        phase_motor_names = ['alba03:10000/ideu71_motor_y1',
                             'alba03:10000/ideu71_motor_y2']
        speeds = [ 1000, 1000]
        accelerations = [ 0.1, 0.1]
        decelerations = accelerations
        for motor, speed, acceleration, deceleration in zip(phase_motor_names, speeds, accelerations, decelerations):
            m = PyTango.DeviceProxy(motor)
            m.write_attribute('velocity',speed)
            m.write_attribute('acceleration',acceleration)
            m.write_attribute('deceleration',deceleration)
        self.debug('Moving phase to middle positions: %f' % self.id_phase_middle)
        self.execMacro('mv %s %f' % (self.id_phase_name, self.id_phase_middle))

    def run(self, *arg, **kwarg):
        old_mg = self.getEnv('ActiveMntGrp')
        var_name = 'ActiveMntGrp'
        self.setEnv(var_name, self.mg_name)
        try:
            a2scanct, pars = self.createMacro(['a2scanct',
                                              self.energy_name,
                                              self.start_pos,
                                              self.final_pos,
                                              self.id_gap_name,
                                              self.id_gap_start_pos,
                                              self.id_gap_final_pos,
                                              self.nr_of_points,
                                              self.integ_time])

            a2scanct.hooks = [ (self.preConfigure, ['pre-configuration']),
                               (self.preStart, ['pre-start']) ]

            self.runMacro(a2scanct)
        finally:
            self.setEnv(var_name, old_mg)
            motors = ['alba03:10000/ideu71_motor_y1', 'alba03:10000/ideu71_motor_y2', 'alba03:10000/ideu71_motor_z1', 'alba03:10000/ideu71_motor_z2', 'alba03:10000/ideu71_motor_z3', 'alba03:10000/ideu71_motor_z4', 'gr_pitch']
            #speeds = [ 1000, 1000, 400.0, 400.0, 400.0, 400.0, 294.98525073746316 ]
            speeds = [ 1000, 1000, 200.0, 200.0, 200.0, 200.0, 294.98525073746316 ] #PLG reduced ID gap speeds to avoid ID taper problems
            accelerations = [ 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.29981099999999999 ]
            decelerations = accelerations
            for motor, speed in zip(motors, speeds):
                m = PyTango.DeviceProxy(motor)
                m.write_attribute('velocity',speed)
            for motor, acceleration in zip(motors, accelerations):
                m = PyTango.DeviceProxy(motor)
                m.write_attribute('acceleration',acceleration)
            for motor, deceleration in zip(motors, decelerations):
                m = PyTango.DeviceProxy(motor)
                m.write_attribute('deceleration',deceleration)


class mono_scanct(Macro):

    energy_name = 'energy_mono'
    gr_name = 'gr_pitch'
    mg_name = 'BL29_CONT'
    pos_channel_name = 'energy_mono_ct'
    encoder_resolution = 1
    sample_clock = "/Dev1/PFI36"

    param_def = [
        ['energy_start',Type.Float, None,'start energy'],
        ['energy_final',Type.Float, None,'end energy'],
        ['nr_of_points',Type.Integer,None,'number of points'],
        ['integ_time', Type.Float, None,'integration time for each point'],
        ['antiphase', Type.Boolean, False,'use antiphase mode (optional True/False, False by default)'],
        ]

    def prepare(self, start, final, nr_of_points, integ_time, antiphase, **opts):
        self.name = self.__class__.__name__
        self.start_pos = start
        self.final_pos = final
        self.nr_of_points = nr_of_points
        self.integ_time = integ_time
        motor_energy = self.getMoveable(self.energy_name)
        moveables = [motor_energy]

    def preConfigure(self):
        self.debug("preConfigure entering...")
        self.pos_channel = PyTango.DeviceProxy(self.pos_channel_name)

        #since sardana channels when written are also read, 
        #SampleClockSource can not be read after writing - probably bug in the ds 

        counterDevName = self.pos_channel['channelDevName'].value
        counterDev = PyTango.DeviceProxy(counterDevName)
        counterDev['SampleClockSource'] = self.sample_clock
        counterDev['SampleTimingType'] = 'SampClk'
        counterDev['ZIndexEnabled'] = False
        counterDev['PulsesPerRevolution'] = self.encoder_resolution
        counterDev['Units'] = 'Ticks'

    def preStart(self):
        self.debug('preStart entering...')
        gr_motor = PyTango.DeviceProxy(self.gr_name)
        initial_position = gr_motor['EncEncin'].value
        self.debug('initial_position = %f' % initial_position)
        self.pos_channel['InitialPosition'] = initial_position

    def run(self, *arg, **kwarg):
        old_mg = self.getEnv('ActiveMntGrp')
        var_name = 'ActiveMntGrp' 
        self.setEnv(var_name, self.mg_name)
        try:
            ascanct, pars = self.createMacro(['ascanct',
                                              self.energy_name, 
                                              self.start_pos,
                                              self.final_pos,
                                              self.nr_of_points,
                                              self.integ_time])

            ascanct.hooks = [ (self.preConfigure, ['pre-configuration']),
                               (self.preStart, ['pre-start']) ]

            self.runMacro(ascanct)
        finally:
            self.setEnv(var_name, old_mg)
            motors = ['gr_pitch']
            speeds = [ 294.98525073746316 ]
            accelerations = [ 0.29981099999999999 ]
            decelerations = accelerations
            for motor, speed in zip(motors, speeds):
                m = PyTango.DeviceProxy(motor)
                m.write_attribute('velocity',speed)
            for motor, acceleration in zip(motors, accelerations):
                m = PyTango.DeviceProxy(motor)
                m.write_attribute('acceleration',acceleration)
            for motor, deceleration in zip(motors, decelerations):
                m = PyTango.DeviceProxy(motor)
                m.write_attribute('deceleration',deceleration)


class grpitch_scanct(Macro):

    energy_name = 'gr_pitch'
    gr_name = 'gr_pitch'
    mg_name = 'BL29_cont'
    pos_channel_name = 'energy_mono_ct'
    encoder_resolution = 1
    sample_clock = "/Dev1/PFI36"

    param_def = [
        ['energy_start',Type.Float, None,'start energy'],
        ['energy_final',Type.Float, None,'end energy'],
        ['nr_of_points',Type.Integer,None,'number of points'],
        ['integ_time', Type.Float, None,'integration time for each point'],
        ['antiphase', Type.Boolean, False,'use antiphase mode (optional True/False, False by default)'],
        ]

    def prepare(self, start, final, nr_of_points, integ_time, antiphase, **opts):
        self.name = self.__class__.__name__
        self.start_pos = start
        self.final_pos = final
        self.nr_of_points = nr_of_points
        self.integ_time = integ_time
        motor_energy = self.getMoveable(self.energy_name)
        moveables = [motor_energy]

    def preConfigure(self):
        self.debug("preConfigure entering...")
        self.pos_channel = PyTango.DeviceProxy(self.pos_channel_name)

        #since sardana channels when written are also read, 
        #SampleClockSource can not be read after writing - probably bug in the ds 

        counterDevName = self.pos_channel['channelDevName'].value
        counterDev = PyTango.DeviceProxy(counterDevName)
        counterDev['SampleClockSource'] = self.sample_clock
        counterDev['SampleTimingType'] = 'SampClk'
        counterDev['ZIndexEnabled'] = False
        counterDev['PulsesPerRevolution'] = self.encoder_resolution
        counterDev['Units'] = 'Ticks'

    def preStart(self):
        self.debug('preStart entering...')
        gr_motor = PyTango.DeviceProxy(self.gr_name)
        initial_position = gr_motor['EncEncin'].value
        self.debug('initial_position = %f' % initial_position)
        self.pos_channel['InitialPosition'] = initial_position

    def run(self, *arg, **kwarg):
        old_mg = self.getEnv('ActiveMntGrp')
        var_name = 'ActiveMntGrp' 
        self.setEnv(var_name, self.mg_name)
        try:
            ascanct, pars = self.createMacro(['ascanct',
                                              self.energy_name, 
                                              self.start_pos,
                                              self.final_pos,
                                              self.nr_of_points,
                                              self.integ_time])

            ascanct.hooks = [ (self.preConfigure, ['pre-configuration']),
                               (self.preStart, ['pre-start']) ]

            self.runMacro(ascanct)
        finally:
            self.setEnv(var_name, old_mg)
            motors = ['gr_pitch']
            speeds = [ 294.98525073746316 ]
            accelerations = [ 0.29981099999999999 ]
            decelerations = accelerations
            for motor, speed in zip(motors, speeds):
                m = PyTango.DeviceProxy(motor)
                m.write_attribute('velocity',speed)
            for motor, acceleration in zip(motors, accelerations):
                m = PyTango.DeviceProxy(motor)
                m.write_attribute('acceleration',acceleration)
            for motor, deceleration in zip(motors, decelerations):
                m = PyTango.DeviceProxy(motor)
                m.write_attribute('deceleration',deceleration)


class useless_scanct(Macro):

    energy_name = 'dummy_mot01'
    gr_name = 'dummy_mot01'
    mg_name = 'BL29_SCANC3_BRANCH_3'
    pos_channel_name = 'energy_mono_ct'
    encoder_resolution = 1
    sample_clock = "/Dev1/PFI36"

    param_def = [
        ['energy_start',Type.Float, None,'start energy'],
        ['energy_final',Type.Float, None,'end energy'],
        ['nr_of_points',Type.Integer,None,'number of points'],
        ['integ_time', Type.Float, None,'integration time for each point'],
        ['antiphase', Type.Boolean, False,'use antiphase mode (optional True/False, False by default)'],
        ]

    def prepare(self, start, final, nr_of_points, integ_time, antiphase, **opts):
        self.name = self.__class__.__name__
        self.start_pos = start
        self.final_pos = final
        self.nr_of_points = nr_of_points
        self.integ_time = integ_time
        motor_energy = self.getMoveable(self.energy_name)
        moveables = [motor_energy]

    def preConfigure(self):
        self.debug("preConfigure entering...")
        self.pos_channel = PyTango.DeviceProxy(self.pos_channel_name)

        #since sardana channels when written are also read, 
        #SampleClockSource can not be read after writing - probably bug in the ds 

        counterDevName = self.pos_channel['channelDevName'].value
        counterDev = PyTango.DeviceProxy(counterDevName)
        counterDev['SampleClockSource'] = self.sample_clock
        counterDev['SampleTimingType'] = 'SampClk'
        counterDev['ZIndexEnabled'] = False
        counterDev['PulsesPerRevolution'] = self.encoder_resolution
        counterDev['Units'] = 'Ticks'

    def preStart(self):
        self.debug('preStart entering...')
        gr_motor = PyTango.DeviceProxy(self.gr_name)
        self.pos_channel['InitialPosition'] = 0

    def run(self, *arg, **kwarg):
        old_mg = self.getEnv('ActiveMntGrp')
        var_name = 'ActiveMntGrp' 
        self.output("Setting meas ... %s", self.mg_name)
        self.setEnv(var_name, self.mg_name)
        try:
            ascanct, pars = self.createMacro(['ascanct',
                                              self.energy_name, 
                                              self.start_pos,
                                              self.final_pos,
                                              self.nr_of_points,
                                              self.integ_time])

            ascanct.hooks = [ (self.preConfigure, ['pre-configuration']),
                               (self.preStart, ['pre-start']) ]

            self.runMacro(ascanct)
        finally:
            self.setEnv(var_name, old_mg)
            motors = ['dummy_mot01']
            speeds = [ 294.98525073746316 ]
            accelerations = [ 0.29981099999999999 ]
            decelerations = accelerations
            for motor, speed in zip(motors, speeds):
                m = PyTango.DeviceProxy(motor)
                m.write_attribute('velocity',speed)
            for motor, acceleration in zip(motors, accelerations):
                m = PyTango.DeviceProxy(motor)
                m.write_attribute('acceleration',acceleration)
            for motor, deceleration in zip(motors, decelerations):
                m = PyTango.DeviceProxy(motor)
                m.write_attribute('deceleration',deceleration)
