'''
Created on 07.08.2012

@author: gschoenb
'''
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

    def getTestname(self):
        return self.__testname
    
    def getFilename(self):
        return self.__filename
    
    def getTests(self):
        return self.__tests
    
    def addTest(self,key,test):
        self.__tests[key] = test
    
    def resetTests(self):
        self.__tests.clear()
    
    def runTests(self):
        for test in self.__tests:
            test.run()
    
    def getXmlReport(self):
        return self.__xmlReport
    
    def getRstReport(self):
        return self.__rstReport
    
    def toXml(self):
        '''
        Calls for every test in the test dictionary the toXMl method
        and writes the results to the xml file.
        '''
        tests = self.getTests()
        e = self.getXmlReport().getXml()
        
        #call the xml function for every test in the dictionary
        #TODO Sort the dict
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
        for tag in SsdPerfTest.testKeys:
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
        rst.addSetupInfo(tests['iops'].getFioJob().__str__())
        rst.addFioJobInfo(tests['iops'].getNj(), tests['iops'].getIod())
        rst.addGeneralInfo()
        
        rst.addChapter("IOPS")
        rst.addTestInfo('iops')
        rst.addSection("Measurement Plots")
        for i,fig in enumerate(tests['iops'].getFigures()):
            rst.addFigure(fig,'iops',i)
        rst.addSection("Measurement Window Summary Table")
        rst.addTable(tests['iops'].getTables()[0],ssd.IopsTest.bsLabels,'iops')
        
        rst.addChapter("Throughput")
        rst.addTestInfo('tp')
        rst.addSection("Measurement Plots")
        for i,fig in enumerate(tests['tp'].getFigures()):
            rst.addFigure(fig,'tp',i)
        rst.addSection("Measurement Window Summary Table")    
        rst.addTable(tests['tp'].getTables()[0],ssd.TPTest.bsLabels,'tp')
            
        rst.addChapter("Latency")
        rst.addTestInfo('lat')
        rst.addSection("Measurement Plots")
        for i,fig in enumerate(tests['lat'].getFigures()):
            rst.addFigure(fig,'lat',i)
        rst.addSection("Measurement Window Summary Table")    
        rst.addTable(tests['lat'].getTables()[0],ssd.LatencyTest.bsLabels,'avg-lat')#avg lat 
        rst.addTable(tests['lat'].getTables()[1],ssd.LatencyTest.bsLabels,'max-lat')#max lat
        
        rst.addChapter("Write Saturation")
        rst.addTestInfo('writesat')
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
            pgp.latMes3DPlt(tests['lat'])
        #plots for throughout
        if SsdPerfTest.testKeys[2] in tests:
            pgp.tpStdyStConvPlt(tests['tp'], "read","ssd")
            pgp.tpStdyStConvPlt(tests['tp'], "write","ssd")
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
        for tag in HddPerfTest.testKeys:
            for elem in root.iterfind(tag):
                test = None
                if elem.tag == HddPerfTest.testKeys[0]:
                    test = hdd.IopsTest(self.getTestname(),self.getFilename,self.__nj,self.__iod)
                if elem.tag == HddPerfTest.testKeys[1]:
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
        #fio version is the same for every test, just take the
        #one from iops
        rst.addSetupInfo(tests['iops'].getFioJob().__str__())
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

        