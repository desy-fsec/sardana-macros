import time
import os
import Queue
import PyTango

from sardana.macroserver.macro import Macro, Type, ParamRepeat
from taurus.core.tango.sardana.pool import StopException
from macro_utils.slsdetector import SlsDetectorGet, SlsDetectorPut, SlsDetectorAcquire, SlsDetectorProgram
from macro_utils.macroutils import MntGrpController, SoftShutterController, MoveableController

def splitStringIntoLines(string, delimeter):
    '''Splits string into lines.'''

    splitted_lines = []
    lines = string.split(delimeter)
    for line in lines:
        if len(line) != 0:
            splitted_lines.append(line)
    return splitted_lines

class mythen_getThreshold(Macro):
    """Gets mythen threshold."""
    
    result_def =  [['threshold',Type.Integer, None, 'Threshold']]
    
    def prepare(self, *args, **kwargs):
        self.slsDetectorProgram = SlsDetectorGet(["threshold"])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        threshold = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: " + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if "threshold" in outLine:
                    #example of output: "threshold 10015"
                    try:
                        threshold = int(outLine.split()[1])
                    except Exception, e:
                        self.error("Could not parse '%s' output: %s" % (self.slsDetectorProgram.args, outLine))
                        raise e
                else:
                    self.output(outLine)
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if threshold is None:
            raise Exception("It was not able to retrieve threshold.")
        return threshold
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()
            
            
class mythen_setThreshold(Macro):
    """Sets mythen threshold."""
    
    param_def =  [['threshold',Type.Integer, None, 'Threshold']]
    result_def =  [['threshold',Type.Integer, None, 'Threshold']]
    
    def prepare(self, *args, **kwargs):
        threshold = str(args[0])
        self.slsDetectorProgram = SlsDetectorPut(["threshold", threshold])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        threshold = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: " + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
        
            if lenOutLine != 0:
                if "threshold" in outLine:
                    #example of output: "threshold 10015"
                    try:
                        threshold = int(outLine.split()[1])
                    except Exception, e:
                        self.error("Could not parse '%s' output: %s" % (self.slsDetectorProgram.args, outLine))
                        raise e
                else:
                    self.output(outLine)
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if threshold is None:
            raise Exception("It was not able to retrieve threshold.")        
        return threshold
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()
       
class mythen_getIndex(Macro):
    """Gets index of the next output file."""
    
    result_def =  [['index', Type.Integer, None, 'Index of the next output file']]
    
    def prepare(self, *args, **kwargs):
        self.slsDetectorProgram = SlsDetectorGet(["index"])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        index = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: " + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if "index" in outLine:
                    #example of output: "threshold 10015"
                    try:
                        index = int(outLine.split()[1])
                    except Exception, e:
                        self.error("Could not parse '%s' output: %s" % (self.slsDetectorProgram.args, outLine))
                        raise e
                else:
                    self.output(outLine)
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if index is None:
            raise Exception("It was not able to retrieve index.")
        return index
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()

class mythen_setIndex(Macro):
    """Sets new index for the output file."""
    
    param_def =  [['index', Type.Integer, None, 'New index of the next output file']]
    result_def =  [['index', Type.Integer, None, 'Index of the next output file']]
    
    def prepare(self, *args, **kwargs):
        index = str(args[0])
        self.slsDetectorProgram = SlsDetectorPut(["index", index])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        index = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: " + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if "index" in outLine:
                    #example of output: "index 1"
                    try:
                        index = int(outLine.split()[1])
                    except Exception, e:
                        self.error("Could not parse '%s' output: %s" % (self.slsDetectorProgram.args, outLine))
                        raise e
                else:
                    self.output(outLine)
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if index is None:
            raise Exception("It was not able to retrieve index.")
        return index
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()
            
class mythen_getOutFileName(Macro):
    """Gets name of the next output file."""
    
    result_def =  [['outFileName', Type.String, None, 'Name of the next output file']]
    
    def prepare(self, *args, **kwargs):
        self.slsDetectorProgram = SlsDetectorGet(["fname"])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        fileName = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: " + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if "fname" in outLine:
                    #example of output: "fname NAConMoedgeRh"
                    fileName = outLine.split()[1]
                else:
                    self.output(outLine)
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if fileName is None:
            raise Exception("It was not able to retrieve outFileName.")
        return fileName
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()
            
class mythen_setOutFileName(Macro):
    """Sets name of the next output file."""
    
    param_def =  [['outFileName', Type.String, None, 'New name of the next output file']]
    result_def =  [['outFileName', Type.String, None, 'Name of the next output file']]
    
    def prepare(self, *args, **kwargs):
        fileName = args[0]
        self.slsDetectorProgram = SlsDetectorPut(["fname", fileName])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        fileName = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: " + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if "fname" in outLine:
                    #example of output: "fname NAConMoedgeRh"
                    fileName = outLine.split()[1]
                else:
                    self.output(outLine)
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if fileName is None:
            raise Exception("It was not able to retrieve outFileName.")
        return fileName
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()

class mythen_getOutDir(Macro):
    """Gets name of the output directory."""
    
    result_def =  [['outDir', Type.String, None, 'Name of the output directory']]
    
    def prepare(self, *args, **kwargs):
        self.slsDetectorProgram = SlsDetectorGet(["outdir"])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        outDir = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: " + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if "outdir" in outLine:
                    #example of output: "fname NAConMoedgeRh"
                    outDir = outLine.split()[1]
                else:
                    self.output(outLine)
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if outDir is None:
            raise Exception("It was not able to retrieve outDir.")
        return outDir
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()
            
class mythen_setOutDir(Macro):
    """Sets name of the output directory."""
    
    param_def  =  [['outDir', Type.String, None, 'New name of the output directory']]
    result_def =  [['outDir', Type.String, None, 'Name of the output directory']]
    
    def prepare(self, *args, **kwargs):
        outDir = args[0]
        self.slsDetectorProgram = SlsDetectorPut(["outdir", outDir])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        outDir = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: " + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if "outdir" in outLine:
                    #example of output: "fname NAConMoedgeRh"
                    outDir = outLine.split()[1]
                else:
                    self.output(outLine)
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if outDir is None:
            raise Exception("It was not able to retrieve outDir.")
        return outDir
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()
            
