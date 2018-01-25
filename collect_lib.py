# 20150113, JA, GJ, DF, RB: reorganized macros
#         - moved old unused macros to obsolete directory within user_macros
#         - added collect_wrapper macro to start different exisiting (and future) collect macros
#         - added inverse collection to the collect macro lib
#         - moved old collect macro still in use in the crystaldifftest macro to that library (needs FIX!!)
# 2015014, RB: reduced waiting time opening pshu from 120 to 20 secs
# 20150604, RB: added additional parameter ('addfix') to collect_saving to allow hemisphere addition
# 20160530: RB: removed non 'mode' collection functions.
# 20160826: RB: substantially reworked collect_prepare to parallelize operations. renamed old macro to collect_prepare_serial
#       - added prepdiff_for_diffraction and checkdiff_for_diffraction to diffractometer package
#       - added prepshutters_for_diffraction and checkshutters_for_diffraction in shutters package
#       - added prepdetector_for_diffraction and checkdetector_for_diffraction in shutters package (not yet implemented in macro)

from sardana.macroserver.macro import Macro, Type
import taurus
import os
import shutil
import bl13constants
import bl13check
import sample
import time
from datetime import datetime, timedelta
import math
import getflux
from epsf import epsf
import shutters
import diffractometer
import detector
#from bl13_guis.extras import epselements

COLLECT_ENV = {}

class collect_prepare(Macro):
    '''Prepare the beamline to collect data'''
    param_def = [[ 'diffrmode', Type.String, '1wedge', 'Type of diffraction experiment' ],]

#    global COLLECT_ENV

    def run(self, diffrmode):
        self.checkPoint()
        self.info('Running collect_prepare in collect_lib')
        
        # First of all, make sure the fast shutter is in the beam and closed, to protect the detector!!!
        # The shutter motor is turned off when the distfluo (fluorescence detector is in
        tries = 0
        maxtries = 100
        while bl13check.is_distfluo_in() and tries < maxtries: 
            if tries == 0 and bl13check.is_distfluo_out_allowed(): 
                self.execMacro('act distfluo out') # move the distfluo to the out position
                self.info('COLLECT_PREPARE: the fluorescence detector is in, removing it.')
            time.sleep(0.05)
            tries = tries +1
        if tries >= maxtries:
                Exception('COLLECT_PREPARE ERROR: it is not allowed to remove the distfluo')
                msg = 'COLLECT_PREPARE ERROR: it is not allowed to remove the distfluo'
                self.error(msg)
                
        self.info('COLLECT_PREPARE: prepare fast shutter')   
        try:
            self.execMacro('turn fshuz on')
            self.execMacro('mv fshuz 0')
            self.execMacro('ni660x_shutter_open_close close')
        except Exception('COLLECT_PREPARE ERROR: Cannot move the fast shutter into position'):
            msg = 'COLLECT_PREPARE ERROR: Cannot move the fast shutter into position'
            self.error(msg)

        collect_env = self.getEnv( 'collect_env' )
        self.debug("Collect environment vars: %s"  % str(collect_env) )

        tries = 0
        maxtries = 50
        fshuz = taurus.Device('fshuz')
        while fshuz.position> 0.01 and tries < maxtries:
            time.sleep(0.1)
            tries = tries +1
        self.info('COLLECT_PREPARE: the position of fshuz %f' % fshuz.position)
            
# -----------------------------------------------------------------------
        # RB set initial omega velocity
        omega = self.getMoveable("omega")
        initomegavelocity = omega.read_attribute('Velocity').value
        omegax = self.getMoveable("omegax")
        initomegaxvelocity = omegax.read_attribute('Velocity').value
        centx = self.getMoveable("centx")
        initcentxvelocity = centx.read_attribute('Velocity').value
        centy = self.getMoveable("centy")
        initcentyvelocity = centy.read_attribute('Velocity').value
        COLLECT_ENV['initomegavelocity'] = initomegavelocity
        COLLECT_ENV['initomegaxvelocity'] = initomegaxvelocity
        COLLECT_ENV['initcentxvelocity'] = initcentxvelocity
        COLLECT_ENV['initcentyvelocity'] = initcentyvelocity
        
        # RB20160825: implement prepdiff_for_diffraction functions
        goon,msg = diffractometer.prepdiff_for_diffraction(collect_env)
        if not goon:
            self.error(msg)
            raise Exception(msg)
# -----------------------------------------------------------------------

