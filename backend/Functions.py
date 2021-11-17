import pandas as pd
import numpy as np
import CoolProp as CP
import appdirs
from GUI_functions import load_refrigerant_list

class ValuesClass():
    pass

def get_2phase_HTC_ranges():
    database_path = appdirs.user_data_dir("EGSim")+"/2phase_HTC.csv"
    values = pd.read_csv(database_path,index_col=0)
        
    values = values.dropna()
    ranges = ValuesClass()
    
    ranges.id_uniq = list(set(values["id"]))

    ranges.id = list(values["id"])

    ranges.deviation = np.array(values["deviation"])
    
    ranges.K_f = np.array([[values["id"].iloc[i],min(values["K_f_min"].iloc[i],values["K_f_max"].iloc[i]),min(values["K_f_min"].iloc[i],values["K_f_max"].iloc[i]),max(values["K_f_min"].iloc[i],values["K_f_max"].iloc[i]),max(values["K_f_min"].iloc[i],values["K_f_max"].iloc[i])] for i in range(len(values))])
    ranges.K_f[:,1] *= 0.75
    ranges.K_f[:,4] *= 1.25

    ranges.K_g = np.array([[values["id"].iloc[i],min(values["K_g_min"].iloc[i],values["K_g_max"].iloc[i]),min(values["K_g_min"].iloc[i],values["K_g_max"].iloc[i]),max(values["K_g_min"].iloc[i],values["K_g_max"].iloc[i]),max(values["K_g_min"].iloc[i],values["K_g_max"].iloc[i])] for i in range(len(values))])
    ranges.K_g[:,1] *= 0.75
    ranges.K_g[:,4] *= 1.25

    ranges.mu_f = np.array([[values["id"].iloc[i],min(values["mu_f_min"].iloc[i],values["mu_f_max"].iloc[i]),min(values["mu_f_min"].iloc[i],values["mu_f_max"].iloc[i]),max(values["mu_f_min"].iloc[i],values["mu_f_max"].iloc[i]),max(values["mu_f_min"].iloc[i],values["mu_f_max"].iloc[i])] for i in range(len(values))])
    ranges.mu_f[:,1] *= (0.75)
    ranges.mu_f[:,4] *= (1.25)

    ranges.mu_g = np.array([[values["id"].iloc[i],min(values["mu_g_min"].iloc[i],values["mu_g_max"].iloc[i]),min(values["mu_g_min"].iloc[i],values["mu_g_max"].iloc[i]),max(values["mu_g_min"].iloc[i],values["mu_g_max"].iloc[i]),max(values["mu_g_min"].iloc[i],values["mu_g_max"].iloc[i])] for i in range(len(values))])
    ranges.mu_g[:,1] *= 0.75
    ranges.mu_g[:,4] *= 1.25

    ranges.Sur_ten_f = np.array([[values["id"].iloc[i],min(values["Sur_ten_f_min"].iloc[i],values["Sur_ten_f_max"].iloc[i]),min(values["Sur_ten_f_min"].iloc[i],values["Sur_ten_f_max"].iloc[i]),max(values["Sur_ten_f_min"].iloc[i],values["Sur_ten_f_max"].iloc[i]),max(values["Sur_ten_f_min"].iloc[i],values["Sur_ten_f_max"].iloc[i])] for i in range(len(values))])
    ranges.Sur_ten_f[:,1] *= 0.75
    ranges.Sur_ten_f[:,4] *= 1.25

    ranges.Pr_f = np.array([[values["id"].iloc[i],min(values["Pr_f_min"].iloc[i],values["Pr_f_max"].iloc[i]),min(values["Pr_f_min"].iloc[i],values["Pr_f_max"].iloc[i]),max(values["Pr_f_min"].iloc[i],values["Pr_f_max"].iloc[i]),max(values["Pr_f_min"].iloc[i],values["Pr_f_max"].iloc[i])] for i in range(len(values))])
    ranges.Pr_f[:,1] *= 0.75
    ranges.Pr_f[:,4] *= 1.25

    ranges.Pr_g = np.array([[values["id"].iloc[i],min(values["Pr_g_min"].iloc[i],values["Pr_g_max"].iloc[i]),min(values["Pr_g_min"].iloc[i],values["Pr_g_max"].iloc[i]),max(values["Pr_g_min"].iloc[i],values["Pr_g_max"].iloc[i]),max(values["Pr_g_min"].iloc[i],values["Pr_g_max"].iloc[i])] for i in range(len(values))])
    ranges.Pr_g[:,1] *= 0.75
    ranges.Pr_g[:,4] *= 1.25

    ranges.rho_f = np.array([[values["id"].iloc[i],min(values["rho_f_min"].iloc[i],values["rho_f_max"].iloc[i]),min(values["rho_f_min"].iloc[i],values["rho_f_max"].iloc[i]),max(values["rho_f_min"].iloc[i],values["rho_f_max"].iloc[i]),max(values["rho_f_min"].iloc[i],values["rho_f_max"].iloc[i])] for i in range(len(values))],dtype=float)
    ranges.rho_f[:,1] *= 0.75
    ranges.rho_f[:,4] *= 1.25

    ranges.rho_g = np.array([[values["id"].iloc[i],min(values["rho_g_min"].iloc[i],values["rho_g_max"].iloc[i]),min(values["rho_g_min"].iloc[i],values["rho_g_max"].iloc[i]),max(values["rho_g_min"].iloc[i],values["rho_g_max"].iloc[i]),max(values["rho_g_min"].iloc[i],values["rho_g_max"].iloc[i])] for i in range(len(values))],dtype=float)
    ranges.rho_g[:,1] *= 0.75
    ranges.rho_g[:,4] *= 1.25

    ranges.G = np.array([[values["id"].iloc[i],min(values["G_min"].iloc[i],values["G_max"].iloc[i]),min(values["G_min"].iloc[i],values["G_max"].iloc[i]),max(values["G_min"].iloc[i],values["G_max"].iloc[i]),max(values["G_min"].iloc[i],values["G_max"].iloc[i])] for i in range(len(values))])
    ranges.G[:,1] *= 0.5
    ranges.G[:,4] *= 1.5

    ranges.D = np.array([[values["id"].iloc[i],min(values["D_min"].iloc[i],values["D_max"].iloc[i]),min(values["D_min"].iloc[i],values["D_max"].iloc[i]),max(values["D_min"].iloc[i],values["D_max"].iloc[i]),max(values["D_min"].iloc[i],values["D_max"].iloc[i])] for i in range(len(values))])
    ranges.D[:,1] *= 0.75
    ranges.D[:,4] *= 1.5

    ranges.Pr = np.array([[values["id"].iloc[i],min(values["Pr_min"].iloc[i],values["Pr_g_max"].iloc[i]),min(values["Pr_min"].iloc[i],values["Pr_max"].iloc[i]),max(values["Pr_min"].iloc[i],values["Pr_max"].iloc[i]),max(values["Pr_min"].iloc[i],values["Pr_max"].iloc[i])] for i in range(len(values))])
    ranges.Pr[:,1] *= 0.5
    ranges.Pr[:,4] *= 1.5
    
    ranges.Tube_type = np.array([[values["id"].iloc[i],values["tube_type"].iloc[i]] for i in range(len(values))])

    ranges.Mode = np.array([[values["id"].iloc[i],values["mode"].iloc[i]] for i in range(len(values))])
    
    return ranges

