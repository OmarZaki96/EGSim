from sklearn.linear_model import LinearRegression
import numpy as np
from unit_conversion import *

def Create_coefficients(M_array,P_array,Tc_unit,Te_unit,M_unit):
    M_coeffs = []
    for M in M_array:
        rows = []
        for row in M:
            Tc_value = temperature_unit_converter(float(row[0]), Tc_unit) - 273.15
            Te_value = temperature_unit_converter(float(row[1]), Te_unit) - 273.15
            M_value = mass_flowrate_unit_converter(float(row[2]),M_unit)
            values = [Te_value, Tc_value, Te_value**2, Tc_value*Te_value, Tc_value**2, Te_value**3, Tc_value*Te_value**2, Te_value*Tc_value**2, Tc_value**3, M_value]
            rows.append(values)
        rows = np.array(rows)
        model = LinearRegression()
        model.fit(rows[:,:-1],rows[:,-1])
        Mcoeff = tuple([model.intercept_] + list(model.coef_))
        M_coeffs.append(Mcoeff)

    P_coeffs = []
    for P in P_array:
        rows = []
        for row in P:
            Tc_value = temperature_unit_converter(float(row[0]), Tc_unit) - 273.15
            Te_value = temperature_unit_converter(float(row[1]), Te_unit) - 273.15
            P_value = float(row[2])
            values = [Te_value, Tc_value, Te_value**2, Tc_value*Te_value, Tc_value**2, Te_value**3, Tc_value*Te_value**2, Te_value*Tc_value**2, Tc_value**3, P_value]
            rows.append(values)
        rows = np.array(rows)
        model = LinearRegression()
        model.fit(rows[:,:-1],rows[:,-1])
        Pcoeff = tuple([model.intercept_] + list(model.coef_))
        P_coeffs.append(Pcoeff)
    
    return (M_coeffs,P_coeffs)

if __name__ == '__main__':
    import pandas as pd
    M_values = pd.read_csv(r"C:\Users\Omar\Desktop\M_rows.csv").to_numpy()
    P_values = pd.read_csv(r"C:\Users\Omar\Desktop\P_rows.csv").to_numpy()
    print(Create_coefficients(M_values,P_values,0,0,0))
    