# -*- coding: utf-8 -*-
"""
Created on Wed Apr 14 12:43:48 2021

@author: Omar
"""
import numpy as np
from itertools import product
from scipy.interpolate import lagrange
import random
from scipy.optimize import least_squares, root, newton

def main_solver(fn, x_init, method="newton", max_iter=30,bounds=None):
    if method.lower() == "lagrange": # this is not stable and not good at all
        x = lagrange_solver(fn,x_init,max_iter)
    elif method.lower()  == 'newton':
        x = newton(fn,x_init,maxiter=max_iter,full_output=True)
    elif method.lower() == 'broyden 1':
        x = root(fn,x_init,method='broyden1', options={'maxiter':max_iter})['x']
    elif method.lower() == 'broyden 2':
        x = root(fn,x_init,method='broyden2', options={'maxiter':max_iter})['x']
    elif method.lower() == 'hybrid':
        x = root(fn,x_init,method='hybr', options={'maxfev':max_iter})['x']
    elif method.lower() == 'least squares':
        x = least_squares(fn,x_init,max_nfev=max_iter,bounds=bounds)['x']
    elif method.lower() == 'exciting mixing':
        x = root(fn,x_init,method='excitingmixing', options={'maxiter':max_iter})['x']
    return x

def lagrange_solver(fn, x_init, max_iter, eps=1e-6):
    # if single value given, convert to list
    try:
        len(x_init)
    except:
        x_init = [x_init]
    
    # converting the initial guess to numpy array
    x_init = np.array(x_init)
    
    # calculating the number of variables
    num_vars = len(x_init)
    
    # first, we use the initial guess of each vairable to evaluate the function at
    # 0.8 and 1.0 of the inital guess (0.01 in case zero is given as inital guess)
    
    variables_values = []
    
    for var_init in x_init:
        if var_init == 0:
            var_2nd_init = 1
        else:
            var_2nd_init = var_init * 0.8
            
        variables_values.append(tuple([var_init, var_2nd_init]))
    
    set_of_values = list(product(*variables_values))
    
    
    # create guesses table and residuals table
    guess_table = np.zeros([0,num_vars+1],dtype=float)
    residuals_table = np.zeros([0,num_vars+1],dtype=float)
    
    for i,values in enumerate(set_of_values):
        if num_vars == 1:
            resids = fn(values[0])
            resids = [resids]
        else:
            resids = fn(values)
            
        guess_table = np.vstack([guess_table,[i]+list(values)])
        residuals_table = np.vstack([residuals_table,[i]+list(resids)])

    # trying to find solution using lagrange
    converged = False
    j = 0
    while not converged and j < max_iter:
        j += 1
        new_guess = []
        
        for i in range(num_vars):
            i += 1
            unique_guess_table = list(np.unique(guess_table[:,i]))
            unique_residuals_table = []
            for unqiue_guess in unique_guess_table:
                unique_residuals_table.append(residuals_table[guess_table == unqiue_guess][0])
            i -= 1
            unique_guess_table = np.array(unique_guess_table)
            unique_residuals_table = np.array(unique_residuals_table)
            least_residuals_indices = np.argsort(np.abs(unique_residuals_table))[:5]
            poly = lagrange(unique_residuals_table[least_residuals_indices], unique_guess_table[least_residuals_indices])
            new_guess_value = poly(0)
            if new_guess_value in unique_guess_table:
                new_guess_value = unique_guess_table[0] * random.random()
            new_guess.append(new_guess_value)
            
        if num_vars == 1:
            resids = fn(new_guess[0])
            resids = [resids]
        else:
            resids = fn(new_guess)
            
        guess_table = np.vstack([guess_table,[len(guess_table)]+list(new_guess)])
        residuals_table = np.vstack([residuals_table,[len(residuals_table)]+list(resids)])
        
        converged = True
        solution_indices = []
        for i in range(num_vars):
            if np.min(np.abs(residuals_table[:,i+1])) > eps:
                converged = False
            else:
                solution_indices.append(int(np.where(np.abs(residuals_table[:,i+1]) == np.amin(np.abs(residuals_table[:,i+1])))[0]))
            
    if converged:
        print(guess_table)
        print(residuals_table)
        return guess_table[solution_indices,[1,2]]
    else:
        print(guess_table)
        print(residuals_table)
        raise
    
if __name__ == '__main__':
    def objective(X):
        return 3 * X[0]**3 + X[0]**2 + 5, 23 * X[1]**6 - X[1]**2 - 3
    
    print(main_solver(objective,[2,19], method="Lagrange",max_iter=60))