import time
import datetime
import os
import mmap
from sardana.macroserver.macro import macro, Type, Macro, ViewOption, Optional
from sardana.macroserver.msexception import StopException
import taurus
import PyTango
from taurus.console.table import Table
import pyIcePAP
from albaemlib import AlbaEm
from albaEmUtils import em_range
from tools import fewait
from mntgroup_utils import MGManager


###############################################################################
#       Create aliases for general macros
###############################################################################
class EMrange(em_range):
    """
    Macro alias of em_range
    """
    pass


class waitFE(fewait):
    """
    Macro alias of fewait
    """
    pass


###############################################################################

def _getMotorAlias(dev_name):
    return PyTango.Database().get_alias(dev_name)


class wa_print(Macro):
    env = ('Printer',)

    param_def = []

    def prepare(self, **opts):
        self.all_motors = self.findObjs('.*', type_class=Type.Moveable)
        self.table_opts = {}

        printer_name = self.getEnv('Printer')
        if printer_name is None:
            print 'Printer is None, set printer Name in Printer enviroment'
            return

        self.printer = os.popen('lpr -P %s' % printer_name, 'w')

    def run(self):
        nr_motors = len(self.all_motors)
        if nr_motors == 0:
            self.output('No motor defined')
            return

        d = datetime.datetime.now().isoformat(' ')

        self.printer.write('\n\nCurrent positions (user) on %s\n\n\n' % d)
        self.output('Current positions (user) on %s' % d)

        show_dial = self.getViewOption(ViewOption.ShowDial)
        motor_width = 9
        motor_names = []
        motor_pos = []
        motor_list = list(self.all_motors)
        motor_list.sort()
        for motor in motor_list:
            name = motor.getName()
            motor_names.append([name])
            pos = motor.getPosition(force=True)
            if pos is None:
                pos = float('NAN')

            if show_dial:
                dial_pos = motor.getDialPosition(force=True)
                if dial_pos is None:
                    dial_pos = float('NAN')
                motor_pos.append((pos, dial_pos))
            else:
                motor_pos.append((pos,))

            motor_width = max(motor_width, len(name))

        fmt = '%c*.%df' % ('%', motor_width - 5)

        table = Table(motor_pos, elem_fmt=[fmt],
                      col_head_str=motor_names, col_head_width=motor_width,
                      **self.table_opts)
        for line in table.genOutput():
            self.output(line)
            self.printer.write(line+'\n')

        self.printer.close()


@macro()
def sho(self):
    self.execMacro('shopen')
    time.sleep(2)
    self.execMacro('moco_go')


@macro()
def shc(self):
    self.execMacro('moco_stop')
    time.sleep(2)
    self.execMacro('shclose')


class tripod_z_homming(Macro):
    jack_steps = 5128  # steps_per_unit 1mm
    icepap_name = 'icebl2202'

    motors_conf = [[PyTango.DeviceProxy('motor/eh_ipap_ctrl/6'), 1085],
                   [PyTango.DeviceProxy('motor/eh_ipap_ctrl/7'), 28300],
                   [PyTango.DeviceProxy('motor/eh_ipap_ctrl/5'), 15210]]

    def run(self):
        self.execMacro('mv tripod_z 16')
        macro = 'ipap_homing True False tripod_j1 -1 tripod_j2 -1 tripod_j3 -1'
        self.execMacro(macro)
        states = []

        # go to home position horizontal
        for motor, offset in self.motors_conf:
            motor.step_per_unit = 1
            motor.position = offset
            states.append(motor.state)

        # wait for each motor finish
        while True:
            time.sleep(0.1)
            count = 0
            for state in states:
                if state() == PyTango._PyTango.DevState.ON:
                    count += 1
            if count == 3:
                break

        # recover the step per unit set the current position as homing
        ipap = pyIcePAP.EthIcePAP(self.icepap_name)
        for motor, offset in self.motors_conf:
            motor.step_per_unit = self.jack_steps
            axis = int(motor.dev_name()[-1])
            ipap.setPosition(axis, 0)


