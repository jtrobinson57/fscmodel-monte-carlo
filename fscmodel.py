# -*- coding: utf-8 -*-
"""
Created on Thu Jun  7 13:49:17 2018

@author: j.robinson
"""

from __future__ import division
from pyomo.environ import *
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

class Source:
    name = ''
    capex = 0
    opex = 0
    energyType = ''
    CO2 = 0
    
class Sink:
    name = ''
    capex = 0
    opex = 0
    energyType = ''
    demand = 0
    
class Transformer:
    name = ''
    inp = ''
    capex = 0
    opex = 0
    totalEff = 0
    products = {}

class Connection:
    name = ''
    inp = ''
    out = ''
    energyType = ''

SourceIn    = pd.read_excel('input.xlsx', 'Sources', index_col=None, na_values=['NA'])
SinkIn      = pd.read_excel('input.xlsx', 'Sinks', index_col=None, na_values=['NA'])
TransIn     = pd.read_excel('input.xlsx', 'Transformers', index_col=None, na_values=['NA'])
ConnIn      = pd.read_excel('input.xlsx', 'Connectors', index_col=None, na_values=['NA'])

SourceList  = [Source() for i in range(len(SourceIn.index))]
SinkList    = [Sink() for i in range(len(SinkIn.index))]
TransList   = [Transformer() for i in range(len(TransIn.index))]
ConnList    = [Connection() for i in range(len(ConnIn.index))]

for i in range(len(SourceIn.index)):
    SourceList[i].name = SourceIn.loc[i,'Name']
    SourceList[i].capex = SourceIn.loc[i,'Capex']
    SourceList[i].opex = SourceIn.loc[i,'Opex']
    SourceList[i].energyType = SourceIn.loc[i,'EnergyType']
    SourceList[i].CO2 = SourceIn.loc[i,'CO2']

for i in range(len(SinkIn.index)):
    SinkList[i].name = SinkIn.loc[i,'Name']
    SinkList[i].capex = SinkIn.loc[i,'Capex']
    SinkList[i].opex = SinkIn.loc[i,'Opex']
    SinkList[i].energyType = SinkIn.loc[i,'EnergyType']
    SinkList[i].demand = SinkIn.loc[i,'Demand']

for i in range(len(TransIn.index)):
    TransList[i].name = TransIn.loc[i,'Name']
    TransList[i].inp = TransIn.loc[i,'Input']
    TransList[i].capex = TransIn.loc[i,'Capex']
    TransList[i].opex = TransIn.loc[i,'Opex']
    TransList[i].totalEff = TransIn.loc[i,'TotalEff']
    
    k = 0
    x = 0
    
    for j in range(len(TransIn.loc[i,'Prod0':])):
        if k % 2 == 0:
            TransList[i].products[TransIn.loc[i,'Prod'+str(x)]] = TransIn.loc[i,'SubEff'+str(x)]
            x = x + 1
        k = k + 1

for i in range(len(ConnIn.index)):
    ConnList[i].name = ConnIn.loc[i,'Name']
    ConnList[i].inp = ConnIn.loc[i,'In']
    ConnList[i].out = ConnIn.loc[i,'Out']
    ConnList[i].energyType = ConnIn.loc[i,'EnergyType']


def createModel(SourceList, SinkList, TransList, ConnList, CO2 = 40):
    M = ConcreteModel()
    
    M.connectors = Set(initialize = ConnList)
    M.c = Param(M.connectors)
    M.carbon = Param(M.connectors)
    M.sources = SourceList
    M.sinks = SinkList
    M.trans = TransList
    
    
    M.connections = Var(M.connectors, domain = NonNegativeReals)
    
    #Constructs cost vector and carbon constraints
    for con in ConnList:
        for source in SourceList:
            if source.name == con.inp and source.energyType==con.energyType:
                M.c[con] = source.opex
                M.carbon[con] = source.CO2
                
                
     #Constructs Sink constraints
    #def sinkrule(model):
       # return (sum(con in M.connectors if con.out==))
    
    def objrule(model):
        return summation(model.connections,model.c, index=M.connectors)
    
    def co2rule(model, limit):
        return summation(model.connections,model.carbon,index = M.connectors) <= limit
    
    M.sinkconstraint = Constraint(M.sinks, rule = sinkrule)
    
    M.Co2limit = Constraint(rule = co2rule)
            
    M.Obj = Objective(rule = objrule, sense = minimize)
    
        
        
    return M

def opti(model):
    
    return output

model = createModel(SourceList, SinkList, Translist, ConnList, CO2 = 40)


