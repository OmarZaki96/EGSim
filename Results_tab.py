from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import io,csv
from GUI_functions import create_outputs_array,concatenate_outputs, construct_table
import numpy as np
from Plots import PlotsWidget, PlotsParamWidget
from unit_conversion import *
from copy import deepcopy

class values():
    pass

class ResultsTable_single(QTableWidget):
    def __init__(self, table, header, parent=None):
        super(ResultsTable_single, self).__init__(parent)
        table = table[0]
        self.setRowCount(len(table))
        self.setColumnCount(len(header))
        self.setHorizontalHeaderLabels(header)

        class MyDelegate(QItemDelegate):

            def createEditor(self, parent, option, index):
                return_object = QLineEdit(parent)
                return_object.setMaxLength(1000)
                return return_object
        delegate = MyDelegate()
        self.setItemDelegate(delegate)
        
        for i in range(len(table)):
            self.setItem(i,0,QTableWidgetItem(table[i,0]))
            try:
                float(table[i,2])
                test = True
            except:
                test = False
            if test and (table[i,1].lower() in ["c","k","kg","w","pa","kg/s","m^3/s","m","m^2","m^3","degree","w/m.k","w/m^2.k","s","w/w","j/kg.k","w/k","j/kg","m/s"]):
                Combo = QComboBox()
                if table[i,1].lower() == "c":
                    options = ["C","K","F"]
                    function = temperature_unit_converter
                    value = float(table[i,2])+273.15
                elif table[i,1].lower() == "k":
                    options = ["C","F"]
                    function = temperature_diff_unit_converter
                    value = float(table[i,2])
                elif table[i,1].lower() == "kg":
                    options = ["kg","lb"]
                    function = mass_unit_converter
                    value = float(table[i,2])
                elif table[i,1].lower() == "w":
                    options = ["W","Btu/hr"]
                    function = power_unit_converter
                    value = float(table[i,2])
                elif table[i,1].lower() == "pa":
                    options = ["Pa","kPa","MPa","bar","atm","psi"]
                    function = pressure_unit_converter
                    value = float(table[i,2])
                elif table[i,1].lower() == "kg/s":
                    options = ["kg/s","kg/min","kg/hr","lb/s","lb/min","lb/hr"]
                    function = mass_flowrate_unit_converter
                    value = float(table[i,2])
                elif table[i,1].lower() == "m^3/s":
                    options = ["m3/s","m3/min","m3/hr","ft3/s","ft3/min","ft3/hr"]
                    function = volume_flowrate_unit_converter
                    value = float(table[i,2])
                elif table[i,1].lower() == "m":
                    options = ["m","cm","mm","ft","in"]
                    function = length_unit_converter
                    value = float(table[i,2])
                elif table[i,1].lower() == "m^2":
                    options = ["m^2","cm^2","mm^2","ft^2","in^2"]
                    function = area_unit_converter
                    value = float(table[i,2])
                elif table[i,1].lower() == "m^3":
                    options = ["m^3","cm^3","ft^3","in^3"]
                    function = volume_unit_converter
                    value = float(table[i,2])
                elif table[i,1].lower() == "degree":
                    options = ["degree","rad","min","sec"]
                    function = angle_unit_converter
                    value = float(table[i,2])
                elif table[i,1].lower() == "w/m.k":
                    options = ["W/m.K","Btu/hr.ft.F"]
                    function = Thermal_K_unit_converter
                    value = float(table[i,2])
                elif table[i,1].lower() == "w/m^2.k":
                    options = ["W/m^2.K","Btu/hr.ft^2.F"]
                    function = HTC_unit_converter
                    value = float(table[i,2])
                elif table[i,1].lower() == "s":
                    options = ["sec","min","hr"]
                    function = time_converter
                    value = float(table[i,2])
                elif table[i,1].lower() == "w/w":
                    options = ["W/W","(Btu/hr)/W"]
                    function = COP_converter
                    value = float(table[i,2])
                elif table[i,1].lower() == "j/kg.k":
                    options = ["J/kg.K","Btu/hr.F"]
                    function = entropy_converter
                    value = float(table[i,2])
                elif table[i,1].lower() == "w/k":
                    options = ["W/K","Btu/hr/F"]
                    function = entropy_gen_converter
                    value = float(table[i,2])
                elif table[i,1].lower() == "j/kg":
                    options = ["J/kg","Btu/lb"]
                    function = enthalpy_converter
                    value = float(table[i,2])
                elif table[i,1].lower() == "m/s":
                    options = ["m/s","m/min","m/hr","ft/s","ft/min","ft/hr"]
                    function = velocity_converter
                    value = float(table[i,2])
                Combo.addItems(options)
                Combo.function = function
                Combo.currentIndexChanged.connect(self.unit_changed)
                Combo.setObjectName(str(i))
                Combo.originalValue = value
                self.setCellWidget(i,1,Combo)
            else:
                self.setItem(i,1,QTableWidgetItem(table[i,1]))
            try:
                value = float(table[i,2])
                value = "%.5g" % float(value)
            except:
                value = table[i,2]
            self.setItem(i,2,QTableWidgetItem(value))
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)

    def unit_changed(self,new_index):
        row = int(self.sender().objectName())
        function = self.sender().function
        try:
            new_value = function(self.sender().originalValue,new_index,reverse=True)
            new_value = "%.5g" % float(new_value)
            self.setItem(row,2,QTableWidgetItem(new_value))
        except:
            import traceback
            print(traceback.format_exc())
            pass
        
    def keyPressEvent(self, event):
        super(ResultsTable_single, self).keyPressEvent(event)
        if (event.type() == QEvent.KeyPress and
            event.matches(QKeySequence.Copy)):
            self.copySelection()
        
    def copySelection(self):
        selection = self.selectedIndexes()
        if selection:
            
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
            csv.writer(stream, csv.excel_tab).writerows(table)
            cb = QApplication.clipboard()
            cb.clear(mode=cb.Clipboard )
            cb.setText(stream.getvalue(), mode=cb.Clipboard)
        return

