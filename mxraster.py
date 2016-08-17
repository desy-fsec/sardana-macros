from sardana.macroserver.macro import macro, iMacro, Macro, Type, ParamRepeat
import numpy, time
import datetime
import taurus
from find_spots import find_spots


class oav_raster_config(Macro):
    """
    Category: Configuration

    This macro is used to set/get the raster macro configuration.
    There are 4 possible parameters to configure:

    * PhiY: Motor for the Y direction.
    * PhyZ: for the Z direction.
    * Att: Motor for the beam attenuation.
    * MeritMethod: function name used to rank the different rastered regions.

    If the macro is executed without parameters, it shows the current
    raster configuration.
    """
    # TODO: param repeat will change on the future.
    PARAMS_ALLOWED = ['PhiY', 'PhiZ', 'Att', 'MeritMethod'] 

    param_def = [['param_list', ParamRepeat(['Param', Type.String, None, 'Name of the parameter'],
                                            ['Value', Type.String, None, 'Value of the parameter'], min=0, max=4),
                  None, '']]

    def run(self, *param_list):

        if param_list is not None:

            config = self.getEnv('MXRasterConfig')

            for key, value in param_list[0]:
                if key not in self.PARAMS_ALLOWED:
                    raise ValueError('The allowed parameters are %s' % repr(self.PARAMS_ALLOWED))
                config[key] = value
            
            self.setEnv('MXRasterConfig', config)

        config = self.getEnv('MXRasterConfig')
        self.info('Raster configuration:')
        self.info('=====================')
        for key in config:
            self.info("[%s] = %s" %(key, config[key]))
            pass


class oav_merit_method(Macro):
    # TODO: complete merit method descriptions.
    """
    Category: Configuration

    This macro is used to set/get the merit method for the mxraster macro.
    The merit method selected depends on the available methods defined in
    find_spots.py module:

    * xds: Diffraction data indexing program from Wolfgang Kabsch (http://xds.mpimf-heidelberg.mpg.de/)
    * labelit: Diffraction data indexing program of choice for automating production line from
    Lawrence Berkeley Laboratory (http://ipo.lbl.gov/lbnl1960/)
    * random: Only for test purposes. This method 'random' simulates finding
    spots on an image using a random method from the image filename. Returns
    a random value between 810 and 1120.

    If the macro is executed without parameters, it shows the current method.
    """

    PARAMS_ALLOWED = ['xds', 'labelit', 'random']

    param_def = [['param_list', ParamRepeat(['MeritMethod', Type.String, None, 'Name of the merit method selected'], min=0, max=1),
                  None, '']]

    def run(self, *param_list):

        key = 'MeritMethod'

        if param_list is not None:

            config = self.getEnv('MXRasterConfig')

            for value in param_list[0]:
                if value not in self.PARAMS_ALLOWED:
                    raise ValueError('The allowed merit methods are %s' % repr(self.PARAMS_ALLOWED))
                else:
                    config[key] = value

            self.setEnv('MXRasterConfig', config)

        config = self.getEnv('MXRasterConfig')
        self.info('Current merit method:')
        self.info('=====================')
        self.info("[%s] = %s" %(key, config[key]))


class mxraster_config(Macro):
    """
    Category: Deprecated

    Deprecated since 17/06/2015!
    You MUST use oav_raster_config macro instead.
    """
    param_def = [['PhiY', Type.String, None, 'Motor for Y direction'],
                 ['PhiZ', Type.String, None, 'Motor for Z direction'],
                 ['Att', Type.String, None, 'Motor for Beam Attenuation'],
                 ['MeritMethod', Type.String, None, 'Method for figure of merit'],
                 ]
 
    def run(self, phiy, phiz, att, method):
        msg = 'Deprecated since 17/06/2015!\n'
        msg += 'You MUST use oav_raster_config macro instead.'
        self.warning(msg)
        # config_dir = {'PhiY':  phiy,
        #                'PhiZ':  phiz,
        #                'Att':  att,
        #                'MeritMethod':  method,
        #               }
        # self.setEnv('MXRasterConfig', config_dir)


class spots_finder(Macro):
    """
    Category: Post-Processing

    Calculate the number of diffraction spots from a given image file.
    Two methods are available: xds (default) and labelit.
    """
    param_def = [['image', Type.String, None, 'Image to process'],
                 ['method', Type.String, 'xds', 'Method for figure of merit'],
                 ]

    def run(self, image, method):
        if method not in ['labelit', 'xds']:
            self.error('Invalid method value. Aborting...')
            self.abort()

        self.info("      - processing %s ... " % image )
        self.info("      - merith metod: %s" % method)
        result = find_spots( image, method)
        self.info("        * result is: %s " % result )


