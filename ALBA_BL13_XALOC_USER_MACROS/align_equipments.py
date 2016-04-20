from sardana.macroserver.macro import Macro, Type
import math as m

# self.info() = output in blue    
# self.error() = output in red
# self.output() = output in black


class align_lamo(Macro):
    def run(self):
        self.execMacro('umv dmot1 100 dmot2 200 dmot3 300')
        print 'Lamo in position'


class opvfmpit_realign(Macro):
    '''realign optics after mvr vfmpit
      Outputs the command that can be copy-pasted to move OH downstream elements
      accordinly to a relative movement of vfmpit'''
    param_def = [ [ 'mvrvfmpit', Type.Float, 0.0, 'Relative movement of vfmpit. Default 0']
                ]
    def run(self, mvrvfmpit):
        
        if (mvrvfmpit<-5 or mvrvfmpit>5):
            self.error('Relative vfmpit step is probably too large to be true!')
            return

	# Distances in m from vfm to the dowstream elements
	dist_s2 = 0.975
	dist_bpm3 = 1.165
	dist_hfm = 1.985
	dist_bpm4 = 2.96
	dist_fsm2 = 3.2

	# relative movement in mm of the dowstream elements
	mvr_s2vo = dist_s2*mvrvfmpit*2
	mvr_bpm3 = dist_bpm3*mvrvfmpit*2
	mvr_hfm = dist_hfm*mvrvfmpit*2
	mvr_bpm4 = dist_bpm4*mvrvfmpit*2
	mvr_fsm2 = dist_fsm2*mvrvfmpit*2
	

        macro_cmd1 = 'umvr vfmpit %f s2vo %f bpm3z %f hfmx %f bpm4z %f fsm2z %f' % (mvrvfmpit, mvr_s2vo, mvr_bpm3, mvr_hfm, mvr_bpm4, mvr_fsm2)
	# self.execMacro(macro_cmd1)
        self.info('\nCommand needed to coherently move the OH elements with a mvr vfmpit %f:' % mvrvfmpit)
        self.output(macro_cmd1)



class ophfmpit_realign(Macro):
    '''realign optics after mvr vfmpit'''
    param_def = [ [ 'mvrhfmpit', Type.Float, 0.0, 'Relative movement of hfmpit. Default 0']
                ]
    def run(self, mvrhfmpit):
        
        if (mvrhfmpit<-5 or mvrhfmpit>5):
            self.error('Relative hfmpit step is probably too large to be true!')
            return

	# Distances in m from vfm to the dowstream elements
	dist_s3 = 2.76-1.985
	dist_bpm4 = 2.96-1.985
	dist_fsm2 = 3.2-1.985

	# relative movement in mm of the dowstream elements
	mvr_s3ho = -dist_s3*mvrhfmpit*2
	mvr_bpm4 = dist_bpm4*mvrhfmpit*2
	mvr_fsm2 = dist_fsm2*mvrhfmpit*2
	

        macro_cmd1 = 'umvr hfmpit %f s3ho %f bpm4x %f' % (mvrhfmpit, mvr_s3ho, mvr_bpm4)
	# self.execMacro(macro_cmd1)
        self.info('\nCommand needed to coherently move the OH downstream elements with a mvr hfmpit %f:' % mvrhfmpit)
        self.output(macro_cmd1)
        self.output('\nCommand mvr hfmpit %f displaces laterally (x) fsm2 by %f mm (not correctable)' % (mvrhfmpit, mvr_fsm2))



