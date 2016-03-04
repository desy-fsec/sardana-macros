#!/bin/env python
""" NeXus recorder macros """

import PyTango
import time
import json
import fnmatch
import pprint
import StringIO
import os
import subprocess
from sardana.macroserver.macro import (
    Macro, Type, macro, ParamRepeat)

from taurus.console.list import List
from taurus.console import Alignment

Left, Right, HCenter = Alignment.Left, Alignment.Right, Alignment.HCenter


def device_groups(self):
    """ Return device groups """
    if hasattr(self.selector, "deviceGroups"):
        return json.loads(self.selector.deviceGroups)
    else:
        return {
            "counter": ["*exp_c*"],
            "timer": ["*exp_t*"],
            "mca": ["*exp_mca*"],
            "dac": ["*exp_dac*"],
            "adc": ["*exp_adc*"],
            "motor": ["*exp_mot*"],
            }


@macro([["mode", Type.String, '',
         "interface mode, i.e. simple, user, advanced, expert"],
        ["selector", Type.String, '', "Selector server"],
        ["door", Type.String, '', "Door"]])
def nxselector(self, mode, selector, door):
    """ Run NeXus Component Selector """
    args = ["nxselector"]
    if mode:
        args.append("-m%s" % mode)
    if selector:
        args.append("-s%s" % selector)
    if door:
        args.append("-d%s" % door)
    my_env = os.environ.copy()
    if not 'DISPLAY' in my_env.keys():
        my_env['DISPLAY'] = ':0.0'
    if not 'USER' in my_env.keys():
        if 'TANGO_USER' in my_env.keys():
            my_env['USER'] = my_env['TANGO_USER']
        else:
            import getpass
            my_env['USER'] = getpass.getuser()
    subprocess.Popen(args, env=my_env)


@macro([["selector", Type.String, '', "Selector server"],
        ["door", Type.String, '', "Door"]])
def nxsmacrogui(self, selector, door):
    """ Run NeXus MacroGUI """
    args = ["nxsmacrogui"]
    if selector:
        args.append("-s%s" % selector)
    if door:
        args.append("-d%s" % door)
    my_env = os.environ.copy()
    if not 'DISPLAY' in my_env.keys():
        my_env['DISPLAY'] = ':0.0'
    if not 'USER' in my_env.keys():
        if 'TANGO_USER' in my_env.keys():
            my_env['USER'] = my_env['TANGO_USER']
        else:
            import getpass
            my_env['USER'] = getpass.getuser()
    subprocess.Popen(args, env=my_env)


class nxsprof(Macro):
    """ List the current profile """

    def run(self):
        server = set_selector(self)
        printProfile(self, server)


@macro()
def lsprof(self):
    """ List the current profile """

    server = set_selector(self)
    mout = printProfile(self, server, True)
    for line in mout.genOutput():
        self.output(line)


@macro()
def nxslscp(self):
    """ List configuration server components.
        The result includes only components
        stored in the configuration server
        """

    set_selector(self)
    printList(self, "AvailableComponents", False, None, True)


@macro()
def nxslsds(self):
    """ List configuration server datasources.
        The result includes only datasources
        stored in the configuration server
"""

    set_selector(self)
    printList(self, "AvailableDataSources", False, None, True)


@macro()
def nxslsprof(self):
    """ List all avaliable profiles.
        A profile can be selectected by 'nxsetprof' macro.
    """

    set_selector(self)
    printList(self, "AvailableProfiles", False,
              "Available profiles", True)


@macro()
def nxslstimers(self):
    """ List all available timers.
        Timers can be set by 'nxsettimers' macro
    """

    set_selector(self)
    printList(self, "AvailableTimers", False,
              "Available timers", True)


@macro()
def nxslsdevtype(self):
    """ List all available device types.
        These device types are used by 'nxsls' macro.
        They are defined by DeviceGroups attribute of NXSRecSelector.
    """
    set_selector(self)
    self.output("Device Types:  %s" % ", ".join(device_groups(self).keys()))


