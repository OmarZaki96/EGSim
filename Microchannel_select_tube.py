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

FROM_Microchannel_Select_Tube_Main,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/microchannel_select_tube.ui"))
FROM_Microchannel_Edit_Tube_Main,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/microchannel_edit_tube.ui"))

class values():
    pass

class Microchannel_select_tube_window(QDialog, FROM_Microchannel_Select_Tube_Main):
    def __init__(self, parent=None):
        # first UI
        super(Microchannel_select_tube_window, self).__init__(parent)
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
                self.tube_selected.tube_w = float(tubes_data[current_selection-1,0])/1000                
                self.tube_selected.tube_h = float(tubes_data[current_selection-1,1])/1000                
                self.tube_selected.tube_s = float(tubes_data[current_selection-1,2])/1000                
                self.tube_selected.tube_e_D = float(tubes_data[current_selection-1,3])              
                self.tube_selected.tube_n_ports = float(tubes_data[current_selection-1,5])              
                if tubes_data[current_selection-1,4].lower() == "rectangle":
                    self.tube_selected.port_shape_index = 0
                    self.tube_selected.port_dim_1 = float(tubes_data[current_selection-1,6])/1000                
                    self.tube_selected.port_dim_2 = float(tubes_data[current_selection-1,7])/1000
                    
                elif tubes_data[current_selection-1,4].lower() == "circle":
                    self.tube_selected.port_shape_index = 1
                    self.tube_selected.port_dim_1 = float(tubes_data[current_selection-1,6])/1000                

                elif tubes_data[current_selection-1,4].lower() == "triangle":
                    self.tube_selected.port_shape_index = 2
                    self.tube_selected.port_dim_1 = float(tubes_data[current_selection-1,6])/1000                
                    self.tube_selected.port_dim_2 = float(tubes_data[current_selection-1,7])/1000

                self.tube_selected.tube_K = float(tubes_data[current_selection-1,8])
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

        tubes_file = appdirs.user_data_dir("EGSim")+r"/microchannel_tubes.csv"
        if os.path.exists(tubes_file):
            try:
                self.tubes_data = pd.read_csv(tubes_file,index_col=0)
                empty_cols = [col for col in self.tubes_data.columns if (self.tubes_data[col].isnull().all() and ("unnamed" in col.lower()))]
                self.tubes_data.drop(empty_cols, axis=1, inplace=True)
                if (len(self.tubes_data.columns) != 9):
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
                self.save_table()
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
                edit_window = Microchannel_edit_tube_window(self)
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
            add_window = Microchannel_edit_tube_window(self)
            add_window.exec_()
            if hasattr(add_window,"tube_data"):
                self.tubes_data = self.tubes_data.reset_index(drop=True)
                self.tubes_data.loc[len(self.tubes_data.index)] = add_window.tube_data
                if not self.save_table():
                    raise
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
            tubes_file = appdirs.user_data_dir("EGSim")+r"/Microchannel_tubes.csv"
            self.tubes_data.to_csv(tubes_file)
            return True
        except:
            return False
        
    def populate_table(self):
        tubes_data = self.tubes_data
        assert(len(tubes_data.columns) == 9)
        self.Tubes_table.setRowCount(len(tubes_data)+1)
        self.Tubes_table.setColumnCount(len(tubes_data.columns))
        self.Tubes_table.setHorizontalHeaderLabels(tubes_data.columns)
        self.Tubes_table.setSelectionBehavior(QAbstractItemView.SelectRows);
        self.Tubes_table.setEditTriggers(QAbstractItemView.NoEditTriggers);

        units = ["mm","mm","mm","-","-","-","mm","mm","W/m.K"]
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
                    if not (value.lower() in ["triangle","circle","rectangle",""]):
                        raise
                self.Tubes_table.setItem(i+1,j,QTableWidgetItem(value))
        header = self.Tubes_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        self.Tubes_table.setVerticalHeaderLabels([""]+[str(i+1) for i in range(0,len(tubes_data))])

