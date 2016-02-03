from numpy import linspace, arange
from sardana.macroserver.macro import Type, Macro, ParamRepeat
from taurus import Device
import PyTango
from bl22tools import MythenPostProcessing, ReadFile
import time

DEV_STATE_ALARM = PyTango._PyTango.DevState.ALARM
DEV_STATE_MOVING = PyTango._PyTango.DevState.MOVING
DEV_STATE_ON = PyTango._PyTango.DevState.ON

# TODO: set this variable in the environment
XTAL_BRAGG_LIM = [[20, 75], [20, 75], [0, 130], [0, 130]]


class CLEAR(object):
    """
    Class to control the CLEAR
    """
    # Name convention:
    # C: Clear
    # A: Analyzer
    # D: Detector
    # SL: Slit
    # AB: Analyzer Bender
    # (X,Y,Z): Axes translation and with R is rotation
    # (D, U): Down/Up

    # Physical motors
    CAXR = 'motor/eh_ipap_ctrl/28'
    CAY = 'motor/eh_ipap_ctrl/26'
    CAZ = 'motor/eh_ipap_ctrl/27'
    CDMASK = 'motor/eh_ipap_ctrl/34'
    CDX = 'motor/eh_ipap_ctrl/35'
    CDXR = 'motor/eh_ipap_ctrl/31'
    CDY = 'motor/eh_ipap_ctrl/33'
    CDZ = 'motor/eh_ipap_ctrl/32'
    CSLX1 = 'motor/eh_ipap_ctrl/21'
    CSLX2 = 'motor/eh_ipap_ctrl/22'
    CSLXR = 'motor/eh_ipap_ctrl/25'
    CSLZ1 = 'motor/eh_ipap_ctrl/23'
    CSLZ2 = 'motor/eh_ipap_ctrl/24'
    CABD = 'motor/eh_ipap_ctrl/36'
    CABU = 'motor/eh_ipap_ctrl/37'

    #PseudoMotors
    XTAL = 'pm/dpm_ctrl_crystal/1'
    BRAGG = 'pm/clear_bragg_ctrl/1'
    MASK = 'pm/dpm_ctrl_cdfilter/1'
    DET = 'pm/dpm_ctrl_cdet/1'
    ENERGY = 'pm/eout_ctrl/1'

    #Controllers
    BRAGG_CTRL = 'controller/braggcontroller/clear_bragg_ctrl'

    def init_clear(self):
        self.caxr = Device(self.CAXR)
        self.cay = Device(self.CAY)
        self.caz = Device(self.CAZ)
        self.cdmask = Device(self.CDMASK)
        self.cdx = Device(self.CDX)
        self.cdxr = Device(self.CDXR)
        self.cdy = Device(self.CDY)
        self.cdz = Device(self.CDZ)
        self.cslx1 = Device(self.CSLX1)
        self.cslx2 = Device(self.CSLX2)
        self.cslxr = Device(self.CSLXR)
        self.cslz1 = Device(self.CSLZ1)
        self.cslz2 = Device(self.CSLZ2)
        self.cabd = Device(self.CABD)
        self.cabu = Device(self.CABU)

        self.physical_motor = [self.caxr, self.cay, self.caz, self.cdmask,
                               self.cdx, self.cdxr, self.cdy, self.cdz,
                               self.cslx1, self.cslx2, self.cslxr, self.cslz1,
                               self.cslz2, self.cabd, self.cabu]

        self.xtal = Device(self.XTAL)
        self.bragg = Device(self.BRAGG)
        self.mask = Device(self.MASK)
        self.det = Device(self.DET)
        self.energy = Device(self.ENERGY)
        self.bragg_ctrl = Device(self.BRAGG_CTRL)

    def clear_turn_onoff(self, power):
        if power == 'ON':
            pwr = True
        elif power == 'OFF':
            pwr = False
        else:
            raise ValueError('The value should be ON/OFF')

        for motor in self.physical_motor:
            motor.write_attribute('PowerON', pwr)

    def _find_pos(self, motor, value):
        labels = str(motor.read_attribute('Labels').value).split()
        if value not in labels:
            raise ValueError('%s is not a valid. See the help' % value)

        # Move to the selected detector
        for label in labels:
            if value in label:
                # mythen:0 or Si111:0
                pos = int(label.split(':')[1])
                break
        return pos

    def _move_motor(self, motor, pos):
        mv_macro, _ = self.createMacro('mv', motor, pos)
        self.runMacro(mv_macro)

    def set_xtal(self, xtal):
        pos = self._find_pos(self.xtal, xtal)

        bragg_min, bragg_max = XTAL_BRAGG_LIM[pos]
        current_bragg = self.bragg.read_attribrute('Position').value
        if current_bragg < bragg_min or current_bragg > bragg_max:
            msg = ('It is not possible to select %s, you will have a '
                   'collision. You should move the bragg first in [%f, '
                   '%f]' % (xtal, bragg_min, bragg_max))
            raise RuntimeError(msg)

        # Set the new bragg limits
        conf_bragg = self.bragg.get_attribute_config('Position')
        conf_bragg.max_value = str(bragg_max)
        conf_bragg.min_value = str(bragg_min)
        self.bragg.set_attribute_config(conf_bragg)

        # Move to selected crystal
        self._move_motor(self.xtal, pos)

    def set_detector(self, det):
        pos = self._find_pos(self.det, det)
        self._move_motor(self.det, pos)

    def set_mask(self, mask):
        pos = self._find_pos(self.mask, mask)
        self._move_motor(self.mask, pos)

    def move_bragg(self, pos):
        current_bragg = self.bragg.read_attribute('Position').value
        prop_name = 'bragg_tolerance'
        tolerance_prop = self.bragg_ctrl.get_property(prop_name)
        bragg_tolerance = float(tolerance_prop[prop_name][0])

        # Verifing if there are software limits
        position_conf = self.bragg.get_attribute_config('Position')
        try:
            bragg_min = float(position_conf.min_value)
            bragg_max = float(position_conf.max_value)
        except:
            msg = ('You must set first the crystal to set the limits.')
            raise RuntimeError(msg)

        if pos < bragg_min or pos > bragg_max:
            msg = ('It is not possible to move the bragg to %f. The bragg '
                   'range is [%f, %f]' %(pos, bragg_min, bragg_max))
            raise ValueError(msg)

        # Generate trajectory
        num_steps = int(abs(current_bragg - pos) / bragg_tolerance) + 1
        positions = [pos]
        if num_steps > 1:
            # To avoid the approximation in the linspace and remove current pos
            num_steps += 1
            positions = linspace(current_bragg, pos, num_steps)[1:]

        for next_position in positions:
            self._move_motor(self.bragg, next_position)

    def move_energy(self, pos):
        bragg_pos = self.energy.CalcPhysical(pos)
        self.move_bragg(bragg_pos)


