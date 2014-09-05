'''
Created on Aug 26, 2014

@author: gschoenb
'''

import logging
import json
from lxml import etree

class Options(object):
    '''
    A class holding user defined options on command line.
    '''

    def __init__(self, nj=1, iod=1, xargs=None):
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
    
    def appendXml(self,r):
        '''
        Append the information about options to a XML node. 
        @param root The xml root tag to append the new elements to
        ''' 
        data = json.dumps(list(self.__numJobs))
        e = etree.SubElement(r,'numjobs')
        e.text = data
        
        data = json.dumps(list(self.__ioDepth))
        e = etree.SubElement(r,'iodepth')
        e.text = data
        
        data = json.dumps(list(self.__xargs))
        e = etree.SubElement(r,'xargs')
        e.text = data

    def fromXml(self,root):
        '''
        Loads the information about options from XML.
        @param root The given element containing the information about
        the object to be initialized.
        '''
        self.__numJobs = json.loads(root.findtext('numjobs'))
        self.__ioDepth = json.loads(root.findtext('iodepth'))
        self.__xargs = json.loads(root.findtext('xargs'))
        logging.info("# Loading options from xml")