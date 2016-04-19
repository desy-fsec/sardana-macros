from sardana.macroserver.macro import Macro
import time

class FakeMacroJustWaitWithCheckpoints():
    def run(self):
        # Could be nice to have also info for the progress
        for i in range(10):
            self.info(i)
            time.sleep(1)
            self.pausePoint()

class beam_center(Macro, FakeMacroJustWaitWithCheckpoints):
    def run(self, *args, **kwargs):
        FakeMacroJustWaitWithCheckpoints.run(self)

class beam_quick_realign(Macro, FakeMacroJustWaitWithCheckpoints):
    def run(self, *args, **kwargs):
        FakeMacroJustWaitWithCheckpoints.run(self)

class beam_take_powders(Macro, FakeMacroJustWaitWithCheckpoints):
    def run(self, *args, **kwargs):
        FakeMacroJustWaitWithCheckpoints.run(self)

class beam_anneal(Macro, FakeMacroJustWaitWithCheckpoints):
    def run(self, *args, **kwargs):
        FakeMacroJustWaitWithCheckpoints.run(self)
