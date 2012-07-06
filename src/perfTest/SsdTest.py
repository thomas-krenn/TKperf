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
    
    ## Number of rounds to carry out workload independent preconditioning.
    wlIndPrecRnds = 2
    
    ## Max number of test rounds for the IOPS test.
    IOPSTestRnds = 25
    
    ## Alwasys use a slinding window of 4 to measure performance values.
    testMesWindow = 4
    
    def __init__(self,testname,filename):
        '''
        Constructor
        '''
        super(SsdTest,self).__init__(testname,filename)
        
        ## A list of matrices with the collected fio measurement values of each round.
        self.__roundMatrices = []
        
    def wlIndPrec(self):
        ''' 
        Workload independent preconditioning for SSDs.
        
        Write two times the device with streaming I/O.
        '''
        job = FioJob()
        job.addKVArg("filename",self.getFilename())
        job.addKVArg("bs","128k")
        job.addKVArg("rw","write")
        job.addKVArg("direct","1")
        for i in range(SsdTest.wlIndPrecRnds):
            print "#Starting preconditioning round "+str(i)
            job.addKVArg("name", self.getTestname() + '-run' + str(i))
            job.start()
        print "#Finished workload independent preconditioning"
    
    def IOPSTestRnd(self):
        '''
        Carry out one test round of the IOPS test.
        
        The round consists of two inner loops: one iterating over the
        percentage of random reads/writes in the mixed workload, the other
        over different block sizes. In every fio call the sum of average IOPS
        of reads and writes is calculated and written to an output matrix.
        @return An output matrix 7*8 values - the sum of avg. IOPS in each
        round of the inner loops.
        '''
        rwmixreads = [100,95]#,65,50,35,5,0] #Start with 100% reads
        bs = [4,0.5]#[1024,128,64,32,16,8,4,0.5] #List of block sizes
        
        job = FioJob()
        job.addKVArg("filename",self.getFilename())
        job.addKVArg("name",self.getTestname())
        job.addKVArg("rw","randrw")
        job.addKVArg("direct","1")
        job.addKVArg("runtime","60")
        job.addSglArg("time_based")
        job.addKVArg("minimal","1")
        job.addSglArg("group_reporting")     
        
        #iterate over mixed rand read and write and vary block size
        #save the output of fio for parsing and retreiving IOPS
        jobOut = ''
        
        rndMatrix = []        
        for i in rwmixreads:
            rwRow = []
            for j in bs:
                job.addKVArg("rwmixread",str(i))
                job.addKVArg("bs",str(j)+'k')
                jobOut = job.start()
                print jobOut
                print "#####################################"
                rwRow.append(job.getIOPS(jobOut))
            rndMatrix.append(rwRow)
        return rndMatrix
    
    def IOPSTest(self):
        rndMatrix = []
                
        
        
        
        
        
    
    
    
    
    
        