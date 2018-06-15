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
    def __init__(self,name,energyType,capex,opexMin,opexAvg,opexMax,CO2,minProd,maxProd):
        self.name = name
        self.energyType = energyType
        self.capex = capex
        self.opex = 0
        self.opexMin = opexMin
        self.opexAvg = opexAvg
        self.opexMax = opexMax
        self.CO2 = CO2
        self.outcons = []
        self.minProd = minProd
        self.maxProd = maxProd
    
    def __str__(self):
        return "Source:" + self.name + ", " + self.energyType
    
    def __lt__(self,other):
        if isinstance(other, Source):
            return self.name < other.name


class Sink:
    def __init__(self,name,capex,opexMin,opexAvg,opexMax,energyType,demand):
        self.name = name
        self.energyType = energyType
        self.capex = capex
        self.opex = 0
        self.opexMin = opexMin
        self.opexAvg = opexAvg
        self.opexMax = opexMax
        self.demand = demand
        self.incons = []
        
    def __str__(self):
        return "Sink:" + self.name + ", " + self.energyType
    
    def __lt__(self,other):
        if isinstance(other, Sink):
            return self.name < other.name
    
class Transformer:
    def __init__(self,name,capex,opexMin,opexAvg,opexMax,totalEffMin,totalEffAvg,totalEffMax):
        self.name = name
        self.capex = capex
        self.opex = 0
        self.opexMin = opexMin
        self.opexAvg = opexAvg
        self.opexMax = opexMax
        self.totalEff = 0
        self.totalEffMin = totalEffMin
        self.totalEffAvg = totalEffAvg
        self.totalEffMax = totalEffMax
        self.inputs = {}
        self.products = {}
        self.incons = []
        self.outcons = []
    
    def __str__(self):
        return "Transformer:" + self.name
    
    def __lt__(self,other):
        if isinstance(other, Transformer):
            return self.name < other.name
        
class Hub:
    def __init__(self,name,energyType,capex,opexMin,opexAvg,opexMax):
        self.name = name
        self.energyType = energyType
        self.capex = capex
        self.opex = 0
        self.opexMin = opexMin
        self.opexAvg = opexAvg
        self.opexMax = opexMax
        self.incons = []
        self.outcons = []
    
    def __str__(self):
        return "Hub:" + self.name + ", " + self.energyType
    
    def __lt__(self,other):
        if isinstance(other, Hub):
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

def createModel(SourceList, SinkList, TransList, ConnList, HubList, CO2):
    M = ConcreteModel()
    
    M.connectors = Set(initialize = ConnList)
    M.sources = Set(initialize = SourceList)
    M.sinks = Set(initialize = SinkList)
    M.trans = Set(initialize = TransList)
    M.hubs = Set(initialize = HubList)
    M.stations = Set(initialize = SourceList + SinkList + TransList + HubList)
    
    M.c = Param(M.stations, mutable = True)
    M.carbon = Param(M.sources, mutable = True)
    M.cape = Param(M.stations, mutable = True)
    
    #For the amount in facilities, for calculating Opex. For transformer, the amount coming out
    M.facilities = Var( M.stations, domain = NonNegativeReals)
    #Whether a facility is being used. For calculating Capex
    M.isopen = Var(M.stations, domain = Boolean)
    #Amount going through connectors
    M.connections = Var(M.connectors, domain = NonNegativeReals)
    #Amount coming into a transformer. Used to consider transformer production ratio
    M.trintotals = Var(M.trans, domain = NonNegativeReals)
    
    #Populates capex costs
    for fac in M.stations:
        M.cape[fac]=fac.capex
    
    #Constructs cost vector from opex and carbon constraints from sources.
    for fac in M.stations:
        M.c[fac] = fac.opex
        if isinstance(fac, Source):
            M.carbon[fac] = fac.CO2
    
    
    def sourcecount(model, source):
        return M.facilities[source] == sum(M.connections[con] for con in source.outcons)
    
    M.sourcesum = Constraint(M.sources, rule = sourcecount)
    
    for source in M.sources:
        M.facilities[source].setub(source.maxProd)
        M.facilities[source].setlb(source.minProd)
    
    def transrule(model, tra):
        return M.facilities[tra] == tra.totalEff * M.trintotals[tra]
    
    def transcount(model, tra):
        return M.trintotals[tra] ==  sum(M.connections[con] for con in tra.incons)
    
    def inputratiorule(model, con):
        for tra in TransList:
            if con in tra.incons:
                return tra.inputs[con.energyType] * M.trintotals[tra] == M.connections[con]
        return Constraint.Skip
     
    def productratiorule(model, con):
        for tra in TransList:
            if con in tra.outcons:
                etype = con.energyType
                return tra.products[etype] * M.facilities[tra] == M.connections[con]
        return Constraint.Skip

    M.transconstraint = Constraint(M.trans, rule = transrule)
    M.transsum = Constraint(M.trans, rule = transcount)
    M.inputconstraint = Constraint(M.connectors, rule = inputratiorule)
    M.productconstraint = Constraint(M.connectors, rule = productratiorule)
    
    
    def sinkrule(model, sink):
        return sum(M.connections[con] for con in sink.incons) == sink.demand
    
    def sinkcount(model,sink):
        return M.facilities[sink]== sum(M.connections[con] for con in sink.incons)
    
    M.sinkconstraint = Constraint(M.sinks, rule = sinkrule)
    M.sinksum = Constraint(M.sinks, rule = sinkcount)
    
    
    def hubrule(model, hub):
        return sum(M.connections[con] for con in hub.incons)==sum(M.connections[con] for con in hub.outcons)
    
    def hubcount(model,hub):
        return M.facilities[hub] == sum(M.connections[con] for con in hub.incons)
    
    M.hubconstraint = Constraint(M.hubs, rule = hubrule)
    M.hubsum = Constraint(M.hubs, rule = hubcount)
    
    #Quadratic constraint that turns isopen on and off
    def binrule(model, fac):
        return M.facilities[fac] - M.isopen[fac]*M.facilities[fac] <= 0
    
    M.checkopen = Constraint(M.stations, rule = binrule)


    M.Co2limit = Constraint(expr = summation(M.facilities,M.carbon,index = M.sources) <= CO2)    
        
    def objrule(model):
       ob = summation(model.facilities,model.c, index=M.stations) + summation(model.cape, model.isopen, index=M.stations)
       return ob
            
    M.Obj = Objective(rule = objrule, sense = minimize)
            
    return M

