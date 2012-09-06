'''
Created on 09.07.2012

@author: gschoenb
'''
from __future__ import division
#import matplotlib
#matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from pylab import setp

import numpy as np
from copy import deepcopy

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
    plt.suptitle(title,fontweight='bold')
    plt.xlabel("Round #")
    if mode == "LAT":
        plt.ylabel("Latency (us)")
    if mode == "TP":
        plt.ylabel("Bandwidth (KB/s)")
    if mode == "IOPS":
        plt.ylabel(mode)
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.07),
               ncol=3, fancybox=True, shadow=True,prop={'size':12})
    plt.savefig(toPlot.getTestname()+'-'+mode+'-stdyStVerPlt.png',dpi=300)
    toPlot.addFigure(toPlot.getTestname()+'-'+mode+'-stdyStVerPlt.png')

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
                #also convert it from us to ms
                readLines[i].append((rndMat[0][i][2]) / 1000)#mean latency
                mixLines[i].append((rndMat[1][i][2]) / 1000)#mean latency
                writeLines[i].append((rndMat[2][i][2]) / 1000)#mean latency
    
    plt.clf()#clear

    #fetch number of rounds, we want to include all rounds
    x = range(rnds + 1)
    max_y = 0
    min_y = 0
    if mode == "IOPS":
        for i in range(len(lines)):
            min_y,max_y = getMinMax(lines[i], min_y, max_y)
            plt.plot(x,lines[i],'o-',label='bs='+pT.SsdTest.IopsTest.bsLabels[i])
    if mode == "LAT":
        for i in range(len(readLines)):
            min_y,max_y = getMinMax(readLines[i], min_y, max_y)
            plt.plot(x,readLines[i],'s-',label='bs='+pT.SsdTest.LatencyTest.bsLabels[i]+' read')
        for i in range(len(mixLines)):
            min_y,max_y = getMinMax(mixLines[i], min_y, max_y)
            plt.plot(x,mixLines[i],'^-',label='bs='+pT.SsdTest.LatencyTest.bsLabels[i]+' mixed')
        for i in range(len(writeLines)):
            min_y,max_y = getMinMax(writeLines[i], min_y, max_y)
            plt.plot(x,writeLines[i],'o-',label='bs='+pT.SsdTest.LatencyTest.bsLabels[i]+' write')
    
    plt.xticks(x)
    plt.suptitle(mode+" Steady State Convergence Plot",fontweight='bold')
    plt.xlabel("Round #")
    plt.ylim((min_y*0.75,max_y*1.25))
    if mode == "LAT":
        plt.ylabel("Latency (ms)")
    if mode == "IOPS":
        plt.ylabel(mode)
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.07),
               ncol=3, fancybox=True, shadow=True,prop={'size':12})
    plt.savefig(toPlot.getTestname()+'-'+mode+'-stdyStConvPlt.png',dpi=300)
    toPlot.addFigure(toPlot.getTestname()+'-'+mode+'-stdyStConvPlt.png')
    
def IOPSplot(toPlot):
    rnds = pT.HddTest.HddTest.maxRnds
    matrices = toPlot.getRndMatrices()
    
    wlds = pT.HddTest.IopsTest.mixWlds
    bsLabels = pT.HddTest.IopsTest.bsLabels
    
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
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.07),
               ncol=3, fancybox=True, shadow=True,prop={'size':12})
    plt.savefig(toPlot.getTestname()+'-IOPSPlt.png',dpi=300)
    toPlot.addFigure(toPlot.getTestname()+'-IOPSPlt.png')
    
