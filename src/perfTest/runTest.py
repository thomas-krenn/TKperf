'''
Created on 27.06.2012

@author: gschoenb
'''


import argparse
from fio.FioJob import FioJob

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", help="specify the test mode for the device", choices=["hdd","ssd"])
    parser.add_argument("-v","--version", help="get the version information", action="store_true")
    args = parser.parse_args()
    if args.mode == "hdd":
        print "hdd on"
        fio = FioJob()
        fio.addArg("name", "io-perf-test")#
        fio.addArg("size","10M")
        fio.addArg("rw","read")
        fio.hddTest()
    if args.mode == "ssd":
        print "ssd on"
    if args.version:
        print fio