# -----------------------------------------------------------------------
# RB 20160829: replaced some lines and call the prepdetector_for_diffraction function
          
        self.info('COLLECT_PREPARE: Preparing detector for diffraction')
        restart_dev_lst = ['bl13/eh/pilatuslima']

        goon,msg = detector.detector.prepdetector_for_diffraction(collect_env)
        if not goon:
            restarting_devs = False
            self.info('COLLECT_PREPARE: Checking that device servers are fine')
            for resdev in restart_dev_lst:
                if resdev in msg:
                    restarting_devs = True
                    self.warning('COLLECT_PREPARE WARNING: Restarting the device server %s' % resdev)
                    self.execMacro('restartDS %s' % resdev)
            if restarting_devs:
                time.sleep(5) # TODO: do this more better, 5 secs sometimes not enough
                goon,msg = detector.detector.prepdetector_for_diffraction(collect_env)
            if not goon:
                self.error(msg)
                raise Exception(msg)
            else:
                self.info('COLLECT_PREPARE: device servers seem to be working fine now')
        if not msg == '': self.info('COLLECT_PREPARE: message from prepdetector_for_diffraction:\n %s' % msg)
# -----------------------------------------------------------------------
                    
 
# -----------------------------------------------------------------------
# RB20160825: implement prepshutters_for_diffraction functions TODO
#lines removed
        (goon,msg) = shutters.prepshutters_for_diffraction(collect_env)
        if not goon:
            self.error(msg)
            raise Exception(msg)
#-----------------------------------------------------------------------


        self.info('COLLECT_PREPARE: All commands sent to prepare the beamline elements for diffraction, checking actual state')
        # slow things first: if there's a problem there, no need to wait for slow things like det energy change
        # These lines could go into an overall checking function of the beamline status
        blelementlist = [['shutters',shutters.checkshutters_for_diffraction,20,0.5],\
                        ['diffractometer',diffractometer.checkdiff_for_diffraction,30,1.0]\
                        ,['detector',detector.checkdetector_for_diffraction,120,1.0]] #implement detector function


        for blelement in blelementlist:
            limit = 1
            goon = False
            msg = ''
            maxlimit = blelement[2]
            sleeptime = blelement[3]
            while not goon and limit<maxlimit: 
                (goon,msg) = blelement[1](collect_env)
                if msg:
                    if 'threshold' in msg or 'pilatusspecific' in msg:
                        sleeptime = 5.0
                    self.info('COLLECT_PREPARE: %s waiting with message:\n %s' % (blelement[0], msg))
                self.checkPoint()
                #time.sleep(0.5)
                time.sleep(sleeptime)
                limit = limit + 1
                self.checkPoint()
            if limit == maxlimit:
                self.error(msg)
                raise Exception(msg)
            self.info('COLLECT_PREPARE: %s ready for diffraction' % blelement[0])


        self.info('COLLECT_PREPARE: all good (goon is %s), proceeding to remove the detector cover' % str(goon))
        # close THE DETECTOR COVER for commissioning purposes
        #self.info('COLLECT_PREPARE: Remove the detector cover')
        #self.execMacro('act detcover in')
        #tries = 1
        #maxtries = 25
        #while epsf('read', 'detcover')[2] != 0 and tries<maxtries: 
        #    time.sleep(0.5)

# -----------------------------------------------------------------------
                
