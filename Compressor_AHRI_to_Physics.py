# -*- coding: utf-8 -*-
"""
Created on Wed Feb 10 15:06:52 2021

@author: Omar
"""
import numpy as np
from itertools import product
from backend.CompressorAHRI import CompressorAHRIClass
from backend.CompressorPHY import CompressorPHYClass
import CoolProp as CP

def calculate_efficiencies(Comp_props,AS,Pin_r,Pout_r):
    F_factor = Comp_props['F_factor']
    act_speed = Comp_props['act_speed']
    Displacement = Comp_props['Displacement']
    fp = Comp_props['fp']
    Unit_system = Comp_props['Unit_system']
    Speeds = Comp_props['Speeds']
    P = Comp_props['P_array']
    M = Comp_props['M_array']
    SH_type = Comp_props['SH_type']
        
    # making sure that length of coefficients array and speeds are the same
    if not ((len(P) == len(M)) and (len(P) == len(Speeds))):
        raise AttributeError("please make sure that the length of coefficients array and speeds are the same")
    if not (len(Speeds) == len(set(Speeds))):
        raise AttributeError("please make sure that no speed in speeds array is repeated")
    
    # choose unit system
    if not Unit_system.lower() in ['ip','si',"si2"]:
        raise AttributeError("please choose either ip or si for compressor unit system")
    
    # create a universal array for all coefficients and speeds
    coeffs = []
    for (P_coeffs,M_coeffs,Speed) in zip(P,M,Speeds):
        coeffs.append([Speed,P_coeffs,M_coeffs])
    coeffs = np.array(coeffs,dtype=object)

    #Calculate suction superheat and dew temperatures
    AS.update(CP.PQ_INPUTS, Pin_r, 1.0)
    Tsat_s_K=AS.T() #[K]
    
    AS.update(CP.PQ_INPUTS, Pout_r, 1.0)
    Tsat_d_K=AS.T() #[K]
    
    if SH_type == 0:
        SH_Ref = max(Comp_props['SH_Ref'], 0)
    elif SH_type == 1:
        SH_Ref = max(Comp_props['Suction_Ref'] - Tsat_s_K,0)

    DT_sh_K=SH_Ref

    if Unit_system == "ip":
    #Convert saturation temperatures in K to F
        Tsat_s = (Tsat_s_K - 273.15) * 9/5 + 32
        Tsat_d = (Tsat_d_K - 273.15) * 9/5 + 32
    elif Unit_system == "si":
        Tsat_s = Tsat_s_K - 273.15
        Tsat_d = Tsat_d_K - 273.15
    elif Unit_system == "si2":
        Tsat_s = Tsat_s_K - 273.15
        Tsat_d = Tsat_d_K - 273.15
        
    # to use coefficients of minimum speed if actual speed is lower than it
    if act_speed <= min(coeffs[:,0]): 
        P_coeffs, M_coeffs = coeffs[coeffs[:,0] == min(coeffs[:,0]),[1,2]]
        power_map = P_coeffs[0] + P_coeffs[1] * Tsat_s + P_coeffs[2] * Tsat_d + P_coeffs[3] * Tsat_s**2 + P_coeffs[4] * Tsat_s * Tsat_d + P_coeffs[5] * Tsat_d**2 + P_coeffs[6] * Tsat_s**3 + P_coeffs[7] * Tsat_d * Tsat_s**2 + P_coeffs[8] * Tsat_d**2*Tsat_s + P_coeffs[9] * Tsat_d**3
        mdot_map = M_coeffs[0] + M_coeffs[1] * Tsat_s + M_coeffs[2] * Tsat_d + M_coeffs[3] * Tsat_s**2 + M_coeffs[4] * Tsat_s * Tsat_d + M_coeffs[5] * Tsat_d**2 + M_coeffs[6] * Tsat_s**3 + M_coeffs[7] * Tsat_d * Tsat_s**2 + M_coeffs[8] * Tsat_d**2*Tsat_s + M_coeffs[9] * Tsat_d**3
        power_map = act_speed/min(coeffs[:,0])*power_map
        mdot_map = act_speed/min(coeffs[:,0])*mdot_map

    # to use coefficients of maximum speed if actual speed is higher than it
    elif act_speed >= max(coeffs[:,0]): 
        P_coeffs, M_coeffs = coeffs[coeffs[:,0] == max(coeffs[:,0]),[1,2]]
        power_map = P_coeffs[0] + P_coeffs[1] * Tsat_s + P_coeffs[2] * Tsat_d + P_coeffs[3] * Tsat_s**2 + P_coeffs[4] * Tsat_s * Tsat_d + P_coeffs[5] * Tsat_d**2 + P_coeffs[6] * Tsat_s**3 + P_coeffs[7] * Tsat_d * Tsat_s**2 + P_coeffs[8] * Tsat_d**2*Tsat_s + P_coeffs[9] * Tsat_d**3
        mdot_map = M_coeffs[0] + M_coeffs[1] * Tsat_s + M_coeffs[2] * Tsat_d + M_coeffs[3] * Tsat_s**2 + M_coeffs[4] * Tsat_s * Tsat_d + M_coeffs[5] * Tsat_d**2 + M_coeffs[6] * Tsat_s**3 + M_coeffs[7] * Tsat_d * Tsat_s**2 + M_coeffs[8] * Tsat_d**2*Tsat_s + M_coeffs[9] * Tsat_d**3
        power_map = act_speed/max(coeffs[:,0])*power_map
        mdot_map = act_speed/max(coeffs[:,0])*mdot_map

    # to interpolate between values matich speeds higher and lower than the actual speed in the map
    else:
        if not (act_speed in coeffs[:,0]): # check if the speed is in the map or not
            # first, create a dummy row for the actual speed
            coeffs = np.vstack((coeffs,[act_speed,0,0]))

            # sort the array using speeds
            coeffs = coeffs[coeffs[:,0].argsort()]
            
            # getting the index of the actual speed
            index = np.where(coeffs[:,0] == act_speed)
            
            # index of speed lower and higher than actual speed
            index1 = int(index[0])-1
            index2 = int(index[0])+1
            
            # coefficients of lower speed
            P_coeffs = coeffs[index1,1]
            M_coeffs = coeffs[index1,2]
            
            # values matching the coefficients
            power_map1 = P_coeffs[0] + P_coeffs[1] * Tsat_s + P_coeffs[2] * Tsat_d + P_coeffs[3] * Tsat_s**2 + P_coeffs[4] * Tsat_s * Tsat_d + P_coeffs[5] * Tsat_d**2 + P_coeffs[6] * Tsat_s**3 + P_coeffs[7] * Tsat_d * Tsat_s**2 + P_coeffs[8] * Tsat_d**2*Tsat_s + P_coeffs[9] * Tsat_d**3
            mdot_map1 = M_coeffs[0] + M_coeffs[1] * Tsat_s + M_coeffs[2] * Tsat_d + M_coeffs[3] * Tsat_s**2 + M_coeffs[4] * Tsat_s * Tsat_d + M_coeffs[5] * Tsat_d**2 + M_coeffs[6] * Tsat_s**3 + M_coeffs[7] * Tsat_d * Tsat_s**2 + M_coeffs[8] * Tsat_d**2*Tsat_s + M_coeffs[9] * Tsat_d**3
            
            # coefficients of higher speed
            P_coeffs = coeffs[index2,1]
            M_coeffs = coeffs[index2,2]

            # values matching the coefficients
            power_map2 = P_coeffs[0] + P_coeffs[1] * Tsat_s + P_coeffs[2] * Tsat_d + P_coeffs[3] * Tsat_s**2 + P_coeffs[4] * Tsat_s * Tsat_d + P_coeffs[5] * Tsat_d**2 + P_coeffs[6] * Tsat_s**3 + P_coeffs[7] * Tsat_d * Tsat_s**2 + P_coeffs[8] * Tsat_d**2*Tsat_s + P_coeffs[9] * Tsat_d**3
            mdot_map2 = M_coeffs[0] + M_coeffs[1] * Tsat_s + M_coeffs[2] * Tsat_d + M_coeffs[3] * Tsat_s**2 + M_coeffs[4] * Tsat_s * Tsat_d + M_coeffs[5] * Tsat_d**2 + M_coeffs[6] * Tsat_s**3 + M_coeffs[7] * Tsat_d * Tsat_s**2 + M_coeffs[8] * Tsat_d**2*Tsat_s + M_coeffs[9] * Tsat_d**3
            
            # constructing an array of lower speed and its values, the higher speed and its values
            SPM_array = np.array([[coeffs[index1,0],power_map1,mdot_map1],[coeffs[index2,0],power_map2,mdot_map2]])
            
            # interpolating between actual speed and higher and lower speeds
            power_map = np.interp(act_speed,SPM_array[:,0],SPM_array[:,1])
            mdot_map = np.interp(act_speed,SPM_array[:,0],SPM_array[:,2])
        else: # there is a speed in the map matching actual speed
            # get the index of the speed
            index = int(np.where(coeffs[:,0] == act_speed)[0])
            # get the coefficients
            P_coeffs = coeffs[index,1]
            M_coeffs = coeffs[index,2]
            # get the values
            power_map = P_coeffs[0] + P_coeffs[1] * Tsat_s + P_coeffs[2] * Tsat_d + P_coeffs[3] * Tsat_s**2 + P_coeffs[4] * Tsat_s * Tsat_d + P_coeffs[5] * Tsat_d**2 + P_coeffs[6] * Tsat_s**3 + P_coeffs[7] * Tsat_d * Tsat_s**2 + P_coeffs[8] * Tsat_d**2*Tsat_s + P_coeffs[9] * Tsat_d**3
            mdot_map = M_coeffs[0] + M_coeffs[1] * Tsat_s + M_coeffs[2] * Tsat_d + M_coeffs[3] * Tsat_s**2 + M_coeffs[4] * Tsat_s * Tsat_d + M_coeffs[5] * Tsat_d**2 + M_coeffs[6] * Tsat_s**3 + M_coeffs[7] * Tsat_d * Tsat_s**2 + M_coeffs[8] * Tsat_d**2*Tsat_s + M_coeffs[9] * Tsat_d**3
    
    if Unit_system == "ip":
        # Convert mass flow rate to kg/s from lbm/h
        mdot_map *= 0.000125998
    elif Unit_system == "si2":
        # Convert mass flow rate to kg/s from kg/hr
        mdot_map /= 3600
        
    # inlet and outlet pressures of compressor
    P1 = Pin_r
    P2 = Pout_r
    
    # inlet temperature to the compressor
    if DT_sh_K >= 1e-3:
        T1_actual = Tsat_s_K + DT_sh_K
    
    else: # if superheat in the compressor is negative, then assume inlet to compressor is saturated (1e-3 is just a small margin for CoolProp to be able to calculate the value)
        T1_actual = Tsat_s_K + 1e-3
        
    T1_map = Tsat_s_K + SH_Ref
    
    # getting values at T1_map
    AS.update(CP.PT_INPUTS, P1, T1_map)
    v_map = 1 / AS.rhomass() #[m^3/kg]
    s1_map = AS.smass() #[J/kg-K]
    h1_map = AS.hmass() #[J/kg]
    
    # getting values at T1_actual
    AS.update(CP.PT_INPUTS, P1, T1_actual)
    s1_actual = AS.smass() #[J/kg-K]
    h1_actual = AS.hmass() #[J/kg]
    v_actual = 1 / AS.rhomass() #[m^3/kg]
    F = F_factor # Volumetric efficiency correction factor
    mdot = (1 + F * (v_map / v_actual - 1)) * mdot_map

    #volumetric efficiency calculation
    eta_v = mdot/(Displacement/v_actual*act_speed/60)
    
    # getting outlet isentropic values
    AS.update(CP.PSmass_INPUTS, P2, s1_map)
    h2s_map = AS.hmass() #[J/kg]        
    AS.update(CP.PSmass_INPUTS, P2, s1_actual)
    h2s_actual = AS.hmass() #[J/kg]
    
    #Shaft power based on reference superheat calculation from fit overall isentropic efficiency
    power = power_map * (mdot / mdot_map) * (h2s_actual - h1_actual) / (h2s_map - h1_map)

    # calculating actual isentropic efficiency
    eta_isen = mdot * (h2s_actual - h1_actual) / power
    
    return eta_v, eta_isen

