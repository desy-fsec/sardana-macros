from sardana.macroserver.macro import Macro, Type
import taurus

POS_DELAY = 'pos_delay'
SHUT_DELAY = 'shutter_delay'
SHUT_HIGH = 'shutter_high'
SHUT_LOW = 'shutter_low'
DET_DELAY = 'detector_delay'
DET_HIGH = 'det_high'
DET_LOW = 'det_low'
TRIGGERS_COUNT = 'triggers_count'

class ni660x_configure_collect(Macro):
    """ Configures the ni6602 card to generate triggers for the shutter and the detector at given position. """
    param_def = [['shutter_delay_time', Type.Float, None, 'Time for shutter to be opened (seconds).'],
               ['det_trigger_pos', Type.Float, None, 'Position to trigger the detector.'],
               ['pulse_high_width', Type.Float, None, 'Pulse high width in relative position units.'],
               ['pulse_low_width', Type.Float, None, 'Pulse low width in relative position units.'],
               ['triggers_count', Type.Integer, 1, 'Number of repetitions of the trigger. Default is 1.']]

    def run(self, shutter_delay_time, det_trigger_pos, pulse_high_width, pulse_low_width, triggers_count):
    # some values do not need to be passed through the macro...
        omega = self.getDevice('omega')
        ni_dev = taurus.Device('BL13/IO/ibl1302-dev1')
        ni_poschan = taurus.Device('BL13/IO/ibl1302-dev1-ctr0')
        ni_shutterchan = taurus.Device('BL13/IO/ibl1302-dev1-ctr2')
        ni_pilatuschan = taurus.Device('BL13/IO/ibl1302-dev1-ctr4')

        vel_0 = 0.
        vel = omega.read_attribute('velocity').value
        t_acc = omega.read_attribute('acceleration').value
        t_shutter = shutter_delay_time
        enc_resolution_X4 = 80175
        x_abs_0 = omega.read_attribute('position').value
        x_abs_trigger = det_trigger_pos
        x_rel_high = pulse_high_width
        x_rel_low = pulse_low_width

        try:
            ni_cfg_dict = ni660x_build_position_trigger_config(vel_0, vel, t_acc, t_shutter, enc_resolution_X4, x_abs_0, x_abs_trigger, x_rel_high, x_rel_low, triggers_count)
            self.info('before collect!!!')
            self.info("%s, %s, %s, %s" % (ni_dev, ni_poschan, ni_shutterchan, ni_cfg_dict))
            ni660x_tango_configure_collect(ni_dev, ni_poschan, ni_shutterchan, ni_pilatuschan, ni_cfg_dict)
            self.info('NI card configure. Remember to unconfigure it at the end of the collect macro.')
        except Exception, e:
            self.error('Not possible to configure NI card, exception is:')
            self.error(str(e))


class ni660x_unconfigure_collect(Macro):
    """ Removes the configuration of the ni6602 card."""

    def run(self):
        # some values do not need to be passed through the macro...
        ni_dev = taurus.Device('BL13/IO/ibl1302-dev1')
        ni_poschan = taurus.Device('BL13/IO/ibl1302-dev1-ctr0')
        ni_shutterchan = taurus.Device('BL13/IO/ibl1302-dev1-ctr2')
        ni_pilatuschan = taurus.Device('BL13/IO/ibl1302-dev1-ctr4')

        ni660x_tango_unconfigure_collect(ni_dev, ni_poschan, ni_shutterchan, ni_pilatuschan)

class ni660x_shutter_open_close(Macro):
    param_def = [['open_close', Type.String, None, 'open/close keywords allowed.']]

    def run(self, open_close):
        open_close = open_close.lower()
        idle_state = None
        if open_close == 'open':
            idle_state = 'Low'
        elif open_close == 'close':
            idle_state = 'High'
        else:
            raise Exception('Only open/close keywords allowed.')

        ni_shutterchan = taurus.Device('BL13/IO/ibl1302-dev1-ctr2')
        ni660x_tango_set_channel_idle_state(ni_shutterchan, idle_state)

####################################
# AUXILIARY FUNCTIONS TO CONFIGURE #
####################################
def positionToX1counts(position, resolution):
    return int((position * resolution) / 4)

