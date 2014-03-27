import PyTango
from sardana.macroserver.macro import Macro, Type

class AmConf(Macro):
    """
    How to use it:
    AmConf (without paramters): Return the value of each parameter. 
    AmConf PT  (read the PeakingTime)
    AmConf FG 0.6  (write the FineGain)
    
    
    To see the valid parameters: AmConf help
    
    """ 
    
    param_def = [
                 ['attr', Type.String, 'None', 'Name of attribute'],
                 ['value', Type.String, 'None', 'Value for attribute']]
    
    # Table of supported attributes, ['alias', 'attr name', 'writeable']
    params = [['CG', 'CoarseGain', True, 'int'],
              ['FG', 'FineGain', True, 'float'],
              ['PT', 'PeakingTime', True, 'float'],
              ['FTW', 'FlatTopWidth', True, 'float'],
              ['TG', 'TotalGain', False, 'float'],   
              ['MCAC','MCAC', True, 'int'],
              ['PUR', 'PileupReject', True, 'str'],
              ['CLK', 'Clock', True, 'int']]
              
    
    def prepare(self, *args, **kwargs):
        ds_name = self.getEnv('AmptekPX5TangoDevice')
        if ds_name == None:
            msg = ('You must defiene the enviroment variable: '
                   'AmptekPX5TangoDevice with the name of the device.')
            raise Exception(msg)

        self.device = PyTango.DeviceProxy(ds_name)
            
        
    def run(self, attribute, value):
        attribute = attribute.lower()
        if attribute == 'help':
            self._printList('help');
            return
        elif attribute == 'none':
            self._printList('values')
            return
        
        for param, name, writable, data_type in self.params:
            if attribute == param.lower():
                break
        else:
            msg=('The paramter (%s) is not valid. Use AmConf help to see the '
                ' valid paramters' %(attribute.upper()))
            raise Exception(msg)

      
        if value == 'None':
              result = self._getValue(name)
              self.output('%s = %s' %(param, result))
        else:
            if writable:
                self._setValue(name, value, data_type)
            else:
                raise Exception('This attribute is not writable.')
                      
    def _getValue(self, attr):
        result = self.device.read_attribute(attr).value             
        self.debug('AmConf::_getvalue(%s) result:%s' %(attr, result))
        return result

    
    def _setValue(self, attr, value, data_type):
        if data_type == 'int':
            value = int(value)
        elif data_type == 'float':
            value = float(value)
        elif data_type == 'str':
            pass
        else:
            msg = ('The params valiable is wrong, verified the macro code')
            raise Exception(msg)

        self.device.write_attribute(attr, value)
        self.debug('AmConf::_setvalue(%s,%s) :' %(attr, value))
        result = self._getValue(attr)
        return result
        
    def _printList(self, op):
        if op == 'help':
            msg = ('The list of attribute is:[Parameter, Name, Writable]')
            self.output(msg)

        for attr, name, writable, data_type in self.params:
            if op == 'help':
                msg = ('%s, %s, %s, %s' %(attr, name, writable, data_type))
                self.output(msg)
            elif op == 'values':
                result = self._getValue(name)
                self.output('%s = %s ' %(attr,result))



             
             