def AHRI_to_Physics(Comp_props,AS,Tevap_range,Tcond_range,volum_model_degree,isen_model_degree):
    Tevap = tuple(np.linspace(Tevap_range[0],Tevap_range[1],Tevap_range[2]))
    Tcond = tuple(np.linspace(Tcond_range[0],Tcond_range[1],Tcond_range[2]))
    potentials = product(Tevap,Tcond)
    results = []
    for Tevap_i, Tcond_i in potentials:
        try:
            AS.update(CP.QT_INPUTS, 1.0, Tevap_i)
            Pin=AS.p()
            AS.update(CP.QT_INPUTS, 1.0, Tcond_i)
            Pout=AS.p()
            eta_v, eta_isen = calculate_efficiencies(Comp_props,AS,Pin,Pout)
            results.append([Tevap_i,Tcond_i,Pin,Pout,eta_v,eta_isen])
        except:
            import traceback
            print(traceback.format_exc())
            pass
    if results:
        # regression for volumetric efficiency model
        data = np.array([[row[3]/row[2],row[4],row[5]] for row in results])
        coeffs_volum = np.flip(np.polyfit(data[:,0], data[:,1],volum_model_degree))
    
        # regression for isentropic efficiency model
        data = np.array([[row[3]/row[2],row[4],row[5]] for row in results])
        coeffs_isen = np.flip(np.polyfit(data[:,0], data[:,2],isen_model_degree))
        
        volum_exp = "%.5g" % coeffs_volum[0]
        if len(coeffs_volum) > 1:
            for j,i in enumerate(coeffs_volum[1:]):
                if i >= 0:
                    volum_exp += " + %.5g" % np.abs(i) + "*PR**"+str(j+1)
                else:
                    volum_exp += " - %.5g" % np.abs(i) + "*PR**"+str(j+1)
        isen_exp = "%.5g" % coeffs_isen[0]
        if len(coeffs_isen) > 1:
            for j,i in enumerate(coeffs_isen[1:]):
                if i >= 0:
                    isen_exp += " + %.5g" % np.abs(i) + "*PR**"+str(j+1)
                else:
                    isen_exp += " - %.5g" % np.abs(i) + "*PR**"+str(j+1)
        return volum_exp, isen_exp
    else:
        raise Exception("Failed to find model")

