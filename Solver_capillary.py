from PyQt5.QtCore import QObject, pyqtSignal
import time
import CoolProp as CP
from GUI_functions import load_refrigerant_list
from backend.Capillary import CapillaryClass
from backend.Functions import get_AS

class solver(QObject):
    finished = pyqtSignal(tuple)
    terminal_message = pyqtSignal(str)
    
    def __init__(self,capillary,options,parent=None):
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
            self.cond_in = 0
            self.P_in = options['inlet_pressure']
            self.T_in = options['inlet_temperature']
        elif options['inlet_cond'] == 1:
            self.cond_in = 1
            self.P_in = options['inlet_pressure']
            self.Q_in = options['inlet_quality']
        elif options['inlet_cond'] == 2:
            self.cond_in = 2
            self.Q_in = options['inlet_quality']
            self.T_in = options['inlet_temperature']
        elif options['inlet_cond'] == 3:
            self.cond_in = 3
            self.P_in = options['inlet_pressure']
            self.T_diff_in = options['inlet_temp_diff']
        elif options['inlet_cond'] == 4:
            self.cond_in = 4
            self.T_in = options['inlet_temperature']
            self.T_diff_in = options['inlet_temp_diff']
        if options['outlet_cond'] == 0:
            self.cond_out = 0
            self.P_out = options['outlet_pressure']
        elif options['outlet_cond'] == 1:
            self.cond_out = 1
            self.T_out = options['outlet_temperature']
                
        self.Capillary = CapillaryClass()
        self.Capillary.name = capillary.Capillary_name
        self.Capillary.L = capillary.Capillary_length
        self.Capillary.D = capillary.Capillary_D
        self.Capillary.D_liquid = capillary.Capillary_entrance_D
        self.Capillary.DP_converged = capillary.Capillary_DP_tolerance
        self.Capillary.DT_2phase = capillary.Capillary_DT
        self.Capillary.Ntubes = capillary.Capillary_N_tubes
        if capillary.Capillary_correlation == 0:    
            self.Capillary.method = "choi"
        elif capillary.Capillary_correlation == 1:    
            self.Capillary.method = "wolf"
        elif capillary.Capillary_correlation == 2:    
            self.Capillary.method = "wolf_physics"
        elif capillary.Capillary_correlation == 3:
            self.Capillary.method = "wolf_pate"            
        elif capillary.Capillary_correlation == 4:
            self.Capillary.method = "rasti"            
        
    def run(self):
        self.terminal_message.emit("Checked inputs")
        time.sleep(0.1)
        self.terminal_message.emit("Trying to solve Capillary")
        time.sleep(0.1)
        result = self.solve()
        if result[0]:
            self.finished.emit((1,"Simulation finished",result[1]))
        else:
            self.finished.emit((0,result[1]))

    def solve(self):
        try:
            if self.cond_in == 0:
                self.AS.update(CP.PT_INPUTS,self.P_in,self.T_in)
                self.h_in = self.AS.hmass()
            elif self.cond_in == 1:
                self.AS.update(CP.PQ_INPUTS,self.P_in,self.Q_in)
                self.h_in = self.AS.hmass()
            elif self.cond_in == 2:
                self.AS.update(CP.QT_INPUTS,self.Q_in,self.T_in)
                self.P_in = self.AS.p()
                self.h_in = self.AS.hmass()
            elif self.cond_in == 3:
                self.AS.update(CP.PQ_INPUTS,self.P_in,0.0)
                T_in = self.AS.T()
                self.AS.update(CP.PT_INPUTS,self.P_in,T_in-self.T_diff_in)
                self.h_in = self.AS.hmass()
            elif self.cond_in == 4:
                self.AS.update(CP.QT_INPUTS,0.0, self.T_in)
                self.P_in = self.AS.p()
                self.AS.update(CP.PT_INPUTS,self.P_in,self.T_in-self.T_diff_in)
                self.h_in = self.AS.hmass()
            if self.cond_out == 1:
                self.AS.update(CP.QT_INPUTS,0.0,self.T_out)
                self.P_out = self.AS.p()
            
            if self.P_out >= self.P_in:
                return (0, "Target outlet refrigerant pressure should be less than inlet refrigerant pressure")
            params={
                    'Pin_r': self.P_in,
                    'Pout_r_target': self.P_out,
                    'hin_r': self.h_in,
                    'AS':self.AS,
                }
            self.Capillary.Update(**params)
            self.Capillary.Calculate()
            return (1,self.Capillary)
        except:
            import traceback
            print(traceback.format_exc())
            if self.Capillary.terminate:
                return (0,"user terminated simulation")
            else:
                return (0,"Failed to solve Capillary")
    