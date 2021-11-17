from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
import os, sys
from unit_conversion import *
import numpy as np

FROM_compressor_Parametric_Main,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/compressor_parametric.ui"))

class values():
    pass

class parametric_compressor_Window(QDialog, FROM_compressor_Parametric_Main):
    def __init__(self, parent=None):
        super(parametric_compressor_Window, self).__init__(parent)
        self.setupUi(self)
        
        # connecting signals
        self.Vdot_check.stateChanged.connect(self.check_changed)
        self.Speed_check.stateChanged.connect(self.check_changed)
        self.fp_check.stateChanged.connect(self.check_changed)
        self.eta_electric_check.stateChanged.connect(self.check_changed)
        self.mdot_multiplier_check.stateChanged.connect(self.check_changed)
        self.power_multiplier_check.stateChanged.connect(self.check_changed)
        self.Compressor_check.stateChanged.connect(self.check_changed)
        self.cancel_button.clicked.connect(self.close)
        self.ok_button.clicked.connect(self.ok_button_clicked)
    
    def update_selected_refirgerants(self):
        selected_items = [x.text() for x in self.refrigerant.selectedItems()]
        if selected_items:
            self.refrigerant_unit.setPlainText(", ".join(selected_items))
        else:
            self.refrigerant_unit.setPlainText("")
        
    def load_fields(self,data):
        if data[0,0]: # speed
            self.Speed_check.setChecked(True)
            self.Speed.setText(", ".join([str(round(i,6)) for i in data[0,1]]))
        if data[1,0]: # Heat loss fraction
            self.fp_check.setChecked(True)
            self.fp.setText(", ".join([str(round(i,6)*100) for i in data[1,1]]))
        if data[2,0]: # electric efficiency
            self.eta_electric_check.setChecked(True)
            self.eta_electric.setText(", ".join([str(round(i,6)*100) for i in data[2,1]]))
        if data[3,0]: # mass flowrate multiplier
            self.mdot_multiplier_check.setChecked(True)
            self.mdot_multiplier.setText(", ".join([str(round(i,6)) for i in data[3,1]]))
        if data[4,0]: # power multiplier
            self.power_multiplier_check.setChecked(True)
            self.power_multiplier.setText(", ".join([str(round(i,6)) for i in data[4,1]]))
        if data[5,0]: # Vdot
            self.Vdot_check.setChecked(True)
            self.Vdot.setText(", ".join([str(round(i,6)) for i in data[5,1]]))
        if data[6,0]: # compressor
            self.Compressor_check.setChecked(True)
            for i in data[6,1]:
                self.Compressor.item(i).setSelected(True)
        
    def raise_error_message(self,message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(message)
        msg.setWindowTitle("Sorry!")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        
    def validate(self):
        data = []
        if self.Speed_check.checkState():
            try:
                value = self.Speed.text()
                list_of_values = [float(i) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.Speed_check.text()+" values must be greater than 0")
                data.append([1,values,"Compressor Speed",'rpm'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.Speed_check.text()+" values")
        else:
            data.append([0,0,'',''])

        if self.fp_check.checkState():
            try:
                value = self.fp.text()
                list_of_values = [float(i)/100 for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not 0 <= i < 1:
                        return (0,self.fp_check.text()+" values must be between 0 and 100")
                data.append([1,values,"Compressor heat loss ratio",'%'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.fp_check.text()+" values")
        else:
            data.append([0,0,'',''])

        if self.eta_electric_check.checkState():
            try:
                value = self.eta_electric.text()
                list_of_values = [float(i)/100 for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not 0 < i <= 1:
                        return (0,self.eta_electric_check.text()+" values must be between 0 and 100")
                data.append([1,values,"Compressor electric efficiency",'%'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.eta_electric_check.text()+" values")
        else:
            data.append([0,0,'',''])

        if self.mdot_multiplier_check.checkState():
            try:
                value = self.mdot_multiplier.text()
                list_of_values = [float(i) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.mdot_multiplier_check.text()+" values must be greater than 0")
                data.append([1,values,"Compressor mass flowrate multiplier",''])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.mdot_multiplier_check.text()+" values")
        else:
            data.append([0,0,'',''])

        if self.power_multiplier_check.checkState():
            try:
                value = self.power_multiplier.text()
                list_of_values = [float(i) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.power_multiplier_check.text()+" values must be greater than 0")
                data.append([1,values,"Compressor power multiplier",''])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.power_multiplier_check.text()+" values")
        else:
            data.append([0,0,'',''])

        if self.Vdot_check.checkState():
            try:
                value = self.Vdot.text()
                list_of_values = [float(i) for i in value.replace(" ","").split(",")]
                list_of_values = [volume_unit_converter(value,self.Vdot_unit.currentIndex()) for value in list_of_values]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.Vdot_check.text()+" values must be greater than 0")
                data.append([1,values,"Compressor Displacement Volume per Revolution",'m3'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.Speed_check.text()+" values")
        else:
            data.append([0,0,'',''])

        if self.Compressor_check.checkState():
            try:
                selected_items = [x.row() for x in self.Compressor.selectedIndexes()]
                if selected_items:
                    list_of_values = selected_items
                else:
                    return (0, "Please choose at least one compressor")
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                data.append([1,values,"Compressor used",''])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading compressors")
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

    def refresh_ui(self,compressors):
        compressor_names = []
        for compressor in compressors:
            compressor_names.append(compressor[1])
        self.Compressor.clear()
        self.Compressor.addItems(compressor_names)