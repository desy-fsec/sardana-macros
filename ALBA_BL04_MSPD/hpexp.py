import PyTango
import time, math
from sardana.macroserver.macro import Macro, Type
from taurus.console.table import Table
from trigger import PositionBase, Trigger
from macro_utils.macroutils import SoftShutterController

class BaseExp:

    def init(self):
        self.debug("BaseExp.init() entering...")
        self.acqTime = None         #time when photon shutter is exposuring [s]
        self.marAcqTime = None      #time when detector is acquireing [s]
        self.mntGrpAcqTime = None   #time when measurement group is acquireing [s]
        self.countId = None         #id of the measurement group count
        self.marSave = None         #writing or not lima file
        self.rayonixSpecific = PyTango.DeviceProxy("rayonix_custom") #lima device implementing specifics of rayonix detector
        self.hpDiode = PyTango.DeviceProxy("hpi") # hp diode actuator device   
        self.debug("BaseExp.init() leaving...")

    def checkDetector(self):
        self.debug("BaseExp.checkDetector() entering...")
        ready = True

        state,acq = self.execMacro('lima_status','rayonix').getResult().split()
        if acq == 'Configuration': 
            self.info("Dark image must be taken first")
            self.info("Execute martake_bg")
            raise Exception("Marccd is not ready to start an acquisition.")

        self.marSave = self.getEnv("MarSave")
        if self.marSave:
            self.marDir = self.getEnv("MarDir")
            self.marFile = self.getEnv("MarFile")
            if len(self.marDir) <= 0 or len(self.marFile) <= 0 : 
                self.error("Problem with Directory path and/or Prefix name. Please check env variables using lsenv ")  
                raise Exception("Marccd is not ready to start an acquisition.")
            else:
                self.fileNumber=self.execMacro(['lima_lastimage','rayonix']).getResult()
        else:
            self.info("Image will not be saved.")
        self.debug("BaseExp.checkDetector() leaving...")

    def checkDiode(self):
        self.debug("BaseExp.checkDiode() entering...")        
        hpi_status = self.hpDiode.read_attribute('value').value
        if hpi_status == 0:
            self.warning("Diode might be in!!!")
            self.error("Press Ctrl+C within 3 secs if you want to abort.")
            for i in range(60): 
                time.sleep(0.05)
                self.pausePoint()
        self.debug("BaseExp.checkDiode() leaving...")

    def prepareDetector(self):
        self.debug("BaseExp.prepareDetector() entering...")
        if self.marSave:
            self.execMacro(['lima_saving', 'rayonix', self.marDir, self.marFile, 'EDF', False]) #we write the file manually 
        latency = 2.5
        self.execMacro(['lima_prepare', 'rayonix', self.marAcqTime, latency])
        #taking the real file information
        self.marDir = self.execMacro(['lima_getconfig','rayonix', 'directory']).getResult()
        self.marFile = self.execMacro(['lima_getconfig','rayonix', 'prefix']).getResult()
        self.fileNumber = self.execMacro(['lima_lastimage','rayonix']).getResult()
        self.debug("BaseExp.prepareDetector() leaving...")

    def prepareMntGrp(self):
        self.debug("BaseExp.prepareMntGrp() entering...")
        mntGrpName = self.getEnv('ActiveMntGrp')
        self.mntGrp = self.getObj(mntGrpName, type_class=Type.MeasurementGroup)
        cfg = self.mntGrp.getConfiguration()
        cfg.prepare()
        self.mntGrp.setIntegrationTime(self.mntGrpAcqTime)
        self.debug("BaseExp.prepareMntGrp() leaving...")

    def acquireDetector(self):
        self.debug("BaseExp.acquireDetector() entering...")
        self.execMacro(['lima_acquire','rayonix'])
        self.debug("BaseExp.acquireDetector() leaving...")

    def acquireMntGrp(self):
        self.debug("BaseExp.acquireMntGrp() entering...")
        self.countId = self.mntGrp.start()
        self.debug("BaseExp.acquireMntGrp() leaving...")

    def waitMntGrp(self):
        self.debug("BaseExp.waitMntGrp() entering...")
        self.mntGrp.waitFinish(id=self.countId)
        self.debug("BaseExp.waitMntGrp() leaving...")    

    def monitorDetector(self):
        self.debug("BaseExp.monitorDetector() entering...")
        state,acq = self.execMacro('lima_status','rayonix').getResult().split()
        while acq == "Running":
            self.pausePoint()
            state,acq = self.execMacro('lima_status','rayonix').getResult().split()
            time.sleep(0.05)
        self.debug("BaseExp.monitorDetector() leaving...")

    def populateHeader(self):
        self.debug("BaseExp.populateHeader() entering...")               
        headerLines = []
        headerLines.append("scan_type = %s %s" % (self.getName(),self.getParameters()))
        headerBeamX = self.rayonixSpecific.read_attribute("header_beam_x").value
        headerLines.append("beam_center_x = %.2f" % headerBeamX)
        headerBeamY = self.rayonixSpecific.read_attribute("header_beam_y").value
        headerLines.append("beam_center_y = %.2f" % headerBeamY)
        headerDistance = self.rayonixSpecific.read_attribute("header_distance").value
        headerLines.append("refined_distance = %.2f" % (headerDistance))
        headerWavelength = self.rayonixSpecific.read_attribute("header_wavelength").value
        headerLines.append("refined_wavelength = %.4f" % (headerWavelength))
        headerIntegrationTime = self.rayonixSpecific.read_attribute("header_integration_time").value
        headerLines.append("t_int = %.4f" % headerIntegrationTime)
        headerReadoutTime = self.rayonixSpecific.read_attribute("header_readout_time").value
        headerLines.append("t_read = %.4f" % headerReadoutTime)
        headerPixelSizeX = self.rayonixSpecific.read_attribute("header_pixelsize_x").value
        headerLines.append("pixel_size_x = %.2f" % headerPixelSizeX)
        headerPixelSizeY = self.rayonixSpecific.read_attribute("header_pixelsize_y").value
        headerLines.append("pixel_size_y = %.2f" % headerPixelSizeY)

        dcmKev = PyTango.DeviceProxy("dcm_kev")
        energy = dcmKev.read_attribute("position").value
        wavelength = 12.39/energy
        headerLines.append("exp_wavelength = %.4f" % wavelength)
        hpDy = PyTango.DeviceProxy("hp_dy")
        hpDyPos = hpDy.read_attribute("position").value
        hpSyu = PyTango.DeviceProxy("hp_syu")
        hpSyuPos = hpSyu.read_attribute("position").value
        hpSyd = PyTango.DeviceProxy("hp_syd")
        hpSydPos = hpSyd.read_attribute("position").value
        distance =  hpDyPos - hpSyuPos - hpSydPos
        headerLines.append("exp_distance = %.2f" % distance)
        
        
        #temporary solution: file /beamlines/bl04/inhouse/ff/header.txt is a communication channels between scientist and controls
        #at the end the list of motors will got fixed
        f = None
        try:
            f = open("/beamlines/bl04/inhouse/ff/header.txt", "r")
            motorLines = f.readlines()
            for idx,line in enumerate(motorLines):
                headerMotors, headerPositions = [], []
                motorNames = line.split()
                for motorName in motorNames:
                    try:
                        motor = PyTango.DeviceProxy(motorName)
                        position = motor.read_attribute("Position").value
                    except Exception, e:
                        self.error("Unable to retrieve information about motor: %s postion" % motorName)
                        continue
                    headerMotors.append(motorName)
                    headerPositions.append("%.4f" % position)
                headerLineMotors = "motor_mne%d = " % idx + " ".join(headerMotors)
                headerLinePositions = "motor_pos%d = " % idx + " ".join(headerPositions)                
                headerLines.append(headerLineMotors)
                headerLines.append(headerLinePositions)
        except Exception, e:
            self.error("Problem while populating image header information.")
            self.debug(e)
        finally:
            if f != None: f.close()
        #end 

        data = self.mntGrp.getValues()
        headerCounters, headerValues = [], []
        for ch_info in self.mntGrp.getChannelsInfo():
            headerCounters.append(ch_info.label)
            if ch_info.shape > [1]:
                headerValues.append(ch_info.shape)
            else:
                headerValues.append(data.get(ch_info.full_name))

        table = Table([headerValues], row_head_str=headerCounters, row_head_fmt='%*s',
                      col_sep='  =  ')
        for line in table.genOutput():
            self.output(line)
        headerLineCounters = "counter_mne = " + " ".join(headerCounters)
        headerLineValues = "counter_pos = " + " ".join(["%.4e" % value for value in headerValues])
        headerLines.append(headerLineCounters)
        headerLines.append(headerLineValues)

        header = "0;" + "|".join(headerLines)
        self.debug("BaseExp.populateHeader() setting lima header: %s" % header)

        self.execMacro(['lima_image_header','rayonix', header]) 
        self.debug("BaseExp.populateHeader() leving...")

    def writeImage(self):
        self.debug("BaseExp.writeImage() entering...")
        self.execMacro(['lima_write_image','rayonix', 0])
        infoString = "Image saved as " + self.marDir + "/" + self.marFile + ("%.4d"%(self.fileNumber+1)) + ".edf"
        self.info(infoString)
        self.report(infoString)
        self.report("scan_type = %s %s" % (self.getName(),self.getParameters()))
        self.debug("BaseExp.writeImage() leaving...")


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

    def closeShutter(self):
        self.debug("SoftShutterController.closeShutter() entering...")
        self.fs.write_attribute("value",0)
        self.debug("SoftShutterController.closeShutter() leaving...")