################################################################################
#
#                           CLEAR Macros
#
################################################################################

class clearon(Macro, CLEAR):
    """
    Macro to turn ON CLEAR motors
    """

    param_def = []

    def run(self):
        self.init_clear()
        self.clear_turn_onoff('ON')


class clearoff(Macro, CLEAR):
    """
    Macro to turn OFF CLEAR motors
    """

    param_def = []

    def run(self):
        self.init_clear()
        self.clear_turn_onoff('OFF')


class clearmv(Macro, CLEAR):
    """
    Macro to move the bragg or Energy out
    """

    param_def = [['motor', Type.PseudoMotor, None, 'Motor.'],
                 ['pos', Type.Float, None, 'Position.']]

    def run(self, motor, pos):
        self.init_clear()
        
        if motor.full_name == self.bragg.getFullName():
            self.move_bragg(pos)
        elif motor.full_name == self.ENERGY.getFullName():
            self.move_energy(pos)
        else:
            bragg_name = self.bragg.getDisplayName().split()[0]
            eout_name = self.energy.getDisplayName().split()[0]
            raise Exception(('This macro only works with: %s and %s' %
                             (bragg_name, eout_name)))




# Todo: Old macros. We should implement them with the class CLEAR
class clearconfig(Macro):
    """
    Macro to set the value of: crystal, detector, filter and energy order.
    The macro can receive a list of parameter with the value:
        xtal: Si111, Si220, Si400, Ge111,
        dect: xxxx
        mask: xxx
        n: xxxx

    If you do introduce any parameter the macro shows you the current value
    of all parameters
    """
    # TODO: finish the help with each parameter values

    param_def = [['attr', Type.String, None, 'Name of attribute'],
                 ['value', Type.String, '', 'Value for attribute']]

    XTAL_NAME = 'xtal'
    CRYSTAL_MOTOR = '__DO_NOT_TOUCH_CLEAR_CRYSTAL'
    DETECTOR_MOTOR = '__DO_NOT_TOUCH_CLEAR_DETECTOR'
    FILTERS_MOTOR ='__DO_NOT_TOUCH_CLEAR_FILTERS'
    BRAGG_CTRL = 'clear_bragg_ctrl' # 'braggctrl_dum' # 'pm_ctrl_clear_bragg'

    param_list =[[XTAL_NAME, CRYSTAL_MOTOR],
                 ['det', DETECTOR_MOTOR],
                 ['fil', FILTERS_MOTOR]]

    xtal_bragg = {0: [20, 75], 1: [0, 130], 2: [0, 130], 3: [0, 136]}

    PARAM_NAME = 0
    MOTOR_NAME = 1

    def run(self, attr, value):
        attr = attr.lower()
        for param in self.param_list:
            if attr == param[self.PARAM_NAME]:
                motor = param[self.MOTOR_NAME]
                break
            else:
                self.error('This attribute is not implemented')
                return

        #first implementation:
        if value !='':
            if attr == self.XTAL_NAME:
                self._checkBragg(value)
                self._setBraggLimits(value)

            value = float(value)
            macro = 'mv %s %f' % (motor,value)
            self.info('Moving %s to %f....' %(attr, value))
            self.execMacro(macro)
            self.info('Done!')
        else:
            position =  self.getPseudoMotor(motor).position
            self.info('%s is in %f Position' %(attr, position))

    def _checkBragg(self, value):
         self.ctrl = self.getController(self.BRAGG_CTRL)
         self.motor = self.getPseudoMotor(self.ctrl.elementlist[0])
         current_pos = self.motor.position
         key = int(value)

         if not self.xtal_bragg.has_key(key):
             raise Exception('%d is not a valid position' % key)

         min, max = self.xtal_bragg[key]
         if current_pos < min or current_pos > max:
             msg = ('It is not possible to selet this crystal. '
                    'Bragg range angle(%d,%d)' % (min, max))
             raise Exception (msg)



    def _setBraggLimits(self, value):
        attr_conf = self.motor.get_attribute_config('Position')
        key = int(value)
        min, max = self.xtal_bragg[key]
        attr_conf.max_value = str(max)
        attr_conf.min_value = str(min)
        self.motor.set_attribute_config(attr_conf)


