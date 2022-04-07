from __future__ import division, print_function, absolute_import
import numpy as np
import CoolProp as CP

class CompressorAHRIClass():
    """
    Compressor Model based on 10-coefficient Model from `ANSI/AHRI standard 540 <http://www.ahrinet.org/App_Content/ahri/files/standards%20pdfs/ANSI%20standards%20pdfs/ANSI-ARI-540-2004%20latest.pdf>`_
    
    Required Parameters:
    
    ===========    ==============   ========================================================================
    Variable       Units            Description
    ===========    ==============   ========================================================================
    M              Ibm/hr or kg/s   list of tuples, each containing 10 coefficient
    P              Watts            list of tuples, each containing 10 coefficient
    Speeds         RPM              list of speeds matching each set of coefficients of M and P
    act_speed      RPM              Actual speed of compressor
    Displacement   m3/rev           Displacement volume per revolution of compressor
    hin_r          J/kg             Refrigerant inlet enthalpy
    Pin_r          Pa               Refrigerant suction pressure (absolute)
    Pout_r         Pa               Refrigerant discharge3 pressure (absolute)
    fp             --               Fraction of shaft power lost as heat to ambient
    Elec_eff       --               Electrical efficiency (from electrical power to shaft power)
    SH_Ref         R or C           Standard of Superheat for the map; R for IP, C for SI
    Vdot_ratio_P   --               Power Scale factor
    Vdot_ratio_M   --               Mass flow rate Scale factor
    AS             --               Abstract state defining the refrigerant state
    F_factor       --                interpolation factor between map and actual superheat specific volumes (default should be 0.75)
    ===========   ==============    ========================================================================
    
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
            ('Inlet Entropy','J/kg.K',self.sin_r),
            ('','',''),
            ('Outlet Pressure','Pa',self.Pout_r),
            ('Outlet Temperature','C',self.Tout_r-273.15),
            ('Outlet Enthalpy','J/kg',self.hout_r),
            ('Outlet Entropy','J/kg.K',self.sout_r),
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
            ('Map Mechanical Power','W',self.power_map),
            ('Map Mass flow rate','kg/s',self.mdot_map),
            ('','',''),
            ('Entropy generation','W/K',self.S_gen),
         ]
        
    def Calculate(self):
        #AbstractState
        AS = self.AS
        #Local copies of coefficients and speeds
        P=self.P
        M=self.M
        Speeds = self.Speeds
        
        # calculating pressure ratio
        PR = self.Pout_r / self.Pin_r
        
        # making sure that length of coefficients array and speeds are the same
        if not ((len(P) == len(M)) and (len(P) == len(Speeds))):
            raise AttributeError("please make sure that the length of coefficients array and speeds are the same")
        if not (len(Speeds) == len(set(Speeds))):
            raise AttributeError("please make sure that no speed in speeds array is repeated")
        
        # choose unit system
        if self.Unit_system in ['ip','si','si2']:
            Unit_system = self.Unit_system
        else:
            raise AttributeError("please choose either ip or si for compressor unit system")
        
        # create a universal array for all coefficients and speeds
        coeffs = []
        for (P_coeffs,M_coeffs,Speed) in zip(P,M,Speeds):
            coeffs.append([Speed,P_coeffs,M_coeffs])
        coeffs = np.array(coeffs,dtype=object)

        #Calculate suction superheat and dew temperatures
        AS.update(CP.PQ_INPUTS, self.Pin_r, 1.0)
        self.Tsat_s_K=AS.T() #[K]
        
        AS.update(CP.PQ_INPUTS, self.Pout_r, 1.0)
        self.Tsat_d_K=AS.T() #[K]
        
        AS.update(CP.HmassP_INPUTS,self.hin_r,self.Pin_r)
        self.Tin_r = AS.T()
        self.DT_sh_K=self.Tin_r-self.Tsat_s_K

        if Unit_system == "ip":
        #Convert saturation temperatures in K to F
            Tsat_s = (self.Tsat_s_K - 273.15) * 9/5 + 32
            Tsat_d = (self.Tsat_d_K - 273.15) * 9/5 + 32
        elif Unit_system == "si":
            Tsat_s = self.Tsat_s_K - 273.15
            Tsat_d = self.Tsat_d_K - 273.15
            
        elif Unit_system == "si2":
            Tsat_s = self.Tsat_s_K - 273.15
            Tsat_d = self.Tsat_d_K - 273.15
            
        # to use coefficients of minimum speed if actual speed is lower than it
        if self.act_speed <= min(coeffs[:,0]): 
            P_coeffs, M_coeffs = coeffs[coeffs[:,0] == min(coeffs[:,0]),[1,2]]
            power_map = P_coeffs[0] + P_coeffs[1] * Tsat_s + P_coeffs[2] * Tsat_d + P_coeffs[3] * Tsat_s**2 + P_coeffs[4] * Tsat_s * Tsat_d + P_coeffs[5] * Tsat_d**2 + P_coeffs[6] * Tsat_s**3 + P_coeffs[7] * Tsat_d * Tsat_s**2 + P_coeffs[8] * Tsat_d**2*Tsat_s + P_coeffs[9] * Tsat_d**3
            mdot_map = M_coeffs[0] + M_coeffs[1] * Tsat_s + M_coeffs[2] * Tsat_d + M_coeffs[3] * Tsat_s**2 + M_coeffs[4] * Tsat_s * Tsat_d + M_coeffs[5] * Tsat_d**2 + M_coeffs[6] * Tsat_s**3 + M_coeffs[7] * Tsat_d * Tsat_s**2 + M_coeffs[8] * Tsat_d**2*Tsat_s + M_coeffs[9] * Tsat_d**3
            
            # extrapolating for the actual speed
            power_map = self.act_speed/min(coeffs[:,0])*power_map
            mdot_map = self.act_speed/min(coeffs[:,0])*mdot_map

        # to use coefficients of maximum speed if actual speed is higher than it
        elif self.act_speed >= max(coeffs[:,0]):
            P_coeffs, M_coeffs = coeffs[coeffs[:,0] == max(coeffs[:,0]),[1,2]]
            power_map = P_coeffs[0] + P_coeffs[1] * Tsat_s + P_coeffs[2] * Tsat_d + P_coeffs[3] * Tsat_s**2 + P_coeffs[4] * Tsat_s * Tsat_d + P_coeffs[5] * Tsat_d**2 + P_coeffs[6] * Tsat_s**3 + P_coeffs[7] * Tsat_d * Tsat_s**2 + P_coeffs[8] * Tsat_d**2*Tsat_s + P_coeffs[9] * Tsat_d**3
            mdot_map = M_coeffs[0] + M_coeffs[1] * Tsat_s + M_coeffs[2] * Tsat_d + M_coeffs[3] * Tsat_s**2 + M_coeffs[4] * Tsat_s * Tsat_d + M_coeffs[5] * Tsat_d**2 + M_coeffs[6] * Tsat_s**3 + M_coeffs[7] * Tsat_d * Tsat_s**2 + M_coeffs[8] * Tsat_d**2*Tsat_s + M_coeffs[9] * Tsat_d**3
            
            # extrapolating for the actual speed
            power_map = self.act_speed/max(coeffs[:,0])*power_map
            mdot_map = self.act_speed/max(coeffs[:,0])*mdot_map

        # to interpolate between values matching speeds higher and lower than the actual speed in the map
        else:
            if not (self.act_speed in coeffs[:,0]): # check if the speed is in the map or not
                # first, create a dummy row for the actual speed
                coeffs = np.vstack((coeffs,[self.act_speed,0,0]))

                # sort the array using speeds
                coeffs = coeffs[coeffs[:,0].argsort()]
                
                # getting the index of the actual speed
                index = np.where(coeffs[:,0] == self.act_speed)
                
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
                power_map = np.interp(self.act_speed,SPM_array[:,0],SPM_array[:,1])
                mdot_map = np.interp(self.act_speed,SPM_array[:,0],SPM_array[:,2])
                
            else: # there is a speed in the map matching actual speed
                # get the index of the speed
                index = int(np.where(coeffs[:,0] == self.act_speed)[0])
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
        
        # scale values using passed scale ratios
        self.power_map = power_map
        self.mdot_map = mdot_map
        mdot_map*=self.Vdot_ratio_M
        power_map*=self.Vdot_ratio_P

        # inlet and outlet pressures of compressor
        P1 = self.Pin_r
        P2 = self.Pout_r
        
        # inlet temperature to the compressor
        if self.DT_sh_K >= 1e-3:
            T1_actual = self.Tsat_s_K + self.DT_sh_K
        
        else: # if superheat in the compressor is negative, then assume inlet to compressor is saturated (1e-3 is just a small margin for CoolProp to be able to calculate the value)
            T1_actual = self.Tsat_s_K + 1e-3
        
        # reference superheat used
        if hasattr(self,"SH_Ref"):
            SH_Ref = self.SH_Ref # in k
            
        elif hasattr(self,"Suction_Ref"):
            SH_Ref = self.Suction_Ref - self.Tsat_s_K
        
        if SH_Ref <= 1e-3:
            SH_Ref = 1e-3
        
        T1_map = self.Tsat_s_K + SH_Ref

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
        
        F = self.F_factor # Volumetric efficiency correction factor
        mdot = (1 + F * (v_map / v_actual - 1)) * mdot_map
        
        #volumetric efficiency calculation
        self.eta_v = mdot/(self.Displacement/v_actual*self.act_speed/60)
        
        # getting outlet isentropic values
        AS.update(CP.PSmass_INPUTS, P2, s1_map)
        h2s_map = AS.hmass() #[J/kg]        
        AS.update(CP.PSmass_INPUTS, P2, s1_actual)
        h2s_actual = AS.hmass() #[J/kg]
        
        #Shaft power based on reference superheat calculation from fit overall isentropic efficiency
        power = power_map * (mdot / mdot_map) * ((h2s_actual - h1_actual) / (h2s_map - h1_map))
        h2 = power * (1 - self.fp) / mdot + h1_actual
        
        # calculating actual isentropic efficiency
        self.eta_isen = mdot * (h2s_actual - h1_actual) / power
        
        # getting actual outlet values
        AS.update(CP.HmassP_INPUTS, h2, P2)
        self.Tout_r = AS.T() #[K]
        self.sout_r = AS.smass() #[J/kg-K] 
        
        # saving some values
        self.mdot_r_adj = 1 + F * (v_map / v_actual - 1)
        self.hout_r_s = h2s_actual
        self.vin_r = v_actual
        self.sin_r = s1_actual
        self.hout_r = h2
        self.hin_r = h1_actual
        self.mdot_r = mdot
        self.power_mech = power
        self.power_elec = power / self.Elec_eff
        self.Vdot_pumped = mdot * v_actual
        self.Q_amb = -self.fp * power
        self.PR = PR
        self.S_gen = mdot * (self.sout_r - s1_actual)
        
if __name__=='__main__':
    def fun1():
        Ref = 'R410a'
        Backend = 'HEOS'
        AS = CP.AbstractState(Backend, Ref)
        Tcond = 51.66666666667
        Tevap = 10.55555555556
        AS.update(CP.QT_INPUTS,1.0,Tcond+273.15)
        Pout_r = AS.p()
        AS.update(CP.QT_INPUTS,1.0,Tevap+273.15)
        Pin_r = AS.p()
        DT = 20*5/9
        AS.update(CP.PT_INPUTS,Pin_r,Tevap+DT+273.15)
        hin_r = AS.hmass()
        kwds={
              'name':'Generic',
              'M':[(1.26E+01,-4.97E-03,2.40E-01,7.53E-03,3.50E-03,-3.26E-03,-2.56E-05,-6.20E-08,-1.68E-05,1.13E-05),
                   (3.78E+01,-1.49E-02,7.19E-01,2.26E-02,1.05E-02,-9.78E-03,-7.67E-05,-1.86E-07,-5.03E-05,3.38E-05),
                   (1.76E+02,2.72E+00,-2.12E+00,1.72E-02,-1.12E-02,1.81E-02,6.52E-05,1.08E-05,4.00E-05,-5.54E-05),
                   (2.06E+02,2.68E+00,-1.97E+00,2.48E-02,-3.95E-03,1.52E-02,7.10E-05,3.68E-05,-2.24E-06,-4.24E-05),
                   (2.36E+02,2.64E+00,-1.81E+00,3.24E-02,3.29E-03,1.24E-02,7.67E-05,6.28E-05,-4.45E-05,-2.94E-05),
                   (1.84E+02,4.36E+00,8.08E-01,5.98E-02,-1.88E-02,-7.89E-03,-6.90E-05,8.60E-05,3.94E-05,2.14E-05)],
              'P':[(3.20E+02,1.44E+00,-7.03E+00,-2.18E-02,-2.86E-02,7.40E-02,-5.57E-05,6.40E-05,2.39E-04,-2.05E-04),
                   (9.59E+02,4.33E+00,-2.11E+01,-6.53E-02,-8.57E-02,2.22E-01,-1.67E-04,1.92E-04,7.16E-04,-6.16E-04),
                   (1.59E+03,6.79E+00,-3.49E+01,-2.26E-01,-6.60E-02,3.88E-01,-1.37E-05,1.01E-03,7.41E-04,-1.12E-03),
                   (-1.23E+02,-1.80E+00,1.65E+01,-2.38E-01,8.79E-02,-6.70E-02,-1.56E-05,9.67E-04,2.37E-04,2.66E-04),
                   (-1.84E+03,-1.04E+01,6.79E+01,-2.50E-01,2.42E-01,-5.22E-01,-1.74E-05,9.29E-04,-2.66E-04,1.65E-03),
                   (-3.11E+03,-2.31E+01,1.15E+02,-1.66E-01,4.47E-01,-9.52E-01,-4.18E-04,2.02E-04,-6.70E-04,3.09E-03)],
              'Speeds':[600,1800,3600,4500,5400,7200], # map speeds
              'AS': AS, #Abstract state
              'Ref': Ref, # refrgierant name
              'hin_r':hin_r, # inlet refrigerant enthalpy
              'Pin_r':Pin_r, # inlet refrigerant pressure
              'Pout_r':Pout_r, # outlet refrigernat pressure
              'fp':0.1, #Fraction of electrical power lost as heat to ambient
              'Vdot_ratio_P': 1.0, #Displacement Scale factor
              'Vdot_ratio_M': 1.0, #Displacement Scale factor
              'Displacement':1.502692929782e-5, # displacement volume per revolution
              'SH_Ref':20 * 5 / 9, #in C
              'act_speed': 6200, # operating speed of the compressor
              'Unit_system':'ip', # choose from "ip", "si", "si2"
              'Elec_eff':1.0, # electrical efficiency of the compressor
              'F_factor':0.75, # volumetric efficiency correction factor, used as 0.75 in several sources
              }
        Comp=CompressorAHRIClass(**kwds)
        Comp.Calculate()
        print(*Comp.OutputList(),sep="\n")

    def fun2():
        Ref = 'R410a'
        Backend = 'HEOS'
        AS = CP.AbstractState(Backend, Ref)
        Pout_r = 2.8367e+06
        Pin_r = 9.798e+05
        hin_r = 4.3075e+05
        kwds={
              'name':'Generic',
              'M':[(129.6200839,4.246382916,-0.196,0.055359014,-0.000478,-0.000658732,0.000435873,-4.74E-06,-2.86E-06,-1.00E-05)],
              'P':[(171.4573606,-14.15995084,34.91149717,-0.144,0.132,-0.0398,0.000179894,-0.00228,0.005493878,0.001111111)],
              'Speeds':[2900],
              'AS': AS, #Abstract state
              'Ref': Ref,
              'hin_r':hin_r,
              'Pin_r':Pin_r,
              'Pout_r':Pout_r,
              'fp':0.0, #Fraction of electrical power lost as heat to ambient
              'Vdot_ratio_P': 1.0, #Displacement Scale factor
              'Vdot_ratio_M': 1.0, #Displacement Scale factor
              'Displacement':26e-6,
              'SH_Ref':20 * 5 / 9, #in C
              'act_speed': 2900,
              'Unit_system':'si2',
              'Elec_eff':1.0,
              'F_factor':0, # volumetric efficiency correction factor, used as 0.75 in several sources
              }
        Comp=CompressorAHRIClass(**kwds)
        Comp.Calculate()
        print(*Comp.OutputList(),sep="\n")

    fun2()