class mythen_getExpTime(Macro):
    """Gets exposure time."""
    
    result_def =  [['expTime', Type.String, None, 'Exposure time [s]']]
    
    def prepare(self, *args, **kwargs):
        self.slsDetectorProgram = SlsDetectorGet(["exptime"])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        expTime = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: " + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if "exptime" in outLine:
                    #example of output: "fname NAConMoedgeRh"
                    try:
                        expTime = float(outLine.split()[1])
                    except Exception, e:
                        self.error("Could not parse '%s' output: %s" % (" ".self.slsDetectorProgram.args, outLine))
                        raise e
                else:
                    self.output(outLine)                
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if expTime is None:
            raise Exception("It was not able to retrieve expTime.")
        return expTime
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()            
            
class mythen_setExpTime(Macro):
    """Sets exposure time."""
    
    param_def  =  [['expTime', Type.String, None, 'New exposure time [s]']]
    result_def =  [['expTime', Type.String, None, 'Exposure time [s]']]
    
    def prepare(self, *args, **kwargs):
        expTime = str(args[0])
        self.slsDetectorProgram = SlsDetectorPut(["exptime", expTime])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        expTime = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: "  + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if "exptime" in outLine:
                    #example of output: "fname NAConMoedgeRh"
                    try:
                        expTime = float(outLine.split()[1])
                    except Exception, e:
                        self.error("Could not parse '%s' output: %s" % (" ".self.slsDetectorProgram.args, outLine))
                        raise e
                else:
                    self.output(outLine)
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if expTime is None:
            raise Exception("It was not able to retrieve expTime.")
        return expTime
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()

class mythen_getFlatFieldDir(Macro):
    """Gets name of the flat field directory."""
    
    result_def =  [['flatFieldDir', Type.String, None, 'Name of the flat field directory']]
    
    def prepare(self, *args, **kwargs):
        self.slsDetectorProgram = SlsDetectorGet(["ffdir"])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        flatFieldDir = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: "  + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if "ffdir" in outLine:
                    #example of output: "fname NAConMoedgeRh"
                    flatFieldDir = outLine.split()[1]
                else:
                    self.output(outLine)
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if flatFieldDir is None:
            raise Exception("It was not able to retrieve outDir.")
        return flatFieldDir
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()   
            
class mythen_setFlatFieldDir(Macro):
    """Sets name of the flat filed directory."""
    
    param_def =  [['flatFieldDir', Type.String, None, 'New name of the flat field directory']]
    result_def =  [['flatFieldDir', Type.String, None, 'Name of the flat field directory']]
    
    def prepare(self, *args, **kwargs):
        flatFieldDir = args[0]
        self.slsDetectorProgram = SlsDetectorPut(["ffdir", flatFieldDir])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        flatFieldDir = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: "  + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if "ffdir" in outLine:
                    #example of output: "fname NAConMoedgeRh"
                    flatFieldDir = outLine.split()[1]
                else:
                    self.output(outLine)
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if flatFieldDir is None:
            raise Exception("It was not able to retrieve outDir.")
        return flatFieldDir
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()   
            
class mythen_getFlatFieldFile(Macro):
    """Gets name of the flat field correction file.
       'none' - flat field correction is disabled"""
          
    result_def =  [['flatFieldFile', Type.String, None, 'Name of the flat field file']]
    
    def prepare(self, *args, **kwargs):
        self.slsDetectorProgram = SlsDetectorGet(["flatfield"])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        flatFieldFile = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: "  + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if "flatfield" in outLine:
                    #example of output: "fname NAConMoedgeRh"
                    flatFieldFile = outLine.split()[1]
                else:
                    self.output(outLine)
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if flatFieldFile is None:
            raise Exception("It was not able to retrieve outDir.")
        return flatFieldFile
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()

class mythen_setFlatFieldFile(Macro):
    """Sets name of the flat field correction file.
       'none' - disables flat field correction"""
    
    param_def =  [['flatFieldFile', Type.String, None, 'New name of the flat field file']]
    result_def =  [['flatFieldFile', Type.String, None, 'Name of the flat field file']]
    
    def prepare(self, *args, **kwargs):
        flatFieldFile = args[0]
        self.slsDetectorProgram = SlsDetectorPut(["flatfield", flatFieldFile])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        flatFieldFile = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: "  + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if "flatfield" in outLine:
                    #example of output: "fname NAConMoedgeRh"
                    flatFieldFile = outLine.split()[1]
#                else:
#                    self.output(outLine)
            if lenErrLine != 0:
                if "flatfield" in errLine:
                    #example of output: "fname NAConMoedgeRh"
                    flatFieldFile = errLine.split()[1]
#                else:
#                    self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if flatFieldFile is None:
            raise Exception("It was not able to retrieve outDir.")
        return flatFieldFile
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()
            
class mythen_setPositions(Macro):
    """Sets positions."""
    
    param_def = [['positions', ParamRepeat(['position', Type.Float, None, 'Position to be moved'],min=0), None, 'Positions']]
    result_def = [['positions', Type.String, None, 'Position to be moved']]
    
    def prepare(self, *args, **kwargs):
        self.positions = args
        self.nrOfPositions = len(self.positions)
        positions = map(str,self.positions)        
        nrOfPositions = str(self.nrOfPositions)
        args = ["positions", nrOfPositions]
        args += positions
        self.slsDetectorProgram = SlsDetectorPut(args)

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        positions = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: "  + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if "positions" in outLine:
                    #example of output: "positions 2 -10.00000 -20.00000"
                    try:
                        _positions = outLine.split()
                        nrOfPositions = int(_positions[1])
                        if nrOfPositions > 0:
                            positions = _positions[2:]
                            self.output(positions)
                            positions = map(float,positions)
                        else:
                            positions = []
                    except Exception, e:
                        self.error("Could not parse '%s' output: %s" % (" ".self.slsDetectorProgram.args, outLine))
                        raise e
                else:
                    self.output(outLine)
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if positions is None:
            raise Exception("It was not able to retrieve positions.")
        #self.output(positions)
        return repr(positions)
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()