class collect_saving(Macro):
    '''  '''

    param_def = [ 
        ['dir', Type.String, "/beamlines/bl13/commissioning/tmp/", 'Data directory'],           #1
        ['prefix', Type.String, None, 'Filename prefix'],                                       #2
        ['run', Type.Integer, None, 'Run number'],                                              #3
        ['startnum', Type.Integer, 1, 'Start file number'],                                     #4 20170328
        ['diffrmode', Type.String, '1wedge', 'Type of diffraction experiment' ],                #5
        ['addfix',Type.String,'','Additional prefix (eg hemispheres for inverse collect'],      #6
        ]

    global COLLECT_ENV

    def run(self, dir, prefix, run, startnum, diffrmode, addfix):
        self.checkPoint()
        self.debug('dir = %s' % dir)
        self.debug('prefix = %s' % prefix)
        self.debug('run = %s' % run)
        self.debug('diffrmode = %s' % diffrmode)
        self.debug('addfix = %s' % addfix)

        self.info('Running collect_saving in collect_lib')
        # Default directory images 
        imgdir = 'images'
        try:
            imgdir = bl13constants.BL13_DATSAV_DICT[diffrmode]
        except Exception, e:
            msg = 'COLLECT_SAVING WARNING: the diffrmode %s is not intialized in the system' % diffrmode
            self.error(msg)
            raise Exception(msg)
            
        # CREATE DIRECTORIES 
        datadir = dir + "/" + prefix + "/" + bl13constants.BL13_DATSAV_DICT[diffrmode] + "/"
        if not os.path.exists(dir): 
            try: 
                os.makedirs(dir)
            except Exception, e: 
                msg = 'COLLECT_SAVING ERROR: Could not create root directory [%s]' % dir
                self.error(msg)
                raise Exception(msg)
        #if stop_execution: raise Exception(msg)
        COLLECT_ENV['dir'] = dir
        self.debug('COLLECT_SAVING: Rootdir made ')
        
        if not os.path.exists(datadir): 
            try: 
                os.makedirs(datadir)
            except Exception, e:  
                msg = 'COLLECT_SAVING ERROR: Could not create data directory %s' % datadir
                self.error(msg)
                raise Exception(msg)
        self.debug('COLLECT_SAVING: Datadir made ')

        if not os.path.exists(datadir): 
            msg = 'COLLECT_SAVING ERROR: The directory %s does not exist' % datadir
            self.error(msg)
            raise Exception(msg)
        elif os.path.isfile(datadir): 
            msg = 'COLLECT_SAVING ERROR: The directory %s exists as a file, cant overwrite as a directory' % datadir
            self.error(msg)
            raise Exception(msg)
            
        COLLECT_ENV['datadir'] = datadir
        self.debug('COLLECT_SAVING: Datadir exists ')
        
        #RB 20150910 for uind1402, copy propriety perl script to datadir
        #if os.path.isfile(bl13constants.BL13_DATPROC_postprocessscript_file):
        #    shutil.copy(bl13constants.BL13_DATPROC_postprocessscript_file, datadir)
        #else: self.info('Post processing file does not exist!!!')
        
        # SEND PARAMETERS TO LIMA
        limaprefix = prefix + "_" + str(run) + "_"
        if addfix != '': 
            limaprefix = limaprefix + addfix + "_"
        COLLECT_ENV['prefix'] = prefix
        COLLECT_ENV['limaprefix'] = limaprefix
        COLLECT_ENV['run'] = run

        self.info('COLLECT_SAVING: Data directory = %s' % datadir)
        #self.info('COLLECT_SAVING: Data directory = %s' % datadir)
        self.info('COLLECT_SAVING: lima_saving %s %s %d' % (datadir, limaprefix, startnum))
        try: 
            # Force AUTO_FRAME required by mxraster 
            #self.execMacro(['lima_saving','pilatus',datadir,limaprefix,'CBF', True])
            self.execMacro(['lima_saving','pilatus',datadir,limaprefix,'CBF', True,startnum]) 
            #self.execMacro(['lima_saving','pilatus',datadir,limaprefix,'TIFF', True,startnum]) 
        except:
            msg ='COLLECT_SAVING ERROR: Error with lima_saving'
            self.error(msg)
            raise Exception(msg)
        self.debug('COLLECT_SAVING: sent data to lima')


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
        ['setroi', Type.String, 'C60', 'ROI to be used: C60, C18, C2'],
        ['diffrmode', Type.String, '1wedge', 'Diffraction ']
        ]

    global COLLECT_ENV

    def run(self, startangle, angleincrement, ni, userexpt, startnum, setroi, diffrmode):
        self.checkPoint()

        self.info('Running collect_mode_config in collect_lib')
        
        # Get environment variables for helical
        collect_env = self.getEnv( 'collect_env' )
        
        # CHECK INPUT VALUES
        if userexpt <= 0:
            msg = 'COLLECT_CONFIG ERROR: Exposure time cannot be <= 0'
            self.error(msg)
            raise Exception(msg)
        
        if setroi == 'C60' and userexpt < 0.08:
            msg = 'COLLECT_CONFIG ERROR: ' + \
                       'Exposure time cannot be < 0.08 sec for ROI = C60'
            self.error(msg)
            raise Exception(msg)
        if setroi == 'C18' and userexpt < 0.04:
            msg = 'COLLECT_CONFIG ERROR: ' + \
                       'Exposure time cannot be < 0.08 sec for ROI = C18'
            self.error(msg)
            raise Exception(msg)

        # DEFINE DEVICES AND VARIABLES
        try:
            var_dev = 'bl13/ct/variables'
            var = taurus.Device(var_dev)
            var_state = var.state()
        except:
            self.error('COLLECT_CONFIG ERROR: ' + \
                       'The DS of the %s Device is unavailable, start it' %(var_dev))
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
            pilatuslima = taurus.Device('pilatus') # pilatuslima device server
        except:
            #self.error('COLLECT_CONFIG ERROR: ' + 
            #           "The DS of the %s Device is unavailable, start it" %(pilatus_dev))
            self.error('COLLECT_CONFIG ERROR: ' + 
                       "The DS of the %s Device is unavailable, start it" %(pilatuslima))
            raise

 
        # CHECK THE MBATS AND CALCULATE TRANSMISSION
        try: 
            transmission = mbattrans.getPosition() / 100. 
        except:
            self.error("COLLECT_CONFIG ERROR: Could not read the mbat positions")
            raise

        if transmission < 0.001: 
            self.warning('COLLECT_CONFIG WARNING: transmission below 0.1 %')
  
        # PREPARE THE VARIABLES NEEDED FOR THE DETECTOR
        self.info('COLLECT_CONFIG: Prepare variables')
        #readouttime = 0.0023
        # TODO: review DS!!
        # This is forced by the new LimaCCDs DS
        readouttime = 0.003
