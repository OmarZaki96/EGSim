import CoolProp as CP
from backend.CompressorAHRI import CompressorAHRIClass
from backend.CompressorPHY import CompressorPHYClass
from backend.FinTubeHEX import FinTubeHEXClass
from backend.MicroChannelHEX import MicroChannelHEXClass

from CoolProp.CoolProp import HAPropsSI

def get_Tsats(validation_table):
    if validation_table["mode"] == 0:
        mode = "AC"
    else:
        mode = "HP"
    
    SC = validation_table["SC"]
    SH = validation_table["SH"]

    COP = validation_table["COP"]

    TTD_evap_AC = validation_table["TTD_evap_AC"]
    TTD_cond_AC = validation_table["TTD_cond_AC"]
    TTD_evap_HP = validation_table["TTD_evap_HP"]
    TTD_cond_HP = validation_table["TTD_cond_HP"]
    
    Test_cond = validation_table["Test_Condition"]
    
    capacity = validation_table["Capacity"]
    
    if Test_cond == "T1":
        Tin_a_evap = 27 + 273.15
        Win_a_evap = HAPropsSI("W","T", 27 + 273.15,"P",101325,"B", 19 + 273.15)
        Tin_a_cond = 35 + 273.15
        Win_a_cond = HAPropsSI("W","T", 35 + 273.15,"P",101325,"B", 24 + 273.15)

    elif Test_cond == "T2":
        Tin_a_evap = 21 + 273.15
        Win_a_evap = HAPropsSI("W","T", 21 + 273.15,"P",101325,"B", 15 + 273.15)
        Tin_a_cond = 27 + 273.15
        Win_a_cond = HAPropsSI("W","T", 27 + 273.15,"P",101325,"B", 19 + 273.15)

    elif Test_cond == "T3":
        Tin_a_evap = 29 + 273.15
        Win_a_evap = HAPropsSI("W","T", 29 + 273.15,"P",101325,"B", 19 + 273.15)
        Tin_a_cond = 46 + 273.15
        Win_a_cond = HAPropsSI("W","T", 46 + 273.15,"P",101325,"B", 24 + 273.15)

    elif Test_cond == "H1":
        Tin_a_evap = 7 + 273.15
        Win_a_evap = HAPropsSI("W","T", 7 + 273.15,"P",101325,"B", 6 + 273.15)
        Tin_a_cond = 20 + 273.15
        Win_a_cond = HAPropsSI("W","T", 20 + 273.15,"P",101325,"B", 15 + 273.15)

    elif Test_cond == "H2":
        Tin_a_evap = 2 + 273.15
        Win_a_evap = HAPropsSI("W","T", 2 + 273.15,"P",101325,"B", 1 + 273.15)
        Tin_a_cond = 20 + 273.15
        Win_a_cond = HAPropsSI("W","T", 20 + 273.15,"P",101325,"B", 15 + 273.15)

    elif Test_cond == "H3":
        Tin_a_evap = -7 + 273.15
        Win_a_evap = HAPropsSI("W","T", -7 + 273.15,"P",101325,"B", -8 + 273.15)
        Tin_a_cond = 20 + 273.15
        Win_a_cond = HAPropsSI("W","T", 20 + 273.15,"P",101325,"B", 15 + 273.15)
    
    else:
        if "Tin_a_evap" in validation_table.keys():
            Tin_a_evap = validation_table["Tin_a_evap"]
            Pin_a_evap = validation_table["Pin_a_evap"]
            Win_a_evap = validation_table["win_a_evap"]
        else:            
            if mode == "AC":
                Tin_a_evap = 27 + 273.15
                Win_a_evap = HAPropsSI("W","T", 27 + 273.15,"P",101325,"B", 19 + 273.15)
            elif mode == "HP":
                Tin_a_evap = 7 + 273.15
                Win_a_evap = HAPropsSI("W","T", 7 + 273.15,"P",101325,"B", 6 + 273.15)
        
        if "Tin_a_cond" in validation_table.keys():
            Tin_a_cond = validation_table["Tin_a_cond"]
            Pin_a_cond = validation_table["Pin_a_cond"]
            Win_a_cond = validation_table["win_a_cond"]
        else:            
            if mode == "AC":
                Tin_a_cond = 35 + 273.15
                Win_a_cond = HAPropsSI("W","T", 35 + 273.15,"P",101325,"B", 24 + 273.15)
            elif mode == "HP":
                Tin_a_cond = 20 + 273.15
                Win_a_cond = HAPropsSI("W","T", 27 + 273.15,"P",101325,"B", 15 + 273.15)
    
    if "Vdot_ha_evap" in validation_table.keys():
        Vdot_ha_evap = validation_table["Vdot_ha_evap"]
        v_spec = HAPropsSI("V","T",Tin_a_evap,"W",Win_a_evap,"P",101325)
        mdot_da_evap = Vdot_ha_evap / v_spec
    elif "mdot_da_evap" in validation_table.keys():
        mdot_da_evap = validation_table["mdot_da_evap"]
    else:
        Vdot_ha_evap = capacity / 3517 * 400 / 2118.88
        v_spec = HAPropsSI("V","T",Tin_a_evap,"W",Win_a_evap,"P",101325)
        mdot_da_evap = Vdot_ha_evap / v_spec
    
    hin_a_evap = HAPropsSI("H","T",Tin_a_evap,"W",Win_a_evap,"P",101325)
    if mode == "AC":
        hout_a_evap = hin_a_evap - capacity / mdot_da_evap
    elif mode == "HP":
        hout_a_evap = hin_a_evap - (capacity * (1 - 1 / COP)) / mdot_da_evap
    
    Tout_a_evap = HAPropsSI("T","H",hout_a_evap,"R",0.9,"P",101325)
    
    if mode == "AC":
        Tsat_cond_init = Tin_a_cond + TTD_cond_AC + SC
        Tsat_evap_init = Tout_a_evap - TTD_evap_AC - SH
    elif mode == "HP":
        Tsat_cond_init = Tin_a_cond + TTD_cond_HP + SC
        Tsat_evap_init = Tout_a_evap - TTD_evap_HP - SH
    return Tsat_evap_init,Tsat_cond_init

def check_compressor_capacity(compressor):
    validation_table = compressor.capacity_validation_table
    
    AS = CP.AbstractState("HEOS",validation_table["ref"])

    SH = validation_table["SH"]
    SC = validation_table["SC"]

    if validation_table["mode"] == 0:
        mode = "AC"
    else:
        mode = "HP"
    
    Target_capacity = validation_table["Capacity"]

    Capacity_tolerance = validation_table["Capacity_tolerance"]

    if compressor.Comp_model == "physics":
        Compressor = CompressorPHYClass()
        Compressor.name = compressor.Comp_name
        Compressor.fp = compressor.Comp_fp
        Compressor.Vdot_ratio_P = compressor.Comp_ratio_P
        Compressor.Vdot_ratio_M = compressor.Comp_ratio_M
        Compressor.Displacement = compressor.Comp_vol
        Compressor.act_speed = compressor.Comp_speed
        Compressor.Elec_eff = compressor.Comp_elec_eff
        Compressor.isen_eff = compressor.isentropic_exp
        Compressor.vol_eff = compressor.vol_exp
    
    elif compressor.Comp_model == "map":
        Compressor = CompressorAHRIClass()
        Compressor.name = compressor.Comp_name
        Compressor.M = compressor.map_data.M_coeffs
        Compressor.P = compressor.map_data.P_coeffs
        Compressor.Speeds = compressor.map_data.Speeds
        Compressor.fp = compressor.Comp_fp
        Compressor.Vdot_ratio_P = compressor.Comp_ratio_P
        Compressor.Vdot_ratio_M = compressor.Comp_ratio_M
        Compressor.Displacement = compressor.Comp_vol
        if compressor.map_data.std_type == 0:
            Compressor.SH_Ref = compressor.map_data.std_sh
        elif compressor.map_data.std_type == 1:
            Compressor.Suction_Ref = compressor.map_data.std_suction
            
        Compressor.act_speed = compressor.Comp_speed
        Compressor.Unit_system = compressor.unit_system
        Compressor.Elec_eff = compressor.Comp_elec_eff
        Compressor.F_factor = compressor.map_data.F_value

    elif compressor.Comp_model == "10coefficients":
        Compressor = CompressorAHRIClass()
        Compressor.name = compressor.Comp_name
        Compressor.M = compressor.M
        Compressor.P = compressor.P
        Compressor.Speeds = compressor.speeds
        Compressor.fp = compressor.Comp_fp
        Compressor.Vdot_ratio_P = compressor.Comp_ratio_P
        Compressor.Vdot_ratio_M = compressor.Comp_ratio_M
        Compressor.Displacement = compressor.Comp_vol
        if compressor.std_type == 0:
            Compressor.SH_Ref = compressor.std_sh
        elif compressor.std_type == 1:
            Compressor.Suction_Ref = compressor.std_suction
        Compressor.act_speed = compressor.Comp_speed
        Compressor.Unit_system = compressor.unit_system
        Compressor.Elec_eff = compressor.Comp_elec_eff
        Compressor.F_factor = compressor.Comp_AHRI_F_value
    
    Tsat_evap, Tsat_cond = get_Tsats(validation_table)
    AS.update(CP.QT_INPUTS,1.0,Tsat_cond)
    psat_cond=AS.p() #[Pa]
    AS.update(CP.QT_INPUTS,1.0,Tsat_evap)
    psat_evap=AS.p() #[Pa]    
    AS.update(CP.PT_INPUTS,psat_evap,Tsat_evap + SH)
    hin_comp = AS.hmass()
    params={
        'Pin_r': psat_evap,
        'Pout_r': psat_cond,
        'hin_r': hin_comp,
        'AS': AS,
    }
    
    Compressor.Update(**params)
    Compressor.Calculate()
    AS.update(CP.QT_INPUTS, 0.0, Tsat_cond)
    psat_cond = AS.p()
    AS.update(CP.PT_INPUTS, psat_cond, Tsat_cond - SC)
    hin_evap = AS.hmass()

    if mode == "AC":
        Q_compressor = Compressor.mdot_r * (Compressor.hin_r - hin_evap)
        
        # compressor checks
    elif mode == "HP":
        Q_compressor = Compressor.mdot_r * (Compressor.hout_r - hin_evap)
        
    # compressor checks
    Error = (Q_compressor - Target_capacity) / (Target_capacity)
    if (Q_compressor - Target_capacity) / (Target_capacity) > Capacity_tolerance:            
        return (0,"Compressor capacity might be higher than target capacity by about {:.0f}%.".format(Error*100))
    elif (Q_compressor - Target_capacity) / (Target_capacity) < (-1 * Capacity_tolerance):
        return (0,"Compressor capacity might be lower than target capacity by about {:.0f}%.".format(Error*100))
    else:
        return (1,)    

