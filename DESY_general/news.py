#!/usr/bin/env python
# 
from sardana.macroserver.macro import *
from sardana.macroserver.macro import macro

class news(Macro):
    """   Outputs the list of most recent changes to Sardana
    """
    def run(self):
        self.output( "09.03.2015 added the 'news' macro")         

