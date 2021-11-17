import CoolProp as CP
from scipy.optimize import fsolve

def precondition_TXV(Cycle, epsilon=0.9):

    #Assume the heat exchangers are highly effective
    #Condensing heat transfer rate from enthalpies
    rho_air=1.1
    Cp_air =1005 #[J/kg/K]
    
    #AbstractState
    AS = Cycle.AS
    
    def OBJECTIVE(x):
        Tevap=x[0]
        Tcond=x[1]
        DT_sh=abs(x[2])

        #Use fixed effectiveness to get a guess for the condenser capacity
        Qcond=epsilon*Cycle.Condenser.Vdot_ha*rho_air*(Cycle.Condenser.Tin_a-Tcond)*Cp_air
        
        AS.update(CP.QT_INPUTS,1.0,Tevap)
        pevap=AS.p() #[pa]
        AS.update(CP.QT_INPUTS,0.0,Tcond)
        pcond=AS.p() #[pa]

        AS.update(CP.PT_INPUTS,pevap, Tevap+DT_sh)
        hin_comp = AS.hmass()
        
        params={
                'Pin_r': pevap,
                'Pout_r': pcond,
                'hin_r': hin_comp,
                'AS': AS,
                }
        Cycle.Compressor.Update(**params)
        Cycle.Compressor.Calculate()
        
        W=Cycle.Compressor.power_mech
        
        # Evaporator fully-dry analysis
        Qevap=epsilon*Cycle.Evaporator.Vdot_ha*rho_air*(Cycle.Evaporator.Tin_a-Tevap)*Cp_air
        
        if Cycle.Second_Cond == 'Subcooling': #if Subcooling is imposed
            AS.update(CP.PT_INPUTS,pcond,Tcond-Cycle.cond2_value)
            h_target = AS.hmass() #[J/kg]
            Qcond_enthalpy=Cycle.Compressor.mdot_r*(Cycle.Compressor.hout_r-h_target)
        elif Cycle.Second_Cond == 'Charge': #if Charge is imposed
            AS.update(CP.PT_INPUTS,pcond,Tcond-5)
            h_target = AS.hmass() #[J/kg]
            Qcond_enthalpy=Cycle.Compressor.mdot_r*(Cycle.Compressor.hout_r-h_target)
        
        Qevap_enthalpy=Cycle.Compressor.mdot_r*(Cycle.Compressor.hin_r-h_target)
        
        resids=[Qevap+W+Qcond,Qcond+Qcond_enthalpy,Qevap-Qevap_enthalpy]#,f_dry]
        return resids
    
    Tevap_init=Cycle.Evaporator.Tin_a-15
    Tcond_init=Cycle.Condenser.Tin_a+8
    DT_sh_init=Cycle.SH_value
    
    x = fsolve(OBJECTIVE,[Tevap_init,Tcond_init,DT_sh_init])
    DT_evap=Cycle.Evaporator.Tin_a-x[0]
    DT_cond=x[1]-Cycle.Condenser.Tin_a
    DT_sh=abs(x[2])
    
    return DT_evap, DT_cond, DT_sh

def precondition_capillary(Cycle, epsilon=0.9):

    #Assume the heat exchangers are highly effective
    #Condensing heat transfer rate from enthalpies
    rho_air=1.1
    Cp_air =1005 #[J/kg/K]
    
    #AbstractState
    AS = Cycle.AS
    
    def OBJECTIVE(x):
        Tevap=x[0]
        Tcond=x[1]
        DT_sh=abs(x[2])

        #Use fixed effectiveness to get a guess for the condenser capacity
        Qcond=epsilon*Cycle.Condenser.Vdot_ha*rho_air*(Cycle.Condenser.Tin_a-Tcond)*Cp_air
        
        AS.update(CP.QT_INPUTS,1.0,Tevap)
        pevap=AS.p() #[pa]
        AS.update(CP.QT_INPUTS,1.0,Tcond)
        pcond=AS.p() #[pa]

        AS.update(CP.PT_INPUTS,pevap, Tevap+DT_sh)
        hin_comp = AS.hmass()
        
        params={
                'Pin_r': pevap,
                'Pout_r': pcond,
                'hin_r': hin_comp,
                'AS': AS,
                }
        Cycle.Compressor.Update(**params)
        Cycle.Compressor.Calculate()
        
        W=Cycle.Compressor.power_mech
        
        # Evaporator fully-dry analysis
        Qevap=epsilon*Cycle.Evaporator.Vdot_ha*rho_air*(Cycle.Evaporator.Tin_a-Tevap)*Cp_air
        
        if Cycle.Second_Cond == 'Subcooling': #if Subcooling is imposed
            AS.update(CP.PT_INPUTS,pcond,Tcond-Cycle.cond2_value)
            h_target = AS.hmass() #[J/kg]
            Qcond_enthalpy=Cycle.Compressor.mdot_r*(Cycle.Compressor.hout_r-h_target)
        elif Cycle.Second_Cond == 'Charge': #if Charge is imposed
            AS.update(CP.PT_INPUTS,pcond,Tcond-5)
            h_target = AS.hmass() #[J/kg]
            Qcond_enthalpy=Cycle.Compressor.mdot_r*(Cycle.Compressor.hout_r-h_target)
        
        Qevap_enthalpy=Cycle.Compressor.mdot_r*(Cycle.Compressor.hin_r-h_target)
        
        resids=[Qevap+W+Qcond,Qcond+Qcond_enthalpy,Qevap-Qevap_enthalpy]#,f_dry]
        return resids
    
    Tevap_init=Cycle.Evaporator.Tin_a-15
    Tcond_init=Cycle.Condenser.Tin_a+8
    DT_sh_init=Tevap_init+5
    
    x = fsolve(OBJECTIVE,[Tevap_init,Tcond_init,DT_sh_init])
    DT_evap=Cycle.Evaporator.Tin_a-x[0]
    DT_cond=x[1]-Cycle.Condenser.Tin_a
    DT_sh=abs(x[2])
    
    return DT_evap, DT_cond, DT_sh
    