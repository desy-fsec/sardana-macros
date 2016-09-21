from sardana.macroserver.macro import macro, iMacro, Macro, Type, ParamRepeat
import os


class which_user(Macro):
    """
    Category: Diagnostics

    Returns the user currently running the MacroServer instance.
    """
    param_def = []
 
    def run(self):
        if 'USER' in os.environ.keys():
            self.info("user %s" % os.environ['USER'])
        else:
            self.warning("USER is not defined in this host!")

