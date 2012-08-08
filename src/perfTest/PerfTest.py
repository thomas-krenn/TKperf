'''
Created on 07.08.2012

@author: gschoenb
'''
import perfTest.SsdTest as ssd

import perfTest.HddTest as hdd

from reports.XmlReport import XmlReport
from lxml import etree

from matplotlib.backends.backend_pdf import PdfPages

class PerfTest(object):
    '''
    A performance test, consists of multiple Device Tests
    '''


    def __init__(self,testname,filename,baseDir):
        '''
        A performance test has several reports and plots.
        '''
        
        ## The output file for the fio job test results.
        self.__testname = testname
        
        ## The data file for the test, can be a whole device also.
        self.__filename = filename
        
        ## Base directory to write results to.
        self.__baseDir = baseDir
        if self.__baseDir != '':
            if self.__baseDir[-1] != '/':
                self.__baseDir += '/'
            
        ## Xml file to write test results to
        self.__xmlReport = XmlReport(testname)
        
        ## Pdf file to write pyplot images to
        self.__pdfReport = PdfPages(self.__testname+'.pdf')
        
        ## List of tests to carry out
        self.__tests = []

    def getTestname(self):
        return self.__testname
    
    def getFilename(self):
        return self.__filename
    
    def getTests(self):
        return self.__tests
    
    def runTests(self):
        for test in self.__tests:
            test.run()
    
    def getXmlReport(self):
        return self.__xmlReport
    
    def getPdfReport(self):
        return self.__pdfReport
    
    def getBaseDir(self):
        return self.__baseDir
    
    def setBaseDir(self):
        for test in self.__tests:
            test.setBaseDir(self.__baseDir)

class SsdPerfTest(PerfTest):
    '''
    A performance test for ssds consists of all ssd tests
    '''
    
    def __init__(self,testname,filename,baseDir,nj,iod):
        PerfTest.__init__(self, testname, filename, baseDir)
        
        test = ssd.IopsTest(testname,filename,nj,iod)
        self.getTests().append(test)
        test = ssd.LatencyTest(testname,filename,nj,iod)
        self.getTests().append(test)
        test = ssd.TPTest(testname,filename,nj,iod)
        self.getTests().append(test)
        test = ssd.WriteSatTest(testname,filename,nj,iod)
        self.getTests().append(test)
        test = ssd.IodTest(testname,filename,nj,iod)
        self.getTests().append(test)
        
        if self.getBaseDir() != '':
            self.setBaseDir()
    
    def run(self):
        self.runTests()
        
    def toXml(self):
        tests = self.getTests()
        e = self.getXmlReport().getXml()
        e.append(tests[0].toXml('iops'))
        e = self.getXmlReport().getXml()
        e.append(tests[1].toXml('lat'))
        e = self.getXmlReport().getXml()
        e.append(tests[2].toXml('tp'))
        e = self.getXmlReport().getXml()
        e.append(tests[3].toXml('writesat'))
        e = self.getXmlReport().getXml()
        e.append(tests[4].toXml('iod'))
        
        self.getXmlReport().xmlToFile(self.getTestname())
        

class HddPerfTest(PerfTest):
    '''
    A performance test for hdds consists of all hdd
    '''
    
    def __init__(self,testname,filename,baseDir,iod):
        PerfTest.__init__(self, testname, filename, baseDir)
        
        test = hdd.IopsTest(testname,filename,iod)
        self.getTests().append(test)
        test = hdd.TPTest(testname,filename,iod)
        self.getTests().append(test)
        
        if self.getBaseDir() != '':
            self.setBaseDir()
    
    def run(self):
        self.runTests()

    
        

        