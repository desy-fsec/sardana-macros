#!/usr/bin/env python
#
from sardana.macroserver.macro import Macro
from sardana.macroserver.macro import Type
import HasyUtils
import PyTango
import time
import math

__all__ = ["GalilRS"]


class GalilRS(Macro):
    """
    Resets GalilMotors
    - the current motor positions are stored, opMode: -x
    - the macro sends a RS (reset) to the Galil controller
    - the macro waits for the motors to reach their final positions
    - finally motors are moved to their original positions, opMode: -x

    The -f option resets the device ignoring the initial positions. This
    option is intended to be used, if the positions cannot be read out.

    The positions to be reached after RS are hard coded for each BL
      haspp09: abs(pos) == 5
    """

    result_def = [['result', Type.Boolean, None, 'GalilRS return status']]
    param_def = [['opMode', Type.String, None,
                  '-x execute, -f forced, execute ignoring curr positions']]

    def run(self, opMode):
        #
        # check the opMode parameter
        #
        if opMode != '-x' and opMode != '-f':
            self.output("GalilRS: use '-x' or '-f'")
            return True
        #
        # posPowerOn is used to sense that the RS procedure is completed
        #
        posPowerOn = 5
        if HasyUtils.getHostname() == 'haspp09':
            posPowerOn = 5
        else:
            self.output("GalilRS: failed recognize the experiment")
            return False

        galilCtrl = HasyUtils.getDeviceNamesByClass('GalilDMCCtrl')
        try:
            galilCtrlProxy = PyTango.DeviceProxy(galilCtrl[0])
        except:
            self.output("GalilRS failed to create proxy to %s" %
                        galilCtrl[0])
            return False

        galilMotors = HasyUtils.getDeviceNamesByClass('GalilDMCMotor')

        #
        # store current positions
        #
        dct = {}
        galilCtrlProxy.ReadAllRemaining()
        if opMode == '-f':
            self.output("GalilRS: ignoring initial positions")
        for elm in galilMotors:
            dct[elm] = {}
            try:
                dct[elm]['proxy'] = PyTango.DeviceProxy(elm)
            except:
                self.output("GalilRS failed to create proxy to %s" % elm)
                return False
            if opMode != '-f':
                retryCount = 0
                while retryCount < 2:
                    try:
                        dct[elm]['position'] = dct[elm]['proxy'].Position
                        break
                    except:
                        self.output("GalilRS failed to read Position of %s" %
                                    elm)
                        retryCount += 1
                else:
                    self.output("GalilRS: tried to read %s \
position %d times, failed" % elm)
                    self.output("GalilRS: consider to use '-f' option")
                    return False
                self.output("GalilRS: %s is at %g (old position)" %
                            (elm, dct[elm]['position']))
        #
        # send 'RS' (reset) and wait for motors to stop moving
        #
        self.output("GalilRS: sending RS")
        galilCtrlProxy.Write_read("RS")
        time.sleep(3)

        while 1:
            moving = False
            for elm in galilMotors:
                pos = dct[elm]['proxy'].Position
                galilCtrlProxy.ReadAllRemaining()
                self.output("GalilRS: %s is at %g (target: abs(pos) == %g)" %
                            (elm, pos, posPowerOn))
                if math.fabs(posPowerOn - math.fabs(pos)) > 0.1:
                    moving = True
                    break
            if moving is False:
                break
            time.sleep(2)
        galilCtrlProxy.ReadAllRemaining()
        #
        # -f means that the initial positions are ignored
        #
        if opMode != '-f':
            #
            # move to old positions
            #
            for elm in galilMotors:
                if dct[elm]['position'] > dct[elm]['proxy'].UnitLimitMax:
                    dct[elm]['proxy'].Position = dct[elm]['proxy'].UnitLimitMax
                elif dct[elm]['position'] < dct[elm]['proxy'].UnitLimitMin:
                    dct[elm]['proxy'].Position = dct[elm]['proxy'].UnitLimitMin
                else:
                    dct[elm]['proxy'].Position = dct[elm]['position']
                self.output("GalilRS: started %s to %g" %
                            (elm, dct[elm]['position']))
                while 1:
                    pos = dct[elm]['proxy'].Position
                    self.output("GalilRS: %s is at %g (target: %g) " %
                                (elm, pos, dct[elm]['position']))
                    if math.fabs(math.fabs(
                            dct[elm]['position']) - math.fabs(pos)) < 0.1:
                        break
                    time.sleep(1)

        self.output("")
        for elm in galilMotors:
            pos = dct[elm]['proxy'].Position
            self.output("GalilRS: %s finally at %g" % (elm, pos))

        return True
