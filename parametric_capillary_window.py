from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
import os, sys
from unit_conversion import *
import numpy as np

FROM_capillary_Parametric_Main,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/capillary_parametric.ui"))

class values():
    pass

class parametric_capillary_Window(QDialog, FROM_capillary_Parametric_Main):
    def __init__(self, parent=None):
        super(parametric_capillary_Window, self).__init__(parent)
        self.setupUi(self)

        # connecting signals
        self.capillary_length_check.stateChanged.connect(self.check_changed)
        self.capillary_D_check.stateChanged.connect(self.check_changed)
        self.Capillary_entrance_D_check.stateChanged.connect(self.check_changed)
        self.Capillary_N_tubes_check.stateChanged.connect(self.check_changed)
        self.Capillary_DP_tolerance_check.stateChanged.connect(self.check_changed)
        self.Capillary_DT_check.stateChanged.connect(self.check_changed)
        self.cancel_button.clicked.connect(self.close)
        self.ok_button.clicked.connect(self.ok_button_clicked)
        
    def load_fields(self,data):
        if data[0,0]: # capillary length
            self.capillary_length_check.setChecked(True)
            self.capillary_length.setText(", ".join([str(round(i,6)) for i in data[0,1]]))
        if data[1,0]: # capillary diameter
            self.capillary_D_check.setChecked(True)
            self.capillary_D.setText(", ".join([str(round(i,6)) for i in data[1,1]]))
        if data[2,0]: # capillary entrance diameter
            self.Capillary_entrance_D_check.setChecked(True)
            self.Capillary_entrance_D.setText(", ".join([str(round(i,6)) for i in data[2,1]]))
        if data[3,0]: # number of parallel tubes
            self.Capillary_N_tubes_check.setChecked(True)
            self.Capillary_N_tubes.setText(", ".join([str(round(i,6)) for i in data[3,1]]))
        if data[4,0]: # pressure tolerance
            self.Capillary_DP_tolerance_check.setChecked(True)
            self.Capillary_DP_tolerance.setText(", ".join([str(round(i,6)) for i in data[4,1]]))
        if data[5,0]: # temperature discretization
            self.Capillary_DT_check.setChecked(True)
            self.Capillary_DT.setText(", ".join([str(round(i,6)) for i in data[5,1]]))
        
    def raise_error_message(self,message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(message)
        msg.setWindowTitle("Sorry!")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        
    def validate(self):
        data = []
        if self.capillary_length_check.checkState():
            try:
                value = self.capillary_length.text()
                list_of_values = [length_unit_converter(i,self.capillary_length_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.capillary_length_check.text()+" values must be greater than 0")
                data.append([1,values,"Capillary tube length",'m'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.capillary_length_check.text()+" values")
        else:
            data.append([0,0,'',''])

        if self.capillary_D_check.checkState():
            try:
                value = self.capillary_D.text()
                list_of_values = [length_unit_converter(i,self.capillary_D_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.capillary_D_check.text()+" values must be greater than 0")
                data.append([1,values,"Capillary tube diameter",'m'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.capillary_D_check.text()+" values")
        else:
            data.append([0,0,'',''])

        if self.Capillary_entrance_D_check.checkState():
            try:
                value = self.Capillary_entrance_D.text()
                list_of_values = [length_unit_converter(i,self.Capillary_entrance_D_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.Capillary_entrance_D_check.text()+" values must be greater than 0")
                data.append([1,values,"Capillary tube entrance diameter",'m'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.Capillary_entrance_D_check.text()+" values")
        else:
            data.append([0,0,'',''])

        if self.Capillary_N_tubes_check.checkState():
            try:
                value = self.Capillary_N_tubes.text()
                list_of_values = [int(i) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i >= 0:
                        return (0,self.Capillary_N_tubes_check.text()+" values must be greater than 0")
                data.append([1,values, "Capillary number of tubes",''])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.Capillary_N_tubes_check.text()+" values")
        else:
            data.append([0,0,'',''])

        if self.Capillary_DP_tolerance_check.checkState():
            try:
                value = self.Capillary_DP_tolerance.text()
                list_of_values = [pressure_unit_converter(i,self.Capillary_DP_tolerance_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i >= 0:
                        return (0,self.Capillary_DP_tolerance_check.text()+" values must be greater than 0")
                data.append([1,values,"Capillary pressure drop tolerance",'Pa'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.Capillary_DP_tolerance_check.text()+" values")
        else:
            data.append([0,0,'',''])

        if self.Capillary_DT_check.checkState():
            try:
                value = self.Capillary_DT.text()
                list_of_values = [temperature_diff_unit_converter(i,self.Capillary_DT_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.Capillary_DT_check.text()+" values must be greater than 0")
                data.append([1,values,"Capillary descritization temperature",'C'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.Capillary_DT_check.text()+" values")
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
