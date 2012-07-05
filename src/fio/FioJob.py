''' @package FioJob
A module realizing a fio job run.
'''
import subprocess

class FioJob(object):
    '''
    A class configuring the fio job.
    '''
    
    ## Position of read IOPS in the fio terse output.
    terseIOPSReadPos = 7

    ## Position of write IOPS in the fio terse output.
    terseIOPSWritePos = 48
    
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
        ## Key value arguments e.g. name="test"
        self.__fioKVArgs = {}
        ## Single arguments e.g. group_reporting
        self.__fioSglArgs = []
        
    def __str__(self):
        ''' Return a string representation of the fio executable. '''   
        res = "fio: " + self.__fioPath + ", " + self.__fioVersion
        return res
    
    def getKVArgs(self):
        ''' Return the current configured fio key value arguments. '''
        return self.__fioKVArgs
    
    def getSglArgs(self):
        ''' Return the current configured fio single key arguments. '''
        return self.__fioSglArgs
    
    def addKVArg(self,key,value):
        ''' Add a key value pair as an argument to fio.
        @param key: Name of the option for fio.
        @param value: Value for the given fio option.  
        '''
        self.__fioKVArgs[key] = value
        
    def addSglArg(self,key):
        ''' Add a single value option to fio argument list.
        @param key: Name of the option being added.
        ''' 
        self.__fioSglArgs.append(key)
        
    def prepKVArgs(self):
        ''' Generate an argument list out of the dictionary suited for fio. '''
        argList = [self.__fioPath]
        for k,v in self.__fioKVArgs.iteritems():
            argList.append('--' + k + '=' + v)
        return argList
    
    def prepSglArgs(self,argList):
        ''' Generate an argument list out of the single key arguments. '''
        for k in self.__fioSglArgs:
            argList.append('--' + k)
        return argList
        
    def start(self):
        ''' Start a fio job with its argument list.
        The argument list defines the parameters given to fio.
        @return: The standard output of the fio test or stderr on error.
        '''
        args = self.prepKVArgs()
        args = self.prepSglArgs(args)
        print args
        if len(args) == 0:
            print "Error: fio argument list is empty."
            exit(1)
        out = subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdout,stderr) = out.communicate()
        if stderr != '':
            print "Fio encountered an error: " + stderr
            return stderr
        else:
            return stdout
        
    def getIOPS(self,fioOut):
        '''
        Parses the average IOPS out of the fio result output.
        @param fioOut The output of the fio performance test.
        @return Sum of read IOPS and write IOPS
        '''
        #index 7 iops read
        #index 48 iops write
        fioTerse = fioOut.split(';')
        print "iops read:" + fioTerse[FioJob.terseIOPSReadPos]
        print "iops write:" + fioTerse[FioJob.terseIOPSWritePos]
        return int(fioTerse[FioJob.terseIOPSReadPos]) + int(fioTerse[FioJob.terseIOPSWritePos])
       
     
        
        
        