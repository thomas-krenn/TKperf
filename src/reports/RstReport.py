'''
Created on 9 Aug 2012

@author: gschoenb
'''
from io import StringIO
from copy import deepcopy
import os
import inspect
import subprocess
import logging

import perfTest.DeviceTests as dt
from perfTest.StdyState import StdyState

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
        print("====================", file=self.__rst)
        print("TKperf Test Report", file=self.__rst)
        print("====================\n", file=self.__rst)
        print(".. contents::", file=self.__rst)
        print(".. sectnum::", file=self.__rst)
        print(".. include:: <isonum.txt>", file=self.__rst)
        print(".. raw:: pdf\n", file=self.__rst)
        print("\tPageBreak\n", file=self.__rst)

    def addFooter(self):
        print(".. |logo| image:: " + os.path.dirname(inspect.getfile(RstReport)) + "/pics/TKperf_logo.png", file=self.__rst)
        print("\t:height: 90px", file=self.__rst)
        print(".. footer::", file=self.__rst)
        print("\t |logo| A `Thomas-Krenn <http://www.thomas-krenn.com/>`_ project, Page ###Page### of ###Total###\n", file=self.__rst)

    def addChapter(self,chap):
        print(chap, file=self.__rst)
        line = "="
        for i in chap:
            line += "="
        print(line+'\n', file=self.__rst)

    def addSection(self,sec):
        print(sec, file=self.__rst)
        line = "-"
        for i in sec:
            line += "-"
        print(line+'\n', file=self.__rst)
        
    def addString(self,str):
        if str[-1] != '\n':
            str += '\n'
        print(str, file=self.__rst)
    
    def addFigure(self,filename,testtype,perftype,index):
        '''
        Adds a figure to the restructured text.
        @param filename The filename of the figure.
        @param testtype The type of the performance test (ssd,hdd)
        @param type The type of the test (iops,tp etc)
        @param index The index of the caption to insert after the figure.
        '''
        print(".. figure:: "+filename, file=self.__rst) 
        print("\t:scale: 65%", file=self.__rst)
        print("\t:figwidth: 85%\n", file=self.__rst)
        caption = ''
        if testtype == 'ssd':
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
        if testtype == 'hdd':
            if perftype == 'iops':
                if index == 0:
                    caption= "\tThe Measurement Plot shows the IOPS of each one-128th part of the disk. For every "
                    caption += "workload the IOPS of all block sizes are plotted."
            if perftype == 'tp':
                if index == 0:
                    caption= "\tThe Measurement Plot shows the bandwidth of reads and writes in each one-128th part "
                    caption += "of the disk. For all block sizes the seq. read and write bandwidth is plotted."
                if index == 1:
                    caption= "\tThe Boxplot shows minimum, lower quartile, median, upper quartile and maximum. "
                    caption += "For all block sizes the seq. read and write data is plotted."
                    
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
            print(".. csv-table:: Average IOPS vs. Block Size and R/W Mix %", file=self.__rst)
            print("\t:header: \"Block Size\ |darr|\", \"Wld. |rarr| \" 100/0, 95/5, 65/35, 50/50, 35/65, 5/95, 0/100\n", file=self.__rst)
            #reverse the block size in each table row, to start with 512B
            for row in t:
                row.reverse()
            #also reverse labels
            l.reverse()
        if perftype == 'tp':
            val = StringIO()
            print(".. csv-table:: Average MB/s vs. Block Size and R/W", file=self.__rst)
            print("\t:header: \"Block Size\ |darr|\", \"Read\", \"Write\"\n", file=self.__rst)
            
        if perftype == 'avg-lat':
            val = StringIO()
            print(".. csv-table:: Average Latency (ms) vs. Block Size and R/W Mix %", file=self.__rst)
            print("\t:header: \"Block Size\ |darr|\", \"Wld. |rarr| \" 0/100, 65/35, 100/0\n", file=self.__rst)
            #reverse to start with 0/100
            t.reverse()
        
        if perftype == 'max-lat':
            val = StringIO()
            print(".. csv-table:: Max Latency (ms) vs. Block Size and R/W Mix %", file=self.__rst)
            print("\t:header: \"Block Size\ |darr|\", \"Wld. |rarr| \" 0/100, 65/35, 100/0\n", file=self.__rst)
            #reverse to start with 0/100
            t.reverse()
            
        for i in range(len(l)):
            val.write("\t")
            val.write(l[i] + ', ')
            #access the matrix column wise, round the numbers to 3 after
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
    
    def toPDF(self,pdfgen):
        pdf = subprocess.Popen([pdfgen, self.__testname+'.rst'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
        stderr = pdf.communicate()[1]
        if pdf.returncode != 0:
            logging.error("generating the PDF encountered an error: " + stderr)
            raise RuntimeError("PDF gen command error")
    
    def addDevInfo(self,devStr,featMat):
        '''
        Add info about the tested device to the report.
        @param devStr The device information from hdparm or the dsc file.
        @param featMat The extra feature matrix given via a csv table. 
        ''' 
        self.addChapter("Setup Information")
        print("Tested Device:", file=self.__rst)
        if devStr[-1] == '\n':
            devStr = devStr[:-1]
        for line in devStr.split('\n'):
            print(" - " + line, file=self.__rst)
        print('\n', file=self.__rst)
        
        if featMat != None:
            print("Feature Matrix:", file=self.__rst)
            print(featMat + "\n", file=self.__rst)
            
    def addCmdLine(self,cmdLineStr):
        print("Used command line:", file=self.__rst)
        print(" - " + cmdLineStr, file=self.__rst)
        
    def addSetupInfo(self,ioVer,fioVer,dateStr):
        '''
        Add info about the version of Fio to the report.
        @param setupStr The Fio version string, fetched via str-method of a FioJob.
        @param dateStr The date string the test was carried out.
        ''' 
        print("Performance System:", file=self.__rst)
        print(" - TKperf Version: " + ioVer, file=self.__rst)
        print(" - Fio Version: " + fioVer, file=self.__rst)
        print(" - Date of test run: " + dateStr, file=self.__rst)
        
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
        
    def addOSInfo(self,OSDict):
        if OSDict != None:
            print("Operating System:", file=self.__rst)
            if 'kernel' in OSDict:
                print(" - Kernel Version: " + OSDict['kernel'], file=self.__rst)
            if 'lsb' in OSDict:
                print(" - " + OSDict['lsb'], file=self.__rst)
        
    def addGeneralInfo(self,testtype,testrounds):
        '''
        Defines some general used words.
        @param testtype The type of the performance test (ssd,hdd)
        ''' 
        info = StringIO()
        self.addChapter("General Information")
        info.write("- *workloads*: The percentage of read operations in the random mixed workload. In the plots the ")
        info.write("term \"100/00\" means 100% read and 0% write, \"95/5\" 95% read and 5% write, and so on.\n")
        info.write("- *block sizes*: The block size of Fio to be used for IO operations.\n")
        if testtype == 'ssd':
            info.write("- *measurement window*: Those rounds, where the dependence variable became stable.\n")
            info.write("- *dependence variable*: A specific type of test variable to determine the steady state.\n")
        if testtype == 'hdd':
            info.write("- *round*: As an hdd's performance is different at outer and inner side, the ")
            info.write("device is divided into equal size parts. In every round one part of the device is tested")
        self.addString(info.getvalue())
        info.close()
        if testtype == 'ssd':
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
            print("- Measurement Window: " + str(StdyState.testMesWindow), file=info)
            print("- Max. number of rounds: " + str(testrounds) + '\n', file=info)
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
        print(test.getStdyState().isSteady(), file=stdyStr)
        
        stdyStr.write("Steady State has been reached in rounds    :\n")
        stdyStr.write(" - ")
        print(test.getStdyState().getStdyRnds(), file=stdyStr)
        
        stdyStr.write("Values in stdy measurement window:\n")
        stdyStr.write(" - ")
        print(test.getStdyState().getStdyValues(), file=stdyStr)
        
        stdyStr.write("Average in stdy measurement window:\n")
        stdyStr.write(" - ")
        print(test.getStdyState().getStdyAvg(), file=stdyStr)  
        
        self.addString(stdyStr.getvalue())
        stdyStr.close()
    
    def addTestInfo(self,testtype,testname,test):
        '''
        Add information about a test to the rst report.
        This part is the main information about a test, it describes how 
        a test has been carried out.
        @param testtype Type of performance test (hdd,ssd)
        @param testname Type name of a test.
        @param test The specific test object 
        '''
        if testtype == 'ssd':
            if testname == 'iops':
                desc = StringIO()
                desc.write("The IOPS test consists of looping over the following parameters:\n")
                desc.write('\n::\n\n\t')
                print("Make Secure Erase", file=desc)
                print("\tWorkload Ind. Preconditioning", file=desc)
                print("\tWhile not Steady State", file=desc)
                print("\t\tFor workloads ", end=' ', file=desc)
                print(dt.SsdIopsTest.mixWlds, file=desc)
                desc.write('\t\t\t')
                print("For block sizes", end=' ', file=desc)
                print(test.getBsLabels(), file=desc)
                desc.write("\nEach combination of workload and block size is carried out for 60 seconds using direct IO. ")
                desc.write("The average number of read and write IOPS is measured and summed up, therefore 56 values are ")
                desc.write("the result of the two loops.\n")
                desc.write("After these loops are finished one test round has been carried out. To detect the steady state ")
                desc.write("the IOPS of 4k random write are taken.\n\n")
                print("- Dependent Variable: 4k block size, random write", file=desc)
                self.addString(desc.getvalue())
                desc.close()
                self.addSteadyInfo(test)
            if testname == 'tp':  
                desc = StringIO()
                desc.write("The throughput test consists of looping over the following parameters:\n")
                desc.write('\n::\n\n\t')
                print("For block sizes ", end=' ', file=desc)
                print(test.getBsLabels(), file=desc)
                desc.write('\t\t')
                print("Make Secure Erase", file=desc)
                desc.write('\t\t')
                print("While not Steady State", file=desc)
                desc.write('\t\t\t')
                print("Sequential read", file=desc)
                desc.write('\t\t\t')
                print("Sequential write", file=desc)
                desc.write("\nFor each block size sequential read and write is carried out for 60 seconds using direct IO. ")
                desc.write("The number of kilobytes for read and write is measured, therefore 2 values are ")
                desc.write("the result of one round.\n")
                desc.write("To detect the steady state the throughput of 1024k sequential write is taken.\n\n")
                print("- Dependent Variable: 1024k block size, sequential write", file=desc)
                self.addString(desc.getvalue())
                desc.close()
                self.addSteadyInfo(test)
            if testname == 'lat':  
                desc = StringIO()
                desc.write("The latency test consists of looping over the following parameters:\n")
                desc.write('\n::\n\n\t')
                print("Make Secure Erase", file=desc)
                print("\tWorkload Ind. Preconditioning", file=desc)
                print("\tWhile not Steady State", file=desc)
                print("\t\tFor workloads ", end=' ', file=desc)
                print(dt.SsdLatencyTest.mixWlds, file=desc)
                desc.write('\t\t\t')
                print("For block sizes", end=' ', file=desc)
                print(test.getBsLabels(), file=desc)
                desc.write("\nFor all block sizes random read, a 65/35 read/write mixed workload and random write is carried out for 60 ") 
                desc.write("seconds using direct IO. ")
                desc.write("For every combination the Min, Max and Mean Latency is measured. ")
                desc.write("After these loops are finished one test round has been carried out. To detect the steady state ")
                desc.write("the mean latency of 4k random write is taken.\n\n")
                print("- Dependent Variable: 4k block size, random write mean latency", file=desc)
                self.addString(desc.getvalue())
                desc.close()
                self.addSteadyInfo(test)
            if testname == 'writesat':  
                desc = StringIO()
                desc.write("The write saturation test consists of looping over the following parameters:\n")
                desc.write('\n::\n\n\t')
                print("Make Secure Erase", file=desc)
                print("\tWhile not written 4x User Capacity or 24h", file=desc)
                print("\t\tCarry out random write, 4k block size for 1 minute.", file=desc)
                desc.write("\nFor 4k block size random write is carried out for 60 ") 
                desc.write("seconds using direct IO. ")
                desc.write("For each round (60 second window) the write IOPS and latencies are measured. Also the total written ")
                desc.write("IO is measured to check if 4x capacity has been written.\n\n")
                desc.write("As no steady state detection is necessary there is no dependence variable.\n\n")
                self.addString(desc.getvalue())
                desc.close()
        
        if testtype == 'hdd':
            if testname == 'iops':
                desc = StringIO()
                desc.write("The IOPS test consists of looping over the following parameters:\n")
                desc.write('\n::\n\n\t')
                print("Divide device in " + str(dt.HddIopsTest.maxRnds) + " parts", file=desc)
                print("\tFor range(" + str(dt.HddIopsTest.maxRnds) + ")", file=desc)
                print("\t\tFor workloads ", end=' ', file=desc)
                print(dt.HddIopsTest.mixWlds, file=desc)
                desc.write('\t\t\t')
                print("For block sizes", end=' ', file=desc)
                print(test.getBsLabels(), file=desc)
                desc.write("\nEach combination of workload and block size is carried out for 60 seconds using direct IO. ")
                desc.write("The IOPS of one round are an indicator for the random performance of the corresponding area.")
                self.addString(desc.getvalue())
                desc.close()
            if testname == 'tp':  
                desc = StringIO()
                desc.write("The throughput test consists of looping over the following parameters:\n")
                desc.write('\n::\n\n\t')
                print("For block sizes ", end=' ', file=desc)
                print(test.getBsLabels(), file=desc)
                desc.write('\t\t')
                print("For range(" + str(dt.HddTPTest.maxRnds) + ")", file=desc)
                desc.write('\t\t\t')
                print("Sequential read", file=desc)
                desc.write('\t\t\t')
                print("Sequential write", file=desc)
                desc.write("\nFor each block size, every area of the device (this are the rounds) is tested ")
                desc.write("with sequential read and write using direct IO. ")
                self.addString(desc.getvalue())
                desc.close()
