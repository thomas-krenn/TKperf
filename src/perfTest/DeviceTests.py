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
        @param testname Name of the test, specifies the output file.
        @param device The tested device, a device object.
        '''
        ## The output file for the fio job test results.
        self.__testname = testname
        
        ## The tested device, a Device object
        self.__device = device