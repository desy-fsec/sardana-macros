from sardana.macroserver.macro import Macro, Type
import taurus
import time


class turn(Macro):

    '''
           This macro is used to turn on/off any motor 
    '''

    param_def = [ 
                  [ 'motorname', Type.String, None, 'motor name'],
                  [ 'status', Type.String, 'True', 'status']
                ]
    
    def run(self,motorname,status):
        dicton={'ON':True,'OFF':False}
        dicttrue={'True':'ON','False':'OFF'}
        status = status.upper() 
        motor = self.getMoveable(motorname)

        #Check if the motor is with External disable
        motor_enable = motor.getAttribute('statusdisable').read().value
        if  motor_enable ==  'Disable':
            msg = ('The %s Motor is in External Disabling Mode. '
                   'Verify the EPS signals.' % motorname)
            raise Exception(msg)

        status_motor = motor.getAttribute('PowerOn').read().value
        if status == 'STATUS': 
            self.info('%s is %s' % (motorname,dicttrue[str(status_motor)]))
            return
        if not dicttrue[str(status_motor)] == status:
            try:
                motor.write_attribute('PowerOn',dicton[status])
            except Exception, e:
                msg = ('It is not possible to change the state of the motors, '
                       'execute: ipap_reset_motor %s' % motorname)
                self.error(msg)
                raise

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
       kappa = self.getMoveable("kappa")
       eh=[
'analz','aperx','aperz','bpm6x','bpm6z','bpm5x','bpm5z','bstopx','bstopz',  'centx',  'centy',  'cryodist',  'dettabx',  'dettaby',  'dettabzb',  'dettabzf',  'diftabxb',  'diftabxf',  'diftabzb',  'diftabzf',  'fshuz',  'kappa',  'omega', 'omegaenc', 'omegax',  'omegay',  'omegaz',  'phi',  'zoommot', 's4hg',  's4vg', 's4ho', 's4vo', 'bsx', 'bsy', 'bsz', 'yagz'
              ]
       all = [
'analz','aperx','aperz','bpm3x','bpm3z','bpm4x','bpm4z','bpm5x','bpm5z','bpm6x','bpm6z','bstopx','bstopz',  'centx',  'centy',  'cryodist',  'dettabx',  'dettaby',  'dettabzb',  'dettabzf',  'diftabxb',  'diftabxf',  'diftabzb',  'diftabzf',  'feh1',  'feh2',  'fev1',  'fev2',  'foilb1',  'foilb2',  'foilb3',  'foilb4',  'fshuz',  'fsm2z',  'hfmbenb',  'hfmbenf',  'hfmpit',  'hfmx',  'hfmz',  'kappa',  'lamopit',  'lamoroll',  'lamox',  'lamoz',  'omega', 'omegaenc', 'omegax',  'omegay',  'omegaz',  'phi',  'pitang',  'pitstroke',  's1d',  's1l',  's1r',  's1u', 's2d',  's2u', 's3l',  's3r',  's4hg',  's4ho',  's4vg',  's4vo', 'bsx', 'bsy', 'bsz', 'theta',  'ugap',  'vfmbenb',  'vfmbenf',  'vfmpit',  'vfmroll',  'vfmx',  'vfmz',  'zoommot', 'yagz'
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
                test = status == 'ON' and kappa.getAttribute('StatusLimNeg').read().value and motorname in ['kappa','phi']  
                if test: 
                   self.warning('Cannot turn on the %s motor because the minikappa is not present' % motor) 
                else:
                   motor.write_attribute('PowerOn',dicton[status]) 
             final_status_motor = motor.getAttribute('PowerOn').read().value
             final_state = dicttrue[str(final_status_motor)] 
          except:
             self.error('error %s' % motorname)

class turn_motors_on(Macro):
    '''
           This macro is used to turn on all experimental hutch motors
    '''

    param_def = [
                  
                ]

    def run(self):
        self.info('turn_motors_on: Turning on all eh motors')
        self.execMacro('turnall eh on')
        time.sleep(2)
