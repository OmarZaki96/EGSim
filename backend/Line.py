from __future__ import division, print_function, absolute_import
import numpy as np
import CoolProp as CP
from math import pi, log
from backend.FinTubeHEXCorrelations import CorrelationsClass
from scipy.optimize import fsolve

class ValuesClass():
    pass

class LineClass():
    """
    Line class, used to solve heat transfer and pressure drop in lines
    
    Required Parameters:
    
    ===========    ==========  ========================================================================
    Variable       Units       Description
    ===========    ==========  ========================================================================
    Pin_r          Pa          Refrigerant inlet pressure
    hin_r          J/kg        Refrigerant inlet enthalpy
    T_sur          K           Temperature of Air surrounding the line
    h_sur          W/m^2.K     Heat transfer coefficient of air surrounding the line
    t_ins          m           Insulation thickness around the line
    k_ins          W/m.K       Thermal conductivity of insulation around line
    OD             m           Line outer diameter (excluding insulation)
    ID             m           Line inner diameter
    L              m           Line length
    k_line         W/m.K       Thermal conductivity of the line (excluding insulation)
    e_D            --          roughness of the inner surface of the tube
    Nsegments      --          Number of segments to solve the line
    mdot_r         kg/s        Refrigerant mass flow rate
    Q_error_tol    --          error tolerance in heat transfer while solving 1phase
    DP_tuning      --          tuning factor for pressure drop
    HT_tuning      --          tuning factor for heat trasnfer
    N_90_bends     --          Number of 90 degrees bends
    N_180_bends    --          Number of 180 degrees bends
    ===========   ==========  ========================================================================
    
    All variables are of double-type unless otherwise specified
        
    """
    def __init__(self,**kwargs):
        #Load up the parameters passed in
        # using the dictionary
        self.Correlations = CorrelationsClass()
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
            ('Length of Line','m',self.L),
            ('Line OD','m',self.OD),
            ('Line ID','m',self.ID),
            ('','',''),
            ('Line relative roughness (e/D)','-',self.e_D),
            ('Line thermal conductivity','W/m.K',self.k_line),
            ('','',''),
            ('Insulation thickness','m',self.t_ins),
            ('Insulation thermal conductivity','W/m.K',self.k_ins),
            ('','',''),
            ('Refrigerant Mass Flowrate','kg/s',self.mdot_r),
            ('','',''),
            ('Surrounding air HTC','W/m^2.K',self.h_sur),
            ('Surrounding air temperature','C',self.T_sur-273.15),
            ('','',''),
            ('Number of Segments','-',self.Nsegments),
            ('','',''),
            ('Heat Trasnfer Error Tolerance','%',self.Q_error_tol*100),
            ('Heat Transfer Tuning Factor','-',self.HT_tuning),
            ('Pressure Drop Tuning Factor','-',self.DP_tuning),
            ('','',''),
            ('Heat transfer of line','W',self.Results.Q),
            ('','',''),
            ('Pressure drop of line','Pa',self.Results.DP_r),
            ('Bends Pressure drop','Pa',self.Results.DP_bends),
            ('','',''),
            ('Charge','kg',self.Results.Charge),
            ('','',''),
            ('Inlet refrigerant temperature','C',self.Results.Tin_r-273.15),
            ('Inlet refrigerant enthalpy','J/kg',self.Results.hin_r),
            ('Inlet refrigerant Pressure','Pa',self.Results.Pin_r),
            ('Inlet refrigerant Entropy','J/kg.K',self.Results.Sin_r),
            ('','',''),
            ('Outlet refrigerant temperature','C',self.Results.Tout_r-273.15),
            ('Outlet refrigerant enthalpy','J/kg',self.Results.hout_r),
            ('Outlet refrigerant Pressure','Pa',self.Results.Pout_r),
            ('Outlet refrigerant Entropy','J/kg.K',self.Results.Sout_r),
            ('','',''),
            ('','',''),
            ('Entropy generation','W/K',self.Results.S_gen),
         ]
    
    def Calculate_Thermal_Resistances(self):
        '''
        Function used to calculate auxillary thermal resistance that depend on
        thermal and geometric properties given; this inclued wall thermal
        resistance, air thermal resistance and insulation thermal resistance.

        Returns
        -------
        R_aux : float
            total auxillary thermal resistance.

        '''
        # defining necessary parameters
        h_sur = self.h_sur
        ID = self.ID
        OD = self.OD
        t_ins = self.t_ins
        k_ins = self.k_ins
        k_line = self.k_line

        # calculating surrounding air thermal resistance, if zero or negative, then thermal resistance is infinity
        if h_sur <= 0:
            R_sur = 1e15
        else:
            R_sur = 1.0 / (h_sur * pi * (OD + 2.0 * t_ins))
        
        # calculating insulation thermal resistance
        R_ins = log((OD + 2.0 * t_ins) / OD) / (2.0 * pi * k_ins)
        
        # calculating line thermal resistance
        R_line = log(OD / ID) / (2.0 * pi * k_line)
                
        # calculating total auxillary thermal resistances
        R_aux = R_sur + R_ins + R_line
        return R_aux
    
    def Calculate(self):
        '''
        The function to calculate the heat transfer and pressure drop in the 
        line.

        Returns
        -------
        None.

        '''
        # Getting inlet values
        Pin_r = self.Pin_r
        hin_r = self.hin_r
        
        # create geometry class to use the correlations class of fin-tube that is already written
        geometry = self.create_geometry()
        
        # create thermal class to use the correlations class of fin-tube that is already written
        thermal = ValuesClass()
        
        # get auxillary thermal resistances (this is per unit length)
        R_aux = self.Calculate_Thermal_Resistances()
        
        # create segments list
        segments = [ValuesClass() for i in range(self.Nsegments)]
        
        # assign classes and R_aux to each segment
        for segment in segments:
            segment.R_aux = R_aux
            segment.geometry = geometry
            segment.thermal = thermal
        
        # assign values of first segment
        segments[0].Pin_r = Pin_r
        segments[0].hin_r = hin_r
        
        # solving each segment using the values from previous segment
        for i,segment in enumerate(segments):
            if self.terminate:
                raise
            segment = self.solve_segment(segment)
            if not (i == len(segments) - 1): # not the last segment
                segments[i + 1].Pin_r = segment.Pout_r
                segments[i + 1].hin_r = segment.hout_r
        # save segments
        self.Segments = segments
        
        # create results
        self.Results = self.create_results(segments)
        
    def create_results(self,segments):
        '''
        A function used to create results subclass from passed segments list

        Parameters
        ----------
        segments : list
            a list of segments of the line with inlet and outlet values and 
            heat transfer calculations.

        Returns
        -------
        Results : class
            a class containing the results of the solution.

        '''
        
        
        AS = self.AS
        Results = ValuesClass()
        Results.DP_bends = self.calculate_bends_pressure()
        Results.Pin_r = self.Pin_r
        Results.Pout_r = segments[-1].Pout_r + Results.DP_bends
        Results.DP_r = Results.Pout_r - Results.Pin_r
        Results.hin_r = self.hin_r
        Results.hout_r = segments[-1].hout_r
        Results.Tin_r = segments[0].Tin_r
        AS.update(CP.HmassP_INPUTS, Results.hin_r, Results.Pin_r)
        Results.Sin_r = AS.smass()
        AS.update(CP.HmassP_INPUTS,Results.hout_r,Results.Pout_r)
        Results.Tout_r = AS.T()
        Results.Sout_r = AS.smass()
        Results.Q = self.mdot_r * (Results.hout_r - Results.hin_r)
        Charge = 0
        for segment in segments:
            Charge += segment.Charge 
        Results.Charge = Charge
        Results.S_gen = self.mdot_r * (Results.Sout_r - Results.Sin_r)
        return Results

    def calculate_bends_pressure(self):
        # get necessary properties
        AS = self.AS
        Pin_r = self.Pin_r
        hin_r = self.hin_r
        mdot_r = self.mdot_r
        
        # calculating inlet quality
        AS.update(CP.PQ_INPUTS, Pin_r, 0.0)
        hL = AS.hmass()
        AS.update(CP.PQ_INPUTS, Pin_r, 1.0)
        hV = AS.hmass()
        xin_r = (hin_r - hL) / (hV - hL)
        
        # calculate necessary geometry features
        geometry = self.create_geometry()
        
        # calculate inlet density
        if 0 < xin_r < 1: # two-phase flow
            thermal = ValuesClass() # just a placeholder
            mode = "cooler" # just a placeholder
            A_r = 1 # just a placeholder
            self.Correlations.update(self.AS, geometry, thermal, '2phase',Pin_r, xin_r, mdot_r, A_r, mode,var_2nd_out=xin_r)
            rho = self.Correlations.calculate_rho_2phase()
        else:
            AS.update(CP.HmassP_INPUTS,hin_r,Pin_r)
            rho = AS.rhomass()

        vel = mdot_r / (rho * geometry.A_CS)
        
        DP_90_bend = 0.3 * 0.5 * rho * vel**2 #Kp = 0.3 from cengel fluid book
        DP_180_bend = 0.2 * 0.5 * rho * vel**2 #Kp = 0.2 from cengel fluid book
        
        DP_total = DP_90_bend * self.N_90_bends + DP_180_bend * self.N_180_bends
        
        DP_total *= self.DP_tuning
        
        return -DP_total

    def create_geometry(self):
        '''
        This function will create a psuedo geometry class to use fin-tube 
        correlations class.

        Returns
        -------
        geometry : class
            geomtry class in the style of fin-tube geomtry class.

        '''
        ID = self.ID
        OD = self.OD
        e_D = self.e_D
        geometry = ValuesClass()
        geometry.Tubes_type = 'Smooth'
        geometry.ID = ID
        geometry.e_D = e_D
        geometry.inner_circum = pi * ID
        geometry.A_CS = pi / 4 * ID * ID
        geometry.OD = OD
        geometry.Dh = ID
        return geometry
    
    def solve_segment(self,segment):
        '''
        This function is used to solve the passed segment.

        Parameters
        ----------
        segment : class
            a class containg the necessary heat treansfer values of the segment.

        Returns
        -------
        segment : class
            return the segment class after solving it.

        '''
        # get necessary properties
        AS = self.AS
        Pin_r = segment.Pin_r
        hin_r = segment.hin_r
        
        # calculating inlet quality
        AS.update(CP.PQ_INPUTS, Pin_r, 0.0)
        hL = AS.hmass()
        AS.update(CP.PQ_INPUTS, Pin_r, 1.0)
        hV = AS.hmass()
        xin_r = (hin_r - hL) / (hV - hL)
        
        # saving inlet quality
        segment.xin_r = xin_r
        
        # getting inlet temperature
        AS.update(CP.HmassP_INPUTS, hin_r, Pin_r)
        Tin_r = AS.T()
        
        # saving inlet temperature
        segment.Tin_r = Tin_r
        
        # getting segment length
        L_segment = self.L / self.Nsegments
        
        # create correlations instance of the correlations class from fin-tube
        correlations = self.Correlations
        
        # getting geometry and thermal instances, and getting auxillary thermal resistance value
        geometry = segment.geometry
        thermal = segment.thermal
        R_aux = segment.R_aux
        if xin_r < 0.0: # subcooled inlet
            # solve 1phase segment
            Pout_r, hout_r, Charge = self.solve_1phase(Pin_r,hin_r,L_segment,correlations,geometry,thermal,R_aux)
            # calculating outlet quality
            AS.update(CP.PQ_INPUTS, Pout_r, 0.0)
            hL = AS.hmass()
            AS.update(CP.PQ_INPUTS, Pout_r, 1.0)
            hV = AS.hmass()
            xout_r = (hout_r - hL) / (hV - hL)
            if xout_r <= 0.0: # if outlet is subcooled
                segment.Pout_r = Pout_r
                segment.hout_r = hout_r
                segment.xout_r = xout_r
                segment.Charge = Charge
                AS.update(CP.HmassP_INPUTS, hout_r, Pout_r)
                Tout_r = AS.T()
                segment.Tout_r = Tout_r
                return segment
            elif xout_r > 0.0: # if outlet isn't subcooled
                def objective(L_solve): # find length up to phase change
                    Pout_r, hout_r, Charge = self.solve_1phase(Pin_r,hin_r,L_solve,correlations,geometry,thermal,R_aux)
                    AS.update(CP.PQ_INPUTS, Pout_r, 0.0)
                    hL = AS.hmass()
                    AS.update(CP.PQ_INPUTS, Pout_r, 1.0)
                    hV = AS.hmass()
                    xout_r = (hout_r - hL) / (hV - hL)
                    return xout_r
                
                # getting length of subcooled
                L_subcool = float(fsolve(objective,L_segment))
                
                # getting outlet values from subcooled
                Pout_subcool, hout_subcool, Charge_subcool = self.solve_1phase(Pin_r,hin_r,L_subcool,correlations,geometry,thermal,R_aux)
                
                # solving phase region with outlet values from subcooled and rest of the length
                Pout_r, hout_r, Charge_2phase = self.solve_2phase(Pout_subcool, hout_subcool,L_segment - L_subcool,correlations,geometry,thermal,R_aux)
                AS.update(CP.PQ_INPUTS, Pout_r, 0.0)
                hL = AS.hmass()
                AS.update(CP.PQ_INPUTS, Pout_r, 1.0)
                hV = AS.hmass()
                xout_r = (hout_r - hL) / (hV - hL)
                # getting outlet quality from the 2phase region
                if xout_r <= 1.0: # if 2phase also
                    segment.Pout_r = Pout_r
                    segment.hout_r = hout_r
                    segment.xout_r = xout_r
                    segment.Charge = Charge_subcool + Charge_2phase
                    AS.update(CP.HmassP_INPUTS, hout_r, Pout_r)
                    Tout_r = AS.T()
                    segment.Tout_r = Tout_r
                    return segment
                else: # if superheated
                    def objective(L_solve):
                        Pout_r, hout_r, Charge = self.solve_2phase(Pout_subcool,hout_subcool,L_solve,correlations,geometry,thermal,R_aux)
                        AS.update(CP.PQ_INPUTS, Pout_r, 0.0)
                        hL = AS.hmass()
                        AS.update(CP.PQ_INPUTS, Pout_r, 1.0)
                        hV = AS.hmass()
                        xout_r = (hout_r - hL) / (hV - hL)
                        return 1 - xout_r
                    
                    # find the length of 2phase region
                    L_2phase = float(fsolve(objective,L_segment - L_subcool))
                    
                    # get outlet values from 2phase region using the calculated length
                    Pout_2phase, hout_2phase, Charge_2phase = self.solve_2phase(Pout_subcool,hout_subcool,L_2phase,correlations,geometry,thermal,R_aux)
                    
                    # solve superheated region using the rest of the length
                    Pout_r, hout_r, Charge_superheat = self.solve_1phase(Pout_2phase, hout_2phase,L_segment - L_subcool - L_2phase,correlations,geometry,thermal,R_aux)
                    
                    # calculating outlet quality
                    AS.update(CP.PQ_INPUTS, Pout_r, 0.0)
                    hL = AS.hmass()
                    AS.update(CP.PQ_INPUTS, Pout_r, 1.0)
                    hV = AS.hmass()
                    xout_r = (hout_r - hL) / (hV - hL)
                    segment.Pout_r = Pout_r
                    segment.hout_r = hout_r
                    segment.xout_r = xout_r
                    segment.Charge = Charge_subcool + Charge_2phase + Charge_superheat
                    AS.update(CP.HmassP_INPUTS, hout_r, Pout_r)
                    Tout_r = AS.T()
                    segment.Tout_r = Tout_r
                    return segment
                
        elif xin_r > 1.0: # the same algorith as subcooled, but with necessary changes
            Pout_r, hout_r, Charge = self.solve_1phase(Pin_r,hin_r,L_segment,correlations,geometry,thermal,R_aux)
            AS.update(CP.PQ_INPUTS, Pout_r, 0.0)
            hL = AS.hmass()
            AS.update(CP.PQ_INPUTS, Pout_r, 1.0)
            hV = AS.hmass()
            xout_r = (hout_r - hL) / (hV - hL)
            if xout_r >= 1.0:
                segment.Pout_r = Pout_r
                segment.hout_r = hout_r
                segment.xout_r = xout_r
                segment.Charge = Charge
                AS.update(CP.HmassP_INPUTS, hout_r, Pout_r)
                Tout_r = AS.T()
                segment.Tout_r = Tout_r
                return segment
            elif xout_r < 1.0:
                def objective(L_solve):
                    Pout_r, hout_r, Charge = self.solve_1phase(Pin_r,hin_r,L_solve,correlations,geometry,thermal,R_aux)
                    AS.update(CP.PQ_INPUTS, Pout_r, 0.0)
                    hL = AS.hmass()
                    AS.update(CP.PQ_INPUTS, Pout_r, 1.0)
                    hV = AS.hmass()
                    xout_r = (hout_r - hL) / (hV - hL)
                    return 1.0 - xout_r
                L_superheat = float(fsolve(objective,L_segment))
                Pout_superheat, hout_superheat, Charge_superheat = self.solve_1phase(Pin_r,hin_r,L_superheat,correlations,geometry,thermal,R_aux)
                Pout_r, hout_r, Charge_2phase = self.solve_2phase(Pout_superheat, hout_superheat,L_segment - L_superheat,correlations,geometry,thermal,R_aux)
                AS.update(CP.PQ_INPUTS, Pout_r, 0.0)
                hL = AS.hmass()
                AS.update(CP.PQ_INPUTS, Pout_r, 1.0)
                hV = AS.hmass()
                xout_r = (hout_r - hL) / (hV - hL)
                if xout_r >= 0.0:
                    segment.Pout_r = Pout_r
                    segment.hout_r = hout_r
                    segment.xout_r = xout_r
                    segment.Charge = Charge_superheat + Charge_2phase
                    AS.update(CP.HmassP_INPUTS, hout_r, Pout_r)
                    Tout_r = AS.T()
                    segment.Tout_r = Tout_r
                    return segment
                else:
                    def objective(L_solve):
                        Pout_r, hout_r, Charge = self.solve_2phase(Pout_superheat,hout_superheat,L_solve,correlations,geometry,thermal,R_aux)
                        AS.update(CP.PQ_INPUTS, Pout_r, 0.0)
                        hL = AS.hmass()
                        AS.update(CP.PQ_INPUTS, Pout_r, 1.0)
                        hV = AS.hmass()
                        xout_r = (hout_r - hL) / (hV - hL)
                        return xout_r
                    
                    L_2phase = float(fsolve(objective,L_segment - L_superheat))
                    Pout_2phase, hout_2phase, Charge_2phase = self.solve_2phase(Pout_superheat,hout_superheat,L_2phase,correlations,geometry,thermal,R_aux)
                    Pout_r, hout_r, Charge_subcool = self.solve_1phase(Pout_2phase, hout_2phase,L_segment - L_superheat - L_2phase,correlations,geometry,thermal,R_aux)
                    AS.update(CP.PQ_INPUTS, Pout_r, 0.0)
                    hL = AS.hmass()
                    AS.update(CP.PQ_INPUTS, Pout_r, 1.0)
                    hV = AS.hmass()
                    xout_r = (hout_r - hL) / (hV - hL)
                    segment.Pout_r = Pout_r
                    segment.hout_r = hout_r
                    segment.xout_r = xout_r
                    segment.Charge = Charge_superheat + Charge_2phase + Charge_subcool
                    AS.update(CP.HmassP_INPUTS, hout_r, Pout_r)
                    Tout_r = AS.T()
                    segment.Tout_r = Tout_r
                    return segment
                
        elif 0 < xin_r < 1.0: # the same algorith as subcooled, but with necessary changes
            Pout_r, hout_r, Charge = self.solve_2phase(Pin_r,hin_r,L_segment,correlations,geometry,thermal,R_aux)
            AS.update(CP.PQ_INPUTS, Pout_r, 0.0)
            hL = AS.hmass()
            AS.update(CP.PQ_INPUTS, Pout_r, 1.0)
            hV = AS.hmass()
            xout_r = (hout_r - hL) / (hV - hL)
            if 0 <= xin_r <= 1.0:
                segment.Pout_r = Pout_r
                segment.hout_r = hout_r
                segment.xout_r = xout_r
                segment.Charge = Charge
                AS.update(CP.HmassP_INPUTS, hout_r, Pout_r)
                Tout_r = AS.T()
                segment.Tout_r = Tout_r
                return segment
            else:
                if xout_r > 1.0:
                    goal = 1.0
                else:
                    goal = 0.0
                def objective(L_solve):
                    Pout_r, hout_r, Charge = self.solve_2phase(Pin_r,hin_r,L_solve,correlations,geometry,thermal,R_aux)
                    AS.update(CP.PQ_INPUTS, Pout_r, 0.0)
                    hL = AS.hmass()
                    AS.update(CP.PQ_INPUTS, Pout_r, 1.0)
                    hV = AS.hmass()
                    xout_r = (hout_r - hL) / (hV - hL)
                    return goal - xout_r
                
                L_2phase = float(fsolve(objective,L_segment))
                Pout_2phase, hout_2phase, Charge_2phase = self.solve_2phase(Pin_r,hin_r,L_2phase,correlations,geometry,thermal,R_aux)
                Pout_r, hout_r, Charge_1phase = self.solve_1phase(Pout_2phase, hout_2phase,L_segment - L_2phase,correlations,geometry,thermal,R_aux)
                AS.update(CP.PQ_INPUTS, Pout_r, 0.0)
                hL = AS.hmass()
                AS.update(CP.PQ_INPUTS, Pout_r, 1.0)
                hV = AS.hmass()
                xout_r = (hout_r - hL) / (hV - hL)
                segment.Pout_r = Pout_r
                segment.hout_r = hout_r
                segment.xout_r = xout_r
                segment.Charge = Charge_2phase + Charge_1phase
                AS.update(CP.HmassP_INPUTS, hout_r, Pout_r)
                Tout_r = AS.T()
                segment.Tout_r = Tout_r
                return segment
            
        elif xin_r == 0:
            Pout_r, hout_r, Charge = self.solve_1phase(Pin_r,hin_r,L_segment,correlations,geometry,thermal,R_aux)
            AS.update(CP.PQ_INPUTS, Pout_r, 0.0)
            hL = AS.hmass()
            AS.update(CP.PQ_INPUTS, Pout_r, 1.0)
            hV = AS.hmass()
            xout_r = (hout_r - hL) / (hV - hL)
            if xout_r <= 0:
                segment.Pout_r = Pout_r
                segment.hout_r = hout_r
                segment.xout_r = xout_r
                segment.Charge = Charge
                AS.update(CP.HmassP_INPUTS, hout_r, Pout_r)
                Tout_r = AS.T()
                segment.Tout_r = Tout_r
                return segment
            else:
                Pout_r, hout_r, Charge = self.solve_2phase(Pin_r,hin_r,L_segment,correlations,geometry,thermal,R_aux)
                AS.update(CP.PQ_INPUTS, Pout_r, 0.0)
                hL = AS.hmass()
                AS.update(CP.PQ_INPUTS, Pout_r, 1.0)
                hV = AS.hmass()
                xout_r = (hout_r - hL) / (hV - hL)
                if xout_r <= 1.0:
                    segment.Pout_r = Pout_r
                    segment.hout_r = hout_r
                    segment.xout_r = xout_r
                    segment.Charge = Charge
                    AS.update(CP.HmassP_INPUTS, hout_r, Pout_r)
                    Tout_r = AS.T()
                    segment.Tout_r = Tout_r
                    return segment
                else:
                    def objective(L_solve):
                        Pout_r, hout_r, Charge = self.solve_2phase(Pin_r,hin_r,L_solve,correlations,geometry,thermal,R_aux)
                        AS.update(CP.PQ_INPUTS, Pout_r, 0.0)
                        hL = AS.hmass()
                        AS.update(CP.PQ_INPUTS, Pout_r, 1.0)
                        hV = AS.hmass()
                        xout_r = (hout_r - hL) / (hV - hL)
                        return 1.0 - xout_r
                    
                    L_2phase = float(fsolve(objective,L_segment))
                    Pout_2phase, hout_2phase, Charge_2phase = self.solve_2phase(Pin_r,hin_r,L_2phase,correlations,geometry,thermal,R_aux)
                    Pout_r, hout_r, Charge_1phase = self.solve_1phase(Pout_2phase, hout_2phase,L_segment - L_2phase,correlations,geometry,thermal,R_aux)
                    AS.update(CP.PQ_INPUTS, Pout_r, 0.0)
                    hL = AS.hmass()
                    AS.update(CP.PQ_INPUTS, Pout_r, 1.0)
                    hV = AS.hmass()
                    xout_r = (hout_r - hL) / (hV - hL)
                    segment.Pout_r = Pout_r
                    segment.hout_r = hout_r
                    segment.xout_r = xout_r
                    segment.Charge = Charge_2phase + Charge_1phase
                    AS.update(CP.HmassP_INPUTS, hout_r, Pout_r)
                    Tout_r = AS.T()
                    segment.Tout_r = Tout_r
                    return segment

        elif xin_r == 1:
            Pout_r, hout_r, Charge = self.solve_1phase(Pin_r,hin_r,L_segment,correlations,geometry,thermal,R_aux)
            AS.update(CP.PQ_INPUTS, Pout_r, 0.0)
            hL = AS.hmass()
            AS.update(CP.PQ_INPUTS, Pout_r, 1.0)
            hV = AS.hmass()
            xout_r = (hout_r - hL) / (hV - hL)
            if xout_r >= 1.0:
                segment.Pout_r = Pout_r
                segment.hout_r = hout_r
                segment.xout_r = xout_r
                segment.Charge = Charge
                AS.update(CP.HmassP_INPUTS, hout_r, Pout_r)
                Tout_r = AS.T()
                segment.Tout_r = Tout_r
                return segment
            else:
                Pout_r, hout_r, Charge = self.solve_2phase(Pin_r,hin_r,L_segment,correlations,geometry,thermal,R_aux)
                AS.update(CP.PQ_INPUTS, Pout_r, 0.0)
                hL = AS.hmass()
                AS.update(CP.PQ_INPUTS, Pout_r, 1.0)
                hV = AS.hmass()
                xout_r = (hout_r - hL) / (hV - hL)
                if xout_r >= 0.0:
                    segment.Pout_r = Pout_r
                    segment.hout_r = hout_r
                    segment.xout_r = xout_r
                    segment.Charge = Charge
                    AS.update(CP.HmassP_INPUTS, hout_r, Pout_r)
                    Tout_r = AS.T()
                    segment.Tout_r = Tout_r
                    return segment
                else:
                    def objective(L_solve):
                        Pout_r, hout_r, Charge = self.solve_2phase(Pin_r,hin_r,L_solve,correlations,geometry,thermal,R_aux)
                        AS.update(CP.PQ_INPUTS, Pout_r, 0.0)
                        hL = AS.hmass()
                        AS.update(CP.PQ_INPUTS, Pout_r, 1.0)
                        hV = AS.hmass()
                        xout_r = (hout_r - hL) / (hV - hL)
                        return xout_r
                    
                    L_2phase = float(fsolve(objective,L_segment))
                    Pout_2phase, hout_2phase, Charge_2phase = self.solve_2phase(Pin_r,hin_r,L_2phase,correlations,geometry,thermal,R_aux)
                    Pout_r, hout_r, Charge_1phase = self.solve_1phase(Pout_2phase, hout_2phase,L_segment - L_2phase,correlations,geometry,thermal,R_aux)
                    AS.update(CP.PQ_INPUTS, Pout_r, 0.0)
                    hL = AS.hmass()
                    AS.update(CP.PQ_INPUTS, Pout_r, 1.0)
                    hV = AS.hmass()
                    xout_r = (hout_r - hL) / (hV - hL)
                    segment.Pout_r = Pout_r
                    segment.hout_r = hout_r
                    segment.xout_r = xout_r
                    segment.Charge = Charge_2phase + Charge_1phase
                    AS.update(CP.HmassP_INPUTS, hout_r, Pout_r)
                    Tout_r = AS.T()
                    segment.Tout_r = Tout_r
                    return segment
        
    def solve_1phase(self,Pin_r,hin_r,L,correlations,geometry,thermal,R_aux):
        '''
        This will solve a 1phase problem

        Parameters
        ----------
        Pin_r : float
            inlet pressure to the segment.
        hin_r : float
            inlet enthalpy to the segment.
        L : float
            length of the segment.
        correlations : class
            fin-tube correlations class.
        geometry : class
            fin-tube geometry class style.
        thermal : class
            fin-tube thermal class style.
        R_aux : float
            auxillary thermal resistance.

        Raises
        ------
        ValueError
            if outlet pressure became negative, then pressure drop is very high.

        Returns
        -------
        Pout_r : float
            outlet pressure from the segment.
        hout_r : float
            outlet enthalpy from the segment.
        Charge : float
            total charge in the segment.

        '''
        eps = np.finfo(float).eps
        # defining some necessary parameters
        mdot_r = self.mdot_r
        A_r = geometry.inner_circum * L
        AS = self.AS
        ID = geometry.ID
        T_sur = self.T_sur
        
        # getting refrgierant inlet temperature
        AS.update(CP.HmassP_INPUTS, hin_r, Pin_r)
        Tin_r = AS.T()

        # defining mode
        if Tin_r > T_sur: # heating air
            mode = 'heater'
            Tout_r = T_sur + 1
        else: # cooling air
            mode = 'cooler'
            Tout_r = T_sur - 1

        # updating state
        correlations.update(AS, geometry, thermal, '1phase',Pin_r, hin_r, mdot_r, A_r, mode)
        
        # calculating refrigerant heat transfer coefficient
        h_r_1phase = correlations.calculate_h_1phase()
        # calculating refrigerant thermal resistance
        Rin = 1 / (h_r_1phase * pi * ID)
        
        # calculating heat transfer
        UA = 1 / (Rin + R_aux) * L
        hout_r = hin_r
        Q = 0
        error = 100
        while error > self.Q_error_tol:
            Q_old = Q
            # looping to get correct outlet refrigerant temperature
            DT1 = T_sur - Tin_r
            DT2 = T_sur - Tout_r
            LMTD = (DT1 - DT2) / log(DT1/(DT2+eps))
            Q = UA * LMTD
            Q *= self.HT_tuning
            error = abs(Q - Q_old) / abs(Q+eps)
            hout_r = Q / mdot_r + hin_r
            AS.update(CP.HmassP_INPUTS,hout_r,Pin_r)
            Tout_r = AS.T()
        
        # updating state
        correlations.update(AS, geometry, thermal, '1phase',Pin_r, hin_r, mdot_r, A_r, mode, var_2nd_out=hout_r)
        dpdz_1phase = correlations.calculate_dPdz_f_1phase()
        dpdz_1phase *= self.DP_tuning
        Pout_r = Pin_r + dpdz_1phase * L
        if Pout_r <= 0:
            raise ValueError("Outlet pressure from the segment is negative, pressure drop is very high")

        # calculating charge
        AS.update(CP.HmassP_INPUTS,hin_r,Pin_r)
        rho_1phase = AS.rhomass()
        Charge = rho_1phase * geometry.A_CS * L
        
        return Pout_r, hout_r, Charge
        
    def solve_2phase(self,Pin_r,hin_r,L,correlations,geometry,thermal,R_aux):
        '''
        This will solve a 2phase problem

        Parameters
        ----------
        Pin_r : float
            inlet pressure to the segment.
        hin_r : float
            inlet enthalpy to the segment.
        L : float
            length of the segment.
        correlations : class
            fin-tube correlations class.
        geometry : class
            fin-tube geometry class style.
        thermal : class
            fin-tube thermal class style.
        R_aux : float
            auxillary thermal resistance.

        Raises
        ------
        ValueError
            if outlet pressure became negative, then pressure drop is very high.

        Returns
        -------
        Pout_r : float
            outlet pressure from the segment.
        hout_r : float
            outlet enthalpy from the segment.
        Charge : float
            total charge in the segment.

        '''
        eps = np.finfo(float).eps
        # defining some necessary parameters
        mdot_r = self.mdot_r
        A_r = geometry.inner_circum * L
        AS = self.AS
        ID = geometry.ID
        T_sur = self.T_sur
        
        # getting refrgierant inlet temperature
        AS.update(CP.HmassP_INPUTS, hin_r, Pin_r)
        Tin_r = AS.T()

        # defining mode
        if Tin_r > T_sur: # heating air
            mode = 'heater'
        else: # cooling air
            mode = 'cooler'
        
        # getting inlet quality
        AS.update(CP.PQ_INPUTS, Pin_r, 0.0)
        hL = AS.hmass()
        AS.update(CP.PQ_INPUTS, Pin_r, 1.0)
        hV = AS.hmass()
        xin_r = (hin_r - hL) / (hV - hL)
        if xin_r < 0: # this should not happen
            xin_r = 0
        elif xin_r > 1.0: # this should not happen
            xin_r = 1.0
        
        # updating state
        xout_r = xin_r
        Pout_r = Pin_r
        error = 100
        Q = 0
        while error > self.Q_error_tol:
            Q_old = Q
            # calculating approximate q_flux assuming infinite heat transfer coefficing of 2phase refrigerant
            UA_approx = 1 / R_aux * L
            q_flux_approx = UA_approx * (T_sur - Tin_r) / (geometry.inner_circum * L)
            correlations.update(AS, geometry, thermal, '2phase',Pin_r, xin_r, mdot_r, A_r, mode,q_flux=q_flux_approx,var_2nd_out=xout_r)
            
            # calculating refrigerant heat transfer coefficient
            h_r_2phase = correlations.calculate_h_2phase()
    
            # calculating refrigerant thermal resistance
            Rin = 1 / (h_r_2phase * pi * ID)
            
            # calculating heat transfer
            UA = 1 / (Rin + R_aux) * L
            Q = UA * (T_sur - Tin_r)
            Q *= self.HT_tuning
            hout_r = Q / mdot_r + hin_r
            
            correlations.update(AS, geometry, thermal, '2phase',Pin_r, xin_r, mdot_r, A_r, mode,var_2nd_out=xout_r)
            dpdz_2phase = correlations.calculate_dPdz_f_2phase()
            dpdz_2phase *= self.DP_tuning
            Pout_r = Pin_r + dpdz_2phase * L
            if Pout_r <= 0:
                raise ValueError("Outlet pressure from the segment is negative, pressure drop is very high")
            AS.update(CP.PQ_INPUTS, Pout_r, 0.0)
            hL = AS.hmass()
            AS.update(CP.PQ_INPUTS, Pout_r, 1.0)
            hV = AS.hmass()
            xout_r = (hout_r - hL) / (hV - hL)
            
            # calculating error in Q
            error = abs(Q - Q_old) / abs(Q+eps)
        
        # calculating charge
        AS.update(CP.HmassP_INPUTS,hout_r,Pout_r)
        Tout_r = AS.T()
        AS.update(CP.PQ_INPUTS,Pin_r,0.0)
        Tbubble = AS.T()
        AS.update(CP.PQ_INPUTS,Pin_r,1.0)
        Tdew = AS.T()
        if xout_r <= 0:
            xout_r = np.finfo(float).eps
        elif xout_r >= 1.0:
            xout_r = 1.0 - np.finfo(float).eps
        if xin_r <= 0:
            xin_r = np.finfo(float).eps
        elif xin_r >= 1.0:
            xin_r = 1.0 - np.finfo(float).eps
        correlations.update(AS, geometry, thermal, '2phase',Pin_r, xin_r, mdot_r, A_r, mode,var_2nd_out=xout_r)
        rho_2phase = correlations.calculate_rho_2phase()
        Charge = rho_2phase * geometry.A_CS * L

        return Pout_r, hout_r, Charge

