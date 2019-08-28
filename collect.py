##################################################################################################
#
# 20150211: RB
#       - Changed output messages, included the name of each macro
#
# 20150604: RB
#       - reimplemented startnum for collect_simple
#
# 20150918: RB
#       - started implementation of a single parameter diffraction mode 
#
# 20160722: RB
#       - implemented test_xtal the right way (call only once collect_prepare and collect_end, but multiple calls to save, config and acquire)
#       - Split saving into two parts: first make directories, then prepare beamline, then prepare lima saving. Needed for snapshot
#
##################################################################################################


from sardana.macroserver.macro import Macro, Type
import PyTango
import taurus
import os,sys
import bl13constants
import time
import sample
import math

class collect_wrapper(Macro):

    param_def = [
                    [ 'file_prefix', Type.String, 'test', 'Filename'],                                               #0
                    [ 'number_of_run', Type.Integer, 1, 'RUN'],                                                      #1
                    [ 'num_frames', Type.Integer, 1, 'Number of frames per wedge'],                                  #2
                    [ 'startangle', Type.Float, 0.0, 'Starting angle (deg)'],                                        #3
                    [ 'angleincrement', Type.Float, 1.0, 'Rotation per frame (deg)'],                                #4
                    [ 'exp_time', Type.Float, 1.0, 'Exposure time (s)'],                                             #5
                    [ 'start_frame_num', Type.Integer, 1, 'Start file number'],                                      #6
                    [ 'direc', Type.String, ' /beamlines/bl13/commissioning/tmp/', 'path_to_datacollection'],        #7
                    [ 'force', Type.String, 'NO', 'Force (yes/no) data collection with safety shutter /FE closed'],  #8
                    [ 'pshu', Type.String, 'YES', 'Force (yes/no) safety shutter open'],                             #9
                    [ 'slowshu', Type.String, 'YES', 'Force (yes/no) slow shutter open/close'],                      #10
                    [ 'fe', Type.String, 'YES', 'Force (yes/no) fe open/close'],                                     #11
                    [ 'setroi', Type.String, 'C60', 'ROI to be used: C60, C18, C2'],                                 #12
                    [ 'diffrmode', Type.String, '1wedge', 'Type of diffraction experiment' ],                        #13
                    [ 'inv_displ_angle', Type.Float, 180.0, 'Angle between inverse beam wedges' ],                   #14
                    [ 'inv_total_angle', Type.Float, 10.0, 'Total angle of rotation over one wedge' ],               #15
                ]

    def run(self, prefix, run, ni, startangle, angleincrement, userexpt, startnum, direc, force, pshu, slowshu, fe, setroi, diffrmode, inv_displ_angle, inv_total_angle):
       ''' Wrapper macro that runs appropriate collect macro based on the input parameters. It avoids having multiple macro
buttons in the collect widget '''
       
       #TEST!!!
       #setroi='C18'
       
       # PRINT PARAMETERS
       self.info('COLLECT_WRAPPER: prefix %s\n run %d\n ni %d\n startangle %f \n angleincrement %f \n expt %f \n startnum %d \n dir %s \n force %s \n pshu %s \n slowshu %s  \n fe %s \n setroi %s' % (prefix, run, ni, startangle, angleincrement, userexpt, startnum, direc, force, pshu, slowshu, fe, setroi))
       self.info(' diffrmode %s\n inv_displ_angle %f\n inv_total_angle %f\n' % (diffrmode,inv_displ_angle,inv_total_angle))

       force = force.upper()

       if not diffrmode in ['1wedge','plate','inversebeam','1wedge_mvb','inversebeam_mvb','jet_mvb']:
           self.info('The provided diffracion mode (%s) was not recognized' % diffrmode)

       # Set the default values for the collect environment
       
       collect_env = self.getEnv( 'collect_env' )
       collect_env['force'] = force
       collect_env['pshu'] = pshu
       collect_env['slowshu'] = slowshu
       collect_env['fe'] = fe
       #collect_env['beamstop'] = 'MOVEABLE' # 20190604: redundant, the moveable is set below, according to the diffrmode
       #self.error('The moveable beamstop is being used!!') # 20190604: redundant, the moveable is set below, according to the diffrmode
       collect_env['beamstop'] = 'FIXED' 
       collect_env['setroi'] = setroi
       collect_env['characterization'] = False

       simulation = self.getEnv( 'MXCollectSimulation' )
       if simulation:
            self.warning('COLLECT_WRAPPER: Operating in SIMULATION  mode')
            collect_env['force'] = 'NO'
            collect_env['pshu'] = 'NO'
            collect_env['slowshu'] = 'NO'
            collect_env['fe'] = 'NO'
            collect_env['beamstop'] = 'FIXED'
            collect_env['setroi'] = setroi

       # 20170412: EPS changed: now EH motor icepap racks 0 and 2 (first and third from the top) are turned off, fshuz is not on any more
       # This is taken care of in collect_prepare
       # 20160825 RB: by default, fast shutter is now lowered to cover beam, to make sure that the shutters are ok for collect_prepare.
       # This may seems duplicated, but is necessary to ensure that sample is not exposed during shutter operations in preparing the experiment!!
       self.info('COLLECT_WRAPPER: close fast shutter')   
       fshuz = taurus.Device('fshuz')
       try:
           if math.fabs(fshuz.position) > 0.01:
               self.execMacro('turn fshuz on')
               #self.error("20190719 RB: fshuz will not move in!!!!! Revert lines 97-98 in collect_wrapper")
               self.execMacro('mv fshuz 0')
           self.execMacro('ni660x_shutter_open_close close')
       except Exception as e:
           self.error('COLLECT_WRAPPER ERROR: Cannot actuate the fast shutter')
           self.error('COLLECT_WRAPPER ERROR: error message %s' % e.message)
           return

       #tries = 0
       #maxtries = 50
       #while fshuz.position> 0.01 and tries < maxtries:
       #   time.sleep(0.1)
       #   tries = tries +1
          
       # RB 20160531: use the moveable beamstop if requested
       if '_mvb' in diffrmode or diffrmode == 'plate':
           self.info('COLLECT_WRAPPER: Moveable beamstop')
           collect_env['beamstop'] = 'MOVEABLE'
           diffrmode = diffrmode.strip('_mvb')
           self.info('COLLECT_WRAPPER: collect mode after stripping moveable part: %s' % diffrmode)
           
       self.setEnv( 'collect_env' , collect_env )
       
       # CHECK THAT THE VALUES MAKE SENSE
       if ni < 0:
           self.error('COLLECT_WRAPPER ERROR: Error number of images cannot be < 0')
           return
       elif ni > 9999:
           self.error('COLLECT_WRAPPER ERROR: Number of images cannot be > 9999')
           return
       if angleincrement > 12:
           self.error('COLLECT_WRAPPER ERROR: Angle increment > 12')
           return
       if startnum < 1:
           self.error('COLLECT_WRAPPER ERROR: start number cannot be < 1')
           return
       if setroi == 'C60' and userexpt < 0.08:
           self.error('COLLECT_WRAPPER ERROR: Exposure time cannot be < 0.08 sec for ROI = 0')
           return
       if setroi == 'C18' and userexpt < 0.0399:
           self.error('COLLECT_WRAPPER ERROR: Exposure time cannot be < 0.04 sec for ROI = C18')
           return
       totaltimeestimated = (userexpt*ni)/3600.
       if totaltimeestimated > 3:
           self.error('COLLECT_WRAPPER ERROR: Total data collection time > 3 h')
           return
       finalnum = ni+startnum
       if finalnum > 9999:
           self.error('COLLECT_WRAPPER ERROR: Final image number > 9999')
           return
           
       # -------------------------------------------------------------------------------------------------------
       # Now start the diffraction block
       try: 
           if diffrmode in ['inversebeam']:
               self.execMacro('collect_inverse',direc,prefix,run,startangle,angleincrement,ni,userexpt,inv_displ_angle,inv_total_angle,diffrmode)
               defaultcollection = False
           if diffrmode in ['plate']:
               if startangle != 90:
                   self.error('COLLECT_WRAPPER ERROR: Plate diffraction requires omega = 90 deg.')
                   return
               self.execMacro('collect_simple',direc,prefix,run,startnum,startangle,0,ni,userexpt,diffrmode)
               defaultcollection = False
           if diffrmode in ['1wedge','jet']:
               #pass
               self.execMacro('collect_simple',direc,prefix,run,startnum,startangle,angleincrement,ni,userexpt,diffrmode)
       except Exception, e:
            self.error('COLLECT_WRAPPER ERROR: exception raised, error below')
            self.error(e)
            self.on_abort()
       # --------------------------------------------------------------------------------------------------------
       
       self.execMacro('unset_helical_end_point')
       self.info('COLLECT_WRAPPER: End of collection')

    # ABORT DATA COLLECTION 
    def on_abort(self): 
        # TODO: check for pilatus to finish energy change if required (cam_state of pilatusspecific should not be CHANGE_THRESHOLD
        self.error('COLLECT WARNING: aborting data collection')
        eps = taurus.Device('bl13/ct/eps-plc-01')
        lima_dev = taurus.Device('bl13/eh/pilatuslima')
        omega = taurus.Device('omega')
        omegax = taurus.Device('omegax')
        centx = taurus.Device('centx')
        centy = taurus.Device('centy')
        bsr = taurus.Device('bsr')
        bsr.Abort()

        # close fast shutter
        self.info('COLLECT_END: close fast shutter')
        self.ni_shutterchan = taurus.Device('BL13/IO/ibl1302-dev1-ctr2')
        self.ni_shutterchan.command_inout('Stop')
        self.ni_shutterchan.write_attribute('IdleState', 'High')
        self.ni_shutterchan.command_inout('Start')

        # stop detector & reset lima
        # JA 20170918: Change stop by Abort
        #lima_dev.stopAcq()
        #lima_dev.reset()
        lima_dev.abortAcq()
        # 20190719 RB : close slowshu
        eps['slowshu'] = 0
        # abort omega movement and reset velocity
        omega.Abort()
        omegax.Abort()
        centx.Abort()
        centy.Abort()
        try: bsr.write_attribute('position', bl13constants.BSR_OUT_POSITION)
        except Exception as e: # When the yag is in, the motor is disabled
            self.error('COLLECT_WRAPPER on_abort ERROR: exception raised, error below')
            self.error(e)

        omega.write_attribute('velocity',60)
        omegax.write_attribute('velocity',1.0)
        centx.write_attribute('velocity',0.15)
        centy.write_attribute('velocity',0.15)
       
