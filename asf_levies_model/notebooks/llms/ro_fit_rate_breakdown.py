# %%
import pandas as pd
from datetime import datetime

import asf_levies_model.getters.load_data as data
import asf_levies_model.levies as levies
import asf_levies_model.tariffs as tariffs
from asf_levies_model.summary import create_scenario_weights_dict

# %%
"""
Setup: Load Ofgem data and create baseline objects
"""

# %%
# Denominator values from DESNZ subnational consumption domestic data, 2023
supply_elec = 96_517_461
supply_gas = 266_505_188
customers_gas = 24_605_467
customers_elec = 29_239_936

denominator_values = {
    "supply_elec": supply_elec,
    "supply_gas": supply_gas,
    "customers_gas": customers_gas,
    "customers_elec": customers_elec,
}

# %%
# Scaling factor for estimating domestic share of FIT revenue
total_supply_elec = 249_044_438  # DESNZ GB total electricity consumption - all meters (2023)
exempt_eii_supply = 10_529_633  # Apr-Jun2025 period, Annex 4, New FIT methodology tab
fit_scaling_factor = supply_elec / (total_supply_elec - exempt_eii_supply)

# Scaling factor for estimating domestic share of NCC revenue
ncc_eligible_supply = 119_380_310.7  # Mar-Jun2025 period, Annex 4, NCC methodology tab
ncc_scaling_factor = supply_elec / ncc_eligible_supply

# %%
# Instantiate baseline levies with Annex 4 data
fileobject = data.download_annex_4(as_fileobject=True)

list_levies = [
    levies.RO.from_dataframe(data.process_data_RO(fileobject), denominator=supply_elec),
    levies.AAHEDC.from_dataframe(data.process_data_AAHEDC(fileobject), denominator=supply_elec),
    levies.GGL.from_dataframe(data.process_data_GGL(fileobject), denominator=customers_gas),
    levies.WHD.from_dataframe(
        data.process_data_WHD(fileobject),
        customers_gas=customers_gas,
        customers_elec=customers_elec,
    ),
    levies.ECO4.from_dataframe(data.process_data_ECO(fileobject)),
    levies.GBIS.from_dataframe(data.process_data_ECO(fileobject)),
    levies.FIT.from_dataframe(
        data.process_data_FIT(fileobject),
        scaling_factor=fit_scaling_factor,
    ),
    levies.NCC.from_dataframe(
        data.process_data_NCC(fileobject),
        scaling_factor=ncc_scaling_factor
    ),
]

pc = levies.LevyCollection("Policy Costs", "pc", list_levies, denominator_values)
pc = pc.rebalance_to_denominators()

fileobject.close()

# %%
# Create baseline tariffs from Annex 9
fileobject = data.download_annex_9(as_fileobject=True)

baseline_elec_tariff = tariffs.ElectricityOtherPayment.from_dataframe(
    data.process_tariff_elec_other_payment_nil(fileobject),
    data.process_tariff_elec_other_payment_typical(fileobject),
)
baseline_gas_tariff = tariffs.GasOtherPayment.from_dataframe(
    data.process_tariff_gas_other_payment_nil(fileobject),
    data.process_tariff_gas_other_payment_typical(fileobject),
)

fileobject.close()

# Update tariffs with baseline policy costs
baseline_elec_tariff = baseline_elec_tariff.update_policy_costs(pc)
baseline_gas_tariff = baseline_gas_tariff.update_policy_costs(pc)

# %%
"""
RO + FIT Rebalancing Scenario
"""

# %%
# Create scenario weights for rebalancing RO and FIT to gas
rebalance_ro_fit_weights = create_scenario_weights_dict(pc)

for levy in pc[["ro", "fit"]]:
    rebalance_ro_fit_weights[levy.short_name] = {
        "new_electricity_weight": 0,
        "new_gas_weight": 1,
        "new_tax_weight": 0,
        "new_variable_weight_elec": 0,
        "new_fixed_weight_elec": 0,
        "new_variable_weight_gas": levy.electricity_variable_weight,
        "new_fixed_weight_gas": levy.electricity_fixed_weight,
    }

# %%
# Apply rebalancing
rebalanced_pc = pc.rebalance_levies(rebalance_ro_fit_weights, "RO and FIT to Gas")

# %%
# Create rebalanced tariffs
rebalanced_elec_tariff = baseline_elec_tariff.copy().update_policy_costs(rebalanced_pc)
rebalanced_gas_tariff = baseline_gas_tariff.copy().update_policy_costs(rebalanced_pc)

# %%
"""
Rate Breakdown Comparison
"""

# %%
print("Rate Breakdown: Baseline vs RO+FIT to Gas")
print("=" * 60)

# Extract rates (ex-VAT)
baseline_elec_standing = baseline_elec_tariff.calculate_nil_consumption()
baseline_elec_unit = baseline_elec_tariff.calculate_variable_consumption(1.0)
baseline_gas_standing = baseline_gas_tariff.calculate_nil_consumption()
baseline_gas_unit = baseline_gas_tariff.calculate_variable_consumption(1.0)