class ResultsTable_parametric(QTableWidget):
    def __init__(self, table, header, parent=None):
        super(ResultsTable_parametric, self).__init__(parent)
        table = table[0]
        self.setColumnCount(len(table))
        self.setRowCount(len(header))
        self.setVerticalHeaderLabels(header)
        self.setWordWrap(True)
        self.setTextElideMode(Qt.ElideMiddle)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents);
        class MyDelegate(QItemDelegate):

            def createEditor(self, parent, option, index):
                return_object = QLineEdit(parent)
                return_object.setMaxLength(1000)
                return return_object
        delegate = MyDelegate()
        self.setItemDelegate(delegate)
        self.setHorizontalHeaderLabels(table[:,0])
        for i in range(len(table)):
            test = False
            for col in range(len(table[i,2:])):
                try:
                    float(table[i,col+2])
                    test = True
                    break
                except:
                    pass
            if test and (table[i,1].lower() in ["c","k","kg","w","pa","kg/s","m^3/s","m","m^2","m^3","degree","w/m.k","w/m^2.k","s","w/w","j/kg.k","w/k","j/kg","m/s"]):
                Combo = QComboBox()
                if table[i,1].lower() == "c":
                    options = ["C","K","F"]
                    function = temperature_unit_converter
                    values = []
                    for value in table[i,2:]:
                        try:
                            values.append(float(value)+273.15)
                        except:
                            values.append(value)
                elif table[i,1].lower() == "k":
                    options = ["C","F"]
                    function = temperature_diff_unit_converter
                elif table[i,1].lower() == "kg":
                    options = ["kg","lb"]
                    function = mass_unit_converter
                elif table[i,1].lower() == "w":
                    options = ["W","Btu/hr"]
                    function = power_unit_converter
                elif table[i,1].lower() == "pa":
                    options = ["Pa","kPa","MPa","bar","atm","psi"]
                    function = pressure_unit_converter
                elif table[i,1].lower() == "kg/s":
                    options = ["kg/s","kg/min","kg/hr","lb/s","lb/min","lb/hr"]
                    function = mass_flowrate_unit_converter
                elif table[i,1].lower() == "m^3/s":
                    options = ["m3/s","m3/min","m3/hr","ft3/s","ft3/min","ft3/hr"]
                    function = volume_flowrate_unit_converter
                elif table[i,1].lower() == "m":
                    options = ["m","cm","mm","ft","in"]
                    function = length_unit_converter
                elif table[i,1].lower() == "m^2":
                    options = ["m^2","cm^2","mm^2","ft^2","in^2"]
                    function = area_unit_converter
                elif table[i,1].lower() == "m^3":
                    options = ["m^3","cm^3","ft^3","in^3"]
                    function = volume_unit_converter
                elif table[i,1].lower() == "degree":
                    options = ["degree","rad","min","sec"]
                    function = angle_unit_converter
                elif table[i,1].lower() == "w/m.k":
                    options = ["W/m.K","Btu/hr.ft.F"]
                    function = Thermal_K_unit_converter
                elif table[i,1].lower() == "w/m^2.k":
                    options = ["W/m^2.K","Btu/hr.ft^2.F"]
                    function = HTC_unit_converter
                elif table[i,1].lower() == "s":
                    options = ["sec","min","hr"]
                    function = time_converter
                elif table[i,1].lower() == "w/w":
                    options = ["W/W","(Btu/hr)/W"]
                    function = COP_converter
                elif table[i,1].lower() == "j/kg.k":
                    options = ["J/kg.K","Btu/hr.F"]
                    function = entropy_converter
                elif table[i,1].lower() == "w/k":
                    options = ["W/K","Btu/hr/F"]
                    function = entropy_gen_converter
                elif table[i,1].lower() == "j/kg":
                    options = ["J/kg","Btu/lb"]
                    function = enthalpy_converter
                elif table[i,1].lower() == "m/s":
                    options = ["m/s","m/min","m/hr","ft/s","ft/min","ft/hr"]
                    function = velocity_converter
                try:
                    values
                except:
                    values = []
                    for value in table[i,2:]:
                        try:
                            values.append(float(value))
                        except:
                            values.append(value)
                
                Combo.addItems(options)
                Combo.function = function
                Combo.currentIndexChanged.connect(self.unit_changed)
                Combo.setObjectName(str(i))
                Combo.originalValues = values
                self.setCellWidget(0,i,Combo)
            else:
                values = table[i,2:]
            for row,value in enumerate(values):
                try:
                    value = "%.5g" % float(value)
                except:
                    pass
                # if (isinstance(value,str) and len(value) > 20):
                #     words = value.split(" ")
                #     sentences = []
                #     total_length = 0
                #     sentence = ""
                #     finished = False
                #     i = 0
                #     while not finished:
                #         if i == len(words):
                #             sentences.append(deepcopy(sentence.strip()))                            
                #             finished = True
                #         else:
                #             if total_length < 20:
                #                 sentence = sentence + words[i] + " "
                #                 total_length += len(words[i])
                #                 i += 1
                #             else:
                #                 sentences.append(deepcopy(sentence.strip()))
                #                 sentence = ""
                #                 total_length = 0                    
                #     value = "\n".join(sentences)
                self.setItem(row+1,i,QTableWidgetItem(value))
            try:
                Combo.setCurrentIndex(1)
                Combo.setCurrentIndex(0)
            except:
                pass
            del values
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)

    def unit_changed(self,new_index):
        col = int(self.sender().objectName())
        function = self.sender().function
        try:
            for row,value in enumerate(self.sender().originalValues):
                if isinstance(value,float):
                    new_value = function(value,new_index,reverse=True)
                    new_value = "%.5g" % float(new_value)
                    self.setItem(row+1,col,QTableWidgetItem(new_value))
        except:
            import traceback
            print(traceback.format_exc())
            pass

    def keyPressEvent(self, event):
        super(ResultsTable_parametric, self).keyPressEvent(event)
        if (event.type() == QEvent.KeyPress and
            event.matches(QKeySequence.Copy)):
            self.copySelection()
        
    def copySelection(self):
        selection = self.selectedIndexes()
        if selection:
            
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
            csv.writer(stream, csv.excel_tab).writerows(table)
            cb = QApplication.clipboard()
            cb.clear(mode=cb.Clipboard )
            cb.setText(stream.getvalue(), mode=cb.Clipboard)
        return