class mythen_getPositions(Macro):
    """Gets positions."""
    
    result_def = [['positions', Type.String, None, 'Positions to move']]
    
    def prepare(self, *args, **kwargs):
        self.slsDetectorProgram = SlsDetectorGet(["positions"])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        positions = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: "  + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if "positions" in outLine:
                    #example of output: "fname NAConMoedgeRh"
                    _positions = outLine.split()
                    nrOfPositions = _positions[1]
                    if nrOfPositions > 0:
                        positions = _positions[2:]
                        try:
                            positions = map(float,positions)
                        except Exception, e:
                            self.error("Could not parse '%s' output: %s" % (" ".self.slsDetectorProgram.args, outLine))
                            raise e
                    else:
                        positions = []
                else:
                    self.output(outLine)
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if positions is None:
            raise Exception("It was not able to retrieve positions.")
        return repr(positions)
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()
                        
class mythen_acquire(Macro):
    """Acquires images with mythen detector. If positions are set it will go to positions and acquire one frame per position."""
    
    result_def = [['OutFile', Type.String, None, 'Full path to the output file'],
                  ['Positions', Type.String, None, 'Positions where acquisition took place']]

    POSITION_STR = 'Current position is'
    MOTOR_NAME = 'pd_mc'

    FILTERS = ['Current position is', ' %', 'ERROR:']

    def _obtainPositionFromLine(self, line):
        '''parse output/error lines for existence of current positions'''

        position = None
        if self.POSITION_STR in line:
           str_parts = line.split(self.POSITION_STR)
           position_str = str_parts[1]
           try:
               position = float(position_str)
           except ValueError, e:
               self.debug('Position present in the positions string line had an invalid literal.')
        return position
 
    def _splitStringIntoLines(self, string):
        '''split string into lines'''
        lines = []
        cr_splitted_strings = splitStringIntoLines(string, '\r')
        for string in cr_splitted_strings:
            nl_splitted_lines = splitStringIntoLines(string, '\n')
            lines.extend(nl_splitted_lines)
        return lines

    def _isInfoLine(self, line):
        '''filters output/error line for existence of interesting info'''        
        for filter in self.FILTERS:
            if filter in line:
                return True
        return False
        
    def prepare(self, *args, **kwargs):
        #self.slsDetectorProgram = SlsDetectorAcquire([])       
        self.stdOutQueue = Queue.Queue()
        self.stdErrQueue = Queue.Queue()
        self.slsDetectorProgram = SlsDetectorProgram([], "sls_detector_acquire", self.stdOutQueue, self.stdErrQueue)
        
    def run(self, *args, **kwargs):
        positions_str = self.execMacro('mythen_getPositions').getResult()
        positions = eval(positions_str)
        positions_len = len(positions)
        current_positions = []
        
        if positions_len == 0:
            self.motor=None
        else:
            #this call ensures us that the motor will get aborted 
            #when macro gets aborted
            self.getMotion([self.MOTOR_NAME])
            motor = self.getMotor(self.MOTOR_NAME)
            is_motor_powered = motor.read_attribute('poweron').value
            if not is_motor_powered:
                raise Exception('Motor: %s is powered off.' % self.MOTOR_NAME)
            self.warning("Motor: %s will move to %s" % (self.MOTOR_NAME, repr(positions)))
        
        self.slsDetectorProgram.execute()
        
        while True:
            self.checkPoint()
            try:
                output = None
                output = self.stdOutQueue.get(timeout=.1)
            except Queue.Empty, e:
                pass
            except StopException, e:
                raise e
            except Exception, e:
                self.error("Exception when reading from sls_detector_acquire standard output. Exiting...")
                raise e
            
            try:
                error = None
                error = self.stdErrQueue.get(timeout=.1)
            except Queue.Empty, e:
                pass
            except StopException, e:
                raise e
            except Exception, e:
                self.error("Exception when reading from sls_detector_acquire standard error. Exiting...")
                raise e
                
            if output != None:
                lines = self._splitStringIntoLines(output)
                for line in lines:
                    self.debug('StdOut: %s' % line)
                    # filtering output lines
                    if self._isInfoLine(line):
                        self.output(line.strip())
                # obtaining current positions
                if positions_len != 0:
                    position = self._obtainPositionFromLine(output)
                    if position != None:
                        current_positions.append(position)
            if error != None:
                lines = self._splitStringIntoLines(error)
                for line in lines:
                    self.debug('StdErr: %s' % line)
                    if self._isInfoLine(line):
                        self.error(line.strip())    
                # obtaining current positions
                if positions_len != 0:
                    position = self._obtainPositionFromLine(error)
                    if position != None:
                        current_positions.append(position)
            if self.slsDetectorProgram.isTerminated():
                self.debug("slsDetectorProgram has terminated...")
                break

        outDir = self.execMacro("mythen_getOutDir").getResult()
        outFileName = self.execMacro("mythen_getOutFileName").getResult()
        outIndex = self.execMacro("mythen_getIndex").getResult()
        outPath = outDir + "/" + outFileName + "_" + str(outIndex-1) + ".dat"

        if positions_len != len(current_positions):
            self.warning('Number of the positions reported by' +
                         ' sls_detector_acquire does not correspond to' + 
                         ' number of the requested positions.') 
        return_positions_str = repr(current_positions)
        return (outPath, return_positions_str)
    
    def on_abort(self):
        self.output("on_abort() entering...")
        if not self.slsDetectorProgram.isTerminated():
            abortProgram = SlsDetectorPut(["status", "stop"])            
            abortProgram.execute()
            output = abortProgram.getStdOut()
            error = abortProgram.getStdErr()
            while True:
                outLine = output.readline();self.debug( "outLine: " + outLine)
                errLine = error.readline();self.debug("errLine: "  + errLine)
                lenOutLine = len(outLine)
                lenErrLine = len(errLine)
                if lenOutLine != 0:
                    self.output(outLine)
                if lenErrLine != 0:
                    self.error(errLine)
                if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                    break

