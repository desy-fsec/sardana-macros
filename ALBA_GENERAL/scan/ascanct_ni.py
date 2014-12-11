from sardana.macroserver.macro import macro, Macro, Type
import PyTango


class ascanct_ni(Macro):
    """
    The macro fixes the wrong value of the first point on the continuous 
    scan with the NI660X as a Counter/Timer. It introduces the configuration of 
    one trigger more in the post configuration hook and configures the NI660X 
    counters to take one more sample. 
    
    It use the enviroment variable NiCTDevice. This variable is a list of the 
    NI660X counters that will use during the scan. 
    """
    param_def = [['motor', Type.Moveable, None, 'Moveable name'],
                 ['start_pos', Type.Float, None, 'Starting position'],
                 ['end_pos', Type.Float, None, 'Ending pos value'],
                 ['nr_of_points', Type.Integer, None, 'Nr of scan points'],
                 ['point_time', Type.Float, None, 'Time interval reserved for ' + 
                                                   'each scan point [s].'],
                 ['acq_time', Type.Float, 99, 'Acquisition time per scan point. ' +
                      'Expressed in percentage of point_time. Default: 99 [%]'],
                 ['samp_freq', Type.Float, -1, 'Sampling frequency. ' + 
                                        'Default: -1 (means maximum possible)']]

    
    def __init__(self, *args, **kwargs):
        super(ascanct_ni,self).__init__(*args, **kwargs)
        self.hooks = []
        
    def _postConfigureHook(self):
        if self._post_configure_hook !=None:
            self.debug('Executing user post configure hooks') 
            self._post_configure_hook()
        
        self.debug('Executing NI660X post configure hooks') 
        dev_triggers = self.getEnv('TriggerDevice')
        if type(dev_triggers) == str:
            dev_triggers = [dev_triggers]
        
        for dev_trigger in dev_triggers:
            dev = PyTango.DeviceProxy(dev_trigger)
            self.triggers = dev.read_attribute('SampPerChan').value
            dev.write_attribute('SampPerChan',self.triggers+1)
            
        counters =self.getEnv('NiCTDevice')
        for counter in counters:
            dev = PyTango.DeviceProxy(counter)
            dev.write_attribute('nrOfTriggers',self.triggers+1)
            dev.write_attribute('extraTrigger', True)
        
    def _setHooks(self):
        self.debug(self.hooks)
        self._post_configure_hook = None
        for hook in self.hooks:
            try:
                hook[1].index('post-configuration')
                self._post_configure_hook = hook[0]
                i = self.hooks.index(hook)
                self.hooks.pop(i)
                break
            except ValueError:
                continue
        new_hook = (self._postConfigureHook, ['post-configuration'])
        self.hooks.append(new_hook)
     
    def prepare(self,*args):
        self.ascanct_macro, _ = self.createMacro("ascanct",*args)
        self.extraRecorder = self.ascanct_macro.extraRecorder
    
    
    def run(self,*args):
        
        #Commented to adapt to ascanct
        self._setHooks()
        self.ascanct_macro.hooks = self.hooks
        self.runMacro(self.ascanct_macro)
        
        counters =self.getEnv('NiCTDevice')
        for counter in counters:
            dev = PyTango.DeviceProxy(counter)
            dev.write_attribute('nrOfTriggers',self.triggers)
            dev.write_attribute('extraTrigger', False)
        
