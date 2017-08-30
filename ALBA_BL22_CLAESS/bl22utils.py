import time
import datetime
import os
import mmap
from sardana.macroserver.macro import macro, Type, Macro, ViewOption, ParamRepeat
import PyTango, taurus
from taurus.console.table import Table
import pyIcePAP
from albaemlib import AlbaEm


def _getMotorAlias(dev_name):
    return PyTango.Database().get_alias(dev_name)


class wa_print(Macro):
    env = ('Printer',)

    param_def = []

    def prepare(self, **opts):
        self.all_motors = self.findObjs('.*', type_class=Type.Moveable)
        self.table_opts = {}

        printer_name = self.getEnv('Printer')
        if printer_name == None:
            print 'Printer is None, set printer Name in Printer enviroment'
            return
       
        self.printer = os.popen('lpr -P %s' %printer_name,'w')

    def run(self):
        nr_motors = len(self.all_motors)
        if nr_motors == 0:
            self.output('No motor defined')
            return
        
        d = datetime.datetime.now().isoformat(' ')
        
        self.printer.write('\n\nCurrent positions (user) on %s\n\n\n' %d)
        self.output('Current positions (user) on %s' %d) 
        
        show_dial = self.getViewOption(ViewOption.ShowDial)
        motor_width = 9
        motor_names = []
        motor_pos   = []
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
                motor_pos.append((pos,dial_pos))
            else:
                motor_pos.append((pos,))

            motor_width = max(motor_width,len(name))

        fmt = '%c*.%df' % ('%',motor_width - 5)

        table = Table(motor_pos, elem_fmt=[fmt],
                      col_head_str=motor_names, col_head_width=motor_width,
                      **self.table_opts)
        for line in table.genOutput():
            self.output(line)
            self.printer.write(line+'\n')

        self.printer.close()

@macro()
def waitFE(self):
    self.execMacro('fewait')

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
    jack_steps = 5128 #steps_per_unit 1mm
    icepap_name = 'icebl2202'

    motors_conf = [[PyTango.DeviceProxy('motor/eh_ipap_ctrl/6'), 1085],
                   [PyTango.DeviceProxy('motor/eh_ipap_ctrl/7'), 28300],
                   [PyTango.DeviceProxy('motor/eh_ipap_ctrl/5'), 15210]]
    
    def run(self):
        self.execMacro('mv tripod_z 16')
        macro = 'ipap_homing True False tripod_j1 -1 tripod_j2 -1 tripod_j3 -1'
        self.execMacro(macro)
        states=[]    

        #go to home position horizontal
        for motor,offset in self.motors_conf:
            motor.step_per_unit = 1
            motor.position=offset
            states.append(motor.state)

        #wait for each motor finish
        while True:
           time.sleep(0.1)
           count = 0
           for state in states:
              if state() == PyTango._PyTango.DevState.ON:
                count +=1
           if count == 3:
                break
           
        #recover the step per unit set the current position as homming
        ipap = pyIcePAP.EthIcePAP(self.icepap_name)
        for motor,offset in self.motors_conf:
            motor.step_per_unit = self.jack_steps
            axis = int(motor.dev_name()[-1])
            ipap.setPosition(axis,0)


class reconfig(Macro):
    """Macro to configure some elements at nominal conditions: pcmac, fluo_x,
    Adlink, electrometers."""

    param_def = [["moco_pos", Type.Boolean, True, "Work in moco position mode"]]

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

        self.info('Set the electrometer polarity')
        host_e0 = self.getEnv('ElemI0Host')
        host_e1 = self.getEnv('ElemI1I2Host')
        e0 = AlbaEm(host_e0)
        if moco_pos:
            chn = ['1', 'NO']
        else:
            chn = ['1', 'YES']

        e0_channels = [chn, ['2', 'YES'], ['3', 'YES'], ['4', 'YES']]
        e0.setInvs(e0_channels)
        time.sleep(0.5)
        e0_inv = e0.getInvs([1,2,3,4])
        self.info('EMET-02 signal invertions: %s' % e0_inv)

        e1 = AlbaEm(host_e1)
        e1_channels = [['1', 'YES'], ['2', 'YES'], ['3', 'YES'], ['4', 'YES']]
        e1.setInvs(e1_channels)
        time.sleep(0.5)
        e1_inv = e1.getInvs([1,2,3,4])
        self.info('EMET-03 signal invertions: %s' % e1_inv)


