from sardana.macroserver.macro import Macro, Type
from minikappa import get_centering_motor_positions

class align_kappa_phi(Macro):
    '''
	This macro...blabla
    '''
    param_def = [
                 [ 'kappa_pos', Type.Float, None, 'Position to move kappa to.'],
                 [ 'factor', Type.Float, 1.0, 'Correction factor.'],
                ]

    def prepare(self, *args, **kwargs):
        pass

    def run(self, *args, **kwargs):
	angle, factor = args

	omegax_init_pos = self.getMoveable('omegax').position
	centx_init_pos = self.getMoveable('centx').position
	centy_init_pos = self.getMoveable('centy').position

	ox, cx, cy = get_centering_motor_positions(angle, omegax_init_pos, centx_init_pos, centy_init_pos, factor)
	macro_str = "mv omegax %f centx %f centy %f" % (ox, cx, cy)
        self.info(macro_str)
#        self.execMacro(macro_str)
