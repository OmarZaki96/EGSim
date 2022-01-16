from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import io,csv
from itertools import product
import numpy as np

class Parametric_table(QTableWidget):
    def __init__(self, parametric_data, mode, parent=None):
        super(Parametric_table, self).__init__(parent)
        
        if mode == "HP":
            Evaporator_name = "Outdoor Unit "
            Condenser_name = "Indoor Unit "
        elif mode == "AC":
            Evaporator_name = "Indoor Unit "
            Condenser_name = "Outdoor Unit "
            
        if parent.First_condition.currentIndex() == 0:
            first_condition = 'subcooling'
        else:
            first_condition = 'charge'
        
        comp_names = []
        for comp in parent.Comp_names:
            comp_names.append(comp[1])
        
        if parent.Evaporator_type.currentIndex() == 0:
            evaporator_type = 'Fintube'
        else:
            evaporator_type = 'Microchannel'

        if parent.Condenser_type.currentIndex() == 0:
            condenser_type = 'Fintube'
        else:
            condenser_type = 'Microchannel'
        
        properties = {'first_condition':first_condition,
                      'comp_names':comp_names,
                      'evaporator_type':evaporator_type,
                      'condenser_type':condenser_type,
                      'evaporator_name':Evaporator_name,
                      'condenser_name':Condenser_name,
                      }
        parameters,table = parameter_table(parametric_data,properties)
        self.setRowCount(len(table)+1)
        self.setColumnCount(len(parameters))
        self.setHorizontalHeaderLabels([i[0] for i in parameters])
        self.setVerticalHeaderLabels(['Unit']+["Configuration "+str(i+1) for i in range(len(table))])
        for i in range(len(parameters)):
            self.setItem(0,i,QTableWidgetItem(parameters[i][1]))
        for i in range(len(table)):
            for j in range(len(parameters)):
                try:
                    value = float(table[i,j])
                    value = "%.5g" % value
                except:
                    value = table[i,j]
                self.setItem(i+1,j,QTableWidgetItem(value))
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        
    def keyPressEvent(self, event):
        super(Parametric_table, self).keyPressEvent(event)
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

def parameter_table(parametric_data,properties):
    parameters = []
    parameters_names = []
    if parametric_data[2,0]:
        compressors,compressors_list = create_parametric_compressors(parametric_data[2,1],properties['comp_names'])
        parameters+=compressors
        parameters_names+=compressors_list
    if parametric_data[8,0]:
        condensers,condensers_list = create_parametric_condensers(parametric_data[8,1],properties['condenser_type'],properties['condenser_name'])
        parameters+=condensers
        parameters_names+=condensers_list
    if parametric_data[7,0]:
        evaporators,evaporators_list = create_parametric_evaporators(parametric_data[7,1],properties['evaporator_type'],properties['evaporator_name'])
        parameters+=evaporators
        parameters_names+=evaporators_list
    if parametric_data[3,0]:
        Lines_liquid,Lines_liquid_list = create_parametric_liquids(parametric_data[3,1])
        parameters+=Lines_liquid
        parameters_names+=Lines_liquid_list
    if parametric_data[5,0]:
        Lines_suction,Lines_suction_list = create_parametric_suctions(parametric_data[5,1])
        parameters+=Lines_suction
        parameters_names+=Lines_suction_list
    if parametric_data[6,0]:
        Lines_discharge,Lines_discharge_list = create_parametric_discharges(parametric_data[6,1])
        parameters+=Lines_discharge
        parameters_names+=Lines_discharge_list
    if parametric_data[4,0]:
        Lines_2phase,Lines_2phase_list = create_parametric_2phases(parametric_data[4,1])
        parameters+=Lines_2phase
        parameters_names+=Lines_2phase_list
    if parametric_data[0,0]:
        options,options_list = create_parametric_options(parametric_data[0,1],properties['first_condition'])
        parameters+=options
        parameters_names+=options_list
    if parametric_data[1,0]:
        capillaries,capillaries_list = create_parametric_capillaries(parametric_data[1,1])
        parameters+=capillaries
        parameters_names+=capillaries_list
    objects = product(*parameters)
    number_of_configurations = np.prod([len(i) for i in parameters])
    values = np.zeros([number_of_configurations,len(parameters_names)],dtype=object)
    for i,row in enumerate(objects):
        values[i,:] = row
    return parameters_names,np.array(values)

def create_parametric_options(data,first_condition):
    parameters_list = []
    parameters_names_list = []
    if first_condition == "subcooling":
        if data[0,0]: # subcooling
            parameters_list.append(tuple(data[0,1]))
            parameters_names_list.append(['Cycle Subcooling','C'])
    elif first_condition == "charge":
        if data[0,0]: # subcooling
            parameters_list.append(tuple(data[0,1]))
            parameters_names_list.append(['System Charge','kg'])
    for i in range(1,len(data)):
        if data[i,0]:
            parameters_list.append(tuple(data[i,1]))
            parameters_names_list.append([data[i,2],data[i,3]])
    return parameters_list,parameters_names_list
    
