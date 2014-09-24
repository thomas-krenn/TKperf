'''
Created on Sep 24, 2014

@author: gschoenb
'''

import subprocess
import logging

class OS(object):
    '''
    Represents the operating system the performance test is running on.
    '''

    def __init__(self, params):
        '''
        Constructor
        '''
        self.__blockdevs = []

    def getBlockDevs(self): return self.__blockdevs

    def checkBlockDevs(self):
        '''
        Checks the current available block devices.
        Sets blockdevs of OS.
        '''
        out = subprocess.Popen(['lsblk', '-l', '-n', '-e', '7', '-e', '1', '-o', 'NAME'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (stdout, stderr) = out.communicate()
        if stderr != '':
            logging.error("lsblk encountered an error: " + stderr)
            raise RuntimeError, "lsblk command error"
        else:
            self.__blockdevs = stdout.splitlines()
