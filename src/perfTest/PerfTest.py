'''
Created on 07.08.2012

@author: gschoenb
'''
__version__ = '1.0'

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
        
        ## Per default use the version from main module
        self.__IOPerfVersion = __version__
        
        ## A matrix of special features specific for the device
        self.__featureMatrix = None

    def getTestname(self):
        return self.__testname
    
    def getFilename(self):
        return self.__filename
    
    def getDevInfo(self):
        return self.__deviceInfo
    
    def getFeatureMatrix(self):
        return self.__featureMatrix
    
    def getTestDate(self):
        return self.__testDate
    
    def getIOPerfVersion(self):
        return self.__IOPerfVersion
    
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
        the device information cannot be fetched via hdparm.
        @param fd The path to the description file, has to be opened already.
        '''
        self.__deviceInfo = fd.read()
        logging.info("# Read device info from file")
        logging.info("# Testing device: " + self.__deviceInfo)
        fd.close()
    
    def readFeatureMatrix(self,fd):
        '''
        Reads a special feature matrix from a file.
        @param fd The path to the feature matrix file, has to be opened already.
        '''
        self.__featureMatrix = fd.read()
        fd.close()
        
    def setDevInfo(self,devStr):
        '''
        Init the device information with the given string.
        @param devStr The device information as string.
        '''
        self.__deviceInfo = devStr

    def setFeatureMatrix(self,fmStr):
        '''
        Init the device feature matrix with the given string.
        @param devStr The feature matrix as string.
        '''
        self.__featureMatrix = fmStr

    def setTestDate(self,dateStr):
        '''
        Sets the date the test has been carried out.
        @param dateStr The date string.
        '''
        self.__testDate = dateStr

    def setIOPerfVersion(self,verStr):
        '''
        Sets the current io perf version.
        @param verStr The version string.
        '''
        self.__IOPerfVersion = verStr
    
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
        dev = etree.SubElement(e,'testdate')
        dev.text = json.dumps(self.__testDate)
        
        #Add the device information to the xml file
        dev = etree.SubElement(e,'devinfo')
        dev.text = json.dumps(self.__deviceInfo)
        
        #if a feature matrix is given, add it to the xml file
        if self.__featureMatrix != None:
            dev = etree.SubElement(e,'featmatrix')
            dev.text = json.dumps(self.__featureMatrix)
        
        #Add the current test suite version to the xml file
        dev = etree.SubElement(e,'ioperfversion')
        dev.text = json.dumps(self.__IOPerfVersion)
        
        #call the xml function for every test in the dictionary
        sorted(self.__tests.items())
        for k,v in tests.iteritems():
            e.append(v.toXml(k))
        
        self.getXmlReport().xmlToFile(self.getTestname())

class SsdPerfTest(PerfTest):
    '''
    A performance test for ssds consists of all ssd tests
    '''
    
    ## Keys for the tests carried out
    testKeys = ['iops','lat','tp','writesat']
    ## Keys valid for tests
    iopsKey = 'iops'
    latKey = 'lat'
    tpKey = 'tp'
    wrKey = 'writesat'
    
    def __init__(self,testname,filename,nj,iod):
        PerfTest.__init__(self, testname, filename)
        
        ## Number of jobs for fio.
        self.__nj = nj
        
        ## Number of iodepth for fio.
        self.__iod = iod
        
        #Add current date to test
        now = datetime.datetime.now()
        self.setTestDate(now.strftime("%Y-%m-%d"))
        
        #Add every test to the performance test
        for testType in SsdPerfTest.testKeys:
            if testType == SsdPerfTest.iopsKey:
                test = ssd.IopsTest(testname,filename,nj,iod)
            if testType == SsdPerfTest.latKey:
                test = ssd.LatencyTest(testname,filename,nj,iod)
            if testType == SsdPerfTest.tpKey:
                test = ssd.TPTest(testname,filename,nj,iod)
            if testType == SsdPerfTest.wrKey:
                test = ssd.WriteSatTest(testname,filename,nj,iod)
            #add the test to the key/value structure
            self.addTest(testType, test)
        
    def run(self):
        self.runTests()
        self.toXml()
        self.getPlots()
        self.toRst()
        
    def fromXml(self):
        '''
        Reads out the xml file name 'testname.xml' and initializes the test
        specified with xml. The valid tags are "iops,lat,tp,writesat", but
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
        
        #read the feature matrix from the xml file
        if(root.findtext('featmatrix')):
            self.setFeatureMatrix(json.loads(root.findtext('featmatrix')))
        
        #first read the device information from xml
        self.setIOPerfVersion(json.loads(root.findtext('ioperfversion')))
        
        for tag in SsdPerfTest.testKeys:
            #check which test tags are in the xml file
            for elem in root.iterfind(tag):
                test = None
                if elem.tag == SsdPerfTest.iopsKey:
                    test = ssd.IopsTest(self.getTestname(),self.getFilename,self.__nj,self.__iod)
                if elem.tag == SsdPerfTest.latKey:
                    test = ssd.LatencyTest(self.getTestname(),self.getFilename,self.__nj,self.__iod)
                if elem.tag == SsdPerfTest.tpKey:
                    test = ssd.TPTest(self.getTestname(),self.getFilename,self.__nj,self.__iod)
                if elem.tag == SsdPerfTest.wrKey:
                    test = ssd.WriteSatTest(self.getTestname(),self.getFilename,self.__nj,self.__iod)
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
        rst.addDevInfo(self.getDevInfo(),self.getFeatureMatrix())
        #add the fio version, nj, iod and general info of one test to the report
        for keys in tests.iterkeys():
            rst.addSetupInfo(self.getIOPerfVersion(),tests[keys].getFioJob().getFioVersion(),
                             self.getTestDate())
            rst.addFioJobInfo(tests[keys].getNj(), tests[keys].getIod())
            rst.addGeneralInfo()
            break
        
        if SsdPerfTest.iopsKey in tests:
            rst.addChapter("IOPS")
            rst.addTestInfo('iops',tests['iops'])
            rst.addSection("Measurement Plots")
            for i,fig in enumerate(tests['iops'].getFigures()):
                rst.addFigure(fig,'iops',i)
            rst.addSection("Measurement Window Summary Table")
            rst.addTable(tests['iops'].getTables()[0],ssd.IopsTest.bsLabels,'iops')
        if SsdPerfTest.tpKey in tests:
            rst.addChapter("Throughput")
            rst.addTestInfo('tp',tests['tp'])
            rst.addSection("Measurement Plots")
            for i,fig in enumerate(tests['tp'].getFigures()):
                rst.addFigure(fig,'tp',i)
            rst.addSection("Measurement Window Summary Table")    
            rst.addTable(tests['tp'].getTables()[0],ssd.TPTest.bsLabels,'tp')
        if SsdPerfTest.latKey in tests:
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
        if SsdPerfTest.wrKey in tests:
            rst.addChapter("Write Saturation")
            rst.addTestInfo('writesat',tests['writesat'])
            rst.addSection("Measurement Plots")
            for i,fig in enumerate(tests['writesat'].getFigures()):
                rst.addFigure(fig,'writesat',i)

        rst.toRstFile()
        
    def getPlots(self):
        tests = self.getTests()
        #plots for iops
        if SsdPerfTest.iopsKey in tests:
            pgp.stdyStConvPlt(tests['iops'],"IOPS")
            pgp.stdyStVerPlt(tests['iops'],"IOPS")
            pgp.mes2DPlt(tests['iops'],"IOPS")
            pgp.mes3DPlt(tests['iops'],"IOPS")
        #plots for latency
        if SsdPerfTest.latKey in tests:
            pgp.stdyStConvPlt(tests['lat'],"LAT")
            pgp.stdyStVerPlt(tests['lat'],"LAT")
            pgp.mes2DPlt(tests['lat'],"avg-LAT")
            pgp.mes2DPlt(tests['lat'],"max-LAT")
            pgp.latMes3DPlt(tests['lat'])
        #plots for throughout
        if SsdPerfTest.tpKey in tests:
            pgp.tpRWStdyStConvPlt(tests['tp'])
            pgp.stdyStVerPlt(tests['tp'],"TP")
            pgp.tpMes2DPlt(tests['tp'])
        #plots for write saturation
        if SsdPerfTest.wrKey in tests:
            pgp.writeSatIOPSPlt(tests['writesat'])
            pgp.writeSatLatPlt(tests['writesat'])

