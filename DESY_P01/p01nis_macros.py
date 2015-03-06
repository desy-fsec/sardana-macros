"""
    Macro library containning scan related macros
"""

import time

from sardana.macroserver.macro import *

import PyTango

class _nisscan(Macro):
    """ Base class for NIS scan """

    param_def = [
        ['start',      Type.Float,   None, 'Start in meV'],
        ['stop',       Type.Float,   None, 'Stop in meV'],
        ['nr_interv',  Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float,   None, 'Integration time'],
        ['nb_scans',   Type.Integer, None, 'Nb of scans'],
        ['eh_id',      Type.Integer, 0, '1 -> eh1, 2 -> eh2, 3 -> eh3. If 0 read from EH_ID environment']
        ]    

    def prepare(self,  start, stop, nr_interv, integ_time, nb_scans, eh_id):
        self.prepared = False

        # Set mg_nis to the active one
        self.senv("ActiveMntGrp", "mg_nis")

        # Conversion to position
        self.motor_name = "oh2_1064th"
        self.motor = self.getMotor(self.motor_name)
        self.pos =  self.motor.getPosition()
        conversion = 51790
        self.start_pos = self.pos + start / conversion
        self.stop_pos  = self.pos + stop  / conversion
        
        self.prepared = True

    def check_petracurrent_ic1counts(self):

        flag_check_petra_ic1 = True

        # Check Petra Current:
        petra_device = PyTango.DeviceProxy("petra/globals/keyword")
        petra_current = petra_device.BeamCurrent
                
        if petra_current > 30:
            self.info("PETRA above 30 mA, macro continues")
            check_current = 0
        else:
            self.info("PETRA below 30 mA, macro waits 5 minutes")
            time.sleep(300)
            check_current = 1
                
        # Check IC1
        try:
            mg_ic1 = self.getMeasurementGroup("mg_ic1")
            mg_ic1.write_attribute("IntegrationTime",0.1)
        except:
            self.output("Error from mg_ic1 measurement group. Check if it is defined")
            return
            
        mg_ic1.Start()

        counter_ic1 = self.getCounterTimer("exp_c02")
        
        while mg_ic1.State() == PyTango.DevState.MOVING:
            time.sleep(0.001)
                
        counts_ic1 = counter_ic1.Value

        if counts_ic1 > 10:
            self.info("IC1 above 10, macro continues")
            check_ic1 = 0
        else:
            self.info("IC1 below 10, macro waits 5 s")
            time.sleep(5)
            check_ic1 = 1

        if check_current == 0 and check_ic1 == 0:
            flag_check_petra_ic1 = False

        return flag_check_petra_ic1

    def optimize_motor(self, motor_name, counter_name, mg_name, scan_range, nr_interv, int_time, function):
        
        self.info("Optimizing %s" % motor_name)
        self.senv("ActiveMntGrp", mg_name)  
        motor = self.getMotor(motor_name)
        pos =  motor.getPosition()
        
        self.execMacro('make_scan', motor_name, pos, pos + scan_range, nr_interv, int_time)
        
        self.execMacro('ana_func', counter_name, function)
        


class nisscan(_nisscan):
    """NIS scan (eh2, for eh3 change exp_c02 to exp_c03 in counter_ec1 and change mg_nis) """ 

    param_def = [
        ['start',      Type.Float,   None, 'Start in meV'],
        ['stop',       Type.Float,   None, 'Stop in meV'],
        ['nr_interv',  Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float,   None, 'Integration time'],
        ['nb_scans',   Type.Integer, None, 'Nb of scans'],
        ['eh_id',      Type.Integer, 0, '1 -> eh1, 2 -> eh2, 3 -> eh3. If 0 read from EH_ID environment']
        ]    


    def run(self, start, stop, nr_interv, integ_time, nb_scans, eh_id):
        if not self.prepared:
            return

        self.info("Starting NIS scan")
        self.info("from %f eV oh2_1064th %f" % (start, self.start_pos))
        self.info("to   %f eV oh2_1064th %f" % (stop, self.stop_pos))
        self.info( "%d points", nr_interv ); 
        self.info( "sample time %f seconds", integ_time); 
        self.info( "number of scans %d", nb_scans); 
        self.info( "starting  point %f", self.pos); 
        

        for i in range(0, nb_scans):
            self.info("Scan %d from %d " % (i+1, nb_scans))
            
            flag_check_petra_ic1 = True

            while flag_check_petra_ic1:
                flag_check_petra_ic1 = _nisscan.check_petracurrent_ic1counts(self)

            self.execMacro('ascan', self.motor_name, self.start_pos, self.stop_pos, nr_interv, integ_time)


