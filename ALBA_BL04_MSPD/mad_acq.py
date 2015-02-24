import time
import math
import PyTango, taurus
from sardana.macroserver.macro import *
from sardana.macroserver.msexception import UnknownEnv
from macro_utils.mad26acq import COUNTERS
from macro_utils.mad26acq import PrepareCountersForStepScanning , InitCounters
from macro_utils.macroutils import SoftShutterController

MNT_GRP = "mad"

class InitCounters(Macro):
  
    param_def = []
    
    def run(self, *args, **kwargs):
        InitCounters() 

class PrepareCountersForStepScanning(Macro):

    param_def = []

    def run(self, *args, **kwargs):
        PrepareCountersForStepScanning()


class mad_ct(Macro, SoftShutterController):
    
    param_def = [["time", Type.Float, 1.0, "Acq time"]]

    def prepare(self, *args, **kwargs):  
        SoftShutterController.init(self)  
                 
    def run(self, *args, **kwargs):
        time = args[0]
        oldMntGrp = self.getEnv("ActiveMntGrp")
        self.setEnv("ActiveMntGrp", MNT_GRP)
        PrepareCountersForStepScanning()
            
        try:
            self._fsShutter = self.getEnv("_fsShutter")
        except UnknownEnv, e:
            self._fsShutter = 0
            
        try:
            if self._fsShutter == 1:
                SoftShutterController.openShutter(self)
            self.execMacro("ct", time)
        finally:
            self.setEnv("ActiveMntGrp", oldMntGrp)
            if self._fsShutter == 1:
                SoftShutterController.closeShutter(self)

class mad_ascan(Macro, SoftShutterController):
    
    param_def = [ ['motor',      Type.Moveable,  None, 'Moveable to move'],
              ['start_pos',  Type.Float,   None, 'Scan start position'],
              ['final_pos',  Type.Float,   None, 'Scan final position'],
              ['nr_interv',  Type.Integer, None, 'Number of scan intervals'],
              ['integ_time', Type.Float,   None, 'Integration time']
             ]
    
    def prepare(self, *args, **kwargs):  
        SoftShutterController.init(self)       
        
         
    def run(self, *args, **kwargs):
        mot = args[0]
        StartPos =  args[1]
        EndPos   =  args[2]
        Npts      = args[3]
        intTim    = args[4]      
        args = (mot.name,StartPos,EndPos,Npts,intTim)
        oldMntGrp = self.getEnv("ActiveMntGrp")
        self.setEnv("ActiveMntGrp", MNT_GRP)
        PrepareCountersForStepScanning()
        
        try:
            self._fsShutter = self.getEnv("_fsShutter")
        except UnknownEnv, e:
            self._fsShutter = 0
        
        try:
            if self._fsShutter == 1:
                SoftShutterController.openShutter(self)
            self.execMacro('ascan', *args)
        finally: 
            self.execMacro("senv", "ActiveMntGrp", oldMntGrp)
            if self._fsShutter == 1:
                SoftShutterController.closeShutter(self)

