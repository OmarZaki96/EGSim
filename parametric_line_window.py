from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
import os, sys
from unit_conversion import *
import numpy as np

FROM_line_Parametric_Main,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/line_parametric.ui"))

class values():
    pass

class parametric_line_Window(QDialog, FROM_line_Parametric_Main):
    def __init__(self, parent=None):
        super(parametric_line_Window, self).__init__(parent)
        self.setupUi(self)

        # connecting signals
        self.line_length_check.stateChanged.connect(self.check_changed)
        self.line_OD_check.stateChanged.connect(self.check_changed)
        self.line_ID_check.stateChanged.connect(self.check_changed)
        self.line_ins_t_check.stateChanged.connect(self.check_changed)
        self.line_e_D_check.stateChanged.connect(self.check_changed)
        self.line_K_check.stateChanged.connect(self.check_changed)
        self.line_ins_K_check.stateChanged.connect(self.check_changed)
        self.line_sur_T_check.stateChanged.connect(self.check_changed)
        self.line_sur_h_check.stateChanged.connect(self.check_changed)
        self.cancel_button.clicked.connect(self.close)
        self.ok_button.clicked.connect(self.ok_button_clicked)
            
    def load_fields(self,data):
        if data[0,0]: # line length
            self.line_length_check.setChecked(True)
            self.line_length.setText(", ".join([str(round(i,6)) for i in data[0,1]]))
        if data[1,0]: # line outer diameter
            self.line_OD_check.setChecked(True)
            self.line_OD.setText(", ".join([str(round(i,6)) for i in data[1,1]]))
        if data[2,0]: # line inner diameter
            self.line_ID_check.setChecked(True)
            self.line_ID.setText(", ".join([str(round(i,6)) for i in data[2,1]]))
        if data[3,0]: # line insulation thickness
            self.line_ins_t_check.setChecked(True)
            self.line_ins_t.setText(", ".join([str(round(i,6)) for i in data[3,1]]))
        if data[4,0]: # line e/D ratio
            self.line_e_D_check.setChecked(True)
            self.line_e_D.setText(", ".join([str(round(i,6)) for i in data[4,1]]))
        if data[5,0]: # line thermal conductivity
            self.line_K_check.setChecked(True)
            self.line_K.setText(", ".join([str(round(i,6)) for i in data[5,1]]))
        if data[6,0]: # line insulation thermal conductivity
            self.line_ins_K_check.setChecked(True)
            self.line_ins_K.setText(", ".join([str(round(i,6)) for i in data[6,1]]))
        if data[7,0]: # line surrounding temperature
            self.line_sur_T_check.setChecked(True)
            self.line_sur_T.setText(", ".join([str(round(i-273.15,6)) for i in data[7,1]]))
        if data[8,0]: # line surrounding HTC
            self.line_sur_h_check.setChecked(True)
            self.line_sur_h.setText(", ".join([str(round(i,6)) for i in data[8,1]]))
        
    def raise_error_message(self,message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(message)
        msg.setWindowTitle("Sorry!")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        
    def validate(self):
        data = []
        if self.line_length_check.checkState():
            try:
                value = self.line_length.text()
                list_of_values = [length_unit_converter(i,self.line_length_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.line_length_check.text()+" values must be greater than 0")
                data.append([1,values,'line length','m'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.line_length_check.text()+" values")
        else:
            data.append([0,0,'',''])

        if self.line_OD_check.checkState():
            try:
                value = self.line_OD.text()
                list_of_values = [length_unit_converter(i,self.line_OD_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.line_OD_check.text()+" values must be greater than 0")
                data.append([1,values,'line outer diameter','m'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.line_OD_check.text()+" values")
        else:
            data.append([0,0,'',''])

        if self.line_ID_check.checkState():
            try:
                value = self.line_ID.text()
                list_of_values = [length_unit_converter(i,self.line_ID_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.line_ID_check.text()+" values must be greater than 0")
                data.append([1,values,'line inner diameter','m'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.line_ID_check.text()+" values")
        else:
            data.append([0,0,'',''])

        if self.line_ins_t_check.checkState():
            try:
                value = self.line_ins_t.text()
                list_of_values = [length_unit_converter(i,self.line_ins_t_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i >= 0:
                        return (0,self.line_ins_t_check.text()+" values must be greater than 0")
                data.append([1,values,'line insulation thickness','m'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.line_ins_t_check.text()+" values")
        else:
            data.append([0,0,'',''])

        if self.line_e_D_check.checkState():
            try:
                value = self.line_e_D.text()
                list_of_values = [float(i) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i >= 0:
                        return (0,self.line_e_D_check.text()+" values must be greater than 0")
                data.append([1,values,'line roughness (e/D)',''])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.line_e_D_check.text()+" values")
        else:
            data.append([0,0,'',''])

        if self.line_K_check.checkState():
            try:
                value = self.line_K.text()
                list_of_values = [Thermal_K_unit_converter(i,self.line_K_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.line_K_check.text()+" values must be greater than 0")
                data.append([1,values,'line thermal conductivity','W/m.K'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.line_K_check.text()+" values")
        else:
            data.append([0,0,'',''])

        if self.line_ins_K_check.checkState():
            try:
                value = self.line_ins_K.text()
                list_of_values = [Thermal_K_unit_converter(i,self.line_ins_K_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.line_ins_K_check.text()+" values must be greater than 0")
                data.append([1,values,'line insulation thermal conductivity','W/m.K'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.line_ins_K_check.text()+" values")
        else:
            data.append([0,0,'',''])

        if self.line_sur_T_check.checkState():
            try:
                value = self.line_sur_T.text()
                list_of_values = [temperature_unit_converter(i,self.line_sur_T_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                data.append([1,values,'line surrounding temperature','K'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.line_sur_T_check.text()+" values")
        else:
            data.append([0,0,'',''])

        if self.line_sur_h_check.checkState():
            try:
                value = self.line_sur_h.text()
                list_of_values = [HTC_unit_converter(i,self.line_sur_h_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i >= 0:
                        return (0,self.line_sur_h_check.text()+" values must be greater than 0")
                data.append([1,values, 'line surrounding HTC','W/m2.K'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.line_sur_h_check.text()+" values")
        else:
            data.append([0,0,'',''])


        data = np.array(data, dtype=object)
        return (1, data)
    
    def ok_button_clicked(self):
        validate = self.validate()
        if validate[0]:
            atleast_once = False
            if any(validate[1][:,0]):
                atleast_once = True
            if atleast_once:
                self.parametric_data = validate[1]
            else:
                self.parametric_data = None
            self.close()
        else:
            self.raise_error_message(validate[1])
    
    def check_changed(self,state):
        sender_name = self.sender().objectName()
        object_name = sender_name.replace("_check","")
        if state:
            getattr(self,object_name).setEnabled(True)
            if hasattr(self,object_name+"_unit"):
                getattr(self,object_name+"_unit").setEnabled(True)
        else:
            getattr(self,object_name).setEnabled(False)
            if hasattr(self,object_name+"_unit"):
                getattr(self,object_name+"_unit").setEnabled(False)
