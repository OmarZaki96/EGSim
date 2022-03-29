# -*- coding: utf-8 -*-
"""
Created on Tue Jan 12 21:55:03 2021

@author: OmarZaki
"""
from backend.Cycle import CycleClass
from CoolProp.CoolProp import HAPropsSI

def define_single(compressor,condenser,evaporator,liquid_line,suction_line,
                 discharge_line, twophase_line, options,update_residuals,capillary=None):
    try:
        if compressor.Comp_model == "physics":
            Compressor_Type = 'Physics'
        elif compressor.Comp_model == "10coefficients":
            Compressor_Type = 'AHRI'
        elif compressor.Comp_model == "map":
            Compressor_Type = "AHRI-map"
    
        if condenser.type == "Fintube":
            Condenser_Type = "Fin-tube"
        elif condenser.type == "Microchannel":
            Condenser_Type = "MicroChannel"
        
        if evaporator.type == "Fintube":
            Evaporator_Type = "Fin-tube"
        elif evaporator.type == "Microchannel":
            Evaporator_Type = "MicroChannel"
        
        if options['Expansion_Device_Type'] == "TXV":
            Expansion_Device_Type = "TXV"
            sh_location = options['sh_location']
            sh_value = options['sh_value']
        elif options['Expansion_Device_Type'] == "capillary":
            Expansion_Device_Type = "Capillary"
            sh_location = 0.0
            sh_value = 0.0
        
        if options['Second_Cond'] == "subcooling":
            Second_Cond = "Subcooling"
            cond2_value = options['sc_value']
        elif options['Second_Cond'] == "charge":
            Second_Cond = "Charge"
            cond2_value = options['charge_value']
        
        Cycle = CycleClass()
        params = {'Compressor_Type': Compressor_Type,
                      'Condenser_Type': Condenser_Type,
                      'Evaporator_Type': Evaporator_Type,
                      'Expansion_Device_Type': Expansion_Device_Type,
                      'Superheat_Type': sh_location,
                      'SH_value': sh_value,
                      'Second_Cond': Second_Cond,
                      'SC_value': cond2_value,
                      'Charge_value': cond2_value,
                      'Backend': options['Backend'],
                      'Ref': options['Ref'],
                      'Mode': options['Mode'],
                      'Tevap_init_manual': options['Tevap_init_manual'],
                      'Tevap_init': options['Tevap_init'],
                      'Tcond_init_manual': options['Tcond_init_manual'],
                      'Tcond_init': options['Tcond_init'],
                      'energy_tol': options['energy_tol'],
                      'pressure_tol': options['pressure_tol'],
                      'mass_flowrate_tol': options['mass_flowrate_tol'],
                      'mass_tol': options['mass_tol'],
                      'update_residuals': update_residuals,
                      'max_n_iterations': options['max_n_iterations'],
                      'Accum_charge_per': options['Accum_charge_per'],
                      }
        Cycle.Update(**params)
        
        if "Test_cond" in options.keys():
            Cycle.Test_cond = options["Test_cond"]
            if options["Test_cond"] == "Custom":
                Tin_a_evap = evaporator.Air_T
                Win_a_evap = HAPropsSI("W","T",evaporator.Air_T,"P",evaporator.Air_P,"R",evaporator.Air_RH)
                Tin_a_cond = condenser.Air_T
                Win_a_cond = HAPropsSI("W","T",condenser.Air_T,"P",condenser.Air_P,"R",condenser.Air_RH)        
    
            elif options["Test_cond"] == "T1":
                Tin_a_evap = 27 + 273.15
                Win_a_evap = HAPropsSI("W","T", 27 + 273.15,"P",evaporator.Air_P,"B", 19 + 273.15)
                Tin_a_cond = 35 + 273.15
                Win_a_cond = HAPropsSI("W","T", 35 + 273.15,"P",condenser.Air_P,"B", 24 + 273.15)
    
            elif options["Test_cond"] == "T2":
                Tin_a_evap = 21 + 273.15
                Win_a_evap = HAPropsSI("W","T", 21 + 273.15,"P",evaporator.Air_P,"B", 15 + 273.15)
                Tin_a_cond = 27 + 273.15
                Win_a_cond = HAPropsSI("W","T", 27 + 273.15,"P",condenser.Air_P,"B", 19 + 273.15)        
    
            elif options["Test_cond"] == "T3":
                Tin_a_evap = 29 + 273.15
                Win_a_evap = HAPropsSI("W","T", 29 + 273.15,"P",evaporator.Air_P,"B", 19 + 273.15)
                Tin_a_cond = 46 + 273.15
                Win_a_cond = HAPropsSI("W","T", 46 + 273.15,"P",condenser.Air_P,"B", 24 + 273.15)        
    
            elif options["Test_cond"] == "H1":
                Tin_a_evap = 7 + 273.15
                Win_a_evap = HAPropsSI("W","T", 7 + 273.15,"P",evaporator.Air_P,"B",6 + 273.15)
                Tin_a_cond = 20 + 273.15
                Win_a_cond = HAPropsSI("W","T",20 + 273.15,"P",evaporator.Air_P,"B",15 + 273.15)
    
            elif options["Test_cond"] == "H2":
                Tin_a_evap = 2 + 273.15
                Win_a_evap = HAPropsSI("W","T", 2 + 273.15,"P",evaporator.Air_P,"B",1 + 273.15)
                Tin_a_cond = 20 + 273.15
                Win_a_cond = HAPropsSI("W","T",20 + 273.15,"P",evaporator.Air_P,"B",15 + 273.15)
    
            elif options["Test_cond"] == "H3":
                Tin_a_evap = -7 + 273.15
                Win_a_evap = HAPropsSI("W","T", -7 + 273.15,"P",evaporator.Air_P,"B",-8 + 273.15)
                Tin_a_cond = 20 + 273.15
                Win_a_cond = HAPropsSI("W","T",20 + 273.15,"P",evaporator.Air_P,"B",15 + 273.15)
        
        else:
            Cycle.Test_cond = "Custom"
            Tin_a_evap = evaporator.Air_T
            Win_a_evap = HAPropsSI("W","T",evaporator.Air_T,"P",evaporator.Air_P,"R",evaporator.Air_RH)
            Tin_a_cond = condenser.Air_T
            Win_a_cond = HAPropsSI("W","T",condenser.Air_T,"P",condenser.Air_P,"R",condenser.Air_RH)        
        
        # Compressor definition
        if Compressor_Type == "AHRI":
            Cycle.Compressor.name = compressor.Comp_name
            Cycle.Compressor.M = compressor.M
            Cycle.Compressor.P = compressor.P
            Cycle.Compressor.Speeds = compressor.speeds
            Cycle.Compressor.fp = compressor.Comp_fp
            Cycle.Compressor.Vdot_ratio_P = compressor.Comp_ratio_P
            Cycle.Compressor.Vdot_ratio_M = compressor.Comp_ratio_M
            Cycle.Compressor.Displacement = compressor.Comp_vol
            if compressor.std_type == 0:
                Cycle.Compressor.SH_Ref = compressor.std_sh
            else:
                Cycle.Compressor.Suction_Ref = compressor.std_suction
                
            Cycle.Compressor.act_speed = compressor.Comp_speed
            Cycle.Compressor.Unit_system = compressor.unit_system
            Cycle.Compressor.Elec_eff = compressor.Comp_elec_eff
            Cycle.Compressor.F_factor = compressor.Comp_AHRI_F_value
    
        elif Compressor_Type == "Physics":
            Cycle.Compressor.name = compressor.Comp_name
            Cycle.Compressor.fp = compressor.Comp_fp
            Cycle.Compressor.Vdot_ratio_P = compressor.Comp_ratio_P
            Cycle.Compressor.Vdot_ratio_M = compressor.Comp_ratio_M
            Cycle.Compressor.Displacement = compressor.Comp_vol
            Cycle.Compressor.act_speed = compressor.Comp_speed
            Cycle.Compressor.Elec_eff = compressor.Comp_elec_eff
            Cycle.Compressor.isen_eff = compressor.isentropic_exp
            Cycle.Compressor.vol_eff = compressor.vol_exp
            Cycle.Compressor.F_factor = compressor.F_factor
            Cycle.Compressor.SH_type = compressor.SH_type
            if compressor.SH_type == 0:
                Cycle.Compressor.SH_Ref = compressor.SH_Ref
            elif compressor.SH_type == 1:
                Cycle.Compressor.Suction_Ref = compressor.Suction_Ref
            
        elif Compressor_Type == "AHRI-map":
            Cycle.Compressor.name = compressor.Comp_name
            Cycle.Compressor.M = compressor.map_data.M_coeffs
            Cycle.Compressor.P = compressor.map_data.P_coeffs
            Cycle.Compressor.Speeds = compressor.map_data.Speeds
            Cycle.Compressor.fp = compressor.Comp_fp
            Cycle.Compressor.Vdot_ratio_P = compressor.Comp_ratio_P
            Cycle.Compressor.Vdot_ratio_M = compressor.Comp_ratio_M
            Cycle.Compressor.Displacement = compressor.Comp_vol
            if compressor.map_data.std_type == 0:
                Cycle.Compressor.SH_Ref = compressor.map_data.std_sh
            else:
                Cycle.Compressor.Suction_Ref = compressor.map_data.std_suction
                
            Cycle.Compressor.act_speed = compressor.Comp_speed
            Cycle.Compressor.Unit_system = compressor.unit_system
            Cycle.Compressor.Elec_eff = compressor.Comp_elec_eff
            Cycle.Compressor.F_factor = compressor.map_data.F_value
        
        # Condenser definition
        if Condenser_Type == "Fin-tube":
    
            if condenser.Air_flow_direction in ["Sub Heat Exchanger First","Sub Heat Exchanger Last"]:
                number_of_circuits = condenser.N_series_Circuits + 1
            elif condenser.Air_flow_direction in ["Parallel","Series-Parallel","Series-Counter"]:
                number_of_circuits = condenser.N_series_Circuits
            Cycle.Condenser.name = condenser.name
            if condenser.Accurate == "CoolProp":
                Cycle.Condenser.Accurate = True
            elif condenser.Accurate == "Psychrolib":
                Cycle.Condenser.Accurate = False
            Cycle.Condenser.create_circuits(number_of_circuits)
            for i in range(number_of_circuits):
                N = condenser.circuits[i].N_Circuits
                connection = [i,i+1,i,1.0,N]
                Cycle.Condenser.connect(*tuple(connection))
            Cycle.Condenser.Tin_a = Tin_a_cond
            Cycle.Condenser.Pin_a = condenser.Air_P
            Cycle.Condenser.Win_a = Win_a_cond
            Cycle.Condenser.Fan_add_DP = options['Condenser_Fan_add_DP']
            if condenser.Air_flow_direction == "Parallel":
                Cycle.Condenser.Air_sequence = 'parallel'
                Cycle.Condenser.Air_distribution = condenser.Air_Distribution
            elif condenser.Air_flow_direction == "Series-Parallel":
                Cycle.Condenser.Air_sequence = 'series_parallel'
            elif condenser.Air_flow_direction == "Series-Counter":
                Cycle.Condenser.Air_sequence = 'series_counter'
            elif condenser.Air_flow_direction == "Sub Heat Exchanger First":
                Cycle.Condenser.Air_sequence = 'sub_HX_first'
                Cycle.Condenser.Air_distribution = condenser.Air_Distribution
            elif condenser.Air_flow_direction == "Sub Heat Exchanger Last":
                Cycle.Condenser.Air_sequence = 'sub_HX_last'
                Cycle.Condenser.Air_distribution = condenser.Air_Distribution
            if condenser.model == "Segment by Segment":
                Cycle.Condenser.model = 'segment'
                N_segments = condenser.N_segments
            elif condenser.model == "Phase by Phase":
                Cycle.Condenser.model = 'phase'
                N_segments = 1.0
            Cycle.Condenser.Q_error_tol = condenser.HX_Q_tol
            Cycle.Condenser.max_iter_per_circuit = condenser.N_iterations
            if condenser.Fan_model == "Fan Efficiency Model":
                Cycle.Condenser.Fan.model = 'efficiency'
                Cycle.Condenser.Fan.efficiency = condenser.Fan_model_efficiency_exp
            elif condenser.Fan_model == "Fan Curve Model":
                Cycle.Condenser.Fan.model = 'curve'
                Cycle.Condenser.Fan.power_curve = condenser.Fan_model_P_exp
                Cycle.Condenser.Fan.DP_curve = condenser.Fan_model_DP_exp
            elif condenser.Fan_model == "Fan Power Model":
                Cycle.Condenser.Fan.model = 'power'
                Cycle.Condenser.Fan.power_exp = condenser.Fan_model_power_exp
                
            Cycle.Condenser.Fan.Fan_position = 'after'
            
            if hasattr(condenser,"Vdot_ha"):
                Cycle.Condenser.Vdot_ha = condenser.Vdot_ha
            else:
                v_spec = HAPropsSI("V","T",Cycle.Condenser.Tin_a,"W",Cycle.Condenser.Win_a,"P",Cycle.Condenser.Pin_a)
                Cycle.Condenser.Vdot_ha = condenser.mdot_da * v_spec
            
            if condenser.solver == "Mass flow rate solver":
                Cycle.Condenser.Solver = 'mdot'
            elif condenser.solver == "Pressure drop solver":
                Cycle.Condenser.Solver = 'dp'            
            
            for i in range(number_of_circuits):
                Cycle.Condenser.Circuits[i].Geometry.Ntubes_per_bank_per_subcircuit = condenser.circuits[i].N_tube_per_bank
                Cycle.Condenser.Circuits[i].Geometry.Nbank = condenser.circuits[i].N_bank
                Cycle.Condenser.Circuits[i].Geometry.OD = condenser.circuits[i].OD
                Cycle.Condenser.Circuits[i].Geometry.Ltube = condenser.circuits[i].Ltube
                if condenser.circuits[i].Tube_type == "Smooth":
                    Cycle.Condenser.Circuits[i].Geometry.Tubes_type = "Smooth"
                    Cycle.Condenser.Circuits[i].Geometry.ID = condenser.circuits[i].ID
                    Cycle.Condenser.Circuits[i].Geometry.e_D = condenser.circuits[i].e_D
                elif condenser.circuits[i].Tube_type == "Microfin":
                    Cycle.Condenser.Circuits[i].Geometry.Tubes_type = "Microfin"
                    Cycle.Condenser.Circuits[i].Geometry.t = condenser.circuits[i].Tube_t
                    Cycle.Condenser.Circuits[i].Geometry.beta = condenser.circuits[i].Tube_beta
                    Cycle.Condenser.Circuits[i].Geometry.e = condenser.circuits[i].Tube_e
                    Cycle.Condenser.Circuits[i].Geometry.d = condenser.circuits[i].Tube_d
                    Cycle.Condenser.Circuits[i].Geometry.gama = condenser.circuits[i].Tube_gamma
                    Cycle.Condenser.Circuits[i].Geometry.n = condenser.circuits[i].Tube_n
                Cycle.Condenser.Circuits[i].Geometry.Staggering = condenser.circuits[i].Staggering
                Cycle.Condenser.Circuits[i].Geometry.Pl = condenser.circuits[i].Pl
                Cycle.Condenser.Circuits[i].Geometry.Pt = condenser.circuits[i].Pt
                
                N_tube_per_bank = condenser.circuits[i].N_tube_per_bank
                N_bank = condenser.circuits[i].N_bank
                Ntubes = N_tube_per_bank * N_bank
                if condenser.circuits[i].circuitry == 0:
                    connections = []
                    for k in reversed(range(int(N_bank))):
                        start = k * N_tube_per_bank + 1
                        end = (k + 1) * N_tube_per_bank + 1
                        if (N_bank - k)%2==1:
                            connections += range(start,end)
                        else:
                            connections += reversed(range(start,end))
                    condenser.circuits[i].Connections = connections
                
                elif condenser.circuits[i].circuitry == 1: #parallel flow
                    connections = []
                    for k in range(int(N_bank)):
                        start = k * N_tube_per_bank + 1
                        end = (k + 1) * N_tube_per_bank + 1
                        if k%2==0:
                            connections += range(start,end)
                        else:
                            connections += reversed(range(start,end))
                    condenser.circuits[i].Connections = connections
                    
                Cycle.Condenser.Circuits[i].Geometry.Connections = condenser.circuits[i].Connections
                Cycle.Condenser.Circuits[i].Geometry.FarBendRadius = 0.01
                Cycle.Condenser.Circuits[i].Geometry.FPI = condenser.circuits[i].Fin_FPI
                Cycle.Condenser.Circuits[i].Geometry.Fin_t = condenser.circuits[i].Fin_t
                Cycle.Condenser.Circuits[i].Geometry.FinType = condenser.circuits[i].Fin_type
                if condenser.circuits[i].Fin_type == "Wavy":
                    Cycle.Condenser.Circuits[i].Geometry.Fin_Pd = condenser.circuits[i].Fin_pd
                    Cycle.Condenser.Circuits[i].Geometry.Fin_xf = condenser.circuits[i].Fin_xf
                elif condenser.circuits[i].Fin_type == "WavyLouvered":
                    Cycle.Condenser.Circuits[i].Geometry.Fin_Pd = condenser.circuits[i].Fin_pd
                    Cycle.Condenser.Circuits[i].Geometry.Fin_xf = condenser.circuits[i].Fin_xf
                elif condenser.circuits[i].Fin_type == "Louvered":
                    Cycle.Condenser.Circuits[i].Geometry.Fin_Lp = condenser.circuits[i].Fin_Lp
                    Cycle.Condenser.Circuits[i].Geometry.Fin_Lh = condenser.circuits[i].Fin_Lh
                elif condenser.circuits[i].Fin_type == "Slit":
                    Cycle.Condenser.Circuits[i].Geometry.Fin_Sh = condenser.circuits[i].Fin_Sh
                    Cycle.Condenser.Circuits[i].Geometry.Fin_Ss = condenser.circuits[i].Fin_Ss
                    Cycle.Condenser.Circuits[i].Geometry.Fin_Sn = condenser.circuits[i].Fin_Sn
                    
                Cycle.Condenser.Circuits[i].Thermal.Nsegments = N_segments
                Cycle.Condenser.Circuits[i].Thermal.kw = condenser.circuits[i].Tube_k
                Cycle.Condenser.Circuits[i].Thermal.k_fin = condenser.circuits[i].Fin_k
                Cycle.Condenser.Circuits[i].Thermal.FinsOnce = True
                Cycle.Condenser.Circuits[i].Thermal.HTC_superheat_Corr = condenser.circuits[i].superheat_HTC_corr
                Cycle.Condenser.Circuits[i].Thermal.HTC_subcool_Corr = condenser.circuits[i].subcool_HTC_corr
                Cycle.Condenser.Circuits[i].Thermal.DP_superheat_Corr = condenser.circuits[i].superheat_DP_corr
                Cycle.Condenser.Circuits[i].Thermal.DP_subcool_Corr = condenser.circuits[i].subcool_DP_corr
                Cycle.Condenser.Circuits[i].Thermal.HTC_2phase_Corr = condenser.circuits[i]._2phase_HTC_corr
                Cycle.Condenser.Circuits[i].Thermal.DP_2phase_Corr = condenser.circuits[i]._2phase_DP_corr
                Cycle.Condenser.Circuits[i].Thermal.DP_Accel_Corr = condenser.circuits[i]._2phase_charge_corr
                Cycle.Condenser.Circuits[i].Thermal.rho_2phase_Corr = condenser.circuits[i]._2phase_charge_corr
                Cycle.Condenser.Circuits[i].Thermal.Air_dry_Corr = condenser.circuits[i].air_dry_HTC_corr
                Cycle.Condenser.Circuits[i].Thermal.Air_wet_Corr = condenser.circuits[i].air_wet_HTC_corr
                Cycle.Condenser.Circuits[i].Thermal.h_r_superheat_tuning = condenser.circuits[i].superheat_HTC_correction
                Cycle.Condenser.Circuits[i].Thermal.h_r_subcooling_tuning = condenser.circuits[i].subcool_HTC_correction
                Cycle.Condenser.Circuits[i].Thermal.h_r_2phase_tuning = condenser.circuits[i]._2phase_HTC_correction
                Cycle.Condenser.Circuits[i].Thermal.h_a_dry_tuning = condenser.circuits[i].air_dry_HTC_correction
                Cycle.Condenser.Circuits[i].Thermal.h_a_wet_tuning = condenser.circuits[i].air_wet_HTC_correction
                Cycle.Condenser.Circuits[i].Thermal.DP_a_dry_tuning = condenser.circuits[i].air_dry_DP_correction
                Cycle.Condenser.Circuits[i].Thermal.DP_a_wet_tuning = condenser.circuits[i].air_wet_DP_correction
                Cycle.Condenser.Circuits[i].Thermal.DP_r_superheat_tuning = condenser.circuits[i].superheat_DP_correction
                Cycle.Condenser.Circuits[i].Thermal.DP_r_subcooling_tuning = condenser.circuits[i].subcool_DP_correction
                Cycle.Condenser.Circuits[i].Thermal.DP_r_2phase_tuning = condenser.circuits[i]._2phase_DP_correction
                if hasattr(condenser.circuits[i],'h_a_wet_on'):
                    Cycle.Condenser.Circuits[i].Thermal.h_a_wet_on = condenser.circuits[i].h_a_wet_on
                else:
                    Cycle.Condenser.Circuits[i].Thermal.h_a_wet_on = False
                if hasattr(condenser.circuits[i],'DP_a_wet_on'):
                    Cycle.Condenser.Circuits[i].Thermal.DP_a_wet_on = condenser.circuits[i].DP_a_wet_on
                else:
                    Cycle.Condenser.Circuits[i].Thermal.DP_a_wet_on = False
    
                if hasattr(condenser.circuits[i],'sub_HX_values'):
                    Cycle.Condenser.Circuits[i].Geometry.Sub_HX_matrix = condenser.circuits[i].sub_HX_values
                
        elif Condenser_Type == "MicroChannel":
            Cycle.Condenser.name = condenser.name
            if condenser.Accurate == "CoolProp":
                Cycle.Condenser.Accurate = True
            elif condenser.Accurate == "Psychrolib":
                Cycle.Condenser.Accurate = False
            Cycle.Condenser.Tin_a = Tin_a_cond
            Cycle.Condenser.Pin_a = condenser.Air_P
            Cycle.Condenser.Win_a = Win_a_cond
            Cycle.Condenser.Fan_add_DP = options['Condenser_Fan_add_DP']
            if condenser.model == "Segment by Segment":
                Cycle.Condenser.model = 'segment'
                Cycle.Condenser.Thermal.Nsegments = condenser.N_segments
            elif condenser.model == "Phase by Phase":
                Cycle.Condenser.model = 'phase'
                Cycle.Condenser.Thermal.Nsegments = 1
            Cycle.Condenser.Q_error_tol = condenser.HX_Q_tol
            Cycle.Condenser.max_iter_per_circuit = condenser.N_iterations
            if condenser.Fan_model == "Fan Efficiency Model":
                Cycle.Condenser.Fan.model = 'efficiency'
                Cycle.Condenser.Fan.efficiency = condenser.Fan_model_efficiency_exp
            elif condenser.Fan_model == "Fan Curve Model":
                Cycle.Condenser.Fan.model = 'curve'
                Cycle.Condenser.Fan.power_curve = condenser.Fan_model_P_exp
                Cycle.Condenser.Fan.DP_curve = condenser.Fan_model_DP_exp
            elif condenser.Fan_model == "Fan Power Model":
                Cycle.Condenser.Fan.model = 'power'
                Cycle.Condenser.Fan.power_exp = condenser.Fan_model_power_exp
    
            Cycle.Condenser.Fan.Fan_position = 'after'
    
            Cycle.Condenser.Geometry.N_tube_per_bank_per_pass = condenser.Circuiting.bank_passes
            if condenser.Geometry.Fin_on_side_index:
                Cycle.Condenser.Geometry.Fin_rows = condenser.N_tube_per_bank + 1
            else:
                Cycle.Condenser.Geometry.Fin_rows = condenser.N_tube_per_bank - 1
    
            Cycle.Condenser.Geometry.T_L = condenser.Geometry.T_l
            Cycle.Condenser.Geometry.T_w = condenser.Geometry.T_w
            Cycle.Condenser.Geometry.T_h = condenser.Geometry.T_h
            Cycle.Condenser.Geometry.T_s = condenser.Geometry.T_s
            Cycle.Condenser.Geometry.P_shape = condenser.Geometry.port_shape
            Cycle.Condenser.Geometry.P_end = condenser.Geometry.T_end
            Cycle.Condenser.Geometry.P_a = condenser.Geometry.port_a_dim
            if condenser.Geometry.port_shape in ['Rectangle', 'Triangle']:
                Cycle.Condenser.Geometry.P_b = condenser.Geometry.port_b_dim
            Cycle.Condenser.Geometry.N_port = condenser.Geometry.N_ports
            Cycle.Condenser.Geometry.Enhanced = False
            Cycle.Condenser.Geometry.FinType = condenser.Geometry.Fin_type
            if condenser.Geometry.Fin_type == "Louvered":
                Cycle.Condenser.Geometry.Fin_Llouv = condenser.Geometry.Fin_llouv
                Cycle.Condenser.Geometry.Fin_alpha = condenser.Geometry.Fin_lalpha
                Cycle.Condenser.Geometry.Fin_Lp = condenser.Geometry.Fin_lp
                
            Cycle.Condenser.Geometry.Fin_t = condenser.Geometry.Fin_t
            Cycle.Condenser.Geometry.Fin_L = condenser.Geometry.Fin_l
            Cycle.Condenser.Geometry.FPI = condenser.Geometry.Fin_FPI
            Cycle.Condenser.Geometry.e_D = condenser.Geometry.e_D
            Cycle.Condenser.Geometry.Header_CS_Type = condenser.Geometry.header_shape
            Cycle.Condenser.Geometry.Header_dim_a = condenser.Geometry.header_a_dim
            if condenser.Geometry.header_shape in ["Rectangle"]:
                Cycle.Condenser.Geometry.Header_dim_b = condenser.Geometry.header_b_dim
            Cycle.Condenser.Geometry.Header_length = condenser.Geometry.header_height
    
            if hasattr(condenser,"Vdot_ha"):
                Cycle.Condenser.Vdot_ha = condenser.Vdot_ha
            else:
                v_spec = HAPropsSI("V","T",Cycle.Condenser.Tin_a,"W",Cycle.Condenser.Win_a,"P",Cycle.Condenser.Pin_a)
                Cycle.Condenser.Vdot_ha = condenser.mdot_da * v_spec
            Cycle.Condenser.Thermal.k_fin = condenser.Geometry.Fin_k
            Cycle.Condenser.Thermal.kw = condenser.Geometry.Tube_k
            Cycle.Condenser.Thermal.Headers_DP_r = condenser.Geometry.Header_DP
            Cycle.Condenser.Thermal.FinsOnce = True
            Cycle.Condenser.Thermal.HTC_superheat_Corr = condenser.superheat_HTC_corr
            Cycle.Condenser.Thermal.HTC_subcool_Corr = condenser.subcool_HTC_corr
            Cycle.Condenser.Thermal.DP_superheat_Corr = condenser.superheat_DP_corr
            Cycle.Condenser.Thermal.DP_subcool_Corr = condenser.subcool_DP_corr
            Cycle.Condenser.Thermal.HTC_2phase_Corr = condenser._2phase_HTC_corr
            Cycle.Condenser.Thermal.DP_2phase_Corr = condenser._2phase_DP_corr
            Cycle.Condenser.Thermal.DP_Accel_Corr = condenser._2phase_charge_corr
            Cycle.Condenser.Thermal.rho_2phase_Corr = condenser._2phase_charge_corr
            Cycle.Condenser.Thermal.Air_dry_Corr = condenser.air_dry_HTC_corr
            Cycle.Condenser.Thermal.Air_wet_Corr = condenser.air_wet_HTC_corr
            Cycle.Condenser.Thermal.h_r_superheat_tuning = condenser.superheat_HTC_correction
            Cycle.Condenser.Thermal.h_r_subcooling_tuning = condenser.subcool_HTC_correction
            Cycle.Condenser.Thermal.h_r_2phase_tuning = condenser._2phase_HTC_correction
            Cycle.Condenser.Thermal.h_a_dry_tuning = condenser.air_dry_HTC_correction
            Cycle.Condenser.Thermal.h_a_wet_tuning = condenser.air_wet_HTC_correction
            Cycle.Condenser.Thermal.DP_a_dry_tuning = condenser.air_dry_DP_correction
            Cycle.Condenser.Thermal.DP_a_wet_tuning = condenser.air_wet_DP_correction
            Cycle.Condenser.Thermal.DP_r_superheat_tuning = condenser.superheat_DP_correction
            Cycle.Condenser.Thermal.DP_r_subcooling_tuning = condenser.subcool_DP_correction
            Cycle.Condenser.Thermal.DP_r_2phase_tuning = condenser._2phase_DP_correction
            if hasattr(condenser,'h_a_wet_on'):
                Cycle.Condenser.Thermal.h_a_wet_on = condenser.h_a_wet_on
            else:
                Cycle.Condenser.Thermal.h_a_wet_on = False
            if hasattr(condenser,'DP_a_wet_on'):
                Cycle.Condenser.Thermal.DP_a_wet_on = condenser.DP_a_wet_on
            else:
                Cycle.Condenser.Thermal.DP_a_wet_on = False
    
        # Evaporator definition
        if Evaporator_Type == "Fin-tube":
    
            if evaporator.Air_flow_direction in ["Sub Heat Exchanger First","Sub Heat Exchanger Last"]:
                number_of_circuits = evaporator.N_series_Circuits + 1
            elif evaporator.Air_flow_direction in ["Parallel","Series-Parallel","Series-Counter"]:
                number_of_circuits = evaporator.N_series_Circuits
            Cycle.Evaporator.name = evaporator.name
            if evaporator.Accurate == "CoolProp":
                Cycle.Evaporator.Accurate = True
            elif evaporator.Accurate == "Psychrolib":
                Cycle.Evaporator.Accurate = False
            Cycle.Evaporator.create_circuits(number_of_circuits)
            for i in range(number_of_circuits):
                N = evaporator.circuits[i].N_Circuits
                connection = [i,i+1,i,1.0,N]
                Cycle.Evaporator.connect(*tuple(connection))
            Cycle.Evaporator.Tin_a = Tin_a_evap
            Cycle.Evaporator.Pin_a = evaporator.Air_P
            Cycle.Evaporator.Win_a = Win_a_evap
            Cycle.Evaporator.Fan_add_DP = options['Evaporator_Fan_add_DP']
            if evaporator.Air_flow_direction == "Parallel":
                Cycle.Evaporator.Air_sequence = 'parallel'
                Cycle.Evaporator.Air_distribution = evaporator.Air_Distribution
            elif evaporator.Air_flow_direction == "Series-Parallel":
                Cycle.Evaporator.Air_sequence = 'series_parallel'
            elif evaporator.Air_flow_direction == "Series-Counter":
                Cycle.Evaporator.Air_sequence = 'series_counter'
            elif evaporator.Air_flow_direction == "Sub Heat Exchanger First":
                Cycle.Evaporator.Air_sequence = 'sub_HX_first'
                Cycle.Evaporator.Air_distribution = evaporator.Air_Distribution
            elif evaporator.Air_flow_direction == "Sub Heat Exchanger Last":
                Cycle.Evaporator.Air_sequence = 'sub_HX_last'
                Cycle.Evaporator.Air_distribution = evaporator.Air_Distribution
            if evaporator.model == "Segment by Segment":
                Cycle.Evaporator.model = 'segment'
                N_segments = evaporator.N_segments
            elif evaporator.model == "Phase by Phase":
                Cycle.Evaporator.model = 'phase'
                N_segments = 1.0
            Cycle.Evaporator.Q_error_tol = evaporator.HX_Q_tol
            Cycle.Evaporator.max_iter_per_circuit = evaporator.N_iterations
            if evaporator.Fan_model == "Fan Efficiency Model":
                Cycle.Evaporator.Fan.model = 'efficiency'
                Cycle.Evaporator.Fan.efficiency = evaporator.Fan_model_efficiency_exp
            elif evaporator.Fan_model == "Fan Curve Model":
                Cycle.Evaporator.Fan.model = 'curve'
                Cycle.Evaporator.Fan.power_curve = evaporator.Fan_model_P_exp
                Cycle.Evaporator.Fan.DP_curve = evaporator.Fan_model_DP_exp
            elif evaporator.Fan_model == "Fan Power Model":
                Cycle.Evaporator.Fan.model = 'power'
                Cycle.Evaporator.Fan.power_exp = evaporator.Fan_model_power_exp
                
            Cycle.Evaporator.Fan.Fan_position = 'after'
            if hasattr(evaporator,"Vdot_ha"):
                Cycle.Evaporator.Vdot_ha = evaporator.Vdot_ha
            else:
                v_spec = HAPropsSI("V","T",Cycle.Evaporator.Tin_a,"W",Cycle.Evaporator.Win_a,"P",Cycle.Evaporator.Pin_a)
                Cycle.Evaporator.Vdot_ha = evaporator.mdot_da * v_spec
            
            if evaporator.solver == "Mass flow rate solver":
                Cycle.Evaporator.Solver = 'mdot'
            elif evaporator.solver == "Pressure drop solver":
                Cycle.Evaporator.Solver = 'dp'            
            
            for i in range(number_of_circuits):
                Cycle.Evaporator.Circuits[i].Geometry.Ntubes_per_bank_per_subcircuit = evaporator.circuits[i].N_tube_per_bank
                Cycle.Evaporator.Circuits[i].Geometry.Nbank = evaporator.circuits[i].N_bank
                Cycle.Evaporator.Circuits[i].Geometry.OD = evaporator.circuits[i].OD
                Cycle.Evaporator.Circuits[i].Geometry.Ltube = evaporator.circuits[i].Ltube
                if evaporator.circuits[i].Tube_type == "Smooth":
                    Cycle.Evaporator.Circuits[i].Geometry.Tubes_type = "Smooth"
                    Cycle.Evaporator.Circuits[i].Geometry.ID = evaporator.circuits[i].ID
                    Cycle.Evaporator.Circuits[i].Geometry.e_D = evaporator.circuits[i].e_D
                elif evaporator.circuits[i].Tube_type == "Microfin":
                    Cycle.Evaporator.Circuits[i].Geometry.Tubes_type = "Microfin"
                    Cycle.Evaporator.Circuits[i].Geometry.t = evaporator.circuits[i].Tube_t
                    Cycle.Evaporator.Circuits[i].Geometry.beta = evaporator.circuits[i].Tube_beta
                    Cycle.Evaporator.Circuits[i].Geometry.e = evaporator.circuits[i].Tube_e
                    Cycle.Evaporator.Circuits[i].Geometry.d = evaporator.circuits[i].Tube_d
                    Cycle.Evaporator.Circuits[i].Geometry.gama = evaporator.circuits[i].Tube_gamma
                    Cycle.Evaporator.Circuits[i].Geometry.n = evaporator.circuits[i].Tube_n
                Cycle.Evaporator.Circuits[i].Geometry.Staggering = evaporator.circuits[i].Staggering
                Cycle.Evaporator.Circuits[i].Geometry.Pl = evaporator.circuits[i].Pl
                Cycle.Evaporator.Circuits[i].Geometry.Pt = evaporator.circuits[i].Pt
                Cycle.Evaporator.Circuits[i].Geometry.Connections = evaporator.circuits[i].Connections
                Cycle.Evaporator.Circuits[i].Geometry.FarBendRadius = 0.01
                Cycle.Evaporator.Circuits[i].Geometry.FPI = evaporator.circuits[i].Fin_FPI
                Cycle.Evaporator.Circuits[i].Geometry.Fin_t = evaporator.circuits[i].Fin_t
                Cycle.Evaporator.Circuits[i].Geometry.FinType = evaporator.circuits[i].Fin_type
                if evaporator.circuits[i].Fin_type == "Wavy":
                    Cycle.Evaporator.Circuits[i].Geometry.Fin_Pd = evaporator.circuits[i].Fin_pd
                    Cycle.Evaporator.Circuits[i].Geometry.Fin_xf = evaporator.circuits[i].Fin_xf
                elif evaporator.circuits[i].Fin_type == "WavyLouvered":
                    Cycle.Evaporator.Circuits[i].Geometry.Fin_Pd = evaporator.circuits[i].Fin_pd
                    Cycle.Evaporator.Circuits[i].Geometry.Fin_xf = evaporator.circuits[i].Fin_xf
                elif evaporator.circuits[i].Fin_type == "Louvered":
                    Cycle.Evaporator.Circuits[i].Geometry.Fin_Lp = evaporator.circuits[i].Fin_Lp
                    Cycle.Evaporator.Circuits[i].Geometry.Fin_Lh = evaporator.circuits[i].Fin_Lh
                elif evaporator.circuits[i].Fin_type == "Slit":
                    Cycle.Evaporator.Circuits[i].Geometry.Fin_Sh = evaporator.circuits[i].Fin_Sh
                    Cycle.Evaporator.Circuits[i].Geometry.Fin_Ss = evaporator.circuits[i].Fin_Ss
                    Cycle.Evaporator.Circuits[i].Geometry.Fin_Sn = evaporator.circuits[i].Fin_Sn
                    
                Cycle.Evaporator.Circuits[i].Thermal.Nsegments = N_segments
                Cycle.Evaporator.Circuits[i].Thermal.kw = evaporator.circuits[i].Tube_k
                Cycle.Evaporator.Circuits[i].Thermal.k_fin = evaporator.circuits[i].Fin_k
                Cycle.Evaporator.Circuits[i].Thermal.FinsOnce = True
                Cycle.Evaporator.Circuits[i].Thermal.HTC_superheat_Corr = evaporator.circuits[i].superheat_HTC_corr
                Cycle.Evaporator.Circuits[i].Thermal.HTC_subcool_Corr = evaporator.circuits[i].subcool_HTC_corr
                Cycle.Evaporator.Circuits[i].Thermal.DP_superheat_Corr = evaporator.circuits[i].superheat_DP_corr
                Cycle.Evaporator.Circuits[i].Thermal.DP_subcool_Corr = evaporator.circuits[i].subcool_DP_corr
                Cycle.Evaporator.Circuits[i].Thermal.HTC_2phase_Corr = evaporator.circuits[i]._2phase_HTC_corr
                Cycle.Evaporator.Circuits[i].Thermal.DP_2phase_Corr = evaporator.circuits[i]._2phase_DP_corr
                Cycle.Evaporator.Circuits[i].Thermal.DP_Accel_Corr = evaporator.circuits[i]._2phase_charge_corr
                Cycle.Evaporator.Circuits[i].Thermal.rho_2phase_Corr = evaporator.circuits[i]._2phase_charge_corr
                Cycle.Evaporator.Circuits[i].Thermal.Air_dry_Corr = evaporator.circuits[i].air_dry_HTC_corr
                Cycle.Evaporator.Circuits[i].Thermal.Air_wet_Corr = evaporator.circuits[i].air_wet_HTC_corr
                Cycle.Evaporator.Circuits[i].Thermal.h_r_superheat_tuning = evaporator.circuits[i].superheat_HTC_correction
                Cycle.Evaporator.Circuits[i].Thermal.h_r_subcooling_tuning = evaporator.circuits[i].subcool_HTC_correction
                Cycle.Evaporator.Circuits[i].Thermal.h_r_2phase_tuning = evaporator.circuits[i]._2phase_HTC_correction
                Cycle.Evaporator.Circuits[i].Thermal.h_a_dry_tuning = evaporator.circuits[i].air_dry_HTC_correction
                Cycle.Evaporator.Circuits[i].Thermal.h_a_wet_tuning = evaporator.circuits[i].air_wet_HTC_correction
                Cycle.Evaporator.Circuits[i].Thermal.DP_a_dry_tuning = evaporator.circuits[i].air_dry_DP_correction
                Cycle.Evaporator.Circuits[i].Thermal.DP_a_wet_tuning = evaporator.circuits[i].air_wet_DP_correction
                Cycle.Evaporator.Circuits[i].Thermal.DP_r_superheat_tuning = evaporator.circuits[i].superheat_DP_correction
                Cycle.Evaporator.Circuits[i].Thermal.DP_r_subcooling_tuning = evaporator.circuits[i].subcool_DP_correction
                Cycle.Evaporator.Circuits[i].Thermal.DP_r_2phase_tuning = evaporator.circuits[i]._2phase_DP_correction
                if hasattr(evaporator.circuits[i],'h_a_wet_on'):
                    Cycle.Evaporator.Circuits[i].Thermal.h_a_wet_on = evaporator.circuits[i].h_a_wet_on
                else:
                    Cycle.Evaporator.Circuits[i].Thermal.h_a_wet_on = False
                    
                if hasattr(evaporator.circuits[i],'DP_a_wet_on'):
                    Cycle.Evaporator.Circuits[i].Thermal.DP_a_wet_on = evaporator.circuits[i].DP_a_wet_on
                else:
                    Cycle.Evaporator.Circuits[i].Thermal.DP_a_wet_on = False
    
                if hasattr(evaporator.circuits[i],'sub_HX_values'):
                    Cycle.Evaporator.Circuits[i].Geometry.Sub_HX_matrix = evaporator.circuits[i].sub_HX_values
                
        elif Evaporator_Type == "MicroChannel":
            Cycle.Evaporator.name = evaporator.name
            if evaporator.Accurate == "CoolProp":
                Cycle.Evaporator.Accurate = True
            elif evaporator.Accurate == "Psychrolib":
                Cycle.Evaporator.Accurate = False
            Cycle.Evaporator.Tin_a = Tin_a_evap
            Cycle.Evaporator.Pin_a = evaporator.Air_P
            Cycle.Evaporator.Win_a = Win_a_evap
            Cycle.Evaporator.Fan_add_DP = options['Evaporator_Fan_add_DP']
            if evaporator.model == "Segment by Segment":
                Cycle.Evaporator.model = 'segment'
                Cycle.Evaporator.Thermal.Nsegments = evaporator.N_segments
            elif evaporator.model == "Phase by Phase":
                Cycle.Evaporator.model = 'phase'
                Cycle.Evaporator.Thermal.Nsegments = 1
            Cycle.Evaporator.Q_error_tol = evaporator.HX_Q_tol
            Cycle.Evaporator.max_iter_per_circuit = evaporator.N_iterations
            if evaporator.Fan_model == "Fan Efficiency Model":
                Cycle.Evaporator.Fan.model = 'efficiency'
                Cycle.Evaporator.Fan.efficiency = evaporator.Fan_model_efficiency_exp
            elif evaporator.Fan_model == "Fan Curve Model":
                Cycle.Evaporator.Fan.model = 'curve'
                Cycle.Evaporator.Fan.power_curve = evaporator.Fan_model_P_exp
                Cycle.Evaporator.Fan.DP_curve = evaporator.Fan_model_DP_exp
            elif evaporator.Fan_model == "Fan Power Model":
                Cycle.Evaporator.Fan.model = 'power'
                Cycle.Evaporator.Fan.power_exp = evaporator.Fan_model_power_exp
    
            Cycle.Evaporator.Fan.Fan_position = 'after'
    
            Cycle.Evaporator.Geometry.N_tube_per_bank_per_pass = evaporator.Circuiting.bank_passes
            if evaporator.Geometry.Fin_on_side_index:
                Cycle.Evaporator.Geometry.Fin_rows = evaporator.N_tube_per_bank + 1
            else:
                Cycle.Evaporator.Geometry.Fin_rows = evaporator.N_tube_per_bank - 1
    
            Cycle.Evaporator.Geometry.T_L = evaporator.Geometry.T_l
            Cycle.Evaporator.Geometry.T_w = evaporator.Geometry.T_w
            Cycle.Evaporator.Geometry.T_h = evaporator.Geometry.T_h
            Cycle.Evaporator.Geometry.T_s = evaporator.Geometry.T_s
            Cycle.Evaporator.Geometry.P_shape = evaporator.Geometry.port_shape
            Cycle.Evaporator.Geometry.P_end = evaporator.Geometry.T_end
            Cycle.Evaporator.Geometry.P_a = evaporator.Geometry.port_a_dim
            if evaporator.Geometry.port_shape in ['Rectangle', 'Triangle']:
                Cycle.Evaporator.Geometry.P_b = evaporator.Geometry.port_b_dim
            Cycle.Evaporator.Geometry.N_port = evaporator.Geometry.N_ports
            Cycle.Evaporator.Geometry.Enhanced = False
            Cycle.Evaporator.Geometry.FinType = evaporator.Geometry.Fin_type
            if evaporator.Geometry.Fin_type == "Louvered":
                Cycle.Evaporator.Geometry.Fin_Llouv = evaporator.Geometry.Fin_llouv
                Cycle.Evaporator.Geometry.Fin_alpha = evaporator.Geometry.Fin_lalpha
                Cycle.Evaporator.Geometry.Fin_Lp = evaporator.Geometry.Fin_lp
                
            Cycle.Evaporator.Geometry.Fin_t = evaporator.Geometry.Fin_t
            Cycle.Evaporator.Geometry.Fin_L = evaporator.Geometry.Fin_l
            Cycle.Evaporator.Geometry.FPI = evaporator.Geometry.Fin_FPI
            Cycle.Evaporator.Geometry.e_D = evaporator.Geometry.e_D
            Cycle.Evaporator.Geometry.Header_CS_Type = evaporator.Geometry.header_shape
            Cycle.Evaporator.Geometry.Header_dim_a = evaporator.Geometry.header_a_dim
            if evaporator.Geometry.header_shape in ["Rectangle"]:
                Cycle.Evaporator.Geometry.Header_dim_b = evaporator.Geometry.header_b_dim
            Cycle.Evaporator.Geometry.Header_length = evaporator.Geometry.header_height
    
            if hasattr(evaporator,"Vdot_ha"):
                Cycle.Evaporator.Vdot_ha = evaporator.Vdot_ha
            else:
                v_spec = HAPropsSI("V","T",Cycle.Evaporator.Tin_a,"W",Cycle.Evaporator.Win_a,"P",Cycle.Evaporator.Pin_a)
                Cycle.Evaporator.Vdot_ha = evaporator.mdot_da * v_spec
            Cycle.Evaporator.Thermal.k_fin = evaporator.Geometry.Fin_k
            Cycle.Evaporator.Thermal.kw = evaporator.Geometry.Tube_k
            Cycle.Evaporator.Thermal.Headers_DP_r = evaporator.Geometry.Header_DP
            Cycle.Evaporator.Thermal.FinsOnce = True
            Cycle.Evaporator.Thermal.HTC_superheat_Corr = evaporator.superheat_HTC_corr
            Cycle.Evaporator.Thermal.HTC_subcool_Corr = evaporator.subcool_HTC_corr
            Cycle.Evaporator.Thermal.DP_superheat_Corr = evaporator.superheat_DP_corr
            Cycle.Evaporator.Thermal.DP_subcool_Corr = evaporator.subcool_DP_corr
            Cycle.Evaporator.Thermal.HTC_2phase_Corr = evaporator._2phase_HTC_corr
            Cycle.Evaporator.Thermal.DP_2phase_Corr = evaporator._2phase_DP_corr
            Cycle.Evaporator.Thermal.DP_Accel_Corr = evaporator._2phase_charge_corr
            Cycle.Evaporator.Thermal.rho_2phase_Corr = evaporator._2phase_charge_corr
            Cycle.Evaporator.Thermal.Air_dry_Corr = evaporator.air_dry_HTC_corr
            Cycle.Evaporator.Thermal.Air_wet_Corr = evaporator.air_wet_HTC_corr
            Cycle.Evaporator.Thermal.h_r_superheat_tuning = evaporator.superheat_HTC_correction
            Cycle.Evaporator.Thermal.h_r_subcooling_tuning = evaporator.subcool_HTC_correction
            Cycle.Evaporator.Thermal.h_r_2phase_tuning = evaporator._2phase_HTC_correction
            Cycle.Evaporator.Thermal.h_a_dry_tuning = evaporator.air_dry_HTC_correction
            Cycle.Evaporator.Thermal.h_a_wet_tuning = evaporator.air_wet_HTC_correction
            Cycle.Evaporator.Thermal.DP_a_dry_tuning = evaporator.air_dry_DP_correction
            Cycle.Evaporator.Thermal.DP_a_wet_tuning = evaporator.air_wet_DP_correction
            Cycle.Evaporator.Thermal.DP_r_superheat_tuning = evaporator.superheat_DP_correction
            Cycle.Evaporator.Thermal.DP_r_subcooling_tuning = evaporator.subcool_DP_correction
            Cycle.Evaporator.Thermal.DP_r_2phase_tuning = evaporator._2phase_DP_correction
            if hasattr(evaporator,'h_a_wet_on'):
                Cycle.Evaporator.Thermal.h_a_wet_on = evaporator.h_a_wet_on
            else:
                Cycle.Evaporator.Thermal.h_a_wet_on = False
            if hasattr(evaporator,'DP_a_wet_on'):
                Cycle.Evaporator.Thermal.DP_a_wet_on = evaporator.DP_a_wet_on
            else:
                Cycle.Evaporator.Thermal.DP_a_wet_on = False
            
        # Liqid Line Definition
        Cycle.Line_Liquid.name = liquid_line.Line_name
        Cycle.Line_Liquid.L = liquid_line.Line_length
        Cycle.Line_Liquid.ID = liquid_line.Line_ID
        Cycle.Line_Liquid.OD = liquid_line.Line_OD
        Cycle.Line_Liquid.k_line = liquid_line.Line_tube_k
        Cycle.Line_Liquid.k_ins = liquid_line.Line_insulation_k
        Cycle.Line_Liquid.t_ins = liquid_line.Line_insulation_t
        Cycle.Line_Liquid.T_sur = liquid_line.Line_surrounding_T
        Cycle.Line_Liquid.h_sur = liquid_line.Line_surrounding_HTC
        Cycle.Line_Liquid.e_D = liquid_line.Line_e_D
        Cycle.Line_Liquid.Nsegments = liquid_line.Line_N_segments
        Cycle.Line_Liquid.Q_error_tol = liquid_line.Line_q_tolerance
        Cycle.Line_Liquid.DP_tuning = liquid_line.Line_DP_correction
        Cycle.Line_Liquid.HT_tuning = liquid_line.Line_HT_correction
        Cycle.Line_Liquid.N_90_bends = liquid_line.Line_N_90_bends
        Cycle.Line_Liquid.N_180_bends = liquid_line.Line_N_180_bends
    
        # 2phase Line Definition
        Cycle.Line_2phase.name = twophase_line.Line_name
        Cycle.Line_2phase.L = twophase_line.Line_length
        Cycle.Line_2phase.ID = twophase_line.Line_ID
        Cycle.Line_2phase.OD = twophase_line.Line_OD
        Cycle.Line_2phase.k_line = twophase_line.Line_tube_k
        Cycle.Line_2phase.k_ins = twophase_line.Line_insulation_k
        Cycle.Line_2phase.t_ins = twophase_line.Line_insulation_t
        Cycle.Line_2phase.T_sur = twophase_line.Line_surrounding_T
        Cycle.Line_2phase.h_sur = twophase_line.Line_surrounding_HTC
        Cycle.Line_2phase.e_D = twophase_line.Line_e_D
        Cycle.Line_2phase.Nsegments = twophase_line.Line_N_segments
        Cycle.Line_2phase.Q_error_tol = twophase_line.Line_q_tolerance
        Cycle.Line_2phase.DP_tuning = twophase_line.Line_DP_correction
        Cycle.Line_2phase.HT_tuning = twophase_line.Line_HT_correction
        Cycle.Line_2phase.N_90_bends = twophase_line.Line_N_90_bends
        Cycle.Line_2phase.N_180_bends = twophase_line.Line_N_180_bends
    
        # Liqid Line Definition
        Cycle.Line_Suction.name = suction_line.Line_name
        Cycle.Line_Suction.L = suction_line.Line_length
        Cycle.Line_Suction.ID = suction_line.Line_ID
        Cycle.Line_Suction.OD = suction_line.Line_OD
        Cycle.Line_Suction.k_line = suction_line.Line_tube_k
        Cycle.Line_Suction.k_ins = suction_line.Line_insulation_k
        Cycle.Line_Suction.t_ins = suction_line.Line_insulation_t
        Cycle.Line_Suction.T_sur = suction_line.Line_surrounding_T
        Cycle.Line_Suction.h_sur = suction_line.Line_surrounding_HTC
        Cycle.Line_Suction.e_D = suction_line.Line_e_D
        Cycle.Line_Suction.Nsegments = suction_line.Line_N_segments
        Cycle.Line_Suction.Q_error_tol = suction_line.Line_q_tolerance
        Cycle.Line_Suction.DP_tuning = suction_line.Line_DP_correction
        Cycle.Line_Suction.HT_tuning = suction_line.Line_HT_correction
        Cycle.Line_Suction.N_90_bends = suction_line.Line_N_90_bends
        Cycle.Line_Suction.N_180_bends = suction_line.Line_N_180_bends
    
        # Liqid Line Definition
        Cycle.Line_Discharge.name = discharge_line.Line_name
        Cycle.Line_Discharge.L = discharge_line.Line_length
        Cycle.Line_Discharge.ID = discharge_line.Line_ID
        Cycle.Line_Discharge.OD = discharge_line.Line_OD
        Cycle.Line_Discharge.k_line = discharge_line.Line_tube_k
        Cycle.Line_Discharge.k_ins = discharge_line.Line_insulation_k
        Cycle.Line_Discharge.t_ins = discharge_line.Line_insulation_t
        Cycle.Line_Discharge.T_sur = discharge_line.Line_surrounding_T
        Cycle.Line_Discharge.h_sur = discharge_line.Line_surrounding_HTC
        Cycle.Line_Discharge.e_D = discharge_line.Line_e_D
        Cycle.Line_Discharge.Nsegments = discharge_line.Line_N_segments
        Cycle.Line_Discharge.Q_error_tol = discharge_line.Line_q_tolerance
        Cycle.Line_Discharge.DP_tuning = discharge_line.Line_DP_correction
        Cycle.Line_Discharge.HT_tuning = discharge_line.Line_HT_correction
        Cycle.Line_Discharge.N_90_bends = discharge_line.Line_N_90_bends
        Cycle.Line_Discharge.N_180_bends = discharge_line.Line_N_180_bends
        
        # Capillary tube
        if capillary != None:
            Cycle.Capillary.Ref = options['Ref']
            Cycle.Capillary.name = capillary.Capillary_name
            Cycle.Capillary.L = capillary.Capillary_length
            Cycle.Capillary.D = capillary.Capillary_D
            Cycle.Capillary.D_liquid = capillary.Capillary_entrance_D
            Cycle.Capillary.Ntubes = capillary.Capillary_N_tubes
            Cycle.Capillary.DT_2phase = capillary.Capillary_DT
            Cycle.Capillary.DP_converged = capillary.Capillary_DP_tolerance        
            if capillary.Capillary_correlation == 0:    
                Cycle.Capillary.method = "choi"
            elif capillary.Capillary_correlation == 1:    
                Cycle.Capillary.method = "wolf"
            elif capillary.Capillary_correlation == 2:    
                Cycle.Capillary.method = "wolf_physics"
            elif capillary.Capillary_correlation == 3:    
                Cycle.Capillary.method = "wolf_pate"
            elif capillary.Capillary_correlation == 4:    
                Cycle.Capillary.method = "rasti"
    
        Cycle.update_residuals = update_residuals
        Cycle.solver_option = options['solver']
        Cycle.check_terminate = False
        return (1,Cycle)
    except:
        return (0,"could not define cycle")
