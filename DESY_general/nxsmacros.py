#!/usr/bin/env python
""" NeXus recorder macros """

import PyTango
import time
import json
import fnmatch
import os
import sys
import subprocess
from sardana.macroserver.macro import (
    Macro, Type, macro)
from sardana.macroserver.msexception import UnknownEnv

from taurus.console.list import List
from taurus.console import Alignment

Left, Right, HCenter = Alignment.Left, Alignment.Right, Alignment.HCenter
Nothing = '< None >'
Splitter = ', '


if sys.version_info > (3,):
    str = str


def device_groups(self):
    """ Return device groups """
    if hasattr(self.selector, "deviceGroups"):
        return json.loads(self.selector.deviceGroups)
    else:
        return { "counter": ["*exp_c*"],
                 "timer": ["*exp_t*"],
                 "mca": ["*exp_mca*"],
                 "dac": ["*exp_dac*"],
                 "adc": ["*exp_adc*"],
                 "motor": ["*exp_mot*"]}


@macro([["options_list",
         [['option', Type.String, 'None', 'option'],
          ['value', Type.String, 'None', 'value']],
         ['None', 'None'],
         "List of options and values"]])
def nxselector(self, options_list):
    """
    nxselector -m <interface_mode> -d <door_device> -s <selector_server> \
-x <display> -u <user>

    Run NeXus Component Selector. All parameters are optional.
      -m <interface_mode>: interface mode,
                           i.e. simple, user, advanced, expert
      -d <door_device>:  door device name
      -s <selector_server>: selector server device name
      -x <display>: display environment variable, \
 i.e. value of the linux $DISPLAY variable.
                   In spock one can get it via the `!echo $DISPLAY` command.
                   It is useful to start nxselector on remote computer/monitor.
                   Other option is to run nxselector \
from the linux command-line.
      -u <user>: remote user name

    Example:
      nxselector -m expert -d p09/door/haso228 -s p09/nxsrecselector/haso228 \
-x localhost:10.0 -u p09user
    """
    opt_dict = {}
    for opt_par in options_list:
        opt_dict[opt_par[0]] = opt_par[1]
    args = ["nxselector"]
    if '-m' in opt_dict.keys():
        args.append("-m%s" % opt_dict['-m'])
    if '-d' in opt_dict.keys():
        args.append("-d%s" % opt_dict['-d'])
    if '-s' in opt_dict.keys():
        args.append("-s%s" % opt_dict['-s'])
    my_env = os.environ.copy()
    if 'GNOME_DESKTOP_SESSION_ID' not in my_env.keys():
        my_env['GNOME_DESKTOP_SESSION_ID'] = 'qtconfig'
    if '-x' not in opt_dict.keys():
        if 'DISPLAY' not in my_env.keys():
            my_env['DISPLAY'] = ':0.0'
    else:
        my_env['DISPLAY'] = opt_dict['-x']
        if 'XAUTHORITY' in my_env.keys():
            my_env.pop('XAUTHORITY')
    if '-u' not in opt_dict.keys():
        if 'USER' not in my_env.keys():
            if 'TANGO_USER' in my_env.keys():
                my_env['USER'] = my_env['TANGO_USER']
            else:
                import getpass
                my_env['USER'] = getpass.getuser()
    else:
        my_env['USER'] = opt_dict['-u']
    subprocess.Popen(args, env=my_env)


@macro([["options_list",
         [['option', Type.String, 'None', 'option'],
          ['value', Type.String, 'None', 'value']],
         ['None', 'None'],
         "List of options and values"]])
