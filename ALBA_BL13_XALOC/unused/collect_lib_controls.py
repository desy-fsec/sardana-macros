# 20150113, JA, GJ, DF, RB: reorganized macros
#         - moved old unused macros to obsolete directory within user_macros
#         - added collect_wrapper macro to start different exisiting (and future) collect macros
#         - added inverse collection to the collect macro lib
#         - moved old collect macro still in use in the crystaldifftest macro to that library (needs FIX!!)
# 2015014, RB: reduced waiting time opening pshu from 120 to 20 secs

# 20150121, JA: merge with collect_plate_lib_2014.py
#         - Define global variable bstop=YES and initialize the local value.
#         - Modify the logic related to the bstop and the LN2 cover:
#           between CLOSE THE FAST SHUTTER and REMOVE DETECTOR COVER
#         - Add protection OPEN SLOW SHUTTER at collect_config level
#         - Modify Bstop logic at collect_end function

# TODO: implement raise exception to abort macro and be catched in collect.py


# USAGE: for collect plate, ni has to be set to 1 (see collect config)


from sardana.macroserver.macro import Macro, Type
import taurus
import os
import time
from datetime import datetime, timedelta
import math
import getflux
from epsf import epsf



COLLECT_ENV = {'force':'NO',
               'pshu':'YES',
               'slowshu':'YES',
               'fe':'YES',
               'bstop': 'YES'}


class collect_prepare(Macro):
    '''Prepare the beamline to collect data'''

    param_def = [
        ]

    global COLLECT_ENV

    def run(self):

        # DEFINE DEVICES AND VARIABLES
        force = COLLECT_ENV['force']
        pshu = COLLECT_ENV['pshu']
        slowshu = COLLECT_ENV['slowshu']
        fe = COLLECT_ENV['fe']
        bstop = COLLECT_ENV['bstop']

        self.debug("FORCE %s, PSHU %s, SLOWSHU %s, FE %s" 
                   % (force, pshu, slowshu, fe))

#         force = force.upper()
#         pshu = pshu.upper()
#         slowshu = slowshu.upper()
#         fe = fe.upper()

#         COLLECT_ENV['force'] = force
#         COLLECT_ENV['pshu'] = pshu
#         COLLECT_ENV['slowshu'] = slowshu
#         COLLECT_ENV['fe'] = fe
        try:
            pilatus_dev = 'bl13/eh/pilatusspecific'
            pilatusdet = taurus.Device(pilatus_dev)
            pilatus_threshold = pilatusdet.getAttribute('energy_threshold')
        except:
            self.error("The DS of the %s Device is unavailable, start it" %(pilatus_dev))
            raise

        try:
            lima_dev = 'bl13/eh/pilatuslima'
            lima = taurus.Device(lima_dev)
            lima_acqstatus = lima.getAttribute('acq_status')
        except:
            self.error("The DS of the %s Device is unavailable, start it" %(pilatus_dev))
            raise


#         eugap = self.getMoveable("Eugap")
#         bstopx = self.getMoveable("bstopx")
#         bstopz = self.getMoveable("bstopz")
        eugap_m = taurus.Device('Eugap')
        bstopx_m = taurus.Device('bstopx')
        bstopz_m = taurus.Device('bstopz')

        eugap = eugap_m.getAttribute('Position')
        bstopx = bstopx_m.getAttribute('Position')
        bstopz = bstopz_m.getAttribute('Position')

        blight_ior = taurus.Device('blight')
        flight_ior = taurus.Device('flight')

        blight_on = blight_ior.getAttribute('Value')
        blight = blight_ior.getAttribute('Brightness')
        flight = flight_ior.getAttribute('Brightness')

        # Setup LIMA
        # check status of the lima server
        self.info('COLLECT: Checking that Lima is fine')
        try:
            state = lima.getAttribute('acq_status').read().value
            self.info('COLLECT: lima status is %s' % (state))
        except:
            self.warning('COLLECT WARNING: ' + 
                         'There is an error with the lima server')
            self.warning('COLLECT WARNING: Restarting the lima server')
            self.execMacro('restartDS ' + lima.getNormalName())
            time.sleep(5)
            try:
                state = lima_acqstatus.read().value
                self.info('COLLECT: lima status is %s' % (state))
            except:
                self.error('COLLECT ERROR: ' + 
                           'There is an error with the lima server')
                return
 
        # CHECK ENERGY VS ENERGY_THRESHOLD 
        setenergy = pilatus_threshold.read().value 
        threshold = setenergy / 2.
        limitenergy = threshold / 0.8 
        currentenergy = eugap.read().value
        energydiff = currentenergy - threshold
        self.info('COLLECT: X-ray energy is: %s keV' 
                  % round(currentenergy, 6))
        self.info('COLLECT: Detector X-ray set energy is: %s keV' 
                  % round(setenergy, 6))
        self.info('COLLECT: Detector threshold X-ray energy is: %s keV' 
                  % round(threshold, 6))
        kev_diff = math.fabs(setenergy - currentenergy)
        self.info('COLLECT: Detector X-ray set energy - current energy: %s keV' 
                  % round(kev_diff, 4))
        if round(currentenergy, 6) < 7.538: 
            currentenergy = 7.538
        kev_diff = math.fabs(setenergy - currentenergy)
        if kev_diff > 1.2: 
            pilatus_threshold.write(currentenergy)
