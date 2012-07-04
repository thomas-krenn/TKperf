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
        ''' 
        Workload independent preconditioning for SSDs
        
        Write two times the device with streaming I/O
        '''
        job = FioJob()
        job.addArg("filename",self.getFilename())
        job.addArg("bs","128k")
        job.addArg("rw","write")
        job.addArg("direct","1")
        for i in range(2):
            print "#Starting preconditioning round "+str(i)
            job.addArg("name", self.getTestname() + '-run' + str(i))
            job.start()
        print "#Finished workload independent preconditioning"
        
        