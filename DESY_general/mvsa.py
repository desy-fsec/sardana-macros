#!/usr/bin/env python
#
# 
from sardana.macroserver.macro import *
from sardana.macroserver.macro import macro
import PyTango
import time
import numpy as np
import HasyUtils

class mvsa(Macro):
    """   Reads the most recent output file and moves a motor 
          to the maximum of the column defined by SignalCounter.

          Used environment variables: 
              ScanDir, ScanFile, ScanID  -> file name
              ScanHistory                -> motor name and scan type, 
                                            supported: ascan, a2scan, a3scan, dscan, d2scan, d3scan
              SignalCounter              -> counter name   
          'mvsa show' shows the results, no move """
    param_def = [ 
        ['mode', Type.String  , 'peak', "Options: 'show','peak','cms','cen','dip','dipm','dipc','slit', 'slitm', 'slitc', 'step','stepm' and 'stepc'"],
        ['interactiveFlag', Type.Integer , 1, " '1' query before move (def.) "]
        ]
    result_def = [[ "result", Type.String, None, "'status=False' or 'status=True,mot1=12,...'" ]]
    interactive = True

    def getFullPathName( self): 
        '''
        constructs the full file name using ScanDir, ScanFile and ScanID
        '''
        self.scanId =  int(self.getEnv( "ScanID"))
        temp = "%05d" % int(self.getEnv( "ScanID"))
        
        #
        # sometimes ScanFile is a one-element list instead of an array
        #
        var = self.getEnv( "ScanFile")
        lst = []
        if type(var).__name__ == 'list':
            if var[0].find( '.fio') > 0:
                lst = var[0].split(".")
            elif var[1].find( '.fio') > 0:
                lst = var[1].split(".")
            else:
                self.output( "mvsa: ScanFile does not contain a .fio file")
                return None
        else:
            if var.find( '.fio') > 0:
                lst = var.split(".")
            else:
                self.output( "mvsa: ScanFile does not contain a .fio file")
                return None
        argout = self.getEnv( 'ScanDir') + "/" + lst[0] + "_" + temp + "." + lst[1]
        return argout

    def getMotorInfo( self, xpos):
        """ 
        finds the relevant motors in the ScanHistory and
        uses the target position of the first motor to calculate
        the target positions of the other motors
        """
        #
        # d2scan exp_dmy01 -1.0 1.0 exp_dmy02 -2.0 2.0 11 0.1
        # 
        self.output( "Cmd: %s " % self.getEnv( "ScanHistory")[-1]['title'])

        lst = self.getEnv( "ScanHistory")[-1]['title'].split()
        if self.scanId != self.getEnv("ScanHistory")[-1]['serialno']:
            self.output( "mvsa.getMotorInfo: previous scan ended incomplete")
            return None

        argout = []
        if lst[0].lower() == "ascan":
            dct = {}
            dct[ 'motorName'] = lst[1]
            dct[ 'proxy'] = PyTango.DeviceProxy( dct['motorName'])
            dct[ 'targetPos'] = xpos
            argout.append( dct)
        elif lst[0].lower() == "dscan":
            dct = {}
            dct[ 'motorName'] = lst[1]
            dct[ 'proxy'] = PyTango.DeviceProxy( dct['motorName'])
            dct[ 'targetPos'] = xpos
            argout.append( dct)
        elif lst[0].lower() == "a2scan":
            dct = {}
            dct[ 'motorName'] = lst[1]
            dct[ 'proxy'] = PyTango.DeviceProxy( dct['motorName'])
            dct[ 'targetPos'] = xpos
            startPos = float( lst[2])
            endPos   = float( lst[3])
            ratio = (xpos - startPos)/(endPos - startPos)
            argout.append( dct)
            dct = {}
            dct[ 'motorName'] = lst[4]
            dct[ 'proxy'] = PyTango.DeviceProxy( dct['motorName'])
            startPos = float( lst[5])
            endPos   = float( lst[6])
            dct[ 'targetPos'] = startPos + (endPos - startPos)*ratio
            argout.append( dct)
        elif lst[0].lower() == "a3scan":
            dct = {}
            dct[ 'motorName'] = lst[1]
            dct[ 'proxy'] = PyTango.DeviceProxy( dct['motorName'])
            dct[ 'targetPos'] = xpos
            startPos = float( lst[2])
            endPos   = float( lst[3])
            ratio = (xpos - startPos)/(endPos - startPos)
            argout.append( dct)
            dct = {}
            dct[ 'motorName'] = lst[4]
            dct[ 'proxy'] = PyTango.DeviceProxy( dct['motorName'])
            startPos = float( lst[5])
            endPos   = float( lst[6])
            dct[ 'targetPos'] = startPos + (endPos - startPos)*ratio
            argout.append( dct)
            dct = {}
            dct[ 'motorName'] = lst[7]
            dct[ 'proxy'] = PyTango.DeviceProxy( dct['motorName'])
            startPos = float( lst[8])
            endPos   = float( lst[9])
            dct[ 'targetPos'] = startPos + (endPos - startPos)*ratio
            argout.append( dct)
        elif lst[0].lower() == "d2scan":
            dct = {}
            dct[ 'motorName'] = lst[1]
            dct[ 'proxy'] = PyTango.DeviceProxy( dct['motorName'])
            dct[ 'targetPos'] = xpos
            startPos = dct['proxy'].Position + float(lst[2])
            endPos   = dct['proxy'].Position + float(lst[3])
            ratio = (xpos - startPos)/(endPos - startPos)
            argout.append( dct)
            dct = {}
            dct[ 'motorName'] = lst[4]
            dct[ 'proxy'] = PyTango.DeviceProxy( dct['motorName'])
            startPos = dct['proxy'].Position + float( lst[5])
            endPos   = dct['proxy'].Position + float(lst[6])
            dct[ 'targetPos'] = startPos + (endPos - startPos)*ratio
            argout.append( dct)
        elif lst[0].lower() == "d3scan":
            dct = {}
            dct[ 'motorName'] = lst[1]
            dct[ 'proxy'] = PyTango.DeviceProxy( dct['motorName'])
            dct[ 'targetPos'] = xpos
            startPos = dct['proxy'].Position + float(lst[2])
            endPos   = dct['proxy'].Position + float(lst[3])
            ratio = (xpos - startPos)/(endPos - startPos)
            argout.append( dct)
            dct = {}
            dct[ 'motorName'] = lst[4]
            dct[ 'proxy'] = PyTango.DeviceProxy( dct['motorName'])
            startPos = dct['proxy'].Position + float( lst[5])
            endPos   = dct['proxy'].Position + float(lst[6])
            dct[ 'targetPos'] = startPos + (endPos - startPos)*ratio
            argout.append( dct)
            dct = {}
            dct[ 'motorName'] = lst[7]
            dct[ 'proxy'] = PyTango.DeviceProxy( dct['motorName'])
            startPos = dct['proxy'].Position + float( lst[8])
            endPos   = dct['proxy'].Position + float(lst[9])
            dct[ 'targetPos'] = startPos + (endPos - startPos)*ratio
            argout.append( dct)
        else:
            return None
        return argout
        
    def run(self, mode, interactiveFlag):

        signalCounter = self.getEnv( "SignalCounter")
        result = "status=False"
        #
        # mvsa only for ascan, dscan, a2scan, d2scan
        #
        scanType = self.getEnv( "ScanHistory")[-1]['title'].split()[0]
        if not scanType.lower()  in ['ascan', 'dscan', 'a2scan', 'd2scan', 'a3scan', 'd3scan']:
            self.output( "mvsa: scanType %s not in ['ascan', 'dscan', 'a2scan', 'd2scan']" % scanType)
            return result

        fileName = self.getFullPathName()
        if fileName is None:
            self.output( "mvsa.run: terminated ")
            return result
        self.output( "mvsa.run: file %s " % fileName)
        a = HasyUtils.fioReader( fileName)

        message = 'undefined'
        flagFound = False
        for col in a.columns:
            if col.name == signalCounter:
                message, xpos, xpeak, xcms, xcen = HasyUtils.fastscananalysis( col.x, col.y, mode)
                if mode.lower() == 'show':
                    #
                    # par-3: flag-non-background-subtraction
                    #
                    ssaDct = HasyUtils.ssa( np.array(col.x), np.array(col.y), False)
                flagFound = True
                break

        if not flagFound:
            self.output( "Column %s not found in %s" % ( signalCounter, fileName))
            for col in a.columns:
                self.output( "%s" % col.name)
            return result

        if message != 'success':
            self.output( "mvsa: failed to find the maximum for %s" % ( a.fileName))
            self.output( "mvsa: reason %s" % ( message))
            return result

        if mode.lower() == 'show':
            self.output( "File name: %s " % fileName)
            self.output( "fsa: message %s" % (message))
            self.output( "fsa: xpos %g" % (xpos))
            self.output( "fsa: xpeak %g, cms %g cen  %g" % ( xpeak, xcms, xcen))
            self.output( "ssa: status %d, reason %d" % (ssaDct['status'], ssaDct['reason']))
            self.output( "ssa: xpeak %g, cms %g midp %g" % (ssaDct['peak_x'], ssaDct['cms'], ssaDct['midpoint']))
            self.output( "ssa: l_back %g, r_back %g" % (ssaDct['l_back'], ssaDct['r_back']))
            return result

        motorArr = self.getMotorInfo( xpos)
        if motorArr is None:
            return result
        #
        # prompt the user for confirmation, unless we have an uncoditional 'go'
        #
        if interactiveFlag == 1:
            self.output( "File name: %s " % fileName)
            for elm in motorArr:
                self.output( "Move %s from %g to %g" % ( elm[ 'motorName'], elm[ 'proxy'].Position, elm[ 'targetPos']))
            answer = self.input( "Exec move(s) [Y/N], def. 'N': ")
            if not (answer.lower() == "yes" or answer.lower() == "y"):
                self.output( "Motor(s) not moved!")
                return result

        for elm in ( motorArr):
            elm[ 'proxy'].write_attribute( "Position", elm[ 'targetPos'])
        moving = True
        while moving:
            moving = False
            for elm in ( motorArr):
                if elm[ 'proxy'].State() == PyTango.DevState.MOVING:
                    moving = True
                    break
            time.sleep( 0.1)
        result = "status=True"
        for elm in ( motorArr):
            self.output( "Motor %s is now at %g" % ( elm[ 'motorName'], elm[ 'proxy'].Position))
            result = result + ",%s=%s" % (elm[ 'motorName'], str(elm[ 'proxy'].Position))
        return result
