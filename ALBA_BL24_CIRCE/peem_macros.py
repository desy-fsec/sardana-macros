import PyTango
import time
import taurus
from sardana.macroserver.macro import *

deviceName='BL24/EH/Peem'

@macro([['integrationTime', Type.Float, None, "Integration time"],
        ["fileName", Type.String, None, "Full windows compatible filename for the image.\n For a windows \
                                         path insert \\ instead of \ "],
        ["imageFormat", Type.String, None, "See description in device server"],
        ["imageContent", Type.String, None, "See description in device server"],
        ["imageId", Type.Integer, None, "Especifies Uview image window to collect."]
    ])
def peemSaveImage(self,integrationTime,fileName,imageFormat,imageContent,imageId): #,imageId):
    """This macro only takes one image from the PEEM
    """
    peem = PyTango.DeviceProxy(deviceName)
    peem.CameraExpTime = integrationTime * 1000
    #imageId = 1
    #peem.AcquisitionInProgress=False
    #peem.AcquireSimpleImage(imageId) 
    #if not peem.AcquisitionInProgress:
    #    peem.AcquisitionInProgress=True

    if peem.AcquisitionInProgress:
        peem.AcquisitionInProgress = False
    peem.AcquireSimpleImage(-1)
    while peem.AcquisitionInProgress:
        time.sleep(integrationTime)
    peem.ExportImage([fileName,imageFormat,imageContent])

@macro([['initValue',Type.Integer, None, "Initial value"],
        ['endValue', Type.Integer, None, "End value"],
        ['nIntervals', Type.Integer, None, "Number of intervals"],
        ['integrationTime', Type.Float, None, "Integration time"],
        ['dwellTime', Type.Float, None, "Dwell time ..."],
        ['nSamples', Type.Integer, None, "Number of samples"],
        ["fileName", Type.String, None, "Full windows compatible filename for the image.\n For a windows \
                                         path insert \\ instead of \ "],
        ["imageFormat", Type.String, None, "See description in device server"],
        ["imageContent", Type.String, None, "See description in device server"],
        ])
def peemFocus(self,initValue,endValue,nIntervals,integrationTime,dwellTime,nSamples,
                   fileName,imageFormat,imageContent):
    
    peem=PyTango.DeviceProxy(deviceName)
    objectiveModIndex = getIndexFromModule('Objective')
    
    peem.CameraExpTime = integrationTime * 1000

    incr=(endValue-initValue)/nIntervals
    
    #if not peem.AcquisitionInProgress:
    #    peem.AcquisitionInProgress=True
    if peem.AcquisitionInProgress:
        peem.AcquisitionInProgress = False
    
    for iteration in range(nIntervals+1):
        currentValue=initValue+(iteration*incr)
        peem.setPSValue([objectiveModIndex,currentValue])
        
        #while peem.getPSValue(11) != currentValue:
        #    self.output('Waiting arrive to the current increment, which is: %d' %currentValue)
        #    time.sleep(0.5)
        time.sleep(dwellTime)
        
        for index in range(nSamples):
            self.output('Saving image %d for iteration %d' %(index,iteration))
            actualFileName=fileName+'_'+str(currentValue)+'_%03d'%iteration
            peem.AcquireSimpleImage(-1)
            while peem.AcquisitionInProgress:
                time.sleep(integrationTime)
            peem.ExportImage([actualFileName,imageFormat,imageContent])
        

@macro([['initVoltage', Type.Float, None, 'initial voltage'],
        ['endVoltage', Type.Float, None, 'end voltage'],
        ['nIntervals', Type.Integer, None, 'Number of intervals'],
        ['nSamples', Type.Integer, None, "Number of samples"],
        ['integrationTime', Type.Float, None, "Integration time"],
        ['dwellTime', Type.Float, None, "Dwell time ..."],
        ["fileName", Type.String, None, "Full windows compatible filename for the image.\n For a windows \
                                         path insert \\ instead of \ "],
        ["imageFormat", Type.String, None, "See description in device server"],
        ["imageContent", Type.String, None, "See description in device server"],
        ]
       )
