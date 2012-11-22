from sardana.macroserver.macro import Macro, Type
import taurus
from datetime import *
from transmission import *
import os
import time
from testomega import *
import math
from cbfread import *

class collectnolima(Macro):
    ''' This macro is used to collect a diffraction dataset '''

    param_def = [ 
                  [ 'prefix', Type.String, None, 'Filename prefix'],
                  [ 'run', Type.Integer, None, 'Run number'],
                  [ 'ni', Type.Integer, None, 'Number of images'],
                  [ 'startangle', Type.Float, None, 'Oscillation start in degrees'],
                  [ 'angleincrement', Type.Float, None, 'Oscillation range in degrees'],
                  [ 'userexpt', Type.Float, None, 'Exposure time in seconds'],
                  [ 'startnum', Type.Integer, 1, 'Start file number'],
                  [ 'dir', Type.String, "/beamlines/bl13/commissioning/tmp/", 'Data directory'],
                  [ 'force', Type.String, 'NO', 'Force (yes/no) data collection with safety shutter /FE closed'],
                  [ 'pshu', Type.String, 'YES', 'Force (yes/no) safety shutter open'],
                  [ 'slowshu', Type.String, 'YES', 'Force (yes/no) slow shutter open/close'],
                  [ 'fe', Type.String, 'YES', 'Force (yes/no) fe open/close'],
                  [ 'setroi', Type.String, '0', 'ROI to be used: 0, C18, C2']
                ]

    def run(self, prefix, run, ni, startangle, angleincrement, userexpt, startnum,dir,force,pshu,slowshu,fe,setroi):
       # PRINT PARAMETERS
       self.info(' prefix %s\n run %d\n ni %d\n startangle %f \n angleincrement %f \n expt %f \n startnum %d \n dir %s \n force %s \n pshu %s \n slowshu %s  \n fe %s \n setroi %s' %(prefix,run,ni,startangle,angleincrement,userexpt,startnum,dir,force,pshu,slowshu,fe,setroi))



       # CHECK OMEGA
       #if testomega() != '1':
       #   self.error('ERROR: Omega is not OK')
       #   return
      


       # CHECK THAT THE VALUES MAKE SENSE
       if ni < 0: 
          self.error('ERROR: Error number of images cannot be < 0')
          return
       elif ni > 9999:
          self.error('ERROR: Number of images cannot be > 9999')
          return
       if angleincrement > 10:
          self.error('ERROR: Angle increment > 10')
          return
       if startnum < 1:
          self.error('ERROR: start number cannot be < 1')
          return
       if setroi == '0' and userexpt < 0.08:
          self.error('ERROR: Exposure time cannot be < 0.08 sec for ROI = 0')
          return
       if setroi == 'C18' and userexpt < 0.04:
          self.error('ERROR: Exposure time cannot be < 0.08 sec for ROI = C18')
          return
       totaltimeestimated = (userexpt*ni)/3600.
       if totaltimeestimated > 3: 
          self.error('ERROR: Total data collection time > 3 h')
          return
 
       # DEFINE DEVICES AND VARIABLES
       eps = taurus.Device('bl13/ct/eps-plc-01')
       var = taurus.Device('bl13/ct/variables')
       blight = self.getDevice('tango://blight')
       pilatusdet = taurus.Device('bl13/eh/pilatusspecific')
       slowshu = slowshu.upper()
       self.info('Devices defined')
       mbattrans = self.getMoveable("mbattrans")
       dettaby = self.getMoveable("dettaby")



       # CLOSE THE SLOW SHUTTER
       if slowshu == 'YES':
           try: 
              self.execMacro('act slowshu in')              
              self.info('Slow shutter closed')   
           except:
              self.error('ERROR: Cannot actuate the slowshu')
              return



       # MOVE BSTOP TO 0
       self.info('Moving bstopx')
       self.execMacro('turn bstopx on')
       self.execMacro('mv bstopx 0')
       self.info('Moving bstopz')
       self.execMacro('turn bstopz on')
       if not eps['ln2cover'].value == 1: 
          self.info('Removing LN2 cover...')
          self.execMacro('act ln2cover out')
          for trials in range(20):
             if eps['ln2cover'].value == 1:
                break
             time.sleep(.2)
       if not eps['ln2cover'].value == 1:
          self.error['ERROR: cannot actuate the LN2 cover']
       self.execMacro('mv bstopz 0')
      

 
       # CHECK BSTOP
       bstopx=self.getMoveable("bstopx")
       bstopz=self.getMoveable("bstopz")
       bstopx.pos = bstopx.getPosition()
       bstopz.pos = bstopz.getPosition()
       delta = math.fabs(bstopx.pos+0.0)
       if delta > 5E-2:
          self.error('ERROR: bstopx position is wrong') 
          return
       delta = math.fabs(bstopz.pos+0.0)
       if delta > 5E-2:
          self.error('ERROR: bstopz position is wrong')
          return
       self.info('bstop is in place')



       # REMOVE & TURN OFF BACKLIGHT
       self.info('Remove and turn off backlight')
       blight['Value'] = '0'
       if not eps['backlight'].value == 1: 
          self.execMacro('act backlight out')              
          for trials in range(50):
              if eps['backlight'].value == 1:
                 break
              time.sleep(0.2)
       
 

       # CHECK THAT THE BACKLIGHT IS OUT 
       self.info('Check that the backlight is out')
       if not eps['backlight'].value == 1:
          self.error('ERROR: The Backlight is still in')
          return



       # CHECK THAT THE BACKLIGHT IS OFF 
       if not blight['Value'].value == 0:
          self.warning('WARNING: The Backlight is still on')
          blight['Value'] = '0'
      


       # OPEN FE IF ASKED FOR
       fe = fe.upper()
       if fe == 'YES':
           try:
               if eps['fe_open'].value == False:
                   self.execMacro('fe open')              
                   self.info('Opening the FE')
                   for trials in range(50):
                       if eps['fe_open'].value == True:
                          break
                       time.sleep(0.2)
           except:
              self.error('ERROR: Cannot actuate the FE')
              return 
       elif fe == 'NO':
           self.info('Not actuating the FE')



       # OPEN PSHU IF ASKED FOR
       pshu = pshu.upper()
       if pshu == 'YES':
           try: 
               if eps['pshu'].value == 0:
                   self.info('Opening the safety shutter')
                   self.execMacro('act pshu open')              
                   time.sleep(10)
                   for trials in range(50):
                       if eps['pshu'].value == 1:
                          break
                       time.sleep(0.2)
           except:
              self.error('ERROR: Cannot actuate the safety shutter')
              return
       elif pshu == 'NO':
           self.info('Not actuating the safety shutter')



       # CHECK THAT THE SAFETY SHUTTER OR FE ARE OPEN
       force = force.upper()
       if force == 'YES':
          if eps['pshu'].value == 0:
              self.warning('WARNING: The safety shutter is closed')
          if eps['fe_open'].value == 0:
              self.warning('WARNING: The FE is closed')
       elif force == 'NO':
          if eps['pshu'].value == 0:
              self.error('ERROR: The safety shutter is closed')
              return
          if eps['fe_open'].value == 0:
              self.error('ERROR: The FE is closed')
              return
    

 
       # CHECK THAT THE DETECTOR DOES NOT GET THE DIRECT BEAM 
