from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
import os, sys
import CoolProp as CP
from unit_conversion import *
from GUI_functions import load_refrigerant_list, load_last_location, save_last_location
from inputs_validation import check_line
from Solver_line import solver
from Results_tab import ResultsTabsWidget_Line
import time
import datetime
from GUI_functions import save_Line_results_excel, read_line_file, write_line_file, copy_file
import appdirs
from LineUI import LineWindow
from copy import deepcopy


FROM_Line_Simulation,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Line_Simulation.ui"))

class values():
    pass

class Line_Simulation_Window(QDialog, FROM_Line_Simulation):
    def __init__(self, parent=None):
        super(Line_Simulation_Window, self).__init__(parent)
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

        # validator
        only_number = QRegExpValidator(QRegExp("(([0-9]+\.[0-9]*[1-9][0-9]*)|([0-9]*[1-9][0-9]*\.[0-9]+)|([0-9]*[1-9][0-9]*))"))
        self.Ref_mdot.setValidator(only_number)
        
        # intially load changes to load validators
        self.cond_chnaged()

        # initially load REFPROP
        self.load_REFPROP()

    def load_items(self):
        self.Component_List.clear()
        List_of_Components = []
        for Line in self.parent.Line_names:
            List_of_Components.append(Line[1])
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
            options['Ref'] = self.Refrigerant.currentText()
            number_of_tabs = self.tabWidget.count()
            if number_of_tabs == 2:
                self.tabWidget.removeTab(number_of_tabs-1)
            self.add_to_terminal("Starting a new simulation")
            self.solving_thread = QThread()
            self.solver_worker = solver(self.Line,options)
            self.solver_worker.moveToThread(self.solving_thread)
            self.solving_thread.started.connect(self.solver_worker.run)
            self.solver_worker.terminal_message.connect(self.add_to_terminal)
            self.solver_worker.finished.connect(self.finished_run)
            self.solving_thread.start()
            self.stop_button.setEnabled(True)
            self.solve_button.setEnabled(False)

    def stop_button_clicked(self):
        try:
            self.solver_worker.Line.terminate = True
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
            self.result_Line = results[2]
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
        self.Results_tabs_widget = ResultsTabsWidget_Line(Line=self.result_Line)
        layout.addWidget(self.Results_tabs_widget)
        self.Results_tab = QWidget()
        self.Results_tab.setLayout(layout)
        self.tabWidget.addTab(self.Results_tab,"Results")
        number_of_tabs = self.tabWidget.count()
        self.tabWidget.setCurrentIndex(number_of_tabs-1)
        self.export_button = self.Results_tabs_widget.export_button
        self.export_button.clicked.connect(self.export_to_excel)

    def export_to_excel(self):
            path = QFileDialog.getSaveFileName(self, caption='Save Line results',directory=load_last_location(),filter="Excel file (*.xlsx);;All files (*.*)")[0]
            if path != "":
                save_last_location(path)
                if path[-5:].lower() != ".xlsx":
                    path = path+".xlsx"
                try:
                    succeeded = save_Line_results_excel(self.result_Line,path)
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
            return (2, "Please choose a line")
        
        self.Line = self.parent.Line_list[self.Component_List.currentRow()][1]
        
        result = check_line(self.Line)
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
        line_Window = LineWindow(self)
        line_Window.exec_()
        if hasattr(line_Window,"line_result"):
            file = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '.line'
            result = write_line_file(line_Window.line_result,self.database_path+file)
            if result:
                self.parent.Line_list.append([file,line_Window.line_result])
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setText("Line was added to the database successfully")
                msg.setWindowTitle("Line Added")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
            else:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("Line Could not be added")
                msg.setWindowTitle("Line was not added!")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()                
            
            self.parent.load_database()
            self.load_items()


    def import_component(self):        
        path = QFileDialog.getOpenFileName(self, 'Open line file',directory=load_last_location(),filter="line file (*.line);;All files (*.*)")[0]
        if path != "":
            save_last_location(path)
            result = read_line_file(path)
            if result[0]:
                file_name = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '.line'
                path = self.database_path + file_name
                write_result = write_line_file(result[1],path)
                self.parent.Line_list.append([path,result[1]])
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setText("Line was imported successfully")
                msg.setWindowTitle("Line imported")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
            else:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("Line Could not be imported")
                msg.setWindowTitle("Line was not imported!")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()                
                    
            self.parent.load_database()
            self.load_items()

    def export_component(self):
        selected_items = [x.row() for x in self.Component_List.selectedIndexes()]
        if selected_items:
            selected_item = selected_items[0]
            to_path = QFileDialog.getSaveFileName(self, caption='Save line file',directory=load_last_location(),filter="line file (*.line);;All files (*.*)")[0]
            if to_path != "":
                save_last_location(to_path)
                if to_path[-5:].lower() != ".line":
                    to_path = to_path+".line"
                Line = deepcopy(self.parent.Line_list[selected_item])
                from_path = self.database_path + Line[0]
                result = copy_file(from_path,to_path)
                if result:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("Line was exported successfully")
                    msg.setWindowTitle("Line exported")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                else:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("Line Could not be exported")
                    msg.setWindowTitle("Line was not exported!")
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
        
            Line = deepcopy(self.parent.Line_list[selected_item])
            file_name = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '.line'
            path = self.database_path + file_name
            Line[1].Line_name += " Copy"
            Line[0] = file_name
            result = write_line_file(Line[1],path)
            if result:
                self.parent.Line_list.append(Line)
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setText("Line was duplicated successfully")
                msg.setWindowTitle("Line duplicated")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
            else:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("Line Could not be duplicated")
                msg.setWindowTitle("Line was not duplicated!")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()                    
            self.parent.load_database()
            self.load_items()
            self.Component_List.setCurrentRow(self.Component_List.count()-1)
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please select a component")
            msg.setWindowTitle("Error!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()                

    
    def edit_component(self):
        selected_items = [x.row() for x in self.Component_List.selectedIndexes()]
        if selected_items:
            selected_item = selected_items[0]
            line_Window = LineWindow(self)
            Line = self.parent.Line_list[selected_item]
            line_Window.load_fields(Line[1])
            line_Window.exec_()
            if hasattr(line_Window,"line_result"):
                result = write_line_file(line_Window.line_result,self.database_path+Line[0])
                if result:
                    Line[1] = line_Window.line_result
                    self.parent.Line_list[selected_item] = Line
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("Line was edited successfully")
                    msg.setWindowTitle("Line was edited!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()                
                else:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("Line Could not be edited")
                    msg.setWindowTitle("Line was not edited!")
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
                    os.remove(self.database_path+self.parent.Line_list[selected_item][0])
                    del(self.parent.Line_list[selected_item])
                
                    self.parent.load_database()
                    self.load_items()
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("Line was deleted successfully")
                    msg.setWindowTitle("Line was deleted!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()                
                except:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("Line Could not be deleted")
                    msg.setWindowTitle("Line was not deleted!")
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
        window = Microchannel_Simulation_Window()
        window.show()
        app.exec_()
    try:
        main()
    except Exception as why:
        print(why)
