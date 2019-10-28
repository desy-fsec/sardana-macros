import os
import subprocess
from sardana.macroserver.macro import Macro, Type, Optional


class ClearPostProcessing(object):
    def __init__(self, macro_obj, params):
        self.macro_obj = macro_obj
        self.params = params
        self.cmd = None
        self._develop = False
        try:
            self._develop = self.macro_obj.getEnv('_ClearDevelop')
            self.macro_obj.warning('It is using develop version.!!!')
        except Exception:
            self._develop = False

    def add_scan_id(self):
        try:
            scan_id = self.params.pop('scanid')
        except Exception:
            scan_id = None

        if scan_id is None:
            scan_id = self.macro_obj.getEnv('ScanID')
        self.cmd += '{} '.format(scan_id)

    def add_filename(self):
        try:
            scan_file = self.params.pop('scanfile')
        except Exception:
            scan_file = None

        try:
            scan_dir = self.params.pop('scandir')
        except Exception:
            scan_dir = None

        if scan_file is None:
            scan_files = self.macro_obj.getEnv('ScanFile')
            if type(scan_files) is list:
                for f in scan_files:
                    if '.dat' in f:
                        scan_file = f
                        break
            elif type(scan_files) is str:
                if '.dat' in scan_files:
                    scan_file = scan_files

            if scan_file is None:
                raise RuntimeError('There are not Spec file on '
                                   'the ScanFile: {}'.format(repr(scan_files)))

        if scan_dir is None:
            scan_dir = self.macro_obj.getEnv('ScanDir')

        filename = os.path.join(scan_dir, scan_file)
        self.cmd += '{} '.format(filename)
        return

    def add_roi(self, send_auto_roi=True):
        try:
            roi = self.params.pop('roi')
        except Exception:
            roi = None

        if roi is not None:
            roi_low, roi_high = roi.split(':')

            if send_auto_roi:
                self.cmd += '--no_auto_roi '

            self.cmd += '--roi=[{},{}] '.format(roi_low, roi_high)

    def add_noise(self):
        try:
            noise = self.params.pop('noise')
        except Exception:
            noise = None
        if noise is not None:
            self.cmd += '--noise={} '.format(noise)

    def add_raw(self):
        try:
            raw = self.params.pop('raw')
        except Exception:
            raw = None

        if raw is not None and raw.lower() == 'true':
            self.cmd += '--extract_raw '

    def add_outfile(self):
        out_file = self.params.pop('outfile')
        self.cmd += '{} '.format(out_file)

    def add_calibfile(self):
        calib_file = self.macro_obj.getEnv('ClearCalibrationFile')
        self.cmd += '{} '.format(calib_file)

    def add_nrscans(self):
        try:
            nr_scans = self.params.pop('nrscans')
        except Exception:
            nr_scans = -3
        self.cmd += '{} '.format(nr_scans)

    def add_json(self):
        try:
            json_file = self.params.pop('json')
        except Exception:
            json_file = None

        if json_file is not None and json_file.lower() == 'true':
            self.cmd += '--extract_json '

    def add_i0(self):
        try:
            i0_name = self.params.pop('i0')
        except Exception:
            i0_name = None
        if i0_name is not None:
            self.cmd += '--i0={} '.format(i0_name)

    def add_energy_step(self):
        try:
            energy_step = self.params.pop('energy_step')
        except Exception:
            energy_step = None
        if energy_step is not None:
            self.cmd += '--energy_step={} '.format(energy_step)

    def add_smooth_window(self):
        try:
            smooth_window = self.params.pop('smooth_window')
        except Exception:
            smooth_window = None
        if smooth_window is not None:
            self.cmd += '--smooth_window={} '.format(smooth_window)

    def add_smooth_order(self):
        try:
            smooth_order = self.params.pop('smooth_order')
        except Exception:
            smooth_order = None
        if smooth_order is not None:
            self.cmd += '--smooth_order={} '.format(smooth_order)

    def del_smooth(self):
        try:
            smooth = eval(self.params.pop('smooth'))
        except Exception:
            smooth = None
        if smooth is not None and smooth is False:
            self.cmd += '--no_smooth '

    def run(self):
        if len(self.params.keys()) != 0:
            self.macro_obj.warning('There are invalid parameters not used: '
                                   '{}'.format(repr(self.params.keys())))

        # Run the command on another PC
        if self._develop:
            base_cmd = "ssh -X sicilia@ctbl22sard02 " \
                       "'conda activate pyclear; pyClear {}'"
        else:
            base_cmd = "ssh -X sicilia@ctbl22sard02 " \
                       "'pyClear {}'"

        cmd = base_cmd.format(self.cmd)
        self.macro_obj.info('Run command:\n {}'.format(cmd))
        self.macro_obj.output('Script output: ... ')
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        output = ''
        while True:
            out = p.stdout.readline()
            if out == '' and p.poll() is not None:
                break
            if out != '':
                self.macro_obj.output(out.strip())
                output += out
        # self.macro_obj.info(output)
        # self.macro_obj.error(error)
        return output

    def elastic(self):
        self.cmd = 'calib '
        self.add_noise()
        self.add_raw()
        self.add_roi()
        self.add_i0()
        self.add_energy_step()
        self.add_smooth_order()
        self.add_smooth_window()
        self.del_smooth()
        self.add_filename()
        self.add_scan_id()
        self.add_outfile()
        out = self.run()

        out_lines = out.split('\n')
        calib_file = None
        for line in out_lines:
            if '.json' in line:
                calib_file = line.split()[-1]
                break
        if calib_file is None:
            raise RuntimeError('There are problems with the calibration '
                               'output')
        self.macro_obj.setEnv('ClearCalibrationFile', calib_file)

    def spectra(self):
        self.cmd = 'spectra '
        self.add_raw()
        self.add_filename()
        self.add_scan_id()
        self.add_calibfile()
        self.add_outfile()
        self.run()

    def pfy(self):
        self.cmd = 'pfy '
        self.add_raw()
        self.add_json()
        self.add_roi(send_auto_roi=False)
        self.add_filename()
        self.add_scan_id()
        self.add_nrscans()
        self.add_calibfile()
        self.add_outfile()
        self.run()


