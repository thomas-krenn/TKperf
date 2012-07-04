'''
Created on 27.06.2012

@author: gschoenb
'''


import argparse
from fio.FioJob import FioJob
from perfTest.SsdTest import SsdTest

if __name__ == '__main__':
    vTest = FioJob()
    fioVersion = vTest.__str__()#Fetch the fio version
    
    parser = argparse.ArgumentParser()
    
    parser.add_argument("mode", help="specify the test mode for the device", choices=["hdd","ssd"])
    parser.add_argument("testname",help="name of the fio job, corresponds to the result output file")
    parser.add_argument("filename",help="data file or device name to run fio test on")
    
    parser.add_argument("-v","--version", help="get the version information", action='version',version=fioVersion)
    
    args = parser.parse_args()
    if args.mode == "hdd":
        print "hdd on"
    if args.mode == "ssd":
        print "ssd on"
        myTest = SsdTest(args.testname,args.filename)
        myTest.wlIndPrec()
        print myTest.getTestname()
        print myTest.getFilename()