#       m = self.execMacro('testdet')
#       testdetvalue = m.getResult() 
#       self.info('The result of testing the detector is %s' %testdetvalue) 
#       if not testdetvalue == '1':
#          self.error('There is an error with the beamstop')
#          return


       
       # CREATE DIRECTORIES 
       datadir=dir+"/"+prefix+"/"
       if not os.path.exists(dir): 
          try: os.mkdir(dir)
          except: 
             self.error('ERROR: Could not create directory %s' % dir)
             return
       if not os.path.exists(datadir): 
          try: os.mkdir(datadir)
          except: 
             self.error('ERROR: Could not create directory %s' % datadir)
             return
       if not os.path.exists(datadir): 
          self.error('ERROR: The directory %s does not exist' % datadir)
          return



       # CHECK THE MBATS AND CALCULATE TRANSMISSION
       mbattrans = self.getMoveable("mbattrans")
       try: transmission = mbattrans.getPosition()/100. 
       except:
           self.error("ERROR: Could not read the mbat positions")
           return
       if transmission < 0.1: self.warning('WARNING: transmission below 0.1')



       # PREPARE THE VARIABLES NEEDED FOR THE DETECTOR
       self.info('Prepare variables')
       expp = userexpt 
       expt = userexpt - 0.0023
       wavelength = self.getMoveable("wavelength")
       try: sampledetdistance = var['detsamdis'].value/float(1000)
       except: 
           self.error("ERROR: Could not read the detector-to-sample distance")
           return
       try: beamx, beamy = var['beamx'].value, var['beamy'].value
       except: 
           self.error("ERROR: Could not read the beam center") 
           return
       kappa = self.getMoveable("kappa")
       phi = self.getMoveable("phi")



       # CREATE XDS.INP FILE
       self.info('Create XDS.INP & mosflm.dat files')
       self.execMacro('xdsinp %s %d %d %f %f %f %d %s' %(prefix,run,ni,startangle,angleincrement,expt,startnum,datadir))



       # SEND PARAMETERS TO LIMA
       limaprefix=prefix+"_"+str(run)+"_"
       limaexpt=expt 
       self.info('Data directory = %s' % datadir)

