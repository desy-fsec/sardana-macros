"""
    Macro library containing icepap related macros for the macro
    server Tango device server as part of the Sardana project.
"""

import pyIcePAP
import time
import PyTango
from sardana.macroserver.macro import *
from macro_utils.icepap import create_motor_info_dict, home, \
                               home_group, home_strict, home_group_strict

# globals
ENV_FROM = '_IcepapEmailAuthor'
ENV_TO = '_IcepapEmailRecipients'
SUBJECT = 'Icepap: %s was reset by a Sardana macro' 

# util functions
def isIcepapMotor(macro, motor):
    '''Checks if pool motor belongs to the IcepapController'''

    controllers = macro.getControllers()
    ctrl_name = motor.controller
    controller_obj = controllers[ctrl_name]
    return isIcepapController(macro, controller_obj)

def isIcepapController(macro, controller):
    '''Checks if pool controller is of type IcepapController'''

    if isinstance(controller, str):
        controller_name = controller
        controllers = macro.getControllers()
        controller_obj = controllers[controller_name]
    else:
        controller_obj = controller
    controller_class_name = controller_obj.getClassName()
    if controller_class_name != "IcepapController":
        return False
    return True

def fromAxisToCrateNr(axis_nr):

    '''Translates axis number to crate number'''

    #TODO: add validation for wrong axis numbers
    crate_nr = axis_nr / 10
    return crate_nr

def sendMail(efrom, eto, subject, message):
    '''sends email using smtp'''

    from email.MIMEMultipart import MIMEMultipart
    from email.MIMEText import MIMEText
    import smtplib
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = efrom
    msg["To"] = ','.join(eto)
    body = MIMEText(message)
    msg.attach(body)
    smtp = smtplib.SMTP('localhost')
    smtp.sendmail(msg["From"], msg["To"], msg.as_string())
    smtp.quit()


def waitSeconds(macro, seconds):
    '''an "abort safe" wait'''

    for i in range(seconds):
        time.sleep(1)
        macro.checkPoint()


def getResetNotificationAuthorAndRecipients(macro):
    '''gets a recipients list and author from the environment variable.
       In case the variable is not defined it rises a verbose exception'''
    try:
        recipients = macro.getEnv(ENV_TO)
        if not (isinstance(recipients, list) and len(recipients)):
            msg = '"%s" variable is not a list or is empty.' % ENV_TO
            raise Exception(msg)
        author = macro.getEnv(ENV_FROM)
        if not (isinstance(author, str) and len(author)):
            msg = '"%s" variable is not a string or is empty.' % ENV_FROM
            raise Exception(msg)
    except Exception, e:
        macro.debug(e)
        msg = 'Icepap resets should be executed with caution. ' + \
              'It is recommended to notify the Icepap experts about the ' + \
              'reset. Automatic notifications WILL NOT be send. ' + str(e)
        raise Exception(msg)
    return author, recipients


#macros
class ipap_get_closed_loop(Macro):
    """Returns current closed loop configuration value for a given motor"""

    param_def = [
       ["motor",  Type.Motor,  None, "motor to request (must be and IcePAP motor)"],
    ]

    icepap_ctrl = "IcePAPCtrl.py"

    def prepare(self, motor):
        """Check that parameters for the macro are correct"""
        motorOk = False

        #check that motor controller is of type icepap
        controller = motor.getControllerName()
        pool = motor.getPoolObj()
        ctrls_list = pool.read_attribute("ControllerList").value
        for ctrl in ctrls_list:
            found = ctrl.find(controller)
            if found >= 0:
                if ctrl.find(self.icepap_ctrl) >= 0:
                    motorOk = True
                break
        if not motorOk:
            raise Exception("Motor %s is not an IcePAP motor" % str(motor))

    def run(self, motor):
        """Run macro"""

        if motor.read_attribute("ClosedLoop").value:
            status = "ON"
        else:
            status = "OFF"

        self.output("Closed loop is %s in motor %s" % (status, str(motor)))
        return status