def peemScanVoltage(self,initVoltage,endVoltage,nIntervals,integrationTime,dwellTime,fileName,imageFormat,imageContent):
    peem = PyTango.DeviceProxy(deviceName)
    startVoltageIndex = getIndexFromModule('Start Voltage')

    incr = (endVoltage - initVoltage)/nIntervals

    peem.CameraExpTime = integrationTime * 1000 #convert to ms.

    #if not peem.AcquisitionInProgress:
    #    peem.AcquisitionInProgress=True

    for iteration in range(nIntervals+1):
        currentValue = initVoltage + (iteration * incr)
        peem.setPSValue([startVoltageIndex, currentVoltage])
        
        #while peem.getPSValue(startVoltageIndex) != currentVoltage:
        #    self.output('Waiting to arrive at next point ( %d )'%currentVoltage)
            #self.output('   Actual value: %d'%actualValue)
        #    time.sleep(0.5)
        time.sleep(dwellTime)
        for index in range(nSamples):
            self.output('Saving image %d for iteration %d' %(index, iteration))
            actualFileName = fileName + '_%03d'%iteration
            if peem.AcquisitionInProgress:
                peem.AcquisitionInProgress = False
            peem.AcquireSimpleImage(-1)
            while peem.AcquisitionInProgress:
                time.sleep(integrationTime)
            peem.ExportImage([actualFileName, imageFormat, imageContent])
    #---------------------------------------
    #self.execMacro('closeFEandValves')

@macro([['motor', Type.Moveable, None, 'Motor to move'],
        ['initPos', Type.Float, None, 'initial position'],
        ['endPos', Type.Float, None, 'end position'],
        ['nIntervals', Type.Integer, None, 'Number of intervals'],
        ['nSamples', Type.Integer, None, "Number of samples"],
        ['integrationTime', Type.Float, None, "Integration time"],
        ['dwellTime', Type.Float, None, "Dwell time ..."],
        ["fileName", Type.String, None, "Full windows compatible filename for the image.\n For a windows \
                                         path insert \\ instead of \ "],
        ["imageFormat", Type.String, None, "See description in device server"],
        ["imageContent", Type.String, None, "See description in device server"],
        ]
       )
def peemScan(self,motor,initPos,endPos,nIntervals,nSamples,integrationTime,dwellTime,fileName,imageFormat,imageContent):
    peem = PyTango.DeviceProxy(deviceName)
    #startVoltageIndex = getIndexFromModule('Start Voltage')
    
    incr = (endPos - initPos)/nIntervals

    peem.CameraExpTime = integrationTime * 1000
        
    #if not peem.AcquisitionInProgress:
    #    peem.AcquisitionInProgress=True

    for iteration in range(nIntervals+1):
        currentPos = initPos + (iteration * incr)
        #peem.setPSValue([startVoltageIndex, currentVoltage])
        motor.move(currentPos)

        #while peem.getPSValue(startVoltageIndex) != currentVoltage:
        #    self.output('Waiting to arrive at next point ( %d )'%currentVoltage)
        #    #self.output('   Actual value: %d'%actualValue)
        #    time.sleep(0.5)
        time.sleep(dwellTime)
        for index in range(nSamples):
            self.output('Saving image %d for iteration %d' %(index, iteration))
            actualFileName = fileName + '_%03d'%iteration+ '_sample%d'%index 
            if peem.AcquisitionInProgress:
                peem.AcquisitionInProgress = False
            peem.AcquireSimpleImage(-1)
            while peem.AcquisitionInProgress:
                time.sleep(integrationTime)
            peem.ExportImage([actualFileName, imageFormat, imageContent])
    #self.execMacro('closeFEandValves')