def get_2phase_HTC_corr(P,G,D,Tube_type,Mode,AS,ranges):    
    values = ValuesClass()
    
    # assign mass flux
    values.G = G
    values.D = D * 1000
    
    # get physical properties at the pressure given
    AS.update(CP.PQ_INPUTS,P,1)
    values.K_g = AS.conductivity()  * 1e3  # [mW/m-K]
    values.mu_g = AS.viscosity()  * 1e6  # [uPa-s]
    cp_g = AS.cpmass()  # [J/kg-K]
    values.rho_g = AS.rhomass()  # [J/kg-K]
    values.Pr_g = cp_g * values.mu_g / values.K_g / 1e3  # [-]
    
    AS.update(CP.PQ_INPUTS,P,0)
    values.K_f = AS.conductivity() * 1e3  # [mW/m-K]
    values.mu_f = AS.viscosity() * 1e6  # [uPa-s]
    cp_f = AS.cpmass()  # [J/kg-K]
    values.rho_f = AS.rhomass()  # [J/kg-K]
    values.Pr_f = cp_f * values.mu_f / values.K_f / 1e3  # [-]
    values.Sur_ten_f = AS.surface_tension() * 1e3 # [mN/m]

    # check for these values against ranges
    props = ["K_g","mu_g","Pr_g","K_f","mu_f","Pr_f","Sur_ten_f","G","rho_f","rho_g","D"]
    
    # give relative weights for each property
    weights = [1 for i in range(len(props))]
    
    # first, we need to filter the correlations for the tube type and mode (evaporation or condensation)
    corr = list(range(len(ranges.id)))
    corr_to_remove = []
    for i,corr_i in enumerate(corr):
        if ranges.Mode[corr_i,1] != Mode:
            corr_to_remove.append(corr_i)
    for i in corr_to_remove: corr.remove(i)
    corr_to_remove = []
    for i,corr_i in enumerate(corr):
        if ranges.Tube_type[corr_i,1] != Tube_type:
            corr_to_remove.append(corr_i)
    for i in corr_to_remove: corr.remove(i)
    
    # create scores array
    scores = np.zeros([len(corr),2])
    scores[:,0] = corr

    # for each element in props, we will give a score
    for j,element in enumerate(props):
        ranges_i = getattr(ranges,element).copy()
        ranges_i = ranges_i[corr]
        for i,row in enumerate(ranges_i):
            x = [row[1],row[2],row[3],row[4]]
            y = [0,1,1,0]
            value = getattr(values,element)
            score = np.interp(value,x,y)
            scores[i,1] += score * weights[j]

    if any(scores[:,1]):
        maximum_score = np.max(scores[:,1])
        scores = scores[scores[:,1] > 0.95 * maximum_score]
        deviations = 1 - ranges.deviation[[int(i) for i in scores[:,0]]]
        for m,deviation in enumerate(deviations):
            if deviation == 1:
                deviations[m] = 0.9
        deviations /= np.max(deviations)
        scores[:,1] *= deviations
        maximum_corr = int(scores[np.argmax(scores[:,1])][0])
        selected_corr = ranges.id[maximum_corr]
    else:
        if Tube_type == 1: # Smooth
            if Mode == 1:# evaporation
                selected_corr = 2 # shah evaporation
            elif Mode == 2: # condensation
                selected_corr = 1 # shah condensation
        elif Tube_type == 2: # microfin
            if Mode == 1: # evaporation
                selected_corr = 10 # wu evaporation
            elif Mode == 2: # condensation
                selected_corr = 15 # Koyama condensation
    return selected_corr

