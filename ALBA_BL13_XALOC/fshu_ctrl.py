from sardana.macroserver.macro import Macro
import taurus

# self.info() = output in blue    
# self.error() = output in red
# self.output() = output in black


class fshu_open(Macro):
    def run(self):
        dio7300 = taurus.Device('bl13/ct/dio7300-01')
        #dio7300.Output([1,1])
        dio7300.command_inout('Output', [1,1])

class fshu_close(Macro):
    def run(self):
        dio7300 = taurus.Device('bl13/ct/dio7300-01')
        dio7300.Stop()


