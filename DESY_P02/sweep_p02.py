#!/bin/env python

"""sweep scan p02"""

__all__ = ["sweep_p02", "sweep_senv"]

import PyTango
from sardana.macroserver.macro import *
from sardana.macroserver.macro import macro
import json
import time
import pytz
import datetime
import numpy
import math
from xml.dom.minidom import parseString

angleOffsets = {
    "polar_angle_channel_1": 0.,
    "polar_angle_channel_2": 1.,
    "polar_angle_channel_3": 2.,
    "polar_angle_channel_4": 3.,
    "polar_angle_channel_5": 4.,
    "polar_angle_channel_6": 5.,
    "polar_angle_channel_7": 6.,
    "polar_angle_channel_8": 7.,
    "polar_angle_channel_9": 8.,
    "polar_angle_channel_10": 9.
}


class sweep_p02(Macro):
    """Perfoms a sweep scan. Counters are read during the sweep
       (they are always active) """

    #
    param_def = [
        ['motor',           Type.Motor,     None, 'Sweep motor'],
        ['sweep_start_pos', Type.Float,     None, 'Sweep start position'],
        ['sweep_distance',  Type.Float,     None, 'Sweep distance'],
        ['sweep_offset',    Type.Float,     None, 'Sweep offset'],
        ['nb_intervals',    Type.Integer,   None, 'Sweep number of intervals'],
        ['sample_time',     Type.Float,     None, 'Sweep sample time']
        ]

    #
    def run(self, motor, sweep_start_pos, sweep_distance, sweep_offset,
            nb_intervals, sample_time):
        slewOrig = None
        motor_device = None
        try:
            # class NXSConfigServer
            nexusconfig_device_name = self.getEnv('NeXusConfigDevice')
            self.nexusconfig_device = PyTango.DeviceProxy(nexusconfig_device_name)
            # class NXSDataWriter
            nexuswriter_device_name = self.getEnv('NeXusWriterDevice')
            self.nexuswriter_device = PyTango.DeviceProxy(nexuswriter_device_name)

            sweep_counters_prefix = self.getEnv('SweepCountersPrefix')
            hshCounters = self._get_sweep_counters("ten_channel_detector", 
                                                   sweep_counters_prefix)

            self.debug("hshCounters %s", hshCounters.keys())
            clock_name = None
            for alias in hshCounters.keys():
                if alias.find('32') >= 0:
                    clock_name = alias
            if not clock_name:
                self.error("Clock cannot be found")
            self.output("clock: %s" % clock_name  )      


            motor_device = PyTango.DeviceProxy(motor.name)

            # For the timer one has to use the corresponding tango device
            # and not the device in the pool
            # because it can not be started outside a measurement group

            timer_device_name = self.getEnv('SweepTimerTangoDevice')
            timer_device = PyTango.DeviceProxy(timer_device_name)

            slew_orig = motor_device.Velocity

            self.sweep_motor = motor.name
            self.sweep_start = sweep_start_pos
            self.sweep_distance = sweep_distance
            self.sweep_offset = sweep_offset
            self.nb_intervals = nb_intervals
            self.sample_time = sample_time

           # Compute sweep velocity

            sweep_time = nb_intervals * sample_time
            sweep_full_distance = sweep_distance + 2 * sweep_offset
            move_time_orig = math.fabs(sweep_full_distance / slew_orig)
            self.output("sweep_time %g move_time_orig %g " %
                        (sweep_time, move_time_orig))

            slew_sweep = move_time_orig *slew_orig / sweep_time
