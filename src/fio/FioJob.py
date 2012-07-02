""" @package FioJob
A module realizing a fio job run.
"""
import subprocess
""" A class configuring the fio job. """
class FioJob(object):

    """ The constructor """
    def __init__(self):
        fio = subprocess.Popen(['which', 'fio'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout = fio.communicate()[0]
        fio.wait()
        if fio.returncode != 0:
            print "Error: command 'which fio' returned an error code."
            exit(1)

        self.__fioPath = stdout.rstrip("\n");
        fio = subprocess.Popen(['fio','--version'],stdout=subprocess.PIPE)
        self.__fioVersion = fio.communicate()[0]
        self.__fioArgs = {}
        
        
    """ Return a string representation of the fio executable. """    
    def __str__(self):
        res = "fio: " + self.__fioPath + ", " + self.__fioVersion
        return res
    
    """ Return the current configured fio arguments. """
    def getArgs(self):
        return self.__fioArgs
    
    """ Add a key value pair as an argument to fio. """
    def addArg(self,key,value):
        self.__fioArgs[key] = value
        
    """ Generate an argument list out of the dictionary suited for fio. """
    def prepArgs(self):
        argList = [self.__fioPath]
        for k,v in self.__fioArgs.iteritems():
            argList.append('--' + k + '=' + v)
        return argList
        
    def hddTest(self):
        args = self.prepArgs()
        if len(args) == 0:
            print "Error: fio argument list is empty."
            exit(1)
        out = subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdout,stderr) = out.communicate()
        if stderr != '':
            print "Fio encountered an error: " + stderr
        else:
            print stdout