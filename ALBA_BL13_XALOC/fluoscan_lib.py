import os
import nxs
import numpy
import math
import time
from epsf import *
import amptekfluodet
from sardana.macroserver.macro import Macro, Type
import taurus
import bl13check
from bl13constants import YAGZ_OUT_POSITION, BSTOPZ_OUT_POSITION

class fluoscan(Macro):
    """Executes a fluorescence scan"""

    BRUKER = 'bruker'
    AMPTEK = 'amptek'

    AMPTEK_TIMEOUT = 12000

    param_def = [['Prefix', Type.String, None, 'Prefix for the scan data file: Fluoscan_$Prefix.h5.'],
                 ['ScanDir', Type.String, None, 'Directory for the scan data.'],
                 ['Element', Type.String, None, 'Element selected (to feed chooch).'],
                 ['Edge', Type.String, None, 'Edge selected (to feed chooch).'],
                 ['CenterFluoROI', Type.Float, None, 'Center of the Fluorescence energy ROI (ROI1 -+ 5eV).'],
                 ['CenterEdgeROI', Type.Float, None, 'Center of the Edge energy ROI (ROI2 +- 5eV).'],
                 ['FullScanWidth', Type.Integer, 100, 'Full scan width in eV.'],
                 ['ScanPoints', Type.Integer, 50, 'Total number of scan points.']]

    result_def = [['fluo_data_dict_str', Type.String, None, 'The Fluo data dictionary as string.']]


    def run(self, prefix, scanDir, element, edge, fluoROI, edgeROI, fullScanWidth, scanPoints):

        # CREATE SCAN DIRECTORY 
        scanDir = scanDir+"/"
        if not os.path.exists(scanDir): 
            try:
                os.makedirs(scanDir)
                self.info('FLUOSCAN: Created directory %s' % scanDir)
            except: 
                self.error('FLUOSCAN ERROR: Could not create directory %s' % scanDir)
                return

        msg = 'FLUOSCAN: Running fluorescence scan with:\nFile\t%s/Fluoscan_%s.h5\nEdge\t%s %s\nEdge E\t%.4f keV\nFluo E detected\t%.4f keV\nFullScanWidth\t%d\nScanPoints\t%d' %(scanDir,prefix, element, edge, edgeROI, fluoROI, fullScanWidth, scanPoints)
        self.info(msg)

        eps = taurus.Device('bl13/ct/eps-plc-01')
        blight = self.getDevice('tango://blight')
        numtrials = 20
        check_pos = False
        
        #out = List(['Name', 'Value'])
        #env = self.getAllDoorEnv()
        #for k,v in env.iteritems():
            #str_val = reprValue(v)
            #out.appendRow([str(k), str_val])
        #currentScanFile = str_val[str.index('ScanFile')]

        # CLOSE THE SLOWSHUTTER & FAST SHUTTER
        self.execMacro('act slowshu in')
        self.execMacro('ni660x_shutter_open_close close')

        # COVER THE DETECTOR
        self.execMacro('act detcover in')
        time.sleep(1.0)
        for trials in range(30):
            time.sleep(1.0)
            self.warning('FLUOSCAN WARNING: waiting for the detector cover to be IN')
            if epsf('read','detcover')[2] == 0:
               break
        if epsf('read','detcover')[2] == 1:
            self.error('FLUOSCAN ERROR: the detector cover is still OUT')
            return

        if epsf('read','ln2cover')[2] == 1:
            # MOVE BSTOPZ OUT
            self.info('FLUOSCAN: Remove bstopz')
            self.execMacro('turn bstopz on')
            bstopz = self.getMoveable("bstopz")
            lim1 = bstopz.Limit_switches[2]
            try: 
                if not lim1:
                   self.info('FLUOSCAN: Moving bstopz')
                   bstopz.getAttribute('position').write(BSTOPZ_OUT_POSITION)
                elif lim1:
                   self.info('FLUOSCAN: Bstopz is at the negative limit')
            except:
                self.error('FLUOSCAN ERROR: Cannot move bstopz')
                return

            # MOVE APERZ OUT
            self.info('FLUOSCAN: Remove aperz')
            self.execMacro('turn aperz on')
            self.execMacro('mv aperz -96')
            self.info('FLUOSCAN: Remove yagz')
            # RB 20170503: yagz cannot be turned on when sample on magnet
            self.execMacro('act yag out')
            #self.execMacro('turn yagz on')
            #self.execMacro('mv yagz %f' % YAGZ_OUT_POSITION)

            
        # CHECK THE POSITION OF KAPPA
        kappa = self.getMoveable("kappa")
        # Use LimNeg to check whether KAPPA motor is in place.
        # LimNeg==1 --> Not in place || LimNeg==0 --> In place
        lim1 = kappa.getAttribute('StatusLimNeg').read().value
        if lim1:
           self.warning("FLUOSCAN WARNING: kappa not present")
        if not lim1:
           self.warning("FLUOSCAN WARNING: kappa present")
       #    if math.fabs(kappa.getPosition()) > 0.01:
       #        kappa.write_attribute('position',0.0)
       #    while math.fabs(kappa.getPosition()) > 0.2:
       #        self.warning("FLUOSCAN WARNING: moving kappa to 0") 
       #        time.sleep(1)


        # REMOVE & TURN OFF BACKLIGHT
        blight.write_attribute('Value', 0)
        if epsf('read','backlight')[2] != 1: 
            self.info('FLUOSCAN: Removing backlight...')
            self.execMacro('act backlight out')
            for trials in range(numtrials):
               if eps['backlight'].value == 1:
                  break
               time.sleep(.2)
        if epsf('read','backlight')[2] != 1:
            self.error('FLUOSCAN ERROR: cannot remove the backlight')
            self.error('FLUOSCAN WARNING: backlight will be in during fluoscan')


        ## CHECK THAT THE DETECTOR DOES NOT GET THE DIRECT BEAM 
        #m = self.execMacro('testdet')
        #testdetvalue = m.getResult() 
        #self.info('The result of testing the detector is %s' %testdetvalue) 
        #if not testdetvalue == '1':
            #self.error('There is an error with the beamstop')
            #return
        ## testdet macro leaves open FE and PSHU, and closes fshu and slowshu


        # BEFORE OPENING SHUTTERS, CLOSE FAST SHUTTER
        self.execMacro('ni660x_shutter_open_close close')  

        # FLUO DETECTOR IN
         
        try:
            if epsf('read','distfluo')[2] == 1:
                self.execMacro('act distfluo in')              
                limit = 0
                while epsf('read','distfluo')[2]:
                    self.warning("FLUOSCAN WARNING: moving the fluorescence detector IN") 
                    time.sleep(1)
                    limit = limit + 1
                    if limit > 40:
		      self.error("FLUOSCAN ERROR: Can NOT actuate the fluorescence detector IN")
		      return
                self.info('FLUOSCAN: Fluo Detector IN (distfluo)')

            if epsf('read','distfluo')[2] == 0:
                self.info('FLUOSCAN: Fluo Detector is already IN') 
        except:
            self.error('FLUOSCAN ERROR: Cannot connect with the Fluo detector (distfluo). Not moved.')


        # OPEN FE IF CLOSED
        try:
            if epsf('read','fe_open')[2] == False:
                self.info('FLUOSCAN: Opening the Front End (fe)')
                self.execMacro('fe open')              
                for trials in range(numtrials*2):
                    if eps['fe_open'].value == True:
                        break
                    time.sleep(.2)
            #if eps['fe_open'].value == True:
            if epsf('read','fe_open')[2] == True:
                self.info('FLUOSCAN: FE is Open')
        except:
            self.error('FLUOSCAN ERROR: Cannot actuate the Front End (fe)')
            return 

        # OPEN PSHU IF CLOSED
        try:
            if epsf('read','pshu')[2] == 0:
                self.execMacro('act pshu open')              
                self.info('FLUOSCAN: Opening the Photon Shutter (pshu)')
                for trials in range(numtrials*2):
                    if epsf('read','pshu')[2] == 1:
                        break
                    time.sleep(.2)
