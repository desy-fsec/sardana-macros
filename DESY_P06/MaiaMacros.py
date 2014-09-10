#!/bin/env python

import PyTango
import time
import string
from sardana.macroserver.macro import macro, Type, Macro

__all__ = ["maia_scan", "maia_senv"] 

# Sardana macro for producing a 2D scan using the Maia detector at P.06.
#
# Scans motors through snake pattern
# Controls fast shutter, pauses during beam loss
# Produces one Maia run in the blog directory


pixel1 = 0
maia_extra_file = None

enc_dict = {"p06/hydramotor/exp.01":"enc0", "p06/hydramotor/exp.04":"enc1", "p06/hydramotor/exp.02":"enc2"}
 
class HookPars:
    pass

def hook_pre_move(self, hook_pars):
    global pixel1
    global PetraCurrentDevice
    global maia_extra_file
    global vfcDevice

    # check ring current and wait until it returns
    # pause scan while beam unavailable
    #    while PetraCurrentDevice.BeamCurrent < 75.:
    #        self.output("Scan paused at pixel1 = " + str(pixel1))
    #        time.sleep(15.)
    
    #     check the flux rate and pause the scan if below a limit

    
#    while hook_pars.MaiaFlux0.FluxRate > 10.:
#        self.output("Scan paused at pixel1 = " + str(pixel1))
#        time.sleep(15.)

#    while vfcDevice.Counts < 30.:
#        self.output("Scan paused at pixel1 = " + str(pixel1))
#        time.sleep(15.)  
        
    m = self.macros

    # scan inner motor left or right
    if pixel1 % 2 == 0:
        #self.output("Axis 0 to right: " + str(hook_pars.mot0_right)) 
        m.mv(hook_pars.mot0, hook_pars.mot0_right)
    else:
        #self.output("Axis 0 to left: " + str(hook_pars.mot0_left)) 
        m.mv(hook_pars.mot0, hook_pars.mot0_left)

    # keep the shutter open, as best we can
    # this is because the shutter maximum time is (perhaps) 4000 seconds
    #global ShutterDevice
    #ShutterDevice.SampleTime = 99999.99 original
    #ShutterDevice.SampleTime = 99.99

    # log a progress message
    if pixel1 > 0:
        fraction_done = float(pixel1)/float(hook_pars.npixels1)
        fraction_todo = 1. - float(pixel1)/float(hook_pars.npixels1)
        duration_done = time.time() - hook_pars.starttime
        duration_todo = duration_done/fraction_done*fraction_todo
        time_final = time.localtime(time.time() + duration_todo)
        self.output(
            str(round(fraction_done*100., 2)) + "% done, runtime " +
            str(round(duration_done/60., 1)) + " min, remaining time " + 
            str(round(duration_todo/60., 1)) + " min, estimated completion " + 
            time.strftime("%a %H:%M", time_final)
        )

    pixel1 = pixel1 + 1


@macro(param_def = [
    ['mot0', Type.Moveable, None, 'Internal (fast) motor (axis 0)'],
    ['mot1', Type.Moveable, None, 'External (slow) motor (axis 1)'],
    ['origin0', Type.Float, None, 'Origin position, axis 0'],
    ['origin1', Type.Float, None, 'Origin position, axis 1'],
    ['range0', Type.Float, None, 'Scan extent, axis 0'],
    ['range1', Type.Float, None, 'Scan extent, axis 1'],
    ['pitch0', Type.Float, None, 'Pixel pitch, axis 0'],
    ['pitch1', Type.Float, None, 'Pixel pitch, axis 1'],
    ['dwell', Type.Float, None, 'Time per pixel'],
    ['group', Type.String, "", 'Logger group'],
    ['sample', Type.String, "", 'Name of sample'],
    ['region', Type.String, "", 'Region within sample'],
    ['comment', Type.String, "", 'Other scan comment']
])