class ResultsTabsWidget(QWidget):
    def __init__(self, Cycles=None,outputs=None,parameters=None,parent=None,mode="AC"):
        super(ResultsTabsWidget, self).__init__(parent)
        if mode == "AC":
            condenser_name = "Outdoor Unit"
            evaporator_name = "Indoor Unit"
        elif mode == "HP":
            condenser_name = "Indoor Unit"
            evaporator_name = "Outdoor Unit"
            
        if not Cycles is None:
            ResultsTable = ResultsTable_single
            if not isinstance(Cycles,list):
                Cycles = [[1,Cycles]]
            # create tables
            if len(Cycles) > 1:
                Configurations = []
                for i,Cycle in enumerate(Cycles):
                    if Cycle[0]:
                        Configurations.append("Configuration "+str(i+1))
                header = ["Unit"]+Configurations
            else:
                header = ["Parameter","Unit","Value"]
            Plot = True
            self.Plots = PlotsWidget(Cycles[0][1],mode)
            outputs = create_outputs_array(Cycles)
            for Cycle in Cycles:
                if Cycle[0]:
                    Cycle = Cycle[1]
                    break
                
        elif not outputs is None:
            Plot = False
            ResultsTable = ResultsTable_parametric
            Configurations = []
            outputs_list = []
            for i,output in enumerate(outputs):                    
                Configurations.append("Configuration "+str(output[0]))
                outputs_list.append(output[1])
            header = ["Unit"]+Configurations
            Cycle = values()
            Cycle.Condenser = values()
            Cycle.Evaporator = values()
            Cycle.Condenser.Circuits = [i for i in range(parameters['N_condenser_circuits'])]
            Cycle.Evaporator.Circuits = [i for i in range(parameters['N_evaporator_circuits'])]
            Cycle.Condenser_Type = parameters['Condenser_Type']
            Cycle.Evaporator_Type = parameters['Evaporator_Type']
            if parameters['Capillary']:
                Cycle.Capillary = True
            outputs = concatenate_outputs(outputs_list)
            Plot = True
            self.Plots = PlotsParamWidget(outputs, mode)
        
        self.Cycle_table = ResultsTable(outputs[outputs[:,0] == "Cycle",1],header)
        self.Cycle_table.setColumnWidth(1,70);
        self.Compressor_table = ResultsTable(outputs[outputs[:,0] == "Compressor",1],header)
        if Cycle.Condenser_Type == "Fin-tube":
            self.Condenser_table = ResultsTable(outputs[outputs[:,0] == "Condenser",1],header)
            self.Condenser_Circuits_tables = []
            for i,Circuit in enumerate(Cycle.Condenser.Circuits):
                self.Condenser_Circuits_tables.append(ResultsTable(outputs[outputs[:,0] == "Condenser Circuit "+str(i+1),1],header))
            self.Condenser_Fan_table = ResultsTable(outputs[outputs[:,0] == "Condenser Fan",1],header)
        elif Cycle.Condenser_Type.lower() == "microchannel":
            self.Condenser_table = ResultsTable(outputs[outputs[:,0] == "Condenser",1],header)
            self.Condenser_Fan_table = ResultsTable(outputs[outputs[:,0] == "Condenser Fan",1],header)
        if Cycle.Evaporator_Type == "Fin-tube":
            self.Evaporator_table = ResultsTable(outputs[outputs[:,0] == "Evaporator",1],header)
            self.Evaporator_Circuits_tables = []
            for i,Circuit in enumerate(Cycle.Evaporator.Circuits):
                self.Evaporator_Circuits_tables.append(ResultsTable(outputs[outputs[:,0] == "Evaporator Circuit "+str(i+1),1],header))
            self.Evaporator_Fan_table = ResultsTable(outputs[outputs[:,0] == "Evaporator Fan",1],header)
        elif Cycle.Evaporator_Type.lower() == "microchannel":
            self.Evaporator_table = ResultsTable(outputs[outputs[:,0] == "Evaporator",1],header)
            self.Evaporator_Fan_table = ResultsTable(outputs[outputs[:,0] == "Evaporator Fan",1],header)
        self.Liquid_Line_table = ResultsTable(outputs[outputs[:,0] == "Liquid Line",1],header)
        self._2phase_Line_table = ResultsTable(outputs[outputs[:,0] == "Two-phase Line",1],header)
        self.Suction_Line_table = ResultsTable(outputs[outputs[:,0] == "Suction Line",1],header)
        self.Discharge_Line_table = ResultsTable(outputs[outputs[:,0] == "Discharge Line",1],header)
        if hasattr(Cycle,"Capillary"):
            self.Capillary_table = ResultsTable(outputs[outputs[:,0] == "Capillary Tube",1],header)
        
        # create layout
        self.layout = QVBoxLayout() 
  
        # Initialize tab screen 
        self.tabs = QTabWidget() 
        self.Cycle_tab = QWidget()
        self.Compressor_tab = QWidget()
        self.Condenser_tab = QWidget()
        self.Evaporator_tab = QWidget()
        self.Liquid_Line_tab = QWidget()
        self._2phase_Line_tab = QWidget()
        self.Suction_Line_tab = QWidget()
        self.Discharge_Line_tab = QWidget()
        if hasattr(Cycle,"Capillary"):
            self.Capillary_tab = QWidget()
        if Plot:
            self.Plots_tab = QWidget()
        
        # Add tabs 
        self.tabs.addTab(self.Cycle_tab, "Cycle") 
        self.tabs.addTab(self.Compressor_tab, "Compressor") 
        self.tabs.addTab(self.Condenser_tab, condenser_name) 
        self.tabs.addTab(self.Evaporator_tab, evaporator_name) 
        self.tabs.addTab(self.Liquid_Line_tab, "Liquid Line") 
        self.tabs.addTab(self._2phase_Line_tab, "Two-phase Line") 
        self.tabs.addTab(self.Suction_Line_tab, "Suction Line") 
        self.tabs.addTab(self.Discharge_Line_tab, "Discharge Line") 
        if hasattr(Cycle,"Capillary"):
            self.tabs.addTab(self.Capillary_tab, "Capillary Tube") 
        if Plot:
            self.tabs.addTab(self.Plots_tab, "Plots")

        # Create Cycle tab 
        self.Cycle_tab.layout = QHBoxLayout() 
        self.Cycle_tab.layout.addWidget(self.Cycle_table) 
        self.Cycle_tab.setLayout(self.Cycle_tab.layout) 

        # Create Compressor tab 
        self.Compressor_tab.layout = QHBoxLayout() 
        self.Compressor_tab.layout.addWidget(self.Compressor_table) 
        self.Compressor_tab.setLayout(self.Compressor_tab.layout) 

        # Create Condenser tab
        if Cycle.Condenser_Type == "Fin-tube":
            # create layout
            self.Condenser_tab.layout = QVBoxLayout() 
            # Initialize tab screen 
            self.Condenser_tabs = QTabWidget() 
            self.Condenser_main_tab = QWidget()
            self.Condenser_circuits_tabs = []
            for i in range(len(self.Condenser_Circuits_tables)):
                self.Condenser_circuits_tabs.append(QWidget())
            self.Condenser_Fan_tab = QWidget()

            # Add tabs
            self.Condenser_tabs.addTab(self.Condenser_main_tab, "Overall") 
            for i,tab in enumerate(self.Condenser_circuits_tabs):
                self.Condenser_tabs.addTab(tab, "Circuit "+str(i+1)) 
            self.Condenser_tabs.addTab(self.Condenser_Fan_tab, "Fan") 

            # Create Main tab 
            self.Condenser_main_tab.layout = QHBoxLayout() 
            self.Condenser_main_tab.layout.addWidget(self.Condenser_table) 
            self.Condenser_main_tab.setLayout(self.Condenser_main_tab.layout) 

            # Create Circuits tabs
            for i,tab in enumerate(self.Condenser_circuits_tabs):
                tab.layout = QHBoxLayout() 
                tab.layout.addWidget(self.Condenser_Circuits_tables[i]) 
                tab.setLayout(tab.layout) 

            # Create Fan tab 
            self.Condenser_Fan_tab.layout = QHBoxLayout() 
            self.Condenser_Fan_tab.layout.addWidget(self.Condenser_Fan_table) 
            self.Condenser_Fan_tab.setLayout(self.Condenser_Fan_tab.layout) 

            # Add tabs to widget 
            self.Condenser_tab.layout.addWidget(self.Condenser_tabs)
            self.Condenser_tab.setLayout(self.Condenser_tab.layout)
            
        elif Cycle.Condenser_Type.lower() == "microchannel":
            # create layout
            self.Condenser_tab.layout = QVBoxLayout() 
            # Initialize tab screen 
            self.Condenser_tabs = QTabWidget() 
            self.Condenser_main_tab = QWidget()
            self.Condenser_Fan_tab = QWidget()

            # Add tabs
            self.Condenser_tabs.addTab(self.Condenser_main_tab, "Overall") 
            self.Condenser_tabs.addTab(self.Condenser_Fan_tab, "Fan") 

            # Create Main tab 
            self.Condenser_main_tab.layout = QHBoxLayout() 
            self.Condenser_main_tab.layout.addWidget(self.Condenser_table) 
            self.Condenser_main_tab.setLayout(self.Condenser_main_tab.layout) 

            # Create Fan tab 
            self.Condenser_Fan_tab.layout = QHBoxLayout() 
            self.Condenser_Fan_tab.layout.addWidget(self.Condenser_Fan_table) 
            self.Condenser_Fan_tab.setLayout(self.Condenser_Fan_tab.layout) 

            # Add tabs to widget 
            self.Condenser_tab.layout.addWidget(self.Condenser_tabs)
            self.Condenser_tab.setLayout(self.Condenser_tab.layout) 

        # Create Evaporator tab
        if Cycle.Evaporator_Type == "Fin-tube":
            # create layout
            self.Evaporator_tab.layout = QVBoxLayout() 
            # Initialize tab screen 
            self.Evaporator_tabs = QTabWidget() 
            self.Evaporator_main_tab = QWidget()
            self.Evaporator_circuits_tabs = []
            for i in range(len(self.Evaporator_Circuits_tables)):
                self.Evaporator_circuits_tabs.append(QWidget())
            self.Evaporator_Fan_tab = QWidget()

            # Add tabs
            self.Evaporator_tabs.addTab(self.Evaporator_main_tab, "Overall") 
            for i,tab in enumerate(self.Evaporator_circuits_tabs):
                self.Evaporator_tabs.addTab(tab, "Circuit "+str(i+1)) 
            self.Evaporator_tabs.addTab(self.Evaporator_Fan_tab, "Fan") 

            # Create Main tab 
            self.Evaporator_main_tab.layout = QHBoxLayout() 
            self.Evaporator_main_tab.layout.addWidget(self.Evaporator_table) 
            self.Evaporator_main_tab.setLayout(self.Evaporator_main_tab.layout) 

            # Create Circuits tabs
            for i,tab in enumerate(self.Evaporator_circuits_tabs):
                tab.layout = QHBoxLayout() 
                tab.layout.addWidget(self.Evaporator_Circuits_tables[i]) 
                tab.setLayout(tab.layout) 

            # Create Main tab 
            self.Evaporator_Fan_tab.layout = QHBoxLayout() 
            self.Evaporator_Fan_tab.layout.addWidget(self.Evaporator_Fan_table) 
            self.Evaporator_Fan_tab.setLayout(self.Evaporator_Fan_tab.layout) 

            # Add tabs to widget 
            self.Evaporator_tab.layout.addWidget(self.Evaporator_tabs)
            self.Evaporator_tab.setLayout(self.Evaporator_tab.layout) 
        elif Cycle.Evaporator_Type.lower() == "microchannel":
            # create layout
            self.Evaporator_tab.layout = QVBoxLayout() 
            # Initialize tab screen 
            self.Evaporator_tabs = QTabWidget() 
            self.Evaporator_main_tab = QWidget()
            self.Evaporator_circuits_tabs = []
            self.Evaporator_Fan_tab = QWidget()

            # Add tabs
            self.Evaporator_tabs.addTab(self.Evaporator_main_tab, "Overall") 
            self.Evaporator_tabs.addTab(self.Evaporator_Fan_tab, "Fan") 

            # Create Main tab 
            self.Evaporator_main_tab.layout = QHBoxLayout() 
            self.Evaporator_main_tab.layout.addWidget(self.Evaporator_table) 
            self.Evaporator_main_tab.setLayout(self.Evaporator_main_tab.layout) 

            # Create Main tab 
            self.Evaporator_Fan_tab.layout = QHBoxLayout() 
            self.Evaporator_Fan_tab.layout.addWidget(self.Evaporator_Fan_table) 
            self.Evaporator_Fan_tab.setLayout(self.Evaporator_Fan_tab.layout) 

            # Add tabs to widget 
            self.Evaporator_tab.layout.addWidget(self.Evaporator_tabs)
            self.Evaporator_tab.setLayout(self.Evaporator_tab.layout) 

        # Create Liquid Line tab 
        self.Liquid_Line_tab.layout = QHBoxLayout() 
        self.Liquid_Line_tab.layout.addWidget(self.Liquid_Line_table) 
        self.Liquid_Line_tab.setLayout(self.Liquid_Line_tab.layout) 

        # Create 2phase Line tab 
        self._2phase_Line_tab.layout = QHBoxLayout() 
        self._2phase_Line_tab.layout.addWidget(self._2phase_Line_table) 
        self._2phase_Line_tab.setLayout(self._2phase_Line_tab.layout) 

        # Create Suction Line tab 
        self.Suction_Line_tab.layout = QHBoxLayout() 
        self.Suction_Line_tab.layout.addWidget(self.Suction_Line_table) 
        self.Suction_Line_tab.setLayout(self.Suction_Line_tab.layout) 

        # Create Discharge Line tab 
        self.Discharge_Line_tab.layout = QHBoxLayout() 
        self.Discharge_Line_tab.layout.addWidget(self.Discharge_Line_table) 
        self.Discharge_Line_tab.setLayout(self.Discharge_Line_tab.layout) 

        if hasattr(Cycle,"Capillary"):
            # Create Capillary tab
            self.Capillary_tab.layout = QHBoxLayout() 
            self.Capillary_tab.layout.addWidget(self.Capillary_table) 
            self.Capillary_tab.setLayout(self.Capillary_tab.layout) 

        if Plot:        
            # Create Plots tab 
            self.Plots_tab.layout = QHBoxLayout() 
            self.Plots_tab.layout.addWidget(self.Plots) 
            self.Plots_tab.setLayout(self.Plots_tab.layout) 
        
        # Add tabs to widget 
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout) 