def ni660x_build_position_trigger_config(vel_0, vel, t_acc, t_shutter, enc_resolution_X4, x_abs_0, x_abs_trigger, x_rel_high, x_rel_low, triggers_count):
    """X4, X2 and X1 encoding is explained here:   http://www.ni.com/white-paper/7109/en#toc2
    """
    acc = (vel - vel_0)/(1.*t_acc)
    x_constant_vel = vel_0 * t_acc + 1/2. * (acc) * (t_acc**2)
    x_abs_constant_vel = x_abs_0 + x_constant_vel

    x_min_chan_delay_X1 = 4
    x_min_chan_delay = (x_min_chan_delay_X1 * 4) / enc_resolution_X4

    x_t_shutter = vel*t_shutter

    x_min_abs_trig_shutter = x_abs_constant_vel + x_min_chan_delay

    x_min_abs_trig_det = x_min_abs_trig_shutter + x_t_shutter

    x_padding_first_trigger = x_abs_trigger - x_min_abs_trig_det

    if x_padding_first_trigger < 0:
        msg = 'Trigger not possible:'
        msg += '\nStart Position: %f' % x_abs_0
        msg += '\nConstant Speed: %f' % x_abs_constant_vel
        msg += '\nMin Shutter Trigger: %f' % x_min_abs_trig_shutter
        msg += '\nMin Detector Trigger: %f (Shutter opened)' % x_min_abs_trig_det
        msg += '\nTrigger requested: %f' % x_abs_trigger
        raise Exception(msg)

    x_abs_trig_shutter = x_padding_first_trigger + x_min_abs_trig_shutter
    trig_shutter_high = x_t_shutter + x_rel_high
    trig_shutter_low = x_rel_low

    x_abs_trig_det = x_padding_first_trigger + x_min_abs_trig_det
    trig_det_high = x_rel_high
    trig_det_low = x_rel_low

    # NI CONFIGURATION
    ni_cfg_dict = {}

    poschan_delay_X1 = positionToX1counts(x_constant_vel, enc_resolution_X4)

    shutterchan_initial_delay_X1 = positionToX1counts((x_abs_trig_shutter - x_abs_constant_vel), enc_resolution_X4)
    shutterchan_high_ticks_X1 = positionToX1counts(trig_shutter_high, enc_resolution_X4)
    shutterchan_low_ticks_X1 = positionToX1counts(trig_shutter_low, enc_resolution_X4)

    detchan_initial_delay_X1 = positionToX1counts((x_abs_trig_det - x_abs_constant_vel), enc_resolution_X4)
    detchan_high_ticks_X1 = positionToX1counts(trig_det_high, enc_resolution_X4)
    detchan_low_ticks_X1 = positionToX1counts(trig_det_low, enc_resolution_X4)

    ni_cfg_dict[POS_DELAY] = poschan_delay_X1
    ni_cfg_dict[SHUT_DELAY] = shutterchan_initial_delay_X1
    ni_cfg_dict[SHUT_HIGH] = shutterchan_high_ticks_X1
    ni_cfg_dict[SHUT_LOW] = shutterchan_low_ticks_X1
    ni_cfg_dict[DET_DELAY] = detchan_initial_delay_X1
    ni_cfg_dict[DET_HIGH] = detchan_high_ticks_X1
    ni_cfg_dict[DET_LOW] = detchan_low_ticks_X1
    # BE CAREFUL, IT HAS TO BE A LONG!
    ni_cfg_dict[TRIGGERS_COUNT] = long(triggers_count)

    return ni_cfg_dict


def ni660x_tango_unconfigure_collect(ni_dev, ni_poschan, ni_shutterchan, ni_pilatuschan):
    # output of ctr4 to output of ctr1
    ni_dev.command_inout('DisconnectTerms',['/Dev1/PFI20', '/Dev1/PFI32'])
    # indexer X4 phase A
    # ni_dev.command_inout('DisconnectTerms',['/Dev1/PFI39', '/Dev1/PFI12'])
    # timebase
    # ni_dev.command_inout('DisconnectTerms',['/Dev1/PFI36', '/Dev1/PFI8'])

    # Stop jobs
    ni_poschan.command_inout('Stop')
    ni_shutterchan.command_inout('Stop')
    ni_pilatuschan.command_inout('Stop')


