import time
from sardana.macroserver.macro import Macro, Type
from sardana import State

# TODO:
TRAJECTORY_CTRL = 'cbragg_traj_ctrl'
TRAJECTORY_MOTOR = 'cbragg'


class clearSync(Macro):
    """
    Macro to synchronize the clear motor to a position of the trajectory.
    """

    param_def = [['position', Type.Float, None, 'Synchronize position'],
                 ['motors', [['motor', Type.Motor, None, 'Motor'],
                             {'min': 1}],
                  None, 'Motor list']]

    def run(self, position, motors):
        try:
            pool = self.getPools()[0]
            motors_axis = []
            motors_names = []
            for motor in motors:
                axis = motor.get_property('axis')['axis'][0]
                motors_axis.append(str(axis))
                motors_names.append(motor.name)
            cmd = 'MOVEP {0} {1}'.format(position, ' '.join(motors_axis))
            ans = pool.SendToController([TRAJECTORY_CTRL, cmd])
            if ans != 'Done':
                raise RuntimeError('The command does not work')
            self.info('Synchronizing to {0} motors: {1}'.format(position,
                                                                motors_names))
            time.sleep(0.1)
            while True:
                states = []
                self.checkPoint()
                for motor in motors:
                    mstate = motor.read_attribute('state').value
                    states.append(mstate == State.Moving)
                if not any(states):
                    break
            self.info('Done')
        finally:
            for motor in motors:
                motor.stop()


class clearMoveTo(Macro):
    """
    Macro to move in the trajectory table some motors.
    """

    param_def = [['position', Type.Float, None, 'Synchronize position'],
                 ['motors', [['motor', Type.Motor, None, 'Motor'],
                             {'min': 1}],
                  None, 'Motor list']]

    def run(self, position, motors):
        try:
            pool = self.getPools()[0]
            motors_axis = []
            motors_names = []
            for motor in motors:
                axis = motor.get_property('axis')['axis'][0]
                motors_axis.append(str(axis))
                motors_names.append(motor.name)
            cmd = 'PMOVE {0} {1}'.format(position, ' '.join(motors_axis))
            ans = pool.SendToController([TRAJECTORY_CTRL, cmd])
            if ans != 'Done':
                raise RuntimeError('The command does not work')
            self.info('Moving to {0} motors: {1}'.format(position,
                                                         motors_names))
            time.sleep(0.1)
            while True:
                states = []
                self.checkPoint()
                for motor in motors:
                    mstate = motor.read_attribute('state').value
                    states.append(mstate == State.Moving)
                if not any(states):
                    break
            self.info('Done')
        finally:
            for motor in motors:
                motor.stop()


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

    param_def = [['filename', Type.String, '', 'Parametric table filename']]

    def run(self, filename):
        if filename == '':
           filename = None
        cmd = 'Load {0}'.format(filename)
        pool = self.getPools()[0]
        ans = pool.SendToController([TRAJECTORY_CTRL, cmd])
        if ans != 'Done':
            raise RuntimeError('The command did not work')

        bragg_motor = self.getMotor(TRAJECTORY_MOTOR)
        max_vel = bragg_motor.read_attribute('MaxVelocity').value
        self.output('Set bragg velocity to {0}'.format(max_vel))

        bragg_motor.write_attribute('velocity', max_vel)
        self.output('Done')


class clearAutoSync(Macro):
    """
    Macro to auto synchronize the motors to the trajectory and to move them
    to the same caxr position.
    """

    def run(self):
        motor = self.getMotor(TRAJECTORY_MOTOR)
        status = motor.status()
        if 'clearSync' in status:
            self.output('Auto synchronization...')
            lines = status.split(':')[1].split('\n')[1:-1]

            for line in lines:
                values = line.split()
                motor_name = self.getMotor(values[0])
                near_pos = float(values[-1])
                self.clearSync(near_pos, [motor_name])
        status = motor.status()
        if 'clearMoveTo' in status:
            self.output('Auto move...')
            lines = status.split(':')[1].split('\n')[1:-1]
            for line in lines:
                values = line.split()
                motor_name = self.getMotor(values[0])
                pos = float(values[-1])
                self.clearMoveTo(pos, [motor_name])
        self.output('Set cbragg velocity & acceleration')
        max_vel = motor.read_attribute('maxvelocity').value - 0.0001
        motor.write_attribute('velocity', max_vel)

        motor.write_attribute('acceleration', 1.6)
        self.output('Done')
