'''
Created on 09.07.2012

@author: gschoenb
'''
from __future__ import division
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from mpl_toolkits.mplot3d import Axes3D

import numpy as np
from copy import deepcopy

import perfTest.DeviceTests as dt

__matplotVersion__=float('.'.join(matplotlib.__version__.split('.')[0:2]))

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
    x = np.array(toPlot.getStdyState().getStdyRnds())
    #calculate average and its top and bottom limit
    av = []
    avT = []
    avB = []
    av.append(toPlot.getStdyState().getStdyAvg())
    avTop = toPlot.getStdyState().getStdyAvg() * 1.10
    avBot = toPlot.getStdyState().getStdyAvg() * 0.9
    avT.append(avTop)
    avB.append(avBot)
    av = av * len(x)
    avT = avT * len(x)
    avB = avB * len(x)

    plt.clf()#clear
    plt.plot(x,toPlot.getStdyState().getStdyValues(),'o', label=mode, markersize=10)
    plt.plot(x, toPlot.getStdyState().getStdySlope()[0]*x + toPlot.getStdyState().getStdySlope()[1], 'r', label='Slope')
    plt.plot(x, av, '-', color='black',label='Average')
    plt.plot(x, avT, '--', color='black',label='Top')
    plt.plot(x, avB, '--', color='black',label='Bottom')
    
    #set the y axes to start at 3/4 of mininum
    plt.ylim(min(toPlot.getStdyState().getStdyValues())*0.75,max(toPlot.getStdyState().getStdyValues())*1.25)
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
    rnds = toPlot.getStdyState().getRnds()
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
            plt.plot(x,lines[i],'o-',label='bs='+dt.SsdIopsTest.bsLabels[i])
    if mode == "LAT":
        for i in range(len(readLines)):
            min_y,max_y = getMinMax(readLines[i], min_y, max_y)
            plt.plot(x,readLines[i],'s-',label='bs='+dt.SsdLatencyTest.bsLabels[i]+' read')
        for i in range(len(mixLines)):
            min_y,max_y = getMinMax(mixLines[i], min_y, max_y)
            plt.plot(x,mixLines[i],'^-',label='bs='+dt.SsdLatencyTest.bsLabels[i]+' mixed')
        for i in range(len(writeLines)):
            min_y,max_y = getMinMax(writeLines[i], min_y, max_y)
            plt.plot(x,writeLines[i],'o-',label='bs='+dt.SsdLatencyTest.bsLabels[i]+' write')
    
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
    # Generate the measurement table
    calcMsmtTable(toPlot, mode)
    if mode == "IOPS":
        wlds = dt.SsdIopsTest.mixWlds
        bsLabels = dt.SsdIopsTest.bsLabels
        mixWLds = toPlot.getTables()[0]
    if mode == "avg-LAT" or mode == "max-LAT":
        wlds = dt.SsdLatencyTest.mixWlds
        bsLabels = dt.SsdLatencyTest.bsLabels
        if mode == "avg-LAT":
            mixWLds = toPlot.getTables()[0]
        if mode == "max-LAT":
            mixWLds = toPlot.getTables()[1]

    plt.clf()#clear plot
    if mode == "IOPS":
        x = getBS(dt.SsdIopsTest.bsLabels)
    if mode == "avg-LAT" or mode == "max-LAT":
        x = getBS(dt.SsdLatencyTest.bsLabels)
        
    max_y = 0
    min_y = 0
    for i in range(len(mixWLds)):
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