#             energy_in_ev = currentenergy * 1000.
#             camserver_text = str(energy_in_ev)
            self.warning('COLLECT WARNING: Waiting 120 s for the Pilatus ' + 
                         'to set the right threshold')
#             pilatusdet.sendCamserverCmd('setenergy %s' % camserver_text)
            time.sleep(120)
            self.warning('COLLECT WARNING: Done waiting for the Pilatus ' + 
                         'to set the right threshold')
            setenergy = pilatus_threshold.read().value
            self.info('COLLECT: Detector X-ray new set energy is: %s keV'
                      % round(setenergy, 6))
        #  these messages should appear less often now 
        if currentenergy <= threshold and force == 'NO':
            self.error('COLLECT ERROR: Current X-ray energy is lower ' + 
                       'than the energy threshold of the detector')
            return
        elif energydiff <= 1 and force == 'NO':
            self.error('COLLECT ERROR: Current X-ray energy is less ' + 
                       'than 1keV from the energy threshold of the detector')
            return
        elif currentenergy <= limitenergy:
            self.warning('COLLECT WARNING: ' + 
                         'The energy threshold of the detector ' + 
                         'is > 80% of the current X-ray energy')
        elif currentenergy >= threshold * 2.0: 
            self.warning('COLLECT WARNING: The energy threshold ' + 
                         'is below 50 % of the current energy')

        # CLOSE THE SLOW SHUTTER
        if slowshu == 'YES':
            try: 
                if epsf('read', 'slowshu')[2] != 0:
                    self.execMacro('act slowshu in')              
                    self.info('COLLECT: Slow shutter closed')   
            except:
                self.error('COLLECT ERROR: Cannot actuate the slowshu')
                return
            
        # CLOSE THE FAST SHUTTER
        self.info('COLLECT: Fast shutter closed')   
        try:
            self.execMacro('ni660x_shutter_open_close close')
        except:
            self.error('COLLECT ERROR: Cannot actuate the fast shutter')
            return

        # OPERATE WITHOUT BEAMSTOP
        if bstop == 'NO':

            # LN2 COVER SHOULD BE IN
            self.info('COLLECT: Check the LN2 cover')
            if epsf('read', 'ln2cover')[2] != 0:
                self.info('COLLECT_PLATE: The LN2 cover should be in!!')
                return

        # OPERATE WITH BEAMSTOP
        elif bstop == 'YES':
    
            # REMOVE LN2 COVER 
            self.info('COLLECT: Remove the LN2 cover')
            if epsf('read', 'ln2cover')[2] != 1:
                self.execMacro('act ln2cover out')
            limit = 1
            while epsf('read', 'ln2cover')[2] != 1: 
    #or eps['ln2cover'].quality != PyTango._PyTango.AttrQuality.ATTR_VALID:
                self.info("COLLECT WARNING: " + 
                          "waiting for the LN2 cover to be removed")
                limit = limit + 1
                if limit > 5:
                    self.error("COLLECT ERROR: " + 
                               "There is an error with the LN2 cover")
                    return
                self.checkPoint()
                time.sleep(2)

            # MOVE BSTOP TO 0
            self.info('COLLECT: Moving bstopx')
            bstopx_m['PowerOn'] = True
            self.mv(bstopx_m, 0)
    #         self.execMacro('turn bstopx on')
    #         self.execMacro('mv bstopx 0')
            self.info('COLLECT: Moving bstopz')
    #         self.execMacro('turn bstopz on')
            if epsf('read', 'ln2cover')[2] != 1: 
                self.info('COLLECT: Removing LN2 cover')
                self.execMacro('act ln2cover out')
                for trials in range(20):
                    if epsf('read', 'ln2cover')[2] == 1:
                        break
                    time.sleep(.2)
            if epsf('read', 'ln2cover')[2] != 1:
                self.error['COLLECT ERROR: cannot actuate the LN2 cover']
                return
    #         self.execMacro('mv bstopz 0')
            bstopz_m['PowerOn'] = True
            self.mv(bstopz_m, 0)
      

        # OPERATE WITHOUT BEAMSTOP
        if bstop == 'NO':

            # CHECK BSTOP
            delta = math.fabs(bstopx.read().value + 0.0)
            #if delta > 1E-2:
            #    self.error('COLLECT ERROR: bstopx position is wrong, should be smaller than 0.01') 
            #    return
            #delta = math.fabs(bstopz.read().value + 0.0)
            if delta < 95.7:
                self.error('COLLECT ERROR: bstopz position is wrong, should be smaller than -95.7')
                return
            self.info('COLLECT: bstop is not in')


        # OPERATE WITH BEAMSTOP
        if bstop == 'YES':

            # CHECK BSTOP
            delta = math.fabs(bstopx.read().value + 0.0)
            if delta > 5E-2:
                self.error('COLLECT ERROR: bstopx position is wrong') 
                return
            #delta = math.fabs(bstopz.read().value + 0.0)
            #if delta > 5E-2:
            #    self.error('COLLECT ERROR: bstopz position is wrong')
            #    return
            self.info('COLLECT: bstop is in place')


        # REMOVE THE DETECTOR COVER 
        if force == 'NO':
            self.info('COLLECT: Remove the detector cover')
            if epsf('read', 'detcover')[2] != 1: 
                self.execMacro('act detcover out')              

        # TURN OFF BACKLIGHT and FRONTLIGHT
        self.info('COLLECT: Remove and turn off backlight')
        blight_on.write(0)
        blight.write(1)
        flight.write(1)
        time.sleep(2)

        # SET BACKLIGHT IS OUT
        if epsf('read', 'backlight')[2] != 1: 
            self.execMacro('act backlight out')              
            for trials in range(50):
                if epsf('read', 'backlight')[2] == 1:
                    break
                time.sleep(0.2)

        # CHECK THAT THE BACKLIGHT IS OUT 
        self.info('COLLECT: Check that the backlight is out')
        if not epsf('read', 'backlight')[2] == 1:
            self.error('COLLECT ERROR: The Backlight is still in')
            return

        # CHECK THAT THE BACKLIGHT IS OFF 
        self.info('COLLECT: Check that the backlight is off')
        if not blight.read().value == 1:
            self.warning('COLLECT WARNING: The Backlight is still on')
            blight.write(0)

        # CHECK THAT THE FRONTLIGHT IS OFF 
        self.info('COLLECT: Check that the frontlight is off')
        if not flight.read().value == 1:
            self.warning('COLLECT WARNING: The Frontlight is still on')
            flight.write(1)

        # OPEN FE IF ASKED FOR
        if fe == 'YES':
            self.info('COLLECT: Open the FE')
            try:
                if epsf('read', 'fe_open')[2] is False:
                    self.execMacro('fe open')              
                    self.info('COLLECT: Opening the FE')
                    for trials in range(50):
                        if epsf('read', 'fe_open')[2] is True:
                            break
                        time.sleep(0.2)
            except:
                self.error('COLLECT ERROR: Cannot actuate the FE')
                return 
        elif fe == 'NO':
            self.info('COLLECT: Not actuating the FE')

        # OPEN PSHU IF ASKED FOR
        if pshu == 'YES':
            self.info('COLLECT: Open the PSHU')
            try: 
                if epsf('read', 'pshu')[2] != 1:
                    self.info('COLLECT: Opening the safety shutter')
                    self.execMacro('act pshu open')              
                    #time.sleep(10)
                    for trials in range(10):
                        if epsf('read', 'pshu')[2] == 1:
                            break
                        time.sleep(1)
            except:
                self.error('COLLECT ERROR: Cannot actuate the safety shutter')
                return
        elif pshu == 'NO':
            self.info('COLLECT: Not actuating the safety shutter')

        # CHECK THAT THE SAFETY SHUTTER OR FE ARE OPEN
        if epsf('read', 'pshu')[2] == 0:
            if pshu == 'YES' and force == 'NO':
                self.error('COLLECT ERROR: The safety shutter is closed')
                return
            else:
                self.warning('COLLECT WARNING: The safety shutter is closed')
        if epsf('read', 'fe_open')[2] is False:
            if fe == 'YES' and force == 'NO':
                self.error('COLLECT ERROR: The FE is closed')
                return
            else:
                self.warning('COLLECT WARNING: The FE is closed')
    
        # CHECK THAT THE DETECTOR COVER IS OUT
        if force == 'NO':
            self.info('COLLECT: removing detector cover')
            for trials in range(50):
                if epsf('read', 'detcover')[2] == 1:
                    break
                time.sleep(1.0)
                self.warning('COLLECT WARNING: ' +
                             'waiting for the detector to be OUT')
            if epsf('read', 'detcover')[2] == 0:
                self.error('COLLECT ERROR: the detector cover is still in')
                return
 
