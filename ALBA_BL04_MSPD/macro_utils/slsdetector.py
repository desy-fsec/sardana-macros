import subprocess, sys, threading, thread, time


class MythenReadoutTime(dict):

    def __init__(self):
        dict.__init__(self)
        dict.__setitem__(self, 24, 0.000240) #theoretical 250us  
        dict.__setitem__(self, 16, 0.000180) #theoretical 200us  
        dict.__setitem__(self, 8, 0.000120)  #theoretical 125us  
        dict.__setitem__(self, 4, 0.000090)  #theoretical 90us  
        dict.__setitem__(self, 1, 0.000070)  #theoretical 70us  
    
    def __setitem__(self, key, value):
        pass

    def __delitem__(self, key, value):
        pass

class SlsDetectorProgram():

    def __init__(self, args, executable, stdOutQueue=None, stdErrQueue=None):
        self.args = args
        self.bufferSize = 0
        self.executable = executable
        self.stdIn = None
        self.stdOut = subprocess.PIPE
        self.stdErr = subprocess.PIPE
        self.preExecFn = None
        self.closeFds = False
        self.shell = False
        self.__process = None
        #@todo: manage with only one queue!!!
        self.stdOutQueue = stdOutQueue
        self.stdErrQueue = stdErrQueue
        self.__keepUpdatingStdPipes = False
   
    def execute(self):
        self.args.insert(0,self.executable)
        self.__process = subprocess.Popen(self.args,
                         bufsize=self.bufferSize,
                         executable=self.executable,
                         stdin=self.stdIn,
                         stdout=self.stdOut,
                         stderr=self.stdErr,
                         preexec_fn=self.preExecFn,
                         close_fds=self.closeFds,
                         shell=self.shell)
        missingPipes = [self.stdOutQueue,self.stdErrQueue].count(None)
        if missingPipes == 0:
            self.startUpdatePipes()
        elif missingPipes == 1:
            raise Exception("Not all the queues were passed in the contructor. Constructor requires stdOutQueue and stdErrQueue. Missing pipes = %d" % missingPipes)
        
    def getReturnCode(self):
        return self.__process.returncode
        
    def getStdOut(self):
        return self.__process.stdout
        
    def getStdErr(self):
        return self.__process.stdout
        
    def isTerminated(self):
        terminated = False
        if self.__process.poll() is not None:
            terminated = True
        return terminated
        
    def terminate(self):
        self.__keepUpdatingStdPipes = False
        self.__process.terminate()
        
    def kill(self):
        self.__keepUpdatingStdPipes = False
        self.__process.kill()        
                    
    def startUpdatePipes(self):
        self.__keepUpdatingStdPipes = True
        #@todo: manage with only one queue!!!
        for p,q in zip((self.getStdOut(), self.getStdErr()),(self.stdOutQueue, self.stdErrQueue)):
            t = threading.Thread(target=self.updateStdPipes, args=(p, q))
            t.deamon = True
            t.start()
        
    def stopUpdateStdPipes(self):
        self.__keepUpdatingStdPipes
                        
    def updateStdPipes(self, pipe, queue):
        tid = thread.get_ident()
        print("Thread id: %d" % tid)
        while self.__keepUpdatingStdPipes:
            if self.isTerminated():
                lines = pipe.readlines()
                for line in lines:
                    queue.put(line)
                break
            line = pipe.readline()
            print("%d: %s" % (tid,line))
            queue.put(line)
            time.sleep(.1)
    
         
class SlsDetectorPut(SlsDetectorProgram):
    
    def __init__(self, args):
        SlsDetectorProgram.__init__(self, args, "sls_detector_put")

class SlsDetectorGet(SlsDetectorProgram):
    
    def __init__(self, args):
        SlsDetectorProgram.__init__(self, args, "sls_detector_get")
        
class SlsDetectorAcquire(SlsDetectorProgram):
    
    def __init__(self, args):
        SlsDetectorProgram.__init__(self, args, "sls_detector_acquire")
        
def testGetThreshold():
    slsDetectorProgram = SlsDetectorGet(["threshold"])
    slsDetectorProgram.execute()
    output = slsDetectorProgram.getStdOut()
    error = slsDetectorProgram.getStdErr()
    while True:
        outLine = output.readline()
        errLine = error.readline()
        if len(outLine) != 0:
            print(outLine)
        if len(errLine) != 0:
            print(errLine)                        
        if slsDetectorProgram.isTerminated():
            break
            
def testGetOutdir():
    slsDetectorProgram = SlsDetectorGet(["outdir"])
    slsDetectorProgram.execute()
    output = slsDetectorProgram.getStdOut()
    error = slsDetectorProgram.getStdErr()
    while True:
        outLine = output.readline()
        errLine = error.readline()
        if len(outLine) != 0:
            print(outLine)
        if len(errLine) != 0:
            print(errLine)
        isTerminated = slsDetectorProgram.isTerminated()
        print("isTerminated",isTerminated)
        if isTerminated:
            break
        
if __name__ == "__main__":
    argv = sys.argv
    if len(argv) < 2:
        print("usage: <get|put|acquire> [<arg1> <arg2> ... <argN>]")
        sys.exit()
    else:
        if argv[1] == "get":
            if argv[2] == "threshold":
                testGetThreshold()
            elif argv[2] == "outdir":
                testGetOutdir()
            else:
                print("usage: get threshold")
        elif argv[1] == "put":
            pass
        elif sys.argv[1] == "acquire":
            pass
        else:
            print("usage: <get|put|acquire> [<arg1> <arg2> ... <argN>]")
            sys.exit()
        
            