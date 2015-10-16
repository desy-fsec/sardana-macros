from sardana.macroserver.macro import macro, iMacro, Macro, Type, ParamRepeat
import os


class test_find_spots(Macro):
    '''
    Testing
    '''
    param_def = [[]]
 
    def run(self, image, method):
        self.info("user %s" % os.environ['USER'])

