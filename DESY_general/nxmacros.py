#!/bin/env python
""" NeXus recorder macros """

import PyTango
import time
import json
import fnmatch
import pprint
from sardana.macroserver.macro import (
    Macro, Type, macro, ParamRepeat)


def device_groups():
    """ Return device groups """

    return {
        "counter": ["*exp_c*"],
        "timer": ["*exp_t*"],
        "mca": ["*exp_mca*"],
        "dac": ["*exp_dac*"],
        "adc": ["*exp_adc*"],
        "motor": ["*exp_mot*"],
        }


class nxprof(Macro):
    """ List the current profile """

    def run(self):
        server = set_selector(self)

        printString(self, "MntGrp", "Profile (and MntGrp)")
        self.output("")
        printConfList(self, "Timer", True, "Timer(s)")
        self.output("")
        printList(self, "Components", False, "Detector Components")
        self.output("")
        printList(self, "DataSources", False, "Other Detector Channels")
        self.output("")
        printList(self, "MandatoryComponents", False, "Mandatory Components",
                  True)
        self.output("")
        printList(self, "AutomaticComponents", False, "Description Components")
        self.output("")
        printConfList(self, "InitDataSources", True,
                      "Other Description Channels")
        self.output("")
        printDict(self, "DataRecord", True, "User Data")
        self.output("")
        printDict(self, "ConfigVariables", True, "ConfigServer Variables")
        self.output("")
        printString(self, "AppendEntry")
        self.output("")
        self.output("SelectorServer: %s" % str(server))
        printString(self, "ConfigDevice", "ConfigServer")
        printString(self, "WriterDevice", "WriterServer")


@macro()
def nxlscp(self):
    """ List all available components """

    set_selector(self)
    printList(self, "AvailableComponents", False, None, True)


@macro()
def nxlsds(self):
    """ List all available datasources """

    set_selector(self)
    printList(self, "AvailableDataSources", False, None, True)


@macro()
def nxlsprof(self):
    """ List all avaliable profiles """

    set_selector(self)
    printList(self, "AvailableSelections", False, None, True)


@macro()
def nxlstimers(self):
    """ List all available timers """

    set_selector(self)
    printList(self, "AvailableTimers", False)


@macro()
def nxlsdevtype(self):
    """ List all available device types """

    self.output("Types: %s" % str(device_groups().keys()))


class nxlsprofvar(Macro):
    """ List profile variable names or its values (with param)"""

    param_def = [
        ['name', Type.String, '', 'profile variable name'],
        ]

    def run(self, name):
        set_selector(self)
        conf = json.loads(self.selector.Configuration)
        if not name or name not in conf.keys():
            self.output(conf.keys())
        else:
            self.output(conf[name])


class nxsetprof(Macro):
    """ Set the active profile """

    param_def = [
        ['name', Type.String, '', 'profile name'],
        ]

    def run(self, name):
        set_selector(self)
        self.selector.mntgrp = name
        self.selector.fetchConfiguration()
        self.selector.importMntGrp()
        self.selector.storeConfiguration()
        self.selector.updateMntGrp()
        self.selector.importMntGrp()


class nxrmprof(Macro):
    """ Remove the current profile """

    param_def = [
        ['name', Type.String, '', 'profile name'],
        ]

    def run(self, name):
        set_selector(self)
        self.selector.deleteMntGrp(name)


class nxsettimers(Macro):
    """ Set the current profile timers """

    param_def = [
        ['timer_list',
         ParamRepeat(['timer', Type.String, None, 'timer to select']),
         None, 'List of profile timers to set'],
    ]

    def run(self, *timer_list):
        set_selector(self)
        cnf = json.loads(self.selector.Configuration)

        cnf["Timer"] = str(json.dumps(timer_list))
        self.selector.configuration = str(json.dumps(cnf))
        self.selector.updateMntGrp()
        self.selector.importMntGrp()