# CHECK THAT THE DETECTOR DOES NOT GET THE DIRECT BEAM 
#       m = self.execMacro('testdet')
#       testdetvalue = m.getResult() 
#       self.info('The result of testing the detector is %s' %testdetvalue) 
#       if not testdetvalue == '1':
#          self.error('There is an error with the beamstop')
#          return


class collect_saving(Macro):
    ''' '''

    param_def = [ 
        ['dir', Type.String, "/beamlines/bl13/commissioning/tmp/", 
         'Data directory'],
        ['prefix', Type.String, None, 'Filename prefix'],
        ['run', Type.Integer, None, 'Run number'],
        ]

    global COLLECT_ENV

    def run(self, dir, prefix, run):
        # CREATE DIRECTORIES 
        datadir = dir + "/" + prefix + "/"
        if not os.path.exists(dir): 
            try: 
                os.makedirs(dir)
            except: 
                self.error('COLLECT ERROR: Could not create directory %s' 
                           % dir)
                return
        COLLECT_ENV['dir'] = dir

        if not os.path.exists(datadir): 
            try: 
                os.makedirs(datadir)
            except: 
                self.error('COLLECT ERROR: Could not create directory %s' 
                           % datadir)
                return

        if not os.path.exists(datadir): 
            self.error('COLLECT ERROR: The directory %s does not exist' 
                       % datadir)
            return
        COLLECT_ENV['datadir'] = datadir
        
        # SEND PARAMETERS TO LIMA
        limaprefix = prefix + "_" + str(run) + "_"
        COLLECT_ENV['prefix'] = prefix
        COLLECT_ENV['limaprefix'] = limaprefix
        COLLECT_ENV['run'] = run

        self.info('COLLECT: Data directory = %s' % datadir)
 
        self.info('COLLECT: lima_saving %s %s' % (datadir, limaprefix))
        try: 
            self.execMacro(['lima_saving', 'pilatus',
                            datadir, limaprefix, 'CBF', False])
        except:
            self.error('COLLECT ERROR: Error with lima_saving')
            return

        #TODO: self.info explicant el image name template agafant info de lima

        