def check_evaporator_capacity_fintube(evaporator):
    Evaporator = FinTubeHEXClass()
    
    validation_table = evaporator.capacity_validation_table
    
    AS = CP.AbstractState("HEOS",validation_table["ref"])

    SH = validation_table["SH"]
    SC = validation_table["SC"]
    COP = validation_table["COP"]
    isen_eff = validation_table["comp_isen_eff"]

    if validation_table["mode"] == 0:
        mode = "AC"
        Target_capacity = validation_table["Capacity"]
    else:
        mode = "HP"
        Target_capacity = validation_table["Capacity"] * (1 - 1/COP)
    
    Capacity_tolerance = validation_table["Capacity_tolerance"]
    
    if evaporator.Air_flow_direction in ["Sub Heat Exchanger First","Sub Heat Exchanger Last"]:
        number_of_circuits = evaporator.N_series_Circuits + 1
    elif evaporator.Air_flow_direction in ["Parallel","Series-Parallel","Series-Counter"]:
        number_of_circuits = evaporator.N_series_Circuits
    
    Evaporator.name = evaporator.name
    if evaporator.Accurate == "CoolProp":
        Evaporator.Accurate = True
    elif evaporator.Accurate == "Psychrolib":
        Evaporator.Accurate = False
    Evaporator.create_circuits(number_of_circuits)
    for i in range(number_of_circuits):
        N = evaporator.circuits[i].N_Circuits
        connection = [i,i+1,i,1.0,N]
        Evaporator.connect(*tuple(connection))
    Evaporator.Tin_a = validation_table["Tin_a_evap"]
    Evaporator.Pin_a = evaporator.Air_P
    Evaporator.Win_a = validation_table["win_a_evap"]
    if evaporator.Air_flow_direction == "Parallel":
        Evaporator.Air_sequence = 'parallel'
        Evaporator.Air_distribution = evaporator.Air_Distribution
    elif evaporator.Air_flow_direction == "Series-Parallel":
        Evaporator.Air_sequence = 'series_parallel'
    elif evaporator.Air_flow_direction == "Series-Counter":
        Evaporator.Air_sequence = 'series_counter'
    elif evaporator.Air_flow_direction == "Sub Heat Exchanger First":
        Evaporator.Air_sequence = 'sub_HX_first'
        Evaporator.Air_distribution = evaporator.Air_Distribution
    elif evaporator.Air_flow_direction == "Sub Heat Exchanger Last":
        Evaporator.Air_sequence = 'sub_HX_last'
        Evaporator.Air_distribution = evaporator.Air_Distribution
    if evaporator.model == "Segment by Segment":
        Evaporator.model = 'segment'
        N_segments = evaporator.N_segments
    elif evaporator.model == "Phase by Phase":
        Evaporator.model = 'phase'
        N_segments = 1.0
    Evaporator.Q_error_tol = evaporator.HX_Q_tol
    Evaporator.max_iter_per_circuit = evaporator.N_iterations
    if evaporator.Fan_model == "Fan Efficiency Model":
        Evaporator.Fan.model = 'efficiency'
        Evaporator.Fan.efficiency = evaporator.Fan_model_efficiency_exp
    elif evaporator.Fan_model == "Fan Curve Model":
        Evaporator.Fan.model = 'curve'
        Evaporator.Fan.power_curve = evaporator.Fan_model_P_exp
        Evaporator.Fan.DP_curve = evaporator.Fan_model_DP_exp
    elif evaporator.Fan_model == "Fan Power Model":
        Evaporator.Fan.model = 'power'
        Evaporator.Fan.power_exp = evaporator.Fan_model_power_exp
        
    Evaporator.Fan.Fan_position = 'after'
    
    if hasattr(evaporator,"Vdot_ha"):
        Evaporator.Vdot_ha = evaporator.Vdot_ha
    else:
        v_spec = HAPropsSI("V","T",Evaporator.Tin_a,"W",Evaporator.Win_a,"P",Evaporator.Pin_a)
        Evaporator.Vdot_ha = evaporator.mdot_da * v_spec
    
    if evaporator.solver == "Mass flow rate solver":
        Evaporator.Solver = 'mdot'
    elif evaporator.solver == "Pressure drop solver":
        Evaporator.Solver = 'dp'            
    
    for i in range(number_of_circuits):
        Evaporator.Circuits[i].Geometry.Ntubes_per_bank_per_subcircuit = evaporator.circuits[i].N_tube_per_bank
        Evaporator.Circuits[i].Geometry.Nbank = evaporator.circuits[i].N_bank
        Evaporator.Circuits[i].Geometry.OD = evaporator.circuits[i].OD
        Evaporator.Circuits[i].Geometry.Ltube = evaporator.circuits[i].Ltube
        if evaporator.circuits[i].Tube_type == "Smooth":
            Evaporator.Circuits[i].Geometry.Tubes_type = "Smooth"
            Evaporator.Circuits[i].Geometry.ID = evaporator.circuits[i].ID
            Evaporator.Circuits[i].Geometry.e_D = evaporator.circuits[i].e_D
        elif evaporator.circuits[i].Tube_type == "Microfin":
            Evaporator.Circuits[i].Geometry.Tubes_type = "Microfin"
            Evaporator.Circuits[i].Geometry.t = evaporator.circuits[i].Tube_t
            Evaporator.Circuits[i].Geometry.beta = evaporator.circuits[i].Tube_beta
            Evaporator.Circuits[i].Geometry.e = evaporator.circuits[i].Tube_e
            Evaporator.Circuits[i].Geometry.d = evaporator.circuits[i].Tube_d
            Evaporator.Circuits[i].Geometry.gama = evaporator.circuits[i].Tube_gamma
            Evaporator.Circuits[i].Geometry.n = evaporator.circuits[i].Tube_n
        Evaporator.Circuits[i].Geometry.Staggering = evaporator.circuits[i].Staggering
        Evaporator.Circuits[i].Geometry.Pl = evaporator.circuits[i].Pl
        Evaporator.Circuits[i].Geometry.Pt = evaporator.circuits[i].Pt
        
        N_tube_per_bank = evaporator.circuits[i].N_tube_per_bank
        N_bank = evaporator.circuits[i].N_bank
        Ntubes = N_tube_per_bank * N_bank
        if evaporator.circuits[i].circuitry == 0:
            connections = []
            for k in reversed(range(int(N_bank))):
                start = k * N_tube_per_bank + 1
                end = (k + 1) * N_tube_per_bank + 1
                if (N_bank - k)%2==1:
                    connections += range(start,end)
                else:
                    connections += reversed(range(start,end))
            evaporator.circuits[i].Connections = connections
        
        elif evaporator.circuits[i].circuitry == 1: #parallel flow
            connections = []
            for k in range(int(N_bank)):
                start = k * N_tube_per_bank + 1
                end = (k + 1) * N_tube_per_bank + 1
                if k%2==0:
                    connections += range(start,end)
                else:
                    connections += reversed(range(start,end))
            evaporator.circuits[i].Connections = connections
            
        Evaporator.Circuits[i].Geometry.Connections = evaporator.circuits[i].Connections
        Evaporator.Circuits[i].Geometry.FarBendRadius = 0.01
        Evaporator.Circuits[i].Geometry.FPI = evaporator.circuits[i].Fin_FPI
        Evaporator.Circuits[i].Geometry.Fin_t = evaporator.circuits[i].Fin_t
        Evaporator.Circuits[i].Geometry.FinType = evaporator.circuits[i].Fin_type
        if evaporator.circuits[i].Fin_type == "Wavy":
            Evaporator.Circuits[i].Geometry.Fin_Pd = evaporator.circuits[i].Fin_pd
            Evaporator.Circuits[i].Geometry.Fin_xf = evaporator.circuits[i].Fin_xf
        elif evaporator.circuits[i].Fin_type == "WavyLouvered":
            Evaporator.Circuits[i].Geometry.Fin_Pd = evaporator.circuits[i].Fin_pd
            Evaporator.Circuits[i].Geometry.Fin_xf = evaporator.circuits[i].Fin_xf
        elif evaporator.circuits[i].Fin_type == "Louvered":
            Evaporator.Circuits[i].Geometry.Fin_Lp = evaporator.circuits[i].Fin_Lp
            Evaporator.Circuits[i].Geometry.Fin_Lh = evaporator.circuits[i].Fin_Lh
        elif evaporator.circuits[i].Fin_type == "Slit":
            Evaporator.Circuits[i].Geometry.Fin_Sh = evaporator.circuits[i].Fin_Sh
            Evaporator.Circuits[i].Geometry.Fin_Ss = evaporator.circuits[i].Fin_Ss
            Evaporator.Circuits[i].Geometry.Fin_Sn = evaporator.circuits[i].Fin_Sn
            
        Evaporator.Circuits[i].Thermal.Nsegments = N_segments
        Evaporator.Circuits[i].Thermal.kw = evaporator.circuits[i].Tube_k
        Evaporator.Circuits[i].Thermal.k_fin = evaporator.circuits[i].Fin_k
        Evaporator.Circuits[i].Thermal.FinsOnce = True
        Evaporator.Circuits[i].Thermal.HTC_superheat_Corr = evaporator.circuits[i].superheat_HTC_corr
        Evaporator.Circuits[i].Thermal.HTC_subcool_Corr = evaporator.circuits[i].subcool_HTC_corr
        Evaporator.Circuits[i].Thermal.DP_superheat_Corr = evaporator.circuits[i].superheat_DP_corr
        Evaporator.Circuits[i].Thermal.DP_subcool_Corr = evaporator.circuits[i].subcool_DP_corr
        Evaporator.Circuits[i].Thermal.HTC_2phase_Corr = evaporator.circuits[i]._2phase_HTC_corr
        Evaporator.Circuits[i].Thermal.DP_2phase_Corr = evaporator.circuits[i]._2phase_DP_corr
        Evaporator.Circuits[i].Thermal.DP_Accel_Corr = evaporator.circuits[i]._2phase_charge_corr
        Evaporator.Circuits[i].Thermal.rho_2phase_Corr = evaporator.circuits[i]._2phase_charge_corr
        Evaporator.Circuits[i].Thermal.Air_dry_Corr = evaporator.circuits[i].air_dry_HTC_corr
        Evaporator.Circuits[i].Thermal.Air_wet_Corr = evaporator.circuits[i].air_wet_HTC_corr
        Evaporator.Circuits[i].Thermal.h_r_superheat_tuning = evaporator.circuits[i].superheat_HTC_correction
        Evaporator.Circuits[i].Thermal.h_r_subcooling_tuning = evaporator.circuits[i].subcool_HTC_correction
        Evaporator.Circuits[i].Thermal.h_r_2phase_tuning = evaporator.circuits[i]._2phase_HTC_correction
        Evaporator.Circuits[i].Thermal.h_a_dry_tuning = evaporator.circuits[i].air_dry_HTC_correction
        Evaporator.Circuits[i].Thermal.h_a_wet_tuning = evaporator.circuits[i].air_wet_HTC_correction
        Evaporator.Circuits[i].Thermal.DP_a_dry_tuning = evaporator.circuits[i].air_dry_DP_correction
        Evaporator.Circuits[i].Thermal.DP_a_wet_tuning = evaporator.circuits[i].air_wet_DP_correction
        Evaporator.Circuits[i].Thermal.DP_r_superheat_tuning = evaporator.circuits[i].superheat_DP_correction
        Evaporator.Circuits[i].Thermal.DP_r_subcooling_tuning = evaporator.circuits[i].subcool_DP_correction
        Evaporator.Circuits[i].Thermal.DP_r_2phase_tuning = evaporator.circuits[i]._2phase_DP_correction
        if hasattr(evaporator.circuits[i],'h_a_wet_on'):
            Evaporator.Circuits[i].Thermal.h_a_wet_on = evaporator.circuits[i].h_a_wet_on
        else:
            Evaporator.Circuits[i].Thermal.h_a_wet_on = False
        if hasattr(evaporator.circuits[i],'DP_a_wet_on'):
            Evaporator.Circuits[i].Thermal.DP_a_wet_on = evaporator.circuits[i].DP_a_wet_on
        else:
            Evaporator.Circuits[i].Thermal.DP_a_wet_on = False
    
        if hasattr(evaporator.circuits[i],'sub_HX_values'):
            Evaporator.Circuits[i].Geometry.Sub_HX_matrix = evaporator.circuits[i].sub_HX_values
    
    #calculating inlet condition with the isentropic efficiency
    Tsat_evap, Tsat_cond = get_Tsats(validation_table)
    AS.update(CP.QT_INPUTS,1.0,Tsat_cond)
    psat_cond=AS.p() #[Pa]
    AS.update(CP.QT_INPUTS,1.0,Tsat_evap)
    psat_evap=AS.p() #[Pa]    
    AS.update(CP.PT_INPUTS,psat_cond,Tsat_cond - SC)
    hin_evap = AS.hmass()
    AS.update(CP.PT_INPUTS,psat_evap,Tsat_evap + SH)
    hin_comp = AS.hmass()
    
    #calculating the mass flowrate from target capacity and typical ref effect
    ref_effect = abs(hin_comp - hin_evap)
    mdot_r = abs(Target_capacity / ref_effect)
    
    params={
        'Pin_r': psat_evap,
        'mdot_r': mdot_r,
        'hin_r': hin_evap,
        'AS': AS,
    }
    
    Evaporator.Update(**params)
    try:
        Evaporator.solve()
    except:
        import traceback
        print(traceback.format_exc())
        return (-1,)
        
    # evaporator checks    
    Error = (abs(Evaporator.Results.Q) - Target_capacity) / (Target_capacity)

    DT_sat_max_evap = validation_table["DT_sat_max_evap"] 
    AS.update(CP.PQ_INPUTS,psat_evap,1.0)
    T1 = AS.T()
    AS.update(CP.PQ_INPUTS,psat_evap+Evaporator.Results.DP_r,1.0)
    T2 = AS.T()
    if (abs(Evaporator.Results.Q) - Target_capacity) / (Target_capacity) > Capacity_tolerance:            
        return (0,"Evaporator capacity might be higher than required capacity by about {:.0f}%.".format(Error*100))
    elif (abs(Evaporator.Results.Q) - Target_capacity) / (Target_capacity) < (-1 * Capacity_tolerance):
        return (0,"Evaporator capacity might be lower than required capacity by about {:.0f}%.".format(Error*100))        
    elif (T1 - T2) > DT_sat_max_evap:
        return (0,"Evaporator pressure drop might be too high!")
   
    return (1,Evaporator.Results.TTD)

