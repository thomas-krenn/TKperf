'''
Created on 9 Aug 2012

@author: gschoenb
'''
from cStringIO import StringIO

import perfTest.SsdTest as ssd

class RstReport(object):
    '''
    A report as restructured text.
    '''

    def __init__(self,testname):
        '''
        @param testname Name of the test, also the filename. 
        '''
        self.__testname = testname
        self.__rst = StringIO()
    
    def getRst(self):
        return self.__rst    
    
    def addTitle(self):
        print >>self.__rst,"===================="
        print >>self.__rst,"IO perf test report"
        print >>self.__rst,"====================\n"
        print >>self.__rst,".. contents::"
        print >>self.__rst,".. sectnum::\n"
        
    def addFooter(self):
        print >>self.__rst,".. |logo| image:: ../../../TK_Logo_RGB.png"
        print >>self.__rst,"\t:height: 70px"
        print >>self.__rst,".. footer::"
        print >>self.__rst,"\t|logo| http://www.thomas-krenn.com - Page ###Page### of ###Total###\n"
    
    def addChapter(self,chap):
        print >>self.__rst, chap
        line = "="
        for i in chap:
            line += "="
        print >>self.__rst, line+'\n'
        
    def addSection(self,sec):
        print >>self.__rst, sec
        line = "-"
        for i in sec:
            line += "-"
        print >>self.__rst, line+'\n'
        
    def addString(self,str):
        if str[-1] != '\n':
            str += '\n'
        print >>self.__rst, str
    
    def addFigure(self,filename,perftype,index):
        '''
        Adds a figure to the restructured text.
        @param filename The filename of the figure.
        @param type The type of performance test
        @param index The index of the caption to insert after the figure.
        '''
        print >>self.__rst,".. figure:: "+filename 
        print >>self.__rst,"\t:scale: 65%"
        print >>self.__rst,"\t:figwidth: 85%\n"
        caption = ''
        if perftype == 'iops':
            if index == 0:
                caption= "\tThe Steady State Convergence Plot shows the reached IOPS for "
                caption += "all block sizes of random writes over all rounds."
            if index == 1:
                caption= "\tThe Steady State Verification Plot shows the measured IOPS of 4k "
                caption += "random writes, the 20% average window and the slope of the linear best fit line "
                caption += "in the measurement window."
            if index == 2:
                caption= "\tThe Measurement Plot shows the average of IOPS in the measurement window. For every "
                caption += "workload the IOPS of all block sizes are plotted."
        if perftype == 'tp':
            if index == 0:
                caption= "\tThe Read Steady State Convergence Plot shows the bandwidth for "
                caption += "all block sizes of seq. reads over all rounds."
            if index == 1:
                caption= "\tThe Write Steady State Convergence Plot shows the bandwidth for "
                caption += "all block sizes of seq. writes over all rounds."
            if index == 2:
                caption= "\tThe Steady State Verification Plot shows the bandwidth of 1024k "
                caption += "seq. writes, the 20% average window and the slope of the linear best fit line "
                caption += "in the measurement window."
            if index == 3:
                caption= "\tThe Measurement Plot shows the average bandwidth of reads and writes in the measurement window. "
                caption += "For all block sizes the seq. read and write bandwidth is plotted."
        if perftype == 'lat':
            if index == 0:
                caption= "\tThe Steady State Convergence Plot shows the mean latency for "
                caption += "all block sizes of random read, mixed workload and write."
            if index == 1:
                caption= "\tThe Steady State Verification Plot shows the mean latency of 4k "
                caption += "random writes, the 20% average window and the slope of the linear best fit line "
                caption += "in the measurement window."
            if index == 2:
                caption= "\tThe Average Latency Measurement Plot shows the mean latency over the measurement window. For every "
                caption += "workload the latency of all block sizes is plotted."
            if index == 3:
                caption= "\tThe Max Latency Measurement Plot shows the maximum latency of the measurement window. For every "
                caption += "workload the maximum latency of all block sizes is plotted."
        if perftype == 'writesat':
            if index == 0:
                caption= "\tThe Write Saturation IOPS Plot shows the average IOPS of 4k random "
                caption += "writes over all rounds."
            if index == 1:
                caption= "\tThe Write Saturation Latency Plot shows the mean latency of 4k random "
                caption += "writes over all rounds."
        self.addString(caption)
        
    
    def toRstFile(self):
        f = open(self.__testname+'.rst','w')
        f.write(self.__rst.getvalue())
        self.__rst.close()
        f.close()
        
    def addSetupInfo(self,str):
        '''
        Add info about the version of Fio to the report.
        @param str The Fio version string, fetched via str-method of a FioJob.
        ''' 
        self.addChapter("Setup Information")
        self.addString("Performance Tool:\n" + " - " + str)
        
    def addFioJobInfo(self,nj,iod):
        '''
        Write information about Fio number of jobs and iodepth to report.
        @param nj The number of jobs.
        @param iod The number of outstanding ios (iodepth).
        ''' 
        info = StringIO()
        info.write(" - Number of jobs: " + str(nj) + "\n")
        info.write(" - Number of outstanding IOs (iodepth): " + str(iod))
        self.addString(info.getvalue())
        info.close()
        
    def addGeneralInfo(self):
        info = StringIO()
        self.addChapter("General Information")
        info.write("- *workloads*: The percentage of read operations in the random mixed workload. In the plots the ")
        info.write("term \"100/00\" means 100% read and 0% write, \"95/5\" 95% read and 5% write, and so on.\n")
        info.write("- *block sizes*: The block size of Fio to be used for IO operations.\n")
        info.write("- *measurement window*: Those rounds, where the dependence variable became stable.\n")
        info.write("- *dependence variable*: A specific type of test variable to determine the steady state.\n")
        self.addString(info.getvalue())
        info.close()
        info = StringIO()
        self.addSection("Steady State")
        info.write("The Steady State is to determine if a test has reached a steady performance level. ")
        info.write("Each test has a different dependence variable to check if the state has already been reached. ")
        info.write("To check for the steady state the performance values of a test measurement window are taken (the last 5 rounds).\n")
        info.write("The steady state is reached if:\n\n")
        info.write("- The maximum data excursion is less than 20% of the average in the measurement window.\n")
        info.write("- The slope of the linear best fit line is less than 10% of the average in the measurement window\n\n")
        
        info.write("If these two conditions are met the steady state has been reach for the specific dependence variable. ")
        info.write("Therefore the test can be stopped and the performance values of the measurement window can be taken ")
        info.write("for the measurement plots. If the steady state has not been reached after a maximum number of rounds the test ")
        info.write("can be stopped as well. The numbers for these two variables are:\n\n")
        print >>info, "- Measurement Window: " + str(ssd.StdyTest.testMesWindow)
        print >>info, "- Max. number of rounds: " + str(ssd.StdyTest.testRnds) + '\n'
        self.addString(info.getvalue())
        info.close()
    
    def addTestInfo(self,testname):
        if testname == 'iops':
            desc = StringIO()
            desc.write("The IOPS test consists of looping over the following parameters:\n")
            desc.write('\n::\n\n\t')
            print >>desc, "Make Secure Erase"
            print >>desc, "\tWorkload Ind. Preconditioning"
            print >>desc, "\tWhile not Steady State"
            print >>desc, "\t\tFor workloads ",
            print >>desc, ssd.IopsTest.mixWlds
            desc.write('\t\t\t')
            print >>desc, "For block sizes",
            print >>desc, ssd.IopsTest.bsLabels
            desc.write("\nEach combination of workload and block size is carried out for 60 seconds using direct IO. ")
            desc.write("The average number of read and write IOPS is measured and summed up, therefore 56 values are ")
            desc.write("the result of the two loops.\n")
            desc.write("After these loops are finished one test round has been carried out. To detect the steady state ")
            desc.write("the IOPS of 4k random write are taken.\n\n")
            print >>desc, "- Dependent Variable: 4k block size, random write"
        if testname == 'tp':  
            desc = StringIO()
            desc.write("The throughput test consists of looping over the following parameters:\n")
            desc.write('\n::\n\n\t')
            print >>desc, "For block sizes ",
            print >>desc, ssd.TPTest.bsLabels
            desc.write('\t\t')
            print >>desc, "Make Secure Erase"
            desc.write('\t\t')
            print >>desc, "While not Steady State"
            desc.write('\t\t\t')
            print >>desc, "Sequential read"
            desc.write('\t\t\t')
            print >>desc, "Sequential write"
            desc.write("\nFor each block size sequential read and write is carried out for 60 seconds using direct IO. ")
            desc.write("The number of kilobytes for read and write is measured, therefore 2 values are ")
            desc.write("the result of one round.\n")
            desc.write("To detect the steady state the throughput of 1024k sequential write is taken.\n\n")
            print >>desc, "- Dependent Variable: 1024k block size, sequential write"
        if testname == 'lat':  
            desc = StringIO()
            desc.write("The latency test consists of looping over the following parameters:\n")
            desc.write('\n::\n\n\t')
            print >>desc, "Make Secure Erase"
            print >>desc, "\tWorkload Ind. Preconditioning"
            print >>desc, "\tWhile not Steady State"
            print >>desc, "\t\tFor workloads ",
            print >>desc, ssd.LatencyTest.mixWlds
            desc.write('\t\t\t')
            print >>desc, "For block sizes",
            print >>desc, ssd.LatencyTest.bsLabels
            desc.write("\nFor all block sizes random read, a 65/35 read/write mixed workload and random write is carried out for 60 ") 
            desc.write("seconds using direct IO. ")
            desc.write("For every combination the Min, Max and Mean Latency is measured. ")
            desc.write("After these loops are finished one test round has been carried out. To detect the steady state ")
            desc.write("the mean latency of 4k random write is taken.\n\n")
            print >>desc, "- Dependent Variable: 4k block size, random write mean latency"
        if testname == 'writesat':  
            desc = StringIO()
            desc.write("The write saturation test consists of looping over the following parameters:\n")
            desc.write('\n::\n\n\t')
            print >>desc, "Make Secure Erase"
            print >>desc, "\tWhile not written 4x User Capacity or 24h"
            print >>desc, "\t\tCarry out random write, 4k block size for 1 minute."
            desc.write("\nFor 4k block size random write is carried out for 60 ") 
            desc.write("seconds using direct IO. ")
            desc.write("For each round (60 second window) the write IOPS and latencies are measured. Also the total written ")
            desc.write("IO is measured to check if 4x capacity has been written.\n\n")
            desc.write("As no steady state detection is necessary there is no dependence variable.\n\n")
        self.addString(desc.getvalue())
        desc.close()
        
        
        
        
        
        
        
        
        
        
        
        
        
        