class collect_config(Macro):
    ''' '''

#### Prefix Run Start_angle Num_images Angle_increment Exposure_time
#### Start_number (del fitxer) Directory Set_ROI (del detector)

#### Motor omegax Motor omegay Motor omegaz Motor centx Motor centy
#### Motor kappa Motor phi Motor mbattrans Motor Ealign Motor detsamdis

    param_def = [ 
        ['startangle', Type.Float, None, 'Oscillation start in degrees'],
        ['angleincrement', Type.Float, None, 'Oscillation range in degrees'],
        ['ni', Type.Integer, None, 'Number of images'],
        ['userexpt', Type.Float, None, 'Exposure time in seconds'],
        ['startnum', Type.Integer, 1, 'Start file number'],
        ['setroi', Type.String, '0', 'ROI to be used: 0, C18, C2']
        ]

    global COLLECT_ENV

    def run(self, startangle, angleincrement, ni, userexpt, startnum, setroi):

        # CHECK INPUT VALUES
        if userexpt <= 0:
            self.error('COLLECT ERROR: Exposure time cannot be <= 0')
        
        if setroi == '0' and userexpt < 0.08:
            self.error('COLLECT ERROR: ' + 
                       'Exposure time cannot be < 0.08 sec for ROI = 0')
            return
        if setroi == 'C18' and userexpt < 0.04:
            self.error('COLLECT ERROR: ' + 
                       'Exposure time cannot be < 0.08 sec for ROI = C18')
            return

        bstop = COLLECT_ENV['bstop']

        if bstop == 'NO' and ni != 1:
            self.error('COLLECT ERROR:' +
                       'Number of images MUST BE 1 for btop = NO')

        # DEFINE DEVICES AND VARIABLES
        try:
            var_dev = 'bl13/ct/variables'
            var = taurus.Device(var_dev)
            var_state = var.state()
        except:
            self.error("The DS of the %s Device is unavailable, start it" %(var_dev))
            raise
#         dettabx = self.getMoveable("dettabx")
#         dettaby = self.getMoveable("dettaby")
#         dettabzf = self.getMoveable("dettabzf")
#         dettabzb = self.getMoveable("dettabzb")

        kappa = self.getMoveable("kappa")
        phi = self.getMoveable("phi")
 
        mbattrans = self.getMoveable("mbattrans")
        wavelength = self.getMoveable("wavelength")

        try:
            pilatus_dev = 'bl13/eh/pilatusspecific'
            pilatusdet = taurus.Device(pilatus_dev)
            pilatus_state = pilatusdet.state()
        except:
            self.error("The DS of the %s Device is unavailable, start it" %(pilatus_dev))
            raise

 
        # CHECK THE MBATS AND CALCULATE TRANSMISSION
        try: 
            transmission = mbattrans.getPosition() / 100. 
        except:
            self.error("COLLECT ERROR: Could not read the mbat positions")
            return

        if transmission < 0.001: 
            self.warning('COLLECT WARNING: transmission below 0.1 %')
  
