'''
Created on Aug 26, 2014

@author: gschoenb
'''

import logging
import numpy as np
import json
from lxml import etree

class StdyState(object):
    '''
    Used to define a stable state of a device
    '''
    ## Max number of carried out test rounds.
    testRnds = 25
    ## Always use a sliding window of 4 to measure performance values.
    testMesWindow = 4

    def __init__(self):
        '''
        Constructor
        '''
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

    def getRnds(self): return self.__rounds
    def setReachStdyState(self,s): self.__reachStdyState = s

    def isSteady(self):
        '''
        Return if the current state is steady.
        @return: True if yes, False if no
        @exception RuntimeError if state is not set (None)
        '''
        if self.__reachStdyState == None:
            raise RuntimeError, "steady state is none"
        return self.__reachStdyState

    def checkSteadyState(self,xs,ys,rounds):
        '''
        Checks if the steady is reached for the given values.
        The steady state is defined by the allowed data excursion from the average (+-10%), and
        the allowed slope excursion of the linear regression best fit line (+-5%).
        @param xs Values on x axis
        @param ys Corresponding values for xs on y axis
        @param rounds Number of carried out rounds
        @return True (k*x+d is slope line) if steady state is reached, False if not
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

        self.__rounds = rounds
        self.__stdyRnds = xs
        self.__stdyValues = ys
        self.__stdyAvg = avg
        self.__stdySlope.extend([k,d])
        self.__reachStdyState = stdyState
        return stdyState

    def appendXml(self,r):
        '''
        Append the information about a steady state test to a XML node. 
        @param root The xml root tag to append the new elements to
        ''' 
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
        e = etree.SubElement(r,'reachstdystate')
        e.text = data
        
        data = json.dumps(self.__rounds)
        e = etree.SubElement(r,'rndnr')
        e.text = data

    def fromXml(self,root):
        '''
        Loads the information about a steady state from XML.
        @param root The given element containing the information about
        the object to be initialized.
        '''
        self.__stdyRnds = json.loads(root.findtext('stdyrounds'))
        self.__stdyValues = json.loads(root.findtext('stdyvalues'))
        self.__stdySlope = json.loads(root.findtext('stdyslope'))
        self.__stdyAvg = json.loads(root.findtext('stdyavg'))
        self.__reachStdyState = json.loads(root.findtext('reachstdystate'))
        self.__rounds = json.loads(root.findtext('rndnr'))
        logging.info("########### Loading steady state from xml ###########")
        self.toLog()

    def toLog(self):
        '''
        Log information about the steady state and how it 
        has been reached.
        '''
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