def maia_scan(self,
        mot0, mot1,
        origin0, origin1,
        range0, range1,
        pitch0, pitch1,
        dwell,
        group, sample, region, comment):

    """Scans with Maia detector """

    debug_point = 0

    try:
        # get the Maia device names from environment
        maia_dimension0 = self.getEnv('MaiaDimension0Device')
        maia_dimension1 = self.getEnv('MaiaDimension1Device')
        maia_logger = self.getEnv('MaiaLoggerDevice')
        maia_scan = self.getEnv('MaiaScanDevice')
        maia_processing = self.getEnv('MaiaProcessingDevice')
        maia_sample = self.getEnv('MaiaSampleDevice')
        maia_flux0 = self.getEnv('MaiaFlux0Device')
        maia_flux1 = self.getEnv('MaiaFlux1Device')

        # get the other interface device names
        energy_device = self.getEnv('EnergyDevice')
        flux0_device = self.getEnv('Flux0Device')
        flux1_device = self.getEnv('Flux1Device')
        shutter_device = self.getEnv('ShutterDevice')

        debug_point = 1
        # get directory and file name for saving extra maia information
        # open file for writing
        global maia_extra_file
        try:
            dir_temp = self.getEnv('ScanDir')
            file_temp = self.getEnv('ScanFile')
            file_to_open = dir_temp + "/" + file_temp + ".extradata"
            maia_extra_file = open(file_to_open,'a')
            self.output("Extra Maia data will be written to %s " % file_to_open)
        except:
            self.output("ScanDir and/or ScanFile not defined. Extra Maia data will not be saved \n")

        start_scan_info = str('mot0: ' + str(mot0.TangoDevice) + '\n' +
                              'mot1: ' + str(mot1.TangoDevice) + '\n' +
                              'origin0: ' + str(origin0)  + '\n' +
                              'origin1: ' + str(origin1)  + '\n' +
                              'range0: ' + str(range0)  + '\n' +
                              'range1: ' + str(range1)  + '\n' +
                              'pitch0: ' + str(pitch0)  + '\n' +
                              'pitch1: ' + str(pitch1)  + '\n' +
                              'dwell: ' + str(dwell)  + '\n' +
                              'group: ' + str(group)  + '\n')
  
        if maia_extra_file != None:
            maia_extra_file.write(start_scan_info)

        
        # get handles to Tango devices
        MaiaDimension0 = PyTango.DeviceProxy(maia_dimension0)
        MaiaDimension1 = PyTango.DeviceProxy(maia_dimension1)
        MaiaLogger = PyTango.DeviceProxy(maia_logger)
        MaiaScan = PyTango.DeviceProxy(maia_scan)
        MaiaProcessing = PyTango.DeviceProxy(maia_processing)
        MaiaFlux0 = PyTango.DeviceProxy(maia_flux0)
        MaiaFlux1 = PyTango.DeviceProxy(maia_flux1)

        debug_point = 2

        # used by continue_scan()
        global PetraCurrentDevice
        PetraCurrentDevice = PyTango.DeviceProxy("petra/globals/keyword")
        global vfcDevice
        vfcDevice = PyTango.DeviceProxy("p06/vfc/exp.09")

        global ShutterDevice
        ShutterDevice = PyTango.DeviceProxy(shutter_device)

        EnergyDevice = PyTango.DeviceProxy(energy_device) 
        Flux0Device = PyTango.DeviceProxy(flux0_device)
        Flux1Device = PyTango.DeviceProxy(flux1_device)

        debug_point = 3
        
        # remove naughty characters and set the logger group
        group = string.translate(group, None, "'\"")
        MaiaLogger.GroupNext  = group

        # Set the MaiaEncoderAxis to the MaiaDimension

        MaiaDimension0.PositionSource = enc_dict[mot0.TangoDevice]
        MaiaDimension1.PositionSource = enc_dict[mot1.TangoDevice]

        # set the pixel pitch, then read back the actual pixel size
        # (as pixel pitch is rounded to encoder resolution by Maia)
        MaiaDimension0.PixelPitch = pitch0
        MaiaDimension1.PixelPitch = pitch1 
        pitch0 = MaiaDimension0.PixelPitch
        pitch1 = MaiaDimension1.PixelPitch

        debug_point = 4

        # set the origin position, then read back the actual origin
        # (as origin is rounded to pixel pitch by Maia)
        MaiaDimension0.PixelOrigin = origin0
        MaiaDimension1.PixelOrigin = origin1
        origin0 = MaiaDimension0.PixelOrigin
        origin1 = MaiaDimension1.PixelOrigin

        debug_point = 5


        # move motors to the origin position
        self.info("Moving to origin ...")
        macro_mov_pos0,pars = self.createMacro('mv', mot0, origin0)
        macro_mov_pos1,pars = self.createMacro('mv', mot1, origin1)
        self.runMacro(macro_mov_pos0)
        self.runMacro(macro_mov_pos1)
        self.debug(">>> at origin (apparently)")

        self.output("Origin "
            + str(origin0) + MaiaDimension0.PositionUnit + ", "
            + str(origin1) + MaiaDimension1.PositionUnit)
        
        debug_point = 6
        
        # set Maia's idea of current position to "here"
        time.sleep(1.)
