'''
Created on Oct 3, 2013

@author: gschoenb
'''
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import perfTest as pT


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