class Microchannel_edit_tube_window(QDialog, FROM_Microchannel_Edit_Tube_Main):
    def __init__(self, parent=None):
        # first UI
        super(Microchannel_edit_tube_window, self).__init__(parent)
        self.setupUi(self)
        self.port_shape_changed()
        
        # Connections
        self.Port_shape.currentIndexChanged.connect(self.port_shape_changed)
        self.Cancel_Button.clicked.connect(self.cancel_button)
        self.Ok_button.clicked.connect(self.ok_button)

        # loading validators
        only_number = QRegExpValidator(QRegExp("(([0-9]+\.[0-9]*[1-9][0-9]*)|([0-9]*[1-9][0-9]*\.[0-9]+)|([0-9]*[1-9][0-9]*))"))
        only_number_negative = QRegExpValidator(QRegExp("[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)"))
        only_number_integer = QRegExpValidator(QRegExp("[0-9]{8}"))
        self.Tube_w.setValidator(only_number)
        self.Tube_h.setValidator(only_number)
        self.Tube_s.setValidator(only_number)
        self.Tube_e_D.setValidator(only_number)
        self.Port_w.setValidator(only_number)
        self.Port_h.setValidator(only_number)
        self.Tube_K.setValidator(only_number)

        # intially load images
        def images_loader(path,var_name,size):
            try:
                photo = QPixmap(path)
                photo = photo.scaledToWidth(size)
                setattr(self,var_name,photo)
            except:
                pass
        
        images_loader("photos/Microchannel_TrianglePort.png",'TrianglePort_photo',250)
        images_loader("photos/Microchannel_RectanglePort.png",'RectanglePort_photo',250)
        images_loader("photos/Microchannel_CirclePort.png",'CirclePort_photo',250)

        # intially populate available images
        if hasattr(self,"RectanglePort_photo"):
            self.Port_shape_image.setPixmap(self.RectanglePort_photo)
        else:
            self.Port_shape_image.setText("Rectangular Port Demonistration photo")
        
    def validate(self):
        if str(self.Tube_w.text()).replace(" ","") in ["","-","."]:
            return 0
        if self.Tube_h.text() in ["","-","."]:
            return 0
        if self.Tube_s.text() in ["","-","."]:
            return 0
        if self.Tube_e_D.text() in ["","-","."]:
            return 0
        if self.Port_w.text() in ["","-","."]:
            return 0
        if self.Port_h.isEnabled():
            if self.Port_h.text() in ["","-","."]:
                return 0
        if self.Tube_K.text() in ["","-","."]:
            return 0
        return 1

    def port_shape_changed(self):
        if self.Port_shape.currentIndex() == 0:
            self.Port_h.setEnabled(True)
            self.Port_h_unit.setEnabled(True)
            if hasattr(self,"RectanglePort_photo"):
                self.Port_shape_image.setPixmap(self.RectanglePort_photo)
            else:
                self.Port_shape_image.clear()
                self.Port_shape_image.setText("Rectangular Port Demonistration photo")
            
        elif self.Port_shape.currentIndex() == 1:
            self.Port_h.setEnabled(False)
            self.Port_h_unit.setEnabled(False)
            if hasattr(self,"CirclePort_photo"):
                self.Port_shape_image.setPixmap(self.CirclePort_photo)
            else:
                self.Port_shape_image.clear()
                self.Port_shape_image.setText("Circular Port Demonistration photo")

        elif self.Port_shape.currentIndex() == 2:
            self.Port_h.setEnabled(True)
            self.Port_h_unit.setEnabled(True)
            if hasattr(self,"TrianglePort_photo"):
                self.Port_shape_image.setPixmap(self.TrianglePort_photo)
            else:
                self.Port_shape_image.clear()
                self.Port_shape_image.setText("Triangular Port Demonistration photo")
                

    def load_fields(self,tube_data):
        self.Tube_w.setText("%.5g" % (tube_data[0]))

        self.Tube_h.setText("%.5g" % (tube_data[1]))

        self.Tube_s.setText("%.5g" % (tube_data[2]))

        self.Tube_e_D.setText("%.5g" % (tube_data[3]))

        self.Port_n.setValue(int(tube_data[5]))

        self.Port_w.setText("%.5g" % (tube_data[6]))

        if tube_data[4].lower() == "rectangle":
            self.Port_shape.setCurrentIndex(0)
            self.Port_h.setText("%.5g" % (tube_data[7]))

        elif tube_data[4].lower() == "circle":
            self.Port_shape.setCurrentIndex(1)

        elif tube_data[4].lower() == "triangle":
            self.Port_shape.setCurrentIndex(2)
            self.Port_h.setText("%.5g" % (tube_data[7]))

        self.Tube_K.setText("%.5g" % (tube_data[8]))

    def cancel_button(self):
        self.close()

    def ok_button(self):
        check = self.validate()
        if check == 1:
            tube_data = []
            tube_data.append(length_unit_converter(self.Tube_w.text(),self.Tube_w_unit.currentIndex())*1000)
            tube_data.append(length_unit_converter(self.Tube_h.text(),self.Tube_h_unit.currentIndex())*1000)
            tube_data.append(length_unit_converter(self.Tube_s.text(),self.Tube_s_unit.currentIndex())*1000)
            tube_data.append(float(self.Tube_e_D.text()))
            if self.Port_shape.currentIndex() == 0:
                tube_data.append("Rectangle")
                tube_data.append(int(self.Port_n.value()))                
                tube_data.append(length_unit_converter(self.Port_w.text(),self.Port_w_unit.currentIndex())*1000)
                tube_data.append(length_unit_converter(self.Port_h.text(),self.Port_h_unit.currentIndex())*1000)
            elif self.Port_shape.currentIndex() == 1:
                tube_data.append("Circle")
                tube_data.append(int(self.Port_n.value()))                
                tube_data.append(length_unit_converter(self.Port_w.text(),self.Port_w_unit.currentIndex())*1000)
                tube_data.append("")
            elif self.Port_shape.currentIndex() == 2:
                tube_data.append("Triangle")
                tube_data.append(int(self.Port_n.value()))                
                tube_data.append(length_unit_converter(self.Port_w.text(),self.Port_w_unit.currentIndex())*1000)
                tube_data.append(length_unit_converter(self.Port_h.text(),self.Port_h_unit.currentIndex())*1000)

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