class peemScanM(Macro):
    hints = { 'allowsHooks':('post-move') } 
    
    param_def = [ [ 'motor', Type.Moveable, None, 'Motor or pseudomotor to move' ],
                  [ 'startPos', Type.Float, None, 'startPos' ],
                  [ 'endPos', Type.Float, None, 'endPos' ],
                  [ 'nIntervals', Type.Integer, None, 'Number of intervals' ],
                  [ 'nSamples', Type.Integer, None, "Number of samples"],
                  [ 'integrationTime', Type.Float, None, 'Integration time' ],
                  [ 'dwellTime', Type.Float, None, "Dwell time ..."],
                  [ 'fileName', Type.String, None, "Full windows compatible filename for the image.\n For a windows \
                                         path insert \\ instead of \ "],
                  [ 'imageFormat', Type.String, None, "See description in device server"],
                  [ 'imageContent', Type.String, None, "See description in device server"],
                ]

    def prepare(self, motor1,startPos,endPos,nIntervals,nSamples,integrationTime,dwellTime,filename,imageFormat,imageContent):
        """Check that parameters for the macro are correct"""
        #@note: Modify the integration time in the camera is still missing!! Comming soon!!
        self.output("\n\n~~~~~ Preparing peemScanMM macro ~~~~")
        self.sleepTime = dwellTime
        self.integrationTime = integrationTime
        self.imageIndex = 0
        self.nSamples = nSamples

        self.peem = PyTango.DeviceProxy(deviceName)
        self.peem.CameraExpTime = integrationTime * 1000
        
    def myHook(self):
        time.sleep(self.sleepTime)
        for sampleNumber in range(self.nSamples):
            if self.peem.AcquisitionInProgress:
                self.peem.AcquisitionInProgress=False   
            self.peem.AcquireSimpleImage(-1) 
            while self.peem.AcquisitionInProgress:
                time.sleep(self.integrationTime)
            
            actualFileName = fileName + '_sample_' + str(sampleNumber) + '_%03d'%self.imageIndex
            self.imageIndex = self.imageIndex+1
            self.peem.ExportImage([actualFileName,imageFormat,imageContent])
    
    def run(self, motor1,startPos,endPos,nIntervals,integrationTime,motor2,fixedPos,sleepTime):
        #"""Run macro"""       
        myMacro, pars = self.createMacro("ascan",motor1,startPos,endPos,nIntervals,integrationTime)
        myMacro.hooks = [(self.myHook, ['post-move'])]
        self.runMacro(myMacro)


@macro()
def getAlbaEmName(self):
    chan = 'emet05_c04'
    channel = self.getObj(chan)
    self.output(channel)
    ctrlr = channel.getControllerName()
    ct = self.getController(ctrlr)
    prop = ct.get_property('albaemname')['albaemname'][0]
    self.output(prop)
    self.output(ctrlr)

