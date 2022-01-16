from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import numpy as np
from CoolProp.Plots import PropertyPlot
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import CoolProp as CP
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import warnings
from GUI_functions import load_refrigerant_list

class values():
    pass

class PlotsWidget(QWidget):
    def __init__(self, Cycle, mode, parent=None):
        super(PlotsWidget, self).__init__(parent)

        if mode == "AC":
            condenser_name = "Outdoor Unit"
            evaporator_name = "Indoor Unit"
        elif mode == "HP":
            condenser_name = "Indoor Unit"
            evaporator_name = "Outdoor Unit"

        Widgets_list = []
        
        # PH diagram tab
        Widgets_list.append(["PH diagram",Plot_PH(Cycle.Ref,Cycle.Results.States_matrix[:,0],Cycle.Results.States_matrix[:,2],evaporator_name,condenser_name)])
        
        # TS diagram tab
        Widgets_list.append(["TS diagram",Plot_TS(Cycle.Ref,Cycle.Results.States_matrix[:,1],Cycle.Results.States_matrix[:,3],evaporator_name,condenser_name)])
        
        # charge Distribution tab
        charge_list = [Cycle.Evaporator.Results.Charge,
                       Cycle.Condenser.Results.Charge,
                       Cycle.Line_Suction.Results.Charge,
                       Cycle.Line_Discharge.Results.Charge,
                       Cycle.Line_Liquid.Results.Charge,
                       Cycle.Line_2phase.Results.Charge,
                       ]
        names = [evaporator_name, condenser_name, 'Suction Line', 'Dishcarge Line', 'Liquid Line', 'Two-phase Line']
        Widgets_list.append(["Charge Distribution",Plot_pie(charge_list,names,"Charge","kg",4)])
        
        # power distribution tab
        power_list = [Cycle.Evaporator.Fan.power,
                       Cycle.Condenser.Fan.power,
                       Cycle.Compressor.power_elec,
                       ]
        names = [evaporator_name+' Fan', condenser_name+' Fan', 'Compressor']
        Widgets_list.append(["Electric Power Distribution",Plot_pie(power_list,names,"electric power","W",2)])
        
        # compressor efficiencies tab
        Compressor_efficiencies_list = [Cycle.Compressor.eta_isen*100,
                                        Cycle.Compressor.eta_v*100,
                                        Cycle.Compressor.Elec_eff*100,
                                        ]
        names = ['Isentropic Efficiency', 'Volumetric Efficiency', 'Electric Efficiency']
        Widgets_list.append(["Compressor Efficiencies",Plot_bar(Compressor_efficiencies_list,names,"Efficiency (%)",2,"%",(0,100))])

        # pressure drop tab
        pressure_drop_list = [abs(Cycle.Evaporator.Results.DP_r),
                              abs(Cycle.Condenser.Results.DP_r),
                              abs(Cycle.Line_Suction.Results.DP_r),
                              abs(Cycle.Line_Discharge.Results.DP_r),
                              abs(Cycle.Line_Liquid.Results.DP_r),
                              abs(Cycle.Line_2phase.Results.DP_r),
                              ]
        names = [evaporator_name, condenser_name, 'Suction Line', 'Dishcarge Line', 'Liquid Line', 'Two-phase Line']
        Widgets_list.append(["Refrigerant Pressure Drop Distribution",Plot_pie(pressure_drop_list,names,"refrigerant pressure drop","Pa",2)])

        # Entropy Generation Tab
        names = [evaporator_name, condenser_name, 'Compressor', 'Suction Line', 'Dishcarge Line', 'Liquid Line', 'Two-phase Line']
        S_gen_list = [abs(Cycle.Evaporator.Results.S_gen),
                      abs(Cycle.Condenser.Results.S_gen),
                      abs(Cycle.Compressor.S_gen),
                      abs(Cycle.Line_Suction.Results.S_gen),
                      abs(Cycle.Line_Discharge.Results.S_gen),
                      abs(Cycle.Line_Liquid.Results.S_gen),
                      abs(Cycle.Line_2phase.Results.S_gen),
                      ]
        if hasattr(Cycle,"Capillary"):
            S_gen_list.append(abs(Cycle.Capillary.Results.S_gen))
            names.append("Capillary Tube")    
        Widgets_list.append(["Entropy Generation",Plot_pie(S_gen_list,names,"entropy generation","W/K",3)])

        # condenser tab
        Widgets_list.append([condenser_name,Plot_HX(Cycle.Condenser)])
        
        # evaporator tab
        Widgets_list.append([evaporator_name,Plot_HX(Cycle.Evaporator)])
        
        # create layout
        self.layout = QVBoxLayout()
  
        # Initialize tab screen 
        self.tabs = QTabWidget() 
        
        for Widget in Widgets_list:
            Widget_tab = QWidget()
            
            # Add tab 
            self.tabs.addTab(Widget_tab, Widget[0]) 
    
            # Create Cycle tab 
            Widget_tab.layout = QHBoxLayout() 
            Widget_tab.layout.addWidget(Widget[1]) 
            Widget_tab.setLayout(Widget_tab.layout) 
            
        # Add tabs to widget
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

