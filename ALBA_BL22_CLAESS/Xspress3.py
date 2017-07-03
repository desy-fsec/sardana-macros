from sardana.macroserver.macro import Type, Macro, Hookable
import taurus

RoIs = [['x_ch1_roi1', 'x_ch2_roi1', 'x_ch3_roi1', 'x_ch4_roi1',
         'x_ch5_roi1'],
        ['x_ch1_roi2', 'x_ch2_roi2', 'x_ch3_roi2', 'x_ch4_roi2',
         'x_ch5_roi2'],
        ['x_ch1_roi3', 'x_ch2_roi3', 'x_ch3_roi3', 'x_ch4_roi3',
         'x_ch5_roi3'],
        ['x_ch1_roi4', 'x_ch2_roi4', 'x_ch3_roi4', 'x_ch4_roi4',
         'x_ch5_roi4'],
        ['x_ch1_roi5', 'x_ch2_roi5', 'x_ch3_roi5', 'x_ch4_roi5',
         'x_ch5_roi5']]


class setXRoI(Macro):
    """
    Macro to set the Xspress3 RoIs.
    """
    param_def = [['rois', [['roi_nr', Type.Integer, None, 'RoI number'],
                           ['low', Type.Integer, None, 'Low Pixel'],
                           ['high', Type.Integer, None, 'High Pixel'],
                           {'min': 1, 'max': 5}],
                  None, 'List of RoIs configuration']]


    def run(self, rois):
        for roi_nr, low_value, high_value in rois:
            if high_value >4095 or low_value<0:
                raise ValueError('The roi range is [0,4095]')
            if low_value >= high_value:
                raise ValueError('The high value must be greater '
                                 'than low value')
            for roi_chn_name in RoIs[roi_nr-1]:
                roi_chn = taurus.Device(roi_chn_name)
                roi_chn['roix1'] = low_value
                roi_chn['roix2'] = (high_value - low_value) + 1


class getXRoIs(Macro):
    """
    Macro to print the Xspress3 RoIs.
    """

    def run(self):
        header = 'Chn\tRoI1L\tRoI1H\tRoI2L\tRoI2H\tRoI3L\tRoI3H\tRoI4L\t' +\
            'RoI4H\tRoI5L\tRoI5H'
        self.output(header)
        for chn_nr in range(5):
            line = 'ch_%d\t' % (chn_nr+1)
            for roi_nr in range(5):
                roi_name = RoIs[roi_nr][chn_nr]
                roi_chn = taurus.Device(roi_name)
                low_value = roi_chn['roix1'].value
                high_value = roi_chn['roix2'].value + low_value - 1
                line += '%d\t%d\t' % (low_value, high_value)
            self.output(line)

        
