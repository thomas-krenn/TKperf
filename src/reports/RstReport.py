'''
Created on 9 Aug 2012

@author: gschoenb
'''
from cStringIO import StringIO
from copy import deepcopy

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
        print >>self.__rst,".. sectnum::"
        print >>self.__rst,".. include:: <isonum.txt>\n"
        
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
            if index == 3:
                caption= "\tThe Measurement 3D Plot shows the average of IOPS in the measurement window. For every "
                caption += "workload the IOPS of all block sizes are plotted."
        if perftype == 'tp':
            if index == 0:
                caption= "\tThe Read/Write Steady State Convergence Plot shows the bandwidth for "
                caption += "all block sizes of seq. reads over all rounds. On the top the write throughput is plotted, below "
                caption += "the throughput for read."
            if index == 1:
                caption= "\tThe Steady State Verification Plot shows the bandwidth of 1024k "
                caption += "seq. writes, the 20% average window and the slope of the linear best fit line "
                caption += "in the measurement window."
            if index == 2:
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
            if index == 4:
                caption = "\tThe Latency Measurement 3D Plot shows the average latency on top and the max latency below it. "
                caption += "For the measurement window every workload including all block sizes is plotted."
        if perftype == 'writesat':
            if index == 0:
                caption= "\tThe Write Saturation IOPS Plot shows the average IOPS of 4k random "
                caption += "writes over all rounds."
            if index == 1:
                caption= "\tThe Write Saturation Latency Plot shows the mean latency of 4k random "
                caption += "writes over all rounds."
        self.addString(caption)
        
    def addTable(self,table,labels,perftype):
        '''
        Adds a table to the restructured text.
        @param table The table to insert into the report.
        @param type The type of performance test.
        '''
        #copy labels and values, don't want to change them
        l = list(labels)
        t = deepcopy(table)
        
        if perftype == 'iops':
            val = StringIO()
            print >>self.__rst,".. csv-table:: Average IOPS vs. Block Size and R/W Mix %"
            print >>self.__rst,"\t:header: \"Block Size\ |darr|\", \"Wld. |rarr| \" 100/0, 95/5, 65/35, 50/50, 35/65, 5/95, 0/100\n"
            #reverse the block size in each table row, to start with 512B
            for row in t:
                row.reverse()
            #also reverse labels
            l.reverse()
        if perftype == 'tp':
            val = StringIO()
            print >>self.__rst,".. csv-table:: Average MB/s vs. Block Size and R/W"
            print >>self.__rst,"\t:header: \"Block Size\ |darr|\", \"Read\", \"Write\"\n"
            
        if perftype == 'avg-lat':
            val = StringIO()
            print >>self.__rst,".. csv-table:: Average Latency (ms) vs. Block Size and R/W Mix %"
            print >>self.__rst,"\t:header: \"Block Size\ |darr|\", \"Wld. |rarr| \" 0/100, 65/35, 100/0\n"
            #reverse to start with 0/100
            t.reverse()
        
        if perftype == 'max-lat':
            val = StringIO()
            print >>self.__rst,".. csv-table:: Max Latency (ms) vs. Block Size and R/W Mix %"
            print >>self.__rst,"\t:header: \"Block Size\ |darr|\", \"Wld. |rarr| \" 0/100, 65/35, 100/0\n"
            #reverse to start with 0/100
            t.reverse()
            
        for i in range(len(l)):
            val.write("\t")
            val.write(l[i] + ', ')
            #access the matrix column wise
            for j,elem in enumerate(row[i] for row in t):
                if j != 0:
                    val.write(", ")
                val.write(str(round(elem,3)))
            val.write("\n")
        self.addString(val.getvalue())
        val.close()
                
    
    def toRstFile(self):
        f = open(self.__testname+'.rst','w')
        f.write(self.__rst.getvalue())
        self.__rst.close()
        f.close()
        
    def addDevInfo(self,devStr):
        '''
        Add info about the tested device to the report.
        @param devStr The device information from hdparm or the dsc file.
        ''' 
        self.addChapter("Device Information")
        print >>self.__rst,"Tested Device:"
        if devStr[-1] == '\n':
            devStr = devStr[:-1]
        for line in devStr.split('\n'):
            print >>self.__rst," - " + line
        print >>self.__rst,'\n'
        
    def addSetupInfo(self,ioVer,fioVer,dateStr):
        '''
        Add info about the version of Fio to the report.
        @param setupStr The Fio version string, fetched via str-method of a FioJob.
        @param dateStr The date string the test was carried out.
        ''' 
        self.addChapter("Setup Information")
        print >>self.__rst," - IO Perf Version: " + ioVer
        print >>self.__rst," - Fio Version: " + fioVer
        print >>self.__rst," - Date of test run " + dateStr
        
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
    
    def addSteadyInfo(self,test):
        ''' 
        Adds information about the steady state to the rst report.
        @param test The corresponding test object.
        '''
        self.addSection("Steady State Information")

        stdyStr = StringIO()
        stdyStr.write("Steady State has been reached:\n")
        stdyStr.write(" - ")
        print >>stdyStr, test.getReachStdyState()
        
        stdyStr.write("Steady State has been reached in rounds    :\n")
        stdyStr.write(" - ")
        print >>stdyStr, test.getStdyRnds()
        
        stdyStr.write("Values in stdy measurement window:\n")
        stdyStr.write(" - ")
        print >>stdyStr, test.getStdyValues()
        
        stdyStr.write("Average in stdy measurement window:\n")
        stdyStr.write(" - ")
        print >>stdyStr, test.getStdyAvg()  
        
        self.addString(stdyStr.getvalue())
        stdyStr.close()
    
    def addTestInfo(self,testname,test):
        '''
        Add information about a test to the rst report.
        This part is the main information about a test, it describes how 
        a test has been carried out.
        @param testname Type name of a test.
        @param test The specific test object 
        '''
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
            self.addString(desc.getvalue())
            desc.close()
            self.addSteadyInfo(test)
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
            self.addString(desc.getvalue())
            desc.close()
            self.addSteadyInfo(test)
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
            self.addString(desc.getvalue())
            desc.close()
            self.addSteadyInfo(test)
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
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        