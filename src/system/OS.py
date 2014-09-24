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
        self.__blockdevs = None

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
        ## Path of the storcli executable
        self.__path = None
        ## List of current virtual drives
        self.__vds = None
    
    def initialize(self):
        storcli = subprocess.Popen(['which', 'storcli'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout = storcli.communicate()[0]
        if storcli.returncode != 0:
            logging.error("# Error: command 'which storcli' returned an error code.")
            raise RuntimeError, "which storcli command error"
        else:
            self.__path = stdout.rstrip("\n");

    def getVDs(self): return self.__vds

    def checkVDs(self):
        process1 = subprocess.Popen([self.__path, '/call', '/vall', 'show'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process2 = subprocess.Popen(['awk', 'BEGIN{RS=ORS=\"\\n\\n\";FS=OFS=\"\\n\\n\"}/TYPE /'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=process1.stdout)
        process3 = subprocess.Popen(['awk', '/^[0-9]/{print $1}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=process2.stdout)
        process1.stdout.close()
        process2.stdout.close()
        (stdout, stderr) = process3.communicate()
        if stderr != '':
            logging.error("storcli encountered an error: " + stderr)
            raise RuntimeError, "storcli command error"
        else:
            self.__vds = stdout.splitlines()