def opti(model):
    opt = SolverFactory('gurobi')
    results = opt.solve(model, tee = True)
    print(model.display())
    return results


def checkModel(ConnList, entypes):
    for con in ConnList:
        if con.energyType not in entypes:
            raise ValueError(str(con) + ' has an unrecognized energy type.')
    
        
    #What more can be added?
    return None

def randomizeOpex(List):
    
    for i in List:
        while True:
            i.opex = np.random.normal(i.opexAvg,((i.opexMax-i.opexMin)/6))
            if i.opex >= i.opexMin and i.opex <= i.opexMax:
                break

def randomizeEff(List):
    
    for i in List:
        while True:
            i.totalEff = np.random.normal(i.totalEffAvg,((i.totalEffMax-i.totalEffMin)/6))
            if i.totalEff >= i.totalEffMin and i.totalEff <= i.totalEffMax:
                break

#int main



SourceIn    = pd.read_excel('input.xlsx', 'Sources', index_col=None, na_values=['NA'])
SinkIn      = pd.read_excel('input.xlsx', 'Sinks', index_col=None, na_values=['NA'])
TransIn     = pd.read_excel('input.xlsx', 'Transformers', index_col=None, na_values=['NA'])
HubIn      = pd.read_excel('input.xlsx', 'Hubs', index_col=None, na_values=['NA'])
ConnIn      = pd.read_excel('input.xlsx', 'Connectors', index_col=None, na_values=['NA'])
RestrIn      = pd.read_excel('input.xlsx', 'Restrictions', index_col=None, na_values=['NA'])

SourceList = []
SinkList   = []
TransList  = []
HubList    = []
ConnList   = []
FuelTypeList = []
DemandTypeList = []

#Import restrictions, just CO2 for now
CO2Max = RestrIn.loc[0,'CO2 Max']

#Energy sources available from sources
for i in range(len(SourceIn.index)):
    if not SourceIn.loc[i,'EnergyType'] in FuelTypeList:
        FuelTypeList.append(SourceIn.loc[i,'EnergyType'])
        
#Energy types demanded at sinks     
for i in range(len(SinkIn.index)):
    if not SinkIn.loc[i, 'EnergyType'] in DemandTypeList:
        DemandTypeList.append(SinkIn.loc[i, 'EnergyType'])

#All energy types 
EnergyList = FuelTypeList + DemandTypeList

#Initialize the connectors        
for i in range(len(ConnIn.index)):
    ConnList.append(Connection(name = ConnIn.loc[i,'Name'],
                              inp = ConnIn.loc[i,'In'],
                              out = ConnIn.loc[i,'Out'],
                              energyType = ConnIn.loc[i,'EnergyType']))

