# -*- coding: utf-8 -*-
"""
Created on Sun Jan 10 18:45:31 2021

@author: OmarZaki
"""
from math import pi

def temperature_diff_unit_converter(value,index,reverse=False):
    value = float(value)
    if not reverse:
        if index == 0: # C
            return value
        elif index == 1: # F
            return value * 5 / 9
    else:
        if index == 0: # C
            return value
        elif index == 1: # F
            return value / 5 * 9
        
def mass_unit_converter(value,index,reverse=False):
    value = float(value)
    if not reverse:
        if index == 0: # kg
            return value
        elif index == 1: # lb
            return value / 2.205
    else:
        if index == 0: # kg
            return value
        elif index == 1: # lb
            return value * 2.205

def power_unit_converter(value,index,reverse=False):
    value = float(value)
    if not reverse:
        if index == 0: # W
            return value
        elif index == 1: # Btu/hr
            return value * 0.29307107
    else:
        if index == 0: # W
            return value
        elif index == 1: # Btu/hr
            return value / 0.29307107
        
def pressure_unit_converter(value,index,reverse=False):
    value = float(value)
    if not reverse:
        if index == 0: #Pa
            return value
        elif index == 1: #kPa
            return value * (1e3)
        elif index == 2: #MPa
            return value * (1e6)
        elif index == 3: #bar
            return value * (1e5)
        elif index == 4: #atm
            return value * (101325)       
        elif index == 5: #psi
            return value * (6894.76)
    else:
        if index == 0: #Pa
            return value
        elif index == 1: #kPa
            return value / (1e3)
        elif index == 2: #MPa
            return value / (1e6)
        elif index == 3: #bar
            return value / (1e5)
        elif index == 4: #atm
            return value / (101325)       
        elif index == 5: #psi
            return value / (6894.76)

def mass_flowrate_unit_converter(value,index,reverse=False):
    value = float(value)
    if not reverse:
        if index == 0: # kg/s
            return value
        elif index == 1: # kg/min
            return value / 60
        elif index == 2: # kg/hr
            return value / 3600
        elif index == 3: # lb/s
            return value / (2.205)
        elif index == 4: # lb/min
            return value / (2.205 * 60)
        elif index == 5: # lb/hr
            return value / (2.205 * 3600)
    else:
        if index == 0: # kg/s
            return value
        elif index == 1: # kg/min
            return value * 60
        elif index == 2: # kg/hr
            return value * 3600
        elif index == 3: # lb/s
            return value * (2.205)
        elif index == 4: # lb/min
            return value * (2.205 * 60)
        elif index == 5: # lb/hr
            return value * (2.205 * 3600)

def volume_flowrate_unit_converter(value,index,reverse=False):
    value = float(value)
    if not reverse:
        if index == 0: # m3/s
            return value
        elif index == 1: # m3/min
            return value / 60
        elif index == 2: # m3/hr
            return value / (60 * 60)
        elif index == 3: # lit/min
            return value / (1000 * 60)
        elif index == 4: # ft3/s
            return value / (3.281**3)
        elif index == 5: # ft3/min
            return value / (3.281**3 * 60)
        elif index == 6: # ft3/hr
            return value / (3.281**3 * 3600)       
    else:
        if index == 0: # m3/s
            return value
        elif index == 1: # m3/min
            return value * 60
        elif index == 2: # m3/hr
            return value * (60 * 60)
        elif index == 3: # lit/min
            return value * (1000 * 60)
        elif index == 4: # ft3/s
            return value * (3.281**3)
        elif index == 5: # ft3/min
            return value * (3.281**3 * 60)
        elif index == 6: # ft3/hr
            return value * (3.281**3 * 3600)       

def temperature_unit_converter(value,index,reverse=False):
    value = float(value)
    if not reverse:
        if index == 0: # C
            return value + 273.15
        elif index == 1: # K
            return value
        elif index == 2: # F
            return (value - 32) * 5 / 9 + 273.15
    else:
        if index == 0: # C
            return value - 273.15
        elif index == 1: # K
            return value
        elif index == 2: # F
            return (value - 273.15) * 9 / 5 + 32

def length_unit_converter(value,index,reverse=False):
    value = float(value)
    if not reverse:
        if index == 0:
            return value
        elif index == 1: # cm
            return value / 100
        elif index == 2: # mm
            return value / 1000
        elif index == 3: # ft
            return value / 3.281
        elif index == 4: # in
            return value * 0.0254        
    else:
        if index == 0:
            return value
        elif index == 1: # cm
            return value * 100
        elif index == 2: # mm
            return value * 1000
        elif index == 3: # ft
            return value * 3.281
        elif index == 4: # in
            return value / 0.0254        