class madscan(Macro, SoftShutterController):

    mntGrp = "mad_cs"

    motName = "pd_oc"
    
    _fsShutter = None
    
    counterNames = ["i1", "i2", "i3", "i4", "i5", "i6", "i7", "i8", "i9", "i10", "i11", "i12", "i13", "i14"]    
    
    posNames = ["oc"]    
    
    channelNames = counterNames + posNames

    devName = "bl04/io/ibl0403-dev3"
    
    param_def = [["startPos", Type.Float, None, "Starting position"],
                 ["endPos", Type.Float, None, "Ending pos value"],
                 ["speed", Type.Float, None, "deg/min"],
                 ["integTime", Type.Float, -1.0, "Integration time"]]
    
    def prepare(self, *args, **kwargs):
        SoftShutterController.init(self)
        self.debug("prepare entering...")
        self.debug("ckecking power of motor...")
        #Comprove if Power of Moveable is ON
        mot = taurus.Device(self.motName)     
        stateMotor = mot['PowerOn'].value
        if stateMotor == False:
            raise Exception("The Motor %s  is POWER OFF!!!, please check it." % self.motName)

        #This is to save the Result in MadScanFile and MadScanDir defined in the environment Attributes

        self.bkpScanFile = self.getEnv("ScanFile")
        self.bkpScanDir = self.getEnv("ScanDir")
        self.bkpScanID = self.getEnv("ScanID")

        #New directory and dir to save Results
        self.MadScanFile = self.getEnv("MadScanFile")
        self.MadScanDir = self.getEnv("MadScanDir")
        self.MadScanID = self.getEnv("MadScanID")
      
        self.setEnv("ScanID", self.MadScanID)
        self.setEnv("ScanFile", self.MadScanFile)     
        self.setEnv("ScanDir", self.MadScanDir)
        
        #Printing Info of the madscan
        self.info("Operation will be saved in %s/%s" %(self.MadScanDir,self.MadScanFile))
        now = time.strftime("%c")
        self.info("Scan #%i started at %s"%(self.MadScanID+1,now))


    def preConfigure(self):
        self.debug("preConfigure entering...")
        InitCounters()
        dev = taurus.Device(self.devName)
        dev.ConnectTerms(["/Dev3/PFI12", "/Dev3/RTSI0", "DoNotInvertPolarity"])
        for name in self.channelNames:
            self.debug("ChannelName: %s", name)
            channel = taurus.Device(name)
            #since sardana channels when written are also read, 
            #SampleClockSource can not be read after writing - probably bug in the ds 
            counterDevName = channel["channelDevName"].value
            counterDev = taurus.Device(counterDevName) 
            counterDev["SampleClockSource"] = "/Dev3/RTSI0"
            channel["triggerMode"] = "gate"
            channel["dataTransferMechanism"] = "Interrupts"
            if name == self.posNames[0]:
                channel["ZIndexEnabled"] = False
                channel["PulsesPerRevolution"] = 144000000                
                channel["Sign"] = -1
        
    def postCleanup(self):
        self.debug("postCleanup entering...")
        dev = taurus.Device(self.devName)
        dev.DisconnectTerms(["/Dev3/PFI12", "/Dev3/RTSI0"])
        InitCounters()
        PrepareCountersForStepScanning()

    def preStart(self):
        self.debug("preStart entering...")
        mot = taurus.Device(self.motName)
        initialPosition = mot["Position"].value
             
        posChan = taurus.Device(self.posNames[0])        
        posChan["InitialPosition"] = initialPosition
        try:
            self._fsShutter = self.getEnv("_fsShutter")
        except UnknownEnv, e:
            self._fsShutter = 0
        if self._fsShutter == 1:
            SoftShutterController.openShutter(self)
 
                      
    def run(self, startPos, finalPos, speed, integTime):
        #since from time to time, retrieving poolObj from sardana elements gives errors
        #getting them here, to avoid problems in the future
        for counterName in self.counterNames:
            self.getExpChannel(counterName).getPoolObj()

        #works only in positive direction
        scanTime = ((finalPos - startPos) / speed) * 60
        self.debug("Scan time: %f" % scanTime) 
        if integTime < 0:
            integTime = (0.0005 / speed) * 60
        self.debug("Integration time: %f" % integTime) 
        nrOfTriggers = int(math.ceil(scanTime / integTime))
        self.debug("NrOfTriggers: %f" % nrOfTriggers) 
        oldMntGrp = self.getEnv("ActiveMntGrp")
        varName = "ActiveMntGrp" #% self.getDoorName()
        self.setEnv(varName, self.mntGrp)
        try:
            moveable = self.getMoveable(self.motName)
            quickScanPosCapture, pars = self.createMacro("ascanct_ni", moveable, startPos, finalPos, nrOfTriggers, scanTime, 100)
            
        #Modify the title of the macro in the Recorder
            command = "madscan "+str(startPos)+" "+str(finalPos)+" "+str(speed)+" "+str(integTime)
            quickScanPosCapture.extraRecorder.env["title"] = command
            quickScanPosCapture.hooks = [ (self.preConfigure, ["pre-configuration"]), (self.preStart, ["pre-start"]), (self.postCleanup, ["post-cleanup"])]
            self.runMacro(quickScanPosCapture)
        finally:
            self.setEnv(varName, oldMntGrp)
            if self._fsShutter == 1:
                SoftShutterController.closeShutter(self)

            self.info("Operation saved in %s/%s" %(self.MadScanDir,self.MadScanFile))
            now = time.strftime("%c")
            self.info("Scan #%i ended at %s"%(self.MadScanID+1,now))

            #Restore the ScanFile and ScanDir after to do MadScan
            self.setEnv("ScanFile", self.bkpScanFile)
            self.setEnv("ScanDir", self.bkpScanDir)        
            self.setEnv("MadScanID", self.getEnv("ScanID") )
            self.setEnv("ScanID", self.bkpScanID)



