from PyQt5.QtCore import QObject, pyqtSignal
import time
import CoolProp as CP
from GUI_functions import load_refrigerant_list
from backend.MicroChannelHEX import MicroChannelHEXClass
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
        
        self.HX = MicroChannelHEXClass()
        self.HX.name = HX.name
        
        if HX.Accurate == "CoolProp":
            self.HX.Accurate = True
        elif HX.Accurate == "Psychrolib":
            self.HX.Accurate = False
        self.HX.Tin_a = HX.Air_T
        self.HX.Pin_a = HX.Air_P
        Win_a = HAPropsSI("W","T",HX.Air_T,"P",HX.Air_P,"R",HX.Air_RH)
        self.HX.Win_a = Win_a
        self.HX.Fan_add_DP = 0
        if HX.model == "Segment by Segment":
            self.HX.model = 'segment'
            self.HX.Thermal.Nsegments = HX.N_segments
        elif HX.model == "Phase by Phase":
            self.HX.model = 'phase'
            self.HX.Thermal.Nsegments = 1
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

        self.HX.Geometry.N_tube_per_bank_per_pass = HX.Circuiting.bank_passes
        if HX.Geometry.Fin_on_side_index:
            self.HX.Geometry.Fin_rows = HX.N_tube_per_bank + 1
        else:
            self.HX.Geometry.Fin_rows = HX.N_tube_per_bank - 1

        self.HX.Geometry.T_L = HX.Geometry.T_l
        self.HX.Geometry.T_w = HX.Geometry.T_w
        self.HX.Geometry.T_h = HX.Geometry.T_h
        self.HX.Geometry.T_s = HX.Geometry.T_s
        self.HX.Geometry.P_shape = HX.Geometry.port_shape
        self.HX.Geometry.P_end = HX.Geometry.T_end
        self.HX.Geometry.P_a = HX.Geometry.port_a_dim
        if HX.Geometry.port_shape in ['Rectangle', 'Triangle']:
            self.HX.Geometry.P_b = HX.Geometry.port_b_dim
        self.HX.Geometry.N_port = HX.Geometry.N_ports
        self.HX.Geometry.Enhanced = False
        self.HX.Geometry.FinType = HX.Geometry.Fin_type
        if HX.Geometry.Fin_type == "Louvered":
            self.HX.Geometry.Fin_Llouv = HX.Geometry.Fin_llouv
            self.HX.Geometry.Fin_alpha = HX.Geometry.Fin_lalpha
            self.HX.Geometry.Fin_Lp = HX.Geometry.Fin_lp
            
        self.HX.Geometry.Fin_t = HX.Geometry.Fin_t
        self.HX.Geometry.Fin_L = HX.Geometry.Fin_l
        self.HX.Geometry.FPI = HX.Geometry.Fin_FPI
        self.HX.Geometry.e_D = HX.Geometry.e_D
        self.HX.Geometry.Header_CS_Type = HX.Geometry.header_shape
        self.HX.Geometry.Header_dim_a = HX.Geometry.header_a_dim
        if HX.Geometry.header_shape in ["Rectangle"]:
            self.HX.Geometry.Header_dim_b = HX.Geometry.header_b_dim
        self.HX.Geometry.Header_length = HX.Geometry.header_height

        if hasattr(HX,"Vdot_ha"):
            self.HX.Vdot_ha = HX.Vdot_ha
        else:
            v_spec = HAPropsSI("V","T",self.HX.Tin_a,"W",self.HX.Win_a,"P",self.HX.Pin_a)
            self.HX.Vdot_ha = HX.mdot_da * v_spec
        self.HX.Thermal.k_fin = HX.Geometry.Fin_k
        self.HX.Thermal.kw = HX.Geometry.Tube_k
        self.HX.Thermal.Headers_DP_r = HX.Geometry.Header_DP
        self.HX.Thermal.FinsOnce = True
        self.HX.Thermal.HTC_superheat_Corr = HX.superheat_HTC_corr
        self.HX.Thermal.HTC_subcool_Corr = HX.subcool_HTC_corr
        self.HX.Thermal.DP_superheat_Corr = HX.superheat_DP_corr
        self.HX.Thermal.DP_subcool_Corr = HX.subcool_DP_corr
        self.HX.Thermal.HTC_2phase_Corr = HX._2phase_HTC_corr
        self.HX.Thermal.DP_2phase_Corr = HX._2phase_DP_corr
        self.HX.Thermal.DP_Accel_Corr = HX._2phase_charge_corr
        self.HX.Thermal.rho_2phase_Corr = HX._2phase_charge_corr
        self.HX.Thermal.Air_dry_Corr = HX.air_dry_HTC_corr
        self.HX.Thermal.Air_wet_Corr = HX.air_wet_HTC_corr
        self.HX.Thermal.h_r_superheat_tuning = HX.superheat_HTC_correction
        self.HX.Thermal.h_r_subcooling_tuning = HX.subcool_HTC_correction
        self.HX.Thermal.h_r_2phase_tuning = HX._2phase_HTC_correction
        self.HX.Thermal.h_a_dry_tuning = HX.air_dry_HTC_correction
        self.HX.Thermal.h_a_wet_tuning = HX.air_wet_HTC_correction
        self.HX.Thermal.DP_a_dry_tuning = HX.air_dry_DP_correction
        self.HX.Thermal.DP_a_wet_tuning = HX.air_wet_DP_correction
        self.HX.Thermal.DP_r_superheat_tuning = HX.superheat_DP_correction
        self.HX.Thermal.DP_r_subcooling_tuning = HX.subcool_DP_correction
        self.HX.Thermal.DP_r_2phase_tuning = HX._2phase_DP_correction
        if hasattr(HX,'h_a_wet_on'):
            self.HX.Thermal.h_a_wet_on = HX.h_a_wet_on
        else:
            self.HX.Thermal.h_a_wet_on = False
        if hasattr(HX,'DP_a_wet_on'):
            self.HX.Thermal.DP_a_wet_on = HX.DP_a_wet_on
        else:
            self.HX.Thermal.DP_a_wet_on = False

    def run(self):
        self.terminal_message.emit("Checked inputs")
        time.sleep(0.1)
        self.terminal_message.emit("Trying to solve Microchannel")
        time.sleep(0.1)
        result = self.solve()
        if result[0]:
            self.finished.emit((1,"Simulation finished",result[1]))
        else:
            self.finished.emit((0,result[1]))

    def solve(self):
        try:
            if self.cond == 0:
                self.AS.update(CP.PT_INPUTS,self.P_in ,self.T_in)
                self.h_in = self.AS.hmass()
            elif self.cond == 1:
                self.AS.update(CP.PQ_INPUTS,self.P_in ,self.Q_in)
                self.h_in = self.AS.hmass()
            elif self.cond == 2:
                self.AS.update(CP.QT_INPUTS,self.Q_in,self.T_in)
                self.P_in = self.AS.p()
                self.h_in = self.AS.hmass()
            elif self.cond == 3:
                if self.T_diff_in >= 0:
                    self.AS.update(CP.PQ_INPUTS,self.P_in ,1.0)
                    T_in = self.AS.T()
                    self.AS.update(CP.PT_INPUTS,self.P_in ,T_in+self.T_diff_in)
                    self.h_in = self.AS.hmass()
                elif self.T_diff_in < 0:
                    self.AS.update(CP.PQ_INPUTS,self.P_in ,0.0)
                    T_in = self.AS.T()
                    self.AS.update(CP.PT_INPUTS,self.P_in ,T_in+self.T_diff_in)
                    self.h_in = self.AS.hmass()
            elif self.cond == 4:
                if self.T_diff_in >= 0:
                    self.AS.update(CP.QT_INPUTS,1.0, self.T_in)
                    self.P_in = self.AS.p()
                    self.AS.update(CP.PT_INPUTS,self.P_in ,self.T_in+self.T_diff_in)
                    self.h_in = self.AS.hmass()
                elif self.T_diff_in < 0:
                    self.AS.update(CP.QT_INPUTS,0.0, self.T_in)
                    self.P_in = self.AS.p()
                    self.AS.update(CP.PT_INPUTS,self.P_in ,self.T_in+self.T_diff_in)
                    self.h_in = self.AS.hmass()
            
            print(self.P_in)
            print(self.T_in+self.T_diff_in)
            print(self.h_in)
            params={
                    'Pin_r': self.P_in ,
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
                return (0,"Failed to solve Microchannel")
    