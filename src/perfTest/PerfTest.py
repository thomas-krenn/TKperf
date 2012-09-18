'''
Created on 07.08.2012

@author: gschoenb
'''
import logging
import subprocess
from lxml import etree
import json
import datetime

import perfTest.SsdTest as ssd
import perfTest.HddTest as hdd
from reports.XmlReport import XmlReport
from reports.RstReport import RstReport
import plots.genPlots as pgp

class PerfTest(object):
    '''
    A performance test, consists of multiple Device Tests
    '''
    
    def __init__(self,testname,filename):
        '''
        A performance test has several reports and plots.
        '''
        
        ## The output file for the fio job test results.
        self.__testname = testname
        
        ## The data file for the test, can be a whole device also.
        self.__filename = filename
        
        ## Xml file to write test results to
        self.__xmlReport = XmlReport(testname)
        
        ## Rst file to generate pdf of
        self.__rstReport = RstReport(self.__testname)
        
        ## Dictionary of tests to carry out
        self.__tests = {}
        
        ## Information about the tested device fetched via hdparm or a desc file
        self.__deviceInfo = None
        
        ## Date the test has been carried out
        self.__testDate = None

    def getTestname(self):
        return self.__testname
    
    def getFilename(self):
        return self.__filename
    
    def getDevInfo(self):
        return self.__deviceInfo
    
    def getTestDate(self):
        return self.__testDate
    
    def readDevInfoHdparm(self):
        '''
        Read the device information via hdparm -I. If an error occured
        the script is stopped and an error message to use a description
        file is printed to the log file.
        @return True if the device info was set, False if not.
        '''
        #device info has already been set
        if self.__deviceInfo != None:
            return True
        
        out = subprocess.Popen(['hdparm','-I',self.__filename],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdout,stderr) = out.communicate()
        if stderr != '':
            logging.error("hdparm -I encountered an error: " + stderr)
            logging.error("Please use a description file to set device information!")
            return False
        else:
            self.__deviceInfo = ""
            for line in stdout.split('\n'):
                if line.find("questionable sense data") > -1 or line.find("bad/missing sense data") > -1:
                    logging.error("hdparm sense data may be incorrect!")
                    logging.error("Please use a description file to set device information!")
                    return False
                
                if line.find("Model Number") > -1:
                    self.__deviceInfo += line + '\n'
                if line.find("Serial Number") > -1:
                    self.__deviceInfo += line +'\n'
                if line.find("Firmware Revision") > -1:
                    self.__deviceInfo += line + '\n'
                if line.find("Media Serial Num") > -1:
                    self.__deviceInfo += line + '\n'
                if line.find("Media Manufacturer") > -1:
                    self.__deviceInfo += line + '\n'
                if line.find("device size with M = 1000*1000") > -1:
                    self.__deviceInfo += line + '\n'
            logging.info("# Testing device: " + self.__deviceInfo)
            return True

    def readDevInfoFile(self,fd):
        '''
        Reads the device description from a file. This is necessary if
        the device informaiton cannot be fetched via hdparm.
        @param fd The path to the description file, has to be opened already.
        '''
        self.__deviceInfo = fd.read()
        fd.close()
    
    def setDevInfo(self,devStr):
        '''
        Init the device information with the given string.
        @param devStr The device information as string.
        '''
        self.__deviceInfo = devStr

    def setTestDate(self,dateStr):
        '''
        Sets the date the test has been carried out.
        @param dateStr The date string.
        '''
        self.__testDate = dateStr

    def getTests(self):
        return self.__tests
    
    def addTest(self,key,test):
        '''
        Add a test to the test dictionary.
        @param key The key for the test in the dictionary.
        @param test The test object to be added.
        '''
        self.__tests[key] = test
    
    def resetTests(self):
        '''
        Clear the dictionary containing the tests.
        '''
        self.__tests.clear()
    
    def runTests(self):
        '''
        Call the run method of every test in the test dictionary. The run method
        of a test is its core function where the performance test is carried out.
        '''
        #sort per key to ensure tests have the same order
        sorted(self.__tests.items())
        for k,v in self.__tests.items():
            print "Starting test: " + k
            v.run()
    
    def addSglArgToTests(self,key):
        '''
        Adds a single key argument to the Fio job of every test.
        @param key The argument to be added to the job.
        '''
        for v in self.__tests.values():
            v.getFioJob().addSglArg(key)
    
    def getXmlReport(self):
        return self.__xmlReport
    
    def getRstReport(self):
        return self.__rstReport
    
    def toXml(self):
        '''
        First the device information is written to the xml file.
        Calls for every test in the test dictionary the toXMl method
        and writes the results to the xml file.
        '''
        tests = self.getTests()
        e = self.getXmlReport().getXml()
        
        #add the current date to the xml
        now = datetime.datetime.now()
        dev = etree.SubElement(e,'testdate')
        dev.text = json.dumps(now.strftime("%Y-%m-%d"))
        
        #Add the device information to the xml file
        dev = etree.SubElement(e,'devinfo')
        dev.text = json.dumps(self.__deviceInfo)
        
        #call the xml function for every test in the dictionary
        sorted(self.__tests.items())
        for k,v in tests.iteritems():
            e.append(v.toXml(k))
        
        self.getXmlReport().xmlToFile(self.getTestname())

