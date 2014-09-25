import PyTango
import os
import taurus
from sardana.macroserver.macro import *


PARAMS = ['RESC', 'CLCK', 'TPEA', 'GAIF', 'GAIN', 'RESL', 'TFLA', 'TPFA', 
        'PURE', 'RTDE', 'MCAS', 'MCAC', 'SOFF', 'AINP', 'INOF', 'GAIA', 'CUSP', 'PDMD', 
        'THSL', 'TLLD', 'THFA', 'DACO', 'DACF', 'RTDS', 'RTDT', 'BLRM', 'BLRD', 'BLRU', 
        'GATE', 'AUO1', 'PRET', 'PRER', 'PREC', 'PRCL', 'PRCH', 'HVSE', 'TECS', 'PAPS', 
        'SCOE', 'SCOT', 'SCOG', 'MCSL', 'MCSH', 'MCST', 'AUO2', 'TPMO', 'GPED', 'GPIN', 
        'GPME', 'GPGA', 'GPMC', 'MCAE', 'VOLU', 'CON1', 'CON2', 'BOOT', 'TPEA', 'GAIF', 
        'GAIN', 'RESL', 'TFLA', 'SOFF', 'INOF', 'CUSP', 'THSL', 'TLLD', 'THFA', 'DACO', 
        'DACF', 'RTDS', 'RTDT', 'BLRD', 'BLRU', 'AUO1', 'PRET', 'PRER', 'PREC', 'PRCL', 
        'PRCH', 'HVSE', 'TECS', 'MCSL', 'MCSH', 'MCST', 'AUO2', 'GPIN' ]


PARAMS_IN_DS = [['PRET','AcquisitionTime'],['AUO1','AuxOut1'],['CLCK','Clock']
                , ['GAIA','CoarseGain'],['CON1','Con1'],['GAIF','FineGain']
                , ['TFLA','FlatTopWidth'], ['MCAC','MCAC'], ['TPEA','PeakingTime']
                , ['PURE','PileupReject']]





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
                
                
                
                






class amptekLoadConf(Macro):
    '''Loads the ASCI configuration paramters to the Amptek PX5 . Commands are 
    send via the AmptekPX5 Tango device server. Each line of the configuration 
    file must obey the following syntax: 
    <PARAM>=<VALUE>;

    The configruation parameters are docummented in the "DP5 Programming Guide"
    (page 78) which could be found in:
    /beamlines/bl22/controls/doc/DP5_Programmers_Guide_A5.pdf'''
    
    param_def = [["path", Type.String, None, "Path to the configuration file"]]
    
    
    def conditionLine(line):
        '''Does early conditioning of the configuration line e.g. strip white
        characters, new line character, etc...
        '''
        line = line.rstrip('\n') # eliminate the new line character
        line = line.strip() # eliminate white space characters 
        return line

    def validateLine(line):
        '''Validates configuration line if obeys the required syntax: 
        <PARAM>=<VALUE>;
        '''
        valid = True
        msgs = []
        if not line.endswith(';'):
            msgs.append('no ";" character at the end of the line')
        else:
            # right stripping the ';' to facilitate validation
            line = line.rstrip(';')
        # checking if line contains configuration
        if not ('=' in line):
            msgs.append('line is not an assignment')
        else:
            param, value = line.split('=')
            # checking if configuration contains value
            if len(param) == 0:
                msgs.append('no param is present')
            if len(value) == 0:
                msgs.append('no value is present')
        if len(msgs) > 0:
            valid = False
        return valid, msgs
    

    def prepare(self, *args, **kwargs):
        ds_name = self.getEnv('AmptekPX5TangoDevice')
        
        self.path = args[0]
        if not os.path.isfile(self.path):
            self.error("The following path: %s does not point to a file" % path)
        self.amptek = taurus.Device(ds_name)
        try:
            self.amptek.ping()
        except PyTango.DevFailed, e:
            self.debug(e)
            msg = ('Communication with AmptekPX5 Tango DS failed ("%s" ' +
                   'device did not respond to ping)') % ds_name 
            raise Exception(msg)

    def run(self, *args, **kwargs):
        with open(self.path, "r") as conf_file:
            for i, line in enumerate(conf_file):
                self.debug(line)
                line = conditionLine(line)
                valid, details = validateLine(line)
                if not valid:
                    line_nr = i + 2
                    msg = 'Line nr %d (%s) is not valid. Skipping it...' %\
                          (line_nr, line)
                    self.warning(msg)
                    self.output('Details: ')
                    for d in details:
                        self.output(' *) ' + d)
                    continue
                # TODO: For the moment we send one parameter per one cmd 
                # execution but we could compose bigger sets of configuration 
                # parameters and send them at once. Be careful with the max size
                # of the communication packet to amptek ~1400 bytes.
                line = line.rstrip(';') # ';' character is not accepted by cmd
                argin = [line]
                try:
                    self.amptek.SetTextConfiguration(argin)
                    
                except PyTango.DevFailed, e:
                    self.error("Error while sending %s configuration" % line)
                    dev_error = e.args[0]
                    if dev_error.reason == 'AMPTEK_ERROR':
                        self.output('Details: %s' % dev_error.desc)
                        break
                    else:
                        self.error(e)
                        return
                except Exception, e:
                    self.debug(e)
                    raise Exception('unexpected error')
                self.info('%s configuration was sent to the AmptekPX5' % line)
                
                try:
                    self.dev = PyTango.DeviceProxy(ds_name)
                    for params_in_ds in PARAMS_IN_DS:
                         if argin[0] in params_in_ds:
                            self.dev.write_attribute(argin[0],argin[1])
                except   PyTango.DevFailed, e:
                    self.error("Error while sending %s configuration on DS" % line)
                

