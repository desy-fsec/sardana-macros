from sardana.macroserver.macro import Macro, Type
import taurus
from datetime import *
import time
import PyTango
import diagnostics
import numpy


# self.info() = output in blue    
# self.error() = output in red
# self.output() = output in black


class vfm_mono_calibration4(Macro):
    '''
           To find the vfm vertical change due to mono Energy change
    '''
    param_def = [ 
                  [ 'name', Type.String, '', 'filename'],
                  [ 'E_start', Type.Float, 12, 'Initial Energy to calibrate'],
                  [ 'E_end', Type.Float, 13, 'Final Energy to calibrate']
                ]
    def run(self,name, E_start, E_end):
        

        bpm3 = taurus.Device('bl13/di/emet-03-bpm03')
        bpm4 = taurus.Device('bl13/di/emet-04-bpm04')
        
        dir = "/beamlines/bl13/commissioning/20120609/"
        if name == '': 
           self.error('Please write a filename')
           return
        cfilename = dir+name+".csv"
        FILE = open(cfilename,"w")
        FILE.writelines('#E,b3x,b3z,b4x,b4z\n')
        
        Epoints = numpy.linspace(E_start,E_end,1+max(10,(E_end-E_start)/0.1))
        for Energy in Epoints:
            moveEugap = 'umv Eugap '+str(Energy)
            self.execMacro(moveEugap)
            time.sleep(.5)
            b3xa=[]
            b3za=[]
            b4xa=[]
            b4za=[]
            for i in range(10):
                try:
                    b3zpos = diagnostics.b3z_calibration((bpm3.ib3u-bpm3.ib3d)/(bpm3.ib3u+bpm3.ib3d))
                    b3zpos = str(b3zpos)
                    b3za.append(b3zpos)
                except:
                    b3zpos = ' '
                try:
                    b3xpos = diagnostics.b3x_calibration((bpm3.ib3r-bpm3.ib3l)/(bpm3.ib3r+bpm3.ib3l))
                    b3xpos = str(b3xpos)
                    b3xa.append(b3xpos)
                except:
                    b3xpos = ' '
                try:
                    b4zpos = diagnostics.b4z_calibration((bpm4.ib4u-bpm4.ib4d)/(bpm4.ib4u+bpm4.ib4d))
                    b4zpos = str(b4zpos)
                    b4za.append(b4zpos)
                except:
                    b4zpos = ' '
                try:
                    b4xpos = diagnostics.b4x_calibration((bpm4.ib4r-bpm4.ib4l)/(bpm4.ib4r+bpm4.ib4l))
                    b4xpos = str(b4xpos)
                    b4xa.append(b4xpos)
                except:
                    b4xpos = ' '
            
                line = str(Energy)+','+b3xpos+','+b3zpos+','+b4xpos+','+b4zpos+'\n'

#            self.info(str(Energy)+str(b3xa)+str(b3za)+str(b4xa)+str(b4za))
            FILE.writelines(line)
        
        FILE.close()



        #motors = [ 
#'analz','aperx','aperz','bpm3x','bpm3z','bpm4x','bpm4z','bpm6x','bpm6z','bpmfex','bpmfez','bstopx','bstopz',  'centx',  'centy',  'cryodist',  'dettabpit',  'dettabx',  'dettaby',  'dettabz',  'dettabzb',  'dettabzf',  'diftabpit',  'diftabx',  'diftabxb',  'diftabxf',  'diftabyaw',  'diftabz',  'diftabzb',  'diftabzf',  'dmot1',  'dmot2',  'dmot3',  'dmot4',  'dmot5',  'E',  'feh1',  'feh2',  'fehg',  'feho',  'fev1',  'fev2',  'fevg',  'fevo',  'foilb1',  'foilb2',  'foilb3',  'foilb4',  'fshuz',  'fsm2z',  'hfmbenb',  'hfmbenf',  'hfmpit',  'hfmx',  'hfmz',  'holderlength',  'kappa',  'lamopit',  'lamoroll',  'lamox',  'lamoz',  'omega', 'omegaenc', 'omegax',  'omegay',  'omegaz',  'phi',  'pitang',  'pitstroke',  's1d',  's1hg',  's1ho',  's1l',  's1r',  's1u',  's1vg',  's1vo',  's2d',  's2u',  's2vg',  's2vo',  's3hg',  's3ho',  's3l',  's3r',  's4hg',  's4ho',  's4vg',  's4vo',  'theta',  'ugap',  'vfmbenb',  'vfmbenf',  'vfmbenfb',  'vfmbenff',  'vfmDE3',  'vfmpit',  'vfmq',  'vfmroll',  'vfmx',  'vfmz',  'zoommot'
              #] 
        #dir = "/beamlines/bl13/commissioning/20120609/"
        #if name == '': 
           #self.error('Please write a filename')
           #return
        #cfilename = dir+name+".csv"
        #FILE = open(cfilename,"w")
        #FILE.writelines('##########  MOTOR POSITIONS  #########'+"\n")
        #for motor in motors:
           #self.info(motor)
           #motor_dev = PyTango.DeviceProxy(motor)
           #attributes = motor_dev.get_attribute_list()
           #for attr in attributes:
              #try:
                 #attr_value = motor_dev.read_attribute(attr).value
                 ##self.info('%s.%s = %s' % (motor, attr, attr_value))
                 #line=motor+"."+attr+" = "+repr(attr_value)+"\n"
              #except:
                 #line=motor+"."+attr+" = ERROR"+"\n" 
              #FILE.writelines(line)

        #eps = taurus.Device('bl13/ct/eps-plc-01')
        #FILE.writelines('##########  IMPORTANT ACTUATORS  #########'+"\n")
        #dictf={'7AL':'mbat16','14AL':'mbat15','25AL':'mbat14','50AL':'mbat13',
               #'100AL':'mbat12','200AL':'mbat11','500AL':'mbat26','FE':'mbat25',
               #'NI':'mbat24','ZN':'mbat23','AU':'mbat22','ZR':'mbat21'}
        #list_foils = ['7AL', '14AL','25AL','50AL','100AL','200AL','500AL','FE','NI','ZN','AU','ZR']
        #dicts={0:'out',1:'in'}
        #for mbat in list_foils:
            #self.info(mbat)
            #try: 
                #line=mbat+" is "+dicts[eps[dictf[mbat]].value]+"\n"
            #except:
                #line=mbat+" is in unknown state"
            #FILE.writelines(line) 
        #actuators = ['fe_open', 'pshu','slowshu']
        #dicts2={1:'out',0:'in'}
        #for pneu in actuators:
            #self.info(pneu)
            #try:
                #line=pneu+" is "+dicts2[eps[pneu].value]+"\n"
            #except:
                #line=pneu+" is in unknown state"
            #FILE.writelines(line)

        #FILE.writelines('##########  EPS VARIABLES  ##########'+"\n")
        #epsvar = list(eps['AttributeList'].value) 
        #for var in epsvar: 
           #self.info(var)
           #try:
               #var_value = eps[var].value
               #line=var+"="+repr(eps[var].value)+"\n"
           #except:      
               #line=var+"=NAN"+"\n"
           #FILE.writelines(line) 
        #FILE.close()


 
 










































