#class mythen_acquire(Macro):
    #"""Acquires images with mythen detector. If positions are set it will go to positions and acquire one frame per position."""
    
    #result_def = [['OutFile', Type.String, None, 'Full path to the output file']]
    
    #def prepare(self, *args, **kwargs):
        ##self.slsDetectorProgram = SlsDetectorAcquire([])
        #import threading
        #self.stdOutQueue = threading.Queue() 
        #self.slsDetectorProgram = SlsDetectorProgram([], "sls_detector_acquire", self.stdOutQueue)
        
    #def run(self, *args, **kwargs):
        #positions = self.execMacro('mythen_getPositions').getResult()
        #if positions == "[]":
            #self.motor=None
        #else:
            #self.warning("Motor 'pd_mc' will move to %s" % repr(positions))
            #self.motor=self.getMotion(["pd_mc"])
        
        #self.slsDetectorProgram.execute()
        #output = self.slsDetectorProgram.getStdOut()
        #error = self.slsDetectorProgram.getStdErr()
        
        #while True:
            #outLine = output.readline();self.debug( "outLine: " + outLine)
            #errLine = error.readline();self.debug("errLine: "  + errLine)
            #lenOutLine = len(outLine)
            #lenErrLine = len(errLine)
            #if lenOutLine != 0:
                #self.output(outLine)
            #if lenErrLine != 0:
                #self.error(errLine)
            #if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                #self.debug("Terminating...")
                #break
        #outDir = self.execMacro("mythen_getOutDir").getResult()
        #outFileName = self.execMacro("mythen_getOutFileName").getResult()
        #outIndex = self.execMacro("mythen_getIndex").getResult()
        #outPath = outDir + "/" + outFileName + "_" + str(outIndex-1) + ".dat"
        ##self.info("File created: %s" % outPath)
        #return outPath
    
    #def on_abort(self):
        #self.output("on_abort() entering...")
        #if not self.slsDetectorProgram.isTerminated():
            #abortProgram = SlsDetectorPut(["status", "stop"])
            #abortProgram.execute()
            #while True:
                #outLine = output.readline();self.debug( "outLine: " + outLine)
                #errLine = error.readline();self.debug("errLine: "  + errLine)
                #if lenOutLine != 0:
                    #self.output(outLine)
                #if lenErrLine != 0:
                    #self.error(errLine)
                #if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                    #break
                    
                    
class mythen_getStatus(Macro):
    """Gets mythen status. Return values:
       running - detector is acquiring
       error - detector is in error state
       transmitting - detector is transmitting data
       idle - detector is waiting for commands
       finished - unknown @todo
       waiting - unknown @todo"""
       
    result_def =  [['status', Type.String, None, 'Detector status']]

    def prepare(self, *args, **kwargs):
        self.slsDetectorProgram = SlsDetectorGet(["status"])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        status = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: " + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if "status" in outLine:
                    #example of output: "status idle"
                    try:
                        status = outLine.split()[1]
                    except Exception, e:
                        self.error("Could not parse '%s' output: %s" % (self.slsDetectorProgram.args, outLine))
                        raise e
                else:
                    self.output(outLine)                
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if status is None:
            raise Exception("It was not able to retrieve Status.")
        return status
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill() 
        
        
class mythen_getTiming(Macro):
    """Gets timing mode. Return values:
       auto - software timing
       gating - hardware gating
       trigger - hardware trigger
       complementary - unknown @todo"""
       
    result_def =  [['mode', Type.String, None, 'Configured timing mode']]

    def prepare(self, *args, **kwargs):
        self.slsDetectorProgram = SlsDetectorGet(["timing"])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        mode = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: " + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if "timing" in outLine:
                    #example of output: "timing gating"
                    try:
                        mode = outLine.split()[1]
                    except Exception, e:
                        self.error("Could not parse '%s' output: %s" % (self.slsDetectorProgram.args, outLine))
                        raise e
                else:
                    self.output(outLine)                
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if mode is None:
            raise Exception("It was not able to retrieve Timing.")
        return mode
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()  
    
    
class mythen_setTiming(Macro):
    """Sets timing mode. Return values:
       auto - software timing
       gating - hardware gating
       trigger - hardware trigger
       complementary - unknown @todo"""
       
    param_def =  [['mode', Type.String, None, 'New timing mode']]

    def prepare(self, *args, **kwargs):
        mode = args[0]
        self.slsDetectorProgram = SlsDetectorPut(["timing", mode])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        mode = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: " + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if "timing" in outLine:
                    #example of output: "timing gating"
                    try:
                        mode = outLine.split()[1]
                    except Exception, e:
                        self.error("Could not parse '%s' output: %s" % (self.slsDetectorProgram.args, outLine))
                        raise e
                else:
                    self.output(outLine)                
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if mode is None:
            raise Exception("It was not able to retrieve Timing.")
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()  

