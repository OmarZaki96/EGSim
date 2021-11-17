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
from unit_conversion import *
from Microchannel_select_fin import Microchannel_select_fin_window
from Microchannel_select_tube import Microchannel_select_tube_window

FROM_Microchannel_Geometry_Main,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Microchannel_bank_geometry_define.ui"))

class values():
    pass

class Microchannel_Geometry_Window(QDialog, FROM_Microchannel_Geometry_Main):
    def __init__(self, parent=None):
        # first UI
        super(Microchannel_Geometry_Window, self).__init__(parent)
        self.setupUi(self)
        self.Delete_validation_range = False
        
        # defining validators
        only_number = QRegExpValidator(QRegExp("(([0-9]+\.[0-9]*[1-9][0-9]*)|([0-9]*[1-9][0-9]*\.[0-9]+)|([0-9]*[1-9][0-9]*))"))
        only_number_integer = QRegExpValidator(QRegExp("[0-9]{8}"))
        self.Microchannel_tube_width.setValidator(only_number)
        self.Microchannel_tube_height.setValidator(only_number)
        self.Microchannel_tube_length.setValidator(only_number)
        self.Microchannel_tube_spacing.setValidator(only_number)
        self.Microchannel_tube_e_D.setValidator(only_number)
        self.Microchannel_port_number.setValidator(only_number_integer)
        self.Microchannel_port_dimension_a.setValidator(only_number)
        self.Microchannel_port_dimension_b.setValidator(only_number)
        self.Microchannel_header_CS_dimension_a.setValidator(only_number)
        self.Microchannel_header_CS_dimension_b.setValidator(only_number)
        self.Microchannel_header_height.setValidator(only_number)
        self.Microchannel_fin_t.setValidator(only_number)
        self.Microchannel_fin_FPI.setValidator(only_number)
        self.Microchannel_fin_length.setValidator(only_number)
        self.Microchannel_fin_dimension_1.setValidator(only_number)
        self.Microchannel_fin_dimension_2.setValidator(only_number)
        self.Microchannel_fin_dimension_3.setValidator(only_number)
        self.Microchannel_tube_k.setValidator(only_number)
        self.Microchannel_fin_k.setValidator(only_number)
            
        # setting connections
        self.Microchannel_header_CS_shape.currentIndexChanged.connect(self.header_shape_changed)
        self.Microchannel_port_shape.currentIndexChanged.connect(self.port_shape_changed)
        self.Microchannel_port_end.currentIndexChanged.connect(self.port_end_changed)
        self.Microchannel_fin_type.currentIndexChanged.connect(self.fin_type_changed)
        self.Microchannel_ok_button.clicked.connect(self.ok_button)
        self.Microchannel_cancel_button.clicked.connect(self.cancel_button)
        self.select_fin_button.clicked.connect(self.select_fin)
        self.select_tube_button.clicked.connect(self.select_tube)
        
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
        images_loader("photos/Microchannel_RectangleHeader.png",'RectangleHeader_photo',250)
        images_loader("photos/Microchannel_CircleHeader.png",'CircleHeader_photo',250)
        images_loader("photos/Microchannel_LouveredFins.png",'LouveredFins_photo',460)

        # intially populate available images
        if hasattr(self,"RectanglePort_photo"):
            self.Microchannel_port_dimension_photo.setPixmap(self.RectanglePort_photo)
        else:
            self.Microchannel_port_dimension_photo.setText("Rectanglular Port Demonistration photo")
        if hasattr(self,"RectangleHeader_photo"):
            self.Microchannel_header_photo.setPixmap(self.RectangleHeader_photo)
        else:
            self.Microchannel_header_photo.setText("Rectanglular Header Demonistration photo")
        if hasattr(self,"LouveredFins_photo"):
            self.Microchannel_fin_type_photo.setPixmap(self.LouveredFins_photo)
        else:
            self.Microchannel_fin_type_photo.setText("Louvered Fin Demonistration photo")
        
        # initially change fin type
        self.fin_type_changed()

    def select_fin(self):
        select_fin_window = Microchannel_select_fin_window()
        if not select_fin_window.load_fins():
            self.raise_error_message("Could not load fins database.\nPlease fix database csv file.")
        else:
            select_fin_window.exec_()
            if hasattr(select_fin_window,"fin_selected"):
                self.load_fin(select_fin_window.fin_selected)

    def select_tube(self):
        select_tube_window = Microchannel_select_tube_window()
        if not select_tube_window.load_tubes():
            self.raise_error_message("Could not load tubes database.\nPlease fix database csv file.")
        else:
            select_tube_window.exec_()
            if hasattr(select_tube_window,"tube_selected"):
                self.load_tube(select_tube_window.tube_selected)
    
    def load_fin(self,fin_data):
        self.Microchannel_fin_t.setText('%s' % float('%.5g' % (fin_data.fin_t*1000)))
        self.Microchannel_fin_FPI.setText('%s' % float('%.5g' % fin_data.fin_FPI))
        self.Microchannel_fin_length.setText('%s' % float('%.5g' % (fin_data.fin_Fd*1000)))
        self.Microchannel_fin_type.setCurrentIndex(fin_data.fin_type_index)
        self.Microchannel_fin_number.setCurrentIndex(fin_data.fin_on_sides)
        for i,parameter in enumerate(fin_data.fin_params):
            if i < 2:
                getattr(self,"Microchannel_fin_dimension_"+str(i+1)).setText('%s' % float('%.5g' % (parameter*1000)))
            else:
                getattr(self,"Microchannel_fin_dimension_"+str(i+1)).setText('%s' % float('%.5g' % (parameter)))
        self.Microchannel_fin_k.setText('%s' % float('%.5g' % fin_data.fin_K))
        self.Microchannel_fin_t_unit.setCurrentIndex(2)
        self.Microchannel_fin_length_unit.setCurrentIndex(2)
        self.Microchannel_fin_dimension_1_unit.setCurrentIndex(2)
        self.Microchannel_fin_dimension_2_unit.setCurrentIndex(2)
        self.Microchannel_fin_dimension_3_unit.setCurrentIndex(0)
        self.Microchannel_fin_k_unit.setCurrentIndex(0)

    def load_tube(self,tube_data):
        self.Microchannel_tube_width.setText('%s' % float('%.5g' % (tube_data.tube_w*1000)))
        self.Microchannel_tube_height.setText('%s' % float('%.5g' % (tube_data.tube_h*1000)))
        self.Microchannel_tube_spacing.setText('%s' % float('%.5g' % (tube_data.tube_s*1000)))
        self.Microchannel_tube_e_D.setText('%s' % float('%.5g' % (tube_data.tube_e_D)))
        self.Microchannel_port_number.setText('%s' % int('%.5g' % (tube_data.tube_n_ports)))
        self.Microchannel_port_dimension_a.setText('%s' % float('%.5g' % (tube_data.port_dim_1*1000)))
        self.Microchannel_port_shape.setCurrentIndex(tube_data.port_shape_index)
        if tube_data.port_shape_index == 0:
            self.Microchannel_port_dimension_b.setText('%s' % float('%.5g' % (tube_data.port_dim_2*1000)))
            self.Microchannel_port_dimension_b_unit.setCurrentIndex(2)
        elif tube_data.port_shape_index == 1:
            pass
        elif tube_data.port_shape_index == 2:        
            self.Microchannel_port_dimension_b.setText('%s' % float('%.5g' % (tube_data.port_dim_2*1000)))
            self.Microchannel_port_dimension_b_unit.setCurrentIndex(2)
        self.Microchannel_tube_k.setText('%s' % float('%.5g' % tube_data.tube_K))
        
        self.Microchannel_tube_width_unit.setCurrentIndex(2)
        self.Microchannel_tube_height_unit.setCurrentIndex(2)
        self.Microchannel_tube_spacing_unit.setCurrentIndex(2)
        self.Microchannel_port_dimension_a_unit.setCurrentIndex(2)
        self.Microchannel_tube_k_unit.setCurrentIndex(0)
        
    def enable_range_validation(self):
        self.Microchannel_tube_length.editingFinished.connect(lambda: self.validate_range_item("lineedit",'length'))
        self.Microchannel_tube_spacing.editingFinished.connect(lambda: self.validate_range_item("lineedit","length"))
        self.Microchannel_tube_height.editingFinished.connect(lambda: self.validate_range_item("lineedit","length"))
        self.Microchannel_tube_width.editingFinished.connect(lambda: self.validate_range_item("lineedit","length"))
        self.Microchannel_fin_t.editingFinished.connect(lambda: self.validate_range_item("lineedit","length"))
        self.Microchannel_fin_FPI.editingFinished.connect(lambda: self.validate_range_item("lineedit",None))
        self.Microchannel_fin_length.editingFinished.connect(lambda: self.validate_range_item("lineedit","length"))
        self.validated_fin_type = self.Microchannel_fin_type.currentIndex()

        if self.Microchannel_fin_dimension_1.isEnabled():
            self.Microchannel_fin_dimension_1.editingFinished.connect(lambda: self.validate_range_item("lineedit","length"))
        if self.Microchannel_fin_dimension_1.isEnabled():
            self.Microchannel_fin_dimension_1.editingFinished.connect(lambda: self.validate_range_item("lineedit","length"))
        if self.Microchannel_fin_dimension_1.isEnabled():
            self.Microchannel_fin_dimension_1.editingFinished.connect(lambda: self.validate_range_item("lineedit",None))

    def validate_range_item(self,data_type,conversion=None):
        if hasattr(self,"validation_range"):
            sender = self.sender()
            prop_name = sender.objectName()
            validate = True
            if "Microchannel_fin_dimension" in prop_name:
                if self.validated_fin_type != self.Microchannel_fin_type.currentIndex():
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
                    value = sender.value()
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
        
    def validate(self):
        if str(self.Microchannel_tube_width.text()).strip() in ["","-","."]:
            return 0
        elif str(self.Microchannel_tube_height.text()).strip() in ["","-","."]:
            return 0
        elif str(self.Microchannel_tube_length.text()).strip() in ["","-","."]:
            return 0
        elif str(self.Microchannel_tube_spacing.text()).strip() in ["","-","."]:
            return 0
        elif str(self.Microchannel_tube_e_D.text()).strip() in ["","-","."]:
            return 0
        elif str(self.Microchannel_port_number.text()).strip() in ["","-","."]:
            return 0
        elif str(self.Microchannel_header_height.text()).strip() in ["","-","."]:
            return 0
        elif str(self.Microchannel_fin_t.text()).strip() in ["","-","."]:
            return 0
        elif str(self.Microchannel_fin_FPI.text()).strip() in ["","-","."]:
            return 0
        elif str(self.Microchannel_fin_length.text()).strip() in ["","-","."]:
            return 0
        elif str(self.Microchannel_tube_k.text()).strip() in ["","-","."]:
            return 0
        elif str(self.Microchannel_fin_k.text()).strip() in ["","-","."]:
            return 0

        if self.Microchannel_port_shape.currentIndex() == 0:
            if str(self.Microchannel_port_dimension_a.text()).strip() in ["","-","."]:
                return 0
            elif str(self.Microchannel_port_dimension_b.text()).strip() in ["","-","."]:
                return 0

        elif self.Microchannel_port_shape.currentIndex() == 1:
            if str(self.Microchannel_port_dimension_a.text()).strip() in ["","-","."]:
                return 0

        elif self.Microchannel_port_shape.currentIndex() == 1:
            if str(self.Microchannel_port_dimension_a.text()).strip() in ["","-","."]:
                return 0
            elif str(self.Microchannel_port_dimension_b.text()).strip() in ["","-","."]:
                return 0
        
        if self.Microchannel_header_CS_shape.currentIndex() == 0:
            if str(self.Microchannel_header_CS_dimension_a.text()).strip() in ["","-","."]:
                return 0
            elif str(self.Microchannel_header_CS_dimension_b.text()).strip() in ["","-","."]:
                return 0
        
        elif self.Microchannel_header_CS_shape.currentIndex() == 1:
            if str(self.Microchannel_header_CS_dimension_a.text()).strip() in ["","-","."]:
                return 0
            
        if self.Microchannel_fin_type.currentIndex() == 2:
            if str(self.Microchannel_fin_dimension_1.text()).strip() in ["","-","."]:
                return 0
            elif str(self.Microchannel_fin_dimension_2.text()).strip() in ["","-","."]:
                return 0
            elif str(self.Microchannel_fin_dimension_3.text()).strip() in ["","-","."]:
                return 0

        return 1
                    
    def ok_button(self):
        validate = self.validate()
        if validate == 1:
            self.Geometry = values()
            self.Geometry.defined = True
            self.Geometry.T_w = length_unit_converter(self.Microchannel_tube_width.text(),self.Microchannel_tube_width_unit.currentIndex())
            self.Geometry.T_h = length_unit_converter(self.Microchannel_tube_height.text(),self.Microchannel_tube_height_unit.currentIndex())
            self.Geometry.T_l = length_unit_converter(self.Microchannel_tube_length.text(),self.Microchannel_tube_length_unit.currentIndex())
            self.Geometry.T_s = length_unit_converter(self.Microchannel_tube_spacing.text(),self.Microchannel_tube_spacing_unit.currentIndex())
            self.Geometry.e_D = float(self.Microchannel_tube_e_D.text())
            if self.Microchannel_port_end.currentIndex() == 0:
                self.Geometry.T_end_index = 0
                self.Geometry.T_end = "Normal"
            elif self.Microchannel_port_end.currentIndex() == 1:
                self.Geometry.T_end_index = 1
                self.Geometry.T_end = "Extended"
            self.Geometry.N_ports = int(self.Microchannel_port_number.text())
            
            if self.Microchannel_port_shape.currentIndex() == 0:
                self.Geometry.port_shape_index = 0
                self.Geometry.port_shape = "Rectangle"
                self.Geometry.port_a_dim = length_unit_converter(self.Microchannel_port_dimension_a.text(),self.Microchannel_port_dimension_a_unit.currentIndex())
                self.Geometry.port_b_dim = length_unit_converter(self.Microchannel_port_dimension_b.text(),self.Microchannel_port_dimension_b_unit.currentIndex())
            elif self.Microchannel_port_shape.currentIndex() == 1:
                self.Geometry.port_shape_index = 1
                self.Geometry.port_shape = "Circle"
                self.Geometry.port_a_dim = length_unit_converter(self.Microchannel_port_dimension_a.text(),self.Microchannel_port_dimension_a_unit.currentIndex())
            elif self.Microchannel_port_shape.currentIndex() == 2:
                self.Geometry.port_shape_index = 2
                self.Geometry.port_shape = "Triangle"
                self.Geometry.port_a_dim = length_unit_converter(self.Microchannel_port_dimension_a.text(),self.Microchannel_port_dimension_a_unit.currentIndex())
                self.Geometry.port_b_dim = length_unit_converter(self.Microchannel_port_dimension_b.text(),self.Microchannel_port_dimension_b_unit.currentIndex())

            if self.Microchannel_header_CS_shape.currentIndex() == 0:
                self.Geometry.header_shape_index = 0
                self.Geometry.header_shape = "Rectangle"
                self.Geometry.header_a_dim = length_unit_converter(self.Microchannel_header_CS_dimension_a.text(),self.Microchannel_header_CS_dimension_a_unit.currentIndex())
                self.Geometry.header_b_dim = length_unit_converter(self.Microchannel_header_CS_dimension_b.text(),self.Microchannel_header_CS_dimension_b_unit.currentIndex())
            elif self.Microchannel_header_CS_shape.currentIndex() == 1:
                self.Geometry.header_shape_index = 1
                self.Geometry.header_shape = "Circle"
                self.Geometry.header_a_dim = length_unit_converter(self.Microchannel_header_CS_dimension_a.text(),self.Microchannel_header_CS_dimension_a_unit.currentIndex())
            
            self.Geometry.header_height = length_unit_converter(self.Microchannel_header_height.text(),self.Microchannel_header_height_unit.currentIndex())
            self.Geometry.Fin_t = length_unit_converter(self.Microchannel_fin_t.text(),self.Microchannel_fin_t_unit.currentIndex())
            self.Geometry.Fin_FPI = float(self.Microchannel_fin_FPI.text())
            self.Geometry.Fin_l = length_unit_converter(self.Microchannel_fin_length.text(),self.Microchannel_fin_length_unit.currentIndex())
            if self.Microchannel_fin_number.currentIndex() == 0:    
                self.Geometry.Fin_on_side_index = 0
                self.Geometry.Fin_on_side = True
            else:
                self.Geometry.Fin_on_side_index = 1
                self.Geometry.Fin_on_side = False
            if self.Microchannel_fin_type.currentIndex() == 0:
                self.Geometry.Fin_type_index = 0
                self.Geometry.Fin_type = "Louvered"
                self.Geometry.Fin_llouv = length_unit_converter(self.Microchannel_fin_dimension_1.text(),self.Microchannel_fin_dimension_1_unit.currentIndex())
                self.Geometry.Fin_lp = length_unit_converter(self.Microchannel_fin_dimension_2.text(),self.Microchannel_fin_dimension_2_unit.currentIndex())
                self.Geometry.Fin_lalpha = angle_unit_converter(self.Microchannel_fin_dimension_3.text(),self.Microchannel_fin_dimension_3_unit.currentIndex())
                        
            self.Geometry.Tube_k = Thermal_K_unit_converter(self.Microchannel_tube_k.text(),self.Microchannel_tube_k_unit.currentIndex())
            self.Geometry.Fin_k = Thermal_K_unit_converter(self.Microchannel_fin_k.text(),self.Microchannel_fin_k_unit.currentIndex())

            self.Geometry.Header_DP = pressure_unit_converter(self.Microchannel_header_DP.text(),self.Microchannel_header_DP_unit.currentIndex())
            self.close()
            
        elif validate == 0:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please fill all empty fields")
            msg.setWindowTitle("Empty Fields!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()

    def fin_type_changed(self):
        if self.Microchannel_fin_type.currentIndex() == 0:
            self.Microchannel_fin_dimension_1_label.setText("louver Height (L1)*")
            self.Microchannel_fin_dimension_2_label.setText("Louver Pitch (Lp)*")
            self.Microchannel_fin_dimension_3_label.setText("Louver Angle (L<html><span>&alpha;</span></html>)*")
            self.line_7.show()
            self.Microchannel_fin_dimension_1.show()
            self.Microchannel_fin_dimension_2.show()
            self.Microchannel_fin_dimension_3.show()
            self.Microchannel_fin_dimension_1.setEnabled(True)
            self.Microchannel_fin_dimension_2.setEnabled(True)
            self.Microchannel_fin_dimension_3.setEnabled(True)
            self.Microchannel_fin_dimension_1_label.show()
            self.Microchannel_fin_dimension_2_label.show()
            self.Microchannel_fin_dimension_3_label.show()
            self.Microchannel_fin_dimension_1_unit.show()
            self.Microchannel_fin_dimension_2_unit.show()
            self.Microchannel_fin_dimension_3_unit.show()
            self.Microchannel_fin_dimension_3_unit.clear()
            self.Microchannel_fin_dimension_3_unit.addItems(['degree','radian','minute','second'])
            self.Microchannel_fin_dimension_3_unit.setEnabled(True)
            if hasattr(self,"LouveredFins_photo"):
                self.Microchannel_fin_type_photo.setPixmap(self.LouveredFins_photo)
            else:
                self.Microchannel_fin_type_photo.clear()
                self.Microchannel_fin_type_photo.setText("Louvered Fin Demonistration photo")
        
    def port_end_changed(self):
        pass
    
    def port_shape_changed(self):
        if self.Microchannel_port_shape.currentIndex() == 0:
            if hasattr(self,"RectanglePort_photo"):
                self.Microchannel_port_dimension_photo.setPixmap(self.RectanglePort_photo)
            else:
                self.Microchannel_port_dimension_photo.clear()
                self.Microchannel_port_dimension_photo.setText("Rectangular Port Demonistration photo")
            self.Microchannel_port_dimension_a.setEnabled(True)
            self.Microchannel_port_dimension_a_unit.setEnabled(True)
            self.Microchannel_port_dimension_b.setEnabled(True)
            self.Microchannel_port_dimension_b_unit.setEnabled(True)

        elif self.Microchannel_port_shape.currentIndex() == 1:
            if hasattr(self,"CirclePort_photo"):
                self.Microchannel_port_dimension_photo.setPixmap(self.CirclePort_photo)
            else:
                self.Microchannel_port_dimension_photo.clear()
                self.Microchannel_port_dimension_photo.setText("Circular Port Demonistration photo")
            self.Microchannel_port_dimension_a.setEnabled(True)
            self.Microchannel_port_dimension_a_unit.setEnabled(True)
            self.Microchannel_port_dimension_b.setEnabled(False)
            self.Microchannel_port_dimension_b_unit.setEnabled(False)

        elif self.Microchannel_port_shape.currentIndex() == 2:
            if hasattr(self,"TrianglePort_photo"):
                self.Microchannel_port_dimension_photo.setPixmap(self.TrianglePort_photo)
            else:
                self.Microchannel_port_dimension_photo.clear()
                self.Microchannel_port_dimension_photo.setText("Triangular Port Demonistration photo")
            self.Microchannel_port_dimension_a.setEnabled(True)
            self.Microchannel_port_dimension_a_unit.setEnabled(True)
            self.Microchannel_port_dimension_b.setEnabled(True)
            self.Microchannel_port_dimension_b_unit.setEnabled(True)

    def header_shape_changed(self):
        if self.Microchannel_header_CS_shape.currentIndex() == 0:
            if hasattr(self,"RectangleHeader_photo"):
                self.Microchannel_header_photo.setPixmap(self.RectangleHeader_photo)
            else:
                self.Microchannel_header_photo.clear()
                self.Microchannel_header_photo.setText("Rectangular Header Demonistration photo")
            self.Microchannel_header_CS_dimension_a.setEnabled(True)
            self.Microchannel_header_CS_dimension_a_unit.setEnabled(True)
            self.Microchannel_header_CS_dimension_b.setEnabled(True)
            self.Microchannel_header_CS_dimension_b_unit.setEnabled(True)

        elif self.Microchannel_header_CS_shape.currentIndex() == 1:
            if hasattr(self,"CircleHeader_photo"):
                self.Microchannel_header_photo.setPixmap(self.CircleHeader_photo)
            else:
                self.Microchannel_header_photo.clear()
                self.Microchannel_header_photo.setText("Circular Header Demonistration photo")
            self.Microchannel_header_CS_dimension_a.setEnabled(True)
            self.Microchannel_header_CS_dimension_a_unit.setEnabled(True)
            self.Microchannel_header_CS_dimension_b.setEnabled(False)
            self.Microchannel_header_CS_dimension_b_unit.setEnabled(False)
            
    def cancel_button(self):
        self.close()
        
if __name__ == '__main__':
    def main():
        app=QApplication(sys.argv)
        app.setStyle('Fusion')
        window = Microchannel_Geometry_Window()
        window.show()
        app.exec_()
    try:
        main()
    except Exception as why:
        print(why)

