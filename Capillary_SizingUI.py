from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
import os, sys
import CoolProp as CP
from unit_conversion import *
from GUI_functions import load_refrigerant_list
import datetime
import appdirs
from scipy.optimize import least_squares,newton
from backend.Capillary import CapillaryClass
import numpy as np
from backend.Functions import get_AS

FROM_Capillary_Sizing,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Capillary_Sizing.ui"))

class values():
    pass

class Capillary_sizing_window(QDialog, FROM_Capillary_Sizing):
    def __init__(self, parent=None):
        super(Capillary_sizing_window, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent
        
        # populate refrigerant list
        ref_list = load_refrigerant_list()
        if not ref_list[0]:
            self.raise_error_meesage("Could not load refrigerants list, program will exit")
            self.close()
        else:
            ref_list = ref_list[1]
        self.Ref.addItems(ref_list[:,0])
        self.ref_list = ref_list

        # validator
        only_number = QRegExpValidator(QRegExp("(([0-9]+\.[0-9]*[1-9][0-9]*)|([0-9]*[1-9][0-9]*\.[0-9]+)|([0-9]*[1-9][0-9]*))"))
        only_number_negative = QRegExpValidator(QRegExp("[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)"))
        self.Cycle_Capacity.setValidator(only_number)
        self.Condensing_T.setValidator(only_number_negative)
        self.Evaporating_T.setValidator(only_number_negative)
        self.Subcooling.setValidator(only_number)
        self.Superheat.setValidator(only_number)
        self.Diameter.setValidator(only_number)
        
        # create connections
        self.Calculate_button.clicked.connect(self.calculate)
        self.Condensing_T_label.toggled.connect(self.check_cond_input)
        self.Condensing_P_label.toggled.connect(self.check_cond_input)
        self.Evaporating_T_label.toggled.connect(self.check_evap_input)
        self.Evaporating_P_label.toggled.connect(self.check_evap_input)

        # initially load REFPROP
        self.load_REFPROP()        
        
        # defining radio button groups
        self.Cond_group = QButtonGroup()
        self.Cond_group.addButton(self.Condensing_T_label)
        self.Cond_group.addButton(self.Condensing_P_label)

        self.Evap_group = QButtonGroup()
        self.Evap_group.addButton(self.Evaporating_T_label)
        self.Evap_group.addButton(self.Evaporating_P_label)

    def check_cond_input(self):
        if self.Condensing_T_label.isChecked():
            self.Condensing_T.setEnabled(True)
            self.Condensing_T_unit.setEnabled(True)
            self.Condensing_P.setEnabled(False)
            self.Condensing_P_unit.setEnabled(False)
        elif self.Condensing_P_label.isChecked():
            self.Condensing_T.setEnabled(False)
            self.Condensing_T_unit.setEnabled(False)
            self.Condensing_P.setEnabled(True)
            self.Condensing_P_unit.setEnabled(True)

    def check_evap_input(self):
        if self.Evaporating_T_label.isChecked():
            self.Evaporating_T.setEnabled(True)
            self.Evaporating_T_unit.setEnabled(True)
            self.Evaporating_P.setEnabled(False)
            self.Evaporating_P_unit.setEnabled(False)
        elif self.Evaporating_P_label.isChecked():
            self.Evaporating_T.setEnabled(False)
            self.Evaporating_T_unit.setEnabled(False)
            self.Evaporating_P.setEnabled(True)
            self.Evaporating_P_unit.setEnabled(True)

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

    def validate(self):
        if self.Cycle_Capacity.text() in ["","-","."]:
            self.raise_error_meesage("Please enter Cycle Capacity")
            return 0
        if self.Condensing_T.text() in ["","-","."]:
            self.raise_error_meesage("Please enter Condensing temperature")
            return 0
        if self.Evaporating_T.text() in ["","-","."]:
            self.raise_error_meesage("Please enter evaporating temperature")
            return 0
        try:
            if float(self.Condensing_T.text()) <= float(self.Evaporating_T.text()):
                self.raise_error_meesage("Condensing temperature has to be larger than evaporating temperature")
                return 0
        except:
            self.raise_error_meesage("Error in condensing or evaporating temperatures")

        if self.Subcooling.text() in ["","-","."]:
            self.raise_error_meesage("Please enter subcooling")
            return 0

        if self.Superheat.text() in ["","-","."]:
            self.raise_error_meesage("Please enter superheat")
            return 0

        if float(self.Subcooling.text()) == 0:
            self.raise_error_meesage("Subcooling value can not be zero")
            return 0

        if float(self.Superheat.text() ) == 0:
            self.raise_error_meesage("Superheat value can not be zero")
            return 0
            
        if self.Compressor_isen_eff.value() == 0:
            self.raise_error_meesage("Compressor isentropic efficiency can not be zero")
            return 0

        if self.Diameter.text() in ["","-","."]:
            self.raise_error_meesage("Please enter Capillary tube Diameter")
            return 0

        if float(self.Diameter.text() ) == 0:
            self.raise_error_meesage("Capillary tube diameter can not be zero")
            return 0
        
        Ref = self.Ref.currentText()
        if self.Ref_library.currentIndex() == 0:
            Backend = "REFPROP"
        else:
            Backend = "HEOS"
        AS = get_AS(Backend,Ref,None)
        if AS[0]:
            self.AS = AS[1]
        else:
            self.raise_error_meesage("Failed to use REFPROP!")
            return 0
        return 1
    
    def calculate(self):
        validate = self.validate()
        succeeded = False
        if validate == 1:
            try:
                Ref = self.Ref.currentText()
                Cycle_Mode = self.Cycle_Mode.currentIndex()
                Capacity = power_unit_converter(self.Cycle_Capacity.text(),self.Cycle_Capacity_unit.currentIndex())
                N_tubes = self.N_tubes.value()
                SC = temperature_diff_unit_converter(self.Subcooling.text(),self.Subcooling_unit.currentIndex())
                SH = temperature_diff_unit_converter(self.Superheat.text(),self.Superheat_unit.currentIndex())
                Compressor_eff = self.Compressor_isen_eff.value()/100
                corr = self.Correlation.currentIndex()
                D = length_unit_converter(self.Diameter.text(),self.Diameter_unit.currentIndex())
                
                AS = self.AS
                
                if self.Condensing_T_label.isChecked():
                    Tcond = temperature_unit_converter(self.Condensing_T.text(),self.Condensing_T_unit.currentIndex())
                elif self.Condensing_P_label.isChecked():
                    Pcond = pressure_unit_converter(self.Condensing_P.text(),self.Condensing_P_unit.currentIndex())
                    AS.update(CP.PQ_INPUTS,Pcond,1.0)
                    Tcond = AS.T()

                if self.Evaporating_T_label.isChecked():
                    Tevap = temperature_unit_converter(self.Evaporating_T.text(),self.Evaporating_T_unit.currentIndex())
                elif self.Evaporating_P_label.isChecked():
                    Pevap = pressure_unit_converter(self.Evaporating_P.text(),self.Evaporating_P_unit.currentIndex())
                    AS.update(CP.PQ_INPUTS,Pevap,1.0)
                    Tevap = AS.T()
                    
                AS.update(CP.QT_INPUTS,1.0,Tevap)
                P1 = AS.p()
                AS.update(CP.PT_INPUTS,P1,Tevap+SH)
                h1 = AS.hmass()
                s1 = AS.smass()
                AS.update(CP.QT_INPUTS,1.0,Tcond)
                P2 = AS.p()
                AS.update(CP.PSmass_INPUTS,P2,s1)
                h2s = AS.hmass()
                h2 = h1 + (h2s - h1) / Compressor_eff
                AS.update(CP.QT_INPUTS,0.0,Tcond)
                P3 = AS.p()
                AS.update(CP.PT_INPUTS,P3,Tcond-SC)
                h3 = h4 = AS.hmass()
                AS.update(CP.QT_INPUTS,0.0,Tevap)
                P4 = AS.p()
                
                if Cycle_Mode == 0:
                    mdot = Capacity / (h1 - h4)
                else:
                    mdot = Capacity / (h2 - h3)

                Capillary = CapillaryClass()
                Capillary.name = ""
                Capillary.AS = AS
                Capillary.D = D
                Capillary.D_liquid = 8*D
                Capillary.DP_converged = 1.0
                Capillary.DT_2phase = 0.5
                Capillary.Ntubes = N_tubes
                Capillary.STD_sh = SH
                if corr == 0:    
                    Capillary.method = "choi"
                elif corr == 1:    
                    Capillary.method = "wolf"
                elif corr == 2:    
                    Capillary.method = "wolf_physics"
                elif corr == 3:
                    Capillary.method = "wolf_pate"
                elif corr == 4:
                    Capillary.method = "rasti"
                    
                Capillary.Pin_r = P3
                Capillary.hin_r = h3
                Capillary.Pout_r_target = P4
                Capillary.Ref = Ref
                def objective(L):
                    L = float(L)
                    Capillary.L = L
                    Capillary.Calculate()
                    return mdot - Capillary.mdot_r
                
                Capillary_length = least_squares(objective,0.1,bounds=(0,np.inf))["x"]
                error = objective(float(Capillary_length))

                if abs(error) > 0.0001:
                    raise
                Capillary_length = length_unit_converter(Capillary_length,self.Length_unit.currentIndex(),True)
                succeeded = True
            except:
                import traceback
                print(traceback.format_exc())
                succeeded = False
            
            if succeeded:
                self.raise_success_meesage("Capillary tube length is: "+ "%.5g" % float(Capillary_length)+" "+self.Length_unit.currentText())
            else:
                self.raise_error_meesage("Error calculating capillary tube length.")
                
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
        window = Capillary_sizing_window()
        window.show()
        app.exec_()
    try:
        main()
    except Exception as why:
        print(why)
