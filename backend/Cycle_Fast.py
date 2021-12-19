from __future__ import division, print_function, absolute_import
import numpy as np
import CoolProp as CP
from backend.Capillary import CapillaryClass
from backend.CompressorAHRI import CompressorAHRIClass
from backend.CompressorPHY import CompressorPHYClass
from backend.Line import LineClass
from backend.HXFast import Fintube_fastClass, Microchannel_fastClass
from backend.cycle_solvers import main_solver
import time
from GUI_functions import load_refrigerant_list
from backend.Functions import get_AS

class ValuesClass():
    pass

class CycleFastClass():
    """
    Cycle class, used to solve a cycle consisting of several components
    
    Required Parameters:
    
    ===========    ==========  ========================================================================
    Variable       Units       Description
    ===========    ==========  ========================================================================
    Components     --          a list of classes of different components
    var_1          --          first variable of the cycle, can be 'SC' for subcooling or 'CH' for charge
    var_2          --          second variable of the cycle, can be 'SH' for superheating or 'CAP' for capillary tube
    ===========   ==========  ========================================================================
    
    """
    def __init__(self,**kwargs):
        #Load up the parameters passed in
        # using the dictionary
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
            self.Condenser = ValuesClass()
            self.Condenser_fast = Fintube_fastClass()
        elif self.Condenser_Type == "MicroChannel":
            self.Condenser = ValuesClass()
            self.Condenser_fast = Microchannel_fastClass()
        else:
            raise Exception("Please define consdenser type")

        if self.Evaporator_Type == "Fin-tube":
            self.Evaporator = ValuesClass()
            self.Evaporator_fast = Fintube_fastClass()
        elif self.Evaporator_Type == "MicroChannel":
            self.Evaporator = ValuesClass()
            self.Evaporator_fast = Microchannel_fastClass()
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
            self.cond2_value = self.Charge_value
        else:
            raise Exception("Please define second condition")
        
        self.ref_list = load_refrigerant_list()
        if not self.ref_list[0]:
            raise
        self.ref_list = self.ref_list[1]
        
    def OutputList(self):
        """
            Return a list of parameters for this component for further output
            
            It is a list of tuples, and each tuple is formed of items with indices:
                [0] Description of value
                
                [1] Units of value
                
                [2] The value itself
        """
        
        output_list_1 = [('Solved?','','Yes'),
                        ('','',''),
                        ('Refrigerant','',self.Ref),
                        ('','',''),
                        ('Cycle Capacity','W',self.Results.Capacity),
                        ('Cycle Power','W',self.Results.Power),
                        ('Cycle Charge','kg',self.Results.Charge),
                        ('','',''),
                        ('Cycle Condensing Temperature','K',self.Results.Tdew_cond),
                        ('Cycle Evaporating Temperature','K',self.Results.Tdew_evap),
                        ('','',''),
                        ('Cycle COP','-',self.Results.COP),
                        ('System COP','-',self.Results.COP_S),
                        ('','',''),
                        ('Refrigerant Mass Flow Rate','kg/s',self.Results.mdot_r),
                        ('','',''),
                        ('Condenser Subcooling','K',self.Condenser.Results.SC),
                        ('Evaporator Superheat','K',self.Evaporator.Results.SH),
                        ('Compressor Superheat','K',self.Results.Compressor_SH),
                        ('','',''),
                        ]
        
        if self.Expansion_Device_Type == "TXV":
            output_list_2_1 = [('Expansion Device','-','TXV'),
                               ('Superheat Value','K',self.SH_value),
                               ]
            if self.Superheat_Type == "Evaporator":
                output_list_2_2 = [('Superheat location','-','Evaporator Exit'),
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

        output_list_4 = [('','',''),
                         ('','',''),
                         ('Solver','',self.solver),
                         ('Solving time','s',self.solving_time),
                         ]
        
        output_list = output_list_1 + output_list_2 + output_list_3 + output_list_4
        
        return output_list

    def Calculate_type_1(self,DT_evap,DT_cond):
        """
        type_1 is used for superheat at evaporator with subcooling or charge
        
        Inputs are differences in temperature [K] between HX air inlet temperature 
        and the dew temperature for the heat exchanger.
        
        Required Inputs:
            DT_evap: 
                Difference in temperature [K] between evaporator air inlet 
                temperature and refrigerant dew temperature
            DT_cond:
                Difference in temperature [K] between condenser air inlet temperature and refrigeant dew temperature
        """
        #AbstractState
        # if converged, just return zeros
        if self.converged:
            return (0,0)
        
        if hasattr(self,"check_terminate"): #used to terminate run in GUI
            if self.check_terminate:
                self.Error_message = "User terminated run"
                raise
        AS = self.AS
        #Condenser and evaporator dew temperature (guess)
        if self.Native_HX_files:
            Tdew_cond = self.Condenser.Air_T + DT_cond
            Tdew_evap = self.Evaporator.Air_T - DT_evap
        else:
            if hasattr(self.Evaporator_fast,"HX"):
                Tdew_evap = self.Evaporator_fast.HX.Tin_a - DT_evap
            elif hasattr(self.Evaporator_fast,"HX_fast"):
                Tdew_evap = self.Evaporator_fast.HX_fast.Tin_a - DT_evap
                
            if hasattr(self.Condenser_fast,"HX"):
                Tdew_cond = self.Condenser_fast.HX.Tin_a + DT_cond
            elif hasattr(self.Condenser_fast,"HX_fast"):
                Tdew_cond = self.Condenser_fast.HX_fast.Tin_a + DT_cond
        
        #Condenser and evaporator saturation pressures
        AS.update(CP.QT_INPUTS,1.0,Tdew_cond)
        psat_cond=AS.p() #[Pa]
        AS.update(CP.QT_INPUTS,1.0,Tdew_evap)
        psat_evap=AS.p() #[Pa]

        DT_sh = self.SH_value
        
        if hasattr(self,'Evap_Pout_r'):
            Pin_suction = self.Evap_Pout_r
            AS.update(CP.PQ_INPUTS,Pin_suction,1.0)
            Tin_suction = AS.T() + DT_sh
        else:
            Pin_suction = psat_evap
            Tin_suction = Tdew_evap + DT_sh
            
        # inlet enthalpy to suction line
        AS.update(CP.PT_INPUTS,Pin_suction, Tin_suction)
        hin_suction = AS.hmass()
        
        self.Tdew_cond = Tdew_cond
        self.Tdew_evap = Tdew_evap
        
        if not hasattr(self.Compressor,'mdot_r') or self.Compressor.mdot_r<0.00001:
            # The first run of model, run the compressor just so you can get a preliminary value 
            # for the mass flow rate for the line set 
            params={
                'Pin_r': float(psat_evap),
                'Pout_r': float(psat_cond),
                'hin_r': float(hin_suction),
                'AS': AS,
            }
            self.Compressor.Update(**params)
            self.Compressor.Calculate()

        #solve suction line
        params={
            'Pin_r': float(psat_evap),
            'hin_r': float(hin_suction),
            'mdot_r': float(self.Compressor.mdot_r),
            'AS':  AS,
        }
        self.Line_Suction.Update(**params)
        self.Line_Suction.Calculate()

        # solve compressor
        params={
            'Pin_r': float(psat_evap - self.DP_low),
            'Pout_r': float(psat_cond + self.DP_high),
            'hin_r': float(self.Line_Suction.Results.hout_r),
            'AS': AS,
        }
        self.Compressor.Update(**params)
        self.Compressor.Calculate()

        # solve Discharge line
        params={
                'Pin_r': float(psat_cond),
                'hin_r': float(self.Compressor.hout_r),
                'mdot_r': float(self.Compressor.mdot_r),
                'AS':AS,
            }
        
        self.Line_Discharge.Update(**params)
        self.Line_Discharge.Calculate()
        
        # solve condenser
        DP_Cond, (TTD_Cond, self.Cond_hout_r) = self.Condenser_fast.solve(
                                                 float(self.Compressor.mdot_r),
                                                 float(psat_cond),
                                                 float(self.Line_Discharge.Results.hout_r))
        # solving liquid line
        params={
                'Pin_r': float(psat_cond),
                'hin_r': float(self.Cond_hout_r),
                'mdot_r': float(self.Compressor.mdot_r),
                'AS':AS,
            }
        
        self.Line_Liquid.Update(**params)
        self.Line_Liquid.Calculate()

        # solving 2phase line if enabled
        params={
                'Pin_r': float(psat_evap),
                'hin_r': float(self.Line_Liquid.Results.hout_r),
                'mdot_r': float(self.Compressor.mdot_r),
                'AS': AS,
            }
        self.Line_2phase.Update(**params)
        self.Line_2phase.Calculate()
        
        # solving evaporator
        DP_Evap, (TTD_Evap, self.Evap_hout_r) = self.Evaporator_fast.solve(
                                                    float(self.Compressor.mdot_r),
                                                    float(psat_evap),
                                                    float(self.Line_2phase.Results.hout_r))
        
        self.DP_HighPressure= abs(DP_Cond + self.Line_Discharge.Results.DP_r + self.Line_Liquid.Results.DP_r)
        
        self.DP_LowPressure= abs(DP_Evap + self.Line_Suction.Results.DP_r + self.Line_2phase.Results.DP_r)
        # creating residuals list
        resid = np.zeros((2))
                
        # evaporator residual
        evaporator_residual = self.Compressor.mdot_r * (self.Evap_hout_r - self.Line_Suction.Results.hin_r)
        resid[0] = evaporator_residual
        if abs(resid[0]) < self.energy_tol:
            resid[0] = 0
                
        # condenser residual
        if self.Second_Cond == 'Subcooling':
            AS.update(CP.PQ_INPUTS,psat_cond+DP_Cond,0.0)
            Tdew_out = AS.T()
            AS.update(CP.PT_INPUTS,psat_cond+DP_Cond,Tdew_out - self.cond2_value)
            h_subcool_req = AS.hmass()
            resid[1] = self.Compressor.mdot_r * (self.Cond_hout_r - h_subcool_req)
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
        if self.Native_HX_files:
            self.Evaporator.Tin_a = self.Evaporator.Air_T
            self.Condenser.Tin_a = self.Condenser.Air_T
        else:
            if hasattr(self.Evaporator_fast,"HX"):
                self.Evaporator.Tin_a = self.Evaporator_fast.HX.Tin_a
            elif hasattr(self.Evaporator_fast,"HX_fast"):
                self.Evaporator.Tin_a = self.Evaporator_fast.HX_fast.Tin_a
                
            if hasattr(self.Condenser_fast,"HX"):
                self.Condenser.Tin_a = self.Condenser_fast.HX.Tin_a
            elif hasattr(self.Condenser_fast,"HX_fast"):
                self.Condenser.Tin_a = self.Condenser_fast.HX_fast.Tin_a
            
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
            except ValueError:
                raise
            return resids
        
        if self.cond1 == 'superheat_evap':
            objective = OBJECTIVE_type_1
        elif self.cond1 == 'superheat_comp':
            objective = OBJECTIVE_type_2
        
        DT_evap_init = 16
        DT_cond_init = 16
        self.DT_evap = DT_evap_init
        self.DT_cond = DT_cond_init
        
        GoodRun=False
        i = 0
        self.iter = 0
        while GoodRun == False:
            try:
                self.DP_low=0
                self.DP_high=0
                self.resid_pressure = None
                DP_converged=False
                while DP_converged == False:
                    self.converged = False

                    try:
                        # run solver chosen by user
                        main_solver(objective,[DT_evap_init,DT_cond_init],max_iter=self.max_n_iterations,method = solver)
                    except:
                        import traceback
                        print(traceback.format_exc())
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
                    
                    # update old values
                    self.DP_low = abs(self.DP_LowPressure)
                    self.DP_high = abs(self.DP_HighPressure)
                    
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
                        raise
            except:
                import traceback
                print(traceback.format_exc())
                self.CalculationTime = time.time() - T1
                if hasattr(self,"Error_message"):
                    return(0,self.Error_message)
                else:
                    return (0,"Could not solve the cycle. Try using another solver (hybrid is slow but recommended)")
        self.CalculationTime = time.time() - T1
        if not self.converged:
            return (0,"Energy did not converge. Try using another solver (hybrid is slow but recommended)")
        return (1,)

    def Calculate(self,solver):
        T1 = time.time()
        AS = get_AS(self.Backend,self.Ref,self.REFPROP_path)
        if AS[0]:
            self.AS = AS[1]
        else:
            pass

        if self.Native_HX_files == True:
            if self.Condenser_Type == "Fin-tube":
                self.Condenser_fast.HX_define_fintube(self.Condenser,self.AS)
            elif self.Condenser_Type == "MicroChannel":
                self.Condenser_fast.HX_define_microchannel(self.Condenser,self.AS)
            if self.Evaporator_Type == "Fin-tube":
                self.Evaporator_fast.HX_define_fintube(self.Evaporator,self.AS)
            elif self.Evaporator_Type == "MicroChannel":
                self.Evaporator_fast.HX_define_microchannel(self.Evaporator,self.AS)
        else:
            self.Condenser_fast.AS = self.AS
            self.Evaporator_fast.AS = self.AS
            
        self.Line_Discharge.Nsegments = 1
        self.Line_Liquid.Nsegments = 1
        self.Line_2phase.Nsegments = 1
        self.Line_Suction.Nsegments = 1
        
        if self.Expansion_Device_Type == 'TXV':
            result = self.PreconditionedSolve_TXV(solver)

        elif self.Expansion_Device_Type == 'Capillary':
            result = self.PreconditionedSolve_capillary(solver)
        self.solving_time = time.time() - T1
        try:
            self.create_results()
        except:
            pass
        return result
        
    def create_results(self):
        if self.Mode == 'AC':
            self.Results = ValuesClass()
            
            self.Results.Capacity = abs(self.Compressor.mdot_r * (self.Evap_hout_r - self.Line_2phase.Results.hout_r))
            self.Results.Power = abs(self.Compressor.power_elec)
            self.Results.Charge = self.Evaporator.Results.Charge + self.Condenser.Results.Charge + self.Line_Liquid.Results.Charge + self.Line_Suction.Results.Charge + self.Line_Discharge.Results.Charge + self.Line_Discharge.Results.Charge
            self.Results.CalculationTime = self.CalculationTime
            self.Results.Tdew_cond = self.Tdew_cond
            self.Results.Tdew_evap = self.Tdew_evap
            self.Results.COP = self.Results.Capacity / self.Compressor.power_mech
            self.Results.COP_S = self.Results.Capacity / self.Results.Power
            self.Results.Condition_1 = self.Second_Cond
            self.Results.Condition_1_value = self.cond2_value
            self.Results.Expansion_Device_Type = self.Expansion_Device_Type
            self.Results.mdot_r = self.Compressor.mdot_r
            
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
            self.Results.Charge = self.Evaporator.Results.Charge + self.Condenser.Results.Charge + self.Line_Liquid.Results.Charge + self.Line_Suction.Results.Charge + self.Line_Discharge.Results.Charge + self.Line_Discharge.Results.Charge
            self.Results.CalculationTime = self.CalculationTime
            self.Results.Tdew_cond = self.Tdew_cond
            self.Results.Tdew_evap = self.Tdew_evap
            self.Results.COP = self.Condenser.Results.Q / self.Compressor.power_mech
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

        self.AS.update(CP.PQ_INPUTS,self.Compressor.Pin_r,1.0)
        self.Results.Compressor_SH = self.Compressor.Tin_r - self.AS.T()
            
if __name__ == '__main__':
    global Cycle
    def fun1():
        T1 = time.time()
        Cycle = CycleFastClass()
        
        # defining cycle parameters
        Cycle.Compressor_Type = 'Physics'
        # Cycle.Compressor_Type = 'Physics'
        
        Cycle.Condenser_Type = 'MicroChannel'
        Cycle.Evaporator_Type = 'Fin-tube'
        
        Cycle.Second_Cond = "Subcooling"
        Cycle.SC_value = 1
    
        # Cycle.Second_Cond = "Charge"
        # Cycle.Charge_value = 31
    
        Cycle.Expansion_Device_Type = 'TXV'
        Cycle.SH_value = 5.0
        Cycle.Superheat_Type = 'Evaporator'
        # Cycle.Superheat_Type = 'Compressor'
    
        # Cycle.Expansion_Device_Type = 'Capillary'
    
        Cycle.Backend = "HEOS"
        Cycle.Ref = "R410A"
        Cycle.Mode = "AC"
        Cycle.Tevap_init_manual = False
        Cycle.Tcond_init_manual = False
        Cycle.energy_tol = 1
        Cycle.pressure_tol = 100
        Cycle.mass_flowrate_tol = 0.001
        Cycle.mass_tol = 0.01
        Cycle.max_n_iterations = 20
        Cycle.Update()
        
        Cycle.Native_HX_files = False
        # defining condenser
        Cycle.Condenser_fast = Fintube_fastClass()
        Cycle.Condenser_fast.HX_fast = ValuesClass()
        Cycle.Condenser_fast.HX_fast.h_a = 50
        Cycle.Condenser_fast.HX_fast.N_circuits = 4
        Cycle.Condenser_fast.HX_fast.A_a_total = 15
        Cycle.Condenser_fast.HX_fast.h_r_2phase = 3000
        Cycle.Condenser_fast.HX_fast.h_r_superheat = 450
        Cycle.Condenser_fast.HX_fast.h_r_subcool = 800
        Cycle.Condenser_fast.HX_fast.D = 0.0127
        Cycle.Condenser_fast.HX_fast.L_circuit = 6
        Cycle.Condenser_fast.HX_fast.Tin_a = 35 + 273.15
        Cycle.Condenser_fast.HX_fast.Win_a = 0.01
        Cycle.Condenser_fast.HX_fast.Vdot_ha = 1.79
        Cycle.Condenser_fast.HX_fast.DPDZ_2phase = 2000
        Cycle.Condenser_fast.HX_fast.DPDZ_superheat = 2500
        Cycle.Condenser_fast.HX_fast.DPDZ_subcool = 500
        
        # defining evaporator
        Cycle.Evaporator_fast = Fintube_fastClass()
        Cycle.Evaporator_fast.HX_fast = ValuesClass()
        Cycle.Evaporator_fast.HX_fast.h_a = 70
        Cycle.Evaporator_fast.HX_fast.N_circuits = 2
        Cycle.Evaporator_fast.HX_fast.A_a_total = 9
        Cycle.Evaporator_fast.HX_fast.h_r_2phase = 3000
        Cycle.Evaporator_fast.HX_fast.h_r_superheat = 450
        Cycle.Evaporator_fast.HX_fast.h_r_subcool = 0
        Cycle.Evaporator_fast.HX_fast.D = 0.0127
        Cycle.Evaporator_fast.HX_fast.L_circuit = 4
        Cycle.Evaporator_fast.HX_fast.Tin_a = 22 + 273.15
        Cycle.Evaporator_fast.HX_fast.Win_a = 0.008
        Cycle.Evaporator_fast.HX_fast.Vdot_ha = 0.78
        Cycle.Evaporator_fast.HX_fast.DPDZ_2phase = 2000
        Cycle.Evaporator_fast.HX_fast.DPDZ_superheat = 2500
        Cycle.Evaporator_fast.HX_fast.DPDZ_subcool = 0
        
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
        Cycle.Line_Liquid.Nsegments = 1
        Cycle.Line_Liquid.Q_error_tol = 0.01
        Cycle.Line_Liquid.DP_tuning = 1.0
        Cycle.Line_Liquid.HT_tuning = 1.0
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
        Cycle.Line_2phase.Nsegments = 1
        Cycle.Line_2phase.Q_error_tol = 0.01
        Cycle.Line_2phase.DP_tuning = 1.0
        Cycle.Line_2phase.HT_tuning = 1.0
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
        Cycle.Line_Suction.Nsegments = 1
        Cycle.Line_Suction.Q_error_tol = 0.01
        Cycle.Line_Suction.DP_tuning = 1.0
        Cycle.Line_Suction.HT_tuning = 1.0
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
        Cycle.Line_Discharge.Nsegments = 1
        Cycle.Line_Discharge.Q_error_tol = 0.01
        Cycle.Line_Discharge.DP_tuning = 1.0
        Cycle.Line_Discharge.HT_tuning = 1.0
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
            Cycle.Compressor.Displacement = 0.00005
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
            Cycle.Compressor.Displacement = 0.00005
            Cycle.Compressor.act_speed = 2500
            Cycle.Compressor.Elec_eff = 1.0
            Cycle.Compressor.isen_eff = "0.7"
            Cycle.Compressor.vol_eff = "0.8"
            
        if Cycle.Expansion_Device_Type == 'Capillary':
            Cycle.Capillary.L = 4.0
            Cycle.Capillary.D = 0.0009
            Cycle.Capillary.D_liquid = Cycle.Line_Liquid.ID
            Cycle.Capillary.Ntubes = 5
            Cycle.Capillary.DT_2phase = 0.5
            Cycle.Capillary.DP_converged = 1
        
        Cycle.REFPROP_path = ""
        result = Cycle.Calculate('Hybrid')
        if not result[0]:
            print("Cycle was not solved!")
            Cycle.Error_message = result[1]
        else:
            print("Cycle was solved successfully!")
        print('Calculation time:',round(time.time() - T1,3),'s')
    
    fun1()