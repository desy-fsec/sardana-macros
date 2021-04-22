#!/usr/bin/env python
"""
Change active mg

28.5.2018: handles Debian-8 and Debian-9

"""

from __future__ import print_function
import os
import sys
from sardana.macroserver.macro import Macro, Type
# import time
from PyTango import DeviceProxy, DevFailed, Database, Except
import json
import HasyUtils
from taurus.console import Alignment

__all__ = ["delete_mg", "change_mg", "check_mg"]

# from taurus.console.list import List
Left, Right, HCenter = Alignment.Left, Alignment.Right, Alignment.HCenter


class MgConf:
    def __init__(self, poolName, mntgrpName, flagClear):
        self.db = Database()
        #
        # the pool for the Mg
        #
        try:
            self.poolMg = DeviceProxy(poolName)
        except Exception as e:
            Except.print_exception(e)
            print("failed to get proxy to ", poolName)
            sys.exit(255)
        #
        # find the MG
        #
        try:
            self.mg = DeviceProxy(mntgrpName)
        except Exception:
            lst = [mntgrpName, 'exp_t01', 'exp_c01', 'exp_c02']
            self.poolMg.command_inout('CreateMeasurementGroup', lst)
            self.mg = DeviceProxy(mntgrpName)

        if not flagClear:
            self.hsh = json.loads(self.mg.Configuration)
            self.masterTimer = self.findMasterTimer()
            self.index = len(self.mg.ElementList)
        else:
            self.hsh = {}
            self.hsh[u'controllers'] = {}
            self.hsh[u'description'] = "Measurement Group"
            self.hsh[u'label'] = mntgrpName
            self.index = 0

    def findMasterTimer(self):
        if not HasyUtils.versionSardanaNewMg():
            self.findMasterTimerD8()
        else:
            self.findMasterTimerD9()

    def findMasterTimerD8(self):
        for ctrl in self.hsh[u'controllers']:
            Channels = self.hsh[u'controllers'][ctrl][u'units'][u'0'][
                u'channels']
            for chan in Channels:
                if chan.find('dgg2') > 0:
                    temp = chan
                    if temp.find('0000') >= 0:
                        lst = temp.split("/")
                        temp = "/".join(lst[1:])
                    masterTimer = self.db.get_alias(str(temp))
                    return masterTimer
        raise ('MgUtils.findMasterTimer', "No timer found")

    def findMasterTimerD9(self):

        temp = self.hsh[u'timer']
        if temp.find('0000') >= 0:
            lst = temp.split("/")
            #
            # tango://haso113u.desy.de:10000/expchan/dgg2_d1_01/1
            #
            if lst[0].lower() == 'tango:':
                temp = "/".join(lst[3:])
            else:
                temp = "/".join(lst[1:])
            #
            # expchan/dgg2_d1_01/1
            #
            masterTimer = self.db.get_alias(str(temp))
        return masterTimer

    def findDeviceController(self, device):
        """
        returns the controller that belongs to a device
        """

        lst = []
        if self.poolMg.ExpChannelList is not None:
            lst = self.poolMg.ExpChannelList
        ctrl = None
        for elm in lst:
            chan = json.loads(elm)
            # chan:
            # {
            # u'axis': 17,
            # u'controller':
            # u'haso107klx:10000/controller/sis3820ctrl/sis3820_exp',
            # u'full_name': u'haso107klx:10000/expchan/sis3820_exp/17',
            # u'id': 146,
            # u'instrument': u'',
            # u'interfaces': [u'Object', u'PoolObject', u'Element',
            # u'ExpChannel', u'PoolElement', u'CTExpChannel', u'Acquirable'],
            # u'manager': u'exp_pool01',
            # u'name': u'exp_c17',
            # u'parent': u'sis3820_exp',
            # u'pool': u'exp_pool01',
            # u'source': u'haso107klx:10000/expchan/sis3820_exp/17/value',
            # u'type': u'CTExpChannel',
            # u'unit': u'0',
            # }
            if device == chan['name']:
                ctrl = chan['controller']
                break
        if ctrl is None and device.find("adc") >= 0:
            ctrl = os.getenv("TANGO_HOST") + "/" + \
                "controller/hasylabadcctrl/hasyadcctrl"
        elif ctrl is None and device.find("vfc") >= 0:
            ctrl = os.getenv("TANGO_HOST") + "/" + \
                "controller/vfcadccontroller/hasyvfcadcctrl"
        return ctrl

    def findFullDeviceName(self, device):
        """
          input: exp_c01
          returns: expchan/hasylabvirtualcounterctrl/1
        """

        lst = self.poolMg.AcqChannelList
        argout = None
        for elm in lst:
            chan = json.loads(elm)
            if device == chan['name']:
                #
                # from: expchan/hasysis3820ctrl/1/value
                # to:   expchan/hasysis3820ctrl/1
                #
                arr = chan['full_name'].split("/")
                argout = "/".join(arr[0:-1])
        if argout is None:
            print("Error with device")
            print(device)
            raise Exception('MgUtils.findFullDeviceName, %s' % device,
                            "failed to find  %s" % device)
        return argout

    def updateConfiguration(self):
        """
        json-dump the dictionary self.hsh to the Mg configuration
        """
        self.mg.Configuration = json.dumps(self.hsh)

    def addTimer(self, device):
        if not HasyUtils.versionSardanaNewMg():
            self.addTimerD8(device)
        else:
            self.addTimerD9(device)

    def addTimerD8(self, device):
        """
        add a timer to the Mg
        device: exp_t01
        """
        ctrl = self.findDeviceController(device)
        if ctrl not in self.hsh[u'controllers'].keys():
            self.masterTimer = device
            self.hsh[u'monitor'] = self.findFullDeviceName(device)
            self.hsh[u'timer'] = self.findFullDeviceName(device)
            self.hsh[u'controllers'][ctrl] = {}
            self.hsh[u'controllers'][ctrl][u'units'] = {}
            self.hsh[u'controllers'][ctrl][u'units'][u'0'] = {}
            self.hsh[u'controllers'][ctrl][u'units'][u'0'][u'channels'] = {}
            self.hsh[u'controllers'][ctrl][u'units'][u'0'][u'id'] = 0
            self.hsh[u'controllers'][ctrl][u'units'][u'0'][u'monitor'] = \
                self.findFullDeviceName(device)
            self.hsh[u'controllers'][ctrl][u'units'][u'0'][u'timer'] = \
                self.findFullDeviceName(device)
            self.hsh[u'controllers'][ctrl][u'units'][u'0'][u'trigger_type'] = 0

        ctrlChannels = self.hsh[u'controllers'][ctrl][u'units'][u'0'][
            u'channels']
        fullDeviceName = self.findFullDeviceName(device)
        if fullDeviceName not in ctrlChannels.keys():
            print("adding index", self.index, device)
            dct = {}
            dct[u'_controller_name'] = str(ctrl)
            dct[u'_unit_id'] = u'0'
            dct[u'conditioning'] = u''
            dct[u'data_type'] = u'float64'
            dct[u'data_units'] = u'No unit'
            dct[u'enabled'] = True
            dct[u'full_name'] = fullDeviceName
            dct[u'index'] = self.index
            self.index += 1
            dct[u'instrument'] = None
            dct[u'label'] = str(device)
            dct[u'name'] = str(device)
            dct[u'ndim'] = 0
            dct[u'nexus_path'] = u''
            dct[u'normalization'] = 0
            dct[u'output'] = True
            dct[u'plot_axes'] = []
            dct[u'plot_type'] = 0
            dct[u'shape'] = []
            dct[u'source'] = dct['full_name'] + "/value"
            ctrlChannels[fullDeviceName] = dct

    def addTimerD9(self, device):
        """
        add a timer to the Mg
        device: exp_t01
        """
        ctrl = self.findDeviceController(device)
        if ctrl not in self.hsh[u'controllers'].keys():
            self.masterTimer = device
            self.hsh[u'monitor'] = self.findFullDeviceName(device)
            self.hsh[u'timer'] = self.findFullDeviceName(device)
            self.hsh[u'controllers'][ctrl] = {}
            self.hsh[u'controllers'][ctrl][u'synchronizer'] = "software"
            self.hsh[u'controllers'][ctrl][u'channels'] = {}
            self.hsh[u'controllers'][ctrl][u'id'] = 0
            self.hsh[u'controllers'][ctrl][u'monitor'] = \
                self.findFullDeviceName(device)
            self.hsh[u'controllers'][ctrl][u'timer'] = \
                self.findFullDeviceName(device)
            self.hsh[u'controllers'][ctrl][u'trigger_type'] = 0

        ctrlChannels = self.hsh[u'controllers'][ctrl][u'channels']
        fullDeviceName = self.findFullDeviceName(device)
        if fullDeviceName not in ctrlChannels.keys():
            print("adding index", self.index, device)
            dct = {}
            dct[u'conditioning'] = u''
            dct[u'enabled'] = True
            dct[u'full_name'] = fullDeviceName
            dct[u'index'] = self.index
            self.index += 1
            dct[u'label'] = str(device)
            dct[u'name'] = str(device)
            dct[u'ndim'] = 0
            dct[u'normalization'] = 0
            dct[u'output'] = True
            dct[u'plot_axes'] = []
            dct[u'plot_type'] = 0
            dct[u'source'] = dct['full_name'] + "/value"
            ctrlChannels[fullDeviceName] = dct

    def addExtraTimer(self, device):
        if not HasyUtils.versionSardanaNewMg():
            self.addExtraTimerD8(device)
        else:
            self.addExtraTimerD9(device)

    #
    # add an extra timer to the measurement group
    #
    def addExtraTimerD8(self, device):
        """ device: exp_t01"""
        ctrl = self.findDeviceController(device)
        if ctrl not in self.hsh[u'controllers'].keys():
            self.hsh[u'controllers'][ctrl] = {}
            self.hsh[u'controllers'][ctrl][u'units'] = {}
            self.hsh[u'controllers'][ctrl][u'units'][u'0'] = {}
            self.hsh[u'controllers'][ctrl][u'units'][u'0'][u'channels'] = {}
            self.hsh[u'controllers'][ctrl][u'units'][u'0'][u'id'] = 0
            self.hsh[u'controllers'][ctrl][u'units'][u'0'][u'monitor'] = \
                self.findFullDeviceName(device)
            self.hsh[u'controllers'][ctrl][u'units'][u'0'][u'timer'] = \
                self.findFullDeviceName(device)
            self.hsh[u'controllers'][ctrl][u'units'][u'0'][u'trigger_type'] = 0

        ctrlChannels = self.hsh[u'controllers'][ctrl][u'units'][u'0'][
            u'channels']
        fullDeviceName = self.findFullDeviceName(device)
        if fullDeviceName not in ctrlChannels.keys():
            dct = {}
            dct[u'_controller_name'] = str(ctrl)
            dct[u'_unit_id'] = u'0'
            dct[u'conditioning'] = u''
            dct[u'data_type'] = u'float64'
            dct[u'data_units'] = u'No unit'
            dct[u'enabled'] = True
            dct[u'full_name'] = fullDeviceName
            dct[u'index'] = self.index
            self.index += 1
            dct[u'instrument'] = None
            dct[u'label'] = str(device)
            dct[u'name'] = str(device)
            dct[u'ndim'] = 0
            dct[u'nexus_path'] = u''
            dct[u'normalization'] = 0
            dct[u'output'] = True
            dct[u'plot_axes'] = []
            dct[u'plot_type'] = 0
            dct[u'shape'] = []
            dct[u'source'] = dct['full_name'] + "/value"
            ctrlChannels[fullDeviceName] = dct

    #
    # add an extra timer to the measurement group
    #
    def addExtraTimerD9(self, device):
        """ device: exp_t01"""
        ctrl = self.findDeviceController(device)
        if ctrl not in self.hsh[u'controllers'].keys():
            self.hsh[u'controllers'][ctrl] = {}
            self.hsh[u'controllers'][ctrl][u'synchronizer'] = "software"
            self.hsh[u'controllers'][ctrl][u'channels'] = {}
            self.hsh[u'controllers'][ctrl][u'id'] = 0
            self.hsh[u'controllers'][ctrl][u'monitor'] = \
                self.findFullDeviceName(device)
            self.hsh[u'controllers'][ctrl][u'timer'] = \
                self.findFullDeviceName(device)
            self.hsh[u'controllers'][ctrl][u'trigger_type'] = 0

        ctrlChannels = self.hsh[u'controllers'][ctrl][u'channels']
        fullDeviceName = self.findFullDeviceName(device)
        if fullDeviceName not in ctrlChannels.keys():
            dct = {}
            dct[u'conditioning'] = u''
            dct[u'enabled'] = True
            dct[u'full_name'] = fullDeviceName
            dct[u'index'] = self.index
            self.index += 1
            dct[u'label'] = str(device)
            dct[u'name'] = str(device)
            dct[u'ndim'] = 0
            dct[u'normalization'] = 0
            dct[u'output'] = True
            dct[u'plot_axes'] = []
            dct[u'plot_type'] = 0
            dct[u'source'] = dct['full_name'] + "/value"
            ctrlChannels[fullDeviceName] = dct

    def addCounter(self, device, flagDisplay, flagOutput):
        if not HasyUtils.versionSardanaNewMg():
            self.addCounterD8(device, flagDisplay, flagOutput)
        else:
            self.addCounterD9(device, flagDisplay, flagOutput)

    #
    # add a counter to the measurement group
    #
    def addCounterD8(self, device, flagDisplay, flagOutput):

        if device.find('sca_') == 0:
            return self.addSCA(device, flagDisplay, flagOutput)

        ctrl = self.findDeviceController(device)
        if ctrl not in self.hsh[u'controllers'].keys():
            print("MgUtils.addCounter adding controller ", ctrl)
            self.hsh[u'controllers'][ctrl] = {}
            self.hsh[u'controllers'][ctrl][u'units'] = {}
            self.hsh[u'controllers'][ctrl][u'units'][u'0'] = {}
            self.hsh[u'controllers'][ctrl][u'units'][u'0'][u'channels'] = {}
            self.hsh[u'controllers'][ctrl][u'units'][u'0'][u'id'] = 0
            self.hsh[u'controllers'][ctrl][u'units'][u'0'][u'monitor'] = \
                self.findFullDeviceName(self.masterTimer)
            self.hsh[u'controllers'][ctrl][u'units'][u'0'][u'timer'] = \
                self.findFullDeviceName(self.masterTimer)
            self.hsh[u'controllers'][ctrl][u'units'][u'0'][u'trigger_type'] = 0

        ctrlChannels = self.hsh[u'controllers'][ctrl][u'units'][u'0'][
            u'channels']
        fullDeviceName = self.findFullDeviceName(device)
        if fullDeviceName not in ctrlChannels.keys():
            print("adding index", self.index, device)
            dct = {}
            dct[u'_controller_name'] = str(ctrl)
            dct[u'_unit_id'] = u'0'
            dct[u'conditioning'] = u''
            dct[u'data_type'] = u'float64'
            dct[u'data_units'] = u'No unit'
            dct[u'enabled'] = True
            dct[u'full_name'] = fullDeviceName
            dct[u'index'] = self.index
            self.index += 1
            dct[u'instrument'] = u''
            dct[u'label'] = str(device)
            dct[u'name'] = str(device)
            dct[u'ndim'] = 0
            dct[u'nexus_path'] = u''
            dct[u'normalization'] = 0
            if flagOutput:
                dct[u'output'] = True
            else:
                dct[u'output'] = False
            dct[u'plot_axes'] = [u'<mov>']
            if flagDisplay:
                dct[u'plot_type'] = 1
            else:
                dct[u'plot_type'] = 0
            dct[u'shape'] = []
            dct[u'source'] = dct['full_name'] + "/value"
            ctrlChannels[fullDeviceName] = dct

    #
    # add a counter to the measurement group
    #
    def addCounterD9(self, device, flagDisplay, flagOutput):

        if device.find('sca_') == 0:
            return self.addSCA(device, flagDisplay, flagOutput)

        ctrl = self.findDeviceController(device)
        if ctrl not in self.hsh[u'controllers'].keys():
            print("MgUtils.addCounter adding controller ", ctrl)
            self.hsh[u'controllers'][ctrl] = {}
            self.hsh[u'controllers'][ctrl][u'synchronizer'] = "software"
            self.hsh[u'controllers'][ctrl][u'channels'] = {}
            self.hsh[u'controllers'][ctrl][u'id'] = 0
            self.hsh[u'controllers'][ctrl][u'monitor'] = \
                self.findFullDeviceName(device)
            self.hsh[u'controllers'][ctrl][u'timer'] = \
                self.findFullDeviceName(device)
            self.hsh[u'controllers'][ctrl][u'trigger_type'] = 0

        ctrlChannels = self.hsh[u'controllers'][ctrl][u'channels']
        fullDeviceName = self.findFullDeviceName(device)
        if fullDeviceName not in ctrlChannels.keys():
            print("adding index", self.index, device)
            dct = {}
            dct[u'conditioning'] = u''
            dct[u'enabled'] = True
            dct[u'full_name'] = fullDeviceName
            dct[u'index'] = self.index
            self.index += 1
            dct[u'label'] = str(device)
            dct[u'name'] = str(device)
            dct[u'ndim'] = 0
            dct[u'normalization'] = 0
            if flagOutput:
                dct[u'output'] = True
            else:
                dct[u'output'] = False
            dct[u'plot_axes'] = [u'<mov>']
            if flagDisplay:
                dct[u'plot_type'] = 1
            else:
                dct[u'plot_type'] = 0
            dct[u'source'] = dct['full_name'] + "/value"
            ctrlChannels[fullDeviceName] = dct

    def addMCA(self, device):
        if not HasyUtils.versionSardanaNewMg():
            self.addMCAD8(device)
        else:
            self.addMCAD9(device)

    #
    # add a MCA to the measurement group
    #
    def addMCAD8(self, device):
        ctrl = self.findDeviceController(device)
        if ctrl not in self.hsh[u'controllers'].keys():
            print("MgUtils.addMCA adding controller ", ctrl)
            self.hsh[u'controllers'][ctrl] = {}
            self.hsh[u'controllers'][ctrl][u'units'] = {}
            self.hsh[u'controllers'][ctrl][u'units'][u'0'] = {}
            self.hsh[u'controllers'][ctrl][u'units'][u'0'][u'channels'] = {}
            self.hsh[u'controllers'][ctrl][u'units'][u'0'][u'id'] = 0
            self.hsh[u'controllers'][ctrl][u'units'][u'0'][u'monitor'] = \
                self.findFullDeviceName(self.masterTimer)
            self.hsh[u'controllers'][ctrl][u'units'][u'0'][u'timer'] = \
                self.findFullDeviceName(self.masterTimer)
            self.hsh[u'controllers'][ctrl][u'units'][u'0'][u'trigger_type'] = 0

        ctrlChannels = self.hsh[u'controllers'][ctrl][u'units'][u'0'][
            u'channels']
        fullDeviceName = self.findFullDeviceName(device)
        if fullDeviceName not in ctrlChannels.keys():
            print("adding index", self.index, device)
            proxy = DeviceProxy(str(fullDeviceName))
            dct = {}
            dct[u'_controller_name'] = str(ctrl)
            dct[u'_unit_id'] = u'0'
            dct[u'conditioning'] = u''
            dct[u'data_type'] = u'float64'
            dct[u'data_units'] = u'No unit'
            dct[u'enabled'] = True
            dct[u'full_name'] = fullDeviceName
            dct[u'index'] = self.index
            self.index += 1
            dct[u'instrument'] = None
            dct[u'label'] = str(device)
            dct[u'name'] = str(device)
            dct[u'ndim'] = 1
            dct[u'nexus_path'] = u''
            dct[u'normalization'] = 0
            dct[u'output'] = True
            dct[u'plot_axes'] = []
            dct[u'plot_type'] = 0
            dct[u'shape'] = [proxy.DataLength]
            dct[u'source'] = fullDeviceName + "/Value"
            ctrlChannels[fullDeviceName] = dct

    #
    # add a MCA to the measurement group
    #
    def addMCAD9(self, device):
        ctrl = self.findDeviceController(device)
        if ctrl not in self.hsh[u'controllers'].keys():
            print("MgUtils.addMCA adding controller ", ctrl)
            self.hsh[u'controllers'][ctrl] = {}
            self.hsh[u'controllers'][ctrl][u'synchronizer'] = "software"
            self.hsh[u'controllers'][ctrl][u'channels'] = {}
            self.hsh[u'controllers'][ctrl][u'id'] = 0
            self.hsh[u'controllers'][ctrl][u'monitor'] = \
                self.findFullDeviceName(device)
            self.hsh[u'controllers'][ctrl][u'timer'] = \
                self.findFullDeviceName(device)
            self.hsh[u'controllers'][ctrl][u'trigger_type'] = 0

        ctrlChannels = self.hsh[u'controllers'][ctrl][u'channels']
        fullDeviceName = self.findFullDeviceName(device)
        if fullDeviceName not in ctrlChannels.keys():
            print("adding index", self.index, device)
            # proxy =
            DeviceProxy(str(fullDeviceName))
            dct = {}
            dct[u'conditioning'] = u''
            dct[u'enabled'] = True
            dct[u'full_name'] = fullDeviceName
            dct[u'index'] = self.index
            self.index += 1
            dct[u'label'] = str(device)
            dct[u'name'] = str(device)
            dct[u'ndim'] = 1
            dct[u'normalization'] = 0
            dct[u'output'] = True
            dct[u'plot_axes'] = [u'<mov>']
            dct[u'plot_type'] = 0
            dct[u'source'] = fullDeviceName + "/Value"
            ctrlChannels[fullDeviceName] = dct

    def addPilatus(self, device):
        if not HasyUtils.versionSardanaNewMg():
            self.addPilatusD8(device)
        else:
            self.addPilatusD9(device)

    #
    # add a MCA to the measurement group
    #
    def addPilatusD8(self, device):
        ctrl = self.findDeviceController(device)
        if ctrl not in self.hsh[u'controllers'].keys():
            print("MgUtils.addPilatus adding controller ", ctrl)
            self.hsh[u'controllers'][ctrl] = {}
            self.hsh[u'controllers'][ctrl][u'units'] = {}
            self.hsh[u'controllers'][ctrl][u'units'][u'0'] = {}
            self.hsh[u'controllers'][ctrl][u'units'][u'0'][u'channels'] = {}
            self.hsh[u'controllers'][ctrl][u'units'][u'0'][u'id'] = 0
            self.hsh[u'controllers'][ctrl][u'units'][u'0'][u'monitor'] = \
                self.findFullDeviceName(self.masterTimer)
            self.hsh[u'controllers'][ctrl][u'units'][u'0'][u'timer'] = \
                self.findFullDeviceName(self.masterTimer)
            self.hsh[u'controllers'][ctrl][u'units'][u'0'][u'trigger_type'] = 0

        ctrlChannels = self.hsh[u'controllers'][ctrl][u'units'][u'0'][
            u'channels']
        fullDeviceName = self.findFullDeviceName(device)
        if fullDeviceName not in ctrlChannels.keys():
            print("adding index", self.index, device)
            # proxy =
            DeviceProxy(str(fullDeviceName))
            dct = {}
            dct[u'_controller_name'] = str(ctrl)
            dct[u'_unit_id'] = u'0'
            dct[u'conditioning'] = u''
            dct[u'enabled'] = True
            dct[u'full_name'] = fullDeviceName
            dct[u'index'] = self.index
            self.index += 1
            dct[u'instrument'] = u''
            dct[u'label'] = str(device)
            dct[u'name'] = str(device)
            dct[u'ndim'] = 2
            dct[u'nexus_path'] = u''
            dct[u'normalization'] = 0
            dct[u'output'] = True
            dct[u'plot_axes'] = []
            dct[u'plot_type'] = 0
            dct[u'source'] = fullDeviceName + "/Value"
            ctrlChannels[fullDeviceName] = dct

    #
    # add a Pilatus to the measurement group
    #
    def addPilatusD9(self, device):
        ctrl = self.findDeviceController(device)
        if ctrl not in self.hsh[u'controllers'].keys():
            print("MgUtils.addPilatus adding controller ", ctrl)
            self.hsh[u'controllers'][ctrl] = {}
            self.hsh[u'controllers'][ctrl][u'synchronizer'] = "software"
            self.hsh[u'controllers'][ctrl][u'channels'] = {}
            self.hsh[u'controllers'][ctrl][u'id'] = 0
            self.hsh[u'controllers'][ctrl][u'monitor'] = \
                self.findFullDeviceName(device)
            self.hsh[u'controllers'][ctrl][u'timer'] = \
                self.findFullDeviceName(device)
            self.hsh[u'controllers'][ctrl][u'trigger_type'] = 0

        ctrlChannels = self.hsh[u'controllers'][ctrl][u'channels']
        fullDeviceName = self.findFullDeviceName(device)
        if fullDeviceName not in ctrlChannels.keys():
            print("adding index", self.index, device)
            # proxy =
            DeviceProxy(str(fullDeviceName))
            dct = {}
            dct[u'conditioning'] = u''
            dct[u'enabled'] = True
            dct[u'full_name'] = fullDeviceName
            dct[u'index'] = self.index
            self.index += 1
            dct[u'label'] = str(device)
            dct[u'name'] = str(device)
            dct[u'ndim'] = 2
            dct[u'normalization'] = 0
            dct[u'output'] = True
            dct[u'plot_axes'] = [u'<mov>']
            dct[u'plot_type'] = 0
            dct[u'source'] = fullDeviceName + "/Value"
            ctrlChannels[fullDeviceName] = dct

    def parseSCA(self, name):
        """
        name: sca_exp_mca01_100_200, returns ['exp_mca01', '100', '200']
        """
        lst = name.split('_')
        return [lst[1] + '_' + lst[2], lst[3], lst[4]]

    def _getMcaName(self, mcaSardanaDeviceAlias):
        """
        input: sardana device name alias
        output: the MCA Tango server name which is used by the Sardana device
        """
        try:
            proxy = DeviceProxy(mcaSardanaDeviceAlias)
        except DevFailed as e:
            Except.re_throw_exception( e, "MgUtils", "failed to create proxy to %s " % mcaSardanaDeviceAlias, "MgUtils._gHeMcaName")
        return proxy.TangoDevice

    def _addSca(self, device):
        """
        Input: device: sca_exp_mca01_100_200
        Returns full controller name, e.g.:
        haso107klx:10000/controller/hasscactrl/sca_exp_mca01_100_200
        Creates a HasySca controller and creates a device for this controller,
        There is only one device per controller
        """
        mca, roiMin, roiMax = self.parseSCA(device)
        #
        # find the tango device name which is used my the sardana device
        #
        tgMca = self._getMcaName(mca)
        #
        # sca_exp_mca01_100_200_ctrl
        #
        ctrlAlias = device + "_ctrl"
        #
        # see whether the controller exists already
        #

        lst = self.poolMg.ControllerList
        ctrlFullName = None
        for elm in lst:
            chan = json.loads(elm)
            if ctrlAlias == chan['name']:
                ctrlFullName = chan['full_name']
                break
        #
        # if the controller does not exist, create it
        #
        proxy = DeviceProxy(tgMca)
        dataLength = proxy.DataLength
        if int(roiMax) >= dataLength:
            raise Exception(
                "MgUtils._addSca %s " % device,
                "roiMax %d  >= datalength %d "
                % (int(roiMax), int(dataLength)))
        if int(roiMin) >= dataLength:
            raise Exception(
                "MgUtils._addSca %s " % device,
                "roiMin %d  >= datalength %d "
                % (int(roiMin), dataLength))

        if ctrlFullName is None:
            lst = ['CTExpChannel', 'HasyScaCtrl.py', 'HasyScaCtrl',
                   ctrlAlias, "mca", tgMca, "roi1", roiMin, "roi2", roiMax]
            print("MgUtils._addSca", lst)
            try:
                self.poolMg.CreateController(lst)
            except DevFailed as e:
                Except.print_exception(e)
                # print "failed to get proxy to ", poolName
                sys.exit(255)

            lst = self.poolMg.ControllerList
            for elm in lst:
                chan = json.loads(elm)
                if ctrlAlias == chan['name']:
                    ctrlFullName = chan['full_name']
                    break
        if ctrlFullName is None:
            raise Exception('MgUtils._addSca',
                            "failed to make controller for %s" % device)

        #
        # see whether the SCA device exists
        #
        lst = self.poolMg.ExpChannelList
        flag = False
        for elm in lst:
            chan = json.loads(elm)
            if device == chan['name']:
                flag = True
                break

        if not flag:
            #
            # "CTExpChannel","HasyScaCtrl","1","sca_exp_mca01_100_200"
            #
            lst = ["CTExpChannel", ctrlAlias, "1", device]
            self.poolMg.CreateElement(lst)

        return ctrlFullName

    def makeScaControllerForPseudoCounter(self, device):
        """
        Input: device: sca_exp_mca01_100_200
        Returns full controller name, e.g.:
        haso107klx:10000/controller/mca2scactrl/sca_exp_mca01_100_200_ctrl
        """
        mca, roiMin, roiMax = self.parseSCA(device)

        ctrlAlias = device + "_ctrl"
        #
        # see whether the controller exists already
        #
        lst = self.poolMg.ControllerList
        for elm in lst:
            chan = json.loads(elm)
            if ctrlAlias == chan['name']:
                return chan['full_name']
        lst = ['PseudoCounter', 'MCA2SCACtrl.py',
               'MCA2SCACtrl', device + "_ctrl",
               'mca=' + self.findFullDeviceName(mca), 'sca=' + device]

        # print "MgUutils.makeSardanaController", lst
        self.poolMg.CreateController(lst)
        #
        # now it has been created.
        # go through the list again an return the full controller name
        #
        lst = self.poolMg.ControllerList
        for elm in lst:
            chan = json.loads(elm)
            if ctrlAlias == chan['name']:
                #
                # set the ROIs
                #
                proxy = DeviceProxy(device)
                proxy.Roi1 = int(roiMin)
                proxy.Roi2 = int(roiMax)
                return chan['full_name']
        raise Exception('MgUtils.makeController',
                        "failed to make controller for %s" % device)

    def addSCA(self, device, flagDisplay, flagOutput):
        if not HasyUtils.versionSardanaNewMg():
            self.addSCAD8(device, flagDisplay, flagOutput)
        else:
            self.addSCAD9(device, flagDisplay, flagOutput)

    def addSCAD8(self, device, flagDisplay, flagOutput):
        """
        add a SCA to the measurement group
          input: device, e.g. sca_exp_mca01_100_200
        """
        if device.find('sca_') != 0:
            print("MgUtils.addSCA: '%s' does not begin with 'sca_'," % device)
            return False

        #
        # there is one element per controller
        #
        fullCtrlName = self._addSca(device)
        if fullCtrlName not in self.hsh[u'controllers'].keys():
            print("MgUtils.addSca adding controller ", fullCtrlName)
            self.hsh[u'controllers'][fullCtrlName] = {}
            self.hsh[u'controllers'][fullCtrlName][u'units'] = {}
            self.hsh[u'controllers'][fullCtrlName][u'units'][u'0'] = {}
            self.hsh[u'controllers'][fullCtrlName][u'units'][u'0'][
                u'channels'] = {}
            self.hsh[u'controllers'][fullCtrlName][u'units'][u'0'][u'id'] = 0
            self.hsh[u'controllers'][fullCtrlName][u'units'][u'0'][
                u'monitor'] = self.findFullDeviceName(self.masterTimer)
            self.hsh[u'controllers'][fullCtrlName][u'units'][u'0'][
                u'timer'] = self.findFullDeviceName(self.masterTimer)
            self.hsh[u'controllers'][fullCtrlName][u'units'][u'0'][
                u'trigger_type'] = 0

        ctrlChannels = self.hsh[u'controllers'][fullCtrlName][u'units'][
            u'0'][u'channels']
        if not self.findFullDeviceName(device) in ctrlChannels.keys():
            print("adding index", self.index, device)
            dct = {}
            dct[u'_controller_name'] = str(fullCtrlName)
            dct[u'_unit_id'] = u'0'
            dct[u'conditioning'] = u''
            dct[u'enabled'] = True
            dct[u'full_name'] = self.findFullDeviceName(device)
            dct[u'index'] = self.index
            self.index += 1
            dct[u'instrument'] = None
            dct[u'label'] = str(device)
            dct[u'name'] = str(device)
            dct[u'ndim'] = 0
            dct[u'normalization'] = 0
            if flagOutput:
                dct[u'output'] = True
            else:
                dct[u'output'] = False
            dct[u'plot_axes'] = [u'<mov>']
            if flagDisplay:
                dct[u'plot_type'] = 1
            else:
                dct[u'plot_type'] = 0
            dct[u'source'] = dct['full_name'] + "/value"
            ctrlChannels[self.findFullDeviceName(device)] = dct
        return True

    def addSCAD9(self, device, flagDisplay, flagOutput):
        """
        add a SCA to the measurement group
          input: device, e.g. sca_exp_mca01_100_200
        """
        if device.find('sca_') != 0:
            print("MgUtils.addSCA: '%s' does not begin with 'sca_'," % device)
            return False

        #
        # there is one element per controller
        #
        fullCtrlName = self._addSca(device)
        if fullCtrlName not in self.hsh[u'controllers'].keys():
            print("MgUtils.addSca adding controller ", fullCtrlName)
            self.hsh[u'controllers'][fullCtrlName] = {}
            ctrl = fullCtrlName
            self.hsh[u'controllers'][ctrl][u'synchronizer'] = "software"
            self.hsh[u'controllers'][ctrl][u'channels'] = {}
            self.hsh[u'controllers'][ctrl][u'id'] = 0
            self.hsh[u'controllers'][ctrl][u'monitor'] = \
                self.findFullDeviceName(device)
            self.hsh[u'controllers'][ctrl][u'timer'] = \
                self.findFullDeviceName(device)
            self.hsh[u'controllers'][ctrl][u'trigger_type'] = 0

        ctrlChannels = self.hsh[u'controllers'][fullCtrlName][u'channels']
        if not self.findFullDeviceName(device) in ctrlChannels.keys():
            print("adding index", self.index, device)
            dct = {}
            dct[u'conditioning'] = u''
            dct[u'enabled'] = True
            dct[u'full_name'] = self.findFullDeviceName(device)
            dct[u'index'] = self.index
            self.index += 1
            dct[u'label'] = str(device)
            dct[u'name'] = str(device)
            dct[u'ndim'] = 0
            dct[u'normalization'] = 0
            if flagOutput:
                dct[u'output'] = True
            else:
                dct[u'output'] = False
            dct[u'plot_axes'] = [u'<mov>']
            if flagDisplay:
                dct[u'plot_type'] = 1
            else:
                dct[u'plot_type'] = 0
            dct[u'source'] = dct['full_name'] + "/value"
            ctrlChannels[self.findFullDeviceName(device)] = dct
        return True