class getScanFile(Macro):
    """
    The macro returns the scanFile: ScanDir+ScanFile
    """
    result_def = [['scan_filenames',Type.String, None, '']]

    def run(self):
        scan_dir = self.getEnv('ScanDir')
        scan_files = self.getEnv('ScanFile')
        scan_filenames = ''
        if type(scan_files) is not list:
            scan_files = [scan_files]
        for filename in scan_files:
            scan_filenames +='%s/%s,' % (scan_dir, filename)
            
        return scan_filenames


class getScanID(Macro):
    """
    The macro returns the scanid.
    """
        
    result_def = [['scanid',Type.Integer, None, '']]
    
    def run(self):
        scanid = self.getEnv('ScanID')
        return scanid


class HVread(Macro):
    """
    Macro to set the high voltage of the IO chambers power supplies.
    """

    param_def = [['chambers', [['chamber', Type.String, None, 'i0,i1 or i2'],
                               {'min': 1, 'max': 3}],
                  None, 'List of IO chambers']]


    I0_DsName = 'bl22/ct/nhq_x0xx_01'
    I1I2_DSName = 'bl22/ct/nhq_x0xx_02'
    AttrNames = {'i0': 'voltageA', 'i1': 'voltageA', 'i2': 'voltageB'}

    def run(self, chambers):
        factor = 10
        msg = ''
        for io in chambers:
            io = io.lower()
            if io not in self.AttrNames.keys():
                self.error('Wrong name of the chamber %s. It should be %s' %
                           (io, self.AttrNames.keys()))
                return
            if io == 'i0':
                ds_name = self.I0_DsName
            else:
                ds_name = self.I1I2_DSName
            attr_name = ds_name + '/' + self.AttrNames[io]
            attr = PyTango.AttributeProxy(attr_name)
            current_value = attr.read().value / factor
            msg += '%s = %fV \n' % (io, current_value)

        self.info(msg)

    
class HVset(Macro):
    """
    Macro to set the high voltage of the IO chambers power supplies.
    """

    param_def = [['chambers', [['chamber', Type.String, None, 'i0,i1 or i2'],
                               ['voltage', Type.Float, None, 'Voltage'],
                               {'min': 1, 'max': 3}],
                  None, 'List of IO chambers']]


    I0_DsName = 'bl22/ct/nhq_x0xx_01'
    I1I2_DSName = 'bl22/ct/nhq_x0xx_02'
    AttrNames = {'i0': 'voltageA', 'i1': 'voltageA', 'i2': 'voltageB'}
    
    TOLERANCE = 10  # value in volts
    RAMPSPEED = 100  # V/s

    def run(self, chambers):
        attrs = []
        wait_time = 0
        factor = 10
        for io, value in chambers:
            io = io.lower()
            if io not in self.AttrNames.keys():
                self.error('Wrong name of the chamber %s. It should be %s' %
                           (io, self.AttrNames.keys()))
                return
            if io == 'i0':
                ds_name = self.I0_DsName
            else:
                ds_name = self.I1I2_DSName
            attr_name = ds_name + '/' + self.AttrNames[io]
            attr = PyTango.AttributeProxy(attr_name)
            attr.write(value)
            attrs.append([io, value, attr])
            t = value/self.RAMPSPEED
            if t > wait_time:
                wait_time = t
        wait_time += 5
        self.info('Waiting to set value: %f ....' % wait_time)
        time.sleep(wait_time)
        msg = ''
        while len(attrs):
            rm = []
            for chamber in attrs:
                io, value, attr = chamber
                current_value = attr.read().value / factor
                error = abs(abs(current_value) - abs(value))
                if error <= self.TOLERANCE:
                    msg += '%s = %fV [Error: %f]\n' % (io, current_value, error)
                    rm.append(chamber)
            for i in rm:
                attrs.remove(i)
            self.checkPoint()
            time.sleep(0.1)

        self.info(msg)