#Initialize the Sources
for i in range(len(SourceIn.index)):
    SourceList.append(Source(name = SourceIn.loc[i,'Name'],
                             energyType = SourceIn.loc[i,'EnergyType'],
                             capex = SourceIn.loc[i,'Capex'], 
                             opexMin = SourceIn.loc[i,'OpexMin'],
                             opexAvg = SourceIn.loc[i,'OpexAvg'],
                             opexMax = SourceIn.loc[i,'OpexMax'],
                             CO2 = SourceIn.loc[i,'CO2'],
                             minProd = SourceIn.loc[i,'MinProduction'],
                             maxProd = SourceIn.loc[i, 'MaxProduction']))
    
    for con in ConnList:
        if con.inp==SourceList[i].name and con.energyType==SourceList[i].energyType:
            SourceList[i].outcons.append(con)

#Initialize the sinks
for i in range(len(SinkIn.index)):
    SinkList.append(Sink(name = SinkIn.loc[i,'Name'],
                         energyType = SinkIn.loc[i,'EnergyType'],
                         capex = SinkIn.loc[i,'Capex'],
                         opexMin = SinkIn.loc[i,'OpexMin'],
                         opexAvg = SinkIn.loc[i,'OpexAvg'],
                         opexMax = SinkIn.loc[i,'OpexMax'],
                         demand = SinkIn.loc[i,'Demand']))
    
    for con in ConnList:
        if con.out==SinkList[i].name and con.energyType==SinkList[i].energyType:
            SinkList[i].incons.append(con)

#Initialize the transfomers
for i in range(len(TransIn.index)):
    TransList.append(Transformer(name = TransIn.loc[i,'Name'],
                                 capex = TransIn.loc[i,'Capex'],
                                 opexMin = TransIn.loc[i,'OpexMin'],
                                 opexAvg = TransIn.loc[i,'OpexAvg'],
                                 opexMax = TransIn.loc[i,'OpexMax'],
                                 totalEffMin = TransIn.loc[i,'TotalEffMin'],
                                 totalEffAvg = TransIn.loc[i,'TotalEffAvg'],
                                 totalEffMax = TransIn.loc[i,'TotalEffMax']))
    
    k = 0
    x = 0
    
    for j in range(len(TransIn.loc[i,'Input0':'Prod0'])-1):
        x = int(j/2)
        inp = TransIn.loc[i,'Input'+str(x)]       
        if k % 2 == 0 and isinstance(inp,str):
            if not inp in EnergyList:
                EnergyList.append(inp)
            TransList[i].inputs[inp] = TransIn.loc[i,'InRatio'+str(x)]
        k = k + 1
        
    k = 0
    x = 0
    
    for j in range(len(TransIn.loc[i,'Prod0':])):
        product = TransIn.loc[i,'Prod'+str(x)]       
        if k % 2 == 0 and isinstance(product,str):
            if not product in EnergyList:
                EnergyList.append(product)
            TransList[i].products[product] = TransIn.loc[i,'SubEff'+str(x)]
            x = x + 1
        k = k + 1
 
    for con in ConnList:
        if con.out==TransList[i].name and con.energyType in TransList[i].inputs:
            TransList[i].incons.append(con)
        elif con.inp==TransList[i].name and con.energyType in TransList[i].products:
            TransList[i].outcons.append(con)

 #Initialize the Hubs   
for i in range(len(HubIn.index)):
    HubList.append(Hub(name = HubIn.loc[i,'Name'],
                       energyType = HubIn.loc[i,'EnergyType'],
                       capex = HubIn.loc[i,'Capex'],
                       opexMin = HubIn.loc[i,'OpexMin'],
                       opexAvg = HubIn.loc[i,'OpexAvg'],
                       opexMax = HubIn.loc[i,'OpexMax']))
    
    for con in ConnList:
        if con.out==HubList[i].name and con.energyType==HubList[i].energyType:
            HubList[i].incons.append(con)
        elif con.inp==HubList[i].name and con.energyType==HubList[i].energyType:
            HubList[i].outcons.append(con)
    
numIter = RestrIn.loc[0,'NumIterations']
objList = np.zeros(numIter)
fuelQuantity = np.zeros((numIter,len(FuelTypeList)))

checkModel(ConnList, EnergyList)

for i in range(numIter):
    
    randomizeOpex(SourceList)
    randomizeOpex(SinkList)
    randomizeOpex(TransList)
    randomizeOpex(HubList)
    
    randomizeEff(TransList)
    
    model = createModel(SourceList, SinkList, TransList, ConnList, HubList, CO2 = CO2Max)
    
    results = opti(model)
    
    #Output formatting starts here

    objList[i] = model.Obj()
    
    for j in range(len(ConnList)):
        for k in range(len(FuelTypeList)):
            if ConnList[j].energyType == FuelTypeList[k]:
                fuelQuantity[i,k] = fuelQuantity[i,k] + model.connections[ConnList[k]].value
       
outdf = pd.DataFrame({'Total System Cost' : objList
                      })
    
outdf.to_excel('output.xlsx', sheet_name='Sheet1')


#return 0