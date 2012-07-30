'''
Created on 09.07.2012

@author: gschoenb
'''
from __future__ import division
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

import perfTest as pT

def stdyStVerPlt(toPlot,mode):
    '''
    Generate a steady state verification plot.
    The plot includes:
    -Measured IOPS|Latencies|Throughput of rounds in which steady state was reached
    -Average IOPS|Latencies|Throughput in steady state rounds
    -Slope of best fit line
    -Top and Bottom limits: +-10% percent of average
    The figure is saved as SsdTest.Testname-stdyStVerPlt.png.
    @param toPlot A SsdTest object.
    @param mode A string representing the test mode (IOPS|LAT|TP)
    '''
    x = np.array(toPlot.getStdyRnds())
    #calculate average and its top and bottom limit
    av = []
    avT = []
    avB = []
    av.append(toPlot.getStdyAvg())
    avTop = toPlot.getStdyAvg() * 1.10
    avBot = toPlot.getStdyAvg() * 0.9
    avT.append(avTop)
    avB.append(avBot)
    av = av * len(x)
    avT = avT * len(x)
    avB = avB * len(x)
    
    plt.clf()#clear
    plt.plot(x,toPlot.getStdyValues(),'o', label=mode, markersize=10)
    plt.plot(x, toPlot.getStdySlope()[0]*x + toPlot.getStdySlope()[1], 'r', label='Slope')
    plt.plot(x, av, '-', color='black',label='Average')
    plt.plot(x, avT, '--', color='black',label='Top')
    plt.plot(x, avB, '--', color='black',label='Bottom')
    
    #set the y axes to start at 3/4 of mininum
    plt.ylim(min(toPlot.getStdyValues())*0.75,max(toPlot.getStdyValues())*1.25)
    plt.xticks(x)
    title = mode + " Steady State Verification Plot"
    plt.title(title)
    plt.xlabel("Round")
    if mode == "LAT":
        plt.ylabel("Avg latency (us)")
    if mode == "TP":
        plt.ylabel("Avg bandwidth (KB/s)")
    if mode == "IOPS":
        plt.ylabel(mode)
    plt.legend()
    plt.savefig(toPlot.getTestname()+'-'+mode+'-stdyStVerPlt.png',dpi=300)
    
def stdyStConvPlt(toPlot,mode):
    '''
    Generate a steady state convergence plot.
    The plot consists of:
    IOPS:
        -Measured IOPS of pure random write
    LAT:
        -Avg latency of read, mixed, write
    -All lines are the different block sizes
    -IOPS/Latencies of all the rounds are plotted
    The figure is saved as SsdTest.Testname-stdyStConvPlt.png.
    @param toPlot A SsdTest object.
    @param mode A string representing the test mode (IOPS|LAT)
    '''
    rnds = toPlot.getRnds()
    matrices = toPlot.getRndMatrices()
    bsLens = len(matrices[0][-1])#fetch the number of bs of the first matrix
    
    #initialize matrix for plotting
    if mode == "IOPS":
        lines = []
        for i in range(bsLens):
            lines.append([])
        for rndMat in matrices:
            row = rndMat[-1]#last row is random write
            for i in range(len(row)):
                lines[i].append(row[i])#switch from row to column wise ordering of values
    
    if mode == "LAT":
        readLines = []
        writeLines = []
        mixLines = []
        for i in range(bsLens):
            readLines.append([])
            writeLines.append([])
            mixLines.append([])
        for rndMat in matrices:
            #take read mat len, every elem has the same len
            for i in range(len(rndMat[0])):
                readLines[i].append(rndMat[0][i][2])#mean latency
                mixLines[i].append(rndMat[1][i][2])#mean latency
                writeLines[i].append(rndMat[2][i][2])#mean latency
    
    plt.clf()#clear

    #fetch number of rounds, we want to include all rounds
    x = range(rnds + 1)
    max_y = 0
    min_y = 0
    if mode == "IOPS":
        for i in range(len(lines)):
            min_y,max_y = getMinMax(lines[i], min_y, max_y)
            plt.plot(x,lines[i],'o-',label='bs='+pT.SsdTest.SsdTest.bsLabels[i])
    if mode == "LAT":
        for i in range(len(readLines)):
            min_y,max_y = getMinMax(readLines[i], min_y, max_y)
            plt.plot(x,readLines[i],'o-',label='bs='+pT.SsdTest.SsdTest.latBsLabels[i]+' read')
        for i in range(len(mixLines)):
            min_y,max_y = getMinMax(mixLines[i], min_y, max_y)
            plt.plot(x,mixLines[i],'o-',label='bs='+pT.SsdTest.SsdTest.latBsLabels[i]+' mixed')
        for i in range(len(writeLines)):
            min_y,max_y = getMinMax(writeLines[i], min_y, max_y)
            plt.plot(x,writeLines[i],'o-',label='bs='+pT.SsdTest.SsdTest.latBsLabels[i]+' write')
    
    #create a subplot with two columns for legend placement
    plt.xticks(x)
    plt.suptitle(mode+" Steady State Convergence Plot",fontweight='bold')
    plt.xlabel("Round")
    plt.ylim((min_y*0.75,max_y*1.25))
    if mode == "LAT":
        plt.ylabel("Avg latency (us)")
    if mode == "IOPS":
        plt.ylabel(mode)
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.09),
               ncol=3, fancybox=True, shadow=True)
    plt.savefig(toPlot.getTestname()+'-'+mode+'-stdyStConvPlt.png',dpi=300)

