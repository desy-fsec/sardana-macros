"""
    Macro library containning scan related macros
"""
from sardana.macroserver.macro import Macro, Type

class lup(Macro):
    """Line-up scan:
    Like dscan, a relative motor scan of one motor.
    """

    param_def = [
        ['motor', Type.Moveable, None, 'Moveable to move'],
        ['rel_start_pos', Type.Float, -999, 'Scan start position'],
        ['rel_final_pos', Type.Float, -999, 'Scan final position'],
        ['nr_interv', Type.Integer, -999, 'Number of scan intervals'],
        ['integ_time', Type.Float, -999, 'Integration time']
    ]

    def run(self, motor, rel_start_pos, rel_final_pos, nr_interv, integ_time):

        if ((integ_time != -999)):
            # motor_pos =
            motor.getPosition()
            # scan =
            self.dscan(
                motor, rel_start_pos, rel_final_pos, nr_interv, integ_time)
        else:
            self.output("Usage:   lup motor start end intervals time")


class dummyscan(Macro):
    """dummyscan:

    Scan of dummy motor, just reading out the counters
    """

    param_def = [
        ['start_pos', Type.Float, -999, 'Scan start position'],
        ['final_pos', Type.Float, -999, 'Scan final position'],
        ['nr_interv', Type.Integer, -999, 'Number of scan intervals'],
        ['integ_time', Type.Float, -999, 'Integration time']]

    def run(self, start_pos, final_pos, nr_interv, integ_time):

        if ((integ_time != -999)):
            # scan =
            self.ascan("exp_dmy01", start_pos, final_pos, nr_interv,
                       integ_time)
        else:
            self.output("Usage:   dummyscan start stop intervals time")


class scan_loop(Macro):

    param_def = [
        ['motor',      Type.Moveable,   None, 'Moveable to move'],
        ['start_pos', Type.Float,   None, 'Scan start position'],
        ['final_pos', Type.Float,   None, 'Scan final position'],
        ['nr_interv', Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float,   None, 'Integration time'],
        ['nb_loops', Type.Integer, -1, 'Nb of loops (optional)']]

    def run(self, motor, start_pos, final_pos, nr_interv, integ_time,
            nb_loops):

        if nb_loops > 0:
            for i in range(0, nb_loops):
                self.execMacro(
                    'ascan', motor.getName(), start_pos, final_pos, nr_interv,
                    integ_time)
        else:
            while 1:
                self.execMacro(
                    'ascan', motor.getName(), start_pos, final_pos,
                    nr_interv, integ_time)


class ascan_regions(Macro):
    """ Absolute scan in regions """

    param_def = [
        ['motor',
         Type.Moveable, None, 'Motor to scan to move'],
        ["scan_regions", [
            ['start', Type.Float, None, 'Start position'],
            ['stop', Type.Float, None, 'Stop position'],
            ['nbstep', Type.Integer, None, 'Nb of steps'],
            ['integ_time', Type.Float, None, 'Integration time']],
         None, 'List of scan regions']]

    def run(self, motor, scan_regions):
        # calculate number of regions
        nregions = len(scan_regions)
        for i in range(0, nregions):
            macro, pars = self.createMacro(
                'ascan', motor,
                scan_regions[i][0],         # start
                scan_regions[i][1],         # stop
                scan_regions[i][2],         # number of steps
                scan_regions[i][3])         # integration time

            self.runMacro(macro)


class dscan_regions(Macro):
    """ Relative scan in regions """

    param_def = [
        ['motor',      Type.Moveable,   None, 'Motor to scan to move'],
        ["scan_regions", [
            ['start', Type.Float, None, 'Relative start position'],
            ['stop', Type.Float, None, 'Relative stop position'],
            ['nbstep', Type.Integer, None, 'Nb of steps'],
            ['integ_time', Type.Float, None, 'Integration time']],
         None, 'List of scan regions']]

    def run(self, motor, scan_regions):

        # calculate number of regions
        nregions = len(scan_regions)
        posOld = motor.getPosition()
        for i in range(0, nregions):
            macro, pars = self.createMacro(
                'ascan', motor,
                posOld+scan_regions[i][0],         # start
                posOld+scan_regions[i][1],         # stop
                scan_regions[i][2],                # number of steps
                scan_regions[i][3])                # integration time

            self.runMacro(macro)
        self.mv(motor, posOld)


class fscan_regions(Macro):
    """ Scan in regions """

    param_def = [
        ['motor', Type.Moveable, None, 'Motor to scan to move'],
        ["scan_regions", [
            ['start', Type.Float, None, 'Start position'],
            ['stop', Type.Float, None, 'Stop position'],
            ['nbstep', Type.Integer, None, 'Nb of steps'],
            ['integ_time', Type.Float, None, 'Integration time']],
         None, 'List of scan regions']]

    def run(self, motor, scan_regions):
        nregions = len(scan_regions)
        x_points = []
        time_arr = []
        for i in range(0, nregions):
            start = scan_regions[i][0]
            stop = scan_regions[i][1]
            nbsteps = scan_regions[i][2]
            int_time = scan_regions[i][3]
            step_length = (stop - start)/nbsteps
            for j in range(0, nbsteps + 1):
                x_points.append(start + j*step_length)
                time_arr.append(int_time)

        x_str = "x=["
        time_str = "["
        for i in range(0, len(x_points)):
            x_str = x_str + str(x_points[i]) + ", "
            time_str = time_str + str(time_arr[i]) + ", "
        x_str = x_str + "]"
        time_str = time_str + "]"

        macro, pars = self.createMacro('fscan', x_str, time_str, motor, "x")

        self.runMacro(macro)