#       self.execMacro('lima_cfg_saving %s %s %s %s' %(datadir,limaprefix,'.cbf','CBF'))
#       self.execMacro('lima_cfg_acq %f %d %s' %(limaexpt,ni,'External_trigger'))
#       self.execMacro('lima_cfg_acq %f %d %s' %(limaexpt,ni,'INTERNAL_TRIGGER'))
#       pilatusdet['nb_first_image'] = startnum 

#       self.execMacro(['lima_saving','pilatus',datadir,limaprefix,'CBF',False])
#       self.execMacro(['lima_prepare','pilatus',ni,'EXTERNAL_TRIGGER',limaexpt])
#       self.execMacro(['pilatus_set_first_image','pilatus_custom',startnum])




       # SEND THE MXSETTINGS TO CAMSERVER
       pilatusdet.sendCamserverCmd('setroi %s' % setroi)
       pilatusdet.sendCamserverCmd('mxsettings Wavelength %s' % wavelength.getPosition())
       pilatusdet.sendCamserverCmd('mxsettings Detector_distance %s ' % sampledetdistance)
       pilatusdet.sendCamserverCmd('mxsettings Detector_Voffset 0')
       pilatusdet.sendCamserverCmd('mxsettings Beam_xy %s, %s' %(beamx,beamy))
       pilatusdet.sendCamserverCmd('mxsettings Filter_transmission %s' % transmission)
       pilatusdet.sendCamserverCmd('mxsettings Flux 2x10E12')
       pilatusdet.sendCamserverCmd('mxsettings Detector_2theta 0')
       pilatusdet.sendCamserverCmd('mxsettings Polarization 0.99')
       pilatusdet.sendCamserverCmd('mxsettings Alpha 0')
       pilatusdet.sendCamserverCmd('mxsettings Kappa %s' % kappa.getPosition())
       pilatusdet.sendCamserverCmd('mxsettings Phi %s' % phi.getPosition())
       pilatusdet.sendCamserverCmd('mxsettings Chi 0')
       pilatusdet.sendCamserverCmd('mxsettings Oscillation_axis X, CW')
       pilatusdet.sendCamserverCmd('mxsettings N_oscillations 1')
       pilatusdet.sendCamserverCmd('mxsettings Start_angle %s' % startangle)
       pilatusdet.sendCamserverCmd('mxsettings Angle_increment %s' % angleincrement)
       pilatusdet.sendCamserverCmd('mxsettings Detector_2theta 0.0000')
       pilatusdet.sendCamserverCmd('imgpath %s' % datadir)
       pilatusdet.sendCamserverCmd('ni %s' % ni)
       pilatusdet.sendCamserverCmd('expt %s' % expt)
       pilatusdet.sendCamserverCmd('expp %s' % expp)


       # CHECK THAT OMEGA IS FINE BEFORE DATA COLLECTION
       #if testomega() != '1': 
       #   self.error('ERROR: Omega is not OK')
       #   return



       # PREPARE OMEGA
       self.execMacro('turn omega on')
       self.execMacro('turn omegaenc on')
       self.info('define omega')
       omega = self.getMoveable("omega")
       initomegavelocity = omega.getVelocity()
       omegavelocity = float(angleincrement)/expp
       omegaaccelerationtime = omega.getAcceleration()
       omega.write_attribute('velocity',30)
       self.info('omega velocity = %s' % omegavelocity)
       omegaaccelerationtime = omegaaccelerationtime + 0.2
       safedelta = 3.0*omegavelocity*omegaaccelerationtime 
       initialpos = startangle - safedelta 
       try: 
           self.info('Moving omega to initial position %s' % initialpos)
           self.execMacro('mv omega %s' % initialpos) 
       except:
           self.error('ERROR: Cannot move omega')
           return




       # CHECK THAT OMEGA IS FINE
       #if testomega() != '1':
       #   self.error('ERROR: Omega is not OK')
       #   return



       # WAIT IF DETTABY IS MOVING
       self.info('Check if the detector is moving')
       limit = 1
       while dettaby.getAttribute('StatusMoving').read().value: 
          self.warning('WARNING: The detector is still moving')
          time.sleep(5.) 
          limit = limit + 1
          if limit > 60:
              self.error('ERROR: There is an error with the Y movement of the detector')
              return


 
       # OPEN SLOW SHUTTER 
       if slowshu == 'YES':
           try:  
              self.execMacro('act slowshu out')
           except:
               self.error('ERROR: Cannot actuate the slow shutter')
 
 
 
       # ANNOUNCE TOTAL TIME
       seconds = ni*expp + safedelta/omegavelocity
       minutes = seconds/60
       timenow = datetime.now()
       timefinish = datetime.now() + timedelta(seconds=seconds)
       self.info('This data collection was started at: %s and will take %s seconds or %s minutes' % (timenow,seconds,minutes))
       self.info('This data collection will finish at: %s' % timefinish)



       # PREPARE OMEGA FOR MOVEMENT 
       omega.write_attribute('velocity',omegavelocity)
       finalpos = startangle + ni*angleincrement + safedelta
       totalangleincrement = ni*angleincrement
       # PREPARE NI CARD
       self.info('startangle %s totalangleincrement %s' % (startangle,totalangleincrement))
       self.info('omegavelocity %s' %omegavelocity)
       self.execMacro('ni660x_configure_collect 0.0 %s %s 0 1' % (startangle,totalangleincrement))

       # START MOVING OMEGA
       try: 
          self.info('Started moving omega toward final position %f' % finalpos)
          self.omega = self.getDevice('omega')
          self.omega.getAttribute('position').write(finalpos)
       except:
          self.error('ERROR: Cannot move omega')
          return

       # START DATA COLLECTION 
       self.info('Start data collection')
       try: 
          padded = str(startnum).zfill(4)
          filename = prefix+"_"+str(run)+"_"+padded+".cbf"
          self.info('Filename %s' %filename)
          pilatusdet.sendCamserverCmd('exposure %s' % filename) 
          time.sleep(ni*expp)