def mes3DPlt(toPlot,mode):
    '''
    Generate a measurement 3D plot. This plot depends on the
    mes2DPlt as there the measurement overview table is calculated.
    @param toPlot A SsdTest object.
    @param mode A string representing the test mode (IOPS)
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
        bsLabels = list(dt.SsdIopsTest.bsLabels)
        mixWlds = list(dt.SsdIopsTest.mixWlds)
    
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
    if __matplotVersion__ >= 1.0:
        ax = fig.gca(projection='3d')
    else:
        ax = Axes3D(fig)
    for j,wl in enumerate(matrix):
        ax.bar3d(xpos,ypos,zpos, dx, dy, wl, color = colorTable[j])
        for pos in range(len(ypos)):
            ypos[pos] += 1
            
    ticksx = np.arange(0.5, len(bsLabels), 1)
    bsLabels.reverse()
    ticksy = np.arange(0.5, len(mixWlds), 1)
    mixWlds.reverse()
    if __matplotVersion__ >= 1.0:
        plt.yticks(ticksy,mixWlds)
        plt.xticks(ticksx, bsLabels)
    else:
        ax.w_xaxis.set_major_locator(ticker.FixedLocator(ticksx))
        ax.w_xaxis.set_ticklabels(bsLabels)
        ax.w_yaxis.set_major_locator(ticker.FixedLocator(ticksy))
        ax.w_yaxis.set_ticklabels(mixWlds)
    
    plt.suptitle(mode+" 3D Measurement Plot",fontweight='bold')
    ax.set_xlabel('Block Size (Byte)')
    ax.set_ylabel('R/W Mix%')
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
    mixWlds = list(dt.SsdLatencyTest.mixWlds)
    bsLabels = list(dt.SsdLatencyTest.bsLabels)

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
    if __matplotVersion__ >= 1.0:
        ax = fig.add_subplot(2, 1, 1, projection='3d')
    else:
        rect = fig.add_subplot(2, 1, 1).get_position()
        ax = Axes3D(fig, rect)
    for j,wl in enumerate(avgMatrix):
        ax.bar3d(xpos,ypos,zpos, dx, dy, wl, color = colorTable[j])
        for pos in range(len(ypos)):
            ypos[pos] += 1
    ax.xaxis.set_ticks([]) 
    ax.yaxis.set_ticks([])
    ax.set_zlabel('Latency (ms)',rotation='vertical')
            
    #Second subplot
    if __matplotVersion__ >= 1.0:
        ax = fig.add_subplot(2,1,2, projection='3d')
    else:
        rect = fig.add_subplot(2, 1, 2).get_position()
        ax = Axes3D(fig, rect)
    #reset ypos
    ypos = np.array([0.25] * len(bsLabels)) 
    for j,wl in enumerate(maxMatrix):
        ax.bar3d(xpos,ypos,zpos, dx, dy, wl, color = colorTable[j])
        for pos in range(len(ypos)):
            ypos[pos] += 1
            
    ticksx = np.arange(0.5, len(bsLabels), 1)
    ticksy = np.arange(0.5, len(mixWlds), 1)
    if __matplotVersion__ >= 1.0:
        plt.xticks(ticksx, bsLabels)
        plt.yticks(ticksy,mixWlds)
    else:
        ax.w_xaxis.set_major_locator(ticker.FixedLocator(ticksx))
        ax.w_xaxis.set_ticklabels(bsLabels)
        ax.w_yaxis.set_major_locator(ticker.FixedLocator(ticksy))
        ax.w_yaxis.set_ticklabels(mixWlds)

    plt.suptitle("LAT 3D Measurement Plot",fontweight='bold')
    #ax.set_xlabel('Block Size (Byte)')
    ax.set_ylabel('R/W Mix%')
    ax.set_zlabel('Latency (ms)',rotation='vertical')
    plt.savefig(toPlot.getTestname()+'-LAT-mes3DPlt.png',dpi=300)
    toPlot.addFigure(toPlot.getTestname()+'-LAT-mes3DPlt.png')

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
    rnds = toPlot.getStdyState().getRnds()#fetch the number of total rounds
    bsLens = len(matrices)#fetch the number of bs, each row is a bs in the matrix
    bsLabels = dt.SsdTPTest.bsLabels
    
    #initialize matrix for plotting
    lines = []
    for i in range(bsLens):
        lines.append([])
    
    #values for scaling the axes
    max_y = 0
    min_y = 0
    
    plt.clf()#clear
    x = range(rnds+1)#ensure to include all rounds
    
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
        row = rndMat[0]#plot the read row
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
    Generate a measurement 2D plot and the measurement overview table for throughput.
    The plot includes:
    -One line for read, one line for write
    -Each line consists of the average of IOPS per round
    for each block size in the measurement window!
    Therefore the x axes are the block sizes, the y axes is
    the average over the measurement window for each block size.
    The figure is saved as SsdTest.Testname-bw-mes2DPlt.png.
    @param toPlot A SsdTest object.
    '''
    calcMsmtTPTable(toPlot)
    wlds = toPlot.getTables()[0]
    #start plotting
    plt.clf()#clear
    x = getBS(dt.SsdTPTest.bsLabels)
    for i in range(len(wlds)):
        if i == 0:
            label = "read"
        else:
            label = "write"
        plt.plot(x,wlds[i],'o-',label=label)

    plt.xscale('log')
    plt.suptitle("TP Measurement Plot",fontweight='bold')
    plt.xlabel("Block Size (Byte)")
    plt.ylabel("Bandwidth (MB/s)")
    plt.xticks(x,dt.SsdTPTest.bsLabels)
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.07),
               ncol=3, fancybox=True, shadow=True,prop={'size':12})
    plt.savefig(toPlot.getTestname()+'-TP-mes2DPlt.png',dpi=300)
    toPlot.addFigure(toPlot.getTestname()+'-TP-mes2DPlt.png')

