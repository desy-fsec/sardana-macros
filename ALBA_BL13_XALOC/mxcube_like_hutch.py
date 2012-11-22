from sardana.macroserver.macro import Macro
import time

class FakeMacroJustWaitWithCheckpoints():
    def run(self):
        # Could be nice to have also info for the progress
        for i in range(10):
            self.info(i)
            time.sleep(1)
            self.pausePoint()

class hutch_center(Macro, FakeMacroJustWaitWithCheckpoints):
    def run(self, *args, **kwargs):
        FakeMacroJustWaitWithCheckpoints.run(self)

class hutch_center_accept(Macro, FakeMacroJustWaitWithCheckpoints):
    def run(self, *args, **kwargs):
        FakeMacroJustWaitWithCheckpoints.run(self)

class hutch_center_reject(Macro, FakeMacroJustWaitWithCheckpoints):
    def run(self, *args, **kwargs):
        FakeMacroJustWaitWithCheckpoints.run(self)

class hutch_autofocus(Macro, FakeMacroJustWaitWithCheckpoints):
    def run(self, *args, **kwargs):
        FakeMacroJustWaitWithCheckpoints.run(self)

class hutch_snapshot(Macro, FakeMacroJustWaitWithCheckpoints):
    def run(self, *args, **kwargs):
        FakeMacroJustWaitWithCheckpoints.run(self)
