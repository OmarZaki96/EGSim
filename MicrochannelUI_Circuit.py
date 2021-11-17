from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
import CoolProp as CP
import os, sys
from GUI_functions import *
from CoolProp.CoolProp import HAPropsSI
from sympy.parsing.sympy_parser import parse_expr
from sympy import S, Symbol
from math import pi
from copy import deepcopy

FROM_Microchannel_Circuit_Main,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Microchannel_bank_circuit_define.ui"))

class values():
    pass

class Microchannel_Circuit_Window(QDialog, FROM_Microchannel_Circuit_Main):
    def __init__(self, parent=None):
        # first UI
        super(Microchannel_Circuit_Window, self).__init__(parent)
        self.setupUi(self)
        self.Microchannel_circuit_cancel_button.clicked.connect(self.cancel_button)
        self.Microchannel_bank_number_choose.currentIndexChanged.connect(self.update_table)
        self.Microchannel_bank_number_passes.valueChanged.connect(self.N_passes_changed)
        self.Microchannel_circuit_ok_button.clicked.connect(self.ok_button)
        self.Microchannel_N_tubes_per_pass_table.itemChanged.connect(self.update_values)
        self.bank_passes = [[1]]
        class MyDelegate(QItemDelegate):
            def createEditor(self, parent, option, index):
                return_object = QLineEdit(parent)
                only_number = QIntValidator(0,999999)
                return_object.setValidator(only_number)
                return return_object
        delegate = MyDelegate()
        self.Microchannel_N_tubes_per_pass_table.setItemDelegate(delegate)
        self.Microchannel_N_tubes_per_pass_table.installEventFilter(self)

    def eventFilter(self, source, event):
        if (event.type() == QEvent.KeyPress and
            event.matches(QKeySequence.Copy)):
            self.copySelection()
            return True
        if (event.type() == QEvent.KeyPress and
            event.matches(QKeySequence.Paste)):
            self.pasteSelection()
            return True
        return super(Microchannel_Circuit_Window, self).eventFilter(source, event)

    def copySelection(self):
        selection = self.FinTube_Distrubution.selectedIndexes()
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
            csv.writer(stream, delimiter='\t').writerows(table)
            qApp.clipboard().setText(stream.getvalue())
        return

    def pasteSelection(self,table_number):
        selection = self.FinTube_Distrubution.selectedIndexes()
        if selection:
            model = self.FinTube_Distrubution.model()
            buffer = qApp.clipboard().text() 
            rows = sorted(index.row() for index in selection)
            columns = sorted(index.column() for index in selection)
            reader = csv.reader(io.StringIO(buffer), delimiter='\t')
            if len(rows) == 1 and len(columns) == 1:
                for i, line in enumerate(reader):
                    for j, cell in enumerate(line):
                        model.setData(model.index(rows[0]+i,columns[0]+j), cell)
            else:
                arr = [ [ cell for cell in row ] for row in reader]
                for index in selection:
                    row = index.row() - rows[0]
                    column = index.column() - columns[0]
                    model.setData(model.index(index.row(), index.column()), arr[row][column])
        return
        
    def update_UI(self):
        self.Microchannel_bank_number_choose.addItems([str(i+1) for i in range(self.N_bank)])
        self.bank_passes = [[0] for i in range(self.N_bank)]
        self.update_table()
    
    def update_table(self):
        bank_passes = deepcopy(self.bank_passes)
        current_bank = int(self.Microchannel_bank_number_choose.currentIndex())
        number_of_passes = len(self.bank_passes[current_bank])
        self.Microchannel_bank_number_passes.setValue(number_of_passes)
        self.Microchannel_N_tubes_per_pass_table.setRowCount(number_of_passes)
        self.Microchannel_N_tubes_per_pass_table.setVerticalHeaderLabels(["Pass "+str(i+1) for i in range(number_of_passes)])
        for i in range(number_of_passes):
            self.Microchannel_N_tubes_per_pass_table.setItem(i,0,QTableWidgetItem(str(bank_passes[current_bank][i])))
            self.bank_passes = bank_passes
    
    def update_values(self):
        current_bank = int(self.Microchannel_bank_number_choose.currentIndex())
        number_of_passes = int(self.Microchannel_bank_number_passes.value())
        for i in range(number_of_passes):
            if self.Microchannel_N_tubes_per_pass_table.item(i,0) != None:
                self.bank_passes[current_bank][i] = int(self.Microchannel_N_tubes_per_pass_table.item(i,0).text())
        
    def N_passes_changed(self):
        current_bank = int(self.Microchannel_bank_number_choose.currentIndex())
        current_N_passes = int(self.Microchannel_bank_number_passes.value())
        saved_N_passes = len(self.bank_passes[current_bank])
        if current_N_passes > saved_N_passes:
            rows = self.Microchannel_N_tubes_per_pass_table.rowCount()
            while (current_N_passes != rows):
                self.Microchannel_N_tubes_per_pass_table.insertRow(rows)
                self.bank_passes[current_bank].append(0)
                rows = self.Microchannel_N_tubes_per_pass_table.rowCount()

        elif current_N_passes < saved_N_passes:
            rows = self.Microchannel_N_tubes_per_pass_table.rowCount()
            while (current_N_passes != rows):
                self.Microchannel_N_tubes_per_pass_table.removeRow(rows-1)
                rows = self.Microchannel_N_tubes_per_pass_table.rowCount()
                del self.bank_passes[current_bank][-1]
        self.Microchannel_N_tubes_per_pass_table.setVerticalHeaderLabels(["Pass "+str(i+1) for i in range(current_N_passes)])
        for i in range(current_N_passes):
            self.Microchannel_N_tubes_per_pass_table.setItem(i,0,QTableWidgetItem(str(self.bank_passes[current_bank][i])))
        
    def validate(self):
        for i,bank in enumerate(self.bank_passes):
            if not (sum(bank) == self.N_tube_per_bank):
                return (0,i)
        return (1,1)
    
    def ok_button(self):
        check = self.validate()
        if check[0]:
            self.Circuiting = values()
            self.Circuiting.defined = True
            self.Circuiting.bank_passes = self.bank_passes
            self.close()
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Total Number of Tubes of bank "+str(check[1]+1)+" should equal to "+str(self.N_tube_per_bank))
            msg.setWindowTitle("Error!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
    
    def cancel_button(self):
        self.close()
        
if __name__ == '__main__':
    def main():
        app=QApplication(sys.argv)
        app.setStyle('Fusion')
        window = Microchannel_Circuit_Window()
        window.show()
        app.exec_()
    try:
        main()
    except Exception as why:
        print(why)