def IOPSplot(toPlot):
    rnds = pT.HddTest.HddTest.tpTestRnds
    matrices = toPlot.getRndMatrices()
    
    wlds = pT.HddTest.HddTest.mixWlds
    bsLabels = pT.HddTest.HddTest.bsLabels
    
    #each row will be a workload percentage
    mixWLds = []
    for i in range(len(wlds)):
        mixWLds.append([])
        #in each row will be the different block sizes
        for bs in range(len(bsLabels)):
            mixWLds[i].append([])
            
    for rnd in matrices:
        #each round has its workloads
        for i,row in enumerate(rnd):
            #each workload has its block sizes
            for j,bs in enumerate(row):
                mixWLds[i][j].append(bs)

    plt.clf()#clear
    x = range(rnds)
    max_y = 0
    min_y = 0
    for i in range(len(mixWLds)):
        if i == 0:
            lc = 'blue'
        if i == 1:
            lc = 'green'
        if i == 2:
            lc = 'red'
        for j in range(len(mixWLds[i])):
            if j == 0:
                ls = 's-'
            if j == 1:
                ls = 'o-'
            if j == 2:
                ls = '^-'
            min_y,max_y = getMinMax(mixWLds[i][j], min_y, max_y)
            plt.plot(x,mixWLds[i][j],ls,color=lc,
                  label=str(wlds[i])+'/bs=' + bsLabels[j])
    plt.xticks(x)
    plt.suptitle("HDD IOPS plot",fontweight='bold')
    plt.xlabel("Number of Area of Device")
    plt.ylabel("IOPS")
    #plt.yscale('log')
    plt.ylim((min_y*0.75,max_y*1.25))
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.09),
               ncol=3, fancybox=True, shadow=True)
    plt.savefig(toPlot.getTestname()+'-IOPSPlt.png',dpi=300)
    
