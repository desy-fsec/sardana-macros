from sardana.macroserver.macro import Macro, Type
import time
import taurus

class get_oav_iba_beam(Macro):
    """Save fitted oav iba beam in bl13 variables"""
    
    def run(self):
        oav_iba = taurus.Device('bl13/eh/oav-01-iba')
        bl13vars = taurus.Device('bl13/ct/variables')
        
        if oav_iba.XProjFitConverged and oav_iba.YProjFitConverged:
            XProjFitCenter = oav_iba.XProjFitCenter
            YProjFitCenter = oav_iba.YProjFitCenter
            XProjFitFWHM = oav_iba.XProjFitFWHM
            YProjFitFWHM = oav_iba.YProjFitFWHM
            # Center should be relative to center not to the origin
            # Because changing zoom should not
        else:
            self.warning('beam not fitted')
