'''
Created on 04.07.2012

@author: gschoenb
'''
from perfTest.DeviceTest import DeviceTest
from fio.FioJob import FioJob

import numpy as np
from collections import deque

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
        rwmixreads = [5,0]#[100,95,65,50,35,5,0] #Start with 100% reads
        bs = [8,4]#[1024,128,64,32,16,8,4,0.5] #List of block sizes
        #FIXME This is a problem as fio can't handle bs of 0.5k
        
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
                print jobOut #TODO what to do with the fio output
                print "#####################################"
                rwRow.append(job.getIOPS(jobOut))
            rndMatrix.append(rwRow)
        return rndMatrix
    
    def checkSteadyState(self,xs,ys):
        '''
        Checks if the steady is reached for the given values.
        The steady state is defined by the allowed data excursion from the average (+-10%), and
        the allowed slope excursion of the linear regression best fit line (+-5%).
        @return [True,avg,k,d] (k*x+d is slope line) if steady state is reached, [False,0,0,0] if not
        '''
        maxY = max(ys)
        minY = min(ys)
        avg = sum(ys)/len(ys)#calc average of values
        avgLowLim = avg * 0.9
        avgUppLim = avg * 1.10#calc limits where avg must be in
        #given min and max are out of allowed range
        if minY < avgLowLim and maxY > avgUppLim:
            return [False,0,0,0]
        
        #do linear regression to calculate slope of linear best fit
        y = np.array(ys)
        x = np.array(xs)
        A = np.vstack([x, np.ones(len(x))]).T
        #calculate k*x+d
        k, d = np.linalg.lstsq(A, y)[0]
        
        #as we have a measurement window of 4, we double the slope 
        #to get the maximum slope excursion
        slopeExc = k * (self.testMesWindow / 2)
        if slopeExc < 0:
            slopeExc *= -1
        maxSlopeExc = avg * 0.10 #allowed are 10% of avg
        if slopeExc > maxSlopeExc:
            return [False,0,0,0]
        
        return [True,avg,k,d]
          
    def IOPSTest(self):
        rndMatrix = []
        steadyValues = deque([])#List of 4k random writes IOPS
        xranges = deque([])#rounds of current measurement window
        
        for i in range(self.IOPSTestRnds):
            rndMatrix = self.IOPSTestRnd()
            self.__roundMatrices.append(rndMatrix)
            # Use the last row and its last value -> 0/100% r/w and 4k for steady state detection
            steadyValues.append(rndMatrix[-1][-1])
            xranges.append(i)
            #remove the first value and append the next ones
            if i > 4:
                xranges.popleft()
                steadyValues.popleft()
            if i >= 4:
                steadyState,avg,k,d = self.checkSteadyState(xranges,steadyValues)
                if steadyState == True:
                    return [True,xranges,avg,k,d]
        return [False,0,0,0]
        
    def IOPSTestReport(self):
        
        steadyState,rounds,avg,k,d = self.IOPSTest()
        if steadyState == False:
            print "Not reached Steady State"
        else:
            print self.__roundMatrices
        
#       
#        if steadyState == True:
#            import matplotlib.pyplot as plt
#            x = np.array(rounds)
#            av = []
#            av.append(avg)
#            av = av * len(x)
#            print av
#            plt.plot(x,
#                     [self.__roundMatrices[0][-1][-1],
#                      self.__roundMatrices[1][-1][-1],
#                      self.__roundMatrices[2][-1][-1],
#                      self.__roundMatrices[3][-1][-1],
#                      self.__roundMatrices[4][-1][-1]],
#                     'o', label='Original data', markersize=10)
#            plt.plot(x, k*x + d, 'r', label='Fitted line')
#            plt.plot(x, av, 'g', label='Average')
#            plt.legend()
#            plt.show()
        
            
        
        
        
        
        
        
        
        
    
    
    
    
    
        