from lxml import etree as ET
import pandas as pd
import numpy as np
import appdirs
import zipfile
import os
import datetime
import csv
from shutil import copyfile
from PyQt5.QtCore import QDir

def read_comp_AHRI_xml(path):
    try:
        class values():
            pass
        comp = values()
        tree = ET.parse(path)
        root = tree.getroot()
        if root.tag != "Coefficients":
            root = root.find("Coefficients")
        comp.num_speeds = int(root.find("number_of_speeds").text)
        comp.unit_system = str(root.find("unit_system").text)
        comp.std_sh = str(root.find("Standard_Superheat").text)
        comp.std_sh_unit = str(root.find("Standard_Superheat_unit").text)
        comp.Comp_AHRI_F_value = str(root.find("Volumetric_Efficiency_Correction_Factor").text)
        comp.speeds = [values() for _ in range(comp.num_speeds)]
        for i in range(comp.num_speeds):
            speed = root.find("speed_"+str(i+1))
            comp.speeds[i].speed_value = float(speed.find("speed_value").text)
            comp.speeds[i].M = []
            M = speed.find("M")
            for j in range(10):
                comp.speeds[i].M.append(float(M.find("M"+str(j+1)).text))
            comp.speeds[i].P = []
            P = speed.find("P")
            for j in range(10):
                comp.speeds[i].P.append(float(P.find("P"+str(j+1)).text))

        return(1,comp)
    except:
        import traceback
        print(traceback.format_exc())
        return (0,0)
    
def write_comp_AHRI_xml(comp,path):
    try:
        data = ET.Element('Coefficients')
        unit_system = ET.SubElement(data, 'unit_system')
        unit_system.text = str(comp.unit_system)
        num_speeds = ET.SubElement(data, 'number_of_speeds')
        num_speeds.text = str(comp.num_speeds)
        Comp_AHRI_F_value = ET.SubElement(data, 'Volumetric_Efficiency_Correction_Factor')
        Comp_AHRI_F_value.text = str(comp.Comp_AHRI_F_value)
        std_sh = ET.SubElement(data, 'Standard_Superheat')
        std_sh.text = str(comp.std_sh)
        std_sh_unit = ET.SubElement(data, 'Standard_Superheat_unit')
        std_sh_unit.text = str(comp.std_sh_unit)
        for i in range(comp.num_speeds):
            speed = ET.SubElement(data, 'speed_'+str(i+1))
            speed_value = ET.SubElement(speed, 'speed_value')
            speed_value.text = str(comp.speeds[i].speed_value)
            M_values = ET.SubElement(speed, 'M')
            for j in range(10):
                M = ET.SubElement(M_values, 'M'+str(j+1))
                M.text = str(comp.speeds[i].M[j])
            P_values = ET.SubElement(speed, 'P')
            for j in range(10):
                P = ET.SubElement(P_values, 'P'+str(j+1))
                P.text = str(comp.speeds[i].P[j])
        mydata = str(ET.tostring(data, pretty_print=True),"utf-8")
        with open(path, "w") as myfile:
            myfile.write(mydata)
        return 1
    except:
        import traceback
        print(traceback.format_exc())
        return 0

def read_comp_xml(path):
    try:
        class values():
            pass
        comp = values()
        tree = ET.parse(path)
        root = tree.getroot()
        if root.tag != "Compressor":
            root = root.find("Compressor")
        comp.Comp_name = str(root.find("Compressor_name").text)
        comp.Ref = str(root.find("Compressor_Refrigerant").text)
        comp.Comp_vol = float(root.find("Compressor_Volume").text)
        comp.Comp_speed = float(root.find("Compressor_speed").text)
        comp.Comp_fp = float(root.find("Compressor_heat_loss_fraction").text)
        comp.Comp_elec_eff = float(root.find("Compressor_electrical_efficiency").text)
        comp.Comp_ratio_M = float(root.find("Compresso_Mass_Flowrate_Multiplier").text)
        comp.Comp_ratio_P = float(root.find("Compresso_Power_Multiplier").text)
        comp.Comp_model = str(root.find("Compressor_Model").text)
        if comp.Comp_model == "Physics-based model":
            comp.Comp_model = "physics"
        if comp.Comp_model == "AHRI 10-coefficients model":
            comp.Comp_model = "10coefficients"
        if comp.Comp_model == "AHRI compressor map":
            comp.Comp_model = "map"
        
        if comp.Comp_model == "physics":
            comp.isentropic_exp = str(root.find("Compressor_Isentropic_Efficiency").text)
            comp.vol_exp = str(root.find("Compressor_Volumetric_Efficiency").text)
            comp.model_data_exist = True
               
        elif comp.Comp_model == "10coefficients":
            comp.unit_system = str(root.find("Compressor_Coefficients_Unit_System").text)
            comp.num_speeds = int(root.find("Compressor_Number_of_Speeds").text)
            std_type = root.find("Compressor_Standard_Type")
            if std_type != None:
                comp.std_type = int(root.find("Compressor_Standard_Type").text)
                if comp.std_type == 0:
                    comp.std_sh = float(root.find("Compressor_Standard_Superheat").text)
                elif comp.std_type == 1:
                    comp.std_suction = float(root.find("Compressor_Standard_Suction_Temperature").text)
            else:
                comp.std_sh = float(root.find("Compressor_Standard_Superheat").text)
                comp.std_type = 0
                
            comp.Comp_AHRI_F_value = float(root.find("Compressor_Volumetric_Correction_Factor").text)
            speeds = root.find("Compressor_Speeds")
            comp.speeds = []
            comp.M = []
            comp.P = []
            for i in range(comp.num_speeds):
                speed = speeds.find("speed_"+str(i+1))
                comp.speeds.append(float(speed.find("speed_value").text))
                M = speed.find("M")
                M_list = []
                for j in range(10):
                    M_list.append(float(M.find("M"+str(j+1)).text))
                comp.M.append(tuple(M_list))
                P = speed.find("P")
                P_list = []
                for j in range(10):
                    P_list.append(float(P.find("P"+str(j+1)).text))
                comp.P.append(tuple(P_list))
            comp.model_data_exist = True
        elif comp.Comp_model == "map":
            comp.map_data = values()
            Tcond_unit = str(root.find("Condensing_temperature_unit").text)
            if Tcond_unit == "C":
                comp.map_data.Tcond_unit = 0
            elif Tcond_unit == "K":
                comp.map_data.Tcond_unit = 1
            elif Tcond_unit == "F":
                comp.map_data.Tcond_unit = 2
            else:
                raise
                
            Tevap_unit = str(root.find("Evaporating_temperature_unit").text)
            if Tevap_unit == "C":
                comp.map_data.Tevap_unit = 0
            elif Tevap_unit == "K":
                comp.map_data.Tevap_unit = 1
            elif Tevap_unit == "F":
                comp.map_data.Tevap_unit = 2
            else:
                raise
            
            M_unit = int(root.find("Mass_flowrate_unit").text)
            comp.map_data.M_unit = M_unit
            
            comp.unit_system = "si"
            
            std_type = root.find("Compressor_Standard_Type")
            if std_type != None:
                comp.map_data.std_type = int(root.find("Compressor_Standard_Type").text)
                if comp.map_data.std_type == 0:
                    comp.map_data.std_sh = float(root.find("Compressor_Standard_Superheat").text)
                elif comp.map_data.std_type == 1:
                    comp.map_data.std_suction = float(root.find("Compressor_Standard_Suction_Temperature").text)
            else:
                comp.map_data.std_sh = float(root.find("Compressor_Standard_Superheat").text)
                comp.map_data.std_type = 0
            
            comp.map_data.F_value = float(root.find("Compressor_Volumetric_Correction_Factor").text)

            num_speeds = int(root.find("Number_of_Compressor_Speeds").text)

            speeds = root.find("Compressor_Speeds")
            
            comp.map_data.Speeds = []

            comp.map_data.M_coeffs = []
            comp.map_data.P_coeffs = []

            comp.map_data.M_array = []
            comp.map_data.P_array = []
            
            for i in range(num_speeds):
                speed = speeds.find('speed_'+str(i+1))
                
                speed_value = float(speed.find('speed_value').text)
                comp.map_data.Speeds.append(speed_value)
                
                M = speed.find("M_coefficients")
                M_list = []
                for j in range(10):
                    M_list.append(float(M.find("M"+str(j+1)).text))
                comp.map_data.M_coeffs.append(tuple(M_list))
                P = speed.find("P_coefficients")
                P_list = []
                for j in range(10):
                    P_list.append(float(P.find("P"+str(j+1)).text))
                comp.map_data.P_coeffs.append(tuple(P_list))
                
                M_map = speed.find("M_map")
                P_map = speed.find("P_map")
                
                failed = False
                i = 1
                M_array = []
                while not failed:
                    Tc_M_i = M_map.find("Tc_"+str(i))
                    if Tc_M_i == None:
                        failed = True
                    else:
                        Tc_M_i = float(M_map.find("Tc_"+str(i)).text)
                        Te_M_i = float(M_map.find("Te_"+str(i)).text)
                        M_i = float(M_map.find("M_"+str(i)).text)
                        M_array.append([Tc_M_i,Te_M_i,M_i])
                    i += 1

                failed = False
                i = 1
                P_array = []
                while not failed:
                    Tc_P_i = P_map.find("Tc_"+str(i))
                    if Tc_P_i == None:
                        failed = True
                    else:
                        Tc_P_i = float(P_map.find("Tc_"+str(i)).text)
                        Te_P_i = float(P_map.find("Te_"+str(i)).text)
                        P_i = float(P_map.find("P_"+str(i)).text)
                        P_array.append([Tc_P_i,Te_P_i,P_i])
                    i += 1

                comp.map_data.M_array.append(np.array(M_array))
                comp.map_data.P_array.append(np.array(P_array))
            comp.model_data_exist = True
        return(1,comp)
    except:
        import traceback
        print(traceback.format_exc())
        return (0,0)
    
def write_comp_xml(comp,path):
    try:
        data = ET.Element('Compressor')
        Comp_name = ET.SubElement(data, 'Compressor_name')
        Comp_name.text = str(comp.Comp_name)
        Ref = ET.SubElement(data, 'Compressor_Refrigerant')
        Ref.text = str(comp.Ref)
        Comp_vol = ET.SubElement(data, 'Compressor_Volume')
        Comp_vol.text = str(comp.Comp_vol)
        Comp_speed = ET.SubElement(data, 'Compressor_speed')
        Comp_speed.text = str(comp.Comp_speed)
        Comp_fp = ET.SubElement(data, 'Compressor_heat_loss_fraction')
        Comp_fp.text = str(comp.Comp_fp)
        Comp_elec_eff = ET.SubElement(data, 'Compressor_electrical_efficiency')
        Comp_elec_eff.text = str(comp.Comp_elec_eff)
        Comp_ratio_M = ET.SubElement(data, 'Compresso_Mass_Flowrate_Multiplier')
        Comp_ratio_M.text = str(comp.Comp_ratio_M)
        Comp_ratio_P = ET.SubElement(data, 'Compresso_Power_Multiplier')
        Comp_ratio_P.text = str(comp.Comp_ratio_P)
        if comp.Comp_model == "Physics-based model":
            comp.Comp_model = "physics"
        if comp.Comp_model == "AHRI 10-coefficients model":
            comp.Comp_model = "10coefficients"
        if comp.Comp_model == "AHRI compressor map":
            comp.Comp_model = "map"
        Comp_model = ET.SubElement(data, 'Compressor_Model')
        Comp_model.text = str(comp.Comp_model)
        if comp.Comp_model == "physics":
            isentropic_exp = ET.SubElement(data, 'Compressor_Isentropic_Efficiency')
            isentropic_exp.text = str(comp.isentropic_exp)
            vol_exp = ET.SubElement(data, 'Compressor_Volumetric_Efficiency')
            vol_exp.text = str(comp.vol_exp)

        elif comp.Comp_model == "10coefficients":
            unit_system = ET.SubElement(data, 'Compressor_Coefficients_Unit_System')
            unit_system.text = str(comp.unit_system)
            num_speeds = ET.SubElement(data, 'Compressor_Number_of_Speeds')
            num_speeds.text = str(comp.num_speeds)
            std_type = ET.SubElement(data, 'Compressor_Standard_Type')
            std_type.text = str(comp.std_type)
            if comp.std_type == 0:
                std_sh = ET.SubElement(data, 'Compressor_Standard_Superheat')
                std_sh.text = str(comp.std_sh)
            elif comp.std_type == 1:
                std_suction = ET.SubElement(data, 'Compressor_Standard_Suction_Temperature')
                std_suction.text = str(comp.std_suction)
            Comp_AHRI_F_value = ET.SubElement(data, 'Compressor_Volumetric_Correction_Factor')
            Comp_AHRI_F_value.text = str(comp.Comp_AHRI_F_value)
            speeds = ET.SubElement(data, 'Compressor_Speeds')
            for i in range(comp.num_speeds):
                speed = ET.SubElement(speeds, 'speed_'+str(i+1))
                speed_value = ET.SubElement(speed, 'speed_value')
                speed_value.text = str(comp.speeds[i])
                M_major = ET.SubElement(speed, 'M')
                P_major = ET.SubElement(speed, 'P')
                for j in range(10):
                    M = ET.SubElement(M_major, 'M'+str(j+1))
                    M.text = str(comp.M[i][j])
                    P = ET.SubElement(P_major, 'P'+str(j+1))
                    P.text = str(comp.P[i][j])
        elif comp.Comp_model == "map":
            Tcond_unit = ET.SubElement(data, 'Condensing_temperature_unit')
            if comp.map_data.Tcond_unit == 0:
                Tcond_unit.text = "C"
            elif comp.map_data.Tcond_unit == 1:
                Tcond_unit.text = "K"
            elif comp.map_data.Tcond_unit == 2:
                Tcond_unit.text = "F"

            Tevap_unit = ET.SubElement(data, 'Evaporating_temperature_unit')
            if comp.map_data.Tevap_unit == 0:
                Tevap_unit.text = "C"
            elif comp.map_data.Tevap_unit == 1:
                Tevap_unit.text = "K"
            elif comp.map_data.Tevap_unit == 2:
                Tevap_unit.text = "F"

            M_unit = ET.SubElement(data, 'Mass_flowrate_unit')
            M_unit.text = str(comp.map_data.M_unit)
            
            std_type = ET.SubElement(data, 'Compressor_Standard_Type')
            std_type.text = str(comp.map_data.std_type)
            if comp.map_data.std_type == 0:
                std_sh = ET.SubElement(data, 'Compressor_Standard_Superheat')
                std_sh.text = str(comp.map_data.std_sh)
            elif comp.map_data.std_type == 1:
                std_suction = ET.SubElement(data, 'Compressor_Standard_Suction_Temperature')
                std_suction.text = str(comp.map_data.std_suction)

            F_value = ET.SubElement(data, 'Compressor_Volumetric_Correction_Factor')
            F_value.text = str(comp.map_data.F_value)

            num_speeds = ET.SubElement(data, 'Number_of_Compressor_Speeds')
            num_speeds.text = str(len(comp.map_data.Speeds))

            speeds = ET.SubElement(data, 'Compressor_Speeds')
            
            for i in range(len(comp.map_data.Speeds)):
                speed = ET.SubElement(speeds, 'speed_'+str(i+1))
                speed_value = ET.SubElement(speed, 'speed_value')
                speed_value.text = str(comp.map_data.Speeds[i])
                M_major = ET.SubElement(speed, 'M_coefficients')
                P_major = ET.SubElement(speed, 'P_coefficients')
                for j in range(10):
                    M = ET.SubElement(M_major, 'M'+str(j+1))
                    M.text = str(comp.map_data.M_coeffs[i][j])
                    P = ET.SubElement(P_major, 'P'+str(j+1))
                    P.text = str(comp.map_data.P_coeffs[i][j])
                M_array = ET.SubElement(speed, 'M_map')
                P_array = ET.SubElement(speed, 'P_map')
                for j,M_row in enumerate(comp.map_data.M_array[i]):
                    Tc_M_i = ET.SubElement(M_array,'Tc_'+str(j+1))
                    Tc_M_i.text = str(M_row[0])
                    Te_M_i = ET.SubElement(M_array,'Te_'+str(j+1))
                    Te_M_i.text = str(M_row[1])
                    M_value_i = ET.SubElement(M_array, 'M_'+str(j+1))
                    M_value_i.text = str(M_row[2])
                for j,P_row in enumerate(comp.map_data.P_array[i]):
                    Tc_P_i = ET.SubElement(P_array,'Tc_'+str(j+1))
                    Tc_P_i.text = str(P_row[0])
                    Te_P_i = ET.SubElement(P_array,'Te_'+str(j+1))
                    Te_P_i.text = str(P_row[1])
                    P_value_i = ET.SubElement(P_array, 'P_'+str(j+1))
                    P_value_i.text = str(P_row[2])
        mydata = str(ET.tostring(data, pretty_print=True),"utf-8")
        with open(path, "w") as myfile:
            myfile.write(mydata)
        return 1
    except:
        import traceback
        print(traceback.format_exc())
        return 0

