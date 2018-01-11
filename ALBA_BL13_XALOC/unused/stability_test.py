from sardana.macroserver.macro import Macro, Type
import taurus
import time

class Estability_test(Macro):

    '''
           To do E stability tests overnight
    '''

    param_def = [ 
                  [ 'pymcafilename', Type.String, 'Estability_test', 'file name'],
                  [ 'waitingtime', Type.Float, 30, 'waiting time in min'],
                  [ 'measurementgroup', Type.String, 'mg_bpm2', 'mntgrp']
                ]

    def run(self,pymcafilename,waitingtime,measurementgroup):
           self.execMacro('senv ScanID 2')
#           self.execMacro('senv ActiveMntGrp '+measurementgroup)
           self.setEnv('ActiveMntGrp', measurementgroup)
           self.setEnv('ScanFile', pymcafilename+'.h5')
 #          self.execMacro('senv ScanFile Estability_test.h5')
           for i in range(100):
               try:
                   self.execMacro('mv Eugap 8.333')
                   self.info('Scan %i started. ' %i)
                   self.execMacro('dscan Eugap -.2 .2 400 1')
                   self.info('Scan %i done. Wating %.1f min' %(i, waitingtime))
                   time.sleep(60*waitingtime)
               except:
                   self.info('Error in the scan')
           
