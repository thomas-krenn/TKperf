'''
Created on 04.07.2012

@author: gschoenb
'''
from perfTest.DeviceTest import DeviceTest
from fio.FioJob import FioJob

class SsdTest(DeviceTest):
    '''
    A fio performance test for a solid state drive.
    '''


    def __init__(self,testname,filename):
        '''
        Constructor
        '''
        super(SsdTest,self).__init__(testname,filename)
        
    def wlIndPrec(self):
        job = FioJob()
        job.addArg("filename",self.getFilename())#TODO: how to specify the device parameter?
        job.addArg("rw","write")
        job.addArg("direct","1")
        for i in range(1):
            job.addArg("name", self.getTestname() + '-run' + str(i))
            job.start()
        