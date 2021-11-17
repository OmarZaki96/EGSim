from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
import os, sys, csv, io
from sympy.parsing.sympy_parser import parse_expr
from sympy import S, Symbol

FROM_Compressor_Physics,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/Compressor_define_physics.ui"))

class Compressor_Physics(QDialog, FROM_Compressor_Physics):
    def __init__(self, parent=None):
        super(Compressor_Physics, self).__init__(parent)
        self.setupUi(self)
        self.Comp_physics_cancel_button.clicked.connect(self.cancel_button)
        self.Comp_physics_ok_button.clicked.connect(self.ok_button)
        
    def cancel_button(self):
        self.close()
    
    def ok_button(self):
        isentropic_exp = str(self.Comp_physics_isentropic_eff.text()).replace(" ","")
        isentropic_exp = isentropic_exp.replace("^","**")
        Error_1 = False
        if isentropic_exp in ["","-","."]:
            Error_1 = True
            Text = "Isentropic efficiency expression is empty"
            
        try:
            isen_eff=parse_expr(isentropic_exp)
        except:
            Error_1 = True
            Text = "Isentropic efficiency expression is wrong"
        
        if not Error_1:
            # getting expression variables
            all_symbols_isen = [str(x) for x in isen_eff.atoms(Symbol)]
            
            # making sure 1 variable (pressure ratio) is present
            if len(all_symbols_isen) != 1:
                if len(all_symbols_isen) == 0: # if no variable is given, then a number is given
                    isen_eff_value = isen_eff.evalf()
                    if not (0.0 <= isen_eff_value <= 1.0):
                        Error_1 = True
                        Text = "Isentropic efficiency must be between 0 and 1.0"
                else:
                    Error_1 = True
                    Text = "Isentropic efficiency expression is wrong"        
        if Error_1:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText(Text)
            msg.setWindowTitle("Error!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        else:
            Error_2 = False
            vol_exp = str(self.Comp_physics_vol_eff.text()).replace(" ","")
            vol_exp = vol_exp.replace("^","**")
            if vol_exp in ["","-","."]:
                Error_1 = True
                Text = "Volumetric efficiency expression is empty"
            try:
                vol_eff=parse_expr(vol_exp)
            except:
                Error_2 = True
                Text = "Volumetric efficiency expression is wrong"
            
            if not Error_2:
                # getting expression variables
                all_symbols_vol = [str(x) for x in vol_eff.atoms(Symbol)]
                
                # making sure 1 variable (pressure ratio) is present
                if len(all_symbols_vol) != 1:
                    if len(all_symbols_vol) == 0: # if no variable is given, then a number is given
                        vol_eff_value = vol_eff.evalf()
                        if not (0.0 < vol_eff_value < 1.0):
                            Error_2 = True
                            Text = "Volumetric efficiency must be between 0 and 1.0"
                    else:
                        Error_2 = True
                        Text = "Volumetric efficiency expression is wrong"        
            if Error_2:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText(Text)
                msg.setWindowTitle("Error!")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
            else:
                self.isentropic_exp = isentropic_exp
                self.vol_exp = vol_exp
                self.close()