if __name__=='__main__':
    import time
    def f1():
        global Line
        AS = CP.AbstractState("HEOS",'R22')
        Pin_r = 10 * 101325

        DT = -5
        AS.update(CP.PQ_INPUTS,Pin_r,0.0)
        Tdew = AS.T()
        AS.update(CP.PT_INPUTS,Pin_r,Tdew+DT)
        hin_r = AS.hmass()

        for i in range(1):
            kwds={
                  'name':"Generic Line",
                  'AS': AS,
                  'Pin_r': Pin_r,
                  'hin_r': hin_r,
                  'L': 10,
                  'ID': 0.02,
                  'OD': 0.0254,
                  'k_line': 385,
                  'k_ins': 0.036,
                  't_ins': 0.01,
                  'T_sur': 40 + 273.15,
                  'h_sur': 120,
                  'e_D': 0.005,
                  'Nsegments': 20,
                  'mdot_r': 0.05,
                  'Q_error_tol':0.001,
                  'DP_tuning':1.0,
                  'HT_tuning':1.0,
                  'N_90_bends':0,
                  'N_180_bends':0,
                  }
            Line = LineClass(**kwds)
            Line.Calculate()
    def f2():
        global Line
        AS = CP.AbstractState("HEOS",'R22')
        Pin_r = 4 * 101325

        AS.update(CP.PQ_INPUTS,Pin_r,0.1)
        hin_r = AS.hmass()

        for i in range(1):
            kwds={
                  'name':"Generic Line",
                  'AS': AS,
                  'Pin_r': Pin_r,
                  'hin_r': hin_r,
                  'L': 10,
                  'ID': 0.008,
                  'OD': 0.009,
                  'k_line': 1,
                  'k_ins': 1,
                  't_ins': 0,
                  'T_sur': 1,
                  'h_sur': 0,
                  'e_D': 0,
                  'Nsegments': 20,
                  'mdot_r': 56/3600,
                  'Q_error_tol':0.001,
                  'DP_tuning':1.0,
                  'HT_tuning':0.0,
                  'N_90_bends':2,
                  'N_180_bends':3,
                  }
            Line = LineClass(**kwds)
            Line.Calculate()
    T1 = time.time()
    f1()
    print("total time:",time.time() - T1, "s")
    print(*Line.OutputList(),sep="\n")
    