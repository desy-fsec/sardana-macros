#!/usr/bin/env python

"""
the general hooks/conditions/on_stop macro interface:
the hooks/conditions are defined in $HOME/sardanaMacros/generalFunctions/general_functions.py
the feature is used in gscan.py, scan.py and macro.py
"""

__all__ = ["gf_status", "gf_list", "gf_head", "gf_enable", "gf_disable", "gf_setSelector", 
           "gh_enable", "gh_disable", "gh_isEnabled", "gh_setSelector", "gh_getSelector",
           "gc_enable", "gc_enable", "gc_isEnabled",  "gc_setSelector", "gc_getSelector",
	   "gs_enable", "gs_disable", "gs_isEnabled", "gs_setSelector", "gs_getSelector",
	   ]

import PyTango, os, sys
from sardana.macroserver.macro import *
from sardana.macroserver.macro import macro
#
# find the local user
#
locus = os.popen("cat /home/etc/local_user").read().strip()
dirName = "/home/%s/sardanaMacros/generalFunctions" % locus
if (len(locus) > 0) and (dirName not in sys.path):
        sys.path.append( dirName)
try:
    import general_functions
except:
    pass
#
# status for all features
#
class gf_status(Macro):
    """display the status of the general features: hooks, conditions, on_stop """

    param_def = []

    def run(self):            
        if 'general_functions' in sys.modules:
            reload( general_functions)
        else:
            self.output( "no general_functions")
            return
        self.output( "general features status:")
        #
        # hooks
        #
        if __builtins__.has_key('gh_flagIsEnabled'):
            if __builtins__['gh_flagIsEnabled']:
                if __builtins__.has_key( 'gh_selector'):
                    self.output( "general hooks feature (gh) is enabled, selector %s" % __builtins__['gh_selector'])
                else:
                    self.output( "general hooks feature (gh) is enabled, no selector")
            else:
                self.output( "general hooks feature (gh) is disabled")
        else:
            self.output( "general hooks feature (gh) is disabled")

        #
        # condition
        #
        if __builtins__.has_key('gc_flagIsEnabled'):
            if __builtins__['gc_flagIsEnabled']:
                if __builtins__.has_key( 'gc_selector'):
                    self.output( "general condition feature (gc) is enabled, selector %s" % __builtins__['gc_selector'])
                else:
                    self.output( "general condition feature (gc) is enabled, no selector")
            else:
                self.output( "general condition feature (gc) is disabled")
        else:
            self.output( "general condition feature (gc) is disabled")
        #
        # on-stop
        #
        if __builtins__.has_key('gs_flagIsEnabled'):
            if __builtins__['gs_flagIsEnabled']:
                if __builtins__.has_key( 'gs_selector'):
                    self.output( "general on_stop feature (gs) is enabled, selector %s" % __builtins__['gs_selector'])
                else:
                    self.output( "general on_stop feature (gs) is enabled, no selector")
            else:
                self.output( "general on_stop feature (gs) is disabled")
        else:
            self.output( "general on_stop feature (gs) is disabled")

        #
        # from: <module 'general_functions' from 
        #        '/home/kracht/sardanaMacros/generalFunctions/general_functions.pyc'>
        # to: '/home/kracht/sardanaMacros/generalFunctions/general_functions.pyc'
        #
        self.output( "\nCode: %s" % str(sys.modules[ 'general_functions']).split( "from")[1].replace(">", "").strip())
        self.output( "\nThe following macros are involved: gf_status, gf_list, gf_head")
        self.output( "All features: gf_enable, gf_disable, gf_set_selector")
        self.output( "Individual: XX_enable, XX_disable, XX_isEnabled, XX_setSelector, XX_getSelector")

class gf_list(Macro):
    """display the general_functions.py file """
    
    param_def = []

    def run(self):

        self.writer = self.output
        if self.mwTest().getResult():
            self.writer = self.mwOutput

        fname = "%s/general_functions.py" % dirName
        if 'general_functions' in sys.modules:
            reload( general_functions)
        else:
            self.output( "no general_functions")
            return

        inp = open( fname, 'r')        
        lines = inp.readlines() 
        inp.close()
        for line in lines:
            self.writer( line.rstrip()) 

class gf_head(Macro):
    """display the first lines of general_functions.py file """
    
    param_def = []

    def run(self):

        self.writer = self.output
        if self.mwTest().getResult():
            self.writer = self.mwOutput

        fname = "%s/general_functions.py" % dirName
        if 'general_functions' in sys.modules:
            reload( general_functions)
        else:
            self.output( "no general_functions")
            return

        inp = open( fname, 'r')        
        lines = inp.readlines() 
        inp.close()
        count = 0
        for line in lines:
            self.writer( " " + line.rstrip()) 
            count += 1
            if count > 20:
                break