def ni660x_tango_configure_collect(ni_dev, ni_poschan, ni_shutterchan, ni_pilatuschan, ni_cfg_dict):

    # JUST TO MAKE SURE IT IS UNCONFIGURED
    ni660x_tango_unconfigure_collect(ni_dev, ni_poschan, ni_shutterchan, ni_pilatuschan)

    # CONFIGURE POSITION CHANNEL

    # set initial ans reset positions
    initialPos = pow(2,32) - 2 - ni_cfg_dict[POS_DELAY]
    resetPos = pow(2,32) - 2

    # generate pulse on overflow (default: Toggle)
    ni_poschan.write_attribute('OutputEventBehaviour', 'Pulse')
    # use default output PFI for overflow pulse
    ni_poschan.write_attribute('OutputEventTerminal', '/Dev1/PFI36')
    # counter overflow occurs when it reaches 2^32 - 1
    # configure initial position to 2^32 - 2
    # so with an increment of 1 it will reach overflow
    # and generate a pulse on the output terminal
    ni_poschan.write_attribute('InitialPos', initialPos)
    # configure reset position to 2^32 - 2
    # in order to achieve a continuous reset when counting positive
    ni_poschan.write_attribute('ZindexVal', resetPos)
    # set phase for z-signal reset (use different values depending on motion's direction)
    # * 'AHighBLow' when moving in positive direction
    # * 'ALowBLow' when moving in negative direction
    ni_poschan.write_attribute('ZindexPhase', 'AHighBLow')
    # use units of ticks
    ni_poschan.write_attribute('Units', 'Ticks')
    # MUST use decoding X1 - this reduces resolution by factor of 4 in comparison to X4
    # in X4 any transition of each of the phases A and B, counts
    # in X1 only a certain transition of one of the phases counts
    ni_poschan.write_attribute('Decoding', 'X1')


    # CONFIGURE SHUTTER TRIGGER

    # use position measurement overflow pulses as source of trigger
    ni_shutterchan.write_attribute('SourceTerminal', '/Dev1/PFI36')
    # configuring nr of pulses (it has to be a long type)
    ni_shutterchan.write_attribute('SampPerChan', ni_cfg_dict[TRIGGERS_COUNT])
    # configure finite generation of triggers (not infinite)
    ni_shutterchan.write_attribute('SampleMode','Finite')
    # configure sampling timing type to implicit
    ni_shutterchan.write_attribute('SampleTimingType', 'Implicit')
    # set the value for the idle state
    ni_shutterchan.write_attribute('IdleState', 'High')
    # configure minimum possible initial delay in ticks
    # for multiple trigger generation
    ni_shutterchan.write_attribute('InitialDelayTicks', ni_cfg_dict[SHUT_DELAY])
    # configure minimum low interval in ticks
    ni_shutterchan.write_attribute('LowTicks', ni_cfg_dict[SHUT_HIGH])
    # configure minimum high interval in ticks
    ni_shutterchan.write_attribute('HighTicks', ni_cfg_dict[SHUT_LOW])


    # CONFIGURE DETECTOR TRIGGER

    # use position measurement overflow pulses as source of trigger
    ni_pilatuschan.write_attribute('SourceTerminal', '/Dev1/PFI36')
    # configuring nr of pulses (it has to be a long type)
    ni_pilatuschan.write_attribute('SampPerChan', ni_cfg_dict[TRIGGERS_COUNT])
    # configure finite generation of triggers (not infinite)
    ni_pilatuschan.write_attribute('SampleMode','Finite')
    # configure sampling timing type to implicit
    ni_pilatuschan.write_attribute('SampleTimingType', 'Implicit')
    # set the value for the idle state
    ni_pilatuschan.write_attribute('IdleState', 'Low')
    # configure minimum possible initial delay in ticks
    # for multiple trigger generation
    ni_pilatuschan.write_attribute('InitialDelayTicks', ni_cfg_dict[DET_DELAY])
    # configure minimum low interval in ticks
    ni_pilatuschan.write_attribute('LowTicks', ni_cfg_dict[DET_LOW])
    # configure minimum high interval in ticks
    ni_pilatuschan.write_attribute('HighTicks', ni_cfg_dict[DET_HIGH])


    # CONFIGURE NI 660X INTERNAL CONNECTIONS
    # CRYPTIC RIGHT NOW...
    # output of ctr4 to output of ctr1
    ni_dev.command_inout('ConnectTerms',['/Dev1/PFI20', '/Dev1/PFI32', 'DoNotInvertPolarity'])
    # indexer X4 phase A
    # ni_dev.command_inout('ConnectTerms',['/Dev1/PFI39', '/Dev1/PFI12', 'DoNotInvertPolarity'])
    # timebase
    # ni_dev.command_inout('ConnectTerms',['/Dev1/PFI36', '/Dev1/PFI8', 'DoNotInvertPolarity'])

    ni_poschan.command_inout('Start')
    ni_shutterchan.command_inout('Start')
    ni_pilatuschan.command_inout('Start')


def ni660x_tango_set_channel_idle_state(ni_chan, highlow):
    ni_chan.command_inout('Stop')
    ni_chan.write_attribute('IdleState', highlow)
    ni_chan.command_inout('Start')