class create_delete_mgOBSOLETE(Macro):
    """Change the active measurement group"""

    param_def = [
        ['list_of_elements', Type.String, None, '0 -> close, 1 -> open']]

    def run(self, list_of_elements):

        self.output("Changing active MG")

        mg_name = self.getEnv('ActiveMntGrp')

        pools = self.getPools()
        for tmp_pool in pools:
            for mg in tmp_pool.MeasurementGroupList:
                hsh = json.loads(mg)
                if mg_name == hsh["name"]:
                    pool = tmp_pool

        pool.DeleteElement(mg_name)

        args = []
        args.append(mg_name)

        elements = list_of_elements.split(',')

        for el in elements:
            args.append(el)

        pool.CreateMeasurementGroup(args)

        self.output("Done")


class delete_mg(Macro):
    """
    Delete a MG
    """

    param_def = [
        ['mgName', Type.String, None, 'MG to be deleted']]

    def run(self, mgName):

        pools = self.getPools()
        pool = None
        for tmp_pool in pools:
            for mg in tmp_pool.MeasurementGroupList:
                hsh = json.loads(mg)
                if mgName == hsh["name"]:
                    pool = tmp_pool

        if pool:
            pool.DeleteElement(mgName)
            self.output("delete_mg: %s deleted" % mgName)
            mg_active = self.getEnv('ActiveMntGrp')
            if mg_active == mgName:
                self.unsetEnv('ActiveMntGrp')
                self.output("delete_mg: usenv ActiveMgtGrp")
            self.output(
                "delete_mg: restart MacroServer before re-creating %s"
                % mgName)
        else:
            self.output("delete_mg: %s does not belong to any pool" % mgName)

        return True