class clearascan(Macro):
    """This macro does a scan with the bragg or energy pseudomotor"""

    param_def = [['motor', Type.PseudoMotor, None, 'Motor.'],
                 ['startpos', Type.Float, None, 'Start position.'],
                 ['endpos', Type.Float, None, 'End position.'],
                 ['nrofpoints', Type.Float, None, 'number of points.'],
                 ['inttime', Type.Float, None, 'Integration time per  point.']]


    def _checkLim(self, motor, startpos, endpos):
        attr_pos = motor.get_attribute_config('Position')
        min = float(attr_pos.min_value)
        max = float(attr_pos.max_value)

        for pos in [startpos, endpos]:
            if pos > max or pos < min:
                msg = ('It is not possible to move the bragg to %f. '
                       'The bragg range is [%f, %f]' % (pos, min, max))
                raise Exception(msg)

    def prepare(self, motor, startpos, endpos, nrofpoints, inttime):
        if motor.name == 'clear_bragg':
            self._checkLim(motor, startpos, endpos)

        if startpos!=motor.position:
            macro = 'clearmv %s %f' % (motor.name, startpos)
            self.execMacro(macro)


    def run(self, motor, startpos, endpos, nrofpoints, inttime):
        macro =('ascan %s %f %f %d %f' % (motor.name, startpos, endpos,
                                          nrofpoints, inttime))
        self.execMacro(macro)