def validation_physics_model(Comp_props,Tevap_range,Tcond_range,vol_eff,isen_eff,AS,Ref):
    results = []
    for Tevap,Tcond in product(tuple(np.linspace(*Tevap_range)),tuple(np.linspace(*Tcond_range))):
        try:
            Comp_AHRI = CompressorAHRIClass()
            AS.update(CP.QT_INPUTS,1.0,Tcond)
            Pout_r = AS.p()
            AS.update(CP.QT_INPUTS,1.0,Tevap)
            Pin_r = AS.p()
            if Comp_props['SH_type'] == 0:
                SH_Ref = max(Comp_props['SH_Ref'], 0)
            elif Comp_props['SH_type'] == 1:
                SH_Ref = max(Comp_props['Suction_Ref'] - Tevap,0)
        
            DT=SH_Ref
            AS.update(CP.PT_INPUTS,Pin_r,Tevap+DT)
            hin_r = AS.hmass()
            kwds={
                  'name':'Generic',
                  'M':Comp_props['M_array'],
                  'P':Comp_props['P_array'],
                  'Speeds':Comp_props['Speeds'],
                  'AS': AS, #Abstract state
                  'Ref': Ref,
                  'hin_r':hin_r,
                  'Pin_r':Pin_r,
                  'Pout_r':Pout_r,
                  'fp':Comp_props['fp'], #Fraction of electrical power lost as heat to ambient
                  'Vdot_ratio_P': 1.0, #Displacement Scale factor
                  'Vdot_ratio_M': 1.0, #Displacement Scale factor
                  'Displacement':Comp_props['Displacement'],
                  'act_speed': Comp_props['act_speed'],
                  'Unit_system':Comp_props['Unit_system'],
                  'Elec_eff':1.0,
                  'F_factor':Comp_props['F_factor'], # volumetric efficiency correction factor, used as 0.75 in several sources
                  }
            Comp_AHRI=CompressorAHRIClass(**kwds)
            if Comp_props['SH_type'] == 0:
                Comp_AHRI.SH_Ref = Comp_props['SH_Ref']
            elif Comp_props['SH_type'] == 1:
                Comp_AHRI.Suction_Ref = Comp_props['Suction_Ref']
            Comp_AHRI.Calculate()
            kwds={
                  'isen_eff': isen_eff,
                  'vol_eff': vol_eff,
                  'F_factor': Comp_props['F_factor'],
                  'AS': AS, #Abstract state
                  'Ref': Ref,
                  'hin_r':hin_r,
                  'Pin_r':Pin_r,
                  'Pout_r':Pout_r,
                  'fp':Comp_props['fp'], #Fraction of electrical power lost as heat to ambient
                  'Vdot_ratio_P': 1.0, #Displacement Scale factor
                  'Vdot_ratio_M': 1.0, #Displacement Scale factor
                  'Displacement':Comp_props['Displacement'],
                  'act_speed':Comp_props['act_speed'],
                  'Elec_eff':1.0,
                  }
            Comp_PHY=CompressorPHYClass(**kwds)
            if Comp_props['SH_type'] == 0:
                Comp_PHY.SH_Ref = Comp_props['SH_Ref']
            elif Comp_props['SH_type'] == 1:
                Comp_PHY.Suction_Ref = Comp_props['Suction_Ref']
            Comp_PHY.Calculate()
            results.append([Comp_AHRI.power_mech,Comp_PHY.power_mech,Comp_AHRI.mdot_r,Comp_PHY.mdot_r])
        except ValueError:
            pass
    results = np.array(results)
    rmse_M = np.sqrt((((results[:,0] - results[:,1])/results[:,0])**2).mean(axis=None))*100
    rmse_P = np.sqrt((((results[:,2] - results[:,3])/results[:,2])**2).mean(axis=None))*100
    return "%.5g" % rmse_M, "%.5g" %rmse_P

