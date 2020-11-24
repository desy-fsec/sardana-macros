#!/usr/bin/env python
#
from sardana.macroserver.macro import Macro
from sardana.macroserver.macro import Type
import HasyUtils
import os
__all__ = ["ppPurge"]

class ppPurge(Macro):
    """
    post-processing-purge on data that have been taken with the
    repeat-on-condition feature. The .fio file is used to
    find the points with identical x-values. The invalid points
    are removed and also the invalid MCA files and images.
    - purges /<ScanDir>/prefix_01234.fio
    - purges MCA files /<ScanDir>/<scanName>
    - purges images in /<ScanDir>/<scanName>/<detector>
    - processes the most recent files, if scanID is not specified

    Environment variables: ScanDir, ScanFile, ScanID

    Here is an example for a directory structure that is ppPurge-compliant.

      <ScanDir> == /gpfs/current/raw

      the .fio file
        /gpfs/current/raw/au_00456.fio
      the MCA files:
        /gpfs/current/raw/au_00456/au_00456_mca_s1.fio
        /gpfs/current/raw/au_00456/au_00456_mca_s2.fio
        ...
      the images
        /gpfs/current/raw/au_00456/pilatus300k/au_00456_00001.cbf
        /gpfs/current/raw/au_00456/pilatus300k/au_00456_00002.cbf
       ...
        /gpfs/current/raw/au_00456/pilatus1M/au_00456_00001.cbf
        /gpfs/current/raw/au_00456/pilatus1M/au_00456_00002.cbf
       ...

    The names pilatus300k and pilatus1M are defined, e.g., by the
    vc_exectutor script (see the DESY Sardana/Spock/Taurus manual).
    They can be chosen at will.
    """

    result_def = [['result', Type.Boolean, None, 'ppPurge return status']]
    param_def = [['scanID', Type.Integer, -1, 'Overrides the env-variable ScanID (optional)']]

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
            self.output( "ppPurge._prepareFileNames: scanFile %s has the wrong extension (NOT fio)")
            return False

        self.scanName = "%s_%05d" % (prefix, scanID)

        logFile = self.scanDir + "/" + self.scanName + "_ppPurge.log"
        if os.path.isfile( logFile):
            self.output( "ppPurge: %s exists already" % logFile)
            self.output( "ppPurge: file retained, ppPurge aborted")
            return False

        self.imageRootDir = self.scanDir + "/" + self.scanName
        self.detectorDirs = []
        filesTemp = []
        for rootDir, subDirs, files in HasyUtils.walkLevel( self.imageRootDir, level=0):
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
            self._writer( "\nppPurge: nothing to purge in %s\n" % fioFile)
            return False

        self._writer( "ppPurge: Doubles %s (index starts at 0)" % str(self.iDoubles))
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
        self._writer( "ppPurge: re-created %s" % fioObj.fileName)
        return True

    def _purgeMCAFiles( self):
        """
        purges files, e.g.
          /<ScanDir>/<scanName>/<scanName>_mca_s<no.>.fio
        """

        if not os.path.isfile( "%s/%s_mca_s1.fio" % ( self.imageRootDir, self.scanName)):
            self._writer( "ppPurge: no MCA files found")
            return True

        countRemove = 0
        for i in self.iDoubles:
            fNameI = "%s/%s_mca_s%d.fio" % ( self.imageRootDir, self.scanName, i + 1)
            os.remove( fNameI)
            self._writer( "removed %s\n" % fNameI)
            countRemove += 1
        self._writer( "ppPurge: removed %d MCA files in %s" % (countRemove, self.imageRootDir))

        count = 1
        for i in range( 1, self.lenOrig + 1):
            fNameCount = "%s/%s_mca_s%d.fio" % ( self.imageRootDir, self.scanName, count)
            fNameI = "%s/%s_mca_s%d.fio" % ( self.imageRootDir, self.scanName, i)
            if not os.path.exists( fNameI):
                continue
            if fNameI != fNameCount:
                if os.path.exists( fNameCount):
                    self._writer( "ppPurge._purgeMCAFiles:error: %s exists" % fNameCount)
                    return False
                os.rename( fNameI, fNameCount)
            count += 1
        self._writer( "ppPurge: MCA files purge DONE")
        return True

    def _purgeImageFiles( self):
        """
        purges files in the directories, e.g.
          /<ScanDir>/<scanName>/pilatus300k,
          /<ScanDir>/<scanName>/pilatus1M, etc
        """

        if len( self.detectorDirs) == 0:
            self._writer( "ppPurge: no image dirs ")
            return True

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
            countRemove = 0
            for i in self.iDoubles:
                fNameI = "%s/%s_%05d.%s" % ( imageDir, self.scanName, i + 1, extension)
                os.remove( fNameI)
                self._writer( "removed %s\n" % fNameI)
                countRemove += 1
            self._writer( "ppPurge: removed %d files in %s" % (countRemove, imageDir))

            count = 1
            for i in range( 1, self.lenOrig + 1):
                fNameCount = "%s/%s_%05d.%s" % ( imageDir, self.scanName, count, extension)
                fNameI = "%s/%s_%05d.%s" % ( imageDir, self.scanName, i, extension)
                if not os.path.exists( fNameI):
                    continue
                if fNameI != fNameCount:
                    if os.path.exists( fNameCount):
                        self._writer( "ppPurge._purgeImageFiles:error: %s exists" % fNameCount)
                        return False
                    os.rename( fNameI, fNameCount)
                count += 1
        self._writer( "ppPurge: image files purge DONE")
        return True

    def _writer( self, msg):

        if not hasattr( self, 'writer'):
            #
            # send the output to the info stream
            self.writer = self.info
            #
            # do not overwrite an existing log file
            #
            logFile = self.scanDir + "/" + self.scanName + "_ppPurge.log"
            if os.path.isfile( logFile):
                self.writer( "ppPurge: %s exists already, retained" % logFile)
                self.logFile = None
            else:
                self.logFile = open( logFile, 'w')

        self.writer( msg)
        if self.logFile is not None:
            self.logFile.write( msg + "\n")

    def run(self, scanID):

        if not self._prepareFileNames( scanID):
            return False

        fioFile = "%s/%s.fio" % ( self.scanDir, self.scanName)
        if not os.path.exists( fioFile):
            self._writer( "ppPurge: %s does not exist" % fioFile)
            return False

        if not self._findDoubles():
            if self.logFile is not None:
                self.logFile.close()
            return False

        if not self._purgeFioFile():
            if self.logFile is not None:
                self.logFile.close()
            return False

        if not self._purgeMCAFiles():
            if self.logFile is not None:
                self.logFile.close()
            return False

        if not self._purgeImageFiles():
            if self.logFile is not None:
                self.logFile.close()
            return False

        if self.logFile is not None:
            self.logFile.close()

        return True
