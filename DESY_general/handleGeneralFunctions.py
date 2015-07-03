#!/usr/bin/env python

"""
the general hooks/conditions macro interface:
the hooks/conditions are defined in $HOME/sardanaMacros/generalFunctions/general_functions.py
the feature is used in gscan.py
"""

__all__ = ["gh_list", "gh_enable", "gh_disable", "gh_isEnabled",
           "gh_setSelector", "gh_getSelector",
           "gc_enable", "gc_enable", "gc_isEnabled",
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
    """return True, if the general hooks are enabled """    

    param_def = []

    def run(self):            
        if 'general_functions' in sys.modules:
            reload( general_functions)
        else:
            self.output( "no general_functions")
            return

        if __builtins__.has_key('gh_flagIsEnabled'):
            if __builtins__['gh_flagIsEnabled']:
                self.output( "general hooks are enabled")
            else:
                self.output( "general hooks are disabled")
        else:
            self.output( "general hooks are enabled")

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
        self.output( "enable general conditions")

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
        self.output( "disable general conditions")

class gc_isEnabled(Macro):
    """return True, if the general conditions are enabled """    

    param_def = []

    def run(self):            
        if 'general_functions' in sys.modules:
            reload( general_functions)
        else:
            self.output( "no general_functions")
            return

        if __builtins__.has_key('gc_flagIsEnabled'):
            if __builtins__['gc_flagIsEnabled']:
                self.output( "general conditions are enabled")
            else:
                self.output( "general conditions are disabled")
        else:
            self.output( "general conditions are enabled")



class gs_isEnabled(Macro):
    """return True, if the general on_stop are enabled """    

    param_def = []

    def run(self):            
        if 'general_functions' in sys.modules:
            reload( general_functions)
        else:
            self.output( "no general_functions")
            return

        if __builtins__.has_key('gs_flagIsEnabled'):
            if __builtins__['gs_flagIsEnabled']:
                self.output( "general on_stop are enabled")
            else:
                self.output( "general on_stop are disabled")
        else:
            self.output( "general on_stop are enabled")



class gs_getSelector(Macro):
    """a selector is a string that may be used in the hooks to 
       distinguish between alignment, absorber mode, etc.
       This feature is optional"""

    param_def = []

    def run(self):            
        if __builtins__.has_key( 'gs_selector'):
            self.output( "selector %s" % __builtins__['gs_selector'])
        else:
            self.output( "selector not set")

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
        self.output( "gs_setSelector to %s" % selector)

        

        