class ipap_set_closed_loop(Macro):
    """Enables/Disables closed loop in a given motor"""

    param_def = [
       ["motor",  Type.Motor,  None, "motor to configure (must be and IcePAP motor)"],
       ["ON/OFF", Type.String, None, "ON to enable / OFF to disable closed loop"]
    ]

    icepap_ctrl = "IcePAPCtrl.py"
    actions = ("ON", "OFF")

    def prepare(self, motor, action):
        """Check that parameters for the macro are correct"""
        motorOk = False

        #check that motor controller is of type icepap
        controller = motor.getControllerName()
        pool = motor.getPoolObj()
        ctrls_list = pool.read_attribute("ControllerList").value
        for ctrl in ctrls_list:
            found = ctrl.find(controller)
            if found >= 0:
                if ctrl.find(self.icepap_ctrl) >= 0:
                    motorOk = True
                break
        if not motorOk:
            raise Exception("Motor %s is not an IcePAP motor" % str(motor))

        #check that "action" is valid
        if action.upper() in self.actions:
            pass
        else:
            raise Exception("action must be one of: %s" % str(self.actions))

    def run(self, motor, action):
        """Run macro"""
        action = action.upper()

        if action == "ON":
            closed_loop = True
        else:
            closed_loop = False
        #read back closed loop status to check it's the one we have just set
        motor.write_attribute("ClosedLoop",closed_loop)
        closed_loop_rb = motor.read_attribute("ClosedLoop").value
        if closed_loop == closed_loop_rb:
            self.output("Closed loop %s correctly set in motor %s" % (action,str(motor)))
            return True
        else:
            self.output("WARNING!: read back from the controller (%s) didn't match the requested parameter (%s)" %  (str(closed_loop_rb),str(closed_loop)))
            return False


class ipap_get_steps_per_turn(Macro):
    """Returns current steps per turn value for a given motor"""

    param_def = [
       ["motor",  Type.Motor,  None, "motor to request (must be and IcePAP motor)"],
    ]

    icepap_ctrl = "IcePAPCtrl.py"
    config_command = "%d:CONFIG"
    get_command = "%d:?CFG ANSTEP"

    def prepare(self, motor):
        """Check that parameters for the macro are correct"""
        motorOk = False

        #check that motor controller is of type icepap
        controller = motor.getControllerName()
        pool = motor.getPoolObj()
        ctrls_list = pool.read_attribute("ControllerList").value
        for ctrl in ctrls_list:
            found = ctrl.find(controller)
            if found >= 0:
                if ctrl.find(self.icepap_ctrl) >= 0:
                    motorOk = True
                break
        if not motorOk:
            raise Exception("Motor %s doesn't support closed loop" % str(motor))

    def run(self, motor):
        """Run macro"""
        #get axis number, controller name and pool
        axis = motor.getAxis()
        controller = motor.getControllerName()
        pool = motor.getPoolObj()

        #write command to icepap
        cmd = self.get_command % axis
        result = pool.SendToController([controller,cmd])

        #read result and return value
        steps = result.split()[2]
        self.output("% s steps per turn in motor %s" % (steps, str(motor)))
        return int(steps)


class ipap_set_steps_per_turn(Macro):
    """Set steps per turn value for a given motor"""

    param_def = [
       ["motor",  Type.Motor,  None, "motor to configure (must be and IcePAP motor)"],
       ["steps", Type.Integer, None, "steps per turn value"]
    ]

    icepap_ctrl = "IcePAPCtrl.py"
    config_command = "%d:CONFIG" 
    set_command = "%d:CFG ANSTEP %d"
    get_command = "%d:?CFG ANSTEP"
    sign_command = "%d:CONFIG %s"

    def prepare(self, motor, steps):
        """Check that parameters for the macro are correct"""
        motorOk = False

        #check that motor controller is of type iceepap
        controller = motor.getControllerName()
        pool = motor.getPoolObj()
        ctrls_list = pool.read_attribute("ControllerList").value
        for ctrl in ctrls_list:
            found = ctrl.find(controller)
            if found >= 0:
                if ctrl.find(self.icepap_ctrl) >= 0:
                    motorOk = True
                break
        if not motorOk:
            raise Exception("Motor %s is not an IcePAP motor" % str(motor))

    def run(self, motor, steps):
        """Run macro"""
        #get axis number, controller name and pool
        axis = motor.getAxis()
        controller = motor.getControllerName()
        pool = motor.getPoolObj()

        #set controller in config mode
        cmd = self.config_command % axis
        result = pool.SendToController([controller,cmd])

        #set the requested steps per turn
        cmd = self.set_command % (axis,steps)
        result = pool.SendToController([controller,cmd])

        #sign the change in icepap controller
        cmd = self.sign_command % (axis,"Steps per turn changed on user request from macro %s on %s" % (str(self.__class__.__name__),str(time.ctime())))
        result = pool.SendToController([controller,cmd])

        #read back steps per turn to confirm command worked OK
        cmd = self.get_command % axis
        result = pool.SendToController([controller,cmd])
        steps_rb = int(result.split()[2])
        if steps == steps_rb:
            self.output("Steps per turn %d correctly set in motor %s" % (steps,str(motor)))
            return True
        else:
            self.output("WARNING!: read back from the controller (%s) didn't match the requested parameter (%d)" %  (str(result),steps))
            return False