class collect_simple(Macro):
    
    param_def = [   
                    [ 'path_to_datacollection', Type.String, None, 'path_to_datacollection'], #1
                    [ 'file_prefix', Type.String, None, 'Filename'],                          #2
                    [ 'number_of_run', Type.Integer, None, 'RUN'],                            #3
                    [ 'startnum', Type.Integer, None, 'First image number'],                  #4
                    [ 'startangle', Type.Float, None, 'Starting angle (deg)'],                #5
                    [ 'angleincrement', Type.Float, None, 'Rotation per frame (deg)'],        #6
                    [ 'num_frames', Type.Integer, None, 'Number of frames per wedge'],        #7
                    [ 'exp_time', Type.Float, None, 'Exposure time (s)'],                     #8
                    [ 'diffrmode', Type.String, '1wedge', 'Type of diffraction experiment'],  #9
                    [ 'setroi', Type.String, 'C60', 'ROI to be used: C60, C18, C2'],          #10
                ]
    
    def run (self, path_to_datacollection, file_prefix,number_of_run,startnum,startangle, angleincrement, num_frames, exp_time, diffrmode, setroi):

        file_template='%s_%d_####.cbf'%(file_prefix,number_of_run)
        self.info('COLLECT_SIMPLE: diffrmode %s',diffrmode)
        self.debug('COLLECT_SIMPLE DEBUG: no of images %d' % num_frames)
        
        real = True
        if real:
            # CREATE XDS.INP AND MOSFLM.DAT FILES
            self.info('COLLECT_SIMPLE: Create XDS.INP & mosflm.dat files')
            imgdir = 'images'
            try:
                imgdir = bl13constants.BL13_DATSAV_DICT[diffrmode]
            except Exception, e:
                self.error('COLLECT_SIMPLE ERROR: the diffrmode %s was not recognized' % diffrmode)
                self.error('COLLECT_SIMPLE ERROR: the subdir was set to: %s' % imgdir)
            process_path =  os.path.join(path_to_datacollection,file_prefix,imgdir)
            try:
                self.execMacro('xdsinp %s %d %d %f %f %f %d %s' % (file_prefix,number_of_run,num_frames,startangle,angleincrement,exp_time,startnum,process_path))
            except Exception, e:
                self.error('COLLECT_SIMPLE ERROR: error in preparing the xds script' % diffrmode)
                self.error('COLLECT_SIMPLE ERROR: error is: %s' % e.messageeeee)
                raise e
      
            self.info('COLLECT_SIMPLE: done Create XDS.INP & mosflm.dat files')
            #self.execMacro('collect_env_set fe no') ### disable fe for testing
            #self.output('DISABLED FOR TESTING: collect_env_set fe no')

            # Collect
            self.execMacro('collect_prepare %s' % diffrmode)  
            #self.debug("running collect_saving")
            self.execMacro('collect_saving %s %s %i %d %s' % (path_to_datacollection, file_prefix ,number_of_run, startnum, diffrmode))
            self.execMacro('collect_config %.6f %.6f %d %.6f %d %s %s' %(startangle, angleincrement,num_frames, exp_time, startnum, setroi, diffrmode))
            self.execMacro('collect_acquire')
            self.execMacro('collect_end') 

                        
        self.output('COLLECT_SIMPLE: collect_prepare %s' % diffrmode) 
        self.output('COLLECT_SIMPLE: collect_saving %s %s %i %d %s'%(path_to_datacollection, file_template ,number_of_run, startnum, diffrmode))
        self.output('COLLECT_SIMPLE: collect_config %.3f %.3f %d %.3f %d %s %s' % (startangle, angleincrement,num_frames, exp_time,startnum, setroi, diffrmode))
        self.output('COLLECT_SIMPLE: collect_acquire')
        self.output('COLLECT_SIMPLE: collect_end')
        a=os.getcwd()
        self.output(a)
        
