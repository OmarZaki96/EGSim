from __future__ import division, print_function, absolute_import
from math import pi, log, sqrt, exp, cos, sin, tan, atan, acos, asin
from scipy.integrate import quad, quadrature, simps
import numpy as np
import CoolProp as CP
from backend.Functions import get_2phase_HTC_ranges, get_2phase_HTC_corr, get_2phase_DP_ranges, get_2phase_DP_corr

machine_eps = np.finfo(float).eps

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
        self.Selected_2phase_HTC = False
        self.Selected_2phase_DP = False
        self.HTC_2phase_corr_names = [
                                      "",
                                      "Shah (Condensation)",
                                      "Shah (Evaporation)",
                                      "Kandlikar",
                                      "Olivier",
                                      "",
                                      "Cavallini",
                                      "Dobson-Chato",
                                      "Rollmann",
                                      "",
                                      "Wu",
                                      "Chen (7.14 mm)",
                                      "Chen (8.8 mm)",
                                      "Wongsangam",
                                      "Gungor-Winterton",
                                      "Koyama",
                                      ]

        self.DP_2phase_corr_names = [
                                      "",
                                      "Lockhart-Martinelli",
                                      "Olivier",
                                      "Souza",
                                      "Radermacher",
                                      "Chisholm",
                                      "Friedel",
                                      "Choi",
                                      "Rollmann",
                                      "Koyama",
                                      "Wu",
                                      ]

        self.HTC_1phase_corr_names = [
                                      "",
                                      "Gnielinski",
                                      "Carnavos",
                                      "Copetti",
                                      ]

        self.DP_1phase_corr_names = [
                                      "",
                                      "Churchill",
                                      "Carnavos",
                                      "Copetti",
                                      "Haaland",
                                      ]
        
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
        # get some necessary properties
        self.AS = AS
        self.P = float(P)
        self.q_flux = float(q_flux)
        self.mdot_r = float(mdot_r)
        self.A_segment = float(A_r)
        self.mode = mode
        self.L = A_r / geometry.inner_circum
        self.phase = phase
        self.G_r = float(self.mdot_r) / float(geometry.A_CS)
        if phase == '1phase': # if 1phase is chosen
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
        else: #2phase is chosen
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
        self.ref = "&".join(AS.fluid_names())
        self.OD = float(geometry.OD)
        self.Tubes_type = geometry.Tubes_type
        if self.Tubes_type == 'Smooth':
            self.ID = float(geometry.ID)
            self.Dh = float(geometry.Dh)
            self.e_D = float(geometry.e_D)
        elif self.Tubes_type == 'Microfin': # microfin tube
            # area calculations
            if not hasattr(self,'Afa'):
                self.t = float(geometry.t)
                t = self.t # tube thickness
                self.e = float(geometry.e)
                e = self.e # fin height
                self.d = float(geometry.d)
                d = self.d # fin base width
                self.w = float(geometry.w)
                w = self.w # fin tip width
                self.n = float(geometry.n)
                n = self.n # number of fins per tube
                Do = self.OD # tube outside diameter
                self.ID = Do - 2 * (t-e) # tube inside diameter
                Di = self.ID
                self.FD = Do - 2 * t # tube fin diameter
                FD = self.FD
                self.beta = geometry.beta*pi/180
                beta = self.beta # helix angle in radians
                self.A_fin = (w+d) / 2 * e # signle fin area
                A_fin = self.A_fin
                self.Afa = pi / 4 * pow(Di, 2) - n * A_fin # actual flow area
                Afa = self.Afa
                self.Afn = pi/4*pow(Di, 2) # nominal flow area
                self.Afc = pi/4*pow(FD, 2) # core flow area
                self.An = pi * Di # nominal heat transfer area
                self.Ac = pi * FD # core heat transfer area
                self.side = pow(pow((d-w)/2, 2)+pow(e, 2), 0.5)
                
                side = self.side # side length of fin
                self.Aa = (pi * Di + (2 * side + w - d) * n) / cos(beta)
                # theta = 2 * asin(d / Di)
                # self.Aa = ((side * 2 + w) * n + (2 * pi - n * theta) * Di / 2) / cos(beta)
                Aa = self.Aa # actual heat transfer area
                self.Dh = 4 * Afa / Aa # hydraulic diameter of tube
                self.gama = geometry.gama * pi / 180
                self.Deq = sqrt(Afa / (pi / 4))
                self.pitch = pi * Di / n # fin pitch
        else:
            raise AttributeError("Please Choose correct tube type")
            
        AS.update(CP.HmassP_INPUTS,self.h,self.P)
        self.T = float(AS.T())
        
        # choosing correlation by setting number
        if (not self.imposed_h_2phase) and (not self.Selected_2phase_HTC):
            if not hasattr(self,"HTC_2phase_ranges"):
                self.HTC_2phase_ranges = get_2phase_HTC_ranges()
            if self.Tubes_type == "Smooth":
                tube_type = 1
            elif self.Tubes_type == "Microfin":
                tube_type = 2
            if mode == "heater":
                mode_id = 2
            elif mode == "cooler":
                mode_id = 1
            self.HTC_2phase_corr_id = get_2phase_HTC_corr(self.P,self.G_r,self.ID,tube_type,mode_id,AS,self.HTC_2phase_ranges)
            self.Selected_2phase_HTC = True

        if (not self.imposed_dPdz_f_2phase) and (not self.Selected_2phase_DP):
            if not hasattr(self,"DP_2phase_ranges"):
                self.DP_2phase_ranges = get_2phase_DP_ranges()
            if self.Tubes_type == "Smooth":
                tube_type = 1
            elif self.Tubes_type == "Microfin":
                tube_type = 2
            if mode == "heater":
                mode_id = 2
            elif mode == "cooler":
                mode_id = 1
            self.DP_2phase_corr_id = get_2phase_DP_corr(self.P,self.G_r,self.ID,tube_type,mode_id,AS,self.DP_2phase_ranges)
            self.Selected_2phase_DP = True
        
        if self.phase == '1phase':
            if self.Tubes_type == 'Smooth':
                if not self.imposed_dPdz_f_subcool:
                    # options: 1, 4
                    self.dPdz_f_corr_subcool = 1
                if not self.imposed_dPdz_f_superheat:
                    # options: 1, 4
                    self.dPdz_f_corr_superheat = 1
                if not self.imposed_h_subcool:
                    # options: 1
                    self.h_corr_subcool = 1
                if not self.imposed_h_superheat:
                    # options: 1
                    self.h_corr_superheat = 1
                
            elif self.Tubes_type == 'Microfin':
                if not self.imposed_dPdz_f_subcool:
                    # options: 2, 3
                    self.dPdz_f_corr_subcool = 2
                if not self.imposed_dPdz_f_superheat:
                    # options: 2, 3
                    self.dPdz_f_corr_superheat = 2
                if not self.imposed_h_subcool:
                    # options: 2, 3
                    self.h_corr_subcool = 2
                if not self.imposed_h_superheat:
                    # options: 2, 3
                    self.h_corr_superheat = 2
                
        elif self.phase == '2phase':
            if mode == 'heater':
                if self.Tubes_type == 'Smooth':
                    if self.ref != None:
                        if not self.imposed_dPdz_f_2phase:
                            # options: 1, 3, 4, 5, 6
                            self.dPdz_f_corr_2phase = self.DP_2phase_corr_id
                        if not self.imposed_dP_a:
                            # options: 1, 2, 3
                            self.dP_a_corr = 1
                        if not self.imposed_h_2phase:
                            # options: 1, 6, 7
                            self.h_corr_2phase = self.HTC_2phase_corr_id
                        if not self.imposed_rho_2phase:
                            # options: 1, 2, 3
                            self.rho_2phase_corr = 1
            
                elif self.Tubes_type == 'Microfin':
                    if self.ref != None:
                        if not self.imposed_dPdz_f_2phase:
                            # options: 2
                            self.dPdz_f_corr_2phase = self.DP_2phase_corr_id
                        if not self.imposed_dP_a:
                            # options: 1, 2, 3
                            self.dP_a_corr = 1
                        if not self.imposed_h_2phase:
                            # options: 4, 15
                            self.h_corr_2phase = self.HTC_2phase_corr_id
                        if not self.imposed_rho_2phase:
                            # options: 1, 2, 3
                            self.rho_2phase_corr = 1
                                                    
            elif mode == 'cooler':
                if self.Tubes_type == 'Smooth':
                    if self.ref != None:
                        if not self.imposed_dPdz_f_2phase:
                            # options: 1, 3, 4, 5, 6
                            self.dPdz_f_corr_2phase = self.DP_2phase_corr_id
                        if not self.imposed_dP_a:
                            # options: 1, 2, 3
                            self.dP_a_corr = 1
                        if not self.imposed_h_2phase:
                            # options: 2, 3
                            self.h_corr_2phase = self.HTC_2phase_corr_id
                        if not self.imposed_rho_2phase:
                            # options: 1, 2, 3
                            self.rho_2phase_corr = 1
                        
                elif self.Tubes_type == 'Microfin':
                    if self.ref != None:
                        if not self.imposed_dPdz_f_2phase:
                            # options: 7, 8
                            self.dPdz_f_corr_2phase = self.DP_2phase_corr_id
                        if not self.imposed_dP_a:
                            # options: 1, 2, 3
                            self.dP_a_corr = 1
                        if not self.imposed_h_2phase:
                            # options: 5, 8, 9, 10, 11, 12, 13
                            self.h_corr_2phase = self.HTC_2phase_corr_id
                        if not self.imposed_rho_2phase:
                            # options: 1, 2, 3
                            self.rho_2phase_corr = 1
                else:
                    raise
            else:
                raise
        else:
            raise
            
    # the set of functions following is used to impose a certain correlation
    def impose_h_subcool(self,h):
        self.imposed_h_subcool = True
        self.h_corr_subcool = h

    def impose_h_superheat(self,h):
        self.imposed_h_superheat = True
        self.h_corr_superheat = h
        
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
                ''' Calculate Single-phase h using Gnielinski or laminar h or 
                interpolate between them in transition '''
                h = self.Gnielinski_1phase_Tube(self.mdot_r, self.ID, self.e_D, self.h, self.P, self.AS)
                return h
            
            elif self.h_corr_superheat == 2:
                '''calculate single phase h for microfin tubes using carnavos'''
                h =  self.Carnavos_single_h(self.AS,self.G_r,self.P,self.h,self.OD,self.n,self.e,self.t,self.d,self.w,self.beta,self.Afa,self.Afc,self.An,self.Aa,self.ID,self.Dh)
                return h
                            
            elif self.h_corr_superheat == 3:
                '''calculate single phase h for microfin tubes using Copetti'''
                h =  self.Copetti_single_h(self.AS,self.G_r,self.P,self.h,self.OD,self.n,self.e,self.t,self.d,self.w,self.beta, self.Deq)
                return h
            else:
                raise
        elif self.phase_type == "liquid":
            if self.h_corr_subcool == 1:
                ''' Calculate Single-phase h using Gnielinski or laminar h or 
                interpolate between them in transition '''
                h = self.Gnielinski_1phase_Tube(self.mdot_r, self.ID, self.e_D, self.h, self.P, self.AS)
                return h
            
            elif self.h_corr_subcool == 2:
                '''calculate single phase h for microfin tubes using carnavos'''
                h =  self.Carnavos_single_h(self.AS,self.G_r,self.P,self.h,self.OD,self.n,self.e,self.t,self.d,self.w,self.beta,self.Afa,self.Afc,self.An,self.Aa,self.ID,self.Dh)
                return h
                            
            elif self.h_corr_subcool == 3:
                '''calculate single phase h for microfin tubes using Copetti'''
                h =  self.Copetti_single_h(self.AS,self.G_r,self.P,self.h,self.OD,self.n,self.e,self.t,self.d,self.w,self.beta, self.Deq)
                return h
            else:
                raise
    
    def calculate_dPdz_f_1phase(self):
        if self.phase_type == "vapor":
            if self.dPdz_f_corr_superheat == 1:
                ''' Single-Phase pressure drop for smooth tubes using Churchill '''
                f = self.Churchill_1phase_Tube(self.mdot_r, self.ID, self.e_D, self.h, self.P, self.AS)
                self.AS.update(CP.HmassP_INPUTS, self.h, self.P)
                rho_r = self.AS.rhomass()
                v_r = 1/rho_r
                dpdz=-f*v_r*self.G_r**2/(2*self.ID) #Pressure gradient
                return dpdz
            
            elif self.dPdz_f_corr_superheat == 2:
                ''' Single phase pressure drop for microfin tubes using 
                Carnavos '''
                f =  self.Carnavos_single_f(self.AS,self.G_r,self.P,self.h,self.OD,self.n,self.e,self.t,self.d,self.w,self.beta, self.Afa,self.Afn,self.ID,self.Dh)
                self.AS.update(CP.HmassP_INPUTS, self.h, self.P)
                rho_r = self.AS.rhomass()
                v_r = 1 / rho_r
                G_r = self.G_r * self.Afa / self.Afn
                dpdz=-f*v_r*G_r**2/(2*self.Dh) #Pressure gradient
                return dpdz
                    
            elif self.dPdz_f_corr_superheat == 3:
                ''' Single phase pressure drop for microfin tubes using Copetti '''
                f =  self.Copetti_single_f(self.AS,self.G_r,self.P,self.h,self.OD,self.n,self.e,self.t,self.d,self.w,self.beta,self.Deq)
                self.AS.update(CP.HmassP_INPUTS, self.h, self.P)
                rho_r = self.AS.rhomass()
                v_r = 1/rho_r
                dpdz_r=-f*v_r*self.G_r**2/(2*self.Deq) #Pressure gradient
                return dpdz_r
    
            elif self.dPdz_f_corr_superheat == 4:
                ''' Single-Phase pressure drop for smooth tubes using Haaland '''
                f = self.Haaland_1phase_Tube(self.mdot_r, self.ID, self.e_D, self.h, self.P, self.AS)
                self.AS.update(CP.HmassP_INPUTS, self.h, self.P)
                rho_r = self.AS.rhomass()
                v_r = 1/rho_r
                dpdz=-f*v_r*self.G_r**2/(2*self.ID) #Pressure gradient
                return dpdz
            else:
                raise
        elif self.phase_type == "liquid":
            if self.dPdz_f_corr_subcool == 1:
                ''' Single-Phase pressure drop for smooth tubes using Churchill '''
                f = self.Churchill_1phase_Tube(self.mdot_r, self.ID, self.e_D, self.h, self.P, self.AS)
                self.AS.update(CP.HmassP_INPUTS, self.h, self.P)
                rho_r = self.AS.rhomass()
                v_r = 1/rho_r
                dpdz=-f*v_r*self.G_r**2/(2*self.ID) #Pressure gradient
                
                return dpdz
            
            elif self.dPdz_f_corr_subcool == 2:
                ''' Single phase pressure drop for microfin tubes using 
                Carnavos '''
                f =  self.Carnavos_single_f(self.AS,self.G_r,self.P,self.h,self.OD,self.n,self.e,self.t,self.d,self.w,self.beta, self.Afa,self.Afn,self.ID,self.Dh)
                self.AS.update(CP.HmassP_INPUTS, self.h, self.P)
                rho_r = self.AS.rhomass()
                v_r = 1 / rho_r
                G_r = self.G_r * self.Afa / self.Afn
                dpdz=-f*v_r*G_r**2/(2*self.Dh) #Pressure gradient
                return dpdz
                    
            elif self.dPdz_f_corr_subcool == 3:
                ''' Single phase pressure drop for microfin tubes using Copetti '''
                f =  self.Copetti_single_f(self.AS,self.G_r,self.P,self.h,self.OD,self.n,self.e,self.t,self.d,self.w,self.beta,self.Deq)
                self.AS.update(CP.HmassP_INPUTS, self.h, self.P)
                rho_r = self.AS.rhomass()
                v_r = 1/rho_r
                dpdz_r=-f*v_r*self.G_r**2/(2*self.Deq) #Pressure gradient
                return dpdz_r
    
            elif self.dPdz_f_corr_subcool == 4:
                ''' Single-Phase pressure drop for smooth tubes using Haaland '''
                f = self.Haaland_1phase_Tube(self.mdot_r, self.ID, self.e_D, self.h, self.P, self.AS)
                self.AS.update(CP.HmassP_INPUTS, self.h, self.P)
                rho_r = self.AS.rhomass()
                v_r = 1/rho_r
                dpdz=-f*v_r*self.G_r**2/(2*self.ID) #Pressure gradient
                return dpdz
            else:
                raise

    def calculate_h_2phase(self):
                
        if self.h_corr_2phase == 1:
            ''' calculate two-phase h condensation in smooth tubes using shah '''
            self.AS.update(CP.PQ_INPUTS,self.P,0.0)
            Tbubble = self.AS.T()
            self.AS.update(CP.PQ_INPUTS,self.P,1.0)
            Tdew = self.AS.T()
            if self.x == 1:
                x_in = 0.999
            else:
                x_in = self.x
            if self.x_out == 1:
                x_out = 0.999
            elif self.x_out == 0:
                x_out = 0.001
            else:
                x_out = self.x_out
                
            h = self.ShahCondensation_Average(min(x_in,x_out),max(x_in,x_out),self.AS,self.G_r,self.ID,self.P,Tbubble,Tdew)
            return h
        
        elif self.h_corr_2phase == 2:
            ''' calculate two-phase h evaporation in smooth tubes using shah '''
            self.AS.update(CP.PQ_INPUTS,self.P,0.0)
            Tbubble = self.AS.T()
            self.AS.update(CP.PQ_INPUTS,self.P,1.0)
            Tdew = self.AS.T()
            q_flux = self.q_flux
            h = self.ShahEvaporation_Average(min(self.x,self.x_out),max(self.x,self.x_out),self.AS,self.G_r,self.ID,self.P,q_flux,Tbubble,Tdew)
            return h
        
        elif self.h_corr_2phase == 3:
            ''' calculate two-phase h evaporation in smooth tubes using Kandlikar '''
            self.AS.update(CP.PQ_INPUTS,self.P,0.0)
            Tbubble = self.AS.T()
            self.AS.update(CP.PQ_INPUTS,self.P,1.0)
            Tdew = self.AS.T()
            q_flux = self.q_flux
            h = self.KandlikarEvaporation_average(min(self.x,self.x_out),max(self.x,self.x_out),self.AS,self.G_r,self.ID,self.P,q_flux,Tbubble,Tdew)
            return h
                
        elif self.h_corr_2phase == 4:
            '''calculate h condensation in microfin tubes using Olivier'''
            self.AS.update(CP.PQ_INPUTS,self.P,0.0)
            Tbubble = self.AS.T()
            self.AS.update(CP.PQ_INPUTS,self.P,1.0)
            Tdew = self.AS.T()
            h = self.Olivier_Condensation_h_average(self.AS,self.G_r,self.P,Tbubble,Tdew,min(self.x,self.x_out),max(self.x,self.x_out),self.OD,self.n,self.e,self.t,self.d,self.w,self.beta, self.ID, self.gama)
            return h
        
        elif self.h_corr_2phase == 5:
            ''' calculate two-phase h evaporation in microfin tubes using shah '''
            self.AS.update(CP.PQ_INPUTS,self.P,0.0)
            Tbubble = self.AS.T()
            self.AS.update(CP.PQ_INPUTS,self.P,1.0)
            Tdew = self.AS.T()
            q_flux = self.q_flux
            h = self.ShahEvaporation_Average(min(self.x,self.x_out),max(self.x,self.x_out),self.AS,self.G_r,self.ID,self.P,q_flux,Tbubble,Tdew)
            return h

        elif self.h_corr_2phase == 6:
            '''calculate condensation h for smooth tubes using Cavallini'''
            self.AS.update(CP.PQ_INPUTS,self.P,0.0)
            Tbubble = self.AS.T()
            self.AS.update(CP.PQ_INPUTS,self.P,1.0)
            Tdew = self.AS.T()
            if self.x > 0.999:
                x = 0.999
            elif self.x == 0:
                x = 0.001
            else:
                x = self.x
            if self.x_out > 0.999:
                x_out = 0.999
            elif self.x_out == 0:
                x_out = 0.001
            else:
                x_out = self.x_out
                
            h = self.CavalliniCondensation_Average(min(x,x_out),max(x,x_out),self.AS,self.G_r,self.ID,self.P,Tbubble,Tdew,self.q_flux)
            return h
        
        elif self.h_corr_2phase == 7:
            '''calculate condensation h for smooth tubes using Dobson-Chato'''
            self.AS.update(CP.PQ_INPUTS,self.P,0.0)
            Tbubble = self.AS.T()
            self.AS.update(CP.PQ_INPUTS,self.P,1.0)
            Tdew = self.AS.T()
            if self.x > 0.99:
                x = 0.99
            else:
                x = self.x
            if self.x_out > 0.99:
                x_out = 0.99
            else:
                x_out = self.x_out
            h = self.DobsonChatoCondensation_Average(min(x,x_out),max(x,x_out),self.AS,self.G_r,self.ID,self.P,Tbubble,Tdew,self.q_flux)

            return h
        
        elif self.h_corr_2phase == 8:
            '''calculate evaporation h for microfin tubes using Rollmann'''
            self.AS.update(CP.PQ_INPUTS,self.P,0.0)
            Tbubble = self.AS.T()
            self.AS.update(CP.PQ_INPUTS,self.P,1.0)
            Tdew = self.AS.T()
            if self.x == 0:
                x_in = np.finfo(float).eps
            else:
                x_in = self.x
            x = (x_in+self.x_out)/2
            h = self.Rollmann_2016_h(self.AS, self.G_r, Tbubble, Tdew, self.ID, self.q_flux, x, self.Ac, self.Aa)
            return h
    
        elif self.h_corr_2phase == 9:
            ''' calculate two-phase h evaporation in microfin tubes using Kandlikar '''
            self.AS.update(CP.PQ_INPUTS,self.P,0.0)
            Tbubble = self.AS.T()
            self.AS.update(CP.PQ_INPUTS,self.P,1.0)
            Tdew = self.AS.T()
            q_flux = self.q_flux
            h = self.KandlikarEvaporation_average(min(self.x,self.x_out),max(self.x,self.x_out),self.AS,self.G_r,self.ID,self.P,q_flux,Tbubble,Tdew)
            return h

        elif self.h_corr_2phase == 10:
            ''' calculate two-phase h evaporation in microfin tubes using Wu'''
            self.AS.update(CP.PQ_INPUTS,self.P,0.0)
            Tbubble = self.AS.T()
            self.AS.update(CP.PQ_INPUTS,self.P,1.0)
            Tdew = self.AS.T()
            q_flux = self.q_flux
            
            if self.x > 0.9999:
                x = 0.9999
            else:
                x = self.x
            if self.x_out > 0.9999:
                x_out = 0.9999
            else:
                x_out = self.x_out

            h = self.Wu_2013_h_average(self.AS, self.G_r, Tbubble, Tdew, self.Afa, self.Deq, self.e, self.pitch, self.beta, self.An, self.Ac, min(x, x_out), max(x, x_out), q_flux)
            return h

        elif self.h_corr_2phase == 11:
            ''' calculate two-phase h evaporation in microfin tubes using Chen for 7.14 mm internal diameter tubes'''
            self.AS.update(CP.PQ_INPUTS,self.P,0.0)
            Tbubble = self.AS.T()
            self.AS.update(CP.PQ_INPUTS,self.P,1.0)
            Tdew = self.AS.T()
            if self.x == 0:
                x_in = np.finfo(float).eps
            else:
                x_in = self.x
            x = (x_in+self.x_out)/2
            h = self.chen_2018_h_7_14mm(self.AS, self.G_r, Tbubble, Tdew, self.Dh, self.ID, self.Ac, self.Aa, x)
            return h

        elif self.h_corr_2phase == 12:
            ''' calculate two-phase h evaporation in microfin tubes using Chen for 8.8 mm internal diameter tubes'''
            self.AS.update(CP.PQ_INPUTS,self.P,0.0)
            Tbubble = self.AS.T()
            self.AS.update(CP.PQ_INPUTS,self.P,1.0)
            Tdew = self.AS.T()
            if self.x == 0:
                x_in = np.finfo(float).eps
            else:
                x_in = self.x
            x = (x_in+self.x_out)/2
            h = self.chen_2018_h_8_8mm(self.AS, self.G_r, Tbubble, Tdew, self.Dh, self.ID, self.Ac, self.Aa, x)
            return h

        elif self.h_corr_2phase == 13:
            '''calculate evaporation h for microfin tubes using Wongsangam'''
            self.AS.update(CP.PQ_INPUTS,self.P,0.0)
            Tbubble = self.AS.T()
            self.AS.update(CP.PQ_INPUTS,self.P,1.0)
            Tdew = self.AS.T()
            if self.x == 0:
                x_in = np.finfo(float).eps
            else:
                x_in = self.x
            x = (x_in+self.x_out)/2
            h = self.Wongsangam_2004_h(self.AS, self.G_r, Tbubble, Tdew, self.ID, self.q_flux, x, self.Ac, self.Aa)
            return h

        elif self.h_corr_2phase == 14:
            ''' calculate two-phase h evaporation in Smooth tubes using Gungor-Winterton '''
            self.AS.update(CP.PQ_INPUTS,self.P,0.0)
            Tbubble = self.AS.T()
            self.AS.update(CP.PQ_INPUTS,self.P,1.0)
            Tdew = self.AS.T()
            q_flux = self.q_flux
            h = self.Gungor_Winterton_average(min(self.x,self.x_out),max(self.x,self.x_out),self.AS,self.G_r,self.ID,self.P,q_flux,Tbubble,Tdew)
            return h

        elif self.h_corr_2phase == 15:
            ''' calculate two-phase h condensation in Microfin tubes using Koyama '''
            self.AS.update(CP.PQ_INPUTS,self.P,0.0)
            Tbubble = self.AS.T()
            self.AS.update(CP.PQ_INPUTS,self.P,1.0)
            Tdew = self.AS.T()
            q_flux = self.q_flux
            G_r = self.G_r * self.Afa / self.Afn
            if self.x == 0:
                x_in = 0.001
            else:
                x_in = self.x
            if self.x_out == 0:
                x_out = 0.001
            else:
                x_out = self.x_out
                
            h = self.Koyama2006_Condensation_h(min(x_in,x_out),max(x_in,x_out),self.AS,G_r,self.Deq,self.P,Tbubble,Tdew,self.beta,self.Afa,self.Afn,self.Aa,self.An,self.pitch,self.d,self.q_flux)
            return h

    def calculate_dPdz_f_2phase(self):        
        if self.dPdz_f_corr_2phase == 1:
            '''two-phase pressure drop using LockhartMartinelli'''
            
            self.AS.update(CP.PQ_INPUTS,self.P,0.0)
            Tbubble = self.AS.T()
            self.AS.update(CP.PQ_INPUTS,self.P,1.0)
            Tdew = self.AS.T()
            dpdz = -self.LMPressureGradientAvg(min(self.x_out,self.x),max(self.x_out,self.x),self.AS,self.G_r,self.ID,Tbubble,Tdew)
            return dpdz
        
        elif self.dPdz_f_corr_2phase == 2:
            '''calculate dpdz condensation in microfin tubes using Olivier'''
            self.AS.update(CP.PQ_INPUTS,self.P,0.0)
            Tbubble = self.AS.T()
            self.AS.update(CP.PQ_INPUTS,self.P,1.0)
            Tdew = self.AS.T()
            dpdz = -self.Olivier_Condensation_dpdz_average(self.AS,self.G_r,self.P,Tbubble,Tdew,min(self.x,self.x_out),max(self.x,self.x_out),self.OD,self.n,self.e,self.t,self.d,self.w,self.beta,self.ID,self.Afa)
            return dpdz
        
        elif self.dPdz_f_corr_2phase == 3:
            '''two-phase pressure drop using Souza'''
            
            self.AS.update(CP.PQ_INPUTS,self.P,0.0)
            Tbubble = self.AS.T()
            self.AS.update(CP.PQ_INPUTS,self.P,1.0)
            Tdew = self.AS.T()
            dpdz = -self.SouzaPressureGradientAvg(min(self.x_out,self.x),max(self.x_out,self.x),self.AS,self.G_r,self.ID,Tbubble,Tdew)
            return dpdz
        
        elif self.dPdz_f_corr_2phase == 4:
            '''two-phase pressure drop using Radermacher'''
            
            self.AS.update(CP.PQ_INPUTS,self.P,0.0)
            Tbubble = self.AS.T()
            self.AS.update(CP.PQ_INPUTS,self.P,1.0)
            Tdew = self.AS.T()
            dpdz = -self.RadermacherPressureGradientAvg(min(self.x_out,self.x),max(self.x_out,self.x),self.AS,self.G_r,self.ID,Tbubble,Tdew)
            return dpdz

        elif self.dPdz_f_corr_2phase == 5:
            '''two-phase pressure drop using Chisholm'''
            
            self.AS.update(CP.PQ_INPUTS,self.P,0.0)
            Tbubble = self.AS.T()
            self.AS.update(CP.PQ_INPUTS,self.P,1.0)
            Tdew = self.AS.T()
            dpdz = -self.ChisholmPressureGradientAvg(min(self.x_out,self.x),max(self.x_out,self.x),self.AS,self.G_r,self.ID,Tbubble,Tdew)
            return dpdz

        elif self.dPdz_f_corr_2phase == 6:
            '''two-phase pressure drop using Friedel'''
            
            self.AS.update(CP.PQ_INPUTS,self.P,0.0)
            Tbubble = self.AS.T()
            self.AS.update(CP.PQ_INPUTS,self.P,1.0)
            Tdew = self.AS.T()
            dpdz = -self.FriedelPressureGradientAvg(min(self.x_out,self.x),max(self.x_out,self.x),self.AS,self.G_r,self.ID,Tbubble,Tdew)
            return dpdz

        elif self.dPdz_f_corr_2phase == 7:
            '''calculate dpdz evaporation in microfin tubes using Choi'''
            dpdz = -self.Choi_1999_dpdz(self.AS,self.G_r,self.P,self.L,min(self.x,self.x_out),max(self.x,self.x_out),self.ID)
            return dpdz

        elif self.dPdz_f_corr_2phase == 8:
            '''calculate dpdz evaporation in microfin tubes using Rollmann'''
            dpdz = -self.Rollmann_2016_dpdz(self.AS,self.G_r,self.P,self.L,self.ID,self.Afa,self.Aa,min(self.x,self.x_out),max(self.x,self.x_out))
            return dpdz

        elif self.dPdz_f_corr_2phase == 9:
            '''calculate dpdz condensation in microfin tubes using Koyama'''
            self.AS.update(CP.PQ_INPUTS,self.P,0.0)
            Tbubble = self.AS.T()
            self.AS.update(CP.PQ_INPUTS,self.P,1.0)
            Tdew = self.AS.T()
            dpdz = -self.Koyama2006_Condensation_dpdz(min(self.x,self.x_out),max(self.x,self.x_out),self.AS,self.G_r,self.Deq,self.P,Tbubble,Tdew,self.beta,self.Afa,self.Afn,self.Aa,self.An)
            return dpdz

        elif self.dPdz_f_corr_2phase == 10:
            '''calculate dpdz evaporation in microfin tubes using Wu'''
            self.AS.update(CP.PQ_INPUTS,self.P,0.0)
            Tbubble = self.AS.T()
            self.AS.update(CP.PQ_INPUTS,self.P,1.0)
            Tdew = self.AS.T()
            dpdz = -self.Wu_2013_dpdz_average(self.AS, self.G_r, Tbubble, Tdew, self.ID, self.e, self.beta, min(self.x,self.x_out), max(self.x,self.x_out))
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
            DP_accel = self.AccelPressureDrop(min(self.x_out,self.x),max(self.x_out,self.x),self.AS,self.G_r,Tbubble,Tdew,slipModel='Premoli',D = self.ID)
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
            S = self.Premoli((xmin+xmax)/2, AS, self.G_r, self.ID, Tbubble, Tdew, rhof,rhog)
        else:
            raise ValueError(
                "slipModel must be either 'Zivi' or 'Homogeneous' or 'Premoli'")
        C = S*rhog/rhof

        if xmin+5*machine_eps < 0 or xmax-5*machine_eps > 1.0:
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

    def LMPressureGradientAvg(self,x_min, x_max, AS, G, D, Tbubble, Tdew, C=None,satTransport=None):
        """
        Returns the average pressure gradient between qualities of x_min and x_max.

        To obtain the pressure gradient for a given value of x, pass it in as x_min and x_max

        Required parameters:
        * x_min : The minimum quality for the range [-]
        * x_max : The maximum quality for the range [-]
        * AS : AbstractState with the refrigerant name and backend
        * G : Mass flux [kg/m^2/s]
        * D : Diameter of tube [m]
        * Tbubble : Bubblepoint temperature of refrigerant [K]
        * Tdew : Dewpoint temperature of refrigerant [K]

        Optional parameters:
        * C : The coefficient in the pressure drop
        * satTransport : A dictionary with the keys 'mu_f','mu_g,'v_f','v_g' for the saturation properties.  So they can be calculated once and passed in for a slight improvement in efficiency 
        """
        def LMFunc(x):
            dpdz = self.LockhartMartinelli(AS, G, D, x, Tbubble, Tdew,C,satTransport)
            return dpdz

        # Use Simpson's Rule to calculate the average pressure gradient
        # Can't use adapative quadrature since function is not sufficiently smooth
        # Not clear why not sufficiently smooth at x>0.9
        if abs(x_max-x_min) < 100*machine_eps:
            return LMFunc(x_min)
        else:
            # Calculate the tranport properties once
            satTransport = {}
            AS.update(CP.QT_INPUTS, 0.0, Tbubble)
            satTransport['v_f'] = 1/AS.rhomass()  # [m^3/kg]
            satTransport['mu_f'] = AS.viscosity()  # [Pa-s]
            AS.update(CP.QT_INPUTS, 1.0, Tdew)
            satTransport['v_g'] = 1/AS.rhomass()  # [m^3/kg]
            satTransport['mu_g'] = AS.viscosity()  # [Pa-s]

            xx = np.linspace(x_min, x_max, 30)
            DP = np.zeros_like(xx)
            for i in range(len(xx)):
                DP[i] = LMFunc(xx[i])
            return simps(DP, xx)/(x_max-x_min)

    def LockhartMartinelli(self, AS, G, D, x, Tbubble, Tdew, C=None, satTransport=None):
        x = float(x)
        if satTransport == None:
            # Calculate Necessary saturation properties
            AS.update(CP.QT_INPUTS, 0.0, Tbubble)
            v_f = 1/AS.rhomass()  # [m^3/kg]
            mu_f = AS.viscosity()  # [Pa-s]
            AS.update(CP.QT_INPUTS, 1.0, Tdew)
            v_g = 1/AS.rhomass()  # [m^3/kg]
            mu_g = AS.viscosity()  # [Pa-s]
        else:
            # Pull out of the dictionary
            v_f = satTransport['v_f']
            v_g = satTransport['v_g']
            mu_f = satTransport['mu_f']
            mu_g = satTransport['mu_g']
        
        # 1. Find the Reynolds Number for each phase based on the actual flow rate of the individual phase
        Re_g = G*x*D/mu_g
        Re_f = G*(1-x)*D/mu_f

        # 2. Friction factor for each phase
        if x == 1:  # No liquid
            f_f = 0  # Just to be ok until next step
        elif Re_f < 1000:  # Laminar
            f_f = 16/Re_f
        elif Re_f > 2000:  # Fully-Turbulent
            f_f = 0.079/(Re_f**0.25)
        else:  # Mixed
            # Weighting factor
            w = (Re_f-1000)/(2000-1000)
            # Linear interpolation between laminar and turbulent
            f_f = (1-w)*16.0/Re_f+w*0.079/(Re_f**0.25)
        
        if x == 0:  # No gas
            f_g = 0  # Just to be ok until next step
        elif Re_g < 1000:  # Laminar
            f_g = 16.0/Re_g
        elif Re_g > 2000:  # Fully-Turbulent
            f_g = 0.079/(Re_g**0.25)
        else:  # Mixed
            # Weighting factor
            w = (Re_g-1000)/(2000-1000)
            # Linear interpolation between laminar and turbulent
            f_g = (1-w)*16.0/Re_g+w*0.079/(Re_g**0.25)

        # 3. Frictional pressure drop based on actual flow rate of each phase
        dpdz_f = 2*f_f*G**2*(1-x)**2*v_f/D
        dpdz_g = 2*f_g*G**2*x**2*v_g/D

        if x <= 0.001:
            # Entirely liquid
            dpdz = dpdz_f
            return dpdz
        if x >= 0.999:
            # Entirely vapor
            dpdz = dpdz_g
            return dpdz
        
        # 4. Lockhart-Martinelli parameter
        Xtt = pow((1 - x) / x, 0.875) * pow(v_f / v_g, 0.5) * pow(mu_f / mu_g, 0.125)
        
        if Xtt > 1e3:
            Xtt  = sqrt(dpdz_f/dpdz_g)

        # 5. Find the Constant based on the flow Re of each phase
        #    (using 1500 as the transitional Re to ensure continuity)

        # Calculate C if not passed in:
        if C == None:
            if Re_f > 1500 and Re_g > 1500:
                C = 20.0
            elif Re_f < 1500 and Re_g > 1500:
                C = 12.0
            elif Re_f > 1500 and Re_g < 1500:
                C = 10.0
            else:
                C = 5.0

        # 6. Two-phase multipliers for each phase
        phi_f2 = 1+C/Xtt+1/Xtt**2

        # 7. Find gradient
        
        dpdz = dpdz_f*phi_f2
        
        return dpdz

    def SouzaPressureGradientAvg(self,x_min, x_max, AS, G, D, Tbubble, Tdew, C=None,satTransport=None):
        """
        Returns the average pressure gradient between qualities of x_min and x_max.

        To obtain the pressure gradient for a given value of x, pass it in as x_min and x_max

        Required parameters:
        * x_min : The minimum quality for the range [-]
        * x_max : The maximum quality for the range [-]
        * AS : AbstractState with the refrigerant name and backend
        * G : Mass flux [kg/m^2/s]
        * D : Diameter of tube [m]
        * Tbubble : Bubblepoint temperature of refrigerant [K]
        * Tdew : Dewpoint temperature of refrigerant [K]

        """
        def SouzaFunc(x):
            dpdz = self.Souza(AS, G, D, x, Tbubble, Tdew,C,satTransport)
            return dpdz

        # Use Simpson's Rule to calculate the average pressure gradient
        # Can't use adapative quadrature since function is not sufficiently smooth
        # Not clear why not sufficiently smooth at x>0.9
        if abs(x_max-x_min) < 100*machine_eps:
            return SouzaFunc(x_min)
        else:
            # Calculate the tranport properties once
            satTransport = {}
            AS.update(CP.QT_INPUTS, 0.0, Tbubble)
            satTransport['v_f'] = 1/AS.rhomass()  # [m^3/kg]
            satTransport['mu_f'] = AS.viscosity()  # [Pa-s]
            AS.update(CP.QT_INPUTS, 1.0, Tdew)
            satTransport['v_g'] = 1/AS.rhomass()  # [m^3/kg]
            satTransport['mu_g'] = AS.viscosity()  # [Pa-s]

            xx = np.linspace(x_min, x_max, 30)
            DP = np.zeros_like(xx)
            for i in range(len(xx)):
                DP[i] = SouzaFunc(xx[i])
            return simps(DP, xx)/(x_max-x_min)

    def Souza(self, AS, G, D, x, Tbubble, Tdew, C=None, satTransport=None):
        '''from "Pressure Drop During Two-Phase Flow of Refrigerants in 
            Horizontal Smooth Tubes", Souza et al. (1992) '''

        x = float(x)
        if satTransport == None:
            # Calculate Necessary saturation properties
            AS.update(CP.QT_INPUTS, 0.0, Tbubble)
            v_f = 1/AS.rhomass()  # [m^3/kg]
            mu_f = AS.viscosity()  # [Pa-s]
            AS.update(CP.QT_INPUTS, 1.0, Tdew)
            v_g = 1/AS.rhomass()  # [m^3/kg]
            mu_g = AS.viscosity()  # [Pa-s]
        else:
            # Pull out of the dictionary
            v_f = satTransport['v_f']
            v_g = satTransport['v_g']
            mu_f = satTransport['mu_f']
            mu_g = satTransport['mu_g']


        if x == 1:
            Re_g = G * D / mu_g
            if Re_g < 1000:  # Laminar
                f_g = 16.0/Re_g
            elif Re_g > 2000:  # Fully-Turbulent
                f_g = 0.079/(Re_g**0.25)
            else:  # Mixed
                # Weighting factor
                w = (Re_g-1000)/(2000-1000)
                # Linear interpolation between laminar and turbulent
                f_g = (1-w)*16.0/Re_g+w*0.079/(Re_g**0.25)
            dpdz_g = 2 * f_g * pow(G, 2) * v_g / D 
            return dpdz_g
        
        elif x == 0:
            Re_f = G * D / mu_f
            if Re_f < 1000:  # Laminar
                f_f = 16.0/Re_f
            elif Re_f > 2000:  # Fully-Turbulent
                f_f = 0.079/(Re_f**0.25)
            else:  # Mixed
                # Weighting factor
                w = (Re_f-1000)/(2000-1000)
                # Linear interpolation between laminar and turbulent
                f_f = (1-w)*16.0/Re_f+w*0.079/(Re_f**0.25)
            dpdz_f = 2 * f_f * pow(G, 2) * v_f / D
            return dpdz_f
        
        Re_LO = G * D / mu_f
        
        if Re_LO < 1000:  # Laminar
            f_LO = 16.0/Re_LO
        elif Re_LO > 2000:  # Fully-Turbulent
            f_LO = 0.079/(Re_LO**0.25)
        else:  # Mixed
            # Weighting factor
            w = (Re_LO-1000)/(2000-1000)
            # Linear interpolation between laminar and turbulent
            f_LO = (1-w)*16.0/Re_LO+w*0.079/(Re_LO**0.25)
        
        dpdz_LO = 2 * f_LO * pow(G, 2) * v_f / D
        
        Xtt = pow(mu_f / mu_g, 0.125) * pow(v_f / v_g, 0.5) * pow((1 - x) / x, 0.875)
        Fr_f = pow(G, 2) * pow(v_f, 2) / (9.81 * D)
        C1 = 4.172 + 5.48 * Fr_f - 1.564 * pow(Fr_f, 2)
        C2 = 1.773 - 0.169 * Fr_f
        Phi_LO2 = (1.376 + C1 * pow(Xtt, -C2)) * pow(1 - x, 1.75)
        dpdz = Phi_LO2 * dpdz_LO
        return dpdz

    def RadermacherPressureGradientAvg(self,x_min, x_max, AS, G, D, Tbubble, Tdew, C=None,satTransport=None):
        """
        Returns the average pressure gradient between qualities of x_min and x_max.

        To obtain the pressure gradient for a given value of x, pass it in as x_min and x_max

        Required parameters:
        * x_min : The minimum quality for the range [-]
        * x_max : The maximum quality for the range [-]
        * AS : AbstractState with the refrigerant name and backend
        * G : Mass flux [kg/m^2/s]
        * D : Diameter of tube [m]
        * Tbubble : Bubblepoint temperature of refrigerant [K]
        * Tdew : Dewpoint temperature of refrigerant [K]

        """
        def RadermacherFunc(x):
            dpdz = self.Radermacher(AS, G, D, x, Tbubble, Tdew,C,satTransport)
            return dpdz

        # Use Simpson's Rule to calculate the average pressure gradient
        # Can't use adapative quadrature since function is not sufficiently smooth
        # Not clear why not sufficiently smooth at x>0.9
        if abs(x_max-x_min) < 100*machine_eps:
            return RadermacherFunc(x_min)
        else:
            # Calculate the tranport properties once
            satTransport = {}
            AS.update(CP.QT_INPUTS, 0.0, Tbubble)
            satTransport['v_f'] = 1/AS.rhomass()  # [m^3/kg]
            satTransport['mu_f'] = AS.viscosity()  # [Pa-s]
            AS.update(CP.QT_INPUTS, 1.0, Tdew)
            satTransport['v_g'] = 1/AS.rhomass()  # [m^3/kg]
            satTransport['mu_g'] = AS.viscosity()  # [Pa-s]

            xx = np.linspace(x_min, x_max, 30)
            DP = np.zeros_like(xx)
            for i in range(len(xx)):
                DP[i] = RadermacherFunc(xx[i])
            result = simps(DP, xx)/(x_max-x_min)
            return result

    def Radermacher(self, AS, G, D, x, Tbubble, Tdew, C=None, satTransport=None):
        '''from Jung, D. S. and Radermacher, R., 1989, "Prediction of Pressure
            Drop During Horizontal Annular Flow Boiling of Pure and Mixed 
            Refrigerants" International Journal of Heat and Mass Transfer, 
            Vol. 32, pp. 2435-2446. '''

        x = float(x)
        if satTransport == None:
            # Calculate Necessary saturation properties
            AS.update(CP.QT_INPUTS, 0.0, Tbubble)
            v_f = 1/AS.rhomass()  # [m^3/kg]
            mu_f = AS.viscosity()  # [Pa-s]
            AS.update(CP.QT_INPUTS, 1.0, Tdew)
            v_g = 1/AS.rhomass()  # [m^3/kg]
            mu_g = AS.viscosity()  # [Pa-s]
        else:
            # Pull out of the dictionary
            v_f = satTransport['v_f']
            v_g = satTransport['v_g']
            mu_f = satTransport['mu_f']
            mu_g = satTransport['mu_g']


        if x == 1:
            Re_g = G * D / mu_g
            if Re_g < 1000:  # Laminar
                f_g = 16.0/Re_g
            elif Re_g > 2000:  # Fully-Turbulent
                f_g = 0.046/(Re_g**0.2)
            else:  # Mixed
                # Weighting factor
                w = (Re_g-1000)/(2000-1000)
                # Linear interpolation between laminar and turbulent
                f_g = (1-w)*16.0/Re_g+w*0.046/(Re_g**0.2)
            dpdz_g = 2 * f_g * pow(G, 2) * v_g / D 
            return dpdz_g
        
        elif x == 0:
            Re_f = G * D / mu_f
            if Re_f < 1000:  # Laminar
                f_f = 16.0/Re_f
            elif Re_f > 2000:  # Fully-Turbulent
                f_f = 0.046/(Re_f**0.2)
            else:  # Mixed
                # Weighting factor
                w = (Re_f-1000)/(2000-1000)
                # Linear interpolation between laminar and turbulent
                f_f = (1-w)*16.0/Re_f+w*0.046/(Re_f**0.2)
            dpdz_f = 2 * f_f * pow(G, 2) * v_f / D
            return dpdz_f

        Re_LO = G * D / mu_f
        
        if Re_LO < 1000:  # Laminar
            f_LO = 16.0/Re_LO
        elif Re_LO > 2000:  # Fully-Turbulent
            f_LO = 0.046/(Re_LO**0.2)
        else:  # Mixed
            # Weighting factor
            w = (Re_LO-1000)/(2000-1000)
            # Linear interpolation between laminar and turbulent
            f_LO = (1-w)*16.0/Re_LO+w*0.046/(Re_LO**0.2)
        
        dpdz_LO = 2 * f_LO * pow(G, 2) * v_f / D
        
        Xtt = pow(mu_f / mu_g, 0.1) * pow(v_f / v_g, 0.5) * pow((1 - x) / x, 0.9)
        Phi_LO2 = 12.82 * pow(Xtt, -1.47) * pow(1 - x, 1.8)
        dpdz = Phi_LO2 * dpdz_LO
        
        return dpdz

    def ChisholmPressureGradientAvg(self,x_min, x_max, AS, G, D, Tbubble, Tdew, C=None,satTransport=None):
        """
        Returns the average pressure gradient between qualities of x_min and x_max.

        To obtain the pressure gradient for a given value of x, pass it in as x_min and x_max

        Required parameters:
        * x_min : The minimum quality for the range [-]
        * x_max : The maximum quality for the range [-]
        * AS : AbstractState with the refrigerant name and backend
        * G : Mass flux [kg/m^2/s]
        * D : Diameter of tube [m]
        * Tbubble : Bubblepoint temperature of refrigerant [K]
        * Tdew : Dewpoint temperature of refrigerant [K]

        """
        def ChisholmFunc(x):
            dpdz = self.Chisholm(AS, G, D, x, Tbubble, Tdew,C,satTransport)
            return dpdz

        # Use Simpson's Rule to calculate the average pressure gradient
        # Can't use adapative quadrature since function is not sufficiently smooth
        # Not clear why not sufficiently smooth at x>0.9
        if abs(x_max-x_min) < 100*machine_eps:
            return ChisholmFunc(x_min)
        else:
            # Calculate the tranport properties once
            satTransport = {}
            AS.update(CP.QT_INPUTS, 0.0, Tbubble)
            satTransport['v_f'] = 1/AS.rhomass()  # [m^3/kg]
            satTransport['mu_f'] = AS.viscosity()  # [Pa-s]
            AS.update(CP.QT_INPUTS, 1.0, Tdew)
            satTransport['v_g'] = 1/AS.rhomass()  # [m^3/kg]
            satTransport['mu_g'] = AS.viscosity()  # [Pa-s]

            xx = np.linspace(x_min, x_max, 30)
            DP = np.zeros_like(xx)
            for i in range(len(xx)):
                DP[i] = ChisholmFunc(xx[i])
            return simps(DP, xx)/(x_max-x_min)

    def Chisholm(self, AS, G, D, x, Tbubble, Tdew, C=None, satTransport=None):
        '''from Jung, D. S. and Radermacher, R., 1989, "Prediction of Pressure
            Drop During Horizontal Annular Flow Boiling of Pure and Mixed 
            Refrigerants," International Journal of Heat and Mass Transfer, 
            Vol. 32, pp. 2435-2446. '''

        x = float(x)
        if satTransport == None:
            # Calculate Necessary saturation properties
            AS.update(CP.QT_INPUTS, 0.0, Tbubble)
            v_f = 1/AS.rhomass()  # [m^3/kg]
            mu_f = AS.viscosity()  # [Pa-s]
            AS.update(CP.QT_INPUTS, 1.0, Tdew)
            v_g = 1/AS.rhomass()  # [m^3/kg]
            mu_g = AS.viscosity()  # [Pa-s]
        else:
            # Pull out of the dictionary
            v_f = satTransport['v_f']
            v_g = satTransport['v_g']
            mu_f = satTransport['mu_f']
            mu_g = satTransport['mu_g']


        if x == 1:
            Re_g = G * D / mu_g
            if Re_g < 1000:  # Laminar
                f_g = 16.0/Re_g
            elif Re_g > 2000:  # Fully-Turbulent
                f_g = 0.079/(Re_g**0.25)
            else:  # Mixed
                # Weighting factor
                w = (Re_g-1000)/(2000-1000)
                # Linear interpolation between laminar and turbulent
                f_g = (1-w)*16.0/Re_g+w*0.079/(Re_g**0.25)
            dpdz_g = 2 * f_g * pow(G, 2) * v_g / D 
            return dpdz_g
        
        elif x == 0:
            Re_f = G * D / mu_f
            if Re_f < 1000:  # Laminar
                f_f = 16.0/Re_f
            elif Re_f > 2000:  # Fully-Turbulent
                f_f = 0.079/(Re_f**0.25)
            else:  # Mixed
                # Weighting factor
                w = (Re_f-1000)/(2000-1000)
                # Linear interpolation between laminar and turbulent
                f_f = (1-w)*16.0/Re_f+w*0.079/(Re_f**0.25)
            dpdz_f = 2 * f_f * pow(G, 2) * v_f / D
            return dpdz_f

        Re_LO = G * D / mu_f
        
        if Re_LO < 1000:  # Laminar
            f_LO = 16.0/Re_LO
        elif Re_LO > 2000:  # Fully-Turbulent
            f_LO = 0.079/(Re_LO**0.25)
        else:  # Mixed
            # Weighting factor
            w = (Re_LO-1000)/(2000-1000)
            # Linear interpolation between laminar and turbulent
            f_LO = (1-w)*16.0/Re_LO+w*0.079/(Re_LO**0.25)
        
        dpdz_LO = 2 * f_LO * pow(G, 2) * v_f / D
        
        gamma = pow(v_g / v_f, 0.5) * pow(mu_g / mu_f, 0.125)
        if 0 <= gamma <= 9.5:
            if G <= 500:
                B = 4.8
            elif  500 < G < 1900:
                B = 2400 / G
            else:
                B = 55 / pow(G, 0.5)
        elif 9.5 < gamma  < 28:
            if G <= 600:
                B = 520 / (gamma * pow(G, 0.5))
            else:
                B = 21 / gamma
        else:
            B = 15000 / (pow(gamma, 2) * pow(G, 0.5))

        Phi_LO2 = 1 + (pow(gamma, 2) - 1) * (B * pow(x, 0.875) * pow(1 - x, 0.875) + pow(x, 1.75))
        dpdz = Phi_LO2 * dpdz_LO
        return dpdz

    def FriedelPressureGradientAvg(self,x_min, x_max, AS, G, D, Tbubble, Tdew, C=None,satTransport=None):
        """
        Returns the average pressure gradient between qualities of x_min and x_max.

        To obtain the pressure gradient for a given value of x, pass it in as x_min and x_max

        Required parameters:
        * x_min : The minimum quality for the range [-]
        * x_max : The maximum quality for the range [-]
        * AS : AbstractState with the refrigerant name and backend
        * G : Mass flux [kg/m^2/s]
        * D : Diameter of tube [m]
        * Tbubble : Bubblepoint temperature of refrigerant [K]
        * Tdew : Dewpoint temperature of refrigerant [K]

        """
        def FriedelFunc(x):
            dpdz = self.Friedel(AS, G, D, x, Tbubble, Tdew,C,satTransport)
            return dpdz

        # Use Simpson's Rule to calculate the average pressure gradient
        # Can't use adapative quadrature since function is not sufficiently smooth
        # Not clear why not sufficiently smooth at x>0.9
        if abs(x_max-x_min) < 100*machine_eps:
            return FriedelFunc(x_min)
        else:
            # Calculate the tranport properties once
            satTransport = {}
            AS.update(CP.QT_INPUTS, 0.0, Tbubble)
            satTransport['v_f'] = 1/AS.rhomass()  # [m^3/kg]
            satTransport['mu_f'] = AS.viscosity()  # [Pa-s]
            satTransport['ST'] = AS.surface_tension()
            AS.update(CP.QT_INPUTS, 1.0, Tdew)
            satTransport['v_g'] = 1/AS.rhomass()  # [m^3/kg]
            satTransport['mu_g'] = AS.viscosity()  # [Pa-s]

            xx = np.linspace(x_min, x_max, 30)
            DP = np.zeros_like(xx)
            for i in range(len(xx)):
                DP[i] = FriedelFunc(xx[i])
            return simps(DP, xx)/(x_max-x_min)

    def Friedel(self, AS, G, D, x, Tbubble, Tdew, C=None, satTransport=None):
        '''from Jung, D. S. and Radermacher, R., 1989, "Prediction of Pressure
            Drop During Horizontal Annular Flow Boiling of Pure and Mixed 
            Refrigerants," International Journal of Heat and Mass Transfer, 
            Vol. 32, pp. 2435-2446. '''

        x = float(x)
        if satTransport == None:
            # Calculate Necessary saturation properties
            AS.update(CP.QT_INPUTS, 0.0, Tbubble)
            v_f = 1/AS.rhomass()  # [m^3/kg]
            mu_f = AS.viscosity()  # [Pa-s]
            ST = AS.surface_tension()
            AS.update(CP.QT_INPUTS, 1.0, Tdew)
            v_g = 1/AS.rhomass()  # [m^3/kg]
            mu_g = AS.viscosity()  # [Pa-s]
        else:
            # Pull out of the dictionary
            v_f = satTransport['v_f']
            v_g = satTransport['v_g']
            mu_f = satTransport['mu_f']
            mu_g = satTransport['mu_g']
            ST = satTransport['ST']

        # Re_g = G * (1 - x) * D / mu_g
        Re_g = G * D / mu_g
        if Re_g <= 0:
            f_g = 0
        elif Re_g < 1000:  # Laminar
            f_g = 16.0/Re_g
        elif Re_g > 2000:  # Fully-Turbulent
            f_g = 0.079/(Re_g**0.25)
        else:  # Mixed
            # Weighting factor
            w = (Re_g-1000)/(2000-1000)
            # Linear interpolation between laminar and turbulent
            f_g = (1-w)*16.0/Re_g+w*0.079/(Re_g**0.25)
        if x == 1:
            dpdz_g = 2 * f_g * pow(G, 2) * v_g / D 
            return dpdz_g

        # Re_f = G * x * D / mu_f
        Re_f = G * D / mu_f
        if Re_f <= 0:
            f_f = 0
        elif Re_f < 1000:  # Laminar
            f_f = 16.0/Re_f
        elif Re_f > 2000:  # Fully-Turbulent
            f_f = 0.079/(Re_f**0.25)
        else:  # Mixed
            # Weighting factor
            w = (Re_f-1000)/(2000-1000)
            # Linear interpolation between laminar and turbulent
            f_f = (1-w)*16.0/Re_f+w*0.079/(Re_f**0.25)
        if x == 0:
            dpdz_f = 2 * f_f * pow(G, 2) * v_f / D
            return dpdz_f

        Re_LO = G * D / mu_f
        
        if Re_LO < 1000:  # Laminar
            f_LO = 16.0/Re_LO
        elif Re_LO > 2000:  # Fully-Turbulent
            f_LO = 0.079/(Re_LO**0.25)
        else:  # Mixed
            # Weighting factor
            w = (Re_LO-1000)/(2000-1000)
            # Linear interpolation between laminar and turbulent
            f_LO = (1-w)*16.0/Re_LO+w*0.079/(Re_LO**0.25)
        
        dpdz_LO = 2 * f_LO * pow(G, 2) * v_f / D
        
        E = pow(1 - x, 2) + pow(x, 2) * (v_g * f_g) / (v_f * f_f)
        
        F = pow(x, 0.78) * pow(1 - x, 0.24)
        
        H = pow(v_g / v_f, 0.91) * pow(mu_g / mu_f, 0.19) * pow(1 - mu_g / mu_f, 0.7)
        
        v_H = x * v_g + (1 - x) * v_f
        
        Fr = pow(G, 2) / (9.81 * D * pow(1 / v_H, 2))
        
        We_f = pow(G, 2) * D * v_H / ST
        
        Phi_LO2 = E + 3.24 * F * H / (pow(Fr, 0.045) * pow(We_f, 0.035))
        
        dpdz = Phi_LO2 * dpdz_LO
        
        return dpdz


    def ShahEvaporation_Average(self, x_min, x_max, AS, G, D, p, q_flux, Tbubble,Tdew):
        """
        Returns the average heat transfer coefficient between qualities of x_min and x_max.

        Required parameters:
        * x_min : The minimum quality for the range [-]
        * x_max : The maximum quality for the range [-]
        * AS : AbstractState with the refrigerant name and backend
        * G : Mass flux [kg/m^2/s]
        * D : Diameter of tube [m]
        * p : Pressure [Pa]
        * q_flux : Heat transfer flux [W/m^2]
        * Tbubble : Bubblepoint temperature of refrigerant [K]
        * Tdew : Dewpoint temperature of refrigerant [K]
        """
        # ********************************
        #        Necessary Properties
        # ********************************
        AS.update(CP.QT_INPUTS, 0.0, Tbubble)
        rho_f = AS.rhomass()  # [kg/m^3]
        mu_f = AS.viscosity()  # [Pa-s OR kg/m-s]
        cp_f = AS.cpmass()  # [J/kg-K]
        k_f = AS.conductivity()  # [W/m-K]
        h_l = AS.hmass()  # [J/kg]

        AS.update(CP.QT_INPUTS, 1.0, Tdew)
        rho_g = AS.rhomass()  # [kg/m^3]
        mu_g = AS.viscosity()  # [Pa-s OR kg/m-s]
        cp_g = AS.cpmass()  # [J/kg-K]
        k_g = AS.conductivity()  # [W/m-K]
        h_v = AS.hmass()  # [J/kg]

        h_fg = h_v - h_l  # [J/kg]
        Pr_f = cp_f * mu_f / k_f  # [-]
        Pr_g = cp_g * mu_g / k_g  # [-]

        g_grav = 9.81  # [m/s^2]

        # Shah evaporation correlation
        Fr_L = G**2 / (rho_f*rho_f * g_grav * D)  # [-]
        Bo = abs(q_flux) / (G * h_fg)  # [-]

        if Bo >= 11e-4:
            F = 14.7
        else:
            F = 15.43
        # Pure vapor single-phase heat transfer coefficient
        h_g = 0.023 * (G*D/mu_g)**(0.8) * Pr_g**(0.4) * k_g / D  # [W/m^2-K]
        
        def ShahEvaporation(x):
            if abs(1-x) < 100*machine_eps:
                return h_g
            x = float(x)
            # If the quality is above 0.999, linearly interpolate to avoid division by zero
            if x > 0.999:
                h_1 = ShahEvaporation(1.0)  # Fully fry
                h_999 = ShahEvaporation(0.999)  # At a quality of 0.999
                # Linear interpolation
                return (h_1-h_999)/(1.0-0.999)*(x-0.999)+h_999
            if abs(x) < 100*machine_eps:
                h_L = 0.023 * (G*(1 - x)*D/mu_f)**(0.8) * Pr_f**(0.4) * k_f / D  # [W/m^2-K]
                return h_L
            else:
                h_L = 0.023 * (G*(1 - x)*D/mu_f)**(0.8) * Pr_f**(0.4) * k_f / D  # [W/m^2-K]
            Co = (1 / x - 1)**(0.8) * (rho_g / rho_f)**(0.5)  # [-]

            if Fr_L >= 0.04:
                N = Co
            else:
                N = 0.38 * Fr_L**(-0.3) * Co

            psi_cb = 1.8 / N**(0.8)
            if (0.1 <= N and N <= 1.0):
                psi_bs = F * (Bo)**(0.5) * exp(2.74 * N**(-0.1))
                psi = max([psi_bs, psi_cb])
            else:
                if (N > 1.0):
                    if (Bo > 0.3e-4):
                        psi_nb = 230 * (Bo)**(0.5)
                    else:
                        psi_nb = 1.0 + 46.0 * (Bo)**(0.5)
                    psi = max([psi_nb, psi_cb])
                else:
                    psi_bs = F * (Bo)**(0.5) * exp(2.47 * N**(-0.15))
                    psi = max([psi_bs, psi_cb])
            return psi * h_L  # [W/m^2-K]

        # Calculate h over the range of x
        x = np.linspace(x_min, x_max, 100)
        h = np.zeros_like(x)
        for i in range(len(x)):
            h[i] = ShahEvaporation(x[i])

        # if abs(x_max-x_min) < 5*machine_eps, or they are really really close to being the same
        if abs(x_max-x_min) < 100*machine_eps:
            # return just one of the edge values
            return h[0]
        else:
            # Use Simpson's rule to carry out numerical integration to get average
            return simps(h, x)/(x_max-x_min)

    def KandlikarEvaporation_average(self, x_min, x_max, AS, G, D, p, q_flux, Tbubble,Tdew):
        """
        "A General Correlation for Saturated Two-Phase Flow Boiling Heat 
        Transfer Inside Horizontal and Vertical Tubes" by Kandlikar (1990)

        Returns the average heat transfer coefficient between qualities of x_min and x_max.

        Required parameters:
        * x_min : The minimum quality for the range [-]
        * x_max : The maximum quality for the range [-]
        * AS : AbstractState with the refrigerant name and backend
        * G : Mass flux [kg/m^2/s]
        * D : Diameter of tube [m]
        * p : Pressure [Pa]
        * q_flux : Heat transfer flux [W/m^2]
        * Tbubble : Bubblepoint temperature of refrigerant [K]
        * Tdew : Dewpoint temperature of refrigerant [K]
        """
        # ********************************
        #        Necessary Properties
        # ********************************
        AS.update(CP.QT_INPUTS, 0.0, Tbubble)
        rho_f = AS.rhomass()  # [kg/m^3]
        mu_f = AS.viscosity()  # [Pa-s OR kg/m-s]
        cp_f = AS.cpmass()  # [J/kg-K]
        k_f = AS.conductivity()  # [W/m-K]
        h_l = AS.hmass()  # [J/kg]

        AS.update(CP.QT_INPUTS, 1.0, Tdew)
        rho_g = AS.rhomass()  # [kg/m^3]
        mu_g = AS.viscosity()  # [Pa-s OR kg/m-s]
        cp_g = AS.cpmass()  # [J/kg-K]
        k_g = AS.conductivity()  # [W/m-K]
        h_v = AS.hmass()  # [J/kg]

        h_fg = h_v - h_l  # [J/kg]
        Pr_f = cp_f * mu_f / k_f  # [-]
        Pr_g = cp_g * mu_g / k_g  # [-]

        g_grav = 9.81  # [m/s^2]
        
        # Petterson evaporation correlation
        Fr_L = G**2 / (rho_f*rho_f * g_grav * D)  # [-]
        Bo = abs(q_flux) / (G * h_fg)  # [-]
        
        # Forster and Zuber multiplier depends on fluid type.
        if self.ref == 'Water':
            F_fl = 1
        elif self.ref == 'R11':
            F_fl = 1.3
        elif self.ref == 'R12':
            F_fl = 1.5
        elif self.ref == 'R22':
            F_fl = 2.2
        elif self.ref == 'R113':
            F_fl = 1.3
        elif self.ref == 'R114':
            F_fl = 1.24
        elif self.ref == 'R152A':
            F_fl = 1.1
        elif self.ref == 'Nitrogen':
            F_fl = 4.7
        elif self.ref == 'Neon':
            F_fl = 3.5
        elif self.ref == 'R32':
            F_fl = 3.26
        else: # should be calculated based on the Forster and Zuber (1955) correlation to correlate the pool boiling data for that fluid. but I couldn't find the correlation
            F_fl = 1.0
        
        # Kandlikar correlation constants
        c_c_1 = 1.1360
        c_c_2 = -0.9
        c_c_3 = 667.2
        c_c_4 = 0.7
        c_n_1 = 0.6683
        c_n_2 = -0.2
        c_n_3 = 1058.0
        c_n_4 = 0.7
        if Fr_L > 0.04:
            c_c_5 = 0.0
            c_n_5 = 0.0
        else:
            c_c_5 = 0.3
            c_n_5 = 0.3

        # Pure vapor single-phase heat transfer coefficient
        h_g = 0.023 * (G*D/mu_g)**(0.8) * Pr_g**(0.4) * k_g / D  # [W/m^2-K]

        def KandlikarEvaporation(x):
            if abs(1-x) < 100 * machine_eps:
                return h_g
            x = float(x)
            # If the quality is above 0.999, linearly interpolate to avoid division by zero
            if x > 0.999:
                h_1 = KandlikarEvaporation(1.0)  # Fully fry
                h_999 = KandlikarEvaporation(
                    0.999)  # At a quality of 0.999
                # Linear interpolation
                return (h_1-h_999)/(1.0-0.999)*(x-0.999)+h_999
            if abs(x) < 100 * machine_eps:
                h_L = 0.023 * (G*(1 - x)*D/mu_f)**(0.8) * \
                    Pr_f**(0.4) * k_f / D  # [W/m^2-K]
                return h_L
            else:
                h_L = 0.023 * (G*(1 - x)*D/mu_f)**(0.8) * \
                    Pr_f**(0.4) * k_f / D  # [W/m^2-K]

            Co = (1 / x - 1)**(0.8) * (rho_g / rho_f)**(0.5)  # [-]

            # HTC due to convective boiling
            h_c = h_L*(c_c_1*pow(Co, c_c_2)*pow((25.0*Fr_L),c_c_5) + c_c_3*pow(Bo, c_c_4)*F_fl)
            
            # HTC due to nucleate boiling
            h_n = h_L*(c_n_1*pow(Co, c_n_2)*pow((25.0*Fr_L),c_n_5) + c_n_3*pow(Bo, c_n_4)*F_fl)

            return max(h_n , h_c)

        # Calculate h over the range of x
        x = np.linspace(x_min, x_max, 100)
        h = np.zeros_like(x)
        for i in range(len(x)):
            h[i] = KandlikarEvaporation(x[i])

        # if abs(x_max-x_min) < 5*machine_eps, or they are really really close to being the same
        if abs(x_max-x_min) < 100*machine_eps:
            # return just one of the edge values
            return h[0]
        else:
            # Use Simpson's rule to carry out numerical integration to get average
            return simps(h, x)/(x_max-x_min)

    def Gungor_Winterton_average(self, x_min, x_max, AS, G, D, p, q_flux, Tbubble,Tdew):
        """
        "A general correlation for flow boiling in tubes and annuli" by Gungor 
        and Winterton (1986)

        Returns the average heat transfer coefficient between qualities of x_min and x_max.

        Required parameters:
        * x_min : The minimum quality for the range [-]
        * x_max : The maximum quality for the range [-]
        * AS : AbstractState with the refrigerant name and backend
        * G : Mass flux [kg/m^2/s]
        * D : Diameter of tube [m]
        * p : Pressure [Pa]
        * q_flux : Heat transfer flux [W/m^2]
        * Tbubble : Bubblepoint temperature of refrigerant [K]
        * Tdew : Dewpoint temperature of refrigerant [K]
        """
        # ********************************
        #        Necessary Properties
        # ********************************
        AS.update(CP.QT_INPUTS, 0.0, Tbubble)
        rho_f = AS.rhomass()  # [kg/m^3]
        mu_f = AS.viscosity()  # [Pa-s OR kg/m-s]
        cp_f = AS.cpmass()  # [J/kg-K]
        k_f = AS.conductivity()  # [W/m-K]
        h_l = AS.hmass()  # [J/kg]
        pcrit = AS.p_critical()
        Pstar = p / pcrit
        M = AS.molar_mass()
        
        AS.update(CP.QT_INPUTS, 1.0, Tdew)
        rho_g = AS.rhomass()  # [kg/m^3]
        mu_g = AS.viscosity()  # [Pa-s OR kg/m-s]
        cp_g = AS.cpmass()  # [J/kg-K]
        k_g = AS.conductivity()  # [W/m-K]
        h_v = AS.hmass()  # [J/kg]

        h_fg = h_v - h_l  # [J/kg]
        Pr_f = cp_f * mu_f / k_f  # [-]
        Pr_g = cp_g * mu_g / k_g  # [-]

        g_grav = 9.81  # [m/s^2]
        
        # Petterson evaporation correlation
        Fr_L = G**2 / (rho_f*rho_f * g_grav * D)  # [-]
        Bo = abs(q_flux) / (G * h_fg)  # [-]

        if Fr_L < 0.05:
            E2 = pow(Fr_L, 0.1 - 2 * Fr_L)
            S2 = pow(Fr_L, 0.5)
        else:
            E2 = 1.0
            S2 = 1.0
        
        # Pure vapor single-phase heat transfer coefficient
        h_g = 0.023 * (G*D/mu_g)**(0.8) * Pr_g**(0.4) * k_g / D  # [W/m^2-K]

        # Pool boiling heat transfer coefficient
        h_pool = 55 * pow(Pstar, 0.12) * pow(-log(Pstar,10), -0.55) * pow(M*1000, -0.5) * pow(q_flux, 0.67)

        def GungorEvaporation(x):
            if abs(1-x) < 100 * machine_eps:
                return h_g
            x = float(x)
            Re_f = G*(1 - x)*D/mu_f
            # If the quality is above 0.999, linearly interpolate to avoid division by zero
            if x > 0.999:
                h_1 = GungorEvaporation(1.0)  # Fully fry
                h_999 = GungorEvaporation(0.999)  # At a quality of 0.999
                # Linear interpolation
                return (h_1-h_999)/(1.0-0.999)*(x-0.999)+h_999
            
            if abs(x) < 100 * machine_eps:
                h_L = 0.023 * (Re_f)**(0.8) * \
                    Pr_f**(0.4) * k_f / D  # [W/m^2-K]
                return h_L
            h_L = 0.023 * (Re_f)**(0.8) * Pr_f**(0.4) * k_f / D  # [W/m^2-K]
            
            Xtt = pow(mu_f / mu_g, 0.1) * pow(rho_g / rho_f, 0.5) * pow((1 - x) / x, 0.9)

            E = 1 + 24000 * pow(Bo, 1.16) + 1.37 / pow(Xtt, 0.86)
            
            E *= E2
            
            S = 1 / (1 + 1.15e-6 * pow(E, 2) * pow(Re_f, 1.17))
            
            S *= S2

            h = E * h_L + S * h_pool
            
            return h

        # Calculate h over the range of x
        x = np.linspace(x_min, x_max, 100)
        h = np.zeros_like(x)
        for i in range(len(x)):
            h[i] = GungorEvaporation(x[i])

        # if abs(x_max-x_min) < 5*machine_eps, or they are really really close to being the same
        if abs(x_max-x_min) < 100*machine_eps:
            # return just one of the edge values
            return h[0]
        else:
            # Use Simpson's rule to carry out numerical integration to get average
            return simps(h, x)/(x_max-x_min)

    def LongoCondensation(self, x_avg, G, dh, AS, TsatL, TsatV):

        AS.update(CP.QT_INPUTS, 1.0, TsatV)
        rho_V = AS.rhomass()  # [kg/m^3]
        AS.update(CP.QT_INPUTS, 0.0, TsatL)
        rho_L = AS.rhomass()  # [kg/m^3]
        mu_L = AS.viscosity()  # [Pa-s OR kg/m-s]
        cp_L = AS.cpmass()  # [J/kg-K]
        k_L = AS.conductivity()  # [W/m-K]
        Pr_L = cp_L * mu_L / k_L  # [-]

        Re_eq = G*((1-x_avg)+x_avg*sqrt(rho_L/rho_V))*dh/mu_L

        if Re_eq < 1750:
            Nu = 60*Pr_L**(1/3)
        else:
            Nu = ((75-60)/(3000-1750)*(Re_eq-1750)+60)*Pr_L**(1/3)
        h = Nu*k_L/dh
        return h

    def ShahCondensation_Average(self, x_min, x_max, AS, G, D, p, TsatL, TsatV):
        # ********************************
        #        Necessary Properties
        #    Calculated outside the quadrature integration for speed
        # ********************************
        AS.update(CP.QT_INPUTS, 0.0, TsatL)
        rho_f = AS.rhomass()
        mu_f = AS.viscosity()  # [Pa-s OR kg/m-s]
        cp_f = AS.cpmass()  # [J/kg-K]
        k_f = AS.conductivity()  # [W/m-K]
        Pr_f = cp_f * mu_f / k_f  # [-]
        pcrit = AS.p_critical()  # [Pa]
        AS.update(CP.QT_INPUTS, 1.0, TsatV)
        rho_g = AS.rhomass()
        mu_g = AS.viscosity()  # [Pa-s OR kg/m-s]
        Pstar = p / pcrit
        h_L = 0.023 * (G*D/mu_f)**(0.8) * Pr_f**(0.4) * \
            k_f / D  # [W/m^2-K]

        def ShahCondensation(x, AS, G, D, p):
            '''From "An Improved and Extended General Correlation for Heat 
            Transfer During Condensation in Plain Tubes" by Shah (2009)'''
            x = float(x)
            Z = pow(1/x - 1, 0.8) * pow(Pr_f, 0.4)
            J_g_boundary = 0.98 * pow(Z + 0.263, -0.62)
            J_g = (x * G) / pow(9.81 * D * rho_g * (rho_f - rho_g), 0.5)
            n = 0.0058 + 0.577 * Pstar
            h_I = h_L * pow(mu_f / (14 * mu_g), n) *((1 - x)**(0.8) + (3.8 * x**(0.76) * (1 - x)**(0.04)) / (Pstar**(0.38)))
            if J_g >= J_g_boundary:
                # Regime I
                h = h_I
            else:
                # Regime II
                Re_LS = G * (1 - x) * D / mu_f
                h_Nu = 1.32 * pow(Re_LS, -1/3) * pow(rho_f * (rho_f - rho_g) * 9.81 * pow(k_f, 3) / pow(mu_f, 2), 1/3)
                h = h_Nu + h_I
            return h

        # Calculate Dp over the range of xx
        xx = np.linspace(x_min, x_max, 100)
        h = np.zeros_like(xx)
        for i in range(len(xx)):
            h[i] = ShahCondensation(xx[i],AS, G, D, p)
        
        # Use Simpson's rule to carry out numerical integration to get average DP and average h
        if abs(x_max-x_min) < 100*machine_eps:
            # return just one of the edge values
            return h[0]
        else:
            # Use Simpson's rule to carry out numerical integration to get average DP
            return simps(h, xx)/(x_max-x_min)

    def DobsonChatoCondensation_Average(self, x_min, x_max, AS, G, D, p, TsatL, TsatV, q_flux):
        ''' from 'Condensation in Smooth Horizontal Tubes', Dobson and Chato (1998)'''

        # ********************************
        #        Necessary Properties
        #    Calculated outside the quadrature integration for speed
        # ********************************
        AS.update(CP.QT_INPUTS, 0.0, TsatL)
        mu_f = AS.viscosity()  # [Pa-s OR kg/m-s]
        cp_f = AS.cpmass()  # [J/kg-K]
        k_f = AS.conductivity()  # [W/m-K]
        rho_f = AS.rhomass()
        Pr_f = cp_f * mu_f / k_f  # [-]
        ST = AS.surface_tension()
        h_f = AS.hmass()
        
        AS.update(CP.QT_INPUTS, 1.0, TsatV)
        mu_g = AS.viscosity()  # [Pa-s OR kg/m-s]
        cp_g = AS.cpmass()  # [J/kg-K]
        k_g = AS.conductivity()  # [W/m-K]
        rho_g = AS.rhomass()
        Pr_g = cp_g * mu_g / k_g  # [-]
        h_g = AS.hmass()
        
        h_GL = h_g - h_f
        Fr_f = sqrt(pow(G, 2) / (pow(rho_f, 2) * 9.81 * D))
        Re_vo = G * D / mu_g
        Ga = 9.81 * rho_f * (rho_f - rho_g) * pow(D, 3) / pow(mu_f, 2)
        
        def DobsonChatoCondensation(x, AS, G, D, p):
            x = float(x)
            if x < 5 *np.finfo(float).eps:
                x = 5 *np.finfo(float).eps
            Re_f = G * D * (1 - x) / mu_f
            
            Xtt = pow(mu_f / mu_g, 0.1) * pow(rho_g / rho_f, 0.5) * pow((1 - x) / x, 0.9)
            
            if Re_f > 1250:
                Fr_so = 1.26 * pow(Re_f, 1.04) * pow((1 + 1.09 * pow(Xtt, 0.039)) / Xtt, 1.5) / pow(Ga, 0.5)
            else:
                Fr_so = 0.025 * pow(Re_f, 1.59) * pow((1 + 1.09 * pow(Xtt, 0.039)) / Xtt, 1.5) / pow(Ga, 0.5)

            if G >= 500:
                Nu = 0.023 * pow(Re_f, 0.8) * pow(Pr_f, 0.4) * (1 + 2.22 / pow(Xtt, 0.89))
            else:
                if Fr_so <= 20:
                    alpha = pow(1 + (1 - x) / x * pow(rho_g / rho_f, 2 / 3), -1) # Zivi
                    theta_f = pi - acos(2 * alpha - 1)
                    if 0 < Fr_f <= 0.7:
                        C1 = 4.172 + 5.48 * Fr_f - 1.564 * pow(Fr_f, 2)
                        C2 = 1.773 - 0.169 * Fr_f
                    elif Fr_f > 0.7:
                        C1 = 7.242
                        C2 = 1.655
                    
                    Phi_f = pow(1.376 + C1 / pow(Xtt, C2), 0.5)
                    Nu_forced = 0.0195 * pow(Re_f, 0.8) * pow(Pr_f, 0.4) * Phi_f
                    error = 100
                    h = 2500
                    i = 1
                    while abs(error) > 1 and i <= 100:
                        delta_T = abs(q_flux / h)
                        Ja_f = cp_f * delta_T / h_GL
                        Nu = (0.23 * pow(Re_vo, 0.12)) / (1 + 1.11 * pow(Xtt, 0.58)) * pow(Ga * Pr_f / Ja_f, 0.25) + (1 - theta_f / pi) * Nu_forced
                        error = Nu * k_f / D - h
                        h = Nu * k_f / D
                        i += 1
                else:
                    Nu = 0.023 * pow(Re_f, 0.8) * pow(Pr_f, 0.4) * (1 + 2.22 / pow(Xtt, 0.889))
            
            h = Nu * k_f / D
            return h
            
        # Use Simpson's Rule to calculate the average pressure drop
        if abs(x_max-x_min) < 100*machine_eps:
            value = DobsonChatoCondensation(x_min,AS, G, D, p)
        else:
            # Calculate h over the range of xx
            xx = np.linspace(x_min, x_max, 100)
            h = np.zeros_like(xx)
            for i in range(len(xx)):
                h[i] = DobsonChatoCondensation(xx[i], AS, G, D, p)
            # Use Simpson's rule to carry out numerical integration to get average h
            value = simps(h, xx)/(x_max-x_min)
        return value

    def CavalliniCondensation_Average(self, x_min, x_max, AS, G, D, p, TsatL, TsatV, q_flux):
        ''' from 'Condensation inside and outside smooth and enhanced tubes — 
        a review of recent research', Cavallini (2003)'''
        
        # ********************************
        #        Necessary Properties
        #    Calculated outside the quadrature integration for speed
        # ********************************
        AS.update(CP.QT_INPUTS, 0.0, TsatL)
        mu_f = AS.viscosity()  # [Pa-s OR kg/m-s]
        cp_f = AS.cpmass()  # [J/kg-K]
        k_f = AS.conductivity()  # [W/m-K]
        rho_f = AS.rhomass()
        Pr_f = cp_f * mu_f / k_f  # [-]
        ST = AS.surface_tension()
        h_f = AS.hmass()
        
        AS.update(CP.QT_INPUTS, 1.0, TsatV)
        mu_g = AS.viscosity()  # [Pa-s OR kg/m-s]
        cp_g = AS.cpmass()  # [J/kg-K]
        k_g = AS.conductivity()  # [W/m-K]
        rho_g = AS.rhomass()
        Pr_g = cp_g * mu_g / k_g  # [-]
        h_g = AS.hmass()
        
        h_GL = h_g - h_f
        
        def CavalliniCondensation(x, AS, G, D, p, q_flux):
            x = float(x)
            J_g = x * G / pow(9.81 * D * rho_g * (rho_f - rho_g), 0.5)
            Xtt = pow(mu_f / mu_g, 0.1) * pow(rho_g / rho_f, 0.5) * pow((1 - x) / x, 0.9)
            if J_g >= 2.5:
                Re_L = G*(1-x)*D/mu_f
                if Re_L <= 1145:
                    delta_plus = pow(Re_L / 2, 0.5)
                else:
                    delta_plus = 0.0504 * pow(Re_L, 7 / 8)
                if delta_plus <= 5:
                    T_plus = delta_plus * Pr_f
                elif 5 < delta_plus < 30:
                    T_plus = 5 * (Pr_f + log(1 + Pr_f * (delta_plus / 5 - 1)))
                else:
                    T_plus = 5 * (Pr_f + log(1 + 5 * Pr_f) + 0.495 * log(delta_plus / 30))

                F = pow(x, 0.6978)
                if G*D/mu_f > 2000:
                    f_LO = 0.046 * pow(G * D / mu_f, -0.2)
                else:
                    f_LO = 16 / (G * D / mu_f)
                
                if G*D/mu_g > 2000:
                    f_GO = 0.046 * pow(G * D / mu_g, -0.2)
                else:
                    f_GO = 16 / (G * D / mu_g)
                H = pow(rho_f / rho_g, 0.3278) * pow(mu_g / mu_f, -1.181) * pow(1- mu_g / mu_f, 3.477)
                E = pow(1 - x, 2) + pow(x, 2) * (rho_f * f_GO)/(rho_g * f_LO)
                We = pow(G, 2) * D / (rho_g * ST)
                Phi_LO2 = E + (1.262 * F * H)/pow(We, 0.1458)
                dpdz_f = Phi_LO2 * 2 * f_LO * pow(G, 2) / (D*rho_f)
                taw = dpdz_f * D / 4
                h = rho_f * cp_f * pow(taw/rho_f, 0.5) / T_plus
                
            elif J_g < 2.5 and Xtt <= 1.6:
                G_JG2_5 = 2.5 * pow(9.81 * D * rho_g * (rho_f - rho_g), 0.5) / x
                Re_L = G_JG2_5*(1-x)*D/mu_f
                if Re_L <= 1145:
                    delta_plus = pow(Re_L / 2, 0.5)
                else:
                    delta_plus = 0.0504 * pow(Re_L, 7 / 8)
                if delta_plus <= 5:
                    T_plus = delta_plus * Pr_f
                elif 5 < delta_plus < 30:
                    T_plus = 5 * (Pr_f + log(1 + Pr_f * (delta_plus / 5 - 1)))
                else:
                    T_plus = 5 * (Pr_f + log(1 + 5 * Pr_f) + 0.495 * log(delta_plus / 30))
                F = pow(x, 0.6978)
                if G_JG2_5*D/mu_f > 2000:
                    f_LO = 0.046 * pow(G_JG2_5 * D / mu_f, -0.2)
                else:
                    f_LO = 16 / (G_JG2_5 * D / mu_f)
                
                if G_JG2_5*D/mu_g > 2000:
                    f_GO = 0.046 * pow(G_JG2_5 * D / mu_g, -0.2)
                else:
                    f_GO = 16 / (G_JG2_5 * D / mu_g)
                H = pow(rho_f / rho_g, 0.3278) * pow(mu_g / mu_f, -1.181) * pow(1- mu_g / mu_f, 3.477)
                E = pow(1 - x, 2) + pow(x, 2) * (rho_f * f_GO)/(rho_g * f_LO)
                We = pow(G_JG2_5, 2) * D / (rho_g * ST)
                Phi_LO2 = E + (1.262 * F * H)/pow(We, 0.1458)
                dpdz_f = Phi_LO2 * 2 * f_LO * pow(G_JG2_5, 2) / (D*rho_f)
                taw = dpdz_f * D / 4
                h_JG2_5 = rho_f * cp_f * pow(taw/rho_f, 0.5) / T_plus
                
                Re_LO = G * D / mu_f
                alpha_LO = 0.023 * (k_f / D) * pow(Re_LO, 0.8) * pow(Pr_f, 0.4)
                alpha_f = alpha_LO * pow(1 - x, 0.8)
                epslon = x / (x + (1 - x) * pow(rho_g / rho_f, 0.66)) # Zivi
                theta = pi - acos(2 * epslon - 1)
                h = 3000
                error = 100
                i = 1
                while (not (-1 < error < 1)) and i <= 100:
                    delta_T = abs(q_flux / h)
                    h_st = 0.725 * pow(1 + 0.82 * pow((1 - x) / x, 0.268), -1) * pow(pow(k_f, 3) * rho_f * (rho_f - rho_g) * 9.81 * h_GL / (mu_f * D * delta_T), 0.25) + alpha_f * (1 - theta/pi)
                    error = (h_JG2_5 - h_st) * (J_g / 2.5) + h_st - h
                    h = h + error
                    i += 1

            elif J_g < 2.5 and Xtt > 1.6:
                Re_LO = G * D / mu_f
                alpha_LO = 0.023 * (k_f / D) * pow(Re_LO, 0.8) * pow(Pr_f, 0.4)
                x_1_6 = pow(mu_f/mu_g, 1/9) * pow(rho_g/rho_f, 5/9) / (1.686 + pow(mu_f / mu_g, 1/9) * pow(rho_g/rho_f, 5/9))
                
                G_JG2_5 = 2.5 * pow(9.81 * D * rho_g * (rho_f - rho_g), 0.5) / x_1_6
                Re_L = G_JG2_5*(1-x_1_6)*D/mu_f
                if Re_L <= 1145:
                    delta_plus = pow(Re_L / 2, 0.5)
                else:
                    delta_plus = 0.0504 * pow(Re_L, 7 / 8)
                if delta_plus <= 5:
                    T_plus = delta_plus * Pr_f
                elif 5 < delta_plus < 30:
                    T_plus = 5 * (Pr_f + log(1 + Pr_f * (delta_plus / 5 - 1)))
                else:
                    T_plus = 5 * (Pr_f + log(1 + 5 * Pr_f) + 0.495 * log(delta_plus / 30))
                F = pow(x_1_6, 0.6978)
                if G_JG2_5*D/mu_f > 2000:
                    f_LO = 0.046 * pow(G_JG2_5 * D / mu_f, -0.2)
                else:
                    f_LO = 16 / (G_JG2_5 * D / mu_f)
                
                if G_JG2_5*D/mu_g > 2000:
                    f_GO = 0.046 * pow(G_JG2_5 * D / mu_g, -0.2)
                else:
                    f_GO = 16 / (G_JG2_5 * D / mu_g)
                H = pow(rho_f / rho_g, 0.3278) * pow(mu_g / mu_f, -1.181) * pow(1- mu_g / mu_f, 3.477)
                E = pow(1 - x_1_6, 2) + pow(x_1_6, 2) * (rho_f * f_GO)/(rho_g * f_LO)
                We = pow(G_JG2_5, 2) * D / (rho_g * ST)
                Phi_LO2 = E + (1.262 * F * H)/pow(We, 0.1458)
                dpdz_f = Phi_LO2 * 2 * f_LO * pow(G_JG2_5, 2) / (D*rho_f)
                taw = dpdz_f * D / 4
                h_JG2_5 = rho_f * cp_f * pow(taw/rho_f, 0.5) / T_plus
                
                alpha_f = alpha_LO * pow(1 - x_1_6, 0.8)
                epslon = x_1_6 / (x_1_6 + (1 - x_1_6) * pow(rho_g / rho_f, 0.66)) # Zivi
                theta = pi - acos(2 * epslon - 1)
                h = 3000
                error = 100
                i = 1
                while error > 1 and i <= 100:
                    delta_T = abs(q_flux / h)
                    h_st = 0.725 * pow(1 + 0.82 * pow((1 - x_1_6) / x_1_6, 0.268), -1) * pow(pow(k_f, 3) * rho_f * (rho_f - rho_g) * 9.81 * h_GL / (mu_f * D * delta_T), 0.25) + alpha_f * (1 - theta/pi)
                    h_1_6 = (h_JG2_5 - h_st) * (J_g / 2.5) + h_st
                    error = alpha_LO + x * (h_1_6 - alpha_LO) / x_1_6 - h
                    h = h + error
                    i += 1
            return h
        
        # Use Simpson's Rule to calculate the average pressure drop
        if abs(x_max-x_min) < 100*machine_eps:
            return CavalliniCondensation(x_min,AS, G, D, p,q_flux)
        else:
            # Calculate h over the range of xx
            xx = np.linspace(x_min, x_max, 100)
            h = np.zeros_like(xx)
            for i in range(len(xx)):
                h[i] = CavalliniCondensation(xx[i], AS, G, D, p, q_flux)
                
            # Use Simpson's rule to carry out numerical integration to get average h
            if abs(x_max-x_min) < 100*machine_eps:
                # return just one of the edge values
                return h[0]
            else:
                # Use Simpson's rule to carry out numerical integration to get average h
                return simps(h, xx)/(x_max-x_min)

    def Koyama2006_Condensation_h(self, x_min, x_max, AS, G, Dh, p, TsatL, TsatV, beta, Afa, Afn, Aa, An, pitch, w, q_flux):
        ''' from 'Experimental Study on Condensation of Pure Refrigerants in 
        Horizontal Micro-Fin Tube Proposal of Correlations for Heat Transfer 
        Coefficient and Frictional Pressure Drop', Koyama (2006)'''
        
        # ********************************
        #        Necessary Properties
        #    Calculated outside the quadrature integration for speed
        # ********************************
        AS.update(CP.QT_INPUTS, 0.0, TsatL)
        mu_f = AS.viscosity()  # [Pa-s OR kg/m-s]
        cp_f = AS.cpmass()  # [J/kg-K]
        k_f = AS.conductivity()  # [W/m-K]
        rho_f = AS.rhomass()
        Pr_f = cp_f * mu_f / k_f  # [-]
        ST = AS.surface_tension()
        h_f = AS.hmass()
        
        AS.update(CP.QT_INPUTS, 1.0, TsatV)
        mu_g = AS.viscosity()  # [Pa-s OR kg/m-s]
        cp_g = AS.cpmass()  # [J/kg-K]
        k_g = AS.conductivity()  # [W/m-K]
        rho_g = AS.rhomass()
        Pr_g = cp_g * mu_g / k_g  # [-]
        h_g = AS.hmass()
        
        h_GL = h_g - h_f
        
        # friction factor from carnavos
        Fstar = pow(Afa / Afn, 0.5) * pow(1/cos(beta), 0.75)
        
        Bo = (pitch - w) * Dh * 9.81 * (rho_f - rho_g) / ST # [-]
        
        Ga = 9.81 * pow(rho_f, 2) * pow(Dh, 3) / pow(mu_f, 2)

        eta_A = Aa / An

        def Koyama2006(x, AS, G, Dh, p):
            if x > 0.99:
               x = 0.99
            
            Re_g = G * x * Dh / mu_g
            Re_f = G * (1 - x) * Dh / mu_g
                
            # f_g = 0.046 / pow(Re_g, 0.2) / Fstar
            e_D = 0
            A = ((-2.457 * log((7.0 / Re_g)**(0.9) + 0.27 * e_D)))**16
            B = (37530.0 / Re_g)**16
            f_g = 8 * ((8/Re_g)**12.0 + 1 / (A + B)**(1.5))**(1/12)
            f_g /= Fstar
            
            Fr = G / pow(9.81 * Dh * rho_g * (rho_f - rho_g), 0.5)
            
            Xtt = pow(mu_f / mu_g, 0.1) * pow(rho_g / rho_f, 0.5) * pow((1 - x) / x, 0.9)
            
            phi_V = 1 + 1.2 * pow(Fr, 0.05) * pow(Xtt, 0.5)
            
            eps_smith = pow(1 + rho_g / rho_f * 0.4 * (1 / x - 1) + rho_g / rho_f * 0.6 * (1 / x - 1) * pow((rho_f / rho_g + 0.4 * (1 / x - 1))/(1 + 0.4 * (1 / x - 1)) ,0.5) ,-1)
            
            eps_homo = pow(1 + (rho_g / rho_f) * (1 - x) / x ,-1)

            eps = 0.81 * eps_smith + 0.19 * pow(x, 100 * pow(rho_g / rho_f, 0.8)) * eps_homo
            
            H = eps + (10 * pow(1 - eps, 0.1) - 8.9) * pow(eps, 0.5) * (1 - pow(eps, 0.5))
            
            Nu_f = 2.12 * pow(f_g, 0.5) * phi_V * pow(rho_f/ rho_g, 0.1) * (x / (1 - x)) * pow(Re_f, 0.5) * pow(Pr_f, 0.5)
            
            h_2phase = 5000
            i = 1
            error = 100
            while abs(error) > 1 and i < 10:
                delta_T = abs(q_flux) / h_2phase
                Ph_f = cp_f * delta_T / h_GL
                Nu_N = 1.98 * H / (pow(eta_A, 0.5) * pow(Bo, 0.1)) * pow(Ga * Pr_f / Ph_f, 0.25)
                Nu = pow(pow(Nu_f, 2) + pow(Nu_N, 2), 0.5)
                error = h_2phase - Nu * k_f / Dh
                h_2phase = Nu * k_f / Dh
                i += 1
            
            h_2phase *= eta_A * self.Deq / self.ID

            return h_2phase
            
        # Use Simpson's Rule to calculate the average pressure drop
        if abs(x_max-x_min) < 100*machine_eps:
            return Koyama2006(x_min,AS, G, Dh, p)
        else:
            # Calculate h over the range of xx
            xx = np.linspace(x_min, x_max, 100)
            h = np.zeros_like(xx)
            for i in range(len(xx)):
                h[i] = Koyama2006(xx[i], AS, G, Dh, p)
                
            # Use Simpson's rule to carry out numerical integration to get average h
            if abs(x_max-x_min) < 100*machine_eps:
                # return just one of the edge values
                return h[0]
            else:
                # Use Simpson's rule to carry out numerical integration to get average h
                return simps(h, xx)/(x_max-x_min)

    def Koyama2006_Condensation_dpdz(self, x_min, x_max, AS, G, Di, p, TsatL, TsatV, beta, Afa, Afn, Aa, An):
        ''' from 'Experimental Study on Condensation of Pure Refrigerants in 
        Horizontal Micro-Fin Tube Proposal of Correlations for Heat Transfer 
        Coefficient and Frictional Pressure Drop', Koyama (2006)'''
        
        # ********************************
        #        Necessary Properties
        #    Calculated outside the quadrature integration for speed
        # ********************************
        AS.update(CP.QT_INPUTS, 0.0, TsatL)
        mu_f = AS.viscosity()  # [Pa-s OR kg/m-s]
        cp_f = AS.cpmass()  # [J/kg-K]
        k_f = AS.conductivity()  # [W/m-K]
        rho_f = AS.rhomass()
        Pr_f = cp_f * mu_f / k_f  # [-]
        ST = AS.surface_tension()
        h_f = AS.hmass()
        
        AS.update(CP.QT_INPUTS, 1.0, TsatV)
        mu_g = AS.viscosity()  # [Pa-s OR kg/m-s]
        cp_g = AS.cpmass()  # [J/kg-K]
        k_g = AS.conductivity()  # [W/m-K]
        rho_g = AS.rhomass()
        Pr_g = cp_g * mu_g / k_g  # [-]
        h_g = AS.hmass()
        
        h_GL = h_g - h_f
        
        # friction factor from carnavos
        Fstar = pow(Afa / Afn, 0.5) * pow(1/cos(beta), 0.75)

        def Koyama2006(x, AS, G, Di, p):          
            if (1 - x) < 100*machine_eps:
                Re_g = G * x * Di / mu_g
                f_g = 0.046/pow(Re_g, 0.2)/Fstar
                dpdz_g = 2 * f_g * pow(G, 2) * pow(x, 2) / (Di * rho_g)
                return dpdz_g

            if x < 100*machine_eps:
                Re_f = G * (1 - x) * Di / mu_f
                f_f = 0.046/pow(Re_f, 0.2)/Fstar
                dpdz_f = 2 * f_f * pow(G, 2) * pow((1 - x), 2) / (Di * rho_f)
                return dpdz_f
            
            Re_g = G * x * Di / mu_g
            f_g = 0.046/pow(Re_g, 0.2)/Fstar
            dpdz_g = 2 * f_g * pow(G, 2) * pow(x, 2) / (Di * rho_g)

            Fr = G / pow(9.81 * Di * rho_g * (rho_f - rho_g), 0.5)
                        
            Xtt = pow(mu_f / mu_g, 0.1) * pow(rho_g / rho_f, 0.5) * pow((1 - x) / x, 0.9)
            
            phi_V = 1 + 1.2 * pow(Fr, 0.05) * pow(Xtt, 0.5)
            
            dpdz = dpdz_g * pow(phi_V, 2)
            return dpdz
            
        # Use Simpson's Rule to calculate the average pressure drop
        if abs(x_max-x_min) < 100*machine_eps:
            return Koyama2006(x_min,AS, G, Di, p)
        else:
            # Calculate h over the range of xx
            xx = np.linspace(x_min, x_max, 100)
            dpdz = np.zeros_like(xx)
            for i in range(len(xx)):
                dpdz[i] = Koyama2006(xx[i], AS, G, Di, p)
                
            # Use Simpson's rule to carry out numerical integration to get average h
            if abs(x_max-x_min) < 100*machine_eps:
                # return just one of the edge values
                return dpdz[0]
            else:
                # Use Simpson's rule to carry out numerical integration to get average h
                return simps(dpdz, xx)/(x_max-x_min)
            
    def Gnielinski_1phase_Tube(self,mdot, ID, e_D, h, p, AS, Phase='Single'):
        """ 
        Convenience function to run annular model for tube.  Tube is a degenerate case of annulus with inner diameter of 0

        """
        return self.Gnielinski_1phase_Annulus(mdot, ID, 0.0, e_D, h, p, AS, Phase)  # it was Phase="Single"

    def Gnielinski_1phase_Annulus(self, mdot, OD, ID, e_D, h, p, AS, Phase='Single'):
        """
        calculates single phase heat transfer coefficient with Gnielinski
        """
        AS.update(CP.HmassP_INPUTS,h, p)
        mu = AS.viscosity()  # [Pa-s OR kg/m-s]
        cp = AS.cpmass()  # [J/kg-K]
        rho = AS.rhomass()  # [kg/m^3]
        k = AS.conductivity()  # [W/m-K]
        T_r = AS.T()
        
        if cp < 0:
            # sometimes, negative values of cp appears, so this is an approximation
            AS.update(CP.PT_INPUTS,p,T_r+0.0001)
            cp = (AS.hmass() - h) / (0.0001)

        Pr = cp * mu / k  # [-]
        Dh = OD - ID
        Area = pi*(OD**2-ID**2)/4.0
        u = mdot/(Area*rho)
        Re = rho*u*Dh/mu
        # Friction factor of Churchill (Darcy Friction factor where f_laminar=64/Re)
        A = ((-2.457 * log((7.0 / Re)**(0.9) + 0.27 * e_D)))**16
        B = (37530.0 / Re)**16
        f = 8 * ((8/Re)**12.0 + 1 / (A + B)**(1.5))**(1/12)

        if 3000 < Re and 0.5 < Pr < 2000:
            # Heat Transfer coefficient of Gnielinski
            Nu = (f/8)*(Re-1000)*Pr/(1 + 12.7*sqrt(f/8)*(Pr**(2/3)-1))  # [-]
        elif 0 < Re < 1000:
            # laminar flow with imposed constant heat flux
            Nu = 3.66
        elif 1000 < Re < 3000:
            # Transition, will do linear interpolation of both
            Nu1 = 4.36
            Nu2 = (f / 8) * (Re - 1000.) * Pr / (1 + 12.7 * sqrt(f / 8) * (Pr**(2 / 3) - 1))  # [-]
            Nu = Nu1 + (Re - 1000) * ((Nu2 - Nu1) / (3000 - 1000))
        h = k * Nu / Dh  # W/m^2-K
        return h

    def Churchill_1phase_Tube(self,mdot, ID, e_D, h, p, AS, Phase='Single'):
        """ 
        Convenience function to run annular model for tube.  Tube is a degenerate case of annulus with inner diameter of 0

        """
        return self.Churchill_1phase_Annulus(mdot, ID, 0.0, e_D, h, p, AS, Phase)  # it was Phase="Single"

    def Churchill_1phase_Annulus(self, mdot, OD, ID, e_D, h, p, AS, Phase='Single'):
        """
        Calculates friction factor with Churchill
        """
        AS.update(CP.HmassP_INPUTS,h, p)
        mu = AS.viscosity()  # [Pa-s OR kg/m-s]
        cp = AS.cpmass()  # [J/kg-K]
        rho = AS.rhomass()  # [kg/m^3]
        k = AS.conductivity()  # [W/m-K]
        
        Pr = cp * mu / k  # [-]
        Dh = OD - ID
        Area = pi*(OD**2-ID**2)/4.0
        u = mdot/(Area*rho)
        Re = rho*u*Dh/mu
        # Friction factor of Churchill 
        A = ((-2.457 * log((7.0 / Re)**(0.9) + 0.27 * e_D)))**16
        B = (37530.0 / Re)**16
        f = 8 * ((8/Re)**12.0 + 1 / (A + B)**(1.5))**(1/12)
        return f

    def Haaland_1phase_Tube(self, mdot, Dh, e_D, h, p, AS, Phase='Single'):
        """
        Calculates friction factor with Churchill
        """
        AS.update(CP.HmassP_INPUTS,h, p)
        mu = AS.viscosity()  # [Pa-s OR kg/m-s]
        cp = AS.cpmass()  # [J/kg-K]
        rho = AS.rhomass()  # [kg/m^3]
        k = AS.conductivity()  # [W/m-K]
        
        Pr = cp * mu / k  # [-]
        Area = pi * (Dh**2) / 4.0
        u = mdot/(Area*rho)
        Re = rho*u*Dh/mu
        # Friction factor of Churchill 
        A = -1.8 * log(pow(e_D / 3.7, 1.11) + 6.9 / Re)
        f = pow(1 / A, 2)
        return f

    def Olivier_Condensation_dpdz_average(self,AS, G, P, Tbubble, Tdew, x_min, x_max, Do, n, e, t, d, w, beta, Di, Afa):
        ''' from the paper "Heat transfer, pressure drop, and flow pattern 
                recognition during condensation inside smooth, helical micro-fin, 
                and herringbone tube" by Olivier (2007) 


            the function calculates the average pressur gradient between x_min and x_max
                Do: outer diameter of tube
                n: number of fins
                e: fin thickness
                t: fin thickness + tube thickness
                d: base width of fin
                w: top width of fin
                beta: tube helix angle (radians)
        '''

        def OlivierFunc(x):
            dpdz = self.Olivier_Condensation_dpdz(AS, G, P, Tbubble, Tdew, x, Do, n, e, t, d, w, beta, Di, Afa)
            return dpdz

        # Use Simpson's Rule to calculate the average pressure gradient
        # Can't use adapative quadrature since function is not sufficiently smooth
        # Not clear why not sufficiently smooth at x>0.9
        if abs(x_max-x_min) < 100*machine_eps:
            return OlivierFunc(x_min)
        else:
            # Calculate Dp over the range of xx
            xx = np.linspace(x_min, x_max, 100)
            DP = np.zeros_like(xx)
            for i in range(len(xx)):
                DP[i] = OlivierFunc(xx[i])
            
            # Use Simpson's rule to carry out numerical integration to get average DP and average h
            if abs(x_max-x_min) < 100*machine_eps:
                # return just one of the edge values
                return DP[0]
            else:
                # Use Simpson's rule to carry out numerical integration to get average DP
                return simps(DP, xx)/(x_max-x_min)

    def Olivier_Condensation_dpdz(self, AS, G, P, Tbubble, Tdew, x, Do, n, e, t, d, w, beta, Di, Afa):
        ''' from the paper "Heat transfer, pressure drop, and flow pattern 
                recognition during condensation inside smooth, helical micro-fin, 
                and herringbone tube" by Olivier (2007) 

                Do: outer diameter of tube
                n: number of fins
                e: fin thickness
                t: fin thickness + tube thickness
                d: base width of fin
                w: top width of fin
                beta: tube helix angle (radians)

        '''
        # equivalent diameter
        Deq = pow(4*Afa/pi, 0.5)
        
        # area ratio
        A_An = 1-(2*e*n*(t-e))/(pi*pow(Di, 2)*cos(beta))

        x = float(x)

        # Calculate Necessary saturation properties
        AS.update(CP.QT_INPUTS, 0.0, Tbubble)
        v_f = 1/AS.rhomass()  # [m^3/kg]
        mu_f = AS.viscosity()  # [Pa-s]
        AS.update(CP.QT_INPUTS, 1.0, Tdew)
        v_g = 1/AS.rhomass()  # [m^3/kg]
        mu_g = AS.viscosity()  # [Pa-s]

        # 1. Find the Reynolds Number for each phase based on the actual flow rate of the individual phase
        Re_g = G*x*Di/mu_g
        Re_f = G*(1-x)*Di/mu_f
        
        # 2. Friction factor for each phase
        if x == 1:  # No liquid
            f_f = 0  # Just to be ok until next step
        elif Re_f < 1000:  # Laminar
            f_f = 16/Re_f*(Deq/Di) * pow(A_An, -0.5)*pow(2/cos(beta), 1.1)
        elif Re_f > 2000:  # Fully-Turbulent
            f_f = 0.046/(Re_f**0.2) * (Deq/Di) * pow(A_An, -0.5) * pow(2/cos(beta), 1.1)
        else:  # Mixed
            # Weighting factor
            w = (Re_f-1000)/(2000-1000)
            # Linear interpolation between laminar and turbulent
            f_f = (1-w)*16.0/Re_f*(Deq/Di) * pow(A_An, -0.5)*pow(2/cos(beta), 1.1)+w*0.046/(Re_f**0.2)*(Deq/Di) * pow(A_An, -0.5)*pow(2/cos(beta), 1.1)

        if x == 0:  # No Gas
            f_g = 0  # Just to be ok until next step
        elif Re_g < 1000:  # Laminar
            f_g = 16/Re_g * (Deq/Di) * pow(A_An, -0.5)*pow(2/cos(beta), 1.1)
        elif Re_g > 2000:  # Fully-Turbulent
            f_g = 0.046/(Re_g**0.2) *(Deq/Di) * pow(A_An, -0.5)*pow(2/cos(beta), 1.1)
        else:  # Mixed
            # Weighting factor
            w = (Re_g-1000)/(2000-1000)
            # Linear interpolation between laminar and turbulent
            f_g = (1-w)*16.0/Re_g *(Deq/Di) * pow(A_An, -0.5)*pow(2/cos(beta), 1.1)+w*0.046/(Re_g**0.2) *(Deq/Di) * pow(A_An, -0.5)*pow(2/cos(beta), 1.1)
        # 3. Frictional pressure drop based on actual flow rate of each phase
        dpdz_f = 2*f_f*G**2*(1-x)**2*v_f/Di
        dpdz_g = 2*f_g*G**2*x**2*v_g/Di
        
        if x <= 0:
            # Entirely liquid
            alpha = 0.0
            dpdz = dpdz_f
            return dpdz
        if x >= 1:
            # Entirely vapor
            alpha = 1.0
            dpdz = dpdz_g
            return dpdz
        
        # 4. Lockhart-Martinelli parameter
        X = sqrt(dpdz_f/dpdz_g)
        
        # 5. Two-phase multipliers
        phi_f2 = 1.376 + 7.242 / pow(X, 1.655)
        
        dpdz = dpdz_f * phi_f2
        return dpdz

    def Olivier_Condensation_h_average(self,AS, G, P, Tbubble, Tdew, x_min, x_max, Do, n, e, t, d, w, beta, Di, gama):
        ''' from the paper "Heat transfer, pressure drop, and flow pattern 
                recognition during condensation inside smooth, helical micro-fin, 
                and herringbone tube" by Olivier (2007) 


            the function calculates the average HTC between x_min and x_max
                Do: outer diameter of tube
                n: number of fins
                e: fin thickness
                t: fin thickness + tube thickness
                d: base width of fin
                w: top width of fin
                beta: tube helix angle (degrees)

        '''

        def OlivierFunc(x):
            h = self.Olivier_Condensation_h(AS, G, P, Tbubble, Tdew, x, Do, n, e, t, d, w, beta, Di, gama)
            return h

        # Use Simpson's Rule to calculate the average pressure drop
        if abs(x_max-x_min) < 100*machine_eps:
            return OlivierFunc(x_min)
        else:
            # Calculate h over the range of xx
            xx = np.linspace(x_min, x_max, 100)
            h = np.zeros_like(xx)
            for i in range(len(xx)):
                h[i] = OlivierFunc(xx[i])
                
            # Use Simpson's rule to carry out numerical integration to get average h
            if abs(x_max-x_min) < 100*machine_eps:
                # return just one of the edge values
                return h[0]
            else:
                # Use Simpson's rule to carry out numerical integration to get average h
                return simps(h, xx)/(x_max-x_min)

    def Olivier_Condensation_h(self, AS, G, P, Tbubble, Tdew, x, Do, n, e, t, d, w, beta, Di, gama):
        ''' 
                from the paper "Heat transfer, pressure drop, and flow pattern 
                recognition during condensation inside smooth, helical micro-fin, 
                and herringbone tube" by Olivier (2007) 

                Do: outer diameter of tube
                n: number of fins
                e: fin thickness
                t: fin thickness + tube thickness
                d: base width of fin
                w: top width of fin
                beta: tube helix angle (degrees)

        '''

        x = float(x)
        # find liquid properties
        AS.update(CP.QT_INPUTS, 0.0, Tbubble)
        rho_f = AS.rhomass()  # [kg/m^3]
        mu_f = AS.viscosity()  # [Pa-s OR kg/m-s]
        cp_f = AS.cpmass()  # [J/kg-K]
        k_f = AS.conductivity()  # [W/m-K]
        h_l = AS.hmass()  # [J/kg]
        ST = AS.surface_tension()

        # find vapour properties
        AS.update(CP.QT_INPUTS, 1.0, Tdew)
        rho_g = AS.rhomass()  # [kg/m^3]
        mu_g = AS.viscosity()  # [Pa-s OR kg/m-s]
        cp_g = AS.cpmass()  # [J/kg-K]
        k_g = AS.conductivity()  # [W/m-K]
        h_v = AS.hmass()  # [J/kg]

        # find reynolds number for fluid and vapour separately
        Re_g = G*x*Di/mu_g
        Re_f = G*(1-x)*Di/mu_f

        # find prandtl number of fluid
        Pr_f = cp_f * mu_f / k_f

        # trend factor
        TF = (1-x) + pow(x, 1.3)

        Rx = ((2*e*n*(1-sin(gama/2)))/(pi * Di * cos(gama/2))+1) * \
            pow(cos(beta), -1.0)

        # Bond number
        Bo = 9.81 * rho_f * e * pi * Di / 8 / n / ST

        # Froude number
        u_vo = G / rho_g
        Fr = pow(u_vo, 2)/9.81/Di

        # equivalent reynolds number
        Re_eq = G*(1-x+x*pow(rho_f/rho_g, 0.5))*Di/mu_f

        # heat transfer coefficient
        h = k_f / Di * 0.05 * \
            pow(Re_eq, 0.7) * pow(Pr_f, 1/3) * TF * \
        pow(Rx, 2) * pow(Bo * log(Fr), -0.26)
        
        h *= self.Aa / self.An
        return h

    def Carnavos_single_h(self, AS, G, P, h, Do, n, e, t, d, w, beta, Afa, Afc, An, Aa, Di, Dh):
        ''' 
        from "Heat Transfer Performance of Internally Finned Tubes in
        Turbulent Flow", Carnavos (1980)

        Do: outer diameter of tube
        n: number of fins
        e: fin thickness
        t: fin thickness + tube thickness
        d: base width of fin
        w: top width of fin
        beta: tube helix angle (degrees)
        '''
                
        AS.update(CP.HmassP_INPUTS,h, P)
        mu = AS.viscosity()  # [Pa-s OR kg/m-s]
        cp = AS.cpmass()  # [J/kg-K]
        rho = AS.rhomass()  # [kg/m^3]
        k = AS.conductivity()  # [W/m-K]
        
        G *= Afa / self.Afn
        Pr = cp * mu / k  # [-]
        Re = G * Dh / mu
        F = pow(Afa / Afc, 0.1) * pow(An / Aa, 0.5) * pow(1/cos(beta), 3)
        Nu = 0.023 * pow(Re, 0.8) * pow(Pr, 0.4) * F
        h_single = Nu * k / Dh
        h_single *= Aa / An

        return h_single

    def Carnavos_single_f(self, AS, G, P, h, Do, n, e, t, d, w, beta, Afa, Afn, Di, Dh):
        ''' 
        from "Heat Transfer Performance of Internally Finned Tubes in
        Turbulent Flow", Carnavos (1980)

        Do: outer diameter of tube
        n: number of fins
        e: fin thickness
        t: fin thickness + tube thickness
        d: base width of fin
        w: top width of fin
        beta: tube helix angle (degrees)
        '''

        AS.update(CP.HmassP_INPUTS,h, P)
        mu = AS.viscosity()  # [Pa-s OR kg/m-s]
        G *= Afa / Afn
        Re = G * Di / mu
        Fstar = pow(Afa / Afn, 0.5) * pow(1/cos(beta), 0.75)
        e_D = 0
        A = ((-2.457 * log((7.0 / Re)**(0.9) + 0.27 * e_D)))**16
        B = (37530.0 / Re)**16
        f = 8 * ((8/Re)**12.0 + 1 / (A + B)**(1.5))**(1/12)

        f = f / Fstar
        return f
    
    def Copetti_single_f(self, AS, G, P, h, Do, n, e, t, d, w, beta, Deq):
        ''' 
        from "Experiments with micro-fin tube in single phase", Copetti (2004)

        Do: outer diameter of tube
        n: number of fins
        e: fin thickness
        t: fin thickness + tube thickness
        d: base width of fin
        w: top width of fin
        beta: tube helix angle (degrees)
        '''

        AS.update(CP.HmassP_INPUTS,h, P)
        mu = AS.viscosity()  # [Pa-s OR kg/m-s]
        
        Re = G * Deq / mu
        
        f = 0.014*Re**0.12
        
        return f

    def Copetti_single_h(self, AS, G, P, h, Do, n, e, t, d, w, beta, Deq):
        ''' 
        from "Experiments with micro-fin tube in single phase", Copetti (2004)

        Do: outer diameter of tube
        n: number of fins
        e: fin thickness
        t: fin thickness + tube thickness
        d: base width of fin
        w: top width of fin
        beta: tube helix angle (degrees)
        '''

        AS.update(CP.HmassP_INPUTS, h, P)
        mu = AS.viscosity()  # [Pa-s OR kg/m-s]
        cp = AS.cpmass()  # [J/kg-K]
        rho = AS.rhomass()  # [kg/m^3]
        k = AS.conductivity()  # [W/m-K]
        
        Re = G * Deq / mu
        f = 0.014*Re**0.12
        Pr = cp * mu / k  # [-]
        
        if Re > 1000:    
            Nu = ((f/8)*(Re-1000)*Pr)/(1+(f/8)**0.5*(8.05*Pr**(-0.38)+9.09))
        else:
            Nu = 0.0034*Re**1.1*Pr**0.4
            
        h_single = Nu * k / Deq
        
        return h_single

    def Choi_1999_dpdz(self, AS, G, P, L, xmin, xmax, Dh):
        '''from  J.Y. Choi, M.A. Kedzierski, P. Domanski, A Generalized 
            Pressure Drop Correlation for Evaporation and Condensation of 
            Alternative Refrigerants in Smooth and Microfin Tubes, US 
            Department of Commerce, Technology Administration, National 
            Institute of Standards and Technology, Building and Fire Research 
            Laboratory, 1999.'''
        
        # Calculate Necessary saturation properties
        AS.update(CP.PQ_INPUTS, P, 0.0)
        v_f = 1/AS.rhomass()  # [m^3/kg]
        mu_f = AS.viscosity()  # [Pa-s]
        hf = AS.hmass()
        AS.update(CP.PQ_INPUTS, P, 1.0)
        v_g = 1/AS.rhomass()  # [m^3/kg]
        mu_g = AS.viscosity()  # [Pa-s]
        hg = AS.hmass()
        
        # Calculate specific volumes
        AS.update(CP.PQ_INPUTS, P, xmin)
        v_in = 1 / AS.rhomass()
        AS.update(CP.PQ_INPUTS, P, xmax)
        v_out = 1 / AS.rhomass()        
        
        hfg = hg - hf
                
        Re_LO = G * Dh / mu_f
        
        Kf = (xmax - xmin) * hfg / (L * 9.81)
        
        fN = 0.00506 * pow(Re_LO, -0.0951) * pow(Kf, 0.1554)
        
        dpdz = fN * (v_in + v_out) * pow(G, 2) / Dh
        
        return dpdz

    def Rollmann_2016_dpdz(self, AS, G, P, L, Di, Afa, Aa, xmin, xmax):
        '''from  P. Rollmann, K. Spindler, New models for heat transfer and 
           pressure drop during flow boiling of R407C and R410A in a horizontal 
           microfin tube, Int. J. Therm. Sci. 103 (2016) 57–66.'''
        
        # Calculate Necessary saturation properties
        AS.update(CP.PQ_INPUTS, P, 0.0)
        v_f = 1/AS.rhomass()  # [m^3/kg]
        
        AS.update(CP.PQ_INPUTS, P, 1.0)
        v_g = 1/AS.rhomass()  # [m^3/kg]
        
        Bo = Afa * (xmax - xmin) / (Aa * L)
        
        dpdz = 0.05 * pow(G, 2) / (2 * Di) * ((2 * Bo / Di + xmin) * (v_g - v_f) + v_f)
        
        return dpdz
    
    def Rollmann_2016_h(self, AS, G, Tbubble, Tdew, Di, q_flux, x, An, Aa):
        '''from  P. Rollmann, K. Spindler, New models for heat transfer and 
           pressure drop during flow boiling of R407C and R410A in a horizontal 
           microfin tube, Int. J. Therm. Sci. 103 (2016) 57–66.'''
        
        # calculate necessary liquid properties
        AS.update(CP.QT_INPUTS, 0.0, Tbubble)
        mu_f = AS.viscosity()  # [Pa-s OR kg/m-s]
        cp_f = AS.cpmass()  # [J/kg-K]
        k_f = AS.conductivity()  # [W/m-K]
        h_f = AS.hmass()  # [J/kg]

        # calculate necessary vapor properties
        AS.update(CP.QT_INPUTS, 1.0, Tdew)
        h_v = AS.hmass()  # [J/kg]

        # find specefic heat of vaporization
        h_fv = h_v - h_f
        
        # find Reynolds number
        Re = G * Di / mu_f

        # find boiling number
        Bo = q_flux / (G * h_fv)
        
        # find prandtl number
        Pr = mu_f * cp_f / k_f
        
        # calculate nusselt number
        C1 = -3.7
        C2 = 0.71
        C3 = 12.17
        C4 = 1.2
        Nu = C4 * (C1 / pow(Pr, 2) + C2) * pow(Re, 2 / 3) * (log(Bo) + C3) * pow(x, C1 / pow(Pr, 2) + C2)
        
        # calculate heat transfer coefficient
        h = Nu * k_f / Di
        
        # correction of heat transfer area used in calculating UA
        h *= An / Aa

        return h

    def Wu_2013_h_average(self,AS, G, Tbubble, Tdew, Afa, Di, e, pitch, beta, An, Ac, x_min, x_max, q_flux):
        '''the function calculates the average HTC between x_min and x_max
                n: number of fins
                e: fin thickness
                t: fin thickness + tube thickness
                d: base width of fin
                w: top width of fin
                beta: tube helix angle (radians)
        '''

        def WuFunc(x):
            h = self.Wu_2013_h(AS, G, Tbubble, Tdew, Afa, Di, e, pitch, beta, An, Ac, x, q_flux)
            return h

        # Use Simpson's Rule to calculate the average pressure gradient
        # Can't use adapative quadrature since function is not sufficiently smooth
        # Not clear why not sufficiently smooth at x>0.9
        if abs(x_max-x_min) < 100*machine_eps:
            return WuFunc(x_min)
        else:
            # Calculate Dp over the range of xx
            xx = np.linspace(x_min, x_max, 100)
            h = np.zeros_like(xx)
            for i in range(len(xx)):
                h[i] = WuFunc(xx[i])
            
            # Use Simpson's rule to carry out numerical integration to get average DP and average h
            if abs(x_max-x_min) < 100*machine_eps:
                # return just one of the edge values
                return h[0]
            else:
                # Use Simpson's rule to carry out numerical integration to get average DP
                return simps(h, xx)/(x_max-x_min)

    def Wu_2013_h(self, AS, G, Tbubble, Tdew, Afa, Di, e, pitch, beta, An, Ac, x, q_flux):
        ''' from "Convective vaporization in micro-fin tubes of different 
        geometries" by Wu et al. (2013)'''
        
        # calculate necessary liquid properties
        AS.update(CP.QT_INPUTS, 0.0, Tbubble)
        rho_f = AS.rhomass()
        mu_f = AS.viscosity()  # [Pa-s OR kg/m-s]
        cp_f = AS.cpmass()  # [J/kg-K]
        k_f = AS.conductivity()  # [W/m-K]
        h_f = AS.hmass()  # [J/kg]
        Pr_f = mu_f * cp_f / k_f
        ST = AS.surface_tension()
        
        # calculate necessary vapor properties
        AS.update(CP.QT_INPUTS, 1.0, Tdew)
        rho_g = AS.rhomass()
        h_v = AS.hmass()  # [J/kg]
        
        # calculate latent heat of vaporization
        h_fg = h_v - h_f
        
        # calculate saturation temperature
        T_sat = (1 - x) * Tbubble + x * Tdew

        # calculate void fraction
        epsilon = x / rho_g * pow((1 + 0.12 * (1 - x)) * (x / rho_g + (1 - x) / rho_f) + 1.18 * (1 - x) * pow(9.81 * ST * (rho_f - rho_g), 0.25) / (G * pow(rho_f, 0.5)), -1)

        # calculate film thickness
        delta = sqrt(Afa / pi) * (1 - sqrt(epsilon))

        # calculate reynolds number
        Re_delta = 4 * G * (1 - x) * delta / ((1 - epsilon) * mu_f)
        
        # calculate enhancement factor
        E_rb = pow(1 + pow(2.64 * pow(Re_delta, 0.036) * pow(Pr_f, -0.024) * pow(e / Di, 0.212) * pow(pitch / Di, -0.21) * pow(beta / pi * 2, 0.29), 7), 1 / 7)
        
        # calculate h_cb_f
        h_cb_f = 0.014 * pow(Re_delta, 0.68) * pow(Pr_f, 0.4) * k_f / delta
        
        # calculate Q_onb
        q_onb = 2 * ST * T_sat * E_rb * h_cb_f / (0.38 * 1e-6 * rho_g * h_fg)
                
        if abs(q_flux) > q_onb: # the absolute is just to prevent raising an error if flux was negative due to a segment with condensation instead of boiling (most likely in first iterations of solution)
            # calculate departure bubble diameter
            D_b = 0.51 * pow(2 * ST / (9.81 * (rho_f - rho_g)), 0.5)

            # calculate epi
            epi = 1.96 * 1e-5 * pow(rho_f / rho_g * cp_f / h_fg * T_sat, 1.25) * (E_rb * h_cb_f) * D_b / k_f
        
            # calculate nucleat boiling correction factor
            S = 1 / epi * (1 - exp(-epi))

            # calculate h_pb
            h_pb = 2.8 * 207 * k_f / D_b * pow((abs(q_flux) - q_onb) * D_b / (k_f * T_sat), 0.745) * pow(rho_g / rho_f, 0.581) * pow(Pr_f, 0.533)

        else:
            h_pb = 0
            S = 0
            
        # calculate h
        h = pow(pow(E_rb * h_cb_f, 3) + pow(S * h_pb, 3), 1 / 3)
        
        h *= self.Aa / self.An
        return h

    def Wu_2013_dpdz_average(self,AS, G, Tbubble, Tdew, Di, e, beta, x_min, x_max):
        '''the function calculates the average pressur gradient between x_min and x_max
                n: number of fins
                e: fin thickness
                t: fin thickness + tube thickness
                d: base width of fin
                w: top width of fin
                beta: tube helix angle (radians)
        '''

        def WuFunc(x):
            ''' from "Convective vaporization in micro-fin tubes of different 
            geometries" by Wu et al. (2013)'''
            
            # calculate necessary liquid properties
            AS.update(CP.QT_INPUTS, 0.0, Tbubble)
            rho_f = AS.rhomass()
            mu_f = AS.viscosity()  # [Pa-s OR kg/m-s]

            # calculate necessary vapor properties
            AS.update(CP.QT_INPUTS, 1.0, Tdew)
            rho_g = AS.rhomass()
            mu_g = AS.viscosity()  # [Pa-s OR kg/m-s]
            
            # calculate two phase density
            rho_tp = 1 / (x / rho_g + (1 - x) / rho_f)
            
            # calculate two phase viscosity
            mu_tp = mu_f - 2.5 * mu_f * pow(x * rho_f / (x * rho_f + (1 - x) * rho_g), 2) + (x * rho_f * (1.5 * mu_f + mu_g)) / (x * rho_f + (1 - x) * rho_g)
    
            # calculate two phase reynolds number
            Re_tp = G * Di / mu_tp
            
            # calculate microfin roughness factor
            R_xf = 0.18 * (e / Di) / (0.1 + cos(beta))
            
            # calculate friction factor parameters
            a = pow(2.457 * log(1 / (pow(7 / Re_tp, 0.9) + 0.27 * R_xf)), 16)
            b = pow(37530 / Re_tp, 16)
        
            # calculate two phase friction factor
            # the 1.61399354 is calculated from the paper by fitting the experimental data in the paper with the calculated values from the correlation to get least sum RMSE
            f_tp =  2 * pow(pow(8 / Re_tp, 12) + 1 / pow(a + b, 3 / 2), 1 / 12)

            # calculate frictional pressure drop gradient
            dpdz_f = 2 * f_tp * pow(G, 2) / (Di * rho_tp)
            
            return dpdz_f

        # Use Simpson's Rule to calculate the average pressure gradient
        # Can't use adapative quadrature since function is not sufficiently smooth
        # Not clear why not sufficiently smooth at x>0.9
        if abs(x_max-x_min) < 100*machine_eps:
            return WuFunc(x_min)
        else:
            # Calculate Dp over the range of xx
            xx = np.linspace(x_min, x_max, 100)
            DP = np.zeros_like(xx)
            for i in range(len(xx)):
                DP[i] = WuFunc(xx[i])
            
            # Use Simpson's rule to carry out numerical integration to get average DP and average h
            if abs(x_max-x_min) < 100*machine_eps:
                # return just one of the edge values
                return DP[0]
            else:
                # Use Simpson's rule to carry out numerical integration to get average DP
                return simps(DP, xx)/(x_max-x_min)        
    
    def chen_2018_h_7_14mm(self, AS, G, Tbubble, Tdew, Dh, Di, An, Aa, x):
        '''from "Correlation of Evaporation Heat Transfer Inside 8.8 mm and 
            7.14 mm Horizontal Round Micro-Fin Tubes" by chen et al. (2018)'''
        # calculate necessary liquid properties
        AS.update(CP.QT_INPUTS, 0.0, Tbubble)
        rho_f = AS.rhomass()
        mu_f = AS.viscosity()  # [Pa-s OR kg/m-s]
        cp_f = AS.cpmass()  # [J/kg-K]
        k_f = AS.conductivity()  # [W/m-K]
        
        # calculate necessary vapor properties
        AS.update(CP.QT_INPUTS, 1.0, Tdew)
        rho_g = AS.rhomass()
        mu_g = AS.viscosity()
        
        # calculating reynolds number
        Re_f = G * Dh * (1 - x) / mu_f
        
        # calculating Prandtl number
        Pr_f = cp_f * mu_f / k_f
        
        # calculating epsilon
        epsilon = Dh / Di
        
        # calculating lockhart-martenilli parameter
        Xtt = pow((1 - x) / x, 0.9) * pow(rho_g / rho_f, 0.5) * pow(mu_f / mu_g, 0.1)
        
        # calculating Nusselt number
        Nu = (0.97 * epsilon - 0.23) * pow(Re_f, 0.5) * pow(1.55 - x, 0.96) * pow(Pr_f / Xtt, 1.09)
        
        # calculating heat transfer coefficient
        h = Nu * k_f / Dh
                
        # correction of heat transfer area used in calculating UA
        h *= An / Aa
        
        return h

    def chen_2018_h_8_8mm(self, AS, G, Tbubble, Tdew, Dh, Di, An, Aa, x):
        '''from "Correlation of Evaporation Heat Transfer Inside 8.8 mm and 
            7.14 mm Horizontal Round Micro-Fin Tubes" by chen et al. (2018)'''
        # calculate necessary liquid properties
        AS.update(CP.QT_INPUTS, 0.0, Tbubble)
        rho_f = AS.rhomass()
        mu_f = AS.viscosity()  # [Pa-s OR kg/m-s]
        cp_f = AS.cpmass()  # [J/kg-K]
        k_f = AS.conductivity()  # [W/m-K]
        
        # calculate necessary vapor properties
        AS.update(CP.QT_INPUTS, 1.0, Tdew)
        rho_g = AS.rhomass()
        mu_g = AS.viscosity()

        # calculating reynolds number
        Re_f = G * Dh * (1 - x) / mu_f
        
        # calculating Prandtl number
        Pr_f = cp_f * mu_f / k_f
        
        # calculating epsilon
        epsilon = Dh / Di
        
        # calculating lockhart-martenilli parameter
        Xtt = pow((1 - x) / x, 0.9) * pow(rho_g / rho_f, 0.5) * pow(mu_f / mu_g, 0.1)
        
        # calculating Nusselt number
        Nu = (-0.394 * epsilon + 0.307) * pow(Re_f, 0.7) * pow(1.55 - x, 0.96) * pow(Pr_f / Xtt, 1.09)
        
        # calculating heat transfer coefficient
        h = Nu * k_f / Dh
                
        # correction of heat transfer area used in calculating UA
        h *= An / Aa
        
        return h
        
    def Wongsangam_2004_h(self, AS, G, Tbubble, Tdew, Di, q_flux, x, An, Aa):
        '''from  "Performance of smooth and micro-fin tubes in high mass flux 
        region of R-134a during evaporation" by Wongsangam et al (2004)'''
        
        # calculate necessary liquid properties
        AS.update(CP.QT_INPUTS, 0.0, Tbubble)
        mu_f = AS.viscosity()  # [Pa-s OR kg/m-s]
        cp_f = AS.cpmass()  # [J/kg-K]
        k_f = AS.conductivity()  # [W/m-K]
        h_f = AS.hmass()  # [J/kg]
        rho_f = AS.rhomass()

        # calculate necessary vapor properties
        AS.update(CP.QT_INPUTS, 1.0, Tdew)
        h_v = AS.hmass()  # [J/kg]
        rho_g = AS.rhomass()
        mu_g = AS.viscosity()

        # find specefic heat of vaporization
        h_fv = h_v - h_f

        # find boiling number
        Bo = q_flux / (G * h_fv)
        
        # calculate Reynolds number
        Re = G * Di / mu_f
        
        # calculate Prandtl number
        Pr = cp_f * mu_f / k_f
        
        # calculate hlo
        h_lo = 0.023 * pow(Re, 0.8) * pow(Pr, 0.4) * (k_f / Di)
        
        # calculate lockhart martenilli parameter
        Xtt = pow((1 - x) / x, 0.9) * pow(rho_g / rho_f, 0.5) * pow(mu_f / mu_g, 0.1)
        
        # calculate heat transfer coefficient
        h = 5.5864 * h_lo * pow(Bo * 1e4, 0.35) * pow(Xtt, -0.14)
        
        # correction of heat transfer area used in calculating UA
        h *= An / Aa
        
        return h

