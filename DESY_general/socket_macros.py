#!/bin/env python
  
"""
macros that communicate to the SardanaMonitor and the SardanaMessageWindow via sockets
"""

__all__ = ["socketIO", "smOpen", "smPost", "mwOutput"]

from sardana.macroserver.macro import Macro, Type
import socket 
import os, time
import commands

scktDct = {}

class socketIO(Macro):
    """
    Communicate with a socket server (write-read). Scans for available ports
    in the range [port, port + 9]

    Default ports: 
      SardanaMonitor:       7650
      SardanaMessageWindow: 7660

    """
    param_def = [
        [ "host", Type.String, None,  "the server host" ],
        [ "port", Type.Integer, None, "the port number" ],
        [ "msg",  Type.String, None,  "a msg to be passed" ],
        ]

    result_def = [[ "result", Type.Boolean, None, "completion status" ]]

    def findServer( self, host, port):
        global scktDct
        hp = "%s:%-d" % (host, port)
        sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #
        #  find the server
        #
        for i in range(10):
            try:
                sckt.connect((host, port))
            except Exception, e:
                port = port + 1
                continue
            break
        else:
            sckt.close()
            return False
        self.output("findServer: connect() via port %d" % port)
        scktDct[ hp] = sckt
        return True
 
    def run(self, host, port, msg):
        global scktDct
        hp = "%s:%-d" % (host, port)
        result = False
        if not scktDct.has_key( hp):
            if not self.findServer( host, port):
                return result
        if msg == "":
            msg = "_"
        lenOut = scktDct[ hp].send( msg)
        data = scktDct[ hp].recv(1024)
        #
        # scktDct lives in the MacroServer. The contents may very 
        # be out-dated, because we may have restarted the MessageWindow 
        # for each spock session. Therefore we delete the dictionary 
        # entry and try to find the server
        #
        if len(data) == 0:
            del scktDct[hp]
            if not self.findServer( host, port):
                return result
            lenOut = scktDct[ hp].send( msg)
            data = scktDct[ hp].recv(1024)
            if len(data) > 0:
                return True
            else:
                return False
        # self.output( "%s -> %s ", msg, str(data).strip())
        result = True
        return result
#
# the SardanaMonitor macros
#
class smPost(Macro):
    """
    sends a postscript command, 'post/print/nocon', to the SardanaMonitor

    """
    param_def = [
        [ "printer", Type.String, "default",  "the printer name" ],
        ]

    def run(self, printer):
        if printer.find( 'default') == 0:
            printer = os.getenv( 'PRINTER')
            if printer is None:
                self.output( "smPost: shell-environment variable PRINTER not defined and no parameter supplied")
                return

        a = self.socketIO( socket.gethostname(), 7650, "post/print/nocon/lp=%s" % printer)
        if not a.getResult():
            self.output( "smPost: no SardanaMonitor")
#
# the message window macros
#
class mwOutput(Macro):
    """
    Send a message to the message window. 
    To launch the message window from spock:
      p10/door/haspp10e2.01 [6]: ! SardanaMessageWindow.py &
    """
    param_def = [
        [ "msg", Type.String, "",  "message to the message window" ],
        ]
    def run(self, msg):
        a = self.socketIO( socket.gethostname(), 7660, msg)

class mwTest(Macro):
    """
    Send a test message to the message windowto see whether it exists. 
    To launch the message window from spock, e.g.:
      p10/door/haspp10e2.01 [6]: ! SardanaMessageWindow.py &
    """
    param_def = []
    result_def = [[ "result", Type.Boolean, None, "server exists" ]]
    def run(self):
        result = False
        #
        # testMessage will not be printed
        #
        a = self.socketIO( socket.gethostname(), 7660, "testMessage")
        if a.getResult():
            result = True
        return result



