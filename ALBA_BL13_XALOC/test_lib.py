from sardana.macroserver.macro import Macro, Type
import taurus
import time

class test_result(Macro):

    '''
           This macro is used to turn on/off a motor 
    '''

    param_def = [ [ 'param', Type.String, None, 'a parameter'] ]
    result_def = [ [ 'dict_as_str', Type.String, None, 'dictionary info']
                ]

    def run(self, param):
        self.info(param)
        result_dict = {}
        splitted = param.split()
        for w in splitted:
            result_dict[param.index(w)] = w

        return str(result_dict)

 
class test_getting_result(Macro):

    '''
           This macro is used to turn on/off a motor 
    '''

    def run(self):

        frase = 'una altra frase per mirar'
        m = self.execMacro('test_result',frase)
        result_string = m.getResult()
        result_dict = eval(result_string)
        self.info(result_dict.keys())

class test_testdet(Macro):

    '''
           This macro is used to turn on/off a motor 
    '''

    def run(self):

       m = self.execMacro('testdet')
       testdetvalue = m.getResult()
       self.info('The result of testing the detector is %s' %testdetvalue)
       if not testdetvalue == '1':
          self.error('There is an error with the beamstop')
          return



class test_report_progress(Macro):

    '''
           This macro is used to report progress (%)
    '''

    def run(self):
        for i in range(10):
            yield (i+1)*10
            self.info('step %d, %d%%'%(i,(i+1)*10))
            time.sleep(1)
        


 

class test_stress_cryodist(Macro):
    """Test cryodist shutter mode"""
    def run(self):
        import random
        cryodist = self.getMoveable('cryodist')
        eps_dev = taurus.Device('bl13/ct/eps-plc-01')

        for i in range(1000):
            eps_dev.write_attribute('IPAP_RKX13A01_03_Ax1', True)
            pos_1 = cryodist.read_attribute('Position').value
            indexer_1 = cryodist.read_attribute('PosIndexer').value
            encoder_1 = cryodist.read_attribute('EncEncIn').value
            time.sleep(5)

            eps_dev.write_attribute('IPAP_RKX13A01_03_Ax1', True)
            pos_2 = cryodist.read_attribute('Position').value
            indexer_2 = cryodist.read_attribute('PosIndexer').value
            encoder_2 = cryodist.read_attribute('EncEncIn').value

            self.info('Step %d\t%.2f mm\t%.2f hstps\t%.2f ects\t%.2f mm\t%.2f hstps\t%.2f ects' % (i, pos_1, indexer_1, encoder_1, pos_2, indexer_2, encoder_2))

            time.sleep(30 + 5*random.random())
            
