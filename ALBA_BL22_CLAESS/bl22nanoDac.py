# Created on Oct 28, 2013
# @author: droldan

from sardana.macroserver.macro import Macro, Type
import PyTango
import time
import math


class nDac(Macro):
    """Usage:
    nDac temp  (to read temperature)
    nDac sp1   (to read Heat SetPoint1)
    nDac sp1 300 (To write '300' on SetPoint1)
    nDac flux xxx (To write xxx on flux)
    Actuals Attributes accepted
    temp, sp1 (Heat SetPoint), flux (flow, 0 to 100 %), sp2 (Cool SetPoint)"""

    param_def = [
        ['attr', Type.String, None, 'Name of attribute'],
        ['value', Type.Float, float('inf'), 'Value for attribute']
    ]

    DS_NANODAC = 'bl22/ct/nanodac'
    num_try = 10
    # params = [[Name, register, R/W access, [limits]]]
    params = [['temp', 256, False, []],
              ['sp1', 5724, True, [-200, 400]],
              ['sp2', 5980, True, [-200, 400]],
              ['flux', 6016, True, [0, 100]]]

    def prepare(self, attribute, value):
        self.dev_proxy = PyTango.DeviceProxy(self.DS_NANODAC)
        self.dev_proxy.reconnect(False)
        time.sleep(0.1)
        self.dev_proxy.reconnect(True)
        time.sleep(0.1)

    def run(self, attribute, value):
        attribute = attribute.lower()
        for attr in self.params:
            if attribute == attr[0]:
                self.reg = attr[1]
                self.writable = attr[2]
                self.limits = attr[3]
                break
        else:
            self.error('This attribute is not implemented')
            return

        if math.isinf(value):
            self.getRegister(self.reg)
        else:
            if not self.writable:
                self.error('This attribute is not writable')
            else:
                if value < self.limits[0] or value > self.limits[1]:
                    self.error('The value is out of range: %s' % self.limits)
                else:
                    self.setRegister(self.reg, value)

        self.dev_proxy.reconnect(False)

    def setRegister(self, address, value):
        address = int(address)
        value = int(value * 10)
        self.output('Writing...')

        try:
            self.dev_proxy.writeint([address, value])
        except Exception:
            self.debug('It did not write the value')

        self.output('... %d Writted' % value)

    def getRegister(self, address):
        address = int(address)
        self.output('Reading...')
        try:
            value = self.dev_proxy.reg(address) / 10.
        except Exception:
            self.error('It does not read the register')
            return
        msg = 'Value %3.2f' % value
        self.output(msg)
