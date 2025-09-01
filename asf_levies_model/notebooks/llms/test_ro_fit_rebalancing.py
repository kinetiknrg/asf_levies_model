#!/usr/bin/env python
"""
Test script to debug RO+FIT rebalancing issue
"""

import asf_levies_model.getters.load_data as data
import asf_levies_model.levies as levies
from asf_levies_model.summary import _rebalance_levies, set_common_denominators

# Load data
annex_4 = data.download_annex_4(as_fileobject=True)

# Set up denominators
supply_elec = 96_517_461
supply_gas = 266_505_188
customers_gas = 24_605_467
customers_elec = 29_239_936

# Create just RO and FIT levies
ro = levies.RO.from_dataframe(data.process_data_RO(annex_4), denominator=supply_elec)
fit = levies.FIT.from_dataframe(data.process_data_FIT(annex_4))

print("BEFORE REBALANCING:")
print(f"RO: elec_weight={ro.electricity_weight}, gas_weight={ro.gas_weight}")
print(f"    elec_var_rate={ro.electricity_variable_rate:.2f}")
print(f"FIT: elec_weight={fit.electricity_weight}, gas_weight={fit.gas_weight}")
print(f"    elec_var_rate={fit.electricity_variable_rate:.2f}")

# Calculate current costs
ro_cost = ro.calculate_levy(2.7, 11.5, True, True)
fit_cost = fit.calculate_levy(2.7, 11.5, True, True)
print(f"\nCurrent costs: RO=£{ro_cost:.2f}, FIT=£{fit_cost:.2f}")

# Test direct rebalancing
print("\n" + "="*50)
print("TESTING DIRECT REBALANCE:")

# Set up denominators
levy_denominators = set_common_denominators(
    [ro, fit],
    supply_elec=supply_elec,
    supply_gas=supply_gas,
    customers_gas=customers_gas,
    customers_elec=customers_elec
)

# Define weights to move to gas
rebalancing_weights = {
    "RO": {
        "new_electricity_weight": 0.0,
        "new_gas_weight": 1.0,
        "new_tax_weight": 0.0,
        "new_variable_weight_elec": 0.0,
        "new_fixed_weight_elec": 0.0,
        "new_variable_weight_gas": 1.0,
        "new_fixed_weight_gas": 0.0,
    },
    "FIT": {
        "new_electricity_weight": 0.0,
        "new_gas_weight": 1.0,
        "new_tax_weight": 0.0,
        "new_variable_weight_elec": 0.0,
        "new_fixed_weight_elec": 0.0,
        "new_variable_weight_gas": 1.0,
        "new_fixed_weight_gas": 0.0,
    }
}

# Apply rebalancing
rebalanced = _rebalance_levies(
    [ro, fit],
    {"test": rebalancing_weights},
    levy_denominators,
    "test"
)

print("\nAFTER REBALANCING:")
for levy in rebalanced:
    print(f"{levy.short_name}: elec_weight={levy.electricity_weight}, gas_weight={levy.gas_weight}")
    print(f"      elec_var_rate={levy.electricity_variable_rate:.2f}")
    print(f"      gas_var_rate={levy.gas_variable_rate:.2f}")
    
    # Calculate new cost
    new_cost = levy.calculate_levy(2.7, 11.5, True, True)
    print(f"      New cost: £{new_cost:.2f}")

print("\nDone")

