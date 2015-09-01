#!/usr/bin/env python
# 
__all__ = ["ppPurge"]

from sardana.macroserver.macro import Macro, Type
import HasyUtils
import os, shutil

class ppPurge(Macro):
    """
    post-processing for diffraction measurements:
    - purges /ScanDir/prefix_01234.fio
    - purges images in /ScanDir/<scanName>/<detector>
      + scanName = <prefix>_<ScanID>
      + prefix = ScanFile.split('.')[0]
    - saves the original files in /ScanDir/saves
    - processes the most recent files, if scanID is not specified

    Environment variables: ScanDir, ScanFile, ScanID
    """

    result_def = [['result', Type.Boolean, None, 'ppPurge return status']]
    param_def = [['scanID', Type.Integer,  -1, 'Overrides the env-variable ScanID (optional)']]

    def _walkLevel( self, some_dir, level=1):
        some_dir = some_dir.rstrip(os.path.sep)
        if not os.path.isdir(some_dir):
            self.writer( "ppPurge._walkLevel %s not a directory" % some_dir)
            
        num_sep = some_dir.count(os.path.sep)
        for root, dirs, files in os.walk(some_dir):
            yield root, dirs, files
            num_sep_this = root.count(os.path.sep)
            if num_sep + level <= num_sep_this:
                del dirs[:]

    def _prepareFileNames( self, scanID):

        self.scanDir = HasyUtils.getEnv( 'ScanDir')
        if scanID == -1: 
            scanID = int(self.getEnv( 'ScanID'))
        self.scanId = scanID

        self.scanFile = HasyUtils.getEnv( 'ScanFile')
        if type( self.scanFile) is list:
            self.scanFile = self.scanFile[0]
        
        prefix, ext = self.scanFile.split( '.')
        if ext != 'fio':
            self.writer( "scanFile %s has the wrong extension (NOT fio)")
            return False

        self.scanName = "%s_%05d" % (prefix, scanID)
        self.imageRootDir = self.scanDir + "/" + self.scanName
        self.detectorDirs = []
        filesTemp = []
        for rootDir, subDirs, files in self._walkLevel( self.imageRootDir, level=0):
            filesTemp.extend( files)
            for sDir in subDirs:
                self.detectorDirs.append( rootDir + "/" + sDir)
        #
        # get MCA files, make sure they begin with <scanName>_mca_s
        #
        self.mcaFiles = []
        mcaPattern = self.scanName + "_mca_s"
        for elm in filesTemp:
            if elm.find( mcaPattern) == 0:
                self.mcaFiles.append( self.imageRootDir + "/" + elm)

        return True
        
    def _saveAllFiles( self): 
        """
        save the files: .fio, MCA, images
        """
        fioFile = "%s/%s.fio" % ( self.scanDir, self.scanName)
        saveDir = "%s/saved" % ( self.scanDir)
        if not os.path.isdir( saveDir):
            os.mkdir( saveDir)
        shutil.copy( fioFile, saveDir)
        self.writer( "saved %s in %s" % (fioFile, saveDir))
        #
        # save the mca and image files
        #
        if os.path.isdir( "%s/%s" % (self.scanDir, self.scanName)):
            shutil.copytree( "%s/%s" % (self.scanDir, self.scanName),
                             "%s/saved/%s" % (self.scanDir, self.scanName))
            self.writer( "saved mca and image files in %s/saved/%s" % (self.scanDir, self.scanName))
        return True

    def _findDoubles( self):
        """
        find doubles in, e.g., /<ScanDir>/<scanName>.fio
        """
        fioFile = "%s/%s.fio" % ( self.scanDir, self.scanName)
        fioObj = HasyUtils.fioReader( fioFile)
        #
        # find the indices of the doubles
        #
        self.iDoubles = []
        x = fioObj.columns[0].x
        self.lenOrig = len( x)
        for i in range( len( x) - 1):
            if x[i] == x[i + 1]:
                self.iDoubles.append( i)
        if len( self.iDoubles) == 0:
            self.output( "ppPurge: nothing to purge in %s" % fioFile)
            return False

        self.writer( "Doubles %s (index starts at 0)" % str(self.iDoubles))
        return True

    def _purgeFioFile( self):
        """
        purges the contents of, e.g., /<ScanDir>/<scanName>.fio
        """

        fioFile = "%s/%s.fio" % ( self.scanDir, self.scanName)
        fioObj = HasyUtils.fioReader( fioFile)
        #        
        # we must not start to delete from the beginning so reverse the order
        #        
        self.iDoubles.reverse()
        for i in self.iDoubles:
            for col in fioObj.columns:
                del col.x[i]
                del col.y[i]
        #
        # and bring it back into the right order
        #
        self.iDoubles.reverse()
        #
        # create the new fio file 'in place'
        #
        os.remove( fioFile)
        HasyUtils.fioWriter( fioObj)
        self.writer( "ppPurge: created %s" % fioObj.fileName)
        return True

    def _purgeMCAFiles( self):
        """
        purges files, e.g. 
          /<ScanDir>/<scanName>/<scanName>_mca_s<no.>.fio
        """

        for i in self.iDoubles:
            fNameI = "%s/%s_mca_s%d.fio" % ( self.imageRootDir, self.scanName, i + 1)
            os.remove( fNameI)
            self.writer( "removed %s" % fNameI)
        count = 1
        for i in range( 1, self.lenOrig + 1):
            fNameCount = "%s/%s_mca_s%d.fio" % ( self.imageRootDir, self.scanName, count)
            fNameI = "%s/%s_mca_s%d.fio" % ( self.imageRootDir, self.scanName, i)
            if not os.path.exists( fNameI):
                continue
            if fNameI != fNameCount:
                if os.path.exists( fNameCount):
                    self.writer( "error: %s exists" %fNameCount)
                    return False
                os.rename( fNameI, fNameCount)
                self.writer( "renamed %s to %s " % ( fNameI, fNameCount))
            count += 1
        return True

    def _purgeImageFiles( self):
        """
        purges files in the directories, e.g. 
          /<ScanDir>/<scanName>/pilatus300k, 
          /<ScanDir>/<scanName>/pilatus1M, etc
        """
        for imageDir in self.detectorDirs:
            extension = None
            if imageDir.find( 'mythen') >= 0:
                extension = 'raw'
            elif imageDir.find( 'pilatus') >= 0:
                extension = 'cbf'
            else:
                self.output( "ppPurge: failed to identify detector %s " % (imageDir))
                return False
            #
            # remove the images that belong to the superfluous points
            # mind that the indices of the images start at 1
            #
            for i in self.iDoubles:
                fNameI = "%s/%s_%05d.%s" % ( imageDir, self.scanName, i + 1, extension)
                os.remove( fNameI)
                self.writer( "removed %s" % fNameI)

            count = 1
            for i in range( 1, self.lenOrig + 1):
                fNameCount = "%s/%s_%05d.%s" % ( imageDir, self.scanName, count, extension)
                fNameI = "%s/%s_%05d.%s" % ( imageDir, self.scanName, i, extension)
                if not os.path.exists( fNameI):
                    continue
                if fNameI != fNameCount:
                    if os.path.exists( fNameCount):
                        self.writer( "error: %s exists" %fNameCount)
                        return False
                    os.rename( fNameI, fNameCount)
                    self.writer( "renamed %s to %s " % ( fNameI, fNameCount))
                count += 1
        return True

    def run(self, scanID):

        #
        # do we have an open message window?
        #
        res = self.mwTest()
        if res.getResult():
            self.writer = self.mwOutput
        else:
            self.writer = self.output

        if not self._prepareFileNames( scanID):
            return False

        fioFile = "%s/%s.fio" % ( self.scanDir, self.scanName)
        if not os.path.exists( fioFile):
            self.writer( "%s does not exist" % fioFile)
            return False

        #
        # if the fioFiles has already been saved, assume that the work is done
        #
        fioFileSaved = "%s/saved/%s.fio" % ( self.scanDir, self.scanName)
        if os.path.exists( fioFileSaved):
            self.writer( "%s exists already, nothing to be done" % fioFileSaved)
            return False

        if not self._saveAllFiles():
            return False

        if not self._findDoubles():
            return False

        if not self._purgeFioFile():
            return False

        if not self._purgeMCAFiles():
            return False

        if not self._purgeImageFiles():
            return False

        return True
