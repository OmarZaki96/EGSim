from __future__ import division, print_function, absolute_import
from math import log,exp,floor,ceil,pi,sqrt,cos, asin, sin, tan
from CoolProp.CoolProp import HAPropsSI, PropsSI, cair_sat
from backend.FinTubeHEXFins import FinsClass
from backend.FinTubeHEXCorrelations import CorrelationsClass
from backend.Tools import ValidateFields
import CoolProp as CP
from scipy.optimize import brentq
import numpy as np
import psychrolib as pl

pl.SetUnitSystem(pl.SI)

class ValuesClass():
    pass

class FinTubeCircuitClass():
    def __init__(self,**kwargs):
        self.Geometry = ValuesClass()
        self.Fins = FinsClass()
        self.Fins.calculated_before = False
        self.Thermal = ValuesClass()
        self.Correlations = CorrelationsClass()
        self.__dict__.update(kwargs)
        self.geometry_calculated = False
        self.terminate = False
    
    def update(self,**kwargs):
        self.__dict__.update(kwargs)
        
    def OutputList(self):
        """
            Return a list of parameters for this component for further output
            
            It is a list of tuples, and each tuple is formed of items:
                [0] Description of value
                [1] Units of value
                [2] The value itself
        """
        Output_list_HEX_Geometry_basic = [
            ('Tube outer diameter','m',self.Geometry.OD),
            ]

        if hasattr(self.Geometry,'ID'):
            Output_list_HEX_Geometry_optional = [
                ('Tube inner diameter','m',self.Geometry.ID),
                ]
        if hasattr(self.Geometry,'d'):
            Output_list_HEX_Geometry_optional = [
                ('','',''),
                ('Tube t','m',self.Geometry.t),
                ('Tube e','m',self.Geometry.e),
                ('Tube gama','m',self.Geometry.gama),
                ('Tube d','m',self.Geometry.d),
                ('Tube n','-',self.Geometry.n),
                ('Tube beta','degrees',self.Geometry.beta),
                ]
        Output_list_HEX_Geometry_basic += Output_list_HEX_Geometry_optional
        Output_list_HEX_Geometry_basic += [
            ('','',''),
            ('Tube length','m',self.Geometry.Ltube),
            ('Number of tubes per bank per circuit','-',self.Geometry.Ntubes_per_bank_per_subcircuit),
            ('Number of banks','-',self.Geometry.Nbank),
            ('Number of duplicate parallel circuits','-',self.Geometry.Nsubcircuits),
            ('Stagerring style','-',self.Geometry.Staggering),
            ('Tubes type','-',self.Geometry.Tubes_type),
            ('Tubes spacing in flow direction','m',self.Geometry.Pl),
            ('Tubes spacing orthogonal to flow direction','m',self.Geometry.Pt),
            ('','',''),
            ('Fin type','-',self.Geometry.FinType),
            ('Fins-per-Inch','1/in',self.Geometry.FPI),
            ('Fin thickness','m',self.Geometry.Fin_t),
            ('','',''),
            ]

        Output_list_HEX_Geometry_calculated = [
            ('','',''),
            ('Number of tubes per circuit','-',self.Geometry.Ntubes_per_subcircuit),
            ('Length of circuit','m',self.Geometry.Lsubcircuit),
            ('','',''),
            ('Inner heat transfer area (refrigerant side)','m^2',self.Geometry.A_r),
            ('Outer heat transfer area (air side)','m^2',self.Geometry.A_a),
            ('','',''),
            ('Circuit face area','m^2',self.Geometry.A_face),
            ('','',''),
            ('Inner flow area (cross sectional area)','m^2',self.Geometry.A_CS),
            ]

        Output_list_HEX_correction_factors = [
            ('','',''),
            ('Refrigerant superheated HTC correction factor','-',self.Thermal.h_r_superheat_tuning),
            ('Refrigerant subcooled HTC correction factor','-',self.Thermal.h_r_subcooling_tuning),
            ('Refrigerant two-phase HTC correction factor','-',self.Thermal.h_r_2phase_tuning),
            ('Refrigerant superheated pressure drop correction factor','-',self.Thermal.DP_r_superheat_tuning),
            ('Refrigerant subcooled pressure drop correction factor','-',self.Thermal.DP_r_subcooling_tuning),
            ('Refrigerant two-phase pressure drop correction factor','-',self.Thermal.DP_r_2phase_tuning),
            ('Air dry HTC correction factor','-',self.Thermal.h_a_dry_tuning),
            ('Air wet HTC correction factor','-',self.Thermal.h_a_wet_tuning),
            ('Air dry pressure drop correction factor','-',self.Thermal.DP_a_dry_tuning),
            ('Air wet pressure drop correction factor','-',self.Thermal.DP_a_wet_tuning),
            ('','',''),
            ]

        Output_list_HEX_Thermal_air = [
            ('','',''),
            ('','',''),
            ('Air inlet humid volume flow rate','m^3/s',self.Results.Vdot_ha_in),
            ('Air inlet temperature','C',self.Thermal.Tin_a-273.15),
            ('Air inlet humidity ratio','kg/kg',self.Thermal.Win_a),
            ('','',''),
            ('Air outlet humid volume flow rate','m^3/s',self.Results.Vdot_ha_out),
            ('Air outlet temperature','C',self.Results.Tout_a-273.15),
            ('Air outlet humidity ratio','kg/kg',self.Results.Wout_a),
            ('','',''),
            ('Air average face velocity','m/s',self.Results.V_air_average),
            ('','',''),
            ('Air heat transfer coefficient','W/m^2.K',self.Results.h_a),
            ('Air fin overall efficiency','%',self.Results.eta_a*100),
            ('','',''),
            ('Air pressure drop','Pa',self.Results.DP_a),
            ('','',''),
            ('Air inlet humid mass flow rate','kg/s',self.Thermal.mdot_ha),
            ('Air dry mass flow rate','kg/s',self.Thermal.mdot_ha/(1+self.Thermal.Win_a)),
            ]
        Output_list_HEX_Thermal_refrigerant = [
            ('','',''),
            ('','',''),
            ('Refrigerant inlet temperature','C',self.Results.Tin_r-273.15),
            ('Refrigerant inlet pressure','Pa',self.Results.Pin_r),
            ('Refrigerant inlet enthalpy','J/Kg',self.Results.hin_r),
            ('Refrigerant inlet quality','-',self.Results.xin_r),
            ('','',''),
            ('Refrigerant outlet temperature','C',self.Results.Tout_r-273.15),
            ('Refrigerant outlet pressure','Pa',self.Results.Pout_r),
            ('Refrigerant outlet enthalpy','J/Kg',self.Results.hout_r),
            ('Refrigerant outlet quality','-',self.Results.xout_r),
            ('','',''),
            ('Refrigerant pressure drop','Pa',self.Results.DP_r),
            ('Refrigerant pressure drop in subcool region','Pa',self.Results.DP_r_subcool),
            ('Refrigerant pressure drop in 2phase region','Pa',self.Results.DP_r_2phase),
            ('Refrigerant pressure drop in superheat region','Pa',self.Results.DP_r_superheat),
            ('','',''),
            ]
        Output_list_HEX_Thermal_HEX = [
            ('','',''),
            ('Heat transfer','W',self.Results.Q),
            ('Heat transfer in subcool region','W',self.Results.Q_subcool),
            ('Heat transfer in 2phase region','W',self.Results.Q_2phase),
            ('Heat transfer in superheat region','W',self.Results.Q_superheat),
            ('','',''),
            ('UA','W/K',self.Results.UA),
            ('UA in subcool region','W/K',self.Results.UA_subcool),
            ('UA in 2phase region','W/K',self.Results.UA_2phase),
            ('UA in superheat region','W/K',self.Results.UA_superheat),
            ('','',''),
            ('Refrigerant subcool HTC','W/m^2.K',self.Results.h_r_subcool),
            ('Refrigerant two-phase HTC','W/m^2.K',self.Results.h_r_2phase),
            ('Refrigerant superheat HTC','W/m^2.K',self.Results.h_r_superheat),
            ('','',''),
            ('Condensed water from air','Kg/s',self.Results.water_cond),
            ('Condensed water from air in subcool region','Kg/s',self.Results.water_cond_subcool),
            ('Condensed water from air in 2phase region','Kg/s',self.Results.water_cond_2phase),
            ('Condensed water from air in superheat region','Kg/s',self.Results.water_cond_superheat),
            ('','',''),
            ('Charge','Kg',self.Results.Charge),
            ('Charge in subcool region','Kg',self.Results.Charge_subcool),
            ('Charge in 2phase region','Kg',self.Results.Charge_2phase),
            ('Charge in superheat region','Kg',self.Results.Charge_superheat),
            ('','',''),
            ('Sensible heat factor of HEX','-',self.Results.SHR),
            ('','',''),
            ('Subcool region fraction','%',self.Results.w_subcool*100),
            ('2phase region fraction','%',self.Results.w_2phase*100),
            ('Superheat region fraction','%',self.Results.w_superheat*100),
            ('','',''),
            ('','',''),
            ]
        if hasattr(self.Results,'SH') and self.Results.SH != None:
            Output_list_HEX_Thermal_SH = [
                ('Superheat in HEX','K',self.Results.SH)
                ]
        else:
            Output_list_HEX_Thermal_SH = [
                ('Superheat in HEX','K','-')
                ]
        if hasattr(self.Results,'SC') and self.Results.SC != None:
            Output_list_HEX_Thermal_SC = [
                ('Subcool in HEX','K',self.Results.SC)
                ]
        else:
            Output_list_HEX_Thermal_SC = [
                ('Subcool in HEX','K','-')
                ]

        if hasattr(self.Results,'Tdew_in') and self.Results.Tdew_in != None:
            Output_list_HEX_Thermal_Tdew_in = [
                ('','',''),
                ('Inlet refrigerant saturation temperature in 2phase','C',self.Results.Tdew_in-273.15)
                ]
        else:
            Output_list_HEX_Thermal_Tdew_in = [
                ('','',''),
                ('Inlet refrigerant saturation temperature in 2phase','-','-')
                ]

        if hasattr(self.Results,'Tdew_out') and self.Results.Tdew_out != None:
            Output_list_HEX_Thermal_Tdew_out = [
                ('Outlet refrigerant saturation temperature in 2phase','C',self.Results.Tdew_out-273.15)
                ]   
        else:
            Output_list_HEX_Thermal_Tdew_out = [
                ('Outlet refrigerant saturation temperature in 2phase','-','-')
                ]   
        
        if not hasattr(self.Correlations,"h_corr_subcool"):
            self.Correlations.h_corr_subcool = 0
        if not hasattr(self.Correlations,"dPdz_f_corr_subcool"):
            self.Correlations.dPdz_f_corr_subcool = 0
        if not hasattr(self.Correlations,"h_corr_superheat"):
            self.Correlations.h_corr_superheat = 0
        if not hasattr(self.Correlations,"dPdz_f_corr_superheat"):
            self.Correlations.dPdz_f_corr_superheat = 0
        if not hasattr(self.Correlations,"h_corr_2phase"):
            self.Correlations.h_corr_2phase = 0
        if not hasattr(self.Correlations,"dPdz_f_corr_2phase"):
            self.Correlations.dPdz_f_corr_2phase = 0
        Output_list_Corr_names = [
                                  ("","",""),
                                  ("Subcooled HTC Correlation","",self.Correlations.HTC_1phase_corr_names[self.Correlations.h_corr_subcool]),
                                  ("Subcooled Pressure Drop Correlation","",self.Correlations.DP_1phase_corr_names[self.Correlations.dPdz_f_corr_subcool]),
                                  ("Two-phase HTC Correlation","",self.Correlations.HTC_2phase_corr_names[self.Correlations.h_corr_2phase]),
                                  ("Two-phase Pressure Drop Correlation","",self.Correlations.DP_2phase_corr_names[self.Correlations.dPdz_f_corr_2phase]),
                                  ("Superheated HTC Correlation","",self.Correlations.HTC_1phase_corr_names[self.Correlations.h_corr_superheat]),
                                  ("Superheated Pressure Drop Correlation","",self.Correlations.DP_1phase_corr_names[self.Correlations.dPdz_f_corr_superheat]),
                                  ("","",""),
                                  ]
        
        Output_list = Output_list_HEX_Geometry_basic +\
                Output_list_HEX_Geometry_calculated +\
                    Output_list_HEX_correction_factors +\
                        Output_list_HEX_Thermal_air +\
                            Output_list_HEX_Thermal_refrigerant +\
                                Output_list_HEX_Thermal_HEX +\
                                    Output_list_HEX_Thermal_SH +\
                                        Output_list_HEX_Thermal_SC +\
                                            Output_list_HEX_Thermal_Tdew_in +\
                                                Output_list_HEX_Thermal_Tdew_out +\
                                                    Output_list_Corr_names
                                                
        return Output_list
                
    def check_input(self):
        '''
        A function to check for HEX inputs before calculating.

        Returns
        -------
        None.

        '''
        reqFields=[
               ('OD',float,0,1000000000),
               ('Ltube',float,0,10000000),
               ('Ntubes_per_bank_per_subcircuit',int,0.1,10000000),
               ('Nbank',int,0.1,10000000),
               ('Nsubcircuits',int,0.1,10000000),               
               ('Staggering',str,None,None),
               ('Tubes_type',str,None,None),
               ('Pl',float,0,10000000),
               ('Pt',float,0,10000000),
               ('Connections',list,None,None),
               ('FinType',str,None,None),
               ('Fin_t',float,0,10000000),
               ('FPI',float,0,10000000),
               ]
        optFields=['ID','t','e','n','d','w', 'gama','beta','Ntubes_per_subcircuit', 'Nheight', 'Lsubcircuit', 'Ntubes', 'Total_length', 'Vol','Dh','FarBendRadius','Nair_grid_vertical', 'inner_circum', 'A_CS','A_r','A_a','e_D','Fin_Pd','Fin_xf','Fin_Lh','Fin_Lp','Fin_Sn','Fin_Ss','Fin_Sh','Di', 'FD', 'A_fin', 'Afa', 'Afn', 'Afc', 'Ac', 'An', 'Aa','Sub_HX_matrix','A_face']
        ValidateFields(self.Geometry.__dict__,reqFields,optFields)
        reqFields=[
               ('Tin_a',float,0,1000000000),
               ('Win_a',float,0,1000000000),
               ('Pin_a',float,0,1000000000),
               ('Pin_r',float,0.01,100000000000),
               ('hin_r',float,1,1000000000000),
               ('mdot_r',float,0.000001,2000),
               ('Nsegments',int,0.1,50000),
               ('kw',float,0.00000001,1000000000),
               ('k_fin',float,0,10000000),
               ]
        optFields=['DP_a_dry_tuning','DP_a_wet_tuning','h_a_wet_tuning','h_a_dry_tuning','DP_r_2phase_tuning','DP_r_subcooling_tuning','DP_r_superheat_tuning','h_r_2phase_tuning','h_r_subcooling_tuning','Rw', 'NsegmentsActual','FinsOnce','Tin_r','h_r_superheat_tuning','Vdot_ha','mdot_ha','Vel_dist','HTC_superheat_Corr', 'HTC_subcool_Corr', 'DP_subcool_Corr', 'DP_superheat_Corr', 'HTC_2phase_Corr', 'DP_2phase_Corr', 'DP_Accel_Corr','rho_2phase_Corr','Air_dry_Corr','Air_wet_Corr','h_a_wet_on','DP_a_wet_on']
        ValidateFields(self.Thermal.__dict__,reqFields,optFields)
        
        if hasattr(self.Thermal,'Vel_dist'):
            self.Thermal.Vel_dist = np.array(self.Thermal.Vel_dist)
            assert(self.Thermal.Vel_dist.shape[0] == self.Geometry.Ntubes_per_bank_per_subcircuit)
        elif hasattr(self.Thermal,'Vdot_ha'):
            pass
        elif hasattr(self.Thermal,'mdot_ha'):
            pass
        else:
            raise Exception("You have to define volume flow rate, mass flow rate or velocity distribution")
        
        if hasattr(self.Thermal,'HTC_superheat_Corr'):
            if self.Thermal.HTC_superheat_Corr != 0:
                self.Correlations.impose_h_superheat(int(self.Thermal.HTC_superheat_Corr))
        if hasattr(self.Thermal,'HTC_subcool_Corr'):
            if self.Thermal.HTC_subcool_Corr != 0:
                self.Correlations.impose_h_subcool(int(self.Thermal.HTC_subcool_Corr))
        if hasattr(self.Thermal,'DP_superheat_Corr'):
            if self.Thermal.DP_superheat_Corr != 0:
                self.Correlations.impose_dPdz_f_superheat(int(self.Thermal.DP_superheat_Corr))
        if hasattr(self.Thermal,'DP_subcool_Corr'):
            if self.Thermal.DP_subcool_Corr != 0:
                self.Correlations.impose_dPdz_f_subcool(int(self.Thermal.DP_subcool_Corr))
        if hasattr(self.Thermal,'HTC_2phase_Corr'):
            if self.Thermal.HTC_2phase_Corr != 0:
                self.Correlations.impose_h_2phase(int(self.Thermal.HTC_2phase_Corr))
        if hasattr(self.Thermal,'DP_2phase_Corr'):
            if self.Thermal.DP_2phase_Corr != 0:
                self.Correlations.impose_dPdz_f_2phase(int(self.Thermal.DP_2phase_Corr))
        if hasattr(self.Thermal,'DP_Accel_Corr'):
            if self.Thermal.DP_Accel_Corr != 0:
                self.Correlations.impose_dP_a(int(self.Thermal.DP_Accel_Corr))
        if hasattr(self.Thermal,'rho_2phase_Corr'):
            if self.Thermal.rho_2phase_Corr != 0:
                self.Correlations.impose_rho_2phase(int(self.Thermal.rho_2phase_Corr))
        if hasattr(self.Thermal,'Air_dry_Corr'):
            if self.Thermal.Air_dry_Corr != 0:
                self.Fins.impose_dry(int(self.Thermal.Air_dry_Corr))
        if hasattr(self.Thermal,'Air_wet_Corr'):
            if self.Thermal.Air_wet_Corr != 0:
                self.Fins.impose_wet(int(self.Thermal.Air_wet_Corr))

        if self.Geometry.Pl <= self.Geometry.OD:
            if not hasattr(self,"Solver_Error"):
                self.Solver_Error = "Longitudinal tube pitch can not be less than tube outer diameter in "
            raise
            
        if self.Geometry.Pt <= self.Geometry.OD:
            if not hasattr(self,"Solver_Error"):
                self.Solver_Error = "Transverse tube pitch can not be less than tube outer diameter in "
            raise
        
        if self.Geometry.FPI >= 0.0254 / self.Geometry.Fin_t / 2.0:
            if not hasattr(self,"Solver_Error"):
                self.Solver_Error = "FPI is too large and not possible in "
            raise
            
        if self.Geometry.Tubes_type == 'Smooth':
            if self.Geometry.OD <= self.Geometry.ID:
                if not hasattr(self,"Solver_Error"):
                    self.Solver_Error = "Inner diameter can not be larger than or equal outer diameter in "
                raise
            
        if hasattr(self.Geometry,"Sub_HX_matrix"):
            for row in self.Geometry.Sub_HX_matrix:
                if row[1] > row[2]:
                    if not hasattr(self,"Solver_Error"):
                        self.Solver_Error = "Sub Heat exchanger data is wrong. Tube number "+str(row[0])+ " has a start point larger than end point in "
                    raise

                if row[2] > self.Geometry.Ltube:
                    if not hasattr(self,"Solver_Error"):
                        self.Solver_Error = "Sub Heat exchanger data is wrong. Tube number "+str(row[0])+ " has an end point larger than tube original length in "
                    raise
                
                Ntubes_per_subcircuit = self.Geometry.Ntubes_per_bank_per_subcircuit * self.Geometry.Nbank
                
                if row[0] > Ntubes_per_subcircuit:
                    if not hasattr(self,"Solver_Error"):
                        self.Solver_Error = "Sub Heat exchanger data is wrong. Tube number "+str(row[0])+ " does not exist in "
                    raise
                    
    def geometry(self):
        '''
        To calculate main geometry parameters per circuit

        Returns
        -------
        None.
        
        '''
        # to use shorter names
        OD = self.Geometry.OD
        Ntubes_per_bank_per_subcircuit = self.Geometry.Ntubes_per_bank_per_subcircuit
        Nbank=self.Geometry.Nbank
        Staggering = self.Geometry.Staggering
        Tubes_type = self.Geometry.Tubes_type
        if Staggering == 'aAa': # all rows same number of tubes, lower - upper - lower
            self.Geometry.Ntubes_per_subcircuit = Ntubes_per_bank_per_subcircuit * Nbank
            self.Geometry.Nair_grid_vertical =  2 * Ntubes_per_bank_per_subcircuit
        elif Staggering == 'AaA': # all rows same number of tubes, upper - lower - upper
            self.Geometry.Ntubes_per_subcircuit = Ntubes_per_bank_per_subcircuit * Nbank
            self.Geometry.Nair_grid_vertical =  2 * Ntubes_per_bank_per_subcircuit
        elif Staggering == 'inline': # all rows same number of tubes, parallel
            self.Geometry.Ntubes_per_subcircuit = Ntubes_per_bank_per_subcircuit * Nbank
            self.Geometry.Nair_grid_vertical = Ntubes_per_bank_per_subcircuit
        
        if Tubes_type == 'Smooth': # tube is smooth internally
            ID = self.Geometry.ID
            inner_circum = pi * ID
            CS_area = pi/4*ID * ID
            self.Geometry.Dh = ID
            
        elif Tubes_type == 'Microfin': # tube has microfins internally
            # visit https://imgur.com/TpZezhe for more details
            t = self.Geometry.t
            e = self.Geometry.e
            n = self.Geometry.n
            d = self.Geometry.d
            gama = self.Geometry.gama * pi / 180
            w = d - 2 * e * tan(gama / 2)
            if w < 0:
                e = d / (2 * tan(gama / 2))
                w = d - 2 * e * tan(gama / 2)
            self.Geometry.w = w
            ID = OD - 2 * (t-e)
            beta = self.Geometry.beta / 180 * pi
            self.Geometry.Di = ID
            self.Geometry.ID = ID
            self.Geometry.FD = OD - 2 * t # tube fin diameter
            A_fin = (w+d)/2*e
            self.Geometry.A_fin = A_fin
            CS_area = pi/4*pow(ID,2)-n*A_fin
            side = pow(pow((d-w)/2,2)+pow(e,2),0.5)
            inner_circum = pi * self.Geometry.ID
            A_fin = (w+d)/2*e
            Afa = pi/4*pow(ID, 2)-n*A_fin
            self.Geometry.Afa = Afa
            self.Geometry.Afn = pi/4*pow(ID, 2) # nominal flow area
            self.Geometry.Afc = pi/4*pow(self.Geometry.FD, 2) # core flow area
            self.Geometry.Ac = pi * self.Geometry.FD # core heat transfer area
            self.Geometry.An = pi * ID # nominal heat transfer area
            side = pow(pow((d-w)/2, 2) + pow(e, 2), 0.5)
            Aa = (pi * ID + (2 * side + w - d) * n) / cos(beta)
            self.Geometry.Aa = Aa
            Dh = 4 * Afa / Aa
            self.Geometry.Dh = Dh
            
        # inner heat transfer area            
        self.Geometry.inner_circum = inner_circum
        # inner Cross sectional area
        self.Geometry.A_CS = CS_area
        self.Geometry.Lsubcircuit = self.Geometry.Ntubes_per_subcircuit * self.Geometry.Ltube
        if hasattr(self.Geometry,"Sub_HX_matrix"):
            for tube in self.Geometry.Sub_HX_matrix:
                cut_length = self.Geometry.Ltube - (tube[2] - tube[1])
                self.Geometry.Lsubcircuit -= cut_length

        if self.Geometry.Lsubcircuit <= 0:
            if not hasattr(self,"Solver_Error"):
                self.Solver_Error = "Sub Heat exchanger data is wrong. Total tube length is zero."
            raise
            
        self.Geometry.A_r = self.Geometry.Lsubcircuit * self.Geometry.inner_circum*self.Geometry.Nsubcircuits

        self.Geometry.A_face = self.Geometry.Ltube * self.Geometry.Ntubes_per_bank_per_subcircuit * self.Geometry.Pt * self.Geometry.Nsubcircuits
        
        self.geometry_calculated == True
        
        if not hasattr(self.Thermal,'h_r_superheat_tuning'):
            self.Thermal.h_r_superheat_tuning = 1.0
        if not hasattr(self.Thermal,'h_r_subcooling_tuning'):
            self.Thermal.h_r_subcooling_tuning = 1.0
        if not hasattr(self.Thermal,'h_r_2phase_tuning'):
            self.Thermal.h_r_2phase_tuning = 1.0
        if not hasattr(self.Thermal,'DP_r_superheat_tuning'):
            self.Thermal.DP_r_superheat_tuning = 1.0
        if not hasattr(self.Thermal,'DP_r_subcooling_tuning'):
            self.Thermal.DP_r_subcooling_tuning = 1.0
        if not hasattr(self.Thermal,'DP_r_2phase_tuning'):
            self.Thermal.DP_r_2phase_tuning = 1.0
        if not hasattr(self.Thermal,'h_a_dry_tuning'):
            self.Thermal.h_a_dry_tuning = 1.0
        if not hasattr(self.Thermal,'h_a_wet_tuning'):
            self.Thermal.h_a_wet_tuning = 1.0
        if not hasattr(self.Thermal,'DP_a_dry_tuning'):
            self.Thermal.DP_a_dry_tuning = 1.0
        if not hasattr(self.Thermal,'DP_a_wet_tuning'):
            self.Thermal.DP_a_wet_tuning = 1.0

        if hasattr(self.Thermal,'HTC_superheat_Corr'):
            if self.Thermal.HTC_superheat_Corr != 0:
                self.Correlations.impose_h_superheat(int(self.Thermal.HTC_superheat_Corr))
        if hasattr(self.Thermal,'HTC_subcool_Corr'):
            if self.Thermal.HTC_subcool_Corr != 0:
                self.Correlations.impose_h_subcool(int(self.Thermal.HTC_subcool_Corr))
        if hasattr(self.Thermal,'DP_superheat_Corr'):
            if self.Thermal.DP_superheat_Corr != 0:
                self.Correlations.impose_dPdz_f_superheat(int(self.Thermal.DP_superheat_Corr))
        if hasattr(self.Thermal,'DP_subcool_Corr'):
            if self.Thermal.DP_subcool_Corr != 0:
                self.Correlations.impose_dPdz_f_subcool(int(self.Thermal.DP_subcool_Corr))
        if hasattr(self.Thermal,'HTC_2phase_Corr'):
            if self.Thermal.HTC_2phase_Corr != 0:
                self.Correlations.impose_h_2phase(int(self.Thermal.HTC_2phase_Corr))
        if hasattr(self.Thermal,'DP_2phase_Corr'):
            if self.Thermal.DP_2phase_Corr != 0:
                self.Correlations.impose_dPdz_f_2phase(int(self.Thermal.DP_2phase_Corr))
        if hasattr(self.Thermal,'DP_Accel_Corr'):
            if self.Thermal.DP_Accel_Corr != 0:
                self.Correlations.impose_dP_a(int(self.Thermal.DP_Accel_Corr))
        if hasattr(self.Thermal,'rho_2phase_Corr'):
            if self.Thermal.rho_2phase_Corr != 0:
                self.Correlations.impose_rho_2phase(int(self.Thermal.rho_2phase_Corr))
        if hasattr(self.Thermal,'Air_dry_Corr'):
            if self.Thermal.Air_dry_Corr != 0:
                self.Fins.impose_dry(int(self.Thermal.Air_dry_Corr))
        if hasattr(self.Thermal,'Air_wet_Corr'):
            if self.Thermal.Air_wet_Corr != 0:
                self.Fins.impose_wet(int(self.Thermal.Air_wet_Corr))
        
    def mdot_da_array_creator(self,Nsegments):
        '''
        A function used to create the array for mass flow rate of dry ar per
        each segment based on the passed number of segments and the staggering
        style.

        Parameters
        ----------
        Nsegments : float
            Number of segments per tube.

        Returns
        -------
        Air_grid_mdot_da_full : numpy array
            A 3d array of dry mass flow rate of air.

        '''
        # if humid velocity distribution is defined, then use it.
        if hasattr(self.Thermal, 'Vel_dist'):
            # the following code will integrate the distribution and distribute it on the segments accordingly
            if self.Accurate:
                v_ha_in = HAPropsSI('V','T',self.Thermal.Tin_a,'P',self.Thermal.Pin_a,'W',self.Thermal.Win_a)
            else:
                v_ha_in = pl.GetMoistAirVolume(self.Thermal.Tin_a-273.15, self.Thermal.Win_a, self.Thermal.Pin_a)
            
            # create an empty 2d array
            Air_grid_mdot_da = np.zeros([len(self.Thermal.Vel_dist[:]), Nsegments])
            
            # this will fill the 2d array using the inlet distribution
            for i, tube_dist in enumerate(self.Thermal.Vel_dist):
                # define the ratio between the elemenets of distribution to number of segments
                portion = len(tube_dist)/Nsegments
                if (portion - int(portion)) == 0: # they are equal or multiple (portion is an integer) (assuming step function)
                    for j in range(Nsegments): # each segment will take the portion of velocity distribution
                        Air_grid_mdot_da[int(i),int(j)] = np.sum(self.Thermal.Vel_dist[int(i),int(j * portion) : int((j + 1) * portion)])
                else: # portion is not an integer, will integrate and then distribute again (assuming step function)
                    w = 0
                    for j in range(Nsegments):
                        first_part = 1 - (w - int(w))
                        second_part = (portion - first_part) - int((portion - first_part))
                        a = self.Thermal.Vel_dist[int(i),int(w)] * first_part
                        b = sum(self.Thermal.Vel_dist[int(i),int(w)+1 , int(w) + int(portion - first_part - second_part) + 1])
                        c = self.Thermal.Vel_dist[int(i),int(w) + int(portion)] * second_part
                        Air_grid_mdot_da[int(i),int(j)] = a + b + c
                        w += portion
            
            # converting velocity to humid volume flow rate by multiplying by area
            Air_grid_mdot_da *= self.Geometry.Ltube / len(tube_dist) * self.Geometry.Pt
            
            # converting volume flow rate to dry air flow rate by multiply by density
            Air_grid_mdot_da *= (1 / v_ha_in)
            self.Thermal.mdot_ha = np.sum(Air_grid_mdot_da) * (1 + self.Thermal.Win_a) * self.Geometry.Nsubcircuits

        # a humid mass flow rate is defined

        # a humid volume flow rate is defined
        elif hasattr(self.Thermal, 'Vdot_ha'):
            if self.Accurate:
                v_ha_in = HAPropsSI('V','T',self.Thermal.Tin_a,'P',self.Thermal.Pin_a,'W',self.Thermal.Win_a)
            else:
                v_ha_in = pl.GetMoistAirVolume(self.Thermal.Tin_a-273.15, self.Thermal.Win_a, self.Thermal.Pin_a)
            
            Air_grid_mdot_da = np.zeros([self.Geometry.Ntubes_per_bank_per_subcircuit, Nsegments])
            Air_grid_mdot_da += self.Thermal.Vdot_ha / (Nsegments * self.Geometry.Ntubes_per_bank_per_subcircuit * self.Geometry.Nsubcircuits)
            Air_grid_mdot_da *= (1 / v_ha_in)
            self.Thermal.mdot_ha = self.Thermal.Vdot_ha / v_ha_in * (1 + self.Thermal.Win_a)

        elif hasattr(self.Thermal, 'mdot_ha'):
            Air_grid_mdot_da = np.zeros([self.Geometry.Ntubes_per_bank_per_subcircuit, Nsegments])
            Air_grid_mdot_da += self.Thermal.mdot_ha / (Nsegments * self.Geometry.Ntubes_per_bank_per_subcircuit * self.Geometry.Nsubcircuits)
            
        # converting 2d array to 3d array
        Air_grid_mdot_da_full = np.zeros(list(Air_grid_mdot_da.shape)+[int(self.Geometry.Nbank)])
        
        # first row will use the previous calculated 2d array
        Air_grid_mdot_da_full[:,:,0] = Air_grid_mdot_da.copy()
        
        # depending on stagerring style, the following rows will be calculated
        if self.Geometry.Staggering == 'inline' or len(Air_grid_mdot_da_full[:,0,0]) == 1:
            # the same array will be used for following rows
            for i in range(1, self.Geometry.Nbank):
                Air_grid_mdot_da_full[:,:,i] = Air_grid_mdot_da.copy()
        else:
            # depending on staggered configuration, the distribution will differ
            for i in range(1, self.Geometry.Nbank):
                if self.Geometry.Staggering == 'AaA':
                    if (i % 2) == 0:
                        # first tube will take 0.5, last tube will take 1.5
                        Air_grid_mdot_da_full[0,:,i] = Air_grid_mdot_da_full[0,:,i - 1] * 0.5
                        Air_grid_mdot_da_full[-1,:,i] = Air_grid_mdot_da_full[-1,:,i - 1] + 0.5 * Air_grid_mdot_da_full[-2,:,i - 1]
                        for k in range(1,len(Air_grid_mdot_da_full[:,0,i])-1):
                            Air_grid_mdot_da_full[k,:,i] = (Air_grid_mdot_da_full[k-1,:,i-1] + Air_grid_mdot_da_full[k,:,i-1]) / 2
                    else:
                        # last tube will take 0.5, first tube will take 1.5
                        Air_grid_mdot_da_full[-1,:,i] = Air_grid_mdot_da_full[-1,:,i - 1] * 0.5
                        Air_grid_mdot_da_full[0,:,i] = Air_grid_mdot_da_full[0,:,i - 1] + 0.5 * Air_grid_mdot_da_full[1,:,i - 1]
                        for k in range(1,len(Air_grid_mdot_da_full[:,0,i])-1):
                            Air_grid_mdot_da_full[k,:,i] = (Air_grid_mdot_da_full[k+1,:,i-1] + Air_grid_mdot_da_full[k,:,i-1]) / 2
                elif self.Geometry.Staggering == 'aAa':
                    if (i % 2) == 1:
                        # first tube will take 0.5, last tube will take 1.5
                        Air_grid_mdot_da_full[0,:,i] = Air_grid_mdot_da_full[0,:,i - 1] * 0.5
                        Air_grid_mdot_da_full[-1,:,i] = Air_grid_mdot_da_full[-1,:,i - 1] + 0.5 * Air_grid_mdot_da_full[-2,:,i - 1]
                        for k in range(1,len(Air_grid_mdot_da_full[:,0,i])-1):
                            Air_grid_mdot_da_full[k,:,i] = (Air_grid_mdot_da_full[k-1,:,i-1] + Air_grid_mdot_da_full[k,:,i-1]) / 2
                    else:
                        # last tube will take 0.5, first tube will take 1.5
                        Air_grid_mdot_da_full[-1,:,i] = Air_grid_mdot_da_full[-1,:,i - 1] * 0.5
                        Air_grid_mdot_da_full[0,:,i] = Air_grid_mdot_da_full[0,:,i - 1] + 0.5 * Air_grid_mdot_da_full[1,:,i - 1]
                        for k in range(1,len(Air_grid_mdot_da_full[:,0,i])-1):
                            Air_grid_mdot_da_full[k,:,i] = (Air_grid_mdot_da_full[k+1,:,i-1] + Air_grid_mdot_da_full[k,:,i-1]) / 2
                    
        return Air_grid_mdot_da_full

    def fins_calculate(self,Pin,Pout,Tin,Tout,Win,Wout,mdot_ha,L,Wet=False,Accurate=True,Tw_o=None,water_cond=None,mu_f=None):
        '''
        This function will calculate fins class, it can either be wet or dry, 
        it also will either calculate the fins class once or for each segment.

        Parameters
        ----------
        Pin : float
            inlet air pressure.
        Pout : float
            outlet air pressure.
        Tin : float
            inlet air dry bulb temperature.
        Tout : float
            outlet air dry bulb temperature.
        Win : float
            inlet humdity ratio.
        Wout : float
            outlet humdity ratio.
        mdot_ha : float
            humid flow rate of air.
        L : float
            segment length.
        Wet : float
            DESCRIPTION.
        Accurate : bool, optional
            either use CoolProp (True) or psychrolib (False). The default is True.
        Tw_o : float, optional
            tube wall temperature, used in wet analysis. The default is None.
        water_cond : float, optional
            water condensation rate, used in wet analysis. The default is None.
        mu_f : float, optional
            condensed water viscosity, used in wet analysis. The default is None.

        Returns
        -------
        heat transfer and pressure drop parameters.
        '''
        try:
            if self.Thermal.FinsOnce == True:
                # will calculate fins only once
                if self.Fins.calculated_before == False: # didn't calculate fins before
                    Fins_geometry = ValuesClass()
                    Fins_geometry.FinType = self.Geometry.FinType
                    Fins_geometry.NTubes_per_bank = self.Geometry.Ntubes_per_bank_per_subcircuit
                    Fins_geometry.FPI = self.Geometry.FPI
                    Fins_geometry.Pl = self.Geometry.Pl
                    Fins_geometry.Pt = self.Geometry.Pt
                    Fins_geometry.Do = self.Geometry.OD
                    Fins_geometry.Di = self.Geometry.Dh
                    Fins_geometry.Nbank = self.Geometry.Nbank
                    Fins_geometry.Ltube = self.Geometry.Ltube
                    Fins_geometry.Nheight = self.Geometry.Ntubes_per_bank_per_subcircuit
                    Fins_geometry.Ntubes_bank = self.Geometry.Ntubes_per_bank_per_subcircuit
                    Fins_geometry.t = self.Geometry.Fin_t
                    Fins_geometry.Staggering = self.Geometry.Staggering
                    if Fins_geometry.FinType == 'Louvered':
                        Fins_geometry.Lh = self.Geometry.Fin_Lh
                        Fins_geometry.Lp = self.Geometry.Fin_Lp
                    elif Fins_geometry.FinType in ['Wavy', 'WavyLouvered']:
                        Fins_geometry.Pd = self.Geometry.Fin_Pd
                        Fins_geometry.xf = self.Geometry.Fin_xf
                    elif Fins_geometry.FinType == 'Slit':
                        Fins_geometry.Sn = self.Geometry.Fin_Sn
                        Fins_geometry.Sh = self.Geometry.Fin_Sh
                        Fins_geometry.Ss = self.Geometry.Fin_Ss
                    elif Fins_geometry.FinType == 'Plain':
                        pass
                    else:
                        raise
                        
                    # calculate dry analysis
                    Tin = self.Thermal.Tin_a
                    Pin = self.Thermal.Pin_a
                    Win = self.Thermal.Win_a
                    if self.model.lower() == "segment":
                        last_tubes_list = self.Tubes_list[self.Tubes_list[:,2] == 2 * self.Geometry.Nbank - 1,1]
                        last_tubes_list = [int(i) for i in last_tubes_list]
                        h_out = self.Air_grid_h[last_tubes_list,2 * self.Geometry.Nbank,:]
                        W_out = self.Air_grid_W[last_tubes_list,2 * self.Geometry.Nbank,:]
                        
                        h_out_weighted = np.sum(h_out * self.Air_grid_mdot_da[:,:,self.Geometry.Nbank - 1])
                        W_out_weighted = np.sum(W_out * self.Air_grid_mdot_da[:,:,self.Geometry.Nbank - 1])
                        
                        h_out_average = float(h_out_weighted / np.sum(self.Air_grid_mdot_da[:,:,0]))
                        W_out_average = float(W_out_weighted / np.sum(self.Air_grid_mdot_da[:,:,0]))
                        P_out_average = float(np.average(self.Air_grid_P[last_tubes_list,2 * self.Geometry.Nbank,:]))
                    
                        Pout = P_out_average
                        Wout = W_out_average
                        hout = h_out_average
                        if self.Accurate:
                            Tout = HAPropsSI('T','H',hout,'P',Pout,'W',Wout)
                        else:
                            Tout = pl.GetTDryBulbFromEnthalpyAndHumRatio(hout, Wout) + 273.15
    
                    elif self.model.lower() == "phase":
                        if hasattr(self,'phase_segments') and self.phase_segments:
                            Pout_a_values = []
                            Wout_a_values = []
                            hout_a_values = []
                            for Segment in self.phase_segments:
                                Pout_a_values.append(Segment.Pout_a)
                                hout_a_values.append(Segment.hout_a * Segment.w_phase)
                                Wout_a_values.append(Segment.Wout_a * Segment.w_phase)
    
                            h_out_average = float(np.sum(hout_a_values))
                            W_out_average = float(np.sum(Wout_a_values))
                            P_out_average = float(np.average(Pout_a_values))
                    
                            Pout = P_out_average
                            Wout = W_out_average
                            hout = h_out_average
                            if self.Accurate:    
                                Tout = HAPropsSI('T','H',hout,'P',Pout,'W',Wout)
                            else:
                                Tout = pl.GetTDryBulbFromEnthalpyAndHumRatio(hout, Wout) + 273.15
    
                        else:
                            Pout = self.Thermal.Pin_a
                            Wout = self.Thermal.Win_a
                            Tout = self.Thermal.Tin_a

                    self.Fins.update(Tin,Tout,Win,Wout,Pin,Pout,self.Thermal.mdot_ha/self.Geometry.Nsubcircuits,Fins_geometry,False,Accurate)
                    h_a_dry, DP_dry = self.Fins.calculate_dry()
                    eta_o_dry = self.Fins.calculate_eff_dry(self.Thermal.k_fin, h_a_dry)
                    
                    water_cond = np.finfo(float).eps
                    mu_f = 1e-3
                    # calculate wet heat transfer
                    if Wet:
                        temp = True
                    else:
                        temp = False
                    Wet = True
                    self.Fins.update(Tin,Tout,Win,Wout,Pin,Pout,self.Thermal.mdot_ha/self.Geometry.Nsubcircuits,Fins_geometry,True,Accurate,water_cond=water_cond,mu_f=mu_f)
                    h_a_wet, DP_wet = self.Fins.calculate_wet()
                    Wet = temp
                    
                    if not self.Thermal.DP_a_wet_on:
                        DP_wet = DP_dry

                    if not self.Thermal.h_a_wet_on:
                        h_a_wet = h_a_dry
                    
                    L_full_subcircuit = self.Geometry.Ntubes_per_subcircuit * self.Geometry.Ltube
                    ratio = self.Geometry.Lsubcircuit / L_full_subcircuit # due to sub HX

                    # save values
                    self.Fins.h_a_dry = h_a_dry
                    self.Fins.DP_dry = DP_dry * ratio
                    self.Fins.h_a_wet = h_a_wet
                    self.Fins.DP_wet = DP_wet * ratio
                    self.Fins.eta_o_dry = eta_o_dry
                    self.Fins.calculated_before = True
    
                if Wet: # will calculate depending on wall temperature
                    bw_m, eta_o_wet = self.Fins.calculate_eff_wet(Tw_o, self.Thermal.k_fin, self.Fins.h_a_wet)
                    return bw_m, self.Fins.h_a_wet, self.Fins.DP_wet, eta_o_wet
                else: # just return dry values
                    return self.Fins.h_a_dry, self.Fins.DP_dry, self.Fins.eta_o_dry
            else: # calculating fins for each segment
                if not hasattr(self,'Fins_geometry'): # didn't calculate geometry of fins before
                    self.Fins_geometry = ValuesClass()
                    self.Fins_geometry.FinType = self.Geometry.FinType
                    self.Fins_geometry.NTubes_per_bank = 1
                    self.Fins_geometry.FPI = self.Geometry.FPI
                    self.Fins_geometry.Pl = self.Geometry.Pl
                    self.Fins_geometry.Pt = self.Geometry.Pt
                    self.Fins_geometry.Do = self.Geometry.OD
                    self.Fins_geometry.Di = self.Geometry.Dh
                    self.Fins_geometry.Nbank = 1
                    self.Fins_geometry.Nheight = 1
                    self.Fins_geometry.Ntubes_bank = 1
                    self.Fins_geometry.t = self.Geometry.Fin_t
                    self.Fins_geometry.Staggering = self.Geometry.Staggering
                    if self.Fins_geometry.FinType == 'Louvered':
                        self.Fins_geometry.Lh = self.Geometry.Fin_Lh
                        self.Fins_geometry.Lp = self.Geometry.Fin_Lp
                    elif self.Fins_geometry.FinType in ['Wavy', 'WavyLouvered']:
                        self.Fins_geometry.Pd = self.Geometry.Fin_Pd
                        self.Fins_geometry.xf = self.Geometry.Fin_xf
                    elif self.Fins_geometry.FinType == 'Slit':
                        self.Fins_geometry.Sn = self.Geometry.Fin_Sn
                        self.Fins_geometry.Sh = self.Geometry.Fin_Sh
                        self.Fins_geometry.Ss = self.Geometry.Fin_Ss
                    elif self.Fins_geometry.FinType == 'Plain':
                        pass
                    else:
                        raise AttributeError("please choose correct fin type")
                        
                self.Fins_geometry.Ltube = L # segment length
                    
                if Wet:
                    self.Fins.update(Tin,Tout,Win,Wout,Pin,Pout,mdot_ha,self.Fins_geometry,True,Accurate,water_cond=water_cond,mu_f=mu_f)
                    h_a_wet, DP_wet = self.Fins.calculate_wet()
                    bw_m, eta_o_wet = self.Fins.calculate_eff_wet(Tw_o, self.Thermal.k_fin, h_a_wet)
                    
                    if self.Thermal.DP_a_wet_on:
                        h_a_dry, DP_dry = self.Fins.calculate_dry()
                        DP_wet = DP_dry

                    if self.Thermal.h_a_wet_on:
                        h_a_dry, DP_dry = self.Fins.calculate_dry()
                        h_a_wet = h_a_dry
                
                    return bw_m, h_a_wet, DP_wet * ratio, eta_o_wet
                
                else:
                    self.Fins.update(Tin,Tout,Win,Wout,Pin,Pout,mdot_ha,self.Fins_geometry,False,Accurate)
                    h_a_dry, DP_dry = self.Fins.calculate_dry()
                    eta_o_dry = self.Fins.calculate_eff_dry(self.Thermal.k_fin, h_a_dry)

                    return h_a_dry, DP_dry * ratio, eta_o_dry
        except:
            import traceback
            print(traceback.format_exc())
            if not hasattr(self,"Solver_Error"):
                if Wet:
                    self.Solver_Error = "Failed to calculate wet air-side heat transfer in "
                else:
                    self.Solver_Error = "Failed to calculate dry air-side heat transfer in "
            raise
    
    def DP_a_fast_calculate(self):
        '''
        This function is used to calculate HX pressure drop based on dry analysis
        without solving heat transfer. used as initial solution while solving HX with fan

        Returns
        -------
        DP_a_dry : float
            HX air pressure drop.
        '''
        FinsOnce = self.Thermal.FinsOnce
        self.Fins.calculated_before = False
        self.Thermal.FinsOnce = True
        if self.geometry_calculated == False:
            self.geometry()
        Pin_a = self.Thermal.Pin_a
        Tin_a = self.Thermal.Tin_a
        Win_a = self.Thermal.Win_a
        
        # this will assume that the volume humid flow rate is the parameter defined
        if self.Accurate:
            v_ha_in = HAPropsSI('V','T',self.Thermal.Tin_a,'P',self.Thermal.Pin_a,'W',self.Thermal.Win_a)
        else:
            v_ha_in = pl.GetMoistAirVolume(self.Thermal.Tin_a-273.15, self.Thermal.Win_a, self.Thermal.Pin_a)
        
        mdot_ha = self.Thermal.Vdot_ha / v_ha_in * (1 + self.Thermal.Win_a)
        self.Thermal.mdot_ha = mdot_ha
        Ltube = self.Geometry.Ltube
        h_a_dry, DP_a_dry, eta_a_dry = self.fins_calculate(Pin_a,Pin_a,Tin_a,Tin_a,Win_a,Win_a,mdot_ha/self.Geometry.Nsubcircuits,Ltube,Wet=False,Accurate=True)
        L_full_subcircuit = self.Geometry.Ntubes_per_subcircuit * self.Geometry.Ltube
        ratio = self.Geometry.Lsubcircuit / L_full_subcircuit # due to sub HX
        self.Thermal.FinsOnce = FinsOnce
        delattr(self.Thermal,'mdot_ha') # to avoid being used in next iteration
        return DP_a_dry * ratio
    
    def results_creator(self):
        '''
        This function will be used to create a results subclass.

        Returns
        -------
        None.

        '''
        self.Results = ValuesClass()
        x1,y1 = self.Tubes_list[0,[1,2]]
        x2,y2 = self.Tubes_list[-1,[1,2]]
        x1 = int(x1)
        y1 = int(y1)
        x2 = int(x2)
        y2 = int(y2)
        self.Results.Tin_r = self.Tubes_grid[x1][y1].Segments[0].Tin_r
        self.Results.Tout_r = self.Tubes_grid[x2][y2].Segments[-1].Tout_r
        self.Results.hin_r = self.Tubes_grid[x1][y1].Segments[0].hin_r
        self.Results.hout_r = self.Tubes_grid[x2][y2].Segments[-1].hout_r
        self.Results.Pin_r = self.Tubes_grid[x1][y1].Segments[0].Pin_r
        self.Results.Pout_r = self.Tubes_grid[x2][y2].Segments[-1].Pout_r
        self.Results.xin_r = self.Tubes_grid[x1][y1].Segments[0].x_in
        self.Results.xout_r = self.Tubes_grid[x2][y2].Segments[-1].x_out
        self.Results.mdot_r = self.Thermal.mdot_r
        self.Results.Q_superheat = 0
        self.Results.Q_2phase = 0
        self.Results.Q_subcool = 0
        self.Results.w_superheat = 0
        self.Results.w_2phase = 0
        self.Results.w_subcool = 0
        self.Results.water_cond_superheat = 0
        self.Results.water_cond_2phase = 0
        self.Results.water_cond_subcool = 0
        self.Results.Charge_superheat = 0
        self.Results.Charge_2phase = 0
        self.Results.Charge_subcool = 0
        self.Results.DP_r_superheat = 0
        self.Results.DP_r_2phase = 0
        self.Results.DP_r_subcool = 0
        self.Results.UA_superheat = 0
        self.Results.UA_2phase = 0
        self.Results.UA_subcool = 0
        self.Results.Q_sensible = 0
        self.Air_h_a_dry_values = []
        self.Air_eta_a_dry_values = []
        self.Air_UA_dry_values = []
        self.Air_h_a_wet_values = []
        self.Air_eta_a_wet_values = []
        self.Air_UA_wet_values = []
        self.h_r_subcool_values = []
        self.h_r_2phase_values = []
        self.h_r_superheat_values = []
        self.w_phase_subcool_values = []
        self.w_phase_2phase_values = []
        self.w_phase_superheat_values = []
        self.h_a_values = []
        self.eta_a_values = []
        delta_T_pinch = np.inf
        delta_T_loc = None
        
        for j,(num,x,y,orient) in enumerate(self.Tubes_list):
            x = int(x)
            y = int(y)
            Segments = self.Tubes_grid[x][y].Segments
            for i, Segment in enumerate(Segments):
                if Segment.h_a_dry != 0:
                    self.Air_h_a_dry_values.append(Segment.h_a_dry)
                if Segment.eta_a_dry != 0:
                    self.Air_eta_a_dry_values.append(Segment.eta_a_dry)
                if Segment.UA_dry != 0:
                    self.Air_UA_dry_values.append(Segment.UA_dry)
                
                delta_T_pinch = min(delta_T_pinch,abs(Segment.Tout_a - Segment.Tout_r))
                delta_T_pinch = min(delta_T_pinch,abs(Segment.Tin_a - Segment.Tin_r))
                if delta_T_pinch == abs(Segment.Tout_a - Segment.Tout_r):
                    delta_T_loc = Segment.x_out
                elif delta_T_pinch == abs(Segment.Tin_a - Segment.Tin_r):
                    delta_T_loc = Segment.x_in
                
                if Segment.f_dry == 1:
                    if Segment.h_a_dry != 0:
                        self.h_a_values.append(Segment.h_a_dry)
                    if Segment.eta_a_dry != 0:
                        self.eta_a_values.append(Segment.eta_a_dry)
                elif Segment.f_dry == 0:
                    if Segment.h_a_wet != 0:
                        self.h_a_values.append(Segment.h_a_wet)
                    if Segment.eta_a_wet != 0:
                        self.eta_a_values.append(Segment.eta_a_wet)
                else:
                    if Segment.eta_a != 0:
                        self.eta_a_values.append(Segment.eta_a)
                if Segment.f_dry != 1.0:
                    if Segment.h_a_wet != 0:
                        self.Air_h_a_wet_values.append(Segment.h_a_wet)
                    if Segment.eta_a_wet != 0:
                        self.Air_eta_a_wet_values.append(Segment.eta_a_wet)
                    if Segment.UA_wet != 0:
                        self.Air_UA_wet_values.append(Segment.UA_wet)
                if Segment.x_in == 0.0:
                    if Segment.x_out > 0.0:
                        self.Results.Tdew_in = Segment.Tin_r
                        self.Results.SC = Segment.Tin_r - self.Results.Tin_r
                        self.Results.DP_r_subcool = Segment.Pin_r - self.Results.Pin_r
                        P_r_0 = Segment.Pin_r
                    elif Segment.x_out < 0.0:
                        self.Results.Tdew_out = Segment.Tin_r
                        self.Results.SC = Segment.Tin_r - self.Results.Tout_r
                        self.Results.DP_r_subcool = self.Results.Pout_r - Segment.Pin_r
                        if self.Results.xin_r > 1.0:
                            self.Results.DP_r_2phase = Segment.Pin_r - P_r_1
                        elif self.Results.xin_r <= 1.0:
                            self.Results.DP_r_2phase = Segment.Pin_r - self.Results.Pin_r
                    else:
                        raise
                elif Segment.x_in == 1.0:
                    if Segment.x_out < 1.0:
                        self.Results.Tdew_in = Segment.Tin_r
                        self.Results.SH = self.Results.Tin_r - Segment.Tin_r
                        self.Results.DP_r_superheat = Segment.Pin_r - self.Results.Pin_r
                        P_r_1 = Segment.Pin_r
                    elif Segment.x_out > 1.0:
                        self.Results.Tdew_out = Segment.Tin_r
                        self.Results.SH = self.Results.Tout_r - Segment.Tin_r
                        self.Results.DP_r_superheat = self.Results.Pout_r - Segment.Pin_r
                        if self.Results.xin_r < 0.0:
                            self.Results.DP_r_2phase = Segment.Pin_r - P_r_0
                        elif self.Results.xin_r >= 0.0:
                            self.Results.DP_r_2phase = Segment.Pin_r - self.Results.Pin_r
                    else:
                        raise                    

                if (Segment.x_in < 0) or (Segment.x_in == 0 and Segment.x_out < 0):
                    self.Results.Q_subcool += Segment.Q
                    self.Results.w_subcool += Segment.A_r / (self.Geometry.inner_circum * self.Geometry.Ntubes_per_subcircuit * self.Geometry.Ltube)
                    self.Results.water_cond_subcool += Segment.water_condensed
                    self.Results.Charge_subcool += Segment.Charge
                    self.Results.UA_subcool += Segment.UA
                    self.h_r_subcool_values.append(Segment.h_r * Segment.w_phase)
                    self.w_phase_subcool_values.append(Segment.w_phase)
                elif (0 < Segment.x_in < 1) or (Segment.x_in == 0 and Segment.x_out > 0) or (Segment.x_in == 1 and Segment.x_out <1):
                    self.Results.Q_2phase += Segment.Q
                    self.Results.w_2phase += Segment.A_r / (self.Geometry.inner_circum * self.Geometry.Ntubes_per_subcircuit * self.Geometry.Ltube)
                    self.Results.water_cond_2phase += Segment.water_condensed
                    self.Results.Charge_2phase += Segment.Charge
                    self.Results.UA_2phase += Segment.UA
                    self.h_r_2phase_values.append(Segment.h_r * Segment.w_phase)
                    self.w_phase_2phase_values.append(Segment.w_phase)
                elif (Segment.x_in > 1) or (Segment.x_in == 1 and Segment.x_out > 1):
                    self.Results.Q_superheat += Segment.Q
                    self.Results.w_superheat += Segment.A_r / (self.Geometry.inner_circum * self.Geometry.Ntubes_per_subcircuit * self.Geometry.Ltube)
                    self.Results.water_cond_superheat += Segment.water_condensed
                    self.Results.Charge_superheat += Segment.Charge
                    self.Results.UA_superheat += Segment.UA
                    self.h_r_superheat_values.append(Segment.h_r * Segment.w_phase)
                    self.w_phase_superheat_values.append(Segment.w_phase)
                self.Results.Q_sensible += Segment.Q_sensible
            if self.Bends[j].x_in < 0 or (self.Bends[j].x_in == 0 and self.Bends[j].x_out < 0):
                self.Results.Charge_subcool += self.Bends[j].Charge
            elif (0 < self.Bends[j].x_in < 1) or (self.Bends[j].x_in == 0 and self.Bends[j].x_out > 0) or (self.Bends[j].x_in == 1 and self.Bends[j].x_out < 1):
                self.Results.Charge_2phase += self.Bends[j].Charge
            elif self.Bends[j].x_in > 1 or (self.Bends[j].x_in == 1 and self.Bends[j].x_out > 1):
                self.Results.Charge_superheat += self.Bends[j].Charge
        if (self.Results.xin_r > 1.0) and (self.Results.xout_r > 1.0):
            self.Results.DP_r_subcool = 0
            self.Results.DP_r_2phase = 0
            self.Results.DP_r_superheat = self.Results.Pout_r - self.Results.Pin_r
        if (self.Results.xin_r < 0.0) and (self.Results.xout_r < 0.0):
            self.Results.DP_r_subcool = self.Results.Pout_r - self.Results.Pin_r
            self.Results.DP_r_2phase = 0
            self.Results.DP_r_superheat = 0
        if (0 < self.Results.xin_r < 1.0) and (0 < self.Results.xout_r < 1.0):
            self.Results.DP_r_subcool = 0
            self.Results.DP_r_2phase = self.Results.Pout_r - self.Results.Pin_r
            self.Results.DP_r_superheat = 0
        if (self.Results.xin_r > 1.0) and (1 > self.Results.xout_r > 0):
            self.Results.DP_r_2phase = self.Results.Pout_r - (self.Results.Pin_r + self.Results.DP_r_superheat)
        if (self.Results.xin_r < 0.0) and (1 > self.Results.xout_r > 0):
            self.Results.DP_r_2phase = self.Results.Pout_r - (self.Results.Pin_r + self.Results.DP_r_subcool)
            
        if not hasattr(self.Results,'SH'):
            self.Results.SH = None
        if not hasattr(self.Results,'SC'):
            self.Results.SC = None
        if not hasattr(self.Results,'Tdew_in'):
            self.Results.Tdew_in = None
        if not hasattr(self.Results,'Tdew_out'):
            self.Results.Tdew_out = None
        
        self.Results.delta_T_pinch = delta_T_pinch
        self.Results.delta_T_loc = delta_T_loc
        
        self.Results.Q = self.Results.Q_superheat + self.Results.Q_2phase + self.Results.Q_subcool
        self.Results.DP_r = self.Results.Pout_r - self.Results.Pin_r
        self.Results.water_cond = self.Results.water_cond_superheat + self.Results.water_cond_2phase + self.Results.water_cond_subcool
        self.Results.Charge = self.Results.Charge_superheat + self.Results.Charge_2phase + self.Results.Charge_subcool
        self.Results.UA = self.Results.UA_superheat + self.Results.UA_2phase + self.Results.UA_subcool
        if self.h_r_subcool_values:    
            self.Results.h_r_subcool = sum(self.h_r_subcool_values) / sum(self.w_phase_subcool_values)
        else:
            self.Results.h_r_subcool = 0
        if self.h_r_2phase_values:
            self.Results.h_r_2phase = sum(self.h_r_2phase_values) / sum(self.w_phase_2phase_values)
        else:
            self.Results.h_r_2phase = 0
        if self.h_r_superheat_values:    
            self.Results.h_r_superheat = sum(self.h_r_superheat_values) / sum(self.w_phase_superheat_values)
        else:
            self.Results.h_r_superheat = 0
        if self.Air_UA_dry_values:
            self.Results.UA_dry = sum(self.Air_UA_dry_values)
        else:
            self.Results.UA_dry = 0
        if self.Air_UA_wet_values:
            self.Results.UA_wet = sum(self.Air_UA_wet_values)
        else:
            self.Results.UA_wet = 0
            
        self.Results.SHR = self.Results.Q_sensible/self.Results.Q
       
        self.Results.Q *= self.Geometry.Nsubcircuits
        self.Results.Q_superheat *= self.Geometry.Nsubcircuits
        self.Results.Q_2phase *= self.Geometry.Nsubcircuits
        self.Results.Q_subcool *= self.Geometry.Nsubcircuits
        self.Results.Q_sensible *= self.Geometry.Nsubcircuits
        self.Results.water_cond *= self.Geometry.Nsubcircuits
        self.Results.water_cond_superheat *= self.Geometry.Nsubcircuits
        self.Results.water_cond_2phase *= self.Geometry.Nsubcircuits
        self.Results.water_cond_subcool *= self.Geometry.Nsubcircuits
        self.Results.Charge *= self.Geometry.Nsubcircuits
        self.Results.Charge_superheat *= self.Geometry.Nsubcircuits
        self.Results.Charge_2phase *= self.Geometry.Nsubcircuits
        self.Results.Charge_subcool *= self.Geometry.Nsubcircuits
        self.Results.UA *= self.Geometry.Nsubcircuits
        self.Results.UA_superheat *= self.Geometry.Nsubcircuits
        self.Results.UA_2phase *= self.Geometry.Nsubcircuits
        self.Results.UA_subcool *= self.Geometry.Nsubcircuits
        self.Results.UA_wet *= self.Geometry.Nsubcircuits
        self.Results.UA_dry *= self.Geometry.Nsubcircuits
        
        # Air results
        self.Results.Tin_a = self.Thermal.Tin_a
        self.Results.Win_a = self.Thermal.Win_a
        self.Results.Pin_a = self.Thermal.Pin_a

        self.Results.mdot_ha = self.Thermal.mdot_ha
        self.Results.mdot_da = self.Thermal.mdot_ha / (1 + self.Thermal.Win_a)
        
        last_tubes_list = self.Tubes_list[self.Tubes_list[:,2] == 2 * self.Geometry.Nbank - 1,1]
        last_tubes_list = [int(i) for i in last_tubes_list]
        h_out = self.Air_grid_h[last_tubes_list,2 * self.Geometry.Nbank,:]
        W_out = self.Air_grid_W[last_tubes_list,2 * self.Geometry.Nbank,:]
        
        h_out_weighted = np.sum(h_out * self.Air_grid_mdot_da[:,:,self.Geometry.Nbank - 1])
        W_out_weighted = np.sum(W_out * self.Air_grid_mdot_da[:,:,self.Geometry.Nbank - 1])
        
        h_out_average = float(h_out_weighted / np.sum(self.Air_grid_mdot_da[:,:,0]))
        W_out_average = float(W_out_weighted / np.sum(self.Air_grid_mdot_da[:,:,0]))
        P_out_average = float(np.average(self.Air_grid_P[last_tubes_list,2 * self.Geometry.Nbank,:]))

        self.Results.Pout_a = P_out_average
        self.Results.Wout_a = W_out_average
        self.Results.hout_a = h_out_average
        if self.Accurate:    
            self.Results.Tout_a = HAPropsSI('T','H',h_out_average,'P',self.Results.Pout_a,'W',self.Results.Wout_a)
        else:
            self.Results.Tout_a = pl.GetTDryBulbFromEnthalpyAndHumRatio(h_out_average, self.Results.Wout_a) + 273.15
        
        self.Results.DP_a = self.Results.Pout_a - self.Results.Pin_a
        if self.Air_h_a_dry_values:
            self.Results.h_a_dry = sum(self.Air_h_a_dry_values) / len(self.Air_h_a_dry_values)
        else:
            self.Results.h_a_dry = self.Results.h_a_wet
            
        if self.Air_h_a_wet_values:
            self.Results.h_a_wet = sum(self.Air_h_a_wet_values) / len(self.Air_h_a_wet_values)
        else:
            self.Results.h_a_wet = self.Results.h_a_dry
        
        self.Results.h_a = sum(self.h_a_values) / len(self.h_a_values)

        self.Results.eta_a = sum(self.eta_a_values) / len(self.eta_a_values)
        
        if self.Air_eta_a_dry_values:
            self.Results.eta_a_dry = sum(self.Air_eta_a_dry_values) / len(self.Air_eta_a_dry_values)
        else:
            self.Results.eta_a_dry = self.Results.eta_a_wet

        if self.Air_eta_a_wet_values:
            self.Results.eta_a_wet = sum(self.Air_eta_a_wet_values) / len(self.Air_eta_a_wet_values)
        else:
            self.Results.eta_a_wet = self.Results.eta_a_dry

        if self.Accurate:
            v_ha_in = HAPropsSI('V','T',self.Thermal.Tin_a,'P',self.Thermal.Pin_a,'W',self.Thermal.Win_a)
            v_ha_out = HAPropsSI('V','T',self.Results.Tout_a,'P',self.Results.Pout_a,'W',self.Results.Wout_a)
        else:
            v_ha_in = pl.GetMoistAirVolume(self.Thermal.Tin_a-273.15, self.Thermal.Win_a, self.Thermal.Pin_a)
            v_ha_out = pl.GetMoistAirVolume(self.Results.Tout_a-273.15, self.Results.Wout_a, self.Results.Pout_a)
        
        if hasattr(self.Thermal,'Vdot_ha'):
            self.Results.Vdot_ha_in = self.Thermal.Vdot_ha
        else:    
            self.Results.Vdot_ha_in = self.Results.mdot_da * v_ha_in
        self.Results.Vdot_ha_out = self.Results.mdot_da * v_ha_out

        L_full_subcircuit = self.Geometry.Ntubes_per_subcircuit * self.Geometry.Ltube
        ratio = self.Geometry.Lsubcircuit / L_full_subcircuit # due to sub HX

        self.Results.V_air_average = (self.Results.Vdot_ha_in + self.Results.Vdot_ha_out) / 2 / self.Geometry.A_face

           
        if self.Thermal.FinsOnce == True:
            self.Geometry.A_a = self.Fins.Ao * self.Geometry.Nsubcircuits * ratio
        else:
            self.Geometry.A_a = self.Fins.Ao * self.Thermal.Nsegments * self.Geometry.Ntubes_per_subcircuit*self.Geometry.Nsubcircuits

    def calculate(self,Max_Q_error = 0.01, Max_num_iter = 20, initial_Nsegments=1):
        '''
        Will solve HX based on given parameters

        Parameters
        ----------
        Max_Q_error : float, optional
            the maximum allowed error in Capacity. The default is 0.01.
        Max_num_iter : float, optional
            maximum number of iterations. The default is 20.
        initial_Nsegments : flaot, optional
            inital number of segments for initial solution. The default is 1.

        Returns
        -------
        None.

        '''
        self.check_input()
        self.Correlations.Selected_2phase_HTC = False
        self.Correlations.Selected_2phase_DP = False
        self.Correlations.Selected_2phase_Air = False
        if self.model == 'segment': # segment model will be used
            self.Fins.calculated_before = False
            self.Thermal.FinsOnce = True
            self.initialize(Max_Q_error,initial_Nsegments)
            self.solve(Q_error = Max_Q_error,i_max = Max_num_iter,Nsegments_calc=self.Thermal.Nsegments)
            self.results_creator()
        elif self.model == 'phase': # phase model will be used
            if self.geometry_calculated == False:
                self.geometry()
            if not hasattr(self.Thermal,'mdot_ha'):
                if self.Accurate:
                    v_ha_in = HAPropsSI('V','T',self.Thermal.Tin_a,'P',self.Thermal.Pin_a,'W',self.Thermal.Win_a)
                else:
                    v_ha_in = pl.GetMoistAirVolume(self.Thermal.Tin_a-273.15, self.Thermal.Win_a, self.Thermal.Pin_a)
                self.Thermal.mdot_ha = self.Thermal.Vdot_ha / v_ha_in * (1 + self.Thermal.Win_a)

            self.Fins.calculated_before = False
            self.Thermal.FinsOnce = True
            self.phase_by_phase_solver()
            self.results_creator_phase()

    def initialize(self,Max_Q_error,initial_Nsegments):
        '''
        A function used to initialize solution with initial number of segments

        Parameters
        ----------
        Max_Q_error : float
            maximum error in capacity.
        initial_Nsegments : float
            initial number of segments.

        Returns
        -------
        None.

        '''
        
        self.check_input()
        self.geometry()
        self.Tube_grid_creator()
        self.Air_grid_h,self.Air_grid_W,self.Air_grid_P = self.Air_grid_creator(initial_Nsegments)
        self.Air_grid_initializer(Max_Q_error,Nsegments = initial_Nsegments)
        self.Air_grid_h_initial = self.Air_grid_h
        self.Air_grid_W_initial = self.Air_grid_W
        self.Air_grid_P_initial = self.Air_grid_P
        self.Air_grid_h,self.Air_grid_W,self.Air_grid_P = self.Air_grid_creator(self.Thermal.Nsegments)
        for i in range(len(self.Air_grid_h[0,0,:])):
            self.Air_grid_h[:,:,i] = self.Air_grid_h_initial[:,:,0]
            self.Air_grid_W[:,:,i] = self.Air_grid_W_initial[:,:,0]
            self.Air_grid_P[:,:,i] = self.Air_grid_P_initial[:,:,0]
            
    def solve(self,Q_error = 0.01,i_max=20,Nsegments_calc=20):
        '''
        The function will solve the HX using the used parameters

        Parameters
        ----------
        Q_error : float, optional
            maximum error in capacity. The default is 0.01.
        i_max : float, optional
            maximum number of iterations. The default is 20.
        Nsegments_calc : float, optional
            number of segments to be used. The default is 20.

        '''
        if hasattr(self.Geometry,"Sub_HX_matrix"):
            self.Geometry.Sub_HX_matrix = np.array(self.Geometry.Sub_HX_matrix)
        self.Converged = False
        self.Fins.geometry_calculated_dry = False
        self.Fins.geometry_calculated_wet = False
        self.Nsegments_calc = Nsegments_calc
        self.Air_grid_mdot_da = self.mdot_da_array_creator(Nsegments_calc)
        AS = self.AS
        def objective(Air_grid_h):
            if self.terminate:
                self.Solver_Error = "User Terminated run!"
                raise
            self.Fins.calculated_before = False
            # assign passed air grid
            self.Air_grid_h = Air_grid_h.copy()
            hin_r = self.Thermal.hin_r
            Pin_r = self.Thermal.Pin_r
            AS.update(CP.HmassP_INPUTS,hin_r,Pin_r)
            Tin_r = AS.T()
            self.Thermal.Tin_r = Tin_r
            AS.update(CP.PQ_INPUTS,Pin_r,0.0)
            hL = AS.hmass()
            AS.update(CP.PQ_INPUTS,Pin_r,1.0)
            hV = AS.hmass()
            x_in = (hin_r-hL)/(hV-hL)
            # empty list for bends
            self.Bends = []
            for num,x,y,orient in self.Tubes_list:
                num = int(num)
                x = int(x)
                y = int(y)
                orient = int(orient) # tube solving orientation, either 1 or -1
                if not self.Geometry.Staggering == 'inline':
                    self.Tubes_grid[x][y].Pin_r = Pin_r
                    self.Tubes_grid[x][y].hin_r = hin_r
                    self.Tubes_grid[x][y].Tin_r = Tin_r
                    self.Tubes_grid[x][y].x_in = x_in
                    self.tube_staggered_solver(x,y,orient)
                    Bend_solution = self.solve_bend(num)
                    self.Bends.append(Bend_solution)
                    Pin_r = Bend_solution.Pout_r
                    hin_r = Bend_solution.hout_r
                    Tin_r = Bend_solution.Tout_r
                    x_in = Bend_solution.x_out
                elif self.Geometry.Staggering == 'inline':
                    self.Tubes_grid[x][y].Pin_r = Pin_r
                    self.Tubes_grid[x][y].hin_r = hin_r
                    self.Tubes_grid[x][y].Tin_r = Tin_r
                    self.Tubes_grid[x][y].x_in = x_in
                    self.tube_inline_solver(x,y,orient)
                    Bend_solution = self.solve_bend(num)
                    self.Bends.append(Bend_solution)
                    Pin_r = Bend_solution.Pout_r
                    hin_r = Bend_solution.hout_r
                    Tin_r = Bend_solution.Tout_r
                    x_in = Bend_solution.x_out
            error = self.circuit_error()
            return error
        i = 1
        error = 99
        error_change = 1
        Conditions = [True, True, True]
        while all(Conditions):
            old_error = error
            error = objective(self.Air_grid_h)
            error_change = abs(old_error - error)
            i += 1
            Conditions = [(abs(error) > Q_error), (i <= i_max), (error_change > 1e-6)]
        if Conditions[0] == False:
            self.Converged = True
            
    def circuit_error(self):        
        '''
        This function will calculate the capacity percentage error between 
        refrigerant and air.

        Returns
        -------
        TYPE
            DESCRIPTION.

        '''
        last_tubes_list = self.Tubes_list[self.Tubes_list[:,2] == 2 * self.Geometry.Nbank - 1,1]
        last_tubes_list = list(set([int(i) for i in last_tubes_list]))
        first_tubes_list = self.Tubes_list[self.Tubes_list[:,2] == 1,1]
        first_tubes_list = list(set([int(i) for i in first_tubes_list]))
        Air_Energy_in = self.Air_grid_h[first_tubes_list,0,:] * self.Air_grid_mdot_da[:,:,0]
        Air_Energy_out = self.Air_grid_h[last_tubes_list,2 * self.Geometry.Nbank,:] * self.Air_grid_mdot_da[:,:,self.Geometry.Nbank - 1]
        Q_a = np.sum(Air_Energy_out) - np.sum(Air_Energy_in)
        x1,y1 = self.Tubes_list[0,[1,2]]
        x2,y2 = self.Tubes_list[-1,[1,2]]
        x1 = int(x1)
        y1 = int(y1)
        x2 = int(x2)
        y2 = int(y2)
        hin_r = self.Tubes_grid[x1][y1].Segments[0].hin_r
        hout_r = self.Tubes_grid[x2][y2].Segments[-1].hout_r
        Q_r = self.Thermal.mdot_r * (hout_r - hin_r)  / self.Geometry.Nsubcircuits
        error = (Q_a + Q_r)/min(abs(Q_r),abs(Q_a))
        return error
        
    def solve_bend(self,num):
        '''The function is used to solve a bend depending on inlet condtions'''
        try:
            AS = self.AS
            bend_solution = ValuesClass()
            i = list(self.Tubes_list[:,0]).index(num)
            Tube1_x,Tube1_y = self.Tubes_list[i,[1,2]]
            Tube1_x = int(Tube1_x)
            Tube1_y = int(Tube1_y)
            Dh = self.Geometry.Dh
            try: # last bend will raise error
                Tube2_num,Tube2_x,Tube2_y = self.Tubes_list[i+1,[0,1,2]]
                Tube2_x = int(Tube2_x)
                Tube2_y = int(Tube2_y)
                hin_r = self.Tubes_grid[Tube1_x][Tube1_y].hout_r
                Pin_r = self.Tubes_grid[Tube1_x][Tube1_y].Pout_r
                x_in = self.Tubes_grid[Tube1_x][Tube1_y].x_out
                # Calculating bend length and radius
                if self.Geometry.Staggering != 'inline':
                    if ((Tube1_y-Tube2_y == 0) and (abs(Tube1_x-Tube2_x) == 2)) or\
                        ((abs(Tube1_y-Tube2_y) == 2) and (abs(Tube1_x-Tube2_x) == 1)):
                    # successive tubes
                        y_dist = self.Geometry.Pl * (abs(Tube1_y-Tube2_y)/2)
                        x_dist = self.Geometry.Pt * (abs(Tube1_x-Tube2_x)/2)
                        Radius = sqrt(x_dist**2+y_dist**2)/2
                        Length = pi * Radius
                        Direct = True
                    else: #tubes are not successive
                        max_radius = 0
                        Radius = 0
                        y_dist = self.Geometry.Pl * (abs(Tube1_y-Tube2_y)/2)
                        x_dist = self.Geometry.Pt * (abs(Tube1_x-Tube2_x)/2)
                        normal_distance = sqrt(x_dist**2+y_dist**2)
                        FarBendRadius = self.Geometry.FarBendRadius
                        if normal_distance > 2 * FarBendRadius:
                            if hasattr(self,'Bends'):
                                for bend in self.Bends:
                                    max_radius = max(max_radius,bend.Radius)
                            L1 = max(0,max_radius-FarBendRadius)
                            L2 = pi * FarBendRadius/2
                            L3 = normal_distance-2*FarBendRadius
                            Length = 2*L1 + 2*L2 + L3
                        elif normal_distance == 2 * FarBendRadius:
                            Length = pi * FarBendRadius
                        elif normal_distance < 2 * FarBendRadius:
                            raise Exception("Far bend radius is too large")
                        Direct = False
                elif self.Geometry.Staggering == 'inline':
                    if ((Tube1_y-Tube2_y == 0) and (abs(Tube1_x-Tube2_x) == 1)) or\
                        ((abs(Tube1_y-Tube2_y) == 2) and (abs(Tube1_x-Tube2_x) == 0)):
                    # successive tubes
                        y_dist = self.Geometry.Pl * (abs(Tube1_y-Tube2_y)/2)
                        x_dist = self.Geometry.Pt * (abs(Tube1_x-Tube2_x))
                        Radius = sqrt(x_dist**2+y_dist**2)/2
                        Length = pi * Radius
                        Direct = True
                    else: #tubes are not successive
                        max_radius = 0
                        Radius = 0
                        y_dist = self.Geometry.Pl * (abs(Tube1_y-Tube2_y)/2)
                        x_dist = self.Geometry.Pt * (abs(Tube1_x-Tube2_x))
                        normal_distance = sqrt(x_dist**2+y_dist**2)
                        FarBendRadius = self.Geometry.FarBendRadius
                        if normal_distance > 2 * FarBendRadius:
                            if hasattr(self,'Bends'):
                                for bend in self.Bends:
                                    max_radius = max(max_radius,bend.Radius)
                            L1 = max(0,max_radius-FarBendRadius)
                            L2 = pi * FarBendRadius/2
                            L3 = normal_distance-2*FarBendRadius
                            Length = 2*L1 + 2*L2 + L3
                        elif normal_distance == 2 * FarBendRadius:
                            Length = pi * FarBendRadius
                        elif normal_distance < 2 * FarBendRadius:
                            raise Exception("Far bend radius is too large")
                        Direct = False
                else:
                    raise
                # calculating pressure drop
                mdot_r = self.Thermal.mdot_r / self.Geometry.Nsubcircuits
                G_r = mdot_r / self.Geometry.A_CS
                if 0 < x_in < 1.0:
                    # from Christoffersen, B. R, J. C. Chato, J. P. Wattelet, and A. L. de Souza. 1993. Heat Transfer and Flow Characteristics of R-22, R-321R-125, and R-134a in Smooth and Micro-Fin Tubes. M.S. Thesis, Department of Mechanical and Industrial Engineering, University of Illinois, Urbana.
                    AS.update(CP.PQ_INPUTS,Pin_r,0.0)
                    Tbubble = AS.T()
                    mu_f = AS.viscosity()
                    rho_f = AS.rhomass()
                    
                    AS.update(CP.PQ_INPUTS,Pin_r,1.0)
                    Tdew = AS.T()
                    mu_g = AS.viscosity()
                    rho_g = AS.rhomass()
                    
                    Re_f = G_r * (1 - x_in) * Dh / mu_f
                    
                    if Direct:
                        Xtt = pow(mu_f / mu_g, 0.1) * pow(rho_g / rho_f, 0.5) * pow((1 - x_in) / x_in, 0.9)
                        dpdz_f = -self.Correlations.Chisholm(self.AS,G_r,self.Geometry.Dh,x_in,Tbubble,Tdew)
                        Cd = 2 * Radius
                        delta = pow(Dh / (Cd), 0.5)
                        epslon = 6.93E-5 * pow(Xtt, -0.712) * delta * Re_f / 2
                        DP_r_friction = dpdz_f * Length
                        v_avg = (1 - x_in) * (1 / rho_f) + (x_in) * (1 / rho_g)
                        DP_r_turning = -pow(G_r, 2) * v_avg * epslon / 2
                        DP_r = DP_r_friction + DP_r_turning
                    else:
                        Xtt = pow(mu_f / mu_g, 0.1) * pow(rho_g / rho_f, 0.5) * pow((1 - x_in) / x_in, 0.9)
                        Cd = sqrt(2) * FarBendRadius
                        dpdz_f = -self.Correlations.Souza(self.AS,G_r,self.Geometry.Dh,x_in,Tbubble,Tdew)
                        delta = pow(Dh / (Cd), 0.5)
                        epslon = 6.93E-5 * pow(Xtt, -0.712) * delta * Re_f / 2
                        DP_r_friction = dpdz_f * Length
                        v_avg = (1 - x_in) * (1 / rho_f) + (x_in) * (1 / rho_g)
                        DP_r_turning = -2 * pow(G_r, 2) * v_avg * epslon / 2
                        DP_r_bend = DP_r_friction + DP_r_turning
                        if self.Thermal.Tin_a < self.Thermal.Tin_r:
                            mode = 'heater'
                        else:
                            mode = 'cooler'
                        L = (2 * L1 + L3)
                        A_r = L * self.Geometry.inner_circum
                        self.Correlations.update(AS,self.Geometry,self.Thermal,'2phase',Pin_r,x_in,mdot_r,A_r,mode,var_2nd_out=x_in)
                        DP_friction_straight = self.Correlations.calculate_dPdz_f_2phase() * L
                        DP_r = DP_friction_straight + DP_r_bend
            
                else:
                    # from C.O. Popieil, J. Wojtkowiak, Friction factor in U-type undulated pipe, J. Fluid Eng. 122 (2000) 260–263
                    if Direct:
                        AS.update(CP.HmassP_INPUTS, hin_r, Pin_r)
                        rho = AS.rhomass()
                        mu = AS.viscosity()
                        Re = G_r * Dh / mu
                        Dn = Re / (2 * Radius / Dh)
                        f_c = 64 / Re * exp(0.021796 +  0.0413356 * pow(log(Dn), 2))
                        DP_r = -f_c / 2 / rho * G_r**2 / 2 / Dh * Length
                    else:
                        AS.update(CP.HmassP_INPUTS, hin_r, Pin_r)
                        rho = AS.rhomass()
                        mu = AS.viscosity()
                        Re = G_r * Dh / mu
                        Dn = Re / (2 * FarBendRadius / Dh)
                        f_c = 64 / Re * exp(0.021796 +  0.0413356 * pow(log(Dn), 2))
                        DP_r = -f_c / 2 / rho * G_r**2 / 2 / Dh * (2 * L2)
                        if self.Thermal.Tin_a < self.Thermal.Tin_r:
                            mode = 'heater'
                        else:
                            mode = 'cooler'
                        L = (2 * L1 + L3)
                        A_r = L * self.Geometry.inner_circum
                        self.Correlations.update(AS,self.Geometry,self.Thermal,'1phase',Pin_r,hin_r,mdot_r,A_r,mode)
                        DP_friction_straight = self.Correlations.calculate_dPdz_f_1phase() * L
                        DP_r = DP_friction_straight + DP_r
        
                Pout_r = Pin_r+DP_r
                
                # exit enthalpy
                hout_r = hin_r
                # calculating exit quality:
                AS.update(CP.HmassP_INPUTS,hout_r,Pout_r)
                Tout_r = AS.T()
                rho = AS.rhomass()
                AS.update(CP.PQ_INPUTS,Pout_r,0.0)
                hL = AS.hmass()
                Tbubble = AS.T()
                AS.update(CP.PQ_INPUTS,Pout_r,1.0)
                hV = AS.hmass()
                Tdew = AS.T()
                x_out = (hout_r-hL)/(hV-hL)
                if x_in <= 0:
                    xin_r_charge = np.finfo(float).eps
                elif x_in >= 1.0:
                    xin_r_charge = 1.0 - np.finfo(float).eps
                else:
                    xin_r_charge = x_in
                #charge calculation
                A_r = self.Geometry.inner_circum * Length
                if 0 <= x_in <= 1:
                    if 0 <= x_out <= 1:
                        self.Correlations.update(AS, self.Geometry,self.Thermal, '2phase',Pin_r,xin_r_charge,mdot_r,A_r,'heater',var_2nd_out=x_out)
                        rho = self.Correlations.calculate_rho_2phase()
                    else:
                        self.Correlations.update(AS, self.Geometry,self.Thermal, '2phase',Pin_r,xin_r_charge,mdot_r,A_r,'heater',var_2nd_out=xin_r_charge)
                        rho = self.Correlations.calculate_rho_2phase()
                Charge = rho * Length * self.Geometry.A_CS
                # passing results
                bend_solution.Length = Length
                bend_solution.IsDirect = Direct
                bend_solution.Radius = Radius
                bend_solution.hout_r = hout_r
                bend_solution.Pout_r = Pout_r
                bend_solution.DP_r = DP_r
                bend_solution.Charge = Charge
                bend_solution.x_in = x_in
                bend_solution.x_out = x_out
                bend_solution.Tout_r = Tout_r
                bend_solution.num = num
            except:#the last bend will return nothing and will not be used
                bend_solution.Pout_r = 0
                bend_solution.x_out = 0
                bend_solution.Tout_r = 0
                bend_solution.hout_r = 0
                bend_solution.Charge = 0
                bend_solution.Length = 0
                bend_solution.Radius = 0
                bend_solution.x_in = 0
                bend_solution.x_out = 0
                bend_solution.num = num
            return bend_solution
        except:
            if not hasattr(self,"Solver_Error"):
                self.Solver_Error = "Failed to calculate bend ("+str(num+1)+") pressure drop in "
            raise
    
    def Tube_grid_creator(self):
        '''
        The function will create a grid containing tubes at the correct 
        locations depending on staggering style

        Returns
        -------
        None.

        '''
        self.Tubes_grid = [[0 for y in range(int(self.Geometry.Nbank*2+1))] for x in range(int(self.Geometry.Nair_grid_vertical))] 
        num = 1
        tubes_list = np.zeros([self.Geometry.Ntubes_per_subcircuit,3])
        if self.Geometry.Staggering == 'aAa':
            for j in range(self.Geometry.Nbank):
                ss = 1 if j%2 == 0 else 0 
                y = int(2*j+1)
                
                for i in range(int(self.Geometry.Nair_grid_vertical/2)):
                    x = int(2*i+ss)
                    self.Tubes_grid[x][y] = ValuesClass()
                    self.Tubes_grid[x][y].num = num
                    tubes_list[num-1] = [num,x,y]
                    num += 1
        elif self.Geometry.Staggering == 'AaA':
            for j in range(self.Geometry.Nbank):
                ss = 0 if j%2 == 0 else 1
                y = int(2*j+1)
                
                for i in range(int(self.Geometry.Nair_grid_vertical/2)):
                    x = int(2*i+ss)
                    self.Tubes_grid[x][y] = ValuesClass()
                    self.Tubes_grid[x][y].num = num
                    tubes_list[num-1] = [num,x,y]
                    num += 1
        elif self.Geometry.Staggering == 'inline':
            for j in range(self.Geometry.Nbank):
                y = int(2*j+1)
                for i in range(int(self.Geometry.Nair_grid_vertical)):
                    x = int(i)
                    self.Tubes_grid[x][y] = ValuesClass()
                    self.Tubes_grid[x][y].num = num
                    tubes_list[num-1] = [num,x,y]
                    num += 1
        Cond1 = self.Geometry.Ntubes_per_subcircuit != len(set(self.Geometry.Connections))
        Cond2 = max(self.Geometry.Connections) > self.Geometry.Ntubes_per_subcircuit
        Cond3 = min(self.Geometry.Connections) < 1
        Cond4 = any([not isinstance(i,int) for i in self.Geometry.Connections])
        if Cond1 or Cond2 or Cond3 or Cond4:
            raise AttributeError("Something wrong in Connection list")
        orient = []
        for i in range(len(tubes_list)):
            if i%2:
                orient.append(-1)
            else:
                orient.append(1)
        Connections = self.Geometry.Connections
        self.Tubes_list = [tubes_list[i-1] for i in Connections]
        b = np.zeros((len(self.Tubes_list),4))
        b[:,:3] = self.Tubes_list
        b[:,3] = orient
        self.Tubes_list = b

    def Air_grid_creator(self,Nsegments):
        ''' This function will only create the structure of the air grid'''
        Air_grid_h = np.array([[[0.0 for z in range(int(Nsegments))] for y in range(int(self.Geometry.Nbank*2+1))] for x in range(int(self.Geometry.Nair_grid_vertical))])
        Air_grid_P = np.array([[[0.0 for z in range(int(Nsegments))] for y in range(int(self.Geometry.Nbank*2+1))] for x in range(int(self.Geometry.Nair_grid_vertical))])
        Air_grid_W = np.array([[[0.0 for z in range(int(Nsegments))] for y in range(int(self.Geometry.Nbank*2+1))] for x in range(int(self.Geometry.Nair_grid_vertical))])
        return Air_grid_h,Air_grid_W,Air_grid_P
    
    def Air_grid_initializer(self,Q_error_init,Nsegments):
        ''' This function will assume initial values for air grid'''
        AS = self.AS
        AS.update(CP.HmassP_INPUTS,self.Thermal.hin_r,self.Thermal.Pin_r)
        Win_a = self.Thermal.Win_a
        Pin_a = self.Thermal.Pin_a
        
        w_list = []
        
        for i in range(len(self.Air_grid_h[0,:])):
            w_list.append((i)/len(self.Air_grid_h[0,:]))
        for z in range(len(self.Air_grid_h[0,0,:])):
            for y in range(len(self.Air_grid_h[0,:])):
                for x in range(len(self.Air_grid_h[:])):
                    self.Air_grid_P[x,y,z] = Pin_a
                    self.Air_grid_W[x,y,z] = Win_a
        
        # intializing air enthalpy grid
        self.Air_grid_mdot_da = self.mdot_da_array_creator(Nsegments)
        self.Air_grid_h_initializer(Nsegments)
        
        for num,x,y,orient in self.Tubes_list:
            x = int(x)
            y = int(y)
            self.Air_grid_h[x,y,:] = [0 for i in range(len(self.Air_grid_h[x,y,:]))]
            self.Air_grid_P[x,y,:] = [0 for i in range(len(self.Air_grid_h[x,y,:]))]
            self.Air_grid_W[x,y,:] = [0 for i in range(len(self.Air_grid_h[x,y,:]))]

        self.solve(Q_error=Q_error_init,Nsegments_calc=Nsegments,i_max=40)

    def Air_grid_h_initializer(self,Nsegments):
        try:
            mdot_ha = self.Thermal.mdot_ha
            FinsOnce = self.Thermal.FinsOnce
            Pin_a = self.Thermal.Pin_a
            Pout_a = Pin_a
            Win_a = self.Thermal.Win_a
            Wout_a = Win_a
            Tin_a = self.Thermal.Tin_a
            Tout_a = Tin_a
            L = 123 # dummy and won't be used anyway
            self.Thermal.FinsOnce = True
            h_a_dry, DP_a_dry, eta_a_dry = self.fins_calculate(Pin_a,Pout_a,Tin_a,Tout_a,Win_a,Wout_a,mdot_ha/self.Geometry.Nsubcircuits,L,Wet=False,Accurate=self.Accurate)
            h_a_dry *= self.Thermal.h_a_dry_tuning
            cp_da = self.Fins.cp_da
            self.Thermal.FinsOnce = FinsOnce
            
            h_air = h_a_dry
            eta_air = eta_a_dry

            L_full_subcircuit = self.Geometry.Ntubes_per_subcircuit * self.Geometry.Ltube
            ratio = self.Geometry.Lsubcircuit / L_full_subcircuit # due to sub HX
            
            A_a = self.Fins.Ao * ratio
            k_wall = self.Thermal.kw
            L = self.Geometry.Lsubcircuit
            Do = self.Geometry.OD
            Di = self.Geometry.ID
            mdot_da = self.Thermal.mdot_ha / (1 + Win_a) / self.Geometry.Nsubcircuits
            
            self.AS.update(CP.PQ_INPUTS, self.Thermal.Pin_r, 1.0)
            hV = self.AS.hmass()
            TV = self.AS.T()
            self.AS.update(CP.PQ_INPUTS, self.Thermal.Pin_r, 0.0)
            hL = self.AS.hmass()
            TL = self.AS.T()
            self.AS.update(CP.HmassP_INPUTS, self.Thermal.hin_r,self.Thermal.Pin_r)
            T_r = self.AS.T()
            
            xin_r = (self.Thermal.hin_r - hL) / (hV - hL)
            
            if xin_r > 1.0:    
                Tin_r = TV
            elif xin_r < 0.0:
                Tin_r = TL
            else:
                Tin_r = T_r
            
            R_air_tot = 1 / (h_air * A_a * eta_air)
            R_wall_tot = log(Do/Di) / (2 * pi * k_wall * L)
            UA_overall_tot = 1 / (R_air_tot + R_wall_tot)
            NTU_tot = UA_overall_tot / (mdot_da * cp_da)
            epsilon_tot = (1 - exp(-NTU_tot)) # this is an approximation to account for the refrigerant heat transfer
    
            # calculating most outlet conditions
            Q = epsilon_tot * mdot_da * cp_da * (Tin_a - Tin_r)
            Tout_a = Tin_a - Q / (mdot_da * cp_da)
            
            if self.Accurate:
                try:
                    hout_a = HAPropsSI('H','T',Tout_a, 'P',Pin_a, 'W', Win_a) #[kJ/kg_da]
                except:
                    hout_a = HAPropsSI('H','T',Tout_a, 'P',Pin_a, 'R',1.0)
            else:
                RHout_a = pl.GetRelHumFromHumRatio(Tout_a-273.15,Win_a,Pin_a)
                if RHout_a <= 1.0:
                    hout_a = pl.GetMoistAirEnthalpy(Tout_a-273.15, Win_a)
                else:
                    Wsat = pl.GetSatHumRatio(Tout_a-273.15, Pin_a)
                    hout_a = pl.GetMoistAirEnthalpy(Tout_a-273.15, Wsat)
    
            if self.Accurate:
                hin_a = HAPropsSI('H','T',Tin_a, 'P',Pin_a, 'W', Win_a) #[kJ/kg_da]
            else:
                hin_a = pl.GetMoistAirEnthalpy(Tin_a-273.15, Win_a)
            
            # getting middle values
            A = hin_a
            B = log(hin_a/hout_a)
            x = np.linspace(0,1,int(self.Geometry.Nbank + 1))
            h_list = []
            for x_i in x:
                h_list.append(A*exp(-B*x_i))
                
            # moving backwards with the grid
            for z in range(len(self.Air_grid_h[0,0,:])):
                for y in range(len(self.Air_grid_h[0,:])):
                    if y%2 == 0:    
                        h = h_list[int(y/2)]
                    else:
                        h = 0
                    for x in range(len(self.Air_grid_h[:])):
                        self.Air_grid_h[x,y,z] = h
        except:
            if not hasattr(self,"Solver_Error"):
                self.Solver_Error = "Failed to intialize solution in "
            raise

    def tube_staggered_solver(self,x,y,orient):
        '''
            This function will solve one tube with coordinates x and y where 
            x is the row, and y is the column; z can be either 1 (entering
            from first segment) or -1 (entering from last segment)
            
        '''
        hin_r = self.Tubes_grid[x][y].hin_r
        Pin_r = self.Tubes_grid[x][y].Pin_r
        Tin_r = self.Tubes_grid[x][y].Tin_r
        x_in = self.Tubes_grid[x][y].x_in
        if orient == 1:
            z = 0
        elif orient == -1:
            z = self.Nsegments_calc-1
        hin_a = self.Air_grid_h[x,y-1,z]
        Win_a = self.Air_grid_W[x,y-1,z]
        hout_a = self.Air_grid_h[x,y+1,z]
        Wout_a = self.Air_grid_W[x,y+1,z]            
        num = self.Tubes_grid[x][y].num
        self.Tubes_grid[x][y].Segments = []
        Segment_1 = ValuesClass()
        Segment_2 = ValuesClass()
        Segment_1.hin_r = hin_r
        Segment_1.Pin_r = Pin_r
        Segment_1.Tin_r = Tin_r        
        Segment_1.x_in = x_in
        Segment_1.hin_a = hin_a
        Segment_1.Win_a = Win_a
        Segment_1.hout_a = hout_a
        Segment_1.Wout_a = Wout_a
        Segment_1.L = self.Geometry.Ltube/self.Nsegments_calc

        L_fraction_list = [1 for i in range(self.Nsegments_calc)]
        
        # for sub HX
        if hasattr(self.Geometry,"Sub_HX_matrix"):
            if num in self.Geometry.Sub_HX_matrix[:,0]:
                tube = self.Geometry.Sub_HX_matrix[self.Geometry.Sub_HX_matrix[:,0] == num]
                tube_start = tube[1]
                tube_end = tube[2]
                L_fraction_list = [1 for i in range(self.Nsegments_calc)]
                L_segment = self.Geometry.Ltube/self.Nsegments_calc
                for i in range(self.Nsegments_calc):
                    segment_start = i * L_segment
                    segment_end = (i + 1) * L_segment
                    if segment_end <= tube_start:
                        L_fraction_list[i] = 0
                    elif segment_start >= tube_end:
                        L_fraction_list[i] = 0
                    else:
                        L_fraction_list[i] = (min(segment_end,tube_end) - max(segment_start,tube_start)) / L_segment
        
        Segment_1.L_fraction = L_fraction_list[z]
        
        while num > self.Geometry.Ntubes_per_bank_per_subcircuit:
            num -= self.Geometry.Ntubes_per_bank_per_subcircuit
            
        Segment_1.mdot_ha = self.Air_grid_mdot_da[num - 1, z,int((y-1)/2)] * (1 + Win_a)
        if y == 1:
            x_tube_list_current = self.Tubes_list[self.Tubes_list[:,2] == y,1]
            x_tube_list_current = [int(i) for i in x_tube_list_current]
            x_tube_list_before = self.Tubes_list[self.Tubes_list[:,2] == y,1]
            x_tube_list_before = [int(i) for i in x_tube_list_before]
        else:
            x_tube_list_current = self.Tubes_list[self.Tubes_list[:,2] == y,1]
            x_tube_list_current = [int(i) for i in x_tube_list_current]
            x_tube_list_before = self.Tubes_list[self.Tubes_list[:,2] == y-2,1]
            x_tube_list_before = [int(i) for i in x_tube_list_before]
        Segment_1.Pin_a = np.average(self.Air_grid_P[x_tube_list_before,y-1,:])
        Segment_1.Pout_a = np.average(self.Air_grid_P[x_tube_list_current,y+1,:])
        Segment_1.phase_change_before = False
        Segment_1 = self.Segment_solver(Segment_1)
        self.Tubes_grid[x][y].Segments.append(Segment_1)
        while True:
            if Segment_1.phase_change_before == True:
                hout_a_segment = segment_1_w_phase * hout_a_1 + (1-segment_1_w_phase) * Segment_1.hout_a
                Wout_a_segment = segment_1_w_phase * Wout_a_1 + (1-segment_1_w_phase) * Segment_1.Wout_a
                Pout_a_segment = segment_1_w_phase * Pout_a_1 + (1-segment_1_w_phase) * Segment_1.Pout_a
            else:
                hout_a_segment = Segment_1.hout_a
                Wout_a_segment = Segment_1.Wout_a
                Pout_a_segment = Segment_1.Pout_a
            
            if Segment_1.phase_change == False:
                        
                #updating Air_grid
                # points to the right of tubes
                self.Air_grid_h[x,y+1,z] = hout_a_segment
                self.Air_grid_W[x,y+1,z] = Wout_a_segment
                self.Air_grid_P[x,y+1,z] = Pout_a_segment
                try: # Updating other point to the next row of tubes
                    # points to the right of below tubes
                    num1 = self.Tubes_grid[x][y].num
                    while num1 > self.Geometry.Ntubes_per_bank_per_subcircuit:
                        num1 -= self.Geometry.Ntubes_per_bank_per_subcircuit
                    
                    num2 = self.Tubes_grid[x+1][y+2].num
                    while num2 > self.Geometry.Ntubes_per_bank_per_subcircuit:
                        num2 -= self.Geometry.Ntubes_per_bank_per_subcircuit
                    mdot1 = self.Air_grid_mdot_da[num1 - 1,z,int((y-1)/2)]
                    mdot2 = self.Air_grid_mdot_da[num1 ,z,int((y-1)/2)]
                    mdot3 = self.Air_grid_mdot_da[num2 - 1,z,int((y+1)/2)]
                    if (num1 == 1) and (num2 == 1): # convergant section at most upper tube
                        self.Air_grid_h[x+1,y+1,z] = (mdot1 * self.Air_grid_h[x,y+1,z] + 0.5 * mdot2 * self.Air_grid_h[x+2,y+1,z]) / mdot3
                        self.Air_grid_W[x+1,y+1,z] = (mdot1 * self.Air_grid_W[x,y+1,z] + 0.5 * mdot2 * self.Air_grid_W[x+2,y+1,z]) / mdot3
                    elif(num1 == self.Geometry.Ntubes_per_bank_per_subcircuit - 1) and (num2 == self.Geometry.Ntubes_per_bank_per_subcircuit): # tube before last with already convergant calculated section
                        pass
                    else:                
                        self.Air_grid_h[x+1,y+1,z] = (0.5 * mdot1 * self.Air_grid_h[x,y+1,z] + 0.5 * mdot2 * self.Air_grid_h[x+2,y+1,z]) / mdot3
                        self.Air_grid_W[x+1,y+1,z] = (0.5 * mdot1 * self.Air_grid_W[x,y+1,z] + 0.5 * mdot2 * self.Air_grid_W[x+2,y+1,z]) / mdot3
                        
                except: # most below tubes
                    try:
                        # if most below tube has point below it
                        self.Air_grid_h[x+1,y+1,z] = hout_a_segment
                        self.Air_grid_W[x+1,y+1,z] = Wout_a_segment
                    except: # most below tube doesn't have point below it
                        pass
                try:
                    if (x-1) < 0 or (x-2) < 0:
                        raise
                    # points to the right of above tubes
                    num1 = self.Tubes_grid[x][y].num
                    while num1 > self.Geometry.Ntubes_per_bank_per_subcircuit:
                        num1 -= self.Geometry.Ntubes_per_bank_per_subcircuit
                    
                    num2 = self.Tubes_grid[x-1][y+2].num
                    while num2 > self.Geometry.Ntubes_per_bank_per_subcircuit:
                        num2 -= self.Geometry.Ntubes_per_bank_per_subcircuit
                    mdot1 = self.Air_grid_mdot_da[num1 - 1,z,int((y-1)/2)]
                    mdot2 = self.Air_grid_mdot_da[num1 - 2,z,int((y-1)/2)]
                    mdot3 = self.Air_grid_mdot_da[num2 - 1,z,int((y+1)/2)]
                    if (num1 == self.Geometry.Ntubes_per_bank_per_subcircuit) and (num2 == self.Geometry.Ntubes_per_bank_per_subcircuit): # convergant section at most lower tube
                        self.Air_grid_h[x-1,y+1,z] = (mdot1 * self.Air_grid_h[x,y+1,z] + 0.5 * mdot2 * self.Air_grid_h[x-2,y+1,z]) / mdot3
                        self.Air_grid_W[x-1,y+1,z] = (mdot1 * self.Air_grid_W[x,y+1,z] + 0.5 * mdot2 * self.Air_grid_W[x-2,y+1,z]) / mdot3
                    elif(num1 == 2) and (num2 == 1): # tube after first with already convergant calculated section
                        pass
                    else: # any other case
                        self.Air_grid_h[x-1,y+1,z] = (0.5 * mdot1 * self.Air_grid_h[x,y+1,z] + 0.5 * mdot2 * self.Air_grid_h[x-2,y+1,z]) / mdot3
                        self.Air_grid_W[x-1,y+1,z] = (0.5 * mdot1 * self.Air_grid_W[x,y+1,z] + 0.5 * mdot2 * self.Air_grid_W[x-2,y+1,z]) / mdot3
                except: # most upper tubes
                    try:
                        if (x-1) < 0:
                            raise
                        # if most upper tube has point above it
                        self.Air_grid_h[x-1,y+1,z] = hout_a_segment
                        self.Air_grid_W[x-1,y+1,z] = Wout_a_segment
                    except:# most upper tube doesn't have point above it
                        pass

            if Segment_1.phase_change == False:
                if orient == 1:
                    z += 1
                else:
                    z -=1
            else:
                hout_a_1 = Segment_1.hout_a
                Wout_a_1 = Segment_1.Wout_a
                Pout_a_1 = Segment_1.Pout_a
                
            if ((z == (self.Nsegments_calc)) or (z == -1)):
                self.Tubes_grid[x][y].Pout_r = Segment_1.Pout_r
                self.Tubes_grid[x][y].Tout_r = Segment_1.Tout_r
                self.Tubes_grid[x][y].hout_r = Segment_1.hout_r
                self.Tubes_grid[x][y].x_out = Segment_1.x_out
                break

            Segment_2.hin_r = Segment_1.hout_r
            Segment_2.Pin_r = Segment_1.Pout_r
            Segment_2.Tin_r = Segment_1.Tout_r
            Segment_2.x_in = Segment_1.x_out
            Segment_2.hin_a = self.Air_grid_h[x,y-1,z]
            Segment_2.Win_a = self.Air_grid_W[x,y-1,z]
            Segment_2.hout_a = self.Air_grid_h[x,y+1,z]
            Segment_2.Wout_a = self.Air_grid_W[x,y+1,z]
            Segment_2.L = self.Geometry.Ltube/self.Nsegments_calc
            Segment_2.L_fraction = L_fraction_list[z]
            
            num = self.Tubes_grid[x][y].num
            while num > self.Geometry.Ntubes_per_bank_per_subcircuit:
                num -= self.Geometry.Ntubes_per_bank_per_subcircuit
            Segment_2.mdot_ha = self.Air_grid_mdot_da[num - 1,z,int((y-1)/2)] * (1 + Segment_2.Win_a)
            if y == 1:
                x_tube_list_current = self.Tubes_list[self.Tubes_list[:,2] == y,1]
                x_tube_list_current = [int(i) for i in x_tube_list_current]
                x_tube_list_before = self.Tubes_list[self.Tubes_list[:,2] == y,1]
                x_tube_list_before = [int(i) for i in x_tube_list_before]
            else:
                x_tube_list_current = self.Tubes_list[self.Tubes_list[:,2] == y,1]
                x_tube_list_current = [int(i) for i in x_tube_list_current]
                x_tube_list_before = self.Tubes_list[self.Tubes_list[:,2] == y-2,1]
                x_tube_list_before = [int(i) for i in x_tube_list_before]
            Segment_2.Pin_a = np.average(self.Air_grid_P[x_tube_list_before,y-1,:])
            Segment_2.Pout_a = np.average(self.Air_grid_P[x_tube_list_current,y+1,:])
            if Segment_1.phase_change == True:
                Segment_2.phase_change_before = True
                segment_1_w_phase = Segment_1.w_phase
                Segment_2.w_phase = 1 - segment_1_w_phase
                Segment_2.phase_change_type = Segment_1.phase_change_type
            else:
                Segment_2.phase_change_before = False
            Segment_1 = self.Segment_solver(Segment_2)
            self.Tubes_grid[x][y].Segments.append(Segment_1)

    def tube_inline_solver(self,x,y,orient):
        '''
            This function will solve one tube with coordinates x and y where 
            x is the row, and y is the column; z can be either 1 (entering
            from first segment) or -1 (entering from last segment)
            
        '''
        hin_r = self.Tubes_grid[x][y].hin_r
        Pin_r = self.Tubes_grid[x][y].Pin_r
        Tin_r = self.Tubes_grid[x][y].Tin_r
        x_in = self.Tubes_grid[x][y].x_in
        if orient == 1:
            z = 0
        elif orient == -1:
            z = self.Nsegments_calc-1
        hin_a = self.Air_grid_h[x,y-1,z]
        Win_a = self.Air_grid_W[x,y-1,z]
        hout_a = self.Air_grid_h[x,y+1,z]
        Wout_a = self.Air_grid_W[x,y+1,z]            
        self.Tubes_grid[x][y].Segments = []
        Segment_1 = ValuesClass()
        Segment_2 = ValuesClass()
        Segment_1.hin_r = hin_r
        Segment_1.Pin_r = Pin_r
        Segment_1.Tin_r = Tin_r
        Segment_1.x_in = x_in
        Segment_1.hin_a = hin_a
        Segment_1.Win_a = Win_a
        Segment_1.hout_a = hout_a
        Segment_1.Wout_a = Wout_a
        Segment_1.L = self.Geometry.Ltube/self.Nsegments_calc

        num = self.Tubes_grid[x][y].num

        L_fraction_list = [1 for i in range(self.Nsegments_calc)]

        # for sub HX
        if hasattr(self.Geometry,"Sub_HX_matrix"):
            if num in self.Geometry.Sub_HX_matrix[:,0]:
                tube = self.Geometry.Sub_HX_matrix[self.Geometry.Sub_HX_matrix[:,0] == num][0]
                tube_start = tube[1]
                tube_end = tube[2]
                L_segment = self.Geometry.Ltube/self.Nsegments_calc
                for i in range(self.Nsegments_calc):
                    segment_start = i * L_segment
                    segment_end = (i + 1) * L_segment
                    if segment_end <= tube_start:
                        L_fraction_list[i] = 0
                    elif segment_start >= tube_end:
                        L_fraction_list[i] = 0
                    else:
                        L_fraction_list[i] = (min(segment_end,tube_end) - max(segment_start,tube_start)) / L_segment
                    
        Segment_1.L_fraction = L_fraction_list[z]

        while num > self.Geometry.Ntubes_per_bank_per_subcircuit:
            num -= self.Geometry.Ntubes_per_bank_per_subcircuit
        Segment_1.mdot_ha = self.Air_grid_mdot_da[num - 1, z,int((y-1)/2)] * (1 + Win_a)
        Segment_1.Pin_a = np.average(self.Air_grid_P[:,y-1,:])
        Segment_1.Pout_a = np.average(self.Air_grid_P[:,y+1,:])
        Segment_1.phase_change_before = False
        Segment_1 = self.Segment_solver(Segment_1)
        self.Tubes_grid[x][y].Segments.append(Segment_1)
        while True:
            if Segment_1.phase_change_before == True:
                hout_a_segment = segment_1_w_phase * hout_a_1 + (1-segment_1_w_phase) * Segment_1.hout_a
                Wout_a_segment = segment_1_w_phase * Wout_a_1 + (1-segment_1_w_phase) * Segment_1.Wout_a
                Pout_a_segment = segment_1_w_phase * Pout_a_1 + (1-segment_1_w_phase) * Segment_1.Pout_a
            else:
                hout_a_segment = Segment_1.hout_a
                Wout_a_segment = Segment_1.Wout_a
                Pout_a_segment = Segment_1.Pout_a
                
            if Segment_1.phase_change == False:
                #updating Air_grid
                self.Air_grid_h[x,y+1,z] = hout_a_segment
                self.Air_grid_W[x,y+1,z] = Wout_a_segment
                self.Air_grid_P[x,y+1,z] = Pout_a_segment

            if Segment_1.phase_change == False:
                if orient == 1:
                    z += 1
                else:
                    z -=1
            else:
                hout_a_1 = Segment_1.hout_a
                Wout_a_1 = Segment_1.Wout_a
                Pout_a_1 = Segment_1.Pout_a
                
            if ((z == (self.Nsegments_calc)) or (z == -1)):
                self.Tubes_grid[x][y].Pout_r = Segment_1.Pout_r
                self.Tubes_grid[x][y].Tout_r = Segment_1.Tout_r
                self.Tubes_grid[x][y].hout_r = Segment_1.hout_r
                self.Tubes_grid[x][y].x_out = Segment_1.x_out
                break
                
            Segment_2.hin_r = Segment_1.hout_r
            Segment_2.Pin_r = Segment_1.Pout_r
            Segment_2.Tin_r = Segment_1.Tout_r
            Segment_2.x_in = Segment_1.x_out
            Segment_2.hin_a = self.Air_grid_h[x,y-1,z]
            Segment_2.Win_a = self.Air_grid_W[x,y-1,z]
            Segment_2.hout_a = self.Air_grid_h[x,y+1,z]
            Segment_2.Wout_a = self.Air_grid_W[x,y+1,z]
            Segment_2.L = self.Geometry.Ltube/self.Nsegments_calc
            Segment_2.L_fraction = L_fraction_list[z]
            num = self.Tubes_grid[x][y].num
            while num > self.Geometry.Ntubes_per_bank_per_subcircuit:
                num -= self.Geometry.Ntubes_per_bank_per_subcircuit
            Segment_2.mdot_ha = self.Air_grid_mdot_da[num - 1,z,int((y-1)/2)] * (1 + Segment_2.Win_a)
            Segment_2.Pin_a = np.average(self.Air_grid_P[:,y-1,:])
            Segment_2.Pout_a = np.average(self.Air_grid_P[:,y+1,:])
            if Segment_1.phase_change == True:
                Segment_2.phase_change_before = True
                segment_1_w_phase = Segment_1.w_phase
                Segment_2.w_phase = 1 - segment_1_w_phase
                Segment_2.phase_change_type = Segment_1.phase_change_type
            else:
                Segment_2.phase_change_before = False
            Segment_1 = self.Segment_solver(Segment_2)
            self.Tubes_grid[x][y].Segments.append(Segment_1)

    def Segment_solver(self,Segment):
        '''this will solve a segment (it can be a first or second of phase 
        change segments)'''
        Ref = ValuesClass()
        Air = ValuesClass()
        Ref.hin_r = Segment.hin_r
        Ref.Pin_r = Segment.Pin_r
        Ref.Tin_r = Segment.Tin_r
        Ref.x_in = Segment.x_in
        Ref.L = Segment.L
        if Ref.L <= 0:
            Ref.L = np.finfo(float).eps
        Ref.L_fraction = Segment.L_fraction
        Air.hin_a = Segment.hin_a
        Air.hout_a = Segment.hout_a
        Air.Win_a = Segment.Win_a
        Air.Wout_a = Segment.Wout_a
        Air.Pin_a = Segment.Pin_a
        Air.Pout_a = Segment.Pout_a
        Air.mdot_ha = Segment.mdot_ha
        if self.Thermal.Tin_a < self.Thermal.Tin_r:
            mode = 'heater'
        else:
            mode = 'cooler'
        if Segment.phase_change_before == False:
            # this is a normal segment
            if 0 < Ref.x_in < 1 or (Ref.x_in == 0 and mode == 'cooler') or (Ref.x_in == 1 and mode == 'heater'): # 2phase inlet
                Results = self.solver_2phase(Ref,Air)
                # normally
                Results.phase_change = False
                if not (0 <= Results.x_out <= 1):
                    # phase change happened
                    if Results.x_out > 1:
                        # it is from 2phase to Vapor
                        
                        # this is to find portion of segment where 2phase exist
                        # and construct the first segment
                        w_2phase = self.mixed_segment(Segment,'2phasetoV')
                        phase_change_type = "2phasetoV"
                        
                        Results = self.solver_2phase(Ref,Air,w_2phase)
                        # to avoid small tolerance in x
                        Results.x_out = 1.0
                    elif Results.x_out < 0:
                        # it is from 2phase to liquid
                        # this is to find portion of segment where 2phase exist
                        # and construct the first segment
                        w_2phase = self.mixed_segment(Segment,'2phasetoL')
                        phase_change_type = "2phasetoL"
                        
                        Results = self.solver_2phase(Ref,Air,w_2phase)
                        # to avoid small tolerance in x
                        Results.x_out = 0.0
                    Results.phase_change_type = phase_change_type
                    Results.phase_change = True
                    Results.w_phase = w_2phase
            elif Ref.x_in < 0 or (Ref.x_in == 0 and mode == 'heater'): #subcooled
                Results = self.solver_1phase(Ref,Air)
                # normally
                Results.phase_change = False
                if not (Results.x_out < 0):
                    # phase change happened
                    
                    # this is to find portion of segment where Liquid exist
                    # and construct the first segment
                    w_1phase = self.mixed_segment(Segment,'Lto2phase')
                    Results = self.solver_1phase(Ref,Air,w_1phase)
                    # to avoid small tolerance in x
                    Results.x_out = 0.0
                    Results.phase_change_type = "Lto2phase"
                    Results.phase_change = True
                    Results.w_phase = w_1phase
            elif Ref.x_in > 1 or (Ref.x_in == 1 and mode == 'cooler'): # superheated
                Results = self.solver_1phase(Ref,Air)
                # normally
                Results.phase_change = False
                if not (Results.x_out > 1):
                    # phase change happened
                    
                    # find porion of segment where vapor exist and contruct
                    # a segment with it
                    w_1phase = self.mixed_segment(Segment,'Vto2phase')
                                        
                    Results = self.solver_1phase(Ref,Air,w_1phase)
                    # to avoid small tolerance in x
                    Results.x_out = 1.0
                    Results.phase_change_type = "Vto2phase"
                    Results.phase_change = True
                    Results.w_phase = w_1phase
            Results.phase_change_before = False
        else:
            # phase change happened in previous segment, so this is the second
            # segment of phase change
            
            # portion of the other phase
            w_phase = Segment.w_phase
            if Segment.phase_change_type in ['Lto2phase','Vto2phase']:
                # second segment is 2 phase
                Results = self.solver_2phase(Ref,Air,w_2phase=w_phase)
            elif Segment.phase_change_type in ['2phasetoL','2phasetoV']:
                # second phase is either vapor or liquid
                Results = self.solver_1phase(Ref,Air,w_1phase=w_phase)
            Results.phase_change = False
            Results.phase_change_before = True
        return Results

    def mixed_segment(self,Segment,change):
        '''
        Used to calculate portion of the segment where the phase exists

        Parameters
        ----------
        change : type of phase change

        Returns
        -------
        portion
            float.

        '''
        Ref = ValuesClass()
        Air = ValuesClass()
        Ref.hin_r = Segment.hin_r
        Ref.Pin_r = Segment.Pin_r
        Ref.Tin_r = Segment.Tin_r
        Ref.x_in = Segment.x_in
        Ref.L = Segment.L
        Ref.L_fraction = Segment.L_fraction
        Air.hin_a = Segment.hin_a
        Air.hout_a = Segment.hout_a
        Air.Win_a = Segment.Win_a
        Air.Wout_a = Segment.Wout_a
        Air.Pin_a = Segment.Pin_a
        Air.Pout_a = Segment.Pout_a
        Air.mdot_ha = Segment.mdot_ha
        if change == "Lto2phase":
            def objective(w_1phase):
                Results = self.solver_1phase(Ref,Air,w_1phase) 
                return Results.x_out
            w_1phase = brentq(objective,np.finfo(float).eps,1-np.finfo(float).eps)
            return w_1phase
        
        if change == "Vto2phase":
            def objective(w_1phase):
                Results = self.solver_1phase(Ref,Air,w_1phase)
                return Results.x_out-1
            w_1phase = brentq(objective,np.finfo(float).eps,1-np.finfo(float).eps)
            return w_1phase
        if change == "2phasetoL":
            def objective(w_2phase):
               Results = self.solver_2phase(Ref,Air,w_2phase) 
               return Results.x_out
            w_2phase = brentq(objective,np.finfo(float).eps,1-np.finfo(float).eps)
            return w_2phase
        if change == "2phasetoV":
            def objective(w_2phase):
               Results = self.solver_2phase(Ref,Air,w_2phase) 
               return Results.x_out-1
            w_2phase = brentq(objective,np.finfo(float).eps,1-np.finfo(float).eps)
            return w_2phase
        
    def solver_2phase(self,Ref_inputs,Air_inputs,w_2phase=1.0):
        '''the function will solve a 2 phase segment'''
        AS = self.AS
        Pin_r = Ref_inputs.Pin_r
        x_in = Ref_inputs.x_in
        hin_r = Ref_inputs.hin_r
        AS.update(CP.PQ_INPUTS,Pin_r,x_in)
        Tin_r = AS.T()
        L = Ref_inputs.L * w_2phase * Ref_inputs.L_fraction + np.finfo(float).eps
        A_r = self.Geometry.inner_circum * L
        mdot_r = self.Thermal.mdot_r / self.Geometry.Nsubcircuits
        Rw = log(self.Geometry.OD/self.Geometry.ID)/(2*pi*self.Thermal.kw*L)
        
        # calculating inlet and outlet air properties
        hin_a = Air_inputs.hin_a
        hout_a = Air_inputs.hout_a
        Pin_a = Air_inputs.Pin_a
        Pout_a = Air_inputs.Pout_a
        Win_a = Air_inputs.Win_a
        Wout_a = Air_inputs.Wout_a
        if self.Accurate:
            Tin_a = HAPropsSI('T','H',hin_a,'P',Pin_a,'W',Win_a)
            Tout_a = HAPropsSI('T','H',hout_a,'P',Pout_a,'W',Wout_a)
        else:
            Tin_a = pl.GetTDryBulbFromEnthalpyAndHumRatio(hin_a, Win_a) + 273.15
            Tout_a = pl.GetTDryBulbFromEnthalpyAndHumRatio(hout_a, Wout_a) + 273.15
        
        mdot_ha = Air_inputs.mdot_ha * w_2phase * Ref_inputs.L_fraction + np.finfo(float).eps
        
        # Calculating air thermal heat transfer properties
        h_a_dry, DP_a_dry, eta_a_dry = self.fins_calculate(Pin_a,Pout_a,Tin_a,Tout_a,Win_a,Wout_a,mdot_ha/w_2phase,L/w_2phase,Wet=False,Accurate=self.Accurate)
        h_a_dry *= self.Thermal.h_a_dry_tuning
        cp_da = self.Fins.cp_da
        if self.Thermal.FinsOnce == True:
            if hasattr(self,'Nsegments_calc'):
                DP_a_dry = DP_a_dry / self.Geometry.Nbank
        
        DP_a_dry *= self.Thermal.DP_a_dry_tuning
        Pout_a = Pin_a + DP_a_dry
        
        # air side total area
        if self.Thermal.FinsOnce == True:
            A_a = self.Fins.Ao * w_2phase / (self.Nsegments_calc * self.Geometry.Ntubes_per_subcircuit) * Ref_inputs.L_fraction + np.finfo(float).eps
        else:
            A_a = self.Fins.Ao * Ref_inputs.L_fraction + np.finfo(float).eps
        
        # dry air flow rate
        mdot_da = mdot_ha / (1 + Win_a)
        
        # heater is condenser, cooler is evaporator
        if Tin_a > Tin_r:
            mode = 'cooler'
        else:
            mode = 'heater'
            
        # dew point temperature of inlet air
        if self.Accurate:
            Tdp = HAPropsSI('D','T',Tin_a,'P',Pin_a,'W',Win_a)
        else:
            Tdp = pl.GetTDewPointFromHumRatio(Tin_a-273.15, Win_a, Pin_a) + 273.15
            
        # to get approximate value of q_flux
        if L > 1e-7: # length is very small, just don't solve (used for sub HX)
            h_r = 1500
            for _ in range(5):
                h_r_old = h_r
                #approximate overall heat transfer coefficient
                UA_approx = 1/(1/(h_a_dry * A_a * eta_a_dry) + 1/(h_r * A_r) + Rw);
                
                #Number of transfer units
                Ntu_approx = UA_approx / (mdot_da * cp_da);
                
                #since Cr=0, e.g. see Incropera - Fundamentals of Heat and Mass Transfer, 2007, p. 690
                epsilon_approx = 1 - exp(-Ntu_approx);
                
                # approximate heat transfer
                Q_approx = epsilon_approx * mdot_da * cp_da * (Tin_a - Tin_r);
    
                # approximate heat flux
                qflux = Q_approx / A_r
                
                # calculating refrigerant HTC
                try:
                    self.Correlations.update(AS,self.Geometry,self.Thermal,'2phase',Pin_r,x_in,mdot_r,A_r,mode,q_flux=qflux)
                    h_r = self.Correlations.calculate_h_2phase()
                except:
                    if not hasattr(self,"Solver_Error"):
                        self.Solver_Error = "Failed to calculate two-phase HTC in "
                    raise
                    
                h_r *= self.Thermal.h_r_2phase_tuning
                if (abs((h_r_old - h_r) / h_r)) < 1e-6:
                    break
    
            # calculating heat transfer in case of dry conditions
            
            #overall heat thermal transfer coefficients of internal and external
            UA_o_dry = (h_a_dry * A_a * eta_a_dry)
            UA_i = (h_r * A_r)
            
            #overall heat transfer coefficient in dry conditions
            UA_dry = 1 / (1 / UA_o_dry + 1 / UA_i + Rw)
            
            #Number of transfer units
            Ntu_dry = UA_dry / (mdot_da * cp_da)
            
            #since Cr=0, e.g. see Incropera - Fundamentals of Heat and Mass Transfer, 2007, p. 690
            epsilon_dry = 1 - exp(-Ntu_dry)  
            
            #heat transfer in dry conditions
            Q_dry = epsilon_dry * mdot_da * cp_da * (Tin_a - Tin_r)
            
            # Dry-analysis air outlet temp [K]
            Tout_a_dry = Tin_a - Q_dry / (mdot_da * cp_da)
            
            #wall outside temperature (at inlet and outlet air points, Tin_r is assumed constant)
            Tw_o_a = Tin_r + UA_dry * (1 / UA_i + Rw) * (Tin_a - Tin_r)
            Tw_o_b = Tin_r + UA_dry * (1 / UA_i + Rw) * (Tout_a_dry - Tin_r)
    
            Wout_a = Win_a # no condensation in dry condition
            
            Tout_a = Tout_a_dry
    
            if Tw_o_b > Tdp:
                #All dry, since surface at outlet dry
                f_dry = 1.0
                Q = Q_dry #[W]
                Q_sensible = Q #[W]
                hout_a = hin_a - Q / mdot_da #[J/kg_da]
            else:
                if Tw_o_a < Tdp:
                    #All wet, since surface at refrigerant inlet is wet
                    f_dry = 0.0
                    Q_dry = 0.0
                    T_ac = Tin_a # temperature at onset of wetted wall
                    h_ac = hin_a # enthalpy at onset of wetted surface
                else:
                    # Partially wet, partially dry
                    # Based on equating heat fluxes at the wall which is at dew point UA_i*(Tw-Ti)=UA_o*(To-Tw)
                    T_ac = Tdp + UA_i / UA_o_dry * (Tdp - Tin_r)
                    
                    # Dry effectiveness (minimum capacitance on the air side by definition)
                    epsilon_dry = (Tin_a - T_ac) / (Tin_a - Tin_r)
                    
                    # Dry fraction found by solving epsilon=1-exp(-f_dry*Ntu) for known epsilon from above equation
                    f_dry = -1.0 / Ntu_dry * log(1.0 - epsilon_dry)
                    
                    # Enthalpy, using air humidity at the interface between wet and dry surfaces, which is same humidity ratio as inlet
                    if self.Accurate:
                        h_ac = HAPropsSI('H','T',T_ac,'P',Pin_a,'W',Win_a) #[J/kg_da]
                    else:
                        h_ac = pl.GetMoistAirEnthalpy(T_ac-273.15, Win_a)
                    
                    # Dry heat transfer
                    Q_dry = mdot_da * cp_da * (Tin_a - T_ac)
                
                # intial guess
                error_per = 1
                UA_o_wet = UA_o_dry
                eta_a_wet = eta_a_dry
                h_a_wet = h_a_dry
                Q = Q_dry
                i = 1
                water_cond = np.finfo(float).eps
                UA_wet = UA_dry
                b_r = cair_sat(Tin_r) * 1000
                mu_f = 1e-3
                if self.Accurate:
                    h_s_w = HAPropsSI('H','T',Tin_r, 'P',Pin_a, 'R', 1.0) #[kJ/kg_da]
                else:
                    Wsat = pl.GetSatHumRatio(Tin_r-273.15, Pin_a)
                    h_s_w = pl.GetMoistAirEnthalpy(Tin_r-273.15, Wsat)
                
                while (error_per > 0.00001) and i <= 15:
                    UA_star = 1 / (cp_da / (eta_a_wet * h_a_wet * A_a) + b_r * (1 / (h_r * A_r) + b_r * Rw))
                    
                    Tw_o = Tin_r + UA_star / (h_r * A_r) * (hin_a - h_s_w)
    
                    Q_old = Q
                    
                    bw_m, h_a_wet, DP_a_wet, eta_a_wet = self.fins_calculate(Pin_a,Pout_a,Tin_a,Tout_a,Win_a,Wout_a,mdot_ha/w_2phase,L/w_2phase,Wet=True,Accurate=self.Accurate,Tw_o = Tw_o, water_cond = water_cond, mu_f = mu_f)
                    h_a_wet *= self.Thermal.h_a_wet_tuning
                    cp_da = self.Fins.cp_da
                    
                    if self.Thermal.FinsOnce == True and hasattr(self,'Nsegments_calc'):
                        DP_a_wet = DP_a_wet/self.Geometry.Nbank
                    
                    DP_a_wet *= self.Thermal.DP_a_wet_tuning
                    
                    DP_a = f_dry * DP_a_dry + (1 - f_dry) * DP_a_wet
                    Pout_a = Pin_a + DP_a
                    
                    UA_o_wet = eta_a_wet * h_a_wet * A_a
                    Ntu_o_wet = UA_o_wet / (mdot_da * cp_da)
                    
                    # Wet analysis overall Ntu for two-phase refrigerant
                    # Minimum capacitance rate is by definition on the air side
                    # Ntu_wet is the NTU if the entire two-phase region were to be wetted
                    UA_wet = 1 / (cp_da / UA_o_wet + b_r / UA_i + Rw * b_r) #overall heat transfer coefficient
                    Ntu_wet = UA_wet / (mdot_da)
                    
                    # Wet effectiveness [-]
                    epsilon_wet = 1 - exp(-(1 - f_dry) * Ntu_wet)
                    
                    # Air saturated at refrigerant saturation temp [J/kg]
                    if self.Accurate:
                        h_s_s_o = HAPropsSI('H','T',Tin_r, 'P',Pin_a, 'R', 1.0) #[kJ/kg_da]
                    else:
                        Wsat = pl.GetSatHumRatio(Tin_r-273.15, Pin_a)
                        h_s_s_o = pl.GetMoistAirEnthalpy(Tin_r-273.15, Wsat)
                    
                    # Wet heat transfer [W]
                    Q_wet = epsilon_wet * mdot_da * (h_ac - h_s_s_o)
                    
                    # Total heat transfer [W]
                    Q = Q_wet + Q_dry
                    
                    # Air exit enthalpy [J/kg]
                    hout_a = h_ac - Q_wet / mdot_da
                    
                    # Saturated air enthalpy at effective surface temp [J/kg_da]
                    h_s_s_e = h_ac - (h_ac - hout_a) / (1 - exp(-(1 - f_dry) * Ntu_o_wet))
                    
                    # Effective surface temperature [K]
                    if self.Accurate:
                        T_s_e = HAPropsSI('T','H',h_s_s_e,'P',Pin_a,'R',1.0)
                    else:
                        T_s_e = brentq(lambda x: pl.GetSatAirEnthalpy(x,Pin_a) - h_s_s_e, -100,200)
                        T_s_e += 273.15
                    
                    # Outlet dry-bulb temp [K]
                    Tout_a = T_s_e + (T_ac - T_s_e) * exp(-(1 - f_dry) * Ntu_o_wet)
                    
                    # error
                    error_per = abs((Q - Q_old) / Q)
                    i += 1
                    
                    # heat flux
                    qflux = Q / A_r
        
                    # calculating refrigerant HTC
                    try:
                        self.Correlations.update(AS,self.Geometry,self.Thermal,'2phase',Pin_r,x_in,mdot_r,A_r,mode,q_flux=qflux)
                        h_r = self.Correlations.calculate_h_2phase()
                    except:
                        if not hasattr(self,"Solver_Error"):
                            self.Solver_Error = "Failed to calculate two-phase HTC in "
                        raise
                    h_r *= self.Thermal.h_r_2phase_tuning
    
                # outlet humidity ratio
                if self.Accurate:
                    Wout_a = HAPropsSI('W','H',hout_a,'T',Tout_a,'P',Pout_a)
                else:
                    Wout_a = pl.GetHumRatioFromEnthalpyAndTDryBulb(hout_a,Tout_a-273.15)
    
                # condensed water
                water_cond = (Win_a - Wout_a) * mdot_da #kg/sec
                if water_cond < 0 or f_dry == 1.0:
                    water_cond = 0
                    
                #Sensible heat transfer rate [kW]
                Q_sensible = mdot_da * cp_da * (Tin_a - Tout_a)
            
            if Q_sensible > Q:
                Q_sensible = Q
    
            # refrigerant outlet quality
            hout_r = hin_r + Q / (mdot_r)
            AS.update(CP.PQ_INPUTS,Pin_r,0.0)
            h_L = AS.hmass()
            AS.update(CP.PQ_INPUTS,Pin_r,1.0)
            h_V = AS.hmass()
            x_out = (hout_r - h_L) / (h_V - h_L)
            old_DP = 50
            error_DP = 50
            i = 0
            while error_DP > 1 and i < 5:
                # refrigerant pressure drop
                try:
                    self.Correlations.update(AS,self.Geometry,self.Thermal,'2phase',Pin_r,x_in,mdot_r,A_r,mode,var_2nd_out=x_out)
                    DP_friction = self.Correlations.calculate_dPdz_f_2phase() * L
                except:
                    if not hasattr(self,"Solver_Error"):
                        self.Solver_Error = "Failed to calculate two-phase friction pressure drop in "
                    raise
                try:
                    DP_accel = self.Correlations.calculate_dP_a()
                except:
                    if not hasattr(self,"Solver_Error"):
                        self.Solver_Error = "Failed to calculate two-phase acceleration pressure drop in "
                    raise
    
                DP_total = DP_friction + DP_accel
                DP_total *= self.Thermal.DP_r_2phase_tuning
                Pout_r = Pin_r + DP_total
                if Pout_r <= 0:
                    if not hasattr(self,"Solver_Error"):
                        self.Solver_Error = "Pressure drop is very high that negative pressure exists; please check mass flow rate from compressor or circuit length in "
                    raise ValueError("Outlet pressure is not positive value, pressure drop is very high")
    
                error_DP = abs(DP_total - old_DP)
                # correcting outlet quality with new pressure
                AS.update(CP.PQ_INPUTS,Pout_r,0.0)
                h_L = AS.hmass()
                AS.update(CP.PQ_INPUTS,Pout_r,1.0)
                h_V = AS.hmass()
                x_out = (hout_r-h_L)/(h_V-h_L)
                
                old_DP = DP_total
                i += 1
                
            # calculating charge
            AS.update(CP.HmassP_INPUTS,hout_r,Pout_r)
            Tout_r = AS.T()
            if x_in <= 0:
                xin_r_charge = np.finfo(float).eps
            elif x_in >= 1.0:
                xin_r_charge = 1.0 - np.finfo(float).eps
            else:
                xin_r_charge = x_in
            if x_out < 0:
                x_out_charge = 0
            elif x_out > 1.0:
                x_out_charge = 1.0
            else:
                x_out_charge = x_out
            q_flux = mdot_r * (hout_r - hin_r) / A_r
            try:
                self.Correlations.update(AS, self.Geometry,self.Thermal, '2phase',Pin_r,xin_r_charge,mdot_r,A_r,mode,var_2nd_out=x_out_charge,q_flux=q_flux)
                rho_2phase = self.Correlations.calculate_rho_2phase()
            except:
                if not hasattr(self,"Solver_Error"):
                    self.Solver_Error = "Failed to calculate two-phase charge in "
                raise
            
            Charge = rho_2phase * self.Geometry.A_CS * L
    
            Results = ValuesClass()
            Results.h_a_dry = h_a_dry            
            Results.UA_dry = UA_dry * f_dry
            Results.eta_a_dry = eta_a_dry
            Results.Tin_a = Tin_a
            Results.A_a = A_a
            Results.Pin_a = Pin_a
            Results.DP_a = Pin_a - Pout_a
            Results.Pout_a = Pout_a
            Results.mdot_da = mdot_da
            Results.mdot_ha = mdot_ha
            Results.Pin_r = Pin_r
            Results.Pout_r = float(Pout_r)
            Results.x_in = x_in
            Results.x_out = x_out
            Results.Tout_r = Tout_r
            Results.Tin_r = Tin_r
            Results.hin_r = hin_r
            Results.hout_r = float(hout_r)
            Results.A_r = A_r
            Results.mdot_r = mdot_r
            Results.Rw = Rw
            Results.h_r = h_r
            Results.hin_a = hin_a
            Results.Q_sensible = Q_sensible
            Results.Tout_a = Tout_a
            Results.f_dry = f_dry
            Results.Q = Q
            Results.hout_a = hout_a
            Results.Win_a = Win_a
            Results.Wout_a = Wout_a
            Results.DP_r = DP_total
            Results.Charge = Charge
            if f_dry != 1.0:
                Results.h_a_wet = h_a_wet
                Results.eta_a_wet = eta_a_wet
                Results.h_a = h_a_dry * f_dry + h_a_wet * (1 - f_dry)
                Results.eta_a = eta_a_dry * f_dry + eta_a_wet * (1 - f_dry)
                Results.UA_wet = UA_wet * (1 - f_dry)
                Results.UA = UA_wet * (1 - f_dry) + UA_dry * f_dry
            else:
                Results.UA = UA_dry
                Results.h_a = h_a_dry
                Results.eta_a = eta_a_dry
            Results.w_phase = w_2phase
    
            if f_dry == 1.0:
                Results.water_condensed = 0.0
            else:
                Results.water_condensed = water_cond #kg/s

        else: # fake results for not solving segment
            # producing results
            Results = ValuesClass()
            Results.h_a_dry = 0
            Results.UA_dry = 0
            Results.eta_a_dry = 0
            Results.Tin_a = Tin_a
            Results.A_a = 0
            Results.Pin_a = Pin_a
            Results.DP_a = Pin_a - Pout_a
            Results.Pout_a = Pout_a
            Results.mdot_da = mdot_da
            Results.mdot_ha = mdot_ha
            Results.Pin_r = Pin_r
            Results.Pout_r = Pin_r
            Results.x_in = x_in
            Results.x_out = x_in
            Results.Tout_r = Tin_r
            Results.Tin_r = Tin_r
            Results.hin_r = hin_r
            Results.hout_r = hin_r
            Results.A_r = 0
            Results.mdot_r = mdot_r
            Results.Rw = Rw
            Results.h_r = 0
            Results.hin_a = hin_a
            Results.Q_sensible = 0
            Results.Tout_a = Tin_a
            Results.f_dry = 1
            Results.Q = 0
            Results.hout_a = hin_a
            Results.Win_a = Win_a
            Results.Wout_a = Win_a
            Results.DP_r = 0
            Results.Charge = 0
            Results.UA = 0
            Results.h_a = 0
            Results.eta_a = 0
            Results.w_phase = 0
            Results.water_condensed = 0

        return Results

    def solver_1phase(self,Ref_inputs,Air_inputs,w_1phase = 1.0):
        '''the function will solve a 1 phase segment'''
        AS = self.AS
        Pin_r = Ref_inputs.Pin_r
        hin_r = Ref_inputs.hin_r        
        Tin_r = Ref_inputs.Tin_r
        x_in = Ref_inputs.x_in
        AS.update(CP.HmassP_INPUTS,hin_r,Pin_r)
        cp_r = AS.cpmass()
        L = Ref_inputs.L * w_1phase * Ref_inputs.L_fraction + np.finfo(float).eps
        A_r = self.Geometry.inner_circum * L
        mdot_r = self.Thermal.mdot_r / self.Geometry.Nsubcircuits
        Rw = log(self.Geometry.OD/self.Geometry.ID)/(2*pi*self.Thermal.kw*L)
        
        # calculating inlet and outlet air properties
        hin_a = Air_inputs.hin_a
        hout_a = Air_inputs.hout_a
        Pin_a = Air_inputs.Pin_a
        Pout_a = Air_inputs.Pout_a
        Win_a = Air_inputs.Win_a
        Wout_a = Air_inputs.Wout_a
        
        if self.Accurate:            
            Tin_a = HAPropsSI('T','H',hin_a,'P',Pin_a,'W',Win_a)
            Tout_a = HAPropsSI('T','H',hout_a,'P',Pout_a,'W',Wout_a)
        else:
            Tin_a = pl.GetTDryBulbFromEnthalpyAndHumRatio(hin_a, Win_a) + 273.15
            Tout_a = pl.GetTDryBulbFromEnthalpyAndHumRatio(hout_a, Wout_a) + 273.15
        
        mdot_ha = Air_inputs.mdot_ha * w_1phase * Ref_inputs.L_fraction + np.finfo(float).eps
        
        # calculating air thermal heat transfer properties
        h_a_dry, DP_a_dry, eta_a_dry = self.fins_calculate(Pin_a,Pout_a,Tin_a,Tout_a,Win_a,Wout_a,mdot_ha/w_1phase,L/w_1phase,Wet=False,Accurate=self.Accurate)
        h_a_dry *= self.Thermal.h_a_dry_tuning
        cp_da = self.Fins.cp_da
        if self.Thermal.FinsOnce == True:
            if hasattr(self,'Nsegments_calc'):
                DP_a_dry = DP_a_dry / self.Geometry.Nbank
        
        DP_a_dry *= self.Thermal.DP_a_dry_tuning
        Pout_a = Pin_a + DP_a_dry

        # air side total area
        if self.Thermal.FinsOnce == True:
            A_a = self.Fins.Ao * w_1phase / (self.Nsegments_calc * self.Geometry.Ntubes_per_subcircuit) * Ref_inputs.L_fraction + np.finfo(float).eps
        else:
            A_a = self.Fins.Ao * Ref_inputs.L_fraction + np.finfo(float).eps

        # dry air flow rate
        mdot_da = mdot_ha / (1 + Win_a)

        # heater is condenser, cooler is evaporator
        if Tin_a > Tin_r:
            mode = 'cooler'
        else:
            mode = 'heater'
        
        # dew pooint temperature of inlet air
        if self.Accurate:
            Tdp = HAPropsSI('D','T',Tin_a,'P',Pin_a,'W',Win_a)
        else:
            Tdp = pl.GetTDewPointFromHumRatio(Tin_a-273.15, Win_a, Pin_a) + 273.15

        if L > 1e-7:
            
            # refrigerant side heat transfer coefficient
            try:
                self.Correlations.update(AS,self.Geometry,self.Thermal,'1phase',Pin_r,hin_r,mdot_r,A_r,mode)
                h_r = self.Correlations.calculate_h_1phase()
            except:
                if not hasattr(self,"Solver_Error"):
                    self.Solver_Error = "Failed to calculate single-phase HTC in "
                raise
            if x_in >= 1.0:
                h_r *= self.Thermal.h_r_superheat_tuning
            elif x_in <= 0.0:
                h_r *= self.Thermal.h_r_subcooling_tuning
            else:
                raise
            
            # Internal UA between fluid flow and internal surface
            UA_i = h_r * A_r 
            # External dry UA between outer surface and free stream
            UA_o_dry = eta_a_dry * h_a_dry * A_a 
            
            # overall heat transfer coefficient        
            UA_dry = 1 / (1 / (UA_i) + 1 / (UA_o_dry) + Rw);
            
            # Min and max capacitance rates [W/K]
            Cmin = min([cp_r * mdot_r, cp_da * mdot_da])
            Cmax = max([cp_r * mdot_r, cp_da * mdot_da])
            
            # Capacitance rate ratio [-]
            C_star = Cmin / Cmax
            
            # NTU of refrigerant
            NTU_i = UA_i / (mdot_r * cp_r)
            
            # NTU of air
            NTU_o_dry = UA_o_dry / (mdot_da * cp_da)
            
            # Ntu overall [-]
            NTU_dry = UA_dry / Cmin
            
            #Crossflow effectiveness (e.g. see Incropera - Fundamentals of Heat and Mass Transfer, 2007, p. 662)
            if (cp_r * mdot_r) < (cp_da * mdot_da):
                epsilon_dry = 1 - exp(-C_star**(-1) * (1 - exp(-C_star * (NTU_dry))))
                #Cross flow, single phase, cmax is airside, which is unmixed
            else:
                epsilon_dry = (1 / C_star) * (1 - exp(-C_star * (1 - exp(-NTU_dry))))
                #Cross flow, single phase, cmax is refrigerant side, which is mixed
            
            # Dry heat transfer [W]
            Q_dry = epsilon_dry * Cmin * (Tin_a - Tin_r)
            
            # Dry-analysis air outlet temp [K]
            Tout_a_dry = Tin_a - Q_dry / (mdot_da * cp_da)
            
            # Dry-analysis outlet temp [K]
            Tout_r_dry = Tin_r + Q_dry / (mdot_r * cp_r)
            
            # Dry-analysis air outlet enthalpy from energy balance [J/kg]
            hout_a = hin_a - Q_dry / mdot_da
           
            #dry analysis surface temperature at refrigerant inlet (at inlet and outlet air points)
            Tw_i_a = Tin_r + UA_dry * (Rw + 1 / UA_i) * (Tin_a - Tin_r)
            Tw_i_b = Tin_r + UA_dry * (Rw + 1 / UA_i) * (Tout_a_dry - Tin_r)
            Tw_i = (Tw_i_a + Tw_i_b) / 2
    
            #dry analysis surface temperature at refrigerant outlet (at inlet and outlet air points)
            Tw_o_a = Tout_r_dry + UA_dry * (Rw + 1 / UA_i) * (Tin_a - Tout_r_dry)
            Tw_o_b = Tout_r_dry + UA_dry * (Rw + 1 / UA_i) * (Tout_a_dry - Tout_r_dry)
            Tw_o = (Tw_o_a + Tw_o_b) / 2

            #dry analysis average surface temperature
            Tw = (Tw_o + Tw_i) / 2
            
            # Air outlet humidity ratio [-]
            Wout_a = Win_a
    
            Tout_r = Tout_r_dry
            
            Tout_a = Tout_a_dry
                        
            if Tw < Tdp:
                # There is some wetting, the coil could be partially or fully wet
                Tout_r = Tin_r
                eps = 1e-5
                i = 1
                b_r = cair_sat(Tin_r) * 1000
                Q_wet = 0
                water_cond = np.finfo(float).eps
                mu_f = 1e-3
                Error_Q = 100
                while ((i <= 3) or Error_Q > eps) and (i<20):
                    
                    # saving old value of Q_wet
                    Q_wet_old = Q_wet
                    
                    # saturated air enthalpy at refrigerant inlet temperature
                    if self.Accurate:
                        h_s_w_i = HAPropsSI('H','T',Tin_r, 'P',Pin_a, 'R', 1.0) #[kJ/kg_da]
                    else:
                        Wsat = pl.GetSatHumRatio(Tin_r-273.15, Pin_a)
                        h_s_w_i = pl.GetMoistAirEnthalpy(Tin_r-273.15, Wsat)
                                    
                    # calculating wet air properties
                    bw_m, h_a_wet, DP_a_wet, eta_a_wet = self.fins_calculate(Pin_a,Pout_a,Tin_a,Tout_a,Win_a,Wout_a,mdot_ha/w_1phase,L/w_1phase,Wet=True,Accurate=self.Accurate,Tw_o = Tw, water_cond = water_cond, mu_f = mu_f)
                    h_a_wet *= self.Thermal.h_a_wet_tuning
                    cp_da = self.Fins.cp_da
                    
                    # Effective humid air mass flow ratio
                    m_star = min([cp_r * mdot_r / b_r, mdot_da])/max([cp_r * mdot_r / b_r, mdot_da])
                    
                    # minimum effective flow rate
                    mdot_min = min([cp_r * mdot_r / b_r, mdot_da])
                    
                    # new NTU_o_wet
                    NTU_o_wet = eta_a_wet * h_a_wet * A_a / (mdot_da * cp_da)
                    
                    # Wet analysis overall NTU
                    if (cp_r * mdot_r > b_r * mdot_da):
                        NTU_wet = NTU_o_dry / (1 + m_star * (NTU_o_wet / NTU_i))
                    else:
                        NTU_wet = NTU_o_dry / (1 + m_star * (NTU_i / NTU_o_wet))
                    
                    # wet analysis UA value
                    UA_wet = NTU_wet * min([cp_r * mdot_r, b_r * mdot_da])
                    
                    # crossflow effectiveness for wet analysis
                    if (cp_r * mdot_r) < (b_r * mdot_da):
                        #Cross flow, single phase, cmax is airside, which is unmixed
                        epsilon_wet = 1 - exp(-m_star**(-1) * (1 - exp(-m_star * (NTU_wet))))
                    else:
                        #Cross flow, single phase, cmax is refrigerant side, which is mixed
                        epsilon_wet = (1 / m_star) * (1 - exp(-m_star * (1 - exp(-NTU_wet))))
                    
                    # wet analysis heat transfer rate
                    Q_wet = epsilon_wet * mdot_min * (hin_a - h_s_w_i)
                    
                    # Air outlet enthalpy
                    hout_a = hin_a - Q_wet / mdot_da
                    
                    # refrigerant outlet temperature
                    Tout_r = Tin_r + Q_wet / (mdot_r * cp_r)
                    
                    # refrigerant outler saturated surface enthalpy
                    if self.Accurate:
                        h_s_w_o = HAPropsSI('H','T',Tout_r, 'P',Pin_a, 'R', 1.0) #[kJ/kg_da]
                    else:
                        Wsat = pl.GetSatHumRatio(Tout_r-273.15, Pin_a)
                        h_s_w_o = pl.GetMoistAirEnthalpy(Tout_r-273.15, Wsat)
                    
                    # Local UA* and b_r
                    b_r = cair_sat((Tin_r + Tout_r) / 2) * 1000
                    UA_star = 1 / (cp_da / (eta_a_wet * h_a_wet * A_a) + b_r * (1 / (h_r * A_r) + Rw))
                    
                    # wet-analysis outer surface tempererature at outlet
                    Tw_o = Tout_r + UA_star / (h_r * A_r) * (hin_a - h_s_w_o)
    
                    # wet-analysis outer surface tempererature at inlet
                    Tw_i = Tin_r + UA_star / (h_r * A_r) * (hin_a - h_s_w_o)
                                    
                    # wet-analysis average outer surface tempererature
                    Tw = (Tw_o + Tw_i) / 2

                    # Error in Q_wet
                    Error_Q = abs((Q_wet - Q_wet_old) / Q_wet)
                    
                    # increasing counter
                    i += 1
                
                # outlet humidity ratio
                if self.Accurate:
                    Wout_a = HAPropsSI('W','H',hout_a,'T',Tout_a,'P',Pout_a)
                else:
                    Wout_a = pl.GetHumRatioFromEnthalpyAndTDryBulb(hout_a,Tout_a-273.15)
                
                # condensed water
                water_cond = (Win_a - Wout_a) * mdot_da #kg/sec
                if water_cond < 0:
                    water_cond = 0
                    
                # wet-analysis saturation enthalpy
                h_s_s_e = hin_a + (hout_a - hin_a) / (1 - exp(-NTU_o_wet))
                
                # surface effective temperature
                if self.Accurate:
                    T_s_e = HAPropsSI('T','H',h_s_s_e,'P',Pin_a,'R',1.0)
                else:
                    T_s_e = brentq(lambda x: pl.GetSatAirEnthalpy(x,Pin_a) - h_s_s_e, -100,200)
                    T_s_e += 273.15
                
                # Air outlet temperature based on effective temperature
                Tout_a = T_s_e + (Tin_a - T_s_e) * exp(-NTU_o_dry)
    
                # sensible heat transfer 
                Q_sensible = mdot_da * cp_da * (Tin_a - Tout_a)
                
                # dry fraction
                f_dry = 0.0
                
                Q = Q_wet
                                
            else:
                # all dry, since refrigerant outlet surface temperature is dry
                f_dry = 1.0
                Q = Q_dry
                Q_sensible = Q
                hout_a = hin_a - Q / mdot_da
                Wout_a = Win_a
    
            # refrigerant pressure drop
            try:
                self.Correlations.update(AS,self.Geometry,self.Thermal,'1phase',Pin_r,hin_r,mdot_r,A_r,mode)
                DP_total = self.Correlations.calculate_dPdz_f_1phase() * L
            except:
                if not hasattr(self,"Solver_Error"):
                    self.Solver_Error = "Failed to calculate single-phase pressure drop in "
                raise
            if x_in >= 1.0:
                DP_total *= self.Thermal.DP_r_superheat_tuning
            elif x_in <= 0.0:
                DP_total *= self.Thermal.DP_r_subcooling_tuning
            else:
                raise
            Pout_r = Pin_r + DP_total
            if Pout_r <= 0:
                if not hasattr(self,"Solver_Error"):
                    self.Solver_Error = "Pressure drop is very high that negative pressure exists; please check mass flow rate from compressor or circuit length in "
                raise ValueError("Outlet pressure is not positive value, pressure drop is very high")
            hout_r = hin_r + Q/(mdot_r)
            AS.update(CP.HmassP_INPUTS,hout_r,Pout_r)
            Tout_r = AS.T()
            AS.update(CP.PQ_INPUTS,Pout_r,0.0)
            h_L = AS.hmass()
            AS.update(CP.PQ_INPUTS,Pout_r,1.0)
            h_V = AS.hmass()
            x_out = (hout_r-h_L)/(h_V-h_L)
                                        
            AS.update(CP.HmassP_INPUTS,hin_r,Pin_r)
            rho_1phase = AS.rhomass()
            Charge = rho_1phase * self.Geometry.A_CS * L
            
            # producing results
            Results = ValuesClass()
            Results.h_a_dry = h_a_dry            
            Results.UA_dry = UA_dry * f_dry
            Results.eta_a_dry = eta_a_dry
            Results.Tin_a = Tin_a
            Results.A_a = A_a
            Results.Pin_a = Pin_a
            Results.DP_a = Pin_a - Pout_a
            Results.Pout_a = Pout_a
            Results.mdot_da = mdot_da
            Results.mdot_ha = mdot_ha
            Results.Pin_r = Pin_r
            Results.Pout_r = float(Pout_r)
            Results.x_in = x_in
            Results.x_out = x_out
            Results.Tout_r = Tout_r
            Results.Tin_r = Tin_r
            Results.hin_r = hin_r
            Results.hout_r = float(hout_r)
            Results.A_r = A_r
            Results.mdot_r = mdot_r
            Results.Rw = Rw
            Results.h_r = h_r
            Results.hin_a = hin_a
            Results.Q_sensible = Q_sensible
            Results.Tout_a = Tout_a
            Results.f_dry = f_dry
            Results.Q = Q
            Results.hout_a = hout_a
            Results.Win_a = Win_a
            Results.Wout_a = Wout_a
            Results.DP_r = DP_total
            Results.Charge = Charge
            if f_dry != 1.0:
                Results.h_a_wet = h_a_wet
                Results.eta_a_wet = eta_a_wet
                Results.h_a = h_a_dry * f_dry + h_a_wet * (1 - f_dry)
                Results.eta_a = eta_a_dry * f_dry + eta_a_wet * (1 - f_dry)
                Results.UA_wet = UA_wet * (1 - f_dry)
                Results.UA = UA_wet * (1 - f_dry) + UA_dry * f_dry
            else:
                Results.UA = UA_dry
                Results.h_a = h_a_dry
                Results.eta_a = eta_a_dry
            Results.w_phase = w_1phase
            if f_dry == 1.0:
                Results.water_condensed = 0.0
            else:
                Results.water_condensed = water_cond #kg/s
        else: # fake results for not solving segment
            # producing results
            Results = ValuesClass()
            Results.h_a_dry = 0
            Results.UA_dry = 0
            Results.eta_a_dry = 0
            Results.Tin_a = Tin_a
            Results.A_a = 0
            Results.Pin_a = Pin_a
            Results.DP_a = Pin_a - Pout_a
            Results.Pout_a = Pout_a
            Results.mdot_da = mdot_da
            Results.mdot_ha = mdot_ha
            Results.Pin_r = Pin_r
            Results.Pout_r = Pin_r
            Results.x_in = x_in
            Results.x_out = x_in
            Results.Tout_r = Tin_r
            Results.Tin_r = Tin_r
            Results.hin_r = hin_r
            Results.hout_r = hin_r
            Results.A_r = 0
            Results.mdot_r = mdot_r
            Results.Rw = Rw
            Results.h_r = 0
            Results.hin_a = hin_a
            Results.Q_sensible = 0
            Results.Tout_a = Tin_a
            Results.f_dry = 1
            Results.Q = 0
            Results.hout_a = hin_a
            Results.Win_a = Win_a
            Results.Wout_a = Win_a
            Results.DP_r = 0
            Results.Charge = 0
            Results.UA = 0
            Results.h_a = 0
            Results.eta_a = 0
            Results.w_phase = 0
            Results.water_condensed = 0
            
        return Results

    def solver_2phase_phase(self,Ref_inputs,Air_inputs,w_2phase=1.0):
        '''The function is used to solve 2phase segment with phase solver'''
        # will solve a 2 phase segment
        AS = self.AS
        Pin_r = Ref_inputs.Pin_r
        x_in = Ref_inputs.x_in 
        hin_r = Ref_inputs.hin_r
        AS.update(CP.PQ_INPUTS,Pin_r,x_in)
        Tin_r = AS.T()
        L = Ref_inputs.L*w_2phase
        A_r = self.Geometry.inner_circum * L
        mdot_r = self.Thermal.mdot_r / self.Geometry.Nsubcircuits
        Rw = log(self.Geometry.OD/self.Geometry.ID)/(2*pi*self.Thermal.kw*L)
        
        # calculating inlet and outlet air properties
        hin_a = Air_inputs.hin_a
        hout_a = Air_inputs.hout_a
        Pin_a = Air_inputs.Pin_a
        Pout_a = Air_inputs.Pout_a
        Win_a = Air_inputs.Win_a
        Wout_a = Air_inputs.Wout_a
        if self.Accurate:            
            Tin_a = HAPropsSI('T','H',hin_a,'P',Pin_a,'W',Win_a)
            Tout_a = HAPropsSI('T','H',hout_a,'P',Pout_a,'W',Wout_a)
        else:
            Tin_a = pl.GetTDryBulbFromEnthalpyAndHumRatio(hin_a, Win_a) + 273.15
            Tout_a = pl.GetTDryBulbFromEnthalpyAndHumRatio(hout_a, Wout_a) + 273.15
        mdot_ha = Air_inputs.mdot_ha * w_2phase
        
        # Calculating air thermal heat transfer properties
        h_a_dry, DP_a_dry, eta_a_dry = self.fins_calculate(Pin_a,Pout_a,Tin_a,Tout_a,Win_a,Wout_a,mdot_ha/w_2phase,L/w_2phase,Wet=False,Accurate=self.Accurate)
        h_a_dry *= self.Thermal.h_a_dry_tuning
        cp_da = self.Fins.cp_da
        
        DP_a_dry *= self.Thermal.DP_a_dry_tuning
        Pout_a = Pin_a + DP_a_dry

        L_full_subcircuit = self.Geometry.Ntubes_per_subcircuit * self.Geometry.Ltube
        ratio = self.Geometry.Lsubcircuit / L_full_subcircuit # due to sub HX

        # air side total area

        A_a = self.Fins.Ao * L / self.Geometry.Lsubcircuit * ratio
        
        # dry air flow rate
        mdot_da = mdot_ha / (1 + Win_a)
        
        # heater is condenser, cooler is evaporator
        if Tin_a > Tin_r:
            mode = 'cooler'
        else:
            mode = 'heater'
                
        # dew point temperature of inlet air
        if self.Accurate:
            Tdp = HAPropsSI('D','T',Tin_a,'P',Pin_a,'W',Win_a)
        else:
            Tdp = pl.GetTDewPointFromHumRatio(Tin_a-273.15, Win_a, Pin_a) + 273.15
            
        h_r = 1500

        #approximate overall heat transfer coefficient
        UA_approx = 1/(1/(h_a_dry * A_a * eta_a_dry) + 1/(h_r * A_r) + Rw);
        
        #Number of transfer units
        Ntu_approx = UA_approx / (mdot_da * cp_da);
        
        #since Cr=0, e.g. see Incropera - Fundamentals of Heat and Mass Transfer, 2007, p. 690
        epsilon_approx = 1 - exp(-Ntu_approx);
        
        # approximate heat transfer
        Q_approx = epsilon_approx * mdot_da * cp_da * (Tin_a - Tin_r);
        Q = Q_approx
        error_Q = 100
        Q_old_major = 0
        x_out = x_in
        iter_num = 0
        while error_Q > 0.001 and iter_num < 10:
            qflux = Q / A_r
            if x_out > 1.0:
                x_out = 1.0
            elif x_out < 0.0:
                x_out = 0.0
            # calculating refrigerant HTC
            try:
                self.Correlations.update(AS,self.Geometry,self.Thermal,'2phase',Pin_r,x_in,mdot_r,A_r,mode,q_flux=qflux,var_2nd_out=x_out)
                h_r = self.Correlations.calculate_h_2phase()
            except:
                if not hasattr(self,"Solver_Error"):
                    self.Solver_Error = "Failed to calculate two-phase HTC in "
                raise
            h_r *= self.Thermal.h_r_2phase_tuning
            
            # calculating heat transfer in case of dry conditions
            
            #over heat thermal transfer coefficients of internal and external
            UA_o_dry = (h_a_dry * A_a * eta_a_dry)
            UA_i = (h_r * A_r)

            #overall heat transfer coefficient in dry conditions
            UA_dry = 1 / (1 / UA_o_dry +1 / UA_i + Rw); 
            
            #Number of transfer units
            Ntu_dry = UA_dry / (mdot_da * cp_da)
            
            #since Cr=0, e.g. see Incropera - Fundamentals of Heat and Mass Transfer, 2007, p. 690
            epsilon_dry = 1 - exp(-Ntu_dry)  
            
            #heat transfer in dry conditions
            Q_dry = epsilon_dry * mdot_da * cp_da * (Tin_a - Tin_r)
            
            # Dry-analysis air outlet temp [K]
            Tout_a_dry = Tin_a - Q_dry / (mdot_da * cp_da)
            
            #wall outside temperature (at inlet and outlet air points, Tin_r is assumed constant)
            Tw_o_a = Tin_r + UA_dry * (1 / UA_i + Rw) * (Tin_a - Tin_r)
            Tw_o_b = Tin_r + UA_dry * (1 / UA_i + Rw) * (Tout_a_dry - Tin_r)
            
            Wout_a = Win_a
            
            Tout_a = Tout_a_dry
            
            
            if Tw_o_b > Tdp:
                #All dry, since surface at outlet dry
                f_dry = 1.0
                Q = Q_dry #[W]
                Q_sensible = Q #[W]
                hout_a = hin_a - Q / mdot_da #[J/kg_da]
            else:
                if Tw_o_a < Tdp:
                    #All wet, since surface at refrigerant inlet is wet
                    f_dry = 0.0
                    Q_dry = 0.0
                    T_ac = Tin_a # temperature at onset of wetted wall
                    h_ac = hin_a # enthalpy at onset of wetted surface
                else:
                    # Partially wet, partially dry
                    # Based on equating heat fluxes at the wall which is at dew point UA_i*(Tw-Ti)=UA_o*(To-Tw)
                    T_ac = Tdp + UA_i / UA_o_dry * (Tdp - Tin_r)
                    
                    # Dry effectiveness (minimum capacitance on the air side by definition)
                    epsilon_dry = (Tin_a - T_ac) / (Tin_a - Tin_r)
                    
                    # Dry fraction found by solving epsilon=1-exp(-f_dry*Ntu) for known epsilon from above equation
                    f_dry = -1.0 / Ntu_dry * log(1.0 - epsilon_dry)
                    
                    # Enthalpy, using air humidity at the interface between wet and dry surfaces, which is same humidity ratio as inlet
                    if self.Accurate:
                        h_ac = HAPropsSI('H','T',T_ac,'P',Pin_a,'W',Win_a) #[J/kg_da]
                    else:
                        h_ac = pl.GetMoistAirEnthalpy(T_ac-273.15, Win_a)
                    
                    # Dry heat transfer
                    Q_dry = mdot_da * cp_da * (Tin_a - T_ac)
                
                # intial guess
                error_per = 1
                UA_o_wet = UA_o_dry
                eta_a_wet = eta_a_dry
                h_a_wet = h_a_dry
                Q = Q_dry
                i = 1
                water_cond = np.finfo(float).eps
                UA_wet = UA_dry
                b_r = cair_sat(Tin_r) * 1000
                mu_f = 1e-3
                if self.Accurate:
                    h_s_w = HAPropsSI('H','T',Tin_r, 'P',Pin_a, 'R', 1.0) #[kJ/kg_da]
                else:
                    Wsat = pl.GetSatHumRatio(Tin_r-273.15, Pin_a)
                    h_s_w = pl.GetMoistAirEnthalpy(Tin_r-273.15, Wsat)
                while (error_per > 0.001) and i <= 15:
                    UA_star = 1 / (cp_da / (eta_a_wet * h_a_wet * A_a) + b_r * (1 / (h_r * A_r) + b_r * Rw))
                    
                    Tw_o = Tin_r + UA_star / (h_r * A_r) * (hin_a - h_s_w)
                    
                    Q_old = Q
                    
                    bw_m, h_a_wet, DP_a_wet, eta_a_wet = self.fins_calculate(Pin_a,Pout_a,Tin_a,Tout_a,Win_a,Wout_a,mdot_ha/w_2phase,L/w_2phase,Wet=True,Accurate=self.Accurate,Tw_o = Tw_o, water_cond = water_cond, mu_f = mu_f)
                    h_a_wet *= self.Thermal.h_a_wet_tuning
                    cp_da = self.Fins.cp_da
                    
                    DP_a_wet *= self.Thermal.DP_a_wet_tuning
                    
                    DP_a = f_dry * DP_a_dry + (1 - f_dry) * DP_a_wet
                    Pout_a = Pin_a + DP_a
        
                    UA_o_wet = eta_a_wet * h_a_wet * A_a
                    Ntu_o_wet = UA_o_wet / (mdot_da * cp_da)
                    
                    # Wet analysis overall Ntu for two-phase refrigerant
                    # Minimum capacitance rate is by definition on the air side
                    # Ntu_wet is the NTU if the entire two-phase region were to be wetted
                    UA_wet = 1 / (cp_da / UA_o_wet + b_r / UA_i + Rw * b_r) #overall heat transfer coefficient
                    Ntu_wet = UA_wet / (mdot_da)
                    
                    # Wet effectiveness [-]
                    epsilon_wet = 1 - exp(-(1 - f_dry) * Ntu_wet)
                    
                    # Air saturated at refrigerant saturation temp [J/kg]
                    if self.Accurate:
                        h_s_s_o = HAPropsSI('H','T',Tin_r, 'P',Pin_a, 'R', 1.0) #[kJ/kg_da]
                    else:
                        Wsat = pl.GetSatHumRatio(Tin_r-273.15, Pin_a)
                        h_s_s_o = pl.GetMoistAirEnthalpy(Tin_r-273.15, Wsat)
                    
                    # Wet heat transfer [W]
                    Q_wet = epsilon_wet * mdot_da * (h_ac - h_s_s_o)
                    
                    # Total heat transfer [W]
                    Q = Q_wet + Q_dry
                    
                    # Air exit enthalpy [J/kg]
                    hout_a = h_ac - Q_wet / mdot_da
                    
                    # Saturated air enthalpy at effective surface temp [J/kg_da]
                    h_s_s_e = h_ac - (h_ac - hout_a) / (1 - exp(-(1 - f_dry) * Ntu_o_wet))
                    
                    # Effective surface temperature [K]
                    if self.Accurate:
                        T_s_e = HAPropsSI('T','H',h_s_s_e,'P',Pin_a,'R',1.0)
                    else:
                        T_s_e = brentq(lambda x: pl.GetSatAirEnthalpy(x,Pin_a) - h_s_s_e, -100,200)
                        T_s_e += 273.15
                    
                    # Outlet dry-bulb temp [K]
                    Tout_a = T_s_e + (T_ac - T_s_e) * exp(-(1 - f_dry) * Ntu_o_wet)
                    
                    # outlet humidity ratio
                    if self.Accurate:
                        Wout_a = HAPropsSI('W','H',hout_a,'T',Tout_a,'P',Pout_a)
                    else:
                        Wout_a = pl.GetHumRatioFromEnthalpyAndTDryBulb(hout_a,Tout_a-273.15)
                    
                    # condensed water
                    water_cond = (Win_a - Wout_a) * mdot_da #kg/
                    if water_cond < 0:
                        water_cond = 0
                    
                    # error
                    error_per = abs((Q - Q_old) / Q)
                    i += 1
                    
                #Sensible heat transfer rate [kW]
                Q_sensible = mdot_da * cp_da * (Tin_a - Tout_a)
                if Q_sensible > Q:
                    Q_sensible = Q

            # refrigerant outlet quality
            hout_r = hin_r + Q / (mdot_r)
            AS.update(CP.PQ_INPUTS,Pin_r,0.0)
            h_L = AS.hmass()
            AS.update(CP.PQ_INPUTS,Pin_r,1.0)
            h_V = AS.hmass()
            x_out = (hout_r - h_L) / (h_V - h_L)
            
            # refrigerant pressure drop
            try:
                self.Correlations.update(AS,self.Geometry,self.Thermal,'2phase',Pin_r,x_in,mdot_r,A_r,mode,var_2nd_out=x_out)
                DP_friction = self.Correlations.calculate_dPdz_f_2phase() * (L)
            except:
                if not hasattr(self,"Solver_Error"):
                    self.Solver_Error = "Failed to calculate two-phase friction pressure drop in "
                raise
            try:
                DP_accel = self.Correlations.calculate_dP_a()
            except:
                if not hasattr(self,"Solver_Error"):
                    self.Solver_Error = "Failed to calculate two-phase acceleration pressure drop in "
                raise
            DP_total = DP_friction + DP_accel
            DP_total *= self.Thermal.DP_r_2phase_tuning
            Pout_r = Pin_r + DP_total
            
            # calculating bends pressure drop
            # from Christoffersen, B. R, J. C. Chato, J. P. Wattelet, and A. L. de Souza. 1993. Heat Transfer and Flow Characteristics of R-22, R-321R-125, and R-134a in Smooth and Micro-Fin Tubes. M.S. Thesis, Department of Mechanical and Industrial Engineering, University of Illinois, Urbana.
            N_bends = int(L / self.Geometry.Ltube)
            DP = Pout_r - Pin_r
            Dx = x_out - x_in
            P_r_bend_range = [Pin_r + DP*(i + 1)/N_bends for i in range(N_bends)]
            x_r_bend_range = [x_in + Dx*(i + 1)/N_bends for i in range(N_bends)]
            Dh = self.Geometry.Dh
            Radius = self.Geometry.Pt / 2
            Length = pi * Radius
            G_r = mdot_r / self.Geometry.A_CS
            
            for num,(P_r,x_r) in enumerate(zip(P_r_bend_range, x_r_bend_range)):
                try:
                    if x_r > 1.0:
                        x_r = 1.0 - np.finfo(float).eps
                    elif x_r < 0.0:
                        x_r = 0.0 + np.finfo(float).eps
                
                    AS.update(CP.PQ_INPUTS,P_r,0.0)
                    Tbubble = AS.T()
                    mu_f = AS.viscosity()
                    rho_f = AS.rhomass()
                    
                    AS.update(CP.PQ_INPUTS,P_r,1.0)
                    Tdew = AS.T()
                    mu_g = AS.viscosity()
                    rho_g = AS.rhomass()
                    
                    Re_f = G_r * (1 - x_r) * Dh / mu_f
                    
                    Xtt = pow(mu_f / mu_g, 0.1) * pow(rho_g / rho_f, 0.5) * pow((1 - x_r) / x_r, 0.9)
                    dpdz_f = -self.Correlations.Chisholm(self.AS,G_r,self.Geometry.Dh,x_r,Tbubble,Tdew)
                    Cd = 2 * Radius
                    delta = pow(Dh / (Cd), 0.5)
                    epslon = 6.93E-5 * pow(Xtt, -0.712) * delta * Re_f / 2
                    DP_r_friction = dpdz_f * Length
                    v_avg = (1 - x_r) * (1 / rho_f) + (x_r) * (1 / rho_g)
                    DP_r_turning = -pow(G_r, 2) * v_avg * epslon / 2
                    DP_r_bend = DP_r_friction + DP_r_turning
                    DP_total += DP_r_bend
                except:
                    if not hasattr(self,"Solver_Error"):
                        self.Solver_Error = "Failed to calculate bend ("+str(num+1)+") pressure drop in "
                    raise
                    
            Pout_r = Pin_r + DP_total
            if Pout_r <= 0:
                if not hasattr(self,"Solver_Error"):
                    self.Solver_Error = "Pressure drop is very high that negative pressure exists; please check mass flow rate from compressor or circuit length in "
                raise ValueError("Pressure drop is very high, the pressure became negative")
            # correcting outlet quality with new pressure
            AS.update(CP.PQ_INPUTS,Pout_r,0.0)
            h_L = AS.hmass()
            AS.update(CP.PQ_INPUTS,Pout_r,1.0)
            h_V = AS.hmass()
            x_out = (hout_r-h_L)/(h_V-h_L)
            
            error_Q = abs(Q - Q_old_major)/abs(Q)
            Q_old_major = Q
            iter_num += 1
            
        # calculating charge
        try:
            AS.update(CP.HmassP_INPUTS,hout_r,Pout_r)
            Tout_r = AS.T()
            Success = True
        except:
            AS.update(CP.PQ_INPUTS,Pin_r,0.0)
            Tbubble = AS.T()
            AS.update(CP.PQ_INPUTS,Pin_r,1.0)
            Tdew = AS.T()
            Success = False
            Tout_r = 200
        if Success:
            if x_in <= 0:
                xin_r_charge = np.finfo(float).eps
            elif x_in >= 1.0:
                xin_r_charge = 1.0 - np.finfo(float).eps
            else:
                xin_r_charge = x_in
            if x_out < 0:
                x_out_charge = 0
            elif x_out > 1.0:
                x_out_charge = 1.0
            else:
                x_out_charge = x_out
            q_flux = mdot_r * (hout_r - hin_r) / A_r
            try:
                self.Correlations.update(AS, self.Geometry,self.Thermal, '2phase',Pin_r,xin_r_charge,mdot_r,A_r,mode,var_2nd_out=x_out_charge,q_flux=q_flux)
                rho_2phase = self.Correlations.calculate_rho_2phase()
            except:
                if not hasattr(self,"Solver_Error"):
                    self.Solver_Error = "Failed to calculate two-phase charge in "
                raise
            Charge = rho_2phase * self.Geometry.A_CS * L
        else:
            Charge = 0
            
        Results = ValuesClass()
        Results.h_a_dry = h_a_dry            
        Results.UA_dry = UA_dry * f_dry
        Results.eta_a_dry = eta_a_dry
        Results.Tin_a = Tin_a
        Results.A_a = A_a
        Results.Pin_a = Pin_a
        Results.DP_a = Pin_a - Pout_a
        Results.Pout_a = Pout_a
        Results.mdot_da = mdot_da
        Results.mdot_ha = mdot_ha
        Results.Pin_r = Pin_r
        Results.Pout_r = float(Pout_r)
        Results.x_in = x_in
        Results.x_out = x_out
        Results.Tout_r = Tout_r
        Results.Tin_r = Tin_r
        Results.hin_r = hin_r
        Results.hout_r = float(hout_r)
        Results.A_r = A_r
        Results.mdot_r = mdot_r
        Results.Rw = Rw
        Results.h_r = h_r
        Results.hin_a = hin_a
        Results.Q_sensible = Q_sensible
        Results.Tout_a = Tout_a
        Results.f_dry = f_dry
        Results.Q = Q
        Results.hout_a = hout_a
        Results.Win_a = Win_a
        Results.Wout_a = Wout_a
        Results.DP_r = DP_total
        Results.Charge = Charge
        if f_dry != 1.0:
            Results.h_a_wet = h_a_wet
            Results.eta_a_wet = eta_a_wet
            Results.h_a = h_a_dry * f_dry + h_a_wet * (1 - f_dry)
            Results.eta_a = eta_a_dry * f_dry + eta_a_wet * (1 - f_dry)
            Results.UA_wet = UA_wet * (1 - f_dry)
            Results.UA = UA_wet * (1 - f_dry) + UA_dry * f_dry
        else:
            Results.UA = UA_dry
            Results.h_a = h_a_dry
            Results.eta_a = eta_a_dry
        Results.w_phase = w_2phase
        
        if f_dry == 1.0:
            Results.water_condensed = 0.0
        else:
            Results.water_condensed = water_cond #kg/s
        
        return Results

    def solver_1phase_phase(self,Ref_inputs,Air_inputs,w_1phase = 1.0):
        '''The function is used to solve 1phase segment with phase solver'''
        # will solve a 1 phase segment
        AS = self.AS
        Pin_r = Ref_inputs.Pin_r
        hin_r = Ref_inputs.hin_r
        Tin_r = Ref_inputs.Tin_r
        x_in = Ref_inputs.x_in
        L = Ref_inputs.L * w_1phase
        A_r = self.Geometry.inner_circum * L
        mdot_r = self.Thermal.mdot_r / self.Geometry.Nsubcircuits

        Rw = log(self.Geometry.OD/self.Geometry.ID)/(2*pi*self.Thermal.kw*L)
        # calculating inlet and outlet air properties
        hin_a = Air_inputs.hin_a
        hout_a = Air_inputs.hout_a
        Pin_a = Air_inputs.Pin_a
        Pout_a = Air_inputs.Pout_a
        Win_a = Air_inputs.Win_a
        Wout_a = Air_inputs.Wout_a
        
        if self.Accurate:            
            Tin_a = HAPropsSI('T','H',hin_a,'P',Pin_a,'W',Win_a)
            Tout_a = HAPropsSI('T','H',hout_a,'P',Pout_a,'W',Wout_a)
        else:
            Tin_a = pl.GetTDryBulbFromEnthalpyAndHumRatio(hin_a, Win_a) + 273.15
            Tout_a = pl.GetTDryBulbFromEnthalpyAndHumRatio(hout_a, Wout_a) + 273.15
        
        mdot_ha = Air_inputs.mdot_ha * w_1phase
        
        # calculating air thermal heat transfer properties
        h_a_dry, DP_a_dry, eta_a_dry = self.fins_calculate(Pin_a,Pout_a,Tin_a,Tout_a,Win_a,Wout_a,mdot_ha/w_1phase,L/w_1phase,Wet=False,Accurate=self.Accurate)
        h_a_dry *= self.Thermal.h_a_dry_tuning
        cp_da = self.Fins.cp_da
        DP_a_dry *= self.Thermal.DP_a_dry_tuning
        Pout_a = Pin_a + DP_a_dry
        
        L_full_subcircuit = self.Geometry.Ntubes_per_subcircuit * self.Geometry.Ltube
        ratio = self.Geometry.Lsubcircuit / L_full_subcircuit # due to sub HX
        
        # air side total area
        A_a = self.Fins.Ao * L / self.Geometry.Lsubcircuit * ratio
        
        # dry air flow rate
        mdot_da = mdot_ha / (1 + Win_a)
        
        # heater is condenser, cooler is evaporator
        if Tin_a > Tin_r:
            mode = 'cooler'
        else:
            mode = 'heater'
        
        # dew point temperature of inlet air
        if self.Accurate:
            Tdp = HAPropsSI('D','T',Tin_a,'P',Pin_a,'W',Win_a)
        else:
            Tdp = pl.GetTDewPointFromHumRatio(Tin_a-273.15, Win_a, Pin_a) + 273.15
        
        Error_Q = 100
        eps = 1e-5
        Q = 0
        j = 0
        Pout_r = Pin_r
        hout_r = hin_r
        
        while ((j <= 3) or Error_Q > eps) and (j<20):
            # saving old value of Q
            Q_old = Q

            try:
                Pavg = (Pin_r+Pout_r)/2
                havg = (hin_r+hout_r)/2
                if x_in >= 1:
                    AS.update(CP.PQ_INPUTS,Pavg,1.0)
                    if havg < AS.hmass():
                        raise
                if x_in <= 0:
                    AS.update(CP.PQ_INPUTS,Pavg,0.0)
                    if havg > AS.hmass():
                        raise
            except:
                Pavg = Pin_r
                havg = hin_r
                
            AS.update(CP.HmassP_INPUTS,havg,Pavg)
            cp_r = AS.cpmass()

            # refrigerant side heat transfer coefficient
            try:
                self.Correlations.update(AS,self.Geometry,self.Thermal,'1phase',Pavg,havg,mdot_r,A_r,mode)
                h_r = self.Correlations.calculate_h_1phase()
            except:
                if not hasattr(self,"Solver_Error"):
                    self.Solver_Error = "Failed to calculate single-phase HTC in "
                raise
            if x_in >= 1.0:
                h_r *= self.Thermal.h_r_superheat_tuning
            elif x_in <= 0.0:
                h_r *= self.Thermal.h_r_subcooling_tuning
            else:
                raise
            
            # Internal UA between fluid flow and internal surface
            UA_i = h_r * A_r 
            
            # External dry UA between outer surface and free stream
            UA_o_dry = eta_a_dry * h_a_dry * A_a 
            
            # overall heat transfer coefficient        
            UA_dry = 1 / (1 / (UA_i) + 1 / (UA_o_dry) + Rw)

            # Min and max capacitance rates [W/K]
            Cmin = min([cp_r * mdot_r, cp_da * mdot_da])
            Cmax = max([cp_r * mdot_r, cp_da * mdot_da])        
            
            # Capacitance rate ratio [-]
            C_star = Cmin / Cmax
            
            # NTU of refrigerant
            NTU_i = UA_i / (mdot_r * cp_r)
            
            # NTU of air
            NTU_o_dry = UA_o_dry / (mdot_da * cp_da)
            
            # Ntu overall [-]
            NTU_dry = UA_dry / Cmin
            
            #############################
            
            #Crossflow effectiveness (e.g. see Incropera - Fundamentals of Heat and Mass Transfer, 2007, p. 662)
            if (cp_r * mdot_r) < (cp_da * mdot_da):
                epsilon_dry = 1 - exp(-C_star**(-1) * (1 - exp(-C_star * (NTU_dry))))
                #Cross flow, single phase, cmax is airside, which is unmixed
            else:
                epsilon_dry = (1 / C_star) * (1 - exp(-C_star * (1 - exp(-NTU_dry))))
                #Cross flow, single phase, cmax is refrigerant side, which is mixed
            
            # Dry heat transfer [W]
            Q_dry = epsilon_dry * Cmin * (Tin_a - Tin_r)
            
            # Dry-analysis air outlet temp [K]
            Tout_a_dry = Tin_a - Q_dry / (mdot_da * cp_da)
            
            # Dry-analysis outlet temp [K]
            Tout_r_dry = Tin_r + Q_dry / (mdot_r * cp_r)
    
            # Dry-analysis air outlet enthalpy from energy balance [J/kg]
            hout_a = hin_a - Q_dry / mdot_da
            
            #dry analysis surface temperature at refrigerant inlet (at inlet and outlet air points)
            Tw_i_a = Tin_r + UA_dry * (Rw + 1 / UA_i) * (Tin_a - Tin_r)
            Tw_i_b = Tin_r + UA_dry * (Rw + 1 / UA_i) * (Tout_a_dry - Tin_r)
            Tw_i = (Tw_i_a + Tw_i_b) / 2
            
            #dry analysis surface temperature at refrigerant outlet (at inlet and outlet air points)
            Tw_o_a = Tout_r_dry + UA_dry * (Rw + 1 / UA_i) * (Tin_a - Tout_r_dry)
            Tw_o_b = Tout_r_dry + UA_dry * (Rw + 1 / UA_i) * (Tout_a_dry - Tout_r_dry)
            Tw_o = (Tw_o_a + Tw_o_b) / 2
            
            #dry analysis average surface temperature
            Tw = (Tw_i + Tw_o) / 2
            
            # Air outlet humidity ratio [-]
            Wout_a = Win_a
            
            Tout_r = Tout_r_dry
            
            Tout_a = Tout_a_dry
            
            if Tw < Tdp:
                # The coil is wet
                Tout_r = Tin_r
                eps = 1e-5
                i = 1
                b_r = cair_sat(Tin_r) * 1000
                Q_wet = 0
                water_cond = np.finfo(float).eps
                mu_f = 1e-3
                Error_Q = 100
                while ((i <= 3) or Error_Q > eps) and (i<20):
                    
                    # saving old value of Q_wet
                    Q_wet_old = Q_wet
                    
                    # saturated air enthalpy at refrigerant inlet temperature
                    if self.Accurate:
                        h_s_w_i = HAPropsSI('H','T',Tin_r, 'P',Pin_a, 'R', 1.0) #[kJ/kg_da]
                    else:
                        Wsat = pl.GetSatHumRatio(Tin_r-273.15, Pin_a)
                        h_s_w_i = pl.GetMoistAirEnthalpy(Tin_r-273.15, Wsat)
                                    
                    # calculating wet air properties
                    bw_m, h_a_wet, DP_a_wet, eta_a_wet = self.fins_calculate(Pin_a,Pout_a,Tin_a,Tout_a,Win_a,Wout_a,mdot_ha/w_1phase,L/w_1phase,Wet=True,Accurate=self.Accurate,Tw_o = (Tw_o+Tw_i)/2, water_cond = water_cond, mu_f = mu_f)
                    h_a_wet *= self.Thermal.h_a_wet_tuning
                    cp_da = self.Fins.cp_da
                    
                    # Effective humid air mass flow ratio
                    m_star = min([cp_r * mdot_r / b_r, mdot_da])/max([cp_r * mdot_r / b_r, mdot_da])
                    
                    # minimum effective flow rate
                    mdot_min = min([cp_r * mdot_r / b_r, mdot_da])
                    
                    # new NTU_o_wet
                    NTU_o_wet = eta_a_wet * h_a_wet * A_a / (mdot_da * cp_da)
                    
                    # Wet analysis overall NTU
                    if (cp_r * mdot_r > b_r * mdot_da):
                        NTU_wet = NTU_o_dry / (1 + m_star * (NTU_o_wet / NTU_i))
                    else:
                        NTU_wet = NTU_o_dry / (1 + m_star * (NTU_i / NTU_o_wet))
                    
                    # wet analysis UA value
                    UA_wet = NTU_wet * min([cp_r * mdot_r, b_r * mdot_da])
                    
                    # crossflow effectiveness for wet analysis
                    if (cp_r * mdot_r) < (b_r * mdot_da):
                        #Cross flow, single phase, cmax is airside, which is unmixed
                        epsilon_wet = 1 - exp(-m_star**(-1) * (1 - exp(-m_star * (NTU_wet))))
                    else:
                        #Cross flow, single phase, cmax is refrigerant side, which is mixed
                        epsilon_wet = (1 / m_star) * (1 - exp(-m_star * (1 - exp(-NTU_wet))))
                    
                    # wet analysis heat transfer rate
                    Q_wet = epsilon_wet * mdot_min * (hin_a - h_s_w_i)
                    
                    # Air outlet enthalpy
                    hout_a = hin_a - Q_wet / mdot_da
                    
                    # refrigerant outlet temperature
                    Tout_r = Tin_r + Q_wet / (mdot_r * cp_r)
                    
                    # refrigerant outler saturated surface enthalpy
                    if self.Accurate:
                        h_s_w_o = HAPropsSI('H','T',Tout_r, 'P',Pin_a, 'R', 1.0) #[kJ/kg_da]
                    else:
                        Wsat = pl.GetSatHumRatio(Tout_r-273.15, Pin_a)
                        h_s_w_o = pl.GetMoistAirEnthalpy(Tout_r-273.15, Wsat)
                    
                    # Local UA* and b_r
                    b_r = cair_sat((Tin_r + Tout_r) / 2) * 1000
                    UA_star = 1 / (cp_da / (eta_a_wet * h_a_wet * A_a) + b_r * (1 / (h_r * A_r) + Rw))
                    
                    # wet-analysis outer surface tempererature at outlet
                    Tw_o = Tout_r + UA_star / (h_r * A_r) * (hin_a - h_s_w_o)
    
                    # wet-analysis outer surface tempererature at inlet
                    Tw_i = Tin_r + UA_star / (h_r * A_r) * (hin_a - h_s_w_o)
                                    
                    # wet-analysis outer average surface tempererature
                    Tw = (Tw_i + Tw_o) / 2
                    
                    # Error in Q_wet
                    Error_Q = abs((Q_wet - Q_wet_old) / Q_wet)
                    
                    # increasing counter
                    i += 1
                
                # outlet humidity ratio
                if self.Accurate:
                    Wout_a = HAPropsSI('W','H',hout_a,'T',Tout_a,'P',Pout_a)
                else:
                    Wout_a = pl.GetHumRatioFromEnthalpyAndTDryBulb(hout_a,Tout_a-273.15)
                
                # condensed water
                water_cond = (Win_a - Wout_a) * mdot_da #kg/sec
                if water_cond < 0:
                    water_cond = 0
                    
                # wet-analysis saturation enthalpy
                h_s_s_e = hin_a + (hout_a - hin_a) / (1 - exp(-NTU_o_wet))
                
                # surface effective temperature
                if self.Accurate:
                    T_s_e = HAPropsSI('T','H',h_s_s_e,'P',Pin_a,'R',1.0)
                else:
                    T_s_e = brentq(lambda x: pl.GetSatAirEnthalpy(x,Pin_a) - h_s_s_e, -100,200)
                    T_s_e += 273.15
                
                # Air outlet temperature based on effective temperature
                Tout_a = T_s_e + (Tin_a - T_s_e) * exp(-NTU_o_dry)
    
                # sensible heat transfer 
                Q_sensible = mdot_da * cp_da * (Tin_a - Tout_a)
                
                # dry fraction
                f_dry = 0.0
                
                Q = Q_wet
                            
            else:
                # all dry, since refrigerant outlet surface temperature is dry
                f_dry = 1.0
                Q = Q_dry
                Q_sensible = Q
                hout_a = hin_a - Q / mdot_da
                Wout_a = Win_a
            
            # refrigerant pressure drop
            try:
                self.Correlations.update(AS,self.Geometry,self.Thermal,'1phase',Pin_r,hin_r,mdot_r,A_r,mode)
                DP_total = self.Correlations.calculate_dPdz_f_1phase() * (L)
            except:
                if not hasattr(self,"Solver_Error"):
                    self.Solver_Error = "Failed to calculate single-phase pressure drop in "
                raise
            hout_r = hin_r + Q/(mdot_r)        
            
            # calculate bend pressure drop in segment
            # from C.O. Popieil, J. Wojtkowiak, Friction factor in U-type undulated pipe, J. Fluid Eng. 122 (2000) 260–263
            Radius = self.Geometry.Pt / 2
            Length = pi * Radius
            Dh = self.Geometry.Dh
            G_r = mdot_r / self.Geometry.A_CS
            AS.update(CP.HmassP_INPUTS, hin_r, Pin_r)
            rho = AS.rhomass()
            mu = AS.viscosity()
            Re = G_r * Dh / mu
            Dn = Re / (2 * Radius / Dh)
            f_c = 64 / Re * exp(0.021796 +  0.0413356 * pow(log(Dn), 2))
            DP_r_bend = -f_c / 2 / rho * G_r**2 / 2 / Dh * Length
            N_bends = int(L / self.Geometry.Ltube)
            DP_r_bends = DP_r_bend * N_bends
            DP_total += DP_r_bends
            
            if x_in >= 1.0:
                DP_total *= self.Thermal.DP_r_superheat_tuning
            elif x_in <= 0.0:
                DP_total *= self.Thermal.DP_r_subcooling_tuning
            else:
                raise
            Pout_r = Pin_r + DP_total
            if Pout_r <= 0:
                if not hasattr(self,"Solver_Error"):
                    self.Solver_Error = "Pressure drop is very high that negative pressure exists; please check mass flow rate from compressor or circuit length in "
                raise ValueError("Pressure drop is very high, the pressure became negative")
            Error_Q = abs((Q - Q_old) / Q)
            j += 1
            
        AS.update(CP.HmassP_INPUTS,hout_r,Pout_r)
        Tout_r = AS.T()
        AS.update(CP.PQ_INPUTS,Pout_r,0.0)
        h_L = AS.hmass()
        AS.update(CP.PQ_INPUTS,Pout_r,1.0)
        h_V = AS.hmass()
        x_out = (hout_r-h_L)/(h_V-h_L)
        AS.update(CP.HmassP_INPUTS,hin_r,Pin_r)
        rho_1phase = AS.rhomass()
        Charge = rho_1phase * self.Geometry.A_CS * L
        
        # producing results
        Results = ValuesClass()
        Results.h_a_dry = h_a_dry            
        Results.UA_dry = UA_dry * f_dry
        Results.eta_a_dry = eta_a_dry
        Results.Tin_a = Tin_a
        Results.A_a = A_a
        Results.Pin_a = Pin_a
        Results.DP_a = Pin_a - Pout_a
        Results.Pout_a = Pout_a
        Results.mdot_da = mdot_da
        Results.mdot_ha = mdot_ha
        Results.Pin_r = Pin_r
        Results.Pout_r = float(Pout_r)
        Results.x_in = x_in
        Results.x_out = x_out
        Results.Tout_r = Tout_r
        Results.Tin_r = Tin_r
        Results.hin_r = hin_r
        Results.hout_r = float(hout_r)
        Results.A_r = A_r
        Results.mdot_r = mdot_r
        Results.cp_r = cp_r
        Results.Cmin = Cmin
        Results.Rw = Rw
        Results.h_r = h_r
        Results.hin_a = hin_a
        Results.Q_sensible = Q_sensible
        Results.Tout_a = Tout_a
        Results.f_dry = f_dry
        Results.Q = Q
        Results.hout_a = hout_a
        Results.Win_a = Win_a
        Results.Wout_a = Wout_a
        Results.DP_r = DP_total
        Results.Charge = Charge
        if f_dry != 1.0:
            Results.h_a_wet = h_a_wet
            Results.eta_a_wet = eta_a_wet
            Results.h_a = h_a_dry * f_dry + h_a_wet * (1 - f_dry)
            Results.eta_a = eta_a_dry * f_dry + eta_a_wet * (1 - f_dry)
            Results.UA_wet = UA_wet * (1 - f_dry)
            Results.UA = UA_wet * (1 - f_dry) + UA_dry * f_dry
        else:
            Results.UA = UA_dry
            Results.h_a = h_a_dry
            Results.eta_a = eta_a_dry
        Results.w_phase = w_1phase
        if f_dry == 1.0:
            Results.water_condensed = 0.0
        else:
            Results.water_condensed = water_cond #kg/s

        return Results
    
    def mixed_segment_phase(self,Segment,change):
        
        '''
        Used to calculate portion of the segment where the phase exists with phase solver

        Parameters
        ----------
        change : type of phase change

        Returns
        -------
        portion
            float.

        '''
        Ref = ValuesClass()
        Air = ValuesClass()
        Ref.hin_r = Segment.hin_r
        Ref.Pin_r = Segment.Pin_r
        Ref.Tin_r = Segment.Tin_r
        Ref.x_in = Segment.x_in
        Ref.L = Segment.L
        Air.hin_a = Segment.hin_a
        Air.hout_a = Segment.hout_a
        Air.Win_a = Segment.Win_a
        Air.Wout_a = Segment.Wout_a
        Air.Pin_a = Segment.Pin_a
        Air.Pout_a = Segment.Pout_a
        Air.mdot_ha = Segment.mdot_ha
        if change == "Lto2phase":
            def objective(w_1phase):
                Results = self.solver_1phase_phase(Ref,Air,w_1phase) 
                return Results.x_out
            w_1phase = brentq(objective,np.finfo(float).eps,1-np.finfo(float).eps, xtol=1e-6)
            return w_1phase
        
        if change == "Vto2phase":
            def objective(w_1phase):
                Results = self.solver_1phase_phase(Ref,Air,w_1phase)
                return Results.x_out-1
            w_1phase = brentq(objective,np.finfo(float).eps,1-np.finfo(float).eps, xtol=1e-6)
            return w_1phase
        if change == "2phasetoL":
            def objective(w_2phase):
               Results = self.solver_2phase_phase(Ref,Air,w_2phase) 
               return Results.x_out
            w_2phase = brentq(objective,np.finfo(float).eps,1-np.finfo(float).eps, xtol=1e-6)
            return w_2phase
        if change == "2phasetoV":
            def objective(w_2phase):
               Results = self.solver_2phase_phase(Ref,Air,w_2phase)
               return Results.x_out-1
            w_2phase = brentq(objective,np.finfo(float).eps,1-np.finfo(float).eps, xtol=1e-6)
            return w_2phase

    def phase_by_phase_solver(self):        
        mdot_r_phase = self.Thermal.mdot_r / self.Geometry.Nsubcircuits
        hin_r = self.Thermal.hin_r
        Pin_r = self.Thermal.Pin_r
        AS = self.AS
        AS.update(CP.HmassP_INPUTS, hin_r, Pin_r)
        Tin_r = AS.T()
        AS.update(CP.PQ_INPUTS, Pin_r, 0.0)
        hL = AS.hmass()
        AS.update(CP.PQ_INPUTS, Pin_r, 1.0)
        hV = AS.hmass()
        xin_r = (hin_r - hL) / (hV - hL)
        self.Thermal.Tin_r = Tin_r
        finished = False
        phase_segment_1 = ValuesClass()
        phase_segment_1.hin_r = hin_r
        phase_segment_1.Pin_r = Pin_r
        phase_segment_1.Tin_r = Tin_r
        phase_segment_1.x_in = xin_r
        phase_segment_1.mdot_r = mdot_r_phase
        phase_segment_1.mdot_ha = self.Thermal.mdot_ha / self.Geometry.Nsubcircuits
        phase_segment_1.Pin_a = self.Thermal.Pin_a
        phase_segment_1.Pout_a = self.Thermal.Pin_a
        phase_segment_1.Win_a = self.Thermal.Win_a
        phase_segment_1.Wout_a = self.Thermal.Win_a
        if self.Accurate:
            hin_a = HAPropsSI('H','T',self.Thermal.Tin_a,'W',self.Thermal.Win_a,'P',self.Thermal.Pin_a)
        else:
            hin_a = pl.GetMoistAirEnthalpy(self.Thermal.Tin_a-273.15, self.Thermal.Win_a)
        phase_segment_1.hin_a = hin_a
        phase_segment_1.hout_a = hin_a

        phase_segment_1.L = self.Geometry.Lsubcircuit
        phase_segment_1.w_phase = 1.0
        self.phase_segments = []
        w_HX = 0
        i = 0
        while not finished:
            if self.terminate:
                self.Solver_Error = "User Terminated run!"
                raise
            phase_segment_2 = self.solve_phase(phase_segment_1)
            w_phase = phase_segment_2.w_phase
            phase_segment_2.w_phase *= (1 - w_HX)
            w_HX += w_phase * (1 - w_HX)
            self.phase_segments.append(phase_segment_2)
            phase_segment_1.hin_r = phase_segment_2.hout_r
            phase_segment_1.Pin_r = phase_segment_2.Pout_r
            phase_segment_1.Tin_r = phase_segment_2.Tout_r
            phase_segment_1.x_in = phase_segment_2.x_out
            phase_segment_1.mdot_r = mdot_r_phase
            phase_segment_1.mdot_ha = self.Thermal.mdot_ha * (1 - w_HX) / self.Geometry.Nsubcircuits
            phase_segment_1.Pin_a = self.Thermal.Pin_a
            phase_segment_1.Pout_a = self.Thermal.Pin_a
            phase_segment_1.Win_a = self.Thermal.Win_a
            phase_segment_1.Wout_a = self.Thermal.Win_a
            phase_segment_1.hin_a = hin_a
            phase_segment_1.hout_a = hin_a
            phase_segment_1.L = self.Geometry.Lsubcircuit * (1 - w_HX)
            
            if w_HX >= 1.0:
                finished = True
            i += 1
            if i >5:
                raise
        
    def solve_phase(self,phase_segment):
        '''The function is used to solve a phase segment with phase solver'''
        Ref = ValuesClass()
        Air = ValuesClass()
        Ref.hin_r = phase_segment.hin_r
        Ref.Pin_r = phase_segment.Pin_r
        Ref.Tin_r = phase_segment.Tin_r
        Ref.x_in = phase_segment.x_in
        Ref.mdot_r = phase_segment.mdot_r
        Ref.L = phase_segment.L

        Air.hin_a = phase_segment.hin_a
        Air.hout_a = phase_segment.hout_a
        Air.Win_a = phase_segment.Win_a
        Air.Wout_a = phase_segment.Wout_a
        Air.Pin_a = phase_segment.Pin_a
        Air.Pout_a = phase_segment.Pout_a
        Air.mdot_ha = phase_segment.mdot_ha
        if self.Thermal.Tin_a < self.Thermal.Tin_r:
            mode = 'heater'
        else:
            mode = 'cooler'
        # this is a normal segment
        if 0 < Ref.x_in < 1 or (Ref.x_in == 0 and mode == 'cooler') or (Ref.x_in == 1 and mode == 'heater'): # 2phase inlet
            Results = self.solver_2phase_phase(Ref,Air)
            # normally
            Results.phase_change = False
            if not (0 <= Results.x_out <= 1):
                # phase change happened
                if Results.x_out > 1:
                    # it is from 2phase to Vapor
                    
                    # this is to find portion of segment where 2phase exist
                    # and construct the first segment
                    w_2phase = self.mixed_segment_phase(phase_segment,'2phasetoV')
                    phase_change_type = "2phasetoV"
                    
                    Results = self.solver_2phase_phase(Ref,Air,w_2phase)
                    # to avoid small tolerance in x
                    Results.x_out = 1.0
                elif Results.x_out < 0:
                    # it is from 2phase to liquid
                    # this is to find portion of segment where 2phase exist
                    # and construct the first segment
                    w_2phase = self.mixed_segment_phase(phase_segment,'2phasetoL')
                    phase_change_type = "2phasetoL"
                    
                    Results = self.solver_2phase_phase(Ref,Air,w_2phase)
                    # to avoid small tolerance in x
                    Results.x_out = 0.0
                Results.phase_change_type = phase_change_type
                Results.phase_change = True
                Results.w_phase = w_2phase
        elif Ref.x_in < 0 or (Ref.x_in == 0 and mode == 'heater'): #subcooled
            Results = self.solver_1phase_phase(Ref,Air)
            # normally
            Results.phase_change = False
            if not (Results.x_out < 0):
                # phase change happened
                
                # this is to find portion of segment where Liquid exist
                # and construct the first segment
                w_1phase = self.mixed_segment_phase(phase_segment,'Lto2phase')
                Results = self.solver_1phase_phase(Ref,Air,w_1phase)
                # to avoid small tolerance in x
                Results.x_out = 0.0
                Results.phase_change_type = "Lto2phase"
                Results.phase_change = True
                Results.w_phase = w_1phase
        elif Ref.x_in > 1 or (Ref.x_in == 1 and mode == 'cooler'): # superheated
            Results = self.solver_1phase_phase(Ref,Air)
            # normally
            Results.phase_change = False
            if not (Results.x_out > 1):
                # phase change happened
                
                # find porion of segment where vapor exist and contruct
                # a segment with it
                w_1phase = self.mixed_segment_phase(phase_segment,'Vto2phase')
                                    
                Results = self.solver_1phase_phase(Ref,Air,w_1phase)
                # to avoid small tolerance in x
                Results.x_out = 1.0
                Results.phase_change_type = "Vto2phase"
                Results.phase_change = True
                Results.w_phase = w_1phase
        return Results

    def results_creator_phase(self):
        '''The function is used to create the results subclass with phase solver'''
        self.Results = ValuesClass()

        Pout_r = self.phase_segments[-1].Pout_r
        hout_r = self.phase_segments[-1].hout_r
        AS = self.AS
        AS.update(CP.PQ_INPUTS,Pout_r,0.0)
        hL = AS.hmass()
        AS.update(CP.PQ_INPUTS,Pout_r,1.0)
        hV = AS.hmass()
        xout_r = (hout_r - hL) / (hV - hL)

        self.Results.Tin_r = self.phase_segments[0].Tin_r
        self.Results.Tout_r = self.phase_segments[-1].Tout_r
        self.Results.hin_r = self.phase_segments[0].hin_r
        self.Results.hout_r = hout_r
        self.Results.Pin_r = self.phase_segments[0].Pin_r
        self.Results.Pout_r = Pout_r
        self.Results.xin_r = self.phase_segments[0].x_in
        self.Results.xout_r = xout_r
        self.Results.mdot_r = self.Thermal.mdot_r
        
        AS.update(CP.HmassP_INPUTS, self.Results.hin_r, self.Results.Pin_r)
        self.Results.Sin_r = AS.smass()
        AS.update(CP.HmassP_INPUTS, self.Results.hout_r, self.Results.Pout_r)
        self.Results.Sout_r = AS.smass()

        self.Results.Q_superheat = 0
        self.Results.Q_2phase = 0
        self.Results.Q_subcool = 0
        self.Results.w_superheat = 0
        self.Results.w_2phase = 0
        self.Results.w_subcool = 0
        self.Results.water_cond_superheat = 0
        self.Results.water_cond_2phase = 0
        self.Results.water_cond_subcool = 0
        self.Results.Charge_superheat = 0
        self.Results.Charge_2phase = 0
        self.Results.Charge_subcool = 0
        self.Results.DP_r_superheat = 0
        self.Results.DP_r_2phase = 0
        self.Results.DP_r_subcool = 0
        self.Results.UA_superheat = 0
        self.Results.UA_2phase = 0
        self.Results.UA_subcool = 0
        self.Results.Q_sensible = 0
        self.Air_h_a_dry_values = []
        self.Air_eta_a_dry_values = []
        self.Air_UA_dry_values = []
        self.Air_h_a_wet_values = []
        self.Air_eta_a_wet_values = []
        self.Air_UA_wet_values = []
        self.h_r_subcool_values = []
        self.h_r_2phase_values = []
        self.h_r_superheat_values = []
        self.w_phase_subcool_values = []
        self.w_phase_2phase_values = []
        self.w_phase_superheat_values = []
        self.Pout_a_values = []
        self.hout_a_values = []
        self.Wout_a_values = []
        self.h_a_values = []
        self.eta_a_values = []
        
        delta_T_pinch = np.inf
        delta_T_loc = None

        for Segment in self.phase_segments:
            self.Pout_a_values.append(Segment.Pout_a)
            self.hout_a_values.append(Segment.hout_a * Segment.w_phase)
            self.Wout_a_values.append(Segment.Wout_a * Segment.w_phase)
            self.Air_h_a_dry_values.append(Segment.h_a_dry)
            self.Air_eta_a_dry_values.append(Segment.eta_a_dry)
            self.Air_UA_dry_values.append(Segment.UA_dry)
            
            
            delta_T_pinch = min(delta_T_pinch,abs(Segment.Tout_a - Segment.Tout_r))
            delta_T_pinch = min(delta_T_pinch,abs(Segment.Tin_a - Segment.Tin_r))
            if delta_T_pinch == abs(Segment.Tout_a - Segment.Tout_r):
                delta_T_loc = Segment.x_out
            elif delta_T_pinch == abs(Segment.Tin_a - Segment.Tin_r):
                delta_T_loc = Segment.x_in
            
            if Segment.f_dry == 1:
                self.h_a_values.append(Segment.h_a_dry)
                self.eta_a_values.append(Segment.eta_a_dry)
            elif Segment.f_dry == 0:
                self.h_a_values.append(Segment.h_a_wet)
                self.eta_a_values.append(Segment.eta_a_wet)
            else:
                self.h_a_values.append(Segment.h_a)
                self.eta_a_values.append(Segment.eta_a)
            if Segment.f_dry != 1.0:
                self.Air_h_a_wet_values.append(Segment.h_a_wet)
                self.Air_eta_a_wet_values.append(Segment.eta_a_wet)
                self.Air_UA_wet_values.append(Segment.UA_wet)
            if Segment.x_in == 0.0:
                if Segment.x_out > 0.0:
                    self.Results.Tdew_in = Segment.Tin_r
                    self.Results.SC = Segment.Tin_r - self.Results.Tin_r
                    self.Results.DP_r_subcool = Segment.Pin_r - self.Results.Pin_r
                    P_r_0 = Segment.Pin_r
                elif Segment.x_out < 0.0:
                    self.Results.Tdew_out = Segment.Tin_r
                    self.Results.SC = Segment.Tin_r - self.Results.Tout_r
                    self.Results.DP_r_subcool = self.Results.Pout_r - Segment.Pin_r
                    if self.Results.xin_r > 1.0:
                        self.Results.DP_r_2phase = Segment.Pin_r - P_r_1
                    elif self.Results.xin_r <= 1.0:
                        self.Results.DP_r_2phase = Segment.Pin_r - self.Results.Pin_r
                else:
                    raise
            elif Segment.x_in == 1.0:
                if Segment.x_out < 1.0:
                    self.Results.Tdew_in = Segment.Tin_r
                    self.Results.SH = self.Results.Tin_r - Segment.Tin_r
                    self.Results.DP_r_superheat = Segment.Pin_r - self.Results.Pin_r
                    P_r_1 = Segment.Pin_r
                elif Segment.x_out > 1.0:
                    self.Results.Tdew_out = Segment.Tin_r
                    self.Results.SH = self.Results.Tout_r - Segment.Tin_r
                    self.Results.DP_r_superheat = self.Results.Pout_r - Segment.Pin_r
                    if self.Results.xin_r < 0.0:
                        self.Results.DP_r_2phase = Segment.Pin_r - P_r_0
                    elif self.Results.xin_r >= 0.0:
                        self.Results.DP_r_2phase = Segment.Pin_r - self.Results.Pin_r
                else:
                    raise                    
            if (Segment.x_in < 0) or (Segment.x_in == 0 and Segment.x_out < 0):
                self.Results.Q_subcool += Segment.Q
                self.Results.w_subcool += Segment.A_r / (self.Geometry.inner_circum * self.Geometry.Ntubes_per_subcircuit * self.Geometry.Ltube)
                self.Results.water_cond_subcool += Segment.water_condensed
                self.Results.Charge_subcool += Segment.Charge
                self.Results.UA_subcool += Segment.UA
                self.h_r_subcool_values.append(Segment.h_r * Segment.w_phase)
                self.w_phase_subcool_values.append(Segment.w_phase)
            elif (0 < Segment.x_in < 1) or (Segment.x_in == 0 and Segment.x_out > 0) or (Segment.x_in == 1 and Segment.x_out <1):
                self.Results.Q_2phase += Segment.Q
                self.Results.w_2phase += Segment.A_r / (self.Geometry.inner_circum * self.Geometry.Ntubes_per_subcircuit * self.Geometry.Ltube)
                self.Results.water_cond_2phase += Segment.water_condensed
                self.Results.Charge_2phase += Segment.Charge
                self.Results.UA_2phase += Segment.UA
                self.h_r_2phase_values.append(Segment.h_r * Segment.w_phase)
                self.w_phase_2phase_values.append(Segment.w_phase)
            elif (Segment.x_in > 1) or (Segment.x_in == 1 and Segment.x_out > 1):
                self.Results.Q_superheat += Segment.Q
                self.Results.w_superheat += Segment.A_r / (self.Geometry.inner_circum * self.Geometry.Ntubes_per_subcircuit * self.Geometry.Ltube)
                self.Results.water_cond_superheat += Segment.water_condensed
                self.Results.Charge_superheat += Segment.Charge
                self.Results.UA_superheat += Segment.UA
                self.h_r_superheat_values.append(Segment.h_r * Segment.w_phase)
                self.w_phase_superheat_values.append(Segment.w_phase)
            self.Results.Q_sensible += Segment.Q_sensible
        if (self.Results.xin_r > 1.0) and (self.Results.xout_r > 1.0):
            self.Results.DP_r_subcool = 0
            self.Results.DP_r_2phase = 0
            self.Results.DP_r_superheat = self.Results.Pout_r - self.Results.Pin_r
        if (self.Results.xin_r < 0.0) and (self.Results.xout_r < 0.0):
            self.Results.DP_r_subcool = self.Results.Pout_r - self.Results.Pin_r
            self.Results.DP_r_2phase = 0
            self.Results.DP_r_superheat = 0
        if (0 < self.Results.xin_r < 1.0) and (0 < self.Results.xout_r < 1.0):
            self.Results.DP_r_subcool = 0
            self.Results.DP_r_2phase = self.Results.Pout_r - self.Results.Pin_r
            self.Results.DP_r_superheat = 0
        if (self.Results.xin_r > 1.0) and (1 > self.Results.xout_r > 0):
            self.Results.DP_r_2phase = self.Results.Pout_r - (self.Results.Pin_r + self.Results.DP_r_superheat)
        if (self.Results.xin_r < 0.0) and (1 > self.Results.xout_r > 0):
            self.Results.DP_r_2phase = self.Results.Pout_r - (self.Results.Pin_r + self.Results.DP_r_subcool)
        
        if not hasattr(self.Results,'SH'):
            self.Results.SH = None
        if not hasattr(self.Results,'SC'):
            self.Results.SC = None
        if not hasattr(self.Results,'Tdew_in'):
            self.Results.Tdew_in = None
        if not hasattr(self.Results,'Tdew_out'):
            self.Results.Tdew_out = None

        self.Results.delta_T_pinch = delta_T_pinch
        self.Results.delta_T_loc = delta_T_loc

        self.Results.Q = self.Results.Q_superheat + self.Results.Q_2phase + self.Results.Q_subcool
        self.Results.DP_r = self.Results.Pout_r - self.Results.Pin_r
        self.Results.water_cond = self.Results.water_cond_superheat + self.Results.water_cond_2phase + self.Results.water_cond_subcool
        self.Results.Charge = self.Results.Charge_superheat + self.Results.Charge_2phase + self.Results.Charge_subcool
        self.Results.UA = self.Results.UA_superheat + self.Results.UA_2phase + self.Results.UA_subcool
        if self.h_r_subcool_values:
            self.Results.h_r_subcool = sum(self.h_r_subcool_values) / sum(self.w_phase_subcool_values)
        else:
            self.Results.h_r_subcool = 0
        if self.h_r_2phase_values:
            self.Results.h_r_2phase = sum(self.h_r_2phase_values) / sum(self.w_phase_2phase_values)
        else:
            self.Results.h_r_2phase = 0
        if self.h_r_superheat_values:    
            self.Results.h_r_superheat = sum(self.h_r_superheat_values) / sum(self.w_phase_superheat_values)
        else:
            self.Results.h_r_superheat = 0
        if self.Air_UA_dry_values:
            self.Results.UA_dry = sum(self.Air_UA_dry_values)
        else:
            self.Results.UA_dry = 0
        if self.Air_UA_wet_values:
            self.Results.UA_wet = sum(self.Air_UA_wet_values)
        else:
            self.Results.UA_wet = 0

        
        self.Results.SHR = self.Results.Q_sensible/self.Results.Q
        self.Results.Q *= self.Geometry.Nsubcircuits
        self.Results.Q_superheat *= self.Geometry.Nsubcircuits
        self.Results.Q_2phase *= self.Geometry.Nsubcircuits
        self.Results.Q_subcool *= self.Geometry.Nsubcircuits
        self.Results.Q_sensible *= self.Geometry.Nsubcircuits
        self.Results.water_cond *= self.Geometry.Nsubcircuits
        self.Results.water_cond_superheat *= self.Geometry.Nsubcircuits
        self.Results.water_cond_2phase *= self.Geometry.Nsubcircuits
        self.Results.water_cond_subcool *= self.Geometry.Nsubcircuits
        self.Results.Charge *= self.Geometry.Nsubcircuits
        self.Results.Charge_superheat *= self.Geometry.Nsubcircuits
        self.Results.Charge_2phase *= self.Geometry.Nsubcircuits
        self.Results.Charge_subcool *= self.Geometry.Nsubcircuits
        self.Results.UA *= self.Geometry.Nsubcircuits
        self.Results.UA_superheat *= self.Geometry.Nsubcircuits
        self.Results.UA_2phase *= self.Geometry.Nsubcircuits
        self.Results.UA_subcool *= self.Geometry.Nsubcircuits
        self.Results.UA_wet *= self.Geometry.Nsubcircuits
        self.Results.UA_dry *= self.Geometry.Nsubcircuits
        
        # Air results
        self.Results.Tin_a = self.Thermal.Tin_a
        self.Results.Win_a = self.Thermal.Win_a
        self.Results.Pin_a = self.Thermal.Pin_a
        self.Results.mdot_ha = self.Thermal.mdot_ha
        self.Results.mdot_da = self.Thermal.mdot_ha / (1 + self.Thermal.Win_a)
        
        h_out_average = float(np.sum(self.hout_a_values))
        W_out_average = float(np.sum(self.Wout_a_values))
        P_out_average = float(np.average(self.Pout_a_values))

        self.Results.Pout_a = P_out_average
        self.Results.Wout_a = W_out_average
        self.Results.hout_a = h_out_average
        if self.Accurate:    
            self.Results.Tout_a = HAPropsSI('T','H',h_out_average,'P',self.Results.Pout_a,'W',self.Results.Wout_a)
        else:
            self.Results.Tout_a = pl.GetTDryBulbFromEnthalpyAndHumRatio(h_out_average, self.Results.Wout_a) + 273.15
        
        self.Results.DP_a = self.Results.Pout_a - self.Results.Pin_a
        if self.Air_h_a_dry_values:
            self.Results.h_a_dry = sum(self.Air_h_a_dry_values) / len(self.Air_h_a_dry_values)
        else:
            self.Results.h_a_dry = self.Results.h_a_wet
            
        if self.Air_h_a_wet_values:
            self.Results.h_a_wet = sum(self.Air_h_a_wet_values) / len(self.Air_h_a_wet_values)
        else:
            self.Results.h_a_wet = self.Results.h_a_dry

        self.Results.h_a = sum(self.h_a_values) / len(self.h_a_values)

        self.Results.eta_a = sum(self.eta_a_values) / len(self.eta_a_values)

        if self.Air_eta_a_dry_values:
            self.Results.eta_a_dry = sum(self.Air_eta_a_dry_values) / len(self.Air_eta_a_dry_values)
        else:
            self.Results.eta_a_dry = self.Results.eta_a_wet

        if self.Air_eta_a_wet_values:
            self.Results.eta_a_wet = sum(self.Air_eta_a_wet_values) / len(self.Air_eta_a_wet_values)
        else:
            self.Results.eta_a_wet = self.Results.eta_a_dry

        if self.Accurate:
            v_ha_in = HAPropsSI('V','T',self.Thermal.Tin_a,'P',self.Thermal.Pin_a,'W',self.Thermal.Win_a)
            v_ha_out = HAPropsSI('V','T',self.Results.Tout_a,'P',self.Results.Pout_a,'W',self.Results.Wout_a)
        else:
            v_ha_in = pl.GetMoistAirVolume(self.Thermal.Tin_a-273.15, self.Thermal.Win_a, self.Thermal.Pin_a)
            v_ha_out = pl.GetMoistAirVolume(self.Results.Tout_a-273.15, self.Results.Wout_a, self.Results.Pout_a)
        
        if hasattr(self.Thermal,'Vdot_ha'):
            self.Results.Vdot_ha_in = self.Thermal.Vdot_ha
        else:    
            self.Results.Vdot_ha_in = self.Results.mdot_da * v_ha_in
        self.Results.Vdot_ha_out = self.Results.mdot_da * v_ha_out
        
        L_full_subcircuit = self.Geometry.Ntubes_per_subcircuit * self.Geometry.Ltube
        ratio = self.Geometry.Lsubcircuit / L_full_subcircuit # due to sub HX

        self.Results.V_air_average = (self.Results.Vdot_ha_in + self.Results.Vdot_ha_out) / 2 / self.Geometry.A_face

        self.Geometry.A_a = self.Fins.Ao*self.Geometry.Nsubcircuits * ratio
        self.Converged = True