def mes2DPlt(toPlot,mode):
    '''
    Generate a measurement 2D plot and the measurement overview table.
    The plot includes:
    -Lines of the workloads
    -Each line consists of the average of IOPS/Latencies per round
    for each block size in the measurement window!
    Therefore the x axes are the block sizes, the plotted lines
    are the different workloads (from 100% read to 100% write). The
    y axes are the IOPS/Latencies over the measurement window for each block sizes
    and workload.
    The figure is saved as SsdTest.Testname-mode-mes2DPlt.png.
    @param toPlot A SsdTest object.
    @param mode A string representing the test mode (IOPS|max-LAT|avg-LAT)
    '''
    mixWLds = []
    mesWin = toPlot.getStdyRnds() #get measurement window, only include these values
    
    if mode == "IOPS":
        wlds = pT.SsdTest.IopsTest.mixWlds
        bsLabels = pT.SsdTest.IopsTest.bsLabels
    if mode == "avg-LAT" or mode == "max-LAT":
        wlds = pT.SsdTest.LatencyTest.mixWlds
        bsLabels = pT.SsdTest.LatencyTest.bsLabels
    
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
        x = getBS(pT.SsdTest.IopsTest.bsLabels)
    if mode == "avg-LAT" or mode == "max-LAT":
        x = getBS(pT.SsdTest.LatencyTest.bsLabels)
        
    max_y = 0
    min_y = 0
    for i in range(len(mixWLds)):
        #for latency convert to ms
        if mode == "avg-LAT" or mode == "max-LAT":
            for v in range(len(mixWLds[i])):
                mixWLds[i][v] = (mixWLds[i][v]) / 1000
                
        min_y,max_y = getMinMax(mixWLds[i], min_y, max_y)
        #the labels are r/w percentage of mixed workload
        plt.plot(x,mixWLds[i],'o-',
                  label=str(wlds[i])+'/'+str(100-wlds[i]))
    
    if mode == 'IOPS':
        plt.yscale('log')
        plt.xscale('log')
        plt.ylabel(mode)
        plt.legend(prop={'size':12})
    if mode == "avg-LAT" or mode == "max-LAT":
        plt.ylabel("Latency (ms)")
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.07),
               ncol=3, fancybox=True, shadow=True,prop={'size':12})
    
    plt.xlabel("Block Size (Byte)")
    #scale axis to min and max
    plt.ylim((min_y*0.75,max_y*1.15))
    plt.xticks(x,bsLabels)
    plt.suptitle(mode+" Measurement Plot",fontweight='bold')
    plt.savefig(toPlot.getTestname()+'-'+mode+'-mes2DPlt.png',dpi=300)
    toPlot.addFigure(toPlot.getTestname()+'-'+mode+'-mes2DPlt.png')
    #For latency and IOPS we also want the overview table
    toPlot.addTable(mixWLds)

def mes3DPlt(toPlot,mode):
    '''
    Generate a measurement 3D plot. This plot depends on the
    mes2DPlt as there the measurement overview table is calculated.
    @param toPlot A SsdTest object.
    @param mode A string representing the test mode (IOPS|max-LAT|avg-LAT)
    '''
    colorTable = ['#0000FF','#008080','#00FFFF','#FFFF00','#00FF00','#FF00FF','#800000']
    if mode == 'IOPS':
        #Iops have only one measurement table
        matrix = deepcopy(toPlot.getTables()[0])
        #reverse to start with 0/100
        matrix.reverse()
        #reverse the block size in each table row, to start with 512B
        for row in matrix:
            row.reverse()
        bsLabels = list(pT.SsdTest.IopsTest.bsLabels)
        mixWlds = list(pT.SsdTest.IopsTest.mixWlds)
    if mode == "avg-LAT" or mode == "max-LAT":
        mixWlds = list(pT.SsdTest.LatencyTest.mixWlds)
        bsLabels = list(pT.SsdTest.LatencyTest.bsLabels)
    
    #define positions for bars
    ypos = np.array([0.25] * len(bsLabels)) 
    xpos = np.arange(0.25, len(bsLabels)+0.25, 1)
    zpos = np.array([0] * len(bsLabels))
    
    #define widht and height (x,y) of bars
    # z will be the measured values
    dx = np.array([0.5] * len(bsLabels))
    dy = np.array([0.5] * len(bsLabels))
    
    plt.clf
    fig = plt.figure()
    ax = Axes3D(fig)
    for j,wl in enumerate(matrix):
        ax.bar3d(xpos,ypos,zpos, dx, dy, wl, color = colorTable[j])
        for pos in range(len(ypos)):
            ypos[pos] += 1
            
    ticksx = np.arange(0.5, len(bsLabels), 1)
    bsLabels.reverse()
    plt.xticks(ticksx, bsLabels)

    ticksy = np.arange(0.5, len(mixWlds), 1)
    mixWlds.reverse()
    plt.yticks(ticksy,mixWlds)
    
    plt.suptitle(mode+" 3D Measurement Plot",fontweight='bold')
    ax.set_xlabel('Block Size (Byte)')
    ax.set_ylabel('R/W Mix%')
    if mode == "avg-LAT" or mode == "max-LAT":
        ax.set_zlabel('Latency (ms)')
    if mode == 'IOPS':
        ax.set_zlabel('IOPS',rotation='vertical')
    plt.savefig(toPlot.getTestname()+'-'+mode+'-mes3DPlt.png',dpi=300)
    toPlot.addFigure(toPlot.getTestname()+'-'+mode+'-mes3DPlt.png')

