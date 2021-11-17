from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
import os, sys
from unit_conversion import *
from CoolProp.CoolProp import HAPropsSI
import numpy as np

FROM_microchannel_Parametric_Main,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/microchannel_parametric.ui"))

class values():
    pass

class parametric_microchannel_Window(QDialog, FROM_microchannel_Parametric_Main):
    def __init__(self, parent=None):
        super(parametric_microchannel_Window, self).__init__(parent)
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
        if data[0,0]: # Tube width
            self.Tube_width_check.setChecked(True)
            self.Tube_width.setText(", ".join([str(round(i,6)) for i in data[0,1]]))
            
        if data[1,0]: # Tube height
            self.Tube_height_check.setChecked(True)
            self.Tube_height.setText(", ".join([str(round(i,6)) for i in data[1,1]]))
            
        if data[2,0]: # Tube length
            self.Tube_length_check.setChecked(True)
            self.Tube_length.setText(", ".join([str(round(i,6)) for i in data[2,1]]))
            
        if data[3,0]: # Tube spacing
            self.Tube_spacing_check.setChecked(True)
            self.Tube_spacing.setText(", ".join([str(round(i,6)) for i in data[3,1]]))

        if data[4,0]: # Number of ports
            self.N_ports_check.setChecked(True)
            self.N_ports.setText(", ".join([str(i) for i in data[4,1]]))
            
        if data[5,0]: # Port Dimension a
            self.port_dim_a_check.setChecked(True)
            self.port_dim_a.setText(", ".join([str(round(i,6)) for i in data[5,1]]))
            
        if data[6,0]: # Port Dimension b
            self.port_dim_b_check.setChecked(True)
            self.port_dim_b.setText(", ".join([str(round(i,6)) for i in data[6,1]]))
            
        if data[7,0]: # Fin Thickness
            self.Fin_thickness_check.setChecked(True)
            self.Fin_thickness.setText(", ".join([str(round(i,6)) for i in data[7,1]]))

        if data[8,0]: # Fin FPI
            self.Fin_FPI_check.setChecked(True)
            self.Fin_FPI.setText(", ".join([str(round(i,6)) for i in data[8,1]]))

        if data[9,0]: # Air inlet humid flow rate
            self.Air_Vdot_check.setChecked(True)
            self.Air_Vdot.setText(", ".join([str(round(i,6)) for i in data[9,1]]))

        if data[10,0]: # Air Pressure
            self.Air_Pressure_check.setChecked(True)
            self.Air_Pressure.setText(", ".join([str(round(i,6)) for i in data[10,1]]))

        if data[11,0]: # Air Temperature
            self.Air_Temperature_check.setChecked(True)
            self.Air_Temperature.setText(", ".join([str(round(i-273.15,6)) for i in data[11,1]]))

        if data[12,0]: # Air RH
            self.Air_RH_check.setChecked(True)
            self.Air_RH.setText(", ".join([str(round(i,6)*100) for i in data[12,1]]))
    
    def raise_error_message(self,message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(message)
        msg.setWindowTitle("Sorry!")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        
    def validate(self):
        data = []
        if self.Tube_width_check.checkState():
            try:
                value = self.Tube_width.text()
                list_of_values = [length_unit_converter(i,self.Tube_width_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.Tube_width_check.text()+" values must be greater than 0")
                data.append([1,values,'tube width','m'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.Tube_width_check.text()+" values")
        else:
            data.append([0,0,'',''])

        if self.Tube_height_check.checkState():
            try:
                value = self.Tube_height.text()
                list_of_values = [length_unit_converter(i,self.Tube_height_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.Tube_height_check.text()+" values must be greater than 0")
                data.append([1,values,'tube height','m'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.Tube_height_check.text()+" values")
        else:
            data.append([0,0,'',''])

        if self.Tube_length_check.checkState():
            try:
                value = self.Tube_length.text()
                list_of_values = [length_unit_converter(i,self.Tube_length_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.Tube_length_check.text()+" values must be greater than 0")
                data.append([1,values,'tube length','m'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.Tube_length_check.text()+" values")
        else:
            data.append([0,0,'',''])

        if self.Tube_spacing_check.checkState():
            try:
                value = self.Tube_spacing.text()
                list_of_values = [length_unit_converter(i,self.Tube_spacing_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.Tube_spacing_check.text()+" values must be greater than 0")
                data.append([1,values,'tube spacing','m'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.Tube_spacing_check.text()+" values")
        else:
            data.append([0,0,'',''])

        if self.N_ports_check.checkState():
            try:
                value = self.N_ports.text()
                list_of_values = [int(i) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.N_ports_check.text()+" values must be greater than 0")
                data.append([1,values,'number of ports',''])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.N_ports_check.text()+" values")
        else:
            data.append([0,0,'',''])

        if self.port_dim_a_check.checkState():
            try:
                value = self.port_dim_a.text()
                list_of_values = [length_unit_converter(i,self.port_dim_a_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.port_dim_a_check.text()+" values must be greater than 0")
                data.append([1,values,'port dimension (a)','m'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.port_dim_a_check.text()+" values")
        else:
            data.append([0,0,'',''])

        if self.port_dim_b_check.checkState():
            try:
                value = self.port_dim_b.text()
                list_of_values = [length_unit_converter(i,self.port_dim_b_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.port_dim_b_check.text()+" values must be greater than 0")
                data.append([1,values,'port dimension (b)','m'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.port_dim_b_check.text()+" values")
        else:
            data.append([0,0,'',''])

        if self.Fin_thickness_check.checkState():
            try:
                value = self.Fin_thickness.text()
                list_of_values = [length_unit_converter(i,self.Fin_thickness_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.Fin_thickness_check.text()+" values must be greater than 0")
                data.append([1,values,'fin thickness','m'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.Fin_thickness_check.text()+" values")
        else:
            data.append([0,0,'',''])

        if self.Fin_FPI_check.checkState():
            try:
                value = self.Fin_FPI.text()
                list_of_values = [length_unit_converter(i,self.Fin_FPI_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.Fin_FPI_check.text()+" values must be greater than 0")
                data.append([1,values,'fin FPI','1/in'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.Fin_FPI_check.text()+" values")
        else:
            data.append([0,0,'',''])

        if self.Air_Vdot_check.checkState():
            try:
                value = self.Air_Vdot.text()
                list_of_values = [volume_flowrate_unit_converter(i,self.Air_Vdot_unit.currentIndex()) for i in value.replace(" ","").split(",")]
                list_of_values = list(set(list_of_values))
                values = tuple(sorted(list_of_values))
                for i in values:
                    if not i > 0:
                        return (0,self.Air_Vdot_check.text()+" values must be greater than 0")
                data.append([1,values,'air humid volume flowrate','m3/s'])
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
                    if not i > 0:
                        return (0,self.Air_Pressure_check.text()+" values must be greater than 0")
                data.append([1,values,'air pressure','Pa'])
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
                data.append([1,values,'air temperature','K'])
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
                data.append([1,values,'air relative humidity','%'])
            except:
                import traceback
                print(traceback.format_exc())
                return (0, "Error in reading "+self.Air_RH_check.text()+" values")
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
        
    def refresh_ui(self,microchannel_data):
        if microchannel_data.Geometry.port_shape_index == 1:
            self.port_dim_b_check.setEnabled(False)