rebalanced_elec_standing = rebalanced_elec_tariff.calculate_nil_consumption()
rebalanced_elec_unit = rebalanced_elec_tariff.calculate_variable_consumption(1.0)
rebalanced_gas_standing = rebalanced_gas_tariff.calculate_nil_consumption()
rebalanced_gas_unit = rebalanced_gas_tariff.calculate_variable_consumption(1.0)

# %%
print("ELECTRICITY")
print(f"Standing charge:  £{baseline_elec_standing:.2f}/year → £{rebalanced_elec_standing:.2f}/year  ({rebalanced_elec_standing - baseline_elec_standing:+.2f})")
print(f"                  {baseline_elec_standing * 100 / 365.25:.2f}p/day → {rebalanced_elec_standing * 100 / 365.25:.2f}p/day")
print(f"Unit rate:        £{baseline_elec_unit:.2f}/MWh → £{rebalanced_elec_unit:.2f}/MWh  ({rebalanced_elec_unit - baseline_elec_unit:+.2f})")
print(f"                  {baseline_elec_unit / 10:.2f}p/kWh → {rebalanced_elec_unit / 10:.2f}p/kWh")

print("\nGAS")
print(f"Standing charge:  £{baseline_gas_standing:.2f}/year → £{rebalanced_gas_standing:.2f}/year  ({rebalanced_gas_standing - baseline_gas_standing:+.2f})")
print(f"                  {baseline_gas_standing * 100 / 365.25:.2f}p/day → {rebalanced_gas_standing * 100 / 365.25:.2f}p/day")
print(f"Unit rate:        £{baseline_gas_unit:.2f}/MWh → £{rebalanced_gas_unit:.2f}/MWh  ({rebalanced_gas_unit - baseline_gas_unit:+.2f})")
print(f"                  {baseline_gas_unit / 10:.2f}p/kWh → {rebalanced_gas_unit / 10:.2f}p/kWh")

# %%
# Policy cost component breakdown
print("\nPolicy Cost Components")
print("-" * 30)

baseline_elec_policy = baseline_elec_tariff.pc
baseline_gas_policy = baseline_gas_tariff.pc
rebalanced_elec_policy = rebalanced_elec_tariff.pc
rebalanced_gas_policy = rebalanced_gas_tariff.pc

print(f"Electricity policy: £{baseline_elec_policy:.2f}/MWh → £{rebalanced_elec_policy:.2f}/MWh  ({rebalanced_elec_policy - baseline_elec_policy:+.2f})")
print(f"                    {baseline_elec_policy / 10:.2f}p/kWh → {rebalanced_elec_policy / 10:.2f}p/kWh")
print(f"Gas policy:         £{baseline_gas_policy:.2f}/MWh → £{rebalanced_gas_policy:.2f}/MWh  ({rebalanced_gas_policy - baseline_gas_policy:+.2f})")
print(f"                    {baseline_gas_policy / 10:.2f}p/kWh → {rebalanced_gas_policy / 10:.2f}p/kWh")

# %%
# Typical household impact
print("\nTypical Household (2.7 MWh elec, 11.5 MWh gas)")
print("-" * 50)

baseline_elec_bill = baseline_elec_tariff.calculate_total_consumption(2.7, vat=True)
baseline_gas_bill = baseline_gas_tariff.calculate_total_consumption(11.5, vat=True)
rebalanced_elec_bill = rebalanced_elec_tariff.calculate_total_consumption(2.7, vat=True)
rebalanced_gas_bill = rebalanced_gas_tariff.calculate_total_consumption(11.5, vat=True)

print(f"Electricity bill: £{baseline_elec_bill:.2f}/year → £{rebalanced_elec_bill:.2f}/year  ({rebalanced_elec_bill - baseline_elec_bill:+.2f})")
print(f"Gas bill:         £{baseline_gas_bill:.2f}/year → £{rebalanced_gas_bill:.2f}/year  ({rebalanced_gas_bill - baseline_gas_bill:+.2f})")
print(f"Combined bill:    £{baseline_elec_bill + baseline_gas_bill:.2f}/year → £{rebalanced_elec_bill + rebalanced_gas_bill:.2f}/year  ({(rebalanced_elec_bill + rebalanced_gas_bill) - (baseline_elec_bill + baseline_gas_bill):+.2f})")

# %%
# Revenue neutrality verification
print("\nRevenue Neutrality Check")
print("-" * 25)

baseline_total_revenue = sum(levy.revenue for levy in pc)
rebalanced_total_revenue = sum(levy.revenue for levy in rebalanced_pc)

print(f"Total policy revenue: £{baseline_total_revenue:,.0f} → £{rebalanced_total_revenue:,.0f}")
print(f"Revenue maintained: {abs(rebalanced_total_revenue - baseline_total_revenue) < 1}")

# %%
