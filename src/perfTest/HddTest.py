'''
Created on 04.07.2012

@author: gschoenb
'''
from perfTest.DeviceTest import DeviceTest

class HddTest(DeviceTest):
    '''
    A fio performance test for a hard disk.
    '''
    
    def __init__(self,testname,filename):
        '''
        Constructor
        '''
        super(HddTest,self).__init__(testname,filename)
        
        