class nxsetprof(Macro):
    """ Set the active profile.
        This action changes also ActiveMntGrp.
    """

    param_def = [
        ['name', Type.String, '', 'profile name'],
        ]

    def run(self, name):
        set_selector(self)
        self.selector.mntgrp = name
        self.selector.fetchProfile()
        self.selector.importMntGrp()
        self.selector.storeProfile()
        update_configuration(self)


class nxsrmprof(Macro):
    """ Remove the current profile
        The current profile can be shown by
        'nxsprof' or 'lsprof' macros
 """

    param_def = [
        ['name', Type.String, '', 'profile name'],
        ]

    def run(self, name):
        set_selector(self)
        self.selector.deleteProfile(name)


class nxsettimers(Macro):
    """ Set the current profile timers.
        Available timer names can be listed by 'nxslstimers' macro
    """

    param_def = [
        ['timer_list',
         ParamRepeat(['timer', Type.String, None, 'timer to select']),
         None, 'List of profile timers to set'],
    ]

    def run(self, *timer_list):
        set_selector(self)
        cnf = json.loads(self.selector.profileConfiguration)

        cnf["Timer"] = str(json.dumps(timer_list))
        self.selector.profileConfiguration = str(json.dumps(cnf))
        update_configuration(self)


class nxsadd(Macro):
    """ Add the given detector components
        Available components can be listed by
        'nxsls', 'nxslscp' or 'nxslsds' macros
    """

    param_def = [
        ['component_list',
         ParamRepeat(['component', Type.String, None,
                      'detector component to add']),
         None, 'List of detector components to add'],
    ]

    def run(self, *component_list):
        set_selector(self)
        cnf = json.loads(self.selector.profileConfiguration)
        cpdct = json.loads(cnf["ComponentSelection"])
        dsdct = json.loads(cnf["DataSourceSelection"])
        pch = self.selector.poolChannels()
        for name in component_list:
            if name not in pch and name in self.selector.availableComponents():
                cpdct[str(name)] = True
            else:
                dsdct[str(name)] = True
        cnf["DataSourceSelection"] = str(json.dumps(dsdct))
        cnf["ComponentSelection"] = str(json.dumps(cpdct))
        self.selector.profileConfiguration = str(json.dumps(cnf))
        update_configuration(self)


class nxsrm(Macro):
    """ Deselect the given detector components.
        Selected detector components
        and other detector channels can be listed by
        'nxsprof' or 'lsprof' macros
    """

    param_def = [
        ['component_list',
         ParamRepeat(['component', Type.String, None,
                      'detector component to remove']),
         None, 'List of components to show'],
    ]

    def run(self, *component_list):
        set_selector(self)
        cnf = json.loads(self.selector.profileConfiguration)
        cpdct = json.loads(cnf["ComponentSelection"])
        dsdct = json.loads(cnf["DataSourceSeleciton"])
        for name in component_list:
            if name in cpdct:
                cpdct[str(name)] = False
            if name in dsdct:
                dsdct[str(name)] = False
        cnf["DataSourceSeleciton"] = str(json.dumps(dsdct))
        cnf["ComponentSelection"] = str(json.dumps(cpdct))
        self.selector.profileConfiguration = str(json.dumps(cnf))
        update_configuration(self)


class nxsclr(Macro):
    """ Removes all detector components from the current profile"""

    def run(self):
        set_selector(self)
        cnf = json.loads(self.selector.profileConfiguration)
        cpdct = json.loads(cnf["ComponentSelection"])
        dsdct = json.loads(cnf["DataSourceSeleciton"])
        for name in cpdct.keys():
            cpdct[str(name)] = False
        for name in dsdct.keys():
            dsdct[str(name)] = False
        cnf["DataSourceSeleciton"] = str(json.dumps(dsdct))
        cnf["ComponentSelection"] = str(json.dumps(cpdct))
        self.selector.profileConfiguration = str(json.dumps(cnf))
        update_configuration(self)