def get_2phase_DP_ranges():
    database_path = appdirs.user_data_dir("EGSim")+"/2phase_DP.csv"
    values = pd.read_csv(database_path,index_col=0)
        
    values = values.fillna(0)
    ranges = ValuesClass()
    
    ranges.id_uniq = list(set(values["id"]))

    ranges.id = list(values["id"])

    ranges.deviation = np.array(values["deviation"])
    
    ranges.nu_f = np.array([[values["id"].iloc[i],min(values["nu_f_min"].iloc[i],values["nu_f_max"].iloc[i]),min(values["nu_f_min"].iloc[i],values["nu_f_max"].iloc[i]),max(values["nu_f_min"].iloc[i],values["nu_f_max"].iloc[i]),max(values["nu_f_min"].iloc[i],values["nu_f_max"].iloc[i])] for i in range(len(values))],dtype=float)
    ranges.nu_f[:,1] *= 0.75
    ranges.nu_f[:,4] *= 1.25

    ranges.nu_g = np.array([[values["id"].iloc[i],min(values["nu_g_min"].iloc[i],values["nu_g_max"].iloc[i]),min(values["nu_g_min"].iloc[i],values["nu_g_max"].iloc[i]),max(values["nu_g_min"].iloc[i],values["nu_g_max"].iloc[i]),max(values["nu_g_min"].iloc[i],values["nu_g_max"].iloc[i])] for i in range(len(values))],dtype=float)
    ranges.nu_g[:,1] *= 0.75
    ranges.nu_g[:,4] *= 1.25

    ranges.Sur_ten_f = np.array([[values["id"].iloc[i],min(values["Sur_ten_f_min"].iloc[i],values["Sur_ten_f_max"].iloc[i]),min(values["Sur_ten_f_min"].iloc[i],values["Sur_ten_f_max"].iloc[i]),max(values["Sur_ten_f_min"].iloc[i],values["Sur_ten_f_max"].iloc[i]),max(values["Sur_ten_f_min"].iloc[i],values["Sur_ten_f_max"].iloc[i])] for i in range(len(values))],dtype=float)
    ranges.Sur_ten_f[:,1] *= 0.75
    ranges.Sur_ten_f[:,4] *= 1.25

    ranges.rho_f = np.array([[values["id"].iloc[i],min(values["rho_f_min"].iloc[i],values["rho_f_max"].iloc[i]),min(values["rho_f_min"].iloc[i],values["rho_f_max"].iloc[i]),max(values["rho_f_min"].iloc[i],values["rho_f_max"].iloc[i]),max(values["rho_f_min"].iloc[i],values["rho_f_max"].iloc[i])] for i in range(len(values))],dtype=float)
    ranges.rho_f[:,1] *= 0.75
    ranges.rho_f[:,4] *= 1.25

    ranges.rho_g = np.array([[values["id"].iloc[i],min(values["rho_g_min"].iloc[i],values["rho_g_max"].iloc[i]),min(values["rho_g_min"].iloc[i],values["rho_g_max"].iloc[i]),max(values["rho_g_min"].iloc[i],values["rho_g_max"].iloc[i]),max(values["rho_g_min"].iloc[i],values["rho_g_max"].iloc[i])] for i in range(len(values))],dtype=float)
    ranges.rho_g[:,1] *= 0.75
    ranges.rho_g[:,4] *= 1.25

    ranges.G = np.array([[values["id"].iloc[i],min(values["G_min"].iloc[i],values["G_max"].iloc[i]),min(values["G_min"].iloc[i],values["G_max"].iloc[i]),max(values["G_min"].iloc[i],values["G_max"].iloc[i]),max(values["G_min"].iloc[i],values["G_max"].iloc[i])] for i in range(len(values))],dtype=float)
    ranges.G[:,1] *= 0.5
    ranges.G[:,4] *= 1.5

    ranges.D = np.array([[values["id"].iloc[i],min(values["D_min"].iloc[i],values["D_max"].iloc[i]),min(values["D_min"].iloc[i],values["D_max"].iloc[i]),max(values["D_min"].iloc[i],values["D_max"].iloc[i]),max(values["D_min"].iloc[i],values["D_max"].iloc[i])] for i in range(len(values))],dtype=float)
    ranges.D[:,1] *= 0.75
    ranges.D[:,4] *= 1.5
    
    ranges.Tube_type = np.array([[values["id"].iloc[i],values["tube_type"].iloc[i]] for i in range(len(values))],dtype=float)

    ranges.Mode = np.array([[values["id"].iloc[i],values["mode"].iloc[i]] for i in range(len(values))],dtype=float)
    
    return ranges