class GasFillBase(object):
    """
    Macro to execute the quick Exafs experiment.
    """

    eps_name = 'bl22/ct/eps-plc-02'
    attrs = {'io2': {'energy': 'ConsignaI2_wr',
                    'set': 'PLC_CONFIG_I02_CM',
                    'done': 'CH3_done',
                    'pressure': 'FL_PST_EH01_03_AF',
                    'gases': {'Ar': 'TarjetI2_Ar',
                              'He': 'TarjetI2_He',
                              'Kr': 'TarjetI2_Kr',
                              'N2': 'TarjetI2_N2',
                              'Xe': 'TarjetI2_Xe'}
                    }
            }


    def fill(self, io, energy):
        if energy <= 4000 or energy >= 63000:
            raise Exception('The energy is out of range[4000,63000]')
        io = io.lower()
        eps = self.getDevice(self.eps_name)
        eps[self.attrs[io]['energy']] = energy
        eps[self.attrs[io]['set']] = 1
        self.info('Waiting....')
        while not eps[self.attrs[io]['done']]:
            time.sleep(0.01)
            self.checkPoint()

        # Time needed by the EPS DS to update the values
        time.sleep(3)

        msg = '%s fill done!\n' % io
        msg += 'Presure: %r\n' % eps[self.attrs[io]['pressure']].value
        for name, attr in self.attrs[io]['gases'].items():
            msg += '%s: %r' % (name, eps[self.attrs[io]['gases'][name]].value)

        self.output(msg)

    def clean(self, io):

        io = io.lower()
        eps = self.getDevice(self.eps_name)
        eps[self.attrs[io]['energy']] = 0
        eps[self.attrs[io]['set']] = 1

        self.info('Cleaning....')
        t1 = time.time()
        while True:
            self.checkPoint()
            time.sleep(0.10)
            if time.time() - t1 > 30:
               break

        self.output('IOChamber %r cleaned.' % io)


class gasClean(Macro, GasFillBase):
    """
    Macro to clean the IO Chamber.
    """

    hints = {}

    param_def = [["IOChamber", Type.String, None, ""],]

    def run(self, io):
        self.clean(io)


class gasFill(Macro, GasFillBase):
    """
    Macro to fill the IO Chamber.
    """

    hints = {}

    param_def = [["IOChamber", Type.String, None, "IO name [io0, io1, io2]"],
                 ["energy", Type.Float, None, "energy value"]]

    def run(self, io, energy):
        self.fill(io, energy)


class EMrange(Macro):
    param_def = [['chns',
                  [['ch', Type.CTExpChannel, None, 'electrometer chn'],
                   ['range',  Type.String, None, 'Amplifier range'], 
                   {'min':1, 'max':12}],
                  None, 'List of [channels,range]'],]

    def run(self, chns):
        for ch, rg in chns:
            old_range = ch.range
            ch.range = rg            
            self.output('%s changed range from %s to %s' %(ch, old_range,
                                                           ch.range))

class set_mode(Macro):
    """
    Macro to set the Measuement Group acording to the experiment type:
    * Transmission (transm)
    * Fluorescence (fluo)
    * CLEAR (clear)
    * ALL (all)
    """
    env = ('ContScanMG','DefaultMG', 'ActiveMntGrp')
    
    param_def = [['ExpType', Type.String, None, 'transm, fluo, clear, all']]
    
    exp_type = {'transm': ['mg_cont', 'mg_step'],
                'fluo': ['mg_xcont', 'mg_xstep'],
                'clear': ['mg_mcont', 'mg_mstep'],
                'all' : ['mg_all', 'mg_all']
                }

    def run(self, exptype):
        exptype = exptype.lower()
        
        if exptype not in self.exp_type:
            raise ValueError('The values must be: %r' % self.exp_type.keys())
        mg_cont, mg_step = self.exp_type[exptype]
        self.output('Setting mode...')
        self.setEnv('ContScanMG', mg_cont)
        self.setEnv('DefaultMG', mg_step)
        self.setEnv('ActiveMntGrp', mg_step)
        self.output('ContScanMG: %s\nDefaultMG: %s\n' %(mg_cont, mg_step))




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
            elif type(f) == str:
                if not '.dat' in f:
                    self.error('You should save the data on Spec File')
                    raise StopException()
                scan_file = f
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

        
        


