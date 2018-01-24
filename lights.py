from sardana.macroserver.macro import Macro, Type
import taurus
import bl13constants
from bl13constants import FRONTLIGHT_MAXBRIGHTNESS as MB_FRONT
from bl13constants import BACKLIGHT_MAXBRIGHTNESS as MB_BACK
import time


class frontlight(Macro):

    """
    This macro is used to control the front light.
    The brightness is set from 0 to FRONTLIGHT_MAXBRIGHTNESS.
    """

    param_def = [ 
                  [ 'brightness', Type.Integer, -999, 'brightness: Off=0, Max=50']
                ]
   
    def run(self,brightness):
        flight_dev = taurus.Device('ioregister/eh_blightior_ctrl/2')
        brightness_val_init = flight_dev.read_attribute('brightness').value
        
        # Value 1 is OFF
        if brightness == 0: brightness = 1

        # ONLY READ VALUE
        if brightness == -999:
            if brightness_val_init == 1:
                self.info("Front light is OFF")
            else:
                self.info("Front light brightness %d" %int(brightness_val_init))
            return

        if brightness < 1 or brightness > MB_FRONT:
            self.info("Value must be between 0 and 50")
            return
        
        # Change Brightness value
        flight_dev.write_attribute('brightness', int(brightness))
        time.sleep(.5)        

        # Output final Brightness value
        brightness_val = flight_dev.read_attribute('brightness').value
        if brightness_val == 1:
            self.info("Front light is OFF")
        else:
            self.info("Front light brightness %d" %int(brightness_val))


class backlight(Macro):

    """
    NOT TO BE USED YET - ONLY MONITORING
    This macro is used to use the back light.
    The brightness is set from 0 to BACKLIGHT_MAXBRIGHTNESS.
    """

    param_def = [ 
                  [ 'brightness', Type.Integer, -999, 'brightness: Off=0, Max=50']
                ]
   
    def run(self,brightness):
        blight_dev = taurus.Device('ioregister/eh_blightior_ctrl/1')
        brightness_val = blight_dev.brightness
        blight_onoff = blight_dev.value
        
        # Value 1 is OFF
        if brightness == 0: blight_dev.value = 0

        if brightness < 1 or brightness > MB_BACK:
            self.info("Value must be between 0 and %d" % MB_BACK)
            return
                
        # Change Brightness value
        blight_dev.write_attribute('brightness', int(brightness))
        
        if blight_dev.value == 0:
            self.info("Back light is OFF")
        else:
            self.info("Back light brightness %d" %int(brightness_val))

