from __future__ import division, print_function, absolute_import
from math import pi, log, sqrt, exp, sin, tanh
import numpy as np
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
        if self.Fins_geometry.FinType == 'Louvered':
            if Wet:
                if not self.imposed_wet:
                    # options: 1, 2
                    self.corr_wet = 2
            elif not Wet:
                if not self.imposed_dry:
                    # options: 1
                    self.corr_dry = 1

        elif self.Fins_geometry.FinType == 'Wavy':
            if Wet:
                if not self.imposed_wet:
                    # options: 3, 4 (dry correlations)
                    self.corr_wet = 3
            elif not Wet:
                if not self.imposed_dry:
                    # options: 2, 3
                    self.corr_dry = 2

        else:
            raise
    
    # imposing a correlation functions
    def impose_wet(self,num):
        self.imposed_wet = True
        self.corr_wet = num
    
    def remove_impose_wet(self):
        self.imposed_wet = False

    def impose_dry(self,num):
        self.imposed_h_dry = True
        self.corr_dry = num
        
    def remove_impose_dry(self):
        self.imposed_dry = False
    
    # calculating h and DP
    def calculate_dry(self):
        if self.corr_dry == 1:
            ''' using Kim 2002 for j and f for louvered fins'''
            if self.geometry_calculated_dry == False:
                self.Kim2002_louvered_dry_geometry()
                self.geometry_calculated_dry = True
            h_a, DP = self.Kim2002_louvered_dry(self.Tin, self.Tout, self.Win,
                                                 self.Wout, self.Pin, self.Pout,
                                                 self.mdot_ha)
            return h_a, DP
        
        elif self.corr_dry == 2:
            ''' using Junqi 2007 for j and f for wavy fins'''
            if self.geometry_calculated_dry == False:
                self.Junqi2007_wavy_dry_geometry()
                self.geometry_calculated_dry = True
            h_a, DP = self.Junqi2007_wavy_dry(self.Tin, self.Tout, self.Win,
                                                 self.Wout, self.Pin, self.Pout,
                                                 self.mdot_ha)
            return h_a, DP
        
        elif self.corr_dry == 3:
            ''' using Dong 2013 for j and f for wavy fins'''
            if self.geometry_calculated_dry == False:
                self.Dong2013_wavy_dry_geometry()
                self.geometry_calculated_dry = True
            h_a, DP = self.Dong2013_wavy_dry(self.Tin, self.Tout, self.Win,
                                                 self.Wout, self.Pin, self.Pout,
                                                 self.mdot_ha)
            return h_a, DP
            
        else:
            raise
                    
    def calculate_wet(self):
        if self.corr_wet == 1:
            ''' using Kim 2002 for j and f for Louvered fins'''
            if self.geometry_calculated_wet == False:
                self.Kim2002_louvered_wet_geometry()
                self.geometry_calculated_wet = True
            h_a, DP = self.Kim2002_louvered_wet(self.Tin, self.Tout, self.Win,
                                                 self.Wout, self.Pin, self.Pout,
                                                 self.mdot_ha)
            return h_a, DP
        
        elif self.corr_wet == 2:
            ''' using Park 2009 for j and f for Louvered fins'''
            if self.geometry_calculated_wet == False:
                self.Park2009_louvered_wet_geometry()
                self.geometry_calculated_wet = True
            h_a, DP = self.Park2009_louvered_wet(self.Tin, self.Tout, self.Win,
                                                 self.Wout, self.Pin, self.Pout,
                                                 self.mdot_ha)
            return h_a, DP

        elif self.corr_wet == 3:
            ''' using Junqi 2007 for j and f for wavy fins'''
            if self.geometry_calculated_dry == False:
                self.Junqi2007_wavy_dry_geometry()
                self.geometry_calculated_dry = True
            h_a, DP = self.Junqi2007_wavy_dry(self.Tin, self.Tout, self.Win,
                                                 self.Wout, self.Pin, self.Pout,
                                                 self.mdot_ha)
            return h_a, DP
        
        elif self.corr_wet == 4:
            ''' using Dong 2013 for j and f for wavy fins'''
            if self.geometry_calculated_dry == False:
                self.Dong2013_wavy_dry_geometry()
                self.geometry_calculated_dry = True
            h_a, DP = self.Dong2013_wavy_dry(self.Tin, self.Tout, self.Win,
                                                 self.Wout, self.Pin, self.Pout,
                                                 self.mdot_ha)
            return h_a, DP

        else:
            raise
    
    # calculating efficiency
    def calculate_eff_wet(self, Tw_o, k_fin, h_a):
        bw_m = cair_sat(Tw_o) * 1000
        delta_f = self.Fins_geometry.t      #Fin thickness
        Lf = self.Fins_geometry.Lf
        Ls = self.Ls
        m = sqrt(2 * h_a / (k_fin * delta_f) * (1 + delta_f/Lf))
        mw = m * sqrt(bw_m / self.cp_da)
        eta_fin_wet = tanh(mw * Ls) / (mw * Ls)
        eta_o_wet = 1 - self.Af_Ao_eff * (1 - eta_fin_wet)
        return bw_m, eta_o_wet
    
    def calculate_eff_dry(self, k_fin, h_a):
        delta_f = self.Fins_geometry.t      #Fin thickness
        Lf = self.Fins_geometry.Lf
        Ls = self.Ls
        m = sqrt(2 * h_a / (k_fin * delta_f) * (1 + delta_f/Lf))
        eta_f = tanh(m * Ls) / (m * Ls)
        eta_o_dry = 1 - self.Af_Ao_eff * (1 - eta_f)
        
        return eta_o_dry
    
    # air properties calculation
    def calculate_air_props(self, Tin, Tout, Win, Wout, Pin, Pout):
        if self.Accurate == True:
            v_da_in = HAPropsSI('V', 'T', Tin, 'P', Pin, 'W', Win)
        else:
            v_da_in = pl.GetMoistAirVolume(Tin-273.15, Win, Pin)
        
        rho_ha_in = 1 / v_da_in * (1 + Win) #[kg_ha/m^3]
        rho_da_in = 1 / v_da_in #[kg_da/m^3]

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
    def Kim2002_louvered_dry_geometry(self):
        Lalpha =      self.Fins_geometry.Lalpha         #Louver angle, in degree
        lp =          self.Fins_geometry.lp             #Louver pitch
        delta =       self.Fins_geometry.t              #Fin thickness
        Lf =          self.Fins_geometry.Lf             #Fin length (flow depth)
        FPI =         self.Fins_geometry.FPI            #Fin per inch (fin density)
        Ntubes =      self.Fins_geometry.Ntubes         #Number of tubes
        Nbank =       self.Fins_geometry.Nbank          #Number of banks
        L3 =          self.Fins_geometry.Ltube          #length of a single tube    
        L2 =          self.Fins_geometry.Td             #Tube outside width (depth)
        Ht =          self.Fins_geometry.Ht             #Tube outside height (major diameter)
        b =           self.Fins_geometry.b              #Tube spacing       
        Llouv =       self.Fins_geometry.Llouv          #Louver cut length
        Npg =         self.Fins_geometry.Npg            #Number of fin rows

        FPM = FPI / 0.0254
        pf = 1 / FPM
        sf = sqrt(b**2 + pf**2) 
        pt = Ht + b
        lh = lp * sin(Lalpha*pi/180)
        L1 = Npg * b + Ntubes * Ht
        nf = L3/pf * Npg
        Ap = (2*(L2 - Ht) + pi * Ht)*L3 *Ntubes - 2*delta*L2*nf
        nlouv = (Lf/lp - 1)*nf
        Af = 2 * (sf*Lf + sf*delta)*nf + 2*Llouv*delta*nlouv
        At = (Af + Ap) * Nbank    
        Ac = b*L3*Npg - (delta*(sf-Llouv) +Llouv*lh)*nf
        Afr = L1*L3
        Dh = 4*Ac*L2*Nbank / At
        Fd = Lf * Nbank
        self.Kim2002_Louvered_dry = ValuesClass()
        self.Kim2002_Louvered_dry.pf = pf
        self.Kim2002_Louvered_dry.sf = sf
        self.Kim2002_Louvered_dry.pt = pt
        self.Kim2002_Louvered_dry.Af = Af
        self.Kim2002_Louvered_dry.At = At
        self.Kim2002_Louvered_dry.Ac = Ac
        self.Kim2002_Louvered_dry.Afr = Afr
        self.Kim2002_Louvered_dry.Dh = Dh
        self.Kim2002_Louvered_dry.lp = lp
        self.Kim2002_Louvered_dry.Lalpha = Lalpha
        self.Kim2002_Louvered_dry.b = b
        self.Kim2002_Louvered_dry.Fd = Fd
        self.Kim2002_Louvered_dry.Llouv = Llouv
        self.Kim2002_Louvered_dry.delta = delta
        self.Kim2002_Louvered_dry.Ht = Ht
        
        self.Ao = At
        self.Ls = sf/2 - delta
        self.Af_Ao_eff = Af / At
        
    def Kim2002_louvered_dry(self, Tin, Tout, Win, Wout, Pin, Pout, mdot_ha):
        '''
        from "Air-side thermal hydraulic performance of multi-louvered fin 
        aluminum heat exchangers", Kim and Bullard (2002)
        '''
        
        pf = self.Kim2002_Louvered_dry.pf
        sf = self.Kim2002_Louvered_dry.sf
        pt = self.Kim2002_Louvered_dry.pt
        Af = self.Kim2002_Louvered_dry.Af
        At = self.Kim2002_Louvered_dry.At
        Ac = self.Kim2002_Louvered_dry.Ac
        Afr = self.Kim2002_Louvered_dry.Afr
        Dh = self.Kim2002_Louvered_dry.Dh
        lp = self.Kim2002_Louvered_dry.lp
        Lalpha = self.Kim2002_Louvered_dry.Lalpha
        b = self.Kim2002_Louvered_dry.b
        Fd = self.Kim2002_Louvered_dry.Fd
        Llouv = self.Kim2002_Louvered_dry.Llouv
        delta = self.Kim2002_Louvered_dry.delta
        Ht = self.Kim2002_Louvered_dry.Ht

        rho_ha, rho_da, mu_ha, k_ha, cp_da, cp_ha = self.calculate_air_props(Tin, Tout, Win, Wout, Pin, Pout)

        #mass flux on air-side
        G = mdot_ha / Ac #[kg/m^2-s]
        #maximum velocity on air-side
        umax = G / rho_ha * Afr/Ac #[m/s]

        #Dimensionless Groups
        Pr = cp_ha * mu_ha / k_ha #Prandlt's number
        Re_Dh = G * Dh / mu_ha #Reynold's number on air-side
        Re_lp = rho_ha * umax * lp / mu_ha
        
        j = pow(Re_lp,-0.487) * pow((Lalpha/90.0),0.257) * pow(pf/lp,-0.13) * pow(b/lp,-0.29) * pow(Fd/lp,-0.235) * pow(Llouv/lp,0.68) * pow(pt/lp,-0.279) * pow(delta/lp,-0.05)
        h_a = j * rho_ha * umax * cp_ha / pow(Pr,2.0/3.0)
        
        #Fanning friction factor
        f = pow(Re_lp,-0.781) * pow((Lalpha/90.0),0.444) * pow(pf/lp,-1.682) * pow(b/lp,-1.22) * pow(Fd/lp,0.818) * pow(Llouv/lp,1.97)
        
        #Air-side pressure drop
        DP = -f * At/Ac * G**2 / (2.0*rho_ha)

        return h_a, DP

    def Kim2002_louvered_wet_geometry(self):
        Lalpha =      self.Fins_geometry.Lalpha         #Louver angle, in degree
        lp =          self.Fins_geometry.lp             #Louver pitch
        delta =       self.Fins_geometry.t              #Fin thickness
        Lf =          self.Fins_geometry.Lf             #Fin length (flow depth)
        FPI =         self.Fins_geometry.FPI            #Fin per inch (fin density)
        Ntubes =      self.Fins_geometry.Ntubes         #Number of tubes
        Nbank =       self.Fins_geometry.Nbank          #Number of banks
        L3 =          self.Fins_geometry.Ltube          #length of a single tube    
        L2 =          self.Fins_geometry.Td             #Tube outside width (depth)
        Ht =          self.Fins_geometry.Ht             #Tube outside height (major diameter)
        b =           self.Fins_geometry.b              #Tube spacing       
        Llouv =       self.Fins_geometry.Llouv          #Louver cut length
        Npg =         self.Fins_geometry.Npg            #Number of fin rows
        
        FPM = FPI / 0.0254
        pf = 1 / FPM
        sf = sqrt(b**2 + pf**2) 
        pt = Ht + b
        lh = lp * sin(Lalpha*pi/180)
        L1 = Npg * b + Ntubes * Ht
        nf = L3/pf * Npg
        Ap = (2*(L2 - Ht) + pi * Ht)*L3 *Ntubes - 2*delta*L2*nf
        nlouv = (Lf/lp - 1)*nf
        Af = 2 * (sf*Lf + sf*delta)*nf + 2*Llouv*delta*nlouv
        At = (Af + Ap) * Nbank    
        Ac = b*L3*Npg - (delta*(sf-Llouv) +Llouv*lh)*nf
        Afr = L1*L3
        Dh = 4*Ac*L2*Nbank / At
        Fd = Lf * Nbank
        self.Kim2002_Louvered_wet = ValuesClass()
        self.Kim2002_Louvered_wet.pf = pf
        self.Kim2002_Louvered_wet.pt = pt
        self.Kim2002_Louvered_wet.Af = Af
        self.Kim2002_Louvered_wet.At = At
        self.Kim2002_Louvered_wet.Ac = Ac
        self.Kim2002_Louvered_wet.Afr = Afr
        self.Kim2002_Louvered_wet.Dh = Dh
        self.Kim2002_Louvered_wet.lp = lp
        self.Kim2002_Louvered_wet.Lalpha = Lalpha
        self.Kim2002_Louvered_wet.b = b
        self.Kim2002_Louvered_wet.Fd = Fd
        self.Kim2002_Louvered_wet.Llouv = Llouv
        self.Kim2002_Louvered_wet.delta = delta
        self.Kim2002_Louvered_wet.Ht = Ht
        
        self.Ao = At
        self.Ls = sf/2 - delta
        self.Af_Ao_eff = Af / At
        
    def Kim2002_louvered_wet(self, Tin, Tout, Win, Wout, Pin, Pout, mdot_ha):
        '''
        from "Air-side performance of brazed aluminum heat exchangers under 
        dehumidifying conditions", Kim and Bullard (2002)
        '''
        
        pf = self.Kim2002_Louvered_wet.pf
        pt = self.Kim2002_Louvered_wet.pt
        Af = self.Kim2002_Louvered_wet.Af
        At = self.Kim2002_Louvered_wet.At
        Ac = self.Kim2002_Louvered_wet.Ac
        Afr = self.Kim2002_Louvered_wet.Afr
        Dh = self.Kim2002_Louvered_wet.Dh
        lp = self.Kim2002_Louvered_wet.lp
        Lalpha = self.Kim2002_Louvered_wet.Lalpha
        b = self.Kim2002_Louvered_wet.b
        Fd = self.Kim2002_Louvered_wet.Fd
        Llouv = self.Kim2002_Louvered_wet.Llouv
        delta = self.Kim2002_Louvered_wet.delta
        
        rho_ha, rho_da, mu_ha, k_ha, cp_da, cp_ha = self.calculate_air_props(Tin, Tout, Win, Wout, Pin, Pout)

        #mass flux on air-side
        G = mdot_ha / Ac #[kg/m^2-s]
        #maximum velocity on air-side
        umax = G / rho_ha * Afr/Ac #[m/s]

        #Dimensionless Groups
        Pr = cp_ha * mu_ha / k_ha #Prandlt's number
        Re_Dh = G * Dh / mu_ha #Reynold's number on air-side
        Re_lp = rho_ha * umax * lp / mu_ha
        
        j = pow(Re_lp,-0.512) * pow((Lalpha/90.0),0.25) * pow(pf/lp,-0.171) * pow(b/lp,-0.29) * pow(Fd/lp,-0.248) * pow(Llouv/lp,0.68) * pow(pt/lp,-0.275) * pow(delta/lp,-0.05)
        h_a = j * rho_ha * umax * cp_ha / pow(Pr,2.0/3.0)
        
        #Fanning friction factor    
        f = pow(Re_lp,-0.798) * pow((Lalpha/90.0),0.395) * pow(pf/lp,-2.635) * pow(b/lp,-1.22) * pow(Fd/lp,0.823) * pow(Llouv/lp,1.97)

        #Air-side pressure drop
        DP = -f * At/Ac * G**2 / (2.0*rho_ha)
                
        return h_a, DP
    
    def Park2009_louvered_wet_geometry(self):
        Lalpha =      self.Fins_geometry.Lalpha         #Louver angle, in degree
        lp =          self.Fins_geometry.lp             #Louver pitch
        delta =       self.Fins_geometry.t              #Fin thickness
        Lf =          self.Fins_geometry.Lf             #Fin length (flow depth)
        FPI =         self.Fins_geometry.FPI            #Fin per inch (fin density)
        Ntubes =      self.Fins_geometry.Ntubes         #Number of tubes
        Nbank =       self.Fins_geometry.Nbank          #Number of banks
        L3 =          self.Fins_geometry.Ltube          #length of a single tube    
        L2 =          self.Fins_geometry.Td             #Tube outside width (depth)
        Ht =          self.Fins_geometry.Ht             #Tube outside height (major diameter)
        b =           self.Fins_geometry.b              #Tube spacing       
        Llouv =       self.Fins_geometry.Llouv          #Louver cut length
        Npg =         self.Fins_geometry.Npg            #Number of fin rows

        FPM = FPI / 0.0254
        pf = 1 / FPM
        sf = sqrt(b**2 + pf**2) 
        pt = Ht + b
        lh = lp * sin(Lalpha*pi/180)
        L1 = Npg * b + Ntubes * Ht
        nf = L3/pf * Npg
        Tp = b + Ht
        Ap = (2*(L2 - Ht) + pi * Ht)*L3 *Ntubes - 2*delta*L2*nf
        nlouv = (Lf/lp - 1)*nf
        Af = 2 * (sf*Lf + sf*delta)*nf + 2*Llouv*delta*nlouv
        At = (Af + Ap) * Nbank    
        Ac = b*L3*Npg - (delta*(sf-Llouv) +Llouv*lh)*nf
        Afr = L1*L3
        F1 = sqrt(b*b + pf * pf)
        Dh = 4*Ac*L2*Nbank / At
        Fd = Lf * Nbank
        
        self.Park2009_Louvered_wet = ValuesClass()
        self.Park2009_Louvered_wet.pf = pf
        self.Park2009_Louvered_wet.Af = Af
        self.Park2009_Louvered_wet.At = At
        self.Park2009_Louvered_wet.Ac = Ac
        self.Park2009_Louvered_wet.Afr = Afr
        self.Park2009_Louvered_wet.Dh = Dh
        self.Park2009_Louvered_wet.lp = lp
        self.Park2009_Louvered_wet.F1 = F1
        self.Park2009_Louvered_wet.Tp = Tp
        self.Park2009_Louvered_wet.Lalpha = Lalpha
        self.Park2009_Louvered_wet.Llouv = Llouv
        self.Park2009_Louvered_wet.Fd = Fd
        
        self.Ao = At
        self.Ls = sf/2 - delta
        self.Af_Ao_eff = Af / At
        
    def Park2009_louvered_wet(self, Tin, Tout, Win, Wout, Pin, Pout, mdot_ha):
        '''
        from "The Air-Side Thermal-Hydraulic Performance of Flat-Tube Heat 
        Exchangers With Louvered, Wavy, and Plain Fins Under Dry and Wet 
        Conditions", Park and Jacobi (2009)
        '''
        
        pf = self.Park2009_Louvered_wet.pf
        Af = self.Park2009_Louvered_wet.Af
        At = self.Park2009_Louvered_wet.At
        Ac = self.Park2009_Louvered_wet.Ac
        Afr = self.Park2009_Louvered_wet.Afr
        Dh = self.Park2009_Louvered_wet.Dh
        lp = self.Park2009_Louvered_wet.lp
        F1 = self.Park2009_Louvered_wet.F1
        Tp = self.Park2009_Louvered_wet.Tp
        Lalpha = self.Park2009_Louvered_wet.Lalpha        
        Llouv = self.Park2009_Louvered_wet.Llouv
        Fd = self.Park2009_Louvered_wet.Fd

        rho_ha, rho_da, mu_ha, k_ha, cp_da, cp_ha = self.calculate_air_props(Tin, Tout, Win, Wout, Pin, Pout)

        #mass flux on air-side
        G = mdot_ha / Ac #[kg/m^2-s]
        #maximum velocity on air-side
        umax = G / rho_ha * Afr/Ac #[m/s]

        #Dimensionless Groups
        Pr = cp_ha * mu_ha / k_ha #Prandlt's number
        Re_lp = rho_ha * umax * lp / mu_ha
        
        
        j = 0.4260 * pow(Re_lp, -0.3149) * pow(lp / pf, 0.6705) *  pow(sin(Lalpha*pi/180), 0.3489) * pow(Llouv / F1, 0.5123) * pow(Fd / pf, -0.2698) * pow(F1 / Tp, -0.2845)
        h_a = j * rho_ha * umax * cp_ha / pow(Pr,2.0/3.0)
        
        #Fanning friction factor    
        f = 0.074 + 152.7 * pow(Re_lp, -1.116) * pow(lp / pf, 2.242) * pow(sin(Lalpha*pi/180), 0.968) * pow(F1 / Tp, 1.716)
        #Air-side pressure drop
        DP = -f * At/Ac * G**2 / (2.0*rho_ha)
        
        return h_a, DP

    def Junqi2007_wavy_dry_geometry(self):
        delta =       self.Fins_geometry.t              #Fin thickness
        Lf =          self.Fins_geometry.Lf             #Fin length (flow depth)
        FPI =         self.Fins_geometry.FPI            #Fin per inch (fin density)
        Ntubes =      self.Fins_geometry.Ntubes         #Number of tubes
        Nbank =       self.Fins_geometry.Nbank          #Number of banks
        L3 =          self.Fins_geometry.Ltube          #length of a single tube    
        L2 =          self.Fins_geometry.Td             #Tube outside width (depth)
        Ht =          self.Fins_geometry.Ht             #Tube outside height (major diameter)
        b =           self.Fins_geometry.b              #Tube spacing       
        Npg =         self.Fins_geometry.Npg            #Number of fin rows
        xf =          self.Fins_geometry.xf             #Half wave length
        pd =          self.Fins_geometry.pd             #2 * wave amplitube
        
        FPM = FPI / 0.0254
        pf = 1 / FPM
        sf = sqrt(b**2 + pf**2) 
        L1 = Npg * b + Ntubes * Ht
        nf = L3/pf * Npg
        Ap = (2*(L2 - Ht) + pi * Ht)*L3 *Ntubes - 2*delta*L2*nf
        sec_theta = sqrt(xf*xf + pd*pd) / xf   
        Af = 2 * (sf*Lf * sec_theta + sf*delta)*nf 
        At = (Af + Ap) * Nbank    
        Ac = b*L3*Npg - (delta * sf)*nf
        Afr = L1*L3
        A = pd / 2
        L = 2 * xf
        De = 2 * b * pf / (b + pf)
        Fd = Lf * Nbank
        
        self.Junqi2007_Wavy_dry = ValuesClass()
        self.Junqi2007_Wavy_dry.pf = pf
        self.Junqi2007_Wavy_dry.Af = Af
        self.Junqi2007_Wavy_dry.At = At
        self.Junqi2007_Wavy_dry.Ac = Ac
        self.Junqi2007_Wavy_dry.Afr = Afr
        self.Junqi2007_Wavy_dry.Fd = Fd
        self.Junqi2007_Wavy_dry.L = L
        self.Junqi2007_Wavy_dry.A = A
        self.Junqi2007_Wavy_dry.b = b
        self.Junqi2007_Wavy_dry.De = De
        
        self.Ao = At
        self.Ls = b / 2
        self.Af_Ao_eff = Af / At
        
    def Junqi2007_wavy_dry(self, Tin, Tout, Win, Wout, Pin, Pout, mdot_ha):
        '''
        from "The Air-Side Thermal-Hydraulic Performance of Flat-Tube Heat 
        Exchangers With Louvered, Wavy, and Plain Fins Under Dry and Wet 
        Conditions", Park and Jacobi (2009)
        '''
        
        Fp = self.Junqi2007_Wavy_dry.pf
        Af = self.Junqi2007_Wavy_dry.Af
        At = self.Junqi2007_Wavy_dry.At
        Ac = self.Junqi2007_Wavy_dry.Ac
        Afr = self.Junqi2007_Wavy_dry.Afr
        L = self.Junqi2007_Wavy_dry.L
        A = self.Junqi2007_Wavy_dry.A
        Fh = self.Junqi2007_Wavy_dry.b
        Ld = self.Junqi2007_Wavy_dry.Fd
        De = self.Junqi2007_Wavy_dry.De

        rho_ha, rho_da, mu_ha, k_ha, cp_da, cp_ha = self.calculate_air_props(Tin, Tout, Win, Wout, Pin, Pout)

        #mass flux on air-side
        G = mdot_ha / Ac #[kg/m^2-s]
        #maximum velocity on air-side
        umax = G / rho_ha * Afr/Ac #[m/s]

        #Dimensionless Groups
        Pr = cp_ha * mu_ha / k_ha #Prandlt's number
        Re_De = rho_ha * umax * De / mu_ha
        
        j = 0.0836 * pow(Re_De, -0.2309) * pow(Fp / Fh, 0.1284) * pow(Fp / (2*A), -0.153) * pow(Ld / L, -0.326)
        h_a = j * rho_ha * umax * cp_ha / pow(Pr,2.0/3.0)
        
        #Fanning friction factor    
        f = 1.16 * pow(Re_De, -0.309) * pow(Fp / Fh, 0.3703) * pow(Fp / (2*A), -0.25) * pow(Ld / L, -0.1152)
        #Air-side pressure drop
        DP = -f * At/Ac * G**2 / (2.0*rho_ha)
        
        return h_a, DP

    def Dong2013_wavy_dry_geometry(self):
        delta =       self.Fins_geometry.t              #Fin thickness
        Lf =          self.Fins_geometry.Lf             #Fin length (flow depth)
        FPI =         self.Fins_geometry.FPI            #Fin per inch (fin density)
        Ntubes =      self.Fins_geometry.Ntubes         #Number of tubes
        Nbank =       self.Fins_geometry.Nbank          #Number of banks
        L3 =          self.Fins_geometry.Ltube          #length of a single tube    
        L2 =          self.Fins_geometry.Td             #Tube outside width (depth)
        Ht =          self.Fins_geometry.Ht             #Tube outside height (major diameter)
        b =           self.Fins_geometry.b              #Tube spacing       
        Npg =         self.Fins_geometry.Npg            #Number of fin rows
        xf =          self.Fins_geometry.xf             #Half wave length
        pd =          self.Fins_geometry.pd             #2 * wave amplitube
        
        FPM = FPI / 0.0254
        pf = 1 / FPM
        sf = sqrt(b**2 + pf**2) 
        L1 = Npg * b + Ntubes * Ht
        nf = L3/pf * Npg
        Ap = (2*(L2 - Ht) + pi * Ht)*L3 *Ntubes - 2*delta*L2*nf
        sec_theta = sqrt(xf*xf + pd*pd) / xf   
        Af = 2 * (sf*Lf * sec_theta + sf*delta)*nf 
        At = (Af + Ap) * Nbank    
        Ac = b*L3*Npg - (delta * sf)*nf
        Afr = L1*L3
        A = pd / 2
        L = 2 * xf
        De = 2 * b * pf / (b + pf)
        Fd = Lf * Nbank
        
        self.Dong2013_Wavy_dry = ValuesClass()
        self.Dong2013_Wavy_dry.pf = pf
        self.Dong2013_Wavy_dry.Af = Af
        self.Dong2013_Wavy_dry.At = At
        self.Dong2013_Wavy_dry.Ac = Ac
        self.Dong2013_Wavy_dry.Afr = Afr
        self.Dong2013_Wavy_dry.Fd = Fd
        self.Dong2013_Wavy_dry.L = L
        self.Dong2013_Wavy_dry.A = A
        self.Dong2013_Wavy_dry.b = b
        self.Dong2013_Wavy_dry.De = De
        
        self.Ao = At
        self.Ls = b / 2
        self.Af_Ao_eff = Af / At
        
    def Dong2013_wavy_dry(self, Tin, Tout, Win, Wout, Pin, Pout, mdot_ha):
        '''
        from "The Air-Side Thermal-Hydraulic Performance of Flat-Tube Heat 
        Exchangers With Louvered, Wavy, and Plain Fins Under Dry and Wet 
        Conditions", Park and Jacobi (2009)
        '''
        
        Fp = self.Dong2013_Wavy_dry.pf * 2
        Af = self.Dong2013_Wavy_dry.Af
        At = self.Dong2013_Wavy_dry.At
        Ac = self.Dong2013_Wavy_dry.Ac
        Afr = self.Dong2013_Wavy_dry.Afr
        L = self.Dong2013_Wavy_dry.L
        A = self.Dong2013_Wavy_dry.A
        Fh = self.Dong2013_Wavy_dry.b
        Ld = self.Dong2013_Wavy_dry.Fd
        De = self.Dong2013_Wavy_dry.De
        k_fin = self.Fins_geometry.k_fin

        rho_ha, rho_da, mu_ha, k_ha, cp_da, cp_ha = self.calculate_air_props(Tin, Tout, Win, Wout, Pin, Pout)

        #mass flux on air-side
        G = mdot_ha / Ac #[kg/m^2-s]
        #maximum velocity on air-side
        umax = G / rho_ha * Afr/Ac #[m/s]

        #Dimensionless Groups
        Pr = cp_ha * mu_ha / k_ha #Prandlt's number
        Re_De = rho_ha * umax * De / mu_ha
        
        Nu = 0.0864 * pow(Re_De, 0.914) * pow(Fp / Fh, -0.301) * pow((2*A) / L, 0.7875) * pow(Ld / L, -0.254) * pow((2*A) / Ld, -0.226)
        h_a = Nu * k_fin / De
        
        #Fanning friction factor    
        f = 15.46 * pow(Re_De, -0.416) * pow(Fp / Fh, -0.138) * pow((2*A) / L, 1.098) * pow(Ld / L, -0.45) * pow((2*A) / Ld, -0.506)
        #Air-side pressure drop
        DP = -f * At/Ac * G**2 / (2.0*rho_ha)
        
        return h_a, DP