class PlotsParamWidget(QWidget):
    def __init__(self, outputs, mode, parent=None):
        super(PlotsParamWidget, self).__init__(parent)

        if mode == "AC":
            condenser_name = "Outdoor Unit"
            evaporator_name = "Indoor Unit"
        elif mode == "HP":
            condenser_name = "Indoor Unit"
            evaporator_name = "Outdoor Unit"
        Widgets_list = []
        '''
        # PH diagram tab
        Widgets_list.append(["PH diagram",Plot_PH(Cycle.Ref,Cycle.Results.States_matrix[:,0],Cycle.Results.States_matrix[:,2],evaporator_name,condenser_name)])
        
        # TS diagram tab
        Widgets_list.append(["TS diagram",Plot_TS(Cycle.Ref,Cycle.Results.States_matrix[:,1],Cycle.Results.States_matrix[:,3],evaporator_name,condenser_name)])
        
        # charge Distribution tab
        charge_list = [Cycle.Evaporator.Results.Charge,
                       Cycle.Condenser.Results.Charge,
                       Cycle.Line_Suction.Results.Charge,
                       Cycle.Line_Discharge.Results.Charge,
                       Cycle.Line_Liquid.Results.Charge,
                       Cycle.Line_2phase.Results.Charge,
                       ]
        names = [evaporator_name, condenser_name, 'Suction Line', 'Dishcarge Line', 'Liquid Line', 'Two-phase Line']
        Widgets_list.append(["Charge Distribution",Plot_pie(charge_list,names,"Charge","kg",4)])
        
        # power distribution tab
        power_list = [Cycle.Evaporator.Fan.power,
                       Cycle.Condenser.Fan.power,
                       Cycle.Compressor.power_elec,
                       ]
        names = [evaporator_name+' Fan', condenser_name+' Fan', 'Compressor']
        Widgets_list.append(["Electric Power Distribution",Plot_pie(power_list,names,"electric power","W",2)])
        
        # compressor efficiencies tab
        Compressor_efficiencies_list = [Cycle.Compressor.eta_isen*100,
                                        Cycle.Compressor.eta_v*100,
                                        Cycle.Compressor.Elec_eff*100,
                                        ]
        names = ['Isentropic Efficiency', 'Volumetric Efficiency', 'Electric Efficiency']
        Widgets_list.append(["Compressor Efficiencies",Plot_bar(Compressor_efficiencies_list,names,"Efficiency (%)",2,"%",(0,100))])

        # pressure drop tab
        pressure_drop_list = [abs(Cycle.Evaporator.Results.DP_r),
                              abs(Cycle.Condenser.Results.DP_r),
                              abs(Cycle.Line_Suction.Results.DP_r),
                              abs(Cycle.Line_Discharge.Results.DP_r),
                              abs(Cycle.Line_Liquid.Results.DP_r),
                              abs(Cycle.Line_2phase.Results.DP_r),
                              ]
        names = [evaporator_name, condenser_name, 'Suction Line', 'Dishcarge Line', 'Liquid Line', 'Two-phase Line']
        Widgets_list.append(["Refrigerant Pressure Drop Distribution",Plot_pie(pressure_drop_list,names,"refrigerant pressure drop","Pa",2)])

        # Entropy Generation Tab
        names = [evaporator_name, condenser_name, 'Compressor', 'Suction Line', 'Dishcarge Line', 'Liquid Line', 'Two-phase Line']
        S_gen_list = [abs(Cycle.Evaporator.Results.S_gen),
                      abs(Cycle.Condenser.Results.S_gen),
                      abs(Cycle.Compressor.S_gen),
                      abs(Cycle.Line_Suction.Results.S_gen),
                      abs(Cycle.Line_Discharge.Results.S_gen),
                      abs(Cycle.Line_Liquid.Results.S_gen),
                      abs(Cycle.Line_2phase.Results.S_gen),
                      ]
        if hasattr(Cycle,"Capillary"):
            S_gen_list.append(abs(Cycle.Capillary.Results.S_gen))
            names.append("Capillary Tube")    
        Widgets_list.append(["Entropy Generation",Plot_pie(S_gen_list,names,"entropy generation","W/K",3)])

        # condenser tab
        Widgets_list.append([condenser_name,Plot_HX(Cycle.Condenser)])
        
        # evaporator tab
        Widgets_list.append([evaporator_name,Plot_HX(Cycle.Evaporator)])
        
        # create layout
        self.layout = QVBoxLayout()
  
        # Initialize tab screen 
        self.tabs = QTabWidget() 
        
        for Widget in Widgets_list:
            Widget_tab = QWidget()
            
            # Add tab 
            self.tabs.addTab(Widget_tab, Widget[0]) 
    
            # Create Cycle tab 
            Widget_tab.layout = QHBoxLayout() 
            Widget_tab.layout.addWidget(Widget[1]) 
            Widget_tab.setLayout(Widget_tab.layout) 
            
        # Add tabs to widget
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)
        '''
