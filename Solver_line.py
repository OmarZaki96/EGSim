from PyQt5.QtCore import QObject, pyqtSignal
import time
import CoolProp as CP
from GUI_functions import load_refrigerant_list
from backend.Line import LineClass
from backend.Functions import get_AS

class solver(QObject):
    finished = pyqtSignal(tuple)
    terminal_message = pyqtSignal(str)
    
    def __init__(self,line,options,parent=None):
        super(solver, self).__init__(parent)
        
        ref_list = load_refrigerant_list()
        if not ref_list[0]:
            raise
        ref_list = ref_list[1]
        
        ref = options['Ref']
        
        AS = get_AS(options['Backend'],ref,None)
        if AS[0]:
            self.AS = AS[1]
        else:
            pass
        
        if options['inlet_cond'] == 0:
            self.cond = 0
            self.P_in = options['inlet_pressure']
            self.T_in = options['inlet_temperature']
        elif options['inlet_cond'] == 1:
            self.cond = 1
            self.P_in = options['inlet_pressure']
            self.Q_in = options['inlet_quality']
        elif options['inlet_cond'] == 2:
            self.cond = 2
            self.Q_in = options['inlet_quality']
            self.T_in = options['inlet_temperature']
        elif options['inlet_cond'] == 3:
            self.cond = 3
            self.P_in = options['inlet_pressure']
            self.T_diff_in = options['inlet_temp_diff']
        elif options['inlet_cond'] == 4:
            self.cond = 4
            self.T_in = options['inlet_temperature']
            self.T_diff_in = options['inlet_temp_diff']
        
        self.mdot = options['mdot_r']
        
        self.Line = LineClass()
        
        self.Line.name = line.Line_name
        self.Line.L = line.Line_length
        self.Line.ID = line.Line_ID
        self.Line.OD = line.Line_OD
        self.Line.k_line = line.Line_tube_k
        self.Line.k_ins = line.Line_insulation_k
        self.Line.t_ins = line.Line_insulation_t
        self.Line.T_sur = line.Line_surrounding_T
        self.Line.h_sur = line.Line_surrounding_HTC
        self.Line.e_D = line.Line_e_D
        self.Line.Nsegments = line.Line_N_segments
        self.Line.Q_error_tol = line.Line_q_tolerance
        self.Line.DP_tuning = line.Line_DP_correction
        self.Line.HT_tuning = line.Line_HT_correction

    def run(self):
        self.terminal_message.emit("Checked inputs")
        time.sleep(0.1)
        self.terminal_message.emit("Trying to solve Line")
        time.sleep(0.1)
        result = self.solve()
        if result[0]:
            self.finished.emit((1,"Simulation finished",result[1]))
        else:
            self.finished.emit((0,result[1]))

    def solve(self):
        try:
            if self.cond == 0:
                self.AS.update(CP.PT_INPUTS,self.P_in,self.T_in)
                self.h_in = self.AS.hmass()
            elif self.cond == 1:
                self.AS.update(CP.PQ_INPUTS,self.P_in,self.Q_in)
                self.h_in = self.AS.hmass()
            elif self.cond == 2:
                self.AS.update(CP.QT_INPUTS,self.Q_in,self.T_in)
                self.P_in = self.AS.p()
                self.h_in = self.AS.hmass()
            elif self.cond == 3:
                if self.T_diff_in >= 0:
                    self.AS.update(CP.PQ_INPUTS,self.P_in,1.0)
                    T_in = self.AS.T()
                    self.AS.update(CP.PT_INPUTS,self.P_in,T_in+self.T_diff_in)
                    self.h_in = self.AS.hmass()
                elif self.T_diff_in < 0:
                    self.AS.update(CP.PQ_INPUTS,self.P_in,0.0)
                    T_in = self.AS.T()
                    self.AS.update(CP.PT_INPUTS,self.P_in,T_in+self.T_diff_in)
                    self.h_in = self.AS.hmass()
            elif self.cond == 4:
                if self.T_diff_in >= 0:
                    self.AS.update(CP.QT_INPUTS,1.0, self.T_in)
                    self.P_in = self.AS.p()
                    self.AS.update(CP.PT_INPUTS,self.P_in,self.T_in+self.T_diff_in)
                    self.h_in = self.AS.hmass()
                elif self.T_diff_in < 0:
                    self.AS.update(CP.QT_INPUTS,0.0, self.T_in)
                    self.P_in = self.AS.p()
                    self.AS.update(CP.PT_INPUTS,self.P_in,self.T_in+self.T_diff_in)
                    self.h_in = self.AS.hmass()
            params={
                    'Pin_r': self.P_in,
                    'hin_r': self.h_in,
                    'mdot_r': self.mdot,
                    'AS':self.AS,
                }
            self.Line.Update(**params)
            self.Line.Calculate()
            return (1,self.Line)
        except:
            import traceback
            print(traceback.format_exc())
            if self.Line.terminate:
                return (0,"user terminated simulation")
            else:
                return (0,"Failed to solve Line")
    