def write_Fin_tube(HX,path):
    try:
        data = ET.Element('FinTube_HX')
        HX_name = ET.SubElement(data, 'Heat_Exchanger_Name')
        HX_name.text = str(HX.name)
        HX_solver = ET.SubElement(data, 'Heat_Exchanger_Solver')
        HX_solver.text = str(HX.solver)
        HX_model = ET.SubElement(data, 'Heat_Exchanger_Model')
        HX_model.text = str(HX.model)
        if hasattr(HX,"N_segments"):            
            HX_N_segments = ET.SubElement(data, 'Number_of_Segments_Per_Tube')
            HX_N_segments.text = str(HX.N_segments)
        HX_Accurate = ET.SubElement(data, 'Air_Properties_Library')
        HX_Accurate.text = str(HX.Accurate)
        HX_N_series_Circuits = ET.SubElement(data, 'Number_of_Series_Circuits')
        HX_N_series_Circuits.text = str(HX.N_series_Circuits)
        HX_HX_Q_tol = ET.SubElement(data, 'Capacity_Error_Tolerance')
        HX_HX_Q_tol.text = str(HX.HX_Q_tol)
        HX_N_iterations = ET.SubElement(data, 'Maximum_Number_of_Iterations')
        HX_N_iterations.text = str(HX.N_iterations)
        if hasattr(HX,"HX_DP_tol"):            
            HX_HX_DP_tol = ET.SubElement(data, 'Pressure_Drop_Tolerance')
            HX_HX_DP_tol.text = str(HX.HX_DP_tol)
        HX_Air_flow_direction = ET.SubElement(data, 'Air_Flow_Direction')
        HX_Air_flow_direction.text = str(HX.Air_flow_direction)
        if hasattr(HX,"Air_Distribution"):
            HX_Air_Distribution = ET.SubElement(data, 'Air_Distribution')
            Air_Distribution = [str(i) for i in HX.Air_Distribution]
            HX_Air_Distribution.text = ','.join(Air_Distribution)
        HX_Fan_model = ET.SubElement(data, 'Fan_Model')
        HX_Fan_model.text = str(HX.Fan_model)
        if hasattr(HX,'Fan_model_efficiency_exp'):
            HX_Fan_model_efficiency_exp = ET.SubElement(data, 'Fan_Model_Efficiency_Expression')
            HX_Fan_model_efficiency_exp.text = str(HX.Fan_model_efficiency_exp)
        if hasattr(HX,'Fan_model_power_exp'):
            HX_Fan_model_power_exp = ET.SubElement(data, 'Fan_Model_Power_Model_Expression')
            HX_Fan_model_power_exp.text = str(HX.Fan_model_power_exp)
        if hasattr(HX,'Fan_model_P_exp'):
            HX_Fan_model_P_exp = ET.SubElement(data, 'Fan_Model_Power_Expression')
            HX_Fan_model_P_exp.text = str(HX.Fan_model_P_exp)
        if hasattr(HX,'Fan_model_DP_exp'):
            HX_Fan_model_DP_exp = ET.SubElement(data, 'Fan_Model_Pressure_Drop_Expression')
            HX_Fan_model_DP_exp.text = str(HX.Fan_model_DP_exp)
        if hasattr(HX,"Vdot_ha"):
            HX_Vdot_ha = ET.SubElement(data, 'Air_Humid_Flow_rate')
            HX_Vdot_ha.text = str(HX.Vdot_ha)
        elif hasattr(HX,"mdot_da"):
            HX_mdot_da = ET.SubElement(data, 'Air_Dry_Mass_Flow_rate')
            HX_mdot_da.text = str(HX.mdot_da)
        else:
            raise
        HX_Air_P = ET.SubElement(data, 'Air_Inlet_Pressure')
        HX_Air_P.text = str(HX.Air_P)
        HX_Air_T = ET.SubElement(data, 'Air_Inlet_Temeprature')
        HX_Air_T.text = str(HX.Air_T)
        HX_Air_RH = ET.SubElement(data, 'Air_Inlet_Relative_Humidity')
        HX_Air_RH.text = str(HX.Air_RH)
        HX_circuits = ET.SubElement(data, 'Circuits')
        for i,circuit in enumerate(HX.circuits):
            circuit_info = ET.SubElement(HX_circuits, 'Circuit_'+str(i))
            OD = ET.SubElement(circuit_info, 'Outer_Diameter')
            OD.text = str(circuit.OD)
            Ltube = ET.SubElement(circuit_info, 'Tube_Length')
            Ltube.text = str(circuit.Ltube)
            Tube_type = ET.SubElement(circuit_info, 'Tube_Type')
            Tube_type.text = str(circuit.Tube_type)
            if circuit.Tube_type_index == 0:
                ID = ET.SubElement(circuit_info, 'Inner_Diameter')
                ID.text = str(circuit.ID)
                e_D = ET.SubElement(circuit_info, 'Tube_Roughness')
                e_D.text = str(circuit.e_D)
            elif circuit.Tube_type_index == 1:
                Tube_t = ET.SubElement(circuit_info, 'Tube_thickness')
                Tube_t.text = str(circuit.Tube_t)
                Tube_d = ET.SubElement(circuit_info, 'Tube_Fin_Base_Width')
                Tube_d.text = str(circuit.Tube_d)
                Tube_e = ET.SubElement(circuit_info, 'Tube_Fin_Height')
                Tube_e.text = str(circuit.Tube_e)
                Tube_n = ET.SubElement(circuit_info, 'Tube_Fin_number')
                Tube_n.text = str(circuit.Tube_n)
                Tube_gamma = ET.SubElement(circuit_info, 'Tube_Fin_Apex_Angle')
                Tube_gamma.text = str(circuit.Tube_gamma)
                Tube_beta = ET.SubElement(circuit_info, 'Tube_Fin_Spiral_Angle')
                Tube_beta.text = str(circuit.Tube_beta)
            Staggering = ET.SubElement(circuit_info, 'Staggering_Style')
            Staggering.text = str(circuit.Staggering)
            N_tube_per_bank = ET.SubElement(circuit_info, 'Number_of_Tubes_per_Bank')
            N_tube_per_bank.text = str(circuit.N_tube_per_bank)
            N_bank = ET.SubElement(circuit_info, 'Number_Banks')
            N_bank.text = str(circuit.N_bank)
            Pl = ET.SubElement(circuit_info, 'Tube_Longitudinal_Spacing')
            Pl.text = str(circuit.Pl)
            Pt = ET.SubElement(circuit_info, 'Tube_Transverse_Spacing')
            Pt.text = str(circuit.Pt)
            circuitry_name = ET.SubElement(circuit_info, 'Circuitry_Style')
            circuitry_name.text = str(circuit.circuitry_name)
            Connections = ET.SubElement(circuit_info, 'Tubes_Connections')
            Connections_list = [str(i) for i in circuit.Connections]
            Connections.text = ','.join(Connections_list)
            N_Circuits = ET.SubElement(circuit_info, 'Number_of_Parallel_Duplicate_Circuits')
            N_Circuits.text = str(circuit.N_Circuits)
            Fin_t = ET.SubElement(circuit_info, 'Fin_Thickness')
            Fin_t.text = str(circuit.Fin_t)
            Fin_FPI = ET.SubElement(circuit_info, 'Fin_FPI')
            Fin_FPI.text = str(circuit.Fin_FPI)
            Fin_type = ET.SubElement(circuit_info, 'Fin_Type')
            Fin_type.text = str(circuit.Fin_type)
            if circuit.Fin_type_index == 1:
                Fin_xf = ET.SubElement(circuit_info, 'Fin_xf')
                Fin_xf.text = str(circuit.Fin_xf)
                Fin_pd = ET.SubElement(circuit_info, 'Fin_pd')
                Fin_pd.text = str(circuit.Fin_pd)
            elif circuit.Fin_type_index == 2:
                Fin_Sh = ET.SubElement(circuit_info, 'Fin_Sh')
                Fin_Sh.text = str(circuit.Fin_Sh)
                Fin_Ss = ET.SubElement(circuit_info, 'Fin_Ss')
                Fin_Ss.text = str(circuit.Fin_Ss)
                Fin_Sn = ET.SubElement(circuit_info, 'Fin_Sn')
                Fin_Sn.text = str(circuit.Fin_Sn)
            elif circuit.Fin_type_index == 3:
                Fin_Lp = ET.SubElement(circuit_info, 'Fin_Lp')
                Fin_Lp.text = str(circuit.Fin_Lp)
                Fin_Lh = ET.SubElement(circuit_info, 'Fin_Lh')
                Fin_Lh.text = str(circuit.Fin_Lh)
            elif circuit.Fin_type_index == 4:
                Fin_xf = ET.SubElement(circuit_info, 'Fin_xf')
                Fin_xf.text = str(circuit.Fin_xf)
                Fin_pd = ET.SubElement(circuit_info, 'Fin_pd')
                Fin_pd.text = str(circuit.Fin_pd)
            Tube_k = ET.SubElement(circuit_info, 'Tube_Thermal_Conductivity')
            Tube_k.text = str(circuit.Tube_k)
            Fin_k = ET.SubElement(circuit_info, 'Fin_Thermal_Conductivity')
            Fin_k.text = str(circuit.Fin_k)
            superheat_HTC_corr = ET.SubElement(circuit_info, 'Superheat_HTC_Correlation')
            superheat_HTC_corr.text = str(circuit.superheat_HTC_corr)
            superheat_HTC_correction = ET.SubElement(circuit_info, 'Superheat_HTC_Correlation_Correction')
            superheat_HTC_correction.text = str(circuit.superheat_HTC_correction)
            superheat_DP_corr = ET.SubElement(circuit_info, 'Superheat_DP_Correlation')
            superheat_DP_corr.text = str(circuit.superheat_DP_corr)
            superheat_DP_correction = ET.SubElement(circuit_info, 'Superheat_DP_Correlation_Correction')
            superheat_DP_correction.text = str(circuit.superheat_DP_correction)
            _2phase_HTC_corr = ET.SubElement(circuit_info, 'Two_Phase_HTC_Correlation')
            _2phase_HTC_corr.text = str(circuit._2phase_HTC_corr)
            _2phase_HTC_correction = ET.SubElement(circuit_info, 'Two_Phase_HTC_Correlation_Correction')
            _2phase_HTC_correction.text = str(circuit._2phase_HTC_correction)
            _2phase_DP_corr = ET.SubElement(circuit_info, 'Two_Phase_DP_Correlation')
            _2phase_DP_corr.text = str(circuit._2phase_DP_corr)
            _2phase_DP_correction = ET.SubElement(circuit_info, 'Two_Phase_DP_Correlation_Correction')
            _2phase_DP_correction.text = str(circuit._2phase_DP_correction)
            _2phase_charge_corr = ET.SubElement(circuit_info, 'Two_Phase_Charge_Correlation')
            _2phase_charge_corr.text = str(circuit._2phase_charge_corr)
            subcool_HTC_corr = ET.SubElement(circuit_info, 'Subcool_HTC_Correlation')
            subcool_HTC_corr.text = str(circuit.subcool_HTC_corr)
            subcool_HTC_correction = ET.SubElement(circuit_info, 'Subcool_HTC_Correlation_Correction')
            subcool_HTC_correction.text = str(circuit.subcool_HTC_correction)
            subcool_DP_corr = ET.SubElement(circuit_info, 'Subcool_DP_Correlation')
            subcool_DP_corr.text = str(circuit.subcool_DP_corr)
            subcool_DP_correction = ET.SubElement(circuit_info, 'Subcool_DP_Correlation_Correction')
            subcool_DP_correction.text = str(circuit.subcool_DP_correction)
            air_dry_HTC_corr = ET.SubElement(circuit_info, 'Air_Dry_HTC_Correlation')
            air_dry_HTC_corr.text = str(circuit.air_dry_HTC_corr)
            air_dry_HTC_correction = ET.SubElement(circuit_info, 'Air_Dry_HTC_Correction')
            air_dry_HTC_correction.text = str(circuit.air_dry_HTC_correction)
            air_dry_DP_corr = ET.SubElement(circuit_info, 'Air_Dry_DP_Correlation')
            air_dry_DP_corr.text = str(circuit.air_dry_HTC_corr)
            air_dry_DP_correction = ET.SubElement(circuit_info, 'Air_Dry_DP_Correction')
            air_dry_DP_correction.text = str(circuit.air_dry_DP_correction)
            air_wet_HTC_corr = ET.SubElement(circuit_info, 'Air_Wet_HTC_Correlation')
            air_wet_HTC_corr.text = str(circuit.air_wet_HTC_corr)
            air_wet_HTC_correction = ET.SubElement(circuit_info, 'Air_Wet_HTC_Correction')
            air_wet_HTC_correction.text = str(circuit.air_wet_HTC_correction)
            air_wet_DP_corr = ET.SubElement(circuit_info, 'Air_Wet_DP_Correlation')
            air_wet_DP_corr.text = str(circuit.air_wet_HTC_corr)
            air_wet_DP_correction = ET.SubElement(circuit_info, 'Air_Wet_DP_Correction')
            air_wet_DP_correction.text = str(circuit.air_wet_DP_correction)
            
            if hasattr(circuit,'h_a_wet_on'):
                h_a_wet_on = ET.SubElement(circuit_info, 'Use_Wet_air_HTC_Correlation')
                h_a_wet_on.text = str(float(circuit.h_a_wet_on))

            if hasattr(circuit,'DP_a_wet_on'):
                DP_a_wet_on = ET.SubElement(circuit_info, 'Use_Wet_air_DP_Correlation')
                DP_a_wet_on.text = str(float(circuit.DP_a_wet_on))

            if hasattr(circuit,'sub_HX_values'):
                Sub_HX_data = ET.SubElement(circuit_info, 'Sub_HX_data')
                Sub_HX_data.text = ';'.join([','.join([str(i) for i in tube]) for tube in circuit.sub_HX_values])
            
        mydata = str(ET.tostring(data, pretty_print=True),"utf-8")
        with open(path, "w") as myfile:
            myfile.write(mydata)
        return 1
    except:
        import traceback
        print(traceback.format_exc())
        return 0

