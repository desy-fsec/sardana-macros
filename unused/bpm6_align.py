#import os
#import nxs
import numpy as np
import math
#import time
import scipy.stats

from sardana.macroserver.macro import Macro, Type
import taurus


class bpm6_align(Macro):
    """alignment through bpm6
    ** TEST **
    """

    param_def = [['mode', Type.String, 'standard', 'safe/standard'],
                 ['referencez', Type.Float, 0.270153, 'value set as a reference'],
                 ['referencex', Type.Float, -0.101104, 'value set as a reference']]

    
    def run(self, mode, referencez, referencex):

        mode = mode.upper()
        numtrials = 50
        scanlimitz = 0.03
        eps = taurus.Device('bl13/ct/eps-plc-01')
        ib6ruref  =  1.26456e-07
        ib6luref  =  1.6818e-07
        ib6rdref  =  8.07718e-08
        ib6ldref  =  8.84067e-08
  
        mbattrans = self.getMoveable('mbattrans')
        trans_init = mbattrans.read_attribute('Position').value
        mbattrans.write_attribute('Position',100)


        # OPEN SLOWSHU IF CLOSED
        if mode == 'SAFE':
            try:
                if eps['slowshu'].value == 1:
                    self.execMacro('act slowshu close')              
                    self.info('BPM6_ALIGN: Closing Slow Shutter (slowshu)')
                    for trials in range(numtrials):
                        if eps['slowshu'].value == 1:
                            break
                        time.sleep(.2)
                if eps['slowshu'].value == 0:
                    self.info('FLUOSCAN: Slow Shutter is Closed')
                if eps['slowshu'].value == 1:
                    self.error('BPM6_ALIGN ERROR: Slow Shutter (slowshu) is open')
            except:
                self.error('BPM6_ALIGN ERROR: Cannot actuate the Slow Shutter (slowshu)')
                return 

        self.setEnv('ActiveMntGrp', 'mg_bpm6_oav')

        macro_cmd = 'dscan diftabz -%f %f %i 1' %(scanlimitz, scanlimitz, int(round(2*scanlimitz/0.002)))
        self.info('BPM6_ALIGN: Scanning diftabz with macro: "%s"' % macro_cmd)
        gscan_macro, pars = self.createMacro(macro_cmd)
        self.runMacro(gscan_macro)
        gscan_data = gscan_macro.data


        self.info('BPM6_ALIGN: Scan Done')
 
        #self.setEnv('ScanDir', scanDir)
        #scanFile = 'Fluoscan_%s.h5' % prefix
        #self.setEnv('ScanFile', scanFile)

        SCAN_MOTOR = 'diftabz'
        CT_CHANNEL = 'ib6z'
        #EDGE_CHANNEL = 'fluodet_scatteringcts'
        #DEADTIME_CHANNEL = 'fluodet_deadtime'

        zposlist = []
        ib6zposlist = []
        ib6rupos = []
        ib6lupos = []
        ib6rdpos = []
        ib6ldpos = []

        for record in gscan_data.records:
            record_data = record.data
            zpos = record_data[SCAN_MOTOR]
            zposlist.append(float(zpos))
            ct_channel_fullname = self.getExpChannel(CT_CHANNEL).full_name
            ib6zpos = record_data[ct_channel_fullname]
            ib6zposlist.append(float(ib6zpos))

            ib6ru_channel_fullname = self.getExpChannel('ib6ru').full_name
            ib6lu_channel_fullname = self.getExpChannel('ib6lu').full_name
            ib6rd_channel_fullname = self.getExpChannel('ib6rd').full_name
            ib6ld_channel_fullname = self.getExpChannel('ib6ld').full_name

            ib6rupos.append(record_data[ib6ru_channel_fullname]/ib6ruref)
            ib6lupos.append(record_data[ib6lu_channel_fullname]/ib6luref)
            ib6rdpos.append(record_data[ib6rd_channel_fullname]/ib6rdref)
            ib6ldpos.append(record_data[ib6ld_channel_fullname]/ib6ldref)
  
  

        ib6zpos = ( (np.array(ib6rupos)+np.array(ib6lupos)) - (np.array(ib6rdpos)+np.array(ib6ldpos)) )/( (np.array(ib6rupos)+np.array(ib6lupos)) + (np.array(ib6rdpos)+np.array(ib6ldpos)) )
        
        slope, z0_at_ib6z0, r_value, p_value, std_err = scipy.stats.linregress(ib6zpos,zposlist)
        
        optimus1z = z0_at_ib6z0+referencez*slope
        self.info('BPM6_ALIGN: regression: optimus1z  =  z0_at_ib6z0 + referencez * slope')
        self.info('BPM6_ALIGN: regression: %f = %f + %f*%f' %(optimus1z,z0_at_ib6z0,referencez,slope))
        
        if abs(optimus1z-referencez)<scanlimitz:
            self.info('BPM6_ALIGN: Optimized z value is %f, shift %f' %(optimus1z,optimus1z-referencez))
        else:
          self.error('BPM6_ALIGN: Found optimized z value out of reasonable range <%.3f' % scanlimitz)
 
        mbattrans.write_attribute('Position',trans_init)
        self.info('BPM6_ALIGN: Done')
        
 