#         # WAIT IF DETTABY IS MOVING
#         self.info('COLLECT: Check if the detector is moving')
#         limit = 1
#         while (dettabx.getAttribute('StatusMoving').read().value 
#                or dettaby.getAttribute('StatusMoving').read().value 
#                or dettabzf.getAttribute('StatusMoving').read().value 
#                or dettabzb.getAttribute('StatusMoving').read().value):
#             self.warning('COLLECT WARNING: The detector is still moving')
#             if limit > 60:
#                 self.error('COLLECT ERROR: ' +
#                            'There is an error with the Y movement ' + 
#                            'of the detector')
#                 return
#             limit = limit + 1
#             time.sleep(5.)
  
        # PREPARE THE VARIABLES NEEDED FOR THE DETECTOR
        self.info('COLLECT: Prepare variables')
        readouttime = 0.0023
# MULTI TRIGGER TEST
#        readouttime = 0.004

        expt = userexpt - readouttime 
        limaexpt = expt 
        COLLECT_ENV['userexpt'] = userexpt

        try: 
            sampledetdistance = var['detsamdis'].value / float(1000)
        except: 
            self.error("COLLECT ERROR: " + 
                       "Could not read the detector-to-sample distance")
            return
        try: 
            beamx, beamy = var['beamx'].value, var['beamy'].value
        except: 
            self.error("COLLECT ERROR: Could not read the beam center") 
            return

        self.info('COLLECT: lima_prepare')
        try: 
            self.info('COLLECT: angleincrement %f' % angleincrement)
            if angleincrement != 0: 
                self.info('COLLECT: lima prepare external trigger')
                trigger = 'EXTERNAL_TRIGGER'
# MULTI TRIGGER TEST
#                trigger = 'EXTERNAL_TRIGGER_MULTI'
            else: 
                self.info('COLLECT: lima prepare internal trigger')
                trigger = 'INTERNAL_TRIGGER'

            self.info('COLLECT: limaexpt %f' % limaexpt)
            self.info('COLLECT: n images %d' % ni)
            self.execMacro(['lima_prepare', 'pilatus',
                            limaexpt, readouttime, ni, trigger])
        except: 
            self.error('COLLECT ERROR: Error with lima_prepare')
            return

        self.info('COLLECT: pilatus_set_first_image')
        try: 
            self.execMacro(['pilatus_set_first_image',
                            'pilatus_custom', startnum])
        except: 
            self.error('COLLECT ERROR: Error with pilatus_set_first_image')
            return

        COLLECT_ENV['limaexpt'] = limaexpt
        COLLECT_ENV['readouttime'] = readouttime
        COLLECT_ENV['ni'] = ni
        COLLECT_ENV['trigger'] = trigger
        COLLECT_ENV['startnum'] = startnum
 
        #
        # Make sure we have a proper reading of the flux, set default if not
        #
        if var['fluxlast'].value < 1E7:
            flux = 1E12 
        else:
            flux = getflux.lastcurrenttrans()

        # SEND THE MXSETTINGS TO CAMSERVER
        #pilatusdet.sendCamserverCmd('exptime %s' % limaexpt)
        #pilatusdet.sendCamserverCmd('expperiod %s' % userexpt)
        pilatusdet.sendCamserverCmd('setroi %s' % setroi)
        pilatusdet.sendCamserverCmd('mxsettings Wavelength %s' % wavelength.getPosition())
        pilatusdet.sendCamserverCmd('mxsettings Detector_distance %s ' % sampledetdistance)
        pilatusdet.sendCamserverCmd('mxsettings Detector_Voffset 0')
        pilatusdet.sendCamserverCmd('mxsettings Beam_xy %s, %s' %(beamx,beamy))
        pilatusdet.sendCamserverCmd('mxsettings Filter_transmission %s' % transmission)
        #pilatusdet.sendCamserverCmd('mxsettings Flux 2x10E12')
        pilatusdet.sendCamserverCmd('mxsettings Flux %.4g' % flux) 
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

        COLLECT_ENV['setroi'] = setroi
        COLLECT_ENV['wavelength'] = wavelength.getPosition()
        COLLECT_ENV['sampledetdistance'] = sampledetdistance
        COLLECT_ENV['beamx'] = beamx
        COLLECT_ENV['beamy'] = beamy
        COLLECT_ENV['transmission'] = transmission
        COLLECT_ENV['flux'] = flux
        COLLECT_ENV['kappa'] = kappa.getPosition()
        COLLECT_ENV['phi'] =  phi.getPosition()
        COLLECT_ENV['startangle'] = startangle
        COLLECT_ENV['angleincrement'] = angleincrement

        # CHECK THAT OMEGA IS FINE BEFORE DATA COLLECTION
        #if testomega() != '1': 
        #   self.error('ERROR: Omega is not OK')
        #   return
 
        # PREPARE OMEGA
        # on 20130507 omegai/motor27 acceleration was 0.05957 for velocity 1 deg/s 
        # on 20130507 omegai/motor27 acceleration was 0.2 for velocity 50 deg/s (icepapcms) 
        self.execMacro('turn omega on')
        self.execMacro('turn omegaenc on')

        self.info('COLLECT: define omega')
        omega = self.getMoveable("omega")
        initomegavelocity = omega.read_attribute('Velocity').value
        omegavelocity = float(angleincrement) / userexpt
        omegaaccelerationtime = omega.read_attribute('Acceleration').value
        omega.write_attribute('velocity', 60)

        self.info('COLLECT: omega velocity = %s' % omegavelocity)
        omegaaccelerationtime = omegaaccelerationtime + 0.2
        safedelta = 3.0 * omegavelocity * omegaaccelerationtime 
        initialpos = startangle - safedelta 
        realfinalpos = startangle + ni*angleincrement

        COLLECT_ENV['initomegavelocity'] = initomegavelocity
        COLLECT_ENV['omegavelocity'] = omegavelocity
        COLLECT_ENV['initialpos'] = initialpos
        COLLECT_ENV['realfinalpos'] = realfinalpos
        COLLECT_ENV['safedelta'] = safedelta

        try: 
            self.info('COLLECT: Moving omega to initial position %s' % initialpos)
            self.execMacro('mv omega %s' % initialpos) 
        except:
            self.error('COLLECT ERROR: Cannot move omega')
            return
 
        # CHECK THAT OMEGA IS FINE
        #if testomega() != '1':
        #   self.error('ERROR: Omega is not OK')
        #   return
 