def read_Fin_tube(path):
    class values():
        pass
    try:
        HX = values()
        tree = ET.parse(path)
        root = tree.getroot()
        if root.tag != "FinTube_HX":
            root = root.find("FinTube_HX")

        HX.name = str(root.find("Heat_Exchanger_Name").text)
        HX.solver = str(root.find("Heat_Exchanger_Solver").text)
        HX.model = str(root.find("Heat_Exchanger_Model").text)
        N_segments = root.find("Number_of_Segments_Per_Tube")
        if N_segments != None:
            HX.N_segments = int(N_segments.text)
        HX.Accurate = str(root.find("Air_Properties_Library").text)
        HX.N_series_Circuits = int(root.find("Number_of_Series_Circuits").text)
        HX.HX_Q_tol = float(root.find("Capacity_Error_Tolerance").text)
        HX.N_iterations = int(root.find("Maximum_Number_of_Iterations").text)
        HX_DP_tol = root.find("Pressure_Drop_Tolerance")
        if HX_DP_tol != None:
            HX.DP_tol = float(HX_DP_tol.text)
        HX.Air_flow_direction = str(root.find("Air_Flow_Direction").text)
        HX_Air_distribution = root.find("Air_Distribution")
        if HX_Air_distribution != None:
            HX.Air_Distribution = [float(i) for i in str(HX_Air_distribution.text).split(",")]
        HX.Fan_model = str(root.find("Fan_Model").text)
        HX_Fan_model_efficiency_exp = root.find("Fan_Model_Efficiency_Expression")
        if HX_Fan_model_efficiency_exp != None:
            HX.Fan_model_efficiency_exp = str(HX_Fan_model_efficiency_exp.text)
        HX_Fan_model_power_exp = root.find("Fan_Model_Power_Model_Expression")
        if HX_Fan_model_power_exp != None:
            HX.Fan_model_power_exp = str(HX_Fan_model_power_exp.text)
        HX_Fan_model_P_exp = root.find("Fan_Model_Power_Expression")
        if HX_Fan_model_P_exp != None:
            HX.Fan_model_P_exp = str(HX_Fan_model_P_exp.text)
        HX_Fan_model_DP_exp = root.find("Fan_Model_Pressure_Drop_Expression")
        if HX_Fan_model_DP_exp != None:
            HX.Fan_model_DP_exp = str(HX_Fan_model_DP_exp.text)
        HX_Vdot_ha = root.find("Air_Humid_Flow_rate")
        if HX_Vdot_ha != None:
            HX.Vdot_ha = float(root.find("Air_Humid_Flow_rate").text)
        else:
            HX.mdot_da = float(root.find("Air_Dry_Mass_Flow_rate").text)
            
        HX.Air_P = float(root.find("Air_Inlet_Pressure").text)
        HX.Air_T = float(root.find("Air_Inlet_Temeprature").text)
        HX.Air_RH = float(root.find("Air_Inlet_Relative_Humidity").text)
        circuits = root.find("Circuits")
        if HX.Air_flow_direction in ["Sub Heat Exchanger First","Sub Heat Exchanger Last"]:
            number_of_circuits = HX.N_series_Circuits + 1
        elif HX.Air_flow_direction in ["Parallel","Series-Parallel","Series-Counter"]:
            number_of_circuits = HX.N_series_Circuits
        else:
            raise
        HX.circuits = [values() for _ in range(number_of_circuits)]
        for i in range(number_of_circuits):
            circuit = circuits.find("Circuit_"+str(i))
            HX.circuits[i].OD = float(circuit.find("Outer_Diameter").text)
            HX.circuits[i].Ltube = float(circuit.find("Tube_Length").text)
            HX.circuits[i].Tube_type = str(circuit.find("Tube_Type").text)
            if HX.circuits[i].Tube_type == "Smooth":
                HX.circuits[i].Tube_type_index = 0
            elif HX.circuits[i].Tube_type == "Microfin":
                HX.circuits[i].Tube_type_index = 1

            ID = circuit.find("Inner_Diameter")
            if ID != None:
                HX.circuits[i].ID = float(ID.text)
            e_D = circuit.find("Tube_Roughness")
            if e_D != None:
                HX.circuits[i].e_D = float(e_D.text)
            Tube_t = circuit.find("Tube_thickness")
            if Tube_t != None:
                HX.circuits[i].Tube_t = float(Tube_t.text)
            Tube_d = circuit.find("Tube_Fin_Base_Width")
            if Tube_d != None:
                HX.circuits[i].Tube_d = float(Tube_d.text)
            Tube_e = circuit.find("Tube_Fin_Height")
            if Tube_e != None:
                HX.circuits[i].Tube_e = float(Tube_e.text)
            Tube_n = circuit.find("Tube_Fin_number")
            if Tube_n != None:
                HX.circuits[i].Tube_n = int(Tube_n.text)
            Tube_gamma = circuit.find("Tube_Fin_Apex_Angle")
            if Tube_gamma != None:
                HX.circuits[i].Tube_gamma = float(Tube_gamma.text)
            Tube_beta = circuit.find("Tube_Fin_Spiral_Angle")
            if Tube_beta != None:
                HX.circuits[i].Tube_beta = float(Tube_beta.text)

            HX.circuits[i].Staggering = str(circuit.find("Staggering_Style").text)
            if HX.circuits[i].Staggering == "inline":
                HX.circuits[i].Staggering_index = 0
            elif HX.circuits[i].Staggering == "AaA":
                HX.circuits[i].Staggering_index = 1
            elif HX.circuits[i].Staggering == "aAa":
                HX.circuits[i].Staggering_index = 2

            HX.circuits[i].N_tube_per_bank = int(circuit.find("Number_of_Tubes_per_Bank").text)
            HX.circuits[i].N_bank = int(circuit.find("Number_Banks").text)
            HX.circuits[i].Pl = float(circuit.find("Tube_Longitudinal_Spacing").text)
            HX.circuits[i].Pt = float(circuit.find("Tube_Transverse_Spacing").text)
            HX.circuits[i].circuitry_name = str(circuit.find("Circuitry_Style").text)
            if HX.circuits[i].circuitry_name == "Counter":
                HX.circuits[i].circuitry = 0
            elif HX.circuits[i].circuitry_name == "Parallel":
                HX.circuits[i].circuitry = 1
            elif HX.circuits[i].circuitry_name == "Customized":
                HX.circuits[i].circuitry = 2
            HX.circuits[i].Connections = [int(i) for i in str(circuit.find("Tubes_Connections").text).split(",")]
            HX.circuits[i].N_Circuits = int(circuit.find("Number_of_Parallel_Duplicate_Circuits").text)
            HX.circuits[i].Fin_t = float(circuit.find("Fin_Thickness").text)
            HX.circuits[i].Fin_FPI = float(circuit.find("Fin_FPI").text)
            HX.circuits[i].Fin_type = str(circuit.find("Fin_Type").text)
            
            if HX.circuits[i].Fin_type == "Plain":
                HX.circuits[i].Fin_type_index = 0
            elif HX.circuits[i].Fin_type == "Wavy":
                HX.circuits[i].Fin_type_index = 1
                HX.circuits[i].Fin_xf = float(circuit.find("Fin_xf").text)
                HX.circuits[i].Fin_pd = float(circuit.find("Fin_pd").text)
            elif HX.circuits[i].Fin_type == "Slit":
                HX.circuits[i].Fin_type_index = 2
                HX.circuits[i].Fin_Sh = float(circuit.find("Fin_Sh").text)
                HX.circuits[i].Fin_Ss = float(circuit.find("Fin_Ss").text)
                HX.circuits[i].Fin_Sn = int(float(circuit.find("Fin_Sn").text))
            elif HX.circuits[i].Fin_type == "Louvered":
                HX.circuits[i].Fin_type_index = 3
                HX.circuits[i].Fin_Lp = float(circuit.find("Fin_Lp").text)
                HX.circuits[i].Fin_Lh = float(circuit.find("Fin_Lh").text)
            elif HX.circuits[i].Fin_type == "WavyLouvered":
                HX.circuits[i].Fin_type_index = 4
                HX.circuits[i].Fin_xf = float(circuit.find("Fin_xf").text)
                HX.circuits[i].Fin_pd = float(circuit.find("Fin_pd").text)
                
            HX.circuits[i].Tube_k = float(circuit.find("Tube_Thermal_Conductivity").text)
            HX.circuits[i].Fin_k = float(circuit.find("Fin_Thermal_Conductivity").text)

            HX.circuits[i].superheat_HTC_corr = int(circuit.find("Superheat_HTC_Correlation").text)
            HX.circuits[i].superheat_HTC_correction = float(circuit.find("Superheat_HTC_Correlation_Correction").text)
            HX.circuits[i].superheat_DP_corr = int(circuit.find("Superheat_DP_Correlation").text)
            HX.circuits[i].superheat_DP_correction = float(circuit.find("Superheat_DP_Correlation_Correction").text)

            HX.circuits[i]._2phase_HTC_corr = int(circuit.find("Two_Phase_HTC_Correlation").text)
            HX.circuits[i]._2phase_HTC_correction = float(circuit.find("Two_Phase_HTC_Correlation_Correction").text)
            HX.circuits[i]._2phase_DP_corr = int(circuit.find("Two_Phase_DP_Correlation").text)
            HX.circuits[i]._2phase_DP_correction = float(circuit.find("Two_Phase_DP_Correlation_Correction").text)

            HX.circuits[i]._2phase_charge_corr = int(float(circuit.find("Two_Phase_Charge_Correlation").text))

            HX.circuits[i].subcool_HTC_corr = int(circuit.find("Subcool_HTC_Correlation").text)
            HX.circuits[i].subcool_HTC_correction = float(circuit.find("Subcool_HTC_Correlation_Correction").text)
            HX.circuits[i].subcool_DP_corr = int(circuit.find("Subcool_DP_Correlation").text)
            HX.circuits[i].subcool_DP_correction = float(circuit.find("Subcool_DP_Correlation_Correction").text)

            HX.circuits[i].air_dry_HTC_corr = int(circuit.find("Air_Dry_HTC_Correlation").text)
            HX.circuits[i].air_dry_HTC_correction = float(circuit.find("Air_Dry_HTC_Correction").text)
            HX.circuits[i].air_dry_DP_corr = int(circuit.find("Air_Dry_DP_Correlation").text)
            HX.circuits[i].air_dry_DP_correction = float(circuit.find("Air_Dry_DP_Correction").text)
            HX.circuits[i].air_wet_HTC_corr = int(circuit.find("Air_Wet_HTC_Correlation").text)
            HX.circuits[i].air_wet_HTC_correction = float(circuit.find("Air_Wet_HTC_Correction").text)
            HX.circuits[i].air_wet_DP_corr = int(circuit.find("Air_Wet_DP_Correlation").text)
            HX.circuits[i].air_wet_DP_correction = float(circuit.find("Air_Wet_DP_Correction").text)
            
            h_a_wet_on = circuit.find("Use_Wet_air_HTC_Correlation")
            if h_a_wet_on != None:
                HX.circuits[i].h_a_wet_on = bool(float(h_a_wet_on.text))
                
            DP_a_wet_on = circuit.find("Use_Wet_air_DP_Correlation")
            if DP_a_wet_on != None:
                HX.circuits[i].DP_a_wet_on = bool(float(DP_a_wet_on.text))

            Sub_HX_data = circuit.find("Sub_HX_data")
            if Sub_HX_data != None:
                HX.circuits[i].sub_HX_values = [[float(i) for i in tube.split(",")] for tube in str(Sub_HX_data.text).split(";")]
                for row in HX.circuits[i].sub_HX_values:
                    row[0] = int(float(row[0]))
                    
            HX.circuits[i].defined = True
            
        return(1,HX)
    except:
        import traceback
        print(traceback.format_exc())
        return (0,0)

