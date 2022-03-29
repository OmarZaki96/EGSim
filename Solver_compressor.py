from PyQt5.QtCore import QObject, pyqtSignal
import time
import CoolProp as CP
from GUI_functions import load_refrigerant_list
from backend.CompressorPHY import CompressorPHYClass
from backend.CompressorAHRI import CompressorAHRIClass
from backend.Functions import get_AS

class solver(QObject):
    finished = pyqtSignal(tuple)
    terminal_message = pyqtSignal(str)
    
    def __init__(self,compressor,options,parent=None):
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
        
        if compressor.Comp_model == "physics":
            self.Compressor = CompressorPHYClass()
            self.Compressor.name = compressor.Comp_name
            self.Compressor.fp = compressor.Comp_fp
            self.Compressor.Vdot_ratio_P = compressor.Comp_ratio_P
            self.Compressor.Vdot_ratio_M = compressor.Comp_ratio_M
            self.Compressor.Displacement = compressor.Comp_vol
            self.Compressor.act_speed = compressor.Comp_speed
            self.Compressor.Elec_eff = compressor.Comp_elec_eff
            self.Compressor.isen_eff = compressor.isentropic_exp
            self.Compressor.vol_eff = compressor.vol_exp
            self.Compressor.F_factor = compressor.F_factor
            self.Compressor.SH_type = compressor.SH_type
            if compressor.SH_type == 0:
                self.Compressor.SH_Ref = compressor.SH_Ref
            elif compressor.SH_type == 1:
                self.Compressor.Suction_Ref = compressor.Suction_Ref
                        
        elif compressor.Comp_model == "map":
            self.Compressor = CompressorAHRIClass()
            self.Compressor.name = compressor.Comp_name
            self.Compressor.M = compressor.map_data.M_coeffs
            self.Compressor.P = compressor.map_data.P_coeffs
            self.Compressor.Speeds = compressor.map_data.Speeds
            self.Compressor.fp = compressor.Comp_fp
            self.Compressor.Vdot_ratio_P = compressor.Comp_ratio_P
            self.Compressor.Vdot_ratio_M = compressor.Comp_ratio_M
            self.Compressor.Displacement = compressor.Comp_vol
            if compressor.map_data.std_type == 0:
                self.Compressor.SH_Ref = compressor.map_data.std_sh
            elif compressor.map_data.std_type == 1:
                self.Compressor.Suction_Ref = compressor.map_data.std_suction
                
            self.Compressor.act_speed = compressor.Comp_speed
            self.Compressor.Unit_system = compressor.unit_system
            self.Compressor.Elec_eff = compressor.Comp_elec_eff
            self.Compressor.F_factor = compressor.map_data.F_value

        elif compressor.Comp_model == "10coefficients":
            self.Compressor = CompressorAHRIClass()
            self.Compressor.name = compressor.Comp_name
            self.Compressor.M = compressor.M
            self.Compressor.P = compressor.P
            self.Compressor.Speeds = compressor.speeds
            self.Compressor.fp = compressor.Comp_fp
            self.Compressor.Vdot_ratio_P = compressor.Comp_ratio_P
            self.Compressor.Vdot_ratio_M = compressor.Comp_ratio_M
            self.Compressor.Displacement = compressor.Comp_vol
            if compressor.std_type == 0:
                self.Compressor.SH_Ref = compressor.std_sh
            elif compressor.std_type == 1:
                self.Compressor.Suction_Ref = compressor.std_suction
            self.Compressor.act_speed = compressor.Comp_speed
            self.Compressor.Unit_system = compressor.unit_system
            self.Compressor.Elec_eff = compressor.Comp_elec_eff
            self.Compressor.F_factor = compressor.Comp_AHRI_F_value
        
    def run(self):
        self.terminal_message.emit("Checked inputs")
        time.sleep(0.1)
        self.terminal_message.emit("Trying to solve compressor")
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
                self.AS.update(CP.PQ_INPUTS,self.P_in,1.0)
                T_in = self.AS.T()
                self.AS.update(CP.PT_INPUTS,self.P_in,T_in+self.T_diff_in)
                self.h_in = self.AS.hmass()
            elif self.cond_in == 4:
                self.AS.update(CP.QT_INPUTS,1.0, self.T_in)
                self.P_in = self.AS.p()
                self.AS.update(CP.PT_INPUTS,self.P_in,self.T_in+self.T_diff_in)
                self.h_in = self.AS.hmass()
            if self.cond_out == 1:
                self.AS.update(CP.QT_INPUTS,0.0,self.T_out)
                self.P_out = self.AS.p()
            
            if self.P_out <= self.P_in:
                return (0, "Outlet refrigerant pressure should be higher than inlet refrigerant pressure")

            params={
                    'Pin_r': self.P_in,
                    'Pout_r': self.P_out,
                    'hin_r': self.h_in,
                    'AS':self.AS,
                }
            self.Compressor.Update(**params)
            self.Compressor.Calculate()
            return (1,self.Compressor)
        except:
            import traceback
            print(traceback.format_exc())
            if self.Compressor.terminate:
                return (0,"user terminated simulation")
            else:
                return (0,"Failed to solve Compressor")
    