#!/usr/bin/env python
# 
# some change
from sardana.macroserver.macro import *
from sardana.macroserver.macro import macro
from optparse import OptionParser
import PyTango
import sys, time

class fioColumn:
    '''
    the class represents a column of a FIO file. The first column is the
    x-axis which is used by all columns, name_in, e.g. test_00001_C1
    '''
    def __init__(self, name_in):
        self.name = name_in
        lst = self.name.split('_')
        if len(lst) > 1:
            self.deviceName = lst[-1]
            if self.deviceName.find( "0") == 0:
                self.deviceName = "ScanName"
        else:
            self.deviceName = "n.n."
        self.x = []
        self.y = []
        return

class fileObj:
    '''
    represents an entire file with several columns
    '''
    def __init__(self, ms):
        self.comments = []
        self.user_comments = []
        self.parameters = []
        self.columns = []
        self.ms = ms
        self.fileName = self._makeFileName()
        if self.fileName.find( 'fio') > 0:
            if not self._readFio():
                return 
        else:
            ms.output( "fileObj: file format unknown")
            return
        #
        # /home/p12user/dirName/gen_00001.fio -> gen_00001
        #
        self.scanName = self.fileName.split("/")[-1].split(".")[0]
        return

    def _makeFileName( self):

        #
        # 
        # the file name is constructed from ScanDir, ScanFile and ScanID
        #
        temp = "%05d" % int(self.ms.getEnv( "ScanID"))
        #
        # sometimes ScanFile is a one-element list instead of an array
        #
        var = self.ms.getEnv( "ScanFile")
        lst = []
        if type(var).__name__ == 'list':
            lst = var[0].split(".")
        else:
            lst = var.split(".")
        argout = self.ms.getEnv( 'ScanDir') + "/" + lst[0] + "_" + temp + "." + lst[1]
        return argout

    def _readFio( self):
        '''
        !
        ! user comments
        !
        %c
        comments
        %p
        parameterName = parameterValue
        %d
        Col 1 AU_ALO_14_0001  FLOAT 
        Col 2 AU_ALO_14_0001  FLOAT 
        Col 3 AU_ALO_14_0001_RING  FLOAT 
        data data data etc.
        '''
        self.ms.output( "readFio: reading %s", self.fileName)
        try:
            inp = open( self.fileName, 'r')
        except IOError as e:
            self.ms.output ( "failed to open %s" % self.fileName)
            return False
        lines = inp.readlines()
        inp.close()
        flagComment = 0
        flagParameter = 0
        flagData = 0
        for line in lines:
            line = line.strip()
            if line.find( "!") == 0:
                self.user_comments.append( line)
                flagComment, flagParameter, flagData = False, False, False
            elif line.find( "%c") == 0:
                flagComment, flagParameter, flagData = True, False, False
                continue
            elif line.find( "%p") == 0:
                flagComment, flagParameter, flagData = False, True, False
                continue
            elif line.find( "%d") == 0:
                flagComment, flagParameter, flagData = False, False, True
                continue
            #
            if flagComment:
                self.comments.append( line)
            #
            # parName = parValue
            #
            if flagParameter:
                lst = line.split( "=")
                self.parameters.append( {lst[0]: lst[1]})
            if not flagData:
                continue
            lst = line.split()
            if lst[0] == "Col":
                #
                # the 'Col 1 ...' description does not create a
                # new FIO_dataset because it contains the x-axis for all
                #
                if lst[1] == "1":
                    pass
                else:
                    self.columns.append( fioColumn( lst[2]))
            else:
                for i in range(1, len( self.columns)):
                    self.columns[i-1].x.append( float(lst[0]))
                    self.columns[i-1].y.append( float( lst[i]))
        return True

    def posMax( self, counterName, mode):
        '''
        find the counterName column and call the function 
        that returns the peak position (x, y)
        '''
        for col in self.columns:
            if col.name == counterName:
                if mode == "peak":
                    return self.posMaxPeak( col)
                else:
                    self.ms.output( "posMax: Failed to identify mode %s" % mode)
                    return (None, None)

    def posMaxPeak( self, col):
        maxX = None
        maxY = None
        self.ms.output( "analysing column %s" % ( col.name))
        for i in range( len( col.y)):
            #self.ms.output( "ckecking %d %g %g" % ( i, col.x[i], col.y[i]))
            if maxY is None or col.y[i] > maxY:
                maxY = col.y[i]
                maxX = col.x[i]
        return (maxX, maxY)
        
class mvsa(Macro):
    """    Reads the most recent output file and moves a motor 
    to the maximum of the column defined by SignalCounter.

    Used environment variables: 
      ScanDir, ScanFile, ScanID  -> file name
      ScanHistory                -> motor name
      SignalCounter              -> counter name"""
    param_def = [
        ['mode', Type.String, "peak", 'CEN: enter of mass, PEAK: maximum, STEP: cms of positive derivative'],
        ]
    interactive = True

    def run(self, mode):
        a = fileObj( self)
        counterName = self.getEnv( "SignalCounter")
        (maxX, maxY) = a.posMax( counterName, mode)
        if maxX == None:
            self.output( "mvsa: failed to find the maximum for %s" % ( a.fileName))
            return
        
        motorName = self.getEnv( "ScanHistory")[-1]['title'].split()[1] 
        motorProxy = PyTango.DeviceProxy( motorName)
        answer = self.input( "Move %s from %g to %g (%s Signal: %g) :" % 
                             (motorName, motorProxy.Position, maxX, counterName, maxY))
        if answer == "yes":
            motorProxy.write_attribute( "Position", maxX)
            while motorProxy.State() == PyTango.DevState.MOVING:
                time.sleep( 0.1)
            self.output( "Motor %s now at %g" % (motorName, motorProxy.Position))
        else:
            self.output( "%s not moved" % motorName)