def write_Microchannel(HX,path):
    try:
        data = ET.Element('Microchannel_HX')
        HX_name = ET.SubElement(data, 'Heat_Exchanger_Name')
        HX_name.text = str(HX.name)
        HX_model = ET.SubElement(data, 'Heat_Exchanger_Model')
        HX_model.text = str(HX.model)
        if hasattr(HX,"N_segments"):            
            HX_N_segments = ET.SubElement(data, 'Number_of_Segments_Per_Tube')
            HX_N_segments.text = str(HX.N_segments)
        HX_Accurate = ET.SubElement(data, 'Air_Properties_Library')
        HX_Accurate.text = str(HX.Accurate)
        HX_N_bank = ET.SubElement(data, 'Number_of_Banks')
        HX_N_bank.text = str(HX.N_bank)
        HX_N_tube_per_bank = ET.SubElement(data, 'Number_of_Tubes_per_Bank')
        HX_N_tube_per_bank.text = str(HX.N_tube_per_bank)
        HX_HX_Q_tol = ET.SubElement(data, 'Capacity_Error_Tolerance')
        HX_HX_Q_tol.text = str(HX.HX_Q_tol)
        HX_N_iterations = ET.SubElement(data, 'Maximum_Number_of_Iterations')
        HX_N_iterations.text = str(HX.N_iterations)
        HX_Fan_model = ET.SubElement(data, 'Fan_Model')
        HX_Fan_model.text = str(HX.Fan_model)
        if hasattr(HX,'Fan_model_efficiency_exp'):
            HX_Fan_model_efficiency_exp = ET.SubElement(data, 'Fan_Model_Efficiency_Expression')
            HX_Fan_model_efficiency_exp.text = str(HX.Fan_model_efficiency_exp)
        if hasattr(HX,'Fan_model_power_exp'):
            HX_Fan_model_power_exp = ET.SubElement(data, 'Fan_Model_Power_Model_Expression')
            HX_Fan_model_power_exp.text = str(HX.Fan_model_power_exp)
        if hasattr(HX,'Fan_model_P_exp'):
            HX_Fan_model_P_exp = ET.SubElement(data, 'Fan_Model_Power_Expression')
            HX_Fan_model_P_exp.text = str(HX.Fan_model_P_exp)
        if hasattr(HX,'Fan_model_DP_exp'):
            HX_Fan_model_DP_exp = ET.SubElement(data, 'Fan_Model_Pressure_Drop_Expression')
            HX_Fan_model_DP_exp.text = str(HX.Fan_model_DP_exp)
        if hasattr(HX,"Vdot_ha"):
            HX_Vdot_ha = ET.SubElement(data, 'Air_Humid_Flow_rate')
            HX_Vdot_ha.text = str(HX.Vdot_ha)
        elif hasattr(HX,"mdot_da"):
            HX_mdot_da = ET.SubElement(data, 'Air_Dry_Mass_Flow_rate')
            HX_mdot_da.text = str(HX.mdot_da)
        else:
            raise
        HX_Air_P = ET.SubElement(data, 'Air_Inlet_Pressure')
        HX_Air_P.text = str(HX.Air_P)
        HX_Air_T = ET.SubElement(data, 'Air_Inlet_Temeprature')
        HX_Air_T.text = str(HX.Air_T)
        HX_Air_RH = ET.SubElement(data, 'Air_Inlet_Relative_Humidity')
        HX_Air_RH.text = str(HX.Air_RH)
        
        HX_Circuiting = ET.SubElement(data, 'Circuiting')
        bank_passes = ';'.join([','.join([str(i) for i in Pass]) for Pass in HX.Circuiting.bank_passes])
        HX_Circuiting.text = str(bank_passes)
        
        HX_Geometry = ET.SubElement(data, 'Geometry')
        Geometry = HX.Geometry
        T_w = ET.SubElement(HX_Geometry, 'Tube_Width')
        T_w.text = str(Geometry.T_w)
        T_h = ET.SubElement(HX_Geometry, 'Tube_Height')
        T_h.text = str(Geometry.T_h)
        T_l = ET.SubElement(HX_Geometry, 'Tube_Length')
        T_l.text = str(Geometry.T_l)
        T_s = ET.SubElement(HX_Geometry, 'Tube_Spacing')
        T_s.text = str(Geometry.T_s)
        e_D = ET.SubElement(HX_Geometry, 'Tube_Roughness')
        e_D.text = str(Geometry.e_D)
        T_end = ET.SubElement(HX_Geometry, 'Tube_End_Type')
        T_end.text = str(Geometry.T_end)
        N_ports = ET.SubElement(HX_Geometry, 'Number_of_Ports')
        N_ports.text = str(Geometry.N_ports)
        port_shape = ET.SubElement(HX_Geometry, 'Port_Shape')
        port_shape.text = str(Geometry.port_shape)
        if Geometry.port_shape_index == 0:
            port_a_dim = ET.SubElement(HX_Geometry, 'Port_Dimension_a')
            port_a_dim.text = str(Geometry.port_a_dim)
            port_b_dim = ET.SubElement(HX_Geometry, 'Port_Dimension_b')
            port_b_dim.text = str(Geometry.port_b_dim)
        elif Geometry.port_shape_index == 1:
            port_a_dim = ET.SubElement(HX_Geometry, 'Port_Dimension_a')
            port_a_dim.text = str(Geometry.port_a_dim)
        elif Geometry.port_shape_index == 2:
            port_a_dim = ET.SubElement(HX_Geometry, 'Port_Dimension_a')
            port_a_dim.text = str(Geometry.port_a_dim)
            port_b_dim = ET.SubElement(HX_Geometry, 'Port_Dimension_b')
            port_b_dim.text = str(Geometry.port_b_dim)
            
        header_shape = ET.SubElement(HX_Geometry, 'Header_Shape')
        header_shape.text = str(Geometry.header_shape)
        if Geometry.header_shape_index == 0:
            header_a_dim = ET.SubElement(HX_Geometry, 'Header_Dimension_a')
            header_a_dim.text = str(Geometry.header_a_dim)
            header_b_dim = ET.SubElement(HX_Geometry, 'Header_Dimension_b')
            header_b_dim.text = str(Geometry.header_b_dim)
        elif Geometry.header_shape_index == 1:
            header_a_dim = ET.SubElement(HX_Geometry, 'Header_Dimension_a')
            header_a_dim.text = str(Geometry.header_a_dim)
        
        header_height = ET.SubElement(HX_Geometry, 'Header_Height')
        header_height.text = str(Geometry.header_height)
        Fin_t = ET.SubElement(HX_Geometry, 'Fin_Thickness')
        Fin_t.text = str(Geometry.Fin_t)
        Fin_FPI = ET.SubElement(HX_Geometry, 'Fins_FPI')
        Fin_FPI.text = str(Geometry.Fin_FPI)
        Fin_l = ET.SubElement(HX_Geometry, 'Fin_Length')
        Fin_l.text = str(Geometry.Fin_l)
        Fin_on_side = ET.SubElement(HX_Geometry, 'Fins_On_The_Sides')
        Fin_on_side.text = str(float(Geometry.Fin_on_side))
        Fin_type = ET.SubElement(HX_Geometry, 'Fin_Type')
        Fin_type.text = str(Geometry.Fin_type)
        if Geometry.Fin_type_index == 0:
            Fin_llouv = ET.SubElement(HX_Geometry, 'Fin_Louver_Length')
            Fin_llouv.text = str(Geometry.Fin_llouv)
            Fin_lp = ET.SubElement(HX_Geometry, 'Fin_Louver_Pitch')
            Fin_lp.text = str(Geometry.Fin_lp)
            Fin_lalpha = ET.SubElement(HX_Geometry, 'Fin_Louver_Angle')
            Fin_lalpha.text = str(Geometry.Fin_lalpha)        
        Tube_k = ET.SubElement(HX_Geometry, 'Tube_Thermal_Conductivity')
        Tube_k.text = str(Geometry.Tube_k)
        Fin_k = ET.SubElement(HX_Geometry, 'Fin_Thermal_Conductivity')
        Fin_k.text = str(Geometry.Fin_k)
        Header_DP = ET.SubElement(HX_Geometry, 'Header_Pressure_Drop')
        Header_DP.text = str(Geometry.Header_DP)
        superheat_HTC_corr = ET.SubElement(data, 'Superheat_HTC_Correlation')
        superheat_HTC_corr.text = str(HX.superheat_HTC_corr)
        superheat_HTC_correction = ET.SubElement(data, 'Superheat_HTC_Correlation_Correction')
        superheat_HTC_correction.text = str(HX.superheat_HTC_correction)
        superheat_DP_corr = ET.SubElement(data, 'Superheat_DP_Correlation')
        superheat_DP_corr.text = str(HX.superheat_DP_corr)
        superheat_DP_correction = ET.SubElement(data, 'Superheat_DP_Correlation_Correction')
        superheat_DP_correction.text = str(HX.superheat_DP_correction)
        _2phase_HTC_corr = ET.SubElement(data, 'Two_Phase_HTC_Correlation')
        _2phase_HTC_corr.text = str(HX._2phase_HTC_corr)
        _2phase_HTC_correction = ET.SubElement(data, 'Two_Phase_HTC_Correlation_Correction')
        _2phase_HTC_correction.text = str(HX._2phase_HTC_correction)
        _2phase_DP_corr = ET.SubElement(data, 'Two_Phase_DP_Correlation')
        _2phase_DP_corr.text = str(HX._2phase_DP_corr)
        _2phase_DP_correction = ET.SubElement(data, 'Two_Phase_DP_Correlation_Correction')
        _2phase_DP_correction.text = str(HX._2phase_DP_correction)
        _2phase_charge_corr = ET.SubElement(data, 'Two_Phase_Charge_Correlation')
        _2phase_charge_corr.text = str(HX._2phase_charge_corr)
        subcool_HTC_corr = ET.SubElement(data, 'Subcool_HTC_Correlation')
        subcool_HTC_corr.text = str(HX.subcool_HTC_corr)
        subcool_HTC_correction = ET.SubElement(data, 'Subcool_HTC_Correlation_Correction')
        subcool_HTC_correction.text = str(HX.subcool_HTC_correction)
        subcool_DP_corr = ET.SubElement(data, 'Subcool_DP_Correlation')
        subcool_DP_corr.text = str(HX.subcool_DP_corr)
        subcool_DP_correction = ET.SubElement(data, 'Subcool_DP_Correlation_Correction')
        subcool_DP_correction.text = str(HX.subcool_DP_correction)
        air_dry_HTC_corr = ET.SubElement(data, 'Air_Dry_HTC_Correlation')
        air_dry_HTC_corr.text = str(HX.air_dry_HTC_corr)
        air_dry_HTC_correction = ET.SubElement(data, 'Air_Dry_HTC_Correction')
        air_dry_HTC_correction.text = str(HX.air_dry_HTC_correction)
        air_dry_DP_corr = ET.SubElement(data, 'Air_Dry_DP_Correlation')
        air_dry_DP_corr.text = str(HX.air_dry_HTC_corr)
        air_dry_DP_correction = ET.SubElement(data, 'Air_Dry_DP_Correction')
        air_dry_DP_correction.text = str(HX.air_dry_DP_correction)
        air_wet_HTC_corr = ET.SubElement(data, 'Air_Wet_HTC_Correlation')
        air_wet_HTC_corr.text = str(HX.air_wet_HTC_corr)
        air_wet_HTC_correction = ET.SubElement(data, 'Air_Wet_HTC_Correction')
        air_wet_HTC_correction.text = str(HX.air_wet_HTC_correction)
        air_wet_DP_corr = ET.SubElement(data, 'Air_Wet_DP_Correlation')
        air_wet_DP_corr.text = str(HX.air_wet_HTC_corr)
        air_wet_DP_correction = ET.SubElement(data, 'Air_Wet_DP_Correction')
        air_wet_DP_correction.text = str(HX.air_wet_DP_correction)

        if hasattr(HX,'h_a_wet_on'):
            h_a_wet_on = ET.SubElement(data, 'Use_Wet_air_HTC_Correlation')
            h_a_wet_on.text = str(float(HX.h_a_wet_on))

        if hasattr(HX,'DP_a_wet_on'):
            DP_a_wet_on = ET.SubElement(data, 'Use_Wet_air_DP_Correlation')
            DP_a_wet_on.text = str(float(HX.DP_a_wet_on))
            
        mydata = str(ET.tostring(data, pretty_print=True),"utf-8")
        with open(path, "w") as myfile:
            myfile.write(mydata)
        return 1
    except:
        import traceback
        print(traceback.format_exc())
        return 0

