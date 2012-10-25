"""
    Macros for data acquisition with LimaCCDs DS
"""

import PyTango
import os, errno
import time
import functools

from sardana.macroserver.macro import Macro, Type, ParamRepeat



def catch_error(meth):
    @functools.wraps(meth)
    def _catch_error(self, *args, **kws):
        try:
            return meth(self, *args, **kws)
        except Exception, e:
            self.error("Could not comunicate with %s. " +
                       "Check if device server is exported.\n" % args[0])
            self.debug(e)
            raise e
    return _catch_error



class lima_status(Macro):
    """Returns device and acquisition status."""

    param_def =  [['dev',Type.String, None, 'Device name or alias']]
    result_def =  [['state_and_status',Type.String, None, 
                    'Device State and Acquisition Status']]

    @catch_error
    def run(self,dev):
        lima = PyTango.DeviceProxy(dev)
        state = '%s %s' % (lima.State(), 
                           lima.read_attribute('acq_status').value)
        return state



class lima_saving(Macro):
    """Configure data storage."""

    param_def = [['dev',Type.String, None, 'Device name or alias'],
                 ['BaseDir', Type.String, None, 
                  'Base directory to store data.'],
                 ['Prefix', Type.String, None, 'Prefix for the experiment.'],
                 ['Format', Type.String, 'EDF', 'File format'],
                 ['Autosave' , Type.Boolean, True, 
                  'Flag to save all frames automatically']]

    @catch_error
    def run(self,dev,basedir,prefix,fileformat,auto):
        lima = PyTango.DeviceProxy(dev)
        if auto:
            lima.write_attribute('saving_mode', 'AUTO_FRAME')
        else:
            lima.write_attribute('saving_mode', 'MANUAL')
            
        if not os.path.exists(basedir):
            try:
                os.makedirs(basedir)
            except OSError, e:
                if e.errno != errno.EEXIST:
                    raise

        lima.write_attribute('saving_directory', basedir)
        lima.write_attribute('saving_prefix', prefix)
        lima.write_attribute('saving_format', fileformat)



class lima_prepare(Macro):
    """Prepare a set of NF frames with Texp exposure time and Tlat latency time.
Trigger modes are:
  INTERNAL_TRIGGER    EXTERNAL_TRIGGER_MULTI    EXTERNAL_START_STOP
  EXTERNAL_TRIGGER    EXTERNAL_GATE"""

    param_def =  [['dev',Type.String, None, 'Device name or alias'],
                  ['Texp', Type.Float, 1.0, 'Exposure time.'],
                  ['Tlat', Type.Float, 0.0, 'Latency time.'],
                  ['NF', Type.Integer, 1, 'Number of frames.'],
                  ['Trig', Type.String, 'INTERNAL_TRIGGER', 'Trigger mode.']]

    @catch_error
    def run(self,dev,Texp,Tlat,NF,Trig):
        lima = PyTango.DeviceProxy(dev)

        TrigList = ['INTERNAL_TRIGGER'
                    ,'EXTERNAL_TRIGGER'
                    ,'EXTERNAL_TRIGGER_MULTI'
                    ,'EXTERNAL_GATE'
                    ,'EXTERNAL_START_STOP']
        
        if Trig not in TrigList:
            self.info("Error, Trigger mode %s not accepted." % Trig)

        lima.write_attribute('acq_trigger_mode', Trig)

        lima.write_attribute('acq_nb_frames', NF)
        lima.write_attribute('acq_expo_time', Texp)
        lima.write_attribute('latency_time', Tlat)

        lima.prepareAcq()



class lima_acquire(Macro):
    """
    Aquire a set of frames
    """

    param_def =  [['dev',Type.String, None, 'Device name or alias']]

    @catch_error
    def run(self,dev):
        lima = PyTango.DeviceProxy(dev)
        lima.startAcq()



class lima_stop(Macro):
    """Aborts acquisition."""

    param_def =  [['dev',Type.String, None, 'Device name or alias']]

    @catch_error
    def run(self,dev):
        lima = PyTango.DeviceProxy(dev)
        lima.stopAcq()



