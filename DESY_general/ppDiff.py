#!/usr/bin/env python
# 
__all__ = ["ppDiff"]

from sardana.macroserver.macro import Macro, Type
import HasyUtils
import os, shutil

class ppDiff(Macro):
    """
    post-processing for diffraction measurements:
    - removes doubles from /ScanDir/prefix_01234.fio and /ImageRootDir/prefix_01234/<imageFiles>
    - saves the original files in /ScanDir/saves and /ImageRootDir/saves
    - processes the most recent files, if scanID is not specified

    Environment variables: ScanDir, ImageRootDir, ScanFile, ScanID
    """
    param_def = [
        ['detector',   Type.String,  None, 'Detector: none, mythen, pilatus300k, pilatus1m'],
        ['scanID',   Type.Integer,  -1, 'Overrides the env-variable ScanID (optional)'],
        ]

    def run(self, detector, scanID):

        detectors = ['none', 'mythen', 'pilatus300k', 'pilatus1m']

        if detector not in detectors:
            self.output( "ppDiff: failed to identify detector, can be %s " % str(detectors))
            return

        imageRootDir = self.getEnv( 'ImageRootDir')
        if imageRootDir is None: 
            self.output( "ppDiff: no ImageRootDir")
            return
            
        scanDir = self.getEnv( 'ScanDir')
        scanFile = self.getEnv( 'ScanFile')
        if type( scanFile) is list:
            for f in scanFile:
                if f.find( '.fio') > 0:
                    scanFile = f

        if scanID == -1: 
            scanID = int(self.getEnv( 'ScanID'))
        
        prefix, ext = scanFile.split( '.')

        if ext != 'fio':
            self.output( "scanFile %s has the wrong extension (NOT fio)")
            return

        fioFile = "%s/%s_%05d.fio" % ( scanDir, prefix, scanID)
        if not os.path.exists( fioFile):
            self.output( "%s does not exist" % fioFile)
            return

        imageDir = "%s/%s_%05d_%s" % ( imageRootDir, prefix, scanID, detector)
        #
        # if the fioFiles has already been saved, assume that the work is done
        #
        fioFileSaved = "%s/saved/%s_%05d.fio" % ( scanDir, prefix, scanID)
        if os.path.exists( fioFileSaved):
            self.output( "%s exists already, nothing to be done" % fioFileSaved)
            return
        #
        # save the .fio files
        #
        savesFioDir = "%s/saved" % ( scanDir)
        if not os.path.isdir( savesFioDir):
            os.mkdir( savesFioDir)
        shutil.copy( fioFile, savesFioDir)
        self.output( "saved %s in %s" % (fioFile, savesFioDir))
        #
        # save the image files
        #
        if detector != 'none':
            savesImageDir = "%s/saved" % ( imageRootDir)
            if not os.path.isdir( savesImageDir):
                os.mkdir( savesImageDir)
            if os.path.isdir( imageDir):
                shutil.copytree( imageDir, "%s/%s_%05d_%s" % (savesImageDir, prefix, scanID, detector))
                self.output( "saved images in %s" % (savesImageDir))

        fioObj = HasyUtils.fioReader( fioFile)
        #
        # find the indices of the doubles
        #
        iDoubles = []
        x = fioObj.columns[0].x
        lenOrig = len( x)
        for i in range( len( x) - 1):
            if x[i] == x[i + 1]:
                iDoubles.append( i)
        if len( iDoubles) == 0:
            self.output( "No doubles found")
            return

        self.output( "Doubles %s" % str(iDoubles))
        #        
        # we must not start to delete from the beginning so revers the order
        #        
        iDoubles.reverse()
        for i in iDoubles:
            for col in fioObj.columns:
                del col.x[i]
                del col.y[i]
        #
        # create the new fio file 'in place'
        #
        os.remove( fioFile)
        HasyUtils.fioWriter( fioObj)
        self.output( "ppDiff: created %s" % fioObj.fileName)

        if not os.path.isdir( imageDir):
            self.output( "No images need to be processed")
            return

        if detector == 'none': 
            self.output( "No detector specified")
            return
        #
        # remove the images that belong to the superfluous points
        # mind that the indices of the images start at 1
        #
        iDoubles.reverse()
        for i in iDoubles:
            fNameI = "%s/%s_%05d_%d.raw" % ( imageDir, prefix, scanID, i + 1)
            os.remove( fNameI)
            self.output( "removed %s" % fNameI)

        count = 1
        for i in range( 1, lenOrig + 1):
            fNameCount = "%s/%s_%05d_%d.raw" % ( imageDir, prefix, scanID, count)
            fNameI = "%s/%s_%05d_%d.raw" % ( imageDir, prefix, scanID, i)
            if not os.path.exists( fNameI):
                continue
            if fNameI != fNameCount:
                if os.path.exists( fNameCount):
                    self.output( "error: %s exists" %fNameCount)
                    return
                os.rename( fNameI, fNameCount)
                self.output( "renamed %s to %s " % ( fNameI, fNameCount))
            count += 1
