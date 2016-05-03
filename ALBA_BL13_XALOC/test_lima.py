from sardana.macroserver.macro import macro, iMacro, Macro, Type, ParamRepeat
import time
import taurus

class test_limastatusquery(Macro):
    '''
    Category: Test
    Request the status fo a device server at certain frquency.
    '''
    param_def = [ ['det', Type.String, 'bl13/eh/pilatuslima', 'lima device name'],
                  ['nq', Type.Integer, 0, "number of queries to perform" ],
                  ['freq', Type.Float, 1, "time between queries"]
                ]
 
    def run(self, det, nq, freq):

        self.info('Numer of queries: %s' % nq)
        self.info('Performe query every %s s.' % freq)
        self.info('Detector: %s' % det)

        try:
            dev = taurus.Device(det)
            self.info('ping: %s s' % dev.ping())

        except:
            raise Exception('Cannot connect to detector %s' % det)
            
        
        counter = 0

        try:
            while counter <= nq or nq == 0:
                limastatus = self.execMacro('lima_status', det)
                state, acq = limastatus.getResult().split()
                self.info('Query #%s: state: %s, acq: %s' % (counter, state, acq))
                counter += 1
                self.checkPoint()
                time.sleep(freq)
                
        except:
            self.error('Exception during queries')