class BaseScan(BaseExp):

    def init(self):
        self.debug("BaseScan.init() entering...")
        BaseExp.init(self)
        self.motor = None           #motor to scan
        self.starPos = None         #position where constant velocity starts
        self.endPos = None          #position where constant velocity ends
        self.currentPos = None      #position where motor was found before scanning
        self.oldVel = None          #velocity which was configured before scanning [<user_unit>/s]
        self.accTime = None         #acceleration time of the motion [s]
        self.acc = None             #acceleration of the motion [<user_unit>/s^2]
        self.accDist = None         #acceleration discantance of the motion [<user_unit>]
        self.newVel = None          #velocity during the scan [<user_unit>/s]
        self.preStartPos = None     #position where motor start to accelerate
        self.postEndPos = None      #position where motor stop to decelerate
        self.move = None            #displacement (sign indicates the direction)
        self.debug("BaseScan.init() leaving...")

    def checkParams(self, args):
        self.debug("BaseScan.checkParams(%s) entering..." % repr(args))
        self.motor = args[0]
        self.startPos = args[1]
        self.endPos = args[2]
        self.acqTime = args[3]
        self.marAcqTime = self.acqTime + self.MAR_EXTRA_ACQ_TIME
        self.mntGrpAcqTime = self.acqTime - 0.02
        self.debug("BaseScan.checkParams(%s) leaving..." % repr(args))    

    def prepareMotion(self):
        self.debug("BaseScan.prepareMotion() entering...")
        self.currentPos = self.motor.read_attribute("position").value
        self.oldVel = self.motor.read_attribute("velocity").value
        self.accTime = self.motor.read_attribute("acceleration").value
        self.newVel = abs(float((self.endPos - self.startPos) / self.acqTime))

        velConf = self.motor.get_attribute_config('velocity')
        minVelocity = velConf.min_value
        maxVelocity = velConf.max_value
        self.debug("%s motor allowed velocity range <%s,%s>" % (self.motor.name, minVelocity, maxVelocity))

        if maxVelocity != "Not specified" and self.newVel > float(maxVelocity):
            raise Exception("Required velocity exceeds max value of %s deg/sec. \
                             Please either adjust oscillation range or acquisition time" % maxVelocity)
        if minVelocity != "Not specified" and self.newVel < float(minVelocity):
            raise Exception("""Required velocity is below min value of %s deg/sec. \ 
                             Please either adjust oscillation range or acquisition time""" % minVelocity)

        self.acc = self.newVel/self.accTime
        self.accDist = self.acc * self.accTime * self.accTime / 2
        self.debug("%s motor acceleration: %f; acceleration distance: %f" % (self.motor.name,self.acc,self.accDist))

        self.move = self.endPos - self.startPos
        if self.move == 0:
            raise Exception("Start and end positions are equal. For static acquisition, please use mar_ct macro.")
        if self.move < 0:
            self.accDist *= -1 # in case of motion in negative direction, accDist has to be added to the starting pos 
                          # and substracted from the ending position
 
        self.preStartPos = self.startPos - self.accDist
        self.postEndPos = self.endPos + self.accDist
        self.info("Start/End pos %.2f %.2f" %(self.preStartPos,self.postEndPos))
        self.debug("BaseScan.prepareMotion() leaving...")

    def moveToPrestart(self):
        self.debug("BaseScan.moveToPrestart() entering...")
        self.debug("%s motor moving to the pre-start position: %f." % (self.motor.name, self.preStartPos))
        self.motor.move(self.preStartPos)
        self.debug("BaseScan.moveToPrestart() leaving...")

    def moveToPostend(self):
        self.debug("BaseScan.moveToPostend() entering...")
        self.motor.write_attribute("velocity", self.newVel)
        #icepap recalculated acceleration, overwritting it
        self.motor.write_attribute("acceleration", self.accTime)
        realVel = self.motor.read_attribute("velocity").value
        realAccTime = self.motor.read_attribute("acceleration").value
        self.output("REAL VELOCITY= %f; REAL ACCTIME= %f" % (realVel, realAccTime))
        self.debug("%s motor moving to the post-end position: %f." % (self.motor.name, self.postEndPos))
        self.motor.write_attribute("position", self.postEndPos)
        self.debug("BaseScan.moveToPostend() leaving...")

    def cleanup(self):
        self.debug("BaseScan.cleanup() entering...")
        self.motor.stop()
        self.motor.write_attribute("velocity", self.oldVel)
        #icepap recalculated acceleration, overwritting it
        self.motor.write_attribute("acceleration", self.accTime)
        self.motor.move(self.currentPos)
        self.motor.move(self.currentPos)
        self.info("Move %s back to initial position : %.4f" % (self.motor.name,self.currentPos) )
        self.debug("BaseScan.cleanup() leaving...")