class Plot_PH(QWidget):
    def __init__(self, Ref,P_list,h_list,evaporator_name,condenser_name, parent=None):
        super(Plot_PH, self).__init__(parent)
        sc = MplCanvas(width=5, height=4)
        try:
            ref_list = load_refrigerant_list()
            if ref_list[0]:
                ref_list = ref_list[1]
            else:
                raise
            mass_fractions = ref_list[ref_list[:,0] == Ref][0,2]
            ref_names = ref_list[ref_list[:,0] == Ref][0,1]
            ref_name_list = [ref_names[i]+"["+str(mass_fractions[i])+"]" for i in range(len(ref_names))]
            Ref_name = "&".join(ref_name_list)
            plot = PropertyPlot("REFPROP::"+Ref_name, 'ph',tp_limits='ACHP',axis=sc.axes)
            Ref_name = "&".join(ref_list[ref_list[:,0] == Ref][0,1])
            mass_fractions = ref_list[ref_list[:,0] == Ref][0,2]
            AS = CP.AbstractState("REFPROP", Ref_name) # defining abstract state
            if not len(mass_fractions) == 1:
                AS.set_mass_fractions(mass_fractions)
            succeeded = True
        except:
            import traceback
            print(traceback.format_exc())
            try:
                plot = PropertyPlot(Ref, 'ph',tp_limits='ACHP',axis=sc.axes)
                AS = CP.AbstractState("HEOS",Ref)
                succeeded = True
            except:
                succeeded = False
        if succeeded:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                plot.calc_isolines(CP.iQ)
            plot.draw_isolines()
            for i in range(8):
                sc.axes.plot(h_list[i]/1000,P_list[i]/1e3,'o')
                if i%2==0:
                    sc.axes.annotate(str(i+1), (h_list[i]/1000,P_list[i]/1e3),horizontalalignment='right', verticalalignment='top')
                else:
                    sc.axes.annotate(str(i+1), (h_list[i]/1000,P_list[i]/1e3),horizontalalignment='left', verticalalignment='bottom')
                    
            for i in range(8):
                if i < 7:
                    sc.axes.plot([h_list[i]/1000,h_list[i+1]/1000],[P_list[i]/1e3,P_list[i+1]/1e3],'-',color="blue")
                else:
                    sc.axes.plot([h_list[i]/1000,h_list[0]/1000],[P_list[i]/1e3,P_list[0]/1e3],'-',color="blue")
            Pmax = AS.p_critical()
            sc.axes.set_xlim([min(h_list/1000)*0.8,max(h_list/1000)*1.2])
            sc.axes.set_ylim([min(P_list/1e3)*0.7,max(Pmax/1e3,max(P_list/1e3))*1.2])
            sc.axes.set_xlabel("Specific enthalpy (kJ/kg)")
            sc.axes.set_ylabel("Pressure (MPa)")
            logfmt = FuncFormatter(lambda x, pos: '{0:g}'.format(x/1000))
            sc.axes.yaxis.set_major_formatter(logfmt)
            sc.axes.yaxis.set_minor_formatter(logfmt)
            sc.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            label = QLabel()
            label.setText("<p>1 -> 2   (Discharge Line)</p><p>2 -> 3   ("+condenser_name+")</p><p>3 -> 4   (Liquid Line)</p><p>4 -> 5   (Throttling Device)</p><p>5 -> 6   (Two-phase Line)</p><p>6 -> 7   ("+evaporator_name+")</p><p>7 -> 8   (Suction Line)</p><p>8 -> 1   (Compressor)</p>")
            
            table = QTableWidget(2,len(P_list))
            table.setHorizontalHeaderLabels([str(i+1) for i in range(len(P_list))])
            table.setVerticalHeaderLabels(["Pressure (MPa)","Enthalpy (kJ/kg"])
            table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    
            for i in range(len(P_list)):
                P = P_list[i]/1e6
                h = h_list[i]/1000
                table.setItem(0,i,QTableWidgetItem("%.5g" % P))
                table.setItem(1,i,QTableWidgetItem("%.5g" % h))
                
            table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
            table.resizeColumnsToContents()
            table.verticalHeader().setStretchLastSection(True)
            
            self.layout = QVBoxLayout()
            layout0 = QHBoxLayout()
            layout1 = QHBoxLayout()
            layout1.addWidget(label)        
            layout1.addStretch()
            layout2 = QHBoxLayout()
            layout2.addWidget(sc)
            layout2.addStretch()
            layout0.addLayout(layout1)
            layout0.addLayout(layout2)
            self.layout.addLayout(layout0)
            layout3 = QHBoxLayout()
            layout3.addWidget(table)
            self.layout.addLayout(layout3)
            self.layout.addStretch()
            self.setLayout(self.layout) 

