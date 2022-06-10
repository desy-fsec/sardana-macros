#!/usr/bin/env python

"""
this file contains miscellaneous macros

  - smPost: sends a command to the SardanaMonitor to create
            a postscript file and print it
"""
from sardana.macroserver.macro import Macro, Type
import HasyUtils
import os

__all__ = ["smPost"]


#
# the SardanaMonitor macros
#
class smPost(Macro):
    """
    Sends a postscript command, 'post/print/nocon', to the SardanaMonitor
    """
    param_def = [
        ["printer", Type.String, "default", "the printer name"]]

    def run(self, printer):
        if printer.find('default') == 0:
            printer = os.getenv('PRINTER')
            if printer is None:
                self.output(
                    "smPost: shell-environment variable PRINTER not defined "
                    "and no parameter supplied")
                return

        a = HasyUtils.toSardanaMonitor(
            {'gra_command': "post/print/nolog/nocon/lp=%s" % printer})
        if a['result'] != '1':
            self.output("smPost: bad result %s" % repr(a))
