from __future__ import division, print_function, absolute_import
import numpy as np
import CoolProp as CP
from sympy.parsing.sympy_parser import parse_expr
from sympy import Symbol

class CompressorPHYClass():
    """
    Physics model compressor based on isentropic efficiency and volumetric 
    efficiency as a function of pressure ratio
    
    Required Parameters:
    
    ===========    ==========  ========================================================================
    Variable       Units       Description
    ===========    ==========  ========================================================================
    isen_eff       --          Symbolic expression of isentropic efficiency as function of x (pressure ratio) assuming zero shell loss
    vol_eff        --          Symbolic expression of volumetric efficiency as function of x (pressure ratio)
    Elec_eff       --          Electrical efficiency (from electrical power to shaft power)
    Speed          RPM         Actual speed of compressor
    Displacement   m3/rev      Displacement volume per revolution of compressor
    Ref            N/A         A string representing the refrigerant
    hin_r          K           Refrigerant inlet enthalpy
    Pin_r          Pa          Refrigerant suction pressure (absolute)
    Pout_r         Pa          Refrigerant discharge3 pressure (absolute)
    fp             --          Fraction of shaft power lost as heat to ambient
    Vdot_ratio_P   --          Power Scale factor
    Vdot_ratio_M   --          Mass flow rate Scale factor
    ===========   ==========  ========================================================================
    
    All variables are of double-type unless otherwise specified
        
    """
    def __init__(self,**kwargs):
        #Load up the parameters passed in
        # using the dictionary
        self.__dict__.update(kwargs)
        self.terminate = False
    def Update(self,**kwargs):
        #Update the parameters passed in
        # using the dictionary
        self.__dict__.update(kwargs)
        
    def OutputList(self):
        """
            Return a list of parameters for this component for further output
            
            It is a list of tuples, and each tuple is formed of items with indices:
                [0] Description of value
                
                [1] Units of value
                
                [2] The value itself
        """
        
        return [ 
            ('Name','',self.name),
            ('','',''),
            ('Compressor Speed','rpm',self.act_speed),
            ('Displacement volume per revolution','m^3',self.Displacement),
            ('Heat Loss Fraction','%',self.fp*100),
            ('Power scale factor','-',self.Vdot_ratio_P),
            ('Mass flow rate scale factor','-',self.Vdot_ratio_M),
            ('','',''),
            ('','',''),
            ('Mechanical power','W',self.power_mech),
            ('Electrical power','W',self.power_elec),
            ('','',''),
            ('Mass flow rate','kg/s',self.mdot_r),
            ('','',''),
            ('Inlet Pressure','Pa',self.Pin_r),
            ('Inlet Temperature','C',self.Tin_r-273.15),
            ('Inlet Enthalpy','J/kg',self.hin_r),
            ('Inlet Entropy','J/K',self.sin_r),
            ('','',''),
            ('Outlet Pressure','Pa',self.Pout_r),
            ('Outlet Temperature','C',self.Tout_r-273.15),
            ('Outlet Enthalpy','J/kg',self.hout_r),
            ('Outlet Entropy','J/K',self.sout_r),
            ('','',''),
            ('','',''),
            ('isentropic efficiency assuming zero shell loss','%',self.eta_isen*100),
            ('Volumetric Efficiency','%',self.eta_v*100),
            ('Electrical Efficiency','%',self.Elec_eff*100),
            ('','',''),
            ('Pumped flow rate','m^3/s',self.Vdot_pumped),
            ('Ambient heat loss','W',self.Q_amb),
            ('Pressure ratio','-',self.PR),
            ('','',''),
            ('','',''),
            ('Reference Mass flow rate','kg/s',self.mdot_ref),
            ('','',''),
            ('Entropy generation','W/K',self.S_gen),
         ]
        
    def Calculate(self):
        #AbstractState
        AS = self.AS
        
        # getting isentropic and volumetric efficiency expressions
        try:
            isen_eff=parse_expr(self.isen_eff)
            vol_eff=parse_expr(self.vol_eff)
        except:
            raise AttributeError("error in parsing isentropic or volumetric efficiencies expressions")
        
        # getting expression variables
        all_symbols_isen = [str(x) for x in isen_eff.atoms(Symbol)]
        all_symbols_vol = [str(x) for x in vol_eff.atoms(Symbol)]
        
        # calculating pressure ratio
        PR = self.Pout_r/self.Pin_r

        # making sure 1 variable (pressure ratio) is present
        if len(all_symbols_isen) != 1:
            if len(all_symbols_isen) == 0: # if no variable is given, then a number is given
                isen_eff_value = isen_eff.evalf()
            else:
                raise AttributeError("error in parsing isentropic or volumetric efficiencies expressions")
        else:
            # calculating and assigning pressure ratio to variable
            symbol_vals_isen = {all_symbols_isen[0]: PR}

            # evaluating expression
            isen_eff_value = float(isen_eff.subs(symbol_vals_isen))
        
        # making sure 1 variable (pressure ratio) is present
        if len(all_symbols_vol) != 1:
            if len(all_symbols_vol) == 0: # if no variable is given, then a number is given
                vol_eff_value = vol_eff.evalf()
            else:
                raise AttributeError("error in parsing isentropic or volumetric efficiencies expressions")
        else:
            # calculating and assigning pressure ratio to variable
            symbol_vals_vol = {all_symbols_vol[0]: PR}
                    
            # evaluating expression
            vol_eff_value = float(vol_eff.subs(symbol_vals_vol))
                
        # getting values
        h1 = self.hin_r
        P1 = self.Pin_r
        V_rev = self.Displacement
        N = self.act_speed
        P2 = self.Pout_r
        fp = self.fp
        elec_eff = self.Elec_eff
        
        # inlet properties
        AS.update(CP.HmassP_INPUTS, h1, P1)
        rho1 = AS.rhomass() #[kg/m^3]
        s1 = AS.smass()
        T1 = AS.T()
                
        # using reference state to find reference density
        AS.update(CP.PQ_INPUTS, self.Pin_r, 1.0)
        Tsat_s_K=AS.T() #[K]
        
        if hasattr(self,"SH_Ref"):
            SH_Ref = self.SH_Ref # in k
            
        elif hasattr(self,"Suction_Ref"):
            SH_Ref = self.Suction_Ref - Tsat_s_K
        
        if SH_Ref <= 1e-3:
            SH_Ref = 1e-3
        
        T1_ref = Tsat_s_K + SH_Ref
        AS.update(CP.PT_INPUTS, P1, T1_ref)
        rho_ref = AS.rhomass() #[m^3/kg]

        # calculating mass flow rate from volumetric efficiency
        mdot_ref = V_rev * N / 60 * rho_ref * vol_eff_value
        
        mdot_ref *= self.Vdot_ratio_M
        
        self.mdot_ref = mdot_ref
        
        mdot = (1 + self.F_factor * (rho1 / rho_ref - 1)) * mdot_ref
        
        # calculating outlet enthalpy from isentropic efficiency
        AS.update(CP.PSmass_INPUTS, P2, s1)
        h2s = AS.hmass()
        h2 = (h2s - h1) / isen_eff_value * (1-fp) + h1
        
        # calculating shaft power
        shaft_power = mdot * (h2 - h1) / (1 - fp)

        shaft_power *= self.Vdot_ratio_P

        h2 = shaft_power * (1 - fp) / mdot + h1
        
        # calculating electrical power
        elect_power = shaft_power / elec_eff
                
        # outlet properties
        AS.update(CP.HmassP_INPUTS, h2, P2)
        s2 = AS.smass()
        T2 = AS.T()

        # recalculating the volumetric efficiency using the corrected mass flow rate        
        self.eta_v = mdot/(self.Displacement*rho1*self.act_speed/60)

        # calculating actual isentropic efficiency
        self.eta_isen = mdot * (h2s - h1) / shaft_power
        
        # saving results
        self.mdot_r_adj = (1 + self.F_factor * (rho1 / rho_ref - 1))
        self.hout_r_s = h2s
        self.vin_r = 1 / rho1
        self.Tin_r = T1
        self.Tout_r = T2
        self.sout_r = s2
        self.sin_r = s1
        self.hout_r = h2
        self.hin_r = h1
        self.mdot_r = mdot
        self.power_mech = shaft_power
        self.power_elec = elect_power
        self.Vdot_pumped = mdot/rho1
        self.Q_amb = -shaft_power * fp
        self.PR = PR
        self.S_gen = mdot * (s2 - s1)
        
