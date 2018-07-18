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
    def __init__(self, name, energyType, capex, opexMin, opexAvg, opexMax, CO2, isSet, usageMin, usageAvg, usageMax):
        self.name = name
        self.energyType = energyType
        self.capex = capex
        self.opex = 0
        self.opexMin = opexMin
        self.opexAvg = opexAvg
        self.opexMax = opexMax
        self.CO2 = CO2
        self.isSet = isSet
        self.usage = 0
        self.usageMin = usageMin
        self.usageAvg = usageAvg
        self.usageMax = usageMax
        self.outcons = []
    
    def __str__(self):
        return "Source:" + self.name + ", " + self.energyType
    
    def __lt__(self,other):
        if isinstance(other, Source):
            return self.name < other.name


class Sink:
    def __init__(self,name,capex,opexMin,opexAvg,opexMax,energyType,demandMin,demandAvg,demandMax):
        self.name = name
        self.energyType = energyType
        self.capex = capex
        self.opex = 0
        self.opexMin = opexMin
        self.opexAvg = opexAvg
        self.opexMax = opexMax
        self.demand = 0
        self.demandMin = demandMin
        self.demandAvg = demandAvg
        self.demandMax = demandMax
        self.incons = []
        
    def __str__(self):
        return "Sink:" + self.name + ", " + self.energyType
    
    def __lt__(self,other):
        if isinstance(other, Sink):
            return self.name < other.name
    
class Transformer:
    def __init__(self,name,capex,opexMin,opexAvg,opexMax,totalEffMin,totalEffAvg,totalEffMax,outMin,outMax):
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
        self.outMin = outMin
        self.outMax = outMax
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
    M.facilities = Var(M.stations, domain = NonNegativeReals)
    #Whether a facility is being used. For calculating Capex
    M.isopen = Var(M.stations, domain = Boolean)
    #Amount going through connectors
    M.connections = Var(M.connectors, domain = NonNegativeReals)
    #Amount coming into a transformer. Used to consider transformer production ratio
    M.trintotals = Var(M.trans, domain = NonNegativeReals)
    
    M.carbonsum = Var(domain = NonNegativeReals)
    
    #Populates capex costs
    for fac in M.stations:
        M.cape[fac] = fac.capex
    
    #Constructs cost vector from opex and carbon constraints from sources.
    for fac in M.stations:
        M.c[fac] = fac.opex
        if isinstance(fac, Source):
            M.carbon[fac] = fac.CO2
    
    
    def sourcecount(model, source):
        return M.facilities[source] == sum(M.connections[con] for con in source.outcons)
    
    M.sourcesum = Constraint(M.sources, rule = sourcecount)
    
    for source in M.sources:
        if source.isSet:
            M.facilities[source].setub(source.usage)
            M.facilities[source].setlb(source.usage)

    
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
    
    for tran in M.trans:
        M.facilities[tran].setub(tran.outMax)
        M.facilities[tran].setlb(tran.outMin)
    
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
    
    M.carbonset = Constraint(expr = summation(M.facilities, M.carbon, index = M.sources) == M.carbonsum)


    M.Co2limit = Constraint(expr = M.carbonsum <= CO2)    
        
    def objrule(model):
       ob = summation(model.facilities, model.c, index = M.stations) + summation(model.cape, model.isopen, index = M.stations)
       return ob
            
    M.Obj = Objective(rule = objrule, sense = minimize)
            
    return M

def opti(model):
    model.preprocess()
    opt = SolverFactory('gurobi', tee = True)
    results = opt.solve(model)
    #print(model.display())
    return results


def checkModel(ConnList, entypes):
    for con in ConnList:
        if con.energyType not in entypes:
            raise ValueError(str(con) + ' has an unrecognized energy type.')
            
    for Source in SourceList:
        if not Source.outcons:
            print('\nWARNING: ' + Source.name + ' has empty out connections, so it probably is not being used. Would you like to check that?' + '\n')
        
    #What more can be added?
    return None