class amptekSaveConf(Macro):
    '''Saves the ASCI configuration paramters read from the Amptek PX5 to a text
    file. Read commands are send via the AmptekPX5 Tango device server. 
    File will be stored with one line per configuration parameter in the 
    following syntax: <PARAM>=<VALUE>;

    The configruation parameters are docummented in the "DP5 Programming Guide"
    (page 78) which could be found in:
    /beamlines/bl22/controls/doc/DP5_Programmers_Guide_A5.pdf'''
    
    param_def = [["path", Type.String, None, "Path to the configuration file"],
                 ["verbose", Type.Boolean, False, 
                             "Whether output to the console the configuration"]]

    def prepare(self, *args, **kwargs):
        ds_name = self.getEnv('AmptekPX5TangoDevice')
        #TODO: check if we have permissions to write there
        self.path = args[0]
        self.verbose = args[1]
        if not os.path.isfile(self.path):
            #TODO: change it an interactive macro and ask for permission
            msg = 'This file (%s) already exists it will be overriden' %\
                  self.path
            self.warning(msg)
        self.amptek = taurus.Device(ds_name)
        try:
            self.amptek.ping()
        except PyTango.DevFailed, e:
            self.debug(e)
            msg = ('Communication with AmptekPX5 Tango DS failed ("%s" ' +
                   'device did not respond to ping)') % ds_name 
            raise Exception(msg)

    def run(self, *args, **kwargs):
        with open(self.path, "w") as conf_file:
            for param in PARAMS:
                argin = [param]
                try:
                    argout = self.amptek.GetTextConfiguration(argin)
                except PyTango.DevFailed, e:
                    exiting = False
                    self.error("Error while sending %s configuration" % line)
                    dev_error = e.args[0]
                    if dev_error.reason == 'AMPTEK_ERROR':
                        self.output('Details: %s' % dev_error.desc)
                    else:
                        self.error(e)
                        return
                except Exception, e:
                    self.debug(e)
                    raise Exception('unexpected error')
                self.debug(argout)
                conf = argout[0]
                line = conf + ';' + '\n'
                if self.verbose:
                    self.output(line)
                conf_file.write(line)

             
             
class setROI(Macro):
    """Macro to configure the AmptekPX5 Hardware SCAs"""

    param_def = [
        ['sca_list',ParamRepeat(['Number', Type.Integer, None, 'SCA channel'],
                     ['Low_Value', Type.Integer, None, 'Low threshold '],
                     ['High_Value', Type.Integer, None, 'High threshold'],
                     min=1, max=6), None, 
         'List of SCA configuration, example: sca1 100 800']]

    dev_name = 'bl22/eh/amptekpx5-01'
    #dev_name = "amptekpx5/devel/1"
 
    def run(self, *sca_list):
        dev_name = self.getEnv('AmptekPX5TangoDevice')
        dev = PyTango.DeviceProxy(dev_name)
        self.info('Configuring the ICR...')
        cmd = ['AUO1=ICR']
        cmd2 = ['CON1=AUXOUT1']
        dev.setTextConfiguration(cmd)
        dev.setTextConfiguration(cmd2)
        mcac = int(dev.read_attribute('MCAC').value)
        self.info('Configuring the TCR')
        #self._setSCA(dev, 1, 0, mcac)
        chn_list = []
        for index, low_value, high_value in sca_list:
            if index<0 or low_value<0 or high_value<0:
                raise ValueError('The values must be positive')
            if high_value > mcac:
                high_value = mcac
            index +=1 #the first sca we used to the TCR
            chn_list.append(index)
            self._setSCA(dev, index-1, low_value, high_value)
        #for index in range(2,8):
        #    if index in chn_list:
        #        continue
        #    self._setSCA(dev, index-1, 0 , 0)

    def _setSCA(self,dev, index, low=0, high=8191):
        scai = 'SCA%i' %index
        scailt = scai+"LT"
        scaiht = scai+"HT"
        dev.write_attributes([(scailt, low),(scaiht,high)])


   