from sardana.macroserver.macro import macro, Type, Macro
import ConfigParser
import time

class bkp_sardana(Macro):
    """
    Macro to save the configuration of all controller and their elements.
    
    """
    param_def = [["filename", Type.String, None, "Position to move"]]
    
    def run(self, filename):
        error_flg = False
        error_msg = ''
        data=''
        data += ('Enviroment')
        data += str(self.getAllEnv())
        data += '-'*80 +'\n'
        data +='Controllers:\n'
        ctrls = self.getControllers()
        for ctrl in ctrls.values():
            #controllers
            ctrl = ctrl.getObj()
            data += ctrl.getName() + '\n'
            data += str(ctrl.get_property(ctrl.get_property_list('*'))) + '\n'
            elements = ctrl.elementlist
            for element in elements:
                #elements (motors, counter/timers, etc..)
                data += '*'*80 +'\n'
                data += str(element) + '\n'
                elm = self.getObj(element)
                data += str(elm.get_property(elm.get_property_list('*'))) + '\n'
                attrs = elm.get_attribute_list()
                for attr in attrs:
                    data += '-'*20 + '\n'
                    try:
                        attr_value = elm.read_attribute(attr).value
                    except Exception as e:
                        attr_value = 'Error on the read method %s ' % e
                        error_flg = True
                        error_msg += attr_value + '\n'
                    data += '%s = %s \n' % (attr, attr_value)

            data += '-'*80 +'\n'

        with open(filename,'w') as f:
            f.write(data)
        if error_flg:
            self.error(error_msg)
        

class MntGrpConf(object):
    """
    Class Helper to read the configuration file.
    """

    def _tolist(self, data):
        data = data.replace('\n', ' ')
        data = data.replace(',', ' ')
        return data.split()

    def _create_bkp(self):
        self.info('Creating backup...')
        path, filename = self.config_path.rsplit('/', 1)
        t = '{0}/bkp_{1}_{2}'
        nfilename = t.format(path,time.strftime('%Y%m%d_%H%M%S'), filename)
        self._save_file(nfilename)
        self.info('Created backup file: %s' % nfilename)

    def _save_file(self, filename):
        """
        :param filename: New file name to save the current configuration.
        """
        with open(filename,'w') as f:
            self.config_file.write(f)

    def init_config(self, config_path):
        self.config_file = ConfigParser.RawConfigParser()
        self.config_file.read(config_path)
        self.config_path = config_path

    def get_config(self, mnt_grp):
        mnt_grp = mnt_grp.lower()
        self.info(mnt_grp)
        try:
            config_value = self.config_file.get(mnt_grp, 'configuration')

        except:
            raise RuntimeError('The configuration file is corrupted or you '
                               'did not save the configuration.')

        return config_value

    def save(self, mnt_grp, config):
        self._create_bkp()
        self.info('Saving configuration....')
        mnt_grp = mnt_grp.lower()
        if not self.config_file.has_section(mnt_grp):
            self.config_file.add_section(mnt_grp)
        self.config_file.set(mnt_grp, 'configuration', config)
        self._save_file(self.config_path)
        self.output('Saved configuration.')


class save_mntgrp(Macro, MntGrpConf):
    """
    Macro to create backups of the measurement group configurations

    """

    env = ('MntGrpConfFile',)
    param_def = [['mg', Type.MeasurementGroup, None, 'Measurement Group'],
                 ['UseDefault', Type.Boolean, False, 'Use default']]

    def run(self, mg, use_default):
        config_path = self.getEnv('MntGrpConfFile')
        if use_default:
           path = config_path.rsplit('/',1)[0]
           filename = '/mntgrp_default.cfg'
           config_path = path + filename
        self.init_config(config_path)
        config = mg.read_attribute('configuration').value
        self.save(mg.getName(), config)


class load_mntgrp(Macro, MntGrpConf):
    """
    Macro to create backups of the measurement group configurations

    """

    env = ('MntGrpConfFile',)
    param_def = [['mg', Type.MeasurementGroup, None, 'Measurement Group'],
                 ['UseDefault', Type.Boolean, True, 'Use default']]

    def run(self, mg, use_default):
        config_path = self.getEnv('MntGrpConfFile')
        if use_default:
           path = config_path.rsplit('/',1)[0]
           filename = '/mntgrp_default.cfg'
           config_path = path + filename
       
        self.init_config(config_path)

        mg_bkp_config = self.get_config(mg.getName())
        mg_config = mg.read_attribute('configuration').value
        diff_conf = mg_config != mg_bkp_config
        msg = 'The current configuration %s the same than the backup' % \
              ['is', 'is not'][diff_conf]
        if diff_conf:
            self.warning(msg)
            self.info('Loading backup...')
            mg.write_attribute('configuration', mg_bkp_config)
            self.output('Loaded backup')
        else:
            self.output(msg)
