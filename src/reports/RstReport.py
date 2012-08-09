'''
Created on 9 Aug 2012

@author: gschoenb
'''
from cStringIO import StringIO

class RstReport(object):
    '''
    A report as restructured text.
    '''

    def __init__(self,testname):
        '''
        @param testname Name of the test, also the filename. 
        '''
        self.__testname = testname
        self.__rst = StringIO()
    
    def getRst(self):
        return self.__rst    
    
    def addTitle(self):
        print >>self.__rst,"===================="
        print >>self.__rst,"IO perf test report"
        print >>self.__rst,"====================\n"
        print >>self.__rst,".. contents::"
        print >>self.__rst,".. sectnum::\n"
        
    def addChapter(self,chap):
        print >>self.__rst, chap
        line = "="
        for i in chap:
            line += "="
        print >>self.__rst, line+'\n'
        
    def addString(self,str):
        if str[-1] != '\n':
            str += '\n'
        print >>self.__rst, str
    
    def addFigure(self,filename):
        '''
        Adds a figure to the restructured text.
        @param filename The filename of the figure.
        '''
        print >>self.__rst,".. image:: "+filename 
    
    def toRstFile(self):
        f = open(self.__testname+'.rst','w')
        f.write(self.__rst.getvalue())
        self.__rst.close()
        f.close()
        
    def addSetupInfo(self,str):
        self.addChapter("Setup Information")
        self.addString("Performance Tool:\n" + " - " + str)
        
        
        