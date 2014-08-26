'''
Created on Aug 25, 2014

@author: gschoenb
'''

from abc import ABCMeta, abstractmethod
import logging
from perfTest.Devices import Device

class DeviceTest(object):
    '''
    Representing a performance test, run on a device.
    '''
    __metaclass__ = ABCMeta

    def __init__(self,testname,device):
        '''
        Constructor
        @param testname Name of the test, specifies the output file
        @param device The tested device, a device object
        '''
        ## The name of the test, is used to give the resulting files a name
        self.__testname = testname
        ## The tested device, a Device object
        self.__device = device

    @abstractmethod
    def testRound(self):
        ''' A test round for a specific device performance test. '''
    @abstractmethod
    def runRounds(self):
        ''' Run the specific test rounds. '''
    @abstractmethod
    def run(self):
        ''' Run the type specific performance test. '''

class IopsTest(DeviceTest):
    '''
    Representing an IOPS test for a device.
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