class collect_inverse(Macro):
    
    """ Data Collection Strategy to collect an inverse beam dataset. Images are taken in wedges, which are situated in two hemispheres. """
   
    #360 images
    #angle_total=90
    #angleincrement=0.5
   
    #90 images # 3 bi_sets (3*2*15)
    #angle_total=45
    #angleincrement=1
   
   
    #60 images #2 bi_sets
    #angle_total=11.25
    #angleincrement=0.375
   
    param_def = [   
                    [ 'path_to_datacollection', Type.String, None, 'path_to_datacollection'], #1
                    [ 'file_prefix', Type.String, None, 'Filename'], #2
                    [ 'number_of_run', Type.Float, None, 'RUN'], #3
                    [ 'startangle', Type.Float, None, 'Starting angle (deg)'], #4
                    [ 'angleincrement', Type.Float, None, 'Rotation per frame (deg)'],#5
                    [ 'num_frames', Type.Integer, None, 'Number of frames per hemisphere'], #6 #was Float
                    [ 'exp_time', Type.Float, None, 'Exposure time (s)'],#7
                    [ 'displ_angle',Type.Float ,None,'Angle between wedge hemispheres (deg)' ], #8
                    [ 'wedge_angle',Type.Float ,None,'Total angle to be scanned per wedge (deg)' ], #9
                    [ 'diffrmode', Type.String, 'inversebeam', 'Type of diffraction experiment'],  #10                  
                    [ 'setroi', Type.String, 'C60', 'ROI to be used: C60, C18, C2'],          #11
                ]
    
    # define abort action
    
    def run (self, path_to_datacollection, file_prefix, number_of_run, startangle, angleincrement, num_frames, exp_time, displ_angle, wedge_angle, diffrmode, setroi):
        
        #num_frames=int(num_frames) # float from index to integer 
        self.output('COLLECT_INVERSE: path to data collection:%s' % path_to_datacollection)
        self.output('COLLECT_INVERSE: file_prefix:%s' % file_prefix)
        self.output('COLLECT_INVERSE: run %s' % number_of_run)
        self.output('COLLECT_INVERSE: Total angle in a wedge:%s' % wedge_angle )
        
        wedge_frames = int ( wedge_angle / angleincrement )
        if wedge_frames == 0:             wedge_frames = 1
        if wedge_frames > num_frames: wedge_frames = num_frames
        true_wedge_angle = wedge_frames * angleincrement # corrected wedge angle when wedge_angle cannot be divided neatly by the angleincrement

        lastset = num_frames % wedge_frames # last set specifies the left over images in the last set, if there are any
        bi_sets = int(num_frames / wedge_frames) # number of sets (with full wedge_frames) to be measured
        
        self.output("\n\nCOLLECT_INVERSE: 1st WEDGE: Starting angle: %.3f and Final angle: %.3f"%(startangle, startangle + true_wedge_angle))
        self.output("COLLECT_INVERSE: Total angle scanned per wedge: %.3f and per hemisphere: %.3f"%(true_wedge_angle, bi_sets*true_wedge_angle+lastset*angleincrement))
        self.output("COLLECT_INVERSE: 2nd WEDGE: Starting angle: %.3f and Final angle %.3f"%(displ_angle+startangle, displ_angle+startangle + true_wedge_angle))
        self.output("COLLECT_INVERSE: Families of bi-sets: %f, left over images %d" % (bi_sets,lastset))
        self.output('COLLECT_INVERSE: Path to save the data: %s %s %i' % (path_to_datacollection, file_prefix ,number_of_run))
       
        self.output('COLLECT_INVERSE: execMacro (prepare)')
        self.execMacro('collect_prepare %s' % diffrmode) 
        
        t=0
        pilatuslima = taurus.Device('bl13/eh/pilatuslima')
        omega = taurus.Device('omega')

        while t<bi_sets:

            ### Northern  hemisphere
            start_angle = startangle + t * true_wedge_angle    # angle inicial 1er hemisphere
            start_number = 1 + t * wedge_frames         # num imatge inicial 1er hemisphere

            #self.output('COLLECT_INVERSE: execMacro (saving) - %s %s %i %s' % (path_to_datacollection, file_prefix, number_of_run, 'hemi1'))
            #self.output('COLLECT_INVERSE: execMacro (config) - %.3f %.3f %d %.3f %d 0' % (start_angle, angleincrement, wedge_frames, exp_time,start_number) )
            #self.output('COLLECT_INVERSE: execMacro (acquire)')
        
            self.execMacro('collect_saving %s %s %i %d %s %s' % (path_to_datacollection, file_prefix, number_of_run, start_number, diffrmode, 'hemi1'))
            self.execMacro('collect_config %.3f %.3f %d %.3f %d %s %s' % (start_angle, angleincrement,wedge_frames, exp_time,start_number, setroi, diffrmode) )
            self.execMacro('collect_acquire')
            self.execMacro(['ni660x_shutter_open_close','close'])

            self.info( pilatuslima.status() )
            while pilatuslima.acq_status.lower() == 'running' or omega.statusmoving:
                time.sleep(0.1)
            
            ### Southern  hemisphere
            start_angle = startangle + t * true_wedge_angle + displ_angle # angle inicial 2n hemisphere
            #start_number = 1 + t*wedge_frames # num imatge inicial 2n hemisphere
            #self.output('COLLECT_INVERSE: execMacro (saving) - %s %s %i %d %s %s' % (path_to_datacollection, file_prefix, number_of_run, start_number, diffrmode, 'hemi2'))
            #self.output('COLLECT_INVERSE: execMacro (config) - %.3f %.3f %d %.3f %d %s' % (start_angle, angleincrement, wedge_frames, exp_time,start_number, setroi))
            #self.output('COLLECT_INVERSE: execMacro (acquire)')

            self.execMacro('collect_saving %s %s %i %d %s %s' % (path_to_datacollection, file_prefix, number_of_run, start_number, diffrmode, 'hemi2'))
            self.execMacro('collect_config %.3f %.3f %d %.3f %d %s %s' % (start_angle, angleincrement,wedge_frames, exp_time,start_number,setroi, diffrmode) )
            self.execMacro('collect_acquire')
            self.execMacro(['ni660x_shutter_open_close','close'])
            
            t = t + 1

            while pilatuslima.acq_status.lower() == 'running' or omega.statusmoving:
                time.sleep(0.1)

        if lastset > 0:

            ### Northern  hemisphere
            start_angle = startangle + bi_sets * true_wedge_angle
            start_number = 1 + bi_sets * wedge_frames 
            self.output('COLLECT_INVERSE: execMacro (saving) - %s %s %i %d %s %s' % (path_to_datacollection, file_prefix, number_of_run, start_number, diffrmode, 'hemi1'))
            self.output('COLLECT_INVERSE: execMacro (config) - %.3f %.3f %d %.3f %d %s' % (start_angle, angleincrement, lastset, exp_time,start_number, setroi))
            self.output('COLLECT_INVERSE: execMacro (acquire)')

            self.execMacro('collect_saving %s %s %i %d %s %s' % (path_to_datacollection, file_prefix, number_of_run, start_number, diffrmode, 'hemi1'))
            self.execMacro('collect_config %.3f %.3f %d %.3f %d %s'%(start_angle, angleincrement,lastset, exp_time,start_number, setroi))
            self.execMacro('collect_acquire')
            self.execMacro(['ni660x_shutter_open_close','close'])

            self.info( pilatuslima.status() )
            while pilatuslima.acq_status.lower() == 'running' or omega.statusmoving:
                time.sleep(0.1)

            ### Southern  hemisphere
            start_angle = startangle + bi_sets*true_wedge_angle + displ_angle # angle inicial 2n hemisphere
            #start_number = 1 + bi_sets * wedge_frames # num imatge inicial 2n hemisphere
            self.output('COLLECT_INVERSE: execMacro (saving) - %s %s %i %d %s %s' % (path_to_datacollection, file_prefix, number_of_run, start_number, diffrmode, 'hemi2'))
            self.output('COLLECT_INVERSE: execMacro (config) - %.3f %.3f %d %.3f %d %s' % (start_angle, angleincrement, lastset, exp_time,start_number, setroi))
            self.output('COLLECT_INVERSE: execMacro (acquire)')

            self.execMacro('collect_saving %s %s %i %d %s %s' % (path_to_datacollection, file_prefix, number_of_run, start_number, diffrmode, 'hemi2'))
            self.execMacro('collect_config %.3f %.3f %d %.3f %d %s'%(start_angle, angleincrement,lastset, exp_time,start_number, setroi))
            self.execMacro('collect_acquire')
            self.execMacro(['ni660x_shutter_open_close','close'])

            self.info( pilatuslima.status() )
            while pilatuslima.acq_status.lower() == 'running' or omega.statusmoving:
                time.sleep(0.1)

            
        self.output('COLLECT_INVERSE: reached end')
        self.info('COLLECT_INVERSE: Create XDS.INP & mosflm.dat files')
        process_path =  os.path.join(path_to_datacollection,file_prefix)
        self.execMacro('xdsinp %s %d %d %f %f %f %d %s' %(file_prefix,number_of_run,num_frames,startangle,angleincrement,exp_time,1,process_path))
        self.info('COLLECT_INVERSE: done Create XDS.INP & mosflm.dat files')

