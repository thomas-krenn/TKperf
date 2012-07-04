'''
Created on 04.07.2012

@author: gschoenb
'''

class DeviceTest(object):
    '''
    A generic class for a performance test.
    '''


    def __init__(self,testname,filename):
        '''
        Constructor
        @param testname Name of the test, specifies the output file.
        @param filename Name of the device or file to put test data to.  
        '''
        
        ## The output file for the fio job test results.
        self.__testname = testname
        ## The data file for the test, can be a whole device also.
        self.__filename = filename
        
    def getTestname(self):
        ''' Return the name of the test, is the name of the output file also. '''
        return self.__testname
    
    def getFilename(self):
        ''' Return the name of the data file or device. '''
        return self.__filename