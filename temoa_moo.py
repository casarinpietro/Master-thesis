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

# (a) Determine the Pareto boundaries
# (a.1) f1_lowest
def f1lowest_rule( M, moo_f1 ):

	if moo_f1 == 'cost':
		return sum(M.V_Costs_rp[r, p] for p in M.time_optimize for r in M.regions)
	elif moo_f1 == 'emissions':
		return sum(M.V_Emissions_rp[r, p] for p in M.time_optimize for r in M.regions)
	elif moo_f1 == 'energySR':
		return sum(M.V_EnergySupplyRisk[r, p] for p in M.time_optimize for r in M.regions)
	elif moo_f1 == 'materialSR':
		return sum(M.V_MaterialSupplyRisk[r, p] for p in M.time_optimize for r in M.regions)

# (a.2) f2_lowest
def f2lowest_rule( M, moo_f2 ):

	if moo_f2 == 'cost':
		return sum(M.V_Costs_rp[r, p] for p in M.time_optimize for r in M.regions)
	elif moo_f2 == 'emissions':
		return sum(M.V_Emissions_rp[r, p] for p in M.time_optimize for r in M.regions)
	elif moo_f2 == 'energySR':
		return sum(M.V_EnergySupplyRisk[r, p] for p in M.time_optimize for r in M.regions)
	elif moo_f2 == 'materialSR':
		return sum(M.V_MaterialSupplyRisk[r, p] for p in M.time_optimize for r in M.regions)

# (a.3) f2_highest
def f2highest_rule ( M, moo_f1, f1_lowest ):

	f1_actual = f1lowest_rule( M, moo_f1 )
	expr = f1_actual == f1_lowest

	return expr

# (c) Calculate Pareto optimal solutions
# f1_slacked: f1 - s*c/o(f2) (in case of minimization)
def f1SlackedObjective_rule ( M, moo_f1, moo_f2, moo_c, moo_of2):
	# moo_c should be defined in the config_file, such as mga_slack for the MGA
	# moo_of2 is defined locally in temoa_run

	f1_actual = f1lowest_rule( M, moo_f1 )
	slacked_f1 = f1_actual - M.V_Slack[moo_f2] * moo_c/(10**moo_of2)

	return slacked_f1

# f2 constraint_slacked: f2 + s = eps (in case of minimization)
def f2SlackedConstraint_rule(M, moo_f2, f2_cap):

	f2_actual = f2lowest_rule( M, moo_f2 )
	expr = f2_actual + M.V_Slack[moo_f2] == f2_cap

	return expr

