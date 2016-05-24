#!/usr/bin/env python

"""
the general hooks/conditions/on_stop macro interface:
the feature is used in gscan.py, scan.py and macro.py
"""

__all__ = ["new_gf_status", "new_gf_list", "new_gf_head", "new_gf_enable",
           "new_gh_enable", "new_gh_disable", "new_gh_isEnabled",
           "new_gc_enable", "new_gc_enable", "new_gc_isEnabled",
	   ]

import PyTango, os, sys
from sardana.macroserver.macro import *
from sardana.macroserver.macro import macro

#
# status for all features
#
class new_gf_status(Macro):
    """display the status of the general features: hooks, conditions, on_stop """

    def run(self):    
        self.output( "Status general features:")
        self.output("")
        #
        # hooks
        #
        self.execMacro("new_gh_isEnabled")

        self.output("")
        
        #
        # condition
        #
        self.execMacro("new_gc_isEnabled")

        self.output("")
        #
        # on-stop
        #
        self.execMacro("new_gs_isEnabled")

#
# general feature
#
class new_gf_enable(Macro):
    """enable all general features: hooks, conditions, on_stop """
    
    def run(self):
        self.execMacro("new_gh_enable")
        self.execMacro("new_gc_enable")
        self.execMacro("new_gs_enable")

class new_gf_disable(Macro):
    """disable all general features: hooks, conditions, on_stop """

    def run(self):
        self.execMacro("new_gc_disable")
        self.execMacro("new_gh_disable")
        self.execMacro("new_gs_disable")
        
        self.output( "All general features disabled")

#
# general hooks feature
#
class new_gh_enable(Macro):
    """enable general hooks """
    
    param_def = [
        ['macro_name', Type.String, "default", 'Macro name with parameters or selector for the default macros. Ex.: "mv exp_dmy01 10", several macros "mv exp_dmy01 18, mv exp_dmy02 15"'],
        ['hook_pos', Type.String, "default", 'Position where the hook has to be executed'],
    ]
    
    def run(self, macro_name, hook_pos):
        positions = ['pre-scan', 'pre-move', 'pre-acq', 'post-acq',
                     'post-move', 'post-step', 'post-scan']
        default_dict = {'pre-scan': ['gh_pre_scan'],
                        'pre-move': ['gh_pre_move'],
                        'pre-acq': ['gh_pre_acq'],
                        'post-acq': ['gh_post_acq'],
                        'post-move': ['gh_post_move'],
                        'post-step': ['gh_post_step'],
                        'post-scan': ['gh_post_scan']}
        if hook_pos == "default":
            self.output("Enabling all general hooks with default names")
                
            gh_macros_dict = {}
            for elem in positions:
                if macro_name != "default":
                    self.output(default_dict[elem])
                    default_dict[elem].append(macro_name)
                    self.output(default_dict[elem])
                gh_macros_dict[elem] = default_dict[elem]
            self.setEnv("GeneralHooks", gh_macros_dict)
        else:
            gh_macros_dict = self.getEnv("GeneralHooks")
            if hook_pos in positions:
                macro_name_split = macro_name.split(",")
                gh_macros_dict[hook_pos] = []
                for name in macro_name_split:
                    gh_macros_dict[hook_pos].append(name)
                self.setEnv("GeneralHooks", gh_macros_dict)                
            else:
                self.error("Wrong hook position. Possible values:")
                self.error(positions)
        

class new_gh_disable(Macro):
    """disable general hooks """

    def run(self):
        try:
            self.unsetEnv("GeneralHooks")
        except:
            pass
        
class new_gh_isEnabled(Macro):
    """return True, if the general hooks feature is enabled """    

    result_def = [[ "result", Type.Boolean, None, "True, if the general hooks feature is enabled" ]]

    def run(self):            
        result = False
        #
        # hooks
        #
        try:
            general_hooks = self.getEnv("GeneralHooks")
            self.output("Selected general hooks:")
            for pos in general_hooks.keys():
                self.output(pos)
                self.output(general_hooks[pos])
            result = True
        except:
            self.output("No general hooks")
            
        return result
#
# general condition feature
#
class new_gc_enable(Macro):
    """enable general conditions """
    
    param_def = [
        ['macro_name', Type.String, "default", 'Macro name with parameters'],
        ]
    
    def run(self, macro_name):
        if macro_name == "default":
            self.setEnv("GeneralCondition", "gc_macro")
        else:
            self.setEnv("GeneralCondition", macro_name)
            
            
class new_gc_disable(Macro):
    """disable general conditions """
    
    def run(self):
        try:
            self.unsetEnv("GeneralCondition")
        except:
            pass

class new_gc_isEnabled(Macro):
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
class new_gs_enable(Macro):
    """enable on_stop feature """
    
    param_def = [
        ['function_name', Type.String, "default", 'Function name with module and parameters'],
        ]
    
    def run(self, function_name):
        if function_name == "default":
            self.setEnv("GeneralOnStopFunction", "general_functions.general_on_stop")
        else:
            self.setEnv("GeneralOnStopFunction", function_name)
            
    

class new_gs_disable(Macro):
    """disable on_stop feature """

    def run(self):
        try:
            self.unsetEnv("GeneralOnStopFunction")
        except:
            pass

class new_gs_isEnabled(Macro):
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
