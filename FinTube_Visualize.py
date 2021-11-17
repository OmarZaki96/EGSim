# -*- coding: utf-8 -*-
"""
Created on Mon Dec 28 00:26:24 2020

@author: OmarZaki
"""
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import sys
import numpy as np

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self,Parameters,parent=None,dpi=300):
        Ntube = Parameters[0]
        Nbank = Parameters[1]
        Do = Parameters[2]
        Pl = Parameters[3]
        Pt = Parameters[4]
        Staggering = Parameters[5]
        fig = Draw(Ntube,Nbank,Do,Pl,Pt,Staggering)
        super(MplCanvas,self).__init__(fig)

class Visualise_Window(QDialog):
    def __init__(self, parent=None):
        # first UI
        super(Visualise_Window, self).__init__(parent)
        self.setMaximumSize(500, 500) 
    
    def Draw_tubes(self,Ntube,Nbank,Do,Pl,Pt,Staggering):
        Parameters = [Ntube,Nbank,Do,Pl,Pt,Staggering]
        sc = MplCanvas(Parameters,self,300)

        toolbar = NavigationToolbar(sc, self)

        layout = QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(sc)

        self.setLayout(layout)

def annotate_dim(ax,xyfrom,xyto,fontsize,text=None):

    if text is None:
        number = np.sqrt( (xyfrom[0]-xyto[0])**2 + (xyfrom[1]-xyto[1])**2)
        if round(number,4) == 0:
            if round(number,6) == 0:
                number = round(number,8)
            else:
                number = round(number,6)
        else:
            number = round(number,4)
        text = str(number)

    ax.annotate("",xyfrom,xyto,arrowprops=dict(arrowstyle='|-|'),annotation_clip=False)
    ax.text(xyto[0]*1.05,(xyfrom[1]+xyto[1])/2,text+" m",fontsize=fontsize)

def Draw(Ntube,Nbank,Do,Pl,Pt,Staggering):
    Centers = []
    if Staggering == "inline":
        maximum = (Ntube-0.5) * Pt
        minimum = -Pt/2
        for i in range(Ntube):
            for j in range(Nbank):
                Centers.append((j*Pl,i*Pt))
    elif Staggering == 'AaA':
        maximum = (Ntube) * Pt - Do/2
        minimum = -Do/2
        for i in range(Ntube):
            for j in range(Nbank):
                if j%2==1:
                    Centers.append((j*Pl,i*Pt))
                else:
                    Centers.append((j*Pl,(i+0.5)*Pt))
    elif Staggering == 'aAa':
        maximum = (Ntube-0.5) * Pt+Do/2
        minimum = -Pt/2+Do/2
        for i in range(Ntube):
            for j in range(Nbank):
                if j%2==0:
                    Centers.append((j*Pl,i*Pt))
                else:
                    Centers.append((j*Pl,(i+0.5)*Pt))
    Tubes = []
    for x,y in Centers:
        Tubes.append(plt.Circle((x, y), Do/2,clip_on=False,color='black',fill=False))
    
    fig, ax = plt.subplots() # note we must use plt.subplots, not plt.subplot
    for Tube in Tubes:
        ax.add_artist(Tube)
    ax.arrow(-maximum/2,maximum/2,maximum/4,0,width=maximum/150,color="black",clip_on=False)
    ax.annotate("Air Flow",[-maximum*0.5,maximum/2+maximum/50],annotation_clip=False,fontsize="large")
    ax.plot([-Pl/2, (Nbank-0.5) * Pl],[minimum,minimum],color='black',linewidth=1,clip_on=False)
    ax.plot([-Pl/2,-Pl/2],[minimum,maximum],color='black',linewidth=1,clip_on=False)
    ax.plot([(Nbank-0.5) * Pl,(Nbank-0.5) * Pl],[minimum,maximum],color='black',linewidth=1,clip_on=False)
    ax.plot([-Pl/2, (Nbank-0.5) * Pl],[maximum,maximum],color='black',linewidth=1,clip_on=False)
    ax.set_aspect(1.0)
    ax.autoscale(enable=True, axis='y')
    annotate_dim(ax,(0,maximum*1.08),(Pl,maximum*1.08),"medium")
    annotate_dim(ax,(Nbank*Pl*1.1,(Ntube-2)*Pt),(Nbank*Pl*1.1,(Ntube-1)*Pt),'medium')
    ax.set_axis_off()
    return fig

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Visualise_Window()
    w.Draw_tubes(5,5,0.008,2*0.0127,3*0.0127,'aAa')
    w.exec_()