class nxadd(Macro):
    """ Add the given profile elements """

    param_def = [
        ['element_list',
         ParamRepeat(['element', Type.String, None, 'Profile element to add']),
         None, 'List of profile elements to add'],
    ]

    def run(self, *element_list):
        set_selector(self)
        cnf = json.loads(self.selector.Configuration)
        cpdct = json.loads(cnf["ComponentGroup"])
        dsdct = json.loads(cnf["DataSourceGroup"])
        pch = self.selector.PoolChannels()
        for name in element_list:
            if name not in pch and name in self.selector.availableComponents():
                cpdct[str(name)] = True
            else:
                dsdct[str(name)] = True
        cnf["DataSourceGroup"] = str(json.dumps(dsdct))
        cnf["ComponentGroup"] = str(json.dumps(cpdct))
        self.selector.Configuration = str(json.dumps(cnf))
        self.selector.updateMntGrp()
        self.selector.importMntGrp()


class nxrm(Macro):
    """ Deselect the given profile elements """

    param_def = [
        ['element_list',
         ParamRepeat(['element', Type.String, None, 'Profile element to remove']),
         None, 'List of elements to show'],
    ]

    def run(self, *element_list):
        set_selector(self)
        cnf = json.loads(self.selector.Configuration)
        cpdct = json.loads(cnf["ComponentGroup"])
        dsdct = json.loads(cnf["DataSourceGroup"])
        for name in element_list:
            if name in cpdct:
                cpdct[str(name)] = False
            if name in dsdct:
                dsdct[str(name)] = False
        cnf["DataSourceGroup"] = str(json.dumps(dsdct))
        cnf["ComponentGroup"] = str(json.dumps(cpdct))
        self.selector.configuration = str(json.dumps(cnf))
        self.selector.updateMntGrp()
        self.selector.importMntGrp()


class nxclr(Macro):
    """ Removes all profile elements """

    def run(self):
        set_selector(self)
        cnf = json.loads(self.selector.Configuration)
        cpdct = json.loads(cnf["ComponentGroup"])
        dsdct = json.loads(cnf["DataSourceGroup"])
        for name in cpdct.keys():
            cpdct[str(name)] = False
        for name in dsdct.keys():
            dsdct[str(name)] = False
        cnf["DataSourceGroup"] = str(json.dumps(dsdct))
        cnf["ComponentGroup"] = str(json.dumps(cpdct))
        self.selector.configuration = str(json.dumps(cnf))
        self.selector.updateMntGrp()
        self.selector.importMntGrp()


class nxadddesc(Macro):
    """ Add the given description components """

    param_def = [
        ['element_list',
         ParamRepeat(['element', Type.String, None,
                      'description component to add']),
         None, 'List of description components to add'],
    ]

    def run(self, *element_list):
        set_selector(self)
        cnf = json.loads(self.selector.Configuration)
        cpdct = json.loads(cnf["AutomaticComponentGroup"])
        for name in element_list:
            if name in self.selector.availableComponents():
                cpdct[str(name)] = True
                self.output("%s added" % name)
        cnf["AutomaticComponentGroup"] = str(json.dumps(cpdct))
        self.selector.configuration = str(json.dumps(cnf))
        update_description(self)
        self.selector.updateMntGrp()
        self.selector.importMntGrp()


class nxrmdesc(Macro):
    """ Remove the given description components"""

    param_def = [
        ['element_list',
         ParamRepeat(['element', Type.String, None,
                      'description component to remove']),
         None, 'List of descpription components to remove'],
    ]

    def run(self, *element_list):
        set_selector(self)
        cnf = json.loads(self.selector.Configuration)
        cpdct = json.loads(cnf["AutomaticComponentGroup"])
        for name in element_list:
            if name in cpdct:
                cpdct[str(name)] = False
        cnf["AutomaticComponentGroup"] = str(json.dumps(cpdct))
        self.selector.configuration = str(json.dumps(cnf))
        update_description(self)
        self.selector.updateMntGrp()
        self.selector.importMntGrp()


