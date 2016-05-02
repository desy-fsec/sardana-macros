#!/usr/bin/env python

"""
Utility macros specifically developed for Alba BL29 Boreas beamline
"""

import PyTango

from sardana.macroserver.macro import Macro, Type, ParamRepeat

class speak(Macro):
    """
    """

    SPEAK_DEV = 'BL29/CT/VOICE'

    param_def = [
        ['words', ParamRepeat(['word',  Type.String, None, 'one word']), [''],
            'words forming the phrase to be played']
    ]

    def run(self,*words):
        speech = ' '.join(words)
        self.output(speech)
        speech_dev = PyTango.DeviceProxy(self.SPEAK_DEV)
        speech_dev.command_inout('Play_Sequence',speech)
