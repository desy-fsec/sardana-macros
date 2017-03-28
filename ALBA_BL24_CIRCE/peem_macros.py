import PyTango
import time, datetime
import numpy
import os
import taurus
from sardana.macroserver.macro import *
#from peem_config import *
#from peem_tools import *


SAMPLE_TEMP = 39
BOMB_VOLTAGE=41
EMISSION_CURR = 42
START_VOLTAGE=38
SAMPLE_TEMP=39
OBJECTIVE=11
MCP_VOLTAGE=105 #93
deviceName='BL24/EH/Peem'
devicePreview='bl24/ct/peempreview-01'
peemDS = PyTango.DeviceProxy(deviceName)
IOCHANNEL = 'emet05_c03'


#################### peemSimone  ################################
## This temporary macro is used for talk with Simene's hardware
#@macro([
        #["cmd", Type.String, None, "cmd to send to the device"],
        #])
#def peemSimone(self,cmd):
    #try:
        #peem = PyTango.DeviceProxy("NAPP/CT/SERIAL-12")
    
        #param = [1][cmd]
        #ans = peem.WriteRead(param)
        #self.info(ans)
    #except Exception,e:
        #self.warning('Error in peemSimone')
        #self.debug(e) 

################################################################################



#move to tools
################### peemGetAllModuleValues  ################################
# This macro is used for storing all the peem-module values in a file
# It is usually called at the beginning of each macro
@macro([
        ["current_dir", Type.String, None, "current directory"],
        ])
def peemGetAllModuleValuesToFile(self,current_dir):
    # Name of the file into the directory
    counter = self.getEnv('PeemFolderCounter')
    logFile = "%s/%03d_PeemSettings.txt" %(current_dir, counter)
    # Open log file
    self.fd = open(logFile,'wa')
    peem = PyTango.DeviceProxy(deviceName)
    
    # For reading modules and values #
    try:
        for i in range(peem.NrModules):
            moduleName = peem.GetPSName(i)
            moduleValue = peem.GetPSValue(i)
            str_to_file = "Index=%2d\tModule Name = %12s\tValue = %f" %(i,moduleName,moduleValue)
            # Write header of log file
            self.fd.write(str_to_file + "\n")
            #self.output(str_to_file)
    except Exception,e:
        self.warning('Error in peemGetAllModuleValuesToFile')
        self.debug(e) 
    self.fd.close()


    
    

###############################################################################



#move to tools
################### peemGetAllModuleValues  ###################################
#  This macro is for online visualization
#  It reads the index, the name and the value for each module of the Peem
#  i.e. "Index=11        Module Name =    Objective      Value = 1897.699463"
@macro()
def peemGetAllModuleValues(self):
    peem = PyTango.DeviceProxy(deviceName)
    
    # For reading modules and values #
    #for i in range(peem.NrModules):
    for i in range(120):
        moduleName = peem.GetPSName(i)
        moduleValue = peem.GetPSValue(i)
        self.output("Index=%2d\tModule Name = %12s\tValue = %f" %(i,moduleName,moduleValue))
###############################################################################



#move to tools
################### peemSetStartVoltage  #######################################
#  This macro set the Startvoltage parameter
@macro([
        [ 'StartVoltage', Type.Float, None, "Start Voltage to be set"],
        ]
       )
def peemSetStartVoltage(self,StartVoltage ):
    peem = PyTango.DeviceProxy(deviceName)

    peem.setPSValue([START_VOLTAGE, StartVoltage])
    self.output('Setting StartVoltage = %.2f eV'%(StartVoltage))
###############################################################################




################### peemFlash  ################################################
#  This macro set the Bomb Voltage parameter
@macro([
        [ 'BombVoltage', Type.Float, None, "Bomb Voltage to be set"],
        [ 'MaxTemp', Type.Float, None, "Max Temp to be set"],
        [ 'Repetitions', Type.Integer, None, "Repetitions"],
        ]
       )
def peemFlash(self,BombVoltage,MaxTemp, Repetitions ):
    peem = PyTango.DeviceProxy(deviceName)

    moduleValue = 0
    #t = 0

    for i in range(Repetitions):
        peem.setPSValue([BOMB_VOLTAGE, BombVoltage])
        self.output('Setting Bomb Voltage = %.2f eV'%(BombVoltage))
        moduleValue = peem.GetPSValue(SAMPLE_TEMP)
        while moduleValue < MaxTemp:
#            old_moduleValue = moduleValue
            moduleValue = peem.GetPSValue(SAMPLE_TEMP)
            self.output("Sample Temp = %.2f Celsius" %(moduleValue))        
            time.sleep(1.0)
        peem.setPSValue([BOMB_VOLTAGE, 0.0])
        self.output('Setting Bomb Voltage = %.2f eV'%(0.0))

      
        time.sleep(300.0)
    #t = 0
    #while moduleValue> 10:
        #old_moduleValue = moduleValue
        #moduleValue = peem.GetPSValue(SAMPLE_TEMP)
        #self.output("Sample Temp = %.2f Celsius" %(moduleValue))
        ##if old_moduleValue > moduleValue:
            ##t = t + moduleValue/(old_moduleValue - moduleValue)
            ##self.output("Time to 0 Celsius = %.2f s" %(t))
            ##t = 0
        ##else:
            ##t = t +1
        #time.sleep(1.0)
###############################################################################



#move to tools    
################### peemSetEmissionCurr  ######################################
#  This macro set the Emission Current parameter
@macro([
        [ 'EmissionCurr', Type.Float, None, "EmissionCurr to be set"],
        ]
       )
def peemSetEmissionCurr(self,EmissionCurr ):
    peem = PyTango.DeviceProxy(deviceName)

    peem.setPSValue([EMISSION_CURR, EmissionCurr])
    self.output('Setting EmissionCurr = %.2f eV'%(EmissionCurr))
###############################################################################



#move to tools
################### peemSetObjective  #########################################
#  This macro set the Objective parameter
@macro([
        [ 'Objective', Type.Float, None, "Objective to be set"],
        ]
       )
def peemSetObjective(self,Objective ):
    peem = PyTango.DeviceProxy(deviceName)

    peem.setPSValue([OBJECTIVE, Objective])
    self.output('Setting Objective = %.2f mA'%(Objective))
###############################################################################



#move to tools
################### peemSetMCP_Voltage  #########################################
#  This macro set the Objective parameter
@macro([
        [ 'Voltage', Type.Float, None, "MCP Voltage between 1.1kV and 1.55kV"],
        ]
       )
def peemSetMCPVoltage(self,Voltage ):
    peem = PyTango.DeviceProxy(deviceName)
    if Voltage>=1.1 and Voltage <= 1.55:
        peem.setPSValue([MCP_VOLTAGE, Voltage])
        self.output('Setting MCP Voltage = %.2f kV'%(Voltage))
    else:
        self.error("The voltage is out of range")
###############################################################################



#move to tools
################### peemSetAverageImages  #####################################
#  This macro set the peem acquisition mode: sliding or not
#  We force no-average images before an acquisition and we set sliding-images at the end
@macro([
        [ 'AverageImages', Type.Integer, None, "0 = No average images"],
        ]
       )
def peemSetAverageImages(self,AverageImages ):
    peem = PyTango.DeviceProxy(deviceName)
    peem.AverageImages = AverageImages
    if AverageImages == 0:
        self.output('Setting No average images')
    elif AverageImages == 1:
        self.output('Setting Sliding images')
###############################################################################



#move to tools
################### setDailyFolder  ###########################################
# Take current day and build the automatic folders
# It sets: scanDir, scanFile, PeemFolderForImages and PeemFolderCounter environment variables
@macro()
def setDailyFolder(self):
    # Get current date
    today = datetime.datetime.today()
    year = today.year
    month = today.month
    day = today.day

    # Configure ScanDir
    scanDir = "/beamlines/bl24/commissioning/%d/%d_%02d/%d%02d%02d" %(year, year, month, year, month, day)
    envArg = "\"%s\"" %(scanDir)
    self.setEnv('ScanDir', envArg)
    self.output("Setting ScanDir = %s" %(envArg))
    # Create directory
    if not os.path.exists(scanDir):
        self.output("Making directory %s" %scanDir)
        os.makedirs(scanDir)
        # Initialize counter = 1
        self.setEnv('PeemFolderCounter', 1)
        self.output("Setting PeemFolderCounter = 1")

    # Configure ScanFile
    scanFile_dat = "%d%02d%02d_01.dat" %(year, month, day)
    scanFile_h5 = "%d%02d%02d_01.h5" %(year, month, day)
    envArg = "[\"%s\", \"%s\"]" %(scanFile_dat, scanFile_h5)
    self.setEnv('ScanFile', envArg)
    self.output("Setting ScanFile = %s" %(envArg))

    # Configure PeemFolderForImages
    #scanDir = "/beamlines/bl24/controls/tmp/fb"
    envArg = "\"%s\"" %(scanDir)
    self.setEnv('PeemFolderForImages', envArg)
    self.output("Setting PeemFolderForImages = %s" %(envArg))
    # Create directory
    if not os.path.exists(scanDir):
        self.output("Making directory %s" %scanDir)
        os.makedirs(scanDir)
###############################################################################




################### peemSetDailyFolder  #######################################
# This macro is specific of the Peem experiment.
# We use it for non-standard directory/files
# It needs to be update just before a weekly experiment
@macro()
def peemSetDailyFolder(self):
    # Get current date
    today = datetime.datetime.today()
    year = today.year
    month = today.month
    day = today.day

    # Configure ScanDir
    scanDir = "/beamlines/bl24/projects/cycle2017-I/2015021245-jdelafiguera/DATA/%d%02d%02d" %(year, month, day)
    #scanDir = "/beamlines/bl24/inhouse/2017/LEEM_2017_02/%d%02d%02d" %(year, month, day)
    envArg = "\"%s\"" %(scanDir)
    self.setEnv('ScanDir', envArg)
    self.output("Setting ScanDir = %s" %(envArg))
    # Create directory
    if not os.path.exists(scanDir):
        self.output("Making directory %s" %scanDir)
        os.makedirs(scanDir)
        # Initialize counter = 1
        self.setEnv('PeemFolderCounter', 1)
        self.output("Setting PeemFolderCounter = 1")

    # Configure ScanFile
    scanFile_dat = "%d%02d%02d_01.dat" %(year, month, day)
    scanFile_h5 = "%d%02d%02d_01.h5" %(year, month, day)
    envArg = "[\"%s\", \"%s\"]" %(scanFile_dat, scanFile_h5)
    self.setEnv('ScanFile', envArg)
    self.output("Setting ScanFile = %s" %(envArg))

    # Configure PeemFolderForImages
    #scanDir = "/beamlines/bl24/controls/tmp/fb"
    envArg = "\"%s\"" %(scanDir)
    self.setEnv('PeemFolderForImages', envArg)
    self.output("Setting PeemFolderForImages = %s" %(envArg))
    # Create directory
    if not os.path.exists(scanDir):
        self.output("Making directory %s" %scanDir)
        os.makedirs(scanDir)

###############################################################################



#move to tools
################### peemSetFolder  ############################################
# get the env-variable "PeemFolderForImages" and set the Tango attribute "FolferForImage" to that value
@macro([
        ["subDir", Type.String, None, "subDir"],
        ]
       )
def peemSetFolder(self, subDir):
    self.peem = PyTango.DeviceProxy(deviceName)

    # Get environment variable
    env = self.getEnv('PeemFolderForImages')
    counter = self.getEnv('PeemFolderCounter')
    #pffi = "%s/%s" %(env, subDir)
    pffi = "%s/%03d_%s" %(env, counter, subDir)

    # Create directory
    if not os.path.exists(pffi):
        self.output("Making directory %s" %pffi)
        os.makedirs(pffi)
        # Save all peem parameters in a file
        self.execMacro("peemGetAllModuleValuesToFile %s" %pffi)

        # Increase the counter for peem folder
        self.setEnv('PeemFolderCounter', counter+1)
        # Set peem attribute
        dirName_aux = pffi.split("/beamlines/bl24")[1] 
        dirName = "l:" + dirName_aux.replace("/","\\") +"\\"
        self.peem.write_attribute("FolderForImage", dirName)
        self.output("Setting FolderForImage = %s" %(dirName))
    else:
        self.output("The Folder %s already exists" %(pffi))