class mythen_getExtSignal(Macro):
    """Gets external signal configuration. Return values:
       off - acquisition of software trigger
       gate_in_active_high - acquisition while signal is high
       gate_in_active_low - acquision while signal is low
       trigger_in_rising_edge - acquisition starts when transition from low to high
       trigger_in_falling_edge - acquistion start when transition from high to low
       ro_trigger_in_rising_edge - unknown
       ro_trigger_in_falling_edge - unknown
       gate_out_active_high - generates high signal while acquiring
       gate_out_active_low - generates low signal while acquiring
       trigger_out_rising_edge - generates transition form low to high when acquisition starts
       trigger_out_falling_edge - generates transition form high to low when acquisition starts
       ro_trigger_out_rising_edge - unknown,
       ro_trigger_out_falling_edge - unknown"""
       
    param_def = [['channelNr', Type.Integer, None, 'Channel nr']]
    result_def =  [['mode', Type.String, None, 'Configured mode ']]

    def prepare(self, *args, **kwargs):
        channelNr = args[0]
        self.slsDetectorProgram = SlsDetectorGet(["extsig:%d" % channelNr])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        mode = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: " + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if "extsig" in outLine:
                    #example of output: "extsig:0 gate_in_active_high"
                    try:
                        mode = outLine.split()[1]
                    except Exception, e:
                        self.error("Could not parse '%s' output: %s" % (self.slsDetectorProgram.args, outLine))
                        raise e
                else:
                    self.output(outLine)                
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if mode is None:
            raise Exception("It was not able to retrieve ExtSig.")
        return mode
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()            

class mythen_setExtSignal(Macro):
    """Sets external signal configuration. Return values:
       off - acquisition of software trigger
       gate_in_active_high - acquisition while signal is high
       gate_in_active_low - acquision while signal is low
       trigger_in_rising_edge - acquisition starts when transition from low to high
       trigger_in_falling_edge - acquistion start when transition from high to low
       ro_trigger_in_rising_edge - unknown
       ro_trigger_in_falling_edge - unknown
       gate_out_active_high - generates high signal while acquiring
       gate_out_active_low - generates low signal while acquiring
       trigger_out_rising_edge - generates transition form low to high when acquisition starts
       trigger_out_falling_edge - generates transition form high to low when acquisition starts
       ro_trigger_out_rising_edge - unknown,
       ro_trigger_out_falling_edge - unknown"""
       
    param_def = [['channelNr', Type.Integer, None, 'Channel nr'],
                 ['mode', Type.String, None, 'Mode']]

    def prepare(self, *args, **kwargs):
        channelNr = args[0]
        mode = args[1]
        self.slsDetectorProgram = SlsDetectorPut(["extsig:%d" % channelNr, mode])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: " + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if "extsig" in outLine:
                    #example of output: "extsig:0 gate_in_active_high"
                    try:
                        mode = outLine.split()[1]
                    except Exception, e:
                        self.error("Could not parse '%s' output: %s" % (self.slsDetectorProgram.args, outLine))
                        raise e
                else:
                    self.output(outLine)                
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if mode is None:
            raise Exception("It was not able to configure ExtSignal.")
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()   
            
            
class mythen_getNrOfTriggers(Macro):
    """Gets nr of triggers. """
       
    result_def =  [['NrOfTriggers', Type.Integer, None, 'Nr of triggers']]

    def prepare(self, *args, **kwargs):
        self.slsDetectorProgram = SlsDetectorGet(["cycles"])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        nrOfTriggers = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: " + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if "cycles" in outLine:
                    #example of output: "cycles 2.000000000"
                    try:
                        nrOfTriggers = int(float(outLine.split()[1]))
                    except Exception, e:
                        self.error("Could not parse '%s' output: %s" % (self.slsDetectorProgram.args, outLine))
                        raise e
                else:
                    self.output(outLine)                
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if nrOfTriggers is None:
            raise Exception("It was not able to retrieve NrOfTriggers.")
        return nrOfTriggers
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()    
            
class mythen_setNrOfTriggers(Macro):
    """Gets nr of triggers. """
    
    param_def =  [['NrOfTriggers', Type.Integer, None, 'Nr of triggers']]

    def prepare(self, *args, **kwargs):
        nrOfTriggers = args[0]
        self.slsDetectorProgram = SlsDetectorPut(["cycles", str(nrOfTriggers)])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        nrOfTriggers = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: " + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if "cycles" in outLine:
                    #example of output: "cycles 2.000000000"
                    try:
                        nrOfTriggers = int(float(outLine.split()[1]))
                    except Exception, e:
                        self.error("Could not parse '%s' output: %s" % (self.slsDetectorProgram.args, outLine))
                        raise e
                else:
                    self.output(outLine)                
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if nrOfTriggers is None:
            raise Exception("It was not able to retrieve NrOfTriggers.")
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()  
            
            
class mythen_getNrOfFramesPerTrigger(Macro):
    """Gets nr of frames per trigger. """
       
    result_def =  [['NrOfFramesPerTrigger', Type.Integer, None, 'Nr of frames per trigger']]

    def prepare(self, *args, **kwargs):
        self.slsDetectorProgram = SlsDetectorGet(["frames"])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        nrOfFramesPerTrigger = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: " + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if "frames" in outLine:
                    #example of output: "frames 2.000000000"
                    try:
                        nrOfFramesPerTrigger = int(float(outLine.split()[1]))
                    except Exception, e:
                        self.error("Could not parse '%s' output: %s" % (self.slsDetectorProgram.args, outLine))
                        raise e
                else:
                    self.output(outLine)                
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if nrOfFramesPerTrigger is None:
            raise Exception("It was not able to retrieve NrOfFramsePerTrigger.")
        return nrOfFramesPerTrigger
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill() 
            
            
class mythen_setNrOfFramesPerTrigger(Macro):
    """Gets nr of frames per trigger. """
       
    param_def =  [['NrOfFramesPerTrigger', Type.Integer, None, 'Nr of frames per trigger']]

    def prepare(self, *args, **kwargs):
        nrOfFramesPerTrigger = args[0]
        self.slsDetectorProgram = SlsDetectorPut(["frames", str(nrOfFramesPerTrigger)])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        nrOfFramesPerTrigger = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: " + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if "frames" in outLine:
                    #example of output: "frames 2.000000000"
                    try:
                        nrOfFramesPerTrigger = int(float(outLine.split()[1]))
                    except Exception, e:
                        self.error("Could not parse '%s' output: %s" % (self.slsDetectorProgram.args, outLine))
                        raise e
                else:
                    self.output(outLine)                
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if nrOfFramesPerTrigger is None:
            raise Exception("It was not able to retrieve NrOfFramsePerTrigger.")
        return nrOfFramesPerTrigger
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()
            
