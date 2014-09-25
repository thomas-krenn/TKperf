'''
Created on Sep 24, 2014

@author: gschoenb
'''

from abc import ABCMeta, abstractmethod
import subprocess
import logging
from string import split
import re
from os import lstat
from stat import S_ISBLK

class RAIDtec(object):
    '''
    Representing a RAID technology, used from the OS.
    '''
    __metaclass__ = ABCMeta

    def __init__(self, path, level, devices):
        ## Path of the RAID utils
        self.__util = None
        ## Path of the raid device
        self.__path = path
        ## RAID level
        self.__level = level
        ## List of devices
        self.__devices = devices
        ## List of current RAID virtual drives
        self.__vds = None
        ## List of block Devices in OS
        self.__blockdevs = None

    def getUtil(self): return self.__util
    def getDevPath(self): return self.__path
    def getLevel(self): return self.__level
    def getDevices(self): return self.__devices
    def getVDs(self): return self.__vds
    def getBlockDevs(self): return self.__blockdevs

    def setUtil(self, u):
        self.__util = u
    def setVDs(self, v):
        self.__vds = v

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

    @abstractmethod
    def initialize(self):
        ''' Initialize the specific RAID technology. '''
    @abstractmethod
    def checkRaidPath(self):
        ''' Checks if the virtual drive exists. '''
    @abstractmethod
    def checkVDs(self):
        ''' Check which virtual drives are configured. '''
    @abstractmethod
    def createVD(self):
        ''' Create a virtual drive. '''
    @abstractmethod
    def deleteVD(self):
        ''' Delete a virtual drive. '''
    @abstractmethod
    def isReady(self):
        ''' Check if a virtual drive is ready. '''