def randomizeOpex(List, row, dataout):
    
    if(distr == 'normal'):
        for i in List:
            while True:
                i.opex = np.random.normal(i.opexAvg,((i.opexMax - i.opexMin)/6))
                if i.opex >= i.opexMin and i.opex <= i.opexMax:
                    break
            dataout.at[row, i.name + 'opex'] = i.opex
            
    elif(distr == 'rayleigh'):
        for i in List:
            midp = (i.opexMax - i.opexMin) / 2 
            if(i.opexAvg < (midp + i.opexMin)):
                mode = (i.opexAvg - i.opexMin) * np.sqrt(2 / np.pi)
                while True:
                    i.opex = np.random.rayleigh(mode)
                    i.opex = i.opex + i.opexMin
                    if i.opex >= i.opexMin and i.opex <= i.opexMax:
                        break
            elif(i.opexAvg >= (midp + i.opexMin)):
                mode = (i.opexMax - i.opexAvg) * np.sqrt(2 / np.pi)
                while True:
                    i.opex = np.random.rayleigh(mode)
                    i.opex = i.opexMax - i.opex
                    if i.opex >= i.opexMin and i.opex <= i.opexMax:
                        break
            dataout.at[row, i.name + 'opex'] = i.opex
            
            
def randomizeEff(List, row, dataout):
    
    if(distr == 'normal'):
        for i in List:
            while True:
                i.totalEff = np.random.normal(i.totalEffAvg, ((i.totalEffMax - i.totalEffMin)/6))
                if i.totalEff >= i.totalEffMin and i.totalEff <= i.totalEffMax:
                    break
            dataout.at[row, i.name + 'TotalEff'] = i.totalEff
            
    elif(distr == 'rayleigh'):
        for i in List:
            midp = (i.totalEffMax - i.totalEffMin) / 2 
            if(i.totalEffAvg < (midp + i.totalEffMin)):
                mode = (i.totalEffAvg - i.totalEffMin) * np.sqrt(2 / np.pi)
                while True:
                    i.totalEff = np.random.rayleigh(mode)
                    i.totalEff = i.totalEff + i.totalEffMin
                    if i.totalEff >= i.totalEffMin and i.totalEff <= i.totalEffMax:
                        break
            elif(i.totalEffAvg >= (midp + i.totalEffMin)):
                mode = (i.totalEffMax - i.totalEffAvg) * np.sqrt(2 / np.pi)
                while True:
                    i.totalEff = np.random.rayleigh(mode)
                    i.totalEff = i.totalEffMax - i.totalEff
                    if i.totalEff >= i.totalEffMin and i.totalEff <= i.totalEffMax:
                        break
            dataout.at[row, i.name + 'TotalEff'] = i.totalEff
            
def randomizeDem(List, row, dataout):
    
    if(distr == 'normal'):
        for i in List:
            while True:
                i.demand = np.random.normal(i.demandAvg, ((i.demandMax - i.demandMin)/6))
                if i.demand >= i.demandMin and i.demand <= i.demandMax:
                    break
            dataout.at[row, i.name+'Demand'] = i.demand
            
    elif(distr == 'rayleigh'):
        for i in List:
            midp = (i.demandMax - i.demandMin) / 2
            if(i.demandAvg < (midp + i.demandMin)):
                mode = (i.demandAvg - i.demandMin) * np.sqrt(2 / np.pi)
                while True:
                    i.demand = np.random.rayleigh(mode)
                    i.demand = i.demand + i.demandMin
                    if i.demand >= i.demandMin and i.demand <= i.demandMax:
                        break
            elif(i.demandAvg >= (midp + i.demandMin)):
                mode = (i.demandMax - i.demandAvg) * np.sqrt(2 / np.pi)
                while True:
                    i.demand = np.random.rayleigh(mode)
                    i.demand = i.demandMax - i.demand
                    if i.demand >= i.demandMin and i.demand <= i.demandMax:
                        break
            dataout.at[row, i.name + 'Demand'] = i.demand

def randomizeUsage(List, row, dataout):
    
    if (distr == 'normal'):
        for i in List:
            if i.isSet:
                dataout.at[row, i.energyType + 'isFixed'] = i.isSet
                while True:
                    i.usage = np.random.normal(i.usageAvg, ((i.usageMax - i.usageMin)/6)) 
                    if i.usage >= i.usageMin and i.usage <= i.usageMax:
                        break
                    
    if(distr == 'rayleigh'):
        for i in List:
            midp = (i.usageMax - i.usageMin) / 2
            if(i.usageAvg < (midp + i.usageMin)):
                mode = (i.usageAvg - i.usageMin) * np.sqrt(2 / np.pi)
                if i.isSet:
                    dataout.at[row, i.energyType + 'isFixed'] = i.isSet
                    while True:
                        i.usage = np.random.rayleigh(mode)
                        i.usage = i.usage + i.usageMin
                        if i.usage >= i.usageMin and i.usage <= i.usageMax:
                            break
            elif(i.usageAvg >= (midp + i.usageMin)):
                mode = (i.usageMax - i.usageAvg) * np.sqrt(2 / np.pi)
                if i.isSet:
                    dataout.at[row, i.energyType + 'isFixed'] = i.isSet
                    while True:
                        i.usage = np.random.rayleigh(mode)
                        i.usage = i.usageMax - i.usage
                        if i.usage >= i.usageMin and i.usage <= i.usageMax:
                            break

        