def read_Microchannel(path):
    class values():
        pass
    try:
        HX = values()
        tree = ET.parse(path)
        root = tree.getroot()
        if root.tag != "Microchannel_HX":
            root = root.find("Microchannel_HX")

        HX.name = str(root.find("Heat_Exchanger_Name").text)
        HX.model = str(root.find("Heat_Exchanger_Model").text)
        N_segments = root.find("Number_of_Segments_Per_Tube")
        if N_segments != None:
            HX.N_segments = int(N_segments.text)
        HX.Accurate = str(root.find("Air_Properties_Library").text)
        HX.N_bank = int(root.find("Number_of_Banks").text)
        HX.N_tube_per_bank = int(root.find("Number_of_Tubes_per_Bank").text)
        HX.HX_Q_tol = float(root.find("Capacity_Error_Tolerance").text)
        HX.N_iterations = int(root.find("Maximum_Number_of_Iterations").text)
        HX.Fan_model = str(root.find("Fan_Model").text)
        HX_Fan_model_efficiency_exp = root.find("Fan_Model_Efficiency_Expression")
        if HX_Fan_model_efficiency_exp != None:
            HX.Fan_model_efficiency_exp = str(HX_Fan_model_efficiency_exp.text)
        HX_Fan_model_power_exp = root.find("Fan_Model_Power_Model_Expression")
        if HX_Fan_model_power_exp != None:
            HX.Fan_model_power_exp = str(HX_Fan_model_power_exp.text)
        HX_Fan_model_P_exp = root.find("Fan_Model_Power_Expression")
        if HX_Fan_model_P_exp != None:
            HX.Fan_model_P_exp = str(HX_Fan_model_P_exp.text)
        HX_Fan_model_DP_exp = root.find("Fan_Model_Pressure_Drop_Expression")
        if HX_Fan_model_DP_exp != None:
            HX.Fan_model_DP_exp = str(HX_Fan_model_DP_exp.text)
        HX_Vdot_ha = root.find("Air_Humid_Flow_rate")
        if HX_Vdot_ha != None:
            HX.Vdot_ha = float(root.find("Air_Humid_Flow_rate").text)
        else:
            HX.mdot_da = float(root.find("Air_Dry_Mass_Flow_rate").text)
        HX.Air_P = float(root.find("Air_Inlet_Pressure").text)
        HX.Air_T = float(root.find("Air_Inlet_Temeprature").text)
        HX.Air_RH = float(root.find("Air_Inlet_Relative_Humidity").text)
        bank_passes = str(root.find("Circuiting").text)
        HX.Circuiting = values()
        HX.Circuiting.bank_passes = [[int(i) for i in Pass.split(",")] for Pass in bank_passes.split(";")]
        HX.Circuiting.defined = True
        Geometry = root.find("Geometry")
        HX.Geometry = values()
        HX.Geometry.T_w = float(Geometry.find("Tube_Width").text)
        HX.Geometry.T_h = float(Geometry.find("Tube_Height").text)
        HX.Geometry.T_l = float(Geometry.find("Tube_Length").text)
        HX.Geometry.T_s = float(Geometry.find("Tube_Spacing").text)
        HX.Geometry.e_D = float(Geometry.find("Tube_Roughness").text)
        HX.Geometry.T_end = str(Geometry.find("Tube_End_Type").text)
        HX.Geometry.N_ports = int(float(Geometry.find("Number_of_Ports").text))
        if HX.Geometry.T_end == "Normal":
            HX.Geometry.T_end_index = 0
        elif HX.Geometry.T_end == "Extended":
            HX.Geometry.T_end_index = 1
            
        HX.Geometry.port_shape = str(Geometry.find("Port_Shape").text)
        if HX.Geometry.port_shape == "Rectangle":
            HX.Geometry.port_shape_index = 0
            HX.Geometry.port_a_dim = float(Geometry.find("Port_Dimension_a").text)
            HX.Geometry.port_b_dim = float(Geometry.find("Port_Dimension_b").text)
        elif HX.Geometry.port_shape == "Circle":
            HX.Geometry.port_shape_index = 1
            HX.Geometry.port_a_dim = float(Geometry.find("Port_Dimension_a").text)
        elif HX.Geometry.port_shape == "Triangle":
            HX.Geometry.port_shape_index = 2
            HX.Geometry.port_a_dim = float(Geometry.find("Port_Dimension_a").text)
            HX.Geometry.port_b_dim = float(Geometry.find("Port_Dimension_b").text)
            
        HX.Geometry.header_shape = str(Geometry.find("Header_Shape").text)
        if HX.Geometry.header_shape == "Rectangle":
            HX.Geometry.header_shape_index = 0
            HX.Geometry.header_a_dim = float(Geometry.find("Header_Dimension_a").text)
            HX.Geometry.header_b_dim = float(Geometry.find("Header_Dimension_b").text)
        elif HX.Geometry.header_shape == "Circle":
            HX.Geometry.header_shape_index = 1
            HX.Geometry.header_a_dim = float(Geometry.find("Header_Dimension_a").text)
        
        HX.Geometry.header_height = float(Geometry.find("Header_Height").text)
        HX.Geometry.Fin_t = float(Geometry.find("Fin_Thickness").text)
        HX.Geometry.Fin_l = float(Geometry.find("Fin_Length").text)
        HX.Geometry.Fin_FPI = float(Geometry.find("Fins_FPI").text)
        try:
            HX.Geometry.Fin_on_side = bool(float(Geometry.find("Fins_On_The_Sides").text))
        except:
            HX.Geometry.Fin_on_side = False
            
        if HX.Geometry.Fin_on_side:
            HX.Geometry.Fin_on_side_index = 1
        else:
            HX.Geometry.Fin_on_side_index = 0
        
        HX.Geometry.Fin_type = str(Geometry.find("Fin_Type").text)
        if HX.Geometry.Fin_type == "Louvered":
            HX.Geometry.Fin_type_index = 0
            HX.Geometry.Fin_llouv = float(Geometry.find("Fin_Louver_Length").text)
            HX.Geometry.Fin_lp = float(Geometry.find("Fin_Louver_Pitch").text)
            HX.Geometry.Fin_lalpha = float(Geometry.find("Fin_Louver_Angle").text)
        
        HX.Geometry.Tube_k = float(Geometry.find("Tube_Thermal_Conductivity").text)
        HX.Geometry.Fin_k = float(Geometry.find("Fin_Thermal_Conductivity").text)
        HX.Geometry.Header_DP = float(Geometry.find("Header_Pressure_Drop").text)

        HX.superheat_HTC_corr = int(root.find("Superheat_HTC_Correlation").text)
        HX.superheat_HTC_correction = float(root.find("Superheat_HTC_Correlation_Correction").text)
        HX.superheat_DP_corr = int(root.find("Superheat_DP_Correlation").text)
        HX.superheat_DP_correction = float(root.find("Superheat_DP_Correlation_Correction").text)

        HX._2phase_HTC_corr = int(root.find("Two_Phase_HTC_Correlation").text)
        HX._2phase_HTC_correction = float(root.find("Two_Phase_HTC_Correlation_Correction").text)
        HX._2phase_DP_corr = int(root.find("Two_Phase_DP_Correlation").text)
        HX._2phase_DP_correction = float(root.find("Two_Phase_DP_Correlation_Correction").text)

        HX._2phase_charge_corr = int(float(root.find("Two_Phase_Charge_Correlation").text))

        HX.subcool_HTC_corr = int(root.find("Subcool_HTC_Correlation").text)
        HX.subcool_HTC_correction = float(root.find("Subcool_HTC_Correlation_Correction").text)
        HX.subcool_DP_corr = int(root.find("Subcool_DP_Correlation").text)
        HX.subcool_DP_correction = float(root.find("Subcool_DP_Correlation_Correction").text)

        HX.air_dry_HTC_corr = int(root.find("Air_Dry_HTC_Correlation").text)
        HX.air_dry_HTC_correction = float(root.find("Air_Dry_HTC_Correction").text)
        HX.air_dry_DP_corr = int(root.find("Air_Dry_DP_Correlation").text)
        HX.air_dry_DP_correction = float(root.find("Air_Dry_DP_Correction").text)
        HX.air_wet_HTC_corr = int(root.find("Air_Wet_HTC_Correlation").text)
        HX.air_wet_HTC_correction = float(root.find("Air_Wet_HTC_Correction").text)
        HX.air_wet_DP_corr = int(root.find("Air_Wet_DP_Correlation").text)
        HX.air_wet_DP_correction = float(root.find("Air_Wet_DP_Correction").text)

        h_a_wet_on = root.find("Use_Wet_air_HTC_Correlation")
        if h_a_wet_on != None:
            HX.h_a_wet_on = bool(float(h_a_wet_on.text))
            
        DP_a_wet_on = root.find("Use_Wet_air_DP_Correlation")
        if DP_a_wet_on != None:
            HX.DP_a_wet_on = bool(float(DP_a_wet_on.text))

        HX.Geometry.defined = True
        return(1,HX)
    except:
        import traceback
        print(traceback.format_exc())
        return (0,0)

def read_line_file(path):
    try:
        class values():
            pass
        line = values()
        tree = ET.parse(path)
        root = tree.getroot()
        if root.tag != "Line":
            root = root.find("Line")
        
        line.Line_name = str(root.find("Line_Name").text)
        line.Line_length = float(root.find("Line_Length").text)
        line.Line_OD = float(root.find("Line_Outer_Diameter").text)
        line.Line_ID = float(root.find("Line_Inner_Diameter").text)
        line.Line_insulation_t = float(root.find("Insulation_Thickness").text)
        line.Line_e_D = float(root.find("Line_Internal_Roughness").text)
        line.Line_tube_k = float(root.find("Line_Thermal_Conductivity").text)
        line.Line_insulation_k = float(root.find("Insulation_Thermal_Conductivity").text)
        line.Line_surrounding_T = float(root.find("Surrounding_Temperature").text)
        line.Line_surrounding_HTC = float(root.find("Surrounding_HTC").text)
        line.Line_N_segments = int(root.find("Number_of_Segments").text)
        line.Line_q_tolerance = float(root.find("Heat_Transfer_Error_Tolerance").text)
        line.Line_HT_correction = float(root.find("Heat_Transfer_Correction_Factor").text)
        line.Line_DP_correction = float(root.find("Pressure_Drop_Correction_Factor").text)
        line.Line_HT_enabled = str(root.find("Heat_Transfer_Enabled").text)
        line.Line_DP_enabled = str(root.find("Pressure_Drop_Enabled").text)
        Line_N_90_bends = root.find("Number_of_90_bends")
        if Line_N_90_bends != None:
            line.Line_N_90_bends = int(Line_N_90_bends.text)
        else:
            line.Line_N_90_bends = 0
            
        Line_N_180_bends = root.find("Number_of_180_bends")
        if Line_N_180_bends != None:
            line.Line_N_180_bends = int(Line_N_180_bends.text)
        else:
            line.Line_N_180_bends = 0

        return(1,line)
    except:
        import traceback
        print(traceback.format_exc())
        return (0,0)
    
def write_line_file(line,path):
    try:
        data = ET.Element('Line')
        Line_name = ET.SubElement(data, 'Line_Name')
        Line_name.text = str(line.Line_name)
        Line_length = ET.SubElement(data, 'Line_Length')
        Line_length.text = str(line.Line_length)
        Line_OD = ET.SubElement(data, 'Line_Outer_Diameter')
        Line_OD.text = str(line.Line_OD)
        Line_ID = ET.SubElement(data, 'Line_Inner_Diameter')
        Line_ID.text = str(line.Line_ID)
        Line_insulation_t = ET.SubElement(data, 'Insulation_Thickness')
        Line_insulation_t.text = str(line.Line_insulation_t)
        Line_e_D = ET.SubElement(data, 'Line_Internal_Roughness')
        Line_e_D.text = str(line.Line_e_D)
        Line_tube_k = ET.SubElement(data, 'Line_Thermal_Conductivity')
        Line_tube_k.text = str(line.Line_tube_k)
        Line_insulation_k = ET.SubElement(data, 'Insulation_Thermal_Conductivity')
        Line_insulation_k.text = str(line.Line_insulation_k)
        Line_surrounding_T = ET.SubElement(data, 'Surrounding_Temperature')
        Line_surrounding_T.text = str(line.Line_surrounding_T)
        Line_surrounding_HTC = ET.SubElement(data, 'Surrounding_HTC')
        Line_surrounding_HTC.text = str(line.Line_surrounding_HTC)
        Line_N_segments = ET.SubElement(data, 'Number_of_Segments')
        Line_N_segments.text = str(line.Line_N_segments)
        Line_q_tolerance = ET.SubElement(data, 'Heat_Transfer_Error_Tolerance')
        Line_q_tolerance.text = str(line.Line_q_tolerance)
        Line_HT_correction = ET.SubElement(data, 'Heat_Transfer_Correction_Factor')
        Line_HT_correction.text = str(line.Line_HT_correction)
        Line_DP_correction = ET.SubElement(data, 'Pressure_Drop_Correction_Factor')
        Line_DP_correction.text = str(line.Line_DP_correction)
        Line_HT_enabled = ET.SubElement(data, 'Heat_Transfer_Enabled')
        Line_HT_enabled.text = str(line.Line_HT_enabled)
        Line_DP_enabled = ET.SubElement(data, 'Pressure_Drop_Enabled')
        Line_DP_enabled.text = str(line.Line_DP_enabled)
        Line_N_90_bends = ET.SubElement(data, 'Number_of_90_bends')
        Line_N_90_bends.text = str(line.Line_N_90_bends)
        Line_N_180_bends = ET.SubElement(data, 'Number_of_180_bends')
        Line_N_180_bends.text = str(line.Line_N_180_bends)

        mydata = str(ET.tostring(data, pretty_print=True),"utf-8")
        with open(path, "w") as myfile:
            myfile.write(mydata)
        return 1
    except:
        return 0

def read_capillary_file(path):
    try:
        class values():
            pass
        capillary = values()
        tree = ET.parse(path)
        root = tree.getroot()
        if root.tag != "Capillary":
            root = root.find("Capillary")
        
        capillary.Capillary_name = str(root.find("Capillary_Name").text)
        capillary.Capillary_length = float(root.find("Capillary_Length").text)
        capillary.Capillary_D = float(root.find("Capillary_Diameter").text)
        capillary.Capillary_entrance_D = float(root.find("Capillary_Entrance_Diameter").text)
        capillary.Capillary_N_tubes = int(root.find("Number_of_Parallel_Tubes").text)
        capillary.Capillary_DP_tolerance = float(root.find("Pressure_Drop_Tolerance").text)
        capillary.Capillary_DT = float(root.find("Discretization_Temperature_Two_Phase").text)
        Capillary_correlation = root.find("Correlation")
        if Capillary_correlation != None:
            capillary.Capillary_correlation = int(Capillary_correlation.text)
        else:
            capillary.Capillary_correlation = 0

        return(1,capillary)
    except:
        import traceback
        print(traceback.format_exc())
        return (0,0)
    
def write_capillary_file(capillary,path):
    try:
        data = ET.Element('Capillary')
        Capillary_name = ET.SubElement(data, 'Capillary_Name')
        Capillary_name.text = str(capillary.Capillary_name)
        Capillary_length = ET.SubElement(data, 'Capillary_Length')
        Capillary_length.text = str(capillary.Capillary_length)
        Capillary_D = ET.SubElement(data, 'Capillary_Diameter')
        Capillary_D.text = str(capillary.Capillary_D)
        Capillary_entrance_D = ET.SubElement(data, 'Capillary_Entrance_Diameter')
        Capillary_entrance_D.text = str(capillary.Capillary_entrance_D)
        Capillary_N_tubes = ET.SubElement(data, 'Number_of_Parallel_Tubes')
        Capillary_N_tubes.text = str(capillary.Capillary_N_tubes)
        Capillary_DP_tolerance = ET.SubElement(data, 'Pressure_Drop_Tolerance')
        Capillary_DP_tolerance.text = str(capillary.Capillary_DP_tolerance)
        Capillary_DT = ET.SubElement(data, 'Discretization_Temperature_Two_Phase')
        Capillary_DT.text = str(capillary.Capillary_DT)
        Capillary_correlation = ET.SubElement(data, 'Correlation')
        Capillary_correlation.text = str(capillary.Capillary_correlation)

        mydata = str(ET.tostring(data, pretty_print=True),"utf-8")
        with open(path, "w") as myfile:
            myfile.write(mydata)
        return 1
    except:
        import traceback
        print(traceback.format_exc())
        return 0