def latMes3DPlt(toPlot):
    '''
    Generate a measurement 3D plot for latency. This plot depends on the
    mes2DPlt as there the measurement overview table is calculated.
    @param toPlot A SsdTest object.
    '''
    colorTable = ['#0000FF','#008080','#00FFFF']
    mixWlds = list(pT.SsdTest.LatencyTest.mixWlds)
    bsLabels = list(pT.SsdTest.LatencyTest.bsLabels)

    avgMatrix = deepcopy(toPlot.getTables()[0])
    maxMatrix = deepcopy(toPlot.getTables()[1])
    
    #define positions for bars
    ypos = np.array([0.25] * len(bsLabels)) 
    xpos = np.arange(0.25, len(bsLabels)+0.25, 1)
    zpos = np.array([0] * len(bsLabels))
    
    #define widht and height (x,y) of bars
    # z will be the measured values
    dx = np.array([0.5] * len(bsLabels))
    dy = np.array([0.5] * len(bsLabels))
    
    plt.clf()
    fig = plt.figure()
    ax = fig.add_subplot(2, 1, 1, projection='3d')
    for j,wl in enumerate(avgMatrix):
        ax.bar3d(xpos,ypos,zpos, dx, dy, wl, color = colorTable[j])
        for pos in range(len(ypos)):
            ypos[pos] += 1
    ax.xaxis.set_ticks([None]) 
    ax.yaxis.set_ticks([None])
    ax.set_zlabel('Latency (ms)',rotation='vertical')
            
    #Second subplot
    ax = fig.add_subplot(2,1,2, projection='3d')
    #reset ypos
    ypos = np.array([0.25] * len(bsLabels)) 
    for j,wl in enumerate(maxMatrix):
        ax.bar3d(xpos,ypos,zpos, dx, dy, wl, color = colorTable[j])
        for pos in range(len(ypos)):
            ypos[pos] += 1
            
    ticksx = np.arange(0.5, len(bsLabels), 1)
    plt.xticks(ticksx, bsLabels)
    ticksy = np.arange(0.5, len(mixWlds), 1)
    plt.yticks(ticksy,mixWlds)
    

    plt.suptitle("LAT 3D Measurement Plot",fontweight='bold')
    #ax.set_xlabel('Block Size (Byte)')
    ax.set_ylabel('R/W Mix%')
    ax.set_zlabel('Latency (ms)',rotation='vertical')
    plt.savefig(toPlot.getTestname()+'-LAT-mes3DPlt.png',dpi=300)
    toPlot.addFigure(toPlot.getTestname()+'-LAT-mes3DPlt.png')

def getBS(bsLabels):
    '''
    Convert a list of string block size labels to a list of integers.
    This can be handy if the block sizes are needed to be plotted at
    the x axis.
    @return A list of integer block sizes.
    '''
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
    rnds = toPlot.getRnds()
    x = range(rnds + 1)
    
    iops_l = toPlot.getRndMatrices()[0]#first elem in matrix are iops

    plt.clf()#clear plot        
    plt.plot(x,iops_l,'-',label='Avg IOPS')
    plt.ylim(min(iops_l)*0.75,max(iops_l)*1.25)
    #every 10 rounds print the round number
    x = range(0,rnds + 1,50)
    plt.xticks(x)
    plt.suptitle("Write Saturation Test",fontweight='bold')
    plt.xlabel("Round #")
    plt.ylabel("IOPS")
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.07),
               ncol=1, fancybox=True, shadow=True,prop={'size':12})
    plt.savefig(toPlot.getTestname()+'-writeSatIOPSPlt.png',dpi=300)
    toPlot.addFigure(toPlot.getTestname()+'-writeSatIOPSPlt.png')
    