######### PLOTS FOR HDD TESTS #########
def TPplot(toPlot):
    '''
    Generate a R/W throughput measurement plot for the hdd round results.
    The plot consists of:
    -Measured bandwidths per round, per block size for read and write
    -x axes is the number of carried out rounds
    -y axes is the bandwidth of the corresponding round
    The figure is saved as TPTest.Testname-TP-RW-Plt.png.
    @param toPlot A hdd TPTest object.
    '''
    #As the values are converted to KB, copy the matrices
    matrices = deepcopy(toPlot.getRndMatrices())
    rnds = dt.HddTPTest.maxRnds
    bsLabels = dt.HddTPTest.bsLabels
    
    #values for scaling the axes
    max_y = 0
    min_y = 0
    
    plt.clf()#clear
    x = range(rnds)
    for i,rndMat in enumerate(matrices):
        #convert to MB/S
        for v in range(len(rndMat[0])):
            rndMat[0][v] = (rndMat[0][v]) / 1024
        #plot the read row for current BS
        min_y,max_y = getMinMax(rndMat[0], min_y, max_y)
        plt.plot(x,rndMat[0],'o-',label='read bs='+bsLabels[i])
        #plot the write row for current BS
        for v in range(len(rndMat[1])):
            rndMat[1][v] = (rndMat[1][v]) / 1024
        min_y,max_y = getMinMax(rndMat[1], min_y, max_y)
        plt.plot(x,rndMat[1],'o-',label='write bs='+bsLabels[i])
    
    x = range(0,rnds+1,16)
    plt.xticks(x)
    plt.suptitle("TP Measurement Plot",fontweight='bold')    
    plt.xlabel("Area of Device (in rounds)")
    plt.ylabel("Bandwidth (MB/s)")
    #scale axis to min and max +- 15%
    plt.ylim((min_y*0.6,max_y*1.15))
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.07),
               ncol=2, fancybox=True, shadow=True,prop={'size':12})
    plt.savefig(toPlot.getTestname()+'-TP-RW-Plt.png',dpi=300)
    toPlot.addFigure(toPlot.getTestname()+'-TP-RW-Plt.png')

def IOPSplot(toPlot):
    '''
    Generate the IOPS plot for a hdd performance test. The plot consists
    of plotting the IOPS results from the 128 rounds that have been carried
    out. In each round the mixed workloads and all block sizes are plotted.
    @param toPlot An hdd IopsTest object.
    '''
    rnds = dt.HddIopsTest.maxRnds
    matrices = toPlot.getRndMatrices()
    
    wlds = dt.HddIopsTest.mixWlds
    bsLabels = dt.HddIopsTest.bsLabels
    
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
    x = range(0,rnds + 1,16)
    plt.xticks(x)
    plt.suptitle("IOPS Measurement Plot",fontweight='bold')
    plt.xlabel("Area of Device (in rounds)")
    plt.ylabel("IOPS")
    #plt.yscale('log')
    plt.ylim((min_y*0.75,max_y*1.25))
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.07),
               ncol=3, fancybox=True, shadow=True,prop={'size':12})
    plt.savefig(toPlot.getTestname()+'-IOPSPlt.png',dpi=300)
    toPlot.addFigure(toPlot.getTestname()+'-IOPSPlt.png')
    
def TPBoxPlot(toPlot):
    '''
    Generate a R/W throughput box plot for the hdd round results.
    The plot consists of:
    -Measured bandwidths per round, per block size for read and write
    -x axes is the number of carried out rounds
    -y axes is the bandwidth of the corresponding round
    The figure is saved as TPTest.Testname-TP-RW-Plt.png.
    @param toPlot A hdd TPTest object.
    '''
    #As the values are converted to KB, copy the matrices
    matrices = deepcopy(toPlot.getRndMatrices())
    bsLabels = dt.HddTPTest.bsLabels
    
    plt.clf()#clear
    boxes = []
    min_y = 0
    max_y = 0
    for bsRows in matrices:
        #For each BS we have read and write, both rows have equal length
        for v in range(len(bsRows[0])):
            bsRows[0][v] = (bsRows[0][v]) / 1024
            bsRows[1][v] = (bsRows[1][v]) / 1024
        boxes.append(bsRows[0])
        min_y,max_y = getMinMax(bsRows[0], min_y, max_y)
        boxes.append(bsRows[1])
        min_y,max_y = getMinMax(bsRows[1], min_y, max_y)
    #Length of BS per R/W
    pos = range(len(bsLabels) * 2)
    plt.boxplot(boxes,positions=pos)
    labels = []
    for l in bsLabels:
        labels.append(l + ' (R)')
        labels.append(l + ' (W)')
    plt.xticks(pos,labels)
    plt.xlabel('BS (Mode)')
    plt.suptitle("TP Boxplot",fontweight='bold')    
    plt.ylabel("Bandwidth (MB/s)")
    #scale axis to min and max +- 15%
    plt.ylim((min_y*0.7,max_y*1.10))
    #Draw some fake data for legend
    hB, = plt.plot([1,1],'b-')
    hR, = plt.plot([1,1],'r-')
    plt.legend((hB, hR),('Quartiles', 'Median'),loc='upper center', bbox_to_anchor=(0.5, 1.07),
               ncol=2, fancybox=True, shadow=True,prop={'size':12})
    hB.set_visible(False)
    hR.set_visible(False)
    plt.savefig(toPlot.getTestname()+'-TP-Boxplt.png',dpi=300)
    toPlot.addFigure(toPlot.getTestname()+'-TP-Boxplt.png')

