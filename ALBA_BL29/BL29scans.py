#!/usr/bin/env python

"""
Specific scan macros for Alba BL29
"""

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