def mes2DPlt(toPlot,mode):
    '''
    Generate a measurement 2D plot.
    The plot includes:
    -Lines of the workloads
    -Each line consists of the average of IOPS per round
    for each block size in the measurement window!
    Therefore the x axes are the block sizes, the plotted lines
    are the different workloads (from 100% read to 100% write). The
    y axes is the average of IOPS over the measurement window for each block sizes
    and workload.
    The figure is saved as SsdTest.Testname-mes2DPlt.png.
    @param toPlot A SsdTest object.
    @param mode A string representing the test mode (IOPS|max-LAT|avg-LAT)
    '''
    mixWLds = []
    mesWin = toPlot.getStdyRnds() #get measurement window, only include these values
    
    if mode == "IOPS":
        wlds = pT.SsdTest.SsdTest.mixWlds
        bsLabels = pT.SsdTest.SsdTest.bsLabels
    if mode == "avg-LAT" or mode == "max-LAT":
        wlds = pT.SsdTest.SsdTest.latMixWlds
        bsLabels = pT.SsdTest.SsdTest.latBsLabels
    
    #each row will be a workload percentage
    for i in range(len(wlds)):
        mixWLds.append([])
        #in each row will be the different block sizes
        for bs in range(len(bsLabels)):
            mixWLds[i].append(0)
    matrices = toPlot.getRndMatrices()    
    
    #limit the matrices to the measurement window
    for j in mesWin:
        rndMat = matrices[j]
        #each row is a percentage of a workload
        for i,row in enumerate(rndMat):
            #in each row are the different block sizes
            for bs in range(len(row)):
                #calculate average iteratively
                if mixWLds[i][bs] != 0:
                    #calculate max latency or continue with average
                    if mode == "max-LAT":
                        if row[bs][1] > mixWLds[i][bs]:
                            mixWLds[i][bs] = row[bs][1]#max latency
                    else:
                        mixWLds[i][bs] *= bs
                        if mode == "IOPS":
                            mixWLds[i][bs] += row[bs]#IOPS
                        if mode == "avg-LAT":
                            mixWLds[i][bs] += row[bs][2]#mean latency
                        mixWLds[i][bs] = (mixWLds[i][bs]) / (bs+1)
                else:
                    if mode == "IOPS":
                        mixWLds[i][bs] = row[bs]#IOPS
                    if mode == "max-LAT":
                        mixWLds[i][bs] = row[bs][1]#max latency
                    if mode == "avg-LAT":
                        mixWLds[i][bs] = row[bs][2]#mean latency
                        
    plt.clf()#clear plot
    if mode == "IOPS":
        x = getBS(pT.SsdTest.SsdTest.bsLabels)
        #x = range(len(pT.SsdTest.SsdTest.bsLabels   ))
    if mode == "avg-LAT" or mode == "max-LAT":
        x = getBS(pT.SsdTest.SsdTest.latBsLabels)
        
    max_y = 0
    min_y = 0
    for i in range(len(mixWLds)):
        min_y,max_y = getMinMax(mixWLds[i], min_y, max_y)
        #the labels are r/w percentage of mixed workload
        plt.plot(x,mixWLds[i],'o-',
                  label=str(wlds[i])+'/'+str(100-wlds[i]))
     
    
    plt.title(mode+" Measurement Plot")
    plt.xlabel("Block Size (Byte)")
    plt.yscale('log')
    plt.xscale('log')
    #scale axis to min and max +- 25%
    plt.ylim((min_y*0.75,max_y*1.25))
    plt.xticks(x,bsLabels)
    if mode == "avg-LAT" or mode == "max-LAT":
        plt.ylabel("Avg latency (us)")
    if mode == "IOPS":
        plt.ylabel(mode)
    plt.legend()
    plt.savefig(toPlot.getTestname()+'-'+mode+'-mes2DPlt.png',dpi=300)

def getBS(bsLabels):
    bs = []
    for b in bsLabels:
        if b == "512":
            bs.append(0.5)
            continue
        s = b[0:-1]
        bs.append(int(s))
    return bs

def getMinMax(values, currMin, currMax):
    '''
    Returns the minimum and maximum of a sequence of values.
    @param values Squence to calculate min and max for
    @param currMin Current minimum to compare to.
    @param currMax Current maximum to compare to.
    @return [newMin,newMax] if newMin is smaller than currMin,
    newMax if it is greater than currMax.
    '''
    #TODO Testing for 0 can be a problem if minimum is really 0
    # This should not happen for performance tests under normal circumstances
    newMin = 0
    newMax = 0
    curr = max(values)
    if curr > currMax:
        newMax = curr
    else:
        newMax = currMax
    curr = min(values)
    if currMin == 0:
        newMin = curr
    else:
        if curr < currMin:
            newMin = curr
        else:
            newMin = currMin
    return [newMin,newMax]
    
def writeSatIOPSPlt(toPlot):
    #fetch number of rounds, we want to include all rounds
    #as stdy state was reached at rnds, it must be included
    rnds = toPlot.getWriteSatRnds()
    x = range(rnds + 1)
    
    iops_l = toPlot.getWriteSatMatrix()[0]#first elem in matrix are iops

    plt.clf()#clear plot        
    plt.plot(x,iops_l,'-',label='Avg IOPS')
    plt.ylim(min(iops_l)*0.75,max(iops_l)*1.25)
    #every 10 rounds print the round number
    x = range(0,rnds + 1,50)
    plt.xticks(x)
    plt.suptitle("Write Saturation Test",fontweight='bold')
    plt.xlabel("Round #")
    plt.ylabel("IOPS")
    plt.legend()
    plt.savefig(toPlot.getTestname()+'-writeSatIOPSPlt.png',dpi=300)
    