class mar_scan(Macro, BaseScan):

    MAR_EXTRA_ACQ_TIME = 0.1

    param_def = [[ 'motor', Type.Motor, None, 'Motor to scan'],
                [ 'start_pos', Type.Float, None, 'Start position'],
                [ 'end_pos', Type.Float, None, 'End position'],
                [ 'time', Type.Float, None, 'Count time']]

    def init(self):
        self.debug("mar_scan.init() entering...")
        BaseScan.init(self)
        self.posBase = None     #NI task to measure position of the scanning motor
        self.blade3 = None      #NI task to handle 3rd blade of the photon shutter
        self.blade4 = None      #NI task to handle 4th blade of the photon shutter    
        self.debug("mar_scan.init() leaving...")

    def checkParams(self, args):
        self.debug("mar_scan.checkParams(%s) entering..." % repr(args))
        BaseScan.checkParams(self, args)
        motName = self.motor.name
        allowedMotors = ["hp_som"]
        if motName not in allowedMotors:
            raise Exception("Wrong motor. Allowed motors are: %s." % repr(ALLOWED_MOTORS))
        self.debug("mar_scan.checkParams(%s) leaving..." % repr(args))

    def prepareShutter(self):
        self.debug("mar_scan.prepareShutter() entering...")
        if self.motor.name == "hp_som":
            resolution = 3.81373708097e-05
            #resolution = 2.5e-03 #indexer
            posCtrName = "bl04/io/ibl0403-dev1-ctr3"
        self.posBase = PositionBase(posCtrName, resolution)
        #accDist = abs(self.accDist) #acc distance sign is irrelevant
        accEnc = abs(self.accDist) / resolution #encoder pulses in acceleration space
        accSpaceBase = math.ceil(accEnc/4) #counter position is X1 not X4 decoded!
        self.debug("accEnc = %d, accSpaceBase = %d" % (accEnc,accSpaceBase))

        if self.move < 0: #counting down
            overflow = 0 #TC is generated when counter decrements its value from 1 to 0
            initialPos = overflow + (abs(accSpaceBase) - 2) #2 is the lowest delay for single trigger
            resetPos = overflow + 1
            direction = -1
        else: #counting up
            overflow = pow(2,32) - 1 #TC is generated when counter increments its value from 2^32 - 2 to 2^32 - 1
            initialPos = overflow - (accSpaceBase - 2) #2 is the lowest delay for single trigger
            resetPos = overflow - 1
            direction = 1

        self.posBase.setDirection(direction)
        self.posBase.setInitialPos(initialPos)
        self.posBase.setResetPos(resetPos)
        #configuring 1st pulse
        blade3_idle = "High"
        blade3_delay = 0
        blade3_high = 0.0
        blade3_low = abs(self.move)+abs(self.accDist)/4
        self.debug("mar_scan.prepareShutter(): blade3: idle = %s; delay = %f; high = %f; low = %f" % (blade3_idle,blade3_delay,blade3_high,blade3_low))
        self.blade3 = Trigger("bl04/io/ibl0403-dev1-ctr0", self.posBase)
        self.blade3.setIdleState(blade3_idle)
        self.blade3.setDelay(blade3_delay)
        self.blade3.setHigh(blade3_high)
        self.blade3.setLow(blade3_low)
        #configuring 2nd pulse
        blade4_idle = "High"
        blade4_delay = abs(self.move)
        blade4_high = 0.0
        blade4_low = abs(self.accDist) / 2
        self.debug("mar_scan.prepareShutter(): blade4: idle = %s; delay = %f; high = %f; low = %f" % (blade4_idle,blade4_delay,blade4_high,blade4_low))
        self.blade4 = Trigger("bl04/io/ibl0403-dev1-ctr1", self.posBase)
        self.blade4.setIdleState(blade4_idle)
        self.blade4.setDelay(blade4_delay)
        self.blade4.setHigh(blade4_high)
        self.blade4.setLow(blade4_low)
        self.debug("mar_scan.prepareShutter() leaving...")

    def startShutter(self):
        self.debug("mar_scan.startShutter() entering...")
        self.posBase.start()
        self.blade3.start()
        self.blade4.start()
        self.debug("mar_scan.startShutter() leaving...")

    def closeShutter(self):
        self.debug("mar_scan.closeShutter() entering...")
        self.posBase.stop()
        self.blade3.stop()
        self.blade4.stop()
        self.debug("mar_scan.closeShutter() leaving...")

    def cleanup(self):
        self.debug("mar_scan.cleanup() entering...")
        self.closeShutter()
        BaseScan.cleanup(self)
        self.debug("mar_scan.cleanup() leaving...")
        
    def run(self, *args, **kwargs):
        #preparing the scan
        self.init()
        self.checkParams(args)
        self.checkDetector()
        self.checkDiode()
        self.prepareMotion()
        self.prepareDetector()
        self.prepareMntGrp()
        self.prepareShutter()
        self.moveToPrestart()
        #dev = PyTango.DeviceProxy("bl04/io/ibl0403-dev1")
        #dev.command_inout("ConnectTerms", ["/Dev1/PFI36", "/Dev1/PFI28", "DoNotInvertPolarity"])#ctr0.out (blade3) -> ctr2.out
        #dev.command_inout("ConnectTerms", ["/Dev1/PFI27", "/Dev1/PFI16", "DoNotInvertPolarity"])#ctr3.src (PhaseA) -> ctr5.out
        #dev.command_inout("ConnectTerms", ["/Dev1/PFI25", "/Dev1/PFI12", "DoNotInvertPolarity"])#ctr3.dir (PhaseB) -> ctr6.out
        self.startShutter()

        try:
            self.moveToPostend()
            self.acquireDetector() # detector has to start acquiring before shutter is opened
            time.sleep(self.accTime)
            self.acquireMntGrp() # mnt grp have to start acquiring when shutter is already opened
            self.monitorDetector()
            self.waitMntGrp()
            self.populateHeader()
            if self.marSave:
                self.writeImage()
        finally:
            #dev.command_inout("DisconnectTerms", ["/Dev1/PFI36", "/Dev1/PFI28"])
            #dev.command_inout("DisconnectTerms", ["/Dev1/PFI27", "/Dev1/PFI16"])
            #dev.command_inout("DisconnectTerms", ["/Dev1/PFI25", "/Dev1/PFI12"])
            self.cleanup()

