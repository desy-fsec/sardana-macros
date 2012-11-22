from sardana.macroserver.macro import Macro, Type
import taurus

class turn(Macro):

    '''
           This macro is used to turn on/off a motor 
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
       status_motor = motor.getAttribute('PowerOn').read().value
       if status == 'STATUS': 
          self.info('%s is %s' % (motorname,dicttrue[str(status_motor)]))
          return
       if not dicttrue[str(status_motor)] == status:
          motor.write_attribute('PowerOn',dicton[status])
