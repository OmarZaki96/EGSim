from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
import os, sys
import CoolProp as CP
from unit_conversion import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.cm as cm
from matplotlib.colors import Normalize

class Sub_HX_UI_Widget(QWidget):
    def __init__(self,parent=None):
        super(Sub_HX_UI_Widget, self).__init__(parent)
        
        self.layout_i = QHBoxLayout()
        self.visualization = Tubes_Visualize([1,1,'inline',None,0,None])
        
        self.table = Sub_HX_Table(self)
        
        self.layout_i.addWidget(self.visualization)
        self.layout_i.addWidget(self.table)
        
        layout = QVBoxLayout()
        self.Enable = QCheckBox("Enable sub heat exchanger")
        self.Enable.stateChanged.connect(self.show_hide)
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        layout.addWidget(self.Enable)
        layout.addWidget(line)
        layout.addLayout(self.layout_i)
        layout2 = QHBoxLayout()
        layout2.addStretch()
        self.label = QLabel()
        self.label.setTextFormat(Qt.RichText)
        self.label.setText("<ul><li>Refrigerant enter the first tube in the circuit where start position is 0.0.</li><li>if you want to disable a tube, enter 0 for both the start and the end points.</li><li>Note that you don't have to take into account that reducing tube length or disabling tubes will affect the amount of air flow rate. This has already been taken into account.</li></ul>")
        font = self.label.font()
        font.setPointSize(12)
        self.label.setFont(font)
        layout2.addWidget(self.label)
        layout2.addStretch()
        self.line = QFrame()
        self.line.setFrameShape(QFrame.HLine)
        layout.addWidget(self.line)
        layout.addLayout(layout2)
        layout.addStretch()
        self.setLayout(layout)
        self.show_hide()
        
    def show_hide(self):
        condition = self.Enable.checkState()
        self.table.setVisible(condition)
        self.visualization.setVisible(condition)
        self.label.setVisible(condition)
        self.line.setVisible(condition)

    def update(self,Nbank,Ntubes_per_bank,staggering_index,tube_length,tube_length_index):
        if staggering_index == 0:
            staggering = "inline"
        elif staggering_index == 1:
            staggering = "AaA"
        elif staggering_index == 2:
            staggering = "aAa"
        self.Nbank = Nbank
        self.Ntubes_per_bank = Ntubes_per_bank
        self.staggering_index = staggering_index
        self.tube_length = tube_length
        self.tube_length_index = tube_length_index
        self.table.update_dimensions(Nbank,Ntubes_per_bank,tube_length,tube_length_index)
        self.layout_i.removeWidget(self.visualization)
        self.layout_i.removeWidget(self.table)
        plt.close('all')
        self.visualization.deleteLater()
        self.visualization = None

        try:
            values = self.table.get_values_without_validation()
            if values[0]:
                values = values[1]
            else:
                raise
            tube_length = self.tube_length
        except:
            values = None
            tube_length = 0

        self.visualization = Tubes_Visualize([self.Nbank,self.Ntubes_per_bank,staggering,values,tube_length,None])
        
        self.layout_i.addWidget(self.visualization)

        self.layout_i.addWidget(self.table)
        self.show_hide()

    def update_figure(self,active_tube,old_tube):
        if active_tube != None:
            active_tube = active_tube.row()
        if self.staggering_index == 0:
            staggering = "inline"
        elif self.staggering_index == 1:
            staggering = "AaA"
        elif self.staggering_index == 2:
            staggering = "aAa"
        
        self.layout_i.removeWidget(self.visualization)
        self.layout_i.removeWidget(self.table)
        plt.close('all')
        self.visualization.deleteLater()
        self.visualization = None

        try:
            values = self.table.get_values_without_validation()
            if values[0]:
                values = values[1]
            else:
                raise
            tube_length = length_unit_converter(self.tube_length,self.tube_length_index)
        except:
            values = None
            tube_length = 0
            
        self.visualization = Tubes_Visualize([self.Nbank,self.Ntubes_per_bank,staggering,values,tube_length,active_tube])
        
        self.layout_i.addWidget(self.visualization)

        self.layout_i.addWidget(self.table)

    def get_values(self):
        return self.table.get_values()

    def load_values(self,values):
        self.table.load_values(values)