class nislong(_nisscan):
    """NIS scan (eh2, for eh3 change limits for petracurrent and counters) """ 

    param_def = [
        ['start',      Type.Float,   None, 'Start in meV'],
        ['stop',       Type.Float,   None, 'Stop in meV'],
        ['nr_interv',  Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float,   None, 'Integration time'],
        ['nb_scans',   Type.Integer, None, 'Nb of scans'],
        ['eh_id',      Type.Integer, 0, '1 -> eh1, 2 -> eh2, 3 -> eh3. If 0 read from EH_ID environment']
        ]   
    
    def run(self, start, stop, nr_interv, integ_time, nb_scans, eh_id):
        if not self.prepared:
            return

        self.info("Starting NIS scan")
        self.info("from %f eV oh2_1064th %f" % (start, self.start_pos))
        self.info("to   %f eV oh2_1064th %f" % (stop, self.stop_pos))
        self.info( "%d points", nr_interv ); 
        self.info( "sample time %f seconds", integ_time); 
        self.info( "number of scans %d", nb_scans); 
        self.info( "starting  point %f", self.pos); 
        
        for i in range(0, nb_scans):
            self.info("Scan %d from %d " % (i+1, nb_scans))
            
            flag_check_petra_ic1 = True
            second_check = True
            third_check = True


            while third_check:
                while second_check:
                    while flag_check_petra_ic1:
                        flag_check_petra_ic1 = _nisscan.check_petracurrent_ic1counts(self)

                    self.execMacro('ascan', self.motor_name, self.start_pos, self.stop_pos, nr_interv, integ_time)

                    second_check = _nisscan.check_petracurrent_ic1counts(self)
                
                    if not second_check:
                        _nisscan.optimize_motor(self, "dcm_pitch", "exp_c02", "mg_optpitch", 0.002, 50, 0.1, "peak")
                        _nisscan.optimize_motor(self, "oh2_1064th", "nisd_eh1", "mg_opt1064", 0.0005, 50, 0.5, "peak")
                        
                        third_check = _nisscan.check_petracurrent_ic1counts(self)

                        if not third_check:
                            _nisscan.optimize_motor(self, "piezo_th2", "exp_c03", "mg_opt1064", 1600, 40, 0.5, "cms")
                            _nisscan.optimize_motor(self, "oh2_400th", "exp_c03", "mg_opt400", 0.004, 60, 0.2, "cms")
                            if eh_id == 1:
                                counter_name = "nisd_eh1"
                            elif eh_id == 3:
                                counter_name = "eh3_c02nisd"
                            _nisscan.optimize_motor(self, "oh2_1064th", counter_name, "mg_opt1064", 0.0005, 50, 0.5, "peak")
                            
                    

class nis_create_mgs(Macro):
    """Create measurement groups for nis scans """
    
    param_def = [
        ['eh_id',      Type.Integer, 0, '1 -> eh1, 2 -> eh2, 3 -> eh3. If 0 read from EH_ID environment']
        ]   

    def run(self, eh_id):

        self.output("Creating mg_ic1")

        pools = self.getPools()
        pool = pools[0]

        args = []
        args.append("mg_ic1")
        args.append("exp_t01")
        args.append("exp_c02")

        if eh_id == 0:
            eh_id = self.getEnv("EH_ID")

        try:
            pool.CreateMeasurementGroup(args)
        except:
            self.warning("Error creating mg_ic1 measurement group. Check if it already exits")

        self.output("Creating mg_nis")

        args = []
        args.append("mg_nis")
        args.append("exp_t01")
        args.append("exp_c02")
        args.append("exp_c03")
        args.append("ipetra")
        args.append("vc10")
        args.append("vc36")
        if eh_id == 1:
            args.append("exp_c09nfsp")
            args.append("exp_c10nfsd")
            args.append("nisp_eh1")
            args.append("nisd_eh1")
        elif eh_id == 3:
            args.append("eh3_c03nfsp")
            args.append("eh3_c04nfsd")
            args.append("eh3_c06_exp_c02")
            args.append("eh3_c01nisp")
            args.append("eh3_c02nisd")
            args.append("eh3_c17_nisp1")
            args.append("eh3_c18_nisd1")
            args.append("eh3_c19_nisp2")
            args.append("eh3_c20_nisd2")
            
       
        try:
            pool.CreateMeasurementGroup(args)
        except:
            self.warning("Error creating mg_nis measurement group. Check if it already exits")

        self.output("Creating mg_optpitch")

        args = []
        args.append("mg_optpitch")
        args.append("exp_t01")
        args.append("exp_c02")
        args.append("exp_c03")
        args.append("exp_c05")
        args.append("exp_c10")
       
        try:
            pool.CreateMeasurementGroup(args)
        except:
            self.warning("Error creating mg_optpitch measurement group. Check if it already exits")
  
        self.output("Creating mg_opt1064")

        args = []
        args.append("mg_opt1064")
        args.append("exp_t01")
        args.append("exp_c02")
        args.append("exp_c03")
        if eh_id == 1:
            args.append("exp_c09nfsp")
            args.append("exp_c10nfsd")
            args.append("nisp_eh1")
            args.append("nisd_eh1")
        elif eh_id == 3:
            args.append("eh3_c03nfsp")
            args.append("eh3_c04nfsd")
            args.append("eh3_c01nisp")
            args.append("eh3_c02nisd")
            args.append("vc10")
            args.append("vc36")
            args.append("ipetra")
            
       
        try:
            pool.CreateMeasurementGroup(args)
        except:
            self.warning("Error creating mg_opt1064 measurement group. Check if it already exits")

        self.output("Creating mg_opt400")

        args = []
        args.append("mg_opt400")
        args.append("exp_t01")
        args.append("exp_c02")
        args.append("exp_c03")
        if eh_id == 1:
            args.append("exp_c06")
            args.append("exp_c07")
            args.append("exp_c08")
            args.append("exp_c09")
            args.append("exp_c10")
       
        try:
            pool.CreateMeasurementGroup(args)
        except:
            self.warning("Error creating mg_opt400 measurement group. Check if it already exits")
        
        
