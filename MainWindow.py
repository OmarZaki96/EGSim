from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
import os, sys, csv, io
from GUI_functions import *
from Component_selection import Component_selection
from Component_edit import Component_edit
import datetime
import CoolProp as CP
import zipfile
import shutil
from unit_conversion import *
from Solver import solver
from CompressorUI import CompressorWindow
from FinTubeUI import FinTubeWindow
from MicrochannelUI import MicrochannelWindow
from LineUI import LineWindow
from CapillaryUI import CapillaryWindow
from Results_tab import ResultsTabsWidget
from REFPROP_properties import REFPROP_Properties_Window
import appdirs
from Fintube_SimulationUI import Fintube_Simulation_Window
from Microchannel_SimulationUI import Microchannel_Simulation_Window
from Line_SimulationUI import Line_Simulation_Window
from Capillary_SimulationUI import Capillary_Simulation_Window
from Compressor_SimulationUI import Compressor_Simulation_Window
from parametric_cycle_window import parametric_cycle_Window
from parametric_compressor_window import parametric_compressor_Window
from parametric_fintube_window import parametric_fintube_Window
from parametric_microchannel_window import parametric_microchannel_Window
from parametric_capillary_window import parametric_capillary_Window
from parametric_line_window import parametric_line_Window
from Parallel_processingUI import Parallel_Processing_Window
import numpy as np
from multiprocessing import cpu_count
import time
from Parametric_data_table import Parametric_table
from AboutUI import AboutWindow
from Compressor_AHRI_to_Physics_UI import Compressor_to_physics_Window
from Design_check_properties import Design_Check_Properties_Window
from design_checker import check_design_object
import shutil
from Ranges_Creator_Properties import Ranges_Creator_Window
from FinTube_select_fin import FinTube_select_fin_window
from FinTube_select_tube import FinTube_select_tube_window
from Microchannel_select_fin import Microchannel_select_fin_window
from Microchannel_select_tube import Microchannel_select_tube_window
from Line_select_tube import Line_select_tube_window
from inputs_validation import check_compressor_capacity, check_condenser_capacity_fintube, check_evaporator_capacity_fintube, check_evaporator_capacity_microchannel, check_condenser_capacity_microchannel
from Capillary_SizingUI import Capillary_sizing_window
from CoolProp.CoolProp import HAPropsSI
from CompressorUI_rating_to_physics import Compressor_rating_to_physics_Window
from Compressor_select_datasheet import Compressor_select_datasheet_window

FROM_Main_Window,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/MainWindow.ui"))

class values():
    pass