class mar_softscan(Macro, BaseScan, SoftShutterController):

    MAR_EXTRA_ACQ_TIME = 0.27

    param_def = [[ 'motor', Type.Motor, None, 'Motor to scan'],
                [ 'start_pos', Type.Float, None, 'Start position'],
                [ 'end_pos', Type.Float, None, 'End position'],
                [ 'time', Type.Float, None, 'Count time']]

    def init(self):
        BaseScan.init(self)
        SoftShutterController.init(self)

    def checkParams(self, args):
        self.debug("mar_sofscan.checkParams(%s) entering..." % repr(args))
        BaseScan.checkParams(self, args)
        motName = self.motor.name
        allowedMotors = ["hp_som", "hp_sxu", "hp_syu", "hp_sz"]
        if motName not in allowedMotors:
            raise Exception("Wrong motor. Allowed motors are: %s." % repr(allowedMotors))
        self.debug("mar_softscan.checkParams(%s) leaving..." % repr(args))

    def run(self, *args, **kwargs):
        #preparing the scan
        self.init()
        self.checkParams(args)
        self.checkDetector()
        self.checkDiode()
        self.prepareShutter()
        self.prepareDetector()
        self.prepareMntGrp()
        self.prepareMotion()
        try:
            self.moveToPrestart()
            self.moveToPostend()
            self.acquireDetector()
            time.sleep(self.accTime)
            self.exposureShutter()
            self.acquireMntGrp()
            self.monitorDetector()
            self.waitMntGrp()
            self.populateHeader()
            if self.marSave:
                self.writeImage()
        finally:
            self.cleanup()

    def on_abort(self):
        self.closeShutter()

class mar_ct(Macro, BaseExp, SoftShutterController):

    param_def = [ [ 'time', Type.Float, 1.0, 'Count time']]   

    MAR_EXTRA_ACQ_TIME = 0.3#0.5

    def checkParams(self, args):
        self.debug("mar_ct.checkParams(%s) entering..." % repr(args))
        self.acqTime = args[0]
        self.marAcqTime = self.acqTime + self.MAR_EXTRA_ACQ_TIME
        self.mntGrpAcqTime = self.acqTime - 0.02
        self.debug("mar_ct.checkParams(%s) leaving..." % repr(args))    

    def run(self, *args, **kwargs):
        BaseExp.init(self)
        SoftShutterController.init(self)
        self.checkParams(args)
        self.checkDetector()
        self.checkDiode()
        self.prepareShutter()
        self.prepareDetector()
        self.prepareMntGrp()
        self.acquireDetector()
        self.exposureShutter()
        self.acquireMntGrp()
        self.monitorDetector()
        self.waitMntGrp()
        self.populateHeader()
        if self.marSave:
            self.writeImage()

    def on_abort(self, *args, **kwargs):
        self.debug("mar_ct.on_abort() entering...")
        self.closeShutter()
        self.debug("mar_ct.on_abort() leaving...")
