from __future__ import division, print_function, absolute_import
from backend.FinTubeCircuit import FinTubeCircuitClass
import numpy as np
from scipy.optimize import newton, least_squares, root
import CoolProp as CP
from backend.Fan import FanClass
from CoolProp.CoolProp import HAPropsSI
import psychrolib as pl
pl.SetUnitSystem(pl.SI)

class ValuesClass():
    pass

class FinTubeHEXClass():
    def __init__(self,**kwargs):
        # to initiate connections and mass ratios
        self.mass_ratios = []
        self.Fan = FanClass()
        self.Connections = np.zeros([1,7])-1
        self.DP_converged = False
        self.terminate = False
        
    def Update(self,**kwargs):
        self.__dict__.update(kwargs)

    def OutputList(self):
        if self.model == "phase":
            model = "Phase-by-phase"
        elif self.model == "segment":
            model = "Segment-by-segment"
        output_list = [('Name','',self.name),
                       ('','',''),
                       ('Heat Exchanger Mode','',model),
                       ('','',''),
                       ('Heat Transfer','W',self.Results.Q),
                       ('Superheat Heat Trasnfer','W',self.Results.Q_superheat),
                       ('Two-phase Heat Trasnfer','W',self.Results.Q_2phase),
                       ('Subcool Heat Trasnfer','W',self.Results.Q_subcool),
                       ('','',''),
                       ('Sensible Heat Transfer','W',self.Results.Q_sensible),
                       ('Latent Heat Transfer','W',self.Results.Q - self.Results.Q_sensible),
                       ('','',''),
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
                       ('Inner heat transfer area (refrigerant side)','m^2',self.Results.A_r),
                       ('Outer heat transfer area (air side)','m^2',self.Results.A_a),
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
                       ('Refrigerant Outlet Dew Temperature','C',"None" if (self.Results.Tdew_out==None) else self.Results.Tdew_out-273.15),
                       ('','',''),
                       ('Refrigerant Superheat','K',"None" if (self.Results.SH==None) else self.Results.SH),
                       ('Refrigerant Subcool','K',"None" if (self.Results.SC==None) else self.Results.SC),
                       ('','',''),
                       ('Air Inlet Temperature','C',self.Results.Tin_a-273.15),
                       ('Air Inlet Pressure','Pa',self.Results.Pin_a),
                       ('Air Inlet Humidity Ratio','kg/kg',self.Results.Win_a),
                       ('','',''),
                       ('Air Outlet Temperature','C',self.Results.Tout_a-273.15),
                       ('Air Outlet Pressure','Pa',self.Results.Pout_a),
                       ('Air Outlet Humidity Ratio','kg/kg',self.Results.Wout_a),
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
                       ('Converged?','',self.Converged),
                       ]
        return output_list
                
    def results_creator(self):
        ''' function used to create results as a values class'''
        AS = self.AS
        self.Results = ValuesClass()
        self.Results.Q = 0
        self.Results.water_cond = 0
        self.Results.water_cond_superheat = 0
        self.Results.water_cond_2phase = 0
        self.Results.water_cond_subcool = 0
        self.Results.Charge = 0
        self.Results.Charge_superheat = 0
        self.Results.Charge_2phase = 0
        self.Results.Charge_subcool = 0
        self.Results.UA = 0
        self.Results.UA_superheat = 0
        self.Results.UA_2phase = 0
        self.Results.UA_subcool = 0
        self.Results.Q_sensible = 0
        self.Results.Q_superheat = 0
        self.Results.Q_2phase = 0
        self.Results.Q_subcool = 0
        self.Results.DP_r_superheat = 0
        self.Results.DP_r_2phase = 0
        self.Results.DP_r_subcool = 0
        self.Results.A_r = 0
        self.Results.A_a = 0
        self.Air_h_a_dry_values = []
        self.Air_eta_a_dry_values = []
        self.Air_UA_dry_values = []
        self.Air_h_a_wet_values = []
        self.Air_eta_a_wet_values = []
        self.Air_UA_values = []
        self.Air_h_a_values = []
        self.Air_eta_a_values = []
        self.Air_UA_wet_values = []
        self.h_r_subcool_values = []
        self.h_r_2phase_values = []
        self.h_r_superheat_values = []
        self.w_circuit_values = []
        
        A_r = 0
        A_r_superheat = 0
        A_r_2phase = 0
        A_r_subcool = 0
        
        delta_T_pinch = np.inf
        delta_T_loc = None
        
        # summing results from circuits
        for circuit in self.Circuits:
            A_r_circuit = circuit.Geometry.A_r
            A_r += A_r_circuit
            self.Air_h_a_dry_values.append(circuit.Results.h_a_dry)
            self.Air_eta_a_dry_values.append(circuit.Results.eta_a_dry)
            self.Air_UA_dry_values.append(circuit.Results.UA_dry)
            self.Air_h_a_wet_values.append(circuit.Results.h_a_wet)
            self.Air_eta_a_wet_values.append(circuit.Results.eta_a_wet)
            self.Air_UA_wet_values.append(circuit.Results.UA_wet)
            self.Air_h_a_values.append(circuit.Results.h_a)
            self.Air_eta_a_values.append(circuit.Results.eta_a)
            self.Air_UA_values.append(circuit.Results.UA)
            self.h_r_subcool_values.append(circuit.Results.h_r_subcool)
            self.h_r_2phase_values.append(circuit.Results.h_r_2phase)
            self.h_r_superheat_values.append(circuit.Results.h_r_superheat)
            
            delta_T_pinch = min(delta_T_pinch,circuit.Results.delta_T_pinch)

            if delta_T_pinch == circuit.Results.delta_T_pinch:
                delta_T_loc = circuit.Results.delta_T_loc
            
            self.Results.Q += circuit.Results.Q
            self.Results.Q_superheat += circuit.Results.Q_superheat
            self.Results.Q_2phase += circuit.Results.Q_2phase
            self.Results.Q_subcool += circuit.Results.Q_subcool
            self.Results.water_cond += circuit.Results.water_cond
            self.Results.water_cond_superheat += circuit.Results.water_cond_superheat
            self.Results.water_cond_2phase += circuit.Results.water_cond_2phase
            self.Results.water_cond_subcool += circuit.Results.water_cond_subcool
            A_r_superheat += circuit.Results.w_superheat * A_r_circuit
            A_r_2phase += circuit.Results.w_2phase * A_r_circuit
            A_r_subcool += circuit.Results.w_subcool * A_r_circuit
            self.Results.Charge += circuit.Results.Charge
            self.Results.Charge_superheat += circuit.Results.Charge_superheat
            self.Results.Charge_2phase += circuit.Results.Charge_2phase
            self.Results.Charge_subcool += circuit.Results.Charge_subcool
            self.Results.DP_r_superheat += circuit.Results.DP_r_superheat
            self.Results.DP_r_2phase += circuit.Results.DP_r_2phase
            self.Results.DP_r_subcool += circuit.Results.DP_r_subcool
            self.Results.UA += circuit.Results.UA # this is not very accurate
            self.Results.UA_superheat += circuit.Results.UA_superheat # this is not very accurate
            self.Results.UA_2phase += circuit.Results.UA_2phase # this is not very accurate
            self.Results.UA_subcool += circuit.Results.UA_subcool # this is not very accurate
            self.Results.Q_sensible += circuit.Results.Q_sensible
            self.Results.A_r += circuit.Geometry.A_r
            self.Results.A_a += circuit.Geometry.A_a
        
        self.w_circuit_values = [circuit.Geometry.A_r/A_r for circuit in self.Circuits]
        self.Results.delta_T_pinch = delta_T_pinch
        self.Results.delta_T_loc = delta_T_loc
        
        self.Results.w_superheat = A_r_superheat / A_r
        self.Results.w_2phase = A_r_2phase / A_r
        self.Results.w_subcool = A_r_subcool / A_r

        self.Air_h_a_dry_values = np.array(self.Air_h_a_dry_values)
        self.Air_eta_a_dry_values = np.array(self.Air_eta_a_dry_values)
        self.Air_UA_dry_values = np.array(self.Air_UA_dry_values)
        self.Air_h_a_wet_values = np.array(self.Air_h_a_wet_values)
        self.Air_eta_a_wet_values = np.array(self.Air_eta_a_wet_values)
        self.Air_UA_wet_values = np.array(self.Air_UA_wet_values)
        self.Air_h_a_values = np.array(self.Air_h_a_values)
        self.Air_eta_a_values = np.array(self.Air_eta_a_values)
        self.Air_UA_values = np.array(self.Air_UA_values)
        self.h_r_subcool_values = np.array(self.h_r_subcool_values)
        self.h_r_2phase_values = np.array(self.h_r_2phase_values)
        self.h_r_superheat_values = np.array(self.h_r_superheat_values)
        self.w_circuit_values = np.array(self.w_circuit_values)
        
        self.Results.h_a_dry = sum(self.Air_h_a_dry_values * self.w_circuit_values)
        self.Results.eta_a_dry = sum(self.Air_eta_a_dry_values * self.w_circuit_values)
        self.Results.UA_dry = sum(self.Air_UA_dry_values * self.w_circuit_values)
        self.Results.h_a_wet = sum(self.Air_h_a_wet_values * self.w_circuit_values)
        self.Results.eta_a_wet = sum(self.Air_eta_a_wet_values * self.w_circuit_values)
        self.Results.UA_wet = sum(self.Air_UA_wet_values * self.w_circuit_values)
        self.Results.h_a = sum(self.Air_h_a_values * self.w_circuit_values)
        self.Results.eta_a = sum(self.Air_eta_a_values * self.w_circuit_values)
        self.Results.UA = sum(self.Air_UA_values * self.w_circuit_values)
        self.Results.h_r_subcool = sum(self.h_r_subcool_values * self.w_circuit_values)
        self.Results.h_r_2phase = sum(self.h_r_2phase_values * self.w_circuit_values)
        self.Results.h_r_superheat = sum(self.h_r_superheat_values * self.w_circuit_values)
        
        # calculating SHR of HX
        self.Results.SHR = self.Results.Q_sensible / self.Results.Q
            
        # inlet pressure is by definition highest pressure
        self.Results.Pin_r = max(self.nodes[:,2])
        
        self.Results.mdot_r = self.mdot_r
        
        # inlet conditions
        self.Results.hin_r = self.hin_r
        AS.update(CP.HmassP_INPUTS, self.Results.hin_r, self.Results.Pin_r)
        self.Results.Tin_r = AS.T()
        self.Results.Sin_r = AS.smass()
        AS.update(CP.PQ_INPUTS, self.Results.Pin_r, 0.0)
        hL = AS.hmass()
        AS.update(CP.PQ_INPUTS, self.Results.Pin_r, 1.0)
        hV = AS.hmass()
        self.Results.xin_r = (self.hin_r - hL) / (hV - hL)
        
        # assuming all refrigerant is mixed at the end, lowest pressure will be outlet pressure
        self.Results.Pout_r = min(self.nodes[:,2])
        self.Results.DP_r = self.Results.Pout_r - self.Results.Pin_r
        
        # column 4 represents mdot*h, getting values at lowest pressure node
        self.Results.hout_r = float(self.nodes[self.nodes[:,2] == self.Results.Pout_r,3] / self.nodes[self.nodes[:,2] == self.Results.Pout_r,1])
        AS.update(CP.HmassP_INPUTS,self.Results.hout_r,self.Results.Pout_r)
        self.Results.Tout_r = AS.T()
        self.Results.Sout_r = AS.smass()
        AS.update(CP.PQ_INPUTS,self.Results.Pout_r,0.0)
        hL = AS.hmass()
        AS.update(CP.PQ_INPUTS,self.Results.Pout_r,1.0)
        hV = AS.hmass()
        self.Results.xout_r = (self.Results.hout_r-hL)/(hV-hL)
        AS.update(CP.PQ_INPUTS,self.Pin_r,0.0)
        hL = AS.hmass()
        AS.update(CP.PQ_INPUTS,self.Pin_r,1.0)
        hV = AS.hmass()
        self.Results.xin_r = (self.hin_r-hL)/(hV-hL)
        
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
                
        # air results 
        self.Results.Tin_a = self.Tin_a
        self.Results.Pin_a = self.Pin_a
        self.Results.Win_a = self.Win_a
        
        mdot_ha = 0
        mdot_da = 0
        hout_a_weighted = []
        Wout_a_weighted = []
        Pout_a_weighted = []
        Convergence = []
        A_a = 0
        if self.Air_sequence == "parallel":
            DP_a_array = []
            for circuit in self.Circuits:
                mdot_ha += circuit.Results.mdot_ha
                mdot_da += circuit.Results.mdot_da
                hout_a_weighted.append(circuit.Results.hout_a * circuit.Results.mdot_da)
                Wout_a_weighted.append(circuit.Results.Wout_a * circuit.Results.mdot_da)
                Pout_a_weighted.append(circuit.Results.Pout_a * circuit.Results.mdot_da)
                Convergence.append(circuit.Converged)
                A_a += circuit.Geometry.A_a
                DP_a_array.append(circuit.Results.DP_a)
            
            self.Results.DP_a_array = DP_a_array
            hout_a = sum(hout_a_weighted) / mdot_da
            Wout_a = sum(Wout_a_weighted) / mdot_da
            Pout_a = sum(Pout_a_weighted) / mdot_da
            
        elif self.Air_sequence == 'series_parallel':
            self.Connections = self.Connections[np.lexsort([self.Connections[:,1],self.Connections[:,0]])]
            first_circuit_num = int(self.Connections[0,2])
            last_circuit_num = int(self.Connections[-1,2])
            mdot_ha = self.Circuits[first_circuit_num].Results.mdot_ha
            mdot_da = self.Circuits[first_circuit_num].Results.mdot_da
            Pout_a = self.Circuits[last_circuit_num].Results.Pout_a
            hout_a = self.Circuits[last_circuit_num].Results.hout_a
            Wout_a = self.Circuits[last_circuit_num].Results.Wout_a
            for circuit in self.Circuits:
                Convergence.append(circuit.Converged)
                A_a += circuit.Geometry.A_a

        elif self.Air_sequence == 'series_counter':
            self.Connections = self.Connections[np.lexsort([self.Connections[:,1],self.Connections[:,0]])]
            first_circuit_num = int(self.Connections[0,2])
            last_circuit_num = int(self.Connections[-1,2])
            mdot_ha = self.Circuits[last_circuit_num].Results.mdot_ha
            mdot_da = self.Circuits[last_circuit_num].Results.mdot_da
            Pout_a = self.Circuits[first_circuit_num].Results.Pout_a
            hout_a = self.Circuits[first_circuit_num].Results.hout_a
            Wout_a = self.Circuits[first_circuit_num].Results.Wout_a
            for circuit in self.Circuits:
                Convergence.append(circuit.Converged)
                A_a += circuit.Geometry.A_a

        elif self.Air_sequence == 'sub_HX_first':
            DP_a_array = []
            for circuit in self.Circuits[1:]:
                mdot_ha += circuit.Results.mdot_ha
                mdot_da += circuit.Results.mdot_da
                hout_a_weighted.append(circuit.Results.hout_a * circuit.Results.mdot_da)
                Wout_a_weighted.append(circuit.Results.Wout_a * circuit.Results.mdot_da)
                Pout_a_weighted.append(circuit.Results.Pout_a * circuit.Results.mdot_da)
                Convergence.append(circuit.Converged)
                A_a += circuit.Geometry.A_a
                DP_a_array.append(circuit.Results.DP_a)
            Convergence.append(self.Circuits[0].Converged)
            A_a += self.Circuits[0].Geometry.A_a
            
            self.Results.DP_a_array = DP_a_array
            hout_a = sum(hout_a_weighted) / mdot_da
            Wout_a = sum(Wout_a_weighted) / mdot_da
            Pout_a = sum(Pout_a_weighted) / mdot_da

        elif self.Air_sequence == 'sub_HX_last':
            DP_a_array = []
            for circuit in self.Circuits[:-1]:
                mdot_ha += circuit.Results.mdot_ha
                mdot_da += circuit.Results.mdot_da
                hout_a_weighted.append(circuit.Results.hout_a * circuit.Results.mdot_da)
                Wout_a_weighted.append(circuit.Results.Wout_a * circuit.Results.mdot_da)
                Pout_a_weighted.append(circuit.Results.Pout_a * circuit.Results.mdot_da)
                Convergence.append(circuit.Converged)
                A_a += circuit.Geometry.A_a
                DP_a_array.append(circuit.Results.DP_a)
            Convergence.append(self.Circuits[-1].Converged)
            A_a += self.Circuits[-1].Geometry.A_a
            
            self.Results.DP_a_array = DP_a_array
            hout_a = sum(hout_a_weighted) / mdot_da
            Wout_a = sum(Wout_a_weighted) / mdot_da
            Pout_a = sum(Pout_a_weighted) / mdot_da
        
        self.Results.mdot_ha = mdot_ha
        self.Results.mdot_da = mdot_da
        self.Results.Pout_a = Pout_a
        self.Results.Wout_a = Wout_a
        if self.Accurate:
            Tout_a = HAPropsSI('T','H',hout_a,'P',Pout_a,'W',Wout_a)
        else:
            Tout_a = pl.GetTDryBulbFromEnthalpyAndHumRatio(hout_a, Wout_a) + 273.15
        self.Results.Tout_a = Tout_a
        self.Results.DP_a = self.Results.Pout_a - self.Results.Pin_a
        if self.Accurate:
            v_ha_in = HAPropsSI('V','T',self.Results.Tin_a,'P',self.Results.Pin_a,'W',self.Results.Win_a)
            v_ha_out = HAPropsSI('V','T',self.Results.Tout_a,'P',self.Results.Pout_a,'W',self.Results.Wout_a)
        else:
            v_ha_in = pl.GetMoistAirVolume(self.Results.Tin_a-273.15, self.Results.Win_a, self.Results.Pin_a)
            v_ha_out = pl.GetMoistAirVolume(self.Results.Tout_a-273.15, self.Results.Wout_a, self.Results.Pout_a)
        self.Results.Vdot_ha_in = mdot_da * v_ha_in
        self.Results.Vdot_ha_out = self.Results.mdot_da * v_ha_out
        self.Results.A_a = A_a
        if all(Convergence):
            self.Converged = True
        else:
            self.Converged = False
        
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
                self.Results.TTD = abs(self.Results.Tout_a - self.Results.Tin_r)
                
        elif self.Results.Tin_r < self.Results.Tin_a: # Evaporator
            if self.Results.Tdew_out != None:
                self.Results.TTD = abs(self.Results.Tout_a - self.Results.Tdew_out)
            else:
                self.Results.TTD = abs(self.Results.Tout_a - self.Results.Tout_r)
                

    def DP_a_fast_calculate(self):
        '''
        This function is used to calculate HX pressure drop based on dry analysis
        without solving heat transfer. used as initial solution while solving HX with fan

        Returns
        -------
        DP_a_dry : float
            HX air pressure drop.

        '''
        Vdot_a = self.Vdot_ha
        if self.Air_sequence == 'parallel':
            for i,circuit in enumerate(self.Circuits):
                circuit.Thermal.Vdot_ha = Vdot_a * self.Air_distribution[i]
        elif self.Air_sequence in ['series_counter','series_parallel']:
            for i,circuit in enumerate(self.Circuits):
                circuit.Thermal.Vdot_ha = Vdot_a
        elif self.Air_sequence == 'sub_HX_first':
            for i,circuit in enumerate(self.Circuits[1:]):
                circuit.Thermal.Vdot_ha = Vdot_a * self.Air_distribution[i]
            self.Circuits[0].Thermal.Vdot_ha = Vdot_a
        elif self.Air_sequence == 'sub_HX_last':
            for i,circuit in enumerate(self.Circuits[:-1]):
                circuit.Thermal.Vdot_ha = Vdot_a * self.Air_distribution[i]
            self.Circuits[-1].Thermal.Vdot_ha = Vdot_a

        if not hasattr(self,'model'):
            self.model = 'segment'
        assert(self.model in ['segment', 'phase']),'please choose a correct model for HX'
        for Circuit in self.Circuits:
            Circuit.model = self.model
            
        DP_a = 0
        for circuit in self.Circuits:
            circuit.Accurate = self.Accurate
        if self.Air_sequence == "parallel":
            # pressure drop is the volume average of circuits
            Vdot_ha = 0
            Pout_a_weighted = []
            for circuit in self.Circuits:
                circuit.Thermal.Tin_a = self.Tin_a
                circuit.Thermal.Pin_a = self.Pin_a
                circuit.Thermal.Win_a = self.Win_a
                Vdot_ha += circuit.Thermal.Vdot_ha
                DP_a = circuit.DP_a_fast_calculate()
                Pout_a_circuit = self.Pin_a + DP_a
                Pout_a_weighted.append(Pout_a_circuit * circuit.Thermal.Vdot_ha)
            
            Pout_a = sum(Pout_a_weighted) / Vdot_ha
            DP_a = Pout_a - self.Pin_a
            
        elif self.Air_sequence in ['series_parallel','series_counter']:
            # pressure drop is the sum of pressure drops of circuits
            DP_a = 0
            for circuit in self.Circuits:
                circuit.Thermal.Tin_a = self.Tin_a
                circuit.Thermal.Pin_a = self.Pin_a
                circuit.Thermal.Win_a = self.Win_a
                DP_a += circuit.DP_a_fast_calculate()

        elif self.Air_sequence == 'sub_HX_first':
            # pressure drop is the sum of pressure drop of parallel circuits and the sub circuit
            Vdot_ha = 0
            Pout_a_weighted = []
            for circuit in self.Circuits[1:]:
                circuit.Thermal.Tin_a = self.Tin_a
                circuit.Thermal.Pin_a = self.Pin_a
                circuit.Thermal.Win_a = self.Win_a
                Vdot_ha += circuit.Thermal.Vdot_ha
                DP_a = circuit.DP_a_fast_calculate()
                Pout_a_circuit = self.Pin_a + DP_a
                Pout_a_weighted.append(Pout_a_circuit * circuit.Thermal.Vdot_ha)
            
            Pout_a = sum(Pout_a_weighted) / Vdot_ha
            DP_a = Pout_a - self.Pin_a
            self.Circuits[0].Thermal.Tin_a = self.Tin_a
            self.Circuits[0].Thermal.Pin_a = self.Pin_a
            self.Circuits[0].Thermal.Win_a = self.Win_a
            DP_a += self.Circuits[0].DP_a_fast_calculate()

        elif self.Air_sequence == 'sub_HX_last':
            # pressure drop is the sum of pressure drop of parallel circuits and the sub circuit
            Vdot_ha = 0
            Pout_a_weighted = []
            for circuit in self.Circuits[:-1]:
                circuit.Thermal.Tin_a = self.Tin_a
                circuit.Thermal.Pin_a = self.Pin_a
                circuit.Thermal.Win_a = self.Win_a
                Vdot_ha += circuit.Thermal.Vdot_ha
                DP_a = circuit.DP_a_fast_calculate()
                Pout_a_circuit = self.Pin_a + DP_a
                Pout_a_weighted.append(Pout_a_circuit * circuit.Thermal.Vdot_ha)
            
            Pout_a = sum(Pout_a_weighted) / Vdot_ha
            DP_a = Pout_a - self.Pin_a
            self.Circuits[-1].Thermal.Tin_a = self.Tin_a
            self.Circuits[-1].Thermal.Pin_a = self.Pin_a
            self.Circuits[-1].Thermal.Win_a = self.Win_a
            DP_a += self.Circuits[-1].DP_a_fast_calculate()
            
        return DP_a
    
    def solve(self):
        '''This function is used to solve the HX based on solver and model'''
        try:
            if not hasattr(self,'model'):
                self.model = 'segment'
            assert(self.model in ['segment', 'phase']),'please choose a correct model for HX'
            for Circuit in self.Circuits:
                Circuit.model = self.model
            
            assert(type(self.Accurate) == bool),'please set air property accuracy to true or false'
            if not hasattr(self,'Accurate'):
                self.Accurate = True
            for Circuit in self.Circuits:
                Circuit.Accurate = self.Accurate
                    
            if self.Fan.model == 'efficiency' or self.Fan.model == 'power':
                # assigning air flow rate to each circuit
                Vdot_a = self.Vdot_ha
                if self.Air_sequence == 'parallel':
                    for i,circuit in enumerate(self.Circuits):
                        circuit.Thermal.Vdot_ha = Vdot_a * self.Air_distribution[i]
                elif self.Air_sequence in ['series_counter','series_parallel']:
                    for i,circuit in enumerate(self.Circuits):
                        circuit.Thermal.Vdot_ha = Vdot_a
                elif self.Air_sequence == 'sub_HX_first':
                    for i,circuit in enumerate(self.Circuits[1:]):
                        circuit.Thermal.Vdot_ha = Vdot_a * self.Air_distribution[i]
                    self.Circuits[0].Thermal.Vdot_ha = Vdot_a
                elif self.Air_sequence == 'sub_HX_last':
                    for i,circuit in enumerate(self.Circuits[:-1]):
                        circuit.Thermal.Vdot_ha = Vdot_a * self.Air_distribution[i]
                    self.Circuits[-1].Thermal.Vdot_ha = Vdot_a
                
                # solving HX depending on solver
                if self.Solver.lower() == 'mdot': # mass flow rate solver is used
                    self.mdot_solver()
                elif self.Solver.lower() == 'dp': # pressure solver is used
                    self.DP_solver()
                else:
                    raise AttributeError("please choose correct solver")
                self.results_creator()
    
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
                # get initial guess from given volume flow rate value
                Vdot_a_initial = self.Vdot_ha
                global error
                error = 1
                def objective(Vdot_a):
                    global error
                    if abs(error) < 0.1:
                        return 0
                    Vdot_a = float(Vdot_a)

                    for circuit in self.Circuits:                        
                        if hasattr(circuit.Thermal,'mdot_ha'):
                            delattr(circuit.Thermal,'mdot_ha')
                        if hasattr(circuit.Thermal,'Vel_dist'):
                            delattr(circuit.Thermal,'Vel_dist')

                    self.Fan.Vdot_a = Vdot_a
                    self.Fan.Calculate()
                    if self.Air_sequence == 'parallel':
                        for i,circuit in enumerate(self.Circuits):
                            circuit.Thermal.Vdot_ha = Vdot_a * self.Air_distribution[i]
                    elif self.Air_sequence in ['series_counter','series_parallel']:
                        for i,circuit in enumerate(self.Circuits):
                            circuit.Thermal.Vdot_ha = Vdot_a
                    elif self.Air_sequence == 'sub_HX_first':
                        for i,circuit in enumerate(self.Circuits[1:]):
                            circuit.Thermal.Vdot_ha = Vdot_a * self.Air_distribution[i]
                        self.Circuits[0].Thermal.Vdot_ha = Vdot_a
                    elif self.Air_sequence == 'sub_HX_last':
                        for i,circuit in enumerate(self.Circuits[:-1]):
                            circuit.Thermal.Vdot_ha = Vdot_a * self.Air_distribution[i]
                        self.Circuits[-1].Thermal.Vdot_ha = Vdot_a
                    DP_HX = self.DP_a_fast_calculate()
                    error = DP_HX + self.Fan.DP_a
                    return error
                try:
                    Vdot_a_initial = newton(objective, Vdot_a_initial)
                except:
                    Vdot_a_initial = root(objective, Vdot_a_initial,method="hybr")['x']

                if self.Fan.Fan_position == 'before':
                    def objective(Vdot_a):
                        global error
                        if abs(error) < 0.1:
                            error = 0
                        Vdot_a = float(Vdot_a)
                        self.Vdot_ha = Vdot_a
                        for circuit in self.Circuits:                        
                            if hasattr(circuit.Thermal,'mdot_ha'):
                                delattr(circuit.Thermal,'mdot_ha')
                            if hasattr(circuit.Thermal,'Vel_dist'):
                                delattr(circuit.Thermal,'Vel_dist')
    
                        if self.Air_sequence == 'parallel':
                            for i,circuit in enumerate(self.Circuits):
                                circuit.Thermal.Vdot_ha = Vdot_a * self.Air_distribution[i]
                        elif self.Air_sequence in ['series_counter','series_parallel']:
                            self.Vdot_ha_once = True # to pass the volume flow rate from one circuit to the next using defined value in self.Vdot_ha

                        elif self.Air_sequence == 'sub_HX_first':
                            for i,circuit in enumerate(self.Circuits[1:]):
                                circuit.Thermal.Vdot_ha = Vdot_a * self.Air_distribution[i]
                            self.Circuits[0].Thermal.Vdot_ha = Vdot_a
                        elif self.Air_sequence == 'sub_HX_last':
                            for i,circuit in enumerate(self.Circuits[:-1]):
                                circuit.Thermal.Vdot_ha = Vdot_a * self.Air_distribution[i]
                            self.Circuits[-1].Thermal.Vdot_ha = Vdot_a
    
                        # solving HX depending on solver
                        if self.Solver.lower() == 'mdot': # mass flow rate solver is used
                            self.mdot_solver()
                        elif self.Solver.lower() == 'dp': # pressure solver is used
                            self.DP_solver()
                        else:
                            raise AttributeError("please choose correct solver")
                        self.results_creator()
                        self.Fan.Vdot_a = self.Results.Vdot_ha_in
                        self.Fan.Calculate()
                        error = self.Results.DP_a + self.Fan.DP_a
                        return error
                    
                    try:
                        Vdot_a = newton(objective, Vdot_a_initial,rtol=0.01)
                    except:
                        Vdot_a = root(objective, Vdot_a_initial,method="hybr",options={"xtol":0.01})['x']
                    self.Vdot_ha = Vdot_a
                    
                elif self.Fan.Fan_position == 'after':
                    error = 1
                    def objective(Vdot_a):
                        global error
                        if abs(error) < 0.1:
                            error = 0
                        Vdot_a = float(Vdot_a)
                        self.Vdot_ha = Vdot_a
                        for circuit in self.Circuits:                        
                            if hasattr(circuit.Thermal,'mdot_ha'):
                                delattr(circuit.Thermal,'mdot_ha')
                            if hasattr(circuit.Thermal,'Vel_dist'):
                                delattr(circuit.Thermal,'Vel_dist')
                        
                        if self.Air_sequence == 'parallel':
                            for i,circuit in enumerate(self.Circuits):
                                circuit.Thermal.Vdot_ha = Vdot_a * self.Air_distribution[i]
                        elif self.Air_sequence in ['series_counter','series_parallel']:
                            self.Vdot_ha_once = True

                        elif self.Air_sequence == 'sub_HX_first':
                            self.Vdot_ha_once_sub = True
                            
                        elif self.Air_sequence == 'sub_HX_last':
                            self.Vdot_ha_once_sub = True
    
                        # solving HX depending on solver
                        if self.Solver.lower() == 'mdot': # mass flow rate solver is used
                            self.mdot_solver()
                        elif self.Solver.lower() == 'dp': # pressure solver is used
                            self.DP_solver()
                        else:
                            raise AttributeError("please choose correct solver")

                        self.results_creator()
                        self.Fan.Vdot_a = self.Results.Vdot_ha_out
                        self.Fan.Calculate()                    
                        error = self.Results.DP_a + self.Fan.DP_a
                        return error
                    
                    try:
                        Vdot_a = newton(objective, Vdot_a_initial,rtol=0.01)
                    except:
                        Vdot_a = root(objective, Vdot_a_initial,method="hybr",options={"xtol":0.01})['x']
                    
                    self.Vdot_ha = Vdot_a
                    
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
        except:
            for circuit in self.Circuits:
                if hasattr(circuit,"Solver_Error"):
                    self.Solver_Error = circuit.Solver_Error
                raise
            
    def create_circuits(self,num):
        ''' function will create multiple instances of circuits class with
            the given number and append it to self.Circuits list'''
        self.Circuits = [FinTubeCircuitClass() for i in range(int(num))]
        
    def connect(self,Node_1,Node_2,Circuit_num,mass_ratio=-1,sub_circuits=1):
        ''' function is used to define a connection in the network; defined by
        (Node_1, Node_2, Circuit_Number, Mass_ratio, Number_of_sub_circuits):
            
            1- flow rate must be from node with lower index to node with higher index
            
            2- circuit number is defined as 0,1,2,....
            
            3- Mass_ratio is the ratio of mass flow rate this connection will
                take from the inlet mass flow rate of this node
            
            4- number_of_sub_circuits is used if many circuits are connected in
                parallel between these nodes with the same configuration, so 
                instead of solving them independently, this is used to save
                computational time; note that the defined mass flow rate to this
                connection will be devided equally on these circuits, and also
                air humid mass flow rate.
            '''
        if mass_ratio == -1: # if mass_ratio not given, set it to 1.0
            mass_ratio = 1.0
        else: # mass_ratio is given
            if not (0 < mass_ratio <= 1):
                raise Exception("mass_ratio must be between 0 and 1 (not 0)")
        
        if (not isinstance(Circuit_num, int)) or (not 0 <= Circuit_num <= len(self.Circuits)-1):
            raise Exception("invalid circuit number given: "+str(Circuit_num))
        
        if Circuit_num in self.Connections[:,2]:
            raise Exception("Circuit number "+str(Circuit_num)+" is connected more than once")
        
        if self.Connections[0,2] == -1: # appending the connection to the connections array
            self.Connections[0] = [min(Node_1,Node_2),max(Node_1,Node_2),Circuit_num,mass_ratio,0,0,0]
        else:
            self.Connections = np.vstack([self.Connections,[min(Node_1,Node_2),max(Node_1,Node_2),Circuit_num,mass_ratio,0,0,0]])
        
        if isinstance(sub_circuits,int) and sub_circuits > 0:
            self.Circuits[Circuit_num].Geometry.Nsubcircuits = sub_circuits
        else:
            raise Exception("Wrong sub_circuits given:",sub_circuits)
    
    def check_ratios(self):
        '''function to make sure all nodes have sum of 1.0 of mass ratios for
        connections out of them'''
        for i in set(self.Connections[:,0]):
            ratio_sum = np.sum(self.Connections[self.Connections[:,0] == i][:,3])
            if ratio_sum != 1.0:
                raise Exception("mass ratios sum out of node "+str(int(i))+" is not 1.0, it is "+str(ratio_sum))
    
    def check_connections(self):
        ''' check if all circuits are connected to 2 nodes'''
        if not len(set(self.Connections[:,2])) == len(self.Circuits):
            raise Exception("some circuits were not connected to nodes")
    
    def mdot_solver(self):
        ''' mass flow rate solver
        
        the solver will solve circuits with the defined mass ratios;
        
        pressure at nodes will be defined using the lowest outlet pressure
        of a connection to this node, assuming a throttling is used for other
        connections with higher pressure'''
        
        self.check_connections()
        self.check_ratios()
        self.nodes = np.array([[i,0,np.Inf,0] for i in set(sorted(self.Connections[:,0])+sorted(self.Connections[:,1]))]) # construct nodes array
        self.nodes[self.nodes[:,0] == min(sorted(set(self.Connections[:,0]))),[1,2,3]] = [self.mdot_r,self.Pin_r,self.mdot_r*self.hin_r] # for inlet node
        for node in self.nodes[1:]: # to assign mass flow rates of each node
            in_flow = 0
            for from_node in self.Connections[self.Connections[:,1] == node[0]]:
                in_flow += from_node[3]*self.nodes[self.nodes[:,0] == from_node[0],1]
            node[1] = in_flow
        
        # solving order, will depend on solving circuits depending of the order of outlet node number; this will make sure that no inlet node will not be undefined when solving a connection
        self.Connections = self.Connections[np.lexsort([self.Connections[:,1],self.Connections[:,0]])]
        
        # setting inlet air conditions corresponding to chosen air sequence
        if self.Air_sequence == 'parallel':
            for connection in self.Connections:
                connection[4:7] = [self.Pin_a,self.Tin_a,self.Win_a]

        elif self.Air_sequence == 'series_parallel':
            self.Connections[0,4:7] = [self.Pin_a,self.Tin_a,self.Win_a]

        elif self.Air_sequence == 'series_counter':
            pass
            
        elif self.Air_sequence == 'sub_HX_first':
            self.Connections[0,4:7] = [self.Pin_a,self.Tin_a,self.Win_a]

        elif self.Air_sequence == 'sub_HX_last':
            pass
        
        else:
            raise AttributeError("Please choose correct value for air sequence")
        
        if not (self.Air_sequence in ['series_counter',"sub_HX_last"]):
            
            if hasattr(self,'Vdot_ha_once'): # used in curve model of fan
                if self.Vdot_ha_once:
                    Vdot_ha = self.Vdot_ha
            if hasattr(self,'Vdot_ha_once_sub'): # used in curve model of fan
                if self.Vdot_ha_once_sub:
                    Vdot_ha = self.Vdot_ha
            # starting to solve each connection
            for i,(in_node,out_node,Circuit_num,mass_ratio,Pin_a,Tin_a,Win_a) in enumerate(self.Connections):
                if self.terminate:
                    self.Circuits[int(Circuit_num)].terminate = True
                # will take values from inlet node solved before
                Q_error = self.Q_error_tol
                max_iter_per_circuit = self.max_iter_per_circuit
                self.Circuits[int(Circuit_num)].AS = self.AS
                self.Circuits[int(Circuit_num)].Thermal.mdot_r = float(mass_ratio*self.nodes[self.nodes[:,0] == in_node,1])
                self.Circuits[int(Circuit_num)].Thermal.Pin_r = float(self.nodes[self.nodes[:,0] == in_node,2])
                self.Circuits[int(Circuit_num)].Thermal.hin_r = float(self.nodes[self.nodes[:,0] == in_node,3])/float(self.nodes[self.nodes[:,0] == in_node,1])                
                if hasattr(self,'Vdot_ha_once'): # used in curve model of fan
                    if self.Vdot_ha_once:
                        self.Circuits[int(Circuit_num)].Thermal.Vdot_ha = Vdot_ha
                if hasattr(self,'Vdot_ha_once_sub'): # used in curve model of fan
                    if self.Vdot_ha_once_sub:
                        self.Circuits[int(Circuit_num)].Thermal.Vdot_ha = Vdot_ha
                self.Circuits[int(Circuit_num)].Thermal.Pin_a = float(Pin_a)
                self.Circuits[int(Circuit_num)].Thermal.Tin_a = float(Tin_a)
                self.Circuits[int(Circuit_num)].Thermal.Win_a = float(Win_a)
                self.Circuits[int(Circuit_num)].calculate(Max_Q_error=Q_error,Max_num_iter=max_iter_per_circuit)
                self.nodes[self.nodes[:,0] == out_node,2] = min(self.nodes[self.nodes[:,0] == out_node,2],self.Circuits[int(Circuit_num)].Results.Pout_r)
                self.nodes[self.nodes[:,0] == out_node,3] += self.Circuits[int(Circuit_num)].Thermal.mdot_r*self.Circuits[int(Circuit_num)].Results.hout_r # outlet energy, to account for mixing easily
                if self.Air_sequence == 'series_parallel':
                    if not i == (len(self.Connections) - 1):
                        Pin_a = self.Circuits[int(Circuit_num)].Results.Pout_a
                        Tin_a = self.Circuits[int(Circuit_num)].Results.Tout_a
                        Win_a = self.Circuits[int(Circuit_num)].Results.Wout_a
                        self.Connections[i + 1,4:7] = [Pin_a, Tin_a, Win_a]
                elif self.Air_sequence == 'sub_HX_first':
                    if i == 0:
                        for connection in self.Connections[1:]:
                            Pin_a = self.Circuits[int(Circuit_num)].Results.Pout_a
                            Tin_a = self.Circuits[int(Circuit_num)].Results.Tout_a
                            Win_a = self.Circuits[int(Circuit_num)].Results.Wout_a                            
                            connection[4:7] = [Pin_a,Tin_a,Win_a]
                if hasattr(self,'Vdot_ha_once'): # used in curve model of fan
                    if self.Vdot_ha_once:
                        Vdot_ha = self.Circuits[int(Circuit_num)].Results.Vdot_ha_out
                elif hasattr(self,'Vdot_ha_once_sub'): # used in curve model of fan
                    if self.Vdot_ha_once_sub:
                        Vdot_a = self.Circuits[int(Circuit_num)].Results.Vdot_ha_out
                        for k,circuit in enumerate(self.Circuits[1:]):
                            circuit.Thermal.Vdot_ha = Vdot_a * self.Air_distribution[k]
                        self.Vdot_ha_once_sub = False

        elif self.Air_sequence == 'series_counter':
            for connection in self.Connections:
                connection[4] = self.Pin_a
                connection[6] = self.Win_a

            distribution_T = np.zeros(len(self.Connections))
            distribution_P = np.zeros(len(self.Connections)) + self.Pin_a
            distribution_W = np.zeros(len(self.Connections)) + self.Win_a

            Tin_a = self.Tin_a
            AS = self.AS
            AS.update(CP.HmassP_INPUTS, self.hin_r, self.Pin_r)
            hin_r = self.hin_r
            Tin_r = AS.T()
            epsilon_total = 0.7
            Tout_a = epsilon_total * (Tin_r - Tin_a) + Tin_a
            epsilon = epsilon_total / len(self.Connections)
            for i,connection in enumerate(self.Connections):
                
                Tin_a = (Tout_a - epsilon * Tin_r) / (1 - epsilon)
                distribution_T[i] = Tin_a
                Circuit_num = int(connection[2])
                self.Circuits[int(Circuit_num)].Thermal.Tin_a = self.Tin_a
                self.Circuits[int(Circuit_num)].Thermal.Pin_a = self.Pin_a
                self.Circuits[int(Circuit_num)].Thermal.Win_a = self.Win_a
                pseudo = self.Circuits[int(Circuit_num)].mdot_da_array_creator(1)
                mdot_da = self.Circuits[int(Circuit_num)].Thermal.mdot_ha / (1 + self.Win_a)
                Q = mdot_da * (Tout_a - Tin_a)
                hout_r = hin_r - Q / self.mdot_r
                AS.update(CP.HmassP_INPUTS, hout_r, self.Pin_r)
                Tout_r = AS.T()
                hin_r = hout_r
                Tin_r = Tout_r
                Tout_a = Tin_a
            distribution_T[-1] = self.Tin_a            

            for i,connection in enumerate(self.Connections):
                connection[5] = distribution_T[i]
            j = 0
            Q_total_old = 0
            Q_total = 0
            error_total_Q = 100
            while error_total_Q > self.Q_error_tol and j <= 15:
                self.nodes = np.array([[i,0,np.Inf,0] for i in set(sorted(self.Connections[:,0])+sorted(self.Connections[:,1]))]) # construct nodes array
                self.nodes[self.nodes[:,0] == min(sorted(set(self.Connections[:,0]))),[1,2,3]] = [self.mdot_r,self.Pin_r,self.mdot_r*self.hin_r] # for inlet node
                for node in self.nodes[1:]: # to assign mass flow rates of each node
                    in_flow = 0
                    for from_node in self.Connections[self.Connections[:,1] == node[0]]:
                        in_flow += from_node[3]*self.nodes[self.nodes[:,0] == from_node[0],1]
                    node[1] = in_flow

                for i,connection in enumerate(self.Connections):
                    connection[5] = distribution_T[i]
                    connection[4] = distribution_P[i]
                    connection[6] = distribution_W[i]
                
                Q_total = 0
                if hasattr(self,'Vdot_ha_once'):
                    if self.Vdot_ha_once:
                        Vdot_ha = self.Vdot_ha
                for i,(in_node,out_node,Circuit_num,mass_ratio,Pin_a,Tin_a,Win_a) in enumerate(self.Connections):
                    if self.terminate:
                        self.Circuits[int(Circuit_num)].terminate = True
                    # will take values from inlet node solved before
                    Q_error = self.Q_error_tol
                    max_iter_per_circuit = self.max_iter_per_circuit
                    self.Circuits[int(Circuit_num)].AS = self.AS
                    self.Circuits[int(Circuit_num)].Thermal.mdot_r = float(mass_ratio*self.nodes[self.nodes[:,0] == in_node,1])
                    self.Circuits[int(Circuit_num)].Thermal.Pin_r = float(self.nodes[self.nodes[:,0] == in_node,2])
                    self.Circuits[int(Circuit_num)].Thermal.hin_r = float(self.nodes[self.nodes[:,0] == in_node,3])/float(self.nodes[self.nodes[:,0] == in_node,1])
                    self.Circuits[int(Circuit_num)].Thermal.Pin_a = float(Pin_a)
                    self.Circuits[int(Circuit_num)].Thermal.Tin_a = float(Tin_a)
                    self.Circuits[int(Circuit_num)].Thermal.Win_a = float(Win_a)
                    if hasattr(self,'Vdot_ha_once'):
                        if self.Vdot_ha_once:
                            self.Circuits[int(Circuit_num)].Thermal.Vdot_ha = Vdot_ha
                    
                    pseudo = self.Circuits[int(Circuit_num)].mdot_da_array_creator(1)
                        
                    self.Circuits[int(Circuit_num)].calculate(Max_Q_error=Q_error,Max_num_iter=max_iter_per_circuit)
                    self.nodes[self.nodes[:,0] == out_node,2] = min(self.nodes[self.nodes[:,0] == out_node,2],self.Circuits[int(Circuit_num)].Results.Pout_r)
                    self.nodes[self.nodes[:,0] == out_node,3] += self.Circuits[int(Circuit_num)].Thermal.mdot_r*self.Circuits[int(Circuit_num)].Results.hout_r # outlet energy, to account for mixing easily
                    Q_total += self.Circuits[int(Circuit_num)].Results.Q
                    if not (i == 0):
                        distribution_T[i-1] = self.Circuits[int(Circuit_num)].Results.Tout_a
                        distribution_P[i-1] = self.Circuits[int(Circuit_num)].Results.Pout_a
                        distribution_W[i-1] = self.Circuits[int(Circuit_num)].Results.Wout_a
                    if hasattr(self,'Vdot_ha_once'):
                        if self.Vdot_ha_once:
                            Vdot_ha = self.Circuits[int(Circuit_num)].Results.Vdot_ha_out
                error_total_Q = abs(Q_total - Q_total_old) / abs(Q_total)
                Q_total_old = Q_total
                j += 1

        elif self.Air_sequence == 'sub_HX_last':
            for connection in self.Connections:
                connection[4] = self.Pin_a
                connection[6] = self.Win_a
            
            distribution_T = np.zeros(len(self.Connections))
            distribution_P = np.zeros(len(self.Connections)) + self.Pin_a
            distribution_W = np.zeros(len(self.Connections)) + self.Win_a

            Tin_a = self.Tin_a
            AS = self.AS
            AS.update(CP.HmassP_INPUTS, self.hin_r, self.Pin_r)
            hin_r = self.hin_r
            Tin_r = AS.T()
            epsilon_total = 0.7
            Tout_a = epsilon_total * (Tin_r - Tin_a) + Tin_a
            epsilon = epsilon_total / len(self.Connections)
            
            Q = 0
            Tin_a_list = []
            mdot_a_list = []
            # for parallel circuits
            for i,connection in enumerate(self.Connections[:-1]):
                Tin_a = (Tout_a - epsilon * Tin_r) / (1 - epsilon)
                distribution_T[i] = Tin_a
                Circuit_num = int(connection[2])
                self.Circuits[int(Circuit_num)].Thermal.Tin_a = self.Tin_a
                self.Circuits[int(Circuit_num)].Thermal.Pin_a = self.Pin_a
                self.Circuits[int(Circuit_num)].Thermal.Win_a = self.Win_a
                        
            self.Circuits[-1].Thermal.Tin_a = self.Tin_a
            self.Circuits[-1].Thermal.Pin_a = self.Pin_a
            self.Circuits[-1].Thermal.Win_a = self.Win_a
                
            distribution_T[-1] = self.Tin_a

            for i,connection in enumerate(self.Connections):
                connection[5] = distribution_T[i]
                
            j = 0
            Q_total_old = 0
            Q_total = 0
            error_total_Q = 100
            while error_total_Q > self.Q_error_tol and j <= 15:
                self.nodes = np.array([[i,0,np.Inf,0] for i in set(sorted(self.Connections[:,0])+sorted(self.Connections[:,1]))]) # construct nodes array
                self.nodes[self.nodes[:,0] == min(sorted(set(self.Connections[:,0]))),[1,2,3]] = [self.mdot_r,self.Pin_r,self.mdot_r*self.hin_r] # for inlet node
                for node in self.nodes[1:]: # to assign mass flow rates of each node
                    in_flow = 0
                    for from_node in self.Connections[self.Connections[:,1] == node[0]]:
                        in_flow += from_node[3]*self.nodes[self.nodes[:,0] == from_node[0],1]
                    node[1] = in_flow

                for i,connection in enumerate(self.Connections):
                    connection[5] = distribution_T[i]
                    connection[4] = distribution_P[i]
                    connection[6] = distribution_W[i]
                
                Q_total = 0
                if hasattr(self,'Vdot_ha_once'):
                    if self.Vdot_ha_once:
                        Vdot_ha = self.Vdot_ha
                elif hasattr(self,'Vdot_ha_once_sub'): # used in curve model of fan
                    if self.Vdot_ha_once_sub:
                        Vdot_ha = self.Vdot_ha

                for i,(in_node,out_node,Circuit_num,mass_ratio,Pin_a,Tin_a,Win_a) in enumerate(self.Connections):
                    if self.terminate:
                        self.Circuits[int(Circuit_num)].terminate = True
                    # will take values from inlet node solved before
                    Q_error = self.Q_error_tol
                    max_iter_per_circuit = self.max_iter_per_circuit
                    self.Circuits[int(Circuit_num)].AS = self.AS
                    self.Circuits[int(Circuit_num)].Thermal.mdot_r = float(mass_ratio*self.nodes[self.nodes[:,0] == in_node,1])
                    self.Circuits[int(Circuit_num)].Thermal.Pin_r = float(self.nodes[self.nodes[:,0] == in_node,2])
                    self.Circuits[int(Circuit_num)].Thermal.hin_r = float(self.nodes[self.nodes[:,0] == in_node,3])/float(self.nodes[self.nodes[:,0] == in_node,1])
                    self.Circuits[int(Circuit_num)].Thermal.Pin_a = float(Pin_a)
                    self.Circuits[int(Circuit_num)].Thermal.Tin_a = float(Tin_a)
                    self.Circuits[int(Circuit_num)].Thermal.Win_a = float(Win_a)
                    if hasattr(self,'Vdot_ha_once'):
                        if self.Vdot_ha_once:
                            self.Circuits[int(Circuit_num)].Thermal.Vdot_ha = Vdot_ha
                    elif hasattr(self,'Vdot_ha_once_sub'): # used in curve model of fan
                        if self.Vdot_ha_once_sub:
                            self.Circuits[int(Circuit_num)].Thermal.Vdot_ha = Vdot_ha
                    self.Circuits[int(Circuit_num)].calculate(Max_Q_error=Q_error,Max_num_iter=max_iter_per_circuit)
                    self.nodes[self.nodes[:,0] == out_node,2] = min(self.nodes[self.nodes[:,0] == out_node,2],self.Circuits[int(Circuit_num)].Results.Pout_r)
                    self.nodes[self.nodes[:,0] == out_node,3] += self.Circuits[int(Circuit_num)].Thermal.mdot_r*self.Circuits[int(Circuit_num)].Results.hout_r # outlet energy, to account for mixing easily
                    Q_total += self.Circuits[int(Circuit_num)].Results.Q
                    if i == len(self.Connections) - 1:
                        distribution_T[:-1] = self.Circuits[int(Circuit_num)].Results.Tout_a
                        distribution_P[:-1] = self.Circuits[int(Circuit_num)].Results.Pout_a
                        distribution_W[:-1] = self.Circuits[int(Circuit_num)].Results.Wout_a
                    if hasattr(self,'Vdot_ha_once'):
                        if self.Vdot_ha_once:
                            Vdot_ha = self.Circuits[int(Circuit_num)].Results.Vdot_ha_out
                    elif hasattr(self,'Vdot_ha_once_sub'): # used in curve model of fan
                        if self.Vdot_ha_once_sub:
                            Vdot_a = self.Circuits[int(Circuit_num)].Results.Vdot_ha_out
                            for k,circuit in enumerate(self.Circuits[1:]):
                                circuit.Thermal.Vdot_ha = Vdot_a * self.Air_distribution[k]
                            self.Vdot_ha_once_sub = False
                error_total_Q = abs(Q_total - Q_total_old) / abs(Q_total)
                Q_total_old = Q_total
                j += 1

    def create_ratios(self):
        '''function used to create initial mass ratios for the pressure solver
        assumning equal between parallel connections'''
        
        ratios_list = np.zeros([len(set(self.Connections[:,0])),2])
        for i,node in enumerate(set(self.Connections[:,0])):
            ratio = 1/sum(self.Connections[:,0] == node)
            ratios_list[i] = [node, ratio]
        for i in range(len(self.Connections)):
            self.Connections[i,3] = ratios_list[ratios_list[:,0] == self.Connections[i,0],1] 
    
    def DP_solver(self):
        '''pressure solver; will solve for outlet pressure of all connection to
        a node to be the same (with up to 1 Pa error)
        
        sequence of solution:
            1- solve for mass ratios that satisfy zero residuals for constant 
                f and specific volume => get ratios_0
            2- solve once the HEX with ratios_0 to get state at all nodes
            3- solve for mass ratios that satisfy zero residuals for f and 
                specific volume calculated from average inlet and outlet of 
                each circuit => get ratios_1
            4- solve with accurate solver for mass ratios that satisfy zero 
                residuals but with 2 segments per tube and FinsOnce set to True
                and high Q_error and Pressure_error => get ratios_2
            5- solve with accurate solver for mass ratios that satisfy zero 
                residuals but with user setting for Nsegments, FinsOnce, T_error
                and Pressure_error
        
        '''
        
        self.check_connections()
        mass_ratios = self.Connections[:,3].copy()
        
        # these are the circuits that has a mass ratio that can be varied
        variable_circuits_list= []
        for in_node in set(self.Connections[:,0]):
            if sum(self.Connections[:,0] == in_node) > 1: # multiple connections has the same inlet node
                circuits = self.Connections[self.Connections[:,0] == in_node,2]
                variable_circuits_list.extend(circuits)
        
        # I could have combined both loops, but for clarity of analyzing code, it is separated
        var_circuits_array = np.zeros([len(variable_circuits_list),3])
        for i,Circuit_num in enumerate(variable_circuits_list):
            Circuit_num = int(Circuit_num)
            var_circuits_array[i] = [self.Connections[self.Connections[:,2] == Circuit_num,0],self.Connections[self.Connections[:,2] == Circuit_num,1],Circuit_num]

        # number of independent variables of solution
        num_of_vars = len(var_circuits_array[:,0])-len(set(var_circuits_array[:,0]))
        
        if num_of_vars == 0: # no need for dp solver, will use mdot solver instead
            # for i in range(len(self.Circuits)):
            #     self.Circuits[i].Thermal.Nsegments = Nsegments[i]
            #     self.Circuits[i].Thermal.FinsOnce = Fins_Once[i]
            self.mdot_solver()
        else:
            try:
                self.check_ratios() # if user enters a guessed mass ratios, it will be used
            except:
                self.create_ratios() # if not, we will create ours; equal ratios for each inlet
            
            # an array for mass ratios and circuit number
            var_ratios = np.zeros([num_of_vars,2])
            num = 0
            
            for i in set(var_circuits_array[:,0]):
                list_of_circuits = var_circuits_array[var_circuits_array[:,0] == i][:,2]
                if len(list_of_circuits) == 2:
                    var_ratios[num,1] = list_of_circuits[0]
                    num += 1
                else:
                    for circuit in list_of_circuits[:-1]:
                        var_ratios[num,1] = circuit
                        num += 1
            
            for i in range(len(var_ratios)):
                var_ratios[i,0] = self.Connections[self.Connections[:,2] == var_ratios[i,1],3]
            # this is the objective function to be used to solve the circuit using variable mass ratios
            
            def objective(var_ratios,var_circuits,all_var_circuits):
                if isinstance(var_circuits,float):
                    var_circuits = [var_circuits]
                for ratio,circuit in zip(var_ratios,var_circuits): # setting variable ratios
                    self.Connections[self.Connections[:,2] == circuit,3] = ratio
                for connection in self.Connections:
                    if (not (connection[2] in var_circuits)) and (connection[3] != 1): # variable connection but not takes as variable mass ratio
                        # for 3 parallel connections, 2 will have independant mass ratios, the 3rd will have the rest up to 1.0
                        ratio = 1 - (sum(self.Connections[self.Connections[:,0] == connection[0],3]) - connection[3])
                        self.Connections[self.Connections[:,2] == connection[2],3] = ratio
                return self.DP_solve_with_ratios_simple(all_var_circuits)
            
            def constrainedFunction(x, minIncr=0.001):
                ''' used to prevent overshooting in the prediction of mass 
                flow rates higher than 1.0 or lower than 0.0; the boundaries 
                are not set to 0.0 and 1.0 as that will cause a error in the 0
                mass flow rate connection'''
                
                x = np.asarray(x)
                lower = np.asarray(0.01)
                upper = np.asarray(0.99)
                xBorder = np.where(x<lower, lower, x)
                xBorder = np.where(x>upper, upper, xBorder)
                fBorder = objective(xBorder,var_ratios[:,1],var_circuits_array[:,2])
                distFromBorder = (np.sum(np.where(x<lower, lower-x, 0.))
                                +np.sum(np.where(x>upper, x-upper, 0.)))
                Result = (fBorder + (fBorder
                                  +np.where(fBorder>0, minIncr, -minIncr))*distFromBorder)
                # in case pressure residual is less than 1 Pa, just return 0 to prevent further solving
                if max(Result) < 0.001:
                    Result = np.zeros(len(Result))
                return Result
            try: # this is a method which is not stable, but fast
                ratios_0 = least_squares(constrainedFunction,var_ratios[:,0],method='dogbox')
                ratios_0 = np.array(ratios_0['x'])
            except: # this is robust method, but relatively slow
                ratios_0 = np.array(newton(constrainedFunction,var_ratios[:,0]))
            
            def objective(var_ratios,var_circuits,all_var_circuits,Q_error_input,max_num_iter):
                if isinstance(var_circuits,float):
                    var_circuits = [var_circuits]
                for ratio,circuit in zip(var_ratios,var_circuits): # setting variable ratios
                    self.Connections[self.Connections[:,2] == circuit,3] = ratio
                for connection in self.Connections:
                    if (not (connection[2] in var_circuits)) and (connection[3] != 1): # variable connection but not takes as variable mass ratio
                        # for 3 parallel connections, 2 will have independant mass ratios, the 3rd will have the rest up to 1.0
                        ratio = 1 - (sum(self.Connections[self.Connections[:,0] == connection[0],3]) - connection[3])
                        self.Connections[self.Connections[:,2] == connection[2],3] = ratio
                return self.DP_solve_with_ratios(all_var_circuits,Q_error_input,max_num_iter)
            
            def constrainedFunction(x, minIncr=0.001):
                ''' used to prevent overshooting in the prediction of mass 
                flow rates higher than 1.0 or lower than 0.0; the boundaries 
                are not set to 0.0 and 1.0 as that will cause a error in the 0
                mass flow rate connection'''
                
                if self.DP_converged == True:
                    return np.zeros(len(x))
                
                x = np.asarray(x)
                lower = np.asarray(0.01)
                upper = np.asarray(0.99)
                xBorder = np.where(x<lower, lower, x)
                xBorder = np.where(x>upper, upper, xBorder)
                fBorder = objective(xBorder,var_ratios[:,1],var_circuits_array[:,2],Q_error_input_user,max_num_iter_user)
                distFromBorder = (np.sum(np.where(x<lower, lower-x, 0.))
                                +np.sum(np.where(x>upper, x-upper, 0.)))
                Result = (fBorder + (fBorder
                                  +np.where(fBorder>0, minIncr, -minIncr))*distFromBorder)
                # in case pressure residual is less than 1 Pa, just return 0 to prevent further solving
                if max(Result) < Pressure_error:
                    Result = np.zeros(len(Result))
                    self.DP_converged = True
                return Result
                        
            self.DP_converged = False
            Q_error_input_user = self.Q_error_tol
            Pressure_error = self.Ref_Pressure_error_tol
            max_num_iter_user = self.max_iter_per_circuit
            try: # using the robust solver first as calculation this time might take long time and we can't risk it
                ratios = least_squares(constrainedFunction,ratios_0,method='dogbox',jac='2-point')
            except: # very unlikely that this line will be used, but if so, this is a last trial to solve
                ratios = newton(constrainedFunction,ratios_0,maxiter=10)
        
    def DP_solve_with_ratios(self,var_circuits,Q_error_circuit,iter_max):
        '''excute solution with the defined ratios, var_circuits is used to produce
        residuals'''
        # construct nodes array
        self.nodes = np.array([[i,0,np.Inf,0] for i in set(sorted(self.Connections[:,0])+sorted(self.Connections[:,1]))])
        self.nodes[self.nodes[:,0] == min(set(sorted(self.Connections[:,0])+sorted(self.Connections[:,1]))),[1,2,3]] = [self.mdot_r,self.Pin_r,self.mdot_r*self.hin_r]
        for node in self.nodes[1:]:
            in_flow = 0
            for from_node in self.Connections[self.Connections[:,1] == node[0]]:
                in_flow += from_node[3]*self.nodes[self.nodes[:,0] == from_node[0],1]
            node[1] = in_flow
        # correct order of solution, to make sure a connection will always have a solved inlet node
        self.Connections = self.Connections[np.lexsort([self.Connections[:,1],self.Connections[:,0]])]
        for in_node,out_node,Circuit_num,mass_ratio,Pin_a,Tin_a,Win_a in self.Connections:
            if self.terminate:
                self.Circuits[int(Circuit_num)].terminate = True
            # assign inlet conditions from the node
            self.Circuits[int(Circuit_num)].AS = self.AS
            self.Circuits[int(Circuit_num)].Thermal.mdot_r = float(mass_ratio*self.nodes[self.nodes[:,0] == in_node,1])
            self.Circuits[int(Circuit_num)].Thermal.Pin_r = float(self.nodes[self.nodes[:,0] == in_node,2])
            self.Circuits[int(Circuit_num)].Thermal.hin_r = float(self.nodes[self.nodes[:,0] == in_node,3])/float(self.nodes[self.nodes[:,0] == in_node,1])
            self.Circuits[int(Circuit_num)].Thermal.Pin_a = float(Pin_a)
            self.Circuits[int(Circuit_num)].Thermal.Tin_a = float(Tin_a)
            self.Circuits[int(Circuit_num)].Thermal.Win_a = float(Win_a)
            self.Circuits[int(Circuit_num)].calculate(Max_Q_error=Q_error_circuit,Max_num_iter=iter_max)
            self.nodes[self.nodes[:,0] == out_node,2] = min(self.nodes[self.nodes[:,0] == out_node,2],self.Circuits[int(Circuit_num)].Results.Pout_r)
            self.nodes[self.nodes[:,0] == out_node,3] += self.Circuits[int(Circuit_num)].Thermal.mdot_r*self.Circuits[int(Circuit_num)].Results.hout_r
        
        #residuals array
        resid = np.zeros([len(self.Connections),2])
        for i,(in_node,out_node,Circuit_num) in enumerate(self.Connections[:,[0,1,2]]):
            resid[i] = [self.Circuits[int(Circuit_num)].Results.Pout_r - self.nodes[self.nodes[:,0] == out_node,2],out_node]
        list_of_out_nodes_used = []
        shorted_resid = []
        
        # this is to produced shorted list of residuals equal to the number of variables used
        for i in var_circuits:
            out_node = self.Connections[self.Connections[:,2] == i,1]
            if not out_node in list_of_out_nodes_used:
                # this is to make sure of the order of the residuals to be consistant with the order of the variables
                resid_of_out_node = resid[resid[:,1] == out_node,0]
                resid_part = resid_of_out_node[resid_of_out_node.argsort()[::-1]][:-1]
                shorted_resid.extend(resid_part)
                list_of_out_nodes_used.append(out_node)
        shorted_resid = np.array(shorted_resid)
        return shorted_resid

    def DP_solve_with_ratios_simple(self,var_circuits):
        '''excute solution with the defined ratios, var_circuits is used to produce
            residuals, doesn't calculate actual DP, just a simple form of G^2*L/D'''
        # construct nodes array
        self.nodes = np.array([[i,0,np.Inf,0] for i in set(sorted(self.Connections[:,0])+sorted(self.Connections[:,1]))])
        self.nodes[self.nodes[:,0] == min(set(sorted(self.Connections[:,0])+sorted(self.Connections[:,1]))),[1,2,3]] = [self.mdot_r,self.Pin_r,self.mdot_r*self.hin_r]
        for node in self.nodes[1:]:
            in_flow = 0
            for from_node in self.Connections[self.Connections[:,1] == node[0]]:
                in_flow += from_node[3]*self.nodes[self.nodes[:,0] == from_node[0],1]
            node[1] = in_flow
        # correct order of solution, to make sure a connection will always have a solved inlet node
        self.Connections = self.Connections[np.lexsort([self.Connections[:,1],self.Connections[:,0]])]
        f = 0.04
        v_r = 0.1
        for in_node,out_node,Circuit_num,mass_ratio,Pin_a,Tin_a,Win_a in self.Connections:
            # assign inlet conditions from the node
            self.Circuits[int(Circuit_num)].geometry()
            Dh = self.Circuits[int(Circuit_num)].Geometry.Dh
            G = float(mass_ratio*self.nodes[self.nodes[:,0] == in_node,1])/self.Circuits[int(Circuit_num)].Geometry.A_CS
            L = self.Circuits[int(Circuit_num)].Geometry.Ltube * self.Circuits[int(Circuit_num)].Geometry.Ntubes_per_bank_per_subcircuit * self.Circuits[int(Circuit_num)].Geometry.Nbank
            DP=-f*v_r/2*G**2/(2*Dh)*L            
            Pin_r = float(self.nodes[self.nodes[:,0] == in_node,2])
            self.Circuits[int(Circuit_num)].Results = ValuesClass()
            self.Circuits[int(Circuit_num)].Results.Pout_r = Pin_r + DP
            self.nodes[self.nodes[:,0] == out_node,2] = min(Pin_r + DP,self.nodes[self.nodes[:,0] == out_node,2])
            self.nodes[self.nodes[:,0] == out_node,3] += float(mass_ratio*self.nodes[self.nodes[:,0] == in_node,1])*float(self.nodes[self.nodes[:,0] == in_node,3])/float(self.nodes[self.nodes[:,0] == in_node,1])
        #residuals array
        resid = np.zeros([len(self.Connections),2])
        for i,(in_node,out_node,Circuit_num) in enumerate(self.Connections[:,[0,1,2]]):
            resid[i] = [self.Circuits[int(Circuit_num)].Results.Pout_r - self.nodes[self.nodes[:,0] == out_node,2],out_node]
        list_of_out_nodes_used = []
        shorted_resid = []
        # this is to produced shorted list of residuals equal to the number of variables used
        for i in var_circuits:
            out_node = self.Connections[self.Connections[:,2] == i,1]
            if not out_node in list_of_out_nodes_used:
                # this is to make sure of the order of the residuals to be consistant with the order of the variables
                resid_of_out_node = resid[resid[:,1] == out_node,0]
                resid_part = resid_of_out_node[resid_of_out_node.argsort()[::-1]][:-1]
                shorted_resid.extend(resid_part)
                list_of_out_nodes_used.append(out_node)
        shorted_resid = np.array(shorted_resid)
        return shorted_resid
        
