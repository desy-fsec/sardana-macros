import PyTango
import time
from sardana.macroserver.macro import macro, Type, Macro , \
ViewOption, ParamRepeat

XIA1_NAME = 'bl22/ct/xiapfcu-1'
XIA2_NAME = 'bl22/ct/xiapfcu-2'

xia1 = PyTango.DeviceProxy(XIA1_NAME)
xia2 = PyTango.DeviceProxy(XIA2_NAME)
retries = 3

 
filters = {1: 4, 2: 3, 3: 2, 4: 1}
 
def _getFilters():
    for i in range(retries):
        data1 = xia1.read_attribute('Filter_Positions').value.split(' ')[3]
        data2 = xia2.read_attribute('Filter_Positions').value.split(' ')[3]
        if data1 !='' and data2!='':
            break
    filter_state = []
    data = data1 + data2
    for i in data:
        if int(i) == 0 :
            st = 'OUT'
        elif int(1) == 1 :
            st = 'IN'
        else:
            raise Exception('Problem with the communication')
        filter_state.append(st)
    return filter_state

def _prepareCmd(filters):
    cmd1 = ''
    cmd2 = ''
        
    for i in filters:
        if i < 1 or i >8:
            raise ValueError('Filter must be from 1 to 8')
        if i < 5:
            cmd1 += str(filters[i])
        else:
            cmd2 += str(filters[i-4])
    return cmd1, cmd2

def _insFilter(filters):
    cmd1, cmd2 = _prepareCmd(filters)
    if cmd1 != '':
        xia1.write_attribute('Insert_Filter', cmd1)

    if cmd2 != '':
        xia2.write_attribute('Insert_Filter', cmd2)

    time.sleep(1)  
  
def _remFilter(filters):
    cmd1, cmd2 = _prepareCmd(filters)
    
    if cmd1 != '':
        xia1.write_attribute('Remove_Filter', cmd1)

    if cmd2 != '':
        xia2.write_attribute('Remove_Filter', cmd2)

    time.sleep(1)


class insFilter(Macro):
    param_def = [
        ['filter_list',ParamRepeat(['Number', Type.Integer, None, 'Filter'],
                                   min=1, max=8), None, 
         'Filter list, form 1 to 8']]

    def run(self, *filter_list):
        
        self.info(filter_list)
        _insFilter(filter_list)

class remFilter(Macro):
    param_def = [
        ['filter_list',ParamRepeat(['Number', Type.Integer, None, 'Filter'],
                                   min=1, max=8), None, 
         'Filter list, form 1 to 8']]

    def run(self, *filter_list):
        _remFilter(filter_list)


class getFilter(Macro):
    def run(self):
        filter = _getFilters()
        self.info('Filters: %s' % repr(filter))



if __name__ == "__main__":
    pass
