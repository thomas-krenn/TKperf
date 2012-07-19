'''
Created on 04.07.2012

@author: gschoenb
'''
from perfTest.DeviceTest import DeviceTest
from fio.FioJob import FioJob
import plots.genPlots as pgp

import logging

class HddTest(DeviceTest):
    '''
    A fio performance test for a hard disk.
    '''
    
    ##Number of rounds to carry out tp tests
    tpTestRnds = 128
    
    ##Labels of block sizes for throughput test
    tpBsLabels = ["1024k","4k"]
    
    def __init__(self,testname,filename):
        '''
        Constructor
        '''
        super(HddTest,self).__init__(testname,filename)
        
        ## A list of matrices with the throughput data.
        self.__tpRoundMatrices = []
        
    def getTPRndMatrices(self):
        return self.__tpRoundMatrices
    
    def resetTestData(self):
        '''
        Reset all class attributes. This is necessary if
        multiple tests are using the same attributes as
        internal states.
        '''
        self.__tpRoundMatrices = []
    
    def tpTestRnd(self,bs,offset,size):
        '''
        Carry a read and write test over the whole device.
        This is done with different block sizes.
        @param bs The current block size to use.
        @param offset The offset to start testing.
        @param size The size to read starting from offset.
        @return Read and Write bandwidths [tpRead,tpWrite]
        '''
        job = FioJob()
        job.addKVArg("filename",self.getFilename())
        job.addKVArg("name",self.getTestname())
        job.addKVArg("direct","1")
        job.addKVArg("runtime","10")#FIXME Change to 60 seconds
        job.addKVArg("offset", str(offset))
        job.addKVArg("size", str(size))
        job.addKVArg("minimal","1")
        job.addSglArg("group_reporting")  
        job.addKVArg("bs",bs)   
      
        jobOut = ''
        tpRead = 0 #read bandwidth
        tpWrite = 0#write bandwidth

        #start read tests
        job.addKVArg("rw","read")
        call,jobOut = job.start()
        if call == False:
            exit(1)
        logging.info("Read TP test:")
        logging.info(jobOut)
        logging.info("######")
        tpRead = job.getTPRead(jobOut)
    
        #start write tests
        job.addKVArg("rw","write")
        call,jobOut = job.start()
        if call == False:
            exit(1)
        logging.info("Write TP test:")
        logging.info(jobOut)
        logging.info("######")
        tpWrite = job.getTPWrite(jobOut)
            
        return [tpRead,tpWrite]
    
    def tpTest(self):
        
        (call,devSizeKB) = self.getDevSizeKB()
        if call == False:
            logging.error("#Could not get size of device.")
            exit(1)
        
        #in each round the offset is incremented
        #the offset has to be in bytes
        #if it can be divided by 1024, we can also divide it by 128
        increment = (devSizeKB * 1024) / self.tpTestRnds
        logging.info("Increment in byte: "+str(increment))

        #rounds are the same for IOPS and throughput
        for j in HddTest.tpBsLabels:
            tpRead_l = []
            tpWrite_l = []
            logging.info("#################")
            logging.info("Current block size. "+str(j))
            #set offset back for current bs
            offset = 0
            for i in range(self.tpTestRnds):
                logging.info("######")
                logging.info("Round nr. "+str(i))
                logging.info("Offset "+str(offset))
                
                #TODO It can happen that the rest of the device is smaller
                #than one block size, then the output is 0
                #block size as integer, to check if rest of device is smaller than 1 block size
                #currBs = int(j[0:-1])
                
                #we read an icrement starting at the offset
                tpRead,tpWrite = self.tpTestRnd(j,offset,increment)
                tpRead_l.append(tpRead)
                tpWrite_l.append(tpWrite)
                offset += increment
            #finished current bs
            self.__tpRoundMatrices.append([tpRead_l,tpWrite_l])
            
    def runTpTest(self):
        '''
        Print various informations about the Throughput test (steady state informations etc.).
        Moreover call the functions to plot the results.
        '''
        #ensure to start at initialization state
        self.resetTestData()
        logging.info("########### Starting HDD Throughput Test ###########")
        self.tpTest()
        logging.info("Round TP results: ")
        logging.info(self.__tpRoundMatrices)
        
        pgp.tpStdyStConvPlt(self, "rw","hdd")

        return True