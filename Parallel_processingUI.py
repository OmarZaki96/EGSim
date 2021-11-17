from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
import os, sys, csv, io
from GUI_functions import read_capillary_file, write_capillary_file
from unit_conversion import *
from inputs_validation import check_capillary
import appdirs
from multiprocessing import cpu_count
FROM_Parallel_Processing_Main,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Parallel_processing.ui"))

class Parallel_Processing_Window(QDialog, FROM_Parallel_Processing_Main):
    def __init__(self, parent=None):
        super(Parallel_Processing_Window, self).__init__(parent)
        self.setupUi(self)
        
        # defining connections
        self.Ok_button.clicked.connect(self.ok_button_clicked)
        self.Cancel_button.clicked.connect(self.close)
        
        # create N_Processes ini file path
        self.N_processes_ini_path = appdirs.user_data_dir("EGSim")+"/N_Processes.ini"
        
        # make sure N_Processes ini file exists, if not then create it
        if not os.path.exists(self.N_processes_ini_path):
            with open(self.N_processes_ini_path, "w") as file1:
                file1.write(str(cpu_count()))
        
        # read N_Processes ini file
        with open(self.N_processes_ini_path, 'r') as file:
            for line in file:
                N_processes = line.strip()
        try:
            self.N_Processes = int(N_processes)
        except:
            import traceback
            print(traceback.format_exc())
            self.N_Processes = cpu_count()
            self.raise_error_meesage("Failed to load saved number of processes for parallel processing, using "+str(cpu_count())+" instead")
        
        # populate spinbox with value of N_Processes
        self.N_processes.setValue(self.N_Processes)
        
        # show maximum number of processes hint
        self.Hint_label.setText("Maximum Number of cores available on this computer is "+str(cpu_count()))
    
    def ok_button_clicked(self):
        with open(self.N_processes_ini_path, "w") as file1:
            file1.write(str(self.N_processes.value()))
        self.N_processes_passed = self.N_processes.value()
        self.close()
        
if __name__ == '__main__':
    def main():
        app=QApplication(sys.argv)
        app.setStyle('Fusion')
        window = CapillaryWindow()
        window.show()
        app.exec_()
    try:
        main()
    except Exception as why:
        print(why)

