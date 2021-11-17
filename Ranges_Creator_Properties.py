from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
import os, sys
from GUI_functions import load_ranges_creator_options, set_ranges_creator_options

class Ranges_Creator_Window(QDialog):
    def __init__(self, parent=None):
        super(Ranges_Creator_Window, self).__init__(parent)
        
        value = load_ranges_creator_options()
        
        self.setWindowTitle("Ranges Creator Properties")
        
        self.option = QCheckBox("Enable validation ranges creator upon successful signle run")
        
        self.option.setChecked(value)
        
        self.cancel_button = QPushButton("Cancel")
        self.ok_button = QPushButton("Ok")
        
        self.ok_button.clicked.connect(self.set_value)
        self.cancel_button.clicked.connect(self.close)
        self.ok_button.setDefault(True)

        layout1 = QHBoxLayout()
        layout1.addStretch()
        layout1.addWidget(self.cancel_button)
        layout1.addStretch()
        layout1.addWidget(self.ok_button)
        layout1.addStretch()
        
        layout2 = QVBoxLayout()
        layout2.addWidget(self.option)
        layout2.addStretch()
        layout2.addLayout(layout1)
        
        self.setLayout(layout2)

    def set_value(self):
        set_ranges_creator_options(self.option.isChecked())
        self.close()

if __name__ == '__main__':
    def main():
        app=QApplication(sys.argv)
        app.setStyle('Fusion')
        window = Ranges_Creator_Window()
        window.show()
        app.exec_()
    try:
        main()
    except Exception as why:
        print(why)
