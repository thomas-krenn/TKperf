'''
Created on 04.07.2012

@author: gschoenb
'''
from __future__ import division
from perfTest.DeviceTest import DeviceTest
from fio.FioJob import FioJob

import numpy as np
from collections import deque
import logging
import json
from lxml import etree

class SsdTest(DeviceTest):
    '''
    A fio performance test for a solid state drive.
    '''

    ## Number of rounds to carry out workload independent preconditioning.
    wlIndPrecRnds = 2
    
    def __init__(self,testname,filename,nj,iod):
        '''
        Constructor
        @param nj Number of jobs for Fio.
        @param iod IO depth for libaio used by Fio. 
        '''
        super(SsdTest,self).__init__(testname,filename)
        
        ##Number of jobs started by fio
        self.__numJobs = nj
        
        ##IO depth for libaio used by fio
        self.__ioDepth = iod
        
        ##The fio job for the current SSD test
        self.__fioJob = FioJob()
        self.__fioJob.addKVArg("filename",self.getFilename())
        self.__fioJob.addKVArg("name",self.getTestname())
        self.__fioJob.addKVArg("direct","1")
        self.__fioJob.addKVArg("minimal","1")
        self.__fioJob.addKVArg("ioengine","libaio")
        self.__fioJob.addKVArg("numjobs",str(self.__numJobs))
        self.__fioJob.addKVArg("iodepth",str(self.__ioDepth))
        self.__fioJob.addSglArg("group_reporting")   

    def getFioJob(self):
        return self.__fioJob
    
    def getNj(self):
        return self.__numJobs
    
    def getIod(self):
        return self.__ioDepth
    
    def setNj(self,nj):
        self.__numJobs = nj
        
    def setIod(self,iod):
        self.__ioDepth = iod
    
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
        job.addKVArg("minimal","1")
        job.addKVArg("numjobs",str(self.__numJobs))
        job.addKVArg("ioengine","libaio")
        job.addKVArg("iodepth",str(self.__ioDepth))
        job.addSglArg("group_reporting")
        
        for i in range(SsdTest.wlIndPrecRnds):
            logging.info("# Starting preconditioning round "+str(i))
            job.addKVArg("name", self.getTestname() + '-run' + str(i))
            call,out = job.start()
            if call == False:
                logging.error("# Could not carry out workload independent preconditioning")
                return False
            else:
                logging.info(out)
        logging.info("# Finished workload independent preconditioning")
        return True

