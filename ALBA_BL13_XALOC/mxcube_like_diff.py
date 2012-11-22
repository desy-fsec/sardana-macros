from sardana.macroserver.macro import Macro
import time

class FakeMacroJustWaitWithCheckpoints():
    def run(self):
        # Could be nice to have also info for the progress
        for i in range(10):
            self.info(i)
            time.sleep(1)
            self.pausePoint()

class diff_initialize(Macro, FakeMacroJustWaitWithCheckpoints):
    """ * POWERON ALL MOTORS
        * w = 0, wx,wy,wz = 0, centx,centy = 0, kappa = 0, phi = 0
        * cryodist = IN, bstop = IN, aperture = IN
    """
    def run(self, *args, **kwargs):
        FakeMacroJustWaitWithCheckpoints.run(self)

class diff_home(Macro, FakeMacroJustWaitWithCheckpoints):
    """ * POWERON ALL MOTORS
        * w = 0, wx,wy,wz = 0, centx,centy = 0, kappa = 0, phi = 0
        * cryodist = IN, bstop = OUT, aperture = OUT
    """
    def run(self, *args, **kwargs):
        FakeMacroJustWaitWithCheckpoints.run(self)

class diff_manual_load(Macro, FakeMacroJustWaitWithCheckpoints):
    """ * POWERON ALL MOTORS
        * w = 0, wx,wy,wz = 0, centx,centy = 0, kappa = 0, phi = 0
        * cryodist = OUT, bstop = OUT, aperture = OUT
        ? NOT SURE ABOUT kappa != 0 or omega != 0
    """
    def run(self, *args, **kwargs):
        FakeMacroJustWaitWithCheckpoints.run(self)