def check_condenser_capacity_fintube(condenser):
    Condenser = FinTubeHEXClass()
    
    validation_table = condenser.capacity_validation_table
    
    AS = CP.AbstractState("HEOS",validation_table["ref"])

    SH = validation_table["SH"]
    SC = validation_table["SC"]
    COP = validation_table["COP"]
    isen_eff = validation_table["comp_isen_eff"]

    if validation_table["mode"] == 0:
        mode = "AC"
        Target_capacity = validation_table["Capacity"] * (1 + 1/COP)
        evap_capacity = validation_table["Capacity"]
    else:
        mode = "HP"
        Target_capacity = validation_table["Capacity"]
        evap_capacity = validation_table["Capacity"] * (1 - 1/COP)
    
    Capacity_tolerance = validation_table["Capacity_tolerance"]
    
    if condenser.Air_flow_direction in ["Sub Heat Exchanger First","Sub Heat Exchanger Last"]:
        number_of_circuits = condenser.N_series_Circuits + 1
    elif condenser.Air_flow_direction in ["Parallel","Series-Parallel","Series-Counter"]:
        number_of_circuits = condenser.N_series_Circuits
    
    Condenser.name = condenser.name
    if condenser.Accurate == "CoolProp":
        Condenser.Accurate = True
    elif condenser.Accurate == "Psychrolib":
        Condenser.Accurate = False
    Condenser.create_circuits(number_of_circuits)
    for i in range(number_of_circuits):
        N = condenser.circuits[i].N_Circuits
        connection = [i,i+1,i,1.0,N]
        Condenser.connect(*tuple(connection))
    Condenser.Tin_a = validation_table["Tin_a_cond"]
    Condenser.Pin_a = condenser.Air_P
    Condenser.Win_a = validation_table["win_a_cond"]
    if condenser.Air_flow_direction == "Parallel":
        Condenser.Air_sequence = 'parallel'
        Condenser.Air_distribution = condenser.Air_Distribution
    elif condenser.Air_flow_direction == "Series-Parallel":
        Condenser.Air_sequence = 'series_parallel'
    elif condenser.Air_flow_direction == "Series-Counter":
        Condenser.Air_sequence = 'series_counter'
    elif condenser.Air_flow_direction == "Sub Heat Exchanger First":
        Condenser.Air_sequence = 'sub_HX_first'
        Condenser.Air_distribution = condenser.Air_Distribution
    elif condenser.Air_flow_direction == "Sub Heat Exchanger Last":
        Condenser.Air_sequence = 'sub_HX_last'
        Condenser.Air_distribution = condenser.Air_Distribution
    if condenser.model == "Segment by Segment":
        Condenser.model = 'segment'
        N_segments = condenser.N_segments
    elif condenser.model == "Phase by Phase":
        Condenser.model = 'phase'
        N_segments = 1.0
    Condenser.Q_error_tol = condenser.HX_Q_tol
    Condenser.max_iter_per_circuit = condenser.N_iterations
    if condenser.Fan_model == "Fan Efficiency Model":
        Condenser.Fan.model = 'efficiency'
        Condenser.Fan.efficiency = condenser.Fan_model_efficiency_exp
    elif condenser.Fan_model == "Fan Curve Model":
        Condenser.Fan.model = 'curve'
        Condenser.Fan.power_curve = condenser.Fan_model_P_exp
        Condenser.Fan.DP_curve = condenser.Fan_model_DP_exp
    elif condenser.Fan_model == "Fan Power Model":
        Condenser.Fan.model = 'power'
        Condenser.Fan.power_exp = condenser.Fan_model_power_exp
        
    Condenser.Fan.Fan_position = 'after'
    
    if hasattr(condenser,"Vdot_ha"):
        Condenser.Vdot_ha = condenser.Vdot_ha
    else:
        v_spec = HAPropsSI("V","T",Condenser.Tin_a,"W",Condenser.Win_a,"P",Condenser.Pin_a)
        Condenser.Vdot_ha = condenser.mdot_da * v_spec
    
    if condenser.solver == "Mass flow rate solver":
        Condenser.Solver = 'mdot'
    elif condenser.solver == "Pressure drop solver":
        Condenser.Solver = 'dp'            
    
    for i in range(number_of_circuits):
        Condenser.Circuits[i].Geometry.Ntubes_per_bank_per_subcircuit = condenser.circuits[i].N_tube_per_bank
        Condenser.Circuits[i].Geometry.Nbank = condenser.circuits[i].N_bank
        Condenser.Circuits[i].Geometry.OD = condenser.circuits[i].OD
        Condenser.Circuits[i].Geometry.Ltube = condenser.circuits[i].Ltube
        if condenser.circuits[i].Tube_type == "Smooth":
            Condenser.Circuits[i].Geometry.Tubes_type = "Smooth"
            Condenser.Circuits[i].Geometry.ID = condenser.circuits[i].ID
            Condenser.Circuits[i].Geometry.e_D = condenser.circuits[i].e_D
        elif condenser.circuits[i].Tube_type == "Microfin":
            Condenser.Circuits[i].Geometry.Tubes_type = "Microfin"
            Condenser.Circuits[i].Geometry.t = condenser.circuits[i].Tube_t
            Condenser.Circuits[i].Geometry.beta = condenser.circuits[i].Tube_beta
            Condenser.Circuits[i].Geometry.e = condenser.circuits[i].Tube_e
            Condenser.Circuits[i].Geometry.d = condenser.circuits[i].Tube_d
            Condenser.Circuits[i].Geometry.gama = condenser.circuits[i].Tube_gamma
            Condenser.Circuits[i].Geometry.n = condenser.circuits[i].Tube_n
        Condenser.Circuits[i].Geometry.Staggering = condenser.circuits[i].Staggering
        Condenser.Circuits[i].Geometry.Pl = condenser.circuits[i].Pl
        Condenser.Circuits[i].Geometry.Pt = condenser.circuits[i].Pt
        
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
            
        Condenser.Circuits[i].Geometry.Connections = condenser.circuits[i].Connections
        Condenser.Circuits[i].Geometry.FarBendRadius = 0.01
        Condenser.Circuits[i].Geometry.FPI = condenser.circuits[i].Fin_FPI
        Condenser.Circuits[i].Geometry.Fin_t = condenser.circuits[i].Fin_t
        Condenser.Circuits[i].Geometry.FinType = condenser.circuits[i].Fin_type
        if condenser.circuits[i].Fin_type == "Wavy":
            Condenser.Circuits[i].Geometry.Fin_Pd = condenser.circuits[i].Fin_pd
            Condenser.Circuits[i].Geometry.Fin_xf = condenser.circuits[i].Fin_xf
        elif condenser.circuits[i].Fin_type == "WavyLouvered":
            Condenser.Circuits[i].Geometry.Fin_Pd = condenser.circuits[i].Fin_pd
            Condenser.Circuits[i].Geometry.Fin_xf = condenser.circuits[i].Fin_xf
        elif condenser.circuits[i].Fin_type == "Louvered":
            Condenser.Circuits[i].Geometry.Fin_Lp = condenser.circuits[i].Fin_Lp
            Condenser.Circuits[i].Geometry.Fin_Lh = condenser.circuits[i].Fin_Lh
        elif condenser.circuits[i].Fin_type == "Slit":
            Condenser.Circuits[i].Geometry.Fin_Sh = condenser.circuits[i].Fin_Sh
            Condenser.Circuits[i].Geometry.Fin_Ss = condenser.circuits[i].Fin_Ss
            Condenser.Circuits[i].Geometry.Fin_Sn = condenser.circuits[i].Fin_Sn
            
        Condenser.Circuits[i].Thermal.Nsegments = N_segments
        Condenser.Circuits[i].Thermal.kw = condenser.circuits[i].Tube_k
        Condenser.Circuits[i].Thermal.k_fin = condenser.circuits[i].Fin_k
        Condenser.Circuits[i].Thermal.FinsOnce = True
        Condenser.Circuits[i].Thermal.HTC_superheat_Corr = condenser.circuits[i].superheat_HTC_corr
        Condenser.Circuits[i].Thermal.HTC_subcool_Corr = condenser.circuits[i].subcool_HTC_corr
        Condenser.Circuits[i].Thermal.DP_superheat_Corr = condenser.circuits[i].superheat_DP_corr
        Condenser.Circuits[i].Thermal.DP_subcool_Corr = condenser.circuits[i].subcool_DP_corr
        Condenser.Circuits[i].Thermal.HTC_2phase_Corr = condenser.circuits[i]._2phase_HTC_corr
        Condenser.Circuits[i].Thermal.DP_2phase_Corr = condenser.circuits[i]._2phase_DP_corr
        Condenser.Circuits[i].Thermal.DP_Accel_Corr = condenser.circuits[i]._2phase_charge_corr
        Condenser.Circuits[i].Thermal.rho_2phase_Corr = condenser.circuits[i]._2phase_charge_corr
        Condenser.Circuits[i].Thermal.Air_dry_Corr = condenser.circuits[i].air_dry_HTC_corr
        Condenser.Circuits[i].Thermal.Air_wet_Corr = condenser.circuits[i].air_wet_HTC_corr
        Condenser.Circuits[i].Thermal.h_r_superheat_tuning = condenser.circuits[i].superheat_HTC_correction
        Condenser.Circuits[i].Thermal.h_r_subcooling_tuning = condenser.circuits[i].subcool_HTC_correction
        Condenser.Circuits[i].Thermal.h_r_2phase_tuning = condenser.circuits[i]._2phase_HTC_correction
        Condenser.Circuits[i].Thermal.h_a_dry_tuning = condenser.circuits[i].air_dry_HTC_correction
        Condenser.Circuits[i].Thermal.h_a_wet_tuning = condenser.circuits[i].air_wet_HTC_correction
        Condenser.Circuits[i].Thermal.DP_a_dry_tuning = condenser.circuits[i].air_dry_DP_correction
        Condenser.Circuits[i].Thermal.DP_a_wet_tuning = condenser.circuits[i].air_wet_DP_correction
        Condenser.Circuits[i].Thermal.DP_r_superheat_tuning = condenser.circuits[i].superheat_DP_correction
        Condenser.Circuits[i].Thermal.DP_r_subcooling_tuning = condenser.circuits[i].subcool_DP_correction
        Condenser.Circuits[i].Thermal.DP_r_2phase_tuning = condenser.circuits[i]._2phase_DP_correction
        if hasattr(condenser.circuits[i],'h_a_wet_on'):
            Condenser.Circuits[i].Thermal.h_a_wet_on = condenser.circuits[i].h_a_wet_on
        else:
            Condenser.Circuits[i].Thermal.h_a_wet_on = False
        if hasattr(condenser.circuits[i],'DP_a_wet_on'):
            Condenser.Circuits[i].Thermal.DP_a_wet_on = condenser.circuits[i].DP_a_wet_on
        else:
            Condenser.Circuits[i].Thermal.DP_a_wet_on = False
    
        if hasattr(condenser.circuits[i],'sub_HX_values'):
            Condenser.Circuits[i].Geometry.Sub_HX_matrix = condenser.circuits[i].sub_HX_values
    
    #calculating inlet condition with the isentropic efficiency
    Tsat_evap, Tsat_cond = get_Tsats(validation_table)
    AS.update(CP.QT_INPUTS,1.0,Tsat_cond)
    psat_cond=AS.p() #[Pa]
    AS.update(CP.QT_INPUTS,1.0,Tsat_evap)
    psat_evap=AS.p() #[Pa]    
    AS.update(CP.PT_INPUTS,psat_evap,Tsat_evap + SH)
    hin_comp = AS.hmass()
    sin_comp = AS.smass()
    AS.update(CP.PSmass_INPUTS,psat_cond,sin_comp)
    hout_comp_isen = AS.hmass()
    hin_cond = hin_comp + (hout_comp_isen - hin_comp) / isen_eff
    
    #calculating the mass flowrate from target capacity and typical ref effect
    AS.update(CP.PT_INPUTS,psat_cond,Tsat_cond - SC)
    hout_cond = AS.hmass()
    ref_effect = abs(hin_comp - hout_cond)
    mdot_r = abs(evap_capacity / ref_effect)
    
    params={
        'Pin_r': psat_cond,
        'mdot_r': mdot_r,
        'hin_r': hin_cond,
        'AS': AS,
    }
    
    Condenser.Update(**params)
    try:
        Condenser.solve()
    except:
        import traceback
        print(traceback.format_exc())
        return (-1,)
        
    # condenser checks
    DT_sat_max_cond = validation_table["DT_sat_max_cond"] 
    AS.update(CP.PQ_INPUTS,psat_cond,1.0)
    T1 = AS.T()
    AS.update(CP.PQ_INPUTS,psat_cond+Condenser.Results.DP_r,1.0)
    T2 = AS.T()

    Error = (abs(Condenser.Results.Q) - Target_capacity) / (Target_capacity)
    if (abs(Condenser.Results.Q) - Target_capacity) / (Target_capacity) > Capacity_tolerance:            
        return (0,"Condenser capacity might be higher than required capacity by about {:.0f}%.".format(Error*100))
    elif (abs(Condenser.Results.Q) - Target_capacity) / (Target_capacity) < (-1 * Capacity_tolerance):
        return (0,"Condenser capacity might be lower than required capacity by about {:.0f}%.".format(Error*100))
    elif (T1 - T2) > DT_sat_max_cond:
        return (0,"Condenser pressure drop might be too high!")
    
    return (1,Condenser.Results.TTD)