class elastic(Macro):
    """
    Macro to calibrate the clear.

    How to use it
        By using the last scan and the default parameters:
            elastic /tmp/calib_output
        By using another scanid and change some default parameters:
            elastic /tmp/calib_output scanid 3042 energy_step 0.1 roi 300:800

    Allowed optional parameters:
    * scanid: Number of the scan.
       Default last scan.
    * scanfile: Name of the file.
       Default last file.
    * scandir: Path to the scan file.
       Default last dir.
    * noise: Percent of noise to be removed.
       Default 10%
    * roi: ROI value eg 400:900.
       Default auto-roi
    * raw: True/False to extract the raw data.
       Default False
    * i0: Channel name used for normalize.
       Default: n_i0_1
    * energy_step: Change energy step interpolation,
       Default: 0.03 eV
    * smooth: True/False the smoothing of the calibration
       Default: True
    *smooth_window: Window for the savgol filter
       Default: 51
    *smooth_order: Order of the polynomial order
       Default: 3

    """
    param_def = [
        ['output', Type.String, None, 'output file pattern'],
        ['params', [
            ['param', Type.String, None, 'param to set'],
            ['value', Type.String, None, 'param value'],
            {'min': 0, 'max': None}], None, 'List of params']
        ]

    def run(self, output, params):
        params = dict(params)
        params['outfile'] = output
        clear = ClearPostProcessing(self, params)
        clear.elastic()


class spectra(Macro):
    """
    Macro to extract the spectra.
    How to use it
        By using the last scan and the default parameters:
            spectra /tmp/kbeta_output
        By using another scanid and change some default parameters:
            elastic /tmp/kbeta_output scanid 3042 raw True

    Allowed optional parameters:
    * scanid: Number of the scan.
       Default last scan.
    * scanfile: Name of the file.
       Default last file.
    * scandir: Path to the scan file.
       Default last dir.
    * raw: True/False to extract the raw data.
       Default False
    """
    param_def = [
        ['output', Type.String, None, 'output file pattern'],
        ['params', [
            ['param', Type.String, None, 'param to set'],
            ['value', Type.String, None, 'param value'],
            {'min': 0, 'max': None}], None, 'List of params']
        ]

    def run(self, output, params):
        params = dict(params)
        params['outfile'] = output
        clear = ClearPostProcessing(self, params)
        clear.spectra()


class pfy(Macro):
    """
    Macro to extract the PFY.
    How to use it
        By using the last three scan and the default parameters:
            pfy /tmp/pfy_output
        By using another scanid and change some default parameters:
            pfy /tmp/pfy_output scanid 3042 roi 8405:8406 raw True

    Allowed optional parameters:
    * nrscans: Number of scans to concatenate. It can be negative.
       Default <-3> last three scans
    * scanid: Number of the scan.
       Default last scan.
    * scanfile: Name of the file.
       Default last file.
    * scandir: Path to the scan file.
       Default last dir.
    * roi: Energy ROI value eg 7400:7450.
       Default use the calibration ROI
    * raw: True/False to extract the raw data.
       Default False
    * json: True/False to extract the post-processed matrix and vectors.
       Default False
    """
    param_def = [
        ['output', Type.String, None, 'output file pattern'],
        ['params', [
            ['param', Type.String, None, 'param to set'],
            ['value', Type.String, None, 'param value'],
            {'min': 0, 'max': None}], None, 'List of params']
        ]

    def run(self, output, params):
        params = dict(params)
        params['outfile'] = output
        clear = ClearPostProcessing(self, params)
        clear.pfy()

