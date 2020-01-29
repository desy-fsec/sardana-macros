#!/usr/bin/env python
# 
__all__ = ["GalilRS"]

from sardana.macroserver.macro import Macro, Type
import HasyUtils
import PyTango
import time, math

class GalilRS(Macro):
    """
    Resets GalilMotors
    - the current motor positions are stored, opMode: -x
    - the macro sends a RS (reset) to the Galil controller
    - the macro waits for the motors to reach their final positions
    - finally motors are moved to their original positions, opMode: -x

    The -f option resets the device ignoring the initial positions. This
    option is intended to be used, if the positions cannot be read out.

    The positions to be reached after RS are hard coded for each BL
      haspp09: abs(pos) == 5
    """

    def run( self):
        #
        # check the opMode parameter
        #
        #
        # posPowerOn is used to sense that the RS procedure is completed
        #
        pass


