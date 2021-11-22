from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
import os, sys
import CoolProp as CP
from unit_conversion import *
from GUI_functions import load_refrigerant_list
from GUI_functions import write_comp_xml
import appdirs
import datetime
FROM_Compressor_rating_to_Physics,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Compressor_rating_to_physics.ui"))
import numpy as np
import pyperclip
from backend.Functions import get_AS

class values():
    pass

class Compressor_rating_to_physics_Window(QDialog, FROM_Compressor_rating_to_Physics):
    def __init__(self, parent=None):
        super(Compressor_rating_to_physics_Window, self).__init__(parent)
        self.setupUi(self)
                
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
        self.Vdot.setValidator(only_number)
        
        # hide outputs tab
        self.tabWidget.setTabEnabled(1,False)
        
        # create connections
        self.Convert_button.clicked.connect(self.convert_clicked)
        self.N_points.valueChanged.connect(self.refresh_inputs_rows)
        self.Create_compressor_button.clicked.connect(self.compressor_creator)
        self.vol_poly_copy.clicked.connect(self.copy_vol_poly)
        self.isen_poly_copy.clicked.connect(self.copy_isen_poly)

        # initially load REFPROP
        self.load_REFPROP()
        
        # intially create units row
        self.setup_rating_table()

    def copy_vol_poly(self):
        pyperclip.copy(self.Vol_poly.text())
        
    def copy_isen_poly(self):
        pyperclip.copy(self.isen_poly.text())

    def setup_rating_table(self):
        self.Rating_table.setRowCount(2)
        units = []
        self.unit_combos = []
        def create_dropbox(items,function):
            combo = QComboBox()
            combo.addItems(items)
            combo.function = function
            self.unit_combos.append(combo)
            return combo
        self.Rating_table.setHorizontalHeaderLabels([" mode ",
                                                     " Condensing \n Temperature ",
                                                     " Evaporating \n Temperature ",
                                                     " Condenser \n Subcooling ",
                                                     " Evaporator \n Superheat ",
                                                     " Rating \n Capacity ",
                                                     " Rating \n Power "])
        units.append(QLabel(""))
        units.append(create_dropbox(["C","K","F"],temperature_unit_converter))
        units.append(create_dropbox(["C","K","F"],temperature_unit_converter))
        units.append(create_dropbox(["C","F"],temperature_diff_unit_converter))
        units.append(create_dropbox(["C","F"],temperature_diff_unit_converter))
        units.append(create_dropbox(["W","Btu/hr"],power_unit_converter))
        units.append(create_dropbox(["W"],None))
        for i,unit in enumerate(units):
            if i==5: # default capacity unit is btu/hr
                unit.setCurrentIndex(1)
            self.Rating_table.setCellWidget(0,i,unit)
        self.mode_combos = []
        self.refresh_inputs_rows()
        self.Rating_table.resizeColumnsToContents()
        class MyDelegate(QItemDelegate):
            def createEditor(self, parent, option, index):
                return_object = QLineEdit(parent)
                only_number_negative = QRegExpValidator(QRegExp("[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)"))
                return_object.setValidator(only_number_negative)
                return return_object
        delegate = MyDelegate()
        self.Rating_table.setItemDelegate(delegate)

        # initial values for the table
        for i,value in enumerate([54.5,7.2,8.4,27.8]):
            self.Rating_table.setItem(1,i+1,QTableWidgetItem(str(value)))

    def get_rating_table_values(self):
        try:
            N = self.Rating_table.rowCount()
            M = self.Rating_table.columnCount()
            Data = np.zeros([N-1,M],dtype=float)
            Data[:,0] = [combo.currentIndex() for combo in self.mode_combos]
            for i in range(1,N):
                for k in range(1,M):
                    combo = self.unit_combos[k-1]
                    function = combo.function
                    if function != None:
                        Data[i-1,k] = function(self.Rating_table.item(i,k).text().replace(" ",""),combo.currentIndex())
                    else:
                        Data[i-1,k] = float(self.Rating_table.item(i,k).text().replace(" ",""))
            if np.any(Data[:,2]<=0):
                self.raise_error_meesage("Condenser subcooling must be positive number!")
                return (0,)                
            if np.any(Data[:,3]<=0):
                self.raise_error_meesage("Evaproator superheat must be positive number!")
                return (0,)                
            if np.any(Data[:,4]<=0):
                self.raise_error_meesage("Rating capacity must be positive number!")
                return (0,)                
            if np.any(Data[:,5]<=0):
                self.raise_error_meesage("Rating power must be positive number!")
                return (0,)
            return (1,Data)
        except:
            import traceback
            print(traceback.format_exc())
            self.raise_error_meesage("Failed to obtain values from rating values table!")
            return (0,)

    def refresh_inputs_rows(self):
        N_points = self.N_points.value()
        self.Rating_table.setRowCount(N_points+1)
        self.Rating_table.setVerticalHeaderLabels(["Units"]+[str(i+1) for i in range(self.Rating_table.rowCount())])
        if len(self.mode_combos) > N_points:
            del(self.mode_combos[N_points:])
        else:
            for i in range(len(self.mode_combos)+1,N_points+1):
                combo = QComboBox()
                combo.addItems(["Cooling","Heating"])
                self.mode_combos.append(combo)
                self.Rating_table.setCellWidget(i,0,combo)
                # initial values for the table
                for j,value in enumerate([54.5,7.2,8.4,27.8]):
                    self.Rating_table.setItem(i,j+1,QTableWidgetItem(str(value)))
        self.volumetric_degree.setValue(max(N_points-2,0))
        self.isentropic_degree.setValue(max(N_points-2,0))

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
            return (0,)

        if self.Vdot.text() in ["","-","."]:
            self.raise_error_meesage("Please enter compressor volumetric displacement per revolution")
            return (0,)

        if self.Ref_library.currentIndex() == 0:
            Backend = "REFPROP"
        else:
            Backend = "HEOS"
        AS = get_AS(Backend,self.Comp_ref.currentText(),None)
        if AS[0]:
            self.AS = AS[1]
        else:        
            self.raise_error_meesage("Failed to use REFPROP!")
            return (0,)

        try:
            Speed = float(self.Speed.text())
        except:
            self.raise_error_meesage("Failed to read compressor speed!")
            return (0,)

        try:
            Vdot = float(self.Vdot.text())
        except:
            self.raise_error_meesage("Failed to read compressor volumetric displacement per revolution!")
            return (0,)
            
        return self.get_rating_table_values()
    
    def convert_clicked(self):
        validate = self.validate_convert()
        if validate[0] == 1:
            AS = self.AS
            Data = validate[1]
            Vdot = volume_unit_converter(self.Vdot.text(),self.Vdot_unit.currentIndex())
            Speed = float(self.Speed.text())
            results = []
            for i,row in enumerate(Data):
                try:
                    Cycle_Mode = row[0]
                    Tcond = row[1]
                    Tevap = row[2]
                    SC = row[3]
                    SH = row[4]
                    Capacity = row[5]
                    Power = row[6]
                    AS.update(CP.QT_INPUTS,1.0,Tevap)
                    P1 = AS.p()
                    AS.update(CP.PT_INPUTS,P1,Tevap+SH)
                    h1 = AS.hmass()
                    s1 = AS.smass()
                    rho1 = AS.rhomass() #[kg/m^3]
                    AS.update(CP.QT_INPUTS,1.0,Tcond)
                    P2 = AS.p()
                    AS.update(CP.PSmass_INPUTS,P2,s1)
                    h2s = AS.hmass()
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
                    PR = P2 / P1
                    isen_eff = mdot * (h2s - h1) / (Power)
                    vol_eff = mdot / (Vdot * Speed / 60 * rho1)
                    results.append([PR,isen_eff,vol_eff])
                    
                except:
                    import traceback
                    print(traceback.format_exc())
                    self.raise_error_meesage("Failed to convert case"+str(i+1))
                    results.append([np.nan,np.nan,np.nan])
            
            results = np.array(results)
            self.set_results_table(results[:,1:])
            results = results[~np.isnan(results).any(axis=1)]
            if (len(results)-self.volumetric_degree.value() < 1):
                self.raise_error_meesage("Failed to generate volumetric efficiency polynomial. Number of succeeded point must be higher than polynomial degree.")
                self.Vol_poly.setText("")
                vol_cond = False
            else:
                vol_cond = True
                # regression for volumetric efficiency model
                coeffs_volum = np.flip(np.polyfit(results[:,0], results[:,2],self.volumetric_degree.value()))
                    
                volum_exp = "%.5g" % coeffs_volum[0]
                if len(coeffs_volum) > 1:
                    for j,i in enumerate(coeffs_volum[1:]):
                        if i >= 0:
                            volum_exp += " + %.5g" % np.abs(i) + "*PR**"+str(j+1)
                        else:
                            volum_exp += " - %.5g" % np.abs(i) + "*PR**"+str(j+1)
                self.Vol_poly.setText(volum_exp.replace("**","^"))
                
            if (len(results)-self.isentropic_degree.value() < 1):
                self.raise_error_meesage("Failed to generate isentropic efficiency polynomial. Number of succeeded point must be higher than polynomial degree.")
                self.isen_poly.setText("")
                isen_cond = False
            else:
                isen_cond = True
                # regression for isentropic efficiency model
                coeffs_isen = np.flip(np.polyfit(results[:,0], results[:,1],self.isentropic_degree.value()))
                    
                isen_exp = "%.5g" % coeffs_isen[0]
                if len(coeffs_isen) > 1:
                    for j,i in enumerate(coeffs_isen[1:]):
                        if i >= 0:
                            isen_exp += " + %.5g" % np.abs(i) + "*PR**"+str(j+1)
                        else:
                            isen_exp += " - %.5g" % np.abs(i) + "*PR**"+str(j+1)
                self.isen_poly.setText(isen_exp.replace("**","^"))

            if isen_cond and vol_cond:
                self.Comp_name.setEnabled(True)
                self.Create_compressor_button.setEnabled(True)                
                comp = values()
                comp.Ref = self.Comp_ref.currentText()
                comp.Comp_vol = Vdot
                comp.Comp_speed = Speed
                comp.Comp_fp = 0.0
                comp.Comp_elec_eff = 1.0
                comp.Comp_ratio_M = 1.0
                comp.Comp_ratio_P = 1.0
                comp.Comp_model = "physics"
                comp.isentropic_exp = isen_exp
                comp.vol_exp = volum_exp
                self.Compressor = comp
            else:
                self.Comp_name.setEnabled(False)
                self.Create_compressor_button.setEnabled(False)                

            self.tabWidget.setTabEnabled(1,True)
            self.tabWidget.setCurrentIndex(1)
        else:
            if hasattr(self,"Compressor"):
                delattr(self,"Compressor")
            self.tabWidget.setTabEnabled(0,True)
            self.tabWidget.setCurrentIndex(0)

    def compressor_creator(self):
        file_name = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '.comp'
        path = self.database_path + file_name
        self.Compressor.Comp_name = self.Comp_name.text()
        result = write_comp_xml(self.Compressor,path)        
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

    def set_results_table(self,results):
        self.results_table.resizeColumnsToContents()
        self.results_table.setRowCount(len(results))
        for i,row in enumerate(results):
            if (row[0] != np.nan):
                value = float(row[0])*100
                self.results_table.setItem(i,0,QTableWidgetItem("%.4g" % value))
            else:
                self.results_table.setItem(i,0,QTableWidgetItem("Failed"))

            if (row[1] != np.nan):
                value = float(row[1])*100
                self.results_table.setItem(i,1,QTableWidgetItem("%.4g" % value))
            else:
                self.results_table.setItem(i,1,QTableWidgetItem("Failed"))

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
        window = Compressor_rating_to_physics_Window()
        window.show()
        app.exec_()
    try:
        main()
    except Exception as why:
        print(why)