if __name__=='__main__':    
    def HEX1():
        global HEX
        HEX = FinTubeHEXClass()
        HEX.Accurate = True
        HEX.create_circuits(1)
        HEX.connect(0,1,0,1.0,5)
        HEX.mdot_r = 0.03779765654529419
        HEX.Pin_r = 25*101325
        HEX.Tin_a = 308.15
        HEX.Pin_a = 100667
        from CoolProp.CoolProp import HAPropsSI
        Win_a = HAPropsSI('W','P',HEX.Pin_a,'T',HEX.Tin_a,'R',0.4)
        HEX.Win_a = Win_a
        HEX.Air_sequence = 'parallel'
        # HEX.Air_sequence = 'series_parallel'
        # HEX.Air_sequence = 'series_counter'
        if HEX.Air_sequence == 'parallel':
            Air_distribution = [1 / len(HEX.Circuits) for _ in range(len(HEX.Circuits))]
            HEX.Air_distribution = Air_distribution
        HEX.model = 'phase'
        HEX.Q_error_tol = 0.01
        HEX.max_iter_per_circuit = 20
        HEX.Ref_Pressure_error_tol = 100
        Ref = 'R22'
        Backend = 'HEOS'
        AS = CP.AbstractState(Backend, Ref)
        HEX.AS = AS
        SH_target = 7
        AS.update(CP.PQ_INPUTS,HEX.Pin_r,1.0)
        T = AS.T()
        AS.update(CP.PT_INPUTS,HEX.Pin_r,T+SH_target)
        HEX.hin_r = AS.hmass()
        HEX.Vdot_ha = 1.0
        for i in range(len(HEX.Circuits)):
            HEX.Circuits[i].Geometry.Ntubes_per_bank_per_subcircuit=4       #number of tubes per bank per circuit
            HEX.Circuits[i].Geometry.Nbank = 2                             #number of banks or rows
            HEX.Circuits[i].Geometry.OD = 0.0070104
            HEX.Circuits[i].Geometry.ID = 0.0062992
            HEX.Circuits[i].Geometry.Staggering = 'aAa'
            HEX.Circuits[i].Geometry.Tubes_type='Smooth'
            HEX.Circuits[i].Geometry.Pl = 0.022225               #distance between center of tubes in flow direction                                                
            HEX.Circuits[i].Geometry.Pt = 0.0254                #distance between center of tubes orthogonal to flow direction
            # HEX.Circuits[i].Geometry.Connections = [16,17,18,19,20,15,14,13,12,11,6,7,8,9,10,5,4,3,2,1]
            HEX.Circuits[i].Geometry.Connections = [5,6,7,8,4,3,2,1]
            HEX.Circuits[i].Geometry.FarBendRadius = 0.0127
            HEX.Circuits[i].Geometry.e_D = 0
            HEX.Circuits[i].Geometry.FPI = 15.83333333333
            HEX.Circuits[i].Geometry.FinType = 'Plain'
            HEX.Circuits[i].Geometry.Fin_t = 0.0001400048
            HEX.Circuits[i].Geometry.Fin_Pd = 0.001
            HEX.Circuits[i].Geometry.Fin_xf = 0.001
            
            HEX.Circuits[i].Thermal.Nsegments = 20
            HEX.Circuits[i].Thermal.kw = 338.99713
            HEX.Circuits[i].Thermal.FinsOnce = True
            HEX.Circuits[i].Thermal.k_fin = 221.90475547848

            HEX.Circuits[i].Thermal.DP_a_wet_on = False
            HEX.Circuits[i].Thermal.h_a_wet_on = False

        HEX.Fan.model = 'curve'
        a = 17.04447135
        b = 2135.389026
        c = -16099.01934
        d = 48475.41375
        HEX.Fan.power_curve = str(a)+'+('+str(b)+')*X+('+str(c)+')*X**2+('+str(d)+')*X**3'
        a = 16.13
        b = 8.69
        c = -11.85
        d = -12.82
        HEX.Fan.DP_curve = str(a)+'+('+str(b)+')*X+('+str(c)+')*X**2+('+str(d)+')*X**3'

        # HEX.Fan.model = 'efficiency'
        # HEX.Fan.efficiency = '0.5'
    
        HEX.Fan.Fan_position = 'after'
        
        if HEX.Fan.model == 'curve':
            HEX.Vdot_ha = 0.7
        
        HEX.Circuits[0].Geometry.Ltube=0.8128                        #one tube length
        import time
        T1 = time.time()
        HEX.Solver = 'mdot'
        for i in range(10):
            print("trial: ",i)
            HEX.solve()
            print("---------------")
        T2 = time.time()
        print("total time:",T2-T1)

    def HEX2():
        global HEX
        HEX = FinTubeHEXClass()
        HEX.Accurate = True
        HEX.create_circuits(4)
        HEX.connect(0,1,0,1.0,1)
        HEX.connect(1,2,1,1.0,3)
        HEX.connect(2,3,2,1.0,6)
        HEX.connect(3,4,3,1.0,10)
        HEX.mdot_r = 0.07
        HEX.Pin_r = 7*101325
        HEX.Tin_a = 295
        HEX.Pin_a = 101325
        from CoolProp.CoolProp import HAPropsSI
        Win_a = HAPropsSI('W','P',HEX.Pin_a,'T',HEX.Tin_a,'R',0.5)
        HEX.Win_a = Win_a
        # HEX.Air_sequence = 'parallel'
        # HEX.Air_sequence = 'series_parallel'
        # HEX.Air_sequence = 'series_counter'
        HEX.Air_sequence = 'sub_HX_first'
        # HEX.Air_sequence = 'sub_HX_last'
        if HEX.Air_sequence in ['sub_HX_first','sub_HX_last']:
            Air_distribution = [1 / (len(HEX.Circuits)-1) for _ in range(len(HEX.Circuits)-1)]
            HEX.Air_distribution = Air_distribution
        elif HEX.Air_sequence in ['parallel']:
            Air_distribution = [1 / len(HEX.Circuits) for _ in range(len(HEX.Circuits))]
            HEX.Air_distribution = Air_distribution
        HEX.model = 'segment'
        HEX.Q_error_tol = 0.01
        HEX.max_iter_per_circuit = 20
        HEX.Ref_Pressure_error_tol = 100
        Ref = 'R22'
        Backend = 'HEOS'
        AS = CP.AbstractState(Backend, Ref)
        HEX.AS = AS
        AS.update(CP.PQ_INPUTS,HEX.Pin_r,0.1)
        HEX.hin_r = AS.hmass()
        
        for i in range(1,len(HEX.Circuits)):
            HEX.Circuits[i].Geometry.Ntubes_per_bank_per_subcircuit=5       #number of tubes per bank per circuit
            HEX.Circuits[i].Geometry.Nbank = 2                             #number of banks or rows
            HEX.Circuits[i].Geometry.OD = 0.012
            HEX.Circuits[i].Geometry.ID = 0.011
            HEX.Circuits[i].Geometry.Staggering = 'aAa'
            HEX.Circuits[i].Geometry.Tubes_type='Smooth'
            HEX.Circuits[i].Geometry.Pl = 0.019               #distance between center of tubes in flow direction                                                
            HEX.Circuits[i].Geometry.Pt = 0.019                #distance between center of tubes orthogonal to flow direction
            # HEX.Circuits[i].Geometry.Connections = [16,17,18,19,20,15,14,13,12,11,6,7,8,9,10,5,4,3,2,1]
            HEX.Circuits[i].Geometry.Connections = [6,7,8,9,10,5,4,3,2,1]
            HEX.Circuits[i].Geometry.FarBendRadius = 0.01
            HEX.Circuits[i].Geometry.e_D = 0
            HEX.Circuits[i].Geometry.FPI = 18
            HEX.Circuits[i].Geometry.FinType = 'WavyLouvered'
            HEX.Circuits[i].Geometry.Fin_t = 0.0001
            HEX.Circuits[i].Geometry.Fin_Pd = 0.001
            HEX.Circuits[i].Geometry.Fin_xf = 0.001
            
            HEX.Circuits[i].Thermal.Nsegments = 20
            HEX.Circuits[i].Thermal.kw = 385
            HEX.Circuits[i].Thermal.FinsOnce = True
            HEX.Circuits[i].Thermal.k_fin = 210

            HEX.Circuits[i].Thermal.DP_a_wet_on = False
            HEX.Circuits[i].Thermal.h_a_wet_on = False
            HEX.Circuits[i].Geometry.Ltube=0.9                        #one tube length

        HEX.Circuits[0].Geometry.Ntubes_per_bank_per_subcircuit=15       #number of tubes per bank per circuit
        HEX.Circuits[0].Geometry.Nbank = 1                             #number of banks or rows
        HEX.Circuits[0].Geometry.OD = 0.012
        HEX.Circuits[0].Geometry.ID = 0.011
        HEX.Circuits[0].Geometry.Staggering = 'aAa'
        HEX.Circuits[0].Geometry.Tubes_type='Smooth'
        HEX.Circuits[0].Geometry.Pl = 0.019               #distance between center of tubes in flow direction                                                
        HEX.Circuits[0].Geometry.Pt = 0.019                #distance between center of tubes orthogonal to flow direction
        # HEX.Circuits[i].Geometry.Connections = [16,17,18,19,20,15,14,13,12,11,6,7,8,9,10,5,4,3,2,1]
        HEX.Circuits[0].Geometry.Connections = [(i+1) for i in reversed(range(15))]
        HEX.Circuits[0].Geometry.FarBendRadius = 0.01
        HEX.Circuits[0].Geometry.e_D = 0
        HEX.Circuits[0].Geometry.FPI = 18
        HEX.Circuits[0].Geometry.FinType = 'WavyLouvered'
        HEX.Circuits[0].Geometry.Fin_t = 0.0001
        HEX.Circuits[0].Geometry.Fin_Pd = 0.001
        HEX.Circuits[0].Geometry.Fin_xf = 0.001
        
        HEX.Circuits[0].Thermal.Nsegments = 20
        HEX.Circuits[0].Thermal.kw = 385
        HEX.Circuits[0].Thermal.FinsOnce = True
        HEX.Circuits[0].Thermal.k_fin = 210

        HEX.Circuits[0].Thermal.DP_a_wet_on = False
        HEX.Circuits[0].Thermal.h_a_wet_on = False
        HEX.Circuits[0].Geometry.Ltube=0.9                        #one tube length

        # HEX.Fan.model = 'curve'
        # a = 17.04447135
        # b = 2135.389026
        # c = -16099.01934
        # d = 48475.41375
        # HEX.Fan.power_curve = str(a)+'+('+str(b)+')*X+('+str(c)+')*X**2+('+str(d)+')*X**3'
        # a = 2508.571429
        # b = 8400.974026
        # c = -459253.2468
        # d = -767045.4545
        # HEX.Fan.DP_curve = str(a)+'+('+str(b)+')*X+('+str(c)+')*X**2+('+str(d)+')*X**3'

        HEX.Fan.model = 'efficiency'
        HEX.Fan.efficiency = '0.4'
    
        HEX.Fan.Fan_position = 'after'
        
        if HEX.Fan.model == 'curve':
            HEX.Vdot_ha = 0.8

        elif HEX.Fan.model == 'efficiency':
            HEX.Vdot_ha = 0.8
        
        import time
        T1 = time.time()
        HEX.Solver = 'mdot'
        HEX.solve()
        T2 = time.time()
        print("total time:",T2-T1)

    def HEX3():
        global HEX
        HEX = FinTubeHEXClass()
        HEX.Accurate = True
        HEX.create_circuits(4)
        HEX.connect(0,1,0,1.0,10)
        HEX.connect(1,2,1,1.0,6)
        HEX.connect(2,3,2,1.0,3)
        HEX.connect(3,4,3,1.0,1)
        HEX.mdot_r = 0.07
        HEX.Pin_r = 15*101325
        HEX.Tin_a = 305
        HEX.Pin_a = 101325
        from CoolProp.CoolProp import HAPropsSI
        Win_a = HAPropsSI('W','P',HEX.Pin_a,'T',HEX.Tin_a,'R',0.5)
        HEX.Win_a = Win_a
        # HEX.Air_sequence = 'parallel'
        # HEX.Air_sequence = 'series_parallel'
        # HEX.Air_sequence = 'series_counter'
        HEX.Air_sequence = 'sub_HX_last'
        # HEX.Air_sequence = 'sub_HX_last'
        if HEX.Air_sequence in ['sub_HX_first','sub_HX_last']:
            Air_distribution = [1 / (len(HEX.Circuits)-1) for _ in range(len(HEX.Circuits)-1)]
            HEX.Air_distribution = Air_distribution
        elif HEX.Air_sequence in ['parallel']:
            Air_distribution = [1 / len(HEX.Circuits) for _ in range(len(HEX.Circuits))]
            HEX.Air_distribution = Air_distribution
        HEX.model = 'segment'
        HEX.Q_error_tol = 0.01
        HEX.max_iter_per_circuit = 20
        HEX.Ref_Pressure_error_tol = 100
        Ref = 'R22'
        Backend = 'HEOS'
        AS = CP.AbstractState(Backend, Ref)
        HEX.AS = AS
        AS.update(CP.PT_INPUTS,HEX.Pin_r,90+273.15)
        HEX.hin_r = AS.hmass()
        
        for i in range(len(HEX.Circuits)-1):
            HEX.Circuits[i].Geometry.Ntubes_per_bank_per_subcircuit=5       #number of tubes per bank per circuit
            HEX.Circuits[i].Geometry.Nbank = 2                             #number of banks or rows
            HEX.Circuits[i].Geometry.OD = 0.012
            HEX.Circuits[i].Geometry.ID = 0.011
            HEX.Circuits[i].Geometry.Staggering = 'aAa'
            HEX.Circuits[i].Geometry.Tubes_type='Smooth'
            HEX.Circuits[i].Geometry.Pl = 0.019               #distance between center of tubes in flow direction                                                
            HEX.Circuits[i].Geometry.Pt = 0.019                #distance between center of tubes orthogonal to flow direction
            # HEX.Circuits[i].Geometry.Connections = [16,17,18,19,20,15,14,13,12,11,6,7,8,9,10,5,4,3,2,1]
            HEX.Circuits[i].Geometry.Connections = [6,7,8,9,10,5,4,3,2,1]
            HEX.Circuits[i].Geometry.FarBendRadius = 0.01
            HEX.Circuits[i].Geometry.e_D = 0
            HEX.Circuits[i].Geometry.FPI = 18
            HEX.Circuits[i].Geometry.FinType = 'WavyLouvered'
            HEX.Circuits[i].Geometry.Fin_t = 0.0001
            HEX.Circuits[i].Geometry.Fin_Pd = 0.001
            HEX.Circuits[i].Geometry.Fin_xf = 0.001
            
            HEX.Circuits[i].Thermal.Nsegments = 20
            HEX.Circuits[i].Thermal.kw = 385
            HEX.Circuits[i].Thermal.FinsOnce = True
            HEX.Circuits[i].Thermal.k_fin = 210

            HEX.Circuits[i].Thermal.DP_a_wet_on = False
            HEX.Circuits[i].Thermal.h_a_wet_on = False
            HEX.Circuits[i].Geometry.Ltube=0.9                        #one tube length

        HEX.Circuits[-1].Geometry.Ntubes_per_bank_per_subcircuit=15       #number of tubes per bank per circuit
        HEX.Circuits[-1].Geometry.Nbank = 1                             #number of banks or rows
        HEX.Circuits[-1].Geometry.OD = 0.012
        HEX.Circuits[-1].Geometry.ID = 0.011
        HEX.Circuits[-1].Geometry.Staggering = 'aAa'
        HEX.Circuits[-1].Geometry.Tubes_type='Smooth'
        HEX.Circuits[-1].Geometry.Pl = 0.019               #distance between center of tubes in flow direction                                                
        HEX.Circuits[-1].Geometry.Pt = 0.019                #distance between center of tubes orthogonal to flow direction
        # HEX.Circuits[i].Geometry.Connections = [16,17,18,19,20,15,14,13,12,11,6,7,8,9,10,5,4,3,2,1]
        HEX.Circuits[-1].Geometry.Connections = [(i+1) for i in reversed(range(15))]
        HEX.Circuits[-1].Geometry.FarBendRadius = 0.01
        HEX.Circuits[-1].Geometry.e_D = 0
        HEX.Circuits[-1].Geometry.FPI = 18
        HEX.Circuits[-1].Geometry.FinType = 'WavyLouvered'
        HEX.Circuits[-1].Geometry.Fin_t = 0.0001
        HEX.Circuits[-1].Geometry.Fin_Pd = 0.001
        HEX.Circuits[-1].Geometry.Fin_xf = 0.001
        
        HEX.Circuits[-1].Thermal.Nsegments = 20
        HEX.Circuits[-1].Thermal.kw = 385
        HEX.Circuits[-1].Thermal.FinsOnce = True
        HEX.Circuits[-1].Thermal.k_fin = 210

        HEX.Circuits[-1].Thermal.DP_a_wet_on = False
        HEX.Circuits[-1].Thermal.h_a_wet_on = False
        HEX.Circuits[-1].Geometry.Ltube=0.9                        #one tube length

        # HEX.Fan.model = 'curve'
        # a = 17.04447135
        # b = 2135.389026
        # c = -16099.01934
        # d = 48475.41375
        # HEX.Fan.power_curve = str(a)+'+('+str(b)+')*X+('+str(c)+')*X**2+('+str(d)+')*X**3'
        # a = 2508.571429
        # b = 8400.974026
        # c = -459253.2468
        # d = -767045.4545
        # HEX.Fan.DP_curve = str(a)+'+('+str(b)+')*X+('+str(c)+')*X**2+('+str(d)+')*X**3'

        HEX.Fan.model = 'efficiency'
        HEX.Fan.efficiency = '0.4'
    
        HEX.Fan.Fan_position = 'after'
        
        if HEX.Fan.model == 'curve':
            HEX.Vdot_ha = 0.8

        elif HEX.Fan.model == 'efficiency':
            HEX.Vdot_ha = 0.8
        
        import time
        T1 = time.time()
        HEX.Solver = 'mdot'
        HEX.solve()
        T2 = time.time()
        print("total time:",T2-T1)

    def HEX4():
        global HEX
        HEX = FinTubeHEXClass()
        HEX.Accurate = True
        HEX.create_circuits(2)
        HEX.connect(0,1,0,1.0,1)
        HEX.connect(1,2,1,1.0,2)
        HEX.mdot_r = 0.044372891058857056
        HEX.Pin_r = 1025411.8245815673
        HEX.hin_r = 263379.13941641495
        HEX.Tin_a = 27+273.15
        HEX.Pin_a = 101325
        from CoolProp.CoolProp import HAPropsSI
        Win_a = HAPropsSI('W','P',HEX.Pin_a,'T',HEX.Tin_a,'B',19+273.15)
        HEX.Win_a = Win_a
        HEX.Air_sequence = 'parallel'
        Air_distribution = [0.1667, 0.8333]
        HEX.Air_distribution = Air_distribution
        HEX.model = 'phase'
        HEX.Q_error_tol = 0.01
        HEX.max_iter_per_circuit = 20
        HEX.Ref_Pressure_error_tol = 100
        Ref = 'R410A'
        Backend = 'HEOS'
        AS = CP.AbstractState(Backend, Ref)
        HEX.AS = AS

        HEX.Circuits[0].Geometry.Ntubes_per_bank_per_subcircuit=2       #number of tubes per bank per circuit
        HEX.Circuits[0].Geometry.Nbank = 2                             #number of banks or rows
        HEX.Circuits[1].Geometry.Ntubes_per_bank_per_subcircuit=5       #number of tubes per bank per circuit
        HEX.Circuits[1].Geometry.Nbank = 2                             #number of banks or rows
        
        for i in range(len(HEX.Circuits)):
            HEX.Circuits[i].Geometry.OD = 0.00953
            HEX.Circuits[i].Geometry.t = 0.43 /1000
            HEX.Circuits[i].Geometry.e = 0.15 /1000
            HEX.Circuits[i].Geometry.gama = 30
            HEX.Circuits[i].Geometry.beta = 15
            HEX.Circuits[i].Geometry.d = 0.0804 /1000
            HEX.Circuits[i].Geometry.n = 70
            HEX.Circuits[i].Geometry.Staggering = 'AaA'
            HEX.Circuits[i].Geometry.Tubes_type='Microfin'
            HEX.Circuits[i].Geometry.Pl = 0.01905               #distance between center of tubes in flow direction                                                
            HEX.Circuits[i].Geometry.Pt = 0.0254                #distance between center of tubes orthogonal to flow direction
            HEX.Circuits[i].Geometry.FarBendRadius = 0.01
            HEX.Circuits[i].Geometry.e_D = 0
            HEX.Circuits[i].Geometry.FPI = 17
            HEX.Circuits[i].Geometry.FinType = 'Louvered'
            HEX.Circuits[i].Geometry.Fin_t = 0.000105
            HEX.Circuits[i].Geometry.Fin_Lp = 0.001505
            HEX.Circuits[i].Geometry.Fin_Lh = 0.0008
            HEX.Circuits[i].Geometry.Connections = [(i+1) for i in reversed(range(HEX.Circuits[i].Geometry.Ntubes_per_bank_per_subcircuit*HEX.Circuits[i].Geometry.Nbank))]
            
            HEX.Circuits[i].Thermal.Nsegments = 20
            HEX.Circuits[i].Thermal.kw = 339
            HEX.Circuits[i].Thermal.FinsOnce = True
            HEX.Circuits[i].Thermal.k_fin = 195

            HEX.Circuits[i].Thermal.DP_a_wet_on = False
            HEX.Circuits[i].Thermal.h_a_wet_on = False
            HEX.Circuits[i].Geometry.Ltube = 0.8172                        #one tube length
            HEX.Circuits[i].Thermal.h_a_dry_tuning = 0.8
            HEX.Circuits[i].Thermal.h_a_wet_tuning = 0.8
            HEX.Circuits[i].Thermal.h_a_dry_tuning = 0.8
            HEX.Circuits[i].Thermal.h_a_wet_tuning = 0.8
            HEX.Circuits[i].Thermal.HTC_subcool_Corr = 2
            HEX.Circuits[i].Thermal.DP_subcool_Corr = 2
            HEX.Circuits[i].Thermal.HTC_2phase_Corr = 2
            HEX.Circuits[i].Thermal.DP_2phase_Corr = 6
            HEX.Circuits[i].Thermal.HTC_superheat_Corr = 2
            HEX.Circuits[i].Thermal.DP_superheat_Corr = 2

        HEX.Fan.model = 'efficiency'
        HEX.Fan.efficiency = '0.4'
    
        HEX.Fan.Fan_position = 'after'
        
        HEX.Vdot_ha = 0.3145
        
        import time
        T1 = time.time()
        HEX.Solver = 'mdot'
        HEX.solve()
        T2 = time.time()
        print("total time:",T2-T1)

    def HEX5():
        global HEX
        HEX = FinTubeHEXClass()
        HEX.Accurate = True
        HEX.create_circuits(2)
        HEX.connect(0,1,0,1.0,1)
        HEX.connect(1,2,1,1.0,2)
        HEX.mdot_r = 0.044376311255301434
        HEX.Pin_r = 1025482.6055180468
        HEX.hin_r = 263382.3973842334
        HEX.Tin_a = 27+273.15
        HEX.Pin_a = 101325
        from CoolProp.CoolProp import HAPropsSI
        Win_a = HAPropsSI('W','P',HEX.Pin_a,'T',HEX.Tin_a,'B',19+273.15)
        HEX.Win_a = Win_a
        HEX.Air_sequence = 'parallel'
        Air_distribution = [0.1667, 0.8333]
        HEX.Air_distribution = Air_distribution
        HEX.model = 'phase'
        HEX.Q_error_tol = 0.01
        HEX.max_iter_per_circuit = 20
        HEX.Ref_Pressure_error_tol = 100
        Ref = 'R410A'
        Backend = 'HEOS'
        AS = CP.AbstractState(Backend, Ref)
        HEX.AS = AS

        HEX.Circuits[0].Geometry.Ntubes_per_bank_per_subcircuit=2       #number of tubes per bank per circuit
        HEX.Circuits[0].Geometry.Nbank = 2                             #number of banks or rows
        HEX.Circuits[1].Geometry.Ntubes_per_bank_per_subcircuit=5       #number of tubes per bank per circuit
        HEX.Circuits[1].Geometry.Nbank = 2                             #number of banks or rows
        
        for i in range(len(HEX.Circuits)):
            HEX.Circuits[i].Geometry.OD = 0.00953
            HEX.Circuits[i].Geometry.t = 0.43 /1000
            HEX.Circuits[i].Geometry.e = 0.15 /1000
            HEX.Circuits[i].Geometry.gama = 30
            HEX.Circuits[i].Geometry.beta = 15
            HEX.Circuits[i].Geometry.d = 0.0804 /1000
            HEX.Circuits[i].Geometry.n = 70
            HEX.Circuits[i].Geometry.Staggering = 'AaA'
            HEX.Circuits[i].Geometry.Tubes_type='Microfin'
            HEX.Circuits[i].Geometry.Pl = 0.01905               #distance between center of tubes in flow direction                                                
            HEX.Circuits[i].Geometry.Pt = 0.0254                #distance between center of tubes orthogonal to flow direction
            HEX.Circuits[i].Geometry.FarBendRadius = 0.01
            HEX.Circuits[i].Geometry.e_D = 0
            HEX.Circuits[i].Geometry.FPI = 17
            HEX.Circuits[i].Geometry.FinType = 'Louvered'
            HEX.Circuits[i].Geometry.Fin_t = 0.000105
            HEX.Circuits[i].Geometry.Fin_Lp = 0.001505
            HEX.Circuits[i].Geometry.Fin_Lh = 0.0008
            HEX.Circuits[i].Geometry.Connections = [(i+1) for i in reversed(range(HEX.Circuits[i].Geometry.Ntubes_per_bank_per_subcircuit*HEX.Circuits[i].Geometry.Nbank))]
            
            HEX.Circuits[i].Thermal.Nsegments = 20
            HEX.Circuits[i].Thermal.kw = 339
            HEX.Circuits[i].Thermal.FinsOnce = True
            HEX.Circuits[i].Thermal.k_fin = 195

            HEX.Circuits[i].Thermal.DP_a_wet_on = False
            HEX.Circuits[i].Thermal.h_a_wet_on = False
            HEX.Circuits[i].Geometry.Ltube=0.8172                        #one tube length
            HEX.Circuits[i].Thermal.h_a_dry_tuning = 0.8
            HEX.Circuits[i].Thermal.h_a_wet_tuning = 0.8
            HEX.Circuits[i].Thermal.h_a_dry_tuning = 0.8
            HEX.Circuits[i].Thermal.h_a_wet_tuning = 0.8
            HEX.Circuits[i].Thermal.h_a_dry_tuning = 0.8
            HEX.Circuits[i].Thermal.h_a_wet_tuning = 0.8
            HEX.Circuits[i].Thermal.HTC_subcool_Corr = 2
            HEX.Circuits[i].Thermal.DP_subcool_Corr = 2
            HEX.Circuits[i].Thermal.HTC_2phase_Corr = 2
            HEX.Circuits[i].Thermal.DP_2phase_Corr = 6
            HEX.Circuits[i].Thermal.HTC_superheat_Corr = 2
            HEX.Circuits[i].Thermal.DP_superheat_Corr = 2


        HEX.Fan.model = 'efficiency'
        HEX.Fan.efficiency = '0.4'
    
        HEX.Fan.Fan_position = 'after'
        
        HEX.Vdot_ha = 0.3145
        
        import time
        T1 = time.time()
        HEX.Solver = 'mdot'
        HEX.solve()
        T2 = time.time()
        print("total time:",T2-T1)


    HEX1()

    print('model:',HEX.model)
    print('DP_r:',HEX.Results.DP_r)
    print('DP_r_subcool:',HEX.Results.DP_r_subcool)
    print('DP_r_2phase:',HEX.Results.DP_r_2phase)
    print('DP_r_superheat:',HEX.Results.DP_r_superheat)
    print('h_r_subcool:',HEX.Results.h_r_subcool)
    print('h_r_2phase:',HEX.Results.h_r_2phase)
    print('h_r_superheat:',HEX.Results.h_r_superheat)
    print('w_subcool:',HEX.Results.w_subcool)
    print('w_2phase:',HEX.Results.w_2phase)
    print('w_superheat:',HEX.Results.w_superheat)
    print('DP_a:',HEX.Results.DP_a)
    print('h_a_dry:',HEX.Results.h_a_dry)
    print('h_a_wet:',HEX.Results.h_a_wet)
    print('Q:',HEX.Results.Q)
    print('Q_latent:',HEX.Results.Q-HEX.Results.Q_sensible)
    print('Vdot_ha:',HEX.Vdot_ha)
    for i,circuit in enumerate(HEX.Circuits):
        print("Circuit_",i,"_Q: ",circuit.Results.Q,sep="")
        print("Circuit_",i,"_Q_latent: ",circuit.Results.Q-circuit.Results.Q_sensible,sep="")
        if hasattr(circuit,"phase_segments"):
            for j,segment in enumerate(circuit.phase_segments):
                print("Circuit_",i,"_semgnet_",j,"_Q_latent: ",segment.Q-segment.Q_sensible,sep="")
                print("Circuit_",i,"_semgnet_",j,"_Q_sensible: ",segment.Q_sensible,sep="")
                print("Circuit_",i,"_semgnet_",j,"_f_dry: ",segment.f_dry,sep="")
                print("Circuit_",i,"_semgnet_",j,"_Tin_r: ",segment.Tin_r,sep="")
                print("Circuit_",i,"_semgnet_",j,"_Tin_a: ",segment.Tin_a,sep="")
                print("Circuit_",i,"_semgnet_",j,"_h_a: ",segment.h_a,sep="")
                print("Circuit_",i,"_semgnet_",j,"_h_r: ",segment.h_r,sep="")
                print("Circuit_",i,"_semgnet_",j,"_x_in_r: ",segment.x_in,sep="")
                
                
    print('x_out',HEX.Results.xout_r)
    print('Converged:',HEX.Converged)
    if HEX.Air_sequence == 'parallel':
        print("DP_a_array:",HEX.Results.DP_a_array)
