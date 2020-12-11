#!/usr/bin/env python
#
# version 30.9.2020
#
from sardana.macroserver.macro import Macro
from sardana.macroserver.macro import Type
import PyTango
import time
import numpy as np
import HasyUtils

class mvsa(Macro):
    """
    Moves a motor to the maximum of the column defined by SignalCounter.
    Data are fetched from SardanaMonitor, if it is running on the local host.
    Otherwise the most recent .fio output file is read.

    Used environment variables:
      ScanDir, ScanFile, ScanID  -> file name
      ScanHistory                -> motor name and scan type,
                                    supported: ascan, a2scan, a3scan, dscan, d2scan, d3scan, hscan, kscan, lscan, hklscan
      SignalCounter              -> counter name

      'mvsa show' shows the results, no move
"""
    param_def = [
        ['mode', Type.String  , 'peak', "Options: 'show','peak','cms','cen', 'dip','dipm','dipc', 'slit', 'slitm', 'slitc', 'step','stepm', 'stepc', 'stepssa' and '*ssa' in general"],
        ['interactiveFlag', Type.Integer , 1, " '1' query before move (def.) "],
    ]
    result_def = [[ "result", Type.String, None, "'status=False' or 'status=True,mot1=12,...'" ]]
    interactive = True

    def run(self, mode, interactiveFlag):
        #
        # the next line throws an exception, if SignalCounter does not exist,
        # so we don't have to check here
        #
        signalCounter = self.getEnv( "SignalCounter")
        result = "status=False"
        #
        # mvsa is restricted to certail scan types
        #
        scanType = self.getEnv( "ScanHistory")[-1]['title'].split()[0]

        supportedScanTypes = ['ascan', 'dscan', 'a2scan', 'd2scan', 'a3scan', 'd3scan',
                              'hscan', 'kscan', 'lscan', 'hklscan']
        if not scanType.lower() in supportedScanTypes:
            self.output( "mvsa: scanType %s not in %s" % (scanType, repr( supportedScanTypes)))
            return result

        self.scanInfo = HasyUtils.createScanInfo()
        if self.scanInfo is None:
            self.output( "mvsa: last scan aborted?")
            return result

        fileName = HasyUtils.getScanFileName()
        if fileName is None:
            self.output( "mvsa: fileName cannot be created")

        #
        # data from pyspMonitor or SardanaMonitor
        #
        message = 'undefined'
        flagDataFound = False
        flagDataFromMonitor = True
        toMonitorFunc = None
        isPysp = False
        if HasyUtils.isPyspMonitorAlive():
            toMonitorFunc = HasyUtils.toPyspMonitor
            isPysp = True
        elif HasyUtils.isSardanaMonitorAlive():
            toMonitorFunc = HasyUtils.toSardanaMonitor

        if toMonitorFunc is not None:
            hsh = toMonitorFunc( { 'getData': True})
            if hsh[ 'result'].upper() != 'DONE':
                self.output( "mvsa: monitor did not send DONE, instead: %s" % hsh[ 'result'])
                return result
            if len( hsh[ 'getData'].keys()) == 0:
                self.output( "mvsa: no data")
                return result
            if not signalCounter.upper() in hsh[ 'getData']:
                self.output( "mvsa: column %s is missing (from SM)" % signalCounter)
                return result
            flagDataFound = True
            #
            # try-except because npSig has been added, 21.09.2020
            #
            try:
                message, xpos, xpeak, xcms, xcen, npSig = HasyUtils.fastscananalysis( hsh[ 'getData'][ signalCounter.upper()][ 'x'],
                                                                                      hsh[ 'getData'][ signalCounter.upper()][ 'y'],
                                                                                      mode)
            except:
                npSig = 0
            if mode.lower() == 'show':
                #
                # par-3: flag-non-background-subtraction
                #
                ssaDct = HasyUtils.ssa( np.array( hsh[ 'getData'][ signalCounter.upper()][ 'x']),
                                        np.array(hsh[ 'getData'][ signalCounter.upper()][ 'y']), False)
        #
        # data from file
        #
        else:
            flagDataFromMonitor = False
            if fileName is None:
                self.output( "mvsa.run: terminated ")
                return result
            a = HasyUtils.fioReader( fileName)

            for col in a.columns:
                if col.name == signalCounter:
                    #
                    # try-except because npSig has been added, 21.09.2020
                    #
                    try:
                        message, xpos, xpeak, xcms, xcen, npSig = HasyUtils.fastscananalysis( col.x, col.y, mode)
                    except:
                        pass
                    if mode.lower() == 'show':
                        #
                        # par-3: flag-non-background-subtraction
                        #
                        ssaDct = HasyUtils.ssa( np.array(col.x), np.array(col.y), False)
                    flagDataFound = True
                    break

        if not flagDataFound:
            self.output( "Column %s not found in %s" % ( signalCounter, fileName))
            for col in a.columns:
                self.output( "%s" % col.name)
            return result

        if message != 'success':
            if toMonitorFunc is not None:
                self.output( "mvsa: failed to find the maximum, mode %s" % ( mode))
                self.output( "mvsa: fsa-reason %s" % ( message))
            else:
                self.output( "mvsa: failed to find the maximum for %s, mode %s" % ( fileName, mode))
                self.output( "mvsa: fsa-reason %s" % ( message))
            return result

        if mode.lower() == 'show':
            self.output( "mvsa: file name: %s " % fileName)
            self.output( "mvsa: dataFromSM %s" % repr( flagDataFromMonitor))
            self.output( "mvsa: message '%s'" % (message))
            self.output( "mvsa: xpos %g" % (xpos))
            self.output( "mvsa: xpeak %g, cms %g cen  %g" % ( xpeak, xcms, xcen))
            self.output( "mvsa: status %d, reason %d" % (ssaDct['status'], ssaDct['reason']))
            self.output( "mvsa(SSA): xpeak %g, cms %g midp %g" % (ssaDct['peak_x'], ssaDct['cms'], ssaDct['midpoint']))
            self.output( "mvsa(SSA): l_back %g, r_back %g    " % (ssaDct['l_back'], ssaDct['r_back']))
            return result
        #
        # scanInfo:
        # {
        #  motors: [{'start': 0.0, 'stop': 0.1, 'name': 'e6cctrl_l'}],
        #  serialno: 1230,
        #  title: 'hscan 0.0 0.1 20 0.1",
        # }
        #
        motorArr = self.scanInfo['motors']
        if len( motorArr) == 0:
            self.output( "mvsa: len( motorArr) == 0, something is wrong")
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
            motorArr[1]['targetPos'] = (motorArr[1]['stop'] - motorArr[1]['start']) * r + motorArr[1]['start']
        elif len( motorArr) == 3:
            motorArr[0]['targetPos'] = xpos
            motorArr[1]['targetPos'] = (motorArr[1]['stop'] - motorArr[1]['start']) * r + motorArr[1]['start']
            motorArr[2]['targetPos'] = (motorArr[2]['stop'] - motorArr[2]['start']) * r + motorArr[2]['start']
        else:
            return result
        #
        # prompt the user for confirmation, unless we have an uncoditional 'go'
        #
        if interactiveFlag == 1:
            if flagDataFromMonitor:
                self.output( "Scan name: %s, data from SM" % fileName)
            else:
                self.output( "File name: %s " % fileName)
            for elm in motorArr:
                p = PyTango.DeviceProxy( elm['name'])
                elm[ 'proxy'] = p
                self.output( "Move %s from %g to %g" % ( elm[ 'name'], p.Position, elm[ 'targetPos']))
            #
            # move the red arrow to the target position
            #
            if isPysp:
                toMonitorFunc( {'command': ['display %s' % signalCounter,
                                            'setArrowMisc %s position %g' %
                                            ( signalCounter, motorArr[0]['targetPos']),
                                            'setArrowMisc %s show' % signalCounter]})
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
                p = PyTango.DeviceProxy( elm['name'])
                p.write_attribute( "Position", elm[ 'targetPos'])
        moving = True
        while moving:
            moving = False
            for elm in ( motorArr):
                p = PyTango.DeviceProxy( elm['name'])
                if p.State() == PyTango.DevState.MOVING:
                    moving = True
                    break
            time.sleep( 0.1)
            # if isPysp:
            #    toMonitorFunc( {'command': ['setArrowCurrent %s position %g' % \
            #                                ( signalCounter, motorArr[0][ 'proxy'].position)]})
        result = "status=True"
        #
        # hide the misc arrow
        #
        if isPysp:
            toMonitorFunc( {'command': [ 'setArrowMisc %s hide' % signalCounter]})
        for elm in ( motorArr):
            p = PyTango.DeviceProxy( elm['name'])
            self.output( "Motor %s is now at %g" % ( elm[ 'name'], p.Position))
            result = result + ",%s=%s" % (elm[ 'name'], str(p.Position))

        # self.output( "mvsa returns %s" % result)
        return result


