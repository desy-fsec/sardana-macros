"""
    Macros for starting/stopping device servers
"""

import fandango

from sardana.macroserver.macro import Macro, Type, ParamRepeat


class startDS(Macro): 
    """ Starts the given device server"""
    
    param_def = [['dev',Type.String, None, 'Device name or alias']]

    def run(self, dev): 
        serverDict = fandango.ServersDict('*')
        serverName = serverDict.get_device_server(dev)
        server = fandango.ServersDict(serverName)
        server.start_servers()


class stopDS(Macro): 
    """ Stops the given device server"""

    param_def = [['dev',Type.String, None, 'Device name or alias']]

    def run(self, dev): 
        serverDict = fandango.ServersDict('*')
        serverName = serverDict.get_device_server(dev)
        server = fandango.ServersDict(serverName)
        server.stop_servers()


class restartDS(Macro): 
    """ Restarts the given device server"""

    param_def = [['dev',Type.String, None, 'Device name or alias']]

    def run(self, dev): 
        serverDict = fandango.ServersDict('*')
        serverName = serverDict.get_device_server(dev)
        server = fandango.ServersDict(serverName)
        server.restart_servers()
