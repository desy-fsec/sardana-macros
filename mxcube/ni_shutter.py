from sardana.macroserver.macro import Macro, Type
import PyTango


class ni_shutter(Macro):
    """
    This macro is used to operate a shutter via a ni660x channel.
    The channel name is expected to be accessible as an environment
    variable (NIShutterChannel)
    """
    param_def = [['open_close', Type.String, None, 'open/close the shutter']]

    def prepare(self, open_close):
        self.idle_state = None
        open_close = open_close.lower()
        if open_close == 'open':
            self.idle_state = 'Low'
        elif open_close == 'close':
            self.idle_state = 'High'
        else:
            raise Exception('Only open/close keywords allowed.')

        ni_channel_name = self.getEnv('NIShutterChannel')
        self.channel = PyTango.DeviceProxy(ni_channel_name)

    def run(self):
        self.channel.command_inout('Stop')
        self.channel.write_attribute('IdleState', self.idle_state)
        self.channel.command_inout('Start')



