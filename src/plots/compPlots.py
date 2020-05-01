'''
Created on Oct 3, 2013

@author: gschoenb
'''

import plots.genPlots as pgp
import matplotlib.pyplot as plt

__colorTable__ = ['#0000FF','#32cd32','#ffff00','#00ffff','#b22222','#9932cc','#ff4500']

def compWriteSatIOPSPlt(testsToPlot, subfolder=None):
    """
    Compare multiple tests and create a write saturation IOPS plot.
    All test objects in testsToPlot are plotted.
    
    Keyword arguments:
    testsToPlot -- an array of perfTest objects
    """
    plt.clf()#clear plot
    min_y = 0
    max_y = 0
    max_x = 0
    for i,tests in enumerate(testsToPlot):
        test = tests.getTests()['writesat']
        rnds = test.getRnds()
        x = list(range(rnds + 1))
        #first elem in matrix are iops
        iops_l = test.getRndMatrices()[0]
        plt.plot(x,iops_l,'-',label=test.getTestname(), color = __colorTable__[i])
        #fetch new min and max from current test values
        min_y,max_y = pgp.getMinMax(iops_l, min_y, max_y)
        if max(x) > max_x:
            max_x = max(x)
    
    plt.ylim(min_y * 0.75, max_y * 1.25)
    #every 50 rounds print the round number
    x = list(range(0, max_x, 50))
    plt.xticks(x)
    plt.suptitle("Write Saturation Test",fontweight='bold')
    plt.xlabel("Round #")
    plt.ylabel("Avg. IOPS")
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.07),
               ncol=3, fancybox=True, shadow=True,prop={'size':10})
    if subfolder == None:
        plt.savefig('compWriteSatIOPSPlt.png',dpi=300)
    else:
        plt.savefig(subfolder+'/compWriteSatIOPSPlt.png',dpi=300)

def compILPlt(testsToPlot, mode, subfolder=None):
    """
    Compare multiple tests and create an IOPS or Latency plot.
    All test objects in testsToPlot are plotted.
    
    Keyword arguments:
    testsToPlot -- an array of perfTest objects
    mode -- the desired test mode (IOPS or Latency)
    """
    plt.clf()#clear plot
    x = list(range(3))
    width = 1/len(testsToPlot)
    max_y = 0
    for i in range(len(x)):
        x[i] = x[i] + (i * width)
    for i,tests in enumerate(testsToPlot):
        if mode == "IOPS":
            test = tests.getTests()['iops']
            pgp.calcMsmtTable(test, 'IOPS')
        if mode == "LAT":
            test = tests.getTests()['lat']
            pgp.calcMsmtTable(test, 'avg-LAT')
        mixWLds = test.getTables()[0]
        if mode == "IOPS":
            testVal = [mixWLds[0][6],mixWLds[3][6],mixWLds[6][6]]
        if mode == "LAT":
            testVal = [mixWLds[0][1],mixWLds[1][1],mixWLds[2][1]]
        plt.bar(x, testVal, width,label=test.getTestname(),color = __colorTable__[i])
        x = [v + width for v in x]
        if max(testVal) > max_y:
            max_y = max(testVal)
    ticksx = [(len(testsToPlot)/2) * width, 1 + width + 0.5, 2 + (2 * width) + 0.5 ]
    if mode == "IOPS":
        labelsx = ['Read','50/50','Write']
    if mode == "LAT":
        labelsx = ['Read','65/35','Write']
    plt.xticks(ticksx, labelsx)
    plt.ylim(0, max_y * 1.15)
    if mode == "IOPS":
        title = "IOPS"
        plt.ylabel("Avg. " + title + " at 4k Block Size")
    if mode == "LAT":
        title = "LAT"
        plt.ylabel("Avg. "+ title + " (ms) at 4k Block Size")
    plt.suptitle(title + " Measurement Test",fontweight='bold')
    plt.xlabel("R/W Workload")
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.07),
               ncol=3,fancybox=True, shadow=True,prop={'size':10})
    if subfolder == None:
        plt.savefig('comp'+title+'Plt.png',dpi=300)
    else:
        plt.savefig(subfolder+'/comp'+title+'Plt.png',dpi=300)

def compTPPlt(testsToPlot, subfolder=None):
    """
    Compare multiple tests and create a throughput plot.
    All test objects in testsToPlot are plotted.
    
    Keyword arguments:
    testsToPlot -- an array of perfTest objects
    """
    plt.clf()#clear plot
    height = 1/len(testsToPlot)
    ticksy = [(len(testsToPlot)/2) * height, 1 + height + 0.5, 2 + (2 * height) + 0.5 ]
    labelsy = ['8k','64k','1024k']
    max_x = 0
    fig = plt.figure()
    # Plot read throughput
    ax = fig.add_subplot(2, 1, 2)
    y = list(range(3))
    for i in range(len(y)):
        y[i] = y[i] + (i * height)
    for i,tests in enumerate(testsToPlot):
        test = tests.getTests()['tp']
        pgp.calcMsmtTPTable(test)
        wlds = test.getTables()[0]
        testRTP = [wlds[0][2],wlds[0][1],wlds[0][0]]
        ax.barh(y, testRTP, height, label=test.getTestname(),color = __colorTable__[i])
        y = [v + height for v in y]
        if max(testRTP) > max_x:
            max_x = max(testRTP)
    plt.xlabel("Read Bandwidth (MB/s)")
    plt.xlim(0,max_x*1.05)
    plt.yticks(ticksy, labelsy)
    plt.ylabel("Block Size (Byte)")
    plt.grid()
    
    # Plot write throughput
    ax = fig.add_subplot(2, 1, 1)
    y = list(range(3))
    for i in range(len(y)):
        y[i] = y[i] + (i * height)
    for i,tests in enumerate(testsToPlot):
        test = tests.getTests()['tp']
        wlds = test.getTables()[0]
        testRTP = [wlds[1][2],wlds[1][1],wlds[1][0]]
        ax.barh(y, testRTP, height, label=test.getTestname(),color = __colorTable__[i])
        y = [v + height for v in y]
    plt.xlabel("Write Bandwidth (MB/s)")
    plt.xlim(0,max_x*1.05)
    plt.yticks(ticksy, labelsy)
    plt.ylabel("Block Size (Byte)")
    plt.grid()
    plt.legend()
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.18),
       ncol=3,fancybox=True, shadow=True,prop={'size':9})
    plt.suptitle("TP R/W Measurement Test",fontweight='bold')
    if subfolder == None:
        plt.savefig('compTPPlt.png',dpi=300)
    else:
        plt.savefig(subfolder+'/compTPPlt.png',dpi=300)
