from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
import os, sys
from unit_conversion import *
from GUI_functions import load_refrigerant_list
import numpy as np

FROM_cycle_Parametric_Main,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/cycle_parametric.ui"))

class values():
    pass

class parametric_cycle_Window(QDialog, FROM_cycle_Parametric_Main):
    def __init__(self, parent=None):
        super(parametric_cycle_Window, self).__init__(parent)
        self.setupUi(self)
        
        # load refirgerant list
        ref_list = load_refrigerant_list()
        if not ref_list[0]:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Could not load refrigerants list, window will exit")
            msg.setWindowTitle("Sorry!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            self.close()
        else:
            ref_list = ref_list[1]
        self.refrigerant.addItems(ref_list[:,0])
        
        # connecting signals
        self.Cond_1_check.stateChanged.connect(self.check_changed)
        self.Superheat_check.stateChanged.connect(self.check_changed)
        self.Max_N_check.stateChanged.connect(self.check_changed)
        self.Energy_residual_check.stateChanged.connect(self.check_changed)
        self.Pressure_residual_check.stateChanged.connect(self.check_changed)
        self.Mass_flowrate_residual_check.stateChanged.connect(self.check_changed)
        self.Mass_residual_check.stateChanged.connect(self.check_changed)
        self.solver_check.stateChanged.connect(self.check_changed)
        self.refrigerant_check.stateChanged.connect(self.check_changed)
        self.cancel_button.clicked.connect(self.close)
        self.ok_button.clicked.connect(self.ok_button_clicked)
        self.refrigerant.itemSelectionChanged.connect(self.update_selected_refirgerants)
    
    def update_selected_refirgerants(self):
        selected_items = [x.text() for x in self.refrigerant.selectedItems()]
        if selected_items:
            self.refrigerant_unit.setPlainText(", ".join(selected_items))
        else:
            self.refrigerant_unit.setPlainText("")
        
    def load_fields(self,data):
        if data[0,0]: # subcooling or charge
            self.Cond_1_check.setChecked(True)
            self.Cond_1.setText(", ".join([str(round(i,6)) for i in data[0,1]]))
        if data[1,0]: # superheat
            self.Superheat_check.setChecked(True)
            self.Superheat.setText(", ".join([str(round(i,6)) for i in data[1,1]]))
        if data[2,0]: # maximum number of iterations
            self.Max_N_check.setChecked(True)
            self.Max_N.setText(", ".join([str(i) for i in data[2,1]]))
        if data[3,0]: # energy residual
            self.Energy_residual_check.setChecked(True)
            self.Energy_residual.setText(", ".join([str(round(i,6)) for i in data[3,1]]))
        if data[4,0]: # Pressure residual
            self.Pressure_residual_check.setChecked(True)
            self.Pressure_residual.setText(", ".join([str(round(i,6)) for i in data[4,1]]))
        if data[5,0]: # Mass flowrate residual
            self.Mass_flowrate_residual_check.setChecked(True)
            self.Mass_flowrate_residual.setText(", ".join([str(round(i,6)) for i in data[5,1]]))
        if data[6,0]: # Mass residual
            self.Mass_residual_check.setChecked(True)
            self.Mass_residual.setText(", ".join([str(round(i,6)) for i in data[6,1]]))
        if data[7,0]: # solver
            self.solver_check.setChecked(True)
            index = []
            for item in data[7,1]:
                index.append(self.solver.row((self.solver.findItems(item, Qt.MatchFixedString)[0])))
            for i in index:
                self.solver.item(i).setSelected(True)
        if data[8,0]: # refrigerant
            self.refrigerant_check.setChecked(True)
            index = []
            for item in data[8,1]:
                index.append(self.refrigerant.row(self.refrigerant.findItems(item, Qt.MatchFixedString)[0]))
            for i in index:
                self.refrigerant.item(i).setSelected(True)
        
    def raise_error_message(self,message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(message)
        msg.setWindowTitle("Sorry!")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        
    def validate(self):
        data = []
        if self.Cond_1_check.checkState():
            try:
                value = self.Cond_1.text()
                if self.cond_values[0] == 0:
                    list_of_values = [temperature_diff_unit_converter(i,self.Cond_1_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                    list_of_values = list(set(list_of_values))
                    values = tuple(sorted(list_of_values))
                elif self.cond_values[0] == 1:
                    list_of_values = [mass_unit_converter(i,self.Cond_1_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                    list_of_values = list(set(list_of_values))
                    values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.Cond_1_check.text()+" values must be greater than 0")
                data.append([1,values,'',''])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.Cond_1_check.text()+" values")
        else:
            data.append([0,0,'',''])

        if self.Superheat_check.checkState():
            try:
                value = self.Superheat.text()
                list_of_values = [temperature_diff_unit_converter(i,self.Superheat_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,"Superheat values must be greater than 0")
                data.append([1,values,"Cycle superheat",'C'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading superheat values")
        else:
            data.append([0,0,'',''])
            
        if self.Max_N_check.checkState():
            try:
                value = self.Max_N.text()
                list_of_values = [int(i) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,"max number of iterations values must be greater than 0")
                data.append([1,values,"Cycle maximum number of iterations",''])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading maximum number of iterations values")
        else:
            data.append([0,0,'',''])

        if self.Energy_residual_check.checkState():
            try:
                value = self.Energy_residual.text()
                list_of_values = [power_unit_converter(i,self.Energy_residual_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,"Energy residual values must be greater than 0")
                data.append([1,values,'Cycle energy tolerance','W'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading Energy residual values")
        else:
            data.append([0,0,'',''])

        if self.Pressure_residual_check.checkState():
            try:
                value = self.Pressure_residual.text()
                list_of_values = [pressure_unit_converter(i,self.Pressure_residual_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,"Pressure residual values must be greater than 0")
                data.append([1,values,"Cycle pressure tolerance",'Pa'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading pressure residual values")
        else:
            data.append([0,0,'',''])

        if self.Mass_flowrate_residual_check.checkState():
            try:
                value = self.Mass_flowrate_residual.text()
                list_of_values = [mass_flowrate_unit_converter(i,self.Mass_flowrate_residual_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,"Mass flowrate residual values must be greater than 0")
                data.append([1,values,"Cycle mass flowrate tolerance",'kg/s'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading mass flowrate residual values")
        else:
            data.append([0,0,'',''])

        if self.Mass_residual_check.checkState():
            try:
                value = self.Mass_residual.text()
                list_of_values = [mass_unit_converter(i,self.Mass_residual_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,"Mass residual values must be greater than 0")
                data.append([1,values,'Cycle mass tolerance','kg'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading mass residual values")
        else:
            data.append([0,0,'',''])

        if self.solver_check.checkState():
            try:
                selected_items = [x.text() for x in self.solver.selectedItems()]
                if selected_items:
                    list_of_values = selected_items
                else:
                    return (0, "Please choose at least one solver")
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                data.append([1,values,'Cycle solver',''])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading solver values")
        else:
            data.append([0,0,'',''])

        if self.refrigerant_check.checkState():
            try:
                selected_items = [x.text() for x in self.refrigerant.selectedItems()]
                if selected_items:
                    list_of_values = selected_items
                else:
                    return (0, "Please choose at least one refrigerant")
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                data.append([1,values,'Cycle Refrigerant',''])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading refrigerant values")
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

    def refresh_ui(self,cond_values):
        self.cond_values = cond_values
        if cond_values[0] == 0:
            self.Cond_1_check.setText("Subcooling")
            self.Cond_1_unit.addItems(["C","F"])
        else:
            self.Cond_1_check.setText("Charge")
            self.Cond_1_unit.addItems(["kg","lb"])

        if cond_values[1] == 0:
            self.Superheat_check.setEnabled(True)
        else:
            self.Superheat_check.setEnabled(False)

        if cond_values[2]:
            self.Energy_residual_check.setEnabled(True)
        else:
            self.Energy_residual_check.setEnabled(False)

        if cond_values[3]:
            self.Pressure_residual_check.setEnabled(True)
        else:
            self.Pressure_residual_check.setEnabled(False)

        if cond_values[4]:
            self.Mass_flowrate_residual_check.setEnabled(True)
        else:
            self.Mass_flowrate_residual_check.setEnabled(False)

        if cond_values[5]:
            self.Mass_residual_check.setEnabled(True)
        else:
            self.Mass_residual_check.setEnabled(False)
            