#!/usr/bin/env python

"""pilc triggered continuous scan macros"""

import PyTango
from sardana.macroserver.macro import Type, Macro
# from sardana.macroserver.macro import macro
import json
import time
import pytz
import datetime
# import numpy


__all__ = ["cscan_pilc_sis3820mcs", "cscan_pilc_xia",
           "c2dscan_pilc_sis3820mcs_postrigger",
           "cscan_pilc_senv"]

class cscan_pilc_sis3820mcs(Macro):
    """Perfoms a continuous scan with the pilc triggering the sis3820"""

    param_def = [
        ['motor', Type.Motor, None, 'Motor to move'],
        ['start_pos', Type.Float, None, 'Scan start position'],
        ['final_pos', Type.Float, None, 'Scan final position'],
        ['nb_triggers', Type.Integer, None,
         'Nb of triggers generated by the pilc'],
        ['trigger_interval', Type.Float, None,
         'Time or position units between consecutive triggers'],
        ['trigger_mode', Type.Integer, 3,
         'Trigger mode: 1 pos, 2 time, 3 pos-time, 4 time-pos']
    ]

    result_def = [["result", Type.String, None, "the cscan object"]]

    def run(self, motor, start_pos, final_pos, nb_triggers, trigger_interval,
            trigger_mode):

        pilctg_device_name = self.getEnv('PiLCTGDevice')
        self.output("Using PiLCTriggerGenerator device " + pilctg_device_name)
        mcs_device_name = self.getEnv('MCSDevice')
        self.output("Using SIS3820MCS device " + mcs_device_name)

        # nexusconfig_device_name = self.getEnv('NeXusConfigDevice')
        # # class XMLConfigServer
        # nexuswriter_device_name = self.getEnv('NeXusWriterDevice')
        # # class TangoDataServer

        pilctg_device = PyTango.DeviceProxy(pilctg_device_name)
        mcs_device = PyTango.DeviceProxy(mcs_device_name)

        motor_device = PyTango.DeviceProxy(motor.getName())

        # self.nexusconfig_device = PyTango.DeviceProxy(
        #     nexusconfig_device_name)
        # self.nexuswriter_device = PyTango.DeviceProxy(
        #     nexuswriter_device_name)

        # self._openNxFile()

        # Set the PiLCTriggerGenerator device

        # ###

        pilctg_device.TriggerMode = trigger_mode

        # always smaller als trigger_interval
        pilctg_device.TriggerPulseLength = 0.00001

        if trigger_mode == 1:
            pilctg_device.PositionTriggerStart = start_pos
            # position units between triggers
            pilctg_device.PositionTriggerStepSize = trigger_interval
        elif trigger_mode == 2:
            # start triggering directly after Arm is set to 1
            pilctg_device.TimeTriggerStart = 0
            # time for counting
            pilctg_device.TimeTriggerStepSize = trigger_interval
        elif trigger_mode == 3:
            pilctg_device.PositionTriggerStart = start_pos
            # time for counting
            pilctg_device.TimeTriggerStepSize = trigger_interval
        elif trigger_mode == 4:
            pilctg_device.TimeTriggerStart = 0
            # position units between triggers
            pilctg_device.PositionTriggerStepSize = trigger_interval
        else:
            self.warning("Wrong trigger mode. Exit")
            result = "Not run"
            return result

        pilctg_device.NbTriggers = nb_triggers

        # Set MCS

        mcs_device.NbAcquisitions = 0  # Continuous mode
        mcs_device.NbChannels = 2      # Set two channels
        mcs_device.Preset = 1          # every trigger is used

        # nb_mcs_taken_triggers =
        nb_triggers

        # Compute motor slewrate for the continuous scan

        # old_slewrate = motor_device.Velocity

        # scan_slewrate = abs(final_pos - start_pos)
        #          /(trigger_interval * (nb_triggers - 1))

        # motor_device.Velocity = scan_slewrate

        # Move motor to start position minus an offset

        if start_pos < final_pos:
            pos_offset = 0.1
        else:
            pos_offset = -0.1

        motor_device.Position = start_pos - pos_offset

        while motor_device.State() == PyTango.DevState.MOVING:
            time.sleep(1)

        if trigger_mode == 2 or trigger_mode == 4:
            # Start motor movement to final position
            # (the macro mv can not be used because it blocks)
            motor_device.Position = final_pos + pos_offset

            # Check when the motor is in the start_position
            #  for starting the trigger

            while motor_device.Position < start_pos:
                time.sleep(0.001)

            # Store starttime

            amsterdam = pytz.timezone('Europe/Amsterdam')
            self.starttime = amsterdam.localize(datetime.datetime.now())

            # Clear and setup mcs

            mcs_device.ClearSetupMCS()

            # Start pilc triggering

            pilctg_device.Arm = 1

        elif trigger_mode == 1 or trigger_mode == 3:
            # Store starttime

            amsterdam = pytz.timezone('Europe/Amsterdam')
            self.starttime = amsterdam.localize(datetime.datetime.now())

            # Clear and setup mcs

            mcs_device.ClearSetupMCS()

            # Start pilc triggering

            pilctg_device.Arm = 1

            # Start motor movement to final position
            # (the macro mv can not be used because it blocks)
            motor_device.Position = final_pos + pos_offset

            # Check when the triggering is done

        while pilctg_device.State() == PyTango.DevState.MOVING:
            time.sleep(1)

        # Read MCS

        mcs_device.ReadMCS()

        # Reset motor slewrate

        # motor_device.Velocity = old_slewrate

        # MCS Data

        # nb_mcs_taken_triggers =
        mcs_device.AcquiredTriggers
        # nb_mcs_channels =
        mcs_device.NbChannels
        # mcs_data =
        mcs_device.CountsArray

        # PiLC Data

        # pilcencoder_data =
        pilctg_device.EncoderData
        # pilccounter_data =
        pilctg_device.CounterData

        # Open the nexus file for saving data

        # self._openNxFile()
        # self._openNxEntry(motor.getName(), start_pos,
        # final_pos, nb_triggers, trigger_interval, nb_xia_channels)

        # Close NeXus file

        # self._closeNxEntry()
        # self._closeNxFile()

        result = "Scan ended sucessfully"
        return result

    def _openNxFile(self):
        cscan_id = self.getEnv('CScanID')
        fileNameNx = self.getEnv('CScanFileName') + "_" + str(cscan_id) + ".h5"
        self.setEnv("CScanID", cscan_id + 1)
        self.nexuswriter_device.Init()
        self.nexuswriter_device.FileName = str(fileNameNx)
        self.nexuswriter_device.OpenFile()
        return 1

    def _openNxEntry(
            self, motor_name, start_pos, final_pos, nb_triggers,
            trigger_interval, xia_spec_length):

        self._sendGlobalDictionaryBefore(
            motor_name, start_pos, final_pos, nb_triggers, trigger_interval,
            xia_spec_length)

        self.nexusconfig_device.Open()
        cmps = self.nexusconfig_device.AvailableComponents()
        cmp_list = []
        if "zebra_init" not in cmps:
            self.output("_openNxEntry: zebra not in configuration server")
        else:
            cmp_list.append("zebra_init")

        # Add component for the XIA.

        if "xia_init" not in cmps:
            self.output("_openNxEntry: xia not in configuration server")
        else:
            cmp_list.append("xia_init")

        # Add the default component

        if "default" not in cmps:
            self.output("_openNxEntry: default not in configuration server")
        else:
            cmp_list.append("default")

        self.nexusconfig_device.CreateConfiguration(cmp_list)
        xmlconfig = self.nexusconfig_device.XMLString
        self.nexuswriter_device.XMLSettings = str(xmlconfig)
        #        try:
        #            self.nexuswriter_device.OpenEntry()
        #        except Exception:
        #            pass

        try:
            self.nexuswriter_device.OpenEntryAsynch()
        except Exception:
            pass

        while self.nexuswriter_device.State() == PyTango.DevState.RUNNING:
            time.sleep(0.01)

        return 1

    def _closeNxFile(self):
        self._sendGlobalDictionaryAfter()
        self.nexuswriter_device.CloseEntry()
        return 1

    def _closeNxEntry(self):
        return 1

    def _sendGlobalDictionaryBefore(
            self, motor_name, start_pos, final_pos,
            nb_triggers, trigger_interval, xia_spec_length):
        hsh = {}
        hshSub = {}
        hshSub['motor_name'] = str(motor_name)
        hshSub['start_pos'] = start_pos
        hshSub['final_pos'] = final_pos
        hshSub['nb_triggers'] = nb_triggers
        hshSub['sample_time'] = trigger_interval
        fmt = '%Y-%m-%dT%H:%M:%S.%f%z'
        hshSub['start_time'] = str(self.starttime.strftime(fmt))
        hshSub['title'] = ""
        hshSub['sample_name'] = ""
        hshSub['chemical_formula'] = ""
        hshSub['beamtime_id'] = ""
        # hshSub["encoder_pos"] = [dt for dt in self.zebra_data]
        hsh['data'] = hshSub
        self._setParameter(hsh)
        return 1

    def _sendGlobalDictionaryAfter(self):
        hsh = {}
        hshSub = {}
        amsterdam = pytz.timezone('Europe/Amsterdam')
        fmt = '%Y-%m-%dT%H:%M:%S.%f%z'
        starttime = amsterdam.localize(datetime.datetime.now())
        hshSub['end_time'] = str(starttime.strftime(fmt))
        hshSub['comments'] = "some comment"
        hsh['data'] = hshSub
        self._setParameter(hsh)
        return 1

    def _setParameter(self, hsh):
        jsondata = json.dumps(hsh)
        self.nexuswriter_device.JSONRecord = str(jsondata)
        return 1

    def _sendRecordToNxWriter(self, hsh):
        mstr = json.dumps(hsh)
        self.nexuswriter_device.Record(mstr)
        return 1


