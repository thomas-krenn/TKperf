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
    def __init__(self):
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

class Storcli(object):
    '''
    Represents the information about the current storcli controller management.
    '''
    def __init__(self):
        '''
        Constructor
        '''
        self.__path = None
    
    def initialize(self):
        storcli = subprocess.Popen(['which', 'storcli'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout = storcli.communicate()[0]
        if storcli.returncode != 0:
            logging.error("# Error: command 'which storcli' returned an error code.")
            raise RuntimeError, "which storcli command error"
        else:
            self.__path = stdout.rstrip("\n");
