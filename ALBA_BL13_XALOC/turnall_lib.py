from sardana.macroserver.macro import Macro, Type
import taurus

class turnall(Macro):

    '''
           This macro is used to turn on/off a group of motors 
           EH, OH, ALL
           DATACOL = all motors related to data colection
    '''

    param_def = [ 
                  [ 'motorgroup', Type.String, None, 'motor group: EH, OH, DATACOL, ALL'],
                  [ 'status', Type.String, 'True', 'status']
                ]

    def run(self,motorgroup,status):
       dicton={'ON':True,'OFF':False}
       dicttrue={'True':'ON','False':'OFF'}
       status = status.upper() 
       motorgroup = motorgroup.upper() 
       eh=[
'analz','aperx','aperz','bpm6x','bpm6z','bpm5x','bpm5z','bstopx','bstopz',  'centx',  'centy',  'cryodist',  'dettabx',  'dettaby',  'dettabzb',  'dettabzf',  'diftabxb',  'diftabxf',  'diftabzb',  'diftabzf',  'fshuz',  'kappa',  'omega', 'omegaenc', 'omegax',  'omegay',  'omegaz',  'phi',  'zoommot', 's4hg',  's4vg', 's4ho', 's4vo'
              ]
       all = [
'analz','aperx','aperz','bpm3x','bpm3z','bpm4x','bpm4z','bpm5x','bpm5z','bpm6x','bpm6z','bstopx','bstopz',  'centx',  'centy',  'cryodist',  'dettabx',  'dettaby',  'dettabzb',  'dettabzf',  'diftabxb',  'diftabxf',  'diftabzb',  'diftabzf',  'feh1',  'feh2',  'fev1',  'fev2',  'foilb1',  'foilb2',  'foilb3',  'foilb4',  'fshuz',  'fsm2z',  'hfmbenb',  'hfmbenf',  'hfmpit',  'hfmx',  'hfmz',  'kappa',  'lamopit',  'lamoroll',  'lamox',  'lamoz',  'omega', 'omegaenc', 'omegax',  'omegay',  'omegaz',  'phi',  'pitang',  'pitstroke',  's1d',  's1l',  's1r',  's1u', 's2d',  's2u', 's3l',  's3r',  's4hg',  's4ho',  's4vg',  's4vo',  'theta',  'ugap',  'vfmbenb',  'vfmbenf',  'vfmpit',  'vfmroll',  'vfmx',  'vfmz',  'zoommot'
              ]
       oh = [
'bpm3x','bpm3z','bpm4x','bpm4z','feh1',  'feh2',  'fev1',  'fev2',  'foilb1',  'foilb2',  'foilb3',  'foilb4', 'hfmbenb',  'hfmbenf',  'hfmpit',  'hfmx',  'hfmz',  'lamopit',  'lamoroll',  'lamox',  'lamoz','pitang',  'pitstroke',  's1d',  's1l',  's1r',  's1u', 's2d',  's2u', 's3l',  's3r',  's4hg',  's4ho',  's4vg',  's4vo',  'theta',  'ugap',  'vfmbenb',  'vfmbenf',  'vfmpit',  'vfmroll',  'vfmx',  'vfmz'  
              ]
       datacol = [
'analz','aperx','aperz','bstopx','bstopz',  'centx',  'centy',  'cryodist',  'dettabx',  'dettaby',  'dettabzb',  'dettabzf',  'diftabxb',  'diftabxf',  'diftabzb',  'diftabzf',  'kappa', 'omega', 'omegaenc', 'omegax',  'omegay',  'omegaz',  'phi',  'theta',  'ugap',  'zoommot'
              ]
       if motorgroup not in ['EH','OH','ALL','DATACOL']:
          self.error('Motor group should be:  EH, OH, DATACOL, ALL')
          return
       if status not in ['ON','OFF']:
          self.error('Status should be on or off')
          return
       if motorgroup == 'EH': group = eh
       if motorgroup == 'OH': group = oh
       if motorgroup == 'ALL': group = all
       if motorgroup == 'DATACOL': group = datacol
       self.info('Turning %s the %s motors' % (status,motorgroup))
       for motorname in group:
          try:
             self.info('motor %s' % motorname)
             motor = self.getMoveable(motorname)
             status_motor = motor.getAttribute('PowerOn').read().value 
             if not dicttrue[str(status_motor)] == status:
                motor.write_attribute('PowerOn',dicton[status]) 
             final_status_motor = motor.getAttribute('PowerOn').read().value
             final_state = dicttrue[str(final_status_motor)] 
          except:
             self.error('error %s' % motorname)
 
