#!/usr/bin/env python

"""
Macros for restarting servers
"""

import PyTango
import time
from sardana.macroserver.macro import Macro, Type

__all__ = ["restart_server"]


class restart_server(Macro):
    """ restart servers """

    param_def = [
        ['starter_devname', Type.String, None, 'Name of the Starter device'],
        ['server_name', Type.String, None, 'Name of the server']]

    def run(self, starter_devname, server_name):
        starter_dev = PyTango.DeviceProxy(starter_devname)

        list_dev = starter_dev.command_inout("DevGetStopServers", True)
        if server_name in list_dev:
            self.output(" Server already stopped ")
        else:
            self.output("Stopping server %s " % server_name)
            # starter_dev.command_inout("HardKillServer", server_name)
            starter_dev.command_inout("DevStop", server_name)
        list_dev = starter_dev.command_inout("DevGetStopServers", True)
        while server_name not in list_dev:
            time.sleep(1)
            list_dev = starter_dev.command_inout("DevGetStopServers", True)
            self.debug("Waiting for server to stop")
        time.sleep(2)
        list_dev = starter_dev.command_inout("DevGetRunningServers", True)
        if server_name in list_dev:
            self.output(" Server already running ")
        else:
            self.output("Starting server %s " % server_name)
            starter_dev.command_inout("DevStart", server_name)

        list_dev = starter_dev.command_inout("DevGetRunningServers", True)
        while server_name not in list_dev:
            time.sleep(1)
            list_dev = starter_dev.command_inout("DevGetRunningServers", True)
            self.debug("Waiting for server to start")