class SsdPerfTest(PerfTest):
    '''
    A performance test for ssds consists of all ssd tests
    '''
    
    ## Keys valid for test dictionary and xml file
    testKeys = ['iops','lat','tp','writesat','iod']
    
    def __init__(self,testname,filename,nj,iod):
        PerfTest.__init__(self, testname, filename)
        
        ## Number of jobs for fio.
        self.__nj = nj
        
        ## Number of iodepth for fio.
        self.__iod = iod
        
        #Add every test to the performance test
        test = ssd.IopsTest(testname,filename,nj,iod)
        self.addTest(SsdPerfTest.testKeys[0], test)
        test = ssd.LatencyTest(testname,filename,nj,iod)
        self.addTest(SsdPerfTest.testKeys[1], test)
        test = ssd.TPTest(testname,filename,nj,iod)
        self.addTest(SsdPerfTest.testKeys[2], test)
        test = ssd.WriteSatTest(testname,filename,nj,iod)
        self.addTest(SsdPerfTest.testKeys[3], test)
        test = ssd.IodTest(testname,filename,nj,iod)
        self.addTest(SsdPerfTest.testKeys[4], test)
        
    def run(self):
        self.runTests()
        self.toXml()
        self.getPlots()
        self.toRst()
        
    def fromXml(self):
        '''
        Reads out the xml file name 'testname.xml' and initializes the test
        specified with xml. The valid tags are "iops,lat,tp,writesat,iod", but
        there don't must be every tag in the file.
        Afterwards the plotting and rst methods for the specified tests are
        called.
        '''
        self.getXmlReport().fileToXml(self.getTestname())
        self.resetTests()
        root = self.getXmlReport().getXml()

        self.setTestDate(json.loads(root.findtext('testdate')))

        #first read the device information from xml
        self.setDevInfo(json.loads(root.findtext('devinfo')))
        
        for tag in SsdPerfTest.testKeys:
            #check which test tags are in the xml file
            for elem in root.iterfind(tag):
                test = None
                if elem.tag == SsdPerfTest.testKeys[0]:
                    test = ssd.IopsTest(self.getTestname(),self.getFilename,self.__nj,self.__iod)
                if elem.tag == SsdPerfTest.testKeys[1]:
                    test = ssd.LatencyTest(self.getTestname(),self.getFilename,self.__nj,self.__iod)
                if elem.tag == SsdPerfTest.testKeys[2]:
                    test = ssd.TPTest(self.getTestname(),self.getFilename,self.__nj,self.__iod)
                if elem.tag == SsdPerfTest.testKeys[3]:
                    test = ssd.WriteSatTest(self.getTestname(),self.getFilename,self.__nj,self.__iod)
                if elem.tag == SsdPerfTest.testKeys[4]:
                    test = ssd.IodTest(self.getTestname(),self.getFilename,self.__nj,self.__iod)
                #we found a tag in the xml file, now we ca read the data from xml
                if test != None:
                    test.fromXml(elem)
                    self.addTest(tag, test)

        self.getPlots()
        self.toRst()
    
    def toRst(self):
        tests = self.getTests()
        rst = self.getRstReport()
        
        rst.addFooter()
        rst.addTitle()
        #fio version is the same for every test, just take the
        #one from iops
        rst.addDevInfo(self.getDevInfo())
        rst.addSetupInfo(tests['iops'].getFioJob().__str__(),self.getTestDate())
        rst.addFioJobInfo(tests['iops'].getNj(), tests['iops'].getIod())
        rst.addGeneralInfo()
        
        rst.addChapter("IOPS")
        rst.addTestInfo('iops',tests['iops'])
        rst.addSection("Measurement Plots")
        for i,fig in enumerate(tests['iops'].getFigures()):
            rst.addFigure(fig,'iops',i)
        rst.addSection("Measurement Window Summary Table")
        rst.addTable(tests['iops'].getTables()[0],ssd.IopsTest.bsLabels,'iops')
        
        rst.addChapter("Throughput")
        rst.addTestInfo('tp',tests['tp'])
        rst.addSection("Measurement Plots")
        for i,fig in enumerate(tests['tp'].getFigures()):
            rst.addFigure(fig,'tp',i)
        rst.addSection("Measurement Window Summary Table")    
        rst.addTable(tests['tp'].getTables()[0],ssd.TPTest.bsLabels,'tp')
            
        rst.addChapter("Latency")
        rst.addTestInfo('lat',tests['lat'])
        rst.addSection("Measurement Plots")
        for i,fig in enumerate(tests['lat'].getFigures()):
            #index 2 and 3 are 2D measurement plots that are not required
            #but we need them to generate the measurement overview table
            if i == 2 or i == 3: continue
            rst.addFigure(fig,'lat',i)
        rst.addSection("Measurement Window Summary Table")    
        rst.addTable(tests['lat'].getTables()[0],ssd.LatencyTest.bsLabels,'avg-lat')#avg lat 
        rst.addTable(tests['lat'].getTables()[1],ssd.LatencyTest.bsLabels,'max-lat')#max lat
        
        rst.addChapter("Write Saturation")
        rst.addTestInfo('writesat',tests['writesat'])
        rst.addSection("Measurement Plots")
        for i,fig in enumerate(tests['writesat'].getFigures()):
            rst.addFigure(fig,'writesat',i)

        rst.toRstFile()
        
    def getPlots(self):
        tests = self.getTests()
        #plots for iops
        if SsdPerfTest.testKeys[0] in tests:
            pgp.stdyStConvPlt(tests['iops'],"IOPS")
            pgp.stdyStVerPlt(tests['iops'],"IOPS")
            pgp.mes2DPlt(tests['iops'],"IOPS")
            pgp.mes3DPlt(tests['iops'],"IOPS")
        #plots for latency
        if SsdPerfTest.testKeys[1] in tests:
            pgp.stdyStConvPlt(tests['lat'],"LAT")
            pgp.stdyStVerPlt(tests['lat'],"LAT")
            pgp.mes2DPlt(tests['lat'],"avg-LAT")
            pgp.mes2DPlt(tests['lat'],"max-LAT")
            pgp.latMes3DPlt(tests['lat'])
        #plots for throughout
        if SsdPerfTest.testKeys[2] in tests:
            pgp.tpRWStdyStConvPlt(tests['tp'])
            pgp.stdyStVerPlt(tests['tp'],"TP")
            pgp.tpMes2DPlt(tests['tp'])
        #plots for write saturation
        if SsdPerfTest.testKeys[3] in tests:
            pgp.writeSatIOPSPlt(tests['writesat'])
            pgp.writeSatLatPlt(tests['writesat'])
        #plots for io depth        
        if SsdPerfTest.testKeys[4] in tests:
            pgp.ioDepthMes3DPlt(tests['iod'],"read")
            pgp.ioDepthMes3DPlt(tests['iod'],"write")
            pgp.ioDepthMes3DPlt(tests['iod'],"randread")
            pgp.ioDepthMes3DPlt(tests['iod'],"randwrite")

