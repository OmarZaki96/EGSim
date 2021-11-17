from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
import os, sys, csv, io
import CoolProp as CP
import appdirs
import importlib

FROM_Refprop_Properties,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/REFPROP_Properties.ui"))

class REFPROP_Properties_Window(QDialog, FROM_Refprop_Properties):
    def __init__(self, parent=None):
        super(REFPROP_Properties_Window, self).__init__(parent)
        self.setupUi(self)
        
        # intially get Refprop.ini file path
        self.refprop_ini_path = appdirs.user_data_dir("EGSim")+"\REFPROP.ini"
        
        # check if REFPROP.ini file exists, if not, create it
        if not os.path.exists(self.refprop_ini_path):
            self.create_REFPROP_ini()
        
        # intially read refprop_ini_path
        self.REFPROP_path = self.read_REFPROP_ini()
        
        # intially load path lineedit
        self.load_path()
        
        # connections
        self.refprop_path_select_button.clicked.connect(self.select_folder)
        self.refprop_path_test_button.clicked.connect(self.test_refprop_label_update)
    
    def select_folder(self):
        if self.REFPROP_path != "":
            default = self.REFPROP_path
        else:
            default = QDir.homePath()
        path = QFileDialog.getExistingDirectory(self, "Select REFPROP Directory",directory=default)
        if path != "":
            self.REFPROP_path = path
            f = open(self.refprop_ini_path, 'w')  # open file in append mode
            f.write(path)
            f.close()
            self.load_path()
    
    def test_refprop_label_update(self):
        succeeded = self.test_Refprop()
        if succeeded:
            self.refprop_path_test.setText("REFPROP is working")
            self.refprop_path_test.setStyleSheet('QLabel {color: green}')
        else:
            self.refprop_path_test.setText("REFPROP is not working")
            self.refprop_path_test.setStyleSheet('QLabel {color: red}')
    
    def test_Refprop(self):
        try:
            if not os.path.exists(self.REFPROP_path+"\MIXTURES"):
                raise
            if not os.path.exists(self.REFPROP_path+"\FLUIDS"):
                raise
            if not os.path.exists(self.REFPROP_path+"\REFPRP64.DLL"):
                if not os.path.exists(self.REFPROP_path+"\REFPROP.DLL"):
                    raise
            if not os.path.exists(self.REFPROP_path+"\REFPRP64.LIB"):
                if not os.path.exists(self.REFPROP_path+"\REFPROP.LIB"):
                    raise
            return 1
        except:
            return 0
    
    def create_REFPROP_ini(self):
        f = open(self.refprop_ini_path, 'a+')  # open file in append mode
        f.write('')
        f.close()
    
    def read_REFPROP_ini(self):
        with open(self.refprop_ini_path, 'r') as file:
            for line in file:
                path = line.strip()
                if os.path.exists(path):
                    return path
                else:
                    return ""
    
    def load_path(self):
        self.refprop_path.setText(self.REFPROP_path)
    