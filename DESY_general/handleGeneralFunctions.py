#!/usr/bin/env python

"""
the general hooks/conditions/on_stop macro interface:
the hooks/conditions are defined in $HOME/sardanaMacros/generalFunctions/general_functions.py
the feature is used in gscan.py, scan.py and macro.py
"""

__all__ = ["gf_status",
           "gh_list", "gh_enable", "gh_disable", "gh_isEnabled",
           "gh_setSelector", "gh_getSelector",
           "gc_enable", "gc_enable", "gc_isEnabled",
           "gc_setSelector", "gc_getSelector",
	   "gs_enable", "gs_disable", "gs_isEnabled",
           "gs_setSelector", "gs_getSelector",
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
                    self.output( "general hooks feature is enabled, selector %s" % __builtins__['gh_selector'])
                else:
                    self.output( "general hooks feature is enabled, no selector")
            else:
                self.output( "general hooks feature is disabled")
        else:
            self.output( "general hooks feature is disabled")

        #
        # condition
        #
        if __builtins__.has_key('gc_flagIsEnabled'):
            if __builtins__['gc_flagIsEnabled']:
                if __builtins__.has_key( 'gc_selector'):
                    self.output( "general condition feature is enabled, selector %s" % __builtins__['gc_selector'])
                else:
                    self.output( "general condition feature is enabled, no selector")
            else:
                self.output( "general condition feature is disabled")
        else:
            self.output( "general condition feature is disabled")
        #
        # on-stop
        #
        if __builtins__.has_key('gs_flagIsEnabled'):
            if __builtins__['gs_flagIsEnabled']:
                if __builtins__.has_key( 'gs_selector'):
                    self.output( "general on_stop is enabled, selector %s" % __builtins__['gs_selector'])
                else:
                    self.output( "general on_stop feature is enabled, no selector")
            else:
                self.output( "general on_stop feature is disabled")
        else:
            self.output( "general on_stop feature is disabled")
#
# general hooks feature
#
class gh_list(Macro):
    """display the general_functions.py file """
    
    param_def = []

    def run(self):
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
            self.output( line.rstrip()) 
class gh_enable(Macro):
    """enable general hooks """
    
    param_def = []

    def run(self):
        if 'general_functions' in sys.modules:
            reload( general_functions)
        else:
            self.output( "no general_functions")
            return
        __builtins__['gh_flagIsEnabled'] = True
        self.output( "enable general hooks")

class gh_disable(Macro):
    """disable general hooks """

    param_def = []

    def run(self):
        if 'general_functions' in sys.modules:
            reload( general_functions)
        else:
            self.output( "no general_functions")
            return
        __builtins__['gh_flagIsEnabled'] = False
        self.output( "disable general hooks")

class gh_isEnabled(Macro):
    """return True, if the general hooks feature is enabled """    

    param_def = []

    def run(self):            
        if 'general_functions' in sys.modules:
            reload( general_functions)
        else:
            self.output( "no general_functions")
            return

        if __builtins__.has_key('gh_flagIsEnabled'):
            if __builtins__['gh_flagIsEnabled']:
                self.output( "general hooks feature is enabled")
            else:
                self.output( "general hooks feature is disabled")
        else:
            self.output( "general hooks feature is disabled")

class gh_getSelector(Macro):
    """a selector is a string that may be used in the hooks to 
       distinguish between alignment, absorber mode, etc.
       This feature is optional"""

    param_def = []

    def run(self):            
        if __builtins__.has_key( 'gh_selector'):
            self.output( "selector %s" % __builtins__['gh_selector'])
        else:
            self.output( "selector not set")

class gh_setSelector(Macro):
    """a selector is a string that may be used in the hooks to 
       distinguish between alignment, absorber mode, etc.
       This feature is optional"""

    param_def = [ ["selector", Type.String, "None", "the general hooks selector"],
                  ]    
    def run(self, selector):            
        if 'general_functions' in sys.modules:
            reload( general_functions)
        __builtins__['gh_selector'] = selector
        self.output( "gh_setSelector to %s" % selector)
#
# general condition feature
#
class gc_enable(Macro):
    """enable general conditions """
    
    param_def = []

    def run(self):
        if 'general_functions' in sys.modules:
            reload( general_functions)
        else:
            self.output( "no general_functions")
            return
        __builtins__['gc_flagIsEnabled'] = True
        self.output( "enable general conditions feature")

class gc_disable(Macro):
    """disable general conditions """

    param_def = []

    def run(self):
        if 'general_functions' in sys.modules:
            reload( general_functions)
        else:
            self.output( "no general_functions")
            return
        __builtins__['gc_flagIsEnabled'] = False
        self.output( "disable general conditions feature")

class gc_isEnabled(Macro):
    """return True, if the general conditions feature is enabled """    

    param_def = []

    def run(self):            
        if 'general_functions' in sys.modules:
            reload( general_functions)
        else:
            self.output( "no general_functions")
            return

        if __builtins__.has_key('gc_flagIsEnabled'):
            if __builtins__['gc_flagIsEnabled']:
                self.output( "general conditions feature is enabled")
            else:
                self.output( "general conditions feature is disabled")
        else:
            self.output( "general conditions feature is disabled")

class gc_getSelector(Macro):
    """a selector is a string that may be used in the condition 
       function to distinguish between alignment, absorber mode, etc.
       This feature is optional"""

    param_def = []

    def run(self):            
        if __builtins__.has_key( 'gc_selector'):
            self.output( "condition-selector %s" % __builtins__['gc_selector'])
        else:
            self.output( "condition-selector not set")

class gc_setSelector(Macro):
    """a selector is a string that may be used in the condition
       function to distinguish between alignment, absorber mode, etc.
       This feature is optional"""

    param_def = [ ["selector", Type.String, "None", "the general condition selector"],
                  ]    
    def run(self, selector):            
        if 'general_functions' in sys.modules:
            reload( general_functions)
        __builtins__['gc_selector'] = selector
        self.output( "condition-selector to %s" % selector)
#
# on_stop feature
#
class gs_enable(Macro):
    """enable on_stop feature """
    
    param_def = []

    def run(self):
        if 'general_functions' in sys.modules:
            reload( general_functions)
        else:
            self.output( "no general_functions")
            return
        __builtins__['gs_flagIsEnabled'] = True
        self.output( "enable general on_stop feature")

class gs_disable(Macro):
    """disable on_stop feature """

    param_def = []

    def run(self):
        if 'general_functions' in sys.modules:
            reload( general_functions)
        else:
            self.output( "no general_functions")
            return
        __builtins__['gs_flagIsEnabled'] = False
        self.output( "disable general on_stop feature")

class gs_isEnabled(Macro):
    """return True, if the general on_stop feature is enabled """    

    param_def = []

    def run(self):            
        if 'general_functions' in sys.modules:
            reload( general_functions)
        else:
            self.output( "no general_functions")
            return

        if __builtins__.has_key('gs_flagIsEnabled'):
            if __builtins__['gs_flagIsEnabled']:
                self.output( "general on_stop feature is enabled")
            else:
                self.output( "general on_stop feature is enabled")
        else:
            self.output( "general on_stop feature is disabled")

class gs_getSelector(Macro):
    """a selector is a string that may be used in the on_stop
       function to distinguish between alignment, absorber mode, etc.
       This feature is optional"""

    param_def = []

    def run(self):            
        if __builtins__.has_key( 'gs_selector'):
            self.output( "on_stop selector %s" % __builtins__['gs_selector'])
        else:
            self.output( "on_stop selector not set")

class gs_setSelector(Macro):
    """a selector is a string that may be used in the hooks to 
       distinguish between alignment, absorber mode, etc.
       This feature is optional"""

    param_def = [ ["selector", Type.String, "None", "the general hooks selector"],
                  ]    
    def run(self, selector):            
        if 'general_functions' in sys.modules:
            reload( general_functions)
        __builtins__['gs_selector'] = selector
        self.output( "on_stop selector to %s" % selector)
