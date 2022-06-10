#!/usr/bin/env python
"""
command line interface to the Eiger2 detectors
"""
import HasyUtils
from sardana.macroserver.macro import Macro, Type

class eigerCli(Macro):
    """
    eigerCli name --ints         write EigerPars_<name> then execute internal trigger run
    eigerCli name --exts         write EigerPars_<name> then execute external trigger run
    eigerCli name --extssim      write EigerPars_<name> then execute simulated external trigger run (using oreg)

    eigerCli name --list         list files in the DCU  ( if HiDRA is offline)
    eigerCli name --delete       delete files in the DCU ( if HiDRA is offline)
    eigerCli name --download     download files from the DCU ( if HiDRA is offline)

    eigerCli name --init         sets some Eiger attributes to defaults

    eigerCli name --display      display parameter as stored in EigerPars_<name> (env. dict.)
    eigerCli name --read         read detector attributes
    eigerCli name --write        write parameters from EigerPars_<name> to detector

    set EigerPars_<name> and write to detector
      eigerCli name --ct <value>  CountTime
      eigerCli name --et <value>  EnergyThreshold
      eigerCli name --ipf <value> ImagesPerFile
      eigerCli name --nbi <value> NbImages
      eigerCli name --nbt <value> NbTriggers
      eigerCli name --pf <value>  Prefix
      eigerCli name --tm <value>  TriggerMode: 'ints' or 'exts'

    names: p02e2x4m p06p029racke4m p07e2x4m p08e2x1m p10e4m p10e500 p11e2x16m p21e2x4m p62e2x4m p62e2x9m
    """
    param_def = [
        [ 'name', Type.String, None, 'Detector name'],
        [ 'selector', Type.String, None, 'e.g.: --list, --nbt, --nbi'],
        [ 'value', Type.String, 'NONE', 'a value']]

    def run(self, name, selector, value):

        self.eiger = HasyUtils.TgUtils.Eiger( name, self)

        if selector == 'default':
            self.eiger.setDefaults()
            return
        #
        # DCU actions
        #
        if selector == '--delete':
            self.eiger.crawler( self.eiger.dataURL, self.eiger.deleteFunc)
            self.eiger.crawler( self.eiger.dataURL, self.eiger.deleteDirFunc)
            return
        if selector == '--download':
            self.eiger.crawler( self.eiger.dataURL, self.eiger.downloadFunc)
            return
        if selector == '--list':
            self.eiger.crawler( self.eiger.dataURL, self.eiger.listFunc)
            return

        if selector == '--display':
            self.eiger.displayEigerPars()
            return
        #
        # detector actions
        #
        if selector == '--init':
            self.eiger.initDetector()
            return
        if selector == '--read':
            self.eiger.readDetector()
            return
        if selector == '--write':
            self.eiger.writeAttrs()
            self.eiger.readDetector()
            return

        #
        # runs
        #
        if selector == '--ints':
            self.eiger.runInts()
            return
        if selector == '--exts':
            self.eiger.runExts( True)
            return
        if selector == '--extssim':
            self.eiger.runExts( False)
            return
        #
        # detector and filewrite atttributes
        #
        flag = True
        if selector == '--ct':
            self.eiger.storeVar( 'CountTime', float( value))
        elif selector == '--et':
            self.eiger.storeVar( 'EnergyThreshold', float( value))
        elif selector == '--ipf':
            self.eiger.storeVar( 'ImagesPerFile', int( value))
        elif selector == '--nbi':
            self.eiger.storeVar( 'NbImages', int( value))
        elif selector == '--nbt':
            self.eiger.storeVar( 'NbTriggers', int( value))
        elif selector == '--pe':
            self.eiger.storeVar( 'PhotonEnergy', float( value))
        elif selector == '--pf':
            self.eiger.storeVar( 'Prefix', str( value))
        elif selector == '--tm':
            self.eiger.storeVar( 'TriggerMode', str( value))
        else:
            self.output( "eigerCli: failed to identify %s" % selector)
            flag = False

        if flag:
            self.eiger.writeAttrs()
            self.eiger.readDetector()

        return
