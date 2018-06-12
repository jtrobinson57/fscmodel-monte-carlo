# -*- coding: utf-8 -*-
"""
Created on Thu Jun  7 13:49:17 2018

@author: j.robinson
"""

from __future__ import division
from pyomo.environ import *
from pyomo.opt import SolverFactory
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

class Source:
    def __init__(self,name,energyType,capex=0,opex=0,CO2 = 0):
        self.name = name
        self.energyType = energyType
        self.capex = capex
        self.opex = opex
        self.CO2 = CO2
        self.outcons = []
    
    def __str__(self):
        return "Source:" + self.name + ", " + self.energyType
    
    def __lt__(self,other):
        if isinstance(other, Source):
            return self.name < other.name


class Sink:
    def __init__(self,name,capex,opex,energyType,demand):
        self.name = name
        self.energyType = energyType
        self.capex = capex
        self.opex = opex
        self.demand = demand
        self.incons = []
        
    def __str__(self):
        return "Sink:" + self.name + ", " + self.energyType
    
    def __lt__(self,other):
        if isinstance(other, Sink):
            return self.name < other.name
    
class Transformer:
    def __init__(self,name,inp,capex=0,opex=0,totalEff=0):
        self.name = name
        self.inp = inp
        self.capex = capex
        self.opex = opex
        self.totalEff = totalEff
        self.products = {}
        self.incons = []
        self.outcons = []
    
    def __str__(self):
        return "Transformer:" + self.name
    
    def __lt__(self,other):
        if isinstance(other, Transformer):
            return self.name < other.name

class Connection:
    def __init__(self,name,inp,out,energyType):
        self.name = name
        self.inp = inp
        self.out = out
        self.energyType = energyType
    
    def __lt__(self,other):
        if isinstance(other, Connection):
            return self.name < other.name
    def __str__(self):
        return "Connection:" + self.name + ", " + self.energyType


SourceIn    = pd.read_excel('input.xlsx', 'Sources', index_col=None, na_values=['NA'])
SinkIn      = pd.read_excel('input.xlsx', 'Sinks', index_col=None, na_values=['NA'])
TransIn     = pd.read_excel('input.xlsx', 'Transformers', index_col=None, na_values=['NA'])
ConnIn      = pd.read_excel('input.xlsx', 'Connectors', index_col=None, na_values=['NA'])

SourceList = []
SinkList   = []
TransList  = []
ConnList   = []
FuelTypeList = []
DemandTypeList = []

#Energy sources available
for i in range(len(SourceIn.index)):
    if not SourceIn.loc[i,'EnergyType'] in FuelTypeList:
        FuelTypeList.append(SourceIn.loc[i,'EnergyType'])
        
#Energy types demanded        
for i in range(len(SinkIn.index)):
    if not SinkIn.loc[i, 'EnergyType'] in DemandTypeList:
        DemandTypeList.append(SinkIn.loc[i, 'EnergyType'])

for i in range(len(SourceIn.index)):
    SourceList.append(Source(name = SourceIn.loc[i,'Name'],
                             energyType = SourceIn.loc[i,'EnergyType'],
                             capex=SourceIn.loc[i,'Capex'], 
                             opex = SourceIn.loc[i,'Opex'], 
                             CO2 = SourceIn.loc[i,'CO2']))

for i in range(len(SinkIn.index)):
    SinkList.append(Sink(name = SinkIn.loc[i,'Name'],
                         energyType = SinkIn.loc[i,'EnergyType'],
                         capex = SinkIn.loc[i,'Capex'],
                         opex = SinkIn.loc[i,'Opex'],
                         demand = SinkIn.loc[i,'Demand']))

for i in range(len(TransIn.index)):
    TransList.append(Transformer(name = TransIn.loc[i,'Name'],
                                 inp = TransIn.loc[i,'Input'],
                                 capex = TransIn.loc[i,'Capex'],
                                 opex = TransIn.loc[i,'Opex'],
                                 totalEff = TransIn.loc[i,'TotalEff']))
    
    k = 0
    x = 0
    for j in range(len(TransIn.loc[i,'Prod0':])):
        if k % 2 == 0 and isinstance(TransIn.loc[i,'Prod'+str(x)],str):
            TransList[i].products[TransIn.loc[i,'Prod'+str(x)]] = TransIn.loc[i,'SubEff'+str(x)]
            x = x + 1
        k = k + 1

