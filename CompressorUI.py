from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
import os, sys, csv, io
import CoolProp as CP
from copy import deepcopy
from GUI_functions import read_comp_AHRI_xml, write_comp_AHRI_xml, read_comp_xml, write_comp_xml, load_last_location, save_last_location
from sympy.parsing.sympy_parser import parse_expr
from sympy import S, Symbol
from unit_conversion import *
from inputs_validation import check_compressor_AHRI, check_compressor_physics, check_compressor_map
from CompressorUI_AHRI import Compressor_AHRI
from CompressorUI_Map import Compressor_Map
from CompressorUI_physics import Compressor_Physics
from GUI_functions import load_refrigerant_list

FROM_Compressor_Main,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Compressor_main.ui"))

class values():
    pass

class CompressorWindow(QDialog, FROM_Compressor_Main):
    def __init__(self, parent=None):
        super(CompressorWindow, self).__init__(parent)
        self.setupUi(self)

        # populate refrigerants
        ref_list = load_refrigerant_list()
        if not ref_list[0]:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Could not load refrigerants list, program will exit")
            msg.setWindowTitle("Sorry!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            self.close()
        else:
            ref_list = ref_list[1]
        self.Comp_ref.addItems(ref_list[:,0])
        
        self.Comp_model_define_button.clicked.connect(self.comp_definition_dialog)
        self.Comp_model.currentIndexChanged.connect(self.Comp_model_changed)
        self.Comp_cancel_button.clicked.connect(self.cancel_button)
        self.Comp_load_button.clicked.connect(self.load_button)
        self.Comp_save_button.clicked.connect(self.save_button)
        self.Comp_ok_button.clicked.connect(self.ok_button)
        only_number = QRegExpValidator(QRegExp("(([0-9]+\.[0-9]*[1-9][0-9]*)|([0-9]*[1-9][0-9]*\.[0-9]+)|([0-9]*[1-9][0-9]*))"))
        self.Comp_vol.setValidator(only_number)
        self.Comp_speed.setValidator(only_number)
        self.Comp_ratio_M.setValidator(only_number)
        self.Comp_ratio_P.setValidator(only_number)

    def load_fields(self,comp):
        try:
            self.Comp_name.setText(str(comp.Comp_name))
            index = self.Comp_ref.findText(comp.Ref, Qt.MatchFixedString)
            self.Comp_ref.setCurrentIndex(index)
            comp_vol = comp.Comp_vol*1e6
            self.Comp_vol.setText("%.5g" % comp_vol)
            self.Comp_speed.setText("%.5g" % comp.Comp_speed)
            self.Comp_fp.setValue(comp.Comp_fp*100)
            self.Comp_elec_eff.setValue(comp.Comp_elec_eff*100)
            self.Comp_ratio_M.setText("%.5g" % comp.Comp_ratio_M)
            self.Comp_ratio_P.setText("%.5g" % comp.Comp_ratio_P)
            
            if comp.Comp_model == "physics":
                index = 0
            elif comp.Comp_model == "10coefficients":
                index = 1
            elif comp.Comp_model == "map":
                index = 2
            else:
                index = 0
            self.Comp_model.setCurrentIndex(index)
            
            if self.Comp_model.currentIndex() == 0:
                self.isentropic_exp = comp.isentropic_exp
                self.vol_exp = comp.vol_exp
            elif self.Comp_model.currentIndex() == 1:
                self.unit_system = comp.unit_system
                self.num_speeds = comp.num_speeds
                self.std_type = comp.std_type
                if comp.std_type == 0:
                    self.std_sh = comp.std_sh
                elif comp.std_type == 1:
                    self.std_suction = comp.std_suction
                self.speeds = comp.speeds
                self.Comp_AHRI_F_value = comp.Comp_AHRI_F_value
                self.M = comp.M
                self.P = comp.P
                
            elif self.Comp_model.currentIndex() == 2:
                self.map_data = values()
                self.map_data.std_type = comp.map_data.std_type
                if comp.map_data.std_type == 0:
                    self.map_data.std_sh = comp.map_data.std_sh
                elif comp.map_data.std_type == 1:
                    self.map_data.std_suction = comp.map_data.std_suction
                self.map_data.F_value = comp.map_data.F_value
                self.map_data.Speeds = comp.map_data.Speeds
                self.map_data.Tcond_unit = comp.map_data.Tcond_unit
                self.map_data.Tevap_unit = comp.map_data.Tevap_unit
                self.map_data.M_unit = comp.map_data.M_unit
                self.map_data.M_array = comp.map_data.M_array
                self.map_data.P_array = comp.map_data.P_array
                self.map_data.M_coeffs = comp.map_data.M_coeffs
                self.map_data.P_coeffs = comp.map_data.P_coeffs
            self.Comp_save_button.setEnabled(True)
            self.Comp_ok_button.setEnabled(True)
        except:
            import traceback
            print(traceback.format_exc())
            self.raise_error_message("Faield to load compressor inputs")
        
    def load_button(self):
        path = QFileDialog.getOpenFileName(self, 'Open compressor file',directory=load_last_location(),filter="Compressor file (*.comp);;All files (*.*)")[0]
        if path != "":
            save_last_location(path)
            result = read_comp_xml(path)
            if result[0]:
                try:
                    comp = result[1]
                    self.load_fields(comp)
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
        check = self.validate()
        if check in [1,2,3]:
            path = QFileDialog.getSaveFileName(self, caption='Save compressor file',directory=load_last_location(),filter="Compressor file (*.comp);;All files (*.*)")[0]
            if path != "":
                save_last_location(path)
                if path[-5:].lower() != ".comp":
                    path = path+".comp"
                class values():
                    pass
                comp = values()
                comp.Comp_name = str(self.Comp_name.text())
                comp.Ref = str(self.Comp_ref.currentText())
                comp.Comp_vol = str(volume_unit_converter(self.Comp_vol.text(),self.Comp_vol_unit.currentIndex()))
                comp.Comp_speed = str(self.Comp_speed.text())
                comp.Comp_fp = str(self.Comp_fp.value()/100)
                comp.Comp_elec_eff = str(self.Comp_elec_eff.value()/100)
                comp.Comp_ratio_M = str(self.Comp_ratio_M.text())
                comp.Comp_ratio_P = str(self.Comp_ratio_P.text())
                if self.Comp_model.currentIndex() == 0:
                    comp.Comp_model = "physics"
                    comp.isentropic_exp = self.isentropic_exp
                    comp.vol_exp = self.vol_exp
                elif self.Comp_model.currentIndex() == 1:
                    comp.Comp_model = "10coefficients"
                    comp.unit_system = self.unit_system
                    comp.std_type = self.std_type
                    comp.num_speeds = self.num_speeds
                    if self.std_type == 0:
                        comp.std_sh = self.std_sh
                    elif self.std_type == 1:
                        comp.std_suction = self.std_suction                        
                    comp.Comp_AHRI_F_value = self.Comp_AHRI_F_value
                    comp.speeds = self.speeds
                    comp.M = self.M
                    comp.P = self.P
                elif self.Comp_model.currentIndex() == 2:
                    comp.Comp_model = "map"
                    comp.map_data = self.map_data
                    comp.unit_system = "si"
                    if self.map_data.std_type == 0:
                        comp.std_sh = float(self.map_data.std_sh)
                    elif self.map_data.std_type == 1:
                        comp.std_suction = float(self.map_data.std_suction)
                result = write_comp_xml(comp,path)
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
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please fill all empty fields")
            msg.setWindowTitle("Empty fields!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()

    def raise_error_message(self,message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(message)
        msg.setWindowTitle("Error!")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def ok_button(self):
        check = self.validate()
        if check == 1:
            class CompressorClass():
                pass
            Compressor = CompressorClass()
            Compressor.Comp_name = str(self.Comp_name.text()).strip()
            Compressor.Ref = str(self.Comp_ref.currentText())
            Compressor.Comp_vol = volume_unit_converter(self.Comp_vol.text(),self.Comp_vol_unit.currentIndex())
            Compressor.Comp_speed = float(self.Comp_speed.text())
            Compressor.Comp_fp = float(self.Comp_fp.value())/100
            Compressor.Comp_elec_eff = float(self.Comp_elec_eff.value())/100
            Compressor.Comp_ratio_M = float(self.Comp_ratio_M.text())
            Compressor.Comp_ratio_P = float(self.Comp_ratio_P.text())
            if hasattr(self,"capacity_validation"):
                if self.capacity_validation:
                    Compressor.capacity_validation_table = self.capacity_validation_table

            selection = str(self.Comp_model.currentText())
            if self.Comp_model.currentIndex() == 0:
                Compressor.Comp_model = "physics"
                Compressor.isentropic_exp = self.isentropic_exp
                Compressor.vol_exp = self.vol_exp
                validation = check_compressor_physics(Compressor)
            elif self.Comp_model.currentIndex() == 1:
                Compressor.Comp_model = "10coefficients"
                Compressor.unit_system = self.unit_system
                Compressor.std_type = self.std_type
                if self.std_type == 0:
                    Compressor.std_sh = float(self.std_sh)
                elif self.std_type == 1:
                    Compressor.std_suction = float(self.std_suction)
                Compressor.Comp_AHRI_F_value = float(self.Comp_AHRI_F_value)
                Compressor.num_speeds = self.num_speeds
                Compressor.speeds = self.speeds
                Compressor.M = self.M
                Compressor.P = self.P
                validation = check_compressor_AHRI(Compressor)
            elif self.Comp_model.currentIndex() == 2:
                Compressor.Comp_model = "map"
                Compressor.unit_system = "si"
                if self.map_data.std_type == 0:
                    Compressor.std_sh = float(self.map_data.std_sh)
                elif self.map_data.std_type == 1:
                    Compressor.std_suction = float(self.map_data.std_suction)
                    
                Compressor.Comp_AHRI_F_value = float(self.map_data.F_value)
                Compressor.num_speeds = len(self.map_data.Speeds)
                Compressor.speeds = self.map_data.Speeds
                Compressor.M = self.map_data.M_coeffs
                Compressor.P = self.map_data.P_coeffs
                Compressor.Tcond_unit = self.map_data.Tcond_unit
                Compressor.Tevap_unit = self.map_data.Tevap_unit
                Compressor.M_unit = self.map_data.M_unit
                Compressor.M_array = self.map_data.M_array
                Compressor.P_array = self.map_data.P_array
                Compressor.map_data = self.map_data
                validation = check_compressor_map(Compressor)
            Compressor.model_data_exist = True
            if validation[0] == 1:
                self.Compressor = Compressor
                self.close()
                
            elif validation[0] == 2:
                reply = QMessageBox.warning(self, 'Warning!',
                    validation[1]+" Continue?", QMessageBox.Yes | 
                    QMessageBox.No, QMessageBox.No)
            
                if reply == QMessageBox.Yes:
                    self.Compressor = Compressor
                    self.close()
                else:
                    pass
            else:
                self.raise_error_message(validation[1])      

        elif check == 0:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please fill all empty fields")
            msg.setWindowTitle("Empty fields!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        elif check == 2:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Heat losses fraction can not be 100%")
            msg.setWindowTitle("Wrong Value!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        elif check == 3:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Electrical efficinecy can not be 0%")
            msg.setWindowTitle("Wrong Value!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        elif check == 4:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("You must specify a refrigerant unless physics model is used")
            msg.setWindowTitle("Wrong Value!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()

    def validate(self):
        if str(self.Comp_name.text()).replace(" ","") in ["","-","."]:
            return 0
        if self.Comp_vol.text() in ["","-","."]:
            return 0
        if self.Comp_speed.text() in ["","-","."]:
            return 0
        if self.Comp_ratio_M.text() in ["","-","."]:
            return 0
        if self.Comp_ratio_P.text() in ["","-","."]:
            return 0
        if self.Comp_fp.value() == 100:
            return 2
        if self.Comp_elec_eff.value() == 0.0:
            return 3
        if not (self.Comp_model.currentIndex() == 0):
            if self.Comp_ref.currentIndex() == 0:
                return 4
        return 1

    def cancel_button(self):
        self.close()

    def comp_definition_dialog(self):
        selection = str(self.Comp_model.currentText())
        if self.Comp_model.currentIndex() == 0:
            Comp_physics_dialog = Compressor_Physics(self)
            Comp_physics_dialog.setFocusPolicy(Qt.StrongFocus)
            if hasattr(self,'isentropic_exp'):
                Comp_physics_dialog.Comp_physics_isentropic_eff.setText(self.isentropic_exp.replace("**","^"))
            if hasattr(self,'vol_exp'):
                Comp_physics_dialog.Comp_physics_vol_eff.setText(self.vol_exp.replace("**","^"))
            Comp_physics_dialog.exec_()
            if hasattr(Comp_physics_dialog,"isentropic_exp"):
                self.isentropic_exp = Comp_physics_dialog.isentropic_exp
                self.vol_exp = Comp_physics_dialog.vol_exp
                self.Comp_save_button.setEnabled(True)
                self.Comp_ok_button.setEnabled(True)
        elif self.Comp_model.currentIndex() == 1:
            Comp_AHRI_dialog = Compressor_AHRI(self)
            Comp_AHRI_dialog.setFocusPolicy(Qt.StrongFocus)
            if hasattr(self,"unit_system"):
                if self.unit_system == "ip":                    
                    Comp_AHRI_dialog.Comp_AHRI_unitsys.setCurrentIndex(0)
                elif self.unit_system == "si":
                    Comp_AHRI_dialog.Comp_AHRI_unitsys.setCurrentIndex(1)                    
                elif self.unit_system == "si2":
                    Comp_AHRI_dialog.Comp_AHRI_unitsys.setCurrentIndex(2)
                    
            if hasattr(self,"num_speeds"):
                Comp_AHRI_dialog.Comp_AHRI_num_speed.setValue(int(self.num_speeds))
                Comp_AHRI_dialog.AHRI_num_speed_change()
            if hasattr(self,'std_type'):
                if self.std_type == 0:
                    Comp_AHRI_dialog.Comp_AHRI_std_sh_radio.setChecked(True)
                    if hasattr(self,"std_sh"):
                        Comp_AHRI_dialog.Comp_AHRI_std_sh.setText("%.5g" % self.std_sh)
                elif self.std_type == 1:
                    Comp_AHRI_dialog.Comp_AHRI_std_suction_radio.setChecked(True)
                    if hasattr(self,"std_suction"):
                        Comp_AHRI_dialog.Comp_AHRI_std_suction.setText("%.5g" % temperature_unit_converter(self.std_suction,0,True))
            if hasattr(self,"Comp_AHRI_F_value"):
                Comp_AHRI_dialog.Comp_AHRI_F.setText(str(self.Comp_AHRI_F_value))
            if hasattr(self,"speeds"):
                for i in range(int(self.num_speeds)):
                    getattr(Comp_AHRI_dialog,'Comp_nominal_speed_'+str(i+1)).setText(str(self.speeds[i]))
            if hasattr(self,"M"):
                for i in range(int(self.num_speeds)):
                    for col in range(10):
                        getattr(Comp_AHRI_dialog,'Comp_coefficients_table_'+str(i+1)).setItem(0, col, QTableWidgetItem(str(self.M[i][col])))
            if hasattr(self,"P"):
                for i in range(int(self.num_speeds)):
                    for col in range(10):
                        getattr(Comp_AHRI_dialog,'Comp_coefficients_table_'+str(i+1)).setItem(1, col, QTableWidgetItem(str(self.P[i][col])))
            Comp_AHRI_dialog.exec_()
            if hasattr(Comp_AHRI_dialog,'num_speeds'):
                self.num_speeds = Comp_AHRI_dialog.num_speeds
            if hasattr(Comp_AHRI_dialog,'unit_system'):
                if Comp_AHRI_dialog.unit_system == 0:
                    self.unit_system = "ip"
                elif Comp_AHRI_dialog.unit_system == 1:
                    self.unit_system = "si"
                elif Comp_AHRI_dialog.unit_system == 2:
                    self.unit_system = "si2"
            if hasattr(Comp_AHRI_dialog,"std_type"):
                self.std_type = Comp_AHRI_dialog.std_type
                if Comp_AHRI_dialog.std_type == 0:
                    if hasattr(Comp_AHRI_dialog,'std_sh'):
                        self.std_sh = Comp_AHRI_dialog.std_sh
                elif Comp_AHRI_dialog.std_type == 1:
                    if hasattr(Comp_AHRI_dialog,'std_suction'):
                        self.std_suction = Comp_AHRI_dialog.std_suction
            if hasattr(Comp_AHRI_dialog,'Comp_AHRI_F_value'):
                self.Comp_AHRI_F_value = Comp_AHRI_dialog.Comp_AHRI_F_value
            if hasattr(Comp_AHRI_dialog,'speeds'):
                self.speeds = Comp_AHRI_dialog.speeds
            if hasattr(Comp_AHRI_dialog,'M'):
                self.M = Comp_AHRI_dialog.M
            if hasattr(Comp_AHRI_dialog,'P'):
                self.P = Comp_AHRI_dialog.P
                self.Comp_save_button.setEnabled(True)
                self.Comp_ok_button.setEnabled(True)
        elif self.Comp_model.currentIndex() == 2:
            Comp_map_dialog = Compressor_Map()
            Comp_map_dialog.setFocusPolicy(Qt.StrongFocus)
            if hasattr(self,"map_data"):
                Comp_map_dialog.load_fields(self.map_data)
            Comp_map_dialog.exec_()
            if hasattr(Comp_map_dialog,"map_window"):
                self.map_data = Comp_map_dialog.map_window
            self.Comp_save_button.setEnabled(True)
            self.Comp_ok_button.setEnabled(True)
        else:
            raise
    
    def Comp_model_changed(self):
        if hasattr(self,"isentropic_exp"):
            delattr(self,"isentropic_exp")
        if hasattr(self,"vol_exp"):
            delattr(self,"vol_exp")
        if hasattr(self,"num_speeds"):
            delattr(self,"num_speeds")
        if hasattr(self,"unit_system"):
            delattr(self,"unit_system")
        if hasattr(self,"speeds"):
            delattr(self,"speeds")
        if hasattr(self,"std_sh"):
            delattr(self,"std_sh")
        if hasattr(self,"std_suction"):
            delattr(self,"std_suction")
        if hasattr(self,"std_type"):
            delattr(self,"std_type")
        if hasattr(self,"M"):
            delattr(self,"M")
        if hasattr(self,"P"):
            delattr(self,"P")
        if hasattr(self,"Comp_AHRI_F_value"):
            delattr(self,"Comp_AHRI_F_value")
        if hasattr(self,"map_data"):
            delattr(self,"map_data")
        
        self.Comp_save_button.setEnabled(False)
        self.Comp_ok_button.setEnabled(False)


if __name__ == '__main__':
    def main():
        app=QApplication(sys.argv)
        app.setStyle('Fusion')
        window = CompressorWindow()
        window.show()
        app.exec_()
    try:
        main()
    except Exception as why:
        print(why)

