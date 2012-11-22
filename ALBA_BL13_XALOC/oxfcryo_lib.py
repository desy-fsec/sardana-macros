from sardana.macroserver.macro import Macro, Type
import taurus


# self.info() = output in blue    
# self.error() = output in red
# self.output() = output in black


class oxfcryo(Macro):
    '''
           Prints the variable status of the Oxford cryostream 
    '''
    def run(self):
       oxfcryo = taurus.Device('bl13/eh/oxfcryo')
       self.info('##########  BL13/EH/OXFCRYO  ##########'+"\n")
       varsvar = ['Alarm','ControllerNr','EvapAdjust','EvapHeat','EvapTemp','GasError','GasFlow','GasHeat', 'GasSetPoint', 'GasTemp', 'LinePressure', 'Phase', 'RampRate', 'RunMode', 'RunTime', 'SoftwareVersion', 'State', 'Status', 'SuctHeat', 'SuctTemp', 'TargetTemp']
       for var in varsvar:
          try:
             line=var+"="+str(oxfcryo[var].value)
          except:
             line=var+"=NAN"
          self.info(line) 







 
 










































































