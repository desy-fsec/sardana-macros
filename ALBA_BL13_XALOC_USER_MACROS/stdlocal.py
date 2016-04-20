from sardana.macroserver.macro import Macro, Type, Hookable
import taurus
FEAUTO_ATTR = "BL13/CT/EPS-PLC-01/FE_AUTO"
FE_PSS_PERMIT = "alba03:10000/expchan/id13ivu_machine_attributes/8/value"

class feauto(Macro):
    """This macro enables or disables the Front End Automatic opening mode"""

    param_def = [
       ['state', Type.String, '', '1/0 Yes/No' ]
    ]

    def run(self,state):
        _attr = taurus.Attribute(FEAUTO_ATTR)
        if state == '':
            self.output("FE Automatic mode is %d." % _attr.read().value)
        elif state == '1' or state.upper() == "YES":
            _attr.write(1)
            self.output("FE Automatic mode is  set to %d." % _attr.read().value)
        elif state == '0' or state.upper() == "NO":
            _attr.write(0)
            self.output("FE Automatic mode is set to %d." % _attr.read().value)
        else:
            self.output("Error. FE state not valid. disabling")
            _attr.write(0)

class fepss(Macro):

    """This macro checks the permits of the PSS from the Machine to open the FE"""

    def run(self):
        _attr = taurus.Attribute(FE_PSS_PERMIT)
        self.output("FE PERMIT FROM THE PSS is %d." % _attr.read().value)