if __name__=='__main__':
    def fun1():
        #Abstract State        
        Ref = 'R410a'
        Backend = 'HEOS'
        AS = CP.AbstractState(Backend, Ref)
        Tcond = (125 - 32) * 5 / 9
        Tevap = (51 - 32) * 5 / 9
        AS.update(CP.QT_INPUTS,1.0,Tcond+273.15)
        Pout_r = AS.p()
        AS.update(CP.QT_INPUTS,1.0,Tevap+273.15)
        Pin_r = AS.p()
        DT = 7*5/9
        AS.update(CP.PT_INPUTS,Pin_r,Tevap+DT+273.15)
        hin_r = AS.hmass()
        kwds={
              'name': 'physics_generic_compressor',
              'isen_eff': '0.7', # isentropic efficiency expression as f(Pressure ratio)
              'vol_eff': '0.9', # volumetric efficiency expression as f(Pressure ratio)
              'AS': AS, #Abstract state
              'Ref': Ref, # refrgierant name
              'hin_r':hin_r, # inlet refrigerant enthalpy
              'Pin_r':Pin_r, # inlet refrigerant pressure
              'Pout_r':Pout_r, # outlet refrigerant pressure
              'fp':0.1, #Fraction of electrical power lost as heat to ambient
              'Vdot_ratio_P': 1.0, #Displacement Scale factor
              'Vdot_ratio_M': 1.0, #Displacement Scale factor
              'Displacement':0.000530671 * 0.3048**3, # displacement volume per revolution
              'act_speed':5200, # operating speed of the compressor
              'Elec_eff':1.0, # electrical efficiency
              'Suction_Ref':35+273, # electrical efficiency
              'F_factor':0.75, # electrical efficiency
              }
        Comp=CompressorPHYClass(**kwds)
        Comp.Calculate()
        print(*Comp.OutputList(),sep="\n")
            
    fun1()