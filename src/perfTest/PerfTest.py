'''
Created on 07.08.2012

@author: gschoenb
'''
from perfTest.SsdTest import IopsTest, LatencyTest, TPTest, WriteSatTest,\
    IodTest

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
        self.__xmlReport = ''
        
        ## Pdf file to write pyplot images to
        self.__pdfReport = ''
        
        ## List of tests to carry out
        self.__tests = []

    def getTests(self):
        return self.__tests
    
    def run(self):
        for test in self.__tests:
            test.run()

class SsdPerfTest(PerfTest):
    '''
    A performance test for ssds, consists of all ssd tests
    '''
    
    def __init__(self,testname,filename,baseDir,nj,iod):
        PerfTest.__init__(self, testname, filename, baseDir)
        
        test = IopsTest(testname,filename,nj,iod)
        self.getTests().append(test)
        test = LatencyTest(testname,filename,nj,iod)
        self.getTests().append(test)
        test = TPTest(testname,filename,nj,iod)
        self.getTests().append(test)
        test = WriteSatTest(testname,filename,nj,iod)
        self.getTests().append(test)
        test = IodTest(testname,filename,nj,iod)
        self.getTests().append(test)
        
        

        