def read_cycle_file(path):
    try:
        class values():
            pass
        cycle = values()
        tree = ET.parse(path)
        root = tree.getroot()
        if root.tag != "Cycle":
            root = root.find("Cycle")
        
        cycle.Cycle_refrigerant = str(root.find("Cycle_refrigerant").text)
        cycle.Condenser_type = int(root.find("Condenser_type").text)
        cycle.Evaporator_type = int(root.find("Evaporator_type").text)
        cycle.First_condition = int(root.find("First_condition").text)
        if cycle.First_condition == 0:
            cycle.Subcooling = float(root.find("Subcooling").text)
        elif cycle.First_condition == 1:
            cycle.Charge = float(root.find("Charge").text)
        cycle.Cycle_mode_index = int(root.find("Cycle_mode").text)
        cycle.Ref_library_index = int(root.find("Ref_library").text)
        cycle.Expansion_device = int(root.find("Expansion_device").text)
        if cycle.Expansion_device == 0:
            cycle.Superheat_location = int(root.find("Superheat_location").text)
            cycle.Superheat = float(root.find("Superheat").text)
        cycle.Solver = int(root.find("Solver").text)
        Energy_resid = root.find("Energy_resid")
        if Energy_resid != None:
            cycle.Energy_resid = float(root.find("Energy_resid").text)
        cycle.Pressire_resid = float(root.find("Pressire_resid").text)
        Mass_flowrate_resid = root.find("Mass_flowrate_resid")
        if Mass_flowrate_resid != None:
            cycle.Mass_flowrate_resid = float(root.find("Mass_flowrate_resid").text)
        Mass_resid = root.find("Mass_resid")
        if Mass_resid != None:
            cycle.Mass_resid = float(root.find("Mass_resid").text)
        cycle.Tevap_guess_type = int(root.find("Tevap_guess_type").text)        
        if cycle.Tevap_guess_type == 1:
            cycle.Tevap_guess = float(root.find("Tevap_guess").text)
        cycle.Tcond_guess_type = int(root.find("Tcond_guess_type").text)        
        if cycle.Tcond_guess_type == 1:
            cycle.Tcond_guess = float(root.find("Tcond_guess").text)

        Capacity_target = root.find("Capacity_target")
        if Capacity_target != None:
            cycle.Capacity_target = float(Capacity_target.text)

        Test_Condition = root.find("Test_Condition")
        if Test_Condition != None:
            cycle.Test_cond = str(Test_Condition.text)

        Accumulator_charge_percentage = root.find("Accumulator_charge_percentage")
        if Accumulator_charge_percentage != None:
            cycle.accum_charge_per = float(Accumulator_charge_percentage.text)
        else:
            cycle.accum_charge_per = 0.7

        condenser_selected = root.find("condenser_selected")
        if condenser_selected != None:
            cycle.condenser_selected = str(root.find("condenser_selected").text)

        evaporator_selected = root.find("evaporator_selected")
        if evaporator_selected != None:
            cycle.evaporator_selected = str(root.find("evaporator_selected").text)

        liquidline_selected = root.find("liquidline_selected")
        if liquidline_selected != None:
            cycle.liquidline_selected = str(root.find("liquidline_selected").text)

        suctionline_selected = root.find("suctionline_selected")
        if suctionline_selected != None:
            cycle.suctionline_selected = str(root.find("suctionline_selected").text)

        twophaseline_selected = root.find("twophaseline_selected")
        if twophaseline_selected != None:
            cycle.twophaseline_selected = str(root.find("twophaseline_selected").text)

        dischargeline_selected = root.find("dischargeline_selected")
        if dischargeline_selected != None:
            cycle.dischargeline_selected = str(root.find("dischargeline_selected").text)

        compressor_selected = root.find("compressor_selected")
        if compressor_selected != None:
            cycle.compressor_selected = str(root.find("compressor_selected").text)

        capillary_selected = root.find("capillary_selected")
        if capillary_selected != None:
            cycle.capillary_selected = str(root.find("capillary_selected").text)
        
        parametric_tree = root.find("Parametric_data")
        if parametric_tree != None:
            parametric_data = np.zeros([9,2],dtype=object)
            for i,row in enumerate(parametric_data):
                parametric_row = parametric_tree.find("Component_"+str(i+1))
                if parametric_row != None:
                    N_parameters = int(parametric_row.find("N_parameters").text)
                    parameters_array = np.zeros([N_parameters,4],dtype=object)
                    for j,element in enumerate(parameters_array):
                        parameter_value = parametric_row.find("Parameter_"+str(j+1))
                        if parameter_value != None:
                            parameter_values = parameter_value.text.split(",")
                            parameter_values = [value.strip() for value in parameter_values]
                            try:
                                values_list = []
                                for value in parameter_values:
                                    if int(float(value)) == float(value):
                                        values_list.append(int(float(value)))
                                    else:
                                        values_list.append(float(value))
                                    parameter_values = tuple(values_list)                                
                            except ValueError:
                                import traceback
                                print(traceback.format_exc())
                                parameter_values = tuple(parameter_values)
                            parameter_name = parametric_row.find("Parameter_"+str(j+1)+"_name").text
                            parameter_unit = parametric_row.find("Parameter_"+str(j+1)+"_unit").text
                            parameters_array[j,:] = [1,parameter_values,parameter_name,parameter_unit]

                        elif (i in [7,8]):
                            circuits = parametric_row.find("N_Circuits")
                            if circuits != None:
                                N_circuits = int(float(parametric_row.find("N_Circuits").text))
                                circuits_data = []
                                for z in range(N_circuits):
                                    circuit = parametric_row.find("Circuit_"+str(z+1))
                                    N_parameters = int(float(circuit.find("N_parameters").text))
                                    parametric_data_circuit = np.zeros([N_parameters,4],dtype=object)
                                    for k in range(N_parameters):
                                        parameter_value = circuit.find("Parameter_"+str(j+1)+"_"+str(z+1)+"_"+str(k+1))
                                        if parameter_value != None:
                                            parameter_values = parameter_value.text.split(",")
                                            parameter_values = [value.strip() for value in parameter_values]
                                            try:
                                                values_list = []
                                                for value in parameter_values:
                                                    if int(float(value)) == float(value):
                                                        values_list.append(int(float(value)))
                                                    else:
                                                        values_list.append(float(value))
                                                    parameter_values = tuple(values_list)                                
                                            except ValueError:
                                                import traceback
                                                print(traceback.format_exc())
                                                parameter_values = tuple(parameter_values)
                                            parameter_name = circuit.find("Parameter_"+str(j+1)+"_name").text
                                            parameter_unit = circuit.find("Parameter_"+str(j+1)+"_unit").text
                                            parametric_data_circuit[k,:] = [1,parameter_values,parameter_name,parameter_unit]                                            
                                    circuits_data.append(parametric_data_circuit)
                            else:
                                circuits_data = 0
                            parameters_array[j,:] = [0,circuits_data,'','']
                    parametric_data[i,:] = [1,parameters_array]
            cycle.parametric_data = parametric_data
        return(1,cycle)
    except:
        import traceback
        print(traceback.format_exc())
        return (0,0)

def write_cycle_with_components_file(cycle,path):
    try:
        temp_dir = appdirs.user_data_dir("EGSim")+"/Temp/"
        database_dir = appdirs.user_data_dir("EGSim")+"/Database/"
        if not os.path.exists(temp_dir):
            os.mkdir(temp_dir)
        cycle_filename = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '.cycle'
        result = write_cycle_file(cycle,temp_dir+cycle_filename)
        if result:
            database_zip = zipfile.ZipFile(path, 'w')
            database_zip.write(temp_dir+cycle_filename, cycle_filename, compress_type=zipfile.ZIP_DEFLATED)
            
            files = []
            if hasattr(cycle,"condenser_selected"):
                files.append(cycle.condenser_selected)
    
            if hasattr(cycle,"evaporator_selected"):
                files.append(cycle.evaporator_selected)
    
            if hasattr(cycle,"liquidline_selected"):
                files.append(cycle.liquidline_selected)
    
            if hasattr(cycle,"suctionline_selected"):
                files.append(cycle.suctionline_selected)
    
            if hasattr(cycle,"twophaseline_selected"):
                files.append(cycle.twophaseline_selected)
    
            if hasattr(cycle,"dischargeline_selected"):
                files.append(cycle.dischargeline_selected)
    
            if hasattr(cycle,"compressor_selected"):
                files.append(cycle.compressor_selected)
    
            if hasattr(cycle,"capillary_selected"):
                files.append(cycle.capillary_selected)
            
            files = set(files)
            
            for file in files:
                database_zip.write(database_dir+file, file, compress_type=zipfile.ZIP_DEFLATED)
            database_zip.close()
            os.remove(temp_dir+cycle_filename)
            return 1
        else:
            return 0
    except:
        import traceback
        print(traceback.format_exc())
        return 0


def read_cycle_with_components_file(path):
    try:
        files_to_delete_file = appdirs.user_data_dir("EGSim")+"/Temp/files_to_delete.ini"
        database_dir = appdirs.user_data_dir("EGSim")+"/Database/"
        if not os.path.exists(files_to_delete_file):
            open(files_to_delete_file, 'a').close()
        files_list = []
        with open(files_to_delete_file, newline='') as csvfile:
            files = csv.reader(csvfile)
            for row in files:
                for file in row:
                    if file.strip() != "":
                        files_list.append(file.strip())
        files_deleted = []
        for file in files_list:
            if os.path.exists(database_dir+file):
                os.remove(database_dir+file)
        file = open(files_to_delete_file, 'w')
        file.write("")
        file.close()
        
        temp_dir = appdirs.user_data_dir("EGSim")+"/Temp/"
        files_to_delete_file = appdirs.user_data_dir("EGSim")+"/Temp/files_to_delete.ini"
        if not os.path.exists(temp_dir):
            os.mkdir(temp_dir)
        if not os.path.exists(files_to_delete_file):
            open(files_to_delete_file, 'a').close()
        
        temp_dir_to_exctract = temp_dir + datetime.datetime.now().strftime("%Y%m%d%H%M%S")+"/"
        os.mkdir(temp_dir_to_exctract)
        database_zip = zipfile.ZipFile(path)
        database_zip.extractall(temp_dir_to_exctract)
        database_zip.close()
        _, _, files = next(os.walk(temp_dir_to_exctract))
        result = (0,0)
        for file in files:
            if file[-6:].lower() == ".cycle":
                cycle_file = temp_dir_to_exctract+file
                result = read_cycle_file(cycle_file)
        if result[0]:
            os.remove(cycle_file)
            _, _, files = next(os.walk(temp_dir_to_exctract))
            files_to_remove = []
            for file in files:
                if not os.path.exists(database_dir+file):
                    os.rename(temp_dir_to_exctract+file, database_dir+file)
                    files_to_remove.append(file)
                else:
                    path, filename_with_extension = os.path.split(file)
                    Old_name, ext = os.path.splitext(filename_with_extension)
                    finished = False
                    i = 0
                    while not finished:
                        New_name = str(int(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))+i)
                        new_file = file.replace(Old_name,New_name)
                        path, New_filename_with_extension = os.path.split(new_file)
                        try:
                            os.rename(temp_dir_to_exctract+file, database_dir+new_file)

                            if hasattr(result[1],"condenser_selected"):
                                if result[1].condenser_selected == filename_with_extension:
                                    result[1].condenser_selected = New_filename_with_extension

                            if hasattr(result[1],"evaporator_selected"):
                                if result[1].evaporator_selected == filename_with_extension:
                                    result[1].evaporator_selected = New_filename_with_extension

                            if hasattr(result[1],"liquidline_selected"):
                                if result[1].liquidline_selected == filename_with_extension:
                                    result[1].liquidline_selected = New_filename_with_extension

                            if hasattr(result[1],"suctionline_selected"):
                                if result[1].suctionline_selected == filename_with_extension:
                                    result[1].suctionline_selected = New_filename_with_extension

                            if hasattr(result[1],"twophaseline_selected"):
                                if result[1].twophaseline_selected == filename_with_extension:
                                    result[1].twophaseline_selected = New_filename_with_extension

                            if hasattr(result[1],"dischargeline_selected"):
                                if result[1].dischargeline_selected == filename_with_extension:
                                    result[1].dischargeline_selected = New_filename_with_extension

                            if hasattr(result[1],"compressor_selected"):
                                if result[1].compressor_selected == filename_with_extension:
                                    result[1].compressor_selected = New_filename_with_extension

                            if hasattr(result[1],"capillary_selected"):
                                if result[1].capillary_selected == filename_with_extension:
                                    result[1].capillary_selected = New_filename_with_extension
                            
                            finished = True
                        except FileExistsError:
                            i += 1
                    files_to_remove.append(new_file)
                    
            os.rmdir(temp_dir_to_exctract)
            file_object = open(files_to_delete_file, 'a')
            if files_to_remove:
                file_object.write(",".join(files_to_remove)+",")
            file_object.close()
            return result
        else:
            _, _, files = next(os.walk(temp_dir_to_exctract))
            for file in files:
                os.remove(temp_dir_to_exctract+file)
            os.rmdir(temp_dir_to_exctract)
            return (0,0)
    except:
        import traceback
        print(traceback.format_exc())
        return (0,0)

