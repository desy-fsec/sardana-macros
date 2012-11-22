import os
import nxs
import numpy
import math
import time

from sardana.macroserver.macro import Macro, Type
import taurus

class readenv(Macro):
    """reads env"""

    def run(self):
        out = list(['Name', 'Value'])
        env = self.getAllDoorEnv()
        for k,v in env.iteritems():
            self.info('%s %s\n' %(repr(k),repr(v))
#            str_val = repr(v)
#            out.append([str(k), str_val])
#        currentScanFile = str_val[str.index('ScanFile')]
#        self.info('Current Scan File is %s' %currentScanFile)