###############################################################################

    

#move to tools
################### peemSetIntegrationTime  ###################################
# the IntegrationTime is set as the ExposureTime for the camera
@macro([
        [ 'integrationTime', Type.Float, None, "Integration Time in seconds"],
        ]
       )
def peemSetIntegrationTime(self, integrationTime):
    self.peem = PyTango.DeviceProxy(deviceName)

    self.peem.write_attribute("CameraExpTime",integrationTime * 1000)
    self.output("Setting Peem Integration Time to %f sec" %integrationTime)
###############################################################################





################### peemGetNormImage  ##########################################
# This macro takes one normalization image with the current peem-setting (objectibe +50mA) and it associates to it an automatica dir-name/file-name
@macro ([
        ['Avg', Type.Integer, 64, "Uview_internal averages (32 or 64)"],
        ['defocus (mA)', Type.Float, 100, "defocus (mA))"]
        ]
       )

def peemGetNormImage(self, Avg, defocus):
    # Config peem
    peem = PyTango.DeviceProxy(deviceName)
    current = peem.GetPSValue(11)
    defcurrent = float(current)+defocus
    self.execMacro("peemSetObjective %f" %defcurrent)
    time.sleep(2)  #better: get exposure time
    dirName = "norm"
    counter = self.getEnv('PeemFolderCounter')
    fileName = "norm" + "%03d_%s" %(counter, dirName)
    if Avg != 1:
        self.execMacro("peemSetAverageImages %d" %Avg)   #set here internal average
    else:
        self.execMacro("peemSetAverageImages %d" %0)   #set here internal average
    self.execMacro("peemSetFolder %s" %dirName)
    #self.execMacro("peemSetAverageImages %d" %0)
    self.execMacro("peemGetImage %s" %fileName)
    #self.execMacro("peemSetIntegrationTime %f" %integrationTime)
    self.execMacro("peemSetObjective %f" %(float(current)))
    self.execMacro("peemSetAverageImages %d" %0) 
###############################################################################




################### peemGetSingleImage  ##########################################
# This macro takes one single image with the current peem-setting and it associates to it an automatica dir-name/file-name
@macro ([
        ['Avg', Type.Integer, 8, "Uview_internal averages (1,2,4,8,.."]
        ]
       )

def peemGetSingleImage(self, Avg):
    # Config peem
    dirName = "img"
    counter = self.getEnv('PeemFolderCounter')
    fileName = "%03d_%s" %(counter, dirName)
    if Avg != 1:
        self.execMacro("peemSetAverageImages %d" %Avg)   #set here internal average
    else:
        self.execMacro("peemSetAverageImages %d" %0)   #set here internal average
    self.execMacro("peemSetFolder %s" %dirName)
    #self.execMacro("peemSetAverageImages %d" %0)
    self.execMacro("peemGetImage %s" %fileName)
    #self.execMacro("peemSetIntegrationTime %f" %integrationTime)
    self.execMacro("peemSetAverageImages %d" %1) 

###############################################################################


@macro([
        ['high_time', Type.Float, None, 'Time on high state.'],
        ['low_time', Type.Float, None, 'Time on high state.'],
        ['ntriggers', Type.Integer, 1, 'Total number of triggers'],
        ]
       )
def peemTestGetImages(self, high_time,low_time, ntriggers):
    try:
        # Config peem
        dirName = "img" # FB
        counter = self.getEnv('PeemFolderCounter')
        Avg = 1 # FB
        if Avg != 1:
            self.execMacro("peemSetAverageImages %d" %Avg)   #set here internal average
        else:
            self.execMacro("peemSetAverageImages %d" %0)   #set here internal average
        self.execMacro("peemSetFolder %s" %dirName)


        self.output("Step 1: ni_config_trigger")
        self.execMacro("ni_config_trigger %f %f %d" %(high_time, low_time, ntriggers))
        
        self.output("Step 2: adlink_bl24_config")
        self.execMacro("adlink_bl24_config %d " %(high_time))
        
        self.output("Step 3: start adlink")
        self.execMacro("adlink_bl24_start")
            
        self.output("Step 4: getImages")
        t0 = time.time()
        for i in range(ntriggers):
            fileName = "%03d_%s_%d" %(counter, dirName, i)
            self.execMacro("peemGetImageFromTrigger %s" %fileName )
            
        self.output("Step 5: showResults")
        self.output("Dead time %.3f", (time.time() - t0)-ntriggers * (high_time  + low_time ))

        self.execMacro("peemSetAverageImages %d" %1) 

    except Exception,e:
        self.error("Error in peemTestGetImages", str(e))

################### peemGetImageFromTrigger  #############################################
# get any actual Image and save it with the name = fileName (in the directory PeemFolderForImages")
# using continous aquisition!!!

@macro([
        ["fileName", Type.String,"Default", "Only filename for the image.(the directory is an attr of the peem)"],
        ]
       )
def peemGetImageFromTrigger(self, fileName):
    
     #start_acq = time.time()  MF06062014
    if fileName == "Default":
        self.execMacro("peemGetSingleImage")
    else:
        self.peem = PyTango.DeviceProxy(deviceName)
        timeout = 6000
        self.peem.set_timeout_millis(timeout)
        # Get image format from environment variable
        imageConf = self.getEnv('PeemImageConf')
        imageFormat = str(imageConf[0])
        imageContent = str(imageConf[1])

        
        #start_acq = time.time()
        # Check AcquisitionInProgress variable
        try:
            if self.peem.AcquisitionInProgress:
                #self.output("Forcing AcquisitionInProgress=False")
                self.peem.AcquisitionInProgress=False
        except Exception,e:
            self.warning('Workaround.Timeout exceeded %f seconds in reading AcquisitionInProgress attr ' % (float(timeout)/1000.))
            self.error("Error in peemGetImageFromTrigger", str(e))
        ### self.output('Check AcquisitionInProgress variable in = %.2f sec' %(time.time()-start_acqA ))
        #start_acq = time.time()   until here delay almost zero XXX
        start_acqB = time.time()
        # Start acquiring image
        try:
            self.output("tango ds: peem.AcquireSimpleImage")
            self.peem.AcquireSimpleImage(-1)
            self.output("macro: ni_trigger")
            self.execMacro("ni_trigger")# FB to be revised
        except Exception,e:
            self.warning('Workaround.Timeout exceeded %f seconds in AcquireSimpleImage cmd ' % (float(timeout)/1000.))
            
            self.error("Error in peemGetImageFromTrigger", str(e))
        self.output('Start acquiring image in = %.2f sec' %(time.time()-start_acqB ))
        

        try:
            # Waiting for the flag: Acquiring
            start_acq = time.time()  #MF 06062014 from XXX to here 1.8seconds
            i=0
            while self.peem.AcquisitionInProgress == True:
                i=i+1
                time.sleep(0.1)
                if i%30==0:
                    self.output("Acquiring ... %.2f sec"%(time.time()-start_acq))
        except Exception,e:
            self.warning('Workaround.Timeout exceeded %f seconds in Waiting for the flag ' % (float(timeout)/1000.))
            self.debug(e) 
            self.warning('Workaround.Waiting 30s before next ExportImage ')
            time.sleep(30.0)
    
        # Export images 
        try:
            self.peem.ExportImage([fileName, imageFormat,imageContent])  
            self.peem.AcquisitionInProgress=True #lucia 20131027 
        except Exception,e:
            self.warning('Workaround. Timeout exceeded %f seconds in ExportImage cmd' % (float(timeout)/1000.))
            self.debug(e) 
            #self.peem.ExportImage([fileName, imageFormat,imageContent])
        
        # Export images 
        self.output('Exporting Image %s in = %.2f sec' %(fileName, time.time()-start_acq ))

###############################################################################

################### peemGetImageFromTriggerMF  #############################################
# get any actual Image and save it with the name = fileName (in the directory PeemFolderForImages")
# using continous aquisition!!!

@macro([
        ["fileName", Type.String,"Default", "Only filename for the image.(the directory is an attr of the peem)"],
        ]
       )
def peemGetImageFromTriggerMF(self, fileName):
    
    start_acq = time.time()  #MF06062014
    if fileName == "Default":
        self.execMacro("peemGetSingleImage")# FB to be revised
    else:
        self.peem = PyTango.DeviceProxy(deviceName)
        timeout = 6000
        self.peem.set_timeout_millis(timeout)
        # Get image format from environment variable
        imageConf = self.getEnv('PeemImageConf')
        imageFormat = str(imageConf[0])
        imageContent = str(imageConf[1])
        #start_acq = time.time()
        # Export images 
        try:
            self.output("macro: ni_trigger")
            self.execMacro("ni_trigger")# FB to be revised
            self.output("tango ds: peem.ExportImage")
            self.peem.ExportImage([fileName, imageFormat,imageContent])  
        #    self.peem.AcquisitionInProgress=True #lucia 20131027 
        except Exception,e:
            self.warning('Workaround. Timeout exceeded %f seconds in ExportImage cmd' % (float(timeout)/1000.))
            self.debug(e) 
            #self.peem.ExportImage([fileName, imageFormat,imageContent])
        # Export images 
        self.output('Exporting Image %s in = %.2f sec' %(fileName, time.time()-start_acq ))
###############################################################################

#move to tools
################### peemGetImage  #############################################
# get Image and save it with the name = fileName (in the directory PeemFolderForImages")
# It is used in every peem-macro
# uses aquisition on/off
@macro([
        ["fileName", Type.String,"Default", "Only filename for the image.(the directory is an attr of the peem)"],
        ]
       )
def peemGetImage(self, fileName):
    
    #start_acq = time.time()  MF06062014
    if fileName == "Default":
        self.execMacro("peemGetSingleImage")
    else:
        self.peem = PyTango.DeviceProxy(deviceName)
        timeout = 6000
        self.peem.set_timeout_millis(timeout)
        # Get image format from environment variable
        imageConf = self.getEnv('PeemImageConf')
        imageFormat = str(imageConf[0])
        imageContent = str(imageConf[1])

        
        #start_acq = time.time()
        # Check AcquisitionInProgress variable
        try:
            if self.peem.AcquisitionInProgress:
                #self.output("Forcing AcquisitionInProgress=False")
                self.peem.AcquisitionInProgress=False
        except Exception,e:
            self.warning('Workaround.Timeout exceeded %f seconds in reading AcquisitionInProgress attr ' % (float(timeout)/1000.))
            self.debug(e) 
        ### self.output('Check AcquisitionInProgress variable in = %.2f sec' %(time.time()-start_acqA ))
        #start_acq = time.time()   until here delay almost zero XXX
        start_acqB = time.time()
        # Start acquiring image
        try:
            self.peem.AcquireSimpleImage(-1)
        except Exception,e:
            self.warning('Workaround.Timeout exceeded %f seconds in AcquireSimpleImage cmd ' % (float(timeout)/1000.))
            self.debug(e) 
        self.output('Start acquiring image in = %.2f sec' %(time.time()-start_acqB ))
        

        try:
            # Waiting for the flag: Acquiring
            start_acq = time.time()  #MF 06062014 from XXX to here 1.8seconds
            i=0
            while self.peem.AcquisitionInProgress == True:
                i=i+1
                time.sleep(0.1)
                if i%30==0:
                    self.output("Acquiring ... %.2f sec"%(time.time()-start_acq))
        except Exception,e:
            self.warning('Workaround.Timeout exceeded %f seconds in Waiting for the flag ' % (float(timeout)/1000.))
            self.debug(e) 
            self.warning('Workaround.Waiting 30s before next ExportImage ')
            time.sleep(30.0)
    
        # Export images 
        try:
            self.peem.ExportImage([fileName, imageFormat,imageContent])  
            self.peem.AcquisitionInProgress=True #lucia 20131027 
        except Exception,e:
            self.warning('Workaround. Timeout exceeded %f seconds in ExportImage cmd' % (float(timeout)/1000.))
            self.debug(e) 
            #self.peem.ExportImage([fileName, imageFormat,imageContent])
        
        # Export images 
        self.output('Exporting Image %s in = %.2f sec' %(fileName, time.time()-start_acq ))

