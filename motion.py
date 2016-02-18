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
    """A macro that executes an asynchronous movement of a motor. The movement
    can be cancelled in a save way.
    This macro is part of the examples package. It was written for
    demonstration purposes"""

    param_def = [['name', Type.String, None, 'motor name'],
                 ['pos', Type.Float, None, 'target position'],
                 ]

    def prepare(self, name, pos):
        self.motor = self.getMotion([name])
        self.info('moving motor %s to reference position 0.' % name)
        self.motor.move(0)

    def run(self, name, pos):
        try:
            self.info('initial position: %s' % self.motor.readPosition())
            _id = self.motor.startMove([pos])
            while self.motor.readState() == State.Moving:
                self.info('current position: %s' % self.motor.readPosition(force=True))
                time.sleep(0.1)
        except Exception, e:
            self.warning('manage any exception as "%s" here.' % e)
        finally:
            self.motor.waitMove(id=_id)
            self.info('final position: %s' % self.motor.readPosition())


