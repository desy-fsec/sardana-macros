from PyTango import DeviceProxy
from bl13constants import (pentaaperpos_X, pentaaperpos_Z,
                           pentaaper_postolerance_X, pentaaper_postolerance_Z)
from sardana.macroserver.macro import Macro, Type, ParamRepeat

PSEUDO='aperture'

class aperture_update_configuration(Macro):
    """
    Category: Configuration

    Macro intended to send tha calibration (dynamic attribute) to the
    penta aperture pseudo motor (pentaaper). The calibration is constructed
    by importing the list of values and tolerances of each pseudomotor from
    a python module (bl13constants). The calibration is validated against
    the existent labels (available pseudo positions) of the pseudomotor.
    It is MANDATORY to restart the pool to apply the changes after applying
    the new calibration.
    """

    def _createCalibration(self, pos, tol):
        calib = []
        for value, res in zip(pos, tol):
            min = value - res
            max = value + res
            p = [min, value, max]
            calib.append(p)
        return calib

    #param_def = [[]]

    def prepare(self):
        # Initialize connection to device
        try:
            self.aperture = DeviceProxy(PSEUDO)
        except:
            raise Exception('Cannot connect to %s device.' % PSEUDO)

        # Read values from file and check consistency with existent labels
        xpos = pentaaperpos_X
        xtol = pentaaper_postolerance_X
        zpos = pentaaperpos_Z
        ztol = pentaaper_postolerance_Z
        npos = self.aperture.nlabels

        lxpos = len(xpos)
        lxtol = len(xtol)
        lzpos = len(zpos)
        lztol = len(ztol)

        size = [lxpos, lxtol, lzpos, lztol]
        self.debug('x_pos (%s) = %s' % (lxpos, xpos))
        self.debug('x_tol (%s) = %s' % (lxtol, xtol))
        self.debug('z_pos (%s) = %s' % (lzpos, zpos))
        self.debug('z_tol (%s) = %s' % (lztol, ztol))

        # If the values are consistent, build the calibration
        if all(npos == x for x in size):
            self.calibration = []
            self.calibration.append(self._createCalibration(xpos, xtol))
            self.calibration.append(self._createCalibration(zpos, ztol))
            self.debug('Calibration:')
            self.debug(repr(self.calibration))
        else:
            raise Exception('Invalid data to build a calibration.')

    def run(self):
        self.info('Sending calibration to %s.' % PSEUDO)
        try:
            self.info(str(self.calibration))
            self.aperture.write_attribute('calibration', str(self.calibration))
            msg = 'done!'
            self.info(msg)
        except:
            raise Exception('Calibration cannot be sent to %s.' % PSEUDO)
