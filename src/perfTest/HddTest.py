'''
Created on 04.07.2012

@author: gschoenb
'''

class HddTest(object):
    '''
    A fio performance test for a hard disk.
    '''
    
    def __init__(self,testName):
        '''
        Constructor
        @param testName Name of the test, specifies the output file 
        '''
        
        ## The output file for the fio job.
        self.__outputFile = testName
        
        