def write_cycle_file(cycle,path):
    try:
        data = ET.Element('Cycle')

        Cycle_refrigerant = ET.SubElement(data, 'Cycle_refrigerant')
        Cycle_refrigerant.text = str(cycle.Cycle_refrigerant)

        Condenser_type = ET.SubElement(data, 'Condenser_type')
        Condenser_type.text = str(cycle.Condenser_type)

        Evaporator_type = ET.SubElement(data, 'Evaporator_type')
        Evaporator_type.text = str(cycle.Evaporator_type)

        First_condition = ET.SubElement(data, 'First_condition')
        First_condition.text = str(cycle.First_condition)

        if cycle.First_condition == 0:
            Subcooling = ET.SubElement(data, 'Subcooling')
            Subcooling.text = str(cycle.Subcooling)

        elif cycle.First_condition == 1:
            Charge = ET.SubElement(data, 'Charge')
            Charge.text = str(cycle.Charge)

        Cycle_mode = ET.SubElement(data, 'Cycle_mode')
        Cycle_mode.text = str(cycle.Cycle_mode_index)

        Ref_library = ET.SubElement(data, 'Ref_library')
        Ref_library.text = str(cycle.Ref_library_index)
            
        Expansion_device = ET.SubElement(data, 'Expansion_device')
        Expansion_device.text = str(cycle.Expansion_device)
        
        if cycle.Expansion_device == 0:
            Superheat_location = ET.SubElement(data, 'Superheat_location')
            Superheat_location.text = str(cycle.Superheat_location)
    
            Superheat = ET.SubElement(data, 'Superheat')
            Superheat.text = str(cycle.Superheat)

        Solver = ET.SubElement(data, 'Solver')
        Solver.text = str(cycle.Solver)
        
        if hasattr(cycle,"Energy_resid"):
            Energy_resid = ET.SubElement(data, 'Energy_resid')
            Energy_resid.text = str(cycle.Energy_resid)

        Pressire_resid = ET.SubElement(data, 'Pressire_resid')
        Pressire_resid.text = str(cycle.Pressire_resid)

        if hasattr(cycle,"Mass_flowrate_resid"):
            Mass_flowrate_resid = ET.SubElement(data, 'Mass_flowrate_resid')
            Mass_flowrate_resid.text = str(cycle.Mass_flowrate_resid)

        if hasattr(cycle,"Mass_resid"):
            Mass_resid = ET.SubElement(data, 'Mass_resid')
            Mass_resid.text = str(cycle.Mass_resid)

        Tevap_guess_type = ET.SubElement(data, 'Tevap_guess_type')
        Tevap_guess_type.text = str(cycle.Tevap_guess_type)

        if cycle.Tevap_guess_type == 1:
            Tevap_guess = ET.SubElement(data, 'Tevap_guess')
            Tevap_guess.text = str(cycle.Tevap_guess)

        Tcond_guess_type = ET.SubElement(data, 'Tcond_guess_type')
        Tcond_guess_type.text = str(cycle.Tcond_guess_type)

        Capacity_target = ET.SubElement(data, 'Capacity_target')
        Capacity_target.text = str(cycle.Capacity_target)

        Accumulator_charge_percentage = ET.SubElement(data, 'Accumulator_charge_percentage')
        Accumulator_charge_percentage.text = str(cycle.accum_charge_per)

        Test_Condition = ET.SubElement(data, 'Test_Condition')
        Test_Condition.text = str(cycle.Test_cond)

        if cycle.Tcond_guess_type == 1:
            Tcond_guess = ET.SubElement(data, 'Tcond_guess')
            Tcond_guess.text = str(cycle.Tcond_guess)

        if hasattr(cycle,'condenser_selected'):
            condenser_selected = ET.SubElement(data, 'condenser_selected')
            condenser_selected.text = str(cycle.condenser_selected)

        if hasattr(cycle,'evaporator_selected'):
            evaporator_selected = ET.SubElement(data, 'evaporator_selected')
            evaporator_selected.text = str(cycle.evaporator_selected)

        if hasattr(cycle,'liquidline_selected'):
            liquidline_selected = ET.SubElement(data, 'liquidline_selected')
            liquidline_selected.text = str(cycle.liquidline_selected)

        if hasattr(cycle,'suctionline_selected'):
            suctionline_selected = ET.SubElement(data, 'suctionline_selected')
            suctionline_selected.text = str(cycle.suctionline_selected)

        if hasattr(cycle,'twophaseline_selected'):
            twophaseline_selected = ET.SubElement(data, 'twophaseline_selected')
            twophaseline_selected.text = str(cycle.twophaseline_selected)

        if hasattr(cycle,'dischargeline_selected'):
            dischargeline_selected = ET.SubElement(data, 'dischargeline_selected')
            dischargeline_selected.text = str(cycle.dischargeline_selected)

        if hasattr(cycle,'compressor_selected'):
            compressor_selected = ET.SubElement(data, 'compressor_selected')
            compressor_selected.text = str(cycle.compressor_selected)

        if hasattr(cycle,'capillary_selected'):
            capillary_selected = ET.SubElement(data, 'capillary_selected')
            capillary_selected.text = str(cycle.capillary_selected)
        
        if hasattr(cycle,'parametric_data'):
            parametric_tree = ET.SubElement(data, 'Parametric_data')
            for i,row in enumerate(cycle.parametric_data):
                if row[0]:
                    parametric_row = ET.SubElement(parametric_tree, "Component_"+str(i+1))
                    parametric = row[1]
                    parametric_row_header = ET.SubElement(parametric_row, "N_parameters")
                    parametric_row_header.text = str(len(parametric))
                    for j,element in enumerate(parametric):
                        if element[0]:
                            parametric_row_element = ET.SubElement(parametric_row, "Parameter_"+str(j+1))
                            parametric_row_element.text = ', '.join([str(value) for value in element[1]])
                            parametric_row_name = ET.SubElement(parametric_row, "Parameter_"+str(j+1)+"_name")
                            parametric_row_name.text = str(element[2])
                            parametric_row_unit = ET.SubElement(parametric_row, "Parameter_"+str(j+1)+"_unit")
                            parametric_row_unit.text = str(element[3])
                        elif (i in [7,8]) and (not isinstance(element[1],int)) and (not element[0]):
                            circuits_row_header = ET.SubElement(parametric_row, "N_Circuits")
                            circuits_row_header.text = str(len(element[1]))
                            for z,circuit in enumerate(element[1]):
                                circuit_row = ET.SubElement(parametric_row, "Circuit_"+str(z+1))
                                circuits_Parameter_row_header = ET.SubElement(circuit_row, "N_parameters")
                                circuits_Parameter_row_header.text = str(len(circuit))
                                for k,element_interior in enumerate(circuit):
                                    if element_interior[0]:
                                        parametric_row_element_interior = ET.SubElement(circuit_row, "Parameter_"+str(j+1)+"_"+str(z+1)+"_"+str(k+1))
                                        parametric_row_element_interior.text = ', '.join([str(value) for value in element_interior[1]])                                
                                        parametric_row_element_interior_name = ET.SubElement(circuit_row, "Parameter_"+str(j+1)+"_"+str(z+1)+"_"+str(k+1))
                                        parametric_row_element_interior_name.text = str(element_interior[2])
                                        parametric_row_element_interior_unit = ET.SubElement(circuit_row, "Parameter_"+str(j+1)+"_"+str(z+1)+"_"+str(k+1))
                                        parametric_row_element_interior_unit.text = str(element_interior[3])
                            
        mydata = str(ET.tostring(data, pretty_print=True),"utf-8")
        with open(path, "w") as myfile:
            myfile.write(mydata)
        return 1
    except:
        import traceback
        print(traceback.format_exc())
        return 0

def load_compressor_map_file(path):
    try:
        map_values = pd.read_csv(path,index_col=None,usecols=[0,1,2])
        map_values = map_values.apply(lambda x: pd.to_numeric(x, errors='coerce') )
        map_values = map_values.dropna()
        map_values = map_values.to_numpy()
        return (1,map_values)
    except:
        import traceback
        print(traceback.format_exc())
        return (0,)

def save_results_excel(Cycles,Path):
    try:
        writer = pd.ExcelWriter(Path, engine='openpyxl')
        try:
            mode = Cycles.Mode
        except:
            mode = Cycles[0].Mode

        if mode == "AC":
            condenser_name = "Outdoor Unit"
            evaporator_name = "Indoor Unit"
        elif mode == "HP":
            condenser_name = "Indoor Unit"
            evaporator_name = "Outdoor Unit"
                
        outputs = create_outputs_array(Cycles)
        header = ["Parameter","Unit","Value"]
        for output in outputs:
            output_list = pd.DataFrame(output[1],columns=header)
            name = output[0].replace("Evaporator",evaporator_name)
            name = name.replace("Condenser",condenser_name)
            output_list.to_excel(writer, sheet_name=name)
        writer.save()
        return 1
    except:
        import traceback
        print(traceback.format_exc())
        return 0

def save_results_excel_parametric(outputs,Path):
    try:
        writer = pd.ExcelWriter(Path, engine='openpyxl')
        Configurations = []
        outputs_only = []
        
        outputs[0].to_excel(writer, sheet_name="Parametric Configurations")
        
        for output in outputs[1:]:
            Configurations.append("Configuration "+str(output[0]))
            outputs_only.append(output[1])
            for row in output[1][0][1]:
                if "Heat pump" in row[2]:
                    mode = "HP"
                elif "Air conditioning" in row[2]:
                    mode = "AC"
        if mode == "AC":
            condenser_name = "Outdoor Unit"
            evaporator_name = "Indoor Unit"
        elif mode == "HP":
            condenser_name = "Indoor Unit"
            evaporator_name = "Outdoor Unit"
        
        header = ["Parameter","Unit"]+Configurations
        outputs_list = concatenate_outputs(outputs_only)
        for output in outputs_list:
            output_list = pd.DataFrame(output[1],columns=header)
            output_list = output_list.transpose()
            name = output[0].replace("Evaporator",evaporator_name)
            name = name.replace("Condenser",condenser_name)
            output_list.to_excel(writer, sheet_name=name)
        writer.save()
        return 1
    except:
        import traceback
        print(traceback.format_exc())
        return 0

def save_fintube_results_excel(HX,Path):
    def construct_table(output_list, writer,sheet_name):
        for i,row in enumerate(output_list):
            row = list(row)
            value = row[2]
            if value == None:
                value = 'Not Defined'
            elif not isinstance(value,str):
                if not isinstance(value,bool):
                    value = "%.5g" % value
                else:
                    if value:
                        value = "Yes"
                    else:
                        value = "No"
            row[2] = value
        output_list = pd.DataFrame(output_list,columns=["Parameter","Unit","Value"])
        output_list.to_excel(writer, sheet_name=sheet_name)
        return
    try:
        writer = pd.ExcelWriter(Path, engine='openpyxl')
        HX_table = construct_table(HX.OutputList(),writer,"Heat Exchanger Overall")
        HX_Circuits_tables = []
        for i,Circuit in enumerate(HX.Circuits):
            HX_Circuits_tables.append(construct_table(Circuit.OutputList(),writer,"Heat Exchanger Circuit "+str(i+1)))
        HX_Fan_table = construct_table(HX.Fan.OutputList(),writer, "Heat Exchanger Fan")
        writer.save()
        return 1
    except:
        import traceback
        print(traceback.format_exc())
        return 0

def save_Microchannel_results_excel(HX,Path):
    def construct_table(output_list, writer,sheet_name):
        for i,row in enumerate(output_list):
            row = list(row)
            value = row[2]
            if value == None:
                value = 'Not Defined'
            elif not isinstance(value,str):
                if not isinstance(value,bool):
                    value = "%.5g" % value
                else:
                    if value:
                        value = "Yes"
                    else:
                        value = "No"
            row[2] = value
        output_list = pd.DataFrame(output_list,columns=["Parameter","Unit","Value"])
        output_list.to_excel(writer, sheet_name=sheet_name)
        return
    try:
        writer = pd.ExcelWriter(Path, engine='openpyxl')
        HX_table = construct_table(HX.OutputList(),writer,"Heat Exchanger Overall")
        HX_Fan_table = construct_table(HX.Fan.OutputList(),writer, "Heat Exchanger Fan")
        writer.save()
        return 1
    except:
        return 0

def save_Line_results_excel(Line,Path):
    def construct_table(output_list, writer,sheet_name):
        for i,row in enumerate(output_list):
            row = list(row)
            value = row[2]
            if value == None:
                value = 'Not Defined'
            elif not isinstance(value,str):
                if not isinstance(value,bool):
                    value = "%.5g" % value
                else:
                    if value:
                        value = "Yes"
                    else:
                        value = "No"
            row[2] = value
        output_list = pd.DataFrame(output_list,columns=["Parameter","Unit","Value"])
        output_list.to_excel(writer, sheet_name=sheet_name)
        return
    try:
        writer = pd.ExcelWriter(Path, engine='openpyxl')
        Line_table = construct_table(Line.OutputList(),writer,"Line results")
        writer.save()
        return 1
    except:
        return 0

def save_Capillary_results_excel(Capillary,Path):
    def construct_table(output_list, writer,sheet_name):
        for i,row in enumerate(output_list):
            row = list(row)
            value = row[2]
            if value == None:
                value = 'Not Defined'
            elif not isinstance(value,str):
                if not isinstance(value,bool):
                    value = "%.5g" % value
                else:
                    if value:
                        value = "Yes"
                    else:
                        value = "No"
            row[2] = value
        output_list = pd.DataFrame(output_list,columns=["Parameter","Unit","Value"])
        output_list.to_excel(writer, sheet_name=sheet_name)
        return
    try:
        writer = pd.ExcelWriter(Path, engine='openpyxl')
        Capillary_table = construct_table(Capillary.OutputList(),writer,"Capillary tube results")
        writer.save()
        return 1
    except:
        return 0

def save_Compressor_results_excel(Compressor,Path):
    def construct_table(output_list, writer,sheet_name):
        for i,row in enumerate(output_list):
            row = list(row)
            value = row[2]
            if value == None:
                value = 'Not Defined'
            elif not isinstance(value,str):
                if not isinstance(value,bool):
                    value = "%.5g" % value
                else:
                    if value:
                        value = "Yes"
                    else:
                        value = "No"
            row[2] = value
        output_list = pd.DataFrame(output_list,columns=["Parameter","Unit","Value"])
        output_list.to_excel(writer, sheet_name=sheet_name)
        return
    try:
        writer = pd.ExcelWriter(Path, engine='openpyxl')
        Compressor_table = construct_table(Compressor.OutputList(),writer,"Compressor results")
        writer.save()
        return 1
    except:
        return 0

def load_refrigerant_list():
    try:
        single_refrigerants_path = appdirs.user_data_dir("EGSim")+"/Single_Refrigerants.xml"
        tree = ET.parse(single_refrigerants_path)
        root = tree.getroot()
        single_ref_list = []
        for node in root:
            ref = root.find(node.tag)
            ref_name = ref.find("Ref_name").text
            single_ref_list.append([ref_name,[ref_name],[1.0]])
        
        mixed_refrigerants_path = appdirs.user_data_dir("EGSim")+"/Mixed_Refrigerants.xml"
        tree = ET.parse(mixed_refrigerants_path)
        root = tree.getroot()
        mixed_ref_list = []
        for node in root:
            ref = root.find(node.tag)
            ref_name = ref.find("Ref_name").text
            ref_components = ref.find("Ref_components").text.split(",")
            ref_fractions = [float(i) for i in ref.find("Ref_fractions").text.split(",")]
            assert(len(ref_components) == len(ref_fractions))
            mixed_ref_list.append([ref_name,ref_components,ref_fractions])
        
        ref_list = np.array(single_ref_list + mixed_ref_list,dtype=object)
        return (1,ref_list)
    except:
        import traceback
        print(traceback.format_exc())
        return (0,)