class Sub_HX_Table(QTableWidget):
    def __init__(self, parent=None):
        self.parent = parent
        super(Sub_HX_Table, self).__init__(parent)
        self.setRowCount(0)
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["Tube start point","Tube end point","unit"])
        class MyDelegate(QItemDelegate):

            def createEditor(self, parent, option, index):
                return_object = QLineEdit(parent)
                only_number = QRegExpValidator(QRegExp("([0-9]+([.][0-9]*)?|[.][0-9]+)"))
                return_object.setValidator(only_number)
                return return_object
        delegate = MyDelegate()
        self.setItemDelegate(delegate)
        self.currentItemChanged.connect(self.parent.update_figure)
        
    def update_dimensions(self,Nbank,Ntubes_per_bank,tube_length,tube_length_index):            
        self.setRowCount(0)
        self.tube_length = length_unit_converter(tube_length,tube_length_index)
        self.setRowCount(Ntubes_per_bank*Nbank)
        units = ['m','cm','mm','ft','in']
        for i in range(Ntubes_per_bank*Nbank):
            units_combo = QComboBox()
            units_combo.addItems(units)
            units_combo.currentIndexChanged.connect(self.get_values)
            self.setCellWidget(i,2,units_combo)
        
        self.setVerticalHeaderLabels([str(i+1) for i in range(Ntubes_per_bank*Nbank)])
        for i in range(Nbank):
            for j in range(Ntubes_per_bank):
                self.setItem(i*Ntubes_per_bank+j,0,QTableWidgetItem("0.0"))
                self.setItem(i*Ntubes_per_bank+j,1,QTableWidgetItem("%.5g" % tube_length))
                self.cellWidget(i*Ntubes_per_bank+j,2).setCurrentIndex(tube_length_index)

        for i in range(1,Nbank-1):
            for j in range(Ntubes_per_bank):
                item = self.item(i*Ntubes_per_bank+j,0)
                item.setFlags(item.flags() ^ Qt.ItemIsEnabled)
                item = self.item(i*Ntubes_per_bank+j,1)
                item.setFlags(item.flags() ^ Qt.ItemIsEnabled)
                self.cellWidget(i*Ntubes_per_bank+j,2).setEnabled(False)
                
    def get_values(self):
        values = []
        for i in range(self.rowCount()):
            unit_index = self.cellWidget(i,2).currentIndex()
            tube = i + 1            
            try:
                start = float(self.item(i,0).text())
                start = length_unit_converter(start,unit_index)
            except:
                message = "Error in Sub Heat exchanger. Something is wrong with start poing of tube number "+str(tube)
                return [0,message]
            try:
                end = float(self.item(i,1).text())
                end = length_unit_converter(end,unit_index)
            except:
                message = "Error in Sub Heat exchanger. Something is wrong with end poing of tube number "+str(tube)
                return [0,message]

            if end > self.tube_length:
                message = "Error in Sub Heat exchanger. End point can't be larger than tube length for tube number "+str(tube)
                return [0,message]

            if start > end:
                message = "Error in Sub Heat exchanger. Start point can't be larger than end point for tube number "+str(tube)
                return [0,message]
            values.append([tube,start,end])
        values = np.array(values)
        if all(values[:,1] == 0) and all(values[:,2] == 0):
            message = "Error in Sub Heat exchanger. You can't disable all tubes of heat exchanger."
            return [0,message]
        return [1,values]

    def get_values_without_validation(self):
        values = []
        for i in range(self.rowCount()):
            unit_index = self.cellWidget(i,2).currentIndex()
            tube = i + 1            
            try:
                start = float(self.item(i,0).text())
                start = length_unit_converter(start,unit_index)
            except:
                message = "Error in Sub Heat exchanger. Something is wrong with start poing of tube number "+str(tube)
                return [0,message]
            try:
                end = float(self.item(i,1).text())
                end = length_unit_converter(end,unit_index)
            except:
                message = "Error in Sub Heat exchanger. Something is wrong with end poing of tube number "+str(tube)
                return [0,message]

            values.append([tube,start,end])
        values = np.array(values)
        return [1,values]

    def load_values(self,values):
        values = np.array(values)
        self.setRowCount(len(values))
        for i in range(self.rowCount()):
            start = float(values[i,1]) * 1000.0
            end = float(values[i,2]) * 1000.0
            self.setItem(i,0,QTableWidgetItem("%.5g" % start))
            self.setItem(i,1,QTableWidgetItem("%.5g" % end))
    
    def raise_error_message(self,message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(message)
        msg.setWindowTitle("Error!")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
                
class Tubes_Visualize(FigureCanvasQTAgg):
    def __init__(self,Parameters,parent=None,dpi=300):
        Ntube = Parameters[1]
        Nbank = Parameters[0]
        Staggering = Parameters[2]
        values = Parameters[3]
        Tube_length = Parameters[4]
        active_tube = Parameters[5]
        Do = 0.01
        Pl = 0.02
        Pt = 0.02
        self.fig, self.ax = Draw(Ntube,Nbank,Do,Pl,Pt,Staggering,values,Tube_length,active_tube)
        super(Tubes_Visualize,self).__init__(self.fig)

def Draw(Ntube,Nbank,Do,Pl,Pt,Staggering, values=None, Tube_length=None,active_tube=None):
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
    Centers = np.array(Centers)
    Centers = Centers[np.lexsort((-1*Centers[:,1],Centers[:,0]))]
    if not values is None:
        cmap = cm.Greens
        norm = Normalize(0, 1.3)
        if Tube_length > 0:
            print(float((values[values[:,0] == i+1,2])))
            print(Tube_length)
            Tubes_color_index = [float((values[values[:,0] == i+1,2] - values[values[:,0] == i+1,1])/Tube_length) for i in range(len(Centers))]
        else:
            Tubes_color_index = [1.0 for i in range(len(Centers))]   
    else:
        Tubes_color_index = None
    
    for i,(x,y) in enumerate(Centers):
        if active_tube != None and i == active_tube:
            Tubes.append(plt.Circle((x, y), Do/2,clip_on=False,color='black',fill=True))                
        else:
            if not Tubes_color_index is None:
                if Tubes_color_index[i] != 0:
                    Tubes.append(plt.Circle((x, y), Do/2,clip_on=False,color='black',fill=False))
                    if 0 < Tubes_color_index[i] <= 1:
                        Tubes.append(plt.Circle((x, y), Do/2,clip_on=False,color=cmap(norm(Tubes_color_index[i])),fill=True))
                    else:
                        Tubes.append(plt.Circle((x, y), Do/2,clip_on=False,color='red',fill=True))
            else:
                Tubes.append(plt.Circle((x, y), Do/2,clip_on=False,color='black',fill=False))
                            
    fig = plt.figure() # create the canvas for plotting
    ax = plt.subplot(1,1,1) 
    for Tube in Tubes:
        ax.add_artist(Tube)
    for i,(x,y) in enumerate(Centers):
        if not Tubes_color_index is None:
            if Tubes_color_index[i] > 0:
                ax.text(x, y, str(i+1),horizontalalignment='center', verticalalignment='center')
        else:
            ax.text(x, y, str(i+1),horizontalalignment='center', verticalalignment='center')
    ax.arrow(-maximum/2,maximum/2,maximum/4,0,width=maximum/150,color="black",clip_on=False)
    ax.annotate("Air Flow",[-maximum*0.5,maximum/2+maximum/50],annotation_clip=False,fontsize="large")
    ax.plot([-Pl/2, (Nbank-0.5) * Pl],[minimum,minimum],color='black',linewidth=1,clip_on=False)
    ax.plot([-Pl/2,-Pl/2],[minimum,maximum],color='black',linewidth=1,clip_on=False)
    ax.plot([(Nbank-0.5) * Pl,(Nbank-0.5) * Pl],[minimum,maximum],color='black',linewidth=1,clip_on=False)
    ax.plot([-Pl/2, (Nbank-0.5) * Pl],[maximum,maximum],color='black',linewidth=1,clip_on=False)
    ax.set_aspect(1.0)
    ax.autoscale(enable=True, axis='y')
    ax.set_axis_off()
    return fig, ax

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = QDialog()
    layout = QHBoxLayout()
    widget = Sub_HX_UI_Widget()
    widget.update(3,12,0,1.2,0)
    layout.addWidget(widget)
    w.setLayout(layout)
    w.exec_()