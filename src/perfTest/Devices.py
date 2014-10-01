'''
Created on Aug 6, 2014

@author: gschoenb
'''

from abc import ABCMeta, abstractmethod
import logging
import subprocess
import json
from lxml import etree
from time import sleep

from fio.FioJob import FioJob
from system.OS import Storcli
from system.OS import Mdadm


class Device(object):
    '''
    Representing the tested device.
    '''
    __metaclass__ = ABCMeta

    def __init__(self, devtype, path, devname, vendor=None, intfce=None):
        '''
        Constructor
        @param devtype Type of the device, ssd, hdd etc.
        @param path Path of the device, e.g. /dev/sda
        @param devname Name of the device to test, e.g. intel320
        @param vendor A specific vendor if desired
        @param intfce A specific device interface if desired
        '''
        ## The type of the device
        self.__devtype = devtype
        ## The path name of the device
        self.__path = path
        ## The common name of the device
        self.__devame = devname
        ## A specific vendor for the device
        self.__vendor = vendor
        ## A specific interface for the device, e.g. sas
        self.__intfce = intfce
        ## Device specific information for reporting
        self.__devinfo = None
        ## A list of special features for the device
        self.__featureMatrix = None
        ## The size of the device in bytes
        self.__devsizeb = None
        ## The size of the device in kilo bytes
        self.__devsizekb = None
        ## Check if the device is mounted
        self.__devismounted = None
        ## Check if a valid partition is used
        self.__devisavailable = None

    def getDevType(self): return self.__devtype
    def getDevPath(self): return self.__path
    def getDevName(self): return self.__devame
    def getDevSizeKB(self): return self.__devsizekb
    def getDevSizeB(self): return self.__devsizeb
    def getVendor(self): return self.__vendor
    def getIntfce(self): return self.__intfce
    def getDevInfo(self): return self.__devinfo
    def getFeatureMatrix(self): return self.__featureMatrix

    def setDevInfo(self,dInfo):
        self.__devinfo = dInfo
    def setFeatureMatrix(self,fm):
        self.__featureMatrix = fm
    def setDevSizeB(self,ds):
        self.__devsizeb = ds
    def setDevSizeKB(self,ds):
        self.__devsizekb = ds
    def setDevIsAvailable(self,ia):
        self.__devisavailable = ia
    def setDevIsMounted(self,im):
        self.__devismounted = im
    def setInterface(self,intf):
        self.__intfce = intf

    def initialize(self):
        '''
        Run size and devinfo methods for the current device.
        '''
        try:
            self.__devsizeb = self.calcDevSizeB()
            self.__devsizekb = self.calcDevSizeKB()
            self.__devismounted = self.checkDevIsMounted()
            self.__devisavailable = self.checkDevIsAvbl()
            self.readDevInfo()
        except RuntimeError:
            logging.error("# Could not fetch initial information for " + self.__path)
            raise

    def isInitialized(self):
        '''
        Checks if the device info was read correctly.
        @return True if yes, False if not.
        '''
        if self.__devinfo != None:
            return True
        else:
            return False
    
    def isMounted(self): return self.__devismounted
    def isAvailable(self): return self.__devisavailable

    def calcDevSizeKB(self):
        '''
        Get the device size in KByte.
        The function calls 'blockdev' to determine device sector size
        and sector count.
        @return Size on success
        @exception RuntimeError if blockdev fails
        '''
        out = subprocess.Popen(['blockdev','--getss',self.__path],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdout,stderr) = out.communicate()
        if stderr != '':
            logging.error("blockdev --getss encountered an error: " + stderr)
            raise RuntimeError, "blockdev error"
        else:
            sectorSize = int(stdout)
            out = subprocess.Popen(['blockdev','--getsz',self.__path],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            (stdout,stderr) = out.communicate()
            if stderr != '':
                logging.error("blockdev --getsz encountered an error: " + stderr)
                raise RuntimeError, "blockdev error"
            else:
                sectorCount = long(stdout)
                if ((sectorCount * sectorSize) % 1024) != 0:
                        logging.error("blockdev sector count cannot be divided by 1024")
                        raise RuntimeError, "blockdev error"
                devSzKB = (sectorCount * sectorSize) / 1024
                logging.info("#Device" + self.__path + " sector count: " + str(sectorCount))
                logging.info("#Device" + self.__path + " sector size: " + str(sectorSize))
                logging.info("#Device" + self.__path + " size in KB: " + str(devSzKB))
                return devSzKB

    def calcDevSizeB(self):
        '''
        Get the device size in Byte.
        The function calls 'blockdev' to determine device sector size
        and sector count.
        @return Size on success
        @exception RuntimeError if blockdev fails
        '''
        out = subprocess.Popen(['blockdev','--getsize64',self.__path],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdout,stderr) = out.communicate()
        if stderr != '':
            logging.error("blockdev --getss encountered an error: " + stderr)
            raise RuntimeError, "blockdev error"
        else:
            byteSize = long(stdout)
            if byteSize == 0:
                logging.error("blockdev --getsize64 returned zero.")
                raise RuntimeError, "blockdev error"
            return byteSize

    def checkDevIsMounted(self):
        '''
        Check if the given device is mounted. As we work as
        super user it is slightly dangerous to overwrite
        a mounted partition.
        @return True if device is mounted, False if not
        @exception RuntimeError if mount command fails
        '''
        out = subprocess.Popen(['mount','-l'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdout,stderr) = out.communicate()
        if stderr != '':
            logging.error("mount -l encountered an error: " + stderr)
            raise RuntimeError, "mount command error"
        else:
            for line in stdout.split('\n'):
                if line.find(self.__path) > -1:
                    logging.info("#"+line)
                    return True
            return False

    def checkDevIsAvbl(self):
        '''
        Check if the given device is a valid partition.
        @return True if yes, False if not.
        '''
        out = subprocess.Popen(['cat','/proc/partitions'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdout,stderr) = out.communicate()
        if stderr != '':
            logging.error("cat /proc/partitions encountered an error: " + stderr)
            raise RuntimeError, "cat /proc/partitions command error"
        else:
            for line in stdout.split('\n'):
                if line.find(self.__path[5:]) > -1:
                    logging.info("#"+line)
                    return True
            return False

    def readDevInfoFile(self,fd):
        '''
        Reads the device description from a file. This is necessary if
        the device information cannot be fetched via hdparm.
        @param fd The path to the description file, has to be opened already.
        '''
        self.__devinfo = fd.read()
        logging.info("# Reading device info from dsc file")
        logging.info("# Testing device: " + self.__devinfo)
        fd.close()

    def readFeatureFile(self,fd):
        '''
        Reads the special feature matrix from file.
        @param fd The path to the feature matrix file, has to be opened already.
        '''
        self.__featureMatrix = fd.read()
        logging.info("# Reading feature matrix from file")
        logging.info("# Feature Matrix: " + self.__featureMatrix)
        fd.close()

    @abstractmethod
    def secureErase(self):
        ''' Erase a device. '''
    @abstractmethod
    def precondition(self):
        ''' Carry out workload independent preconditioning. '''

    @abstractmethod
    def readDevInfo(self):
        '''
        Per default read the device information via hdparm -I. If an error occured
        the method returns False and an error message is logged to use a description
        file is.
        @return True if the device info was set, False if not.
        '''
        # The device info has already been set
        if self.__devinfo != None:
            return True
        # If no interface is specified, use hdparm
        if self.getIntfce() == None:
            out = subprocess.Popen(['hdparm','-I',self.__path],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            (stdout,stderr) = out.communicate()
            if stderr != '':
                logging.error("hdparm -I encountered an error: " + stderr)
                logging.error("Please use a description file to set device information!")
                return False
            else:
                self.__devinfo = ""
                for line in stdout.split('\n'):
                    if line.find("questionable sense data") > -1 or line.find("bad/missing sense data") > -1:
                        logging.error("hdparm sense data may be incorrect!")
                        logging.error("Please use a description file to set device information!")
                        return False
                    if line.find("Model Number") > -1:
                        self.__devinfo += line + '\n'
                    if line.find("Serial Number") > -1:
                        self.__devinfo += line +'\n'
                    if line.find("Firmware Revision") > -1:
                        self.__devinfo += line + '\n'
                    if line.find("Media Serial Num") > -1:
                        self.__devinfo += line + '\n'
                    if line.find("Media Manufacturer") > -1:
                        self.__devinfo += line + '\n'
                    if line.find("device size with M = 1000*1000") > -1:
                        self.__devinfo += line + '\n'
                #Check for write caching state
                stdout = ''
                stderr = ''
                out = subprocess.Popen(['hdparm','-W',self.__path],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                (stdout,stderr) = out.communicate()
                if stderr != '':
                    logging.error("# Error: hdparm -W encountered an error: " + stderr)
                    logging.error("# Please use a description file to set device information!")
                    return False
                for line in stdout.split('\n'):
                    if line.find("write-caching") > -1:
                        line = line.lstrip(' ')
                        line = '\t' + line
                        self.__devinfo += line + '\n'
                logging.info("# Testing device: " + self.__devinfo)
        # For sas devices use sg utils
        elif self.getIntfce() == 'sas':
            out = subprocess.Popen(['sginfo', '-a', self.__path],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            (stdout,stderr) = out.communicate()
            if out.returncode != 0:
                logging.error("sginfo -a encountered an error: " + stderr)
                return False
            else:
                self.__devinfo = ""
                for line in stdout.split('\n'):
                    if line.find("Vendor") > -1:
                        self.__devinfo += line + '\n'
                    if line.find("Product") > -1:
                        self.__devinfo += line + '\n'
                    if line.find("Revision Level") > -1:
                        self.__devinfo += line + '\n'
                    if line.find("Serial Number") > -1:
                        self.__devinfo += line + '\n'
                    if line.find("Write Cache Enabled") > -1:
                        self.__devinfo += line + '\n'
                out = subprocess.Popen(['sg_readcap', self.__path],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                (stdout,stderr) = out.communicate()
                if out.returncode != 0:
                    logging.error("sg_readcap encountered an error: " + stderr)
                    return False
                else:
                    for line in stdout.split('\n'):
                        if line.find("Device size") > -1:
                            self.__devinfo += line + '\n'
        return True

    def toXml(self,root):
        '''
        Get the Xml representation of the device.
        @param r The xml root tag to append the new elements to
        ''' 
        data = json.dumps(self.__devinfo)
        e = etree.SubElement(root,'devinfo')
        e.text = data
        if self.__featureMatrix != None:
            data = json.dumps(self.__featureMatrix)
            e = etree.SubElement(root,'featmatrix')
            e.text = data
    
    def fromXml(self,root):
        '''
        Loads the information about a device from XML.
        @param root The given element containing the information about
        the object to be initialized.
        '''
        self.__devinfo = json.loads(root.findtext('devinfo'))
        if(root.findtext('featmatrix')):
            self.__devinfo = json.loads(root.findtext('featmatrix'))
        logging.info("# Loading device info from xml")

class SSD(Device):
    '''
    Representing a SSD.
    '''
    ## Number of rounds to carry out workload independent preconditioning.
    wlIndPrecRnds = 2
    
    def readDevInfo(self):
        super(SSD, self).readDevInfo()

    def secureErase(self):
        '''
        Carries out a secure erase via hdparm or sg_format for the given device.
        sg_format is used only for SAS devices
        @return True if device is secure erased, False if not.
        '''
        frozen = True
        security = False
        logging.info("# Starting Secure Erase for device: "+self.getDevPath())
        if self.getIntfce() == None:
            out = subprocess.Popen(['hdparm','-I',self.getDevPath()],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            (stdout,stderr) = out.communicate()
            if stderr != '':
                logging.error("hdparm -I encountered an error: " + stderr)
                raise RuntimeError, "hdparm command error"
            else:
                for line in stdout.split('\n'):
                    if line.find("frozen") > -1:
                        if line.find("not") > -1:
                            frozen = False
                            logging.info("# Not in frozen state")
                if frozen:
                    logging.error("# Device still in frozen state")
                    raise RuntimeError, "frozen state error"
                if not frozen:
                    out = subprocess.Popen(['hdparm', '--user-master','u',
                                            '--security-set-pass','pwd',self.getDevPath()],
                                           stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                    stdout,stderr = out.communicate()
                    if out.returncode != 0:
                        logging.error("# Error: command 'hdparm --user-master u --security-set-pass pwd returned an error code.")
                        logging.error(stderr)
                        raise RuntimeError, "hdparm command error"
                    else:
                        out = subprocess.Popen(['hdparm','-I',self.getDevPath()],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                        (stdout,stderr) = out.communicate()
                        if stderr != '':
                            logging.error("hdparm -I encountered an error: " + stderr)
                            raise RuntimeError, "hdparm command error"
                        else:
                            lines = stdout.split('\n')
                            for i,line in enumerate(lines):
                                if line.find("Master password") > -1:
                                    if lines[i+2].find("not") == -1 and lines[i+2].find("enabled") > -1:
                                        security = True
                                        logging.info("# Successfully enabled security for hdparm")
                                        break
                                    else:
                                        logging.info("# Security NOT enabled for hdparm")
                                        raise RuntimeError, "hdparm command error"
                            if security:
                                out = subprocess.Popen(['hdparm', '--user-master','u',
                                                        '--security-erase','pwd',self.getDevPath()],
                                                       stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                                stdout,stderr = out.communicate()
                                if out.returncode != 0:
                                    logging.error("# Error: command 'hdparm --user-master u --security-erase pwd returned an error code.")
                                    logging.error(stderr)
                                    raise RuntimeError, "hdparm command error"
                                else:
                                    logging.info("# Successfully carried out secure erase for "+self.getDevPath())
                                    #Check if security is diasbled again
                                    out = subprocess.Popen(['hdparm','-I',self.getDevPath()],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                                    (stdout,stderr) = out.communicate()
                                    if stderr != '':
                                        logging.error("hdparm -I encountered an error: " + stderr)
                                        raise RuntimeError, "hdparm command error"
                                    else:
                                        lines = stdout.split('\n')
                                        for i,line in enumerate(lines):
                                            if line.find("Master password") > -1:
                                                if lines[i+2].find("not") > -1 and lines[i+2].find("enabled") > -1:
                                                    security = False
                                                    logging.info("#Successfully deactivated security for hdparm.")
                                                    return True
                                                else:
                                                    #Try to disable security manually
                                                    logging.info("# Security still enabled for hdparm, therefore calling disable.")
                                                    out = subprocess.Popen(['hdparm', '--user-master','u',
                                                        '--security-disable','pwd',self.getDevPath()],
                                                       stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                                                    stdout,stderr = out.communicate()
                                                    if out.returncode != 0:
                                                        logging.error("# Error: command 'hdparm --user-master u --security-disable pwd returned an error code.")
                                                        logging.error(stderr)
                                                        raise RuntimeError, "hdparm command error"
                                                    else:
                                                        logging.info("# Successfully deactivated security for hdparm.")
                                                        return True
        elif self.getIntfce() == 'sas':
            logging.info("# Using sg_format as secure erase for SAS device.")
            out = subprocess.Popen(['sg_format', '--format', self.__path],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            (stdout,stderr) = out.communicate()
            if out.returncode != 0:
                logging.error("# Error: sg_format --format encountered an error: " + stderr)
                return False
            else:
                logging.info("# sg_format: " + stdout)
                return True

    def precondition(self,nj=1,iod=1):
        ''' 
        Workload independent preconditioning for SSDs.
        Write two times the device with streaming I/O.
        @return True if precontioning succeded
        @exception RuntimeError if fio command fails
        '''
        job = FioJob()
        job.initialize()
        job.addKVArg("filename",self.getDevPath())
        job.addKVArg("bs","128k")
        job.addKVArg("rw","write")
        job.addKVArg("direct","1")
        job.addSglArg("minimal")
        job.addKVArg("numjobs",str(nj))
        job.addKVArg("ioengine","libaio")
        job.addKVArg("iodepth",str(iod))
        job.addSglArg("group_reporting")
        job.addSglArg('refill_buffers')

        for i in range(SSD.wlIndPrecRnds):
            logging.info("# Starting preconditioning round "+str(i))
            job.addKVArg("name", self.getDevName() + '-run' + str(i))
            call,out = job.start()
            if call == False:
                logging.error("# Could not carry out workload independent preconditioning")
                raise RuntimeError, "precondition error, fio command error"
            else:
                logging.info(out)
        logging.info("# Finished workload independent preconditioning")
        return True

class HDD(Device):
    '''
    Representing a HDD.
    '''
    def readDevInfo(self):
        super(HDD, self).readDevInfo()

    def secureErase(self):
        return True

    def precondition(self):
        return True

class RAID(Device):
    '''
    Representing a RAID device.
    '''
    raidLevels = [0, 1, 5, 6, 10]

    def __init__(self, devtype, path, devname, config=None, vendor=None):
        '''
        Constructor
        @param config The config file describing the RAID set
        '''
        super(RAID, self).__init__(devtype, path, devname, vendor)
        ## Type of raid, read from config, e.g. sw_mdadm, hw_lsi
        self.__type = None
        ## The config file describing the RAID device
        self.__config = config
        ## The used RAID technology, linux sw RAID, lsi hw RAID
        self.__raidTec = None

    def getType(self): return self.__type
    def getConfig(self): return self.__config
    def setConfig(self,cfg):
        self.__config = cfg

    def initialize(self):
        '''
        Run size and devinfo methods for the current device.
        If a raid doesn't exist, create it.
        '''
        try:
            # Init from config if not done yet
            if self.__raidTec == None:
                self.initRaidFromConf(self.__config)
            # Create raid if it doesn't exist
            if not self.__raidTec.checkRaidPath():
                self.__raidTec.createVD()
            self.setDevSizeB(self.calcDevSizeB())
            self.setDevSizeKB(self.calcDevSizeKB())
            self.setDevIsMounted(self.checkDevIsMounted())
            self.setDevIsAvailable(self.checkDevIsAvbl())
            self.readDevInfo()
        except RuntimeError:
            logging.error("# Could not fetch initial information for " + self.getDevPath())
            raise

    def initRaidFromConf(self,fd):
        '''
        Initializes a RAID device from a json config file.
        @param fd An already opened file descriptor for the config file.
        '''
        decoded = json.load(fd)
        if "devices" in decoded and "raidlevel" in decoded and "type" in decoded:
            self.__type = decoded["type"]
        if self.__type == "sw_mdadm":
            self.__raidTec = Mdadm(self.getDevPath(), decoded["raidlevel"], decoded["devices"])
        if self.__type == "hw_lsi":
            self.__raidTec = Storcli(self.getDevPath(), decoded["raidlevel"], decoded["devices"])
        self.__raidTec.initialize()

    def readDevInfo(self):
        #FIXME Add correct info about raid setup
        devInfo = ""
        devInfo += self.__type + "\n"
        devInfo += ', '.join(self.__raidTec.getDevices())
        devInfo += str(self.__raidTec.getLevel()) + "\n"
        self.setDevInfo(devInfo)

    def createRaid(self):
        # Check if there is already a device, if yes delete it
        if self.__raidTec.checkRaidPath() == True:
            logging.info("# Found raid device "+self.getDevPath()+", deleting it!")
            self.__raidTec.deleteVD()
        # Create the raid device
        self.__raidTec.createVD()
        while not self.__raidTec.isReady():
            sleep(30)

    def secureErase(self):
        '''
        Carries out the secure erase for a RAID device.
        '''
        if self.getType() == 'sw_mdadm':
            import multiprocessing
            m = multiprocessing.Manager()
            exc = m.Queue()
            ps = []
            for d in self.__raidTec.getDevices():
                p = multiprocessing.Process(target=self.operator,args=(d,'erase',None, None, exc))
                ps.append(p)
                p.start()
            for p in ps:
                p.join()
            if exc.empty():
                pass
            else:
                logging.error("# Error: Could not secure erase " + self.getDevPath())
                raise RuntimeError, "secure erase error"
        if self.getType() == 'hw_lsi':
            logging.info("# Secure Erase not implemented on LSI controllers, skipping...")
            return
        # After secure erase create the raid device
        logging.info("# Creating raid device "+self.getDevPath()+" after secure erase!")
        self.createRaid()

    def precondition(self,nj=1,iod=1):
        '''
        Carries out the preconditioning for a RAID device.
        '''
        if self.getType() == 'sw_mdadm':
            import multiprocessing
            m = multiprocessing.Manager()
            exc = m.Queue()
            ps = []
            for d in self.__raidTec.getDevices():
                p = multiprocessing.Process(target=self.operator,args=(d,'condition',nj, iod, exc))
                ps.append(p)
                p.start()
            for p in ps:
                p.join()
            if exc.empty():
                pass
            else:
                logging.error("# Error: Could not precondition " + self.getDevPath())
                raise RuntimeError, "precondition error"
        if self.getType() == 'hw_lsi':
            tmpSSD = SSD('ssd', self.getDevPath(), self.getDevName())
            tmpSSD.precondition(nj, iod)
        # After preconditioning create the raid device
        logging.info("# Creating raid device "+self.getDevPath()+" after workload independet preconditioning!")
        self.createRaid()

    def operator(self, path, op, nj, iod, exc):
        try:
            tmpSSD = SSD('ssd', path, self.getDevName())
            if op == 'erase':
                tmpSSD.secureErase()
            if op == 'condition':
                tmpSSD.precondition(nj, iod)
        except RuntimeError:
            exc.put('Error')