class reconfig(Macro):
    """Macro to configure some elements at nominal conditions: pcmac, fluo_x,
    Adlink, electrometers."""

    param_def = [["moco_pos", Type.Boolean, True,
                  "Work in moco position mode"]]
    timeout = 10
    def run(self, moco_pos):
        self.execMacro('qExafsCleanup')

        # self.info('Reconfig dmot1')
        # dev = PyTango.DeviceProxy('dmot1')
        # dev.write_attribute('velocity', 1000000)
        # dev.write_attribute('base_rate', 0)
        # dev.write_attribute('acceleration', 0.1)
        #
        # self.info('Reconfig fluo_x')
        # fluo_x = PyTango.DeviceProxy('motor/eh_ipap_ctrl/53')
        # fluo_x.velocity = 0.8
        # fluo_x.acceleration = 1
        self.info('Configure mg_all timeout to {}s'.format(self.timeout))
        mg = taurus.Device('mg_all')
        mg.set_timeout_millis(self.timeout*1000)
        self.info('Restore exit_offset')
        self.execMacro('mv oh_dcm_exit_offset 25.5')
        self.info('Restore phx velocity')
        dev = PyTango.DeviceProxy('phx')
        dev.write_attribute('velocity', 1.8)
        self.info('Restore phz velocity')
        dev = PyTango.DeviceProxy('phz')
        dev.write_attribute('velocity', 1.8)
        self.info('Restore tripod_x velocity')
        dev = PyTango.DeviceProxy('tripod_x')
        dev.write_attribute('velocity', 0.15)
        dev.write_attribute('acceleration', 0.354331)
        for tripod in ['tripod_j1', 'tripod_j2', 'tripod_j3']:
            self.info('Restore %s velocity' % tripod)
            dev = PyTango.DeviceProxy(tripod)
            dev.write_attribute('velocity', 0.71489859)
            dev.write_attribute('acceleration', 0.2)

        self.clearReconfig()
        self.info('Set the electrometer polarity')
        host_e0 = self.getEnv('ElemI0Host')
        host_e1 = self.getEnv('ElemI1I2Host')
        if moco_pos:
            chn = ['1', 'NO']
        else:
            chn = ['1', 'YES']

        if self.getEnv('phd_enabled'):
            self.warning('Using pin-hole')
            chn_i1_1 = ['4', 'NO']
        else:
            chn_i1_1 = ['4', 'YES']

        try:
            e0 = AlbaEm(host_e0)
            e0_channels = [chn, ['2', 'YES'], ['3', 'YES'], ['4', 'YES']]
            e0.setInvs(e0_channels)
            time.sleep(0.5)
            e0_inv = e0.getInvs([1, 2, 3, 4])
            self.info('EMET-02 signal invertions: %s' % e0_inv)
        except Exception as e:
            self.warning('It was not possible to configure the EMET-02')
            self.debug(e)

        try:
            e1 = AlbaEm(host_e1)
            e1_channels = [['1', 'YES'], ['2', 'YES'], ['3', 'YES'], chn_i1_1]
            e1.setInvs(e1_channels)
            time.sleep(0.5)
            e1_inv = e1.getInvs([1, 2, 3, 4])
            self.info('EMET-03 signal inversions: %s' % e1_inv)
        except Exception as e:
            self.warning('It was not possible to configure the EMET-03')
            self.debug(e)


class getScanFile(Macro):
    """
    The macro returns the scanFile: ScanDir+ScanFile
    """
    result_def = [['scan_filenames', Type.String, None, '']]

    def run(self):
        scan_dir = self.getEnv('ScanDir')
        scan_files = self.getEnv('ScanFile')
        scan_filenames = ''
        if type(scan_files) is not list:
            scan_files = [scan_files]
        for filename in scan_files:
            scan_filenames += '%s/%s,' % (scan_dir, filename)

        return scan_filenames


class getScanID(Macro):
    """
    The macro returns the scanid.
    """

    result_def = [['scanid', Type.Integer, None, '']]

    def run(self):
        scanid = self.getEnv('ScanID')
        return scanid


