import time
import math
import PyTango, taurus
from sardana.macroserver.macro import *
from sardana.macroserver.msexception import UnknownEnv
from macro_utils.macroutils import SoftShutterController
from sardana.macroserver.recorders.storage import SPEC_FileRecorder
from sardana.macroserver.macros.scan import ascanct

MNT_GRP = "mad"

class mad_ct(Macro, SoftShutterController):
    
    param_def = [["time", Type.Float, 1.0, "Acq time"]]

    def prepare(self, *args, **kwargs):  
        SoftShutterController.init(self)  
                 
    def run(self, *args, **kwargs):
        time = args[0]
        oldMntGrp = self.getEnv("ActiveMntGrp")
        self.setEnv("ActiveMntGrp", MNT_GRP)
            
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

class _madscan(Macro, SoftShutterController):

    mntGrp = "mad_cs_test"

    motName = "pd_oc"
    #motName = 'dmot1'
    _fsShutter = None
      
    posName = "oc"
    
    
    param_def = [["startPos", Type.Float, None, "Starting position"],
                 ["endPos", Type.Float, None, "Ending pos value"],
                 ["speed", Type.Float, None, "deg/min"],
                 ["integTime", Type.Float, -1.0, "Integration time"]]
    
    def prepare(self, *args, **kwargs):
        #SoftShutterController.init(self)
        self.debug("prepare entering...")
        
        #Comprove if Power of Moveable is ON
        self.debug("ckecking power of motor...")
        mot = taurus.Device(self.motName)     
        stateMotor = mot['PowerOn'].value
        if stateMotor == False:
            raise Exception("The Motor %s  is POWER OFF!!!, please check it." 
                            % self.motName)


        self.bkpScanFile = self.getEnv("ScanFile")

        # ascanct ScanRecorder Backup
        self.bkpScanRecorder = None
        try:
            self.bkpScanRecorder = self.getEnv("ascanct.ScanRecorder")
        except UnknownEnv:
            pass
        self.bkpScanDir = self.getEnv("ScanDir")
        self.bkpScanID = self.getEnv("ScanID")
        
        #Request New directory and dir to save Results
        self.MadScanFile = self.getEnv("MadScanFile")
        self.MadScanRecorder = self.getEnv("MadScanRecorder")
        self.MadScanDir = self.getEnv("MadScanDir")
        self.MadScanID = self.getEnv("MadScanID")
        
        # #Set the specific environment for Mad experiments
        self.setEnv("ScanID", self.MadScanID)
        self.setEnv("ScanFile", self.MadScanFile)
        self.debug("Previous ScanRecorder: %s"%self.getEnv("MadScanRecorder"))
        self.setEnv("ascanct.ScanRecorder", self.MadScanRecorder)
        self.setEnv("ScanDir", self.MadScanDir)
        
        # Deleted these info because the recorder write the same.

        #self.info("Operation will be saved in %s/%s" %(self.MadScanDir, self.MadScanFile))
        #now = time.strftime("%c")
        #self.info("Scan #%i started at %s"%(self.MadScanID+1,now))

    def preConfigure(self):
        self.debug("preConfigure entering...")
        name = self.posName
        channel = PyTango.DeviceProxy(name)
        channel["ZIndexEnabled"] = False
        channel["PulsesPerRevolution"] = 144000000                
        channel["Sign"] = -1
    
    def preStart(self):
        self.debug("preStart entering...")
        mot = taurus.Device(self.motName)
        initialPosition = mot["Position"].value
             
        posChan = taurus.Device(self.posName)
        posChan["initialPos"] = initialPosition

    def run(self, startPos, finalPos, speed, integTime):
        #works only in positive direction
        scanTime = ((finalPos - startPos) / speed) * 60
        self.debug("Scan time: %f" % scanTime) 
        if integTime < 0:
             integTime = (0.0005 / speed) * 60
        self.debug("Integration time: %f" % integTime) 
        nrOfTriggers = int(math.ceil(scanTime / integTime))
        self.debug("NrOfTriggers: %f" % nrOfTriggers) 
        oldMntGrp = self.getEnv("ActiveMntGrp")
        self.setEnv("ActiveMntGrp", self.mntGrp)
        try:
            moveable = self.getMoveable(self.motName)
            # To use in sep6-bliss
            #ascanct_macro, _ = self.createMacro("ascanct", moveable,
            #                                              startPos, finalPos, 
            #                                              nrOfTriggers, 
            #                                              integTime, 100)

            #to use in SEP 6
            ascanct_macro, _ = self.createMacro("ascanct", moveable,
                                                          startPos, finalPos, 
                                                          nrOfTriggers, 
                                                          integTime, 0)

            ascanct_macro.hooks = [
                                   (self.preConfigure, ["pre-configuration"]),
                                   (self.preStart, ["pre-start"])
                                  ]
            
            command = "madscan "+str(startPos)+" "+str(finalPos)+" "+str(speed)\
                      + " " + str(integTime)
            ascanct_macro._gScan._env['title'] = command
             
            self.runMacro(ascanct_macro)
        finally:

            self.debug("Leaving of _madscan")
            self.setEnv("ActiveMntGrp", oldMntGrp)
            

            # Commented because the recorder writes the same:.

            #self.info("Operation saved in %s/%s" %(self.MadScanDir, self.MadScanFile))
            #now = time.strftime("%c")
            #self.info("Scan #%i ended at %s"%(self.MadScanID,now))

 #           self.debug('Restoring %s'%self.bkpScanRecorder)
            self.setEnv("ScanFile", self.bkpScanFile)
            if not self.bkpScanRecorder is None:
                self.debug('Restoring %s'%self.bkpScanRecorder)
                self.setEnv("ascanct.ScanRecorder", self.bkpScanRecorder)
            self.setEnv("ScanDir", self.bkpScanDir)
            self.setEnv("MadScanID", self.getEnv("ScanID") )
	    
            self.setEnv("ScanID", self.bkpScanID)