# MULTI TRIGGER TEST
#        readouttime = 0.004

        expt = userexpt - readouttime 
        limaexpt = expt 
        COLLECT_ENV['userexpt'] = userexpt

        try: 
            sampledetdistance = var['detsamdis'].value / float(1000)
        except: 
            self.error("COLLECT_CONFIG ERROR: " + 
                       "Could not read the detector-to-sample distance")
            raise
        try: 
            beamx, beamy = var['beamx'].value, var['beamy'].value
        except: 
            self.error("COLLECT_CONFIG ERROR: Could not read the beam center") 
            raise

        COLLECT_ENV['limaexpt'] = limaexpt
        COLLECT_ENV['readouttime'] = readouttime
        COLLECT_ENV['ni'] = ni
        #COLLECT_ENV['trigger'] = trigger
        COLLECT_ENV['trigger'] = 'EXTERNAL_TRIGGER'
        COLLECT_ENV['startnum'] = startnum

#        COLLECT_ENV['trigger'] = trigger
 
        #
        # Make sure we have a proper reading of the flux, set default if not
        #
        defaultflux = 6E11 * transmission
        if var['fluxlast'].value < 1E7:
            flux = defaultflux
            self.warning('COLLECT_CONFIG WARNING: The set flux has unlikely values, flux set to default of %.2g' % flux)
        else:
            try:
                flux = getflux.lastcurrenttrans()
            except:
                flux = defaultflux
                self.warning('COLLECT_CONFIG WARNING: The set flux has unlikely values, flux set to default of %.2g' % flux)

        # SEND THE MXSETTINGS TO CAMSERVER
        # Aquisition values
        single_header={}
        single_header["Exposure_time"] = '%7f' % limaexpt
        single_header["Exposure_period"] = '%7f' % userexpt
        try:
            single_header["Wavelength"] = "%.5f A" % wavelength.getPosition()
        except:
            single_header["Wavelength"] = 0.979
            self.warning('COLLECT_CONFIG WARNING: The wavelength cannot be read, machine not up? Lambda set to %.2f' % single_header["Wavelength"])
            
        single_header["Detector_distance"] = "%.5f m" % sampledetdistance
        single_header["Detector_Voffset"] = '0 m' #"%.5f m" % detector_vosffset
        single_header["Beam_xy"] = "(%.2f, %.2f) pixels" % (beamx, beamy)
        #single_header["Beam_xy"] = "%.2f, %.2f" % (beamx, beamy)
        single_header["Filter_transmission"] = "%.4f" % transmission
        single_header["Flux"] = "%.4g" % flux
        single_header["Detector_2theta"] = "0.0000"
        single_header["Polarization"] = "0.99" # "%.4f" % polarization
        single_header["Alpha"] = '0 deg.' #"%.4f deg." % alpha
        single_header["Kappa"] = "%.4f deg." % kappa.getPosition()
        single_header["Phi"] = "%.4f deg." % phi.getPosition()
        single_header["Chi"] = "0 deg." # "%.4f deg." % chi
        single_header["Oscillation_axis"] = "X, CW"
        single_header["N_oscillations"] = '1' #"%d" % n_oscillations
        single_header["Start_angle"] = "%.4f deg." % startangle
        single_header["Angle_increment"] = "%.4f deg." % angleincrement
        single_header["Detector_2theta"] = "0.0000 deg" # "%.4f deg." % detector_2theta
        self.info(COLLECT_ENV['datadir'])
        sp = COLLECT_ENV['datadir'].split("/")[:]
        single_header["Image_path"] = ': %s' % str(str.join("/",sp))
        