#        MaiaDimension0.Position = origin0
#        MaiaDimension1.Position = origin1
        self.debug(">>> calibrated, at pixel "
            + str(MaiaDimension0.PixelCoord) + " "
            + str(MaiaDimension1.PixelCoord))

        # compute true size of scan in pixels
        npixels0 = int(round(range0/pitch0))
        npixels1 = int(round(range1/pitch1))
        MaiaDimension0.PixelCoordExtent = npixels0
        MaiaDimension1.PixelCoordExtent = npixels1 

        self.output("Pixel array "
            + str(MaiaDimension0.PixelCoordExtent) + " x "
            + str(MaiaDimension1.PixelCoordExtent))

        debug_point = 7

        # recompute scan width precisely
        range0 = pitch0 * (npixels0 - 1)
        range1 = pitch1 * (npixels1 - 1)
        self.output("Scan area "
            + str(range0) + MaiaDimension0.PositionUnit + " x "
            + str(range1) + MaiaDimension1.PositionUnit)
        
        MaiaProcessing.PixelEnable = 1

        debug_point = 8
	
	
        # flux metadata items
        flux0_gain = 1.E9/10**(Flux0Device.Gain)
        flux1_gain = 1.E9/10**(Flux1Device.Gain)
        MaiaFlux0.FluxCoeff = flux0_gain
        MaiaFlux1.FluxCoeff = flux1_gain
        MaiaFlux0.FluxName = flux0_device
        MaiaFlux1.FluxName = flux1_device

        debug_point = 9
	
	
        # set up other metadata
        sample = string.translate(sample, None, "'\"")
        region = string.translate(region, None, "'\"")
        comment = string.translate(comment, None, "'\"")
        # ONLY FOR TEST. Comment out the readout from the mono_energy device:
        mono_energy = 0
        # mono_energy = round(EnergyDevice.Position/1000., 4)
    
	
        debug_point = 10
	
        # build the old-style metadata string
        scan_info = str(
            '"{'
                + 'energy:' + str(mono_energy) + ','
                + 'IC_sensitivity0:' + str(flux0_gain) + ','
                + 'IC_sensitivity1:' + str(flux1_gain) + ','
                + 'sample:\'' + sample + '\'' + ','
                + 'region:\'' + region + '\'' + ','
                + 'comment:\'' + comment + '\''
            + '}"')

        
        if maia_extra_file != None:
            maia_extra_file.write(scan_info + "\n")
        
	MaiaScan.ScanDwell = dwell 
        MaiaScan.ScanInfo = scan_info
        MaiaScan.ScanOrder = "012"
        #MaiaScan.ScanCrossRef = str(self.getEnv('ScanID'))

        debug_point = 11


        # Set mot0 to the desired slew rate (save old rate first)
        # (SlewDouble is still not accesible in the Sardana motor)
        mot0_tango = PyTango.DeviceProxy(mot0.TangoDevice)
        mot0_old_slewrate=mot0_tango.SlewDouble 
        mot0_desired_slewrate = pitch0/dwell
        mot0_tango.SlewDouble = mot0_desired_slewrate
	
	
        # set up scan range and counter
        global pixel1
        pixel1 = 0
        starttime=time.time()

        mot0_right = origin0
        mot0_left = origin0 + range0
        mot1_start = origin1
        mot1_final = origin1 + range1
        integ_time = 0.

        debug_point = 12

        # construct scan macro scan in direction 1
        macro,pars = self.createMacro('ascan',
            mot1, mot1_start, mot1_final, npixels1 - 1, integ_time)

        # paramters for scan hook function
        hook_pars = HookPars()
        hook_pars.mot0 = mot0
        hook_pars.mot0_left = mot0_left
        hook_pars.mot0_right = mot0_right
        hook_pars.MaiaScan = MaiaScan
        hook_pars.npixels1 = npixels1
        hook_pars.MaiaDimension1 = MaiaDimension1
        hook_pars.starttime = starttime
        hook_pars.MaiaFlux0 = MaiaFlux0
        f = lambda : hook_pre_move(self, hook_pars)
        macro.hooks = [
            (f, ["pre-move"]),
        ]

        self.info("Maia run "
            + str(MaiaLogger.RunNumber + 1)
            + " (project '" + MaiaLogger.ProjectNext + "'"
            + " group '" + MaiaLogger.GroupNext + "') started"
        )


        debug_point = 13

        # start the run
        MaiaProcessing.PhotonEnable = 1
