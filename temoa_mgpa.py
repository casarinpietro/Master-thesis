"""
Tools for Energy Model Optimization and Analysis (Temoa): 
An open source framework for energy systems optimization modeling

Copyright (C) 2015,  NC State University

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

A complete copy of the GNU General Public License v2 (GPLv2) is available 
in LICENSE.txt.  Users uncompressing this from an archive may not have 
received this license file.  If not, see <http://www.gnu.org/licenses/>.
"""

from pyomo.environ import *
from temoa_rules import TotalCost_rule
import numpy

# (c) Calculate near Pareto optimal solutions
# f1_slacked: w*x - s1*c/o(f1) - s2*c/o(f2) (in case of minimization)
def MGPAObjective_rule ( M, moo_f1, moo_f2, mga_weight, moo_c, moo_of1, moo_of2 ):

	objective = 0

	for t in M.V_ActivityByTech:
		if t in mga_weight:
			objective += mga_weight[t] * M.V_ActivityByTech[t]
	
	objective += (- M.V_Slack[moo_f1] * moo_c/(10**moo_of1) - M.V_Slack[moo_f2] * moo_c/(10**moo_of2))
	
	return objective

def MGPAWeight_rule ( M, mga_method, mga_weight ):

	#   The version below weights each technology by its previous cumulative
	#   activity. However, different sectors may be tracked in different units and 
	#   have activities of very different magnitudes. 

	epsilon=1e-6

	if mga_method == 'integer':
		for t in M.V_ActivityByTech:
			if t in M.tech_mga:
				val = value( M.V_ActivityByTech[t] )
				if abs(val) < epsilon: continue
				mga_weight[t] += 1.0
		return mga_weight
               
	#   The version below calculates activity by sector and normalized technology-
	#   specific activity by the total activity for the sector. Currently accounts
	#   for electric and transport sectors, but others can be added to the block below.

	elif mga_method == 'normalized':
		sectors = set(['ELC', 'STG', 'UPS', 'CCUS'])  # Note: 'sector' must be in sector_labels
		act     = dict()
		techs   = {'ELC':    M.tech_ELC,
		           'STG':    M.tech_STG,
		           'UPS':    M.tech_UPS,
		           'CCUS':   M.tech_CCUS}  # Note: M.tech_sector must be defined in temoa_model.py
		for s in sectors:
			if len(techs[s]) > 0:
				act[s] = sum(
		  		value( M.V_ActivityByTech[S_t] )
		  		for S_t in techs[s]
				)
      	
		for t in M.V_ActivityByTech:
			for s in sectors:
				if t in techs[s]:
					val = value( M.V_ActivityByTech[t] )
					if abs(val) < epsilon: continue
					mga_weight[t] += val / act[s]
		return mga_weight

	#   The version below weights each technology with random weights within the -1/+1 interval.

	elif mga_method == 'random':
		for t in M.V_ActivityByTech:
			if t in M.tech_mga:
				mga_weight[t] = numpy.random.uniform(-1, 1)
		return mga_weight

def MGPASlackedObjective_rule ( M, moo_f, f_pareto, mga_slack ):
	# It is important that this function name *not* match its constraint name
	# plus '_rule', else Pyomo will attempt to be too smart.  That is, at the
	# first implementation, the associated constraint name is
	# 'PreviousSlackedObjective', for which Pyomo searches the namespace for
	# 'PreviousSlackedObjective_rule'.  We decidedly do not want Pyomo
	# trying to call this function because it is not aware of the second arg.
	
	if moo_f == 'cost':
		oldobjective =  sum(M.V_Costs_rp[r, p] for p in M.time_optimize for r in M.regions)
	elif moo_f == 'emissions':
		oldobjective =  sum(M.V_Emissions_rp[r, p] for p in M.time_optimize for r in M.regions)
	elif moo_f == 'energySR':
		oldobjective =  sum(M.V_EnergySupplyRisk[r, p] for p in M.time_optimize for r in M.regions)
	elif moo_f == 'materialSR':
		oldobjective =  sum(M.V_MaterialSupplyRisk[r, p] for p in M.time_optimize for r in M.regions)
	
	expr = oldobjective + M.V_Slack[moo_f] == (1 + mga_slack) * f_pareto

	return expr

def MGPAMinObjective_rule ( M, moo_f, f_pareto, mga_slack ):
	# It is important that this function name *not* match its constraint name
	# plus '_rule', else Pyomo will attempt to be too smart.  That is, at the
	# first implementation, the associated constraint name is
	# 'PreviousSlackedObjective', for which Pyomo searches the namespace for
	# 'PreviousSlackedObjective_rule'.  We decidedly do not want Pyomo
	# trying to call this function because it is not aware of the second arg.
	
	if moo_f == 'cost':
		oldobjective =  sum(M.V_Costs_rp[r, p] for p in M.time_optimize for r in M.regions)
	elif moo_f == 'emissions':
		oldobjective =  sum(M.V_Emissions_rp[r, p] for p in M.time_optimize for r in M.regions)
	elif moo_f == 'energySR':
		oldobjective =  sum(M.V_EnergySupplyRisk[r, p] for p in M.time_optimize for r in M.regions)
	elif moo_f == 'materialSR':
		oldobjective =  sum(M.V_MaterialSupplyRisk[r, p] for p in M.time_optimize for r in M.regions)
	
	expr = oldobjective >= (1 - mga_slack) * f_pareto

	return expr
