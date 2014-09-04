'''
Created on Aug 25, 2014

@author: gschoenb
'''

from abc import ABCMeta, abstractmethod
import logging
from collections import deque
from lxml import etree
import json

from perfTest.Devices import Device
from perfTest.Options import Options
from perfTest.StdyState import StdyState
from fio.FioJob import FioJob

class DeviceTest(object):
    '''
    Representing a performance test, run on a device.
    '''
    __metaclass__ = ABCMeta

    def __init__(self,testname,device,options=None):
        '''
        Constructor
        @param testname Name of the test, specifies the output file
        @param device The tested device, a device object
        '''
        ## The name of the test, is used to give the resulting files a name
        self.__testname = testname
        ## The tested device, a Device object
        self.__device = device
        ## User defined options
        self.__options = options
        ## A fio job used to run the tests
        self.__fioJob = self.initFio()

    def getTestname(self): return self.__testname
    def getDevice(self): return self.__device
    def getOptions(self): return self.__options
    def getFioJob(self): return self.__fioJob

    def initFio(self):
        '''
        Initializes the fio job to run a performance test.
        @return An initialized fio job object
        '''
        job = FioJob()
        job.addKVArg("filename",self.__device.getDevPath())
        job.addKVArg("name",self.__testname)
        job.addKVArg("direct","1")
        job.addKVArg("minimal","1")
        job.addKVArg("ioengine","libaio")
        if self.__options == None:
            job.addKVArg("numjobs",str(1))
            job.addKVArg("iodepth",str(1))
        else:
            if self.getOptions().getNj() != None:
                job.addKVArg("numjobs",str(self.getOptions().getNj()))
            if self.getOptions().getIod() != None:
                job.addKVArg("iodepth",str(self.getOptions().getIod()))
            if self.getOptions().getXargs() != None:
                for arg in self.getOptions().getXargs():
                    job.addSglArg(arg)
        job.addSglArg("group_reporting")
        return job

    @abstractmethod
    def testRound(self):
        ''' A test round for a specific device performance test. '''
    @abstractmethod
    def runRounds(self):
        ''' Run the specific test rounds. '''
    @abstractmethod
    def run(self):
        ''' Run the type specific performance test. '''
    
    @abstractmethod
    def toXml(self):
        ''' Get the Xml representation of a test. '''

