#!/bin/env python

import PyTango
import time
from sardana.macroserver.macro import macro, Type, ParamRepeat

__all__ = ["maia_3d_scan"] 

scan = 0
 
enc_dict = {"p06/hydramotor/exp.01":"enc0", "p06/hydramotor/exp.04":"enc1", "p06/hydramotor/exp.02":"enc2"}

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
    ['dwell', Type.Float, None, 'Dwell time per pixel'],
    ['group', Type.String, "", 'Logger group'],
    ['sample', Type.String, "", 'Name of sample'],
    ['region', Type.String, "", 'Region within sample'],
    ['comment', Type.String, "", 'Other scan comment'],
    ['mot2', Type.Moveable, None, 'External  motor'],
    ['start_pos2', Type.Float, None, 'Start position external motor'],
    ['end_pos2', Type.Float, None, 'End position exernal motor'],
    ['nb_points2', Type.Integer, None, 'Number of scan points']
])

def maia_3d_scan(self, *list_parameters):
    """ scan with maia scans """

    maia_dimension2 = self.getEnv('MaiaDimension2Device')
    MaiaDimension2 = PyTango.DeviceProxy(maia_dimension2)
    MaiaDimension2.PositionSource = enc_dict[list_parameters[13].TangoDevice]
    MaiaDimension2.PixelPitch = (list_parameters[15] - list_parameters[14])/(list_parameters[16] -1)
    MaiaDimension2.PixelOrigin = list_parameters[14]
    MaiaDimension2.PixelCoordExtent = list_parameters[16] 
    
    macro,pars = self.createMacro('ascan',
                                  #mot2,
				  list_parameters[13],		#outer Loop motor (mot2)
                                  list_parameters[14],         # start_pos
                                  list_parameters[15],         # end_pos
                                  list_parameters[16],         # nb_points
                                  0.)                          # integration time set by scan
    
    # construct maia scan for this region
    hook_pars = HookPars()
    hook_pars.mot0 = list_parameters[0]
    hook_pars.mot1 = list_parameters[1]
    hook_pars.origin0 = list_parameters[2]
    hook_pars.origin1 = list_parameters[3]
    hook_pars.range0 = list_parameters[4]
    hook_pars.range1 = list_parameters[5]
    hook_pars.pitch0 = list_parameters[6]
    hook_pars.pitch1 = list_parameters[7]
    hook_pars.dwell = list_parameters[8]
    hook_pars.group = list_parameters[9]
    hook_pars.sample = list_parameters[10]
    hook_pars.region = list_parameters[11]
    hook_pars.comment = list_parameters[12]
    hook_pars.nscans = list_parameters[16]
   # hook_pars.nscans = nb_points2
    
    f = lambda : hook_post_move(self, hook_pars)
    macro.hooks = [
        (f, ["post-move"]),
        ]
    
    # scan enegy, calling maia_scan through hook function
    self.runMacro(macro)