class lima_reset(Macro):
    """Resets lima device server."""

    param_def =  [['dev',Type.String, None, 'Device name or alias']]

    @catch_error
    def run(self,dev):
        lima = PyTango.DeviceProxy(dev)
        lima.reset()



class lima_common_header(Macro):
    """Defines a list of common headers
Example:
    lima_common_header my_device "beam_x=1024|beam_y=1024" 
"""

    param_def =  [['dev',Type.String, None, 'Device name or alias'],
                  ['header', Type.String, None, 'Header definition syntax: key1=value1|key2=value2|key3=value3 ...']]

    @catch_error
    def run(self,dev,header):
        lima = PyTango.DeviceProxy(dev)
        lima.write_attribute('saving_common_header', header.split("|"))
        


class lima_image_header(Macro):
    """Defines a list of image headers
Example:
    lima_image_header my_device "0;beam_x=1024|beam_y=1024" "1;beam_x=1024|beam_y=1024" ...
"""

    param_def =  [['dev',Type.String, None, 'Device name or alias'],
                  ['header_list',
                   ParamRepeat(['header', Type.String, None, 'Header definition syntax: IMAGE_ID;key1=value1|key2=value2|key3=value3 ...']), 
                   None, 'List of header definitions']
                  ]

    @catch_error
    def run(self,*args):
        dev = args[0]
        headers = args[1:]
        lima = PyTango.DeviceProxy(dev)
        lima.write_attribute('saving_header_delimiter', ['=','|',';'])
        lima.setImageHeader(headers)
        


class lima_write_image(Macro):
    """Writes on disk the image with the given ID"""

    param_def =  [['dev',Type.String, None, 'Device name or alias'],
                  ['ImageID',Type.Integer, None, 'ID of image to be written']]

    @catch_error
    def run(self,dev,imageid):
        lima = PyTango.DeviceProxy(dev)
        lima.writeImage(imageid)
 


class lima_getconfig(Macro):
    """Returns the desired parameter value
Parameter list:
    directory    format       expo_time       trigger
    prefix       nb_frames    latency_time    next_image"""

    param_def =  [['dev',Type.String, None, 'Device name or alias'],
                  ['paramIn',Type.String, None, 'Parameter name.']]
    result_def = [['paramOut',Type.String, None, 'Parameter value']]
        
    @catch_error
    def run(self,dev,param):
        lima = PyTango.DeviceProxy(dev)

        Param = {'directory': 'saving_directory',
                 'prefix': 'saving_prefix',
                 'format': 'saving_format',
                 'nb_frames': 'acq_nb_frames',
                 'expo_time': 'acq_expo_time',
                 'latency_time': 'latency_time',
                 'trigger':'acq_trigger_mode',
                 'next_image':'saving_next_number'}

        value = lima.read_attribute(Param[param]).value
        return str(value)



class lima_printconfig(Macro):
    """Prints configuration"""

    param_def =  [['dev',Type.String, None, 'Device name or alias']]

    @catch_error
    def run(self,dev):

        Param = ['directory', 'prefix', 'format', 'nb_frames', 
                 'expo_time', 'latency_time', 'trigger']

        for par in Param:            
            result = self.execMacro(['lima_getconfig',dev,par])
            self.info("%s = %s" % (par,result.getResult()))



class lima_lastbuffer(Macro):
    """Returns the frame Id of last buffer ready"""
    
    param_def =  [['dev',Type.String, None, 'Device name or alias']]
    result_def = [['lastBuffer',Type.Integer, None, 
                   'Frame Id of last buffer ready']]

    @catch_error
    def run(self,dev):
        lima = PyTango.DeviceProxy(dev)
        value = lima.read_attribute("last_image_ready").value
        return value
     


class lima_lastimage(Macro):
    """Returns the image Id of last image saved"""
    
    param_def =  [['dev',Type.String, None, 'Device name or alias']]
    result_def = [['lastImage',Type.Integer, None, 'Id of last image saved']]

    @catch_error
    def run(self,dev):
        lima = PyTango.DeviceProxy(dev)
        value = lima.read_attribute("saving_next_number").value - 1 
        return value 
     