class cscan_pilc_xia(Macro):
    """Perfoms a continuous scan with the pilc triggering the xia"""

    param_def = [
        ['motor', Type.Motor, None, 'Motor to move'],
        ['start_pos', Type.Float, None, 'Scan start position'],
        ['final_pos', Type.Float, None, 'Scan final position'],
        ['nb_triggers', Type.Integer, None,
         'Nb of triggers generated by the pilc'],
        ['trigger_interval', Type.Float, None,
         'Time or position units between consecutive triggers'],
        ['trigger_mode', Type.Integer, 3,
         'Trigger mode: 1 pos, 2 time, 3 pos-time, 4 time-pos']
    ]

    result_def = [["result", Type.String, None, "the cscan object"]]

    def run(self, motor, start_pos, final_pos, nb_triggers, trigger_interval,
            trigger_mode):

        pilctg_device_name = self.getEnv('PiLCTGDevice')
        self.output("Using PiLCTriggerGenerator device " + pilctg_device_name)
        xia_device_name = self.getEnv('XIADevice')
        self.output("Using XIA device " + xia_device_name)

        # # class XMLConfigServer
        # nexusconfig_device_name = self.getEnv('NeXusConfigDevice')
        # # class TangoDataServer
        # nexuswriter_device_name = self.getEnv('NeXusWriterDevice')

        pilctg_device = PyTango.DeviceProxy(pilctg_device_name)
        xia_device = PyTango.DeviceProxy(xia_device_name)

        motor_device = PyTango.DeviceProxy(motor.getName())

        # self.nexusconfig_device = PyTango.DeviceProxy(
        #     nexusconfig_device_name)
        # self.nexuswriter_device = PyTango.DeviceProxy(
        #      nexuswriter_device_name)

        # self._openNxFile()

        # Set the PiLCTriggerGenerator device

        pilctg_device.TriggerMode = trigger_mode

        # always smaller als trigger_interval
        pilctg_device.TriggerPulseLength = 0.00001

        if trigger_mode == 1:
            pilctg_device.PositionTriggerStart = start_pos
            # position units between triggers
            pilctg_device.PositionTriggerStepSize = trigger_interval
        elif trigger_mode == 2:
            # start triggering directly after Arm is set to 1
            pilctg_device.TimeTriggerStart = 0
            # time for counting
            pilctg_device.TimeTriggerStepSize = trigger_interval
        elif trigger_mode == 3:
            pilctg_device.PositionTriggerStart = start_pos
            # time for counting
            pilctg_device.TimeTriggerStepSize = trigger_interval
        elif trigger_mode == 4:
            pilctg_device.TimeTriggerStart = 0
            # position units between triggers
            pilctg_device.PositionTriggerStepSize = trigger_interval
        else:
            self.warning("Wrong trigger mode. Exit")
            result = "Not run"
            return result

        pilctg_device.NbTriggers = nb_triggers

        # Set XIA

        xia_device.MappingMode = 1
        xia_device.GateMaster = 1
        xia_device.NumberMcaChannels = 2048
        xia_device.NumMapPixels = nb_triggers
        if nb_triggers % 2 == 0:
            xia_device.NumMapPixelsPerBuffer = nb_triggers / 2
        else:
            xia_device.NumMapPixelsPerBuffer = (nb_triggers + 1) / 2
        # xia_device.NumMapPixelsPerBuffer = -1
        # change if one wants to work with more XIA channels
        xia_device.MaskMapChannels = 1

        # nb_xia_channels =
        xia_device.NumberMcaChannels

        xia_device.StartMapping()

        # Compute motor slewrate for the continuous scan

        old_slewrate = motor_device.Velocity

        scan_slewrate = abs(final_pos - start_pos) / \
            (trigger_interval * (nb_triggers - 1))

        motor_device.Velocity = scan_slewrate

        # Move motor to start position minus an offset

        if start_pos < final_pos:
            pos_offset = 0.1
        else:
            pos_offset = -0.1

        self.execMacro("mv", [[motor, start_pos - pos_offset]])

        while motor_device.State() == PyTango.DevState.MOVING:
            time.sleep(1)
        self.output(motor_device.Position)

        if trigger_mode == 2 or trigger_mode == 4:
            # Start motor movement to final position
            # (the macro mv can not be used because it blocks)
            motor_device.Position = final_pos + pos_offset

            # Check when the motor is in the start_position for starting
            # the trigger

            while motor_device.Position < start_pos:
                time.sleep(0.001)

            # Store starttime

            amsterdam = pytz.timezone('Europe/Amsterdam')
            self.starttime = amsterdam.localize(datetime.datetime.now())

            # Start pilc triggering

            pilctg_device.Arm = 1

        elif trigger_mode == 1 or trigger_mode == 3:
            # Store starttime

            amsterdam = pytz.timezone('Europe/Amsterdam')
            self.starttime = amsterdam.localize(datetime.datetime.now())

            # Start pilc triggering

            pilctg_device.Arm = 1

            time.sleep(1)
            # Start motor movement to final position
            #     (the macro mv can not be used because it blocks)
            motor_device.Position = final_pos + pos_offset

        # Check when the triggering is done

        while pilctg_device.State() == PyTango.DevState.MOVING:
            time.sleep(1)

        # Check that the XIA is done

        self.output("Checking xia state")
        while xia_device.State() == PyTango.DevState.MOVING:
            time.sleep(1)

        # Reset motor slewrate

        motor_device.Velocity = old_slewrate

        # PiLC Data

        # pilcencoder_data =
        pilctg_device.EncoderData
        # pilccounter_data =
        pilctg_device.CounterData

        # Open the nexus file for saving data

        # self._openNxFile()
        # self._openNxEntry(motor.getName(), start_pos,
        #       final_pos, nb_triggers, trigger_interval, nb_xia_channels)

        # Close NeXus file

        # self._closeNxEntry()
        # self._closeNxFile()

        result = "Scan ended sucessfully"
        return result


