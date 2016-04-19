from sardana.macroserver.macro import Macro, Type
import time
import taurus

class lima_cfg_saving(Macro):
    """Configure saving parameters of the Active Lima Tango Device"""
    
    env = ('ActiveLimaTangoDevice',)

    param_def = [
        ['saving_directory', Type.String, None, "Saving's directory."],
        ['saving_prefix', Type.String, None, "Saving's prefix."],
        ['saving_suffix', Type.String, None, "Saving's suffix."],
        ['saving_format', Type.String, None, "Saving's format."], ]
    
    def run(self, saving_directory, saving_prefix, saving_suffix, saving_format):
        lima_dev_name = self.getEnv('ActiveLimaTangoDevice')
        lima_dev = taurus.Device(lima_dev_name)

        lima_dev['saving_directory'] = saving_directory
        lima_dev['saving_prefix'] = saving_prefix
        lima_dev['saving_suffix'] = saving_suffix
        lima_dev['saving_format'] = saving_format
        self.info('Lima saving: %s %s %s %s' % (saving_directory, saving_prefix, saving_suffix, saving_format))

class lima_cfg_acq(Macro):
    """Configure acquisition parameters of the Active Lima Tango Device"""
    
    env = ('ActiveLimaTangoDevice',)

    param_def = [
        ['acq_exp_time', Type.Float, None, "Acquisition's time."],
        ['acq_nb_frames', Type.Integer, None, "Acquisition's number of frames."],
        ['acq_trigger_mode', Type.String, 'INTERNAL_TRIGGER', "Acquisition's trigger mode."], ]

    def run(self, acq_exp_time, acq_nb_frames, acq_trigger_mode):
        lima_dev_name = self.getEnv('ActiveLimaTangoDevice')
        lima_dev = taurus.Device(lima_dev_name)

        lima_dev['acq_expo_time'] = acq_exp_time
        lima_dev['acq_nb_frames'] = acq_nb_frames
        lima_dev['acq_trigger_mode'] = acq_trigger_mode
        self.info('Lima acq: %f %d %s' % (acq_exp_time, acq_nb_frames, acq_trigger_mode))

class lima_start_acq(Macro):
    """Prepare and Start acquisition of the Active Lima Tango Device"""
    
    env = ('ActiveLimaTangoDevice',)

    param_def = [
        ['waitAcq', Type.Boolean, True, "Wait until Acquisition finishes."], ]

    def prepare(self, waitAcq):
        lima_dev_name = self.getEnv('ActiveLimaTangoDevice')
        self.lima_dev = taurus.Device(lima_dev_name)

    def run(self, waitAcq):
        self.wait_acq()
        self.info('Preparing Lima acquisition.')
        self.lima_dev.prepareAcq()
        self.info('Starting Lima acquisition.')
        self.lima_dev.startAcq()
        if waitAcq:
            self.info('Waiting for the acquisition to finish.')
            self.wait_acq()

    def wait_acq(self):
        transient_corbas = 0
        while transient_corbas < 10:
            try:
                if self.lima_dev.acq_status.lower() != 'running':
                    return
                time.sleep(1)
            except:
                transient_corbas += 1


    def on_abort(self):
        # INFO SEEMS NOT AVAILABLE ON THIS METHOD, THERE IS AN EXCEPTION SAYING THAT
        # 'MARCO IS ALREADY STOPPED'
        #self.info('Aborting acquisition')
        
        # NONE OF THESE WAYS TO STOP THE ACQUISITION WORKED
        # USING JIVE OR ANOTHER PROCESS WORKS
        #self.lima_dev.stopAcq()
        #taurus.Device('bl13/eh/pilatuslima').stopAcq()
        #taurus.Device('bl13/eh/pilatuslima').command_inout('stopAcq')
        return

class lima_stop_acq(Macro):
    """Start acquisition of the Active Lima Tango Device"""
    
    env = ('ActiveLimaTangoDevice',)

    def run(self):
        lima_dev_name = self.getEnv('ActiveLimaTangoDevice')
        lima_dev = taurus.Device(lima_dev_name)
        lima_dev.stopAcq()