class nxsadddesc(Macro):
    """ Add the given description components.
        Available components can be listed by 'nxslscp' macro.
        Available other datasources can be listed by 'nxslsds' macro
    """

    param_def = [
        ['component_list',
         ParamRepeat(['component', Type.String, None,
                      'description component to add']),
         None, 'List of description components to add'],
    ]

    def run(self, *component_list):
        set_selector(self)
        cnf = json.loads(self.selector.profileConfiguration)
        cpdct = json.loads(cnf["ComponentPreselection"])
        dsdct = set(json.loads(cnf["InitDataSources"]))
        for name in component_list:
            if name in self.selector.availableComponents():
                cpdct[str(name)] = True
                self.output("%s added" % name)
            elif name in self.selector.availableDataSources():
                dsdct.add(str(name))
        cnf["ComponentPreselection"] = str(json.dumps(cpdct))
        cnf["InitDataSources"] = str(json.dumps(list(dsdct)))
        self.selector.profileConfiguration = str(json.dumps(cnf))
        update_description(self)
        update_configuration(self)


class nxsrmdesc(Macro):
    """ Remove the given description components.
        Selected description components can be listed by
        'nxsprof' or 'lsprof' macros
        """

    param_def = [
        ['component_list',
         ParamRepeat(['component', Type.String, None,
                      'description component to remove']),
         None, 'List of descpription components to remove'],
    ]

    def run(self, *component_list):
        set_selector(self)
        cnf = json.loads(self.selector.profileConfiguration)
        cpdct = json.loads(cnf["ComponentPreselection"])
        dsdct = set(json.loads(cnf["InitDataSources"]))
        for name in component_list:
            if name in cpdct:
                cpdct.pop(str(name))
                self.output("Removing %s" % name)
            if name in dsdct:
                dsdct.remove(str(name))
                self.output("Removing %s" % name)
        cnf["ComponentPreselection"] = str(json.dumps(cpdct))
        cnf["InitDataSources"] = str(json.dumps(list(dsdct)))
        self.selector.profileConfiguration = str(json.dumps(cnf))
        update_description(self)
        update_configuration(self)


class nxsetappentry(Macro):
    """ Set the append entry flag for the current profile.
        If the flag is True all consecutive scans are stored in one file
    """

    param_def = [
        ['append_flag', Type.Boolean, '', 'append entry flag'],
        ]

    def run(self, append_flag):
        set_selector(self)
        self.selector.appendEntry = append_flag
        update_configuration(self)
        self.output("AppendEntry set to: %s" % self.selector.appendEntry)


class nxsetudata(Macro):
    """Set the given user data.
       Typical user data are:
       title, sample_name, beamtime_id, chemical_formula, ...
"""

    param_def = [['name', Type.String, None, 'user data name'],
                 ['value', Type.String, None, 'user data value']]

    def run(self, name, value):
        set_selector(self)
        cnf = json.loads(self.selector.profileConfiguration)
        udata = json.loads(cnf["UserData"])
        udata[str(name)] = value

        cnf["UserData"] = str(json.dumps(udata))
        self.selector.profileConfiguration = str(json.dumps(cnf))
        update_configuration(self)


class nxsusetudata(Macro):
    """Unset the given user data.
       The currently set user data can be shown by
       'nxsprof' or 'lsprof' macros
       Typical user data are:
       title, sample_name, beamtime_id, chemical_formula, ...
"""

    param_def = [
        ['name_list',
         ParamRepeat(['name', Type.String, None, 'user data name to delete']),
         None, 'List of user data names to delete'],
    ]

    def run(self, *name_list):
        set_selector(self)
        cnf = json.loads(self.selector.profileConfiguration)
        udata = json.loads(cnf["UserData"])
        changed = False
        for name in name_list:
            if name in udata.keys():
                udata.pop(str(name))
                self.output("%s removed" % name)
                changed = True

        if changed:
            cnf["UserData"] = str(json.dumps(udata))
            self.selector.profileConfiguration = str(json.dumps(cnf))
            update_configuration(self)


