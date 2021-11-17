from backend.Cycle_Fast import CycleFastClass
from copy import deepcopy
import numpy as np
from CoolProp.CoolProp import HAPropsSI

class values():
    pass

def create_ranges(cycle):
    # structure of parameter list:
    ## save to this list of hierarchy
    ## list of path hierarchy in cycle
    ## parameter name in cycle
    ## type: "int" or "float"
    
    Ranges = values()
    Parameters = []
    
    # cycle ranges
    Ranges.Cycle = values()
    if cycle.Second_Cond == "Subcooling":
        Parameters += [[["Cycle","Subcooling"],["SC_value"],"float"]]
    elif cycle.Second_Cond == "Charge":
        Parameters += [[["Cycle","Charge"],["Charge_value"],"float"]]
    
    Parameters += [[["Cycle","Superheat"],["SH_value"],"float"]]
    
    if cycle.Evaporator_Type == "Fin-tube":
        Parameters += [[["Evaporator","FinTube_air_flowrate"],["Evaporator","Vdot_ha"],"float"]]
        for i in range(len(cycle.Evaporator.Circuits)):
            Parameters += [[["Evaporator","Circuits_"+str(i),"FinTube_circuit_tube_OD"],["Evaporator","Circuits",i,"Geometry","OD"],"float"]]
            Parameters += [[["Evaporator","Circuits_"+str(i),"FinTube_circuit_tube_length"],["Evaporator","Circuits",i,"Geometry","Ltube"],"float"]]
            Parameters += [[["Evaporator","Circuits_"+str(i),"FinTube_circuit_tube_Pl"],["Evaporator","Circuits",i,"Geometry","Pl"],"float"]]
            Parameters += [[["Evaporator","Circuits_"+str(i),"FinTube_circuit_tube_Pt"],["Evaporator","Circuits",i,"Geometry","Pt"],"float"]]
            Parameters += [[["Evaporator","Circuits_"+str(i),"FinTube_circuit_fin_FPI"],["Evaporator","Circuits",i,"Geometry","FPI"],"float"]]
            Parameters += [[["Evaporator","Circuits_"+str(i),"FinTube_circuit_fin_t"],["Evaporator","Circuits",i,"Geometry","Fin_t"],"float"]]
            Parameters += [[["Evaporator","Circuits_"+str(i),"FinTube_circuit_tube_N_per_bank"],["Evaporator","Circuits",i,"Geometry","Ntubes_per_bank_per_subcircuit"],"int"]]
            Parameters += [[["Evaporator","Circuits_"+str(i),"FinTube_circuit_tube_N_bank"],["Evaporator","Circuits",i,"Geometry","Nbank"],"int"]]
            Parameters += [[["Evaporator","Circuits_"+str(i),"FinTube_circuit_N_circuits"],["Evaporator","Circuits",i,"Geometry","Nsubcircuits"],"int"]]
            if cycle.Evaporator.Circuits[i].Geometry.FinType in ["WavyLouvered","Wavy"]:
                Parameters += [[["Evaporator","Circuits_"+str(i),"FinTube_circuit_fin_dim_1"],["Evaporator","Circuits",i,"Geometry","Fin_xf"],"float"]]
                Parameters += [[["Evaporator","Circuits_"+str(i),"FinTube_circuit_fin_dim_2"],["Evaporator","Circuits",i,"Geometry","Fin_Pd"],"float"]]
            elif cycle.Evaporator.Circuits[i].Geometry.FinType == "Slit":
                Parameters += [[["Evaporator","Circuits_"+str(i),"FinTube_circuit_fin_dim_1"],["Evaporator","Circuits",i,"Geometry","Fin_Sh"],"float"]]
                Parameters += [[["Evaporator","Circuits_"+str(i),"FinTube_circuit_fin_dim_2"],["Evaporator","Circuits",i,"Geometry","Fin_Ss"],"float"]]
                Parameters += [[["Evaporator","Circuits_"+str(i),"FinTube_circuit_fin_dim_3"],["Evaporator","Circuits",i,"Geometry","Fin_Sn"],"int"]]
            elif cycle.Evaporator.Circuits[i].Geometry.FinType == "Louvered":
                Parameters += [[["Evaporator","Circuits_"+str(i),"FinTube_circuit_fin_dim_1"],["Evaporator","Circuits",i,"Geometry","Fin_Lp"],"float"]]
                Parameters += [[["Evaporator","Circuits_"+str(i),"FinTube_circuit_fin_dim_2"],["Evaporator","Circuits",i,"Geometry","Fin_Lh"],"float"]]

    elif cycle.Evaporator_Type == "MicroChannel":
        Parameters += [[["Condenser","Microchannel_air_flowrate"],["Evaporator","Vdot_ha"],"float"]]
        Parameters += [[["Evaporator","Geometry","Microchannel_tube_length"],["Evaporator","Geometry","T_L"],"float"]]
        Parameters += [[["Evaporator","Geometry","Microchannel_tube_spacing"],["Evaporator","Geometry","T_s"],"float"]]
        Parameters += [[["Evaporator","Geometry","Microchannel_tube_height"],["Evaporator","Geometry","T_h"],"float"]]
        Parameters += [[["Evaporator","Geometry","Microchannel_tube_width"],["Evaporator","Geometry","T_w"],"float"]]
        Parameters += [[["Evaporator","Geometry","Microchannel_fin_t"],["Evaporator","Geometry","Fin_t"],"float"]]
        Parameters += [[["Evaporator","Geometry","Microchannel_fin_FPI"],["Evaporator","Geometry","FPI"],"float"]]
        Parameters += [[["Evaporator","Geometry","Microchannel_fin_length"],["Evaporator","Geometry","Fin_L"],"float"]]
        if cycle.Evaporator.Geometry.FinType == "Louvered":
            Parameters += [[["Evaporator","Geometry","Microchannel_fin_dimension_1"],["Evaporator","Geometry","Fin_Llouv"],"float"]]
            Parameters += [[["Evaporator","Geometry","Microchannel_fin_dimension_2"],["Evaporator","Geometry","Fin_Lp"],"float"]]
            Parameters += [[["Evaporator","Geometry","Microchannel_fin_dimension_3"],["Evaporator","Geometry","Fin_alpha"],"float"]]

        Parameters += [[["Evaporator","Microchannel_N_bank"],["Evaporator","Geometry","N_tube_per_bank_per_pass"],"int"]]
        Parameters += [[["Evaporator","Microchannel_N_tube_per_bank"],["Evaporator","Geometry","N_tube_per_bank_per_pass"],"int"]]

    if cycle.Condenser_Type == "Fin-tube":
        Parameters += [[["Condenser","FinTube_air_flowrate"],["Condenser","Vdot_ha"],"float"]]
        for i in range(len(cycle.Condenser.Circuits)):
            Parameters += [[["Condenser","Circuits_"+str(i),"FinTube_circuit_tube_OD"],["Condenser","Circuits",i,"Geometry","OD"],"float"]]
            Parameters += [[["Condenser","Circuits_"+str(i),"FinTube_circuit_tube_length"],["Condenser","Circuits",i,"Geometry","Ltube"],"float"]]
            Parameters += [[["Condenser","Circuits_"+str(i),"FinTube_circuit_tube_Pl"],["Condenser","Circuits",i,"Geometry","Pl"],"float"]]
            Parameters += [[["Condenser","Circuits_"+str(i),"FinTube_circuit_tube_Pt"],["Condenser","Circuits",i,"Geometry","Pt"],"float"]]
            Parameters += [[["Condenser","Circuits_"+str(i),"FinTube_circuit_fin_FPI"],["Condenser","Circuits",i,"Geometry","FPI"],"float"]]
            Parameters += [[["Condenser","Circuits_"+str(i),"FinTube_circuit_fin_t"],["Condenser","Circuits",i,"Geometry","Fin_t"],"float"]]
            Parameters += [[["Condenser","Circuits_"+str(i),"FinTube_circuit_tube_N_per_bank"],["Condenser","Circuits",i,"Geometry","Ntubes_per_bank_per_subcircuit"],"int"]]
            Parameters += [[["Condenser","Circuits_"+str(i),"FinTube_circuit_tube_N_bank"],["Condenser","Circuits",i,"Geometry","Nbank"],"int"]]
            Parameters += [[["Condenser","Circuits_"+str(i),"FinTube_circuit_N_circuits"],["Condenser","Circuits",i,"Geometry","Nsubcircuits"],"int"]]
            if cycle.Condenser.Circuits[i].Geometry.FinType in ["WavyLouvered","Wavy"]:
                Parameters += [[["Condenser","Circuits_"+str(i),"FinTube_circuit_fin_dim_1"],["Condenser","Circuits",i,"Geometry","Fin_xf"],"float"]]
                Parameters += [[["Condenser","Circuits_"+str(i),"FinTube_circuit_fin_dim_2"],["Condenser","Circuits",i,"Geometry","Fin_Pd"],"float"]]
            elif cycle.Condenser.Circuits[i].Geometry.FinType == "Slit":
                Parameters += [[["Condenser","Circuits_"+str(i),"FinTube_circuit_fin_dim_1"],["Condenser","Circuits",i,"Geometry","Fin_Sh"],"float"]]
                Parameters += [[["Condenser","Circuits_"+str(i),"FinTube_circuit_fin_dim_2"],["Condenser","Circuits",i,"Geometry","Fin_Ss"],"float"]]
                Parameters += [[["Condenser","Circuits_"+str(i),"FinTube_circuit_fin_dim_3"],["Condenser","Circuits",i,"Geometry","Fin_Sn"],"int"]]
            elif cycle.Condenser.Circuits[i].Geometry.FinType == "Louvered":
                Parameters += [[["Condenser","Circuits_"+str(i),"FinTube_circuit_fin_dim_1"],["Condenser","Circuits",i,"Geometry","Fin_Lp"],"float"]]
                Parameters += [[["Condenser","Circuits_"+str(i),"FinTube_circuit_fin_dim_2"],["Condenser","Circuits",i,"Geometry","Fin_Lh"],"float"]]

    elif cycle.Condenser_Type == "MicroChannel":
        Parameters += [[["Condenser","Microchannel_air_flowrate"],["Condenser","Vdot_ha"],"float"]]
        Parameters += [[["Condenser","Geometry","Microchannel_tube_length"],["Condenser","Geometry","T_L"],"float"]]
        Parameters += [[["Condenser","Geometry","Microchannel_tube_spacing"],["Condenser","Geometry","T_s"],"float"]]
        Parameters += [[["Condenser","Geometry","Microchannel_tube_height"],["Condenser","Geometry","T_h"],"float"]]
        Parameters += [[["Condenser","Geometry","Microchannel_tube_width"],["Condenser","Geometry","T_w"],"float"]]
        Parameters += [[["Condenser","Geometry","Microchannel_fin_t"],["Condenser","Geometry","Fin_t"],"float"]]
        Parameters += [[["Condenser","Geometry","Microchannel_fin_FPI"],["Condenser","Geometry","FPI"],"float"]]
        Parameters += [[["Condenser","Geometry","Microchannel_fin_length"],["Condenser","Geometry","Fin_L"],"float"]]
        if cycle.Condenser.Geometry.FinType == "Louvered":
            Parameters += [[["Condenser","Geometry","Microchannel_fin_dimension_1"],["Condenser","Geometry","Fin_Llouv"],"float"]]
            Parameters += [[["Condenser","Geometry","Microchannel_fin_dimension_2"],["Condenser","Geometry","Fin_Lp"],"float"]]
            Parameters += [[["Condenser","Geometry","Microchannel_fin_dimension_3"],["Condenser","Geometry","Fin_alpha"],"float"]]

        Parameters += [[["Condenser","Microchannel_N_bank"],["Condenser","Geometry","N_tube_per_bank_per_pass"],"int"]]
        Parameters += [[["Condenser","Microchannel_N_tube_per_bank"],["Condenser","Geometry","N_tube_per_bank_per_pass"],"int"]]
    
    # checking every parameter
    for parameter in Parameters:
        if hasattr(cycle,"check_terminate"): #used to terminate run in GUI
            if cycle.check_terminate:
                return None
        parent_range = Ranges
        for i,hierarchy_i_range in enumerate(parameter[0]):
            if i != (len(parameter[0])-1): # this is not the last item
                if not hasattr(parent_range,hierarchy_i_range):
                    setattr(parent_range,hierarchy_i_range,values())
                parent_range = getattr(parent_range,hierarchy_i_range)
                        
            else: # this is the last item
                setattr(parent_range,hierarchy_i_range,[None,None,None])
                range_item = getattr(parent_range,hierarchy_i_range)
        
        parent_cycle = cycle
        for i,hierarchy_i_cycle in enumerate(parameter[1]):
            if i != (len(parameter[1])-1): # this is not the last item
                if not isinstance(hierarchy_i_cycle,int):
                    parent_cycle = getattr(parent_cycle,hierarchy_i_cycle)
                else:
                    parent_cycle = parent_cycle[hierarchy_i_cycle]
            else: # this is the last item
                value = getattr(parent_cycle,hierarchy_i_cycle)
        
        range_item[0] = value
        
        # getting maximum
        i = 1
        multiplier_array = np.array([1,1])
        multiplier = 8

        if hierarchy_i_range == "FinTube_circuit_tube_OD":
            ID = getattr(parent_cycle,"ID")

        if hierarchy_i_range == "Microchannel_tube_height":
            P_a = getattr(parent_cycle,"P_a")

        if hierarchy_i_range == "Microchannel_tube_width":
            N_port = getattr(parent_cycle,"N_port")
            Fin_L = getattr(parent_cycle,"Fin_L")
        
        while i <=5:
            if not hierarchy_i_range in ["Microchannel_N_bank","Microchannel_N_tube_per_bank"]:
                if parameter[2] == "int":
                    new_value = int(round(value * multiplier,0))
                elif parameter[2] == "float":
                    new_value = float(value * multiplier)

            elif hierarchy_i_range == "Microchannel_N_bank":
                multiplier = int(round(multiplier,0))
                new_value = value * multiplier

            elif hierarchy_i_range == "Microchannel_N_tube_per_bank":
                new_value = deepcopy(value)
                for j,bank in enumerate(new_value):
                    for k,bank_pass in enumerate(bank):
                        new_value[j][k] = int(round(bank_pass * multiplier,0))
                if getattr(parent_cycle,"Fin_rows") > sum(getattr(parent_cycle,"N_tube_per_bank_per_pass")[0]):
                    setattr(parent_cycle,"Fin_rows",sum(new_value[0])+1)
                elif getattr(parent_cycle,"Fin_rows") < sum(getattr(parent_cycle,"N_tube_per_bank_per_pass")[0]):
                    setattr(parent_cycle,"Fin_rows",sum(new_value[0])-1)
                if hasattr(parent_cycle,"N_tube_per_bank"):
                    delattr(parent_cycle,"N_tube_per_bank")
                
            setattr(parent_cycle,hierarchy_i_cycle,new_value)
            
            if hierarchy_i_range == "FinTube_circuit_tube_OD":
                setattr(parent_cycle,"ID",ID * multiplier)

            if hierarchy_i_range == "Microchannel_tube_height":
                setattr(parent_cycle,"P_a",P_a * multiplier)

            if hierarchy_i_range == "Microchannel_tube_width":
                setattr(parent_cycle,"N_port",int(N_port * multiplier))
                setattr(parent_cycle,"Fin_L",Fin_L * multiplier)

            result = solve_cycle_fast(cycle)
            
            multiplier_array = np.vstack([multiplier_array,[float(multiplier),result]])
            maximum_working = np.max(multiplier_array[multiplier_array[:,1] == 1,0])
            if len(multiplier_array[multiplier_array[:,1] == 0]) > 0:
                minimum_not_working = np.min(multiplier_array[multiplier_array[:,1] == 0,0])
            else:
                minimum_not_working = maximum_working * 3
            multiplier = (maximum_working + minimum_not_working) / 2
            if multiplier > 8:
                break
            i += 1
        
        best_multiplier = np.max(multiplier_array[multiplier_array[:,1] == 1,0])
        
        if not hierarchy_i_range in ["Microchannel_N_bank","Microchannel_N_tube_per_bank"]:
            if parameter[2] == "int":
                if best_multiplier == 1:
                    range_item[2] = None
                else:
                    range_item[2] = int(round(value * best_multiplier,0))
            elif parameter[2] == "float":
                if best_multiplier == 1:
                    range_item[2] = None
                else:
                    range_item[2] = float(value * best_multiplier)

        elif hierarchy_i_range == "Microchannel_N_bank":
            if best_multiplier == 1:
                range_item[2] = None
            else:
                range_item[2] = len(value) * best_multiplier

        elif hierarchy_i_range == "Microchannel_N_tube_per_bank":

            new_value = deepcopy(value)
            for j,bank in enumerate(new_value):
                for k,bank_pass in enumerate(bank):
                    new_value[j][k] = int(round(bank_pass * best_multiplier,0))
            if sum(new_value[0]) == sum(value[0]):
                range_item[2] == None
            else:
                range_item[2] = sum(new_value[0])

        # getting minimum
        i = 1
        multiplier_array = np.array([[1,1]])
        multiplier = 8
        while i <=5:
            if not hierarchy_i_range in ["Microchannel_N_bank","Microchannel_N_tube_per_bank"]:
                if parameter[2] == "int":
                    new_value = int(round(value / multiplier,0))
                elif parameter[2] == "float":
                    new_value = float(value / multiplier)
            
            elif hierarchy_i_range == "Microchannel_N_bank":
                N_banks = len(value)
                New_N_banks = int(round(N_banks / multiplier,0))
                if New_N_banks < 1:
                    i += 1
                    continue
                new_value = value[:New_N_banks]

            elif hierarchy_i_range == "Microchannel_N_tube_per_bank":
                new_value = deepcopy(value)
                for j,bank in enumerate(new_value):
                    for k,bank_pass in enumerate(bank):
                        new_value[j][k] = int(round(bank_pass / multiplier,0))
                        if new_value[j][k] < 1:
                            new_value[j][k] = 1
                if getattr(parent_cycle,"Fin_rows") > sum(getattr(parent_cycle,"N_tube_per_bank_per_pass")[0]):
                    setattr(parent_cycle,"Fin_rows",sum(new_value[0])+1)
                elif getattr(parent_cycle,"Fin_rows") < sum(getattr(parent_cycle,"N_tube_per_bank_per_pass")[0]):
                    setattr(parent_cycle,"Fin_rows",sum(new_value[0])-1)
                if hasattr(parent_cycle,"N_tube_per_bank"):
                    delattr(parent_cycle,"N_tube_per_bank")
                
            setattr(parent_cycle,hierarchy_i_cycle,new_value)

            if hierarchy_i_range == "FinTube_circuit_tube_OD":
                setattr(parent_cycle,"ID",ID / multiplier)

            if hierarchy_i_range == "Microchannel_tube_height":
                setattr(parent_cycle,"P_a",P_a / multiplier)

            if hierarchy_i_range == "Microchannel_tube_width":
                new_N_port = int(N_port / multiplier)
                if new_N_port < 1:
                    new_N_port = 1
                setattr(parent_cycle,"N_port",new_N_port)
                setattr(parent_cycle,"Fin_L",Fin_L / multiplier)

            result = solve_cycle_fast(cycle)
            
            multiplier_array = np.vstack([multiplier_array,[float(multiplier),result]])
            maximum_working = np.max(multiplier_array[multiplier_array[:,1] == 1,0])
            if len(multiplier_array[multiplier_array[:,1] == 0]) > 0:
                minimum_not_working = np.min(multiplier_array[multiplier_array[:,1] == 0,0])
            else:
                minimum_not_working = maximum_working * 3
            multiplier = (maximum_working + minimum_not_working) / 2

            if multiplier > 8:
                break
            
            i += 1
            
        best_multiplier = np.max(multiplier_array[multiplier_array[:,1] == 1,0])

        if not hierarchy_i_range in ["Microchannel_N_bank","Microchannel_N_tube_per_bank"]:
            if parameter[2] == "int":
                if best_multiplier == 1:
                    range_item[1] = None
                else:
                    range_item[1] = int(round(value / best_multiplier,0))
            elif parameter[2] == "float":
                if best_multiplier == 1:
                    range_item[1] = None
                else:
                    range_item[1] = float(value / best_multiplier)

        elif hierarchy_i_range == "Microchannel_N_bank":
            if best_multiplier == 1:
                range_item[1] = None
            else:
                range_item[1] = len(value) * best_multiplier
            range_item[0] = len(value)
        
        elif hierarchy_i_range == "Microchannel_N_tube_per_bank":
            new_value = deepcopy(value)
            for j,bank in enumerate(new_value):
                for k,bank_pass in enumerate(bank):
                    new_value[j][k] = int(round(bank_pass / best_multiplier,0))
            if sum(new_value[0]) == sum(value[0]):
                range_item[1] == None
            else:
                range_item[1] = sum(new_value[0])
            range_item[0] = sum(value[0])

        # return cycle to original
        setattr(parent_cycle,hierarchy_i_cycle,value)

        if hierarchy_i_range == "FinTube_circuit_tube_OD":
            setattr(parent_cycle,"ID",ID)

        if hierarchy_i_range == "Microchannel_tube_height":
            setattr(parent_cycle,"P_a",P_a)

        if hierarchy_i_range == "Microchannel_tube_width":
            setattr(parent_cycle,"N_port",N_port)
            setattr(parent_cycle,"Fin_L",Fin_L)
        
    if cycle.Evaporator_Type == "Fin-tube":
        minimum_flowrate = Ranges.Evaporator.FinTube_air_flowrate[1]
        maximum_flowrate = Ranges.Evaporator.FinTube_air_flowrate[2]
        mass_flowrate_name = "FinTube_air_mass_flowrate"
    elif cycle.Evaporator_Type == "MicroChannel":
        minimum_flowrate = Ranges.Evaporator.Microchannel_air_flowrate[1]
        maximum_flowrate = Ranges.Evaporator.Microchannel_air_flowrate[2]
        mass_flowrate_name = "Microchannel_air_mass_flowrate"
    v_spec = HAPropsSI("V","T",cycle.Evaporator.Tin_a,"W",cycle.Evaporator.Win_a,"P",cycle.Evaporator.Pin_a)
    if minimum_flowrate != None:
        minimum = minimum_flowrate/v_spec
    else:
        minimum = None
    if maximum_flowrate != None:
        maximum = maximum_flowrate/v_spec
    else:
        maximum = None
    setattr(Ranges.Evaporator,mass_flowrate_name,[cycle.Evaporator.Vdot_ha/v_spec,minimum,maximum])

    if cycle.Condenser_Type == "Fin-tube":
        minimum_flowrate = Ranges.Condenser.FinTube_air_flowrate[1]
        maximum_flowrate = Ranges.Condenser.FinTube_air_flowrate[2]
        mass_flowrate_name = "FinTube_air_mass_flowrate"
    elif cycle.Condenser_Type == "MicroChannel":
        minimum_flowrate = Ranges.Condenser.Microchannel_air_flowrate[1]
        maximum_flowrate = Ranges.Condenser.Microchannel_air_flowrate[2]
        mass_flowrate_name = "Microchannel_air_mass_flowrate"
    v_spec = HAPropsSI("V","T",cycle.Condenser.Tin_a,"W",cycle.Condenser.Win_a,"P",cycle.Condenser.Pin_a)
    if minimum_flowrate != None:
        minimum = minimum_flowrate/v_spec
    else:
        minimum = None
    if maximum_flowrate != None:
        maximum = maximum_flowrate/v_spec
    else:
        maximum = None
    setattr(Ranges.Condenser,mass_flowrate_name,[cycle.Condenser.Vdot_ha/v_spec,minimum,maximum])
    
    return Ranges
    