def check_evaporator_capacity_microchannel(evaporator):
    Evaporator = MicroChannelHEXClass()
    
    validation_table = evaporator.capacity_validation_table
    
    AS = CP.AbstractState("HEOS",validation_table["ref"])

    SH = validation_table["SH"]
    SC = validation_table["SC"]
    COP = validation_table["COP"]
    isen_eff = validation_table["comp_isen_eff"]

    if validation_table["mode"] == 0:
        mode = "AC"
        Target_capacity = validation_table["Capacity"]
    else:
        mode = "HP"
        Target_capacity = validation_table["Capacity"] * (1 - 1/COP)
    
    Capacity_tolerance = validation_table["Capacity_tolerance"]
    
    Evaporator.name = evaporator.name
    if evaporator.Accurate == "CoolProp":
        Evaporator.Accurate = True
    elif evaporator.Accurate == "Psychrolib":
        Evaporator.Accurate = False
    Evaporator.Tin_a = validation_table["Tin_a_evap"]
    Evaporator.Pin_a = evaporator.Air_P
    Evaporator.Win_a = validation_table["win_a_evap"]
    if evaporator.model == "Segment by Segment":
        Evaporator.model = 'segment'
        Evaporator.Thermal.Nsegments = evaporator.N_segments
    elif evaporator.model == "Phase by Phase":
        Evaporator.model = 'phase'
        Evaporator.Thermal.Nsegments = 1
    Evaporator.Q_error_tol = evaporator.HX_Q_tol
    Evaporator.max_iter_per_circuit = evaporator.N_iterations
    if evaporator.Fan_model == "Fan Efficiency Model":
        Evaporator.Fan.model = 'efficiency'
        Evaporator.Fan.efficiency = evaporator.Fan_model_efficiency_exp
    elif evaporator.Fan_model == "Fan Curve Model":
        Evaporator.Fan.model = 'curve'
        Evaporator.Fan.power_curve = evaporator.Fan_model_P_exp
        Evaporator.Fan.DP_curve = evaporator.Fan_model_DP_exp
    elif evaporator.Fan_model == "Fan Power Model":
        Evaporator.Fan.model = 'power'
        Evaporator.Fan.power_exp = evaporator.Fan_model_power_exp

    Evaporator.Fan.Fan_position = 'after'

    Evaporator.Geometry.N_tube_per_bank_per_pass = evaporator.Circuiting.bank_passes
    if evaporator.Geometry.Fin_on_side_index:
        Evaporator.Geometry.Fin_rows = evaporator.N_tube_per_bank + 1
    else:
        Evaporator.Geometry.Fin_rows = evaporator.N_tube_per_bank - 1

    Evaporator.Geometry.T_L = evaporator.Geometry.T_l
    Evaporator.Geometry.T_w = evaporator.Geometry.T_w
    Evaporator.Geometry.T_h = evaporator.Geometry.T_h
    Evaporator.Geometry.T_s = evaporator.Geometry.T_s
    Evaporator.Geometry.P_shape = evaporator.Geometry.port_shape
    Evaporator.Geometry.P_end = evaporator.Geometry.T_end
    Evaporator.Geometry.P_a = evaporator.Geometry.port_a_dim
    if evaporator.Geometry.port_shape in ['Rectangle', 'Triangle']:
        Evaporator.Geometry.P_b = evaporator.Geometry.port_b_dim
    Evaporator.Geometry.N_port = evaporator.Geometry.N_ports
    Evaporator.Geometry.Enhanced = False
    Evaporator.Geometry.FinType = evaporator.Geometry.Fin_type
    if evaporator.Geometry.Fin_type == "Louvered":
        Evaporator.Geometry.Fin_Llouv = evaporator.Geometry.Fin_llouv
        Evaporator.Geometry.Fin_alpha = evaporator.Geometry.Fin_lalpha
        Evaporator.Geometry.Fin_Lp = evaporator.Geometry.Fin_lp
        
    Evaporator.Geometry.Fin_t = evaporator.Geometry.Fin_t
    Evaporator.Geometry.Fin_L = evaporator.Geometry.Fin_l
    Evaporator.Geometry.FPI = evaporator.Geometry.Fin_FPI
    Evaporator.Geometry.e_D = evaporator.Geometry.e_D
    Evaporator.Geometry.Header_CS_Type = evaporator.Geometry.header_shape
    Evaporator.Geometry.Header_dim_a = evaporator.Geometry.header_a_dim
    if evaporator.Geometry.header_shape in ["Rectangle"]:
        Evaporator.Geometry.Header_dim_b = evaporator.Geometry.header_b_dim
    Evaporator.Geometry.Header_length = evaporator.Geometry.header_height

    if hasattr(evaporator,"Vdot_ha"):
        Evaporator.Vdot_ha = evaporator.Vdot_ha
    else:
        v_spec = HAPropsSI("V","T",Evaporator.Tin_a,"W",Evaporator.Win_a,"P",Evaporator.Pin_a)
        Evaporator.Vdot_ha = evaporator.mdot_da * v_spec
    Evaporator.Thermal.k_fin = evaporator.Geometry.Fin_k
    Evaporator.Thermal.kw = evaporator.Geometry.Tube_k
    Evaporator.Thermal.Headers_DP_r = evaporator.Geometry.Header_DP
    Evaporator.Thermal.FinsOnce = True
    Evaporator.Thermal.HTC_superheat_Corr = evaporator.superheat_HTC_corr
    Evaporator.Thermal.HTC_subcool_Corr = evaporator.subcool_HTC_corr
    Evaporator.Thermal.DP_superheat_Corr = evaporator.superheat_DP_corr
    Evaporator.Thermal.DP_subcool_Corr = evaporator.subcool_DP_corr
    Evaporator.Thermal.HTC_2phase_Corr = evaporator._2phase_HTC_corr
    Evaporator.Thermal.DP_2phase_Corr = evaporator._2phase_DP_corr
    Evaporator.Thermal.DP_Accel_Corr = evaporator._2phase_charge_corr
    Evaporator.Thermal.rho_2phase_Corr = evaporator._2phase_charge_corr
    Evaporator.Thermal.Air_dry_Corr = evaporator.air_dry_HTC_corr
    Evaporator.Thermal.Air_wet_Corr = evaporator.air_wet_HTC_corr
    Evaporator.Thermal.h_r_superheat_tuning = evaporator.superheat_HTC_correction
    Evaporator.Thermal.h_r_subcooling_tuning = evaporator.subcool_HTC_correction
    Evaporator.Thermal.h_r_2phase_tuning = evaporator._2phase_HTC_correction
    Evaporator.Thermal.h_a_dry_tuning = evaporator.air_dry_HTC_correction
    Evaporator.Thermal.h_a_wet_tuning = evaporator.air_wet_HTC_correction
    Evaporator.Thermal.DP_a_dry_tuning = evaporator.air_dry_DP_correction
    Evaporator.Thermal.DP_a_wet_tuning = evaporator.air_wet_DP_correction
    Evaporator.Thermal.DP_r_superheat_tuning = evaporator.superheat_DP_correction
    Evaporator.Thermal.DP_r_subcooling_tuning = evaporator.subcool_DP_correction
    Evaporator.Thermal.DP_r_2phase_tuning = evaporator._2phase_DP_correction
    if hasattr(evaporator,'h_a_wet_on'):
        Evaporator.Thermal.h_a_wet_on = evaporator.h_a_wet_on
    else:
        Evaporator.Thermal.h_a_wet_on = False
    if hasattr(evaporator,'DP_a_wet_on'):
        Evaporator.Thermal.DP_a_wet_on = evaporator.DP_a_wet_on
    else:
        Evaporator.Thermal.DP_a_wet_on = False
    
    #calculating inlet condition with the isentropic efficiency
    Tsat_evap, Tsat_cond = get_Tsats(validation_table)
    AS.update(CP.QT_INPUTS,1.0,Tsat_cond)
    psat_cond=AS.p() #[Pa]
    AS.update(CP.QT_INPUTS,1.0,Tsat_evap)
    psat_evap=AS.p() #[Pa]    
    AS.update(CP.PT_INPUTS,psat_cond,Tsat_cond - SC)
    hin_evap = AS.hmass()
    AS.update(CP.PT_INPUTS,psat_evap,Tsat_evap + SH)
    hin_comp = AS.hmass()
    
    #calculating the mass flowrate from target capacity and typical ref effect
    ref_effect = abs(hin_comp - hin_evap)
    mdot_r = abs(Target_capacity / ref_effect)
    
    params={
        'Pin_r': psat_evap,
        'mdot_r': mdot_r,
        'hin_r': hin_evap,
        'AS': AS,
    }
    
    Evaporator.Update(**params)
    try:
        Evaporator.solve()
    except:
        import traceback
        print(traceback.format_exc())
        return (-1,)
        
    # evaporator checks
    Error = (abs(Evaporator.Results.Q) - Target_capacity) / (Target_capacity)

    DT_sat_max_evap = validation_table["DT_sat_max_evap"] 
    AS.update(CP.PQ_INPUTS,psat_evap,1.0)
    T1 = AS.T()
    AS.update(CP.PQ_INPUTS,psat_evap+Evaporator.Results.DP_r,1.0)
    T2 = AS.T()

    if (abs(Evaporator.Results.Q) - Target_capacity) / (Target_capacity) > Capacity_tolerance:            
        return (0,"Evaporator capacity might be higher than required capacity by about {:.0f}%.".format(Error*100))
    elif (abs(Evaporator.Results.Q) - Target_capacity) / (Target_capacity) < (-1 * Capacity_tolerance):
        return (0,"Evaporator capacity might be lower than required capacity by about {:.0f}%.".format(Error*100))
    elif (T1 - T2) > DT_sat_max_evap:
        return (0,"Evaporator pressure drop might be too high!")
    
    return (1,Evaporator.Results.TTD)