class Plot_TS(QWidget):
    def __init__(self, Ref,T_list,S_list,evaporator_name,condenser_name, parent=None):
        super(Plot_TS, self).__init__(parent)
        sc = MplCanvas(width=5, height=4)
        try:
            ref_list = load_refrigerant_list()
            if ref_list[0]:
                ref_list = ref_list[1]
            else:
                raise
            mass_fractions = ref_list[ref_list[:,0] == Ref][0,2]
            ref_names = ref_list[ref_list[:,0] == Ref][0,1]
            ref_name_list = [ref_names[i]+"["+str(mass_fractions[i])+"]" for i in range(len(ref_names))]
            Ref_name = "&".join(ref_name_list)
            plot = PropertyPlot("REFPROP::"+Ref_name, 'ts',tp_limits='ACHP',axis=sc.axes)
            Ref_name = "&".join(ref_list[ref_list[:,0] == Ref][0,1])
            mass_fractions = ref_list[ref_list[:,0] == Ref][0,2]
            AS = CP.AbstractState("REFPROP", Ref_name) # defining abstract state
            if not len(mass_fractions) == 1:
                AS.set_mass_fractions(mass_fractions)
            succeeded = True
        except:
            import traceback
            print(traceback.format_exc())
            try:
                plot = PropertyPlot(Ref, 'ts',tp_limits='ACHP',axis=sc.axes)
                AS = CP.AbstractState("HEOS",Ref)
                succeeded = True
            except:
                succeeded = False
        if succeeded:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                plot.calc_isolines(CP.iQ)
            plot.draw_isolines()
            sc.axes.plot(T_list,S_list/1000,'o')
            for i in range(8):
                sc.axes.plot(S_list[i]/1000,T_list[i],'o')
                if i%2==0:
                    sc.axes.annotate(str(i+1), (S_list[i]/1000,T_list[i]),horizontalalignment='right', verticalalignment='top')
                else:
                    sc.axes.annotate(str(i+1), (S_list[i]/1000,T_list[i]),horizontalalignment='left', verticalalignment='bottom')
                    
            for i in range(8):
                if i < 7:
                    sc.axes.plot([S_list[i]/1000,S_list[i+1]/1000],[T_list[i],T_list[i+1]],'-',color="blue")
                else:
                    sc.axes.plot([S_list[i]/1000,S_list[0]/1000],[T_list[i],T_list[0]],'-',color="blue")
            Tmax = AS.T_critical()
            sc.axes.set_xlim([min(S_list/1000)*0.8,max(S_list/1000)*1.2])
            sc.axes.set_ylim([min(T_list)*0.7,max(Tmax,max(T_list))*1.2])
            sc.axes.set_xlabel("Specific entropy (kJ/kg.K)")
            sc.axes.set_ylabel("Temperature ($^\circ$K)")
            
            sc.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    
            label = QLabel()
            label.setText("<p>1 -> 2   (Discharge Line)</p><p>2 -> 3   ("+condenser_name+")</p><p>3 -> 4   (Liquid Line)</p><p>4 -> 5   (Throttling Device)</p><p>5 -> 6   (Two-phase Line)</p><p>6 -> 7   ("+evaporator_name+")</p><p>7 -> 8   (Suction Line)</p><p>8 -> 1   (Compressor)</p>")
    
            table = QTableWidget(2,len(T_list))
            table.setHorizontalHeaderLabels([str(i+1) for i in range(len(T_list))])
            table.setVerticalHeaderLabels(["Temperature (K)","Entropy (kJ/kg.K"])
            table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            
            for i in range(len(T_list)):
                table.setItem(0,i,QTableWidgetItem("%.5g" % T_list[i]))
                S = S_list[i]/1000
                table.setItem(1,i,QTableWidgetItem("%.5g" % S))
                
            table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
            table.resizeColumnsToContents()
            table.verticalHeader().setStretchLastSection(True)
            
            self.layout = QVBoxLayout()
            layout0 = QHBoxLayout()
            layout1 = QHBoxLayout()
            layout1.addWidget(label)        
            layout1.addStretch()
            layout2 = QHBoxLayout()
            layout2.addWidget(sc)
            layout2.addStretch()
            layout0.addLayout(layout1)
            layout0.addLayout(layout2)
            self.layout.addLayout(layout0)
            layout3 = QHBoxLayout()
            layout3.addWidget(table)
            self.layout.addLayout(layout3)
            self.layout.addStretch()
            self.setLayout(self.layout) 

