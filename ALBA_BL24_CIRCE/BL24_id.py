from sardana.macroserver.macro import Type, Macro
import PyTango


class IDOffsetCorrection(object):
    POLARIZATION_VALUES = ['LH', 'LV', 'C+', 'C-']
    GRX_IOR_NAME = 'grx_ior'
    GRX_LABELS = ['FLU', 'DUM', 'HEG', 'MEG', 'LEG']

    MOTORS = {'C': ['ideu62_motor_energy', 'ideu62_motor_polarization', ],
              'L': ['ideu62_energy_plus', 'ideu62_polarization_plus']}

    # The equation dictionary is organized by:
    # {Harmnic:{grating:{ Polarization: Formula}}}
    EQUATIONS = {1: {'LEG': {'LH': '(-1.13327 + 1.04863 * en) - en',
                             'LV': '(-3.44044 + 1.05578 * en) - en',
                             'C+': '(-3.50083  + 1.04102 * en) - en',
                             'C-': '(-2.85084 + 1.04661 * en) - en'},
                     'MEG': {'LH': '(-18.94173 + 1.06952 * en) - en',
                             'LV': '(-2.93174 + 1.05511 * en) - en',
                             'C+': '(-7.52251 + 1.04976 * en) - en',
                             'C-': '(-2.78891 + 1.04861 * en) - en', },
                     },

                 3: {'MEG': {'LH': '(1.1687 + 1.02153 * en) - en',
                             'LV': '(-10.86851 + 1.03518 * en) - en'},
                     'HEG': {'LH': '(1.37209 + 1.02218 * en) - en',
                             'LV': '(-11.2187 + 1.03655 * en) - en'},

                     }, }


    def calc_offset(self, energy, pol, grx, harmonic):
        pol = pol.upper();
        if pol not in self.POLARIZATION_VALUES:
            raise ValueError('The polarization must be %r' %
                             self.POLARIZATION_VALUES)

        try:
            formula = self.EQUATIONS[harmonic][grx][pol]
        except KeyError:
            raise RuntimeError('There is not equation for the next parameters %r'
                               % [harmonic, grx, pol])

        offset = eval(formula, {'en': energy})
        return offset

    def set_offset(self, energy, pol):
        pol = pol.upper()
        grx_value = self.getDevice(self.GRX_IOR_NAME)['value'].value
        grx = self.GRX_LABELS[grx_value]
        self.info(grx)
        motors = self.MOTORS[pol[0]]
        motor = PyTango.DeviceProxy('alba03:10000/'+motors[0])
        harmonic=motor.read_attribute('edHarmonic').value
        
        self.info('Calculating offset for: %r' %[grx, pol, harmonic])
        offset = self.calc_offset(energy,pol, grx, harmonic)
        self.info('Offset = %r' % offset)

        for motor_name in motors:
            motor = PyTango.DeviceProxy('alba03:10000/'+motor_name)
            motor.write_attribute('edOffset', offset)

        self.info('Moving id to %r' % energy)
        self.execMacro('mv %s %f' % (motors[0], energy))


class setIDEnegyWithOffset(Macro, IDOffsetCorrection):
    """
        Macro to calcule the ID energy offset and set it.
    """

    param_def = [['Energy', Type.Float, None, 'Mono energy in eV '],
                 ['Polarization', Type.String, 'LH', 'Values of polarization']]


    def run(self, energy, pol):
        self.set_offset(energy, pol)


class testIDEnegyWithOffset(Macro, IDOffsetCorrection):
    """
        Macro to calcule the ID energy offset and set it.
    """

    param_def = [['Energy', Type.Float, None, 'Mono energy in eV '],
                 ['Polarization', Type.String, None, 'Values of polarization'],
                 ['GRX', Type.String, None, 'Mono energy in eV '],
                 ['Harmonic', Type.Float, None, 'Values of polarization'],

                 ]
    def run(self, energy, pol, grx, harmonic):
        self.output('Offset = %r' % self.calc_offset(energy,pol, grx, harmonic))