class StdyTest(SsdTest):
    '''
    Tests that work with a steady state.
    '''
    ## Max number of carried out test rounds.
    testRnds = 25
    
    ## Always use a sliding window of 4 to measure performance values.
    testMesWindow = 4
    
    def __init__(self):
        
        self.getFioJob().addKVArg("runtime","2")#FIXME
        self.getFioJob().addSglArg("time_based")
        
        ## A list of matrices with the collected fio measurement values of each round.
        self.__roundMatrices = []
        
        ## Number of rounds until steady state has been reached
        self.__rounds = 0
        
        ## Number of round where steady state has been reached.
        self.__stdyRnds = []
        
        ## Dependent variable to detect steady state.
        self.__stdyValues = []
        
        ##Measured average in measurement window
        self.__stdyAvg = 0
        
        ##Slope of steady regression line.
        self.__stdySlope = []
        
        ##States if the steady state has been reached or not
        self.__reachStdyState = None
        
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
    def getReachStdyState(self):
        return self.__reachStdyState
    
    def setRnds(self,r):
        self.__rounds = r
    def setStdyRnds(self,r):
        self.__stdyRnds = r
    def setStdyValues(self,v):
        self.__stdyValues = v
    def setStdyAvg(self,a):
        self.__stdyAvg = a
    def setStdySlope(self,s):
        self.__stdySlope = s
    def setReachStdyState(self,s):
        self.__reachStdyState = s
    
    def checkSteadyState(self,xs,ys):
        '''
        Checks if the steady is reached for the given values.
        The steady state is defined by the allowed data excursion from the average (+-10%), and
        the allowed slope excursion of the linear regression best fit line (+-5%).
        @return [True,avg,k,d] (k*x+d is slope line) if steady state is reached, [False,avg,k,d] if not
        '''
        stdyState = True
        maxY = max(ys)
        minY = min(ys)
        avg = sum(ys)/len(ys)#calc average of values
        #allow max excursion of 20% of average
        avgRange = avg * 0.20
        if (maxY - minY) > avgRange:
            stdyState = False
        
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
            stdyState = False
        
        return [stdyState,avg,k,d]

    def logTestData(self):
        '''
        Log information about the steady state and how it 
        has been reached.
        '''
        logging.info("Round matrices: ")
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
        logging.info("Reached steady state:")
        logging.info(self.__reachStdyState)
        
    def toXml(self,root):
        '''
        Dump the information about a steady state test to xml. This is
        useful if changes to reporting functions are made, then the
        report can be generated again from the xml file.
        @param root The xml root tag to append the new elements to
        @return An xml root element containing the information about the test.
        ''' 
        r = etree.Element(root)
        
        data = json.dumps(self.getNj())
        e = etree.SubElement(r,'numjobs')
        e.text = data
        
        data = json.dumps(self.getIod())
        e = etree.SubElement(r,'iodepth')
        e.text = data
        
        data = json.dumps(self.__roundMatrices)
        e = etree.SubElement(r,'roundmat')
        e.text = data
        
        data = json.dumps(list(self.__stdyRnds))
        e = etree.SubElement(r,'stdyrounds')
        e.text = data
        
        data = json.dumps(list(self.__stdyValues))
        e = etree.SubElement(r,'stdyvalues')
        e.text = data
        
        data = json.dumps(self.__stdySlope)
        e = etree.SubElement(r,'stdyslope')
        e.text = data
        
        data = json.dumps(self.__stdyAvg)
        e = etree.SubElement(r,'stdyavg')
        e.text = data
        
        data = json.dumps(self.__reachStdyState)
        e = etree.SubElement(r,'reachStdyState')
        e.text = data
        
        data = json.dumps(self.__rounds)
        e = etree.SubElement(r,'rndnr')
        e.text = data
        
        #TODO Add FioJob to xml file
        return r
        
        
    def fromXml(self,root):
        '''
        Loads the information from the given xml element an initializes
        the object attributes.
        @param root The given element containing the information about
        the object to be initialized.
        ''' 
        self.setNj(json.loads(root.findtext('numjobs')))
        self.setIod(json.loads(root.findtext('iodepth')))
        self.__roundMatrices = json.loads(root.findtext('roundmat'))
        self.__stdyRnds = json.loads(root.findtext('stdyrounds'))
        self.__stdyValues = json.loads(root.findtext('stdyvalues'))
        self.__stdySlope = json.loads(root.findtext('stdyslope'))
        self.__stdyAvg = json.loads(root.findtext('stdyavg'))
        self.__reachStdyState = json.loads(root.findtext('reachStdyState'))
        self.__rounds = json.loads(root.findtext('rndnr'))
        logging.info("########### Loading from "+self.getTestname()+".xml ###########")
        self.logTestData()


class IopsTest(StdyTest):
    '''
    A class to carry out the IOPS test.
    '''
    
    ##Labels of block sizes
    bsLabels = ["1024k","128k","64k","32k","16k","8k","4k","512"]
    
    ##Percentages of mixed workloads
    mixWlds = [100,95,65,50,35,5,0]
    
    def __init__(self,testname,filename,nj,iod):
        '''
        Constructor.
        '''
        SsdTest.__init__(self, testname, filename, nj, iod)
        StdyTest.__init__(self)
        self.getFioJob().addKVArg("rw","randrw")
    
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
        for i in IopsTest.mixWlds:
            rwRow = []
            for j in IopsTest.bsLabels:
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
        
        for i in range(StdyTest.testRnds):
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
                steadyState,avg,k,d = self.checkSteadyState(xranges,steadyValues)
                if steadyState == True:
                    self.setReachStdyState(True)
                    break
        self.setRnds(i)
        self.setStdyRnds(xranges)
        self.setStdyValues(steadyValues)
        self.setStdyAvg(avg)
        self.getStdySlope().extend([k,d])
        #Check if steady state has been reached
        if self.getReachStdyState() != True:
            self.setReachStdyState(False)
        return self.getReachStdyState()

    def run(self):
        '''
        Start the rounds, log the steady state infos and call plot functions.
        @return True if steady state was reached and plots were generated.
        '''
        if self.makeSecureErase() == False:
            logging.error("# Could not carry out secure erase.")
            exit(1) 
        if self.wlIndPrec() == False:
            logging.error("# Could not carry out preconditioning.")
            exit(1)
        logging.info("########### Starting IOPS Test ###########")
        steadyState = self.runRounds()
        if steadyState == False:
            logging.info("# Steady State has not been reached for IOPS Test.")
        self.logTestData()
        return True

