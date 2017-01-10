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
from time import sleep

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
        ## List of block Devices in OS
        self.__blockdevs = None

    def getUtil(self): return self.__util
    def getDevPath(self): return self.__path
    def getLevel(self): return self.__level
    def getDevices(self): return self.__devices
    def getBlockDevs(self): return self.__blockdevs

    def setUtil(self, u):
        self.__util = u

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
            logging.info("# Got the following BDs: ")
            logging.info(self.getBlockDevs())

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
        logging.info("# Checking for device "+self.getDevPath())
        try:
            mode = lstat(self.getDevPath()).st_mode
        except OSError:
            return False
        else:
            return S_ISBLK(mode)

    def checkVDs(self):
        pass

    def createVD(self):
        self.getDevPath()
        args = [self.getUtil(), "--create", self.getDevPath(), "--quiet", "--metadata=default", str("--level=" + str(self.getLevel())), str("--raid-devices=" + str(len(self.getDevices())))]
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
    
#    def __init__(self, path, level, devices, wt=True, nora=True):
    def __init__(self, path, level, devices, readpolicy, writepolicy):
        '''
        Constructor
        '''
        super(Storcli, self).__init__(path, level, devices)
        ## The virtual drive of the raid controller
        self.__vd = None
        ## List of current RAID virtual drives
        self.__vds = None
        ## Read policy of the virtual drive
        self.__readpolicy = readpolicy
        ## Write policy of the virtual drive
        self.__writepolicy = writepolicy

    def getVD(self): return self.__vd
    def getVDs(self): return self.__vds
    def getREADPOLICY(self): return self.__readpolicy
    def getWRITEPOLICY(self): return self.__writepolicy
    def setVD(self,v): self.__vd = v
    def setVDs(self, v): self.__vds = v

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
        '''
        Checks if the virtual drive of the RAID controller is available.
        @return True if yes, False if not
        '''
        if self.getVD() != None:
            logging.info("# Checking for virtual drive "+self.getVD())
            match = re.search('^[0-9]\/([0-9]+)',self.getVD())
            vdNum = match.group(1)
            storcli = subprocess.Popen([self.getUtil(),'/c0/v'+vdNum, 'show', 'all'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            (stdout,stderr) = storcli.communicate()
            if storcli.returncode != 0:
                logging.error("storcli encountered an error: " + stderr)
                raise RuntimeError, "storcli command error"
            else:
                vdCheck = None
                for line in stdout.splitlines():
                    match = re.search('^Description = (\w+)$',line)
                    if match != None:
                        if match.group(1) == 'No VDs have been configured':
                            vdCheck = False
                        else:
                            vdCheck = True
                    match = re.search('^Status = (\w+)$',line)
                    if match != None:
                        if match.group(1) == 'Failure':
                            vdCheck = False
                        else:
                            vdCheck = True
                return vdCheck
        else:
            logging.info("# VD not set, checking for PDs: ")
            logging.info(self.getDevices())
            storcli = subprocess.Popen([self.getUtil(),'/c0/vall', 'show', 'all'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            (stdout,stderr) = storcli.communicate()
            if storcli.returncode != 0:
                logging.error("storcli encountered an error: " + stderr)
                raise RuntimeError, "storcli command error"
            else:
                vdCheck = None
                for line in stdout.splitlines():
                    match = re.search('^Description = (\w+)$',line)
                    if match != None:
                        if match.group(1) == 'No VDs have been configured':
                            logging.info("# No VDs configured!")
                            vdCheck = False
                            break
                    match = re.search('^PDs for VD ([0-9]+) \:$',line)
                    if match != None:
                        vdNum = match.group(1)
                        PDs = self.getPDsFromVD(vdNum)
                        if set(self.getDevices()) == set(PDs):
                            self.setVD('0/'+vdNum)
                            logging.info("# Set VD as "+self.getVD())
                            vdCheck = True
                            break
                        else:
                            vdCheck = False
                return vdCheck

    def getPDsFromVD(self,vdNum):
        '''
        Returns a list of PDs for a given VD.
        @param vdNum Number of VD to check for
        @return A list of enclosure:device IDs
        '''
        storcli = subprocess.Popen([self.getUtil(),'/c0/v'+vdNum, 'show', 'all'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdout,stderr) = storcli.communicate()
        if storcli.returncode != 0:
            logging.error("storcli encountered an error: " + stderr)
            raise RuntimeError, "storcli command error"
        else:
            PDs = []
            for line in stdout.splitlines():
                match = re.search('^([0-9]+\:[0-9]+).*$',line)
                if match != None:
                    PDs.append(match.group(1))
            logging.info("# Found PDs for VD "+ vdNum +":")
            logging.info(PDs)
            return PDs

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
            logging.info("# Got the following VDs: ")
            logging.info(self.getVDs())

    def createVD(self):
        '''
        Creates a virtual drive from a given raid level and a list of
        enclosure:drive IDs. self.__devices must be a list of raid devices as
        strings, e.g. ['e252:1','e252:2'].
        ''' 
        encid = split(self.getDevices()[0], ":")[0]
        args = [self.getUtil(), '/c0', 'add', 'vd', str('type=r' + str(self.getLevel()))]
        devicearg = "drives=" + encid + ":"
        for dev in self.getDevices():
            devicearg += split(dev, ":")[1] + ","
        args.append(devicearg.rstrip(","))
#        if self.getWT():
#            args.append('wt')
#        if self.getNORA():
#            args.append('nora')
        if self.getREADPOLICY():
            args.append(self.getREADPOLICY())
        if self.getWRITEPOLICY():
            args.append(self.getWRITEPOLICY())
        logging.info("# Creating raid device with storcli")
        logging.info("# Command line: "+subprocess.list2cmdline(args))
        # Fetch VDs before creating the new one
        # Wait for update of lsblk
        sleep(5)
        self.checkVDs()
        self.checkBlockDevs()
        VDsbefore = self.getVDs()
        BDsbefore = self.getBlockDevs()
        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stderr = process.communicate()[1]
        if process.returncode != 0:
            logging.error("storcli encountered an error: " + stderr)
            raise RuntimeError, "storcli command error"
        else:
            # Wait for update of lsblk
            sleep(5)
            # Fetch VDs after creating the new one
            self.checkVDs()
            self.checkBlockDevs()
            VDsafter = self.getVDs()
            BDsafter = self.getBlockDevs()
            vd = [x for x in VDsafter if x not in VDsbefore]
            if self.getVD() != None:
                if vd[0] != self.getVD():
                    logging.info("# The VD changed, the new on is: " + vd[0])
            self.setVD(vd[0])
            bd = [x for x in BDsafter if x not in BDsbefore]
            if (len(bd) != 1) or (('/dev/'+bd[0]) != self.getDevPath()):
                logging.info("Got BD: " + bd[0])
                logging.error("# Error: The new block device doesn't match the tested device path!")
                raise RuntimeError, "New block dev doesn't match tested dev error"
            logging.info("# Created VD " + self.getVD())
            logging.info("# Using block device " + bd[0])

    def deleteVD(self):
        '''
        Deletes a virtual drive, self.__vd must be a string like 0/0 specifying
        the virtual drive.
        '''
        match = re.search('^[0-9]\/([0-9]+)',self.getVD())
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
        match = re.search('^[0-9]\/([0-9]+)',self.getVD())
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
