from sardana.macroserver.macro import Macro, Type
import taurus
from datetime import *
import PyTango
from bl13constants import MBATFOILNAMES

# self.info() = output in blue    
# self.error() = output in red
# self.output() = output in black


class blmemo(Macro):
    '''
           To save the state of the beamline in /beamlines/bl13/commissioning/blmemo/*.blmemo
           blmemo -> will save a file with today's dayte and extension .blemo
           blmemo name -> will save a file called name.blmemo
           special mode NOMAC avoids checking FE real motors and UGAP that give problems when there is a shutdown
           default MODE is all
    '''
    param_def = [ 
                  [ 'name', Type.String, '', 'filename'],
                  [ 'mode', Type.String, '', '']
                ]
    def run(self,name,mode):

        # set mode uppercase
        mode = mode.upper()
        
        # define list of motors to query
        motors = [ 
'analz','aperx','aperz','bpm3x','bpm3z','bpm4x','bpm4z','bpm5x','bpm5z','bpm6x','bpm6z','bpmfex','bpmfez','bstopx','bstopz',  'centx',  'centy',  'cryodist',  'dettabpit',  'dettabx',  'dettaby',  'dettabz',  'dettabzb',  'dettabzf',  'diftabpit',  'diftabx',  'diftabxb',  'diftabxf',  'diftabyaw',  'diftabz',  'diftabzb',  'diftabzf',  'dmot1',  'dmot2',  'dmot3',  'dmot4',  'dmot5',  'E',  'feh1',  'feh2',  'fehg',  'feho',  'fev1',  'fev2',  'fevg',  'fevo',  'foilb1',  'foilb2',  'foilb3',  'foilb4',  'fshuz',  'fsm2z',  'hfmq', 'hfmde3','hfmbenb',  'hfmbenf',  'hfmpit',  'hfmx',  'hfmz',  'holderlength',  'kappa',  'lamopit',  'lamoroll',  'lamox',  'lamoz',  'omega', 'omegaenc', 'omegax',  'omegay',  'omegaz',  'phi',  'pitang',  'pitstroke',  's1d',  's1hg',  's1ho',  's1l',  's1r',  's1u',  's1vg',  's1vo',  's2d',  's2u',  's2vg',  's2vo',  's3hg',  's3ho',  's3l',  's3r',  's4hg',  's4ho',  's4vg',  's4vo',  'theta',  'ugap',  'vfmbenb',  'vfmbenf',  'vfmbenfb',  'vfmbenff',  'vfmDE3',  'vfmpit',  'vfmq',  'vfmroll',  'vfmx',  'vfmz',  'zoommot', 'mbattrans',  'bsx',  'bsy',  'bsz',  'yagy',  'yagz'
              ] 

        # define list of motors minus those from the machine
        if mode == 'NOMAC': motors = [
'analz','aperx','aperz','bpm3x','bpm3z','bpm4x','bpm4z','bpm5x','bpm5z','bpm6x','bpm6z','bstopx','bstopz',  'centx',  'centy',  'cryodist',  'dettabpit',  'dettabx',  'dettaby',  'dettabz',  'dettabzb',  'dettabzf',  'diftabpit',  'diftabx',  'diftabxb',  'diftabxf',  'diftabyaw',  'diftabz',  'diftabzb',  'diftabzf',  'dmot1',  'dmot2',  'dmot3',  'dmot4',  'dmot5',  'E',  'fehg',  'feho',  'fevg',  'fevo',  'foilb1',  'foilb2',  'foilb3',  'foilb4',  'fshuz',  'fsm2z',  'hfmq', 'hfmde3','hfmbenb',  'hfmbenf',  'hfmpit',  'hfmx',  'hfmz',  'holderlength',  'kappa',  'lamopit',  'lamoroll',  'lamox',  'lamoz',  'omega', 'omegaenc', 'omegax',  'omegay',  'omegaz',  'phi',  'pitang',  'pitstroke',  's1d',  's1hg',  's1ho',  's1l',  's1r',  's1u',  's1vg',  's1vo',  's2d',  's2u',  's2vg',  's2vo',  's3hg',  's3ho',  's3l',  's3r',  's4hg',  's4ho',  's4vg',  's4vo',  'theta',  'vfmbenb',  'vfmbenf',  'vfmbenfb',  'vfmbenff',  'vfmDE3',  'vfmpit',  'vfmq',  'vfmroll',  'vfmx',  'vfmz',  'zoommot', 'mbattrans',  'bsx',  'bsy',  'bsz',  'yagy',  'yagz'
              ] 

        # define dir where blmemos are placed
        dir = "/beamlines/bl13/commissioning/blmemo/"
        if name == '': 
           self.error('Please write a filename')
           return
        cfilename = dir+name+".blmemo"

        # open file
        FILE = open(cfilename,"w")

        # write motor values
        FILE.writelines('##########  MOTOR POSITIONS  #########'+"\n")
        self.info('##########  MOTOR POSITIONS  ##########'+"\n")
        for motor in motors:
           self.info(motor)
           try:
              motor_dev = PyTango.DeviceProxy(motor)
              attributes = motor_dev.get_attribute_list()
              for attr in attributes:
                 try:
                    attr_value = motor_dev.read_attribute(attr).value
                    #self.info('%s.%s = %s' % (motor, attr, attr_value))
                    line=motor+"."+attr+" = "+repr(attr_value)+"\n"
                 except:
                    line=motor+"."+attr+" = ERROR"+"\n" 
                 FILE.writelines(line)
           except:
              self.error('error %s' % motor)

        # define devices
        oxfcryo = taurus.Device('bl13/eh/oxfcryo')
        eps = taurus.Device('bl13/ct/eps-plc-01')
        vars = taurus.Device('bl13/ct/variables')

        # write status of important actuators
        FILE.writelines('##########  IMPORTANT ACTUATORS  #########'+"\n")
        self.info('##########  IMPORTANT ACTUATORS  ##########'+"\n")
        #dictf={'7AL':'mbat16','14AL':'mbat15','25AL':'mbat14','50AL':'mbat13',
        #       '100AL':'mbat12','200AL':'mbat11','500AL':'mbat26','FE':'mbat25',
        #       'NI':'mbat24','ZN':'mbat23','AU':'mbat22','ZR':'mbat21'}
        #list_foils = ['7AL', '14AL','25AL','50AL','100AL','200AL','500AL','FE','NI','ZN','AU','ZR']
        dictf=MBATFOILNAMES
        list_foils = MBATFOILNAMES.keys()
        dicts={0:'out',1:'in'}
        for mbat in list_foils:
            self.info(mbat)
            try: 
                line=mbat+" is "+dicts[eps[dictf[mbat]].value]+"\n"
            except:
                line=mbat+" is in unknown state"
            FILE.writelines(line) 
        actuators = ['fe_open', 'pshu','slowshu', 'ln2cover','detcover']
        dicts2={1:'out',0:'in'}
        for pneu in actuators:
            self.info(pneu)
            try:
                line=pneu+" is "+dicts2[eps[pneu].value]+"\n"
            except:
                line=pneu+" is in unknown state"
            FILE.writelines(line)

        # write status of EPS variables
        FILE.writelines('##########  EPS VARIABLES  ##########'+"\n")
        self.info('##########  EPS VARIABLES  ##########'+"\n")
        epsvar = list(eps['AttributeList'].value) 
        for var in epsvar: 
           self.info(var)
           try:
               var_value = eps[var].value
               line=var+"="+repr(eps[var].value)+"\n"
           except:      
               line=var+"=NAN"+"\n"
           FILE.writelines(line) 

        # write values of bl13/ct/variables
        FILE.writelines('##########  BL13/CT/VARIABLES  ##########'+"\n")
        self.info('##########  BL13/CT/VARIABLES  ##########'+"\n")
        varsvar = ['beamx','beamxa','beamxb','beamy','beamya','beamyb','detsamdis','detsamdisa','deltadiftabx','deltadiftabz','detsamdisb','MachineCurrent','oav_pixelsize_x','oav_pixelsize_y','pinlength','totalroicountsfluo','totalroicountsratio','totalroicountsscat','update_pixelsize_x','update_pixelsize_y','xprojfitcenterfromcenter','xprojfitfwhm','yprojfitcenterfromcenter','yprojfitfwhm','fluxlasttime','fluxlast','fluxlastnorm','robotcurrcom','OAV_OAI_X','OAV_OAI_Y','usetaurus','DivPerPix']
        for var in varsvar:
           self.info(var)
           try:
               var_value = vars[var].value
               line=var+"="+repr(vars[var].value)+"\n"
           except:
               line=var+"=NAN"+"\n"
           FILE.writelines(line)

        # write variables of oxfcryo
        FILE.writelines('##########  BL13/EH/OXFCRYO  ##########'+"\n")
        self.info('##########  BL13/EH/OXFCRYO  ##########'+"\n")
        varsvar = ['Alarm','ControllerNr','EvapAdjust','EvapHeat','EvapTemp','GasError','GasFlow','GasHeat', 'GasSetPoint', 'GasTemp', 'LinePressure', 'Phase', 'RampRate', 'RunMode', 'RunTime', 'SoftwareVersion', 'State', 'Status', 'SuctHeat', 'SuctTemp', 'TargetTemp']
        for var in varsvar:
           self.info(var)
           try:
               #self.info(oxfcryo[var].value)
               #self.info(var_value)
               line=var+"="+str(oxfcryo[var].value)+"\n"
           except:
               line=var+"=NAN"+"\n"
           FILE.writelines(line)



        # CLOSE FILE
        FILE.close()




 
 










































