class nxsetappentry(Macro):
    """ Set the append entry flag for the current profile"""

    param_def = [
        ['append_flag', Type.Boolean, '', 'append entry flag'],
        ]

    def run(self, append_flag):
        set_selector(self)
        self.selector.appendEntry = append_flag
        self.selector.updateMntGrp()
        self.selector.importMntGrp()
        self.output("AppendEntry set to: %s" % self.selector.appendEntry)


class nxsetudata(Macro):
    """Set the given user data"""

    param_def = [['name', Type.String, None, 'user data name'],
                 ['value', Type.String, None, 'user data value']]

    def run(self, name, value):
        set_selector(self)
        cnf = json.loads(self.selector.Configuration)
        udata = json.loads(cnf["DataRecord"])
        udata[str(name)] = value

        cnf["DataRecord"] = str(json.dumps(udata))
        self.selector.configuration = str(json.dumps(cnf))
        self.selector.updateMntGrp()
        self.selector.importMntGrp()


class nxusetudata(Macro):
    """Unset the given user data"""

    param_def = [
        ['name_list',
         ParamRepeat(['name', Type.String, None, 'user data name to delete']),
         None, 'List of user data names to delete'],
    ]

    def run(self, *name_list):
        set_selector(self)
        cnf = json.loads(self.selector.Configuration)
        udata = json.loads(cnf["DataRecord"])
        changed = False
        for name in name_list:
            if name in udata.keys():
                udata.pop(str(name))
                self.output("%s removed" % name)
                changed = True

        if changed:
            cnf["DataRecord"] = str(json.dumps(udata))
            self.selector.configuration = str(json.dumps(cnf))
            self.selector.updateMntGrp()


class nxsetcnfvar(Macro):
    """Set the given configserver variable"""

    param_def = [['name', Type.String, None, 'configserver variable name'],
                 ['value', Type.String, None, 'configserver variable value']]

    def run(self, name, value):
        set_selector(self)
        cnf = json.loads(self.selector.Configuration)
        udata = json.loads(cnf["ConfigVariables"])
        udata[str(name)] = value

        cnf["ConfigVariables"] = str(json.dumps(udata))
        self.selector.configuration = str(json.dumps(cnf))
        self.selector.updateMntGrp()
        self.selector.importMntGrp()


class nxusetcnfvar(Macro):
    """Unset the given configserver variables"""

    param_def = [
        ['name_list',
         ParamRepeat(['name', Type.String, None,
                      'ConfigServer variable name to delete']),
         None, 'List of configserver variables to delete'],
    ]

    def run(self, *name_list):
        set_selector(self)
        cnf = json.loads(self.selector.Configuration)
        udata = json.loads(cnf["ConfigVariables"])
        changed = False
        for name in name_list:
            if name in udata.keys():
                udata.pop(str(name))
                self.output("%s removed" % name)
                changed = True

        if changed:
            cnf["ConfigVariables"] = str(json.dumps(udata))
            self.selector.configuration = str(json.dumps(cnf))
            self.selector.updateMntGrp()
            self.selector.importMntGrp()


class nxupdatedesc(Macro):
    """ Update selection of description components """

    def run(self):
        set_selector(self)
        update_description(self)
        self.selector.updateMntGrp()
        self.selector.importMntGrp()


class nxsetcnfsrv(Macro):
    """ Set the current configuration server """

    param_def = [
        ['name', Type.String, '', 'configserver name'],
        ]

    def run(self, name):
        set_selector(self)
        self.selector.configDevice = str(name)
        self.selector.fetchConfiguration()
        self.selector.importMntGrp()
        self.selector.storeConfiguration()
        self.selector.updateMntGrp()
        self.selector.importMntGrp()