if __name__=='__main__':
    def fun1():
        import time
        Ref = 'R32&R125'
        Backend = 'REFPROP'
        AS = CP.AbstractState(Backend, Ref) # defining abstract state
        if '&' in Ref:
            if Ref == 'R32&R125':
                AS.set_mass_fractions([0.5,0.5])
        HX = FinTubeCircuitClass()
        HX.AS = AS    
        HX.model = 'phase'
        HX.Geometry.Ntubes_per_bank_per_subcircuit = 5       #number of tubes per bank per subcircuit
        HX.Geometry.Nbank = 4                             #number of banks or rows
        HX.Geometry.Nsubcircuits = 1                         #number of circuits
        HX.Geometry.Ltube = 0.5                         #one tube length
        HX.Geometry.Staggering = 'AaA'
        HX.Geometry.OD = 0.0127
        HX.Geometry.ID = 0.0118
        HX.Geometry.Tubes_type ='Smooth'
        # HX.Geometry.Tubes_type ='Microfin'
        # HX.Geometry.t = 0.00065
        # HX.Geometry.beta = 25
        # HX.Geometry.e = 0.0002
        # HX.Geometry.d = 0.00037
        # HX.Geometry.w = 0.000172
        # HX.Geometry.n = 60
        HX.Geometry.Pl = 0.019               #distance between center of tubes in flow direction                                                
        HX.Geometry.Pt = 0.019               #distance between center of tubes orthogonal to flow direction
        HX.Geometry.Connections = [16,17,18,19,20,15,14,13,12,11,6,7,8,9,10,5,4,3,2,1]
        HX.Geometry.FarBendRadius = 0.01
        HX.Geometry.e_D = 0
        HX.Geometry.FPI = 18
        HX.Geometry.FinType = 'Plain'
        HX.Geometry.Fin_t = 0.0001
        HX.Geometry.Fin_Pd = 0.001
        HX.Geometry.Fin_xf = 0.001
        HX.Geometry.Fin_Lp = 0.001
        HX.Geometry.Fin_Lh = 0.001
        HX.Geometry.Fin_Sn = 10
        HX.Geometry.Fin_Sh = 0.0001
        HX.Geometry.Fin_Ss = 0.001
        
        # HX.Thermal.Vdot_ha = 0.15
        HX.Thermal.mdot_ha = 0.2
        # HX.Thermal.Vel_dist = [[0.8 for i in range(20)],
        #                           [0.9 for i in range(20)],
        #                           [1.1 for i in range(20)],
        #                           [0.9 for i in range(20)],
        #                           [0.7 for i in range(20)],]
        
        HX.Thermal.Pin_a = 101325
        HX.Thermal.mdot_r = 0.04
        HX.Thermal.Nsegments = 1
        HX.Thermal.kw = 385
        HX.Thermal.h_r_superheat_tuning = 1.0
        HX.Thermal.h_r_subcooling_tuning = 1.0
        HX.Thermal.h_r_2phase_tuning = 1.0
        HX.Thermal.h_a_dry_tuning = 1.0
        HX.Thermal.h_a_wet_tuning = 1.0
        HX.Thermal.DP_r_superheat_tuning = 1.0
        HX.Thermal.DP_r_subcooling_tuning = 1.0
        HX.Thermal.DP_r_2phase_tuning = 1.0
        HX.Thermal.DP_a_dry_tuning = 1.0
        HX.Thermal.DP_a_wet_tuning = 1.0
        HX.Thermal.k_fin = 210
        HX.Thermal.FinsOnce = True
        HX.Thermal.DP_a_wet_on = False
        HX.Thermal.h_a_wet_on = False
        HX.Accurate = True
    
        # evaporator    
        HX.Thermal.Pin_r = 7 * 101325
        AS.update(CP.PQ_INPUTS,HX.Thermal.Pin_r,0.1)
        h_in = AS.hmass()
        HX.Thermal.hin_r = h_in
        HX.Thermal.Tin_a = 295
        Win_a = HAPropsSI('W','P',HX.Thermal.Pin_a,'T',HX.Thermal.Tin_a,'R',0.4)
        HX.Thermal.Win_a = Win_a
        
        # condenser
        # HX.Thermal.Pin_r = 25 * 101325
        # DT = 5
        # AS.update(CP.PQ_INPUTS,HX.Thermal.Pin_r,1.0)
        # T_sat = AS.T()
        # T_in = T_sat + DT
        # AS.update(CP.PT_INPUTS,HX.Thermal.Pin_r, T_in)
        # HX.Thermal.hin_r = AS.hmass()
        # HX.Thermal.Tin_a = 305
        # Win_a = HAPropsSI('W','P',HX.Thermal.Pin_a,'T',HX.Thermal.Tin_a,'R',0.4)
        # HX.Thermal.Win_a = Win_a
        
        T1 = time.time()
        HX.calculate(Max_Q_error=0.01,Max_num_iter=30, initial_Nsegments=1)
        T2 = time.time()
        print("total time:",T2-T1)
        global A_a
        A_a = 0
        i = 1
        global list_of_segments
        list_of_segments = []
        if hasattr(HX,'Tubes_list'):
            for x,y in HX.Tubes_list[:,[1,2]]:
                x = int(x)
                y = int(y)
                for j,segment in enumerate(HX.Tubes_grid[x][y].Segments):
                    A_a += segment.A_a
                    i += 1
                    list_of_segments.append(segment)
            global states
            states = np.zeros([len(list_of_segments)+1,9])
            w = 0.0
            for i,Segment in enumerate(list_of_segments):
                states[i] = [w, Segment.hin_r, Segment.Pin_r, Segment.x_in, Segment.Tout_a, Segment.Wout_a,Segment.w_phase,Segment.DP_a,Segment.h_r]
                w = states[i,0]+Segment.A_r/(HX.Geometry.inner_circum*HX.Geometry.Ntubes_per_subcircuit*HX.Geometry.Ltube)
                states[-1] = [1.0, list_of_segments[-1].hout_r, list_of_segments[-1].Pout_r, list_of_segments[-1].x_out, -1, -1,0,0,0]
        print('model:',HX.model)
        print('DP_r:',HX.Results.DP_r)
        print('DP_r_subcool:',HX.Results.DP_r_subcool)
        print('DP_r_2phase:',HX.Results.DP_r_2phase)
        print('DP_r_superheat:',HX.Results.DP_r_superheat)
        print('h_r_subcool:',HX.Results.h_r_subcool)
        print('h_r_2phase:',HX.Results.h_r_2phase)
        print('h_r_superheat:',HX.Results.h_r_superheat)
        print('DP_a:',HX.Results.DP_a)
        print('h_a_dry:',HX.Results.h_a_dry)
        print('h_a_wet:',HX.Results.h_a_wet)
        print('Q:',HX.Results.Q)
        print('x_out',HX.Results.xout_r)
        print('Converged:',HX.Converged)
        from copy import deepcopy
        HX1 = deepcopy(HX.Results)
        HX.model='segment'
        T1 = time.time()
        HX.calculate(Max_Q_error=0.01,Max_num_iter=30, initial_Nsegments=1)
        T2 = time.time()
        print("----------------------")
        print("total time:",T2-T1)
        print('model:',HX.model)
        print('DP_r:',HX.Results.DP_r)
        print('DP_r_subcool:',HX.Results.DP_r_subcool)
        print('DP_r_2phase:',HX.Results.DP_r_2phase)
        print('DP_r_superheat:',HX.Results.DP_r_superheat)
        print('h_r_subcool:',HX.Results.h_r_subcool)
        print('h_r_2phase:',HX.Results.h_r_2phase)
        print('h_r_superheat:',HX.Results.h_r_superheat)
        print('DP_a:',HX.Results.DP_a)
        print('h_a_dry:',HX.Results.h_a_dry)
        print('h_a_wet:',HX.Results.h_a_wet)
        print('Q:',HX.Results.Q)
        print('x_out',HX.Results.xout_r)
        print('Converged:',HX.Converged)

    def fun2(): 
        global HX, HX1, geometry
        import time
        Ref = 'R410A'
        Backend = 'HEOS'
        AS = CP.AbstractState(Backend, Ref) # defining abstract state
        HX = FinTubeCircuitClass()
        HX.AS = AS
        HX.model = 'phase'
        HX.Geometry.Ntubes_per_bank_per_subcircuit = 5       #number of tubes per bank per subcircuit
        HX.Geometry.Nsubcircuits = 3                         #number of circuits
        HX.Geometry.Ltube = 2.252                         #one tube length
        HX.Geometry.Staggering = 'inline'
        HX.Geometry.OD = 0.00913
        HX.Geometry.ID = 0.00849
        HX.Geometry.Tubes_type ='Smooth'
        HX.Geometry.Pl = 0.0191               #distance between center of tubes in flow direction                                                
        HX.Geometry.Pt = 0.0254               #distance between center of tubes orthogonal to flow direction

        # HX.Geometry.Nbank = 1                             #number of banks or rows
        # HX.Geometry.Connections = [1,2,3,4,5,6]
        # HX.Geometry.Sub_HX_matrix = [[6  ,0   ,0],
        #                                 [5  ,0   ,0],
        #                                 ]

        HX.Geometry.Nbank = 2                             #number of banks or rows
        HX.Geometry.Connections = [6,7,8,9,10,5,4,3,2,1]
                
        HX.Geometry.FarBendRadius = 0.01
        HX.Geometry.e_D = 0
        HX.Geometry.FPI = 24
        HX.Geometry.FinType = 'Plain'
        HX.Geometry.Fin_t = 0.00011
        HX.Geometry.Fin_Pd = 0.001
        HX.Geometry.Fin_xf = 0.001
        
        HX.Thermal.Vdot_ha = 1.7934
        
        HX.Thermal.Pin_a = 101325
        HX.Thermal.mdot_r = 0.057
        HX.Thermal.Nsegments = 1
        HX.Thermal.kw = 237
        HX.Thermal.h_r_superheat_tuning = 1.0
        HX.Thermal.h_r_subcooling_tuning = 1.0
        HX.Thermal.h_r_2phase_tuning = 1.0
        HX.Thermal.h_a_dry_tuning = 1.0
        HX.Thermal.h_a_wet_tuning = 1.0
        HX.Thermal.DP_r_superheat_tuning = 1.0
        HX.Thermal.DP_r_subcooling_tuning = 1.0
        HX.Thermal.DP_r_2phase_tuning = 1.0
        HX.Thermal.k_fin = 237
        HX.Thermal.FinsOnce = True
        HX.Accurate = True
        HX.Thermal.DP_a_wet_on = False
        HX.Thermal.h_a_wet_on = False
        
        THX_list = np.linspace(40,50,50)
        Q = []
        Q_target = []
        Q_available = []
        Q_LMTD = []
        SH = 45
        THX = 37.78
        AS.update(CP.QT_INPUTS,1.0,THX+273.15)
        HX.Thermal.Pin_r = AS.p()
        AS.update(CP.PT_INPUTS,HX.Thermal.Pin_r,THX+SH+273.15)
        HX.Thermal.hin_r = 487529.6
        HX.Thermal.Tin_a = 308.15
        Win_a = HAPropsSI("W","T",HX.Thermal.Tin_a,"P",HX.Thermal.Pin_a,"R",0.5)
        HX.Thermal.Win_a = Win_a
        import time
        T1 = time.time()
        HX.calculate(Max_Q_error=0.01,Max_num_iter=30, initial_Nsegments=1)
        T2 = time.time()
        print("total time:",T2-T1)
        global A_a
        A_a = 0
        i = 1
        global list_of_segments
        list_of_segments = []
        if hasattr(HX,'Tubes_list'):
            for x,y in HX.Tubes_list[:,[1,2]]:
                x = int(x)
                y = int(y)
                for j,segment in enumerate(HX.Tubes_grid[x][y].Segments):
                    A_a += segment.A_a
                    i += 1
                    list_of_segments.append(segment)
            global states
            states = np.zeros([len(list_of_segments)+1,11])
            w = 0.0
            import pandas as pd
            for i,Segment in enumerate(list_of_segments):
                states[i] = [w, Segment.hin_r, Segment.Pin_r, Segment.Tin_r, Segment.x_in,Segment.Tin_a, Segment.Tout_a, Segment.w_phase,Segment.DP_a,Segment.h_r,Segment.Q]
                w = states[i,0]+Segment.A_r/(HX.Geometry.inner_circum*HX.Geometry.Ntubes_per_subcircuit*HX.Geometry.Ltube)
            states[-1] = [1.0, list_of_segments[-1].hout_r, list_of_segments[-1].Pout_r, list_of_segments[-1].Tout_r, list_of_segments[-1].x_out, -1, -1,0,0,0,0]
            states = pd.DataFrame(states,columns=["w","hin_r","Pin_r","Tin_r","xin_r","Tin_a","Tout_a","w_phase","DP_a","h_r","Q"])
        print('model:',HX.model)
        print('DP_r:',HX.Results.DP_r)
        print('DP_r_subcool:',HX.Results.DP_r_subcool)
        print('DP_r_2phase:',HX.Results.DP_r_2phase)
        print('DP_r_superheat:',HX.Results.DP_r_superheat)
        print('h_r_subcool:',HX.Results.h_r_subcool)
        print('h_r_2phase:',HX.Results.h_r_2phase)
        print('h_r_superheat:',HX.Results.h_r_superheat)
        print('DP_a:',HX.Results.DP_a)
        print('h_a_dry:',HX.Results.h_a_dry)
        print('h_a_wet:',HX.Results.h_a_wet)
        print('Q:',HX.Results.Q)
        print("mdot_da",HX.Results.mdot_da)
        print("Tin_a",HX.Results.Tin_a)
        print("Tout_a",HX.Results.Tout_a)
        hin_a = HAPropsSI("H","P",HX.Thermal.Pin_a,"T",HX.Thermal.Tin_a,"W",HX.Thermal.Win_a)
        print("hin_a",hin_a)
        hout_a = HAPropsSI("H","P",HX.Results.Pout_a,"T",HX.Results.Tout_a,"W",HX.Results.Wout_a)
        print("hout_a",hout_a)
        print("Q_air",HX.Results.mdot_da * (hout_a - hin_a))
        print("x_in",HX.Results.xin_r)
        print('x_out',HX.Results.xout_r)
        print('Converged:',HX.Converged)
    
    fun2()