for i in range(len(ConnIn.index)):
    ConnList.append(Connection(name = ConnIn.loc[i,'Name'],
                              inp = ConnIn.loc[i,'In'],
                              out = ConnIn.loc[i,'Out'],
                              energyType = ConnIn.loc[i,'EnergyType']))
    
for fac in SourceList:
    for con in ConnList:
        if con.inp==fac.name and con.energyType==fac.energyType:
            fac.outcons.append(con)

for fac in SinkList:
    for con in ConnList:
        if con.out==fac.name and con.energyType==fac.energyType:
            fac.incons.append(con)

for fac in TransList:
    for con in ConnList:
        if con.out==fac.name and con.energyType==fac.inp:
            fac.incons.append(con)
        elif con.inp==fac.name and con.energyType in fac.products:
            fac.outcons.append(con)


def createModel(SourceList, SinkList, TransList, ConnList, CO2 = 40):
    M = ConcreteModel()
    
    M.connectors = Set(initialize = ConnList) #Ordered allows you to access by number, not sure if necessary.
    M.c = Param(M.connectors, mutable = True)
    M.carbon = Param(M.connectors, mutable = True)
    M.sources = Set(initialize = SourceList)
    M.sinks = Set(initialize = SinkList)
    M.trans = Set(initialize = TransList)
    
#    #For the amount in facilities, for calculating Opex. capex will be added to objective
#    M.facilities = Var(M.stations, domain = NonNegativeReals)
    #Amount going through connectors
    M.connections = Var(M.connectors, domain = NonNegativeReals)
    #Amount coming out of a transformer
    M.trouttotals = Var(M.trans, domain = NonNegativeReals)
    
    #Constructs cost vector and carbon constraints. Right now only coming from sources.
    #may have to add other types later
    for con in M.connectors:
        added = False
        for fac in M.sources:
            if con in fac.outcons:
                M.c[con] = fac.opex
                M.carbon[con] = fac.CO2 
                added = True
        if not added:
            M.c[con] = 0
            M.carbon[con] = 0
    
    
    def transrule(model, tra):
        return M.trouttotals[tra] == tra.totalEff * sum(M.connections[con] for con in tra.incons)
    
    def productratiorule(model, con):
        for tra in TransList:
            if con in tra.outcons:
                etype = con.energyType
                return tra.products[etype] * M.trouttotals[tra] == M.connections[con]
        return Constraint.Skip


    def sinkrule(model, sink):
        return sum(M.connections[con] for con in M.connectors and sink.incons) == sink.demand
    
    
    def objrule(model):
       ob = summation(model.connections,model.c, index=M.connectors)
       return ob

    M.productconstraint = Constraint(M.connectors, rule = productratiorule)
    
    M.transconstraint = Constraint(M.trans, rule = transrule)
    
    M.sinkconstraint = Constraint(M.sinks, rule = sinkrule)
    
    M.Co2limit = Constraint(expr = summation(M.connections,M.carbon,index = M.connectors) <= CO2)
            
    M.Obj = Objective(rule = objrule, sense = minimize)
    
            
    return M

def opti(model):
    opt = SolverFactory('gurobi')
    results = opt.solve(model, tee = True)
    print(model.display())
    return results


def checkModel():
    return None


model = createModel(SourceList, SinkList, TransList, ConnList, CO2 = 40)

results = opti(model)


#Output formatting starts here

outMJ = [0] * len(FuelTypeList)

for i in range(len(ConnList)):
    for j in range(len(FuelTypeList)):
        if ConnList[i].energyType == FuelTypeList[j]:
            outMJ[j] = outMJ[j] + model.connections[ConnList[i]].value

outdf = pd.DataFrame({'Fuel Type' : FuelTypeList,
                             'MJ by Fuel' : outMJ,
                             'Total System Cost' : model.Obj()})
    
for i in range(1,len(outdf.index)):
    outdf.at[i,'Total System Cost'] = np.nan

outdf.to_excel('output.xlsx', sheet_name='Sheet1')
