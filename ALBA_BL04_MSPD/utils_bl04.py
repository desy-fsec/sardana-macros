import PyTango
import taurus
from sardana.macroserver.macro import Macro, Type
from sardana.macroserver.macro import *
from subprocess import call
from albaemlib import AlbaEm
import subprocess
import socket

# Default Configuration used in the NI Devices
NI_DEFAULT_CONFIG = {
    # Dev1
    'bl04/io/ibl0403-dev1-ctr0':['CIPulseWidthChan', 'i15'],
    'bl04/io/ibl0403-dev1-ctr1':['COPulseChanTicks', 'Blade3'],
    'bl04/io/ibl0403-dev1-ctr2':['COPulseChanTicks', 'Blade4'],
    'bl04/io/ibl0403-dev1-ctr3':['CIPulseWidthChan', 'ivf1'],
    'bl04/io/ibl0403-dev1-ctr4':['CIPulseWidthChan', 'ivf2'],
    'bl04/io/ibl0403-dev1-ctr5':['CIAngEncoderChan', 'hp_som'],
    'bl04/io/ibl0403-dev1-ctr6':['CIPulseWidthChan', 'ivf3'],
    'bl04/io/ibl0403-dev1-ctr7':['CIAngEncoderChan', 'pd_oc'],
    # Dev2
    'bl04/io/ibl0403-dev2-ctr0':['CIPulseWidthChan', 'i14'],
    'bl04/io/ibl0403-dev2-ctr1':['CIPulseWidthChan', 'i1'],
    'bl04/io/ibl0403-dev2-ctr2':['CIPulseWidthChan', 'i2'],
    'bl04/io/ibl0403-dev2-ctr3':['CIPulseWidthChan', 'i3'],
    'bl04/io/ibl0403-dev2-ctr4':['CIPulseWidthChan', 'i4'],
    'bl04/io/ibl0403-dev2-ctr5':['CIPulseWidthChan', 'i5'],
    'bl04/io/ibl0403-dev2-ctr6':['CIPulseWidthChan', 'i6'],
    'bl04/io/ibl0403-dev2-ctr7':['CIPulseWidthChan', 'i7'],
    # Dev3
    'bl04/io/ibl0403-dev3-ctr0':['CIPulseWidthChan', 'i8'],
    'bl04/io/ibl0403-dev3-ctr1':['CIPulseWidthChan', 'i9'],
    'bl04/io/ibl0403-dev3-ctr2':['CIPulseWidthChan', 'i10'],
    'bl04/io/ibl0403-dev3-ctr3':['CIPulseWidthChan', 'i11'],
    'bl04/io/ibl0403-dev3-ctr4':['CIPulseWidthChan', 'i12'],
    'bl04/io/ibl0403-dev3-ctr5':['CIPulseWidthChan', 'i13'],
    'bl04/io/ibl0403-dev3-ctr6':['COPulseChanTime', 'it'],
    'bl04/io/ibl0403-dev3-ctr7':['COPulseChanTime', 'it_pair'],
    # ibl0402 Dev1
    'bl04/io/ibl0402-dev1-ctr0':['CIPulseWidthChan', 'ivf0'],
    'bl04/io/ibl0402-dev1-ctr1':['CIPulseWidthChan', 'ivfhp'],
    'bl04/io/ibl0402-dev1-ctr2':['CIPulseWidthChan', 'ivfpd'],
    'bl04/io/ibl0402-dev1-ctr3':['CIPulseWidthChan', 'ivfgen'],
    'bl04/io/ibl0402-dev1-ctr4':['CIPulseWidthChan', 'ivfgen2'],
    'bl04/io/ibl0402-dev1-ctr5':['CIPulseWidthChan', 'ivfgen3'],
    #'bl04/io/ibl0402-dev1-ctr6':['CIPulseWidthChan', 'ivfgen4'],
    #'bl04/io/ibl0402-dev1-ctr7':['CIPulseWidthChan', 'ivfgen5']
}

def setNiConfig(dev, app, task):
         dev = taurus.Device(dev)
         prop = {'applicationType':[app]}
         dev.put_property(prop)
         prop = {'taskname':[task]}
         dev.put_property(prop)
         dev.init()


class ni_app_change(Macro):
    """
    Macro to change the application type and the task name in the NI dev 
    selected.
    """
    param_def = [
        ["dev", Type.String, None, "Device to Change Application Type"],
        ["application_type", Type.String, None, "Application Type name"],
        ["task_name", Type.String, None, "TaskName to set"]]

    def run(self, dev, application_type, task_name):
         setNiConfig(dev, application_type, task_name)
         self.debug("NI660X is ready to work in %s Type", application_type)


