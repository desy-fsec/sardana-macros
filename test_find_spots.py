from sardana.macroserver.macro import macro, iMacro, Macro, Type, ParamRepeat
import PyTango
import numpy, time
import datetime
import taurus
from find_spots import find_spots
#import os


class test_find_spots(Macro):
    '''
    Testing
    '''
    param_def = [['image', Type.String, None, 'Image to process'],
                 ['method', Type.String, None, 'Method for figure of merit'],
                 ]
 
    def run(self, image, method):
#        self.info("user %s" % os.getenv['USER'])
#        self.info("find spots is %s" % find_spots.__file__)
        self.info("      - processing %s ... " % image )
        self.info("      - merith metod: %s" % method)
        result = find_spots( image, method)
        self.info("        * result is: %s " % result )

