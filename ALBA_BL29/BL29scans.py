#!/usr/bin/env python

"""
Specific scan macros for Alba BL29
"""

__all__=['regmagscan', 'ascanp', 'rscan']

import numpy

from sardana.macroserver.macro import Macro, Type, ParamRepeat
from sardana.macroserver.scan import SScan

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