#
# general feature
#
class gf_enable(Macro):
    """enable all general features: hooks, conditions, on_stop """
    
    param_def = []
    result_def = [[ "result", Type.Boolean, None, "Completion status" ]]

    def run(self):
        if not self.gh_enable().getResult():
            self.output( "gh_enable returned False")
            return False
        if not self.gc_enable().getResult():
            self.output( "gc_enable returned False")
            return False
        if not self.gs_enable().getResult():
            self.output( "gs_enable returned False")
            return False
        self.output( "enable all general features")
        return True

class gf_disable(Macro):
    """disable all general features: hooks, conditions, on_stop """
    
    param_def = []
    result_def = [[ "result", Type.Boolean, None, "Completion status" ]]

    def run(self):
        if not self.gh_disable().getResult():
            self.output( "gh_disable returned False")
            return False
        if not self.gc_disable().getResult():
            self.output( "gc_disable returned False")
            return False
        if not self.gs_disable().getResult():
            self.output( "gs_disable returned False")
            return False

        self.output( "disable all general features")
        return True

class gf_setSelector(Macro):
    """a selector is a string that may be used in the hooks to 
       distinguish between alignment, absorber mode, etc.
       This feature is optional"""

    param_def = [ ["selector", Type.String, "None", "the general features selector for hooks, conditions, on_stop"],
                  ]    
    result_def = [[ "result", Type.Boolean, None, "Completion status" ]]

    def run(self, selector):            
        if not self.gh_setSelector( selector).getResult(): 
            self.output( "gh_setSelector returned False")
            return False
        if not self.gc_setSelector( selector).getResult(): 
            self.output( "gc_setSelector returned False")
            return False
        if not self.gs_setSelector( selector).getResult(): 
            self.output( "gs_setSelector returned False")
            return False
        return True
#
# general hooks feature
#
class gh_enable(Macro):
    """enable general hooks """
    
    param_def = []
    result_def = [[ "result", Type.Boolean, None, "Completion status" ]]

    def run(self):
        if 'general_functions' in sys.modules:
            reload( general_functions)
        else:
            self.output( "no general_functions")
            return False
        __builtins__['gh_flagIsEnabled'] = True
        self.output( "enable general hooks feature")
        return True

class gh_disable(Macro):
    """disable general hooks """

    param_def = []
    result_def = [[ "result", Type.Boolean, None, "Completion status" ]]

    def run(self):
        if 'general_functions' in sys.modules:
            reload( general_functions)
        else:
            self.output( "no general_functions")
            return False
        __builtins__['gh_flagIsEnabled'] = False
        self.output( "disable general hooks feature")
        return True

class gh_isEnabled(Macro):
    """return True, if the general hooks feature is enabled """    

    param_def = []
    result_def = [[ "result", Type.Boolean, None, "True, if the general hooks feature is enabled" ]]

    def run(self):            
        result = False
        if 'general_functions' in sys.modules:
            reload( general_functions)
        else:
            self.output( "no general_functions")
            return result

        if __builtins__.has_key('gh_flagIsEnabled'):
            if __builtins__['gh_flagIsEnabled']:
                self.output( "general hooks feature is enabled")
                result = True
            else:
                self.output( "general hooks feature is disabled")
        else:
            self.output( "general hooks feature is disabled")
        return result

class gh_getSelector(Macro):
    """a selector is a string that may be used in the hooks to 
       distinguish between alignment, absorber mode, etc.
       This feature is optional"""

    param_def = []
    result_def = [[ "result", Type.String, None, "the general hooks selector" ]]

    def run(self):            
        if __builtins__.has_key( 'gh_selector'):
            self.output( "selector %s" % __builtins__['gh_selector'])
            return __builtins__['gh_selector']
        else:
            self.output( "gh_selector not set")
            return "None"

class gh_setSelector(Macro):
    """a selector is a string that may be used in the hooks to 
       distinguish between alignment, absorber mode, etc.
       This feature is optional"""

    param_def = [ ["selector", Type.String, "None", "the general hooks selector"],]
    result_def = [[ "result", Type.Boolean, None, "Completion status" ]]

    def run(self, selector):            
        if 'general_functions' in sys.modules:
            reload( general_functions)
        __builtins__['gh_selector'] = selector
        self.output( "gh-selector to %s" % selector)
        return True
#
# general condition feature
#
class gc_enable(Macro):
    """enable general conditions """
    
    param_def = []
    result_def = [[ "result", Type.Boolean, None, "Completion status" ]]

    def run(self):
        if 'general_functions' in sys.modules:
            reload( general_functions)
        else:
            self.output( "no general_functions")
            return False
        __builtins__['gc_flagIsEnabled'] = True
        self.output( "enable general conditions feature")
        return True