class ResultsTabsWidget_Fintube(QWidget):
    def __init__(self, HX,parent=None):
        super(ResultsTabsWidget_Fintube, self).__init__(parent)
        # create tables
        header = ["Parameter","Unit","Value"]
        self.HX_table = ResultsTable_single((construct_table(HX.OutputList()),),header)
        self.HX_Circuits_tables = []
        for Circuit in HX.Circuits:
            self.HX_Circuits_tables.append(ResultsTable_single((construct_table(Circuit.OutputList()),),header))
        self.HX_Fan_table = ResultsTable_single((construct_table(HX.Fan.OutputList()),),header)

        # create layout
        self.layout = QVBoxLayout() 
        # Initialize tab screen 
        self.HX_tabs = QTabWidget() 
        self.HX_main_tab = QWidget()
        self.HX_circuits_tabs = []
        for i in range(len(self.HX_Circuits_tables)):
            self.HX_circuits_tabs.append(QWidget())
        self.HX_Fan_tab = QWidget()

        # Add tabs
        self.HX_tabs.addTab(self.HX_main_tab, "Overall") 
        for i,tab in enumerate(self.HX_circuits_tabs):
            self.HX_tabs.addTab(tab, "Circuit "+str(i+1)) 
        self.HX_tabs.addTab(self.HX_Fan_tab, "Fan") 

        # Create Main tab 
        self.HX_main_tab.layout = QHBoxLayout() 
        self.HX_main_tab.layout.addWidget(self.HX_table) 
        self.HX_main_tab.setLayout(self.HX_main_tab.layout) 

        # Create Circuits tabs
        for i,tab in enumerate(self.HX_circuits_tabs):
            tab.layout = QHBoxLayout() 
            tab.layout.addWidget(self.HX_Circuits_tables[i]) 
            tab.setLayout(tab.layout) 

        # Create Fan tab 
        self.HX_Fan_tab.layout = QHBoxLayout() 
        self.HX_Fan_tab.layout.addWidget(self.HX_Fan_table) 
        self.HX_Fan_tab.setLayout(self.HX_Fan_tab.layout) 

        # create export button
        self.button_layout = QHBoxLayout()
        self.export_button = QPushButton(self)
        self.export_button.setText("Export to Excel")
        self.button_layout.addWidget(self.export_button)
        self.button_layout.addStretch()
        
        # Add tabs to widget 
        self.layout.addWidget(self.HX_tabs)
        self.layout.addLayout(self.button_layout)
        self.setLayout(self.layout) 

