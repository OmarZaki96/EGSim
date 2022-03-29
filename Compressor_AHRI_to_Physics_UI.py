from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
import os, sys
import CoolProp as CP
from unit_conversion import *
from inputs_validation import check_compressor_AHRI, check_compressor_physics, check_compressor_map
from GUI_functions import load_refrigerant_list
from Compressor_AHRI_to_Physics import AHRI_to_Physics, validation_physics_model
from GUI_functions import write_comp_xml
import appdirs
from copy import deepcopy
import datetime
from backend.Functions import get_AS

FROM_Compressor_to_Physics,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Compressor_to_physics.ui"))

class values():
    pass

class Compressor_to_physics_Window(QDialog, FROM_Compressor_to_Physics):
    def __init__(self, parent=None):
        super(Compressor_to_physics_Window, self).__init__(parent)
        self.setupUi(self)
        
        self.parent = parent
        
        # create database path
        self.database_path = appdirs.user_data_dir("EGSim")+"/Database/"        
        
        # populate refrigerant list
        ref_list = load_refrigerant_list()
        if not ref_list[0]:
            self.raise_error_meesage("Could not load refrigerants list, program will exit")
            self.close()
        else:
            ref_list = ref_list[1]
        self.Comp_ref.addItems(ref_list[:,0])
        self.ref_list = ref_list

        # validator
        only_number = QRegExpValidator(QRegExp("(([0-9]+\.[0-9]*[1-9][0-9]*)|([0-9]*[1-9][0-9]*\.[0-9]+)|([0-9]*[1-9][0-9]*))"))
        self.Speed.setValidator(only_number)
        
        # create connections
        self.Convert_button.clicked.connect(self.convert_clicked)
        self.Create_compressor_button.clicked.connect(self.create_compressor_clicked)

        # intially load compressors
        self.load_compressors()

        # initially load REFPROP
        self.load_REFPROP()

    def load_compressors(self):
        self.Compressors_list.clear()
        self.parent.load_database()
        # load available components
        List_of_Components = []
        for Compressor in self.parent.Comp_names:
            List_of_Components.append(Compressor[1])

        self.Compressors_list.addItems(List_of_Components)

        disabled_list = []
        for i,Compressor in enumerate(self.parent.Compressor_list):
            if Compressor[1].Comp_model == "physics":
                self.Compressors_list.item(i).setFlags(Qt.NoItemFlags)
        

    def load_REFPROP(self):
        path_to_ini = appdirs.user_data_dir("EGSim")+"\REFPROP.ini"
        if os.path.exists(path_to_ini):
            with open(path_to_ini, 'r') as file:
                for line in file:    
                    path = line.strip()
                    if os.path.exists(path):
                        try:
                            CP.CoolProp.set_config_string(CP.ALTERNATIVE_REFPROP_PATH, path)
                            self.refprop_path = path
                            break
                        except:
                            self.Ref_library.setCurrentIndex(1)
                    else:
                        self.Ref_library.setCurrentIndex(1)
        else:
            self.Ref_library.setCurrentIndex(1)

    def validate_convert(self):
        if self.Speed.text() in ["","-","."]:
            self.raise_error_meesage("Please enter compressor operating speed")
            return 0
        
        if self.Te_from.value() >= self.Te_to.value():
            self.raise_error_meesage("Evaporating temperature range is invalid")
            return 0
            
        if self.Tc_from.value() >= self.Tc_to.value():
            self.raise_error_meesage("Condensing temperature range is invalid")
            return 0

        if self.Tc_from.value() <= self.Te_to.value():
            self.raise_error_meesage("Condensing temperature range should be greater than evaporating temperature range")
            return 0
                    
        if self.Compressors_list.currentRow() == -1:
            self.raise_error_meesage("Please choose a compressor to be converted")
        
        self.Compressor = self.parent.Compressor_list[self.Compressors_list.currentRow()][1]
        
        if not (self.Compressor.Ref in self.ref_list[:,0]):
            self.raise_error_meesage("Compressor refrigerant does not exist in refrigerant database")
        
        if self.Ref_library.currentIndex() == 0:
            Backend = "REFPROP"
        else:
            Backend = "HEOS"
        AS = get_AS(Backend,self.Compressor.Ref,None)
        if AS[0]:
            self.AS = AS[1]
        else:        
            self.raise_error_meesage("Failed to use REFPROP!")
            return 0
        return 1
    
    def convert_clicked(self):
        validate = self.validate_convert()
        if validate == 1:
            try:
                self.eta_volumetric.setText("")
                self.eta_isentropic.setText("")
                self.RMSE_M.setText("")
                self.RMSE_P.setText("")
                if hasattr(self,"Compressor_base"):
                    delattr(self,"Compressor_base")
                if self.Compressor.Comp_model == "10coefficients":
                    Comp_props = {'F_factor': self.Compressor.Comp_AHRI_F_value,
                                  'act_speed':float(self.Speed.text()),
                                  'M_array':self.Compressor.M,
                                  'P_array':self.Compressor.P,
                                  'Displacement':self.Compressor.Comp_vol,
                                  'fp':self.Compressor.Comp_fp,
                                  'Unit_system':self.Compressor.unit_system,
                                  'Speeds':self.Compressor.speeds,
                                  }
                    
                    if self.Compressor.std_type == 0:
                        Comp_props['SH_type'] = 0
                        Comp_props['SH_Ref'] = self.Compressor.std_sh
                    elif self.Compressor.std_type == 1:
                        Comp_props['SH_type'] = 1
                        Comp_props['Suction_Ref'] = self.Compressor.std_suction
                    
                elif self.Compressor.Comp_model == "map":
                    Comp_props = {'F_factor': self.Compressor.map_data.F_value,
                                  'act_speed':float(self.Speed.text()),
                                  'M_array':self.Compressor.map_data.M_coeffs,
                                  'P_array':self.Compressor.map_data.P_coeffs,
                                  'Displacement':self.Compressor.Comp_vol,
                                  'fp':self.Compressor.Comp_fp,
                                  'Unit_system':self.Compressor.unit_system,
                                  'Speeds':self.Compressor.map_data.Speeds,
                                  }
                    if self.Compressor.map_data.std_type == 0:
                        Comp_props['SH_type'] = 0
                        Comp_props['SH_Ref'] = self.Compressor.map_data.std_sh
                        SH = self.Compressor.map_data.std_sh
                    elif self.Compressor.map_data.std_type == 1:
                        Comp_props['SH_type'] = 1
                        Comp_props['Suction_Ref'] = self.Compressor.map_data.std_suction
                        SH = self.Compressor.map_data.std_suction
                    
                AS = self.AS
                Tevap_range = (self.Te_from.value()+273.15,self.Te_to.value()+273.15,self.Te_step.value())
                Tcond_range = (self.Tc_from.value()+273.15,self.Tc_to.value()+273.15,self.Tc_step.value())
                volum_model_degree = self.volumetric_degree.value()
                isen_model_degree = self.isentropic_degree.value()
                vol_eff, isen_eff = AHRI_to_Physics(Comp_props,AS,Tevap_range,Tcond_range,volum_model_degree,isen_model_degree)
                RMSE_M,RMSE_P = validation_physics_model(Comp_props,Tevap_range,Tcond_range,vol_eff,isen_eff,AS,self.Compressor.Ref)
                succeeded = True
            except:
                import traceback
                print(traceback.format_exc())
                self.raise_error_meesage("Failed to convert compressor")
                succeeded = False
            
            if succeeded:
                self.eta_volumetric.setText(vol_eff.replace("**","^"))
                self.eta_isentropic.setText(isen_eff.replace("**","^"))
                self.RMSE_M.setText(str(RMSE_M))
                self.RMSE_P.setText(str(RMSE_P))
                self.raise_success_meesage("Conversion succeeded!")
                Compressor = deepcopy(self.parent.Compressor_list[self.Compressors_list.currentRow()])
                Compressor[1].Comp_model = "physics"
                Compressor[1].isentropic_exp = self.eta_isentropic.text().replace("^","**")
                Compressor[1].vol_exp = self.eta_volumetric.text().replace("^","**")
                Compressor[1].SH_type = Comp_props['SH_type']
                if Comp_props['SH_type'] == 0:    
                    Compressor[1].SH_Ref = Comp_props['SH_Ref']
                elif Comp_props['SH_type'] == 1:
                    Compressor[1].Suction_Ref = Comp_props['Suction_Ref']
                Compressor[1].F_factor = Comp_props['F_factor']
                Compressor[1].Comp_ratio_P = 1.0
                Compressor[1].Comp_ratio_M = 1.0
                Compressor[1].Comp_speed = float(self.Speed.text())
                self.Compressor_base = Compressor
                self.Comp_name.setEnabled(True)
                self.Comp_ref.setEnabled(True)
                self.Create_compressor_button.setEnabled(True)
            else:
                self.Comp_name.setEnabled(False)
                self.Comp_ref.setEnabled(False)
                self.Create_compressor_button.setEnabled(False)

    def validate_create_compressor(self):
        if self.Speed.text() in ["","-","."]:
            self.raise_error_meesage("Please enter compressor operating speed")
            return 0
        if (not hasattr(self,"Compressor_base")):
            self.raise_error_meesage("You have to perform a successful conversion first")
            return 0
        
        return 1
    
    def create_compressor_clicked(self):
        Compressor = self.Compressor_base
        file_name = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '.comp'
        path = self.database_path + file_name
        Compressor[0] = file_name
        Compressor[1].Comp_name = self.Comp_name.text()
        Compressor[1].Ref = self.Comp_ref.currentText()
        result = write_comp_xml(Compressor[1],path)
        if result:
            self.parent.Compressor_list.append(Compressor)
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("Compressor was added successfully")
            msg.setWindowTitle("Compressor added")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Compressor Could not be added")
            msg.setWindowTitle("Compressor was not added!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        self.load_compressors()

    def raise_error_meesage(self,message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(message)
        msg.setWindowTitle("Error!")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def raise_success_meesage(self,message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(message)
        msg.setWindowTitle("Success!")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def closeEvent(self, event):
        quit_msg = "Are you sure you want to close the window?"
        reply = QMessageBox.question(self, 'Message', 
                         quit_msg, QMessageBox.Yes, QMessageBox.No)
    
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
            
if __name__ == '__main__':
    def main():
        app=QApplication(sys.argv)
        app.setStyle('Fusion')
        window = Compressor_to_physics_Window()
        window.show()
        app.exec_()
    try:
        main()
    except Exception as why:
        print(why)
