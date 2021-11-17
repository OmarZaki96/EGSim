from __future__ import division, print_function, absolute_import
from math import pi, log, sqrt, exp, tanh, atan
from CoolProp.CoolProp import HAPropsSI, cair_sat
import psychrolib as pl

pl.SetUnitSystem(pl.SI)

class ValuesClass():
    pass

class FinsClass():
    def __init__(self):
        self.imposed_dry = False
        self.imposed_wet = False
        self.geometry_calculated_dry = False
        self.geometry_calculated_wet = False
    
    def geometry(self):
        # to calculate geometry based on fin type
        if self.FinType == 'Plain':
            self.geometry_Plain()
        elif self.FinType == 'Wavy':
            self.geometry_Wavy()
        elif self.FinType == 'WavyLouvered':
            self.geometry_WavyLouvered()
        elif self.FinType == 'Slit':
            self.geometry_Slit()
        elif self.FinType == 'Louvered':
            self.geometry_Louvered()
        else:
            raise
            
        self.geometry_calculated = True
    
    # which correlation will be used (not active when imposing function is used)
    def update(self,Tin,Tout,Win,Wout,Pin,Pout,mdot_ha,fins_geometry,Wet,Accurate=True,water_cond=None,mu_f=None):
        self.Fins_geometry = fins_geometry
        self.Accurate = Accurate
        self.Tin = Tin
        self.Tout = Tout
        self.Win = Win
        self.Wout = Wout
        self.Pin = Pin
        self.Pout = Pout
        self.mdot_ha = mdot_ha
        self.water_cond = water_cond
        self.mu_f = mu_f
        
        # choosing correlation by setting number
        if self.Fins_geometry.FinType == 'Plain':
            if Wet:
                if not self.imposed_wet:
                    # options: 1, 5
                    self.corr_wet = 5
            elif not Wet:
                if not self.imposed_dry:
                    # options: 1, 2 ,8
                    self.corr_dry = 2

        elif self.Fins_geometry.FinType == 'Wavy':
            if Wet:
                if not self.imposed_wet:
                    # options: 4, 6
                    self.corr_wet = 6
            elif not Wet:
                if not self.imposed_dry:
                    # options: 6, 10
                    self.corr_dry = 6

        elif self.Fins_geometry.FinType == 'WavyLouvered':
            if Wet:
                if not self.imposed_wet:
                    # options: None
                    self.corr_wet = 4
            elif not Wet:
                if not self.imposed_dry:
                    # options: 7, 9
                    self.corr_dry = 7
            
        elif self.Fins_geometry.FinType == 'Slit':
            if Wet:
                if not self.imposed_wet:
                    # options: 3
                    self.corr_wet = 3
            elif not Wet:
                if not self.imposed_dry:
                    # options: 4, 5
                    self.corr_dry = 5

        elif self.Fins_geometry.FinType == 'Louvered':
            if Wet:
                if not self.imposed_wet:
                    # options: 2
                    self.corr_wet = 2
            elif not Wet:
                if not self.imposed_dry:
                    # options: 3
                    self.corr_dry = 3
        else:
            raise
    
    # imposing a correlation functions
    def impose_wet(self,num):
        self.imposed_wet = True
        self.corr_wet = num
    
    def remove_impose_wet(self):
        self.imposed_wet = False

    def impose_dry(self,num):
        self.imposed_dry = True
        self.corr_dry = num
        
    def remove_impose_dry(self):
        self.imposed_dry = False
    
    # calculating h and DP
    def calculate_dry(self):
        if self.corr_dry == 1:
            ''' using Abumadi 1998 for j and f for plain fins'''
            if self.geometry_calculated_dry == False:
                self.Abumadi1998_Plane_dry_geometry()
                self.geometry_calculated_dry = True
            h_a, DP = self.Abumadi1998_Plane_dry(self.Tin, self.Tout, self.Win,
                                                 self.Wout, self.Pin, self.Pout,
                                                 self.mdot_ha)
            return h_a, DP
        
        elif self.corr_dry == 2:
            ''' using Wang 2000 for j and f for plain fins'''
            if self.geometry_calculated_dry == False:
                self.Wang2000_Plain_Dry_geometry()
                self.geometry_calculated_dry = True
            h_a, DP = self.Wang2000_Plain_Dry(self.Tin, self.Tout, self.Win,
                                                 self.Wout, self.Pin, self.Pout,
                                                 self.mdot_ha)
            return h_a, DP

        elif self.corr_dry == 3:
            ''' using Wang 1999 for j and f for louvered fins'''
            if self.geometry_calculated_dry == False:
                self.Wang1999_Louvered_Dry_geometry()
                self.geometry_calculated_dry = True
            h_a, DP = self.Wang1999_Louvered_Dry(self.Tin, self.Tout, self.Win,
                                                 self.Wout, self.Pin, self.Pout,
                                                 self.mdot_ha)
            return h_a, DP

        elif self.corr_dry == 4:
            ''' using Wang 2001 for j and f for Slit fins'''
            if self.geometry_calculated_dry == False:
                self.Wang2001_Slit_Dry_geometry()
                self.geometry_calculated_dry = True
            h_a, DP = self.Wang2001_Slit_Dry(self.Tin, self.Tout, self.Win,
                                                 self.Wout, self.Pin, self.Pout,
                                                 self.mdot_ha)
            return h_a, DP

        elif self.corr_dry == 5:
            ''' using Kim 2000 for j and f for Slit fins'''
            if self.geometry_calculated_dry == False:
                self.Kim2000_Slit_Dry_geometry()
                self.geometry_calculated_dry = True
            h_a, DP = self.Kim2000_Slit_Dry(self.Tin, self.Tout, self.Win,
                                                 self.Wout, self.Pin, self.Pout,
                                                 self.mdot_ha)
            return h_a, DP

        elif self.corr_dry == 6:
            ''' using Wang 1997 for j and f for Wavy fins'''
            if self.geometry_calculated_dry == False:
                self.Wang1997_Wavy_Dry_geometry()
                self.geometry_calculated_dry = True
            h_a, DP = self.Wang1997_Wavy_Dry(self.Tin, self.Tout, self.Win,
                                                 self.Wout, self.Pin, self.Pout,
                                                 self.mdot_ha)
            return h_a, DP

        elif self.corr_dry == 7:
            ''' using Wang 1998 for j and f for WavyLouvered fins'''
            if self.geometry_calculated_dry == False:
                self.Wang1998_WavyLouvered_Dry_geometry()
                self.geometry_calculated_dry = True
            h_a, DP = self.Wang1998_WavyLouvered_Dry(self.Tin, self.Tout, self.Win,
                                                 self.Wout, self.Pin, self.Pout,
                                                 self.mdot_ha)
            return h_a, DP

        elif self.corr_dry == 8:
            ''' using Wang 1996 for j and f for Plain fins'''
            if self.geometry_calculated_dry == False:
                self.Wang1996_Plain_Dry_geometry()
                self.geometry_calculated_dry = True
            h_a, DP = self.Wang1996_Plain_Dry(self.Tin, self.Tout, self.Win,
                                                 self.Wout, self.Pin, self.Pout,
                                                 self.mdot_ha)
            return h_a, DP

        elif self.corr_dry == 9:
            ''' using Wang 1996 for j and f for WavyLouvered fins'''
            if self.geometry_calculated_dry == False:
                self.Wang1996_WavyLouvered_Dry_geometry()
                self.geometry_calculated_dry = True
            h_a, DP = self.Wang1996_WavyLouvered_Dry(self.Tin, self.Tout, self.Win,
                                                 self.Wout, self.Pin, self.Pout,
                                                 self.mdot_ha)
            return h_a, DP

        elif self.corr_dry == 10:
            ''' using Kim 1997 for j and f for Wavy fins'''
            if self.geometry_calculated_dry == False:
                self.Kim1997_Wavy_Dry_geometry()
                self.geometry_calculated_dry = True
            h_a, DP = self.Kim1997_Wavy_Dry(self.Tin, self.Tout, self.Win,
                                                 self.Wout, self.Pin, self.Pout,
                                                 self.mdot_ha)
            return h_a, DP
        
        else:
            raise
            
    def calculate_wet(self):
        if self.corr_wet == 1:
            ''' using Wang 1997 for j and f for plain fins'''
            if self.geometry_calculated_wet == False:
                self.Wang1997_Plain_Wet_geometry()
                self.geometry_calculated_wet = True
            h_a, DP = self.Wang1997_Plain_Wet(self.Tin, self.Tout, self.Win,
                                                 self.Wout, self.Pin, self.Pout,
                                                 self.mdot_ha)
            return h_a, DP

        elif self.corr_wet == 2:
            ''' using Wang 2000 for j and f for louvered fins'''
            if self.geometry_calculated_wet == False:
                self.Wang2000_Louvered_Wet_geometry()
                self.geometry_calculated_wet = True
            h_a, DP = self.Wang2000_Louvered_Wet(self.Tin, self.Tout, self.Win,
                                                 self.Wout, self.Pin, self.Pout,
                                                 self.mdot_ha, self.water_cond,
                                                 self.mu_f)
            return h_a, DP

        elif self.corr_wet == 3:
            ''' using Kim 2000 for j and f for Slit fins'''
            if self.geometry_calculated_wet == False:
                self.Kim2000_Slit_Wet_geometry()
                self.geometry_calculated_wet = True
            h_a, DP = self.Kim2000_Slit_Wet(self.Tin, self.Tout, self.Win,
                                                 self.Wout, self.Pin, self.Pout,
                                                 self.mdot_ha)
            return h_a, DP

        elif self.corr_wet == 4:
            ''' using Wang 1999 for j and f for Wavy fins'''
            if self.geometry_calculated_wet == False:
                self.Wang1999_Wavy_Wet_geometry()
                self.geometry_calculated_wet = True
            h_a, DP = self.Wang1999_Wavy_Wet(self.Tin, self.Tout, self.Win,
                                                 self.Wout, self.Pin, self.Pout,
                                                 self.mdot_ha, self.water_cond,
                                                 self.mu_f)
            return h_a, DP

        elif self.corr_wet == 5:
            ''' using Wang 2000 for j and f for Plain fins'''
            if self.geometry_calculated_wet == False:
                self.Wang2000_Plain_Wet_geometry()
                self.geometry_calculated_wet = True
            h_a, DP = self.Wang2000_Plain_Wet(self.Tin, self.Tout, self.Win,
                                                 self.Wout, self.Pin, self.Pout,
                                                 self.mdot_ha, self.water_cond,
                                                 self.mu_f)
            return h_a, DP

        elif self.corr_wet == 6:
            ''' using Wang 2002 for j and f for Wavy fins'''
            if self.geometry_calculated_wet == False:
                self.Wang2002_Wavy_Wet_geometry()
                self.geometry_calculated_wet = True
            h_a, DP = self.Wang2002_Wavy_Wet(self.Tin, self.Tout, self.Win,
                                                 self.Wout, self.Pin, self.Pout,
                                                 self.mdot_ha, self.water_cond,
                                                 self.mu_f)
            return h_a, DP
        
        elif self.corr_wet == 7:
            ''' using (((dry))) Wang 2001 for j and f for Slit fins'''
            if self.geometry_calculated_dry == False:
                self.Wang2001_Slit_Dry_geometry()
                self.geometry_calculated_dry = True
            h_a, DP = self.Wang2001_Slit_Dry(self.Tin, self.Tout, self.Win,
                                                 self.Wout, self.Pin, self.Pout,
                                                 self.mdot_ha)
            return h_a, DP

        else:
            raise
    
    # calculating efficiency
    def calculate_eff_wet(self, Tw_o, k_fin, h_a):
        bw_m = cair_sat(Tw_o) * 1000
        delta_f = self.Fins_geometry.t      #Fin thickness
        h_eff = h_a * bw_m / self.cp_da
        m = sqrt(2 * h_a / (k_fin * delta_f))
        eta_f = tanh(m * self.ri_eff * self.phi_eff) / (m * self.ri_eff * self.phi_eff)
        eta_o_wet = 1 - self.Af_Ao_eff * (1 - eta_f)
        return bw_m, eta_o_wet
    
    def calculate_eff_dry(self, k_fin, h_a):
        delta_f = self.Fins_geometry.t      #Fin thickness
        m = sqrt(2 * h_a / (k_fin * delta_f))
        eta_f = tanh(m * self.ri_eff * self.phi_eff) / (m * self.ri_eff * self.phi_eff)
        eta_o_dry = 1 - self.Af_Ao_eff * (1 - eta_f)
        
        return eta_o_dry
    
    # air properties calculation
    def calculate_air_props(self, Tin, Tout, Win, Wout, Pin, Pout):        
        # Calculate properties at mean temperature
        Wmean = (Win + Wout) / 2
        Tmean = (Tin + Tout) / 2
        Pmean = (Pin + Pout) / 2
        
        if self.Accurate == True:
            v_da=HAPropsSI('V', 'T', Tmean, 'P', Pmean, 'W', Wmean)
            h_da=HAPropsSI('H', 'T', Tmean, 'P', Pmean, 'W', Wmean) #[J/kg]
        else:
            v_da = pl.GetMoistAirVolume(Tmean-273.15, Wmean, Pmean)
            h_da = pl.GetMoistAirEnthalpy(Tmean - 273.15, Wmean)

        rho_ha = 1 / v_da * ( 1 + Wmean) #[kg_ha/m^3]
        rho_da = 1 / v_da #[kg_da/m^3]

        #Transport properties of humid air from CoolProp
        mu_ha = HAPropsSI('M', 'T', Tmean, 'P', Pmean, 'W', Wmean)
        k_ha = HAPropsSI('K', 'T', Tmean, 'P', Pmean, 'W', Wmean)
        
        #Use a forward difference to calculate cp from cp=dh/dT
        dT=0.0001 #[K]
        if self.Accurate == True:
            cp_da = (HAPropsSI('H', 'T', Tmean + dT, 'P', Pmean, 'W', Wmean) - h_da) / dT 
        else:
            cp_da = (pl.GetMoistAirEnthalpy(Tmean + dT - 273.15, Wmean) - h_da) / dT 
        #[J/kg_da/K]
        self.cp_da = cp_da
        cp_ha = cp_da / (1 + Wmean) #[J/kg_ha/K]
        
        return rho_ha, rho_da, mu_ha, k_ha, cp_da, cp_ha
        
    
    # Correlations
    def Abumadi1998_Plane_dry_geometry(self):
        FPI = self.Fins_geometry.FPI        #Fins per inch
        FPM = FPI / 0.0254                  #Fins per meter [1/m]
        Ltube = self.Fins_geometry.Ltube
        Nfin = Ltube * FPM
        delta_f = self.Fins_geometry.t      #Fin thickness
        Sf = 1 / FPM - delta_f              #Fin spacing(m)
        Sr = self.Fins_geometry.Pl          #row spacing
        St = self.Fins_geometry.Pt          #tube spacing
        Do = self.Fins_geometry.Do          #tube outside diameter
        Di = self.Fins_geometry.Di          #tube inside diameter
        Nbank = self.Fins_geometry.Nbank    #number of tube rows
        Ltube = self.Fins_geometry.Ltube
        Nheight = self.Fins_geometry.Nheight
        Ntubes_bank = self.Fins_geometry.Ntubes_bank
        
        self.Abumadi1998 = ValuesClass()
        self.Abumadi1998.R3 = Do / Di * (1 - delta_f / Sf) + 2 * St * Sr / (pi * Di * Sf) - pow(Do, 2) / (2 * Di * Sf) + 2 * delta_f * St / (pi * Di * Sf * Nbank)
        self.Abumadi1998.R4 = Sf * St / ((St - Do) * (Sf - delta_f))
        self.Abumadi1998.R5 = pi * Nbank * Do * (1 - delta_f / Sf) / St + Nbank / Sf * (2 * Sr - pi * pow(Do, 2) / (2 * St) + 2 * delta_f / Nbank)
        self.Abumadi1998.R5_1 = self.Abumadi1998.R5 / Nbank
        self.Abumadi1998.R6 = 4 * Sr * Nbank / self.Abumadi1998.R5
        self.Abumadi1998.R7 = 1 / (1 + (2 * pi * Do * (Sf - delta_f) / (4 * St * Sr - pi * pow(Do, 2) + 4 * St * delta_f / Nbank)))
        self.Abumadi1998.R8 = Sf / Do
        self.Abumadi1998.R9 = Sr / Do
        self.Abumadi1998.Ac = St * Nheight * Ltube - delta_f * Ltube * FPM * (St * Nheight - Do * Ntubes_bank) - Ntubes_bank * Do * Ltube
        self.Abumadi1998.Nbank = Nbank
        
        Af = Nfin * 2.0 * (St * Nheight * Sr * Nbank - Ntubes_bank * Nbank * pi * Do * Do / 4) 
        Ao = Af + Ntubes_bank * Nbank * pi * Do * (Ltube - Nfin * delta_f)
        
        self.Ao = Ao

        self.Af_Ao_eff = self.Abumadi1998.R7
        X_T = St / 2
        X_D = sqrt(pow(Sr, 2) + pow(St, 2) / 4) / 2
        self.ro_eff = 1.27 * X_T * sqrt(X_D / X_T - 0.3)
        self.ri_eff = Do / 2
        self.rfr_eff = self.ro_eff / self.ri_eff
        self.phi_eff = (self.rfr_eff - 1) * (1 + 0.35 * log(self.rfr_eff))
        
    def Abumadi1998_Plane_dry(self, Tin, Tout, Win, Wout, Pin, Pout, mdot_ha):
        '''
        from "Performance characteristics correlation for round tube and plate
        finned heat exchangers", Abumadi (1998)
        '''
        
        R3 = self.Abumadi1998.R3
        R4 = self.Abumadi1998.R4
        R5 = self.Abumadi1998.R5
        R5_1 = self.Abumadi1998.R5_1
        R6 = self.Abumadi1998.R6
        R7 = self.Abumadi1998.R7
        R8 = self.Abumadi1998.R8
        R9 = self.Abumadi1998.R9
        Ac = self.Abumadi1998.Ac
        Nbank = self.Abumadi1998.Nbank
        
        rho_ha, rho_da, mu_ha, k_ha, cp_da, cp_ha = self.calculate_air_props(Tin, Tout, Win, Wout, Pin, Pout)
        
        u_max = mdot_ha / (rho_ha * Ac) # free flow area velocity
        Re = rho_ha * u_max * R6 / mu_ha
        
        j4 = pow(Re, -0.44) * pow(R4, -3.07) * pow(R5_1, 0.37) * pow(R7, -6.14) * pow(R9, -2.13)
        
        jNbank = j4 / (0.87 + 1.43E-5 * pow(Re, 0.55) * pow(Nbank, -0.67) * pow(R3, -3.13) * pow(R5_1, 4.95))
        Pr = cp_ha * mu_ha / k_ha
        h_a = jNbank * rho_ha * u_max * cp_ha / pow(Pr, 2.0 / 3.0) 

        f = pow(Re, -0.25) * pow(R4, -1.43) * pow(R5_1, 1.37) * pow(R8, 1.65) * pow(R9, -3.05)
        
        DP = -f * pow(u_max, 2) * pow(R4, 3) * R5 / 2
        
        return h_a, DP
        
    def Wang2000_Plain_Dry_geometry(self):
        FPI = self.Fins_geometry.FPI        #Fins per inch
        FPM = FPI / 0.0254                  #Fins per meter [1/m]
        Fp = 1 / FPM                        #Fin pitch (distance between centerlines of fins)
        Ltube = self.Fins_geometry.Ltube
        Nfin = Ltube * FPM
        delta_f = self.Fins_geometry.t      #Fin thickness
        Pl = self.Fins_geometry.Pl          #row spacing
        Pt = self.Fins_geometry.Pt          #tube spacing
        Do = self.Fins_geometry.Do          #tube outside diameter
        Nbank = self.Fins_geometry.Nbank    #number of tube rows
        Ltube = self.Fins_geometry.Ltube
        Nheight = self.Fins_geometry.Nheight
        Ntubes_bank = self.Fins_geometry.Ntubes_bank
        Dc = Do + 2 * delta_f
        Ac = Pt * Nheight * Ltube - delta_f * Ltube * FPM * (Pt * Nheight - Do * Ntubes_bank) - Ntubes_bank * Do * Ltube
        
        Af = 2.0 * (Pt * Nheight * Pl * Nbank - Ntubes_bank * Nbank * pi * Do * Do / 4) 
        
        Af_o = Nfin * Af
        Ao = Af_o + Ntubes_bank * Nbank * pi * Do * (Ltube - Nfin * delta_f)

        L = Pl * Nbank
        
        Dh = 4 * Ac * L / Ao #Hydraulic diameter

        self.Ao = Ao
        self.Af_Ao_eff = Af_o / Ao
        X_T = Pt / 2
        X_D = sqrt(pow(Pl, 2) + pow(Pt, 2) / 4) / 2
        self.ro_eff = 1.27 * X_T * sqrt(X_D / X_T - 0.3)
        self.ri_eff = Do / 2
        self.rfr_eff = self.ro_eff / self.ri_eff
        self.phi_eff = (self.rfr_eff - 1) * (1 + 0.35 * log(self.rfr_eff))
        self.Wang2000 = ValuesClass()
        self.Wang2000.Dc = Dc
        self.Wang2000.Dh = Dh
        self.Wang2000.Ac = Ac
        self.Wang2000.Pt = Pt
        self.Wang2000.Pl = Pl
        self.Wang2000.Fp = Fp
        self.Wang2000.Nbank = Nbank
        self.Wang2000.delta_f = delta_f
    
    def Wang2000_Plain_Dry(self,Tin, Tout, Win, Wout, Pin, Pout, mdot_ha):
        ''' from "Heat transfer and friction characteristics of plain fin-and-
            tube heat exchangers, part II: Correlation", Wang et al. (2000)
        '''
        Dc = self.Wang2000.Dc
        Dh = self.Wang2000.Dh
        Ac = self.Wang2000.Ac
        Pt = self.Wang2000.Pt
        Pl = self.Wang2000.Pl
        Fp = self.Wang2000.Fp
        Ao = self.Ao
        Nbank = self.Wang2000.Nbank
        
        rho_ha, rho_da, mu_ha, k_ha, cp_da, cp_ha = self.calculate_air_props(Tin, Tout, Win, Wout, Pin, Pout)
                
        u_max = mdot_ha / (rho_ha * Ac) # free flow area velocity
        Re_Dc = rho_ha * u_max * Dc / mu_ha

        #heat transfer
        if Nbank == 1:
            P1 = 1.9 - 0.23 * log(Re_Dc)
            P2 = -0.236 + 0.126 * log(Re_Dc)
            j = 0.108 * pow(Re_Dc, -0.29) * pow(Pt / Pl, P1) * pow(Fp / Dc, -1.084) * pow(Fp / Dh, -0.786) * pow(Fp / Pt, P2)
        if Nbank >= 2:
            P3 = -0.361 - 0.042 * Nbank / log(Re_Dc) + 0.158 * log(Nbank * pow(Fp / Dc, 0.41))
            P4 = -1.224 - 0.076 * pow(Pl / Dh, 1.42) / log(Re_Dc)
            P5 = -0.083 + 0.058 * Nbank / log(Re_Dc)
            P6 = -5.735 + 1.21 * log(Re_Dc / Nbank)
            j = 0.086*pow(Re_Dc, P3) * pow(Nbank, P4) * pow(Fp / Dc, P5) * pow(Fp / Dh, P6) * pow(Fp / Pt, -0.93)
        #pressure drop
        F1 = -0.764 + 0.739 * Pt / Pl + 0.177 * Fp / Dc - 0.00758 / Nbank
        F2 = -15.689 + 64.021 / log(Re_Dc)
        F3 = 1.696 - 15.695 / log(Re_Dc)
        f = 0.0267 * pow(Re_Dc, F1) * pow(Pt / Pl, F2) * pow(Fp / Dc, F3)
        Pr = cp_ha * mu_ha / k_ha
        h_a = j * rho_ha * u_max * cp_ha / pow(Pr, 2.0 / 3.0) 
        
        Gc = mdot_ha / Ac #air mass flux
        DP = -Ao * Gc**2 * f / (Ac * rho_ha * 2.0) #airside pressure drop
        
        return h_a, DP
    
    def Wang1997_Plain_Wet_geometry(self):
        FPI = self.Fins_geometry.FPI        #Fins per inch
        FPM = FPI / 0.0254                  #Fins per meter [1/m]
        Fp = 1 / FPM                        #Fin pitch (distance between centerlines of fins)
        Ltube = self.Fins_geometry.Ltube
        Nfin = Ltube * FPM
        delta_f = self.Fins_geometry.t      #Fin thickness
        Pl = self.Fins_geometry.Pl          #row spacing
        Pt = self.Fins_geometry.Pt          #tube spacing
        Do = self.Fins_geometry.Do          #tube outside diameter
        Nbank = self.Fins_geometry.Nbank    #number of tube rows
        Ltube = self.Fins_geometry.Ltube
        Nheight = self.Fins_geometry.Nheight
        Ntubes_bank = self.Fins_geometry.Ntubes_bank
        Dc = Do + 2 * delta_f
        Ac = Pt * Nheight * Ltube - delta_f * Ltube * FPM * (Pt * Nheight - Do * Ntubes_bank) - Ntubes_bank * Do * Ltube
        
        Af = Nfin * 2.0 * (Pt * Nheight * Pl * Nbank - Ntubes_bank * Nbank * pi * Do * Do / 4) 
            
        Ao = Af + Ntubes_bank * Nbank * pi * Do * (Ltube - Nfin * delta_f)
        
        Atube = Ntubes_bank * Nbank * pi * Do * Ltube
        
        self.Ao = Ao
        self.Af_Ao_eff = Af / Ao
        X_T = Pt / 2
        X_D = sqrt(pow(Pl, 2) + pow(Pt, 2) / 4) / 2
        self.ro_eff = 1.27 * X_T * sqrt(X_D / X_T - 0.3)
        self.ri_eff = Do / 2
        self.rfr_eff = self.ro_eff / self.ri_eff
        self.phi_eff = (self.rfr_eff - 1) * (1 + 0.35 * log(self.rfr_eff))
        
        self.Wang1997_wet = ValuesClass()
        self.Wang1997_wet.Atube = Atube
        self.Wang1997_wet.Dc = Dc
        self.Wang1997_wet.Ac = Ac
        self.Wang1997_wet.Pt = Pt
        self.Wang1997_wet.Pl = Pl
        self.Wang1997_wet.Fp = Fp
        self.Wang1997_wet.Nbank = Nbank
        self.Wang1997_wet.delta_f = delta_f
        self.Wang1997_wet.Ltube = Ltube
    
    def Wang1997_Plain_Wet(self,Tin, Tout, Win, Wout, Pin, Pout, mdot_ha):
        ''' from "Performance of Plate Finned Tube Heat Exchangers Under 
            Dehumidifying Conditions", Wang et al. (1997)
        '''
        
        Dc = self.Wang1997_wet.Dc
        Ac = self.Wang1997_wet.Ac
        Fp = self.Wang1997_wet.Fp
        Atube = self.Wang1997_wet.Atube
        Ao = self.Ao
        Nbank = self.Wang1997_wet.Nbank
        
        rho_ha, rho_da, mu_ha, k_ha, cp_da, cp_ha = self.calculate_air_props(Tin, Tout, Win, Wout, Pin, Pout)
        
        u_max = mdot_ha / (rho_ha * Ac) # free flow area velocity
        Re_Dc = rho_ha * u_max * Dc / mu_ha
        
        epsilon = Ao / Atube
        
        if Nbank == 4:
            j = 0.29773 * pow(Re_Dc, -0.364) * pow(epsilon, -0.168)        
        else:
            j = 0.4 * pow(Re_Dc, -0.468 + 0.04076 * Nbank) * pow(epsilon, 0.159) * pow(Nbank, -1.261)
        
        f = 28.209 * pow(Re_Dc, -0.5653) * pow(Nbank, -0.1026) * pow(Fp / Dc, -1.3405) * pow(epsilon, -1.3343)
        
        Pr = cp_ha * mu_ha / k_ha
        h_a = j * rho_ha * u_max * cp_ha / pow(Pr, 2.0 / 3.0) 
        
        Gc = mdot_ha / Ac #air mass flux
        DP = -Ao * Gc**2 * f / (Ac * rho_ha * 2.0) #airside pressure drop
        
        return h_a, DP
    
    def Wang1999_Louvered_Dry_geometry(self):
        '''
            For dimensions:
            https://imgur.com/uCBZx4Y
        '''
        FPI = self.Fins_geometry.FPI        #Fins per inch
        FPM = FPI / 0.0254                  #Fins per meter [1/m]
        Fp = 1 / FPM                        #Fin pitch (distance between centerlines of fins)
        Ltube = self.Fins_geometry.Ltube
        Nfin = Ltube * FPM
        delta_f = self.Fins_geometry.t      #Fin thickness
        Lp = self.Fins_geometry.Lp          #Breadth of a slit in the direction of ariflow (m)
        Lh = self.Fins_geometry.Lh          #height of slit (m)
        Pl = self.Fins_geometry.Pl          #row spacing
        Pt = self.Fins_geometry.Pt          #tube spacing
        Do = self.Fins_geometry.Do          #tube outside diameter
        Nbank = self.Fins_geometry.Nbank    #number of tube rows
        Ltube = self.Fins_geometry.Ltube
        Nheight = self.Fins_geometry.Nheight
        Ntubes_bank = self.Fins_geometry.Ntubes_bank
        Dc = Do + 2 * delta_f
        Ac = Pt * Nheight * Ltube - delta_f * Ltube * FPM * (Pt * Nheight - Do * Ntubes_bank) - Ntubes_bank * Do * Ltube
        
        Fin_width = Nbank * Pl
        
        Af = Nfin * 2.0 * (Pt * Nheight * Fin_width - Ntubes_bank * Nbank * pi * Do * Do / 4)

        Ao = Af + Ntubes_bank * Nbank * pi * Do * (Ltube - Nfin * delta_f)

        Atube = Ntubes_bank * Nbank * pi * Do * Ltube
                
        Dh = 4 * Ac * (Nbank * Pl) / Ao #Hydraulic diameter
        
        self.Ao = Ao
        self.Af_Ao_eff = Af / Ao
        X_T = Pt / 2
        X_D = sqrt(pow(Pl, 2) + pow(Pt, 2) / 4) / 2
        self.ro_eff = 1.27 * X_T * sqrt(X_D / X_T - 0.3)
        self.ri_eff = Do / 2
        self.rfr_eff = self.ro_eff / self.ri_eff
        self.phi_eff = (self.rfr_eff - 1) * (1 + 0.35 * log(self.rfr_eff))
        
        self.Wang1999_Louvered_dry = ValuesClass()
        self.Wang1999_Louvered_dry.Atube = Atube
        self.Wang1999_Louvered_dry.Dc = Dc
        self.Wang1999_Louvered_dry.Dh = Dh
        self.Wang1999_Louvered_dry.Ac = Ac
        self.Wang1999_Louvered_dry.Pt = Pt
        self.Wang1999_Louvered_dry.Pl = Pl
        self.Wang1999_Louvered_dry.Fp = Fp
        self.Wang1999_Louvered_dry.Nbank = Nbank
        self.Wang1999_Louvered_dry.Lp = Lp
        self.Wang1999_Louvered_dry.Lh = Lh
    
    def Wang1999_Louvered_Dry(self,Tin, Tout, Win, Wout, Pin, Pout, mdot_ha):
        '''from "Heat transfer and friction correlation for compact louvered
        fin-and-tube heat exchangers", Wang et al (1999)        
        '''
        
        Dc = self.Wang1999_Louvered_dry.Dc
        Dh = self.Wang1999_Louvered_dry.Dh
        Ac = self.Wang1999_Louvered_dry.Ac
        Pt = self.Wang1999_Louvered_dry.Pt
        Pl = self.Wang1999_Louvered_dry.Pl
        Fp = self.Wang1999_Louvered_dry.Fp
        Atube = self.Wang1999_Louvered_dry.Atube
        Ao = self.Ao
        Nbank = self.Wang1999_Louvered_dry.Nbank
        Lp = self.Wang1999_Louvered_dry.Lp
        Lh = self.Wang1999_Louvered_dry.Lh
        
        rho_ha, rho_da, mu_ha, k_ha, cp_da, cp_ha = self.calculate_air_props(Tin, Tout, Win, Wout, Pin, Pout)
        u_max = mdot_ha / (rho_ha * Ac) # free flow area velocity
        Re_Dc = rho_ha * u_max * Dc / mu_ha
        #heat transfer
        if Re_Dc >= 1000:
            j5 = -0.6027 + 0.02593 * pow(Pl / Dh, 0.52) * pow(Nbank, -0.5) * log(Lh / Lp)
            j6 = -0.4776 + 0.40774 * (pow(Nbank, 0.7) / (log(Re_Dc) - 4.4))
            j7 = -0.58655 * pow(Fp / Dh, 2.3) * pow(Pl / Pt, -1.6) * pow(Nbank, -0.65)
            j8 = 0.0814 * (log(Re_Dc) - 3)
            j = 1.1373 * pow(Re_Dc, j5) * pow(Fp / Pl, j6) * pow(Lh / Lp, j7) * pow(Pl / Pt, j8) * pow(Nbank, 0.3545)
        
        elif Re_Dc < 1000:
            j1 = -0.991 - 0.1055 * pow(Pl / Pt, 3.1) * log(Lh / Lp)
            j2 = -0.7344 + 2.1059 * (pow(Nbank, 0.55) / (log(Re_Dc) - 3.2))
            j3 = 0.08485 * pow(Pl / Pt, -4.4) * pow(Nbank, -0.68)
            j4 = -0.1741 * log(Nbank)
            j = 14.3117 * pow(Re_Dc, j1) * pow(Fp / Dc, j2) * pow(Lh / Lp, j3) * pow(Fp / Pl, j4) * pow(Pl / Pt, -1.724)
            
        #pressure drop
        if Nbank == 1:
            f1 = 0.1691 + 4.4118 * pow(Fp / Pl, -0.3) * pow(Lh / Lp, -2.0) * log(Pl / Pt) * pow(Fp / Pt, 3)
            f2 = -2.6642 - 14.3809 / log(Re_Dc)
            f3 = -0.6816 * log(Fp / Pl)
            f4 = 6.4668 * pow(Fp / Pt, 1.7) * log(Ao / Atube)
            f = 0.00317 * pow(Re_Dc, f1) * pow(Fp / Pl, f2) * pow(Dh / Dc, f3) * pow(Lh / Lp, f4) * pow(log(Ao / Atube), -6.0483)

        elif Nbank > 1:
            f5 = 0.1395 - 0.0101 * pow(Fp / Pl, 0.58) * pow(Lh / Lp, -2) * log(Ao / Atube) * pow(Pl / Pt, 1.9)
            f6 = -6.4367 / log(Re_Dc)
            f7 = 0.07191 * log(Re_Dc)
            f8 = -2.0585 * pow(Fp/Pt, 1.67) * log(Re_Dc)
            f9 = 0.1036 * log(Pl / Pt)
            f = 0.06393 * pow(Re_Dc, f5) * pow(Fp / Dc, f6) * pow(Dh / Dc, f7) * pow(Lh / Lp, f8) * pow(Nbank, f9) * pow(log(Re_Dc) - 4.0, -1.093)

        Pr = cp_ha * mu_ha / k_ha
        h_a = j * rho_ha * u_max * cp_ha / pow(Pr, 2.0 / 3.0) 
        
        Gc = mdot_ha / Ac #air mass flux
        DP = -Ao * Gc**2 * f / (Ac * rho_ha * 2.0) #airside pressure drop
        
        return h_a, DP
    
    def Wang2000_Louvered_Wet_geometry(self):
        '''
            For dimensions:
            https://imgur.com/uCBZx4Y
        '''
        FPI = self.Fins_geometry.FPI        #Fins per inch
        FPM = FPI / 0.0254                  #Fins per meter [1/m]
        Fp = 1 / FPM                        #Fin pitch (distance between centerlines of fins)
        Ltube = self.Fins_geometry.Ltube
        Nfin = Ltube * FPM
        delta_f = self.Fins_geometry.t      #Fin thickness
        Lp = self.Fins_geometry.Lp          #Breadth of a slit in the direction of ariflow (m)
        Lh = self.Fins_geometry.Lh          #height of slit (m)
        Pl = self.Fins_geometry.Pl          #row spacing
        Pt = self.Fins_geometry.Pt          #tube spacing
        Do = self.Fins_geometry.Do          #tube outside diameter
        Nbank = self.Fins_geometry.Nbank    #number of tube rows
        Ltube = self.Fins_geometry.Ltube
        Nheight = self.Fins_geometry.Nheight
        Ntubes_bank = self.Fins_geometry.Ntubes_bank
        Dc = Do + 2 * delta_f
        Ac = Pt * Nheight * Ltube - delta_f * Ltube * FPM * (Pt * Nheight - Do * Ntubes_bank) - Ntubes_bank * Do * Ltube
        Aface = Pt * Nheight * Ltube
        Fin_width = Nbank * Pl
        
        Af = Nfin * 2.0 * (Pt * Nheight * Fin_width - Ntubes_bank * Nbank * pi * Do * Do / 4)
            
        Ao = Af + Ntubes_bank * Nbank * pi * Do * (Ltube - Nfin * delta_f)
        
        Atube = Ntubes_bank * Nbank * pi * Do * Ltube
        
        self.Ao = Ao
        self.Af_Ao_eff = Af / Ao
        X_T = Pt / 2
        X_D = sqrt(pow(Pl, 2) + pow(Pt, 2) / 4) / 2
        self.ro_eff = 1.27 * X_T * sqrt(X_D / X_T - 0.3)
        self.ri_eff = Do / 2
        self.rfr_eff = self.ro_eff / self.ri_eff
        self.phi_eff = (self.rfr_eff - 1) * (1 + 0.35 * log(self.rfr_eff))
        
        self.Wang2000_Louvered_wet = ValuesClass()
        self.Wang2000_Louvered_wet.Atube = Atube
        self.Wang2000_Louvered_wet.Dc = Dc
        self.Wang2000_Louvered_wet.Ac = Ac
        self.Wang2000_Louvered_wet.Aface = Aface
        self.Wang2000_Louvered_wet.Pt = Pt
        self.Wang2000_Louvered_wet.Pl = Pl
        self.Wang2000_Louvered_wet.Fp = Fp
        self.Wang2000_Louvered_wet.Nbank = Nbank
        self.Wang2000_Louvered_wet.Lp = Lp
        self.Wang2000_Louvered_wet.Lh = Lh
        self.Wang2000_Louvered_wet.Ltube = Ltube

    def Wang2000_Louvered_Wet(self,Tin, Tout, Win, Wout, Pin, Pout, mdot_ha, water_cond, mu_f):
        '''from "Heat transfer and friction correlation for compact louvered
        fin-and-tube heat exchangers", Wang et al (2000)        
        '''
        
        Dc = self.Wang2000_Louvered_wet.Dc
        Ac = self.Wang2000_Louvered_wet.Ac
        Pt = self.Wang2000_Louvered_wet.Pt
        Pl = self.Wang2000_Louvered_wet.Pl
        Fp = self.Wang2000_Louvered_wet.Fp
        Ao = self.Ao
        Nbank = self.Wang2000_Louvered_wet.Nbank
        Lp = self.Wang2000_Louvered_wet.Lp
        Lh = self.Wang2000_Louvered_wet.Lh
        Ltube = self.Wang2000_Louvered_wet.Ltube

        rho_ha, rho_da, mu_ha, k_ha, cp_da, cp_ha = self.calculate_air_props(Tin, Tout, Win, Wout, Pin, Pout)
        
        u_max = mdot_ha / (rho_ha * Ac)
        Re_Dc = rho_ha * u_max * Dc / mu_ha

        # heat transfer
        j1 = -0.023634 - 1.2475 * pow(Fp / Dc, 0.65) * pow(Pl / Pt, 0.2) * pow(Nbank, -0.18)
        j2 = 0.856 * exp(Lh / Lp)
        j3 = 0.25 * log(Re_Dc)
        j = 9.717 * pow(Re_Dc, j1) * pow(Fp / Dc, j2) * pow(Pl / Pt, j3) * pow(log(3 - Lp / Fp), 0.07162) * pow(Nbank, -0.543)

        # pressure drop
        f1 = 1.223 - 2.857 * pow(Fp / Dc, 0.71) * pow(Pl / Pt, -0.05)
        f2 = 0.8079 * log(Re_Dc)
        f3 = 0.8932 * log(Re_Dc)
        if water_cond == None or (2 * water_cond/ Ltube / mu_f) < 1: # to avoid very low values of pressure drop
            water_cond = Ltube
            mu_f = 0.2
            
        f4 = -0.999 * log(2 * water_cond/ Ltube / mu_f)
        f = 2.814 * pow(Re_Dc, f1) * pow(Fp/ Dc, f2) * pow(Pl / Dc, f3) * pow(Pl / Pt + 0.091, f4) * pow(Lp / Fp, 1.958) * pow(Nbank, 0.04674)
        
        Pr = cp_ha * mu_ha / k_ha
        h_a = j * rho_ha * u_max * cp_ha / pow(Pr, 2.0 / 3.0)

        Gc = mdot_ha / Ac #air mass flux
        DP = -Ao * Gc**2 * f / (Ac * rho_ha * 2.0) #airside pressure drop
        return h_a, DP
    
    def Wang2001_Slit_Dry_geometry(self):
        '''
            For dimensions:
            https://imgur.com/mt9jy0F
        '''
        FPI = self.Fins_geometry.FPI        #Fins per inch
        FPM = FPI / 0.0254                  #Fins per meter [1/m]
        Fp = 1 / FPM                        #Fin pitch (distance between centerlines of fins)
        Ltube = self.Fins_geometry.Ltube
        Nfin = Ltube * FPM
        delta_f = self.Fins_geometry.t      #Fin thickness
        Fs = 1 / FPM - delta_f              #Fin spacing(m)
        Ss = self.Fins_geometry.Ss                  #Breadth of a slit in the direction of ariflow (m)
        Sh = self.Fins_geometry.Sh                  #height of slit (m)
        Sn = self.Fins_geometry.Sn                  #Number of slits in an enhanced zone
        Pl = self.Fins_geometry.Pl          #row spacing
        Pt = self.Fins_geometry.Pt          #tube spacing
        Do = self.Fins_geometry.Do          #tube outside diameter
        Nbank = self.Fins_geometry.Nbank    #number of tube rows
        Ltube = self.Fins_geometry.Ltube
        Nheight = self.Fins_geometry.Nheight
        Ntubes_bank = self.Fins_geometry.Ntubes_bank
        Dc = Do + 2 * delta_f
        Ac = Pt * Nheight * Ltube - delta_f * Ltube * FPM * (Pt * Nheight - Do * Ntubes_bank) - Ntubes_bank * Do * Ltube
                
        Af = Nfin * 2.0 * (Pt * Nheight * Pl * Nbank - Ntubes_bank * Nbank * pi * Do * Do / 4)
            
        Ao = Af + Ntubes_bank * Nbank * pi * Do * (Ltube - Nfin * delta_f)
                
        Dh = 4 * Ac * Nbank * Pl / Ao #Hydraulic diameter

        self.Ao = Ao
        self.Af_Ao_eff = Af / Ao
        X_T = Pt / 2
        X_D = sqrt(pow(Pl, 2) + pow(Pt, 2) / 4) / 2
        self.ro_eff = 1.27 * X_T * sqrt(X_D / X_T - 0.3)
        self.ri_eff = Do / 2
        self.rfr_eff = self.ro_eff / self.ri_eff
        self.phi_eff = (self.rfr_eff - 1) * (1 + 0.35 * log(self.rfr_eff))
        
        self.wang2001_Slit_dry = ValuesClass()
        self.wang2001_Slit_dry.Dc = Dc
        self.wang2001_Slit_dry.Dh = Dh
        self.wang2001_Slit_dry.Ac = Ac
        self.wang2001_Slit_dry.Pt = Pt
        self.wang2001_Slit_dry.Pl = Pl
        self.wang2001_Slit_dry.Fp = Fp
        self.wang2001_Slit_dry.Fs = Fs
        self.wang2001_Slit_dry.Nbank = Nbank
        self.wang2001_Slit_dry.Ss = Ss
        self.wang2001_Slit_dry.Sh = Sh
        self.wang2001_Slit_dry.Sn = Sn
    
    def Wang2001_Slit_Dry(self,Tin, Tout, Win, Wout, Pin, Pout, mdot_ha):
        '''from "A Comparative study of compact enhanced fin-and-tube heat
            exchangers", Wang et al (2001)        
        '''
        
        Dc = self.wang2001_Slit_dry.Dc
        Dh = self.wang2001_Slit_dry.Dh
        Ac = self.wang2001_Slit_dry.Ac
        Pt = self.wang2001_Slit_dry.Pt
        Pl = self.wang2001_Slit_dry.Pl
        Fs = self.wang2001_Slit_dry.Fs
        Ao = self.Ao
        Nbank = self.wang2001_Slit_dry.Nbank
        Ss = self.wang2001_Slit_dry.Ss
        Sh = self.wang2001_Slit_dry.Sh
        Sn = self.wang2001_Slit_dry.Sn
        
        rho_ha, rho_da, mu_ha, k_ha, cp_da, cp_ha = self.calculate_air_props(Tin, Tout, Win, Wout, Pin, Pout)
        
        u_max = mdot_ha / (rho_ha * Ac) # free flow area velocity
        Re_Dc = rho_ha * u_max * Dc / mu_ha
        Re = rho_ha * u_max * Dh / mu_ha
        
        if (0 < Nbank <= 2) or (Nbank > 2 and Re_Dc > 700):
            j4 = -0.535 + 0.017 * (Pt / Pl) - 0.0107 * Nbank
            j5 = 0.4115 + 5.5756 * sqrt(Nbank / Re_Dc) * log(Nbank / Re_Dc) + 24.2028 * sqrt(Nbank / Re_Dc)
            j6 = 0.2646 + 1.0491 * (Ss / Sh) * log(Ss / Sh) - 0.216 * pow(Ss / Sh, 3)
            j7 = 0.3749 + 0.0046 * sqrt(Re_Dc) * log(Re_Dc) - 0.0433 * sqrt(Re_Dc)
            j = 1.0691 * pow(Re_Dc, j4) * pow(Fs / Dc, j5) * pow(Ss / Sh, j6) * pow(Nbank, j7)
            
        elif Nbank > 2 and Re_Dc < 700:
            j1 = -0.2555 - 0.0312 / (Fs / Dc) - 0.0487 * Nbank
            j2 = 0.9703 - 0.0455 * sqrt(Re_Dc) - 0.4986 * pow(log(Pt / Pl), 2)
            j3 = 0.2405 - 0.003 * Re + 5.5349 * (Fs / Dc)
            j = 0.9047 * pow(Re_Dc, j1) * pow(Fs / Dc, j2) * pow(Pt / Pl, j3) * pow(Ss / Sh, -0.0305) * pow(Nbank, 0.0782)
        
        #pressure drop
        f1 = -0.1401 + 0.2567 * log(Fs / Dc) + 4.399 * exp(-Sn)
        f2 = -0.383 + 0.7998 * log(Fs / Dc) + 5.1772 / Sn
        f3 = -1.7266 - 0.1102 * log(Re_Dc) - 1.4501 * (Fs / Dc)
        if Ss == Sh:
            f4 = 1.0
        else:
            f4 = 0.4034 - 0.199 * ((Ss / Sh) / log(Ss / Sh)) + 0.4208 * (log(Ss / Sh) / pow(Ss / Sh, 2))
        if Nbank != 1:
            f5 = -9.0566 + 0.6199 * log(Re_Dc) + 32.8057 / log(Re_Dc) - 0.2881 / log(Nbank) + 0.9583 / pow(Nbank, 1.5)
        else:
            f5 = 0
        f6 = -1.4994 + 1.209 * (Pt / Pl) + 1.4601 / Sn
        f = 1.201 * pow(Re_Dc, f1) * pow(Fs / Dc, f2) * pow(Pt / Pl, f3) * pow(Ss / Sh, f4) * pow(Nbank, f5) * pow(Sn, f6)

        Pr = cp_ha * mu_ha / k_ha
        h_a = j * rho_ha * u_max * cp_ha / pow(Pr, 2.0 / 3.0) 
        
        Gc = mdot_ha / Ac #air mass flux
        DP = -Ao * Gc**2 * f / (Ac * rho_ha * 2.0) #airside pressure drop
        
        return h_a, DP

    def Kim2000_Slit_Dry_geometry(self):
        '''
            For dimensions:
            https://imgur.com/mt9jy0F
        '''
        FPI = self.Fins_geometry.FPI        #Fins per inch
        FPM = FPI / 0.0254                  #Fins per meter [1/m]
        Fp = 1 / FPM                        #Fin pitch (distance between centerlines of fins)
        Ltube = self.Fins_geometry.Ltube
        Nfin = Ltube * FPM
        delta_f = self.Fins_geometry.t      #Fin thickness
        Pl = self.Fins_geometry.Pl          #row spacing
        Pt = self.Fins_geometry.Pt          #tube spacing
        Do = self.Fins_geometry.Do          #tube outside diameter
        Nbank = self.Fins_geometry.Nbank    #number of tube rows
        Ltube = self.Fins_geometry.Ltube
        Nheight = self.Fins_geometry.Nheight
        Ntubes_bank = self.Fins_geometry.Ntubes_bank
        Dc = Do + 2 * delta_f
        Ac = Pt * Nheight * Ltube - delta_f * Ltube * FPM * (Pt * Nheight - Do * Ntubes_bank) - Ntubes_bank * Do * Ltube
        
        Af = Nfin * 2.0 * (Pt * Nheight * Pl * Nbank - Ntubes_bank * Nbank * pi * Do * Do / 4)
            
        Ao = Af + Ntubes_bank * Nbank * pi * Do * (Ltube - Nfin * delta_f)
                
        self.Ao = Ao
        self.Af_Ao_eff = Af / Ao
        X_T = Pt / 2
        X_D = sqrt(pow(Pl, 2) + pow(Pt, 2) / 4) / 2
        self.ro_eff = 1.27 * X_T * sqrt(X_D / X_T - 0.3)
        self.ri_eff = Do / 2
        self.rfr_eff = self.ro_eff / self.ri_eff
        self.phi_eff = (self.rfr_eff - 1) * (1 + 0.35 * log(self.rfr_eff))
        
        self.kim2000_Slit_dry = ValuesClass()
        self.kim2000_Slit_dry.Dc = Dc
        self.kim2000_Slit_dry.Ac = Ac
        self.kim2000_Slit_dry.Pl = Pl
        self.kim2000_Slit_dry.Fp = Fp
        self.kim2000_Slit_dry.Nbank = Nbank


    def Kim2000_Slit_Dry(self,Tin, Tout, Win, Wout, Pin, Pout, mdot_ha):
        '''from "Condensate Accumulation Effects on the Air-Side Thermal 
            Performance of Slit-Fin Surfaces", Kim and Jacobi (2000)
        '''
        
        Dc = self.kim2000_Slit_dry.Dc
        Ac = self.kim2000_Slit_dry.Ac
        Pl = self.kim2000_Slit_dry.Pl
        Fp = self.kim2000_Slit_dry.Fp
        Ao = self.Ao
        Nbank = self.kim2000_Slit_dry.Nbank
        
        rho_ha, rho_da, mu_ha, k_ha, cp_da, cp_ha = self.calculate_air_props(Tin, Tout, Win, Wout, Pin, Pout)
        
        u_max = mdot_ha / (rho_ha * Ac) # free flow area velocity
        Re_Dc = rho_ha * u_max * Dc / mu_ha
        
        # heat transfer
        j = 0.2476 * pow(Re_Dc, -0.209) * pow(Fp / Dc, 0.4325) * pow(Pl * Nbank / Dc, -0.3792)
        
        # pressure drop        
        f = 1.024 * pow(Re_Dc, -0.5123) * pow(Fp / Dc, -0.7315) * pow(Pl * Nbank / Dc, 0.1666)
        
        Pr = cp_ha * mu_ha / k_ha
        h_a = j * rho_ha * u_max * cp_ha / pow(Pr, 2.0 / 3.0) 
        
        Gc = mdot_ha / Ac #air mass flux
        DP = -Ao * Gc**2 * f / (Ac * rho_ha * 2.0) #airside pressure drop
        
        return h_a, DP

    def Kim2000_Slit_Wet_geometry(self):
        '''
            For dimensions:
            https://imgur.com/mt9jy0F
        '''
        FPI = self.Fins_geometry.FPI        #Fins per inch
        FPM = FPI / 0.0254                  #Fins per meter [1/m]
        Fp = 1 / FPM                        #Fin pitch (distance between centerlines of fins)
        Ltube = self.Fins_geometry.Ltube
        Nfin = Ltube * FPM
        delta_f = self.Fins_geometry.t      #Fin thickness
        Pl = self.Fins_geometry.Pl          #row spacing
        Pt = self.Fins_geometry.Pt          #tube spacing
        Do = self.Fins_geometry.Do          #tube outside diameter
        Nbank = self.Fins_geometry.Nbank    #number of tube rows
        Ltube = self.Fins_geometry.Ltube
        Nheight = self.Fins_geometry.Nheight
        Ntubes_bank = self.Fins_geometry.Ntubes_bank
        Dc = Do + 2 * delta_f
        Ac = Pt * Nheight * Ltube - delta_f * Ltube * FPM * (Pt * Nheight - Do * Ntubes_bank) - Ntubes_bank * Do * Ltube
        
        Af = Nfin * 2.0 * (Pt * Nheight * Pl * Nbank - Ntubes_bank * Nbank * pi * Do * Do / 4)
            
        Ao = Af + Ntubes_bank * Nbank * pi * Do * (Ltube - Nfin * delta_f)
                
        self.Ao = Ao
        self.Af_Ao_eff = Af / Ao
        X_T = Pt / 2
        X_D = sqrt(pow(Pl, 2) + pow(Pt, 2) / 4) / 2
        self.ro_eff = 1.27 * X_T * sqrt(X_D / X_T - 0.3)
        self.ri_eff = Do / 2
        self.rfr_eff = self.ro_eff / self.ri_eff
        self.phi_eff = (self.rfr_eff - 1) * (1 + 0.35 * log(self.rfr_eff))
        
        self.kim2000_Slit_Wet = ValuesClass()
        self.kim2000_Slit_Wet.Dc = Dc
        self.kim2000_Slit_Wet.Ac = Ac
        self.kim2000_Slit_Wet.Pt = Pt
        self.kim2000_Slit_Wet.Fp = Fp
        self.kim2000_Slit_Wet.Nbank = Nbank


    def Kim2000_Slit_Wet(self,Tin, Tout, Win, Wout, Pin, Pout, mdot_ha):
        '''from "Condensate Accumulation Effects on the Air-Side Thermal 
            Performance of Slit-Fin Surfaces", Kim and Jacobi (2000)
        '''
        
        Dc = self.kim2000_Slit_Wet.Dc
        Ac = self.kim2000_Slit_Wet.Ac
        Pt = self.kim2000_Slit_Wet.Pt
        Fp = self.kim2000_Slit_Wet.Fp
        Ao = self.Ao
        Nbank = self.kim2000_Slit_Wet.Nbank
        
        rho_ha, rho_da, mu_ha, k_ha, cp_da, cp_ha = self.calculate_air_props(Tin, Tout, Win, Wout, Pin, Pout)
        
        u_max = mdot_ha / (rho_ha * Ac) # free flow area velocity
        Re_Dc = rho_ha * u_max * Dc / mu_ha

        # heat transfer
        j = 0.3647 * pow(Re_Dc, -0.1457) * pow(Fp / Dc, 1.21) * pow(Pt * Nbank / Dc, -0.3181)

        # pressure drop        
        f = 1.265 * pow(Re_Dc, -0.2991) * pow(Fp / Dc, -0.2918) * pow(Pt * Nbank / Dc, -0.1985)

        Pr = cp_ha * mu_ha / k_ha
        h_a = j * rho_ha * u_max * cp_ha / pow(Pr, 2.0 / 3.0) 
        
        Gc = mdot_ha / Ac #air mass flux
        DP = -Ao * Gc**2 * f / (Ac * rho_ha * 2.0) #airside pressure drop
        
        return h_a, DP

    def Wang1997_Wavy_Dry_geometry(self):
        '''        
        || -    xf    ->
        ^              ==                          ==
        |           ==  |  ==                  ==
        Pd       ==     |     ==            ==
        |     ==        |        ==     ==
        =  ==           s             ==  
                        |
                        |
                        |
                       ==                        ==
                    ==     ==                 ==
                 ==           ==           ==
              ==                 ==     ==
           ==                        ==  
        
         t: thickness of fin plate
         Pf: fin pitch (centerline-to-centerline distance between fins)
         Pd: indentation for waviness (not including fin thickness)
         s: fin spacing (free space between fins) = Pf-t
        
        
        
                     |--       Pl      -|
                    ___                 |
                  /     \               |
           =     |       |              |
           |      \ ___ /               |
           |                            |
           |                           ___      
           |                         /     \      |
          Pt                        |       |     D
           |                         \ ___ /      |
           |    
           |        ___
           |      /     \
           =     |       |
                  \ ___ /
        '''
        FPI = self.Fins_geometry.FPI        #Fins per inch
        FPM = FPI / 0.0254                  #Fins per meter [1/m]
        Ltube = self.Fins_geometry.Ltube
        Nfin = Ltube * FPM
        delta_f = self.Fins_geometry.t      #Fin thickness
        pd = self.Fins_geometry.Pd                   
        xf = self.Fins_geometry.xf                   
        Pl = self.Fins_geometry.Pl          #row spacing
        Pt = self.Fins_geometry.Pt          #tube spacing
        Do = self.Fins_geometry.Do          #tube outside diameter
        Nbank = self.Fins_geometry.Nbank    #number of tube rows
        Ltube = self.Fins_geometry.Ltube
        Nheight = self.Fins_geometry.Nheight
        Ntubes_bank = self.Fins_geometry.Ntubes_bank
        Dc = Do + 2 * delta_f
        Ac = Pt * Nheight * Ltube - delta_f * Ltube * FPM * (Pt * Nheight - Do * Ntubes_bank) - Ntubes_bank * Do * Ltube
        
        sec_theta = sqrt(xf*xf + pd*pd) / xf   
                
        Af = Nfin * 2.0 * (Pt * Nheight * Pl * Nbank * sec_theta - Ntubes_bank * Nbank * pi * Do * Do / 4)

        Ao = Af + Ntubes_bank * Nbank * pi * Do * (Ltube - Nfin * delta_f)

        Atube = Ntubes_bank * Nbank * pi * Do * Ltube
        
        Aduct = Pt * Nheight * Ltube
        
        segma = Ac / Aduct
        
        self.Ao = Ao
        self.Af_Ao_eff = Af / Ao
        X_T = Pt / 2
        X_D = sqrt(pow(Pl, 2) + pow(Pt, 2) / 4) / 2
        self.ro_eff = 1.27 * X_T * sqrt(X_D / X_T - 0.3)
        self.ri_eff = Do / 2
        self.rfr_eff = self.ro_eff / self.ri_eff
        self.phi_eff = (self.rfr_eff - 1) * (1 + 0.35 * log(self.rfr_eff))
        
        self.wang1997_Wavy_dry = ValuesClass()
        self.wang1997_Wavy_dry.Dc = Dc
        self.wang1997_Wavy_dry.Ac = Ac
        self.wang1997_Wavy_dry.segma = segma
        self.wang1997_Wavy_dry.Atube = Atube
        self.wang1997_Wavy_dry.Nbank = Nbank
    
    def Wang1997_Wavy_Dry(self,Tin, Tout, Win, Wout, Pin, Pout, mdot_ha):
        '''from "Heat Transfer and Friction Characteristics of Typical Wavy 
        Fin-and-Tube Heat Exchangers", Wang et al (1997)        
        '''
        
        Dc = self.wang1997_Wavy_dry.Dc
        Ac = self.wang1997_Wavy_dry.Ac
        segma = self.wang1997_Wavy_dry.segma
        Atube = self.wang1997_Wavy_dry.Atube
        Ao = self.Ao
        Nbank = self.wang1997_Wavy_dry.Nbank
        
        rho_ha, rho_da, mu_ha, k_ha, cp_da, cp_ha = self.calculate_air_props(Tin, Tout, Win, Wout, Pin, Pout)
        
        u_max = mdot_ha / (rho_ha * Ac) # free flow area velocity
        Re_Dc = rho_ha * u_max * Dc / mu_ha
        
        #heat transfer
        j = 1.201 / pow(log(pow(Re_Dc, segma)), 2.921)
        
        #pressure drop
        f = 16.67 / pow(log(Re_Dc), 2.64) * pow(Ao / Atube, -0.096) * pow(Nbank, 0.098)

        Pr = cp_ha * mu_ha / k_ha
        h_a = j * rho_ha * u_max * cp_ha / pow(Pr, 2.0 / 3.0) 
        
        Gc = mdot_ha / Ac #air mass flux
        DP = -Ao * Gc**2 * f / (Ac * rho_ha * 2.0) #airside pressure drop
        
        return h_a, DP

    def Wang1999_Wavy_Wet_geometry(self):
        '''        
        || -    xf    ->
        ^              ==                          ==
        |           ==  |  ==                  ==
        Pd       ==     |     ==            ==
        |     ==        |        ==     ==
        =  ==           s             ==  
                        |
                        |
                        |
                       ==                        ==
                    ==     ==                 ==
                 ==           ==           ==
              ==                 ==     ==
           ==                        ==  
        
         t: thickness of fin plate
         Pf: fin pitch (centerline-to-centerline distance between fins)
         Pd: indentation for waviness (not including fin thickness)
         s: fin spacing (free space between fins) = Pf-t
        
        
        
                     |--       Pl      -|
                    ___                 |
                  /     \               |
           =     |       |              |
           |      \ ___ /               |
           |                            |
           |                           ___      
           |                         /     \      |
          Pt                        |       |     D
           |                         \ ___ /      |
           |    
           |        ___
           |      /     \
           =     |       |
                  \ ___ /
        '''
        FPI = self.Fins_geometry.FPI        #Fins per inch
        FPM = FPI / 0.0254                  #Fins per meter [1/m]
        Fp = 1 / FPM                        #Fin pitch (distance between centerlines of fins)
        Ltube = self.Fins_geometry.Ltube
        Nfin = Ltube * FPM
        delta_f = self.Fins_geometry.t      #Fin thickness
        Fs = 1 / FPM - delta_f              #Fin spacing(m)
        Pd = self.Fins_geometry.Pd
        xf = self.Fins_geometry.xf
        Pl = self.Fins_geometry.Pl          #row spacing
        Pt = self.Fins_geometry.Pt          #tube spacing
        Do = self.Fins_geometry.Do          #tube outside diameter
        Nbank = self.Fins_geometry.Nbank    #number of tube rows
        Ltube = self.Fins_geometry.Ltube
        Nheight = self.Fins_geometry.Nheight
        Ntubes_bank = self.Fins_geometry.Ntubes_bank
        Dc = Do + 2 * delta_f
        Ac = Pt * Nheight * Ltube - delta_f * Ltube * FPM * (Pt * Nheight - Do * Ntubes_bank) - Ntubes_bank * Do * Ltube
        
        sec_theta = sqrt(xf * xf + Pd * Pd) / xf        
        
        Af = Nfin * 2.0 * (Pt * Nheight * Pl * Nbank * sec_theta  - Ntubes_bank * Nbank * pi * Do * Do / 4)
            
        Ao = Af + Ntubes_bank * Nbank * pi * Do * (Ltube - Nfin * delta_f)
                
        self.Ao = Ao
        self.Af_Ao_eff = Af / Ao
        X_T = Pt / 2
        X_D = sqrt(pow(Pl, 2) + pow(Pt, 2) / 4) / 2
        self.ro_eff = 1.27 * X_T * sqrt(X_D / X_T - 0.3)
        self.ri_eff = Do / 2
        self.rfr_eff = self.ro_eff / self.ri_eff
        self.phi_eff = (self.rfr_eff - 1) * (1 + 0.35 * log(self.rfr_eff))
        
        self.Wang1999_Wavy_wet = ValuesClass()
        self.Wang1999_Wavy_wet.Dc = Dc
        self.Wang1999_Wavy_wet.Ac = Ac
        self.Wang1999_Wavy_wet.Pt = Pt
        self.Wang1999_Wavy_wet.Pl = Pl
        self.Wang1999_Wavy_wet.Fs = Fs
        self.Wang1999_Wavy_wet.Fp = Fp
        self.Wang1999_Wavy_wet.Nbank = Nbank
        self.Wang1999_Wavy_wet.Pd = Pd
        self.Wang1999_Wavy_wet.xf = xf
        self.Wang1999_Wavy_wet.Ltube = Ltube

    def Wang1999_Wavy_Wet(self,Tin, Tout, Win, Wout, Pin, Pout, mdot_ha, water_cond, mu_f):
        '''from "Air-side performance of herringbone wavy fin-and-tube heat 
            exchangers under dehumidifying condition – Data with larger 
            diameter tube", Wang et Liaw (1999)        
        '''
        
        Dc = self.Wang1999_Wavy_wet.Dc
        Ac = self.Wang1999_Wavy_wet.Ac
        Pt = self.Wang1999_Wavy_wet.Pt
        Pl = self.Wang1999_Wavy_wet.Pl
        Fs = self.Wang1999_Wavy_wet.Fs
        Fp = self.Wang1999_Wavy_wet.Fp
        Ao = self.Ao
        Nbank = self.Wang1999_Wavy_wet.Nbank
        Pd = self.Wang1999_Wavy_wet.Pd
        xf = self.Wang1999_Wavy_wet.xf
        Ltube = self.Wang1999_Wavy_wet.Ltube

        rho_ha, rho_da, mu_ha, k_ha, cp_da, cp_ha = self.calculate_air_props(Tin, Tout, Win, Wout, Pin, Pout)
        
        u_max = mdot_ha / (rho_ha * Ac) # free flow area velocity
        Re_Dc = rho_ha * u_max * Dc / mu_ha
        
        # heat transfer
        j1 = -0.5836 + 0.2371 * pow(Fs / Dc, 0.55) * pow(Nbank, 0.34) * pow(Pt / Pl, 1.2)
        j2 = 1.1873 - 3.0219 * pow(Fs / Dc, 1.5) * pow(Pd / xf, 0.9) * pow(log(Re_Dc), 1.22)
        j3 = 0.006672 * (Pt / Pl) * pow(Nbank, 1.96)
        j4 = -0.1157 * pow(Fs / Dc, 0.9) * log(50 / Re_Dc)
        j = 0.472293 * pow(Re_Dc, j1) * pow(Pt / Pl, j2) * pow(Pd / xf, j3) * pow(Pd / Fs, j4) * pow(Nbank, -0.4933)
        
        # Pressure drop
        f1 = -0.067 + (Pd / Fs) * (1.35 / log(Re_Dc)) - 0.15 * (Nbank / log(Re_Dc)) + 0.0153 * (Fs / Dc)
        f2 = 2.981 - 0.082 * log(Re_Dc) + 0.127 * Nbank / (4.605 - log(Re_Dc))
        f3 = 0.53 - 0.0491 * log(Re_Dc)
        f4 = 11.91 * pow(Nbank / log(Re_Dc), 0.7)
        f5 = -1.32 + 0.287 * log(Re_Dc)
        if water_cond == None or (2 * water_cond/ Ltube / mu_f) < 1:
            water_cond = Ltube
            mu_f = 0.2
        f = 0.149001 * pow(Re_Dc, f1) * pow(Pt / Pl, f2) * pow(Nbank, f3) * pow(log(3.1 - Pd / xf), f4) * pow(Fp / Dc, f5) * pow(2 * water_cond/ Ltube / mu_f, 0.0769)
        
        Pr = cp_ha * mu_ha / k_ha
        h_a = j * rho_ha * u_max * cp_ha / pow(Pr, 2.0 / 3.0)
        
        Gc = mdot_ha / Ac #air mass flux
        DP = -Ao * Gc**2 * f / (Ac * rho_ha * 2.0) #airside pressure drop
        
        return h_a, DP

    def Wang2002_Wavy_Wet_geometry(self):
        '''        
        || -    xf    ->
        ^              ==                          ==
        |           ==  |  ==                  ==
        Pd       ==     |     ==            ==
        |     ==        |        ==     ==
        =  ==           s             ==  
                        |
                        |
                        |
                       ==                        ==
                    ==     ==                 ==
                 ==           ==           ==
              ==                 ==     ==
           ==                        ==  
        
         t: thickness of fin plate
         Pf: fin pitch (centerline-to-centerline distance between fins)
         Pd: indentation for waviness (not including fin thickness)
         s: fin spacing (free space between fins) = Pf-t
        
        
        
                     |--       Pl      -|
                    ___                 |
                  /     \               |
           =     |       |              |
           |      \ ___ /               |
           |                            |
           |                           ___      
           |                         /     \      |
          Pt                        |       |     D
           |                         \ ___ /      |
           |    
           |        ___
           |      /     \
           =     |       |
                  \ ___ /
        '''
        FPI = self.Fins_geometry.FPI        #Fins per inch
        FPM = FPI / 0.0254                  #Fins per meter [1/m]
        Ltube = self.Fins_geometry.Ltube
        Nfin = Ltube * FPM
        delta_f = self.Fins_geometry.t      #Fin thickness
        Fs = 1 / FPM - delta_f              #Fin spacing(m)
        Pd = self.Fins_geometry.Pd
        xf = self.Fins_geometry.xf
        Pl = self.Fins_geometry.Pl          #row spacing
        Pt = self.Fins_geometry.Pt          #tube spacing
        Do = self.Fins_geometry.Do          #tube outside diameter
        Nbank = self.Fins_geometry.Nbank    #number of tube rows
        Ltube = self.Fins_geometry.Ltube
        Nheight = self.Fins_geometry.Nheight
        Ntubes_bank = self.Fins_geometry.Ntubes_bank
        Ac = Pt * Nheight * Ltube - delta_f * Ltube * FPM * (Pt * Nheight - Do * Ntubes_bank) - Ntubes_bank * Do * Ltube

        sec_theta = sqrt(xf * xf + Pd * Pd) / xf        
        
        theta = atan(Pd / xf) * 180 / pi

        Af = Nfin * 2.0 * (Pt * Nheight * Pl * Nbank * sec_theta  - Ntubes_bank * Nbank * pi * Do * Do / 4)
            
        Ao = Af + Ntubes_bank * Nbank * pi * Do * (Ltube - Nfin * delta_f)
        
        Dh = 4 * Ac * Pl * Nbank / Ao #Hydraulic diameter
        
        self.Ao = Ao
        self.Af_Ao_eff = Af / Ao
        X_T = Pt / 2
        X_D = sqrt(pow(Pl, 2) + pow(Pt, 2) / 4) / 2
        self.ro_eff = 1.27 * X_T * sqrt(X_D / X_T - 0.3)
        self.ri_eff = Do / 2
        self.rfr_eff = self.ro_eff / self.ri_eff
        self.phi_eff = (self.rfr_eff - 1) * (1 + 0.35 * log(self.rfr_eff))
        
        self.Wang2002_Wavy_wet = ValuesClass()
        self.Wang2002_Wavy_wet.Dh = Dh
        self.Wang2002_Wavy_wet.Ac = Ac
        self.Wang2002_Wavy_wet.Fs = Fs
        self.Wang2002_Wavy_wet.theta = theta

    def Wang2002_Wavy_Wet(self,Tin, Tout, Win, Wout, Pin, Pout, mdot_ha, water_cond, mu_f):
        '''from "Performance of the herringbone wavy fin under dehumidifying 
            conditions", Lin et. al (2002)        
        '''
        
        Dh = self.Wang2002_Wavy_wet.Dh
        Ac = self.Wang2002_Wavy_wet.Ac
        Fs = self.Wang2002_Wavy_wet.Fs
        theta = self.Wang2002_Wavy_wet.theta
        Ao = self.Ao

        rho_ha, rho_da, mu_ha, k_ha, cp_da, cp_ha = self.calculate_air_props(Tin, Tout, Win, Wout, Pin, Pout)
        
        u_max = mdot_ha / (rho_ha * Ac) # free flow area velocity
        Re_Dh = rho_ha * u_max * Dh / mu_ha

        if self.Accurate == True:
            RH = HAPropsSI('R', 'T', Tin, 'P', Pin, 'W', Win) * 100
        else:
            RH = pl.GetRelHumFromHumRatio(Tin - 273.15, Win, Pin) * 100
        
        # heat transfer
        n1 = 0.92333
        n2 = 2.5906
        n3 = 0.47028
        n4 = 0.07773
        Nu = 0.02656 * pow(Re_Dh, n1) * pow(Fs / Dh, n2) * pow(theta, n3) * pow(RH, n4)
        
        # Pressure drop
        f1 = -0.41543
        f2 = -0.096529
        f3 = 1.3385
        f4 = -0.13035
        f = 0.02403 * pow(Re_Dh, f1) * pow(Fs / Dh, f2) * pow(theta, f3) * pow(RH, f4)
        
        h_a = Nu * k_ha / Dh

        Gc = mdot_ha / Ac #air mass flux
        DP = -Ao * Gc**2 * f / (Ac * rho_ha * 2.0) #airside pressure drop

        return h_a, DP

    def Wang1998_WavyLouvered_Dry_geometry(self):
        '''        
        || -    xf    ->
        ^              ==                          ==
        |           ==  |  ==                  ==
        Pd       ==     |     ==            ==
        |     ==        |        ==     ==
        =  ==           s             ==  
                        |
                        |
                        |
                       ==                        ==
                    ==     ==                 ==
                 ==           ==           ==
              ==                 ==     ==
           ==                        ==  
        
         t: thickness of fin plate
         Pf: fin pitch (centerline-to-centerline distance between fins)
         Pd: indentation for waviness (not including fin thickness)
         s: fin spacing (free space between fins) = Pf-t
        
        
        
                     |--       Pl      -|
                    ___                 |
                  /     \               |
           =     |       |              |
           |      \ ___ /               |
           |                            |
           |                           ___      
           |                         /     \      |
          Pt                        |       |     D
           |                         \ ___ /      |
           |    
           |        ___
           |      /     \
           =     |       |
                  \ ___ /
        '''
        FPI = self.Fins_geometry.FPI        #Fins per inch
        FPM = FPI / 0.0254                  #Fins per meter [1/m]
        Fp = 1 / FPM                        #Fin pitch (distance between centerlines of fins)
        Ltube = self.Fins_geometry.Ltube
        Nfin = Ltube * FPM
        delta_f = self.Fins_geometry.t      #Fin thickness
        pd = self.Fins_geometry.Pd                   
        xf = self.Fins_geometry.xf                   
        Pl = self.Fins_geometry.Pl          #row spacing
        Pt = self.Fins_geometry.Pt          #tube spacing
        Do = self.Fins_geometry.Do          #tube outside diameter
        Nbank = self.Fins_geometry.Nbank    #number of tube rows
        Ltube = self.Fins_geometry.Ltube
        Nheight = self.Fins_geometry.Nheight
        Ntubes_bank = self.Fins_geometry.Ntubes_bank
        Dc = Do + 2 * delta_f
        Ac = Pt * Nheight * Ltube - delta_f * Ltube * FPM * (Pt * Nheight - Do * Ntubes_bank) - Ntubes_bank * Do * Ltube
                
        sec_theta = sqrt(xf*xf + pd*pd) / xf   
                
        Af = Nfin * 2.0 * (Pt * Nheight * Pl * Nbank * sec_theta - Ntubes_bank * Nbank * pi * Do * Do / 4)
            
        Ao = Af + Ntubes_bank * Nbank * pi * Do * (Ltube - Nfin * delta_f)
        
        Atube = Ntubes_bank * Nbank * pi * Do * Ltube
                
        self.Ao = Ao
        self.Af_Ao_eff = Af / Ao
        X_T = Pt / 2
        X_D = sqrt(pow(Pl, 2) + pow(Pt, 2) / 4) / 2
        self.ro_eff = 1.27 * X_T * sqrt(X_D / X_T - 0.3)
        self.ri_eff = Do / 2
        self.rfr_eff = self.ro_eff / self.ri_eff
        self.phi_eff = (self.rfr_eff - 1) * (1 + 0.35 * log(self.rfr_eff))
        
        self.wang1998_WavyLouvered_dry = ValuesClass()
        self.wang1998_WavyLouvered_dry.Dc = Dc
        self.wang1998_WavyLouvered_dry.Ac = Ac
        self.wang1998_WavyLouvered_dry.Fp = Fp
        self.wang1998_WavyLouvered_dry.Atube = Atube
        self.wang1998_WavyLouvered_dry.Nbank = Nbank
    
    def Wang1998_WavyLouvered_Dry(self,Tin, Tout, Win, Wout, Pin, Pout, mdot_ha):
        '''from "Comprehensive Study of Convex-Louver and Wavy Fin-and-Tube Heat 
            Exchangers", Wang et al (1998)
        '''
        
        Dc = self.wang1998_WavyLouvered_dry.Dc
        Ac = self.wang1998_WavyLouvered_dry.Ac
        Fp = self.wang1998_WavyLouvered_dry.Fp
        Atube = self.wang1998_WavyLouvered_dry.Atube
        Ao = self.Ao
        Nbank = self.wang1998_WavyLouvered_dry.Nbank
        
        rho_ha, rho_da, mu_ha, k_ha, cp_da, cp_ha = self.calculate_air_props(Tin, Tout, Win, Wout, Pin, Pout)
        
        u_max = mdot_ha / (rho_ha * Ac) # free flow area velocity
        
        Re_Dc = rho_ha * u_max * Dc / mu_ha

        #Heat transfer
        j = 16.06 * pow(Re_Dc, -1.02 * (Fp / Dc) - 0.256) * pow(Ao / Atube, -0.601) * pow(Nbank, -0.069) * pow(Fp / Dc, 0.84)
        
        # Pressure drop
        if (Re_Dc<1e3):
            f = 0.264 * (0.105 + 0.708 * exp(-Re_Dc / 225)) * pow(Re_Dc, -0.637) * pow(Ao/Atube, 0.263) *  pow(Fp / Dc, -0.317)
        else:
            f = 0.768 * (0.0494 + 0.142 * exp(-Re_Dc / 1180)) * pow(Ao/Atube, 0.0195) * pow(Fp / Dc, -0.121)
            
        Pr = cp_ha * mu_ha / k_ha
        h_a = j * rho_ha * u_max * cp_ha / pow(Pr, 2.0 / 3.0) 
        
        Gc = mdot_ha / Ac #air mass flux
        DP = -Ao * Gc**2 * f / (Ac * rho_ha * 2.0) #airside pressure drop

        return h_a, DP

    def Wang1996_Plain_Dry_geometry(self):
        FPI = self.Fins_geometry.FPI        #Fins per inch
        FPM = FPI / 0.0254                  #Fins per meter [1/m]
        Fp = 1 / FPM                        #Fin pitch (distance between centerlines of fins)
        Ltube = self.Fins_geometry.Ltube
        Nfin = Ltube * FPM
        delta_f = self.Fins_geometry.t      #Fin thickness
        Pl = self.Fins_geometry.Pl          #row spacing
        Pt = self.Fins_geometry.Pt          #tube spacing
        Do = self.Fins_geometry.Do          #tube outside diameter
        Nbank = self.Fins_geometry.Nbank    #number of tube rows
        Ltube = self.Fins_geometry.Ltube
        Nheight = self.Fins_geometry.Nheight
        Ntubes_bank = self.Fins_geometry.Ntubes_bank
        Dc = Do + 2 * delta_f
        Ac = Pt * Nheight * Ltube - delta_f * Ltube * FPM * (Pt * Nheight - Do * Ntubes_bank) - Ntubes_bank * Do * Ltube

        Af = Nfin * 2.0 * (Pt * Nheight * Pl * Nbank - Ntubes_bank * Nbank * pi * Do * Do / 4) 
            
        Ao = Af + Ntubes_bank * Nbank * pi * Do * (Ltube - Nfin * delta_f)
        
        self.Ao = Ao
        self.Af_Ao_eff = Af / Ao
        X_T = Pt / 2
        X_D = sqrt(pow(Pl, 2) + pow(Pt, 2) / 4) / 2
        self.ro_eff = 1.27 * X_T * sqrt(X_D / X_T - 0.3)
        self.ri_eff = Do / 2
        self.rfr_eff = self.ro_eff / self.ri_eff
        self.phi_eff = (self.rfr_eff - 1) * (1 + 0.35 * log(self.rfr_eff))
        self.Wang1996_plain_dry = ValuesClass()
        self.Wang1996_plain_dry.Dc = Dc
        self.Wang1996_plain_dry.Ac = Ac
        self.Wang1996_plain_dry.Fp = Fp
        self.Wang1996_plain_dry.Nbank = Nbank
        self.Wang1996_plain_dry.delta_f = delta_f
    
    def Wang1996_Plain_Dry(self,Tin, Tout, Win, Wout, Pin, Pout, mdot_ha):
        ''' from "Sensible heat and friction characteristics of plate 
            fin-and-tube heat exchangers having plane fins", Wang et al. (1996)
        '''
        Dc = self.Wang1996_plain_dry.Dc
        Ac = self.Wang1996_plain_dry.Ac
        Fp = self.Wang1996_plain_dry.Fp
        Ao = self.Ao
        Nbank = self.Wang1996_plain_dry.Nbank
        delta_f = self.Wang1996_plain_dry.delta_f
        
        rho_ha, rho_da, mu_ha, k_ha, cp_da, cp_ha = self.calculate_air_props(Tin, Tout, Win, Wout, Pin, Pout)
        
        u_max = mdot_ha / (rho_ha * Ac) # free flow area velocity
        Re_Dc = rho_ha * u_max * Dc / mu_ha
                
        #heat transfer
        j = 0.394 * pow(Re_Dc, -0.392) * pow(delta_f / Dc, -0.0449) * pow(Nbank, -0.0897) * pow(Fp / Dc, -0.212)
        
        #pressure drop
        f = 1.039 * pow(Re_Dc, -0.418) * pow(delta_f / Dc, -0.104) * pow(Nbank, -0.0935) * pow(Fp / Dc, -0.197)
        
        Pr = cp_ha * mu_ha / k_ha
        h_a = j * rho_ha * u_max * cp_ha / pow(Pr, 2.0 / 3.0) 
        
        Gc = mdot_ha / Ac #air mass flux
        DP = -Ao * Gc**2 * f / (Ac * rho_ha * 2.0) #airside pressure drop
        return h_a, DP

    def Wang2000_Plain_Wet_geometry(self):
        FPI = self.Fins_geometry.FPI        #Fins per inch
        FPM = FPI / 0.0254                  #Fins per meter [1/m]
        Fp = 1 / FPM                        #Fin pitch (distance between centerlines of fins)
        Ltube = self.Fins_geometry.Ltube
        Nfin = Ltube * FPM
        delta_f = self.Fins_geometry.t      #Fin thickness
        Pl = self.Fins_geometry.Pl          #row spacing
        Pt = self.Fins_geometry.Pt          #tube spacing
        Do = self.Fins_geometry.Do          #tube outside diameter
        Nbank = self.Fins_geometry.Nbank    #number of tube rows
        Ltube = self.Fins_geometry.Ltube
        Nheight = self.Fins_geometry.Nheight
        Ntubes_bank = self.Fins_geometry.Ntubes_bank
        Dc = Do + 2 * delta_f
        Ac = Pt * Nheight * Ltube - delta_f * Ltube * FPM * (Pt * Nheight - Do * Ntubes_bank) - Ntubes_bank * Do * Ltube
        
        Af = Nfin * 2.0 * (Pt * Nheight * Pl * Nbank - Ntubes_bank * Nbank * pi * Do * Do / 4) 
            
        Ao = Af + Ntubes_bank * Nbank * pi * Do * (Ltube - Nfin * delta_f)
        
        Atube = Ntubes_bank * Nbank * pi * Do * Ltube
        
        Dh = 4 * Ac * Pl * Nbank / Ao #Hydraulic diameter
        
        self.Ao = Ao
        self.Af_Ao_eff = Af / Ao
        X_T = Pt / 2
        X_D = sqrt(pow(Pl, 2) + pow(Pt, 2) / 4) / 2
        self.ro_eff = 1.27 * X_T * sqrt(X_D / X_T - 0.3)
        self.ri_eff = Dc / 2
        self.rfr_eff = self.ro_eff / self.ri_eff
        self.phi_eff = (self.rfr_eff - 1) * (1 + 0.35 * log(self.rfr_eff))
        
        self.Wang2000_Plain_wet = ValuesClass()
        self.Wang2000_Plain_wet.Atube = Atube
        self.Wang2000_Plain_wet.Dc = Dc
        self.Wang2000_Plain_wet.Dh = Dh
        self.Wang2000_Plain_wet.Ac = Ac
        self.Wang2000_Plain_wet.Pt = Pt
        self.Wang2000_Plain_wet.Pl = Pl
        self.Wang2000_Plain_wet.Fp = Fp
        self.Wang2000_Plain_wet.Nbank = Nbank
        self.Wang2000_Plain_wet.Ltube = Ltube

    def Wang2000_Plain_Wet(self,Tin, Tout, Win, Wout, Pin, Pout, mdot_ha, water_cond, mu_f):
        '''from "An airside correlation for plain fin-and-tube heat exchangers 
            in wet conditions", Wang et al (2000)        
        '''
        
        Dc = self.Wang2000_Plain_wet.Dc
        Dh = self.Wang2000_Plain_wet.Dh
        Ac = self.Wang2000_Plain_wet.Ac
        Pt = self.Wang2000_Plain_wet.Pt
        Pl = self.Wang2000_Plain_wet.Pl
        Fp = self.Wang2000_Plain_wet.Fp
        Atube = self.Wang2000_Plain_wet.Atube
        Ao = self.Ao
        Nbank = self.Wang2000_Plain_wet.Nbank
        Ltube = self.Wang2000_Plain_wet.Ltube

        rho_ha, rho_da, mu_ha, k_ha, cp_da, cp_ha = self.calculate_air_props(Tin, Tout, Win, Wout, Pin, Pout)
        
        u_max = mdot_ha / (rho_ha * Ac) # free flow area velocity
        Re_Dc = rho_ha * u_max * Dc / mu_ha
        # Re = rho_ha * u_max * Dh / mu_ha
        Re_film = 2 * water_cond / Ltube / mu_f
        if Re_film < 0.01:
            Re_film = 8 # This is an assumption, to avoid very low values of f in case water_cond value couldn't be calculated at each step
        # heat transfer
        j1 = 0.3745 - 1.554 * pow(Fp / Dc, 0.24) * pow(Pl / Pt, 0.12) * pow(Nbank, -0.19)
        j = 19.36 * pow(Re_Dc, j1) * pow(Fp / Dc, 1.352) * pow(Pl / Pt, 0.6795) * pow(Nbank, -1.291)

        # pressure drop
        f1 = -0.7339 + 7.187 * pow(Fp / Pl, 2.5) * log(9 * Re_film)
        f2 = -0.5417 * log(Ao / Atube) * pow(Fp / Dc, 0.9)
        f3 = 0.02722 * log(6 * Re_film) * pow(Pl / Pt, 3.2) * log(Re_Dc)
        f4 = 0.2973 * log(Ao / Atube) * log(Dh / Dc)
        f = 16.55 * pow(Re_Dc, f1) * pow(10 * Re_film, f2) * pow(Ao / Atube, f3) * pow(Pl / Pt, f4) * pow(Fp / Dh, -0.5827) * pow(exp(Dh / Dc), -1.117)

        Pr = cp_ha * mu_ha / k_ha
        h_a = j * rho_ha * u_max * cp_ha / pow(Pr, 2.0 / 3.0)
        
        Gc = mdot_ha / Ac #air mass flux
        DP = -Ao * Gc**2 * f / (Ac * rho_ha * 2.0) #airside pressure drop

        return h_a, DP

    def Wang1996_WavyLouvered_Dry_geometry(self):
        '''        
        || -    xf    ->
        ^              ==                          ==
        |           ==  |  ==                  ==
        Pd       ==     |     ==            ==
        |     ==        |        ==     ==
        =  ==           s             ==  
                        |
                        |
                        |
                       ==                        ==
                    ==     ==                 ==
                 ==           ==           ==
              ==                 ==     ==
           ==                        ==  
        
         t: thickness of fin plate
         Pf: fin pitch (centerline-to-centerline distance between fins)
         Pd: indentation for waviness (not including fin thickness)
         s: fin spacing (free space between fins) = Pf-t
        
        
        
                     |--       Pl      -|
                    ___                 |
                  /     \               |
           =     |       |              |
           |      \ ___ /               |
           |                            |
           |                           ___      
           |                         /     \      |
          Pt                        |       |     D
           |                         \ ___ /      |
           |    
           |        ___
           |      /     \
           =     |       |
                  \ ___ /
        '''
        FPI = self.Fins_geometry.FPI        #Fins per inch
        FPM = FPI / 0.0254                  #Fins per meter [1/m]
        Fp = 1 / FPM                        #Fin pitch (distance between centerlines of fins)
        Ltube = self.Fins_geometry.Ltube
        Nfin = Ltube * FPM
        delta_f = self.Fins_geometry.t      #Fin thickness
        pd = self.Fins_geometry.Pd                   
        xf = self.Fins_geometry.xf                   
        Pl = self.Fins_geometry.Pl          #row spacing
        Pt = self.Fins_geometry.Pt          #tube spacing
        Do = self.Fins_geometry.Do          #tube outside diameter
        Nbank = self.Fins_geometry.Nbank    #number of tube rows
        Ltube = self.Fins_geometry.Ltube
        Nheight = self.Fins_geometry.Nheight
        Ntubes_bank = self.Fins_geometry.Ntubes_bank
        Dc = Do + 2 * delta_f
        Ac = Pt * Nheight * Ltube - delta_f * Ltube * FPM * (Pt * Nheight - Do * Ntubes_bank) - Ntubes_bank * Do * Ltube
                
        sec_theta = sqrt(xf*xf + pd*pd) / xf   
                
        Af = Nfin * 2.0 * (Pt * Nheight * Pl * Nbank * sec_theta - Ntubes_bank * Nbank * pi * Do * Do / 4)
            
        Ao = Af + Ntubes_bank * Nbank * pi * Do * (Ltube - Nfin * delta_f)
        
        Atube = Ntubes_bank * Nbank * pi * Do * Ltube
                        
        self.Ao = Ao
        self.Af_Ao_eff = Af / Ao
        X_T = Pt / 2
        X_D = sqrt(pow(Pl, 2) + pow(Pt, 2) / 4) / 2
        self.ro_eff = 1.27 * X_T * sqrt(X_D / X_T - 0.3)
        self.ri_eff = Do / 2
        self.rfr_eff = self.ro_eff / self.ri_eff
        self.phi_eff = (self.rfr_eff - 1) * (1 + 0.35 * log(self.rfr_eff))
        
        self.wang1996_WavyLouvered_dry = ValuesClass()
        self.wang1996_WavyLouvered_dry.Dc = Dc
        self.wang1996_WavyLouvered_dry.Ac = Ac
        self.wang1996_WavyLouvered_dry.Fp = Fp
        self.wang1996_WavyLouvered_dry.Atube = Atube
    
    def Wang1996_WavyLouvered_Dry(self,Tin, Tout, Win, Wout, Pin, Pout, mdot_ha):
        '''from "HEAT TRANSFER AND FRICTION CHARACTERISTICS OF CONVEX-LOUVER 
            FIN-AND-TUBE HEAT EXCHANGERS", Wang et al (1996)
        '''
        
        Dc = self.wang1996_WavyLouvered_dry.Dc
        Ac = self.wang1996_WavyLouvered_dry.Ac
        Fp = self.wang1996_WavyLouvered_dry.Fp
        Atube = self.wang1996_WavyLouvered_dry.Atube
        Ao = self.Ao
        
        rho_ha, rho_da, mu_ha, k_ha, cp_da, cp_ha = self.calculate_air_props(Tin, Tout, Win, Wout, Pin, Pout)
        
        u_max = mdot_ha / (rho_ha * Ac) # free flow area velocity
        Re_Dc = rho_ha * u_max * Dc / mu_ha
        
        #Heat transfer
        j = 0.782 * pow(Re_Dc, -1.508 * (Fp / Dc) - 0.115) * pow(Ao / Atube, 3.085) * pow(Fp / Dc, 5.152)
        
        # Pressure drop
        if Re_Dc <= 1000:
            f = 0.02082 * pow(Re_Dc, -0.637) * pow(Ao / Atube, 4.75) * pow(Fp / Dc, 4.14)
        else:
            f = 2.486 * pow(Re_Dc, -0.461) * pow(Ao / Atube, -0.06) * pow(Fp / Dc, -0.0798)
        
        Pr = cp_ha * mu_ha / k_ha
        h_a = j * rho_ha * u_max * cp_ha / pow(Pr, 2.0 / 3.0) 
        
        Gc = mdot_ha / Ac #air mass flux
        DP = -Ao * Gc**2 * f / (Ac * rho_ha * 2.0) #airside pressure drop
        
        return h_a, DP

    def Kim1997_Wavy_Dry_geometry(self):
        '''        
        || -    xf    ->
        ^              ==                          ==
        |           ==  |  ==                  ==
        Pd       ==     |     ==            ==
        |     ==        |        ==     ==
        =  ==           s             ==  
                        |
                        |
                        |
                       ==                        ==
                    ==     ==                 ==
                 ==           ==           ==
              ==                 ==     ==
           ==                        ==  
        
         t: thickness of fin plate
         Pf: fin pitch (centerline-to-centerline distance between fins)
         Pd: indentation for waviness (not including fin thickness)
         s: fin spacing (free space between fins) = Pf-t
        
        
        
                     |--       Pl      -|
                    ___                 |
                  /     \               |
           =     |       |              |
           |      \ ___ /               |
           |                            |
           |                           ___      
           |                         /     \      |
          Pt                        |       |     D
           |                         \ ___ /      |
           |    
           |        ___
           |      /     \
           =     |       |
                  \ ___ /
        '''
        FPI = self.Fins_geometry.FPI        #Fins per inch
        FPM = FPI / 0.0254                  #Fins per meter [1/m]
        Fp = 1 / FPM                        #Fin pitch (distance between centerlines of fins)
        Ltube = self.Fins_geometry.Ltube
        Nfin = Ltube * FPM
        delta_f = self.Fins_geometry.t      #Fin thickness
        Fs = 1 / FPM - delta_f              #Fin spacing(m)
        Pd = self.Fins_geometry.Pd                   
        xf = self.Fins_geometry.xf                   
        Pl = self.Fins_geometry.Pl          #row spacing
        Pt = self.Fins_geometry.Pt          #tube spacing
        Do = self.Fins_geometry.Do          #tube outside diameter
        Nbank = self.Fins_geometry.Nbank    #number of tube rows
        Ltube = self.Fins_geometry.Ltube
        Nheight = self.Fins_geometry.Nheight
        Ntubes_bank = self.Fins_geometry.Ntubes_bank
        Dc = Do + 2 * delta_f
        Ac = Pt * Nheight * Ltube - delta_f * Ltube * FPM * (Pt * Nheight - Do * Ntubes_bank) - Ntubes_bank * Do * Ltube

        Atube = Ntubes_bank * Nbank * pi * Do * Ltube
                
        sec_theta = sqrt(xf*xf + Pd*Pd) / xf   
                
        Af = Nfin * 2.0 * (Pt * Nheight * Pl * Nbank * sec_theta - Ntubes_bank * Nbank * pi * Do * Do / 4)
            
        Ao = Af + Ntubes_bank * Nbank * pi * Do * (Ltube - Nfin * delta_f)
                                
        self.Ao = Ao
        self.Af_Ao_eff = Af / Ao
        X_T = Pt / 2
        X_D = sqrt(pow(Pl, 2) + pow(Pt, 2) / 4) / 2
        self.ro_eff = 1.27 * X_T * sqrt(X_D / X_T - 0.3)
        self.ri_eff = Do / 2
        self.rfr_eff = self.ro_eff / self.ri_eff
        self.phi_eff = (self.rfr_eff - 1) * (1 + 0.35 * log(self.rfr_eff))
        
        self.kim1997_Wavy_dry = ValuesClass()
        self.kim1997_Wavy_dry.Dc = Dc
        self.kim1997_Wavy_dry.Ac = Ac
        self.kim1997_Wavy_dry.Pt = Pt
        self.kim1997_Wavy_dry.Pl = Pl
        self.kim1997_Wavy_dry.Fp = Fp
        self.kim1997_Wavy_dry.Fs = Fs
        self.kim1997_Wavy_dry.Atube = Atube
        self.kim1997_Wavy_dry.Nbank = Nbank
        self.kim1997_Wavy_dry.Pd = Pd
        self.kim1997_Wavy_dry.xf = xf
        self.kim1997_Wavy_dry.Af = Af
        self.kim1997_Wavy_dry.delta_f = delta_f
        
    
    def Kim1997_Wavy_Dry(self,Tin, Tout, Win, Wout, Pin, Pout, mdot_ha):
        '''from "Heat Transfer and Friction Correlations for Wavy Plate 
            Fin-and-Tube Heat Exchangers", Kim et al (1997)
        '''
        
        Dc = self.kim1997_Wavy_dry.Dc
        Ac = self.kim1997_Wavy_dry.Ac
        Pt = self.kim1997_Wavy_dry.Pt
        Pl = self.kim1997_Wavy_dry.Pl
        Fp = self.kim1997_Wavy_dry.Fp
        Fs = self.kim1997_Wavy_dry.Fs
        Atube = self.kim1997_Wavy_dry.Atube
        Ao = self.Ao
        Nbank = self.kim1997_Wavy_dry.Nbank
        Pd = self.kim1997_Wavy_dry.Pd
        xf = self.kim1997_Wavy_dry.xf
        Afin = self.kim1997_Wavy_dry.Af
        delta_f = self.kim1997_Wavy_dry.delta_f
        Staggering = self.Fins_geometry.Staggering
        
        rho_ha, rho_da, mu_ha, k_ha, cp_da, cp_ha = self.calculate_air_props(Tin, Tout, Win, Wout, Pin, Pout)
        
        u_max = mdot_ha / (rho_ha * Ac) # free flow area velocity
        Re_Dc = rho_ha * u_max * Dc / mu_ha
        
        #heat transfer
        if Staggering in ['AaA', 'aAa'] or Nbank == 1:
            j3 = 0.394 * pow(Re_Dc, -0.357) * pow(Pt / Pl, -0.272) * pow(Fs / Dc, -0.205) * pow(xf / Pd, -0.558) * pow(Pd / Fs, -0.133)
            if (0 < Nbank <= 2) and (Re_Dc >= 1000):
                j = j3 * (0.978 - 0.01 * Nbank)
            elif (0 < Nbank <= 2) and (Re_Dc < 1000):
                j = j3 * (1.35 - 0.162 * Nbank)
            else:
                j = j3
                
        elif Staggering == 'inline':
            if (2 <= Nbank <= 4) and (Re_Dc >= 2000):
                j = 0.37 * pow(Re_Dc, -0.186) * pow(Fs / Dc, -0.045)
            elif (Nbank == 4) and (Re_Dc < 2000):
                j = 0.238 * pow(Re_Dc, -0.528) * pow(Fs / Dc, -0.635)
            elif (2 <= Nbank <= 3) and (Re_Dc < 2000):
                j4 = 0.238 * pow(Re_Dc, -0.528) * pow(Fs / Dc, -0.635)
                j = j4 * (1.35 - 0.097 * Nbank)
        else:
            raise
        #pressure drop
        if Staggering in ['AaA', 'aAa']:
            ff = 4.467 * pow(Re_Dc, -0.423) * pow(Pt / Pl, -1.08) * pow(Fs / Dc, -0.0339) * pow(xf / Pd, -0.672)
            
        elif Staggering == 'inline':
            ff = 0.571 * pow(Re_Dc, -0.601) * pow(Fs / Dc, -0.82)
        else:
            raise
                        
        # should have used Zukauskas and Ulinskas correlations, but it is 
        # extremely tidious calculations, instead, I used Jakob correlation
        Eu = 4 * (0.044 + 0.08 * Pt / (Dc * pow((Pt - Dc) / Dc, 0.43 + 1.13 * Dc / Pt))) * pow(Re_Dc, -0.15)
        
        ft =  Eu * Ac / (Nbank * Atube)       
        
        # should have used Zukauskas and Ulinskas correlations, but it is 
        # extremely tidious calculations, instead, I used Jakob correlation
        Eu = 4 * (0.044 + 0.08 * Pt / (Dc * pow((Pt - Dc) / Dc, 0.43 + 1.13 * Dc / Pt))) * pow(Re_Dc, -0.15)
        ft =  Eu * Ac / (Nbank * Atube)       
        
        f = ff * Afin / Ao + ft * (1 - Afin / Ao) * (1 - delta_f / Fp)

        Pr = cp_ha * mu_ha / k_ha
        h_a = j * rho_ha * u_max * cp_ha / pow(Pr, 2.0 / 3.0) 
        
        Gc = mdot_ha / Ac #air mass flux
        DP = -Ao * Gc**2 * f / (Ac * rho_ha * 2.0) #airside pressure drop
        
        return h_a, DP