def nxsmacrogui(self, options_list):
    """
    nxsmacrogui -d <door_device> -s <selector_server> \
-x <display> -u <user>

    Run NeXus MacroGUI. All parameters are optional.
      -d <door_device>:  door device name
      -s <selector_server>: selector server device name
      -x <display>: display environment variable, \
i.e. value of the linux $DISPLAY variable.
                   In spock one can get it via the `!echo $DISPLAY` command.
                   It is useful to start nxselector on remote computer/monitor.
                   Other option is to run nxselector \
from the linux command-line.
      -u <user>: remote user name

    Example:
      nxsmacrogui -d p09/door/haso228 -s p09/nxsrecselector/haso228 \
-x localhost:10.0 -u p09user
    """
    opt_dict = {}
    for opt_par in options_list:
        opt_dict[opt_par[0]] = opt_par[1]
    args = ["nxsmacrogui"]
    if '-d' in opt_dict.keys():
        args.append("-d%s" % opt_dict['-d'])
    if '-s' in opt_dict.keys():
        args.append("-s%s" % opt_dict['-s'])
    my_env = os.environ.copy()
    if 'GNOME_DESKTOP_SESSION_ID' not in my_env.keys():
        my_env['GNOME_DESKTOP_SESSION_ID'] = 'qtconfig'
    if '-x' not in opt_dict.keys():
        if 'DISPLAY' not in my_env.keys():
            my_env['DISPLAY'] = ':0.0'
    else:
        my_env['DISPLAY'] = opt_dict['-x']
        if 'XAUTHORITY' in my_env.keys():
            my_env.pop('XAUTHORITY')
    if '-u' not in opt_dict.keys():
        if 'USER' not in my_env.keys():
            if 'TANGO_USER' in my_env.keys():
                my_env['USER'] = my_env['TANGO_USER']
            else:
                import getpass
                my_env['USER'] = getpass.getuser()
    else:
        my_env['USER'] = opt_dict['-u']
    subprocess.Popen(args, env=my_env)


@macro()
def nxsprof(self):
    """ List the current profile """

    server = set_selector(self)
    try:
        ismgupdated = False
        self.nxsimportmg()
        ismgupdated = self.selector.isMntGrpUpdated()
    finally:
        mout = printProfile(self, server)
        for line in mout.genOutput():
            self.output(line)

        if not ismgupdated:
            self.info("\nProfile is not set by nxselector(nxsmacros) "
                      "or MntGrp has been changed")


@macro()
def lsprof(self):
    """ List the current profile """

    nxsprof(self)


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
    self.output("Device Types:  %s"
                % Splitter.join(device_groups(self).keys()))


class nxsetprof(Macro):
    """ Set the active profile.
        This action changes also ActiveMntGrp if the profile name is given
    """

    param_def = [
        ['name', Type.String, '', 'profile name'],
    ]

    def run(self, name):
        set_selector(self)
        profname = self.selector.mntgrp
        try:
            mgname = self.getEnv("ActiveMntGrp")
        except UnknownEnv:
            mgname = None
        if not name:
            name = mgname
        elif mgname != profname:
            if mgname:
                self.unsetEnv("ActiveMntGrp")
        if name:
            self.selector.mntgrp = name
        fetchProfile(self)
        self.selector.importMntGrp()
        self.selector.storeProfile()
        update_configuration(self)


class nxsimportmg(Macro):
    """ Import Active Measurement Group
    """

    def run(self):
        set_selector(self)
        try:
            name = self.getEnv("ActiveMntGrp")
        except UnknownEnv:
            name = self.selector.mntgrp
        self.selector.mntgrp = name
        fetchProfile(self)
        self.selector.importMntGrp()
        self.selector.storeProfile()


class nxsrmprof(Macro):
    """ Remove the given profile
        A list of available profiles can be shown by the 'nxslsprof' macro
 """

    param_def = [
        ['name', Type.String, None, 'profile name']]

    def run(self, name):
        set_selector(self)
        self.selector.deleteProfile(name)


class nxsrmallprof(Macro):
    """ Remove the all profiles
        A list of available profiles can be shown by the 'nxslsprof' macro
 """

    param_def = [
        ['execute', Type.Boolean, False, 'remove all profiles']]

    def run(self, execute):
        set_selector(self)
        if execute:
            self.selector.deleteAllProfiles()
        else:
            self.output("To remove all available profile: "
                        "'nxsrmallprof True'\n")
            printList(self, "AvailableProfiles", False,
                      "Available Profiles", True)


class nxsettimers(Macro):
    """ Set the current profile timers.
        Available timer names can be listed by 'nxslstimers' macro
    """

    param_def = [
        ['timer_list',
         [['timer', Type.String, None, 'timer to select']],
         None, 'List of profile timers to set']]

    def run(self, timer_list):
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
         [['component', Type.String, None,
           'detector component to add']],
         None, 'List of detector components to add']]

    def run(self, component_list):
        set_selector(self)
        cnf = json.loads(self.selector.profileConfiguration)
        cpdct = json.loads(cnf["ComponentSelection"])
        dsdct = json.loads(cnf["DataSourceSelection"])
        pch = self.selector.poolElementNames('ExpChannelList')
        for name in component_list:
            if name not in pch and name in self.selector.availableComponents():
                cpdct[str(name)] = True
            elif name in pch or name in self.selector.availableComponents():
                dsdct[str(name)] = True
            else:
                self.warning("'%s' is not defined" % name)
        cnf["DataSourceSelection"] = str(json.dumps(dsdct))
        cnf["ComponentSelection"] = str(json.dumps(cpdct))
        self.selector.profileConfiguration = str(json.dumps(cnf))
        update_configuration(self)


