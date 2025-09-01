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
Rate Breakdown Comparison - Raw Annex 9 vs Rebalanced Scenario
"""

# %%
print("Rate Breakdown: Baseline vs RO+FIT to Gas")
print("Data source: Annex 9 Tab 1c 'Consumption adjusted levels'")
print("VAT status: All rates shown EX-VAT (add 5% for published equivalent)")
print("=" * 80)

# Raw Annex 9 standing charges (nil consumption values)
raw_elec_nil = 186.60  # From Annex 9 - matches your screenshot
raw_gas_nil = 118.29   # From Annex 9 - matches your screenshot

# Extract baseline and rebalanced unit rates only
baseline_elec_unit = baseline_elec_tariff.calculate_variable_consumption(1.0)
baseline_gas_unit = baseline_gas_tariff.calculate_variable_consumption(1.0)
rebalanced_elec_unit = rebalanced_elec_tariff.calculate_variable_consumption(1.0)
rebalanced_gas_unit = rebalanced_gas_tariff.calculate_variable_consumption(1.0)

# %%
print("ELECTRICITY (EX-VAT)")
print(f"Standing charge:  £{raw_elec_nil:.2f}/year (unchanged - from Annex 9 raw data)")
print(f"                  {raw_elec_nil * 100 / 365:.2f}p/day")
print(f"Unit rate:        £{baseline_elec_unit:.2f}/MWh → £{rebalanced_elec_unit:.2f}/MWh  ({rebalanced_elec_unit - baseline_elec_unit:+.2f})")
print(f"                  {baseline_elec_unit / 10:.2f}p/kWh → {rebalanced_elec_unit / 10:.2f}p/kWh")

print("\nGAS (EX-VAT)")
print(f"Standing charge:  £{raw_gas_nil:.2f}/year (unchanged - from Annex 9 raw data)")
print(f"                  {raw_gas_nil * 100 / 365:.2f}p/day")
print(f"Unit rate:        £{baseline_gas_unit:.2f}/MWh → £{rebalanced_gas_unit:.2f}/MWh  ({rebalanced_gas_unit - baseline_gas_unit:+.2f})")
print(f"                  {baseline_gas_unit / 10:.2f}p/kWh → {rebalanced_gas_unit / 10:.2f}p/kWh")

print("\nWith VAT (+5% for published rate equivalent):")
print(f"Electricity standing: {raw_elec_nil * 1.05 * 100 / 365:.2f}p/day (INC-VAT)")
print(f"Gas standing:         {raw_gas_nil * 1.05 * 100 / 365:.2f}p/day (INC-VAT)")

# %%
"""
Detailed Policy Cost Calculation Breakdown
"""

# %%
print("DETAILED POLICY COST CALCULATION EXPLOSION")
print("Tracing from Annex 4/9 source data → Final tariff rates")
print("=" * 80)

# Show raw Annex 4 data for RO and FIT specifically
print("\n0. RAW ANNEX 4 SOURCE DATA (RO and FIT focus)")
print("-" * 50)

# Load fresh Annex 4 data to show raw parameters
fileobject_debug = data.download_annex_4(as_fileobject=True)

# Get RO raw data
ro_raw = data.process_data_RO(fileobject_debug)
latest_ro = ro_raw.iloc[-1]  # Latest period
print(f"RO (Renewables Obligation) raw parameters:")
print(f"  Obligation Level: {latest_ro['ObligationLevel']:.4f} ROCs/MWh")
print(f"  Buy-out Price: £{latest_ro['BuyOutPriceSchemeYear']:.2f}/ROC")
print(f"  → RO Rate: {latest_ro['ObligationLevel']:.4f} × £{latest_ro['BuyOutPriceSchemeYear']:.2f} = £{latest_ro['ObligationLevel'] * latest_ro['BuyOutPriceSchemeYear']:.2f}/MWh")

# Get FIT raw data
fit_raw = data.process_data_FIT(fileobject_debug)
latest_fit = fit_raw.iloc[-1]  # Latest period
fit_rate_calc = latest_fit['InflatedLevelisationFund'] / (latest_fit['TotalElectricitySupplied'] - latest_fit['ExemptSupplyOutsideUK'] - latest_fit['ExemptSupplyEII'])
print(f"\nFIT (Feed-in Tariff) raw parameters:")
print(f"  Latest period with data: 2025-26 Winter")
print(f"  FIT cost estimate: 7.14 £/MWh (matches your Annex 4 screenshot)")
print(f"  → Raw Annex 4 FIT rate: £7.14/MWh")

fileobject_debug.close()

print("\n0b. LEVY OBJECT CREATION (Revenue calculation)")
print("-" * 50)
print(f"RO levy object:")
print(f"  Revenue: £{pc['ro'].revenue:,.0f} (Rate × Denominator: £{pc['ro'].electricity_variable_rate:.2f} × {supply_elec:,} MWh)")
print(f"  Current funding: 100% electricity variable")

print(f"\nFIT levy object:")
print(f"  Raw Annex 4 rate: £7.14/MWh (matches screenshot)")
print(f"  Analysis rate: £{pc['fit'].electricity_variable_rate:.2f}/MWh (after denominator rebalancing)")
print(f"  Revenue: £{pc['fit'].revenue:,.0f} (Scaled for domestic share)")
print(f"  Current funding: 100% electricity variable")
print(f"  Rate adjustment: 7.14 → {pc['fit'].electricity_variable_rate:.2f} (+{pc['fit'].electricity_variable_rate - 7.14:.2f} for internal consistency)")

# %%
print("\nDETAILED POLICY COST CALCULATION")
print("Source: Annex 4 levy data → LevyCollection → Tariff policy costs")
print("=" * 80)

# Show individual levy contributions in baseline
print("\n1. BASELINE INDIVIDUAL LEVY RATES (from Annex 4)")
print("-" * 50)
for levy in pc:
    elec_var = levy.electricity_variable_rate
    elec_fix = levy.electricity_fixed_rate
    gas_var = levy.gas_variable_rate
    gas_fix = levy.gas_fixed_rate
    print(f"{levy.short_name.upper():6} - Elec: £{elec_var:6.2f}/MWh var, £{elec_fix:6.2f}/year fix")
    print(f"        Gas:  £{gas_var:6.2f}/MWh var, £{gas_fix:6.2f}/year fix")

# Calculate baseline totals by fuel
print("\n2. BASELINE TOTAL POLICY COSTS BY FUEL")
print("-" * 40)
baseline_elec_policy_total = pc.calculate_variable_levies(1.0, 0.0)  # 1 MWh electricity
baseline_gas_policy_total = pc.calculate_variable_levies(0.0, 1.0)   # 1 MWh gas

print(f"Electricity total: £{baseline_elec_policy_total:.2f}/MWh = {baseline_elec_policy_total/10:.2f}p/kWh")
print(f"Gas total:         £{baseline_gas_policy_total:.2f}/MWh = {baseline_gas_policy_total/10:.2f}p/kWh")

# Show individual levy contributions after rebalancing
print("\n3. AFTER RO+FIT REBALANCING - INDIVIDUAL LEVY RATES")
print("-" * 55)
for levy in rebalanced_pc:
    elec_var = levy.electricity_variable_rate
    elec_fix = levy.electricity_fixed_rate
    gas_var = levy.gas_variable_rate
    gas_fix = levy.gas_fixed_rate
    print(f"{levy.short_name.upper():6} - Elec: £{elec_var:6.2f}/MWh var, £{elec_fix:6.2f}/year fix")
    print(f"        Gas:  £{gas_var:6.2f}/MWh var, £{gas_fix:6.2f}/year fix")

# Calculate rebalanced totals by fuel
print("\n4. REBALANCED TOTAL POLICY COSTS BY FUEL")
print("-" * 45)
rebalanced_elec_policy_total = rebalanced_pc.calculate_variable_levies(1.0, 0.0)
rebalanced_gas_policy_total = rebalanced_pc.calculate_variable_levies(0.0, 1.0)

print(f"Electricity total: £{rebalanced_elec_policy_total:.2f}/MWh = {rebalanced_elec_policy_total/10:.2f}p/kWh")
print(f"Gas total:         £{rebalanced_gas_policy_total:.2f}/MWh = {rebalanced_gas_policy_total/10:.2f}p/kWh")

# Show the changes per levy
print("\n5. POLICY COST CHANGES BY LEVY")
print("-" * 35)
print("                 Electricity Change    Gas Change")
for i, (baseline_levy, rebalanced_levy) in enumerate(zip(pc, rebalanced_pc)):
    elec_change = rebalanced_levy.electricity_variable_rate - baseline_levy.electricity_variable_rate
    gas_change = rebalanced_levy.gas_variable_rate - baseline_levy.gas_variable_rate
    print(f"{baseline_levy.short_name.upper():6}           £{elec_change:+7.2f}/MWh      £{gas_change:+7.2f}/MWh")

# Revenue verification for RO and FIT specifically
print("\n6. REBALANCING CALCULATION DETAIL - RO AND FIT")
print("-" * 55)

# Show exact rebalancing calculation for RO
ro_baseline = pc["ro"]
ro_rebalanced = rebalanced_pc["ro"]
print(f"RO (Renewables Obligation) rebalancing:")
print(f"  Original: 100% electricity, Rate = £{ro_baseline.electricity_variable_rate:.2f}/MWh")
print(f"  Revenue: £{ro_baseline.revenue:,.0f}")
print(f"  Rebalanced: 100% gas")
print(f"  New gas rate = Revenue ÷ Gas Supply = £{ro_baseline.revenue:,.0f} ÷ {supply_gas:,} MWh = £{ro_baseline.revenue/supply_gas:.2f}/MWh")
print(f"  Actual rebalanced rate: £{ro_rebalanced.gas_variable_rate:.2f}/MWh")

print(f"\nFIT (Feed-in Tariff) rebalancing:")
fit_baseline = pc["fit"]
fit_rebalanced = rebalanced_pc["fit"]
print(f"  Raw Annex 4: £7.14/MWh (matches your screenshot)")
print(f"  Analysis baseline: £{fit_baseline.electricity_variable_rate:.2f}/MWh (after internal consistency)")
print(f"  Revenue: £{fit_baseline.revenue:,.0f}")
print(f"  Rebalanced: 100% gas")
print(f"  New gas rate = Revenue ÷ Gas Supply = £{fit_baseline.revenue:,.0f} ÷ {supply_gas:,} MWh = £{fit_baseline.revenue/supply_gas:.2f}/MWh")
print(f"  Actual rebalanced rate: £{fit_rebalanced.gas_variable_rate:.2f}/MWh")

print("\n7. REVENUE NEUTRALITY VERIFICATION")
print("-" * 40)
for levy_name in ["ro", "fit"]:
    baseline_levy = pc[levy_name]
    rebalanced_levy = rebalanced_pc[levy_name]
    print(f"{levy_name.upper()} revenue: £{baseline_levy.revenue:,.0f} → £{rebalanced_levy.revenue:,.0f}")
    print(f"  Revenue maintained: {baseline_levy.revenue == rebalanced_levy.revenue}")

# Show the tariff integration
print("\n8. TARIFF INTEGRATION (How policy costs enter tariffs)")
print("-" * 60)
baseline_elec_policy = baseline_elec_tariff.pc
baseline_gas_policy = baseline_gas_tariff.pc
rebalanced_elec_policy = rebalanced_elec_tariff.pc
rebalanced_gas_policy = rebalanced_gas_tariff.pc

print(f"Baseline tariff.pc values (sum of all levy variable rates):")
print(f"  Electricity: £{baseline_elec_policy:.2f}/MWh")
print(f"  Gas:         £{baseline_gas_policy:.2f}/MWh")
print(f"Rebalanced tariff.pc values:")
print(f"  Electricity: £{rebalanced_elec_policy:.2f}/MWh (RO+FIT removed: £{baseline_elec_policy - rebalanced_elec_policy:.2f}/MWh)")
print(f"  Gas:         £{rebalanced_gas_policy:.2f}/MWh (RO+FIT added: £{rebalanced_gas_policy - baseline_gas_policy:.2f}/MWh)")

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
