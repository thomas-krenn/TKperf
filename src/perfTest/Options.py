'''
Created on Aug 26, 2014

@author: gschoenb
'''

class Options(object):
    '''
    A class holding user defined options on command line.
    '''

    def __init__(self, nj, iod, xargs):
        '''
        Constructor
        @param nj Number of jobs
        @param iod Number for io depth
        @param xargs Further argument as list for all fio jobs in tests
        '''
        ## Number of jobs for fio.
        self.__nj = nj
        ## Number of iodepth for fio.
        self.__iod = iod
        ## Further single arguments as list for fio.
        self.__xargs = xargs

    def getNj(self): return self.__numJobs
    def getIod(self): return self.__ioDepth
    def getXargs(self): return self.__xargs
    def setNj(self,nj): self.__numJobs = nj
    def setIod(self,iod): self.__ioDepth = iod
    def setXargs(self,xargs): self.__xargs = xargs