class nxsetwrtsrv(Macro):
    """ Set the current writer server """

    param_def = [
        ['name', Type.String, '', 'writerserver name'],
        ]

    def run(self, name):
        set_selector(self)
        self.selector.writerDevice = str(name)
        self.selector.updateMntGrp()
        self.selector.importMntGrp()


class nxsave(Macro):
    """ Save the current profile to the given file """

    param_def = [
        ['fname', Type.String, '', 'file name'],
        ]

    def run(self, fname):
        set_selector(self)
        if fname:
            self.selector.ConfigFile = str(fname)
        self.selector.saveConfiguration()
        self.output("Profile was saved in %s"
                    % self.selector.ConfigFile)


class nxload(Macro):
    """ Load a profile from the given file """

    param_def = [
        ['fname', Type.String, '', 'file name'],
        ]

    def run(self, fname):
        set_selector(self)
        if fname:
            self.selector.ConfigFile = str(fname)
        self.selector.loadConfiguration()
        self.output("Profile was loaded from %s"
                    % self.selector.ConfigFile)


class nxsetprofvar(Macro):
    """Set profile variable"""

    param_def = [['name', Type.String, None, 'selector variable name'],
                 ['value', Type.String, None, 'selector variable value']]

    def run(self, name, value):
        set_selector(self)
        cnf = json.loads(self.selector.Configuration)
        if name not in cnf.keys():
            self.output("%s not in %s" % (name, cnf.keys()))
            return
        cnf[str(name)] = value
        self.selector.configuration = str(json.dumps(cnf))
        self.selector.updateMntGrp()
        self.selector.importMntGrp()


class nxlse(Macro):
    """ Show available profile elements to select"""

    param_def = [
        ['dev_type', Type.String, '', 'device type or name pattern'],
        ]

    def run(self, dev_type):
        set_selector(self)

        allch = set(self.selector.availableDataSources())
        allch.update(set(self.selector.PoolChannels()))
        allch.update(set(self.selector.availableComponents()))
        available = set()
        groups = device_groups()
        if dev_type:
            if dev_type not in groups.keys() and \
                    dev_type[-1] == 's' and dev_type[:-1] in groups.keys():
                dev_type = dev_type[:-1]
            if dev_type in groups.keys():
                for gr in groups[dev_type]:
                    filtered = fnmatch.filter(
                        allch, gr)
                    available.update(filtered)
            else:
                filtered = fnmatch.filter(
                    allch, "*%s*" % dev_type)
                available.update(filtered)
        else:
            available.update(allch)
        self.output(list(available))


class nxshow(Macro):
    """ Describe the given profile element """

    param_def = [
        ['name', Type.String, '', 'element name'],
        ]

    def run(self, name):
        set_selector(self)

        cpdesc = json.loads(self.selector.Description)
        avcp = self.selector.availableComponents()
        avds = self.selector.availableDataSources()
        fullpool = json.loads(self.selector.fullDeviceNames)
        dslist = []
        if name in avcp:
            found = False
            for grp in cpdesc:
                for cp in grp.keys():
                    if cp == name:
                        dss = grp[cp]
                        for ds in dss.keys():
                            for vds in dss[ds]:
                                elem = {}
                                elem["dsname"] = ds
                                elem["strategy"] = vds[0]
                                elem["dstype"] = vds[1]
                                elem["source"] = vds[2]
                                elem["nxtype"] = vds[3]
                                elem["shape"] = vds[4]
                                elem["cpname"] = cp
                                dslist.append(json.dumps(elem))
                        found = True
                        break
                    if found:
                        break

        if name in fullpool.keys():
            if name in fullpool.keys():
                dslist.append(str(json.dumps(
                            {"dsname": name,
                             "dstype": "POOL",
                             "source": fullpool[name]})))
        if name in avds:
            desc = self.selector.getSourceDescription([str(name)])
            if desc:
                md = json.loads(desc[0])
                if "record" in md:
                    md["source"] = md["record"]
                    md.pop("record")
                dslist.append(str(json.dumps(md)))

        self.output(pprint.pformat(dslist))