class align(Macro):
    '''align oh eh '''
    param_def = [ [ 'focusing_mode', Type.String, '', 'One of FF, FU, UF, UU modes'],
                  [ 'station', Type.String, '', 'One of oh, eh'],
                  [ 'station2', Type.String, '', 'One of oh, eh']
                ]
    def run(self, focusing_mode, station, station2):
	motors_to_move = {}

        focusing_mode = focusing_mode.upper()
        station = station.upper()
        station2 = station2.upper()
        if focusing_mode not in ['FF', 'FU', 'UF', 'UU', '']:
            self.error('Focus mode should be one of: FF, FU, UF, UU (HxV)')
            return
        elif focusing_mode == 'FF':
            if station == 'OH' or station2 == 'OH':
                  motors_to_move['bpm3x'] = -1.9862500
                  motors_to_move['bpm3z'] = -1.1893125
                  motors_to_move['bpm4x'] = -4.9825000
                  motors_to_move['bpm4z'] = -11.1970000
                  motors_to_move['fehg'] = 2.7050000
                  motors_to_move['fevg'] = 0.7000000
                  motors_to_move['foilb1'] = 54.9990000
                  motors_to_move['foilb2'] = 50.0
                  motors_to_move['foilb3'] = 43.0
                  motors_to_move['foilb4'] = 23.0
                  motors_to_move['fsm2z'] = 38.2030000
                  motors_to_move['hfmpit'] = 4.0999679
                  motors_to_move['hfmx'] = 8.1999406
                  motors_to_move['hfmz'] = -0.250047865593 
                  motors_to_move['lamopit'] = 0.0005000
                  motors_to_move['lamoroll'] = 0.0000000
                  motors_to_move['lamox'] = 4.9999500
                  motors_to_move['lamoz'] = 9.2897500
                  motors_to_move['s1hg'] = 6.0100000
                  motors_to_move['s1vg'] = 2.9990000
                  motors_to_move['s2vg'] = 24.9560000
                  motors_to_move['vfmpit'] = 4.0999425
                  motors_to_move['vfmroll'] = 0.0000000
                  motors_to_move['vfmx'] = 0.0000496
                  motors_to_move['vfmz'] = -0.4822810
            if station == 'EH' or station2 == 'EH':
                  motors_to_move['diftabpit'] = 8.15
                  motors_to_move['diftabx'] = -36.2199219
                  motors_to_move['diftabyaw'] = 9.452
                  motors_to_move['diftabz'] = 54.3726019
                  motors_to_move['s4hg'] = 4.0
                  motors_to_move['s4vg'] = 4.0
        elif focusing_mode == 'FU':
              if station == 'OH' or station2 == 'OH':
                  motors_to_move['bpm3x'] = -1.9862500
                  motors_to_move['bpm3z'] = 0.9828125 
                  motors_to_move['bpm4x'] = -4.9825000
                  motors_to_move['bpm4z'] = -11.2668750
                  motors_to_move['fehg'] = 2.7050000
                  motors_to_move['fevg'] = 0.7000000
                  motors_to_move['foilb1'] = 54.9990000
                  motors_to_move['foilb2'] = 50.0
                  motors_to_move['foilb3'] = 43.0
                  motors_to_move['foilb4'] = 23.0
                  motors_to_move['fsm2z'] = 13.8000000 
                  motors_to_move['hfmpit'] = 4.0999679
                  motors_to_move['hfmx'] = 8.1999406
                  motors_to_move['hfmz'] = -0.250047865593 
                  motors_to_move['lamopit'] = 0.0005000
                  motors_to_move['lamoroll'] = 0.0000000
                  motors_to_move['lamox'] = 4.9999500
                  motors_to_move['lamoz'] = 9.2897500
                  motors_to_move['s1hg'] = 6.0100000
                  motors_to_move['s1vg'] = 2.9990000
                  motors_to_move['s2vg'] = 24.9560000
                  motors_to_move['vfmpit'] = 4.0999425
                  motors_to_move['vfmroll'] = 0.0000000
                  motors_to_move['vfmx'] = 0.0000496
                  motors_to_move['vfmz'] = -2
        elif focusing_mode == 'UF':
              motors_to_move['bpm3x'] = -1.9862500
              motors_to_move['bpm3z'] = -1.1891250
              motors_to_move['bpm4x'] = 4.7992188
              motors_to_move['bpm4z'] = -11.1911250
              motors_to_move['fehg'] = 2.7050000
              motors_to_move['fevg'] = 0.7000000
              motors_to_move['foilb1'] = 54.9990000
              motors_to_move['foilb2'] = 50.0000000
              motors_to_move['foilb3'] = 43.0
              motors_to_move['foilb4'] = 23.0
              motors_to_move['fsm2z'] = 38.2030000
              motors_to_move['hfmpit'] = 4.1 
              motors_to_move['hfmx'] = 8.1998625
              motors_to_move['hfmz'] = -5.1502381
              motors_to_move['lamopit'] = 0.0005000
              motors_to_move['lamoroll'] = 0.0000000
              motors_to_move['lamox'] = 4.9999500
              motors_to_move['lamoz'] = 9.2897500
              motors_to_move['s1hg'] = 6.0100000
              motors_to_move['s1vg'] = 2.9990000
              motors_to_move['s2vg'] = 24.9560000
              motors_to_move['vfmpit'] = 4.0999425
              motors_to_move['vfmroll'] = 0.0000000
              motors_to_move['vfmx'] = 0.0000496
              motors_to_move['vfmz'] = -0.4822810
        elif focusing_mode == 'UU':
              motors_to_move['bpm3x'] = -2.0059375
              motors_to_move['bpm3z'] = 0.9828125
              motors_to_move['bpm4x'] = 4.7957813
              motors_to_move['bpm4z'] = -11.2668750
              motors_to_move['fehg'] = 2.7050000
              motors_to_move['fevg'] = 0.7000000
              motors_to_move['foilb1'] = 54.0
              motors_to_move['foilb2'] = 54.0
              motors_to_move['foilb3'] = 43.0
              motors_to_move['foilb4'] = 23.0
              motors_to_move['fsm2z'] = 13.8000000
              motors_to_move['hfmpit'] = 4.0999679
              motors_to_move['hfmx'] = -0.0000208
              motors_to_move['hfmz'] = -4.9999601
              motors_to_move['lamopit'] = 0.0005000
              motors_to_move['lamoroll'] = 0.0000000
              motors_to_move['lamox'] = 4.9999500
              motors_to_move['lamoz'] = 9.2897500
              motors_to_move['s1hg'] = 6.0100000
              motors_to_move['s1vg'] = 2.9990000
              motors_to_move['s2vg'] = 24.9560000
              motors_to_move['vfmpit'] = 4.0999425
              motors_to_move['vfmroll'] = 0.0000000
              motors_to_move['vfmx'] = 0.0000496
              motors_to_move['vfmz'] = -2
              if station == 'EH':
                  motors_to_move['diftabpit'] = 0.0001332
                  motors_to_move['diftabx'] = -0.1412109
                  motors_to_move['diftabyaw'] = 1.2123712
                  motors_to_move['diftabz'] = 0.0001572
                  motors_to_move['s4hg'] = 4 
                  motors_to_move['s4vg'] = 4 


	for motor,pos in motors_to_move.iteritems():
	    #self.execMacro('umv %s %f' %(motor,pos))
	    # GET THE MOTOR OBJECT
	    motor_obj = self.getObj(motor)
	    try:
		motor_obj['PowerOn'] =  True
	    except:
	        self.warning('Motor %s DOES NOT HAVE PowerOn' % motor)
	    # OR USE MACRO set_attr
	   
            self.info ('Moving %s' % motor) 
	    try: self.execMacro('umv',motor, pos)
            except: self.warning('Could not move %s' % motor)
	    #umv_cmd += '%s %f ' % (motor, pos)

	#self.info('I COULD EXECUTE MACRO: '+umv_cmd)	
	wm_cmd = 'wm '+' '.join(motors_to_move.keys())
	self.info(wm_cmd)
	self.execMacro(wm_cmd)


        self.info('\nMirrors in %s mode position' % focusing_mode)