class peemScanIo(Macro):
    hints = { 'allowsHooks':('post-move') } 
    
    param_def = [ [ 'motor', Type.Moveable, None, 'Motor or pseudomotor to move' ],
                  [ 'startPos', Type.Float, None, 'startPos' ],
                  [ 'endPos', Type.Float, None, 'endPos' ],
                  [ 'nIntervals', Type.Integer, None, 'Number of intervals' ],
                  [ 'nSamples', Type.Integer, None, "Number of samples"],
                  [ 'integrationTime', Type.Float, None, 'Integration time' ],
                  [ 'dwellTime', Type.Float, None, "Dwell time ..."],
                  [ 'ioChannel', Type.String, None, "Channel to save in the extra file .dat"],
                  [ 'fileName', Type.String, None, "Full windows compatible filename for the image.\n For a windows \
                                         path insert \\ instead of \ "],
                  [ 'imageFormat', Type.String, None, "See description in device server"],
                  [ 'imageContent', Type.String, None, "See description in device server"],
                ]

    def prepare(self, motor1,startPos,endPos,nIntervals,nSamples,integrationTime,dwellTime,ioChannel,filename,imageFormat,imageContent):
        """Check that parameters for the macro are correct"""
        self.output("\n\n~~~~~ Preparing peemScan1Image macro ~~~~")
        self.sleepTime = dwellTime
        self.imageIndex = 0
        self.nSamples = nSamples
        self.integrationTime = integrationTime
        self.peem = PyTango.DeviceProxy(deviceName)
        self.ioChannel = self.getObj(ioChannel)
        self.motor = motor1
        #self.imageId = 3
        self.peem.CameraExpTime = integrationTime * 1000
        #logFile = filename + '.txt'
        logFile = '/beamlines/bl24'+filename.split('l:')[1].replace('\\','/')+'.txt'
        #logFile = '/beamlines/bl24/commissioning/tmp/peemTests/testingIO.txt'
        self.fileName = filename
        self.imageFormat = imageFormat
        self.imageContent = imageContent
        #aem = 'BL24/DI/ALBAEM-0' + albaemNum

        ctrlr = self.ioChannel.getControllerName()
        ct = self.getController(ctrlr)
        aem = ct.get_property('albaemname')['albaemname'][0]

        self.albaEm = PyTango.DeviceProxy(aem)
        self.output('Opening logFile: %s'%logFile)
        self.fd = open(logFile,'wa')
        self.fd.write('-----  -------\n')
        self.fd.write('motor | I0value\n')
        self.fd.write('-----  -------\n')
        
    def myPostMoveHook(self):
        self.output("\n~~~~~ Entering to post-move hook ~~~~")
        time.sleep(self.sleepTime)

    def myPreAcqHook(self):
        self.output("\n~~~~~ Entering to pre-acq hook ~~~~")
        if self.peem.AcquisitionInProgress:
            self.peem.AcquisitionInProgress=False   
        self.peem.AcquireSimpleImage(-1)
        
    def myPostAcqHook(self):
        self.output("\n~~~~~ Entering to post-acq hook ~~~~")
        #while self.peem.AcquisitionInProgress:
        #    time.sleep(self.sleepTime)
        for i in reversed(range(self.nSamples)):
            actualFileName = self.fileName +  '_%03d'%self.imageIndex + '_sample%d'%i 
            self.imageIndex = self.imageIndex+1
            self.peem.ExportImage([actualFileName,self.imageFormat,self.imageContent])
            if i is not 0:
                self.peem.AcquireSimpleImage(-1)
                self.albaEm.start()
                time.sleep(self.integrationTime)
            self.saveLog()
    
    def saveLog(self):
        stringToSave = str(self.motor.position) + ' ' + str(self.ioChannel.value) + '\n'
        self.fd.write(stringToSave)

    def run(self, motor1,startPos,endPos,nIntervals,nSamples,integrationTime,dwellTime,ioChannel,filename,imageFormat,imageContent):
        #"""Run macro"""       
        myMacro, pars = self.createMacro("ascan",motor1,startPos,endPos,nIntervals,integrationTime)
        myMacro.hooks = [(self.myPostMoveHook, ['post-move'])]
        myMacro.hooks = [(self.myPreAcqHook, ['pre-acq'])]
        myMacro.hooks = [(self.myPostAcqHook, ['post-acq'])]
        self.runMacro(myMacro)
        self.fd.close()
    #self.execMacro('closeFEandValves')

