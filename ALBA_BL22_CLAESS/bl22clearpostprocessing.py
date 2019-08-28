import os
import subprocess
from sardana.macroserver.macro import Macro, Type, Optional


class ClearPostProcessing(object):
    def __init__(self, macro_obj):
        self.macro_obj = macro_obj

    def _get_scan_id(self, scan_id):
        if scan_id is None:
            scan_id = self.macro_obj.getEnv('ScanID')
        return scan_id

    def _get_filename(self, scan_file, scan_dir):
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
        return filename

    def run_subcmd(self, subcmd):
        # Run the command on another PC
        base_cmd = "ssh -X sicilia@ctbl22sard02 " \
                   "'conda activate pyclear; pyClear {}'" \
                   ""
        cmd = base_cmd.format(subcmd)
        self.macro_obj.info('Run command:\n {}'.format(cmd))
        self.macro_obj.output('Script output: ... ')
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        output = ''
        while True:
            out = p.stdout.readline()
            if out == '' and p.poll() != None:
                break
            if out != '':
                self.macro_obj.output(out.strip())
                output += out
        # self.macro_obj.info(output)
        # self.macro_obj.error(error)
        return output

    def elastic(self, output, scan_id, scan_file, scan_dir):
        scan_id = self._get_scan_id(scan_id)
        filename = self._get_filename(scan_file, scan_dir)
        subcmd = 'calib {} {} {}'.format(filename, scan_id, output)
        out = self.run_subcmd(subcmd)
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

    def kbeta(self, output, scan_id, scan_file, scan_dir):
        scan_id = self._get_scan_id(scan_id)
        filename = self._get_filename(scan_file, scan_dir)
        calib_file = self.macro_obj.getEnv('ClearCalibrationFile')
        self.macro_obj.info('Use as calibration file: {}'.format(calib_file))
        subcmd = 'spectra {} {} {} {}'.format(filename, scan_id, calib_file,
                                              output)
        self.run_subcmd(subcmd)

    def pfy(self, output, nr_scans, start_scan_id, scan_file, scan_dir):
        start_scan_id = self._get_scan_id(start_scan_id)
        filename = self._get_filename(scan_file, scan_dir)
        calib_file = self.macro_obj.getEnv('ClearCalibrationFile')
        self.macro_obj.info('Use as calibration file: {}'.format(calib_file))
        subcmd = 'pfy {} {} {} {} {}'.format(filename, start_scan_id, nr_scans,
                                             calib_file, output)
        self.run_subcmd(subcmd)


class elastic(Macro):
    """
    Macro to calibrate the clear. It generate two text filesq
    """
    param_def = [
        ['output', Type.String, None, 'output file pattern'],
        ['scanId', Type.Integer, Optional, 'scan id'],
        ['scanFile', Type.String, Optional, 'scan filename'],
        ['ScanDir', Type.String, Optional, 'scan dir'],
    ]

    def run(self, output, scan_id, scan_file, scan_dir):
        clear = ClearPostProcessing(self)
        clear.elastic(output, scan_id, scan_file, scan_dir)


class kbeta(Macro):
    """
    Macro to calibrate the clear. It generate two text filesq
    """
    param_def = [
        ['output', Type.String, None, 'output file pattern'],
        ['scanId', Type.Integer, Optional, 'scan id'],
        ['scanFile', Type.String, Optional, 'scan filename'],
        ['ScanDir', Type.String, Optional, 'scan dir'],
    ]

    def run(self, output, scan_id, scan_file, scan_dir):
        clear = ClearPostProcessing(self)
        clear.kbeta(output, scan_id, scan_file, scan_dir)


class pfy(Macro):
    """
    Macro to calibrate the clear. It generate two text filesq
    """
    param_def = [
        ['output', Type.String, None, 'output file pattern'],
        ['nrScans', Type.Integer, -3,
         'number of scans to concatenate can be negative'],
        ['scanId', Type.Integer, Optional, 'scan id'],
        ['scanFile', Type.String, Optional, 'scan filename'],
        ['ScanDir', Type.String, Optional, 'scan dir'],
    ]

    def run(self, output, nr_scans, scan_id, scan_file, scan_dir):
        clear = ClearPostProcessing(self)
        clear.pfy(output, nr_scans, scan_id, scan_file, scan_dir)