class ipap_homing(Macro):
    """This macro will execute an icepap homing routine for all motors passed as arguments in directions passes as arguments.
       Directions are considered in pool sense. 
       Icepap homing routine is parametrizable in group and strict sense, so it has 4 possible configurations. 
       Macro result depends on the configuration which you have chosen:
       - HOME (macro result is True if all the motors finds home, otherwise result is False) 
       - HOME GROUP (macro result is True if all the motors finds home, otherwise result is False)
       - HOME STRICT (macro result is True when first motor finds home, otherwise result is False)
       - HOME GROUP STRICT (macro result is True when first motor finds home, otherwise result is False) 
    """

    param_def = [
        ["group",  Type.Boolean, False, "If performed group homing."],         
        ["strict",  Type.Boolean, False, "If performed strict homing."],         
        ['motor_direction_list',
        ParamRepeat(['motor', Type.Motor, None, 'Motor to be homed.'],
                    ['direction', Type.Integer, None, 'Direction of homing (in pool sense) <-1|1>']),
        None, 'List of motors and homing directions.']
    ]

    result_def = [
        ['homed',  Type.Boolean, None, 'Motors homed state']
    ]       
       
    def prepare(self, *args, **opts):
        self.group = args[0]
        self.strict = args[1]
        self.motors = []

        motors_directions = args[2:]
        self.motorsInfoList = [create_motor_info_dict(m,d) for m,d in motors_directions]

        #getting motion object for automatic aborting
        motorNames = [motorInfoDict['motor'].name for motorInfoDict in self.motorsInfoList] 
        self.getMotion(motorNames)
        
        
    def run(self, *args, **opts):

        if self.group and self.strict:
            return home_group_strict(self, self.motorsInfoList)
        elif self.group:
            return home_group(self, self.motorsInfoList)
        elif self.strict:
            return home_strict(self, self.motorsInfoList)
        else: 
            return home(self, self.motorsInfoList)


@macro([["motor", Type.Motor, None, "motor to jog"],
        ["velocity", Type.Integer, None, "velocity"]])
def ipap_jog(self, motor, velocity):
    poolObj = motor.getPoolObj()
    ctrlName = motor.getControllerName()
    axis = motor.getAxis()
    poolObj.SendToController([ctrlName, "%d: JOG %d" % (axis, velocity)])


@macro([["motor", Type.Motor, None, "motor to reset"]])
def ipap_reset_motor(self, motor):
    '''Resets a crate where the Icepap motor belongs to. This will send an 
       autmatic notification to recipients declared 
       in '_IcepapEmailRecipients' variable'''

    motor_name = motor.getName()
    if not isIcepapMotor(self, motor):
        self.error('Motor: %s is not an Icepap motor' % motor_name)
        return
    
    #pool_obj = motor.getPoolObj()
    
    # We call to next funcion because the getPoolObj of sardana randomly have
    # a exception, then we use this fix _getPoolObj of this file.
    
    pool_obj = _getPoolObj(motor)
    ctrl_name = motor.getControllerName()
    ctrl_obj = motor.getControllerObj()
    icepap_host = ctrl_obj.get_property('host')['host'][0]
    axis_nr = motor.getAxis()
    crate_nr = fromAxisToCrateNr(axis_nr)
    status = motor.read_attribute('StatusDetails').value
    status_closeLoop = motor.read_attribute('StatusStopCode').value
    alarm_msg_closeLoop = "Close loop error"
    

    # Implement verification about the StatusStopCode to decide which command to execute:
    if alarm_msg_closeLoop in status_closeLoop:
        cmd = "%d:ESYNC" % axis_nr
        self.debug('Detected Close Loop error')
    else:
        cmd = "RESET %d" % crate_nr

    self.debug('Sending command: %s' % cmd)
    pool_obj.SendToController([ctrl_name, cmd])
    msg = 'Crate nr: %d of the Icepap host: %s ' % (crate_nr, icepap_host) + \
          'is being reset. It will take aprox. 3 seconds...'
    self.info(msg)

    try: 
        efrom, eto = getResetNotificationAuthorAndRecipients(self)
    except Exception, e:
        self.warning(e)
        return
    
    ms = self.getMacroServer()
    ms_name = ms.get_name()
    efrom = '%s <%s>' % (ms_name,efrom)
    subject = SUBJECT % icepap_host
    message =  'Macro: ipap_reset_motor(%s)\n' % motor_name
    message += 'Pool name: %s\n' % pool_obj.name()
    message += 'Controller name: %s\n' % ctrl_name
    message += 'Motor name: %s\n' % motor_name
    message += 'Icepap host: %s\n' % icepap_host
    message += 'Axis: %s\n' % axis_nr
    message += 'Status: %s\n' % status
    self.info(message)    
    sendMail(efrom, eto, subject, message)
    self.info('Email notification was send to: %s' % eto)
    # waiting 3 seconds so the Icepap recovers after the reset
    # it is a dummy wait, probably it could poll the Icepap 
    # and break if the reset is already finished
    waitSeconds(self, 3)


