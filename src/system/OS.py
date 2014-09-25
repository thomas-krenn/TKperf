'''
Created on Sep 24, 2014

@author: gschoenb
'''

import subprocess
import logging
from string import split
import re

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
        self.__storcli = None
        ## List of current virtual drives
        self.__vds = None
    
    def initialize(self):
        '''
        Checks for the storcli executable and sets the path of storcli.
        '''
        storcli = subprocess.Popen(['which', 'storcli'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout = storcli.communicate()[0]
        if storcli.returncode != 0:
            storcli = subprocess.Popen(['which', 'storcli64'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            stdout = storcli.communicate()[0]
        if storcli.returncode != 0:
            logging.error("# Error: command 'which storcli' returned an error code.")
            raise RuntimeError, "which storcli command error"
        else:
            self.__storcli = stdout.rstrip("\n");

    def getVDs(self): return self.__vds

    def checkVDs(self):
        '''
        Checks which virtual drives are configured.
        Sets self.__vds as a list of virtual drives.
        '''
        process1 = subprocess.Popen([self.__storcli, '/call', '/vall', 'show'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process2 = subprocess.Popen(['awk', 'BEGIN{RS=ORS=\"\\n\\n\";FS=OFS=\"\\n\\n\"}/TYPE /'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=process1.stdout)
        process3 = subprocess.Popen(['awk', '/^[0-9]/{print $1}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=process2.stdout)
        process1.stdout.close()
        process2.stdout.close()
        (stdout, stderr) = process3.communicate()
        if process3.returncode != 0:
            logging.error("storcli encountered an error: " + stderr)
            raise RuntimeError, "storcli command error"
        else:
            self.__vds = stdout.splitlines()

    def createVD(self, level, devices):
        '''
        Creates a virtual drive from a given raid level and a list of
        enclosure:drive IDs.
        @param level The desired raid level
        @param devices The list of raid devices as strings, e.g. ['e252:1','e252:2']
        ''' 
        encid = split(devices[0], ":")[0]
        args = [self.__storcli, '/c0', 'add', 'vd', str('type=r' + str(level))]
        devicearg = "drives=" + encid + ":"
        for dev in devices:
            devicearg += split(dev, ":")[1] + ","
        args.append(devicearg.rstrip(","))
        logging.info("# Creating raid device with storcli")
        logging.info("# Command line: "+subprocess.list2cmdline(args))
        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (stdout,stderr) = process.communicate()
        if process.returncode != 0:
            logging.error("storcli encountered an error: " + stderr)
            raise RuntimeError, "storcli command error"
        else:
            logging.info(stdout)

    def deleteVD(self, vd):
        '''
        Deletes a virtual drive.
        @param vd The ID of the virtual drive, e.g. 0/0.
        '''
        match = re.search('^[0-9]\/([0-9]+)',vd)
        vdNum = match.group(1)
        storcli = subprocess.Popen([self.__storcli,'/c0/v'+vdNum, 'del', 'force'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stderr = storcli.communicate()[1]
        if storcli.returncode != 0:
            logging.error("storcli encountered an error: " + stderr)
            raise RuntimeError, "storcli command error"
        else:
            logging.info("# Deleting raid device VD "+vdNum)

    def isReady(self, vd, devices):
        '''
        Checks if a virtual device is ready, i.e. if no rebuild on any PDs is running
        and if not initializarion process is going on.
        @param vd ID of the VD, e.g. 0/0.
        @param devices Array of enclosusre:PD IDs, e.g. ['e252:1','e252:2']
        @return True if VD is ready, False if not
        '''
        ready = None
        storcli = subprocess.Popen([self.__storcli,'/c0/eall/sall', 'show', 'rebuild'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdout, stderr) = storcli.communicate()
        if storcli.returncode != 0:
            logging.error("storcli encountered an error: " + stderr)
            raise RuntimeError, "storcli command error"
        else:
            for line in stdout.splitlines():
                match = re.search('^\/c0\/e([0-9]+\/s[0-9]+).*$',line)
                if match != None:
                    for d in devices:
                        d = d.replace(':','/s')
                        if d == match.group(1):
                            logging.info(line)
                            status = re.search('Not in progress',line)
                            if status != None:
                                ready = True
                            else:
                                ready = False
        match = re.search('^[0-9]\/([0-9]+)',vd)
        vdNum = match.group(1)
        storcli = subprocess.Popen([self.__storcli,'/call', '/v'+vdNum, 'show', 'init'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdout, stderr) = storcli.communicate()
        if storcli.returncode != 0:
            logging.error("storcli encountered an error: " + stderr)
            raise RuntimeError, "storcli command error"
        else:
            for line in stdout.splitlines():
                match = re.search(vdNum+' INIT',line)
                if match != None:
                    logging.info(line)
                    status = re.search('Not in progress',line)
                    if status != None:
                        ready = True
                    else:
                        ready = False
        return ready