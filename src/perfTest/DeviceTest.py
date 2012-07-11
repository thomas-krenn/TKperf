'''
Created on 04.07.2012

@author: gschoenb
'''

import logging
import subprocess

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
    
    def getDevSizeKB(self):
        '''
        Get the device size in KByte.
        The function calls 'blockdev' to determine device sector size
        and sector count.
        @return [True,size] on success, [False,0] if an error occured.
        '''
        out = subprocess.Popen(['blockdev','--getss',self.__filename],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdout,stderr) = out.communicate()
        if stderr != '':
            logging.error("blockdev --getss encountered an error: " + stderr)
            return [False,0]
        else:
            sectorSize = int(stdout)
            out = subprocess.Popen(['blockdev','--getsz',self.__filename],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            (stdout,stderr) = out.communicate()
            if stderr != '':
                logging.error("blockdev --getsz encountered an error: " + stderr)
                return [False,0]
            else:
                sectorCount = long(stdout)
                devSzKB = (sectorCount * sectorSize) / 1024
                logging.info("#Device" + self.__filename + " sector count: " + str(sectorCount))
                logging.info("#Device" + self.__filename + " sector size: " + str(sectorSize))
                logging.info("#Device" + self.__filename + " size in KB: " + str(devSzKB))
                return [True,devSzKB]