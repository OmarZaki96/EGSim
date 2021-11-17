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

FROM_Microchannel_Select_Fin_Main,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Microchannel_select_fin.ui"))
FROM_Microchannel_Edit_Fin_Main,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Microchannel_edit_fin.ui"))

class values():
    pass

class Microchannel_select_fin_window(QDialog, FROM_Microchannel_Select_Fin_Main):
    def __init__(self, parent=None):
        # first UI
        super(Microchannel_select_fin_window, self).__init__(parent)
        self.setupUi(self)
        
        # connections
        self.Select_button.clicked.connect(self.select_row)
        self.Delete_button.clicked.connect(self.delete_button)
        self.Edit_button.clicked.connect(self.edit_fin)
        self.Add_button.clicked.connect(self.add_fin)

    def select_row(self):
        current_selection = self.Fins_table.currentRow()
        if current_selection > 0:
            try:
                fins_data = self.fins_data.to_numpy()
                self.fin_selected = values()
                self.fin_selected.fin_t = float(fins_data[current_selection-1,1])/1000
                self.fin_selected.fin_FPI = float(fins_data[current_selection-1,2])
                self.fin_selected.fin_Fd = float(fins_data[current_selection-1,3])/1000
                if fins_data[current_selection-1,4].lower() == "louvered":
                    self.fin_selected.fin_type_index = 0
                    self.fin_selected.fin_params = [float(fins_data[current_selection-1,5])/1000,float(fins_data[current_selection-1,6])/1000,float(fins_data[current_selection-1,7])]
                if fins_data[current_selection-1,8].lower() == "yes":
                    self.fin_selected.fin_on_sides = 0
                elif fins_data[current_selection-1,8].lower() == "no":
                    self.fin_selected.fin_on_sides = 1
                self.fin_selected.fin_K = float(fins_data[current_selection-1,9])
                self.close()
            except:
                import traceback
                print(traceback.format_exc())
                self.raise_error_message("Failed to select this fin, there might be missing fields.")
                
        else:
            self.raise_error_message("Please select a fin first")
            
    def raise_error_message(self,message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(message)
        msg.setWindowTitle("Error!")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def load_fins(self):
        if self.Select_button.isEnabled():
            self.Fins_table.doubleClicked.connect(self.select_row)
        else:
            self.Fins_table.doubleClicked.connect(self.edit_fin)          

        fins_file = appdirs.user_data_dir("EGSim")+r"/microchannel_fins.csv"
        if os.path.exists(fins_file):
            try:
                self.fins_data = pd.read_csv(fins_file,index_col=0)
                empty_cols = [col for col in self.fins_data.columns if (self.fins_data[col].isnull().all() and ("unnamed" in col.lower()))]
                self.fins_data.drop(empty_cols, axis=1, inplace=True)
                if (len(self.fins_data.columns) != 10):
                    self.fins_data = pd.read_csv(fins_file,index_col=None)
                    empty_cols = [col for col in self.fins_data.columns if (self.fins_data[col].isnull().all() and ("unnamed" in col.lower()))]
                    self.fins_data.drop(empty_cols, axis=1, inplace=True)
                self.fins_data.dropna(how="all",axis=0,inplace=True)
                self.fins_data = self.fins_data.replace(np.nan, '', regex=True)
                self.populate_table()
                return True
            except:
                import traceback
                print(traceback.format_exc())
                return False
        else:
            return False

    def delete_button(self):
        current_selection = self.Fins_table.currentRow()
        if current_selection > 0:
            try:
                self.fins_data = self.fins_data.reset_index(drop=True)
                self.fins_data = self.fins_data.drop([current_selection-1])
                self.save_table()
            except:
                self.raise_error_message("Failed to delete fin!")
            try:
                self.load_fins()
                self.raise_information_message("Fin deleted!")
            except:
                self.close()
        else:
            self.raise_error_message("Please select a fin first")

    def edit_fin(self):
        current_selection = self.Fins_table.currentRow()
        if current_selection > 0:
            try:
                fins_data = self.fins_data.to_numpy()
                edit_window = Microchannel_edit_fin_window(self)
                edit_window.load_fields(fins_data[current_selection-1])
                edit_window.exec_()
                if hasattr(edit_window,"fin_data"):
                    self.fins_data = self.fins_data.reset_index(drop=True)
                    self.fins_data.iloc[current_selection-1,:] = edit_window.fin_data
                    if not self.save_table():
                        raise
            except:
                import traceback
                print(traceback.format_exc())
                self.raise_error_message("Failed to edit fin!")
            try:
                self.load_fins()
            except:
                self.close()
        else:
            self.raise_error_message("Please select a fin first")

    def add_fin(self):
        try:
            add_window = Microchannel_edit_fin_window(self)
            add_window.exec_()
            if hasattr(add_window,"fin_data"):
                self.fins_data = self.fins_data.reset_index(drop=True)
                self.fins_data.loc[len(self.fins_data.index)] = add_window.fin_data
                if not self.save_table():
                    raise
                
        except:
            import traceback
            print(traceback.format_exc())
            self.raise_error_message("Failed to add fin!")
        try:
            self.load_fins()
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
            fins_file = appdirs.user_data_dir("EGSim")+r"/microchannel_fins.csv"
            self.fins_data.to_csv(fins_file)
            return True
        except:
            return False
        
    def populate_table(self):
        fins_data = self.fins_data
        assert(len(fins_data.columns) == 10)
        self.Fins_table.setRowCount(len(fins_data)+1)
        self.Fins_table.setColumnCount(len(fins_data.columns))
        self.Fins_table.setHorizontalHeaderLabels(fins_data.columns)
        self.Fins_table.setSelectionBehavior(QAbstractItemView.SelectRows);
        self.Fins_table.setEditTriggers(QAbstractItemView.NoEditTriggers);

        units = ["","mm","-","mm","-","mm","mm","degree","-","W/m.K"]
        for j in range(len(fins_data.columns)):
            item = QTableWidgetItem(units[j])
            item.setFlags(item.flags() ^ (Qt.ItemIsSelectable | Qt.ItemIsEnabled))
            self.Fins_table.setItem(0,j,item)
            
        fins_data = fins_data.to_numpy()
        for i in range(len(fins_data)):
            for j in range(len(fins_data[0,:])):
                try:
                    value = float(fins_data[i,j])
                    value = "%.5g" % value
                except:
                    value = fins_data[i,j]
                self.Fins_table.setItem(i+1,j,QTableWidgetItem(value))
        header = self.Fins_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        self.Fins_table.setVerticalHeaderLabels([""]+[str(i+1) for i in range(0,len(fins_data))])
        
class Microchannel_edit_fin_window(QDialog, FROM_Microchannel_Edit_Fin_Main):
    def __init__(self, parent=None):
        # first UI
        super(Microchannel_edit_fin_window, self).__init__(parent)
        self.setupUi(self)
        self.fin_type_changed()
        
        # Connections
        self.Fin_type.currentIndexChanged.connect(self.fin_type_changed)
        self.Cancel_Button.clicked.connect(self.cancel_button)
        self.Ok_button.clicked.connect(self.ok_button)

        # loading validators
        only_number = QRegExpValidator(QRegExp("(([0-9]+\.[0-9]*[1-9][0-9]*)|([0-9]*[1-9][0-9]*\.[0-9]+)|([0-9]*[1-9][0-9]*))"))
        only_number_negative = QRegExpValidator(QRegExp("[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)"))
        only_number_integer = QRegExpValidator(QRegExp("[0-9]{8}"))
        self.Fin_t.setValidator(only_number)
        self.Fin_FPI.setValidator(only_number)
        self.Fin_Fd.setValidator(only_number)
        self.Fin_parameter_1.setValidator(only_number)
        self.Fin_parameter_2.setValidator(only_number)
        self.Fin_parameter_3.setValidator(only_number)
        self.Fin_K.setValidator(only_number)

        # intially load images
        def images_loader(path,var_name,size):
            try:
                photo = QPixmap(path)
                photo = photo.scaledToWidth(size)
                setattr(self,var_name,photo)
            except:
                pass
        
        images_loader("photos/Microchannel_LouveredFins.png",'LouveredFins_photo',460)
        
        # intially populate available images
        if hasattr(self,"LouveredFins_photo"):
            self.Fin_type_image.setPixmap(self.LouveredFins_photo)
        else:
            self.Fin_type_image.setText("Louvered Fins Demonistration photo")

    def validate(self):
        if str(self.Fin_Die_Name.text()).strip() == "":
            return 0
        if str(self.Fin_t.text()).replace(" ","") in ["","-","."]:
            return 0
        if self.Fin_FPI.text() in ["","-","."]:
            return 0
        if self.Fin_parameter_1.isEnabled():
            if self.Fin_parameter_1.text() in ["","-","."]:
                return 0
        if self.Fin_parameter_2.isEnabled():
            if self.Fin_parameter_2.text() in ["","-","."]:
                return 0
        if self.Fin_parameter_3.isEnabled():
            if self.Fin_parameter_3.text() in ["","-","."]:
                return 0
        if self.Fin_Fd.text() in ["","-","."]:
            return 0
        if self.Fin_K.text() in ["","-","."]:
            return 0
        return 1

    def fin_type_changed(self):
        if self.Fin_type.currentIndex() == 0:
            self.Fin_parameter_1.setEnabled(True)
            self.Fin_parameter_1_unit.setEnabled(True)
            self.Fin_parameter_2.setEnabled(True)
            self.Fin_parameter_2_unit.setEnabled(True)
            self.Fin_parameter_3.setEnabled(True)
            self.Fin_parameter_3_unit.setEnabled(True)
            self.Fin_parameter_1_label.setText("Louver height (L1)")
            self.Fin_parameter_2_label.setText("Louver pitch (Lp)")
            self.Fin_parameter_3_label.setTextFormat(Qt.RichText)
            self.Fin_parameter_3_label.setText("Louver Angle (L<spab>&alpha;</span>)")
            self.Fin_parameter_3_unit.clear()
            self.Fin_parameter_3_unit.addItems(['degree','radian','minute','second'])
            if hasattr(self,"LouveredFins_photo"):
                self.Fin_type_image.setPixmap(self.LouveredFins_photo)
            else:
                self.Fin_type_image.clear()
                self.Fin_type_image.setText("Louvered Fins Demonistration photo")

    def load_fields(self,fin_data):
        self.Fin_Die_Name.setText(fin_data[0])
        self.Fin_t.setText("%.5g" % (fin_data[1]))
        self.Fin_FPI.setText("%.5g" % (fin_data[2]))
        self.Fin_Fd.setText("%.5g" % (fin_data[3]))
        try:
            self.Fin_parameter_1.setText("%.5g" % (fin_data[5]))
        except:
            pass
        try:
            self.Fin_parameter_2.setText("%.5g" % (fin_data[6]))
        except:
            pass
        try:
            self.Fin_parameter_3.setText("%.5g" % (fin_data[7]))
        except:
            pass

        if fin_data[8].lower() == "yes":
            self.Fins_on_sides.setCurrentIndex(0)
        elif fin_data[8].lower() == "no":
            self.Fins_on_sides.setCurrentIndex(1)
        
        self.Fin_K.setText("%.5g" % (fin_data[9]))

        if fin_data[4].lower() == "louvered":
            self.Fin_type.setCurrentIndex(0)

    def cancel_button(self):
        self.close()

    def ok_button(self):
        check = self.validate()
        if check == 1:
            fin_data = []
            fin_data.append(self.Fin_Die_Name.text().strip())
            fin_data.append(length_unit_converter(self.Fin_t.text(),self.Fin_t_unit.currentIndex())*1000)
            fin_data.append(float(self.Fin_FPI.text()))
            fin_data.append(length_unit_converter(self.Fin_Fd.text(),self.Fin_Fd_unit.currentIndex())*1000)
            if self.Fin_type.currentIndex() == 0:
                fin_data.append("louvered")
            if self.Fin_parameter_1.isEnabled():
                fin_data.append(length_unit_converter(self.Fin_parameter_1.text(),self.Fin_parameter_1_unit.currentIndex())*1000)
            else:
                fin_data.append("")
            if self.Fin_parameter_2.isEnabled():
                fin_data.append(length_unit_converter(self.Fin_parameter_2.text(),self.Fin_parameter_2_unit.currentIndex())*1000)
            else:
                fin_data.append("")
            if self.Fin_parameter_3.isEnabled():
                fin_data.append(angle_unit_converter(self.Fin_parameter_3.text(),self.Fin_parameter_3_unit.currentIndex()))
            else:
                fin_data.append("")
            if self.Fins_on_sides.currentIndex() == 0:
                fin_data.append("Yes")
            elif self.Fins_on_sides.currentIndex() == 1:
                fin_data.append("No")

            fin_data.append(Thermal_K_unit_converter(self.Fin_K.text(),self.Fin_K_unit.currentIndex()))
            self.fin_data = fin_data
            self.close()

        elif check == 0:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please fill all empty fields")
            msg.setWindowTitle("Empty fields!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
