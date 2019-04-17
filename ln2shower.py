from sardana.macroserver.macro import Macro, Type
import taurus
import PyTango
import time
from  bl13check import status

SHOWER_OPERATION_STRINGS = ['OFF','ON','Not a valid pump mode','PUMPING']

class ln2shower_wash(Macro):

    """
    This macro is used to switch on the ln2 shower.
    """

    param_def = [ 
                   [ 'washflow', Type.Float, 50, 'Ln2 pump wash flow']
                ]
   
    def run(self, washflow):
        self.shower_dev = taurus.Device('bl13/eh/ln2pump')
        self.epsf = taurus.Device('bl13/ct/eps-plc-01')        
        self.cats_dev = taurus.Device('bl13/eh/cats')

        if status.is_lima_running():
            raise Exception('LN2SHOWER_WASH ERROR: detector in collection state')

        if self.cats_dev['do_PRO5_IDL'].value != True:
            raise Exception('LN2SHOWER_WASH ERROR: CATS is not idle')
 
        self.info('LN2SHOWER_WASH: moving diffractometer to safe state')
        superdev = taurus.Device('bl13/eh/supervisor')
        superdev.gotransferphase()
        tries = 0
        maxtries = 300
        sleeptime = 0.2
        while superdev.currentphase.upper() != 'TRANSFER' and tries < maxtries:
            time.sleep(sleeptime)
            tries = tries + 1
           
        if tries >= maxtries: 
            self.error('LN2SHOWER_WASH ERROR: The ln2cover could not be closed')
            raise Exception('LN2SHOWER_WASH ERROR: The ln2cover could not be closed')
        
        
        self.info('LN2SHOWER_WASH: LN2 cover is closed')
        self.execMacro('ln2shower_on')
        self.execMacro('ln2shower_setflow %.1f' % washflow)
        self.info('LN2SHOWER_WASH: Succesfully set the pump flow...')
        

class ln2shower_cold(Macro):

    """
    This macro is used to keep cold the ln2 pump until next crystal shower.
    """

    param_def = [ 
                   [ 'coldflow', Type.Float, 2, 'Ln2 pump minimal flow to keep the line cold']
                ]
   

    def run(self, coldflow):
        self.shower_dev = taurus.Device('bl13/eh/ln2pump')
        
        self.info('LN2SHOWER_COLD: Keeping the pump cold using low flow...')
        
        self.execMacro('ln2shower_on')
        self.execMacro('ln2shower_setflow %.1f' % coldflow)
              
        self.info('LN2SHOWER_COLD: Pump flow successfully changed to cold flow.')
                
class ln2shower_setflow(Macro):
    
    param_def = [ 
                   [ 'setflow', Type.Float, 10, 'Ln2 pump wash flow']
                ]
   
    def run(self, setflow):
                
        self.shower_dev = taurus.Device('bl13/eh/ln2pump')
        operation = int(self.shower_dev['operation'].value)

        if operation == 3:
            self.shower_dev.getAttribute('flow').write(setflow) # set the flux of the shower to setflow
            tries = 1
            maxtries =300
            while float(self.shower_dev['flow'].value) <= setflow*0.9 or float(self.shower_dev['flow'].value) >= setflow*1.1:
                time.sleep(0.5)
                tries = tries + 1
                if tries > maxtries:
                    msg = 'LN2SHOWER_COLD ERROR: pump cannot reach desired flow of %.1f, current flow is %.1f' % (setflow, float(self.shower_dev['flow'].value))
                    self.error(msg)
                    raise Exception(msg)
        else:
            msg = 'LN2SHOWER_COLD ERROR: the pump could not be turned on'
            self.error(msg)
            raise Exception(msg)
        
                
class ln2shower_on(Macro):

    """
    This macro is used to turn the ln2 pump on (pumping operation mode 3)
    """

    param_def = [ 
                  
                ]

    def run(self):
        self.shower_dev = taurus.Device('bl13/eh/ln2pump')
        operation = int(self.shower_dev['operation'].value)
        self.info('LN2SHOWER_ON:Turning on the pump...')
        if operation == 3:
            self.warning('LN2SHOWER_ON: Pump is already on...')
        else: 
            try:
                self.shower_dev.getAttribute('operation').write(3) # set the shower in pump mode 
                tries = 1
                maxtries = 50
                while int(self.shower_dev['operation'].value) != 3:
                    time.sleep(0.5)
                    tries = tries + 1
                    if tries > maxtries:
                        msg = 'LN2SHOWER_WASH ERROR: the pump could not be turned on'
                        self.error(msg)
                        raise Exception(msg)
            except Exception('LN2SHOWER_WASH WARNING: The ln2shower cannot be operated '):
                msg = 'LN2SHOWER_WASH WARNING: The ln2shower cannot be operated '
                self.error(msg)                
        
        self.info('LN2SHOWER_ON: Succesfully turned on the pump...')

class ln2shower_off(Macro):

    """
    This macro is used to keep cold the ln2 pump until next crystal shower.
    """

    param_def = [ 
                  
                ]
   

    def run(self):
        self.shower_dev = taurus.Device('bl13/eh/ln2pump')
        operation = self.shower_dev['operation'].value
        
        self.info('LN2SHOWER:Turning off the pump...')

        if int(operation) == 3:
            self.shower_dev.getAttribute('operation').write(0) # Switch off the pump
        else:
            self.warning('LN2SHOWER WARNING: Pump is OFF (Pump mode=%d)'%int(operation))
            
        self.info('LN2SHOWER: Successfully turned off the pump...')
                   
                   
                   
                   
