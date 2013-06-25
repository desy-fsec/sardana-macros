import time
from sardana.macroserver.macro import Type
from taurus.console.table import Table

class SoftShutterController:

    def init(self):
        self.debug("SoftShutterController.init() entering...")
        self.fs = self.getDevice("fs") #taurus device of photon shutter
        self.debug("SoftShutterController.init() leaving...")

    def prepareShutter(self):
        self.debug("SoftShutterController.prepareShutter() entering...")
        self.fs.write_attribute("time", self.acqTime)
        self.debug("SoftShutterController.prepareShutter() leaving...")

    def exposureShutter(self):
        self.debug("SoftShutterController.exposureShutter() entering...")
        self.fs.write_attribute("value",2)
        self.debug("SoftShutterController.exposureShutter() leaving...")

    def openShutter(self):
        self.debug("SoftShutterController.openShutter() entering...")
        self.fs.write_attribute("value",1)
        self.debug("SoftShutterController.openShutter() leaving...")

    def closeShutter(self):
        self.debug("SoftShutterController.closeShutter() entering...")
        self.fs.write_attribute("value",0)
        self.debug("SoftShutterController.closeShutter() leaving...")

class MntGrpController:
    
    def init(self, macro):
        self.macro = macro

    def prepareMntGrp(self):
        self.macro.debug("MntGrpController.prepareMntGrp() entering...")
        mntGrpName = self.macro.getEnv('ActiveMntGrp')
        self.mntGrp = self.macro.getObj(mntGrpName, type_class=Type.MeasurementGroup)
        cfg = self.macro.mntGrp.getConfiguration()
        cfg.prepare()
        self.mntGrp.setIntegrationTime(self.mntGrpAcqTime)
        self.macro.debug("MntGrpController.prepareMntGrp() leaving...")
        
    def acquireMntGrp(self):
        self.macro.debug("MntGrpController.acquireMntGrp() entering...")
        self.countId = self.mntGrp.start()
        self.macro.debug("MntGrpController.acquireMntGrp() leaving...")

    def waitMntGrp(self):
        self.macro.debug("MntGrpController.waitMntGrp() entering...")
        self.mntGrp.waitFinish(id=self.countId)
        self.macro.debug("MntGrpController.waitMntGrp() leaving...")

    #old way to retrieve results, since table is formatted, it is not very useful
    #def getMntGrpResults(self):
        #data = self.mntGrp.getValues()
        #headerCounters, headerValues = [], []
        #for ch_info in self.mntGrp.getChannelsInfo():
            #headerCounters.append(ch_info.label)
            #if ch_info.shape > [1]:
                #headerValues.append(ch_info.shape)
            #else:
                #headerValues.append(data.get(ch_info.full_name))

        #table = Table([headerValues], row_head_str=headerCounters, row_head_fmt='%*s',
                      #col_sep='  =  ')
        #results = table.genOutput()
        #return results
        
    def getMntGrpResults(self):
        self.macro.debug("MntGrpController.getMntGrpResults() entering...")
        channels = self.mntGrp.getChannels()
        values = self.mntGrp.getValues()
        
        self.macro.debug("channels: " + repr(channels))
        self.macro.debug("values: " + repr(values))
        results = [ch["name"] + " " + str(values[ch["full_name"]]) for ch in channels]
        resultsStr = " ".join(results)
        self.macro.debug("MntGrpController.getMntGrpResults() leaving...")
        return resultsStr
            
        
class FeController:
    
    def init(self, macro):
        self.macro = macro
        self.fe = self.getDevice("fe")

    def isFeOpened(self):
        self.macro.debug("FeController.feStatus() entering...")
        isOpened = False
        if self.fe.read_attribute("value").value == 1:
            isOpened = True
        self.macro.debug("FeController.feStatus() returning %d ..." % isOpened)
        return isOpened
        
    def openFe(self):
        self.macro.debug("FeController.openFe() entering...")
        self.fe.write_attribute("value", 1)
        isOpened = False
        for i in range(10):
            time.sleep(1)
            if self.fe.read_attribute("value").value == 1:
                isOpened = True
        self.macro.debug("FeController.openFe() returning %d ..." % isOpened)
        return isOpened
        
    def closeFe(self):
        self.macro.debug("FeController.closeFe() entering...")
        self.fe.value = 0
        isClosed = True
        for i in range(10):
            time.sleep(1)
            if self.fe.read_attribute("value").value == 0:
                isClosed = True
        self.macro.debug("FeController.closeFe() returning %d ..." % isClosed)
        return isClosed
