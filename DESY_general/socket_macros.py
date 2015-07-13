#!/bin/env python

"""
macros that communicate to the SardanaMonitor and the SardanaMessageWindow via sockets
"""

__all__ = ["socketIO", "smOpen", "smPost", "mwOpen", "mwOutput"]

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

    def run(self, host, port, msg):
        global scktDct
        hp = "%s:%-d" % (host, port)
        result = False
        if not scktDct.has_key( hp):
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
                return result
            self.output("new socket: connect() via port %d" % port)
            scktDct[ hp] = sckt

        lenOut = scktDct[ hp].send( msg)
        data = scktDct[ hp].recv(1024)
        if len(data) == 0:
            self.output( "socketIO: lost connection, resetting things")
            del scktDct[hp]
            return result
        # self.output( "%s -> %s ", msg, str(data).strip())
        result = True
        return result
#
# the SardanaMonitor macros
#
class smStart(Macro):
    """
    launches the SardanaMonitor
    """
    param_def = []

    def run(self):
        self.output( "launching the SardanaMonitor")
        os.system( "export DISPLAY=:0;/usr/bin/SardanaMonitor.py &")

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
                self.output( "smPost: shell-environment variable PRINTER not defined")
                return

        a = self.socketIO( socket.gethostname(), 7650, "post/print/nocon/lp=%s" % printer)
        if not a.getResult():
            self.output( "smPost: no SardanaMonitor")
#
# the message window macros
#
class mwOutput(Macro):
    """
    send a message to the message window
    """
    param_def = [
        [ "msg", Type.String, None,  "message to the message window" ],
        ]
    def run(self, msg):
        a = self.socketIO( socket.gethostname(), 7660, msg)
        if not a.getResult():
            os.system( "export DISPLAY=:0;/usr/bin/SardanaMessageWindow.py &")
            time.sleep(2)
            a = self.socketIO( socket.gethostname(), 7660, msg)
            if not a.getResult():
                self.output( "mwOutput: something's wrong")