def solve_cycle_fast(cycle):
    Cycle_Fast = CycleFastClass()
    
    # defining cycle parameters
    
    # Cycle Parameters
    Cycle_Fast.Compressor_Type = cycle.Compressor_Type
    
    Cycle_Fast.Condenser_Type = cycle.Condenser_Type
    Cycle_Fast.Evaporator_Type = cycle.Evaporator_Type
    
    Cycle_Fast.Second_Cond = cycle.Second_Cond
    
    if Cycle_Fast.Second_Cond == "Subcooling":
        Cycle_Fast.SC_value = cycle.SC_value
        
    elif Cycle_Fast.Second_Cond == "Charge":
        Cycle_Fast.Charge_value = cycle.Charge_value

    Cycle_Fast.Expansion_Device_Type = 'TXV'
    Cycle_Fast.SH_value = cycle.SH_value
    Cycle_Fast.Superheat_Type = 'Evaporator'

    Cycle_Fast.Backend = "HEOS"
    Cycle_Fast.Ref = cycle.Ref
    
    Cycle_Fast.Mode = cycle.Mode
    Cycle_Fast.Tevap_init_manual = False
    Cycle_Fast.Tcond_init_manual = False
    Cycle_Fast.energy_tol = 100
    Cycle_Fast.pressure_tol = 1000
    Cycle_Fast.mass_flowrate_tol = 0.001
    Cycle_Fast.mass_tol = 0.01
    Cycle_Fast.max_n_iterations = 20
    Cycle_Fast.Update()
    
    Cycle_Fast.Native_HX_files = False
    
    # defining condenser
    Cycle_Fast.Condenser_fast.HX = cycle.Condenser
    if cycle.Condenser_Type == "Fin-tube":
        for circuit in cycle.Condenser.Circuits:
            try:
                circuit.check_input()
            except:
                return 0
    elif cycle.Condenser_Type == "MicroChannel":
        try:
            cycle.Condenser.check_input()
        except:
            import traceback
            print(traceback.format_exc())
            return 0
    
    # defining evaporator
    Cycle_Fast.Evaporator_fast.HX = cycle.Evaporator
    if cycle.Evaporator_Type == "Fin-tube":
        for circuit in cycle.Evaporator.Circuits:
            try:
                circuit.check_input()
            except:
                return 0
    elif cycle.Evaporator_Type == "MicroChannel":
        try:
            cycle.Evaporator.check_input()
        except:
            return 0
    
    # defining Liquid line
    Cycle_Fast.Line_Liquid = cycle.Line_Liquid
    Cycle_Fast.Line_Liquid.Nsegments = 1
    
    # defining 2phase line
    Cycle_Fast.Line_2phase = cycle.Line_2phase
    Cycle_Fast.Line_2phase.Nsegments = 1

    # defining Suction line
    Cycle_Fast.Line_Suction = cycle.Line_Suction
    Cycle_Fast.Line_Suction.Nsegments = 1

    # defining Discharge line
    Cycle_Fast.Line_Discharge = cycle.Line_Discharge
    Cycle_Fast.Line_Discharge.Nsegments = 1
    
    # defining AHRI Compressor
    Cycle_Fast.Compressor = cycle.Compressor
        
    Cycle_Fast.REFPROP_path = ""
    result = Cycle_Fast.Calculate('Newton')
    if not result[0]:
        Cycle_Fast.Error_message = result[1]
    return result[0]
    
