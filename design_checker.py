import appdirs
from backend.CompressorAHRI import CompressorAHRIClass
from backend.CompressorPHY import CompressorPHYClass
from GUI_functions import load_refrigerant_list
from backend.FinTubeHEX import FinTubeHEXClass
from backend.MicroChannelHEX import MicroChannelHEXClass
from PyQt5.QtCore import QObject, pyqtSignal
from lxml import etree as ET
import CoolProp as CP
from CoolProp.CoolProp import HAPropsSI
from scipy.optimize import root, newton
from backend.Functions import get_AS

class values():
    pass

class check_design_object(QObject):
    finished = pyqtSignal(tuple)
    def __init__(self,parent_instance,parent=None):
        super(check_design_object, self).__init__(parent)
        self.parent_instance = parent_instance
        
    def check_design_fn(self):
        parent = self.parent_instance
        try:
            validate = self.validate(parent)
            if validate == 1:
                self.finished.emit((0, "Can not perform design check while parametric study is enabled"))
                raise
            elif validate == 2:
                self.finished.emit((0, "Can not perform design check unless subcooling condition and TXV are chosen"))
                raise
            elif validate == 3:
                self.finished.emit((0, "Please fill subcool, superheat and target capacity values on cycle parameters page"))
                raise
            elif validate == 4:
                self.finished.emit((0, "Please choose a condenser, an evaporator and a compressor"))
                raise
            elif validate == 5:
                self.finished.emit((0, "can not use REFPROP, please fix REFPROP implementation or choose HEOS in cycle parameters page"))
                raise
            elif validate == 6:
                self.finished.emit((0, "could not import error messages xml file."))
                raise
            elif validate == 0:
                if parent.Cycle_mode.currentIndex() == 0:
                    condenser_name = "Outdoor Unit"
                    evaporator_name = "Indoor Unit"
                elif parent.Cycle_mode.currentIndex() == 1:
                    condenser_name = "Indoor Unit"
                    evaporator_name = "Outdoor Unit"
                
                if parent.Condenser_type.currentIndex() == 0:
                    condenser = parent.Fintube_list[parent.selected_condenser_index][1]
        
                elif parent.Condenser_type.currentIndex() == 1:
                    condenser = parent.Microchannel_list[parent.selected_condenser_index][1]
                    
                if parent.Evaporator_type.currentIndex() == 0:
                    evaporator = parent.Fintube_list[parent.selected_evaporator_index][1]
        
                elif parent.Evaporator_type.currentIndex() == 1:
                    evaporator = parent.Microchannel_list[parent.selected_evaporator_index][1]
                    
                compressor = parent.Compressor_list[parent.selected_compressor_index][1]
                
                reference_values = self.import_reference_values()
                if reference_values[0]:
                    TTD_evap_AC_ref,TTD_cond_AC_ref,TTD_evap_HP_ref,TTD_cond_HP_ref,DT_sat_max_evap,DT_sat_max_cond,Capacity_tolerance = reference_values[1]
                else:
                    self.finished.emit((0, "Failed to load design check properties"))
                    raise
                
                Target_capacity = float(parent.Capacity_target.text())
                mode_index = parent.Cycle_mode.currentIndex()
                if mode_index == 0:
                    mode = "AC"
                    TTD_evap_ref = TTD_evap_AC_ref
                    TTD_cond_ref = TTD_cond_AC_ref
                else:
                    mode = "HP"
                    TTD_evap_ref = TTD_evap_HP_ref
                    TTD_cond_ref = TTD_cond_HP_ref
                
                SC = float(parent.Subcooling.text())
                SH = float(parent.Superheat.text())

                Test_cond = parent.Test_Condition.currentText()
                if Test_cond == "Custom":
                    Tin_a_evap = evaporator.Air_T
                    Win_a_evap = HAPropsSI("W","T",evaporator.Air_T,"P",evaporator.Air_P,"R",evaporator.Air_RH)
                    Tin_a_cond = condenser.Air_T
                    Win_a_cond = HAPropsSI("W","T",condenser.Air_T,"P",condenser.Air_P,"R",condenser.Air_RH)        
        
                elif Test_cond == "T1":
                    Tin_a_evap = 27 + 273.15
                    Win_a_evap = HAPropsSI("W","T", 27 + 273.15,"P",evaporator.Air_P,"B", 19 + 273.15)
                    Tin_a_cond = 35 + 273.15
                    Win_a_cond = HAPropsSI("W","T", 35 + 273.15,"P",condenser.Air_P,"B", 24 + 273.15)        
        
                elif Test_cond == "T2":
                    Tin_a_evap = 21 + 273.15
                    Win_a_evap = HAPropsSI("W","T", 21 + 273.15,"P",evaporator.Air_P,"B", 15 + 273.15)
                    Tin_a_cond = 27 + 273.15
                    Win_a_cond = HAPropsSI("W","T", 27 + 273.15,"P",condenser.Air_P,"B", 19 + 273.15)        
        
                elif Test_cond == "T3":
                    Tin_a_evap = 29 + 273.15
                    Win_a_evap = HAPropsSI("W","T", 29 + 273.15,"P",evaporator.Air_P,"B", 19 + 273.15)
                    Tin_a_cond = 46 + 273.15
                    Win_a_cond = HAPropsSI("W","T", 46 + 273.15,"P",condenser.Air_P,"B", 24 + 273.15)        
        
                elif Test_cond == "H1":
                    Tin_a_evap = 7 + 273.15
                    Win_a_evap = HAPropsSI("W","T", 7 + 273.15,"P",evaporator.Air_P,"B",6 + 273.15)
                    Tin_a_cond = 20 + 273.15
                    Win_a_cond = HAPropsSI("W","T",20 + 273.15,"P",evaporator.Air_P,"B",15 + 273.15)
        
                elif Test_cond == "H2":
                    Tin_a_evap = 2 + 273.15
                    Win_a_evap = HAPropsSI("W","T", 2 + 273.15,"P",evaporator.Air_P,"B",1 + 273.15)
                    Tin_a_cond = 20 + 273.15
                    Win_a_cond = HAPropsSI("W","T",20 + 273.15,"P",evaporator.Air_P,"B",15 + 273.15)
        
                elif Test_cond == "H3":
                    Tin_a_evap = -7 + 273.15
                    Win_a_evap = HAPropsSI("W","T", -7 + 273.15,"P",evaporator.Air_P,"B",-8 + 273.15)
                    Tin_a_cond = 20 + 273.15
                    Win_a_cond = HAPropsSI("W","T",20 + 273.15,"P",evaporator.Air_P,"B",15 + 273.15)

                Tsat_cond_init = Tin_a_cond +TTD_cond_ref + SC
    
                Tsat_evap_init = Tin_a_evap - TTD_evap_ref - SH

                ref_list = load_refrigerant_list()
                if not ref_list[0]:
                    self.finished.emit((0, "Could not load refrigerant list"))
                    raise

                ref_list = ref_list[1]          

                Ref = parent.Cycle_refrigerant.currentText()

                if parent.Ref_library.currentIndex() == 0:
                    Backend = "REFPROP"
                else:
                    Backend = "HEOS"
                AS = get_AS(Backend,Ref,None)
                if AS[0]:
                    AS = AS[1]
                else:
                    raise
                    
                if parent.Condenser_type.currentIndex() == 0:    
                    cond_type = "fintube"
                else:
                    cond_type = "microchannel"
    
                if parent.Evaporator_type.currentIndex() == 0:    
                    evap_type = "fintube"
                else:
                    evap_type = "microchannel"            

                try:
                    def objective(x):
                        Tsat_cond = x[0]
                        Tsat_evap = x[1]
                        
                        props = {"mode": mode,
                                 "Tsat_cond": Tsat_cond,
                                 "Tsat_evap": Tsat_evap,
                                 "Capacity_tolerance": Capacity_tolerance,
                                 "SC":SC,
                                 "SH":SH,
                                 "AS":AS,
                                 "cond_type":cond_type,
                                 "evap_type":evap_type,
                                 "Tin_a_evap": Tin_a_evap,
                                 "Win_a_evap": Win_a_evap,
                                 "Tin_a_cond": Tin_a_cond,
                                 "Win_a_cond": Win_a_cond,
                            }
                        comp = self.solve_compressor(compressor, props)
                        
                        AS.update(CP.QT_INPUTS, 0.0, Tsat_cond)
                        psat_cond = AS.p()
                        AS.update(CP.PT_INPUTS, psat_cond, Tsat_cond - SC)
                        hin_evap = AS.hmass()
            
                        AS.update(CP.QT_INPUTS, 1.0, Tsat_cond)
                        psat_cond = AS.p()
            
                        AS.update(CP.QT_INPUTS, 1.0, Tsat_evap)
                        psat_evap = AS.p()
                        
                        DP_evap, Q_evap, DT_Pinch_evap, TTD_evap = self.solve_HX(evaporator, props, psat_evap, hin_evap, comp.mdot_r, props["evap_type"],'evaporator')
                        DP_cond, Q_cond, DT_Pinch_cond, TTD_cond = self.solve_HX(condenser, props, psat_cond, comp.hout_r, comp.mdot_r, props["cond_type"],'condenser')
                        
                        resid = []
                        if abs((TTD_cond - TTD_cond_ref)/TTD_cond_ref) < 0.0001:
                            resid.append(0)
                        else:
                            resid.append(TTD_cond - TTD_cond_ref)

                        if abs((TTD_evap - TTD_evap_ref)/TTD_evap_ref) < 0.0001:
                            resid.append(0)
                        else:
                            resid.append(TTD_evap - TTD_evap_ref)
                        return resid
                    
                    def objective1(Tsat_evap):
                        # wrapper to solve just evaporator
                        resid = objective([Tsat_cond_init,Tsat_evap])
                        return resid[1]

                    def objective2(Tsat_cond):
                        # wrapper to solve just condenser
                        resid = objective([Tsat_cond,Tsat_evap])
                        return resid[0]
                    
                    try:
                        Tsat_evap = newton(objective1,Tsat_evap_init)
                    except:
                        Tsat_evap = root(objective1,Tsat_evap_init,method='hybr')['x']

                    try:
                        Tsat_cond = newton(objective2, Tsat_cond_init)
                    except:
                        Tsat_cond = root(objective2,Tsat_cond_init,method='hybr')['x']

                    try:
                        Tsat_cond,Tsat_evap = newton(objective, [Tsat_cond,Tsat_evap])
                    except:
                        Tsat_cond,Tsat_evap = root(objective,[Tsat_cond,Tsat_evap],method='hybr')['x']
                                        
                    props = {"mode": mode,
                             "Tsat_cond": Tsat_cond,
                             "Tsat_evap": Tsat_evap,
                             "Capacity_tolerance": Capacity_tolerance,
                             "SC":SC,
                             "SH":SH,
                             "AS":AS,
                             "cond_type":cond_type,
                             "evap_type":evap_type,
                             "Tin_a_evap": Tin_a_evap,
                             "Win_a_evap": Win_a_evap,
                             "Tin_a_cond": Tin_a_cond,
                             "Win_a_cond": Win_a_cond,
                        }
                    comp = self.solve_compressor(compressor, props)
                    
                    AS.update(CP.QT_INPUTS, 0.0, Tsat_cond)
                    psat_cond = AS.p()
                    AS.update(CP.PT_INPUTS, psat_cond, Tsat_cond - SC)
                    hin_evap = AS.hmass()
        
                    AS.update(CP.QT_INPUTS, 1.0, Tsat_cond)
                    psat_cond = AS.p()
        
                    AS.update(CP.QT_INPUTS, 1.0, Tsat_evap)
                    psat_evap = AS.p()
                    
                    DP_evap, Q_evap, DT_Pinch_evap, TTD_evap = self.solve_HX(evaporator, props, psat_evap, hin_evap, comp.mdot_r, props["evap_type"],'evaporator')
                    DP_cond, Q_cond, DT_Pinch_cond, TTD_cond = self.solve_HX(condenser, props, psat_cond, comp.hout_r, comp.mdot_r, props["cond_type"],'condenser')
                    
                    if (abs(TTD_cond - TTD_cond_ref) > 0.01)  or (abs(TTD_evap - TTD_evap_ref) > 0.01):
                        raise
                    
                    error_message = ""
                    if mode == "AC":
                        Q_compressor = comp.mdot_r * (comp.hin_r - hin_evap)
                        
                        # compressor checks
                        if (Q_compressor - Target_capacity) / (Target_capacity) > Capacity_tolerance:
                            error_message += "<h3>Compressor Capacity</h3><p>"+self.AC_errors.Compressor_Capacity_over.replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+"</p>"
                        elif (Q_compressor - Target_capacity) / (Target_capacity) < (-1 * Capacity_tolerance):
                            error_message += "<h3>Compressor Capacity</h3><p>"+self.AC_errors.Compressor_Capacity_under_AC.replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+"</p>"
                        
                        # evaporator checks
                        if (abs(Q_evap) - Target_capacity) / (Target_capacity) > Capacity_tolerance:
                            error_message += "<h3>Evaporator Capacity</h3><p>".replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+self.AC_errors.Evaporator_Capacity_over.replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+"</p>"
                        elif (abs(Q_evap) - Target_capacity) / (Target_capacity) < (-1 * Capacity_tolerance):
                            if DT_Pinch_evap > 2.5:
                                error_message += "<h3>Evaporator Capacity</h3><p>".replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+self.AC_errors.Evaporator_Capacity_under.replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+"</p>"
                            else:
                                error_message += "<h3>Evaporator Capacity</h3><p>".replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+self.AC_errors.Evaporator_Capacity_under_pinched.replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+"</p>"
                                
                        AS.update(CP.PQ_INPUTS,psat_evap,1.0)
                        T1 = AS.T()
                        AS.update(CP.PQ_INPUTS,psat_evap+DP_evap,1.0)
                        T2 = AS.T()
                        if (T1 - T2) > DT_sat_max_evap:
                            error_message += "<h3>Evaporator Pressure Drop</h3><p>".replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+self.AC_errors.Evaporator_Pressure_Drop+"</p>"
                        
                        # condenser checks
                        if (abs(Q_cond) - Target_capacity - comp.power_mech) / (Target_capacity + comp.power_mech) > Capacity_tolerance:
                            error_message += "<h3>Condenser Capacity</h3><p>".replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+self.AC_errors.Condenser_Capacity_over.replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+"</p>"
                        elif (abs(Q_cond) - Target_capacity - comp.power_mech) / (Target_capacity + comp.power_mech) < (-1 * Capacity_tolerance):
                            if DT_Pinch_cond > 2.5:                        
                                error_message += "<h3>Condenser Capacity</h3><p>".replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+self.AC_errors.Condenser_Capacity_under.replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+"</p>"
                            else:
                                error_message += "<h3>Condenser Capacity</h3><p>".replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+self.AC_errors.Condenser_Capacity_under_pinched.replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+"</p>"
                        
                        AS.update(CP.PQ_INPUTS,psat_cond,1.0)
                        T1 = AS.T()
                        AS.update(CP.PQ_INPUTS,psat_cond+DP_cond,1.0)
                        T2 = AS.T()
                        if (T1 - T2) > DT_sat_max_cond:
                            error_message += "<h3>Condenser Pressure Drop</h3><p>".replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+self.AC_errors.Condenser_Pressure_Drop.replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+"</p>"
    
                    elif mode == "HP":
                        Q_compressor = comp.mdot_r * (comp.hout_r - hin_evap)
                        
                        # compressor checks
                        if (Q_compressor - Target_capacity) / (Target_capacity) > Capacity_tolerance:
                            error_message += "<h3>Compressor Capacity</h3><p>"+self.HP_errors.Compressor_Capacity_over.replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+"</p>"
                        elif (Q_compressor - Target_capacity) / (Target_capacity) < (-1 * Capacity_tolerance):
                            error_message += "<h3>Compressor Capacity</h3><p>"+self.HP_errors.Compressor_Capacity_under.replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+"</p>"
                        
                        # evaporator checks
                        if (abs(Q_evap) - Target_capacity + comp.power_mech) / (Target_capacity - comp.power_mech) > Capacity_tolerance:
                            error_message += "<h3>Evaporator Capacity</h3><p>".replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+self.HP_errors.Evaporator_Capacity_over.replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+"</p>"
                        elif (abs(Q_evap) - Target_capacity + comp.power_mech) / (Target_capacity - comp.power_mech) < (-1 * Capacity_tolerance):
                            if DT_Pinch_cond > 2.5:                        
                                error_message += "<h3>Evaporator Capacity</h3><p>".replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+self.HP_errors.Evaporator_Capacity_under.replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+"</p>"
                            else:
                                error_message += "<h3>Evaporator Capacity</h3><p>".replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+self.HP_errors.Evaporator_Capacity_under_pinched.replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+"</p>"

                        AS.update(CP.PQ_INPUTS,psat_evap,1.0)
                        T1 = AS.T()
                        AS.update(CP.PQ_INPUTS,psat_evap+DP_evap,1.0)
                        T2 = AS.T()
                        if (T1 - T2) > DT_sat_max_evap:
                            error_message += "<h3>Evaporator Pressure Drop</h3><p>".replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+self.HP_errors.Evaporator_Pressure_Drop.replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+"</p>"
                        
                        # condenser checks
                        if (abs(Q_cond) - Target_capacity) / (Target_capacity) > Capacity_tolerance:
                            error_message += "<h3>Condenser Capacity</h3><p>".replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+self.HP_errors.Condenser_Capacity_over.replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+"</p>"
                        elif (abs(Q_cond) - Target_capacity) / (Target_capacity) < (-1 * Capacity_tolerance):
                            if DT_Pinch_cond > 2.5:                        
                                error_message += "<h3>Condenser Capacity</h3><p>".replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+self.HP_errors.Condenser_Capacity_under.replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+"</p>"
                            else:
                                error_message += "<h3>Condenser Capacity</h3><p>".replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+self.HP_errors.Condenser_Capacity_under_piched.replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+"</p>"
                        
                        AS.update(CP.PQ_INPUTS,psat_cond,1.0)
                        T1 = AS.T()
                        AS.update(CP.PQ_INPUTS,psat_cond+DP_cond,1.0)
                        T2 = AS.T()
                        if (T1 - T2) > DT_sat_max_cond:
                            error_message += "<h3>Condenser Pressure Drop</h3><p>".replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+self.HP_errors.Condenser_Pressure_Drop.replace("Evaporator",evaporator_name).replace("Condenser",condenser_name)+"</p>"
                    
                    if error_message == "":
                        error_message = "<h3>design seems to be ok.</h3>"
                    self.finished.emit((1, error_message))
                except:
                    import traceback
                    print(traceback.format_exc())
                    self.finished.emit((0, "Could not perform design check! try another values for TTD (options => Design Check Properties)"))
            else:
                self.finished.emit((0, "Could not perform design check!"))
        except:
            import traceback
            print(traceback.format_exc())
            self.finished.emit((0, "failed to perform design check"))
            
    def import_reference_values(self):
        try:
            design_check_xml_path = appdirs.user_data_dir("EGSim")+"\Design_check.xml"
            tree = ET.parse(design_check_xml_path)
            root = tree.getroot()            
            TTD_evap_AC = float(root.find("TTD_evap_AC").text)
            TTD_cond_AC = float(root.find("TTD_cond_AC").text)
            TTD_evap_HP = float(root.find("TTD_evap_HP").text)
            TTD_cond_HP = float(root.find("TTD_cond_HP").text)
            DT_sat_max_evap = float(root.find("DT_sat_max_evap").text)
            DT_sat_max_cond = float(root.find("DT_sat_max_cond").text)
            Capacity_tolerance = float(root.find("Capacity_tolerance").text)
            return (1,(TTD_evap_AC,TTD_cond_AC,TTD_evap_HP,TTD_cond_HP,DT_sat_max_evap,DT_sat_max_cond,Capacity_tolerance))
        except:
            import traceback
            print(traceback.format_exc())
            return (0,)
        
    def solve_compressor(self,compressor, props):
        AS = props["AS"]
        if compressor.Comp_model == "physics":
            comp = CompressorPHYClass()
            comp.name = compressor.Comp_name
            comp.fp = compressor.Comp_fp
            comp.Vdot_ratio_P = compressor.Comp_ratio_P
            comp.Vdot_ratio_M = compressor.Comp_ratio_M
            comp.Displacement = compressor.Comp_vol
            comp.act_speed = compressor.Comp_speed
            comp.Elec_eff = compressor.Comp_elec_eff
            comp.isen_eff = compressor.isentropic_exp
            comp.vol_eff = compressor.vol_exp
            comp.F_factor = compressor.F_factor
            comp.SH_type = compressor.SH_type
            if comp.SH_type == 0:
                comp.SH_Ref = compressor.SH_Ref
            elif comp.SH_type == 1:
                comp.Suction_Ref = compressor.Suction_Ref
        
        elif compressor.Comp_model == "map":
            comp = CompressorAHRIClass()
            comp.name = compressor.Comp_name
            comp.M = compressor.map_data.M_coeffs
            comp.P = compressor.map_data.P_coeffs
            comp.Speeds = compressor.map_data.Speeds
            comp.fp = compressor.Comp_fp
            comp.Vdot_ratio_P = compressor.Comp_ratio_P
            comp.Vdot_ratio_M = compressor.Comp_ratio_M
            comp.Displacement = compressor.Comp_vol
            if compressor.map_data.std_type == 0:
                comp.SH_Ref = compressor.map_data.std_sh
            elif compressor.map_data.std_type == 1:
                comp.Suction_Ref = compressor.map_data.std_suction
                
            comp.act_speed = compressor.Comp_speed
            comp.Unit_system = compressor.unit_system
            comp.Elec_eff = compressor.Comp_elec_eff
            comp.F_factor = compressor.map_data.F_value
    
        elif compressor.Comp_model == "10coefficients":
            comp = CompressorAHRIClass()
            comp.name = compressor.Comp_name
            comp.M = compressor.M
            comp.P = compressor.P
            comp.Speeds = compressor.speeds
            comp.fp = compressor.Comp_fp
            comp.Vdot_ratio_P = compressor.Comp_ratio_P
            comp.Vdot_ratio_M = compressor.Comp_ratio_M
            comp.Displacement = compressor.Comp_vol
            if compressor.std_type == 0:
                comp.SH_Ref = compressor.std_sh
            elif compressor.std_type == 1:
                comp.Suction_Ref = compressor.std_suction
            comp.act_speed = compressor.Comp_speed
            comp.Unit_system = compressor.unit_system
            comp.Elec_eff = compressor.Comp_elec_eff
            comp.F_factor = compressor.Comp_AHRI_F_value
        
        AS.update(CP.QT_INPUTS,1.0,props["Tsat_cond"])
        psat_cond=AS.p() #[Pa]
        AS.update(CP.QT_INPUTS,1.0,props["Tsat_evap"])
        psat_evap=AS.p() #[Pa]    
        AS.update(CP.PT_INPUTS,psat_evap,props["Tsat_evap"] + props["SH"])
        hin_comp = AS.hmass()
        params={
            'Pin_r': psat_evap,
            'Pout_r': psat_cond,
            'hin_r': hin_comp,
            'AS': AS,
        }
        
        comp.Update(**params)
        comp.Calculate()
        return comp
    
    def solve_HX(self,HX, props, pin_r, hin_r, mdot_r, HX_type,cond_or_evap):
        if cond_or_evap == "evaporator":
            Tin_a = props['Tin_a_evap']
            Win_a = props['Win_a_evap']
        elif cond_or_evap == 'condenser':
            Tin_a = props['Tin_a_cond']
            Win_a = props['Win_a_cond']
            
        if HX_type == "fintube":
            HX_fast = FinTubeHEXClass()
            if HX.Air_flow_direction in ["Sub Heat Exchanger First","Sub Heat Exchanger Last"]:
                number_of_circuits = HX.N_series_Circuits + 1
            elif HX.Air_flow_direction in ["Parallel","Series-Parallel","Series-Counter"]:
                number_of_circuits = HX.N_series_Circuits
            HX_fast.name = HX.name
            if HX.Accurate == "CoolProp":
                HX_fast.Accurate = True
            elif HX.Accurate == "Psychrolib":
                HX_fast.Accurate = False
            HX_fast.create_circuits(number_of_circuits)
            for i in range(number_of_circuits):
                N = HX.circuits[i].N_Circuits
                connection = [i,i+1,i,1.0,N]
                HX_fast.connect(*tuple(connection))
            HX_fast.Tin_a = Tin_a
            HX_fast.Pin_a = HX.Air_P
            HX_fast.Win_a = Win_a
            HX_fast.Fan_add_DP = 0.0
            if HX.Air_flow_direction == "Parallel":
                HX_fast.Air_sequence = 'parallel'
                HX_fast.Air_distribution = HX.Air_Distribution
            elif HX.Air_flow_direction == "Series-Parallel":
                HX_fast.Air_sequence = 'series_parallel'
            elif HX.Air_flow_direction == "Series-Counter":
                HX_fast.Air_sequence = 'series_counter'
            elif HX.Air_flow_direction == "Sub Heat Exchanger First":
                HX_fast.Air_sequence = 'sub_HX_first'
                HX_fast.Air_distribution = HX.Air_Distribution
            elif HX.Air_flow_direction == "Sub Heat Exchanger Last":
                HX_fast.Air_sequence = 'sub_HX_last'
                HX_fast.Air_distribution = HX.Air_Distribution
            HX_fast.model = 'phase'
            N_segments = 1.0
            HX_fast.Q_error_tol = HX.HX_Q_tol
            HX_fast.max_iter_per_circuit = HX.N_iterations
            if HX.Fan_model == "Fan Efficiency Model":
                HX_fast.Fan.model = 'efficiency'
                HX_fast.Fan.efficiency = HX.Fan_model_efficiency_exp
            elif HX.Fan_model == "Fan Curve Model":
                HX_fast.Fan.model = 'curve'
                HX_fast.Fan.power_curve = HX.Fan_model_P_exp
                HX_fast.Fan.DP_curve = HX.Fan_model_DP_exp
            elif HX.Fan_model == "Fan Power Model":
                HX_fast.Fan.model = 'power'
                HX_fast.Fan.power_exp = HX.Fan_model_power_exp
                
            HX_fast.Fan.Fan_position = 'after'
            if hasattr(HX,"Vdot_ha"):
                HX_fast.Vdot_ha = HX.Vdot_ha
            else:
                v_spec = HAPropsSI("V","T",HX_fast.Tin_a,"W",HX_fast.Win_a,"P",HX_fast.Pin_a)
                HX_fast.Vdot_ha = HX.mdot_da * v_spec
            
            HX_fast.Solver = 'mdot'
            
            for i in range(number_of_circuits):
                HX_fast.Circuits[i].Geometry.Ntubes_per_bank_per_subcircuit = HX.circuits[i].N_tube_per_bank
                HX_fast.Circuits[i].Geometry.Nbank = HX.circuits[i].N_bank
                HX_fast.Circuits[i].Geometry.OD = HX.circuits[i].OD
                HX_fast.Circuits[i].Geometry.Ltube = HX.circuits[i].Ltube
                if HX.circuits[i].Tube_type == "Smooth":
                    HX_fast.Circuits[i].Geometry.Tubes_type = "Smooth"
                    HX_fast.Circuits[i].Geometry.ID = HX.circuits[i].ID
                    HX_fast.Circuits[i].Geometry.e_D = HX.circuits[i].e_D
                elif HX.circuits[i].Tube_type == "Microfin":
                    HX_fast.Circuits[i].Geometry.Tubes_type = "Microfin"
                    HX_fast.Circuits[i].Geometry.t = HX.circuits[i].Tube_t
                    HX_fast.Circuits[i].Geometry.beta = HX.circuits[i].Tube_beta
                    HX_fast.Circuits[i].Geometry.e = HX.circuits[i].Tube_e
                    HX_fast.Circuits[i].Geometry.d = HX.circuits[i].Tube_d
                    HX_fast.Circuits[i].Geometry.gama = HX.circuits[i].Tube_gamma
                    HX_fast.Circuits[i].Geometry.n = HX.circuits[i].Tube_n
                HX_fast.Circuits[i].Geometry.Staggering = HX.circuits[i].Staggering
                HX_fast.Circuits[i].Geometry.Pl = HX.circuits[i].Pl
                HX_fast.Circuits[i].Geometry.Pt = HX.circuits[i].Pt
                HX_fast.Circuits[i].Geometry.Connections = HX.circuits[i].Connections
                HX_fast.Circuits[i].Geometry.FarBendRadius = 0.01
                HX_fast.Circuits[i].Geometry.FPI = HX.circuits[i].Fin_FPI
                HX_fast.Circuits[i].Geometry.Fin_t = HX.circuits[i].Fin_t
                HX_fast.Circuits[i].Geometry.FinType = HX.circuits[i].Fin_type
                if HX.circuits[i].Fin_type == "Wavy":
                    HX_fast.Circuits[i].Geometry.Fin_Pd = HX.circuits[i].Fin_pd
                    HX_fast.Circuits[i].Geometry.Fin_xf = HX.circuits[i].Fin_xf
                elif HX.circuits[i].Fin_type == "WavyLouvered":
                    HX_fast.Circuits[i].Geometry.Fin_Pd = HX.circuits[i].Fin_pd
                    HX_fast.Circuits[i].Geometry.Fin_xf = HX.circuits[i].Fin_xf
                elif HX.circuits[i].Fin_type == "Louvered":
                    HX_fast.Circuits[i].Geometry.Fin_Lp = HX.circuits[i].Fin_Lp
                    HX_fast.Circuits[i].Geometry.Fin_Lh = HX.circuits[i].Fin_Lh
                elif HX.circuits[i].Fin_type == "Slit":
                    HX_fast.Circuits[i].Geometry.Fin_Sh = HX.circuits[i].Fin_Sh
                    HX_fast.Circuits[i].Geometry.Fin_Ss = HX.circuits[i].Fin_Ss
                    HX_fast.Circuits[i].Geometry.Fin_Sn = HX.circuits[i].Fin_Sn
                    
                HX_fast.Circuits[i].Thermal.Nsegments = N_segments
                HX_fast.Circuits[i].Thermal.kw = HX.circuits[i].Tube_k
                HX_fast.Circuits[i].Thermal.k_fin = HX.circuits[i].Fin_k
                HX_fast.Circuits[i].Thermal.FinsOnce = True
                HX_fast.Circuits[i].Thermal.HTC_superheat_Corr = HX.circuits[i].superheat_HTC_corr
                HX_fast.Circuits[i].Thermal.HTC_subcool_Corr = HX.circuits[i].subcool_HTC_corr
                HX_fast.Circuits[i].Thermal.DP_superheat_Corr = HX.circuits[i].superheat_DP_corr
                HX_fast.Circuits[i].Thermal.DP_subcool_Corr = HX.circuits[i].subcool_DP_corr
                HX_fast.Circuits[i].Thermal.HTC_2phase_Corr = HX.circuits[i]._2phase_HTC_corr
                HX_fast.Circuits[i].Thermal.DP_2phase_Corr = HX.circuits[i]._2phase_DP_corr
                HX_fast.Circuits[i].Thermal.DP_Accel_Corr = HX.circuits[i]._2phase_charge_corr + 1
                HX_fast.Circuits[i].Thermal.rho_2phase_Corr = HX.circuits[i]._2phase_charge_corr + 1
                HX_fast.Circuits[i].Thermal.Air_dry_Corr = HX.circuits[i].air_dry_HTC_corr
                HX_fast.Circuits[i].Thermal.Air_wet_Corr = HX.circuits[i].air_wet_HTC_corr
                HX_fast.Circuits[i].Thermal.h_r_superheat_tuning = HX.circuits[i].superheat_HTC_correction
                HX_fast.Circuits[i].Thermal.h_r_subcooling_tuning = HX.circuits[i].subcool_HTC_correction
                HX_fast.Circuits[i].Thermal.h_r_2phase_tuning = HX.circuits[i]._2phase_HTC_correction
                HX_fast.Circuits[i].Thermal.h_a_dry_tuning = HX.circuits[i].air_dry_HTC_correction
                HX_fast.Circuits[i].Thermal.h_a_wet_tuning = HX.circuits[i].air_wet_HTC_correction
                HX_fast.Circuits[i].Thermal.DP_a_dry_tuning = HX.circuits[i].air_dry_DP_correction
                HX_fast.Circuits[i].Thermal.DP_a_wet_tuning = HX.circuits[i].air_wet_DP_correction
                HX_fast.Circuits[i].Thermal.DP_r_superheat_tuning = HX.circuits[i].superheat_DP_correction
                HX_fast.Circuits[i].Thermal.DP_r_subcooling_tuning = HX.circuits[i].subcool_DP_correction
                HX_fast.Circuits[i].Thermal.DP_r_2phase_tuning = HX.circuits[i]._2phase_DP_correction
                
                if hasattr(HX.circuits[i],'h_a_wet_on'):
                    HX_fast.Circuits[i].Thermal.h_a_wet_on = HX.circuits[i].h_a_wet_on
                else:
                    HX_fast.Circuits[i].Thermal.h_a_wet_on = False
                if hasattr(HX.circuits[i],'DP_a_wet_on'):
                    HX_fast.Circuits[i].Thermal.DP_a_wet_on = HX.circuits[i].DP_a_wet_on
                else:
                    HX_fast.Circuits[i].Thermal.DP_a_wet_on = False

                if hasattr(HX.circuits[i],'sub_HX_values'):
                    HX_fast.Circuits[i].Geometry.Sub_HX_matrix = HX.circuits[i].sub_HX_values
                    
            params={
                    'Pin_r': pin_r,
                    'hin_r': hin_r,                        
                    'mdot_r': mdot_r,
                    'AS':props["AS"],
                }
            HX_fast.Update(**params)
            HX_fast.solve()
            
            return HX_fast.Results.DP_r, HX_fast.Results.Q, HX_fast.Results.delta_T_pinch, HX_fast.Results.TTD
        
        elif HX_type == "microchannel":
            HX_fast = MicroChannelHEXClass()
            HX_fast.name = HX.name
            if HX.Accurate == "CoolProp":
                HX_fast.Accurate = True
            elif HX.Accurate == "Psychrolib":
                HX_fast.Accurate = False
            HX_fast.Tin_a = HX.Air_T
            HX_fast.Pin_a = HX.Air_P
            Win_a = HAPropsSI("W","T",HX.Air_T,"P",HX.Air_P,"R",HX.Air_RH)
            HX_fast.Win_a = Win_a
            HX_fast.Fan_add_DP = 0.0
            HX_fast.model = 'phase'
            HX_fast.Thermal.Nsegments = 1
            HX_fast.Q_error_tol = HX.HX_Q_tol
            HX_fast.max_iter_per_circuit = HX.N_iterations
            if HX.Fan_model == "Fan Efficiency Model":
                HX_fast.Fan.model = 'efficiency'
                HX_fast.Fan.efficiency = HX.Fan_model_efficiency_exp
            elif HX.Fan_model == "Fan Curve Model":
                HX_fast.Fan.model = 'curve'
                HX_fast.Fan.power_curve = HX.Fan_model_P_exp
                HX_fast.Fan.DP_curve = HX.Fan_model_DP_exp
            elif HX.Fan_model == "Fan Power Model":
                HX_fast.Fan.model = 'power'
                HX_fast.Fan.power_exp = HX.Fan_model_power_exp
    
            HX_fast.Fan.Fan_position = 'after'
    
            HX_fast.Geometry.N_tube_per_bank_per_pass = HX.Circuiting.bank_passes
            if HX.Geometry.Fin_on_side_index:
                HX_fast.Geometry.Fin_rows = HX.N_tube_per_bank + 1
            else:
                HX_fast.Geometry.Fin_rows = HX.N_tube_per_bank - 1
    
            HX_fast.Geometry.T_L = HX.Geometry.T_l
            HX_fast.Geometry.T_w = HX.Geometry.T_w
            HX_fast.Geometry.T_h = HX.Geometry.T_h
            HX_fast.Geometry.T_s = HX.Geometry.T_s
            HX_fast.Geometry.P_shape = HX.Geometry.port_shape
            HX_fast.Geometry.P_end = HX.Geometry.T_end
            HX_fast.Geometry.P_a = HX.Geometry.port_a_dim
            if HX.Geometry.port_shape in ['Rectangle', 'Triangle']:
                HX_fast.Geometry.P_b = HX.Geometry.port_b_dim
            HX_fast.Geometry.N_port = HX.Geometry.N_ports
            HX_fast.Geometry.Enhanced = False
            HX_fast.Geometry.FinType = HX.Geometry.Fin_type
            if HX.Geometry.Fin_type == "Louvered":
                HX_fast.Geometry.Fin_Llouv = HX.Geometry.Fin_llouv
                HX_fast.Geometry.Fin_alpha = HX.Geometry.Fin_lalpha
                HX_fast.Geometry.Fin_Lp = HX.Geometry.Fin_lp
                
            HX_fast.Geometry.Fin_t = HX.Geometry.Fin_t
            HX_fast.Geometry.Fin_L = HX.Geometry.Fin_l
            HX_fast.Geometry.FPI = HX.Geometry.Fin_FPI
            HX_fast.Geometry.e_D = HX.Geometry.e_D
            HX_fast.Geometry.Header_CS_Type = HX.Geometry.header_shape
            HX_fast.Geometry.Header_dim_a = HX.Geometry.header_a_dim
            if HX.Geometry.header_shape in ["Rectangle"]:
                HX_fast.Geometry.Header_dim_b = HX.Geometry.header_b_dim
            HX_fast.Geometry.Header_length = HX.Geometry.header_height
    
            if hasattr(HX,"Vdot_ha"):
                HX_fast.Vdot_ha = HX.Vdot_ha
            else:
                v_spec = HAPropsSI("V","T",HX_fast.Tin_a,"W",HX_fast.Win_a,"P",HX_fast.Pin_a)
                HX_fast.Vdot_ha = HX.mdot_da * v_spec
            HX_fast.Thermal.k_fin = HX.Geometry.Fin_k
            HX_fast.Thermal.kw = HX.Geometry.Tube_k
            HX_fast.Thermal.Headers_DP_r = HX.Geometry.Header_DP
            HX_fast.Thermal.FinsOnce = True
            HX_fast.Thermal.HTC_superheat_Corr = HX.superheat_HTC_corr
            HX_fast.Thermal.HTC_subcool_Corr = HX.subcool_HTC_corr
            HX_fast.Thermal.DP_superheat_Corr = HX.superheat_DP_corr
            HX_fast.Thermal.DP_subcool_Corr = HX.subcool_DP_corr
            HX_fast.Thermal.HTC_2phase_Corr = HX._2phase_HTC_corr
            HX_fast.Thermal.DP_2phase_Corr = HX._2phase_DP_corr
            HX_fast.Thermal.DP_Accel_Corr = HX._2phase_charge_corr + 1
            HX_fast.Thermal.rho_2phase_Corr = HX._2phase_charge_corr + 1
            HX_fast.Thermal.Air_dry_Corr = HX.air_dry_HTC_corr
            HX_fast.Thermal.Air_wet_Corr = HX.air_wet_HTC_corr
            HX_fast.Thermal.h_r_superheat_tuning = HX.superheat_HTC_correction
            HX_fast.Thermal.h_r_subcooling_tuning = HX.subcool_HTC_correction
            HX_fast.Thermal.h_r_2phase_tuning = HX._2phase_HTC_correction
            HX_fast.Thermal.h_a_dry_tuning = HX.air_dry_HTC_correction
            HX_fast.Thermal.h_a_wet_tuning = HX.air_wet_HTC_correction
            HX_fast.Thermal.DP_a_dry_tuning = HX.air_dry_DP_correction
            HX_fast.Thermal.DP_a_wet_tuning = HX.air_wet_DP_correction
            HX_fast.Thermal.DP_r_superheat_tuning = HX.superheat_DP_correction
            HX_fast.Thermal.DP_r_subcooling_tuning = HX.subcool_DP_correction
            HX_fast.Thermal.DP_r_2phase_tuning = HX._2phase_DP_correction

            if hasattr(HX,'h_a_wet_on'):
                HX_fast.Thermal.h_a_wet_on = HX.h_a_wet_on
            else:
                HX_fast.Thermal.h_a_wet_on = False
            if hasattr(HX,'DP_a_wet_on'):
                HX_fast.Thermal.DP_a_wet_on = HX.DP_a_wet_on
            else:
                HX_fast.Thermal.DP_a_wet_on = False
            
            
            params={
                    'Pin_r': pin_r,
                    'hin_r': hin_r,                        
                    'mdot_r': mdot_r,
                    'AS':props["AS"],
                }
            HX_fast.Update(**params)
            HX_fast.solve()
            
            return HX_fast.Results.DP_r, HX_fast.Results.Q, HX_fast.Results.delta_T_pinch, HX_fast.Results.TTD
                
    def validate(self,parent):
        if hasattr(parent,"parametric_cycle_data") and parent.Parametric_cycle.checkState():
            return 1
        if hasattr(parent,"parametric_capillary_data") and parent.Parametric_capillary.checkState():
            return 1
        if hasattr(parent,"parametric_compressor_data") and parent.Parametric_compressor.checkState():
            return 1
        if hasattr(parent,"parametric_liquid_data") and parent.Parametric_liquid.checkState():
            return 1
        if hasattr(parent,"parametric_2phase_data") and parent.Parametric_2phase.checkState():
            return 1
        if hasattr(parent,"parametric_suction_data") and parent.Parametric_suction.checkState():
            return 1
        if hasattr(parent,"parametric_discharge_data") and parent.Parametric_discharge.checkState():
            return 1
        if hasattr(parent,"parametric_evaporator_data") and parent.Parametric_evaporator.checkState():
            return 1
        if hasattr(parent,"parametric_condenser_data") and parent.Parametric_condenser.checkState():
            return 1
        if parent.First_condition.currentIndex() == 1:
            return 2
        if parent.Expansion_device.currentIndex() == 1:
            return 2
        
        if str(parent.Subcooling.text()).strip() in ["","-","."]:
            return 3
    
        if str(parent.Superheat.text()).strip() in ["","-","."]:
            return 3
    
        if str(parent.Capacity_target.text()).strip() in ["","-","."]:
            return 3
        
        if not hasattr(parent,"selected_condenser_index"):
            return 4
        if not hasattr(parent,"selected_evaporator_index"):
            return 4
        if not hasattr(parent,"selected_compressor_index"):
            return 4
        
        if parent.Ref_library.currentIndex() == 0:
            try:
                AS = CP.AbstractState("REFPROP","R22")
            except:
                return 5
        
        if not self.import_error_messages():
            return 6
        
        return 0
    
    def import_error_messages(self):
        try:
            self.AC_errors = values()
            self.HP_errors = values()
            design_check_errors_xml_path = appdirs.user_data_dir("EGSim")+"\Design_check_errors.xml"
            tree = ET.parse(design_check_errors_xml_path)
            root = tree.getroot()
            AC_errors = root.find("AC")
            self.AC_errors.Evaporator_Capacity_over = AC_errors.find("Evaporator_Capacity_over").text
            self.AC_errors.Evaporator_Capacity_under = AC_errors.find("Evaporator_Capacity_under").text
            self.AC_errors.Evaporator_Capacity_under_pinched = AC_errors.find("Evaporator_Capacity_under_pinched").text
            self.AC_errors.Evaporator_Pressure_Drop = AC_errors.find("Evaporator_Pressure_Drop").text
            self.AC_errors.Condenser_Capacity_over = AC_errors.find("Condenser_Capacity_over").text
            self.AC_errors.Condenser_Capacity_under = AC_errors.find("Condenser_Capacity_under").text
            self.AC_errors.Condenser_Capacity_under_pinched = AC_errors.find("Condenser_Capacity_under_pinched").text
            self.AC_errors.Condenser_Pressure_Drop = AC_errors.find("Condenser_Pressure_Drop").text
            self.AC_errors.Compressor_Capacity_over_AC = AC_errors.find("Compressor_Capacity_over").text
            self.AC_errors.Compressor_Capacity_under_AC = AC_errors.find("Compressor_Capacity_under").text

            HP_errors = root.find("HP")
            self.HP_errors.Evaporator_Capacity_over = HP_errors.find("Evaporator_Capacity_over").text
            self.HP_errors.Evaporator_Capacity_under = HP_errors.find("Evaporator_Capacity_under").text
            self.HP_errors.Evaporator_Capacity_under_pinched = HP_errors.find("Evaporator_Capacity_under_pinched").text
            self.HP_errors.Evaporator_Pressure_Drop = HP_errors.find("Evaporator_Pressure_Drop").text
            self.HP_errors.Condenser_Capacity_over = HP_errors.find("Condenser_Capacity_over").text
            self.HP_errors.Condenser_Capacity_under = HP_errors.find("Condenser_Capacity_under").text
            self.HP_errors.Condenser_Capacity_under_pinched = HP_errors.find("Condenser_Capacity_under_pinched").text
            self.HP_errors.Condenser_Pressure_Drop = HP_errors.find("Condenser_Pressure_Drop").text
            self.HP_errors.Compressor_Capacity_over_AC = HP_errors.find("Compressor_Capacity_over").text
            self.HP_errors.Compressor_Capacity_under_AC = HP_errors.find("Compressor_Capacity_under").text
            
            return 1
        except:
            import traceback
            print(traceback.format_exc())
            return 0