def writeSatLatPlt(toPlot):
    rnds = toPlot.getRnds()
    x = range(rnds + 1)
    
    lats_l = toPlot.getRndMatrices()[1]#second elem in matrix are latencies
    
    #get the average latencies from the lat list (last elem)
    av_lats = []
    for i in lats_l:
        #convert from us to ms
        av_lats.append((i[2]) / 1000)
    
    plt.clf()#clear plot
    plt.plot(x,av_lats,'-',label='Avg latency')
    #set the y axes to start at 3/4 of mininum
    plt.ylim(min(av_lats)*0.75,max(av_lats)*1.25)
    #every 50 rounds print the round number
    x = range(0,rnds + 1,50)
    plt.xticks(x)
    plt.suptitle("Write Saturation Test",fontweight='bold')
    plt.xlabel("Round #")
    plt.ylabel("Latency (ms)")
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.07),
               ncol=1, fancybox=True, shadow=True,prop={'size':12})
    plt.savefig(toPlot.getTestname()+'-writeSatLatPlt.png',dpi=300)
    toPlot.addFigure(toPlot.getTestname()+'-writeSatLatPlt.png')
    
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
    matrices = toPlot.getRndMatrices()
    rnds = len(matrices[0][0])#fetch the number of total rounds
    bsLens = len(matrices)#fetch the number of bs, each row is a bs in the matrix
    
    if dev == "hdd":
        bsLabels = pT.HddTest.TPTest.bsLabels
    else:
        bsLabels = pT.SsdTest.TPTest.bsLabels
    
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
        x = range(0,pT.HddTest.HddTest.maxRnds+1,16)
        plt.xticks(x)
    else:
        x = range(rnds)
        plt.xticks(x)
    if dev == "hdd":
        plt.suptitle("TP "+mode+" Plot",fontweight='bold')    
        plt.xlabel("Number of Area of Device")
    else:
        plt.suptitle("TP "+mode+" Steady State Convergence Plot",fontweight='bold')
        plt.xlabel("Round #")
    plt.ylabel("Bandwidth (KB/s)")
    #scale axis to min and max +- 15%
    plt.ylim((min_y*0.6,max_y*1.15))
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.07),
               ncol=3, fancybox=True, shadow=True,prop={'size':12})
    if dev == "hdd":
        plt.savefig(toPlot.getTestname()+'-'+mode+'-TpPlt.png',dpi=300)
        toPlot.addFigure(toPlot.getTestname()+'-'+mode+'-TpPlt.png')
    else:
        plt.savefig(toPlot.getTestname()+'-TP-'+mode+'-stdyStConvPlt.png',dpi=300)
        toPlot.addFigure(toPlot.getTestname()+'-TP-'+mode+'-stdyStConvPlt.png')