class HddPerfTest(PerfTest):
    '''
    A performance test for hdds consists of all hdd tests.
    '''
    
    ## Keys valid for test dictionary and xml file
    testKeys = ['iops','tp']
    
    def __init__(self,testname,filename,iod):
        PerfTest.__init__(self, testname, filename)
        
        ## Number of iodepth for fio.
        self.__iod = iod
        
        test = hdd.IopsTest(testname,filename,iod)
        self.addTest(HddPerfTest.testKeys[0],test)
        test = hdd.TPTest(testname,filename,iod)
        self.addTest(HddPerfTest.testKeys[1],test)
        
    def run(self):
        self.runTests()
        self.toXml()
        self.getPlots()
        self.toRst()
    
    def fromXml(self):
        '''
        Reads out the xml file name 'testname.xml' and initializes the test
        specified with xml. The valid tags are "iops,tp", but
        there don't must be every tag in the file.
        Afterwards the plotting and rst methods for the specified tests are
        called.
        '''
        self.getXmlReport().fileToXml(self.getTestname())
        self.resetTests()
        root = self.getXmlReport().getXml()
        
        self.setTestDate(json.loads(root.findtext('testdate')))
        
        #first read the device information from xml
        self.setDevInfo(self.root.find('devInfo'))

        for tag in HddPerfTest.testKeys:
            for elem in root.iterfind(tag):
                test = None
                if elem.tag == HddPerfTest.testKeys[0]:
                    test = hdd.IopsTest(self.getTestname(),self.getFilename,self.__iod)
                if elem.tag == HddPerfTest.testKeys[1]:
                    test = hdd.TPTest(self.getTestname(),self.getFilename,self.__iod)
                if test != None:
                    test.fromXml(elem)
                    self.addTest(tag, test)

        self.getPlots()
        self.toRst()
    
    def toRst(self):
        tests = self.getTests()
        rst = self.getRstReport()
        rst.addFooter()
        rst.addTitle()
        rst.addDevInfo(self.getDevInfo())
        #fio version is the same for every test, just take the
        #one from iops
        rst.addSetupInfo(tests['iops'].getFioJob().__str__(),self.getTestDate())
        rst.addFioJobInfo(tests['iops'].getNj(), tests['iops'].getIod())
        
        rst.addChapter("IOPS")
        rst.addFigure(tests['iops'].getFigure()[0])
        rst.toRstFile()
        
        rst.addChapter("Throughput")
        rst.addFigure(tests['tp'].getFigure()[0])
        rst.toRstFile()
        
    def getPlots(self):
        tests = self.getTests()
        if HddPerfTest.testKeys[0] in tests:
            pgp.IOPSplot(tests['iops'])
        if HddPerfTest.testKeys[1] in tests:
            pgp.tpStdyStConvPlt(tests['tp'], "rw","hdd")

        