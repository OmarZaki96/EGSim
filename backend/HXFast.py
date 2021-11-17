from math import pi, exp
from CoolProp.CoolProp import cair_sat
import CoolProp as CP
from numpy import finfo
from scipy.optimize import brentq
from CoolProp.CoolProp import HAPropsSI
from backend.FinTubeHEX import FinTubeHEXClass
from backend.MicroChannelHEX import MicroChannelHEXClass
import numpy as np
from math import log
from copy import deepcopy

class ValuesClass():
    pass

class Fintube_fastClass():

    def HX_define_fintube(self,Fintube,AS):
        self.AS = AS
        self.Fintube = Fintube
        HX = FinTubeHEXClass()
        HX.name = Fintube.name
        if Fintube.Accurate == "CoolProp":
            HX.Accurate = True
        elif Fintube.Accurate == "Psychrolib":
            HX.Accurate = False
        HX.create_circuits(Fintube.N_series_Circuits)
        for i in range(Fintube.N_series_Circuits):
            N = Fintube.circuits[i].N_Circuits
            connection = [i,i+1,i,1.0,N]
            HX.connect(*tuple(connection))
        HX.Tin_a = Fintube.Air_T
        HX.Pin_a = Fintube.Air_P
        Win_a = HAPropsSI("W","T",Fintube.Air_T,"P",Fintube.Air_P,"R",Fintube.Air_RH)
        HX.Win_a = Win_a
        if Fintube.Air_flow_direction == "Parallel":
            HX.Air_sequence = 'parallel'
            HX.Air_distribution = Fintube.Air_Distribution
        elif Fintube.Air_flow_direction == "Series-Parallel":
            HX.Air_sequence = 'series_parallel'
        elif Fintube.Air_flow_direction == "Series-Counter":
            HX.Air_sequence = 'series_counter'
        if Fintube.model == "Segment by Segment":
            HX.model = 'segment'
            N_segments = Fintube.N_segments
        elif Fintube.model == "Phase by Phase":
            HX.model = 'phase'
            N_segments = 1.0
        HX.Q_error_tol = Fintube.HX_Q_tol
        HX.max_iter_per_circuit = Fintube.N_iterations
        if Fintube.Fan_model == "Fan Efficiency Model":
            HX.Fan.model = 'efficiency'
            HX.Fan.efficiency = Fintube.Fan_model_efficiency_exp
        elif Fintube.Fan_model == "Fan Curve Model":
            HX.Fan.model = 'curve'
            HX.Fan.power_curve = Fintube.Fan_model_P_exp
            HX.Fan.DP_curve = Fintube.Fan_model_DP_exp
            
        HX.Fan.Fan_position = 'after'
        if hasattr(Fintube,"Vdot_ha"):
            HX.Vdot_ha = Fintube.Vdot_ha
        else:
            v_spec = HAPropsSI("V","T",Fintube.Tin_a,"W",Fintube.Win_a,"P",Fintube.Pin_a)
            HX.Vdot_ha = Fintube.mdot_da * v_spec
            
        
        if Fintube.solver == "Mass flow rate solver":
            HX.Solver = 'mdot'
        elif Fintube.solver == "Pressure drop solver":
            HX.Solver = 'dp'            
        
        for i in range(Fintube.N_series_Circuits):
            HX.Circuits[i].Geometry.Ntubes_per_bank_per_subcircuit = Fintube.circuits[i].N_tube_per_bank
            HX.Circuits[i].Geometry.Nbank = Fintube.circuits[i].N_bank
            HX.Circuits[i].Geometry.OD = Fintube.circuits[i].OD
            HX.Circuits[i].Geometry.Ltube = Fintube.circuits[i].Ltube
            if Fintube.circuits[i].Tube_type == "Smooth":
                HX.Circuits[i].Geometry.Tubes_type = "Smooth"
                HX.Circuits[i].Geometry.ID = Fintube.circuits[i].ID
                HX.Circuits[i].Geometry.e_D = Fintube.circuits[i].e_D
            elif Fintube.circuits[i].Tube_type == "Microfin":
                HX.Circuits[i].Geometry.Tubes_type = "Microfin"
                HX.Circuits[i].Geometry.t = Fintube.circuits[i].Tube_t
                HX.Circuits[i].Geometry.beta = Fintube.circuits[i].Tube_beta
                HX.Circuits[i].Geometry.e = Fintube.circuits[i].Tube_e
                HX.Circuits[i].Geometry.d = Fintube.circuits[i].Tube_d
                HX.Circuits[i].Geometry.gama = Fintube.circuits[i].Tube_gamma
                HX.Circuits[i].Geometry.n = Fintube.circuits[i].Tube_n
            HX.Circuits[i].Geometry.Staggering = Fintube.circuits[i].Staggering
            HX.Circuits[i].Geometry.Pl = Fintube.circuits[i].Pl
            HX.Circuits[i].Geometry.Pt = Fintube.circuits[i].Pt
            HX.Circuits[i].Geometry.Connections = Fintube.circuits[i].Connections
            HX.Circuits[i].Geometry.FarBendRadius = 0.01
            HX.Circuits[i].Geometry.FPI = Fintube.circuits[i].Fin_FPI
            HX.Circuits[i].Geometry.Fin_t = Fintube.circuits[i].Fin_t
            HX.Circuits[i].Geometry.FinType = Fintube.circuits[i].Fin_type
            if Fintube.circuits[i].Fin_type == "Wavy":
                HX.Circuits[i].Geometry.Fin_Pd = Fintube.circuits[i].Fin_pd
                HX.Circuits[i].Geometry.Fin_xf = Fintube.circuits[i].Fin_xf
            elif Fintube.circuits[i].Fin_type == "WavyLouvered":
                HX.Circuits[i].Geometry.Fin_Pd = Fintube.circuits[i].Fin_pd
                HX.Circuits[i].Geometry.Fin_xf = Fintube.circuits[i].Fin_xf
            elif Fintube.circuits[i].Fin_type == "Louvered":
                HX.Circuits[i].Geometry.Fin_Lp = Fintube.circuits[i].Fin_Lp
                HX.Circuits[i].Geometry.Fin_Lh = Fintube.circuits[i].Fin_Lh
            elif Fintube.circuits[i].Fin_type == "Slit":
                HX.Circuits[i].Geometry.Fin_Sh = Fintube.circuits[i].Fin_Sh
                HX.Circuits[i].Geometry.Fin_Ss = Fintube.circuits[i].Fin_Ss
                HX.Circuits[i].Geometry.Fin_Sn = Fintube.circuits[i].Fin_Sn
                
            HX.Circuits[i].Thermal.Nsegments = N_segments
            HX.Circuits[i].Thermal.kw = Fintube.circuits[i].Tube_k
            HX.Circuits[i].Thermal.k_fin = Fintube.circuits[i].Fin_k
            HX.Circuits[i].Thermal.FinsOnce = True
            HX.Circuits[i].Thermal.HTC_superheat_Corr = Fintube.circuits[i].superheat_HTC_corr
            HX.Circuits[i].Thermal.HTC_subcool_Corr = Fintube.circuits[i].subcool_HTC_corr
            HX.Circuits[i].Thermal.DP_superheat_Corr = Fintube.circuits[i].superheat_DP_corr
            HX.Circuits[i].Thermal.DP_subcool_Corr = Fintube.circuits[i].subcool_DP_corr
            HX.Circuits[i].Thermal.HTC_2phase_Corr = Fintube.circuits[i]._2phase_HTC_corr
            HX.Circuits[i].Thermal.DP_2phase_Corr = Fintube.circuits[i]._2phase_DP_corr
            HX.Circuits[i].Thermal.DP_Accel_Corr = Fintube.circuits[i]._2phase_charge_corr + 1
            HX.Circuits[i].Thermal.rho_2phase_Corr = Fintube.circuits[i]._2phase_charge_corr + 1
            HX.Circuits[i].Thermal.Air_dry_Corr = Fintube.circuits[i].air_dry_HTC_corr
            HX.Circuits[i].Thermal.Air_wet_Corr = Fintube.circuits[i].air_wet_HTC_corr
            HX.Circuits[i].Thermal.h_r_superheat_tuning = Fintube.circuits[i].superheat_HTC_correction
            HX.Circuits[i].Thermal.h_r_subcooling_tuning = Fintube.circuits[i].subcool_HTC_correction
            HX.Circuits[i].Thermal.h_r_2phase_tuning = Fintube.circuits[i]._2phase_HTC_correction
            HX.Circuits[i].Thermal.h_a_dry_tuning = Fintube.circuits[i].air_dry_HTC_correction
            HX.Circuits[i].Thermal.h_a_wet_tuning = Fintube.circuits[i].air_wet_HTC_correction
            HX.Circuits[i].Thermal.DP_a_dry_tuning = Fintube.circuits[i].air_dry_DP_correction
            HX.Circuits[i].Thermal.DP_a_wet_tuning = Fintube.circuits[i].air_wet_DP_correction
            HX.Circuits[i].Thermal.DP_r_superheat_tuning = Fintube.circuits[i].superheat_DP_correction
            HX.Circuits[i].Thermal.DP_r_subcooling_tuning = Fintube.circuits[i].subcool_DP_correction
            HX.Circuits[i].Thermal.DP_r_2phase_tuning = Fintube.circuits[i]._2phase_DP_correction
            if hasattr(Fintube.circuits[i],'h_a_wet_on'):
                HX.Circuits[i].Thermal.h_a_wet_on = Fintube.circuits[i].h_a_wet_on
            else:
                HX.Circuits[i].Thermal.h_a_wet_on = False
            if hasattr(Fintube.circuits[i],'DP_a_wet_on'):
                HX.Circuits[i].Thermal.DP_a_wet_on = Fintube.circuits[i].DP_a_wet_on
            else:
                HX.Circuits[i].Thermal.DP_a_wet_on = False

            if hasattr(Fintube.circuits[i],'sub_HX_values'):
                HX.Circuits[i].Geometry.Sub_HX_matrix = Fintube.circuits[i].sub_HX_values
    
        rho_ha = 1 / HAPropsSI('V','T',HX.Tin_a, 'P',HX.Pin_a, 'W', HX.Win_a)
        
        if hasattr(HX,"Vdot_ha"):
            Vdot_a = HX.Vdot_ha
        else:
            v_spec = HAPropsSI("V","T",HX.Tin_a,"W",HX.Win_a,"P",HX.Pin_a)
            Vdot_a = HX.mdot_da * v_spec
        if HX.Air_sequence == 'parallel':
            for i,circuit in enumerate(HX.Circuits):
                circuit.Thermal.Vdot_ha = Vdot_a * HX.Air_distribution[i]
                circuit.Thermal.mdot_ha = circuit.Thermal.Vdot_ha * rho_ha
        elif HX.Air_sequence in ['series_counter','series_parallel']:
            for i,circuit in enumerate(HX.Circuits):
                circuit.Thermal.Vdot_ha = Vdot_a
                circuit.Thermal.mdot_ha = circuit.Thermal.Vdot_ha * rho_ha

        self.HX = HX
        
    def solve(self,mdot_r,Pin_r,hin_r):
        AS = self.AS
        AS.update(CP.PQ_INPUTS,Pin_r,1.0)
        hV = AS.hmass()
        Tdew = AS.T()
        AS.update(CP.PQ_INPUTS,Pin_r,0.0)
        hL = AS.hmass()
        T_bubble = AS.T()
        xin_r = (hin_r - hL) / (hV - hL)
        AS.update(CP.HmassP_INPUTS,hin_r,Pin_r)
        Tin_r = AS.T()

        if hasattr(self,"HX"):
            L_circuit = 0
            A_a = 0
            h_a_array = []
            h_r_2phase_array = []
            h_r_subcool_array = []
            h_r_superheat_array = []
            DP_r_2phase_array = []
            DP_r_subcool_array = []
            DP_r_superheat_array = []
            N_subcircuits_array = []
    
            for circuit in self.HX.Circuits:
                N_subcircuits_array.append(circuit.Geometry.Nsubcircuits)
                mdot_r_circuit = mdot_r / circuit.Geometry.Nsubcircuits
                circuit.geometry()
                L_circuit += circuit.Geometry.Lsubcircuit * circuit.Geometry.Nsubcircuits
                circuit.Thermal.FinsOnce = True
                circuit.Thermal.Tin_a = self.HX.Tin_a
                circuit.Thermal.Pin_a = self.HX.Pin_a
                circuit.Thermal.Win_a = self.HX.Win_a
                circuit.model = "phase"
    
                rho_ha = 1 / HAPropsSI('V','T',self.HX.Tin_a, 'P',self.HX.Pin_a, 'W', self.HX.Win_a)
                
                circuit.Thermal.mdot_ha = circuit.Thermal.Vdot_ha * rho_ha
    
                mdot_ha = circuit.Thermal.mdot_ha
    
                h_a_dry, DP_dry, eta_o_dry = circuit.fins_calculate(self.HX.Pin_a,self.HX.Pin_a,self.HX.Tin_a,self.HX.Tin_a,self.HX.Win_a,self.HX.Win_a,
                                                                    mdot_ha,1.0,Wet=False,Accurate=True,Tw_o=None,water_cond=None,mu_f=None)
    
                rho_ha = 1 / HAPropsSI('V','T',self.HX.Tin_a, 'P',self.HX.Pin_a+DP_dry/2, 'W', self.HX.Win_a)
                
                circuit.Thermal.mdot_ha = circuit.Thermal.Vdot_ha * rho_ha
    
                h_a_array.append(h_a_dry * eta_o_dry)
                A_a += circuit.Fins.Ao * circuit.Geometry.Nsubcircuits
                D = circuit.Geometry.Dh
    
                if self.HX.Tin_a > Tin_r: #Evaporator
                    if xin_r < 0:
                        qflux = mdot_r_circuit * (hV - hL) / (L_circuit * pi * D * 0.8)
                        AS.update(CP.PT_INPUTS,Pin_r,(Tin_r+T_bubble)/2)
                        h_r = AS.hmass()
                        circuit.Correlations.update(AS,circuit.Geometry,circuit.Thermal,'1phase',Pin_r,h_r,mdot_r_circuit,L_circuit * pi * D,'cooler')
                        h_r_subcool_array.append(circuit.Correlations.calculate_h_1phase())
                        DP_r_subcool_array.append(circuit.Correlations.calculate_dPdz_f_1phase())
                        
                        circuit.Correlations.update(AS,circuit.Geometry,circuit.Thermal,'2phase',Pin_r,0,mdot_r_circuit,L_circuit * pi * D,'cooler',q_flux=qflux,var_2nd_out=1.0)
                        h_r_2phase_array.append(circuit.Correlations.calculate_h_2phase())
                        DP_r_2phase_array.append(circuit.Correlations.calculate_dPdz_f_2phase())
                        
                        AS.update(CP.PT_INPUTS,Pin_r,Tdew+1)
                        h_r = AS.hmass()
                        circuit.Correlations.update(AS,circuit.Geometry,circuit.Thermal,'1phase',Pin_r,h_r,mdot_r_circuit,L_circuit * pi * D,'cooler')
                        h_r_superheat_array.append(circuit.Correlations.calculate_h_1phase())
                        DP_r_superheat_array.append(circuit.Correlations.calculate_dPdz_f_1phase())
    
                    elif 0 < xin_r < 1:
                        qflux = mdot_r_circuit * (hV - hin_r) / (L_circuit * pi * D * 0.8)
                        AS.update(CP.PT_INPUTS,Pin_r,T_bubble-1)
                        h_r = AS.hmass()
                        circuit.Correlations.update(AS,circuit.Geometry,circuit.Thermal,'1phase',Pin_r,h_r,mdot_r_circuit,L_circuit * pi * D,'cooler')
                        h_r_subcool_array.append(circuit.Correlations.calculate_h_1phase())
                        DP_r_subcool_array.append(circuit.Correlations.calculate_dPdz_f_1phase())
                        
                        circuit.Correlations.update(AS,circuit.Geometry,circuit.Thermal,'2phase',Pin_r,xin_r,mdot_r_circuit,L_circuit * pi * D,'cooler',q_flux=qflux,var_2nd_out = 1.0)
                        h_r_2phase_array.append(circuit.Correlations.calculate_h_2phase())
                        DP_r_2phase_array.append(circuit.Correlations.calculate_dPdz_f_2phase())
                        
                        AS.update(CP.PT_INPUTS,Pin_r,Tdew+1)
                        h_r = AS.hmass()
                        circuit.Correlations.update(AS,circuit.Geometry,circuit.Thermal,'1phase',Pin_r,h_r,mdot_r_circuit,L_circuit * pi * D,'cooler')
                        h_r_superheat_array.append(circuit.Correlations.calculate_h_1phase())
                        DP_r_superheat_array.append(circuit.Correlations.calculate_dPdz_f_1phase())
    
                    elif xin_r > 1:
                        qflux = mdot_r_circuit * (hV - hL) / (L_circuit * pi * D * 0.8)
                        AS.update(CP.PT_INPUTS,Pin_r,T_bubble-1)
                        h_r = AS.hmass()
                        circuit.Correlations.update(AS,circuit.Geometry,circuit.Thermal,'1phase',Pin_r,h_r,mdot_r_circuit,L_circuit * pi * D,'cooler')
                        h_r_subcool_array.append(circuit.Correlations.calculate_h_1phase())
                        DP_r_subcool_array.append(circuit.Correlations.calculate_dPdz_f_1phase())
                        
                        circuit.Correlations.update(AS,circuit.Geometry,circuit.Thermal,'2phase',Pin_r,0.0,mdot_r_circuit,L_circuit * pi * D,'cooler',q_flux=qflux,var_2nd_out=1.0)
                        h_r_2phase_array.append(circuit.Correlations.calculate_h_2phase())
                        DP_r_2phase_array.append(circuit.Correlations.calculate_dPdz_f_2phase())
                        
                        AS.update(CP.PT_INPUTS,Pin_r,Tin_r)
                        h_r = AS.hmass()
                        circuit.Correlations.update(AS,circuit.Geometry,circuit.Thermal,'1phase',Pin_r,h_r,mdot_r_circuit,L_circuit * pi * D,'cooler')
                        h_r_superheat_array.append(circuit.Correlations.calculate_h_1phase())
                        DP_r_superheat_array.append(circuit.Correlations.calculate_dPdz_f_1phase())
    
                elif self.HX.Tin_a < Tin_r: #condenser
                    if xin_r < 0:
                        qflux = mdot_r_circuit * (hV - hL) / (L_circuit * pi * D * 0.8)
                        AS.update(CP.PT_INPUTS,Pin_r,Tin_r)
                        h_r = AS.hmass()
                        circuit.Correlations.update(AS,circuit.Geometry,circuit.Thermal,'1phase',Pin_r,h_r,mdot_r_circuit,L_circuit * pi * D,'heater')
                        h_r_subcool_array.append(circuit.Correlations.calculate_h_1phase())
                        DP_r_subcool_array.append(circuit.Correlations.calculate_dPdz_f_1phase())
                        
                        circuit.Correlations.update(AS,circuit.Geometry,circuit.Thermal,'2phase',Pin_r,1.0,mdot_r_circuit,L_circuit * pi * D,'heater',q_flux=qflux,var_2nd_out=0.0)
                        h_r_2phase_array.append(circuit.Correlations.calculate_h_2phase())
                        DP_r_2phase_array.append(circuit.Correlations.calculate_dPdz_f_2phase())
                        
                        AS.update(CP.PT_INPUTS,Pin_r,Tdew+1)
                        h_r = AS.hmass()
                        circuit.Correlations.update(AS,circuit.Geometry,circuit.Thermal,'1phase',Pin_r,h_r,mdot_r_circuit,L_circuit * pi * D,'heater')
                        h_r_superheat_array.append(circuit.Correlations.calculate_h_1phase())
                        DP_r_superheat_array.append(circuit.Correlations.calculate_dPdz_f_1phase())
    
                    elif 0 < xin_r < 1:
                        qflux = mdot_r_circuit * (hin_r - hL) / (L_circuit * pi * D * 0.8)
                        AS.update(CP.PT_INPUTS,Pin_r,T_bubble-1)
                        h_r = AS.hmass()
                        circuit.Correlations.update(AS,circuit.Geometry,circuit.Thermal,'1phase',Pin_r,h_r,mdot_r_circuit,L_circuit * pi * D,'heater')
                        h_r_subcool_array.append(circuit.Correlations.calculate_h_1phase())
                        DP_r_subcool_array.append(circuit.Correlations.calculate_dPdz_f_1phase())
                        
                        circuit.Correlations.update(AS,circuit.Geometry,circuit.Thermal,'2phase',Pin_r,xin_r,mdot_r_circuit,L_circuit * pi * D,'heater',q_flux=qflux,var_2nd_out=1.0)
                        h_r_2phase_array.append(circuit.Correlations.calculate_h_2phase())
                        DP_r_2phase_array.append(circuit.Correlations.calculate_dPdz_f_2phase())
                        
                        AS.update(CP.PT_INPUTS,Pin_r,Tdew+1)
                        h_r = AS.hmass()
                        circuit.Correlations.update(AS,circuit.Geometry,circuit.Thermal,'1phase',Pin_r,h_r,mdot_r_circuit,L_circuit * pi * D,'heater')
                        h_r_superheat_array.append(circuit.Correlations.calculate_h_1phase())
                        DP_r_superheat_array.append(circuit.Correlations.calculate_dPdz_f_1phase())
                    
                    elif xin_r > 1:
                        qflux = mdot_r_circuit * (hV - hL) / (L_circuit * pi * D * 0.8)
                        AS.update(CP.PT_INPUTS,Pin_r,T_bubble-1)
                        h_r = AS.hmass()
                        circuit.Correlations.update(AS,circuit.Geometry,circuit.Thermal,'1phase',Pin_r,h_r,mdot_r_circuit,L_circuit * pi * D,'heater')
                        h_r_subcool_array.append(circuit.Correlations.calculate_h_1phase())
                        DP_r_subcool_array.append(circuit.Correlations.calculate_dPdz_f_1phase())
                        
                        circuit.Correlations.update(AS,circuit.Geometry,circuit.Thermal,'2phase',Pin_r,1.0,mdot_r_circuit,L_circuit * pi * D,'heater',q_flux=qflux,var_2nd_out=0.0)
                        h_r_2phase_array.append(circuit.Correlations.calculate_h_2phase())
                        DP_r_2phase_array.append(circuit.Correlations.calculate_dPdz_f_2phase())
                        
                        AS.update(CP.PT_INPUTS,Pin_r,Tin_r)
                        h_r = AS.hmass()
                        circuit.Correlations.update(AS,circuit.Geometry,circuit.Thermal,'1phase',Pin_r,h_r,mdot_r_circuit,L_circuit * pi * D,'heater')
                        h_r_superheat_array.append(circuit.Correlations.calculate_h_1phase())
                        DP_r_superheat_array.append(circuit.Correlations.calculate_dPdz_f_1phase())

            N_subircuits = np.average(N_subcircuits_array)
            Fast_HX = ValuesClass()
            Fast_HX.N_circuits = N_subircuits
            Fast_HX.h_a = np.average(h_a_array)
            Fast_HX.A_a_total = A_a
            Fast_HX.h_r_2phase = np.average(h_r_2phase_array)
            Fast_HX.h_r_superheat = np.average(h_r_superheat_array)
            Fast_HX.h_r_subcool = np.average(h_r_subcool_array)
            Fast_HX.D = D
            Fast_HX.L_circuit = L_circuit / N_subircuits
            Fast_HX.Tin_a = self.HX.Tin_a
            Fast_HX.Win_a = self.HX.Win_a
            
            if hasattr(self.HX,"Vdot_ha"):
                Fast_HX.Vdot_ha = self.HX.Vdot_ha
            else:
                v_spec = HAPropsSI("V","T",self.HX.Tin_a,"W",self.HX.Win_a,"P",self.HX.Pin_a)
                Fast_HX.Vdot_ha = self.HX.mdot_da * v_spec
                
            Fast_HX.DPDZ_2phase = np.average(DP_r_2phase_array)
            Fast_HX.DPDZ_superheat = np.average(DP_r_superheat_array)
            Fast_HX.DPDZ_subcool = np.average(DP_r_subcool_array)
            self.HX_fast_calc = deepcopy(Fast_HX)
            
        elif hasattr(self,"HX_fast"):
            Fast_HX = deepcopy(self.HX_fast)
        
        Fast_HX.AS = AS
        Fast_HX.Pin_r = Pin_r
        Fast_HX.hin_r = hin_r
        Fast_HX.G_r = mdot_r / (pi/4 * Fast_HX.D**2) / Fast_HX.N_circuits
        Fast_HX.A_a_total /= Fast_HX.N_circuits
        Fast_HX.Vdot_ha /= Fast_HX.N_circuits
        DP,TTD = HX_Fast_calculate(Fast_HX)
        return DP,TTD

