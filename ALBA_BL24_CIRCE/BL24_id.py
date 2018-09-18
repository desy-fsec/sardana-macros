from sardana.macroserver.macro import Type, Macro
import PyTango


class IDOffsetCorrection(object):
    POLARIZATION_VALUES = ['LH', 'LV', 'C+', 'C-']
    GRX_IOR_NAME = 'grx_ior'
    GRX_LABELS = ['FLU', 'DUM', 'HEG', 'MEG', 'LEG']

    MOTORS = {'PARALLEL': ['ideu62_motor_energy', 'ideu62_motor_polarization', ],
              'ANTIPARALLEL': ['ideu62_energy_plus', 'ideu62_polarization_plus']}

    # The equation dictionary is organized by:
    # {Harmnic:{grating:{ Polarization: Formula}}}
    EQUATIONS = {1: {'LEG': {'LH': '(-1.1496 + 1.04084 * en) - en',
                             'LV': '(-5.97893 + 1.05419 * en) - en',
                             'C+': '(-5.62584 + 1.04316 * en) - en',
                             'C-': '(-3.68579 + 1.04635 * en) - en'},
                     'MEG': {'LH': '(-4.78795 + 1.04615 * en) - en',
                             'LV': '(-0.7086 + 1.04623 * en) - en',
                             'C+': '(-8.48997 + 1.0473 * en) - en',
                             'C-': '(-2.00496 + 1.044 * en) - en', },
                     },

                 3: {'MEG': {'LH': '(1.29863 + 1.02141 * en) - en',
                             'LV': '(-11.19874 + 1.03549 * en) - en'},
                     'HEG': {'LH': '(1.30712 + 1.02224 * en) - en',
                             'LV': '(-11.27598 + 1.03661 * en) - en'},

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
        motors = self.MOTORS['PARALLEL']
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



