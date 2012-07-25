'''
Created on 04.07.2012

@author: gschoenb
'''
from __future__ import division
from perfTest.DeviceTest import DeviceTest
from fio.FioJob import FioJob
import plots.genPlots as pgp

import numpy as np
from collections import deque
import logging

class SsdTest(DeviceTest):
    '''
    A fio performance test for a solid state drive.
    '''

    ## Number of rounds to carry out workload independent preconditioning.
    wlIndPrecRnds = 2
    
    ## Max number of test rounds for the IOPS test.
    IOPSTestRnds = 25
    
    ## Always use a sliding window of 4 to measure performance values.
    testMesWindow = 4
    
    ##Labels of block sizes for IOPS test
    bsLabels = ["1024k","128k","64k","32k","16k","8k","4k","512"]#FIXME: [1024,128,64,32,16,8,4,0.5]
    
    ##Percentages of mixed workloads for IOPS test.
    mixWlds = [100,95,65,50,35,5,0]#FIXME: [100,95,65,50,35,5,0] #Start with 100% reads

    ##Percentages of mixed workloads for latency test.
    latMixWlds = [100,65,0]

    ##Labels of block sizes for latency test.
    latBsLabels = ["8k","4k","512"]#FIXMW: ["8k","4k","512"]
    
    ##Labels of block sizes for throughput test
    tpBsLabels = ["1024k","64k","8k","4k","512",]
    
    ##RW modes for io depth test
    iodRW = ["read","write","randread","randwrite"]
    
    ##Labels of block sizes for io depth test
    iodBsLabels = ["1024k","64k","4k","512"]
    
    ##Io depths for libaio
    iodDepths = [1,4,16,64]
    
    def __init__(self,testname,filename):
        '''
        Constructor
        '''
        super(SsdTest,self).__init__(testname,filename)
        
        ## A list of matrices with the collected fio measurement values of each round.
        self.__roundMatrices = []
        
        ## Number of rounds until steady state has been reached
        self.__rounds = 0
        
        ## Number of round where steady state has been reached.
        self.__stdyRnds = []
        
        ## Corresponding 4k random write IOPS for steady state.
        self.__stdyValues = []
        
        ##Average of IOPS in measurement window.
        self.__stdyAvg = 0
        
        ##Slope of steady regression line.
        self.__stdySlope = []
        
        ##Number of rounds until write saturation test ended
        self.__writeSatRnds = 0
        
        ##Write saturation results: [iops_l,lats_l]
        self.__writeSatMatrix = []
        
        ## A list of matrices with the throughput data.
        self.__tpRoundMatrices = []
        
        ## IO depth test matrix results
        self.__iodMatrices = []
        
        self.__iodRnds = 0
    
    def getRndMatrices(self):
        return self.__roundMatrices
    def getRnds(self):
        return self.__rounds
    def getStdyRnds(self):
        return self.__stdyRnds
    def getStdyValues(self):
        return self.__stdyValues
    def getStdyAvg(self):
        return self.__stdyAvg
    def getStdySlope(self):
        return self.__stdySlope
    def getWriteSatRnds(self):
        return self.__writeSatRnds
    def getWriteSatMatrix(self):
        return self.__writeSatMatrix
    def getTPRndMatrices(self):
        return self.__tpRoundMatrices
    
    def resetTestData(self):
        self.__roundMatrices = []
        self.__rounds = 0
        self.__stdyRnds = []
        self.__stdyValues = []
        self.__stdyAvg = 0
        self.__stdySlope = []
        self.__writeSatRnds = 0
        self.__writeSatMatrix = []
        self.__tpRoundMatrices = []
        self.__iodMatrices = []
        self.__iodRnds = 0
    
    def printMatrix(self,mode):
        
        if mode == "LAT":
            for rnd in self.__roundMatrices:
                for wl in rnd:
                    for bs in wl:
                        print bs
                    print "---wl---"
                print "---#rnd---"
    
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
            logging.info("# Starting preconditioning round "+str(i))
            job.addKVArg("name", self.getTestname() + '-run' + str(i))
            job.start()
        logging.info("# Finished workload independent preconditioning")

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
        #allow max excursion of 20% of average
        avgRange = avg * 0.20
        if (maxY - minY) > avgRange:
            return [False,0,0,0]
        
        #do linear regression to calculate slope of linear best fit
        y = np.array(ys)
        x = np.array(xs)
        A = np.vstack([x, np.ones(len(x))]).T
        #calculate k*x+d
        k, d = np.linalg.lstsq(A, y)[0]
        
        #as we have a measurement window of 4, we calculate
        #the slope excursion in  the window
        slopeExc = k * self.testMesWindow
        if slopeExc < 0:
            slopeExc *= -1
        maxSlopeExc = avg * 0.10 #allowed are 10% of avg
        if slopeExc > maxSlopeExc:
            return [False,0,0,0]
        
        return [True,avg,k,d]
    
    def testLoop(self,mode):
        '''
        Carry out one test round of a test.
        The round consists of two inner loops: one iterating over the
        percentage of random reads/writes in the mixed workload, the other
        over different block sizes. In every fio call the sum of the
        corresponding mode unit is calculated and written to an output matrix.
        @param mode String "IOPS" or "LAT" to choose a test mode.
        @return A matrix containing the values of the corresponding mode
        '''
        job = FioJob()
        job.addKVArg("filename",self.getFilename())
        job.addKVArg("name",self.getTestname())
        job.addKVArg("rw","randrw")
        job.addKVArg("direct","1")
        job.addKVArg("runtime","60")#FIXME Change to 60 seconds
        job.addSglArg("time_based")
        job.addKVArg("minimal","1")
        job.addSglArg("group_reporting")     
        
        #iterate over mixed rand read and write and vary block size
        #save the output of fio for parsing and retreiving IOPS/Latencies
        jobOut = ''
        
        if mode == "IOPS":
            wlds = SsdTest.mixWlds
            bsLabels = SsdTest.bsLabels
        if mode == "LAT":
            wlds = SsdTest.latMixWlds
            bsLabels = SsdTest.latBsLabels
        
        rndMatrix = []        
        for i in wlds:
            rwRow = []
            for j in bsLabels:
                job.addKVArg("rwmixread",str(i))
                job.addKVArg("bs",j)
                call,jobOut = job.start()
                if call == False:
                    exit(1)
                logging.info("mixLoad: " +str(i))
                logging.info("bs: "+j)
                logging.info(jobOut)
                logging.info("######")
                if mode == "IOPS":
                    rwRow.append(job.getIOPS(jobOut))
                if mode == "LAT":
                    if i == 65:
                        #if we have a mixed workload weight the latencies
                        l = [0,0,0]
                        r = job.getReadLats(jobOut)
                        w = job.getWriteLats(jobOut)
                        l[0] = (0.65 * r[0]) + (0.35 * w[0])
                        l[1] = (0.65 * r[1]) + (0.35 * w[1])
                        l[2] = (0.65 * r[2]) + (0.35 * w[2])
                    else:
                        l = job.getTotLats(jobOut)
                    rwRow.append(l)
            rndMatrix.append(rwRow)
        return rndMatrix
    
    def runLoops(self,mode):
        '''
        Carry out the IOPS or Latencies test rounds and check if the steady state is reached.
        For a maximum of 25 rounds the test loop is carried out. After each
        test round we check for a measurement window of the last 5 rounds if
        the steady state has been reached. The steady state dependent variables of the measurement
        window as well as their corresponding round numbers are saved as class attributes
        for further usage. If the steady state is reached before 25 rounds we stop the test
        and return.
        @param mode String "IOPS" or "LAT" to choose a test mode.
        @return True if the steady state has been reached, False if not.
        '''
        rndMatrix = []
        steadyValues = deque([])#List of 4k random writes IOPS
        xranges = deque([])#Rounds of current measurement window
        
        #FIXME Purge the device here
        self.wlIndPrec()#FIXME Remove the comment
        
        for i in range(self.IOPSTestRnds):
            logging.info("#################")
            logging.info("Round nr. "+str(i))
            if mode == "IOPS":
                rndMatrix = self.testLoop("IOPS")
            if mode == "LAT":
                rndMatrix = self.testLoop("LAT")
            self.__roundMatrices.append(rndMatrix)
            # Use the last row and its next to last value -> 0/100% r/w and 4k for steady state detection
            if mode == "IOPS":
                steadyValues.append(rndMatrix[-1][-2])
            if mode == "LAT":
                #Latencies always consist of [min,max,mean] latency
                #Take mean/average for steady state detection
                steadyValues.append(rndMatrix[-1][-2][2])
            xranges.append(i)
            #remove the first value and append the next ones
            if i > 4:
                xranges.popleft()
                steadyValues.popleft()
            #check if the steady state has been reached in the last 5 rounds
            if i >= 4:
                steadyState,avg,k,d = self.checkSteadyState(xranges,steadyValues)
                if steadyState == True:
                    self.__rounds = i
                    self.__stdyRnds = xranges
                    self.__stdyValues = steadyValues
                    self.__stdyAvg = avg
                    self.__stdySlope.extend([k,d])
                    return True
        #TODO How to handle the case if the steady state has not been reached
        return False
        
    def runIOPSTest(self):
        '''
        Print various informations about the IOPS test (steady state informations etc.).
        Moreover call the functions to plot the results.
        @return True if steady state was reached and plots were generated, False if not.
        '''
      
        #ensure to start at initialization state
        self.resetTestData()
        logging.info("########### Starting IOPS Test ###########")
        steadyState = self.runLoops("IOPS")
        if steadyState == False:
            logging.warn("Not reached Steady State")
            return False
        else:
            logging.info("Round IOPS results: ")
            logging.info(self.__roundMatrices)
            logging.info("Rounds of steady state:")
            logging.info(self.__stdyRnds)
            logging.info("Steady values:")
            logging.info(self.__stdyValues)
            logging.info("K and d of steady best fit slope:")
            logging.info(self.__stdySlope)
            logging.info("Steady average:")
            logging.info(self.__stdyAvg)
            logging.info("Stopped after round number:")
            logging.info(self.__rounds)
            #call plotting functions
            pgp.stdyStVerPlt(self,"IOPS")
            pgp.stdyStConvPlt(self,"IOPS")
            pgp.mes2DPlt(self,"IOPS")
            return True

    def runLatsTest(self):
        '''
        Print various informations about the Latencies test (steady state informations etc.).
        Moreover call the functions to plot the results.
        @return True if steady state was reached and plots were generated, False if not.
        '''
        #ensure to start at initialization state
        self.resetTestData()
        logging.info("########### Starting Latency Test ###########")
        steadyState = self.runLoops("LAT")
        if steadyState == False:
            logging.warn("Not reached Steady State")
            return False
        else:
            logging.info("Round LATs results: ")
            logging.info(self.__roundMatrices)
            logging.info("Rounds of steady state:")
            logging.info(self.__stdyRnds)
            logging.info("Steady values:")
            logging.info(self.__stdyValues)
            logging.info("K and d of steady best fit slope:")
            logging.info(self.__stdySlope)
            logging.info("Steady average:")
            logging.info(self.__stdyAvg)
            logging.info("Stopped after round number:")
            logging.info(self.__rounds)

            #call plotting functions
            pgp.stdyStVerPlt(self,"LAT")
            pgp.stdyStConvPlt(self,"LAT")
            pgp.mes2DPlt(self,"avg-LAT")
            pgp.mes2DPlt(self,"max-LAT")
            return True
    
    def writeSatTestRnd(self):
        '''
        Carry out one test round of the write saturation test.
        The round consists of random writing with 4k bs for one minute
        @return [TotWriteIO,IOPS,[min,max,mean lats]]
        '''
        job = FioJob()
        job.addKVArg("filename",self.getFilename())
        job.addKVArg("name",self.getTestname())
        job.addKVArg("rw","randwrite")
        job.addKVArg("bs","4k")
        job.addKVArg("direct","1")
        job.addKVArg("runtime","60")#FIXME Change to 60 seconds
        job.addSglArg("time_based")
        job.addKVArg("minimal","1")
        job.addSglArg("group_reporting")     
        
        (call,jobOut) = job.start()
        if call == False:
            exit(1)
        
        writeIO = job.getTotIOWrite(jobOut)
        iops = job.getIOPS(jobOut)
        lats = job.getWriteLats(jobOut)
        
        logging.info(jobOut)
        logging.info("#IOPS: " + str(iops))
        logging.info("#Tot Write IO: " + str(writeIO))
        logging.info("#Latencies: " + str(lats))
        logging.info("######")
        return [writeIO,iops,lats]
        
    def writeSatTest(self):
        #FIXME Add purging the device here
        (call,devSzKB) = self.getDevSizeKB()
        if call == False:
            logging.error("#Could not get size of device.")
            exit(1)
        totWriteIO = 0 #total written IO in KB, must be greater than 4xDevice 
        #carry out the test for a maximum of 24h, one round runs for 1 minute
        maxRounds = 60*24
        
        writeIO = 0
        iops_l = [] #overall list of iops
        iops = 0 #IOPS per round
        lats_l = []#overall list of latencies
        lats = []#latencies per round
        
        self.__writeSatRnds = maxRounds
        #assume all rounds must be carried out            
        for i in range(maxRounds):
            writeIO,iops,lats = self.writeSatTestRnd()
            iops_l.append(iops)
            lats_l.append(lats)
            totWriteIO += writeIO
            
            #Check if 4 times the device size has been reached
            if totWriteIO >= (devSzKB * 4):#FIXME: Change to *4
                self.__writeSatRnds = i
                break
        self.__writeSatMatrix.append(iops_l)
        self.__writeSatMatrix.append(lats_l)
        
        logging.info("#Write saturation has written " + str(totWriteIO) + "KB")
        
    def runWriteSatTest(self):
        #ensure to start at initialization state
        self.resetTestData()
        logging.info("########### Starting Write Saturation Test ###########")
        self.writeSatTest()
        logging.info("Write Sat rounds: ")
        logging.info(self.__writeSatRnds)
        logging.info("Round Write Saturation results: ")
        logging.info(self.__writeSatMatrix)
        pgp.writeSatIOPSPlt(self)
        pgp.writeSatLatPlt(self)
        
    def tpTestRnd(self,bs):
        '''
        Carry out one test round of the throughput test.
        The round consists of two loops: the first carries out
        read throughput test iterating over the different block sizes.
        The second one carries out write throughput tests over all block sizes.
        of reads and writes is calculated and written to an output matrix.
        @param bs The current block size to use.
        @return Read and Write bandwidths [tpRead,tpWrite]
        '''
        job = FioJob()
        job.addKVArg("filename",self.getFilename())
        job.addKVArg("name",self.getTestname())
        job.addKVArg("direct","1")
        job.addKVArg("runtime","10")#FIXME Change to 60 seconds
        job.addSglArg("time_based")
        job.addKVArg("minimal","1")
        job.addSglArg("group_reporting")  
        job.addKVArg("bs",bs)   
      
        jobOut = ''
        tpRead = 0 #read bandwidth
        tpWrite = 0#write bandwidth

        #start read tests
        job.addKVArg("rw","read")
        call,jobOut = job.start()
        if call == False:
            exit(1)
        logging.info("Read TP test:")
        logging.info(jobOut)
        logging.info("######")
        tpRead = job.getTPRead(jobOut)
    
        #start write tests
        job.addKVArg("rw","write")
        call,jobOut = job.start()
        if call == False:
            exit(1)
        logging.info("Write TP test:")
        logging.info(jobOut)
        logging.info("######")
        tpWrite = job.getTPWrite(jobOut)
            
        return [tpRead,tpWrite]
        
    def tpTest(self):
        '''
        Carry out the throughput/bandwidth test rounds and check if the steady state is reached.
         @return True if the steady state has been reached, False if not.
        '''
        stdyValsWrite = deque([])#List of 1M sequential write IOPS
        xrangesWrite = deque([])#Rounds of current measurement window
        
        #rounds are the same for IOPS and throughput
        for j in SsdTest.tpBsLabels:
            #FIXME Add purging the device here
            tpRead_l = []
            tpWrite_l = []
            logging.info("#################")
            logging.info("Current block size. "+str(j))
            
            for i in range(self.IOPSTestRnds):
                logging.info("######")
                logging.info("Round nr. "+str(i))
                tpRead,tpWrite = self.tpTestRnd(j)
                tpRead_l.append(tpRead)
                tpWrite_l.append(tpWrite)
                
                #if the rounds have been set by steady state for 1M block size
                #we need to carry out only i rounds for the other block sizes
                #as steady state has already been reached
                if self.__rounds != 0 and self.__rounds == i:
                    self.__tpRoundMatrices.append([tpRead_l,tpWrite_l])
                    break
                
                # Use 1M block sizes sequential write for steady state detection
                if j == "1024k":
                    stdyValsWrite.append(tpWrite)
                    xrangesWrite.append(i)
                    #remove the first value and append the next ones, this
                    #is out measurement window
                    if i > 4:
                        xrangesWrite.popleft()
                        stdyValsWrite.popleft()
                        #check if the steady state has been reached in the last 5 rounds
                    if i >= 4:
                        steadyState,avg,k,d = self.checkSteadyState(xrangesWrite,stdyValsWrite)
                        if steadyState == True:
                            #TODO Currently the parameters from the previous tests are overwritten
                            #TODO Save the parameters in a suited format (e.g. XML) to have them for reporting
                            self.__rounds = i
                            self.__stdyRnds = xrangesWrite
                            self.__stdyValues = stdyValsWrite
                            self.__stdyAvg = avg
                            self.__stdySlope.extend([k,d])
                            logging.info("Reached steady state at round %d",i)
                            #as we have reached the steady state we can use the results from the rounds
                            self.__tpRoundMatrices.append([tpRead_l,tpWrite_l])
                            break
            #Here we have not reached the steady state after 25 rounds
            #FIXME How to handle the case if steady state is not reached
            if steadyState == False:
                logging.warn("#Did not reach steady state for bs %s",j)
            
        if steadyState == False:
            return False
        if steadyState == True:
            return True
        
    def runTpTest(self):
        '''
        Print various informations about the Throughput test (steady state informations etc.).
        Moreover call the functions to plot the results.
        @return True if steady state was reached and plots were generated, False if not.
        '''
        #ensure to start at initialization state
        self.resetTestData()
        logging.info("########### Starting Throughput Test ###########")
        steadyState = self.tpTest()
        if steadyState == False:
            logging.warn("Not reached Steady State")
            return False
        else:
            logging.info("Round TP results: ")
            logging.info(self.__tpRoundMatrices)
            logging.info("Rounds of steady state:")
            logging.info(self.__stdyRnds)
            logging.info("Steady values:")
            logging.info(self.__stdyValues)
            logging.info("K and d of steady best fit slope:")
            logging.info(self.__stdySlope)
            logging.info("Steady average:")
            logging.info(self.__stdyAvg)
            logging.info("Stopped after round number:")
            logging.info(self.__rounds)
            #call plotting functions
            pgp.stdyStVerPlt(self,"TP")
            pgp.tpStdyStConvPlt(self, "read","ssd")
            pgp.tpStdyStConvPlt(self, "write","ssd")
    

        return True

    def ioDepthTestRnd(self):
        '''
        Carry out one test round of the io depth test.
        The round consists of read, writing, rand read, rand write
        with different block sizes and io depths (libaio).
        @return [writeIO,roundMatrix] Total written IO in KB while write test
        and a Matrix of rw,bs,iodepth
        '''
        job = FioJob()
        job.addKVArg("filename",self.getFilename())
        job.addKVArg("name",self.getTestname())
        job.addKVArg("direct","1")
        job.addKVArg("runtime","20")#FIXME Change to 60 seconds or remove
        job.addKVArg("minimal","1")
        job.addSglArg("group_reporting")     
        job.addKVArg("ioengine","libaio")
        
        #start the fio job rounds with the given static
        #parameters
        writeIO = 0
        roundMatrix = []
        for rw in self.iodRW:
            rwRow = []
            for bs in self.iodBsLabels:
                bsRow = []
                for iod in self.iodDepths:
                    job.addKVArg("rw",rw)
                    job.addKVArg("bs",bs)
                    job.addKVArg("iodepth",str(iod))
                    
                    (call,jobOut) = job.start()
                    if call == False:
                        exit(1)
                    logging.info("rw: " +rw)
                    logging.info("bs: "+bs)
                    logging.info("iodepth: "+str(iod))
                    logging.info(jobOut)
                    logging.info("######")
                    if rw == "read":
                        bsRow.append(job.getTPRead(jobOut))
                    if rw == "write":
                        bsRow.append(job.getTPWrite(jobOut))
                        #we keep the written IO to know if we should stop
                        #FIXME Currently it is summed up for all block sizes
                        writeIO += job.getTotIOWrite(jobOut)
                    if rw == "randread":
                        bsRow.append(job.getIOPSRead(jobOut))
                    if rw == "randwrite":
                        bsRow.append(job.getIOPSWrite(jobOut))
                rwRow.append(bsRow)
            roundMatrix.append(rwRow)
        logging.info("#Tot Write IO: " + str(writeIO))
        return [writeIO,roundMatrix]
        
    def ioDepthTest(self):
        #FIXME Add purging the device here
        (call,devSzKB) = self.getDevSizeKB()
        if call == False:
            logging.error("#Could not get size of device.")
            exit(1)
        totWriteIO = 0 #total written IO in KB, must be greater than 4xDevice 
        #carry out the test for a maximum of 24h, one round runs for 1 minute
        maxRounds = 60*24
        
        self.__iodRnds = maxRounds
        roundMatrix = []
        #assume all rounds must be carried out            
        for i in range(maxRounds):
            logging.info("######")
            logging.info("Round nr. "+str(i))
            writeIO,roundMatrix = self.ioDepthTestRnd()
            self.__iodMatrices.append(roundMatrix)
            totWriteIO += writeIO
            
            #Check if 4 times the device size has been reached
            if totWriteIO >= (devSzKB / 5):#FIXME: Change to *4
                self.__iodRnds = i
                break
        
        logging.info("#IO depth test has written " + str(totWriteIO) + "KB")

    def runIoDepthTest(self):
        #ensure to start at initialization state
        self.resetTestData()
        logging.info("########### Starting IO Depth Test ###########")
        self.ioDepthTest()
        logging.info("IO Depth rounds: ")
        logging.info(self.__iodRnds)
        logging.info("Round IO Depth results: ")
        logging.info(self.__iodMatrices)
    
    
    
        