class peem2ScanIo(Macro):
    hints = { 'allowsHooks':('post-move') } 
    
    param_def = [ [ 'motor1', Type.Moveable, None, 'Motor1 or pseudomotor to move' ],
                  [ 'startPos1', Type.Float, None, 'startPos1' ],
                  [ 'endPos1', Type.Float, None, 'endPos1' ],
                  [ 'motor2', Type.Moveable, None, 'Motor2 or pseudomotor to move' ],
                  [ 'startPos2', Type.Float, None, 'startPos2' ],
                  [ 'endPos2', Type.Float, None, 'endPos2' ],
                  [ 'nIntervals', Type.Integer, None, 'Number of intervals' ],
                  [ 'nSamples', Type.Integer, None, "Number of samples"],
                  [ 'integrationTime', Type.Float, None, 'Integration time' ],
                  [ 'dwellTime', Type.Float, None, "Dwell time ..."],
                  [ 'ioChannel', Type.String, None, "Channel to save in the extra file .txt"],
                  [ 'fileName', Type.String, None, "Full windows compatible filename for the image.\n For a windows \
                                         path insert \\ instead of \ "],
                  [ 'imageFormat', Type.String, None, "See description in device server"],
                  [ 'imageContent', Type.String, None, "See description in device server"],
                ]

    def prepare(self, motor1,startPos1,endPos1,motor2,startPos2,endPos2,nIntervals,nSamples,integrationTime,dwellTime,ioChannel,filename,imageFormat,imageContent):
        """Check that parameters for the macro are correct"""
        self.output("\n\n~~~~~ Preparing peemScan1Image macro ~~~~")
        self.sleepTime = dwellTime
        self.imageIndex = 0
        self.nSamples = nSamples
        self.integrationTime = integrationTime
        self.peem = PyTango.DeviceProxy(deviceName)
        self.ioChannel = self.getObj(ioChannel)
        ctrlr = self.ioChannel.getControllerName()
        ct = self.getController(ctrlr)
        aem = ct.get_property('albaemname')['albaemname'][0]

        self.albaEm = PyTango.DeviceProxy(aem)
        self.motor1 = motor1
        self.motor2 = motor2
        #self.imageId = 3
        self.peem.CameraExpTime = integrationTime * 1000
        #logFile = filename + '.txt'
        logFile = '/beamlines/bl24'+filename.split('l:')[1].replace('\\','/')+'.txt'
        #logFile = '/beamlines/bl24/commissioning/tmp/peemTests/testingIO.txt'
        self.fileName = filename
        self.imageFormat = imageFormat
        self.imageContent = imageContent
        self.output('Opening logFile: %s'%logFile)
        self.fd = open(logFile,'wa')
        self.fd.write('------  -------  -------\n')
        self.fd.write('motor1 | motor2 | I0value\n')
        self.fd.write('------  -------  --------\n')
        
    def myPostMoveHook(self):
        self.output("\n~~~~~ Entering to post-move hook ~~~~")
        time.sleep(self.sleepTime)
        
    def myPreAcqHook(self):
        self.output("\n~~~~~ Entering to pre-acq hook ~~~~")
        if self.peem.AcquisitionInProgress:
            self.peem.AcquisitionInProgress=False   
        self.peem.AcquireSimpleImage(-1)
        
    def myPostAcqHook(self):
        self.output("\n~~~~~ Entering to post-acq hook ~~~~")
        for i in reversed(range(self.nSamples)):
            actualFileName = self.fileName +  '_%03d'%self.imageIndex + '_sample%d'%i
            #actualFileName = self.fileName + '_sample%d'%i +  '_%03d'%self.imageIndex
            self.imageIndex = self.imageIndex+1
            self.peem.ExportImage([actualFileName,self.imageFormat,self.imageContent])
            if i is not 0:
                self.peem.AcquireSimpleImage(-1)
                self.albaEm.start()
                time.sleep(self.integrationTime)
            self.saveLog()
    
    def saveLog(self):
        stringToSave = str(self.motor1.position) + ' ' + str(self.motor2.position) + ' ' + str(self.ioChannel.value) + '\n'
        self.fd.write(stringToSave)

    def run(self, motor1,startPos1,endPos1,motor2,startPos2,endPos2,nIntervals,nSamples,integrationTime,dwellTime,ioChannel,filename,imageFormat,imageContent):
        #"""Run macro"""       
        myMacro, pars = self.createMacro("a2scan",motor1,startPos1,endPos1,motor2,startPos2,endPos2,nIntervals,integrationTime)
        myMacro.hooks = [(self.myPreAcqHook, ['pre-acq'])]
        myMacro.hooks = [(self.myPostAcqHook, ['post-acq'])]
        self.runMacro(myMacro)
        self.fd.close()
    #self.execMacro('closeFEandValves')
    