if __name__ == '__main__':
    import CoolProp as CP
    import inspect
    Comp_props = {'F_factor': 0.75,
                  'act_speed': 2900,
                  'M_array':[(61.371452,2.672678869,5.81E-02,2.32E-02,-1.39E-02,2.20E-03,7.70E-05,-8.32E-05,9.00E-05,-2.92E-05)],
                  'P_array':[(-151.3482321,-11.39785172,18.67172883,-0.133004751,0.264825957,-0.178083358,2.84E-04,0.001019785,-0.001586543,0.001037067)],
                  'Displacement':1.50761e-5,
                  'fp':0.0,
                  'Unit_system':'ip',
                  'Speeds':[2900],
                  'SH_type':0,
                  'SH_Ref':20*5/9
                  }
    
    Ref = 'R410a'
    Backend = "HEOS"
    AS = CP.AbstractState(Backend, Ref)
    Tevap_range = (260,290,32)
    Tcond_range = (300,320,21)
    volum_model_degree = 2
    isen_model_degree = 2
    vol_eff, isen_eff = AHRI_to_Physics(Comp_props,AS,Tevap_range,Tcond_range,volum_model_degree,isen_model_degree)
    
    print(validation_physics_model(Comp_props,Tevap_range,Tcond_range,vol_eff,isen_eff,AS,Ref))
    # Validation
    results = []
    for Tevap,Tcond in product(tuple(np.linspace(*Tevap_range)),tuple(np.linspace(*Tcond_range))):
        try:
            Comp_AHRI = CompressorAHRIClass()
            AS.update(CP.QT_INPUTS,1.0,Tcond)
            Pout_r = AS.p()
            AS.update(CP.QT_INPUTS,1.0,Tevap)
            Pin_r = AS.p()
            DT = 20*5/9
            AS.update(CP.PT_INPUTS,Pin_r,Tevap+DT)
            hin_r = AS.hmass()
            kwds={
                  'name':'Generic',
                  'M':Comp_props['M_array'],
                  'P':Comp_props['P_array'],
                  'Speeds':Comp_props['Speeds'],
                  'AS': AS, #Abstract state
                  'Ref': Ref,
                  'hin_r':hin_r,
                  'Pin_r':Pin_r,
                  'Pout_r':Pout_r,
                  'fp':Comp_props['fp'], #Fraction of electrical power lost as heat to ambient
                  'Vdot_ratio_P': 1.0, #Displacement Scale factor
                  'Vdot_ratio_M': 1.0, #Displacement Scale factor
                  'Displacement':Comp_props['Displacement'],
                  'SH_type':Comp_props['SH_type'],
                  'SH_Ref':Comp_props['SH_Ref'],
                  'act_speed': Comp_props['act_speed'],
                  'Unit_system':Comp_props['Unit_system'],
                  'Elec_eff':1.0,
                  'F_factor':Comp_props['F_factor'], # volumetric efficiency correction factor, used as 0.75 in several sources
                  }
            Comp_AHRI=CompressorAHRIClass(**kwds)
            Comp_AHRI.Calculate()
            kwds={
                  'isen_eff': isen_eff,
                  'vol_eff': vol_eff,
                  'SH_type':Comp_props['SH_type'],
                  'SH_Ref':Comp_props['SH_Ref'],
                  'F_factor':Comp_props['F_factor'], # volumetric efficiency correction factor, used as 0.75 in several sources
                  'AS': AS, #Abstract state
                  'Ref': Ref,
                  'hin_r':hin_r,
                  'Pin_r':Pin_r,
                  'Pout_r':Pout_r,
                  'fp':Comp_props['fp'], #Fraction of electrical power lost as heat to ambient
                  'Vdot_ratio_P': 1.0, #Displacement Scale factor
                  'Vdot_ratio_M': 1.0, #Displacement Scale factor
                  'Displacement':Comp_props['Displacement'],
                  'act_speed':Comp_props['act_speed'],
                  'Elec_eff':1.0,
                  }
            Comp_PHY=CompressorPHYClass(**kwds)
            Comp_PHY.Calculate()
            results.append([Pout_r/Pin_r,Comp_AHRI.power_mech,Comp_PHY.power_mech,Comp_AHRI.mdot_r,Comp_PHY.mdot_r,Tevap,Tcond])
        except ValueError:
            pass
    results = np.array(results)
    import matplotlib.pyplot as plt
    from scipy.interpolate import griddata
    fig, host = plt.subplots(figsize=(8,5)) # (width, height) in inches
    plt.subplots_adjust(right=0.75)
    par1 = host.twinx()
        
    host.set_xlabel("Pressure ratio")
    host.set_ylabel("Power")
    par1.set_ylabel("Mass flowrate")

    color1 = plt.cm.viridis(0)
    color2 = plt.cm.viridis(0.3)
    color3 = plt.cm.viridis(.7)
    color4 = plt.cm.viridis(.9)
        
    p1_1, = host.plot(results[:,0], results[:,1],'.', label="AHRI Power", color=color1)
    p1_2, = host.plot(results[:,0], results[:,2],'.', label="Physics Power", color=color3)
    p2_1, = par1.plot(results[:,0], results[:,3],'x', label="AHRI Mass flowrate", color=color2)
    p2_2, = par1.plot(results[:,0], results[:,4],'x', label="Physics Mass flowrate", color=color4)
        
    host.legend(["AHRI Power","Physics Power"],loc="lower left")
    par1.legend(["AHRI Mass flowrate","Physics Mass flowrate"],loc="upper right")
    
    host.yaxis.label.set_color(p1_1.get_color())
    par1.yaxis.label.set_color(p1_2.get_color())
    fig.tight_layout()
    
    plt.draw()
    plt.show()

    plt.figure()
    power_error = np.abs((results[:,1]-results[:,2])/results[:,1])*100
    mass_flowrate_error = np.abs((results[:,3]-results[:,4])/results[:,3])*100
    plt.plot(results[:,0],power_error,'.',label="Power Error (%)",color=color1)
    plt.plot(results[:,0],mass_flowrate_error,'x',label="Mass flowrate Error (%)",color=color4)
    plt.legend()
    Tevap = np.linspace(*Tevap_range)
    Tcond = np.linspace(*Tcond_range)

    fig, ax = plt.subplots(constrained_layout=True)
    xi = np.array(list(set(results[:,5].copy())))
    yi = np.array(list(set(results[:,6].copy())))
    xi,yi = np.meshgrid(xi,yi)
    zi = griddata((results[:,5], results[:,6]), power_error, (xi,yi))
    plt.contourf(xi,yi,zi,20,cmap = plt.get_cmap('rainbow'))
    plt.colorbar()
    plt.xlabel("Evaporating Temperature (K)")
    plt.ylabel("Condensing Temperature (K)")
    