class MainWindow(QMainWindow, FROM_Main_Window):
    close_signal_to_main = pyqtSignal()
    restart_signal_to_main = pyqtSignal()
    change_style_signal_to_main = pyqtSignal(str)
    def __init__(self, parent=None):
        # first UI
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        
        # enable checking capacity
        self.capacity_check = True

        # disabling cycle charge and capillary tube options
        self.First_condition.model().item(1).setEnabled(False)
        self.Expansion_device.model().item(1).setEnabled(False)

        # create database path
        self.database_path = appdirs.user_data_dir("EGSim")+"/Database/"
        
        # make sure database folder exists, if not then create it
        if not os.path.exists(self.database_path):
            os.mkdir(self.database_path)

        # create temp folder if not exists
        temp_dir = appdirs.user_data_dir("EGSim")+"/Temp/"
        if not os.path.exists(temp_dir):
            os.mkdir(temp_dir)
            
        # deleting old files from database that was imported during loading cycle with components
        self.delete_old_files_from_database()

        # create N_Processes ini file path
        self.N_processes_ini_path = appdirs.user_data_dir("EGSim")+"/N_Processes.ini"
        
        # make sure N_Processes ini file exists, if not then create it
        if not os.path.exists(self.N_processes_ini_path):
            with open(self.N_processes_ini_path, "w") as file1:
                file1.write(str(cpu_count()))
        
        # read N_Processes ini file
        with open(self.N_processes_ini_path, 'r') as file:
            for line in file:
                N_processes = line.strip()
        try:
            self.N_Processes = int(N_processes)
        except:
            import traceback
            print(traceback.format_exc())
            self.N_Processes = cpu_count()
            self.raise_error_meesage("Failed to load saved number of processes for parallel processing, using "+str(cpu_count())+" instead")

        self.restart_state = False
        x = QApplication.desktop().screen().rect().center().x() - self.rect().center().x()
        self.move(QPoint(x,0))
        
        # intially load images
        def images_loader(path,var_name,size):
            try:
                photo = QPixmap(path)
                photo = photo.scaledToWidth(size)
                setattr(self,var_name,photo)
            except:
                pass
        images_loader("photos/HX.png",'HX_image',200)
        images_loader("photos/Compressor.png",'Compressor_image',150)
        images_loader("photos/Expansion.png",'Expansion_image',150)
        images_loader("photos/Liquidline.png",'Liquidline_image',150)
        images_loader("photos/Dischargeline.png",'Dischargeline_image',150)
        images_loader("photos/Suctionline.png",'Suctionline_image',150)
        images_loader("photos/Twophaseline.png",'Twophaseline_image',150)

        if hasattr(self,'HX_image'):
            self.Condenser_photo.setPixmap(self.HX_image)
        else:
            self.Condenser_photo.setText("")

        if hasattr(self,'HX_image'):
            self.Evaporator_photo.setPixmap(self.HX_image)
        else:
            self.Evaporator_photo.setText("")

        if hasattr(self,'Compressor_image'):
            self.Compressor_photo.setPixmap(self.Compressor_image)
        else:
            self.Compressor_photo.setText("")

        if hasattr(self,'Expansion_image'):
            self.Expansion_photo.setPixmap(self.Expansion_image)
        else:
            self.Expansion_photo.setText("")

        if hasattr(self,'Suctionline_image'):
            self.Suctionline_photo.setPixmap(self.Suctionline_image)
        else:
            self.Suctionline_photo.setText("")

        if hasattr(self,'Dischargeline_image'):
            self.Dischargeline_photo.setPixmap(self.Dischargeline_image)
        else:
            self.Dischargeline_photo.setText("")

        if hasattr(self,'Liquidline_image'):
            self.Liquidline_photo.setPixmap(self.Liquidline_image)
        else:
            self.Liquidline_photo.setText("")

        if hasattr(self,'Twophaseline_image'):
            self.Twophaseline_photo.setPixmap(self.Twophaseline_image)
        else:
            self.Twophaseline_photo.setText("")
        
        # intialize components lists
        self.Fintube_list = []
        self.Microchannel_list = []
        self.Compressor_list = []
        self.Line_list = []
        self.Capillary_list = []

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
        self.Cycle_refrigerant.addItems(ref_list[:,0])
        index = self.Cycle_refrigerant.findText("R22", Qt.MatchFixedString)
        self.Cycle_refrigerant.setCurrentIndex(index)

        # load Database
        self.load_database()

        # load refprop initially
        self.load_REFPROP()

        # Validators
        only_number = QRegExpValidator(QRegExp("(([0-9]+\.[0-9]*[1-9][0-9]*)|([0-9]*[1-9][0-9]*\.[0-9]+)|([0-9]*[1-9][0-9]*))"))
        only_number_negative = QRegExpValidator(QRegExp("[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)"))
        self.Subcooling.setValidator(only_number)
        self.Charge.setValidator(only_number)
        self.Superheat.setValidator(only_number)
        self.Energy_resid.setValidator(only_number)
        self.Pressire_resid.setValidator(only_number)
        self.Mass_flowrate_resid.setValidator(only_number)
        self.Mass_resid.setValidator(only_number)
        self.Tevap_guess.setValidator(only_number_negative)
        self.Tcond_guess.setValidator(only_number_negative)
        self.Capacity_target.setValidator(only_number)

        # connections
        self.swap_HXs_button.clicked.connect(self.swap_HXs)
        self.actionNew_Compressor.triggered.connect(self.add_new_compressor)
        self.actionNew_Fin_tube_HX.triggered.connect(self.add_new_fintube)
        self.actionNew_Microchannel_HX.triggered.connect(self.add_new_microchannel)
        self.actionNew_Line.triggered.connect(self.add_new_line)
        self.actionNew_Capillary.triggered.connect(self.add_new_capillary)
        self.actionExit.triggered.connect(self.close)
        self.actionCompressors.triggered.connect(self.edit_component)
        self.actionFin_tube_HX.triggered.connect(self.edit_component)
        self.actionMicrochannel_HX.triggered.connect(self.edit_component)
        self.actionLine.triggered.connect(self.edit_component)
        self.actionCapillary_Tube.triggered.connect(self.edit_component)
        self.First_condition.currentIndexChanged.connect(self.first_condition_changed)
        self.Expansion_device.currentIndexChanged.connect(self.expansion_device_changed)
        self.Tevap_guess_type.currentIndexChanged.connect(self.Tevap_guess_type_changed)
        self.Tcond_guess_type.currentIndexChanged.connect(self.Tcond_guess_type_changed)
        self.actionNew.triggered.connect(self.New_cycle_action)
        self.actionOpen.triggered.connect(self.Open_cycle_action)
        self.actionSave.triggered.connect(self.Save_cycle_action)
        self.Condenser_select_button.clicked.connect(self.select_component)
        self.LiquidLine_select_button.clicked.connect(self.select_component)
        self.Expansion_select_button.clicked.connect(self.select_component)
        self.TwophaseLine_select_button.clicked.connect(self.select_component)
        self.Evaporator_select_button.clicked.connect(self.select_component)
        self.SuctionLine_select_button.clicked.connect(self.select_component)
        self.Compressor_select_button.clicked.connect(self.select_component)
        self.DischargeLine_select_button.clicked.connect(self.select_component)
        self.Condenser_type.currentIndexChanged.connect(self.condenser_type_changed)
        self.Evaporator_type.currentIndexChanged.connect(self.evaporator_type_changed)
        self.actionExport_Database.triggered.connect(self.export_database)
        self.actionImport_Database.triggered.connect(self.import_database)
        self.Cycle_refrigerant.currentIndexChanged.connect(self.refrigerant_changed)
        self.Solve_button.clicked.connect(self.solve_button)
        self.Stop_button.clicked.connect(self.stop_button)
        self.clear_terminal_button.clicked.connect(self.clear_terminal_button_clicked)
        self.actionExport_to_Excel_xlsx.triggered.connect(self.save_results_to_excel)
        self.actionREFPROP_Properties.triggered.connect(self.open_REFPROP_properties)
        self.actionR410A_Cycle_with_TXV.triggered.connect(self.load_example)
        self.actionR22_Cycle_with_TXV.triggered.connect(self.load_example)
        self.actionR32_Cycle_with_TXV.triggered.connect(self.load_example)
        self.actionFin_tube_Heat_Exchanger.triggered.connect(self.load_fintube_simulation)
        self.actionMicrochannel_Heat_Exchanger.triggered.connect(self.load_microchannel_simulation)
        self.actionLine_2.triggered.connect(self.load_line_simulation)
        self.actionCapillary_Tube_2.triggered.connect(self.load_capillary_simulation)
        self.actionSimulate_Compressor.triggered.connect(self.load_compressor_simulation)
        self.Parametric_cycle.stateChanged.connect(self.parametric_cycle_check)
        self.Parametric_compressor.stateChanged.connect(self.parametric_compressor_check)        
        self.Parametric_evaporator.stateChanged.connect(self.parametric_evaporator_check)        
        self.Parametric_condenser.stateChanged.connect(self.parametric_condenser_check)        
        self.Parametric_capillary.stateChanged.connect(self.parametric_capillary_check)        
        self.Parametric_liquid.stateChanged.connect(self.parametric_liquid_check)        
        self.Parametric_2phase.stateChanged.connect(self.parametric_2phase_check)        
        self.Parametric_suction.stateChanged.connect(self.parametric_suction_check)        
        self.Parametric_discharge.stateChanged.connect(self.parametric_discharge_check)
        self.Parametric_cycle_button.clicked.connect(self.parametric_cycle_button_clicked)        
        self.Parametric_compressor_button.clicked.connect(self.parametric_compressor_button_clicked)        
        self.Parametric_evaporator_button.clicked.connect(self.parametric_evaporator_button_clicked)        
        self.Parametric_condenser_button.clicked.connect(self.parametric_condenser_button_clicked)        
        self.Parametric_capillary_button.clicked.connect(self.parametric_capillary_button_clicked)        
        self.Parametric_liquid_button.clicked.connect(self.parametric_liquid_button_clicked)        
        self.Parametric_2phase_button.clicked.connect(self.parametric_2phase_button_clicked)        
        self.Parametric_suction_button.clicked.connect(self.parametric_suction_button_clicked)        
        self.Parametric_discharge_button.clicked.connect(self.parametric_discharge_button_clicked)
        self.actionParallel_Processing.triggered.connect(self.load_parallel_processing_window)
        self.actionAbout.triggered.connect(self.show_copyrights)
        self.actionDocumentation.triggered.connect(self.documentation_clicked)
        self.actionCompressor_to_physics_model.triggered.connect(self.actionCompressor_to_physics_model_triggered)
        self.actionDesign_Check_Properties.triggered.connect(self.actionDesign_Check_Properties_triggered)
        self.Check_design_button.clicked.connect(self.check_design_button_clicked)
        self.actionSave_Cycle_with_Components.triggered.connect(self.save_cycle_with_components)
        self.actionOpen_Cycle_with_Components.triggered.connect(self.open_cycle_with_components)
        self.Cycle_mode.currentIndexChanged.connect(self.cycle_mode_changed)
        self.actionRanges_Creator_Properties.triggered.connect(self.Ranges_creator_properties_triggered)
        self.Test_Condition.currentIndexChanged.connect(self.Test_condition_changed)
        self.Superheat_location.currentIndexChanged.connect(self.superheat_location_changed)
        self.actionFin_tube.triggered.connect(self.open_fin_tube_fins_database_window)
        self.actionFin_tube_2.triggered.connect(self.open_fin_tube_tubes_database_window)
        self.actionMicrochannel.triggered.connect(self.open_microchannel_fins_database_window)
        self.actionMicrochannel_2.triggered.connect(self.open_microchannel_tubes_database_window)
        self.actionEdit_Database.triggered.connect(self.open_line_tubes_database_window)
        self.actionCompressor_Rating_to_Physics.triggered.connect(self.open_comp_rating_to_physics)
        self.actionimport_Fin_tube_fin.triggered.connect(self.import_fintube_fin_file)
        self.actionimport_Microchannel_fin.triggered.connect(self.import_microchannel_fin_file)
        self.actionimport_Fin_tube_tube.triggered.connect(self.import_fintube_tube_file)
        self.actionImport_Database_2.triggered.connect(self.import_line_tube_file)
        self.actionCapillary_Sizing.triggered.connect(self.Capillary_sizing)
        self.actionImport_Compressor_from_Manufacturer_Datasheet.triggered.connect(self.import_compressor_from_datahseet)
        
        self.Subcooling.editingFinished.connect(self.check_components_capacity)
        self.Superheat.editingFinished.connect(self.check_components_capacity)
        self.Capacity_target.editingFinished.connect(self.check_components_capacity)
        
        # initially refresh selected components
        self.refresh_selected_components()

        # intially fix parametric data table
        self.create_parametric_data_table()
        
        # intially enable UI
        self.disable_UI(False)
        
        # intially update residuals options
        self.update_residuals_options()

        # save cycle mode selection
        self.old_Cycle_mode_selection = self.Cycle_mode.currentIndex()
        
        # initally populate the test condition drop menu
        self.refresh_test_condition()

    def open_comp_rating_to_physics(self):
        Compressor_rating_to_physics_window = Compressor_rating_to_physics_Window()
        Compressor_rating_to_physics_window.exec_()        

    def import_compressor_from_datahseet(self):
        compressor_from_datasheet = Compressor_select_datasheet_window()
        compressor_from_datasheet.exec_()
        self.refresh_selected_components()

    def Capillary_sizing(self):
        capillary_sizing_window = Capillary_sizing_window()
        capillary_sizing_window.Ref.setCurrentIndex(self.Cycle_refrigerant.currentIndex())
        capillary_sizing_window.Cycle_Capacity.setText(self.Capacity_target.text())
        capillary_sizing_window.Cycle_Capacity_unit.setCurrentIndex(self.Capacity_target_unit.currentIndex())
        capillary_sizing_window.Subcooling.setText(self.Subcooling.text())
        capillary_sizing_window.Subcooling_unit.setCurrentIndex(self.Subcooling_unit.currentIndex())
        capillary_sizing_window.Superheat.setText(self.Superheat.text())
        capillary_sizing_window.Superheat_unit.setCurrentIndex(self.Superheat_unit.currentIndex())
        capillary_sizing_window.Cycle_Mode.setCurrentIndex(self.Cycle_mode.currentIndex())        
        capillary_sizing_window.exec_()

    def check_components_capacity(self):
        self.check_compressor_capacity()
        self.check_condenser_capacity()
        self.check_evaporator_capacity()

    def check_condenser_capacity(self):
        if self.capacity_check:
            try:
                self.capacity_check = False
                self.update_capacity_validation_table()
                if hasattr(self,"selected_condenser_index"):
                    if self.Condenser_type.currentIndex() == 0:
                        condenser = self.Fintube_list[self.selected_condenser_index][1]
                        condenser.capacity_validation_table = self.capacity_validation_table
                        result = check_condenser_capacity_fintube(condenser)
                    elif self.Condenser_type.currentIndex() == 1:
                        condenser = self.Microchannel_list[self.selected_condenser_index][1]
                        condenser.capacity_validation_table = self.capacity_validation_table
                        result = check_condenser_capacity_microchannel(condenser)
                    if result[0] == 0:
                        self.raise_error_message(result[1])
                    elif result[0] == 1:
                        try:
                            TTD = float(result[1])
                            self.TTD_condenser = TTD
                        except:
                            pass
                    elif result[0] == -1:
                        pass
                self.capacity_check = True
            except:
                self.capacity_check = True
                import traceback
                print(traceback.format_exc())
                pass
        
    def check_evaporator_capacity(self):
        if self.capacity_check:
            try:
                self.capacity_check = False
                self.update_capacity_validation_table()
                if hasattr(self,"selected_evaporator_index"):
                    if self.Evaporator_type.currentIndex() == 0:
                        evaporator = self.Fintube_list[self.selected_evaporator_index][1]
                        evaporator.capacity_validation_table = self.capacity_validation_table
                        result = check_evaporator_capacity_fintube(evaporator)
                    elif self.Evaporator_type.currentIndex() == 1:
                        evaporator = self.Microchannel_list[self.selected_evaporator_index][1]
                        evaporator.capacity_validation_table = self.capacity_validation_table
                        result = check_evaporator_capacity_microchannel(evaporator)
                    if result[0] == 0:
                        self.raise_error_message(result[1])
                    elif result[0] == 1:
                        try:
                            TTD = float(result[1])
                            self.TTD_evaporator = TTD
                        except:
                            pass
                    elif result[0] == -1:
                        pass
                self.capacity_check = True
            except:
                self.capacity_check = True
                import traceback
                print(traceback.format_exc())
                pass

    def check_compressor_capacity(self):
        if self.capacity_check:
            try:
                self.capacity_check = False
                self.update_capacity_validation_table()
                if hasattr(self,"selected_compressor_index"):
                    compressor = self.Compressor_list[self.selected_compressor_index][1]
                    compressor.capacity_validation_table = self.capacity_validation_table
                    result = check_compressor_capacity(compressor)
                    if not result[0]:
                        self.raise_error_message(result[1])
                self.capacity_check = True
            except:
                self.capacity_check = True
                import traceback
                print(traceback.format_exc())
                pass
        
    def import_reference_values(self):
        try:
            design_check_xml_path = appdirs.user_data_dir("EGSim")+"\Design_check.xml"
            tree = ET.parse(design_check_xml_path)
            root = tree.getroot()            
            check_activated = int(root.find("instant_check").text)
            if not check_activated:
                return(0,)
            TTD_evap_AC = float(root.find("TTD_evap_AC").text)
            TTD_cond_AC = float(root.find("TTD_cond_AC").text)
            TTD_evap_HP = float(root.find("TTD_evap_HP").text)
            TTD_cond_HP = float(root.find("TTD_cond_HP").text)
            typical_COP = float(root.find("typical_COP").text)
            typical_eta_isen = float(root.find("typical_eta_isentropic").text)
            DT_sat_max_evap = float(root.find("DT_sat_max_evap").text)
            DT_sat_max_cond = float(root.find("DT_sat_max_cond").text)
            Capacity_tolerance = float(root.find("Capacity_tolerance").text)
            return (1,(TTD_evap_AC,TTD_cond_AC,TTD_evap_HP,TTD_cond_HP,typical_COP,DT_sat_max_evap,DT_sat_max_cond,Capacity_tolerance,typical_eta_isen))
        except:
            design_Check_Properties_window = Design_Check_Properties_Window(self)            
            design_Check_Properties_window.exec_()
            import traceback
            print(traceback.format_exc())
            return (0,)

    def update_capacity_validation_table(self):
        try:
            assert(self.First_condition.currentIndex() == 0)
            assert(self.Expansion_device.currentIndex() == 0)
            result = self.import_reference_values()
            if result[0]:
                self.capacity_validation_table = {
                    "ref":self.Cycle_refrigerant.currentText(),
                    "mode":self.Cycle_mode.currentIndex(),
                    "Test_Condition":self.Test_Condition.currentText(),
                    "Capacity":power_unit_converter(self.Capacity_target.text(),self.Capacity_target_unit.currentIndex()),
                    "SC":temperature_diff_unit_converter(self.Subcooling.text(),self.Subcooling_unit.currentIndex()),
                    "SH":temperature_diff_unit_converter(self.Superheat.text(),self.Superheat_unit.currentIndex()),
                    "TTD_evap_AC":result[1][0],
                    "TTD_cond_AC":result[1][1],
                    "TTD_evap_HP":result[1][2],
                    "TTD_cond_HP":result[1][3],
                    "COP":result[1][4],
                    "DT_sat_max_evap":result[1][5],
                    "DT_sat_max_cond":result[1][6],
                    "Capacity_tolerance":result[1][7],
                    "comp_isen_eff":result[1][8],
                    }
                
                Test_condition = self.Test_Condition.currentText()        
                mode = self.Cycle_mode.currentIndex()
                
                   
                if hasattr(self,"selected_condenser_index"):
                    if self.Condenser_type.currentIndex() == 0:
                        condenser = self.Fintube_list[self.selected_condenser_index][1]
                    elif self.Condenser_type.currentIndex() == 1:
                        condenser = self.Microchannel_list[self.selected_condenser_index][1]
                    Pin_a_cond = condenser.Air_P
                    if Test_condition == "Custom":
                        Tin_a_cond = condenser.Air_T
                        Win_a_cond = HAPropsSI("W","T",condenser.Air_T,"P",condenser.Air_P,"R",condenser.Air_RH)
                        
                    if hasattr(self,"TTD_condenser"):
                        if self.Cycle_mode == 0:
                            self.capacity_validation_table["TTD_cond_AC"] = condenser.TTD
                        elif self.Cycle_mode == 1:
                            self.capacity_validation_table["TTD_cond_HP"] = condenser.TTD
                else:
                    if Test_condition == "Custom":
                        if mode == 0:
                            Tin_a_cond = 35 + 273.15
                            Win_a_cond = HAPropsSI("W","T", 35 + 273.15,"P",101325,"B", 24 + 273.15)
                        else:
                            Tin_a_cond = 20 + 273.15
                            Win_a_cond = HAPropsSI("W","T",20 + 273.15,"P",101325,"B",15 + 273.15)                            
                    
                if hasattr(self,"selected_evaporator_index"):
                    if self.Evaporator_type.currentIndex() == 0:
                        evaporator = self.Fintube_list[self.selected_evaporator_index][1]
                    elif self.Evaporator_type.currentIndex() == 1:
                        evaporator = self.Microchannel_list[self.selected_evaporator_index][1]
                    Pin_a_evap = evaporator.Air_P
                    if Test_condition == "Custom":
                        Tin_a_evap = evaporator.Air_T
                        Win_a_evap = HAPropsSI("W","T",evaporator.Air_T,"P",evaporator.Air_P,"R",evaporator.Air_RH)
                        
                    if hasattr(self,"TTD_evaporator"):
                        if self.Cycle_mode == 0:
                            self.capacity_validation_table["TTD_evap_AC"] = evaporator.TTD
                        elif self.Cycle_mode == 1:
                            self.capacity_validation_table["TTD_evap_HP"] = evaporator.TTD
                else:
                    if Test_condition == "Custom":
                        Pin_a_evap = 101325
                        if mode == 0:
                            Tin_a_evap = 27 + 273.15
                            Win_a_evap = HAPropsSI("W","T", 27 + 273.15,"P",101325,"B", 19 + 273.15)
                        else:
                            Tin_a_evap = 7 + 273.15
                            Win_a_evap = HAPropsSI("W","T", 7 + 273.15,"P",101325,"B",6 + 273.15)

                if Test_condition == "T1":
                    Tin_a_evap = 27 + 273.15
                    Win_a_evap = HAPropsSI("W","T", 27 + 273.15,"P",Pin_a_evap,"B", 19 + 273.15)
                    Tin_a_cond = 35 + 273.15
                    Win_a_cond = HAPropsSI("W","T", 35 + 273.15,"P",Pin_a_cond,"B", 24 + 273.15)
        
                elif Test_condition == "T2":
                    Tin_a_evap = 21 + 273.15
                    Win_a_evap = HAPropsSI("W","T", 21 + 273.15,"P",Pin_a_evap,"B", 15 + 273.15)
                    Tin_a_cond = 27 + 273.15
                    Win_a_cond = HAPropsSI("W","T", 27 + 273.15,"P",Pin_a_cond,"B", 19 + 273.15)        
        
                elif Test_condition == "T3":
                    Tin_a_evap = 29 + 273.15
                    Win_a_evap = HAPropsSI("W","T", 29 + 273.15,"P",Pin_a_evap,"B", 19 + 273.15)
                    Tin_a_cond = 46 + 273.15
                    Win_a_cond = HAPropsSI("W","T", 46 + 273.15,"P",Pin_a_cond,"B", 24 + 273.15)        
        
                elif Test_condition == "H1":
                    Tin_a_evap = 7 + 273.15
                    Win_a_evap = HAPropsSI("W","T", 7 + 273.15,"P",Pin_a_evap,"B",6 + 273.15)
                    Tin_a_cond = 20 + 273.15
                    Win_a_cond = HAPropsSI("W","T",20 + 273.15,"P",Pin_a_cond,"B",15 + 273.15)
        
                elif Test_condition == "H2":
                    Tin_a_evap = 2 + 273.15
                    Win_a_evap = HAPropsSI("W","T", 2 + 273.15,"P",Pin_a_evap,"B",1 + 273.15)
                    Tin_a_cond = 20 + 273.15
                    Win_a_cond = HAPropsSI("W","T",20 + 273.15,"P",Pin_a_cond,"B",15 + 273.15)
        
                elif Test_condition == "H3":
                    Tin_a_evap = -7 + 273.15
                    Win_a_evap = HAPropsSI("W","T", -7 + 273.15,"P",Pin_a_evap,"B",-8 + 273.15)
                    Tin_a_cond = 20 + 273.15
                    Win_a_cond = HAPropsSI("W","T",20 + 273.15,"P",Pin_a_cond,"B",15 + 273.15)

                self.capacity_validation_table["Tin_a_cond"] = Tin_a_cond
                self.capacity_validation_table["Pin_a_cond"] = Pin_a_cond
                self.capacity_validation_table["win_a_cond"] = Win_a_cond
                self.capacity_validation_table["Tin_a_evap"] = Tin_a_evap
                self.capacity_validation_table["Pin_a_evap"] = Pin_a_evap
                self.capacity_validation_table["win_a_evap"] = Win_a_evap
                            

                self.capacity_validation = True
            else:
                if hasattr(self,"capacity_validation_table"):
                    delattr(self,"capacity_validation_table")
                raise
        except:
            import traceback
            print(traceback.format_exc())
            self.capacity_validation = False

    def import_fintube_fin_file(self):
        quit_msg = "You will lose the current fin-tube fins database. Continue?"
        reply = QMessageBox.question(self, 'Message', 
                         quit_msg, QMessageBox.Yes, QMessageBox.No)
    
        if reply == QMessageBox.Yes:
            path = QFileDialog.getOpenFileName(self, 'Open Fin-tube fins database file',directory=load_last_location(),filter="CSV file (*.csv);;All files (*.*)")[0]
            if path != "":
                save_last_location(path)
                result = import_fin_tube_fins_file(path)
                if result:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("The file was loaded successfully")
                    msg.setWindowTitle("Success!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                else:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("File could not be loaded")
                    msg.setWindowTitle("Sorry!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()

    def import_microchannel_fin_file(self):
        quit_msg = "You will lose the current microchannel fins database. Continue?"
        reply = QMessageBox.question(self, 'Message', 
                         quit_msg, QMessageBox.Yes, QMessageBox.No)
    
        if reply == QMessageBox.Yes:
            path = QFileDialog.getOpenFileName(self, 'Open Microchannel fins database file',directory=load_last_location(),filter="CSV file (*.csv);;All files (*.*)")[0]
            if path != "":
                save_last_location(path)
                result = import_microchannel_fins_file(path)
                if result:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("The file was loaded successfully")
                    msg.setWindowTitle("Success!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                else:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("File could not be loaded")
                    msg.setWindowTitle("Sorry!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()

    def import_fintube_tube_file(self):
        quit_msg = "You will lose the current fin-tube tubes database. Continue?"
        reply = QMessageBox.question(self, 'Message', 
                         quit_msg, QMessageBox.Yes, QMessageBox.No)
    
        if reply == QMessageBox.Yes:
            path = QFileDialog.getOpenFileName(self, 'Open Fin-tube tubes database file',directory=load_last_location(),filter="CSV file (*.csv);;All files (*.*)")[0]
            if path != "":
                save_last_location(path)
                result = import_fin_tube_tubes_file(path)
                if result:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("The file was loaded successfully")
                    msg.setWindowTitle("Success!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                else:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("File could not be loaded")
                    msg.setWindowTitle("Sorry!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()

    def import_microchannel_tube_file(self):
        quit_msg = "You will lose the current microchannel tubes database. Continue?"
        reply = QMessageBox.question(self, 'Message', 
                         quit_msg, QMessageBox.Yes, QMessageBox.No)
    
        if reply == QMessageBox.Yes:
            path = QFileDialog.getOpenFileName(self, 'Open Microchannel tubes database file',directory=load_last_location(),filter="CSV file (*.csv);;All files (*.*)")[0]
            if path != "":
                save_last_location(path)
                result = import_microchannel_tubes_file(path)
                if result:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("The file was loaded successfully")
                    msg.setWindowTitle("Success!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                else:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("File could not be loaded")
                    msg.setWindowTitle("Sorry!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()

    def import_line_tube_file(self):
        quit_msg = "You will lose the current lines database. Continue?"
        reply = QMessageBox.question(self, 'Message', 
                         quit_msg, QMessageBox.Yes, QMessageBox.No)
    
        if reply == QMessageBox.Yes:
            path = QFileDialog.getOpenFileName(self, 'Open lines database file',directory=load_last_location(),filter="CSV file (*.csv);;All files (*.*)")[0]
            if path != "":
                save_last_location(path)
                result = import_line_tubes_file(path)
                if result:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("The file was loaded successfully")
                    msg.setWindowTitle("Success!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                else:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("File could not be loaded")
                    msg.setWindowTitle("Sorry!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()

    def open_fin_tube_fins_database_window(self):
        edit_fin_window = FinTube_select_fin_window()
        edit_fin_window.Select_button.hide()
        edit_fin_window.Select_button.setEnabled(False)
        if not edit_fin_window.load_fins():
            self.raise_error_message("Could not load fins database.\nPlease fix database csv file.")
        else:
            edit_fin_window.exec_()

    def open_fin_tube_tubes_database_window(self):
        edit_tube_window = FinTube_select_tube_window()
        edit_tube_window.Select_button.hide()
        edit_tube_window.Select_button.setEnabled(False)
        if not edit_tube_window.load_tubes():
            self.raise_error_message("Could not load tubes database.\nPlease fix database csv file.")
        else:
            edit_tube_window.exec_()

    def open_microchannel_fins_database_window(self):
        edit_fin_window = Microchannel_select_fin_window()
        edit_fin_window.Select_button.hide()
        edit_fin_window.Select_button.setEnabled(False)
        if not edit_fin_window.load_fins():
            self.raise_error_message("Could not load fins database.\nPlease fix database csv file.")
        else:
            edit_fin_window.exec_()

    def open_microchannel_tubes_database_window(self):
        edit_tube_window = Microchannel_select_tube_window()
        edit_tube_window.Select_button.hide()
        edit_tube_window.Select_button.setEnabled(False)
        if not edit_tube_window.load_tubes():
            self.raise_error_message("Could not load tubes database.\nPlease fix database csv file.")
        else:
            edit_tube_window.exec_()

    def open_line_tubes_database_window(self):
        edit_tube_window = Line_select_tube_window()
        edit_tube_window.Select_button.hide()
        edit_tube_window.Select_button.setEnabled(False)
        if not edit_tube_window.load_tubes():
            self.raise_error_message("Could not load lines database.\nPlease fix database csv file.")
        else:
            edit_tube_window.exec_()

    def enable_range_validation(self):
        self.Subcooling.editingFinished.connect(lambda: self.validate_range_item("lineedit",'temperature_diff'))
        self.Charge.editingFinished.connect(lambda: self.validate_range_item("lineedit",'mass'))
        self.Superheat.editingFinished.connect(lambda: self.validate_range_item("lineedit",'temperature_diff'))

    def validate_range_item(self,data_type,conversion=None):
        if hasattr(self,"validation_range"):
            sender = self.sender()
            prop_name = sender.objectName()
            
            name = getattr(self,prop_name+"_label").text()
            
            # getting value
            failed = False
            if data_type == "lineedit":
                try:
                    value = float(sender.text())
                    failed = False
                except:
                    failed = True
                    
            elif data_type == "spinbox":            
                value = sender.value()
            
            # converting value to SI units
            if conversion == "temperature_diff":
                true_value = temperature_diff_unit_converter(value,getattr(self,prop_name+"_unit").currentIndex())
    
            elif conversion == "mass":
                true_value = mass_unit_converter(value,getattr(self,prop_name+"_unit").currentIndex())
    
            elif conversion == "power":
                true_value = power_unit_converter(value,getattr(self,prop_name+"_unit").currentIndex())
    
            elif conversion == "pressure":
                true_value = pressure_unit_converter(value,getattr(self,prop_name+"_unit").currentIndex())
    
            elif conversion == "mass_flowrate":
                true_value = mass_flowrate_unit_converter(value,getattr(self,prop_name+"_unit").currentIndex())
    
            elif conversion == "volume_flowrate":
                true_value = volume_flowrate_unit_converter(value,getattr(self,prop_name+"_unit").currentIndex())
    
            elif conversion == "temperature":
                true_value = temperature_unit_converter(value,getattr(self,prop_name+"_unit").currentIndex())
    
            elif conversion == "length":
                true_value = length_unit_converter(value,getattr(self,prop_name+"_unit").currentIndex())
    
            elif conversion == "volume":
                true_value = volume_unit_converter(value,getattr(self,prop_name+"_unit").currentIndex())
    
            elif conversion == "angle":
                true_value = angle_unit_converter(value,getattr(self,prop_name+"_unit").currentIndex())
    
            elif conversion == "thermal_K":
                true_value = Thermal_K_unit_converter(value,getattr(self,prop_name+"_unit").currentIndex())
    
            elif conversion == "HTC":
                true_value = HTC_unit_converter(value,getattr(self,prop_name+"_unit").currentIndex())
            
            elif conversion == None:
                true_value = value
            
            validation_range = getattr(self.validation_range,prop_name)
            minimum = validation_range[1]
            maximum = validation_range[2]
            if maximum != None and true_value > maximum:
                self.raise_error_message("The value you enter for "+name+" which is "+"%.5g" % true_value+" is higher than recommended maximum value of "+"%.5g" % maximum+". The original value was "+"%.5g" % validation_range[0]+". (all in SI units.)")
            elif minimum != None and true_value < minimum:
                self.raise_error_message("The value you enter for "+name+" which is "+"%.5g" % true_value+ " is lower than recommended minimum value of "+"%.5g" % minimum+". The original value was "+"%.5g" % validation_range[0]+". (all in SI units.)")

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

    def delete_validation_range(self):
        if hasattr(self,"validation_range"):
            delattr(self,"validation_range")
        if hasattr(self,"Validation_ranges"):
            delattr(self,"Validation_ranges")

    def superheat_location_changed(self):
        self.delete_validation_range()

    def Test_condition_changed(self):
        self.delete_validation_range()
        self.check_components_capacity()

    def Ranges_creator_properties_triggered(self):
        Ranges_creator_window = Ranges_Creator_Window()
        Ranges_creator_window.exec_()

    def refresh_test_condition(self):
        self.Test_Condition.clear()
        if self.Cycle_mode.currentIndex() == 0:
            self.Test_Condition.addItems(["Custom","T1","T2","T3"])
        elif self.Cycle_mode.currentIndex() == 1:
            self.Test_Condition.addItems(["Custom","H1","H2","H3"])
        self.Test_Condition.setCurrentIndex(1)

    def cycle_mode_changed(self):
        self.capacity_check = False
        if self.Cycle_mode.currentIndex() == 0:
            self.Condenser_label.setText("Outdoor Unit")
            self.Evaporator_label.setText("Indoor Unit")
            self.Parametric_condenser.setText("Outdoor Unit")
            self.Parametric_evaporator.setText("Indoor Unit")
        elif self.Cycle_mode.currentIndex() == 1:
            self.Condenser_label.setText("Indoor Unit")
            self.Evaporator_label.setText("Outdoor Unit")
            self.Parametric_condenser.setText("Indoor Unit")
            self.Parametric_evaporator.setText("Outdoor Unit")
        
        if hasattr(self,"old_Cycle_mode_selection"):
            if self.Cycle_mode.currentIndex() != self.old_Cycle_mode_selection:
                self.swap_HXs()
                self.swap_lines()
        
        self.delete_validation_range()
        self.old_Cycle_mode_selection = self.Cycle_mode.currentIndex()
        self.refresh_test_condition()
        self.capacity_check = True
        self.check_components_capacity()
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Please make sure that when changing cycle mode, you might need to reverse the sequence of series circuits in Indoor and Outdoor unit and change the circuitry between counter and parallel flow (if using segment-by-segment solver).")
        msg.setWindowTitle("Warning!")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def save_cycle_with_components(self):
        validate = self.validate()
        if validate == 0:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please fill all empty fields")
            msg.setWindowTitle("Empty Fields!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()

        elif validate == 2:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please select all components!")
            msg.setWindowTitle("Empty Components!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            
        elif validate == 1 or validate == 3:
            path = QFileDialog.getSaveFileName(self, caption='Save Cycle with components file',directory=load_last_location(),filter="cycle with components file (*.cyclec);;All files (*.*)")[0]
            if path != "":
                save_last_location(path)
                if path[-7:].lower() != ".cyclec":
                    path = path+".cyclec"
                cycle = values()
                
                cycle.Cycle_refrigerant = self.Cycle_refrigerant.currentText()
                cycle.Condenser_type = self.Condenser_type.currentIndex()
                cycle.Evaporator_type = self.Evaporator_type.currentIndex()
                cycle.First_condition = self.First_condition.currentIndex()
                if self.First_condition.currentIndex() == 0:
                    cycle.Subcooling = temperature_diff_unit_converter(self.Subcooling.text(),self.Subcooling_unit.currentIndex())
                if self.First_condition.currentIndex() == 1:
                    cycle.Charge = mass_unit_converter(self.Charge.text(),self.Charge_unit.currentIndex())

                if self.Energy_resid.isEnabled():
                    cycle.Energy_resid = power_unit_converter(self.Energy_resid.text(),self.Energy_resid_unit.currentIndex())
                else:
                    cycle.Energy_resid = 1
                    
                if self.Mass_resid.isEnabled():
                    cycle.Mass_resid = mass_unit_converter(self.Mass_resid.text(),self.Mass_resid_unit.currentIndex())
                else:
                    cycle.Mass_resid = 0.1
                    
                if self.Mass_flowrate_resid.isEnabled():
                    cycle.Mass_flowrate_resid = mass_flowrate_unit_converter(self.Mass_flowrate_resid.text(),self.Mass_flowrate_resid_unit.currentIndex())
                else:
                    cycle.Mass_flowrate_resid = 0.001
                    
                cycle.Cycle_mode_index = self.Cycle_mode.currentIndex()
                cycle.Expansion_device = self.Expansion_device.currentIndex()
                if self.Expansion_device.currentIndex() == 0:
                    cycle.Superheat_location = self.Superheat_location.currentIndex()
                    cycle.Superheat = temperature_diff_unit_converter(self.Superheat.text(),self.Superheat_unit.currentIndex())
                cycle.Solver = self.Solver.currentIndex()
                cycle.Pressire_resid = pressure_unit_converter(self.Pressire_resid.text(),self.Pressire_resid_unit.currentIndex())
                cycle.Tevap_guess_type = self.Tevap_guess_type.currentIndex()
                if self.Tevap_guess_type.currentIndex() == 1:
                    cycle.Tevap_guess = temperature_unit_converter(self.Tevap_guess.text(),self.Tevap_guess_unit.currentIndex())
                cycle.Tcond_guess_type = self.Tcond_guess_type.currentIndex()
                if self.Tcond_guess_type.currentIndex() == 1:
                    cycle.Tcond_guess = temperature_unit_converter(self.Tcond_guess.text(),self.Tcond_guess_unit.currentIndex())
                cycle.Ref_library_index = self.Ref_library.currentIndex()
                cycle.Test_cond = self.Test_Condition.currentText()
                cycle.accum_charge_per = self.accumulator_charge.value()/100.0
                
                cycle.Capacity_target = power_unit_converter(self.Capacity_target.text(),self.Capacity_target_unit.currentIndex())
                
                if hasattr(self,"selected_condenser_index"):
                    if self.Condenser_type.currentIndex() == 0:
                        filename = self.Fintube_list[self.selected_condenser_index][0]
                    elif self.Condenser_type.currentIndex() == 1:
                        filename = self.Microchannel_list[self.selected_condenser_index][0]
                    cycle.condenser_selected = filename
                if hasattr(self,"selected_evaporator_index"):
                    if self.Evaporator_type.currentIndex() == 0:
                        filename = self.Fintube_list[self.selected_evaporator_index][0]
                    elif self.Evaporator_type.currentIndex() == 1:
                        filename = self.Microchannel_list[self.selected_evaporator_index][0]
                    cycle.evaporator_selected = filename
                if hasattr(self,"selected_liquidline_index"):
                    filename = self.Line_list[self.selected_liquidline_index][0]
                    cycle.liquidline_selected = filename
                if hasattr(self,"selected_suctionline_index"):
                    filename = self.Line_list[self.selected_suctionline_index][0]
                    cycle.suctionline_selected = filename
                if hasattr(self,"selected_twophaseline_index"):
                    filename = self.Line_list[self.selected_twophaseline_index][0]
                    cycle.twophaseline_selected = filename
                if hasattr(self,"selected_dischargeline_index"):
                    filename = self.Line_list[self.selected_dischargeline_index][0]
                    cycle.dischargeline_selected = filename
                if hasattr(self,"selected_compressor_index"):
                    filename = self.Compressor_list[self.selected_compressor_index][0]
                    cycle.compressor_selected = filename
                if hasattr(self,"selected_capillary_index"):
                    filename = self.Capillary_list[self.selected_capillary_index][0]
                    cycle.capillary_selected = filename
                cycle_parametric_array = np.zeros([9,2],dtype=object)
                if hasattr(self,"parametric_cycle_data") and self.Parametric_cycle.checkState():
                    cycle_parametric_array[0] = [1,self.parametric_cycle_data]
                if hasattr(self,"parametric_capillary_data") and self.Parametric_capillary.checkState():
                    cycle_parametric_array[1] = [1,self.parametric_capillary_data]
                if hasattr(self,"parametric_compressor_data") and self.Parametric_compressor.checkState():
                    cycle_parametric_array[2] = [1,self.parametric_compressor_data]
                if hasattr(self,"parametric_liquid_data") and self.Parametric_liquid.checkState():
                    cycle_parametric_array[3] = [1,self.parametric_liquid_data]
                if hasattr(self,"parametric_2phase_data") and self.Parametric_2phase.checkState():
                    cycle_parametric_array[4] = [1,self.parametric_2phase_data]
                if hasattr(self,"parametric_suction_data") and self.Parametric_suction.checkState():
                    cycle_parametric_array[5] = [1,self.parametric_suction_data]
                if hasattr(self,"parametric_discharge_data") and self.Parametric_discharge.checkState():
                    cycle_parametric_array[6] = [1,self.parametric_discharge_data]
                if hasattr(self,"parametric_evaporator_data") and self.Parametric_evaporator.checkState():
                    cycle_parametric_array[7] = [1,self.parametric_evaporator_data]
                if hasattr(self,"parametric_condenser_data") and self.Parametric_condenser.checkState():
                    cycle_parametric_array[8] = [1,self.parametric_condenser_data]
                
                if any(cycle_parametric_array[:,0]):
                    cycle.parametric_data = cycle_parametric_array
                
                result = write_cycle_with_components_file(cycle,path)
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

    def open_cycle_with_components(self):
        quit_msg = "You will lose all current inputs. Continue?"
        reply = QMessageBox.question(self, 'Message', 
                         quit_msg, QMessageBox.Yes, QMessageBox.No)
    
        if reply == QMessageBox.Yes:
            path = QFileDialog.getOpenFileName(self, 'Open Cycle with components file',directory=load_last_location(),filter="Cycle file (*.cyclec);;All files (*.*)")[0]
            if path != "":
                save_last_location(path)
                result = read_cycle_with_components_file(path)
                if result[0]:
                    try:
                        self.load_database()
                        cycle = result[1]
                        self.load_fields(cycle)
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
        
    def check_design_button_clicked(self):
        self.Design_check_result.setText("")
        self.add_to_terminal("Checking design.....")
        self.checking_thread = QThread()
        self.solver_worker = check_design_object(self)
        self.solver_worker.moveToThread(self.checking_thread)
        self.checking_thread.started.connect(self.solver_worker.check_design_fn)
        self.solver_worker.finished.connect(self.finished_checking)
        self.checking_thread.start()
        self.Solve_button.setEnabled(False)
        self.Check_design_button.setEnabled(False)
        
    def finished_checking(self,message):
        if message[0]:
            self.Design_check_result.setText(message[1])
        else:
            self.raise_error_meesage(message[1])
        self.checking_thread.quit()
        self.Solve_button.setEnabled(True)
        self.Check_design_button.setEnabled(True)
        self.add_to_terminal("Finished checking design!")

    def actionDesign_Check_Properties_triggered(self):
        design_Check_Properties_window = Design_Check_Properties_Window(self)
        design_Check_Properties_window.exec_()

    def actionCompressor_to_physics_model_triggered(self):
        compressor_to_physics_window = Compressor_to_physics_Window(self)
        compressor_to_physics_window.exec_()

    def documentation_clicked(self):
        self.raise_error_meesage("Documentation is not available at the moment")

    def show_copyrights(self):
        aboutWindow = AboutWindow()
        aboutWindow.exec_()

    def load_parallel_processing_window(self):
        parallel_processing_window = Parallel_Processing_Window(self)
        parallel_processing_window.exec_()
        if hasattr(parallel_processing_window,"N_processes_passed"):
            self.N_Processes = parallel_processing_window.N_processes_passed

    def parametric_cycle_button_clicked(self):
        parametric_cycle_window = parametric_cycle_Window(self)
        parametric_cycle_window.refresh_ui([self.First_condition.currentIndex(),self.Expansion_device.currentIndex(),self.Energy_resid.isEnabled(),self.Pressire_resid.isEnabled(),self.Mass_flowrate_resid.isEnabled(),self.Mass_resid.isEnabled()])
        if hasattr(self,"parametric_cycle_data"):
            parametric_cycle_window.load_fields(self.parametric_cycle_data)
        parametric_cycle_window.exec_()
        if hasattr(parametric_cycle_window,"parametric_data"):
            if parametric_cycle_window.parametric_data is None:
                if hasattr(self,"parametric_cycle_data"):
                    delattr(self,"parametric_cycle_data")
            else:
                self.parametric_cycle_data = parametric_cycle_window.parametric_data
        self.create_parametric_data_table()
        
    def parametric_compressor_button_clicked(self):
        parametric_compressor_window = parametric_compressor_Window(self)
        parametric_compressor_window.refresh_ui(self.Comp_names)
        if hasattr(self,"parametric_compressor_data"):
            parametric_compressor_window.load_fields(self.parametric_compressor_data)
        parametric_compressor_window.exec_()
        if hasattr(parametric_compressor_window,"parametric_data"):
            if parametric_compressor_window.parametric_data is None:
                if hasattr(self,"parametric_compressor_data"):
                    delattr(self,"parametric_compressor_data")
            else:
                self.parametric_compressor_data = parametric_compressor_window.parametric_data
        self.create_parametric_data_table()

    def parametric_evaporator_button_clicked(self):
        if self.Cycle_mode.currentIndex() == 0:
            title = "Indoor Unit"
        elif self.Cycle_mode.currentIndex() == 1:
            title = "Outdoor Unit"
        if hasattr(self,"selected_evaporator_index"):
            if self.Evaporator_type.currentIndex() == 0:
                parametric_evaporator_window = parametric_fintube_Window(self)
                parametric_evaporator_window.refresh_ui(self.Fintube_list[self.selected_evaporator_index][1])
            elif self.Evaporator_type.currentIndex() == 1:
                parametric_evaporator_window = parametric_microchannel_Window(self)
                parametric_evaporator_window.refresh_ui(self.Microchannel_list[self.selected_evaporator_index][1])
            parametric_evaporator_window.setWindowTitle(title+ " Parametric Study")
            if hasattr(self,"parametric_evaporator_data"):
                parametric_evaporator_window.load_fields(self.parametric_evaporator_data)
            if hasattr(parametric_evaporator_window,"error_loading") and parametric_evaporator_window.error_loading:
                if hasattr(self,"parametric_evaporator_data"):
                    delattr(self,"parametric_evaporator_data")
                self.parametric_evaporator_button_clicked()
            else:    
                parametric_evaporator_window.exec_()
                if hasattr(parametric_evaporator_window,"parametric_data"):
                    if parametric_evaporator_window.parametric_data is None:
                        if hasattr(self,"parametric_evaporator_data"):
                            delattr(self,"parametric_evaporator_data")
                    else:
                        self.parametric_evaporator_data = parametric_evaporator_window.parametric_data
        else:
            self.raise_error_meesage("Please choose "+title+" first")
        self.create_parametric_data_table()

    def parametric_condenser_button_clicked(self):
        if self.Cycle_mode.currentIndex() == 0:
            title = "Outdoor Unit"
        elif self.Cycle_mode.currentIndex() == 1:
            title = "Indoor Unit"
        if hasattr(self,"selected_condenser_index"):
            if self.Condenser_type.currentIndex() == 0:
                parametric_condenser_window = parametric_fintube_Window(self)
                parametric_condenser_window.refresh_ui(self.Fintube_list[self.selected_condenser_index][1])
            elif self.Condenser_type.currentIndex() == 1:
                parametric_condenser_window = parametric_microchannel_Window(self)
                parametric_condenser_window.refresh_ui(self.Microchannel_list[self.selected_condenser_index][1])
            parametric_condenser_window.setWindowTitle(title+ " Parametric Study")
            if hasattr(self,"parametric_condenser_data"):
                parametric_condenser_window.load_fields(self.parametric_condenser_data)
            if hasattr(parametric_condenser_window,"error_loading") and parametric_condenser_window.error_loading:
                if hasattr(self,"parametric_condenser_data"):
                    delattr(self,"parametric_condenser_data")
                self.parametric_condenser_button_clicked()
            else:
                parametric_condenser_window.exec_()
                if hasattr(parametric_condenser_window,"parametric_data"):
                    if parametric_condenser_window.parametric_data is None:
                        if hasattr(self,"parametric_condenser_data"):
                            delattr(self,"parametric_condenser_data")
                    else:
                        self.parametric_condenser_data = parametric_condenser_window.parametric_data
        else:
            self.raise_error_meesage("Please choose "+title+" first")
        self.create_parametric_data_table()

    def parametric_capillary_button_clicked(self):
        parametric_capillary_window = parametric_capillary_Window(self)
        if hasattr(self,"parametric_capillary_data"):
            parametric_capillary_window.load_fields(self.parametric_capillary_data)
        parametric_capillary_window.exec_()
        if hasattr(parametric_capillary_window,"parametric_data"):
            if parametric_capillary_window.parametric_data is None:
                if hasattr(self,"parametric_capillary_data"):
                    delattr(self,"parametric_capillary_data")
            else:
                self.parametric_capillary_data = parametric_capillary_window.parametric_data
        self.create_parametric_data_table()

    def parametric_liquid_button_clicked(self):
        parametric_liquid_window = parametric_line_Window(self)
        parametric_liquid_window.setWindowTitle("Liquid Line Parametric Study")
        if hasattr(self,"parametric_liquid_data"):
            parametric_liquid_window.load_fields(self.parametric_liquid_data)
        parametric_liquid_window.exec_()
        if hasattr(parametric_liquid_window,"parametric_data"):
            if parametric_liquid_window.parametric_data is None:
                if hasattr(self,"parametric_liquid_data"):
                    delattr(self,"parametric_liquid_data")
            else:
                self.parametric_liquid_data = parametric_liquid_window.parametric_data
        self.create_parametric_data_table()

    def parametric_2phase_button_clicked(self):
        parametric_2phase_window = parametric_line_Window(self)
        parametric_2phase_window.setWindowTitle("Two-phase Line Parametric Study")
        if hasattr(self,"parametric_2phase_data"):
            parametric_2phase_window.load_fields(self.parametric_2phase_data)
        parametric_2phase_window.exec_()
        if hasattr(parametric_2phase_window,"parametric_data"):
            if parametric_2phase_window.parametric_data is None:
                if hasattr(self,"parametric_2phase_data"):
                    delattr(self,"parametric_2phase_data")
            else:
                self.parametric_2phase_data = parametric_2phase_window.parametric_data
        self.create_parametric_data_table()

    def parametric_suction_button_clicked(self):
        parametric_suction_window = parametric_line_Window(self)
        parametric_suction_window.setWindowTitle("Suction Line Parametric Study")
        if hasattr(self,"parametric_suction_data"):
            parametric_suction_window.load_fields(self.parametric_suction_data)
        parametric_suction_window.exec_()
        if hasattr(parametric_suction_window,"parametric_data"):
            if parametric_suction_window.parametric_data is None:
                if hasattr(self,"parametric_suction_data"):
                    delattr(self,"parametric_suction_data")
            else:
                self.parametric_suction_data = parametric_suction_window.parametric_data
        self.create_parametric_data_table()

    def parametric_discharge_button_clicked(self):
        parametric_discharge_window = parametric_line_Window(self)
        parametric_discharge_window.setWindowTitle("Discharge Line Parametric Study")
        if hasattr(self,"parametric_discharge_data"):
            parametric_discharge_window.load_fields(self.parametric_discharge_data)
        parametric_discharge_window.exec_()
        if hasattr(parametric_discharge_window,"parametric_data"):
            if parametric_discharge_window.parametric_data is None:
                if hasattr(self,"parametric_discharge_data"):
                    delattr(self,"parametric_discharge_data")
            else:
                self.parametric_discharge_data = parametric_discharge_window.parametric_data
        self.create_parametric_data_table()

    def parametric_cycle_check(self,state):
        if state:
            self.Parametric_cycle_button.setEnabled(True)
        else:
            self.Parametric_cycle_button.setEnabled(False)
        self.create_parametric_data_table()

    def parametric_compressor_check(self,state):
        if state:
            self.Parametric_compressor_button.setEnabled(True)
        else:
            self.Parametric_compressor_button.setEnabled(False)
        self.create_parametric_data_table()

    def parametric_condenser_check(self,state):
        if state:
            self.Parametric_condenser_button.setEnabled(True)
        else:
            self.Parametric_condenser_button.setEnabled(False)
        self.create_parametric_data_table()

    def parametric_evaporator_check(self,state):
        if state:
            self.Parametric_evaporator_button.setEnabled(True)
        else:
            self.Parametric_evaporator_button.setEnabled(False)
        self.create_parametric_data_table()
            
    def parametric_capillary_check(self,state):
        if state:
            self.Parametric_capillary_button.setEnabled(True)
        else:
            self.Parametric_capillary_button.setEnabled(False)
        self.create_parametric_data_table()

    def parametric_liquid_check(self,state):
        if state:
            self.Parametric_liquid_button.setEnabled(True)
        else:
            self.Parametric_liquid_button.setEnabled(False)
        self.create_parametric_data_table()

    def parametric_2phase_check(self,state):
        if state:
            self.Parametric_2phase_button.setEnabled(True)
        else:
            self.Parametric_2phase_button.setEnabled(False)
        self.create_parametric_data_table()

    def parametric_suction_check(self,state):
        if state:
            self.Parametric_suction_button.setEnabled(True)
        else:
            self.Parametric_suction_button.setEnabled(False)
        self.create_parametric_data_table()

    def parametric_discharge_check(self,state):
        if state:
            self.Parametric_discharge_button.setEnabled(True)
        else:
            self.Parametric_discharge_button.setEnabled(False)
        self.create_parametric_data_table()

    def load_fintube_simulation(self):
        fintube_simulation_window = Fintube_Simulation_Window(self)
        fintube_simulation_window.exec_()

    def load_microchannel_simulation(self):
        microchannel_simulation_window = Microchannel_Simulation_Window(self)
        microchannel_simulation_window.exec_()

    def load_line_simulation(self):
        line_simulation_window = Line_Simulation_Window(self)
        line_simulation_window.exec_()

    def load_capillary_simulation(self):
        capillary_simulation_window = Capillary_Simulation_Window(self)
        capillary_simulation_window.exec_()

    def load_compressor_simulation(self):
        compressor_simulation_window = Compressor_Simulation_Window(self)
        compressor_simulation_window.exec_()

    def load_example(self):
        capacity_check = self.capacity_check
        if self.capacity_check:
            self.capacity_check = False
        sender = self.sender().objectName()
        if sender == "actionR410A_Cycle_with_TXV":
            path = appdirs.user_data_dir("EGSim")+"\Examples\R410A_(TXV).cyclec"
        elif sender == "actionR22_Cycle_with_TXV":
            path = appdirs.user_data_dir("EGSim")+"\Examples\R22_(TXV).cyclec"
        elif sender == "actionR32_Cycle_with_TXV":
            path = appdirs.user_data_dir("EGSim")+"\Examples\R32_(TXV).cyclec"
        result = read_cycle_with_components_file(path)
        if result[0]:
            try:
                self.load_database()
                cycle = result[1]
                self.load_fields(cycle)
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setText("Cycle was loaded successfully")
                msg.setWindowTitle("Success!")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
            except:
                import traceback
                print(traceback.format_exc())
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("Cycle could not be loaded")
                msg.setWindowTitle("Sorry!")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Cycle could not be loaded")
            msg.setWindowTitle("Sorry!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        if capacity_check:
            self.capacity_check = True
            
    def open_REFPROP_properties(self):
        refprop_window = REFPROP_Properties_Window()
        refprop_window.exec_()
        self.load_REFPROP()
        
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

    def save_results_to_excel(self):
        if hasattr(self,"Result_Cycle"):
            result = self.Result_Cycle
            function = save_results_excel
            results_exist = True
        elif hasattr(self,"Result_outputs"):
            result = self.Result_outputs
            results_exist = False
            if not (result is None):
                results_exist = True
                result = [self.parametric_table_for_save_results]+result
                
            function = save_results_excel_parametric
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("There are no results to be saved")
            msg.setWindowTitle("Sorry!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            results_exist = False
        
        if results_exist:
            path = QFileDialog.getSaveFileName(self, caption='Save Results',directory=load_last_location(),filter="Excel file (*.xlsx);;All files (*.*)")[0]
            if path != "":
                if path[-5:].lower() != ".xlsx":
                    path = path+".xlsx"
                try:
                    succeeded = function(result,path)
                    if not succeeded:
                        raise
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("The file was saved successfully")
                    msg.setWindowTitle("Success!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                except:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("File could not be saved")
                    msg.setWindowTitle("Sorry!")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("There are no results to be saved")
            msg.setWindowTitle("Sorry!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            results_exist = False
            
    def change_style(self):
        quit_msg = "You will lose all current inputs. Continue?"
        reply = QMessageBox.question(self, 'Message',
                         quit_msg, QMessageBox.Yes, QMessageBox.No)
    
        if reply == QMessageBox.Yes:
            checked_text = [action.text() for action in self.menuStyle.actions() if action.isChecked()][0]
            self.change_style_signal_to_main.emit(checked_text)
            self.hide()
        
    def clear_terminal_button_clicked(self):
        self.Terminal.clear()

    def add_to_terminal(self,message):
        self.Terminal.addItem(datetime.datetime.now().strftime("%H:%M:%S: ")+message)
        self.Terminal.scrollToBottom()
        self.Terminal.setCurrentRow(self.Terminal.count()-1)

    def raise_error_meesage(self,message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(message)
        msg.setWindowTitle("Error!")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def solve_button(self):
        validation = self.validate()
        if validation == 0:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please fill all empty fields")
            msg.setWindowTitle("Empty Fields!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()

        elif validation == 2:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please choose all component of cycle configuration")
            msg.setWindowTitle("Empty components!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()

        elif validation == 3:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Could not load REFPORP library")
            msg.setWindowTitle("REFPROP error!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()

        elif validation == 4:
            pass
        
        elif validation == 1:
            self.disable_UI(True)
            if self.Test_Condition.currentIndex() != 0:
                self.raise_information_message("Please note that air inlet conditions for outdoor and indoor unit will be according to chosen test condition in 'Cycle Parameters' instead of specified conditions in heat exchanger definition or in 'Parametrics'.")
                
            if hasattr(self,"Result_Cycle"):
                delattr(self,"Result_Cycle")
            if self.Condenser_type.currentIndex() == 0:
                Condenser_type = 'Fintube'
                condenser = self.Fintube_list[self.selected_condenser_index][1]

            elif self.Condenser_type.currentIndex() == 1:
                Condenser_type = 'Microchannel'
                condenser = self.Microchannel_list[self.selected_condenser_index][1]
                
            if self.Evaporator_type.currentIndex() == 0:
                Evaporator_type = 'Fintube'
                evaporator = self.Fintube_list[self.selected_evaporator_index][1]

            elif self.Evaporator_type.currentIndex() == 1:
                Evaporator_type = 'Microchannel'
                evaporator = self.Microchannel_list[self.selected_evaporator_index][1]

            if self.First_condition.currentIndex() == 0:
                First_condition = 'subcooling'
                sc_value = temperature_diff_unit_converter(self.Subcooling.text(),self.Subcooling_unit.currentIndex())
                mass_tol = 0.0
                charge_value = 0.0
                
            elif self.First_condition.currentIndex() == 1:
                First_condition = 'charge'
                sc_value = 0.0
                mass_tol = mass_unit_converter(self.Mass_resid.text(),self.Mass_resid_unit.currentIndex())
                charge_value = mass_unit_converter(self.Charge.text(),self.Charge_unit.currentIndex())
                
            if self.Expansion_device.currentIndex() == 0:
                Expansion_device = 'TXV'
                if self.Superheat_location.currentIndex() == 0:
                    sh_location = "Evaporator"
                elif self.Superheat_location.currentIndex() == 1:
                    sh_location = "Compressor"
                sh_value = temperature_diff_unit_converter(self.Superheat.text(),self.Superheat_unit.currentIndex())
                mass_flowrate_tol = 0.0
                
            elif self.Expansion_device.currentIndex() == 1:                
                Expansion_device = 'capillary'
                sh_location = 0.0
                sh_value = 0.0
                mass_flowrate_tol = mass_flowrate_unit_converter(self.Mass_flowrate_resid.text(),self.Mass_flowrate_resid_unit.currentIndex())
                capillary = self.Capillary_list[self.selected_capillary_index][1]
                
            if self.Tevap_guess_type.currentIndex() == 0:
                Tevap_guess_type = 'auto'
                Tevap_guess = 0.0
            elif self.Tevap_guess_type.currentIndex() == 1:
                Tevap_guess_type = 'manual'
                Tevap_guess = temperature_unit_converter(self.Tevap_guess.text(),self.Tevap_guess_unit.currentIndex())

            if self.Tcond_guess_type.currentIndex() == 0:
                Tcond_guess_type = 'auto'
                Tcond_guess = 0.0
                
            elif self.Tcond_guess_type.currentIndex() == 1:
                Tcond_guess_type = 'manual'
                Tcond_guess = temperature_unit_converter(self.Tcond_guess.text(),self.Tcond_guess_unit.currentIndex())

            if self.Cycle_mode.currentIndex() == 0:
                Cycle_mode = 'AC'
                
            elif self.Cycle_mode.currentIndex() == 1:
                Cycle_mode = 'HP'

            if self.Ref_library.currentIndex() == 0:
                Ref_library = 'REFPROP'
                
            elif self.Ref_library.currentIndex() == 1:
                Ref_library = 'HEOS'
            
            if hasattr(self,"refprop_path"):
                refprop_path = self.refprop_path
            else:
                refprop_path = ""
            
            if self.Energy_resid.text() != "":
                energy_resid = power_unit_converter(self.Energy_resid.text(),self.Energy_resid_unit.currentIndex())
            else:
                energy_resid = 0
                
            options = {'parametric':False,
                       'refrigerant': self.Cycle_refrigerant.currentText(),
                       'condenser_type': Condenser_type,
                       'evaporator_type': Evaporator_type,
                       'first_condition': First_condition,
                       'sc_value': sc_value,
                       'charge_value': charge_value,
                       'expansion_type': Expansion_device,
                       'sh_location': sh_location,
                       'sh_value': sh_value,
                       'mass_flowrate_tol': mass_flowrate_tol,
                       'mass_tol': mass_tol,
                       'solver': self.Solver.currentText(),
                       'energy_tol': energy_resid,
                       'max_n_iterations': self.Max_N_iterations.value(),
                       'pressure_tol': pressure_unit_converter(self.Pressire_resid.text(),self.Pressire_resid_unit.currentIndex()),
                       'Tevap_guess_type': Tevap_guess_type,
                       'Tevap_guess': Tevap_guess,
                       'Tcond_guess_type': Tcond_guess_type,
                       'Tcond_guess': Tcond_guess,
                       'N_processes': self.N_Processes,
                       'Cycle_mode': Cycle_mode,
                       'Ref_library': Ref_library,
                       'refprop_path': refprop_path,
                       'Test_cond': self.Test_Condition.currentText(),
                       'Accum_charge_per': self.accumulator_charge.value()/100,
                }

            # check for parametric study
            parametric_array = np.zeros([9,2],dtype=object)
            if hasattr(self,"parametric_cycle_data") and self.Parametric_cycle.checkState():
                parametric_array[0,:] = [1,self.parametric_cycle_data]
            if hasattr(self,"parametric_capillary_data") and self.Parametric_capillary.checkState():
                parametric_array[1,:] = [1,self.parametric_capillary_data]
            if hasattr(self,"parametric_compressor_data") and self.Parametric_compressor.checkState():
                compressor_parametric = self.parametric_compressor_data.copy()
                if compressor_parametric[6,0]:
                    compressor_parametric[6,1] = [self.Compressor_list[i] for i in compressor_parametric[6,1]]
                parametric_array[2,:] = [1,compressor_parametric]
            if hasattr(self,"parametric_liquid_data") and self.Parametric_liquid.checkState():
                parametric_array[3,:] = [1,self.parametric_liquid_data]
            if hasattr(self,"parametric_2phase_data") and self.Parametric_2phase.checkState():
                parametric_array[4,:] = [1,self.parametric_2phase_data]
            if hasattr(self,"parametric_suction_data") and self.Parametric_suction.checkState():
                parametric_array[5,:] = [1,self.parametric_suction_data]
            if hasattr(self,"parametric_discharge_data") and self.Parametric_discharge.checkState():
                parametric_array[6,:] = [1,self.parametric_discharge_data]
            if hasattr(self,"parametric_evaporator_data") and self.Parametric_evaporator.checkState():
                parametric_array[7,:] = [1,self.parametric_evaporator_data]
            if hasattr(self,"parametric_condenser_data") and self.Parametric_condenser.checkState():
                parametric_array[8,:] = [1,self.parametric_condenser_data]
            if any(parametric_array[:,0]):
                options['parametric'] = True
                options['parametric_array'] = parametric_array
                self.Energy_residual_condenser_update.setEnabled(False)
                self.Energy_residual_evaporator_update.setEnabled(False)
                self.mass_flowrate_residual_update.setEnabled(False)
                self.pressure_residual_residual_update.setEnabled(False)
                self.mass_residual_update.setEnabled(False)

            self.parametric_study = options['parametric']
            compressor = self.Compressor_list[self.selected_compressor_index][1]
            liquid_line = self.Line_list[self.selected_liquidline_index][1]
            twophase_line = self.Line_list[self.selected_twophaseline_index][1]
            suction_line = self.Line_list[self.selected_suctionline_index][1]
            discharge_line = self.Line_list[self.selected_dischargeline_index][1]
            if self.Expansion_device.currentIndex() == 1:
                components = [compressor, condenser, evaporator, liquid_line,
                              twophase_line, suction_line, discharge_line, 
                              capillary]
            elif self.Expansion_device.currentIndex() == 0:
                components = [compressor, condenser, evaporator, liquid_line,
                              twophase_line, suction_line, discharge_line]                
            number_of_tabs = self.tabWidget.count()
            if number_of_tabs == 5:
                self.tabWidget.removeTab(number_of_tabs-1)
            self.Energy_residual_condenser_update.setText("")
            self.Energy_residual_evaporator_update.setText("")
            self.mass_flowrate_residual_update.setText("")
            self.pressure_residual_residual_update.setText("")
            self.mass_residual_update.setText("")
            self.add_to_terminal("Starting a new run")
            self.solving_thread = QThread()
            self.solver_worker = solver(components,options)
            self.solver_worker.moveToThread(self.solving_thread)
            self.solving_thread.started.connect(self.solver_worker.run)
            self.solver_worker.input_error.connect(self.raise_error_meesage)
            self.solver_worker.terminal_message.connect(self.add_to_terminal)
            self.solver_worker.update_residuals.connect(self.update_residuals)
            self.solver_worker.finished.connect(self.finished_run)
            self.solving_thread.start()
            self.Stop_button.setEnabled(True)
            self.Solve_button.setEnabled(False)
            self.Check_design_button.setEnabled(False)

    def update_residuals(self,residuals):
        if residuals[1] != None:
            self.Energy_residual_condenser_update.setText(str(round(residuals[1],6)))
        if residuals[2] != None:
            self.Energy_residual_evaporator_update.setText(str(round(residuals[2],6)))
        if residuals[3] != None:
            self.mass_flowrate_residual_update.setText(str(round(residuals[3],6)))
        if residuals[4] != None:
            self.mass_residual_update.setText(str(round(residuals[4],6)))
        if residuals[5] != None:
            self.pressure_residual_residual_update.setText(str(round(residuals[5],6)))
        
    def finished_run(self,results):
        result = results[0]
        if not result:
            self.add_to_terminal(results[1])
            self.add_to_terminal("-------------------------")
        else:
            if self.parametric_study:
                self.Result_outputs = results[2]
                Once = False
                if not (self.Result_outputs is None):
                    self.results_creator_parametric()
                self.add_to_terminal(results[1])
                Calculation_time = round(results[3],3)
            else:
                self.Result_Cycle = results[2]
                if self.Result_Cycle.Create_ranges and hasattr(self.Result_Cycle,"Validation_ranges") and self.Result_Cycle.Validation_ranges != None:
                    self.Validation_ranges = self.Result_Cycle.Validation_ranges
                    self.validation_range = self.Validation_ranges.Cycle
                    self.Validation_ranges.Evaporator.Component = self.selected_evaporator_filename
                    self.Validation_ranges.Condenser.Component = self.selected_condenser_filename
                    self.enable_range_validation()
                    
                self.results_creator_single()
                self.add_to_terminal(results[1])
                Calculation_time = round(self.Result_Cycle.CalculationTime,3)
                
            self.add_to_terminal("Calculation time: "+str(Calculation_time)+" seconds")
            self.add_to_terminal("-------------------------")
        self.solving_thread.quit()
        self.Stop_button.setEnabled(False)
        self.Solve_button.setEnabled(True)
        self.Check_design_button.setEnabled(True)
        self.disable_UI(False)
        self.update_residuals_options()

    def results_creator_single(self):
        layout = QHBoxLayout(self)
        if self.Cycle_mode.currentIndex() == 0:
            mode = "AC"
        elif self.Cycle_mode.currentIndex() == 1:
            mode = "HP"
        self.Results_tabs_widget = ResultsTabsWidget(Cycles=self.Result_Cycle, mode=mode)
        layout.addWidget(self.Results_tabs_widget)
        self.Results_tab = QWidget()
        self.Results_tab.setLayout(layout)
        self.tabWidget.addTab(self.Results_tab,"Results")
        number_of_tabs = self.tabWidget.count()
        self.tabWidget.setCurrentIndex(number_of_tabs-1)

    def results_creator_parametric(self):
        self.parametric_table_for_save_results = create_parametric_data_table_to_export(self.parametric_data_table_instance)
        
        layout = QHBoxLayout(self)
        if self.Cycle_mode.currentIndex() == 0:
            mode = "AC"
        elif self.Cycle_mode.currentIndex() == 1:
            mode = "HP"
        if self.Condenser_type.currentIndex() == 0:
            Condenser_type = "Fin-tube"
            N_condenser_circuits = len(self.Fintube_list[self.selected_condenser_index][1].circuits)
        else:
            Condenser_type = "Microchannel"
            N_condenser_circuits = 1
        if self.Evaporator_type.currentIndex() == 0:
            Evaporator_type = "Fin-tube"
            N_evaporator_circuits = len(self.Fintube_list[self.selected_evaporator_index][1].circuits)
        else:
            Evaporator_type = "Microchannel"
            N_evaporator_circuits = 1
        if self.Expansion_device.currentIndex() == 1:
            Capillary = True
        else:
            Capillary = False
            
        parameters = {'Condenser_Type':Condenser_type,
                      'Evaporator_Type':Evaporator_type,
                      'Capillary':Capillary,
                      'N_condenser_circuits':N_condenser_circuits,
                      'N_evaporator_circuits':N_evaporator_circuits,
                      }
        self.Results_tabs_widget = ResultsTabsWidget(outputs=self.Result_outputs,parameters=parameters,mode=mode)
        layout.addWidget(self.Results_tabs_widget)
        self.Results_tab = QWidget()
        self.Results_tab.setLayout(layout)
        self.tabWidget.addTab(self.Results_tab,"Results")
        number_of_tabs = self.tabWidget.count()
        self.tabWidget.setCurrentIndex(number_of_tabs-1)
        
    def stop_button(self):
        try:
            if self.parametric_study:
                self.solver_worker.terminate = True
                self.add_to_terminal("User terminated parametric study!")
            else:
                self.solver_worker.Cycle.check_terminate = True
            self.Stop_button.setEnabled(False)
        except:
            pass
    
    def disable_UI(self,disabled):
        if disabled:
            for i in range(3):
                self.tabWidget.setTabEnabled(i, False)
                self.menubar.setEnabled(False)
        else:
            for i in range(3):
                self.tabWidget.setTabEnabled(i, True)
                self.menubar.setEnabled(True)

    def refrigerant_changed(self):
        if hasattr(self,"selected_compressor_index"):
            delattr(self,"selected_compressor_index")
            delattr(self,"selected_compressor_filename")
        self.delete_validation_range()
        self.refresh_selected_components()

    def import_database(self):
        quit_msg = "THIS WILL DELETE CURRENT DATABASE. Are you sure?"
        reply = QMessageBox.warning(self, 'Message', 
                         quit_msg, QMessageBox.Yes, QMessageBox.No)
    
        if reply == QMessageBox.Yes:
            path = QFileDialog.getOpenFileName(self, 'Open Database file',directory=load_last_location(),filter="Database file (*.database);;All files (*.*)")[0]
            if path != "":
                save_last_location(path)
                try:
                    os.mkdir(self.database_path+'old_database')
                    _, _, files = next(os.walk(self.database_path))
                    for file in files:
                        os.rename(self.database_path+file, self.database_path+'old_database/'+file)
                    database_zip = zipfile.ZipFile(path)
                    database_zip.extractall(self.database_path)
                    database_zip.close()
                    shutil.rmtree(self.database_path+"old_database")
                    self.load_database()
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
                    try:
                        _, _, files = next(os.walk(self.database_path+'old_database'))
                        for file in files:
                            os.rename(self.database_path+'old_database/'+file, self.database_path+file)
                        shutil.rmtree(self.database_path+"old_database")
                        self.load_database()
                    except:
                        self.load_database()
                        
                if hasattr(self,"selected_condenser_index"):
                    delattr(self,"selected_condenser_index")
                    delattr(self,"selected_condenser_filename")
                if hasattr(self,"selected_evaporator_index"):
                    delattr(self,"selected_evaporator_index")
                    delattr(self,"selected_evaporator_filename")
                if hasattr(self,"selected_liquidline_index"):
                    delattr(self,"selected_liquidline_index")
                    delattr(self,"selected_liquidline_filename")
                if hasattr(self,"selected_suctionline_index"):
                    delattr(self,"selected_suctionline_index")
                    delattr(self,"selected_suctionline_filename")
                if hasattr(self,"selected_twophaseline_index"):
                    delattr(self,"selected_twophaseline_index")
                    delattr(self,"selected_twophaseline_filename")
                if hasattr(self,"selected_dischargeline_index"):
                    delattr(self,"selected_dischargeline_index")
                    delattr(self,"selected_dischargeline_filename")
                if hasattr(self,"selected_compressor_index"):
                    delattr(self,"selected_compressor_index")
                    delattr(self,"selected_compressor_filename")
                if hasattr(self,"selected_capillary_index"):
                    delattr(self,"selected_capillary_index")
                    delattr(self,"selected_capillary_filename")

                if hasattr(self,"parametric_cycle_data"):
                    delattr(self,"parametric_cycle_data")
                if hasattr(self,"parametric_capillary_data"):
                    delattr(self,"parametric_capillary_data")
                if hasattr(self,"parametric_compressor_data"):
                    delattr(self,"parametric_compressor_data")
                if hasattr(self,"parametric_liquid_data"):
                    delattr(self,"parametric_liquid_data")
                if hasattr(self,"parametric_2phase_data"):
                    delattr(self,"parametric_2phase_data")
                if hasattr(self,"parametric_suction_data"):
                    delattr(self,"parametric_suction_data")
                if hasattr(self,"parametric_discharge_data"):
                    delattr(self,"parametric_discharge_data")
                if hasattr(self,"parametric_evaporator_data"):
                    delattr(self,"parametric_evaporator_data")
                if hasattr(self,"parametric_condenser_data"):
                    delattr(self,"parametric_condenser_data")
                self.create_parametric_data_table()                
                self.refresh_selected_components()
                        
    def export_database(self):
        path = QFileDialog.getSaveFileName(self, 'Save Database file',directory=load_last_location(),filter="Database file (*.database);;All files (*.*)")[0]
        if path != "":
            save_last_location(path)
            if path[-9:].lower() != ".database":
                path = path+".database"
            try:
                _, _, files = next(os.walk(self.database_path))
                database_zip = zipfile.ZipFile(path, 'w')
                for file in files:    
                    database_zip.write(self.database_path+file, file, compress_type=zipfile.ZIP_DEFLATED)
                
                database_zip.close()                
                
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setText("The file was saved successfully")
                msg.setWindowTitle("Success!")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
            except:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("File could not be saved")
                msg.setWindowTitle("Sorry!")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()

    def condenser_type_changed(self):
        if hasattr(self,"selected_condenser_index"):
            delattr(self,"selected_condenser_index")
            delattr(self,"selected_condenser_filename")
        if hasattr(self,"parametric_condenser_data"):
            delattr(self,"parametric_condenser_data")
        self.delete_validation_range()
        self.create_parametric_data_table()
        self.refresh_selected_components()

    def evaporator_type_changed(self):
        if hasattr(self,"selected_evaporator_index"):
            delattr(self,"selected_evaporator_index")
            delattr(self,"selected_evaporator_filename")
        if hasattr(self,"parametric_evaporator_data"):
            delattr(self,"parametric_evaporator_data")
        self.delete_validation_range()
        self.create_parametric_data_table()
        self.refresh_selected_components()

    def select_component(self):
        sender_name = self.sender().objectName()
        if sender_name == "Condenser_select_button":
            self.update_capacity_validation_table()
            if self.Condenser_type.currentIndex() == 0:
                select_component_window = Component_selection("Fintube",self)
                if self.capacity_validation:
                    select_component_window.capacity_validation = True
                    select_component_window.capacity_validation_table = self.capacity_validation_table                
                    select_component_window.capacity_validation_table["HX_type"] = "cond"
                else:
                    select_component_window.capacity_validation = False
                if hasattr(self,"selected_condenser_index"):
                    select_component_window.Components_list.setCurrentRow(self.selected_condenser_index)
                
                if hasattr(self,"Validation_ranges"):
                    select_component_window.condenser_validation_range = self.Validation_ranges.Condenser
                    
                select_component_window.exec_()

                if select_component_window.Delete_validation_range:
                    self.delete_validation_range()

                if hasattr(select_component_window,"selected_component"):
                    self.selected_condenser_index = select_component_window.selected_component
                    
                    if hasattr(self,"selected_condenser_filename"):
                        old_selected_condenser_filename = str(self.selected_condenser_filename)
                    else:
                        old_selected_condenser_filename = ""
                    
                    self.selected_condenser_filename = self.Fintube_list[select_component_window.selected_component][0]
                    if old_selected_condenser_filename != self.selected_condenser_filename:
                        self.delete_validation_range()
                    if hasattr(self,"parametric_condenser_data"):
                        delattr(self,"parametric_condenser_data")
                        
            elif self.Condenser_type.currentIndex() == 1:
                select_component_window = Component_selection("Microchannel",self)
                if hasattr(self,"selected_condenser_index"):
                    select_component_window.Components_list.setCurrentRow(self.selected_condenser_index)

                if hasattr(self,"Validation_ranges"):
                    select_component_window.condenser_validation_range = self.Validation_ranges.Condenser

                select_component_window.exec_()

                if select_component_window.Delete_validation_range:
                    self.delete_validation_range()

                if hasattr(select_component_window,"selected_component"):
                    self.selected_condenser_index = select_component_window.selected_component

                    if hasattr(self,"selected_condenser_filename"):
                        old_selected_condenser_filename = str(self.selected_condenser_filename)
                    else:
                        old_selected_condenser_filename = ""

                    self.selected_condenser_filename = self.Microchannel_list[select_component_window.selected_component][0]
                    if old_selected_condenser_filename != self.selected_condenser_filename:
                        self.delete_validation_range()
                    if hasattr(self,"parametric_condenser_data"):
                        delattr(self,"parametric_condenser_data")

        elif sender_name == "Evaporator_select_button":
            if self.Evaporator_type.currentIndex() == 0:
                select_component_window = Component_selection("Fintube",self)
                self.update_capacity_validation_table()
                if self.capacity_validation:
                    select_component_window.capacity_validation = True
                    select_component_window.capacity_validation_table = self.capacity_validation_table                
                    select_component_window.capacity_validation_table["HX_type"] = "evap"
                else:
                    select_component_window.capacity_validation = False
                if hasattr(self,"selected_evaporator_index"):
                    select_component_window.Components_list.setCurrentRow(self.selected_evaporator_index)

                if hasattr(self,"Validation_ranges"):
                    select_component_window.evaporator_validation_range = self.Validation_ranges.Evaporator
                

                select_component_window.exec_()

                if select_component_window.Delete_validation_range:
                    self.delete_validation_range()

                if hasattr(select_component_window,"selected_component"):
                    self.selected_evaporator_index = select_component_window.selected_component

                    if hasattr(self,"selected_evaporator_filename"):
                        old_selected_evaporator_filename = str(self.selected_evaporator_filename)
                    else:
                        old_selected_evaporator_filename = ""

                    self.selected_evaporator_filename = self.Fintube_list[select_component_window.selected_component][0]
                    if old_selected_evaporator_filename != self.selected_evaporator_filename:
                        self.delete_validation_range()
                    if hasattr(self,"parametric_evaporator_data"):
                        delattr(self,"parametric_evaporator_data")

            elif self.Evaporator_type.currentIndex() == 1:
                select_component_window = Component_selection("Microchannel",self)
                self.update_capacity_validation_table()
                if self.capacity_validation:
                    select_component_window.capacity_validation = True
                    select_component_window.capacity_validation_table = self.capacity_validation_table                
                    select_component_window.capacity_validation_table["HX_type"] = "evap"
                else:
                    select_component_window.capacity_validation = False
                if hasattr(self,"selected_evaporator_index"):
                    select_component_window.Components_list.setCurrentRow(self.selected_evaporator_index)

                if hasattr(self,"Validation_ranges"):
                    select_component_window.evaporator_validation_range = self.Validation_ranges.Evaporator

                select_component_window.exec_()

                if select_component_window.Delete_validation_range:
                    self.delete_validation_range()

                if hasattr(select_component_window,"selected_component"):
                    self.selected_evaporator_index = select_component_window.selected_component
                    if hasattr(self,"selected_evaporator_filename"):
                        old_selected_evaporator_filename = str(self.selected_evaporator_filename)
                    else:
                        old_selected_evaporator_filename = ""
                    self.selected_evaporator_filename = self.Microchannel_list[select_component_window.selected_component][0]
                    if old_selected_evaporator_filename != self.selected_evaporator_filename:
                        self.delete_validation_range()
                    if hasattr(self,"parametric_evaporator_data"):
                        delattr(self,"parametric_evaporator_data")

        elif sender_name == "LiquidLine_select_button":
            select_component_window = Component_selection("LiquidLine",self)
            if hasattr(self,"selected_liquidline_index"):
                select_component_window.Components_list.setCurrentRow(self.selected_liquidline_index)
            select_component_window.exec_()
            if hasattr(select_component_window,"selected_component"):
                self.selected_liquidline_index = select_component_window.selected_component

                if hasattr(self,"selected_liquidline_filename"):
                    old_selected_liquidline_filename = str(self.selected_liquidline_filename)
                else:
                    old_selected_liquidline_filename = ""

                old_selected_liquidline_filename = str(self.selected_liquidline_index)
                self.selected_liquidline_filename = self.Line_list[select_component_window.selected_component][0]
                
                if old_selected_liquidline_filename != self.selected_liquidline_filename:
                    self.delete_validation_range()

        elif sender_name == "SuctionLine_select_button":
            select_component_window = Component_selection("SuctionLine",self)
            if hasattr(self,"selected_suctionline_index"):
                select_component_window.Components_list.setCurrentRow(self.selected_suctionline_index)
            select_component_window.exec_()
            if hasattr(select_component_window,"selected_component"):
                self.selected_suctionline_index = select_component_window.selected_component

                if hasattr(self,"selected_suctionline_filename"):
                    old_selected_suctionline_filename = str(self.selected_suctionline_filename)
                else:
                    old_selected_suctionline_filename = ""

                self.selected_suctionline_filename = self.Line_list[select_component_window.selected_component][0]

                if old_selected_suctionline_filename != self.selected_suctionline_filename:
                    self.delete_validation_range()

        elif sender_name == "TwophaseLine_select_button":
            select_component_window = Component_selection("TwophaseLine",self)
            if hasattr(self,"selected_twophaseline_index"):
                select_component_window.Components_list.setCurrentRow(self.selected_twophaseline_index)
            select_component_window.exec_()
            if hasattr(select_component_window,"selected_component"):
                self.selected_twophaseline_index = select_component_window.selected_component

                if hasattr(self,"selected_twophaseline_filename"):
                    old_selected_twophaseline_filename = str(self.selected_twophaseline_filename)
                else:
                    old_selected_twophaseline_filename = ""

                self.selected_twophaseline_filename = self.Line_list[select_component_window.selected_component][0]

                if old_selected_twophaseline_filename != self.selected_twophaseline_filename:
                    self.delete_validation_range()

        elif sender_name == "DischargeLine_select_button":
            select_component_window = Component_selection("DischargeLine",self)
            if hasattr(self,"selected_dischargeline_index"):
                select_component_window.Components_list.setCurrentRow(self.selected_dischargeline_index)
            select_component_window.exec_()
            if hasattr(select_component_window,"selected_component"):
                self.selected_dischargeline_index = select_component_window.selected_component

                if hasattr(self,"selected_dischargeline_filename"):
                    old_selected_dischargeline_filename = str(self.selected_dischargeline_filename)
                else:
                    old_selected_dischargeline_filename = ""

                self.selected_dischargeline_filename = self.Line_list[select_component_window.selected_component][0]

                if old_selected_dischargeline_filename != self.selected_dischargeline_filename:
                    self.delete_validation_range()
            
        elif sender_name == "Compressor_select_button":
            select_component_window = Component_selection("Compressor",self)
            select_component_window.chosen_ref = self.Cycle_refrigerant.currentText()
            if hasattr(self,"selected_compressor_index"):
                select_component_window.Components_list.setCurrentRow(self.selected_compressor_index)
            self.update_capacity_validation_table()
            if self.capacity_validation:
                select_component_window.capacity_validation = True
                select_component_window.capacity_validation_table = self.capacity_validation_table                
            else:
                select_component_window.capacity_validation = False
                
            select_component_window.exec_()
            if hasattr(select_component_window,"selected_component"):
                self.selected_compressor_index = select_component_window.selected_component

                if hasattr(self,"selected_compressor_filename"):
                    old_selected_compressor_filename = str(self.selected_compressor_filename)
                else:
                    old_selected_compressor_filename = ""

                self.selected_compressor_filename = self.Compressor_list[select_component_window.selected_component][0]

                if old_selected_compressor_filename != self.selected_compressor_filename:
                    self.delete_validation_range()

        elif sender_name == "Expansion_select_button":
            select_component_window = Component_selection("Capillary",self)
            if hasattr(self,"selected_capillary_index"):
                select_component_window.Components_list.setCurrentRow(self.selected_capillary_index)
            select_component_window.exec_()
            if hasattr(select_component_window,"selected_component"):
                self.selected_capillary_index = select_component_window.selected_component
                self.selected_capillary_filename = self.Capillary_list[select_component_window.selected_component][0]
            
        self.refresh_selected_components()
        self.create_parametric_data_table()

    def refresh_selected_components(self):
        try:
            self.load_database()
            if hasattr(self,"selected_condenser_index"):
                if hasattr(self,"selected_condenser_filename"):
                    if not os.path.exists(self.database_path+self.selected_condenser_filename):
                        delattr(self,"selected_condenser_index")
                        delattr(self,"selected_condenser_filename")
                        self.refresh_selected_components()
                    else:
                        if self.Condenser_type.currentIndex() == 0:
                            Condenser_name = self.Fintube_list[self.selected_condenser_index][1].name
                            self.Condenser_selected_name.setText(Condenser_name)
                        elif self.Condenser_type.currentIndex() == 1:
                            Condenser_name = self.Microchannel_list[self.selected_condenser_index][1].name
                            self.Condenser_selected_name.setText(Condenser_name)
                        self.Condenser_selected_name.setStyleSheet("background:#75BB2B;")
                else:
                    delattr(self,"selected_condenser_index")
                    delattr(self,"selected_condenser_filename")
                    self.refresh_selected_components()                    
            else:
                self.Condenser_selected_name.setText("No Condenser Selected")
                self.Condenser_selected_name.setStyleSheet("background:#E55D3F;")
    
            if hasattr(self,"selected_evaporator_index"):
                if hasattr(self,"selected_evaporator_filename"):
                    if not os.path.exists(self.database_path+self.selected_evaporator_filename):
                        delattr(self,"selected_evaporator_index")
                        delattr(self,"selected_evaporator_filename")
                        self.refresh_selected_components()
                    else:
                        if self.Evaporator_type.currentIndex() == 0:
                            Evaporator_name = self.Fintube_list[self.selected_evaporator_index][1].name
                            self.Evaporator_selected_name.setText(Evaporator_name)
                        elif self.Evaporator_type.currentIndex() == 1:
                            Evaporator_name = self.Microchannel_list[self.selected_evaporator_index][1].name
                            self.Evaporator_selected_name.setText(Evaporator_name)
                        self.Evaporator_selected_name.setStyleSheet("background:#75BB2B;")
                else:
                    delattr(self,"selected_evaporator_index")
                    delattr(self,"selected_evaporator_filename")
                    self.refresh_selected_components()                    
            else:
                self.Evaporator_selected_name.setText("No Evaporator Selected")
                self.Evaporator_selected_name.setStyleSheet("background:#E55D3F;")
    
            if hasattr(self,"selected_suctionline_index"):
                if hasattr(self,"selected_suctionline_filename"):
                    if not os.path.exists(self.database_path+self.selected_suctionline_filename):
                        delattr(self,"selected_suctionline_index")
                        delattr(self,"selected_suctionline_filename")
                        self.refresh_selected_components()
                    else:
                        Line_name = self.Line_list[self.selected_suctionline_index][1].Line_name
                        self.SuctionLine_selected_name.setText(Line_name)
                        self.SuctionLine_selected_name.setStyleSheet("background:#75BB2B;")
                else:
                    delattr(self,"selected_suctionline_index")
                    delattr(self,"selected_suctionline_filename")
                    self.refresh_selected_components()                    
            else:
                self.SuctionLine_selected_name.setText("No Suction Line Selected")
                self.SuctionLine_selected_name.setStyleSheet("background:#E55D3F;")
    
            if hasattr(self,"selected_dischargeline_index"):
                if hasattr(self,"selected_dischargeline_filename"):
                    if not os.path.exists(self.database_path+self.selected_dischargeline_filename):
                        delattr(self,"selected_dischargeline_index")
                        delattr(self,"selected_dischargeline_filename")
                        self.refresh_selected_components()
                    else:
                        Line_name = self.Line_list[self.selected_dischargeline_index][1].Line_name
                        self.DischargeLine_selected_name.setText(Line_name)
                        self.DischargeLine_selected_name.setStyleSheet("background:#75BB2B;")
                else:
                    delattr(self,"selected_dischargeline_index")
                    delattr(self,"selected_dischargeline_filename")
                    self.refresh_selected_components()                    
            else:
                self.DischargeLine_selected_name.setText("No Discharge Line Selected")
                self.DischargeLine_selected_name.setStyleSheet("background:#E55D3F;")
    
            if hasattr(self,"selected_twophaseline_index"):
                if hasattr(self,"selected_twophaseline_filename"):
                    if not os.path.exists(self.database_path+self.selected_twophaseline_filename):
                        delattr(self,"selected_twophaseline_index")
                        delattr(self,"selected_twophaseline_filename")
                        self.refresh_selected_components()
                    else:
                        Line_name = self.Line_list[self.selected_twophaseline_index][1].Line_name
                        self.TwophaseLine_selected_name.setText(Line_name)
                        self.TwophaseLine_selected_name.setStyleSheet("background:#75BB2B;")
                else:
                    delattr(self,"selected_twophaseline_index")
                    delattr(self,"selected_twophaseline_filename")
                    self.refresh_selected_components()                    
            else:
                self.TwophaseLine_selected_name.setText("No Two-phase Line Selected")
                self.TwophaseLine_selected_name.setStyleSheet("background:#E55D3F;")
    
            if hasattr(self,"selected_liquidline_index"):
                if hasattr(self,"selected_liquidline_filename"):
                    if not os.path.exists(self.database_path+self.selected_liquidline_filename):
                        delattr(self,"selected_liquidline_index")
                        delattr(self,"selected_liquidline_filename")
                        self.refresh_selected_components()
                    else:
                        Line_name = self.Line_list[self.selected_liquidline_index][1].Line_name
                        self.LiquidLine_selected_name.setText(Line_name)
                        self.LiquidLine_selected_name.setStyleSheet("background:#75BB2B;")
                else:
                    delattr(self,"selected_liquidline_index")
                    delattr(self,"selected_liquidline_filename")
                    self.refresh_selected_components()                    
            else:
                self.LiquidLine_selected_name.setText("No Liquid Line Selected")
                self.LiquidLine_selected_name.setStyleSheet("background:#E55D3F;")
    
            if hasattr(self,"selected_compressor_index"):
                if hasattr(self,"selected_compressor_filename"):
                    if not os.path.exists(self.database_path+self.selected_compressor_filename):
                        delattr(self,"selected_compressor_index")
                        delattr(self,"selected_compressor_filename")
                        self.refresh_selected_components()
                    else:
                        Comp_name = self.Compressor_list[self.selected_compressor_index][1].Comp_name
                        self.Compressor_selected_name.setText(Comp_name)
                        self.Compressor_selected_name.setStyleSheet("background:#75BB2B;")
                else:
                    delattr(self,"selected_compressor_index")
                    delattr(self,"selected_compressor_filename")
                    self.refresh_selected_components()                    
            else:
                self.Compressor_selected_name.setText("No Compressor Selected")
                self.Compressor_selected_name.setStyleSheet("background:#E55D3F;")
    
            if self.Expansion_device.currentIndex() == 0:
                self.Expansion_selected_name.setText("Constant Superheat")
                self.Expansion_selected_name.setStyleSheet("background:#75BB2B;")
            elif self.Expansion_device.currentIndex() == 1:
                if hasattr(self,"selected_capillary_index"):
                    if hasattr(self,"selected_capillary_filename"):
                        if not os.path.exists(self.database_path+self.selected_capillary_filename):
                            delattr(self,"selected_capillary_index")
                            delattr(self,"selected_capillary_filename")
                            self.refresh_selected_components()
                        else:
                            Capillary_name = self.Capillary_list[self.selected_capillary_index][1].Capillary_name
                            self.Expansion_selected_name.setText(Capillary_name)
                            self.Expansion_selected_name.setStyleSheet("background:#75BB2B;")
                    else:
                        delattr(self,"selected_capillary_index")
                        delattr(self,"selected_capillary_filename")
                        self.refresh_selected_components()                    
                else:
                    self.Expansion_selected_name.setText("No Capillary Selected")
                    self.Expansion_selected_name.setStyleSheet("background:#E55D3F;")
        except:
            if hasattr(self,"selected_condenser_index"):
                delattr(self,"selected_condenser_index")
                delattr(self,"selected_condenser_filename")
            if hasattr(self,"selected_evaporator_index"):
                delattr(self,"selected_evaporator_index")
                delattr(self,"selected_evaporator_filename")
            if hasattr(self,"selected_liquidline_index"):
                delattr(self,"selected_liquidline_index")
                delattr(self,"selected_liquidline_filename")
            if hasattr(self,"selected_suctionline_index"):
                delattr(self,"selected_suctionline_index")
                delattr(self,"selected_suctionline_filename")
            if hasattr(self,"selected_twophaseline_index"):
                delattr(self,"selected_twophaseline_index")
                delattr(self,"selected_twophaseline_filename")
            if hasattr(self,"selected_dischargeline_index"):
                delattr(self,"selected_dischargeline_index")
                delattr(self,"selected_dischargeline_filename")
            if hasattr(self,"selected_compressor_index"):
                delattr(self,"selected_compressor_index")
                delattr(self,"selected_compressor_filename")
            if hasattr(self,"selected_capillary_index"):
                delattr(self,"selected_capillary_index")
                delattr(self,"selected_capillary_filename")
            self.refresh_selected_components()

    def New_cycle_action(self):
        quit_msg = "You will lose all current inputs. Continue?"
        reply = QMessageBox.question(self, 'Message',
                         quit_msg, QMessageBox.Yes, QMessageBox.No)
    
        if reply == QMessageBox.Yes:
            self.restart_signal_to_main.emit()
            self.hide()
            
    def Open_cycle_action(self):
        quit_msg = "You will lose all current inputs. Continue?"
        reply = QMessageBox.question(self, 'Message', 
                         quit_msg, QMessageBox.Yes, QMessageBox.No)
    
        if reply == QMessageBox.Yes:
            path = QFileDialog.getOpenFileName(self, 'Open Cycle file',directory=load_last_location(),filter="Cycle file (*.cycle);;All files (*.*)")[0]
            if path != "":
                save_last_location(path)
                result = read_cycle_file(path)
                if result[0]:
                    try:
                        cycle = result[1]
                        self.load_fields(cycle)
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
            
    def load_fields(self,cycle):
        capacity_check = self.capacity_check
        if self.capacity_check:
            self.capacity_check = False
        self.Cycle_mode.setCurrentIndex(cycle.Cycle_mode_index)
        index = self.Cycle_refrigerant.findText(cycle.Cycle_refrigerant, Qt.MatchFixedString)
        self.Cycle_refrigerant.setCurrentIndex(index)
        self.Condenser_type.setCurrentIndex(cycle.Condenser_type)
        self.Evaporator_type.setCurrentIndex(cycle.Evaporator_type)
        self.First_condition.setCurrentIndex(cycle.First_condition)
        if cycle.First_condition == 0:
            self.Subcooling.setText(str(round(cycle.Subcooling,6)))
        elif cycle.First_condition == 1:
            self.Charge.setText(str(round(cycle.Charge,6)))       
        
        if hasattr(cycle,"Mass_resid"):
            self.Mass_resid.setText(str(round(cycle.Mass_resid,6)))
        self.Expansion_device.setCurrentIndex(cycle.Expansion_device)
        if cycle.Expansion_device == 0:
            self.Superheat_location.setCurrentIndex(cycle.Superheat_location)
            self.Superheat.setText(str(round(cycle.Superheat,6)))
        self.Solver.setCurrentIndex(cycle.Solver)
        if hasattr(cycle,"Energy_resid"):
            self.Energy_resid.setText(str(round(cycle.Energy_resid,6)))
        self.Pressire_resid.setText(str(round(cycle.Pressire_resid,6)))
        if hasattr(cycle,"Mass_flowrate_resid"):
            self.Mass_flowrate_resid.setText(str(cycle.Mass_flowrate_resid))
        self.Tevap_guess_type.setCurrentIndex(cycle.Tevap_guess_type)
        if cycle.Tevap_guess_type == 1:
            self.Tevap_guess.setText(str(round(cycle.Tevap_guess - 273.15,6)))
        self.Tcond_guess_type.setCurrentIndex(cycle.Tcond_guess_type)
        if cycle.Tcond_guess_type == 1:
            self.Tcond_guess.setText(str(round(cycle.Tcond_guess - 273.15,6)))
        self.Ref_library.setCurrentIndex(cycle.Ref_library_index)
        
        if hasattr(cycle,"Capacity_target"):
            self.Capacity_target.setText(str(round(cycle.Capacity_target,6)))
        
        if hasattr(cycle,"Test_cond"):
            index = self.Test_Condition.findText(cycle.Test_cond, Qt.MatchFixedString)
            self.Test_Condition.setCurrentIndex(index)
        else:
            self.Test_Condition.setCurrentIndex(1)

        self.accumulator_charge.setValue(cycle.accum_charge_per * 100.0)

        if self.Cycle_mode.currentIndex() == 0:
            condenser_name = "Outdoor Unit"
            evaporator_name = "Indoor Unit"
        elif self.Cycle_mode.currentIndex() == 1:
            condenser_name = "Indoor Unit"
            evaporator_name = "Outdoor Unit"
        
        if hasattr(cycle,"condenser_selected"):
            if cycle.Condenser_type == 0:
                for i,Fintube in enumerate(self.Fintube_list):
                    if cycle.condenser_selected == Fintube[0]:
                        self.selected_condenser_index = i
                        self.selected_condenser_filename = Fintube[0]
            elif cycle.Condenser_type == 1:
                for i,Microchannel in enumerate(self.Microchannel_list):
                    if cycle.condenser_selected == Microchannel[0]:
                        self.selected_condenser_index = i
                        self.selected_condenser_filename = Microchannel[0]
            if not hasattr(self,"selected_condenser_index"):
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("Could not select "+condenser_name+"!")
                msg.setWindowTitle("Sorry!")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()

        if hasattr(cycle,"evaporator_selected"):
            if cycle.Evaporator_type == 0:
                for i,Fintube in enumerate(self.Fintube_list):
                    if cycle.evaporator_selected == Fintube[0]:
                        self.selected_evaporator_index = i
                        self.selected_evaporator_filename = Fintube[0]
            elif cycle.Evaporator_type == 1:
                for i,Microchannel in enumerate(self.Microchannel_list):
                    if cycle.evaporator_selected == Microchannel[0]:
                        self.selected_evaporator_index = i
                        self.selected_evaporator_filename = Microchannel[0]
            if not hasattr(self,"selected_evaporator_index"):
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("Could not select "+evaporator_name+"!")
                msg.setWindowTitle("Sorry!")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
                    
        if hasattr(cycle,"liquidline_selected"):
            for i,Line in enumerate(self.Line_list):
                if cycle.liquidline_selected == Line[0]:
                    self.selected_liquidline_index = i
                    self.selected_liquidline_filename = Line[0]
            if not hasattr(self,"selected_liquidline_index"):
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("Could not select liquid line!")
                msg.setWindowTitle("Sorry!")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()

        if hasattr(cycle,"suctionline_selected"):
            for i,Line in enumerate(self.Line_list):
                if cycle.suctionline_selected == Line[0]:
                    self.selected_suctionline_index = i
                    self.selected_suctionline_filename = Line[0]
            if not hasattr(self,"selected_suctionline_index"):
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("Could not select suction line!")
                msg.setWindowTitle("Sorry!")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()

        if hasattr(cycle,"twophaseline_selected"):
            for i,Line in enumerate(self.Line_list):
                if cycle.twophaseline_selected == Line[0]:
                    self.selected_twophaseline_index = i
                    self.selected_twophaseline_filename = Line[0]
            if not hasattr(self,"selected_twophaseline_index"):
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("Could not select two-phase line!")
                msg.setWindowTitle("Sorry!")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()

        if hasattr(cycle,"dischargeline_selected"):
            for i,Line in enumerate(self.Line_list):
                if cycle.dischargeline_selected == Line[0]:
                    self.selected_dischargeline_index = i
                    self.selected_dischargeline_filename = Line[0]
            if not hasattr(self,"selected_dischargeline_index"):
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("Could not select discharge line!")
                msg.setWindowTitle("Sorry!")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()

        if hasattr(cycle,"compressor_selected"):
            for i,Compressor in enumerate(self.Compressor_list):
                if cycle.compressor_selected == Compressor[0]:
                    if cycle.Cycle_refrigerant == Compressor[1].Ref or Compressor[1].Ref == "Not specified":
                        self.selected_compressor_index = i
                        self.selected_compressor_filename = Compressor[0]
                    else:
                        msg = QMessageBox()
                        msg.setIcon(QMessageBox.Warning)
                        msg.setText("Compressor refrigerant in the database is different from the refrigerant selected in the cycle file!")
                        msg.setWindowTitle("Sorry!")
                        msg.setStandardButtons(QMessageBox.Ok)
                        msg.exec_()
            if not hasattr(self,"selected_compressor_index"):
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("Could not select compressor!")
                msg.setWindowTitle("Sorry!")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()

        if hasattr(cycle,"capillary_selected"):
            for i,Capillary in enumerate(self.Capillary_list):
                if cycle.capillary_selected == Capillary[0]:
                    self.selected_capillary_index = i
                    self.selected_capillary_filename = Capillary[0]
            if not hasattr(self,"selected_capillary_index"):
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("Could not select capillary tube!")
                msg.setWindowTitle("Sorry!")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
        
        if hasattr(cycle,"parametric_data"):
            if cycle.parametric_data[0,0]:
                self.parametric_cycle_data = cycle.parametric_data[0,1]
                self.Parametric_cycle.setChecked(True)
            if cycle.parametric_data[1,0]:
                self.parametric_capillary_data = cycle.parametric_data[1,1]
                self.Parametric_capillary.setChecked(True)
            if cycle.parametric_data[2,0]:
                self.parametric_compressor_data = cycle.parametric_data[2,1]
                self.Parametric_compressor.setChecked(True)
            if cycle.parametric_data[3,0]:
                self.parametric_liquid_data = cycle.parametric_data[3,1]
                self.Parametric_liquid.setChecked(True)
            if cycle.parametric_data[4,0]:
                self.parametric_2phase_data = cycle.parametric_data[4,1]
                self.Parametric_2phase.setChecked(True)
            if cycle.parametric_data[5,0]:
                self.parametric_suction_data = cycle.parametric_data[5,1]
                self.Parametric_suction.setChecked(True)
            if cycle.parametric_data[6,0]:
                self.parametric_discharge_data = cycle.parametric_data[6,1]
                self.Parametric_discharge.setChecked(True)
            if cycle.parametric_data[7,0]:
                self.parametric_evaporator_data = cycle.parametric_data[7,1]
                self.Parametric_evaporator.setChecked(True)
            if cycle.parametric_data[8,0]:
                self.parametric_condenser_data = cycle.parametric_data[8,1]
                self.Parametric_condenser.setChecked(True)
        else:
            if hasattr(self,"parametric_cycle_data"):
                delattr(self,"parametric_cycle_data")
            self.Parametric_cycle.setChecked(False)
            if hasattr(self,"parametric_capillary_data"):
                delattr(self,"parametric_capillary_data")
            self.Parametric_capillary.setChecked(False)
            if hasattr(self,"parametric_compressor_data"):
                delattr(self,"parametric_compressor_data")
            self.Parametric_compressor.setChecked(False)
            if hasattr(self,"parametric_liquid_data"):
                delattr(self,"parametric_liquid_data")
            self.Parametric_liquid.setChecked(False)
            if hasattr(self,"parametric_2phase_data"):
                delattr(self,"parametric_2phase_data")
            self.Parametric_2phase.setChecked(False)
            if hasattr(self,"parametric_suction_data"):
                delattr(self,"parametric_suction_data")
            self.Parametric_suction.setChecked(False)
            if hasattr(self,"parametric_discharge_data"):
                delattr(self,"parametric_discharge_data")
            self.Parametric_discharge.setChecked(False)
            if hasattr(self,"parametric_evaporator_data"):
                delattr(self,"parametric_evaporator_data")
            self.Parametric_evaporator.setChecked(False)
            if hasattr(self,"parametric_condenser_data"):
                delattr(self,"parametric_condenser_data")
            self.Parametric_condenser.setChecked(False)
        self.create_parametric_data_table()
        self.refresh_selected_components()
        self.capacity_check = capacity_check
        self.check_components_capacity()
        
    def Save_cycle_action(self):
        validate = self.validate()
        if validate == 0:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please fill all empty fields")
            msg.setWindowTitle("Empty Fields!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            
        elif validate == 1 or validate == 2 or validate == 3:
            path = QFileDialog.getSaveFileName(self, caption='Save Cycle file',directory=load_last_location(),filter="cycle file (*.cycle);;All files (*.*)")[0]
            if path != "":
                save_last_location(path)
                if path[-6:].lower() != ".cycle":
                    path = path+".cycle"
                cycle = values()
                
                cycle.Cycle_refrigerant = self.Cycle_refrigerant.currentText()
                cycle.Condenser_type = self.Condenser_type.currentIndex()
                cycle.Evaporator_type = self.Evaporator_type.currentIndex()
                cycle.First_condition = self.First_condition.currentIndex()
                if self.First_condition.currentIndex() == 0:
                    cycle.Subcooling = temperature_diff_unit_converter(self.Subcooling.text(),self.Subcooling_unit.currentIndex())
                if self.First_condition.currentIndex() == 1:
                    cycle.Charge = mass_unit_converter(self.Charge.text(),self.Charge_unit.currentIndex())

                if self.Energy_resid.isEnabled():
                    cycle.Energy_resid = power_unit_converter(self.Energy_resid.text(),self.Energy_resid_unit.currentIndex())
                else:
                    cycle.Energy_resid = 1
                    
                if self.Mass_resid.isEnabled():
                    cycle.Mass_resid = mass_unit_converter(self.Mass_resid.text(),self.Mass_resid_unit.currentIndex())
                else:
                    cycle.Mass_resid = 0.1
                    
                if self.Mass_flowrate_resid.isEnabled():
                    cycle.Mass_flowrate_resid = mass_flowrate_unit_converter(self.Mass_flowrate_resid.text(),self.Mass_flowrate_resid_unit.currentIndex())
                else:
                    cycle.Mass_flowrate_resid = 0.001
                    
                cycle.Cycle_mode_index = self.Cycle_mode.currentIndex()
                cycle.Expansion_device = self.Expansion_device.currentIndex()
                if self.Expansion_device.currentIndex() == 0:
                    cycle.Superheat_location = self.Superheat_location.currentIndex()
                    cycle.Superheat = temperature_diff_unit_converter(self.Superheat.text(),self.Superheat_unit.currentIndex())
                cycle.Solver = self.Solver.currentIndex()
                cycle.Pressire_resid = pressure_unit_converter(self.Pressire_resid.text(),self.Pressire_resid_unit.currentIndex())
                cycle.Tevap_guess_type = self.Tevap_guess_type.currentIndex()
                if self.Tevap_guess_type.currentIndex() == 1:
                    cycle.Tevap_guess = temperature_unit_converter(self.Tevap_guess.text(),self.Tevap_guess_unit.currentIndex())
                cycle.Tcond_guess_type = self.Tcond_guess_type.currentIndex()
                if self.Tcond_guess_type.currentIndex() == 1:
                    cycle.Tcond_guess = temperature_unit_converter(self.Tcond_guess.text(),self.Tcond_guess_unit.currentIndex())
                cycle.Ref_library_index = self.Ref_library.currentIndex()
                
                cycle.Capacity_target = power_unit_converter(self.Capacity_target.text(),self.Capacity_target_unit.currentIndex())
                cycle.Test_cond = self.Test_Condition.currentText()
                cycle.accum_charge_per = self.accumulator_charge.value()/100.0
                                
                if hasattr(self,"selected_condenser_index"):
                    if self.Condenser_type.currentIndex() == 0:
                        filename = self.selected_condenser_filename
                    elif self.Condenser_type.currentIndex() == 1:
                        filename = self.selected_condenser_filename
                    cycle.condenser_selected = filename
                if hasattr(self,"selected_evaporator_index"):
                    if self.Condenser_type.currentIndex() == 0:
                        filename = self.selected_evaporator_filename
                    elif self.Condenser_type.currentIndex() == 1:
                        filename = self.selected_evaporator_filename
                    cycle.evaporator_selected = filename
                if hasattr(self,"selected_liquidline_index"):
                    filename = self.selected_liquidline_filename
                    cycle.liquidline_selected = filename
                if hasattr(self,"selected_suctionline_index"):
                    filename = self.selected_suctionline_filename
                    cycle.suctionline_selected = filename
                if hasattr(self,"selected_twophaseline_index"):
                    filename = self.selected_twophaseline_filename
                    cycle.twophaseline_selected = filename
                if hasattr(self,"selected_dischargeline_index"):
                    filename = self.selected_dischargeline_filename
                    cycle.dischargeline_selected = filename
                if hasattr(self,"selected_compressor_index"):
                    filename = self.selected_compressor_filename
                    cycle.compressor_selected = filename
                if hasattr(self,"selected_capillary_index"):
                    filename = self.selected_capillary_filename
                    cycle.capillary_selected = filename
                cycle_parametric_array = np.zeros([9,2],dtype=object)
                if hasattr(self,"parametric_cycle_data") and self.Parametric_cycle.checkState():
                    cycle_parametric_array[0] = [1,self.parametric_cycle_data]
                if hasattr(self,"parametric_capillary_data") and self.Parametric_capillary.checkState():
                    cycle_parametric_array[1] = [1,self.parametric_capillary_data]
                if hasattr(self,"parametric_compressor_data") and self.Parametric_compressor.checkState():
                    cycle_parametric_array[2] = [1,self.parametric_compressor_data]
                if hasattr(self,"parametric_liquid_data") and self.Parametric_liquid.checkState():
                    cycle_parametric_array[3] = [1,self.parametric_liquid_data]
                if hasattr(self,"parametric_2phase_data") and self.Parametric_2phase.checkState():
                    cycle_parametric_array[4] = [1,self.parametric_2phase_data]
                if hasattr(self,"parametric_suction_data") and self.Parametric_suction.checkState():
                    cycle_parametric_array[5] = [1,self.parametric_suction_data]
                if hasattr(self,"parametric_discharge_data") and self.Parametric_discharge.checkState():
                    cycle_parametric_array[6] = [1,self.parametric_discharge_data]
                if hasattr(self,"parametric_evaporator_data") and self.Parametric_evaporator.checkState():
                    cycle_parametric_array[7] = [1,self.parametric_evaporator_data]
                if hasattr(self,"parametric_condenser_data") and self.Parametric_condenser.checkState():
                    cycle_parametric_array[8] = [1,self.parametric_condenser_data]
                
                if any(cycle_parametric_array[:,0]):
                    cycle.parametric_data = cycle_parametric_array
                
                result = write_cycle_file(cycle,path)
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

    def validate(self):
        self.refresh_selected_components()
        if self.First_condition.currentIndex() == 0:
            if str(self.Subcooling.text()).strip() in ["","-","."]:
                return 0
        elif self.First_condition.currentIndex() == 1:
            if str(self.Charge.text()).strip() in ["","-","."]:
                return 0

        if self.Expansion_device.currentIndex() == 0:
            if str(self.Superheat.text()).strip() in ["","-","."]:
                return 0

        if self.Mass_resid.isEnabled():
            if str(self.Mass_resid.text()).strip() in ["","-","."]:
                return 0
        
        if self.Energy_resid.isEnabled():
            if str(self.Energy_resid.text()).strip() in ["","-","."]:
                return 0
            
        if self.Pressire_resid.isEnabled():
            if str(self.Pressire_resid.text()).strip() in ["","-","."]:
                return 0

        if self.Mass_flowrate_resid.isEnabled():
            if str(self.Mass_flowrate_resid.text()).strip() in ["","-","."]:
                return 0

        if self.Tevap_guess_type.currentIndex() == 1:
            if str(self.Tevap_guess.text()).strip() in ["","-","."]:
                return 0

        if self.Tcond_guess_type.currentIndex() == 1:
            if str(self.Tcond_guess.text()).strip() in ["","-","."]:
                return 0

        if str(self.Capacity_target.text()).strip() in ["","-","."]:
            return 0

        if self.accumulator_charge.value == 1.0:
            self.raise_error_meesage("Accumulator charge capacity ratio can not be 100%")
            return 4
        
        if not hasattr(self,"selected_condenser_index"):
            return 2
        if not hasattr(self,"selected_evaporator_index"):
            return 2
        if not hasattr(self,"selected_liquidline_index"):
            return 2
        if not hasattr(self,"selected_suctionline_index"):
            return 2
        if not hasattr(self,"selected_twophaseline_index"):
            return 2
        if not hasattr(self,"selected_dischargeline_index"):
            return 2
        if not hasattr(self,"selected_compressor_index"):
            return 2
        if self.Expansion_device.currentIndex() == 1:
            if not hasattr(self,"selected_capillary_index"):
                return 2
        
        if self.Ref_library.currentIndex() == 0:
            try:
                AS = CP.AbstractState("REFPROP","R22")
            except:
                return 3
        
        if self.Parametric_cycle.checkState():
            if not hasattr(self,"parametric_cycle_data"):
                self.raise_error_meesage("Please define cycle parametric data")
                return 4
        if self.Parametric_capillary.checkState():
            if not hasattr(self,"parametric_capillary_data"):
                self.raise_error_meesage("Please define capillary parametric data")
                return 4
        if self.Parametric_compressor.checkState():
            if not hasattr(self,"parametric_compressor_data"):
                self.raise_error_meesage("Please define compressor parametric data")
                return 4
        if self.Parametric_liquid.checkState():
            if not hasattr(self,"parametric_liquid_data"):
                self.raise_error_meesage("Please define liquid line parametric data")
                return 4
        if self.Parametric_2phase.checkState():
            if not hasattr(self,"parametric_2phase_data"):
                self.raise_error_meesage("Please define two-phase line parametric data")
                return 4
        if self.Parametric_suction.checkState():
            if not hasattr(self,"parametric_suction_data"):
                self.raise_error_meesage("Please define suction line parametric data")
                return 4
        if self.Parametric_discharge.checkState():
            if not hasattr(self,"parametric_discharge_data"):
                self.raise_error_meesage("Please define discharge line parametric data")
                return 4
        if self.Parametric_evaporator.checkState():
            if not hasattr(self,"parametric_evaporator_data"):
                self.raise_error_meesage("Please define evaporator parametric data")
                return 4
        if self.Parametric_condenser.checkState():
            if not hasattr(self,"parametric_condenser_data"):
                self.raise_error_meesage("Please define condenser parametric data")
                return 4                

        return 1

    def Tevap_guess_type_changed(self):
        if self.Tevap_guess_type.currentIndex() == 0:
            self.Tevap_guess.setEnabled(False)
            self.Tevap_guess_unit.setEnabled(False)
        elif self.Tevap_guess_type.currentIndex() == 1:
            self.Tevap_guess.setEnabled(True)
            self.Tevap_guess_unit.setEnabled(True)

    def Tcond_guess_type_changed(self):
        if self.Tcond_guess_type.currentIndex() == 0:
            self.Tcond_guess.setEnabled(False)
            self.Tcond_guess_unit.setEnabled(False)
        elif self.Tcond_guess_type.currentIndex() == 1:
            self.Tcond_guess.setEnabled(True)
            self.Tcond_guess_unit.setEnabled(True)        

    def first_condition_changed(self):
        if hasattr(self,"parametric_cycle_data"):
            delattr(self,"parametric_cycle_data")
            self.delete_validation_range()
        
        if self.First_condition.currentIndex() == 0:
            self.Subcooling.setEnabled(True)
            self.Subcooling_unit.setEnabled(True)
            self.Charge.setEnabled(False)
            self.Charge_unit.setEnabled(False)
            self.update_residuals_options()

        elif self.First_condition.currentIndex() == 1:
            self.Subcooling.setEnabled(False)
            self.Subcooling_unit.setEnabled(False)
            self.Charge.setEnabled(True)
            self.Charge_unit.setEnabled(True)
            self.update_residuals_options()
        self.create_parametric_data_table()

    def update_residuals_options(self):
        self.Energy_resid.setEnabled(False)
        self.Energy_resid_unit.setEnabled(False)
        self.Pressire_resid.setEnabled(True)
        self.Pressire_resid_unit.setEnabled(True)
        self.Mass_flowrate_resid.setEnabled(False)
        self.Mass_flowrate_resid_unit.setEnabled(False)
        self.Mass_resid.setEnabled(False)
        self.Mass_resid_unit.setEnabled(False)
        self.Energy_residual_condenser_update.setEnabled(False)
        self.Energy_residual_evaporator_update.setEnabled(False)
        self.mass_flowrate_residual_update.setEnabled(False)
        self.pressure_residual_residual_update.setEnabled(True)
        self.mass_residual_update.setEnabled(False)
        
        if self.First_condition.currentIndex() == 0:
            self.Energy_resid.setEnabled(True)
            self.Energy_resid_unit.setEnabled(True)
            self.Energy_residual_condenser_update.setEnabled(True)
            
        else:
            self.Mass_resid.setEnabled(True)
            self.Mass_resid_unit.setEnabled(True)
            self.mass_residual_update.setEnabled(True)
            
        if self.Expansion_device.currentIndex() == 0:
            self.Energy_resid.setEnabled(True)
            self.Energy_resid_unit.setEnabled(True)
            self.Energy_residual_evaporator_update.setEnabled(True)
        else:
            self.Mass_flowrate_resid.setEnabled(True)
            self.Mass_flowrate_resid_unit.setEnabled(True)
            self.mass_flowrate_residual_update.setEnabled(True)
            
    def expansion_device_changed(self):
        if hasattr(self,"parametric_cycle_data"):
            delattr(self,"parametric_cycle_data")
        
        if hasattr(self,"parametric_capillary_data"):
            delattr(self,"parametric_capillary_data")

        self.delete_validation_range()
            
        if self.Expansion_device.currentIndex() == 0:
            self.Superheat_location.setEnabled(True)
            self.Superheat.setEnabled(True)
            self.Superheat_unit.setEnabled(True)
            self.Expansion_select_button.setEnabled(False)
            self.Expansion_selected_name.setText("Constant Superheat")
            if hasattr(self,"selected_capillary_index"):
                delattr(self,"selected_capillary_index")
                delattr(self,"selected_capillary_filename")
            self.Parametric_capillary.setChecked(False)
            self.Parametric_capillary.setEnabled(False)
            self.update_residuals_options()

        elif self.Expansion_device.currentIndex() == 1:
            self.Superheat_location.setEnabled(False)
            self.Superheat.setEnabled(False)
            self.Superheat_unit.setEnabled(False)
            self.Expansion_select_button.setEnabled(True)
            if hasattr(self,"selected_capillary_index"):
                delattr(self,"selected_capillary_index")
                delattr(self,"selected_capillary_filename")
            self.Parametric_capillary.setChecked(False)
            self.Parametric_capillary.setEnabled(True)
            self.update_residuals_options()
        self.create_parametric_data_table()
        self.refresh_selected_components()

    def edit_component(self):
        sender_name = self.sender().objectName()
        if sender_name == "actionCompressors":
            Edit_window = Component_edit("Compressor",self)
        elif sender_name == "actionFin_tube_HX":
            Edit_window = Component_edit("Fintube",self)
        elif sender_name == "actionMicrochannel_HX":
            Edit_window = Component_edit("Microchannel",self)
        elif sender_name == "actionLine":
            Edit_window = Component_edit("Line",self)
        elif sender_name == "actionCapillary_Tube":
            Edit_window = Component_edit("Capillary",self)
        Edit_window.exec_()
        
    def closeEvent(self, event):
        quit_msg = "Are you sure you want to exit the program?"
        reply = QMessageBox.question(self, 'Message', 
                         quit_msg, QMessageBox.Yes, QMessageBox.No)
    
        if reply == QMessageBox.Yes:
            self.close_signal_to_main.emit()
            event.accept()
        else:
            event.ignore()            

    def add_new_compressor(self):
        Comp_Window = CompressorWindow(self)
        Comp_Window.exec_()
        if hasattr(Comp_Window,"Compressor"):
            file = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '.comp'
            result = write_comp_xml(Comp_Window.Compressor,self.database_path+file)
            if result:
                self.Compressor_list.append([file,Comp_Window.Compressor])
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
            self.load_database()

    def add_new_fintube(self):
        fubtube_Window = FinTubeWindow(self)
        fubtube_Window.exec_()
        if hasattr(fubtube_Window,"HX_data"):
            file = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '.hx'
            result = write_Fin_tube(fubtube_Window.HX_data,self.database_path+file)
            if result:
                self.Fintube_list.append([file,fubtube_Window.HX_data])
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
            self.load_database()

    def add_new_microchannel(self):
        microchannel_Window = MicrochannelWindow(self)
        microchannel_Window.exec_()
        if hasattr(microchannel_Window,"HX_data"):
            file = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '.hx'
            result = write_Microchannel(microchannel_Window.HX_data,self.database_path+file)
            if result:
                self.Microchannel_list.append([file,microchannel_Window.HX_data])
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
            self.load_database()

    def add_new_line(self):
        line_Window = LineWindow(self)
        line_Window.exec_()
        if hasattr(line_Window,"line_result"):
            file = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '.line'
            result = write_line_file(line_Window.line_result,self.database_path+file)
            if result:
                self.Line_list.append([file,line_Window.line_result])
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
            self.load_database()

    def add_new_capillary(self):
        capillary_Window = CapillaryWindow(self)
        capillary_Window.exec_()
        if hasattr(capillary_Window,"capillary_result"):
            file = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '.capillary'
            result = write_capillary_file(capillary_Window.capillary_result,self.database_path+file)
            if result:
                self.Capillary_list.append([file,capillary_Window.capillary_result])
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setText("Capillary was added to the database successfully")
                msg.setWindowTitle("Capillary Added")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
            else:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("Capillary Could not be added")
                msg.setWindowTitle("Capillary was not added!")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()    
            self.load_database()

    def swap_HXs(self):
        if hasattr(self,"selected_condenser_index"):
            condenser_index = self.selected_condenser_index
            condenser_filename = self.selected_condenser_filename
        else:
            condenser_index = -1
        condenser_type = self.Condenser_type.currentIndex()

        if hasattr(self,"selected_evaporator_index"):
            evaporator_index = self.selected_evaporator_index
            evaporator_filename = self.selected_evaporator_filename
        else:
            evaporator_index = -1
        evaporator_type = self.Evaporator_type.currentIndex()
        
        if condenser_index != -1:
            self.selected_evaporator_index = condenser_index
            self.selected_evaporator_filename = condenser_filename
        else:
            if hasattr(self,"selected_evaporator_index"):
                delattr(self,"selected_evaporator_index")
                delattr(self,"selected_evaporator_filename")
        self.Condenser_type.setCurrentIndex(evaporator_type)

        if evaporator_index != -1:
            self.selected_condenser_index = evaporator_index
            self.selected_condenser_filename = evaporator_filename
        else:
            if hasattr(self,"selected_condenser_index"):
                delattr(self,"selected_condenser_index")
                delattr(self,"selected_condenser_filename")
        self.Evaporator_type.setCurrentIndex(condenser_type)

        if hasattr(self,"parametric_condenser_data"):
            delattr(self,"parametric_condenser_data")

        if hasattr(self,"parametric_evaporator_data"):
            delattr(self,"parametric_evaporator_data")

        self.delete_validation_range()

        self.create_parametric_data_table()
        self.refresh_selected_components()

    def swap_lines(self):
        if hasattr(self,"selected_liquidline_index"):
            liquidline_index = self.selected_liquidline_index
            liquidline_filename = self.selected_liquidline_filename
        else:
            liquidline_index = -1

        if hasattr(self,"selected_suctionline_index"):
            suctionline_index = self.selected_suctionline_index
            suctionline_filename = self.selected_suctionline_filename
        else:
            suctionline_index = -1

        if hasattr(self,"selected_twophaseline_index"):
            twophaseline_index = self.selected_twophaseline_index
            twophaseline_filename = self.selected_twophaseline_filename
        else:
            twophaseline_index = -1

        if hasattr(self,"selected_dischargeline_index"):
            dischargeline_index = self.selected_dischargeline_index
            dischargeline_filename = self.selected_dischargeline_filename
        else:
            dischargeline_index = -1
        
        if liquidline_index != -1:
            self.selected_twophaseline_index = liquidline_index
            self.selected_twophaseline_filename = liquidline_filename
        else:
            if hasattr(self,"selected_twophaseline_index"):
                delattr(self,"selected_twophaseline_index")
                delattr(self,"selected_twophaseline_filename")

        if twophaseline_index != -1:
            self.selected_liquidline_index = twophaseline_index
            self.selected_liquidline_filename = twophaseline_filename
        else:
            if hasattr(self,"selected_liquidline_index"):
                delattr(self,"selected_liquidline_index")
                delattr(self,"selected_liquidline_filename")

        if dischargeline_index != -1:
            self.selected_suctionline_index = dischargeline_index
            self.selected_suctionline_filename = dischargeline_filename
        else:
            if hasattr(self,"selected_suctionline_index"):
                delattr(self,"selected_suctionline_index")
                delattr(self,"selected_suctionline_filename")

        if suctionline_index != -1:
            self.selected_dischargeline_index = suctionline_index
            self.selected_dischargeline_filename = suctionline_filename
        else:
            if hasattr(self,"selected_dischargeline_index"):
                delattr(self,"selected_dischargeline_index")
                delattr(self,"selected_dischargeline_filename")

        if hasattr(self,"parametric_liquid_data"):
            delattr(self,"parametric_liquid_data")

        if hasattr(self,"parametric_suction_data"):
            delattr(self,"parametric_suction_data")

        if hasattr(self,"parametric_2phase_data"):
            delattr(self,"parametric_2phase_data")

        if hasattr(self,"parametric_discharge_data"):
            delattr(self,"parametric_discharge_data")

        self.create_parametric_data_table()
        self.refresh_selected_components()

    def delete_old_files_from_database(self):
        files_to_delete_file = appdirs.user_data_dir("EGSim")+"/Temp/files_to_delete.ini"
        if not os.path.exists(files_to_delete_file):
            open(files_to_delete_file, 'a').close()
        files_list = []
        with open(files_to_delete_file, newline='') as csvfile:
            files = csv.reader(csvfile)
            for row in files:
                for file in row:
                    if file.strip() != "":
                        files_list.append(file.strip())
        files_deleted = []
        for file in files_list:
            if os.path.exists(self.database_path+file):
                os.remove(self.database_path+file)
        file = open(files_to_delete_file, 'w')
        file.write("")
        file.close()

    def load_database(self):
        if os.path.exists(self.database_path):
            _, _, files = next(os.walk(self.database_path))
            # intialize components lists
            self.Fintube_list = []
            self.Microchannel_list = []
            self.Compressor_list = []
            self.Line_list = []
            self.Capillary_list = []
            HX_files = []
            Comp_files = []
            Capillary_files = []
            Lines_files = []
            if files:
                for file in files:
                    if file.split(".")[-1].lower() == "hx":
                        HX_files.append(file)
                    elif file.split(".")[-1].lower() == "comp":
                        Comp_files.append(file)
                    elif file.split(".")[-1].lower() == "capillary":
                        Capillary_files.append(file)
                    elif file.split(".")[-1].lower() == "line":
                        Lines_files.append(file)
            for HX_file in HX_files:
                result = read_Fin_tube(self.database_path+HX_file)
                if result[0]:
                    self.Fintube_list.append([HX_file,result[1]])
                result = read_Microchannel(self.database_path+HX_file)
                if result[0]:
                    self.Microchannel_list.append([HX_file,result[1]])
            for Comp_file in Comp_files:
                result = read_comp_xml(self.database_path+Comp_file)
                if result[0]:
                    self.Compressor_list.append([Comp_file,result[1]])
            for Capillary_file in Capillary_files:
                result = read_capillary_file(self.database_path+Capillary_file)
                if result[0]:
                    self.Capillary_list.append([Capillary_file,result[1]])
            for Lines_file in Lines_files:
                result = read_line_file(self.database_path+Lines_file)
                if result[0]:
                    self.Line_list.append([Lines_file,result[1]])
            
            HX_names_Fintube = []
            for Fintube in self.Fintube_list:
                HX_names_Fintube.append([len(HX_names_Fintube)+1,Fintube[1].name])
            self.HX_names_Fintube = HX_names_Fintube

            HX_names_Microchannel = []
            for Microchannel in self.Microchannel_list:
                HX_names_Microchannel.append([len(HX_names_Microchannel),Microchannel[1].name])
            self.HX_names_Microchannel = HX_names_Microchannel
            
            Comp_names = []
            for Compressor in self.Compressor_list:
                Comp_names.append([len(Comp_names),Compressor[1].Comp_name])
            self.Comp_names = Comp_names
        
            Line_names = []
            for Line in self.Line_list:
                Line_names.append([len(Line_names),Line[1].Line_name])
            self.Line_names = Line_names
    
            Capillary_names = []
            for Capillary in self.Capillary_list:
                Capillary_names.append([len(Capillary_names),Capillary[1].Capillary_name])
            self.Capillary_names = Capillary_names

    def create_parametric_data_table(self):
        try:
            cycle_parametric_array = np.zeros([9,2],dtype=object)
            if hasattr(self,"parametric_cycle_data") and self.Parametric_cycle.checkState():
                cycle_parametric_array[0] = [1,self.parametric_cycle_data]
            if hasattr(self,"parametric_capillary_data") and self.Parametric_capillary.checkState():
                cycle_parametric_array[1] = [1,self.parametric_capillary_data]
            if hasattr(self,"parametric_compressor_data") and self.Parametric_compressor.checkState():
                cycle_parametric_array[2] = [1,self.parametric_compressor_data]
            if hasattr(self,"parametric_liquid_data") and self.Parametric_liquid.checkState():
                cycle_parametric_array[3] = [1,self.parametric_liquid_data]
            if hasattr(self,"parametric_2phase_data") and self.Parametric_2phase.checkState():
                cycle_parametric_array[4] = [1,self.parametric_2phase_data]
            if hasattr(self,"parametric_suction_data") and self.Parametric_suction.checkState():
                cycle_parametric_array[5] = [1,self.parametric_suction_data]
            if hasattr(self,"parametric_discharge_data") and self.Parametric_discharge.checkState():
                cycle_parametric_array[6] = [1,self.parametric_discharge_data]
            if hasattr(self,"parametric_evaporator_data") and self.Parametric_evaporator.checkState():
                cycle_parametric_array[7] = [1,self.parametric_evaporator_data]
            if hasattr(self,"parametric_condenser_data") and self.Parametric_condenser.checkState():
                cycle_parametric_array[8] = [1,self.parametric_condenser_data]
            
            if self.Cycle_mode.currentIndex() == 0:
                mode = "AC"
            else:
                mode = "HP"
            
            if any(cycle_parametric_array[:,0]):
                self.parametric_data_table_instance = Parametric_table(cycle_parametric_array, mode,self)
            else:
                self.parametric_data_table_instance = QTableWidget(self)
            if not self.parametric_data_table.layout() is None:
                QWidget().setLayout(self.parametric_data_table.layout())            
            layout = QVBoxLayout()
            layout.addWidget(self.parametric_data_table_instance)
            self.parametric_data_table.setLayout(layout)
        except:
            if hasattr(self,"parametric_cycle_data"):
                delattr(self,"parametric_cycle_data")
            if hasattr(self,"parametric_capillary_data"):
                delattr(self,"parametric_capillary_data")
            if hasattr(self,"parametric_compressor_data"):
                delattr(self,"parametric_compressor_data")
            if hasattr(self,"parametric_liquid_data"):
                delattr(self,"parametric_liquid_data")
            if hasattr(self,"parametric_2phase_data"):
                delattr(self,"parametric_2phase_data")
            if hasattr(self,"parametric_suction_data"):
                delattr(self,"parametric_suction_data")
            if hasattr(self,"parametric_discharge_data"):
                delattr(self,"parametric_discharge_data")
            if hasattr(self,"parametric_evaporator_data"):
                delattr(self,"parametric_evaporator_data")
            if hasattr(self,"parametric_condenser_data"):
                delattr(self,"parametric_condenser_data")
            self.create_parametric_data_table()
            self.refresh_selected_components()
            
if __name__ == '__main__':
    def main():
        currentExitCode = MainWindow.EXIT_CODE_REBOOT
        while currentExitCode == MainWindow.EXIT_CODE_REBOOT:
            app=QApplication(sys.argv)
            window = MainWindow()
            window.show()
            currentExitCode = app.exec_()
            app = None  # delete the QApplication object
    main()