#            self.output("SLEW %g %g %g" % (slew_sweep, sweep_full_distance, sweep_time))
            self.output("slewRate %d slewSweep %d " % (slew_orig, slew_sweep))

            if slew_sweep > slew_orig or slew_sweep < motor_device.Base_rate:
                raise ValueError("slew_sweep %d out of range [%d,%d]" %
                                 (slew_sweep, slew_orig, motor_device.Base_rate))

            self._openNxFile()
            self._openNxEntry("ten_channel_detector")

            #
            # Move the motor to the start position
            #

            self.output("p02sweep: moving %s to start position %g" %
                        (motor.name, (sweep_start_pos - sweep_offset)))

            motor_device.write_attribute("position",
                                         (sweep_start_pos - sweep_offset))

            while motor_device.State() == PyTango.DevState.MOVING:
                self.output("%s to %g, %g " % (motor.name, (sweep_start_pos - sweep_offset), 
                                               motor_device.position))
                time.sleep(1)

            #
            # Reset the counters
            #

            for cnt in hshCounters.keys():
                hshCounters[cnt]['proxy'].Counts = 0

            #
            # Start the timer
            #

            timer_device.SampleTime = 2000
            timer_device.Start()
            time_start_timer = time.time()

            #
            # Start the sweep
            #

            sweep_final_pos = sweep_start_pos + sweep_distance + sweep_offset

            self.output("Sweeping from %g to %g" %
                        (motor_device.position, sweep_final_pos))

            motor_device.Velocity = slew_sweep
            motor_device.write_attribute("position", sweep_final_pos)

            time_overhead = 0.
            hshCounterReadings = {}
            for cnt in hshCounters.keys():
                hshCounterReadings[cnt] = {}
                hshCounterReadings[cnt]['counts'] = 0
                hshCounterReadings[cnt]['counts_old'] = 0

            pos_old = motor_device.position

            hshMain = {}
            hshRecord = {}
            hshMain['data'] = hshRecord

            count = 1

            time_cycle_start = time.time()
            time_total_start = time.time()

            while(motor_device.state() == PyTango.DevState.MOVING):
                if sample_time > time_overhead:
                    time.sleep(sample_time - time_overhead)
                time_overhead_start = time.time()
                pos_before = motor_device.position
                #
                # read all counters
                #
                for cnt in hshCounters.keys():
                    self.debug(cnt)
                    hshCounterReadings[cnt]['counts'] = \
                        hshCounters[cnt]['proxy'].Counts
                    self.debug(hshCounterReadings[cnt]['counts'])
                #
                # clear the clock because we might run out of 32 bit
                #
                hshCounters[clock_name]['proxy'].Counts = 0
                hshCounterReadings[clock_name]['counts_old'] = 0
                #
                # the position is the mean value
                #  - before and after the counter reading
                #
                pos = (pos_before + motor_device.position) / 2.

                if hshCounterReadings[clock_name]['counts'] == \
                        hshCounterReadings[clock_name]['counts_old']:
                    self.output("No clock counts")
                    break

                corr = 1000000. * sample_time / (
                    hshCounterReadings[clock_name]["counts"]
                    - hshCounterReadings[clock_name]["counts_old"])

                for mot in sorted(angleOffsets.keys()):
                    hshRecord[mot] = pos + angleOffsets[mot]

                for cnt in sorted(hshCounters.keys()):
                    temp = corr * (hshCounterReadings[cnt]["counts"]
                                   - hshCounterReadings[cnt]["counts_old"])
                    if temp < 0:
                        temp = 0
                    self.debug("name %s %s" % (cnt,hshCounters[cnt]['name']))
                    hshRecord[hshCounters[cnt]['name']] = temp
                    hshCounterReadings[cnt]['counts_old'] = \
                        hshCounterReadings[cnt]['counts']

                hshRecord['correction'] = corr
                hshRecord['delta_position'] = pos - pos_old

                pos_old = pos

                self._sendRecordToNxWriter(hshMain)

                time_cycle = time.time() - time_cycle_start
                time_cycle_start = time.time()
                self.output("%d Ovrhd %g, timeCycle %g, corr %g" %
                            (count, time_overhead, time_cycle, corr))

                count += 1
                if (count % 20) == 0:
                    self.output(" %d motor at %g " %
                                (count, motor_device.position))

                #
                # make sure that the timer does not expire
                #
                if (time.time() - time_start_timer) > 1900:
                    timer_device.Stop()
                    timer_device.SampleTime = 2000
                    timer_device.Start()
                    time_start_timer = time.time()

                time_overhead = time.time() - time_overhead_start

            self.output("sweep ended, total time %gs (%gs) " %
                        ((time.time() - time_total_start),
                         nb_intervals * sample_time))

            self._closeNxEntry()
            self._closeNxFile()
        finally:
            if motor_device:
                if motor_device.state() == PyTango.DevState.MOVING:
                    motor_device.Stop()
                while(motor_device.state() == PyTango.DevState.MOVING):
                    time.sleep(0.1)
                if slew_orig is not None:
                    motor_device.Velocity = slew_orig
                    
    
            
    def _getRecord(self, node):
        withRec = ["CLIENT"]
        if node.nodeName == 'datasource':
            dsource = node
        else:
            dsource = node.getElementsByTagName("datasource")[0] \
                if len(node.getElementsByTagName("datasource")) else None
        dstype = dsource.attributes["type"] \
            if dsource and dsource.hasAttribute("type") else None
        if dstype.value in withRec:
            rec = dsource.getElementsByTagName("record")[0] \
                if dsource and len(dsource.getElementsByTagName("record")) \
                else None
            if rec.hasAttribute("name"):
                rc = rec.attributes["name"]
            else:
                rc = None
            if rc:
                return rc.value

    def _getDataSource(self, alias):
        dsrcs = self.nexusconfig_device.AvailableDataSources()
        names = []
        records = []
        names.append(alias)
        for nm in names:
            if nm not in dsrcs:
                self.error(
                    "_getDataSource: Datasource %s not stored " \
                    + "in configuration server\n" % nm)
                    
        xmls = self.nexusconfig_device.DataSources(names)
        for xml in xmls:
            if xml:
                try:
                    indom = parseString(xml)
                    rec = self._getRecord(indom)
                    if rec:
                        records.append(rec)
                except:
                    self.error(
                        "_getDataSource: Datasource %s cannot be parsed\n" % xml)
        if len(records) != 1:
            self.error(
                "_getDataSource: more than 1 data sources for %s:\n%s" % \
                    (alias, "\n".join(records)))
        self.debug("_getDataSource: %8s -> %s " % (alias, str(records[0])))
        return str(records[0])

    def _get_sweep_counters(self, componentName, sweep_counters_prefix):
        self.nexusconfig_device.Open()
        cmps = self.nexusconfig_device.AvailableComponents()
        if componentName not in cmps:
            self.error(
                "getProxies: Component %s not stored in configuration server\n" \
                    % componentName)
        lines = self.nexusconfig_device.ComponentDataSources(componentName)
        hshCounters = {}
       
        db = PyTango.Database()        
        for alias in sorted(set(lines)):
            alias = alias.strip()
            if alias.find(sweep_counters_prefix) >= 0:
                ret = self._getDataSource(alias)
                hshCounters[alias] = {}
                hshCounters[alias]['name'] = ret
                full_sardana_name = db.get_device_alias(alias)
            # The properties can not be found using the alias name
                b = db.get_device_property(full_sardana_name, ['__SubDevices'])
                dName = b['__SubDevices'][0]
                # The device to the Tango device and not to the Sardana device
                # is need for writing in the Counts attribute
                hshCounters[alias]['proxy'] = PyTango.DeviceProxy(dName)
        return hshCounters

    #
    def _openNxFile(self):
        sweep_id = self.getEnv('SweepID')
        fileNameNx = self.getEnv('SweepFileName') + "_" + str(sweep_id) \
            + ".nxs"
        self.setEnv("SweepID", sweep_id + 1)
        self.nexuswriter_device.Init()
        self.output(fileNameNx)
        self.nexuswriter_device.FileName = str(fileNameNx)
        self.nexuswriter_device.OpenFile()
        return 1

    #
    def _openNxEntry(self, componentName):

        self._sendGlobalDictionaryBefore()

        self.nexusconfig_device.Open()

        cmps = self.nexusconfig_device.AvailableComponents()
        cmp_list = []
        if componentName not in cmps:
            self.output("_openNxEntry: %s not in configuration server" %
                        componentName)
        else:
            cmp_list.append(componentName)

        self.nexusconfig_device.CreateConfiguration(cmp_list)
        xmlconfig = self.nexusconfig_device.XMLString
        self.nexuswriter_device.XMLSettings = str(xmlconfig)
        try:
            self.nexuswriter_device.OpenEntry()
        except:
            pass

        return 1

    #
    def _closeNxFile(self):
        self.nexuswriter_device.CloseFile()
        return 1

    #
    def _closeNxEntry(self):
        self._sendGlobalDictionaryAfter()
        self.nexuswriter_device.CloseEntry()
        return 1

    #
    def _sendGlobalDictionaryBefore(self):
        hsh = {}
        hshSub = {}
        hshSub['sweep_motor'] = self.sweep_motor
        hshSub['sweep_start'] = self.sweep_start
        hshSub['sweep_distance'] = self.sweep_distance
        hshSub['sweep_offset'] = self.sweep_offset
        hshSub['interval'] = self.nb_intervals
        hshSub['sample_time'] = self.sample_time
        amsterdam = pytz.timezone('Europe/Amsterdam')
        fmt = '%Y-%m-%dT%H:%M:%S.%f%z'
        starttime = amsterdam.localize(datetime.datetime.now())
        hshSub['start_time'] = str(starttime.strftime(fmt))
        try:
            title = self.getEnv('SweepTitle')
        except:
            title = ""
        hshSub['title'] = title
        try:
            sample_name = self.getEnv('SweepSampleName')
        except:
            sample_name = ""
        hshSub['sample_name'] = sample_name
        try:
            chemical_formula = self.getEnv('SweepChemicalFormula')
        except:
            chemical_formula = ""
        hshSub['chemical_formula'] = chemical_formula
        try:
            beamtime_id = self.getEnv('SweepBeamtimeId')
        except:
            beamtime_id = ""
        hshSub['beamtime_id'] = beamtime_id
        hsh['data'] = hshSub
        self._setParameter(hsh)
        return 1

    #
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


