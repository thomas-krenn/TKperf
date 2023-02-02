''' @package FioJob
A module realizing a fio job run.
'''
import subprocess
import logging
import re
import json
from lxml import etree

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

    ## Position of read total IO in the fio terse output
    terseTotIOReadPos = 5

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
        ## Fio path
        self.__fioPath = None
        ## Fio version
        self.__fioVersion = None
        ## Key value arguments e.g. name="test"
        self.__fioKVArgs = {}
        ## Single arguments e.g. group_reporting
        self.__fioSglArgs = []

    def __str__(self):
        ''' Return a string representation of the fio executable. '''   
        res = "fio: " + self.__fioPath + ", " + self.__fioVersion
        return res

    def initialize(self):
        ''' Initialize Fio path and version. '''
        fio = subprocess.Popen(['which', 'fio'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
        stdout = fio.communicate()[0]
        if fio.returncode != 0:
            logging.error("# Error: command 'which fio' returned an error code.")
            raise RuntimeError("which fio command error")

        self.__fioPath = stdout.rstrip("\n");
        fio = subprocess.Popen(['fio','--version'],stdout=subprocess.PIPE,universal_newlines=True)
        self.__fioVersion = fio.communicate()[0]

    def getFioVersion(self):
        ''' Return the current Fio version string. '''
        return self.__fioVersion

    def setFioVersion(self,fioStr):
        ''' Set the used Fio version (useful if loading from xml). '''
        self.__fioVersion = fioStr

    def checkFioVersion(self):
        ''' Check if the Fio version is high enough. '''
        if self.__fioVersion != None:
            match = re.search(r'[\d\.]+',self.__fioVersion)
            if match == None:
                logging.error("# Error: checking fio version returned a none string.")
                raise RuntimeError("fio version string error")
            version = match.group().split('.')
            if int(version[0]) < 2:
                logging.error("# Error: the fio version is to old, ensure to use > 2.0.3.")
                raise RuntimeError("fio version to old error")
            if int(version[0]) >= 2:
                if int(version[1]) == 0:
                    if int(version[2]) < 3:
                        logging.error("# Error: the fio version is to old, ensure to use > 2.0.3.")
                        raise RuntimeError("fio version to old error")

    def appendXml(self,root):
        '''
        Append the information about Fio to a XML node. 
        @param root The xml root tag to append the new elements to.
        ''' 
        data = json.dumps(self.__fioVersion)
        e = etree.SubElement(root,'fioversion')
        e.text = data

    def fromXml(self,root):
        '''
        Loads the information about Fio from XML.
        @param root The given element containing the information about
        the object to be initialized.
        '''
        if root.findtext('fioversion'):
            self.__fioVersion = json.loads(root.findtext('fioversion'))
        else:
            self.__fioVersion = 'n.a'
        logging.info("# Loading Fio version from xml")

    def getKVArgs(self):
        ''' Return the current configured Fio key value arguments. '''
        return self.__fioKVArgs
    
    def getSglArgs(self):
        ''' Return the current configured Fio single key arguments. '''
        return self.__fioSglArgs
    
    def addKVArg(self,key,value):
        ''' Add a key value pair as an argument to fio.
        @param key Name of the option for Fio.
        @param value Value for the given Fio option.
        '''
        self.__fioKVArgs[key] = value
        
    def addSglArg(self,key):
        ''' Add a single value option to fio argument list.
        @param key Name of the option being added.
        ''' 
        self.__fioSglArgs.append(key)
        
    def prepKVArgs(self):
        ''' Generate an argument list out of the dictionary suited for fio. '''
        argList = [self.__fioPath]
        for k,v in self.__fioKVArgs.items():
            argList.append('--' + k + '=' + v)
        return argList
    
    def prepSglArgs(self,argList):
        ''' Generate an argument list out of the single key arguments. '''
        for k in self.__fioSglArgs:
            argList.append('--' + k)
        return argList
        
    def start(self):
        ''' Start a Fio job with its argument list.
        The argument list defines the parameters given to Fio.
        @return [True,standard output] of the Fio test or [False,0] on error.
        '''
        args = self.prepKVArgs()
        args = self.prepSglArgs(args)
        logging.info('%s',args)
        if len(args) == 0:
            logging.error("Error: Fio argument list is empty.")
            exit(1)
        out = subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
        (stdout,stderr) = out.communicate()
        if stderr != '':
            logging.error("Fio encountered an error: " + stderr)
            return [False,'']
        else:
            return [True,stdout]
        
    def getIOPS(self,fioOut):
        '''
        Parses the average IOPS out of the Fio result output.
        @param fioOut The output of the Fio performance test.
        @return Sum of read IOPS and write IOPS.
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
        Parses the average write IOPS out of the Fio result output.
        @param fioOut The output of the Fio performance test.
        @return Write IOPS
        '''
        #index 48 iops write
        fioTerse = fioOut.split(';')
        return int(fioTerse[FioJob.terseIOPSWritePos])
       
    def getTotIOWrite(self,fioOut):
        '''
        Parses the write total IO out of the Fio result output.
        @param fioOut The output of the Fio performance test.
        @return Write total IO in KB.
        '''
        #index 46 write total IO
        fioTerse = fioOut.split(';')
        return int(fioTerse[FioJob.terseTotIOWritePos])

    def getTotIORead(self,fioOut):
        '''
        Parses the read total IO out of the Fio result output.
        @param fioOut The output of the Fio performance test.
        @return Write total IO in KB.
        '''
        #index 5 read total IO
        fioTerse = fioOut.split(';')
        return int(fioTerse[FioJob.terseTotIOReadPos])

    def getWriteLats(self,fioOut):
        '''
        Parses the write total latencies out of the Fio result output.
        @param fioOut The output of the Fio performance test.
        @return [min,max,mean] total write latencies in microseconds.
        '''
        #index 78 write total latency
        fioTerse = fioOut.split(';')
        return [float(fioTerse[FioJob.terseLatStartWritePos]),
                float(fioTerse[FioJob.terseLatStartWritePos + 1]),
                float(fioTerse[FioJob.terseLatStartWritePos + 2])]
        
    def getReadLats(self,fioOut):
        '''
        Parses the read total latencies out of the Fio result output.
        @param fioOut The output of the Fio performance test.
        @return [min,max,mean] total read latencies in microseconds.
        '''
        #index 78 write total latency
        fioTerse = fioOut.split(';')
        return [float(fioTerse[FioJob.terseLatStartReadPos]),
                float(fioTerse[FioJob.terseLatStartReadPos + 1]),
                float(fioTerse[FioJob.terseLatStartReadPos + 2])]
        
    def getTotLats(self,fioOut):
        '''
        Parses the read+write total latencies out of the Fio result output.
        @param fioOut The output of the Fio performance test.
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
        Parses the read bandwidth of the Fio result output.
        @param fioOut The output of the Fio performance test.
        @return Read total bandwidth.
        '''
        #index 6 write total IO
        fioTerse = fioOut.split(';')
        return int(fioTerse[FioJob.terseTPReadPos])
        
    def getTPWrite(self,fioOut):
        '''
        Parses the write bandwidth of the Fio result output.
        @param fioOut The output of the Fio performance test.
        @return Write total bandwidth.
        '''
        #index 47 write total IO
        fioTerse = fioOut.split(';')
        return int(fioTerse[FioJob.terseTPWritePos])