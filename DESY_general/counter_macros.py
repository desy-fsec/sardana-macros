"""Change motor limits for Hasy motors"""

from __future__ import print_function

__all__ = ["resaco"]

import PyTango
from sardana.macroserver.macro import *
from sardana.macroserver.macro import macro

class resaco(Macro):
    """Reset counters in the Active MG"""

    def prepare(self):
        mnt_grp_name = self.getEnv('ActiveMntGrp')
        self.mnt_grp = self.getObj(mnt_grp_name, type_class=Type.MeasurementGroup)

    def run(self):
        if self.mnt_grp is None:
            self.error('ActiveMntGrp is not defined or has invalid value')
            return

        counters = self.mnt_grp.getCounters()

        for counter in counters:
            counter_dev = self.getObj(counter['name'])
            counter_td = PyTango.DeviceProxy(counter_dev.TangoDevice)
            try:
                counter_td.Reset()
                self.info("Counter %s reseted"  % counter['name'])
            except:
                self.warning("Counter %s cannot be reseted" % counter['name'])
