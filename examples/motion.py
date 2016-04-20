##############################################################################
# Contribution to sardana (16/02/2016)
##############################################################################

"""This module contains macros that demonstrate the usage of motion"""

__all__ = ["move_async"]

__docformat__ = 'restructuredtext'

from sardana.macroserver.macro import *
from sardana import State
import time


class move_async(Macro):
    """
    Category: Test

    A macro that executes an asynchronous movement of a motor. The movement
    can be cancelled by a Ctrl-C.
    This macro is part of the examples package. It was written for
    demonstration purposes.
    """

    param_def = [['name', Type.Moveable, None, 'motor name'],
                 ['pos', Type.Float, None, 'target position'],
                 ]

    def run(self, motor, pos):
        try:
            self.motor = self.getMotion([motor])
            self.info('initial position: %s' % self.motor.readPosition())
            _id = self.motor.startMove([pos])
            # Do whatever here (while the motor is moving)
            while self.motor.readState() == State.Moving:
                time.sleep(0.25)
            # End Do whatever here #######################
        finally:
            self.motor.waitMove(id=_id)

    def on_abort(self):
        try:
            self.info('macro aborted by the user.')

        except Exception as e:
            self.error('Exception in on_abort: %s' % e)


class move_async_test(Macro):
    """
    Category: Test

    A macro that executes an asynchronous movement of a motor.
    Be careful when adding functionality to the macro, since the
    canceling process (Ctrl-C) can lead to exceptions. In this macro,
    all possible exceptions are protected by a try/except block.

    ATTENTION: depending when the Ctrl-C sequence is received, the
    exception in captured in a different try/except block. The on_abort
    method is always executed without error.

    This macro is part of the examples package. It was written for
    demonstration purposes"""

    param_def = [['name', Type.Moveable, None, 'motor name'],
                 ['pos', Type.Float, None, 'target position'],
                 ]

    def run(self, motor, pos):
        try:
            self.motor = self.getMotion([motor])
            self.info('initial position: %s' % self.motor.readPosition())
            _id = self.motor.startMove([pos])
            # Do whatever here (while the motor is moving)
            while self.motor.readState() == State.Moving:
                self.info('current position: %s' % self.motor.readPosition())
                time.sleep(0.25)
            # End Do whatever here #######################
        except Exception as e:
            self.warning('Exception in main loop: %s' % e)

        finally:
            try:
                self.motor.waitMove(id=_id)
                self.info('motor state: %s ' % self.motor.readState())
                self.info('final position: %s' % self.motor.readPosition())
            except Exception as e:
                self.error('Exception in finally: %s' % e)

    def on_abort(self):
        import traceback
        print '\n\n'
        traceback.print_stack()
        print '\n\n'
        try:
            self.info('macro aborted by the user.')
        except Exception as e:
            self.error('Exception in on_abort: %s' % e)


class inf_loop(Macro):
    """
    Category: Test

    A macro that executes an infinity loop until cancelled by a Ctrl-C.
    This macro is part of the examples package. It was written for
    demonstration purposes"""

    param_def = []

    def run(self):
        self.info('Press Ctrl-C to cancel macro execution')
        while True:
            time.sleep(0.25)
            self.checkPoint()

    def on_abort(self):
        try:
            self.info('macro aborted by the user.')
        except Exception as e:
            self.error('Exception in on_abort: %s' % e)