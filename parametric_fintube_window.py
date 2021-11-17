from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
import os, sys
from unit_conversion import *
from CoolProp.CoolProp import HAPropsSI
import numpy as np
from copy import deepcopy

FROM_fintube_Parametric_Main,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/fintube_parametric.ui"))

class values():
    pass

class parametric_fintube_Window(QDialog, FROM_fintube_Parametric_Main):
    def __init__(self, parent=None):
        super(parametric_fintube_Window, self).__init__(parent)
        self.setupUi(self)
        
        # validators
        only_number = QRegExpValidator(QRegExp("(([0-9]+\.[0-9]*[1-9][0-9]*)|([0-9]*[1-9][0-9]*\.[0-9]+)|([0-9]*[1-9][0-9]*))"))
        only_number_negative = QRegExpValidator(QRegExp("[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)"))
        self.FinTube_air_calculator_P.setValidator(only_number)
        self.FinTube_air_calculator_T.setValidator(only_number_negative)
        self.FinTube_air_calculator_2nd.setValidator(only_number_negative)

        # Calculator
        self.FinTube_air_calculator_option.currentIndexChanged.connect(self.FinTube_calculator_option_changed)
        self.FinTube_air_calculator_P.textChanged.connect(self.FinTube_calculator_calculate)
        self.FinTube_air_calculator_T.textChanged.connect(self.FinTube_calculator_calculate)
        self.FinTube_air_calculator_2nd.textChanged.connect(self.FinTube_calculator_calculate)
        self.FinTube_air_calculator_P_unit.currentIndexChanged.connect(self.FinTube_calculator_calculate)
        self.FinTube_air_calculator_T_unit.currentIndexChanged.connect(self.FinTube_calculator_calculate)
        self.FinTube_air_calculator_2nd_unit.currentIndexChanged.connect(self.FinTube_calculator_calculate)

        # assignings parameter checkboxes to check_state function
        for i in dir(self):
            if isinstance(getattr(self,i),QCheckBox):        
                getattr(self,i).stateChanged.connect(self.check_changed)
        
        # connections
        self.cancel_button.clicked.connect(self.close)
        self.ok_button.clicked.connect(self.ok_button_clicked)        
        self.Circuit_number.activated[int].connect(self.Circuit_selected_changed)

    def Circuit_selected_changed(self, newitem,enforce=False):
        combo = self.Circuit_number
        lastitem = combo.property("lastitem")
        combo.setProperty("lastitem", newitem)
        if lastitem == None:
            lastitem = 0
        if enforce:
            result = self.save_fields_circuit(newitem)
            if result[0]:
                self.circuits_data[lastitem] = result[1]
            return result
        if newitem != lastitem:
            result = self.save_fields_circuit(lastitem)
            if result[0]:
                self.circuits_data[lastitem] = result[1]
                self.load_fields_circuit(newitem)
                return 1
            else:
                self.raise_error_message(result[1])
                combo.setCurrentIndex(lastitem)
                return 0

    def FinTube_calculator_calculate(self):
        try:
            # Air Pressure
            if self.FinTube_air_calculator_P_unit.currentText() == "Pa":
                Air_Pressure = float(self.FinTube_air_calculator_P.text())
            elif self.FinTube_air_calculator_P_unit.currentText() == "kPa":
                Air_Pressure = float(self.FinTube_air_calculator_P.text()) * 1e3
            elif self.FinTube_air_calculator_P_unit.currentText() == "MPa":
                Air_Pressure = float(self.FinTube_air_calculator_P.text()) * 1e6
            elif self.FinTube_air_calculator_P_unit.currentText() == "bar":
                Air_Pressure = float(self.FinTube_air_calculator_P.text()) * 1e5
            elif self.FinTube_air_calculator_P_unit.currentText() == "atm":
                Air_Pressure = float(self.FinTube_air_calculator_P.text()) * 101325
            elif self.FinTube_air_calculator_P_unit.currentText() == "psi":
                Air_Pressure = float(self.FinTube_air_calculator_P.text()) * 6894.76
            
            # Air DBT
            if self.FinTube_air_calculator_T_unit.currentText() == "C":
                Air_DBT = float(self.FinTube_air_calculator_T.text()) + 273.15
            elif self.FinTube_air_calculator_T_unit.currentText() == "K":
                Air_DBT = float(self.FinTube_air_calculator_T.text())
            elif self.FinTube_air_calculator_T_unit.currentText() == "F":
                Air_DBT = (float(self.FinTube_air_calculator_T.text()) - 32) * 5 / 9 + 273.15

            # 2nd variable
            # WBT
            if self.FinTube_air_calculator_option.currentIndex() == 0:
                if self.FinTube_air_calculator_2nd_unit.currentText() == "C":
                    Air_WBT = float(self.FinTube_air_calculator_2nd.text()) + 273.15
                elif self.FinTube_air_calculator_2nd_unit.currentText() == "K":
                    Air_WBT = float(self.FinTube_air_calculator_2nd.text())
                elif self.FinTube_air_calculator_2nd_unit.currentText() == "F":
                    Air_WBT = (float(self.FinTube_air_calculator_2nd.text()) - 32) * 5 / 9 + 273.15
                
                RH = round(HAPropsSI("R","P",Air_Pressure,"T",Air_DBT,"B",Air_WBT) * 100, 3)
            
            # HR
            elif self.FinTube_air_calculator_option.currentIndex() == 1:
                HR = float(self.FinTube_air_calculator_2nd.text())
                RH = round(HAPropsSI("R","P",Air_Pressure,"T",Air_DBT,"W",HR) * 100,3)
            
            self.FinTube_air_calculator_RH.setText(str(RH))
        
        except:
            self.FinTube_air_calculator_RH.setText("Not Defined")
    
    def FinTube_calculator_option_changed(self):
        if self.FinTube_air_calculator_option.currentIndex() == 0:
            self.FinTube_air_calculator_2nd_label.setText("Air Wet Bulb Temperature")
            self.FinTube_air_calculator_2nd.clear()
            self.FinTube_air_calculator_2nd_unit.clear()
            self.FinTube_air_calculator_2nd_unit.addItems(["C","K","F"])
            self.FinTube_air_calculator_2nd_unit.adjustSize() 

        elif self.FinTube_air_calculator_option.currentIndex() == 1:
            self.FinTube_air_calculator_2nd_label.setText("Humidity Ratio")
            self.FinTube_air_calculator_2nd.clear()
            self.FinTube_air_calculator_2nd_unit.clear()
            self.FinTube_air_calculator_2nd_unit.addItems(["Kg/Kg","lb/lb"])
            self.FinTube_air_calculator_2nd_unit.adjustSize() 
            
    def load_fields(self,data):
        self.circuits_data = data[0,1]
        try:
            self.load_fields_circuit(self.Circuit_number.currentIndex())
            if len(self.circuits_data) != len(self.tube_type_list):
                raise
        except:
            import traceback
            print(traceback.format_exc())
            self.raise_error_message("Failed to old load parametric data")
            self.error_loading = True
            
        if data[1,0]: # Air inlet humid flow rate
            self.Air_Vdot_check.setChecked(True)
            self.Air_Vdot.setText(", ".join([str(round(i,6)) for i in data[1,1]]))
            
        if data[2,0]: # Air Pressure
            self.Air_Pressure_check.setChecked(True)
            self.Air_Pressure.setText(", ".join([str(round(i,6)) for i in data[2,1]]))
            
        if data[3,0]: # Air Temperature
            self.Air_Temperature_check.setChecked(True)
            self.Air_Temperature.setText(", ".join([str(round(i-273.15,6)) for i in data[3,1]]))
            
        if data[4,0]: # Air RH
            self.Air_RH_check.setChecked(True)
            self.Air_RH.setText(", ".join([str(round(i,6)*100) for i in data[4,1]]))
    
    def load_fields_circuit(self,i):
        circuit = self.circuits_data[i]
        if self.tube_type_list[i]:
            self.Tube_ID_check.setEnabled(True)
        else:
            self.Tube_ID_check.setEnabled(False)

        self.Tube_length_check.setChecked(False)
        self.Tube_length.setText("")
        self.Tube_OD_check.setChecked(False)
        self.Tube_OD.setText("")
        self.Tube_ID_check.setChecked(False)
        self.Tube_ID.setText("")
        self.Tube_Pl_check.setChecked(False)
        self.Tube_Pl.setText("")
        self.Tube_Pt_check.setChecked(False)
        self.Tube_Pt.setText("")
        self.N_parallel_check.setChecked(False)
        self.N_parallel.setText("")
        self.N_tubes_check.setChecked(False)
        self.N_tubes.setText("")
        self.N_banks_check.setChecked(False)
        self.N_banks.setText("")
        self.Fin_thickness_check.setChecked(False)
        self.Fin_thickness.setText("")
        self.Fin_FPI_check.setChecked(False)
        self.Fin_FPI.setText("")

        if not isinstance(circuit,int):
            if circuit[0,0]: # tube length
                self.Tube_length_check.setChecked(True)
                self.Tube_length.setText(", ".join([str(round(i,6)) for i in circuit[0,1]]))
    
            if circuit[1,0]: # tube OD
                self.Tube_OD_check.setChecked(True)
                self.Tube_OD.setText(", ".join([str(round(i,6)) for i in circuit[1,1]]))
    
            if circuit[2,0]: # tube ID
                self.Tube_ID_check.setChecked(True)
                self.Tube_ID.setText(", ".join([str(round(i,6)) for i in circuit[2,1]]))
    
            if circuit[3,0]: # tube logitudinal pitch
                self.Tube_Pl_check.setChecked(True)
                self.Tube_Pl.setText(", ".join([str(round(i,6)) for i in circuit[3,1]]))
    
            if circuit[4,0]: # tube transverse pitch
                self.Tube_Pt_check.setChecked(True)
                self.Tube_Pt.setText(", ".join([str(round(i,6)) for i in circuit[4,1]]))
    
            if circuit[5,0]: # number of parallel cirucits
                self.N_parallel_check.setChecked(True)
                self.N_parallel.setText(", ".join([str(round(i,6)) for i in circuit[5,1]]))
    
            if circuit[6,0]: # Number of tubes per bank
                self.N_tubes_check.setChecked(True)
                self.N_tubes.setText(", ".join([str(round(i,6)) for i in circuit[6,1]]))
    
            if circuit[7,0]: # Number of banks
                self.N_banks_check.setChecked(True)
                self.N_banks.setText(", ".join([str(round(i,6)) for i in circuit[7,1]]))
    
            if circuit[8,0]: # Fin thickness
                self.Fin_thickness_check.setChecked(True)
                self.Fin_thickness.setText(", ".join([str(round(i,6)) for i in circuit[8,1]]))
    
            if circuit[9,0]: # fin FPI
                self.Fin_FPI_check.setChecked(True)
                self.Fin_FPI.setText(", ".join([str(round(i,6)) for i in circuit[9,1]]))
            
    def save_fields_circuit(self,j):
        circuit = []

        if self.Tube_length_check.checkState():
            try:
                value = self.Tube_length.text()
                list_of_values = [length_unit_converter(i,self.Tube_length_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.Tube_length_check.text()+" values must be greater than 0")
                circuit.append([1,values,'circuit '+str(j+1)+' tube length','m'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.Tube_length_check.text()+" values")
        else:
            circuit.append([0,0,'',''])

        if self.Tube_OD_check.checkState():
            try:
                value = self.Tube_OD.text()
                list_of_values = [length_unit_converter(i,self.Tube_OD_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.Tube_OD_check.text()+" values must be greater than 0")
                circuit.append([1,values,'circuit '+str(j+1)+' tube outer diameter','m'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.Tube_OD_check.text()+" values")
        else:
            circuit.append([0,0,'',''])

        if self.Tube_ID_check.checkState():
            try:
                value = self.Tube_ID.text()
                list_of_values = [length_unit_converter(i,self.Tube_ID_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.Tube_ID_check.text()+" values must be greater than 0")
                circuit.append([1,values,'circuit '+str(j+1)+' tube inner diameter','m'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.Tube_ID_check.text()+" values")
        else:
            circuit.append([0,0,'',''])


        if self.Tube_Pl_check.checkState():
            try:
                value = self.Tube_Pl.text()
                list_of_values = [length_unit_converter(i,self.Tube_Pl_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.Tube_Pl_check.text()+" values must be greater than 0")
                circuit.append([1,values,'circuit '+str(j+1)+' tube longitudinal pitch','m'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.Tube_Pl_check.text()+" values")
        else:
            circuit.append([0,0,'',''])

        if self.Tube_Pt_check.checkState():
            try:
                value = self.Tube_Pt.text()
                list_of_values = [length_unit_converter(i,self.Tube_Pt_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.Tube_Pt_check.text()+" values must be greater than 0")
                circuit.append([1,values,'circuit '+str(j+1)+' tube transverse pitch','m'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.Tube_Pt_check.text()+" values")
        else:
            circuit.append([0,0,'',''])

        if self.N_parallel_check.checkState():
            try:
                value = self.N_parallel.text()
                list_of_values = [int(i) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.N_parallel_check.text()+" values must be greater than 0")
                circuit.append([1,values,'circuit '+str(j+1)+' number of parallel cirucits',''])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.N_parallel_check.text()+" values")
        else:
            circuit.append([0,0,'',''])

        if self.N_tubes_check.checkState():
            try:
                value = self.N_tubes.text()
                list_of_values = [int(i) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.N_tubes_check.text()+" values must be greater than 0")
                circuit.append([1,values,'circuit '+str(j+1)+' number of tubes per bank',''])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.N_tubes_check.text()+" values")
        else:
            circuit.append([0,0,'',''])

        if self.N_banks_check.checkState():
            try:
                value = self.N_banks.text()
                list_of_values = [int(i) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.N_banks_check.text()+" values must be greater than 0")
                circuit.append([1,values,'circuit '+str(j+1)+' number of banks',''])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.N_banks_check.text()+" values")
        else:
            circuit.append([0,0,'',''])

        if self.Fin_thickness_check.checkState():
            try:
                value = self.Fin_thickness.text()
                list_of_values = [length_unit_converter(i,self.Fin_thickness_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.Fin_thickness_check.text()+" values must be greater than 0")
                circuit.append([1,values,'circuit '+str(j+1)+' fin thickness','m'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.N_banks_check.text()+" values")
        else:
            circuit.append([0,0,'',''])

        if self.Fin_FPI_check.checkState():
            try:
                value = self.Fin_FPI.text()
                list_of_values = [float(i) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.Fin_FPI_check.text()+" values must be greater than 0")
                circuit.append([1,values,'circuit '+str(j+1)+' fin FPI','1/in'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.Fin_FPI_check.text()+" values")
        else:
            circuit.append([0,0,'',''])

        circuit = np.array(circuit, dtype=object)        
        return (1, circuit,'','')

    def raise_error_message(self,message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(message)
        msg.setWindowTitle("Sorry!")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        
    def validate(self):
        result = self.Circuit_selected_changed(self.Circuit_number.currentIndex(),enforce=True)
        at_least_one = False
        for circuit in self.circuits_data:
            if not isinstance(circuit,int):
                example = deepcopy(circuit)
                at_least_one = True
                break
        if at_least_one:
            for i,circuit in enumerate(self.circuits_data):
                if isinstance(circuit, int):
                    self.circuits_data[i] = np.zeros_like(example)
        else:
            for circuit in self.circuits_data:
                circuit = np.zeros([10,2])
        print(at_least_one)
        print(self.circuits_data)
        data = []
        if result[0]:
            data.append([0,self.circuits_data,'',''])
            if self.Air_Vdot_check.checkState():
                try:
                    value = self.Air_Vdot.text()
                    list_of_values = [volume_flowrate_unit_converter(i,self.Air_Vdot_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                    list_of_values = list(set(list_of_values))
                    values = tuple(sorted(list_of_values))
                    for i in values:
                        if not i > 0:
                            return (0,self.Air_Vdot_check.text()+" values must be greater than 0")
                    data.append([1,values, "air humid volume flowrate",'m3/s'])
                except:
                    import traceback
                    print(traceback.format_exc())
                    return (0, "Error in reading "+self.Air_Vdot_check.text()+" values")
            else:
                data.append([0,0,'',''])
    
            if self.Air_Pressure_check.checkState():
                try:
                    value = self.Air_Pressure.text()
                    list_of_values = [pressure_unit_converter(i,self.Air_Pressure_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                    list_of_values = list(set(list_of_values))
                    values = tuple(sorted(list_of_values))
                    for i in values:
                        if not 0 <= i < 1:
                            return (0,self.Air_Pressure_check.text()+" values must be between 0 and 100")
                    data.append([1,values, "air pressure",'Pa'])
                except:
                    import traceback
                    print(traceback.format_exc())
                    return (0, "Error in reading "+self.Air_Pressure_check.text()+" values")
            else:
                data.append([0,0,'',''])
    
            if self.Air_Temperature_check.checkState():
                try:
                    value = self.Air_Temperature.text()
                    list_of_values = [temperature_unit_converter(i,self.Air_Temperature_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                    list_of_values = list(set(list_of_values))
                    values = tuple(sorted(list_of_values))
                    data.append([1,values, "air temperature",'K'])
                except:
                    import traceback
                    print(traceback.format_exc())
                    return (0, "Error in reading "+self.Air_Temperature_check.text()+" values")
            else:
                data.append([0,0,'',''])

            if self.Air_RH_check.checkState():
                try:
                    value = self.Air_RH.text()
                    list_of_values = [float(i)/100 for i in value.replace(" ","").split(",")]
                    list_of_values = list(set(list_of_values))
                    values = tuple(sorted(list_of_values))
                    for i in values:
                        if not 0 <= i <= 1:
                            return (0,self.Air_RH_check.text()+" values must be between 0 and 100")
                    data.append([1,values, "air relative humidity",'%'])
                except:
                    import traceback
                    print(traceback.format_exc())
                    return (0, "Error in reading "+self.Air_RH_check.text()+" values")
            else:
                data.append([0,0,'',''])
            data = np.array(data, dtype=object)
            return (1, data)
        else:
            return (0, result[1])
    
    def ok_button_clicked(self):
        validate = self.validate()
        if validate[0]:
            atleast_once = False
            if any(validate[1][1:,0]):
                atleast_once = True
            for circuit in validate[1][0,1]:
                if any(circuit[:,0]):
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
        
    def refresh_ui(self,fintube_data):
        if fintube_data.Air_flow_direction == "Sub Heat Exchanger First":
            self.Circuit_number.addItem("Sub Heat Exchanger")
            for i in range(1,len(fintube_data.circuits)):
                self.Circuit_number.addItem("Circuit "+str(i))
        elif fintube_data.Air_flow_direction == "Sub Heat Exchanger Last":
            for i in range(len(fintube_data.circuits)-1):
                self.Circuit_number.addItem("Circuit "+str(i+1))
            self.Circuit_number.addItem("Sub Heat Exchanger")
        else:
            for i in range(len(fintube_data.circuits)):
                self.Circuit_number.addItem("Circuit "+str(i+1))
                
        self.tube_type_list = []
        for i in range(len(fintube_data.circuits)):
            if fintube_data.circuits[i].Tube_type == "Smooth":
                self.tube_type_list.append(True)
            else:
                self.tube_type_list.append(False)
        self.circuits_data = [0 for _ in range(len(fintube_data.circuits))]
        if self.tube_type_list[0]:
            self.Tube_ID_check.setEnabled(True)
        else:
            self.Tube_ID_check.setEnabled(False)