def tpRWStdyStConvPlt(toPlot):
    '''
    Generate one steady state convergence plot for throughput read and write measurements.
    The plot consists of:
    -Measured bandwidths per round per block size
    -All lines are the different block sizes
    -x axes is the number of all rounds
    -y axes is the bw of the corresponding round
    The top plot is write, below read
    The figure is saved as SsdTest.Testname-TP-RW-stdyStConvPlt.png.
    @param toPlot A SsdTest object.
    '''
    matrices = deepcopy(toPlot.getRndMatrices())
    #TODO Change to getRnds()?
    rnds = len(matrices[0][0])#fetch the number of total rounds
    bsLens = len(matrices)#fetch the number of bs, each row is a bs in the matrix
    bsLabels = pT.SsdTest.TPTest.bsLabels
    
    #initialize matrix for plotting
    lines = []
    for i in range(bsLens):
        lines.append([])
    
    #values for scaling the axes
    max_y = 0
    min_y = 0
    
    plt.clf()#clear
    x = range(rnds)#determined by len of matrix
    
    plt.clf
    fig = plt.figure()
    ax = fig.add_subplot(2, 1, 1)
    for i,rndMat in enumerate(matrices):
        row = rndMat[1]#plot the write row
        #convert to MB/s
        for v in range(len(row)):
            row[v] = row[v] / 1024
        #calc min,man to scale axes
        min_y,max_y = getMinMax(row, min_y, max_y)
        ax.plot(x,row,'o-',label='bs='+bsLabels[i])
    plt.xticks(x)
    plt.ylim((0,max_y*1.15))
    plt.legend()
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.10),
               ncol=5, fancybox=True, shadow=True,prop={'size':11})
    plt.ylabel("Write TP (MB/s)")
     
    ax = fig.add_subplot(2, 1, 2)
    for i,rndMat in enumerate(matrices):
        row = rndMat[0]#plot the write row
        #convert to MB/s
        for v in range(len(row)):
            row[v] = row[v] / 1024
        #calc min,man to scale axes
        min_y,max_y = getMinMax(row, min_y, max_y)
        ax.plot(x,row,'o-',label='bs='+bsLabels[i])
    plt.xticks(x)
    plt.ylim((0,max_y*1.15))
    plt.ylabel("Read TP (MB/s)")

    plt.xlabel("Round #")
    plt.suptitle("TP R/W Steady State Convergence Plot",fontweight='bold')

    plt.savefig(toPlot.getTestname()+'-TP-RW-stdyStConvPlt.png',dpi=300)
    toPlot.addFigure(toPlot.getTestname()+'-TP-RW-stdyStConvPlt.png')


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
        for bs in range(len(pT.SsdTest.TPTest.bsLabels)):
            wlds[i].append(0)
    matrices = deepcopy(toPlot.getRndMatrices())    
    
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
    x = getBS(pT.SsdTest.TPTest.bsLabels)
    for i in range(len(wlds)):
        #Convert to MB/s
        for v in range(len(wlds[i])):
            wlds[i][v] = (wlds[i][v]) / 1024
        if i == 0:
            label = "read"
        else:
            label = "write"
        plt.plot(x,wlds[i],'o-',label=label)
    
    plt.xscale('log')
    plt.suptitle("TP Measurement Plot",fontweight='bold')
    plt.xlabel("Block Size (Byte)")
    plt.ylabel("Bandwidth (MB/s)")
    plt.xticks(x,pT.SsdTest.TPTest.bsLabels)
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.07),
               ncol=3, fancybox=True, shadow=True,prop={'size':12})
    plt.savefig(toPlot.getTestname()+'-TP-mes2DPlt.png',dpi=300)
    toPlot.addFigure(toPlot.getTestname()+'-TP-mes2DPlt.png')
    toPlot.addTable(wlds)
    
def ioDepthMes3DPlt(toPlot,rw):
    fig = plt.figure()
    ax = Axes3D(fig)
    
    matrices = toPlot.getRndMatrices()
     
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
    
    #as IOPS are the most for small sizes we reverse the block sizes
    if rw == "randread" or rw == "randwrite":
        matrix.reverse()
    for j,bs in enumerate(matrix):
        if j == 0: bcolor = 'b'
        if j == 1: bcolor = 'g'
        if j == 2: bcolor = 'r'
        if j == 3: bcolor = 'y'
        ax.bar3d(xpos,ypos,zpos, dx, dy, bs,color = bcolor)
        for pos in range(len(xpos)):
            xpos[pos] += 1
            
    ticksx = np.arange(0.5, 4, 1)
    if rw == "randread" or rw == "randwrite":
        labels = list(pT.SsdTest.IodTest.bsLabels)
        labels.reverse()
        plt.xticks(ticksx, labels)
    else:
        plt.xticks(ticksx, pT.SsdTest.IodTest.bsLabels)
    ticksy = np.arange(0.5, 4, 1)
    plt.yticks(ticksy,pT.SsdTest.IodTest.iodDepths)
    plt.suptitle("IOD "+rw+" Measurement Plot",fontweight='bold')
    ax.set_xlabel('Block Size (Byte)')
    ax.set_ylabel('IO Depth')
    if rw == "read" or rw == "write":
        ax.set_zlabel('BW')
    if rw == "randread" or rw == "randwrite":
        ax.set_zlabel('IOPS')
    plt.savefig(toPlot.getTestname()+'-IOD-'+rw+'-mes3DPlt.png',dpi=300)
    toPlot.addFigure(toPlot.getTestname()+'-IOD-'+rw+'-mes3DPlt.png')


    
    
    
    