class Plot_pie(QWidget):
    def __init__(self,values_list,names,title,unit,accuracy,show_total=True, parent=None):
        super(Plot_pie, self).__init__(parent)
        sc = MplCanvas(width=5, height=4)
        total = np.sum(values_list)
        values_list = list(values_list)
        for i,item in enumerate(values_list):
            if item == 0:
                values_list[i] = -1
                names[i] = -1
        not_yet = True
        while not_yet:
            if -1 in values_list:
                values_list.remove(-1)
                names.remove(-1)
            else:
                not_yet = False
        explode = [0.1 for i in range(len(names))]
        values_list = np.abs(np.array(values_list))
        while all(values_list < 1):
            values_list *= 10
        sc.axes.pie(values_list,labels=names,autopct='%1.2f%%',explode = explode)
        sc.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        label = QLabel()
        if show_total:
            label.setText("<h2>Total "+title+": "+str(round(total,accuracy))+" "+unit+"</h2>")
        self.layout = QVBoxLayout()
        layout1 = QHBoxLayout()
        layout1.addStretch()
        layout1.addWidget(sc)
        layout1.addStretch()
        layout2 = QHBoxLayout()
        layout2.addStretch()
        layout2.addWidget(label)
        layout2.addStretch()
        self.layout.addLayout(layout1)
        self.layout.addLayout(layout2)
        self.setLayout(self.layout)

class Plot_Compressor_Efficiencies(QWidget):
    def __init__(self,Compressor_Efficiencies,names, parent=None):
        super(Plot_Compressor_Efficiencies, self).__init__(parent)
        sc = MplCanvas(width=5, height=4)
        Compressor_Efficiencies = np.array(Compressor_Efficiencies)
        sc.axes.bar(names,Compressor_Efficiencies,0.4,color=["orange","blue","green"])
        sc.axes.set_ylim([0,100])
        sc.axes.set_ylabel("Efficiency (%)")
        for i, v in enumerate(Compressor_Efficiencies):
            sc.axes.text(i,v*0.5, str(round(v,2))+" %", color='black', fontweight='bold',horizontalalignment="center")
        sc.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.layout = QVBoxLayout()
        layout1 = QHBoxLayout()
        layout1.addStretch()
        layout1.addWidget(sc)        
        layout1.addStretch()
        self.layout.addLayout(layout1)
        self.setLayout(self.layout)

