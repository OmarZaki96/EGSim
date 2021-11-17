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

FROM_FinTube_Select_Tube_Main,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Fin_tube_select_tube.ui"))
FROM_FinTube_Edit_Tube_Main,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Fin_tube_edit_tube.ui"))

class values():
    pass

class FinTube_select_tube_window(QDialog, FROM_FinTube_Select_Tube_Main):
    def __init__(self, parent=None):
        # first UI
        super(FinTube_select_tube_window, self).__init__(parent)
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
                if tubes_data[current_selection-1,1].lower() == "smooth":
                    self.tube_selected.tube_type_index = 0
                    self.tube_selected.tube_ID = float(tubes_data[current_selection-1,2])/1000                
                    self.tube_selected.tube_e_D = float(tubes_data[current_selection-1,3])
                
                elif tubes_data[current_selection-1,1].lower() == "microfin":
                    self.tube_selected.tube_type_index = 1
                    self.tube_selected.tube_t = float(tubes_data[current_selection-1,4])/1000
                    self.tube_selected.tube_e = float(tubes_data[current_selection-1,5])/1000
                    self.tube_selected.tube_d = float(tubes_data[current_selection-1,6])/1000
                    self.tube_selected.tube_n = float(tubes_data[current_selection-1,7])
                    self.tube_selected.tube_gamma = float(tubes_data[current_selection-1,8])
                    self.tube_selected.tube_beta = float(tubes_data[current_selection-1,9])
                    
                self.tube_selected.tube_K = float(tubes_data[current_selection-1,10])
                self.close()
            except:                
                self.raise_error_message("Failed to select this tube, there might be missing fields.")
        else:
            self.raise_error_message("Please select a tube first")
            
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

        tubes_file = appdirs.user_data_dir("EGSim")+r"/fintube_tubes.csv"
        if os.path.exists(tubes_file):
            try:
                self.tubes_data = pd.read_csv(tubes_file,index_col=0)
                empty_cols = [col for col in self.tubes_data.columns if (self.tubes_data[col].isnull().all() and ("unnamed" in col.lower()))]
                self.tubes_data.drop(empty_cols, axis=1, inplace=True)
                if (len(self.tubes_data.columns) != 11):
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
                self.raise_error_message("Failed to delete tube!")
            try:
                self.load_tubes()
                self.raise_information_message("Tube deleted!")
            except:
                self.close()
        else:
            self.raise_error_message("Please select a tube first")

    def edit_tube(self):
        current_selection = self.Tubes_table.currentRow()
        if current_selection > 0:
            try:
                self.tubes_data = self.tubes_data.reset_index(drop=True)
                tubes_data = self.tubes_data.to_numpy()
                edit_window = FinTube_edit_tube_window(self)
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
                self.raise_error_message("Failed to edit tube!")
            try:
                self.load_tubes()
            except:
                self.close()
        else:
            self.raise_error_message("Please select a tube first")

    def add_tube(self):
        try:
            add_window = FinTube_edit_tube_window(self)
            add_window.exec_()
            if hasattr(add_window,"tube_data"):
                self.tubes_data = self.tubes_data.reset_index(drop=True)
                self.tubes_data.loc[len(self.tubes_data.index)] = add_window.tube_data
                self.save_table()
        except:
            import traceback
            print(traceback.format_exc())
            self.raise_error_message("Failed to add tube!")
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
            tubes_file = appdirs.user_data_dir("EGSim")+r"/fintube_tubes.csv"
            self.tubes_data.to_csv(tubes_file)
            return True
        except:
            return False
        
    def populate_table(self):
        tubes_data = self.tubes_data
        print(tubes_data)
        assert(len(tubes_data.columns) == 11)
        self.Tubes_table.setRowCount(len(tubes_data)+1)
        self.Tubes_table.setColumnCount(len(tubes_data.columns))
        self.Tubes_table.setHorizontalHeaderLabels(tubes_data.columns)
        self.Tubes_table.setSelectionBehavior(QAbstractItemView.SelectRows);
        self.Tubes_table.setEditTriggers(QAbstractItemView.NoEditTriggers);

        units = ["mm","-","mm","-","mm","mm","mm","-","degree","degree","W/m.K"]
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
                    if not (value.lower() in ["smooth","microfin",""]):
                        raise
                self.Tubes_table.setItem(i+1,j,QTableWidgetItem(value))
        header = self.Tubes_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        self.Tubes_table.setVerticalHeaderLabels([""]+[str(i+1) for i in range(0,len(tubes_data))])