###############################################################################




#move to tools
################### peemGetImageMF  #############################################
# get any actual Image and save it with the name = fileName (in the directory PeemFolderForImages")
# using continous aquisition!!!

@macro([
        ["fileName", Type.String,"Default", "Only filename for the image.(the directory is an attr of the peem)"],
        ]
       )
def peemGetImageMF(self, fileName):
    
    start_acq = time.time()  #MF06062014
    if fileName == "Default":
        self.execMacro("peemGetSingleImage")
    else:
        self.peem = PyTango.DeviceProxy(deviceName)
        timeout = 6000
        self.peem.set_timeout_millis(timeout)
        # Get image format from environment variable
        imageConf = self.getEnv('PeemImageConf')
        imageFormat = str(imageConf[0])
        imageContent = str(imageConf[1])
        #start_acq = time.time()
        # Export images 
        try:
            self.peem.ExportImage([fileName, imageFormat,imageContent])  
        #    self.peem.AcquisitionInProgress=True #lucia 20131027 
        except Exception,e:
            self.warning('Workaround. Timeout exceeded %f seconds in ExportImage cmd' % (float(timeout)/1000.))
            self.debug(e) 
            #self.peem.ExportImage([fileName, imageFormat,imageContent])
        # Export images 
        self.output('Exporting Image %s in = %.2f sec' %(fileName, time.time()-start_acq ))
###############################################################################



#move to tools
#############  peemSetAEM  ####################################################
# from iochannel-name we configure properly the aem used for peem
@macro([
        ["ioChannel", Type.String, None, "ioChannel name (i.e. emet04_c05)"],
        ]
       )
def peemSetAEM(self,ioChannel):
    # Get"iochannel"
    self.ioChannel = self.getObj(ioChannel)

    # Get controller of "iochannel"
    ctrlr = self.ioChannel.getControllerName()
    ct = self.getController(ctrlr)
    
    # Get aem of "iochannel"
    aem = ct.get_property('albaemname')['albaemname'][0]

    # Configure aem
    self.albaEm = PyTango.DeviceProxy(aem)
    self.albaEm.write_attribute("AvSamples",1)
    self.albaEm.write_attribute("SampleRate",0.001) 

    # Configure albaem_zerod with this aem/channel
    a = ioChannel.split("emet")
    channel = a[1].split("_c0")[1]
    self.albaemzd = PyTango.DeviceProxy("albaemzd")
    attr_zd = "%s/I%d" %(str(aem),int(channel))
    self.albaemzd.write_attribute("TangoAttribute", attr_zd)
    self.output("Setting albaemzd.TangoAttribute = %s" %self.albaemzd.TangoAttribute)

###############################################################################




#move to tools
########  peemGetSampleImages   ###############################################
# It takes N images with the same config.
@macro([
        [ 'n_sample', Type.Integer, None, "Number of images"],
        [ 'fileName', Type.String, None, "filename for the image."],
        ]
       )
def peemGetSampleImages(self, n_sample, fileName):
    self.peem = PyTango.DeviceProxy(deviceName)

    if n_sample < 1:
        self.output("Warning: your number of samples is less than 1 ... you will not take any image!")
    else:
        for r in range(n_sample):
            if n_sample==1:
                fileNameMod = fileName
            else:
                fileNameMod = fileName +  '_s%02d'%r
            self.execMacro("peemGetImage %s" %fileNameMod)
###############################################################################



#move to tools
#######  peemGetSampleImagesMF   ###############################################
# It takes N images with the same config. with time distance = integration time+0.2
# it is good to avoid 1.7 seconds deadtime using single images, 
# so it should be used for high sample numbers (XMCD/XMLD) or low integration time around 1s, because the
# the price to pay is one integration. Until we can poll for new images. 
# now always better in XAS, because the integration time is spent for the measurement group.
# now updated to include internal averages
@macro([
        [ 'n_sample', Type.Integer, None, "Number of images"],
        [ 'fileName', Type.String, None, "filename for the image."],
        [ 'integrationTime', Type.Float, None, "integration time of macro"],
        [ 'Avg', Type.Integer, None, "Avg"],
        ]
       )
def peemGetSampleImagesMF(self, n_sample, fileName, integrationTime, Avg):
    self.peem = PyTango.DeviceProxy(deviceName)
    if Avg==0:  #because no average is 0, sliding average is 1
        x=1
    else:              # for higher numbers
        x=Avg
    if n_sample < 1:
        self.output("Warning: your number of samples is less than 1 ... you will not take any image!")
    else:
        #time.sleep(integrationTime)   #to make sure that the image is at the right condition. to be included upwards&flexible 
        for r in range(n_sample):
            time.sleep(x*integrationTime+0.1)   #x accounts for internal averages
            if n_sample==1:
                fileNameMod = fileName
            else:
                fileNameMod = fileName +  '_s%02d'%r
            self.execMacro("peemGetImageMF %s " %fileNameMod)
            

###############################################################################




  
############# peemScanIo ###################################################
# This Macro scans the Energy ans, at each step, it takes an image
#
class peemScanIo(Macro):
    hints = { 'allowsHooks':('post-move') } 
    
    param_def = [ [ 'motor1', Type.Moveable, None, 'Motor or pseudomotor to move' ],
                  [ 'startPos1', Type.Float, None, 'startPos' ],
                  [ 'endPos1', Type.Float, None, 'endPos' ],
                  [ 'nIntervals', Type.Integer, None, 'Number of intervals' ],
                  [ 'integrationTime', Type.Float, None, 'Integration time' ],
                  [ 'ioChannel', Type.String, None, "Channel to save in the log file"],
                  [ 'fileName', Type.String, None, "Filename for the image"],
                  [ 'nSamples', Type.Integer, None, "Number of samples"],
                ]

    def prepare(self, motor1,startPos1,endPos1,nIntervals,integrationTime,ioChannel,fileName, nSamples):

        # Tango dp
        self.peem = PyTango.DeviceProxy(deviceName)
        # Get Args
        self.imageIndex = 0 # For Image Name
        self.motor1 = motor1
        self.integrationTime = integrationTime
        self.fileName = fileName
        self.nSamples = nSamples
        
        # Config peem
        self.execMacro("peemSetFolder %s" %fileName)
        self.execMacro("peemSetAverageImages %d" %0)
        self.execMacro("peemSetIntegrationTime %f" %integrationTime)
        self.execMacro("peemSetAEM %s" %ioChannel)
        # Config Log file 
        sent_macro = "%s %s %s %s %s %s %s %s %s" %("peemScanIo",motor1,startPos1,endPos1,nIntervals,integrationTime,ioChannel,fileName, nSamples)
        self.log = LogForPeem(self, fileName, sent_macro)# Basic Peem setup
        
    def myPostMoveHook(self):
        self.output("... ... ... ... ... ...")
        self.output('Setting Energy = %s eV' %self.motor1.position) #should be generalized to any motor name!!

    def myPreAcqHook(self):
        actualFileName = self.fileName +  '_%03d'%self.imageIndex 
        self.execMacro("peemGetSampleImages %d %s" %(self.nSamples, actualFileName))
        self.imageIndex = self.imageIndex+1
        
    def myPostAcqHook(self):
        self.log.save(self)
    
    def on_abort(self):
        if self.peem.AcquisitionInProgress:
            self.output("\nAborting: Force AcquisitionInProgress=False in peem server")
            self.peem.AcquisitionInProgress=False   
        self.log.close()

    def run(self, motor1,startPos1,endPos1,nIntervals,integrationTime,ioChannel,filename, nSamples):
        #"""Run macro"""       
        myMacro, pars = self.createMacro("ascan",motor1,startPos1,endPos1,nIntervals,integrationTime)
        myMacro.hooks = [(self.myPostMoveHook, ['post-move'])]
        myMacro.hooks = [(self.myPreAcqHook, ['pre-acq'])]
        myMacro.hooks = [(self.myPostAcqHook, ['post-acq'])]
        self.runMacro(myMacro)
        self.log.close()
###############################################################################




###############################################################################
# Class for managing the log file info
# In the logfile we save Objective, ScanVoltage, EnergyVal, MotorPos, ioChannel
class LogForPeem():
    def __init__(self, mcr, fileName, sentMacro = None, setNewFolder = 1 ):
        # Device proxies for reading log-values 
        self.peem = PyTango.DeviceProxy(deviceName)
        self.energy_val_dp = PyTango.DeviceProxy("energy_val")
        self.albaemzd_dp = PyTango.DeviceProxy("albaemzd")
        self.xbee_dp = PyTango.DeviceProxy("xbee")
        self.imag_norm_dp = PyTango.DeviceProxy("img_normalization")
        self.imag_norm_roi1_dp = PyTango.DeviceProxy("roi1_normalization")
        self.imag_norm_roi2_dp = PyTango.DeviceProxy("roi2_normalization")
        self.imag_norm_roi3_dp = PyTango.DeviceProxy("roi3_normalization")
        #self.motor1 = mcr.motor1
        
        try:
            counter = mcr.getEnv('PeemFolderCounter') -1
      
            pffi = "/%03d_" %(counter)
            # Get environment variable to build log file
            logFile = mcr.getEnv('PeemFolderForImages') + pffi + fileName + "/"+fileName+".txt"
            # Open log file
            self.fd = open(logFile,'a')
            mcr.output('Setting logFile = %s'%logFile)
            # Get scan Number
            scan_id = mcr.getEnv('ScanID')
            # Write header of log file
            #self.fd.write('ScanID = %d\n' %(scan_id+1))
            #self.fd.write('%s\n' %(sentMacro))
            # FB 28-Jan-2015
            #stringToSave = str("%10s\t%10s\t%10s\t%10s\t%10s\t%10s\t%10s\n" %("Obj.","Start_V","Eval(eV)","Epos(eV)", "ioChannel", "Temp", "XASspec"))
            if setNewFolder == 1:
                stringToSave = str("%10s\t%10s\t%10s\t%10s\t%10s\t%10s\t%10s\t%10s\t%10s\t%10s\n" %("Obj.","Start_V","Eval(eV)", "ioChannel", "Temp", "I_norm", "I_roi1", "I_roi2","I_roi3","Drain"))
                self.fd.write(stringToSave)
           
            try:
                mcr.info("peemSaveBLSettings")
                blsetting_name = mcr.getEnv('PeemFolderForImages') + pffi + fileName + pffi + "log_" +fileName+".txt"
                
                a = str(blsetting_name)
                b = "MACRO_NAME"
                c = str(scan_id+1)
                mcr.info(c)
                cmd = "peemSaveBLSettings " + a +" "+ b +" "+ c
                mcr.info(cmd)
                mcr.execMacro(cmd)
            except Exception,e:
                mcr.error("Error in peemSaveBLSettings: %s" %str(e))
        except Exception,e:
            mcr.error("Error in LogForPeem: %s" %str(e))

    def save(self, mcr):
        try:
            objective = str("%.2f" %self.peem.GetPSValue(OBJECTIVE))
        except Exception,e:
            objective = "0.000"
        try:
            start_voltage = str("%.2f" %self.peem.GetPSValue(START_VOLTAGE))
        except Exception,e:
            start_voltage = "0.000"

        try:
            sample_temp = str("%.2f" %self.peem.GetPSValue(SAMPLE_TEMP))
        except Exception,e:
            sample_temp = "0.000"
        #self.output(sample_temp)

        try:
            energy_val = str("%.2f" %self.energy_val_dp.value)
        except Exception,e:
            energy_val = "0.000"
        #try:
            #energy_pos = str("%.2f" %self.motor1.position)
        #except Exception,e:
            #energy_pos = "None"
        try:
            ioChannel_I = str("%.3e" %self.albaemzd_dp.value)
        except Exception,e:
            ioChannel_I = "0.000"

        # FB 21-Jun-2016
        try:
            #self.integrationPreview = PyTango.DeviceProxy("bl24/ct/integrationpreview")
            #I_norm = str("%.3e" %self.integrationPreview.intensity_normal)
            I_norm = str("%.3e" %self.imag_norm_dp.value)
        except Exception,e:
            I_norm = "0.000"

        # FB 21-Jun-2016
        try:
            I_roi1_norm = str("%.3e" %self.imag_norm_roi1_dp.value)
            I_roi2_norm = str("%.3e" %self.imag_norm_roi2_dp.value)
            I_roi3_norm = str("%.3e" %self.imag_norm_roi3_dp.value)
        except Exception,e:
            I_roi1_norm = "0.000"
            I_roi2_norm = "0.000"
            I_roi3_norm = "0.000"
        
        # FB 08-Oct-2015
        try:
            drain = str("%.3e" %self.xbee_dp.value)
        except Exception,e:
            drain = "0.000"

        # FB 28-Jan-2015
        #stringToSave = str("%10s\t%10s\t%10s\t%10s\t%10s\t%10s\t%10s\n" %(objective,start_voltage,energy_val,energy_pos, ioChannel_I, sample_temp, XASspectra))
        stringToSave = str("%10s\t%10s\t%10s\t%10s\t%10s\t%10s\t%10s\t%10s\t%10s\t%10s\n" %(objective,start_voltage,energy_val, ioChannel_I, sample_temp, I_norm, I_roi1_norm, I_roi2_norm, I_roi3_norm,  drain))
            
        self.fd.write(stringToSave)

    def close(self):
        self.fd.close()

