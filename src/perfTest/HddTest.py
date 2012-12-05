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
      
    def __init__(self,testname,devicename,nj,iod):
        '''
        Constructor
        @param nj Number of jobs for Fio.
        @param iod IO depth for libaio used by Fio.
        '''
        DeviceTest.__init__(self,testname,devicename)
        
        ## A list of matrices with the collected fio measurement values of each round.
        self.__roundMatrices = []
        
        ##Number of jobs started by fio
        self.__numJobs = nj
        
        ##IO depth for libaio used by fio
        self.__ioDepth = iod
        
        ##The fio job for the current SSD test
        self.__fioJob = FioJob()
        self.__fioJob.addKVArg("filename",self.getDevName())
        self.__fioJob.addKVArg("name",self.getTestname())
        self.__fioJob.addKVArg("direct","1")
        self.__fioJob.addKVArg("minimal","1")
        self.__fioJob.addKVArg("ioengine","libaio")
        self.__fioJob.addKVArg("numjobs",str(self.__numJobs))
        self.__fioJob.addKVArg("iodepth",str(self.__ioDepth))
        self.__fioJob.addSglArg("group_reporting")

    def getFioJob(self):
        return self.__fioJob
    
    def getRndMatrices(self):
        return self.__roundMatrices
    
    def getNj(self):
        return self.__numJobs
    
    def getIod(self):
        return self.__ioDepth
    
    def setNj(self,nj):
        self.__numJobs = nj
    
    def setIod(self,iod):
        self.__ioDepth = iod
    
    def toXml(self,root):
     
        r = etree.Element(root)
        
        #Add the fio version to the xml
        data = json.dumps(self.getFioJob().getFioVersion())
        e = etree.SubElement(r,'fioversion')
        e.text = data
        
        data = json.dumps(self.getNj())
        e = etree.SubElement(r,'numjobs')
        e.text = data
        
        data = json.dumps(self.getIod())
        e = etree.SubElement(r,'iodepth')
        e.text = data
        
        data = json.dumps(self.__roundMatrices)
        e = etree.SubElement(r,'roundmat')
        e.text = data
        
        data = json.dumps(HddTest.maxRnds)
        e = etree.SubElement(r,'rndnr')
        e.text = data
        
        return r
        
    def fromXml(self,root):
        if(root.findtext('fioversion')):
            self.getFioJob().setFioVersion(json.loads(root.findtext('fioversion')))
        else:
            self.getFioJob().setFioVersion('n.a.')
        self.setNj(json.loads(root.findtext('numjobs')))
        self.setIod(json.loads(root.findtext('iodepth')))
        self.__roundMatrices = json.loads(root.findtext('roundmat'))
        HddTest.maxRnds = json.loads(root.findtext('rndnr'))
        logging.info("########### Loading from "+self.getTestname()+".xml ###########")
        logging.info(HddTest.maxRnds)
        logging.info(self.__roundMatrices)

class IopsTest(HddTest):
    
    ##Labels of block sizes for IOPS test
    bsLabels = ["64k","16k","4k"]
    
    ##Percentages of mixed workloads for IOPS test.
    mixWlds = [100,50,0]
    
    def __init__(self,testname,devicename,nj,iod):
        '''
        Constructor.
        '''

        HddTest.__init__(self,testname,devicename,nj,iod)
        self.getFioJob().addKVArg("rw","randrw")
        #TODO Remove the runtime to test the whole sector
        self.getFioJob().addKVArg("runtime","60")
    
    def testRound(self,offset,size):
        '''
        Carry out one IOPS test round.
        The round consists of two inner loops: one iterating over the
        percentage of random reads/writes in the mixed workload, the other
        over different block sizes.
        @return A matrix containing the sum of average IOPS.
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
        #we must ensure that increment can be divided by 4096
        #as we need to align the direct IO to block size. If it
        #is an advanced sector format with 4k 4096 is ok, if the 
        #sector size i 512b 4096 is also ok
        rem = increment % 4096
        if rem != 0:
            increment = increment - rem
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
            self.getRndMatrices().append(rndMatrix)
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
    '''
    A class to carry out the Throughput test for HDDs.
    '''
    ##Labels of block sizes for throughput test
    bsLabels = ["1024k","4k"]
     
    def __init__(self,testname,devicename,nj,iod):
        '''
        Constructor.
        '''
        HddTest.__init__(self, testname, devicename, nj, iod)
        
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
        
        (call,devSizeB) = self.getDevSizeB()
        if call == False:
            logging.error("#Could not get size of device.")
            exit(1)
        
        #in each round the offset is incremented
        #if it can be divided by 512, we can also divide it by 128
        increment = devSizeB / HddTest.maxRnds
        #we must ensure that increment can be divided by 4096
        #as we need to align the direct IO to block size. If it
        #is an advanced sector format with 4k 4096 is ok, if the 
        #sector size i 512b 4096 is also ok
        rem = increment % 4096
        if rem != 0:
            increment = increment - rem
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