from sardana.macroserver.macro import Macro, Type, ParamRepeat
import math as m
import taurus

BRUKER_XFLASH_SERIAL_DEV='BL13/CT/SERIAL-15'
xflash = taurus.Device(BRUKER_XFLASH_SERIAL_DEV)

# NOTE: THE TRAILING \r CAN BE ADDED BY THE MACRO BUT THE
#       '$' PREFFIX SHOULD BE PASSED BY THE MACRO PARAM

class xflash_write(Macro):
    param_def = [ [ 'cmd',
                    ParamRepeat(['cmd_str', Type.String, None, 'part of the command']),
                    None, 'Command to be sent.'] ]
    def run(self, *cmd):
        cmd_str = ' '.join(cmd)
        cmd_str = cmd_str.upper()
        xflash.DevSerWriteString('$'+cmd_str+'\r')

class xflash_readline(Macro):
    result_def = [ [ 'answer', Type.String, '', 'a line from serial port.' ]
                   ]
    def run(self):
        ans = xflash.DevSerReadLine()
        return ans

class xflash_ask(Macro):
    param_def = [ [ 'cmd',
                    ParamRepeat(['cmd_str', Type.String, None, 'part of the command']),
                    None, 'Command to be sent.'] ]
    result_def = [ [ 'answer', Type.String, '', 'a line from serial port.' ]
 ]
    def run(self, *cmd):
        cmd_str = ' '.join(cmd)
        cmd_str = cmd_str.upper()

        xflash.DevSerWriteString('$'+cmd_str+'\r')
        ans = xflash.DevSerReadLine()

        ## SHOULD BE USING THE TANGO COMMAND WriteRead
        ## BY TRIAL AND ERROR, I RECEIVED THE ERROR:
        ## Serial::error_argin: unknown type of read, must be SL_NCHAR, SL_LINE, SL_RETRY
        ## AND IT DID THE EXPECTED BEHAVIOUR WITH 'TYPE 2'
        #
        #tango_cmd_argin = ([2], ['$'+cmd_str+'\r'])
        #ans = xflash.DevSerWriteString(tango_cmd_argin)

        return ans

class xflash_readbinary(Macro):
    param_def = [ [ 'length', Type.Float, 10000, 'length to read',
                    None, 'Command to be sent.'] ]
    result_def = [ [ 'data', Type.String, '', 'data (string) read.' ]
 ]
    def run(self, length=10000):
        data = xflash.DevSerReadNBinData(length)
        self.info('data'+str(data))
        return ' '.join(map(str,data))

### def plotit():
###     data = []
###     try:
###         while True:
###             data += s.DevSerReadNBinData(10000).tolist();time.sleep(0.5)
###     except Exception,e:
###         print('got an exception\n:'+str(e))
###     print(len(data))
###     plt.plot(xrange(len(data)),data)
###     plt.show()