#         # WAIT IF DETTABY IS MOVING
#         self.info('COLLECT: Check if the detector is moving')
#         limit = 1
#         while dettabx.getAttribute('StatusMoving').read().value or dettaby.getAttribute('StatusMoving').read().value or dettabzf.getAttribute('StatusMoving').read().value or dettabzb.getAttribute('StatusMoving').read().value: 
#            self.warning('COLLECT WARNING: The detector is still moving')
#            if limit > 60:
#                self.error('COLLECT ERROR: There is an error with the Y movement of the detector')
#                return
#            limit = limit + 1
#            time.sleep(5.) 
  
        # WAIT IF OMEGA IS MOVING
        self.info('COLLECT: Wait for omega to stop')
        while omega.read_attribute("StatusMoving").value:
            self.checkPoint()
            time.sleep(0.2)

        # PREPARE OMEGA FOR MOVEMENT 
        if omegavelocity != 0:
            omega.write_attribute('velocity', omegavelocity)
            duration = ni * userexpt + safedelta / omegavelocity
        else:
            duration = ni * userexpt
        finalpos = startangle + ni * angleincrement + safedelta
        totalangleincrement = ni * angleincrement

        COLLECT_ENV['duration'] = duration
        COLLECT_ENV['finalpos'] = finalpos
        COLLECT_ENV['totalangleincrement'] = totalangleincrement

        # PREPARE NI CARD
        if omegavelocity != 0:
            self.info('COLLECT: startangle %s totalangleincrement %s' 
                      % (startangle, totalangleincrement))
            self.info('COLLECT: omegavelocity %s' % omegavelocity)
            self.execMacro('ni660x_configure_collect 0.0 %s %s 0 1' 
                           % (startangle, totalangleincrement))
# MULTI TRIGGER TEST
#            self.execMacro('ni660x_configure_collect 0.0 %f %f %f %d' 
#                           % (startangle, angleincrement/2., 
#                              angleincrement/2., ni))

        # OPEN SLOW SHUTTER 
        self.info('COLLECT: Open the slowshu')
        if COLLECT_ENV['slowshu'] == 'YES':
            try:  
                if epsf('read', 'slowshu')[2] != 1:

### added
#                    self.execMacro('act slowshu out')
                    eps=taurus.Device('bl13/ct/eps-plc-01')
                    limit = 1
                    limit_trials=50
                    while limit < limit_trials:
                        try:
                            if eps['slowshu'].value != 1:
                                eps['slowshu'] = 1
                            elif eps['slowshu'].value == 1:
                                self.warning('ACT WARNING: slowshu is already open')
                            # IF THE PREVIOUS COMMAND WORKED, BREAK THE WHILE LOOP
                            break
                        except: 
                            self.warning('ACT WARNING: slowshu cannot be opened the %s time' % (limit))
                        time.sleep(0.1)
                        limit = limit + 1