def create_parametric_capillaries(data):
    parameters_list = []
    parameters_names_list = []
    for i in range(len(data)):
        if data[i,0]:
            parameters_list.append(tuple(data[i,1]))
            parameters_names_list.append([data[i,2],data[i,3]])
    return parameters_list,parameters_names_list
    
def create_parametric_compressors(data,comp_names):
    parameters_list = []
    parameters_names_list = []
    for i in range(len(data)-1):
        if data[i,0]:
            if i in [1,2]:
                parameters_list.append(tuple(np.array(data[i,1])*100))
            else:
                parameters_list.append(tuple(data[i,1]))
            parameters_names_list.append([data[i,2],data[i,3]])
    if data[len(data)-1,0]:
        parameters_list.append(tuple([str(value+1)+":"+comp_names[value] for value in data[len(data)-1,1]]))
        parameters_names_list.append([data[len(data)-1,2],data[len(data)-1,3]])
    return parameters_list,parameters_names_list

def create_parametric_liquids(data):
    parameters_list = []
    parameters_names_list = []
    for i in range(len(data)):
        if data[i,0]:
            parameters_list.append(tuple(data[i,1]))
            parameters_names_list.append(["Liquid "+data[i,2],data[i,3]])
    return parameters_list,parameters_names_list

def create_parametric_2phases(data):
    parameters_list = []
    parameters_names_list = []
    for i in range(len(data)):
        if data[i,0]:
            parameters_list.append(list(data[i,1]))
            parameters_names_list.append(["Two-phase "+data[i,2],data[i,3]])
    return parameters_list,parameters_names_list

def create_parametric_suctions(data):
    parameters_list = []
    parameters_names_list = []
    for i in range(len(data)):
        if data[i,0]:
            parameters_list.append(tuple(data[i,1]))
            parameters_names_list.append(["Suction "+data[i,2],data[i,3]])
    return parameters_list,parameters_names_list

def create_parametric_discharges(data):
    parameters_list = []
    parameters_names_list = []
    for i in range(len(data)):
        if data[i,0]:
            parameters_list.append(tuple(data[i,1]))
            parameters_names_list.append(["Discharge "+data[i,2],data[i,3]])
    return parameters_list,parameters_names_list

def create_parametric_evaporators(data,HX_type,name):
    if HX_type == "Fintube":
        # circuits data
        circuits = data[0,1]
        circuits_parameters = []
        circuits_parameters_names_list = []
        for i,circuit in enumerate(circuits):
            for i in range(len(circuit)):
                if circuit[i,0]:
                    circuits_parameters.append(tuple(circuit[i,1]))
                    circuits_parameters_names_list.append([name+circuit[i,2],circuit[i,3]])
        parameters_list = [] + circuits_parameters
        parameters_names_list = [] + circuits_parameters_names_list
        for i in range(1,len(data)):
            if data[i,0]:
                parameters_list.append(tuple(data[i,1]))
                parameters_names_list.append([name+data[i,2],data[i,3]])            
        return parameters_list,parameters_names_list
    else: # microchannel
        parameters_list = []
        parameters_names_list = []
        for i in range(len(data)):
            if data[i,0]:
                parameters_list.append(tuple(data[i,1]))
                parameters_names_list.append([name+data[i,2],data[i,3]])
        return parameters_list,parameters_names_list

def create_parametric_condensers(data,HX_type,name):
    if HX_type == "Fintube":
        # circuits data
        circuits = data[0,1]
        circuits_parameters = []
        circuits_parameters_names_list = []
        for i,circuit in enumerate(circuits):
            for i in range(len(circuit)):
                if circuit[i,0]:
                    circuits_parameters.append(tuple(circuit[i,1]))
                    circuits_parameters_names_list.append([name+circuit[i,2],circuit[i,3]])
        parameters_list = [] + circuits_parameters
        parameters_names_list = [] + circuits_parameters_names_list
        for i in range(1,len(data)):
            if data[i,0]:
                parameters_list.append(tuple(data[i,1]))
                parameters_names_list.append([name+data[i,2],data[i,3]])            
        return parameters_list,parameters_names_list
    else: # microchannel
        parameters_list = []
        parameters_names_list = []
        for i in range(len(data)):
            if data[i,0]:
                parameters_list.append(tuple(data[i,1]))
                parameters_names_list.append([name+data[i,2],data[i,3]])
        return parameters_list,parameters_names_list