class nxsupdatedesc(Macro):
    """ Update a selection of description components.
        The selection is made with respected to working status
        of component tango (motor) devices.
        Selected description components can be listed by
        'nxsprof' or 'lsprof' macros.
        Description component group can be changed by
        'nxsadddesc' and 'nxsrmdesc' macros.
    """

    def run(self):
        set_selector(self)
        update_description(self)
        update_configuration(self)


class nxsave(Macro):
    """ Save the current profile to the given file.
        The file name may contain a file path
    """

    param_def = [
        ['fname', Type.String, '', 'file name'],
        ]

    def run(self, fname):
        set_selector(self)
        if fname:
            self.selector.profileFile = str(fname)
        self.selector.saveProfile()
        self.output("Profile was saved in %s"
                    % self.selector.profileFile)


class nxsload(Macro):
    """ Load a profile from the given file.
        The file name may contain a file path
 """

    param_def = [
        ['fname', Type.String, '', 'file name'],
        ]

    def run(self, fname):
        set_selector(self)
        if fname:
            self.selector.profileFile = str(fname)
        self.selector.loadProfile()
        update_configuration(self)
        self.output("Profile was loaded from %s"
                    % self.selector.profileFile)


class nxsls(Macro):
    """ Show all available components to select
        The result includes components and datasources stored
        in the configuration server as well as pool devices.
        The parameter is device type from 'nxslsdevtype' macro
        or an arbitrary name pattern
    """

    param_def = [
        ['dev_type', Type.String, '', 'device type or name pattern'],
        ]

    def run(self, dev_type):
        set_selector(self)

        allch = set(self.selector.availableDataSources())
        allch.update(set(self.selector.poolChannels()))
        allch.update(set(self.selector.availableComponents()))
        available = set()
        groups = device_groups(self)
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
        self.output(", ".join(list(available)))


class nxshow(Macro):
    """ Describe the given detector component.
        Available components can be listed by
        'nxsls', 'nxslscp' or 'nxslsds' macros
    """

    param_def = [
        ['name', Type.String, '', 'component name'],
        ]

    def run(self, name):
        set_selector(self)
        cpdesc = json.loads(getString(
            self, "ComponentDescription", True))
        avcp = self.selector.availableComponents()
        avds = self.selector.availableDataSources()
        fullpool = json.loads(getString(
            self, "FullDeviceNames", True))
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
                                elem["source_name"] = ds
                                elem["strategy"] = vds[0]
                                elem["source_type"] = vds[1]
                                elem["source"] = vds[2]
                                elem["nexus_type"] = vds[3]
                                elem["shape"] = vds[4]
#                                elem["cpname"] = cp
                                dslist.append(elem)
                        found = True
                        break
                    if found:
                        break
        if dslist:
            self.output("\n    Component: %s\n" % name)
            printTable(self, dslist)

        dslist = []
        if name in fullpool.keys():
            if name in fullpool.keys():
                dslist.append(
                            {
#                        "dsname": name,
#                        "dstype": "POOL",
                        "source": fullpool[name]})
        if dslist:
            self.output("\n    PoolDevice: %s\n" % name)
            printTable(self, dslist)
        dslist = []

        if name in avds:
            desc = self.selector.DataSourceDescription([str(name)])
            if desc:
                md = json.loads(desc[0])
                if "record" in md:
                    md["source"] = md["record"]
                    md.pop("record")
                    md.pop("dsname")
                    md["source_type"] = md["dstype"]
                    md.pop("dstype")
                dslist.append(md)

        if dslist:
            self.output("\n    DataSource: %s\n" % name)
            printTable(self, dslist)


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


