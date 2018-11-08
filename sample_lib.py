from sardana.macroserver.macro import Macro, Type
import taurus

class snapshot(Macro):
    param_def = [ [ 'imgfn', Type.String, '/beamlines/bl13/commissioning/temp/snapshot.jpg', 'Image file name to generate'],
                ]

    def run(self, imgfn):

        import sample
        from bl13constants import OAV_device_name
        sample.snapshot(OAV_device_name,imgfn)
        return

