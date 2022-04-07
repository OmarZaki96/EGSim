
from __future__ import division, print_function, absolute_import
import sys,os
path = os.path.join(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(path)
import numpy as np
import CoolProp as CP
from backend.Capillary import CapillaryClass
from backend.CompressorAHRI import CompressorAHRIClass
from backend.CompressorPHY import CompressorPHYClass
from backend.FinTubeHEX import FinTubeHEXClass
from backend.Line import LineClass
from backend.MicroChannelHEX import MicroChannelHEXClass
import time
from backend.Preconditioner import precondition_TXV, precondition_capillary
from GUI_functions import load_refrigerant_list
import random
from backend.cycle_solvers import main_solver
from backend.ranges_creator import create_ranges
from backend.Functions import get_AS
from time import sleep

class ValuesClass():
    pass

class CycleClass():
    """
    Cycle class, used to solve a cycle consisting of several components
    
    Required Parameters:
    
    ===========    ==========  ========================================================================
    Variable       Units       Description
    ===========    ==========  ========================================================================
    Components     --          a list of classes of different components
    ===========   ==========  ========================================================================
    
    """
    def __init__(self,**kwargs):
        #Load up the parameters passed in
        # using the dictionary
        self.Create_ranges = False
        self.__dict__.update(kwargs)
        self.Line_Liquid = LineClass()
        self.Line_Suction = LineClass()
        self.Line_Discharge = LineClass()
        self.Line_2phase = LineClass()

    def Update(self,**kwargs):
        #Update the parameters passed in
        # using the dictionary
        self.__dict__.update(kwargs)
        if self.Compressor_Type == "AHRI":
            self.Compressor = CompressorAHRIClass()
        elif self.Compressor_Type == "Physics":
            self.Compressor = CompressorPHYClass()
        elif self.Compressor_Type == "AHRI-map":
            self.Compressor = CompressorAHRIClass()
        else:
            raise Exception("Please define compressor type")
        
        if self.Condenser_Type == "Fin-tube":
            self.Condenser = FinTubeHEXClass()
        elif self.Condenser_Type == "MicroChannel":
            self.Condenser = MicroChannelHEXClass()
        else:
            raise Exception("Please define consdenser type")

        if self.Evaporator_Type == "Fin-tube":
            self.Evaporator = FinTubeHEXClass()
        elif self.Evaporator_Type == "MicroChannel":
            self.Evaporator = MicroChannelHEXClass()
        else:
            raise Exception("Please define evaporator type")            
        
        if self.Expansion_Device_Type == 'TXV':
            self.cond1_value = self.SH_value
            if self.Superheat_Type == 'Evaporator':
                self.cond1 = 'superheat_evap'
            elif self.Superheat_Type == 'Compressor':
                self.cond1 = 'superheat_comp'
            else:
                raise Exception("Please define superheat condition type")
        elif self.Expansion_Device_Type == 'Capillary':
            self.Capillary = CapillaryClass()
            self.cond1 = 'capillary'
        else:
            raise Exception("Please defing expansion device type")
        
        if self.Second_Cond == 'Subcooling':
            self.cond2_value = self.SC_value
            self.cond2 = 'subcooling'
        elif self.Second_Cond == 'Charge':
            self.cond2 = 'charge'
            self.cond2_value = self.Charge_value * (1 - self.Accum_charge_per)
        else:
            raise Exception("Please define second condition")
        
        self.ref_list = load_refrigerant_list()
        if not self.ref_list[0]:
            raise
        self.ref_list = self.ref_list[1]
                        
    def OutputList(self):
        if self.Mode == "AC":
            condenser_name = "Outdoor Unit"
            evaporator_name = "Indoor Unit"
        elif self.Mode == "HP":
            condenser_name = "Indoor Unit"
            evaporator_name = "Outdoor Unit"
        
        """
            Return a list of parameters for this component for further output
            
            It is a list of tuples, and each tuple is formed of items with indices:
                [0] Description of value
                
                [1] Units of value
                
                [2] The value itself
        """
        
        output_list_1 = [('Solved?','','Yes'),
                        ('Solver Error','',''),
                        ('','',''),
                        ('Refrigerant','',self.Ref),
                        ('','',''),
                        ('System Capacity','W',self.Results.Capacity),
                        ('System Power','W',self.Results.Power),
                        ('','',''),
                        ('Cycle Charge','kg',self.Results.Charge_cycle),
                        ('Accumulator Charge','kg',self.Results.Charge_accum),
                        ('System Charge','kg',self.Results.Charge_system),
                        ('','',''),
                        ('Cycle Condensing Temperature','C',self.Results.Tdew_cond-273.15),
                        ('Cycle Evaporating Temperature','C',self.Results.Tdew_evap-273.15),
                        ('','',''),
                        ('Cycle COP','W/W',self.Results.COP),
                        ('System COP','W/W',self.Results.COP_S),
                        ('','',''),
                        ('Refrigerant Mass Flow Rate','kg/s',self.Results.mdot_r),
                        ('','',''),
                        (condenser_name+' Subcooling','K',self.Condenser.Results.SC),
                        (evaporator_name+' Superheat','K',self.Evaporator.Results.SH),
                        ('Compressor Superheat','K',self.Results.Compressor_SH),
                        ('','',''),
                        (condenser_name+' TTD','K',self.Condenser.Results.TTD),
                        (evaporator_name+' TTD','K',self.Evaporator.Results.TTD),
                        ('','',''),
                        ('Energy Balance','W',self.Results.Energy_balance)
                        ]
        
        if self.Expansion_Device_Type == "TXV":
            output_list_2_1 = [('Expansion Device','-','TXV'),
                               ('Superheat Value','K',self.SH_value),
                               ]
            if self.Superheat_Type == "Evaporator":
                output_list_2_2 = [('Superheat location','-',evaporator_name+' Exit'),
                                   ('','',''),
                                   ]
            elif self.Superheat_Type == "Compressor":
                output_list_2_2 = [('Superheat location','-','Compressor Inlet'),
                                   ('','',''),
                                   ]
            output_list_2 = output_list_2_1 + output_list_2_2
        
        elif self.Expansion_Device_Type == "Capillary":
            output_list_2 = [('Expansion Device','-','Capillary'),
                             ('','',''),
                            ]
        
        if self.Second_Cond == "Subcooling":
            output_list_3 = [('Second Condition Type','-','Subcooling'),
                             ('Subcooling Value','K',self.cond2_value),
                            ]
        elif self.Second_Cond == "Charge":
            output_list_3 = [('Second Condition Type','-','Charge'),
                             ('Charge Value','Kg',self.cond2_value),
                            ]
        if self.Mode == 'HP':
            output_list_4 = [
                             ('','',''),
                             ('Cycle mode','-','Heat pump'),
                             ('Test Condition','',self.Test_cond),
                             ('','',''),
                             ]
        elif self.Mode == 'AC':
            output_list_4 = [
                             ('','',''),
                             ('Cycle mode','-','Air conditioning'),
                             ('Test Condition','',self.Test_cond),
                             ('','',''),
                             ]

        output_list_5 = [('','',''),
                         ('Solver','',self.solver),
                         ('Solving time','s',self.solving_time),
                         ('','',''),
                         ]
        
        output_list = output_list_1 + output_list_2 + output_list_3 + output_list_4 + output_list_5
        
        return output_list

    def Calculate_type_1(self,DT_evap,DT_cond):
        """
        type_1 is used for superheat at evaporator with subcooling or charge
        
        Inputs are differences in temperature [K] between HX air inlet temperature 
        and the dew temperature for the heat exchanger.
        
        Required Inputs:
            DT_evap: 
                Difference in temperature [K] between evaporator air inlet temperature and refrigerant dew temperature
            DT_cond:
                Difference in temperature [K] between condenser air inlet temperature and refrigeant dew temperature
        """        

        #AbstractState
        # if converger, just return zeros
        if self.converged:
            return (0,0)
        
        if hasattr(self,"check_terminate"): #used to terminate run in GUI
            if self.check_terminate:
                self.Solver_Error = "User terminated run"
                raise
        AS = self.AS
        #Condenser and evaporator dew temperature (guess)
        Tdew_cond = self.Condenser.Tin_a + DT_cond
        Tdew_evap = self.Evaporator.Tin_a - DT_evap
        #Condenser and evaporator saturation pressures

        DT_sh = self.SH_value

        try:
            AS.update(CP.QT_INPUTS,1.0,Tdew_cond)
            psat_cond=AS.p() #[Pa]
            AS.update(CP.QT_INPUTS,1.0,Tdew_evap)
            psat_evap=AS.p() #[Pa]

            Pin_suction = psat_evap-(self.DP_evap+self.DP_2phase)
            AS.update(CP.PQ_INPUTS,Pin_suction,1.0)
            Tin_suction = AS.T() + DT_sh

            # inlet enthalpy to suction line
            AS.update(CP.PT_INPUTS,Pin_suction, Tin_suction)
            hin_suction = AS.hmass()

        except:
            self.Solver_Error = "Failed to solve cycle, guessing saturation temperatures diverged. Try another solver or change initial guess for saturation temperatures."
            raise
        
        
        self.Tdew_cond = Tdew_cond
        self.Tdew_evap = Tdew_evap
        
        if (not hasattr(self.Compressor,'mdot_r')) or self.Compressor.mdot_r<0.00001:
            # The first run of model, run the compressor just so you can get a preliminary value 
            # for the mass flow rate for the line set 
            params={
                'Pin_r': psat_evap-self.DP_low,   
                'Pout_r': psat_cond+self.DP_high,
                'hin_r': hin_suction,
                'AS': AS,
            }
            self.Compressor.Update(**params)
            try:
                self.Compressor.Calculate()
            except:
                self.Solver_Error = "Failed to solve compressor!"
        
        #solve suction line
        params={
            'Pin_r': Pin_suction,
            'hin_r': hin_suction,
            'mdot_r': self.Compressor.mdot_r,
            'AS':  AS,
        }
        self.Line_Suction.Update(**params)
        try:
            self.Line_Suction.Calculate()
        except:
            self.Solver_Error = "Failed to solve suction line!"
            
        # solve compressor
        params={
            'Pin_r': psat_evap - self.DP_low,
            'Pout_r': psat_cond + self.DP_high,
            'hin_r': self.Line_Suction.Results.hout_r,
            'AS': AS,
        }
        self.Compressor.Update(**params)
        try:
            self.Compressor.Calculate()
        except:
            self.Solver_Error = "Failed to solve compressor!"

        # solve Discharge line
        params={
                'Pin_r': psat_cond+self.DP_high,
                'hin_r': self.Compressor.hout_r,
                'mdot_r': self.Compressor.mdot_r,
                'AS':AS,
            }
        
        self.Line_Discharge.Update(**params)
        try:
            self.Line_Discharge.Calculate()
        except:
            self.Solver_Error = "Failed to solve discharge line!"
        
        # solve condenser
        params={
                'Pin_r': psat_cond+self.DP_cond+self.DP_liquid,
                'hin_r': self.Line_Discharge.Results.hout_r,                        
                'mdot_r': self.Compressor.mdot_r,
                'AS':AS,
            }
        self.Condenser.Update(**params)
        try:
            self.Condenser.solve()
        except:
            if hasattr(self.Condenser,"Solver_Error"):
                self.Solver_Error = self.Condenser.Solver_Error + "condenser"
            else:
                self.Solver_Error = "Failed to solve condenser!"
        
        # solving liquid line
        params={
                'Pin_r': psat_cond+self.DP_liquid,
                'hin_r': self.Condenser.Results.hout_r,
                'mdot_r': self.Compressor.mdot_r,
                'AS':AS,
            }
        
        self.Line_Liquid.Update(**params)
        try:
            self.Line_Liquid.Calculate()
        except:
            self.Solver_Error = "Failed to solve liquid line!"
        
        # solving 2phase line if enabled
        params={
                'Pin_r': psat_evap,
                'hin_r': self.Line_Liquid.Results.hout_r,
                'mdot_r': self.Compressor.mdot_r,
                'AS': AS,
            }
        self.Line_2phase.Update(**params)
        try:
            self.Line_2phase.Calculate()
        except:
            self.Solver_Error = "Failed to solve two-phase line!"
        
        # solving evaporator
        params={
                'Pin_r':psat_evap-self.DP_2phase,
                'hin_r':self.Line_2phase.Results.hout_r,
                'mdot_r':self.Compressor.mdot_r,
                'AS':AS,
            }
        
        self.Evaporator.Update(**params)
        try:
            self.Evaporator.solve()
        except:
            if hasattr(self.Evaporator,"Solver_Error"):
                self.Solver_Error = self.Evaporator.Solver_Error + "evaporator"
            else:
                self.Solver_Error = "Failed to solve evaporator!"
                                
        self.DP_HighPressure= abs(self.Condenser.Results.DP_r + self.Line_Discharge.Results.DP_r + self.Line_Liquid.Results.DP_r)
        
        self.DP_LowPressure= abs(self.Evaporator.Results.DP_r + self.Line_Suction.Results.DP_r + self.Line_2phase.Results.DP_r)
        
        # creating residuals list
        resid = np.zeros((2))
        
        # evaporator residual
        evaporator_residual = self.Compressor.mdot_r * (self.Evaporator.Results.hout_r - self.Line_Suction.Results.hin_r)
        resid[0] = evaporator_residual
                
        # condenser residual
        if self.Second_Cond == 'Subcooling':
            AS.update(CP.PQ_INPUTS,self.Condenser.Results.Pout_r,0.0)
            Tdew_out = AS.T()
            AS.update(CP.PT_INPUTS,self.Condenser.Results.Pout_r,Tdew_out - self.cond2_value)
            h_subcool_req = AS.hmass()
            resid[1] = self.Compressor.mdot_r * (self.Condenser.Results.hout_r - h_subcool_req)
            if hasattr(self,"update_residuals") and self.update_residuals != None: # sending reisudals to main UI
                self.update_residuals.emit((self.iter,resid[1],evaporator_residual,None,None,None))

            if (abs(resid[1]) < self.energy_tol) and (abs(resid[0]) < self.energy_tol):
                self.converged = True

        elif self.Second_Cond == 'Charge':
            Charge = self.Evaporator.Results.Charge + self.Condenser.Results.Charge + self.Line_Liquid.Results.Charge + self.Line_Suction.Results.Charge + self.Line_Discharge.Results.Charge + self.Line_Discharge.Results.Charge
            resid[1] = self.cond2_value - Charge
            if hasattr(self,"update_residuals") and self.update_residuals != None: # sending reisudals to main UI
                self.update_residuals.emit((self.iter,None,evaporator_residual,None,resid[1],None))

            if (abs(resid[1]) < self.mass_tol) and (abs(resid[0]) < self.energy_tol):
                self.converged = True

        
        self.DT_evap = DT_evap
        self.DT_cond = DT_cond
        self.iter += 1
        return resid

    def Calculate_type_2(self,DT_evap,DT_cond):
        """
        type_2 is used for superheat at compressor with subcooling or charge
        
        Inputs are differences in temperature [K] between HX air inlet temperature 
        and the dew temperature for the heat exchanger.
        
        Required Inputs:
            DT_evap: 
                Difference in temperature [K] between evaporator air inlet temperature and refrigerant dew temperature
            DT_cond:
                Difference in temperature [K] between condenser air inlet temperature and refrigeant dew temperature
        """        
        if self.converged:
            return (0,0)

        #AbstractState
        if hasattr(self,"check_terminate"): #used to terminate run in GUI
            if self.check_terminate:
                self.Solver_Error = "User terminated run"
                raise
        AS = self.AS
        #Condenser and evaporator dew temperature (guess)
        Tdew_cond=self.Condenser.Tin_a+DT_cond
        Tdew_evap=self.Evaporator.Tin_a-DT_evap        
        #Condenser and evaporator saturation pressures
        
        DT_sh = self.SH_value

        try:
            AS.update(CP.QT_INPUTS,1.0,Tdew_cond)
            psat_cond=AS.p() #[Pa]
            AS.update(CP.QT_INPUTS,1.0,Tdew_evap)
            psat_evap=AS.p() #[Pa]

            AS.update(CP.PQ_INPUTS,psat_evap-self.DP_low,1.0)
            Tin_comp=AS.T() + DT_sh
                
            # inlet enthalpy to compressor
            AS.update(CP.PT_INPUTS,psat_evap-self.DP_low, Tin_comp)
            hin_comp = AS.hmass()

        except:
            self.Solver_Error = "Failed to solve cycle, guessing saturation temperatures diverged. Try another solver or change initial guess for saturation temperatures."
            raise

        self.Tdew_cond=Tdew_cond
        self.Tdew_evap=Tdew_evap
        
        # solve compressor
        params={
            'Pin_r': psat_evap-self.DP_low,   
            'Pout_r': psat_cond+self.DP_high,
            'hin_r': hin_comp,
            'AS': AS,
        }
        
        self.Compressor.Update(**params)
        try:
            self.Compressor.Calculate()
        except:
            self.Solver_Error = "Failed to solve compressor!"

        # solve Discharge line
        params={
                'Pin_r': psat_cond+self.DP_high,
                'hin_r': self.Compressor.hout_r,
                'mdot_r': self.Compressor.mdot_r,
                'AS':AS,
            }
        
        self.Line_Discharge.Update(**params)
        try:
            self.Line_Discharge.Calculate()
        except:
            self.Solver_Error = "Failed to solve discharge line!"
        
        # solve condenser            
        params={
                'Pin_r': psat_cond+self.DP_cond+self.DP_liquid,
                'hin_r': self.Line_Discharge.Results.hout_r,                        
                'mdot_r': self.Compressor.mdot_r,
                'AS':AS,
            }
        self.Condenser.Update(**params)
        try:
            self.Condenser.solve()
        except:
            if hasattr(self.Condenser,"Solver_Error"):
                self.Solver_Error = self.Condenser.Solver_Error + "condenser"
            else:
                self.Solver_Error = "Failed to solve condenser!"
        
        # solving liquid line
        params={
                'Pin_r': psat_cond+self.DP_liquid,
                'hin_r': self.Condenser.Results.hout_r,
                'mdot_r': self.Compressor.mdot_r,
                'AS':AS,
            }
        
        self.Line_Liquid.Update(**params)
        try:
            self.Line_Liquid.Calculate()
        except:
            self.Solver_Error = "Failed to solve liquid line!"
        
        # solving 2phase line
        params={
                'Pin_r': psat_evap,
                'hin_r': self.Line_Liquid.Results.hout_r,
                'mdot_r': self.Compressor.mdot_r,
                'AS': AS,
            }
        self.Line_2phase.Update(**params)
        try:
            self.Line_2phase.Calculate()
        except:
            self.Solver_Error = "Failed to solve two-phase line!"
        
        # solving evaporator
        params={
                'Pin_r':psat_evap-self.DP_2phase,
                'hin_r':self.Line_2phase.Results.hout_r,
                'mdot_r':self.Compressor.mdot_r,
                'AS':AS,
            }
        self.Evaporator.Update(**params)
        try:
            self.Evaporator.solve()
        except:
            if hasattr(self.Evaporator,"Solver_Error"):
                self.Solver_Error = self.Evaporator.Solver_Error + "evaporator"
            else:
                self.Solver_Error = "Failed to solve evaporator!"

        #solve suction line
        params={
            'Pin_r': psat_evap-(self.DP_evap+self.DP_2phase),
            'hin_r': self.Evaporator.Results.hout_r,
            'mdot_r': self.Compressor.mdot_r,
            'AS':  AS,
        }
        self.Line_Suction.Update(**params)
        try:
            self.Line_Suction.Calculate()
        except:
            self.Solver_Error = "Failed to solve suction line!"
                                
        self.DP_HighPressure= abs(self.Condenser.Results.DP_r + self.Line_Discharge.Results.DP_r + self.Line_Liquid.Results.DP_r)
        
        self.DP_LowPressure= abs(self.Evaporator.Results.DP_r + self.Line_Suction.Results.DP_r + self.Line_2phase.Results.DP_r)
        
        # creating residuals list
        resid = np.zeros((2))
        
        # evaporator residual
        evaporator_residual = self.Compressor.mdot_r * (self.Line_Suction.Results.hout_r - self.Compressor.hin_r)
        resid[0] = evaporator_residual
                
        # condenser residual
        if self.Second_Cond == 'Subcooling':
            AS.update(CP.PQ_INPUTS,self.Condenser.Results.Pout_r,0.0)
            Tdew_out = AS.T()
            AS.update(CP.PT_INPUTS,self.Condenser.Results.Pout_r,Tdew_out - self.cond2_value)
            h_subcool_req = AS.hmass()
            resid[1] = self.Compressor.mdot_r * (self.Condenser.Results.hout_r - h_subcool_req)
            if hasattr(self,"update_residuals") and self.update_residuals != None: # sending reisudals to main UI
                self.update_residuals.emit((self.iter,resid[1],evaporator_residual,None,None,None))

            if (abs(resid[1]) < self.energy_tol) and (abs(resid[0]) < self.energy_tol):
                self.converged = True

        elif self.Second_Cond == 'Charge':
            Charge = self.Evaporator.Results.Charge + self.Condenser.Results.Charge + self.Line_Liquid.Results.Charge + self.Line_Suction.Results.Charge + self.Line_Discharge.Results.Charge + self.Line_Discharge.Results.Charge
            resid[1] = self.cond2_value - Charge
            if hasattr(self,"update_residuals") and self.update_residuals != None: # sending reisudals to main UI
                self.update_residuals.emit((self.iter,None,evaporator_residual,None,resid[1],None))

            if (abs(resid[1]) < self.mass_tol) and (abs(resid[0]) < self.energy_tol):
                self.converged = True
                
        self.DT_evap = DT_evap
        self.DT_cond = DT_cond
        self.iter += 1
        return resid

    def PreconditionedSolve_TXV(self,solver):
        """
        Used to solve a cycle with TXV expansion device, whether with subcooling
        or with charge second condition
        
        Solver that will precondition by trying a range of DeltaT until the model
        can solve, then will kick into the chosen solver by the user
        
        The two input variables for the system solver are the differences in 
        temperature between the inlet air temperature of the heat exchanger and the
        dew temperature of the refrigerant.  This is important for refrigerant blends
        with temperature glide during constant-pressure evaporation or condensation.
        Good examples of common working fluid with glide would be R404A or R410A.
        """
        T1 = time.time()
        def OBJECTIVE_type_1(x): # superheat at evaporator exit
            """
            A wrapper function to convert input vector for fsolve to the proper form for the solver
            """
            try:
                resids=self.Calculate_type_1(DT_evap=float(x[0]),DT_cond=float(x[1]))
            except ValueError:
                raise
            return resids

        def OBJECTIVE_type_2(x): # superheat at compressor inlet
            """
            A wrapper function to convert input vector for fsolve to the proper form for the solver
            """
            try:
                resids=self.Calculate_type_2(DT_evap=float(x[0]),DT_cond=float(x[1]))
            except:
                raise Exception("failed to run")
            return resids
        
        if self.cond1 == 'superheat_evap':
            objective = OBJECTIVE_type_1
        elif self.cond1 == 'superheat_comp':
            objective = OBJECTIVE_type_2
        
        if not (self.Tevap_init_manual and self.Tcond_init_manual):
            # Use the preconditioner to determine a reasonably good starting guess
            found = False
            epsilon = 0.8
            i = 0
            while not found and i < 50:
                i += 1
                try:
                    DT_evap_init,DT_cond_init,DT_sh_init=precondition_TXV(self, epsilon=epsilon)
                    found = True
                except:
                    epsilon = random.uniform(0.4, 0.98)
                                    
            if not found:
                DT_evap_init = 15
                DT_cond_init = 7
                DT_sh_init = 7

        if (len(self.AS.fluid_names()) == 1) and self.AS.fluid_names()[0] == "R32":
            DT_evap_init = self.Evaporator.Tin_a - 280
            DT_cond_init = 323 - self.Condenser.Tin_a
            
        if self.Tevap_init_manual:
            DT_evap_init  = self.Evaporator.Tin_a - self.Tevap_init
        
        if self.Tcond_init_manual:
            DT_cond_init = self.Tcond_init - self.Condenser.Tin_a

        GoodRun=False
        i = 0
        self.iter = 0
        
        try:
            Tmin = self.AS.Ttriple()
            Tmax = self.AS.T_critical()
        except:
            Tmin = self.AS.Tmin()
            Tmax = self.AS.Tmax()
        
        DT_evap_max = self.Evaporator.Tin_a - Tmin
        DT_evap_min = 0
        DT_cond_max = Tmax - self.Condenser.Tin_a
        DT_cond_min = 0
        
        while GoodRun == False:
            try:
                self.DP_low=0
                self.DP_high=0
                self.resid_pressure = None
                self.DP_evap = 0
                self.DP_suction = 0
                self.DP_discharge = 0
                self.DP_cond = 0
                self.DP_liquid = 0
                self.DP_2phase = 0
                DP_converged=False        
                while DP_converged == False:
                    self.converged = False


                    # for correlations selection algorithm in fintube
                    # to use same correlations during energy iteration, we will impose 
                    # the already chosen correlation for the rest of energy iteration
                    # unless a correlation is already imposed
                    if self.Condenser_Type == "Fin-tube":
                        Cond_h_imposed_array = []
                        for circuit in self.Condenser.Circuits:
                            if circuit.Correlations.imposed_h_2phase:
                                Cond_h_imposed_array.append(True) # a correlation is already imposed
                            else:
                                Cond_h_imposed_array.append(False) # No correlation was imposed
                                if not circuit.Correlations.Selected_2phase_HTC:
                                    circuit.Correlations.Selected_2phase_HTC = True
                                    circuit.Correlations.h_corr_2phase = 1 # just use shah for first iteration
                                circuit.Correlations.imposed_h_2phase = True
                        Cond_DP_imposed_array = []
                        for circuit in self.Condenser.Circuits:
                            if circuit.Correlations.imposed_dPdz_f_2phase:
                                Cond_DP_imposed_array.append(True) # a correlation is already imposed
                            else:
                                Cond_DP_imposed_array.append(False) # No correlation was imposed
                                if not circuit.Correlations.Selected_2phase_DP:
                                    circuit.Correlations.Selected_2phase_DP = True
                                    circuit.Correlations.dPdz_f_corr_2phase = 6 # just use Friedel for first iteration
                                circuit.Correlations.imposed_dPdz_f_2phase = True
                    if self.Evaporator_Type == "Fin-tube":
                        Evap_h_imposed_array = []
                        for circuit in self.Evaporator.Circuits:
                            if circuit.Correlations.imposed_h_2phase:
                                Evap_h_imposed_array.append(True) # a correlation is already imposed
                            else:
                                Evap_h_imposed_array.append(False) # No correlation was imposed
                                if not circuit.Correlations.Selected_2phase_HTC:
                                    circuit.Correlations.Selected_2phase_HTC = True
                                    circuit.Correlations.h_corr_2phase = 2 # just use shah for first iteration
                                circuit.Correlations.imposed_h_2phase = True
                        Evap_DP_imposed_array = []
                        for circuit in self.Evaporator.Circuits:
                            if circuit.Correlations.imposed_dPdz_f_2phase:
                                Evap_DP_imposed_array.append(True) # a correlation is already imposed
                            else:
                                Evap_DP_imposed_array.append(False) # No correlation was imposed
                                if not circuit.Correlations.Selected_2phase_DP:
                                    circuit.Correlations.Selected_2phase_DP = True
                                    circuit.Correlations.dPdz_f_corr_2phase = 6 # just use Friedel for first iteration
                                circuit.Correlations.imposed_dPdz_f_2phase = True
                                    
                    try:
                        # run solver chosen by user
                        if solver.lower() == 'auto':
                            if self.cond1 == 'superheat_evap':
                                solver = "newton"
                            elif self.cond1 == 'superheat_comp':
                                solver = "least squares"
                        main_solver(objective,[DT_evap_init,DT_cond_init],max_iter=self.max_n_iterations,method = solver,bounds = ([DT_evap_min,DT_cond_min],[DT_evap_max,DT_cond_max]))
                    except:
                        pass
                        
                    # error in low pressure side
                    delta_low = abs(self.DP_low - abs(self.DP_LowPressure))
                    
                    # error in high pressure side
                    delta_high = abs(self.DP_high - abs(self.DP_HighPressure))
                    if self.resid_pressure != None:
                        resid_pressure_change = abs(self.resid_pressure - (delta_low + delta_high))
                    else:
                        resid_pressure_change = delta_low + delta_high
                    self.resid_pressure = delta_low + delta_high
                    if hasattr(self,"update_residuals") and self.update_residuals != None: # sending reisudals to main UI
                        self.update_residuals.emit((i,None,None,None,None,self.resid_pressure))
                    
                    # update old values (0.7 is underrelaxation factor)
                    self.DP_low += 0.7 * (abs(self.DP_LowPressure) - self.DP_low)
                    self.DP_high += 0.7 * (abs(self.DP_HighPressure) - self.DP_high)

                    self.DP_evap += 0.7 * (abs(self.Evaporator.Results.DP_r) - self.DP_evap)
                    self.DP_suction += 0.7 * (abs(self.Line_Suction.Results.DP_r) - self.DP_suction)
                    self.DP_discharge += 0.7 * (abs(self.Line_Discharge.Results.DP_r) - self.DP_discharge)
                    self.DP_cond += 0.7 * (abs(self.Condenser.Results.DP_r) - self.DP_cond)
                    self.DP_liquid += 0.7 * (abs(self.Line_Liquid.Results.DP_r) - self.DP_liquid)
                    self.DP_2phase += 0.7 * (abs(self.Line_2phase.Results.DP_r) - self.DP_2phase)
                    
                    #Update the guess values based on last converged values
                    DT_evap_init = self.DT_evap
                    DT_cond_init = self.DT_cond

                    if self.resid_pressure < self.pressure_tol or resid_pressure_change < 0.1 * self.pressure_tol:
                        DP_converged=True
                    GoodRun=True
                    i += 1
                    if i > self.max_n_iterations:
                        if not hasattr(self,"Error_message"):
                            self.Error_message = "Maximum number of iterations exceeded"

                    # for correlations selection algorithm in fintube
                    # to use same correlations during energy iteration, we will impose 
                    # the already chosen correlation for the rest of energy iteration
                    # unless a correlation is already imposed
                    # we will remove here the selected correlations to choose again next iteration
                    if self.Condenser_Type == "Fin-tube":
                        for i,circuit in enumerate(self.Condenser.Circuits):
                            if not Cond_h_imposed_array[i]:
                                circuit.Correlations.imposed_h_2phase = False
                            if not Cond_DP_imposed_array[i]:
                                circuit.Correlations.imposed_dPdz_f_2phase = False
                    if self.Evaporator_Type == "Fin-tube":
                        for i,circuit in enumerate(self.Evaporator.Circuits):
                            if not Evap_h_imposed_array[i]:
                                circuit.Correlations.imposed_h_2phase = False
                            if not Evap_DP_imposed_array[i]:
                                circuit.Correlations.imposed_dPdz_f_2phase = False

            except:
                self.CalculationTime = time.time() - T1
                if hasattr(self,"Error_message"):
                    return(0,self.Error_message)
                else:
                    return (0,"Could not solve the cycle.")
                
        self.CalculationTime = time.time() - T1
        if not self.converged:
            if not hasattr(self,"Solver_Error"):
                self.Solver_Error = "Energy or mass  did not converge. Error in subcooling, superheat or charge input."
            return (0,"Could not solve the cycle.")
        return (1,)

    def Calculate_type_3(self,DT_evap,DT_cond):
        """
        type_3 is used for capillary tube with subcooling or charge
        
        Inputs are differences in temperature [K] between HX air inlet temperature 
        and the dew temperature for the heat exchanger.
        
        Required Inputs:
            DT_evap: 
                Difference in temperature [K] between evaporator air inlet temperature and refrigerant dew temperature
            DT_cond:
                Difference in temperature [K] between condenser air inlet temperature and refrigeant dew temperature
        """

        # if converged, just return zeros
        if self.converged:
            return (0,0)
        
        if hasattr(self,"check_terminate"): #used to terminate run in GUI
            if self.check_terminate:
                self.Solver_Error = "User terminated run"
                raise
        
        # Abstract State
        AS = self.AS
        
        #Condenser and evaporator dew temperature (guess)
        Tdew_cond = self.Condenser.Tin_a + DT_cond
        Tdew_evap = self.Evaporator.Tin_a - DT_evap
        
        #Condenser and evaporator saturation pressures
        try:
            AS.update(CP.QT_INPUTS,1.0,Tdew_cond)
            psat_cond=AS.p() #[Pa]
            AS.update(CP.QT_INPUTS,1.0,Tdew_evap)
            psat_evap=AS.p() #[Pa]
        except:
            self.Solver_Error = "Failed to solve cycle, guessing saturation temperatures diverged. Try another solver or change initial guess for saturation temperatures."
            raise

        self.Tdew_cond = Tdew_cond
        self.Tdew_evap = Tdew_evap
        
        if self.Second_Cond == 'Subcooling':
            Pin_liquid = psat_cond + self.DP_liquid
            AS.update(CP.PQ_INPUTS,Pin_liquid,0.0)
            Tdew_out = AS.T()
            AS.update(CP.PT_INPUTS,Pin_liquid,Tdew_out - self.cond2_value)
            hin_r_liquid = AS.hmass()
            
        elif self.Second_Cond == 'Charge':
            Pin_liquid = psat_cond + self.DP_liquid
            if hasattr(self.Condenser,'Results'):
                hin_r_liquid = self.Condenser.Results.hout_r
            else:
                AS.update(CP.PQ_INPUTS,Pin_liquid,0.0)
                Tdew_out = AS.T()
                AS.update(CP.PT_INPUTS,Pin_liquid,Tdew_out - 5)
                hin_r_liquid = AS.hmass()
        
        if not hasattr(self.Capillary,'Results') or self.Capillary.Results.mdot_r < 0.00001:
            # The first run of model, run the Capillary just so you can get a preliminary value 
            # for the mass flow rate for the liquid line
            params={
                'Pin_r': psat_cond,
                'Pout_r_target': psat_evap,
                'hin_r': hin_r_liquid,
                'AS': AS,
            }
            self.Capillary.Update(**params)
            try:
                self.Capillary.Calculate()
            except:
                self.Solver_Error = "Failed to solve capillary tube!"

        # solving liquid line
        params={
                'Pin_r': Pin_liquid,
                'hin_r': hin_r_liquid,
                'mdot_r': self.Capillary.Results.mdot_r,
                'AS':AS,
            }
        self.Line_Liquid.Update(**params)
        try:
            self.Line_Liquid.Calculate()
        except:
            self.Solver_Error = "Failed to solve liquid line!"

        # solving capillary tube
        params={
            'Pin_r': psat_cond,
            'Pout_r_target': psat_evap,
            'hin_r': self.Line_Liquid.Results.hout_r,
            'AS': AS,
        }
        self.Capillary.Update(**params)
        try:
            self.Capillary.Calculate()
        except:
            self.Solver_Error = "Failed to solve capillary tube!"
        
        # solving 2phase line
        params={
                'Pin_r': psat_evap,
                'hin_r': self.Capillary.Results.hout_r,
                'mdot_r': self.Capillary.Results.mdot_r,
                'AS': AS,
            }
        self.Line_2phase.Update(**params)
        try:
            self.Line_2phase.Calculate()
        except:
            self.Solver_Error = "Failed to solve two-phase line!"

        # solving evaporator
        params={
                'Pin_r':psat_evap-self.DP_2phase,
                'hin_r':self.Line_2phase.Results.hout_r,
                'mdot_r':self.Capillary.Results.mdot_r,
                'AS':AS,
            }
        self.Evaporator.Update(**params)
        try:
            self.Evaporator.solve()
        except:
            if hasattr(self.Evaporator,"Solver_Error"):
                self.Solver_Error = self.Evaporator.Solver_Error + "evaporator"
            else:
                self.Solver_Error = "Failed to solve evaporator!"

        #solve suction line
        params={
            'Pin_r': psat_evap-(self.DP_2phase+self.DP_evap),
            'hin_r': self.Evaporator.Results.hout_r,
            'mdot_r': self.Capillary.Results.mdot_r,
            'AS':  AS,
        }
        self.Line_Suction.Update(**params)
        try:
            self.Line_Suction.Calculate()
        except:
            self.Solver_Error = "Failed to solve suction line!"
        
        # solve compressor
        params={
            'Pin_r': psat_evap - self.DP_low,
            'Pout_r': psat_cond + self.DP_high,
            'hin_r': self.Line_Suction.Results.hout_r,
            'AS': AS,
        }
        self.Compressor.Update(**params)
        try:
            self.Compressor.Calculate()
        except:
            self.Solver_Error = "Failed to solve compressor!"

        # solve Discharge line
        params={
                'Pin_r': psat_cond+self.DP_high,
                'hin_r': self.Compressor.hout_r,
                'mdot_r': self.Compressor.mdot_r,
                'AS':AS,
            }
        self.Line_Discharge.Update(**params)
        try:
            self.Line_Discharge.Calculate()
        except:
            self.Solver_Error = "Failed to solve discharge line!"
        
        # solve condenser
        params={
                'Pin_r': psat_cond+self.DP_cond+self.DP_liquid,
                'hin_r': self.Line_Discharge.Results.hout_r,                        
                'mdot_r': self.Compressor.mdot_r,
                'AS':AS,
            }
        self.Condenser.Update(**params)
        try:
            self.Condenser.solve()
        except:
            if hasattr(self.Condenser,"Solver_Error"):
                self.Solver_Error = self.Condenser.Solver_Error + "condenser"
            else:
                self.Solver_Error = "Failed to solve condenser!"
        
        self.DP_HighPressure = abs(self.Condenser.Results.DP_r + self.Line_Discharge.Results.DP_r + self.Line_Liquid.Results.DP_r)
        
        self.DP_LowPressure = abs(self.Evaporator.Results.DP_r + self.Line_Suction.Results.DP_r + self.Line_2phase.Results.DP_r)
        
        # creating residuals list
        resid = np.zeros((2))
        
        # mass flow rate residual
        mass_flowrate_residual = self.Compressor.mdot_r - self.Capillary.Results.mdot_r
        resid[0] = mass_flowrate_residual
                
        # condenser residual
        if self.Second_Cond == 'Subcooling':
            AS.update(CP.PQ_INPUTS,self.Condenser.Results.Pout_r,0.0)
            Tdew_out = AS.T()
            AS.update(CP.PT_INPUTS,self.Condenser.Results.Pout_r,Tdew_out - self.cond2_value)
            h_subcool_req = AS.hmass()
            resid[1] = self.Compressor.mdot_r * (self.Condenser.Results.hout_r - h_subcool_req)
            if hasattr(self,"update_residuals") and self.update_residuals != None: # sending reisudals to main UI
                self.update_residuals.emit((self.iter,resid[1],None,mass_flowrate_residual,None,None))

            if (abs(resid[1]) < self.energy_tol) and (abs(resid[0]) < self.mass_flowrate_tol):
                self.converged = True

        elif self.Second_Cond == 'Charge':
            Charge = self.Evaporator.Results.Charge + self.Condenser.Results.Charge + self.Line_Liquid.Results.Charge + self.Line_Suction.Results.Charge + self.Line_Discharge.Results.Charge + self.Line_Discharge.Results.Charge
            resid[1] = self.cond2_value - Charge
            if hasattr(self,"update_residuals") and self.update_residuals != None: # sending reisudals to main UI
                self.update_residuals.emit((self.iter,None,None,mass_flowrate_residual,resid[1],None))
            if (abs(resid[1]) < self.mass_tol) and (abs(resid[0]) < self.mass_flowrate_tol):
                self.converged = True
        
        self.DT_evap = DT_evap
        self.DT_cond = DT_cond
        self.iter += 1

        return resid

    def PreconditionedSolve_capillary(self,solver):
        """
        Used to solve a cycle with capillary expansion device, whether with subcooling
        or with charge second condition
        
        Solver that will precondition by trying a range of DeltaT until the model
        can solve, then will kick into the chosen solver by the user
        
        The two input variables for the system solver are the differences in 
        temperature between the inlet air temperature of the heat exchanger and the
        dew temperature of the refrigerant.  This is important for refrigerant blends
        with temperature glide during constant-pressure evaporation or condensation.
        Good examples of common working fluid with glide would be R404A or R410A.
        """
        
        def OBJECTIVE_type_3(x):
            """
            A wrapper function to convert input vector for fsolve to the proper form for the solver
            """
            try:
                resids=self.Calculate_type_3(DT_evap=float(x[0]),DT_cond=float(x[1]))
            except ValueError:
                raise
            return resids
        
        if not (self.Tevap_init_manual and self.Tcond_init_manual):
            # Use the preconditioner to determine a reasonably good starting guess
            found = False
            epsilon = 0.96
            i = 0
            while not found and i < 50:
                i += 1
                try:
                    DT_evap_init,DT_cond_init,DT_sh_init=precondition_capillary(self, epsilon=epsilon)
                    found = True
                except:
                    epsilon = random.uniform(0.7, 0.98)
            if not found:
                DT_evap_init = 15
                DT_cond_init = 7
                DT_sh_init = 1

        if self.Tevap_init_manual:
            DT_evap_init  = self.Evaporator.Tin_a - self.Tevap_init
        
        if self.Tcond_init_manual:
            DT_cond_init = self.Tcond_init - self.Condenser.Tin_a

        Tmin = self.AS.Ttriple()
        Tmax = self.AS.T_critical()
        
        DT_evap_max = self.Evaporator.Tin_a - Tmin
        DT_evap_min = 0
        DT_cond_max = Tmax - self.Condenser.Tin_a
        DT_cond_min = 0
        
        GoodRun=False
        i = 0
        self.iter = 0
        while GoodRun == False:
            try:
                self.DP_low=0
                self.DP_high=0
                self.DP_evap = 0
                self.DP_suction = 0
                self.DP_discharge = 0
                self.DP_cond = 0
                self.DP_liquid = 0
                self.DP_2phase = 0
                self.resid_pressure = None
                DP_converged=False        
                while DP_converged == False:
                    self.converged = False
                    
                    # for correlations selection algorithm in fintube
                    # to use same correlations during energy iteration, we will impose 
                    # the already chosen correlation for the rest of energy iteration
                    # unless a correlation is already imposed
                    if self.Condenser_Type == "Fin-tube":
                        Cond_h_imposed_array = []
                        for circuit in self.Condenser.Circuits:
                            if circuit.Correlations.imposed_h_2phase:
                                Cond_h_imposed_array.append(True) # a correlation is already imposed
                            else:
                                Cond_h_imposed_array.append(False) # No correlation was imposed
                                if not circuit.Correlations.Selected_2phase_HTC:
                                    circuit.Correlations.Selected_2phase_HTC = True
                                    circuit.Correlations.h_corr_2phase = 1 # just use shah for first iteration
                                circuit.Correlations.imposed_h_2phase = True
                        Cond_DP_imposed_array = []
                        for circuit in self.Condenser.Circuits:
                            if circuit.Correlations.imposed_dPdz_f_2phase:
                                Cond_DP_imposed_array.append(True) # a correlation is already imposed
                            else:
                                Cond_DP_imposed_array.append(False) # No correlation was imposed
                                if not circuit.Correlations.Selected_2phase_DP:
                                    circuit.Correlations.Selected_2phase_DP = True
                                    circuit.Correlations.dPdz_f_corr_2phase = 6 # just use Friedel for first iteration
                                circuit.Correlations.imposed_dPdz_f_2phase = True
                    if self.Evaporator_Type == "Fin-tube":
                        Evap_h_imposed_array = []
                        for circuit in self.Evaporator.Circuits:
                            if circuit.Correlations.imposed_h_2phase:
                                Evap_h_imposed_array.append(True) # a correlation is already imposed
                            else:
                                Evap_h_imposed_array.append(False) # No correlation was imposed
                                if not circuit.Correlations.Selected_2phase_HTC:
                                    circuit.Correlations.Selected_2phase_HTC = True
                                    circuit.Correlations.h_corr_2phase = 2 # just use shah for first iteration
                                circuit.Correlations.imposed_h_2phase = True
                        Evap_DP_imposed_array = []
                        for circuit in self.Evaporator.Circuits:
                            if circuit.Correlations.imposed_dPdz_f_2phase:
                                Evap_DP_imposed_array.append(True) # a correlation is already imposed
                            else:
                                Evap_DP_imposed_array.append(False) # No correlation was imposed
                                if not circuit.Correlations.Selected_2phase_DP:
                                    circuit.Correlations.Selected_2phase_DP = True
                                    circuit.Correlations.dPdz_f_corr_2phase = 6 # just use Friedel for first iteration
                                circuit.Correlations.imposed_dPdz_f_2phase = True

                    try:
                        # run solver chosen by user
                        main_solver(OBJECTIVE_type_3,[DT_evap_init,DT_cond_init],max_iter=self.max_n_iterations,method = solver,bounds = ([DT_evap_min,DT_cond_min],[DT_evap_max,DT_cond_max]))
                    except:
                        pass
                    
                    # error in low pressure side
                    delta_low = abs(self.DP_low - abs(self.DP_LowPressure))
                    
                    # error in high pressure side
                    delta_high = abs(self.DP_high - abs(self.DP_HighPressure))
                    if self.resid_pressure != None:
                        resid_pressure_change = abs(self.resid_pressure - (delta_low + delta_high))
                    else:
                        resid_pressure_change = delta_low + delta_high
                    self.resid_pressure = delta_low + delta_high
                    if hasattr(self,"update_residuals") and self.update_residuals != None: # sending reisudals to main UI
                        self.update_residuals.emit((i,None,None,None,None,self.resid_pressure))
                    
                    # update old values (0.7 is underrelaxation factor)
                    self.DP_low += 0.7 * (abs(self.DP_LowPressure) - self.DP_low)
                    self.DP_high += 0.7 * (abs(self.DP_HighPressure) - self.DP_high)

                    self.DP_evap += 0.7 * (abs(self.Evaporator.Results.DP_r) - self.DP_evap)
                    self.DP_suction += 0.7 * (abs(self.Line_Suction.Results.DP_r) - self.DP_suction)
                    self.DP_discharge += 0.7 * (abs(self.Line_Discharge.Results.DP_r) - self.DP_discharge)
                    self.DP_cond += 0.7 * (abs(self.Condenser.Results.DP_r) - self.DP_cond)
                    self.DP_liquid += 0.7 * (abs(self.Line_Liquid.Results.DP_r) - self.DP_liquid)
                    self.DP_2phase += 0.7 * (abs(self.Line_2phase.Results.DP_r) - self.DP_2phase)
                    
                    #Update the guess values based on last converged values
                    DT_evap_init = self.DT_evap
                    DT_cond_init = self.DT_cond

                    if self.resid_pressure < self.pressure_tol or resid_pressure_change < 0.1 * self.pressure_tol:
                        DP_converged=True
                    GoodRun=True
                    i += 1
                    if i > self.max_n_iterations:
                        if not hasattr(self,"Error_message"):
                            self.Error_message = "Maximum number of iterations exceeded"

                    # for correlations selection algorithm in fintube
                    # to use same correlations during energy iteration, we will impose 
                    # the already chosen correlation for the rest of energy iteration
                    # unless a correlation is already imposed
                    # we will remove here the selected correlations to choose again next iteration
                    if self.Condenser_Type == "Fin-tube":
                        for i,circuit in enumerate(self.Condenser.Circuits):
                            if not Cond_h_imposed_array[i]:
                                circuit.Correlations.imposed_h_2phase = False
                            if not Cond_DP_imposed_array[i]:
                                circuit.Correlations.imposed_dPdz_f_2phase = False
                    if self.Evaporator_Type == "Fin-tube":
                        for i,circuit in enumerate(self.Evaporator.Circuits):
                            if not Evap_h_imposed_array[i]:
                                circuit.Correlations.imposed_h_2phase = False
                            if not Evap_DP_imposed_array[i]:
                                circuit.Correlations.imposed_dPdz_f_2phase = False
            except:
                if hasattr(self,"Error_message"):
                    return(0,self.Error_message)
                else:
                    return (0,"Could not solve the cycle.")
        if not self.converged:
            if not hasattr(self,"Solver_Error"):
                self.Solver_Error = "Energy, mass or mass flowrate did not converge. Error in subcooling, charge or capillary input."
            return (0,"Could not solve the cycle.")
        return (1,)

    def Calculate(self,solver):
        T1 = time.time()
        AS = get_AS(self.Backend,self.Ref,self.REFPROP_path)
        if AS[0]:
            self.AS = AS[1]
        else:
            self.Solver_Error = "Error in using "+self.Ref+" with the current refrigerant library"
            return (0,"Error in using "+self.Ref+" with the current refrigerant library")
        self.solver = solver
        
        if self.Expansion_Device_Type == 'TXV':
            result = self.PreconditionedSolve_TXV(solver)

        elif self.Expansion_Device_Type == 'Capillary':
            result = self.PreconditionedSolve_capillary(solver)

        if result[0]:
            self.create_results()
        
        self.solving_time = time.time() - T1
        
        if result[0] and self.Create_ranges:
            if hasattr(self,"terminal_message"):
                self.terminal_message.emit("Solved cycle; Creating validation ranges...")
            self.Validation_ranges = create_ranges(self)

        self.CalculationTime = time.time() - T1
        
        return result
        
    def create_results(self):
        if self.Mode == 'AC':
            self.Results = ValuesClass()
            
            self.Results.Capacity = abs(self.Evaporator.Results.Q) - abs(self.Evaporator.Fan.power)
            self.Results.Power = abs(self.Compressor.power_elec) + abs(self.Evaporator.Fan.power) + abs(self.Condenser.Fan.power)
            self.Results.Charge_cycle = self.Evaporator.Results.Charge + self.Condenser.Results.Charge + self.Line_Liquid.Results.Charge + self.Line_Suction.Results.Charge + self.Line_Discharge.Results.Charge + self.Line_Discharge.Results.Charge
            self.Results.Charge_system = self.Results.Charge_cycle / (1 - self.Accum_charge_per)
            self.Results.Charge_accum = self.Results.Charge_system - self.Results.Charge_cycle
            
            self.Results.CalculationTime = self.CalculationTime
            self.Results.SHR = self.Evaporator.Results.SHR

            self.Results.COP = self.Evaporator.Results.Q / self.Compressor.power_mech
            self.Results.COP_S = self.Results.Capacity / self.Results.Power
            self.Results.Condition_1 = self.Second_Cond
            self.Results.Condition_1_value = self.cond2_value
            self.Results.Expansion_Device_Type = self.Expansion_Device_Type
            self.Results.mdot_r = self.Compressor.mdot_r

            self.Results.Energy_balance = self.Compressor.power_mech + self.Compressor.Q_amb + self.Line_Discharge.Results.Q + self.Condenser.Results.Q + self.Line_Liquid.Results.Q + self.Line_2phase.Results.Q + self.Evaporator.Results.Q + self.Line_Suction.Results.Q
            
            if self.Expansion_Device_Type == "TXV":
                self.Results.Condition_2_value = self.cond1_value
                if self.Superheat_Type == "Evaporator":
                    self.Results.Condition_2 = "Superheat at evaporator outlet"
                elif self.Superheat_Type == "Compressor":
                    self.Results.Condition_2 = "Superheat at compressor outlet"
            elif self.Expansion_Device_Type == "Capillary":
                self.Results.Condition_2_value = None
                self.Results.Condition_2 = "Capillary"

        elif self.Mode == 'HP':
            self.Results = ValuesClass()
            
            self.Results.Capacity = abs(self.Condenser.Results.Q) + abs(self.Evaporator.Fan.power)
            self.Results.Power = abs(self.Compressor.power_elec) + abs(self.Evaporator.Fan.power) + abs(self.Condenser.Fan.power)            
            self.Results.Charge_cycle = self.Evaporator.Results.Charge + self.Condenser.Results.Charge + self.Line_Liquid.Results.Charge + self.Line_Suction.Results.Charge + self.Line_Discharge.Results.Charge + self.Line_Discharge.Results.Charge
            self.Results.Charge_system = self.Results.Charge_cycle / (1 - self.Accum_charge_per)
            self.Results.Charge_accum = self.Results.Charge_system - self.Results.Charge_cycle

            self.Results.CalculationTime = self.CalculationTime
            self.Results.Tdew_cond = self.Tdew_cond
            self.Results.Tdew_evap = self.Tdew_evap
            self.Results.COP = abs(self.Condenser.Results.Q) / self.Compressor.power_mech
            self.Results.COP_S = self.Results.Capacity / self.Results.Power
            self.Results.Condition_1 = self.Second_Cond
            self.Results.Condition_1_value = self.cond2_value
            self.Results.Expansion_Device_Type = self.Expansion_Device_Type
            self.Results.mdot_r = self.Compressor.mdot_r

            self.Results.Energy_balance = self.Compressor.power_mech + self.Compressor.Q_amb + self.Line_Discharge.Results.Q + self.Condenser.Results.Q + self.Line_Liquid.Results.Q + self.Line_2phase.Results.Q + self.Evaporator.Results.Q + self.Line_Suction.Results.Q
            
            if self.Expansion_Device_Type == "TXV":
                self.Results.Condition_2_value = self.cond1_value
                if self.Superheat_Type == "Evaporator":
                    self.Results.Condition_2 = "Superheat at evaporator outlet"
                elif self.Superheat_Type == "Compressor":
                    self.Results.Condition_2 = "Superheat at compressor outlet"
            elif self.Expansion_Device_Type == "Capillary":
                self.Results.Condition_2_value = None
                self.Results.Condition_2 = "Capillary"

        
        self.AS.update(CP.PQ_INPUTS,self.Line_Suction.Results.Pout_r,1.0)        
        self.Results.Tdew_evap = self.AS.T()

        self.AS.update(CP.PQ_INPUTS,self.Compressor.Pout_r,1.0)        
        self.Results.Tdew_cond = self.AS.T()


        self.Results.States_matrix = np.zeros([8, 4])
        self.Results.States_matrix[0] = [self.Compressor.Pout_r, self.Compressor.Tout_r, self.Compressor.hout_r, self.Compressor.sout_r]
        self.Results.States_matrix[1] = [self.Line_Discharge.Results.Pout_r, self.Line_Discharge.Results.Tout_r, self.Line_Discharge.Results.hout_r, self.Line_Discharge.Results.Sout_r]
        self.Results.States_matrix[2] = [self.Condenser.Results.Pout_r, self.Condenser.Results.Tout_r, self.Condenser.Results.hout_r, self.Condenser.Results.Sout_r]
        self.Results.States_matrix[3] = [self.Line_Liquid.Results.Pout_r, self.Line_Liquid.Results.Tout_r, self.Line_Liquid.Results.hout_r, self.Line_Liquid.Results.Sout_r]
        self.Results.States_matrix[4] = [self.Line_2phase.Results.Pin_r, self.Line_2phase.Results.Tin_r, self.Line_2phase.Results.hin_r, self.Line_2phase.Results.Sin_r]
        self.Results.States_matrix[5] = [self.Line_2phase.Results.Pout_r, self.Line_2phase.Results.Tout_r, self.Line_2phase.Results.hout_r, self.Line_2phase.Results.Sout_r]
        self.Results.States_matrix[6] = [self.Evaporator.Results.Pout_r, self.Evaporator.Results.Tout_r, self.Evaporator.Results.hout_r, self.Evaporator.Results.Sout_r]
        self.Results.States_matrix[7] = [self.Line_Suction.Results.Pout_r, self.Line_Suction.Results.Tout_r, self.Line_Suction.Results.hout_r, self.Line_Suction.Results.Sout_r]
        
        self.AS.update(CP.PQ_INPUTS,self.Compressor.Pin_r,1.0)
        self.Results.Compressor_SH = self.Compressor.Tin_r - self.AS.T()
        
        self.Results.evap_TTD = self.Evaporator.Tin_a - self.Evaporator.Results.Tout_r

        self.Results.cond_TTD = self.Condenser.Results.Tout_r - self.Condenser.Tin_a
            
if __name__ == '__main__':
    
    def fun1():
        global Cycle
        global ranges
        from CoolProp.CoolProp import HAPropsSI
        Cycle = CycleClass()
        
        # defining cycle parameters
        # Cycle.Compressor_Type = 'AHRI'
        Cycle.Compressor_Type = 'Physics'
        
        Cycle.Condenser_Type = 'Fin-tube'
        Cycle.Evaporator_Type = 'Fin-tube'
        
        Cycle.Second_Cond = "Subcooling"
        Cycle.SC_value = 7
    
        # Cycle.Second_Cond = "Charge"
        # Cycle.Charge_value = 31
    
        Cycle.Expansion_Device_Type = 'TXV'
        Cycle.SH_value = 5
        Cycle.Superheat_Type = 'Evaporator'
        # Cycle.Superheat_Type = 'Compressor'
    
        # Cycle.Expansion_Device_Type = 'Capillary'
    
        Cycle.Backend = "HEOS"
        Cycle.Ref = "R410A"
        Cycle.Mode = "AC"
        Cycle.Tevap_init_manual = False
        Cycle.Tcond_init_manual = False
        Cycle.energy_tol = 1
        Cycle.pressure_tol = 10
        Cycle.mass_flowrate_tol = 0.001
        Cycle.mass_tol = 0.01
        Cycle.max_n_iterations = 40
        Cycle.Accum_charge_per = 0.7

        Cycle.Test_cond = "T1"

        Cycle.Update()
        
        # defining condenser
        Cycle.Condenser.Fan_add_DP = 0
        Cycle.Condenser.model = 'phase'
        Cycle.Condenser.create_circuits(1)
        Cycle.Condenser.Accurate = True
        Cycle.Condenser.connect(0,1,0,1.0,3)
        Cycle.Condenser.Q_error_tol = 0.01
        Cycle.Condenser.max_iter_per_circuit = 30
        Cycle.Condenser.Ref_Pressure_error_tol = 100
        Cycle.Condenser.Pin_a = 101325
        Cycle.Condenser.Tin_a = 35 + 273.15
        RHin_a = 0.5
        Win_a = HAPropsSI("W","T",Cycle.Condenser.Tin_a,"P",Cycle.Condenser.Pin_a,"R",RHin_a)
        Cycle.Condenser.Win_a = Win_a
        Cycle.Condenser.Vdot_ha = 1.7934
        Cycle.Condenser.name = "Generic Condenser"
        Cycle.Condenser.Circuits[0].Geometry.Ntubes_per_bank_per_subcircuit=6       #number of tubes per bank per circuit
        Cycle.Condenser.Circuits[0].Geometry.Nbank=3                             #number of banks or rows
        Cycle.Condenser.Circuits[0].Geometry.OD = 0.00913
        Cycle.Condenser.Circuits[0].Geometry.ID = 0.00849
        Cycle.Condenser.Circuits[0].Geometry.Staggering = 'aAa'
        Cycle.Condenser.Circuits[0].Geometry.Tubes_type='Smooth'
        Cycle.Condenser.Circuits[0].Geometry.Pl = 0.0191               #distance between center of tubes in flow direction                                                
        Cycle.Condenser.Circuits[0].Geometry.Pt = 0.0254                #distance between center of tubes orthogonal to flow direction
        connections = []
        for k in reversed(range(int(Cycle.Condenser.Circuits[0].Geometry.Nbank))):
            start = k * Cycle.Condenser.Circuits[0].Geometry.Ntubes_per_bank_per_subcircuit + 1
            end = (k + 1) * Cycle.Condenser.Circuits[0].Geometry.Ntubes_per_bank_per_subcircuit + 1
            if (Cycle.Condenser.Circuits[0].Geometry.Nbank - k)%2==1:
                connections += range(start,end)
            else:
                connections += reversed(range(start,end))
        
        Cycle.Condenser.Circuits[0].Geometry.Connections = connections
        Cycle.Condenser.Circuits[0].Geometry.FarBendRadius = 0.01
        Cycle.Condenser.Circuits[0].Geometry.e_D = 0
        Cycle.Condenser.Circuits[0].Geometry.Ltube=2.252                         #one tube length
        Cycle.Condenser.Circuits[0].Geometry.FPI = 25
        Cycle.Condenser.Circuits[0].Geometry.FinType = 'WavyLouvered'
        Cycle.Condenser.Circuits[0].Geometry.Fin_t = 0.00011
        Cycle.Condenser.Circuits[0].Geometry.Fin_xf = 0.001
        Cycle.Condenser.Circuits[0].Geometry.Fin_Pd = 0.001
        # Cycle.Condenser.Circuits[0].Geometry.Nsubcircuits = 4
        
        Cycle.Condenser.Circuits[0].Thermal.Nsegments = 10
        Cycle.Condenser.Circuits[0].Thermal.kw = 237
        Cycle.Condenser.Circuits[0].Thermal.k_fin = 237
        Cycle.Condenser.Circuits[0].Thermal.HTC_superheat_Corr = 0
        Cycle.Condenser.Circuits[0].Thermal.HTC_subcool_Corr = 0
        Cycle.Condenser.Circuits[0].Thermal.DP_superheat_Corr = 0
        Cycle.Condenser.Circuits[0].Thermal.DP_subcool_Corr = 0
        Cycle.Condenser.Circuits[0].Thermal.HTC_2phase_Corr = 0
        Cycle.Condenser.Circuits[0].Thermal.DP_2phase_Corr = 0
        Cycle.Condenser.Circuits[0].Thermal.DP_Accel_Corr = 2
        Cycle.Condenser.Circuits[0].Thermal.rho_2phase_Corr = 2
        Cycle.Condenser.Circuits[0].Thermal.Air_dry_Corr = 0
        Cycle.Condenser.Circuits[0].Thermal.Air_wet_Corr = 0
        Cycle.Condenser.Circuits[0].Thermal.h_r_superheat_tuning = 1.0
        Cycle.Condenser.Circuits[0].Thermal.h_r_subcooling_tuning = 1.0
        Cycle.Condenser.Circuits[0].Thermal.h_r_2phase_tuning = 1.0
        Cycle.Condenser.Circuits[0].Thermal.h_a_dry_tuning = 1.0
        Cycle.Condenser.Circuits[0].Thermal.h_a_wet_tuning = 1.0
        Cycle.Condenser.Circuits[0].Thermal.DP_r_superheat_tuning = 1.0
        Cycle.Condenser.Circuits[0].Thermal.DP_r_subcooling_tuning = 1.0
        Cycle.Condenser.Circuits[0].Thermal.DP_r_2phase_tuning = 1.0
        Cycle.Condenser.Circuits[0].Thermal.h_a_wet_on = False
        Cycle.Condenser.Circuits[0].Thermal.DP_a_wet_on = False
        Cycle.Condenser.Circuits[0].Thermal.FinsOnce = True
        Cycle.Condenser.Fan.model = 'efficiency'
        Cycle.Condenser.Fan.efficiency = '0.4'
        Cycle.Condenser.Fan.Fan_position = 'after'
        Cycle.Condenser.Fan.Fan_add_DP = 0
        Cycle.Condenser.Air_sequence = 'series_counter'
        Cycle.Condenser.Solver = 'mdot'
        
        # defining evaporator
        Cycle.Evaporator.Fan_add_DP = 50
        Cycle.Evaporator.model = 'phase'
        Cycle.Evaporator.create_circuits(1)
        Cycle.Evaporator.Accurate = True
        Cycle.Evaporator.connect(0,1,0,1.0,12)
        Cycle.Evaporator.Q_error_tol = 0.01
        Cycle.Evaporator.max_iter_per_circuit = 30
        Cycle.Evaporator.Ref_Pressure_error_tol = 100        
        Cycle.Evaporator.Pin_a = 101325
        Cycle.Evaporator.Tin_a = 23.889 + 273.15
        RHin_a = 0.5
        Win_a = HAPropsSI("W","T",Cycle.Evaporator.Tin_a,"P",Cycle.Evaporator.Pin_a,"R",RHin_a)
        Cycle.Evaporator.Win_a = Win_a
        Cycle.Evaporator.Vdot_ha = 0.9
        Cycle.Evaporator.name = "Generic Evaporator"
        Cycle.Evaporator.Circuits[0].Geometry.Ntubes_per_bank_per_subcircuit=6       #number of tubes per bank per circuit
        Cycle.Evaporator.Circuits[0].Geometry.Nbank=3                             #number of banks or rows
        Cycle.Evaporator.Circuits[0].Geometry.OD = 0.00913
        Cycle.Evaporator.Circuits[0].Geometry.ID = 0.00849
        Cycle.Evaporator.Circuits[0].Geometry.Staggering = 'aAa'
        Cycle.Evaporator.Circuits[0].Geometry.Tubes_type='Smooth'
        Cycle.Evaporator.Circuits[0].Geometry.Pl = 0.0191               #distance between center of tubes in flow direction                                                
        Cycle.Evaporator.Circuits[0].Geometry.Pt = 0.0254                #distance between center of tubes orthogonal to flow direction
    
        connections = []
        for k in reversed(range(int(Cycle.Evaporator.Circuits[0].Geometry.Nbank))):
            start = k * Cycle.Evaporator.Circuits[0].Geometry.Ntubes_per_bank_per_subcircuit + 1
            end = (k + 1) * Cycle.Evaporator.Circuits[0].Geometry.Ntubes_per_bank_per_subcircuit + 1
            if (Cycle.Evaporator.Circuits[0].Geometry.Nbank - k)%2==1:
                connections += range(start,end)
            else:
                connections += reversed(range(start,end))
    
        Cycle.Evaporator.Circuits[0].Geometry.Connections = connections
        Cycle.Evaporator.Circuits[0].Geometry.FarBendRadius = 0.01
        Cycle.Evaporator.Circuits[0].Geometry.e_D = 0
        Cycle.Evaporator.Circuits[0].Geometry.Ltube=0.452         #one tube length
        Cycle.Evaporator.Circuits[0].Geometry.FPI = 18
        Cycle.Evaporator.Circuits[0].Geometry.FinType = 'WavyLouvered'
        Cycle.Evaporator.Circuits[0].Geometry.Fin_t = 0.00011
        Cycle.Evaporator.Circuits[0].Geometry.Fin_xf = 0.001
        Cycle.Evaporator.Circuits[0].Geometry.Fin_Pd = 0.001
        Cycle.Evaporator.Circuits[0].Geometry.Nsubcircuits = 5
        
        Cycle.Evaporator.Circuits[0].Thermal.Nsegments = 10
        Cycle.Evaporator.Circuits[0].Thermal.kw = 237
        Cycle.Evaporator.Circuits[0].Thermal.k_fin = 237
        Cycle.Evaporator.Circuits[0].Thermal.FinsOnce = True
        Cycle.Evaporator.Circuits[0].Thermal.HTC_superheat_Corr = 0
        Cycle.Evaporator.Circuits[0].Thermal.HTC_subcool_Corr = 0
        Cycle.Evaporator.Circuits[0].Thermal.DP_superheat_Corr = 0
        Cycle.Evaporator.Circuits[0].Thermal.DP_subcool_Corr = 0
        Cycle.Evaporator.Circuits[0].Thermal.HTC_2phase_Corr = 0
        Cycle.Evaporator.Circuits[0].Thermal.DP_2phase_Corr = 0
        Cycle.Evaporator.Circuits[0].Thermal.DP_Accel_Corr = 2
        Cycle.Evaporator.Circuits[0].Thermal.rho_2phase_Corr = 2
        Cycle.Evaporator.Circuits[0].Thermal.Air_dry_Corr = 0
        Cycle.Evaporator.Circuits[0].Thermal.Air_wet_Corr = 0
        Cycle.Evaporator.Circuits[0].Thermal.h_r_superheat_tuning = 1.0
        Cycle.Evaporator.Circuits[0].Thermal.h_r_subcooling_tuning = 1.0
        Cycle.Evaporator.Circuits[0].Thermal.h_r_2phase_tuning = 1.0
        Cycle.Evaporator.Circuits[0].Thermal.h_a_dry_tuning = 1.0
        Cycle.Evaporator.Circuits[0].Thermal.h_a_wet_tuning = 1.0
        Cycle.Evaporator.Circuits[0].Thermal.DP_r_superheat_tuning = 1.0
        Cycle.Evaporator.Circuits[0].Thermal.DP_r_subcooling_tuning = 1.0
        Cycle.Evaporator.Circuits[0].Thermal.DP_r_2phase_tuning = 1.0
        Cycle.Evaporator.Circuits[0].Thermal.h_a_wet_on = False
        Cycle.Evaporator.Circuits[0].Thermal.DP_a_wet_on = False
        Cycle.Evaporator.Circuits[0].Geometry.Sub_HX_matrix = [[18  ,0.15   ,0.4],]
        Cycle.Evaporator.Fan.model = 'efficiency'
        Cycle.Evaporator.Fan.efficiency = '0.5'
        Cycle.Evaporator.Fan.Fan_position = 'after'
        Cycle.Evaporator.Air_sequence = 'series_counter'
        Cycle.Evaporator.Solver = 'mdot'
        
        # defining Liquid line
        Cycle.Line_Liquid.L = 5
        Cycle.Line_Liquid.ID = 0.019
        Cycle.Line_Liquid.OD = 0.022
        Cycle.Line_Liquid.k_line = 385
        Cycle.Line_Liquid.k_ins = 0.036
        Cycle.Line_Liquid.t_ins = 0.01
        Cycle.Line_Liquid.T_sur = 40 + 273.15
        Cycle.Line_Liquid.h_sur = 20
        Cycle.Line_Liquid.e_D = 0.00001
        Cycle.Line_Liquid.Nsegments = 20
        Cycle.Line_Liquid.Q_error_tol = 0.01
        Cycle.Line_Liquid.DP_tuning = 0.0
        Cycle.Line_Liquid.HT_tuning = 0.0
        Cycle.Line_Liquid.N_90_bends = 0
        Cycle.Line_Liquid.N_180_bends = 0
    
        # defining 2phase line
        Cycle.Line_2phase.L = 5
        Cycle.Line_2phase.ID = 0.019
        Cycle.Line_2phase.OD = 0.022
        Cycle.Line_2phase.k_line = 385
        Cycle.Line_2phase.k_ins = 0.036
        Cycle.Line_2phase.t_ins = 0.01
        Cycle.Line_2phase.T_sur = 40 + 273.15
        Cycle.Line_2phase.h_sur = 20
        Cycle.Line_2phase.e_D = 0.00001
        Cycle.Line_2phase.Nsegments = 20
        Cycle.Line_2phase.Q_error_tol = 0.01
        Cycle.Line_2phase.DP_tuning = 0.0
        Cycle.Line_2phase.HT_tuning = 0.0
        Cycle.Line_2phase.N_90_bends = 0
        Cycle.Line_2phase.N_180_bends = 0
    
        # defining Suction line
        Cycle.Line_Suction.L = 5
        Cycle.Line_Suction.ID = 0.012
        Cycle.Line_Suction.OD = 0.014
        Cycle.Line_Suction.k_line = 385
        Cycle.Line_Suction.k_ins = 0.036
        Cycle.Line_Suction.t_ins = 0.01
        Cycle.Line_Suction.T_sur = 40 + 273.15
        Cycle.Line_Suction.h_sur = 20
        Cycle.Line_Suction.e_D = 0.00001
        Cycle.Line_Suction.Nsegments = 20
        Cycle.Line_Suction.Q_error_tol = 0.01
        Cycle.Line_Suction.DP_tuning = 0.0
        Cycle.Line_Suction.HT_tuning = 0.0
        Cycle.Line_Suction.N_90_bends = 0
        Cycle.Line_Suction.N_180_bends = 0
    
        # defining Discharge line
        Cycle.Line_Discharge.L = 5
        Cycle.Line_Discharge.ID = 0.019
        Cycle.Line_Discharge.OD = 0.022
        Cycle.Line_Discharge.k_line = 385
        Cycle.Line_Discharge.k_ins = 0.036
        Cycle.Line_Discharge.t_ins = 0
        Cycle.Line_Discharge.T_sur = 40 + 273.15
        Cycle.Line_Discharge.h_sur = 20
        Cycle.Line_Discharge.e_D = 0.00001
        Cycle.Line_Discharge.Nsegments = 20
        Cycle.Line_Discharge.Q_error_tol = 0.01
        Cycle.Line_Discharge.DP_tuning = 0.0
        Cycle.Line_Discharge.HT_tuning = 0.0
        Cycle.Line_Discharge.N_90_bends = 0
        Cycle.Line_Discharge.N_180_bends = 0
        
        # defining AHRI Compressor
        if Cycle.Compressor_Type == 'AHRI':
            Cycle.Compressor.M = [(158.38079	,4.72993	,1.23499	,0.04045298	,-0.0057017	,-0.0097998	,0.000126	,-6.36e-06	,2.67e-05	,7.51e-06)]
            Cycle.Compressor.P = [(-576.86169	,-2.19523	,46.01597	,0.022031	,-0.0053035	,-0.3578	,0.000917	,-0.0010689	,0.000149	,0.0017934)]
            Cycle.Compressor.Speeds = [2500]
            Cycle.Compressor.fp = 0.0
            Cycle.Compressor.Vdot_ratio_P = 1.0
            Cycle.Compressor.Vdot_ratio_M = 1.0
            Cycle.Compressor.Displacement = 0.001
            Cycle.Compressor.SH_Ref = 20 * 5 / 9
            Cycle.Compressor.act_speed = 2500
            Cycle.Compressor.Unit_system = 'ip'
            Cycle.Compressor.Elec_eff = 1.0
            Cycle.Compressor.F_factor = 0.75
        
    
        # defining Physics-based compressor
        elif Cycle.Compressor_Type == 'Physics':
            Cycle.Compressor.fp = 0.0
            Cycle.Compressor.Vdot_ratio_P = 1.0
            Cycle.Compressor.Vdot_ratio_M = 1.0
            Cycle.Compressor.Displacement = 30E-6
            Cycle.Compressor.act_speed = 2500
            Cycle.Compressor.Elec_eff = 1.0
            Cycle.Compressor.isen_eff = "0.7"
            Cycle.Compressor.vol_eff = "0.92"
            Cycle.Compressor.Suction_Ref = 35+273.15
            Cycle.Compressor.F_factor = 0.75
            
        if Cycle.Expansion_Device_Type == 'Capillary':
            Cycle.Capillary.L = 4.0        
            Cycle.Capillary.D = 0.0009
            Cycle.Capillary.D_liquid = Cycle.Line_Liquid.ID
            Cycle.Capillary.Ntubes = 5
            Cycle.Capillary.DT_2phase = 0.5
            Cycle.Capillary.DP_converged = 1
        
        Cycle.REFPROP_path = ""
        Cycle.Create_ranges = False
        import time
        T1 = time.time()
        result = Cycle.Calculate('Newton')
        if not result[0]:
            print("cycle was not solved!")
            Cycle.Error_message = result[1]
            print(Cycle.Solver_Error)
        else:
            print(*Cycle.OutputList(),sep="\n")

    fun1()