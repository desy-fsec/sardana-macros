from sardana.macroserver.macro import Macro


class lim_tp(Macro):
    """
    Macro to set automatically the limits of the pseudo-motors of the tripod
    the pinhole
    """
    def run(self):
        motors_names = [('phx', 'tripod_x', 'tx'), ('phz', 'tripod_z', 'tz')]

        for pin_hole_name, tripod_name, pseudo_name in motors_names:
            pin_hole = self.getMoveable(pin_hole_name)
            tripod = self.getMoveable(tripod_name)
            pseudo = self.getMoveable(pseudo_name)

            ph_min, ph_max = map(float, pin_hole.getPositionObj().getLimits())
            ph_pos = pin_hole.getPosition()
            t_min, t_max = map(float, tripod.getPositionObj().getLimits())
            t_pos = tripod.getPosition()

            # Lower limit
            delta_neg = abs(ph_pos - ph_min)
            pseudo_max = t_pos + delta_neg
            if pseudo_max > t_max:
                pseudo_max = t_max
            # Lower limit
            delta_pos = abs(ph_pos - ph_max)
            pseudo_min = t_pos - delta_pos
            if pseudo_min < t_min:
                pseudo_min = t_min
            self.set_lim(pseudo, pseudo_min, pseudo_max)


class saveph(Macro):
    """
    Macro to save the current position of the motors (phx, phz, tripod_z,
    tripod_x) on the environment variables phx_pos, phz_pos, tripod_x_pos,
    tripod_z_pos of the macro restore_ph
    """

    def run(self):
        motors_names = ['phx', 'phz', 'tripod_x', 'tripod_z']

        for motor_name in motors_names:
            motor = self.getMoveable(motor_name)
            pos = motor.position
            env_name = 'restoreph.{}_pos'.format(motor_name)
            self.setEnv(env_name, pos)
        self.lim_tp()


class restoreph(Macro):
    """
    Macro to restore the motors (phx, phz, tripod_z, tripod_x) from the
    environment variables phx_pos, phz_pos, tripod_x_pos,
    tripod_z_pos
    """

    def run(self):
        motors_names = ['phx', 'phz', 'tripod_x', 'tripod_z']
        cmd = 'mv '

        for motor_name in motors_names:
            env_name = '{}_pos'.format(motor_name)
            pos = self.getEnv(env_name)
            cmd += '{} {} '.format(motor_name, pos)
        self.output(cmd)
        self.execMacro(cmd)