###
            except:
                self.error('COLLECT ERROR: Cannot actuate the slow shutter')


        # TEMPLATE TO CREATE XDS.INP FILE IN THE STRATEGY
        #prefix = COLLECT_ENV['prefix']
        #run = COLLECT_ENV['run']
        #datadir = COLLECT_ENV['datadir']
        #self.info('COLLECT: Create XDS.INP & mosflm.dat files')
        #self.execMacro('xdsinp %s %d %d %f %f %f %d %s' 
        #               % (prefix, run, ni, startangle, angleincrement, 
        #                  limaexpt, startnum, datadir))
        #self.info('COLLECT: done Create XDS.INP & mosflm.dat files')

            
class collect_acquire(Macro):
    ''' '''

    param_def = [ 
        ]

    global COLLECT_ENV

    def run(self,):
        omega = self.getMoveable("omega")

        # CHECK THAT THE SLOWSHU IS OUT
        if COLLECT_ENV['slowshu'] == 'YES':
            if COLLECT_ENV['limaexpt'] < 0.5: 
                limit = 1
                while epsf('read','slowshu')[2] == 0:
                    self.warning('COLLECT WARNING: The slowshu is still closed')
                    if limit > 20:
                        self.error('COLLECT ERROR: There is an error with the slowshu')
                        return
                    limit = limit + 1
                    self.checkPoint()
                    time.sleep(1.)

        # ANNOUNCE TOTAL TIME
        omegavelocity = COLLECT_ENV['omegavelocity']
        if omegavelocity != 0: 
            seconds = COLLECT_ENV['duration']
        elif omegavelocity == 0: 
            seconds = 0.0
        minutes = seconds/60
        timenow = datetime.now()
        timefinish = datetime.now() + timedelta(seconds=seconds)
        self.info('COLLECT: This data collection was started at: %s' % timenow)
        self.info('COLLECT: This data collection will take %s seconds or %s minutes'
                  % (seconds, minutes))
        self.info('COLLECT: This data collection will finish at: %s' 
                  % timefinish)
 
        # START MOVING OMEGA
        try: 
           self.info('COLLECT: Started moving omega toward final position %f' 
                     % COLLECT_ENV['finalpos'])
           omega.write_attribute('position', COLLECT_ENV['finalpos'])
        except:
           self.error('COLLECT ERROR: Cannot move omega')
           return
 
        # START DATA COLLECTION 
        self.info('COLLECT: Start data collection')
        try: 
 #          self.execMacro('lima_start_acq')
           if omegavelocity == 0: 
               self.execMacro(['ni660x_shutter_open_close','open'])
           self.execMacro(['lima_acquire','pilatus'])
           ni = COLLECT_ENV['ni']
           while True:
               limastatus_macro = self.execMacro('lima_status','pilatus')
               state, acq = limastatus_macro.getResult().split()
###              TODO: fix implementation of last image ready in the plugin
###                    to know the acquisition progress
#                m = self.execMacro('lima_lastimage','pilatus')
#                lastimagenumber = m.getResult() + 1. 
#                yield 100*lastimagenumber/float(ni)
               self.checkPoint()
               time.sleep(1)
               #self.info("Acquiring")
               if acq != 'Running':
                   break
        except: 
 #           self.execMacro('lima_stop_acq') 
            self.error('COLLECT ERROR: acquisition failed')
            self.execMacro(['lima_stop','pilatus'])
            if omegavelocity == 0: self.execMacro(['ni660x_shutter_open_close','close'])
            omega.stop()
            time.sleep(3)
            omega.write_attribute('velocity', COLLECT_ENV['initomegavelocity'])

        # UNCOFIGURE NI660
        self.execMacro('ni660x_unconfigure_collect')
        

class collect_end(Macro):
    ''' '''

    param_def = [ 
        ]

    global COLLECT_ENV

    def run(self):

        force = COLLECT_ENV['force']
        pshu = COLLECT_ENV['pshu']
        slowshu = COLLECT_ENV['slowshu']
        fe = COLLECT_ENV['fe']
        bstop = COLLECT_ENV['bstop']

        bstopz_m = taurus.Device('bstopz')
        bstopz = bstopz_m.getAttribute('Position')

        # CLOSE FAST SHUTTER IN STILL MODE
        self.info('COLLECT: close fast shutter')
