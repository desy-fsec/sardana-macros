from sardana.macroserver.macro import Macro, Type

class set_helical_end_point(Macro):
    param_def = []
    
    def run(self):
        omegax = self.getMoveable("omegax")
        centx = self.getMoveable("centx")
        centy = self.getMoveable("centy")
        collect_env = self.getEnv( 'collect_env' )
        helical_end_point = [omegax.position, centx.position, centy.position]
        collect_env['helical_end_point'] = helical_end_point
        self.debug('set_helical_end_point DEBUG: %s' % str(collect_env) )
        self.setEnv( 'collect_env' , collect_env )
        
class unset_helical_end_point(Macro):
    param_def = []
    
    def run(self):
        collect_env = self.getEnv( 'collect_env' )
        collect_env['helical_end_point'] = 'None'
        self.debug('unset_helical_end_point DEBUG: %s' % str(collect_env) )
        self.setEnv( 'collect_env' , collect_env )

class print_helical_end_point(Macro):
    param_def = []
    
    def run(self):
        collect_env = self.getEnv( 'collect_env' )
        self.info('The helical_end_point is: %s' % str(collect_env['helical_end_point']) )