class comp(Macro):
    """
    Macro to calibrate the experimental energy scale for the Mythen. The
    macro move the Eout (clear energy out) to the Energy selected, after it
    runs a scan with the monochromator, it calculates the linear dispersion
    and set the paramter A and B of the Mythen.
    """

    param_def = [['E', Type.Float, None, 'clear energy out'],
                 ['deltaE', Type.Float, None, 'delta energy to run the scan'],
                 ['nrofpoints', Type.Integer, None, 'number of points.'],
                 ['inttime', Type.Float, 0.1, 'Integration time per  point.'],
                 ['pixmin', Type.Integer, 0, 'Minimun pixel'],
                 ['pixmax', Type.Integer, 1280, 'Maximun pixel'],
                 ['threshold', Type.Integer, 10, 'Level of the noise'],]



    def run(self, E, deltaE, nr, inttime, pixmin, pixmax, threshold):
        mg = self.getEnv('CompMntGrp')
        filelog_name = self.getEnv('MythenScaleLog')

        self.info('Moving Eout...')
        self.execMacro('clearmv Eout %f' % E)
        mg_bkp = self.getEnv('ActiveMntGrp')
        try:
            self.setEnv('ActiveMntGrp', mg)
            startpos = E - deltaE
            endpos = E + deltaE

            macro = ('ascan %s %f %f %d %f' % ('energy', startpos, endpos,
                                               nr, inttime))

            scanid = self.getEnv('ScanID')
            # TODO: Use the getResult method and do not read from the file.
            #scan_data = self.execMacro(macro).getResult()
            self.execMacro(macro)
            filedata_name = self.getEnv('ScanDir')
            for i in self.getEnv('ScanFile'):
                if 'h5' in i:
                    filedata_name += '/%s' % i
                    break
            else:
                self.error('You should set the h5 file to save the mythen data')
                raise RuntimeError()

            filedata = ReadFile(filedata_name)
            mythen_data = filedata.get_channel_data(scanid, 'm_raw')
            energy_data = filedata.get_channel_data(scanid, 'energy')
            self.info('Calculating the linear dispersion....')
            post_proc = MythenPostProcessing(mythen_data, energy_data)
            a, b, fit = post_proc.calc_linear_dispersion(pixmin, pixmax,
                                                         threshold)

            self.info('Results: A=%f, B=%f' % (a, b))
            self.info('Configuring Mythen...')
            mythen_device = Device('mythen')
            mythen_device.write_attribute('ScaleA', a)
            mythen_device.write_attribute('ScaleB', b)
            with open(filelog_name, 'a') as f:
                line = time.asctime()
                line += '/tScanID:%f/tA:%f/tB:%f/tCBragg:%f' % (scanid, a, b,
                                                                scanid, cbragg)
                f.write(line)

        except Exception as e:
            self.error('There was an exception during the scan %s' % e)
        finally:
            self.setEnv('ActiveMntGrp', mg_bkp)


class mythencomp(Macro):
    """
    Macro to extrat to file the compensated value
    """
    param_def = [['outputFile', Type.String,  None, 'Name for the output file'],
                 ['scanid', Type.Integer, -1, 'Scan id [last scan]'],
                 ['pixmin', Type.Integer, 100, 'Minimum pixel [100]'],
                 ['pixmax', Type.Integer, 1000, 'Maximun pixel [1000]'],
                 ['threshold', Type.Integer, 10, 'Noise threshold [10]']]

    def run(self, filename,scanid, pixmin, pixmax, threshold):
        dir_name = self.getEnv('ScanDir')
        h5file_name= dir_name
        datfile_name=dir_name
        for i in self.getEnv('ScanFile'):
            if 'h5' in i:
                h5file_name += '/%s' % i
            if 'dat' in i:
                datfile_name +='/%s' % i
        if scanid == -1:
            scanid = self.getEnv('ScanID') - 1
        filedata = ReadFile(h5file_name)
        mythen_data = filedata.get_channel_data(scanid, 'm_raw')
        energy_data = filedata.get_channel_data(scanid, 'energy')
        post_proc = MythenPostProcessing(mythen_data, energy_data)
        result = post_proc.calc_linear_dispersion(pixmin, pixmax, threshold)
        a = result[0]
        b = result[1]
        self.info('A,B value: %f,%f' % (a,b))
        data_comp = post_proc.calc_compensation(a)
        new_data = post_proc.calc_sum(data_comp)
        with open(filename, 'w') as f:
            line = '#F %s\n' % filename
            line += '#D %s\n\n' % time.asctime()
            line += '#S %d energy sum of images\n' % scanid
            line += '#D %s\n' % time.asctime()
            line += '#O0 A_value  B_value\n'
            line += '#P0 %f %f\n' % (a, b)
            line += '#N 3\n'
            line += '#L pixel  mythen_comp  energy\n'
            f.write(line)
            for i, data in enumerate(new_data):
                energy = a*i+b
                f.write('%f  %f  %f\n' % (i, data, energy))