class LatencyTest(StdyTest):
    '''
    A class to carry out the Latency test.
    '''
    
    ##Percentages of mixed workloads.
    mixWlds = [100,65,0]

    ##Labels of block sizes.
    bsLabels = ["8k","4k","512"]
    
    def __init__(self,testname,filename,nj,iod):
        '''
        Constructor.
        '''
        
        SsdTest.__init__(self, testname, filename, nj, iod)
        StdyTest.__init__(self)
        self.getFioJob().addKVArg("rw","randrw")
        #For latency the specification says to use 1 job/thread, 1 outstanding IO
        self.getFioJob().addKVArg("numjobs","1")
        self.getFioJob().addKVArg("iodepth","1")
            
    def testRound(self):
        '''
        Carry out one latency test round.
        The round consists of two inner loops: one iterating over the
        percentage of random reads/writes in the mixed workload, the other
        over different block sizes.
        @return A matrix containing [min,max,mean] latencies of the round.
        '''
        jobOut = ''
        rndMatrix = []        
        for i in LatencyTest.mixWlds:
            rwRow = []
            for j in LatencyTest.bsLabels:
                self.getFioJob().addKVArg("rwmixread",str(i))
                self.getFioJob().addKVArg("bs",j)
                call,jobOut = self.getFioJob().start()
                if call == False:
                    exit(1)
                logging.info("mixLoad: " +str(i))
                logging.info("bs: "+j)
                logging.info(jobOut)
                logging.info("######")
                if i == 65:
                    #if we have a mixed workload weight the latencies
                    l = [0,0,0]
                    r = self.getFioJob().getReadLats(jobOut)
                    w = self.getFioJob().getWriteLats(jobOut)
                    #FIXME Is this also correct for Min and Max?
                    l[0] = (0.65 * r[0]) + (0.35 * w[0])
                    l[1] = (0.65 * r[1]) + (0.35 * w[1])
                    l[2] = (0.65 * r[2]) + (0.35 * w[2])
                else:
                    l = self.getFioJob().getTotLats(jobOut)
                rwRow.append(l)
            rndMatrix.append(rwRow)
        return rndMatrix
    
    def runRounds(self):
        '''
        Carry out the latency test rounds and check if the steady state is reached.
        For a maximum of 25 rounds the test loop is carried out. After each
        test round we check for a measurement window of the last 5 rounds if
        the steady state has been reached.
        @return True if the steady state has been reached, False if not.
        '''
        rndMatrix = []
        steadyValues = deque([])
        xranges = deque([])#Rounds of current measurement window
        
        for i in range(StdyTest.testRnds):
            logging.info("#################")
            logging.info("Round nr. "+str(i))
            rndMatrix = self.testRound()
            self.getRndMatrices().append(rndMatrix)
            #Latencies always consist of [min,max,mean] latency
            #Take mean/average for steady state detection
            steadyValues.append(rndMatrix[-1][-2][2])
            xranges.append(i)
            if i > 4:
                xranges.popleft()
                steadyValues.popleft()
            #check if the steady state has been reached in the last 5 rounds
            if i >= 4:
                steadyState,avg,k,d = self.checkSteadyState(xranges,steadyValues)
                if steadyState == True:
                    self.setReachStdyState(True)
                    break
        self.setRnds(i)
        self.setStdyRnds(xranges)
        self.setStdyValues(steadyValues)
        self.setStdyAvg(avg)
        self.getStdySlope().extend([k,d])
        #Check if steady state has been reached
        if self.getReachStdyState() != True:
            self.setReachStdyState(False)
        return self.getReachStdyState()
        
    def run(self):
        '''
        Start the rounds, log the steady state infos and call plot functions.
        @return True if steady state was reached and plots were generated.
        '''
        if self.makeSecureErase() == False:
            logging.error("# Could not carry out secure erase.")
            exit(1) 
        if self.wlIndPrec() == False:
            logging.error("# Could not carry out preconditioning.")
            exit(1)
        logging.info("########### Starting Latency Test ###########")
        steadyState = self.runRounds()
        if steadyState == False:
            logging.info("# Steady State has not been reached for Latency Test.")
        self.logTestData()
        return True