@macro([["icepap_ctrl", Type.Controller, None, "icepap controller name"],
        ["crate_nr", Type.Integer, -1, "crate_nr"]])
def ipap_reset(self, icepap_ctrl, crate_nr):
    """Resets Icepap. This will send an autmatic notification to recipients
       declared in '_IcepapEmailRecipients' variable"""

    if not isIcepapController(self, icepap_ctrl):
        self.error('Controller: %s is not an Icepap controller' % \
                                              icepap_ctrl.getName())
        return
    ctrl_obj = icepap_ctrl.getObj()
    
    
    # pool_obj = ctrl_obj.getPoolObj()
    
    icepap_host = ctrl_obj.get_property('host')['host'][0]
    ice_dev = pyIcePAP.EthIcePAP(icepap_host,5000)
    
    pool_obj = _getPoolObj(ctrl_obj)
        

    while not ice_dev.connected:
        time.sleep(0.5)

    crate_list = ice_dev.getRacksAlive()
    if crate_nr >= 0 :
        msg = 'Crate nr: %d of the Icepap host: ' % crate_nr + \
              '%s is being reset.' % icepap_host 
        if crate_nr in crate_list:
            cmd = "RESET %d" % crate_nr
        else:
            self.error('The crate number is not valid')
            return
    else:
        msg = 'Icepap host: %s is being reset.' % icepap_host
        cmd = "RESET"
    
    driver_list = ice_dev.getDriversAlive()
    if crate_nr >=0:
        nr = crate_nr
        driver_list= [i for i in driver_list if i>(nr*10) and i<=(nr*10+8)]
    
    status_message = ''
    for driver in driver_list:
        status_message += 'Axis: %d\nStatus: %s\n' % \
                                        (driver,ice_dev.getVStatus(driver))
    
    pool_obj.SendToController([icepap_ctrl.getName(),cmd])
    msg += ' It will take aprox. 3 seconds...'
    self.info(msg)

    try: 
        efrom, eto = getResetNotificationAuthorAndRecipients(self)
    except Exception, e:
        self.warning(e)
        return

    ms = self.getMacroServer()
    ms_name = ms.get_name()
    efrom = '%s <%s>' % (ms_name,efrom)
    subject = SUBJECT % icepap_host
    ctrl_name = icepap_ctrl.getName()
    message =  'Macro: %s(%s)\n' % (self.getName(), ctrl_name)
    message += 'Pool name: %s\n' % pool_obj.name()
    message += 'Controller name: %s\n' % ctrl_name
    message += 'Icepap host: %s\n' % icepap_host
    if crate_nr >= 0:
        message += 'Crate: %d\n' % crate_nr
    message += status_message
    sendMail(efrom, eto, subject, message)
    self.info('Email notification was send to: %s' % eto)
    # waiting 3 seconds so the Icepap recovers after the0 reset
    # it is a dummy wait, probably it could poll the Icepap 
    # and break if the reset is already finished
    waitSeconds(self, 3)

def _getPoolObj(pool_element):
    db = pool_element.get_device_db()
    db_proxy = PyTango.DeviceProxy((pool_element.get_device_db()).dev_name())
    info = db_proxy.DbGetDeviceInfo(pool_element.dev_name())
    server_name_element = info[1][3] #array, the second element is a str list.
    pool_exported_list = db.get_device_exported_for_class('Pool').value_string
    count = 0
    for pool_exported in pool_exported_list:
        info = db_proxy.DbGetDeviceInfo(pool_exported)
        server_name_pool = info[1][3] #array, the second element is a str list.
        if server_name_element == server_name_pool:
            count +=1
            pool_name = pool_exported

    if count != 1:
        raise Exception('There are more than one instance of the Pool')
    pool_proxy = PyTango.DeviceProxy(pool_name)

    return pool_proxy 

#class ipap_homing(Macro):
    """Macro to do the homing procedure in more than one axis at the same time.
       Given a list of motors to do the home and the direction (in pool motor sense) in which you want
       to move, this macro will move all the motors at the same time waiting to 
       recieve the home signal.
       The macro ends when the home signal is detected or any axis receive an alarm
    """

