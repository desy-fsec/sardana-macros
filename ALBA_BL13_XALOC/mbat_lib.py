from sardana.macroserver.macro import Macro, Type
import taurus
import time
from bl13constants import MBATFOILNAMES

MBAT_IN_OUT = {'IN': 1, 'OUT': 0}
LST_MBAT_12keV_15keV_OUT = ['AU']
LST_MBAT_6keV_10keV_OUT = ['FE','7AL','50AL','100AL']

class mbat_all_in(Macro):
    ''' inserts all mbat foils in the beam path, using the eps '''
    param_def = [ 
                ]
 
    def run(self):
        eps = taurus.Device('bl13/ct/eps-plc-01')
        for foil in MBATFOILNAMES:
            self.info('Inserting foil %s to IN' % MBATFOILNAMES[foil])
            eps[MBATFOILNAMES[foil]] = MBAT_IN_OUT['IN']
        #check if they are all in
        maxiter = 10
        niter = 0
        sleeptime = 1 #sec
        allfoilsin = False
        while not allfoilsin:
            allfoilsin = True
            for foil in MBATFOILNAMES:
                if eps[MBATFOILNAMES[foil]].value == MBAT_IN_OUT['OUT']:
                    self.info('foil %s is OUT' % MBATFOILNAMES[foil])
                    allfoilsin = False
                    break
            niter+=1
            if niter > maxiter:
                raise Exception('MACRO mbat_all_in: cant insert all foils')
            time.sleep(sleeptime)

class mbat_all_out(Macro):
    ''' inserts all mbat foils in the beam path, using the eps '''
    param_def = [ 
                ]
 
    def run(self):
        epsdev = taurus.Device('bl13/ct/eps-plc-01')
        for foil in MBATFOILNAMES:
            self.info('Removing foil %s to OUT' % MBATFOILNAMES[foil])
            epsdev[MBATFOILNAMES[foil]] = MBAT_IN_OUT['OUT']
        #check if they are all in
        maxiter = 10
        niter = 0
        sleeptime = 1 #sec
        allfoilsout = False
        while not allfoilsout:
            allfoilsout = True
            for foil in MBATFOILNAMES:
                if epsdev[MBATFOILNAMES[foil]].value == MBAT_IN_OUT['IN']:
                    self.info('foil %s is IN' % MBATFOILNAMES[foil])
                    allfoilsout = False
                    break
            niter+=1
            if niter > maxiter:
                raise Exception('MACRO mbat_all_out: cant remove all foils')
            time.sleep(sleeptime)

class mbat_beam_size(Macro):
    ''' inserts all mbat foils in the beam path, using the eps '''
    param_def = [ 
                ]
 
    def run(self):
        E  = self.getMoveable('E')
        lst_mbat_out = []
        try: 
            self.execMacro('mbat_all_in')
        except:
            self.error('mbat_beam_size ERROR: Couldnt remove all foils')
            pass
        currentE = E.getPosition()
        if currentE > 4.7 and currentE < 6:
            lst_mbat_out = LST_MBAT_6keV_10keV_OUT
        if currentE >= 6 and currentE < 10:
            lst_mbat_out = LST_MBAT_6keV_10keV_OUT
        if currentE >= 10 and currentE < 12:
            lst_mbat_out = LST_MBAT_12keV_15keV_OUT
        if currentE >= 12 and currentE < 15:
            lst_mbat_out = LST_MBAT_12keV_15keV_OUT
        if currentE >= 15 and currentE < 22:
            lst_mbat_out = LST_MBAT_12keV_15keV_OUT
        self.info('mbat_beam_size INFO: removing foils %s' % lst_mbat_out)
        epsdev = taurus.Device('bl13/ct/eps-plc-01')
        for foilname in lst_mbat_out:
            epsdev[MBATFOILNAMES[foilname]] = MBAT_IN_OUT['OUT']
        niter = 0
        maxiter = 10
        allfoilsout = False
        sleeptime = 1 #sec
        while not allfoilsout:
            allfoilsout = True
            for foil in lst_mbat_out:
                 if not epsdev[MBATFOILNAMES[foil]].value == MBAT_IN_OUT['OUT']:
                     allfoilsout = False
                     break
            niter+=1
            if niter > maxiter:
                raise Exception('MACRO mbat_all_out: cant remove all foils')
            time.sleep(sleeptime)
        return 1                