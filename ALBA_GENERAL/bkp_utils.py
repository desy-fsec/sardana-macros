from sardana.macroserver.macro import macro, Type, Macro

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
        

       
       

