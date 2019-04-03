import time
import os
import pickle
import shutil
from sardana.macroserver.macro import Macro, Type
from sardana import State
from bl22clearmotor import ClearSpectrometer

TRAJECTORY_CTRL = 'cbragg_traj_ctrl'
TRAJECTORY_MOTOR = 'cbragg'
TRAJECTORY_POINTS = 170


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
        self.clearReconfig()
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
        motor.state()
        self.output(motor.statusdetails)


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
        flg_done = False
        self.info('Loading new table to the icepap. It can take time...')
        for i in range(3):
            try:
                ans = pool.SendToController([TRAJECTORY_CTRL, cmd])
                if ans == 'Done':
                    flg_done = True
                    break
            except Exception:
                time.sleep(2)
        if not flg_done:
            raise RuntimeError('There was not possible to load the table. '
                               'You can do it by hand: clearLoadTable '
                               '{0}'.format(filename))
            return

        self.clearReconfig()
        self.output('Done')


class clearReconfig(Macro):
    """
    Macro to restore the velocity and acceleration of the cbragg motor
    """
    CONFIG = {'cy': {'velocity': 0.4, 'acceleration': 1},
              'cslx1': {'velocity': 0.15051, 'acceleration': 0.15},
              'cslx2': {'velocity': 0.15051, 'acceleration': 0.15},
              'cslz1': {'velocity': 0.15051, 'acceleration': 0.15},
              'cslz2': {'velocity': 0.15051, 'acceleration': 0.15},
              'cslxr': {'velocity': 1, 'acceleration': 0.1},
              'cay': {'velocity': 0.8, 'acceleration': 1.6},
              'caz': {'velocity': 0.8, 'acceleration': 1.6},
              'caxr': {'velocity': 0.4, 'acceleration': 1.6},
              'cdxr': {'velocity': 1, 'acceleration': 0.5},
              'cdz': {'velocity': 0.8, 'acceleration': 1.6},
              'cdy': {'velocity': 1.6, 'acceleration': 1.6},
              'cdx': {'velocity': 0.09933, 'acceleration': 0.1},
              'cdmask': {'velocity': 0.15051, 'acceleration': 0.15},
              'cabd': {'velocity': 1.8, 'acceleration': 0.1},
              'cabu': {'velocity': 1.8, 'acceleration': 0.2},
              'chi': {'velocity': 5.004, 'acceleration': 0.1}}

    def run(self):
        try:
            self.info('Restoring clear Motors '
                      'configuration {0}'.format(self.CONFIG.keys()))
            for motor_name, config in self.CONFIG.items():
                motor = self.getMotor(motor_name)
                for param, value in config.items():
                    motor.write_attribute(param, value)

            self.info('Restoring cbragg configuration...')
            pool = self.getPools()[0]
            pool.SendToController([TRAJECTORY_CTRL, 'CalcVel'])

            dev = self.getMotor(TRAJECTORY_MOTOR)
            max_vel = dev.read_attribute('maxvelocity').value - 0.0001
            dev.write_attribute('velocity', max_vel)
            dev.write_attribute('acceleration', 1.6)

        except Exception as e:
            self.error('Can not restore the {0} '
                       'configuration. {1}'.format(TRAJECTORY_MOTOR, e))


class clearAutoSync(Macro):
    """
    Macro to auto synchronize the motors to the trajectory by using the caxr
    position. The macro works only when the different between the positions
    are not greater than 2 degrees, excepts cabu, cabd and cslxr which do
    not have collision problems.
    """

    def run(self):
        motor = self.getMotor(TRAJECTORY_MOTOR)
        motor.state()
        status = motor.statusdetails

        if 'clearSync' not in status:
            raise RuntimeError('This macro is only to synchronize the '
                               'motors. Use clearStatus to check the '
                               'clear current state.')

        self.output('Auto synchronization...')
        if 'PowerOn(False)' in status:
            self.clearStatus()
            raise RuntimeError('You should turn on first the motors, '
                               'and after you can run clearAutoSync.')
        motor_to_sync = status.split('clearSync macro):')
        if len(motor_to_sync) != 2:
            self.info('There are not motors to synchronize')
            return
        lines = motor_to_sync[1].split('\n')[1:-1]
        motors_names = []
        motors_pos = []
        motors_obj = []
        master_pos = motor.masterpos
        for line in lines:
            values = line.split()
            motor_name = values[0]
            motors_names.append(motor_name)
            motors_obj.append(self.getMotor(motor_name))
            pos = float(values[-1])
            motors_pos.append(pos)
        error = 'There is(are) motor(s) with very distant positions:\n {0}' \
                'You must synchronize the motors by hand'
        motor_error = []
        for i, motor_pos in enumerate(motors_pos):
            if motors_names[i] in ['cabu', 'cabd', 'cslxr']:
                continue
            diff = abs(abs(motor_pos) - abs(master_pos))
            if diff > 2.0:
                msg = '{0} near to {1} and should be in ' \
                      '{2}\n'.format(motors_names[i], motors_pos[i],
                                     master_pos)
                motor_error.append(msg)
        if len(motor_error) > 0:
            self.error(error.format(' '.join(motor_error)))
            return

        self.clearSync(master_pos, motors_obj)
        self.clearReconfig()
        self.output('Done')