#        single_header["Image_path"] = ': %s' % str(COLLECT_ENV['datadir']).lstrip()
        #single_header["Threshold_setting"] = '%0f eV' % pilatusdet.energy_threshold
        single_header["Threshold_setting"] = '%0f eV' % pilatusdet.threshold
        single_header["Gain_setting"] = '%s' % str(pilatusdet.threshold_gain)
        
        single_header["Tau"] = '%s s' % str(199.1e-09)
        single_header["Count_cutoff"] = '%s counts' % str(370913)
        single_header["N_excluded_pixels"] = '= %s' % str(1178)
        single_header["Excluded_pixels"] = ': %s' % str("badpix_mask.tif")
        single_header["Trim_file"] = ': %s' % str("p6m0108_E12661_T6330_vrf_m0p20.bin")


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
        COLLECT_ENV['helical_omegax'] = False
        COLLECT_ENV['helical_centx'] = False
        COLLECT_ENV['helical_centy'] = False


        # CHECK THAT OMEGA IS FINE BEFORE DATA COLLECTION
        #if testomega() != '1': 
        #   self.error('ERROR: Omega is not OK')
        #   return
 
        # PREPARE OMEGA
        # on 20130507 omegai/motor27 acceleration was 0.05957 for velocity 1 deg/s 
        # on 20130507 omegai/motor27 acceleration was 0.2 for velocity 50 deg/s (icepapcms) 
        # RB 20160526: for plates, omega cannot be turned on, but omegavelocity will be set to zero
        if not diffrmode== 'plate':
          self.execMacro('turn omega on')
          self.execMacro('turn omegaenc on')

        self.info('COLLECT_CONFIG: define omega')
        omega = self.getMoveable("omega")
        omegavelocity = float(angleincrement) / userexpt
	# 2017/07/07 Apply correction to omega velocity to correct synchronization with pilatus (JAx2)
        # omegavelocity = omegavelocity/1.00023875
        omegaaccelerationtime = omega.read_attribute('Acceleration').value
        omega.write_attribute('velocity', 60)

        self.info('COLLECT_CONFIG: omega velocity = %s' % omegavelocity)
        omegaaccelerationtime = omegaaccelerationtime + 0.2
        safedelta = 3.0 * omegavelocity * omegaaccelerationtime 
        initialpos = startangle - safedelta 
        realfinalpos = startangle + ni*angleincrement

        COLLECT_ENV['omegavelocity'] = omegavelocity
        COLLECT_ENV['initialpos'] = initialpos
        COLLECT_ENV['realfinalpos'] = realfinalpos
        COLLECT_ENV['safedelta'] = safedelta

	# Cretae headers for Lima images. Start number is the only changing value
	# Cretae a list of starting angles
	startangles_list = list()
	for i in range(ni):
            startangles_list.append("%0.4f deg." % (startangle + angleincrement*i))

	headers = list()
	for i, sa in enumerate(startangles_list):
            header = '_array_data.header_convention "PILATUS_1.2"\n' #No present in mxcube
            header += "# Detector: PILATUS 6M, S/N 60-0108, Alba\n"
            header += "# %s\n" % time.strftime("%Y/%b/%d %T")
            header += "# Pixel_size 172e-6 m x 172e-6 m\n"
            header += "# Silicon sensor, thickness 0.000320 m\n"

            # Acquisition values (headers dictionary) but overwrites start angle
            single_header["Start_angle"] = sa
            for key, value in single_header.iteritems():
                header += "# %s %s\n" % (key, value)
            headers.append("%d : array_data/header_contents|%s;" % (i, header))

        pilatuslima.write_attribute('saving_header_delimiter', ["|", ";", ":"])
        pilatuslima.resetCommonHeader()
        pilatuslima.resetFrameHeaders()
        pilatuslima.setImageHeader(headers)

	if diffrmode == 'raster':
            self.warning('Header has already sended for raster image.')
            return

	
        # DEPRECATED: method has been implemented here
        # set_pilatus_header(headers, pilatuslima)

        # RB 20160524: for plates the rotation angle is zero
        if not diffrmode== 'plate':
            try: 
                self.info('COLLECT_CONFIG: Moving omega to initial position %s' % initialpos)
                self.execMacro('mv omega %s' % initialpos) 
            except:
                self.error('COLLECT_CONFIG ERROR: Cannot move omega')
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
            self.info('COLLECT_CONFIG: Wait for omega to stop')
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

            self.debug('COLLECT_CONFIG DEBUG: Characterization is %s' % collect_env['characterization'])
            if not collect_env.get('helical_end_point', False): self.debug('COLLECT_CONFIG: key helical_end_point does not exist')
            elif collect_env['characterization'] == False and len(collect_env['helical_end_point']) == 3: # There are three values for the motor end positions for helical collect
                self.error('COLLECT_CONFIG DEBUG: helical_end_point is %s' % str(collect_env['helical_end_point'])   )
                COLLECT_ENV['omegaxfinpos'] = collect_env['helical_end_point'][0]
                COLLECT_ENV['centxfinpos'] = collect_env['helical_end_point'][1]
                COLLECT_ENV['centyfinpos'] = collect_env['helical_end_point'][2]
                try:
                    COLLECT_ENV['omegaxvel'], ratomx, COLLECT_ENV['centxvel'], ratcenx, COLLECT_ENV['centyvel'], ratceny  = sample.SamplePosition.helical_synchronization(COLLECT_ENV['duration'], 
                                                                                        COLLECT_ENV['omegaxfinpos'], COLLECT_ENV['centxfinpos'], COLLECT_ENV['centyfinpos'])
                except:
                    raise
                omegax = self.getMoveable("omegax")
                centx = self.getMoveable("centx")
                centy = self.getMoveable("centy")
                self.error('COLLECT_CONFIG: Helical collection')
                if not ratomx == -1: 
                    self.debug('COLLECT_CONFIG: setting velocity of omegax to %s' % COLLECT_ENV['omegaxvel'])
                    COLLECT_ENV['helical_omegax'] = True
                    omegax.write_attribute('velocity', COLLECT_ENV['omegaxvel'])
                if not ratcenx == -1: 
                    self.debug('COLLECT_CONFIG: setting velocity of centx to %s' % COLLECT_ENV['centxvel'])
                    COLLECT_ENV['helical_centx'] = True
                    centx.write_attribute('velocity', COLLECT_ENV['centxvel'])
                if not ratceny == -1: 
                    self.debug('COLLECT_CONFIG: setting velocity of centy to %s' % COLLECT_ENV['centyvel'])
                    COLLECT_ENV['helical_centy'] = True
                    centy.write_attribute('velocity', COLLECT_ENV['centyvel'])
            
            # PREPARE NI CARD
            if omegavelocity != 0:
                self.info('COLLECT_CONFIG: startangle %s totalangleincrement %s' 
                      % (startangle, totalangleincrement))
                self.info('COLLECT_CONFIG: omegavelocity %s' % omegavelocity)
                # J.A. TODO: Review fshuz calibration. We need to add an extra 1s to the shutter gate
		# beacause there is a decrease on the images intensity for the last images.
                # This could be due to an incorrect centering of the shutter position.
                # self.execMacro('ni660x_configure_collect 0.0 %s %s 0 1' 
                self.execMacro('ni660x_configure_collect 0.0 %s %s 0 1' 
                           % (startangle, totalangleincrement*(1.005)))
            # MULTI TRIGGER TEST
            #            self.execMacro('ni660x_configure_collect 0.0 %f %f %f %d' 
            #                           % (startangle, angleincrement/2., 
            #                              angleincrement/2., ni))

        # OPEN SLOW SHUTTER , collect_acquire checks if the slowshu opened or not!
        if diffrmode in ['1wedge','inversebeam','plate','test']:
            self.info('COLLECT_CONFIG: Open the slowshu')
            #collect_env = self.getEnv( 'collect_env' )
            self.debug("Collect environment vars: %s"  % str(collect_env) )

            if collect_env['slowshu'] == 'YES':
                try:  
                    if epsf('read', 'slowshu')[2] != 1:
                        self.execMacro('act slowshu out')
                except:
                    self.error('COLLECT_CONFIG ERROR: Cannot actuate the slow shutter')


        # TEMPLATE TO CREATE XDS.INP FILE IN THE STRATEGY
        #prefix = COLLECT_ENV['prefix']
        #run = COLLECT_ENV['run']
        #datadir = COLLECT_ENV['datadir']
        #self.info('COLLECT: Create XDS.INP & mosflm.dat files')
        #self.execMacro('xdsinp %s %d %d %f %f %f %d %s' 
        #               % (prefix, run, ni, startangle, angleincrement, 
        #                  limaexpt, startnum, datadir))
        #self.info('COLLECT: done Create XDS.INP & mosflm.dat files')
        self.info('COLLECT_CONFIG: lima_prepare')
        try: 
            self.info('COLLECT_CONFIG: angleincrement %f' % angleincrement)
            if angleincrement != 0: 
                self.info('COLLECT_CONFIG: lima prepare external trigger')
                trigger = 'EXTERNAL_TRIGGER'