def construct_table(outputs,old_table=None): # function used to construct tables
    for i,row in enumerate(outputs):
        row = list(row)
        value = row[2]
        if value == None:
            value = 'Not Defined'
        elif not isinstance(value,str):
            if not isinstance(value,bool):
                pass
            else:
                if value:
                    value = "Yes"
                else:
                    value = "No"
        row[2] = value
        outputs[i] = row
    if old_table is None:
        return np.array(outputs)
    else:
        outputs = np.array(outputs)
        return np.hstack((old_table,outputs[:,[2]]))

def create_outputs_array(Cycles):
        
    if not isinstance(Cycles,list):
        Cycles = [[1,Cycles]]
    Created_base = False
    for i,Cycle in enumerate(Cycles):
        if Cycle[0]:
            Cycle = Cycle[1]
        else:
            continue
        if not Created_base:
            Cycle_table = construct_table(Cycle.OutputList())
            Compressor_table = construct_table(Cycle.Compressor.OutputList())
            if Cycle.Condenser_Type == "Fin-tube":
                Condenser_table = construct_table(Cycle.Condenser.OutputList())
                Condenser_Circuits_tables = []
                for i,Circuit in enumerate(Cycle.Condenser.Circuits):
                    Condenser_Circuits_tables.append(construct_table(Circuit.OutputList()))
                Condenser_Fan_table = construct_table(Cycle.Condenser.Fan.OutputList())
            elif Cycle.Condenser_Type == "MicroChannel":
                Condenser_table = construct_table(Cycle.Condenser.OutputList())
                Condenser_Fan_table = construct_table(Cycle.Condenser.Fan.OutputList())
                Condenser_Circuits_tables = None        
            if Cycle.Evaporator_Type == "Fin-tube":
                Evaporator_table = construct_table(Cycle.Evaporator.OutputList())
                Evaporator_Circuits_tables = []
                for i,Circuit in enumerate(Cycle.Evaporator.Circuits):
                    Evaporator_Circuits_tables.append(construct_table(Circuit.OutputList()))
                Evaporator_Fan_table = construct_table(Cycle.Evaporator.Fan.OutputList())
            elif Cycle.Evaporator_Type == "MicroChannel":
                Evaporator_table = construct_table(Cycle.Evaporator.OutputList())
                Evaporator_Fan_table = construct_table(Cycle.Evaporator.Fan.OutputList())
                Evaporator_Circuits_tables = None
            Liquid_Line_table = construct_table(Cycle.Line_Liquid.OutputList())
            _2phase_Line_table = construct_table(Cycle.Line_2phase.OutputList())
            Suction_Line_table = construct_table(Cycle.Line_Suction.OutputList())
            Discharge_Line_table = construct_table(Cycle.Line_Discharge.OutputList())
            if hasattr(Cycle,"Capillary"):
                Capillary_table = construct_table(Cycle.Capillary.OutputList())
            else:
                Capillary_table = None
            Created_base = True
        else:
            Cycle_table = construct_table(Cycle.OutputList(),Cycle_table)
            Compressor_table = construct_table(Cycle.Compressor.OutputList(),Compressor_table)
            if Cycle.Condenser_Type == "Fin-tube":
                Condenser_table = construct_table(Cycle.Condenser.OutputList(),Condenser_table)
                for i,Circuit in enumerate(Cycle.Condenser.Circuits):
                    Condenser_Circuits_tables[i] = construct_table(Circuit.OutputList(),Condenser_Circuits_tables[i])
                Condenser_Fan_table = construct_table(Cycle.Condenser.Fan.OutputList(),Condenser_Fan_table)
            elif Cycle.Condenser_Type == "MicroChannel":
                Condenser_table = construct_table(Cycle.Condenser.OutputList(),Condenser_table)
                Condenser_Fan_table = construct_table(Cycle.Condenser.Fan.OutputList(),Condenser_Fan_table)
                Condenser_Circuits_tables = None
            if Cycle.Evaporator_Type == "Fin-tube":
                Evaporator_table = construct_table(Cycle.Evaporator.OutputList(),Evaporator_table)
                for i,Circuit in enumerate(Cycle.Evaporator.Circuits):
                    Evaporator_Circuits_tables[i] = construct_table(Circuit.OutputList(),Evaporator_Circuits_tables[i])
                Evaporator_Fan_table = construct_table(Cycle.Evaporator.Fan.OutputList(),Evaporator_Fan_table)
            elif Cycle.Evaporator_Type == "MicroChannel":
                Evaporator_table = construct_table(Cycle.Evaporator.OutputList(),Evaporator_table)
                Evaporator_Fan_table = construct_table(Cycle.Evaporator.Fan.OutputList(),Evaporator_Fan_table)
                Evaporator_Circuits_tables = None
            Liquid_Line_table = construct_table(Cycle.Line_Liquid.OutputList(),Liquid_Line_table)
            _2phase_Line_table = construct_table(Cycle.Line_2phase.OutputList(),_2phase_Line_table)
            Suction_Line_table = construct_table(Cycle.Line_Suction.OutputList(),Suction_Line_table)
            Discharge_Line_table = construct_table(Cycle.Line_Discharge.OutputList(),Discharge_Line_table)
            if hasattr(Cycle,"Capillary"):
                Capillary_table = construct_table(Cycle.Capillary.OutputList(),Capillary_table)
    outputs = []
    outputs.append(["Cycle",Cycle_table])
    outputs.append(["Compressor",Compressor_table])
    outputs.append(["Condenser",Condenser_table])
    outputs.append(["Condenser Fan",Condenser_Fan_table])
    if isinstance(Condenser_Circuits_tables,list):
        for i,table in enumerate(Condenser_Circuits_tables):
            outputs.append(["Condenser Circuit "+str(i+1),table])
    outputs.append(["Evaporator",Evaporator_table])
    outputs.append(["Evaporator Fan",Evaporator_Fan_table])
    if isinstance(Evaporator_Circuits_tables,list):
        for i,table in enumerate(Evaporator_Circuits_tables):
            outputs.append(["Evaporator Circuit "+str(i+1),table])
    outputs.append(["Liquid Line",Liquid_Line_table])
    outputs.append(["Two-phase Line",_2phase_Line_table])
    outputs.append(["Suction Line",Suction_Line_table])
    outputs.append(["Discharge Line",Discharge_Line_table])
    if hasattr(Cycle,"Capillary"):
        outputs.append(["Capillary Tube",Capillary_table])
    return np.array(outputs,dtype=object)

def concatenate_outputs(outputs_list):
    base_output = outputs_list[0].copy()
    if len(outputs_list) > 1:
        for output in outputs_list[1:]:
            for i,row in enumerate(base_output):
                row[1] = np.hstack((row[1],output[i,1][:,[2]]))
    return base_output

def create_parametric_data_table_to_export(parametric_table):
    N_columns = parametric_table.model().columnCount()
    N_rows = parametric_table.model().rowCount()
    table = np.zeros([N_rows+1,N_columns+1],dtype=object)
    table[0,0] = ""
    for i in range(parametric_table.model().columnCount()):
        table[0,i+1] = parametric_table.horizontalHeaderItem(i).text()
    for i in range(parametric_table.model().rowCount()):
        table[i+1,0] = parametric_table.verticalHeaderItem(i).text()
    for i in range(parametric_table.model().columnCount()):
        for j in range(parametric_table.model().rowCount()):
            table[j+1,i+1] = parametric_table.item(j,i).text()
    table = pd.DataFrame(table)
    table = table.set_index([0])
    table.columns = table.iloc[0]
    table = table[1:]
    return table

def load_ranges_creator_options():
    Properties_file = appdirs.user_data_dir("EGSim")+"/Ranges_creator_Properties.ini"
    if not os.path.exists(Properties_file):
        with open(Properties_file, 'w') as f:
            f.write("0")
    else:
        try:
            failed = False
            with open(Properties_file, 'r') as f:
                value = f.read()
                value = int(value)
                if value in [0,1]:
                    return bool(value)
                else:
                    failed = True
            if failed:
                raise
        except:
            with open(Properties_file, 'w') as f:
                f.write("0")
                return 1

def set_ranges_creator_options(value):
    Properties_file = appdirs.user_data_dir("EGSim")+"/Ranges_creator_Properties.ini"
    with open(Properties_file, 'w') as f:
        f.write(str(int(value)))

def copy_file(from_path,to_path):
    try:
        copyfile(from_path, to_path)
        return 1
    except:
        return 0

def import_fin_tube_fins_file(path):
    if os.path.exists(path):
        try:
            fins_file = appdirs.user_data_dir("EGSim")+"/Fintube_Fins.csv"
            fins_data = pd.read_csv(path,index_col=0)
            empty_cols = [col for col in fins_data.columns if (fins_data[col].isnull().all() and ("unnamed" in col.lower()))]
            fins_data.drop(empty_cols, axis=1, inplace=True)
            if (len(fins_data.columns) != 11):
                fins_data = pd.read_csv(path,index_col=None)
                empty_cols = [col for col in fins_data.columns if (fins_data[col].isnull().all() and ("unnamed" in col.lower()))]
                fins_data.drop(empty_cols, axis=1, inplace=True)
            if (len(fins_data.columns) != 11):
                raise
            fins_data.dropna(how="all",axis=0,inplace=True)
            fins_data.to_csv(fins_file)
            return True
        except:
            import traceback
            print(traceback.format_exc())
            return False
    else:
        return False

def import_microchannel_fins_file(path):
    if os.path.exists(path):
        try:
            fins_file = appdirs.user_data_dir("EGSim")+"/microchannel_fins.csv"
            fins_data = pd.read_csv(path,index_col=0)
            empty_cols = [col for col in fins_data.columns if (fins_data[col].isnull().all() and ("unnamed" in col.lower()))]
            fins_data.drop(empty_cols, axis=1, inplace=True)
            if (len(fins_data.columns) != 10):
                fins_data = pd.read_csv(path,index_col=None)
                empty_cols = [col for col in fins_data.columns if (fins_data[col].isnull().all() and ("unnamed" in col.lower()))]
                fins_data.drop(empty_cols, axis=1, inplace=True)
            if (len(fins_data.columns) != 10):
                raise
            fins_data.dropna(how="all",axis=0,inplace=True)
            fins_data.to_csv(fins_file)
            return True
        except:
            import traceback
            print(traceback.format_exc())
            return False
    else:
        return False

def import_fin_tube_tubes_file(path):
    if os.path.exists(path):
        try:
            tubes_file = appdirs.user_data_dir("EGSim")+"/fintube_tubes.csv"
            tubes_data = pd.read_csv(path,index_col=0)
            empty_cols = [col for col in tubes_data.columns if (tubes_data[col].isnull().all() and ("unnamed" in col.lower()))]
            tubes_data.drop(empty_cols, axis=1, inplace=True)
            if (len(tubes_data.columns) != 11):
                tubes_data = pd.read_csv(path,index_col=None)
                empty_cols = [col for col in tubes_data.columns if (tubes_data[col].isnull().all() and ("unnamed" in col.lower()))]
                tubes_data.drop(empty_cols, axis=1, inplace=True)
            if (len(tubes_data.columns) != 11):
                raise
            tubes_data.dropna(how="all",axis=0,inplace=True)
            tubes_data.to_csv(tubes_file)
            return True
        except:
            import traceback
            print(traceback.format_exc())
            return False
    else:
        return False

def import_microchannel_tubes_file(path):
    if os.path.exists(path):
        try:
            tubes_file = appdirs.user_data_dir("EGSim")+"/microchannel_tubes.csv"
            tubes_data = pd.read_csv(path,index_col=0)
            empty_cols = [col for col in tubes_data.columns if (tubes_data[col].isnull().all() and ("unnamed" in col.lower()))]
            tubes_data.drop(empty_cols, axis=1, inplace=True)
            if (len(tubes_data.columns) != 9):
                tubes_data = pd.read_csv(path,index_col=None)
                empty_cols = [col for col in tubes_data.columns if (tubes_data[col].isnull().all() and ("unnamed" in col.lower()))]
                tubes_data.drop(empty_cols, axis=1, inplace=True)
            if (len(tubes_data.columns) != 9):
                raise
            tubes_data.dropna(how="all",axis=0,inplace=True)
            tubes_data.to_csv(tubes_file)
            return True
        except:
            import traceback
            print(traceback.format_exc())
            return False
    else:
        return False

def import_line_tubes_file(path):
    if os.path.exists(path):
        try:
            tubes_file = appdirs.user_data_dir("EGSim")+"/line_tubes.csv"
            tubes_data = pd.read_csv(path,index_col=0)
            empty_cols = [col for col in tubes_data.columns if (tubes_data[col].isnull().all() and ("unnamed" in col.lower()))]
            tubes_data.drop(empty_cols, axis=1, inplace=True)
            if (len(tubes_data.columns) != 6):
                tubes_data = pd.read_csv(path,index_col=None)
                empty_cols = [col for col in tubes_data.columns if (tubes_data[col].isnull().all() and ("unnamed" in col.lower()))]
                tubes_data.drop(empty_cols, axis=1, inplace=True)
            if (len(tubes_data.columns) != 6):
                raise
            tubes_data.dropna(how="all",axis=0,inplace=True)
            tubes_data.to_csv(tubes_file)
            return True
        except:
            import traceback
            print(traceback.format_exc())
            return False
    else:
        return False

def save_last_location(location):
    if os.path.exists(location):
        if os.path.isdir(location):  
            path = location
        elif os.path.isfile(location):  
            path = os.path.dirname(location)
        else:
            path = None
    else:
        folder = os.path.dirname(location)
        if os.path.exists(folder):
            path = path = folder
    
    if path == None:
        path = QDir.homePath()
    
    save_file = appdirs.user_data_dir("EGSim")+"/last_path.ini"

    with open(save_file, "w") as myfile:
        myfile.write(path)

def load_last_location():
    save_file = appdirs.user_data_dir("EGSim")+"/last_path.ini"

    if os.path.exists(save_file):
        with open(save_file, "r") as myfile:
            data = myfile.read()
        if os.path.exists(data):
            path = data
        else:
            path = None
    else:
        path = None
    
    if path == None:
        path = QDir.homePath()

    return path
