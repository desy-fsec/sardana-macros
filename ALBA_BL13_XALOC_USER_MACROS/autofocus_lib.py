import os
import nxs
import numpy
import math
import time
import PyTango

from sardana.macroserver.macro import Macro, Type
import taurus

class autofocus(Macro):
    """Executes the autofocus macro"""

    param_def = []

    result_def = []
    
    def run(self):
        self.oav = PyTango.DeviceProxy('bl13/eh/diffoav')
        self.focus = PyTango.DeviceProxy('omegay')
        self.vars = taurus.Device('bl13/ct/variables')

        self.original_focus = self.focus.read_attribute('Position').value
        self.start_velocity = self.focus.read_attribute('Velocity').value
        MAX_FOCUS_VALUE = self.focus_calc(self.get_gray_image())
        MAX_FOCUS = self.original_focus

        pixsize_mm = self.vars.oav_pixelsize_x / 1000.
        start_focus = self.original_focus - (500 * pixsize_mm)
        end_focus = self.original_focus + (500 * pixsize_mm)
        self.execMacro('mv', 'omegay', start_focus)

        # MOVE CONTINOUS AND ACQUIRE AS MUCH AS POSSIBLE
        positions = []
        values = []

        self.focus.write_attribute('Velocity', self.start_velocity * 0.3)
        self.focus.write_attribute('Position', end_focus)
        while self.focus.read_attribute('State').value != PyTango.DevState.ON:
            pos = self.focus.read_attribute('Position').value
            focus_value = self.focus_calc(self.get_gray_image())
            positions.append(pos)
            values.append(focus_value)
            if focus_value > MAX_FOCUS_VALUE:
                MAX_FOCUS_VALUE = focus_value
                MAX_FOCUS = pos
            # REPORT SOME INFO ABOUT THE PROGRES..
            yield int(100 * ((pos - start_focus) / (end_focus - start_focus)))

        # TRY TO FIT QUADRATICALLY
        x = positions
        y = values
        a,b,c = numpy.polyfit(x,y,2)
        max_focus_fit = -b/2/a
        fit = lambda t : a * t**2 + b * t + c
        fitted = map(fit, positions)
        
        self.focus.write_attribute('Velocity', self.start_velocity)
        best_focus = MAX_FOCUS
        if a < 0 and start_focus <= max_focus_fit <= end_focus:
            best_focus = max_focus_fit
        else:
            # THIS ELSE MEANS NO SUCCESS, SO:
            # WE COULD DO ANOTHER ITERATION IN ORDER TO HAVE
            # THE MAXIMUM FOCUS _SEEN_ BY THE ALGORITHM
            # AT THE END OF THE SECOND ITERATION WE SHOULD COMPARE RESULTS
            # right now, we will have best_focus = MAX_FOCUS
            pass

        points = len(positions)
        self.info('Autofocus: Processed %d images. Best focus at %.3f' % (points, best_focus))
        yield 100
        self.execMacro('mv', 'omegay', best_focus)


    def get_gray_image(self):
        if self.oav.read_attribute('ColorMode').value == False:
            return self.oav.read_attribute('Image').value
        else:
            img_tango = self.oav.read_attribute('Image').value
            img_rgb = img_tango.reshape(img_tango.shape[0], img_tango.shape[1]/3, 3)
            img_gray = img_rgb.astype(numpy.int).sum(axis=-1)
            return img_gray

    def focus_calc(self, img):
        return numpy.abs(numpy.fft.fft2(img)).sum()