class TPTest(StdyTest):
    '''
    A class to carry out the Throughput test.
    '''
    ##Labels of block sizes for throughput test
    bsLabels = ["1024k","64k","8k","4k","512",]
    
    def __init__(self,testname,filename,nj,iod):
        '''
        Constructor.
        '''
        SsdTest.__init__(self, testname, filename, nj, iod)
        StdyTest.__init__(self)
    
    def testRound(self,bs):
        '''    
        Carry out one test round of the throughput test.
        Read and Write throughput is tested with the given block size
        @param bs The current block size to use.
        @return Read and Write bandwidths [tpRead,tpWrite]
        '''
        self.getFioJob().addKVArg("bs",bs)
        jobOut = ''
        tpRead = 0 #read bandwidth
        tpWrite = 0#write bandwidth

        #start read tests
        self.getFioJob().addKVArg("rw","read")
        call,jobOut = self.getFioJob().start()
        if call == False:
            exit(1)
        logging.info("Read TP test:")
        logging.info(jobOut)
        logging.info("######")
        tpRead = self.getFioJob().getTPRead(jobOut)
    
        #start write tests
        self.getFioJob().addKVArg("rw","write")
        call,jobOut = self.getFioJob().start()
        if call == False:
            exit(1)
        logging.info("Write TP test:")
        logging.info(jobOut)
        logging.info("######")
        tpWrite = self.getFioJob().getTPWrite(jobOut)
            
        return [tpRead,tpWrite]    
    
    def runRounds(self):
        '''
        Carry out the throughput/bandwidth test rounds and check if the steady state is reached.
         @return True if the steady state has been reached, False if not.
        '''
        stdyValsWrite = deque([])#List of 1M sequential write IOPS
        xrangesWrite = deque([])#Rounds of current measurement window
        
        #rounds are the same for IOPS and throughput
        for j in TPTest.bsLabels:
            if self.makeSecureErase() == False:
                logging.error("# Could not carry out secure erase.")
                exit(1)

            tpRead_l = []
            tpWrite_l = []
            logging.info("#################")
            logging.info("Current block size. "+str(j))
            
            for i in range(StdyTest.testRnds):
                logging.info("######")
                logging.info("Round nr. "+str(i))
                tpRead,tpWrite = self.testRound(j)
                tpRead_l.append(tpRead)
                tpWrite_l.append(tpWrite)
                
                #if the rounds have been set by steady state for 1M block size
                #we need to carry out only i rounds for the other block sizes
                #as steady state has already been reached
                if self.getRnds() != 0 and self.getRnds() == i:
                    self.getRndMatrices().append([tpRead_l,tpWrite_l])
                    break
                
                # Use 1M block sizes sequential write for steady state detection
                if j == "1024k":
                    stdyValsWrite.append(tpWrite)
                    xrangesWrite.append(i)
                    if i > 4:
                        xrangesWrite.popleft()
                        stdyValsWrite.popleft()
                        #check if the steady state has been reached in the last 5 rounds
                    if i >= 4:
                        steadyState,avg,k,d = self.checkSteadyState(xrangesWrite,stdyValsWrite)
                        #reached a steady state
                        if steadyState == True:
                            self.setReachStdyState(True)
                            logging.info("Reached steady state at round %d",i)
                        #running from 0 to 24
                        if i == ((StdyTest.testRnds) - 1):
                            self.setReachStdyState(False)
                            logging.warn("#Did not reach steady state for bs %s",j)
                        #In both cases we need the information about the rounds
                        if steadyState == True or i == ((StdyTest.testRnds) - 1):
                            self.setRnds(i)
                            self.setStdyRnds(xrangesWrite)
                            self.setStdyValues(stdyValsWrite)
                            self.setStdyAvg(avg)
                            self.getStdySlope().extend([k,d])
                            self.getRndMatrices().append([tpRead_l,tpWrite_l])  
                            #Done with 1M block size
                            break
        return self.getReachStdyState()
        
    def run(self):
        '''
         Start the rounds, log the steady state infos and call plot functions.
        @return True if steady state was reached and plots were generated.
        '''
        logging.info("########### Starting Throughput Test ###########")
        steadyState = self.runRounds()
        if steadyState == False:
            logging.info("# Steady State has not been reached for Throughput Test.")
        self.logTestData()
        return True

