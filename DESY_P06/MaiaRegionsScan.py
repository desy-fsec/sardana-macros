#!/bin/env python

import PyTango
import time
from sardana.macroserver.macro import macro, Type, ParamRepeat

__all__ = ["maia_regions_scan"] 

scan = 0
  
class HookPars:
    pass

def hook_post_move(self, hook_pars):

    global scan
    scan = scan + 1
    self.info("Scan " + str(scan) + " of " + str(hook_pars.nscans) + ":")
    # wait for mono 
    time.sleep(10.)
    self.output("Changing energy (wait = 10s)")
    macro,pars = self.createMacro('maia_scan',
        hook_pars.mot0, hook_pars.mot1,
        hook_pars.origin0, hook_pars.origin1,
        hook_pars.range0, hook_pars.range1,
        hook_pars.pitch0, hook_pars.pitch1,
        hook_pars.dwell, hook_pars.group, hook_pars.sample, hook_pars.region,
        "Scan " + str(scan) + "/" + str(hook_pars.nscans) + " " +
            hook_pars.comment)
    self.runMacro(macro)


@macro([
    ['mot0', Type.Moveable, None, 'Internal (fast) motor (axis 0)'],
    ['mot1', Type.Moveable, None, 'External (slow) motor (axis 1)'],
    ['origin0', Type.Float, None, 'Origin position, axis 0'],
    ['origin1', Type.Float, None, 'Origin position, axis 1'],
    ['range0', Type.Float, None, 'Scan extent, axis 0'],
    ['range1', Type.Float, None, 'Scan extent, axis 1'],
    ['pitch0', Type.Float, None, 'Pixel pitch, axis 0'],
    ['pitch1', Type.Float, None, 'Pixel pitch, axis 1'],
    ['group', Type.String, "", 'Logger group'],
    ['sample', Type.String, "", 'Name of sample'],
    ['region', Type.String, "", 'Region within sample'],
    ['comment', Type.String, "", 'Other scan comment'],
    ["scan_regions", ParamRepeat(
        ['energy_start', Type.Float, None, 'First energy in region'],
        ['energy_stop', Type.Float, None, 'Last energy in region position'],
        ['nenergies', Type.Integer, None, 'Number of energies in region'],
        ['dwell', Type.Float, None, 'Dwell time per pixel']),
     None, 'List of scan regions']
])

def maia_regions_scan(self, *list_parameters):
    """ region scans with maia scans """

    energy_motor = self.getObj("energy_all")

    # calculate number of regions and total number of scans
    nregions = len(list_parameters) - 12
    nscans = 0
    for i in range(0, nregions):
        nscans = nscans + list_parameters[i + 12][2]

    # step through energy regions
    for i in range(0, nregions):
        macro,pars = self.createMacro('ascan',
            energy_motor,
            list_parameters[i + 12][0],         # energy_start
            list_parameters[i + 12][1],         # energy_stop
            list_parameters[i + 12][2],         # nenergies
            0.)                                 # integration time set by scan

        # construct energy scan for this region
        hook_pars = HookPars()
        hook_pars.mot0 = list_parameters[0]
        hook_pars.mot1 = list_parameters[1]
        hook_pars.origin0 = list_parameters[2]
        hook_pars.origin1 = list_parameters[3]
        hook_pars.range0 = list_parameters[4]
        hook_pars.range1 = list_parameters[5]
        hook_pars.pitch0 = list_parameters[6]
        hook_pars.pitch1 = list_parameters[7]
        hook_pars.dwell = list_parameters[i + 12][3]
        hook_pars.group = list_parameters[8]
        hook_pars.sample = list_parameters[9]
        hook_pars.region = list_parameters[10]
        hook_pars.comment = list_parameters[11]
        hook_pars.nscans = nscans

        f = lambda : hook_post_move(self, hook_pars)
        macro.hooks = [
            (f, ["post-move"]),
        ]

        # scan enegy, calling maia_scan through hook function
        self.runMacro(macro)


# vim:textwidth=79 tabstop=8 softtabstop=4 shiftwidth=4 expandtab