class set_mode(Macro):
    """
    Macro to enable/disable the channel of mg_all measurement group
    according to the experiment type.
    """

    env = ('ContScanMG', 'DefaultMG', 'ActiveMntGrp')

    param_def = [['ExpType', Type.String, None, 'transm, fluo, clear, all']]

    # Channels by elements
    iochamber_chns = ['a_i0i1_timer', 'a_i0_1', 'a_i0_2', 'a_i1_1', 'a_i1_2',
                      'n_timer', 'n_i0_1', 'n_i0_2', 'n_i1_1', 'n_i1_2',
                      'n_i2_1', 'n_i2_2']

    amptek_chns = ['n_timer', 'n_icr', 'n_tcr', 'n_sca1', 'n_sca2', 'n_sca3',
                   'n_sca4']

    xpress3_chns = ['x_timer', 'x_ch1_roi1', 'x_ch2_roi1', 'x_ch3_roi1',
                    'x_ch4_roi1', 'x_ch5_roi1', 'x_ch6_roi1', 'x_ch1_roi2',
                    'x_ch2_roi2', 'x_ch3_roi2', 'x_ch4_roi2', 'x_ch5_roi2',
                    'x_ch6_roi2', 'x_ch1_roi3', 'x_ch2_roi3', 'x_ch3_roi3',
                    'x_ch4_roi3', 'x_ch5_roi3', 'x_ch6_roi3', 'x_ch1_roi4',
                    'x_ch2_roi4', 'x_ch3_roi4', 'x_ch4_roi4', 'x_ch5_roi4',
                    'x_ch6_roi4', 'x_ch1_roi5', 'x_ch2_roi5', 'x_ch3_roi5',
                    'x_ch4_roi5', 'x_ch5_roi5', 'x_ch6_roi5', 'x_ch7_roi1',
                    'x_ch7_roi2', 'x_ch7_roi3', 'x_ch7_roi4', 'x_ch7_roi5']

    xpress3_dt_chns = ['x_timer', 'x_dt_1', 'x_dt_2', 'x_dt_3', 'x_dt_4',
                       'x_dt_5', 'x_dtf_1', 'x_dtf_2', 'x_dtf_3', 'x_dtf_4',
                       'x_dtf_5']

    mythen_chns = ['m_raw', 'mc_roi1', 'mc_roi2', 'mc_roi3']

    # energyc is the timer first channel and it
    # does not  work on the macro
    common_chns = ['energyc', 'sr_i_1', 'TSample', 'Td', 'TBody']

    # Dictionary with the experiment types and their enabled channels
    exp_type_conf = {
        'transm': iochamber_chns + amptek_chns + common_chns,
        'fluo': iochamber_chns + amptek_chns + xpress3_chns + common_chns,
        'fluodt': iochamber_chns +amptek_chns + xpress3_chns +
                  xpress3_dt_chns + common_chns,
        'clear': iochamber_chns + amptek_chns + mythen_chns + common_chns,
        'all': iochamber_chns + amptek_chns + mythen_chns + xpress3_chns +
               xpress3_dt_chns + common_chns
    }

    mg_name = 'mg_all'

    def run(self, exp_type):
        exp_type = exp_type.lower()
        if exp_type not in self.exp_type_conf:
            raise ValueError('The values must be: %r' %
                             self.exp_type_conf.keys())

        self.setEnv('ContScanMG', self.mg_name)
        self.setEnv('DefaultMG', self.mg_name)
        self.setEnv('ActiveMntGrp', self.mg_name)

        chns_names = self.exp_type_conf[exp_type]
        mg = self.getMeasurementGroup(self.mg_name)
        mg_manager = MGManager(self, mg, chns_names)
        mg_manager.enable_only_channels()
        mg_manager.status()


class get_outfilename(Macro):
    """
    Macro to generate new output filename if the filename exists.
    """
    param_def = [['filename', Type.String, None, 'input filename']]
    result_def = [['outFile', Type.String, None, 'output filename']]

    def run(self, filename):
        fname, ext = os.path.splitext(filename)
        temp_filename = fname + '_{0:02}' + ext
        count = 0
        while True:
            self.checkPoint()
            new_filename = temp_filename.format(count)
            if not os.path.exists(new_filename):
                break
            count += 1
        return new_filename