if __name__ == '__main__':
    global Cycle
    global ranges
    from CoolProp.CoolProp import HAPropsSI
    Cycle = CycleClass()
    
    # defining cycle parameters
    Cycle.Compressor_Type = 'AHRI'
    # Cycle.Compressor_Type = 'Physics'
    
    Cycle.Condenser_Type = 'MicroChannel'
    Cycle.Evaporator_Type = 'Fin-tube'
    
    Cycle.Second_Cond = "Subcooling"
    Cycle.SC_value = 7

    # Cycle.Second_Cond = "Charge"
    # Cycle.Charge_value = 31

    Cycle.Expansion_Device_Type = 'TXV'
    Cycle.SH_value = 5
    Cycle.Superheat_Type = 'Evaporator'
    # Cycle.Superheat_Type = 'Compressor'

    # Cycle.Expansion_Device_Type = 'Capillary'

    Cycle.Backend = "HEOS"
    Cycle.Ref = "R410A"
    Cycle.Mode = "AC"
    Cycle.Tevap_init_manual = False
    Cycle.Tcond_init_manual = False
    Cycle.energy_tol = 1
    Cycle.pressure_tol = 10
    Cycle.mass_flowrate_tol = 0.001
    Cycle.mass_tol = 0.01
    Cycle.max_n_iterations = 40
    Cycle.Update()
    
    # defining condenser
    Cycle.Condenser.model = 'phase' # either 'phase' or 'segment'
    # each major array element represent a bank, each element in minor array reperesent number of tubes per pass (number of elements in minor array is the number of passes)
    Cycle.Condenser.Geometry.N_tube_per_bank_per_pass = [[22,14,8,6]]
    Cycle.Condenser.Geometry.Fin_rows = 51 # it can be more or less than number of tubes per bank by 1
    Cycle.Condenser.Geometry.T_L = 0.745 # tube length
    Cycle.Condenser.Geometry.T_w = 0.016 # tube width
    Cycle.Condenser.Geometry.T_h = 0.0018 # tube height
    Cycle.Condenser.Geometry.T_s = 0.008 # tube spacing (fin height)
    Cycle.Condenser.Geometry.P_shape = 'Rectangle' # port shape 'Rectangle' or 'Circle' or 'Triangle'
    Cycle.Condenser.Geometry.P_end = 'Extended' # ports 'Extended' to the far ends by circular ends or not 'Normal'
    Cycle.Condenser.Geometry.P_a = 0.0012 # port major dimension
    Cycle.Condenser.Geometry.P_b = 0.0007 # port minor dimension (optional)
    Cycle.Condenser.Geometry.N_port = 16 # number of ports per tube
    Cycle.Condenser.Geometry.Enhanced = False # internal fins in ports
    Cycle.Condenser.Geometry.FinType = 'Louvered' # fin type
    Cycle.Condenser.Geometry.Fin_t = 0.00008 # fin thickness
    Cycle.Condenser.Geometry.Fin_L = 0.016 # fin length
    Cycle.Condenser.Geometry.Fin_Llouv = 0.0068 # height of fin louver
    Cycle.Condenser.Geometry.Fin_alpha = 24 # angle of louver
    Cycle.Condenser.Geometry.FPI = 19 # fins per inch
    Cycle.Condenser.Geometry.Fin_Lp = 0.001 # louver pitch
    Cycle.Condenser.Geometry.e_D = 0.0 # tube internal roughness
    Cycle.Condenser.Geometry.Header_CS_Type = 'Rectangle' # header cross section 'Rectangle' or 'Circle'
    Cycle.Condenser.Geometry.Header_dim_a = 0.02 # header major dimension
    Cycle.Condenser.Geometry.Header_dim_b = 0.02 # header minor dimension
    Cycle.Condenser.Geometry.Header_length = 0.55 # header total height
    
    Cycle.Condenser.Pin_a = 101325 # inlet air pressure
    Cycle.Condenser.Thermal.Nsegments = 1 # number of segments per tube
    Cycle.Condenser.Thermal.kw = 205 # tube wall conductivity
    Cycle.Condenser.Thermal.h_r_superheat_tuning = 1.0 # tuning factor for refrigerant superheat HTC
    Cycle.Condenser.Thermal.h_r_subcooling_tuning = 1.0 # tuning factor for refrigerant subcool HTC
    Cycle.Condenser.Thermal.h_r_2phase_tuning = 1.0 # tuning factor for refrigerant 2phase HTC
    Cycle.Condenser.Thermal.h_a_dry_tuning = 1.0 # tuning factor for air dry HTC
    Cycle.Condenser.Thermal.h_a_wet_tuning = 1.0 # tuning factor for air wet HTC
    Cycle.Condenser.Thermal.DP_r_superheat_tuning = 1.0 # tuning factor for refrigerant superheat pressure drop
    Cycle.Condenser.Thermal.DP_r_subcooling_tuning = 1.0 # tuning factor for refrigerant subcool pressure drop
    Cycle.Condenser.Thermal.DP_r_2phase_tuning = 1.0 # tuning factor for refrigerant 2phase pressure drop
    Cycle.Condenser.Thermal.DP_a_tuning = 1.0 # tuning factor for air pressure drop
    Cycle.Condenser.Thermal.k_fin = 205 # fin thermal conductivity
    Cycle.Condenser.Thermal.FinsOnce = True # calculate fins only once or per each segment
    Cycle.Condenser.Thermal.Headers_DP_r = 1000 # total header pressure drop in Pa
    Cycle.Condenser.Thermal.h_a_wet_on = False # don't use wet air pressure drop correlation
    Cycle.Condenser.Thermal.DP_a_wet_on = False # don't use wet air pressure drop correlation
    Cycle.Condenser.Accurate = True # use CoolProp (True) or psychrolib (False)
    Cycle.Condenser.Vdot_ha = 33.5/60 # air humid mass flow rate


    Cycle.Condenser.Fan.model = 'efficiency'
    Cycle.Condenser.Fan.efficiency = '0.4'

    Cycle.Condenser.Fan.Fan_position = 'after' # relative to HX

    Cycle.Condenser.Tin_a = 35+273.15
    Win_a = HAPropsSI('W','P',Cycle.Condenser.Pin_a,'T',Cycle.Condenser.Tin_a,'R',0.5)
    Cycle.Condenser.Win_a = Win_a
            
    # defining evaporator
    Cycle.Evaporator.model = 'phase'
    Cycle.Evaporator.create_circuits(1)
    Cycle.Evaporator.Accurate = True
    Cycle.Evaporator.connect(0,1,0,1.0,2)
    Cycle.Evaporator.Q_error_tol = 0.01
    Cycle.Evaporator.max_iter_per_circuit = 30
    Cycle.Evaporator.Ref_Pressure_error_tol = 100        
    Cycle.Evaporator.Pin_a = 101325
    Cycle.Evaporator.Tin_a = 27 + 273.15
    RHin_a = 0.5
    Win_a = HAPropsSI("W","T",Cycle.Evaporator.Tin_a,"P",Cycle.Evaporator.Pin_a,"R",RHin_a)
    Cycle.Evaporator.Win_a = Win_a
    Cycle.Evaporator.Vdot_ha = 10.3/60

    Cycle.Evaporator.Circuits[0].Geometry.Ntubes_per_bank_per_subcircuit=6       #number of tubes per bank per circuit
    Cycle.Evaporator.Circuits[0].Geometry.Nbank=2                             #number of banks or rows
    Cycle.Evaporator.Circuits[0].Geometry.OD = 0.007
    Cycle.Evaporator.Circuits[0].Geometry.ID = 0.0065
    Cycle.Evaporator.Circuits[0].Geometry.Staggering = 'aAa'
    Cycle.Evaporator.Circuits[0].Geometry.Tubes_type='Smooth'
    Cycle.Evaporator.Circuits[0].Geometry.Pl = 0.0127               #distance between center of tubes in flow direction                                                
    Cycle.Evaporator.Circuits[0].Geometry.Pt = 0.021                #distance between center of tubes orthogonal to flow direction

    connections = []
    for k in reversed(range(int(Cycle.Evaporator.Circuits[0].Geometry.Nbank))):
        start = k * Cycle.Evaporator.Circuits[0].Geometry.Ntubes_per_bank_per_subcircuit + 1
        end = (k + 1) * Cycle.Evaporator.Circuits[0].Geometry.Ntubes_per_bank_per_subcircuit + 1
        if (Cycle.Evaporator.Circuits[0].Geometry.Nbank - k)%2==1:
            connections += range(start,end)
        else:
            connections += reversed(range(start,end))

    Cycle.Evaporator.Circuits[0].Geometry.Connections = connections
    Cycle.Evaporator.Circuits[0].Geometry.FarBendRadius = 0.01
    Cycle.Evaporator.Circuits[0].Geometry.e_D = 0
    Cycle.Evaporator.Circuits[0].Geometry.Ltube=0.68         #one tube length
    Cycle.Evaporator.Circuits[0].Geometry.FPI = 18
    Cycle.Evaporator.Circuits[0].Geometry.FinType = 'WavyLouvered'
    Cycle.Evaporator.Circuits[0].Geometry.Fin_t = 0.00011
    Cycle.Evaporator.Circuits[0].Geometry.Fin_xf = 0.001
    Cycle.Evaporator.Circuits[0].Geometry.Fin_Pd = 0.001
    Cycle.Evaporator.Circuits[0].Geometry.Nsubcircuits = 5
    
    Cycle.Evaporator.Circuits[0].Thermal.Nsegments = 10
    Cycle.Evaporator.Circuits[0].Thermal.kw = 237
    Cycle.Evaporator.Circuits[0].Thermal.k_fin = 237
    Cycle.Evaporator.Circuits[0].Thermal.FinsOnce = False
    Cycle.Evaporator.Circuits[0].Thermal.HTC_superheat_Corr = 0
    Cycle.Evaporator.Circuits[0].Thermal.HTC_subcool_Corr = 0
    Cycle.Evaporator.Circuits[0].Thermal.DP_superheat_Corr = 0
    Cycle.Evaporator.Circuits[0].Thermal.DP_subcool_Corr = 0
    Cycle.Evaporator.Circuits[0].Thermal.HTC_2phase_Corr = 0
    Cycle.Evaporator.Circuits[0].Thermal.DP_2phase_Corr = 0
    Cycle.Evaporator.Circuits[0].Thermal.DP_Accel_Corr = 2
    Cycle.Evaporator.Circuits[0].Thermal.rho_2phase_Corr = 2
    Cycle.Evaporator.Circuits[0].Thermal.Air_dry_Corr = 0
    Cycle.Evaporator.Circuits[0].Thermal.Air_wet_Corr = 0
    Cycle.Evaporator.Circuits[0].Thermal.h_r_superheat_tuning = 1.0
    Cycle.Evaporator.Circuits[0].Thermal.h_r_subcooling_tuning = 1.0
    Cycle.Evaporator.Circuits[0].Thermal.h_r_2phase_tuning = 1.0
    Cycle.Evaporator.Circuits[0].Thermal.h_a_dry_tuning = 1.0
    Cycle.Evaporator.Circuits[0].Thermal.h_a_wet_tuning = 1.0
    Cycle.Evaporator.Circuits[0].Thermal.DP_r_superheat_tuning = 1.0
    Cycle.Evaporator.Circuits[0].Thermal.DP_r_subcooling_tuning = 1.0
    Cycle.Evaporator.Circuits[0].Thermal.DP_r_2phase_tuning = 1.0
    Cycle.Evaporator.Circuits[0].Thermal.DP_a_tuning = 1.0
    Cycle.Evaporator.Circuits[0].Thermal.h_a_wet_on = False
    Cycle.Evaporator.Circuits[0].Thermal.DP_a_wet_on = False
    Cycle.Evaporator.Fan.model = 'efficiency'
    Cycle.Evaporator.Fan.efficiency = '0.5'
    Cycle.Evaporator.Fan.Fan_position = 'after'
    Cycle.Evaporator.Air_sequence = 'series_counter'
    Cycle.Evaporator.Solver = 'mdot'
    
    # defining Liquid line
    Cycle.Line_Liquid.L = 5
    Cycle.Line_Liquid.ID = 0.019
    Cycle.Line_Liquid.OD = 0.022
    Cycle.Line_Liquid.k_line = 385
    Cycle.Line_Liquid.k_ins = 0.036
    Cycle.Line_Liquid.t_ins = 0.01
    Cycle.Line_Liquid.T_sur = 40 + 273.15
    Cycle.Line_Liquid.h_sur = 20
    Cycle.Line_Liquid.e_D = 0.00001
    Cycle.Line_Liquid.Nsegments = 20
    Cycle.Line_Liquid.Q_error_tol = 0.01
    Cycle.Line_Liquid.DP_tuning = 0.0
    Cycle.Line_Liquid.HT_tuning = 0.0

    # defining 2phase line
    Cycle.Line_2phase.L = 5
    Cycle.Line_2phase.ID = 0.019
    Cycle.Line_2phase.OD = 0.022
    Cycle.Line_2phase.k_line = 385
    Cycle.Line_2phase.k_ins = 0.036
    Cycle.Line_2phase.t_ins = 0.01
    Cycle.Line_2phase.T_sur = 40 + 273.15
    Cycle.Line_2phase.h_sur = 20
    Cycle.Line_2phase.e_D = 0.00001
    Cycle.Line_2phase.Nsegments = 20
    Cycle.Line_2phase.Q_error_tol = 0.01
    Cycle.Line_2phase.DP_tuning = 0.0
    Cycle.Line_2phase.HT_tuning = 0.0

    # defining Suction line
    Cycle.Line_Suction.L = 5
    Cycle.Line_Suction.ID = 0.012
    Cycle.Line_Suction.OD = 0.014
    Cycle.Line_Suction.k_line = 385
    Cycle.Line_Suction.k_ins = 0.036
    Cycle.Line_Suction.t_ins = 0.01
    Cycle.Line_Suction.T_sur = 40 + 273.15
    Cycle.Line_Suction.h_sur = 20
    Cycle.Line_Suction.e_D = 0.00001
    Cycle.Line_Suction.Nsegments = 20
    Cycle.Line_Suction.Q_error_tol = 0.01
    Cycle.Line_Suction.DP_tuning = 0.0
    Cycle.Line_Suction.HT_tuning = 0.0

    # defining Discharge line
    Cycle.Line_Discharge.L = 5
    Cycle.Line_Discharge.ID = 0.019
    Cycle.Line_Discharge.OD = 0.022
    Cycle.Line_Discharge.k_line = 385
    Cycle.Line_Discharge.k_ins = 0.036
    Cycle.Line_Discharge.t_ins = 0
    Cycle.Line_Discharge.T_sur = 40 + 273.15
    Cycle.Line_Discharge.h_sur = 20
    Cycle.Line_Discharge.e_D = 0.00001
    Cycle.Line_Discharge.Nsegments = 20
    Cycle.Line_Discharge.Q_error_tol = 0.01
    Cycle.Line_Discharge.DP_tuning = 0.0
    Cycle.Line_Discharge.HT_tuning = 0.0
    
    # defining AHRI Compressor
    if Cycle.Compressor_Type == 'AHRI':
        Cycle.Compressor.M = [(158.38079	,4.72993	,1.23499	,0.04045298	,-0.0057017	,-0.0097998	,0.000126	,-6.36e-06	,2.67e-05	,7.51e-06)]
        Cycle.Compressor.P = [(-576.86169	,-2.19523	,46.01597	,0.022031	,-0.0053035	,-0.3578	,0.000917	,-0.0010689	,0.000149	,0.0017934)]
        Cycle.Compressor.Speeds = [2500]
        Cycle.Compressor.fp = 0.0
        Cycle.Compressor.Vdot_ratio_P = 1.0
        Cycle.Compressor.Vdot_ratio_M = 1.0
        Cycle.Compressor.Displacement = 0.001
        Cycle.Compressor.SH_Ref = 20 * 5 / 9
        Cycle.Compressor.act_speed = 2500
        Cycle.Compressor.Unit_system = 'ip'
        Cycle.Compressor.Elec_eff = 1.0
        Cycle.Compressor.F_factor = 0.75
    

    # defining Physics-based compressor
    elif Cycle.Compressor_Type == 'Physics':
        Cycle.Compressor.fp = 0.0
        Cycle.Compressor.Vdot_ratio_P = 1.0
        Cycle.Compressor.Vdot_ratio_M = 1.0
        Cycle.Compressor.Displacement = 0.001
        Cycle.Compressor.act_speed = 2500
        Cycle.Compressor.Elec_eff = 1.0
        Cycle.Compressor.isen_eff = "0.6"
        Cycle.Compressor.vol_eff = "0.45"
        
    if Cycle.Expansion_Device_Type == 'Capillary':
        Cycle.Capillary.L = 4.0        
        Cycle.Capillary.D = 0.0009
        Cycle.Capillary.D_liquid = Cycle.Line_Liquid.ID
        Cycle.Capillary.Ntubes = 5
        Cycle.Capillary.DT_2phase = 0.5
        Cycle.Capillary.DP_converged = 1
    
    Cycle.REFPROP_path = ""
    Cycle.Create_ranges = True
    import time
    T1 = time.time()
    result = Cycle.Calculate('Newton')
    if not result[0]:
        Cycle.Error_message = result[1]
        print(Cycle.Solver_Error)
    print(result)
    print('Calculation time:',round(time.time() - T1,3),'s')
