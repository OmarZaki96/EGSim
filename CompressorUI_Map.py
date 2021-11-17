from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
import os, sys, csv, io
from GUI_functions import load_compressor_map_file
from unit_conversion import temperature_diff_unit_converter
from CompressorMap_Coefficients import Create_coefficients
from unit_conversion import *

FROM_Compressor_Map,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Compressor_define_Map.ui"))
FROM_Compressor_Map_Widget,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Compressor_define_Map_widget.ui"))

class values():
    pass

class Compressor_Map(QDialog, FROM_Compressor_Map):
    def __init__(self, parent=None):        
        super(Compressor_Map, self).__init__(parent)
        self.setupUi(self)
        
        # creating maps holder object
        self.M_array = [0]
        self.P_array = [0]
        
        # connections
        self.Comp_Map_cancel_button.clicked.connect(self.cancel_button)
        self.Comp_Map_N_speeds.valueChanged.connect(self.Map_num_speed_change)
        self.Comp_Map_ok_button.clicked.connect(self.ok_button)
        self.Comp_Map_std_sh_radio.toggled.connect(self.standard_changed)
        self.Comp_Map_std_suction_radio.toggled.connect(self.standard_changed)
        
        # validators
        only_number = QRegExpValidator(QRegExp("(([0-9]+\.[0-9]*[1-9][0-9]*)|([0-9]*[1-9][0-9]*\.[0-9]+)|([0-9]*[1-9][0-9]*))"))
        self.Comp_Map_std_sh.setValidator(only_number)
        self.Comp_Map_std_suction.setValidator(only_number)
        self.Comp_Map_F.setValidator(only_number)
        
        # populate first tab
        num_tabs = 1
        TabPage = Compressor_Map_Widget(self)
        TabPage.installEventFilter(self)
        TabPage.Speed.setValidator(only_number)
        setattr(self,"Comp_Map_map_M_table_"+str(num_tabs),TabPage.map_M_table)
        setattr(self,"Comp_Map_map_P_table_"+str(num_tabs),TabPage.map_P_table)
        setattr(self,"Comp_Map_speed_value_"+str(num_tabs),TabPage.Speed)
        setattr(self,"Comp_Map_tabs_"+str(num_tabs),TabPage.Map_Tabs)
        self.Comp_Map_map_tabs.addTab(TabPage,"Speed "+str(num_tabs))
        
        self.standard_changed()
        
        # intially load images
        def images_loader(path,var_name,size):
            try:
                photo = QPixmap(path)
                photo = photo.scaledToWidth(size)
                setattr(self,var_name,photo)
            except:
                pass
        
        images_loader("photos/Comp_Map_Indication.png",'Comp_Map_Indication',313)
        
        # intially populate available images
        if hasattr(self,"Comp_Map_Indication"):
            self.file_format_image.setPixmap(self.Comp_Map_Indication)
        else:
            self.file_format_image.setText("Compressor map format Demonistration photo")
        

    def eventFilter(self, source, event):
        if isinstance(source,Compressor_Map_Widget):
            if (event.type() == QEvent.KeyPress and
                event.matches(QKeySequence.Copy)):
                tab_number  =  source.Map_Tabs.currentIndex()
                source.copySelection(tab_number+1)
                return True
            return super(Compressor_Map, self).eventFilter(source, event)
    
    def standard_changed(self):
        if self.Comp_Map_std_sh_radio.isChecked():
            self.Comp_Map_std_sh.setEnabled(True)
            self.Comp_Map_std_sh_unit.setEnabled(True)
            self.Comp_Map_std_suction.setEnabled(False)
            self.Comp_Map_std_suction_unit.setEnabled(False)
        elif self.Comp_Map_std_suction_radio.isChecked():
            self.Comp_Map_std_sh.setEnabled(False)
            self.Comp_Map_std_sh_unit.setEnabled(False)
            self.Comp_Map_std_suction.setEnabled(True)
            self.Comp_Map_std_suction_unit.setEnabled(True)
        
    def cancel_button(self):
        self.close()
    
    def load_fields(self,map_window):
        self.Comp_Map_Tcond_unit.setCurrentIndex(map_window.Tcond_unit)
        self.Comp_Map_Tevap_unit.setCurrentIndex(map_window.Tevap_unit)
        self.Comp_Map_M_unit.setCurrentIndex(map_window.M_unit)
        self.Comp_Map_N_speeds.setValue(len(map_window.Speeds))
        self.Map_num_speed_change()
        if map_window.std_type == 0:
            self.Comp_Map_std_sh_radio.setChecked(True)
            self.Comp_Map_std_sh.setText(str(round(map_window.std_sh*9/5,6)))
        elif map_window.std_type == 1:
            self.Comp_Map_std_suction_radio.setChecked(True)
            self.Comp_Map_std_suction.setText(str(round(temperature_unit_converter(map_window.std_suction,0,True),6)))
        self.Comp_Map_F.setText(str(map_window.F_value))
        self.M_array = map_window.M_array
        self.P_array = map_window.P_array
        for i, speed in enumerate(map_window.Speeds):
            getattr(self,"Comp_Map_speed_value_"+str(i+1)).setText(str(speed))
            self.load_map_table(map_window.M_array[i],i+1,0)
            self.load_map_table(map_window.P_array[i],i+1,1)
        
    def validate(self):
        num_speeds = int(self.Comp_Map_N_speeds.value())
        for M in self.M_array:
            if isinstance(M,int):
                return 0
        for P in self.P_array:
            if isinstance(P,int):
                return 0
        if self.Comp_Map_std_sh_radio.isChecked():
            if self.Comp_Map_std_sh.text() in ["","-","."]:
                return 0
            
        elif self.Comp_Map_std_suction_radio.isChecked():
            if self.Comp_Map_std_suction.text() in ["","-","."]:
                return 0
        if self.Comp_Map_F.text() in ["","-","."]:
            return 0
        for i in range(num_speeds):
            if getattr(self,"Comp_Map_speed_value_"+str(i+1)).text() in ["","-","."]:
                return 0
        return 1
    
    def load_map_table(self,map_result,current_speed,current_tab):
        if current_tab == 0:
            table = getattr(self,"Comp_Map_map_M_table_"+str(current_speed))
        elif current_tab == 1:
            table = getattr(self,"Comp_Map_map_P_table_"+str(current_speed))
        table.setRowCount(len(map_result))
        for i,row in enumerate(map_result):
            table.setItem(i,0,QTableWidgetItem(str(row[0])))
            table.setItem(i,1,QTableWidgetItem(str(row[1])))
            table.setItem(i,2,QTableWidgetItem(str(row[2])))
    
    def load_map(self):
        path = QFileDialog.getOpenFileName(self, 'Open Compressor Map file',filter="Compressor Map file (*.csv);;All files (*.*)")[0]
        if path != "":
            result = load_compressor_map_file(path)
            if result[0]:
                try:
                    map_result = result[1]
                    current_speed = self.Comp_Map_map_tabs.currentIndex() + 1
                    current_tab = getattr(self,"Comp_Map_tabs_"+str(current_speed)).currentIndex()
                    self.load_map_table(map_result,current_speed,current_tab)
                    if current_tab == 0:
                        self.M_array[current_speed-1] = map_result
                    elif current_tab == 1:
                        self.P_array[current_speed-1] = map_result
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("The file was loaded successfully")
                    msg.setWindowTitle("Success!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                except:
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
    
    def ok_button(self):
        if self.validate():
            map_window = values()
            map_window.Tcond_unit = self.Comp_Map_Tcond_unit.currentIndex()
            map_window.Tevap_unit = self.Comp_Map_Tevap_unit.currentIndex()
            map_window.M_unit = self.Comp_Map_M_unit.currentIndex()
            if self.Comp_Map_std_sh_radio.isChecked():
                map_window.std_type = 0
                map_window.std_sh = temperature_diff_unit_converter(self.Comp_Map_std_sh.text(),self.Comp_Map_std_sh_unit.currentIndex())
            elif self.Comp_Map_std_suction_radio.isChecked():
                map_window.std_type = 1
                map_window.std_suction = temperature_unit_converter(self.Comp_Map_std_suction.text(),self.Comp_Map_std_suction_unit.currentIndex())
            map_window.F_value = float(self.Comp_Map_F.text())
            map_window.Speeds = []
            for i in range(self.Comp_Map_N_speeds.value()):
                map_window.Speeds.append(float(getattr(self,"Comp_Map_speed_value_"+str(i+1)).text()))
            map_window.M_array = self.M_array
            map_window.P_array = self.P_array
            try:
                M_coeffs, P_coeffs = Create_coefficients(self.M_array,self.P_array,self.Comp_Map_Tcond_unit.currentIndex(),self.Comp_Map_Tevap_unit.currentIndex(),self.Comp_Map_M_unit.currentIndex())
                map_window.M_coeffs = M_coeffs
                map_window.P_coeffs = P_coeffs
                self.map_window = map_window
                self.close()
            except:
                import traceback
                print(traceback.format_exc())
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("Could not convert map data into 10-AHRI coefficients model")
                msg.setWindowTitle("Error!")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please fill all empty fields")
            msg.setWindowTitle("Empty fields!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        
    def Map_num_speed_change(self):
        only_number = QRegExpValidator(QRegExp("(([0-9]+\.[0-9]*[1-9][0-9]*)|([0-9]*[1-9][0-9]*\.[0-9]+)|([0-9]*[1-9][0-9]*))"))
        num_tabs = int(self.Comp_Map_map_tabs.count())
        current_value = int(self.Comp_Map_N_speeds.value())
        if current_value > num_tabs:
            while num_tabs != current_value:
                num_tabs += 1
                self.M_array.append(0)
                self.P_array.append(0)
                TabPage = Compressor_Map_Widget(self)
                TabPage.Speed.setValidator(only_number)
                setattr(self,"Comp_Map_Speed_"+str(num_tabs)+"_value",TabPage.Speed)
                setattr(self,"Comp_Map_map_M_table_"+str(num_tabs),TabPage.map_M_table)
                setattr(self,"Comp_Map_map_P_table_"+str(num_tabs),TabPage.map_P_table)
                setattr(self,"Comp_Map_speed_value_"+str(num_tabs),TabPage.Speed)
                setattr(self,"Comp_Map_tabs_"+str(num_tabs),TabPage.Map_Tabs)
                self.Comp_Map_map_tabs.addTab(TabPage,"Speed "+str(num_tabs))
                
        if current_value < num_tabs:
            while num_tabs != current_value:
                del(self.M_array[-1])
                del(self.P_array[-1])
                num_tabs -= 1
                self.Comp_Map_map_tabs.removeTab(num_tabs)            

class Compressor_Map_Widget(QWidget, FROM_Compressor_Map_Widget):
    def __init__(self, parent=None):
        super(Compressor_Map_Widget, self).__init__(parent)
        self.setupUi(self)
        self.Load_map_button_1.clicked.connect(parent.load_map)
        self.Load_map_button_2.clicked.connect(parent.load_map)

    def copySelection(self,table_number):
        if table_number == 1:
            selection = self.map_M_table.selectedIndexes()
        elif table_number == 2:
            selection = self.map_P_table.selectedIndexes()
        else:
            selection = 0
        if selection != 0:
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
        
if __name__ == '__main__':
    def main():
        app=QApplication(sys.argv)
        app.setStyle('Fusion')
        window = Compressor_Map()
        window.show()
        app.exec_()
    try:
        main()
    except Exception as why:
        print(why)
