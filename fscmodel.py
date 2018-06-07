# -*- coding: utf-8 -*-
"""
Created on Thu Jun  7 13:49:17 2018

@author: j.robinson
"""

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
    
class Transformer:
    name = ''
    capex = 0
    opex = 0
    totalEff = 0
    prod1 = ''
    subEff1 = 0
    prod2 = ''
    subEff2 = 0
    prod3 = ''
    subEff3 = 0

class Connection:
    name = ''
    inp = ''
    out = ''
    energyType = ''

SourceIn    = pd.read_excel('input.xlsx', 'Sources', index_col=None, na_values=['NA'])
SinkIn      = pd.read_excel('input.xlsx', 'Sinks', index_col=None, na_values=['NA'])
TransIn     = pd.read_excel('input.xlsx', 'Transformers', index_col=None, na_values=['NA'])
ConnIn      = pd.read_excel('input.xlsx', 'Connectors', index_col=None, na_values=['NA'])

SourceList  = [len(SourceIn.index)]
SinkList    = [len(SinkIn.index)]
TransList   = [len(TransIn.index)]
ConnList    = [len(ConnIn.index)]

for a in len(SourceIn.index):
    

for b in len(SinkIn.index):
    

for c in len(TransIn.index):
    

for d in len(ConnIn.index):
    
    