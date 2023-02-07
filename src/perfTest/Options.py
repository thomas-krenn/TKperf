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

    def __init__(self, nj=1, iod=1, runtime=60, tpramptime=30, testRounds=25, xargs=None):
        '''
        Constructor
        @param nj Number of jobs
        @param iod Number for io depth
        @param xargs Further argument as list for all fio jobs in tests
        @param testRounds Maximum number of test rounds in a test
        '''
        ## Number of jobs for fio.
        self.__nj = nj
        ## Number of iodepth for fio.
        self.__iod = iod
        ## Runtime of one test round for fio.
        self.__runtime = runtime
        ## Further single arguments as list for fio.
        self.__xargs = xargs
        ## ramp_time of one write test round for fio
        self.__tpramptime = tpramptime
        ## Max number of carried out test rounds.
        self.__testRnds = testRounds

    def getNj(self): return self.__nj
    def getIod(self): return self.__iod
    def getRuntime(self): return self.__runtime
    def getTPramptime(self): return self.__tpramptime
    def getXargs(self): return self.__xargs
    def getTestRnds(self): return self.__testRnds
    def setNj(self,nj): self.__nj = nj
    def setIod(self,iod): self.__iod = iod
    def setRuntime(self,rt): self.__runtime = rt
    def setTPramptime(self,ramptime): self.__tpramptime = ramptime
    def setXargs(self,xargs): self.__xargs = xargs
    def setTestRnds(self,rnds): self.__testRnds = rnds
    
    def appendXml(self,r):
        '''
        Append the information about options to a XML node. 
        @param root The xml root tag to append the new elements to
        ''' 
        data = json.dumps(self.__nj)
        e = etree.SubElement(r,'numjobs')
        e.text = data
        
        data = json.dumps(self.__iod)
        e = etree.SubElement(r,'iodepth')
        e.text = data
        
        data = json.dumps(self.__runtime)
        e = etree.SubElement(r,'runtime')
        e.text = data
        
        data = json.dumps(self.__tpramptime)
        e = etree.SubElement(r,'tpramptime')
        e.text = data
        
        data = json.dumps(self.__testRnds)
        e = etree.SubElement(r,'testrnds')
        e.text = data
        
        if self.__xargs != None:
            data = json.dumps(list(self.__xargs))
            e = etree.SubElement(r,'xargs')
            e.text = data

    def fromXml(self,root):
        '''
        Loads the information about options from XML.
        @param root The given element containing the information about
        the object to be initialized.
        '''
        if root.findtext('numjobs'):
            self.__nj = json.loads(root.findtext('numjobs'))
        if root.findtext('iodepth'):
            self.__iod = json.loads(root.findtext('iodepth'))
        if root.findtext('runtime'):
            self.__runtime = json.loads(root.findtext('runtime'))
        if root.findtext('tpramptime'):
            self.__runtime = json.loads(root.findtext('tpramptime'))
        if root.findtext('testrnds'):
            self.__runtime = json.loads(root.findtext('testrnds'))
        if root.findtext('xargs'):
                self.__xargs = json.loads(root.findtext('xargs'))
        logging.info("# Loading options from xml")
        logging.info("# Options nj:"+str(self.__nj))
        logging.info("# Options iod: "+str(self.__iod))
        logging.info("# Options tpramptime: "+str(self.__tpramptime))
        if self.__xargs != None:
            logging.info("# Options xargs:")
            logging.info(self.__xargs)