class restoreNI(Macro):
    
    """
    Macro To restart all the NI channel to the DEfault Values
    """
    
    def run(self):
        self.info("Restoring NI660X ... ")
        for i in NI_DEFAULT_CONFIG:
            self.debug(i)
            dev = i
            application_type = NI_DEFAULT_CONFIG[dev][0]
            task_name = NI_DEFAULT_CONFIG[dev][1]
            setNiConfig(dev, application_type, task_name)
            self.debug("NI660X %s is Restored to %s Type" %(i,application_type))
        self.info("Restored NI660X DONE")



#class ni_default(Macro):
    #"""
    #Macro to restore the NI device to default values
    #"""
    #param_def = [
        #["dev", Type.String, None, "Device to Change Application Type"]]

    #def run(self, dev):
         #application_type = NI_DEFAULT_CONFIG[dev][0]
         #task_name = NI_DEFAULT_CONFIG[dev][1]
         #setNiConfig(dev, application_type, task_name)
         #self.debug("NI660X is ready to work in %s Type",application_type)


#class count2pulseWidth(Macro):
    #"""
    #Macro to change the application type to CIPulseWidthChan
    #"""
    #param_def = [
        #["dev", Type.String, None, "Device to Convert to PulseWidthMeas Type"]
        #]

    #def run(self, dev):
		
         #dev = taurus.Device(dev)
         #property = {'applicationType':['CIPulseWidthChan']}
         #dev.put_property(property)
         #self.debug("NI660X is ready to work with CIPulseWidthChan Type")
         #dev.init()
         #dev.set_timeout_millis(3000)


#class pulseWidth2count(Macro):
    #"""
    #Macro to change the application type to CICountEdgesChan
    #"""
    
    #param_def = [
        #["dev", Type.String, None, "Device to Convert to CountEdgesChan Type"]
        #]


    #def run(self, dev):
         #dev = taurus.Device(dev)
         #property = {'applicationType':['CICountEdgesChan']}
         #dev.put_property(property)
         #self.debug("NI660X is ready to work with CICountEdgesChan Type")
         #dev.init()
         #dev.set_timeout_millis(3000)




@macro()
def restartNotifd(self):
    call(['alba_notifd', 'restart'])

class mntGrpEnableChannel_old(Macro):
    '''
    mntGrpEnableChannel range_test channel1 false

    '''
    param_def = [
            ['MeasurementGroup',Type.String, None, "Measurement Group to work"],
            ['ChannelState',
            ParamRepeat(['channel', Type.String, None, 'Channel to change '
                                                       'state'],
                        ['state',  Type.Boolean, True, 'State, enable:True, '
                                                       'disable:False'],
                        min=1),
            None, 'List of channels/state pairs'],
            ]

    def run(self, mntGrp,  *ChannelsState):
        self.mntGrp = self.getObj(mntGrp, type_class=Type.MeasurementGroup)
        cfg = self.mntGrp.getConfiguration()
        self.debug(cfg)
        ch_names = {}
        for par in ChannelsState:
            for name, state in par:
                ch_names[name] = state
        found = False
        for channel in self.mntGrp.getChannels():
            # 1Sep,2016 FF replace channel['label'] by channel['name'] for the cases of pseudo counters (eg gastemp, ...) 
            #ch = channel['label']   
            ch = channel['name']
	    #self.debug(channel)	            
            #self.info(ch)
            #self.output(ch_names.keys())
            if ch in ch_names.keys():
                channel['enabled'] = ch_names[ch]
                found = True

        if found:
            self.mntGrp.setConfiguration(cfg.raw_data)
            self.info('Setting ActiveMntGrp : %s'%mntGrp)
	    self.setEnv('ActiveMntGrp', mntGrp)

class mntGrpEnableChannel(Macro):

    param_def = [
            ['MeasurementGroup',Type.MeasurementGroup, None, "Measurement Group to work"],
            ['ChannelState',
            ParamRepeat(['channel', Type.ExpChannel, None, 'Channel to change '
                                                       'state'],
                        ['state',  Type.Boolean, True, 'State, enable:True, '
                                                       'disable:False'],
                        min=1),
                        None, 'List of channels/state pairs'],
            ]               

    def run(self, mntGrp,  *ChannelsState):
        elements = mntGrp.getChannelNames()
        ch_names = {}
        enable = []
        disable = []
        not_found = []
        for par in ChannelsState:
            for ch, state in par:
                ch = ch.name
                if ch in elements:
                    if bool(state):
                        enable.append(ch)
                    else:
                        disable.append(ch)
                else:
                    self.debug('Skipped %r Not found in the mntGrp %r'%(ch,str(mntGrp)))
                    not_found.append(ch)	
        if enable:  
            self.execMacro('meas_enable_ch', mntGrp, enable)
            #mntGrp.enableChannels(enable)
        if disable:
            self.execMacro('meas_disable_ch', mntGrp, disable)
            #mntGrp.disableChannels(disable)
        self.debug("MntGrp Used: %r"%mntGrp)
        self.debug("Enabling: %r" %enable)
        self.debug("Disabling: %r" %disable)
        self.debug("Channels not found: %r"%not_found)
