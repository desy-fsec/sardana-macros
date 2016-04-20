from sardana.macroserver.macro import iMacro, imacro, Macro, macro, Type
import time


class test_abort_macro(Macro):
    """
    Category: Examples

    This macro is designed to show how the abort command is captured and
    managed by the MacroServer.
    """
    param_def = [['duration', Type.Float, 5.0, 'time to abort'],
                 ['check', Type.Boolean, True, 'checkpoints ON'],
                 ]

    def prepare(self, duration, check):
        self.str_macro = str('sleep ' + str(duration) + ' ' + str(check))
        self.info('Starting main macro...')

    def run(self, duration, check):
        while True:
            self.info('Starting sub macro...')
            time.sleep(1)
            self.execMacro(self.str_macro)
            self.checkPoint()
            time.sleep(1)
        self.info('Already out from loop')

    def on_abort(self):
        self.info('on_abort from [main macro] executed!')


class sleep(Macro):
    """
    Category: Examples

    This macro sleeps for a certain time (duration) in cycles of
    1 second. In between, a checkpoint function is used to provide
    the control-C command to effectively abort the macro
    """
    param_def = [['duration', Type.Float, 5.0, 'time to abort'],
                 ['check', Type.Boolean, True, 'checkpoints ON'],
                 ]

    def run(self, duration, check):
        self.info("Counting silently for %s seconds..." % duration)
        self.count = 0
        for i in range(duration):
            time.sleep(1)
            self.count += 1
            if check:
                self.checkPoint()

    def on_abort(self):
        self.info('counter reached %s' % self.count)
        self.info('on_abort from [sub macro] executed!')
