''' @package FioJob
A module realizing a fio job run.
'''
import subprocess

class FioJob(object):
    '''
    A class configuring the fio job.
    '''
    
    
    def __init__(self):
        ''' The constructor '''
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
        
    def __str__(self):
        ''' Return a string representation of the fio executable. '''   
        res = "fio: " + self.__fioPath + ", " + self.__fioVersion
        return res
    
    
    def getArgs(self):
        ''' Return the current configured fio arguments. '''
        return self.__fioArgs
    
    def addArg(self,key,value):
        ''' Add a key value pair as an argument to fio.
        @param key: Name of the option for fio.
        @param value: Value for the given fio option.  
        '''
        self.__fioArgs[key] = value
        
    def prepArgs(self):
        ''' Generate an argument list out of the dictionary suited for fio. '''
        argList = [self.__fioPath]
        for k,v in self.__fioArgs.iteritems():
            argList.append('--' + k + '=' + v)
        return argList
        
    def start(self):
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