def check_condenser_capacity_microchannel(condenser):
    Condenser = MicroChannelHEXClass()
    
    validation_table = condenser.capacity_validation_table
    
    AS = CP.AbstractState("HEOS",validation_table["ref"])

    SH = validation_table["SH"]
    SC = validation_table["SC"]
    COP = validation_table["COP"]
    isen_eff = validation_table["comp_isen_eff"]

    if validation_table["mode"] == 0:
        mode = "AC"
        Target_capacity = validation_table["Capacity"] * (1 + 1/COP)
        evap_capacity = validation_table["Capacity"]
    else:
        mode = "HP"
        Target_capacity = validation_table["Capacity"]
        evap_capacity = validation_table["Capacity"] * (1 - 1/COP)
    
    Capacity_tolerance = validation_table["Capacity_tolerance"]
    
    Condenser.name = condenser.name
    if condenser.Accurate == "CoolProp":
        Condenser.Accurate = True
    elif condenser.Accurate == "Psychrolib":
        Condenser.Accurate = False
    Condenser.Tin_a = validation_table["Tin_a_cond"]
    Condenser.Pin_a = condenser.Air_P
    Condenser.Win_a = validation_table["win_a_cond"]
    if condenser.model == "Segment by Segment":
        Condenser.model = 'segment'
        Condenser.Thermal.Nsegments = condenser.N_segments
    elif condenser.model == "Phase by Phase":
        Condenser.model = 'phase'
        Condenser.Thermal.Nsegments = 1
    Condenser.Q_error_tol = condenser.HX_Q_tol
    Condenser.max_iter_per_circuit = condenser.N_iterations
    if condenser.Fan_model == "Fan Efficiency Model":
        Condenser.Fan.model = 'efficiency'
        Condenser.Fan.efficiency = condenser.Fan_model_efficiency_exp
    elif condenser.Fan_model == "Fan Curve Model":
        Condenser.Fan.model = 'curve'
        Condenser.Fan.power_curve = condenser.Fan_model_P_exp
        Condenser.Fan.DP_curve = condenser.Fan_model_DP_exp
    elif condenser.Fan_model == "Fan Power Model":
        Condenser.Fan.model = 'power'
        Condenser.Fan.power_exp = condenser.Fan_model_power_exp

    Condenser.Fan.Fan_position = 'after'

    Condenser.Geometry.N_tube_per_bank_per_pass = condenser.Circuiting.bank_passes
    if condenser.Geometry.Fin_on_side_index:
        Condenser.Geometry.Fin_rows = condenser.N_tube_per_bank + 1
    else:
        Condenser.Geometry.Fin_rows = condenser.N_tube_per_bank - 1

    Condenser.Geometry.T_L = condenser.Geometry.T_l
    Condenser.Geometry.T_w = condenser.Geometry.T_w
    Condenser.Geometry.T_h = condenser.Geometry.T_h
    Condenser.Geometry.T_s = condenser.Geometry.T_s
    Condenser.Geometry.P_shape = condenser.Geometry.port_shape
    Condenser.Geometry.P_end = condenser.Geometry.T_end
    Condenser.Geometry.P_a = condenser.Geometry.port_a_dim
    if condenser.Geometry.port_shape in ['Rectangle', 'Triangle']:
        Condenser.Geometry.P_b = condenser.Geometry.port_b_dim
    Condenser.Geometry.N_port = condenser.Geometry.N_ports
    Condenser.Geometry.Enhanced = False
    Condenser.Geometry.FinType = condenser.Geometry.Fin_type
    if condenser.Geometry.Fin_type == "Louvered":
        Condenser.Geometry.Fin_Llouv = condenser.Geometry.Fin_llouv
        Condenser.Geometry.Fin_alpha = condenser.Geometry.Fin_lalpha
        Condenser.Geometry.Fin_Lp = condenser.Geometry.Fin_lp
        
    Condenser.Geometry.Fin_t = condenser.Geometry.Fin_t
    Condenser.Geometry.Fin_L = condenser.Geometry.Fin_l
    Condenser.Geometry.FPI = condenser.Geometry.Fin_FPI
    Condenser.Geometry.e_D = condenser.Geometry.e_D
    Condenser.Geometry.Header_CS_Type = condenser.Geometry.header_shape
    Condenser.Geometry.Header_dim_a = condenser.Geometry.header_a_dim
    if condenser.Geometry.header_shape in ["Rectangle"]:
        Condenser.Geometry.Header_dim_b = condenser.Geometry.header_b_dim
    Condenser.Geometry.Header_length = condenser.Geometry.header_height

    if hasattr(condenser,"Vdot_ha"):
        Condenser.Vdot_ha = condenser.Vdot_ha
    else:
        v_spec = HAPropsSI("V","T",Condenser.Tin_a,"W",Condenser.Win_a,"P",Condenser.Pin_a)
        Condenser.Vdot_ha = condenser.mdot_da * v_spec
    Condenser.Thermal.k_fin = condenser.Geometry.Fin_k
    Condenser.Thermal.kw = condenser.Geometry.Tube_k
    Condenser.Thermal.Headers_DP_r = condenser.Geometry.Header_DP
    Condenser.Thermal.FinsOnce = True
    Condenser.Thermal.HTC_superheat_Corr = condenser.superheat_HTC_corr
    Condenser.Thermal.HTC_subcool_Corr = condenser.subcool_HTC_corr
    Condenser.Thermal.DP_superheat_Corr = condenser.superheat_DP_corr
    Condenser.Thermal.DP_subcool_Corr = condenser.subcool_DP_corr
    Condenser.Thermal.HTC_2phase_Corr = condenser._2phase_HTC_corr
    Condenser.Thermal.DP_2phase_Corr = condenser._2phase_DP_corr
    Condenser.Thermal.DP_Accel_Corr = condenser._2phase_charge_corr
    Condenser.Thermal.rho_2phase_Corr = condenser._2phase_charge_corr
    Condenser.Thermal.Air_dry_Corr = condenser.air_dry_HTC_corr
    Condenser.Thermal.Air_wet_Corr = condenser.air_wet_HTC_corr
    Condenser.Thermal.h_r_superheat_tuning = condenser.superheat_HTC_correction
    Condenser.Thermal.h_r_subcooling_tuning = condenser.subcool_HTC_correction
    Condenser.Thermal.h_r_2phase_tuning = condenser._2phase_HTC_correction
    Condenser.Thermal.h_a_dry_tuning = condenser.air_dry_HTC_correction
    Condenser.Thermal.h_a_wet_tuning = condenser.air_wet_HTC_correction
    Condenser.Thermal.DP_a_dry_tuning = condenser.air_dry_DP_correction
    Condenser.Thermal.DP_a_wet_tuning = condenser.air_wet_DP_correction
    Condenser.Thermal.DP_r_superheat_tuning = condenser.superheat_DP_correction
    Condenser.Thermal.DP_r_subcooling_tuning = condenser.subcool_DP_correction
    Condenser.Thermal.DP_r_2phase_tuning = condenser._2phase_DP_correction
    if hasattr(condenser,'h_a_wet_on'):
        Condenser.Thermal.h_a_wet_on = condenser.h_a_wet_on
    else:
        Condenser.Thermal.h_a_wet_on = False
    if hasattr(condenser,'DP_a_wet_on'):
        Condenser.Thermal.DP_a_wet_on = condenser.DP_a_wet_on
    else:
        Condenser.Thermal.DP_a_wet_on = False
    
    #calculating inlet condition with the isentropic efficiency
    Tsat_evap, Tsat_cond = get_Tsats(validation_table)
    AS.update(CP.QT_INPUTS,1.0,Tsat_cond)
    psat_cond=AS.p() #[Pa]
    AS.update(CP.QT_INPUTS,1.0,Tsat_evap)
    psat_evap=AS.p() #[Pa]    
    AS.update(CP.PT_INPUTS,psat_evap,Tsat_evap + SH)
    hin_comp = AS.hmass()
    sin_comp = AS.smass()
    AS.update(CP.PSmass_INPUTS,psat_cond,sin_comp)
    hout_comp_isen = AS.hmass()
    hin_cond = hin_comp + (hout_comp_isen - hin_comp) / isen_eff
    
    #calculating the mass flowrate from target capacity and typical ref effect
    AS.update(CP.PT_INPUTS,psat_cond,Tsat_cond - SC)
    hout_cond = AS.hmass()
    ref_effect = abs(hin_comp - hout_cond)
    mdot_r = abs(evap_capacity / ref_effect)
    
    params={
        'Pin_r': psat_cond,
        'mdot_r': mdot_r,
        'hin_r': hin_cond,
        'AS': AS,
    }
    
    Condenser.Update(**params)
    try:
        Condenser.solve()
    except:
        import traceback
        print(traceback.format_exc())
        return (-1,)
        
    # condenser checks
    Error = (abs(Condenser.Results.Q) - Target_capacity) / (Target_capacity)

    DT_sat_max_cond = validation_table["DT_sat_max_cond"] 
    AS.update(CP.PQ_INPUTS,psat_cond,1.0)
    T1 = AS.T()
    AS.update(CP.PQ_INPUTS,psat_cond+Condenser.Results.DP_r,1.0)
    T2 = AS.T()

    Error = (abs(Condenser.Results.Q) - Target_capacity) / (Target_capacity)
    if (abs(Condenser.Results.Q) - Target_capacity) / (Target_capacity) > Capacity_tolerance:            
        return (0,"Condenser capacity might be higher than required capacity by about {:.0f}%.".format(Error*100))
    elif (abs(Condenser.Results.Q) - Target_capacity) / (Target_capacity) < (-1 * Capacity_tolerance):
        return (0,"Condenser capacity might be lower than required capacity by about {:.0f}%.".format(Error*100))

    if (abs(Condenser.Results.Q) - Target_capacity) / (Target_capacity) > Capacity_tolerance:            
        return (0,"Condenser capacity might be higher than required capacity by about {:.0f}%.".format(Error*100))
    elif (abs(Condenser.Results.Q) - Target_capacity) / (Target_capacity) < (-1 * Capacity_tolerance):
        return (0,"Condenser capacity might be lower than required capacity by about {:.0f}%.".format(Error*100))
    elif (T1 - T2) > DT_sat_max_cond:
        return (0,"Condenser pressure drop might be too high!")
    
    return (1,Condenser.Results.TTD)

