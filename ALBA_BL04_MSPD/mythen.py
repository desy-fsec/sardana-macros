import Queue
import PyTango
import time

from sardana.macroserver.macro import Macro, Type, ParamRepeat
from taurus.core.tango.sardana.pool import StopException
from macro_utils.slsdetector import SlsDetectorGet, SlsDetectorPut, SlsDetectorAcquire, SlsDetectorProgram
from macroutils import MntGrpController



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
    """Gets name of the next output file."""
    
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
    """Sets name of the flat field file."""
    
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
    
    result_def = [['OutFile', Type.String, None, 'Full path to the output file']]
    
    def prepare(self, *args, **kwargs):
        #self.slsDetectorProgram = SlsDetectorAcquire([])       
        self.stdOutQueue = Queue.Queue()
        self.stdErrQueue = Queue.Queue()
        self.slsDetectorProgram = SlsDetectorProgram([], "sls_detector_acquire", self.stdOutQueue, self.stdErrQueue)
        
    def run(self, *args, **kwargs):
        positions = self.execMacro('mythen_getPositions').getResult()
        if positions == "[]":
            self.motor=None
        else:
            self.warning("Motor 'pd_mc' will move to %s" % repr(positions))
            self.motor=self.getMotion(["pd_mc"])
        
        self.slsDetectorProgram.execute()
        
        while True:
            self.checkPoint()
            try:
                outLine = None
                outLine = self.stdOutQueue.get(timeout=.1);self.debug( "outLine: " + outLine)
            except Queue.Empty, e:
                pass
            except StopException, e:
                raise e
            except Exception, e:
                self.error("Exception when reading from sls_detector_acquire standard output. Exiting...")
                raise e
            
            try:
                errLine = None
                errLine = self.stdErrQueue.get(timeout=.1);self.debug( "errLine: " + errLine)
            except Queue.Empty, e:
                pass
            except StopException, e:
                raise e
            except Exception, e:
                self.error("Exception when reading from sls_detector_acquire standard output. Exiting...")
                raise e
                
            if outLine != None and len(outLine) != 0:
                self.output(outLine)
            if errLine != None and len(errLine) != 0:
                self.error(errLine)
            if self.slsDetectorProgram.isTerminated():
                self.debug("slsDetectorProgram has terminated...")
                break
        outDir = self.execMacro("mythen_getOutDir").getResult()
        outFileName = self.execMacro("mythen_getOutFileName").getResult()
        outIndex = self.execMacro("mythen_getIndex").getResult()
        outPath = outDir + "/" + outFileName + "_" + str(outIndex-1) + ".dat"        
        return outPath
    
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
    
    def prepare(self, *args, **kwargs):
        MntGrpController.init(self, self)
        #expTime = self.execMacro("mythen_getExpTime").getResult()
        #positions = self.execMacro("mythen_getPositions").getResult()
        #positions = eval(positions)
        #nrOfPositions = len(positions)
        ##self.output("nrOfPositions: %d" % nrOfPositions)
        #if nrOfPositions > 0: 
            #self.mntGrpAcqTime = expTime * nrOfPositions
        #else:
            #self.mntGrpAcqTime = expTime
        #self.output("mntGrpAcqTime: %d" % self.mntGrpAcqTime)
    
    def run(self, *args, **kwargs):
        outFileName = self.execMacro("mythen_acquire").getResult()
        self.info("Data stored: %s" % outFileName)
        self.mntGrpAcqTime = 0.1
        MntGrpController.prepareMntGrp(self)
        MntGrpController.acquireMntGrp(self)
        MntGrpController.waitMntGrp(self)
        results = MntGrpController.getMntGrpResults(self)
        parFileName = outFileName[:-3] + "par"
        try:
            parFile = open(parFileName,"w")
            parFile.write("#")
            parFile.write(results)
            extraHeader = self.execMacro("_mythpar").getResult()
            parFile.write(extraHeader)
            self.info("MntGrp data stored: %s" % parFileName)
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
                else:
                    self.outline(outLine)
          
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