#        self.info('Setting ActiveMntGrp : %s'%mntGrp)
#        self.setEnv('ActiveMntGrp', str(mntGrp))


class voltagePolarityAlbaEm(Macro):
    '''
    To be passed to scientists Control
    '''
    param_def = [["xbdev", Type.String, 'None',  "EM id (optional)"],
		 ["invert", Type.String, 'None',  "True/False Invert Voltage Polarity (False=Positive)"],
                 ["ichannel", Type.Integer, 0,  "Channel id (1-4)"]]
                
    def run(self,xbdev,invert,ichannel):
        
        self.debug(invert)
        self.debug(ichannel)
        self.debug(xbdev)

        if xbdev == 'None': #raise Exception("no device given, should be xbhp/xbpd/xbo")
            self.info("WARNING! no device given, should be xbhp/xbpd/xbo")
            return
 
        if xbdev == "xbhp" :  emdev = "ELEM01R42-031-bl04"
        if xbdev == "xbpd" :  emdev = "ELEM01R42-035-bl04"
        if xbdev == "xbo" :  emdev = "ELEM01R42-003-bl04"

        #if ichannel < 1 or ichannel > 4 : raise"Channel number should be between 1 and 4"
        e = AlbaEm(emdev)
        if invert != 'None':
            if invert.lower() == 'true':
	        self.info('Setting Inverting  %s polarity' %emdev)
                config = [['1','YES'],['2','YES'],['3','YES'],['4','YES']]
                #ch=str(ichannel)
                #config = [[ch,'YES']]
                self.warning(config)
            else:
                self.info('Setting Positive %s polarity' %emdev)
                config = [['1','NO'],['2','NO'],['3','NO'],['4','NO']]
            self.debug(config)
            e.setInvs(config)

        state =  e.getInvsAll()
        self.info('%s: %s' %(emdev, state))


class checkNIProcess(Macro):

    """
    Macro that checks how long the NI process are working
    """
    LIMIT_DAYS = 40
    WARNING_DAYS = 30

    def run(self, *args, **kargs):
        print 80 * '#'


        hosts = ['ibl0402', 'ibl0403']
        days = []
        common_cmd = 'ps -e -o pid,comm,etime|grep nimxs'
        #common_cmd = 'ls'
        for host in hosts:
            if host == socket.gethostname():
                cmd = '%s' % common_cmd       
            else:
                cmd = 'ssh sicilia@%s \"%s\"' % (host, common_cmd)

            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            process.wait()
            data, err = process.communicate()
            self.debug(data)
            #get only the date
            day = 0
            if len(data.split()) >1:
              date = data.split()[2]
              if '-' in date:
                  # get only the day
                  day = date.split('-')[0]
                                        

            days.append(day)

        current_days = int(max(days))
        self.info("The NI cards are working for %r days " % current_days)


        # MUST
        if current_days >= self.LIMIT_DAYS:
            self.error("The Ni cards MUST be restarted\nProceding to "
                       "restart... executing 'restartNI' \n")
            self.execMacro('restartNI')
            return

        # Should
        if current_days >= self.WARNING_DAYS:
            self.warning('The Ni cards should be restarted')
            self.warning("Execute 'restartNI' macro to restart them")
            return
        self.info('The Ni are correctly configured')

