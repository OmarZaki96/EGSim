from __future__ import division, print_function, absolute_import
from math import pi, log, sqrt, exp, cos, sin, tan, atan, acos
from scipy.integrate import quad, quadrature, simps
import numpy as np
import CoolProp as CP

machine_eps = np.finfo(float).eps

# TODO: add correlations choosing algorithm

class CorrelationsClass():
    def __init__(self):
        self.imposed_h_subcool = False
        self.imposed_h_superheat = False
        self.imposed_h_2phase = False
        self.imposed_dPdz_f_subcool = False
        self.imposed_dPdz_f_superheat = False
        self.imposed_dPdz_f_2phase = False
        self.imposed_dP_a = False
        self.imposed_rho_2phase = False

    def update(self,AS,geometry,thermal,phase,P,var_2nd_in,mdot_r,A_r,mode,q_flux=0,var_2nd_out=None):
        '''
        This function is used to choose the correct correlation number based
        on the inputs given to it.

        Parameters
        ----------
        AS : AbstractState
            AbstractState.
        geometry : class
            A class containing the necessary geometric features.
        thermal : class
            A class containing the necessary thermal features..
        phase : str
            it can be either '1phase' or '2phase'.
        P : float
            pressure.
        var_2nd_in : float
            it can be either inlet quality or enthalpy based on phase.
        mdot_r : float
            mass flow rate of refrigerant.
        A_r : float
            refrigerant side heat transfer area.
        mode : str
            can be either heater or cooler depending on the process on the air.
        q_flux : float, optional
            to assign the heat flux for evaporation or condensation. The default is 0.
        var_2nd_out : float, optional
            can be either quality or enthalpy for outlet condition. The default is None.

        Returns
        -------
        None.

        '''
        self.AS = AS
        self.P = float(P)
        self.q_flux = float(q_flux)
        self.mdot_r = float(mdot_r)
        self.A_segment = float(A_r)
        self.mode = mode
        self.L = A_r / geometry.inner_circum
        self.phase = phase
        self.G_r = float(self.mdot_r) / float(geometry.A_CS)
        if phase == '1phase':
            self.h = float(var_2nd_in)
            AS.update(CP.PQ_INPUTS,P,0.0)
            h_L = float(AS.hmass())
            AS.update(CP.PQ_INPUTS,P,1.0)
            h_V = float(AS.hmass())
            self.x = float((self.h-h_L)/(h_V-h_L))
            if self.x >= 1:
                self.phase_type = 'vapor'
            elif self.x <= 0:
                self.phase_type = 'liquid'                
            else: # due to round error, it is either very close to 1 or 0
                if round(self.x,2) == 1.0:
                    self.phase_type = 'vapor'
                elif round(self.x,2) == 0.0:
                    self.phase_type = 'liquid'
                else:
                    raise Exception("Can't decide phase for quality:"+str(self.x))
        else: #2phase
            self.x = float(var_2nd_in)
            if var_2nd_out != None:
                if var_2nd_out > 1.0:
                    self.x_out = 1.0
                elif var_2nd_out < 0.0:
                    self.x_out = 0.0
                else:
                    self.x_out =float(var_2nd_out)
            else:
                self.x_out = self.x
            AS.update(CP.PQ_INPUTS,P,self.x)
            self.h = float(AS.hmass())
        self.ref = AS.name()
        self.T_w = float(geometry.T_w)
        self.T_h = float(geometry.T_h)
        self.Dh = float(geometry.Dh)
        if hasattr(geometry,'P_b'):
            self.beta = min(geometry.P_a,geometry.P_b) / max(geometry.P_a,geometry.P_b)
        else:
            self.beta = 1.0
        self.e_D = float(geometry.e_D)
        
        AS.update(CP.HmassP_INPUTS,self.h,self.P)
        self.T = float(AS.T())
        # choosing correlation by setting number
        if self.phase == '1phase':
            if not self.imposed_dPdz_f_subcool:
                # options: 1
                self.dPdz_f_corr_subcool = 1
            if not self.imposed_dPdz_f_superheat:
                # options: 1
                self.dPdz_f_corr_superheat = 1
            if not self.imposed_h_subcool:
                # options: 1
                self.h_corr_subcool = 1
            if not self.imposed_h_superheat:
                # options: 1
                self.h_corr_superheat = 1
                                
        elif self.phase == '2phase':
            if mode == 'heater':
                if self.ref != None:
                    if not self.imposed_dPdz_f_2phase:
                        # options: 1
                        self.dPdz_f_corr_2phase = 1
                    if not self.imposed_dP_a:
                        # options: 1, 2, 3
                        self.dP_a_corr = 1
                    if not self.imposed_h_2phase:
                        # options: 1
                        self.h_corr_2phase = 1
                    if not self.imposed_rho_2phase:
                        # options: 1, 2, 3
                        self.rho_2phase_corr = 1
                                                                                                        
            elif mode == 'cooler':
                if self.ref != None:
                    if not self.imposed_dPdz_f_2phase:
                        # options: 2
                        self.dPdz_f_corr_2phase = 2
                    if not self.imposed_dP_a:
                        # options: 1, 2, 3
                        self.dP_a_corr = 1
                    if not self.imposed_h_2phase:
                        # options: 2
                        self.h_corr_2phase = 2
                    if not self.imposed_rho_2phase:
                        # options: 1, 2, 3
                        self.rho_2phase_corr = 1
                        
            else:
                raise
        else:
            raise
                                
    def impose_h_superheat(self,h):
        self.imposed_h_superheat = True
        self.h_corr_superheat = h

    def impose_h_subcool(self,h):
        self.imposed_h_subcool = True
        self.h_corr_subcool = h
        
    def impose_h_2phase(self,h):
        self.imposed_h_2phase = True
        self.h_corr_2phase = h
        
    def impose_dPdz_f_subcool(self,dPdz):
        self.imposed_dPdz_f_subcool = True
        self.dPdz_f_corr_subcool = dPdz

    def impose_dPdz_f_superheat(self,dPdz):
        self.imposed_dPdz_f_superheat = True
        self.dPdz_f_corr_superheat = dPdz

    def impose_dPdz_f_2phase(self,dPdz):
        self.imposed_dPdz_f_2phase = True
        self.dPdz_f_corr_2phase = dPdz

    def impose_dP_a(self,dP_a):
        self.imposed_dP_a = True
        self.dP_a_corr = dP_a

    def impose_rho_2phase(self,rho_2phase):
        self.imposed_rho_2phase = True
        self.rho_2phase_corr = rho_2phase

    def calculate_h_1phase(self):
        if self.phase_type == "vapor":
            if self.h_corr_superheat == 1:
                ''' Calculate Single-phase h '''
                h = self.h_1phase_MicroTube(self.G_r, self.Dh, self.h, self.P, self.AS, self.e_D, Phase='Single')
                return h
            
            else:
                raise
        elif self.phase_type == "liquid":
            if self.h_corr_subcool == 1:
                ''' Calculate Single-phase h '''
                h = self.h_1phase_MicroTube(self.G_r, self.Dh, self.h, self.P, self.AS, self.e_D, Phase='Single')
                return h
            
            else:
                raise
        
    def calculate_dPdz_f_1phase(self):
        if self.phase_type == "vapor":
            if self.dPdz_f_corr_superheat == 1:
                ''' Single-Phase pressure drop '''
                f = self.f_1phase_MicroTube(self.G_r, self.Dh, self.h, self.P, self.AS, self.e_D, Phase='Single')
                self.AS.update(CP.HmassP_INPUTS, self.h, self.P)
                rho_r = self.AS.rhomass()
                v_r = 1/rho_r
                dpdz=-f*v_r*self.G_r**2/(2*self.Dh) #Pressure gradient
                return dpdz
            
            else:
                raise
        elif self.phase_type == "liquid":
            if self.dPdz_f_corr_subcool == 1:
                ''' Single-Phase pressure drop '''
                f = self.f_1phase_MicroTube(self.G_r, self.Dh, self.h, self.P, self.AS, self.e_D, Phase='Single')
                self.AS.update(CP.HmassP_INPUTS, self.h, self.P)
                rho_r = self.AS.rhomass()
                v_r = 1/rho_r
                dpdz=-f*v_r*self.G_r**2/(2*self.Dh) #Pressure gradient
                return dpdz
            
            else:
                raise
    
    def calculate_h_2phase(self):
                
        if self.h_corr_2phase == 1:
            ''' calculate two-phase h condensation in microchannel tubes using Kim&Mudawar '''
            self.AS.update(CP.PQ_INPUTS,self.P,0.0)
            Tbubble = self.AS.T()
            self.AS.update(CP.PQ_INPUTS,self.P,1.0)
            Tdew = self.AS.T()
            h = self.KM_Cond_Average_h(min(self.x,self.x_out),max(self.x,self.x_out),self.AS,self.G_r,self.Dh,Tbubble,Tdew,self.P,self.beta)
            return h
        
        elif self.h_corr_2phase == 2:
            ''' calculate two-phase h evaporation in microchannel tubes using Kim&Mudawar '''
            self.AS.update(CP.PQ_INPUTS,self.P,0.0)
            Tbubble = self.AS.T()
            self.AS.update(CP.PQ_INPUTS,self.P,1.0)
            Tdew = self.AS.T()
            h = self.KM_Evap_Average_h(min(self.x,self.x_out),max(self.x,self.x_out),self.AS,self.G_r,self.Dh,Tbubble,Tdew,self.P,self.beta,self.q_flux)
            return h
        else:
            raise

    def calculate_dPdz_f_2phase(self):
        
        if self.dPdz_f_corr_2phase == 1:
            '''condensation pressure drop using Kim&Mudawar'''
            
            self.AS.update(CP.PQ_INPUTS,self.P,0.0)
            Tbubble = self.AS.T()
            self.AS.update(CP.PQ_INPUTS,self.P,1.0)
            Tdew = self.AS.T()
            dpdz = -self.KM_Cond_Average_DPDZ(min(self.x,self.x_out),max(self.x,self.x_out),self.AS,self.G_r,self.Dh,Tbubble,Tdew,self.P,self.beta)
            return dpdz
        
        elif self.dPdz_f_corr_2phase == 2:
            '''evaporation pressure drop using Kim&Mudawar'''
            
            self.AS.update(CP.PQ_INPUTS,self.P,0.0)
            Tbubble = self.AS.T()
            self.AS.update(CP.PQ_INPUTS,self.P,1.0)
            Tdew = self.AS.T()
            dpdz = -self.KM_Evap_Average_DPDZ(min(self.x,self.x_out),max(self.x,self.x_out),self.AS,self.G_r,self.Dh,Tbubble,Tdew,self.P,self.beta,self.q_flux)
            return dpdz
                
    def calculate_dP_a(self):
        if self.dP_a_corr == 1:
            ''' Acceleration preesure drop using Homogeneous slip model '''
            self.AS.update(CP.PQ_INPUTS,self.P,0.0)
            Tbubble = self.AS.T()
            self.AS.update(CP.PQ_INPUTS,self.P,1.0)
            Tdew = self.AS.T()
            DP_accel = self.AccelPressureDrop(min(self.x_out,self.x),max(self.x_out,self.x),self.AS,self.G_r,Tbubble,Tdew,slipModel='Homogeneous')
            if self.mode == 'heater': # Condenser
                DP_accel *= -1
            else:
                pass
            return DP_accel

        elif self.dP_a_corr == 2:
            ''' Acceleration preesure drop using Zivi slip model '''
            self.AS.update(CP.PQ_INPUTS,self.P,0.0)
            Tbubble = self.AS.T()
            self.AS.update(CP.PQ_INPUTS,self.P,1.0)
            Tdew = self.AS.T()
            DP_accel = self.AccelPressureDrop(min(self.x_out,self.x),max(self.x_out,self.x),self.AS,self.G_r,Tbubble,Tdew,slipModel='Zivi')
            if self.mode == 'heater': # Condenser
                DP_accel *= -1
            else:
                pass
            return DP_accel
        
        elif self.dP_a_corr == 3:
            ''' Acceleration preesure drop using Premoli slip model '''
            self.AS.update(CP.PQ_INPUTS,self.P,0.0)
            Tbubble = self.AS.T()
            self.AS.update(CP.PQ_INPUTS,self.P,1.0)
            Tdew = self.AS.T()
            DP_accel = self.AccelPressureDrop(min(self.x_out,self.x),max(self.x_out,self.x),self.AS,self.G_r,Tbubble,Tdew,slipModel='Premoli',D = self.Dh)
            if self.mode == 'heater': # Condenser
                DP_accel *= -1
            else:
                pass
            return DP_accel
        else:
            raise
                
    def calculate_rho_2phase(self):
        if self.rho_2phase_corr == 1:
            ''' Two phase density using Homogeneous model'''
            self.AS.update(CP.PQ_INPUTS,self.P,0.0)
            Tbubble = self.AS.T()
            self.AS.update(CP.PQ_INPUTS,self.P,1.0)
            Tdew = self.AS.T()
            rho_2phase = self.TwoPhaseDensity(self.AS,min(self.x,self.x_out),max(self.x,self.x_out),Tdew,Tbubble,slipModel="Homogeneous")
            return rho_2phase
        elif self.rho_2phase_corr == 2:
            ''' Two phase density using Zivi model'''
            self.AS.update(CP.PQ_INPUTS,self.P,0.0)
            Tbubble = self.AS.T()
            self.AS.update(CP.PQ_INPUTS,self.P,1.0)
            Tdew = self.AS.T()
            rho_2phase = self.TwoPhaseDensity(self.AS,min(self.x,self.x_out),max(self.x,self.x_out),Tdew,Tbubble,slipModel="Zivi")
            return rho_2phase
        elif self.rho_2phase_corr == 3:
            ''' Two phase density using Premoli model'''
            self.AS.update(CP.PQ_INPUTS,self.P,0.0)
            Tbubble = self.AS.T()
            self.AS.update(CP.PQ_INPUTS,self.P,1.0)
            Tdew = self.AS.T()
            rho_2phase = self.TwoPhaseDensity(self.AS,min(self.x,self.x_out),max(self.x,self.x_out),Tdew,Tbubble,slipModel="Premoli")
            return rho_2phase
        else:
            raise
        
    def TwoPhaseDensity(self, AS, xmin, xmax, Tdew, Tbubble, slipModel='Zivi'):
        """
        function to obtain the average density in the two-phase region
        AS : AbstractState with the refrigerant name and backend
        """
        AS.update(CP.QT_INPUTS, 1.0, Tdew)
        rhog = AS.rhomass()  # [kg/m^3]
        AS.update(CP.QT_INPUTS, 0.0, Tbubble)
        rhof = AS.rhomass()  # [kg/m^3]

        if slipModel == 'Zivi':
            S = pow(rhof/rhog, 0.3333)
        elif slipModel == 'Homogeneous':
            S = 1
        elif slipModel == 'Premoli':
            S = self.Premoli((xmin+xmax)/2, AS, self.G_r, self.Dh, Tbubble, Tdew, rhof,rhog)
        else:
            raise ValueError(
                "slipModel must be either 'Zivi' or 'Homogeneous' or 'Premoli'")
        C = S*rhog/rhof

        if xmin+100*machine_eps < 0 or xmax-100*machine_eps > 1.0:
            raise ValueError('Quality must be between 0 and 1')
        # Avoid the zero and one qualities (undefined integral)
        if abs(xmax-xmin) < 100*machine_eps:
            alpha_average = 1/(1+C*(1-xmin)/xmin)
        else:
            if xmin >= 1.0:
                alpha_average = 1.0
            elif xmax <= 0.0:
                alpha_average = 0.0
            else:
                alpha_average = - \
                    (C*(log(((xmax-1.0)*C-xmax)/((xmin-1.0)*C-xmin)) +
                        xmax-xmin)-xmax+xmin)/(C**2-2*C+1)/(xmax-xmin)
        return alpha_average*rhog + (1-alpha_average)*rhof
    
    def AccelPressureDrop(self, x_min, x_max, AS, G, Tbubble, Tdew, D=None, rhosatL=None,rhosatV=None,slipModel='Zivi'):
        """
        Accelerational pressure drop

        From -dpdz|A=G^2*d[x^2v_g/alpha+(1-x)^2*v_f/(1-alpha)]/dz

        Integrating over z from 0 to L where x=x_1 at z=0 and x=x_2 at z=L

        Maxima code:
                alpha:1/(1+S*rho_g/rho_f*(1-x)/x)$
                num1:x^2/rho_g$
                num2:(1-x)^2/rho_f$
                subst(num1/alpha+num2/(1-alpha),x,1);
                subst(num1/alpha+num2/(1-alpha),x,0);
        """
        if rhosatL == None or rhosatV == None:
            AS.update(CP.QT_INPUTS, 1.0, Tdew)
            rhosatV = AS.rhomass()  # [kg/m^3]
            AS.update(CP.QT_INPUTS, 0.0, Tbubble)
            rhosatL = AS.rhomass()  # [kg/m^3]

        def f(x, AS, G, D, Tbubble, Tdew, rhoL, rhoV):
            if abs(x) < 1e-12:
                return 1/rhosatL
            elif abs(1-x) < 1e-12:
                return 1/rhosatV
            else:
                if slipModel == 'Premoli':
                    S = self.Premoli(x, AS, G, D, Tbubble, Tdew, rhoL,rhoV)
                elif slipModel == 'Zivi':
                    S = pow(rhoL/rhoV, 1/3)
                elif slipModel == 'Homogeneous':
                    S = 1
                else:
                    raise ValueError(
                        "slipModel must be either 'Premoli', 'Zivi' or 'Homogeneous'")
                alpha = 1/(1+S*rhoV/rhoL*(1-x)/x)
                return x**2/rhoV/alpha+(1-x)**2/rhoL/(1-alpha)

        return G**2*(f(x_min, AS, G, D, Tbubble, Tdew, rhosatL, rhosatV)-f(x_max,AS,G,D,Tbubble,Tdew,rhosatL,rhosatV))

    def Premoli(self, x, AS, G, D, Tbubble, Tdew, rhoL=None, rhoV=None):
        '''
        return Premoli (1970) slip flow factor
        function copied from ACMODEL souce code
        same correlations can be found in the Appendix A2 of Petterson (2000)
        '''
        if rhoL == None or rhoV == None:
            AS.update(CP.QT_INPUTS, 1.0, Tdew)
            rhoV = AS.rhomass()  # [kg/m^3]
            AS.update(CP.QT_INPUTS, 0.0, Tbubble)
            rhoL = AS.rhomass()  # [kg/m^3]

        AS.update(CP.QT_INPUTS, 0.0, Tbubble)
        muL = AS.viscosity()  # [Pa-s]
        psat = AS.p()  # [Pa]
        AS.update(CP.PQ_INPUTS, psat, x)
        sigma = AS.surface_tension()  # [N/m]
        PI1 = rhoV/rhoL
        We = pow(G, 2)*D/(sigma*rhoL)
        Re_L = G*D/muL
        F_1 = 1.578*pow(Re_L, -0.19)*pow(PI1, -0.22)
        F_2 = 0.0273*We*pow(Re_L, -0.51)*pow(PI1, 0.08)
        Y = (x/(1-x))*1/PI1
        S = 1+F_1*pow((Y/(1+F_2*Y)-F_2*Y), 0.5)

        return S

    def KM_Cond_Average_h(self,x_min,x_max,AS,G,Dh,Tbubble,Tdew,p,beta,C=None,satTransport=None):
        """
        Returns the  average heat transfer coefficient between qualities of 
        x_min and x_max. for Kim&Mudawar two-phase condensation in mico-channel HX 
        
        To obtain the heat transfer for a given value of x, pass it in as x_min and x_max
        
        Required parameters:
        * x_min : The minimum quality for the range [-]
        * x_max : The maximum quality for the range [-]
        * AS : AbstractState with the refrigerant name and backend
        * G : Mass flux [kg/m^2/s]
        * Dh : Hydraulic diameter of tube [m]
        * Tbubble : Bubblepoint temperature of refrigerant [K]
        * Tdew : Dewpoint temperature of refrigerant [K]
        * beta: channel aspect ratio (=width/height)
        
        Optional parameters:
        * satTransport : A dictionary with the keys 'mu_f','mu_g,'rho_f','rho_g', 'sigma' for the saturation properties.  So they can be calculated once and passed in for a slight improvement in efficiency 
        """
        
        def KMFunc(x):
            h = self.Kim_Mudawar_condensing_h(AS,G,Dh,x,Tbubble,Tdew,p,beta,C,satTransport)
            return h
        
        ## Use Simpson's Rule to calculate the average pressure gradient
        ## Can't use adapative quadrature since function is not sufficiently smooth
        ## Not clear why not sufficiently smooth at x>0.9
        if x_min==x_max:
            return KMFunc(x_min)
        else:
            #Calculate the tranport properties once
            satTransport={}
            AS.update(CP.QT_INPUTS,0.0,Tbubble)
            satTransport['rho_f']=AS.rhomass() #[kg/m^3]
            satTransport['mu_f']=AS.viscosity() #[Pa-s OR kg/m-s]
            satTransport['cp_f']=AS.cpmass() #[J/kg-K]
            satTransport['k_f']=AS.conductivity() #[W/m-K]
            AS.update(CP.QT_INPUTS,1.0,Tdew)
            satTransport['rho_g']=AS.rhomass() #[kg/m^3]
            satTransport['mu_g']=AS.viscosity() #[Pa-s OR kg/m-s]
            
            #Calculate Dp and h over the range of xx
            xx=np.linspace(x_min,x_max,100)
            h=np.zeros_like(xx)
            for i in range(len(xx)):
                h[i]=KMFunc(xx[i])
            
            #Use Simpson's rule to carry out numerical integration to get average DP and average h
            if abs(x_max-x_min)<100*machine_eps:
                #return just one of the edge values
                return h[0]
            else:
                #Use Simpson's rule to carry out numerical integration to get average DP and average h
                return simps(h,xx)/(x_max-x_min)
            
    def Kim_Mudawar_condensing_h(self,AS, G, Dh, x, Tbubble, Tdew, p, beta, C=None, satTransport=None):
        """
        This function return the pressure gradient and heat transfer coefficient for 
        two phase fluid inside Micro-channel tube while CONDENSATION
        Correlations Based on: 
        Kim and Mudawar (2013) "Universal approach to predicting heat transfer coefficient 
        for condensing min/micro-channel flow", Int. J Heat Mass, 56, 238-250
        """
        
        #Convert the quality, which might come in as a single numpy float value, to a float
        #With the conversion, >20x speedup in the LockhartMartinelli function, not clear why
        x=float(x)
        
        if satTransport==None:
            # Calculate Necessary saturation properties
            AS.update(CP.QT_INPUTS,0.0,Tbubble)
            rho_f=AS.rhomass() #[kg/m^3]
            mu_f=AS.viscosity() #[Pa-s OR kg/m-s]
            cp_f=AS.cpmass() #[J/kg-K]
            k_f=AS.conductivity() #[W/m-K]
            AS.update(CP.QT_INPUTS,1.0,Tdew)
            rho_g=AS.rhomass() #[kg/m^3]
            mu_g=AS.viscosity() #[Pa-s OR kg/m-s]
        else:
            #Pull out of the dictionary
            rho_f=satTransport['rho_f']
            rho_g=satTransport['rho_g']
            mu_f=satTransport['mu_f']
            mu_g=satTransport['mu_g']
            cp_f=satTransport['cp_f']
            k_f=satTransport['k_f']
        
        AS.update(CP.PQ_INPUTS,p,x)
        sigma=AS.surface_tension() #surface tesnion [N/m]
        
        Pr_f = cp_f * mu_f / k_f #[-]
        
        Re_f = G*(1-x)*Dh/mu_f
        Re_g = G*x*Dh/mu_g
    
        
        if x==1: #No liquid
            f_f = 0 #Just to be ok until next step
        elif (Re_f<2000): #Laminar
            f_f = 16.0/Re_f
            if (beta<1):
                f_f = 24*(1-1.3553*beta+1.9467*beta*beta-1.7012*pow(beta,3)+0.9564*pow(beta,4)-0.2537*pow(beta,5))/Re_f
        elif (Re_f>=20000): #Fully-Turbulent
            f_f = 0.046*pow(Re_f,-0.2)
        else: #Transient
            f_f = 0.079*pow(Re_f,-0.25)
    
        if x==0: #No gas
            f_g = 0 #Just to be ok until next step
        elif (Re_g<2000): #Laminar
            f_g=16.0/Re_g
            if (beta<1):
                f_g = 24*(1-1.3553*beta+1.9467*beta*beta-1.7012*pow(beta,3)+0.9564*pow(beta,4)-0.2537*pow(beta,5))/Re_g
        elif (Re_g>=20000): #Fully-Turbulent
            f_g = 0.046*pow(Re_g,-0.2)
        else: #Transient
            f_g = 0.079*pow(Re_g,-0.25)
    
        Re_fo = G*Dh/mu_f
        Su_go = rho_g*sigma*Dh/pow(mu_g,2)
    
        dpdz_f = 2*f_f/rho_f*pow(G*(1-x),2)/Dh
        dpdz_g = 2*f_g/rho_g*pow(G*x,2)/Dh
    
        if x<=0:    
            # Entirely liquid
            AS.update(CP.QT_INPUTS,0.0,Tbubble)
            psat = AS.p() #pressure [Pa]
            h = self.h_1phase_MicroTube(G, Dh, Tbubble, psat, AS, self.e_D, Phase='SatLiq')
            return h
        if x>=1:
            #Entirely vapor
            AS.update(CP.QT_INPUTS,1.0,Tdew)
            psat = AS.p() #pressure [Pa]
            h = self.h_1phase_MicroTube(G, Dh, Tdew, psat, AS, self.e_D, Phase='SatVap')
            return h
        
        X = sqrt(dpdz_f/dpdz_g)
    
        # Find the C coefficient (Calculate C if not passed, otherwise use the set value of C)
        if C==None:
            if (Re_f<2000 and Re_g<2000):
                C = 3.5e-5*pow(Re_fo,0.44)*pow(Su_go,0.50)*pow(rho_f/rho_g,0.48)   
            elif (Re_f<2000 and Re_g>=2000):
                C = 0.0015*pow(Re_fo,0.59)*pow(Su_go,0.19)*pow(rho_f/rho_g,0.36)
            elif (Re_f>=2000 and Re_g<2000):
                C = 8.7e-4*pow(Re_fo,0.17)*pow(Su_go,0.50)*pow(rho_f/rho_g,0.14)
            elif (Re_f>=2000 and Re_g>=2000):
                C = 0.39*pow(Re_fo,0.03)*pow(Su_go,0.10)*pow(rho_f/rho_g,0.35)
        else:
            pass
        
        # Two-phase multiplier
        phi_g_square = 1.0 + C*X + X**2
                
        Xtt = X
        
        # Modified Weber number
        if (Re_f <= 1250):
            We_star = 2.45 * pow(Re_g,0.64) / (pow(Su_go,0.3) * pow(1 + 1.09*pow(Xtt,0.039),0.4))
        else:
            We_star = 0.85 * pow(Re_g,0.79) * pow(Xtt,0.157) / (pow(Su_go,0.3) * pow(1 + 1.09*pow(Xtt,0.039),0.4)) * pow(pow(mu_g/mu_f,2) * (rho_f/rho_g),0.084)
        
        # Condensation Heat transfer coefficient
        if (We_star > 7*Xtt**0.2): ##for annual flow (smooth-annular, wavy-annular, transition)
            h = k_f/Dh * 0.048 * pow(Re_f,0.69) * pow(Pr_f,0.34) * sqrt(phi_g_square) / Xtt
        else: ##for slug and bubbly flow
            h = k_f/Dh *pow((0.048 * pow(Re_f,0.69) * pow(Pr_f,0.34) * sqrt(phi_g_square) / Xtt)**2 + (3.2e-7 * pow(Re_f,-0.38) * pow(Su_go,1.39))**2 ,0.5)
        
        return h
    
    def KM_Evap_Average_h(self,x_min,x_max,AS,G,Dh,Tbubble,Tdew,p,beta,q_fluxH,PH_PF=1,C=None,satTransport=None):
        """
        Returns the average heat transfer coefficient between qualities of 
        x_min and x_max. for Kim&Mudawar two-phase evaporation in mico-channel 
        HX 
        
        To obtain the heat transfer coefficient for a given value of x, pass 
        it in as x_min and x_max
        
        Required parameters:
        * x_min : The minimum quality for the range [-]
        * x_max : The maximum quality for the range [-]
        * AS : AbstractState with the refrigerant name and backend
        * G : Mass flux [kg/m^2/s]
        * Dh : Hydraulic diameter of tube [m]
        * Tbubble : Bubblepoint temperature of refrigerant [K]
        * Tdew : Dewpoint temperature of refrigerant [K]
        * p : pressure [Pa]
        * beta: channel aspect ratio (=width/height)
        * q_fluxH: heat flux [W/m^2]
        * PH_PF: ratio of PH over PF where PH: heated perimeter of channel, PF: wetted perimeter of channel
        
        Optional parameters:
        * satTransport : A dictionary with the keys 'mu_f','mu_g,'rho_f','rho_g', 'sigma' for the saturation properties.  So they can be calculated once and passed in for a slight improvement in efficiency 
        """
        
        def KMFunc(x):
            h = self.Kim_Mudawar_boiling_h(AS,G,Dh,x,Tbubble,Tdew,p,beta,q_fluxH,PH_PF,C,satTransport)
            return h
        
        ## Use Simpson's Rule to calculate the average pressure gradient
        ## Can't use adapative quadrature since function is not sufficiently smooth
        ## Not clear why not sufficiently smooth at x>0.9
        if x_min==x_max:
            return KMFunc(x_min)
        else:
            #Calculate the tranport properties once
            satTransport={}
            AS.update(CP.QT_INPUTS,0.0,Tbubble)
            satTransport['rho_f']=AS.rhomass() #[kg/m^3]
            satTransport['mu_f']=AS.viscosity() #[Pa-s OR kg/m-s]
            h_f=AS.hmass() #[J/kg]
            satTransport['cp_f']=AS.cpmass() #[J/kg-K]
            satTransport['k_f']=AS.conductivity() #[W/m-K]
            AS.update(CP.QT_INPUTS,1.0,Tdew)
            satTransport['rho_g']=AS.rhomass() #[kg/m^3]
            satTransport['mu_g']=AS.viscosity() #[Pa-s OR kg/m-s]
            h_g=AS.hmass() #[J/kg]
            satTransport['h_fg'] = h_g - h_f #[J/kg]
            
            #Calculate Dp and h over the range of xx
            xx=np.linspace(x_min,x_max,100)
            h=np.zeros_like(xx)
            for i in range(len(xx)):
                h[i]=KMFunc(xx[i])
            
            #Use Simpson's rule to carry out numerical integration to get average DP and average h
            if abs(x_max-x_min)<100*machine_eps:
                #return just one of the edge values
                return h[0]
            else:
                #Use Simpson's rule to carry out numerical integration to get average DP and average h
                return simps(h,xx)/(x_max-x_min)
            
    def Kim_Mudawar_boiling_h(self,AS, G, Dh, x, Tbubble, Tdew, p, beta, q_fluxH, PH_PF=1, C=None, satTransport=None):
        """
        This function return the heat transfer coefficient for two phase fluid
        inside Micro-channel tube while BOILING (EVAPORATION)
                
        Correlations of HTC Based on: Kim and Mudawar (2013) "Universal approach to predicting
        saturated flow boiling heat transfer in mini/micro-channels - Part II. Two-heat heat transfer coefficient"
        """
        #Convert the quality, which might come in as a single numpy float value, to a float
        #With the conversion, >20x speedup in the LockhartMartinelli function, not clear why
        x=float(x)
        
        if satTransport==None:
            # Calculate Necessary saturation properties
            AS.update(CP.QT_INPUTS,0.0,Tbubble)
            rho_f=AS.rhomass() #[kg/m^3]
            mu_f=AS.viscosity() #[Pa-s OR kg/m-s]
            h_f=AS.hmass() #[J/kg]
            cp_f=AS.cpmass() #[J/kg-K]
            k_f=AS.conductivity() #[W/m-K]
            AS.update(CP.QT_INPUTS,1.0,Tdew)
            rho_g=AS.rhomass() #[kg/m^3]
            mu_g=AS.viscosity() #[Pa-s OR kg/m-s]
            h_g=AS.hmass() #[J/kg]
            h_fg = h_g - h_f #[J/kg]
        else:
            #Pull out of the dictionary
            rho_f=satTransport['rho_f']
            rho_g=satTransport['rho_g']
            mu_f=satTransport['mu_f']
            mu_g=satTransport['mu_g']
            h_fg=satTransport['h_fg']
            cp_f=satTransport['cp_f']
            k_f=satTransport['k_f']
        
        pc=AS.p_critical() #critical pressure [Pa]
        pr=p/pc #reducred pressure [-]
        AS.update(CP.PQ_INPUTS,p,x)
        sigma = AS.surface_tension() #surface tesnion [N/m]
    
        Re_f = G*(1-x)*Dh/mu_f
        Re_g = G*x*Dh/mu_g
        Pr_f = cp_f*mu_f/k_f
        
        if x==1: #No liquid
            f_f = 0 #Just to be ok until next step
        elif (Re_f<2000): #Laminar
            f_f = 16.0/Re_f
            if (beta<1):
                f_f = 24*(1-1.3553*beta+1.9467*beta*beta-1.7012*pow(beta,3)+0.9564*pow(beta,4)-0.2537*pow(beta,5))/Re_f
        elif (Re_f>=20000): #Fully-Turbulent
            f_f = 0.046*pow(Re_f,-0.2)
        else: #Transient
            f_f = 0.079*pow(Re_f,-0.25)
    
        if x==0: #No gas
            f_g = 0 #Just to be ok until next step
        elif (Re_g<2000): #Laminar
            f_g=16.0/Re_g
            if (beta<1):
                f_g = 24*(1-1.3553*beta+1.9467*beta*beta-1.7012*pow(beta,3)+0.9564*pow(beta,4)-0.2537*pow(beta,5))/Re_g
        elif (Re_g>=20000): #Fully-Turbulent
            f_g = 0.046*pow(Re_g,-0.2)
        else: #Transient
            f_g = 0.079*pow(Re_g,-0.25)
    
        Re_fo = G*Dh/mu_f
        Su_go = rho_g*sigma*Dh/pow(mu_g,2)
    
        dpdz_f = 2*f_f/rho_f*pow(G*(1-x),2)/Dh
        dpdz_g = 2*f_g/rho_g*pow(G*x,2)/Dh
        
        if x<=0:
            # Entirely liquid
            AS.update(CP.QT_INPUTS,0.0,Tbubble)
            psat = AS.p() #pressure [Pa]
            hsat = AS.hmass()
            h = self.h_1phase_MicroTube(G, Dh, hsat, psat, AS, self.e_D, Phase='SatLiq')
            return h
        if x>=1:
            #Entirely vapor
            AS.update(CP.QT_INPUTS,1.0,Tdew)
            psat = AS.p() #pressure [Pa]
            hsat = AS.hmass()
            h = self.h_1phase_MicroTube(G, Dh, hsat, psat, AS, self.e_D, Phase='SatVap')
            return h

        #Use calculated Lockhart-Martinelli parameter         
        Xtt = sqrt(dpdz_f/dpdz_g)
        
        We_fo = G*G*Dh/rho_f/sigma
        Bo = q_fluxH/(G*h_fg)
                        
        #Pre-dryout saturated flow boiling Heat transfer coefficient
        h_nb = (2345*pow(Bo*PH_PF,0.7)*pow(pr,0.38)*pow(1-x,-0.51))*(0.023*pow(Re_f,0.8)*pow(Pr_f,0.4)*k_f/Dh)
        h_cb = (5.2*pow(Bo*PH_PF,0.08)*pow(We_fo,-0.54) + 3.5*pow(1/Xtt,0.94)*pow(rho_g/rho_f,0.25))*(0.023*pow(Re_f,0.8)*pow(Pr_f,0.4)*k_f/Dh)
        h = pow(h_nb**2 +h_cb**2,0.5)
        
        return h

    def KM_Cond_Average_DPDZ(self,x_min,x_max,AS,G,Dh,Tbubble,Tdew,p,beta,C=None,satTransport=None):
        """
        Returns the average pressure gradient between qualities of x_min and x_max.
        for Kim&Mudawar two-phase condensation in mico-channel HX 
        
        To obtain the pressure gradient for a given value of x, pass it in as x_min and x_max
        
        Required parameters:
        * x_min : The minimum quality for the range [-]
        * x_max : The maximum quality for the range [-]
        * AS : AbstractState with the refrigerant name and backend
        * G : Mass flux [kg/m^2/s]
        * Dh : Hydraulic diameter of tube [m]
        * Tbubble : Bubblepoint temperature of refrigerant [K]
        * Tdew : Dewpoint temperature of refrigerant [K]
        * beta: channel aspect ratio (=width/height)
        
        Optional parameters:
        * satTransport : A dictionary with the keys 'mu_f','mu_g,'rho_f','rho_g', 'sigma' for the saturation properties.  So they can be calculated once and passed in for a slight improvement in efficiency 
        """
        
        def KMFunc(x):
            dpdz = self.Kim_Mudawar_condensing_DPDZ(AS,G,Dh,x,Tbubble,Tdew,p,beta,C,satTransport)
            return dpdz
        
        ## Use Simpson's Rule to calculate the average pressure gradient
        ## Can't use adapative quadrature since function is not sufficiently smooth
        ## Not clear why not sufficiently smooth at x>0.9
        if x_min==x_max:
            return KMFunc(x_min)
        else:
            #Calculate the tranport properties once
            satTransport={}
            AS.update(CP.QT_INPUTS,0.0,Tbubble)
            satTransport['rho_f']=AS.rhomass() #[kg/m^3]
            satTransport['mu_f']=AS.viscosity() #[Pa-s OR kg/m-s]
            satTransport['cp_f']=AS.cpmass() #[J/kg-K]
            satTransport['k_f']=AS.conductivity() #[W/m-K]
            AS.update(CP.QT_INPUTS,1.0,Tdew)
            satTransport['rho_g']=AS.rhomass() #[kg/m^3]
            satTransport['mu_g']=AS.viscosity() #[Pa-s OR kg/m-s]
            
            #Calculate Dp and h over the range of xx
            xx=np.linspace(x_min,x_max,100)
            DP=np.zeros_like(xx)
            for i in range(len(xx)):
                DP[i]=KMFunc(xx[i])
            
            #Use Simpson's rule to carry out numerical integration to get average DP and average h
            if abs(x_max-x_min)<100*machine_eps:
                #return just one of the edge values
                return DP[0]
            else:
                #Use Simpson's rule to carry out numerical integration to get average DP and average h
                return simps(DP,xx)/(x_max-x_min)
            
    def Kim_Mudawar_condensing_DPDZ(self,AS, G, Dh, x, Tbubble, Tdew, p, beta, C=None, satTransport=None):
        """
        This function return the pressure gradient for  two phase fluid inside 
        Micro-channel tube while CONDENSATION
        Correlations Based on: 
        Kim and Mudawar (2012) "Universal approach to predicting two-phase 
        frictional pressure drop and condensing mini/micro-channel flows", Int. J Heat Mass, 55, 3246-3261
        """
        
        #Convert the quality, which might come in as a single numpy float value, to a float
        #With the conversion, >20x speedup in the LockhartMartinelli function, not clear why
        x=float(x)
        
        if satTransport==None:
            # Calculate Necessary saturation properties
            AS.update(CP.QT_INPUTS,0.0,Tbubble)
            rho_f=AS.rhomass() #[kg/m^3]
            mu_f=AS.viscosity() #[Pa-s OR kg/m-s]
            cp_f=AS.cpmass() #[J/kg-K]
            k_f=AS.conductivity() #[W/m-K]
            AS.update(CP.QT_INPUTS,1.0,Tdew)
            rho_g=AS.rhomass() #[kg/m^3]
            mu_g=AS.viscosity() #[Pa-s OR kg/m-s]
        else:
            #Pull out of the dictionary
            rho_f=satTransport['rho_f']
            rho_g=satTransport['rho_g']
            mu_f=satTransport['mu_f']
            mu_g=satTransport['mu_g']
            cp_f=satTransport['cp_f']
            k_f=satTransport['k_f']
        
        AS.update(CP.PQ_INPUTS,p,x)
        sigma=AS.surface_tension() #surface tesnion [N/m]
        
        Pr_f = cp_f * mu_f / k_f #[-]
        
        Re_f = G*(1-x)*Dh/mu_f
        Re_g = G*x*Dh/mu_g
    
        
        if x==1: #No liquid
            f_f = 0 #Just to be ok until next step
        elif (Re_f<2000): #Laminar
            f_f = 16.0/Re_f
            if (beta<1):
                f_f = 24*(1-1.3553*beta+1.9467*beta*beta-1.7012*pow(beta,3)+0.9564*pow(beta,4)-0.2537*pow(beta,5))/Re_f
        elif (Re_f>=20000): #Fully-Turbulent
            f_f = 0.046*pow(Re_f,-0.2)
        else: #Transient
            f_f = 0.079*pow(Re_f,-0.25)
    
        if x==0: #No gas
            f_g = 0 #Just to be ok until next step
        elif (Re_g<2000): #Laminar
            f_g=16.0/Re_g
            if (beta<1):
                f_g = 24*(1-1.3553*beta+1.9467*beta*beta-1.7012*pow(beta,3)+0.9564*pow(beta,4)-0.2537*pow(beta,5))/Re_g
        elif (Re_g>=20000): #Fully-Turbulent
            f_g = 0.046*pow(Re_g,-0.2)
        else: #Transient
            f_g = 0.079*pow(Re_g,-0.25)
    
        Re_fo = G*Dh/mu_f
        Su_go = rho_g*sigma*Dh/pow(mu_g,2)
    
        dpdz_f = 2*f_f/rho_f*pow(G*(1-x),2)/Dh
        dpdz_g = 2*f_g/rho_g*pow(G*x,2)/Dh
    
        if x<=0:    
            # Entirely liquid
            dpdz = dpdz_f
            return dpdz
        if x>=1:
            #Entirely vapor
            dpdz = dpdz_g
            return dpdz
        
        X = sqrt(dpdz_f/dpdz_g)
    
        # Find the C coefficient (Calculate C if not passed, otherwise use the set value of C)
        if C==None:
            if (Re_f<2000 and Re_g<2000):
                C = 3.5e-5*pow(Re_fo,0.44)*pow(Su_go,0.50)*pow(rho_f/rho_g,0.48)   
            elif (Re_f<2000 and Re_g>=2000):
                C = 0.0015*pow(Re_fo,0.59)*pow(Su_go,0.19)*pow(rho_f/rho_g,0.36)
            elif (Re_f>=2000 and Re_g<2000):
                C = 8.7e-4*pow(Re_fo,0.17)*pow(Su_go,0.50)*pow(rho_f/rho_g,0.14)
            elif (Re_f>=2000 and Re_g>=2000):
                C = 0.39*pow(Re_fo,0.03)*pow(Su_go,0.10)*pow(rho_f/rho_g,0.35)
        else:
            pass
        
        # Two-phase multiplier
        phi_f_square = 1.0 + C/X + 1.0/X**2
        phi_g_square = 1.0 + C*X + X**2
        
        # Find Condensing pressure drop griendient  
        if dpdz_g*phi_g_square > dpdz_f*phi_f_square:
            dpdz=dpdz_g*phi_g_square
        else:
            dpdz=dpdz_f*phi_f_square
        return dpdz
    
    def KM_Evap_Average_DPDZ(self,x_min,x_max,AS,G,Dh,Tbubble,Tdew,p,beta,q_fluxH,PH_PF=1,C=None,satTransport=None):
        """
        Returns the average pressure gradient between qualities of x_min and 
        x_max. for Kim&Mudawar two-phase evaporation in mico-channel HX 
        
        To obtain the pressure gradient for a given value of x, pass it in as x_min and x_max
        
        Required parameters:
        * x_min : The minimum quality for the range [-]
        * x_max : The maximum quality for the range [-]
        * AS : AbstractState with the refrigerant name and backend
        * G : Mass flux [kg/m^2/s]
        * Dh : Hydraulic diameter of tube [m]
        * Tbubble : Bubblepoint temperature of refrigerant [K]
        * Tdew : Dewpoint temperature of refrigerant [K]
        * p : pressure [Pa]
        * beta: channel aspect ratio (=width/height)
        * q_fluxH: heat flux [W/m^2]
        * PH_PF: ratio of PH over PF where PH: heated perimeter of channel, PF: wetted perimeter of channel
        
        Optional parameters:
        * satTransport : A dictionary with the keys 'mu_f','mu_g,'rho_f','rho_g', 'sigma' for the saturation properties.  So they can be calculated once and passed in for a slight improvement in efficiency 
        """
        
        def KMFunc(x):
            dpdz = self.Kim_Mudawar_boiling_DPDZ(AS,G,Dh,x,Tbubble,Tdew,p,beta,q_fluxH,PH_PF,C,satTransport)
            return dpdz
        
        ## Use Simpson's Rule to calculate the average pressure gradient
        ## Can't use adapative quadrature since function is not sufficiently smooth
        ## Not clear why not sufficiently smooth at x>0.9
        if x_min==x_max:
            return KMFunc(x_min)
        else:
            #Calculate the tranport properties once
            satTransport={}
            AS.update(CP.QT_INPUTS,0.0,Tbubble)
            satTransport['rho_f']=AS.rhomass() #[kg/m^3]
            satTransport['mu_f']=AS.viscosity() #[Pa-s OR kg/m-s]
            h_f=AS.hmass() #[J/kg]
            satTransport['cp_f']=AS.cpmass() #[J/kg-K]
            satTransport['k_f']=AS.conductivity() #[W/m-K]
            AS.update(CP.QT_INPUTS,1.0,Tdew)
            satTransport['rho_g']=AS.rhomass() #[kg/m^3]
            satTransport['mu_g']=AS.viscosity() #[Pa-s OR kg/m-s]
            h_g=AS.hmass() #[J/kg]
            satTransport['h_fg'] = h_g - h_f #[J/kg]
            
            #Calculate Dp and h over the range of xx
            xx=np.linspace(x_min,x_max,100)
            DP=np.zeros_like(xx)
            for i in range(len(xx)):
                DP[i]=KMFunc(xx[i])
            
            #Use Simpson's rule to carry out numerical integration to get average DP and average h
            if abs(x_max-x_min)<100*machine_eps:
                #return just one of the edge values
                return DP[0]
            else:
                #Use Simpson's rule to carry out numerical integration to get average DP and average h
                return simps(DP,xx)/(x_max-x_min)
            
    def Kim_Mudawar_boiling_DPDZ(self,AS, G, Dh, x, Tbubble, Tdew, p, beta, q_fluxH, PH_PF=1, C=None, satTransport=None):
        """
        This function return the pressure gradient for two phase fluid inside 
        Micro-channel tube while BOILING (EVAPORATION)
        
        Correlations of DPDZ Based on: Kim and Mudawar (2013) "Universal approach to predicting
        two-phase frictional pressure drop for mini/micro-channel saturated flow boiling"
        
        """
        #Convert the quality, which might come in as a single numpy float value, to a float
        #With the conversion, >20x speedup in the LockhartMartinelli function, not clear why
        x=float(x)
        
        if satTransport==None:
            # Calculate Necessary saturation properties
            AS.update(CP.QT_INPUTS,0.0,Tbubble)
            rho_f=AS.rhomass() #[kg/m^3]
            mu_f=AS.viscosity() #[Pa-s OR kg/m-s]
            h_f=AS.hmass() #[J/kg]
            cp_f=AS.cpmass() #[J/kg-K]
            k_f=AS.conductivity() #[W/m-K]
            AS.update(CP.QT_INPUTS,1.0,Tdew)
            rho_g=AS.rhomass() #[kg/m^3]
            mu_g=AS.viscosity() #[Pa-s OR kg/m-s]
            h_g=AS.hmass() #[J/kg]
            h_fg = h_g - h_f #[J/kg]
        else:
            #Pull out of the dictionary
            rho_f=satTransport['rho_f']
            rho_g=satTransport['rho_g']
            mu_f=satTransport['mu_f']
            mu_g=satTransport['mu_g']
            h_fg=satTransport['h_fg']
            cp_f=satTransport['cp_f']
            k_f=satTransport['k_f']
        
        pc=AS.p_critical() #critical pressure [Pa]
        pr=p/pc #reducred pressure [-]
        AS.update(CP.PQ_INPUTS,p,x)
        sigma = AS.surface_tension() #surface tesnion [N/m]
    
        Re_f = G*(1-x)*Dh/mu_f
        Re_g = G*x*Dh/mu_g
        Pr_f = cp_f*mu_f/k_f
        
        if x==1: #No liquid
            f_f = 0 #Just to be ok until next step
        elif (Re_f<2000): #Laminar
            f_f = 16.0/Re_f
            if (beta<1):
                f_f = 24*(1-1.3553*beta+1.9467*beta*beta-1.7012*pow(beta,3)+0.9564*pow(beta,4)-0.2537*pow(beta,5))/Re_f
        elif (Re_f>=20000): #Fully-Turbulent
            f_f = 0.046*pow(Re_f,-0.2)
        else: #Transient
            f_f = 0.079*pow(Re_f,-0.25)
    
        if x==0: #No gas
            f_g = 0 #Just to be ok until next step
        elif (Re_g<2000): #Laminar
            f_g=16.0/Re_g
            if (beta<1):
                f_g = 24*(1-1.3553*beta+1.9467*beta*beta-1.7012*pow(beta,3)+0.9564*pow(beta,4)-0.2537*pow(beta,5))/Re_g
        elif (Re_g>=20000): #Fully-Turbulent
            f_g = 0.046*pow(Re_g,-0.2)
        else: #Transient
            f_g = 0.079*pow(Re_g,-0.25)
    
        Re_fo = G*Dh/mu_f
        Su_go = rho_g*sigma*Dh/pow(mu_g,2)
    
        dpdz_f = 2*f_f/rho_f*pow(G*(1-x),2)/Dh
        dpdz_g = 2*f_g/rho_g*pow(G*x,2)/Dh
        
        if x<=0:
            # Entirely liquid
            dpdz = dpdz_f
            return dpdz
        if x>=1:
            #Entirely vapor
            dpdz = dpdz_g
            return dpdz
        
        X = sqrt(dpdz_f/dpdz_g)
        
        We_fo = G*G*Dh/rho_f/sigma
        Bo = q_fluxH/(G*h_fg)
        
        # Find the C coefficient (Calculate C if not passed, otherwise use the set value of C)
        if C==None:
            # Calculate C (non boiling)
            if (Re_f<2000 and Re_g<2000):
                Cnon_boiling = 3.5e-5*pow(Re_fo,0.44)*pow(Su_go,0.50)*pow(rho_f/rho_g,0.48)   
            elif (Re_f<2000 and Re_g>=2000):
                Cnon_boiling = 0.0015*pow(Re_fo,0.59)*pow(Su_go,0.19)*pow(rho_f/rho_g,0.36)
            elif (Re_f>=2000 and Re_g<2000):
                Cnon_boiling = 8.7e-4*pow(Re_fo,0.17)*pow(Su_go,0.50)*pow(rho_f/rho_g,0.14)
            elif (Re_f>=2000 and Re_g>=2000):
                Cnon_boiling = 0.39*pow(Re_fo,0.03)*pow(Su_go,0.10)*pow(rho_f/rho_g,0.35)
            # Calculate actual C  
            if (Re_f >= 2000):
                C = Cnon_boiling*(1+60*pow(We_fo,0.32)*pow(Bo*PH_PF,0.78))  
            else:
                C = Cnon_boiling*(1+530*pow(We_fo,0.52)*pow(Bo*PH_PF,1.09))
        else:
            pass
        
        #Two-phase multiplier
        phi_f_square = 1 + C/X + 1/X**2
        phi_g_square = 1 + C*X + X**2
        
        #Find Boiling pressure drop griendient  
        if dpdz_g*phi_g_square > dpdz_f*phi_f_square:
            dpdz=dpdz_g*phi_g_square
        else:
            dpdz=dpdz_f*phi_f_square
        
        return dpdz

    def f_1phase_MicroTube(self,G, Dh, h, p, AS, e_D, Phase='Single'):
        """
        This function return the heat transfer coefficient for single phase 
        fluid inside flat plate tube Micro-channel HX
        """
        if Phase=="SatVap":
            AS.update(CP.PQ_INPUTS,p,1.0)
            mu = AS.viscosity() #[Pa-s OR kg/m-s]
            cp = AS.cpmass() #[J/kg-K]
            k = AS.conductivity() #[W/m-K]
            rho = AS.rhomass() #[kg/m^3]
        elif Phase =="SatLiq":
            AS.update(CP.PQ_INPUTS,p,0.0)
            mu = AS.viscosity() #[Pa-s OR kg/m-s]
            cp = AS.cpmass() #[J/kg-K]
            k = AS.conductivity() #[W/m-K]
            rho = AS.rhomass() #[kg/m^3]
        else:
            AS.update(CP.HmassP_INPUTS,h,p)
            mu = AS.viscosity() #[Pa-s OR kg/m-s]
            cp = AS.cpmass() #[J/kg-K]
            k = AS.conductivity() #[W/m-K]
            rho = AS.rhomass() #[kg/m^3]
        
        Pr = cp * mu / k #[-]
        
        Re=G*Dh/mu

        # Friction factor of Churchill (Darcy Friction factor where f_laminar=64/Re)
        A = ((-2.457 * log( (7.0 / Re)**(0.9) + 0.27 * e_D)))**16
        B = (37530.0 / Re)**16
        f = 8.0 * ((8.0/Re)**12.0 + 1.0 / (A + B)**(1.5))**(1/12)
        
        return f

    def h_1phase_MicroTube(self,G, Dh, h, p, AS, e_D, Phase='Single'):
        """
        This function return the friction factor for single phase fluid inside 
        flat plate tube Micro-channel HX
        """
        if Phase=="SatVap":
            AS.update(CP.PQ_INPUTS,p,1.0)
            mu = AS.viscosity() #[Pa-s OR kg/m-s]
            cp = AS.cpmass() #[J/kg-K]
            k = AS.conductivity() #[W/m-K]
            rho = AS.rhomass() #[kg/m^3]
        elif Phase =="SatLiq":
            AS.update(CP.PQ_INPUTS,p,0.0)
            mu = AS.viscosity() #[Pa-s OR kg/m-s]
            cp = AS.cpmass() #[J/kg-K]
            k = AS.conductivity() #[W/m-K]
            rho = AS.rhomass() #[kg/m^3]
        else:
            AS.update(CP.HmassP_INPUTS,h,p)
            mu = AS.viscosity() #[Pa-s OR kg/m-s]
            cp = AS.cpmass() #[J/kg-K]
            k = AS.conductivity() #[W/m-K]
            rho = AS.rhomass() #[kg/m^3]
        
        Pr = cp * mu / k #[-]
        
        Re=G*Dh/mu
        
        # Friction factor of Churchill (Darcy Friction factor where f_laminar=64/Re)
        e_D = 0.0
        A = ((-2.457 * log( (7.0 / Re)**(0.9) + 0.27 * e_D)))**16
        B = (37530.0 / Re)**16
        f = 8.0 * ((8.0/Re)**12.0 + 1.0 / (A + B)**(1.5))**(1/12)
        
        # Heat Transfer coefficient of Gnielinski
        if 3000 < Re < 5*1E6  and 0.5 < Pr <2000: 
        # Heat Transfer coefficient of Gnielinski
            Nu = (f/8)*(Re-1000)*Pr/(1+12.7*sqrt(f/8)*(Pr**(2/3)-1)) #[-]
        elif 0 < Re < 1000:
            # laminar flow with imposed constant heat flux
            Nu = 4.36
        else:
        # Transition, will do linear interpolation of both
            Nu1 = 4.36
            Nu2 = (f / 8) * (Re - 1000.) * Pr / (1 + 12.7 * sqrt(f / 8) * (Pr**(0.66666) - 1)) #[-]
            Nu = Nu1 + (Re - 1000)*((Nu2-Nu1)/(3000-1000))
        
        h = k*Nu/Dh #W/m^2-K
        return h

if __name__ == '__main__':
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 unused import    
    from itertools import product
    AS = CP.AbstractState("HEOS", "R22")
    Correlation = CorrelationsClass()
    x_start = np.linspace(0,1,100)
    x_end = np.linspace(0,1,100)
    combinations = list(product(x_start,x_end))
    points = np.zeros([len(combinations),3])
    list_of_del = []
    for i,(x_start,x_end) in enumerate(combinations):
        if x_start < x_end:
            DP_vals_acc = -Correlation.AccelPressureDrop(x_start, x_end, AS, 2, 250, 250)
            points[i,0] = x_start
            points[i,1] = x_end
            points[i,2] = DP_vals_acc
        else:
            list_of_del.append(i)
    points = np.delete(points,list_of_del,0)
    ind = np.lexsort((points[:,0],points[:,1]))
    points_order_for_x_end = points[ind]
    print("plot shows accelerational pressure drop as f(x) for 0.1 x segments")
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(points[:,0], points[:,1], points[:,2])
    ax.set_xlabel('x start')
    ax.set_ylabel('x end')
    ax.set_zlabel('dpdz')
    plt.show()
