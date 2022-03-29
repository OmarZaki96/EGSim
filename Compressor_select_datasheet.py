from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
import os, sys
from GUI_functions import *
from unit_conversion import *
import appdirs
import pandas as pd
import numpy as np
import shutil
import datetime
from backend.Functions import get_AS
import CoolProp as CP

FROM_COMPRESSOR_SELECT_MAIN,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Compressor_select_datasheet.ui"))
FROM_COMPRESSOR_AVAILABLE_TEST_COND,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Compressor_available_test_conditions.ui"))

class values():
    pass

class Compressor_select_datasheet_window(QDialog, FROM_COMPRESSOR_SELECT_MAIN):
    def __init__(self, parent=None):
        # first UI
        super(Compressor_select_datasheet_window, self).__init__(parent)
        self.setupUi(self)
        
        
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
            self.ref_list = ref_list[1]        

        # this will load database at the beginning
        self.load_database()
        
        self.database_path = appdirs.user_data_dir("EGSim")+"/Database/"
        
        self.parent = parent

        # connections
        self.import_button.clicked.connect(self.import_database)
        self.export_button.clicked.connect(self.export_database)
        self.available_test_cond_button.clicked.connect(self.show_available_window)
        self.add_button.clicked.connect(self.select_comp)
        self.manufacturer.currentIndexChanged.connect(self.populate_table)
        self.ref.currentIndexChanged.connect(self.populate_table)
        self.freq.currentIndexChanged.connect(self.populate_table)
        self.capacity.currentIndexChanged.connect(self.populate_table)
        self.speed.currentIndexChanged.connect(self.populate_table)
        self.op_cond.currentIndexChanged.connect(self.populate_table)
        self.test_cond.currentIndexChanged.connect(self.populate_table)
        self.search_keyword.textEdited.connect(self.populate_table)
        
    def load_database(self,path=None):
        if path == None:
            imported = False
            path = appdirs.user_data_dir("EGSim")+r"/Compressors.csv"
        else:
            imported = True

        if os.path.exists(path):
            try:
                self.compressor_data = pd.read_csv(path,usecols=["Manufacturer", "Model", "Refrigerant", "Operating Condition", "Test Condition" ,"Displacement Volume", "Capacity", "Power", "COP", "Source", "Minimum Voltage", "Maximum Voltage", "Frequency", "Speed Type", "Speed", "Comments"],dtype={"Manufacturer":str, "Model":str, "Refrigerant":str, "Operating Condition":str, "Test Condition":str ,"Displacement Volume":object, "Capacity":object, "Power":object, "COP":object, "Source":str, "Minimum Voltage":object, "Maximum Voltage":object, "Frequency":object,"Speed Type":str, "Speed":object, "Comments":str})
                cols = ["Displacement Volume", "Capacity", "Power", "COP","Minimum Voltage", "Maximum Voltage","Speed"]
                self.compressor_data[cols] = self.compressor_data[cols].apply(lambda x: pd.to_numeric(x, errors='coerce'))
                self.compressor_data['Test Condition'] = self.compressor_data['Test Condition'].str.strip()
                self.compressor_data['Test Condition'] = self.compressor_data['Test Condition'].str.lower()
                self.compressor_data = self.compressor_data[self.compressor_data['Test Condition'].isin(["ash","hp","eer","hpd","ref","gx","seer60","ari"])]
                self.compressor_data = self.compressor_data[self.compressor_data['Refrigerant'].isin(self.ref_list[:,0])]
                self.compressor_data['Minimum Voltage'] = self.compressor_data['Minimum Voltage'].fillna("-")
                self.compressor_data['Maximum Voltage'] = self.compressor_data['Maximum Voltage'].fillna("-")
                self.compressor_data['Frequency'] = self.compressor_data['Frequency'].fillna("-")
                self.compressor_data = self.compressor_data[self.compressor_data['Displacement Volume'].notna()]
                self.compressor_data = self.compressor_data[self.compressor_data['Capacity'].notna()]
                self.compressor_data = self.compressor_data[self.compressor_data['Power'].notna()]
                self.compressor_data = self.compressor_data[self.compressor_data['COP'].notna()]
                self.compressor_data = self.compressor_data[self.compressor_data['Speed'].notna()]
                self.compressor_data.reset_index(drop=True)
                result = True
            except:
                import traceback
                print(traceback.format_exc())
                if not imported:
                    self.compressor_data = pd.DataFrame(columns = ["Manufacturer", "Model", "Refrigerant", "Operating Condition", "Test Condition" ,"Displacement Volume", "Capacity", "Power", "COP", "Source", "Minimum Voltage", "Maximum Voltage", "Frequency", "Speed Type", "Speed", "Comments"])
                result = False
        else:
            if not imported:
                self.compressor_data = pd.DataFrame(columns = ["Manufacturer", "Model", "Refrigerant", "Operating Condition", "Test Condition" ,"Displacement Volume", "Capacity", "Power", "COP", "Source", "Minimum Voltage", "Maximum Voltage", "Frequency", "Speed Type", "Speed", "Comments"])
            result = False
        if not imported or (imported and result):
            self.populate_filters()
            self.populate_table()
        return result

    def populate_filters(self):
        manufacturers = ['Any']+[str(i) for i in set(self.compressor_data['Manufacturer'])]
        refrigerant = ['Any']+[str(i) for i in set(self.compressor_data['Refrigerant'])]
        operating_conditions = ['Any']+[str(i) for i in set(self.compressor_data['Operating Condition'])]
        test_conditions = ['Any']+[str(i) for i in set(self.compressor_data['Test Condition'])]
        frequencies = ['Any']+[str(i) for i in set(self.compressor_data['Frequency'])]
        speeds = ['Any']+[str(i) for i in set(self.compressor_data['Speed Type'])]
        capacities = ['Any','Below 6000 Btu/hr','6000 to 12000 Btu/hr','12000 to 18000 Btu/hr','18000 to 24000 Btu/hr','Above 24000 Btu/hr']        
        self.manufacturer.clear()
        self.manufacturer.addItems(manufacturers)
        self.manufacturer.setCurrentIndex(0)
        self.ref.clear()
        self.ref.addItems(refrigerant)
        self.ref.setCurrentIndex(0)
        self.op_cond.clear()
        self.op_cond.addItems(operating_conditions)
        self.op_cond.setCurrentIndex(0)
        self.test_cond.clear()
        self.test_cond.addItems(test_conditions)
        self.test_cond.setCurrentIndex(0)
        self.freq.clear()
        self.freq.addItems(frequencies)
        self.freq.setCurrentIndex(0)
        self.speed.clear()
        self.speed.addItems(speeds)
        self.speed.setCurrentIndex(0)
        self.capacity.clear()
        self.capacity.addItems(capacities)
        self.capacity.setCurrentIndex(0)

    def import_database(self):
        quit_msg = "THIS WILL DELETE CURRENT DATABASE. Are you sure?"
        reply = QMessageBox.warning(self, 'Message', 
                         quit_msg, QMessageBox.Yes, QMessageBox.No)
    
        if reply == QMessageBox.Yes:
            path = QFileDialog.getOpenFileName(self, 'Open Database file',directory=load_last_location(),filter="Database file (*.csv);;All files (*.*)")[0]
            if path != "":
                save_last_location(path)
                if self.load_database(path):
                    old_path = appdirs.user_data_dir("EGSim")+r"/Compressors.csv"
                    if os.path.exists(old_path):                    
                        os.remove(old_path)
                    shutil.copyfile(path,old_path)
                    self.raise_information_message("Database was imported successfully")
                    self.populate_table()
                else:
                    self.raise_error_message("Failed to import database file, please review the file again")

    def export_database(self):
        path = QFileDialog.getSaveFileName(self, 'Save Database file',directory=load_last_location(),filter="Database file (*.csv);;All files (*.*)")[0]
        if path != "":
            save_last_location(path)
            old_path = appdirs.user_data_dir("EGSim")+r"/Compressors.csv"
            if os.path.exists(old_path):
                shutil.copyfile(old_path,path)
                self.raise_information_message("Database was exported successfully")
            else:
                raise
        else:
            self.raise_error_message("Failed to export database file, please review the file again")

    def populate_table(self):
        self.Table.clear()
        compressors = self.compressor_data.copy()
        self.Table.setColumnCount(len(compressors.columns))
        self.Table.setHorizontalHeaderLabels(compressors.columns)
        self.Table.setSelectionBehavior(QAbstractItemView.SelectRows);
        self.Table.setEditTriggers(QAbstractItemView.NoEditTriggers);
        
        index = compressors.index.to_numpy()+1
        
        if self.manufacturer.currentIndex() > 0:
            rows = compressors['Manufacturer'] == self.manufacturer.currentText()
            compressors = compressors[rows]
            index = index[rows]

        if self.ref.currentIndex() > 0:
            rows = compressors["Refrigerant"] == self.ref.currentText()
            compressors = compressors[rows]
            index = index[rows]

        if self.freq.currentIndex() > 0:
            rows = compressors["Frequency"] == self.freq.currentText()
            compressors = compressors[rows]
            index = index[rows]

        if self.capacity.currentIndex() > 0:
            if self.capacity.currentIndex() == 1:
                minimum = 0
                maximum = 6000
            elif self.capacity.currentIndex() == 2:
                minimum = 6000
                maximum = 12000
            elif self.capacity.currentIndex() == 3:
                minimum = 12000
                maximum = 18000
            elif self.capacity.currentIndex() == 4:
                minimum = 18000
                maximum = 24000
            elif self.capacity.currentIndex() == 5:
                minimum = 24000
                maximum = np.Inf
            rows = (compressors["Capacity"] >= minimum) & (compressors["Capacity"] <= maximum)
            compressors = compressors[rows]
            index = index[rows]

        if self.speed.currentIndex() > 0:
            rows = compressors["Speed Type"] == self.speed.currentText()
            compressors = compressors[rows]
            index = index[rows]

        if self.op_cond.currentIndex() > 0:
            rows = compressors["Operating Condition"] == self.op_cond.currentText()
            compressors = compressors[rows]
            index = index[rows]

        if self.test_cond.currentIndex() > 0:
            rows = compressors["Test Condition"] == self.test_cond.currentText()
            compressors = compressors[rows]
            index = index[rows]
        
        if self.search_keyword.text() != "":
            rows = np.array(np.sum(compressors.apply(lambda col: col.str.contains(self.search_keyword.text(), na=False,case=False), axis=1),axis=1),dtype=bool)
            compressors = compressors[rows]
            index = index[rows]
        
        compressors = compressors.to_numpy()
        self.Table.setRowCount(len(compressors)+1)
        
        for i in range(len(compressors)):
            self.Table.setItem(i+1,0,QTableWidgetItem(index[i]))
            for j in range(len(compressors[0,1:])):
                try:
                    value = float(compressors[i,j])
                    value = "%.5g" % value
                except:
                    value = compressors[i,j]
                self.Table.setItem(i+1,j,QTableWidgetItem(value))
        self.Table.setVerticalHeaderLabels([""]+[str(i) for i in index])

        units = ["-","-","-","-","cm^3","Btu/hr","W","Btu/hr/W","-","V","V","Hz","-","-","RPM","-"]
        for j in range(len(units)):
            item = QTableWidgetItem(units[j])
            item.setFlags(item.flags() ^ (Qt.ItemIsSelectable | Qt.ItemIsEnabled))
            self.Table.setItem(0,j,item)

        header = self.Table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)

    def select_comp(self):
        model = self.Table.selectionModel()
        selected_rows = set([cell.row() for cell in self.Table.selectedIndexes()])
        if len(selected_rows) > 0:
            try:
                selected_compressors = [int(self.Table.verticalHeaderItem(r).text())-1 for r in selected_rows]
                compressors = self.compressor_data.loc[selected_compressors]
                error = False
                for i,compressor in compressors.iterrows():
                    try:
                        name = str(compressor["Manufacturer"])+" "+str(compressor["Model"])+" "+str(compressor["Refrigerant"])+" "+str(round(compressor["Capacity"]/12000,2))+" TR"
                        if compressor["Test Condition"] == "ash":
                            Tcond = 54.4
                            Tevap = 7.2
                            SC = 8.3
                            Suction_T = 35
    
                        elif compressor["Test Condition"] == "hp":
                            Tcond = 46
                            Tevap = 7.2
                            SC = 8.3
                            Suction_T = 18.3
    
                        elif compressor["Test Condition"] == "eer":
                            Tcond = 45
                            Tevap = 12
                            SC = 5
                            Suction_T = 24
    
                        elif compressor["Test Condition"] == "hpd":
                            Tcond = 70
                            Tevap = 25
                            SC = 9
                            Suction_T = 35
    
                        elif compressor["Test Condition"] == "ref":
                            Tcond = 54.4
                            Tevap = -23.3
                            SC = 22.2
                            Suction_T = 18.3
    
                        elif compressor["Test Condition"] == "gx":
                            Tcond = 46
                            Tevap = 10
                            SC = 5
                            Suction_T = 18

                        elif compressor["Test Condition"] == "ari":
                            Tcond = 54.4
                            Tevap = 7.2
                            SC = 8.3
                            Suction_T = 18.3

                        elif compressor["Test Condition"] == "seer60":
                            Tcond = 42.3
                            Tevap = 2.7
                            SC = 8
                            Suction_T = 12.8
                                            
                        Tcond += 273.15
                        Tevap += 273.15
                        Suction_T += 273.15
                        
                        Capacity = float(compressor["Capacity"])/12000*3517
                        Power = float(compressor["Power"])
                        Ref = compressor["Refrigerant"]
                        Vdot = float(compressor["Displacement Volume"]) * 1E-6
                        Speed = float(compressor["Speed"])
                        AS = get_AS("REFPROP",Ref,None)
                        
                        if AS[0]:
                            AS = AS[1]
                        else:
                            AS = get_AS("HEOS",Ref,None)[1]
    
                        AS.update(CP.QT_INPUTS,1.0,Tevap)
                        P1 = AS.p()
                        AS.update(CP.PT_INPUTS,P1,Suction_T)
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
                        
                        mdot = Capacity / (h1 - h4)
    
                        PR = P2 / P1
                        isen_eff = mdot * (h2s - h1) / (Power)
                        vol_eff = mdot / (Vdot * Speed / 60 * rho1)
                        
                        Comp = ["",values()]
                        file_name = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '.comp'
                        path = self.database_path + file_name
                        Comp[0] = file_name
                        Comp[1].Comp_name = name
                        Comp[1].Ref = Ref
                        Comp[1].Comp_vol = Vdot
                        Comp[1].Comp_speed = Speed
                        Comp[1].Comp_fp = "0.0"
                        Comp[1].Comp_elec_eff = 1
                        Comp[1].Comp_ratio_M = "1"
                        Comp[1].Comp_ratio_P = "1"
                        Comp[1].Comp_model = "physics"
                        Comp[1].isentropic_exp = str(isen_eff)
                        Comp[1].vol_exp = str(vol_eff)
                        Comp[1].F_factor = 0.75
                        Comp[1].SH_type = 1
                        Comp[1].Suction_Ref = Suction_T
                        result = write_comp_xml(Comp[1],path)
                        result = False
                        
                    if not result:
                        error = True
                if not error:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("Compressors were added successfully")
                    msg.setWindowTitle("Compressor added")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                else:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("Some compressors could not be added")
                    msg.setWindowTitle("Compressors were not added!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()                    
            except:
                self.raise_error_message("Failed to add compressors")
        else:
            self.raise_error_message("Please select a compressor first")
            
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
        msg.setWindowTitle("Information!")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        
    def show_available_window(self):
        available_window = Compressor_available_test_conds_window(self)
        available_window.exec_()
    
class Compressor_available_test_conds_window(QDialog, FROM_COMPRESSOR_AVAILABLE_TEST_COND):
    def __init__(self, parent=None):
        # first UI
        super(Compressor_available_test_conds_window, self).__init__(parent)
        self.setupUi(self)
        header = self.Table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)


if __name__ == '__main__':
    def main():
        app=QApplication(sys.argv)
        app.setStyle('Fusion')
        window = Compressor_select_datasheet_window()
        window.show()
        app.exec_()
    main()
