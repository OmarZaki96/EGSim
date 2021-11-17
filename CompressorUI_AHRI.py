from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
import os, sys, csv, io
from unit_conversion import *
from GUI_functions import load_last_location, save_last_location

FROM_Compressor_AHRI,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Compressor_define_AHRI.ui"))

class Compressor_AHRI(QDialog, FROM_Compressor_AHRI):
    def __init__(self, parent=None):
        class MyDelegate(QItemDelegate):

            def createEditor(self, parent, option, index):
                return_object = QLineEdit(parent)
                only_number = QRegExpValidator(QRegExp("[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)"))
                return_object.setValidator(only_number)
                return return_object

        super(Compressor_AHRI, self).__init__(parent)
        self.setupUi(self)
        self.Comp_AHRI_cancel_button.clicked.connect(self.cancel_button)
        self.Comp_AHRI_num_speed.valueChanged.connect(self.AHRI_num_speed_change)
        only_number = QRegExpValidator(QRegExp("(([0-9]+\.[0-9]*[1-9][0-9]*)|([0-9]*[1-9][0-9]*\.[0-9]+)|([0-9]*[1-9][0-9]*))"))
        self.Comp_AHRI_F.setValidator(only_number)
        self.Comp_nominal_speed_1.setValidator(only_number)
        self.Comp_AHRI_std_sh.setValidator(only_number)
        self.Comp_AHRI_std_suction.setValidator(only_number)
        delegate = MyDelegate()
        self.Comp_coefficients_table_1.setItemDelegate(delegate)
        for row in range(2):
            for col in range(10):
                self.Comp_coefficients_table_1.setItem(row, col, QTableWidgetItem("0"))
        self.Comp_coefficients_table_1.installEventFilter(self)
        self.Comp_AHRI_ok_button.clicked.connect(self.ok_button)
        self.Comp_AHRI_std_sh_radio.toggled.connect(self.standard_changed)
        self.Comp_AHRI_std_suction_radio.toggled.connect(self.standard_changed)
        self.Comp_AHRI_load_button.hide()
        self.Comp_AHRI_save_button.hide()

    def standard_changed(self):
        if self.Comp_AHRI_std_sh_radio.isChecked():
            self.Comp_AHRI_std_sh.setEnabled(True)
            self.Comp_AHRI_std_sh_unit.setEnabled(True)
            self.Comp_AHRI_std_suction.setEnabled(False)
            self.Comp_AHRI_std_suction_unit.setEnabled(False)
        elif self.Comp_AHRI_std_suction_radio.isChecked():
            self.Comp_AHRI_std_sh.setEnabled(False)
            self.Comp_AHRI_std_sh_unit.setEnabled(False)
            self.Comp_AHRI_std_suction.setEnabled(True)
            self.Comp_AHRI_std_suction_unit.setEnabled(True)

    def eventFilter(self, source, event):
        if (event.type() == QEvent.KeyPress and
            event.matches(QKeySequence.Copy)):
            tab_number  =  self.tabWidget.currentIndex()
            self.copySelection(tab_number+1)
            return True
        if (event.type() == QEvent.KeyPress and
            event.matches(QKeySequence.Paste)):
            tab_number  =  self.tabWidget.currentIndex()
            self.pasteSelection(tab_number+1)
            return True
        return super(Compressor_AHRI, self).eventFilter(source, event)

    def copySelection(self,table_number):
        selection = getattr(self,'Comp_coefficients_table_'+str(table_number)).selectedIndexes()
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
        selection = getattr(self,'Comp_coefficients_table_'+str(table_number)).selectedIndexes()
        if selection:
            model = getattr(self,'Comp_coefficients_table_'+str(table_number)).model()
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
        
    def cancel_button(self):
        self.close()
        
    def validate(self):
        num_speeds = int(self.Comp_AHRI_num_speed.value())
        if self.Comp_AHRI_std_sh_radio.isChecked():
            if self.Comp_AHRI_std_sh.text() in ["","-","."]:
                return 0
            
        elif self.Comp_AHRI_std_suction_radio.isChecked():
            if self.Comp_AHRI_std_suction.text() in ["","-","."]:
                return 0
            
        if self.Comp_AHRI_F.text() in ["","-","."]:
            return 0
        for i in range(num_speeds):
            if getattr(self,"Comp_nominal_speed_"+str(i+1)).text() in ["","-","."]:
                return 0
        return 1
    
    def ok_button(self):
        if self.validate():
            self.num_speeds = int(self.Comp_AHRI_num_speed.value())
            self.unit_system = self.Comp_AHRI_unitsys.currentIndex()
            if self.Comp_AHRI_std_sh_radio.isChecked():
                self.std_type = 0
                self.std_sh = temperature_diff_unit_converter(self.Comp_AHRI_std_sh.text(),self.Comp_AHRI_std_sh_unit.currentIndex())
            elif self.Comp_AHRI_std_suction_radio.isChecked():
                self.std_type = 1
                self.std_suction = temperature_unit_converter(self.Comp_AHRI_std_suction.text(),self.Comp_AHRI_std_suction_unit.currentIndex())
            self.Comp_AHRI_F_value = str(self.Comp_AHRI_F.text())
            self.speeds = []
            self.M = []
            self.P = []
            for i in range(self.num_speeds):
                self.speeds.append(float(getattr(self,"Comp_nominal_speed_"+str(i+1)).text()))
                M = []
                P = []
                for col in range(10):
                    M.append(float(getattr(self,"Comp_coefficients_table_"+str(i+1)).item(0,col).text().replace(" ","")))
                for col in range(10):
                    P.append(float(getattr(self,"Comp_coefficients_table_"+str(i+1)).item(1,col).text().replace(" ","")))
                self.M.append(M)
                self.P.append(P)
            self.close()
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please fill all empty fields")
            msg.setWindowTitle("Empty fields!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
    
    # def load_xml(self):
    #     path = QFileDialog.getOpenFileName(self, 'Open compressor coefficiencts file',filter="Coefficients file (*.coeffs);;All files (*.*)")[0]
    #     if path != "":
    #         result = read_comp_AHRI_xml(path)
    #         if result[0]:
    #             try:
    #                 comp = result[1]
    #                 self.Comp_AHRI_unitsys.setCurrentIndex(comp.unit_system)
    #                 self.Comp_AHRI_num_speed.setValue(int(comp.num_speeds))
    #                 if comp.std_type == 0:
    #                     self.Comp_AHRI_std_sh_radio.setChecked(True)
    #                     self.Comp_AHRI_std_sh.setText(str(round(comp.std_sh,6)))
    #                 elif comp.std_type == 1:
    #                     self.Comp_AHRI_std_suction_radio.setChecked(True)
    #                     self.Comp_AHRI_std_suction.setText(str(round(comp.std_suction,6)))
    #                 self.AHRI_num_speed_change()
    #                 self.Comp_AHRI_F.setText(comp.Comp_AHRI_F_value)
    #                 for i in range(int(comp.num_speeds)):
    #                     getattr(self,'Comp_nominal_speed_'+str(i+1)).setText(str(comp.speeds[i].speed_value))
    #                     for col in range(10):
    #                         getattr(self,'Comp_coefficients_table_'+str(i+1)).setItem(0, col, QTableWidgetItem(str(comp.speeds[i].M[col])))
    #                     for col in range(10):
    #                         getattr(self,'Comp_coefficients_table_'+str(i+1)).setItem(1, col, QTableWidgetItem(str(comp.speeds[i].P[col])))
    #                 msg = QMessageBox()
    #                 msg.setIcon(QMessageBox.Information)
    #                 msg.setText("The file was loaded successfully")
    #                 msg.setWindowTitle("Success!")
    #                 msg.setStandardButtons(QMessageBox.Ok)
    #                 msg.exec_()
    #             except:
    #                 import traceback
    #                 print(traceback.format_exc())
    #                 msg = QMessageBox()
    #                 msg.setIcon(QMessageBox.Warning)
    #                 msg.setText("File could not be loaded")
    #                 msg.setWindowTitle("Sorry!")
    #                 msg.setStandardButtons(QMessageBox.Ok)
    #                 msg.exec_()
    #         else:
    #             msg = QMessageBox()
    #             msg.setIcon(QMessageBox.Warning)
    #             msg.setText("File could not be loaded")
    #             msg.setWindowTitle("Sorry!")
    #             msg.setStandardButtons(QMessageBox.Ok)
    #             msg.exec_()
    
    # def save_xml(self):
    #     if self.validate():
    #         path = QFileDialog.getSaveFileName(self, caption='Save compressor coefficiencts file',directory=load_last_location(),filter="Coefficients file (*.coeffs);;All files (*.*)")[0]
    #         if path != "":
    #             save_last_location(path)
    #             if path[-7:].lower() != ".coeffs":
    #                 path = path+".coeffs"
    #             class values():
    #                 pass
    #             comp = values
    #             comp.num_speeds = int(self.Comp_AHRI_num_speed.value())
    #             comp.unit_system = str(self.Comp_AHRI_unitsys.currentIndex())
    #             if self.Comp_AHRI_std_sh_radio.isChecked():
    #                 comp.std_type = 0
    #                 comp.std_sh = temperature_diff_unit_converter(self.Comp_AHRI_std_sh.text(),self.Comp_AHRI_std_sh_unit.currentIndex())
    #             elif self.Comp_AHRI_std_suction_radio.isChecked():
    #                 comp.std_type = 1
    #                 comp.std_suction = temperature_unit_converter(self.Comp_AHRI_std_suction.text(),self.Comp_AHRI_std_suction_unit.currentIndex())
    #             comp.Comp_AHRI_F_value = str(self.Comp_AHRI_F.text())
    #             comp.speeds = [values() for _ in range(comp.num_speeds)]
    #             for i in range(comp.num_speeds):
    #                 comp.speeds[i].speed_value = str(getattr(self,"Comp_nominal_speed_"+str(i+1)).text())
    #                 comp.speeds[i].M = []
    #                 comp.speeds[i].P = []
    #                 for col in range(10):
    #                     comp.speeds[i].M.append(getattr(self,"Comp_coefficients_table_"+str(i+1)).item(0,col).text())
    #                 for col in range(10):
    #                     comp.speeds[i].P.append(getattr(self,"Comp_coefficients_table_"+str(i+1)).item(1,col).text())
    #             result = write_comp_AHRI_xml(comp,path)
    #             if result:
    #                 msg = QMessageBox()
    #                 msg.setIcon(QMessageBox.Information)
    #                 msg.setText("The file was saved successfully")
    #                 msg.setWindowTitle("Success!")
    #                 msg.setStandardButtons(QMessageBox.Ok)
    #                 msg.exec_()
    #             else:
    #                 msg = QMessageBox()
    #                 msg.setIcon(QMessageBox.Warning)
    #                 msg.setText("File could not be saved")
    #                 msg.setWindowTitle("Sorry!")
    #                 msg.setStandardButtons(QMessageBox.Ok)
    #                 msg.exec_()
    #     else:
    #         msg = QMessageBox()
    #         msg.setIcon(QMessageBox.Warning)
    #         msg.setText("Please fill all empty fields")
    #         msg.setWindowTitle("Empty fields!")
    #         msg.setStandardButtons(QMessageBox.Ok)
    #         msg.exec_()
    
    def AHRI_num_speed_change(self):
        class MyDelegate(QItemDelegate):

            def createEditor(self, parent, option, index):
                return_object = QLineEdit(parent)
                only_number = QRegExpValidator(QRegExp("[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)"))
                return_object.setValidator(only_number)
                return return_object
        num_tabs = int(self.tabWidget.count())
        current_value = int(self.Comp_AHRI_num_speed.value())
        if current_value > num_tabs:
            while num_tabs != current_value:
                num_tabs += 1
                class TabPage(QWidget):
                    def __init__(self, parent=None):
                        only_number = QRegExpValidator(QRegExp("(([0-9]+\.[0-9]*[1-9][0-9]*)|([0-9]*[1-9][0-9]*\.[0-9]+)|([0-9]*[1-9][0-9]*))"))
                        super().__init__(parent)
                        exec("parent.verticalLayout_" + str(num_tabs+7) + "= QVBoxLayout(self)")
                        exec('parent.verticalLayout_'+str(num_tabs+7)+'.setObjectName("verticalLayout_'+str(num_tabs+7)+'")')
                        exec("parent.verticalLayout_" + str(num_tabs+8) + "= QVBoxLayout()")
                        exec('parent.verticalLayout_'+str(num_tabs+8)+'.setObjectName("verticalLayout_'+str(num_tabs+8)+'")')
                        exec("parent.horizontalLayout_" + str(num_tabs+4) + "= QHBoxLayout()")
                        exec('parent.horizontalLayout_'+str(num_tabs+4)+'.setObjectName("horizontalLayout_'+str(num_tabs+4)+'")')
                        exec('parent.spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)')
                        exec('parent.horizontalLayout_'+str(num_tabs+4)+'.addItem(parent.spacerItem)')
                        exec('parent.Comp_nominal_speed_'+str(num_tabs)+'_label = QLabel(self)')
                        exec('parent.Comp_nominal_speed_'+str(num_tabs)+'_label.setObjectName("Comp_nominal_speed_'+str(num_tabs)+'_label")')
                        exec("parent.horizontalLayout_" + str(num_tabs+4) + ".addWidget(parent.Comp_nominal_speed_"+str(num_tabs)+"_label)")
                        exec("parent.Comp_nominal_speed_"+str(num_tabs)+" = QLineEdit(self)")
                        exec("parent.Comp_nominal_speed_"+str(num_tabs)+'.setObjectName("Comp_nominal_speed_'+str(num_tabs)+'")')
                        exec('parent.Comp_nominal_speed_'+str(num_tabs)+'.setValidator(only_number)')
                        exec("parent.horizontalLayout_" + str(num_tabs+4) + ".addWidget(parent.Comp_nominal_speed_"+str(num_tabs)+")")
                        exec('parent.Comp_nominal_speed_'+str(num_tabs)+'_unit = QComboBox(self)')
                        exec('parent.Comp_nominal_speed_'+str(num_tabs)+'_unit.setEnabled(False)')
                        exec('parent.Comp_nominal_speed_'+str(num_tabs)+'_unit.setObjectName("Comp_nominal_speed_'+str(num_tabs)+'_unit")')
                        exec('parent.Comp_nominal_speed_'+str(num_tabs)+'_unit.setObjectName("Comp_nominal_speed_'+str(num_tabs)+'_unit")')
                        exec('parent.Comp_nominal_speed_'+str(num_tabs)+'_unit.addItem("")')
                        exec('parent.horizontalLayout_'+str(num_tabs+4)+'.addWidget(parent.Comp_nominal_speed_'+str(num_tabs)+'_unit)')
                        exec('parent.spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)')
                        exec('parent.horizontalLayout_'+str(num_tabs+4)+'.addItem(parent.spacerItem1)')
                        exec('parent.verticalLayout_'+str(num_tabs+8)+'.addLayout(parent.horizontalLayout_'+str(num_tabs+4)+')')
                        exec('parent.Comp_coefficients_table_'+str(num_tabs)+' = QTableWidget(self)')
                        delegate = MyDelegate()
                        exec('parent.Comp_coefficients_table_'+str(num_tabs)+'.setItemDelegate(delegate)')
                        exec('parent.Comp_coefficients_table_'+str(num_tabs)+'.installEventFilter(parent)')
                        exec('sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)')
                        exec('sizePolicy.setHorizontalStretch(0)')
                        exec('sizePolicy.setVerticalStretch(0)')
                        exec('sizePolicy.setHeightForWidth(parent.Comp_coefficients_table_'+str(num_tabs)+'.sizePolicy().hasHeightForWidth())')
                        exec('parent.Comp_coefficients_table_'+str(num_tabs)+'.setSizePolicy(sizePolicy)')
                        exec('parent.Comp_coefficients_table_'+str(num_tabs)+'.setMinimumSize(QSize(600, 0))')
                        exec('parent.Comp_coefficients_table_'+str(num_tabs)+'.setRowCount(2)')
                        exec('parent.Comp_coefficients_table_'+str(num_tabs)+'.setColumnCount(10)')
                        exec('parent.Comp_coefficients_table_'+str(num_tabs)+'.setObjectName("Comp_coefficients_table_'+str(num_tabs)+'")')
                        exec('item = QTableWidgetItem()')
                        exec('parent.Comp_coefficients_table_'+str(num_tabs)+'.setVerticalHeaderItem(0, item)')
                        exec('item = QTableWidgetItem()')
                        exec('parent.Comp_coefficients_table_'+str(num_tabs)+'.setVerticalHeaderItem(1, item)')
                        exec('item = QTableWidgetItem()')
                        exec('parent.Comp_coefficients_table_'+str(num_tabs)+'.setHorizontalHeaderItem(0, item)')
                        exec('item = QTableWidgetItem()')
                        exec('parent.Comp_coefficients_table_'+str(num_tabs)+'.setItem(0, 0, item)')
                        exec('parent.Comp_coefficients_table_'+str(num_tabs)+'.horizontalHeader().setCascadingSectionResizes(False)')
                        exec('parent.Comp_coefficients_table_'+str(num_tabs)+'.horizontalHeader().setDefaultSectionSize(50)')
                        exec('parent.Comp_coefficients_table_'+str(num_tabs)+'.horizontalHeader().setMinimumSectionSize(15)')
                        for row in range(2):
                            for col in range(10):
                                exec('parent.Comp_coefficients_table_'+str(num_tabs)+'.setItem(row, col, QTableWidgetItem("0"))')
                        exec('parent.verticalLayout_'+str(num_tabs+8)+'.addWidget(parent.Comp_coefficients_table_'+str(num_tabs)+')')
                        exec('parent.verticalLayout_'+str(num_tabs+7)+'.addLayout(parent.verticalLayout_'+str(num_tabs+8)+')')
                        exec('_translate = QCoreApplication.translate')
                        exec('parent.Comp_nominal_speed_'+str(num_tabs)+'_label.setToolTip(_translate("Form", "<html><head/><body><p>Speed on which the coefficients are defined.</p><p>If constant speed compressor, use the same as operating speed chosen before.</p></body></html>"))')
                        exec('parent.Comp_nominal_speed_'+str(num_tabs)+'_label.setText(_translate("Form", "Nominal Speed"))')
                        exec('parent.Comp_nominal_speed_'+str(num_tabs)+'_unit.setItemText(0, _translate("Form", "rpm"))')
                        exec('parent.Comp_coefficients_table_'+str(num_tabs)+'.setSortingEnabled(False)')
                        exec('item = parent.Comp_coefficients_table_'+str(num_tabs)+'.verticalHeaderItem(0)')
                        exec('item.setText(_translate("Form", "Mass Flow Rate"))')
                        exec('item = parent.Comp_coefficients_table_'+str(num_tabs)+'.verticalHeaderItem(1)')
                        exec('item.setText(_translate("Form", "Power"))')
                        exec('item = parent.Comp_coefficients_table_'+str(num_tabs)+'.horizontalHeaderItem(0)')
                        exec('item.setText(_translate("Form", "1"))')
                        exec('__sortingEnabled = parent.Comp_coefficients_table_'+str(num_tabs)+'.isSortingEnabled()')
                        exec('parent.Comp_coefficients_table_'+str(num_tabs)+'.setSortingEnabled(False)')
                        exec('parent.Comp_coefficients_table_'+str(num_tabs)+'.setSortingEnabled(__sortingEnabled)')
                self.tabWidget.addTab(TabPage(self),"Speed "+str(num_tabs))
                        
        if current_value < num_tabs:
            while num_tabs != current_value:
                num_tabs -= 1
                self.tabWidget.removeTab(num_tabs)            