def get_2phase_DP_corr(P,G,D,Tube_type,Mode,AS,ranges):    
    values = ValuesClass()
    
    # assign mass flux
    values.G = G
    
    # assign diameter
    values.D = D * 1000
    
    # get physical properties at the pressure given
    AS.update(CP.PQ_INPUTS,P,1)
    mu_g = AS.viscosity() # [uPa-s]
    values.rho_g = AS.rhomass()  # [kg/m^3]
    values.nu_g = mu_g / values.rho_g #[m2/s]  
    
    AS.update(CP.PQ_INPUTS,P,0)
    mu_f = AS.viscosity() # [uPa-s]
    values.rho_f = AS.rhomass()  # [kg/m^3]
    values.nu_f = mu_f / values.rho_f #[m2/s]  
    values.Sur_ten_f = AS.surface_tension() # [mN/m]

    # check for these values against ranges
    props = ["nu_g","nu_f","Sur_ten_f","G","D","rho_f","rho_g"]
    
    # give relative weights for each property
    weights = [1 for i in range(len(props))]
    
    # first, we need to filter the correlations for the tube type and mode (evaporation or condensation)
    corr = list(range(len(ranges.id)))
    corr_to_remove = []
    for i,corr_i in enumerate(corr):
        if (ranges.Mode[corr_i,1] != Mode) and (ranges.Mode[corr_i,1] != 0):
            corr_to_remove.append(corr_i)
    for i in corr_to_remove: corr.remove(i)
    corr_to_remove = []
    for i,corr_i in enumerate(corr):
        if ranges.Tube_type[corr_i,1] != Tube_type:
            corr_to_remove.append(corr_i)
    for i in corr_to_remove: corr.remove(i)
    
    # create scores array
    scores = np.zeros([len(corr),2])
    scores[:,0] = corr
    
    # for each element in props, we will give a score
    for j,element in enumerate(props):
        ranges_i = getattr(ranges,element).copy()
        ranges_i = ranges_i[corr]
        for i,row in enumerate(ranges_i):
            if not all(row): # if ranges doesn't exist, just give a score of 0.5
                scores[i,1] += 0.5 * weights[j]
            else:
                x = [row[1],row[2],row[3],row[4]]
                y = [0,1,1,0]
                value = getattr(values,element)
                score = np.interp(value,x,y)
                scores[i,1] += score * weights[j]
                
    if any(scores[:,1]):
        maximum_score = np.max(scores[:,1])
        scores = scores[scores[:,1] > 0.95 * maximum_score]
        deviations = 1 - ranges.deviation[[int(i) for i in scores[:,0]]]
        for m,deviation in enumerate(deviations):
            if deviation == 1:
                deviations[m] = 0.9
        deviations /= np.max(deviations)
        scores[:,1] *= deviations
        maximum_corr = int(scores[np.argmax(scores[:,1])][0])
        selected_corr = ranges.id[maximum_corr]
    else:
        if Tube_type == 1: # Smooth
            selected_corr = 6 # Friedel
        elif Tube_type == 2: # microfin
            if Mode == 1: # evaporation
                selected_corr = 10 # wu evaporation
            elif Mode == 2: # condensation
                selected_corr = 9 # Koyama condensation
    return selected_corr


