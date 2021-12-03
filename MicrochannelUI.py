from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
import CoolProp as CP
import os, sys
from GUI_functions import write_Microchannel, read_Microchannel, load_last_location, save_last_location
from CoolProp.CoolProp import HAPropsSI
from sympy.parsing.sympy_parser import parse_expr
from sympy import S, Symbol
from MicrochannelUI_Geometry import Microchannel_Geometry_Window
from MicrochannelUI_Circuit import Microchannel_Circuit_Window
from unit_conversion import *
from inputs_validation import check_microchannel

FROM_Microchannel_Main,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Microchannel_define.ui"))
FROM_Microchannel_Fan_Model_efficiency,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Microchannel_Fan_Model_Efficiency.ui"))
FROM_Microchannel_Fan_Model_power,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Microchannel_Fan_Model_Power.ui"))
FROM_Microchannel_Fan_Model_curve,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Microchannel_Fan_Model_Curve.ui"))

class values():
    pass

class MicrochannelWindow(QDialog, FROM_Microchannel_Main):
    def __init__(self, parent=None):
        # first UI
        super(MicrochannelWindow, self).__init__(parent)
        self.setupUi(self)
        self.Delete_validation_range = False

        self.Microchannel_cancel_button.clicked.connect(self.cancel_button)
        self.Microchannel_N_bank.valueChanged.connect(self.N_bank_changed)
        self.Microchannel_mode.currentIndexChanged.connect(self.Microchannel_mode_changed)
        self.Microchannel_bank_circuit_define_button.clicked.connect(self.Microchannel_define_circuiting)
        self.Microchannel_bank_geometry_define_button.clicked.connect(self.Microchannel_define_bank_Geometry)
        
        # intializing value holders
        self.Geometry = values()
        self.Geometry.defined = False
        self.Circuiting = values()
        self.Circuiting.defined = False
        
        # defining validators
        only_number = QRegExpValidator(QRegExp("(([0-9]+\.[0-9]*[1-9][0-9]*)|([0-9]*[1-9][0-9]*\.[0-9]+)|([0-9]*[1-9][0-9]*))"))
        only_number_negative = QRegExpValidator(QRegExp("[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)"))
        self.Microchannel_air_flowrate.setValidator(only_number)
        self.Microchannel_air_mass_flowrate.setValidator(only_number)
        self.Microchannel_air_inlet_P.setValidator(only_number)
        self.Microchannel_air_inlet_T.setValidator(only_number_negative)
        self.Microchannel_air_calculator_P.setValidator(only_number)
        self.Microchannel_air_calculator_T.setValidator(only_number_negative)
        self.Microchannel_air_calculator_2nd.setValidator(only_number_negative)
        self.Microchannel_superheat_HTC_correlation_correction.setValidator(only_number)
        self.Microchannel_superheat_DP_correlation_correction.setValidator(only_number)
        self.Microchannel_2phase_HTC_correlation_correction.setValidator(only_number)
        self.Microchannel_2phase_DP_correlation_correction.setValidator(only_number)
        self.Microchannel_subcool_HTC_correlation_correction.setValidator(only_number)
        self.Microchannel_subcool_DP_correlation_correction.setValidator(only_number)
        self.Microchannel_air_dry_HTC_correlation_correction.setValidator(only_number)
        self.Microchannel_air_dry_DP_correlation_correction.setValidator(only_number)
        self.Microchannel_air_wet_HTC_correlation_correction.setValidator(only_number)
        self.Microchannel_air_wet_DP_correlation_correction.setValidator(only_number)
        
        # Calculator
        self.Microchannel_air_calculator_option.currentIndexChanged.connect(self.Microchannel_calculator_option_changed)
        self.Microchannel_air_calculator_P.textChanged.connect(self.Microchannel_calculator_calculate)
        self.Microchannel_air_calculator_T.textChanged.connect(self.Microchannel_calculator_calculate)
        self.Microchannel_air_calculator_2nd.textChanged.connect(self.Microchannel_calculator_calculate)
        self.Microchannel_air_calculator_P_unit.currentIndexChanged.connect(self.Microchannel_calculator_calculate)
        self.Microchannel_air_calculator_T_unit.currentIndexChanged.connect(self.Microchannel_calculator_calculate)
        self.Microchannel_air_calculator_2nd_unit.currentIndexChanged.connect(self.Microchannel_calculator_calculate)
                
        # definition of fan model
        self.Microchannel_fan_model_button.clicked.connect(self.Microchannel_fan_model_definition)
        self.Microchannel_fan_model.currentIndexChanged.connect(self.Microchannel_fan_model_changed)

        # save button clicked
        self.Microchannel_save_button.clicked.connect(self.save_button)

        # load button clicked
        self.Microchannel_load_button.clicked.connect(self.load_button)

        # Ok button clicked
        self.Microchannel_ok_button.clicked.connect(self.ok_button)

        # flowrate type changed
        self.Microchannel_air_flowrate_label.toggled.connect(self.air_flowrate_changed)
        self.Microchannel_air_mass_flowrate_label.toggled.connect(self.air_flowrate_changed)

    def air_flowrate_changed(self):
        if self.Microchannel_air_flowrate_label.isChecked():
            self.Microchannel_air_flowrate.setEnabled(True)
            self.Microchannel_air_flowrate_unit.setEnabled(True)
            self.Microchannel_air_mass_flowrate.setEnabled(False)
            self.Microchannel_air_mass_flowrate_unit.setEnabled(False)
        elif self.Microchannel_air_mass_flowrate_label.isChecked():
            self.Microchannel_air_mass_flowrate.setEnabled(True)
            self.Microchannel_air_mass_flowrate_unit.setEnabled(True)
            self.Microchannel_air_flowrate.setEnabled(False)
            self.Microchannel_air_flowrate_unit.setEnabled(False)

    def enable_range_validation(self):
        if self.Microchannel_air_flowrate_label.isChecked():
            self.Microchannel_air_flowrate.editingFinished.connect(lambda: self.validate_range_item("lineedit",'volume_flowrate'))
        elif self.Microchannel_air_mass_flowrate_label.isChecked():
            self.Microchannel_air_mass_flowrate.editingFinished.connect(lambda: self.validate_range_item("lineedit",'mass_flowrate'))
        self.Microchannel_N_bank.editingFinished.connect(lambda: self.validate_range_item("spinbox",None))
        self.Microchannel_N_tube_per_bank.editingFinished.connect(lambda: self.validate_range_item("spinbox",None))

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

    def raise_error_message(self,message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(message)
        msg.setWindowTitle("Error!")
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
            msg.setText("Please Complete Geometry data")
            msg.setWindowTitle("Circuit not defined!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        elif validate == 3:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please Bank Circuits Data")
            msg.setWindowTitle("BAnk Circuiting Data not defined!")
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
            HX.Geometry = self.Geometry
            HX.Circuiting = self.Circuiting
            HX.name = str(self.Microchannel_name.text())
            HX.model = str(self.Microchannel_mode.currentText())
            if self.Microchannel_mode.currentIndex() == 0:    
                HX.N_segments = int(self.Microchannel_N_segments.value())
            HX.Accurate = str(self.Microchannel_accurate.currentText())
            HX.N_bank = int(self.Microchannel_N_bank.value())
            HX.N_tube_per_bank = int(self.Microchannel_N_tube_per_bank.value())
            HX.HX_Q_tol = float(self.Microchannel_HX_Q_tolerance.value())
            HX.N_iterations = int(self.Microchannel_max_N_iterations.value())
            HX.Fan_model = self.Microchannel_fan_model.currentText()
            if self.Microchannel_fan_model.currentIndex() == 0:
                HX.Fan_model_efficiency_exp = self.Fan_Model_Efficiency
            elif self.Microchannel_fan_model.currentIndex() == 1:
                HX.Fan_model_P_exp = self.Fan_Model_Curve_P
                HX.Fan_model_DP_exp = self.Fan_Model_Curve_DP
            elif self.Microchannel_fan_model.currentIndex() == 2:
                HX.Fan_model_power_exp = self.Fan_Model_Power

            if self.Microchannel_air_flowrate_label.isChecked():
                HX.Vdot_ha = volume_flowrate_unit_converter(self.Microchannel_air_flowrate.text(),self.Microchannel_air_flowrate_unit.currentIndex())
            elif self.Microchannel_air_mass_flowrate_label.isChecked():
                HX.mdot_da = mass_flowrate_unit_converter(self.Microchannel_air_mass_flowrate.text(),self.Microchannel_air_mass_flowrate_unit.currentIndex())                

            HX.Air_P = pressure_unit_converter(self.Microchannel_air_inlet_P.text(),self.Microchannel_air_inlet_P_unit.currentIndex())
            HX.Air_T = temperature_unit_converter(self.Microchannel_air_inlet_T.text(),self.Microchannel_air_inlet_T_unit.currentIndex())
            HX.Air_RH = float(self.Microchannel_air_inlet_RH.value()) / 100

            HX.superheat_HTC_corr = self.Microchannel_superheat_HTC_correlation.currentIndex()
            HX.superheat_HTC_correction = float(self.Microchannel_superheat_HTC_correlation_correction.text())
            
            HX.superheat_DP_corr = self.Microchannel_superheat_DP_correlation.currentIndex()
            HX.superheat_DP_correction = float(self.Microchannel_superheat_DP_correlation_correction.text())
            
            HX._2phase_HTC_corr = self.Microchannel_2phase_HTC_correlation.currentIndex()
            HX._2phase_HTC_correction = float(self.Microchannel_2phase_HTC_correlation_correction.text())
            
            HX._2phase_DP_corr = self.Microchannel_2phase_DP_correlation.currentIndex()
            HX._2phase_DP_correction = float(self.Microchannel_2phase_DP_correlation_correction.text())
            
            HX.subcool_HTC_corr = self.Microchannel_subcool_HTC_correlation.currentIndex()
            HX.subcool_HTC_correction = float(self.Microchannel_subcool_HTC_correlation_correction.text())
            
            HX.subcool_DP_corr = self.Microchannel_subcool_DP_correlation.currentIndex()
            HX.subcool_DP_correction = float(self.Microchannel_subcool_DP_correlation_correction.text())
            
            HX.superheat_HTC_corr = self.Microchannel_superheat_HTC_correlation.currentIndex()
            HX.superheat_HTC_correction = float(self.Microchannel_superheat_HTC_correlation_correction.text())

            HX._2phase_charge_corr = float(self.Microchannel_2phase_charge_correlation.currentIndex())

            HX.air_dry_HTC_corr = self.Microchannel_air_dry_correlation.currentIndex()
            HX.air_dry_HTC_correction = float(self.Microchannel_air_dry_HTC_correlation_correction.text())
            HX.air_dry_DP_correction = float(self.Microchannel_air_dry_DP_correlation_correction.text())

            HX.air_wet_HTC_corr = self.Microchannel_air_wet_correlation.currentIndex()
            HX.air_wet_HTC_correction = float(self.Microchannel_air_wet_HTC_correlation_correction.text())
            HX.air_wet_DP_correction = float(self.Microchannel_air_wet_DP_correlation_correction.text())
            if hasattr(self,"capacity_validation"):
                if self.capacity_validation:
                    HX.capacity_validation_table = self.capacity_validation_table
            validation = check_microchannel(HX)
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
        index = self.Microchannel_mode.findText(HX.model, Qt.MatchFixedString)
        self.Microchannel_mode.setCurrentIndex(index)
        if hasattr(HX,"N_segments"):
            self.Microchannel_N_segments.setValue(HX.N_segments)
        index = self.Microchannel_accurate.findText(HX.Accurate, Qt.MatchFixedString)
        self.Microchannel_accurate.setCurrentIndex(index)
        self.Microchannel_name.setText(HX.name)
        self.Microchannel_N_bank.setValue(HX.N_bank)
        self.Microchannel_N_tube_per_bank.setValue(HX.N_tube_per_bank)
        self.Geometry = HX.Geometry
        self.Circuiting = HX.Circuiting
        self.Microchannel_HX_Q_tolerance.setValue(HX.HX_Q_tol)
        self.Microchannel_max_N_iterations.setValue(HX.N_iterations)
        index = self.Microchannel_fan_model.findText(HX.Fan_model, Qt.MatchFixedString)
        self.Microchannel_fan_model.setCurrentIndex(index)
        if hasattr(HX,'Fan_model_efficiency_exp'):
            self.Fan_Model_Efficiency = HX.Fan_model_efficiency_exp
        if hasattr(HX,'Fan_model_power_exp'):
            self.Fan_Model_Power = HX.Fan_model_power_exp
        if hasattr(HX,'Fan_model_P_exp'):
            self.Fan_Model_Curve_P = HX.Fan_model_P_exp
        if hasattr(HX,'Fan_model_DP_exp'):
            self.Fan_Model_Curve_DP = HX.Fan_model_DP_exp


        if hasattr(HX,"Vdot_ha"):
            self.Microchannel_air_flowrate.setText('%s' % float('%.5g' % (HX.Vdot_ha)))
            self.Microchannel_air_flowrate_label.setChecked(True)
        elif hasattr(HX,"mdot_da"):
            self.Microchannel_air_mass_flowrate.setText('%s' % float('%.5g' % (HX.mdot_da)))
            self.Microchannel_air_mass_flowrate_label.setChecked(True)

        self.Microchannel_air_inlet_P.setText('%s' % float('%.5g' % (HX.Air_P)))

        self.Microchannel_air_inlet_T.setText('%s' % float('%.5g' % (HX.Air_T-273.15)))
        
        self.Microchannel_air_inlet_RH.setValue(HX.Air_RH*100)

        self.Microchannel_superheat_HTC_correlation.setCurrentIndex(HX.superheat_HTC_corr)
        self.Microchannel_superheat_HTC_correlation_correction.setText(str(HX.superheat_HTC_correction))
        
        self.Microchannel_superheat_DP_correlation.setCurrentIndex(HX.superheat_DP_corr)
        self.Microchannel_superheat_DP_correlation_correction.setText(str(HX.superheat_DP_correction))
        
        self.Microchannel_2phase_HTC_correlation.setCurrentIndex(HX._2phase_HTC_corr)
        self.Microchannel_2phase_HTC_correlation_correction.setText(str(HX._2phase_HTC_correction))
        
        self.Microchannel_2phase_DP_correlation.setCurrentIndex(HX._2phase_DP_corr)
        self.Microchannel_2phase_DP_correlation_correction.setText(str(HX._2phase_DP_correction))
        
        self.Microchannel_subcool_HTC_correlation.setCurrentIndex(HX.subcool_HTC_corr)
        self.Microchannel_subcool_HTC_correlation_correction.setText(str(HX.subcool_HTC_correction))
        
        self.Microchannel_subcool_DP_correlation.setCurrentIndex(HX.subcool_DP_corr)
        self.Microchannel_subcool_DP_correlation_correction.setText(str(HX.subcool_DP_correction))
        
        self.Microchannel_superheat_HTC_correlation.setCurrentIndex(HX.superheat_HTC_corr)
        self.Microchannel_superheat_HTC_correlation_correction.setText(str(HX.superheat_HTC_correction))

        self.Microchannel_2phase_charge_correlation.setCurrentIndex(HX._2phase_charge_corr)

        self.Microchannel_air_dry_correlation.setCurrentIndex(HX.air_dry_HTC_corr)
        self.Microchannel_air_dry_HTC_correlation_correction.setText(str(HX.air_dry_HTC_correction))
        self.Microchannel_air_dry_DP_correlation_correction.setText(str(HX.air_dry_DP_correction))

        self.Microchannel_air_wet_correlation.setCurrentIndex(HX.air_wet_HTC_corr)
        self.Microchannel_air_wet_HTC_correlation_correction.setText(str(HX.air_wet_HTC_correction))
        self.Microchannel_air_wet_DP_correlation_correction.setText(str(HX.air_wet_DP_correction))

        if hasattr(HX,'h_a_wet_on'):
            self.wet_h_a_check.setChecked(HX.h_a_wet_on)
        if hasattr(HX,'DP_a_wet_on'):
            self.wet_DP_a_check.setChecked(HX.DP_a_wet_on)
        
    def load_button(self):
        path = QFileDialog.getOpenFileName(self, 'Open Microchannel HX file',directory=load_last_location(),filter="Heat Exchanger file (*.hx);;All files (*.*)")[0]
        if path != "":
            save_last_location(path)
            result = read_Microchannel(path)
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
            msg.setText("Please Complete Geometry data")
            msg.setWindowTitle("Geometry not defined!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        elif validate == 3:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please Bank Circuits Data")
            msg.setWindowTitle("BAnk Circuiting Data not defined!")
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
            path = QFileDialog.getSaveFileName(self, caption='Save Microchannel HX file',directory=load_last_location(),filter="Heat Exchanger file (*.hx);;All files (*.*)")[0]
            if path != "":
                save_last_location(path)
                if path[-3:].lower() != ".hx":
                    path = path+".hx"
                HX = values()
                HX.Geometry = self.Geometry
                HX.Circuiting = self.Circuiting
                HX.name = str(self.Microchannel_name.text())
                HX.model = str(self.Microchannel_mode.currentText())
                if self.Microchannel_mode.currentIndex() == 0:    
                    HX.N_segments = int(self.Microchannel_N_segments.value())
                HX.Accurate = str(self.Microchannel_accurate.currentText())
                HX.N_bank = int(self.Microchannel_N_bank.value())
                HX.N_tube_per_bank = int(self.Microchannel_N_tube_per_bank.value())
                HX.HX_Q_tol = float(self.Microchannel_HX_Q_tolerance.value())
                HX.N_iterations = int(self.Microchannel_max_N_iterations.value())
                HX.Fan_model = self.Microchannel_fan_model.currentText()
                if self.Microchannel_fan_model.currentIndex() == 0:
                    HX.Fan_model_efficiency_exp = self.Fan_Model_Efficiency
                elif self.Microchannel_fan_model.currentIndex() == 1:
                    HX.Fan_model_P_exp = self.Fan_Model_Curve_P
                    HX.Fan_model_DP_exp = self.Fan_Model_Curve_DP
                elif self.Microchannel_fan_model.currentIndex() == 2:
                    HX.Fan_model_power_exp = self.Fan_Model_Power

                if self.Microchannel_air_flowrate_label.isChecked():
                    HX.Vdot_ha = volume_flowrate_unit_converter(self.Microchannel_air_flowrate.text(),self.Microchannel_air_flowrate_unit.currentIndex())
                elif self.Microchannel_air_mass_flowrate_label.isChecked():
                    HX.mdot_da = mass_flowrate_unit_converter(self.Microchannel_air_mass_flowrate.text(),self.Microchannel_air_mass_flowrate_unit.currentIndex())                

                HX.Air_P = pressure_unit_converter(self.Microchannel_air_inlet_P.text(),self.Microchannel_air_inlet_P_unit.currentIndex())
                HX.Air_T = temperature_unit_converter(self.Microchannel_air_inlet_T.text(),self.Microchannel_air_inlet_T_unit.currentIndex())
                HX.Air_RH = float(self.Microchannel_air_inlet_RH.value()) / 100

                HX.superheat_HTC_corr = self.Microchannel_superheat_HTC_correlation.currentIndex()
                HX.superheat_HTC_correction = float(self.Microchannel_superheat_HTC_correlation_correction.text())
                
                HX.superheat_DP_corr = self.Microchannel_superheat_DP_correlation.currentIndex()
                HX.superheat_DP_correction = float(self.Microchannel_superheat_DP_correlation_correction.text())
                
                HX._2phase_HTC_corr = self.Microchannel_2phase_HTC_correlation.currentIndex()
                HX._2phase_HTC_correction = float(self.Microchannel_2phase_HTC_correlation_correction.text())
                
                HX._2phase_DP_corr = self.Microchannel_2phase_DP_correlation.currentIndex()
                HX._2phase_DP_correction = float(self.Microchannel_2phase_DP_correlation_correction.text())
                
                HX.subcool_HTC_corr = self.Microchannel_subcool_HTC_correlation.currentIndex()
                HX.subcool_HTC_correction = float(self.Microchannel_subcool_HTC_correlation_correction.text())
                
                HX.subcool_DP_corr = self.Microchannel_subcool_DP_correlation.currentIndex()
                HX.subcool_DP_correction = float(self.Microchannel_subcool_DP_correlation_correction.text())
                
                HX.superheat_HTC_corr = self.Microchannel_superheat_HTC_correlation.currentIndex()
                HX.superheat_HTC_correction = float(self.Microchannel_superheat_HTC_correlation_correction.text())
    
                HX._2phase_charge_corr = float(self.Microchannel_2phase_charge_correlation.currentIndex())
    
                HX.air_dry_HTC_corr = self.Microchannel_air_dry_correlation.currentIndex()
                HX.air_dry_HTC_correction = float(self.Microchannel_air_dry_HTC_correlation_correction.text())
                HX.air_dry_DP_correction = float(self.Microchannel_air_dry_DP_correlation_correction.text())
    
                HX.air_wet_HTC_corr = self.Microchannel_air_wet_correlation.currentIndex()
                HX.air_wet_HTC_correction = float(self.Microchannel_air_wet_HTC_correlation_correction.text())
                HX.air_wet_DP_correction = float(self.Microchannel_air_wet_DP_correlation_correction.text())

                HX.h_a_wet_on = self.wet_h_a_check.isChecked()
                HX.DP_a_wet_on = self.wet_DP_a_check.isChecked()
                
                result = write_Microchannel(HX,path)
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
    
    def Microchannel_define_circuiting(self):
        Microchannel_define_Circuiting_Dialog = Microchannel_Circuit_Window()
        Microchannel_define_Circuiting_Dialog.setFocusPolicy(Qt.StrongFocus)
        Microchannel_define_Circuiting_Dialog.N_bank = int(self.Microchannel_N_bank.value())
        Microchannel_define_Circuiting_Dialog.N_tube_per_bank = int(self.Microchannel_N_tube_per_bank.value())
        Microchannel_define_Circuiting_Dialog.update_UI()
        if self.Circuiting.defined:
            Microchannel_define_Circuiting_Dialog.bank_passes = self.Circuiting.bank_passes
        Microchannel_define_Circuiting_Dialog.update_table()
        Microchannel_define_Circuiting_Dialog.exec_()
        if hasattr(Microchannel_define_Circuiting_Dialog,'Circuiting'):
            self.Circuiting = Microchannel_define_Circuiting_Dialog.Circuiting
        
    def Microchannel_define_bank_Geometry(self):
        Microchannel_define_bank_Geometry_Dialog = Microchannel_Geometry_Window()
        Microchannel_define_bank_Geometry_Dialog.setFocusPolicy(Qt.StrongFocus)
        if self.Geometry.defined:
            Geometry = self.Geometry
            Microchannel_define_bank_Geometry_Dialog.Microchannel_tube_width.setText('%s' % float('%.5g' % (Geometry.T_w*1000)))            
            Microchannel_define_bank_Geometry_Dialog.Microchannel_tube_height.setText('%s' % float('%.5g' % (Geometry.T_h*1000)))
            Microchannel_define_bank_Geometry_Dialog.Microchannel_tube_length.setText('%s' % float('%.5g' % (Geometry.T_l*1000)))
            Microchannel_define_bank_Geometry_Dialog.Microchannel_tube_spacing.setText('%s' % float('%.5g' % (Geometry.T_s*1000)))
            Microchannel_define_bank_Geometry_Dialog.Microchannel_tube_e_D.setText('%s' % float('%.5g' % (Geometry.e_D)))
            Microchannel_define_bank_Geometry_Dialog.Microchannel_port_number.setText(str(Geometry.N_ports))
            Microchannel_define_bank_Geometry_Dialog.Microchannel_port_shape.setCurrentIndex(Geometry.port_shape_index)
            Microchannel_define_bank_Geometry_Dialog.Microchannel_port_end.setCurrentIndex(Geometry.T_end_index)
            if Geometry.port_shape_index == 0:
                Microchannel_define_bank_Geometry_Dialog.Microchannel_port_dimension_a.setText('%s' % float('%.5g' % (Geometry.port_a_dim*1000)))
                Microchannel_define_bank_Geometry_Dialog.Microchannel_port_dimension_b.setText('%s' % float('%.5g' % (Geometry.port_b_dim*1000)))

            elif Geometry.port_shape_index == 1:
                Microchannel_define_bank_Geometry_Dialog.Microchannel_port_dimension_a.setText('%s' % float('%.5g' % (Geometry.port_a_dim*1000)))
                
            elif Geometry.port_shape_index == 2:
                Microchannel_define_bank_Geometry_Dialog.Microchannel_port_dimension_a.setText('%s' % float('%.5g' % (Geometry.port_a_dim*1000)))
                Microchannel_define_bank_Geometry_Dialog.Microchannel_port_dimension_b.setText('%s' % float('%.5g' % (Geometry.port_b_dim*1000)))
                
            Microchannel_define_bank_Geometry_Dialog.Microchannel_header_CS_shape.setCurrentIndex(Geometry.header_shape_index)
            if Geometry.header_shape_index == 0:
                Microchannel_define_bank_Geometry_Dialog.Microchannel_header_CS_dimension_a.setText('%s' % float('%.5g' % (Geometry.header_a_dim*1000)))
                Microchannel_define_bank_Geometry_Dialog.Microchannel_header_CS_dimension_b.setText('%s' % float('%.5g' % (Geometry.header_b_dim*1000)))

            elif Geometry.header_shape_index == 1:
                Microchannel_define_bank_Geometry_Dialog.Microchannel_header_CS_dimension_a.setText('%s' % float('%.5g' % (Geometry.header_a_dim*1000)))

            Microchannel_define_bank_Geometry_Dialog.Microchannel_header_height.setText('%s' % float('%.5g' % (Geometry.header_height*1000)))
            Microchannel_define_bank_Geometry_Dialog.Microchannel_fin_t.setText('%s' % float('%.5g' % (Geometry.Fin_t*1000)))
            Microchannel_define_bank_Geometry_Dialog.Microchannel_fin_FPI.setText(str(Geometry.Fin_FPI))
            Microchannel_define_bank_Geometry_Dialog.Microchannel_fin_length.setText('%s' % float('%.5g' % (Geometry.Fin_l*1000)))
            Microchannel_define_bank_Geometry_Dialog.Microchannel_fin_number.setCurrentIndex(Geometry.Fin_on_side_index)
            Microchannel_define_bank_Geometry_Dialog.Microchannel_fin_type.setCurrentIndex(Geometry.Fin_type_index)
            if Geometry.Fin_type_index == 0:
                Microchannel_define_bank_Geometry_Dialog.Microchannel_fin_dimension_1.setText('%s' % float('%.5g' % (Geometry.Fin_llouv*1000)))
                Microchannel_define_bank_Geometry_Dialog.Microchannel_fin_dimension_2.setText('%s' % float('%.5g' % (Geometry.Fin_lp*1000)))
                Microchannel_define_bank_Geometry_Dialog.Microchannel_fin_dimension_3.setText('%s' % float('%.5g' % (Geometry.Fin_lalpha)))

            Microchannel_define_bank_Geometry_Dialog.Microchannel_tube_k.setText('%s' % float('%.5g' % (Geometry.Tube_k)))
            Microchannel_define_bank_Geometry_Dialog.Microchannel_fin_k.setText('%s' % float('%.5g' % (Geometry.Fin_k)))

            Microchannel_define_bank_Geometry_Dialog.Microchannel_header_DP.setText('%s' % float('%.5g' % (Geometry.Header_DP/1000)))

        if hasattr(self,"validation_range"):
            Microchannel_define_bank_Geometry_Dialog.validation_range = getattr(self.validation_range,"Geometry")
            Microchannel_define_bank_Geometry_Dialog.enable_range_validation()

        Microchannel_define_bank_Geometry_Dialog.exec_()

        if Microchannel_define_bank_Geometry_Dialog.Delete_validation_range:
            self.delete_validation_range()

        if hasattr(Microchannel_define_bank_Geometry_Dialog,"Geometry"):
            if hasattr(Microchannel_define_bank_Geometry_Dialog.Geometry,"defined"):
                if Microchannel_define_bank_Geometry_Dialog.Geometry.defined:
                    self.Geometry = Microchannel_define_bank_Geometry_Dialog.Geometry
    
    def validate(self):
        if str(self.Microchannel_name.text()).strip() in ["","-","."]:
            return 0

        if self.Microchannel_air_flowrate_label.isChecked():
            if str(self.Microchannel_air_flowrate.text()).strip() in ["","-","."]:
                return 0
        elif self.Microchannel_air_mass_flowrate_label.isChecked():
            if str(self.Microchannel_air_mass_flowrate.text()).strip() in ["","-","."]:
                return 0

        if str(self.Microchannel_air_inlet_P.text()).strip() in ["","-","."]:
            return 0
        if str(self.Microchannel_air_inlet_T.text()).strip() in ["","-","."]:
            return 0
        if not self.Geometry.defined:
            return 2
        if not self.Circuiting.defined:
            return 3

        if str(self.Microchannel_subcool_HTC_correlation_correction.text()).strip() in ["","-","."]:
            return 0
        if str(self.Microchannel_subcool_DP_correlation_correction.text()).strip() in ["","-","."]:
            return 0
        if str(self.Microchannel_2phase_HTC_correlation_correction.text()).strip() in ["","-","."]:
            return 0
        if str(self.Microchannel_2phase_DP_correlation_correction.text()).strip() in ["","-","."]:
            return 0
        if str(self.Microchannel_superheat_HTC_correlation_correction.text()).strip() in ["","-","."]:
            return 0
        if str(self.Microchannel_superheat_DP_correlation_correction.text()).strip() in ["","-","."]:
            return 0
        if str(self.Microchannel_air_dry_HTC_correlation_correction.text()).strip() in ["","-","."]:
            return 0
        if str(self.Microchannel_air_dry_DP_correlation_correction.text()).strip() in ["","-","."]:
            return 0
        if str(self.Microchannel_air_wet_HTC_correlation_correction.text()).strip() in ["","-","."]:
            return 0
        if str(self.Microchannel_air_wet_DP_correlation_correction.text()).strip() in ["","-","."]:
            return 0
            
        if self.Microchannel_fan_model.currentIndex() == 0:
            if not hasattr(self,"Fan_Model_Efficiency"):
                return 4
        elif self.Microchannel_fan_model.currentIndex() == 1:
            if not hasattr(self,"Fan_Model_Curve_P"):
                return 4
            if not hasattr(self,"Fan_Model_Curve_DP"):
                return 4
        elif self.Microchannel_fan_model.currentIndex() == 2:
            if not hasattr(self,"Fan_Model_Power"):
                return 4
        return 1
    
    def Microchannel_fan_model_changed(self):
        if hasattr(self,"Fan_Model_Efficiency"):
            delattr(self,"Fan_Model_Efficiency")
        if hasattr(self,"Fan_Model_Power"):
            delattr(self,"Fan_Model_Power")
        if hasattr(self,"Fan_Model_Curve_P"):
            delattr(self,"Fan_Model_Curve_P")
        if hasattr(self,"Fan_Model_Curve_DP"):
            delattr(self,"Fan_Model_Curve_DP")
        if self.Microchannel_fan_model.currentIndex() == 1:
            self.Microchannel_air_flowrate_label.setText("Initial Guess for Inlet Humid Air Volume Flow Rate")
            self.Microchannel_air_mass_flowrate_label.setText("Initial Guess for Inlet Dry Air Mass Flow Rate")
        else:
            self.Microchannel_air_flowrate_label.setText("Inlet Humid Air Volume Flow Rate")
            self.Microchannel_air_mass_flowrate_label.setText("Inlet Dry Air Mass Flow Rate")            
    
    def Microchannel_fan_model_definition(self):
        if self.Microchannel_fan_model.currentIndex() == 0:            
            Microchannel_Fan_Model_Efficiency_dialog = Microchannel_Fan_Model_Efficiency(self)
            Microchannel_Fan_Model_Efficiency_dialog.setFocusPolicy(Qt.StrongFocus)
            if hasattr(self,"Fan_Model_Efficiency"):
                Microchannel_Fan_Model_Efficiency_dialog.Microchannel_efficiency_exp.setText(self.Fan_Model_Efficiency)
            Microchannel_Fan_Model_Efficiency_dialog.exec_()
            if hasattr(Microchannel_Fan_Model_Efficiency_dialog,"eff_exp"):
                self.Fan_Model_Efficiency = str(Microchannel_Fan_Model_Efficiency_dialog.eff_exp)
        elif self.Microchannel_fan_model.currentIndex() == 1:            
            Microchannel_Fan_Model_Curve_dialog = Microchannel_Fan_Model_Curve(self)
            if hasattr(self,"Fan_Model_Curve_P"):
                Microchannel_Fan_Model_Curve_dialog.Microchannel_P_exp.setText(self.Fan_Model_Curve_P)
            if hasattr(self,"Fan_Model_Curve_DP"):
                Microchannel_Fan_Model_Curve_dialog.Microchannel_DP_exp.setText(self.Fan_Model_Curve_DP)
            Microchannel_Fan_Model_Curve_dialog.exec_()
            if hasattr(Microchannel_Fan_Model_Curve_dialog,"P_exp"):
                self.Fan_Model_Curve_P = str(Microchannel_Fan_Model_Curve_dialog.P_exp)
            if hasattr(Microchannel_Fan_Model_Curve_dialog,"DP_exp"):
                self.Fan_Model_Curve_DP = str(Microchannel_Fan_Model_Curve_dialog.DP_exp)
        elif self.Microchannel_fan_model.currentIndex() == 2: 
            Microchannel_Fan_Model_Power_dialog = Microchannel_Fan_Model_Power(self)
            Microchannel_Fan_Model_Power_dialog.setFocusPolicy(Qt.StrongFocus)
            if hasattr(self,"Fan_Model_Power"):
                Microchannel_Fan_Model_Power_dialog.Microchannel_power_exp.setText(self.Fan_Model_Power)
            Microchannel_Fan_Model_Power_dialog.exec_()
            if hasattr(Microchannel_Fan_Model_Power_dialog,"power_exp"):
                self.Fan_Model_Power = str(Microchannel_Fan_Model_Power_dialog.power_exp)
            
    def Microchannel_calculator_calculate(self):
        try:
            # Air Pressure
            if self.Microchannel_air_calculator_P_unit.currentText() == "Pa":
                Air_Pressure = float(self.Microchannel_air_calculator_P.text())
            elif self.Microchannel_air_calculator_P_unit.currentText() == "kPa":
                Air_Pressure = float(self.Microchannel_air_calculator_P.text()) * 1e3
            elif self.Microchannel_air_calculator_P_unit.currentText() == "MPa":
                Air_Pressure = float(self.Microchannel_air_calculator_P.text()) * 1e6
            elif self.Microchannel_air_calculator_P_unit.currentText() == "bar":
                Air_Pressure = float(self.Microchannel_air_calculator_P.text()) * 1e5
            elif self.Microchannel_air_calculator_P_unit.currentText() == "atm":
                Air_Pressure = float(self.Microchannel_air_calculator_P.text()) * 101325
            elif self.Microchannel_air_calculator_P_unit.currentText() == "psi":
                Air_Pressure = float(self.Microchannel_air_calculator_P.text()) * 6894.76
            
            # Air DBT
            if self.Microchannel_air_calculator_T_unit.currentText() == "C":
                Air_DBT = float(self.Microchannel_air_calculator_T.text()) + 273.15
            elif self.Microchannel_air_calculator_T_unit.currentText() == "K":
                Air_DBT = float(self.Microchannel_air_calculator_T.text())
            elif self.Microchannel_air_calculator_T_unit.currentText() == "F":
                Air_DBT = (float(self.Microchannel_air_calculator_T.text()) - 32) * 5 / 9 + 273.15

            # 2nd variable
            # WBT
            if self.Microchannel_air_calculator_option.currentIndex() == 0:
                if self.Microchannel_air_calculator_2nd_unit.currentText() == "C":
                    Air_WBT = float(self.Microchannel_air_calculator_2nd.text()) + 273.15
                elif self.Microchannel_air_calculator_2nd_unit.currentText() == "K":
                    Air_WBT = float(self.Microchannel_air_calculator_2nd.text())
                elif self.Microchannel_air_calculator_2nd_unit.currentText() == "F":
                    Air_WBT = (float(self.Microchannel_air_calculator_2nd.text()) - 32) * 5 / 9 + 273.15
                
                RH = round(HAPropsSI("R","P",Air_Pressure,"T",Air_DBT,"B",Air_WBT) * 100, 2)
            
            # HR
            elif self.Microchannel_air_calculator_option.currentIndex() == 1:
                HR = float(self.Microchannel_air_calculator_2nd.text())
                RH = round(HAPropsSI("R","P",Air_Pressure,"T",Air_DBT,"W",HR) * 100,2)
            
            self.Microchannel_air_calculator_RH.setText(str(RH))
        
        except:
            self.Microchannel_air_calculator_RH.setText("Not Defined")
    
    def Microchannel_calculator_option_changed(self):
        if self.Microchannel_air_calculator_option.currentIndex() == 0:
            self.Microchannel_air_calculator_2nd_label.setText("Air Wet Bulb Temperature")
            self.Microchannel_air_calculator_2nd.clear()
            self.Microchannel_air_calculator_2nd_unit.clear()
            self.Microchannel_air_calculator_2nd_unit.addItems(["C","K","F"])
            self.Microchannel_air_calculator_2nd_unit.adjustSize() 

        elif self.Microchannel_air_calculator_option.currentIndex() == 1:
            self.Microchannel_air_calculator_2nd_label.setText("Humidity Ratio")
            self.Microchannel_air_calculator_2nd.clear()
            self.Microchannel_air_calculator_2nd_unit.clear()
            self.Microchannel_air_calculator_2nd_unit.addItems(["Kg/Kg","lb/lb"])
            self.Microchannel_air_calculator_2nd_unit.adjustSize() 
            
    def Microchannel_mode_changed(self):
        if self.Microchannel_mode.currentIndex() == 1:
            self.Microchannel_N_segments.setVisible(False)
            self.Microchannel_N_segments_label.setVisible(False)
        else:
            self.Microchannel_N_segments.setVisible(True)
            self.Microchannel_N_segments_label.setVisible(True)
            
    def N_bank_changed(self):
        self.Circuiting.defined = False
        
    def cancel_button(self):
        self.close()

class Microchannel_Fan_Model_Efficiency(QDialog, FROM_Microchannel_Fan_Model_efficiency):
    def __init__(self, parent=None):
        super(Microchannel_Fan_Model_Efficiency, self).__init__(parent)
        self.setupUi(self)
        self.Microchannel_cancel_button.clicked.connect(self.cancel_button)
        self.Microchannel_ok_button.clicked.connect(self.ok_button)
        
    def validate(self):
        efficiency_exp = str(self.Microchannel_efficiency_exp.text()).strip().replace("^","**")
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
            self.eff_exp = str(self.Microchannel_efficiency_exp.text())
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

class Microchannel_Fan_Model_Power(QDialog, FROM_Microchannel_Fan_Model_power):
    def __init__(self, parent=None):
        super(Microchannel_Fan_Model_Power, self).__init__(parent)
        self.setupUi(self)
        self.Microchannel_cancel_button.clicked.connect(self.cancel_button)
        self.Microchannel_ok_button.clicked.connect(self.ok_button)
        
    def validate(self):
        power_exp = str(self.Microchannel_power_exp.text()).strip().replace("^","**")
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
            self.power_exp = str(self.Microchannel_power_exp.text())
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

class Microchannel_Fan_Model_Curve(QDialog, FROM_Microchannel_Fan_Model_curve):
    def __init__(self, parent=None):
        super(Microchannel_Fan_Model_Curve, self).__init__(parent)
        self.setupUi(self)
        self.Microchannel_cancel_button.clicked.connect(self.cancel_button)
        self.Microchannel_ok_button.clicked.connect(self.ok_button)
        
    def validate_P(self):
        P_exp = str(self.Microchannel_P_exp.text()).strip().replace("^","**")
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
        DP_exp = str(self.Microchannel_DP_exp.text()).strip().replace("^","**")
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
            self.P_exp = str(self.Microchannel_P_exp.text())
            self.DP_exp = str(self.Microchannel_DP_exp.text())
            self.close()
            
    def cancel_button(self):
        self.close()
        
if __name__ == '__main__':
    def main():
        app=QApplication(sys.argv)
        app.setStyle('Fusion')
        window = MicrochannelWindow()
        window.show()
        app.exec_()
    try:
        main()
    except Exception as why:
        print(why)

