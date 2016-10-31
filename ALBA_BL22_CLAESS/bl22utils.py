from sardana.macroserver.macro import macro, Type, Macro, ViewOption, ParamRepeat
import PyTango, taurus
import time
import datetime
from taurus.console.table import Table
import os
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


class configpmac(Macro):
    """
    Macro to configure the Pmac to nominal conditions.
    """
    bragg_name = 'motor/dcm_pmac_ctrl/1'
    perp_name = 'motor/dcm_pmac_ctrl/3'
    pmac_name = "pmac"

    def run(self):
        self.info('Set bragg configuration...')
        pmac = taurus.Device(self.pmac_name)
        #Kp I130
        pmac.SetIVariable([130, 19000])
        #Kd I131
        pmac.SetIVariable([131, 400])
        #Kvff I132
        pmac.SetIVariable([132, 700])
        #K1 I133
        pmac.SetIVariable([133, 12000])
        #IM I134
        pmac.SetIVariable([134, 1])
        #Kaff I135
        pmac.SetIVariable([135, 500])

        bragg = PyTango.DeviceProxy(self.bragg_name)
        bragg.velocity = 2.5 #4
        bragg.acceleration = 0.1
        bragg.deceleration = 0.1

        self.info('Set perp configuration...')
        perp = PyTango.DeviceProxy(self.perp_name)
        perp.velocity = 0.5
        perp.acceleration = 0.1
        perp.deceleration = 0.1


class reconfig(Macro):
    """Macro to configure some elements at nominal conditions: pcmac, fluo_x,
    Adlink, electrometers."""

    param_def = [["moco_pos", Type.Boolean, True, "Work in moco position mode"]]

    def run(self, moco_pos):
        mg = self.getEnv('DefaultMG')
        self.info('Set Measurement Group: %s' % mg)
        self.setEnv('ActiveMntGrp', mg)
        self.info('Reconfig pcmac')
        self.execMacro('configpmac')
        
        self.info('Reconfig fluo_x')
        fluo_x = PyTango.DeviceProxy('motor/eh_ipap_ctrl/53')
        fluo_x.velocity = 0.8
        fluo_x.acceleration = 1

        self.execMacro('qExafsCleanup')
        
        self.execMacro('usebraggonly off')

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
        
        e1 = AlbaEm(host_e1)
        e1_channels = [['1', 'YES'], ['2', 'YES'], ['3', 'YES'], ['4', 'YES']]
        e1.setInvs(e1_channels)



class usebraggonly (Macro):
    """
    Macro to set the progam 12 of the Pmac to move only the bragg without
    perpendicular. It's meas that all the movement of the energy will do
    with the bragg only.
    
    If you don't pass the paramter the macro shows you the current state.
    
    """
    param_def = [['Enabled', Type.String, '', 'Active the bragg only movement']]

    PMAC_ATTR = 'controller/dcmturbopmaccontroller/dcm_pmac_ctrl/movebraggonly'
    ALLOW_VALUES = ['on', 'off']

    def run(self, value):
        dev = taurus.Attribute(self.PMAC_ATTR)
        if value != '':
            value = value.lower()
            if value not in self.ALLOW_VALUES:
                msg = ('You must pass: %s' % repr(self.ALLOW_VALUES))
                raise ValueError(msg)
            else:
                active = (value == 'on')
                dev.write(active)

        current_value = dev.read().value
        msg_act = 'Desabled'
        if current_value:
            msg_act = 'Enabled'
        msg = 'The movement of the bragg only is: %s' % msg_act
        self.info(msg)


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