###############################################################################


       


############# peem2ScanIo_MF ##################################################
# This Macro scans the Energy and, at each step, it takes an image
#
class peem2ScanIo_MF(Macro):
    hints = { 'allowsHooks':('post-move') } 
    
    param_def = [ [ 'motor1', Type.Moveable, None, 'Motor1 or pseudomotor1 to move' ],
                  [ 'startPos1', Type.Float, None, 'startPos1' ],
                  [ 'endPos1', Type.Float, None, 'endPo1s' ],
                  [ 'motor2', Type.Moveable, None, 'Motor2 or pseudomotor2 to move' ],
                  [ 'startPos2', Type.Float, None, 'startPos2' ],
                  [ 'endPos2', Type.Float, None, 'endPos2' ],
                  [ 'nIntervals', Type.Integer, None, 'Number of intervals' ],
                  [ 'integrationTime', Type.Float, None, 'Integration time' ],
                  [ 'ioChannel', Type.String, None, "Channel to save in the log file"],
                  [ 'fileName', Type.String, None, "Filename for the image"],
                  [ 'nSamples', Type.Integer, None, "Number of samples"],
                  [ 'setNewFolder', Type.Integer, None, 'Create new folder' ],
                  [ 'startIndex', Type.Integer, None, 'First image of interval' ],
                ]

    def prepare(self, motor1,startPos1,endPos1,motor2,startPos2,endPos2,nIntervals,integrationTime,ioChannel,fileName, nSamples,setNewFolder,startIndex):
        self.Time_Prepare = 0.0 #FB
        self.Time_takePreview = 0.0 #FB
        self.Time_myPostAcqHook = 0.0 #FB
        self.Time_peemGetSampleImages = 0.0#FB
        self.Time_run = 0.0 #FB
        self.startTime_MeasGroup = 0.0 #FB
        self.startTime_Move = time.time()
        self.Time_MeasGroup = 0.0 #FB
        self.Time_Move = 0.0 #FB
        start_acq = time.time() #FB
        self.countmytime = time.time()
        # Tango dp
        self.peem = PyTango.DeviceProxy(deviceName)
        self.topup = PyTango.DeviceProxy("alba03:10000/SR/CT/GATEWAY")
        self.initPreview(fileName, setNewFolder)
        # Get Args
        self.imageIndex = startIndex # For Image Name
        self.motor1 = motor1
        self.motor2 = motor2
#        self.InjectionGate = InjectionGate
        self.integrationTime = integrationTime
        self.fileName = fileName
        self.output('fb: %s' %fileName)
        self.nSamples = nSamples
        self.startIndex = startIndex
        # Config peem
        peem = PyTango.DeviceProxy(deviceName)
        self.peem = PyTango.DeviceProxy(deviceName)
        self.peem.AcquisitionInProgress=True   
        if setNewFolder == 1:
            self.execMacro("peemSetFolder %s" %fileName)
        self.execMacro("peemSetAverageImages %d" %0)
        self.execMacro("peemSetIntegrationTime %f" %integrationTime)
        self.execMacro("peemSetAEM %s" %ioChannel)
        # Config Log file
        sent_macro = "%s %s %s %s %s %s %s %s %s %s %s %s" %("peem2ScanIo_MF",motor1,startPos1,endPos1, motor2,startPos2,endPos2,nIntervals,integrationTime,ioChannel,fileName,nSamples)
        self.log = LogForPeem(self, fileName, sent_macro, setNewFolder)# Basic Peem setup
        self.Time_Prepare = time.time()-start_acq #FB

    #def SaveBLSettings(self,a,b,c):
        ##a = "/beamlines/bl24/commissioning/2016/2016_06/20160622/026_test/026_log_test.txt"
        ##b = "FB"
        ##c = "10"
        #cmd = "peemSaveBLSettings %s %s %s" %(str(a), str(b), str(c))
        #self.execMacro(cmd)
        
    def initPreview(self, subDir, setNewFolder=1):
        try:
            # Tango dp
            self.albaemzd_dp = PyTango.DeviceProxy("albaemzd")
            self.integrationPreview = PyTango.DeviceProxy("bl24/ct/integrationpreview")
            if setNewFolder == 1:
                self.integrationPreview.ResetImages()
            # Get environment variable
            env = self.getEnv('PeemFolderForImages')
            counter = self.getEnv('PeemFolderCounter')
            if setNewFolder == 1:
                self.imageDir = "%s/%03d_%s" %(env, counter, subDir) 
            else:
                self.imageDir = "%s/%03d_%s" %(env, counter-1, subDir)  
            
        except Exception,e:
            self.error("Error in initPreview") 
            self.error(str(e))          
                    
    def takePreview(self, actualFileName):
        self.output("entering take preview....")
        try:
            ImageName = self.imageDir + "/"+  actualFileName + ".dat"
            self.integrationPreview.AddPpos([ImageName])
            #self.output('Integrating Image %s'%(ImageName))
            ioChannel_I = self.albaemzd_dp.value
            self.integrationPreview.write_attribute("intensity_normal", ioChannel_I)
        except Exception,e:
            self.error("Error in takePreview") 
            self.error(str(e))
        
    def myPostMoveHook(self):
        self.Time_Move = self.Time_Move + time.time() - self.startTime_Move
        self.output('in post move...Setting Energy = %s eV' %self.motor1.position)

#    def myPreAcqHook(self):
#        self.output("Pre_Aq.. injection check ... ... ... ... ...")
#        start_acq = time.time() # FB: debug time
#-----------------------------------------------        
#if self.InjectionGate != 0: 
#            injection = False
#            if self.topup.TopUpEnabled == True:
#                self.output("TopUpEnabled")
#                if self.topup.TopUpRemaining > 10:
#                    self.countmytime = time.time()
#                else :    
#                    while ( self.countmytime - time.time() + self.topup.TopUpRemaining) < self.InjectionGate and ( self.countmytime - time.time() + self.topup.TopUpRemaining) > (-1200):     
#second argument is to protect macro from too long/failed injection period
#                        injection = True
#                        self.output("waiting for injection")
#                        time.sleep(3)
#                if injection == True:
#                    time.sleep(2)
#        self.startTime_MeasGroup = time.time() # FB: debug time
#------------------------------    
        
    def myPostAcqHook(self):
        self.output("Post_Aq.. image export... ... ... ... ...")        
        self.Time_MeasGroup = self.Time_MeasGroup + time.time() - self.startTime_MeasGroup
        start_acq = time.time() # FB: debug time
        # write name of image
        actualFileName = self.fileName +  '_%03d'%self.imageIndex 
        # getImage
        self.execMacro("peemGetSampleImagesMF %d %s %f %d" %(self.nSamples, actualFileName, self.integrationTime, 0))
        # Increase image index
        self.imageIndex = self.imageIndex+1
        self.takePreview(actualFileName)
        # Specific of post acq
        self.log.save(self)
        self.Time_myPostAcqHook = self.Time_myPostAcqHook +  time.time()-start_acq#FB
        self.startTime_Move = time.time()#FB
    
    def on_abort(self):
        if self.peem.AcquisitionInProgress:
            self.output("\nAborting: Force AcquisitionInProgress=False in peem server")
            self.peem.AcquisitionInProgress=False   
        self.log.close()

    def run(self, motor1,startPos1,endPos1, motor2,startPos2,endPos2 , nIntervals, integrationTime, ioChannel, fileName, nSamples, setNewFolder, startIndex):
        #"""Run macro"""  
        start_acq = time.time() #FB
        myMacro, pars = self.createMacro("a2scan",motor1,startPos1,endPos1,motor2,startPos2,endPos2,nIntervals,integrationTime)

        myMacro.hooks = [(self.myPostMoveHook, ['post-move'])]
        #myMacro.hooks = [(self.myPreAcqHook, ['pre-acq'])]
        myMacro.hooks = [(self.myPostAcqHook, ['post-acq'])]
        self.runMacro(myMacro) #FB
        self.Time_run = self.Time_run +  time.time()-start_acq#FB
        self.log.close()
        self.info('Time_Prepare = %.2f sec' %(self.Time_Prepare ))#FB
        self.info('Time_takePreview = %.2f sec' %(self.Time_takePreview ))#FB
        self.info('Time_myPostAcqHook = %.2f sec' %(self.Time_myPostAcqHook ))#FB
        self.info('Time_peemGetSampleImages = %.2f sec (%.2f)' %(self.Time_peemGetSampleImages,integrationTime*nIntervals*nSamples ))#FB
        self.info('Time_run = %.2f sec' %(self.Time_run ))#FB
        self.info('Time_MeasGroup = %.2f sec' %(self.Time_MeasGroup ))#FB
        self.info('Time_Move = %.2f sec' %(self.Time_Move ))#FB
      
       
###############################################################################





########## peemXAScont ##################################################### 
@macro([['startE', Type.Float, 695, 'initial voltage'],
        ['endE', Type.Float, 745, 'end voltage'],
        ['nIntervals', Type.Integer, 200, 'Number of intervals'],
        ['integrationTime', Type.Float, 1, "Integration time"],
        ['ioChannel', Type.String, "emet05_c03", "Channel to save in the log file"],
        ['fileName', Type.String, "XAS_Fe_", "Filename for the images "],
        ['nSamples', Type.Integer, 1, "Number of samples"],
        ['InjectionGate', Type.Float, 0, "pause times in s, 0=none"],
        ]
       )
def peemXAS_cont(self,startE,endE,nIntervals,integrationTime, ioChannel, fileName, nSamples, InjectionGate):
    # It calls to peem2ScanIo macro with the same values for mono-energy and ID-energy
    # using continous aquisition 
    # Force the meas Group
    gapcc = PyTango.DeviceProxy('alba03:10000/SR/CT/GATEWAY')
    polarization_mode = gapcc.read_attribute('correctionmode').value
    self.output('ID mode is %s' %polarization_mode)
    self.output('Setting Meas-Group to %s' %("emet05"))
    self.setEnv('ActiveMntGrp', "emet05")
    self.output("\nSetting Mono Energy...")
    self.execMacro("mv Energy %f" %startE)
    self.execMacro("mv Energy %f" %startE)
    
    if polarization_mode == True :                  #in P mode
        self.output("peem2ScanIo_MF Energy %f %f ideu62_motor_energy %f %f %d %f %s %s %d %f" %(startE,endE, startE,endE,nIntervals,integrationTime,ioChannel,fileName,nSamples,InjectionGate))
        self.execMacro("peem2ScanIo_MF Energy %f %f ideu62_motor_energy %f %f %d %f %s %s %d %f" %(startE,endE, startE,endE,nIntervals,integrationTime,ioChannel,fileName,nSamples,InjectionGate))
    elif polarization_mode == False :                 #in AP mode       
        self.output("peem2ScanIo_MF Energy %f %f ideu62_energy_plus %f %f %d %f %s %s %d %f" %(startE,endE, startE,endE,nIntervals,integrationTime,ioChannel,fileName,nSamples,InjectionGate))
        self.execMacro("peem2ScanIo_MF Energy %f %f ideu62_energy_plus %f %f %d %f %s %s %d %f" %(startE,endE, startE,endE,nIntervals,integrationTime,ioChannel,fileName,nSamples,InjectionGate))
    
    