class mxraster(Macro):
    """
    Category: Experiments

    This macro performs a raster scan for a rectangular grid and returns a
    value which marks the different spot positions for collecting. The marks
    are assigned according to the merit method selected.
    The macro is intended to be used through a graphical user interface.
    """
    env = ('MXRasterConfig',)
    param_def = [['phiy_start_pos', Type.Float, None, 'Starting position'],
                 ['phiy_end_pos', Type.Float, None, 'Ending pos value'],
                 ['phiy_steps', Type.Integer, None, 'Steps'],
                 ['phiz_start_pos', Type.Float, None, 'Starting position'],
                 ['phiz_end_pos', Type.Float, None, 'Ending pos value'],
                 ['phiz_steps', Type.Integer, None, 'Moveable name'],
                 ['int_time', Type.Float, None, 'Time interval reserved for '],
                 ['bidir', Type.Boolean, None, 'Bidirectional scan'],
                 ['prefix', Type.String, 'mxraster', 'Filename prefix '],
                 ['save_dir', Type.String, '/beamlines/bl13/controls/tmp/mxraster' , ' '],
                 ['att', Type.String, '8', 'Attenuation value (%)'],
                 ]

    
    SIMULATION = False
    PILATUS_LATENCY = 0.0023
    LIMA_TRIGGER = 'INTERNAL_TRIGGER'

    def prepare(self, phiy_start_position, phiy_end_position, phiy_steps, 
                phiz_start_position, phiz_end_position, phiz_steps, 
                int_time, bidir, prefix, save_dir, att):

        config = self.getEnv('MXRasterConfig')
        self.debug("Config: " + str(config))
        self.merit_method = config['MeritMethod']

        self.phiy = self.getMoveable( config['PhiY'] )
        self.phiz = self.getMoveable( config['PhiZ'] )
        self.att = self.getMoveable( config['Att'] )

        self.lima_prefix = prefix 
        self.lima_runno = int(datetime.datetime.now().strftime('%Y%m%d%H%M'))
        self.lima_save_dir = save_dir

        self.phiy_org = self.phiy.position
        self.phiz_org = self.phiz.position
        self.att_org = self.att.position

        # Be carefull, raster tool returns positions in mm

        self.phiy_start_position = phiy_start_position
        self.phiy_end_position = phiy_end_position
        self.phiy_steps = phiy_steps
        self.phiz_start_position = phiz_start_position
        self.phiz_end_position = phiz_end_position
        self.phiz_steps = phiz_steps
        self.int_time = int_time
        self.bidir = bidir
#         if att is not None:
#             self.att_set_value = att
#         else:
        self.att_set_value = self.att_org
            
        if self.SIMULATION:
           self.execMacro = self.execSimulMacro

        self.execMacro("collect_prepare")
        self.execMacro("collect_saving", self.lima_save_dir, 
                       self.lima_prefix, 
                       self.lima_runno)
               
    def calc_points(self, beg, end, nbivals):
        vals = numpy.array([])
        if (nbivals > 0):
            vals = numpy.arange( beg, end, (end-beg+0.0)/nbivals )
