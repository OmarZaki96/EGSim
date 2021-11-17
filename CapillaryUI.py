from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
import os, sys, csv, io
from GUI_functions import read_capillary_file, write_capillary_file, load_last_location, save_last_location
from unit_conversion import *
from inputs_validation import check_capillary

FROM_Capillary_Main,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Capillary_main.ui"))

class values():
    pass

class CapillaryWindow(QDialog, FROM_Capillary_Main):
    def __init__(self, parent=None):
        super(CapillaryWindow, self).__init__(parent)
        self.setupUi(self)
        
        # loading validators
        only_number = QRegExpValidator(QRegExp("(([0-9]+\.[0-9]*[1-9][0-9]*)|([0-9]*[1-9][0-9]*\.[0-9]+)|([0-9]*[1-9][0-9]*))"))
        only_number_integer = QRegExpValidator(QRegExp("[0-9]{8}"))
        self.Capillary_length.setValidator(only_number)
        self.Capillary_D.setValidator(only_number)
        self.Capillary_entrance_D.setValidator(only_number)
        self.Capillary_DP_tolerance.setValidator(only_number)
        self.Capillary_DT.setValidator(only_number)
        
        #defining connections
        self.Capillary_cancel_button.clicked.connect(self.cancel_button)
        self.Capillary_load_button.clicked.connect(self.load_button)
        self.Capillary_save_button.clicked.connect(self.save_button)
        self.Capillary_ok_button.clicked.connect(self.ok_button)
        
    def load_fields(self,capillary):
        self.Capillary_name.setText(str(capillary.Capillary_name))
        self.Capillary_length.setText(str(round(capillary.Capillary_length,6)))
        self.Capillary_D.setText(str(round(capillary.Capillary_D,6)))
        self.Capillary_entrance_D.setText(str(round(capillary.Capillary_entrance_D,6)))
        self.Capillary_DP_tolerance.setText(str(round(capillary.Capillary_DP_tolerance,6)))
        self.Capillary_DT.setText(str(round(capillary.Capillary_DT,6)))
        self.Capillary_N_tubes.setValue(int(capillary.Capillary_N_tubes))
        self.Capillary_correlation.setCurrentIndex(int(capillary.Capillary_correlation))
    
    def raise_error_message(self,message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(message)
        msg.setWindowTitle("Error!")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def load_button(self):
        path = QFileDialog.getOpenFileName(self, 'Open capillary file',directory=load_last_location(),filter="Capillary file (*.capillary);;All files (*.*)")[0]
        if path != "":
            save_last_location(path)
            result = read_capillary_file(path)
            if result[0]:
                try:
                    capillary = result[1]
                    self.load_fields(capillary)
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("The file was loaded successfully")
                    msg.setWindowTitle("Success!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                except:
                    import traceback
                    print(traceback.format_exc())
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("File could not be loaded")
                    msg.setWindowTitle("Sorry!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
            else:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("File could not be loaded")
                msg.setWindowTitle("Sorry!")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
    
    def save_button(self):
        check = self.validate()
        if check == 1:
            path = QFileDialog.getSaveFileName(self, caption='Save capillary file',directory=load_last_location(),filter="capillary file (*.capillary);;All files (*.*)")[0]
            if path != "":
                save_last_location(path)
                if path[-10:].lower() != ".capillary":
                    path = path+".capillary"
                capillary = values()
                capillary.Capillary_name = str(self.Capillary_name.text())
                capillary.Capillary_length = length_unit_converter(self.Capillary_length.text(),self.Capillary_length_unit.currentIndex())
                capillary.Capillary_D = length_unit_converter(self.Capillary_D.text(),self.Capillary_D_unit.currentIndex())
                capillary.Capillary_entrance_D = length_unit_converter(self.Capillary_entrance_D.text(),self.Capillary_entrance_D_unit.currentIndex())
                capillary.Capillary_N_tubes = int(self.Capillary_N_tubes.value())
                capillary.Capillary_DP_tolerance = pressure_unit_converter(self.Capillary_DP_tolerance.text(),self.Capillary_DP_tolerance_unit.currentIndex())
                capillary.Capillary_DT = temperature_diff_unit_converter(self.Capillary_DT.text(),self.Capillary_DT_unit.currentIndex())
                capillary.Capillary_correlation = self.Capillary_correlation.currentIndex()
                result = write_capillary_file(capillary,path)
                if result:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("The file was saved successfully")
                    msg.setWindowTitle("Success!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                else:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("File could not be saved")
                    msg.setWindowTitle("Sorry!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please fill all empty fields")
            msg.setWindowTitle("Empty fields!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
    
    def ok_button(self):
        check = self.validate()
        if check == 1:
            capillary = values()
            capillary.Capillary_name = str(self.Capillary_name.text())
            capillary.Capillary_length = length_unit_converter(self.Capillary_length.text(),self.Capillary_length_unit.currentIndex())
            capillary.Capillary_D = length_unit_converter(self.Capillary_D.text(),self.Capillary_D_unit.currentIndex())
            capillary.Capillary_entrance_D = length_unit_converter(self.Capillary_entrance_D.text(),self.Capillary_entrance_D_unit.currentIndex())
            capillary.Capillary_N_tubes = int(self.Capillary_N_tubes.value())
            capillary.Capillary_DP_tolerance = pressure_unit_converter(self.Capillary_DP_tolerance.text(),self.Capillary_DP_tolerance_unit.currentIndex())
            capillary.Capillary_DT = temperature_diff_unit_converter(self.Capillary_DT.text(),self.Capillary_DT_unit.currentIndex())
            capillary.Capillary_correlation = self.Capillary_correlation.currentIndex()
            validation = check_capillary(capillary)
            if validation[0]:
                self.capillary_result = capillary
                self.close()
            else:
                self.raise_error_message(validation[1])
        elif check == 0:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please fill all empty fields")
            msg.setWindowTitle("Empty fields!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()

    def validate(self):
        if str(self.Capillary_name.text()).replace(" ","") in ["","-","."]:
            return 0
        if self.Capillary_length.text() in ["","-","."]:
            return 0
        if self.Capillary_D.text() in ["","-","."]:
            return 0
        if self.Capillary_entrance_D.text() in ["","-","."]:
            return 0
        if self.Capillary_DP_tolerance.text() in ["","-","."]:
            return 0
        if self.Capillary_DT.text() in ["","-","."]:
            return 0
        return 1

    def cancel_button(self):
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