class ResultsTabsWidget_Microchannel(QWidget):
    def __init__(self, HX,parent=None):
        super(ResultsTabsWidget_Microchannel, self).__init__(parent)
        # create tables
        header = ["Parameter","Unit","Value"]
        self.HX_table = ResultsTable_single((construct_table(HX.OutputList()),),header)
        self.HX_Fan_table = ResultsTable_single((construct_table(HX.Fan.OutputList()),),header)

        # create layout
        self.layout = QVBoxLayout() 
        # Initialize tab screen 
        self.HX_tabs = QTabWidget() 
        self.HX_main_tab = QWidget()
        self.HX_Fan_tab = QWidget()

        # Add tabs
        self.HX_tabs.addTab(self.HX_main_tab, "Overall") 
        self.HX_tabs.addTab(self.HX_Fan_tab, "Fan") 

        # Create Main tab 
        self.HX_main_tab.layout = QHBoxLayout() 
        self.HX_main_tab.layout.addWidget(self.HX_table) 
        self.HX_main_tab.setLayout(self.HX_main_tab.layout) 

        # Create Fan tab 
        self.HX_Fan_tab.layout = QHBoxLayout() 
        self.HX_Fan_tab.layout.addWidget(self.HX_Fan_table) 
        self.HX_Fan_tab.setLayout(self.HX_Fan_tab.layout) 

        # create export button
        self.button_layout = QHBoxLayout()
        self.export_button = QPushButton(self)
        self.export_button.setText("Export to Excel")
        self.button_layout.addWidget(self.export_button)
        self.button_layout.addStretch()
        
        # Add tabs to widget 
        self.layout.addWidget(self.HX_tabs)
        self.layout.addLayout(self.button_layout)
        self.setLayout(self.layout) 

