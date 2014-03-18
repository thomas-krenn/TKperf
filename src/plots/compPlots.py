'''
Created on Oct 3, 2013

@author: gschoenb
'''
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import perfTest as pT
import plots.genPlots as pgp


def compWriteSatIOPSPlt(testsToPlot):
    """
    Compare multiple tests and create a write saturation IOPS plot.
    All test objects in testsToPlot are plotted.
    
    Keyword arguments:
    testsToPlot -- an array of perfTest objects
    """
    #fetch number of rounds, we want to include all rounds
    #as stdy state was reached at rnds, it must be included
    plt.clf()#clear plot
    min_y = 0
    max_y = 0
    max_x = 0
    for tests in testsToPlot:
        test = tests.getTests()['writesat']
        rnds = test.getRnds()
        x = range(rnds + 1)
        #first elem in matrix are iops
        iops_l = test.getRndMatrices()[0]
        plt.plot(x,iops_l,'-',label=test.getTestname()+'-Avg IOPS')
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
    plt.ylabel("IOPS")
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.07),
               ncol=1, fancybox=True, shadow=True,prop={'size':10})
    plt.savefig('compWriteSatIOPSPlt.png',dpi=300)
    #toPlot.addFigure(toPlot.getTestname()+'-writeSatIOPSPlt.png')