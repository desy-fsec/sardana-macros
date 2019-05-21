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
