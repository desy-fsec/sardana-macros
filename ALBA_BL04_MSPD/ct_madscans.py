import math
import PyTango
import time
from sardana.macroserver.msexception import UnknownEnv
from sardana.macroserver.macro import *
from macro_utils.mad26acq import PrepareCountersForStepScanning, InitCounters
from macro_utils.macroutils import SoftShutterController

class ct_madscan(Macro, SoftShutterController):

    mntGrp = "ct_mad_cs"

    motName = "pd_oc"
    
    _fsShutter = None
    
    counterNames = ["ct_i%d" % i for i in range(1,15)]
    
    posNames = ["ct_oc"]
    
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
        #mot = PyTango.DeviceProxy(self.motName)     
        #stateMotor = mot['PowerOn'].value
        #if stateMotor == False:
        #    raise Exception("The Motor %s  is POWER OFF!!!, please check it." % self.motName)

        #This is to save the Result in MadScanFile and MadScanDir defined in the environment Attributes

        #self.bkpScanFile = self.getEnv("ScanFile")
        #self.bkpScanDir = self.getEnv("ScanDir")
        #self.bkpScanID = self.getEnv("ScanID")

        #New directory and dir to save Results
        #self.MadScanFile = self.getEnv("MadScanFile")
        #self.MadScanDir = self.getEnv("MadScanDir")
        #self.MadScanID = self.getEnv("MadScanID")
      
        #self.setEnv("ScanID", self.MadScanID)
        #self.setEnv("ScanFile", self.MadScanFile)     
        #self.setEnv("ScanDir", self.MadScanDir)
        
	#Printing Info of the madscan
#	self.info("Operation will be saved in %s/%s" %(self.MadScanDir,self.MadScanFile))#
#	now = time.strftime("%c")
#        self.info("Scan #%i started at %s"%(self.MadScanID+1,now))


    def preConfigure(self):
        self.debug("preConfigure entering...")
        InitCounters()
        dev = PyTango.DeviceProxy(self.devName)
        dev.ConnectTerms(["/Dev3/PFI12", "/Dev3/RTSI0", "DoNotInvertPolarity"])
        for name in self.counterNames:
            self.debug("ChannelName: %s", name)
            channel = PyTango.DeviceProxy(name)
            #since sardana channels when written are also read, 
            #SampleClockSource can not be read after writing - probably bug in the ds 
            counterDevName = channel["channelDevName"].value
            counterDev = PyTango.DeviceProxy(counterDevName) 
            counterDev["SampleClockSource"] = "/Dev3/RTSI0"
            counterDev["dataTransferMechanism"] = "Interrupts"
        name = self.posNames[0]
        channel = PyTango.DeviceProxy(name)
        channel["SampleClockSource"] = "/Dev3/RTSI0"
        channel["dataTransferMechanism"] = "Interrupts"
        channel["ZIndexEnabled"] = False
        channel["PulsesPerRevolution"] = 144000000                
        channel["Sign"] = -1
        
    def postCleanup(self):
        self.debug("postCleanup entering...")
        dev = PyTango.DeviceProxy(self.devName)
        dev.DisconnectTerms(["/Dev3/PFI12", "/Dev3/RTSI0"])
        InitCounters()
        PrepareCountersForStepScanning()

    def preStart(self):
        self.debug("preStart entering...")
        mot = PyTango.DeviceProxy(self.motName)
        initialPosition = mot["Position"].value
             
        posChan = PyTango.DeviceProxy(self.posNames[0])        
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
#        for counterName in self.counterNames:
#            self.getExpChannel(counterName).getPoolObj()

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
#            quickScanPosCapture, pars = self.createMacro("ascanct_ni", moveable, startPos, finalPos, nrOfTriggers, scanTime, 100)
            ascanct, _ = self.createMacro(
                            'ascanct', moveable, startPos, finalPos, 
                            nrOfTriggers, integTime, 100)           
	    #Modify the title of the macro in the Recorder
#            command = "madscan "+str(startPos)+" "+str(finalPos)+" "+str(speed)+" "+str(integTime)
#            quickScanPosCapture.extraRecorder.env["title"] = command
            ascanct.hooks = [
                (self.preConfigure, ["pre-configuration"]),
                (self.preStart, ["pre-start"]),
                (self.postCleanup, ["post-cleanup"])
            ]
            self.runMacro(ascanct)
        finally:
            self.setEnv(varName, oldMntGrp)
            if self._fsShutter == 1:
                SoftShutterController.closeShutter(self)

#   	    self.info("Operation saved in %s/%s" %(self.MadScanDir,self.MadScanFile))
#            now = time.strftime("%c")
#            self.info("Scan #%i ended at %s"%(self.MadScanID+1,now))

            #Restore the ScanFile and ScanDir after to do MadScan
#            self.setEnv("ScanFile", self.bkpScanFile)
#            self.setEnv("ScanDir", self.bkpScanDir)        
#            self.setEnv("MadScanID", self.getEnv("ScanID") )
#            self.setEnv("ScanID", self.bkpScanID)
