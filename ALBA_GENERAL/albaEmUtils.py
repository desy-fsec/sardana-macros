import time
from sardana.macroserver.macro import Macro, Type
from taurus import Device, Attribute
from taurus.core import AttrQuality
import PyTango

#TODO Change to taurus in TEP14
STATE_MOVING = PyTango.DevState.MOVING

RANGES = ['1mA', '100uA', '10uA', '1uA', '100nA', '10nA', '1nA', '100pA']
MIN_VALUE = 5
MAX_VALUE = 95
INTEGRATION_TIME = 0.3
AUTO_RANGE_TIMEOUT = 40

class findMaxRange(Macro):
    """
    Macro to find the best range of the electrommeter channels for the scan.

    The parameter start_pos and end_pos are the position of the motor in the
    scan.
    """
    param_def = [['start_pos', Type.Float, None, 'Start position'],
                 ['end_pos', Type.Float, None, 'End position']]

    def __init__(self, *args, **kwargs):
        super(findMaxRange, self).__init__(*args, **kwargs)
        self.elements = {}

    def prepare_mntgrp(self):
        mnt_grp_name = self.getEnv("Meas")
        self.debug("Preparing Meas:  %s" %mnt_grp_name)

        self.meas = self.getObj(mnt_grp_name, type_class=Type.MeasurementGroup)
        cfg = self.meas.getConfiguration()
        cfg.prepare()
        self.extract_conf(cfg)
        self.meas.putIntegrationTime(INTEGRATION_TIME)
        self.debug("Meas used to take the Range: %s" %mnt_grp_name)

    def extract_conf(self, cfg):
        self.debug("Extracting conf of Meas:")
        self.channels = {}
        for i in cfg.getChannelsInfoList():
            if i.full_name.startswith('tango'):
                self.channels[i.full_name] = RANGES.index('100pA')

    def acquire_mntgrp(self):
        self.debug("AcquireMntGrp() entering...")
        self.count_id = self.meas.start()
        self.debug("AcquireMntGrp() leaving...")

    def wait_mntgrp(self):
        self.debug("WaitMntGrp() entering...")
        self.meas.waitFinish(id=self.count_id)
        self.debug("WaitMntGrp() leaving...")

    def extract_channels(self):
        for name in self.channels.keys():
            dev, attr = str(name).rsplit('/', 1)
            if dev not in self.elements:
                # Saving in the dictionary the taurus Device and the list
                # of channels to change the Range
                self.elements[dev] = {'tau_dev': Device(dev), 'chn': {}}
            # Bool, is a Flag to check if the Channel has been checked the Range
            self.elements[dev]['chn'][attr[-1]] = False

    def conf_channels(self, auto_range):
        min_value = MIN_VALUE
        max_value = MAX_VALUE
        if not auto_range:
            min_value = 0
            max_value = 0

        for dev in self.elements.keys():
            tau_dev = self.elements[dev]['tau_dev']
            chn = self.elements[dev]['chn']
            for i in chn:
                attr = 'AutoRange_ch%s'%i
                tau_dev.write_attribute(attr, auto_range)
                attr = 'AutoRangeMin_ch%s'%i
                tau_dev.write_attribute(attr, min_value)
                attr = 'AutoRangeMax_ch%s'%i
                tau_dev.write_attribute(attr, max_value)

    def run(self, start_pos, end_pos):
        try:
            self.info('Starting AutoRange Calibration Process')
            has_been_configured = False
            mot = self.getEnv("Motor")
            self.mot = self.getMoveable(mot)

            if self.mot is None:
                raise Exception("Error Creating The Motor")
            self.prepare_mntgrp()
            self.extract_channels()

            # Configure Channels for AutoRange Mode, True, to enable the
            # AutoMode
            self.conf_channels(True)
            self.debug('The Channels has been Configured in AutoRange Mode')

            has_been_configured = True
            self.info('Moving the motor to Start Position')
            self.mot.move(start_pos)
            t = time.time()
            self.info('AutoConfiguring Electrometers while the motor is '
                      'going to end position:')
            while (time.time() - t) < AUTO_RANGE_TIMEOUT:
                time.sleep(0.5)
                flag_finish = True
                for dev in self.elements.keys():
                    tau_dev = self.elements[dev]['tau_dev']
                    chn = self.elements[dev]['chn']
                    for i, valid in chn.items():
                        # Check if this channel has been checked previously
                        if valid:
                            continue
                        attr = 'range_ch%s'%i
                        valid = (tau_dev.read_attribute(attr).quality ==
                                 AttrQuality.ATTR_VALID)
                        flag_finish &= valid
                        chn[i] = valid
                if flag_finish:
                    break

                self.checkPoint()
            else:
                raise RuntimeError('The AutoRange failed, you should check by '
                                   'hand some channels')

            self.debug('Starting to Move to end Position')
            self.mot.write_attribute('position', end_pos)
            data = []
            self.debug('Starting to Acquire')
            while self.mot.state() == STATE_MOVING:
                self.acquire_mntgrp()
                self.wait_mntgrp()
                d = self.meas.getValues()
                data.append(d)
                self.checkPoint()

            # Unconfigure Channels to AutoRange Mode
            self.conf_channels(False)
            has_been_configured = False
            for line in data:
                for attr in line.keys():
                    if attr in self.channels:
                        range = RANGES.index(line[attr])
                        if self.channels[attr] > range:
                            self.channels[attr] = range

            self.debug(self.channels)
            self.info('Configuring Electrometers Ranges')

            for i in self.channels.keys():
                range = RANGES[self.channels[i]]
                d = Attribute(i)
                d.write(range)

        except Exception, e:
            self.error(e)
        finally:
            self.mot.stop()
            while self.mot.state == STATE_MOVING:
                pass
            if has_been_configured:
                self.conf_channels(False)