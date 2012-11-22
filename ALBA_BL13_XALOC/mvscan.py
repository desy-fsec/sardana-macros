from sardana.macroserver.macro import Macro, Type
import taurus, time

# self.info() = output in blue    
# self.error() = output in red
# self.output() = output in black




class mvscan(Macro):
    '''test de focusing'''
    param_def = [ [ 'axis', Type.String, '', 'motor'],
                  [ 'initpos', Type.Float, None, 'initial value'],
                  [ 'finalpos', Type.Float, None, 'final value'],
                  [ 'npoints', Type.Float, None, 'num of points in scan'],
                  [ 'waittime', Type.Float, 0.0, 'wait time per point']
                ]

    def run(self, axis, initpos, finalpos, npoints, waittime):
        oav = taurus.Device('bl13/eh/oav-01-iba')
        motor1 = taurus.Device(axis)
        ct1 = oav.chamberxprojfitcenter
        ct2 = oav.xprojfitsigma
        ct3 = oav.Chamberyprojfitcenter
        ct4 = oav.yprojfitsigma
        deltamov = (finalpos - initpos)/npoints
        for iter in range(0,npoints+1):
            pos = initpos +  iter*deltamov
            mv_cmd = 'mv %s %f' % (axis, pos)
            self.execMacro(mv_cmd)
            time.sleep(waittime)
            self.output('%f %f %f %f %f' %(motor1.position, ct1, ct2, ct3, ct4))



class mv2scan(Macro):
    '''test de focusing'''
    param_def = [ [ 'axis1', Type.Motor, '', 'motor1'],
                  [ 'initpos1', Type.Float, None, 'initial value'],
                  [ 'finalpos1', Type.Float, None, 'final value'],
                  [ 'axis2', Type.Motor, '', 'motor1'],
                  [ 'initpos2', Type.Float, None, 'initial value'],
                  [ 'finalpos2', Type.Float, None, 'final value'],
                  [ 'npoints', Type.Float, None, 'num of points in scan'],
                  [ 'waittime', Type.Float, 0.0, 'wait time per point']
                ]
    def run(self, axis1, initpos1, finalpos1, axis2, initpos2, finalpos2, npoints, waittime):
        oav = taurus.Device('bl13/eh/oav-01-iba')
        #motor1 = taurus.Device(axis1)
        #motor2 = taurus.Device(axis2)
        axis1_name = axis1.getName()
        axis2_name = axis2.getName()
        vfmDE3 = taurus.Device("vfmDE3")
        deltamov1 = (finalpos1 - initpos1)/npoints
        deltamov2 = (finalpos2 - initpos2)/npoints
        self.output('%s %s %f %f %f %f' %(axis1_name, axis2_name, initpos1, initpos2, finalpos1, finalpos2))
        for iter in range(0,npoints+1):
            pos1 = initpos1 +  iter*deltamov1
            pos2 = initpos2 +  iter*deltamov2
            axis1.move([pos1])
            axis2.move([pos2])
            #if (axis1_name == 'vfmq' or axis1_name == 'vfmq') and abs(vfmDE3.position)>0.05:
            vfmDE3.move([0.])
#       self.output('%f' %(vfmDE3.position))
#       mv_cmd1 = 'mv %s %f' % (axis1.getName(), pos1)
#       mv_cmd2 = 'mv %s %f' % (axis2.getName(), pos2)
#       self.execMacro(mv_cmd1)
#       self.execMacro(mv_cmd2)
            time.sleep(waittime)
            ct1 = oav.chamberxprojfitcenter
            ct2 = oav.xprojfitsigma
            ct3 = oav.Chamberyprojfitcenter
            ct4 = oav.yprojfitsigma
            self.output('%i %f %f %f %f %f %f' %(iter, axis1.position, axis2.position, ct1, ct2, ct3, ct4))