class clearSetCeout(Macro):
    """
    Macro to align the energy out pseudo-motor (ceout). It generates a new
    trajectory table according to the current position of the physicals motor:
    caxr, cay, cabu, cabd, cdxr, cdy, cdz, cslxr.
    """

    param_def = [['energy', Type.Float, None, 'Ceout position in eV'],
                 ['forced', Type.Boolean, False, 'Force the configuration']]

    def get_offsets(self):
        motor_offsets = {}
        for motor in self.motors:
            motor_offsets[motor.name] = motor.read_attribute('offset').value
        return motor_offsets

    def run(self, energy, forced):

        # Read ceout crystal order
        ceout = self.getPseudoMotor('ceout')
        order = ceout.read_attribute('n').value
        motors_names = ['caxr', 'cabu', 'cabd', 'cay', 'cdxr', 'cdy',
                        'cdz', 'cslxr']
        self.motors = []
        for motor_name in motors_names:
            self.motors.append(self.getMotor(motor_name))
        # TODO read the Crystal IOR
        clear = ClearSpectrometer(n=order)
        # TODO implement protection logic
        # Protection of the system
        # if not forced:
        #     new_bragg = clear.energy2bragg(energy)
        #     cbragg.state()
        #     status = cbragg.statusdetails
        #
        # else:
        #     self.warning('Skip bragg change checking, you can misalign the '
        #                  'Clear!!!')
        news_positions = clear.energy2pos(energy)
        self.info('Setting new offsets....')
        for motor in self.motors:
            new_pos = news_positions['{0}_pos'.format(motor.name)][0]
            self.execMacro('set_user_pos', motor, new_pos)
        # Generate the new trajectory file
        self.info('Generating new trajectory file....')
        clear.motors_offsets = self.get_offsets()
        cbragg_ctrl = self.getController(TRAJECTORY_CTRL)
        traj_file = cbragg_ctrl.get_property('datafile')['datafile'][0]
        filename, ext = os.path.splitext(traj_file)
        t_str = time.strftime('%Y%m%d_%H%M%S')
        bkp_file = '{0}_{1}{2}'.format(filename, t_str, ext)
        os.rename(traj_file, bkp_file)
        self.info('Create backup: {0}'.format(bkp_file))
        # TODO: Implement table for each
        clear.save_trajectory(30,
                              80,
                              TRAJECTORY_POINTS,
                              traj_file)

        # Load new file
        self.clearLoadTable(traj_file)
        self.clearAutoSync()


class clearRestoreTable(Macro):
    """
    Macro to restore the a trajectory backup table. It restore the table and
    the motor offset. By default reload the current table again.
    """

    param_def = [['bkp_file', Type.String, '', 'Backup filenme']]

    def run(self, bkp_file):
        cbragg_ctrl = self.getController(TRAJECTORY_CTRL)
        traj_file = cbragg_ctrl.get_property('datafile')['datafile'][0]

        if bkp_file != '':
            self.info('Remove current trajectory file.')
            shutil.copy(bkp_file, traj_file)
            with open(traj_file, 'r') as f:
                traj = pickle.load(f)

            motor_offsets = traj['offset']
            for name, offset in motor_offsets.items():
                motor = self.getMotor(name)
                current_offset = motor.read_attribute('offset').value
                motor.write_attribute('offset', offset)
                self.output('Change {0} offset from {1} to '
                            '{2}'.format(name, current_offset, offset))
        self.clearLoadTable(traj_file)
        self.clearAutoSync()
