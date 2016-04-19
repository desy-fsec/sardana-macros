from sardana.macroserver.macro import Macro, Type

class hooked_scan(Macro):
    """An example on how to attach hooks to the various hook points of a scan.
    This macro is part of the examples package. It was written for 
    demonstration purposes"""
    
    param_def = [
       ['motor',      Type.Motor,   None, 'Motor to move'],
       ['start_pos',  Type.Float,   None, 'Scan start position'],
       ['final_pos',  Type.Float,   None, 'Scan final position'],
       ['nr_interv',  Type.Integer, None, 'Number of scan intervals'],
       ['integ_time', Type.Float,   None, 'Integration time']
    ]
    def hook1(self):
        self.info("\thook1 execution")
    
    def hook2(self):
        self.info("\thook2 execution")
    
    def hook3(self):
        self.info("\thook3 execution")
    
    def run(self, motor, start_pos, final_pos, nr_interv, integ_time):
        ascan, pars = self.createMacro("ascan",motor, start_pos, final_pos, nr_interv, integ_time)
        ascan.hooks = [ (self.hook1, ["pre-acq"]), (self.hook2, ["pre-acq","post-acq","pre-move", "post-move","aaaa"]), self.hook3 ]
        self.runMacro(ascan)