class sweep_senv(Macro):
    """ Sets default environment variables """

    def run(self):
        import socket
        hostname = socket.gethostname().split(".")[0]

        if hostname == "haspp02ch1":
            file_name = "/tmp/sweep_output"
            self.setEnv("SweepFileName", file_name)
            self.output("Setting SweepFileName to %s" % file_name)

            nexus_config_device = "haspp02ch1:10000/p02/nxsconfigserver/haspp02ch1"
            self.setEnv("NeXusConfigDevice",  nexus_config_device)
            self.output("Setting NeXusConfigDevice to  %s" % nexus_config_device)

            nexus_writer_device = "haspp02ch1:10000/p02/nxsdatawriter/haspp02ch1"
            self.setEnv("NeXusWriterDevice", nexus_writer_device)
            self.output("Setting NeXusWriterDevice to %s" % nexus_writer_device)

            self.setEnv("SweepID", 0)
            self.output("Setting SweepID to 0")
            sweep_counters_prefix = "exp_c"
            self.setEnv("SweepCountersPrefix",  sweep_counters_prefix)
            self.output("Setting SweepCountersPrefix to %s" %
                        sweep_counters_prefix)

            sweep_timer_tango_device = "haspp02oh1:10000/p02/timer/eh1b.01"
            self.setEnv("SweepTimerTangoDevice", sweep_timer_tango_device)
            self.output("Setting SweepTimerTangoDevice to %s" %
                        sweep_timer_tango_device)

        elif hostname == "haspp02ch1a":
            file_name = "/tmp/sweep_output"
            self.setEnv("SweepFileName", file_name)
            self.output("Setting SweepFileName to %s" % file_name)

            nexus_config_device = "haspp02oh1:10000/p02/nxsconfigserver/haspp02ch1a"
            self.setEnv("NeXusConfigDevice",  nexus_config_device)
            self.output("Setting NeXusConfigDevice to  %s" % nexus_config_device)

            nexus_writer_device = "haspp02oh1:10000/p02/nxsdatawriter/haspp02ch1a"
            self.setEnv("NeXusWriterDevice", nexus_writer_device)
            self.output("Setting NeXusWriterDevice to %s" % nexus_writer_device)

            self.setEnv("SweepID", 0)
            self.output("Setting SweepID to 0")
            sweep_counters_prefix = "exp_c"
            self.setEnv("SweepCountersPrefix",  sweep_counters_prefix)
            self.output("Setting SweepCountersPrefix to %s" %
                        sweep_counters_prefix)

            sweep_timer_tango_device = "haspp02oh1:10000/p02/timer/eh1b.01"
            self.setEnv("SweepTimerTangoDevice", sweep_timer_tango_device)
            self.output("Setting SweepTimerTangoDevice to %s" %
                        sweep_timer_tango_device)

        elif hostname == "haso111tb":
            file_name = "/home/tnunez/sweep_files/test_sweep_output"
            self.setEnv("SweepFileName", file_name)
            self.output("Setting SweepFileName to %s" % file_name)

            nexus_config_device = "haso111tb:10000/test/xmlconfigserver/01"
            self.setEnv("NeXusConfigDevice",  nexus_config_device)
            self.output("Setting NeXusConfigDevice to  %s" % nexus_config_device)

            nexus_writer_device = "haso111tb:10000/test/tangodataserver/01"
            self.setEnv("NeXusWriterDevice", nexus_writer_device)
            self.output("Setting NeXusWriterDevice to %s" % nexus_writer_device)
            self.setEnv("SweepID", 0)
            self.output("Setting SweepID to 0")

            sweep_counters_prefix = "exp_c"
            self.setEnv("SweepCountersPrefix",  sweep_counters_prefix)
            self.output("Setting SweepCountersPrefix to %s" %
                        sweep_counters_prefix)

            sweep_timer_tango_device = "haso111tb:10000/p09/dgg2/exp.01"
            self.setEnv("SweepTimerTangoDevice", sweep_timer_tango_device)
            self.output("Setting SweepTimerTangoDevice to %s" %
                        sweep_timer_tango_device)

        elif hostname == "haso228k":
            file_name = "/tmp/sweep_output"
            self.setEnv("SweepFileName", file_name)
            self.output("Setting SweepFileName to %s" % file_name)

            nexus_config_device = "haso228k:10000/p02/mcs/r228"
            self.setEnv("NeXusConfigDevice",  nexus_config_device)
            self.output("Setting NeXusConfigDevice to  %s" % nexus_config_device)

            nexus_writer_device = "haso228k:10000/p09/tdw/r228"
            self.setEnv("NeXusWriterDevice", nexus_writer_device)
            self.output("Setting NeXusWriterDevice to %s" % nexus_writer_device)

            self.setEnv("SweepID", 0)
            self.output("Setting SweepID to 0")
            sweep_counters_prefix = "exp_c"
            self.setEnv("SweepCountersPrefix",  sweep_counters_prefix)
            self.output("Setting SweepCountersPrefix to %s" %
                        sweep_counters_prefix)

            sweep_timer_tango_device = "haso228k:10000/p09/dgg2/exp.01"
            self.setEnv("SweepTimerTangoDevice", sweep_timer_tango_device)
            self.output("Setting SweepTimerTangoDevice to %s" %
                        sweep_timer_tango_device)

        elif hostname == "haso107klx":
            file_name = "/tmp/sweep_output"
            self.setEnv("SweepFileName", file_name)
            self.output("Setting SweepFileName to %s" % file_name)

            nexus_config_device = "haso107klx.desy.de:10000/p09/xmlconfigserver/exp.01"
            self.setEnv("NeXusConfigDevice",  nexus_config_device)
            self.output("Setting NeXusConfigDevice to  %s" % nexus_config_device)

            nexus_writer_device = "haso107klx.desy.de:10000/p09/tangodataserver/exp.01"
            self.setEnv("NeXusWriterDevice", nexus_writer_device)
            self.output("Setting NeXusWriterDevice to %s" % nexus_writer_device)

            self.setEnv("SweepID", 0)
            self.output("Setting SweepID to 0")
            sweep_counters_prefix = "exp_c"
            self.setEnv("SweepCountersPrefix",  sweep_counters_prefix)
            self.output("Setting SweepCountersPrefix to %s" %
                        sweep_counters_prefix)

            sweep_timer_tango_device = "haso107klx:10000/p09/dgg2/exp.01"
            self.setEnv("SweepTimerTangoDevice", sweep_timer_tango_device)
            self.output("Setting SweepTimerTangoDevice to %s" %
                        sweep_timer_tango_device)

