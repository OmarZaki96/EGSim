from __future__ import division, print_function, absolute_import
import CoolProp as CP
from scipy.optimize import fsolve
from math import pi, sqrt

class ValuesClass():
    pass

class CapillaryClass():
    """
    Capillary class, used to model a capillary tube
    
    Required Parameters:
    
    ===========    ==========  ========================================================================
    Variable       Units       Description
    ===========    ==========  ========================================================================
    Pin_r          Pa          Refrigerant inlet pressure to the capillary tube
    hin_r          J/kg        Refrigerant inlet enthalpy to the capillary tube
    Pout_r_target  Pa          Refrigerant target outlet pressure from the capillary tube
    L              m           Capillary tube length
    D              m           Capillary inner diameter
    D_liquid       m           Diameter of the tube leading to capillary tube(should be diameter of liquid line)
    Ntubes         --          Number of parallel capillary tubes 
    DT_2phase      K           segment temperature difference discretization in 2phase region
    DP_converged   Pa          pressure convergence criteria
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
            ('Capillary tube length','m',self.L),
            ('Capillary tube inner diameter','m',self.D),
            ('Number of capillary tubes','-',self.Ntubes),
            ('','',''),
            ('','',''),
            ('Refrigernat mass flow rate','kg/s',self.Results.mdot_r),
            ('','',''),
            ('','',''),
            ('Refrigerant inlet pressure','Pa',self.Results.Pin_r),
            ('Refrigerant inlet enthalpy','J/kg',self.Results.hin_r),
            ('Refrigerant inlet temperature','K',self.Results.Tin_r),
            ('Refrigerant inlet entropy','J/K',self.Results.Sin_r),
            ('Refrigerant inlet quality','-',self.Results.xin_r),
            ('','',''),
            ('Refrigernat outlet pressure','Pa',self.Results.Pout_r),
            ('Refrigernat outlet enthalpy','J/kg',self.Results.hout_r),
            ('Refrigernat outlet temperature','K',self.Results.Tout_r),            
            ('Refrigerant outlet entropy','J/K',self.Results.Sout_r),
            ('Refrigerant outlet quality','-',self.Results.xout_r),
            ('','',''),
            ('Capillary tube pressure drop','Pa',self.Results.DP_r),
            ('','',''),
            ('Length of subcooled region','m',self.Results.L_SC),
            ('length of two-phase region','m',self.Results.L_2phase),
            ('','',''),
            ('','',''),
            ('Entropy generation','W/K',self.Results.S_gen),
            ('','',''),
            ('choked?','',self.choked),            
         ]
        
    def calculate_subcool(self,mdot_r,Pin_r,hin_r, L_subcool_required = None):
        '''
        This fucntion is used to calculate the subcooled section. one of the 
        assumption is that this section is adiabatic, so there is no change in
        enthalpy.

        Parameters
        ----------
        mdot_r : float
            flow rate used in subcool section.
        Pin_r : float
            inlet pressure after contraction losses to subcooled section.
        hin_r : float
            inlet enthalpy.
        L_subcool_required : float, optional
            if length is passes, it will solve with this length instead of 
            solving for 2phase outlet. The default is None.

        Returns
        -------
        A tuple of subcool length and outlet pressure.

        '''
        if self.terminate:
            raise
        # get necesssary properties
        AS = self.AS
        D = self.D
        AS.update(CP.HmassP_INPUTS, hin_r, Pin_r)
        mu = AS.viscosity()
        rho = AS.rhomass()
        T = AS.T()
        AS.update(CP.PQ_INPUTS, Pin_r, 0.0)
        Tdew = AS.T()
        AS.update(CP.QT_INPUTS, 0.0, T)
        ST = AS.surface_tension()
        
        # if a not float value is passes, change it to float for faster calculations
        mdot_r = float(mdot_r)
        # calculating flow area
        A_f = pi / 4 * pow(D, 2)
        
        # calculating velocity of refrigerant
        V = mdot_r / (A_f * rho)
        
        # calculating Reynolds Number
        Re = rho * V * D / mu

        # calculating friction factor
        f = 0.23 * pow(Re, -0.216)
        
        # if a certain length to be solved was not sent
        if L_subcool_required == None:
            # finding saturation pressure at the inlet enthalpy assuming constant enthalpy in subcool section
            def objective(P):
                P = float(P)
                AS.update(CP.PQ_INPUTS, P, 0.0)
                hL = AS.hmass()
                AS.update(CP.PQ_INPUTS, P, 1.0)
                hV = AS.hmass()
                x = (hin_r - hL) / (hV - hL)
                return x
            Psat = float(fsolve(objective, Pin_r))
            # finding properties at saturation pressure
            AS.update(CP.PQ_INPUTS, Psat, 0.0)
            v_f = 1 / AS.rhomass()
            AS.update(CP.PQ_INPUTS, Psat, 1.0)
            v_g = 1 / AS.rhomass()
            
            # calculating pressure at the end of subcool region (including metastable region)
            Tcrit = CP.CoolProp.PropsSI("Tcrit",AS.name())
            k_boltz = 1.38064852e-23
            D_dash = sqrt(k_boltz * T / ST) * 1e4
            if (abs(Tdew - T) < 31 * 5/9) and 2.048 < (mdot_r/(pi/4*D**2) / 703) < 7.24:
                Pout = Psat - (0.679 * (v_g / (v_g - v_f)) * pow(Re, 0.914) * pow((Tdew - T) / Tcrit,-0.208) * pow(D / D_dash, -3.18)) * pow(ST, 1.5) / sqrt(k_boltz * T)
            else:
                Pout = Psat
            L_subcool = (2 * (Pin_r - Pout) * D) / (f * rho * pow(V, 2))
        else: # a certain length is passed to be solved
            delta_P = f * L_subcool_required * pow(V, 2) * rho / (2 * D)
            Pout = Pin_r - delta_P
            L_subcool = L_subcool_required
        return L_subcool, Pout
    
    def calculate_2phase(self,mdot_r,Pin_r,hin_r,DT):
        '''
        This function will solve 2phase section. it depends on deviding the 
        length into smaller segments using DT passed parameter, which is the
        change in temperature. this will produce 2 sections, section 1 is the
        inlet of the segment, and section 2 is the outlet of the segment.

        Parameters
        ----------
        mdot_r : float
            mass flow rate to be solved.
        Pin_r : float
            inlet pressure to 2phase region, which is the saturation pressure
            minus the unserpressure caused by metastable region.
        hin_r : float
            inlet enthalpy to 2phase region.
        DT : float
            temperature step for each 2phase segment.

        Raises
        ------
        ValueError
            if entropy is found to decrease instead of increasin, it is a 
            violation of the second law, and the solution is stopped to 
            decrease the mass flow rate.

        Returns
        -------
        A tuple of segment length, outlet pressure, and outlet enthalpy.

        '''
        if self.terminate:
            raise
        # getting necessary properties
        AS = self.AS
        D = self.D
        
        # calculating flow area
        A_f = pi / 4 * pow(D, 2)
        
        # calculating mass flux
        G = mdot_r / A_f

        # finding properties at section 1
        AS.update(CP.PQ_INPUTS, Pin_r, 0.0)
        hL = AS.hmass()
        v_f1 = 1 / AS.rhomass()
        mu_f1 = AS.viscosity()
        AS.update(CP.PQ_INPUTS, Pin_r, 1.0)
        hV = AS.hmass()
        v_g1 = 1 / AS.rhomass()
        mu_g1 = AS.viscosity()
        x1 = (hin_r - hL) / (hV - hL)
        
        # in case inlet quality is in 2phase region
        if 0 <= x1 <= 1.0:
            # getting necessary properties
            AS.update(CP.PQ_INPUTS, Pin_r, 0.0)
            v_f1 = 1 / AS.rhomass()
            mu_f1 = AS.viscosity()
            s_f1 = AS.smass()
            AS.update(CP.PQ_INPUTS, Pin_r, 1.0)
            v_g1 = 1 / AS.rhomass()
            mu_g1 = AS.viscosity()
            s_g1 = AS.smass()
            v_1 = x1 * v_g1 + (1 - x1) * v_f1
            mu_1 = 1 / ((1 - x1) / mu_f1 + x1 / mu_g1)
            s_1 = x1 * s_g1 + (1 - x1) * s_f1
        else: # inlet quality is not in 2phase region due to underpressure in metastable region (which is very rare)
            AS.update(CP.HmassP_INPUTS, hin_r, Pin_r)
            mu_1 = AS.viscosity()
            v_1 = 1 / AS.rhomass()
            s_1 = AS.smass()
        
        # getting inlet temperature
        AS.update(CP.HmassP_INPUTS, hin_r, Pin_r)            
        T1 = AS.T()
        
        # calculating velocity at section 1
        V1 = G * v_1
        
        # calculating properties at section 2
        T2 = T1 - DT
        AS.update(CP.QT_INPUTS, 0.0, T2)
        v_f2 = 1 / AS.rhomass()
        h_f2 = AS.hmass()
        s_f2 = AS.smass()
        mu_f2 = AS.viscosity()
        AS.update(CP.QT_INPUTS, 1.0, T2)
        v_g2 = 1 / AS.rhomass()
        h_g2 = AS.hmass()
        s_g2 = AS.smass()
        mu_g2 = AS.viscosity()
        
        # finding quality at section 2
        def objective(x2):
            x2 = float(x2)
            return (0.5 * pow(G, 2) * pow(v_g2 - v_f2, 2)) * pow(x2, 2) + (pow(G, 2) * v_f2 * (v_g2 - v_f2) + (h_g2 - h_f2)) * x2 + (pow(G, 2) * pow(v_f2, 2) / 2 + h_f2 - hin_r - pow(V1, 2) / 2)
        x2 = float(fsolve(objective, 0.0))
        
        # getting pressure at section 2
        AS.update(CP.QT_INPUTS, x2, T2)
        P2 = AS.p()
        
        # to get necessary properties at section 2
        if x2 > 1.0: # if superheated (unlikely)
            v_2 = v_g2
            mu_2 = mu_g2
            s_2 = s_g2
            h_2 = h_g2
        
        elif x2 < 0.0: # if subcooled (unlikely)
            v_2 = v_f2
            mu_2 = mu_f2
            s_2 = s_f2
            h_2 = h_f2
        
        else: # if 2phase (most likely, this will be the case)
            v_2 = x2 * v_g2 + (1 - x2) * v_f2
            mu_2 = 1 / ((1 - x2) / mu_f2 + x2 / mu_g2)
            s_2 = x2 * s_g2 + (1 - x2) * s_f2
            h_2 = x2 * h_g2 + (1 - x2) * h_f2
        
        # to check for entropy in case it decreased
        if s_2 < s_1:
            raise ValueError('Etropy decreased from '+str(s_1)+" to "+str(s_2))
        
        # finding velocity at section 2
        V2 = G * v_2

        # finding Reynolds numbers
        Re_1 = V1 * D / (mu_1 * v_1)
        Re_2 = V2 * D / (mu_2 * v_2)
        
        # finding mean friction factor
        f1 = 0.23 * pow(Re_1, -0.216)
        f2 = 0.23 * pow(Re_2, -0.216)
        fm = (f1 + f2) / 2
        
        # finding mean specific volume
        v_m = (v_1 + v_2) / 2
        
        # finding mean velocity
        Vm = (V1 + V2) / 2
        
        # finding pressure drop
        delta_P = Pin_r - P2
        
        # finding length
        L_2phase = (delta_P - G * (V2 - V1)) * (2 * v_m * D) / (fm * pow(Vm, 2))
        
        return L_2phase, P2, h_2

    def create_results(self):
        '''
        A function used to create results of the calculation of capillary tube.
        it will create a subclass called Results containing all the necessary 
        values.

        Returns
        -------
        None.

        '''
        self.Results = ValuesClass()
        self.Results.mdot_r = self.mdot_r
        self.Results.hin_r = self.hin_r
        self.Results.hout_r = self.hout_r
        self.Results.Pin_r = self.Pin_r
        self.Results.Pout_r = self.Pout_r
        self.Results.DP_r = self.Pin_r - self.Pout_r
        self.Results.L_SC = self.L_SC
        self.Results.L_2phase = self.L_2phase
        AS = self.AS
        AS.update(CP.HmassP_INPUTS, self.hin_r, self.Pin_r)
        Tin_r = AS.T()
        self.Results.Sin_r = AS.smass()
        self.Results.Tin_r = Tin_r
        AS.update(CP.HmassP_INPUTS, self.hout_r, self.Pout_r)
        Tout_r = AS.T()
        self.Results.Sout_r = AS.smass()        
        self.Results.Tout_r = Tout_r
        AS.update(CP.PQ_INPUTS,self.Pin_r,0.0)
        hL = AS.hmass()
        AS.update(CP.PQ_INPUTS,self.Pin_r,1.0)
        hV = AS.hmass()
        self.Results.xin_r = (self.hin_r - hL) / (hV - hL)
        AS.update(CP.PQ_INPUTS,self.Pout_r,0.0)
        hL = AS.hmass()
        AS.update(CP.PQ_INPUTS,self.Pout_r,1.0)
        hV = AS.hmass()
        self.Results.xout_r = (self.hout_r - hL) / (hV - hL)
        if self.method == "wolf":
            if abs(self.Results.Pout_r - self.Pout_r_target) > self.DP_converged:
                self.choked = True
            else:
                self.choked = False
        else:
            self.choked = True
            
        self.Results.S_gen = self.mdot_r * (self.Results.Sout_r - self.Results.Sin_r)

    def Calculate(self):
        if self.method.lower() == "wolf_physics":
            self.Calculate_wolf_physics()
        elif self.method.lower() == "choi":
            self.Calculate_choi()
        elif self.method.lower() == "wolf":
            self.Calculate_wolf()
        elif self.method.lower() == "wolf_pate":
            self.Calculate_wolf_Pate()
        elif self.method.lower() == "rasti":
            self.Calculate_rasti()

    def Calculate_wolf(self):
        D = self.D
        L = self.L
        AS = self.AS
        Pin_r = self.Pin_r
        hin_r = self.hin_r
        Ref = self.Ref
        
        AS.update(CP.PQ_INPUTS,Pin_r,0.0)
        hf = AS.hmass()        
        AS.update(CP.PQ_INPUTS,Pin_r,1.0)
        hg = AS.hmass()
        hfg = hg - hf
        x = (hin_r - hf) / hfg
        
        if Ref in ["R152A","R152a"] and x < 0:
            # calculating pi group 1 (Geometry group)
            pi_1 = L/D

            # calculating pi group 2 (Vaporization group)
            pi_2 = 1

            # calculating pi group 3
            pi_3 = 1

            # calculating pi group 4
            AS.update(CP.PQ_INPUTS,Pin_r,0.0)
            rho_f = AS.rhomass()
            vis_f = AS.viscosity()
            pi_4 = D**2 * Pin_r * rho_f / vis_f**2
            
            # calculating pi group 5 (subcooling or quality group)
            AS.update(CP.HmassP_INPUTS,hin_r,Pin_r)
            Tin_r = AS.T()
            AS.update(CP.PQ_INPUTS,Pin_r,0.0)
            cp_f = AS.cpmass()
            T_sat = AS.T()
            pi_5 = D**2 * cp_f * (T_sat - Tin_r) * rho_f**2 / vis_f**2
            
            # calculating pi group 6 (Density group)
            pi_6 = 1
            
            # calculating pi group 7 (friction, bubble growth group)
            pi_7 = 1
            
            powers = [1.1037, -0.601, 0.0, 0.0, 0.396, 0.170, 0.0, 0.0]

        elif Ref in ["R410A","R410a"]:
            # calculating pi group 1 (Geometry group)
            pi_1 = L/D

            # calculating pi group 2 (Vaporization group)
            pi_2 = 1

            # calculating pi group 3
            pi_3 = 1

            # calculating pi group 4
            AS.update(CP.PQ_INPUTS,Pin_r,0.0)
            rho_f = AS.rhomass()
            vis_f = AS.viscosity()
            pi_4 = D**2 * Pin_r * rho_f / vis_f**2
            
            # calculating pi group 5 (subcooling or quality group)
            if x < 0:
                AS.update(CP.HmassP_INPUTS,hin_r,Pin_r)
                Tin_r = AS.T()
                AS.update(CP.PQ_INPUTS,Pin_r,0.0)
                cp_f = AS.cpmass()
                T_sat = AS.T()
                pi_5 = D**2 * cp_f * (T_sat - Tin_r) * rho_f**2 / vis_f**2
            else:
                pi_5 = x
            
            # calculating pi group 6 (Density group)
            pi_6 = 1
            
            # calculating pi group 7 (friction, bubble growth group)
            pi_7 = 1
            
            if x < 0:
                powers = [0.3762, -0.520, 0.0, 0.0, 0.423, 0.170, 0.0, 0.0]
            else:
                powers = [3.9123, -0.789, 0.0, 0.0, 0.569, -0.136, 0.0, 0.0]

        elif Ref in ["R134A","R134a"]:
            # calculating pi group 1 (Geometry group)
            pi_1 = L/D

            # calculating pi group 2 (Vaporization group)
            pi_2 = 1

            # calculating pi group 3
            pi_3 = 1

            # calculating pi group 4
            AS.update(CP.PQ_INPUTS,Pin_r,0.0)
            rho_f = AS.rhomass()
            vis_f = AS.viscosity()
            pi_4 = D**2 * Pin_r * rho_f / vis_f**2
            
            # calculating pi group 5 (subcooling or quality group)
            if x < 0:
                AS.update(CP.HmassP_INPUTS,hin_r,Pin_r)
                Tin_r = AS.T()
                AS.update(CP.PQ_INPUTS,Pin_r,0.0)
                cp_f = AS.cpmass()
                T_sat = AS.T()
                pi_5 = D**2 * cp_f * (T_sat - Tin_r) * rho_f**2 / vis_f**2
            else:
                pi_5 = x
            
            # calculating pi group 6 (Density group)
            pi_6 = 1
            
            # calculating pi group 7 (friction, bubble growth group)
            pi_7 = 1
            
            if x < 0:
                powers = [0.0129, -0.387, 0.0, 0.0, 0.492, 0.187, 0.0, 0.0]
            else:
                powers = [0.006975, -0.366, 0.0, 0.0, 0.659, -0.307, 0.0, 0.0]

        elif Ref == "R22":
            # calculating pi group 1 (Geometry group)
            pi_1 = L/D

            # calculating pi group 2 (Vaporization group)
            pi_2 = 1

            # calculating pi group 3
            pi_3 = 1

            # calculating pi group 4
            AS.update(CP.PQ_INPUTS,Pin_r,0.0)
            rho_f = AS.rhomass()
            vis_f = AS.viscosity()
            pi_4 = D**2 * Pin_r * rho_f / vis_f**2
            
            # calculating pi group 5 (subcooling or quality group)
            if x < 0:
                AS.update(CP.HmassP_INPUTS,hin_r,Pin_r)
                Tin_r = AS.T()
                AS.update(CP.PQ_INPUTS,Pin_r,0.0)
                cp_f = AS.cpmass()
                T_sat = AS.T()
                pi_5 = D**2 * cp_f * (T_sat - Tin_r) * rho_f**2 / vis_f**2
            else:
                pi_5 = x
            
            # calculating pi group 6 (Density group)
            pi_6 = 1
            
            # calculating pi group 7 (friction, bubble growth group)
            pi_7 = 1
            
            if x < 0:
                powers = [0.4763, -0.447, 0.0, 0.0, 0.350, 0.206, 0.0, 0.0]
            else:
                powers = [0.0063, -0.339, 0.0, 0.0, 0.600, -0.0449, 0.0, 0.0]

        else:
            # calculating pi group 1 (Geometry group)
            pi_1 = L/D

            # calculating pi group 2 (Vaporization group)
            AS.update(CP.PQ_INPUTS,Pin_r,0.0)
            rho_f = AS.rhomass()
            vis_f = AS.viscosity()
            pi_2 = D**2 * hfg * rho_f**2 / vis_f**2

            # calculating pi group 3
            pi_3 = 1

            # calculating pi group 4
            pi_4 = D**2 * Pin_r * rho_f / vis_f**2
            
            # calculating pi group 5 (subcooling or quality group)
            if x < 0:
                AS.update(CP.HmassP_INPUTS,hin_r,Pin_r)
                Tin_r = AS.T()
                AS.update(CP.PQ_INPUTS,Pin_r,0.0)
                cp_f = AS.cpmass()
                T_sat = AS.T()
                pi_5 = D**2 * cp_f * (T_sat - Tin_r) * rho_f**2 / vis_f**2
            else:
                pi_5 = x
            
            # calculating pi group 6 (Density group)
            AS.update(CP.PQ_INPUTS,Pin_r,1.0)
            rho_g = AS.rhomass()
            pi_6 = rho_f/rho_g
            
            # calculating pi group 7 (friction, bubble growth group)
            AS.update(CP.PQ_INPUTS,Pin_r,1.0)
            vis_g = AS.viscosity()
            pi_7 = (vis_f - vis_g)/vis_g
            
            if x < 0:
                powers = [1.892, -0.484, -0.824, 0.0, 1.339, 0.0187, 0.773, 0.265]
            else:
                powers = [187.27, -0.635, -0.189, 0.0, 0.645, -0.163, -0.213, -0.483]
                
        # calculating pi group 8 (mass flowrate group)        
        pi_8 = powers[0] * pi_1**powers[1] * pi_2**powers[2] * pi_3**powers[3] * pi_4**powers[4] * pi_5**powers[5] * pi_6**powers[6] * pi_7**powers[7]
        mdot_r = pi_8 * D * vis_f
            
        
        self.Pout_r = self.Pout_r_target
        self.hout_r = self.hin_r
        self.L_SC = None
        self.L_2phase = None
        self.mdot_r = mdot_r * self.Ntubes
        
        self.create_results()
        
    def Calculate_wolf_Pate(self):
        D = self.D
        L = self.L
        AS = self.AS
        Pin_r = self.Pin_r
        Pout_r = self.Pout_r_target
        hin_r = self.hin_r
        Ref = self.Ref

        AS.update(CP.HmassP_INPUTS,hin_r,Pin_r)
        Tin_r = AS.T()
        
        AS.update(CP.PQ_INPUTS,Pin_r,0.0)
        T_sat = AS.T()
        cp_f = AS.cpmass()
        h_f = AS.hmass()
        vis_f = AS.viscosity()
        rho_f = AS.rhomass()

        AS.update(CP.PQ_INPUTS,Pin_r,1.0)
        vis_g = AS.viscosity()
        h_g = AS.hmass()

        xin = (hin_r - h_f) / (h_g - h_f)
        
        L_hx = 60 * 25.4/1000
        
        if Ref in ["R134a","R134A"]:
            if xin < 0:
                pi_1 = L/D
                
                pi_3 = L_hx / D
                
                pi_5 = (Pin_r * D**2 * rho_f) / vis_f**2
    
                pi_6 = (Pout_r * D**2 * rho_f) / vis_f**2
        
                pi_7 = D**2 * cp_f * (T_sat - Tin_r) * rho_f**2 / vis_f**2
    
                if hasattr(self,"STD_sh"):
                    SH = self.STD_sh
                else:
                    SH = 5.0
                    
                pi_8 = D**2 * cp_f * SH * rho_f**2 / vis_f**2
                                
                pi_9 = 0.7028 * pi_1**(-0.576) * pi_3**(0.09302) * pi_5**(0.6273) * pi_6**(-0.08078) * pi_7**(0.0434) * pi_8**(-0.01631)
                
            else:
                pi_1 = L/D
                
                pi_5 = (Pin_r * D**2 * rho_f) / vis_f**2
    
                pi_6 = (Pout_r * D**2 * rho_f) / vis_f**2
        
                pi_7 = (1 - xin)
                
                pi_8 = D**2 * cp_f * 5.0 * rho_f**2 / vis_f**2
                
                pi_9 = 14.15 * pi_1**(-0.3256) * pi_5**(0.7244) * pi_6**(-0.2749) * pi_7**(12.35) * pi_8**(-0.05601)
                
        elif Ref == "R22":
            if xin < 0:
                pi_1 = L/D
                
                pi_3 = L_hx / D
                
                pi_5 = (Pin_r * D**2 * rho_f) / vis_f**2
    
                pi_6 = (Pout_r * D**2 * rho_f) / vis_f**2
        
                pi_7 = D**2 * cp_f * (T_sat - Tin_r) * rho_f**2 / vis_f**2
    
                if hasattr(self,"STD_sh"):
                    SH = self.STD_sh
                else:
                    SH = 5.0
                    
                pi_8 = D**2 * cp_f * SH * rho_f**2 / vis_f**2
                                
                pi_9 = 0.07851 * pi_1**(-0.5060) * pi_3**(0.0611) * pi_5**(0.7443) * pi_6**(-0.1548) * pi_7**(0.08693) * pi_8**(-0.03691)

            else:
                pi_1 = L/D
                
                pi_5 = (Pin_r * D**2 * rho_f) / vis_f**2
    
                pi_6 = (Pout_r * D**2 * rho_f) / vis_f**2
        
                pi_7 = (1 - xin)
                
                pi_8 = D**2 * cp_f * 5.0 * rho_f**2 / vis_f**2
                
                pi_9 = 0.001356 * pi_1**(-0.2367) * pi_5**(1.263) * pi_6**(-0.387) * pi_7**(4.006) * pi_8**(-0.1472)

        elif Ref == "R410A":
            if xin < 0:
                pi_1 = L/D
                
                pi_3 = L_hx / D
                
                pi_5 = (Pin_r * D**2 * rho_f) / vis_f**2
    
                pi_6 = (Pout_r * D**2 * rho_f) / vis_f**2
        
                pi_7 = D**2 * cp_f * (T_sat - Tin_r) * rho_f**2 / vis_f**2
    
                if hasattr(self,"STD_sh"):
                    SH = self.STD_sh
                else:
                    SH = 5.0
                    
                pi_8 = D**2 * cp_f * SH * rho_f**2 / vis_f**2
                                
                pi_9 = 0.5785 * pi_1**(-0.4473) * pi_3**(0.04425) * pi_5**(0.5989) * pi_6**(-0.06415) * pi_7**(0.0637) * pi_8**(-0.04557)
                
            else:
                pi_1 = L/D
                
                pi_5 = (Pin_r * D**2 * rho_f) / vis_f**2
    
                pi_6 = (Pout_r * D**2 * rho_f) / vis_f**2
        
                pi_7 = (1 - xin)
                
                pi_8 = D**2 * cp_f * 5.0 * rho_f**2 / vis_f**2
                
                pi_9 = 0.1606 * pi_1**(-0.3654) * pi_5**(0.8483) * pi_6**(-0.1743) * pi_7**(1.433) * pi_8**(-0.08998)

        elif Ref in ["R600A","R600a"]:
            if xin < 0:
                pi_1 = L/D
                
                pi_3 = L_hx / D
                
                pi_5 = (Pin_r * D**2 * rho_f) / vis_f**2
    
                pi_6 = (Pout_r * D**2 * rho_f) / vis_f**2
        
                pi_7 = D**2 * cp_f * (T_sat - Tin_r) * rho_f**2 / vis_f**2
    
                if hasattr(self,"STD_sh"):
                    SH = self.STD_sh
                else:
                    SH = 5.0
                    
                pi_8 = D**2 * cp_f * SH * rho_f**2 / vis_f**2
                                
                pi_9 = 0.03069 * pi_1**(-0.37) * pi_3**(0.1187) * pi_5**(0.6818) * pi_6**(-0.0267) * pi_7**(0.05038) * pi_8**(-0.06939)
                
            else:
                pi_1 = L/D
                
                pi_5 = (Pin_r * D**2 * rho_f) / vis_f**2
    
                pi_6 = (Pout_r * D**2 * rho_f) / vis_f**2
        
                pi_7 = (1 - xin)
                
                pi_8 = D**2 * cp_f * 5.0 * rho_f**2 / vis_f**2
                
                pi_9 = 0.3412 * pi_1**(-0.2449) * pi_5**(1.042) * pi_6**(-0.4307) * pi_7**(6.487) * pi_8**(-0.1052)

        else:
            if xin < 0:
                pi_1 = L/D
                
                pi_3 = L_hx / D
                
                pi_5 = (Pin_r * D**2 * rho_f) / vis_f**2
    
                pi_6 = (Pout_r * D**2 * rho_f) / vis_f**2
        
                pi_7 = D**2 * cp_f * (T_sat - Tin_r) * rho_f**2 / vis_f**2
    
                if hasattr(self,"STD_sh"):
                    SH = self.STD_sh
                else:
                    SH = 5.0
                    
                pi_8 = D**2 * cp_f * SH * rho_f**2 / vis_f**2
                
                pi_11 = (vis_f - vis_g) / vis_f

                pi_9 = 0.07602 * pi_1**(-0.4583) * pi_3**(0.07751) * pi_5**(0.7342) * pi_6**(-0.1204) * pi_7**(0.03774) * pi_8**(-0.04085) * pi_11**(0.1768)

            else:
                pi_1 = L/D
                
                pi_5 = (Pin_r * D**2 * rho_f) / vis_f**2
    
                pi_6 = (Pout_r * D**2 * rho_f) / vis_f**2
        
                pi_7 = (1 - xin)
                
                pi_8 = D**2 * cp_f * 5.0 * rho_f**2 / vis_f**2
                
                pi_9 = 0.0196 * pi_1**(-0.3127) * pi_5**(1.059) * pi_6**(-0.3662) * pi_7**(4.759) * pi_8**(-0.04965)
            
        mdot_r = pi_9 * D * vis_f

        self.Pout_r = self.Pout_r_target
        self.hout_r = self.hin_r
        self.L_SC = None
        self.L_2phase = None
        self.mdot_r = mdot_r * self.Ntubes
        
        self.create_results()

    def Calculate_choi(self):
        D = self.D
        L = self.L
        AS = self.AS
        Pin_r = self.Pin_r
        hin_r = self.hin_r
        
        # calculating pi group 1 (pressure group)
        AS.update(CP.HmassP_INPUTS,hin_r,Pin_r)
        Tin_r = AS.T()
        P_c = AS.p_critical()
        AS.update(CP.QT_INPUTS,0.0,Tin_r)
        P_sat = AS.p()
        pi_1 = (Pin_r - P_sat)/P_c
        
        # calculating pi group 2 (subcooling group)
        AS.update(CP.PQ_INPUTS,Pin_r,0.0)
        T_sat = AS.T()
        T_c = AS.T_critical()
        pi_2 = (T_sat - Tin_r)/T_c
        
        # calculating pi group 3 (Geometry group)
        pi_3 = L/D
        
        # calculating pi group 4 (Density group)
        AS.update(CP.PQ_INPUTS,Pin_r,0.0)
        rho_f = AS.rhomass()
        AS.update(CP.PQ_INPUTS,Pin_r,1.0)
        rho_g = AS.rhomass()
        pi_4 = rho_f/rho_g
        
        # calculating pi group 5 (friction, bubble growth group)
        AS.update(CP.PQ_INPUTS,Pin_r,0.0)
        vis_f = AS.viscosity()
        AS.update(CP.PQ_INPUTS,Pin_r,1.0)
        vis_g = AS.viscosity()
        pi_5 = (vis_f - vis_g)/vis_g
        
        # calculating pi group 6 (friction, bubble growth group)
        AS.update(CP.PQ_INPUTS,Pin_r,0.0)
        segma = AS.surface_tension()
        pi_6 = segma / (D * Pin_r)
        
        # calculating pi group 7 (Vaporization group)
        AS.update(CP.PQ_INPUTS,Pin_r,0.0)
        hf = AS.hmass()        
        AS.update(CP.PQ_INPUTS,Pin_r,1.0)
        hg = AS.hmass()
        hfg = hg - hf
        pi_7 = rho_f * hfg / P_sat
        
        # calculating pi group 8 (mass flowrate group)        
        pi_8 = 1.313 * 10**-3 * pi_1**(-0.087) * pi_2**(0.188) * pi_3**(-0.412) * pi_4**(-0.834) * pi_5**(0.199) * pi_6**(-0.368) * pi_7**(0.992)
        mdot_r = pi_8 * D**2 * sqrt(rho_f * Pin_r)
        
        self.Pout_r = self.Pout_r_target
        self.hout_r = self.hin_r
        self.L_SC = None
        self.L_2phase = None
        self.mdot_r = mdot_r * self.Ntubes
        
        self.create_results()

    def Calculate_rasti(self):
        D = self.D
        L = self.L
        AS = self.AS
        Pin_r = self.Pin_r
        hin_r = self.hin_r

        AS.update(CP.PQ_INPUTS,Pin_r,0.0)
        hf = AS.hmass()        
        vis_f = AS.viscosity()
        rho_f = AS.rhomass()

        AS.update(CP.PQ_INPUTS,Pin_r,1.0)
        rho_g = AS.rhomass()
        hg = AS.hmass()        

        hfg = hg - hf
        
        pi_1 = L/D
        
        pi_2 = D**2*hfg*rho_f**2/vis_f**2
        
        pi_4 = D**2*Pin_r*rho_f/vis_f**2
        
        pi_5 = 1 + (hin_r - hf) / hfg
        
        pi_6 = rho_f/rho_g
        
        if hin_r <= hf: #subcooled inlet
            c5 = 0.6436
        else: # two-phase inlet
            c5 = -1.971
                        
        # calculating pi group 8 (mass flowrate group)        
        pi_8 = 150.26 * pi_1**(-0.5708) * pi_2**(-1.4636) * pi_4**(1.953) * pi_5**(c5) * pi_6**(1.4181)
        mdot_r = pi_8 * D * vis_f
        
        self.Pout_r = self.Pout_r_target
        self.hout_r = self.hin_r
        self.L_SC = None
        self.L_2phase = None
        self.mdot_r = mdot_r * self.Ntubes
        
        self.create_results()
        
    def Calculate_wolf_physics(self):
        '''
        This is the main calculation function.

        Raises
        ------
        ValueError
            In case entrance pressure drop to the capillary tube is very large
            that it produced a negative value of pressure to the capillary tube
            which is very much unlikely to happen.

        Returns
        -------
        Nothing.

        '''
        # getting inputs
        D_liquid = self.D_liquid
        D = self.D
        L = self.L
        AS = self.AS
        Pin_r = self.Pin_r
        hin_r = self.hin_r
        
        # calculating inlet quality and properties
        AS.update(CP.PQ_INPUTS, Pin_r, 0.0)
        hL = AS.hmass()
        v_f = 1 / AS.rhomass()
        AS.update(CP.PQ_INPUTS, Pin_r, 1.0)
        hV = AS.hmass()
        v_g = 1 / AS.rhomass()
        x = (hin_r - hL) / (hV - hL)
        if x < 0:# for the following correlatons, subcooled inlet is considered with x_in = 0
            x_in = 0
        else:
            x_in = x
        
        # calculating enterance pressure drop
        segma = pow(D_liquid, 2) / pow(D, 2) # contraction ratio
        Cc = 0.544 / pow(segma, 3) - 0.242 / pow(segma, 2) + 0.111 / segma + 0.585
        delta_P = (pow(1 / Cc - 1, 2) + (1 - 1 / pow(segma, 2))) * (1 + v_g / v_f * x_in)
        
        # inlet pressure to the capillary tube
        Pin_capillary = Pin_r - delta_P
        
        if Pin_capillary <= 0:
            raise ValueError("entrance pressure drop to capillary tube is very large")
        
        # getting properties at the inlet of capillary tube
        AS.update(CP.PQ_INPUTS, Pin_capillary, 0.0)
        hL = AS.hmass()
        v_f = 1 / AS.rhomass()
        AS.update(CP.PQ_INPUTS, Pin_capillary, 1.0)
        hV = AS.hmass()
        v_g = 1 / AS.rhomass()
        x = (hin_r - hL) / (hV - hL)
        if x < 0: # if inlet is subcooled
            subcool = True
        else:
            subcool = False
        
        # the function is used to solve the capillary tube using the passed 
        # mass flow rate, and will return the outlet pressure, outlet enthalpy, 
        # length of subcooled region and length of 2phase region
        def objective1(mdot_r):
            # convert passed flow rate to float to increase calculation speed
            mdot_r = float(mdot_r)
            if subcool: # subcooled exist
                L_SC, Pout = self.calculate_subcool(mdot_r, Pin_capillary, hin_r)
                if L_SC > L: # in case length of subcooled is larger than capillary tube length, then solve subcooled region with capillary tube length
                    L_SC, Pout = self.calculate_subcool(mdot_r, Pin_capillary, hin_r,L)
                    self.hout_r = self.hin_r
                    return Pout, hin_r, L_SC, 0
            else: # no subcooled region
                L_SC = 0
                Pout = Pin_capillary
            # available length for 2phase
            L_2phase_max = L - L_SC
            # calculated length of 2phase, with initial value of zero
            L_calculated = 0
            finished = False
            Pin_2phase = Pout
            hin_2phase = hin_r # assuming constant enthalpy in subcooled region
            while not finished:
                # solve to geth length of the segment, outlet pressure and enthalpy
                L_segment, P_segment, h_segment = self.calculate_2phase(mdot_r,Pin_2phase,hin_2phase,self.DT_2phase)
                if L_calculated + L_segment > L_2phase_max: # check if total solved length exceeded the available 2phase length
                    # we need to find DT which will give L_segment that will produce the necessary total length equal to the available length for 2phase
                    def objective2(DT):
                        DT = float(DT)
                        L_segment, P_segment, h_segment = self.calculate_2phase(mdot_r,Pin_2phase,hin_2phase,DT)
                        return L_2phase_max - (L_calculated + L_segment)
                    DT = float(fsolve(objective2, 0.05))
                    L_segment, P_segment, h_segment = self.calculate_2phase(mdot_r,Pin_2phase,hin_2phase,DT)
                    Pout_2phase = P_segment
                    hout_2phase = h_segment
                    finished = True
                else: # we didn't finish calculation yet, so we will pass the values from the previous segment
                    L_calculated += L_segment
                    Pin_2phase = P_segment
                    hin_2phase = h_segment
            return Pout_2phase, hout_2phase, L_SC, L_calculated
            
        def objective3(mdot_r):
            # a wrapper to return negative values in case we violated the second law
            try:
                return objective1(mdot_r)
            except ValueError:
                return [-1,-1,-1,-1]
        
        # guessing which decimal will give negative value (max mdot_r)
        once_atleast = False # to make sure we got at least one positive value before we got the negative value
        for i in reversed(range(-2,8)):
            k = objective3(1*pow(10,-i))[0] - self.Pout_r_target
            
            if k < 0 and once_atleast: # we exceeded the required value
                z = i + 1
                break
            else:
                if k > 0:
                    once_atleast = True
        
        # in case we couldn't find a decimal
        if not ('z' in locals()):
            raise ValueError("Could find intial guess for mass flow rate of capillary tube")
        
        # guessing the number in that decimal value
        # we will try 5 first, to devide the guess either between 1 and 5 or 6 and 9
        a1 = objective3(5*pow(10,-z))[0] - self.Pout_r_target
        if a1 < 0:
            b1 = 1
            b2 = 6
        else:
            b1 = 6
            b2 = 10
        for i in range(b1,b2):
            k = objective3(i*pow(10,-z))[0] - self.Pout_r_target
            if k < 0: # we exceeded the required value
                y = i - 1
                break
            else:
                if i == 9:
                    y = 9
                    
        # in case we couldn't find a number in the decimal
        if not ('y' in locals()):
            raise ValueError("Could find intial guess for mass flow rate of capillary tube")        
        
        # this will start to construct the required mass flow rate
        target = y * pow(10, -z)
        
        Converged = False
        for i in range(z + 1,15): # to try up to decimal 15
            a1 = objective3(5 * pow(10, -i) + target)[0] - self.Pout_r_target
            if a1 < 0:
                b1 = 0
                b2 = 6
            else:
                b1 = 6
                b2 = 11
            for j in range(b1,b2):
                old_k = k
                k = objective3(j * pow(10, -i) + target)[0] - self.Pout_r_target
                if abs(k - old_k) < self.DP_converged: # change is very small, we converged
                    Converged = True
                    break # from smaller loop
                if k < 0:
                    break
            if Converged:
                break # from major loop
            if j == 0:
                pass
            elif j == 10:
                target += 9 * pow(10, -i)
            else:
                target += (j - 1) * pow(10, -i)
        
        # pass some values
        mdot_r = target
        Pout, hout, L_SC, L_2phase = objective3(mdot_r)
        self.Pout_r = Pout
        self.hout_r = hout
        self.L_SC = L_SC
        self.L_2phase = L_2phase
        self.mdot_r = mdot_r * self.Ntubes
        
        # create results subclass
        self.create_results()
            
if __name__=='__main__':
    def f1():        
        Ref = "R32"
        AS = CP.AbstractState("REFPROP",Ref)
                
        Tsat_cond = 46.86
        Tsat_evap = 7.534
        Subcooling = 5.1
        
        AS.update(CP.QT_INPUTS,0.0,Tsat_cond+273.15)
        Pin_r = AS.p()
        AS.update(CP.QT_INPUTS,0.0,Tsat_evap+273.15)
        Pout_target = AS.p()
        AS.update(CP.PT_INPUTS,Pin_r,Tsat_cond-Subcooling+273.15)
        hin_r = AS.hmass()
        
        kwds={
              'name': "Generic Capillary",
              'AS': AS, # Abstract state
              'Ref': Ref, # refrigerant name
              'Pin_r': Pin_r, # inlet refrigerant pressure
              'hin_r': hin_r, # inlet refrigerant enthalpy
              'Pout_r_target': Pout_target, # target outlet refrigerant pressure
              'L': 1.1334, # capillary tube length
              'D': 0.06*25.4/1000, # capillary tube internal diameter
              'D_liquid': 0.01, # inlet diameter before capillary (used only in 1 correlation)
              'Ntubes': 1, # number of capillary parallel tubes
              'DT_2phase':0.5, # temperature discretization in C
              'DP_converged':1, # pressure convergence tolerance in Pa
              'method':"rasti", # correlation to be used
              }
        
        Capillary = CapillaryClass(**kwds)
        Capillary.Calculate()
        print(*Capillary.OutputList(),sep="\n")
    f1()