class mythen_getNrOfGates(Macro):
    """Gets nr of frames per trigger. """
       
    result_def =  [['NrOfGates', Type.Integer, None, 'Nr of gates']]

    def prepare(self, *args, **kwargs):
        self.slsDetectorProgram = SlsDetectorGet(["gates"])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        nrOfGates = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: " + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if "gates" in outLine:
                    #example of output: "gates 2.000000000"
                    try:
                        nrOfGates = int(float(outLine.split()[1]))
                    except Exception, e:
                        self.error("Could not parse '%s' output: %s" % (self.slsDetectorProgram.args, outLine))
                        raise e
                else:
                    self.output(outLine)                
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if nrOfGates is None:
            raise Exception("It was not able to retrieve NrOfGates.")
        return nrOfGates
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill() 
            
            
class mythen_setNrOfGates(Macro):
    """Gets nr of frames per trigger. """
       
    param_def =  [['NrOfGates', Type.Integer, None, 'Nr of gates']]

    def prepare(self, *args, **kwargs):
        nrOfGates = args[0]
        self.slsDetectorProgram = SlsDetectorPut(["gates", str(nrOfGates)])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        nrOfGates = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: " + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if "gates" in outLine:
                    #example of output: "gates 2.000000000"
                    try:
                        nrOfGates = int(float(outLine.split()[1]))
                    except Exception, e:
                        self.error("Could not parse '%s' output: %s" % (self.slsDetectorProgram.args, outLine))
                        raise e
                else:
                    self.output(outLine)                
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if nrOfGates is None:
            raise Exception("It was not able to retrieve NrOfGates.")
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()
                   

class mythen_getBinSize(Macro):
    """Gets binning size."""
    
    result_def =  [['binsize', Type.Float, None, 'Binning size']]
    
    def prepare(self, *args, **kwargs):
        self.slsDetectorProgram = SlsDetectorGet(["binsize"])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        binSize = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: " + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if "binsize" in outLine:
                    #example of output: "binsize 0.01"
                    try:
                        binSize = float(outLine.split()[1])
                    except Exception, e:
                        self.error("Could not parse '%s' output: %s" % (" ".self.slsDetectorProgram.args, outLine))
                        raise e
                else:
                    self.output(outLine)                
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if binSize is None:
            raise Exception("It was not able to retrieve binSize.")
        return binSize
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()            
            
class mythen_setBinSize(Macro):
    """Sets binning size."""
    
    param_def  =  [['binSize', Type.String, None, 'Binning size']]
    
    def prepare(self, *args, **kwargs):
        binSize = args[0]
        self.slsDetectorProgram = SlsDetectorPut(["binsize", binSize])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        binSize = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: "  + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if "binsize" in outLine:
                    #example of output: "binsize 0.010000"
                    try:
                        binSize = float(outLine.split()[1])
                    except Exception, e:
                        self.error("Could not parse '%s' output: %s" % (" ".self.slsDetectorProgram.args, outLine))
                        raise e
                else:
                    self.output(outLine)
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if binSize is None:
            raise Exception("It was not able to retrieve expTime.")
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()
            

class mythen_getDr(Macro):
    """Gets dynamic range."""
    
    result_def =  [['dr', Type.Integer, None, 'Dynamic range']]
    
    def prepare(self, *args, **kwargs):
        self.slsDetectorProgram = SlsDetectorGet(["dr"])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        dr = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: " + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if "dr" in outLine:
                    #example of output: "dr 24"
                    try:
                        dr = int(outLine.split()[1])
                    except Exception, e:
                        self.error("Could not parse '%s' output: %s" % (" ".self.slsDetectorProgram.args, outLine))
                        raise e
                else:
                    self.output(outLine)                
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if dr is None:
            raise Exception("It was not able to retrieve binSize.")
        return dr
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()            
            
class mythen_setDr(Macro):
    """Sets dynamic range."""
    
    param_def  =  [['dr', Type.String, None, 'Dynamic range']]
    
    def prepare(self, *args, **kwargs):
        dr = args[0]
        self.slsDetectorProgram = SlsDetectorPut(["dr", str(dr)])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        dr = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: "  + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if "dr" in outLine:
                    #example of output: "binsize 0.010000"
                    try:
                        dr = int(outLine.split()[1])
                    except Exception, e:
                        self.error("Could not parse '%s' output: %s" % (" ".self.slsDetectorProgram.args, outLine))
                        raise e
                else:
                    self.output(outLine)
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if dr is None:
            raise Exception("It was not able to retrieve Dr.")
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()

            
class mythen_getSettings(Macro):
    """Gets settings."""
    
    result_def =  [['settings', Type.String, None, 'Settings']]
    
    def prepare(self, *args, **kwargs):
        self.slsDetectorProgram = SlsDetectorGet(["settings"])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        settings = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: " + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if "settings" in outLine:
                    #example of output: "dr 24"
                    try:
                        settings = outLine.split()[1]
                    except Exception, e:
                        self.error("Could not parse '%s' output: %s" % (" ".join(self.slsDetectorProgram.args), outLine))
                        raise e
                else:
                    self.output(outLine)                
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if settings is None:
            raise Exception("It was not able to retrieve binSize.")
        return settings
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()            
            
class mythen_setSettings(Macro):
    """Sets settings."""
    
    param_def  =  [['settings', Type.String, None, 'Settings type']]
    
    def prepare(self, *args, **kwargs):
        dr = args[0]
        self.slsDetectorProgram = SlsDetectorPut(["settings", str(dr)])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        settings = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: "  + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if "settings" in outLine:
                    #example of output: "settings standard"
                    try:
                        settings = outLine.split()[1]
                    except Exception, e:
                        self.error("Could not parse '%s' output: %s" % (" ".join(self.slsDetectorProgram.args), outLine))
                        raise e
                else:
                    self.output(outLine)
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if settings is None:
            raise Exception("It was not able to retrieve settings.")
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()            
            
