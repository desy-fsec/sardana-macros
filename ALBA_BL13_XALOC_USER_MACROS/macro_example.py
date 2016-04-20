import PyTango
import time

from sardana.macroserver.macro import Macro, Type

class example(Macro):
    
    param_def = [ 
                  [ 'prefix', Type.String, None, 'Filename prefix'],
                  [ 'run', Type.Integer, None, 'Run number'],
                  [ 'ni', Type.Integer, None, 'Number of images'],                 
                  [ 'startnum', Type.Integer, 1, 'Start file number'],
                  [ 'datadir', Type.String, "/beamlines/bl13/commissioning/tmp/", 'Data directory'],                 
                  [ 'slowshu', Type.String, 'YES', 'Force (yes/no) slow shutter open/close'],               
                ]

    def run(self, prefix, run, ni, startnum, datadir, slowshu):
        # SEND PARAMETERS TO LIMA
        limaprefix=prefix+"_"+str(run)+"_"
        limaexpt=expt 
        self.info('Data directory = %s' % datadir)
        self.execMacro(['lima_saving','pilatus',datadir,limaprefix,'CBF',False]) 
        self.execMacro(['lima_prepare','pilatus',ni,'EXTERNAL_TRIGGER',
                        limaexpt]) 
        self.execMacro(['pilatus_set_first_image','pilatus_custom',startnum]) 

        # START DATA COLLECTIO1N 
        self.info('Start data collection')

        try:
            self.execMacro(['lima_acquire','pilatus']) 
            while True:
                limastatus_macro = self.execMacro('lima_status','pilatus')
                state, acq = limastatus_macro.getResult().split()
                time.sleep(1)
                if acq != 'Running' :
                    break
        except: 
            self.execMacro(['lima_stop','pilatus']) 
            omega.write_attribute('velocity',initomegavelocity)
           # CLOSE SLOW SHUTTER 
            if slowshu == 'YES':
                try:
                    self.execMacro('act slowshu in')
                except:
                    self.error('ERROR: Cannot actuate the slow shutter')
            return
