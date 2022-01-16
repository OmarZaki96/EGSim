from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
import os, sys, csv, io
from GUI_functions import read_line_file, write_line_file, load_last_location, save_last_location
from unit_conversion import *
from inputs_validation import check_line
from Line_select_tube import Line_select_tube_window

FROM_Line_Main,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Line_main.ui"))

class values():
    pass

class LineWindow(QDialog, FROM_Line_Main):
    def __init__(self, parent=None):
        super(LineWindow, self).__init__(parent)
        self.setupUi(self)
        
        # loading validators
        only_number = QRegExpValidator(QRegExp("(([0-9]+\.[0-9]*[1-9][0-9]*)|([0-9]*[1-9][0-9]*\.[0-9]+)|([0-9]*[1-9][0-9]*))"))
        only_number_negative = QRegExpValidator(QRegExp("[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)"))
        only_number_integer = QRegExpValidator(QRegExp("[0-9]{8}"))
        self.Line_length.setValidator(only_number)
        self.Line_OD.setValidator(only_number)
        self.Line_ID.setValidator(only_number)
        self.Line_insulation_t.setValidator(only_number)
        self.Line_e_D.setValidator(only_number)
        self.Line_tube_k.setValidator(only_number)
        self.Line_insulation_k.setValidator(only_number)
        self.Line_surrounding_T.setValidator(only_number_negative)
        self.Line_surrounding_HTC.setValidator(only_number)
        self.Line_HT_correction.setValidator(only_number)
        self.Line_DP_correction.setValidator(only_number)
        
        #defining connections
        self.Line_cancel_button.clicked.connect(self.cancel_button)
        self.Line_load_button.clicked.connect(self.load_button)
        self.Line_save_button.clicked.connect(self.save_button)
        self.Line_ok_button.clicked.connect(self.ok_button)
        self.Line_solve_HT.currentIndexChanged.connect(self.HT_option_changed)
        self.Line_solve_DP.currentIndexChanged.connect(self.DP_option_changed)
        self.Select_line_button.clicked.connect(self.select_line)

    def select_line(self):
        select_line_window = Line_select_tube_window()
        if not select_line_window.load_tubes():
            self.raise_error_message("Could not load lines database.\nPlease fix database csv file.")
        else:
            select_line_window.exec_()
            if hasattr(select_line_window,"tube_selected"):
                self.load_line(select_line_window.tube_selected)
    
    def load_line(self,line_data):
        self.Line_OD.setText('%s' % float('%.5g' % (line_data.tube_OD*1000)))
        self.Line_OD_unit.setCurrentIndex(2)
        self.Line_ID.setText('%s' % float('%.5g' % (line_data.tube_ID*1000)))
        self.Line_ID_unit.setCurrentIndex(2)
        self.Line_insulation_t.setText('%s' % float('%.5g' % (line_data.tube_ins_t*1000)))
        self.Line_insulation_t_unit.setCurrentIndex(2)
        self.Line_e_D.setText('%s' % float('%.5g' % (line_data.tube_e_D)))
        self.Line_tube_k.setText('%s' % float('%.5g' % line_data.tube_K))
        self.Line_tube_k_unit.setCurrentIndex(0)
        self.Line_insulation_k.setText('%s' % float('%.5g' % line_data.tube_ins_K))
        self.Line_insulation_k_unit.setCurrentIndex(0)
        
    def raise_error_message(self,message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(message)
        msg.setWindowTitle("Error!")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def HT_option_changed(self):
        if self.Line_solve_HT.currentIndex() == 0:
            self.Line_tube_k.setEnabled(True)
            self.Line_insulation_k.setEnabled(True)
            self.Line_surrounding_T.setEnabled(True)
            self.Line_surrounding_HTC.setEnabled(True)
            self.Line_tube_k_unit.setEnabled(True)
            self.Line_insulation_k_unit.setEnabled(True)
            self.Line_surrounding_T_unit.setEnabled(True)
            self.Line_surrounding_HTC_unit.setEnabled(True)
            self.Line_HT_correction.setEnabled(True)
            self.Line_N_segments.setEnabled(True)
            self.Line_q_tolerance.setEnabled(True)
            try:
                if float(self.Line_HT_correction.text()) == 0:
                    self.Line_HT_correction.setText("1.0")
            except:
                pass
        else:
            self.Line_tube_k.setEnabled(False)
            self.Line_insulation_k.setEnabled(False)
            self.Line_surrounding_T.setEnabled(False)
            self.Line_surrounding_HTC.setEnabled(False)
            self.Line_tube_k_unit.setEnabled(False)
            self.Line_insulation_k_unit.setEnabled(False)
            self.Line_surrounding_T_unit.setEnabled(False)
            self.Line_surrounding_HTC_unit.setEnabled(False)
            self.Line_HT_correction.setEnabled(False)
            self.Line_q_tolerance.setEnabled(False)
            try:
                if self.Line_solve_DP.currentIndex() == 1:
                    self.Line_N_segments.setEnabled(False)
            except:
                pass

    def DP_option_changed(self):
        if self.Line_solve_DP.currentIndex() == 0:
            self.Line_N_segments.setEnabled(True)
            self.Line_DP_correction.setEnabled(True)
            self.Line_N_90_bends.setEnabled(True)
            self.Line_N_180_bends.setEnabled(True)
            if float(self.Line_DP_correction.text()) == 0:
                self.Line_DP_correction.setText("1.0")
        else:
            self.Line_DP_correction.setEnabled(False)
            self.Line_N_90_bends.setEnabled(False)
            self.Line_N_180_bends.setEnabled(False)
            if self.Line_solve_HT.currentIndex() == 1:
                self.Line_N_segments.setEnabled(False)
    
    def load_fields(self,line):
        self.Line_name.setText(str(line.Line_name))
        self.Line_length.setText("%.5g" % line.Line_length)
        self.Line_OD.setText("%.5g" % line.Line_OD)
        self.Line_ID.setText("%.5g" % line.Line_ID)
        self.Line_insulation_t.setText("%.5g" % line.Line_insulation_t)
        self.Line_e_D.setText("%.5g" % line.Line_e_D)
        self.Line_tube_k.setText("%.5g" % line.Line_tube_k)
        self.Line_insulation_k.setText("%.5g" % line.Line_insulation_k)
        line_surrounding_T = line.Line_surrounding_T-273.15
        self.Line_surrounding_T.setText("%.5g" % line_surrounding_T)
        self.Line_N_segments.setValue(line.Line_N_segments)
        self.Line_q_tolerance.setValue(line.Line_q_tolerance*100)
        self.Line_DP_correction.setText("%.5g" % line.Line_DP_correction)
        self.Line_HT_correction.setText("%.5g" % line.Line_HT_correction)
        self.Line_surrounding_HTC.setText("%.5g" % line.Line_surrounding_HTC)
        self.Line_N_90_bends.setValue(int(line.Line_N_90_bends))
        self.Line_N_180_bends.setValue(int(line.Line_N_180_bends))
        if line.Line_HT_enabled == "True":
            self.Line_solve_HT.setCurrentIndex(0)
        else:
            self.Line_solve_HT.setCurrentIndex(1)
        if line.Line_DP_enabled == "True":
            self.Line_solve_DP.setCurrentIndex(0)
        else:
            self.Line_solve_DP.setCurrentIndex(1)

    def load_button(self):
        path = QFileDialog.getOpenFileName(self, 'Open line file',directory=load_last_location(),filter="Line file (*.line);;All files (*.*)")[0]
        if path != "":
            save_last_location(path)
            result = read_line_file(path)
            if result[0]:
                try:
                    line = result[1]
                    self.load_fields(line)
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
            path = QFileDialog.getSaveFileName(self, caption='Save line file',directory=load_last_location(),filter="line file (*.line);;All files (*.*)")[0]
            if path != "":
                save_last_location(path)
                if path[-5:].lower() != ".line":
                    path = path+".line"
                line = values()
                line.Line_name = str(self.Line_name.text())
                line.Line_length = length_unit_converter(self.Line_length.text(),self.Line_length_unit.currentIndex())
                line.Line_OD = length_unit_converter(self.Line_OD.text(),self.Line_OD_unit.currentIndex())
                line.Line_ID = length_unit_converter(self.Line_ID.text(),self.Line_ID_unit.currentIndex())
                line.Line_insulation_t = length_unit_converter(self.Line_insulation_t.text(),self.Line_insulation_t_unit.currentIndex())
                line.Line_e_D = float(self.Line_e_D.text())
                line.Line_N_segments = int(self.Line_N_segments.value())
                line.Line_q_tolerance = float(self.Line_q_tolerance.value()/100)
                line.Line_N_90_bends = int(self.Line_N_90_bends.value())
                line.Line_N_180_bends = int(self.Line_N_180_bends.value())
                if self.Line_solve_HT.currentIndex() == 0:
                    line.Line_HT_enabled = True
                    line.Line_tube_k = Thermal_K_unit_converter(self.Line_tube_k.text(),self.Line_tube_k_unit.currentIndex())
                    line.Line_insulation_k = Thermal_K_unit_converter(self.Line_insulation_k.text(),self.Line_insulation_k_unit.currentIndex())
                    line.Line_surrounding_T = temperature_unit_converter(self.Line_surrounding_T.text(),self.Line_surrounding_T_unit.currentIndex())
                    line.Line_surrounding_HTC = HTC_unit_converter(self.Line_surrounding_HTC.text(),self.Line_surrounding_HTC_unit.currentIndex())
                    line.Line_HT_correction = float(self.Line_HT_correction.text())
                else:
                    line.Line_HT_enabled = False
                    line.Line_tube_k = 1.0
                    line.Line_insulation_k = 1.0
                    line.Line_surrounding_T = 1.0
                    line.Line_surrounding_HTC = 0.0
                    line.Line_HT_correction = 0.0
                if self.Line_solve_DP.currentIndex() == 0:
                    line.Line_DP_enabled = True
                    line.Line_DP_correction = float(self.Line_HT_correction.text())
                else:
                    line.Line_DP_enabled = False
                    line.Line_DP_correction = 0.0
                
                result = write_line_file(line,path)
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
            line = values()
            line.Line_name = str(self.Line_name.text())
            line.Line_length = length_unit_converter(self.Line_length.text(),self.Line_length_unit.currentIndex())
            line.Line_OD = length_unit_converter(self.Line_OD.text(),self.Line_OD_unit.currentIndex())
            line.Line_ID = length_unit_converter(self.Line_ID.text(),self.Line_ID_unit.currentIndex())
            line.Line_insulation_t = length_unit_converter(self.Line_insulation_t.text(),self.Line_insulation_t_unit.currentIndex())
            line.Line_e_D = float(self.Line_e_D.text())
            line.Line_N_segments = int(self.Line_N_segments.value())
            line.Line_q_tolerance = float(self.Line_q_tolerance.value()/100)
            line.Line_N_90_bends = int(self.Line_N_90_bends.value())
            line.Line_N_180_bends = int(self.Line_N_180_bends.value())
            if self.Line_solve_HT.currentIndex() == 0:
                line.Line_HT_enabled = True
                line.Line_tube_k = Thermal_K_unit_converter(self.Line_tube_k.text(),self.Line_tube_k_unit.currentIndex())
                line.Line_insulation_k = Thermal_K_unit_converter(self.Line_insulation_k.text(),self.Line_insulation_k_unit.currentIndex())
                line.Line_surrounding_T = temperature_unit_converter(self.Line_surrounding_T.text(),self.Line_surrounding_T_unit.currentIndex())
                line.Line_surrounding_HTC = HTC_unit_converter(self.Line_surrounding_HTC.text(),self.Line_surrounding_HTC_unit.currentIndex())
                line.Line_HT_correction = float(self.Line_HT_correction.text())
            else:
                line.Line_HT_enabled = False
                line.Line_tube_k = 1.0
                line.Line_insulation_k = 1.0
                line.Line_surrounding_T = 1.0
                line.Line_surrounding_HTC = 0.0
                line.Line_HT_correction = 0.0
            if self.Line_solve_DP.currentIndex() == 0:
                line.Line_DP_enabled = True
                line.Line_DP_correction = float(self.Line_DP_correction.text())
            else:
                line.Line_DP_enabled = False
                line.Line_DP_correction = 0.0
            
            validation = check_line(line)
            if validation[0]:
                self.line_result = line
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
        if str(self.Line_name.text()).replace(" ","") in ["","-","."]:
            return 0
        if self.Line_length.text() in ["","-","."]:
            return 0
        if self.Line_OD.text() in ["","-","."]:
            return 0
        if self.Line_ID.text() in ["","-","."]:
            return 0
        if self.Line_insulation_t.text() in ["","-","."]:
            return 0
        if self.Line_e_D.text() in ["","-","."]:
            return 0
        if self.Line_solve_HT.currentIndex() == 0:
            if self.Line_tube_k.text() in ["","-","."]:
                return 0
            if self.Line_insulation_k.text() in ["","-","."]:
                return 0
            if self.Line_surrounding_T.text() in ["","-","."]:
                return 0
            if self.Line_surrounding_HTC.text() in ["","-","."]:
                return 0
            if self.Line_HT_correction.text() in ["","-","."]:
                return 0
        
        if self.Line_solve_DP.currentIndex() == 0:
            if self.Line_DP_correction.text() in ["","-","."]:
                return 0
        return 1

    def cancel_button(self):
        self.close()

if __name__ == '__main__':
    def main():
        app=QApplication(sys.argv)
        app.setStyle('Fusion')
        window = LineWindow()
        window.show()
        app.exec_()
    try:
        main()
    except Exception as why:
        print(why)

