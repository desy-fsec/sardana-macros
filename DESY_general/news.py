#!/usr/bin/env python
# 
from sardana.macroserver.macro import *
from sardana.macroserver.macro import macro

class news(Macro):
    """   Outputs the list of most recent changes to Sardana
    """
    def run(self):
        self.output( "27.05.2015 fixed mvsa.py to handle ctrl-c'd scans: creates an error")
        self.output( "30.03.2015 Macro wg added. It shows the position of the motors given as argument with the same format as wa")
        self.output( "11.03.2015 Counts attribute changed from Long to Double (SIS3820, VcExecutor, V260)")         
        self.output( "09.03.2015 added the 'news' macro")         