def check_compressor_AHRI(comp):
    if comp.Comp_vol == 0:
        return (0,"Compressor displacement volume can not be zero")

    if comp.Comp_speed == 0:
        return (0,"Compressor operating speed can not be zero")

    if comp.Comp_ratio_M == 0:
        return (0,"Compressor mass flowrate scale ratio can not be zero")

    if comp.Comp_ratio_P == 0:
        return (0,"Compressor power scale ratio can not be zero")
    
    if comp.std_type == 0:
        if comp.std_sh == 0:
            return (0,"Compressor standard superheat in compressor AHRI model can not be zero")

    for i, speed in enumerate(comp.speeds):
        if speed  == 0:
            return (0,"Compressor speed number "+str(i+1)+" in compressor AHRI model can not be zero")        
    
    if hasattr(comp,"capacity_validation_table"):
        try:
            result = check_compressor_capacity(comp)
            if not result[0]:
                return (2,result[1])
        except:
            import traceback
            print(traceback.format_exc())
            pass
    
    return (1,"")

def check_compressor_physics(comp):
    if comp.Comp_vol == 0:
        return (0,"Compressor displacement volume can not be zero")

    if comp.Comp_speed == 0:
        return (0,"Compressor operating speed can not be zero")

    if comp.Comp_ratio_M == 0:
        return (0,"Compressor mass flowrate scale ratio can not be zero")

    if comp.Comp_ratio_P == 0:
        return (0,"Compressor power scale ratio can not be zero")

    if hasattr(comp,"capacity_validation_table"):
        try:
            result = check_compressor_capacity(comp)
            if not result[0]:
                return (2,result[1])
        except:
            import traceback
            print(traceback.format_exc())
            pass
            
    return (1,"")

