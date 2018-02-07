import time
from sardana.macroserver.macro import Type, Macro
import PyTango


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
            t = value / self.RAMPSPEED
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
                    msg += '%s = %fV [Error: %f]\n' % (io, current_value,
                                                       error)
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

    device_name = 'bl22/ct/bl22gasfilling'

    def __init__(self, macro_obj):
        self.macro = macro_obj
        self.device = PyTango.DeviceProxy(self.device_name)

    def wait(self):
        while True:
            self.macro.checkPoint()
            state = self.device.state()
            if state in [PyTango.DevState.ALARM, PyTango.DevState.ON]:
                break
            time.sleep(0.1)
        if state == PyTango.DevState.ALARM:
            status = self.device.status()
            raise RuntimeError('The DS is in ALARM state: %s' % status)
        else:
            self.macro.output('The process has ended successfully')

    def fill(self, values):
        v = []
        is_open_al_valve = False
        io0_energy = 0
        self.macro.shc()
        for i in values:
            if i[0] == 0:
                is_open_al_valve = True
                io0_energy = i[1]
                self.macro.info('Opening Aluminium valve...')
                self.macro.openAl()
            for j in i:
                v.append(j)

        self.macro.info('Starting the filling...')
        self.device.fill(v)
        self.wait()
        if is_open_al_valve and io0_energy > 4000:
            self.macro.info('Closing Aluminium valve...')
            self.macro.closeAl()
    
        self.state()

    def state(self):
        
        msg_result = '  Ar: {0}%\n  He: {1}%\n  Kr: {2}%\n  N2: {3}%\n  ' \
                     'Xe: {4}%'
        n2_attr_name = 'IO{0}N2'
        he_attr_name = 'IO{0}He'
        ar_attr_name = 'IO{0}Ar'
        kr_attr_name = 'IO{0}Kr'
        xe_attr_name = 'IO{0}Xe'

        for i in range(3):
            n2 = self.device.read_attribute(n2_attr_name.format(i)).value
            he = self.device.read_attribute(he_attr_name.format(i)).value
            ar = self.device.read_attribute(ar_attr_name.format(i)).value
            kr = self.device.read_attribute(kr_attr_name.format(i)).value
            xe = self.device.read_attribute(xe_attr_name.format(i)).value
            self.macro.output('IO{0} Gases'.format(i))
            self.macro.output(msg_result.format(ar, he, kr, n2, xe))

    def clean(self, io):
        self.macro.output('Starting the purge...')
        self.macro.shc()
        self.device.clean(io)
        self.wait()

    def stop(self):
        self.macro.output('Send stop to de device...')
        self.device.stop()


class gasClean(Macro):
    """
    Macro to clean the IO Chamber.
    """

    hints = {}

    param_def = [['values', [["IOChamber", Type.Integer, None, ""],
                             {'min': 1, 'max': 3}],
                  None, 'List of values']]

    def run(self, io):
        self.gas_filling = GasFillBase(self)
        self.gas_filling.clean(io)

    def on_abort(self):
        self.gas_filling.stop()


class getFill(Macro):
    """
    Macro to clean the IO Chamber.
    """

    hints = {}
   
    def run(self):
        self.gas_filling = GasFillBase(self)
        self.gas_filling.state()


class gasF(Macro):
    """
    Macro to fill the IO Chambers 0 and 1 with
    the same energy
    """

    param_def = [["energy", Type.Integer, None, "energy value"]]

    def run(self, energy):
        self.gasFill([[0, energy], [1, energy]])


class gasFill(Macro):
    """
    Macro to fill the IO Chamber.
    """

    hints = {}

    param_def = [['values',
                  [["IOChamber", Type.Integer, None,
                    "IO chamber number [0, 1, 2]"],
                   ["energy", Type.Integer, None, "energy value"],
                   {'min': 1, 'max': 3}],
                  None, "List of values"]]

    def run(self, values):
        self.gas_filling = GasFillBase(self)
        self.gas_filling.fill(values)

    def on_abort(self):
        self.gas_filling.stop()



class AluminiumValve(object):
    def __init__(self, macro, timeout=10):
        self.eps = PyTango.DeviceProxy('bl22/ct/eps-plc-02')
        self.timeout = timeout
        self.macro = macro

    def write(self, value):
        t = time.time()
        self.eps.write_attribute('VC_PNV_EH01_02', value)
        while True:
            self.macro.checkPoint()
            v = self.eps.read_attribute('VC_PNV_EH01_02').value
            if v == value:
                break
            if (time.time() - t) > self.timeout:
                raise RuntimeError('To open/close the valve takes too'
                                   'much time')
            time.sleep(0.1)

    def get(self):
        v = self.eps.read_attribute('VC_PNV_EH01_02').value
        self.macro.output('The Al valve is {0}'.format(['CLOSE','OPEN'][v]))

    def open(self):
        self.write(1)

    def close(self):
        self.write(0)


class openAl(Macro):
    param_def = [['timeout', Type.Float, 10, 'Timeout']]

    def run(self, timeout):
        valve = AluminiumValve(self, timeout)
        valve.open()


class closeAl(Macro):
    param_def = [['timeout', Type.Float, 10, 'Timeout']]

    def run(self, timeout):
        valve = AluminiumValve(self, timeout)
        valve.close()


class getAl(Macro):
    
    def run(self):
        valve= AluminiumValve(self,10)
        valve.get()