def wait_for_device(proxy, counter=100):
    """ Wait for the given Tango device """
    found = False
    cnt = 0
    while not found and cnt < counter:
        if cnt > 1:
            time.sleep(0.01)
        try:
            if proxy.state() != PyTango.DevState.RUNNING:
                found = True
        except (PyTango.DevFailed, PyTango.Except, PyTango.DevError):
            time.sleep(0.01)
            found = False
            if cnt == counter - 1:
                raise
        cnt += 1


def printDict(mcr, name, decode=True, label=None):
    """ Print the given server dictionary """

    if not hasattr(mcr, "selector"):
        set_selector(mcr)
    mcr.output("%s:" % (name if label is None else label))
    try:
        data = mcr.selector.read_attribute(name).value
        if decode:
            data = json.loads(data)
    except Exception:
        pass
    mcr.output("  %s" % str(data))


def printConfDict(mcr, name, decode=True, label=None):
    """ Print the given server dictionary from Configuration"""

    if not hasattr(mcr, "selector"):
        set_selector(mcr)
    conf = json.loads(mcr.selector.Configuration)

    mcr.output("%s:" % (name if label is None else label))
    try:
        data = conf[name]
        if decode:
            data = json.loads(data)
    except Exception:
        pass
    mcr.output("  %s" % str(data))


def printConfList(mcr, name, decode=True, label=None):
    """ Print the given server list from Configuration """

    if not hasattr(mcr, "selector"):
        set_selector(mcr)
    conf = json.loads(mcr.selector.Configuration)

    mcr.output("%s:" % (name if label is None else label))
    try:
        data = conf[name]
        if decode:
            data = json.loads(data)
    except Exception as e:
        mcr.output(str(e))
    if isinstance(data, tuple):
        data = list(data)
    mcr.output("  %s" % str(data))


def printList(mcr, name, decode=True, label=None, command=False):
    """ Print the given server list """

    if not hasattr(mcr, "selector"):
        set_selector(mcr)
    mcr.output("%s:" % (name if label is None else label))
    try:
        if not command:
            data = mcr.selector.read_attribute(name).value
        else:
            data = mcr.selector.command_inout(name)
        if decode:
            data = json.loads(data)
    except Exception as e:
        mcr.output(str(e))
    if isinstance(data, tuple):
        data = list(data)
    mcr.output("  %s" % str(data))


def printConfString(mcr, name, label=None):
    """ Print the given server variable from Configuration """

    if not hasattr(mcr, "selector"):
        set_selector(mcr)
    conf = json.loads(mcr.selector.Configuration)
    data = conf[name]
    mcr.output("%s: %s" % (name if label is None else label, data))


def printString(mcr, name, label=None, command=False):
    """ Print the given server attribute """
    if not hasattr(mcr, "selector"):
        set_selector(mcr)
    if not command:
        data = mcr.selector.read_attribute(name).value
    else:
        data = mcr.selector.command_inout(name)
    mcr.output("%s:  %s" % (name if label is None else label, data))


def set_selector(mcr):
    """ Set the current selector server """
    db = PyTango.Database()
    try:
        servers = [mcr.getEnv("NeXusSelectorDevice")]
    except Exception:
        servers = db.get_device_exported_for_class(
            "NXSRecSelector").value_string
    if len(servers) > 0:
        mcr.selector = PyTango.DeviceProxy(str(servers[0]))
        return str(servers[0])


def update_description(mcr):
    """ Update selection of description components """
    try:
        mcr.selector.updateControllers()
    except PyTango.CommunicationFailed as e:
        if e[-1].reason == "API_DeviceTimedOut":
            wait_for_device(mcr.selector)
        else:
            raise