class nxsetorder(Macro):
    """ Set a new order of detector datasources or channels
        Available datasources can be listed by 'nxslsds' macro
    """

    param_def = [
        ['datasource_list',
         [['datasource', Type.String, None,
           'new order of datasources']],
         None, 'List of datasources in the right order'],
    ]

    def run(self, datasource_list):
        set_selector(self)
        cnf = json.loads(self.selector.profileConfiguration)
        dslist = json.loads(cnf["OrderedChannels"])
        cnf["OrderedChannels"] = str(json.dumps(list(datasource_list)))
        self.output("Old channel order: %s" % dslist)
        self.output("New channel order: %s" % datasource_list)
        self.selector.profileConfiguration = str(json.dumps(cnf))
        update_configuration(self)


class nxset(Macro):
    """ Set the given timer(s) and detector components
        Available components can be listed by
        'nxsls', 'nxslscp' or 'nxslsds' macros
    """

    param_def = [
        ['component_list',
         [['component', Type.String, None,
           'detector component to add']],
         None, 'List of detector components to add'],
    ]

    def run(self, component_list):
        set_selector(self)
        timers = self.selector.availableTimers()
        stimers = [tm for tm in component_list if tm in timers]
        if not stimers:
            self.warning("Timer is missing")
            return

        cnf = json.loads(self.selector.profileConfiguration)
        cpdct = json.loads(cnf["ComponentSelection"])
        dsdct = json.loads(cnf["DataSourceSelection"])
        for name in cpdct.keys():
            cpdct[str(name)] = False
        for name in dsdct.keys():
            dsdct[str(name)] = False
        pch = self.selector.poolElementNames('ExpChannelList')
        for name in component_list:
            if name not in pch and name in self.selector.availableComponents():
                cpdct[str(name)] = True
            elif name in pch or name in self.selector.availableComponents():
                if str(name) not in stimers:
                    dsdct[str(name)] = True
            else:
                self.warning("'%s' is not defined" % name)
        cnf["Timer"] = str(json.dumps(stimers))
        cnf["DataSourceSelection"] = str(json.dumps(dsdct))
        cnf["ComponentSelection"] = str(json.dumps(cpdct))
        self.selector.profileConfiguration = str(json.dumps(cnf))
        update_configuration(self)


class nxsdel(Macro):
    """ Remove the given detector components.
        Selected detector components can be listed by
        'nxsprof' or 'lsprof' macros
    """

    param_def = [
        ['component_list',
         [['component', Type.String, None,
           'detector component to remove']],
         None, 'List of components to show'],
    ]

    def run(self, component_list):
        set_selector(self)
        cnf = json.loads(self.selector.profileConfiguration)
        cpdct = json.loads(cnf["ComponentSelection"])
        dsdct = json.loads(cnf["DataSourceSelection"])
        timers = json.loads(cnf["Timer"])
        for name in component_list:
            if name in cpdct:
                cpdct.pop(str(name))
                self.output("Removing %s" % name)
            if name in dsdct:
                dsdct.pop(str(name))
                self.output("Removing %s" % name)
            if timers and name in timers and timers[0] != name:
                timers.remove(name)
        cnf["Timer"] = str(json.dumps(list(timers)))
        cnf["DataSourceSelection"] = str(json.dumps(dsdct))
        cnf["ComponentSelection"] = str(json.dumps(cpdct))
        self.selector.profileConfiguration = str(json.dumps(cnf))
        update_configuration(self)


class nxsrm(Macro):
    """ Deselect the given detector components.
        Selected detector components can be listed by
        'nxsprof' or 'lsprof' macros
    """

    param_def = [
        ['component_list',
         [['component', Type.String, None, 'detector component to remove']],
         None, 'List of components to show'],
    ]

    def run(self, component_list):
        set_selector(self)
        cnf = json.loads(self.selector.profileConfiguration)
        cpdct = json.loads(cnf["ComponentSelection"])
        dsdct = json.loads(cnf["DataSourceSelection"])
        timers = json.loads(cnf["Timer"])
        for name in component_list:
            if name in cpdct:
                cpdct[str(name)] = False
            if name in dsdct:
                dsdct[str(name)] = False
            if timers and name in timers and timers[0] != name:
                timers.remove(name)
        cnf["Timer"] = str(json.dumps(list(timers)))
        cnf["DataSourceSelection"] = str(json.dumps(dsdct))
        cnf["ComponentSelection"] = str(json.dumps(cpdct))
        self.selector.profileConfiguration = str(json.dumps(cnf))
        update_configuration(self)


