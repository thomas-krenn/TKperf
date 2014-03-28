'''
Created on Oct 3, 2013

@author: gschoenb
'''
from __future__ import division
import matplotlib.pyplot as plt
import perfTest as pT
import plots.genPlots as pgp

__colorTable__ = ['#0000FF','#008080','#00FFFF','#FFFF00','#00FF00','#FF00FF','#800000']

def compWriteSatIOPSPlt(testsToPlot):
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
        x = range(rnds + 1)
        #first elem in matrix are iops
        iops_l = test.getRndMatrices()[0]
        plt.plot(x,iops_l,'-',label=test.getTestname(), color = __colorTable__[i])
        #fetch new min and max from current test values
        min_y,max_y = pgp.getMinMax(iops_l, min_y, max_y)
        if max(x) > max_x:
            max_x = max(x)
    
    plt.ylim(min_y * 0.75, max_y * 1.25)
    #every 50 rounds print the round number
    x = range(0, max_x, 50)
    plt.xticks(x)
    plt.suptitle("Write Saturation Test",fontweight='bold')
    plt.xlabel("Round #")
    plt.ylabel("Avg. IOPS")
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.07),
               ncol=3, fancybox=True, shadow=True,prop={'size':10})
    plt.savefig('compWriteSatIOPSPlt.png',dpi=300)
    
def compIOPSPlt(testsToPlot):
    """
    Compare multiple tests and create an IOPS plot.
    All test objects in testsToPlot are plotted.
    
    Keyword arguments:
    testsToPlot -- an array of perfTest objects
    """
    plt.clf()#clear plot
    wlds = pT.SsdTest.IopsTest.mixWlds
    bsLabels = pT.SsdTest.IopsTest.bsLabels
    x = range(3)
    width = 1/len(testsToPlot)
    for i in range(len(x)):
        x[i] = x[i] + (i * width)
    print width
    for i,tests in enumerate(testsToPlot):
        test = tests.getTests()['iops']
        pgp.calcMsmtTable(test, 'IOPS')
        mixWLds = test.getTables()[0]
        testIOPS = [mixWLds[0][6],mixWLds[3][6],mixWLds[6][6]]
        print testIOPS
        print x
        plt.bar(x, testIOPS, width,label=test.getTestname(),color = __colorTable__[i])
        x = [v + width for v in x]
    ticksx = [(len(testsToPlot)/2) * width, 1 + width + 0.5, 2 + (2 * width) + 0.5 ]
    labelsx = ['Read','50/50','Write']
    plt.xticks(ticksx, labelsx)
    plt.suptitle("IOPS Measurement Test",fontweight='bold')
    plt.xlabel("R/W Workload")
    plt.ylabel("IOPS 4kB Block Size")
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.07),
               ncol=3,fancybox=True, shadow=True,prop={'size':10})
    plt.savefig('compIOPSPlt.png',dpi=300)
