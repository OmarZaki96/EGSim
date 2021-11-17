from PyQt5.QtCore import QObject, pyqtSignal
from inputs_validation import validate_inputs
from handler import define_single
import time
from itertools import product
from copy import deepcopy
import multiprocessing
import numpy as np
from GUI_functions import create_outputs_array, load_ranges_creator_options
from CoolProp.CoolProp import HAPropsSI

class solver(QObject):
    finished = pyqtSignal(tuple)
    input_error = pyqtSignal(str)
    update_residuals = pyqtSignal(tuple)
    terminal_message = pyqtSignal(str)
    def __init__(self,components,options,parent=None):
        super(solver, self).__init__(parent)
        self.compressor = components[0]
        self.condenser = components[1]
        self.evaporator = components[2]
        self.liquid_line = components[3]
        self.twophase_line = components[4]
        self.suction_line = components[5]
        self.discharge_line = components[6]
        self.parametric = options["parametric"]
        self.refrigerant = options["refrigerant"]
        self.Backend = options["Ref_library"]
        self.Mode = options["Cycle_mode"]
        self.Accum_charge_per = options["Accum_charge_per"]
        self.Test_cond = options["Test_cond"]
        self.terminate = False
        self.condenser_type = options["condenser_type"]
        if self.condenser_type == "Fintube":
            self.condenser.type = "Fintube"
        elif self.condenser_type == "Microchannel":
            self.condenser.type = "Microchannel"
            
        self.evaporator_type = options["evaporator_type"]
        if self.evaporator_type == "Fintube":
            self.evaporator.type = "Fintube"
        elif self.evaporator_type == "Microchannel":
            self.evaporator.type = "Microchannel"

        self.first_condition = options["first_condition"]
        if self.first_condition == "subcooling":
            self.sc_value = options["sc_value"]
            self.charge_value = 0.0
            self.mass_tol = 0.0
        elif self.first_condition == "charge":
            self.sc_value = 0.0
            self.charge_value = options["charge_value"]
            self.mass_tol = options["mass_tol"]
        self.expansion_type = options["expansion_type"]
        if self.expansion_type == "TXV":
            self.sh_location = options["sh_location"]
            self.sh_value = options["sh_value"]
            self.mass_flowrate_tol = 0.0
        elif self.expansion_type == "capillary":
            self.sh_location = ""
            self.sh_value = 0.0
            self.capillary = components[7]
            self.mass_flowrate_tol = options["mass_flowrate_tol"]
        self.solver = options["solver"]
        self.energy_tol = options["energy_tol"]
        self.max_n_iterations = options["max_n_iterations"]
        self.pressure_tol = options["pressure_tol"]
        self.Tevap_guess_type = options["Tevap_guess_type"]
        if self.Tevap_guess_type == "manual":
            self.Tevap_type = True
            self.Tevap_guess = options["Tevap_guess"]
        elif self.Tevap_guess_type == "auto":
            self.Tevap_type = False
            self.Tevap_guess = 0.0
            
        self.Tcond_guess_type = options["Tcond_guess_type"]
        
        if self.Tcond_guess_type == "manual":
            self.Tcond_type = True
            self.Tcond_guess = options["Tcond_guess"]
        elif self.Tcond_guess_type == "auto":
            self.Tcond_type = False
            self.Tcond_guess = 0.0
        self.N_processes = options["N_processes"]
        self.refprop_path = options['refprop_path']
        
        # taking parametric study if exists
        if self.parametric:
            self.parametric_array = options['parametric_array']
        
    def run(self):
        if not self.parametric:
            self.check_inputs_single()
            time.sleep(0.1)
            self.terminal_message.emit("Trying to solve cycle")
            time.sleep(0.1)
            result = self.run_single()
            if result[0]:
                self.finished.emit((1,"Run finished",result[1]))
            else:
                self.finished.emit((0,result[1]))
        
        if self.parametric:
            self.run_cycles()
            
    def run_single(self):
        if self.expansion_type == "capillary":
            result = define_single(self.compressor, self.condenser, 
                                  self.evaporator, self.liquid_line, 
                                  self.suction_line, self.discharge_line,
                                  self.twophase_line,
                                  {'Expansion_Device_Type':self.expansion_type,
                                   'sh_location':self.sh_location,
                                   'sh_value':self.sh_value,
                                   'Second_Cond':self.first_condition,
                                   'sc_value':self.sc_value,
                                   'charge_value':self.charge_value,
                                   'Backend': self.Backend,
                                   'Ref': self.refrigerant,
                                   'Mode': self.Mode,
                                   'Tevap_init_manual': self.Tevap_type,
                                   'Tevap_init': self.Tevap_guess,
                                   'Tcond_init_manual': self.Tcond_type,
                                   'Tcond_init': self.Tcond_guess,
                                   'energy_tol': self.energy_tol,
                                   'pressure_tol': self.pressure_tol,
                                   'mass_flowrate_tol': self.mass_flowrate_tol,
                                   'mass_tol': self.mass_tol,
                                   'solver': self.solver,
                                   'max_n_iterations': self.max_n_iterations,
                                   'Test_cond': self.Test_cond,
                                   'Accum_charge_per': self.Accum_charge_per,
                                   },self.update_residuals,
                                     self.capillary)
            if result[0]:
                self.Cycle = result[1]
                self.Cycle.REFPROP_path = self.refprop_path
                result = self.Cycle.Calculate(self.Cycle.solver_option)
                if result[0]:
                    if abs(self.Cycle.Capillary.Results.Pout_r - self.Cycle.Capillary.Pout_r_target) > self.Cycle.Capillary.DP_converged:
                        self.input_error.emit("Capillary tube is choked; Capillary tube exit pressure is higher than two-phase line inlet pressure")
                    return (1,self.Cycle)
                else:
                    if hasattr(self.Cycle,"Solver_Error"):
                        self.input_error.emit(self.Cycle.Solver_Error)
                        
                    return (0,result[1])
            else:
                return (0,"failed to define cycle, problem with one of the inputs")

        elif self.expansion_type == "TXV":
            result = define_single(self.compressor, self.condenser, 
                                  self.evaporator, self.liquid_line, 
                                  self.suction_line, self.discharge_line,
                                  self.twophase_line,
                                  {'Expansion_Device_Type':self.expansion_type,
                                   'sh_location':self.sh_location,
                                   'sh_value':self.sh_value,
                                   'Second_Cond':self.first_condition,
                                   'sc_value':self.sc_value,
                                   'charge_value':self.charge_value,
                                   'Backend': self.Backend,
                                   'Ref': self.refrigerant,
                                   'Mode': self.Mode,
                                   'Tevap_init_manual': self.Tevap_type,
                                   'Tevap_init': self.Tevap_guess,
                                   'Tcond_init_manual': self.Tcond_type,
                                   'Tcond_init': self.Tcond_guess,
                                   'energy_tol': self.energy_tol,
                                   'pressure_tol': self.pressure_tol,
                                   'mass_flowrate_tol': self.mass_flowrate_tol,
                                   'mass_tol': self.mass_tol,
                                   'solver': self.solver,
                                   'max_n_iterations': self.max_n_iterations,
                                   'Test_cond': self.Test_cond,
                                   'Accum_charge_per': self.Accum_charge_per,
                                   },self.update_residuals,)
            if result[0]:
                self.Cycle = result[1]
                self.Cycle.REFPROP_path = self.refprop_path
                self.Cycle.Create_ranges = load_ranges_creator_options()
                self.Cycle.terminal_message = self.terminal_message
                result = self.Cycle.Calculate(self.Cycle.solver_option)
                if result[0]:
                    return (1,self.Cycle)
                else:
                    if hasattr(self.Cycle,"Solver_Error"):
                        self.input_error.emit(self.Cycle.Solver_Error)
                        
                    return (0,result[1])
            else:
                return (0,"failed to define cycle, problem with one of the inputs")
    
    def check_inputs_single(self):
        if self.expansion_type == "TXV":
            result = validate_inputs(self.compressor, self.condenser,
                                     self.evaporator, self.liquid_line, 
                                     self.twophase_line, self.suction_line,
                                     self.discharge_line)
        elif self.expansion_type == "capillary":
            result = validate_inputs(self.compressor, self.condenser,
                                     self.evaporator, self.liquid_line, 
                                     self.twophase_line, self.suction_line,
                                     self.discharge_line, self.capillary)
        
        if not result[0]: # error in inputs
            if result[2] == 0:
                result[1] = "Error in compressor:\n"+ result[1]
            elif result[2] == 1:
                result[1] = "Error in condenser:\n"+ result[1]
            elif result[2] == 2:
                result[1] = "Error in evaporator:\n"+ result[1]
            elif result[2] == 3:
                result[1] = "Error in liquid line:\n"+ result[1]
            elif result[2] == 4:
                result[1] = "Error in two-phase line:\n"+ result[1]
            elif result[2] == 5:
                result[1] = "Error in suction line:\n"+ result[1]
            elif result[2] == 6:
                result[1] = "Error in discharge line:\n"+ result[1]
            elif result[2] == 7:
                result[1] = "Error in capillary tube:\n"+ result[1]
            self.input_error.emit(result[1])
            self.finished.emit((0,"Failed to run: Error in inputs"))
        else:
            self.terminal_message.emit("Checked inputs")

    def run_cycles(self):
        T1 = time.time()
        self.terminal_message.emit("Creating potential cycle configurations")        
        Cycles = self.create_Cycles()
        time.sleep(0.1)
        self.check_inputs_parametric()
        time.sleep(0.1)
        self.terminal_message.emit("Trying to solve cycles, there is a total of "+str(len(Cycles))+" potential cycle configurations")
        time.sleep(0.1)

        m = multiprocessing.Manager()
        message = m.Queue()
        self.pool = multiprocessing.Pool(min(self.N_processes,len(Cycles)))
        i = range(len(Cycles))
        message_list = (message for _ in range(len(Cycles)))
        expansion_type_list = [self.expansion_type for _ in range(len(Cycles))]
        result_async = self.pool.map_async(run_cycle,zip(i,Cycles,message_list,expansion_type_list,))
        while True:
            try:
                time.sleep(0.1)
                received = message.get_nowait()
                if received[0] == 0:
                    self.terminal_message.emit(received[1])
                elif received[0] == 1:
                    self.input_error.emit(received[1])
            except:
                if result_async.ready():
                    break
                elif self.terminate:
                    self.pool.terminate()
                    break
                else:
                    pass
        result = []
        for value in result_async._value:
            # get the results from the async solver, if not none, get the value. if note, this cycle failed to solve and just return (0,"")
            if value is not None:
                result.append(value)
            else:
                result.append((0,""))
        self.pool.close()
        self.pool.join()
        N_succeeded = 0
        for i in result:
            # count number of succeeded cases
            if i[0]:
                N_succeeded += 1
        outputs_list = []
        for i,row in enumerate(result):
            # create a table of case numbers and results if succeeded, or 0 if not
            if row[0]:
                outputs_list.append([i+1,row[1]])
            else:
                outputs_list.append([i+1,0])
        one_success = False
        for row in outputs_list:
            # check if any case solved, and get the solved case results as template
            if not (row[1] is 0):
                one_success = True
                success_template = row[1]
        if not one_success:
            # No cases succeeded to solve
            result_list = None
        else:
            # at least one case was able to solve
            for m,(i,output) in enumerate(outputs_list):
                # to replace the failed cases results with the template of succeeded case
                i -= 1
                if output is 0:
                    outputs_list[i][1] = deepcopy(success_template)
                    for j in range(len(success_template)):
                        outputs_list[i][1][j][1][:,2] = "" # replace all result values of solved cases with a ""
                    outputs_list[i][1][0][1] = outputs_list[i][1][0][1].astype(object) # convert the field to object field
                    outputs_list[i][1][0][1][0,2] = "No"
                    try:
                        outputs_list[i][1][0][1][1,2] = result[m][1]
                        print(outputs_list[i])
                    except:
                        pass
            result_list = outputs_list
        Calculation_time = time.time() - T1
        self.finished.emit((1,
                            "Parametric Study finished. A total of "+str(N_succeeded)+" succeeded out of "+str(len(Cycles))+" cycle configurations",
                            result_list,
                            Calculation_time,))

    def check_inputs_parametric(self):
        error = False
        for i,object_i in enumerate(self.objects):
            result = validate_inputs(*object_i)
            
            if not result[0]: # error in inputs
                if result[2] == 0:
                    result[1] = "Error in compressor:\n"+ result[1]
                elif result[2] == 1:
                    result[1] = "Error in condenser:\n"+ result[1]
                elif result[2] == 2:
                    result[1] = "Error in evaporator:\n"+ result[1]
                elif result[2] == 3:
                    result[1] = "Error in liquid line:\n"+ result[1]
                elif result[2] == 4:
                    result[1] = "Error in two-phase line:\n"+ result[1]
                elif result[2] == 5:
                    result[1] = "Error in suction line:\n"+ result[1]
                elif result[2] == 6:
                    result[1] = "Error in discharge line:\n"+ result[1]
                elif result[2] == 7:
                    result[1] = "Error in capillary tube:\n"+ result[1]
                self.input_error.emit(result[1])
                self.finished.emit((0,"Failed to run: Error in inputs of Cycle Configuration "+str(i+1)))
                error = True
            else:
                if not error:
                    error = False
        if not error:
            self.terminal_message.emit("Checked inputs")
        
    def create_Cycles(self):
        options = self.create_parametric_options()
        compressors = self.create_parametric_compressors()
        Lines_liquid = self.create_parametric_liquids()
        Lines_2phase = self.create_parametric_2phases()
        Lines_suction = self.create_parametric_suctions()
        Lines_discharge = self.create_parametric_discharges()
        evaporators = self.create_parametric_evaporators()
        condensers = self.create_parametric_condensers()
        if self.expansion_type == "capillary":
            capillaries = self.create_parametric_capillaries()
        else:
            capillaries = (None,)
        objects = product(compressors,condensers,evaporators,Lines_liquid,
                          Lines_suction,Lines_discharge,Lines_2phase,
                          options,(None,),capillaries) # None here for the update_resiudals function
        self.objects = objects
        Cycle_list = []
        for object_set in objects:
            result = define_single(*object_set)
            if result[0]:
                Cycle = result[1]
                Cycle.REFPROP_path = self.refprop_path
                Cycle_list.append(Cycle)
            else:
                Cycle_list.append(0)
        return Cycle_list
    
    def create_parametric_options(self):
        if self.parametric_array[0,0]: # there is parammetric study for cycle options
            data = self.parametric_array[0,1] # getting cycle parametric data
            if self.first_condition == "subcooling":
                if data[0,0]: # subcooling
                    sc_value = tuple(data[0,1])
                    charge_value = (0,)
                else:
                    sc_value = (self.sc_value,)
                    charge_value = (0,)
            elif self.first_condition == "charge":
                if data[0,0]: # subcooling
                    charge_value = tuple(data[0,1])
                    sc_value = (0,)
                else:
                    charge_value = (self.charge_value,)
                    sc_value = (0,)
            if self.expansion_type == "TXV":
                if data[1,0]: # superheat
                    sh_value = tuple(data[1,1])
                else:
                    sh_value = (self.sh_value,)                
            elif self.expansion_type == "capillary":
                sh_value = (0,)
                
            if data[2,0]: # maximum number of iterations
                max_n_iterations = tuple(data[2,1])
            else:
                max_n_iterations = (self.max_n_iterations,)                
            
            if data[3,0]: # energy residual
                energy_tol = tuple(data[3,1])
            else:
                energy_tol = (self.energy_tol,)                

            if data[4,0]: # pressure residual
                pressure_tol = tuple(data[4,1])
            else:
                pressure_tol = (self.pressure_tol,)                

            if data[5,0]: # Mass flowrate residual
                mass_flowrate_tol = tuple(data[5,1])
            else:
                mass_flowrate_tol = (self.mass_flowrate_tol,)                

            if data[6,0]: # Mass residual
                mass_tol = tuple(data[6,1])
            else:
                mass_tol = (self.mass_tol,)                

            if data[7,0]: # solver
                solver = tuple(data[7,1])
            else:
                solver = (self.solver,)                

            if data[8,0]: # refrigerant
                refrigerant = tuple(data[8,1])
            else:
                refrigerant = (self.refrigerant,)                
            
            values = product(sc_value,charge_value,sh_value,max_n_iterations,
                             energy_tol,pressure_tol,mass_flowrate_tol,
                             mass_tol,solver,refrigerant)
            options_list = []
            for value in values:
                options_list.append({'Expansion_Device_Type':self.expansion_type,
                                    'sh_location':self.sh_location,
                                    'sh_value':value[2],
                                    'Second_Cond':self.first_condition,
                                    'sc_value':value[0],
                                    'charge_value':value[1],
                                    'Backend': self.Backend,
                                    'Ref': value[9],
                                    'Mode': self.Mode,
                                    'Tevap_init_manual': self.Tevap_type,
                                    'Tevap_init': self.Tevap_guess,
                                    'Tcond_init_manual': self.Tcond_type,
                                    'Tcond_init': self.Tcond_guess,
                                    'energy_tol': value[4],
                                    'pressure_tol': value[5],
                                    'mass_flowrate_tol': value[6],
                                    'mass_tol': value[7],
                                    'solver': value[8],
                                    'max_n_iterations': value[3],
                                   'Test_cond': self.Test_cond,
                                   'Accum_charge_per': self.Accum_charge_per,
                                    })
        else:
            options_list = [{'Expansion_Device_Type':self.expansion_type,
                            'sh_location':self.sh_location,
                            'sh_value':self.sh_value,
                            'Second_Cond':self.first_condition,
                            'sc_value':self.sc_value,
                            'charge_value':self.charge_value,
                            'Backend': self.Backend,
                            'Ref': self.refrigerant,
                            'Mode': self.Mode,
                            'Tevap_init_manual': self.Tevap_type,
                            'Tevap_init': self.Tevap_guess,
                            'Tcond_init_manual': self.Tcond_type,
                            'Tcond_init': self.Tcond_guess,
                            'energy_tol': self.energy_tol,
                            'pressure_tol': self.pressure_tol,
                            'mass_flowrate_tol': self.mass_flowrate_tol,
                            'mass_tol': self.mass_tol,
                            'solver': self.solver,
                            'max_n_iterations': self.max_n_iterations,
                            'Test_cond': self.Test_cond,
                            'Accum_charge_per': self.Accum_charge_per,
                            }]
        
        return tuple(options_list)
        
    def create_parametric_capillaries(self):
        if self.parametric_array[1,0]: # there is parammetric study for capillary
            capillary = self.capillary
            data = self.parametric_array[1,1] # getting capillary parametric data

            if data[0,0]: # capillary length
                Capillary_length = tuple(data[0,1])
            else:
                Capillary_length = (capillary.Capillary_length,)                
        
            if data[1,0]: # capillary diameter
                Capillary_D = tuple(data[1,1])
            else:
                Capillary_D = (capillary.Capillary_D,)                
    
            if data[2,0]: # capillary entrance diameter
                Capillary_entrance_D = tuple(data[2,1])
            else:
                Capillary_entrance_D = (capillary.Capillary_entrance_D,)                
    
            if data[3,0]: # number of parallel tubes
                Capillary_N_tubes = tuple(data[3,1])
            else:
                Capillary_N_tubes = (capillary.Capillary_N_tubes,)                
    
            if data[4,0]: # pressure tolerance
                Capillary_DP_tolerance = tuple(data[4,1])
            else:
                Capillary_DP_tolerance = (capillary.Capillary_DP_tolerance,)                
    
            if data[5,0]: # temperature discretization
                Capillary_DT = tuple(data[5,1])
            else:
                Capillary_DT = (capillary.Capillary_DT,)       
            
            values = product(Capillary_length,Capillary_D,Capillary_entrance_D,
                             Capillary_N_tubes,Capillary_DP_tolerance,
                             Capillary_DT)
            capillary_list = []
            for value in values:
                capillary_item = deepcopy(capillary)
                capillary_item.Capillary_length = value[0]
                capillary_item.Capillary_D = value[1]
                capillary_item.Capillary_entrance_D = value[2]
                capillary_item.Capillary_N_tubes = value[3]
                capillary_item.Capillary_DP_tolerance = value[4]
                capillary_item.Capillary_DT = value[5]
                capillary_list.append(capillary_item)
            
            return tuple(capillary_list)
        else:
            return (self.capillary,)
        
    def create_parametric_compressors(self):
        if self.parametric_array[2,0]: # there is parammetric study for compressor
            compressor = self.compressor
            data = self.parametric_array[2,1] # getting compressor parametric data

            if data[0,0]: # compressor speed
                Comp_speed = tuple(data[0,1])
            else:
                Comp_speed = (compressor.Comp_speed,)                
    
            if data[1,0]: # compressor heat loss fraction
                Comp_fp = tuple(data[1,1])
            else:
                Comp_fp = (compressor.Comp_fp,)                
    
            if data[2,0]: # compressor electric efficiency
                Comp_elec_eff = tuple(data[2,1])
            else:
                Comp_elec_eff = (compressor.Comp_elec_eff,)                
    
            if data[3,0]: # compressor mass flowrate multiplier
                Comp_ratio_M = tuple(data[3,1])
            else:
                Comp_ratio_M = (compressor.Comp_ratio_M,)                
    
            if data[4,0]: # compressor power multiplier
                Comp_ratio_P = tuple(data[4,1])
            else:
                Comp_ratio_P = (compressor.Comp_ratio_P,)                

            if data[5,0]: # compressor Volumetric displacement per revolution
                Comp_vol = tuple(data[5,1])
            else:
                Comp_vol = (compressor.Comp_vol,)                
    
            if data[6,0]: # compressors
                compressors = tuple(data[6,1])
            else:
                compressors = ([0,compressor],)
                
            values = product(compressors,Comp_speed,Comp_fp,Comp_elec_eff,Comp_ratio_M,
                             Comp_ratio_P,Comp_vol)
            compressor_list = []
            for value in values:
                compressor_item = deepcopy(value[0][1])
                if len(Comp_speed)>1:
                    compressor_item.Comp_speed = value[1]
                if len(Comp_fp)>1:
                    compressor_item.Comp_fp = value[2]
                if len(Comp_elec_eff)>1:
                    compressor_item.Comp_elec_eff = value[3]
                if len(Comp_ratio_M)>1:
                    compressor_item.Comp_ratio_M = value[4]
                if len(Comp_ratio_P)>1:
                    compressor_item.Comp_ratio_P = value[5]
                if len(Comp_vol)>1:
                    compressor_item.Comp_vol = value[6]
                compressor_list.append(compressor_item)
            return tuple(compressor_list)
        else:
            return (self.compressor,)
    
    def create_parametric_liquids(self):
        if self.parametric_array[3,0]: # there is parammetric study for liquid line
            liquid_line = self.liquid_line
            data = self.parametric_array[3,1] # getting liquid line parametric data

            if data[0,0]: # line length
                Line_length = tuple(data[0,1])
            else:
                Line_length = (liquid_line.Line_length,)                
        
            if data[1,0]: # line outer diameter
                Line_OD = tuple(data[1,1])
            else:
                Line_OD = (liquid_line.Line_OD,)                
    
            if data[2,0]: # line inner diameter
                Line_ID = tuple(data[2,1])
            else:
                Line_ID = (liquid_line.Line_ID,)                
    
            if data[3,0]: # line insulation thickness
                Line_insulation_t = tuple(data[3,1])
            else:
                Line_insulation_t = (liquid_line.Line_insulation_t,)                
    
            if data[4,0]: # line e/D ratio
                Line_e_D = tuple(data[4,1])
            else:
                Line_e_D = (liquid_line.Line_e_D,)                
    
            if data[5,0]: # line thermal conductivity
                Line_tube_k = tuple(data[5,1])
            else:
                Line_tube_k = (liquid_line.Line_tube_k,)       

            if data[6,0]: # insulation thermal conductivity
                Line_insulation_k = tuple(data[6,1])
            else:
                Line_insulation_k = (liquid_line.Line_insulation_k,)       

            if data[7,0]: # line surrounding temperature
                Line_surrounding_T = tuple(data[7,1])
            else:
                Line_surrounding_T = (liquid_line.Line_surrounding_T,)       

            if data[8,0]: # line surrounding HTC
                Line_surrounding_HTC = tuple(data[8,1])
            else:
                Line_surrounding_HTC = (liquid_line.Line_surrounding_HTC,)       
            
            values = product(Line_length,Line_OD,Line_ID,Line_insulation_t,
                             Line_e_D,Line_tube_k,Line_insulation_k,
                             Line_surrounding_T,Line_surrounding_HTC)
            liquid_line_list = []
            for value in values:
                liquid_line_item = deepcopy(liquid_line)
                liquid_line_item.Line_length = value[0]
                liquid_line_item.Line_OD = value[1]
                liquid_line_item.Line_ID = value[2]
                liquid_line_item.Line_insulation_t = value[3]
                liquid_line_item.Line_e_D = value[4]
                liquid_line_item.Line_tube_k = value[5]
                liquid_line_item.Line_insulation_k = value[6]
                liquid_line_item.Line_surrounding_T = value[7]
                liquid_line_item.Line_surrounding_HTC = value[8]
                liquid_line_list.append(liquid_line_item)
            return tuple(liquid_line_list)
        else:
            return (self.liquid_line,)

    def create_parametric_2phases(self):
        if self.parametric_array[4,0]: # there is parammetric study for twophase line
            twophase_line = self.twophase_line
            data = self.parametric_array[4,1] # getting twophase line parametric data

            if data[0,0]: # line length
                Line_length = tuple(data[0,1])
            else:
                Line_length = (twophase_line.Line_length,)                
        
            if data[1,0]: # line outer diameter
                Line_OD = tuple(data[1,1])
            else:
                Line_OD = (twophase_line.Line_OD,)                
    
            if data[2,0]: # line inner diameter
                Line_ID = tuple(data[2,1])
            else:
                Line_ID = (twophase_line.Line_ID,)                
    
            if data[3,0]: # line insulation thickness
                Line_insulation_t = tuple(data[3,1])
            else:
                Line_insulation_t = (twophase_line.Line_insulation_t,)                
    
            if data[4,0]: # line e/D ratio
                Line_e_D = tuple(data[4,1])
            else:
                Line_e_D = (twophase_line.Line_e_D,)                
    
            if data[5,0]: # line thermal conductivity
                Line_tube_k = tuple(data[5,1])
            else:
                Line_tube_k = (twophase_line.Line_tube_k,)       

            if data[6,0]: # insulation thermal conductivity
                Line_insulation_k = tuple(data[6,1])
            else:
                Line_insulation_k = (twophase_line.Line_insulation_k,)       

            if data[7,0]: # line surrounding temperature
                Line_surrounding_T = tuple(data[7,1])
            else:
                Line_surrounding_T = (twophase_line.Line_surrounding_T,)       

            if data[8,0]: # line surrounding HTC
                Line_surrounding_HTC = tuple(data[8,1])
            else:
                Line_surrounding_HTC = (twophase_line.Line_surrounding_HTC,)       
            
            values = product(Line_length,Line_OD,Line_ID,Line_insulation_t,
                             Line_e_D,Line_tube_k,Line_insulation_k,
                             Line_surrounding_T,Line_surrounding_HTC)
            twophase_line_list = []
            for value in values:
                twophase_line_item = deepcopy(twophase_line)
                twophase_line_item.Line_length = value[0]
                twophase_line_item.Line_OD = value[1]
                twophase_line_item.Line_ID = value[2]
                twophase_line_item.Line_insulation_t = value[3]
                twophase_line_item.Line_e_D = value[4]
                twophase_line_item.Line_tube_k = value[5]
                twophase_line_item.Line_insulation_k = value[6]
                twophase_line_item.Line_surrounding_T = value[7]
                twophase_line_item.Line_surrounding_HTC = value[8]
                twophase_line_list.append(twophase_line_item)
            return tuple(twophase_line_list)
        else:
            return (self.twophase_line,)

    def create_parametric_suctions(self):
        if self.parametric_array[5,0]: # there is parammetric study for suction line
            suction_line = self.suction_line
            data = self.parametric_array[5,1] # getting suction line parametric data

            if data[0,0]: # line length
                Line_length = tuple(data[0,1])
            else:
                Line_length = (suction_line.Line_length,)                
        
            if data[1,0]: # line outer diameter
                Line_OD = tuple(data[1,1])
            else:
                Line_OD = (suction_line.Line_OD,)                
    
            if data[2,0]: # line inner diameter
                Line_ID = tuple(data[2,1])
            else:
                Line_ID = (suction_line.Line_ID,)                
    
            if data[3,0]: # line insulation thickness
                Line_insulation_t = tuple(data[3,1])
            else:
                Line_insulation_t = (suction_line.Line_insulation_t,)                
    
            if data[4,0]: # line e/D ratio
                Line_e_D = tuple(data[4,1])
            else:
                Line_e_D = (suction_line.Line_e_D,)                
    
            if data[5,0]: # line thermal conductivity
                Line_tube_k = tuple(data[5,1])
            else:
                Line_tube_k = (suction_line.Line_tube_k,)       

            if data[6,0]: # insulation thermal conductivity
                Line_insulation_k = tuple(data[6,1])
            else:
                Line_insulation_k = (suction_line.Line_insulation_k,)       

            if data[7,0]: # line surrounding temperature
                Line_surrounding_T = tuple(data[7,1])
            else:
                Line_surrounding_T = (suction_line.Line_surrounding_T,)       

            if data[8,0]: # line surrounding HTC
                Line_surrounding_HTC = tuple(data[8,1])
            else:
                Line_surrounding_HTC = (suction_line.Line_surrounding_HTC,)       
            
            values = product(Line_length,Line_OD,Line_ID,Line_insulation_t,
                             Line_e_D,Line_tube_k,Line_insulation_k,
                             Line_surrounding_T,Line_surrounding_HTC)
            suction_line_list = []
            for value in values:
                suction_line_item = deepcopy(suction_line)
                suction_line_item.Line_length = value[0]
                suction_line_item.Line_OD = value[1]
                suction_line_item.Line_ID = value[2]
                suction_line_item.Line_insulation_t = value[3]
                suction_line_item.Line_e_D = value[4]
                suction_line_item.Line_tube_k = value[5]
                suction_line_item.Line_insulation_k = value[6]
                suction_line_item.Line_surrounding_T = value[7]
                suction_line_item.Line_surrounding_HTC = value[8]
                suction_line_list.append(suction_line_item)
            return tuple(suction_line_list)
        else:
            return (self.suction_line,)

    def create_parametric_discharges(self):
        if self.parametric_array[6,0]: # there is parammetric study for discharge line
            discharge_line = self.discharge_line
            data = self.parametric_array[6,1] # getting discharge line parametric data

            if data[0,0]: # line length
                Line_length = tuple(data[0,1])
            else:
                Line_length = (discharge_line.Line_length,)                
        
            if data[1,0]: # line outer diameter
                Line_OD = tuple(data[1,1])
            else:
                Line_OD = (discharge_line.Line_OD,)                
    
            if data[2,0]: # line inner diameter
                Line_ID = tuple(data[2,1])
            else:
                Line_ID = (discharge_line.Line_ID,)                
    
            if data[3,0]: # line insulation thickness
                Line_insulation_t = tuple(data[3,1])
            else:
                Line_insulation_t = (discharge_line.Line_insulation_t,)                
    
            if data[4,0]: # line e/D ratio
                Line_e_D = tuple(data[4,1])
            else:
                Line_e_D = (discharge_line.Line_e_D,)                
    
            if data[5,0]: # line thermal conductivity
                Line_tube_k = tuple(data[5,1])
            else:
                Line_tube_k = (discharge_line.Line_tube_k,)       

            if data[6,0]: # insulation thermal conductivity
                Line_insulation_k = tuple(data[6,1])
            else:
                Line_insulation_k = (discharge_line.Line_insulation_k,)       

            if data[7,0]: # line surrounding temperature
                Line_surrounding_T = tuple(data[7,1])
            else:
                Line_surrounding_T = (discharge_line.Line_surrounding_T,)       

            if data[8,0]: # line surrounding HTC
                Line_surrounding_HTC = tuple(data[8,1])
            else:
                Line_surrounding_HTC = (discharge_line.Line_surrounding_HTC,)       
            
            values = product(Line_length,Line_OD,Line_ID,Line_insulation_t,
                             Line_e_D,Line_tube_k,Line_insulation_k,
                             Line_surrounding_T,Line_surrounding_HTC)
            discharge_line_list = []
            for value in values:
                discharge_line_item = deepcopy(discharge_line)
                discharge_line_item.Line_length = value[0]
                discharge_line_item.Line_OD = value[1]
                discharge_line_item.Line_ID = value[2]
                discharge_line_item.Line_insulation_t = value[3]
                discharge_line_item.Line_e_D = value[4]
                discharge_line_item.Line_tube_k = value[5]
                discharge_line_item.Line_insulation_k = value[6]
                discharge_line_item.Line_surrounding_T = value[7]
                discharge_line_item.Line_surrounding_HTC = value[8]
                discharge_line_list.append(discharge_line_item)
            return tuple(discharge_line_list)
        else:
            return (self.discharge_line,)

    def create_parametric_evaporators(self):
        if self.parametric_array[7,0]: # there is parammetric study for evaporator
            evaporator = self.evaporator
            data = self.parametric_array[7,1] # getting evaporator parametric data
            if hasattr(evaporator,"circuits"): #fintube heat exchanger
                # circuits data
                circuits = data[0,1]
                circuits_list = []
                for i,circuit in enumerate(circuits):
                    if circuit[0,0]: # tube length
                        Ltube = tuple(circuit[0,1])
                    else:
                        Ltube = evaporator.circuits[i].Ltube,

                    if circuit[1,0]: # tube OD
                        OD = tuple(circuit[1,1])
                    else:
                        OD = evaporator.circuits[i].OD,

                    if circuit[2,0]: # tube ID
                        ID = tuple(circuit[2,1])
                    else:
                        if hasattr(evaporator.circuits[i],"ID"):
                            ID = evaporator.circuits[i].ID,
                        else:
                            ID = evaporator.circuits[i].OD * 0.8,

                    if circuit[3,0]: # tube logitudinal pitch
                        Pl = tuple(circuit[3,1])
                    else:
                        Pl = evaporator.circuits[i].Pl,

                    if circuit[4,0]: # tube transverse pitch
                        Pt = tuple(circuit[4,1])
                    else:
                        Pt = evaporator.circuits[i].Pt,

                    if circuit[5,0]: # number of parallel cirucits
                        N_Circuits = tuple(circuit[5,1])
                    else:
                        N_Circuits = evaporator.circuits[i].N_Circuits,

                    if circuit[6,0]: # Number of tubes per bank
                        N_tube_per_bank = tuple(circuit[6,1])
                    else:
                        N_tube_per_bank = evaporator.circuits[i].N_tube_per_bank,

                    if circuit[7,0]: # Number of banks
                        N_bank = tuple(circuit[7,1])
                    else:
                        N_bank = evaporator.circuits[i].N_bank,

                    if circuit[8,0]: # Fin thickness
                        Fin_t = tuple(circuit[8,1])
                    else:
                        Fin_t = evaporator.circuits[i].Fin_t,

                    if circuit[9,0]: # Fin FPI
                        Fin_FPI = tuple(circuit[9,1])
                    else:
                        Fin_FPI = evaporator.circuits[i].Fin_FPI,

                    circuit_values = product(Ltube,OD,ID,Pl,Pt,N_Circuits,N_tube_per_bank,Fin_t,Fin_FPI)
                    circuit_list = []
                    for value in circuit_values:
                        circuit_item = deepcopy(evaporator.circuits[i])
                        circuit_item.Ltube = value[0]
                        circuit_item.OD = value[1]
                        circuit_item.ID = value[2]
                        circuit_item.Pl = value[3]
                        circuit_item.Pt = value[4]
                        circuit_item.N_Circuits = value[5]
                        circuit_item.N_tube_per_bank = value[6]
                        circuit_item.Fin_t = value[7]
                        circuit_item.Fin_FPI = value[8]
                        circuit_list.append(circuit_item)
                    circuit_list = tuple(circuit_list)
                    circuits_list.append(circuit_list)
                potential_circuits = product(*circuits_list)
                potential_circuits = (list(group) for group in potential_circuits)
                if data[1,0]: # Air Volume Flowrate
                    Vdot_ha = tuple(data[1,1])
                else:
                    if hasattr(evaporator,"Vdot_ha"):
                        Vdot_ha = (evaporator.Vdot_ha,)
                    else:
                        v_spec = HAPropsSI("V","T",evaporator.Air_T,"R",evaporator.Air_RH,"P",evaporator.Air_P)
                        Vdot_ha = (evaporator.mdot_da * v_spec,)
            
                if data[2,0]: # Air Pressure
                    Air_P = tuple(data[2,1])
                else:
                    Air_P = (evaporator.Air_P,)                
        
                if data[3,0]: # Air Temperature
                    Air_T = tuple(data[3,1])
                else:
                    Air_T = (evaporator.Air_T,)                
        
                if data[4,0]: # Air Relative Humidity
                    Air_RH = tuple(data[4,1])
                else:
                    Air_RH = (evaporator.Air_RH,)                
                
                values = product(potential_circuits,Vdot_ha,Air_P,Air_T,Air_RH)
                evaporator_list = []
                for value in values:
                    evaporator_item = deepcopy(evaporator)
                    evaporator_item.circuits = list(value[0])
                    evaporator_item.Vdot_ha = value[1]
                    evaporator_item.Air_P = value[2]
                    evaporator_item.Air_T = value[3]
                    evaporator_item.Air_RH = value[4]
                    evaporator_list.append(evaporator_item)
                return tuple(evaporator_list)
            else: # microchannel
                if data[0,0]: # Tube width
                    T_w = tuple(data[0,1])
                else:
                    T_w = (evaporator.Geometry.T_w,)                
            
                if data[1,0]: # Tube height
                    T_h = tuple(data[1,1])
                else:
                    T_h = (evaporator.Geometry.T_h,)                
        
                if data[2,0]: # Tube length
                    T_l = tuple(data[2,1])
                else:
                    T_l = (evaporator.Geometry.T_l,)                
        
                if data[3,0]: # Tube spacing
                    T_s = tuple(data[3,1])
                else:
                    T_s = (evaporator.Geometry.T_s,)                
        
                if data[4,0]: # Number of ports
                    N_ports = tuple(data[4,1])
                else:
                    N_ports = (evaporator.Geometry.N_ports,)                
        
                if data[5,0]: # Port Dimension a
                    port_a_dim = tuple(data[5,1])
                else:
                    port_a_dim = (evaporator.Geometry.port_a_dim,)       
    
                if data[6,0]: # Port Dimension b
                    port_b_dim = tuple(data[6,1])
                else:
                    port_b_dim = (evaporator.Geometry.port_b_dim,)       
    
                if data[7,0]: # Fin Thickness
                    Fin_t = tuple(data[7,1])
                else:
                    Fin_t = (evaporator.Geometry.Fin_t,)       
    
                if data[8,0]: # Fin FPI
                    Fin_FPI = tuple(data[8,1])
                else:
                    Fin_FPI = (evaporator.Geometry.Fin_FPI,)       

                if data[9,0]: # Air inlet humid flow rate
                    Vdot_ha = tuple(data[9,1])
                else:
                    if hasattr(evaporator,"Vdot_ha"):
                        Vdot_ha = (evaporator.Vdot_ha,)
                    else:
                        v_spec = HAPropsSI("V","T",evaporator.Air_T,"R",evaporator.Air_RH,"P",evaporator.Air_P)
                        Vdot_ha = (evaporator.mdot_da * v_spec,)

                if data[10,0]: # Air Pressure
                    Air_P = tuple(data[10,1])
                else:
                    Air_P = (evaporator.Air_P,)       

                if data[11,0]: # Air Temperature
                    Air_T = tuple(data[11,1])
                else:
                    Air_T = (evaporator.Air_T,)       

                if data[12,0]: # Air RH
                    Air_RH = tuple(data[12,1])
                else:
                    Air_RH = (evaporator.Air_RH,)       
                
                values = product(T_w,T_h,T_l,T_s,N_ports,port_a_dim,port_b_dim,
                                 Fin_t,Fin_FPI,Vdot_ha,Air_P,Air_T,Air_RH)
                evaporator_list = []
                for value in values:
                    evaporator_item = deepcopy(evaporator)
                    evaporator_item.Geometry.T_w = value[0]
                    evaporator_item.Geometry.T_h = value[1]
                    evaporator_item.Geometry.T_l = value[2]
                    evaporator_item.Geometry.T_s = value[3]
                    evaporator_item.Geometry.N_ports = value[4]
                    evaporator_item.Geometry.port_a_dim = value[5]
                    evaporator_item.Geometry.port_b_dim = value[6]
                    evaporator_item.Geometry.Fin_t = value[7]
                    evaporator_item.Geometry.Fin_FPI = value[8]
                    evaporator_item.Vdot_ha = value[9]
                    evaporator_item.Air_P = value[10]
                    evaporator_item.Air_T = value[11]
                    evaporator_item.Air_RH = value[12]
                    evaporator_list.append(evaporator_item)
                return tuple(evaporator_list)
        else:
            return (self.evaporator,)

    def create_parametric_condensers(self):
        if self.parametric_array[8,0]: # there is parammetric study for condenser
            condenser = self.condenser
            data = self.parametric_array[8,1] # getting condenser parametric data
            if hasattr(condenser,"circuits"): #fintube heat exchanger
                # circuits data
                circuits = data[0,1]
                circuits_list = []
                for i,circuit in enumerate(circuits):
                    if circuit[0,0]: # tube length
                        Ltube = tuple(circuit[0,1])
                    else:
                        Ltube = condenser.circuits[i].Ltube,

                    if circuit[1,0]: # tube OD
                        OD = tuple(circuit[1,1])
                    else:
                        OD = condenser.circuits[i].OD,

                    if circuit[2,0]: # tube ID
                        ID = tuple(circuit[2,1])
                    else:
                        if hasattr(condenser.circuits[i],"ID"):
                            ID = condenser.circuits[i].ID,
                        else:
                            ID = condenser.circuits[i].OD * 0.8,

                    if circuit[3,0]: # tube logitudinal pitch
                        Pl = tuple(circuit[3,1])
                    else:
                        Pl = condenser.circuits[i].Pl,

                    if circuit[4,0]: # tube transverse pitch
                        Pt = tuple(circuit[4,1])
                    else:
                        Pt = condenser.circuits[i].Pt,

                    if circuit[5,0]: # number of parallel cirucits
                        N_Circuits = tuple(circuit[5,1])
                    else:
                        N_Circuits = condenser.circuits[i].N_Circuits,

                    if circuit[6,0]: # Number of tubes per bank
                        N_tube_per_bank = tuple(circuit[6,1])
                    else:
                        N_tube_per_bank = condenser.circuits[i].N_tube_per_bank,

                    if circuit[7,0]: # Number of banks
                        N_bank = tuple(circuit[7,1])
                    else:
                        N_bank = condenser.circuits[i].N_bank,

                    if circuit[8,0]: # Fin thickness
                        Fin_t = tuple(circuit[8,1])
                    else:
                        Fin_t = condenser.circuits[i].Fin_t,

                    if circuit[9,0]: # Fin FPI
                        Fin_FPI = tuple(circuit[9,1])
                    else:
                        Fin_FPI = condenser.circuits[i].Fin_FPI,

                    circuit_values = product(Ltube,OD,ID,Pl,Pt,N_Circuits,N_tube_per_bank,Fin_t,Fin_FPI)
                    circuit_list = []
                    for value in circuit_values:
                        circuit_item = deepcopy(condenser.circuits[i])
                        circuit_item.Ltube = value[0]
                        circuit_item.OD = value[1]
                        circuit_item.ID = value[2]
                        circuit_item.Pl = value[3]
                        circuit_item.Pt = value[4]
                        circuit_item.N_Circuits = value[5]
                        circuit_item.N_tube_per_bank = value[6]
                        circuit_item.Fin_t = value[7]
                        circuit_item.Fin_FPI = value[8]
                        circuit_list.append(circuit_item)
                    circuit_list = tuple(circuit_list)
                    circuits_list.append(circuit_list)
                potential_circuits = product(*circuits_list)
                potential_circuits = (list(group) for group in potential_circuits)
                if data[1,0]: # Air Volume Flowrate
                    Vdot_ha = tuple(data[1,1])
                else:
                    if hasattr(condenser,"Vdot_ha"):
                        Vdot_ha = (condenser.Vdot_ha,)
                    else:
                        v_spec = HAPropsSI("V","T",condenser.Air_T,"R",condenser.Air_RH,"P",condenser.Air_P)
                        Vdot_ha = (condenser.mdot_da * v_spec,)
            
                if data[2,0]: # Air Pressure
                    Air_P = tuple(data[2,1])
                else:
                    Air_P = (condenser.Air_P,)                
        
                if data[3,0]: # Air Temperature
                    Air_T = tuple(data[3,1])
                else:
                    Air_T = (condenser.Air_T,)                
        
                if data[4,0]: # Air Relative Humidity
                    Air_RH = tuple(data[4,1])
                else:
                    Air_RH = (condenser.Air_RH,)                
                
                values = product(potential_circuits,Vdot_ha,Air_P,Air_T,Air_RH)
                condenser_list = []
                for value in values:
                    condenser_item = deepcopy(condenser)
                    condenser_item.circuits = list(value[0])
                    condenser_item.Vdot_ha = value[1]
                    condenser_item.Air_P = value[2]
                    condenser_item.Air_T = value[3]
                    condenser_item.Air_RH = value[4]
                    condenser_list.append(condenser_item)
                return tuple(condenser_list)
            else: # microchannel
                if data[0,0]: # Tube width
                    T_w = tuple(data[0,1])
                else:
                    T_w = (condenser.Geometry.T_w,)                
            
                if data[1,0]: # Tube height
                    T_h = tuple(data[1,1])
                else:
                    T_h = (condenser.Geometry.T_h,)                
        
                if data[2,0]: # Tube length
                    T_l = tuple(data[2,1])
                else:
                    T_l = (condenser.Geometry.T_l,)                
        
                if data[3,0]: # Tube spacing
                    T_s = tuple(data[3,1])
                else:
                    T_s = (condenser.Geometry.T_s,)                
        
                if data[4,0]: # Number of ports
                    N_ports = tuple(data[4,1])
                else:
                    N_ports = (condenser.Geometry.N_ports,)                
        
                if data[5,0]: # Port Dimension a
                    port_a_dim = tuple(data[5,1])
                else:
                    port_a_dim = (condenser.Geometry.port_a_dim,)       
    
                if data[6,0]: # Port Dimension b
                    port_b_dim = tuple(data[6,1])
                else:
                    port_b_dim = (condenser.Geometry.port_b_dim,)       
    
                if data[7,0]: # Fin Thickness
                    Fin_t = tuple(data[7,1])
                else:
                    Fin_t = (condenser.Geometry.Fin_t,)       
    
                if data[8,0]: # Fin FPI
                    Fin_FPI = tuple(data[8,1])
                else:
                    Fin_FPI = (condenser.Geometry.Fin_FPI,)       

                if data[9,0]: # Air inlet humid flow rate
                    Vdot_ha = tuple(data[9,1])
                else:
                    if hasattr(condenser,"Vdot_ha"):
                        Vdot_ha = (condenser.Vdot_ha,)
                    else:
                        v_spec = HAPropsSI("V","T",condenser.Air_T,"R",condenser.Air_RH,"P",condenser.Air_P)
                        Vdot_ha = (condenser.mdot_da * v_spec,)
                        
                if data[10,0]: # Air Pressure
                    Air_P = tuple(data[10,1])
                else:
                    Air_P = (condenser.Air_P,)       

                if data[11,0]: # Air Temperature
                    Air_T = tuple(data[11,1])
                else:
                    Air_T = (condenser.Air_T,)       

                if data[12,0]: # Air RH
                    Air_RH = tuple(data[12,1])
                else:
                    Air_RH = (condenser.Air_RH,)       
                
                values = product(T_w,T_h,T_l,T_s,N_ports,port_a_dim,port_b_dim,
                                 Fin_t,Fin_FPI,Vdot_ha,Air_P,Air_T,Air_RH)
                condenser_list = []
                for value in values:
                    condenser_item = deepcopy(condenser)
                    condenser_item.Geometry.T_w = value[0]
                    condenser_item.Geometry.T_h = value[1]
                    condenser_item.Geometry.T_l = value[2]
                    condenser_item.Geometry.T_s = value[3]
                    condenser_item.Geometry.N_ports = value[4]
                    condenser_item.Geometry.port_a_dim = value[5]
                    condenser_item.Geometry.port_b_dim = value[6]
                    condenser_item.Geometry.Fin_t = value[7]
                    condenser_item.Geometry.Fin_FPI = value[8]
                    condenser_item.Vdot_ha = value[9]
                    condenser_item.Air_P = value[10]
                    condenser_item.Air_T = value[11]
                    condenser_item.Air_RH = value[12]
                    condenser_list.append(condenser_item)
                return tuple(condenser_list)
        else:
            return (self.condenser,)