# adapted crystal diff test
class collect_test_crystal(Macro):
    ''' This macro is used to collect a diffraction dataset '''

    param_def = [ 
                  [ 'prefix', Type.String, None, 'Filename prefix'],						#0
                  [ 'run', Type.Integer, None, 'Run number'],							#1
                  [ 'ni', Type.Integer, None, 'Number of images'],						#2
                  [ 'startangle', Type.Float, None, 'Oscillation start in degrees'],				#3
                  [ 'angleincrement', Type.Float, None, 'Oscillation range in degrees'],			#4
                  [ 'userexpt', Type.Float, None, 'Exposure time in seconds'],					#5
                  [ 'startnum', Type.Integer, 1, 'Start file number'],						#6
                  [ 'dir', Type.String, "/beamlines/bl13/commissioning/tmp/", 'Data directory'],		#7
                  [ 'force', Type.String, 'NO', 'Force (yes/no) data collection with safety shutter /FE closed'],#8
                  [ 'pshu', Type.String, 'YES', 'Force (yes/no) safety shutter open'],				#9
                  [ 'slowshu', Type.String, 'YES', 'Force (yes/no) slow shutter open/close'],			#10
                  [ 'fe', Type.String, 'YES', 'Force (yes/no) fe open/close'],					#11
                  [ 'setroi', Type.String, 'C60', 'ROI to be used: C60, C18, C2'],					#12
                  [ 'anglestotest', Type.String, '0', 'angles to test diffraction']				#13
                ]
    
    WAIT_TIMEOUT = 5
    
    def run(self, prefix, run, ni, startangle, angleincrement, userexpt, startnum,dir,force,pshu,slowshu,fe,setroi,anglestotest):
      try: 
       #setroi = 'C18'
       # PRINT PARAMETERS
       self.info('COLLECT_TEST_CRYSTAL: prefix %s\n run %d\n ni %d\n startangle %f \n angleincrement %f \n expt %f \n startnum %d \n dir %s \n force %s \n pshu %s \n slowshu %s  \n fe %s \n setroi %s \n anglestotest %s' %(prefix,run,ni,startangle,angleincrement,userexpt,startnum,dir,force,pshu,slowshu,fe,setroi,anglestotest))
       
       collect_env = self.getEnv( 'collect_env' )
       collect_env['force'] = force
       collect_env['pshu'] = pshu
       collect_env['slowshu'] = slowshu
       collect_env['fe'] = fe
       #collect_env['beamstop'] = 'MOVEABLE'
       #self.error('The moveable beamstop is being used!!')
       collect_env['beamstop'] = 'FIXED'
       collect_env['setroi'] = setroi
       collect_env['characterization'] = True
       
       simulation = self.getEnv( 'MXCollectSimulation' )
       if simulation:
           self.warning('Operating in SIMULATION  mode')
           collect_env = {'force':'NO','pshu':'NO', 'slowshu':'NO', 'fe':'NO', 'beamstop':'FIXED', 'setroi':setroi}
       
       self.setEnv( 'collect_env' , collect_env )
       
       diffrmode = 'test'
       omega = self.getMoveable("omega")
       initomega = omega.getPosition()
       ni = 1
       if anglestotest == 'still':
          angles = [0]
          angleincrement = 0.0
       if anglestotest != 'still':
          angles = map(float,anglestotest.split(','))
       self.info(angles)

       #prepare for edna
       edna_dir='/beamlines/bl13/commissioning/software/EDNA/templates/'
       edna_difftestlist='EDNA_DIFF_TEST_FILE_LIST.TXT'
       edna_dirdifftestlist=edna_dir+edna_difftestlist 
       edna_list_file=open(edna_dirdifftestlist,"w")
       startnum = 1 
       for angle in angles:
           line='%s/%s/%s/%s_%s_000%s.cbf' %(dir,prefix,'test',prefix,run,startnum)
           self.info('COLLECT_TEST_CRYSTAL: %s' % line)
           edna_list_file.write("%s\n" % line)
           startnum += 1
       edna_list_file.close()
       #return

       imgdir = 'test'
       process_path =  os.path.join(dir,prefix,imgdir)
       self.execMacro('xdsinp %s %d %d %f %f %f %d %s' % (prefix,run,ni,startangle,angleincrement,userexpt,1,process_path))
       self.info('COLLECT_TEST_CRYSTAL: done Create XDS.INP & mosflm.dat files')

       # Take a snapshot if the backlight is up
       eps = taurus.Device('bl13/ct/eps-plc-01')
       if eps['backlight'].value == 0: # backlight is in (up)
           # RB 20160722: take a snapshot of the crystal before removing camera etc
           self.info('COLLECT_TEST_CRYSTAL: saving a snapshot of the crystal')
           import sample
           snapshotfile = os.path.join(dir,prefix,"%s_%d.jpg" %(prefix,run) )
           from bl13constants import OAV_device_name
           sample.snapshot(OAV_device_name,snapshotfile)

       self.execMacro('collect_prepare %s' % diffrmode)  
       self.output('collect_test_crystal: collect_prepare %s' % diffrmode) 
 
       startnum = 1 
       for angle in angles: 
           self.info('COLLECT_TEST_CRYSTAL: Collecting at omega = %f deg' % angle)
           startangle = initomega+angle
           self.info('COLLECT_TEST_CRYSTAL: Collecting at %f' % startangle)
           #self.info('COLLECT_TEST_CRYSTAL: collect_simple %s %s %d %d %f %f %d %f %s' %(dir,prefix,run,startnum,startangle,angleincrement,ni,userexpt,'test',)) 
           # CREATE XDS.INP AND MOSFLM.DAT FILES
           self.info("running collect_saving")
           self.execMacro('collect_saving %s %s %i %d %s' % (dir, prefix ,run, startnum, diffrmode))
           self.output('collect_test_crystal: collect_saving %s %s %i %d %s'%(dir, prefix, run, startnum, diffrmode))
           self.execMacro('collect_config %.6f %.6f %d %.6f %d %s %s' %(startangle, angleincrement,ni, userexpt, startnum, setroi, diffrmode))
           self.output('collect_test_crystal: collect_config %.3f %.3f %d %.3f %d %s %s' % (startangle, angleincrement, ni, userexpt, startnum, setroi, diffrmode))
           self.execMacro('collect_acquire')
           self.output('collect_test_crystal: collect_acquire')
           startnum += 1
           
       self.execMacro('collect_end') 
       self.output('collect_test_crystal: collect_end')
       try: 
           mot = self.getMoveable('omega')
           t1 = time.time()
           while True:
               self.checkPoint()
               if mot.state() != PyTango.DevState.MOVING:
                   self.execMacro('mv omega %s' % initomega)
                   break
               else:
                   time.sleep(0.2)
               t = time.time() - t1
               if t > self.WAIT_TIMEOUT:
                   self.warning("COLLECT_TEST_CRYSTAL: Omega could not be restored to initial position %s." % initomega)
                   break
       except:
           self.warning("COLLECT_TEST_CRYSTAL: Error Moving Omega to Start position %f." % initomega)
           self.warning("Error is: %s" % sys.exc_info()[0] )
      except Exception,e:
          self.error("COLLECT_TEST_CRYSTAL: error in execution, running on_abort")
          self.error(str(e))
          self.on_abort()
      return       

    # ABORT DATA COLLECTION 
    def on_abort(self): 
        # TODO: check for pilatus to finish energy change if required (cam_state of pilatusspecific should not be CHANGE_THRESHOLD
        self.warning('COLLECT WARNING: aborting data collection')
        eps = taurus.Device('bl13/ct/eps-plc-01')
        lima_dev = taurus.Device('bl13/eh/pilatuslima')
        omega = taurus.Device('omega')
        # WORKAROUND: bsr has been removed

        bsr = taurus.Device('bsr')
        bsr.Abort()

        # CLOSE FAST SHUTTER IN STILL MODE
        self.info('COLLECT_END: close fast shutter')
        self.ni_shutterchan = taurus.Device('BL13/IO/ibl1302-dev1-ctr2')
        self.ni_shutterchan.command_inout('Stop')
        self.ni_shutterchan.write_attribute('IdleState', 'High')
        self.ni_shutterchan.command_inout('Start')

        # stop detector & reset lima
        lima_dev.stopAcq()
        lima_dev.reset()

        # 20190719 RB : close slowshu
        eps['slowshu'] = 0

        # abort omega movement and reset velocity
        omega.Abort()
        try: bsr.write_attribute('position', bl13constants.BSR_OUT_POSITION)
        except Exception as e: # When the yag is in, the motor is disabled
            self.error("COLLECT_TEST_CRYSTAL on_abort ERROR: error in moving bsr")
            self.error(str(e))
            self.error('COLLECT_TEST_CRYSTAL on_abort ERROR: continuing...')

        omega.write_attribute('velocity',60)


