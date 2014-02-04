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
        self.count_id = None

    def setAcqTime(self, acq_time):
        self.mntGrpAcqTime = acq_time

    def prepareMntGrp(self):
        self.macro.debug("MntGrpController.prepareMntGrp() entering...")
        self.count_id = None
        mntGrpName = self.macro.getEnv('ActiveMntGrp')
        self.mntGrp = self.macro.getObj(mntGrpName, type_class=Type.MeasurementGroup)
        cfg = self.macro.mntGrp.getConfiguration()
        cfg.prepare()
        self.mntGrp.setIntegrationTime(self.mntGrpAcqTime)
        self.macro.debug("MntGrpController.prepareMntGrp() leaving...")
        
    def acquireMntGrp(self):
        self.macro.debug("MntGrpController.acquireMntGrp() entering...")
        self.count_id = self.mntGrp.start()
        self.macro.debug("MntGrpController.acquireMntGrp() leaving...")

    def waitMntGrp(self):
        self.macro.debug("MntGrpController.waitMntGrp() entering...")
        if self.count_id != None:
            self.mntGrp.waitFinish(id=self.count_id)
        else:
            msg = "MntGrpController.waitMntGrp() trying to call wait with id = None"
            self.macro.warning(msg)
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


class MoveableController:

    def init(self, motor):
        self.debug("MoveableController.init() entering...")

        self.motor = motor           #motor to scan
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
        self.const_vel_time = None
        self.debug("MoveableController.init() leaving...")

    def prepareMotion(self, const_vel_time, start_pos, end_pos):
        self.debug("MoveableController.prepareMotion() entering...")
        self.current_pos = self.motor.read_attribute("position").value
        self.old_vel = self.motor.read_attribute("velocity").value
        self.acc_time = self.motor.read_attribute("acceleration").value
        self.new_vel = abs(float((end_pos - start_pos) / const_vel_time))

        velConf = self.motor.get_attribute_config('velocity')
        minVelocity = velConf.min_value
        maxVelocity = velConf.max_value
        self.debug("%s motor allowed velocity range <%s,%s>" % 
                   (self.motor.name, minVelocity, maxVelocity))

        if maxVelocity != "Not specified" and self.newVel > float(maxVelocity):
            
            raise Exception("Required velocity exceeds max value of %s deg/sec.\
                             Please either adjust oscillation range or acquisition time" % maxVelocity)
        if minVelocity != "Not specified" and self.newVel < float(minVelocity):
            raise Exception("""Required velocity is below min value of %s deg/sec. \ 
                             Please either adjust oscillation range or acquisition time""" % minVelocity)

        self.acc = self.new_vel/self.acc_time
        self.accDist = self.acc * self.acc_time * self.acc_time / 2
        self.debug("%s motor acceleration: %f; acceleration distance: %f" % (self.motor.name,self.acc,self.accDist))

        self.move = end_pos - start_pos
        if self.move == 0:
            raise Exception("Start and end positions are equal. For static acquisition, please use mar_ct macro.")
        if self.move < 0:
            self.accDist *= -1 # in case of motion in negative direction, accDist has to be added to the starting pos 
                          # and substracted from the ending position
 
        self.preStartPos = start_pos - self.accDist
        self.post_end_pos = end_pos + self.accDist
        self.info("Start/End pos %.2f %.2f" %(self.preStartPos,self.post_end_pos))
        self.debug("MoveableController.prepareMotion() leaving...")

    def moveToPrestart(self):
        self.debug("MoveableController.moveToPrestart() entering...")
        self.debug("%s motor moving to the pre-start position: %f." % (self.motor.name, self.preStartPos))
        self.motor.move(self.preStartPos)
        self.debug("MoveableController.moveToPrestart() leaving...")

    def moveToPostend(self):
        self.debug("MoveableController.moveToPostend() entering...")
        self.motor.write_attribute("velocity", self.new_vel)
        #icepap recalculated acceleration, overwritting it
        self.motor.write_attribute("acceleration", self.acc_time)
        real_vel = self.motor.read_attribute("velocity").value
        real_acc_time = self.motor.read_attribute("acceleration").value
        self.output("REAL VELOCITY= %f; REAL ACCTIME= %f" % 
                    (real_vel, real_acc_time))
        self.debug("%s motor moving to the post-end position: %f." %
                  (self.motor.name, self.post_end_pos))
        self.motor.write_attribute("position", self.post_end_pos)
        self.debug("MoveableController.moveToPostend() leaving...")

    def cleanup(self):
        self.debug("MoveableController.cleanup() entering...")
        self.motor.stop()
        self.motor.write_attribute("velocity", self.old_vel)
        #icepap recalculated acceleration, overwritting it
        self.motor.write_attribute("acceleration", self.acc_time)
        self.motor.move(self.current_pos)
        self.info("Move %s back to initial position : %.4f" % 
                  (self.motor.name, self.current_pos))
        self.debug("MoveableController.cleanup() leaving...")
