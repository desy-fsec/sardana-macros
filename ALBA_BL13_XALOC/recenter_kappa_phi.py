from sardana.macroserver.macro import Macro, Type
import taurus
import diffractometer

class recenter_kappa_phi(Macro):
    param_def = [ [ 'newkappa', Type.Float, 0, 'required value of kappa motor'],
                  [ 'newphi', Type.Float, 0, 'required value of phi motor']
                ]

    def run(self, newkappa, newphi):
        try:
            kappa = self.getMoveable('kappa').read_attribute('Position').value
            phi = self.getMoveable('phi').read_attribute('Position').value
            omegax = self.getMoveable('omegax').read_attribute('Position').value
            centy = self.getMoveable('centy').read_attribute('Position').value
            centx = self.getMoveable('centx').read_attribute('Position').value
        except:
            self.error('cant read values for kappa and phi motors')
            raise
        self.debug('kappa %f, phi %f' % (newkappa,newphi))
        newomegax, newcenty, newcentx = diffractometer.calc_newcenter_kappa_phi(newkappa,kappa,newphi,phi,omegax,centy,centx)
        self.debug('mv kappa %f phi %f omegax %f centy %f centx %f', newkappa,newphi,newomegax,newcenty,newcentx)
        self.execMacro('mv kappa %f phi %f omegax %f centy %f centx %f' % (newkappa,newphi,newomegax,newcenty,newcentx))
        return
    