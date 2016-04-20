from sardana.macroserver.macro import iMacro, imacro, Macro, macro, Type
import functools


def catch_error(meth):
    """
    Decorator functions that provides a generic mechanism to catch any
    exception raised by the method.
    @param meth: method to be decorated
    @return:
    """
    @functools.wraps(meth)
    def _catch_error(self, *args, **kws):
        try:
            return meth(self, *args, **kws)
        except Exception, e:
            mname = self.getName()
            self.info("[%s]: exception cached."% mname)
            self.info("[%s]: exception type = %s" % (mname, type(e)))
            self.info("[%s]: exception msg =  %s" % (mname, e))
            self.info("[%s]: re-raising exception." % mname)
            raise e
        finally:
            self.info("finally statement!")
    return _catch_error


class _raise_exception(Macro):
    """
    Category: None

    This macro raises a given exception according to the dictionary defined.
    """

    param_def = [['m',Type.Integer, 0, 'Number of exception in dictionary']]

    def prepare(self, m):
        self.excepDict = {0: Exception,
                          1: TypeError,
                          2: IOError,
                          3: ZeroDivisionError}

    def run(self, m):
        if self.excepDict.has_key(m):
            e = self.excepDict[m]('Description of the exception raised.')
            mname = self.getName()
            self.info("[%s]: exception raised."% mname)
            self.info("[%s]: exception type = %s" % (mname, type(e)))
            self.info("[%s]: exception msg =  %s" % (mname, e))
            raise e
        else:
            self.info("No exception raised!")


class test_catch_exception(Macro):
    """
    Category: Tests

    Testing the catch exception/error decorator used in lima functions at bl13.
    The testCatchException macros demonstrates that when an exception is raised
    from a nested macro, the macroserver caches the exception. Nevertheless, it raises
    a sardana exception, keeping only the basic comment from the original exception."""

    param_def = [['m',Type.Integer, 0, 'Number of exception in dictionary']]
        
    @catch_error
    def run(self, m):
        self.execMacro("_raiseException %s" % m)