class gc_disable(Macro):
    """disable general conditions """

    param_def = []
    result_def = [[ "result", Type.Boolean, None, "Completion status" ]]

    def run(self):
        if 'general_functions' in sys.modules:
            reload( general_functions)
        else:
            self.output( "no general_functions")
            return False
        __builtins__['gc_flagIsEnabled'] = False
        self.output( "disable general conditions feature")
        return True

class gc_isEnabled(Macro):
    """return True, if the general conditions feature is enabled """    

    param_def = []
    result_def = [[ "result", Type.Boolean, None, "True, if the general condition feature is enabled" ]]

    def run(self):            
        result = False
        if 'general_functions' in sys.modules:
            reload( general_functions)
        else:
            self.output( "no general_functions")
            return result

        if __builtins__.has_key('gc_flagIsEnabled'):
            if __builtins__['gc_flagIsEnabled']:
                self.output( "general conditions feature is enabled")
                result = True
            else:
                self.output( "general conditions feature is disabled")
        else:
            self.output( "general conditions feature is disabled")
        return result

class gc_getSelector(Macro):
    """a selector is a string that may be used in the condition 
       function to distinguish between alignment, absorber mode, etc.
       This feature is optional"""

    param_def = []
    result_def = [[ "result", Type.String, None, "the general conditions selector" ]]

    def run(self):            
        if __builtins__.has_key( 'gc_selector'):
            self.output( "condition-selector %s" % __builtins__['gc_selector'])
            return __builtins__['gc_selector']
        else:
            self.output( "gc_selector not set")
            return "None"

class gc_setSelector(Macro):
    """a selector is a string that may be used in the condition
       function to distinguish between alignment, absorber mode, etc.
       This feature is optional"""

    param_def = [ ["selector", Type.String, "None", "the general condition selector"],
                  ]    
    result_def = [[ "result", Type.Boolean, None, "Completion status" ]]

    def run(self, selector):            
        if 'general_functions' in sys.modules:
            reload( general_functions)
        __builtins__['gc_selector'] = selector
        self.output( "gc-selector to %s" % selector)
        return True
#
# on_stop feature
#
class gs_enable(Macro):
    """enable on_stop feature """
    
    param_def = []
    result_def = [[ "result", Type.Boolean, None, "Completion status" ]]

    def run(self):
        if 'general_functions' in sys.modules:
            reload( general_functions)
        else:
            self.output( "no general_functions")
            return False
        __builtins__['gs_flagIsEnabled'] = True
        self.output( "enable general on_stop feature")
        return True

class gs_disable(Macro):
    """disable on_stop feature """

    param_def = []
    result_def = [[ "result", Type.Boolean, None, "Completion status" ]]

    def run(self):
        if 'general_functions' in sys.modules:
            reload( general_functions)
        else:
            self.output( "no general_functions")
            return False
        __builtins__['gs_flagIsEnabled'] = False
        self.output( "disable general on_stop feature")
        return True

class gs_isEnabled(Macro):
    """return True, if the general on_stop feature is enabled """    

    param_def = []
    result_def = [[ "result", Type.Boolean, None, "True, if the general on_stop feature is enabled" ]]

    def run(self):            
        result = False
        if 'general_functions' in sys.modules:
            reload( general_functions)
        else:
            self.output( "no general_functions")
            return result

        if __builtins__.has_key('gs_flagIsEnabled'):
            if __builtins__['gs_flagIsEnabled']:
                self.output( "general on_stop feature is enabled")
                result = True
            else:
                self.output( "general on_stop feature is enabled")
        else:
            self.output( "general on_stop feature is disabled")
        return result

class gs_getSelector(Macro):
    """a selector is a string that may be used in the on_stop
       function to distinguish between alignment, absorber mode, etc.
       This feature is optional"""

    param_def = []
    result_def = [[ "result", Type.String, None, "the on_stop selector" ]]

    def run(self):            
        if __builtins__.has_key( 'gs_selector'):
            self.output( "on_stop selector %s" % __builtins__['gs_selector'])
            return __builtins__['gs_selector']
        else:
            self.output( "gs_ selector not set")
            return "None"

class gs_setSelector(Macro):
    """a selector is a string that may be used in the hooks to 
       distinguish between alignment, absorber mode, etc.
       This feature is optional"""

    param_def = [ ["selector", Type.String, "None", "the general hooks selector"],]
    result_def = [[ "result", Type.Boolean, None, "Completion status" ]]

    def run(self, selector):            
        if 'general_functions' in sys.modules:
            reload( general_functions)
        __builtins__['gs_selector'] = selector
        self.output( "on_stop-selector to %s" % selector)
        return True
