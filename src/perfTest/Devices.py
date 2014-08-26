'''
Created on Aug 6, 2014

@author: gschoenb
'''

from abc import ABCMeta, abstractmethod
import logging
import subprocess

from fio.FioJob import FioJob

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
        @param devname Name of the device to test, intel320
        @param vendor A specific vendor if desired.
        @param intfce A specific device interface if desired.
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

        try:
            ## The size of the device in bytes
            self.__devsizeb = self.calcDevSizeB()
            ## The size of the device in kilo bytes
            self.__devsizekb = self.calcDevSizeKB()
            ## Check if the device is mounted
            self.__devismounted = self.checkDevIsMounted()
        except RuntimeError:
            logging.error("# Could not fetch initial information for " + self.__path)

    def getDevType(self): return self.__devtype
    def getDevPath(self): return self.__path
    def getDevName(self): return self.__devame
    def getDevSizeKB(self): return self.__devsizekb
    def getDevSizeB(self): return self.__devsizeb
    def getVendor(self): return self.__vendor
    def getIntfce(self): return self.__intfce
    def isMounted(self): return self.__devismounted

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

    @abstractmethod
    def secureErase(self):
        ''' Erase a device. '''
    @abstractmethod
    def precondition(self):
        ''' Carry out workload independent preconditioning. '''

class SSD(Device):
    '''
    Representing a SSD.
    '''
    ## Number of rounds to carry out workload independent preconditioning.
    wlIndPrecRnds = 2
    
    def secureErase(self):
        #TODO
        return True

    def precondition(self,nj,iod):
        ''' 
        Workload independent preconditioning for SSDs.
        Write two times the device with streaming I/O.
        @return True if precontioning succeded
        @exception RuntimeError if fio command fails
        '''
        job = FioJob()
        job.addKVArg("filename",self.getDevPath())
        job.addKVArg("bs","128k")
        job.addKVArg("rw","write")
        job.addKVArg("direct","1")
        job.addKVArg("minimal","1")
        job.addKVArg("numjobs",str(nj))
        job.addKVArg("ioengine","libaio")
        job.addKVArg("iodepth",str(iod))
        job.addSglArg("group_reporting")
        job.addSglArg('refill_buffers')

        for i in range(SSD.wlIndPrecRnds):
            logging.info("# Starting preconditioning round "+str(i))
            job.addKVArg("name", self.getDevType() + '-run' + str(i))
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
    def secureErase(self):
        return True