class Microchannel_fastClass():

    def HX_define_microchannel(self,Microchannel,AS):
        self.AS = AS
        HX = MicroChannelHEXClass()
        HX.name = Microchannel.name
        if Microchannel.Accurate == "CoolProp":
            HX.Accurate = True
        elif Microchannel.Accurate == "Psychrolib":
            HX.Accurate = False
        HX.Tin_a = Microchannel.Air_T
        HX.Pin_a = Microchannel.Air_P
        Win_a = HAPropsSI("W","T",Microchannel.Air_T,"P",Microchannel.Air_P,"R",Microchannel.Air_RH)
        HX.Win_a = Win_a
        if Microchannel.model == "Segment by Segment":
            HX.model = 'segment'
            HX.Thermal.Nsegments = Microchannel.N_segments
        elif Microchannel.model == "Phase by Phase":
            HX.model = 'phase'
            HX.Thermal.Nsegments = 1.0
        HX.Q_error_tol = Microchannel.HX_Q_tol
        HX.max_iter_per_circuit = Microchannel.N_iterations
        if Microchannel.Fan_model == "Fan Efficiency Model":
            HX.Fan.model = 'efficiency'
            HX.Fan.efficiency = Microchannel.Fan_model_efficiency_exp
        elif Microchannel.Fan_model == "Fan Curve Model":
            HX.Fan.model = 'curve'
            HX.Fan.power_curve = Microchannel.Fan_model_P_exp
            HX.Fan.DP_curve = Microchannel.Fan_model_DP_exp
    
        HX.Fan.Fan_position = 'after'
        
        HX.Geometry.N_tube_per_bank_per_pass = Microchannel.Circuiting.bank_passes
        if Microchannel.Geometry.Fin_on_side_index:
            HX.Geometry.Fin_rows = Microchannel.N_tube_per_bank + 1
        else:
            HX.Geometry.Fin_rows = Microchannel.N_tube_per_bank - 1
    
        HX.Geometry.T_L = Microchannel.Geometry.T_l
        HX.Geometry.T_w = Microchannel.Geometry.T_w
        HX.Geometry.T_h = Microchannel.Geometry.T_h
        HX.Geometry.T_s = Microchannel.Geometry.T_s
        HX.Geometry.P_shape = Microchannel.Geometry.port_shape
        HX.Geometry.P_end = Microchannel.Geometry.T_end
        HX.Geometry.P_a = Microchannel.Geometry.port_a_dim
        if Microchannel.Geometry.port_shape in ['Rectangle', 'Triangle']:
            HX.Geometry.P_b = Microchannel.Geometry.port_b_dim
        HX.Geometry.N_port = Microchannel.Geometry.N_ports
        HX.Geometry.Enhanced = False
        HX.Geometry.FinType = Microchannel.Geometry.Fin_type
        if Microchannel.Geometry.Fin_type == "Louvered":
            HX.Geometry.Fin_Llouv = Microchannel.Geometry.Fin_llouv
            HX.Geometry.Fin_alpha = Microchannel.Geometry.Fin_lalpha
            HX.Geometry.Fin_Lp = Microchannel.Geometry.Fin_lp
            
        HX.Geometry.Fin_t = Microchannel.Geometry.Fin_t
        HX.Geometry.Fin_L = Microchannel.Geometry.Fin_l
        HX.Geometry.FPI = Microchannel.Geometry.Fin_FPI
        HX.Geometry.e_D = Microchannel.Geometry.e_D
        HX.Geometry.Header_CS_Type = Microchannel.Geometry.header_shape
        HX.Geometry.Header_dim_a = Microchannel.Geometry.header_a_dim
        if Microchannel.Geometry.header_shape in ["Rectangle"]:
            HX.Geometry.Header_dim_b = Microchannel.Geometry.header_b_dim
        HX.Geometry.Header_length = Microchannel.Geometry.header_height
    
        if hasattr(Microchannel,"Vdot_ha"):    
            HX.Vdot_ha = Microchannel.Vdot_ha
        else:
            
            v_spec = HAPropsSI("V","T",Microchannel.Tin_a,"W",Microchannel.Win_a,"P",Microchannel.Pin_a)
            HX.Vdot_ha = Microchannel.mdot_da * v_spec
            
        HX.Thermal.k_fin = Microchannel.Geometry.Fin_k
        HX.Thermal.kw = Microchannel.Geometry.Tube_k
        HX.Thermal.Headers_DP_r = Microchannel.Geometry.Header_DP
        HX.Thermal.FinsOnce = True
        HX.Thermal.HTC_superheat_Corr = Microchannel.superheat_HTC_corr
        HX.Thermal.HTC_subcool_Corr = Microchannel.subcool_HTC_corr
        HX.Thermal.DP_superheat_Corr = Microchannel.superheat_DP_corr
        HX.Thermal.DP_subcool_Corr = Microchannel.subcool_DP_corr
        HX.Thermal.HTC_2phase_Corr = Microchannel._2phase_HTC_corr
        HX.Thermal.DP_2phase_Corr = Microchannel._2phase_DP_corr
        HX.Thermal.DP_Accel_Corr = Microchannel._2phase_charge_corr + 1
        HX.Thermal.rho_2phase_Corr = Microchannel._2phase_charge_corr + 1
        HX.Thermal.Air_dry_Corr = Microchannel.air_dry_HTC_corr
        HX.Thermal.Air_wet_Corr = Microchannel.air_wet_HTC_corr
        HX.Thermal.h_r_superheat_tuning = Microchannel.superheat_HTC_correction
        HX.Thermal.h_r_subcooling_tuning = Microchannel.subcool_HTC_correction
        HX.Thermal.h_r_2phase_tuning = Microchannel._2phase_HTC_correction
        HX.Thermal.h_a_dry_tuning = Microchannel.air_dry_HTC_correction
        HX.Thermal.h_a_wet_tuning = Microchannel.air_wet_HTC_correction
        HX.Thermal.DP_a_dry_tuning = Microchannel.air_dry_DP_correction
        HX.Thermal.DP_a_wet_tuning = Microchannel.air_wet_DP_correction
        HX.Thermal.DP_r_superheat_tuning = Microchannel.superheat_DP_correction
        HX.Thermal.DP_r_subcooling_tuning = Microchannel.subcool_DP_correction
        HX.Thermal.DP_r_2phase_tuning = Microchannel._2phase_DP_correction
        if hasattr(Microchannel,'h_a_wet_on'):
            HX.Thermal.h_a_wet_on = Microchannel.h_a_wet_on
        else:
            HX.Thermal.h_a_wet_on = False
        if hasattr(Microchannel,'DP_a_wet_on'):
            HX.Thermal.DP_a_wet_on = Microchannel.DP_a_wet_on
        else:
            HX.Thermal.DP_a_wet_on = False
        
        self.HX = HX
        
    def solve(self,mdot_r,Pin_r,hin_r):
        AS = self.AS
        
        AS.update(CP.PQ_INPUTS,Pin_r,1.0)
        hV = AS.hmass()
        Tdew = AS.T()
        AS.update(CP.PQ_INPUTS,Pin_r,0.0)
        hL = AS.hmass()
        T_bubble = AS.T()
        xin_r = (hin_r - hL) / (hV - hL)
        AS.update(CP.HmassP_INPUTS,hin_r,Pin_r)
        Tin_r = AS.T()

        if hasattr(self,"HX"):   
            if hasattr(self.HX,"Vdot_ha"):
                Vdot_a = self.HX.Vdot_ha
            else:
                v_spec = HAPropsSI("V","T",self.HX.Tin_a,"W",self.HX.Win_a,"P",self.HX.Pin_a)
                Vdot_a = self.HX.mdot_da*v_spec
                
            self.HX.geometry()
            N_circuits = float(self.HX.Geometry.N_circuits)
            mdot_r_circuit = mdot_r / N_circuits
            L_circuit = float(self.HX.Geometry.L_circuit)
            self.HX.model = "phase"
            rho_ha = 1 / HAPropsSI('V','T',self.HX.Tin_a, 'P',self.HX.Pin_a, 'W', self.HX.Win_a)
            
            mdot_ha = float(Vdot_a / rho_ha)
            
            self.HX.Thermal.mdot_ha = mdot_ha
    
            h_a_dry, DP_dry, eta_o_dry = self.HX.fins_calculate(self.HX.Pin_a,self.HX.Pin_a,self.HX.Tin_a,self.HX.Tin_a,self.HX.Win_a,self.HX.Win_a,
                                                                mdot_ha,1.0,Wet=False,Accurate=True,Tw_o=None,water_cond=None,mu_f=None)
    
            rho_ha = 1 / HAPropsSI('V','T',self.HX.Tin_a, 'P',self.HX.Pin_a+DP_dry/2, 'W', self.HX.Win_a)
            
            self.HX.Thermal.mdot_ha = Vdot_a * rho_ha
    
            h_a = float(h_a_dry * eta_o_dry)
            A_a = float(self.HX.Fins.Ao)
            D = float(self.HX.Geometry.inner_circum / pi)
            
            if self.HX.Tin_a > Tin_r: #Evaporator
                if xin_r < 0:
                    qflux = mdot_r_circuit * (hV - hL) / (L_circuit * pi * D * 0.8)
                    AS.update(CP.PT_INPUTS,Pin_r,(Tin_r+T_bubble)/2)
                    h_r = AS.hmass()
                    self.HX.Correlations.update(AS,self.HX.Geometry,self.HX.Thermal,'1phase',Pin_r,h_r,mdot_r_circuit,L_circuit * pi * D,'cooler')
                    h_r_subcool = self.HX.Correlations.calculate_h_1phase()
                    DP_r_subcool = self.HX.Correlations.calculate_dPdz_f_1phase()
                    
                    self.HX.Correlations.update(AS,self.HX.Geometry,self.HX.Thermal,'2phase',Pin_r,0,mdot_r_circuit,L_circuit * pi * D,'cooler',q_flux=qflux,var_2nd_out=1.0)
                    h_r_2phase = self.HX.Correlations.calculate_h_2phase()
                    DP_r_2phase = self.HX.Correlations.calculate_dPdz_f_2phase()
                    
                    AS.update(CP.PT_INPUTS,Pin_r,Tdew+1)
                    h_r = AS.hmass()
                    self.HX.Correlations.update(AS,self.HX.Geometry,self.HX.Thermal,'1phase',Pin_r,h_r,mdot_r_circuit,L_circuit * pi * D,'cooler')
                    h_r_superheat = self.HX.Correlations.calculate_h_1phase()
                    DP_r_superheat = self.HX.Correlations.calculate_dPdz_f_1phase()
        
                elif 0 < xin_r < 1:
                    qflux = mdot_r_circuit * (hV - hin_r) / (L_circuit * pi * D * 0.8)
                    AS.update(CP.PT_INPUTS,Pin_r,T_bubble-1)
                    h_r = AS.hmass()
                    self.HX.Correlations.update(AS,self.HX.Geometry,self.HX.Thermal,'1phase',Pin_r,h_r,mdot_r_circuit,L_circuit * pi * D,'cooler')
                    h_r_subcool = self.HX.Correlations.calculate_h_1phase()
                    DP_r_subcool = self.HX.Correlations.calculate_dPdz_f_1phase()
                    
                    self.HX.Correlations.update(AS,self.HX.Geometry,self.HX.Thermal,'2phase',Pin_r,xin_r,mdot_r_circuit,L_circuit * pi * D,'cooler',q_flux=qflux,var_2nd_out = 1.0)
                    h_r_2phase = self.HX.Correlations.calculate_h_2phase()
                    DP_r_2phase = self.HX.Correlations.calculate_dPdz_f_2phase()
                    
                    AS.update(CP.PT_INPUTS,Pin_r,Tdew+1)
                    h_r = AS.hmass()
                    self.HX.Correlations.update(AS,self.HX.Geometry,self.HX.Thermal,'1phase',Pin_r,h_r,mdot_r_circuit,L_circuit * pi * D,'cooler')
                    h_r_superheat = self.HX.Correlations.calculate_h_1phase()
                    DP_r_superheat = self.HX.Correlations.calculate_dPdz_f_1phase()
        
                elif xin_r > 1:
                    qflux = mdot_r_circuit * (hV - hL) / (L_circuit * pi * D * 0.8)
                    AS.update(CP.PT_INPUTS,Pin_r,T_bubble-1)
                    h_r = AS.hmass()
                    self.HX.Correlations.update(AS,self.HX.Geometry,self.HX.Thermal,'1phase',Pin_r,h_r,mdot_r_circuit,L_circuit * pi * D,'cooler')
                    h_r_subcool = self.HX.Correlations.calculate_h_1phase()
                    DP_r_subcool = self.HX.Correlations.calculate_dPdz_f_1phase()
                    
                    self.HX.Correlations.update(AS,self.HX.Geometry,self.HX.Thermal,'2phase',Pin_r,0.0,mdot_r_circuit,L_circuit * pi * D,'cooler',q_flux=qflux,var_2nd_out=1.0)
                    h_r_2phase = self.HX.Correlations.calculate_h_2phase()
                    DP_r_2phase = self.HX.Correlations.calculate_dPdz_f_2phase()
                    
                    AS.update(CP.PT_INPUTS,Pin_r,Tin_r)
                    h_r = AS.hmass()
                    self.HX.Correlations.update(AS,self.HX.Geometry,self.HX.Thermal,'1phase',Pin_r,h_r,mdot_r_circuit,L_circuit * pi * D,'cooler')
                    h_r_superheat = self.HX.Correlations.calculate_h_1phase()
                    DP_r_superheat = self.HX.Correlations.calculate_dPdz_f_1phase()
        
            elif self.HX.Tin_a < Tin_r: #condenser
                if xin_r < 0:
                    qflux = mdot_r_circuit * (hV - hL) / (L_circuit * pi * D * 0.8)
                    AS.update(CP.PT_INPUTS,Pin_r,Tin_r)
                    h_r = AS.hmass()
                    self.HX.Correlations.update(AS,self.HX.Geometry,self.HX.Thermal,'1phase',Pin_r,h_r,mdot_r_circuit,L_circuit * pi * D,'heater')
                    h_r_subcool = self.HX.Correlations.calculate_h_1phase()
                    DP_r_subcool = self.HX.Correlations.calculate_dPdz_f_1phase()
                    
                    self.HX.Correlations.update(AS,self.HX.Geometry,self.HX.Thermal,'2phase',Pin_r,1.0,mdot_r_circuit,L_circuit * pi * D,'heater',q_flux=qflux,var_2nd_out=0.0)
                    h_r_2phase = self.HX.Correlations.calculate_h_2phase()
                    DP_r_2phase = self.HX.Correlations.calculate_dPdz_f_2phase()
                    
                    AS.update(CP.PT_INPUTS,Pin_r,Tdew+1)
                    h_r = AS.hmass()
                    self.HX.Correlations.update(AS,self.HX.Geometry,self.HX.Thermal,'1phase',Pin_r,h_r,mdot_r_circuit,L_circuit * pi * D,'heater')
                    h_r_superheat = self.HX.Correlations.calculate_h_1phase()
                    DP_r_superheat = self.HX.Correlations.calculate_dPdz_f_1phase()
        
                elif 0 < xin_r < 1:
                    qflux = mdot_r_circuit * (hin_r - hL) / (L_circuit * pi * D * 0.8)
                    AS.update(CP.PT_INPUTS,Pin_r,T_bubble-1)
                    h_r = AS.hmass()
                    self.HX.Correlations.update(AS,self.HX.Geometry,self.HX.Thermal,'1phase',Pin_r,h_r,mdot_r_circuit,L_circuit * pi * D,'heater')
                    h_r_subcool = self.HX.Correlations.calculate_h_1phase()
                    DP_r_subcool = self.HX.Correlations.calculate_dPdz_f_1phase()
                    
                    self.HX.Correlations.update(AS,self.HX.Geometry,self.HX.Thermal,'2phase',Pin_r,xin_r,mdot_r_circuit,L_circuit * pi * D,'heater',q_flux=qflux,var_2nd_out=1.0)
                    h_r_2phase = self.HX.Correlations.calculate_h_2phase()
                    DP_r_2phase = self.HX.Correlations.calculate_dPdz_f_2phase()
                    
                    AS.update(CP.PT_INPUTS,Pin_r,Tdew+1)
                    h_r = AS.hmass()
                    self.HX.Correlations.update(AS,self.HX.Geometry,self.HX.Thermal,'1phase',Pin_r,h_r,mdot_r_circuit,L_circuit * pi * D,'heater')
                    h_r_superheat = self.HX.Correlations.calculate_h_1phase()
                    DP_r_superheat = self.HX.Correlations.calculate_dPdz_f_1phase()
                
                elif xin_r > 1:
                    qflux = mdot_r_circuit * (hV - hL) / (L_circuit * pi * D * 0.8)
                    AS.update(CP.PT_INPUTS,Pin_r,T_bubble-1)
                    h_r = AS.hmass()
                    self.HX.Correlations.update(AS,self.HX.Geometry,self.HX.Thermal,'1phase',Pin_r,h_r,mdot_r_circuit,L_circuit * pi * D,'heater')
                    h_r_subcool = self.HX.Correlations.calculate_h_1phase()
                    DP_r_subcool = self.HX.Correlations.calculate_dPdz_f_1phase()
                    
                    self.HX.Correlations.update(AS,self.HX.Geometry,self.HX.Thermal,'2phase',Pin_r,1.0,mdot_r_circuit,L_circuit * pi * D,'heater',q_flux=qflux,var_2nd_out=0.0)
                    h_r_2phase = self.HX.Correlations.calculate_h_2phase()
                    DP_r_2phase = self.HX.Correlations.calculate_dPdz_f_2phase()
                    
                    AS.update(CP.PT_INPUTS,Pin_r,Tin_r)
                    h_r = AS.hmass()
                    self.HX.Correlations.update(AS,self.HX.Geometry,self.HX.Thermal,'1phase',Pin_r,h_r,mdot_r_circuit,L_circuit * pi * D,'heater')
                    h_r_superheat = self.HX.Correlations.calculate_h_1phase()
                    DP_r_superheat = self.HX.Correlations.calculate_dPdz_f_1phase()
                
            Fast_HX = ValuesClass()
            Fast_HX.N_circuits = N_circuits
            Fast_HX.h_a = h_a
            Fast_HX.A_a_total = A_a / N_circuits
            Fast_HX.h_r_2phase = h_r_2phase
            Fast_HX.h_r_superheat = h_r_superheat
            Fast_HX.h_r_subcool = h_r_subcool
            Fast_HX.D = D
            Fast_HX.L_circuit = L_circuit
            Fast_HX.Tin_a = self.HX.Tin_a
            Fast_HX.Win_a = self.HX.Win_a
            Fast_HX.Vdot_ha = Vdot_a / N_circuits
            Fast_HX.DPDZ_2phase = DP_r_2phase
            Fast_HX.DPDZ_superheat = DP_r_superheat
            Fast_HX.DPDZ_subcool = DP_r_subcool
            self.HX_fast_calc = deepcopy(Fast_HX)
        
        elif hasattr(self,"HX_fast"):
            Fast_HX = deepcopy(self.HX_fast)
        
        Fast_HX.AS = AS
        Fast_HX.Pin_r = Pin_r
        Fast_HX.hin_r = hin_r
        Fast_HX.G_r = mdot_r / (pi/4 * Fast_HX.D**2) / Fast_HX.N_circuits
        DP,TTD = HX_Fast_calculate(Fast_HX)
        return DP,TTD

