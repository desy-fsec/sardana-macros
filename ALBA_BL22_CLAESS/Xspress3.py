from sardana.macroserver.macro import Type, Macro, Hookable


class setXRoI(Macro):
    """
    Macro to set the Xspress3 RoIs.
    """
    param_def = [['rois', [['roi_nr', Type.Integer, None, 'RoI number'],
                           ['low', Type.Integer, None, 'Low Pixel'],
                           ['high', Type.Integer, None, 'High Pixel'],
                           {'min': 1, 'max': 5}],
                  None, 'List of RoIs configuration']]

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

    def run(self, rois):
        for roi_nr, low_value, high_value in rois:
            for roi_chn_name in self.RoIs[roi_nr-1]:
                roi_chn = self.getCounterTimer(roi_chn_name)
                roi_chn['roix1'] = low_value
                roi_chn['roix2'] = (high_value - low_value) + 1
