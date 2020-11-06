#!/usr/bin/env python

"""measures the execution time of another macro"""

from sardana.macroserver.macro import Type, Macro
import time


class timedMacro(Macro):
    """
    Measures the execution time of another macro, e.g.:
      timedMacro 'ascan exp_dmy01 0 10 100 0.1'
    """

    param_def = [
       ['cmd', Type.String, None, "the command, in parentheses"],
       ['rest', Type.String, "Empty", "must be empty"],
    ]
    result_def = [["result", Type.Float, None, "the execution time"]]

    def run(self, cmd, rest):

        self.writer = self.output
        if self.mwTest().getResult():
            self.writer = self.mwOutput

        if rest != "Empty":
            self.output("timedMacro: supply the command as one token")
            return 0.
        lst = cmd.split(' ')

        startTime = time.time()
        self.execMacro(lst)
        totalTime = time.time() - startTime
        return totalTime