class c2dscan_pilc_sis3820mcs_postrigger(Macro):
    """Perfoms a 2d continuous scan with the pilc triggering the sis3820mcs"""

    param_def = [
        ['motor', Type.Motor, None, 'Internal motor to scan'],
        ['start_pos', Type.Float, None, 'Internal scan start position'],
        ['final_pos', Type.Float, None, 'Internal scan final position'],
        ['nb_triggers', Type.Integer, None, 'Nb of points internal scan'],
        ['trigger_interval', Type.Float, None,
         'Time between consecutive triggers'],
        ['motor_ext', Type.Motor, None, 'External motor to scan'],
        ['start_pos_ext', Type.Float, None, 'External scan start position'],
        ['final_pos_ext', Type.Float, None, 'External scan final position'],
        ['nb_scans', Type.Integer, None, 'Nb of points external scan'],
        ['trigger_mode', Type.Integer, 1,
         'Trigger mode: 1 pos, 2 time, 3 pos-time, 4 time-pos']
    ]

    def run(self, motor, start_pos, final_pos, nb_triggers, trigger_interval,
            motor_ext, start_pos_ext, final_pos_ext, nb_scans, trigger_mode):

        pilctg_device_name = self.getEnv('PiLCTGDevice')
        pilctg_device = PyTango.DeviceProxy(pilctg_device_name)

        motor_int_device = PyTango.DeviceProxy(motor.getName())
        motor_ext_device = PyTango.DeviceProxy(motor_ext.getName())

        # Compute position increment for external motor
        pos_inc_ext = abs(final_pos_ext - start_pos_ext) / nb_scans

        # Move ext motor to start position
        motor_ext_device.Position = start_pos_ext

        for i in range(0, int(nb_scans + 1)):
            while motor_ext_device.state() == PyTango.DevState.MOVING:
                time.sleep(0.001)
            while motor_int_device.state() == PyTango.DevState.MOVING:
                time.sleep(0.001)

            if i == 0:
                corrected_start = start_pos
            else:
                corrected_start = pilctg_device.EncoderTrigger / \
                    pilctg_device.PositionConversion
            if i % 2 == 0:
                self.execMacro(
                    'cscan_pilc_sis3820mcs', motor, corrected_start,
                    final_pos, nb_triggers, trigger_interval, trigger_mode)
            else:
                self.execMacro(
                    'cscan_pilc_sis3820mcs', motor, corrected_start,
                    start_pos, nb_triggers, trigger_interval, trigger_mode)

            # Move ext motor to next position, except for the last point

            if i < nb_scans:
                self.output(motor_ext_device.state())
                self.execMacro(
                    'mv',
                    [[motor_ext, start_pos_ext + (i + 1) * pos_inc_ext]])
                self.output(motor_ext_device.state())
                # motor_ext_device.Position = start_pos_ext + (i+1)
                #        * pos_inc_ext