# MULTI TRIGGER TEST
#                trigger = 'EXTERNAL_TRIGGER_MULTI'
            else: 
                self.info('COLLECT_CONFIG: lima prepare internal trigger')
                trigger = 'INTERNAL_TRIGGER'

            self.info('COLLECT_CONFIG: limaexpt %f' % limaexpt)
            self.info('COLLECT_CONFIG: n images %d' % ni)
            self.execMacro(['lima_prepare', 'pilatus', 
                            limaexpt, readouttime, ni, trigger]) # 'pilatus' is bl13/eh/pilatuslima
        except: 
            self.error('COLLECT_CONFIG ERROR: Error with lima_prepare')
            raise


            
class collect_acquire(Macro):
    ''' '''

    param_def = [ 
        ]

    global COLLECT_ENV

    def run(self,):
        self.checkPoint()

        self.info('Running collect_acquire in collect_lib')
        omega = self.getMoveable("omega")

        collect_env = self.getEnv( 'collect_env' )
        self.debug("Collect environment vars: %s"  % str(collect_env) )

        #slowshu = self.getEnv('slowshu')
        
        # CHECK THAT THE SLOWSHU IS OUT
        if collect_env['slowshu'] == 'YES':
            if COLLECT_ENV['limaexpt'] < 0.5: 
                limit = 1
                while epsf('read','slowshu')[2] == 0:
                    self.warning('COLLECT_ACQUIRE WARNING: The slowshu is still closed')
                    if limit > 20:
                        self.error('COLLECT_ACQUIRE ERROR: There is an error with the slowshu')
                        raise
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
        self.info('COLLECT_ACQUIRE: This data collection was started at: %s' % timenow)
        self.debug('COLLECT_ACQUIRE: This data collection will take %s seconds or %s minutes'
                  % (seconds, minutes))
        self.info('COLLECT_ACQUIRE: This data collection will finish at: %s' 
                  % timefinish)
 
 
        # START DATA COLLECTION 
        self.info('COLLECT_ACQUIRE: Start data collection')
        try: 
           if omegavelocity == 0: 
               self.execMacro(['ni660x_shutter_open_close','open'])
           self.debug('COLLECT_ACQUIRE: Acquisition started')
           if COLLECT_ENV['helical_omegax']: # velocities are set in collect_config
               self.debug('COLLECT_CONFIG: moving omegax to %f' % COLLECT_ENV['omegaxfinpos'])
               omegax = self.getMoveable("omegax")
               omegax.write_attribute('position', COLLECT_ENV['omegaxfinpos'])
           if COLLECT_ENV['helical_centx']: 
               self.debug('COLLECT_CONFIG: moving centx to %f' % COLLECT_ENV['centxfinpos'])
               centx = self.getMoveable("centx")
               centx.write_attribute('position', COLLECT_ENV['centxfinpos'])
           if COLLECT_ENV['helical_centy']: 
               self.debug('COLLECT_CONFIG: moving centy to %f' % COLLECT_ENV['centyfinpos'])
               centy = self.getMoveable("centy")
               centy.write_attribute('position', COLLECT_ENV['centyfinpos'])
           self.execMacro(['lima_acquire','pilatus'])