class lima_nextimage(Macro):
    """Set next image number to be saved"""

    param_def =  [['dev',Type.String, None, 'Device name or alias'],
                  ['image_nb',Type.Integer, None, 
                   'next image number to be saved']]

    @catch_error
    def run(self, dev, imgn):
        lima = PyTango.DeviceProxy(dev)
        lima.write_attribute('saving_next_number', imgn)



class lima_set_flip(Macro):
    """Flips image Left-Right and/or Up-Down"""

    param_def =  [['dev',Type.String, None, 'Device name or alias'],
                  ['flipLR',Type.Boolean, None, 'Boolean to flip Left-Right'],
                  ['flipUP',Type.Boolean, None, 'Boolean to flip Up-Down']]

    @catch_error
    def run(self, dev, flipLR, flipUP):
        lima = PyTango.DeviceProxy(dev)
        lima.write_attribute('image_flip', [flipLR, flipUP])
       


class lima_get_flip(Macro):
    """Get image flip configuration"""

    param_def =  [['dev',Type.String, None, 'Device name or alias']]
    result_def = [['flip state',Type.String, None, 
                   'Flip state Left-Right Up-Down']]

    @catch_error
    def run(self,dev):
        lima = PyTango.DeviceProxy(dev)
        value = lima.read_attribute('image_flip').value

        return "%s %s" % (str(value[0]),str(value[1]))



class lima_set_bin(Macro):
    """Set image binning"""

    param_def =  [['dev',Type.String, None, 'Device name or alias'],
                  ['binx',Type.Integer, None, 
                   'Number of pixels to be binned in x axis'],
                  ['biny',Type.Integer, None, 
                   'Number of pixels to be binned in y axis']]

    @catch_error
    def run(self, dev, binx, biny):
        lima = PyTango.DeviceProxy(dev)
        lima.write_attribute('image_bin', [binx, biny])
       


class lima_get_bin(Macro):
    """Get get image binning"""

    param_def =  [['dev',Type.String, None, 'Device name or alias']]
    result_def = [['binning',Type.String, None, 
                   'Number of pixels binned in x and y axis']]

    @catch_error
    def run(self,dev):
        lima = PyTango.DeviceProxy(dev)
        value = lima.read_attribute('image_bin').value

        return "%s %s" % (str(value[0]),str(value[1]))



class lima_take(Macro):
    """Simple macro to take N images."""

    param_def = [['dev',Type.String, None, 'Device name or alias'],
                 ['BaseDir', Type.String, '/tmp', 
                  'Base directory to store data.'],
                 ['Texp', Type.Float, 1.0, 'Exposure time.'],
                 ['Tlat', Type.Float, 0.0, 'Latency time.'],
                 ['NF', Type.Integer, 1, 'Number of frames.'],
                 ['Prefix', Type.String, 'Test', 'Prefix for the experiment.'],
                 ['Format', Type.String, 'EDF', 'File format'],
                 ['Autosave' , Type.Boolean, True, 
                  'Flag to save all frames automatically'],
                 ['Trig', Type.String, 'INTERNAL_TRIGGER', 'Trigger mode.'],
                 ]

    def prepare(self, dev, bdir, texp, tlat, nf, pref, form, auto, trig):
        self.device = dev

    def on_abort(self):
        lima = PyTango.DeviceProxy(self.device)
        lima.stopAcq()

    @catch_error
    def run(self, dev, bdir, texp, tlat, nf, pref, form, auto, trig):
        self.execMacro(['lima_saving', dev, bdir, pref, form, auto]) 
        self.execMacro(['lima_prepare', dev, texp, tlat, nf, trig]) 
        self.execMacro(['lima_acquire', dev]) 
        self.info("Started")
        
        status = self.execMacro('lima_status',dev)
        state, acq = status.getResult().split()
        self.info(acq)

        while True:
            status = self.execMacro('lima_status',dev)
            state, acq = status.getResult().split()
            time.sleep(0.5)
            if acq != 'Running' :
                break
            
        self.info(acq)
