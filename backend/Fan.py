from __future__ import division, print_function, absolute_import
from sympy.parsing.sympy_parser import parse_expr
from sympy import Symbol
from lxml import etree as ET
import os

class FanClass():
    """
    Fan class, can be based on either efficiency model or fan curve model
    
    Required Parameters:
    
    ===========    ==========  ========================================================================
    Variable       Units       Description
    ===========    ==========  ========================================================================
    model          --          Can be either 'efficiency' or 'curve' showing the model used for the fan
    efficiency     --          Efficiency expression function of humid volume flow rate, used in case of 'efficiency' model
    DP_a           Pa          Pressure drop of the air, used in case of 'efficiency' model
    Vdot_a         m3/s        Air inlet humid volume flow rate
    power_curve    W           Power curve expression function of humid volume flow rate, used in case of 'curve' model
    DP_curve       Pa          Pressure drop curve expression function of humid volume flow rate, used in case of 'curve' model
    ===========   ==========  ========================================================================
    
    All variables are of double-type unless otherwise specified
        
    """
    def __init__(self,**kwargs):
        #Load up the parameters passed in
        # using the dictionary
        self.__dict__.update(kwargs)
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
            ('Fan Model','-',self.model.capitalize()),
            ('Pressure rise','Pa',self.DP_a+self.DP_fan_add),
            ('Fan efficiency','%',self.isen_eff * 100),
            ('Inlet air humid volume flow rate','m^3/s',self.Vdot_a),
            ('Fan power','W',self.power)
         ]
        
    def Calculate_efficiency(self):        
        # inlet humid volume flow rate
        Vdot = self.Vdot_a
        # getting efficiency expression
        try:
            efficiency=parse_expr(self.efficiency.replace("^","**"))
        except:
            raise AttributeError("error in parsing efficiency expression")
        
        # getting expression variables
        all_symbols_efficiency = [str(x) for x in efficiency.atoms(Symbol)]
        
        # making sure 1 variable (volume flow rate) is present
        if len(all_symbols_efficiency) != 1:
            if len(all_symbols_efficiency) == 0: # no variable is present, a number is passed
                eff_value = efficiency.evalf()
            else:
                raise AttributeError("error in parsing efficiency expression")
        else:
            # calculating and assigning pressure ratio to variable
            symbol_vals_efficiency = {all_symbols_efficiency[0]: Vdot}

            # evaluating expression
            eff_value = float(efficiency.subs(symbol_vals_efficiency))
        
        # making sure values are reasonable
        if not (0 < eff_value < 1):
            raise ValueError("Efficiency is value isn't between 0 and 1")
                
        # calculating power
        DP_a = self.DP_a + self.DP_fan_add
        power = float(DP_a * Vdot / eff_value)
        
        # results
        self.isen_eff = eff_value
        self.power = power

    def Calculate_power(self):        
        # inlet humid volume flow rate
        Vdot = self.Vdot_a
        
        # getting power expression
        try:
            power=parse_expr(self.power_exp.replace("^","**"))
        except:
            raise AttributeError("error in parsing power expression")
        
        # getting expression variables
        all_symbols_power = [str(x) for x in power.atoms(Symbol)]
        
        # making sure 1 variable (volume flow rate) is present
        if len(all_symbols_power) != 1:
            if len(all_symbols_power) == 0: # no variable is present, a number is passed
                power_value = float(power.evalf())
            else:
                raise AttributeError("error in parsing power expression")
        else:
            # calculating and assigning pressure ratio to variable
            symbol_vals_power = {all_symbols_power[0]: Vdot}

            # evaluating expression
            power_value = float(power.subs(symbol_vals_power))
                        
        # calculating power
        DP_a = self.DP_a + self.DP_fan_add
        efficiency = float(DP_a * Vdot / power_value)
        
        # results
        self.isen_eff = efficiency
        self.power = power_value
        
    def Calculate_curve(self):
        # inlet humid volume flow rate
        Vdot = self.Vdot_a
        
        # getting efficiency expression
        try:
            power_curve = parse_expr(self.power_curve.replace("^","**"))
            DP_curve = parse_expr(self.DP_curve.replace("^","**"))
        except:
            import traceback
            print(traceback.format_exc())
            raise AttributeError("error in parsing power or pressure drop expressions")
        
        # getting expression variables
        all_symbols_power_curve = [str(x) for x in power_curve.atoms(Symbol)]
        all_symbols_DP_curve = [str(x) for x in DP_curve.atoms(Symbol)]
        
        # making sure 1 variable (volume flow rate) is present
        if len(all_symbols_power_curve) != 1:
            if len(all_symbols_power_curve) == 0: # no variable is present, a number is passed
                power_value = float(power_curve.evalf())
            else:
                raise AttributeError("error in parsing power expression")
        else:
            # calculating and assigning pressure ratio to variable
            symbol_vals_power_curve = {all_symbols_power_curve[0]: Vdot}

            # evaluating expression
            power_value = float(power_curve.subs(symbol_vals_power_curve))
   
        # making sure 1 variable (volume flow rate) is present
        if len(all_symbols_DP_curve) != 1:
            if len(all_symbols_DP_curve) == 0: # no variable is present, a number is passed
                DP_value = DP_curve.evalf()
            else:
                raise AttributeError("error in parsing pressure drop expression")
        else:
            # calculating and assigning pressure ratio to variable
            symbol_vals_DP_curve = {all_symbols_DP_curve[0]: Vdot}

            # evaluating expression
            DP_value = float(DP_curve.subs(symbol_vals_DP_curve))
                        
        # calculating efficiency
        isen_eff = Vdot * (DP_value + self.DP_fan_add) / power_value
        
        if isen_eff > 1:
            raise ValueError("isentropic efficiency can't exceed 1")
        
        # saving results
        self.DP_a = DP_value
        self.power = power_value
        self.isen_eff = isen_eff
        
    def Calculate(self):
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, 'Settings.xml')
        try:
            tree = ET.parse(filename)
            root = tree.getroot()
            if root.tag == "Settings":
                root = root.find("Parameters")
                if root != None:
                    root = root.find("Fan_Throw_DP")
                    if root != None:
                        self.DP_fan_add = float(root.text)
                else:
                    raise
            else:
                raise
        except:
            self.DP_fan_add = 125
                
        if self.model == 'efficiency':
            self.Calculate_efficiency()
        elif self.model == 'curve':
            self.Calculate_curve()
        elif self.model == 'power':
            self.Calculate_power()
        else:
            raise AttributeError("Unknown fan model used")
        
if __name__=='__main__':
    import time
    def f1():
        global Fan
        for i in range(1):
            kwds={
                  'model': 'efficiency',
                  'efficiency': '0.5 * X + 0.3',
                  'Vdot_a': 0.8,
                  'DP_a': 25,
                  }
            Fan = FanClass(**kwds)
            Fan.Calculate()
    def f2():
        global Fan
        for i in range(1):
            kwds={
                  'model': 'curve',
                  'power_curve': '0.5 * X + 0.3',
                  'DP_curve': '0.5 * X + 0.3',
                  'Vdot_a': 0.8,
                  }
            Fan = FanClass(**kwds)
            Fan.Calculate()

    def f3():
        global Fan
        for i in range(1):
            kwds={
                  'model': 'power',
                  'power_exp': '150',
                  'Vdot_a': 0.8,
                  'DP_a': 25,
                  }
            Fan = FanClass(**kwds)
            Fan.Calculate()
    
    T1 = time.time()
    f3()
    print("total time:",time.time() - T1, "s")
    print ('Power:', Fan.power,'W')
    print ('Pressure drop:',Fan.DP_a,'Pa')
    print ('Efficiency:', Fan.isen_eff)
    print(*Fan.OutputList(),sep="\n")
    