from sardana.macroserver.macro import Macro, Type
import PyTango
import taurus
import os,sys
import bl13constants
import time
import sample

class serial_continuous_collect(Macro):

    param_def = [[ 'number_of_reps', Type.Integer, 1, 'No of repititions'],                                        #0
                    [ 'file_path', Type.String, '/beamlines/bl13/commissioning/tmp/', 'path_to_datacollection'],      #1
                    [ 'file_prefix', Type.String, 'test', 'Filename'],                                                #2
                    [ 'number_of_run', Type.Integer, 1, 'Run number'],                                                 #3
                ]

    def run(self, number_of_reps, file_path, file_prefix, number_of_run):
        
        currep = 0
        self.warning('INFO serial_continuous_collect: starting %d repeated serial collections' % number_of_reps)
        while currep < number_of_reps:
            self.warning('INFO serial_continuous_collect: started collection %d' % int(currep + 1))
            self.execMacro('collect_wrapper %s %d 9998 90 0 0.08 1 %s NO YES YES YES C60 plate' % (file_prefix, int(number_of_run + currep), file_path))
            currep = currep + 1
            time.sleep(20)
            self.warning('INFO serial_continuous_collect: finished %d repeated serial collections' % currep)
        self.warning('INFO serial_continuous_collect: finished %d repeated serial collections' % number_of_reps)

    def on_abort(self):
        self.error('ERROR serial_continuous_collect: data collection finished with error')
