# #############################################################################
#
# This file is part of Sardana
#
# http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
#
# Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
#
# Sardana is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sardana is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Sardana.  If not, see <http://www.gnu.org/licenses/>.
#
# #############################################################################

"""
    Macro library for performing continuous scans taking Lambda images
    synchronized with analog and digital PiLC readings.
    Synchronization is achieved by a
    TriggerGenerator PiLC.
"""
import PyTango
from sardana.macroserver.macro import Macro, Type
import time

__all__ = ['cscan_pilc_lambda', 'cscan_pilc_lambda_senv']

__docformat__ = 'restructuredtext'


class cscan_pilc_lambda(Macro):
    """ Performs a continuous scan taking Lambda images
        synchronized with analog and digital PiLC readings.
    """

    env = ('LambdaDevice', 'PiLCTriggerGeneratorDevice',
           'PiLCDigitalSlaveDevice', 'PiLCAnalogSlaveDevice',
           'ScanDir', 'ScanFile')

    param_def = [
        ['nb_frames', Type.Integer, None,
         'Number of Lambda frames to be taken'],
        ['exp_time', Type.Float, None, 'Exposure time (s)']
    ]

    def run(self, nb_frames, exp_time):

        LAMBDA_TO_BECOME_MOVING = 0.5   # secs

        # creates the proxies
        proxyTG_name = self.getEnv('PiLCTriggerGeneratorDevice')
        proxyTG = PyTango.DeviceProxy(proxyTG_name)
        proxyAS_name = self.getEnv('PiLCAnalogSlaveDevice')
        proxyAS = PyTango.DeviceProxy(proxyAS_name)
        proxyDS_name = self.getEnv('PiLCDigitalSlaveDevice')
        proxyDS = PyTango.DeviceProxy(proxyDS_name)
        proxyLambda_name = self.getEnv('PiLCLambdaDevice')
        proxyLambda = PyTango.DeviceProxy(proxyLambda_name)

        # check states == ON

        msg = ""
        if proxyTG.state() != PyTango.DevState.ON:
            msg = msg + "\n" + (
                "%s is in state %s"
                % (self.proxyTG.name(), self.proxyTG.state()))
        if proxyAS.state() != PyTango.DevState.ON:
            msg = msg + "\n" + (
                "%s is in state %s"
                % (self.proxyAS.name(), self.proxyAS.state()))
        if proxyDS.state() != PyTango.DevState.ON:
            msg = msg + "\n" + (
                "%s is in state %s"
                % (self.proxyDS.name(), self.proxyDS.state()))
        if proxyLambda.state() != PyTango.DevState.ON:
            msg = msg + "\n" + (
                "%s is in state %s"
                % (self.proxyLambda.name(), self.proxyLambda.state()))
        if msg != "":
            self.error(msg)
            return

        # check if slaves are connected

        msg = ""
        if proxyAS.PiLCTGConnected != 1:
            msg = msg + "\n" + \
                ("%s PiLCTGConnected != 1" % self.proxyAS.name())
        if self.proxyDS.PiLCTGConnected != 1:
            msg = msg + "\n" + \
                ("%s PiLCTGConnected != 1" % self.proxyDS.name())
        if msg != "":
            self.error(msg)
            return

        # ## Configure devices ###

        scanDir = self.getEnv('ScanDir')
        scanFile = self.getEnv('ScanFile')

        # set trigger generator attributes

        proxyTG.FileDir = scanDir
        proxyTG.FilePrefix = "%s_TG" % scanFile
        proxyTG.NbTriggers = nb_frames
        proxyTG.TimeTriggerStart = 0    # no delay
        proxyTG.TimeTriggerStepSize = exp_time
        proxyTG.TriggerPulseLength = exp_time
        proxyTG.TriggerMode = 2    # time

        # set analog slave attributes

        proxyAS.FileDir = scanDir
        proxyAS.FilePrefix = "%s_AS" % scanFile
        proxyAS.ManualMode = 0

        # set digital slave attributes

        proxyDS.FileDir = scanDir
        proxyDS.FilePrefix = "%s_DS" % scanFile
        proxyDS.ManualMode = 0

        # set Lambda attributes

        proxyLambda.SaveFilePath = scanDir
        proxyLambda.FilePrefix = "%s_Lambda" % scanFile
        proxyLambda.AppendData = True
        proxyLambda.PrecompressEnabled = True
        proxyLambda.FrameNumbers = nb_frames
        proxyLambda.FramesPerFile = nb_frames
        proxyLambda.OperatingMode = "TwentyFourBit"
        proxyLambda.ShutterTime = int(exp_time * 1000. - 1.)
        proxyLambda.TriggerMode = 2   # external trigger

        # ## Start scan ###

        proxyLambda.StartAcq()

        self.output("Lambda acquisition started")

        startTime = time.time()
        while proxyLambda.state() != PyTango.DevState.MOVING:
            time.sleep(0.01)
            if (time.time() - startTime) > LAMBDA_TO_BECOME_MOVING:
                self.error("Lambda does not become MOVING")
                return

        time.sleep(0.1)
        proxyTG.write_attribute("Arm", 1)

        self.output("Triggergenerator armed")

        totalTime = nb_frames * exp_time
        updateTime = 1
        if totalTime < 2.0:
            updateTime = 0.1
        startTime = time.time()
        while proxyTG.state() != PyTango.DevState.ON:
            time.sleep(updateTime)
            self.output(
                "%.4g/%gs: remaining triggers %d"
                % (time.time() - startTime, totalTime,
                   proxyTG.RemainingTriggers))
            if (time.time() - startTime) > (totalTime + 1):
                self.error("elapsed time exceeds total time")
                return


class cscan_pilc_lambda_senv(Macro):
    """ Sets default environment variables """

    def run(self):
        self.setEnv("LambdaDevice", "hasep23oh:10000/p23/lambda/01")
        self.setEnv("PiLCTriggerGeneratorDevice",
                    "hasep23oh:10000/p23/pilctriggergenerator/dev.01")
        self.setEnv("PiLCDigitalSlaveDevice",
                    "hasep23oh:10000/p23/pilcscanslave/exp.03")
        self.setEnv("PiLCAnalogSlaveDevice",
                    "hasep23oh:10000/p23/pilcscanslave/exp.04")