class SsdIopsTest(DeviceTest):
    '''
    Representing an IOPS test for a ssd based device.
    '''
    ##Labels of block sizes
    bsLabels = ["1024k","128k","64k","32k","16k","8k","4k","512"]
    ##Percentages of mixed workloads
    mixWlds = [100,95,65,50,35,5,0]

    def __init__(self,testname,device,options=None):
        '''
        Constructor.
        '''
        super(SsdIopsTest,self).__init__(testname,device,options)
        ## A list of matrices with the collected fio measurement values of each round.
        self.__roundMatrices = []
        self.__stdyState = StdyState()
        self.getFioJob().addKVArg("rw","randrw")
        self.getFioJob().addKVArg("runtime","60")
        self.getFioJob().addSglArg("time_based")

    def getRndMatrices(self): return self.__roundMatrices
    def getStdyState(self): return self.__stdyState

    def toLog(self):
        '''
        Log information about the steady state and how it 
        has been reached.
        '''
        logging.info("Round matrices: ")
        logging.info(self.__roundMatrices)
        self.getStdyState().toLog()

    def testRound(self):
        '''
        Carry out one IOPS test round.
        The round consists of two inner loops: one iterating over the
        percentage of random reads/writes in the mixed workload, the other
        over different block sizes.
        @return A matrix containing the sum of average IOPS.
        '''
        jobOut = '' #Fio job output
        rndMatrix = []
        for i in SsdIopsTest.mixWlds:
            rwRow = []
            for j in SsdIopsTest.bsLabels:
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
        Carry out the IOPS test rounds and check if the steady state is reached.
        For a maximum of 25 rounds the test loop is carried out. After each
        test round we check for a measurement window of the last 5 rounds if
        the steady state has been reached.
        @return True if the steady state has been reached, False if not.
        '''
        rndMatrix = []
        steadyValues = deque([])#List of 4k random writes IOPS
        xranges = deque([])#Rounds of current measurement window
        
        for i in range(StdyState.testRnds):
            logging.info("#################")
            logging.info("Round nr. "+str(i))
            rndMatrix = self.testRound()
            self.getRndMatrices().append(rndMatrix)
            # Use the last row and its next to last value
            #-> 0/100% r/w and 4k for steady state detection
            steadyValues.append(rndMatrix[-1][-2])
            xranges.append(i)
            if i > 4:
                xranges.popleft()
                steadyValues.popleft()
            #check if the steady state has been reached in the last 5 rounds
            if i >= 4:
                steadyState = self.getStdyState().checkSteadyState(xranges,steadyValues,i)
                if steadyState == True:
                    break
        #Return current steady state
        return self.getStdyState().isSteady()

    def run(self):
        '''
        Start the rounds, log the steady state infos.
        @return True if all tests were run
        '''
        try: 
            self.getDevice().secureErase()
        except RuntimeError:
            logging.error("# Could not carry out secure erase for "+self.getDevice().getDevPath())
        try:
            if self.getOptions() == None:
                self.getDevice().precondition(1,1)
            else:
                if self.getOptions().getNj() != None:
                    nj = self.getOptions().getNj()
                if self.getOptions().getIod() != None:
                    iod = self.getOptions().getIod()
                self.getDevice().precondition(nj,iod)
        except RuntimeError:
            logging.error("# Could not carry out preconditioning for "+self.getDevice().getDevPath())
        logging.info("########### Starting IOPS Test ###########")
        steadyState = self.runRounds()
        if steadyState == False:
            logging.info("# Steady State has not been reached for IOPS Test.")
        self.toLog()
        return True

    def toXml(self,root):
        '''
        Get the Xml representation of the test.
        @param root Name of the new root Xml node
        @return An xml root element containing the information about the test
        ''' 
        r = etree.Element(root)
        data = json.dumps(self.__roundMatrices)
        e = etree.SubElement(r,'roundmat')
        e.text = data
        self.getStdyState().appendXml(r)
        return r

class SsdLatencyTest(DeviceTest):
    '''
    Representing a Latency test for a ssd based device.
    '''
    ##Percentages of mixed workloads.
    mixWlds = [100,65,0]
    ##Labels of block sizes.
    bsLabels = ["8k","4k","512"]

    def __init__(self,testname,device,options=None):
        '''
        Constructor.
        '''
        if options != None:
            #For latency the specification says to use 1 job/thread, 1 outstanding IO
            options.setNj(1)
            options.setNj(1)
        super(SsdLatencyTest,self).__init__(testname,device,options)
        ## A list of matrices with the collected fio measurement values of each round.
        self.__roundMatrices = []
        self.__stdyState = StdyState()
        self.getFioJob().addKVArg("rw","randrw")
        self.getFioJob().addKVArg("runtime","60")
        self.getFioJob().addSglArg("time_based")

    def getRndMatrices(self): return self.__roundMatrices
    def getStdyState(self): return self.__stdyState

    def toLog(self):
        '''
        Log information about the steady state and how it 
        has been reached.
        '''
        logging.info("Round matrices: ")
        logging.info(self.__roundMatrices)
        self.getStdyState().toLog()

    def testRound(self):
        '''
        Carry out one latency test round.
        The round consists of two inner loops: one iterating over the
        percentage of random reads/writes in the mixed workload, the other
        over different block sizes.
        @return A matrix containing [min,max,mean] latencies of the round.
        '''
        jobOut = ''
        rndMatrix = []        
        for i in SsdLatencyTest.mixWlds:
            rwRow = []
            for j in SsdLatencyTest.bsLabels:
                self.getFioJob().addKVArg("rwmixread",str(i))
                self.getFioJob().addKVArg("bs",j)
                call,jobOut = self.getFioJob().start()
                if call == False:
                    exit(1)
                logging.info("mixLoad: " +str(i))
                logging.info("bs: "+j)
                logging.info(jobOut)
                logging.info("######")
                if i == 65:
                    #if we have a mixed workload weight the latencies
                    l = [0,0,0]
                    r = self.getFioJob().getReadLats(jobOut)
                    w = self.getFioJob().getWriteLats(jobOut)
                    #FIXME Is this also correct for Min and Max?
                    l[0] = (0.65 * r[0]) + (0.35 * w[0])
                    l[1] = (0.65 * r[1]) + (0.35 * w[1])
                    l[2] = (0.65 * r[2]) + (0.35 * w[2])
                else:
                    l = self.getFioJob().getTotLats(jobOut)
                rwRow.append(l)
            rndMatrix.append(rwRow)
        return rndMatrix

    def runRounds(self):
        '''
        Carry out the latency test rounds and check if the steady state is reached.
        For a maximum of 25 rounds the test loop is carried out. After each
        test round we check for a measurement window of the last 5 rounds if
        the steady state has been reached.
        @return True if the steady state has been reached, False if not.
        '''
        rndMatrix = []
        steadyValues = deque([])
        xranges = deque([])#Rounds of current measurement window
        
        for i in range(StdyState.testRnds):
            logging.info("#################")
            logging.info("Round nr. "+str(i))
            rndMatrix = self.testRound()
            self.getRndMatrices().append(rndMatrix)
            #Latencies always consist of [min,max,mean] latency
            #Take mean/average for steady state detection
            steadyValues.append(rndMatrix[-1][-2][2])
            xranges.append(i)
            if i > 4:
                xranges.popleft()
                steadyValues.popleft()
            #check if the steady state has been reached in the last 5 rounds
            if i >= 4:
                steadyState = self.getStdyState().checkSteadyState(xranges,steadyValues,i)
                if steadyState == True:
                    break
        #Return current steady state
        return self.getStdyState().isSteady()

    def run(self):
        '''
        Start the rounds, log the steady state infos.
        @return True if all tests were run
        '''
        try: 
            self.getDevice().secureErase()
        except RuntimeError:
            logging.error("# Could not carry out secure erase for "+self.getDevice().getDevPath())
        try:
            if self.getOptions() == None:
                self.getDevice().precondition(1,1)
            else:
                if self.getOptions().getNj() != None:
                    nj = self.getOptions().getNj()
                if self.getOptions().getIod() != None:
                    iod = self.getOptions().getIod()
                self.getDevice().precondition(nj,iod)
        except RuntimeError:
            logging.error("# Could not carry out preconditioning for "+self.getDevice().getDevPath())
        logging.info("########### Starting Latency Test ###########")
        steadyState = self.runRounds()
        if steadyState == False:
            logging.info("# Steady State has not been reached for Latency Test.")
        self.toLog()
        return True

    def toXml(self,root):
        '''
        Get the Xml representation of the test.
        @param root Name of the new root Xml node
        @return An xml root element containing the information about the test
        ''' 
        r = etree.Element(root)
        data = json.dumps(self.__roundMatrices)
        e = etree.SubElement(r,'roundmat')
        e.text = data
        self.getStdyState().appendXml(r)
        return r

class SsdTPTest(DeviceTest):
    '''
    A class to carry out the Throughput test.
    '''
    ##Labels of block sizes for throughput test
    bsLabels = ["1024k","64k","8k","4k","512",]
    
    def __init__(self,testname,device,options):
        '''
        Constructor.
        '''
        super(SsdTPTest,self).__init__(testname,device,options)
        ## A list of matrices with the collected fio measurement values of each round.
        self.__roundMatrices = []
        self.__stdyState = StdyState()
        self.getFioJob().addKVArg("runtime","60")
        self.getFioJob().addSglArg("time_based")

    def getRndMatrices(self): return self.__roundMatrices
    def getStdyState(self): return self.__stdyState

    def toLog(self):
        '''
        Log information about the steady state and how it 
        has been reached.
        '''
        logging.info("Round matrices: ")
        logging.info(self.__roundMatrices)
        self.getStdyState().toLog()

    def testRound(self,bs):
        '''    
        Carry out one test round of the throughput test.
        Read and Write throughput is tested with the given block size
        @param bs The current block size to use.
        @return Read and Write bandwidths [tpRead,tpWrite]
        '''
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
        '''
        Carry out the throughput/bandwidth test rounds and check if the steady state is reached.
         @return True if the steady state has been reached, False if not.
        '''
        stdyValsWrite = deque([])#List of 1M sequential write IOPS
        xrangesWrite = deque([])#Rounds of current measurement window
        
        #rounds are the same for IOPS and throughput
        for j in SsdTPTest.bsLabels:
            try: 
                self.getDevice().secureErase()
            except RuntimeError:
                logging.error("# Could not carry out secure erase for "+self.getDevice().getDevPath())

            tpRead_l = []
            tpWrite_l = []
            logging.info("#################")
            logging.info("Current block size. "+str(j))
            
            for i in range(StdyState.testRnds):
                logging.info("######")
                logging.info("Round nr. "+str(i))
                tpRead,tpWrite = self.testRound(j)
                tpRead_l.append(tpRead)
                tpWrite_l.append(tpWrite)
                
                #if the rounds have been set by steady state for 1M block size
                #we need to carry out only i rounds for the other block sizes
                #as steady state has already been reached
                if self.getRnds() != 0 and self.getRnds() == i:
                    self.getRndMatrices().append([tpRead_l,tpWrite_l])
                    break
                
                # Use 1M block sizes sequential write for steady state detection
                if j == "1024k":
                    stdyValsWrite.append(tpWrite)
                    xrangesWrite.append(i)
                    if i > 4:
                        xrangesWrite.popleft()
                        stdyValsWrite.popleft()
                        #check if the steady state has been reached in the last 5 rounds
                    if i >= 4:
                        steadyState = self.getStdyState().checkSteadyState(xrangesWrite,stdyValsWrite,i)
                        #reached a steady state
                        if steadyState == True:
                            logging.info("Reached steady state at round %d",i)
                        #running from 0 to 24
                        if i == ((StdyState.testRnds) - 1):
                            self.setReachStdyState(False)
                            logging.warn("#Did not reach steady state for bs %s",j)
                        #In both cases we are done with steady state checking
                        if steadyState == True or i == ((StdyState.testRnds) - 1):
                            self.getRndMatrices().append([tpRead_l,tpWrite_l])
                            #Done with 1M block size
                            break
        #Return current steady state
        return self.getStdyState().isSteady()
        
    def run(self):
        '''
        Start the rounds, log the steady state infos.
        @return True if all tests were run
        '''
        logging.info("########### Starting Throughput Test ###########")
        steadyState = self.runRounds()
        if steadyState == False:
            logging.info("# Steady State has not been reached for Throughput Test.")
        self.toLog()
        return True

    def toXml(self,root):
        '''
        Get the Xml representation of the test.
        @param root Name of the new root Xml node
        @return An xml root element containing the information about the test
        ''' 
        r = etree.Element(root)
        data = json.dumps(self.__roundMatrices)
        e = etree.SubElement(r,'roundmat')
        e.text = data
        self.getStdyState().appendXml(r)
        return r

class SsdWriteSatTest(DeviceTest):
    '''
    A class to carry out the Write Saturation test.
    '''
    
    def __init__(self,testname,device,options=None):
        '''
        Constructor.
        '''
        super(SsdWriteSatTest,self).__init__(testname,device,options)
        ##Number of rounds until write saturation test ended
        self.__rounds = 0
        ##Write saturation results: [iops_l,lats_l]
        self.__roundMatrices = []
        self.getFioJob().addKVArg("rw","randwrite")
        self.getFioJob().addKVArg("bs","4k")   
        self.getFioJob().addKVArg("runtime","60")
        self.getFioJob().addSglArg("time_based")

    def getRnds(self): return self.__rounds
    def getRndMatrices(self): return self.__roundMatrices

    def testRound(self):
        '''
        Carry out one test round of the write saturation test.
        The round consists of random writing with 4k bs for one minute
        @return [TotWriteIO,IOPS,[min,max,mean lats]]
        '''
        (call,jobOut) = self.getFioJob().start()
        if call == False:
            exit(1)
        
        writeIO = self.getFioJob().getTotIOWrite(jobOut)
        iops = self.getFioJob().getIOPS(jobOut)
        lats = self.getFioJob().getWriteLats(jobOut)
        
        logging.info(jobOut)
        logging.info("#IOPS: " + str(iops))
        logging.info("#Tot Write IO: " + str(writeIO))
        logging.info("#Latencies: " + str(lats))
        logging.info("######")
        return [writeIO,iops,lats]
    
    def runRounds(self):
        '''
        Carry out the write saturation test rounds
        '''
        (call,devSzB) = self.getDevSizeB()
        if call == False:
            logging.error("#Could not get size of device.")
            exit(1)
        else:
            logging.info("#Device size in Byte: " + str(devSzB))
        totWriteIO = 0 #total written IO in KB, must be greater than 4xDevice 
        #carry out the test for a maximum of 24h, one round runs for 1 minute
        maxRounds = 60*24
        
        writeIO = 0
        iops_l = [] #overall list of iops
        iops = 0 #IOPS per round
        lats_l = []#overall list of latencies
        lats = []#latencies per round
        
        self.__rounds = maxRounds
        #assume all rounds must be carried out            
        for i in range(maxRounds):
            logging.info("#################")
            logging.info("Round nr. "+str(i))
            writeIO,iops,lats = self.testRound()
            iops_l.append(iops)
            lats_l.append(lats)
            totWriteIO += writeIO
            if i == 0:
                logging.info("#If write IO stays steady, it will take "
                             +str((devSzB * 4) / (writeIO * 1024))+" rounds to complete.")
            
            #Check if 4 times the device size has been reached
            if (totWriteIO * 1024) >= (devSzB * 4):
                self.__rounds = i
                break
        self.__roundMatrices.append(iops_l)
        self.__roundMatrices.append(lats_l)
        logging.info("#Write saturation has written " + str(totWriteIO) + "KB")

    def run(self):
        '''
        Start the rounds, log number of rounds until 4 times device size was written.
        @return True if all tests were run
        '''
        try: 
            self.getDevice().secureErase()
        except RuntimeError:
            logging.error("# Could not carry out secure erase for "+self.getDevice().getDevPath())
        logging.info("########### Starting Write Saturation Test ###########")
        self.runRounds()
        logging.info("Write Sat rounds: ")
        logging.info(self.__rounds)
        logging.info("Round Write Saturation results: ")
        logging.info(self.__roundMatrices)
        return True

    def toXml(self,root):
        '''
        Get the Xml representation of the test.
        @param root Name of the new root Xml node
        @return An xml root element containing the information about the test
        ''' 
        #root element of current xml child
        r = etree.Element(root)
        
        data = json.dumps(self.__roundMatrices)
        e = etree.SubElement(r,'roundmat')
        e.text = data
        
        data = json.dumps(self.__rounds)
        e = etree.SubElement(r,'rndnr')
        e.text = data
        return r

    def fromXml(self,root):
        '''
        Load and set from an XML representation of the write saturation test.
        @param root Name of root element to append xml childs to
        '''
        self.__roundMatrices = json.loads(root.findtext('roundmat'))
        self.__rounds = json.loads(root.findtext('rndnr'))
        logging.info("########### Loading from "+self.getTestname()+".xml ###########")
        logging.info("Write Sat rounds: ")
        logging.info(self.__rounds)
        logging.info("Round matrices: ")
        logging.info(self.__roundMatrices)

class HddIopsTest(DeviceTest):
    '''
    Representing an IOPS test for a hdd based device.
    '''
    def testRound(self):
        #TODO
        return True
    def runRounds(self):
        #TODO
        return True
    def run(self):
        #TODO
        return True