@macro([['initVoltage', Type.Float, None, 'initial voltage'],
        ['endVoltage', Type.Float, None, 'end voltage'],
        ['initObjective', Type.Float, None, 'initial Objective'],
        ['endObjective', Type.Float, None, 'end Objective'],
        ['nIntervals', Type.Integer, None, 'Number of intervals'],
        ['nSamples', Type.Integer, None, "Number of samples"],
        ['integrationTime', Type.Float, None, "Integration time"],
        ['dwellTime', Type.Float, None, "Dwell time ..."],
        ["fileName", Type.String, None, "Full windows compatible filename for the image.\n For a windows path insert \\ instead of \ "],
        ["imageFormat", Type.String, None, "See description in device server"],
        ["imageContent", Type.String, None, "See description in device server"],
        ]
       )
def peemA2ScanVoltage(self,initVoltage,endVoltage,initObjective,endObjective,nIntervals,nSamples,integrationTime,dwellTime,fileName,imageFormat,imageContent):
    peem = PyTango.DeviceProxy(deviceName)
    startVoltageIndex = getIndexFromModule('Start Voltage')
    objectiveModIndex = getIndexFromModule('Objective')

    incrVoltage = (endVoltage - initVoltage)/nIntervals
    incrObjective = (endObjective - initObjective)/nIntervals
    
    peem.CameraExpTime = integrationTime * 1000
        
    if peem.AcquisitionInProgress:
        peem.AcquisitionInProgress = False
    
    for iteration in range(nIntervals+1):
        
        currentVoltage = initVoltage + (iteration * incrVoltage)
        peem.setPSValue([startVoltageIndex, currentVoltage])
        
        currentObjective = initObjective + (iteration * incrObjective)
        peem.setPSValue([objectiveModIndex, currentObjective])
        
        time.sleep(dwellTime)
        for index in range(nSamples):
            peem.AcquireSimpleImage(-1)
            time.sleep(integrationTime)
            self.output('Saving image %d for iteration %d' %(index, iteration))
            #if currentVoltage < 0: 
                #strVoltage = 'M'+str(currentVoltage)[1:]
            #else:
                #strVoltage = 'P'+str(currentVoltage)
            actualFileName = fileName + '_%03d'%iteration
            peem.ExportImage([actualFileName, imageFormat, imageContent])

    #-----------------------------------------------------  
    #self.execMacro('closeFEandValves')


@macro([['initVoltage', Type.Float, None, 'initial voltage'],
        ['endVoltage', Type.Float, None, 'end voltage'],
        ['nIntervVoltage', Type.Integer, None, 'Number of intervals for voltage'],
        ['initObjective', Type.Float, None, 'initial Objective'],
        ['endObjective', Type.Float, None, 'end Objective'],
        ['nIntervObjective', Type.Integer, None, 'Number of intervals for objective'],
        ['nSamples', Type.Integer, None, "Number of samples"],
        ['integrationTime', Type.Float, None, "Integration time"],
        ['dwellTimeVolt', Type.Float, None, "Dwell time for voltage ..."],
        ['dwellTimeObj', Type.Float, None, "Dwell time for objective ..."],
        ["fileName", Type.String, None, "Full windows compatible filename for the image.\n For a windows path insert \\ instead of \ "],
        ["imageFormat", Type.String, None, "See description in device server"],
        ["imageContent", Type.String, None, "See description in device server"],
        ]
       )
