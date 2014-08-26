'''
Created on Aug 25, 2014

@author: gschoenb
'''

from abc import ABCMeta, abstractmethod
import logging
from collections import deque

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
        except RuntimeError:
            logging.error("# Could not carry out preconditioning for "+self.getDevice().getDevPath())
        logging.info("########### Starting IOPS Test ###########")
        steadyState = self.runRounds()
        if steadyState == False:
            logging.info("# Steady State has not been reached for IOPS Test.")
        self.toLog()
        return True

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