def run_cycle(x):
    i = x[0]
    Cycle = x[1]
    pipe = x[2]
    expansion_type = x[3]
    message = "Solving cycle Configuration "+str(i+1)
    time.sleep(0.1)
    pipe.put([0,message])
    if Cycle != 0:
        if expansion_type == "capillary":
            result = Cycle.Calculate(Cycle.solver_option)
            if result[0]:
                if abs(Cycle.Capillary.Results.Pout_r - Cycle.Capillary.Pout_r_target) > Cycle.Capillary.DP_converged:
                    message = "Capillary tube is choked in Cycle Configuration "+str(i+1)+"; Capillary tube exit pressure is higher than two-phase line inlet pressure"
                    pipe.put([1,message])
                result_output = create_outputs_array(Cycle)
                return (1,result_output)
            else:
                if Cycle.check_terminate:
                    message = "Cycle Configuration "+str(i+1)+" was terminated by user!"
                    pipe.put([0,message])
                else:    
                    message = "Cycle Configuration "+str(i+1)+" Failed!"
                    pipe.put([0,message])
                if hasattr(Cycle,"Solver_Error"):
                    return (0,Cycle.Solver_Error)
                else:
                    return (0,"")
        elif expansion_type == "TXV":
            result = Cycle.Calculate(Cycle.solver_option)
            if result[0]:
                message = "Cycle Configuration "+str(i+1)+" Succeeded!"
                pipe.put([0,message])
                result_output = create_outputs_array(Cycle)
                return (1,result_output)
            else:
                if Cycle.check_terminate:
                    message = "Cycle Configuration "+str(i+1)+" was terminated by user!"
                    pipe.put([0,message])
                else:    
                    message = "Cycle Configuration "+str(i+1)+" Failed!"
                    pipe.put([0,message])
                if hasattr(Cycle,"Solver_Error"):
                    return (0,Cycle.Solver_Error)
                else:
                    return (0,"")
        return (0,"")
    else:
        message = "Cycle Configuration "+str(i+1)+" Failed!"
        pipe.put([0,message])
        return (0,"Failed to define cycle, there is a problem with one of the inputs")