class Mdadm(RAIDtec):
    '''
    Represents a linux software RAID technology.
    '''

    def initialize(self):
        '''
        Checks for mdadm and sets the util path.
        '''
        mdadm = subprocess.Popen(['which', 'mdadm'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout = mdadm.communicate()[0]
        if mdadm.returncode != 0:
            logging.error("# Error: command 'which mdadm' returned an error code.")
            raise RuntimeError, "which mdadm command error"
        else:
            self.setUtil(stdout.rstrip("\n"))

    def checkRaidPath(self):
        logging.error("# Checking for device "+self.getDevPath())
        try:
            mode = lstat(self.getDevPath()).st_mode
        except OSError:
            return False
        else:
            return S_ISBLK(mode)

    def checkVDs(self):
        pass

    def createVD(self):
        match = re.search('^\/dev\/(.*)$', self.getDevPath())
        vdNum = match.group(1)
        self.getDevPath()
        args = [self.getUtil(), "--create", vdNum, "--quiet", "--metadata=default", str("--level=" + str(self.getLevel())), str("--raid-devices=" + str(len(self.getDevices())))]
        for dev in self.getDevices():
            args.append(dev)
        logging.info("# Creating raid device "+self.getDevPath())
        logging.info("# Command line: "+subprocess.list2cmdline(args))
        ##Execute the commandline
        mdadm = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stderr = mdadm.communicate()[1]
        if stderr != '':
            logging.error("mdadm encountered an error: " + stderr)
            raise RuntimeError, "mdadm command error"

    def deleteVD(self):
        logging.info("# Deleting raid device "+self.getDevPath())
        mdadm = subprocess.Popen([self.getUtil(), "--stop", self.getDevPath()], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stderr = mdadm.communicate()[1]
        if mdadm.returncode != 0:
            logging.error("mdadm encountered an error: " + stderr)
            raise RuntimeError, "mdadm command error"
        # Reset all devices in the Raid
        # If the raid device was overwritten completely before (precondition), zero-superblock can fail
        for dev in self.getDevices():
            logging.info("# Deleting superblock for device "+dev)
            mdadm = subprocess.Popen([self.getUtil(), "--zero-superblock", dev], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            mdadm.communicate()

    def isReady(self):
        logging.info("# Checking if raid device "+self.getDevPath()+" is ready...")
        process = subprocess.Popen(["cat", "/proc/mdstat"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (stdout, stderr) = process.communicate()
        if stderr != '':
            logging.error("cat mdstat encountered an error: " + stderr)
            raise RuntimeError, "cat mdstat command error"
        else:
            # Remove the Personalities line
            stdout = stdout.partition("\n")[2]
            # Split in single devices
            mds = stdout.split("\n\n")
            # Search devices for our device
            match = re.search('^/dev/(.*)$', self.getDevPath())
            mdName = match.group(1)
            for md in mds:
                if md.startswith(mdName):
                    # Check if a task is running)
                    if md.find("finish") != -1:
                        return False
                    else:
                        return True

class Storcli(RAIDtec):
    '''
    Represents a storcli based RAID technology.
    '''

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
            self.setUtil(stdout.rstrip("\n"))

    def checkRaidPath(self):
        match = re.search('^[0-9]\/([0-9]+)',self.getDevPath())
        vdNum = match.group(1)
        storcli = subprocess.Popen([self.getUtil(),'/c0/v'+vdNum, 'show', 'all'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdout,stderr) = storcli.communicate()
        if storcli.returncode != 0:
            logging.error("storcli encountered an error: " + stderr)
            raise RuntimeError, "storcli command error"
        else:
            for line in stdout.splitlines():
                match = re.search('^Description = (\w+)$',line)
                if match.group(1) == 'No VDs have been configured':
                    return False
                else:
                    return True
                match = re.search('^Status = (\w+)$',line)
                if match.group(1) == 'Failure':
                    return False
                else:
                    return True

    def checkVDs(self):
        '''
        Checks which virtual drives are configured.
        Sets VDs as a list of virtual drives.
        '''
        process1 = subprocess.Popen([self.getUtil(), '/call', '/vall', 'show'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process2 = subprocess.Popen(['awk', 'BEGIN{RS=ORS=\"\\n\\n\";FS=OFS=\"\\n\\n\"}/TYPE /'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=process1.stdout)
        process3 = subprocess.Popen(['awk', '/^[0-9]/{print $1}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=process2.stdout)
        process1.stdout.close()
        process2.stdout.close()
        (stdout, stderr) = process3.communicate()
        if process3.returncode != 0:
            logging.error("storcli encountered an error: " + stderr)
            raise RuntimeError, "storcli command error"
        else:
            self.setVDs(stdout.splitlines())

    def createVD(self):
        '''
        Creates a virtual drive from a given raid level and a list of
        enclosure:drive IDs.
        @param level The desired raid level
        @param devices The list of raid devices as strings, e.g. ['e252:1','e252:2']
        ''' 
        encid = split(self.getDevices()[0], ":")[0]
        args = [self.getUtil(), '/c0', 'add', 'vd', str('type=r' + str(self.getLevel))]
        devicearg = "drives=" + encid + ":"
        for dev in self.getDevices():
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

    def deleteVD(self):
        match = re.search('^[0-9]\/([0-9]+)',self.getDevPath())
        vdNum = match.group(1)
        storcli = subprocess.Popen([self.getUtil(),'/c0/v'+vdNum, 'del', 'force'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stderr = storcli.communicate()[1]
        if storcli.returncode != 0:
            logging.error("storcli encountered an error: " + stderr)
            raise RuntimeError, "storcli command error"
        else:
            logging.info("# Deleting raid device VD "+vdNum)

    def isReady(self):
        '''
        Checks if a virtual device is ready, i.e. if no rebuild on any PDs is running
        and if not initializarion process is going on.
        @param vd ID of the VD, e.g. 0/0.
        @param devices Array of enclosusre:PD IDs, e.g. ['e252:1','e252:2']
        @return True if VD is ready, False if not
        '''
        ready = None
        storcli = subprocess.Popen([self.getUtil(),'/c0/eall/sall', 'show', 'rebuild'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdout, stderr) = storcli.communicate()
        if storcli.returncode != 0:
            logging.error("storcli encountered an error: " + stderr)
            raise RuntimeError, "storcli command error"
        else:
            for line in stdout.splitlines():
                match = re.search('^\/c0\/e([0-9]+\/s[0-9]+).*$',line)
                if match != None:
                    for d in self.getDevices():
                        d = d.replace(':','/s')
                        if d == match.group(1):
                            logging.info(line)
                            status = re.search('Not in progress',line)
                            if status != None:
                                ready = True
                            else:
                                ready = False
        match = re.search('^[0-9]\/([0-9]+)',self.getDevPath())
        vdNum = match.group(1)
        storcli = subprocess.Popen([self.getUtil(),'/call', '/v'+vdNum, 'show', 'init'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
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