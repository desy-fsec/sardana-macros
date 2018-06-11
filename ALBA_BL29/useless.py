#!/usr/bin/env python


from sardana.macroserver.macro import Macro


class useless_macro(Macro):

    def run(self, *args, **kwargs):
        self.output('This is a useless macro!')
#        my_macro, aver = self.createMacro('ct')
#        print my_macro, aver
#        self.runMacro(my_macro)
        while True:
            self.execMacro("mares_ccd acquire")
#            self.execMacro("ascan M_detector 20 30 10 0.1")
#            self.execMacro("ascan dummy_mot01 0 100 10 0.1")
#        timer = self.getCounterTimer('uxtimer')
        # timer = self.getPseudoCounter('uxtimer')
#        print timer, type(timer)
#        print 'aver', timer.value, type(timer.value)