def check_compressor_map(comp):
    if comp.Comp_vol == 0:
        return (0,"Compressor displacement volume can not be zero")

    if comp.Comp_speed == 0:
        return (0,"Compressor operating speed can not be zero")

    if comp.Comp_ratio_M == 0:
        return (0,"Compressor mass flowrate scale ratio can not be zero")

    if comp.Comp_ratio_P == 0:
        return (0,"Compressor power scale ratio can not be zero")
    
    if comp.map_data.std_type == 0:
        if comp.map_data.std_sh == 0:
            return (0,"Compressor standard superheat in compressor map model can not be zero")

    for i, speed in enumerate(comp.map_data.Speeds):
        if speed  == 0:
            return (0,"Compressor speed number "+str(i+1)+" in compressor map model can not be zero")        

    if hasattr(comp,"capacity_validation_table"):
        try:
            result = check_compressor_capacity(comp)
            if not result[0]:
                return (2,result[1])
        except:
            import traceback
            print(traceback.format_exc())
            pass
    
    return (1,"")

def check_Fintube(HX):
    if hasattr(HX,"Vdot_ha"):
        if HX.Vdot_ha == 0:
            return (0,"Inlet humid air volumetric flowrate can not be zero")
    if hasattr(HX,"mdot_da"):
        if HX.mdot_da == 0:
            return (0,"Inlet dry air mass flowrate can not be zero")

    if HX.Air_T <= 0:
        return (0,"Inlet air temperature can not be or below 0 kelvin")

    # if HX.Air_flow_direction == "Parallel":
    #     for ratio in HX.Air_distribution:
    #         if ratio <= 0:
    #             return (0,"Air distribution flow rate fraction must be positive number")

    if HX.Air_P == 0:
        return (0,"Inlet air pressure can not be zero")

    if hasattr(HX,"HX_DP_tol"):
        if HX.HX_DP_tol <=0:
            return (0,"Maximum pressure drop error can not be zero")
    
    for i,circuit in enumerate(HX.circuits):
        if circuit.OD == 0:
            return (0,"Tube outer diameter of circuit "+str(i+1)+" can not be zero")
        
        if circuit.Tube_type_index == 0:
            if circuit.ID == 0:
                return (0,"Tube inner diameter of circuit "+str(i+1)+" can not be zero")
        else:
            if circuit.Tube_t == 0:
                return (0,"Tube total thickness of circuit "+str(i+1)+" can not be zero")

            if circuit.Tube_d == 0:
                return (0,"Tube fin base width of circuit "+str(i+1)+" can not be zero")

            if circuit.Tube_e == 0:
                return (0,"Tube fin height of circuit "+str(i+1)+" can not be zero")

            if circuit.Tube_n == 0:
                return (0,"Tube number of fins of circuit "+str(i+1)+" can not be zero")

            if circuit.Tube_gamma == 0:
                return (0,"Tube fin apex angle of circuit "+str(i+1)+" can not be zero")

            if circuit.Tube_beta == 0:
                return (0,"Tube fin swirl angle of circuit "+str(i+1)+" can not be zero")

            if not 0 < circuit.Tube_gamma < 180:
                return (0,"Tube fin apex angle of circuit "+str(i+1)+" should be between 0 and 180 degrees")

            if not 0 < circuit.Tube_beta < 90:
                return (0,"Tube fin swirl angle of circuit "+str(i+1)+" should be between 0 and 90 degrees")

            if circuit.Tube_t  <= circuit.Tube_e:
                return (0,"Tube total thickness of circuit "+str(i+1)+" can not be less than tube fin thickness")

        if circuit.N_tube_per_bank == 0:
            return (0,"Number of tubes per bank of circuit "+str(i+1)+" can not be zero")

        if circuit.N_bank == 0:
            return (0,"Number of banks of circuit "+str(i+1)+" can not be zero")

        if circuit.Pl <= circuit.OD:
            return (0,"Tube longitudinal pitch of circuit "+str(i+1)+" can not be or less than outer diameter")

        if circuit.Pt <= circuit.OD:
            return (0,"Tube transverse pitch of circuit "+str(i+1)+" can not be or less than outer diameter")

        if circuit.Fin_t == 0:
            return (0,"Fin thickness of circuit "+str(i+1)+" can not be zero")

        if circuit.Fin_FPI == 0:
            return (0,"Fin FPI of circuit "+str(i+1)+" can not be zero")
        
        if circuit.Fin_type == "Wavy":
            if circuit.Fin_xf == 0:
                return (0,"Wavy fin (xf) of circuit "+str(i+1)+" can not be zero")

            if circuit.Fin_pd == 0:
                return (0,"Wavy fin (pd) of circuit "+str(i+1)+" can not be zero")
        
        elif circuit.Fin_type == "Slit":
            if circuit.Fin_Sh == 0:
                return (0,"Slot fin (Sh) of circuit "+str(i+1)+" can not be zero")

            if circuit.Fin_Ss == 0:
                return (0,"Slit fin (Ss) of circuit "+str(i+1)+" can not be zero")

            if circuit.Fin_Sn == 0:
                return (0,"Slit fin (Sn) of circuit "+str(i+1)+" can not be zero")
            
        elif circuit.Fin_type == "Louvered":
            if circuit.Fin_Lp == 0:
                return (0,"Louvered fin (Lp) of circuit "+str(i+1)+" can not be zero")

            if circuit.Fin_Lh == 0:
                return (0,"Louvered fin (Lh) of circuit "+str(i+1)+" can not be zero")

        elif circuit.Fin_type == "WavyLouvered":
            if circuit.Fin_xf == 0:
                return (0,"Wavy-Louvered fin (xf) of circuit "+str(i+1)+" can not be zero")

            if circuit.Fin_pd == 0:
                return (0,"Wavy-Louvered fin (pd) of circuit "+str(i+1)+" can not be zero")
        
        if circuit.Tube_k == 0:
            return (0,"Tube thermal conductivity of circuit "+str(i+1)+" can not be zero")

        if circuit.Fin_k == 0:
            return (0,"Fin thermal conductivity of circuit "+str(i+1)+" can not be zero")
        
        if circuit.superheat_HTC_correction == 0:
            return (0,"Superheat HTC correction factor of circuit "+str(i+1)+" can not be zero")

        if circuit.superheat_DP_correction == 0:
            return (0,"Superheat pressure drop correction factor of circuit "+str(i+1)+" can not be zero")

        if circuit._2phase_HTC_correction == 0:
            return (0,"Two-phase HTC correction factor of circuit "+str(i+1)+" can not be zero")

        if circuit._2phase_DP_correction == 0:
            return (0,"Two-phase pressure drop correction factor of circuit "+str(i+1)+" can not be zero")

        if circuit.subcool_HTC_correction == 0:
            return (0,"Subcool HTC correction factor of circuit "+str(i+1)+" can not be zero")

        if circuit.subcool_DP_correction == 0:
            return (0,"Subcool pressure drop correction factor of circuit "+str(i+1)+" can not be zero")

        if circuit.air_dry_HTC_correction == 0:
            return (0,"Air dry HTC correction factor of circuit "+str(i+1)+" can not be zero")

        if circuit.air_dry_DP_correction == 0:
            return (0,"Air dry pressure correction factor of circuit "+str(i+1)+" can not be zero")

        if circuit.air_wet_HTC_correction == 0:
            return (0,"Air wet HTC correction factor of circuit "+str(i+1)+" can not be zero")

        if circuit.air_wet_DP_correction == 0:
            return (0,"Air wet pressure correction factor of circuit "+str(i+1)+" can not be zero")
        
    if hasattr(HX,"capacity_validation_table"):
        try:
            if HX.capacity_validation_table["HX_type"] == "evap":
                result = check_evaporator_capacity_fintube(HX)
            elif HX.capacity_validation_table["HX_type"] == "cond":
                result = check_condenser_capacity_fintube(HX)
                
            if not result[0]:
                return (2,result[1])
        except:
            import traceback
            print(traceback.format_exc())
            pass

    return (1,"")
    
