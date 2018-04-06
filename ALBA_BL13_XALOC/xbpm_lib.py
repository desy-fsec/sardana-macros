from sardana.macroserver.macro import Macro, Type
import taurus
#from bl13check import is_xbpm_scan_possible
#from scipy.optimize import curve_fit
import scipy
import numpy as np
import math
import os
import time

class xbpm_align_beam(Macro):
    ''' align the beam using xbpm5 and xbpm6.'''
    param_def = [[ 'fmotorname', Type.String, 'bpm6z', 'Type of diffraction experiment' ]]

    def run(self, fmotorname):
        ''' This macro should be used to scan through the one of the xbpm motors in the experimental hutch (bpm6x, bpm6z, bpm5x, bpm5z) while
        recording the readout on the diamond windows of the respective xbpms. A gaussion fit is fitted through the profile in order to find the 
        center position on the xbpms. The shift at sample position wrt to a reference position is then calculated, which gives the required 
        diftabz position
        '''
        # Motor list to be moved
        scanmotor = taurus.Device(fmotorname)

        # for bpm6z: p0 = [1E-8,-0.027,0.01] # Initial values for scale, center and st. dev.
        if fmotorname == 'bpm6z':
            motorparlib = {'refpos': 0.149, 'scanwidth': 0.1, 'npoints': 50 }

        # Check if the beamline is in conditions to do the scan
        #### NOTE: the slowshu should be close, the fast shutter open!
        if not True: #is_xbpm_scan_possible():
            self.error('xbpm_align_beam: cannot align the beam, the beamline is not prepared')
        
        # save the motor positions to return back later
        scanmotor_pos = scanmotor.position 
        env_scanfile = self.getEnv( 'ScanFile' )
        env_scandir = self.getEnv( 'ScanDir' )
        env_scanid = self.getEnv( 'ScanID' )

        
        # Check if the electrometer ranges are ok
        
        scanf = '%s_scan.dat' % fmotorname
        scand = '/beamlines/bl13/commissioning/tmp'
        self.setEnv( 'ScanFile', scanf)
        self.setEnv( 'ScanDir', scand)
        self.setEnv( 'ScanID', '1')

        # call xbpmz_scan_ver
        #datalib = self.xbpmz_scan_ver('bpm6z',0.05,5,0.1,scand,scanf) # for testing
        datalib = self.xbpmz_scan_ver(scanmotor,motorparlib['scanwidth'],motorparlib['npoints'],0.1,scand,scanf)
        
        # Return motor positions
        # Wait for motors to stop
        #try: 
        #    while self.anymotormoving([bpm5x,bpm5z,bpm6x,bpm6z]): 
        #       time.sleep(0.1)
        #except:
        #    self.debug('Cant wait for motors')
        
        # return motors to original positions
        scanmotor.getAttribute('position').write(scanmotor_pos)

        # Reset to previous scanfile and ActiveMntGrp parameters
        self.setEnv( 'ScanFile', env_scanfile)
        self.setEnv( 'ScanDir', env_scandir)
        self.setEnv( 'ScanID', env_scanid)
        
        #### Analyze the data
        baseline, slope, pkhght, center, sigma, FWHM = self.analyze_xbpm_scan(datalib)
        
        # Check if the data make sense
        dataok = True
        if pkhght < 10 * baseline: dataok = False
        if FWHM > 0.8 or FWHM < 0.07: dataok = False
        if not dataok:
            raise Exception('xbpm_align_beam: Unrealistic beam fit parameters. No alignment done')
        
        ###TODO: this should be done in a different macro. The idea is to run two scans in paralel, one for bpm5x/z in door_sats and one for bpm6x/z in door_exp
        # Calculate the beam shift at sample position
        self.info('Vertical offset of beam wrt reference position: %g' % (center-motorparlib['refpos']))        

        # Warn if an excessive shift is observed
        if math.fabs(center-motorparlib['refpos']) > 0.002:
            pass
            #email xaloc
        
        
        return

    def xbpmz_scan_ver(self,motor,rel_movz,npoints,intg_intv, scand, scanf):
        '''Do a scan using motor bpm6z. Assumes that the bpm6x motor is in the right position to have the beam fully on ib6ru and ib6rd. 
           bpm6z should be in starting position before calling this macro. The function returns an array of bpm6z motor positions and currents measured on ib6ru and ib6rd'''
        
        # Save the current scanfile and ActiveMntGrp parameters
        env_actmntgrp = self.getEnv( 'ActiveMntGrp' )
        
        # Set the scanfile and ActiveMntGrp parameters
        #scand = '/tmp'
        self.debug('%s' % motor)
        if 'bpm5' in motor:
            self.setEnv( 'ActiveMntGrp', 'mg_bpm5')
        if 'bpm6' in motor:
            self.setEnv( 'ActiveMntGrp', 'mg_bpm6')
        self.debug('%s' % self.getEnv( 'ActiveMntGrp' ) )
        
        # Do the scan
        self.execMacro('dscan %s 0 %f %d %f' % (motor,rel_movz,npoints,intg_intv))
        
        # Read the scan results
        datalib = {}
        with open(os.path.join(scand,scanf)) as f:
            lines = f.readlines()
        for line in lines:
            #self.debug(line)
            if not line[0]=='#':
                field = line.split()
                #self.debug('line has %d fields' % len(field))
                if field: datalib[int(field[0])] = field[1:]

        self.setEnv( 'ActiveMntGrp', env_actmntgrp)
        
        return datalib
        
    def analyze_xbpm_scan(self, datalib):
        # Extract the array from the library
        motorpos = np.array([])
        upperq = np.array([])
        lowerq = np.array([])
        for key in datalib:
            point = datalib[key]
            #self.debug('%s' % point[4])
            #self.debug('%.4g'% float(point[4]))
            motorpos = np.append(motorpos,float(point[0]))
            upperq = np.append(upperq,float(point[2]))
            lowerq = np.append(lowerq,float(point[4]))
        #for x in lowerq: self.debug('lowerq %f' % x)
        # Take gradients, invert one quadrant, average and fit gaussian
        upperq_grad = np.gradient(upperq)
        lowerq_grad = np.gradient(lowerq)
        av_grad = (upperq_grad-lowerq_grad)/2 # Sign of gradients will be opposite
        np.set_printoptions(threshold=np.nan)
        self.info(repr(motorpos))
        self.info(repr(av_grad))
        #for x in lowerq_grad: self.debug('%f' % x)
        #for x in av_grad: self.debug('%.4g' % x)
        import fitlib
        gf = fitlib.GaussianFit()
        baseline, slope, pkhght, center, sigma, FWHM = gf.fit(motorpos,av_grad)
        self.debug('Gaussian peak determined on Mar7 (elog 999): bpm6z = -0.0277')
        self.debug('baseline %.4g, peak height %.4g, mu %.4g, sigma %.4g, FWHM %.4g' % (baseline,pkhght,center,sigma,FWHM))
        return baseline, slope, pkhght, center, sigma, FWHM
        
    def anymotormoving(self, taurusmotorlist):
        answer = False
        msg = ''
        for motor in taurusmotorlist:
            try:
                if motor.statusmoving:
                    answer = True
                    msg = "Motor ", motor," is moving"
            except:
                raise exception('anymotormoving: moving status of motor %s could not be determined'% motor)
                
        return answer,msg
            
    def on_abort(self):
        ''' Abort the scan. Return to default motor positions'''