class mythen_take(Macro, MntGrpController):
    
    result_def = [['OutFile', Type.String, None, 'Full path to the output file']]
    
    MONITOR_CHANNEL = 'bl04/io/ibl0403-dev2-ctr0'
    MONITOR_CHANNEL_GATE = '/Dev2/PFI38'        
        
    def _backupChannel(self, channel):
        self._pauseTriggerType = channel.read_attribute('PauseTriggerType').value
        self._pauseTriggerWhen = channel.read_attribute('PauseTriggerWhen').value
        self._pauseTriggerSource = channel.read_attribute('PauseTriggerSource').value
        self.debug('PauseTriggerType: %s' % self._pauseTriggerType)
        self.debug('PauseTriggerWhen: %s' % self._pauseTriggerWhen)
        self.debug('PauseTriggerSource: %s' % self._pauseTriggerSource)
        
    def _restoreChannel(self, channel):
        channel.write_attribute('PauseTriggerType', self._pauseTriggerType)
        channel.write_attribute('PauseTriggerWhen', self._pauseTriggerWhen)
        channel.write_attribute('PauseTriggerSource', self._pauseTriggerSource)
        
    def _configureChannel(self, channel):
        channel.write_attribute("PauseTriggerType", "DigLvl")
        channel.write_attribute("PauseTriggerWhen", "Low")
        channel.write_attribute("PauseTriggerSource", self.MONITOR_CHANNEL_GATE)

    def _count(self, count_time):
        '''Executes a count of the measurement group. It returns results
           or in case of exception None'''
#        self.mntGrpAcqTime = count_time
        MntGrpController.setAcqTime(self, count_time)
        try: 
            MntGrpController.prepareMntGrp(self)
            MntGrpController.acquireMntGrp(self)
        except Exception, e:
            self.warning('Exception while using measurement group')
            self.debug(e)
            return None
        finally:
            MntGrpController.waitMntGrp(self)
        results = MntGrpController.getMntGrpResults(self)
        return results
                
    def prepare(self, *args, **kwargs):
        MntGrpController.init(self, self)
        self.monitorChannel = PyTango.DeviceProxy(self.MONITOR_CHANNEL)
	self.monitorChannel.Stop()
        #preparing Mythen to generate gate while acquiring
        self.execMacro('mythen_setExtSignal 1 gate_out_active_high')
        
    def run(self, *args, **kwargs):
        self._backupChannel(self.monitorChannel)
        try:
            self._configureChannel(self.monitorChannel)
            self.monitorChannel.Start()
            outFileName, positions = self.execMacro("mythen_acquire").getResult()
            nrOfPositions = len(eval(positions))
            if nrOfPositions == 0:
                nrOfPositions = 1
            monitorValue = self.monitorChannel.read_attribute('Count').value
            monitorValuePerPosition = int(monitorValue / nrOfPositions)
            self.info('MonitorValue: %f' % monitorValue)
            self.info('MonitorValuePerPosition: %d' % monitorValuePerPosition)
        except Exception, e:
            self.error('Exception during acquisition')
            self.warning(e)
            raise e
        finally:
            self.monitorChannel.Stop()
            self._restoreChannel(self.monitorChannel)

        self.info("Data stored: %s" % outFileName)
        
        mnt_grp_time = 0.1
        mnt_grp_results = None
        for i in range(3):
            msg = 'Measurement group count of time: %s [s]' % mnt_grp_time
            self.output(msg)
            mnt_grp_results = self._count(mnt_grp_time)
            if mnt_grp_results != None:
                break
        else:
            msg = 'It was not able to count with the measurement within 3 attempts'
            self.error(msg)
            msg = 'Measurement group data will be skipped in the par file'
            self.info(msg)
                               
        parFileName = outFileName[:-3] + "par"
        try:
            parFile = open(parFileName,"w")
            parFile.write("# imon %d " % monitorValuePerPosition)
            if mnt_grp_results != None:
                parFile.write(mnt_grp_results)
            parFile.write('\nMonitor = %d' % monitorValuePerPosition)
            parFile.write('\nIsPos = %s' % positions)
            extraHeader = self.execMacro("_mythpar").getResult()
            parFile.write(extraHeader)
            self.info("Metadata stored: %s" % parFileName)
        except Exception,e:
            self.error("Error while writing par file.")
            raise e
        finally:
            parFile.close()
        return outFileName


class mythen_getAngConv(Macro):
    """Gets the constants used for angular convertion."""
   
    result_def =  [['fnOut', Type.String, "", '[Filename to print the result]']]
    
    def prepare(self, *args, **kwargs):
        self.slsDetectorProgram = SlsDetectorGet(['angconv'])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
                
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: " + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if 'angconv' in outLine:
                    fnOut = outLine.split()[1]
            if lenErrLine != 0:
                self.error(errLine)

            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        return fnOut
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()            


class mythen_getBadChannels(Macro):
    """Gets the bad channels."""
   
    result_def =  [['filename', Type.String, "", 'Filename to print the result']]
    
    def prepare(self, *args, **kwargs):
        self.slsDetectorProgram = SlsDetectorGet(['badchannels'])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
                
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: " + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if 'badchannels' in outLine:
                    filename = outLine.split()[1]
#                else:
#                    self.output(outLine)
          
#            if lenErrLine != 0:
#                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        return filename
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()            

class mythen_setBadChannels(Macro):
    """Gets the bad channels."""
   
    param_def  =  [['newFileName', Type.String, None, 'Bad channel file name']]
    result_def =  [['ackFileName', Type.String, None, 'Acknowledged bad channel file name']]
    
    def prepare(self, *args, **kwargs):
        self.badChannelFilename = args[0]
        if self.badChannelFilename != 'none':
            if not os.path.isfile(self.badChannelFilename):
                raise Exception('File %s does not exist.' % self.badChannelFilename)
        self.slsDetectorProgram = SlsDetectorPut(['badchannels', self.badChannelFilename])

    def run(self, *args, **kwargs):
        self.info('running')
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
                
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: " + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if 'badchannels' in outLine:
                    filename = outLine.split()[1]
                else:
                    self.output(outLine)
          
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        return filename
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()            

