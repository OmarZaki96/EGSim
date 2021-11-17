from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
import os, sys
from lxml import etree as ET
from unit_conversion import *
import appdirs

FROM_Design_Check_Properties,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Design_check_properties.ui"))

class values():
    pass

class Design_Check_Properties_Window(QDialog, FROM_Design_Check_Properties):
    def __init__(self, parent=None):
        super(Design_Check_Properties_Window, self).__init__(parent)
        self.setupUi(self)

        # intially get Design_check.xml file path
        self.design_check_xml_path = appdirs.user_data_dir("EGSim")+"\Design_check.xml"
        
        # check if Design_check_xml file exists, if not, create it
        if not os.path.exists(self.design_check_xml_path):
            self.create_Design_check_xml()
        
        # intially load fields
        self.load_fields()
        
        # validator
        only_number_negative = QRegExpValidator(QRegExp("[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)"))
        only_number = QRegExpValidator(QRegExp("(([0-9]+\.[0-9]*[1-9][0-9]*)|([0-9]*[1-9][0-9]*\.[0-9]+)|([0-9]*[1-9][0-9]*))"))
        self.TTD_evap_AC.setValidator(only_number_negative)
        self.TTD_cond_AC.setValidator(only_number_negative)        
        self.TTD_evap_HP.setValidator(only_number_negative)
        self.TTD_cond_HP.setValidator(only_number_negative)        
        self.DT_sat_max_evap.setValidator(only_number)        
        self.DT_sat_max_cond.setValidator(only_number)        
        
        # connections
        self.Ok_button.clicked.connect(self.ok_button_clicked)
        self.Cancel_button.clicked.connect(self.close)
        
    def ok_button_clicked(self):
        validate = self.validate()
        if validate == 1:
            try:
                data = ET.Element('Design_check_properties')
                TTD_evap_AC = ET.SubElement(data, 'TTD_evap_AC')
                TTD_evap_AC.text = str(temperature_diff_unit_converter(self.TTD_evap_AC.text(),self.TTD_evap_AC_unit.currentIndex()))
                TTD_cond_AC = ET.SubElement(data, 'TTD_cond_AC')
                TTD_cond_AC.text = str(temperature_diff_unit_converter(self.TTD_cond_AC.text(),self.TTD_cond_AC_unit.currentIndex()))
                TTD_evap_HP = ET.SubElement(data, 'TTD_evap_HP')
                TTD_evap_HP.text = str(temperature_diff_unit_converter(self.TTD_evap_HP.text(),self.TTD_evap_HP_unit.currentIndex()))
                TTD_cond_HP = ET.SubElement(data, 'TTD_cond_HP')
                TTD_cond_HP.text = str(temperature_diff_unit_converter(self.TTD_cond_HP.text(),self.TTD_cond_HP_unit.currentIndex()))
                typical_COP = ET.SubElement(data, 'typical_COP')
                typical_COP.text = str(COP_converter(self.typical_COP.text(),self.typical_COP_unit.currentIndex()))
                typical_eta_isen = ET.SubElement(data, 'typical_eta_isentropic')
                typical_eta_isen.text = str(self.typical_eta_isen.value()/100)
                Capacity_tolerance = ET.SubElement(data, 'Capacity_tolerance')
                Capacity_tolerance.text = str(self.Capacity_tolerance.value()/100)
                DT_sat_max_evap = ET.SubElement(data, 'DT_sat_max_evap')
                DT_sat_max_evap.text = str(temperature_diff_unit_converter(self.DT_sat_max_evap.text(),self.DT_sat_max_evap_unit.currentIndex()))
                DT_sat_max_cond = ET.SubElement(data, 'DT_sat_max_cond')
                DT_sat_max_cond.text = str(temperature_diff_unit_converter(self.DT_sat_max_cond.text(),self.DT_sat_max_cond_unit.currentIndex()))
                insta_check = ET.SubElement(data, 'instant_check')
                insta_check.text = str(int(self.insta_activated.isChecked()))
                mydata = str(ET.tostring(data, pretty_print=True),"utf-8")
                with open(self.design_check_xml_path, "w") as myfile:
                    myfile.write(mydata)
                self.close()
            except:
                import traceback
                print(traceback.format_exc())
                self.raise_error_message("New values could not be saved!")
    
    def validate(self):
        if self.TTD_cond_AC.text() in ["","-","."]:
            self.raise_error_message("Please fill empty fields")
            return 0
        if self.TTD_evap_AC.text() in ["","-","."]:
            self.raise_error_message("Please fill empty fields")
            return 0
        if self.TTD_cond_HP.text() in ["","-","."]:
            self.raise_error_message("Please fill empty fields")
            return 0
        if self.TTD_evap_HP.text() in ["","-","."]:
            self.raise_error_message("Please fill empty fields")
            return 0
        if self.typical_COP.text() in ["","-","."]:
            self.raise_error_message("Please fill empty fields")
            return 0
        
        if self.DT_sat_max_evap.text() in ["","-","."]:
            self.raise_error_message("Please fill empty fields")
            return 0
        if self.DT_sat_max_cond.text() in ["","-","."]:
            self.raise_error_message("Please fill empty fields")
            return 0
        if self.Capacity_tolerance.value() == 0:
            self.raise_error_message("Cycle capacity tolrance can not be zero!")
            return 0
        return 1
    
    def create_Design_check_xml(self):
        try:
            data = ET.Element('Design_check_properties')
            TTD_evap_AC = ET.SubElement(data, 'TTD_evap_AC')
            TTD_evap_AC.text = "5"
            TTD_cond_AC = ET.SubElement(data, 'TTD_cond_AC')
            TTD_cond_AC.text = "5"
            TTD_evap_HP = ET.SubElement(data, 'TTD_evap_HP')
            TTD_evap_HP.text = "1"
            TTD_cond_HP = ET.SubElement(data, 'TTD_cond_HP')
            TTD_cond_HP.text = "14"
            typical_COP = ET.SubElement(data, 'typical_COP')
            typical_COP.text = "3.0"
            typical_eta_isen = ET.SubElement(data, 'typical_eta_isentropic')
            typical_eta_isen.text = "0.7"
            Capacity_tolerance = ET.SubElement(data, 'Capacity_tolerance')
            Capacity_tolerance.text = "0.2"
            DT_sat_max_evap = ET.SubElement(data, 'DT_sat_max_evap')
            DT_sat_max_evap.text = "3"
            DT_sat_max_cond = ET.SubElement(data, 'DT_sat_max_cond')
            DT_sat_max_cond.text = "2"
            insta_check = ET.SubElement(data, 'instant_check')
            insta_check.text = "1"
            mydata = str(ET.tostring(data, pretty_print=True),"utf-8")
            with open(self.design_check_xml_path, "w") as myfile:
                myfile.write(mydata)
            self.load_fields()
        except:
            self.raise_error_message("properties file does not exist, and it could not be created!")
            self.close()
        
    def load_fields(self):
        try:
            tree = ET.parse(self.design_check_xml_path)
            root = tree.getroot()            
            self.TTD_evap_AC.setText(str(round(float(root.find("TTD_evap_AC").text),6)))
            self.TTD_cond_AC.setText(str(round(float(root.find("TTD_cond_AC").text),6)))    
            self.TTD_evap_HP.setText(str(round(float(root.find("TTD_evap_HP").text),6)))
            self.TTD_cond_HP.setText(str(round(float(root.find("TTD_cond_HP").text),6)))    
            self.typical_COP.setText(str(round(float(root.find("typical_COP").text),6)))    
            self.typical_eta_isen.setValue(float(root.find("typical_eta_isentropic").text)*100)
            self.DT_sat_max_evap.setText(str(round(float(root.find("DT_sat_max_evap").text),6)))
            self.DT_sat_max_cond.setText(str(round(float(root.find("DT_sat_max_cond").text),6)))
            self.Capacity_tolerance.setValue(round(float(root.find("Capacity_tolerance").text),6)*100)
            self.insta_activated.setChecked(int(root.find("instant_check").text))
        except:
            import traceback
            print(traceback.format_exc())
            self.raise_warning_message("Could not read properties file, the program will create another one with default values")
            self.create_Design_check_xml()
            self.close()

    def raise_error_message(self,message):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText(message)
            msg.setWindowTitle("Error!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()

    def raise_warning_message(self,message):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText(message)
            msg.setWindowTitle("Warning!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()

if __name__ == '__main__':
    def main():
        app=QApplication(sys.argv)
        app.setStyle('Fusion')
        window = Design_Check_Properties_Window()
        window.show()
        app.exec_()
    try:
        main()
    except Exception as why:
        print(why)