class FinTube_edit_tube_window(QDialog, FROM_FinTube_Edit_Tube_Main):
    def __init__(self, parent=None):
        # first UI
        super(FinTube_edit_tube_window, self).__init__(parent)
        self.setupUi(self)
        self.tube_type_changed()
        
        # Connections
        self.Tube_type.currentIndexChanged.connect(self.tube_type_changed)
        self.Cancel_Button.clicked.connect(self.cancel_button)
        self.Ok_button.clicked.connect(self.ok_button)

        # loading validators
        only_number = QRegExpValidator(QRegExp("(([0-9]+\.[0-9]*[1-9][0-9]*)|([0-9]*[1-9][0-9]*\.[0-9]+)|([0-9]*[1-9][0-9]*))"))
        only_number_negative = QRegExpValidator(QRegExp("[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)"))
        only_number_integer = QRegExpValidator(QRegExp("[0-9]{8}"))
        self.Tube_OD.setValidator(only_number)
        self.Tube_ID.setValidator(only_number)
        self.Tube_e_D.setValidator(only_number)
        self.Tube_t.setValidator(only_number)
        self.Tube_e.setValidator(only_number)
        self.Tube_d.setValidator(only_number)
        self.Tube_gamma.setValidator(only_number)
        self.Tube_beta.setValidator(only_number)
        self.Tube_K.setValidator(only_number)

        # intially load images
        def images_loader(path,var_name,size):
            try:
                photo = QPixmap(path)
                photo = photo.scaledToWidth(size)
                setattr(self,var_name,photo)
            except:
                pass
        
        images_loader("photos/FinTube_MicrofinsTubes.png",'MicrofinsTubes_photo',250)
        
    def validate(self):
        if str(self.Tube_OD.text()).replace(" ","") in ["","-","."]:
            return 0
        if self.Tube_ID.isEnabled():
            if self.Tube_ID.text() in ["","-","."]:
                return 0
        if self.Tube_e_D.isEnabled():
            if self.Tube_e_D.text() in ["","-","."]:
                return 0
        if self.Tube_t.isEnabled():
            if self.Tube_t.text() in ["","-","."]:
                return 0
        if self.Tube_e.isEnabled():
            if self.Tube_e.text() in ["","-","."]:
                return 0
        if self.Tube_d.isEnabled():
            if self.Tube_d.text() in ["","-","."]:
                return 0
        if self.Tube_gamma.isEnabled():
            if self.Tube_gamma.text() in ["","-","."]:
                return 0
        if self.Tube_beta.isEnabled():
            if self.Tube_beta.text() in ["","-","."]:
                return 0
        if self.Tube_K.text() in ["","-","."]:
            return 0
        return 1

    def tube_type_changed(self):
        if self.Tube_type.currentIndex() == 0:
            self.Tube_ID.setEnabled(True)
            self.Tube_ID_unit.setEnabled(True)
            self.Tube_e_D.setEnabled(True)
            self.Tube_t.setEnabled(False)
            self.Tube_t_unit.setEnabled(False)
            self.Tube_e.setEnabled(False)
            self.Tube_e_unit.setEnabled(False)
            self.Tube_d.setEnabled(False)
            self.Tube_d_unit.setEnabled(False)
            self.Tube_gamma.setEnabled(False)
            self.Tube_gamma_unit.setEnabled(False)
            self.Tube_beta.setEnabled(False)
            self.Tube_beta_unit.setEnabled(False)
            self.Tube_n.setEnabled(False)
            self.Tube_type_image.clear()
            
        elif self.Tube_type.currentIndex() == 1:
            self.Tube_ID.setEnabled(False)
            self.Tube_ID_unit.setEnabled(False)
            self.Tube_e_D.setEnabled(False)
            self.Tube_t.setEnabled(True)
            self.Tube_t_unit.setEnabled(True)
            self.Tube_e.setEnabled(True)
            self.Tube_e_unit.setEnabled(True)
            self.Tube_d.setEnabled(True)
            self.Tube_d_unit.setEnabled(True)
            self.Tube_gamma.setEnabled(True)
            self.Tube_gamma_unit.setEnabled(True)
            self.Tube_beta.setEnabled(True)
            self.Tube_beta_unit.setEnabled(True)
            self.Tube_n.setEnabled(True)
            if hasattr(self,"MicrofinsTubes_photo"):
                self.Tube_type_image.setPixmap(self.MicrofinsTubes_photo)
            else:
                self.Tube_type_image.clear()
                self.Tube_type_image.setText("Microfin tube Demonistration photo")
                

    def load_fields(self,tube_data):
        self.Tube_OD.setText("%.5g" % (tube_data[0]))

        if tube_data[1].lower() == "smooth":
            self.Tube_type.setCurrentIndex(0)
            self.Tube_ID.setText("%.5g" % (tube_data[2]))
            self.Tube_e_D.setText("%.5g" % (tube_data[3]))

        elif tube_data[1].lower() == "microfin":
            self.Tube_type.setCurrentIndex(1)
            self.Tube_t.setText("%.5g" % (tube_data[4]))
            self.Tube_e.setText("%.5g" % (tube_data[5]))
            self.Tube_d.setText("%.5g" % (tube_data[6]))
            self.Tube_n.setValue(int(tube_data[7]))
            self.Tube_gamma.setText("%.5g" % (tube_data[8]))
            self.Tube_beta.setText("%.5g" % (tube_data[9]))

        self.Tube_K.setText("%.5g" % (tube_data[10]))

    def cancel_button(self):
        self.close()

    def ok_button(self):
        check = self.validate()
        if check == 1:
            tube_data = []
            tube_data.append(length_unit_converter(self.Tube_OD.text(),self.Tube_OD_unit.currentIndex())*1000)
            if self.Tube_type.currentIndex() == 0:
                tube_data.append("Smooth")
                tube_data.append(length_unit_converter(self.Tube_ID.text(),self.Tube_ID_unit.currentIndex())*1000)
                tube_data.append(float(self.Tube_e_D.text()))
                tube_data.append("")
                tube_data.append("")
                tube_data.append("")
                tube_data.append("")
                tube_data.append("")
                tube_data.append("")
            if self.Tube_type.currentIndex() == 1:
                tube_data.append("Microfin")
                tube_data.append("")
                tube_data.append("")
                tube_data.append(length_unit_converter(self.Tube_t.text(),self.Tube_t_unit.currentIndex())*1000)
                tube_data.append(length_unit_converter(self.Tube_e.text(),self.Tube_e_unit.currentIndex())*1000)
                tube_data.append(length_unit_converter(self.Tube_d.text(),self.Tube_d_unit.currentIndex())*1000)
                tube_data.append(self.Tube_n.value())
                tube_data.append(angle_unit_converter(self.Tube_gamma.text(),self.Tube_gamma_unit.currentIndex()))
                tube_data.append(angle_unit_converter(self.Tube_beta.text(),self.Tube_beta_unit.currentIndex()))

            tube_data.append(Thermal_K_unit_converter(self.Tube_K.text(),self.Tube_K_unit.currentIndex()))
            self.tube_data = tube_data
            self.close()

        elif check == 0:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please fill all empty fields")
            msg.setWindowTitle("Empty fields!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
