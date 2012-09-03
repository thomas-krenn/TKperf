'''
Created on 04.07.2012

@author: gschoenb
'''
from perfTest.DeviceTest import DeviceTest
from fio.FioJob import FioJob

import logging
import json
from lxml import etree

class HddTest(DeviceTest):
    '''
    A fio performance test for a hard disk.
    '''
      
    ##Number of rounds to carry out the tests
    maxRnds = 128 
      
    def __init__(self,testname,filename,iod):
        '''
        Constructor
        '''
        DeviceTest.__init__(self,testname,filename)
        
        ## A list of matrices with the collected fio measurement values of each round.
        self.__roundMatrices = []
        
        ##IO depth for libaio used by fio
        self.__ioDepth = iod
        
        ##The fio job for the current SSD test
        self.__fioJob = FioJob()
        self.__fioJob.addKVArg("filename",self.getFilename())
        self.__fioJob.addKVArg("name",self.getTestname())
        self.__fioJob.addKVArg("direct","1")
        self.__fioJob.addKVArg("minimal","1")
        self.__fioJob.addKVArg("ioengine","libaio")
        self.__fioJob.addKVArg("iodepth",str(self.__ioDepth))
        self.__fioJob.addSglArg("group_reporting")   

    def getFioJob(self):
        return self.__fioJob
    def getRndMatrices(self):
        return self.__tpRoundMatrices
    
    def toXml(self,root):
     
        r = etree.Element(root)
        
        data = json.dumps(self.__roundMatrices)
        e = etree.SubElement(r,'roundmat')
        e.text = data
        
        data = json.dumps(HddTest.maxRnds)
        e = etree.SubElement(r,'rndnr')
        e.text = data
        
    def fromXml(self,root):
        self.__roundMatrices = json.loads(root.findtext('roundmat'))
        self.__rounds = json.loads(root.findtext('rndnr'))
        logging.info("########### Loading from "+self.getTestname()+".xml ###########")
        logging.info(self.__rounds)
        logging.info(self.__roundMatrices)

class IopsTest(HddTest):
    
    ##Labels of block sizes for IOPS test
    bsLabels = ["64k","16k","4k"]
    
    ##Percentages of mixed workloads for IOPS test.
    mixWlds = [100,50,0]
    
    def __init__(self,testname,filename,iod):
        '''
        Constructor.
        '''

        HddTest.__init__(self, testname, filename, iod)
        self.getFioJob().addKVArg("rw","randrw")
        self.getFioJob().addKVArg("runtime","10")#FIXME Change to 60 seconds
    
    def testRound(self,offset,size):
        '''
        IOPS test round for HDD
        '''
        
        self.getFioJob().addKVArg("offset", str(offset))
        self.getFioJob().addKVArg("size", str(size))
        
        #iterate over mixed rand read and write and vary block size
        #save the output of fio for parsing and retreiving IOPS
        jobOut = ''
        
        rndMatrix = []        
        for i in IopsTest.mixWlds:
            rwRow = []
            for j in IopsTest.bsLabels:
                self.getFioJob().addKVArg("rwmixread",str(i))
                self.getFioJob().addKVArg("bs",j)
                call,jobOut = self.getFioJob().start()
                if call == False:
                    exit(1)
                logging.info("mixLoad: " +str(i))
                logging.info("bs: "+j)
                logging.info(jobOut)
                logging.info("######")
                rwRow.append(self.getFioJob().getIOPS(jobOut))
            rndMatrix.append(rwRow)
        return rndMatrix
    
    def runRounds(self):
        '''
        Run IOPS loops for HDD.
        '''
        rndMatrix = []
        (call,devSizeKB) = self.getDevSizeKB()
        if call == False:
            logging.error("#Could not get size of device.")
            exit(1)
        
        increment = (devSizeKB * 1024) / self.maxRnds
        logging.info("Increment in byte: "+str(increment))
        
        #rounds are the same as for TP
        offset = 0
        for i in range(HddTest.maxRnds):
            logging.info("#################")
            logging.info("Round nr. "+str(i))
            logging.info("Offset "+str(offset))
                
            #TODO It can happen that the rest of the device is smaller
            #than one block size, then the output is 0
            #block size as integer, to check if rest of device is smaller than 1 block size
            #currBs = int(j[0:-1])
                
            #we read and write increment starting at the offset
            rndMatrix = self.testRound(offset,increment)
            self.getRoundMatrices.append(rndMatrix)
            offset += increment
    
        return
    
    def run(self):
        '''
        Print various informations about the Throughput test (steady state informations etc.).
        Moreover call the functions to plot the results.
        '''
        logging.info("########### Starting HDD IOPS Test ###########")
        self.runRounds()
        logging.info("Round IOPS results: ")
        logging.info(self.getRndMatrices())
        return True
    
