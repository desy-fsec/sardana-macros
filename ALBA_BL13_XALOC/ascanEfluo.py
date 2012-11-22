from sardana.macroserver.macro import Macro, Type
import matplotlib.pyplot as plt
import taurus
from FluoDet import *
#import PyTango

class ascanEfluo(Macro):
    """
    ascan Eugap with fluodetector counting
    
    An example on how to attach hooks to the various hook points of a scan.
    This macro is part of the examples package. It was written for 
    demonstration purposes"""

    param_def = [
       ['motor',      Type.Motor,   None, 'Motor to scan'],
       ['start_pos',  Type.Float,   None, 'Scan start position'],
       ['final_pos',  Type.Float,   None, 'Scan final position'],
       ['nr_interv',  Type.Integer, None, 'Number of scan intervals'],
       ['integ_time', Type.Float,   None, 'Integration time'],
       ['start_channel', Type.Integer,   None, 'Start Channel for ROI'],
       ['step_width', Type.Integer,   None, 'Fluo detector number of channels step in each count'],
       ['summation_width', Type.Integer,   None, 'Fluo detector summation binning in each step'],
    ]
    
    #def hook1(self,start_channel,step_width,summation_width, max_data=2):
    def hook1(self):
        
#        self.info("\treading fluorescence detector")
        var = taurus.Device('bl13/ct/variables')
        FluoCounts = var.getAttribute('TotalROIcountsFluo')
        ScatCounts = var.getAttribute('TotalROIcountsScat')
        RatioCounts = var.getAttribute('TotalROIcountsRatio')
        counting = GetFluoCounts(self.start_channel,self.step_width,self.summation_width,self.integ_time,self.max_data)
#        self.info("counting: %s" % repr(counting))
        FluoCounts.write(counting[0])
        ScatCounts.write(counting[1])
        if counting[1]>0.: #instead of FluoCounts.read().value
            RatioCounts.write(float(counting[0])/counting[1])
        else:
            RatioCounts.write(0.)
        
        Echannel,counts = GetFluoSpectrum()
        #plt.plot(Echannel,counts)
        #plt.show()

                
   
    def run(self, motor, start_pos, final_pos, nr_interv, integ_time, start_channel, step_width, summation_width):
        #motor = taurus.Device('dmot1')
        var = taurus.Device('bl13/ct/variables')
        self.info("before createMacro")
	#self.info("motor: %s" % repr(motor))
        self.start_channel = start_channel
        self.step_width = step_width
        self.summation_width = summation_width
        self.max_data = 2
        self.integ_time = int(integ_time*1000) # in msec
        ascan, pars = self.createMacro("ascan", motor, start_pos, final_pos, nr_interv, .01)
        self.info('create macro results: %s, %s' % (repr(ascan), repr(pars)))
        #ascan.hooks = [ (self.hook1(start_channel,step_width,summation_width,2), ["pre-acq"])]
        ascan.hooks = [ (self.hook1, ["pre-acq"])]
#        ascan.hooks = [ (self.hook1, ["pre-acq"]), (self.hook2, ["pre-acq","post-acq","pre-move", "post-move","aaaa"]), self.hook3 ]
        self.runMacro(ascan)
