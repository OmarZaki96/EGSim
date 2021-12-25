from __future__ import division, print_function, absolute_import
from math import log,exp,pi,sqrt
from CoolProp.CoolProp import HAPropsSI, cair_sat
from backend.MicroChannelHEXFins import FinsClass
from backend.MicroChannelHEXCorrelations import CorrelationsClass
from backend.Tools import ValidateFields
import CoolProp as CP
from scipy.optimize import brentq, newton, root
import numpy as np
import psychrolib as pl
from backend.Fan import FanClass

pl.SetUnitSystem(pl.SI)

class ValuesClass():
    pass

class MicroChannelHEXClass():
    def __init__(self,**kwargs):
        self.Geometry = ValuesClass()
        self.Fins = FinsClass()
        self.Fins.calculated_before = False
        self.Thermal = ValuesClass()
        self.Correlations = CorrelationsClass()
        self.Fan = FanClass()
        self.__dict__.update(kwargs)
        self.geometry_calculated = False
        self.terminate = False
        
    def Update(self,**kwargs):
        self.__dict__.update(kwargs)
        
    def OutputList(self):
        if self.model == "phase":
            model = "Phase-by-phase"
        elif self.model == "segment":
            model = "Segment-by-segment"

        output_list = [("Name",'',self.name),
                       ('','',''),
                       ('Heat Exchanger Mode','',model),
                       ('','',''),
                       ('','',''),
                       ('Heat Transfer','W',self.Results.Q),
                       ('Superheat Heat Trasnfer','W',self.Results.Q_superheat),
                       ('Two-phase Heat Trasnfer','W',self.Results.Q_2phase),
                       ('Subcool Heat Trasnfer','W',self.Results.Q_subcool),
                       ('','',''),
                       ('Sensible Heat Transfer','W',self.Results.Q_sensible),
                       ('Latent Heat Transfer','W',self.Results.Q - self.Results.Q_sensible),
                       ('','',''),
                       ('Sensible Heat Ratio','-',self.Results.SHR),
                       ('','',''),
                       ('Condensed Water','kg/s',self.Results.water_cond),
                       ('Superheat Condensed Water','kg/s',self.Results.water_cond_superheat),
                       ('Two-phase Condensed Water','kg/s',self.Results.water_cond_2phase),
                       ('Subcool Condensed Water','kg/s',self.Results.water_cond_subcool),
                       ('','',''),
                       ('Charge','kg',self.Results.Charge),
                       ('Superheat Charge','kg',self.Results.Charge_superheat),
                       ('Two-phase Charge','kg',self.Results.Charge_2phase),
                       ('Subcool Charge','kg',self.Results.Charge_subcool),
                       ('','',''),
                       ('Inner heat transfer area (refrigerant side)','m^2',self.Geometry.A_r),
                       ('Outer heat transfer area (air side)','m^2',self.Geometry.A_a),
                       ('','',''),
                       ('Refrigerant Pressure Drop','Pa',self.Results.DP_r),
                       ('Superheat Refrigerant Pressure Drop','Pa',self.Results.DP_r_superheat),
                       ('Two-phase Refrigerant Pressure Drop','Pa',self.Results.DP_r_2phase),
                       ('Subcool Refrigerant Pressure Drop','Pa',self.Results.DP_r_subcool),
                       ('','',''),
                       ('Superheat area fraction','%',self.Results.w_superheat * 100),
                       ('Two-phase area fraction','%',self.Results.w_2phase * 100),
                       ('Subcool area fraction','%',self.Results.w_subcool * 100),
                       ('','',''),
                       ('Condenser Water','kg/s',self.Results.water_cond),
                       ('Superheat Condenser Water','kg/s',self.Results.water_cond_superheat),
                       ('Two-phase Condenser Water','kg/s',self.Results.water_cond_2phase),
                       ('Subcool Condenser Water','kg/s',self.Results.water_cond_subcool),
                       ('','',''),
                       ('Air Dry HTC','W/m^2.K',self.Results.h_a_dry),
                       ('Air Wet HTC','W/m^2.K',self.Results.h_a_wet),
                       ('Air Overall HTC','W/m^2.K',self.Results.h_a),
                       ('','',''),
                       ('Air Dry Fin Efficiency','%',self.Results.eta_a_dry * 100),
                       ('Air Wet Fin Efficiency','%',self.Results.eta_a_wet * 100),
                       ('Air Overall Fin Efficiency','%',self.Results.eta_a * 100),
                       ('','',''),
                       ('Refrigerant Superheat HTC','W/m^2.K',self.Results.h_r_superheat),
                       ('Refrigerant Two-phase HTC','W/m^2.K',self.Results.h_r_2phase),
                       ('Refrigerant Subcool HTC','W/m^2.K',self.Results.h_r_subcool),
                       ('','',''),
                       ('Refrigerant Inlet Pressure','Pa',self.Results.Pin_r),
                       ('Refrigerant Inlet Temperature','C',self.Results.Tin_r-273.15),
                       ('Refrigerant Inlet Enthalpy','J/kg',self.Results.hin_r),
                       ('Refrigerant Inlet Quality','-',self.Results.xin_r),
                       ('Refrigerant Inlet Entropy','J/kg.K',self.Results.Sin_r),
                       ('','',''),
                       ('Refrigerant Outlet Pressure','Pa',self.Results.Pout_r),
                       ('Refrigerant Outlet Temperature','C',self.Results.Tout_r-273.15),
                       ('Refrigerant Outlet Enthalpy','J/kg',self.Results.hout_r),
                       ('Refrigerant Outlet Quality','-',self.Results.xout_r),
                       ('Refrigerant Outlet Entropy','J/kg.K',self.Results.Sout_r),
                       ('','',''),
                       ('Refrigerant Mass Flowrate','kg/s',self.Results.mdot_r),
                       ('','',''),
                       ('Refrigerant Inlet Dew Temperature','C',"None" if (self.Results.Tdew_in==None) else self.Results.Tdew_in-273.15),
                       ('Refrigerant Outlet Dew Temperature','C',"None" if (self.Results.Tdew_in==None) else self.Results.Tdew_in-273.15),
                       ('','',''),
                       ('Refrigerant Superheat','K',self.Results.SH),
                       ('Refrigerant Subcool','K',self.Results.SC),
                       ('','',''),
                       ('Air Inlet Temperature','C',self.Results.Tin_a-273.15),
                       ('Air Inlet Pressure','Pa',self.Results.Pin_a),
                       ('Air Inlet Humidity Ratio','kg/kg',self.Results.Win_a),
                       ('','',''),
                       ('Air Outlet Temperature','C',self.Results.Tout_a-273.15),
                       ('Air Outlet Pressure','Pa',self.Results.Pout_a),
                       ('Air Outlet Humidity Ratio','kg/kg',self.Results.Wout_a),
                       ('','',''),
                       ('Air Average Face Velocity','m/s',self.Results.V_air_average),
                       ('','',''),
                       ('Air Humid Mass Flowrate','kg/s',self.Results.mdot_ha),
                       ('Air Dry Mass Flowrate','kg/s',self.Results.mdot_da),
                       ('','',''),
                       ('Air Inlet Humid Volume Flowrate','m^3/s',self.Results.Vdot_ha_in),
                       ('Air Outlet Humid Volume Flowrate','m^3/s',self.Results.Vdot_ha_out),
                       ('','',''),
                       ('Air Pressure Drop','Pa',self.Results.DP_a),
                       ('','',''),
                       ('','',''),
                       ('NTU based on air capacity','-',self.Results.NTU_a),
                       ('','',''),
                       ('','',''),
                       ('Entropy Generation','W/K',self.Results.S_gen),
                       ('','',''),
                       ('Terminal Temperature Difference','K',self.Results.TTD),                       
                       ('Pinch Temperature Difference','K',self.Results.delta_T_pinch),
                       ('Pinch Location (refrigerant Quality)','-',self.Results.delta_T_loc),
                       ('','',''),
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
                       ('','',''),
                       ('Converged?','',self.Converged),
                       ]
        return output_list
                
    def check_input(self):
        '''
        A function to check for HEX inputs before calculating.

        Returns
        -------
        None.

        '''
        reqFields=[
               ('T_w',float,0,10000000),
               ('T_h',float,0,10000000),
               ('T_L',float,0,10000000),
               ('T_s',float,0,10000000),
               ('N_port',int,0,100000000),
               ('P_shape',str,None,None),
               ('P_end',str,None,None),
               ('Enhanced',bool,None,None),
               ('Fin_alpha',float,0,100000000),
               ('Fin_t',float,0,100000000),
               ('Fin_L',float,0,100000000),
               ('Fin_Llouv',float,0,100000000),
               ('P_a',float,0,10000000),
               ('FinType',str,None,None),
               ('FPI',float,0,10000000),
               ('e_D',float,0,10000000),
               ('Fin_rows',int,0,10000000),
               ('Header_CS_Type',str,None,None),
               ('Header_dim_a',float,0,10000000),
               ('Header_length',float,0,10000000),
               ]
        optFields=['E_t','E_h','E_n','P_b','Fin_Lp','N_tube_per_bank_per_pass','A_r','inner_circum','A_CS','Aw','tw','Dh','Header_dim_b','N_tube_per_bank','A_a','N_bank','N_circuits','L_circuit', 'A_face']
        ValidateFields(self.Geometry.__dict__,reqFields,optFields)
        reqFields=[
               ('Nsegments',int,0.1,50000),
               ('kw',float,0.00000001,1000000000),
               ('k_fin',float,0,10000000),
               ('Headers_DP_r',float,0,10000000)
               ]
        optFields=['DP_a_dry_tuning','DP_a_wet_tuning','h_a_wet_tuning','h_a_dry_tuning','DP_r_2phase_tuning','DP_r_subcooling_tuning','DP_r_superheat_tuning','h_r_2phase_tuning','h_r_subcooling_tuning','Rw', 'NsegmentsActual','FinsOnce','Tin_r','h_r_superheat_tuning','Vdot_ha','mdot_ha','Vel_dist','xin_r','N_tube_per_bank_per_pass','HTC_1phase_Corr', 'DP_1phase_Corr', 'HTC_2phase_Corr', 'DP_2phase_Corr', 'DP_Accel_Corr','rho_2phase_Corr','Air_dry_Corr','Air_wet_Corr','HTC_superheat_Corr', 'HTC_subcool_Corr', 'DP_superheat_Corr', 'DP_subcool_Corr','h_a_wet_on','DP_a_wet_on']
        ValidateFields(self.Thermal.__dict__,reqFields,optFields)
        
        if hasattr(self.Thermal,'Vel_dist'):
            self.Thermal.Vel_dist = np.array(self.Thermal.Vel_dist)
            assert(self.Thermal.Vel_dist.shape[0] == self.Geometry.N_tube_per_bank)
        elif hasattr(self,'Vdot_ha'):
            pass
        elif hasattr(self.Thermal,'mdot_ha'):
            pass
        else:
            raise AttributeError("You have to define volume flow rate, mass flow rate or velocity distribution")
                
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
                self.Correlations.impose_dry(int(self.Thermal.Air_dry_Corr))
        if hasattr(self.Thermal,'Air_wet_Corr'):
            if self.Thermal.Air_wet_Corr != 0:
                self.Correlations.impose_wet(int(self.Thermal.Air_wet_Corr))

        if self.Geometry.P_a >= self.Geometry.T_h:
            if not hasattr(self,"Solver_Error"):
                self.Solver_Error = "Microchannel port height should be smaller than tube height in geometry in "
            raise

        if self.Geometry.P_shape in ["Rectangle","Triangle"]:
            width = self.Geometry.P_b * self.Geometry.N_port
        else:
            width = self.Geometry.P_a * self.Geometry.N_port
            
        if  width >= self.Geometry.T_w:
            if not hasattr(self,"Solver_Error"):
                self.Solver_Error = "Microchannel total ports width should be smaller than tube width in geometry in "
            raise
    
        if self.Geometry.Header_dim_a < self.Geometry.T_w:
            if not hasattr(self,"Solver_Error"):
                self.Solver_Error = "Microchannel header dimension (a) in geometry can not be less than tube width in "
            raise

        N_tube_per_bank = sum(self.Geometry.N_tube_per_bank_per_pass[0])
        height = self.Geometry.Fin_rows * self.Geometry.T_s + N_tube_per_bank * self.Geometry.T_h
        
        if self.Geometry.Header_length < height:
            if not hasattr(self,"Solver_Error"):
                self.Solver_Error = "Microchannel header height in geometry can not be less total height of tubes including spacings in "
            raise
        
        if self.Geometry.FinType == "Louvered":
            if self.Geometry.Fin_Llouv > self.Geometry.T_s:
                if not hasattr(self,"Solver_Error"):
                    self.Solver_Error = "Louver height (L1) can't be larger than tube spacing in "
                raise
        
        if self.Geometry.FPI >= 0.0254 / self.Geometry.Fin_t / 2.0:
            if not hasattr(self,"Solver_Error"):
                self.Solver_Error = "FPI is too large and not possible in "
            raise
        
    def geometry(self):
        '''
        To calculate main geometry parameters per circuit

        Returns
        -------
        None.
        
        '''
        self.check_input()
        # to use shorter names for variables
        T_h = self.Geometry.T_h
        N_port = self.Geometry.N_port
        
        # get number of banks from length of tube per pass per bank array
        self.Geometry.N_bank = int(len(self.Geometry.N_tube_per_bank_per_pass))
        
        # to make sure all banks has the same total number of tubes
        for row in self.Geometry.N_tube_per_bank_per_pass:
            if not hasattr(self.Geometry,'N_tube_per_bank'):
                self.Geometry.N_tube_per_bank = sum(row)
            assert(sum(row) == self.Geometry.N_tube_per_bank),"Number of tubes per bank is not consistant"
        
        # port major dimension
        P_a = self.Geometry.P_a
        
        # calculate heat transfer parameters per unit length of tube
        if self.Geometry.P_shape == 'Rectangle':
            P_b = self.Geometry.P_b # port minor dimension
            if self.Geometry.Enhanced == False:
                if self.Geometry.P_end == 'Normal': # port is not extended by round sections
                    self.Geometry.inner_circum = 2 * (P_a + P_b) * N_port # inner circumference for heat transfer area
                    self.Geometry.A_CS = P_a * P_b * N_port # cross section area for flow calculations
                    self.Geometry.Aw = 2 * N_port * P_b # wall area for wall thermal resistance
                    self.Geometry.tw = (T_h - P_a) / 2 # wall thickness for wall thermal resistance
                    
                elif self.Geometry.P_end == 'Extended': # port is extended by round sections
                    self.Geometry.inner_circum = (2 * N_port) * P_b + (2 * N_port - 2) * P_a + pi * P_a
                    self.Geometry.A_CS = P_b * P_a * N_port + pi / 4 * P_a * P_a
                    self.Geometry.Aw = 2 * N_port * P_b
                    self.Geometry.tw = (T_h - P_a) / 2
                
                else:
                    raise Exception("Please choose either a normal or extended for port end")

            elif self.Geometry.Enhanced == True: # inner fins for enhancing heat transfer
                E_t = self.Geoemtry.E_t
                E_h = self.Geoemtry.E_h
                E_n = self.Geoemtry.E_n
                if self.Geometry.P_end == 'Normal':
                    self.Geometry.inner_circum = 2 * (P_a + P_b) * N_port + E_n * (2 * E_h + E_t)
                    self.Geometry.A_CS = P_a * P_b * N_port - E_t * E_h * E_n 
                    self.Geometry.Aw = 2 * N_port * P_b
                    self.Geometry.tw = (T_h - P_a) / 2
                    
                elif self.Geometry.P_end == 'Extended':
                    self.Geometry.inner_circum = (2 * N_port) * P_b + (2 * N_port - 2) * P_a + pi * P_a + E_n * (2 * E_h + E_t)
                    self.Geometry.A_CS = P_b * P_a * N_port + pi / 4 * P_a * P_a - E_t * E_h * E_n 
                    self.Geometry.Aw = 2 * N_port * P_b
                    self.Geometry.tw = (T_h - P_a) / 2
                
                else:
                    raise Exception("Please choose either a normal or extended for port end")
            else:
                raise Exception("Please define enhanced tube either true or false")

        elif self.Geometry.P_shape == 'Circle':
            if self.Geometry.Enhanced == False:
                if self.Geometry.P_end == 'Normal':
                    self.Geometry.inner_circum = pi * P_a * N_port
                    self.Geometry.A_CS = pi / 4 * P_a * P_a * N_port
                    self.Geometry.Aw = 2 * N_port * P_a
                    self.Geometry.tw = (T_h - sqrt(2) * P_a / 2) / 2
                    
                elif self.Geometry.P_end == 'Extended':
                    self.Geometry.inner_circum = (4 * N_port - 2) * P_a + pi * P_a
                    self.Geometry.A_CS = P_a * P_a * N_port + pi / 4 * P_a * P_a
                    self.Geometry.Aw = 2 * N_port * P_a
                    self.Geometry.tw = (T_h - sqrt(2) * P_a / 2) / 2
                
                else:
                    raise Exception("Please choose either a normal or extended for port end")

            elif self.Geometry.Enhanced == True:
                E_t = self.Geoemtry.E_t
                E_h = self.Geoemtry.E_h
                E_n = self.Geoemtry.E_n
                if self.Geometry.P_end == 'Normal':
                    self.Geometry.inner_circum = 4 * P_a * N_port + E_n * (2 * E_h + E_t)
                    self.Geometry.A_CS = P_a * P_a * N_port - E_n * E_t * E_h
                    self.Geometry.Aw = 2 * N_port * P_a
                    self.Geometry.tw = (T_h - sqrt(2) * P_a / 2) / 2
                    
                elif self.Geometry.P_end == 'Extended':
                    self.Geometry.inner_circum = (4 * N_port - 2) * P_a + pi * P_a + E_n * (2 * E_h + E_t)
                    self.Geometry.A_CS = P_a * P_a * N_port + pi / 4 * P_a * P_a - E_n * E_t * E_h
                    self.Geometry.Aw = 2 * N_port * P_a
                    self.Geometry.tw = (T_h - sqrt(2) * P_a / 2) / 2

                else:
                    raise Exception("Please choose either a normal or extended for port end")
            else:
                raise Exception("Please define enhanced tube either true or false")

        elif self.Geometry.P_shape == 'Triangle':
            P_b = self.Geometry.P_b
            if self.Geometry.Enhanced == False:
                if self.Geometry.P_end == 'Normal':
                    self.Geometry.inner_circum = (P_b + 2 * sqrt(P_a * P_a + P_b * P_b / 4)) * N_port
                    self.Geometry.A_CS = 0.5 * P_a * P_b * N_port
                    self.Geometry.Aw = N_port * P_b
                    self.Geometry.tw = (T_h - P_a) / 2
                    
                elif self.Geometry.P_end == 'Extended':
                    self.Geometry.inner_circum = (P_b + 2 * sqrt(P_a * P_a + P_b * P_b / 4)) * N_port - 2 * sqrt(P_a * P_a + P_b * P_b / 4) + P_b + pi * P_a
                    self.Geometry.A_CS = 0.5 * P_a * P_b * (N_port + 1) + pi / 4 * P_a * P_a
                    self.Geometry.Aw = N_port * P_b
                    self.Geometry.tw = (T_h - P_a) / 2
                
                else:
                    raise Exception("Please choose either a normal or extended for port end")

            elif self.Geometry.Enhanced == True:
                E_t = self.Geoemtry.E_t
                E_h = self.Geoemtry.E_h
                E_n = self.Geoemtry.E_n
                if self.Geometry.P_end == 'Normal':
                    self.Geometry.inner_circum = (P_b + 2 * sqrt(P_a * P_a + P_b * P_b / 4)) * N_port + E_n * (2 * E_h + E_t)
                    self.Geometry.A_CS = 0.5 * P_a * P_b * N_port - E_t * E_h * E_n
                    self.Geometry.Aw = N_port * P_b
                    self.Geometry.tw = (T_h - P_a) / 2
                    
                elif self.Geometry.P_end == 'Extended':
                    self.Geometry.inner_circum = (P_b + 2 * sqrt(P_a * P_a + P_b * P_b / 4)) * N_port - 2 * sqrt(P_a * P_a + P_b * P_b / 4) + P_b + pi * P_a + E_n * (2 * E_h + E_t)
                    self.Geometry.A_CS = 0.5 * P_a * P_b * (N_port + 1) + pi / 4 * P_a * P_a - E_t * E_h * E_n
                    self.Geometry.Aw = N_port * P_b
                    self.Geometry.tw = (T_h - P_a) / 2
                
                else:
                    raise Exception("Please choose either a normal or extended for port end")
            else:
                raise Exception("Please define enhanced tube either true or false")

        else:
            raise Exception("Please define port shape type either Rectangle,Circle or Triangle")

        
        # assert some conditions
        assert(self.Geometry.tw > 0), 'Port height is larger than tube height'
        
        # calculating hydraulic diameter
        self.Geometry.Dh = 4 * self.Geometry.A_CS / self.Geometry.inner_circum
        
        # total refrigerant side area
        self.Geometry.A_r = self.Geometry.inner_circum * self.Geometry.N_tube_per_bank * self.Geometry.N_bank * self.Geometry.T_L
        
        if self.model == "phase":
            # calculating average number of passes across banks
            total_passes = 0
            for Bank in self.Geometry.N_tube_per_bank_per_pass:
                total_passes += len(Bank)
            N_banks = len(self.Geometry.N_tube_per_bank_per_pass)
            Average_N_passes = total_passes / N_banks
            
            # number of tubes per pass represent a circuit
            self.Geometry.N_circuits = self.Geometry.N_tube_per_bank / Average_N_passes
        
            self.Geometry.L_circuit = self.Geometry.N_tube_per_bank * self.Geometry.N_bank * self.Geometry.T_L / self.Geometry.N_circuits

        height = self.Geometry.Fin_rows * self.Geometry.T_s + self.Geometry.N_tube_per_bank * self.Geometry.T_h

        self.Geometry.A_face = self.Geometry.T_L * height
        
        # calculated geometry once
        self.geometry_calculated = True
        
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
                self.Correlations.impose_dry(int(self.Thermal.Air_dry_Corr))
        if hasattr(self.Thermal,'Air_wet_Corr'):
            if self.Thermal.Air_wet_Corr != 0:
                self.Correlations.impose_wet(int(self.Thermal.Air_wet_Corr))
        
    def mdot_da_array_creator(self,Nsegments):
        # check if velocity districution is defined
        if hasattr(self.Thermal, 'Vel_dist'):
            if self.Accurate:
                v_ha_in = HAPropsSI('V','T',self.Tin_a,'P',self.Pin_a,'W',self.Win_a)
            else:
                v_ha_in = pl.GetMoistAirVolume(self.Tin_a-273.15, self.Win_a, self.Pin_a)
            
            # define mass flow rate grid using passed number of segments
            Air_grid_mdot_da = np.zeros([len(self.Thermal.Vel_dist[:]), Nsegments])
            
            # to conserve mass flow rate in case passed number of segments is different from the defined distribution
            for i, tube_dist in enumerate(self.Thermal.Vel_dist):
                portion = len(tube_dist)/Nsegments
                if (portion - int(portion)) == 0:
                    for j in range(Nsegments):
                        Air_grid_mdot_da[int(i),int(j)] = np.sum(self.Thermal.Vel_dist[int(i),int(j * portion) : int((j + 1) * portion)])
                else:
                    w = 0
                    for j in range(Nsegments):
                        first_part = 1 - (w - int(w))
                        second_part = (portion - first_part) - int((portion - first_part))
                        a = self.Thermal.Vel_dist[int(i),int(w)] * first_part
                        b = sum(self.Thermal.Vel_dist[int(i),int(w)+1 , int(w) + int(portion - first_part - second_part) + 1])
                        c = self.Thermal.Vel_dist[int(i),int(w) + int(portion)] * second_part
                        Air_grid_mdot_da[int(i),int(j)] = a + b + c
                        w += portion
                        
            # multiply by area to get volume flow rate
            Air_grid_mdot_da *= self.Geometry.T_L/Nsegments * self.Geometry.Pt
            # multiply by density to get mass flow rate
            Air_grid_mdot_da *= (1 / v_ha_in)
            # to get humid mass flow rate
            self.Thermal.mdot_ha = np.sum(Air_grid_mdot_da) * (1 + self.Win_a)

        # in case humid volume flow rate is defined
        elif hasattr(self, 'Vdot_ha'):
            if self.Accurate:
                v_ha_in = HAPropsSI('V','T',self.Tin_a,'P',self.Pin_a,'W',self.Win_a)
            else:
                v_ha_in = pl.GetMoistAirVolume(self.Tin_a-273.15, self.Win_a, self.Pin_a)
            
            Air_grid_mdot_da = np.zeros([self.Geometry.N_tube_per_bank, Nsegments])
            Air_grid_mdot_da += self.Vdot_ha / (Nsegments * self.Geometry.N_tube_per_bank)
            Air_grid_mdot_da *= (1 / v_ha_in)
            self.Thermal.mdot_ha = np.sum(Air_grid_mdot_da) * (1 + self.Win_a)

        # in case humid mass flow rate is defined
        elif hasattr(self.Thermal, 'mdot_ha'):
            mdot_da = self.Thermal.mdot_ha / (1 + self.Win_a)
            Air_grid_mdot_da = np.zeros([self.Geometry.N_tube_per_bank, Nsegments])
            Air_grid_mdot_da += mdot_da / (Nsegments * self.Geometry.N_tube_per_bank)

        Air_grid_mdot_da_full = np.zeros(list(Air_grid_mdot_da.shape)+[int(self.Geometry.N_bank)])
        Air_grid_mdot_da_full[:,:,0] = Air_grid_mdot_da.copy()
        for i in range(1, self.Geometry.N_bank):
            Air_grid_mdot_da_full[:,:,i] = Air_grid_mdot_da.copy()
                    
        return Air_grid_mdot_da_full

    def fins_calculate(self,Pin,Pout,Tin,Tout,Win,Wout,mdot_ha,L,Wet,Accurate=True,Tw_o=None,water_cond=None,mu_f=None):
        '''
        Will calculate fins class

        Returns
        -------
        None.

        '''
        try:
            # this will calculate the air side heat transfer only once
            if self.Thermal.FinsOnce == True:
                if self.Fins.calculated_before == False:
                    self.Fins.geometry_calculated_dry = False
                    self.Fins.geometry_calculated_wet = False
                    
                    Fins_geometry = ValuesClass()
                    Fins_geometry.FinType = self.Geometry.FinType
                    Fins_geometry.FPI = self.Geometry.FPI
                    Fins_geometry.Ntubes = self.Geometry.N_tube_per_bank
                    Fins_geometry.Nbank = 1 # as every bank is considered a new HX
                    Fins_geometry.Ltube = self.Geometry.T_L
                    Fins_geometry.Lf = self.Geometry.Fin_L
                    Fins_geometry.Td = self.Geometry.T_w
                    Fins_geometry.Ht = self.Geometry.T_h
                    Fins_geometry.b = self.Geometry.T_s
                    Fins_geometry.t = self.Geometry.Fin_t
                    Fins_geometry.Npg = self.Geometry.Fin_rows
                    Fins_geometry.k_fin = self.Thermal.k_fin
                    
                    if Fins_geometry.FinType == 'Louvered':
                        Fins_geometry.Llouv = self.Geometry.Fin_Llouv
                        Fins_geometry.Lalpha = self.Geometry.Fin_alpha
                        Fins_geometry.lp = self.Geometry.Fin_Lp
                    
                    elif Fins_geometry.FinType == 'Wavy':
                        Fins_geometry.xf = self.Geometry.Fin_xf
                        Fins_geometry.pd = self.Geometry.Fin_pd
                    
                    # calculate air dry heat transfer and pressure drop
                    Tin = self.Tin_a
                    Pin = self.Pin_a
                    Win = self.Win_a
                    if self.model.lower() == "segment":
                        last_tubes_list = self.Tubes_list[self.Tubes_list[:,2] == 2 * self.Geometry.N_bank - 1,1]
                        last_tubes_list = [int(i) for i in last_tubes_list]
                        h_out = self.Air_grid_h[last_tubes_list,2 * self.Geometry.N_bank,:]
                        W_out = self.Air_grid_W[last_tubes_list,2 * self.Geometry.N_bank,:]
                        
                        h_out_weighted = np.sum(h_out * self.Air_grid_mdot_da[:,:,self.Geometry.N_bank - 1])
                        W_out_weighted = np.sum(W_out * self.Air_grid_mdot_da[:,:,self.Geometry.N_bank - 1])
                        
                        h_out_average = float(h_out_weighted / np.sum(self.Air_grid_mdot_da[:,:,0]))
                        W_out_average = float(W_out_weighted / np.sum(self.Air_grid_mdot_da[:,:,0]))
                        P_out_average = float(np.average(self.Air_grid_P[last_tubes_list,2 * self.Geometry.N_bank,:]))
                    
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
                            Pout = self.Pin_a
                            Wout = self.Win_a
                            Tout = self.Tin_a
                    
                    self.Fins.update(Tin,Tout,Win,Wout,Pin,Pout,self.Thermal.mdot_ha,Fins_geometry,False,Accurate)
                    h_a_dry, DP_dry = self.Fins.calculate_dry()
                    DP_dry *= self.Geometry.N_bank # to consider multiple banks
                    
                    # calculate fin dry efficiency
                    eta_o_dry = self.Fins.calculate_eff_dry(self.Thermal.k_fin, h_a_dry)
                    
                    # calculate air wet heat transfer and pressure drop                
                    if Wet:
                        temp = True
                    else:
                        temp = False
                    Wet = True
                    self.Fins.update(Tin,Tout,Win,Wout,Pin,Pout,self.Thermal.mdot_ha,Fins_geometry,True,Accurate,water_cond=water_cond,mu_f=mu_f)
                    h_a_wet, DP_wet = self.Fins.calculate_wet()
                    DP_wet *= self.Geometry.N_bank # to consider multiple banks
                    Wet = temp

                    if not self.Thermal.DP_a_wet_on:
                        DP_wet = DP_dry

                    if not self.Thermal.h_a_wet_on:
                        h_a_wet = h_a_dry

                    # save values
                    self.Fins.Ao *= self.Geometry.N_bank # to consider multiple banks
                    self.Fins.h_a_dry = h_a_dry
                    self.Fins.DP_dry = DP_dry
                    self.Fins.h_a_wet = h_a_wet
                    self.Fins.DP_wet = DP_wet
                    self.Fins.eta_o_dry = eta_o_dry
                    self.Fins.calculated_before = True
                if Wet:
                    # calculate fin wet efficiency which depends on surface temperature
                    bw_m, eta_o_wet = self.Fins.calculate_eff_wet(Tw_o, self.Thermal.k_fin, self.Fins.h_a_wet)
                    return bw_m, self.Fins.h_a_wet, self.Fins.DP_wet, eta_o_wet
                else:
                    return self.Fins.h_a_dry, self.Fins.DP_dry, self.Fins.eta_o_dry
            else: # calculate air side heat transfer for each segment
                if not hasattr(self,'Fins_geometry'):
                    self.Fins_geometry = ValuesClass()
                    self.Fins_geometry.FinType = self.Geometry.FinType
                    self.Fins_geometry.FPI = self.Geometry.FPI
                    self.Fins_geometry.Ntubes = 1
                    self.Fins_geometry.Nbank = 1
                    self.Fins_geometry.Lf = self.Geometry.Fin_L
                    self.Fins_geometry.Td = self.Geometry.T_w
                    self.Fins_geometry.Ht = self.Geometry.T_h
                    self.Fins_geometry.b = self.Geometry.T_s
                    self.Fins_geometry.t = self.Geometry.Fin_t
                    # to consider if the number of fin rows and tubes are different
                    self.Fins_geometry.Npg = 1 + ((self.Geometry.Fin_rows - self.Geometry.N_tube_per_bank) / self.Geometry.N_tube_per_bank)
                    self.Fins_geometry.k_fin = self.Thermal.k_fin
                    if self.Geometry.FinType == 'Louvered':
                        self.Fins_geometry.Llouv = self.Geometry.Fin_Llouv
                        self.Fins_geometry.Lalpha = self.Geometry.Fin_alpha
                        self.Fins_geometry.lp = self.Geometry.Fin_Lp
                    elif self.Geometry.FinType == 'Wavy':
                        self.Fins_geometry.xf = self.Geometry.Fin_xf
                        self.Fins_geometry.pd = self.Geometry.Fin_pd
    
                self.Fins_geometry.Ltube = L # depends on segment length
                if Wet:
                    self.Fins.update(Tin,Tout,Win,Wout,Pin,Pout,mdot_ha,self.Fins_geometry,True,Accurate,water_cond=water_cond,mu_f=mu_f)
                    h_a_wet, DP_wet = self.Fins.calculate_wet()
                    bw_m, eta_o_wet = self.Fins.calculate_eff_wet(Tw_o, self.Thermal.k_fin, h_a_wet)
                    return bw_m, h_a_wet, DP_wet, eta_o_wet

                    if self.Thermal.DP_a_wet_on:
                        h_a_dry, DP_dry = self.Fins.calculate_dry()
                        DP_wet = DP_dry

                    if self.Thermal.h_a_wet_on:
                        h_a_dry, DP_dry = self.Fins.calculate_dry()
                        h_a_wet = h_a_dry

                else:
                    self.Fins.update(Tin,Tout,Win,Wout,Pin,Pout,mdot_ha,self.Fins_geometry,False,Accurate)
                    h_a_dry, DP_dry = self.Fins.calculate_dry()
                    eta_o_dry = self.Fins.calculate_eff_dry(self.Thermal.k_fin, h_a_dry)
                    return h_a_dry, DP_dry, eta_o_dry
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
        This function will calculate the dry pressure drop of the HX fast to
        be solved with the fan as an intial solver

        Returns
        -------
        DP_a_dry : float
            the dry pressure drop of the HX.

        '''
        # save finsonce parameter
        FinsOnce = self.Thermal.FinsOnce
        # force calculating fins agains
        self.Fins.calculated_before = False
        # force finsonce to be true
        self.Thermal.FinsOnce = True
        if self.geometry_calculated == False:
            self.geometry()
        Pin_a = self.Pin_a
        Tin_a = self.Tin_a
        Win_a = self.Win_a
        
        # this will assume that the volume humid flow rate is the parameter defined
        if self.Accurate:
            v_ha_in = HAPropsSI('V','T',self.Tin_a,'P',self.Pin_a,'W',self.Win_a)
        else:
            v_ha_in = pl.GetMoistAirVolume(self.Tin_a-273.15, self.Win_a, self.Pin_a)
        
        mdot_ha = self.Vdot_ha / v_ha_in * (1 + self.Win_a)
        self.Thermal.mdot_ha = mdot_ha
        Ltube = self.Geometry.T_L
        h_a_dry, DP_a_dry, eta_a_dry = self.fins_calculate(Pin_a,Pin_a,Tin_a,Tin_a,Win_a,Win_a,mdot_ha,Ltube,Wet=False,Accurate=True)
        self.Thermal.FinsOnce = FinsOnce # return to original value
        delattr(self.Thermal,'mdot_ha') # to avoid being used in next iteration
        return DP_a_dry
    
    def results_creator(self):
        '''
        This function will create the results for segment solver

        Returns
        -------
        None.

        '''
        self.Results = ValuesClass()
        # from header calculations
        Pout_r = self.Headers[-1].P_r
        hout_r = self.Headers[-1].h_r
        AS = self.AS
        AS.update(CP.HmassP_INPUTS,hout_r,Pout_r)
        Tout_r = AS.T()
        AS.update(CP.PQ_INPUTS,Pout_r,0.0)
        hL = AS.hmass()
        AS.update(CP.PQ_INPUTS,Pout_r,1.0)
        hV = AS.hmass()
        xout_r = (hout_r - hL) / (hV - hL)
        self.Results.Tin_r = self.Headers[0].T_r
        self.Results.Tout_r = Tout_r
        self.Results.hin_r = self.Headers[0].h_r
        self.Results.hout_r = hout_r
        self.Results.Pin_r = self.Headers[0].P_r
        self.Results.Pout_r = Pout_r
        self.Results.xin_r = self.Headers[0].x_r
        self.Results.xout_r = xout_r
        AS.update(CP.HmassP_INPUTS, self.Results.hin_r, self.Results.Pin_r)
        self.Results.Sin_r = AS.smass()
        AS.update(CP.HmassP_INPUTS, self.Results.hout_r, self.Results.Pout_r)
        self.Results.Sout_r = AS.smass()
        self.Results.mdot_r = self.mdot_r
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
                        self.Results.DP_r_subcool = Segment.Pin_r - self.Results.Pin_r
                        P_r_0 = Segment.Pin_r
                    elif Segment.x_out < 0.0:
                        self.Results.Tdew_out = Segment.Tin_r
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
                        self.Results.DP_r_superheat = Segment.Pin_r - self.Results.Pin_r
                        P_r_1 = Segment.Pin_r
                    elif Segment.x_out > 1.0:
                        self.Results.Tdew_out = Segment.Tin_r
                        self.Results.DP_r_superheat = self.Results.Pout_r - Segment.Pin_r
                        if self.Results.xin_r < 0.0:
                            self.Results.DP_r_2phase = Segment.Pin_r - P_r_0
                        elif self.Results.xin_r >= 0.0:
                            self.Results.DP_r_2phase = Segment.Pin_r - self.Results.Pin_r
                    else:
                        raise      
                        
                if (Segment.x_in < 0) or (Segment.x_in == 0 and Segment.x_out < 0):
                    self.Results.Q_subcool += Segment.Q
                    self.Results.w_subcool += Segment.A_r / (self.Geometry.inner_circum * self.Geometry.N_tube_per_bank * self.Geometry.T_L * self.Geometry.N_bank)
                    self.Results.water_cond_subcool += Segment.water_condensed
                    self.Results.Charge_subcool += Segment.Charge
                    self.Results.UA_subcool += Segment.UA
                    self.h_r_subcool_values.append(Segment.h_r * Segment.w_phase)
                    self.w_phase_subcool_values.append(Segment.w_phase)
                elif (0 < Segment.x_in < 1) or (Segment.x_in == 0 and Segment.x_out > 0) or (Segment.x_in == 1 and Segment.x_out < 1):
                    self.Results.Q_2phase += Segment.Q
                    self.Results.w_2phase += Segment.A_r / (self.Geometry.inner_circum * self.Geometry.N_tube_per_bank * self.Geometry.T_L * self.Geometry.N_bank)
                    self.Results.water_cond_2phase += Segment.water_condensed
                    self.Results.Charge_2phase += Segment.Charge
                    self.Results.UA_2phase += Segment.UA
                    self.h_r_2phase_values.append(Segment.h_r * Segment.w_phase)
                    self.w_phase_2phase_values.append(Segment.w_phase)
                elif (Segment.x_in > 1) or (Segment.x_in == 1 and Segment.x_out > 1):
                    self.Results.Q_superheat += Segment.Q
                    self.Results.w_superheat += Segment.A_r / (self.Geometry.inner_circum * self.Geometry.N_tube_per_bank * self.Geometry.T_L * self.Geometry.N_bank)
                    self.Results.water_cond_superheat += Segment.water_condensed
                    self.Results.Charge_superheat += Segment.Charge
                    self.Results.UA_superheat += Segment.UA
                    self.h_r_superheat_values.append(Segment.h_r * Segment.w_phase)
                    self.w_phase_superheat_values.append(Segment.w_phase)
                self.Results.Q_sensible += Segment.Q_sensible
        if (self.Results.xin_r >= 1.0) and (self.Results.xout_r > 1.0):
            self.Results.DP_r_subcool = 0
            self.Results.DP_r_2phase = 0
            self.Results.DP_r_superheat = self.Results.Pout_r - self.Results.Pin_r
        if (self.Results.xin_r <= 0.0) and (self.Results.xout_r < 0.0):
            self.Results.DP_r_subcool = self.Results.Pout_r - self.Results.Pin_r
            self.Results.DP_r_2phase = 0
            self.Results.DP_r_superheat = 0
        if (0 < self.Results.xin_r < 1.0) and (0 <= self.Results.xout_r <= 1.0):
            self.Results.DP_r_subcool = 0
            self.Results.DP_r_2phase = self.Results.Pout_r - self.Results.Pin_r
            self.Results.DP_r_superheat = 0
        if (self.Results.xin_r > 1.0) and (1 > self.Results.xout_r > 0):
            self.Results.DP_r_2phase = self.Results.Pout_r - (self.Results.Pin_r + self.Results.DP_r_superheat)
        if (self.Results.xin_r < 0.0) and (1 > self.Results.xout_r > 0):
            self.Results.DP_r_2phase = self.Results.Pout_r - (self.Results.Pin_r + self.Results.DP_r_subcool)
            
        # dew temperatures
        if self.Results.xin_r <= 0.0:
            if self.Results.xout_r >= 1.0:
                AS.update(CP.PQ_INPUTS, self.Results.Pin_r, 0.0)
                Tdew_in = AS.T()
                AS.update(CP.PQ_INPUTS, self.Results.Pout_r, 1.0)
                Tdew_out = AS.T()
                self.Results.Tdew_in = Tdew_in
                self.Results.SC = Tdew_in - self.Results.Tin_r
                self.Results.Tdew_out = Tdew_out
                self.Results.SH = self.Results.Tout_r - Tdew_out
            elif 0 <= self.Results.xout_r <= 1:
                AS.update(CP.PQ_INPUTS, self.Results.Pin_r, 0.0)
                Tdew_in = AS.T()
                self.Results.SC = Tdew_in - self.Results.Tin_r
                self.Results.Tdew_in = Tdew_in
                self.Results.Tdew_out = None
                self.Results.SH = None
            else:
                self.Results.SC = None
                self.Results.Tdew_in = None
                self.Results.Tdew_out = None
                self.Results.SH = None
        elif 0.0 <= self.Results.xin_r <= 1.0:
            if self.Results.xout_r >= 1.0:
                AS.update(CP.PQ_INPUTS, self.Results.Pout_r, 1.0)
                Tdew_out = AS.T()
                self.Results.Tdew_in = None
                self.Results.SC = None
                self.Results.Tdew_out = Tdew_out
                self.Results.SH = self.Results.Tout_r - Tdew_out
            elif self.Results.xout_r <= 0.0:
                AS.update(CP.PQ_INPUTS, self.Results.Pout_r, 0.0)
                Tdew_out = AS.T()
                self.Results.Tdew_in = None
                self.Results.SC = Tdew_out - self.Results.Tout_r
                self.Results.Tdew_out = Tdew_out
                self.Results.SH = None
            else:
                self.Results.Tdew_in = None
                self.Results.Tdew_out = None
                self.Results.SC = None
                self.Results.SH = None
        elif self.Results.xin_r >= 1.0:
            if self.Results.xout_r >= 1.0:
                self.Results.Tdew_in = None
                self.Results.SC = None
                self.Results.Tdew_out = None
                self.Results.SH = None
            elif self.Results.xout_r <= 0.0:
                AS.update(CP.PQ_INPUTS, self.Results.Pout_r, 0.0)
                Tdew_out = AS.T()
                AS.update(CP.PQ_INPUTS, self.Results.Pin_r, 1.0)
                Tdew_in = AS.T()
                self.Results.Tdew_in = Tdew_in
                self.Results.SC = Tdew_out - self.Results.Tout_r
                self.Results.Tdew_out = Tdew_out
                self.Results.SH = self.Results.Tin_r - Tdew_in
            else:
                AS.update(CP.PQ_INPUTS, self.Results.Pin_r, 1.0)
                Tdew_in = AS.T()
                self.Results.Tdew_in = Tdew_in
                self.Results.Tdew_out = None
                self.Results.SC = None
                self.Results.SH = self.Results.Tin_r - Tdew_in

        Headers_charge = 0
        for header in self.Headers:
            Headers_charge += header.Charge
        self.Results.Charge_headers = Headers_charge
            
        self.Results.Q = self.Results.Q_superheat + self.Results.Q_2phase + self.Results.Q_subcool
        self.Results.DP_r = self.Results.Pout_r - self.Results.Pin_r
        self.Results.water_cond = self.Results.water_cond_superheat + self.Results.water_cond_2phase + self.Results.water_cond_subcool
        self.Results.Charge = self.Results.Charge_superheat + self.Results.Charge_2phase + self.Results.Charge_subcool + Headers_charge
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
        
        # Air results
        self.Results.Tin_a = self.Tin_a
        self.Results.Win_a = self.Win_a
        self.Results.Pin_a = self.Pin_a
        self.Results.mdot_ha = self.Thermal.mdot_ha
        self.Results.mdot_da = self.Thermal.mdot_ha / (1 + self.Win_a)
        
        last_tubes_list = self.Tubes_list[self.Tubes_list[:,2] == 2 * self.Geometry.N_bank - 1,1]
        last_tubes_list = [int(i) for i in last_tubes_list]
        h_out = self.Air_grid_h[last_tubes_list,2 * self.Geometry.N_bank,:]
        W_out = self.Air_grid_W[last_tubes_list,2 * self.Geometry.N_bank,:]
        
        h_out_weighted = np.sum(h_out * self.Air_grid_mdot_da[:,:,self.Geometry.N_bank - 1])
        W_out_weighted = np.sum(W_out * self.Air_grid_mdot_da[:,:,self.Geometry.N_bank - 1])
        
        h_out_average = float(h_out_weighted / np.sum(self.Air_grid_mdot_da[:,:,0]))
        W_out_average = float(W_out_weighted / np.sum(self.Air_grid_mdot_da[:,:,0]))
        P_out_average = float(np.average(self.Air_grid_P[last_tubes_list,2 * self.Geometry.N_bank,:]))

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
            self.Results.h_a_dry = 0
            
        if self.Air_h_a_wet_values:
            self.Results.h_a_wet = sum(self.Air_h_a_wet_values) / len(self.Air_h_a_wet_values)
        else:
            self.Results.h_a_wet = 0

        self.Results.h_a = sum(self.h_a_values) / len(self.h_a_values)
        self.Results.eta_a = sum(self.eta_a_values) / len(self.eta_a_values)

        if self.Air_eta_a_dry_values:
            self.Results.eta_a_dry = sum(self.Air_eta_a_dry_values) / len(self.Air_eta_a_dry_values)
        else:
            self.Results.eta_a_dry = 0

        if self.Air_eta_a_wet_values:
            self.Results.eta_a_wet = sum(self.Air_eta_a_wet_values) / len(self.Air_eta_a_wet_values)
        else:
            self.Results.eta_a_wet = 0

        if self.Accurate:
            v_ha_in = HAPropsSI('V','T',self.Tin_a,'P',self.Pin_a,'W',self.Win_a)
            v_ha_out = HAPropsSI('V','T',self.Results.Tout_a,'P',self.Results.Pout_a,'W',self.Results.Wout_a)
        else:
            v_ha_in = pl.GetMoistAirVolume(self.Tin_a-273.15, self.Win_a, self.Pin_a)
            v_ha_out = pl.GetMoistAirVolume(self.Results.Tout_a-273.15, self.Results.Wout_a, self.Results.Pout_a)
        
        if hasattr(self,'Vdot_ha'):
            self.Results.Vdot_ha_in = self.Vdot_ha
        else:    
            self.Results.Vdot_ha_in = self.Results.mdot_da * v_ha_in
        self.Results.Vdot_ha_out = self.Results.mdot_da * v_ha_out
        if self.Thermal.FinsOnce == True:
            self.Geometry.A_a = self.Fins.Ao
        else:
            self.Geometry.A_a = self.Fins.Ao * self.Thermal.Nsegments * self.Geometry.N_tube_per_bank * self.Geometry.N_bank

        if self.Accurate:
            h_ha_in = HAPropsSI('H','T',self.Results.Tin_a,'P',self.Results.Pin_a,'W',self.Results.Win_a)
            h_ha_out = HAPropsSI('H','T',self.Results.Tout_a,'P',self.Results.Pout_a,'W',self.Results.Wout_a)
        else:
            h_ha_in = pl.GetMoistAirEnthalpy(self.Results.Tin_a-273.15, self.Results.Win_a)
            h_ha_out = pl.GetMoistAirEnthalpy(self.Results.Tout_a-273.15, self.Results.Wout_a)
        
        try:
            c_a = abs((h_ha_in - h_ha_out) / (self.Results.Tin_a - self.Results.Tout_a))
        except: # inlet and outlet air temperatures are the same
            DT = 0.1
            c_a = (HAPropsSI('H','T',self.Results.Tin_a+DT,'P',self.Results.Pin_a,'W',self.Results.Win_a) - h_ha_in) / DT
            
        C_a = self.Results.mdot_da * c_a
        if C_a != 0:
            self.Results.NTU_a = self.Results.UA / C_a
        else: # incase no enthalpy change in air
            self.Results.NTU_a = None

        s_ha_in = HAPropsSI('S','T',self.Results.Tin_a,'P',self.Results.Pin_a,'W',self.Results.Win_a)
        s_ha_out = HAPropsSI('S','T',self.Results.Tout_a,'P',self.Results.Pout_a,'W',self.Results.Wout_a)
        
        delta_s_air = self.Results.mdot_da * (s_ha_out - s_ha_in)

        delta_s_ref = self.Results.mdot_r * (self.Results.Sout_r - self.Results.Sin_r)
        
        self.Results.S_gen = delta_s_air + delta_s_ref

        if self.Results.Tin_r >= self.Results.Tin_a: # Condenser
            if self.Results.Tdew_in != None:
                self.Results.TTD = abs(self.Results.Tout_a - self.Results.Tdew_in)
            else:
                self.Results.TTD = abs(self.Results.Tout_a - self.Results.Tout_r)
                
        elif self.Results.Tin_r < self.Results.Tin_a: # Evaporator
            if self.Results.Tdew_out != None:
                self.Results.TTD = abs(self.Results.Tout_a - self.Results.Tdew_out)
            else:
                self.Results.TTD = abs(self.Results.Tout_a - self.Results.Tout_r)

        self.Results.V_air_average = (self.Results.Vdot_ha_in + self.Results.Vdot_ha_out) / 2 / self.Geometry.A_face

        self.Results.delta_T_pinch = delta_T_pinch
        self.Results.delta_T_loc = delta_T_loc
            
    def results_creator_phase(self):
        '''The function will create a results subclass in case of phase solver'''
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
        AS.update(CP.HmassP_INPUTS, self.Results.hin_r, self.Results.Pin_r)
        self.Results.Sin_r = AS.smass()
        AS.update(CP.HmassP_INPUTS, self.Results.hout_r, self.Results.Pout_r)
        self.Results.Sout_r = AS.smass()
        self.Results.mdot_r = self.mdot_r
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

        L_circuit = self.Geometry.T_L * self.Geometry.N_tube_per_bank * self.Geometry.N_bank / self.Geometry.N_circuits
        w_old = 0
        for Segment in self.phase_segments:
            Segment.w_phase = (1 - w_old) * Segment.w_phase
            w_old += Segment.w_phase
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
                self.Results.w_subcool += Segment.A_r / (self.Geometry.inner_circum * self.Geometry.N_tube_per_bank * self.Geometry.T_L * self.Geometry.N_bank) * self.Geometry.N_circuits
                self.Results.water_cond_subcool += Segment.water_condensed
                self.Results.Charge_subcool += Segment.Charge
                self.Results.UA_subcool += Segment.UA
                self.h_r_subcool_values.append(Segment.h_r * Segment.w_phase)
                self.w_phase_subcool_values.append(Segment.w_phase)
            elif (0 < Segment.x_in < 1) or (Segment.x_in == 0 and Segment.x_out > 0) or (Segment.x_in == 1 and Segment.x_out <1):
                self.Results.Q_2phase += Segment.Q
                self.Results.w_2phase += Segment.A_r / (self.Geometry.inner_circum * self.Geometry.N_tube_per_bank * self.Geometry.T_L * self.Geometry.N_bank) * self.Geometry.N_circuits
                self.Results.water_cond_2phase += Segment.water_condensed
                self.Results.Charge_2phase += Segment.Charge
                self.Results.UA_2phase += Segment.UA
                self.h_r_2phase_values.append(Segment.h_r * Segment.w_phase)
                self.w_phase_2phase_values.append(Segment.w_phase)
            elif (Segment.x_in > 1) or (Segment.x_in == 1 and Segment.x_out > 1):
                self.Results.Q_superheat += Segment.Q
                self.Results.w_superheat += Segment.A_r / (self.Geometry.inner_circum * self.Geometry.N_tube_per_bank * self.Geometry.T_L * self.Geometry.N_bank) * self.Geometry.N_circuits
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

        Headers_charge = self.Headers_charge_phase()
        self.Results.Charge_headers = Headers_charge
        
        self.Results.DP_r_subcool -= self.Thermal.Headers_DP_r * self.Results.w_subcool
        self.Results.DP_r_2phase -= self.Thermal.Headers_DP_r * self.Results.w_2phase
        self.Results.DP_r_superheat -= self.Thermal.Headers_DP_r * self.Results.w_superheat
        self.Results.Pout_r = Pout_r - self.Thermal.Headers_DP_r
                
        self.Results.Q_superheat *=  self.Geometry.N_circuits
        self.Results.Q_2phase *= self.Geometry.N_circuits
        self.Results.Q_subcool *= self.Geometry.N_circuits
        self.Results.Q_sensible *= self.Geometry.N_circuits
        self.Results.water_cond_superheat *= self.Geometry.N_circuits
        self.Results.water_cond_2phase *= self.Geometry.N_circuits
        self.Results.water_cond_subcool *= self.Geometry.N_circuits
        self.Results.Charge_superheat *= self.Geometry.N_circuits
        self.Results.Charge_2phase *= self.Geometry.N_circuits
        self.Results.Charge_subcool *= self.Geometry.N_circuits
        self.Results.UA_superheat *= self.Geometry.N_circuits
        self.Results.UA_2phase *= self.Geometry.N_circuits
        self.Results.UA_subcool *= self.Geometry.N_circuits
        
        self.Results.Q = self.Results.Q_superheat + self.Results.Q_2phase + self.Results.Q_subcool
        self.Results.DP_r = self.Results.Pout_r - self.Results.Pin_r
        self.Results.water_cond = self.Results.water_cond_superheat + self.Results.water_cond_2phase + self.Results.water_cond_subcool
        self.Results.Charge = self.Results.Charge_superheat + self.Results.Charge_2phase + self.Results.Charge_subcool + Headers_charge
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
        
        # Air results
        self.Results.Tin_a = self.Tin_a
        self.Results.Win_a = self.Win_a
        self.Results.Pin_a = self.Pin_a
        self.Results.mdot_ha = self.Thermal.mdot_ha
        self.Results.mdot_da = self.Thermal.mdot_ha / (1 + self.Win_a)

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
            self.Results.h_a_dry = 0
            
        if self.Air_h_a_wet_values:
            self.Results.h_a_wet = sum(self.Air_h_a_wet_values) / len(self.Air_h_a_wet_values)
        else:
            self.Results.h_a_wet = 0

        self.Results.h_a = sum(self.h_a_values) / len(self.h_a_values)
        self.Results.eta_a = sum(self.eta_a_values) / len(self.eta_a_values)

        if self.Air_eta_a_dry_values:
            self.Results.eta_a_dry = sum(self.Air_eta_a_dry_values) / len(self.Air_eta_a_dry_values)
        else:
            self.Results.eta_a_dry = 0

        if self.Air_eta_a_wet_values:
            self.Results.eta_a_wet = sum(self.Air_eta_a_wet_values) / len(self.Air_eta_a_wet_values)
        else:
            self.Results.eta_a_wet = 0

        if self.Accurate:
            v_ha_in = HAPropsSI('V','T',self.Tin_a,'P',self.Pin_a,'W',self.Win_a)
            v_ha_out = HAPropsSI('V','T',self.Results.Tout_a,'P',self.Results.Pout_a,'W',self.Results.Wout_a)
        else:
            v_ha_in = pl.GetMoistAirVolume(self.Tin_a-273.15, self.Win_a, self.Pin_a)
            v_ha_out = pl.GetMoistAirVolume(self.Results.Tout_a-273.15, self.Results.Wout_a, self.Results.Pout_a)
        
        
        if hasattr(self,'Vdot_ha'):
            self.Results.Vdot_ha_in = self.Vdot_ha
        else:
            self.Results.Vdot_ha_in = self.Results.mdot_da * v_ha_in
        self.Results.Vdot_ha_out = self.Results.mdot_da * v_ha_out
        self.Geometry.A_a = self.Fins.Ao
        
        self.Converged = True

        if self.Accurate:
            h_ha_in = HAPropsSI('H','T',self.Results.Tin_a,'P',self.Results.Pin_a,'W',self.Results.Win_a)
            h_ha_out = HAPropsSI('H','T',self.Results.Tout_a,'P',self.Results.Pout_a,'W',self.Results.Wout_a)
        else:
            h_ha_in = pl.GetMoistAirEnthalpy(self.Results.Tin_a-273.15, self.Results.Win_a)
            h_ha_out = pl.GetMoistAirEnthalpy(self.Results.Tout_a-273.15, self.Results.Wout_a)
        
        try:
            c_a = abs((h_ha_in - h_ha_out) / (self.Results.Tin_a - self.Results.Tout_a))
        except: # inlet and outlet air temperatures are the same
            DT = 0.1
            c_a = (HAPropsSI('H','T',self.Results.Tin_a+DT,'P',self.Results.Pin_a,'W',self.Results.Win_a) - h_ha_in) / DT
            
        C_a = self.Results.mdot_da * c_a
        if C_a != 0:
            self.Results.NTU_a = self.Results.UA / C_a
        else: # incase no enthalpy change in air
            self.Results.NTU_a = None

        s_ha_in = HAPropsSI('S','T',self.Results.Tin_a,'P',self.Results.Pin_a,'W',self.Results.Win_a)
        s_ha_out = HAPropsSI('S','T',self.Results.Tout_a,'P',self.Results.Pout_a,'W',self.Results.Wout_a)
        
        delta_s_air = self.Results.mdot_da * (s_ha_out - s_ha_in)

        delta_s_ref = self.Results.mdot_r * (self.Results.Sout_r - self.Results.Sin_r)
        
        self.Results.S_gen = delta_s_air + delta_s_ref

        if self.Results.Tin_r >= self.Results.Tin_a: # Condenser
            if self.Results.Tdew_in != None:
                self.Results.TTD = abs(self.Results.Tout_a - self.Results.Tdew_in)
            else:
                self.Results.TTD = abs(self.Results.Tout_a - self.Results.Tout_r)
                
        elif self.Results.Tin_r < self.Results.Tin_a: # Evaporator
            if self.Results.Tdew_out != None:
                self.Results.TTD = abs(self.Results.Tout_a - self.Results.Tdew_out)
            else:
                self.Results.TTD = abs(self.Results.Tout_a - self.Results.Tout_r)

        self.Results.V_air_average = (self.Results.Vdot_ha_in + self.Results.Vdot_ha_out) / 2 / self.Geometry.A_face

        self.Results.delta_T_pinch = delta_T_pinch
        self.Results.delta_T_loc = delta_T_loc
    
    def solve(self,Max_Q_error = 0.01, Max_num_iter = 20, initial_Nsegments=1):
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
        if self.Fan.model == 'efficiency' or self.Fan.model == 'power':
            # solving HX depending on solver
            self.Fan.DP_fan_add = self.Fan_add_DP
            if self.model == 'segment':
                self.Fins.calculated_before = False
                self.initialize(Max_Q_error,initial_Nsegments)
                self.solve_once(Q_error = Max_Q_error,i_max = Max_num_iter,Nsegments_calc=self.Thermal.Nsegments)
                self.Headers_charge()
                self.results_creator()
            elif self.model == 'phase':
                if self.geometry_calculated == False:
                    self.geometry()
                if not hasattr(self.Thermal,'mdot_ha'):
                    if self.Accurate:
                        v_ha_in = HAPropsSI('V','T',self.Tin_a,'P',self.Pin_a,'W',self.Win_a)
                    else:
                        v_ha_in = pl.GetMoistAirVolume(self.Tin_a-273.15, self.Win_a, self.Pin_a)
                    self.Thermal.mdot_ha = self.Vdot_ha / v_ha_in * (1 + self.Win_a)
                self.Fins.calculated_before = False
                self.Thermal.FinsOnce = True
                self.phase_by_phase_solver()
                self.results_creator_phase()
            
            # solving fan
            if self.Fan.Fan_position == 'before':
                self.Fan.Vdot_a = self.Results.Vdot_ha_in
                self.Fan.DP_a = -self.Results.DP_a
                self.Fan.Calculate()
            elif self.Fan.Fan_position == 'after':
                self.Fan.Vdot_a = self.Results.Vdot_ha_out
                self.Fan.DP_a = -self.Results.DP_a
                self.Fan.Calculate()
                Tin_a = self.Results.Tout_a
                Pin_a = self.Results.Pout_a
                Win_a = self.Results.Wout_a
                if self.Accurate:
                    hin_a = HAPropsSI('H','T',Tin_a,'P',Pin_a,'W',Win_a)
                else:
                    hin_a = pl.GetMoistAirEnthalpy(Tin_a-273.15, Win_a)
                hout_a = hin_a + self.Fan.power / self.Results.mdot_da
                Pout_a = Pin_a + self.Fan.DP_a
                Wout_a = Win_a
                if self.Accurate:
                    Tout_a = HAPropsSI('T','H',hout_a,'P',Pout_a,'W',Wout_a)
                else:
                    Tout_a = pl.GetTDryBulbFromEnthalpyAndHumRatio(hout_a, Wout_a) + 273.15
                self.Fan.Tin_a = Tin_a
                self.Fan.Pin_a = Pin_a
                self.Fan.Win_a = Win_a
                self.Fan.Tout_a = Tout_a
                self.Fan.Pout_a = Pout_a
                self.Fan.Wout_a = Wout_a

            else:
                raise AttributeError("Please choose the fan position to be after or before the HX")
        elif self.Fan.model == 'curve':
            error = 100
            # get initial guess from given volume flow rate value
            Vdot_a_initial = self.Vdot_ha
            self.Fan.DP_fan_add = self.Fan_add_DP
            def objective(Vdot_a):
                Vdot_a = float(Vdot_a)
                self.Fan.Vdot_a = Vdot_a
                self.Fan.Calculate()
                self.Vdot_ha = Vdot_a
                DP_HX = self.DP_a_fast_calculate()
                error = DP_HX + self.Fan.DP_a
                return error
            Vdot_a_initial = root(objective, Vdot_a_initial,method="hybr")['x']
            
            if self.Fan.Fan_position == 'before':
                def objective(Vdot_a):
                    Vdot_a = float(Vdot_a)
                    if hasattr(self.Thermal,'mdot_ha'):
                        delattr(self.Thermal,'mdot_ha')
                    self.Vdot_ha = Vdot_a
                    if self.model == 'segment':
                        self.Fins.calculated_before = False
                        self.initialize(Max_Q_error,initial_Nsegments)
                        self.solve_once(Q_error = Max_Q_error,i_max = Max_num_iter,Nsegments_calc=self.Thermal.Nsegments)
                        self.Headers_charge()
                        self.results_creator()
                    elif self.model == 'phase':
                        if not hasattr(self.Thermal,'mdot_ha'):
                            if self.Accurate:
                                v_ha_in = HAPropsSI('V','T',self.Tin_a,'P',self.Pin_a,'W',self.Win_a)
                            else:
                                v_ha_in = pl.GetMoistAirVolume(self.Tin_a-273.15, self.Win_a, self.Pin_a)
                            self.Thermal.mdot_ha = self.Vdot_ha / v_ha_in * (1 + self.Win_a)
                        self.Fins.calculated_before = False
                        self.Thermal.FinsOnce = True
                        self.phase_by_phase_solver()
                        self.results_creator_phase()
                    self.Fan.Vdot_a = self.Results.Vdot_ha_in
                    self.Fan.Calculate()
                    error = self.Results.DP_a + self.Fan.DP_a
                    if abs(error) < 1:
                        error = 0
                    return error
                
                Vdot_a = newton(objective, Vdot_a_initial)
            elif self.Fan.Fan_position == 'after':
                def objective(Vdot_a):
                    Vdot_a = float(Vdot_a)
                    if hasattr(self.Thermal,'mdot_ha'):
                        delattr(self.Thermal,'mdot_ha')
                    self.Vdot_ha = Vdot_a
                    if self.model == 'segment':
                        self.Fins.calculated_before = False
                        self.initialize(Max_Q_error,initial_Nsegments)
                        self.solve_once(Q_error = Max_Q_error,i_max = Max_num_iter,Nsegments_calc=self.Thermal.Nsegments)
                        self.Headers_charge()
                        self.results_creator()
                    elif self.model == 'phase':
                        if not hasattr(self.Thermal,'mdot_ha'):
                            if self.Accurate:
                                v_ha_in = HAPropsSI('V','T',self.Tin_a,'P',self.Pin_a,'W',self.Win_a)
                            else:
                                v_ha_in = pl.GetMoistAirVolume(self.Tin_a-273.15, self.Win_a, self.Pin_a)
                            self.Thermal.mdot_ha = self.Vdot_ha / v_ha_in * (1 + self.Win_a)
                        self.Fins.calculated_before = False
                        self.Thermal.FinsOnce = True
                        self.phase_by_phase_solver()
                        self.results_creator_phase()
                    self.Fan.Vdot_a = self.Results.Vdot_ha_out
                    self.Fan.Calculate()                    
                    error = self.Results.DP_a + self.Fan.DP_a
                    if abs(error) < 1:
                        error = 0
                    return error
                
                Vdot_a = newton(objective, Vdot_a_initial)
                Tin_a = self.Results.Tout_a
                Pin_a = self.Results.Pout_a
                Win_a = self.Results.Wout_a
                if self.Accurate:
                    hin_a = HAPropsSI('H','T',Tin_a,'P',Pin_a,'W',Win_a)
                else:
                    hin_a = pl.GetMoistAirEnthalpy(Tin_a-273.15, Win_a)
                hout_a = hin_a + self.Fan.power / self.Results.mdot_da
                Pout_a = Pin_a + self.Fan.DP_a
                Wout_a = Win_a
                if self.Accurate:
                    Tout_a = HAPropsSI('T','H',hout_a,'P',Pout_a,'W',Wout_a)
                else:
                    Tout_a = pl.GetTDryBulbFromEnthalpyAndHumRatio(hout_a, Wout_a) + 273.15
                self.Fan.Tin_a = Tin_a
                self.Fan.Pin_a = Pin_a
                self.Fan.Win_a = Win_a
                self.Fan.Tout_a = Tout_a
                self.Fan.Pout_a = Pout_a
                self.Fan.Wout_a = Wout_a
            else:
                raise AttributeError("Please choose the fan position to be after or before the HX")
        else:
            raise AttributeError("Please choose the fan model: efficiency, power or curve model")
            
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
            
    def solve_once(self,Q_error = 0.01,i_max=20,Nsegments_calc=20):
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
        self.Converged = False
        self.Fins.geometry_calculated_dry = False
        self.Fins.geometry_calculated_wet = False
        self.Nsegments_calc = Nsegments_calc
        self.Air_grid_mdot_da = self.mdot_da_array_creator(Nsegments_calc)
        AS = self.AS
        N_tube_per_bank_per_pass = self.Geometry.N_tube_per_bank_per_pass
        N_passes = 0
        for bank in N_tube_per_bank_per_pass:
            N_passes += len(bank)
        self.Headers = [ValuesClass() for _ in range(2 * N_passes)]
        def objective(Air_grid_h):
            self.Fins.calculated_before = False
            self.Air_grid_h = Air_grid_h.copy()
            hin_r = self.hin_r
            Pin_r = self.Pin_r
            AS.update(CP.HmassP_INPUTS,hin_r,Pin_r)
            Tin_r = AS.T()
            self.Thermal.Tin_r = Tin_r
            AS.update(CP.PQ_INPUTS,Pin_r,0.0)
            hL = AS.hmass()
            AS.update(CP.PQ_INPUTS,Pin_r,1.0)
            hV = AS.hmass()
            x_in = (hin_r-hL)/(hV-hL)
            self.Thermal.xin_r = x_in
            hin_r = hin_r
            Pin_r = Pin_r
            Tin_r = Tin_r
            x_in = x_in
            self.Headers[0].P_r = Pin_r
            self.Headers[0].h_r = hin_r
            self.Headers[0].T_r = Tin_r
            self.Headers[0].x_r = x_in
            for i in range(int(self.Geometry.N_bank)):
                self.bank_solver(i)
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
        last_tubes_list = self.Tubes_list[self.Tubes_list[:,2] == 2 * self.Geometry.N_bank - 1,1]
        last_tubes_list = [int(i) for i in last_tubes_list]
        first_tubes_list = self.Tubes_list[self.Tubes_list[:,2] == 1,1]
        first_tubes_list = [int(i) for i in first_tubes_list]
        Air_Energy_in = self.Air_grid_h[first_tubes_list,0,:] * self.Air_grid_mdot_da[:,:,0]
        Air_Energy_out = self.Air_grid_h[last_tubes_list,2 * self.Geometry.N_bank,:] * self.Air_grid_mdot_da[:,:,self.Geometry.N_bank - 1]
        Q_a = np.sum(Air_Energy_out) - np.sum(Air_Energy_in)            
        hin_r = np.average(self.Headers[0].h_r)
        hout_r = np.average(self.Headers[-1].h_r)
        Q_r = self.mdot_r * (hout_r - hin_r)
        return (Q_a + Q_r)/min(abs(Q_r),abs(Q_a))
           
    def Headers_charge(self):
        ''' The function is used to calculate headers charge'''
        try:
            AS = self.AS
            if self.Geometry.Header_CS_Type == 'Circle':
                A_CS = pi / 4 * pow(self.Geometry.Header_dim_a, 2)
                inner_circum = pi * self.Geometry.Header_dim_a
            elif self.Geometry.Header_CS_Type == 'Rectangle':
                A_CS = self.Geometry.Header_dim_a * self.Geometry.Header_dim_b
                inner_circum = 2 * (self.Geometry.Header_dim_a + self.Geometry.Header_dim_b)
                
            Height = self.Geometry.Header_length # total headers height
            
            V_r = A_CS * Height # total headers volume per bank on one side
            
            A_r = inner_circum * Height # unnecessary
            
            # construction a height factor for each header depending on number of 
            # tubes per pass
            factor_list = []
            for bank in self.Geometry.N_tube_per_bank_per_pass:
                for Pass in bank:
                    factor_list.append(Pass / self.Geometry.N_tube_per_bank)
                    factor_list.append(Pass / self.Geometry.N_tube_per_bank)
    
            for i, header in enumerate(self.Headers):
                V_header = V_r * factor_list[i]
                P_r = np.average(header.P_r)
                h_r = np.average(header.h_r)
                AS.update(CP.PQ_INPUTS, P_r, 0.0)
                hL = AS.hmass()
                AS.update(CP.PQ_INPUTS, P_r, 1.0)
                hV = AS.hmass()
                x_r = (h_r - hL) / (hV - hL)
                if 0 < x_r < 1:
                    self.Correlations.update(AS, self.Geometry,self.Thermal, '2phase',P_r,x_r,self.mdot_r,A_r,'heater',q_flux=1.0)
                    rho_2phase = self.Correlations.calculate_rho_2phase()
                    header.Charge = rho_2phase * V_header
                else:
                    AS.update(CP.HmassP_INPUTS, h_r, P_r)
                    rho_1phase = AS.rhomass()
                    header.Charge = rho_1phase * V_header
        except:
            if not hasattr(self,"Solver_Error"):
                self.Solver_Error = "Failed to calculate headers charge in "
            raise
            
        
    def Headers_charge_phase(self):
        '''The function is used to calculate headers charge'''
        try:
            AS = self.AS
            if self.Geometry.Header_CS_Type == 'Circle':
                A_CS = pi / 4 * pow(self.Geometry.Header_dim_a, 2)
                inner_circum = pi * self.Geometry.Header_dim_a
            elif self.Geometry.Header_CS_Type == 'Rectangle':
                A_CS = self.Geometry.Header_dim_a * self.Geometry.Header_dim_b
                inner_circum = 2 * (self.Geometry.Header_dim_a + self.Geometry.Header_dim_b)
            
            Height = self.Geometry.Header_length # total headers height
            
            V_r = A_CS * Height # total headers volume per bank on one side
            
            A_r = inner_circum * Height # unnecessary
            
            # constructing a headers array
            N_passes = 0
            N_tubes = 0
            for bank in self.Geometry.N_tube_per_bank_per_pass:
                N_passes += len(bank)
                N_tubes += sum(bank)
            headers = np.zeros([N_passes * 2, 4]) # each pass has 2 headers

            # constructing an array for the condition on each header
            w_subcool = self.Results.w_subcool
            w_2phase = self.Results.w_2phase
            w_superheat = self.Results.w_superheat
            N_tubes_subcool = int(round(N_tubes * w_subcool,0))
            N_tubes_2phase = int(round(N_tubes * w_2phase,0))
            N_tubes_superheat = int(round(N_tubes * w_superheat,0))
            if self.Results.xin_r < self.Results.xout_r:
                i_subcool = 0
                counter = 0
                for bank in self.Geometry.N_tube_per_bank_per_pass:
                    for Pass in bank:
                        counter += 1
                        if counter > 0:
                            N_tubes_subcool -= Pass
                            if N_tubes_subcool >= 0:
                                i_subcool += 1
                i_2phase = 0
                counter = 0
                for bank in self.Geometry.N_tube_per_bank_per_pass:
                    for Pass in bank:
                        counter += 1
                        if counter > i_subcool:
                            N_tubes_2phase -= Pass
                            if N_tubes_2phase >= 0:
                                i_2phase += 1
                i_superheat = 0
                counter = 0
                for bank in self.Geometry.N_tube_per_bank_per_pass:
                    for Pass in bank:
                        counter += 1
                        if counter > (i_subcool + i_2phase):
                            N_tubes_superheat -= Pass
                            if N_tubes_superheat >= 0:
                                i_superheat += 1
                                
            if self.Results.xin_r > self.Results.xout_r:
                i_superheat = 0
                counter = 0
                for bank in self.Geometry.N_tube_per_bank_per_pass:
                    for Pass in bank:
                        counter += 1
                        if counter > 0:
                            N_tubes_superheat -= Pass
                            if N_tubes_superheat >= 0:
                                i_superheat += 1
                i_2phase = 0
                for bank in self.Geometry.N_tube_per_bank_per_pass:
                    for Pass in bank:
                        counter += 1
                        if counter > i_superheat:
                            N_tubes_2phase -= Pass
                            if N_tubes_2phase >= 0:
                                i_2phase += 1
                i_subcool = 0
                for bank in self.Geometry.N_tube_per_bank_per_pass:
                    for Pass in bank:
                        counter += 1
                        if counter > (i_superheat + i_2phase):
                            N_tubes_subcool -= Pass
                            if N_tubes_subcool >= 0:
                                i_subcool += 1
            if i_subcool + i_2phase + i_superheat < N_passes:
                i_2phase = N_passes - i_superheat - i_subcool
            if i_subcool > 0:
                if self.Results.xin_r < 0:
                    Pin_subcool = self.Results.Pin_r
                    hin_subcool = self.Results.hin_r
                    if self.Results.xout_r >= 0:
                        Tdew_in = self.Results.Tdew_in
                        AS.update(CP.QT_INPUTS, 0.0, Tdew_in)
                        Pout_subcool = AS.p()
                        hout_subcool = AS.hmass()
                    elif self.Results.xout_r <= 0:
                        Pout_subcool = self.Results.Pout_r
                        hout_subcool = self.Results.hout_r
    
                elif self.Results.xout_r <= 0:
                    Tdew_out = self.Results.Tdew_out
                    AS.update(CP.QT_INPUTS, 0.0, Tdew_out)
                    Pin_subcool = AS.p()
                    hin_subcool = AS.hmass()
                    Pout_subcool = self.Results.Pout_r
                    hout_subcool = self.Results.hout_r
                    
                P_array_subcool = np.linspace(min(Pin_subcool,Pout_subcool),max(Pin_subcool,Pout_subcool),i_subcool*2)[::-1]
                if self.Results.xin_r > self.Results.xout_r:
                    h_array_subcool = np.linspace(min(hin_subcool,hout_subcool),max(hin_subcool,hout_subcool),i_subcool*2)[::-1]
                else:
                    h_array_subcool = np.linspace(min(hin_subcool,hout_subcool),max(hin_subcool,hout_subcool),i_subcool*2)
                
                for i,(P,h) in enumerate(zip(P_array_subcool,h_array_subcool)):
                    AS.update(CP.PQ_INPUTS,P,0.0)
                    hL = AS.hmass()
                    AS.update(CP.PQ_INPUTS,P,1.0)
                    hV = AS.hmass()
                    x = (h-hL) / (hV - hL)
                    headers[i] = [P,h,x,0]
            
            if i_2phase > 0:
                if 0.0 <= self.Results.xin_r <= 1.0:
                    Pin_2phase = self.Results.Pin_r
                    hin_2phase = self.Results.hin_r
                    if self.Results.xout_r >= 1.0:
                        Tdew_out = self.Results.Tdew_out
                        AS.update(CP.QT_INPUTS, 1.0, Tdew_out)
                        Pout_2phase = AS.p()
                        hout_2phase = AS.hmass()
                    elif self.Results.xout_r <= 0:
                        Tdew_out = self.Results.Tdew_out
                        AS.update(CP.QT_INPUTS, 0.0, Tdew_out)
                        Pout_2phase = AS.p()
                        hout_2phase = AS.hmass()
                    elif 0.0 <= self.Results.xout_r <= 1.0:
                        Pout_2phase = self.Results.Pout_r
                        hout_2phase = self.Results.hout_r
    
                elif self.Results.xin_r <= 0:
                    Tdew_in = self.Results.Tdew_in
                    AS.update(CP.QT_INPUTS, 0.0, Tdew_in)
                    Pin_2phase = AS.p()
                    hin_2phase = AS.hmass()
                    if self.Results.xout_r >= 1.0:
                        Tdew_out = self.Results.Tdew_out
                        AS.update(CP.QT_INPUTS, 1.0, Tdew_out)
                        Pout_2phase = AS.p()
                        hout_2phase = AS.hmass()
                    elif 0.0 <= self.Results.xout_r <= 1.0:                    
                        Pout_2phase = self.Results.Pout_r
                        hout_2phase = self.Results.hout_r
                elif self.Results.xin_r >= 1.0:
                    Tdew_in = self.Results.Tdew_in
                    AS.update(CP.QT_INPUTS, 1.0, Tdew_in)
                    Pin_2phase = AS.p()
                    hin_2phase = AS.hmass()
                    if self.Results.xout_r <= 0.0:
                        Tdew_out = self.Results.Tdew_out
                        AS.update(CP.QT_INPUTS, 0.0, Tdew_out)
                        Pout_2phase = AS.p()
                        hout_2phase = AS.hmass()
                    elif 0.0 <= self.Results.xout_r <= 1.0:                    
                        Pout_2phase = self.Results.Pout_r
                        hout_2phase = self.Results.hout_r

                P_array_2phase = np.linspace(min(Pin_2phase,Pout_2phase),max(Pin_2phase,Pout_2phase),i_2phase*2)[::-1]

                if self.Results.xin_r > self.Results.xout_r:
                    h_array_2phase = np.linspace(min(hin_2phase,hout_2phase),max(hin_2phase,hout_2phase),i_2phase*2)[::-1]
                else:
                    h_array_2phase = np.linspace(min(hin_2phase,hout_2phase),max(hin_2phase,hout_2phase),i_2phase*2)
                for i,(P,h) in enumerate(zip(P_array_2phase,h_array_2phase)):
                    AS.update(CP.PQ_INPUTS,P,0.0)
                    hL = AS.hmass()
                    AS.update(CP.PQ_INPUTS,P,1.0)
                    hV = AS.hmass()
                    x = (h-hL) / (hV - hL)
                    headers[i+i_subcool * 2] = [P,h,x,0]
    
            if i_superheat > 0:
                if self.Results.xin_r > 1.0:
                    Pin_superheat = self.Results.Pin_r
                    hin_superheat = self.Results.hin_r
                    if self.Results.xout_r <= 1.0:
                        Tdew_in = self.Results.Tdew_in
                        AS.update(CP.QT_INPUTS, 1.0, Tdew_in)
                        Pout_superheat = AS.p()
                        hout_superheat = AS.hmass()
                    elif self.Results.xout_r >= 1.0:
                        Pout_superheat = self.Results.Pout_r
                        hout_superheat = self.Results.hout_r
    
                elif self.Results.xout_r >= 1.0:
                    Tdew_out = self.Results.Tdew_out
                    AS.update(CP.QT_INPUTS, 1.0, Tdew_out)
                    Pin_superheat = AS.p()
                    hin_superheat = AS.hmass()
                    Pout_superheat = self.Results.Pout_r
                    hout_superheat = self.Results.hout_r
                
                P_array_superheat = np.linspace(min(Pin_superheat,Pout_superheat),max(Pin_superheat,Pout_superheat),i_superheat*2)[::-1]
                if self.Results.xin_r > self.Results.xout_r:
                    h_array_superheat = np.linspace(min(hin_superheat,hout_superheat),max(hin_superheat,hout_superheat),i_superheat*2)
                else:
                    h_array_superheat = np.linspace(min(hin_superheat,hout_superheat),max(hin_superheat,hout_superheat),i_superheat*2)
                
                for i,(P,h) in enumerate(zip(P_array_superheat,h_array_superheat)):
                    AS.update(CP.PQ_INPUTS,P,0.0)
                    hL = AS.hmass()
                    AS.update(CP.PQ_INPUTS,P,1.0)
                    hV = AS.hmass()
                    x = (h-hL) / (hV - hL)
                    headers[i + 2 * i_subcool + 2 * i_2phase] = [P,h,x,0]
            # construction a height factor for each header depending on number of 
            # tubes per pass
            factor_list = []
            for bank in self.Geometry.N_tube_per_bank_per_pass:
                for Pass in bank:
                    factor_list.append(Pass / self.Geometry.N_tube_per_bank)
                    factor_list.append(Pass / self.Geometry.N_tube_per_bank)

            for i, header in enumerate(headers):
                V_header = V_r * factor_list[i]
                P_r = header[0]
                h_r = header[1]
                x_r = header[2]
                if 0 < x_r < 1:
                    self.Correlations.update(AS, self.Geometry,self.Thermal, '2phase',P_r,x_r,self.mdot_r,A_r,'heater',q_flux=1.0)
                    rho_2phase = self.Correlations.calculate_rho_2phase()
                    header[3] = rho_2phase * V_header
                else:
                    AS.update(CP.HmassP_INPUTS, h_r, P_r)
                    rho_1phase = AS.rhomass()
                    header[3] = rho_1phase * V_header
            return sum(headers[:,3])
        except:
            import traceback
            print(traceback.format_exc())
            if not hasattr(self,"Solver_Error"):
                self.Solver_Error = "Failed to calculate headers charge in "
            raise
    
    def Tube_grid_creator(self):
        '''
        The function will create a grid containing tubes at the correct 
        locations.

        Returns
        -------
        None.

        '''
        self.Tubes_grid = [[0 for y in range(int(self.Geometry.N_bank*2+1))] for x in range(int(self.Geometry.N_tube_per_bank))]
        num = 1
        tubes_list = np.zeros([self.Geometry.N_tube_per_bank * self.Geometry.N_bank,3])
        for j in range(self.Geometry.N_bank):
            if j%2==0:
                range_of_tubes = range(int(self.Geometry.N_tube_per_bank))
            else:
                range_of_tubes = list(reversed(range(int(self.Geometry.N_tube_per_bank))))
            y = int(2*j+1)
            for i in range_of_tubes:
                x = int(i)
                self.Tubes_grid[x][y] = ValuesClass()
                self.Tubes_grid[x][y].num = num
                tubes_list[num-1] = [num,x,y]
                num += 1
        orient = np.zeros(len(tubes_list))
        flip = 1
        N_tube_per_bank_per_pass = self.Geometry.N_tube_per_bank_per_pass
        counter = 0
        for row in N_tube_per_bank_per_pass:
            for Pass in row:
                orient[counter:int(counter+Pass)] = flip
                flip *=-1
                for k in range(counter,int(counter+Pass)):
                    x,y = tubes_list[k,[1,2]]
                    x = int(x)
                    y = int(y)
                    self.Tubes_grid[x][y].mdot_r = self.mdot_r / Pass
                counter += Pass
        orient = list(orient)
        b = np.zeros((len(tubes_list),4))
        b[:,:3] = tubes_list
        b[:,3] = orient
        self.Tubes_list = b
        
    def Air_grid_creator(self,Nsegments):
        ''' This function will only create the structure of the air grid'''
        Air_grid_h = np.array([[[0.0 for z in range(int(Nsegments))] for y in range(int(self.Geometry.N_bank*2+1))] for x in range(int(self.Geometry.N_tube_per_bank))])
        Air_grid_P = np.array([[[0.0 for z in range(int(Nsegments))] for y in range(int(self.Geometry.N_bank*2+1))] for x in range(int(self.Geometry.N_tube_per_bank))])
        Air_grid_W = np.array([[[0.0 for z in range(int(Nsegments))] for y in range(int(self.Geometry.N_bank*2+1))] for x in range(int(self.Geometry.N_tube_per_bank))])
        return Air_grid_h,Air_grid_W,Air_grid_P
    
    def Air_grid_initializer(self,Q_error_init,Nsegments):
        ''' This function will assume initial values for air grid'''
        Win_a = self.Win_a
        Pin_a = self.Pin_a

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
        self.solve_once(Q_error=Q_error_init,Nsegments_calc=Nsegments,i_max=40)

    def Air_grid_h_initializer(self,Nsegments):
        mdot_ha = self.Thermal.mdot_ha
        FinsOnce = self.Thermal.FinsOnce
        Pin_a = self.Pin_a
        Pout_a = Pin_a
        Win_a = self.Win_a
        Wout_a = Win_a
        Tin_a = self.Tin_a
        Tout_a = Tin_a
        L = 123 # dummy and won't be used anyway
        self.Thermal.FinsOnce = True
        h_a_dry, DP_a_dry, eta_a_dry = self.fins_calculate(Pin_a,Pout_a,Tin_a,Tout_a,Win_a,Wout_a,mdot_ha,L,Wet=False,Accurate=self.Accurate)
        h_a_dry *= self.Thermal.h_a_dry_tuning
        cp_da = self.Fins.cp_da
        self.Thermal.FinsOnce = FinsOnce
        
        h_air = h_a_dry
        eta_air = eta_a_dry
        A_a = self.Fins.Ao
        mdot_da = self.Thermal.mdot_ha / (1 + Win_a)
        
        self.AS.update(CP.PQ_INPUTS, self.Pin_r, 1.0)
        hV = self.AS.hmass()
        TV = self.AS.T()
        self.AS.update(CP.PQ_INPUTS, self.Pin_r, 0.0)
        hL = self.AS.hmass()
        TL = self.AS.T()
        self.AS.update(CP.HmassP_INPUTS, self.hin_r,self.Pin_r)
        T_r = self.AS.T()
        
        xin_r = (self.hin_r - hL) / (hV - hL)
        
        if xin_r > 1.0:    
            Tin_r = TV
        elif xin_r < 0.0:
            Tin_r = TL
        else:
            Tin_r = T_r
        
        R_air_tot = 1 / (h_air * A_a * eta_air)
        self.geometry()
        L = self.Geometry.T_L * self.Geometry.N_tube_per_bank * self.Geometry.N_bank
        R_wall_tot = self.Geometry.tw / (self.Geometry.Aw * L * self.Thermal.kw)
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
        x = np.linspace(0,1,int(self.Geometry.N_bank + 1))
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

    def bank_solver(self,bank_num):
        '''This function will solve a bank using the given bank number'''
        N_tube_per_bank_per_pass = self.Geometry.N_tube_per_bank_per_pass
        N_passes = 0
        for bank in N_tube_per_bank_per_pass:
            N_passes += len(bank)
        factor_list = []
        for bank in self.Geometry.N_tube_per_bank_per_pass:
            for Pass in bank:
                factor_list.append(Pass / self.Geometry.N_tube_per_bank * self.Geometry.N_bank)
                factor_list.append(Pass / self.Geometry.N_tube_per_bank * self.Geometry.N_bank)
        Header_DP_r_total = self.Thermal.Headers_DP_r
        
        if bank_num == 0:
            Header_DP_r = Header_DP_r_total * factor_list[0]
            self.Headers[0].P_r = self.Headers[0].P_r - Header_DP_r
            N_Headers_before = 0
        
        if not (bank_num == 0):
            N_Headers_before = 0
            for i in range(bank_num):
                N_Headers_before += len(self.Geometry.N_tube_per_bank_per_pass[i]) * 2
            Header_DP_r = Header_DP_r_total * factor_list[N_Headers_before]
            self.Headers[N_Headers_before].P_r = self.Headers[N_Headers_before - 1].P_r - Header_DP_r
            self.Headers[N_Headers_before].h_r = self.Headers[N_Headers_before - 1].h_r
            self.Headers[N_Headers_before].T_r = self.Headers[N_Headers_before - 1].T_r
            self.Headers[N_Headers_before].x_r = self.Headers[N_Headers_before - 1].x_r
        
        N_tube_per_bank_per_pass = self.Geometry.N_tube_per_bank_per_pass[bank_num]
        groups_start = []
        groups_end = []
        for N_tube_per_bank_per_pass_element in N_tube_per_bank_per_pass:
            if not groups_end:
                groups_start.append(bank_num * self.Geometry.N_tube_per_bank)
            else:
                groups_start.append(groups_end[-1])
            groups_end.append(N_tube_per_bank_per_pass_element + groups_start[-1])
        N_passes_in_bank = len(N_tube_per_bank_per_pass)
        for i in range(int(N_passes_in_bank)):
            Header_DP_r = Header_DP_r_total * factor_list[N_Headers_before + 2 * i]
            Pin_r_pass = self.Headers[N_Headers_before + 2 * i].P_r - Header_DP_r
            hin_r_pass = self.Headers[N_Headers_before + 2 * i].h_r
            Tin_r_pass = self.Headers[N_Headers_before + 2 * i].T_r
            xin_r_pass = self.Headers[N_Headers_before + 2 * i].x_r
            tube_list = self.Tubes_list[groups_start[i]:groups_end[i]]
            P_r_list = []
            h_r_list = []
            T_r_list = []
            x_r_list = []
            for j,(num,x,y,orient) in enumerate(tube_list):
                num = int(num)
                x = int(x)
                y = int(y)
                orient = int(orient)
                x_in = xin_r_pass
                Pin_r = Pin_r_pass
                hin_r = hin_r_pass
                Tin_r = Tin_r_pass
                self.Tubes_grid[x][y].Pin_r = Pin_r
                self.Tubes_grid[x][y].hin_r = hin_r
                self.Tubes_grid[x][y].Tin_r = Tin_r
                self.Tubes_grid[x][y].x_in = x_in
                self.tube_solver(x,y,orient)
                Pout_r = self.Tubes_grid[x][y].Pout_r
                hout_r = self.Tubes_grid[x][y].hout_r
                Tout_r = self.Tubes_grid[x][y].Tout_r
                x_out = self.Tubes_grid[x][y].x_out
                P_r_list.append(Pout_r)
                h_r_list.append(hout_r)
                T_r_list.append(Tout_r)
                x_r_list.append(x_out)
                
            self.Headers[N_Headers_before + 2 * i + 1].P_r = np.average(P_r_list)
            self.Headers[N_Headers_before + 2 * i + 1].h_r = np.average(h_r_list)
            self.Headers[N_Headers_before + 2 * i + 1].T_r = np.average(T_r_list)
            self.Headers[N_Headers_before + 2 * i + 1].x_r = np.average(x_r_list)
            # to update inlet header to next pass
            if (N_passes_in_bank * 2) > (2 * i + 2):
                Header_DP_r = Header_DP_r_total * factor_list[N_Headers_before + 2 * i + 2]
                self.Headers[N_Headers_before + 2 * i + 2].P_r = np.average(P_r_list) - Header_DP_r
                self.Headers[N_Headers_before + 2 * i + 2].h_r = np.average(h_r_list)
                self.Headers[N_Headers_before + 2 * i + 2].T_r = np.average(T_r_list)
                self.Headers[N_Headers_before + 2 * i + 2].x_r = np.average(x_r_list)
        
    def tube_solver(self,x,y,orient):
        '''
            This function will solve one tube with coordinates x and y where 
            x is the row, and y is the column; orient can be either 1 (entering
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
        Segment_1.L = self.Geometry.T_L / self.Nsegments_calc
        Segment_1.hin_a = hin_a
        Segment_1.Win_a = Win_a
        Segment_1.hout_a = hout_a
        Segment_1.Wout_a = Wout_a
        Segment_1.mdot_r = self.Tubes_grid[x][y].mdot_r
        num = self.Tubes_grid[x][y].num
        while num > self.Geometry.N_tube_per_bank:
            num -= self.Geometry.N_tube_per_bank
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
            Segment_2.L = self.Geometry.T_L / self.Nsegments_calc
            Segment_2.mdot_r = self.Tubes_grid[x][y].mdot_r
            Segment_2.hin_a = self.Air_grid_h[x,y-1,z]
            Segment_2.Win_a = self.Air_grid_W[x,y-1,z]
            Segment_2.hout_a = self.Air_grid_h[x,y+1,z]
            Segment_2.Wout_a = self.Air_grid_W[x,y+1,z]
            num = self.Tubes_grid[x][y].num
            while num > self.Geometry.N_tube_per_bank:
                num -= self.Geometry.N_tube_per_bank
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
        '''this will solve a segment (it can be a first or second of phase change segments)'''
        Ref = ValuesClass()
        Air = ValuesClass()
        Ref.hin_r = Segment.hin_r
        Ref.Pin_r = Segment.Pin_r
        Ref.Tin_r = Segment.Tin_r
        Ref.x_in = Segment.x_in
        Ref.mdot_r = Segment.mdot_r
        Ref.L = Segment.L
        Air.hin_a = Segment.hin_a
        Air.hout_a = Segment.hout_a
        Air.Win_a = Segment.Win_a
        Air.Wout_a = Segment.Wout_a
        Air.Pin_a = Segment.Pin_a
        Air.Pout_a = Segment.Pout_a
        Air.mdot_ha = Segment.mdot_ha
        if self.Tin_a < self.Thermal.Tin_r:
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
        Ref.mdot_r = Segment.mdot_r
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
        if self.terminate:
            self.Solver_Error = "User Terminated run!"
            raise
        AS = self.AS
        Pin_r = Ref_inputs.Pin_r
        x_in = Ref_inputs.x_in 
        hin_r = Ref_inputs.hin_r
        AS.update(CP.PQ_INPUTS,Pin_r,x_in)
        Tin_r = AS.T()
        L = Ref_inputs.L*w_2phase
        A_r = self.Geometry.inner_circum * L
        mdot_r = Ref_inputs.mdot_r
        Rw = self.Geometry.tw / (self.Geometry.Aw * L * self.Thermal.kw)
        
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
        if self.Thermal.FinsOnce == True and hasattr(self,'Nsegments_calc'):
            DP_a_dry = DP_a_dry / self.Geometry.N_bank
        
        DP_a_dry *= self.Thermal.DP_a_dry_tuning
        Pout_a = Pin_a + DP_a_dry

        # air side total area
        if self.Thermal.FinsOnce == True:
            A_a = self.Fins.Ao * w_2phase / (self.Nsegments_calc * self.Geometry.N_tube_per_bank * self.Geometry.N_bank)
        else:
            A_a = self.Fins.Ao
        
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
            if (abs((h_r_old - h_r) / h_r)) < 1e-3:
                break
        
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
            b_r = cair_sat(Tin_r) * 1000
            water_cond = np.finfo(float).eps
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
                    DP_a_wet = DP_a_wet/self.Geometry.N_bank
                
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
                    self.Solver_Error = "Failed to calculate two-phase frictional pressure drop in "
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
                raise ValueError("Pressure drop is very high, the pressure became negative")
            
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

        return Results

    def solver_1phase(self,Ref_inputs,Air_inputs,w_1phase = 1.0):
        if self.terminate:
            self.Solver_Error = "User Terminated run!"
            raise

        '''the function will solve a 1 phase segment'''
        AS = self.AS
        Pin_r = Ref_inputs.Pin_r
        hin_r = Ref_inputs.hin_r        
        Tin_r = Ref_inputs.Tin_r
        x_in = Ref_inputs.x_in
        AS.update(CP.HmassP_INPUTS,hin_r,Pin_r)
        cp_r = AS.cpmass()
        L = Ref_inputs.L*w_1phase
        A_r = self.Geometry.inner_circum * L
        mdot_r = Ref_inputs.mdot_r
        Rw = self.Geometry.tw / (self.Geometry.Aw * L * self.Thermal.kw)
        
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
        if self.Thermal.FinsOnce == True and hasattr(self,'Nsegments_calc'):
            DP_a_dry = DP_a_dry / self.Geometry.N_bank
        
        DP_a_dry *= self.Thermal.DP_a_dry_tuning
        Pout_a = Pin_a + DP_a_dry

        # air side total area
        if self.Thermal.FinsOnce == True:
            A_a = self.Fins.Ao * w_1phase / (self.Nsegments_calc * self.Geometry.N_tube_per_bank * self.Geometry.N_bank)
        else:
            A_a = self.Fins.Ao

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
            Error_Q = 1
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
            
            #Sensible heat transfer rate [kW]
            Q_sensible = mdot_da * cp_da * (Tin_a - Tout_a)
            
            # dry fraction
            f_dry = 0.0
            
            Q = Q_wet
            
            if Tw_o > Tdp:
                Q_sensible = Q

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
        hout_r = hin_r + Q/(mdot_r)
        if Pout_r <= 0:
            if not hasattr(self,"Solver_Error"):
                self.Solver_Error = "Pressure drop is very high that negative pressure exists; please check mass flow rate from compressor or circuit length in "
            raise ValueError("Pressure drop is very high, the pressure became negative")
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

        return Results

    def solver_2phase_phase(self,Ref_inputs,Air_inputs,w_2phase=1.0,w_HX=1.0):
        if self.terminate:
            self.Solver_Error = "User Terminated run!"
            raise

        '''the function will solve a 2 phase segment for phase solver'''        
        N_passes = 0
        N_tubes = 0
        for row in self.Geometry.N_tube_per_bank_per_pass:
            for Pass in row:
                N_tubes += Pass
            N_passes += len(row)
        
        # will solve a 2 phase segment
        AS = self.AS
        Pin_r = Ref_inputs.Pin_r
        x_in = Ref_inputs.x_in 
        hin_r = Ref_inputs.hin_r
        AS.update(CP.PQ_INPUTS,Pin_r,x_in)
        Tin_r = AS.T()
        L = Ref_inputs.L * w_2phase
        A_r = self.Geometry.inner_circum * L
        mdot_r = Ref_inputs.mdot_r
        Rw = self.Geometry.tw / (self.Geometry.Aw * L * self.Thermal.kw)
        
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

        # air side total area
        A_a = self.Fins.Ao * w_2phase / self.Geometry.N_circuits * w_HX
        
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
            
        h_r = 1500 # approcimate assumption

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
                    water_cond = (Win_a - Wout_a) * mdot_da #kg/sec
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
            old_DP = 50
            error_DP = 50
            i = 0
            while error_DP > 1 and i < 5:
                # refrigerant pressure drop
                try:
                    self.Correlations.update(AS,self.Geometry,self.Thermal,'2phase',Pin_r,x_in,mdot_r,A_r,mode,var_2nd_out=x_out)
                    DP_friction = self.Correlations.calculate_dPdz_f_2phase() * (L)
                except:
                    if not hasattr(self,"Solver_Error"):
                        self.Solver_Error = "Failed to calculate two-phase frictional pressure drop in "
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
                    raise ValueError("Pressure drop is very high, the pressure became negative")
                error_DP = abs(DP_total - old_DP)
                # correcting outlet quality with new pressure
                AS.update(CP.PQ_INPUTS,Pout_r,0.0)
                h_L = AS.hmass()
                AS.update(CP.PQ_INPUTS,Pout_r,1.0)
                h_V = AS.hmass()
                x_out = (hout_r-h_L)/(h_V-h_L)
                
                old_DP = DP_total
                i += 1
            error_Q = abs((Q - Q_old_major)/Q)
            Q_old_major = Q
            iter_num += 1
        
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

        return Results

    def solver_1phase_phase(self,Ref_inputs,Air_inputs,w_1phase = 1.0,w_HX=1.0):
        if self.terminate:
            self.Solver_Error = "User Terminated run!"
            raise
        '''the function will solve a 1 phase segment for phase solver'''
        # will solve a 1 phase segment
        AS = self.AS
        Pin_r = Ref_inputs.Pin_r
        hin_r = Ref_inputs.hin_r        
        Tin_r = Ref_inputs.Tin_r
        x_in = Ref_inputs.x_in
        L = Ref_inputs.L * w_1phase
        A_r = self.Geometry.inner_circum * L
        mdot_r = Ref_inputs.mdot_r
        Rw = self.Geometry.tw / (self.Geometry.Aw * L * self.Thermal.kw)
        
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

        # air side total area
        A_a = self.Fins.Ao * w_1phase / self.Geometry.N_circuits * w_HX

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
                Error_Q = 1
                while ((i <= 3) or Error_Q > eps) and (i<20):
                    # saving old value of Q_wet
                    Q_wet_old = Q_wet
                    
                    # saturated air enthalpy at refrigerant inlet temperature
                    if self.Accurate:
                        h_s_w_i = HAPropsSI('H','T',Tin_r, 'P',Pin_a, 'R', 1.0) #[kJ/kg_da]
                    else:
                        Wsat = pl.GetSatHumRatio(Tin_r-273.15, Pin_a)
                        h_s_w_i = pl.GetMoistAirEnthalpy(Tin_r-273.15, Wsat)
                                    
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
    
                #Sensible heat transfer rate [kW]
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
            if x_in >= 1.0:
                DP_total *= self.Thermal.DP_r_superheat_tuning
            elif x_in <= 0.0:
                DP_total *= self.Thermal.DP_r_subcooling_tuning
            else:
                raise
            Pout_r = Pin_r + DP_total
            hout_r = hin_r + Q/(mdot_r)
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

    def mixed_segment_phase(self,Segment,change,w_HX=1.0):
        '''
        Used to calculate portion of the segment where the phase exists for
        phase solver

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
        Ref.mdot_r = Segment.mdot_r
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
                Results = self.solver_1phase_phase(Ref,Air,w_1phase,w_HX=w_HX) 
                return Results.x_out
            w_1phase = brentq(objective,np.finfo(float).eps,1-np.finfo(float).eps)
            return w_1phase
        
        if change == "Vto2phase":
            def objective(w_1phase):
                Results = self.solver_1phase_phase(Ref,Air,w_1phase,w_HX=w_HX)
                return Results.x_out-1
            w_1phase = brentq(objective,np.finfo(float).eps,1-np.finfo(float).eps)
            return w_1phase
        if change == "2phasetoL":
            def objective(w_2phase):
               Results = self.solver_2phase_phase(Ref,Air,w_2phase,w_HX=w_HX) 
               return Results.x_out
            w_2phase = brentq(objective,np.finfo(float).eps,1-np.finfo(float).eps)
            return w_2phase
        if change == "2phasetoV":
            def objective(w_2phase):
               Results = self.solver_2phase_phase(Ref,Air,w_2phase,w_HX=w_HX) 
               return Results.x_out-1
            w_2phase = brentq(objective,np.finfo(float).eps,1-np.finfo(float).eps)
            return w_2phase

    def phase_by_phase_solver(self):
        '''The function is used to solve HX with phase by phase model'''
        
        mdot_r_phase = self.mdot_r / self.Geometry.N_circuits
        mdot_ha_phase = self.Thermal.mdot_ha / self.Geometry.N_circuits
        L_circuit = self.Geometry.T_L * self.Geometry.N_tube_per_bank * self.Geometry.N_bank / self.Geometry.N_circuits
        hin_r = self.hin_r
        Pin_r = self.Pin_r
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
        phase_segment_1.mdot_ha = mdot_ha_phase
        phase_segment_1.Pin_a = self.Pin_a
        phase_segment_1.Pout_a = self.Pin_a
        phase_segment_1.Win_a = self.Win_a
        phase_segment_1.Wout_a = self.Win_a
        if self.Accurate:
            hin_a = HAPropsSI('H','T',self.Tin_a,'W',self.Win_a,'P',self.Pin_a)
        else:
            hin_a = pl.GetMoistAirEnthalpy(self.Tin_a-273.15, self.Win_a)
        phase_segment_1.hin_a = hin_a
        phase_segment_1.hout_a = hin_a
        phase_segment_1.L = L_circuit
        phase_segment_1.w_HX = 1.0
        phase_segment_1.w_phase = 1.0
        self.phase_segments = []
        w_HX = 0
        while not finished:
            phase_segment_2 = self.solve_phase(phase_segment_1)
            self.phase_segments.append(phase_segment_2)
            w_HX += phase_segment_2.w_phase * (1 - w_HX)
            phase_segment_1.hin_r = phase_segment_2.hout_r
            phase_segment_1.Pin_r = phase_segment_2.Pout_r
            phase_segment_1.Tin_r = phase_segment_2.Tout_r
            phase_segment_1.x_in = phase_segment_2.x_out
            phase_segment_1.mdot_r = mdot_r_phase
            phase_segment_1.mdot_ha = mdot_ha_phase * (1 - w_HX)
            phase_segment_1.Pin_a = self.Pin_a
            phase_segment_1.Pout_a = self.Pin_a
            phase_segment_1.Win_a = self.Win_a
            phase_segment_1.Wout_a = self.Win_a
            phase_segment_1.hin_a = hin_a
            phase_segment_1.hout_a = hin_a
            phase_segment_1.L = L_circuit * (1 - w_HX)
            phase_segment_1.w_HX = (1 - w_HX)
            if w_HX >= 1.0:
                finished = True
            
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
        w_HX = phase_segment.w_HX
        if self.Tin_a < self.Thermal.Tin_r:
            mode = 'heater'
        else:
            mode = 'cooler'
        # this is a normal segment
        if 0 < Ref.x_in < 1 or (Ref.x_in == 0 and mode == 'cooler') or (Ref.x_in == 1 and mode == 'heater'): # 2phase inlet
            Results = self.solver_2phase_phase(Ref,Air,w_HX=w_HX)
            # normally
            Results.phase_change = False
            if not (0 <= Results.x_out <= 1):
                # phase change happened
                if Results.x_out > 1:
                    # it is from 2phase to Vapor
                    
                    # this is to find portion of segment where 2phase exist
                    # and construct the first segment
                    w_2phase = self.mixed_segment_phase(phase_segment,'2phasetoV',w_HX=w_HX)
                    phase_change_type = "2phasetoV"
                    
                    Results = self.solver_2phase_phase(Ref,Air,w_2phase,w_HX=w_HX)
                    # to avoid small tolerance in x
                    Results.x_out = 1.0
                elif Results.x_out < 0:
                    # it is from 2phase to liquid
                    # this is to find portion of segment where 2phase exist
                    # and construct the first segment
                    w_2phase = self.mixed_segment_phase(phase_segment,'2phasetoL',w_HX=w_HX)
                    phase_change_type = "2phasetoL"
                    
                    Results = self.solver_2phase_phase(Ref,Air,w_2phase,w_HX=w_HX)
                    # to avoid small tolerance in x
                    Results.x_out = 0.0
                Results.phase_change_type = phase_change_type
                Results.phase_change = True
                Results.w_phase = w_2phase
        elif Ref.x_in < 0 or (Ref.x_in == 0 and mode == 'heater'): #subcooled
            Results = self.solver_1phase_phase(Ref,Air,w_HX=w_HX)
            # normally
            Results.phase_change = False
            if not (Results.x_out < 0):
                # phase change happened
                
                # this is to find portion of segment where Liquid exist
                # and construct the first segment
                w_1phase = self.mixed_segment_phase(phase_segment,'Lto2phase',w_HX=w_HX)
                Results = self.solver_1phase_phase(Ref,Air,w_1phase,w_HX=w_HX)
                # to avoid small tolerance in x
                Results.x_out = 0.0
                Results.phase_change_type = "Lto2phase"
                Results.phase_change = True
                Results.w_phase = w_1phase
        elif Ref.x_in > 1 or (Ref.x_in == 1 and mode == 'cooler'): # superheated
            Results = self.solver_1phase_phase(Ref,Air,w_HX=w_HX)
            # normally
            Results.phase_change = False
            if not (Results.x_out > 1):
                # phase change happened
                
                # find porion of segment where vapor exist and contruct
                # a segment with it
                w_1phase = self.mixed_segment_phase(phase_segment,'Vto2phase',w_HX=w_HX)
                                    
                Results = self.solver_1phase_phase(Ref,Air,w_1phase,w_HX=w_HX)
                # to avoid small tolerance in x
                Results.x_out = 1.0
                Results.phase_change_type = "Vto2phase"
                Results.phase_change = True
                Results.w_phase = w_1phase
        return Results

if __name__=='__main__':
    import time
    Ref = 'R410A'
    Backend = 'HEOS'
    AS = CP.AbstractState(Backend, Ref)
    Cond = MicroChannelHEXClass()
    Cond.AS = AS # AbstractState
    Cond.model = 'phase' # either 'phase' or 'segment'
    Cond.Fan_add_DP = 0
    # each major array element represent a bank, each element in minor array reperesent number of tubes per pass (number of elements in minor array is the number of passes)
    Cond.Geometry.N_tube_per_bank_per_pass = [[22,14,8,6]]
    Cond.Geometry.Fin_rows = 51 # it can be more or less than number of tubes per bank by 1
    Cond.Geometry.T_L = 0.745 # tube length
    Cond.Geometry.T_w = 0.016 # tube width
    Cond.Geometry.T_h = 0.0018 # tube height
    Cond.Geometry.T_s = 0.008 # tube spacing (fin height)
    Cond.Geometry.P_shape = 'Rectangle' # port shape 'Rectangle' or 'Circle' or 'Triangle'
    Cond.Geometry.P_end = 'Extended' # ports 'Extended' to the far ends by circular ends or not 'Normal'
    Cond.Geometry.P_a = 0.0012 # port major dimension
    Cond.Geometry.P_b = 0.0007 # port minor dimension (optional)
    Cond.Geometry.N_port = 16 # number of ports per tube
    Cond.Geometry.Enhanced = False # internal fins in ports
    Cond.Geometry.FinType = 'Louvered' # fin type
    Cond.Geometry.Fin_t = 0.00008 # fin thickness
    Cond.Geometry.Fin_L = 0.016 # fin length
    Cond.Geometry.Fin_Llouv = 0.0068 # height of fin louver
    Cond.Geometry.Fin_alpha = 24 # angle of louver
    Cond.Geometry.FPI = 19 # fins per inch
    Cond.Geometry.Fin_Lp = 0.001 # louver pitch
    Cond.Geometry.e_D = 0.0 # tube internal roughness
    Cond.Geometry.Header_CS_Type = 'Rectangle' # header cross section 'Rectangle' or 'Circle'
    Cond.Geometry.Header_dim_a = 0.03 # header major dimension
    Cond.Geometry.Header_dim_b = 0.03 # header minor dimension
    Cond.Geometry.Header_length = 0.550 # header total height
    # Cond.mdot_ha = 0.1 # air humid mass flow rate
    Cond.Vdot_ha = 33.5/60 # air humid volume flow rate
    # Cond.Thermal.Vel_dist = [[0.8 for i in range(20)], # air velocity distribution
    #                           [0.9 for i in range(20)],
    #                           [1.1 for i in range(20)],
    #                           [0.9 for i in range(20)],
    #                           [0.7 for i in range(20)],]
    
    Cond.Pin_a = 101325 # inlet air pressure
    Cond.mdot_r = 77.91/3600 # inlet mass flow rate of refrigerant
    Cond.Thermal.Nsegments = 10 # number of segments per tube
    Cond.Thermal.kw = 205 # tube wall conductivity
    Cond.Thermal.h_r_superheat_tuning = 1.0 # tuning factor for refrigerant superheat HTC
    Cond.Thermal.h_r_subcooling_tuning = 1.0 # tuning factor for refrigerant subcool HTC
    Cond.Thermal.h_r_2phase_tuning = 1.0 # tuning factor for refrigerant 2phase HTC
    Cond.Thermal.h_a_dry_tuning = 1.0 # tuning factor for air dry HTC
    Cond.Thermal.h_a_wet_tuning = 1.0 # tuning factor for air wet HTC
    Cond.Thermal.DP_r_superheat_tuning = 1.0 # tuning factor for refrigerant superheat pressure drop
    Cond.Thermal.DP_r_subcooling_tuning = 1.0 # tuning factor for refrigerant subcool pressure drop
    Cond.Thermal.DP_r_2phase_tuning = 1.0 # tuning factor for refrigerant 2phase pressure drop
    Cond.Thermal.DP_a_dry_tuning = 1.0 # tuning factor for air pressure drop
    Cond.Thermal.k_fin = 205 # fin thermal conductivity
    Cond.Thermal.FinsOnce = False # calculate fins only once or per each segment
    Cond.Thermal.Headers_DP_r = 1000 # total header pressure drop in Pa
    Cond.Thermal.h_a_wet_on = False # don't use wet air pressure drop correlation
    Cond.Thermal.DP_a_wet_on = False # don't use wet air pressure drop correlation
    Cond.Accurate = True # use CoolProp (True) or psychrolib (False)

    # Cond.Fan.model = 'curve'
    # a = 17.04447135
    # b = 2135.389026
    # c = -16099.01934
    # d = 48475.41375
    # Cond.Fan.power_curve = str(a)+'+('+str(b)+')*X+('+str(c)+')*X**2+('+str(d)+')*X**3'
    # a = 1708.571429
    # b = 8400.974026
    # c = -459253.2468
    # d = -767045.4545
    # Cond.Fan.DP_curve = str(a)+'+('+str(b)+')*X+('+str(c)+')*X**2+('+str(d)+')*X**3'

    Cond.Fan.model = 'power'
    Cond.Fan.power_exp = '60'

    Cond.Fan.Fan_position = 'after' # relative to HX

    # evaporator
    # Cond.Pin_r = 9 * 101325 # inlet refrigerant pressure
    # AS.update(CP.PQ_INPUTS,Cond.Pin_r,0.1)
    # h_in = AS.hmass()
    # Cond.hin_r = h_in # inlet refrigerant enthalpy
    # Cond.Tin_a = 295 # inlet air temperature
    # Win_a = HAPropsSI('W','P',Cond.Pin_a,'T',Cond.Tin_a,'R',0.5)
    # Cond.Win_a = Win_a # inlet air humidity ratio
    
    # condenser
    Cond.Pin_r = 2.75e6
    DT = 80
    AS.update(CP.PQ_INPUTS,Cond.Pin_r,1.0)
    T_sat = AS.T()
    T_in = T_sat + DT
    AS.update(CP.PT_INPUTS,Cond.Pin_r, T_in)
    # Cond.hin_r = AS.hmass()
    Cond.hin_r = 475.3409872e3
    Cond.Tin_a = 35+273.15
    Win_a = HAPropsSI('W','P',Cond.Pin_a,'T',Cond.Tin_a,'R',0.5)
    Cond.Win_a = Win_a
    
    T1 = time.time()
    Cond.solve(Max_Q_error=0.01,Max_num_iter=30, initial_Nsegments=1)
    T2 = time.time()
    print("total time:",T2-T1)
    global A_a
    A_a = 0
    i = 1
    global list_of_segments
    list_of_segments = []
    if hasattr(Cond,'Tubes_list'):
        for x,y in Cond.Tubes_list[:,[1,2]]:
            x = int(x)
            y = int(y)
            for j,segment in enumerate(Cond.Tubes_grid[x][y].Segments):
                A_a += segment.A_a
                i += 1
                list_of_segments.append(segment)
        global states
        states = np.zeros([len(list_of_segments)+1,9])
        w = 0.0
        for i,Segment in enumerate(list_of_segments):
            states[i] = [w, Segment.hin_r, Segment.Pin_r, Segment.x_in, Segment.Tout_a, Segment.Wout_a,Segment.w_phase,Segment.DP_a,Segment.h_r]
            w = states[i,0]+Segment.A_r/(Cond.Geometry.inner_circum*Cond.Geometry.N_tube_per_bank*Cond.Geometry.T_L*Cond.Geometry.N_bank)
            states[-1] = [1.0, list_of_segments[-1].hout_r, list_of_segments[-1].Pout_r, list_of_segments[-1].x_out, -1, -1,0,0,0]
    print('model:',Cond.model)
    print('DP_r:',Cond.Results.DP_r)
    print('DP_r_subcool:',Cond.Results.DP_r_subcool)
    print('DP_r_2phase:',Cond.Results.DP_r_2phase)
    print('DP_r_superheat:',Cond.Results.DP_r_superheat)
    print('h_r_subcool:',Cond.Results.h_r_subcool)
    print('h_r_2phase:',Cond.Results.h_r_2phase)
    print('h_r_superheat:',Cond.Results.h_r_superheat)
    print('DP_a:',Cond.Results.DP_a)
    print('h_a_dry:',Cond.Results.h_a_dry)
    print('h_a_wet:',Cond.Results.h_a_wet)
    print('Q:',Cond.Results.Q)
    print('Q_superheat:',Cond.Results.Q_superheat)
    print('Q_2phase:',Cond.Results.Q_2phase)
    print('Q_subcool:',Cond.Results.Q_subcool)
    print('Q_sensible:',Cond.Results.Q_sensible)
    print('Q_latent:',Cond.Results.Q - Cond.Results.Q_sensible)
    print('w_superheat:',Cond.Results.w_superheat)
    print('w_2phase:',Cond.Results.w_2phase)
    print('w_subcool:',Cond.Results.w_subcool)
    print('x_out',Cond.Results.xout_r)
    print('Charge',Cond.Results.Charge)
    print('A_r:',Cond.Geometry.A_r)
    print('SC:',Cond.Results.SC)
    print('Converged:',Cond.Converged)
    from copy import deepcopy
    Cond1 = deepcopy(Cond.Results)
    Cond.model='segment'
    T1 = time.time()
    Cond.solve(Max_Q_error=0.01,Max_num_iter=30, initial_Nsegments=1)
    T2 = time.time()
    print("----------------------")
    print("total time:",T2-T1)
    print('model:',Cond.model)
    print('DP_r:',Cond.Results.DP_r)
    print('DP_r_subcool:',Cond.Results.DP_r_subcool)
    print('DP_r_2phase:',Cond.Results.DP_r_2phase)
    print('DP_r_superheat:',Cond.Results.DP_r_superheat)
    print('h_r_subcool:',Cond.Results.h_r_subcool)
    print('h_r_2phase:',Cond.Results.h_r_2phase)
    print('h_r_superheat:',Cond.Results.h_r_superheat)
    print('DP_a:',Cond.Results.DP_a)
    print('h_a_dry:',Cond.Results.h_a_dry)
    print('h_a_wet:',Cond.Results.h_a_wet)
    print('Q:',Cond.Results.Q)
    print('Q_superheat:',Cond.Results.Q_superheat)
    print('Q_2phase:',Cond.Results.Q_2phase)
    print('Q_subcool:',Cond.Results.Q_subcool)
    print('Q_sensible:',Cond.Results.Q_sensible)
    print('Q_latent:',Cond.Results.Q - Cond.Results.Q_sensible)
    print('w_superheat:',Cond.Results.w_superheat)
    print('w_2phase:',Cond.Results.w_2phase)
    print('w_subcool:',Cond.Results.w_subcool)
    print('x_out',Cond.Results.xout_r)
    print('Charge',Cond.Results.Charge)
    print('A_r:',Cond.Geometry.A_r)
    print('Converged:',Cond.Converged)
    