class TPTest(HddTest):
   
    
    ##Labels of block sizes for throughput test
    bsLabels = ["1024k","4k"]
     
    def __init__(self,testname,filename,iod):
        '''
        Constructor.
        '''
        HddTest.__init__(self, testname, filename, iod)
        self.getFioJob().addKVArg("runtime","60")#FIXME Change to 60 seconds or remove it
        
        
    def testRound(self,bs,offset,size):
        '''
        Carry a read and write test over the whole device.
        This is done with different block sizes.
        @param bs The current block size to use.
        @param offset The offset to start testing.
        @param size The size to read starting from offset.
        @return Read and Write bandwidths [tpRead,tpWrite]
        '''
        self.getFioJob().addKVArg("offset", str(offset))
        self.getFioJob().addKVArg("size", str(size))
        self.getFioJob().addKVArg("bs",bs)   
      
        jobOut = ''
        tpRead = 0 #read bandwidth
        tpWrite = 0#write bandwidth

        #start read tests
        self.getFioJob().addKVArg("rw","read")
        call,jobOut = self.getFioJob().start()
        if call == False:
            exit(1)
        logging.info("Read TP test:")
        logging.info(jobOut)
        logging.info("######")
        tpRead = self.getFioJob().getTPRead(jobOut)
    
        #start write tests
        self.getFioJob().addKVArg("rw","write")
        call,jobOut = self.getFioJob().start()
        if call == False:
            exit(1)
        logging.info("Write TP test:")
        logging.info(jobOut)
        logging.info("######")
        tpWrite = self.getFioJob().getTPWrite(jobOut)
            
        return [tpRead,tpWrite]
    
    def runRounds(self):
        
        (call,devSizeKB) = self.getDevSizeKB()
        if call == False:
            logging.error("#Could not get size of device.")
            exit(1)
        
        #in each round the offset is incremented
        #the offset has to be in bytes
        #if it can be divided by 1024, we can also divide it by 128
        increment = (devSizeKB * 1024) / HddTest.maxRnds
        logging.info("Increment in byte: "+str(increment))

        #rounds are the same for IOPS and throughput
        for j in TPTest.bsLabels:
            tpRead_l = []
            tpWrite_l = []
            logging.info("#################")
            logging.info("Current block size. "+str(j))
            #set offset back for current bs
            offset = 0
            for i in range(HddTest.maxRnds):
                logging.info("######")
                logging.info("Round nr. "+str(i))
                logging.info("Offset "+str(offset))
                
                #TODO It can happen that the rest of the device is smaller
                #than one block size, then the output is 0
                #block size as integer, to check if rest of device is smaller than 1 block size
                #currBs = int(j[0:-1])
                
                #we read and write increment starting at the offset
                tpRead,tpWrite = self.testRound(j,offset,increment)
                tpRead_l.append(tpRead)
                tpWrite_l.append(tpWrite)
                offset += increment
            #finished current bs
            self.getRndMatrices().append([tpRead_l,tpWrite_l])
            
    def run(self):
        '''
        Print various informations about the Throughput test (steady state informations etc.).
        Moreover call the functions to plot the results.
        '''
        logging.info("########### Starting HDD Throughput Test ###########")
        self.runRounds()
        logging.info("Round TP results: ")
        logging.info(self.getRndMatrices())
        return True