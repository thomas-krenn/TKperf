''' @package FioJob
A module realizing a fio job run.
'''
import subprocess
import logging

class FioJob(object):
    '''
    A class configuring the fio job.
    '''
    
    ## Position of read IOPS in the fio terse output.
    terseIOPSReadPos = 7

    ## Position of write IOPS in the fio terse output.
    terseIOPSWritePos = 48
    
    ## Position of write total IO in the fio terse output
    terseTotIOWritePos = 46
    
    ## Start Position of write latencies in fio terse output
    terseLatStartWritePos = 78
    
    ## Start Position of read latencies in fio terse output
    terseLatStartReadPos = 37
    
    ## Postion of total read throughput.
    terseTPReadPos = 6
    
    ## Postion of total write throughput.
    terseTPWritePos = 47
    
    
    def __init__(self):
        ''' The constructor '''
        fio = subprocess.Popen(['which', 'fio'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout = fio.communicate()[0]
        fio.wait()
        if fio.returncode != 0:
            logging.error("# Error: command 'which fio' returned an error code.")
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
    
    def getFioVersion(self):
        ''' Return the current fio version string. '''
        return self.__fioVersion
    
    def setFioVersion(self,fioStr):
        ''' Set the used fio version (useful if loading from xml).'''
        self.__fioVersion = fioStr
    
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
        @return: [True,standard output] of the fio test or [False,0] on error.
        '''
        args = self.prepKVArgs()
        args = self.prepSglArgs(args)
        logging.info('%s',args)
        if len(args) == 0:
            logging.error("Error: fio argument list is empty.")
            exit(1)
        out = subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdout,stderr) = out.communicate()
        if stderr != '':
            logging.error("Fio encountered an error: " + stderr)
            return [False,'']
        else:
            return [True,stdout]
        
    def getIOPS(self,fioOut):
        '''
        Parses the average IOPS out of the fio result output.
        @param fioOut The output of the fio performance test.
        @return Sum of read IOPS and write IOPS
        '''
        #index 7 iops read
        #index 48 iops write
        fioTerse = fioOut.split(';')
        return int(fioTerse[FioJob.terseIOPSReadPos]) + int(fioTerse[FioJob.terseIOPSWritePos])
       
    def getIOPSRead(self,fioOut):
        '''
        Parses the average read IOPS out of the fio result output.
        @param fioOut The output of the fio performance test.
        @return Read IOPS
        '''
        #index 7 iops read
        fioTerse = fioOut.split(';')
        return int(fioTerse[FioJob.terseIOPSReadPos])
    
    def getIOPSWrite(self,fioOut):
        '''
        Parses the average write IOPS out of the fio result output.
        @param fioOut The output of the fio performance test.
        @return Write IOPS
        '''
        #index 48 iops write
        fioTerse = fioOut.split(';')
        return int(fioTerse[FioJob.terseIOPSWritePos])
       
    def getTotIOWrite(self,fioOut):
        '''
        Parses the write total IO out of the fio result output.
        @param fioOut The output of the fio performance test.
        @return Write total IO in KB.
        '''
        #index 46 write total IO
        fioTerse = fioOut.split(';')
        return int(fioTerse[FioJob.terseTotIOWritePos])
    
    def getWriteLats(self,fioOut):
        '''
        Parses the write total latencies out of the fio result output.
        @param fioOut The output of the fio performance test.
        @return [min,max,mean] total write latencies in microseconds.
        '''
        #index 78 write total latency
        fioTerse = fioOut.split(';')
        return [float(fioTerse[FioJob.terseLatStartWritePos]),
                float(fioTerse[FioJob.terseLatStartWritePos + 1]),
                float(fioTerse[FioJob.terseLatStartWritePos + 2])]
        
    def getReadLats(self,fioOut):
        '''
        Parses the read total latencies out of the fio result output.
        @param fioOut The output of the fio performance test.
        @return [min,max,mean] total read latencies in microseconds.
        '''
        #index 78 write total latency
        fioTerse = fioOut.split(';')
        return [float(fioTerse[FioJob.terseLatStartReadPos]),
                float(fioTerse[FioJob.terseLatStartReadPos + 1]),
                float(fioTerse[FioJob.terseLatStartReadPos + 2])]
        
    def getTotLats(self,fioOut):
        '''
        Parses the read+write total latencies out of the fio result output.
        @param fioOut The output of the fio performance test.
        @return [min,max,mean] total latencies in microseconds.
        '''
        #index 78 write total latency
        fioTerse = fioOut.split(';')
        return [float(fioTerse[FioJob.terseLatStartReadPos]) + 
                      float(fioTerse[FioJob.terseLatStartWritePos]),
                float(fioTerse[FioJob.terseLatStartReadPos + 1]) + 
                      float(fioTerse[FioJob.terseLatStartWritePos + 1]),
                float(fioTerse[FioJob.terseLatStartReadPos + 2]) + 
                      float(fioTerse[FioJob.terseLatStartWritePos + 2])]

    def getTPRead(self,fioOut):
        '''
        Parses the read bandwidth of the fio result output.
        @param fioOut The output of the fio performance test.
        @return Read total bandwidth.
        '''
        #index 6 write total IO
        fioTerse = fioOut.split(';')
        return int(fioTerse[FioJob.terseTPReadPos])
        
    def getTPWrite(self,fioOut):
        '''
        Parses the write bandwidth of the fio result output.
        @param fioOut The output of the fio performance test.
        @return Write total bandwidth.
        '''
        #index 47 write total IO
        fioTerse = fioOut.split(';')
        return int(fioTerse[FioJob.terseTPWritePos])
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
        
        
        