#        ShutterDevice.SampleTime = 99999.99 original line UB
        ShutterDevice.SampleTime = 99.99
        ShutterDevice.Start()
        MaiaLogger.NewRun()
        MaiaScan.ScanNew = 1
        

        debug_point = 14
        
        # actually do the scan
        self.runMacro(macro)

    except:
        # FIXME how do I do this?
        self.warning("Exception, scan aborted")
        self.warning("At point ")
        self.warning(debug_point)

    finally:
        # after finishing the scan
        MaiaLogger.EndRun()
        MaiaProcessing.PixelEnable = 0
        ShutterDevice.Stop()

        time.sleep(1.5)
        self.info("Maia run "
            + str(MaiaLogger.RunNumber)
            + " (project '" + MaiaLogger.Project + "'"
            + " group '" + MaiaLogger.group + "') now completed: "
            + str(MaiaLogger.RunSize) + " bytes, "
            + str(round(MaiaLogger.RunTime/60.)) + " min"
        )

        # close the file
        end_scan_info = str("Maia run "
            + str(MaiaLogger.RunNumber)
            + " (project '" + MaiaLogger.Project + "'"
            + " group '" + MaiaLogger.group + "') now completed: "
            + str(MaiaLogger.RunSize) + " bytes, "
            + str(round(MaiaLogger.RunTime/60.)) + " min")
        
        if maia_extra_file != None:
            maia_extra_file.write(end_scan_info + "\n")
            maia_extra_file.close()

        # restore old speed
        mot0_tango.SlewDouble = mot0_old_slewrate

# vim:textwidth=79 tabstop=8 softtabstop=4 shiftwidth=4 expandtab


class maia_senv(Macro):
    """ Sets maia environment variables """

    def run(self):
        self.setEnv("MaiaDimension0Device", "p06/maiadimension/exp.00")
        self.output("Setting MaiaDimension0Device to p06/maiadimension/exp.00")
        self.setEnv("MaiaDimension1Device", "p06/maiadimension/exp.01")
        self.output("Setting MaiaDimension1Device to p06/maiadimension/exp.01")
        self.setEnv("MaiaDimension2Device", "p06/maiadimension/exp.02")
        self.output("Setting MaiaDimension2Device to p06/maiadimension/exp.02 (needed for 3D scans)")
        self.setEnv("MaiaScanDevice", "p06/maiascan/exp.01")
        self.output("Setting MaiaScanDevice to p06/maiascan/exp.01")
        self.setEnv("MaiaProcessingDevice", "p06/maiaprocessing/exp.01")
        self.output("Setting MaiaProcessingDevice to p06/maiaprocessing/exp.01")
        self.setEnv("MaiaLoggerDevice", "p06/maialogger/exp.01")
        self.output("Setting MaiaLoggerDevice to p06/maialogger/exp.01")
        self.setEnv("MaiaSampleDevice", "p06/maiasample/exp.01")
        self.output("Setting MaiaSampleDevice to p06/maiasample/exp.01")
        self.setEnv("MaiaFlux0Device", "p06/maiaflux/exp.00")
        self.output("Setting MaiaFlux0Device to p06/maiaflux/exp.00")
        self.setEnv("MaiaFlux1Device", "p06/maiaflux/exp.01")
        self.output("Setting MaiaFlux1Device to p06/maiaflux/exp.01")
        self.setEnv("EnergyDevice", "p06/dcmener/mono.01")
        self.output("Setting EnergyDevice to p06/dcmener/mono.01")
        self.setEnv("Flux0Device", "p06/keithley428/mc01.10")
        self.output("Setting Flux0Device to p06/keithley428/mc01.10")
        self.setEnv("Flux1Device", "p06/keithley428/mc01.11")
        self.output("Setting Flux1Device to p06/keithley428/mc01.11")
        self.setEnv("ShutterDevice", "p06/timer/exp.01")
        self.output("Setting ShutterDevice to p06/timer/exp.01")