#         else:
#             vals = numpy.array([beg])
        vals = numpy.append( vals, end )
        return vals

    def execSimulMacro(self, *args):
        self.info("Executing (SIMUL) "+ str(args))

    def run(self,*args):
        self.info('Starting the mxraster macro')
        self.info(str(args))

        # build list of z points
        zpts =  self.calc_points(self.phiz_start_position, 
                                 self.phiz_end_position, self.phiz_steps)

        # Total number of points
        self.total_pts = (self.phiz_steps+1) * (self.phiy_steps+1)
        self.curpt = 0

        self.going_back = False

        if self.SIMULATION:
             self.execMacro = self.execSimulMacro

        self.debug(" scanning z " + str(zpts) )

        self.zidx = self.yidx = 0
        step = {}

        # CHANGE ATTENUATION
        self.move_att(self.att_set_value)

        # OPEN SLOW SHUTTER 
        self.info(' Open the slowshu')
        try:  
            self.execMacro('act slowshu out')
        except:
            self.error('ERROR: Cannot actuate the slow shutter')

        # Scan z
        for zpt in zpts:

            # build list of y points
           if self.going_back:
              ypts = self.calc_points(self.phiy_end_position, 
                                     self.phiy_start_position, self.phiy_steps)
           else:
              ypts = self.calc_points(self.phiy_start_position, 
                                     self.phiy_end_position, self.phiy_steps)

           self.nb_ypts  = len(ypts)
           self.move_z(zpt)
           # Scan y and do a collect at each point
           for step in self.scan_y(ypts):
               yield step

           if self.bidir:
              self.going_back = not self.going_back

           self.zidx += 1

        self.debug(" scanning z done " )

        # CLOSE SLOW SHUTTER 
        self.info(' Open the slowshu')
        try:  
            self.execMacro('act slowshu in')
        except:
            self.error('ERROR: Cannot actuate the slow shutter')

        # Move to original position
        self.debug(" going to org " )
        self.move_att(self.att_org)
        self.move_y(self.phiy_org)
        self.move_z(self.phiz_org)
        
    def move_y(self,pos):
        self.debug("    Y --> " + str(pos)  )
        self.execMacro("mv", self.phiy, pos )

    def move_z(self,pos):
        self.debug("Z --> " + str(pos) )
        self.execMacro("mv", self.phiz, pos )

    def move_att(self,pos):
        self.debug("ATT --> " + str(pos) )
        self.execMacro("mv", self.att, pos )

    def scan_y(self,ypts):
        self.debug(" scanning y " + str(ypts) )
        self._yidx = 0

        for ypt in ypts: 

           self.move_y( ypt )

           if self.going_back:
              self.yidx = self.nb_ypts - self._yidx - 1 
           else:
              self.yidx = self._yidx 

           self.curpt = self.zidx*self.nb_ypts + self._yidx
           self.do_one_collect()
           self._yidx += 1 
           self.debug(" yielding " )
           step = {}
           perc = (self.curpt / (self.total_pts+0.0)) * 100
           self.debug ( "%s %% done " % perc )
           step['step'] = perc
           
           yield  step

        self.debug(" scanning y done " )

    def do_one_collect(self):
        self.collect_one()
        self.process_one()
        self.send_one_result()

    def collect_one(self):
        self.debug("      - collecting.." )
        self.open_shutter()
        self.last_image = self.get_one_image()
        self.close_shutter()

    def open_shutter(self):
        self.execMacro(['ni660x_shutter_open_close','open'])

    def close_shutter(self):
        self.execMacro(['ni660x_shutter_open_close','close'])

    def get_one_image(self):
        self.execMacro('pilatus_set_first_image','pilatus_custom',self.curpt+1)
        self.execMacro('lima_prepare', 'pilatus', self.int_time, 
                       self.PILATUS_LATENCY, 1, self.LIMA_TRIGGER)
        self.execMacro("lima_acquire", "pilatus")

        if self.curpt == 0:
            self.info("Acquiring")
        while True:
             limastatus_macro = self.execMacro('lima_status','pilatus')
             if self.SIMULATION:
                  break
             state, acq = limastatus_macro.getResult().split()
             self.checkPoint()
             time.sleep(1)
             if acq != 'Running':
                   break

        # FINISH THIS. HOW TO GET LAST IMAGE NAME
        if self.SIMULATION:
            return "%s/%s_%s_%04d.%s" % (self.lima_save_dir,
                                         self.lima_prefix,
                                         self.lima_runno,
                                         self.curpt, 
                                         "cbf")
        else:
           last_image = self.imageFilename()
           return last_image

    def process_one(self):
        self.debug("      - processing %s ... " % self.last_image )
        self.debug("      - merith metod: %s" % self.merit_method)
        self.last_result = find_spots( self.last_image, self.merit_method)
        self.debug("        * result is: %s " % self.last_result )

    def send_one_result(self):
#        mxraster_results = [ (self.yidx, self.zidx, self.last_result), ]

        mxraster_results = [{'sample_x':self.yidx, 'sample_y':self.zidx,
                             'value': self.last_result, 'image_file_name':
                                 self.last_image},]
        self.debug("      - sending out "  + str(mxraster_results))
        self._macro_status['data'] = {'mxraster_results': mxraster_results}

    def imageFilename(self):
        dir = self.execMacro('lima_getconfig','pilatus','FileDir'
                             ).getResult() 
        prefix = self.execMacro('lima_getconfig','pilatus','FilePrefix'
                             ).getResult() 
        inumber = self.execMacro('pilatus_get_first_image','pilatus_custom',
                                ).getResult()
        id = str("%04d" % inumber)
        format = self.execMacro('lima_getconfig','pilatus','FileFormat'
                             ).getResult() 
        suffix = '.'+ format.lower()

        return dir + prefix + id + suffix

    def on_abort(self): 
        self.warning('MXRASTER WARNING: User abort')
        # close fast shutter
        ni_shutterchan = taurus.Device('BL13/IO/ibl1302-dev1-ctr2')
        ni_shutterchan.command_inout('Stop')
        ni_shutterchan.write_attribute('IdleState', 'High')
        ni_shutterchan.command_inout('Start')

        # stop detector & reset lima
        lima_dev = taurus.Device('bl13/eh/pilatuslima')
        lima_dev.stopAcq()
        lima_dev.reset()

        # move motor to origin
        config = self.getEnv('MXRasterConfig')
        phiy = taurus.Device(config['PhiY'])
        phiz = taurus.Device(config['PhiZ'])
        phiy.write_attribute('position', self.phiy_org)
        phiz.write_attribute('position', self.phiz_org)

        # close slowshu
        eps = taurus.Device('bl13/ct/eps-plc-01')
        eps['slowshu'] = 0

