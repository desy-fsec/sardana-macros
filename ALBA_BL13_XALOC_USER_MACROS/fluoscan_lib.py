import os
import nxs
import numpy
import math
import time

from sardana.macroserver.macro import Macro, Type
import taurus

class fluoscan(Macro):
    """Executes a fluorescence scan"""

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
                self.info('Created directory %s' % scanDir)
            except: 
                self.error('ERROR: Could not create directory %s' % scanDir)
                return

        msg = 'Running fluorescence scan with:\nFile\t%s/Fluoscan_%s.h5\nEdge\t%s %s\nEdge E\t%.4f keV\nFluo E detected\t%.4f keV\nFullScanWidth\t%d\nScanPoints\t%d' %(scanDir,prefix, element, edge, edgeROI, fluoROI, fullScanWidth, scanPoints)
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
            self.warning('WARNING: waiting for the detector cover to be IN')
            if eps['detcover'].value == 0:
               break
        if eps['detcover'].value == 1:
            self.error('ERROR: the detector cover is still OUT')
            return

        if eps['ln2cover'].value == 1:
            # MOVE BSTOPZ OUT
            self.info('Remove bstopz')
            self.execMacro('turn bstopz on')
            bstopz = self.getMoveable("bstopz")
            lim1 = bstopz.getAttribute('StatusLim-').read().value
            try: 
                if not lim1:
                   self.info('Moving bstopz')
                   bstopz.write_attribute('position',-96.0)
                elif lim1:
                   self.info('Bstopz is at the lim-')
            except:
                self.error('ERROR: Cannot move bstopz')
                return

            # MOVE APERZ OUT
            self.info('Remove aperz')
            self.execMacro('turn aperz on')
            self.execMacro('mvaperz -96')
        
        # REMOVE & TURN OFF BACKLIGHT
        blight['Value'] = '0'
        if not eps['backlight'].value == 1: 
            self.info('Removing backlight...')
            self.execMacro('act backlight out')
            for trials in range(numtrials):
               if eps['backlight'].value == 1:
                  break
               time.sleep(.2)
        if not eps['backlight'].value == 1:
            self.error('ERROR: cannot remove the backlight')
            self.error('WARNING: backlight will be in during fluoscan')


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
            if eps['distfluo'].value == True:
                self.execMacro('act distfluo in')              
        #        self.info('Fluo Detector IN (distfluo)')
                for trials in range(numtrials):
                    if eps['distfluo'].value == True:
                        break
                    time.sleep(.2)
            if eps['distfluo'].value == False:
                self.info('Fluo Detector is In')
        except:
            self.error('ERROR: Cannot actuate the Fluo detector (distfluo)')
            return 


        # OPEN FE IF CLOSED
        try:
            if eps['fe_open'].value == False:
                self.info('Opening the Front End (fe)')
                self.execMacro('fe open')              
                for trials in range(numtrials*2):
                    if eps['fe_open'].value == True:
                        break
                    time.sleep(.2)
            if eps['fe_open'].value == True:
                self.info('FE is Open')
        except:
            self.error('ERROR: Cannot actuate the Front End (fe)')
            return 

        # OPEN PSHU IF CLOSED
        try:
            if eps['pshu'].value == False:
                self.execMacro('act pshu open')              
                self.info('Opening the Photon Shutter (pshu)')
                for trials in range(numtrials*2):
                    if eps['pshu'].value == True:
                        break
                    time.sleep(.2)
#               time.sleep(10)
            if eps['pshu'].value == True:
                self.info('Photon Shutter is Open')
            else:
                self.error('ERROR: Photon Shutter (pshu) is NOT open')
        except:
            self.error('ERROR: Cannot actuate the Photon Shutter (pshu)')
            return 

        # OPEN SLOWSHU IF CLOSED
        try:
            if eps['slowshu'].value == False:
                self.execMacro('act slowshu open')              
                self.info('Opening Slow Shutter (slowshu)')
                for trials in range(numtrials):
                    if eps['slowshu'].value == True:
                        break
                    time.sleep(.2)
            if eps['slowshu'].value == True:
                self.info('Slow Shutter is Open')
            else:
                self.error('ERROR: Slow Shutter (slowshu) is NOT open')
        except:
            self.error('ERROR: Cannot actuate the Slow Shutter (slowshu)')
            return 


        # Prepare environment before scan
        self.oldScanDir = self.getEnv('ScanDir')
        self.oldScanFile = self.getEnv('ScanFile')
        self.oldActiveMntGrp = self.getEnv('ActiveMntGrp')

        self.setEnv('ScanDir', scanDir)
        scanFile = 'Fluoscan_%s.h5' % prefix
        self.setEnv('ScanFile', scanFile)
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

        ##############################################
        # SHOULD MOVE EUGAP TO THE EdgeRoiCenter
        # AND THEN DO A dscan
        # RIGHT NOW, JUST SCAN A DUMMY MOTOR
        # 1) comentar EGY_MOTOR =
        # 2) moure Eugap a edgeroicenter (self.execMacro ...)
        # 3) canviar macro_cmd a dscan .....
        ##############################################
        #EGY_MOTOR = 'dmot1'
        macro_cmd_mvEugap = 'mv Eugap %f' %edgeROI #%(edgeROI/1000) # a keV
        #macro_cmd_mvEugap = 'mv Eugap 9.6586'
        self.execMacro(macro_cmd_mvEugap)
        
        # FINALLY, OPEN FAST SHUTTER
        self.info('Opening Fast Shutter')
        self.execMacro('ni660x_shutter_open_close open')

        #DO FLUO SCAN
        # macro_cmd = 'ascan dmot1 0 10 4 .5'
        # macro_cmd = 'dscan Eugap -.05 .05 50 1'
        # Now the macro has as parameters fullScanWidth, scanPoints
        halfScanWidthKeV = fullScanWidth/1000./2
        scanIntervals = scanPoints - 1
        macro_cmd = 'dscan Eugap -%.3f %.3f %d 1' % (halfScanWidthKeV, halfScanWidthKeV, scanIntervals)
        self.info('Scanning energy with macro: "%s"' % macro_cmd)
        gscan_macro, pars = self.createMacro(macro_cmd)
        self.runMacro(gscan_macro)

        # SCAN DONE. CLOSING SHUTTERS & REMOVING DISTFLUO
        self.info('Closing Fast and Slow Shutters')
        self.execMacro('ni660x_shutter_open_close close')
        self.execMacro('act slowshu close')  
        self.execMacro('act distfluo out')  

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
                in_file_fd.write('%f %f\n' % (energy*1000., edge_counts))
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
                self.error('Exception processing chooch output:\n%s'%str(e))

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

        return str(fluo_data)


    def on_abort(self): 
        # Restore Door environment variables
        self.fluoscan_closure()

        self.error('ERROR: User abort')
        eps = taurus.Device('bl13/ct/eps-plc-01')
        # close fast shutter
        self.info('Closing Fast Shutter')
        ni_shutterchan = taurus.Device('BL13/IO/ibl1302-dev1-ctr2')
        ni_shutterchan.command_inout('Stop')
        ni_shutterchan.write_attribute('IdleState', 'High')
        ni_shutterchan.command_inout('Start')
        # close slowshu
        self.info('Closing Slow Shutter')
        eps['slowshu'] = 0
        # fluo detector OUT
        self.info('Removing Fluorescence Detector')
        eps['distfluo'] = 1

    def fluoscan_closure(self):
        self.setEnv('ScanDir', self.oldScanDir)
        self.setEnv('ScanFile', self.oldScanFile)
        self.setEnv('ActiveMntGrp', self.oldActiveMntGrp)
