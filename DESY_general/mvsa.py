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
                                            supported: ascan, a2scan, a3scan, dscan, d2scan, d3scan, hscan, kscan, lscan, hklscan
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

    def run(self, mode, interactiveFlag):

        signalCounter = self.getEnv( "SignalCounter")
        result = "status=False"
        #
        # mvsa only for ascan, dscan, a2scan, d2scan
        #
        scanType = self.getEnv( "ScanHistory")[-1]['title'].split()[0]

        if not scanType.lower()  in ['ascan', 'dscan', 'a2scan', 'd2scan', 'a3scan', 'd3scan', 'hscan', 'kscan', 'lscan', 'hklscan']:
            self.output( "mvsa: scanType %s not in ['ascan', 'dscan', 'a2scan', 'd2scan', 'a3scan', 'd3scan', 'hscan', 'kscan', 'lscan', 'hklscan']" % scanType)
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

        self.scanInfo = HasyUtils.createScanInfo( self.getAllEnv())
        #
        # scanInfo:
        #{
        #  motors: [{'start': 0.0, 'stop': 0.1, 'name': 'e6cctrl_l', 'proxy': PseudoMotor(pm/e6cctrl/3)}],
        #  serialno: 1230,
        #  title: 'hscan 0.0 0.1 20 0.1",
        # }
        #
        motorArr = self.scanInfo['motors']
        if len( motorArr) == 0:
            self.output( "mvsa: len( motorArr) == 0, soemthing is wrong")
            return result
        #
        # xpos is the peak position w.r.t. the first motor. 
        # the ratio r is used to calculate the target positions
        # of the other motors
        #
        r = (xpos - motorArr[0]['start']) / \
            (motorArr[0]['stop'] - motorArr[0]['start']) 
            
        if len( motorArr) == 1:
            motorArr[0]['targetPos'] = xpos
        elif len( motorArr) == 2:
            motorArr[0]['targetPos'] = xpos
            motorArr[1]['targetPos'] = (motorArr[1]['stop'] - motorArr[1]['start'])*r + motorArr[1]['start']
        elif len( motorArr) == 3:
            motorArr[0]['targetPos'] = xpos
            motorArr[1]['targetPos'] = (motorArr[1]['stop'] - motorArr[1]['start'])*r + motorArr[1]['start']
            motorArr[2]['targetPos'] = (motorArr[2]['stop'] - motorArr[2]['start'])*r + motorArr[2]['start']
        else:
            return result
        #
        # prompt the user for confirmation, unless we have an uncoditional 'go'
        #
        if interactiveFlag == 1:
            self.output( "File name: %s " % fileName)
            for elm in motorArr:
                self.output( "Move %s from %g to %g" % ( elm[ 'name'], elm[ 'proxy'].Position, elm[ 'targetPos']))
            answer = self.input( "Exec move(s) [Y/N], def. 'N': ")
            if not (answer.lower() == "yes" or answer.lower() == "y"):
                self.output( "Motor(s) not moved!")
                return result
        #
        # start the move. for hklscans it is important to use 'br'. 
        # We must not start 'single' motors ( e.g.: e6cctrl_h) because
        # they are coupled.
        #
        if self.scanInfo['title'].find( 'hklscan') == 0:
            self.execMacro( "br %g %g %g" % ( motorArr[0]['targetPos'], 
                                              motorArr[1]['targetPos'], 
                                              motorArr[2]['targetPos']))
        else:
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
            self.output( "Motor %s is now at %g" % ( elm[ 'name'], elm[ 'proxy'].Position))
            result = result + ",%s=%s" % (elm[ 'name'], str(elm[ 'proxy'].Position))

        # self.output( "mvsa returns %s" % result)
        return result