def get_AS(Backend,Ref,REFPROP_path=None):
    try:
        ref_list = load_refrigerant_list()
        if not ref_list[0]:
            raise
        ref_list = ref_list[1]
        if Backend == "REFPROP":
            if REFPROP_path != None:
                CP.CoolProp.set_config_string(CP.ALTERNATIVE_REFPROP_PATH, REFPROP_path)
            try:
                AS = CP.AbstractState(Backend,Ref+".MIX")
            except:
                Ref_name = "&".join(ref_list[ref_list[:,0] == Ref][0,1])
                mass_fractions = ref_list[ref_list[:,0] == Ref][0,2]
                AS = CP.AbstractState(Backend, Ref_name) # defining abstract state
                if not len(mass_fractions) == 1:
                    AS.set_mass_fractions(mass_fractions)
        elif Backend == "HEOS":
            try:
                Ref_name = ref_list[ref_list[:,0] == Ref][0,0]
                AS = CP.AbstractState(Backend, Ref_name) # defining abstract state
            except:
                Ref_name = "&".join(ref_list[ref_list[:,0] == Ref][0,1])
                mass_fractions = ref_list[ref_list[:,0] == Ref][0,2]
                AS = CP.AbstractState(Backend, Ref_name) # defining abstract state
                if not len(mass_fractions) == 1:
                    AS.set_mass_fractions(mass_fractions)                
        else:
            raise
        AS.update(CP.QT_INPUTS,1.0,280)
        H_test = AS.hmass()
        p_test = AS.p()
        AS.update(CP.PT_INPUTS,p_test,283)
        H_test = AS.hmass()
        AS.update(CP.HmassP_INPUTS,H_test,p_test)
        AS.T()
        return (1,AS)
    except:
        import traceback
        print(traceback.format_exc())
        return (0,)

if __name__ == "__main__":
    HTC_2phase_ranges = get_2phase_HTC_ranges()
    DP_2phase_ranges = get_2phase_DP_ranges()
    AS = CP.AbstractState("REFPROP","R32")
    print(get_2phase_HTC_corr(6*101325,300,0.008,1,2,AS,HTC_2phase_ranges))
    print(get_2phase_DP_corr(5*101325,350,0.008,1,1,AS,DP_2phase_ranges))