'''
Created on Aug 25, 2014

@author: gschoenb
'''

from abc import ABCMeta, abstractmethod
import logging
from perfTest.Devices import Device
from perfTest.Options import Options
from fio import FioJob

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
        self.__fioJob.addKVArg("filename",self.__device.getDevName())
        self.__fioJob.addKVArg("name",self.__testname)
        self.__fioJob.addKVArg("direct","1")
        self.__fioJob.addKVArg("minimal","1")
        self.__fioJob.addKVArg("ioengine","libaio")
        self.__fioJob.addKVArg("numjobs",str(self.__numJobs))
        self.__fioJob.addKVArg("iodepth",str(self.__ioDepth))
        self.__fioJob.addSglArg("group_reporting")
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
        self.getFioJob().addKVArg("rw","randrw")
        self.getFioJob().addKVArg("runtime","60")
        self.getFioJob().addSglArg("time_based")

    def testRound(self):
        #TODO
        return True
    def runRounds(self):
        #TODO
        return True
    def run(self):
        #TODO
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