#          self.execMacro('lima_start_acq')
#          self.execMacro(['lima_acquire','pilatus'])
#          while True:
#              limastatus_macro = self.execMacro('lima_status','pilatus')
#              state, acq = limastatus_macro.getResult().split()
#              time.sleep(1)
#              if acq != 'Running' :
#                 break
       except: 
           self.info('None')
#           self.execMacro('lima_stop_acq') 
#           self.execMacro(['lima_stop','pilatus'])
           omega.write_attribute('velocity',initomegavelocity)
           # CLOSE SLOW SHUTTER 
           if slowshu == 'YES':
              try:
                 self.execMacro('act slowshu in')
              except:
                 self.error('ERROR: Cannot actuate the slow shutter')
           return



       # CLOSE SLOW SHUTTER 
       if slowshu == 'YES':
           try: 
              self.execMacro('act slowshu in')
           except:
              self.error('ERROR: Cannot actuate the slow shutter')
              self.info('Closing the pshu')
              self.execMacro('act pshu in')



       # SET OMEGA VELOCITY TO THE INITIAL ONE
       time.sleep(5)
       omega.write_attribute('velocity',initomegavelocity)
       self.info('Data collection finished') 



       # UNCOFIGURE NI660
       self.execMacro('ni660x_unconfigure_collect')
       
       # MOVE OMEGA TO REAL FINAL POSITION
       realfinalpos = startangle + ni*angleincrement
       try: 
           self.info('Moving omega to %s' % realfinalpos)
           self.execMacro('mv omega %s' % realfinalpos) 
       except:
           self.error('ERROR: Cannot move omega')
           return



       # SET CURRENT IMAGE FOR ADXV
       #f=open('/beamlines/bl13/controls/adxv/adxv_current_frame',"w")
       #line=str(int(1000*time.clock()))+" "+datadir+prefix+"_"+str(run)+"_0001"+".cbf"
       #self.info(line)
       #f.writelines(line)
       #f.close()



       # ABORT DATA COLLECTION 
       self.info('Data collection finished')
    def on_abort(self): 
        eps = taurus.Device('bl13/ct/eps-plc-01')
        self.execMacro('act slowshu in')
        #lima_dev = taurus.Device('bl13/eh/pilatuslima')
        #lima_dev.stopAcq()

            

       

 