###############################################################################










########### peemScanVoltage ################################################
# This macro scan the voltage
@macro([['initVoltage', Type.Float, None, 'initial voltage'],
        ['endVoltage', Type.Float, None, 'end voltage'],
        ['nIntervals', Type.Integer, None, 'Number of intervals'],
        ['integrationTime', Type.Float, None, "Integration time"],
        ["fileName", Type.String, None, "Filename for the images "],
        ['nSamples', Type.Integer, None, "Number of samples"],
        ]
       )
def peemScanVoltage(self,initVoltage,endVoltage,nIntervals,integrationTime,fileName,nSamples):
    # Tango dp
    peem = PyTango.DeviceProxy(deviceName)
    self.peem = PyTango.DeviceProxy(deviceName)
    # Basic Peem setup
    self.execMacro("peemSetFolder %s" %fileName)
    self.execMacro("peemSetAverageImages %d" %0)
    #self.execMacro("peemSetSeqMode %b" %true)  #(MF 05062014)
    self.execMacro("peemSetIntegrationTime %f" %integrationTime)

    # Configure Voltage range
    incr = (endVoltage - initVoltage)/nIntervals
    # Perform n iterations
    self.peem.AcquisitionInProgress=True    
    for iteration in range(nIntervals+1):
        # Setting StartVoltage
        currentValue = initVoltage + (iteration * incr)
        self.execMacro("peemSetStartVoltage %f" %currentValue)
        # Better waiting a little before taking a new image...
        time.sleep(0.2)
        # For each iteration take "nSamples" images
        actualFileName = "%s_%03d" %(fileName, iteration)
        self.execMacro("peemGetSampleImagesMF %d %s %f %d" %(nSamples, actualFileName, integrationTime, 0))

###############################################################################
    




########### peemScanObjective ##############################################
# This macro scan the Objective
@macro([['initObjective', Type.Float, None, 'initial Objective'],
        ['endObjective', Type.Float, None, 'end Objective'],
        ['nIntervals', Type.Integer, None, 'Number of intervals'],
        ['integrationTime', Type.Float, None, "Integration time"],
        ["fileName", Type.String, None, "Filename for the images "],
        ['nSamples', Type.Integer, None, "Number of samples"],
        ]
       )
def peemScanObjective(self,initObjective,endObjective,nIntervals,integrationTime,fileName,nSamples):
    # Tango dp
    peem = PyTango.DeviceProxy(deviceName)
    # Basic Peem setup
    self.execMacro("peemSetFolder %s" %fileName)
    self.execMacro("peemSetAverageImages %d" %0)
    self.execMacro("peemSetIntegrationTime %f" %integrationTime)

    # Configure Objective range
    incr = (endObjective - initObjective)/nIntervals
    # Perform n iterations
    for iteration in range(nIntervals+1):
        # Setting StartObjective
        currentValue = initObjective + (iteration * incr)
        self.execMacro("peemSetObjective %f" %currentValue)
        # Better waiting a little before taking a new image...
        time.sleep(0.5)

        # For each iteration take "nSamples" images
        actualFileName = "%s_%03d" %(fileName, iteration)
        self.execMacro("peemGetSampleImages %d %s" %(nSamples, actualFileName))

###############################################################################


class peemA2ScanVoltage(Macro):
    
    param_def = [['initVoltage', Type.Float, None, 'initial voltage'],
                    ['endVoltage', Type.Float, None, 'end voltage'],
                    ['initObjective', Type.Float, None, 'initial Objective'],
                    ['endObjective', Type.Float, None, 'end Objective'],
                    ['nIntervals', Type.Integer, None, 'Number of intervals'],
                    ['integrationTime', Type.Float, None, "Integration time"],
                    ['ioChannel', Type.String, "emet05_c03", "Channel to save in the log file"],
                    ["fileName", Type.String, "XPS_", "Filename for the images "],
                    ['nSamples', Type.Integer, 1, "Number of samples"],
                    ]

    def prepare(self, initVoltage, endVoltage, initObjective, endObjective, nIntervals, integrationTime, ioChannel, fileName, nSamples):
        self.execMacro("peemSetFolder %s" %fileName)
        self.execMacro("peemSetAverageImages %d" %0)
        self.execMacro("peemSetIntegrationTime %f" %integrationTime)

        # FB09-Jul-2015 Config Log file
        self.initPreview(fileName)
        self.execMacro("peemSetAEM %s" %ioChannel)
        sent_macro = "%s %s %s %s %s %s %s %s %s %s" %("peemA2ScanVoltage",initVoltage, endVoltage, initObjective, endObjective, nIntervals, integrationTime, ioChannel, fileName, nSamples)
        self.log = LogForPeem(self, fileName, sent_macro)# Basic Peem setup

    # FB09-Oct-2015 
    def startMeasurementGroup(self, integrationTime):
        try:
            time.sleep(0.2)
            mntGrpName = self.getEnv('ActiveMntGrp')
            self.mntGrp = self.getObj(mntGrpName,
            type_class=Type.MeasurementGroup)
            cfg = self.mntGrp.getConfiguration()
            cfg.prepare()
            self.mntGrp.putIntegrationTime(integrationTime)
            self.countId = self.mntGrp.start()    
            return True
        except Exception,e:
            self.error("Error in startMeasurementGroup") 
            self.error(str(e))          
            return False

    # FB09-Oct-2015 
    def readMeasurementGroup(self):
        try:
            #self.prepareMntGrp()
            self.mntGrp.waitFinish(id=self.countId)
            return self.mntGrp.getValues()     
        except Exception,e:
            self.error("Error in readMeasurementGroup") 
            self.error(str(e))      
            return None

    def run(self, initVoltage, endVoltage, initObjective, endObjective, nIntervals, integrationTime, ioChannel, fileName, nSamples):
        #   Configure Voltage and Objective ranges
        incrVoltage = (endVoltage - initVoltage)/nIntervals
        incrObjective = (endObjective - initObjective)/nIntervals
        # Perform n iterations          
        for iteration in range(nIntervals+1):
            # Setting StartVoltage and Objective
            currentVoltage = initVoltage + (iteration * incrVoltage)
            currentObjective = initObjective + (iteration * incrObjective)
            self.execMacro("peemSetStartVoltage %f" %currentVoltage)
            self.execMacro("peemSetObjective %f" %currentObjective)
            # Better waiting a little before taking a new image, but commented while we have the 1.7s delay anyway #20141020
            #time.sleep(0.5)
            # For each iteration take "nSamples" images # For each iteration take "nSamples" images
            actualFileName = "%s_%03d" %(fileName, iteration)
            # FB09-Oct-2015 here start msgG (I0 current, integrate)
            bl = self.startMeasurementGroup(integrationTime)  
            self.execMacro("peemGetSampleImages %d %s" %(nSamples, actualFileName))
            # FB09-Oct-2015 here read value of MsG (I0, E_val)
            if bl ==True:
                new_data = self.readMeasurementGroup() 
            #self.output(new_data)
            
            self.takePreview(actualFileName)
            self.log.save(self)

        # FB09-Jul-2015 Config Log file
        self.log.close()

        
    def initPreview(self, subDir):
        try:
            # Tango dp
            self.albaemzd_dp = PyTango.DeviceProxy("albaemzd")
            self.integrationPreview = PyTango.DeviceProxy("bl24/ct/integrationpreview")
            self.integrationPreview.ResetImages()
            # Get environment variable
            env = self.getEnv('PeemFolderForImages')
            counter = self.getEnv('PeemFolderCounter')
            # FB03-Sep2015 one index less for the directory
            self.imageDir = "%s/%03d_%s" %(env, counter-1, subDir) 
            
        except Exception,e:
            self.error("Error in initPreview") 
            self.error(str(e))          
                    
    def takePreview(self, actualFileName):
        try:
            ImageName = self.imageDir + "/"+  actualFileName + ".dat"
            self.integrationPreview.AddPpos([ImageName])
            #self.output('Integrating Image %s'%(ImageName))
            ioChannel_I = self.albaemzd_dp.value
            self.integrationPreview.write_attribute("intensity_normal", ioChannel_I)
        except Exception,e:
            self.error("Error in takePreview") 
            self.error(str(e))

class peemA3ScanVoltageEnergyAVG16(Macro):
    
    param_def = [['initVoltage', Type.Float, None, 'initial voltage'],
                    ['endVoltage', Type.Float, None, 'end voltage'],
                    ['initEnergy', Type.Float, None, 'initial Objective'],
                    ['endEnergy', Type.Float, None, 'end Objective'],
                    ['nIntervals', Type.Integer, None, 'Number of intervals'],
                    ['integrationTime', Type.Float, None, "Integration time"],
                    ['ioChannel', Type.String, None, "Channel to save in the log file"],
                    ["fileName", Type.String, None, "Filename for the images "],
                    ['nSamples', Type.Integer, None, "Number of samples"],
                    ]

    def prepare(self, initVoltage, endVoltage, initObjective, endObjective, nIntervals, integrationTime, ioChannel, fileName, nSamples):
        self.execMacro("peemSetFolder %s" %fileName)
        self.execMacro("peemSetAverageImages %d" %8)
        self.execMacro("peemSetIntegrationTime %f" %integrationTime)

        # FB09-Jul-2015 Config Log file
        self.initPreview(fileName)
        self.execMacro("peemSetAEM %s" %ioChannel)
        sent_macro = "%s %s %s %s %s %s %s %s %s %s" %("peemA3ScanVoltageEnergyAVG16",initVoltage, endVoltage, initObjective, endObjective, nIntervals, integrationTime, ioChannel, fileName, nSamples)
        self.log = LogForPeem(self, fileName, sent_macro)# Basic Peem setup



    def run(self, initVoltage, endVoltage, initEnergy, endEnergy, nIntervals, integrationTime, ioChannel, fileName, nSamples):
        #   Configure Voltage and Objective ranges
        incrVoltage = (endVoltage - initVoltage)/nIntervals
        incrEnergy = (endEnergy - initEnergy)/nIntervals
        # Perform n iterations
        for iteration in range(nIntervals+1):
            # Setting StartVoltage and Energy
            currentVoltage = initVoltage + (iteration * incrVoltage)
            currentEnergy = initEnergy + (iteration * incrEnergy)
            self.execMacro("peemSetStartVoltage %f" %currentVoltage)
            self.execMacro("mv Energy %f" %currentEnergy)   
            self.execMacro("mv ideu62_motor_energy %f" %currentEnergy)
            # Better waiting a little before taking a new image, but commented while we have the 1.7s delay anyway #20141020
            #time.sleep(0.5)
            # For each iteration take "nSamples" images # For each iteration take "nSamples" images
            actualFileName = "%s_%03d" %(fileName, iteration)
            self.execMacro("peemGetSampleImages %d %s" %(nSamples, actualFileName))
            # FB09-Jul-2015 Config Log file
            self.takePreview(actualFileName)
            self.log.save(self)

        # FB09-Jul-2015 Config Log file
        self.log.close()

        
    def initPreview(self, subDir):
        try:
            # Tango dp
            self.albaemzd_dp = PyTango.DeviceProxy("albaemzd")
            self.integrationPreview = PyTango.DeviceProxy("bl24/ct/integrationpreview")
            self.integrationPreview.ResetImages()
            # Get environment variable
            env = self.getEnv('PeemFolderForImages')
            counter = self.getEnv('PeemFolderCounter')
            self.imageDir = "%s/%03d_%s" %(env, counter, subDir) 
            
        except Exception,e:
            self.error("Error in initPreview") 
            self.error(str(e))          
                    
    def takePreview(self, actualFileName):
        try:
            ImageName = self.imageDir + "/"+  actualFileName + ".dat"
            self.integrationPreview.AddPpos([ImageName])
            #self.output('Integrating Image %s'%(ImageName))
            ioChannel_I = self.albaemzd_dp.value
            self.integrationPreview.write_attribute("intensity_normal", ioChannel_I)
        except Exception,e:
            self.error("Error in takePreview") 
            self.error(str(e))