######### HELPER FUNCTIONS TO GENERATE PLOTS #########
def calcMsmtTable(toPlot,mode):
    '''
    Generate the measurement overview table for IOPS and Latency. The table is
    an overview over the average values in the measurement window. For latency
    the values are converted from us to ms also.
    @param toPlot A SsdTest object.
    @param mode A string representing the test mode (IOPS|max-LAT|avg-LAT)
    '''
    mixWLds = []
    mesWin = toPlot.getStdyState().getStdyRnds() #get measurement window, only include these values
    if mode == "IOPS":
        wlds = dt.SsdIopsTest.mixWlds
        bsLabels = dt.SsdIopsTest.bsLabels
    if mode == "avg-LAT" or mode == "max-LAT":
        wlds = dt.SsdLatencyTest.mixWlds
        bsLabels = dt.SsdLatencyTest.bsLabels

    #each row will be a workload percentage
    for i in range(len(wlds)):
        mixWLds.append([])
        #in each row will be the different block sizes
        for bs in range(len(bsLabels)):
            mixWLds[i].append(0)
    matrices = toPlot.getRndMatrices()

    #as j does not necessarily start from 0, we need k
    #to calculate the average iteratively
    k = 0
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
                        mixWLds[i][bs] *= k
                        if mode == "IOPS":
                            mixWLds[i][bs] += row[bs]#IOPS
                        if mode == "avg-LAT":
                            mixWLds[i][bs] += row[bs][2]#mean latency
                        mixWLds[i][bs] = (mixWLds[i][bs]) / (k+1)
                else:
                    if mode == "IOPS":
                        mixWLds[i][bs] = row[bs]#IOPS
                    if mode == "max-LAT":
                        mixWLds[i][bs] = row[bs][1]#max latency
                    if mode == "avg-LAT":
                        mixWLds[i][bs] = row[bs][2]#mean latency
        k += 1
    #for latency convert to ms
    for i in range(len(mixWLds)):
        if mode == "avg-LAT" or mode == "max-LAT":
            for v in range(len(mixWLds[i])):
                mixWLds[i][v] = (mixWLds[i][v]) / 1000
    toPlot.addTable(mixWLds)

def calcMsmtTPTable(toPlot):
    '''
    Generate the measurement overview table for Throughput. The table is
    an overview over the average values in the measurement window. 
    @param toPlot A SsdTest object.
    '''
    wlds = [] #read and write workload mode
    #one row for read, one for write
    for i in range(2):
        wlds.append([])
        #in each row will be the different block sizes
        for bs in range(len(dt.SsdTPTest.bsLabels)):
            wlds[i].append(0)
    matrices = deepcopy(toPlot.getRndMatrices())
    #each row of the matrix is a block size
    for j,bs in enumerate(matrices):
        #each block size has read and write
        for i,row in enumerate(bs):
            #as rnd does not need to start at 0
            #we need k to calculate average
            k = 0
            #read and write have their round values
            for rnd in toPlot.getStdyState().getStdyRnds():
                #calculate average iteratively
                if wlds[i][j] != 0:
                    wlds[i][j] *= k
                    wlds[i][j] += row[rnd]
                    wlds[i][j] = (wlds[i][j]) / (k+1)
                else:
                    wlds[i][j] = row[rnd]
                k += 1
    #Convert to MB/s
    for i in range(len(wlds)):
        for v in range(len(wlds[i])):
            wlds[i][v] = (wlds[i][v]) / 1024
    toPlot.addTable(wlds)

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
    #This should not happen for performance tests under normal circumstances
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
    
    