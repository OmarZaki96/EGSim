from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import numpy as np

class tubes_circuitry_window(QDialog):
    def __init__(self,Ntubes_per_bank,N_banks,parent=None):
        QDialog.__init__(self)
        self.Ntubes_per_bank = Ntubes_per_bank
        self.N_banks = N_banks
        # setting up UI
        self.tubes_widget = tubes_circuitry_widget(Ntubes_per_bank,N_banks,self)
        self.scroll = QScrollArea()
        self.scroll.setWidget(self.tubes_widget)
        layout = QVBoxLayout()
        layout.addWidget(self.scroll)
        h_layout = QHBoxLayout()
        self.ok_button = QPushButton("Ok")
        self.clear_button = QPushButton("clear")
        h_layout.addStretch()
        h_layout.addWidget(self.clear_button)
        h_layout.addStretch()
        h_layout.addWidget(self.ok_button)
        h_layout.addStretch()
        group = QGroupBox("Hints")
        dummy_layout = QVBoxLayout()
        hint = QLabel("<ul><li>To select tube to be next in order, click left button on mouse.</li><li>to remove selection from a tube, click right button on mouse.</li><li>Air direction is from the left</li></ul>")
        hint.setTextFormat(Qt.RichText)
        dummy_layout.addWidget(hint)
        group.setLayout(dummy_layout)
        layout.addWidget(group)
        layout.addLayout(h_layout)
        self.setLayout(layout)
        
        # connections
        self.ok_button.clicked.connect(self.ok_button_clicked)
        self.clear_button.clicked.connect(self.clear_button_clicked)
        
    def ok_button_clicked(self):
        circuit_array = self.tubes_widget.circuit_array
        if all(circuit_array[:,1]):
            circuit_array = circuit_array[circuit_array[:,1].argsort()]
            self.circuitry = [self.Ntubes_per_bank,self.N_banks,list(circuit_array[:,0] + 1)]
            self.close()
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("You didn't choose all tubes, some of them are missing")
            msg.setWindowTitle("Sorry!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        
    def clear_button_clicked(self):
        self.tubes_widget.circuit_array[:,1] = 0
        self.tubes_widget.update_tubes_numbers()
        
    def load_circuitry(self,circuitry):
        circuitry = np.array(circuitry)-1
        self.tubes_widget.circuit_array[circuitry,1] = [i+1 for i in range(len(self.tubes_widget.circuit_array))]        
        self.tubes_widget.update_tubes_numbers()
            
class tubes_circuitry_widget(QWidget):
    def __init__(self,Ntubes_per_bank,N_banks,parent=None):
        QWidget.__init__(self)
        self.Ntubes_per_bank = Ntubes_per_bank
        self.N_banks = N_banks
        self.Tubes_list = []
        h_layout = QHBoxLayout()
        for i in range(N_banks):
            v_layout = QVBoxLayout()
            for j in range(Ntubes_per_bank):
                self.Tubes_list.append(CircleWidget(int(i*Ntubes_per_bank+j),self))
                v_layout.addWidget(self.Tubes_list[-1])
            h_layout.addLayout(v_layout)
        Ntubes = Ntubes_per_bank * N_banks
        self.circuit_array = np.zeros([Ntubes,2],dtype=int)
        self.circuit_array[:,0] = [i for i in range(Ntubes)]
        self.setLayout(h_layout)
        self.resize(50 * N_banks * 3,50 * Ntubes_per_bank * 3)

    def update_tubes_numbers(self):
        for i,tube in enumerate(self.Tubes_list):
            tube_order = self.circuit_array[i,1]
            if tube_order == 0:
                if hasattr(tube,'order'):
                    delattr(tube,'order')
            else:
                tube.order = tube_order
            tube.update()

class CircleWidget(QWidget):
    def __init__(self,tube_id,parent=None):
        super(CircleWidget, self).__init__()
        self.parent = parent
        self.id = tube_id
        self.update()
        self.setSizePolicy(QSizePolicy.Minimum,QSizePolicy.Minimum)
        self.adjustSize()
        
    def mousePressEvent(self,event):
        if event.button() == Qt.LeftButton:
            if not hasattr(self,'order'):
                maximum_tube = np.max(self.parent.circuit_array[:,1])
                self.parent.circuit_array[self.id,1] = maximum_tube + 1
                self.parent.update_tubes_numbers()
                
        elif event.button() == Qt.RightButton:
            if hasattr(self,'order'):
                current_order = self.order
                self.parent.circuit_array[self.parent.circuit_array[:,1] > self.order,1] -= 1                
                self.parent.circuit_array[self.id,1] = 0
                self.parent.update_tubes_numbers()
                
    def paintEvent(self, event):
        qp = QPainter(self)
        self.draw_circle(qp)
    
    def draw_circle(self, qp):
        qp.setRenderHint(QPainter.Antialiasing)
        qp.setPen(QPen(Qt.black, 3))
        qp.setFont(QFont("Arial",15))
        qp.drawEllipse(25,25, 50, 50)
        if hasattr(self,"order"):
                qp.drawText(QRectF(25,25,50,50.0),Qt.AlignCenter|Qt.AlignCenter,str(int(self.order)))
    
if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = tubes_circuitry_window(12,2)
    window.show()
    sys.exit(app.exec_())