#####OLD # FB09-Jul-2015 ########### peemA2ScanVoltage ##############################################
## This macro scan the voltage and the objective
#@macro([['initVoltage', Type.Float, None, 'initial voltage'],
        #['endVoltage', Type.Float, None, 'end voltage'],
        #['initObjective', Type.Float, None, 'initial Objective'],
        #['endObjective', Type.Float, None, 'end Objective'],
        #['nIntervals', Type.Integer, None, 'Number of intervals'],
        #['integrationTime', Type.Float, None, "Integration time"],
        #["fileName", Type.String, None, "Filename for the images "],
        #['nSamples', Type.Integer, None, "Number of samples"],
        #]
       #)
#def peemA2ScanVoltage(self,initVoltage,endVoltage,initObjective,endObjective,nIntervals,integrationTime,fileName, nSamples):
    ## Tango dp
    #peem = PyTango.DeviceProxy(deviceName)

    ## Basic Peem setup
    #self.execMacro("peemSetFolder %s" %fileName)
    #self.execMacro("peemSetAverageImages %d" %0)
    #self.execMacro("peemSetIntegrationTime %f" %integrationTime)

    ## Configure Voltage and Objective ranges
    #incrVoltage = (endVoltage - initVoltage)/nIntervals
    #incrObjective = (endObjective - initObjective)/nIntervals
    ## Perform n iterations
    #for iteration in range(nIntervals+1):
        ## Setting StartVoltage and Objective
        #currentVoltage = initVoltage + (iteration * incrVoltage)
        #currentObjective = initObjective + (iteration * incrObjective)
        #self.execMacro("peemSetStartVoltage %f" %currentVoltage)
        #self.execMacro("peemSetObjective %f" %currentObjective)
        ## Better waiting a little before taking a new image, but commented while we have the 1.7s delay anyway #20141020
        ##time.sleep(0.5)
        ## For each iteration take "nSamples" images # For each iteration take "nSamples" images
        #actualFileName = "%s_%03d" %(fileName, iteration)
        #self.execMacro("peemGetSampleImages %d %s" %(nSamples, actualFileName))


################################################################################







########## peem2images ###########################################################
# This macro calculate the difference between two polarizations at the same energy
#or between two energies at LH and LV polarization. This depends on the input of the parameter
# SwitchesorE2. Values 1,2 will launch an XMCD measurement wiht either one or two switches of the ID

@macro([['photEnergy', Type.Float, 776, 'photon energy'],
        ['numImages', Type.Integer, 64, 'number of images per polarization'],
        ['integrationTime', Type.Float, 1, "Integration time"],
        ['SwitchesOrE2', Type.Float, 1, "Switches or E2"],  # for the future
        ['fileName', Type.String,"XMCD_Co", "Only the filename for the images "],
        ['IDoffset_plus', Type.Float, 36, "ID energy offset in C+ polarization"],
        ['IDoffset_min', Type.Float, 40, "ID energy offset in C- polarization"],
        ['Internal_Avg (1,2,4,8,16,...)', Type.Integer, 1, "Uview_internal averages (1,2,4,8,.."],
        ]
       )
def peem2Images(self,photEnergy,numImages,integrationTime,SwitchesOrE2,fileName,IDoffset_plus,IDoffset_min, Avg):
    # Tango dp
    peem = PyTango.DeviceProxy(deviceName)
    self.peem = PyTango.DeviceProxy(deviceName)
    PeemPreviewDs = PyTango.DeviceProxy(devicePreview)
    PeemPreviewDs.ResetImages()
    # Basic Peem setup
    self.execMacro("peemSetFolder %s" %fileName)
    if Avg != 1:
        self.execMacro("peemSetAverageImages %d" %Avg)   #set here internal average
    else:
        self.execMacro("peemSetAverageImages %d" %0)   #set here internal average
    self.execMacro("peemSetIntegrationTime %f" %integrationTime)
    self.peem.AcquisitionInProgress=True    
    self.output("\nSetting Mono Energy...")
    self.execMacro("mv Energy %f" %photEnergy)
    self.execMacro("mv Energy %f" %photEnergy)
    self.execMacro("mv Energy %f" %photEnergy)
   
#---images with positive polarization
    IDoffset = IDoffset_plus
    polarization = numpy.pi/4
    iterations = numImages
    label = 'plus'
    numberingOffset = 0
    macrostring1 = "_peemXMCDloop_MF %f %d %f %s %f %f %d %s %d %d" %(photEnergy,numImages,integrationTime,fileName,IDoffset,polarization,iterations,label,numberingOffset, Avg)

#---images with circular negative
    IDoffset = IDoffset_min
    polarization = -numpy.pi/4
    iterations = numImages
    label = 'min'
    numberingOffset = 0
    macrostring2 = "_peemXMCDloop_MF %f %d %f %s %f %f %d %s %d %d" %(photEnergy,numImages,integrationTime,fileName,IDoffset,polarization,iterations,label,numberingOffset, Avg)

#---images with positive polarization (first half)
    IDoffset = IDoffset_plus
    polarization = numpy.pi/4
    iterations = numImages/2
    label = 'plus'
    numberingOffset = 0

    macrostring4 = "_peemXMCDloop_MF %f %d %f %s %f %f %d %s %d %d" %(photEnergy,numImages,integrationTime,fileName,IDoffset,polarization,iterations,label,numberingOffset, Avg)

#---half of the images with circular positive (second half)
    IDoffset = IDoffset_plus
    polarization = numpy.pi/4
    iterations = numImages/2
    label = 'plus'
    numberingOffset = numImages/2

    macrostring3 = "_peemXMCDloop_MF %f %d %f %s %f %f %d %s %d %d"     %(photEnergy,numImages,integrationTime,fileName,IDoffset,polarization,iterations,label,numberingOffset, Avg)

#---images with circular negative (first half)
    IDoffset = IDoffset_min
    polarization = -numpy.pi/4
    iterations = numImages/2
    label = 'min'
    numberingOffset = 0

    macrostring5 = "_peemXMCDloop_MF %f %d %f %s %f %f %d %s %d %d" %(photEnergy,numImages,integrationTime,fileName,IDoffset,polarization,iterations,label,numberingOffset, Avg)

#---images with circular negative (first half)
    IDoffset = IDoffset_min
    polarization = -numpy.pi/4
    iterations = numImages/2
    label = 'min'
    numberingOffset = numImages/2

    macrostring6 = "_peemXMCDloop_MF %f %d %f %s %f %f %d %s %d %d" %(photEnergy,numImages,integrationTime,fileName,IDoffset,polarization,iterations,label,numberingOffset, Avg)

#---images with E1
    IDoffset = IDoffset_plus
    polarization = 0.0
    iterations = numImages
    label = 'plus'
    numberingOffset = 0
    macrostring7 = "_peemXMCDloop_MF %f %d %f %s %f %f %d %s %d %d" %(photEnergy,numImages,integrationTime,fileName,IDoffset,polarization,iterations,label,numberingOffset, Avg)

#---images with E1
    IDoffset = IDoffset_plus
    polarization = 0.001
    iterations = numImages
    label = 'plus'
    numberingOffset = 0
    macrostring7b = "_peemXMCDloop_MF %f %d %f %s %f %f %d %s %d %d" %(photEnergy,numImages,integrationTime,fileName,IDoffset,polarization,iterations,label,numberingOffset, Avg)

#---images with E2
    IDoffset = IDoffset_plus
    polarization = 0
    iterations = numImages
    label = 'min'
    numberingOffset = 0
    macrostring8 = "_peemXMCDloop_MF %f %d %f %s %f %f %d %s %d %d" %(SwitchesOrE2,numImages,integrationTime,fileName,IDoffset,polarization,iterations,label,numberingOffset, Avg)

#---images with E1
    IDoffset = IDoffset_plus
    polarization = 1.57078
    iterations = numImages
    label = 'min'
    numberingOffset = 0  #now used in XLD togther with 7b
    macrostring9 = "_peemXMCDloop_MF %f %d %f %s %f %f %d %s %d %d" %(photEnergy,numImages,integrationTime,fileName,IDoffset,polarization,iterations,label,numberingOffset, Avg)

#---images with E2
    IDoffset = IDoffset_plus
    polarization = 1.57078
    iterations = numImages
    label = 'min'
    numberingOffset = 1000
    macrostring10 = "_peemXMCDloop_MF %f %d %f %s %f %f %d %s %d %d" %(SwitchesOrE2,numImages,integrationTime,fileName,IDoffset,polarization,iterations,label,numberingOffset, Avg)

#---images with E1
    IDoffset = IDoffset_plus
    polarization = 0
    iterations = numImages/4
    label = 'plus'
    numberingOffset = 2*numImages/4
    macrostring11 = "_peemXMCDloop_MF %f %d %f %s %f %f %d %s %d %d" %(photEnergy,numImages,integrationTime,fileName,IDoffset,polarization,iterations,label,numberingOffset, Avg)

#---images with E2
    IDoffset = IDoffset_plus
    polarization = 0
    iterations = numImages/4
    label = 'min'
    numberingOffset = 2*numImages/4
    macrostring12 = "_peemXMCDloop_MF %f %d %f %s %f %f %d %s %d %d" %(SwitchesOrE2,numImages,integrationTime,fileName,IDoffset,polarization,iterations,label,numberingOffset, Avg)

#---images with E1
    IDoffset = IDoffset_plus
    polarization = 0
    iterations = numImages/4
    label = 'plus'
    numberingOffset = 3*numImages/4
    macrostring13 = "_peemXMCDloop_MF %f %d %f %s %f %f %d %s %d %d" %(photEnergy,numImages,integrationTime,fileName,IDoffset,polarization,iterations,label,numberingOffset, Avg)

#---images with E2
    IDoffset = IDoffset_plus
    polarization = 0
    iterations = numImages/4
    label = 'min'
    numberingOffset = 3*numImages/4
    macrostring14 = "_peemXMCDloop_MF %f %d %f %s %f %f %d %s %d %d" %(SwitchesOrE2,numImages,integrationTime,fileName,IDoffset,polarization,iterations,label,numberingOffset, Avg)


##--------------------------------------
    #if switches=1
    pmPol = PyTango.DeviceProxy("alba03:10000/pm/ideu62_energy/2")    
    Pol=pmPol.position
    if SwitchesOrE2 == 0:   #XLD mode
        self.output("\nMacro for LH")
        self.execMacro(macrostring7b)
        self.output("\nMacro for LV")
        self.execMacro(macrostring9)
    elif SwitchesOrE2 == 3:    #series at CP, no switch
        self.output("\nMacro for circular positive")
        self.execMacro(macrostring1)
    elif SwitchesOrE2 == 1:    #XMCD, one switch
        if Pol>-0.1: 
            self.output("\nMacro for circular positive")
            self.execMacro(macrostring1)
            self.output("\nMacro for circular negative")
            self.execMacro(macrostring2)
        else: 
            self.output("\nMacro for circular negative")
            self.execMacro(macrostring2)
            self.output("\nMacro for circular positive")
            self.execMacro(macrostring1)
    elif SwitchesOrE2 ==2:      #XMCD, two switches
        if Pol>-0.1: 
            self.output("\nMacro for circular positive (first half)")
            self.execMacro(macrostring4)
            self.output("\nMacro for circular negative")
            self.execMacro(macrostring2)
            self.output("\nMacro for circular positive (second half)")
            self.execMacro(macrostring3)
        else: 
            self.output("\nMacro for circular negative (first half)")
            self.execMacro(macrostring5)
            self.output("\nMacro for circular positive")
            self.execMacro(macrostring1)
            self.output("\nMacro for circular negative (second half)")
            self.execMacro(macrostring6)
    elif SwitchesOrE2 > 100 and SwitchesOrE2 < 2000:  #using this macros for two energies at default pol
        self.output("\nMacro for E1,Pol_default 1(1)")
        self.execMacro(macrostring7)        
        #self.output("\nMacro for E1, LV 1(1)")
        #self.execMacro(macrostring9)
        self.output("\nMacro for E2, Pol_default 1(1),")
        self.execMacro(macrostring8)
        #self.output("\nMacro for E2, LV 1(1)") some of these string have been changed, do not activate without confirming first what they are
        #self.execMacro(macrostring10)
        #self.output("\nMacro for E1, 3(4)")
        #self.execMacro(macrostring11)
        #self.output("\nMacro for E2, 3(4)")
        #self.execMacro(macrostring12)
        #self.output("\nMacro for E1, 4(4)")
        #self.execMacro(macrostring13)
        #self.output("\nMacro for E2, 4(4)")
        #self.execMacro(macrostring14)
    # Save image
    self.execMacro("savePeemPreviewImage %s %s" %(fileName, "FB"))


