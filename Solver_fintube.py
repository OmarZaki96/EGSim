from PyQt5.QtCore import QObject, pyqtSignal
import time
import CoolProp as CP
from GUI_functions import load_refrigerant_list
from backend.FinTubeHEX import FinTubeHEXClass
from CoolProp.CoolProp import HAPropsSI
from backend.Functions import get_AS

class solver(QObject):
    finished = pyqtSignal(tuple)
    terminal_message = pyqtSignal(str)
    
    def __init__(self,HX,options,parent=None):
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
        
        self.HX = FinTubeHEXClass()
        self.HX.name = HX.name

        if HX.Air_flow_direction in ["Sub Heat Exchanger First","Sub Heat Exchanger Last"]:
            number_of_circuits = HX.N_series_Circuits + 1
        elif HX.Air_flow_direction in ["Parallel","Series-Parallel","Series-Counter"]:
            number_of_circuits = HX.N_series_Circuits

        if HX.Accurate == "CoolProp":
            self.HX.Accurate = True
        elif HX.Accurate == "Psychrolib":
            self.HX.Accurate = False
        self.HX.create_circuits(number_of_circuits)
        for i in range(number_of_circuits):
            N = HX.circuits[i].N_Circuits
            connection = [i,i+1,i,1.0,N]
            self.HX.connect(*tuple(connection))
        self.HX.Tin_a = HX.Air_T
        self.HX.Pin_a = HX.Air_P
        Win_a = HAPropsSI("W","T",HX.Air_T,"P",HX.Air_P,"R",HX.Air_RH)
        self.HX.Win_a = Win_a
        if HX.Air_flow_direction == "Parallel":
            self.HX.Air_sequence = 'parallel'
            self.HX.Air_distribution = HX.Air_Distribution
        elif HX.Air_flow_direction == "Series-Parallel":
            self.HX.Air_sequence = 'series_parallel'
        elif HX.Air_flow_direction == "Series-Counter":
            self.HX.Air_sequence = 'series_counter'
        elif HX.Air_flow_direction == "Sub Heat Exchanger First":
            self.HX.Air_sequence = 'sub_HX_first'
            self.HX.Air_distribution = HX.Air_Distribution
        elif HX.Air_flow_direction == "Sub Heat Exchanger Last":
            self.HX.Air_sequence = 'sub_HX_last'
            self.HX.Air_distribution = HX.Air_Distribution
        if HX.model == "Segment by Segment":
            self.HX.model = 'segment'
            N_segments = HX.N_segments
        elif HX.model == "Phase by Phase":
            self.HX.model = 'phase'
            N_segments = 1.0
        self.HX.Q_error_tol = HX.HX_Q_tol
        self.HX.max_iter_per_circuit = HX.N_iterations
        if HX.Fan_model == "Fan Efficiency Model":
            self.HX.Fan.model = 'efficiency'
            self.HX.Fan.efficiency = HX.Fan_model_efficiency_exp
        elif HX.Fan_model == "Fan Curve Model":
            self.HX.Fan.model = 'curve'
            self.HX.Fan.power_curve = HX.Fan_model_P_exp
            self.HX.Fan.DP_curve = HX.Fan_model_DP_exp
        elif HX.Fan_model == "Fan Power Model":
            self.HX.Fan.model = 'power'
            self.HX.Fan.power_exp = HX.Fan_model_power_exp
            
        self.HX.Fan.Fan_position = 'after'
        if hasattr(HX,"Vdot_ha"):
            self.HX.Vdot_ha = HX.Vdot_ha
        else:
            v_spec = HAPropsSI("V","T",self.HX.Tin_a,"W",self.HX.Win_a,"P",self.HX.Pin_a)
            self.HX.Vdot_ha = HX.mdot_da * v_spec
        
        if HX.solver == "Mass flow rate solver":
            self.HX.Solver = 'mdot'
        elif HX.solver == "Pressure drop solver":
            self.HX.Solver = 'dp'            
        
        for i in range(number_of_circuits):
            self.HX.Circuits[i].Geometry.Ntubes_per_bank_per_subcircuit = HX.circuits[i].N_tube_per_bank
            self.HX.Circuits[i].Geometry.Nbank = HX.circuits[i].N_bank
            self.HX.Circuits[i].Geometry.OD = HX.circuits[i].OD
            self.HX.Circuits[i].Geometry.Ltube = HX.circuits[i].Ltube
            if HX.circuits[i].Tube_type == "Smooth":
                self.HX.Circuits[i].Geometry.Tubes_type = "Smooth"
                self.HX.Circuits[i].Geometry.ID = HX.circuits[i].ID
                self.HX.Circuits[i].Geometry.e_D = HX.circuits[i].e_D
            elif HX.circuits[i].Tube_type == "Microfin":
                self.HX.Circuits[i].Geometry.Tubes_type = "Microfin"
                self.HX.Circuits[i].Geometry.t = HX.circuits[i].Tube_t
                self.HX.Circuits[i].Geometry.beta = HX.circuits[i].Tube_beta
                self.HX.Circuits[i].Geometry.e = HX.circuits[i].Tube_e
                self.HX.Circuits[i].Geometry.d = HX.circuits[i].Tube_d
                self.HX.Circuits[i].Geometry.gama = HX.circuits[i].Tube_gamma
                self.HX.Circuits[i].Geometry.n = HX.circuits[i].Tube_n
            self.HX.Circuits[i].Geometry.Staggering = HX.circuits[i].Staggering
            self.HX.Circuits[i].Geometry.Pl = HX.circuits[i].Pl
            self.HX.Circuits[i].Geometry.Pt = HX.circuits[i].Pt
            self.HX.Circuits[i].Geometry.Connections = HX.circuits[i].Connections
            self.HX.Circuits[i].Geometry.FarBendRadius = 0.01
            self.HX.Circuits[i].Geometry.FPI = HX.circuits[i].Fin_FPI
            self.HX.Circuits[i].Geometry.Fin_t = HX.circuits[i].Fin_t
            self.HX.Circuits[i].Geometry.FinType = HX.circuits[i].Fin_type
            if HX.circuits[i].Fin_type == "Wavy":
                self.HX.Circuits[i].Geometry.Fin_Pd = HX.circuits[i].Fin_pd
                self.HX.Circuits[i].Geometry.Fin_xf = HX.circuits[i].Fin_xf
            elif HX.circuits[i].Fin_type == "WavyLouvered":
                self.HX.Circuits[i].Geometry.Fin_Pd = HX.circuits[i].Fin_pd
                self.HX.Circuits[i].Geometry.Fin_xf = HX.circuits[i].Fin_xf
            elif HX.circuits[i].Fin_type == "Louvered":
                self.HX.Circuits[i].Geometry.Fin_Lp = HX.circuits[i].Fin_Lp
                self.HX.Circuits[i].Geometry.Fin_Lh = HX.circuits[i].Fin_Lh
            elif HX.circuits[i].Fin_type == "Slit":
                self.HX.Circuits[i].Geometry.Fin_Sh = HX.circuits[i].Fin_Sh
                self.HX.Circuits[i].Geometry.Fin_Ss = HX.circuits[i].Fin_Ss
                self.HX.Circuits[i].Geometry.Fin_Sn = HX.circuits[i].Fin_Sn
                
            self.HX.Circuits[i].Thermal.Nsegments = N_segments
            self.HX.Circuits[i].Thermal.kw = HX.circuits[i].Tube_k
            self.HX.Circuits[i].Thermal.k_fin = HX.circuits[i].Fin_k
            self.HX.Circuits[i].Thermal.FinsOnce = True
            self.HX.Circuits[i].Thermal.HTC_superheat_Corr = HX.circuits[i].superheat_HTC_corr
            self.HX.Circuits[i].Thermal.HTC_subcool_Corr = HX.circuits[i].subcool_HTC_corr
            self.HX.Circuits[i].Thermal.DP_superheat_Corr = HX.circuits[i].superheat_DP_corr
            self.HX.Circuits[i].Thermal.DP_subcool_Corr = HX.circuits[i].subcool_DP_corr
            self.HX.Circuits[i].Thermal.HTC_2phase_Corr = HX.circuits[i]._2phase_HTC_corr
            self.HX.Circuits[i].Thermal.DP_2phase_Corr = HX.circuits[i]._2phase_DP_corr
            self.HX.Circuits[i].Thermal.DP_Accel_Corr = HX.circuits[i]._2phase_charge_corr
            self.HX.Circuits[i].Thermal.rho_2phase_Corr = HX.circuits[i]._2phase_charge_corr
            self.HX.Circuits[i].Thermal.Air_dry_Corr = HX.circuits[i].air_dry_HTC_corr
            self.HX.Circuits[i].Thermal.Air_wet_Corr = HX.circuits[i].air_wet_HTC_corr
            self.HX.Circuits[i].Thermal.h_r_superheat_tuning = HX.circuits[i].superheat_HTC_correction
            self.HX.Circuits[i].Thermal.h_r_subcooling_tuning = HX.circuits[i].subcool_HTC_correction
            self.HX.Circuits[i].Thermal.h_r_2phase_tuning = HX.circuits[i]._2phase_HTC_correction
            self.HX.Circuits[i].Thermal.h_a_dry_tuning = HX.circuits[i].air_dry_HTC_correction
            self.HX.Circuits[i].Thermal.h_a_wet_tuning = HX.circuits[i].air_wet_HTC_correction
            self.HX.Circuits[i].Thermal.DP_a_dry_tuning = HX.circuits[i].air_dry_DP_correction
            self.HX.Circuits[i].Thermal.DP_a_wet_tuning = HX.circuits[i].air_wet_DP_correction
            self.HX.Circuits[i].Thermal.DP_r_superheat_tuning = HX.circuits[i].superheat_DP_correction
            self.HX.Circuits[i].Thermal.DP_r_subcooling_tuning = HX.circuits[i].subcool_DP_correction
            self.HX.Circuits[i].Thermal.DP_r_2phase_tuning = HX.circuits[i]._2phase_DP_correction
            if hasattr(HX.circuits[i],'h_a_wet_on'):
                self.HX.Circuits[i].Thermal.h_a_wet_on = HX.circuits[i].h_a_wet_on
            else:
                self.HX.Circuits[i].Thermal.h_a_wet_on = False
            if hasattr(HX.circuits[i],'DP_a_wet_on'):
                self.HX.Circuits[i].Thermal.DP_a_wet_on = HX.circuits[i].DP_a_wet_on
            else:
                self.HX.Circuits[i].Thermal.DP_a_wet_on = False

            if hasattr(HX.circuits[i],'sub_HX_values'):
                self.HX.Circuits[i].Geometry.Sub_HX_matrix = HX.circuits[i].sub_HX_values

    def run(self):
        self.terminal_message.emit("Checked inputs")
        time.sleep(0.1)
        self.terminal_message.emit("Trying to solve Fin-tube")
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
            self.HX.Update(**params)
            self.HX.solve()
            return (1,self.HX)
        except:
            import traceback
            print(traceback.format_exc())
            if self.HX.terminate:
                return (0,"user terminated simulation")
            else:
                return (0,"Failed to solve Fin-tube")
    