class cscan_pilc_senv(Macro):
    """ Sets default environment variables """

    def run(self):
        self.setEnv("MCSDevice", "p09/mcs/d1.01")
        self.output("Setting MCSDevice to p09/mcs/d1.01")
        self.setEnv("XIADevice", "haspp06:10000/p06/xia/p06.1")
        self.output("Setting XIADevice to p06/xia/p06.1")
        self.setEnv("PiLCTGDevice",
                    "haspp06:10000/p06/pilctriggergenerator/exp.01")
        self.output("Setting PiLCTGDevice to p06/pilctriggergenerator/exp.01")
        # self.setEnv("CScanFileName",
        #             "/home/experiment/test_cscan_output")
        # self.output(
        # "Setting CScanFileName to /home/experiment/test_cscan_output")
        # self.setEnv(
        # "NeXusConfigDevice", "p06/nxsconfigserver/haspp06ctrl")
        # self.output(
        # "Setting NeXusConfigDevice to p06/nxsconfigserver/haspp06ctrl")
        # self.setEnv("NeXusWriterDevice", "p06/nxsdatawriter/haspp06ctrl")
        # self.output(
        # "Setting NeXusWriterDevice to p06/nxsdatawriter/haspp06ctrl")
        # self.setEnv("CScanID", 0)
        # self.output("Setting CScanID to 0")
