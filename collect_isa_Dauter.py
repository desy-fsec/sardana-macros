from sardana.macroserver.macro import Macro, Type
import PyTango
import taurus
import os, time

class collect_isa_Dauter(Macro):
    param_def = [
                     [ 'startangle', Type.Float, 0.0, 'Starting angle (deg)'],                                        #1
                     [ 'angleincrement', Type.Float, 2.0, 'Rotation per frame (deg)'],                                #2
                     [ 'exp_time', Type.Float, 1.0, 'Exposure time (s)'],                                             #3
                ]

    def run(self, startangle, angleincrement, exp_time):
        """ This macro repeats an experiment reported by Zbyscek Dauter in Acta Cryst. (2012). D68, 1430-1436. Default values of the parameters are according to Dauter's experiment """
        repetition = 100 # Dauter paper mentions 100 times
        #collect_env = {'force':'NO','pshu':'NO', 'slowshu':'NO', 'fe':'NO', 'beamstop':'FIXED'}
        collect_env = {'force':'NO','pshu':'YES', 'slowshu':'YES', 'fe':'YES', 'beamstop':'FIXED'}
        self.setEnv( 'collect_env' , collect_env )

        # Parameters as in Dauter are given in comments
        path_to_datacollection = os.path.join( '/beamlines/bl13/commissioning',str(time.strftime("%Y%m%d",time.gmtime())+'-isaDauterTest') )
        file_prefix = 'isaDauterTest'
        number_of_run = 1
        #startangle = 0 # Dauter value irrelevant?
        #angleincrement = 2 # Dauter: 2 degrees
        num_frames = 1 # only one image per collect
        #exp_time = 2 # Dauter: 2 secs (Argonne 85 mA, no attenuation, flux 1x10E11 photons/sec, xtal 50x8 um)
        diffrmode = '1wedge'        

        self.execMacro('collect_prepare %s' % diffrmode)
        for i in range(repetition):
            #collect_simple(path_to_datacollection, file_prefix,number_of_run,startnum,startangle, angleincrement, num_frames, exp_time, diffrmode)
            self.execMacro('collect_saving  %s %s %i %d %s' % (path_to_datacollection, file_prefix, number_of_run, i+1, diffrmode) )
            self.execMacro('collect_config %.3f %.3f %d %.3f %d 0 %s' % (startangle, angleincrement, num_frames, exp_time, i+1, diffrmode) )
            self.execMacro('collect_acquire')
            time.sleep(0.1) # give time to the detector to finish the job
            
        self.execMacro('collect_end')
        
        self.info('collect_isa_Dauter info: Successfully finished')
        
    def on_abort(self):
        # TODO: check for pilatus to finish energy change if required (cam_state of pilatusspecific should not be CHANGE_THRESHOLD
        self.warning('collect_isa_Dauter WARNING: aborting data collection')
        eps = taurus.Device('bl13/ct/eps-plc-01')
        lima_dev = taurus.Device('bl13/eh/pilatuslima')
        omega = taurus.Device('omega')

        self.info('collect_isa_Dauter: close fast shutter')
        #self.execMacro('ni660x_shutter_open_close close')
        self.ni_shutterchan = taurus.Device('BL13/IO/ibl1302-dev1-ctr2')
        self.ni_shutterchan.command_inout('Stop')
        self.ni_shutterchan.write_attribute('IdleState', 'High')
        self.ni_shutterchan.command_inout('Start')

        # stop detector & reset lima
        lima_dev.stopAcq()
        lima_dev.reset()
        
        # close slowshu
        # eps['slowshu'] = 0
        # abort omega movement and reset velocity
        omega.Abort()
        omega.write_attribute('velocity',60)
        self.warning('collect_isa_Dauter info: macro is aborted')
        
