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

for i in range(len(ConnIn.index)):
    ConnList[i].name = ConnIn.loc[i,'Name']
    ConnList[i].inp = ConnIn.loc[i,'In']
    ConnList[i].out = ConnIn.loc[i,'Out']
    ConnList[i].energyType = ConnIn.loc[i,'EnergyType']

def createModel(SourceList, SinkList, Translist, ConnList, CO2 = 40):
    M = ConcreteModel()
    M.connections = Var(ConnList, domain = NonNegativeReals)
        
    return M

def opti(model):
    
    return output
