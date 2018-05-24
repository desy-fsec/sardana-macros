#!/usr/bin/env python

"""
the general hooks/conditions/on_stop macro interface:
the feature is used in gscan.py, scan.py and macro.py
"""

__all__ = ["gc_enable", "gc_enable", "gc_isEnabled",
           "gs_enable", "gs_enable", "gs_isEnabled",
	   ]

import PyTango, os, sys
from sardana.macroserver.macro import *
from sardana.macroserver.macro import macro

#
# general condition feature
#
class gc_enable(Macro):
    """enable general conditions """
    
    param_def = [
        ['macro_name', Type.String, "default", 'Macro name with parameters'],
        ]
    
    def run(self, macro_name):
        if macro_name == "default":
            self.setEnv("GeneralCondition", "gc_macro")
        else:
            self.setEnv("GeneralCondition", macro_name)
            
            
class gc_disable(Macro):
    """disable general conditions """
    
    def run(self):
        try:
            self.unsetEnv("GeneralCondition")
        except:
            pass

class gc_isEnabled(Macro):
    """return True, if the general conditions feature is enabled """    

    result_def = [[ "result", Type.Boolean, None, "True, if the general condition feature is enabled" ]]

    def run(self):            
        result = False

        try:
            general_condition = self.getEnv("GeneralCondition")
            self.output("Selected general condition:")
            self.output(general_condition)
            return True
        except:
            self.output("No general condition")
        
        return result
#
# on_stop feature
#
class gs_enable(Macro):
    """enable on_stop feature """
    
    param_def = [
        ['function_name', Type.String, "default", 'Function name with module and parameters'],
        ]
    
    def run(self, function_name):
        if function_name == "default":
            self.setEnv("GeneralOnStopFunction", "general_functions.general_on_stop")
        else:
            self.setEnv("GeneralOnStopFunction", function_name)
            
    

class gs_disable(Macro):
    """disable on_stop feature """

    def run(self):
        try:
            self.unsetEnv("GeneralOnStopFunction")
        except:
            pass

class gs_isEnabled(Macro):
    """return True, if the general on_stop feature is enabled """    

    result_def = [[ "result", Type.Boolean, None, "True, if the general on_stop feature is enabled" ]]

    def run(self):            
        result = False

        try:
            general_on_stop = self.getEnv("GeneralOnStopFunction")
            self.output("Selected general on_stop:")
            self.output(general_on_stop)
            return True
        except:
            self.output("No general on_stop")
        
        return result