def peemMeshVoltObj(self,initVoltage,endVoltage,nIntervVoltage,initObjective,endObjective,nIntervObjective,nSamples,integrationTime,dwellTimeVolt,dwellTimeObj,fileName,imageFormat,imageContent):
    peem = PyTango.DeviceProxy(deviceName)
    startVoltageIndex = getIndexFromModule('Start Voltage')
    objectiveModIndex = getIndexFromModule('Objective')

    incrVoltage = (endVoltage - initVoltage)/nIntervVoltage
    incrObjective = (endObjective - initObjective)/nIntervObjective
    
    peem.CameraExpTime = integrationTime * 1000

    if peem.AcquisitionInProgress:
        peem.AcquisitionInProgress = False

    for iterationVolt in range(nIntervVoltage+1):
        
        currentVoltage = initVoltage + (iterationVolt * incrVoltage)
        peem.setPSValue([startVoltageIndex, currentVoltage])

        time.sleep(dwellTimeVolt)

        for iterationObj in range(nIntervObjective):
        
            currentObjective = initObjective + (iteration * incrObjective)
            peem.setPSValue([objectiveModIndex, currentObjective])
        
            time.sleep(dwellTimeObj)
        
            for index in range(nSamples):
                peem.AcquireSimpleImage(-1)
                time.sleep(integrationTime)
                self.output('Saving image %d for voltage iteration %d and objective iteration %d' %(index, iterationVolt, iterationObj))
                if currentVoltage < 0: 
                    strVoltage = 'M'+str(currentVoltage)[1:]
                else:
                    strVoltage = 'P'+str(currentVoltage)
                actualFileName = fileName + '_' + strVoltage + '_' + str(currentObjective) + '_03d'%index
                #actualFileName = fileName + '_%03d'%index
                peem.ExportImage([actualFileName, imageFormat, imageContent])

@macro()
def getPeemVoltage(self):
    peem = PyTango.DeviceProxy(deviceName)
    startVoltageIndex = getIndexFromModule('Start Voltage')
    startVoltage = peem.getPSValue(startVoltageIndex)
    self.output('Start Voltage = %f'%startVoltage)

@macro()
def getPeemObjective(self):
    peem = PyTango.DeviceProxy(deviceName)
    objectiveIndex = getIndexFromModule('Objective')
    objective = peem.getPSValue(objectiveIndex)
    self.output('Objective = %f'%objective)

@macro()
def getPeemModules(self):
    peem = PyTango.DeviceProxy(deviceName)
    for i in range(peem.NrModules):
        moduleName = peem.GetPSName(i)
        self.output(moduleName)

def getValueFromModule(moduleName):
    peem = PyTango.DeviceProxy(deviceName)
    for i in range(peem.NrModules):
        if peem.GetPSName(i)==moduleName:
            return peem.GetPSValue(i)
             
def getIndexFromModule(moduleName):
    peem = PyTango.DeviceProxy(deviceName)
    for i in range(peem.NrModules):
        if peem.GetPSName(i)==moduleName:
            return i
             
 
 
#In [108]: peem.command_inout('ExportImage',['L:\\controls\\tmp\\peem\\image11.dat','0','0'])
#
#In [109]: '\t'
#Out[109]: '\t'
#
#In [110]: pars = ['L:\controls\tmp\peem\image11.dat','0','0']

#In [111]: print pars[0]
#L:\controls     mp\peem\image11.dat

#In [112]: pars = ['''L:\controls\tmp\peem\image11.dat''','0','0']

#In [113]: print pars[0]
#L:\controls     mp\peem\image11.dat

#In [114]: pars = [u'''L:\controls\tmp\peem\image11.dat''','0','0']

#In [115]: print pars[0]
#L:\controls     mp\peem\image11.dat

#In [116]: pars = [r'''L:\controls\tmp\peem\image11.dat''','0','0']

#In [117]: print pars[0]
#L:\controls\tmp\peem\image11.dat