class createSaDct(Macro):
    """
    fill a dictionary, saDct, with the results from a fastscananalysis as used by mvsa.py
    the dictionary is stored in the MacroServer environment

      saDct                      -> the dictionary containing the results
        saDct[ 'fileName']              : using ScanDir, ScanFIle, ScanID
        saDct[ 'signalCounter']         : the signal counter
        saDct[ 'flagDataFromMonitor']   : if False, a .fio file hase been read
        saDct[ 'scanInfo']              : {'intervals': 49,
                                          'motors': [{'name': 'exp_dmy01',
                                          'start': 0.0,
                                          'stop': 10.0,
                                          'targetPos': 5.1020408163299997}],
                                          'sampleTime': 0.1,
                                          'serialno': 5704,
                                          'title': 'ascan exp_dmy01 0.0 10.0 49 0.1'}
        saDct[ 'message']              : 'success' or an error
        saDct[ 'dataX']                :
        saDct[ 'dataY']                :
        saDct[ 'npSig']                : points in the signal
          no. of pts with y >=  1/3*( yMax - yMin) + yMin  (peak, dip, step, slit)
        saDct[ 'npTotal']              :
        saDct[ 'mode']                 : peak, cms, cen, etc.
        saDct[ 'xpos']                 : xpos depends on mode
        saDct[ 'xpeak']                : xpeak
        saDct[ 'xcms']                 : cms
        saDct[ 'xcen']                 : center
      ScanDir, ScanFile, ScanID  -> file name
      ScanHistory                -> motor name and scan type,
                                    supported: ascan, a2scan, a3scan, dscan, d2scan, d3scan, hscan, kscan, lscan, hklscan
      SignalCounter              -> counter name


"""
    param_def = [
        ['mode', Type.String  , 'peak', "Options: 'peak','cms','cen', 'dip','dipm','dipc', 'slit', 'slitm', 'slitc', 'step','stepm', 'stepc', 'stepssa' and '*ssa' in general"]]
    result_def = [[ "result", Type.String, None, "'status=False' or 'status=True,mot1=12,...'" ]]
    interactive = True

    def run(self, mode):
        #
        # the next line throws an exception, if SignalCounter does not exist,
        # so we don't have to check here
        #
        signalCounter = self.getEnv( "SignalCounter")
        result = "status=False"
        #
        # createSaDct is restricted to certail scan types
        #
        scanType = self.getEnv( "ScanHistory")[-1]['title'].split()[0]

        supportedScanTypes = ['ascan', 'dscan', 'a2scan', 'd2scan', 'a3scan', 'd3scan',
                              'hscan', 'kscan', 'lscan', 'hklscan']
        if not scanType.lower() in supportedScanTypes:
            self.output( "createSaDct: scanType %s not in %s" % (scanType, repr( supportedScanTypes)))
            saDct = { 'message': "createSaDct: scanType %s not in %s" % (scanType, repr( supportedScanTypes))}
            self.setEnv( "saDct", saDct)
            return result

        self.scanInfo = HasyUtils.createScanInfo()
        if self.scanInfo is None:
            self.output( "createSaDct: last scan aborted?")
            saDct = { 'message': 'last scan aborted?'}
            self.setEnv( "saDct", saDct)
            return result

        fileName = HasyUtils.getScanFileName()
        if fileName is None:
            self.output( "createSaDct: failed to getScanFileName")
            saDct = { 'message': 'failed to getScanFileName'}
            self.setEnv( "saDct", saDct)
            return result

        #
        # data from pyspMonitor or SardanaMonitor
        #
        message = 'undefined'
        flagDataFound = False
        flagDataFromMonitor = True
        toMonitorFunc = None
        if HasyUtils.isPyspMonitorAlive():
            toMonitorFunc = HasyUtils.toPyspMonitor
        elif HasyUtils.isSardanaMonitorAlive():
            toMonitorFunc = HasyUtils.toSardanaMonitor
        #
        # data from monitor
        #
        if toMonitorFunc is not None:
            hsh = toMonitorFunc( { 'getData': True})
            if hsh[ 'result'].upper() != 'DONE':
                self.output( "createSaDct: monitor did not send DONE, instead: %s" % hsh[ 'result'])
                saDct = { 'message': "createSaDct: monitor did not send DONE, instead: %s" % hsh[ 'result']}
                self.setEnv( "saDct", saDct)
                return result
            if len( hsh[ 'getData'].keys()) == 0:
                self.output( "createSaDct: no data")
                saDct = { 'message': "no data"}
                self.setEnv( "saDct", saDct)
                return result
            if not signalCounter.upper() in hsh[ 'getData']:
                self.output( "createSaDct: column %s is missing (from SM)" % signalCounter)
                saDct = { 'message': "createSaDct: column %s is missing (from SM)" % signalCounter}
                self.setEnv( "saDct", saDct)
                return result
            flagDataFound = True
            dataX = hsh[ 'getData'][ signalCounter.upper()][ 'x']
            dataY = hsh[ 'getData'][ signalCounter.upper()][ 'y']
        #
        # data from file
        #
        else:
            flagDataFromMonitor = False
            a = HasyUtils.fioReader( fileName)

            for col in a.columns:
                if col.name == signalCounter:
                    dataX = col.x
                    dataY = col.y
                    flagDataFound = True
                    break

        if not flagDataFound:
            self.output( "createSaDct: column %s not found in %s" % ( signalCounter, fileName))
            saDct = { 'message': "createSaDct: column %s not found in %s" % ( signalCounter, fileName)}
            self.setEnv( "saDct", saDct)
            return result

        message, xpos, xpeak, xcms, xcen, npSig = HasyUtils.fastscananalysis( dataX, dataY, mode)

        if message != 'success':
            if toMonitorFunc is not None:
                self.output( "createSaDct: failed to find the maximum, mode %s " % mode)
                self.output( "             reason: %s" % ( message))
                saDct = { 'message': "createSaDct: failed to find the maximum reason: %s, mode %s" % ( message, mode)}
            else:
                self.output( "createSaDct: failed to find the maximum for %s" % ( fileName))
                self.output( "             reason %s" % ( message))
                saDct = { 'message': "createSaDct: failed to find the maximum for %s, reason %s, mode %s" % ( fileName, message, mode)}
            self.setEnv( "saDct", saDct)
            return result

        saDct = {}
        saDct[ 'fileName'] = fileName
        saDct[ 'signalCounter'] = signalCounter
        saDct[ 'flagDataFromMonitor'] = flagDataFromMonitor
        saDct[ 'scanInfo'] = dict( self.scanInfo)
        saDct[ 'message'] = message
        saDct[ 'xData'] = dataX[:]
        saDct[ 'yData'] = dataY[:]
        saDct[ 'yMin'] = min( dataY)
        saDct[ 'yMax'] = max( dataY)
        saDct[ 'npSig'] = npSig
        saDct[ 'npTotal'] = len( dataX)
        saDct[ 'mode'] = mode
        saDct[ 'xpos'] = float( xpos)
        if mode.lower() in [ 'dip', 'dipc', 'dipm']:
            saDct[ 'xdip'] = float(xpeak)
            saDct[ 'xdipm'] = float(xcms)
            saDct[ 'xdipc'] = float(xcen)
        elif mode.lower() in [ 'dipssa', 'dipcssa', 'dipmssa']:
            saDct[ 'xdipssa'] = float(xpeak)
            saDct[ 'xdipmssa'] = float(xcms)
            saDct[ 'xdipcssa'] = float(xcen)
        elif mode.lower() in [ 'step', 'stepc', 'stepm']:
            saDct[ 'xstep'] = float(xpeak)
            saDct[ 'xstepm'] = float(xcms)
            saDct[ 'xstepc'] = float(xcen)
        elif mode.lower() in [ 'stepssa', 'stepcssa', 'stepmssa']:
            saDct[ 'xstepssa'] = float(xpeak)
            saDct[ 'xstepmssa'] = float(xcms)
            saDct[ 'xstepcssa'] = float(xcen)
        elif mode.lower() in [ 'slit', 'slitc', 'slitm']:
            saDct[ 'xslit'] = float(xpeak)
            saDct[ 'xslitm'] = float(xcms)
            saDct[ 'xslitc'] = float(xcen)
        elif mode.lower() in [ 'slitssa', 'slitcssa', 'slitmssa']:
            saDct[ 'xslitssa'] = float(xpeak)
            saDct[ 'xslitmssa'] = float(xcms)
            saDct[ 'xslitcssa'] = float(xcen)
        elif mode.lower() in [ 'peak', 'cms', 'cen']:
            saDct[ 'xpeak'] = float(xpeak)
            saDct[ 'xcms'] = float(xcms)
            saDct[ 'xcen'] = float(xcen)
        elif mode.lower() in [ 'peakssa', 'cmsssa', 'censsa']:
            saDct[ 'xpeakssa'] = float(xpeak)
            saDct[ 'xcmsssa'] = float(xcms)
            saDct[ 'xcenssa'] = float(xcen)
        else:
            self.output( "createSaDct: Mode %s wronmg" % mode)
            return
        #
        # scanInfo:
        # {
        #  motors: [{'start': 0.0, 'stop': 0.1, 'name': 'e6cctrl_l'}],
        #  serialno: 1230,
        #  title: 'hscan 0.0 0.1 20 0.1",
        # }
        #
        motorArr = self.scanInfo['motors']
        if len( motorArr) == 0:
            self.output( "createSaDct: len( motorArr) == 0, something is wrong")
            saDct = { 'message': "createSaDct: len( motorArr) == 0, something is wrong"}
            self.setEnv( "saDct", saDct)
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
            motorArr[1]['targetPos'] = (motorArr[1]['stop'] - motorArr[1]['start']) * r + motorArr[1]['start']
        elif len( motorArr) == 3:
            motorArr[0]['targetPos'] = xpos
            motorArr[1]['targetPos'] = (motorArr[1]['stop'] - motorArr[1]['start']) * r + motorArr[1]['start']
            motorArr[2]['targetPos'] = (motorArr[2]['stop'] - motorArr[2]['start']) * r + motorArr[2]['start']
        else:
            self.output( "createSaDct: error, more than 3 motors")
            saDct = { 'message': "createSaDct: more than 3 motors"}
            self.setEnv( "saDct", saDct)
            return result

        saDct[ 'motorArr'] = motorArr[:]

        self.setEnv( "saDct", saDct)
        result = "status=True"
        return result
