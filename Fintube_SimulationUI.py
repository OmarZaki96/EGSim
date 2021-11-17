from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
import os, sys
import CoolProp as CP
from unit_conversion import *
from GUI_functions import load_refrigerant_list, load_last_location, save_last_location
from inputs_validation import check_Fintube
from Solver_fintube import solver
from Results_tab import ResultsTabsWidget_Fintube
import time
import datetime
from GUI_functions import save_fintube_results_excel, read_Fin_tube, write_Fin_tube, copy_file
import appdirs
from FinTubeUI import FinTubeWindow
from copy import deepcopy


FROM_FinTube_Simulation,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Fintube_Simulation.ui"))

class values():
    pass

class Fintube_Simulation_Window(QDialog, FROM_FinTube_Simulation):
    def __init__(self, parent=None):
        super(Fintube_Simulation_Window, self).__init__(parent)
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
        self.Refrigerant.addItems(ref_list[:,0])
        
        # create connections
        self.Inlet_cond.currentIndexChanged.connect(self.cond_chnaged)
        self.clear_terminal_button.clicked.connect(self.clear_terminal_button_clicked)
        self.solve_button.clicked.connect(self.solve_button_clicked)
        self.stop_button.clicked.connect(self.stop_button_clicked)
        self.Add_button.clicked.connect(self.add_component)
        self.Edit_button.clicked.connect(self.edit_component)
        self.Duplicate_button.clicked.connect(self.duplicate_component)
        self.Delete_button.clicked.connect(self.delete_component)
        self.Import_button.clicked.connect(self.import_component)
        self.Export_button.clicked.connect(self.export_component)

        # load available components
        self.load_items()
        
        # load refrprop intially
        self.load_REFPROP()
        
        # validator
        only_number = QRegExpValidator(QRegExp("(([0-9]+\.[0-9]*[1-9][0-9]*)|([0-9]*[1-9][0-9]*\.[0-9]+)|([0-9]*[1-9][0-9]*))"))
        self.Ref_mdot.setValidator(only_number)                    
        
        # intially load changes to load validators
        self.cond_chnaged()

    def load_items(self):
        self.Component_List.clear()
        List_of_Components = []
        for Fintube in self.parent.HX_names_Fintube:
            List_of_Components.append(Fintube[1])
        self.Component_List.addItems(List_of_Components)

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
    
    def solve_button_clicked(self):
        self.time1 = time.time()
        validate = self.validate()
        if validate[0] == 0:
            self.raise_error_meesage("Please complete all empty fields")
        elif validate[0] == 2:
            self.raise_error_meesage(validate[1])
        elif validate[0] == 1:
            options = dict()
            if self.Inlet_cond.currentIndex() == 0:
                options['inlet_cond'] = 0
                options['inlet_pressure'] = pressure_unit_converter(self.Inlet_cond_1.text(),self.Inlet_cond_1_unit.currentIndex())
                options['inlet_temperature'] = temperature_unit_converter(self.Inlet_cond_2.text(),self.Inlet_cond_2_unit.currentIndex())
            elif self.Inlet_cond.currentIndex() == 1:
                options['inlet_cond'] = 1
                options['inlet_pressure'] = pressure_unit_converter(self.Inlet_cond_1.text(),self.Inlet_cond_1_unit.currentIndex())
                options['inlet_quality'] = float(self.Inlet_cond_2.text())
            elif self.Inlet_cond.currentIndex() == 2:
                options['inlet_cond'] = 2
                options['inlet_temperature'] = temperature_unit_converter(self.Inlet_cond_1.text(),self.Inlet_cond_1_unit.currentIndex())
                options['inlet_quality'] = float(self.Inlet_cond_2.text())
            elif self.Inlet_cond.currentIndex() == 3:
                options['inlet_cond'] = 3
                options['inlet_pressure'] = pressure_unit_converter(self.Inlet_cond_1.text(),self.Inlet_cond_1_unit.currentIndex())
                options['inlet_temp_diff'] = temperature_diff_unit_converter(self.Inlet_cond_2.text(),self.Inlet_cond_2_unit.currentIndex())
            elif self.Inlet_cond.currentIndex() == 4:
                options['inlet_cond'] = 4
                options['inlet_temperature'] = temperature_unit_converter(self.Inlet_cond_1.text(),self.Inlet_cond_1_unit.currentIndex())
                options['inlet_temp_diff'] = temperature_diff_unit_converter(self.Inlet_cond_2.text(),self.Inlet_cond_2_unit.currentIndex())
            options['mdot_r'] = mass_flowrate_unit_converter(self.Ref_mdot.text(),self.Ref_mdot_unit.currentIndex())
            options['Backend'] = self.Ref_library.currentText()
            if options['Backend'] == "REFPROP":
                try:
                    AS = CP.AbstractState("REFPROP", "R22")
                    options['Ref'] = self.Refrigerant.currentText()
                    number_of_tabs = self.tabWidget.count()
                    if number_of_tabs == 2:
                        self.tabWidget.removeTab(number_of_tabs - 1)
                    self.add_to_terminal("Starting a new simulation")
                    self.solving_thread = QThread()
                    self.solver_worker = solver(self.HX,options)
                    self.solver_worker.moveToThread(self.solving_thread)
                    self.solving_thread.started.connect(self.solver_worker.run)
                    self.solver_worker.terminal_message.connect(self.add_to_terminal)
                    self.solver_worker.finished.connect(self.finished_run)
                    self.solving_thread.start()
                    self.stop_button.setEnabled(True)
                    self.solve_button.setEnabled(False)
                except:
                    self.raise_error_meesage("Could not use REFPROP library")
            else:
                options['Ref'] = self.Refrigerant.currentText()
                number_of_tabs = self.tabWidget.count()
                if number_of_tabs == 2:
                    self.tabWidget.removeTab(number_of_tabs - 1)
                self.add_to_terminal("Starting a new simulation")
                self.solving_thread = QThread()
                self.solver_worker = solver(self.HX,options)
                self.solver_worker.moveToThread(self.solving_thread)
                self.solving_thread.started.connect(self.solver_worker.run)
                self.solver_worker.terminal_message.connect(self.add_to_terminal)
                self.solver_worker.finished.connect(self.finished_run)
                self.solving_thread.start()
                self.stop_button.setEnabled(True)
                self.solve_button.setEnabled(False)
                
    def stop_button_clicked(self):
        try:
            self.solver_worker.HX.terminate = True
        except:
            import traceback
            print(traceback.format_exc())
            pass

    def finished_run(self,results):
        result = results[0]
        if not result:
            self.raise_error_message(results[1])
            self.add_to_terminal("-------------------------")
        else:
            self.result_HX = results[2]
            self.results_creator()
            self.add_to_terminal(results[1])
            Calculation_time = round(time.time() - self.time1,3)
            self.add_to_terminal("Calculation time: "+str(Calculation_time)+" seconds")
            self.add_to_terminal("-------------------------")
        self.solving_thread.quit()
        self.stop_button.setEnabled(False)
        self.solve_button.setEnabled(True)

    def raise_error_message(self,message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(message)
        msg.setWindowTitle("Error!")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def results_creator(self):
        layout = QHBoxLayout(self)
        self.Results_tabs_widget = ResultsTabsWidget_Fintube(HX=self.result_HX)
        layout.addWidget(self.Results_tabs_widget)
        self.Results_tab = QWidget()
        self.Results_tab.setLayout(layout)
        self.tabWidget.addTab(self.Results_tab,"Results")
        number_of_tabs = self.tabWidget.count()
        self.tabWidget.setCurrentIndex(number_of_tabs-1)
        self.export_button = self.Results_tabs_widget.export_button
        self.export_button.clicked.connect(self.export_to_excel)

    def export_to_excel(self):
            path = QFileDialog.getSaveFileName(self, caption='Save Fin-tube results',directory=load_last_location(),filter="Excel file (*.xlsx);;All files (*.*)")[0]
            if path != "":
                save_last_location(path)
                if path[-5:].lower() != ".xlsx":
                    path = path+".xlsx"
                try:
                    succeeded = save_fintube_results_excel(self.result_HX,path)
                    if not succeeded:
                        raise
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("The file was saved successfully")
                    msg.setWindowTitle("Success!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                except:
                    import traceback
                    print(traceback.format_exc())
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("File could not be saved")
                    msg.setWindowTitle("Sorry!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
        
            
    def validate(self):
        if self.Inlet_cond_1.text() in ["","-","."]:
            return (0,)
        if self.Inlet_cond_2.text() in ["","-","."]:
            return (0,)
        if self.Inlet_cond.currentIndex() == 0:
            if float(self.Inlet_cond_1.text()) == 0:
                return (2,"Inlet Pressure can not be zero")
        elif self.Inlet_cond.currentIndex() == 1:
            if float(self.Inlet_cond_1.text()) == 0:
                return (2,"Inlet Pressure can not be zero")
            elif not (0 <= float(self.Inlet_cond_2.text()) <= 1):
                return (2, "Inlet quality must be between 0 and 1")
        elif self.Inlet_cond.currentIndex() == 2:
            if not (0 <= float(self.Inlet_cond_2.text()) <= 1):
                return (2, "Inlet quality must be between 0 and 1")
        elif self.Inlet_cond.currentIndex() == 3:
            if (float(self.Inlet_cond_2.text()) == 0):
                return (2, "Temperature difference can not be zero")
        elif self.Inlet_cond.currentIndex() == 4:
            if (float(self.Inlet_cond_2.text()) == 0):
                return (2, "Temperature difference can not be zero")

        if self.Ref_mdot.text() in ["","-","."]:
            return(0,)
        elif float(self.Ref_mdot.text()) == 0:
            return (2, "Refirgerant mass flowrate can not be zero")
        
        if self.Component_List.currentRow() == -1:
            return (2, "Please choose a fin-tube heat exhanger")
        
        self.HX = self.parent.Fintube_list[self.Component_List.currentRow()][1]
        
        result = check_Fintube(self.HX)
        if not result[0]:
            return (2,result[1])
        return (1,)
    
    def cond_chnaged(self):
        if self.Inlet_cond.currentIndex() == 0:
            only_number = QRegExpValidator(QRegExp("(([0-9]+\.[0-9]*[1-9][0-9]*)|([0-9]*[1-9][0-9]*\.[0-9]+)|([0-9]*[1-9][0-9]*))"))
            only_number_negative = QRegExpValidator(QRegExp("[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)"))
            self.Inlet_cond_1_label.setText("Inlet Pressure")
            self.Inlet_cond_1.setText("")
            self.Inlet_cond_1_unit.clear()
            self.Inlet_cond_1_unit.addItems(["Pa","kPa","MPa","bar","atm","psi"])
            self.Inlet_cond_1.setValidator(only_number)
            self.Inlet_cond_2_label.setText("Inlet Temperature")
            self.Inlet_cond_2.setText("")
            self.Inlet_cond_2_unit.clear()
            self.Inlet_cond_2_unit.addItems(["C","K","F"])
            self.Inlet_cond_2.setValidator(only_number_negative)
        elif self.Inlet_cond.currentIndex() == 1:
            only_number = QRegExpValidator(QRegExp("(([0-9]+\.[0-9]*[1-9][0-9]*)|([0-9]*[1-9][0-9]*\.[0-9]+)|([0-9]*[1-9][0-9]*))"))
            only_number_small = QDoubleValidator(0.0,1.0,5)
            self.Inlet_cond_1_label.setText("Inlet Pressure")
            self.Inlet_cond_1.setText("")
            self.Inlet_cond_1_unit.clear()
            self.Inlet_cond_1_unit.addItems(["Pa","kPa","MPa","bar","atm","psi"])
            self.Inlet_cond_1.setValidator(only_number)
            self.Inlet_cond_2_label.setText("Inlet Quality")
            self.Inlet_cond_2.setText("")
            self.Inlet_cond_2_unit.clear()
            self.Inlet_cond_2_unit.addItems(["-"])
            self.Inlet_cond_2.setValidator(only_number_small)
        elif self.Inlet_cond.currentIndex() == 2:
            only_number_negative = QRegExpValidator(QRegExp("[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)"))
            only_number_small = QDoubleValidator(0.0,1.0,12)            
            self.Inlet_cond_1_label.setText("Inlet Saturation Temperature")
            self.Inlet_cond_1.setText("")
            self.Inlet_cond_1_unit.clear()
            self.Inlet_cond_1_unit.addItems(["C","K","F"])
            self.Inlet_cond_1.setValidator(only_number_negative)
            self.Inlet_cond_2_label.setText("Inlet Quality")
            self.Inlet_cond_2.setText("")
            self.Inlet_cond_2_unit.clear()
            self.Inlet_cond_2_unit.addItems(["-"])
            self.Inlet_cond_2.setValidator(only_number_small)

        elif self.Inlet_cond.currentIndex() == 3:
            only_number = QRegExpValidator(QRegExp("(([0-9]+\.[0-9]*[1-9][0-9]*)|([0-9]*[1-9][0-9]*\.[0-9]+)|([0-9]*[1-9][0-9]*))"))
            only_number_negative = QRegExpValidator(QRegExp("[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)"))
            self.Inlet_cond_1_label.setText("Inlet Pressure")
            self.Inlet_cond_1.setText("")
            self.Inlet_cond_1_unit.clear()
            self.Inlet_cond_1_unit.addItems(["Pa","kPa","MPa","bar","atm","psi"])
            self.Inlet_cond_1.setValidator(only_number)
            self.Inlet_cond_2_label.setText("Inlet Superheat (Positive) or Subcooling (Negative)")
            self.Inlet_cond_2.setText("")
            self.Inlet_cond_2_unit.clear()
            self.Inlet_cond_2_unit.addItems(["C","K"])
            self.Inlet_cond_2.setValidator(only_number_negative)

        elif self.Inlet_cond.currentIndex() == 4:
            only_number_negative = QRegExpValidator(QRegExp("[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)"))
            self.Inlet_cond_1_label.setText("Inlet Saturation Temperature")
            self.Inlet_cond_1.setText("")
            self.Inlet_cond_1_unit.clear()
            self.Inlet_cond_1_unit.addItems(["C","K","F"])
            self.Inlet_cond_1.setValidator(only_number_negative)
            self.Inlet_cond_2_label.setText("Inlet Superheat (Positive) or Subcooling (Negative)")
            self.Inlet_cond_2.setText("")
            self.Inlet_cond_2_unit.clear()
            self.Inlet_cond_2_unit.addItems(["C","K"])
            self.Inlet_cond_2.setValidator(only_number_negative)

    def raise_error_meesage(self,message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(message)
        msg.setWindowTitle("Error!")
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

    def clear_terminal_button_clicked(self):
        self.Terminal.clear()

    def add_to_terminal(self,message):
        self.Terminal.addItem(datetime.datetime.now().strftime("%H:%M:%S: ")+message)
        self.Terminal.scrollToBottom()
        self.Terminal.setCurrentRow(self.Terminal.count()-1)

    def add_component(self):
        fubtube_Window = FinTubeWindow(self)
        fubtube_Window.exec_()
        if hasattr(fubtube_Window,"HX_data"):
            file = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '.hx'
            result = write_Fin_tube(fubtube_Window.HX_data,self.database_path+file)
            if result:
                self.parent.Fintube_list.append([file,fubtube_Window.HX_data])
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setText("Fintube Heat Exchanger was added to the database successfully")
                msg.setWindowTitle("Fintube Heat Exchanger Added")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
            else:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("Fintube Heat Exchanger Could not be added")
                msg.setWindowTitle("Fintube Heat Exchanger was not added!")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()                

        self.parent.load_database()
        self.load_items()

    def import_component(self):        
        path = QFileDialog.getOpenFileName(self, 'Open fintube file',directory=load_last_location(),filter="fintube file (*.hx);;All files (*.*)")[0]
        if path != "":
            save_last_location(path)
            result = read_Fin_tube(path)
            if result[0]:
                file_name = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '.hx'
                path = self.database_path + file_name
                write_result = write_Fin_tube(result[1],path)
                self.parent.Fintube_list.append([path,result[1]])
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setText("Fintube hear exchanger was imported successfully")
                msg.setWindowTitle("Fintube hear exchanger imported")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
            else:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("Fintube hear exchanger Could not be imported")
                msg.setWindowTitle("Fintube hear exchanger was not imported!")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
        self.parent.load_database()
        self.load_items()

    def export_component(self):
        selected_items = [x.row() for x in self.Component_List.selectedIndexes()]
        if selected_items:
            selected_item = selected_items[0]
            to_path = QFileDialog.getSaveFileName(self, caption='Save fintube file',directory=load_last_location(),filter="fintube file (*.hx);;All files (*.*)")[0]
            if to_path != "":
                save_last_location(to_path)
                if to_path[-3:].lower() != ".hx":
                    to_path = to_path+".hx"
                Fintube = deepcopy(self.parent.Fintube_list[selected_item])
                from_path = self.database_path + Fintube[0]
                result = copy_file(from_path,to_path)
                if result:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("Fintube hear exchanger was exported successfully")
                    msg.setWindowTitle("Fintube hear exchanger exported")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                else:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("Fintube hear exchanger Could not be exported")
                    msg.setWindowTitle("Fintube hear exchanger was not exported!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
    
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please select a component")
            msg.setWindowTitle("Error!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()                
        
    def duplicate_component(self):
        selected_items = [x.row() for x in self.Component_List.selectedIndexes()]
        if selected_items:
            selected_item = selected_items[0]
        
            Fintube = deepcopy(self.parent.Fintube_list[selected_item])
            file_name = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '.hx'
            path = self.database_path + file_name
            Fintube[1].name += " Copy"
            Fintube[0] = file_name
            result = write_Fin_tube(Fintube[1],path)
            if result:
                self.parent.Fintube_list.append(Fintube)
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setText("Fintube hear exchanger was duplicated successfully")
                msg.setWindowTitle("Fintube hear exchanger duplicated")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
            else:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("Fintube hear exchanger Could not be duplicated")
                msg.setWindowTitle("Fintube hear exchanger was not duplicated!")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please select a component")
            msg.setWindowTitle("Error!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()                

        self.parent.load_database()
        self.load_items()
        self.Component_List.setCurrentRow(self.Component_List.count()-1)
    
    def edit_component(self):
        selected_items = [x.row() for x in self.Component_List.selectedIndexes()]
        if selected_items:
            selected_item = selected_items[0]
            fubtube_Window = FinTubeWindow(self)
            Fintube = self.parent.Fintube_list[selected_item]
            fubtube_Window.load_fields(Fintube[1])
            fubtube_Window.exec_()
            if hasattr(fubtube_Window,"HX_data"):
                result = write_Fin_tube(fubtube_Window.HX_data,self.database_path+Fintube[0])
                if result:
                    Fintube[1] = fubtube_Window.HX_data
                    self.parent.Fintube_list[selected_item] = Fintube
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("Fintube Heat Exchanger was edited successfully")
                    msg.setWindowTitle("Fintube Heat Exchanger was edited!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()                
                else:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("Fintube Heat Exchanger Could not be edited")
                    msg.setWindowTitle("Fintube Heat Exchanger was not edited!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()                
            self.parent.load_database()
            self.load_items()
            self.Component_List.setCurrentRow(selected_item)
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please select a component")
            msg.setWindowTitle("Error!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()                

    def delete_component(self):
        selected_items = [x.row() for x in self.Component_List.selectedIndexes()]
        if selected_items:
            selected_item = selected_items[0]
            quit_msg = "Are you sure you want to delete the component?"
            reply = QMessageBox.question(self, 'Message', 
                             quit_msg, QMessageBox.Yes, QMessageBox.No)
        
            if reply == QMessageBox.Yes:
                try:
                    os.remove(self.database_path+self.parent.Fintube_list[selected_item][0])
                    del(self.parent.Fintube_list[selected_item])                
                    self.parent.load_database()
                    self.load_items()
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("Fintube heat exchanger was deleted successfully")
                    msg.setWindowTitle("Fintube heat exchanger was deleted!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()                
                except:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("Fintube heat exchanger Could not be deleted")
                    msg.setWindowTitle(" Fintube heat exchanger was not deleted!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please select a component")
            msg.setWindowTitle("Error!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()                
            
if __name__ == '__main__':
    def main():
        app=QApplication(sys.argv)
        app.setStyle('Fusion')
        window = Fintube_Simulation_Window()
        window.show()
        app.exec_()
    try:
        main()
    except Exception as why:
        print(why)
