#!/usr/bin/env python

"""
the general hooks/conditions/on_stop macro interface:
the feature is used in gscan.py, scan.py and macro.py
"""

__all__ = ["gf_status", "gf_list", "gf_head", "gf_enable",
           "gh_enable", "gh_disable", "gh_isEnabled",
           "gc_enable", "gc_enable", "gc_isEnabled",
	   ]

import PyTango, os, sys
from sardana.macroserver.macro import *
from sardana.macroserver.macro import macro

#
# status for all features
#
class gf_status(Macro):
    """display the status of the general features: hooks, conditions, on_stop """

    def run(self):    
        self.output( "Status general features:")
        self.output("")
        #
        # hooks
        #
        self.execMacro("gh_isEnabled")

        self.output("")
        
        #
        # condition
        #
        self.execMacro("gc_isEnabled")

        self.output("")
        #
        # on-stop
        #
        self.execMacro("gs_isEnabled")

#
# general feature
#
class gf_enable(Macro):
    """enable all general features: hooks, conditions, on_stop """
    
    def run(self):
        self.execMacro("gh_enable")
        self.execMacro("gc_enable")
        self.execMacro("gs_enable")

class gf_disable(Macro):
    """disable all general features: hooks, conditions, on_stop """

    def run(self):
        self.execMacro("gc_disable")
        self.execMacro("gh_disable")
        self.execMacro("gs_disable")
        
        self.info( "All general features disabled")

#
# general hooks feature
#
class gh_enable(Macro):
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
            self.info("Enabling all general hooks with default names")
                
            gh_macros_dict = {}
            for elem in positions:
                if macro_name != "default":
                    self.output(default_dict[elem])
                    default_dict[elem].append(macro_name)
                    self.output(default_dict[elem])
                gh_macros_dict[elem] = default_dict[elem]
            self.setEnv("GeneralHooks", gh_macros_dict)
        else:
            try:
                gh_macros_dict = self.getEnv("GeneralHooks")
            except:
                gh_macros_dict = {}
            if hook_pos in positions:
                macro_name_split = macro_name.split(",")
                gh_macros_dict[hook_pos] = []
                for name in macro_name_split:
                    gh_macros_dict[hook_pos].append(name)
                self.setEnv("GeneralHooks", gh_macros_dict)                
            else:
                self.error("Wrong hook position. Possible values:")
                self.error(positions)
        

class gh_disable(Macro):
    """disable general hooks """

    param_def = [
        ['hook_pos', Type.String, "all", 'Position of the general hook to be disabled'],
    ]

    def run(self, hook_pos):
        try:
            gh_macros_dict = self.getEnv("GeneralHooks")
        except:
            return

        if hook_pos == "all":
            self.unsetEnv("GeneralHooks")
            self.info("All hooks disabled")
        else:
            try:
                del gh_macros_dict[hook_pos]
                self.info("Hook at position %s disabled" % hook_pos)
            except:
                self.info("Nothing disable. Wrong hook position or not enabled")
                return
            
            self.setEnv("GeneralHooks", gh_macros_dict)
        
class gh_isEnabled(Macro):
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
