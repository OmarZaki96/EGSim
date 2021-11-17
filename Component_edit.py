from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
import os, sys, csv, io
from GUI_functions import read_capillary_file, read_comp_xml, read_Fin_tube,\
    read_Microchannel, read_line_file, read_cycle_file
from GUI_functions import write_capillary_file, write_comp_xml, write_Fin_tube,\
    write_Microchannel, write_line_file, write_cycle_file, copy_file, load_last_location, save_last_location
from CompressorUI import CompressorWindow
from FinTubeUI import FinTubeWindow
from MicrochannelUI import MicrochannelWindow
from LineUI import LineWindow
from CapillaryUI import CapillaryWindow
from copy import deepcopy
import datetime
import appdirs

FROM_Component_Edit,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Component_edit.ui"))

class values():
    pass

class Component_edit(QDialog, FROM_Component_Edit):
    def __init__(self, component_type, parent=None):
        super(Component_edit, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent

        # create database path
        self.database_path = appdirs.user_data_dir("EGSim")+"/Database/"
        
        # Setting Window Title
        if component_type == "Compressor":
            self.setWindowTitle("Edit Compressor")
            self.component_type = component_type
        elif component_type == "Fintube":
            self.setWindowTitle("Edit Fintube Heat Exchanger")
            self.component_type = component_type
        elif component_type == "Microchannel":
            self.setWindowTitle("Edit Microchannel Heat Exchanger")
            self.component_type = component_type
        elif component_type == "Line":
            self.setWindowTitle("Select Liquid Line")
            self.component_type = "Line"
        elif component_type == "Capillary":
            self.setWindowTitle("Edit Capillary Tube")
            self.component_type = component_type
            
        # populate list widget with current components
        self.load_items()

        # Connections
        self.Add_button.clicked.connect(self.add_component)
        self.Edit_button.clicked.connect(self.edit_component)
        self.Duplicate_button.clicked.connect(self.duplicate_component)
        self.Delete_button.clicked.connect(self.delete_component)
        self.Components_list.itemDoubleClicked.connect(self.edit_component)
        self.Import_button.clicked.connect(self.import_component)
        self.Export_button.clicked.connect(self.export_component)

    def add_component(self):
        if self.component_type == "Compressor":
            Comp_Window = CompressorWindow(self)
            Comp_Window.exec_()
            if hasattr(Comp_Window,"Compressor"):
                file = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '.comp'
                result = write_comp_xml(Comp_Window.Compressor,self.database_path+file)
                if result:
                    self.parent.Compressor_list.append([file,Comp_Window.Compressor])
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("Compressor was added to the database successfully")
                    msg.setWindowTitle("Compressor Added")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                else:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("Compressor Could not be added")
                    msg.setWindowTitle("Compressor was not added!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()                

        elif self.component_type == "Fintube":
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

        elif self.component_type == "Microchannel":
            microchannel_Window = MicrochannelWindow(self)
            microchannel_Window.exec_()
            if hasattr(microchannel_Window,"HX_data"):
                file = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '.hx'
                result = write_Microchannel(microchannel_Window.HX_data,self.database_path+file)
                if result:
                    self.parent.Microchannel_list.append([file,microchannel_Window.HX_data])
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("Microchannel Heat Exchanger was added to the database successfully")
                    msg.setWindowTitle("Microchannel Heat Exchanger Added")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                else:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("Microchannel Heat Exchanger Could not be added")
                    msg.setWindowTitle("Microchannel Heat Exchanger was not added!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()                

        elif self.component_type == "Line":
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

        elif self.component_type == "Capillary":
            capillary_Window = CapillaryWindow(self)
            capillary_Window.exec_()
            if hasattr(capillary_Window,"capillary_result"):
                file = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '.capillary'
                result = write_capillary_file(capillary_Window.capillary_result,self.database_path+file)
                if result:
                    self.parent.Capillary_list.append([file,capillary_Window.capillary_result])
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("Capillary tube was added to the database successfully")
                    msg.setWindowTitle("Capillary tube Added")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                else:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("Capillary tube Could not be added")
                    msg.setWindowTitle("Capillary tube was not added!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()    
            
        self.parent.load_database()
        self.load_items()

    def load_items(self):
        self.Components_list.clear()
        List_of_Components = []
        if self.component_type == "Compressor":
            for Compressor in self.parent.Comp_names:
                List_of_Components.append(Compressor[1])
            self.Components_list.addItems(List_of_Components)
        elif self.component_type == "Fintube":
            for Fintube in self.parent.HX_names_Fintube:
                List_of_Components.append(Fintube[1])
            self.Components_list.addItems(List_of_Components)
        elif self.component_type == "Microchannel":
            for Microchannel in self.parent.HX_names_Microchannel:
                List_of_Components.append(Microchannel[1])
            self.Components_list.addItems(List_of_Components)
        elif self.component_type == "Line":
            for Line in self.parent.Line_names:
                List_of_Components.append(Line[1])
            self.Components_list.addItems(List_of_Components)
        elif self.component_type == "Capillary":
            for Capillary in self.parent.Capillary_names:
                List_of_Components.append(Capillary[1])
            self.Components_list.addItems(List_of_Components)

    def import_component(self):        
        if self.component_type == "Compressor":            
            path = QFileDialog.getOpenFileName(self, 'Open compressor file',directory=load_last_location(),filter="compressor file (*.comp);;All files (*.*)")[0]
            if path != "":
                save_last_location(path)
                result = read_comp_xml(path)
                if result[0]:
                    file_name = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '.comp'
                    path = self.database_path + file_name
                    write_result = write_comp_xml(result[1],path)
                    self.parent.Compressor_list.append([path,result[1]])
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("Compressor was imported successfully")
                    msg.setWindowTitle("Compressor imported")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                else:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("Compressor Could not be imported")
                    msg.setWindowTitle("Compressor was not imported!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()                

        elif self.component_type == "Fintube":
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

        elif self.component_type == "Microchannel":
            path = QFileDialog.getOpenFileName(self, 'Open Microchannel file',directory=load_last_location(),filter="Microchannel file (*.hx);;All files (*.*)")[0]
            if path != "":
                save_last_location(path)
                result = read_Microchannel(path)
                if result[0]:
                    file_name = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '.hx'
                    path = self.database_path + file_name
                    write_result = write_Microchannel(result[1],path)
                    self.parent.Microchannel_list.append([path,result[1]])
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("Microchannel hear exchanger was imported successfully")
                    msg.setWindowTitle("Microchannel hear exchanger imported")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                else:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("Microchannel hear exchanger Could not be imported")
                    msg.setWindowTitle("Microchannel hear exchanger was not imported!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()                

        elif self.component_type == "Line":
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

        elif self.component_type == "Capillary":
            path = QFileDialog.getOpenFileName(self, 'Open capillary file',directory=load_last_location(),filter="capillary file (*.capillary);;All files (*.*)")[0]
            if path != "":
                save_last_location(path)
                result = read_capillary_file(path)
                if result[0]:
                    file_name = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '.capillary'
                    path = self.database_path + file_name
                    write_result = write_capillary_file(result[1],path)
                    self.parent.Capillary_list.append([path,result[1]])
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("Capillary was imported successfully")
                    msg.setWindowTitle("Capillary imported")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                else:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("Capillary Could not be imported")
                    msg.setWindowTitle("Capillary was not imported!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()     
                    
        self.parent.load_database()
        self.load_items()

    def export_component(self):
        selected_items = [x.row() for x in self.Components_list.selectedIndexes()]
        if selected_items:
            selected_item = selected_items[0]
            if self.component_type == "Compressor":
                to_path = QFileDialog.getSaveFileName(self, caption='Save compressor file',directory=load_last_location(),filter="compressor file (*.comp);;All files (*.*)")[0]
                if to_path != "":
                    save_last_location(to_path)
                    if to_path[-5:].lower() != ".comp":
                        to_path = to_path+".comp"
                    Compressor = deepcopy(self.parent.Compressor_list[selected_item])
                    from_path = self.database_path + Compressor[0]
                    result = copy_file(from_path,to_path)
                    if result:
                        msg = QMessageBox()
                        msg.setIcon(QMessageBox.Information)
                        msg.setText("Compressor was exported successfully")
                        msg.setWindowTitle("Compressor exported")
                        msg.setStandardButtons(QMessageBox.Ok)
                        msg.exec_()
                    else:
                        msg = QMessageBox()
                        msg.setIcon(QMessageBox.Warning)
                        msg.setText("Compressor Could not be exported")
                        msg.setWindowTitle("Compressor was not exported!")
                        msg.setStandardButtons(QMessageBox.Ok)
                        msg.exec_()
    
            elif self.component_type == "Fintube":
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
    
            elif self.component_type == "Microchannel":
                to_path = QFileDialog.getSaveFileName(self, caption='Save microchannel file',directory=load_last_location(),filter="microchannel file (*.hx);;All files (*.*)")[0]
                if to_path != "":
                    save_last_location(to_path)
                    if to_path[-3:].lower() != ".hx":
                        to_path = to_path+".hx"
                    Microchannel = deepcopy(self.parent.Microchannel_list[selected_item])
                    from_path = self.database_path + Microchannel[0]
                    result = copy_file(from_path,to_path)
                    if result:
                        msg = QMessageBox()
                        msg.setIcon(QMessageBox.Information)
                        msg.setText("Microchannel hear exchanger was exported successfully")
                        msg.setWindowTitle("Microchannel hear exchanger exported")
                        msg.setStandardButtons(QMessageBox.Ok)
                        msg.exec_()
                    else:
                        msg = QMessageBox()
                        msg.setIcon(QMessageBox.Warning)
                        msg.setText("Microchannel hear exchanger Could not be exported")
                        msg.setWindowTitle("Microchannel hear exchanger was not exported!")
                        msg.setStandardButtons(QMessageBox.Ok)
                        msg.exec_()                
    
            elif self.component_type == "Line":
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
    
            elif self.component_type == "Capillary":
                to_path = QFileDialog.getSaveFileName(self, caption='Save capillary file',directory=load_last_location(),filter="capillary file (*.capillary);;All files (*.*)")[0]
                if to_path != "":
                    save_last_location(to_path)
                    if to_path[-10:].lower() != ".capillary":
                        to_path = to_path+".capillary"
                    Capillary = deepcopy(self.parent.Capillary_list[selected_item])
                    from_path = self.database_path + Capillary[0]
                    result = copy_file(from_path,to_path)
                    if result:
                        self.parent.Capillary_list.append(Capillary)
                        msg = QMessageBox()
                        msg.setIcon(QMessageBox.Information)
                        msg.setText("Capillary was exported successfully")
                        msg.setWindowTitle("Capillary exported")
                        msg.setStandardButtons(QMessageBox.Ok)
                        msg.exec_()
                    else:
                        msg = QMessageBox()
                        msg.setIcon(QMessageBox.Warning)
                        msg.setText("Capillary Could not be exported")
                        msg.setWindowTitle("Capillary was not exported!")
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
        selected_items = [x.row() for x in self.Components_list.selectedIndexes()]
        if selected_items:
            selected_item = selected_items[0]
        
            if self.component_type == "Compressor":
                Compressor = deepcopy(self.parent.Compressor_list[selected_item])
                file_name = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '.comp'
                path = self.database_path + file_name
                Compressor[1].Comp_name += " Copy"
                Compressor[0] = file_name
                result = write_comp_xml(Compressor[1],path)
                if result:
                    self.parent.Compressor_list.append(Compressor)
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("Compressor was duplicated successfully")
                    msg.setWindowTitle("Compressor duplicated")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                else:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("Compressor Could not be duplicated")
                    msg.setWindowTitle("Compressor was not duplicated!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()                
    
            elif self.component_type == "Fintube":
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
    
            elif self.component_type == "Microchannel":
                Microchannel = deepcopy(self.parent.Microchannel_list[selected_item])
                file_name = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '.hx'
                path = self.database_path + file_name
                Microchannel[1].name += " Copy"
                Microchannel[0] = file_name
                result = write_Microchannel(Microchannel[1],path)
                if result:
                    self.parent.Microchannel_list.append(Microchannel)
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("Microchannel hear exchanger was duplicated successfully")
                    msg.setWindowTitle("Microchannel hear exchanger duplicated")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                else:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("Microchannel hear exchanger Could not be duplicated")
                    msg.setWindowTitle("Microchannel hear exchanger was not duplicated!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()                
    
            elif self.component_type == "Line":
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
    
            elif self.component_type == "Capillary":
                Capillary = deepcopy(self.parent.Capillary_list[selected_item])
                file_name = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '.capillary'
                path = self.database_path + file_name
                Capillary[1].Capillary_name += " Copy"
                Capillary[0] = file_name
                result = write_capillary_file(Capillary[1],path)
                if result:
                    self.parent.Capillary_list.append(Capillary)
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("Capillary was duplicated successfully")
                    msg.setWindowTitle("Capillary duplicated")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                else:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("Capillary Could not be duplicated")
                    msg.setWindowTitle("Capillary was not duplicated!")
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
        self.Components_list.setCurrentRow(self.Components_list.count()-1)
    
    def edit_component(self):
        selected_items = [x.row() for x in self.Components_list.selectedIndexes()]
        if selected_items:
            selected_item = selected_items[0]
            if self.component_type == "Compressor":
                Comp_Window = CompressorWindow(self)
                Compressor = self.parent.Compressor_list[selected_item]
                Comp_Window.load_fields(Compressor[1])
                Comp_Window.exec_()
                if hasattr(Comp_Window,"Compressor"):
                    result = write_comp_xml(Comp_Window.Compressor,self.database_path+Compressor[0])
                    if result:
                        Compressor[1] = Comp_Window.Compressor
                        self.parent.Compressor_list[selected_item] = Compressor
                        msg = QMessageBox()
                        msg.setIcon(QMessageBox.Information)
                        msg.setText("Compressor was edited successfully")
                        msg.setWindowTitle("Compressor was edited!")
                        msg.setStandardButtons(QMessageBox.Ok)
                        msg.exec_()                
                    else:
                        msg = QMessageBox()
                        msg.setIcon(QMessageBox.Warning)
                        msg.setText("Compressor Could not be edited")
                        msg.setWindowTitle("Compressor was not edited!")
                        msg.setStandardButtons(QMessageBox.Ok)
                        msg.exec_()                
    
            elif self.component_type == "Fintube":
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
    
            elif self.component_type == "Microchannel":
                microchannel_Window = MicrochannelWindow(self)
                Microchannel = self.parent.Microchannel_list[selected_item]
                microchannel_Window.load_fields(Microchannel[1])
                microchannel_Window.exec_()
                if hasattr(microchannel_Window,"HX_data"):
                    result = write_Microchannel(microchannel_Window.HX_data,self.database_path+Microchannel[0])
                    if result:
                        Microchannel[1] = microchannel_Window.HX_data
                        self.parent.Microchannel_list[selected_item] = Microchannel
                        msg = QMessageBox()
                        msg.setIcon(QMessageBox.Information)
                        msg.setText("Microchannel Heat Exchanger was edited successfully")
                        msg.setWindowTitle("Microchannel Heat Exchanger was edited!")
                        msg.setStandardButtons(QMessageBox.Ok)
                        msg.exec_()                
                    else:
                        msg = QMessageBox()
                        msg.setIcon(QMessageBox.Warning)
                        msg.setText("Microchannel Heat Exchanger Could not be edited")
                        msg.setWindowTitle("Microchannel Heat Exchanger was not edited!")
                        msg.setStandardButtons(QMessageBox.Ok)
                        msg.exec_()                
    
            elif self.component_type == "Line":
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
    
            elif self.component_type == "Capillary":
                capillary_Window = CapillaryWindow(self)
                Capillary = self.parent.Capillary_list[selected_item]
                capillary_Window.load_fields(Capillary[1])
                capillary_Window.exec_()
                if hasattr(capillary_Window,"capillary_result"):
                    result = write_capillary_file(capillary_Window.capillary_result,self.database_path+Capillary[0])
                    if result:
                        Capillary[1] = capillary_Window.capillary_result
                        self.parent.Capillary_list[selected_item] = Capillary
                        msg = QMessageBox()
                        msg.setIcon(QMessageBox.Information)
                        msg.setText("Capillary was edited successfully")
                        msg.setWindowTitle("Capillary was edited!")
                        msg.setStandardButtons(QMessageBox.Ok)
                        msg.exec_()                
                    else:
                        msg = QMessageBox()
                        msg.setIcon(QMessageBox.Warning)
                        msg.setText("Capillary Could not be edited")
                        msg.setWindowTitle("Capillary was not edited!")
                        msg.setStandardButtons(QMessageBox.Ok)
                        msg.exec_()                

            self.parent.load_database()
            self.load_items()
            self.Components_list.setCurrentRow(selected_item)
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please select a component")
            msg.setWindowTitle("Error!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()                

    def delete_component(self):
        selected_items = [x.row() for x in self.Components_list.selectedIndexes()]
        if selected_items:
            selected_item = selected_items[0]
            quit_msg = "Are you sure you want to delete the component?"
            reply = QMessageBox.question(self, 'Message', 
                             quit_msg, QMessageBox.Yes, QMessageBox.No)
        
            if reply == QMessageBox.Yes:
                try:
                    if self.component_type == "Compressor":
                        os.remove(self.database_path+self.parent.Compressor_list[selected_item][0])
                        del(self.parent.Compressor_list[selected_item])
                        if hasattr(self.parent,"selected_compressor_index"):
                            delattr(self.parent,"selected_compressor_index")
                        if hasattr(self.parent,"selected_compressor_filename"):
                            delattr(self.parent,"selected_compressor_filename")
                    elif self.component_type == "Fintube":
                        os.remove(self.database_path+self.parent.Fintube_list[selected_item][0])
                        del(self.parent.Fintube_list[selected_item])
                        if self.parent.Condenser_type.currentIndex() == 0:
                            if hasattr(self.parent,"selected_condenser_index"):
                                delattr(self.parent,"selected_condenser_index")
                            if hasattr(self.parent,"selected_condenser_filename"):
                                delattr(self.parent,"selected_condenser_filename")
                        if self.parent.Evaporator_type.currentIndex() == 0:
                            if hasattr(self.parent,"selected_evaporator_index"):
                                delattr(self.parent,"selected_evaporator_index")
                            if hasattr(self.parent,"selected_evaporator_filename"):
                                delattr(self.parent,"selected_evaporator_filename")
                    elif self.component_type == "Microchannel":
                        os.remove(self.database_path+self.parent.Microchannel_list[selected_item][0])
                        del(self.parent.Microchannel_list[selected_item])
                        if self.parent.Condenser_type.currentIndex() == 1:
                            if hasattr(self.parent,"selected_condenser_index"):
                                delattr(self.parent,"selected_condenser_index")
                            if hasattr(self.parent,"selected_condenser_filename"):
                                delattr(self.parent,"selected_condenser_filename")
                        if self.parent.Evaporator_type.currentIndex() == 1:
                            if hasattr(self.parent,"selected_evaporator_index"):
                                delattr(self.parent,"selected_evaporator_index")
                            if hasattr(self.parent,"selected_evaporator_filename"):
                                delattr(self.parent,"selected_evaporator_filename")
                    elif self.component_type == "Line":
                        os.remove(self.database_path+self.parent.Line_list[selected_item][0])
                        del(self.parent.Line_list[selected_item])
                        if hasattr(self.parent,"selected_liquidline_index"):
                            delattr(self.parent,"selected_liquidline_index")
                        if hasattr(self.parent,"selected_liquidline_filename"):
                            delattr(self.parent,"selected_liquidline_filename")
                        if hasattr(self.parent,"selected_suctionline_index"):
                            delattr(self.parent,"selected_suctionline_index")
                        if hasattr(self.parent,"selected_suctionline_filename"):
                            delattr(self.parent,"selected_suctionline_filename")
                        if hasattr(self.parent,"selected_dischargeline_index"):
                            delattr(self.parent,"selected_dischargeline_index")
                        if hasattr(self.parent,"selected_dischargeline_filename"):
                            delattr(self.parent,"selected_dischargeline_filename")
                        if hasattr(self.parent,"selected_twophaseline_index"):
                            delattr(self.parent,"selected_twophaseline_index")
                        if hasattr(self.parent,"selected_twophaseline_filename"):
                            delattr(self.parent,"selected_twophaseline_filename")
                    elif self.component_type == "Capillary":
                        os.remove(self.database_path+self.parent.Capillary_list[selected_item][0])
                        del(self.parent.Capillary_list[selected_item])
                        if hasattr(self.parent,"selected_capillary_index"):
                            delattr(self.parent,"selected_capillary_index")
                        if hasattr(self.parent,"selected_capillary_filename"):
                            delattr(self.parent,"selected_capillary_filename")
                
                    self.parent.load_database()
                    self.load_items()
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText(self.component_type+" was deleted successfully")
                    msg.setWindowTitle(self.component_type+" was deleted!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()                
                except:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText(self.component_type+" Could not be deleted")
                    msg.setWindowTitle(self.component_type+" was not deleted!")
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
        window = Component_selection("Compressor")
        window.show()
        app.exec_()
    try:
        main()
    except Exception as why:
        print(why)
