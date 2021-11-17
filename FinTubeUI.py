from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
import CoolProp as CP
import os, sys
from GUI_functions import write_Fin_tube, read_Fin_tube, load_last_location, save_last_location
from CoolProp.CoolProp import HAPropsSI
from sympy.parsing.sympy_parser import parse_expr
from sympy import S, Symbol
from FinTubeUI_Circuit import FinTube_Circuit_Window
from unit_conversion import *
from inputs_validation import check_Fintube
from copy import deepcopy

FROM_FinTube_Main,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Fin_tube_define.ui"))
FROM_FinTube_Air_Distribution,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Fin_tube_Air_Distribution.ui"))
FROM_FinTube_Fan_Model_efficiency,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Fin_tube_Fan_Model_Efficiency.ui"))
FROM_FinTube_Fan_Model_power,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Fin_tube_Fan_Model_Power.ui"))
FROM_FinTube_Fan_Model_curve,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Fin_tube_Fan_Model_Curve.ui"))

class values():
    pass

class FinTubeWindow(QDialog, FROM_FinTube_Main):
    def __init__(self, parent=None):
        # first UI
        super(FinTubeWindow, self).__init__(parent)
        self.setupUi(self)
        self.Delete_validation_range = False
        self.Fin_tube_cancel_button.clicked.connect(self.cancel_button)
        self.FinTube_N_series_circuits.valueChanged.connect(self.N_series_circuits_changed)
        self.FinTube_circuits = [values()]
        self.FinTube_Sub_Circuit = values()
        self.update_circuits_definition()
        self.FinTube_air_direction.currentIndexChanged.connect(self.Air_flow_direction_changed)
        self.FinTube_mode.currentIndexChanged.connect(self.FinTube_mode_changed)
        self.FinTube_solver.currentIndexChanged.connect(self.FinTube_solver_changed)
        self.FinTube_series_circuit_define_button.clicked.connect(self.FinTube_define_circuit)
        
        # defining validators
        only_number = QRegExpValidator(QRegExp("(([0-9]+\.[0-9]*[1-9][0-9]*)|([0-9]*[1-9][0-9]*\.[0-9]+)|([0-9]*[1-9][0-9]*))"))
        only_number_negative = QRegExpValidator(QRegExp("[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)"))
        self.FinTube_max_DP_error.setValidator(only_number)
        self.FinTube_air_flowrate.setValidator(only_number)
        self.FinTube_air_mass_flowrate.setValidator(only_number)
        self.FinTube_air_inlet_P.setValidator(only_number)
        self.FinTube_air_inlet_T.setValidator(only_number_negative)
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
        
        # definition of Air Flow Distribution
        self.FinTube_air_parallel_distribution_button.clicked.connect(self.FinTube_air_parallel_distribution_definition)
        self.Automatic_Distribution_button.clicked.connect(self.FinTube_air_automatic_distribution)
        
        # definition of fan model
        self.FinTube_fan_model_button.clicked.connect(self.FinTube_fan_model_definition)
        self.FinTube_fan_model.currentIndexChanged.connect(self.FinTube_fan_model_changed)

        # save button clicked
        self.Fin_tube_save_button.clicked.connect(self.save_button)

        # load button clicked
        self.Fin_tube_load_button.clicked.connect(self.load_button)

        # Ok button clicked
        self.Fin_tube_ok_button.clicked.connect(self.ok_button)

        # copy button cliecked
        self.FinTube_series_circuit_copy_button.clicked.connect(self.copy_circuit_button)
        
        # reverse circuits button
        self.reverse_circuits_button.clicked.connect(self.reverse_button)

        # flowrate type changed
        self.FinTube_air_flowrate_label.toggled.connect(self.air_flowrate_changed)
        self.FinTube_air_mass_flowrate_label.toggled.connect(self.air_flowrate_changed)
                
        # intially load images
        def images_loader(path,var_name,size):
            try:
                photo = QPixmap(path)
                photo = photo.scaledToWidth(size)
                setattr(self,var_name,photo)
            except:
                pass
        
        images_loader("photos/FinTube_Parallel_Air.png",'Parallel_Air_photo',400)
        images_loader("photos/FinTube_Series_Counter_Air.png",'Series_Counter_photo',400)
        images_loader("photos/FinTube_Series_Parallel_Air.png",'Series_Parallel_photo',400)
        images_loader("photos/FinTube_Sub_HX_Last_Air.png",'Sub_HX_last_photo',400)
        images_loader("photos/FinTube_Sub_HX_First_Air.png",'Sub_HX_first_photo',400)
        
        # intially populate available images
        if hasattr(self,"Parallel_Air_photo"):
            self.FinTube_Air_direction_photo.setPixmap(self.Parallel_Air_photo)
        else:
            self.FinTube_Air_direction_photo.clear()
            self.FinTube_Air_direction_photo.setText("Parallel Air Flow Direction Demonistration photo")

        # hiding solver option
        self.FinTube_solver_label.setVisible(False)
        self.FinTube_solver.setVisible(False)
        self.FinTube_max_DP_error_label.setVisible(False)
        self.FinTube_max_DP_error.setVisible(False)
        self.FinTube_max_DP_error_unit.setVisible(False)

        # enabling sub heat exchanger
        self.FinTube_Sub_HX_check.stateChanged.connect(self.Sub_HX_check_changed)
        
        # defining sub heat exchanger
        self.FinTube_Sub_HX_button.clicked.connect(self.FinTube_define_sub_circuit)

    def air_flowrate_changed(self):
        if self.FinTube_air_flowrate_label.isChecked():
            self.FinTube_air_flowrate.setEnabled(True)
            self.FinTube_air_flowrate_unit.setEnabled(True)
            self.FinTube_air_mass_flowrate.setEnabled(False)
            self.FinTube_air_mass_flowrate_unit.setEnabled(False)
        elif self.FinTube_air_mass_flowrate_label.isChecked():
            self.FinTube_air_mass_flowrate.setEnabled(True)
            self.FinTube_air_mass_flowrate_unit.setEnabled(True)
            self.FinTube_air_flowrate.setEnabled(False)
            self.FinTube_air_flowrate_unit.setEnabled(False)

    def Sub_HX_check_changed(self,state):
        self.FinTube_Sub_HX_button.setEnabled(state)
        self.FinTube_air_direction.clear()
        if state:
            self.FinTube_air_direction.addItems(["Sub Heat Exchanger First","Sub Heat Exchanger Last"])
        else:
            self.FinTube_air_direction.addItems(["Parallel","Series-Parallel","Series-Counter"])
        self.update_circuits_definition()

    def enable_range_validation(self):
        if self.FinTube_air_flowrate_label.isChecked():
            self.FinTube_air_flowrate.editingFinished.connect(lambda: self.validate_range_item("lineedit",'volume_flowrate'))
        elif self.FinTube_air_mass_flowrate_label.isChecked():
            self.FinTube_air_mass_flowrate.editingFinished.connect(lambda: self.validate_range_item("lineedit",'mass_flowrate'))

    def validate_range_item(self,data_type,conversion=None):
        if hasattr(self,"validation_range"):
            sender = self.sender()
            prop_name = sender.objectName()
    
            name = getattr(self,prop_name+"_label").text()
            
            # getting value
            failed = False
            if data_type == "lineedit":
                try:
                    value = float(sender.text())
                    failed = False
                except:
                    failed = True
                    
            elif data_type == "spinbox":            
                value = sender.value()
            
            # converting value to SI units
            if conversion == "temperature_diff":
                true_value = temperature_diff_unit_converter(value,getattr(self,prop_name+"_unit").currentIndex())
    
            elif conversion == "mass":
                true_value = mass_unit_converter(value,getattr(self,prop_name+"_unit").currentIndex())
    
            elif conversion == "power":
                true_value = power_unit_converter(value,getattr(self,prop_name+"_unit").currentIndex())
    
            elif conversion == "pressure":
                true_value = pressure_unit_converter(value,getattr(self,prop_name+"_unit").currentIndex())
    
            elif conversion == "mass_flowrate":
                true_value = mass_flowrate_unit_converter(value,getattr(self,prop_name+"_unit").currentIndex())
    
            elif conversion == "volume_flowrate":
                true_value = volume_flowrate_unit_converter(value,getattr(self,prop_name+"_unit").currentIndex())
    
            elif conversion == "temperature":
                true_value = temperature_unit_converter(value,getattr(self,prop_name+"_unit").currentIndex())
    
            elif conversion == "length":
                true_value = length_unit_converter(value,getattr(self,prop_name+"_unit").currentIndex())
    
            elif conversion == "volume":
                true_value = volume_unit_converter(value,getattr(self,prop_name+"_unit").currentIndex())
    
            elif conversion == "angle":
                true_value = angle_unit_converter(value,getattr(self,prop_name+"_unit").currentIndex())
    
            elif conversion == "thermal_K":
                true_value = Thermal_K_unit_converter(value,getattr(self,prop_name+"_unit").currentIndex())
    
            elif conversion == "HTC":
                true_value = HTC_unit_converter(value,getattr(self,prop_name+"_unit").currentIndex())
            
            elif conversion == None:
                true_value = value
            
            validation_range = getattr(self.validation_range,prop_name)
            minimum = validation_range[1]
            maximum = validation_range[2]
            if maximum != None and true_value > maximum:
                self.raise_error_message("The value you enter for "+name+" which is "+"%.5g" % true_value+" is higher than recommended maximum value of "+"%.5g" % maximum+". The original value was "+"%.5g" % validation_range[0]+". (all in SI units.)")
            elif minimum != None and true_value < minimum:
                self.raise_error_message("The value you enter for "+name+" which is "+"%.5g" % true_value+ " is lower than recommended minimum value of "+"%.5g" % minimum+". The original value was "+"%.5g" % validation_range[0]+". (all in SI units.)")

    def delete_validation_range(self):
        if hasattr(self,"validation_range"):
            delattr(self,"validation_range")
        self.Delete_validation_range = True

    def reverse_button(self):
        Message = "This will reverse the series circuits sequence, convert connections of each circuit from counter flow to parallel flow and vice versa, reverse the air distribution (if parallel option is selected), and reverse sub heat exchanger location. are you sure?"
        reply = QMessageBox.question(self, 'Message',
                         Message, QMessageBox.Yes, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.reverse_series_circuits()
            if hasattr(self,"validation_range"):
                self.delete_validation_range()
            self.raise_information_message("Circuits sequence reversed!")
    
    def reverse_series_circuits(self):
        self.FinTube_circuits = list(reversed(self.FinTube_circuits))
        if hasattr(self,"Parallel_Air_Distribution"):
            self.Parallel_Air_Distribution = list(reversed(self.Parallel_Air_Distribution))
        if self.FinTube_air_direction.currentText() == "Sub Heat Exchanger First":
            self.FinTube_air_direction.setCurrentIndex(1)
        elif self.FinTube_air_direction.currentText() == "Sub Heat Exchanger Last":
            self.FinTube_air_direction.setCurrentIndex(0)
        if self.FinTube_mode.currentIndex() == 0:
            for i,circuit in enumerate(self.FinTube_circuits):
                if hasattr(self.FinTube_circuits[i],"defined"):
                    if self.FinTube_circuits[i].circuitry == 0:
                        self.FinTube_circuits[i].circuitry = 1
                        self.FinTube_circuits[i].circuitry_name = "Parallel"
                    elif self.FinTube_circuits[i].circuitry == 1:
                        self.FinTube_circuits[i].circuitry = 0
                        self.FinTube_circuits[i].circuitry_name = "Counter"
                if hasattr(self.FinTube_Sub_Circuit,"defined"):
                    if self.FinTube_Sub_Circuit.circuitry == 0:
                        self.FinTube_Sub_Circuit.circuitry = 1
                        self.FinTube_Sub_Circuit.circuitry_name = "Parallel"
                    elif self.FinTube_Sub_Circuit.circuitry == 1:
                        self.FinTube_Sub_Circuit.circuitry = 0
                        self.FinTube_Sub_Circuit.circuitry_name = "Counter"
                
        self.update_circuits_definition()

    def copy_circuit_button(self):
        if self.FinTube_series_circuit_copy_from.currentIndex() != -1:
            if self.FinTube_series_circuit_copy_to.currentIndex() != -1:
                try:
                    from_id = int(self.FinTube_series_circuit_copy_from.currentText()) - 1
                except:
                    from_id = -2
                try:    
                    to_id = int(self.FinTube_series_circuit_copy_to.currentText()) - 1
                except:
                    to_id = -2
                    
                if to_id == -2:
                    if hasattr(self.FinTube_Sub_Circuit,"defined"):
                        quit_msg = "You will lose all data in saved in sub heat exchanger circuit"
                    else:
                        quit_msg = "Are you sure?"
                        
                elif hasattr(self.FinTube_circuits[to_id],"defined") and self.FinTube_circuits[to_id].defined == True:
                    quit_msg = "You will lose all data in saved in cirucit " + str(to_id+1)
                else:
                    quit_msg = "Are you sure?"
                reply = QMessageBox.question(self, 'Message',
                                 quit_msg, QMessageBox.Yes, QMessageBox.No)
            
                if reply == QMessageBox.Yes:
                    self.copy_circuit(from_id,to_id)
                    if hasattr(self,"validation_range"):
                        self.delete_validation_range()
            else:
                self.raise_error_message("Please choose a circuit to copy from first")
        else:
            self.raise_error_message("Please choose a circuit to copy from first")

    def copy_circuit(self,from_id,to_id):
        if from_id == to_id:
            self.raise_error_message("You can not copy a circuit to itself")
        else:
            if from_id != -2:
                from_circuit = deepcopy(self.FinTube_circuits[from_id])
            else:
                from_circuit = deepcopy(self.FinTube_Sub_Circuit)
                if hasattr(from_circuit,"sub_HX_values"):
                    delattr(from_circuit,"sub_HX_values")
            if to_id != -2:
                self.FinTube_circuits[to_id] = from_circuit
            else:
                self.FinTube_Sub_Circuit = from_circuit
            self.update_circuits_definition()
            self.raise_information_message("Circuit was copied successfully!")
        
    def raise_error_message(self,message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(message)
        msg.setWindowTitle("Error!")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def raise_information_message(self,message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(message)
        msg.setWindowTitle("Message")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def ok_button(self):
        validate = self.validate()
        if validate == 0:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please fill all empty fields")
            msg.setWindowTitle("Empty Fields!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        elif validate == 2:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please Complete all circuits data")
            msg.setWindowTitle("Circuit not defined!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        elif validate == 3:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please Complete Air Flow Distribution")
            msg.setWindowTitle("Air Flow Distribution not defined!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        elif validate == 4:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please Complete Fan Model Data")
            msg.setWindowTitle("Fan Model not defined!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            
        elif validate == 1:
            HX = values()
            HX.name = str(self.FinTube_name.text())
            HX.solver = str(self.FinTube_solver.currentText())
            HX.model = str(self.FinTube_mode.currentText())
            if self.FinTube_mode.currentIndex() == 0:    
                HX.N_segments = int(self.FinTube_N_segments.value())
            HX.Accurate = str(self.FinTube_accurate.currentText())
            HX.N_series_Circuits = int(self.FinTube_N_series_circuits.value())
            HX.HX_Q_tol = float(self.FinTube_HX_Q_tolerance.value())/100
            HX.N_iterations = int(self.FinTube_max_N_iterations.value())
            if self.FinTube_solver.currentIndex() == 1:
                HX.HX_DP_tol = float(self.FinTube_max_DP_error.text())
            HX.Air_flow_direction = str(self.FinTube_air_direction.currentText())
            if HX.Air_flow_direction == "Sub Heat Exchanger First":
                self.FinTube_circuits = [self.FinTube_Sub_Circuit] + self.FinTube_circuits
            elif HX.Air_flow_direction == "Sub Heat Exchanger Last":
                self.FinTube_circuits.append(self.FinTube_Sub_Circuit)
            if self.FinTube_Sub_HX_check.isChecked():
                HX.Air_Distribution = self.Parallel_Air_Distribution            
            else:
                if self.FinTube_air_direction.currentIndex() == 0:
                    HX.Air_Distribution = self.Parallel_Air_Distribution
            HX.Fan_model = self.FinTube_fan_model.currentText()
            if self.FinTube_fan_model.currentIndex() == 0:
                HX.Fan_model_efficiency_exp = self.Fan_Model_Efficiency
            elif self.FinTube_fan_model.currentIndex() == 1:
                HX.Fan_model_P_exp = self.Fan_Model_Curve_P
                HX.Fan_model_DP_exp = self.Fan_Model_Curve_DP
            elif self.FinTube_fan_model.currentIndex() == 2:
                HX.Fan_model_power_exp = self.Fan_Model_Power

            if self.FinTube_air_flowrate_label.isChecked():
                HX.Vdot_ha = volume_flowrate_unit_converter(self.FinTube_air_flowrate.text(),self.FinTube_air_flowrate_unit.currentIndex())
            elif self.FinTube_air_mass_flowrate_label.isChecked():
                HX.mdot_da = mass_flowrate_unit_converter(self.FinTube_air_mass_flowrate.text(),self.FinTube_air_mass_flowrate_unit.currentIndex())
            
            HX.Air_P = pressure_unit_converter(self.FinTube_air_inlet_P.text(),self.FinTube_air_inlet_P_unit.currentIndex())
            HX.Air_T = temperature_unit_converter(self.FinTube_air_inlet_T.text(),self.FinTube_air_inlet_T_unit.currentIndex())
            HX.Air_RH = float(self.FinTube_air_inlet_RH.value()) / 100
            HX.circuits = self.FinTube_circuits
            if hasattr(self,"capacity_validation"):
                if self.capacity_validation:
                    HX.capacity_validation_table = self.capacity_validation_table
            validation = check_Fintube(HX)
            if validation[0] == 1:
                self.HX_data = HX
                self.close()
            elif validation[0] == 2:
                reply = QMessageBox.warning(self, 'Warning!',
                    validation[1]+" Continue?", QMessageBox.Yes | 
                    QMessageBox.No, QMessageBox.No)
            
                if reply == QMessageBox.Yes:
                    self.HX_data = HX
                    self.close()
                else:
                    pass
            else:
                self.raise_error_message(validation[1])            

    def load_fields(self,HX):
        index = self.FinTube_solver.findText(HX.solver, Qt.MatchFixedString)
        self.FinTube_solver.setCurrentIndex(index)
        index = self.FinTube_mode.findText(HX.model, Qt.MatchFixedString)
        self.FinTube_mode.setCurrentIndex(index)
        if hasattr(HX,"N_segments"):
            self.FinTube_N_segments.setValue(HX.N_segments)
        if self.FinTube_mode.currentIndex() == 1:
            self.FinTube_N_segments_label.setVisible(False)
            self.FinTube_N_segments.setVisible(False)
        else:
            self.FinTube_N_segments_label.setVisible(True)
            self.FinTube_N_segments.setVisible(True)            
        index = self.FinTube_accurate.findText(HX.Accurate, Qt.MatchFixedString)
        self.FinTube_accurate.setCurrentIndex(index)
        self.FinTube_name.setText(HX.name)
        self.FinTube_N_series_circuits.setValue(HX.N_series_Circuits)
        self.FinTube_circuits = HX.circuits
        self.N_series_circuits_changed()
        self.FinTube_HX_Q_tolerance.setValue(HX.HX_Q_tol*100)
        self.FinTube_max_N_iterations.setValue(HX.N_iterations)
        if hasattr(HX,'DP_tol'):
            self.FinTube_max_DP_error.setText(str(HX.DP_tol))
        if HX.Air_flow_direction == "Sub Heat Exchanger First":
            self.FinTube_Sub_HX_check.setChecked(True)
            self.FinTube_Sub_Circuit = deepcopy(self.FinTube_circuits[0])
            print(self.FinTube_Sub_Circuit.defined)
            self.FinTube_circuits = self.FinTube_circuits[1:]
        elif HX.Air_flow_direction == "Sub Heat Exchanger Last":
            self.FinTube_Sub_HX_check.setChecked(True)
            self.FinTube_Sub_Circuit = deepcopy(self.FinTube_circuits[-1])
            self.FinTube_circuits = self.FinTube_circuits[:-1]
        index = self.FinTube_air_direction.findText(HX.Air_flow_direction, Qt.MatchFixedString)
        self.FinTube_air_direction.setCurrentIndex(index)
        if hasattr(HX,'Air_Distribution'):
            self.Parallel_Air_Distribution = HX.Air_Distribution
        index = self.FinTube_fan_model.findText(HX.Fan_model, Qt.MatchFixedString)
        self.FinTube_fan_model.setCurrentIndex(index)
        if hasattr(HX,'Fan_model_efficiency_exp'):
            self.Fan_Model_Efficiency = HX.Fan_model_efficiency_exp
        if hasattr(HX,'Fan_model_power_exp'):
            self.Fan_Model_Power = HX.Fan_model_power_exp
        if hasattr(HX,'Fan_model_P_exp'):
            self.Fan_Model_Curve_P = HX.Fan_model_P_exp
        if hasattr(HX,'Fan_model_DP_exp'):
            self.Fan_Model_Curve_DP = HX.Fan_model_DP_exp

        if hasattr(HX,"Vdot_ha"):
            self.FinTube_air_flowrate.setText('%s' % float('%.5g' % (HX.Vdot_ha)))
            self.FinTube_air_flowrate_label.setChecked(True)
        elif hasattr(HX,"mdot_da"):
            self.FinTube_air_mass_flowrate.setText('%s' % float('%.5g' % (HX.mdot_da)))
            self.FinTube_air_mass_flowrate_label.setChecked(True)

        self.FinTube_air_inlet_P.setText('%s' % float('%.5g' % (HX.Air_P)))

        self.FinTube_air_inlet_T.setText('%s' % float('%.5g' % (HX.Air_T-273.15)))
        
        self.FinTube_air_inlet_RH.setValue(HX.Air_RH*100)

        self.update_circuits_definition()
        
    def load_button(self):
        path = QFileDialog.getOpenFileName(self, 'Open Fin Tube HX file',directory=load_last_location(),filter="Heat Exchanger file (*.hx);;All files (*.*)")[0]
        if path != "":
            save_last_location(path)
            result = read_Fin_tube(path)
            if result[0]:
                try:
                    HX = result[1]
                    self.load_fields(HX)
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("The file was loaded successfully")
                    msg.setWindowTitle("Success!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                except:
                    import traceback
                    print(traceback.format_exc())
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("File could not be loaded")
                    msg.setWindowTitle("Sorry!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
            else:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("File could not be loaded")
                msg.setWindowTitle("Sorry!")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
        
    def save_button(self):
        validate = self.validate()
        if validate == 0:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please fill all empty fields")
            msg.setWindowTitle("Empty Fields!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        elif validate == 2:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please Complete all circuits data")
            msg.setWindowTitle("Circuit not defined!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        elif validate == 3:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please Complete Air Flow Distribution")
            msg.setWindowTitle("Air Flow Distribution not defined!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        elif validate == 4:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please Complete Fan Model Data")
            msg.setWindowTitle("Fan Model not defined!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            
        elif validate == 1:
            path = QFileDialog.getSaveFileName(self, caption='Save Fin Tube HX file',directory=load_last_location(),filter="Heat Exchanger file (*.hx);;All files (*.*)")[0]
            if path != "":
                save_last_location(path)
                if path[-3:].lower() != ".hx":
                    path = path+".hx"
                HX = values()
                HX.name = str(self.FinTube_name.text())
                HX.solver = str(self.FinTube_solver.currentText())
                HX.model = str(self.FinTube_mode.currentText())
                if self.FinTube_mode.currentIndex() == 0:    
                    HX.N_segments = int(self.FinTube_N_segments.value())
                HX.Accurate = str(self.FinTube_accurate.currentText())
                HX.N_series_Circuits = int(self.FinTube_N_series_circuits.value())
                HX.HX_Q_tol = float(self.FinTube_HX_Q_tolerance.value())/100
                HX.N_iterations = int(self.FinTube_max_N_iterations.value())
                if self.FinTube_solver.currentIndex() == 1:
                    HX.HX_DP_tol = pressure_unit_converter(self.FinTube_max_DP_error.text(),self.FinTube_max_DP_error_unit.currentIndex())
                HX.Air_flow_direction = str(self.FinTube_air_direction.currentText())
                if HX.Air_flow_direction == "Sub Heat Exchanger First":
                    self.FinTube_circuits = [self.FinTube_Sub_Circuit] + self.FinTube_circuits
                elif HX.Air_flow_direction == "Sub Heat Exchanger Last":
                    self.FinTube_circuits.append(self.FinTube_Sub_Circuit)
                if self.FinTube_Sub_HX_check.isChecked():
                    HX.Air_Distribution = self.Parallel_Air_Distribution            
                else:
                    if self.FinTube_air_direction.currentIndex() == 0:
                        HX.Air_Distribution = self.Parallel_Air_Distribution
                HX.Fan_model = self.FinTube_fan_model.currentText()
                if self.FinTube_fan_model.currentIndex() == 0:
                    HX.Fan_model_efficiency_exp = self.Fan_Model_Efficiency
                elif self.FinTube_fan_model.currentIndex() == 1:
                    HX.Fan_model_P_exp = self.Fan_Model_Curve_P
                    HX.Fan_model_DP_exp = self.Fan_Model_Curve_DP
                elif self.FinTube_fan_model.currentIndex() == 2:
                    HX.Fan_model_power_exp = self.Fan_Model_Power
                if self.FinTube_air_flowrate_label.isChecked():
                    HX.Vdot_ha = volume_flowrate_unit_converter(self.FinTube_air_flowrate.text(),self.FinTube_air_flowrate_unit.currentIndex())
                elif self.FinTube_air_mass_flowrate_label.isChecked():
                    HX.mdot_da = mass_flowrate_unit_converter(self.FinTube_air_mass_flowrate.text(),self.FinTube_air_mass_flowrate_unit.currentIndex())                
                HX.Air_P = pressure_unit_converter(self.FinTube_air_inlet_P.text(),self.FinTube_air_inlet_P_unit.currentIndex())
                HX.Air_T = temperature_unit_converter(self.FinTube_air_inlet_T.text(),self.FinTube_air_inlet_T_unit.currentIndex())
                HX.Air_RH = float(self.FinTube_air_inlet_RH.value()) / 100
                HX.circuits = self.FinTube_circuits
                
                result = write_Fin_tube(HX,path)
                if result:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("The file was saved successfully")
                    msg.setWindowTitle("Success!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                else:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("File could not be saved")
                    msg.setWindowTitle("Sorry!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
            
    def FinTube_define_circuit(self):
        FinTube_Circuit_dialog = FinTube_Circuit_Window()
        FinTube_Circuit_dialog.setFocusPolicy(Qt.StrongFocus)
        if self.FinTube_mode.currentIndex() == 1:
            FinTube_Circuit_dialog.FinTube_circuit_circuitry.setEnabled(False)
            FinTube_Circuit_dialog.FinTube_circuit_tube_staggering.setEnabled(False)
        if hasattr(self.FinTube_circuits[int(self.FinTube_series_circuit_define.currentIndex())],"defined"):
            Circuit = self.FinTube_circuits[int(self.FinTube_series_circuit_define.currentIndex())]
            if self.FinTube_mode.currentIndex() == 1:
                FinTube_Circuit_dialog.FinTube_circuit_circuitry_label.setVisible(False)
                FinTube_Circuit_dialog.FinTube_circuit_circuitry.setVisible(False)
                FinTube_Circuit_dialog.FinTube_circuit_circuitry_button.setVisible(False)
                FinTube_Circuit_dialog.FinTube_circuit_tube_staggering.setVisible(False)
                FinTube_Circuit_dialog.FinTube_circuit_tube_staggering_label.setVisible(False)

            FinTube_Circuit_dialog.load_fields(Circuit)
            if hasattr(self,"validation_range"):
                circuit_num = self.FinTube_series_circuit_define.currentIndex()
                if hasattr(self.validation_range,"Circuits_"+str(circuit_num)):
                    FinTube_Circuit_dialog.validation_range = getattr(self.validation_range,"Circuits_"+str(circuit_num))
                    FinTube_Circuit_dialog.enable_range_validation()
        
        FinTube_Circuit_dialog.exec_()
        
        if FinTube_Circuit_dialog.Delete_validation_range:
            self.delete_validation_range()
        
        if hasattr(FinTube_Circuit_dialog,"Circuit_info"):
            self.FinTube_circuits[int(self.FinTube_series_circuit_define.currentIndex())] = FinTube_Circuit_dialog.Circuit_info
        self.update_circuits_definition()

    def FinTube_define_sub_circuit(self):
        FinTube_Circuit_dialog = FinTube_Circuit_Window()
        FinTube_Circuit_dialog.setFocusPolicy(Qt.StrongFocus)
        if self.FinTube_mode.currentIndex() == 1:
            FinTube_Circuit_dialog.FinTube_circuit_circuitry.setEnabled(False)
            FinTube_Circuit_dialog.FinTube_circuit_tube_staggering.setEnabled(False)
        if hasattr(self.FinTube_Sub_Circuit,"defined"):
            Circuit = self.FinTube_Sub_Circuit
            if self.FinTube_mode.currentIndex() == 1:
                FinTube_Circuit_dialog.FinTube_circuit_circuitry_label.setVisible(False)
                FinTube_Circuit_dialog.FinTube_circuit_circuitry.setVisible(False)
                FinTube_Circuit_dialog.FinTube_circuit_circuitry_button.setVisible(False)
                FinTube_Circuit_dialog.FinTube_circuit_tube_staggering.setVisible(False)
                FinTube_Circuit_dialog.FinTube_circuit_tube_staggering_label.setVisible(False)
            FinTube_Circuit_dialog.load_fields(Circuit)
            if hasattr(self,"validation_range"):
                if self.FinTube_air_direction.currentIndex() == 0:
                    circuit_num = 0
                else:
                    circuit_num = len(self.FinTube_circuits)+1
                if hasattr(self.validation_range,"Circuits_"+str(circuit_num)):
                    FinTube_Circuit_dialog.validation_range = getattr(self.validation_range,"Circuits_"+str(circuit_num))
                    FinTube_Circuit_dialog.enable_range_validation()
        FinTube_Circuit_dialog.enable_sub_HX()
        FinTube_Circuit_dialog.exec_()
        
        if FinTube_Circuit_dialog.Delete_validation_range:
            self.delete_validation_range()
        
        if hasattr(FinTube_Circuit_dialog,"Circuit_info"):
            self.FinTube_Sub_Circuit = FinTube_Circuit_dialog.Circuit_info
        self.update_circuits_definition()
    
    def validate(self):
        if str(self.FinTube_name.text()).strip() in ["","-","."]:
            return 0
        if self.FinTube_solver.currentIndex() == 1:
            if str(self.FinTube_max_DP_error.text()).strip() in ["","-","."]:
                return 0
        if self.FinTube_air_flowrate_label.isChecked():
            if str(self.FinTube_air_flowrate.text()).strip() in ["","-","."]:
                return 0
        elif self.FinTube_air_mass_flowrate_label.isChecked():
            if str(self.FinTube_air_mass_flowrate.text()).strip() in ["","-","."]:
                return 0

        if str(self.FinTube_air_inlet_P.text()).strip() in ["","-","."]:
            return 0
        if str(self.FinTube_air_inlet_T.text()).strip() in ["","-","."]:
            return 0
        for circuit in self.FinTube_circuits:
            if not hasattr(circuit,"defined"):
                return 2
            elif circuit.defined == False:
                return 2
        if self.FinTube_Sub_HX_check.isChecked():
            if not hasattr(self.FinTube_Sub_Circuit,'defined'):
                return 2
        if self.FinTube_Sub_HX_check.isChecked():
            if not hasattr(self,"Parallel_Air_Distribution"):
                return 3
        else:
            if self.FinTube_air_direction.currentIndex() == 0:
                if not hasattr(self,"Parallel_Air_Distribution"):
                    return 3
        if self.FinTube_fan_model.currentIndex() == 0:
            if not hasattr(self,"Fan_Model_Efficiency"):
                return 4
        elif self.FinTube_fan_model.currentIndex() == 1:
            if not hasattr(self,"Fan_Model_Curve_P"):
                return 4
            if not hasattr(self,"Fan_Model_Curve_DP"):
                return 4
        elif self.FinTube_fan_model.currentIndex() == 2:
            if not hasattr(self,"Fan_Model_Power"):
                return 4
            
        return 1
    
    def FinTube_fan_model_changed(self):
        if hasattr(self,"Fan_Model_Efficiency"):
            delattr(self,"Fan_Model_Efficiency")
        if hasattr(self,"Fan_Model_Power"):
            delattr(self,"Fan_Model_Power")
        if hasattr(self,"Fan_Model_Curve_P"):
            delattr(self,"Fan_Model_Curve_P")
        if hasattr(self,"Fan_Model_Curve_DP"):
            delattr(self,"Fan_Model_Curve_DP")
        if self.FinTube_fan_model.currentIndex() == 1:
            self.FinTube_air_flowrate_label.setText("Initial Guess for Inlet Humid Air Volume Flow Rate")
            self.FinTube_air_mass_flowrate_label.setText("Initial Guess for Inlet Dry Air Mass Flow Rate")
        else:
            self.FinTube_air_flowrate_label.setText("Inlet Humid Air Volume Flow Rate")
            self.FinTube_air_mass_flowrate_label.setText("Inlet Dry Air Mass Flow Rate")            
    
    def FinTube_fan_model_definition(self):
        if self.FinTube_fan_model.currentIndex() == 0:            
            FinTube_Fan_Model_Efficiency_dialog = FinTube_Fan_Model_Efficiency(self)
            FinTube_Fan_Model_Efficiency_dialog.setFocusPolicy(Qt.StrongFocus)
            if hasattr(self,"Fan_Model_Efficiency"):
                FinTube_Fan_Model_Efficiency_dialog.FinTube_efficiency_exp.setText(self.Fan_Model_Efficiency)
            FinTube_Fan_Model_Efficiency_dialog.exec_()
            if hasattr(FinTube_Fan_Model_Efficiency_dialog,"eff_exp"):
                self.Fan_Model_Efficiency = str(FinTube_Fan_Model_Efficiency_dialog.eff_exp)
        elif self.FinTube_fan_model.currentIndex() == 1:            
            FinTube_Fan_Model_Curve_dialog = FinTube_Fan_Model_Curve(self)
            if hasattr(self,"Fan_Model_Curve_P"):
                FinTube_Fan_Model_Curve_dialog.FinTube_P_exp.setText(self.Fan_Model_Curve_P)
            if hasattr(self,"Fan_Model_Curve_DP"):
                FinTube_Fan_Model_Curve_dialog.FinTube_DP_exp.setText(self.Fan_Model_Curve_DP)
            FinTube_Fan_Model_Curve_dialog.exec_()
            if hasattr(FinTube_Fan_Model_Curve_dialog,"P_exp"):
                self.Fan_Model_Curve_P = str(FinTube_Fan_Model_Curve_dialog.P_exp)
            if hasattr(FinTube_Fan_Model_Curve_dialog,"DP_exp"):
                self.Fan_Model_Curve_DP = str(FinTube_Fan_Model_Curve_dialog.DP_exp)
        elif self.FinTube_fan_model.currentIndex() == 2:            
            FinTube_Fan_Model_Power_dialog = FinTube_Fan_Model_Power(self)
            FinTube_Fan_Model_Power_dialog.setFocusPolicy(Qt.StrongFocus)
            if hasattr(self,"Fan_Model_Power"):
                FinTube_Fan_Model_Power_dialog.FinTube_power_exp.setText(self.Fan_Model_Power)
            FinTube_Fan_Model_Power_dialog.exec_()
            if hasattr(FinTube_Fan_Model_Power_dialog,"power_exp"):
                self.Fan_Model_Power = str(FinTube_Fan_Model_Power_dialog.power_exp)
    
    def FinTube_air_parallel_distribution_definition(self):
        N = int(self.FinTube_N_series_circuits.value())
        FinTube_air_parallel_distribution_dialog = FinTube_Air_Distribution(self,N)
        FinTube_air_parallel_distribution_dialog.setFocusPolicy(Qt.StrongFocus)
        if hasattr(self,"Parallel_Air_Distribution"):
            for col in range(N):
                FinTube_air_parallel_distribution_dialog.FinTube_Distrubution.setItem(0, col, QTableWidgetItem(str(self.Parallel_Air_Distribution[col])))
        FinTube_air_parallel_distribution_dialog.exec_()
        if hasattr(FinTube_air_parallel_distribution_dialog,"Distribution_Result"):
            self.Parallel_Air_Distribution = FinTube_air_parallel_distribution_dialog.Distribution_Result

    def FinTube_air_automatic_distribution(self):
        qm = QMessageBox
        ret = qm.question(self,'Automatic air distribution', "Do you want to set air distribution ratios according to the total number of tubes per bank for each series circuit?", qm.Yes | qm.No)
        if ret == qm.Yes:        
            vertical_tubes = []
            Not_defined = False
            Warning_N_banks = False
            N_bank = 0
            for i,circuit in enumerate(self.FinTube_circuits):
                if not hasattr(circuit,"defined"):
                    Not_defined = True
                else:
                    if N_bank == 0:
                        N_bank = circuit.N_bank
                    else:
                        if N_bank != circuit.N_bank:
                            Warning_N_banks = True
                    vertical_tubes.append(int(circuit.N_tube_per_bank * circuit.N_Circuits))
            
            if Not_defined:
                self.raise_error_message("Please define all series circuits first.")
            else:
                if Warning_N_banks:
                    ret = qm.warning(self,'Warning', "Number of banks is not the same in all circuits, contrinue?", qm.Yes | qm.No)
                    if ret == qm.Yes:
                        Warning_N_banks = False
                
                if not Warning_N_banks:
                    ratios = [round(i/sum(vertical_tubes),5) for i in vertical_tubes]
                    self.Parallel_Air_Distribution = ratios
                    self.raise_information_message("Ratios has been set successfully!")
                
    def FinTube_solver_changed(self):
        if self.FinTube_solver.currentIndex() == 0:
            self.FinTube_max_DP_error.setEnabled(False)
            self.FinTube_max_DP_error_unit.setEnabled(False)
        elif self.FinTube_solver.currentIndex() == 1:
            self.FinTube_max_DP_error.setEnabled(True)
            self.FinTube_max_DP_error_unit.setEnabled(True)        
    
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
                
                RH = round(HAPropsSI("R","P",Air_Pressure,"T",Air_DBT,"B",Air_WBT) * 100, 2)
            
            # HR
            elif self.FinTube_air_calculator_option.currentIndex() == 1:
                HR = float(self.FinTube_air_calculator_2nd.text())
                RH = round(HAPropsSI("R","P",Air_Pressure,"T",Air_DBT,"W",HR) * 100,2)
            
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
            
    def Air_flow_direction_changed(self):
        if self.FinTube_air_direction.currentText() in ["Parallel"]:
            self.FinTube_air_parallel_distribution_button.setEnabled(True)
            self.Automatic_Distribution_button.setEnabled(True)
            if hasattr(self,"Parallel_Air_photo"):
                self.FinTube_Air_direction_photo.setPixmap(self.Parallel_Air_photo)
            else:
                self.FinTube_Air_direction_photo.clear()
                self.FinTube_Air_direction_photo.setText("Parallel Air Flow Direction Demonistration photo")
        
        elif self.FinTube_air_direction.currentText() == "Series-Parallel":
            self.FinTube_air_parallel_distribution_button.setEnabled(False)
            self.Automatic_Distribution_button.setEnabled(False)
            if hasattr(self,"Series_Parallel_photo"):
                self.FinTube_Air_direction_photo.setPixmap(self.Series_Parallel_photo)
            else:
                self.FinTube_Air_direction_photo.clear()
                self.FinTube_Air_direction_photo.setText("Series-Parallel Air Flow Direction Demonistration photo")

        elif self.FinTube_air_direction.currentText() == "Series-Counter":
            self.FinTube_air_parallel_distribution_button.setEnabled(False)
            self.Automatic_Distribution_button.setEnabled(False)
            if hasattr(self,"Series_Counter_photo"):
                self.FinTube_Air_direction_photo.setPixmap(self.Series_Counter_photo)
            else:
                self.FinTube_Air_direction_photo.clear()
                self.FinTube_Air_direction_photo.setText("Series-Series Air Flow Direction Demonistration photo")

        elif self.FinTube_air_direction.currentText() == "Sub Heat Exchanger First":
            self.FinTube_air_parallel_distribution_button.setEnabled(True)
            self.Automatic_Distribution_button.setEnabled(True)
            if hasattr(self,"Sub_HX_first_photo"):
                self.FinTube_Air_direction_photo.setPixmap(self.Sub_HX_first_photo)
            else:
                self.FinTube_Air_direction_photo.clear()
                self.FinTube_Air_direction_photo.setText("Sub Heat Exchanger First Flow Direction Demonistration photo")

        elif self.FinTube_air_direction.currentText() == "Sub Heat Exchanger Last":
            self.FinTube_air_parallel_distribution_button.setEnabled(True)
            self.Automatic_Distribution_button.setEnabled(True)
            if hasattr(self,"Sub_HX_last_photo"):
                self.FinTube_Air_direction_photo.setPixmap(self.Sub_HX_last_photo)
            else:
                self.FinTube_Air_direction_photo.clear()
                self.FinTube_Air_direction_photo.setText("Sub Heat Exchanger Last Air Flow Direction Demonistration photo")

    def FinTube_mode_changed(self):
        if self.FinTube_mode.currentIndex() == 1:
            self.FinTube_N_segments.setVisible(False)
            self.FinTube_N_segments_label.setVisible(False)
        else:
            self.FinTube_N_segments.setVisible(True)
            self.FinTube_N_segments_label.setVisible(True)
    
    def N_series_circuits_changed(self):
        if hasattr(self,"Parallel_Air_Distribution"):
            N = int(self.FinTube_N_series_circuits.value())
            self.Parallel_Air_Distribution = [1/N for _ in range(N)]

        if self.FinTube_N_series_circuits.value() > self.FinTube_series_circuit_define.count():
            while(self.FinTube_series_circuit_define.count() != self.FinTube_N_series_circuits.value()):
                self.FinTube_series_circuit_define.addItem(str(self.FinTube_series_circuit_define.count()+1))
                self.FinTube_series_circuit_copy_to.addItem(str(self.FinTube_series_circuit_copy_to.count()+1))
                self.FinTube_circuits.append(values())
            self.update_circuits_definition()
        elif self.FinTube_N_series_circuits.value() < self.FinTube_series_circuit_define.count():
            while(self.FinTube_series_circuit_define.count() != self.FinTube_N_series_circuits.value()):
                self.FinTube_series_circuit_define.removeItem(self.FinTube_series_circuit_define.count()-1)
                self.FinTube_series_circuit_copy_to.removeItem(self.FinTube_series_circuit_copy_to.count()-1)
                self.FinTube_circuits = self.FinTube_circuits[:-1]
            self.update_circuits_definition()
        else:
            self.update_circuits_definition()
            
    def update_circuits_definition(self):
        self.FinTube_series_circuit_copy_from.clear()
        self.FinTube_series_circuit_copy_to.clear()
        not_defined_list = list(str(i) for i in range(1,len(self.FinTube_circuits) + 1))
        if self.FinTube_Sub_HX_check.isChecked():
            not_defined_list.append("Sub Heat Exchanger")
        self.FinTube_series_circuit_copy_to.addItems(not_defined_list)
        defined_list = []
        for i,circuit in enumerate(self.FinTube_circuits):
            if hasattr(circuit,"defined"):
                not_defined_list.remove(str(i+1))
                defined_list.append(str(i+1))
        if self.FinTube_Sub_HX_check.isChecked():
            if hasattr(self.FinTube_Sub_Circuit,"defined"):
                defined_list.append("Sub Heat Exchanger")
                not_defined_list.remove("Sub Heat Exchanger")
        not_defined_string = ", ".join(not_defined_list)
        self.FinTube_series_circuits_not_defined.setText(not_defined_string)
        self.FinTube_series_circuit_copy_from.addItems(defined_list)
        
    def cancel_button(self):
        self.close()

class FinTube_Air_Distribution(QDialog, FROM_FinTube_Air_Distribution):

    def __init__(self, parent=None,Number_of_Circuits=1):
        class MyDelegate(QItemDelegate):
    
            def createEditor(self, parent, option, index):
                return_object = QLineEdit(parent)
                only_number = QRegExpValidator(QRegExp("[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)"))
                return_object.setValidator(only_number)
                return return_object
        # first UI
        self.Number_of_Circuits = Number_of_Circuits
        super(FinTube_Air_Distribution, self).__init__(parent)
        self.setupUi(self)
        self.FinTube_Distrubution.setColumnCount(Number_of_Circuits)
        self.FinTube_Distrubution.setHorizontalHeaderLabels(["Circuit "+str(i+1) for i in range(Number_of_Circuits)])
        delegate = MyDelegate()
        self.FinTube_Distrubution.setItemDelegate(delegate)
        for col in range(Number_of_Circuits):
            self.FinTube_Distrubution.setItem(0, col, QTableWidgetItem(str(1/Number_of_Circuits)))
        self.FinTube_Distrubution_cancel_button.clicked.connect(self.cancel_button)
        self.FinTube_Distrubution_ok_button.clicked.connect(self.ok_button)
        self.FinTube_Distrubution.installEventFilter(self)

    def validate(self):
        Total = 0
        for col in range(self.Number_of_Circuits):
            Total += float(self.FinTube_Distrubution.item(0,col).text())
        Total = round(Total,7);
        if Total != 1.0:
            return 0
        else:
            return 1

    def ok_button(self):
        if self.validate():
            Total = []
            for col in range(self.Number_of_Circuits):
                Total.append(float(self.FinTube_Distrubution.item(0,col).text()))
            self.Distribution_Result = Total
            self.close()
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Total Sum of Fractions should equal to 1.0")
            msg.setWindowTitle("Error!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()            
    
    def cancel_button(self):
        self.close()

    def eventFilter(self, source, event):
        if (event.type() == QEvent.KeyPress and
            event.matches(QKeySequence.Copy)):
            self.copySelection()
            return True
        if (event.type() == QEvent.KeyPress and
            event.matches(QKeySequence.Paste)):
            self.pasteSelection()
            return True
        return super(FinTube_Air_Distribution, self).eventFilter(source, event)

    def copySelection(self):
        selection = self.FinTube_Distrubution.selectedIndexes()
        if selection:
            rows = sorted(index.row() for index in selection)
            columns = sorted(index.column() for index in selection)
            rowcount = rows[-1] - rows[0] + 1
            colcount = columns[-1] - columns[0] + 1
            table = [[''] * colcount for _ in range(rowcount)]
            for index in selection:
                row = index.row() - rows[0]
                column = index.column() - columns[0]
                table[row][column] = index.data()
            stream = io.StringIO()
            csv.writer(stream, delimiter='\t').writerows(table)
            qApp.clipboard().setText(stream.getvalue())
        return

    def pasteSelection(self,table_number):
        selection = self.FinTube_Distrubution.selectedIndexes()
        if selection:
            model = self.FinTube_Distrubution.model()
            buffer = qApp.clipboard().text() 
            rows = sorted(index.row() for index in selection)
            columns = sorted(index.column() for index in selection)
            reader = csv.reader(io.StringIO(buffer), delimiter='\t')
            if len(rows) == 1 and len(columns) == 1:
                for i, line in enumerate(reader):
                    for j, cell in enumerate(line):
                        model.setData(model.index(rows[0]+i,columns[0]+j), cell)
            else:
                arr = [ [ cell for cell in row ] for row in reader]
                for index in selection:
                    row = index.row() - rows[0]
                    column = index.column() - columns[0]
                    model.setData(model.index(index.row(), index.column()), arr[row][column])
        return

class FinTube_Fan_Model_Efficiency(QDialog, FROM_FinTube_Fan_Model_efficiency):
    def __init__(self, parent=None):
        super(FinTube_Fan_Model_Efficiency, self).__init__(parent)
        self.setupUi(self)
        self.FinTube_cancel_button.clicked.connect(self.cancel_button)
        self.FinTube_ok_button.clicked.connect(self.ok_button)
        
    def validate(self):
        efficiency_exp = str(self.FinTube_efficiency_exp.text()).strip().replace("^","**")
        if efficiency_exp in ["","-","."]:
            return 2
        try:
            eff=parse_expr(efficiency_exp)
        except:
            return 10
        
        all_symbols_eff = [str(x) for x in eff.atoms(Symbol)]
        
        # making sure 1 variable (volume flow rate) is present
        if len(all_symbols_eff) != 1:
            if len(all_symbols_eff) == 0: # if no variable is given, then a number is given
                eff_value = eff.evalf()
                if not (0.0 <= eff_value <= 1.0):
                    return 3
                else:
                    return 1
            else:
                return 10
        else:
            return 1
    
    def ok_button(self):
        validate = self.validate()
        if validate == 1:
            self.eff_exp = str(self.FinTube_efficiency_exp.text())
            self.close()
        elif validate == 2:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Efficiency expression is empty")
            msg.setWindowTitle("Error!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        elif validate == 3:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Efficiency should be between 0 and 1")
            msg.setWindowTitle("Error!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Something is wrong with the efficiency expression")
            msg.setWindowTitle("Error!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            
    def cancel_button(self):
        self.close()

class FinTube_Fan_Model_Power(QDialog, FROM_FinTube_Fan_Model_power):
    def __init__(self, parent=None):
        super(FinTube_Fan_Model_Power, self).__init__(parent)
        self.setupUi(self)
        self.FinTube_cancel_button.clicked.connect(self.cancel_button)
        self.FinTube_ok_button.clicked.connect(self.ok_button)
        
    def validate(self):
        power_exp = str(self.FinTube_power_exp.text()).strip().replace("^","**")
        if power_exp in ["","-","."]:
            return 2
        try:
            power=parse_expr(power_exp)
        except:
            return 10
        
        all_symbols_power = [str(x) for x in power.atoms(Symbol)]
        
        # making sure 1 variable (volume flow rate) is present
        if len(all_symbols_power) != 1:
            if len(all_symbols_power) == 0: # if no variable is given, then a number is given
                power_value = power.evalf()
                return 1
            else:
                return 10
        else:
            return 1
    
    def ok_button(self):
        validate = self.validate()
        if validate == 1:
            self.power_exp = str(self.FinTube_power_exp.text())
            self.close()
        elif validate == 2:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Power expression is empty")
            msg.setWindowTitle("Error!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Something is wrong with the power expression")
            msg.setWindowTitle("Error!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            
    def cancel_button(self):
        self.close()

class FinTube_Fan_Model_Curve(QDialog, FROM_FinTube_Fan_Model_curve):
    def __init__(self, parent=None):
        super(FinTube_Fan_Model_Curve, self).__init__(parent)
        self.setupUi(self)
        self.FinTube_cancel_button.clicked.connect(self.cancel_button)
        self.FinTube_ok_button.clicked.connect(self.ok_button)
        
    def validate_P(self):
        P_exp = str(self.FinTube_P_exp.text()).strip().replace("^","**")
        if P_exp in ["","-","."]:
            return 2
        try:
            P=parse_expr(P_exp)
        except:
            return 10
        
        all_symbols_P = [str(x) for x in P.atoms(Symbol)]
        # making sure 1 variable (volume flow rate) is present
        if len(all_symbols_P) != 1:
            if len(all_symbols_P) == 0: # if no variable is given, then a number is given
                P_value = float(P.evalf())
                if P_value <= 0:
                    return 3
                else:
                    return 1
            else:
                return 10
        else:
            return 1

    def validate_DP(self):
        DP_exp = str(self.FinTube_DP_exp.text()).strip().replace("^","**")
        if DP_exp in ["","-","."]:
            return 2
        try:
            DP=parse_expr(DP_exp)
        except:

            return 10
        
        all_symbols_DP = [str(x) for x in DP.atoms(Symbol)]
        
        # making sure 1 variable (volume flow rate) is present
        if len(all_symbols_DP) != 1:
            if len(all_symbols_DP) == 0: # if no variable is given, then a number is given
                DP_value = float(DP.evalf())
                if DP_value <= 0:
                    return 3
                else:
                    return 1
            else:
                return 10
        else:
            return 1
    
    def ok_button(self):
        validate_P = self.validate_P()
        validate_DP = self.validate_DP()
        if validate_P == 2:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Power expression is empty")
            msg.setWindowTitle("Error!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        elif validate_P == 3:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Power must be positive number")
            msg.setWindowTitle("Error!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        elif validate_P != 1:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Something is wrong with the Power expression")
            msg.setWindowTitle("Error!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()

        elif validate_DP == 2:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Pressure Drop expression is empty")
            msg.setWindowTitle("Error!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        elif validate_DP == 3:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Pressure Drop must be positive number")
            msg.setWindowTitle("Error!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        elif validate_DP != 1:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Something is wrong with the Pressure Drop expression")
            msg.setWindowTitle("Error!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        
        if (validate_DP == 1) and (validate_P == 1):
            self.P_exp = str(self.FinTube_P_exp.text())
            self.DP_exp = str(self.FinTube_DP_exp.text())
            self.close()
            
    def cancel_button(self):
        self.close()
        
if __name__ == '__main__':
    def main():
        app=QApplication(sys.argv)
        app.setStyle('Fusion')
        window = FinTubeWindow()
        window.show()
        app.exec_()
    try:
        main()
    except Exception as why:
        print(why)