def writeSatLatPlt(toPlot):
    rnds = toPlot.getWriteSatRnds()
    x = range(rnds + 1)
    
    lats_l = toPlot.getWriteSatMatrix()[1]#second elem in matrix are latencies
    
    #get the average latencies from the lat list (last elem)
    av_lats = []
    for i in lats_l:
        av_lats.append((i[2]) / 1000)
    
    plt.clf()#clear plot
    plt.plot(x,av_lats,'-',label='Avg latency')
    #set the y axes to start at 3/4 of mininum
    plt.ylim(min(av_lats)*0.75,max(av_lats)*1.25)
    #every 10 rounds print the round number
    x = range(0,rnds + 1,10)
    plt.xticks(x)
    plt.suptitle("Write Saturation Test",fontweight='bold')
    plt.xlabel("Round #")
    plt.ylabel("Latency ms")
    plt.legend()
    plt.savefig(toPlot.getTestname()+'-writeSatLatPlt.png',dpi=300)
    
def tpStdyStConvPlt(toPlot,mode,dev):
    '''
    Generate a steady state convergence plot for throughput measurements.
    The plot consists of:
    -Measured bandwidths per round per block size
    -All lines are the different block sizes
    -x axes is the number of all rounds
    -y axes is the bw of the corresponding round
    The figure is saved as SsdTest.Testname-bw-stdyStConvPlt.png.
    @param toPlot A SsdTest object.
    @param mode String "read|write|rw"
    @param dev String "ssd|hdd"
    '''
    matrices = toPlot.getTPRndMatrices()
    rnds = len(matrices[0][0])#fetch the number of total rounds
    bsLens = len(matrices)#fetch the number of bs, each row is a bs in the matrix
    
    if dev == "hdd":
        bsLabels = pT.HddTest.HddTest.tpBsLabels
    else:
        bsLabels = pT.SsdTest.SsdTest.tpBsLabels
    
    #initialize matrix for plotting
    lines = []
    for i in range(bsLens):
        lines.append([])
    
    #values for scaling the axes
    max_y = 0
    min_y = 0
    
    plt.clf()#clear
    x = range(rnds)#determined by len of matrix
    for i,rndMat in enumerate(matrices):
        if dev == "hdd" and mode == "rw":
            min_y,max_y = getMinMax(rndMat[0], min_y, max_y)
            plt.plot(x,rndMat[0],'o-',label='read bs='+bsLabels[i])
            min_y,max_y = getMinMax(rndMat[1], min_y, max_y)
            plt.plot(x,rndMat[1],'o-',label='write bs='+bsLabels[i])
        else:
            if mode == "read":
                row = rndMat[0]#plot the read row
            if mode == "write":
                row = rndMat[1]#plot the write row
            min_y,max_y = getMinMax(row, min_y, max_y)
            plt.plot(x,row,'o-',label='bs='+bsLabels[i])
    
    if dev == "hdd":
        x = range(0,pT.HddTest.HddTest.tpTestRnds+1,16)
        plt.xticks(x)
    else:
        x = range(rnds)
        plt.xticks(x)
    if dev == "hdd":
        plt.suptitle("TP "+mode+" Plot",fontweight='bold')    
        plt.xlabel("Number of Area of Device")
    else:
        plt.suptitle("TP "+mode+" Steady State Convergence Plot",fontweight='bold')
        plt.xlabel("Round")
    plt.ylabel("BW KB/s")
    #scale axis to min and max +- 25%
    plt.ylim((min_y*0.6,max_y*1.15))
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.09),
               ncol=2, fancybox=True, shadow=True)
    if dev == "hdd":
        plt.savefig(toPlot.getTestname()+'-'+mode+'-TpPlt.png',dpi=300)
    else:
        plt.savefig(toPlot.getTestname()+'-TP-'+mode+'-stdyStConvPlt.png',dpi=300)
    
