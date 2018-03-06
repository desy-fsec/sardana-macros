import time
from sardana.macroserver.macro import Macro, Type
from sardana import State

# TODO:
TRAJECTORY_CTRL = 'rh_clear_tj_ctrl'
TRAJECTORY_MOTOR = 'clear_bragg'


class clearSync(Macro):
    """
    Macro to synchronize the clear motor to a position of the trajectory.
    """

    param_def = [['position', Type.Float, None, 'Synchronize position'],
                 ['motors', [['motor', Type.Motor, None, 'Motor'],
                             {'min': 1}],
                  None, 'Motor list']]

    def run(self, position, motors):
        pool = self.getPools()[0]
        motors_axis = []
        for motor in motors:
            axis = motor.get_property('axis')['axis'][0]
            motors_axis.append(str(axis))
        cmd = 'MOVEP {0} {1}'.format(position, ' '.join(motors_axis))
        ans = pool.SendToController([TRAJECTORY_CTRL, cmd])
        if ans != 'Done':
            raise RuntimeError('The command does not work')
        self.info('Synchronizing motors...')
        time.sleep(0.1)
        while True:
            states = []
            for motor in motors:
                mstate = motor.read_attribute('state').value
                states.append(mstate == State.Moving)
            if not any(states):
                break
        self.info('Done')


class clearMoveTo(Macro):
    """
    Macro to move in the trajectory table some motors.
    """

    param_def = [['position', Type.Float, None, 'Synchronize position'],
                 ['motors', [['motor', Type.Motor, None, 'Motor'],
                             {'min': 1}],
                  None, 'Motor list']]

    def run(self, position, motors):
        pool = self.getPools()[0]
        motors_axis = []
        for motor in motors:
            axis = motor.get_property('axis')['axis'][0]
            motors_axis.append(str(axis))
        cmd = 'PMOVE {0} {1}'.format(position, ' '.join(motors_axis))
        ans = pool.SendToController([TRAJECTORY_CTRL, cmd])
        if ans != 'Done':
            raise RuntimeError('The command does not work')
            raise RuntimeError('The command does not work')
        self.info('Moving motors...')
        time.sleep(0.1)
        while True:
            states = []
            for motor in motors:
                mstate = motor.read_attribute('state').value
                states.append(mstate == State.Moving)
            if not any(states):
                break
        self.info('Done')


class clearStatus(Macro):
    """
    Macro to show the status of the motor used on the trajectories.
    """

    def run(self):
        motor = self.getMotor(TRAJECTORY_MOTOR)
        status = motor.status()
        self.output(status)


class clearLoadTable(Macro):
    """
    Macro to load the parametric table. If filename is set, it will load a
    new table.
    """

    param_def =[['filename', Type.String, '', 'Parametric table filename']]

    def run(self, filename):
        if filename == '':
           filename = None
        cmd = 'Load {0}'.format(filename)
        pool = self.getPools()[0]
        ans = pool.SendToController([TRAJECTORY_CTRL, cmd])
        if ans != 'Done':
            raise RuntimeError('The command does not work')
        self.output('Done')