def HX_Fast_calculate(HX):
    def solve_superheat(Pin_r,hin_r,w_HX):
        DP_total, Q, x_out = calculate_superheat(w_HX,hin_r,Pin_r)
        if x_out < 1:
            def objective(w_superheat):
                DP_total, Q, x_out = calculate_superheat(w_HX*w_superheat,hin_r,Pin_r)
                return 1 - x_out
            w_superheat = brentq(objective,small,1,xtol=1e-2)
            DP_total, Q, x_out = calculate_superheat(w_HX*w_superheat,hin_r,Pin_r)
        else:
            w_superheat = 1.0
        return Q/mdot_r+hin_r,Pin_r+DP_total, Q, w_superheat

    def solve_subcool(Pin_r,hin_r,w_HX):
        DP_total, Q, x_out = calculate_subcool(w_HX,hin_r,Pin_r)
        if x_out > 0:
            def objective(w_subcool):
                DP_total, Q, x_out = calculate_subcool(w_HX*w_subcool,hin_r,Pin_r)
                return x_out
            w_subcool = brentq(objective,small,1,xtol=1e-2)
            DP_total, Q, x_out = calculate_subcool(w_HX*w_subcool,hin_r,Pin_r)
        else:
            w_subcool = 1.0
        return Q/mdot_r+hin_r,Pin_r+DP_total, Q, w_subcool

    def solve_2phase(Pin_r,hin_r,w_HX):
        DP_total, Q, x_out = calculate_2phase(w_HX,hin_r,Pin_r)
        if x_out > 1:
            def objective(w_2phase):
                DP_total, Q, x_out = calculate_2phase(w_HX*w_2phase,hin_r,Pin_r)
                return 1 - x_out
            
            w_2phase = brentq(objective,small,1,xtol=1e-2)
            DP_total, Q, x_out = calculate_2phase(w_HX*w_2phase,hin_r,Pin_r)
            x_out = 1
        elif x_out < 0:
            def objective(w_2phase):
                DP_total, Q, x_out = calculate_2phase(w_HX*w_2phase,hin_r,Pin_r)
                return x_out
            w_2phase = brentq(objective,small,1,xtol=1e-2)
            DP_total, Q, x_out = calculate_2phase(w_HX*w_2phase,hin_r,Pin_r)
            x_out = 0
        else:
            w_2phase = 1.0
        return Q/mdot_r + hin_r,Pin_r + DP_total, Q, w_2phase,x_out
    
    def calculate_TTD(DP_r,Pin_r,Q,hin_r):
        AS.update(CP.HmassP_INPUTS,Q/mdot_r+hin_r,Pin_r+DP_r)
        Tout_r = AS.T()
        if mode == "cooler":
            TTD = Tin_a - Tout_r
        elif mode == "heater":
            TTD = Tout_r - Tin_a
        
        return TTD, Q/mdot_r+hin_r
    
    def calculate_2phase(w_2phase,hin_r,Pin_r):
        w_2phase = float(w_2phase)
        hin_r = float(hin_r)
        Pin_r = float(Pin_r)
        '''The function is used to solve 2phase'''
        # will solve a 2 phase segment
        L = L_circuit * w_2phase
        A_r = pi * D * L
        AS.update(CP.HmassP_INPUTS,hin_r,Pin_r)
        Tin_r = AS.T()
        
        mdot_ha = Vdot_ha / V_a * w_2phase

        # dry air flow rate
        mdot_da = mdot_ha / (1 + Win_a)

        # air side total area
        A_a = A_a_total * w_2phase
                                
        #over heat thermal transfer coefficients of internal and external
        UA_o_dry = (h_a * A_a)
        UA_i = (h_r_2phase * A_r)
        
        #overall heat transfer coefficient in dry conditions
        UA_dry = 1 / (1 / UA_o_dry +1 / UA_i); 
        
        #Number of transfer units
        Ntu_dry = UA_dry / (mdot_da * cp_da)
        
        #since Cr=0, e.g. see Incropera - Fundamentals of Heat and Mass Transfer, 2007, p. 690
        epsilon_dry = 1 - exp(-Ntu_dry)  
        
        #heat transfer in dry conditions
        Q_dry = epsilon_dry * mdot_da * cp_da * (Tin_a - Tin_r)
        
        # Dry-analysis air outlet temp [K]
        Tout_a_dry = Tin_a - Q_dry / (mdot_da * cp_da)
        
        #wall outside temperature (at inlet and outlet air points, Tin_r is assumed constant)
        Tw_o_a = Tin_r + UA_dry * (1 / UA_i) * (Tin_a - Tin_r)
        Tw_o_b = Tin_r + UA_dry * (1 / UA_i) * (Tout_a_dry - Tin_r)
        
        Tout_a = Tout_a_dry
        
        if Tw_o_b > Tdp:# or True: #TODO: this is a huge approximation, no wet analysis
            #All dry, since surface at outlet dry
            f_dry = 1.0
            Q = Q_dry #[W]
            Q_sensible = Q #[W]
            hout_a = hin_a - Q / mdot_da #[J/kg_da]
        else:
            if Tw_o_a < Tdp:
                #All wet, since surface at refrigerant inlet is wet
                f_dry = 0.0
                Q_dry = 0.0
                T_ac = Tin_a # temperature at onset of wetted wall
                h_ac = hin_a # enthalpy at onset of wetted surface
            else:
                # Partially wet, partially dry
                # Based on equating heat fluxes at the wall which is at dew point UA_i*(Tw-Ti)=UA_o*(To-Tw)
                T_ac = Tdp + UA_i / UA_o_dry * (Tdp - Tin_r)
                
                # Dry effectiveness (minimum capacitance on the air side by definition)
                epsilon_dry = (Tin_a - T_ac) / (Tin_a - Tin_r)
                
                # Dry fraction found by solving epsilon=1-exp(-f_dry*Ntu) for known epsilon from above equation
                f_dry = -1.0 / Ntu_dry * log(1.0 - epsilon_dry)
                
                # Enthalpy, using air humidity at the interface between wet and dry surfaces, which is same humidity ratio as inlet
                h_ac = HAPropsSI('H','T',T_ac,'P',101325,'W',Win_a) #[J/kg_da]
                
                # Dry heat transfer
                Q_dry = mdot_da * cp_da * (Tin_a - T_ac)
            
            # intial guess
            error_per = 1
            UA_o_wet = UA_o_dry
            Q = Q_dry
            i = 1
            UA_wet = UA_dry
            b_r = cair_sat(Tin_r) * 1000

            while (error_per > 0.001) and i <= 2:                                
                Q_old = Q
                                                    
                UA_o_wet = h_a * A_a
                Ntu_o_wet = UA_o_wet / (mdot_da * cp_da)
                
                # Wet analysis overall Ntu for two-phase refrigerant
                # Minimum capacitance rate is by definition on the air side
                # Ntu_wet is the NTU if the entire two-phase region were to be wetted
                UA_wet = 1 / (cp_da / UA_o_wet + b_r / UA_i) #overall heat transfer coefficient
                Ntu_wet = UA_wet / (mdot_da)
                
                # Wet effectiveness [-]
                epsilon_wet = 1 - exp(-(1 - f_dry) * Ntu_wet)
                
                # Air saturated at refrigerant saturation temp [J/kg]
                h_s_s_o = HAPropsSI('H','T',Tin_r, 'P',101325, 'R', 1.0) #[kJ/kg_da]
                
                # Wet heat transfer [W]
                Q_wet = epsilon_wet * mdot_da * (h_ac - h_s_s_o)
                
                # Total heat transfer [W]
                Q = Q_wet + Q_dry
                
                # Air exit enthalpy [J/kg]
                hout_a = h_ac - Q_wet / mdot_da
                
                # Saturated air enthalpy at effective surface temp [J/kg_da]
                h_s_s_e = h_ac - (h_ac - hout_a) / (1 - exp(-(1 - f_dry) * Ntu_o_wet))
                
                # Effective surface temperature [K]
                T_s_e = HAPropsSI('T','H',h_s_s_e,'P',101325,'R',1.0)
                
                # Outlet dry-bulb temp [K]
                Tout_a = T_s_e + (T_ac - T_s_e) * exp(-(1 - f_dry) * Ntu_o_wet)
                                
                # error
                error_per = abs((Q - Q_old) / Q)
                i += 1
                
            #Sensible heat transfer rate [kW]
            Q_sensible = mdot_da * cp_da * (Tin_a - Tout_a)
            if Q_sensible > Q:
                Q_sensible = Q
            
        hout_r = Q/mdot_r+hin_r
        DP_total = DPDZ_2phase * L
        Pout_r = Pin_r + DP_total
        
        # correcting outlet quality with new pressure
        AS.update(CP.PQ_INPUTS,Pout_r,0.0)
        h_L = AS.hmass()
        AS.update(CP.PQ_INPUTS,Pout_r,1.0)
        h_V = AS.hmass()
        x_out = (hout_r-h_L)/(h_V-h_L)
        
        return DP_total, Q, x_out
    
    def calculate_superheat(w_1phase,hin_r,Pin_r):
        w_1phase = float(w_1phase)
        hin_r = float(hin_r)
        Pin_r = float(Pin_r)
        '''The function is used to solve superheat phase'''
        # will solve a 1 phase segment
        AS.update(CP.HmassP_INPUTS,hin_r,Pin_r)
        cp_r = AS.cpmass()
        L = L_circuit * w_1phase
        A_r = pi * D * L
        AS.update(CP.HmassP_INPUTS,hin_r,Pin_r)
        Rw = 0
        Tin_r = AS.T()

        mdot_ha = Vdot_ha / V_a * w_1phase
        
        # dry air flow rate
        mdot_da = mdot_ha / (1 + Win_a)
        
        # air side total area
        A_a = A_a_total * w_1phase
        
        # Internal UA between fluid flow and internal surface
        UA_i = h_r_superheat * A_r 

        # External dry UA between outer surface and free stream
        UA_o_dry = h_a * A_a 
        
        # overall heat transfer coefficient        
        UA_dry = 1 / (1 / (UA_i) + 1 / (UA_o_dry))

        # Min and max capacitance rates [W/K]
        Cmin = min([cp_r * mdot_r, cp_da * mdot_da])
        Cmax = max([cp_r * mdot_r, cp_da * mdot_da])
        
        # Capacitance rate ratio [-]
        C_star = Cmin / Cmax
        
        # NTU of refrigerant
        NTU_i = UA_i / (mdot_r * cp_r)
        
        # NTU of air
        NTU_o_dry = UA_o_dry / (mdot_da * cp_da)
        
        # Ntu overall [-]
        NTU_dry = UA_dry / Cmin

        #Crossflow effectiveness (e.g. see Incropera - Fundamentals of Heat and Mass Transfer, 2007, p. 662)
        if (cp_r * mdot_r) < (cp_da * mdot_da):
            epsilon_dry = 1 - exp(-C_star**(-1) * (1 - exp(-C_star * (NTU_dry))))
            #Cross flow, single phase, cmax is airside, which is unmixed
        else:
            epsilon_dry = (1 / C_star) * (1 - exp(-C_star * (1 - exp(-NTU_dry))))
            #Cross flow, single phase, cmax is refrigerant side, which is mixed

        # Dry heat transfer [W]
        Q_dry = epsilon_dry * Cmin * (Tin_a - Tin_r)

        # Dry-analysis air outlet temp [K]
        Tout_a_dry = Tin_a - Q_dry / (mdot_da * cp_da)
        
        # Dry-analysis outlet temp [K]
        Tout_r_dry = Tin_r + Q_dry / (mdot_r * cp_r)
        
        #dry analysis surface temperature at refrigerant inlet (at inlet and outlet air points)
        Tw_i_a = Tin_r + UA_dry * (1 / UA_i) * (Tin_a - Tin_r)
        Tw_i_b = Tin_r + UA_dry * (1 / UA_i) * (Tout_a_dry - Tin_r)
        Tw_i = (Tw_i_a + Tw_i_b) / 2
        
        #dry analysis surface temperature at refrigerant outlet (at inlet and outlet air points)
        Tw_o_a = Tout_r_dry + UA_dry * (1 / UA_i) * (Tin_a - Tout_r_dry)
        Tw_o_b = Tout_r_dry + UA_dry * (1 / UA_i) * (Tout_a_dry - Tout_r_dry)
        Tw_o = (Tw_o_a + Tw_o_b) / 2
                
        Tout_r = Tout_r_dry
        
        if Tw_i < Tdp:
            FullyWet = True
        else:
            FullyWet = False

        if (Tw_o < Tdp or FullyWet):# and False: #TODO: this is a huge approximation, no wet analysis
            # There is some wetting, the coil could be partially or fully wet
            Tout_r = Tin_r
            eps = 1e-5
            i = 1
            b_r = cair_sat(Tin_r) * 1000
            Q_wet = 0
            Error_Q = 100
            while ((i <= 3) or Error_Q > eps) and (i<3):
                
                # saving old value of Q_wet
                Q_wet_old = Q_wet
                
                # saturated air enthalpy at refrigerant inlet temperature
                h_s_w_i = HAPropsSI('H','T',Tin_r, 'P',101325, 'R', 1.0) #[kJ/kg_da]
                                                
                # Effective humid air mass flow ratio
                m_star = min([cp_r * mdot_r / b_r, mdot_da])/max([cp_r * mdot_r / b_r, mdot_da])
                
                # minimum effective flow rate
                mdot_min = min([cp_r * mdot_r / b_r, mdot_da])
                
                # new NTU_o_wet
                NTU_o_wet = h_a * A_a / (mdot_da * cp_da)
                
                # Wet analysis overall NTU
                if (cp_r * mdot_r > b_r * mdot_da):
                    NTU_wet = NTU_o_dry / (1 + m_star * (NTU_o_wet / NTU_i))
                else:
                    NTU_wet = NTU_o_dry / (1 + m_star * (NTU_i / NTU_o_wet))
                
                
                # crossflow effectiveness for wet analysis
                if (cp_r * mdot_r) < (b_r * mdot_da):
                    #Cross flow, single phase, cmax is airside, which is unmixed
                    epsilon_wet = 1 - exp(-m_star**(-1) * (1 - exp(-m_star * (NTU_wet))))
                else:
                    #Cross flow, single phase, cmax is refrigerant side, which is mixed
                    epsilon_wet = (1 / m_star) * (1 - exp(-m_star * (1 - exp(-NTU_wet))))
                
                # wet analysis heat transfer rate
                Q_wet = epsilon_wet * mdot_min * (hin_a - h_s_w_i)
                                
                # refrigerant outlet temperature
                Tout_r = Tin_r + Q_wet / (mdot_r * cp_r)
                
                # refrigerant outler saturated surface enthalpy
                h_s_w_o = HAPropsSI('H','T',Tout_r, 'P',101325, 'R', 1.0) #[kJ/kg_da]
                
                # Local UA* and b_r
                b_r = cair_sat((Tin_r + Tout_r) / 2) * 1000
                UA_star = 1 / (cp_da / (h_a * A_a) + b_r * (1 / (h_r_superheat * A_r) + Rw))
                
                # wet-analysis outer surface tempererature at outlet
                Tw_o = Tout_r + UA_star / (h_r_superheat * A_r) * (hin_a - h_s_w_o)

                # wet-analysis outer surface tempererature at inlet
                Tw_i = Tin_r + UA_star / (h_r_superheat * A_r) * (hin_a - h_s_w_o)
                                
                # Error in Q_wet
                Error_Q = (Q_wet - Q_wet_old) / Q_wet
                
                # increasing counter
                i += 1
                
            Q = Q_wet
                        
        else:
            # all dry, since refrigerant outlet surface temperature is dry
            Q = Q_dry
        
        # refrigerant pressure drop
        DP_total = DPDZ_superheat * L
        hout_r = hin_r + Q/(mdot_r)
        Pout_r = Pin_r + DP_total
        AS.update(CP.PQ_INPUTS,Pout_r,0.0)
        h_L = AS.hmass()
        AS.update(CP.PQ_INPUTS,Pout_r,1.0)
        h_V = AS.hmass()
        x_out = (hout_r-h_L)/(h_V-h_L)
        
        return DP_total, Q, x_out
    
    def calculate_subcool(w_1phase,hin_r,Pin_r):
        w_1phase = float(w_1phase)
        hin_r = float(hin_r)
        Pin_r = float(Pin_r)
        '''The function is used to solve subcool phase'''
        # will solve a 1 phase segment
        AS.update(CP.HmassP_INPUTS,hin_r,Pin_r)
        cp_r = AS.cpmass()
        L = L_circuit * w_1phase
        A_r = pi * D * L
        
        AS.update(CP.HmassP_INPUTS,hin_r,Pin_r)
        Tin_r = AS.T()
        
        mdot_ha = Vdot_ha / V_a * w_1phase
        
        # dry air flow rate
        mdot_da = mdot_ha / (1 + Win_a)
        
        # air side total area
        A_a = A_a_total * w_1phase
                
        # Internal UA between fluid flow and internal surface
        UA_i = h_r_subcool * A_r 
        
        # External dry UA between outer surface and free stream
        UA_o_dry = h_a * A_a 
        
        # overall heat transfer coefficient        
        UA_dry = 1 / (1 / (UA_i) + 1 / (UA_o_dry));

        # Min and max capacitance rates [W/K]
        Cmin = min([cp_r * mdot_r, cp_da * mdot_da])
        Cmax = max([cp_r * mdot_r, cp_da * mdot_da])
        
        # Capacitance rate ratio [-]
        C_star = Cmin / Cmax

        # NTU of refrigerant
        NTU_i = UA_i / (mdot_r * cp_r)
        
        # NTU of air
        NTU_o_dry = UA_o_dry / (mdot_da * cp_da)
        
        # Ntu overall [-]
        NTU_dry = UA_dry / Cmin
        
        #Crossflow effectiveness (e.g. see Incropera - Fundamentals of Heat and Mass Transfer, 2007, p. 662)
        if (cp_r * mdot_r) < (cp_da * mdot_da):
            epsilon_dry = 1 - exp(-C_star**(-1) * (1 - exp(-C_star * (NTU_dry))))
            #Cross flow, single phase, cmax is airside, which is unmixed
        else:
            epsilon_dry = (1 / C_star) * (1 - exp(-C_star * (1 - exp(-NTU_dry))))
            #Cross flow, single phase, cmax is refrigerant side, which is mixed

        # Dry heat transfer [W]
        Q_dry = epsilon_dry * Cmin * (Tin_a - Tin_r)
        
        # Dry-analysis air outlet temp [K]
        Tout_a_dry = Tin_a - Q_dry / (mdot_da * cp_da)
        
        # Dry-analysis outlet temp [K]
        Tout_r_dry = Tin_r + Q_dry / (mdot_r * cp_r)
                
        #dry analysis surface temperature at refrigerant inlet (at inlet and outlet air points)
        Tw_i_a = Tin_r + UA_dry * (1 / UA_i) * (Tin_a - Tin_r)
        Tw_i_b = Tin_r + UA_dry * (1 / UA_i) * (Tout_a_dry - Tin_r)
        Tw_i = (Tw_i_a + Tw_i_b) / 2
        
        #dry analysis surface temperature at refrigerant outlet (at inlet and outlet air points)
        Tw_o_a = Tout_r_dry + UA_dry * (1 / UA_i) * (Tin_a - Tout_r_dry)
        Tw_o_b = Tout_r_dry + UA_dry * (1 / UA_i) * (Tout_a_dry - Tout_r_dry)
        Tw_o = (Tw_o_a + Tw_o_b) / 2
                                
        Tout_r = Tout_r_dry
        
        if Tw_i < Tdp:
            FullyWet = True
        else:
            FullyWet = False

        if Tw_o < Tdp or FullyWet:
            # There is some wetting, the coil could be partially or fully wet
            Tout_r = Tin_r
            eps = 1e-5
            i = 1
            b_r = cair_sat(Tin_r) * 1000
            Q_wet = 0
            Error_Q = 100
            while ((i <= 3) or Error_Q > eps) and (i<3):
                
                # saving old value of Q_wet
                Q_wet_old = Q_wet
                
                # saturated air enthalpy at refrigerant inlet temperature
                h_s_w_i = HAPropsSI('H','T',Tin_r, 'P',101325, 'R', 1.0) #[kJ/kg_da]
                                                
                # Effective humid air mass flow ratio
                m_star = min([cp_r * mdot_r / b_r, mdot_da])/max([cp_r * mdot_r / b_r, mdot_da])
                
                # minimum effective flow rate
                mdot_min = min([cp_r * mdot_r / b_r, mdot_da])
                
                # new NTU_o_wet
                NTU_o_wet = h_a * A_a / (mdot_da * cp_da)
                
                # Wet analysis overall NTU
                if (cp_r * mdot_r > b_r * mdot_da):
                    NTU_wet = NTU_o_dry / (1 + m_star * (NTU_o_wet / NTU_i))
                else:
                    NTU_wet = NTU_o_dry / (1 + m_star * (NTU_i / NTU_o_wet))
                                
                # crossflow effectiveness for wet analysis
                if (cp_r * mdot_r) < (b_r * mdot_da):
                    #Cross flow, single phase, cmax is airside, which is unmixed
                    epsilon_wet = 1 - exp(-m_star**(-1) * (1 - exp(-m_star * (NTU_wet))))
                else:
                    #Cross flow, single phase, cmax is refrigerant side, which is mixed
                    epsilon_wet = (1 / m_star) * (1 - exp(-m_star * (1 - exp(-NTU_wet))))
                
                # wet analysis heat transfer rate
                Q_wet = epsilon_wet * mdot_min * (hin_a - h_s_w_i)
                                
                # refrigerant outlet temperature
                Tout_r = Tin_r + Q_wet / (mdot_r * cp_r)
                
                # refrigerant outler saturated surface enthalpy
                h_s_w_o = HAPropsSI('H','T',Tout_r, 'P',101325, 'R', 1.0) #[kJ/kg_da]
                
                # Local UA* and b_r
                b_r = cair_sat((Tin_r + Tout_r) / 2) * 1000
                UA_star = 1 / (cp_da / (h_a * A_a) + b_r * (1 / (h_r_subcool * A_r)))
                
                # wet-analysis outer surface tempererature at outlet
                Tw_o = Tout_r + UA_star / (h_r_subcool * A_r) * (hin_a - h_s_w_o)

                # wet-analysis outer surface tempererature at inlet
                Tw_i = Tin_r + UA_star / (h_r_subcool * A_r) * (hin_a - h_s_w_o)
                                
                # Error in Q_wet
                Error_Q = (Q_wet - Q_wet_old) / Q_wet
                
                # increasing counter
                i += 1
                        
            Q = Q_wet            
            
        else:
            # all dry, since refrigerant outlet surface temperature is dry
            Q = Q_dry
        
        # refrigerant pressure drop
        DP_total = DPDZ_subcool * L
        hout_r = hin_r + Q/(mdot_r)
        Pout_r = Pin_r + DP_total
        AS.update(CP.PQ_INPUTS,Pout_r,0.0)
        h_L = AS.hmass()
        AS.update(CP.PQ_INPUTS,Pout_r,1.0)
        h_V = AS.hmass()
        x_out = (hout_r-h_L)/(h_V-h_L)
        return DP_total, Q, x_out

    # Solver
    small = finfo(float).eps
    AS = HX.AS
    h_a = HX.h_a
    A_a_total = HX.A_a_total
    h_r_2phase = HX.h_r_2phase
    h_r_superheat = HX.h_r_superheat
    h_r_subcool = HX.h_r_subcool
    D = HX.D
    L_circuit = HX.L_circuit
    Pin_r = HX.Pin_r
    hin_r = HX.hin_r
    Tin_a = HX.Tin_a
    Win_a = HX.Win_a
    mdot_r = HX.G_r * pi / 4 * D * D
    if hasattr(HX,"Vdot_ha"):
        Vdot_ha = HX.Vdot_ha
    else:
        v_spec = HAPropsSI("V","T",HX.Tin_a,"W",HX.Win_a,"P",HX.Pin_a)
        Vdot_ha = HX.mdot_da*v_spec

    DPDZ_2phase = HX.DPDZ_2phase
    DPDZ_superheat = HX.DPDZ_superheat
    DPDZ_subcool = HX.DPDZ_subcool
    
    AS.update(CP.HmassP_INPUTS,hin_r,Pin_r)
    Tin_r = AS.T()
    if Tin_r > Tin_a:
        mode = "heater"
    else:
        mode = "cooler"

    V_a = HAPropsSI('V','T',Tin_a,'P',101325,'W',Win_a)
    hin_a = HAPropsSI('H','T',Tin_a,'P',101325,'W',Win_a)
    cp_da = (HAPropsSI('H','T',Tin_a+0.0001,'P',101325,'W',Win_a)-hin_a)/0.0001
    Tdp = HAPropsSI('D','T',Tin_a,'P',101325,'W',Win_a)
    
    AS.update(CP.PQ_INPUTS,Pin_r,1.0)
    hV = AS.hmass()
    AS.update(CP.PQ_INPUTS,Pin_r,0.0)
    hL = AS.hmass()
    xin_r = (hin_r - hL) / (hV - hL)
    
    if xin_r < 0 or (xin_r == 0 and mode == "heater"):
        hout_r_subcool,Pout_r_subcool, Q_subcool, w_subcool = solve_subcool(Pin_r,hin_r,1.0)
        if w_subcool == 1.0:
            DP = Pout_r_subcool - Pin_r
            return DP,calculate_TTD(DP,Pin_r,Q_subcool,hin_r)
        else:
            hout_r_2phase,Pout_r_2phase, Q_2phase,w_2phase,xout_r = solve_2phase(Pout_r_subcool,hout_r_subcool,1-w_subcool)
            if w_2phase == 1.0:
                DP = Pout_r_2phase - Pin_r
                return DP,calculate_TTD(DP,Pin_r,Q_subcool+Q_2phase,hin_r)
            else:
                hout_r_superheat,Pout_r_superheat, Q_superheat,w_superheat = solve_superheat(Pout_r_2phase,hout_r_2phase,(1-w_subcool)*(1-w_2phase))
                DP = Pout_r_superheat - Pin_r
                return DP,calculate_TTD(DP,Pin_r,Q_subcool+Q_2phase+Q_superheat,hin_r)
    
    elif 0 < xin_r < 1 or (xin_r == 0 and mode == "cooler") or (xin_r == 1 and mode == "heater"):
        hout_r_2phase,Pout_r_2phase, Q_2phase,w_2phase, xout_r = solve_2phase(Pin_r,hin_r,1.0)
        if w_2phase == 1.0:
            DP = Pout_r_2phase - Pin_r
            return DP,calculate_TTD(DP,Pin_r,Q_2phase,hin_r)
        else:
            if xout_r == 1:
                hout_r_superheat,Pout_r_superheat, Q_superheat,w_superheat = solve_superheat(Pout_r_2phase,hout_r_2phase,1-w_2phase)
                DP = Pout_r_superheat - Pin_r
                return DP,calculate_TTD(DP,Pin_r,Q_2phase+Q_superheat,hin_r)
            elif xout_r == 0:
                hout_r_subcool,Pout_r_subcool, Q_subcool,w_subcool = solve_subcool(Pout_r_2phase,hout_r_2phase,1-w_2phase)
                DP = Pout_r_subcool - Pin_r
                return DP,calculate_TTD(DP,Pin_r,Q_2phase+Q_subcool,hin_r)
            
    elif xin_r > 1 or (xin_r == 1 and mode == "cooler"):
        hout_r_superheat,Pout_r_superheat, Q_superheat, w_superheat = solve_superheat(Pin_r,hin_r,1.0)
        if w_superheat == 1.0:
            DP = Pout_r_superheat - Pin_r
            return DP,calculate_TTD(DP,Pin_r,Q_superheat,hin_r)
        else:
            hout_r_2phase,Pout_r_2phase, Q_2phase,w_2phase,xout_r = solve_2phase(Pout_r_superheat,hout_r_superheat,1-w_superheat)
            if w_2phase == 1.0:
                DP = Pout_r_2phase - Pin_r
                return DP,calculate_TTD(DP,Pin_r,Q_superheat+Q_2phase,hin_r)
            else:
                hout_r_subcool,Pout_r_subcool, Q_subcool,w_subcool = solve_subcool(Pout_r_2phase,hout_r_2phase,(1 - w_2phase)*(1-w_superheat))
                DP = Pout_r_subcool - Pin_r
                return DP,calculate_TTD(DP,Pin_r,Q_superheat+Q_2phase+Q_subcool,hin_r)
    