def tpMes2DPlt(toPlot):
    '''
    Generate a measurement 2D plot for throughput measurements.
    The plot includes:
    -One line for read, one line for write
    -Each line consists of the average of IOPS per round
    for each block size in the measurement window!
    Therefore the x axes are the block sizes, the y axes is
    the average over the measurement window for each block size.
    The figure is saved as SsdTest.Testname-bw-mes2DPlt.png.
    @param toPlot A SsdTest object.
    '''
    wlds = [] #read and write workload mode
    
    #one row for read, one for write
    for i in range(2):
        wlds.append([])
        #in each row will be the different block sizes
        for bs in range(len(pT.SsdTest.SsdTest.tpBsLabels)):
            wlds[i].append(0)
    matrices = toPlot.getTPRndMatrices()    
    
    #each row of the matrix is a block size
    for j,bs in enumerate(matrices):
        #each block size has read and write
        for i,row in enumerate(bs):
            #read and write have their round values
            for rnd in toPlot.getStdyRnds():
                #calculate average iteratively
                if wlds[i][j] != 0:
                    wlds[i][j] *= rnd
                    wlds[i][j] += row[rnd]
                    wlds[i][j] = (wlds[i][j]) / (rnd+1)
                else:
                    wlds[i][j] = row[rnd]
    plt.clf()#clear
    x = getBS(pT.SsdTest.SsdTest.tpBsLabels)
    for i in range(len(wlds)):
        if i == 0:
            label = "read"
        else:
            label = "write"
        plt.plot(x,wlds[i],'o-',label=label)
    
    plt.xscale('log')
    plt.suptitle("TP Measurement Plot",fontweight='bold')
    plt.xlabel("Block Size (KB)")
    plt.ylabel("BW KB/s")
    plt.xticks(x,pT.SsdTest.SsdTest.tpBsLabels)
    #plt.legend()
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.09),
               ncol=3, fancybox=True, shadow=True)
    plt.savefig(toPlot.getTestname()+'-TP-mes2DPlt.png',dpi=300)
    
def ioDepthMes3DPlt(toPlot,rw):
    fig = plt.figure()
    ax = Axes3D(fig)
    
    matrices = toPlot.getIodMatrices()
     
    #define positions for bars
    xpos = np.array([0.25,0.25,0.25,0.25]) # Set up a mesh of positions
    ypos = np.array([0.25,1.25,2.25,3.25])
    zpos = np.array([0,0,0,0])
    
    dx = [0.5,0.5,0.5,0.5]
    dy = [0.5,0.5,0.5,0.5]

    #FIXME Currently we use only the first round    
    if rw == "read": matrix = list(matrices[0][0])
    if rw == "write": matrix = list(matrices[0][1])
    if rw == "randread": matrix = list(matrices[0][2])
    if rw == "randwrite": matrix = list(matrices[0][3])
    
    #as IOPS are the mos for small sizes we revers the block sizes
    if rw == "randread" or rw == "randwrite":
        matrix.reverse()
    for j,bs in enumerate(matrix):
        print bs
        if j == 0: bcolor = 'b'
        if j == 1: bcolor = 'g'
        if j == 2: bcolor = 'r'
        if j == 3: bcolor = 'y'
        ax.bar3d(xpos,ypos,zpos, dx, dy, bs,color = bcolor)
        for pos in range(len(xpos)):
            xpos[pos] += 1
            
    print matrices[0][2]
    ticksx = np.arange(0.5, 4, 1)
    if rw == "randread" or rw == "randwrite":
        labels = list(pT.SsdTest.SsdTest.iodBsLabels)
        labels.reverse()
        plt.xticks(ticksx, labels)
    else:
        plt.xticks(ticksx, pT.SsdTest.SsdTest.iodBsLabels)
    ticksy = np.arange(0.5, 4, 1)
    plt.yticks(ticksy,pT.SsdTest.SsdTest.iodDepths)
    plt.suptitle("IOD "+rw+" Measurement Plot",fontweight='bold')
    ax.set_xlabel('Block Size (Byte)')
    ax.set_ylabel('IO Depth')
    if rw == "read" or rw == "write":
        ax.set_zlabel('BW')
    if rw == "randread" or rw == "randwrite":
        ax.set_zlabel('IOPS')
    plt.savefig(toPlot.getTestname()+'-IOD-'+rw+'-mes3DPlt.png',dpi=300)


    
    
    
    