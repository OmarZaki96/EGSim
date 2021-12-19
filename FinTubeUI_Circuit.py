from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
import CoolProp as CP
import os, sys
from GUI_functions import *
from CoolProp.CoolProp import HAPropsSI
from sympy.parsing.sympy_parser import parse_expr
from sympy import S, Symbol
from math import pi
from FinTube_Visualize import Visualise_Window
from unit_conversion import *
from Fintube_circuitry import tubes_circuitry_window
from Sub_HX_UI import Sub_HX_UI_Widget
from FinTube_select_fin import FinTube_select_fin_window
from FinTube_select_tube import FinTube_select_tube_window

FROM_FinTube_Circuit_Main,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Fin_tube_circuit_define.ui"))

class values():
    pass

class FinTube_Circuit_Window(QDialog, FROM_FinTube_Circuit_Main):
    def __init__(self, parent=None):
        # first UI
        super(FinTube_Circuit_Window, self).__init__(parent)
        self.setupUi(self)
        self.FinTube_circuit_cancel_button.clicked.connect(self.cancel_button)
        self.Delete_validation_range = False
        self.loaded_sub_HX_values = False
        
        # defining validators
        only_number = QRegExpValidator(QRegExp("(([0-9]+\.[0-9]*[1-9][0-9]*)|([0-9]*[1-9][0-9]*\.[0-9]+)|([0-9]*[1-9][0-9]*))"))
        only_number_integer = QRegExpValidator(QRegExp("[0-9]{8}"))
        self.FinTube_circuit_tube_OD.setValidator(only_number)
        self.FinTube_circuit_tube_length.setValidator(only_number)
        self.FinTube_circuit_tube_ID.setValidator(only_number)
        self.FinTube_circuit_tube_e_D.setValidator(only_number)
        self.FinTube_circuit_tube_t.setValidator(only_number)
        self.FinTube_circuit_tube_e.setValidator(only_number)
        self.FinTube_circuit_tube_d.setValidator(only_number)
        self.FinTube_circuit_tube_n.setValidator(only_number_integer)
        self.FinTube_circuit_tube_gamma.setValidator(only_number)
        self.FinTube_circuit_tube_beta.setValidator(only_number)
        self.FinTube_circuit_tube_Pl.setValidator(only_number)
        self.FinTube_circuit_tube_Pt.setValidator(only_number)
        self.FinTube_circuit_fin_t.setValidator(only_number)
        self.FinTube_circuit_fin_FPI.setValidator(only_number)
        self.FinTube_circuit_fin_dim_1.setValidator(only_number)
        self.FinTube_circuit_fin_dim_2.setValidator(only_number)
        self.FinTube_circuit_fin_dim_3.setValidator(only_number_integer)
        self.FinTube_circuit_tube_k.setValidator(only_number)
        self.FinTube_circuit_fin_k.setValidator(only_number)
        self.FinTube_superheat_HTC_correlation_correction.setValidator(only_number)
        self.FinTube_superheat_DP_correlation_correction.setValidator(only_number)
        self.FinTube_2phase_HTC_correlation_correction.setValidator(only_number)
        self.FinTube_2phase_DP_correlation_correction.setValidator(only_number)
        self.FinTube_subcool_HTC_correlation_correction.setValidator(only_number)
        self.FinTube_subcool_DP_correlation_correction.setValidator(only_number)
        self.FinTube_air_dry_HTC_correlation_correction.setValidator(only_number)
        self.FinTube_air_dry_DP_correlation_correction.setValidator(only_number)
        self.FinTube_air_wet_HTC_correlation_correction.setValidator(only_number)
        self.FinTube_air_wet_DP_correlation_correction.setValidator(only_number)
    
        # intially hide fin dimensions
        self.line_7.hide()
        self.FinTube_circuit_fin_dim_1.hide()
        self.FinTube_circuit_fin_dim_2.hide()
        self.FinTube_circuit_fin_dim_3.hide()
        self.FinTube_circuit_fin_dim_1_label.hide()
        self.FinTube_circuit_fin_dim_2_label.hide()
        self.FinTube_circuit_fin_dim_3_label.hide()
        self.FinTube_circuit_fin_dim_1_unit.hide()
        self.FinTube_circuit_fin_dim_2_unit.hide()
        self.FinTube_circuit_fin_dim_3_unit.hide()
        
        # setting connections
        self.FinTube_circuit_tube_type.currentIndexChanged.connect(self.Tube_type_changed)
        self.FinTube_circuit_circuitry.currentIndexChanged.connect(self.Circuitry_type_changed)
        self.FinTube_circuit_fin_type.currentIndexChanged.connect(self.Fin_type_changed)
        self.FinTube_circuit_ok_button.clicked.connect(self.ok_button)
        self.FinTube_circuit_tube_staggering.currentIndexChanged.connect(self.Staggering_changed)
        self.FinTube_circuit_visualize_button.clicked.connect(self.visualize_button)
        self.FinTube_circuit_circuitry_button.clicked.connect(self.define_circuitry_manual)
        self.FinTube_circuit_tube_N_bank.valueChanged.connect(self.update_sub_HX_ui)
        self.FinTube_circuit_tube_N_per_bank.valueChanged.connect(self.update_sub_HX_ui)
        self.FinTube_circuit_tube_length.editingFinished.connect(self.update_sub_HX_ui)
        self.FinTube_circuit_tube_length_unit.currentIndexChanged.connect(self.update_sub_HX_ui)
        self.Select_fin_button.clicked.connect(self.select_fin)
        self.Select_tube_button.clicked.connect(self.select_tube)
        
        # intially load images
        def images_loader(path,var_name,size):
            try:
                photo = QPixmap(path)
                photo = photo.scaledToWidth(size)
                setattr(self,var_name,photo)
            except:
                pass
        
        images_loader("photos/FinTube_MicrofinsTubes.png",'MicrofinsTubes_photo',250)
        images_loader("photos/FinTube_WavyFins.png",'WavyFins_photo',250)
        images_loader("photos/FinTube_PlaneFins.png",'PlaneFins_photo',250)
        images_loader("photos/FinTube_SlitFins.png",'SlitFins_photo',650)
        images_loader("photos/FinTube_LouveredFins.png",'LouveredFins_photo',250)
        images_loader("photos/FinTube_inline.png",'inline_photo',200)
        images_loader("photos/FinTube_AaA1.png",'AaA_photo',200)
        images_loader("photos/FinTube_aAa2.png",'aAa_photo',200)
        images_loader("photos/FinTube_Counter.png",'Counter_photo',200)
        images_loader("photos/FinTube_Parallel.png",'Parallel_photo',200)
        images_loader("photos/FinTube_Customized.png",'Customized_photo',200)
        
        # intially populate available images
        if hasattr(self,"MicrofinsTubes_photo"):
            self.FinTube_circuit_microfin_image.setPixmap(self.MicrofinsTubes_photo)
        else:
            self.FinTube_circuit_microfin_image.setText("Microfin Tubes Demonistration photo")
        if hasattr(self,"inline_photo"):
            self.FinTube_circuit_staggering_image.setPixmap(self.inline_photo)
        else:
            self.FinTube_circuit_staggering_image.setText("Inline Staggering Demonistration photo")
        if hasattr(self,"Counter_photo"):
            self.FinTube_circuit_circuitry_image.setPixmap(self.Counter_photo)
        else:
            self.FinTube_circuit_circuitry_image.setText("Counter Circuitry Demonistration photo")
        if hasattr(self,"PlaneFins_photo"):
            self.FinTube_circuit_fin_type_image.setPixmap(self.PlaneFins_photo)
        else:
            self.FinTube_circuit_fin_type_image.setText("Plain Fins Demonistration photo")
        
        self.Sub_HX_UI = Sub_HX_UI_Widget()

    def select_fin(self):
        select_fin_window = FinTube_select_fin_window()
        if not select_fin_window.load_fins():
            self.raise_error_message("Could not load fins database.\nPlease fix database csv file.")
        else:
            select_fin_window.exec_()
            if hasattr(select_fin_window,"fin_selected"):
                self.load_fin(select_fin_window.fin_selected)

    def select_tube(self):
        select_tube_window = FinTube_select_tube_window()
        if not select_tube_window.load_tubes():
            self.raise_error_message("Could not load tubes database.\nPlease fix database csv file.")
        else:
            select_tube_window.exec_()
            if hasattr(select_tube_window,"tube_selected"):
                self.load_tube(select_tube_window.tube_selected)
    
    def load_fin(self,fin_data):
        self.FinTube_circuit_fin_t.setText('%s' % float('%.5g' % (fin_data.fin_t*1000)))
        self.FinTube_circuit_fin_FPI.setText('%s' % float('%.5g' % fin_data.fin_FPI))
        self.FinTube_circuit_fin_type.setCurrentIndex(fin_data.fin_type_index)
        for i,parameter in enumerate(fin_data.fin_params):
            if i < 2:
                getattr(self,"FinTube_circuit_fin_dim_"+str(i+1)).setText('%s' % float('%.5g' % (parameter*1000)))
            else:
                getattr(self,"FinTube_circuit_fin_dim_"+str(i+1)).setText('%s' % float('%.5g' % parameter))
                
        if self.FinTube_circuit_tube_staggering.isEnabled():
            self.FinTube_circuit_tube_staggering.setCurrentIndex(fin_data.Stagerring_index)
        self.FinTube_circuit_tube_Pl.setText('%s' % float('%.5g' % (fin_data.tube_Pl*1000)))
        self.FinTube_circuit_tube_Pt.setText('%s' % float('%.5g' % (fin_data.tube_Pt*1000)))
        self.FinTube_circuit_fin_k.setText('%s' % float('%.5g' % fin_data.fin_K))
        self.FinTube_circuit_fin_dim_1_unit.setCurrentIndex(2)
        self.FinTube_circuit_fin_dim_2_unit.setCurrentIndex(2)
        self.FinTube_circuit_fin_t_unit.setCurrentIndex(2)
        self.FinTube_circuit_tube_Pl_unit.setCurrentIndex(2)
        self.FinTube_circuit_tube_Pt_unit.setCurrentIndex(2)
        self.FinTube_circuit_fin_k_unit.setCurrentIndex(0)

    def load_tube(self,tube_data):
        self.FinTube_circuit_tube_OD.setText('%s' % float('%.5g' % (tube_data.tube_OD*1000)))
        self.FinTube_circuit_tube_OD_unit.setCurrentIndex(2)
        self.FinTube_circuit_tube_type.setCurrentIndex(tube_data.tube_type_index)
        if tube_data.tube_type_index == 0:
            self.FinTube_circuit_tube_ID.setText('%s' % float('%.5g' % (tube_data.tube_ID*1000)))
            self.FinTube_circuit_tube_e_D.setText('%s' % float('%.5g' % tube_data.tube_e_D))
            self.FinTube_circuit_tube_ID_unit.setCurrentIndex(2)
        elif tube_data.tube_type_index == 1:
            self.FinTube_circuit_tube_t.setText('%s' % float('%.5g' % (tube_data.tube_t*1000)))
            self.FinTube_circuit_tube_e.setText('%s' % float('%.5g' % (tube_data.tube_e*1000)))
            self.FinTube_circuit_tube_d.setText('%s' % float('%.5g' % (tube_data.tube_d*1000)))
            self.FinTube_circuit_tube_n.setText('%s' % int('%.5g' % tube_data.tube_n))
            self.FinTube_circuit_tube_gamma.setText('%s' % float('%.5g' % tube_data.tube_gamma))
            self.FinTube_circuit_tube_beta.setText('%s' % float('%.5g' % tube_data.tube_beta))
            self.FinTube_circuit_tube_t_unit.setCurrentIndex(2)
            self.FinTube_circuit_tube_e_unit.setCurrentIndex(2)
            self.FinTube_circuit_tube_d_unit.setCurrentIndex(2)
            self.FinTube_circuit_tube_gamma_unit.setCurrentIndex(0)
            self.FinTube_circuit_tube_beta_unit.setCurrentIndex(0)

        self.FinTube_circuit_tube_k.setText('%s' % float('%.5g' % tube_data.tube_K))
        self.FinTube_circuit_tube_k_unit.setCurrentIndex(0)
        
    def load_fields(self,Circuit):
        self.FinTube_circuit_tube_OD.setText('%s' % float('%.5g' % (Circuit.OD*1000)))
        self.FinTube_circuit_tube_OD_unit.setCurrentIndex(2)
        self.FinTube_circuit_tube_length.setText('%s' % float('%.5g' % (Circuit.Ltube*1000)))
        self.FinTube_circuit_tube_length_unit.setCurrentIndex(2)
        self.FinTube_circuit_tube_type.setCurrentIndex(Circuit.Tube_type_index)
        if Circuit.Tube_type_index == 0:
            self.FinTube_circuit_tube_ID.setText('%s' % float('%.5g' % (Circuit.ID*1000)))
            self.FinTube_circuit_tube_ID_unit.setCurrentIndex(2)
            self.FinTube_circuit_tube_e_D.setText('%s' % float('%.5g' % (Circuit.e_D)))
        elif Circuit.Tube_type_index == 1:
            self.FinTube_circuit_tube_t.setText('%s' % float('%.5g' % (Circuit.Tube_t*1000)))
            self.FinTube_circuit_tube_t_unit.setCurrentIndex(2)
            self.FinTube_circuit_tube_d.setText('%s' % float('%.5g' % (Circuit.Tube_d*1000)))
            self.FinTube_circuit_tube_d_unit.setCurrentIndex(2)
            self.FinTube_circuit_tube_e.setText('%s' % float('%.5g' % (Circuit.Tube_e*1000)))
            self.FinTube_circuit_tube_e_unit.setCurrentIndex(2)

            self.FinTube_circuit_tube_n.setText('%s' % int('%.5g' % (Circuit.Tube_n)))
            self.FinTube_circuit_tube_gamma.setText('%s' % float('%.5g' % (Circuit.Tube_gamma)))
            self.FinTube_circuit_tube_beta.setText('%s' % float('%.5g' % (Circuit.Tube_beta)))
        
        self.FinTube_circuit_tube_staggering.setCurrentIndex(Circuit.Staggering_index)

        self.FinTube_circuit_tube_N_per_bank.setValue(int(Circuit.N_tube_per_bank))
        self.FinTube_circuit_tube_N_bank.setValue(int(Circuit.N_bank))
        self.FinTube_circuit_tube_Pl.setText('%s' % float('%.5g' % (Circuit.Pl*1000)))
        self.FinTube_circuit_tube_Pl_unit.setCurrentIndex(2)
        self.FinTube_circuit_tube_Pt.setText('%s' % float('%.5g' % (Circuit.Pt*1000)))
        self.FinTube_circuit_tube_Pt_unit.setCurrentIndex(2)

        self.FinTube_circuit_circuitry.setCurrentIndex(Circuit.circuitry)
        
        if Circuit.circuitry == 2:
            self.manual_circuitry = [Circuit.N_tube_per_bank,Circuit.N_bank,Circuit.Connections]
        
        self.FinTube_circuit_N_circuits.setValue(Circuit.N_Circuits)

        self.FinTube_circuit_fin_t.setText('%s' % float('%.5g' % (Circuit.Fin_t*1000)))
        self.FinTube_circuit_fin_t_unit.setCurrentIndex(2)
        self.FinTube_circuit_fin_FPI.setText('%s' % float('%.5g' % (Circuit.Fin_FPI)))
        
        self.FinTube_circuit_fin_type.setCurrentIndex(Circuit.Fin_type_index)
        self.Fin_type_changed()
        if Circuit.Fin_type_index == 1:
            self.FinTube_circuit_fin_dim_1.setText('%s' % float('%.5g' % (Circuit.Fin_xf*1000)))
            self.FinTube_circuit_fin_dim_1_unit.setCurrentIndex(2)
            self.FinTube_circuit_fin_dim_2.setText('%s' % float('%.5g' % (Circuit.Fin_pd*1000)))
            self.FinTube_circuit_fin_dim_2_unit.setCurrentIndex(2)
        if Circuit.Fin_type_index == 2:
            self.FinTube_circuit_fin_dim_1.setText('%s' % float('%.5g' % (Circuit.Fin_Sh*1000)))
            self.FinTube_circuit_fin_dim_1_unit.setCurrentIndex(2)
            self.FinTube_circuit_fin_dim_2.setText('%s' % float('%.5g' % (Circuit.Fin_Ss*1000)))
            self.FinTube_circuit_fin_dim_2_unit.setCurrentIndex(2)
            self.FinTube_circuit_fin_dim_3.setText('%s' % int('%.5g' % (Circuit.Fin_Sn)))
        if Circuit.Fin_type_index == 3:
            self.FinTube_circuit_fin_dim_1.setText('%s' % float('%.5g' % (Circuit.Fin_Lp*1000)))
            self.FinTube_circuit_fin_dim_1_unit.setCurrentIndex(2)
            self.FinTube_circuit_fin_dim_2.setText('%s' % float('%.5g' % (Circuit.Fin_Lh*1000)))
            self.FinTube_circuit_fin_dim_2_unit.setCurrentIndex(2)
        if Circuit.Fin_type_index == 4:
            self.FinTube_circuit_fin_dim_1.setText('%s' % float('%.5g' % (Circuit.Fin_xf*1000)))
            self.FinTube_circuit_fin_dim_1_unit.setCurrentIndex(2)
            self.FinTube_circuit_fin_dim_2.setText('%s' % float('%.5g' % (Circuit.Fin_pd*1000)))
            self.FinTube_circuit_fin_dim_2_unit.setCurrentIndex(2)
            
        self.FinTube_circuit_tube_k.setText('%s' % float('%.5g' % (Circuit.Tube_k)))
        self.FinTube_circuit_fin_k.setText('%s' % float('%.5g' % (Circuit.Fin_k)))
        
        self.FinTube_superheat_HTC_correlation.setCurrentIndex(Circuit.superheat_HTC_corr)
        self.FinTube_superheat_HTC_correlation_correction.setText(str(Circuit.superheat_HTC_correction))
        
        self.FinTube_superheat_DP_correlation.setCurrentIndex(Circuit.superheat_DP_corr)
        self.FinTube_superheat_DP_correlation_correction.setText(str(Circuit.superheat_DP_correction))
        
        self.FinTube_2phase_HTC_correlation.setCurrentIndex(Circuit._2phase_HTC_corr)
        self.FinTube_2phase_HTC_correlation_correction.setText(str(Circuit._2phase_HTC_correction))
        
        self.FinTube_2phase_DP_correlation.setCurrentIndex(Circuit._2phase_DP_corr)
        self.FinTube_2phase_DP_correlation_correction.setText(str(Circuit._2phase_DP_correction))
        
        self.FinTube_subcool_HTC_correlation.setCurrentIndex(Circuit.subcool_HTC_corr)
        self.FinTube_subcool_HTC_correlation_correction.setText(str(Circuit.subcool_HTC_correction))
        
        self.FinTube_subcool_DP_correlation.setCurrentIndex(Circuit.subcool_DP_corr)
        self.FinTube_subcool_DP_correlation_correction.setText(str(Circuit.subcool_DP_correction))
        
        self.FinTube_superheat_HTC_correlation.setCurrentIndex(Circuit.superheat_HTC_corr)
        self.FinTube_superheat_HTC_correlation_correction.setText(str(Circuit.superheat_HTC_correction))

        self.FinTube_2phase_charge_correlation.setCurrentIndex(Circuit._2phase_charge_corr)

        self.FinTube_air_dry_correlation.setCurrentIndex(Circuit.air_dry_HTC_corr)
        self.FinTube_air_dry_HTC_correlation_correction.setText(str(Circuit.air_dry_HTC_correction))
        self.FinTube_air_dry_DP_correlation_correction.setText(str(Circuit.air_dry_DP_correction))

        self.FinTube_air_wet_correlation.setCurrentIndex(Circuit.air_wet_HTC_corr)
        self.FinTube_air_wet_HTC_correlation_correction.setText(str(Circuit.air_wet_HTC_correction))
        self.FinTube_air_wet_DP_correlation_correction.setText(str(Circuit.air_wet_DP_correction))
        
        if hasattr(Circuit,'h_a_wet_on'):
            self.wet_h_a_check.setChecked(Circuit.h_a_wet_on)
            
        if hasattr(Circuit,'DP_a_wet_on'):
            self.wet_DP_a_check.setChecked(Circuit.DP_a_wet_on)
        
        if hasattr(Circuit,"sub_HX_values"):
            self.loaded_sub_HX_values = True
            self.Sub_HX_UI.Enable.setChecked(True)
            self.Sub_HX_UI.load_values(Circuit.sub_HX_values)

    def enable_sub_HX(self):
        # creating sub_HX tab
        self.Sub_HX_UI.Enable.setChecked(True)
        self.Sub_HX_UI.Enable.hide()
        self.tabWidget.addTab(self.Sub_HX_UI,"Sub Heat Exchanger")
        
        # disabling number of banks field
        self.FinTube_circuit_tube_N_bank.hide()
        self.FinTube_circuit_tube_N_bank_label.hide()
        self.FinTube_circuit_tube_N_bank.setValue(1)
        
        # disable number of duplicate circuits
        self.FinTube_circuit_N_circuits_label.hide()
        self.FinTube_circuit_N_circuits.hide()
        self.line_8.hide()
        self.FinTube_circuit_tube_circuitry_group.hide()
        self.FinTube_circuit_N_circuits.setValue(1)
        
        # edit number of tubes field
        self.FinTube_circuit_tube_N_per_bank_label.setText("Number of tubes per bank for the whole heat exchanger")
        
        # intially update Sub_HX UI
        if not self.loaded_sub_HX_values:
            self.update_sub_HX_ui()
        else:
            self.Sub_HX_UI.update_figure(None,None)

    def update_sub_HX_ui(self):
        try:
            tube_length = float(self.FinTube_circuit_tube_length.text())
        except:
            tube_length = 0.0
        self.Sub_HX_UI.update(self.FinTube_circuit_tube_N_bank.value(),self.FinTube_circuit_tube_N_per_bank.value(),self.FinTube_circuit_tube_staggering.currentIndex(),tube_length,self.FinTube_circuit_tube_length_unit.currentIndex())

    def enable_range_validation(self):
        self.FinTube_circuit_tube_OD.editingFinished.connect(lambda: self.validate_range_item("lineedit",'length'))
        self.FinTube_circuit_tube_length.editingFinished.connect(lambda: self.validate_range_item("lineedit",'length'))
        self.FinTube_circuit_tube_N_per_bank.editingFinished.connect(lambda: self.validate_range_item("spinbox",None))
        self.FinTube_circuit_tube_N_bank.editingFinished.connect(lambda: self.validate_range_item("spinbox",None))
        self.FinTube_circuit_tube_Pl.editingFinished.connect(lambda: self.validate_range_item("lineedit","length"))
        self.FinTube_circuit_tube_Pt.editingFinished.connect(lambda: self.validate_range_item("lineedit","length"))
        self.FinTube_circuit_N_circuits.editingFinished.connect(lambda: self.validate_range_item("spinbox",None))
        self.FinTube_circuit_fin_t.editingFinished.connect(lambda: self.validate_range_item("lineedit","length"))
        self.FinTube_circuit_fin_FPI.editingFinished.connect(lambda: self.validate_range_item("lineedit",None))
        self.validated_fin_type = self.FinTube_circuit_fin_type.currentIndex()

        if self.FinTube_circuit_fin_dim_1.isEnabled():
            self.FinTube_circuit_fin_dim_1.editingFinished.connect(lambda: self.validate_range_item("lineedit","length"))
        if self.FinTube_circuit_fin_dim_2.isEnabled():
            self.FinTube_circuit_fin_dim_2.editingFinished.connect(lambda: self.validate_range_item("lineedit","length"))
        if self.FinTube_circuit_fin_dim_3.isEnabled():
            self.FinTube_circuit_fin_dim_3.editingFinished.connect(lambda: self.validate_range_item("lineedit",None))

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

    def validate_range_item(self,data_type,conversion=None):
        if hasattr(self,"validation_range"):
            sender = self.sender()
            prop_name = sender.objectName()
            validate = True
            if "FinTube_circuit_fin_dim" in prop_name:
                if self.validated_fin_type != self.FinTube_circuit_fin_type.currentIndex():
                    validate = False
            if validate:
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
                    true_value = sender.value()

                if not failed:
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

    def check_manual_circuitry(self):
        if hasattr(self,"manual_circuitry"):
            check = True
            N_tube_per_bank = self.FinTube_circuit_tube_N_per_bank.value()
            N_bank = self.FinTube_circuit_tube_N_bank.value()
            if (N_tube_per_bank == "") or (int(N_tube_per_bank) != self.manual_circuitry[0]) or (N_bank == "") or (int(N_bank) != self.manual_circuitry[1]):
                check = False
                delattr(self,"manual_circuitry")
        else:
            check = False
        return check

    def define_circuitry_manual(self):
        N_tube_per_bank = self.FinTube_circuit_tube_N_per_bank.value()
        N_bank = self.FinTube_circuit_tube_N_bank.value()
        if N_tube_per_bank != "" and N_bank != "":
            circuitry_window = tubes_circuitry_window(int(N_tube_per_bank),int(N_bank))
            if self.check_manual_circuitry():
                circuitry_window.load_circuitry(self.manual_circuitry[2])
            circuitry_window.exec_()
            if hasattr(circuitry_window,"circuitry"):
                self.manual_circuitry = circuitry_window.circuitry
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please choose number of tubes per bank and number of banks first")
            msg.setWindowTitle("Sorry!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            
    def validate_visualize(self):
        if str(self.FinTube_circuit_tube_OD.text()).strip() in ["","-","."]:
            return 0
        elif str(self.FinTube_circuit_tube_Pl.text()).strip() in ["","-","."]:
            return 0
        elif str(self.FinTube_circuit_tube_Pt.text()).strip() in ["","-","."]:
            return 0
        Pl = length_unit_converter(self.FinTube_circuit_tube_Pl.text(),self.FinTube_circuit_tube_Pl_unit.currentIndex())
        Pt = length_unit_converter(self.FinTube_circuit_tube_Pt.text(),self.FinTube_circuit_tube_Pt_unit.currentIndex())
        Do = length_unit_converter(self.FinTube_circuit_tube_OD.text(),self.FinTube_circuit_tube_OD_unit.currentIndex())
        if Pl < Do:
            return 2
        elif Pt < Do:
            return 2
        return 1
        
    def visualize_button(self):
        result = self.validate_visualize()
        if result == 0:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please fill empty fields first.")
            msg.setWindowTitle("Empty Fields!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        elif result == 2:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Longitudinal or Transverse Pitch can't be less than outer diameter")
            msg.setWindowTitle("Wrong Value!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        elif result == 1:
            Pl = length_unit_converter(self.FinTube_circuit_tube_Pl.text(),self.FinTube_circuit_tube_Pl_unit.currentIndex())
            Pt = length_unit_converter(self.FinTube_circuit_tube_Pt.text(),self.FinTube_circuit_tube_Pt_unit.currentIndex())
            Do = length_unit_converter(self.FinTube_circuit_tube_OD.text(),self.FinTube_circuit_tube_OD_unit.currentIndex())
            N_bank = int(self.FinTube_circuit_tube_N_bank.value())
            N_tubes = int(self.FinTube_circuit_tube_N_per_bank.value()) * int(self.FinTube_circuit_N_circuits.value())
            if self.FinTube_circuit_tube_staggering.currentIndex() == 0:
                Staggering = 'inline'
            elif self.FinTube_circuit_tube_staggering.currentIndex() == 1:
                Staggering = 'AaA'
            elif self.FinTube_circuit_tube_staggering.currentIndex() == 2:
                Staggering = 'aAa'
            FinTube_Visualize_Window = Visualise_Window(self)
            FinTube_Visualize_Window.setFocusPolicy(Qt.StrongFocus)
            FinTube_Visualize_Window.Draw_tubes(N_tubes,N_bank,Do,Pl,Pt,Staggering)
            FinTube_Visualize_Window.exec_()
    
    def Staggering_changed(self):
        if self.FinTube_circuit_tube_staggering.currentIndex() == 0:
            if hasattr(self,"inline_photo"):
                self.FinTube_circuit_staggering_image.setPixmap(self.inline_photo)
            else:
                self.FinTube_circuit_staggering_image.clear()
                self.FinTube_circuit_staggering_image.setText("Inline Staggering Demonistration photo")
        elif self.FinTube_circuit_tube_staggering.currentIndex() == 1:
            if hasattr(self,"AaA_photo"):
                self.FinTube_circuit_staggering_image.setPixmap(self.AaA_photo)
            else:
                self.FinTube_circuit_staggering_image.clear()
                self.FinTube_circuit_staggering_image.setText("AaA Staggering Demonistration photo")
        elif self.FinTube_circuit_tube_staggering.currentIndex() == 2:
            if hasattr(self,"aAa_photo"):
                self.FinTube_circuit_staggering_image.setPixmap(self.aAa_photo)
            else:
                self.FinTube_circuit_staggering_image.clear()
                self.FinTube_circuit_staggering_image.setText("aAa Staggering Demonistration photo")        

    def validate(self):
        if str(self.FinTube_circuit_tube_OD.text()).strip() in ["","-","."]:
            return 0
        elif str(self.FinTube_circuit_tube_length.text()).strip() in ["","-","."]:
            return 0
        elif str(self.FinTube_circuit_tube_Pl.text()).strip() in ["","-","."]:
            return 0
        elif str(self.FinTube_circuit_tube_Pt.text()).strip() in ["","-","."]:
            return 0
        elif str(self.FinTube_circuit_fin_t.text()).strip() in ["","-","."]:
            return 0
        elif str(self.FinTube_circuit_fin_FPI.text()).strip() in ["","-","."]:
            return 0
        elif str(self.FinTube_circuit_tube_k.text()).strip() in ["","-","."]:
            return 0
        elif str(self.FinTube_circuit_fin_k.text()).strip() in ["","-","."]:
            return 0

        if self.FinTube_circuit_tube_type.currentIndex() == 0:
            if str(self.FinTube_circuit_tube_ID.text()).strip() in ["","-","."]:
                return 0
            elif str(self.FinTube_circuit_tube_e_D.text()).strip() in ["","-","."]:
                return 0

        elif self.FinTube_circuit_tube_type.currentIndex() == 1:
            if str(self.FinTube_circuit_tube_t.text()).strip() in ["","-","."]:
                return 0
            elif str(self.FinTube_circuit_tube_d.text()).strip() in ["","-","."]:
                return 0
            elif str(self.FinTube_circuit_tube_e.text()).strip() in ["","-","."]:
                return 0
            elif str(self.FinTube_circuit_tube_n.text()).strip() in ["","-","."]:
                return 0
            elif str(self.FinTube_circuit_tube_gamma.text()).strip() in ["","-","."]:
                return 0
            elif str(self.FinTube_circuit_tube_beta.text()).strip() in ["","-","."]:
                return 0
        
        if self.FinTube_circuit_fin_type.currentIndex() == 0:
            pass
        
        elif self.FinTube_circuit_fin_type.currentIndex() == 1:
            if str(self.FinTube_circuit_fin_dim_1.text()).strip() in ["","-","."]:
                return 0
            elif str(self.FinTube_circuit_fin_dim_2.text()).strip() in ["","-","."]:
                return 0
        elif self.FinTube_circuit_fin_type.currentIndex() == 2:
            if str(self.FinTube_circuit_fin_dim_1.text()).strip() in ["","-","."]:
                return 0
            elif str(self.FinTube_circuit_fin_dim_2.text()).strip() in ["","-","."]:
                return 0
            elif str(self.FinTube_circuit_fin_dim_3.text()).strip() in ["","-","."]:
                return 0
        elif self.FinTube_circuit_fin_type.currentIndex() == 3:
            if str(self.FinTube_circuit_fin_dim_1.text()).strip() in ["","-","."]:
                return 0
            elif str(self.FinTube_circuit_fin_dim_2.text()).strip() in ["","-","."]:
                return 0
        elif self.FinTube_circuit_fin_type.currentIndex() == 4:
            if str(self.FinTube_circuit_fin_dim_1.text()).strip() in ["","-","."]:
                return 0
            elif str(self.FinTube_circuit_fin_dim_2.text()).strip() in ["","-","."]:
                return 0

        if self.FinTube_circuit_circuitry.currentIndex() == 2:
            if not self.check_manual_circuitry():
                return 2

        if str(self.FinTube_subcool_HTC_correlation_correction.text()).strip() in ["","-","."]:
            return 0
        if str(self.FinTube_subcool_DP_correlation_correction.text()).strip() in ["","-","."]:
            return 0
        if str(self.FinTube_2phase_HTC_correlation_correction.text()).strip() in ["","-","."]:
            return 0
        if str(self.FinTube_2phase_DP_correlation_correction.text()).strip() in ["","-","."]:
            return 0
        if str(self.FinTube_superheat_HTC_correlation_correction.text()).strip() in ["","-","."]:
            return 0
        if str(self.FinTube_superheat_DP_correlation_correction.text()).strip() in ["","-","."]:
            return 0
        if str(self.FinTube_air_dry_HTC_correlation_correction.text()).strip() in ["","-","."]:
            return 0
        if str(self.FinTube_air_dry_DP_correlation_correction.text()).strip() in ["","-","."]:
            return 0
        if str(self.FinTube_air_wet_HTC_correlation_correction.text()).strip() in ["","-","."]:
            return 0
        if str(self.FinTube_air_wet_DP_correlation_correction.text()).strip() in ["","-","."]:
            return 0
        
        if self.Sub_HX_UI.Enable.checkState():
            sub_HX_values = self.Sub_HX_UI.get_values()
            if not sub_HX_values[0]:
                return 3
            
        return 1
                    
    def Connection_creator(self,N_tube_per_bank,N_bank,Style):
        Ntubes = N_tube_per_bank * N_bank
        if Style == 0: #counter flow
            connections = []
            for k in reversed(range(int(N_bank))):
                start = k * N_tube_per_bank + 1
                end = (k + 1) * N_tube_per_bank + 1
                if (N_bank - k)%2==1:
                    connections += range(start,end)
                else:
                    connections += reversed(range(start,end))
        
        elif Style == 1: #parallel flow
            connections = []
            for k in range(int(N_bank)):
                start = k * N_tube_per_bank + 1
                end = (k + 1) * N_tube_per_bank + 1
                if k%2==0:
                    connections += range(start,end)
                else:
                    connections += reversed(range(start,end))
        return connections
    
    def ok_button(self):
        validate = self.validate()
        if validate == 1:
            self.Circuit_info = values()
            self.Circuit_info.OD = length_unit_converter(self.FinTube_circuit_tube_OD.text(),self.FinTube_circuit_tube_OD_unit.currentIndex())
            self.Circuit_info.Ltube = length_unit_converter(self.FinTube_circuit_tube_length.text(),self.FinTube_circuit_tube_length_unit.currentIndex())
            if self.FinTube_circuit_tube_type.currentIndex() == 0:
                self.Circuit_info.Tube_type_index = 0
                self.Circuit_info.Tube_type = "Smooth"
                self.Circuit_info.ID = length_unit_converter(self.FinTube_circuit_tube_ID.text(),self.FinTube_circuit_tube_ID_unit.currentIndex())
                self.Circuit_info.e_D = float(self.FinTube_circuit_tube_e_D.text())
            elif self.FinTube_circuit_tube_type.currentIndex() == 1:
                self.Circuit_info.Tube_type_index = 1
                self.Circuit_info.Tube_type = "Microfin"
                self.Circuit_info.Tube_t = length_unit_converter(self.FinTube_circuit_tube_t.text(),self.FinTube_circuit_tube_t_unit.currentIndex())
                self.Circuit_info.Tube_d = length_unit_converter(self.FinTube_circuit_tube_d.text(),self.FinTube_circuit_tube_d_unit.currentIndex())
                self.Circuit_info.Tube_e = length_unit_converter(self.FinTube_circuit_tube_e.text(),self.FinTube_circuit_tube_e_unit.currentIndex())
                self.Circuit_info.Tube_n = int(self.FinTube_circuit_tube_n.text())
                self.Circuit_info.Tube_gamma = angle_unit_converter(self.FinTube_circuit_tube_gamma.text(),self.FinTube_circuit_tube_gamma_unit.currentIndex())
                self.Circuit_info.Tube_beta = angle_unit_converter(self.FinTube_circuit_tube_beta.text(),self.FinTube_circuit_tube_beta_unit.currentIndex())
            if self.FinTube_circuit_tube_staggering.currentIndex() == 0:
                self.Circuit_info.Staggering = "inline"
                self.Circuit_info.Staggering_index = 0
                
            elif self.FinTube_circuit_tube_staggering.currentIndex() == 1:
                self.Circuit_info.Staggering = "AaA"
                self.Circuit_info.Staggering_index = 1

            elif self.FinTube_circuit_tube_staggering.currentIndex() == 2:
                self.Circuit_info.Staggering = "aAa"
                self.Circuit_info.Staggering_index = 2

            self.Circuit_info.N_tube_per_bank = int(self.FinTube_circuit_tube_N_per_bank.value())
            self.Circuit_info.N_bank = int(self.FinTube_circuit_tube_N_bank.value())
            self.Circuit_info.Pl = length_unit_converter(self.FinTube_circuit_tube_Pl.text(),self.FinTube_circuit_tube_Pl_unit.currentIndex())
            self.Circuit_info.Pt = length_unit_converter(self.FinTube_circuit_tube_Pt.text(),self.FinTube_circuit_tube_Pt_unit.currentIndex())
            if self.FinTube_circuit_circuitry.currentIndex() == 0:
                self.Circuit_info.circuitry = 0
                self.Circuit_info.circuitry_name = "Counter"
                self.Circuit_info.Connections = self.Connection_creator(self.Circuit_info.N_tube_per_bank,self.Circuit_info.N_bank,0)
            elif self.FinTube_circuit_circuitry.currentIndex() == 1:
                self.Circuit_info.circuitry = 1
                self.Circuit_info.circuitry_name = "Parallel"
                self.Circuit_info.Connections = self.Connection_creator(self.Circuit_info.N_tube_per_bank,self.Circuit_info.N_bank,1)
            elif self.FinTube_circuit_circuitry.currentIndex() == 2:
                self.Circuit_info.circuitry = 2
                self.Circuit_info.circuitry_name = "Customized"
                self.Circuit_info.Connections = self.manual_circuitry[2]
            
            self.Circuit_info.N_Circuits = int(self.FinTube_circuit_N_circuits.value())
            
            self.Circuit_info.Fin_t = length_unit_converter(self.FinTube_circuit_fin_t.text(),self.FinTube_circuit_fin_t_unit.currentIndex())
            self.Circuit_info.Fin_FPI = float(self.FinTube_circuit_fin_FPI.text())
            
            if self.FinTube_circuit_fin_type.currentIndex() == 0:
                self.Circuit_info.Fin_type = "Plain"
                self.Circuit_info.Fin_type_index = 0
            elif self.FinTube_circuit_fin_type.currentIndex() == 1:
                self.Circuit_info.Fin_type = "Wavy"
                self.Circuit_info.Fin_xf = length_unit_converter(self.FinTube_circuit_fin_dim_1.text(),self.FinTube_circuit_fin_dim_1_unit.currentIndex())
                self.Circuit_info.Fin_pd = length_unit_converter(self.FinTube_circuit_fin_dim_2.text(),self.FinTube_circuit_fin_dim_2_unit.currentIndex())
                self.Circuit_info.Fin_type_index = 1
            elif self.FinTube_circuit_fin_type.currentIndex() == 2:
                self.Circuit_info.Fin_type = "Slit"
                self.Circuit_info.Fin_Sh = length_unit_converter(self.FinTube_circuit_fin_dim_1.text(),self.FinTube_circuit_fin_dim_1_unit.currentIndex())
                self.Circuit_info.Fin_Ss = length_unit_converter(self.FinTube_circuit_fin_dim_2.text(),self.FinTube_circuit_fin_dim_2_unit.currentIndex())
                self.Circuit_info.Fin_Sn = int(float(self.FinTube_circuit_fin_dim_3.text()))
                self.Circuit_info.Fin_type_index = 2
            elif self.FinTube_circuit_fin_type.currentIndex() == 3:
                self.Circuit_info.Fin_type = "Louvered"
                self.Circuit_info.Fin_Lp = length_unit_converter(self.FinTube_circuit_fin_dim_1.text(),self.FinTube_circuit_fin_dim_1_unit.currentIndex())
                self.Circuit_info.Fin_Lh = length_unit_converter(self.FinTube_circuit_fin_dim_2.text(),self.FinTube_circuit_fin_dim_2_unit.currentIndex())
                self.Circuit_info.Fin_type_index = 3
            elif self.FinTube_circuit_fin_type.currentIndex() == 4:
                self.Circuit_info.Fin_type = "WavyLouvered"
                self.Circuit_info.Fin_xf = length_unit_converter(self.FinTube_circuit_fin_dim_1.text(),self.FinTube_circuit_fin_dim_1_unit.currentIndex())
                self.Circuit_info.Fin_pd = length_unit_converter(self.FinTube_circuit_fin_dim_2.text(),self.FinTube_circuit_fin_dim_2_unit.currentIndex())
                self.Circuit_info.Fin_type_index = 4
            
            self.Circuit_info.Tube_k = Thermal_K_unit_converter(self.FinTube_circuit_tube_k.text(),self.FinTube_circuit_tube_k_unit.currentIndex())
            self.Circuit_info.Fin_k = Thermal_K_unit_converter(self.FinTube_circuit_fin_k.text(),self.FinTube_circuit_fin_k_unit.currentIndex())
            
            self.Circuit_info.superheat_HTC_corr = self.FinTube_superheat_HTC_correlation.currentIndex()
            self.Circuit_info.superheat_HTC_correction = float(self.FinTube_superheat_HTC_correlation_correction.text())
            
            self.Circuit_info.superheat_DP_corr = self.FinTube_superheat_DP_correlation.currentIndex()
            self.Circuit_info.superheat_DP_correction = float(self.FinTube_superheat_DP_correlation_correction.text())
            
            self.Circuit_info._2phase_HTC_corr = self.FinTube_2phase_HTC_correlation.currentIndex()
            self.Circuit_info._2phase_HTC_correction = float(self.FinTube_2phase_HTC_correlation_correction.text())
            
            self.Circuit_info._2phase_DP_corr = self.FinTube_2phase_DP_correlation.currentIndex()
            self.Circuit_info._2phase_DP_correction = float(self.FinTube_2phase_DP_correlation_correction.text())
            
            self.Circuit_info.subcool_HTC_corr = self.FinTube_subcool_HTC_correlation.currentIndex()
            self.Circuit_info.subcool_HTC_correction = float(self.FinTube_subcool_HTC_correlation_correction.text())
            
            self.Circuit_info.subcool_DP_corr = self.FinTube_subcool_DP_correlation.currentIndex()
            self.Circuit_info.subcool_DP_correction = float(self.FinTube_subcool_DP_correlation_correction.text())
            
            self.Circuit_info._2phase_charge_corr = float(self.FinTube_2phase_charge_correlation.currentIndex())

            self.Circuit_info.air_dry_HTC_corr = self.FinTube_air_dry_correlation.currentIndex()
            self.Circuit_info.air_dry_HTC_correction = float(self.FinTube_air_dry_HTC_correlation_correction.text())
            self.Circuit_info.air_dry_DP_correction = float(self.FinTube_air_dry_DP_correlation_correction.text())

            self.Circuit_info.air_wet_HTC_corr = self.FinTube_air_wet_correlation.currentIndex()
            self.Circuit_info.air_wet_HTC_correction = float(self.FinTube_air_wet_HTC_correlation_correction.text())
            self.Circuit_info.air_wet_DP_correction = float(self.FinTube_air_wet_DP_correlation_correction.text())

            self.Circuit_info.h_a_wet_on = self.wet_h_a_check.isChecked()
            self.Circuit_info.DP_a_wet_on = self.wet_DP_a_check.isChecked()

            if self.Sub_HX_UI.Enable.isChecked():
                self.Circuit_info.sub_HX_values = self.Sub_HX_UI.get_values()[1]

            self.Circuit_info.defined = True
            self.close()
            
        elif validate == 0:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please fill all empty fields")
            msg.setWindowTitle("Empty Fields!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        elif validate == 2:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please Define Ciruitry as you chose customized option in Circuitry Style")
            msg.setWindowTitle("Empty Fields!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        
        elif validate == 3:
            sub_HX_values = self.Sub_HX_UI.get_values()
            if not sub_HX_values[0]:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText(sub_HX_values[1])
                msg.setWindowTitle("Error!")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()


    def Fin_type_changed(self):
        if self.FinTube_circuit_fin_type.currentIndex() == 0:
            self.line_7.hide()
            self.FinTube_circuit_fin_dim_1.hide()
            self.FinTube_circuit_fin_dim_2.hide()
            self.FinTube_circuit_fin_dim_3.hide()
            self.FinTube_circuit_fin_dim_1.setEnabled(False)
            self.FinTube_circuit_fin_dim_2.setEnabled(False)
            self.FinTube_circuit_fin_dim_3.setEnabled(False)
            self.FinTube_circuit_fin_dim_1_label.hide()
            self.FinTube_circuit_fin_dim_2_label.hide()
            self.FinTube_circuit_fin_dim_3_label.hide()
            self.FinTube_circuit_fin_dim_1_unit.hide()
            self.FinTube_circuit_fin_dim_2_unit.hide()
            self.FinTube_circuit_fin_dim_3_unit.hide()
            if hasattr(self,"PlaneFins_photo"):
                self.FinTube_circuit_fin_type_image.setPixmap(self.PlaneFins_photo)
            else:
                self.FinTube_circuit_fin_type_image.clear()
                self.FinTube_circuit_fin_type_image.setText("Plain Fins Demonistration photo")

        elif self.FinTube_circuit_fin_type.currentIndex() == 1:
            self.FinTube_circuit_fin_dim_1_label.setText("Fin projected length (xf)*")
            self.FinTube_circuit_fin_dim_2_label.setText("Fin pattern depth (Pd)*")
            self.line_7.show()
            self.FinTube_circuit_fin_dim_1.show()
            self.FinTube_circuit_fin_dim_2.show()
            self.FinTube_circuit_fin_dim_3.hide()
            self.FinTube_circuit_fin_dim_1.setEnabled(True)
            self.FinTube_circuit_fin_dim_2.setEnabled(True)
            self.FinTube_circuit_fin_dim_3.setEnabled(False)
            self.FinTube_circuit_fin_dim_1_label.show()
            self.FinTube_circuit_fin_dim_2_label.show()
            self.FinTube_circuit_fin_dim_3_label.hide()
            self.FinTube_circuit_fin_dim_1_unit.show()
            self.FinTube_circuit_fin_dim_2_unit.show()
            self.FinTube_circuit_fin_dim_3_unit.hide()
            if hasattr(self,"WavyFins_photo"):
                self.FinTube_circuit_fin_type_image.setPixmap(self.WavyFins_photo)
            else:
                self.FinTube_circuit_fin_type_image.clear()
                self.FinTube_circuit_fin_type_image.setText("Wavy Fins Demonistration photo")

        elif self.FinTube_circuit_fin_type.currentIndex() == 2:
            self.FinTube_circuit_fin_dim_1_label.setText("Slit Height (Sh)*")
            self.FinTube_circuit_fin_dim_2_label.setText("Slit Width (Ss)*")
            self.FinTube_circuit_fin_dim_3_label.setText("Number of Slits (Sn)*")
            self.line_7.show()
            self.FinTube_circuit_fin_dim_1.show()
            self.FinTube_circuit_fin_dim_2.show()
            self.FinTube_circuit_fin_dim_3.show()
            self.FinTube_circuit_fin_dim_1.setEnabled(True)
            self.FinTube_circuit_fin_dim_2.setEnabled(True)
            self.FinTube_circuit_fin_dim_3.setEnabled(True)
            self.FinTube_circuit_fin_dim_1_label.show()
            self.FinTube_circuit_fin_dim_2_label.show()
            self.FinTube_circuit_fin_dim_3_label.show()
            self.FinTube_circuit_fin_dim_1_unit.show()
            self.FinTube_circuit_fin_dim_2_unit.show()
            self.FinTube_circuit_fin_dim_3_unit.show()
            if hasattr(self,"SlitFins_photo"):
                self.FinTube_circuit_fin_type_image.setPixmap(self.SlitFins_photo)
            else:
                self.FinTube_circuit_fin_type_image.clear()
                self.FinTube_circuit_fin_type_image.setText("Slit Fins Demonistration photo")

        elif self.FinTube_circuit_fin_type.currentIndex() == 3:
            self.FinTube_circuit_fin_dim_1_label.setText("Louver Pitch (Lp)*")
            self.FinTube_circuit_fin_dim_2_label.setText("Louver Height (Lh)*")
            self.line_7.show()
            self.FinTube_circuit_fin_dim_1.show()
            self.FinTube_circuit_fin_dim_2.show()
            self.FinTube_circuit_fin_dim_3.hide()
            self.FinTube_circuit_fin_dim_1.setEnabled(True)
            self.FinTube_circuit_fin_dim_2.setEnabled(True)
            self.FinTube_circuit_fin_dim_3.setEnabled(False)
            self.FinTube_circuit_fin_dim_1_label.show()
            self.FinTube_circuit_fin_dim_2_label.show()
            self.FinTube_circuit_fin_dim_3_label.hide()
            self.FinTube_circuit_fin_dim_1_unit.show()
            self.FinTube_circuit_fin_dim_2_unit.show()
            self.FinTube_circuit_fin_dim_3_unit.hide()
            if hasattr(self,"LouveredFins_photo"):
                self.FinTube_circuit_fin_type_image.setPixmap(self.LouveredFins_photo)
            else:
                self.FinTube_circuit_fin_type_image.clear()
                self.FinTube_circuit_fin_type_image.setText("Louvered Fins Demonistration photo")

        elif self.FinTube_circuit_fin_type.currentIndex() == 4:
            self.FinTube_circuit_fin_dim_1_label.setText("Fin projected length (xf)*")
            self.FinTube_circuit_fin_dim_2_label.setText("Fin pattern depth (Pd)*")
            self.line_7.show()
            self.FinTube_circuit_fin_dim_1.show()
            self.FinTube_circuit_fin_dim_2.show()
            self.FinTube_circuit_fin_dim_3.hide()
            self.FinTube_circuit_fin_dim_1.setEnabled(True)
            self.FinTube_circuit_fin_dim_2.setEnabled(True)
            self.FinTube_circuit_fin_dim_3.setEnabled(False)
            self.FinTube_circuit_fin_dim_1_label.show()
            self.FinTube_circuit_fin_dim_2_label.show()
            self.FinTube_circuit_fin_dim_3_label.hide()
            self.FinTube_circuit_fin_dim_1_unit.show()
            self.FinTube_circuit_fin_dim_2_unit.show()
            self.FinTube_circuit_fin_dim_3_unit.hide()
            if hasattr(self,"WavyFins_photo"):
                self.FinTube_circuit_fin_type_image.setPixmap(self.WavyFins_photo)
            else:
                self.FinTube_circuit_fin_type_image.clear()
                self.FinTube_circuit_fin_type_image.setText("Wavy-louvered Fins Demonistration photo")

    def Circuitry_type_changed(self):
        if self.FinTube_circuit_circuitry.currentIndex() == 0:
            self.FinTube_circuit_circuitry_button.setEnabled(False)
            if hasattr(self,"Counter_photo"):
                self.FinTube_circuit_circuitry_image.setPixmap(self.Counter_photo)
            else:
                self.FinTube_circuit_circuitry_image.clear()
                self.FinTube_circuit_circuitry_image.setText("Counter Circuitry Demonistration photo")        
        elif self.FinTube_circuit_circuitry.currentIndex() == 1:
            self.FinTube_circuit_circuitry_button.setEnabled(False)
            if hasattr(self,"Parallel_photo"):
                self.FinTube_circuit_circuitry_image.setPixmap(self.Parallel_photo)
            else:
                self.FinTube_circuit_circuitry_image.clear()
                self.FinTube_circuit_circuitry_image.setText("Parallel Circuitry Demonistration photo")        
        elif self.FinTube_circuit_circuitry.currentIndex() == 2:
            self.FinTube_circuit_circuitry_button.setEnabled(True)
            if hasattr(self,"Customized_photo"):
                self.FinTube_circuit_circuitry_image.setPixmap(self.Customized_photo)
            else:
                self.FinTube_circuit_circuitry_image.clear()
                self.FinTube_circuit_circuitry_image.setText("Customized Circuitry Demonistration photo")        

    def Tube_type_changed(self):
        if self.FinTube_circuit_tube_type.currentIndex() == 0:
            self.FinTube_circuit_tube_ID.setEnabled(True)
            self.FinTube_circuit_tube_ID_unit.setEnabled(True)
            self.FinTube_circuit_tube_e_D.setEnabled(True)
            self.FinTube_circuit_tube_e_D_unit.setEnabled(True)
            self.FinTube_circuit_tube_t.setEnabled(False)
            self.FinTube_circuit_tube_t_unit.setEnabled(False)
            self.FinTube_circuit_tube_d.setEnabled(False)
            self.FinTube_circuit_tube_d_unit.setEnabled(False)
            self.FinTube_circuit_tube_e.setEnabled(False)
            self.FinTube_circuit_tube_e_unit.setEnabled(False)
            self.FinTube_circuit_tube_e.setEnabled(False)
            self.FinTube_circuit_tube_e_unit.setEnabled(False)
            self.FinTube_circuit_tube_n.setEnabled(False)
            self.FinTube_circuit_tube_beta.setEnabled(False)
            self.FinTube_circuit_tube_beta_unit.setEnabled(False)
            self.FinTube_circuit_tube_gamma.setEnabled(False)
            self.FinTube_circuit_tube_gamma_unit.setEnabled(False)
            
        elif self.FinTube_circuit_tube_type.currentIndex() == 1:
            self.FinTube_circuit_tube_ID.setEnabled(False)
            self.FinTube_circuit_tube_ID_unit.setEnabled(False)
            self.FinTube_circuit_tube_e_D.setEnabled(False)
            self.FinTube_circuit_tube_e_D_unit.setEnabled(False)
            self.FinTube_circuit_tube_t.setEnabled(True)
            self.FinTube_circuit_tube_t_unit.setEnabled(True)
            self.FinTube_circuit_tube_d.setEnabled(True)
            self.FinTube_circuit_tube_d_unit.setEnabled(True)
            self.FinTube_circuit_tube_e.setEnabled(True)
            self.FinTube_circuit_tube_e_unit.setEnabled(True)
            self.FinTube_circuit_tube_e.setEnabled(True)
            self.FinTube_circuit_tube_e_unit.setEnabled(True)
            self.FinTube_circuit_tube_n.setEnabled(True)
            self.FinTube_circuit_tube_beta.setEnabled(True)
            self.FinTube_circuit_tube_beta_unit.setEnabled(True)
            self.FinTube_circuit_tube_gamma.setEnabled(True)
            self.FinTube_circuit_tube_gamma_unit.setEnabled(True)
        
    def cancel_button(self):
        self.close()
        
if __name__ == '__main__':
    def main():
        app=QApplication(sys.argv)
        app.setStyle('Fusion')
        window = FinTube_Circuit_Window()
        window.show()
        app.exec_()
    main()