class WriteSatTest(SsdTest):
    '''
    A class to carry out the Write Saturation test.
    '''
    
    def __init__(self,testname,filename,nj,iod):
        '''
        Constructor.
        '''
        SsdTest.__init__(self, testname, filename, nj, iod)
        self.getFioJob().addKVArg("rw","randwrite")
        self.getFioJob().addKVArg("bs","4k")   
        self.getFioJob().addKVArg("runtime","2")#FIXME
        self.getFioJob().addSglArg("time_based")
        
        ##Number of rounds until write saturation test ended
        self.__rounds = 0
        
        ##Write saturation results: [iops_l,lats_l]
        self.__roundMatrices = []
        
    def getRnds(self):
        return self.__rounds
    def getRndMatrices(self):
        return self.__roundMatrices
    
    def testRound(self):
        '''
        Carry out one test round of the write saturation test.
        The round consists of random writing with 4k bs for one minute
        @return [TotWriteIO,IOPS,[min,max,mean lats]]
        '''
        (call,jobOut) = self.getFioJob().start()
        if call == False:
            exit(1)
        
        writeIO = self.getFioJob().getTotIOWrite(jobOut)
        iops = self.getFioJob().getIOPS(jobOut)
        lats = self.getFioJob().getWriteLats(jobOut)
        
        logging.info(jobOut)
        logging.info("#IOPS: " + str(iops))
        logging.info("#Tot Write IO: " + str(writeIO))
        logging.info("#Latencies: " + str(lats))
        logging.info("######")
        return [writeIO,iops,lats]
    
    def runRounds(self):
        '''
        Carry out the write saturation test rounds
        '''
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
        
        self.__rounds = maxRounds
        #assume all rounds must be carried out            
        for i in range(maxRounds):
            logging.info("#################")
            logging.info("Round nr. "+str(i))
            writeIO,iops,lats = self.testRound()
            iops_l.append(iops)
            lats_l.append(lats)
            totWriteIO += writeIO
            if i == 0:
                logging.info("#If write IO stays steady, it will take "
                             +str((devSzKB*4)/writeIO)+" rounds to complete.")
            
            #Check if 4 times the device size has been reached
            if totWriteIO >= (devSzKB * 4):
                self.__rounds = i
                break
        self.__roundMatrices.append(iops_l)
        self.__roundMatrices.append(lats_l)
        
        logging.info("#Write saturation has written " + str(totWriteIO) + "KB")
    
    def run(self):
        if self.makeSecureErase() == False:
            logging.error("# Could not carry out secure erase.")
            exit(1)
        logging.info("########### Starting Write Saturation Test ###########")
        self.runRounds()
        logging.info("Write Sat rounds: ")
        logging.info(self.__rounds)
        logging.info("Round Write Saturation results: ")
        logging.info(self.__roundMatrices)
        
    def toXml(self,root):
         
        #root element of current xml child
        r = etree.Element(root)
        
        data = json.dumps(self.__roundMatrices)
        e = etree.SubElement(r,'roundmat')
        e.text = data
        
        data = json.dumps(self.__rounds)
        e = etree.SubElement(r,'rndnr')
        e.text = data
        
        return r
        
    def fromXml(self,root):
        self.__roundMatrices = json.loads(root.findtext('roundmat'))
        self.__rounds = json.loads(root.findtext('rndnr'))
        logging.info("########### Loading from "+self.getTestname()+".xml ###########")
        logging.info("Write Sat rounds: ")
        logging.info(self.__rounds)
        logging.info("Round Write Saturation results: ")
        logging.info(self.__roundMatrices)

