'''
Created on 27.06.2012

@author: gschoenb
@version: 1.0
'''
__author__ = 'Georg Schoenberger'
__version__ = '1.0'


import argparse
import logging

from fio.FioJob import FioJob
from perfTest.DeviceTest import DeviceTest
from perfTest.HddTest import TPTest
from perfTest.PerfTest import SsdPerfTest

if __name__ == '__main__':
    vTest = FioJob()
    fioVersion = vTest.__str__()#Fetch the fio version
    
    parser = argparse.ArgumentParser()
    
    parser.add_argument("mode", help="specify the test mode for the device", choices=["hdd","ssd"])
    parser.add_argument("testname",help="name of the fio job, corresponds to the result output file")
    parser.add_argument("filename",help="data file or device name to run fio test on")
    
    parser.add_argument("-v","--version", help="get the version information", action='version',version=fioVersion)
    parser.add_argument("-d","--debug", help="get detailed debug information",action ='store_true')
    parser.add_argument("-q","--quiet", help="turn off logging of info messages",action ='store_true')
    parser.add_argument("-nj","--numjobs",help="specify number of jobs for fio",type=int)
    parser.add_argument("-iod","--iodepth",help="specify iodepth for libaio used by fio",type=int)
    parser.add_argument("-xml","--fromxml",help="don't run tests but load test objects from xml file",
                        action='store_true')
    parser.add_argument("-rfb","--refill_buffers",help="use Fio's refill buffers option to circumvent any compression of devices",
                        action='store_true')
    parser.add_argument("-dsc","--desc_file",help="use a description file for the tested device if hdparm doesn't work correctly",
                        type=argparse.FileType('r'))
    parser.add_argument("-ft","--force_test",help="skip checks if the used device is mounted, don't print warnings and force starting the test",
                        action='store_true')
  
    args = parser.parse_args()
    if args.debug == True:
        logging.basicConfig(filename=args.testname+'.log',level=logging.DEBUG)
    if args.quiet == True:
        logging.basicConfig(filename=args.testname+'.log',level=logging.WARNING)
    else:
        logging.basicConfig(filename=args.testname+'.log',level=logging.INFO)
    
    #Don't print a warning if force is given or loading from xml
    if args.force_test == True or args.fromxml != True:
        toTest = DeviceTest(args.testname,args.filename)
        if toTest.checkDevIsMounted() == True:
            print "!!!WARNING!!!"
            print "You are writing to a mounted device, this is highly dangerous!"
            exit(0)
        if toTest.checkDevIsAvbl() == True:
            print "!!!Attention!!!"
            print "All data on " + args.filename + " will be lost!"
            print "Are you sure you want to continue? (In case you really know what you are doing.)"
            print "Press 'y' to continue, any key to stop:"
            key = raw_input()
            if key != 'y':
                exit(0)
        else:
            print "You are not using a valid device or partition!"
            exit(1)    
        
    #check if iodepth is used
    if args.numjobs == None:
        nj = 1
    else:
        nj = args.numjobs
    if args.iodepth == None:
        iod = 1
    else:
        iod = args.iodepth
            
    if args.mode == "hdd":
        print "Starting HDD mode..."
        #num jobs is not used for hdds
        myTest = TPTest(args.testname,args.filename,iod)
        myTest.run()
        print myTest.getTestname()
        print myTest.getFilename()
        
    if args.mode == "ssd":
        #in xml mode only load objects, don't run tests
        if args.fromxml == True:
            print "Loading from xml file..."
            myTest = SsdPerfTest(args.testname, args.filename,nj, iod)
            myTest.fromXml()
            exit(0)
        
        print "Starting SSD mode..."
        #of jobs and io depth is not given we use 1 for it
        myTest = SsdPerfTest(args.testname, args.filename, nj, iod)
        if args.refill_buffers == True:
            myTest.addSglArgToTests('refill_buffers')
        if myTest.readDevInfoHdparm() != True:
            if args.desc_file == None:
                print "### Error! ###"
                print "Please use a description file for the current device."
                print "The information via hdparm -I is not reliable."
                print "Use -dsc DESC_FILE to provide the information"
                exit(0)
            else:
                myTest.readDevInfoFile(args.desc_file)
        print myTest.getDevInfo()
        myTest.run()