class nextract(Macro):
    """
    Macro to extract multiples scans. It works with spec files.
    """

    env = ('ScanDir', 'ScanFile', 'ScanID')
    param_def = [
        ['NrScans', Type.Integer, None, 'Number of scans per repetition'],
        ['NrRepetitions', Type.Integer, None, 'Number of repetitions'],
        ['OutputFile', Type.String, None, 'Output filename (path included)'],
        ['StartScanID', Type.Integer, -1, 'Start scan ID to process'],
        ['SpecFile', Type.String, "", 'Spec file with the data']]

    def get_output_file(self, filename):
        fname, ext = os.path.splitext(filename)
        temp_filename = fname + '_{0}' + ext
        count = 0
        while True:
            self.checkPoint()

            new_filename = temp_filename.format(count)
            if not os.path.exists(new_filename):
                break
            count += 1
        return new_filename

    def get_input_file(self, scan_file):
        if scan_file == '':
            scan_files = self.getEnv('ScanFile')
            if type(scan_files) == list:
                for f in scan_files:
                    if '.dat' in f:
                        scan_file = f
                        break
                else:
                    self.error('You should save the data on Spec File')
                    raise StopException()
            elif type(scan_files) == str:
                if '.dat' not in scan_file:
                    self.error('You should save the data on Spec File')
                    raise StopException()
            else:
                self.error('You should save the data on Spec File')
                raise StopException()
        return scan_file

    def run(self, nr_scans, nr_repeat, output_file, start_scanid, spec_file):
        scans = nr_repeat * nr_scans
        if start_scanid == -1:
            start_scanid = self.getEnv('ScanID') - scans + 1

        scan_dir = self.getEnv('ScanDir')
        spec_file = self.get_input_file(spec_file)
        input_file = os.path.join(scan_dir, spec_file)

        with open(input_file, 'r') as f:
            mem_file = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

        start_scan_pos = 0
        while True:
            self.checkPoint()
            start_scan_pos = mem_file.rfind('#S', 0, start_scan_pos-1)
            if start_scan_pos < 0:
                raise LookupError
            mem_file.seek(start_scan_pos)
            line = mem_file.readline()
            scan_nr = int(line.split()[1])
            if scan_nr == start_scanid:
                break

        for rp in range(nr_repeat):
            o_file = self.get_output_file(output_file)
            self.info('Saving data in %s ...' % o_file)
            first_scan = start_scanid + (nr_scans) * rp
            last_scan = first_scan + nr_scans
            with open(o_file, 'w') as f:
                line = '#S 1 NoData\n#C\n\n\n'
                line += '#S 2 nextract scans[%d %d] from %s\n' % \
                    (first_scan, last_scan, spec_file)
                f.write(line)
                for nr_scan in range(nr_scans):
                    while True:
                        line = mem_file.readline()

                        if 'ended' in line:
                            break
                        if nr_scan != 0 and '#' in line or line == '\n':
                            pass
                        else:
                            f.write(line)
                f.write(line)

            if rp != nr_repeat-1:
                next_scan = mem_file.find("#S")
                mem_file.seek(next_scan)
                line = mem_file.readline()


class ic_auto(Macro):
    param_def = [['positions',
                  [['pos', Type.Float, None, 'energy'], {'min': 1}],
                  None, 'List of [energies]'],
                 ['chambers',
                  [['chamber', Type.String, 'all', 'i0, i1, i2 or all'],
                   {'min': 1}],
                  None, 'List of [channels]'],
                 ['wait_time',Type.Float, 15, 'waiting time to calibrate']]

    def run(self, positions, chambers, wait_time):
        use_moco = False
        if 'all' in chambers:
            chambers = ['i0', 'i1', 'i2']

        if 'i0' in chambers or 'I0' in chambers:
            use_moco = True

        chns = []
        energy = self.getMoveable('energy')
        for chamber in chambers:
            chns.append(self.getExpChannel('e_{0}_1'.format(chamber)))
            chns.append(self.getExpChannel('e_{0}_2'.format(chamber)))

        moco_dev = PyTango.DeviceProxy('bl22/oh/moco')
        moco_status = moco_dev.read_attribute('MocoState').value

        if use_moco:
            self.info('Stopping moco...')
            self.moco_stop()
            self.set_moco_piezo(5)

        self.em_findmaxrange(energy, positions, chns, wait_time)

        if use_moco:
            self.set_moco_piezo(5)
            if moco_status != 'IDLE':
                self.info('Starting moco again...')
                self.moco_go()