#        if omegavelocity == 0: 
        self.execMacro(['ni660x_shutter_open_close','close'])

        # SET OMEGA VELOCITY TO THE INITIAL ONE
        omega = self.getMoveable("omega")
        while omega.read_attribute('StatusMoving').value:
            self.warning('COLLECT: Omega still moving')
            self.checkPoint()
            time.sleep(1)
        try:
            omega.write_attribute('velocity', COLLECT_ENV['initomegavelocity'])
        except:
            self.warning('COLLECT WARNING: Could not set final omega velocity')
        self.info('COLLECT: Data collection finished') 

        # MOVE OMEGA TO REAL FINAL POSITION
        try: 
            self.info('COLLECT: Moving omega to %s' 
                      % COLLECT_ENV['realfinalpos'])
            self.execMacro('mv omega %s' 
                           % COLLECT_ENV['realfinalpos']) 
        except:
            self.warning('COLLECT WARNING: Cannot move omega to final position')

        # CLOSE DETECTOR COVER
        self.info('COLLECT: close detector cover')
        if epsf('read', 'detcover')[2] == 1: 
            self.execMacro('act detcover in')              

        # CLOSE SLOW SHUTTER 
        if slowshu == 'YES':
            self.info('COLLECT: Close the slow shutter')
            try: 
               if epsf('read','slowshu')[2] != 0:
                  self.execMacro('act slowshu in')
            except:
               self.error('COLLECT ERROR: Cannot actuate the slow shutter')
               self.info('COLLECT: Closing the pshu')
               if epsf('read','pshu')[2] != 0:
                  self.execMacro('act pshu in')
        elif slowshu == 'NO':
            self.info('COLLECT: Not actuating the slow shutter')
 
        # CLOSE PSHU IF ASKED FOR
        if pshu == 'YES':
            self.info('COLLECT: Close the safety shutter')
            try: 
                if epsf('read', 'pshu')[2] == 1:
                    self.info('COLLECT: Closing the safety shutter')
                    self.execMacro('act pshu close')              
                    #time.sleep(10)
                    for trials in range(120):
                        if epsf('read', 'pshu')[2] != 1:
                            break
                        time.sleep(1)
            except:
                self.error('COLLECT ERROR: Cannot actuate the safety shutter')
                return
        elif pshu == 'NO':
            self.info('COLLECT: Not actuating the safety shutter')

        # CLOSE FE IF ASKED FOR
#         if fe == 'YES':
#             self.info('COLLECT: Close the FE')
#             try:
#                 if epsf('read', 'fe_open')[2] is True:
#                     self.execMacro('fe close')              
#                     self.info('COLLECT: Closing the FE')
#                     for trials in range(50):
#                         if epsf('read', 'fe_open')[2] is False:
#                             break
#                         time.sleep(0.2)
#             except:
#                 self.error('COLLECT ERROR: Cannot actuate the FE')
#                 return 
#         elif fe == 'NO':
#             self.info('COLLECT: Not actuating the FE')

        if bstop == 'YES':

            # CLOSE BSTOP
            if epsf('read', 'ln2cover')[2] == 1:
                self.info('COLLECT: Moving bstopz')
                bstopz_m['PowerOn'] = True
                self.mv(bstopz_m,-96)
                #TODO: we should close the LN2 cover.
        self.info('COLLECT: End of data collection')


class collect_check(Macro):  
    ''' '''

    param_def = [ 
        ['param', Type.String, None, 'parameter to be checked'],
        ]

    global COLLECT_ENV

    def run(self, param):
        
        # if param == 'pilatus_ready':
        #     lima = taurus.Device('bl13/eh/pilatuslima')
        #     status = lima.getAttribute('acq_status').read().value
        #     return status == 'Ready'
        # elif param == 'pilatus_threshold':
        #     pilatus = taurus.Device('bl13/eh/pilatusspecific')
        #     eugap = taurus.Device('Eugap')
        #     setenergy = pilatus_threshold.read().value
        #     currentenergy = eugap.getAttribute('Position').read().value
        pass


class collect_env_get(Macro):  
    ''' '''

    param_def = [ 
        ['param', Type.String, None, 'parameter to get'],
        ]

    result_def = [ [ 'value', Type.String, None, 'parameter value']
                ]

    global COLLECT_ENV

    def run(self, param):
        value = None
        if COLLECT_ENV.has_key(param):
            value = str(COLLECT_ENV[param])
            #self.info("%s = %s" % (param, value))
        else:
            self.info("Parameter %s does not exist." % param)

        return value


class collect_env_set(Macro):  
    ''' '''

    param_def = [ 
        ['param', Type.String, None, 'parameter to set'],
        ['value', Type.String, None, 'value to set'],
        ]

    global COLLECT_ENV

    def run(self, param, value):
        if COLLECT_ENV.has_key(param):
            # Try con convert to integer or float if not keep the string
            try:
                v = int(value)
            except:
                try: 
                    v = float(value)
                except:
                    v = value.upper()
            COLLECT_ENV[param] = v
            self.info("%s = %s" % (param, str(COLLECT_ENV[param])))
        else:
            self.info("Parameter %s does not exist." % param)


class collect_env_print(Macro):  
    ''' '''

    param_def = [ 
        ]

    global COLLECT_ENV

    def run(self):
        for param in COLLECT_ENV.keys():
            self.info("%s = %s" % (param, str(COLLECT_ENV[param])))