#               time.sleep(10)
            if epsf('read','pshu')[2] == 1:
                self.info('FLUOSCAN: Photon Shutter is Open')
            else:
                self.error('FLUOSCAN ERROR: Photon Shutter (pshu) is NOT open')
        except:
            self.error('FLUOSCAN ERROR: Cannot actuate the Photon Shutter (pshu)')
            return 

        # OPEN SLOWSHU IF CLOSED
        try:
            if epsf('read','slowshu')[2] == 0:
                self.execMacro('act slowshu open')              
                self.info('FLUOSCAN: Opening Slow Shutter (slowshu)')
                for trials in range(numtrials):
                    if epsf('read','slowshu')[2] == 1:
                        break
                    time.sleep(.2)
            if epsf('read','slowshu')[2] == 1:
                self.info('FLUOSCAN: Slow Shutter is Open')
            if epsf('read','slowshu')[2] == 0:
                self.error('FLUOSCAN ERROR: Slow Shutter (slowshu) is NOT open')
        except:
            self.error('FLUOSCAN ERROR: Cannot actuate the Slow Shutter (slowshu)')
            return 


        # Prepare environment before scan depending on the Active detector
        # Backup current environment  configuration
        self.oldScanDir = self.getEnv('ScanDir')
        self.oldScanFile = self.getEnv('ScanFile')
        self.oldActiveMntGrp = self.getEnv('ActiveMntGrp')

        self.setEnv('ScanDir', scanDir)
        scanFile = 'Fluoscan_%s.h5' % prefix
        self.setEnv('ScanFile', scanFile)

        # get current active fluorescence detector
        fluo_det = self.getEnv('ActiveFluoDet')
        self.info('Active fluorescence detector: %s' % fluo_det)

        # configuring according to the active detector
        if fluo_det.lower() == self.BRUKER:
            self.setEnv('ActiveMntGrp', 'mg_fluodet')

            EGY_MOTOR = 'Eugap'
            FLUO_CHANNEL = 'fluodet_fluocts'
            EDGE_CHANNEL = 'fluodet_scatteringcts'
            DEADTIME_CHANNEL = 'fluodet_deadtime'

            # Configure ROIs, for now, extra attributes of expchans
            # some day, a TangoDS, or a 1D Pool element
            roi1 = self.getExpChannel(FLUO_CHANNEL)
            roi1.getAttribute('FluoRoiCenter').write(fluoROI)

            roi2 = self.getExpChannel(EDGE_CHANNEL)
            roi2.getAttribute('EdgeRoiCenter').write(edgeROI)

        elif fluo_det.lower() == self.AMPTEK:
            self.setEnv('ActiveMntGrp', 'mg_amptek')

            # Increase timeout to reduce communication problems
            self.info('Increasing measurement group timeout to %s' % self.AMPTEK_TIMEOUT)
            self.meas = self.getObj('mg_amptek')
            self.meas.set_timeout_millis(self.AMPTEK_TIMEOUT)

            EGY_MOTOR = 'Eugap'
            FLUO_CHANNEL = 'amptek_fluocts'
            EDGE_CHANNEL = 'amptek_scatteringcts'
            #DEADTIME_CHANNEL = 'fluodet_deadtime'

            # Configure ROIs, for now, extra attributes of expchans
            # some day, a TangoDS, or a 1D Pool element
            roi1 = self.getExpChannel(FLUO_CHANNEL)
            fluoROIchan_low = int(amptekfluodet.getchannel(fluoROI - 0.090)[0])
            fluoROIchan_high = int(amptekfluodet.getchannel(fluoROI + 0.090)[0])
            roi1.getAttribute('lowThreshold').write(fluoROIchan_low)
            roi1.getAttribute('highThreshold').write(fluoROIchan_high)
            
            roi2 = self.getExpChannel(EDGE_CHANNEL)
            edgeROIchan_low = int(amptekfluodet.getchannel(edgeROI - 0.090)[0])
            edgeROIchan_high = int(amptekfluodet.getchannel(edgeROI + 0.090)[0])
            roi2.getAttribute('lowThreshold').write(edgeROIchan_low)
            roi2.getAttribute('highThreshold').write(edgeROIchan_high)

            self.info('ROIS SET TO: %d %d' % (fluoROIchan_low, fluoROIchan_high))
            self.info('ROIS SET TO: %d %d' % (edgeROIchan_low, edgeROIchan_high))

        else:
            self.error('Invalid value for ActiveFluoDet (bruker or amptek): %s' % fluo_det)
        ##############################################
        # SHOULD MOVE EUGAP TO THE EdgeRoiCenter
        # AND THEN DO A dscan
        # RIGHT NOW, JUST SCAN A DUMMY MOTOR
        # 1) comentar EGY_MOTOR =
        # 2) moure Eugap a edgeroicenter (self.execMacro ...)
        # 3) canviar macro_cmd a dscan .....
        ##############################################
        
        #move E
        trans_init = self.getMoveable('mbattrans').read_attribute('Position').value
        macro_cmd_mvEalign = 'mv Ealign %f' %edgeROI
        self.info('FLUOSCAN: Moving energy, undulator and diftab: %s' %macro_cmd_mvEalign)
        self.execMacro(macro_cmd_mvEalign)
        #move transmission
        macro_cmd_mbattrans = 'mv mbattrans %.3f' %trans_init
        self.info('FLUOSCAN: Moving transmission to %.2f with %s' %(trans_init, macro_cmd_mbattrans))
        self.execMacro(macro_cmd_mbattrans)
        
        # FINALLY, OPEN FAST SHUTTER
        self.info('FLUOSCAN: Opening Fast Shutter')
        self.execMacro('ni660x_shutter_open_close open')

        #
        # HERE SHOULD COME THE DEAD TIME TEST!
        #
        
        #DO FLUO SCAN
        # macro_cmd = 'dscan Eugap -.05 .05 50 1'
        # Now the macro has as parameters fullScanWidth, scanPoints
        halfScanWidthKeV = fullScanWidth/1000./2
        scanIntervals = scanPoints - 1
        macro_cmd = 'dscan Eugap -%.3f %.3f %d 1' % (halfScanWidthKeV, halfScanWidthKeV, scanIntervals)
        self.info('FLUOSCAN: Scanning energy with macro: "%s"' % macro_cmd)
        gscan_macro, pars = self.createMacro(macro_cmd)
        self.runMacro(gscan_macro)

        # SCAN DONE. CLOSING SHUTTERS & REMOVING DISTFLUO
        self.info('FLUOSCAN: Closing Fast and Slow Shutters')
        self.execMacro('ni660x_shutter_open_close close')
        self.execMacro('act slowshu close')  
        self.execMacro('act distfluo out')  
       
        # Restore timeout if AMPTEK
        if fluo_det.lower() == self.AMPTEK:
            self.meas.set_timeout_millis(3000)

        # EXECUTE CHOOCH
        chooch_prefix = scanFile.replace('.h5','')
        chooch_input_filename = 'chooch-%s-%s-%s.txt' % (chooch_prefix, element, edge)
        chooch_output_filename = 'chooch-%s-%s-%s-output.txt' % (chooch_prefix, element, edge)
        chooch_output_ps_filename = 'chooch-%s-%s-%s.ps' % (chooch_prefix, element, edge)
        chooch_output_efs_filename = 'chooch-%s-%s-%s.efs' % (chooch_prefix, element, edge)



        in_file = os.path.join(scanDir, chooch_input_filename)
        out_file = os.path.join(scanDir, chooch_output_filename)
        ps_out_file = os.path.join(scanDir, chooch_output_ps_filename)
        efs_out_file = os.path.join(scanDir, chooch_output_efs_filename)

        gscan_data = gscan_macro.data

        maxdeadtime = -1000.
        with open(in_file, 'w') as in_file_fd:
            # before all records, to avoid chooch segfaults
            # we define a title shorter than 80 columns
            trans = self.getMoveable('mbattrans').read_attribute('Position').value
            title = '%s %s %s trans: %.2f %%' % (chooch_prefix, element, edge, trans)
            points = len(gscan_data.records)
            in_file_fd.write('%s\n'%title)
            in_file_fd.write('%d\n'%points)
            for record in gscan_data.records:
                record_data = record.data
                energy = record_data[EGY_MOTOR]
                fluo_channel_fullname = self.getExpChannel(FLUO_CHANNEL).full_name
                #edge_counts = record_data[FLUO_CHANNEL]
                edge_counts = record_data[fluo_channel_fullname]
                # Protect from no data:
                if edge_counts: 
                    in_file_fd.write('%f %f\n' % (energy*1000., edge_counts))

                if fluo_det.lower() == self.BRUKER:
                    deadtime_channel_fullname = self.getExpChannel(DEADTIME_CHANNEL).full_name
                    if maxdeadtime < record_data[deadtime_channel_fullname]:
                        maxdeadtime = record_data[deadtime_channel_fullname]
        
        #############################################################
        ## LET'S GET DUMMY DATA FROM sicilia@ibl1302:tmp/gcuni...
        ## BECAUSE I AM JUST PLAYING WITH A DUMMY MOTOR...
        ## in_file = '/homelocal/sicilia/tmp/gcuni/SeMet.raw'
        #############################################################

        chooch_cmd = 'chooch -e %s -a %s -p %s -o %s %s 2>&1' % (element, edge, ps_out_file, efs_out_file, in_file)

        peak = None
        infl = None
        remote = None
        with os.popen(chooch_cmd) as chooch_output:
            # Get peak and inflection could be done with a
            # match regexp of full output but, right now, we need
            # the complete flow proof of concept...
            lines = chooch_output.readlines()
            try:
                peak = float(lines[-3].split('|')[2])/1000.
                infl = float(lines[-2].split('|')[2])/1000.
                remote = peak + 1.
            except Exception,e:
                self.error('FLUOSCAN ERROR: Exception processing chooch output:\n%s'%str(e))

            # Keep chooch output just for the user...
            with open(out_file, 'w') as out_file_fd:
                out_file_fd.writelines(lines)

        fluo_data = {}
        fluo_data['peak'] = peak
        fluo_data['inflection'] = infl
        fluo_data['remote'] = remote
        fluo_data['deadtime'] = maxdeadtime
        if peak is not None and infl is not None:
            fluo_data['ps_file'] = ps_out_file
        else:
            # PS FILE NOT GENERATED
            fluo_data['ps_file'] = None

        # Restore Door environment variables
        self.fluoscan_closure()

        self.execMacro('turnall eh on')
        return str(fluo_data)


    def on_abort(self): 
        # Restore Door environment variables
        self.fluoscan_closure()

        self.error('FLUOSCAN ERROR: User abort')
        eps = taurus.Device('bl13/ct/eps-plc-01')
        # fluo detector OUT
        self.info('FLUOSCAN: Removing Fluorescence Detector')
        if bl13check.is_distfluo_out_allowed(): 
            self.execMacro('act distfluo out')
        # close fast shutter
        self.info('FLUOSCAN: Closing Fast Shutter')
        ni_shutterchan = taurus.Device('BL13/IO/ibl1302-dev1-ctr2')
        ni_shutterchan.command_inout('Stop')
        ni_shutterchan.write_attribute('IdleState', 'High')
        ni_shutterchan.command_inout('Start')
        # close slowshu
        self.info('FLUOSCAN: Closing Slow Shutter')
        eps['slowshu'] = 0
        # close slowshu
        self.info('FLUOSCAN: Turning all motors on')
        self.execMacro('turnall eh on')

    def fluoscan_closure(self):
        self.setEnv('ScanDir', self.oldScanDir)
        self.setEnv('ScanFile', self.oldScanFile)
        self.setEnv('ActiveMntGrp', self.oldActiveMntGrp)
