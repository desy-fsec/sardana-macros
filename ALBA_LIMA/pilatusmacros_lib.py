"""
    Macros for data acquisition with Pilatus specific DS
"""

import PyTango
#from macro import Macro, Type
from sardana.macroserver.macro import Macro, Type

class pilatus_set_first_image(Macro):
    """Set the image number of first image"""
    
    param_def =  [['dev',Type.String, None, 'Device name or alias'],
                  ['nb_first',Type.Integer, None, 'Image number for first image']]
    
    def run(self,dev,ifirst):
        pilatus = PyTango.DeviceProxy(dev)
        pilatus.write_attribute('nb_first_image', ifirst)

class pilatus_get_first_image(Macro):
    """Get the image number of first image"""
    
    param_def =  [['dev',Type.String, None, 'Device name or alias']]

    result_def =  [['nb_first',Type.Integer, None, 'Image number for first image']]
    
    def run(self,dev):
        pilatus = PyTango.DeviceProxy(dev)
        return pilatus.read_attribute('nb_first_image').value