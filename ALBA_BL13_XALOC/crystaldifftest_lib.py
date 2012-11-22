from sardana.macroserver.macro import Macro, Type
import taurus
from datetime import *
import os
import time

class crystaldifftest(Macro):
    ''' This macro is used to collect a diffraction dataset '''

    param_def = [ 
                  [ 'prefix', Type.String, None, 'Filename prefix'],
                  [ 'run', Type.Integer, None, 'Run number'],
                  [ 'ni', Type.Integer, None, 'Number of images'],
                  [ 'startangle', Type.Float, None, 'Oscillation start in degrees'],
                  [ 'angleincrement', Type.Float, None, 'Oscillation range in degrees'],
                  [ 'userexpt', Type.Float, None, 'Exposure time in seconds'],
                  [ 'startnum', Type.Integer, 1, 'Start file number'],
                  [ 'dir', Type.String, "/beamlines/bl13/commissioning/tmp/", 'Data directory'],
                  [ 'force', Type.String, 'NO', 'Force (yes/no) data collection with safety shutter /FE closed'],
                  [ 'pshu', Type.String, 'YES', 'Force (yes/no) safety shutter open'],
                  [ 'slowshu', Type.String, 'YES', 'Force (yes/no) slow shutter open/close'],
                  [ 'fe', Type.String, 'YES', 'Force (yes/no) fe open/close'],
                  [ 'setroi', Type.String, '0', 'ROI to be used: 0, C18, C2'],
                  [ 'anglestotest', Type.String, '0', 'angles to test diffraction']
                ]

    def run(self, prefix, run, ni, startangle, angleincrement, userexpt, startnum,dir,force,pshu,slowshu,fe,setroi,anglestotest):
       a=1
       # PRINT PARAMETERS
       self.info(' prefix %s\n run %d\n ni %d\n startangle %f \n angleincrement %f \n expt %f \n startnum %d \n dir %s \n force %s \n pshu %s \n slowshu %s  \n fe %s \n setroi %s \n anglestotest %s' %(prefix,run,ni,startangle,angleincrement,userexpt,startnum,dir,force,pshu,slowshu,fe,setroi,anglestotest))

       omega = self.getMoveable("omega")
       initomega = omega.getPosition()
       startnum = 1 
       ni = 1
       if anglestotest == 'still':
          angles = [0]
          angleincrement = 0.0
       if anglestotest != 'still':
          angles = map(float,anglestotest.split(','))
       self.info(angles)
       for angle in angles: 
           self.info('Collecting at omega = %f deg' % angle)
           startangle = initomega+angle
           self.info('Collecting at %f' % startangle)
           self.info('collect %s %d %d %f %f %f %d %s %s %s %s %s %s' %(prefix,run,ni,startangle,angleincrement,userexpt,startnum,dir,force,pshu,slowshu,fe,setroi)) 
           self.execMacro('collect %s %d %d %f %f %f %d %s %s %s %s %s %s' %(prefix,run,ni,startangle,angleincrement,userexpt,startnum,dir,force,pshu,slowshu,fe,setroi)) 
           #self.execMacro('collect',prefix,run,ni,startangle,angleincrement,userexpt,startnum,dir,force,pshu,slowshu,fe,setroi) 
           startnum += 1
       self.execMacro('mv omega %s' % initomega)
       return       

       #self.info('Create XDS.INP & mosflm.dat files')
       #self.execMacro('xdsinp %s %d %d %f %f %f %d %s' %(prefix,run,len(angles),angles[0],angleincrement,expt,1,datadir))
       #self.info('End of crystaldifftest')