#int main

SourceIn  = pd.read_excel('input.xlsx', 'Sources', index_col=None, na_values=['NA'])
SinkIn    = pd.read_excel('input.xlsx', 'Sinks', index_col=None, na_values=['NA'])
TransIn   = pd.read_excel('input.xlsx', 'Transformers', index_col=None, na_values=['NA'])
HubIn     = pd.read_excel('input.xlsx', 'Hubs', index_col=None, na_values=['NA'])
ConnIn    = pd.read_excel('input.xlsx', 'Connectors', index_col=None, na_values=['NA'])
RestrIn   = pd.read_excel('input.xlsx', 'Restrictions', index_col=None, na_values=['NA'])

SourceList = []
SinkList   = []
TransList  = []
HubList    = []
ConnList   = []
FuelTypeList = []
DemandTypeList = []
outcolumns = ['Total Cost', 'CO2']

#Import restrictions
CO2Max = RestrIn.loc[0, 'CO2 Max']
distr = RestrIn.loc[0, 'Distribution']
numIter = int(RestrIn.loc[0, 'NumIterations'])

#Energy sources available from sources
for i in range(len(SourceIn.index)):
    if not SourceIn.loc[i, 'EnergyType'] in FuelTypeList:
        FuelTypeList.append(SourceIn.loc[i, 'EnergyType'])
        outcolumns.append(SourceIn.loc[i, 'EnergyType'])
        outcolumns.append(SourceIn.loc[i, 'EnergyType'] + 'isFixed')
        
#Energy types demanded at sinks     
for i in range(len(SinkIn.index)):
    if not SinkIn.loc[i, 'EnergyType'] in DemandTypeList:
        DemandTypeList.append(SinkIn.loc[i, 'EnergyType'])

#All energy types 
EnergyList = FuelTypeList + DemandTypeList


#Initialize the connectors        
for i in range(len(ConnIn.index)):
    ConnList.append(Connection(name = ConnIn.loc[i, 'Name'],
                              inp = ConnIn.loc[i, 'In'],
                              out = ConnIn.loc[i, 'Out'],
                              energyType = ConnIn.loc[i, 'EnergyType']))

#Initialize the Sources
for i in range(len(SourceIn.index)):
    SourceList.append(Source(name = SourceIn.loc[i, 'Name'],
                             energyType = SourceIn.loc[i, 'EnergyType'],
                             capex = SourceIn.loc[i, 'Capex'], 
                             opexMin = SourceIn.loc[i, 'OpexMin'],
                             opexAvg = SourceIn.loc[i, 'OpexAvg'],
                             opexMax = SourceIn.loc[i, 'OpexMax'],
                             CO2 = SourceIn.loc[i, 'CO2'],
                             isSet = SourceIn.loc[i, 'IsSet'],
                             usageMin = SourceIn.loc[i, 'UsageMin'],
                             usageAvg = SourceIn.loc[i, 'UsageAvg'],
                             usageMax = SourceIn.loc[i, 'UsageMax']))
    
    outcolumns.append(SourceList[i].name + 'opex')

    
    for con in ConnList:
        if con.inp==SourceList[i].name and con.energyType==SourceList[i].energyType:
            SourceList[i].outcons.append(con)

#Initialize the sinks
for i in range(len(SinkIn.index)):
    SinkList.append(Sink(name = SinkIn.loc[i, 'Name'],
                         energyType = SinkIn.loc[i, 'EnergyType'],
                         capex = SinkIn.loc[i, 'Capex'],
                         opexMin = SinkIn.loc[i, 'OpexMin'],
                         opexAvg = SinkIn.loc[i, 'OpexAvg'],
                         opexMax = SinkIn.loc[i, 'OpexMax'],
                         demandMin = SinkIn.loc[i, 'DemandMin'],
                         demandAvg = SinkIn.loc[i, 'DemandAvg'],
                         demandMax = SinkIn.loc[i, 'DemandMax']))
    
    outcolumns.append(SinkList[i].name + 'opex')
    outcolumns.append(SinkList[i].name + 'Demand')
    
    for con in ConnList:
        if con.out==SinkList[i].name and con.energyType==SinkList[i].energyType:
            SinkList[i].incons.append(con)

