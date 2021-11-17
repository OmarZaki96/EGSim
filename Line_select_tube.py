from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
import os, sys
from GUI_functions import *
from unit_conversion import *
import appdirs
import pandas as pd
import numpy as np

FROM_Line_Select_Tube_Main,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Line_select_tube.ui"))
FROM_Line_Edit_Tube_Main,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Line_edit_tube.ui"))

class values():
    pass

class Line_select_tube_window(QDialog, FROM_Line_Select_Tube_Main):
    def __init__(self, parent=None):
        # first UI
        super(Line_select_tube_window, self).__init__(parent)
        self.setupUi(self)
        
        # connections
        self.Select_button.clicked.connect(self.select_row)
        self.Delete_button.clicked.connect(self.delete_button)
        self.Edit_button.clicked.connect(self.edit_tube)
        self.Add_button.clicked.connect(self.add_tube)

    def select_row(self):
        current_selection = self.Tubes_table.currentRow()
        if current_selection > 0:
            try:
                tubes_data = self.tubes_data.to_numpy()
                self.tube_selected = values()
                self.tube_selected.tube_OD = float(tubes_data[current_selection-1,0])/1000
                self.tube_selected.tube_ID = float(tubes_data[current_selection-1,1])/1000                
                self.tube_selected.tube_ins_t = float(tubes_data[current_selection-1,2])/1000
                self.tube_selected.tube_e_D = float(tubes_data[current_selection-1,3])
                self.tube_selected.tube_K = float(tubes_data[current_selection-1,4])
                self.tube_selected.tube_ins_K = float(tubes_data[current_selection-1,5])
        
                self.close()
            except:                
                self.raise_error_message("Failed to select this tube, there might be missing fields.")
        else:
            self.raise_error_message("Please select a line first")
            
    def raise_error_message(self,message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(message)
        msg.setWindowTitle("Error!")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def load_tubes(self):
        if self.Select_button.isEnabled():
            self.Tubes_table.doubleClicked.connect(self.select_row)
        else:
            self.Tubes_table.doubleClicked.connect(self.edit_tube)          

        tubes_file = appdirs.user_data_dir("EGSim")+r"/line_tubes.csv"
        if os.path.exists(tubes_file):
            try:
                self.tubes_data = pd.read_csv(tubes_file,index_col=0)
                empty_cols = [col for col in self.tubes_data.columns if (self.tubes_data[col].isnull().all() and ("unnamed" in col.lower()))]
                self.tubes_data.drop(empty_cols, axis=1, inplace=True)
                if (len(self.tubes_data.columns) != 6):
                    self.tubes_data = pd.read_csv(tubes_file,index_col=None)
                    empty_cols = [col for col in self.tubes_data.columns if (self.tubes_data[col].isnull().all() and ("unnamed" in col.lower()))]
                    self.tubes_data.drop(empty_cols, axis=1, inplace=True)
                self.tubes_data.dropna(how="all",axis=0,inplace=True)
                self.tubes_data = self.tubes_data.replace(np.nan, '', regex=True)
                self.populate_table()
                return True
            except:
                import traceback
                print(traceback.format_exc())
                return False
        else:
            return False

    def delete_button(self):
        current_selection = self.Tubes_table.currentRow()
        if current_selection > 0:
            try:
                self.tubes_data = self.tubes_data.reset_index(drop=True)
                self.tubes_data = self.tubes_data.drop([current_selection-1])
                if not self.save_table():
                    raise
            except:
                self.raise_error_message("Failed to delete line!")
            try:
                self.load_tubes()
                self.raise_information_message("line deleted!")
            except:
                self.close()
        else:
            self.raise_error_message("Please select a line first")

    def edit_tube(self):
        current_selection = self.Tubes_table.currentRow()
        if current_selection > 0:
            try:
                self.tubes_data = self.tubes_data.reset_index(drop=True)
                tubes_data = self.tubes_data.to_numpy()
                edit_window = Line_edit_tube_window(self)
                edit_window.load_fields(tubes_data[current_selection-1])
                edit_window.exec_()
                if hasattr(edit_window,"tube_data"):
                    self.tubes_data = self.tubes_data.reset_index(drop=True)
                    self.tubes_data.iloc[current_selection-1,:] = edit_window.tube_data
                    if not self.save_table():
                        raise
            except:
                import traceback
                print(traceback.format_exc())
                self.raise_error_message("Failed to edit line!")
            try:
                self.load_tubes()
            except:
                self.close()
        else:
            self.raise_error_message("Please select a line first")

    def add_tube(self):
        try:
            add_window = Line_edit_tube_window(self)
            add_window.exec_()
            if hasattr(add_window,"tube_data"):
                self.tubes_data = self.tubes_data.reset_index(drop=True)
                self.tubes_data.loc[len(self.tubes_data.index)] = add_window.tube_data
                self.save_table()
        except:
            import traceback
            print(traceback.format_exc())
            self.raise_error_message("Failed to add line!")
        try:
            self.load_tubes()
        except:
            self.close()

    def raise_information_message(self,message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(message)
        msg.setWindowTitle("Information!")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def save_table(self):
        try:
            tubes_file = appdirs.user_data_dir("EGSim")+r"/line_tubes.csv"
            self.tubes_data.to_csv(tubes_file)
            return True
        except:
            return False
        
    def populate_table(self):
        tubes_data = self.tubes_data
        print(tubes_data)
        assert(len(tubes_data.columns) == 6)
        self.Tubes_table.setRowCount(len(tubes_data)+1)
        self.Tubes_table.setColumnCount(len(tubes_data.columns))
        self.Tubes_table.setHorizontalHeaderLabels(tubes_data.columns)
        self.Tubes_table.setSelectionBehavior(QAbstractItemView.SelectRows);
        self.Tubes_table.setEditTriggers(QAbstractItemView.NoEditTriggers);

        units = ["mm","mm","mm","-","W/m.K","W/m.K"]
        for j in range(len(tubes_data.columns)):
            item = QTableWidgetItem(units[j])
            item.setFlags(item.flags() ^ (Qt.ItemIsSelectable | Qt.ItemIsEnabled))
            self.Tubes_table.setItem(0,j,item)
            
        tubes_data = tubes_data.to_numpy()
        for i in range(len(tubes_data)):
            for j in range(len(tubes_data[0,:])):
                try:
                    value = float(tubes_data[i,j])
                    value = "%.5g" % value
                except:
                    value = tubes_data[i,j]
                    if not (value.lower() in [""]):
                        raise
                self.Tubes_table.setItem(i+1,j,QTableWidgetItem(value))
        header = self.Tubes_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        self.Tubes_table.setVerticalHeaderLabels([""]+[str(i+1) for i in range(0,len(tubes_data))])

class Line_edit_tube_window(QDialog, FROM_Line_Edit_Tube_Main):
    def __init__(self, parent=None):
        # first UI
        super(Line_edit_tube_window, self).__init__(parent)
        self.setupUi(self)
        
        # Connections
        self.Cancel_Button.clicked.connect(self.cancel_button)
        self.Ok_button.clicked.connect(self.ok_button)

        # loading validators
        only_number = QRegExpValidator(QRegExp("(([0-9]+\.[0-9]*[1-9][0-9]*)|([0-9]*[1-9][0-9]*\.[0-9]+)|([0-9]*[1-9][0-9]*))"))
        self.Tube_OD.setValidator(only_number)
        self.Tube_ID.setValidator(only_number)
        self.Tube_e_D.setValidator(only_number)
        self.Tube_ins_t.setValidator(only_number)
        self.Tube_K.setValidator(only_number)
        self.Tube_ins_K.setValidator(only_number)
        
    def validate(self):
        if self.Tube_OD.text() in ["","-","."]:
            return 0
        if self.Tube_e_D.text() in ["","-","."]:
            return 0
        if self.Tube_ID.text() in ["","-","."]:
            return 0
        if self.Tube_ins_t.text() in ["","-","."]:
            return 0
        if self.Tube_K.text() in ["","-","."]:
            return 0
        if self.Tube_ins_K.text() in ["","-","."]:
            return 0
        return 1                

    def load_fields(self,tube_data):
        self.Tube_OD.setText("%.5g" % (tube_data[0]))

        self.Tube_ID.setText("%.5g" % (tube_data[1]))
        self.Tube_ins_t.setText("%.5g" % (tube_data[2]))
        self.Tube_e_D.setText("%.5g" % (tube_data[3]))
        self.Tube_K.setText("%.5g" % (tube_data[4]))
        self.Tube_ins_K.setText("%.5g" % (tube_data[5]))

    def cancel_button(self):
        self.close()

    def ok_button(self):
        check = self.validate()
        if check == 1:
            tube_data = []
            tube_data.append(length_unit_converter(self.Tube_OD.text(),self.Tube_OD_unit.currentIndex())*1000)
            tube_data.append(length_unit_converter(self.Tube_ID.text(),self.Tube_ID_unit.currentIndex())*1000)
            tube_data.append(length_unit_converter(self.Tube_ins_t.text(),self.Tube_ins_t_unit.currentIndex())*1000)
            tube_data.append(float(self.Tube_e_D.text()))
            tube_data.append(Thermal_K_unit_converter(self.Tube_K.text(),self.Tube_K_unit.currentIndex()))
            tube_data.append(Thermal_K_unit_converter(self.Tube_ins_K.text(),self.Tube_ins_K_unit.currentIndex()))

            self.tube_data = tube_data
            self.close()

        elif check == 0:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please fill all empty fields")
            msg.setWindowTitle("Empty fields!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