@macro()
def nxsclr(self):
    """ Removes all detector components from the current profile"""

    if not hasattr(self, "selector"):
        set_selector(self)
    cnf = json.loads(self.selector.profileConfiguration)
    cpdct = json.loads(cnf["ComponentSelection"])
    dsdct = json.loads(cnf["DataSourceSelection"])
    for name in cpdct.keys():
        cpdct[str(name)] = False
    for name in dsdct.keys():
        dsdct[str(name)] = False
    cnf["DataSourceSelection"] = str(json.dumps(dsdct))
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
         [['component', Type.String, None,
           'description component to add']],
         None, 'List of description components to add'],
    ]

    def run(self, component_list):
        set_selector(self)
        cnf = json.loads(self.selector.profileConfiguration)
        cpdct = json.loads(cnf["ComponentPreselection"])
        if self.selector_version <= 2:
            dsdct = set(json.loads(cnf["InitDataSources"]))
            for name in component_list:
                if name in self.selector.availableComponents():
                    cpdct[str(name)] = True
                    self.output("%s added" % name)
                elif name in self.selector.availableDataSources():
                    dsdct.add(str(name))
                else:
                    self.warning("'%s' is not defined" % name)
            cnf["InitDataSources"] = str(json.dumps(list(dsdct)))
        else:
            dsdct = json.loads(cnf["DataSourcePreselection"])
            for name in component_list:
                if name in self.selector.availableComponents():
                    cpdct[str(name)] = True
                    self.output("%s added" % name)
                elif name in self.selector.availableDataSources():
                    dsdct[str(name)] = True
                    self.output("%s added" % name)
                else:
                    self.warning("'%s' is not defined" % name)
            cnf["DataSourcePreselection"] = str(json.dumps(dsdct))
        cnf["ComponentPreselection"] = str(json.dumps(cpdct))
        self.selector.profileConfiguration = str(json.dumps(cnf))
        update_description(self)
        update_configuration(self)


class nxsdeldesc(Macro):
    """ Remove the given description components.
        Selected description components can be listed by
        'nxsprof' or 'lsprof' macros
        """

    param_def = [
        ['component_list',
         [['component', Type.String, None,
           'description component to remove']],
         None, 'List of descpription components to remove'],
    ]

    def run(self, component_list):
        set_selector(self)
        cnf = json.loads(self.selector.profileConfiguration)
        cpdct = json.loads(cnf["ComponentPreselection"])
        if self.selector_version <= 2:
            dsdct = set(json.loads(cnf["InitDataSources"]))
            for name in component_list:
                if name in cpdct:
                    cpdct.pop(str(name))
                    self.output("Removing %s" % name)
                if name in dsdct:
                    dsdct.remove(str(name))
                    self.output("Removing %s" % name)
            cnf["InitDataSources"] = str(json.dumps(list(dsdct)))
        else:
            dsdct = json.loads(cnf["DataSourcePreselection"])
            for name in component_list:
                if name in cpdct:
                    cpdct.pop(str(name))
                    self.output("Removing %s" % name)
                if name in dsdct:
                    dsdct.pop(str(name))
                    self.output("Removing %s" % name)
            cnf["DataSourcePreselection"] = str(json.dumps(dsdct))

        cnf["ComponentPreselection"] = str(json.dumps(cpdct))
        self.selector.profileConfiguration = str(json.dumps(cnf))
        update_description(self)
        update_configuration(self)


class nxsrmdesc(Macro):
    """ Deselect the given description components.
        Selected description components can be listed by
        'nxsprof' or 'lsprof' macros
    """

    param_def = [
        ['component_list',
         [['component', Type.String, None,
           'description component to remove']],
         None, 'List of descpription components to remove'],
    ]

    def run(self, component_list):
        set_selector(self)
        cnf = json.loads(self.selector.profileConfiguration)
        cpdct = json.loads(cnf["ComponentPreselection"])
        if self.selector_version <= 2:
            dsdct = set(json.loads(cnf["InitDataSources"]))
            for name in component_list:
                if name in cpdct:
                    cpdct[str(name)] = False
                if name in dsdct:
                    dsdct.remove(str(name))
                    self.output("Removing %s" % name)
            cnf["InitDataSources"] = str(json.dumps(list(dsdct)))
        else:
            dsdct = json.loads(cnf["DataSourcePreselection"])
            for name in component_list:
                if name in cpdct:
                    cpdct[str(name)] = False
                if name in dsdct:
                    dsdct[str(name)] = False
            cnf["DataSourcePreselection"] = str(json.dumps(dsdct))

        cnf["ComponentPreselection"] = str(json.dumps(cpdct))
        self.selector.profileConfiguration = str(json.dumps(cnf))
        update_description(self)
        update_configuration(self)


