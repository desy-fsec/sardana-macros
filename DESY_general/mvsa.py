#!/usr/bin/env python
# 
from sardana.macroserver.macro import *
from sardana.macroserver.macro import macro
import PyTango
import time
import HasyUtils

class mvsa(Macro):
    """   Reads the most recent output file and moves a motor 
          to the maximum of the column defined by SignalCounter.

          Used environment variables: 
              ScanDir, ScanFile, ScanID  -> file name
              ScanHistory                -> motor name
              SignalCounter              -> counter name   """

    param_def = [ 
        ['mode', Type.String  , 'peak', "Options: 'peak','cms','cen','dip','dipm','dipc','step','stepm' and 'stepc'"],
        ['interactiveFlag', Type.Boolean , True  , "Option to switch from interactive operation"]
        ]

    interactive = True

    def getFullPathName( self): 
        '''
        constructs the full file name using ScanDir, ScanFile and ScanID
        '''
        temp = "%05d" % int(self.getEnv( "ScanID"))
        #
        # sometimes ScanFile is a one-element list instead of an array
        #
        var = self.getEnv( "ScanFile")
        lst = []
        if type(var).__name__ == 'list':
            lst = var[0].split(".")
        else:
            lst = var.split(".")
        argout = self.getEnv( 'ScanDir') + "/" + lst[0] + "_" + temp + "." + lst[1]
        return argout

    def run(self, mode, interactiveFlag):
        signalCounter = self.getEnv( "SignalCounter")

        fileName = self.getFullPathName()
        a = HasyUtils.fioReader( fileName)

        message = 'undefined'
        for col in a.columns:
            if col.name == signalCounter:
                message, xpos, xpeak, xcms, xcen = HasyUtils.fastscananalysis( col.x, col.y, mode)
                break

        if message != 'success':
            self.output( "mvsa: failed to find the maximum for %s" % ( a.fileName))
            self.output( "mvsa: reason %s" % ( message))
            return
        
        motorName  = self.getEnv( "ScanHistory")[-1]['title'].split()[1] 
        motorProxy = PyTango.DeviceProxy( motorName)

        if interactiveFlag == False:
            motorProxy.write_attribute( "Position", xpos)
            while motorProxy.State() == PyTango.DevState.MOVING:
                time.sleep( 0.1)
            self.output( "Motor %s now at %g" % (motorName, motorProxy.Position))
        elif interactiveFlag == True:
            answer = self.input( "Move %s from %g to %g (%s) :" % (motorName, motorProxy.Position, xpos, signalCounter))
            if answer.lower() == "yes" or answer.lower() == "y":
                motorProxy.write_attribute( "Position", xpos)
                while motorProxy.State() == PyTango.DevState.MOVING:
                    time.sleep( 0.1)
                self.output( "Motor %s is now at %g!" % (motorName, motorProxy.Position))
            else:
                self.output( "Motor %s not moved!" % motorName)
        