class IodTest(SsdTest):
    
    
    ##RW modes for io depth test
    iodRW = ["read","write","randread","randwrite"]
    
    ##Labels of block sizes for io depth test
    bsLabels = ["1024k","64k","4k","512"]
    
    ##Io depths for libaio
    iodDepths = [1,4,16,64]
    
    '''
    Constructor.
    '''
    def __init__(self,testname,filename,nj,iod):
        SsdTest.__init__(self, testname, filename, nj, iod)
        self.getFioJob().addKVArg("rw","randwrite")
        self.getFioJob().addKVArg("bs","4k")   
        self.getFioJob().addKVArg("runtime","2")#FIXME
        self.getFioJob().addSglArg("time_based")
        
        ##Number of rounds until write saturation test ended.
        self.__rounds = 0
        
        ##Write saturation results: [iops_l,lats_l].
        self.__roundMatrices = []
    
    def getRnds(self):
        return self.__rounds
    def getRndMatrices(self):
        return self.__roundMatrices
    
    def testRnd(self):
        '''
        Carry out one test round of the io depth test.
        The round consists of read, writing, rand read, rand write
        with different block sizes and io depths (libaio).
        @return [writeIO,roundMatrix] Total written IO in KB while write test
        and a Matrix of rw,bs,iodepth
        '''
        #start the fio job rounds with the given static
        #parameters
        writeIO = 0
        roundMatrix = []
        for rw in IodTest.iodRW:
            rwRow = []
            for bs in IodTest.bsLabels:
                bsRow = []
                for iod in IodTest.iodDepths:
                    self.getFioJob().addKVArg("rw",rw)
                    self.getFioJob().addKVArg("bs",bs)
                    self.getFioJob().addKVArg("iodepth",str(iod))
                    
                    (call,jobOut) = self.getFioJob().start()
                    if call == False:
                        exit(1)
                    logging.info("rw: " +rw)
                    logging.info("bs: "+bs)
                    logging.info("iodepth: "+str(iod))
                    logging.info(jobOut)
                    logging.info("######")
                    if rw == "read":
                        bsRow.append(self.getFioJob().getTPRead(jobOut))
                    if rw == "write":
                        bsRow.append(self.getFioJob().getTPWrite(jobOut))
                        #we keep the written IO to know if we should stop
                    #Sum up the write IO for 1M block size
                    if rw == "write" and bs == "1024k":
                        writeIO += self.getFioJob().getTotIOWrite(jobOut)
                    if rw == "randread":
                        bsRow.append(self.getFioJob().getIOPSRead(jobOut))
                    if rw == "randwrite":
                        bsRow.append(self.getFioJob().getIOPSWrite(jobOut))
                rwRow.append(bsRow)
            roundMatrix.append(rwRow)
        logging.info("#Tot Write IO: " + str(writeIO))
        return [writeIO,roundMatrix]
    
    def runRounds(self):
        (call,devSzKB) = self.getDevSizeKB()
        if call == False:
            logging.error("#Could not get size of device.")
            exit(1)
        totWriteIO = 0 #total written IO in KB, must be greater than 4xDevice 
        #carry out the test for a maximum of 24h, one round runs for 1 minute
        maxRounds = 60*24
        
        self.__rounds = maxRounds
        roundMatrix = []
        #assume all rounds must be carried out            
        for i in range(maxRounds):
            logging.info("######")
            logging.info("Round nr. "+str(i))
            writeIO,roundMatrix = self.testRnd()
            self.__roundMatrices.append(roundMatrix)
            totWriteIO += writeIO
            
            #Check if 2 times the device size has been reached
            if totWriteIO >= (devSzKB):
                self.__rounds = i
                break
        
        logging.info("#IO depth test has written " + str(totWriteIO) + "KB")
        
    def run(self):
        if self.makeSecureErase() == False:
            logging.error("# Could not carry out secure erase.")
            exit(1)
        logging.info("########### Starting IO Depth Test ###########")
        self.runRounds()
        logging.info("IO Depth rounds: ")
        logging.info(self.__rounds)
        logging.info("Round IO Depth results: ")
        logging.info(self.__roundMatrices)
        
        return True
    def toXml(self,root):
         
        #root element of current xml child
        r = etree.Element(root)
        
        data = json.dumps(self.__roundMatrices)
        e = etree.SubElement(r,'roundmat')
        e.text = data
        
        data = json.dumps(self.__rounds)
        e = etree.SubElement(r,'rndnr')
        e.text = data
        
        return r
    
    def fromXml(self,root):
        self.__roundMatrices = json.loads(root.findtext('roundmat'))
        self.__rounds = json.loads(root.findtext('rndnr'))
        logging.info("########### Loading from "+self.getTestname()+".xml ###########")
        logging.info("IO Depth rounds: ")
        logging.info(self.__rounds)
        logging.info("Round IO Depth results: ")
        logging.info(self.__roundMatrices)