if __name__ == '__main__':
    def fun1():
        HX = ValuesClass()
        AS = CP.AbstractState("HEOS","R410A")
        HX.AS = AS
        HX.h_a = 75.282 * 0.82751
        HX.A_a_total = 48.584/3
        HX.h_r_2phase = 2732.7
        HX.h_r_superheat = 928.6
        HX.h_r_subcool = 1384
        HX.D = 0.00849
        HX.L_circuit = 13.512
        HX.Pin_r = 2.9559e+06
        HX.hin_r = 4.7141e+05
        HX.Tin_a = 308.15
        HX.Win_a = 0.01
        HX.G_r = 0.064018 / (pi/4 * HX.D**2) / 3
        HX.Vdot_ha = 1.7934 / 3
        HX.DPDZ_2phase = -922
        HX.DPDZ_superheat = -1421
        HX.DPDZ_subcool = -481
        import time
        T1 = time.time()
        times = 1
        for i in range(times):
            DP,TTD = HX_Fast_calculate(HX)
        print("time:",(time.time()-T1)/times,"s")
        print(DP,TTD)

    def fun2(): # condenser
        AS = CP.AbstractState("HEOS","R410A")
        mdot_r = .059002785838072704
        Pin_r = 2909278.0379495346
        hin_r = 473678.5129476448
        
        from GUI_functions import read_Fin_tube
        Fintube = read_Fin_tube(r"E:\UNIDO\Python\20210117154634.hx")[1]
        import time
        T1 = time.time()
        times = 1
        Fintube_fast = Fintube_fastClass()
        Fintube_fast.HX_define_fintube(Fintube,AS)
        for i in range(times):
            DP,TTD = Fintube_fast.solve(mdot_r,Pin_r,hin_r)
        print("time:",(time.time()-T1)/times,"s")
        print(DP,TTD)
    
    def fun3(): #evaporator
        AS = CP.AbstractState("HEOS","R410A")
        mdot_r = 0.063804
        Pin_r = 1.0581e+06
        hin_r = 2.6787e+05

        from GUI_functions import read_Fin_tube
        Fintube = read_Fin_tube(r"E:\UNIDO\Python\20210117154452.hx")[1]
        import time
        T1 = time.time()
        times = 10
        Fintube_fast = Fintube_fastClass()
        Fintube_fast.HX_define_fintube(Fintube,AS)
        for i in range(times):
            DP,TTD = Fintube_fast.solve(mdot_r,Pin_r,hin_r)
        print("time:",(time.time()-T1)/times,"s")
        print(DP,TTD)

    def fun4(): # condenser
        AS = CP.AbstractState("HEOS","R410A")
        mdot_r = 0.06628014507177625
        Pin_r = 2449579.884429206
        hin_r = 462885.02232889546
        
        from GUI_functions import read_Microchannel
        Microchannel = read_Microchannel(r"E:\UNIDO\Python\20210424012304.hx")[1]
        import time
        T1 = time.time()
        times = 1
        Microchannel_fast = Microchannel_fastClass()
        Microchannel_fast.HX_define_microchannel(Microchannel,AS)
        for i in range(times):
            DP,TTD = Microchannel_fast.solve(mdot_r,Pin_r,hin_r)
        print("time:",(time.time()-T1)/times,"s")
        print(DP,TTD)
    
    def fun5(): #evaporator
        AS = CP.AbstractState("HEOS","R410A")
        mdot_r = 0.063804
        Pin_r = 1.0581e+06
        hin_r = 2.6787e+05
        
        from GUI_functions import read_Microchannel
        Microchannel = read_Microchannel(r"E:\UNIDO\Python\20210424012304.hx")[1]
        
        import time
        T1 = time.time()
        times = 1
        Microchannel_fast = Microchannel_fastClass()
        Microchannel_fast.HX_define_microchannel(Microchannel,AS)
        for i in range(times):
            DP,TTD = Microchannel_fast.solve(mdot_r,Pin_r,hin_r)
        print("time:",(time.time()-T1)/times,"s")
        print(DP,TTD)
        
    fun4()