##save preview here when macro ends
#pmEnergy = PyTango.DeviceProxy("alba03:10000/pm/ideu62_energy/1")
#    self.output("\nSetting Energy %.3f..." %photEnergy )
#    self.execMacro("mv Energy %f" %photEnergy)
#    self.execMacro("mv ideu62_motor_energy %f" %photEnergy)
    ## We set the mono-energy once more for openloop/backlash corrections
#    self.output("Reading Energy %.3f..." %pmEnergy.position )
    
#if switches=2
    #........
    #self.output("\nMacro for circular positive (second half)")
    #self.execMacro(macrostring3)


# Iteration of Images for peemXMCD macro
@macro([['photEnergy', Type.Float, None, 'photon energy'],
        ['numImages', Type.Integer, None, 'number of images per polarization'],
        ['integrationTime', Type.Float, None, "Integration time"],
        ["fileName", Type.String, None, "Full windows compatible filename for the image.\n For a windows path insert \\ instead of \ "],
        ["IDoffset", Type.Float, None, "ID energy offset "],
        ["polarization", Type.Float, None, "polarization"],
        ["iterations", Type.Integer, None, "iterations"],
        ["label", Type.String, None, "label"],
        ["numberingOffset", Type.Integer, None, "numberingOffset"],
        ["Averages", Type.Integer, None, "Avg"],
        ]
       )
def _peemXMCDloop_MF(self,photEnergy,numImages,integrationTime,fileName,IDoffset,polarization,iterations,label,numberingOffset, Avg):   
    peem = PyTango.DeviceProxy(deviceName)
    starvoltage= peem.GetPSValue(38)   # by JMH 20160906 ****uncommented LA 20170213
    pmEnergy = PyTango.DeviceProxy("alba03:10000/pm/ideu62_energy/1")
    gapcc = PyTango.DeviceProxy('alba03:10000/SR/CT/GATEWAY')
    # changed 0711 - 00.10
    polarization_mode = gapcc.read_attribute('correctionmode').value # uncomment
    # end of changes
    if polarization != 0:  #For xmcd, not the actual reading/setting of the BL, but the parameter of the macrostring
        if polarization_mode == True :   #Pmode
            self.info("xmcd mode, setting polarization...")
            self.execMacro("mv ideu62_motor_polarization %f" %polarization)
        else:
            self.info("ERROR xmcd in AP mode")
    else:               #for XMLD/2 energies. NOTE: present setting of the macro in 2E is not to touch Pol at all. This is done by setting the parameter pol of the macrostring to "0". But it can be adjusted previously to any value with ctbl24 or the mv command in sequencer to the desired value. The macro will run with the adjusted pol.
        #self.execMacro("mv ideu62_motor_polarization %f" %polarization)
        self.execMacro("mv Energy %f" %photEnergy)
        self.execMacro("mv Energy %f" %photEnergy)
        self.execMacro("mv Energy %f" %photEnergy)
    pmEnergy.edOffset = IDoffset
    if polarization_mode == True :   #Pmode
        self.execMacro("mv ideu62_motor_energy %f" %photEnergy)  #for use in parallel mode
    elif polarization_mode == False : #APmode
        self.execMacro("mv ideu62_energy_plus %f" %photEnergy)  #for use in ANTIparallel mode
    time.sleep(integrationTime)
    
    # set by JMH 13:30 20160906
    self.execMacro("peemSetStartVoltage %f" %starvoltage)  #  (in case of bing during switching)****uncommented LA 20170213
    time.sleep(5)  #to compensate charging, can be adjusted
    env = self.getEnv('PeemFolderForImages')
    self.output('PeemFolderForImages = %s'%(env))
    counter = self.getEnv('PeemFolderCounter')
    for it in range(iterations):           
        actualFileName = fileName +  '_' + str(label) + '_%03d'%(it+numberingOffset)
        actualFileName = actualFileName.split("\\")[-1]
        self.nSamples = 1

        try:
            self.execMacro("peemGetSampleImagesMF %d %s %f %i" %(self.nSamples, actualFileName, integrationTime, Avg))

            fullImageName = '%s/%03d_%s/%s.dat'%(env,counter-1,fileName, actualFileName)
            imageToSave = "A"
            if label =="min":
                imageToSave = "B"
            self.execMacro("addPeemPreviewImage %s %s" %(fullImageName, imageToSave))

        except Exception,e:
            self.error("!!!WARNING: image lost: %s" %(actualFileName))

###############################################################################





################### addPeemPreviewImage  ######################################
#  This macro adds an image to the peem preview ds
@macro([
        [ 'ImageName', Type.String, None, "Name of the image"],
        [ 'ImageToSave', Type.String, "A", "Image to save in preview ds "],
        ]
       )
def addPeemPreviewImage(self,ImageName, ImageToSave ):
    PeemPreviewDs = PyTango.DeviceProxy(devicePreview)
 
    if ImageToSave=="A":
        PeemPreviewDs.AddImageA([ImageName])
        self.output('Adding Image (A) = %s'%(ImageName))
    elif ImageToSave=="B":
        PeemPreviewDs.AddImageB([ImageName,])
        self.output('Adding Image (B) = %s'%(ImageName))

    PeemPreviewDs.diffImage()

###############################################################################





################### savePeemPreviewImage  ######################################
#  This macro adds an image to the peem preview ds
@macro([
        [ 'fileName', Type.String, None, "Name of the image"],
        [ 'prefix', Type.String, None, "XMCD or XMLD"],
        ]
       )
def savePeemPreviewImage(self,fileName, prefix ):
    PeemPreviewDs = PyTango.DeviceProxy(devicePreview)

    # Save image
    env = self.getEnv('PeemFolderForImages')
    counter = self.getEnv('PeemFolderCounter')
    extension = 'jpg'
    fullImageName = '%s/%03d_%s/%03d_%s_preview.%s'%(env,counter-1,fileName, counter-1,prefix, extension)


    self.output('Saving Image %s '%(fullImageName))
    PeemPreviewDs.SaveImage(fullImageName)

###############################################################################




class peemSaveBLSettings(Macro):
    
    param_def = [   
                    ['file_name', Type.String, None, "Complete file name: dir+file"],
                    ['macro_info', Type.String, None, "Macro name and parameters"],
                    ['scan_id', Type.Integer, None, 'Identification Number'],
                    ]

    def prepare(self, file_name, macro_info, scan_id):
        try:
            #counter = self.getEnv('PeemFolderCounter')
            self.fd = open(file_name,'wa')
        except Exception,e:
            self.error('Error in peemSaveBLSettings macro prepare')
            
            self.error(str(e)) 

    def run(self, file_name, macro_info, scan_id):
        try:
            
            self.fd.write("scan_ID = %d \n" %(scan_id))  
            self.fd.write(macro_info + "\n")

            dp = PyTango.DeviceProxy("alba03:10000/pm/ideu62_energy/1") 
            scan_string = "ID motor energy = %f\n" %(dp.position)
            self.fd.write(scan_string)

            dp = PyTango.DeviceProxy("alba03:10000/pm/ideu62_energy/2") 
            scan_string = "ID motor polar. = %f\n" %(dp.position)
            self.fd.write(scan_string)

            dp = PyTango.DeviceProxy("alba03:10000/pm/ideu62_energyplus/1") 
            scan_string = "ID motor energy (AntiPararallel mode) = %f\n" %(dp.position)
            self.fd.write(scan_string)

            dp = PyTango.DeviceProxy("alba03:10000/pm/ideu62_energyplus/2") 
            scan_string = "ID motor polar. (AntiPararallel mode) = %f\n" %(dp.position)
            self.fd.write(scan_string)
            scan_string = "ID motor offset (AntiPararallel mode) = %f\n" %(dp.edOffset)
            self.fd.write(scan_string)

            dp = PyTango.DeviceProxy("motor/icepap_ctrl/23") 
            dp2 = PyTango.DeviceProxy("ioregister/ioregister_ctrl/3") 
            scan_string = "GRX = %f ( = %d)\n" %(dp.position, dp2.value)
            self.fd.write(scan_string)

            dp = PyTango.DeviceProxy("pm/energy_ctrl/1") 
            scan_string = "Mono energy = %f\n" %(dp.position)
            self.fd.write(scan_string)

            dp = PyTango.DeviceProxy("pm/energy_ctrl/2") 
            scan_string = "Mono cff = %f\n" %(dp.position)
            self.fd.write(scan_string)

        except Exception,e:
            self.error('Error in peemSaveBLSettings macro run')
            
            self.error(str(e)) 
        self.fd.close()

########## peemXAS #####################################################

@macro([['startE1', Type.Float, 695 , 'initial voltage1'],
                ['stepsize1', Type.Float, 1, 'Stepsize of intervals1'],
                ['startE2', Type.Float, 705, 'initial voltage2'],
                ['stepsize2', Type.Float, 0.1, 'Stepsize of intervals2'],
                ['startE3', Type.Float, 713, 'initial voltage3'],
                ['stepsize3', Type.Float, 1, 'Stepsize of intervals3'],
                ['startE4', Type.Float, 718, 'initial voltage4'],
                ['stepsize4', Type.Float, 0.1, 'Stepsize of intervals4'],
                ['startE5', Type.Float, 726, 'initial voltage5'],
                ['stepsize5', Type.Float, 1, 'Stepsize of intervals5'],
                ['endE', Type.Float, 745, 'end voltage'],
        #['nIntervals', Type.Integer, None, 'Number of intervals'],
                ['integrationTime', Type.Float, 1, "Integration time"],
        #['ioChannel', Type.String, None, "Channel to save in the log file"],
                ['fileName', Type.String, "test", "Filename for the images "],
                ['nSamples', Type.Integer, 1, "Number of samples"],
                ['Avg', Type.Integer, 0, "Number of images to average"],

#numbering offset: initially 0, updates at every run (number of steps)      
                ]
       )
# generates different runs with each interval, calculate number of intervals from stepsize (input)
#internal variables setNewFolder and startImage that controls folder creation and batch name to avoid overwritting images
#protects entry stepsize != 0 and stops when startE from last interval is the same as new startE
def peemXAS(self, startE1, stepsize1, startE2, stepsize2, startE3, stepsize3,startE4,stepsize4,startE5,stepsize5,endE,integrationTime,fileName,nSamples,Avg):
    gapcc = PyTango.DeviceProxy('alba03:10000/SR/CT/GATEWAY')
    polarization_mode = gapcc.read_attribute('correctionmode').value
    self.output('ID mode is %s' %polarization_mode)
    self.output('Setting Meas-Group to %s' %("emet05"))
    self.setEnv('ActiveMntGrp', "emet05")
    self.output("\nSetting Mono Energy...")
    self.execMacro("mv Energy %f" %startE1)
    self.execMacro("mv Energy %f" %startE1)
    #self.setNewfolder = setNewfolder    