def volume_unit_converter(value,index,reverse=False):
    value = float(value)
    if not reverse:
        if index == 0: # m3
            return value
        elif index == 1: # cm3
            return value * 1e-6
        elif index == 2: # ft3
            return value / (3.281)**3
        elif index == 3: # in3
            return value * (0.0254)**3
    else:
        if index == 0: # m3
            return value
        elif index == 1: # cm3
            return value / 1e-6
        elif index == 2: # ft3
            return value * (3.281)**3
        elif index == 3: # in3
            return value / (0.0254)**3

def area_unit_converter(value,index,reverse=False):
    value = float(value)
    if not reverse:
        if index == 0: # m2
            return value
        elif index == 1: # cm2
            return value * 1e-4
        elif index == 2: # mm2
            return value * 1e-6
        elif index == 3: # ft2
            return value / (3.281)**2
        elif index == 4: # in2
            return value * (0.0254)**2
    else:
        if index == 0: # m2
            return value
        elif index == 1: # cm2
            return value / 1e-4
        elif index == 2: # mm2
            return value / 1e-6
        elif index == 3: # ft2
            return value * (3.281)**2
        elif index == 4: # in2
            return value / (0.0254)**2

def angle_unit_converter(value,index,reverse=False):
    value = float(value)
    if not reverse:
        if index == 0: #degrees
            return value
        elif index == 1: # radian
            return value / pi * 180
        elif index == 2: # minutes
            return value / 60
        elif index == 3: # seconds
            return value / 3600
    else:
        if index == 0: #degrees
            return value
        elif index == 1: # radian
            return value * pi / 180
        elif index == 2: # minutes
            return value * 60
        elif index == 3: # seconds
            return value * 3600

def Thermal_K_unit_converter(value,index,reverse=False):
    value = float(value)
    if not reverse:
        if index == 0: # W/m.K
            return value
        elif index == 1: # Btu/hr.ft.F
            return value * 1.729577206
    else:
        if index == 0: # W/m.K
            return value
        elif index == 1: # Btu/hr.ft.F
            return value / 1.729577206

def HTC_unit_converter(value,index,reverse=False):
    value = float(value)
    if not reverse:
        if index == 0: # W/m2.K
            return value
        elif index == 1: # Btu/hr.ft2.K
            return value * 5.678263341
    else:
        if index == 0: # W/m2.K
            return value
        elif index == 1: # Btu/hr.ft2.K
            return value / 5.678263341

def time_converter(value,index,reverse=False):
    value = float(value)
    if not reverse:
        if index == 0: # Second
            return value
        elif index == 1: # Minute
            return value * 60.0
        elif index == 2: # Hour
            return value * 3600.0
    else:
        if index == 0: # Second
            return value
        elif index == 1: # Minute
            return value / 60.0
        elif index == 2: # Minute
            return value / 3600.0

def COP_converter(value,index,reverse=False):
    value = float(value)
    if not reverse:
        if index == 0: # W/W
            return value
        elif index == 1: # Btu/hr/W
            return value / (12000/3517)
    else:
        if index == 0: # Second
            return value
        elif index == 1: # Minute
            return value * (12000/3517)

def entropy_converter(value,index,reverse=False):
    value = float(value)
    if not reverse:
        if index == 0: # J/kg.K
            return value
        elif index == 1: # Btu/hr.F
            return value * 4186.8
    else:
        if index == 0: # J/kg.K
            return value
        elif index == 1: # Btu/hr.F
            return value / 4186.8

def enthalpy_converter(value,index,reverse=False):
    value = float(value)
    if not reverse:
        if index == 0: # J/kg
            return value
        elif index == 1: # Btu/lb
            return value * 2324.44
    else:
        if index == 0: # J/kg
            return value
        elif index == 1: # Btu/lb
            return value / 2324.44

def entropy_gen_converter(value,index,reverse=False):
    value = float(value)
    if not reverse:
        if index == 0: # W/K
            return value
        elif index == 1: # Btu/hr.F
            return value * (3517/12000) * (9/5)
    else:
        if index == 0: # W/K
            return value
        elif index == 1: # Btu/hr.F
            return value / (3517/12000) / (9/5)

def velocity_converter(value,index,reverse=False):
    value = float(value)
    if not reverse:
        if index == 0: # m/s
            return value
        elif index == 1: # m/min
            return value / 60
        elif index == 2: # m/hr
            return value / 3600
        elif index == 3: # ft/s
            return value / 3.281
        elif index == 4: # ft/min
            return value / 3.281 / 60
        elif index == 5: # ft/hr
            return value / 3.281 / 3600
    else:
        if index == 0: # m/s
            return value
        elif index == 1: # m/min
            return value * 60
        elif index == 2: # m/hr
            return value * 3600
        elif index == 3: # ft/s
            return value * 3.281
        elif index == 4: # ft/min
            return value * 3.281 / 60
        elif index == 5: # ft/hr
            return value * 3.281 / 3600