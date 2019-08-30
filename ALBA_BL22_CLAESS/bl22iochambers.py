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
    I1I2_DsName = 'bl22/ct/nhq_x0xx_02'
    AttrNames = {'i0': 'voltageA', 'i1': 'voltageA', 'i2': 'voltageB'}

    TOLERANCE = 10  # value in volts
    RAMPSPEED = 100  # V/s

    def run(self, chambers):
        attrs = []
        wait_time = 0
        factor = 10
        i0 = PyTango.DeviceProxy(self.I0_DsName)
        i12 = PyTango.DeviceProxy(self.I1I2_DsName)
        i0.write_attribute('rampSpeedA', self.RAMPSPEED)
        i12.write_attribute('rampSpeedA', self.RAMPSPEED)
        i12.write_attribute('rampSpeedB', self.RAMPSPEED)

        for io, value in chambers:
            io = io.lower()
            if io not in self.AttrNames.keys():
                self.error('Wrong name of the chamber %s. It should be %s' %
                           (io, self.AttrNames.keys()))
                return
            if io == 'i0':
                ds_name = self.I0_DsName
            else:
                ds_name = self.I1I2_DsName
            attr_name = ds_name + '/' + self.AttrNames[io]
            attr = PyTango.AttributeProxy(attr_name)
            attr.write(value)
            attrs.append([io, value, attr])
            t = value / self.RAMPSPEED
            if t > wait_time:
                wait_time = t
        wait_time += 5
        self.info('Waiting to set value: %f ....' % wait_time)
        t0 = time.time()
        while True:
            if time.time()-t0 > wait_time:
                break
            time.sleep(0.01)
            self.checkPoint()
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
    valve_name = 'bl22/eh/pnv-01'
    
    def __init__(self, macro_obj):
        self.macro = macro_obj
        self.device = PyTango.DeviceProxy(self.device_name)
        self.pnv01 = PyTango.DeviceProxy(self.valve_name)

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

    def _change_pnv01(self, close=True):
        if close:
            self.macro.info('Closing valve {} ...'.format(self.valve_name))
            state = PyTango._PyTango.DevState.CLOSE
            action = self.pnv01.close
        else:
            self.macro.info('Opening valve {} ...'.format(self.valve_name))
            state = PyTango._PyTango.DevState.OPEN
            action = self.pnv01.open

        pnv01_state = self.pnv01.state()
        if pnv01_state != state:
            action()
            t = time.time()
            while True:
                pnv01_state = self.pnv01.state()
                if pnv01_state == state:
                    break
                if time.time() - t > 20:
                    raise RuntimeError('It is not possible to {} the '
                                       'valve. Check it'.state)
                time.sleep(0.1)
        self.macro.info('Finished valve operation')

    def fill(self, values):
        v = []
        is_open_al_valve = False
        io0_energy = 0
        self.macro.shc()
        open_pnv = False
        pnv01_state = self.pnv01.state()
        if pnv01_state == PyTango._PyTango.DevState.OPEN:
            open_pnv = True

        for i in values:
            if i[0] == 0:
                is_open_al_valve = True
                io0_energy = i[1]
                self.macro.Alout()
                self._change_pnv01(close=True)
            for j in i:
                v.append(j)

        self.macro.info('Starting the filling...')
        self.device.fill(v)
        self.wait()
        if is_open_al_valve and io0_energy > 4000:
            self.macro.Alin()
        if open_pnv:
            self._change_pnv01(close=False)
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
        self._change_pnv01(close=True)
        self.macro.info('Sending command to the PLC')
        self.device.clean(io)
        self.macro.info('Waiting...')
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
        self.macro.info('Opening Aluminium valve...')
        self.write(1)

    def close(self):
        self.macro.info('Closing Aluminium valve...')
        self.write(0)


class Alout(Macro):
    param_def = [['timeout', Type.Float, 10, 'Timeout']]

    def run(self, timeout):
        valve = AluminiumValve(self, timeout)
        valve.open()
        valve.get()


class Alin(Macro):
    param_def = [['timeout', Type.Float, 10, 'Timeout']]

    def run(self, timeout):
        valve = AluminiumValve(self, timeout)
        valve.close()
        valve.get()


class Alstate(Macro):
    
    def run(self):
        valve = AluminiumValve(self, 10)
        valve.get()