class Plot_bar(QWidget):
    def __init__(self,values_list,names,y_label,accuracy,unit,y_lim=None, parent=None):
        super(Plot_bar, self).__init__(parent)
        sc = MplCanvas(width=5, height=4)
        values_list = list(values_list)
        for i,item in enumerate(values_list):
            if item == 0:
                values_list[i] = -1
                names[i] = -1
        not_yet = True
        while not_yet:
            if -1 in values_list:
                values_list.remove(-1)
                names.remove(-1)
            else:
                not_yet = False
        colors = []
        for i in range(len(values_list)):
            colors.append(plt.cm.brg(i/len(values_list)))
        sc.axes.bar(names,values_list,0.4,color=colors)
        if not y_lim is None:
            sc.axes.set_ylim(y_lim)
        sc.axes.set_ylabel(y_label)
        for i, v in enumerate(values_list):
            sc.axes.text(i,v*0.5, str(round(v,accuracy))+" "+unit, color='black', fontweight='bold',horizontalalignment="center")
        sc.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.layout = QVBoxLayout()
        layout1 = QHBoxLayout()
        layout1.addStretch()
        layout1.addWidget(sc)        
        layout1.addStretch()
        self.layout.addLayout(layout1)
        self.setLayout(self.layout)

class Plot_HX(QWidget):
    def __init__(self, HX, parent=None):
        super(Plot_HX, self).__init__(parent)
        Widgets_list = []
        
        Capacity_list = [abs(HX.Results.Q_superheat),
                         abs(HX.Results.Q_2phase),
                         abs(HX.Results.Q_subcool),]
        Widgets_list.append(["Capacity Distribution",Plot_pie(Capacity_list,["Superheated","Two-phase","Subcooled"],"capacity","W",2)])
        Refrigerant_Pressure_Drop_list = [abs(HX.Results.DP_r_superheat),
                                          abs(HX.Results.DP_r_2phase),
                                          abs(HX.Results.DP_r_subcool),]
        Widgets_list.append(["Ref Pressure Drop Distribution",Plot_pie(Refrigerant_Pressure_Drop_list,["Superheated","Two-phase","Subcooled"],"refrigerant pressure drop","Pa",2)])
        Area_fraction_list = [abs(HX.Results.w_superheat*100),
                              abs(HX.Results.w_2phase*100),
                              abs(HX.Results.w_subcool*100),]
        Widgets_list.append(["Heat Exchanger Area Distribution",Plot_pie(Area_fraction_list,["Superheated","Two-phase","Subcooled"],"Area","m^2",2,show_total=False)])
        Refrigerant_HTC_list = [abs(HX.Results.h_r_superheat),
                                abs(HX.Results.h_r_2phase),
                                abs(HX.Results.h_r_subcool),]
        Widgets_list.append(["Ref HTC",Plot_bar(Refrigerant_HTC_list,["Superheated","Two-phase","Subcooled"],"HTC (W/m.K)",2,"")])
        
        # create layout
        self.layout = QVBoxLayout()
  
        # Initialize tab screen 
        self.tabs = QTabWidget() 
        
        for Widget in Widgets_list:
            Widget_tab = QWidget()
            
            # Add tab 
            self.tabs.addTab(Widget_tab, Widget[0]) 
    
            # Create Cycle tab 
            Widget_tab.layout = QHBoxLayout() 
            Widget_tab.layout.addWidget(Widget[1]) 
            Widget_tab.setLayout(Widget_tab.layout) 
            
        # Add tabs to widget 
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout) 

def zero_to_nan(sample):
    return [np.nan if x==0 else x for x in sample]


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, width=5, height=5):
        self.fig = Figure()
        self.axes = self.fig.add_subplot(111)
        self.fig.subplots_adjust(0.1, 0.1, 0.95, 0.95) 
        super(MplCanvas, self).__init__(self.fig)
        