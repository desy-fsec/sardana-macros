#!/usr/bin/env python

"""
Macros for restarting p08 servers
"""

__all__ = ["restart_mythenrois",
	   ]

import PyTango, os, sys
import time
from sardana.macroserver.macro import *
from sardana.macroserver.macro import macro


class restart_mythenrois(Macro):
    """restart mythenrois server at p08 """

    def run(self):
        
        starter_devname = "tango/admin/haspp08"
        server_name = "MythenRoIs/EXP" 
        
        macro, pars = self.createMacro('restart_server', starter_devname, server_name)
        self.runMacro(macro)
                
        
            
        