######JA START
           if omegavelocity != 0: 
               try: 
                   self.info('COLLECT_ACQUIRE: Started moving omega toward final position %f' 
                        % COLLECT_ENV['finalpos'])
                   omega.write_attribute('position', COLLECT_ENV['finalpos'])
               except:
                   self.error('COLLECT_ACQUIRE ERROR: Cannot move omega')
                   raise

######JA END
           ni = COLLECT_ENV['ni']

##############
           ## The following while loop waits for the collection to finish, as lima_acquire only sends the command and then exits
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
               self.info("Acquiring: acq status is %s" % acq)
               time.sleep(1)
               if acq != 'Running':
                   break
##############

        except Exception as e: 
 #           self.execMacro('lima_stop_acq') 
            self.error('COLLECT_ACQUIRE ERROR: acquisition failed')
            self.error('Exception is: %s' % str(e))
            self.execMacro(['lima_stop','pilatus'])
            if omegavelocity == 0: self.execMacro(['ni660x_shutter_open_close','close'])
            omega.stop()
            time.sleep(3)
            omega.write_attribute('velocity', COLLECT_ENV['initomegavelocity'])

        # UNCOFIGURE NI660
        self.info('COLLECT_ACQUIRE: Unconfiguring NI660')
        self.execMacro('ni660x_unconfigure_collect')
        

class collect_end(Macro):
    ''' '''

    param_def = [ 
        ]

    global COLLECT_ENV

    def run(self):
        self.info('Running collect_end in collect_lib')

        # DEFINE DEVICES AND VARIABLES
        #force = COLLECT_ENV['force']
        #pshu = COLLECT_ENV['pshu']
        #slowshu = COLLECT_ENV['slowshu']
        #fe = COLLECT_ENV['fe']

        #force = self.getEnv('force')    
        #pshu = self.getEnv('pshu')    
        #slowshu = self.getEnv('slowshu')    
        #fe = self.getEnv('fe')    
        #beamstop = self.getEnv('beamstop')

        collect_env = self.getEnv( 'collect_env' )
        self.debug("Collect environment vars: %s"  % str(collect_env) )

        bstopz_m = taurus.Device('bstopz')
        bstopz = bstopz_m.getAttribute('Position')


        # CLOSE FAST SHUTTER IN STILL MODE
        self.info('COLLECT_END: close fast shutter')
