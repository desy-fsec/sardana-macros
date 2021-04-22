#!/usr/bin/env python
#
from sardana.macroserver.macro import Macro

class news(Macro):
    """   Outputs the list of most recent changes to Sardana
    """
    def run(self):
        self.output(
            "08.03.2021 HasyUtils.prepareDetectorAttrs(), added attrnow with ArmFlag = True and ImagesPerFile = 1000")