if __name__ == '__main__':
    def fun1():
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
    
    def fun2(h_corr,Pr_range,prop):
        class ValuesClass():
            pass
        AS = CP.AbstractState("HEOS", "R22")
        geometry = ValuesClass()
        geometry.OD = 0.007
        geometry.inner_circum = 1
        
        # smooth tube
        # geometry.Tubes_type = "Smooth"
        geometry.Tubes_type = "Microfin"
        
        if geometry.Tubes_type == "Smooth":
            geometry.ID = 0.006
            geometry.Dh = geometry.ID
            geometry.e_D = 0
            geometry.A_CS = pi / 4 * geometry.ID**2
        elif geometry.Tubes_type == "Microfin":
            geometry.t = 0.0001
            geometry.e = 0.00005
            geometry.d = 0.00003
            geometry.w = 0.000018
            geometry.n = 54
            geometry.beta = 26
            geometry.gama = 30
            geometry.A_CS = pi / 4 * (geometry.OD - (geometry.t-geometry.e))**2
        
        # dummy thermal class
        thermal = ValuesClass()
        
        # ref properties
        x = 0.5
        G = 200
        A_r = 1
        mode = "heater"
        # mode = "cooler"
        q_flux = 1e4
        if geometry.Tubes_type == "Smooth":
            mdot_r = G * pi / 4 * geometry.ID**2
        elif geometry.Tubes_type == "Microfin":
            mdot_r = G * pi / 4 * (geometry.OD - (geometry.t-geometry.e))**2
        
        corr = CorrelationsClass()
        corr.impose_h_2phase(h_corr)
        Pr = np.linspace(Pr_range[0],Pr_range[1],100)
        prop_range = []
        h = []
        for Pr_i in Pr:
            P_i = AS.p_critical() * Pr_i
            corr.update(AS,geometry,thermal,"2phase",P_i,x,mdot_r,A_r,mode,q_flux)
            h.append(corr.calculate_h_2phase())
            if "_f" in prop:
                prop_name = prop.replace("_f","")
                AS.update(CP.PQ_INPUTS,P_i,0)
                value = getattr(AS,prop_name)()
                prop_range.append(value)
            elif "_g" in prop:
                prop_name = prop.replace("_g","")
                AS.update(CP.PQ_INPUTS,P_i,1)
                value = getattr(AS,prop_name)()
                prop_range.append(value)
                
        return (prop_range,h)
        
    prop = "surface_tension_f"
    P_reduced = (0.25,0.75)
    h_corr = 1
    result = fun2(h_corr=h_corr,Pr_range=P_reduced,prop=prop)
    import matplotlib.pyplot as plt
    plt.plot(result[0],result[1])
    plt.xlabel(prop)
    plt.ylabel("HTC (W/m2.K)")
    