class HddPerfTest(PerfTest):
    '''
    A performance test for hdds consists of all hdd tests.
    '''
    
    ## Keys valid for test dictionary and xml file
    testKeys = ['iops','tp']
    ## Keys valid for tests
    iopsKey = 'iops'
    tpKey = 'tp'
    
    def __init__(self,testname,filename, nj, iod):
        PerfTest.__init__(self, testname, filename)
        
        ## Number of jobs for fio.
        self.__nj = nj
        
        ## Number of iodepth for fio.
        self.__iod = iod
        
        #Add current date
        now = datetime.datetime.now()
        self.setTestDate(now.strftime("%Y-%m-%d"))
        
                #Add every test to the performance test
        for testType in HddPerfTest.testKeys:
            if testType == HddPerfTest.iopsKey:
                test = hdd.IopsTest(testname,filename,nj,iod)
            if testType == HddPerfTest.tpKey:
                test = hdd.TPTest(testname,filename,nj,iod)
            #add the test to the key/value structure
            self.addTest(testType, test)
        
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
        
        #read the feature matrix from the xml file
        if(root.findtext('featmatrix')):
            self.setFeatureMatrix(json.loads(root.findtext('featmatrix')))
        
        #first read the device information from xml
        self.setIOPerfVersion(json.loads(root.findtext('ioperfversion')))

        for tag in HddPerfTest.testKeys:
            for elem in root.iterfind(tag):
                test = None
                if elem.tag == HddPerfTest.iopsKey:
                    test = hdd.IopsTest(self.getTestname(),self.getFilename,self.__nj,self.__iod)
                if elem.tag == HddPerfTest.tpKey:
                    test = hdd.TPTest(self.getTestname(),self.getFilename,self.__nj,self.__iod)
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
        rst.addSetupInfo(self.getIOPerfVersion(),tests['iops'].getFioJob().getFioVersion(),self.getTestDate())
        rst.addFioJobInfo(tests['iops'].getNj(), tests['iops'].getIod())
        rst.addGeneralInfo()
        
        rst.addChapter("IOPS")
        rst.addFigure(tests['iops'].getFigure()[0])
        rst.toRstFile()
        
        rst.addChapter("Throughput")
        rst.addFigure(tests['tp'].getFigure()[0])
        rst.toRstFile()
        
    def getPlots(self):
        tests = self.getTests()
        if HddPerfTest.iopsKey in tests:
            pgp.IOPSplot(tests['iops'])
        if HddPerfTest.tpKey in tests:
            pgp.tpStdyStConvPlt(tests['tp'], "rw","hdd")

        