def printProfile(mcr, server, outflag=False):
    out = None
    if outflag:
        out = List(["Profile (MntGrp): %s"
                    % str(getString(mcr, "MntGrp")), ""],
                   text_alignment=(Right, Right),
                   max_col_width=(-1, 60),
                   )
    if not out:
        printString(mcr, "MntGrp", "Profile (and MntGrp)", out=out)
        mcr.output("")
    printConfList(mcr, "Timer", True, "Timer(s)", out=out)
    if not out:
        mcr.output("")
    printList(mcr, "SelectedComponents", False, "Detector Components",
              True, out=out)
    if not out:
        mcr.output("")
    printList(mcr, "SelectedDataSources", False, "Other Detector Channels",
              True, out=out)
    if not out:
        mcr.output("")
    printList(mcr, "MandatoryComponents", False, "Mandatory Components",
              True, out=out)
    if not out:
        mcr.output("")
    printList(mcr, "PreselectedComponents", False, "Description Components",
              True, out=out)
    if not out:
        mcr.output("")
    printConfList(mcr, "InitDataSources", True,
                  "Other Description Channels", out=out)
    if not out:
        mcr.output("")
    printDict(mcr, "UserData", True, "User Data", out=out)
    if not out:
        mcr.output("")
    #        printDict(mcr, "ConfigVariables", True, "ConfigServer Variables")
#        mcr.output("")
    printString(mcr, "AppendEntry", out=out)
    if not out:
        mcr.output("")
        mcr.output("SelectorServer:  %s" % str(server))
    else:
        out.append(["SelectorServer", str(server)])
    printString(mcr, "ConfigDevice", "ConfigServer", out=out)
    printString(mcr, "WriterDevice", "WriterServer", out=out)
    return out


def printDict(mcr, name, decode=True, label=None, out=None):
    """ Print the given server dictionary """

    if not hasattr(mcr, "selector"):
        set_selector(mcr)
    title = "%s" % (name if label is None else label)
    try:
        mname = str(name)[0].lower() + str(name)[1:]
        data = getattr(mcr.selector, mname)
        if decode:
            data = json.loads(data)
        if data is None:
            data = {}
        else:
            data = dict(
                [str(k), (str(v) if isinstance(v, unicode) else v)]
                for k, v in data.items())
    except Exception:
        pass
    if not out:
        mcr.output("%s:  %s" % (title, str(data)))
    else:
        out.appendRow([title, str(data)])


def printConfDict(mcr, name, decode=True, label=None, out=None):
    """ Print the given server dictionary from Configuration"""

    if not hasattr(mcr, "selector"):
        set_selector(mcr)
    conf = json.loads(mcr.selector.profileConfiguration)

    title = "%s" % (name if label is None else label)
    try:
        data = conf[name]
        if decode:
            data = json.loads(data)
        if data is None:
            data = {}
        else:
            data = dict(
                [str(k), (str(v) if isinstance(v, unicode) else v)]
                for k, v in data.items())
    except Exception:
        pass
    if not out:
        mcr.output("%s:  %s" % (title, str(data)))
    else:
        out.appendRow([title, str(data)])


def printConfList(mcr, name, decode=True, label=None, out=None):
    """ Print the given server list from Configuration """

    if not hasattr(mcr, "selector"):
        set_selector(mcr)
    conf = json.loads(mcr.selector.profileConfiguration)

    title = "%s" % (name if label is None else label)
    try:
        data = conf[name]
        if decode:
            data = json.loads(data)
        if data is None:
            data = []
        else:
            data = [
                (str(v) if isinstance(v, unicode) else v)
                for v in data]
    except Exception as e:
        mcr.output(str(e))
    if not out:
        mcr.output("%s:  %s" % (
                title,
                ", ".join(data) if data else "< None >"))
    else:
        out.appendRow([title, ", ".join(data) if data else "< None >"])


def printList(mcr, name, decode=True, label=None, command=False, out=None):
    """ Print the given server list """

    if not hasattr(mcr, "selector"):
        set_selector(mcr)