#        if omegavelocity == 0: 
        self.execMacro(['ni660x_shutter_open_close','close'])


        # SET OMEGA VELOCITY TO THE INITIAL ONE
        omega = self.getMoveable("omega")
        omegax = self.getMoveable("omegax")
        centx = self.getMoveable("centx")
        centy = self.getMoveable("centy")
        while omega.read_attribute('StatusMoving').value or omegax.read_attribute('StatusMoving').value or centx.read_attribute('StatusMoving').value or centy.read_attribute('StatusMoving').value:
            self.warning('COLLECT_END: sample motors still moving')
            self.checkPoint()
            time.sleep(1)
        try:
            self.info("COLLECT_END: setting omega velocity to %f" % COLLECT_ENV['initomegavelocity'])
            omega.write_attribute('velocity', COLLECT_ENV['initomegavelocity'])
            omegax.write_attribute('velocity', COLLECT_ENV['initomegaxvelocity'])
            centx.write_attribute('velocity', COLLECT_ENV['initcentxvelocity'])
            centy.write_attribute('velocity', COLLECT_ENV['initcentyvelocity'])
            self.debug('COLLECT_CONFIG: setting velocity of omegax to %s' % COLLECT_ENV['initomegaxvelocity'])
            self.debug('COLLECT_CONFIG: setting velocity of centx to %s' % COLLECT_ENV['initcentxvelocity'])
            self.debug('COLLECT_CONFIG: setting velocity of centy to %s' % COLLECT_ENV['initcentyvelocity'])
            
        except:
            self.error('COLLECT_END WARNING: Could not set initial motor velocities')
        self.info('COLLECT_END: Data collection finished') 

        # MOVE OMEGA TO REAL FINAL POSITION
        try: 
            self.info('COLLECT_END: Moving omega to %s' % COLLECT_ENV['realfinalpos'])
            self.execMacro('mv omega %s' % COLLECT_ENV['realfinalpos']) 
        except:
            self.error('COLLECT_END WARNING: Cannot move omega to final position')

        # remove bsr 
        bsr_m = taurus.Device('bsr')
        bsr_m.getAttribute('position').write(bl13constants.BSR_OUT_POSITION)
        
        # RB: 20150924: no need to close cover, only when changing sample..
        # CLOSE DETECTOR COVER
        #self.info('COLLECT_END: close detector cover')
        #if epsf('read', 'detcover')[2] == 1: 
        #    self.execMacro('act detcover in')              

        # CLOSE SLOW SHUTTER 
        # RB 20160930: why close the slow shutter? Not needed
        #if collect_env['slowshu'] == 'YES':
        #    self.info('COLLECT_END: Close the slow shutter')
        #    try: 
        #       if epsf('read','slowshu')[2] != 0:
        #          self.execMacro('act slowshu in')
        #    except:
        #       self.error('COLLECT_END ERROR: Cannot actuate the slow shutter')
        #       self.info('COLLECT_END: Closing the pshu')
        #       if epsf('read','pshu')[2] != 0:
        #          self.execMacro('act pshu in')
        #elif collect_env['slowshu'] == 'NO':
        #    self.info('COLLECT_END: Not actuating the slow shutter')
 
        # CLOSE PSHU IF ASKED FOR
        # RB 20160930: why close the photon shutter? Not needed
        #if collect_env['pshu'] == 'YES':
        #    self.info('COLLECT_END: Close the safety shutter')
        #    try: 
        #        if epsf('read', 'pshu')[2] == 1:
        #            self.info('COLLECT_END: Closing the safety shutter')
        #            self.execMacro('act pshu close')              
        #            #time.sleep(10)
        #            for trials in range(120):
        #                if epsf('read', 'pshu')[2] != 1:
        #                    break
        #                time.sleep(1)
        #    except:
        #        self.error('COLLECT_END ERROR: Cannot actuate the safety shutter')
        #        return
        #elif collect_env['pshu'] == 'NO':
        #    self.info('COLLECT_END: Not actuating the safety shutter')

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

        # CLOSE BSTOP
        #if epsf('read', 'ln2cover')[2] == 1:
        #    self.info('COLLECT: Moving bstopz')
        #    bstopz_m['PowerOn'] = True
        #    execMacro("mv %s %s" % (bstopz_m.alias(),-96))

        self.info('COLLECT_END: End of data collection')


class collect_check(Macro):  
    ''' '''

    param_def = [ 
        ['param', Type.String, None, 'parameter to be checked'],
        ]

    global COLLECT_ENV

    def run(self, param):
        self.info('Running collect_check in collect_lib')
        
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
            self.info("COLLECT_ENV_GET: Parameter %s does not exist." % param)

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
            self.info("COLLECT_ENV_SET: Parameter %s does not exist." % param)


class collect_env_print(Macro):  
    ''' '''

    param_def = [ 
        ]

    global COLLECT_ENV

    def run(self):
        self.info('COLLECT_ENV_PRINT: list of current parameters')
        for param in COLLECT_ENV.keys():
            self.info("%s = %s" % (param, str(COLLECT_ENV[param])))