class nxsetappentry(Macro):
    """ Set the append entry flag for the current profile.
        If the flag is True all consecutive scans are stored in one file
    """

    param_def = [
        ['append_flag', Type.Boolean, '', 'append entry flag']]

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
         [['name', Type.String, None, 'user data name to delete']],
         None, 'List of user data names to delete'],
    ]

    def run(self, name_list):
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
        Descriptive component group can be changed by
        'nxsadddesc' and 'nxsrmdesc' macros.
    """

    def run(self):
        set_selector(self)
        update_description(self)
        update_configuration(self)


class nxsresetdesc(Macro):
    """ Reset a selection of description components to default set.
        The selection is made with respected to working status
        of component tango (motor) devices.
        Selected description components can be listed by
        'nxsprof' or 'lsprof' macros.
        Descriptive component group can be changed by
        'nxsadddesc' and 'nxsrmdesc' macros.
    """

    def run(self):
        set_selector(self)
        reset_descriptive_components(self)
        update_description(self)
        update_configuration(self)


class nxsave(Macro):
    """ Save the current profile to the given file.
        The file name may contain a file path
    """

    param_def = [
        ['fname', Type.String, '', 'file name']]

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
        ['fname', Type.String, '', 'file name']]

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
        ['dev_type', Type.String, '', 'device type or name pattern']]

    def run(self, dev_type):
        set_selector(self)

        adss = set(self.selector.availableDataSources())
        pchs = set(self.selector.poolElementNames('ExpChannelList'))
        acps = set(self.selector.availableComponents())
        fdss = self._filterSet(adss, dev_type)
        fchs = self._filterSet(pchs, dev_type)
        fcps = self._filterSet(acps, dev_type)

        if fdss:
            self.output("\n    DataSources:\n")
            self.output(Splitter.join(list(fdss)))
        if fchs:
            self.output("\n    PoolDevices:\n")
            self.output(Splitter.join(list(fchs)))
        if fcps:
            self.output("\n    Components:\n")
            self.output(Splitter.join(list(fcps)))

    def _filterSet(self, comps, dev_type):
        available = set()
        groups = device_groups(self)
        if dev_type:
            if dev_type not in groups.keys() and \
                    dev_type[-1] == 's' and dev_type[:-1] in groups.keys():
                dev_type = dev_type[:-1]
            if dev_type in groups.keys():
                for gr in groups[dev_type]:
                    filtered = fnmatch.filter(
                        comps, gr)
                    available.update(filtered)
            else:
                filtered = fnmatch.filter(
                    comps, "*%s*" % dev_type)
                available.update(filtered)
        else:
            available.update(comps)
        return available


class nxshow(Macro):
    """ Describe the given detector component.
        Available components can be listed by
        'nxsls', 'nxslscp' or 'nxslsds' macros
    """

    param_def = [
        ['name', Type.String, '', 'component name']]

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
                dslist.append({"source": fullpool[name]})
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


def fetchProfile(mcr):
    configold = getString(mcr, "ConfigDevice")
    doorold = getString(mcr, "Door")
    door = mcr.getDoorName()
    if door and door != doorold:
        mcr.selector.door = door
    mcr.selector.fetchProfile()
    confignew = getString(mcr, "ConfigDevice")
    doornew = getString(mcr, "Door")
    if configold and configold != confignew:
        mcr.selector.configDevice = configold
    if door and door != doornew:
        mcr.selector.door = door
        mcr.info("Profile's door '%s' was changed to '%s'" %
                 (doornew, door))


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


def printProfile(mcr, server):
    out = List(["Profile (MntGrp): %s"
                % str(getString(mcr, "MntGrp")), ""],
               text_alignment=(Right, Right),
               max_col_width=(-1, 60),)
    printConfList(mcr, "Timer", True, "Timer(s)", out=out)
    printList(mcr, "SelectedComponents", False, "Detector Components",
              True, out=out)
    printList(mcr, "SelectedDataSources", False, "", True, out=out)
    mergeLastTwoRows(out)
    printList(mcr, "PreselectedComponents", False, "Descriptive Components",
              True, out=out)
    if mcr.selector_version <= 2:
        printConfList(mcr, "InitDataSources", True, "", out=out)
    else:
        printList(mcr, "PreselectedDataSources", False, "", True, out=out)
    mergeLastTwoRows(out)
    printList(mcr, "MandatoryComponents", False, "Mandatory Components",
              True, out=out)
    printDict(mcr, "UserData", True, "User Data", out=out)
    printString(mcr, "AppendEntry", out=out)
    out.append(["SelectorServer", str(server)])
    printString(mcr, "ConfigDevice", "ConfigServer", out=out)
    printString(mcr, "WriterDevice", "WriterServer", out=out)
    return out


def mergeLastTwoRows(out):
    last = out.pop()
    beforelast = out[-1]
    if last[-1] != Nothing:
        if beforelast[-1] == Nothing:
            beforelast[-1] = last[-1]
        else:
            sbl = beforelast[-1].split(Splitter)
            sl = last[-1].split(Splitter)
            beforelast[-1] = Splitter.join(set(sbl + sl))


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
                [str(k), (str(v) if isinstance(v, str) else v)]
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
                [str(k), (str(v) if isinstance(v, str) else v)]
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
                (str(v) if isinstance(v, str) else v)
                for v in data]
    except Exception as e:
        mcr.output(str(e))
    if not out:
        try:
            mcr.output("%s:  %s" % (
                title,
                Splitter.join(data) if data else Nothing))
        except Exception as e:
            mcr.output(str(e))
    else:
        out.appendRow([title, Splitter.join(data) if data else Nothing])


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
                (str(v) if isinstance(v, str) else v)
                for v in data]
    except Exception as e:
        mcr.output(str(e))
    if not out:
        mcr.output("%s:  %s" % (
            title, Splitter.join(data) if data else Nothing))
    else:
        out.appendRow([title, Splitter.join(data) if data else Nothing])


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
        # to see other timeouts
        mcr.selector.set_timeout_millis(6000)
        mcr.selector.set_source(PyTango.DevSource.DEV)
        setversion(mcr)
        return str(servers[0])
    else:
        from nxsrecconfig import Settings
        mcr.selector = Settings.Settings()
        setversion(mcr)


def setversion(mcr):
    if hasattr(mcr.selector, "version"):
        mcr.selector_version = int(str(mcr.selector.version).split(".")[0])
    else:
        mcr.selector_version = 1


def _long_command(server, command, *var):
    """ Excecutes a long command
    """
    if hasattr(server, "command_inout_asynch"):
        # aid = self.__dp.command_inout_asynch("PreselectComponents")
        # _wait(self.__dp)
        try:
            _command(server, command, *var)
        except PyTango.CommunicationFailed as e:
            if e[-1].reason == "API_DeviceTimedOut":
                _wait(server)
            else:
                raise
    else:
        _command(server, command, *var)


def _command(server, command, *var):
    """ executes command on the server

    :param server: server instance
    :type server: :class:`PyTango.DeviceProxy` \
    or 'nxsrecconfig.Settings.Settings'
    :param command: command name
    :type command: :obj:`str`
    :returns: command result
    :rtype: `any`

    """
    if not hasattr(server, "command_inout"):
        return getattr(server, command)(*var)
    elif var is None:
        return server.command_inout(command)
    else:
        return server.command_inout(command, *var)


def _wait(proxy, counter=100):
    """ waits for server until server is not in running state

    :param proxy: server proxy
    :type proxy: :class:`PyTango.DeviceProxy`
    :param counter: maximum waiting timer in 0.01 sec
                    (without command execution)
    :type counter: :obj:`int`
    """
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


def update_configuration(mcr):
    """ Synchonize profile with mntgrp """
    if hasattr(mcr.selector, "updateProfile"):
        _long_command(mcr.selector, "updateProfile")
    else:
        _long_command(mcr.selector, "updateMntGrp")
        _long_command(mcr.selector, "importMntGrp")
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


def reset_descriptive_components(mcr):
    """ Reset selection of description components """
    try:
        mcr.selector.resetPreselectedComponents()
    except PyTango.CommunicationFailed as e:
        if e[-1].reason == "API_DeviceTimedOut":
            wait_for_device(mcr.selector)
        else:
            raise