#Initialize the transfomers
for i in range(len(TransIn.index)):
    TransList.append(Transformer(name = TransIn.loc[i, 'Name'],
                                 capex = TransIn.loc[i, 'Capex'],
                                 opexMin = TransIn.loc[i, 'OpexMin'],
                                 opexAvg = TransIn.loc[i, 'OpexAvg'],
                                 opexMax = TransIn.loc[i, 'OpexMax'],
                                 totalEffMin = TransIn.loc[i, 'TotalEffMin'],
                                 totalEffAvg = TransIn.loc[i, 'TotalEffAvg'],
                                 totalEffMax = TransIn.loc[i, 'TotalEffMax'],
                                 outMin = TransIn.loc[i, 'OutMin'],
                                 outMax = TransIn.loc[i, 'OutMax']))
    
    outcolumns.append(TransList[i].name + 'opex')
    outcolumns.append(TransList[i].name + 'TotalEff')
    
    k = 0
    
    for j in range(len(TransIn.loc[i, 'Input0':'Prod0'])-1):
        x = int(j/2)
        inp = TransIn.loc[i, 'Input'+str(x)]       
        if k % 2 == 0 and isinstance(inp,str):
            if not inp in EnergyList:
                EnergyList.append(inp)
            TransList[i].inputs[inp] = TransIn.loc[i, 'InRatio'+str(x)]
        k = k + 1
        
    k = 0
    
    for j in range(len(TransIn.loc[i, 'Prod0':])):
        x = int(j/2)
        product = TransIn.loc[i, 'Prod'+str(x)]       
        if k % 2 == 0 and isinstance(product, str):
            if not product in EnergyList:
                EnergyList.append(product)
            TransList[i].products[product] = TransIn.loc[i, 'SubEff' + str(x)]
        k = k + 1

    for con in ConnList:
        if con.out==TransList[i].name and con.energyType in TransList[i].inputs:
            TransList[i].incons.append(con)
        elif con.inp==TransList[i].name and con.energyType in TransList[i].products:
            TransList[i].outcons.append(con)
            outcolumns.append(TransList[i].name + '-' + con.energyType)

#Initialize the Hubs   
for i in range(len(HubIn.index)):
    HubList.append(Hub(name = HubIn.loc[i, 'Name'],
                       energyType = HubIn.loc[i, 'EnergyType'],
                       capex = HubIn.loc[i, 'Capex'],
                       opexMin = HubIn.loc[i, 'OpexMin'],
                       opexAvg = HubIn.loc[i, 'OpexAvg'],
                       opexMax = HubIn.loc[i, 'OpexMax']))
    outcolumns.append(HubList[i].name + 'opex')
    
    for con in ConnList:
        if con.out==HubList[i].name and con.energyType==HubList[i].energyType:
            HubList[i].incons.append(con)
        elif con.inp==HubList[i].name and con.energyType==HubList[i].energyType:
            HubList[i].outcons.append(con)

checkModel(ConnList, EnergyList)

dataout = pd.DataFrame(np.zeros((numIter, len(outcolumns))), columns = outcolumns)

for i in range(numIter):
    
    print('Iteration: ' + str(i) +
          '\n' + str(int(i/numIter *100)) + 
          '% Done\n|' + '▓' * int(i/numIter *100) + 
          '░' * (100-int(i/numIter *100)) + '|')
    
    randomizeOpex(SourceList, i, dataout)
    randomizeOpex(SinkList, i, dataout)
    randomizeOpex(TransList, i, dataout)
    randomizeOpex(HubList, i, dataout)
    
    randomizeEff(TransList, i, dataout)
    
    randomizeDem(SinkList, i, dataout)
    
    randomizeUsage(SourceList, i, dataout)
    
    model = createModel(SourceList, SinkList, TransList, ConnList, HubList, CO2 = CO2Max)
    
    results = opti(model)
    
    #Output formatting starts here
    
    try:
        dataout.at[i, 'Total Cost'] = model.Obj()
    except(ValueError):
#       print(chr(27) + "[2J")
        print("\nValue Error! Make sure the problem you put in input.xlsx is actually solvable, and doesn't have weird bounds.")
        break
        
    dataout.at[i, 'CO2'] = model.carbonsum.value
    
    for source in SourceList:
        dataout.at[i, source.energyType] = model.facilities[source].value
        
    for trans in TransList:
        for con in trans.outcons:
            dataout.at[i, (trans.name + '-' + con.energyType)] = model.connections[con].value
    
    print(chr(27) + "[2J")
    
dataout.to_excel('output.xlsx', sheet_name='Sheet1')

print('Done! Thank you for flying with us at AirJülich. You can find you luggage and model outputs in the output.xlsx file.')

#return 0