def check_microchannel(HX):
    if hasattr(HX,"Vdot_ha"):
        if HX.Vdot_ha == 0:
            return (0,"Inlet humid air volumetric flowrate can not be zero")
    if hasattr(HX,"mdot_da"):
        if HX.mdot_da == 0:
            return (0,"Inlet dry air mass flowrate can not be zero")

    if HX.Air_T <= 0:
        return (0,"Inlet air temperature can not be or below 0 kelvin")

    if HX.Air_P == 0:
        return (0,"Inlet air pressure can not be zero")

    for i,bank in enumerate(HX.Circuiting.bank_passes):
        for j,N_tubes in enumerate(bank):
            if N_tubes <= 0:
                return (0,"Number of tubes of pass "+str(j+1)+" for bank "+str(i+1)+" must be positive")

    if HX.Geometry.T_w == 0:
        return (0,"Microchannel tube width in geometry can not be zero")

    if HX.Geometry.T_h == 0:
        return (0,"Microchannel tube height in geometry can not be zero")

    if HX.Geometry.T_l == 0:
        return (0,"Microchannel tube length in geometry can not be zero")

    if HX.Geometry.T_s == 0:
        return (0,"Microchannel tube spacing in geometry can not be zero")

    if HX.Geometry.N_ports == 0:
        return (0,"Microchannel tube number of ports in geometry can not be zero")

    if HX.Geometry.port_a_dim == 0:
        return (0,"Microchannel port dimension (a) in geometry can not be zero")

    if HX.Geometry.port_a_dim >= HX.Geometry.T_h:
        return (0,"Microchannel port height should be smaller than tube height in geometry")

    if HX.Geometry.port_shape_index in [0,2]:
        if HX.Geometry.port_b_dim == 0:
            return (0,"Microchannel port dimension (b) in geometry can not be zero")

    if HX.Geometry.port_shape_index in [0,2]:
        width = HX.Geometry.port_b_dim * HX.Geometry.N_ports
    else:
        width = HX.Geometry.port_a_dim * HX.Geometry.N_ports
        
    if  width >= HX.Geometry.T_w:
        return (0,"Microchannel total ports width should be smaller than tube width in geometry")

    if HX.Geometry.header_a_dim < HX.Geometry.T_w:
        return (0,"Microchannel header dimension (a) in geometry can not be less than tube width")

    if HX.Geometry.header_shape_index == 0:
        if HX.Geometry.header_b_dim == 0:
            return (0,"Microchannel header dimension (b) in geometry can not be zero")        

    if HX.Geometry.Fin_on_side:    
        height = (HX.N_tube_per_bank + 1) * HX.Geometry.T_s + HX.N_tube_per_bank * HX.Geometry.T_h
    else:
        height = (HX.N_tube_per_bank - 1) * HX.Geometry.T_s + HX.N_tube_per_bank * HX.Geometry.T_h

    if HX.Geometry.header_height < height:
        return (0,"Microchannel header height in geometry can not be less total height of tubes including spacings")    

    if HX.Geometry.Fin_t == 0:
        return (0,"Fin thickness of in geometry can not be zero")

    if HX.Geometry.Fin_FPI == 0:
        return (0,"Fin FPI of in geometry can not be zero")

    if HX.Geometry.Fin_l == 0:
        return (0,"Fin length of in geometry can not be zero")
    
    if HX.Geometry.Fin_type == "Louvered":
        if HX.Geometry.Fin_llouv == 0:
            return (0,"Louvered fin louver length in geometry can not be zero")

        if HX.Geometry.Fin_lp == 0:
            return (0,"Louvered fin louver pitch in geometry can not be zero")

        if not 0 < HX.Geometry.Fin_lalpha < 90:
            return (0,"Louvered fin louver angle in geometry should be between 0 and 90 degrees")

    if HX.Geometry.Tube_k == 0:
        return (0,"Tube thermal conductivity in geometry can not be zero")

    if HX.Geometry.Fin_k == 0:
        return (0,"Fin thermal conductivity in geometry can not be zero")

    if HX.superheat_HTC_correction == 0:
        return (0,"Superheat HTC correction factor can not be zero")

    if HX.superheat_DP_correction == 0:
        return (0,"Superheat pressure drop correction factor can not be zero")

    if HX._2phase_HTC_correction == 0:
        return (0,"Two-phase HTC correction factor can not be zero")

    if HX._2phase_DP_correction == 0:
        return (0,"Two-phase pressure drop correction factor can not be zero")

    if HX.subcool_HTC_correction == 0:
        return (0,"Subcool HTC correction factor can not be zero")

    if HX.subcool_DP_correction == 0:
        return (0,"Subcool pressure drop correction factor can not be zero")

    if HX.air_dry_HTC_correction == 0:
        return (0,"Air dry HTC correction factor can not be zero")

    if HX.air_dry_DP_correction == 0:
        return (0,"Air dry pressure correction factor can not be zero")

    if HX.air_wet_HTC_correction == 0:
        return (0,"Air wet HTC correction factor can not be zero")

    if HX.air_wet_DP_correction == 0:
        return (0,"Air wet pressure correction factor can not be zero")

    if hasattr(HX,"capacity_validation_table"):
        try:
            if HX.capacity_validation_table["HX_type"] == "evap":
                result = check_evaporator_capacity_microchannel(HX)
            elif HX.capacity_validation_table["HX_type"] == "cond":
                result = check_condenser_capacity_microchannel(HX)
                
            if not result[0]:
                return (2,result[1])
        except:
            import traceback
            print(traceback.format_exc())
            pass
    
    return (1,"")

def check_line(line):
    if line.Line_length == 0:
        return (0,"Length of line can not be zero")

    if line.Line_OD == 0:
        return (0,"Line outer diameter can not be zero")

    if line.Line_ID == 0:
        return (0,"Line inner diameter can not be zero")

    if line.Line_q_tolerance == 0:
        return (0,"Line heat transfer tolerance can not be zero")

    if line.Line_insulation_k == 0:
        return (0,"Line insulation thermal conductivity can not be zero")

    if line.Line_tube_k == 0:
        return (0,"Line thermal conductivity can not be zero")

    if line.Line_OD <= line.Line_ID:
        return (0,"Line outer diameter must be greater than inner diameter")
    
    return (1,"")

def check_capillary(capillary):
    if capillary.Capillary_length == 0:
        return (0,"Length of capillary tube can not be zero")

    if capillary.Capillary_D == 0:
        return (0,"Capillary tube diameter can not be zero")

    if capillary.Capillary_entrance_D == 0:
        return (0,"Capillary tube entrance diameter can not be zero")
    
    if capillary.Capillary_entrance_D < capillary.Capillary_D:
        return (0,"Capillary entrance diameter should be more that the capillary tube diameter. The entrance diameter is usually the liquid line diameter.")
    
    if capillary.Capillary_DP_tolerance == 0:
        return (0, "Pressure tolerance of capillary tube can not be zero")
    
    if capillary.Capillary_DT == 0:
        return (0, "Capillary Discretization temperature can not be zero")

    return (1,"")

def validate_inputs(compressor,condenser,evaporator,liquid_line,twophase_line,suction_line,discharge_line,capillary=None):
    if compressor.Comp_model == "10coefficients":
        result = check_compressor_AHRI(compressor)
        if not result[0]:
            return list(result)+[0]

    elif compressor.Comp_model == "physics":
        result = check_compressor_physics(compressor)
        if not result[0]:
            return list(result)+[0]

    elif compressor.Comp_model == "map":
        result = check_compressor_map(compressor)
        if not result[0]:
            return list(result)+[0]
    
    if condenser.type == "Fintube":
        result = check_Fintube(condenser)
        if not result[0]:
            return list(result)+[1]

    elif condenser.type == "Microchannel":
        result = check_microchannel(condenser)
        if not result[0]:
            return list(result)+[1]

    if evaporator.type == "Fintube":
        result = check_Fintube(evaporator)
        if not result[0]:
            return list(result)+[2]

    elif evaporator.type == "Microchannel":
        result = check_microchannel(evaporator)
        if not result[0]:
            return list(result)+[2]

    result = check_line(liquid_line)
    if not result[0]:
        return list(result)+[3]

    result = check_line(twophase_line)
    if not result[0]:
        return list(result)+[4]

    result = check_line(suction_line)
    if not result[0]:
        return list(result)+[5]

    result = check_line(discharge_line)
    if not result[0]:
        return list(result)+[6]
    
    if capillary != None:
        result = check_capillary(capillary)
        if not result[0]:
            return list(result)+[7]
    
    return (1,"",-1)