class ct_custom(Macro):                                                                                         
    """Count for the specified time on the active measurement group"""

    env = ('ActiveMntGrp',)

    param_def = [
       ['integ_time', Type.Float, 1.0, 'Integration time'],
       ['mnt_grp_name', Type.String, 'MntGrp_not_defined', 'MntGrp to use by '
                                                      'default ActiveMntGrp']
    ]

    def prepare(self, integ_time, mnt_grp_name, **opts):
        if mnt_grp_name == 'MntGrp_not_defined':
            mnt_grp_name = self.getEnv('ActiveMntGrp')        
        self.mnt_grp = self.getObj(mnt_grp_name, type_class=Type.MeasurementGroup)
        self.mnt_grp_name = mnt_grp_name

    def run(self, integ_time, mnt_grp_name):
        if self.mnt_grp is None:
            self.error('%r MeasurementGroup does not exist'%self.mnt_grp_name)
            return
        self.debug("Using %s Measurement Group", self.mnt_grp_name)
        self.debug("Counting for %s sec", integ_time)
        self.outputDate()
        self.output('')
        self.flushOutput()

        state, data = self.mnt_grp.count(integ_time)
        names, counts = [], []
        for ch_info in self.mnt_grp.getChannelsEnabledInfo():
            names.append('%s' % ch_info.label)
            ch_data = data.get(ch_info.full_name)
            if ch_data is None:
                counts.append("<nodata>")
            elif ch_info.shape > [1]:
                counts.append(list(ch_data.shape))
            else:
                counts.append(ch_data)

        table = Table([counts], row_head_str=names, row_head_fmt='  %*s',
                      col_sep='  =  ')
        for line in table.genOutput():
            self.output(line)

        # Prepare data result to be extracted by getData()
        self._data = {}
        self._data['mntGrp'] = self.mnt_grp.name
        self._data['integ_time'] = integ_time
        self._data['data'] = zip(names, counts)
        self.debug(self._data)

class ct_manual(Macro):
    param_def = [
            ['acq_time',Type.Float, 1, "Acq_time"],
            ['MeasurementGroup',Type.String, 'None', "Measurement Group to work"],
            ]
    def run(self, act_time, mntGrp):
        a = self.execMacro('ct_custom %r %s' % (act_time, mntGrp))  
        
        try:
            self.info(a.data)
          
            a = a.data
        except:
            self.error('Not data in measurement Grp')
            pass
        self.info(" ".join("%s %s" % tup for tup in a.getData()['data']))

class ct_manual_without_output(Macro):
    param_def = [
            ['acq_time',Type.Float, 1, "Acq_time"],
            ['MeasurementGroup',Type.String, 'None', "Measurement Group to work"],
            ]

    def run(self, act_time, mntGrp):
        a = self.execMacro('ct_custom %r %s' % (act_time, mntGrp))  
        #ct_custom = self.createMacro("ct_custom", act_time, mntGrp)
        #a = self.runMacro(ct_custom)
        try:
            self.info(a.data)
          
            a = a.data
        except:
            self.error('Not data in measurement Grp')
            pass
        self.info(" ".join("%s %s" % tup for tup in a.getData()['data']))


class adlink_setFormula(Macro):
    '''
    Pass 
    '''
    param_def = [["adlink_channel", Type.String, 'None',  "adlink channel"],
                  ['offset',Type.Float, 0, "offset"],
                  ['sign',Type.Float, -1, "sign"],
              ]

    def run(self,adlink_channel, offset, sign):
        PyTango.DeviceProxy(adlink_channel).write_attribute('FORMULA',('%r * value + %r' %(sign, offset)))

class adlink_getFormula(Macro):
    '''
    Pass 
    '''
    param_def = [["adlink_channel", Type.String, 'None',  "adlink channel"],
              ]

    def run(self,adlink_channel):
        formula = PyTango.DeviceProxy(adlink_channel).read_attribute('FORMULA').value
        self.info(formula)
        sign , offset = formula.split('* value +')
        self.debug(sign)
        self.debug(offset)
        return sign, offset

class test_env(Macro):

    def run(self):
        Temp0 = ''
        a = self.getEnv('adlinks')
        self.debug(a)
        self.debug(type(a))
        self.debug(a[0])
        #result = self.execMacro('mythen_getPositions').getResult()               
        #f = eval(result)[0]
        f = eval(self.execMacro('mythen_getPositions').getResult())[0]               
        self.info(f)
        #a = self.execMacro('ct_custom %r %s' %(0.1,'adlink_simple'))
        #a = a.data
        #self.info(a)
        #self.error(a['data'])
        #Temp0 = " ".join("%s %s" % tup for tup in a['data'])
        #self.warning(Temp0)
        chVolt = self.execMacro('ct_custom %r %s' %(0.1,'adlink_simple')).data
        Vnow  = [float(chVolt['data'][1][1]),float(chVolt['data'][2][1]),float(chVolt['data'][3][1]),float(chVolt['data'][4][1])]
        Vname = [chVolt['data'][1][0],chVolt['data'][2][0],chVolt['data'][3][0],chVolt['data'][4][0]]
        self.info(chVolt)
        self.info(Vnow)
        self.info(Vname)
        for _v in range(len(Vnow)) :
            sign,offset=self.execMacro("adlink_getFormula",Vname[_v]).getResult()
            self.info("%d %s %f %f "%(_v,Vname[_v],float(sign),float(offset)))
        #self.setEnv('adlinks',Vnow)
        a = self.getEnv('adlinks')
        self.warning(a)

        #motion=self.getMotion(['pd_msam','pd_mc'])
        #motion.move([0.,f])