#sent_macro = "%s %s %s %s %s %s %s %s %s %s %s %s" %("XASranges",startE1,stepsize1,startE2, stepsize2,startE3,stepsize3,startE4,stepsize4,startE5,integrationTime,fileName)
    #self.log = LogForPeem(self, fileName, sent_macro)# Basic Peem setup
    if stepsize1 != 0:
        nsteps1 = int((startE2-startE1)/stepsize1)
    else:
        nsteps1 = 0        # stop run when stepsize input is 0
    if stepsize2 != 0:
        nsteps2 = int((startE3-startE2)/stepsize2)-1
    else:
        nsteps2 = 0
    if stepsize3 != 0:
        nsteps3 = int((startE4-startE3)/stepsize3)-1
    else:
        nsteps3 = 0
    if stepsize4 != 0:
        nsteps4 = int((startE5-startE4)/stepsize4)-1
    else:
        nsteps4 = 0
    if stepsize5 != 0:
        nsteps5 = int((endE-startE5)/stepsize5)-1
    else:
        nsteps5 = 0
    setNewFolder = 1                        # boolean to select when create new folder
    self.output("\ncheck")
    if polarization_mode == True :
        if nsteps1 != 0:    # E2>E1 and stepsize input != 0
            startImage = 0
            self.output("peem2ScanIo_MF Energy %f %f ideu62_motor_energy %f %f %d %f %s %s %d %d %d" %(startE1,startE2,startE1,startE2,nsteps1,integrationTime,IOCHANNEL,fileName,nSamples,setNewFolder,startImage))
            self.execMacro("peem2ScanIo_MF Energy %f %f ideu62_motor_energy %f %f %d %f %s %s %d %d %d" %(startE1,startE2,startE1,startE2,nsteps1,integrationTime,IOCHANNEL,fileName,nSamples,setNewFolder,startImage))
            if nsteps2 != 0:
                setNewFolder = 0
                startImage = nsteps1+1
                startE2 += stepsize2
                self.output("peem2ScanIo_MF Energy %f %f ideu62_motor_energy %f %f %d %f %s %s %d %d %d" %(startE2,startE3,startE2,startE3,nsteps2,integrationTime,IOCHANNEL,fileName,nSamples,setNewFolder,startImage))
                self.execMacro("peem2ScanIo_MF Energy %f %f ideu62_motor_energy %f %f %d %f %s %s %d %d %d"%(startE2,startE3,startE2,startE3,nsteps2,integrationTime,IOCHANNEL,fileName,nSamples,setNewFolder,startImage))
                if nsteps3 != 0:
                    startImage = nsteps1+nsteps2+2
                    startE3 += stepsize3
                    self.output("peem2ScanIo_MF Energy %f %f ideu62_motor_energy %f %f %d %f %s %s %d %d %d" %(startE3,startE4,startE3,startE4,nsteps3,integrationTime,IOCHANNEL,fileName,nSamples,setNewFolder,startImage))
                    self.execMacro("peem2ScanIo_MF Energy %f %f ideu62_motor_energy %f %f %d %f %s %s %d %d %d" %(startE3,startE4,startE3,startE4,nsteps3,integrationTime,IOCHANNEL,fileName,nSamples,setNewFolder,startImage))
                    if nsteps4 != 0:
                        startImage = nsteps1+nsteps2+nsteps3+3
                        startE4 += stepsize4
                        self.output("peem2ScanIo_MF Energy %f %f ideu62_motor_energy %f %f %d %f %s %s %d %d %d" %(startE4,startE5,startE4,startE5,nsteps4,integrationTime,IOCHANNEL,fileName,nSamples,setNewFolder,startImage))
                        self.execMacro("peem2ScanIo_MF Energy %f %f ideu62_motor_energy %f %f %d %f %s %s %d %d %d" %(startE4,startE5,startE4,startE5,nsteps4,integrationTime,IOCHANNEL,fileName,nSamples,setNewFolder,startImage))
                        if nsteps5 != 0:
                            startImage = nsteps1+nsteps2+nsteps3+nsteps4+4
                            startE5 += stepsize5
                            self.output("peem2ScanIo_MF Energy %f %f ideu62_motor_energy %f %f %d %f %s %s %d %d %d" %(startE5,endE,startE5,endE,nsteps5,integrationTime,IOCHANNEL,fileName,nSamples,setNewFolder,startImage))
                            self.execMacro("peem2ScanIo_MF Energy %f %f ideu62_motor_energy %f %f %d %f %s %s %d %d %d" %(startE5,endE,startE5,endE,nsteps5,integrationTime,IOCHANNEL,fileName,nSamples,setNewFolder,startImage))
    elif polarization_mode == False :                 #in AP mode
        if nsteps1 != 0:    # E2>E1 and stepsize input != 0
            startImage = 0
            self.output("peem2ScanIo_MF Energy %f %f ideu62_energy_plus %f %f %d %f %s %s %d %d %d" %(startE1,startE2,startE1,startE2,nsteps1,integrationTime,IOCHANNEL,fileName,nSamples,setNewFolder,startImage))
            self.execMacro("peem2ScanIo_MF Energy %f %f ideu62_energy_plus %f %f %d %f %s %s %d %d %d" %(startE1,startE2,startE1,startE2,nsteps1,integrationTime,IOCHANNEL,fileName,nSamples,setNewFolder,startImage))
            if nsteps2 != 0:
                setNewFolder = 0
                startImage = nsteps1+1
                startE2 += stepsize2
                self.output("peem2ScanIo_MF Energy %f %f ideu62_energy_plus %f %f %d %f %s %s %d %d %d" %(startE2,startE3,startE2,startE3,nsteps2,integrationTime,IOCHANNEL,fileName,nSamples,setNewFolder,startImage))
                self.execMacro("peem2ScanIo_MF Energy %f %f ideu62_energy_plus %f %f %d %f %s %s %d %d %d"%(startE2,startE3,startE2,startE3,nsteps2,integrationTime,IOCHANNEL,fileName,nSamples,setNewFolder,startImage))
                if nsteps3 != 0:
                    startImage = nsteps1+nsteps2+2
                    startE3 += stepsize3
                    self.output("peem2ScanIo_MF Energy %f %f ideu62_energy_plus %f %f %d %f %s %s %d %d %d" %(startE3,startE4,startE3,startE4,nsteps3,integrationTime,IOCHANNEL,fileName,nSamples,setNewFolder,startImage))
                    self.execMacro("peem2ScanIo_MF Energy %f %f ideu62_energy_plus %f %f %d %f %s %s %d %d %d" %(startE3,startE4,startE3,startE4,nsteps3,integrationTime,IOCHANNEL,fileName,nSamples,setNewFolder,startImage))
                    if nsteps4 != 0:
                        startImage = nsteps1+nsteps2+nsteps3+3
                        startE4 += stepsize4
                        self.output("peem2ScanIo_MF Energy %f %f ideu62_energy_plus %f %f %d %f %s %s %d %d %d" %(startE4,startE5,startE4,startE5,nsteps4,integrationTime,IOCHANNEL,fileName,nSamples,setNewFolder,startImage))
                        self.execMacro("peem2ScanIo_MF Energy %f %f ideu62_energy_plus %f %f %d %f %s %s %d %d %d" %(startE4,startE5,startE4,startE5,nsteps4,integrationTime,IOCHANNEL,fileName,nSamples,setNewFolder,startImage))
                        if nsteps5 != 0:
                            startImage = nsteps1+nsteps2+nsteps3+nsteps4+4
                            startE5 += stepsize5
                            self.output("peem2ScanIo_MF Energy %f %f ideu62_energy_plus %f %f %d %f %s %s %d %d %d" %(startE5,endE,startE5,endE,nsteps5,integrationTime,IOCHANNEL,fileName,nSamples,setNewFolder,startImage))
                            self.execMacro("peem2ScanIo_MF Energy %f %f ideu62_energy_plus %f %f %d %f %s %s %d %d %d" %(startE5,endE,startE5,endE,nsteps5,integrationTime,IOCHANNEL,fileName,nSamples,setNewFolder,startImage))


class peemRFSetPower(Macro):
    param_def = [ [ 'power', Type.Float, None , 'Power in dBm' ],
                ]

    def prepare(self, power):
        if power > -10:
            self.error("User power limit exceeded!")
        else:
            self.dp = PyTango.DeviceProxy('bl24/eh/signalgenerator-01')


    def run(self, power):
        try:
            self.dp.write_attribute("PowerLevel",power)
        except Exception,e:
            self.error('Error in writing attributes')
            #self.error(str(e)) 

class peemRFSetPhase(Macro):
    param_def = [ [ 'phase', Type.Float, 90, 'phase in degree' ],
                ]

    def prepare(self, phase):
        self.dp = PyTango.DeviceProxy('bl24/eh/signalgenerator-01')


    def run(self, phase):
        try:
            self.dp.write_attribute("Phase",phase)
        except Exception,e:
            self.error('Error in writing attributes')
            #self.error(str(e)) 


####### FB to be commissioned ####################
DIRX = "/beamlines/bl24/projects/cycle2017-I/2016091885-lperez/DATA/20170214/057_XMCD_FeL3/"
MINX = "XMCD_FeL3_min_"#000.dat"
NUM_OF_IMAGE = 12
IMAGE_NAME = str("%s%s%03d.dat" %(DIRX,MINX,NUM_OF_IMAGE))

class peemReadImage(Macro):
    param_def = [ [ 'imageName', Type.String, IMAGE_NAME, 'Full Name of the Image' ],
                ]
  
    def prepare(self, imageName):
        pass

    def run(self, imageName):
        try:
            self.info( "---- IMAGE = %s ----" %(imageName))
            fa = open(imageName)
            file_size = os.stat(imageName).st_size
            self.info( "File size (bytes) %s" %file_size)
            self.fileheader = fa.read(104)
            self.info( "File-header size (bytes) %s" %(len(self.fileheader)))

            # Get FileId
            self.FileId = numpy.frombuffer(self.fileheader, count=1,dtype='|S20', offset=0)
            self.info( "File Header FileId = %s" %(self.FileId[0]))
            # Get file Header
            offset = 20
            num_of_addresses = 14
            self.shape = numpy.frombuffer(self.fileheader, count=2*num_of_addresses, dtype='ushort', offset=offset)
            for i in range(num_of_addresses):
                address = offset + 2*i
                description = ""
                if address == 20:
                    description = "Size"
                elif address == 22:
                    description = "Version"
                elif address == 24:
                    description = "BitPerPixel"
                elif address == 26:
                    description = "CameraBitsPerPixels"
                elif address == 28:
                    description = "MCPDiamerterInPixels"
                elif address == 40:
                    description = "ImageWidth"
                    self.width =  int(self.shape[i])
                elif address == 42:
                    description = "ImageHeight"
                    self.height =  int(self.shape[i])
                elif address == 44:
                    description = "NumberOfImages"
                elif address == 46:
                    description = "AttacchedReceipeSize"
                
                if description == "":
                    pass#self.info( "File Header Address %d = %d" %(address, int(self.shape[i])))
                else:
                    self.info( "%s = %d" %(description, int(self.shape[i])))

            # Get binning
            binning = numpy.frombuffer(self.fileheader, count=2,dtype='b', offset=30)
            self.info( "hBinning = %d" %(binning[0]))
            self.info( "vBinning = %d" %(binning[1]))


            # calculate the image header size for getting a perfect square
            header_size = file_size - 104 - self.width*self.height*2
            self.imageheader = fa.read(int(header_size))
            self.info( "FB image-header size (bytes) = %d"  %(len(self.imageheader)))

            # Read Image header
            offset = 0
            num_of_addresses = 272
            self.shape = numpy.frombuffer(self.imageheader, count=2*num_of_addresses, dtype='ushort', offset=offset)
            for i in range(num_of_addresses):
                address = offset + 2*i
                description = ""
                
                if description == "":
                    self.info( "File Header Address %d = %d" %(address, int(self.shape[i])))





            imagedata_a = fa.read()
            fa.close()


            
          
            
        except Exception,e:
            self.error(str(e))



        