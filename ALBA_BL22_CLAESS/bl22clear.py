import time
import subprocess
import json
from sardana.macroserver.macro import Macro, Type
from sardana import State
from bl22clearmotor import ClearSpectrometer

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


class clearSetCeout(Macro):
    """
    Macro to align the energy out pseudo-motor (ceout). It generates a new
    trajectory table according to the current position of the physicals motor:
    caxr, cay, cabu, cabd, cdxr, cdy, cdz, cslxr.
    """

    param_def = [['energy', Type.Float, None, 'Ceout position in eV'],
                 ['points', Type.Integer, 500, 'Trajectory table points']]

    def get_offsets(self):
        motor_offsets = {}
        for motor in self.motors:
            motor_offsets[motor.name] = motor.read_attribute('offset').value
        return motor_offsets

    def run(self, energy):

        # Read ceout crystal order
        ceout = self.getPseudoMotor('ceout')
        order = ceout.read_attribute('n').value
        motors_names = ['caxr', 'cabu', 'cabd', 'cay', 'cdxr', 'cdy', 'cdz',
                        'cslxr']
        motors = []
        for motor_name in motors_names:
            motors.append(self.getMotor(motor_name))

        # TODO read the Crystal IOR
        clear = ClearSpectrometer(n=order)
        news_positions = clear.energy2pos(energy)

        # TODO implement protection
        self.info('Setting new offsets....')
        for motor in motors:
            new_pos = news_positions['{0}_pos'.format(motor.name)]
            self.execMacro('set_user_pos', motor, new_pos)

        # Generate the new trajectory file
        self.info('Generating new trajectory file....')
        clear.motors_offsets = self.get_offsets()
        cbragg = self.getMotor(TRAJECTORY_MOTOR)
        cbragg_ctrl = self.getController(TRAJECTORY_CTRL)
        cbragg_pos_cfg = cbragg.get_attribute_config('position')
        traj_file = cbragg_ctrl.get_property('datafile')['datafile']
        clear.save_trajectory(cbragg_pos_cfg.min_value,
                              cbragg_pos_cfg.max_value,
                              traj_file)

        # Load new file
        self.execMacro('clearLoadTable', traj_file)

        self.output('Loaded new trajectory table. You MUST execute '
                    'clearStatus')