class mythen_getGlobalOff(Macro):
    """Gets the global offset used for angular conversion."""
    
    result_def =  [['globaloff', Type.Float, None, 'Global Offset']]
    
    def prepare(self, *args, **kwargs):
        self.slsDetectorProgram = SlsDetectorGet(['globaloff'])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        globaloff = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: " + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if 'globaloff' in outLine:
                    try:
                        globaloff = float(outLine.split()[1])
                    except Exception, e:
                        self.error("Could not parse '%s' output: %s" % 
                                   (" ".self.slsDetectorProgram.args, outLine))
                        raise e
                else:
                    self.output(outLine)                
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if globaloff is None :
            raise Exception("It was not able to retrieve the global offset.")
        
        return globaloff 
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()            

class mythen_setGlobalOff(Macro):
    """Gets the global offset used for angular conversion."""
    
   
    param_def =  [['globaloff', Type.Float, 0, 'Global Offset']]
    result_def =  [['globaloff', Type.Float, None, 'Global Offset']]
    
    def prepare(self, *args, **kwargs):
        self.globaloff = args[0]
        self.slsDetectorProgram = SlsDetectorPut(['globaloff', str(self.globaloff)])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        globaloff = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: " + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                if 'globaloff' in outLine:
                    try:
                        globaloff = float(outLine.split()[1])
                    except Exception, e:
                        self.error("Could not parse '%s' output: %s" % 
                                   (" ".self.slsDetectorProgram.args, outLine))
                        raise e
                else:
                    self.output(outLine)                
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
        if globaloff is None:
            raise Exception("It was not able to retrieve the global offset.")
        return globaloff 
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()            

class mythen_setConfig(Macro):
    """Sets configuration from file."""
    
    param_def  =  [['confFileName', Type.String, '/homelocal/opbl04/bl04mythen.conf', 'Configuration file name']]
    
    def prepare(self, *args, **kwargs):
        confFileName = args[0]
        if not os.path.isfile(confFileName):
            raise Exception('File %s does not exist.' % confFileName)
        self.slsDetectorProgram = SlsDetectorPut(["config", confFileName])

    def run(self, *args, **kwargs):
        self.slsDetectorProgram.execute()
        output = self.slsDetectorProgram.getStdOut()
        error = self.slsDetectorProgram.getStdErr()
        settings = None
        
        while True:
            outLine = output.readline();self.debug( "outLine: " + outLine)
            errLine = error.readline();self.debug("errLine: "  + errLine)
            lenOutLine = len(outLine)
            lenErrLine = len(errLine)
            if lenOutLine != 0:
                self.output(outLine)
            if lenErrLine != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated() and lenOutLine == 0 and lenErrLine == 0:
                break
    
    def on_abort(self):
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.terminate()
            time.sleep(1)
        if not self.slsDetectorProgram.isTerminated():
            self.slsDetectorProgram.kill()            

class mythen_softscan(Macro, MoveableController, SoftShutterController): #, MntGrpController):

    param_def = [[ 'motor', Type.Motor, None, 'Motor to scan'],
                [ 'start_pos', Type.Float, None, 'Start position'],
                [ 'end_pos', Type.Float, None, 'End position'],
                [ 'time', Type.Float, None, 'Count time']]


    def checkParams(self, args):
        self.debug("mythen_sofscan.checkParams(%s) entering..." % repr(args))
        motor = args[0]
        motName = motor.name
        allowedMotors = ["pd_mc"]
        if motName not in allowedMotors:
            raise Exception("Wrong motor. Allowed motors are: %s." %
                            repr(allowedMotors))
        self.debug("mythen_softscan.checkParams(%s) leaving..." % repr(args))
        
    def prepare(self, *args):    
        self.debug("mythen_softscan. preparing entering...")
        self.checkParams(args)

        self.motor = args[0]
        self.start_pos = args[1]
        self.end_pos = args[2]
        self.count_time = args[3]
        self.acqTime = self.count_time


        #backup of the position and set empty posiiton
        macro_tmp = "mythen_getPositions"
        self.pos_bck = self.execMacro(macro_tmp).getResult()
        self.execMacro("mythen_setPositions")
        #backup timing
        macro_tmp = "mythen_getTiming"
        self.timing_bck = self.execMacro(macro_tmp).getResult()
        self.execMacro("mythen_setTiming  auto")
        #Prepare Shuttter
        SoftShutterController.init(self)
        self.prepareShutter()
        #Prepare Motor
        MoveableController.init(self, self.motor)
        const_vel_time = self.count_time
        self.prepareMotion(const_vel_time, self.start_pos, self.end_pos) 
        
    def run(self, *args, **kwargs):
        self.debug("mythen_softscan. run entering...")
        
        try:
            self.moveToPrestart()
            self.openShutter()
            #self.info("starting AcqMntGrp  ...") 
            #self.acquireMntGrp()
                       
            self.moveToPostend()
            self.info("Waiting, movement and acquisition in progress...") 
            self.execMacro("mythen_take %f" %self.acqTime) 


	        #sleep_time = self.accTime
            #time.sleep(sleep_time)                
            #self.openShutter()                                 
            #outFileName = self.execMacro("mythen_acquire").getResult()
            #self.info("Data stored: %s" % outFileName)
          
            #self.waitMntGrp()
            #self.closeShutter()
            #time.sleep(sleep_time)

        finally:

            self.info("Cleanup...")   
            self.closeShutter() 
            self.cleanup()
            #todo 
            # restore position backup change to 

    def on_abort(self):
        self.debug("mythen_softscan.on_abort() entering...")
        self.info("on_abort() entering...")
        self.closeShutter()
        self.cleanup()
        
            