class change_mg(Macro):
    """
    change_mg -a <addflag> -g <mgName> -t <timer> -e <extraTimer>
              -c <counter> -m <mca> -nd <not displayed counters>
              -no <not spock output for counters>
              -ndo <not displayed and not spock output counters>
              -q <pilatus>

    All parameters are optional. However, a timer has to be specified, if a new
    MG is created or if an existing MG is cleared and re-filled ('-a False' or
    '-a' not supplied). If mgName is not supplied, the active MG is changed.
    If addFlag is not given, the MG will be cleared (addFlag False by default)
    and re-filled with the given elements.
    Lists of elements are separated by ',', like:
                  -c exp_ct01,exp_ct02  (no blank space)

    The ActiveMntGrp is set to the created/changed MG.

    Example:
      change_mg -g mg_ivp -t exp_t01 -c exp_c01 -m d1_mca01 -q pilatus

    """
    param_def = [
        ["options_list",
         [['option', Type.String, "None", 'option'],
          ['value', Type.String, "None", 'value']],
         ["None", "None"], "List of options and values"]]

    def run(self, options_list):

        if options_list[0][0] == "None":
            self.output("\
            change_mg -a <addflag> -g <mgName> -t <timer> -e <extraTimer>\
            -c <counter> -m <mca>  -nd <not displayed counters>\
            -no <not spock output for counters> -ndo"
                        " <not displayed and not spock output counters>\
            -q <pilatus>\
            \
            All parameters are options. However, a timer has to be specified, "
                        "if a new MGoptions\
            is created or if an existing MG is cleared and re-filled "
                        "('-a False' or '-a' not supplied.\
            If mgName is not supplied, the active MGe is changed.\
            If addFlag (true or false) is not given, the MG will be cleared "
                        "(addFlag False by default)\
            and re-filled with the given elements.\
            \
            Lists of elements are separated by ',', like: "
                        "-c exp_ct01,exp_ct02  (no blank space)\
            \
            The ActiveMntGrp is set to the created/change MG. \
            \
            Example:\
            change_mg -g mg_ivp -t exp_t01 -c exp_c01,vc_pilatus300k,"
                        "vc_pilatus1m -m d1_mca01\
            \
            ")
            return

        opt_dict = {}
        for opt_par in options_list:
            opt_dict[opt_par[0]] = opt_par[1]

        key = '-g'
        if key in opt_dict:
            mg_name = opt_dict[key]
        else:
            mg_name = self.getEnv('ActiveMntGrp')

        mntgrp_list = self.findObjs(mg_name, type_class=Type.MeasurementGroup)
        #
        # the MG is created, if it does not exist
        #
        if len(mntgrp_list) == 0:

            pools = self.getPools()
            if len(pools) != 1:
                raise Exception(
                    "change_mg: %s does not exist and no. of pools != 1"
                    % mg_name)
            if '-t' not in opt_dict.keys():
                raise Exception(
                    "change_mg: %s cannot be created because no timer is "
                    "specified" % mg_name)
            lst = opt_dict['-t'].split(',')
            pools[0].CreateMeasurementGroup([mg_name, lst[0]])

        pools = self.getPools()

        for tmp_pool in pools:
            for mg in tmp_pool.MeasurementGroupList:
                hsh = json.loads(mg)
                if mg_name == hsh["name"]:
                    pool = tmp_pool

        flagClear = True
        key = '-a'
        if key in opt_dict:
            if opt_dict[key] in ["True", "true"]:
                flagClear = False

        key = '-t'
        if flagClear is True:
            if key not in opt_dict:
                raise Exception("change_mg: need a timer or '-a True'")

        if type(pool.name) == str:   # +++ 28.5.2018: new sardana
            mgConf = MgConf(pool.name, mg_name, flagClear)
        else:
            mgConf = MgConf(pool.name(), mg_name, flagClear)

        if key in opt_dict:
            for elem in opt_dict[key].split(','):
                mgConf.addTimer(elem)

        key = '-e'
        if key in opt_dict:
            for elem in opt_dict[key].split(','):
                mgConf.addExtraTimer(elem)

        key = '-m'
        if key in opt_dict:
            for elem in opt_dict[key].split(','):
                mgConf.addMCA(elem)

        key = '-c'
        if key in opt_dict:
            for elem in opt_dict[key].split(','):
                mgConf.addCounter(elem, 1, 1)

        key = '-nd'
        if key in opt_dict:
            for elem in opt_dict[key].split(','):
                mgConf.addCounter(elem, 0, 1)

        key = '-no'
        if key in opt_dict:
            for elem in opt_dict[key].split(','):
                mgConf.addCounter(elem, 1, 0)

        key = '-ndo'
        if key in opt_dict:
            for elem in opt_dict[key].split(','):
                mgConf.addCounter(elem, 0, 0)

        key = '-q'
        if key in opt_dict:
            for elem in opt_dict[key].split(','):
                mgConf.addPilatus(elem)
                mgConf.addCounter(elem, 0, 1)

        mgConf.updateConfiguration()
        self.setEnv('ActiveMntGrp', mg_name)
        self.output("change_mg: ActiveMntGrp = %s" % mg_name)


