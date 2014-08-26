'''
Created on Aug 26, 2014

@author: gschoenb
'''

import numpy as np

class StdyState(object):
    '''
    Used to define a stable state of a device
    '''
    ## Max number of carried out test rounds.
    testRnds = 25
    ## Always use a sliding window of 4 to measure performance values.
    testMesWindow = 4

    def __init__(self, params):
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

    def isSteady(self):
        if self.__reachStdyState == None:
            raise RuntimeError, "steady state is none"
        return self.__reachStdyState

    def checkSteadyState(self,xs,ys):
        '''
        Checks if the steady is reached for the given values.
        The steady state is defined by the allowed data excursion from the average (+-10%), and
        the allowed slope excursion of the linear regression best fit line (+-5%).
        @param xs Values on x axis
        @param ys Corresponding values for xs on y axis 
        @return [True,avg,k,d] (k*x+d is slope line) if steady state is reached, [False,avg,k,d] if not
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

        self.__stdyRnds = xs
        self.__stdyValues = ys
        self.__stdyAvg = avg
        self.__stdySlope.extend([k,d])
        self.__reachStdyState = stdyState
        return stdyState