#    title = "%s:" % (name if label is None else label)
    title = "%s" % (name if label is None else label)
    try:
        mname = str(name)[0].lower() + str(name)[1:]
        if not command:
            data = getattr(mcr.selector, mname)
        else:
            if isinstance(mcr.selector, PyTango.DeviceProxy):
                data = mcr.selector.command_inout(name)
            else:
                data = getattr(mcr.selector, mname)()
        if decode:
            data = json.loads(data)
        if data is None:
            data = []
        else:
            data = [
                (str(v) if isinstance(v, unicode) else v)
                for v in data]
    except Exception as e:
        mcr.output(str(e))
    if not out:
        mcr.output("%s:  %s" % (title,
                               ", ".join(data) if data else "< None >"))
    else:
        out.appendRow([title, ", ".join(data) if data else "< None >"])


def printConfString(mcr, name, label=None):
    """ Print the given server variable from Configuration """

    if not hasattr(mcr, "selector"):
        set_selector(mcr)
    conf = json.loads(mcr.selector.profileConfiguration)
    data = conf[name]
    title = name if label is None else label
    if not out:
        mcr.output("%s:  %s" % (title, data))
    else:
        out.appendRow([title, data])


def getString(mcr, name, command=False):
    if not hasattr(mcr, "selector"):
        set_selector(mcr)
    mname = str(name)[0].lower() + str(name)[1:]
    if not command:
        data = getattr(mcr.selector, mname)
    else:
        if isinstance(mcr.selector, PyTango.DeviceProxy):
            data = mcr.selector.command_inout(name)
        else:
            data = getattr(mcr.selector, mname)()
    return data


def printString(mcr, name, label=None, command=False, out=None):
    """ Print the given server attribute """
    data = getString(mcr, name, command)
    title = name if label is None else label
    if not out:
        mcr.output("%s:  %s" % (title, data))
    else:
        out.appendRow([title, data])


def orderedKeys(lst):
    """ Find headers """
    dorder = ["source_name", "source_type", "source", "nexus_type", "shape"]
    headers = set()
    for dct in lst:
        for k in dct.keys():
            headers.add(k)
    ikeys = list(headers)
    if ikeys:
        okeys = [k for k in dorder if k in ikeys]
        okeys.extend(list(sorted(set(ikeys) - set(okeys))))
    else:
        okeys = []
    return okeys


def printTable(mcr, lst):
    """ Print adjusted list """
    headers = orderedKeys(lst)
    out = List(headers,
               text_alignment=tuple([Right] * len(headers)),
               max_col_width=tuple([-1] * len(headers)),
               )
    for dct in lst:
        row = [(dct[key] if key in dct else 'None') for key in headers]
        out.appendRow(row)
    for line in out.genOutput():
        mcr.output(line)


def set_selector(mcr):
    """ Set the current selector server """
    db = PyTango.Database()
    try:
        servers = [mcr.getEnv("NeXusSelectorDevice")]
    except Exception as e:
        mcr.debug(str(e))
        servers = db.get_device_exported_for_class(
            "NXSRecSelector").value_string

    if servers and servers[0] != 'module':
        mcr.selector = PyTango.DeviceProxy(str(servers[0]))
        return str(servers[0])
    else:
        from nxsrecconfig import Settings
        mcr.selector = Settings.Settings()


def update_configuration(mcr):
    """ Synchonize profile with mntgrp """
    mcr.selector.updateMntGrp()
    mcr.selector.importMntGrp()
    if not isinstance(mcr.selector, PyTango.DeviceProxy):
        mcr.selector.exportEnvProfile()


def update_description(mcr):
    """ Update selection of description components """
    try:
        mcr.selector.preselectComponents()
    except PyTango.CommunicationFailed as e:
        if e[-1].reason == "API_DeviceTimedOut":
            wait_for_device(mcr.selector)
        else:
            raise