class setmg(Macro):
    """
        setmg - select active measurement group
    """

    param_def = [
        ["measgroup", Type.Integer, -999, "Measurement group"],
    ]

    interactive = True

    def run(self, measgroup):

        actmg = self.getEnv('ActiveMntGrp')
        a1 = HasyUtils.getLocalMgNames()
        la = len(a1)
        if measgroup != -999:
            i = 0
            while i < la:
                mg = a1[i].split('/')[2]
                if measgroup == i:
                    self.setEnv('ActiveMntGrp', mg)
                    actmg = mg
                i += 1
            self.output("Active measurement group: %s" % (actmg))

        else:
            i = 0
            while i < la:
                mg = a1[i].split('/')[2]
                self.output("[%i] %s" % (i, mg))
                if actmg == mg:
                    nact = i
                i += 1
            self.output("")
            a2 = self.input("Your choice? ", default_value=nact)
            i = 0
            while i < la:
                mg = a1[i].split('/')[2]
                if int(a2) == i:
                    self.setEnv('ActiveMntGrp', mg)
                    actmg = mg
                i += 1
            self.output("")
            self.output("Active measurement group: %s" % (actmg))


# class check_mg(Macro):
#    """
#    check_mg - check status MG channels
#
#    """
#
#    def run(self):
#        active_mg = self.getEnv('ActiveMntGrp')
#        self.mntGrp = self.getObj(active_mg, type_class=Type.MeasurementGroup)
#
#        self.output("")
#        self.output(
#             "Active measurement group (" + active_mg + ") in "
#                   + str(self.mntGrp.getState()) +
#                    " state")
#        self.output("")
#        cols = "Channel", "State"
#        width = -1,     -1
#        align = HCenter,  Right
#        out = List(cols, text_alignment=align,
#                   max_col_width=width)
#        for channel in self.mntGrp.getChannels():
#            ch =  self.getObj(channel['name'])
#            out.appendRow([channel['name'], ch.getState()])
#
#        for line in out.genOutput():
#            self.output(line)
#

class check_mg(Macro):
    """
    Displays '<activeMntGrp> is OK', if everything is OK,  or
    the status strings of the ActiveMntGrp and their elements.
    """
    param_def = []

    def run(self):
        lst = HasyUtils.getActiveMntGrpStatus()
        mg_name = self.getEnv('ActiveMntGrp')
        if lst is None or len(lst) == 0:
            self.output("check_mg: %s is OK" % mg_name)
            return

        self.output("check_mg: %s" % mg_name)
        for elm in lst:
            self.output("check_mg: %s" % elm)
        return
