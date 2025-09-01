#!/usr/bin/env python
"""
Analyze individual levy contributions to understand why RO+FIT rebalancing has minimal impact
"""

import asf_levies_model.getters.load_data as data
import asf_levies_model.levies as levies
from asf_levies_model.summary import set_common_denominators

# Load data
annex_4 = data.download_annex_4(as_fileobject=True)

# Set up denominators
supply_elec = 96_517_461
supply_gas = 266_505_188
customers_gas = 24_605_467
customers_elec = 29_239_936

denominator_values = {
    'elec': supply_elec,
    'gas': supply_gas,
    'num_elec': customers_elec,
    'num_gas': customers_gas
}

# Load all levies
levy_types = ['AAHEDC', 'ECO', 'FIT', 'GGL', 'RO', 'WHD']
list_levies_base = []

for levy_type in levy_types:
    print(f"\nLoading {levy_type}...")
    func_name = f'process_data_{levy_type}'
    func = getattr(data, func_name)
    df = func(annex_4)
    
    levy_class = getattr(levies, levy_type)
    if levy_type in ['RO', 'ECO', 'WHD']:
        levy = levy_class.from_dataframe(df, denominator=supply_elec)
    elif levy_type == 'FIT':
        levy = levy_class.from_dataframe(df)
        # Apply FIT scaling
        levy.electricity_variable_rate = levy.electricity_variable_rate * (supply_elec / 100_000_000)
    else:
        levy = levy_class.from_dataframe(df)
    
    list_levies_base.append(levy)

# Calculate typical household consumption
elec_consumption = 2.7  # MWh
gas_consumption = 11.5  # MWh
has_elec = True
has_gas = True

print("\n" + "="*70)
print("LEVY COST BREAKDOWN FOR TYPICAL HOUSEHOLD")
print("="*70)

total_cost = 0
elec_cost_total = 0
gas_cost_total = 0

for levy in list_levies_base:
    # Calculate individual levy cost
    levy_cost = levy.calculate_levy(elec_consumption, gas_consumption, has_elec, has_gas)
    total_cost += levy_cost
    
    # Calculate electricity and gas components separately
    elec_cost = levy.calculate_levy(elec_consumption, 0, has_elec, False)
    gas_cost = levy.calculate_levy(0, gas_consumption, False, has_gas)
    elec_cost_total += elec_cost
    gas_cost_total += gas_cost
    
    print(f"\n{levy.short_name}:")
    print(f"  Total cost: £{levy_cost:.2f}/year ({levy_cost/total_cost*100:.1f}% of total)")
    print(f"  Electricity portion: £{elec_cost:.2f}")
    print(f"  Gas portion: £{gas_cost:.2f}")
    print(f"  Current weights: elec={levy.electricity_weight:.0%}, gas={levy.gas_weight:.0%}")

print(f"\n{'='*50}")
print(f"TOTAL POLICY COSTS: £{total_cost:.2f}/year")
print(f"  From electricity: £{elec_cost_total:.2f} ({elec_cost_total/total_cost*100:.1f}%)")
print(f"  From gas: £{gas_cost_total:.2f} ({gas_cost_total/total_cost*100:.1f}%)")

# Specifically analyze RO and FIT
print(f"\n{'='*50}")
print("RO + FIT ANALYSIS:")
ro_levy = next(l for l in list_levies_base if l.short_name == 'RO')
fit_levy = next(l for l in list_levies_base if l.short_name == 'FIT')

ro_cost = ro_levy.calculate_levy(elec_consumption, gas_consumption, has_elec, has_gas)
fit_cost = fit_levy.calculate_levy(elec_consumption, gas_consumption, has_elec, has_gas)
ro_fit_total = ro_cost + fit_cost

print(f"RO + FIT combined: £{ro_fit_total:.2f}/year")
print(f"This is {ro_fit_total/total_cost*100:.1f}% of total policy costs")
print(f"\nIf moved to gas, electricity bills would reduce by £{ro_fit_total:.2f}/year")
print(f"Per unit impact on electricity: {ro_fit_total/elec_consumption/10:.2f}p/kWh reduction")