class ohmotors(Macro):
    """
    Macro to turn ON/OFF the motor of the optical hutch.
    """
    param_def = [['state', Type.String, None, 'State: ON or OFF']]

    MOTORS = ('oh_fsm1_z', 'oh_vcm_bend', 'oh_vcm_jack1', 'oh_vcm_jack2',
              'oh_vcm_jack3', 'oh_vcm_x1', 'oh_vcm_x2', 'oh_fsm2_z',
              'oh_dcm_jack1', 'oh_dcm_jack2', 'oh_dcm_jack3',
              'oh_dcm_xtal1_roll', 'oh_dcm_xtal2_roll',
              'oh_dcm_x', 'oh_diag_foil_z', 'oh_diag_bottom',
              'oh_diag_left', 'oh_diag_right', 'oh_diag_top', 'oh_fsm3_z',
              'oh_vfm_bend', 'oh_vfm_jack1', 'oh_vfm_jack2', 'oh_vfm_jack3',
              'oh_vfm_x1', 'oh_vfm_x2', 'oh_fsm4_z')

    def run(self, state):
        state = state.lower()
        if state not in ['on', 'off']:
            raise ValueError('You must pass: on or off')

        power = state == 'on'
        for motor_name in self.MOTORS:
            try:
                motor = self.getDevice(motor_name)
                motor.write_attribute('poweron', power)
                self.output('{0}.poweron={1}'.format(motor_name, power))
            except Exception:
                self.error('Can not configure {0}'.format(motor_name))
                status = motor.read_attribute('statusdetails').value
                self.error('Error: {0}'.format(status))


class set_user_path(Macro):
    """
    Macro to set the user path used on startup macro
    """

    param_def = [['path', Type.String, None, 'Path to the user folder'],
                 ['scan_id', Type.Integer, Optional, 'Start scan ID']]

    def run(self, path, scan_id):
        if not os.path.exists(path):
            raise ValueError('The path {} is not exists. '
                             'Could you check it?'.format(path))

        self.setEnv('startup.UserPath', path)
        self.output('User path set to: {}'.format(path))
        if scan_id is not None:
            if scan_id < 0:
                raise ValueError('The scan id must be positive')
            self.setEnv('ScanID', scan_id)


class get_user_path(Macro):
    """
    Macro to get the user path set on the startup macro
    """
    result_def = [['path', Type.String, None, 'User path set']]

    def run(self):
        try:
            path = self.getEnv('UserPath', macro_name='startup')
        except Exception:
            raise RuntimeError('You should set the user path first: '
                               'set_user_path <path> ')
        self.output('User path set to: {}'.format(path))
        return path


class startup(Macro):
    """
    Macro to create
    """

    def run(self, *args):
        user_path = self.get_user_path().getResult()
        name = time.strftime('%Y%m%d')
        data_path = os.path.join(user_path, name)
        if not os.path.exists(data_path):
            os.makedirs(data_path)

        base_filename = os.path.join(data_path, name)
        dat_filename = base_filename + '.dat'
        h5_filename = base_filename + '.h5'
        lima_filename = base_filename + '.lima'

        dat_filename = self.get_outfilename(dat_filename).getResult()
        h5_filename = self.get_outfilename(h5_filename).getResult()
        scan_id = self.getEnv('ScanID')
        self.newfile([dat_filename, h5_filename, lima_filename], scan_id)
