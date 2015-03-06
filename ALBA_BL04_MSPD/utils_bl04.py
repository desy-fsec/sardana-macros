import taurus
from sardana.macroserver.macro import Macro, Type

# Default Configuration used in the NI Devices
NI_DEFAULT_CONFIG = {
    # Dev1
    'bl04/io/ibl0403-dev1-ctr0':['CICountEdgesChan', 'i15'],
    'bl04/io/ibl0403-dev1-ctr1':['CICountEdgesChan', 'unused1'],
    'bl04/io/ibl0403-dev1-ctr2':['CICountEdgesChan', 'unused2'],
    'bl04/io/ibl0403-dev1-ctr3':['CICountEdgesChan', 'unused3'],
    'bl04/io/ibl0403-dev1-ctr4':['CIAngEncoderChan', 'hp_som'],
    'bl04/io/ibl0403-dev1-ctr5':['CIAngEncoderChan', 'pd_oc'],
    'bl04/io/ibl0403-dev1-ctr6':['CIAngEncoderChan', 'hp_sz'],
    'bl04/io/ibl0403-dev1-ctr7':['CIAngEncoderChan', 'hp_sxd'],
    # Dev2
    'bl04/io/ibl0403-dev2-ctr0':['CICountEdgesChan', 'i14'],
    'bl04/io/ibl0403-dev2-ctr1':['CICountEdgesChan', 'i1'],
    'bl04/io/ibl0403-dev2-ctr2':['CICountEdgesChan', 'i2'],
    'bl04/io/ibl0403-dev2-ctr3':['CICountEdgesChan', 'i3'],
    'bl04/io/ibl0403-dev2-ctr4':['CICountEdgesChan', 'i4'],
    'bl04/io/ibl0403-dev2-ctr5':['CICountEdgesChan', 'i5'],
    'bl04/io/ibl0403-dev2-ctr6':['CICountEdgesChan', 'i6'],
    'bl04/io/ibl0403-dev2-ctr7':['CICountEdgesChan', 'i7'],
    # Dev3
    'bl04/io/ibl0403-dev3-ctr0':['CICountEdgesChan', 'i8'],
    'bl04/io/ibl0403-dev3-ctr1':['CICountEdgesChan', 'i9'],
    'bl04/io/ibl0403-dev3-ctr2':['CICountEdgesChan', 'i10'],
    'bl04/io/ibl0403-dev3-ctr3':['CICountEdgesChan', 'i11'],
    'bl04/io/ibl0403-dev3-ctr4':['CICountEdgesChan', 'i12'],
    'bl04/io/ibl0403-dev3-ctr5':['CICountEdgesChan', 'i13'],
    'bl04/io/ibl0403-dev3-ctr6':['COPulseChanTime', 'it'],
    'bl04/io/ibl0403-dev3-ctr7':['COPulseChanTime', 'it_pair']}

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


class ni_default(Macro):
    """
    Macro to restore the NI device to default values
    """
    param_def = [
        ["dev", Type.String, None, "Device to Change Application Type"]]

    def run(self, dev):
         application_type = NI_DEFAULT_CONFIG[dev][0]
         task_name = NI_DEFAULT_CONFIG[dev][1]
         setNiConfig(dev, application_type, task_name)
         self.debug("NI660X is ready to work in %s Type",application_type)


class count2pulseWidth(Macro):

    param_def = [
        ["dev", Type.String, None, "Device to Convert to PulseWidthMeas Type"]
        ]

    def run(self, dev):
		
         dev = taurus.Device(dev)
         property = {'applicationType':['CIPulseWidthChan']}
         dev.put_property(property)
         self.info("NI660X is ready to work with CIPulseWidthChan Type")
         dev.init()
         dev.set_timeout_millis(3000)


class pulseWidth2count(Macro):

    param_def = [
        ["dev", Type.String, None, "Device to Convert to CountEdgesChan Type"]
        ]


    def run(self, dev):
         dev = taurus.Device(dev)
         property = {'applicationType':['CICountEdgesChan']}
         dev.put_property(property)
         self.info("NI660X is ready to work with CICountEdgesChan Type")
         dev.init()
         dev.set_timeout_millis(3000)