class ResultsTabsWidget_Line(QWidget):
    def __init__(self, Line,parent=None):
        super(ResultsTabsWidget_Line, self).__init__(parent)
        # create tables
        header = ["Parameter","Unit","Value"]
        self.Line_table = ResultsTable_single((construct_table(Line.OutputList()),),header)

        # create layout
        self.layout = QVBoxLayout() 

        # create export button
        self.button_layout = QHBoxLayout()
        self.export_button = QPushButton(self)
        self.export_button.setText("Export to Excel")
        self.button_layout.addWidget(self.export_button)
        self.button_layout.addStretch()
        
        # Add tabs to widget 
        self.layout.addWidget(self.Line_table)
        self.layout.addLayout(self.button_layout)
        self.setLayout(self.layout)

class ResultsTabsWidget_Capillary(QWidget):
    def __init__(self, Capillary,parent=None):
        super(ResultsTabsWidget_Capillary, self).__init__(parent)
        # create tables
        header = ["Parameter","Unit","Value"]
        self.Capillary_table = ResultsTable_single((construct_table(Capillary.OutputList()),),header)

        # create layout
        self.layout = QVBoxLayout() 

        # create export button
        self.button_layout = QHBoxLayout()
        self.export_button = QPushButton(self)
        self.export_button.setText("Export to Excel")
        self.button_layout.addWidget(self.export_button)
        self.button_layout.addStretch()
        
        # Add tabs to widget 
        self.layout.addWidget(self.Capillary_table)
        self.layout.addLayout(self.button_layout)
        self.setLayout(self.layout)

class ResultsTabsWidget_Compressor(QWidget):
    def __init__(self, Compressor,parent=None):
        super(ResultsTabsWidget_Compressor, self).__init__(parent)
        # create tables
        header = ["Parameter","Unit","Value"]
        self.Compressor_table = ResultsTable_single((construct_table(Compressor.OutputList()),),header)

        # create layout
        self.layout = QVBoxLayout() 

        # create export button
        self.button_layout = QHBoxLayout()
        self.export_button = QPushButton(self)
        self.export_button.setText("Export to Excel")
        self.button_layout.addWidget(self.export_button)
        self.button_layout.addStretch()
        
        # Add tabs to widget 
        self.layout.addWidget(self.Compressor_table)
        self.layout.addLayout(self.button_layout)
        self.setLayout(self.layout)
