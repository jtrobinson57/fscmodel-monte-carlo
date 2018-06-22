# fscmodel

Fuel Supply Chain Model

Given input of energy sources, sinks, transformers, and the connections between them (see input.xlsx for format), finds the optimal network flow. The problem minimizes cost while satisfying a constraint on carbon dioxide production.

Instructions:

1. Input data for the system considered into the input.xlsx spreadsheet.

  a. On the 'Sources' sheet, input is mostly straightforward, but one important column is the 'IsSet' column. if this is set to 0, that source's production value is fully flexible, while if it is 1, it is bound by the specified mins and maxes, and is determined with a randomized value on a normal distribution centered on the average value. Note that with this, and all sheets, if one wishes to not input an actual value, 0 should be put there instead.
  
  b. On the 'Sinks' sheet, note that if you wish to have opex be always set to a certain value, just set the min, avg, and max to the same value. This is true for all opexes and anything else with mins, avgs, and maxes.
  
  c. On the 'Transformers' sheet, note that the totalEff refers to the efficiency of goods coming into a transformer and goods coming out of a transformer. The subEff values refer to the ratio of the various outputs to the total transformer output. The same is true for the inratios. Both of these quantities should add up to 1 for each row.
  
  d. For 'Restrictions,' the NumIterations value refers to how many iterations of the Monte Carlo simultation are conducted. CO2 capacity can also be found here.

2. Run the fscmodel.py program through an IDE. We used Spyder.

3. Output data can be found in the output.xlsx spreadsheet. The most important data, regarding the quantities of different fuels used, will be put on the left side of the table, with the individual opexes and efficiencies on the right.
