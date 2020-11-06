#!/usr/bin/env python
#
#
from sardana.macroserver.macro import *
from sardana.macroserver.macro import macro
import PyTango
import time
import numpy as np
import HasyUtils
import PySpectra
import PySpectra.calc as calc

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
        ['mode', Type.String, 'peak', "Options: 'show','peak','cms','cen','dip','dipm','dipc','slit', 'slitm', 'slitc', 'step','stepm' and 'stepc', 'stepssa', 'stepcssa', 'stepmssa'"],
        ['interactiveFlag', Type.Integer, 1, " '1' query before move (def.) "],
        ]
    result_def = [["result", Type.String, None, "'status=False' or 'status=True,mot1=12,...'" ]]
    interactive = True

    def run(self, mode, interactiveFlag):
        #
        # the next line throws an exception, if SignalCounter does not exist,
        # so we don't have to check here
        #
        signalCounter = self.getEnv("SignalCounter")
        result = "status=False"
        #
        # mvsa is restricted to certail scan types
        #
        scanType = self.getEnv("ScanHistory")[-1]['title'].split()[0]

        supportedScanTypes = ['ascan', 'dscan', 'a2scan', 'd2scan', 'a3scan', 'd3scan',
                              'hscan', 'kscan', 'lscan', 'hklscan']
        if not scanType.lower()  in supportedScanTypes:
            self.output("mvsa: scanType %s not in %s" % (scanType, repr(supportedScanTypes)))
            return result

        self.scanInfo = HasyUtils.createScanInfo()
        if self.scanInfo is None:
            self.output("mvsa: last scan aborted?")
            return result

        fileName = HasyUtils.getScanFileName()
        if fileName is None:
            self.output("mvsa: fileName cannot be created")

        #
        # data from pyspMonitor or SardanaMonitor
        #
        message = 'undefined'
        flagDataFound = False
        flagDataFromMonitor = True
        toMonitorFunc = None
        fsaFunc = None
        isPysp = False
        if PySpectra.isPyspMonitorAlive():
            toMonitorFunc = PySpectra.toPyspMonitor
            isPysp = True
        elif HasyUtils.isSardanaMonitorAlive():
            toMonitorFunc = HasyUtils.toSardanaMonitor

        if toMonitorFunc is not None:
            hsh = toMonitorFunc({ 'getData': True})
            if hsh['result'].upper() != 'DONE':
                self.output("mvsa: SardanaMonitor did not send DONE, instead: %s" % hsh['result'])
                return result
            if len(hsh['getData'].keys()) == 0:
                self.output("mvsa: no data")
                return result
            if not hsh['getData'].has_key(signalCounter.upper()):
                self.output("mvsa: column %s is missing (from SM)" % signalCounter)
                return result
            flagDataFound = True
            message, xpos, xpeak, xcms, xcen = calc.fastscananalysis(hsh['getData'][signalCounter.upper()]['x'],
                                                                      hsh['getData'][signalCounter.upper()]['y'],
                                                                      mode)
            if mode.lower() == 'show':
                #
                # par-3: flag-non-background-subtraction
                #
                ssaDct = calc.ssa(np.array(hsh['getData'][signalCounter.upper()]['x']),
                                     np.array(hsh['getData'][signalCounter.upper()]['y']), False)
        #
        # data from file
        #
        else:
            flagDataFromMonitor = False
            if fileName is None:
                self.output("mvsa.run: terminated ")
                return result
            a = HasyUtils.fioReader(fileName)

            for col in a.columns:
                if col.name == signalCounter:
                    message, xpos, xpeak, xcms, xcen = calc.fastscananalysis(col.x, col.y, mode)
                    if mode.lower() == 'show':
                        #
                        # par-3: flag-non-background-subtraction
                        #
                        ssaDct = calc.ssa(np.array(col.x), np.array(col.y), False)
                    flagDataFound = True
                    break

        if not flagDataFound:
            self.output("Column %s not found in %s" % (signalCounter, fileName))
            for col in a.columns:
                self.output("%s" % col.name)
            return result

        if message != 'success':
            self.output("mvsa: failed to find the maximum for %s" % (fileName))
            self.output("mvsa: reason %s" % (message))
            return result

        if mode.lower() == 'show':
            self.output("mvsa: file name: %s " % fileName)
            self.output("mvsa: dataFromSM %s" % repr(flagDataFromMonitor))
            self.output("mvsa: message '%s'" % (message))
            self.output("mvsa: xpos %g" % (xpos))
            self.output("mvsa: xpeak %g, cms %g cen  %g" % (xpeak, xcms, xcen))
            self.output("mvsa: status %d, reason %d" % (ssaDct['status'], ssaDct['reason']))
            self.output("mvsa: xpeak %g, cms %g midp %g" % (ssaDct['peak_x'], ssaDct['cms'], ssaDct['midpoint']))
            self.output("mvsa: l_back %g, r_back %g" % (ssaDct['l_back'], ssaDct['r_back']))
            return result
        #
        # scanInfo:
        #{
        #  motors: [{'start': 0.0, 'stop': 0.1, 'name': 'e6cctrl_l'}],
        #  serialno: 1230,
        #  title: 'hscan 0.0 0.1 20 0.1",
        # }
        #
        motorArr = self.scanInfo['motors']
        if len(motorArr) == 0:
            self.output("mvsa: len(motorArr) == 0, something is wrong")
            return result
        #
        # xpos is the peak position w.r.t. the first motor.
        # the ratio r is used to calculate the target positions
        # of the other motors
        #
        r = (xpos - motorArr[0]['start']) / \
            (motorArr[0]['stop'] - motorArr[0]['start'])

        if len(motorArr) == 1:
            motorArr[0]['targetPos'] = xpos
        elif len(motorArr) == 2:
            motorArr[0]['targetPos'] = xpos
            motorArr[1]['targetPos'] = (motorArr[1]['stop'] - motorArr[1]['start'])*r + motorArr[1]['start']
        elif len(motorArr) == 3:
            motorArr[0]['targetPos'] = xpos
            motorArr[1]['targetPos'] = (motorArr[1]['stop'] - motorArr[1]['start'])*r + motorArr[1]['start']
            motorArr[2]['targetPos'] = (motorArr[2]['stop'] - motorArr[2]['start'])*r + motorArr[2]['start']
        else:
            return result
        #
        # prompt the user for confirmation, unless we have an uncoditional 'go'
        #
        posStart = None
        if interactiveFlag == 1:
            if flagDataFromMonitor:
                self.output("Scan name: %s, data from SM" % fileName)
            else:
                self.output("File name: %s " % fileName)
            for elm in motorArr:
                p = PyTango.DeviceProxy(elm['name'])
                elm['proxy'] = p
                self.output("Move %s from %g to %g" % (elm['name'], p.Position, elm['targetPos']))
            posStart = motorArr[0]['proxy'].position
            #
            # move the red arrow to the target position
            #
            if isPysp:
                toMonitorFunc({'command': ['display %s' % signalCounter,
                                            'setArrowMisc %s position %g' % \
                                            (signalCounter, motorArr[0]['targetPos']),
                                            'setArrowMisc %s show' % signalCounter,
                ]})
            answer = self.input("Exec move(s) [Y/N], def. 'N': ")
            if not (answer.lower() == "yes" or answer.lower() == "y"):
                self.output("Motor(s) not moved!")
                return result
        #
        # start the move. for hklscans it is important to use 'br'.
        # We must not start 'single' motors (e.g.: e6cctrl_h) because
        # they are coupled.
        #
        if self.scanInfo['title'].find('hklscan') == 0:
            self.execMacro("br %g %g %g" % (motorArr[0]['targetPos'],
                                              motorArr[1]['targetPos'],
                                              motorArr[2]['targetPos']))
        else:
            for elm in (motorArr):
                p = PyTango.DeviceProxy(elm['name'])
                p.write_attribute("Position", elm['targetPos'])
        moving = True
        while moving:
            moving = False
            for elm in (motorArr):
                p = PyTango.DeviceProxy(elm['name'])
                if p.State() == PyTango.DevState.MOVING:
                    moving = True
                    break
            time.sleep(0.1)
            #if isPysp:
            #    toMonitorFunc({'command': ['setArrowCurrent %s position %g' % \
            #                                (signalCounter, motorArr[0]['proxy'].position)]})
        result = "status=True"
        #
        # hide the misc arrow
        #
        if isPysp:
            toMonitorFunc({'command': ['setArrowMisc %s hide' % signalCounter]})
        for elm in (motorArr):
            p = PyTango.DeviceProxy(elm['name'])
            self.output("Motor %s is now at %g" % (elm['name'], p.Position))
            result = result + ",%s=%s" % (elm['name'], str(p.Position))

        # self.output("mvsa returns %s" % result)
        return result
