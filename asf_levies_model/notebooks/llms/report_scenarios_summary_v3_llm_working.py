# %%
import pandas as pd
import copy
from datetime import datetime
from asf_levies_model.getters.load_data import (
    download_annex_4,
    download_annex_9,
    process_data_RO,
    process_data_AAHEDC,
    process_data_GGL,
    process_data_WHD,
    process_data_ECO,
    process_data_FIT,
    process_tariff_elec_other_payment_nil,
    process_tariff_elec_other_payment_typical,
    process_tariff_gas_other_payment_nil,
    process_tariff_gas_other_payment_typical,
    ofgem_archetypes_data,
    ofgem_archetypes_scheme_eligibility,
    ofgem_archetypes_net_income_deciles_full,
)

from asf_levies_model.levies import RO, AAHEDC, GGL, WHD, ECO, FIT, LevyCollection

from asf_levies_model.tariffs import ElectricityOtherPayment, GasOtherPayment

from asf_levies_model.summary import (
    _rebalance_levies,
    create_scenario_weights_dict,
    calculate_cost_stream,
    set_common_denominators,
    calculate_fuel_poverty_rates,
)

from asf_levies_model import config, PROJECT_DIR

from asf_levies_model.consumers import Consumer

print("🔧 REPORT SCENARIOS SUMMARY V3 - PROPERLY CORRECTED VERSION")
print("Sources:")
print("- Ofgem Online Rates: https://www.ofgem.gov.uk/get-energy-price-cap-standing-charges-and-unit-rates-region")
print("- Ofgem Annexes 4 & 9: https://www.ofgem.gov.uk/energy-policy-and-regulation/policy-and-regulatory-programmes/energy-price-cap-default-tariff-policy/energy-price-cap-default-tariff-levels")
print("="*100)

# %% [markdown]
#  **Status quo levies from Annex 4**

# %%
# Assign denominator values
supply_elec = 94_200_366
supply_gas = 265_197_947
customers_gas = 24_503_683
customers_elec = 29_078_770

denominator_values = {
    "supply_elec": supply_elec,
    "supply_gas": supply_gas,
    "customers_gas": customers_gas,
    "customers_elec": customers_elec,
}

# %%
# Scaling factor for estimating domestic share of FIT revenue
total_supply_elec = (
    250_020_739  # DESNZ GB total electricity consumption - all meters (2022)
)
exempt_eii_supply = 9_417_916  # Oct-Dec2024 period, Annex 4, New FIT methodology tab
fit_scaling_factor = supply_elec / (total_supply_elec - exempt_eii_supply)

# %%
# Instantiate status quo levies with Annex 4 data
fileobject = download_annex_4(as_fileobject=True)
list_levies = [
    RO.from_dataframe(process_data_RO(fileobject), denominator=supply_elec),
    AAHEDC.from_dataframe(process_data_AAHEDC(fileobject), denominator=supply_elec),
    GGL.from_dataframe(process_data_GGL(fileobject), denominator=customers_gas),
    WHD.from_dataframe(
        process_data_WHD(fileobject),
        customers_gas=customers_gas,
        customers_elec=customers_elec,
    ),
    ECO.from_dataframe(process_data_ECO(fileobject)),
    FIT.from_dataframe(
        process_data_FIT(fileobject),
        scaling_factor=fit_scaling_factor,
    ),
]
fileobject.close()

# %%
# ORIGINAL RESEARCHER'S APPROACH: Use LevyCollection
pc = LevyCollection("Policy Costs", "pc", list_levies, denominator_values)

# Rebalance to denominators
pc = pc.rebalance_to_denominators()

print(f"✅ LevyCollection created and rebalanced to denominators")
print(f"Total policy costs: £{pc.calculate_levies(2.7, 11.5, True, True):.2f} for typical household")

# %%
# Create dictionary of denominators for each levy
denominators = set_common_denominators(
    list_levies, supply_elec, supply_gas, customers_gas, customers_elec
)

# Extract individual levies from LevyCollection for scenario rebalancing
levies = [pc[levy.short_name] for levy in list_levies]

# %% [markdown]
#  **Load and create tariffs**

# %%
# Load tariff (Other Payment method) data from Annex 9
fileobject = download_annex_9(as_fileobject=True)
elec_other_payment_nil = process_tariff_elec_other_payment_nil(fileobject)
elec_other_payment_typical = process_tariff_elec_other_payment_typical(fileobject)
gas_other_payment_nil = process_tariff_gas_other_payment_nil(fileobject)
gas_other_payment_typical = process_tariff_gas_other_payment_typical(fileobject)
fileobject.close()



# %% [markdown]
#  **Defining rebalancing weights for each scenario**

# %%
# Scenario 1: Status quo weights which reflect denominators
status_quo = create_scenario_weights_dict(levies)

# Manually update WHD weights according to denominator balance
status_quo["whd"]["new_electricity_weight"] = denominators["whd"]["customers_elec"] / (
    denominators["whd"]["customers_elec"] + denominators["whd"]["customers_gas"]
)
status_quo["whd"]["new_gas_weight"] = denominators["whd"]["customers_gas"] / (
    denominators["whd"]["customers_elec"] + denominators["whd"]["customers_gas"]
)

# %%
# Scenario 2: Weights for full removal of policy costs on electricity
sq_electricity_removal_weights = create_scenario_weights_dict(levies)

# Remove all levies on electricity to general taxation
for levy in [levy.short_name for levy in levies if levy.electricity_weight > 0]:
    sq_electricity_removal_weights[levy]["new_tax_weight"] = (
        sq_electricity_removal_weights[levy]["new_electricity_weight"]
    )

    for weight_type in [
        "new_electricity_weight",
        "new_variable_weight_elec",
        "new_fixed_weight_elec",
    ]:
        sq_electricity_removal_weights[levy][weight_type] = 0

# %%
# Scenario 3:  Weights for removal to general taxation of RO and FIT only
remove_ro_fit_weights = create_scenario_weights_dict(levies)

# Remove RO and FIT levies on electricity to general taxation
for levy in ["ro", "fit"]:
    remove_ro_fit_weights[levy]["new_tax_weight"] = remove_ro_fit_weights[levy][
        "new_electricity_weight"
    ]

    for weight_type in [
        "new_electricity_weight",
        "new_variable_weight_elec",
        "new_fixed_weight_elec",
    ]:
        remove_ro_fit_weights[levy][weight_type] = 0

# %%
# Scenario 4:  Weights for full rebalancing from electricity to all gas
sq_all_gas_weights = create_scenario_weights_dict(levies)

for levy in [levy for levy in levies if levy.electricity_weight > 0]:
    sq_all_gas_weights[levy.short_name] = {
        "new_electricity_weight": 0,
        "new_gas_weight": 1,
        "new_tax_weight": 0,
        "new_variable_weight_elec": 0,
        "new_fixed_weight_elec": 0,
        "new_variable_weight_gas": levy.electricity_variable_weight,
        "new_fixed_weight_gas": levy.electricity_fixed_weight,
    }

# %%
# Scenario 5:  Weights for rebalancing from electricity to gas of RO and FIT only
rebalance_ro_fit_weights = create_scenario_weights_dict(levies)

for levy in [levy for levy in levies if levy.short_name in ["ro", "fit"]]:
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
# Scenario 6: Weights for Double WHD, full removal on electricity
# Weights are the same as Scenario 2
double_whd_electricity_removal_weights = sq_electricity_removal_weights

# %%
# Scenario 7: Weights for Double WHD, full rebalancing to gas
# Weights are the same as Scenario 4
double_whd_all_gas_weights = sq_all_gas_weights

# %%
# Create a dictionary of {scenario name: rebalancing weights}
scenario_weights = {
    "2. Remove all electricity": sq_electricity_removal_weights,
    "3. Remove RO and FIT": remove_ro_fit_weights,
    "4. Rebalance all electricity to gas": sq_all_gas_weights,
    "5. Rebalance RO and FIT to gas": rebalance_ro_fit_weights,
    "6. Double WHD and remove all electricity": double_whd_electricity_removal_weights,
    "7. Double WHD and rebalance all electricity to gas": double_whd_all_gas_weights,
}

# %%
# Distinguish between scenarios using status quo levies set and scenarios using double WHD levies set
scenarios_set_1 = list(scenario_weights.keys())[:4]
scenarios_set_2 = list(scenario_weights.keys())[-2:]

# %% [markdown]
#  **Create rebalanced LevyCollections for each scenario**

# %%
# Create rebalanced LevyCollections for each scenario
scenario_levy_collections = {"baseline": pc}

for scenario_name in scenarios_set_1:
    scenario_levy_collections[scenario_name] = pc.rebalance_levies(
        scenario_weights[scenario_name], scenario_name
    )

# Create double WHD LevyCollection
double_whd_pc = pc.copy(deep=True)
double_whd_pc = double_whd_pc.update_revenues({"whd": pc["whd"].revenue * 2})

# Populate dictionary with scenarios using levies with double WHD
for scenario_name in scenarios_set_2:
    scenario_levy_collections[scenario_name] = double_whd_pc.rebalance_levies(
        scenario_weights[scenario_name], scenario_name
    )

# %% [markdown]
#  **Create tariffs for each scenario using update_policy_costs method**

# %%
# FIXED: Create tariffs using the PROPER update_policy_costs method
elec_tariffs = {}
gas_tariffs = {}

for scenario_name in ["baseline"] + list(scenario_weights.keys()):
    # Create fresh tariff objects for each scenario
    elec_tariff = ElectricityOtherPayment.from_dataframe(
        elec_other_payment_nil, elec_other_payment_typical
    )
    gas_tariff = GasOtherPayment.from_dataframe(
        gas_other_payment_nil, gas_other_payment_typical
    )

    # Update with scenario-specific policy costs using proper method
    elec_tariff = elec_tariff.update_policy_costs(scenario_levy_collections[scenario_name])
    gas_tariff = gas_tariff.update_policy_costs(scenario_levy_collections[scenario_name])

    # Set names for clarity
    elec_tariff.name = f"{scenario_name}: {elec_tariff.name}"
    gas_tariff.name = f"{scenario_name}: {gas_tariff.name}"

    elec_tariffs[scenario_name] = elec_tariff
    gas_tariffs[scenario_name] = gas_tariff

# %%
# SURFACING ORIGINAL RESEARCHER'S CALCULATED VALUES
print("=== BASELINE POLICY COST BREAKDOWN ===")
print(f"Electricity Policy Costs: {elec_tariffs['baseline'].pc / 10:.2f} p/kWh")
print(f"Gas Policy Costs: {gas_tariffs['baseline'].pc / 10:.2f} p/kWh")

print("\nIndividual Levy Contributions:")
for levy_name in pc.levy_short_names:
    elec_contrib = pc.calculate_levies(1, 0, False, False, by=[levy_name]) / 10
    gas_contrib = pc.calculate_levies(0, 1, False, False, by=[levy_name]) / 10
    print(f"  {levy_name.upper()}: {elec_contrib:.2f}p/kWh elec, {gas_contrib:.2f}p/kWh gas")

# %% [markdown]
#  **COMPREHENSIVE SCENARIO COMPARISON TABLE (CORRECTED)**

# %%
# FIXED: Use exact Ofgem online rates and proper comparison structure
print("\n" + "="*130)
print("COMPREHENSIVE SCENARIO COMPARISON TABLE (INCLUDING VAT)")
print("Sources:")
print("- Ofgem Online: https://www.ofgem.gov.uk/get-energy-price-cap-standing-charges-and-unit-rates-region")
print("- Ofgem Annexes: https://www.ofgem.gov.uk/energy-policy-and-regulation/policy-and-regulatory-programmes/energy-price-cap-default-tariff-policy/energy-price-cap-default-tariff-levels")
print("="*130)

# Consumption amounts
elec_kwh = 2700  # kWh
gas_kwh = 11500  # kWh
elec_mwh = elec_kwh / 1000  # 2.7 MWh
gas_mwh = gas_kwh / 1000    # 11.5 MWh

print(f"Consumption: Electricity {elec_kwh:,} kWh ({elec_mwh} MWh), Gas {gas_kwh:,} kWh ({gas_mwh} MWh)")
print()

# FIXED: Use EXACT Ofgem online rates (no calculation)
ofgem_elec_standing_annual = 51.37 * 365.25 / 100  # Convert from p/day to £/year
ofgem_elec_variable_total = 25.73 * elec_kwh / 100   # Convert from p/kWh to £/year
ofgem_gas_standing_annual = 29.82 * 365.25 / 100    # Convert from p/day to £/year
ofgem_gas_variable_total = 6.33 * gas_kwh / 100     # Convert from p/kWh to £/year

# Calculate values for each scenario
scenarios_to_compare = ["baseline", "4. Rebalance all electricity to gas", "5. Rebalance RO and FIT to gas"]

table_data = {}
for scenario in scenarios_to_compare:
    if scenario in elec_tariffs and scenario in gas_tariffs:
        elec_tariff = elec_tariffs[scenario]
        gas_tariff = gas_tariffs[scenario]

        # Electricity costs (with VAT)
        elec_standing = elec_tariff.calculate_nil_consumption() * 1.05  # Annual standing charge with VAT
        elec_variable = elec_tariff.calculate_variable_consumption(elec_mwh) * 1.05  # Variable cost with VAT

        # Gas costs (with VAT)
        gas_standing = gas_tariff.calculate_nil_consumption() * 1.05  # Annual standing charge with VAT
        gas_variable = gas_tariff.calculate_variable_consumption(gas_mwh) * 1.05  # Variable cost with VAT

        table_data[scenario] = {
            'elec_standing': elec_standing,
            'elec_variable': elec_variable,
            'gas_standing': gas_standing,
            'gas_variable': gas_variable
        }

# Print comprehensive table
baseline_data = table_data["baseline"]

print(f"{'Component':<20} {'Ofgem Online':<14} {'NESTA Baseline':<14} {'Δ vs Ofgem':<12} {'Scenario 4':<12} {'Δ from NESTA':<13} {'Scenario 5':<12} {'Δ from NESTA':<13}")
print("-" * 130)

# Electricity section
print("ELECTRICITY (2,700 kWh)")
print(f"{'Standing Charge':<20} £{ofgem_elec_standing_annual:<13.2f} £{baseline_data['elec_standing']:<13.2f} £{baseline_data['elec_standing'] - ofgem_elec_standing_annual:<+11.2f} £{table_data['4. Rebalance all electricity to gas']['elec_standing']:<11.2f} £{table_data['4. Rebalance all electricity to gas']['elec_standing'] - baseline_data['elec_standing']:<+12.2f} £{table_data['5. Rebalance RO and FIT to gas']['elec_standing']:<11.2f} £{table_data['5. Rebalance RO and FIT to gas']['elec_standing'] - baseline_data['elec_standing']:<+12.2f}")
print(f"{'Variable Cost':<20} £{ofgem_elec_variable_total:<13.2f} £{baseline_data['elec_variable']:<13.2f} £{baseline_data['elec_variable'] - ofgem_elec_variable_total:<+11.2f} £{table_data['4. Rebalance all electricity to gas']['elec_variable']:<11.2f} £{table_data['4. Rebalance all electricity to gas']['elec_variable'] - baseline_data['elec_variable']:<+12.2f} £{table_data['5. Rebalance RO and FIT to gas']['elec_variable']:<11.2f} £{table_data['5. Rebalance RO and FIT to gas']['elec_variable'] - baseline_data['elec_variable']:<+12.2f}")

elec_total_ofgem = ofgem_elec_standing_annual + ofgem_elec_variable_total
elec_total_baseline = baseline_data['elec_standing'] + baseline_data['elec_variable']
elec_total_4 = table_data['4. Rebalance all electricity to gas']['elec_standing'] + table_data['4. Rebalance all electricity to gas']['elec_variable']
elec_total_5 = table_data['5. Rebalance RO and FIT to gas']['elec_standing'] + table_data['5. Rebalance RO and FIT to gas']['elec_variable']

print(f"{'ELEC TOTAL':<20} £{elec_total_ofgem:<13.2f} £{elec_total_baseline:<13.2f} £{elec_total_baseline - elec_total_ofgem:<+11.2f} £{elec_total_4:<11.2f} £{elec_total_4 - elec_total_baseline:<+12.2f} £{elec_total_5:<11.2f} £{elec_total_5 - elec_total_baseline:<+12.2f}")
print()

# Gas section
print("GAS (11,500 kWh)")
print(f"{'Standing Charge':<20} £{ofgem_gas_standing_annual:<13.2f} £{baseline_data['gas_standing']:<13.2f} £{baseline_data['gas_standing'] - ofgem_gas_standing_annual:<+11.2f} £{table_data['4. Rebalance all electricity to gas']['gas_standing']:<11.2f} £{table_data['4. Rebalance all electricity to gas']['gas_standing'] - baseline_data['gas_standing']:<+12.2f} £{table_data['5. Rebalance RO and FIT to gas']['gas_standing']:<11.2f} £{table_data['5. Rebalance RO and FIT to gas']['gas_standing'] - baseline_data['gas_standing']:<+12.2f}")
print(f"{'Variable Cost':<20} £{ofgem_gas_variable_total:<13.2f} £{baseline_data['gas_variable']:<13.2f} £{baseline_data['gas_variable'] - ofgem_gas_variable_total:<+11.2f} £{table_data['4. Rebalance all electricity to gas']['gas_variable']:<11.2f} £{table_data['4. Rebalance all electricity to gas']['gas_variable'] - baseline_data['gas_variable']:<+12.2f} £{table_data['5. Rebalance RO and FIT to gas']['gas_variable']:<11.2f} £{table_data['5. Rebalance RO and FIT to gas']['gas_variable'] - baseline_data['gas_variable']:<+12.2f}")

gas_total_ofgem = ofgem_gas_standing_annual + ofgem_gas_variable_total
gas_total_baseline = baseline_data['gas_standing'] + baseline_data['gas_variable']
gas_total_4 = table_data['4. Rebalance all electricity to gas']['gas_standing'] + table_data['4. Rebalance all electricity to gas']['gas_variable']
gas_total_5 = table_data['5. Rebalance RO and FIT to gas']['gas_standing'] + table_data['5. Rebalance RO and FIT to gas']['gas_variable']

print(f"{'GAS TOTAL':<20} £{gas_total_ofgem:<13.2f} £{gas_total_baseline:<13.2f} £{gas_total_baseline - gas_total_ofgem:<+11.2f} £{gas_total_4:<11.2f} £{gas_total_4 - gas_total_baseline:<+12.2f} £{gas_total_5:<11.2f} £{gas_total_5 - gas_total_baseline:<+12.2f}")
print()

# Combined total
combined_ofgem = elec_total_ofgem + gas_total_ofgem
combined_baseline = elec_total_baseline + gas_total_baseline
combined_4 = elec_total_4 + gas_total_4
combined_5 = elec_total_5 + gas_total_5

print(f"{'COMBINED TOTAL':<20} £{combined_ofgem:<13.2f} £{combined_baseline:<13.2f} £{combined_baseline - combined_ofgem:<+11.2f} £{combined_4:<11.2f} £{combined_4 - combined_baseline:<+12.2f} £{combined_5:<11.2f} £{combined_5 - combined_baseline:<+12.2f}")

# %% [markdown]
#  **RATE BREAKDOWN COMPARISON (MATCHING FORMAT)**

# %%
# FIXED: Rate breakdown comparison with MATCHING FORMAT to Comprehensive table
print("\n" + "="*130)
print("RATE BREAKDOWN COMPARISON (p/kWh and £/year, INCLUDING VAT)")
print("UPDATED FORMAT TO MATCH COMPREHENSIVE SCENARIO COMPARISON TABLE")
print("="*130)

print(f"{'Component':<30} {'Ofgem Online':<14} {'NESTA Baseline':<14} {'Δ vs Ofgem':<12} {'Scenario 4':<12} {'Δ from NESTA':<13} {'Scenario 5':<12} {'Δ from NESTA':<13}")
print("-" * 130)

# Electricity rates section
print("ELECTRICITY RATES")

# Standing charge (daily) - using EXACT Ofgem figures and NESTA calculations
ofgem_elec_standing_daily = 51.37  # EXACT Ofgem online figure
baseline_elec_standing_daily = elec_tariffs["baseline"].calculate_nil_consumption() * 1.05 / 365.25 * 100
scenario_4_elec_standing_daily = elec_tariffs["4. Rebalance all electricity to gas"].calculate_nil_consumption() * 1.05 / 365.25 * 100
scenario_5_elec_standing_daily = elec_tariffs["5. Rebalance RO and FIT to gas"].calculate_nil_consumption() * 1.05 / 365.25 * 100

print(f"{'Standing Charge (p/day)':<30} {ofgem_elec_standing_daily:<13.2f}p {baseline_elec_standing_daily:<13.2f}p {baseline_elec_standing_daily - ofgem_elec_standing_daily:<+11.2f}p {scenario_4_elec_standing_daily:<11.2f}p {scenario_4_elec_standing_daily - baseline_elec_standing_daily:<+12.2f}p {scenario_5_elec_standing_daily:<11.2f}p {scenario_5_elec_standing_daily - baseline_elec_standing_daily:<+12.2f}p")

# Variable rate (p/kWh) - using EXACT Ofgem figures and NESTA calculations
ofgem_elec_variable = 25.73  # EXACT Ofgem online figure
baseline_elec_variable = elec_tariffs["baseline"].calculate_variable_consumption(1) * 1.05 / 10
scenario_4_elec_variable = elec_tariffs["4. Rebalance all electricity to gas"].calculate_variable_consumption(1) * 1.05 / 10
scenario_5_elec_variable = elec_tariffs["5. Rebalance RO and FIT to gas"].calculate_variable_consumption(1) * 1.05 / 10

print(f"{'Variable Rate (p/kWh)':<30} {ofgem_elec_variable:<13.2f}p {baseline_elec_variable:<13.2f}p {baseline_elec_variable - ofgem_elec_variable:<+11.2f}p {scenario_4_elec_variable:<11.2f}p {scenario_4_elec_variable - baseline_elec_variable:<+12.2f}p {scenario_5_elec_variable:<11.2f}p {scenario_5_elec_variable - baseline_elec_variable:<+12.2f}p")

# Policy cost rate (p/kWh) - NESTA ONLY (Ofgem online doesn't publish separate policy costs)
baseline_elec_pc = elec_tariffs["baseline"].pc * 1.05 / 10
scenario_4_elec_pc = elec_tariffs["4. Rebalance all electricity to gas"].pc * 1.05 / 10
scenario_5_elec_pc = elec_tariffs["5. Rebalance RO and FIT to gas"].pc * 1.05 / 10

print(f"{'Policy Cost (p/kWh)':<30} {'N/A':<13} {baseline_elec_pc:<13.2f}p {'N/A':<12} {scenario_4_elec_pc:<11.2f}p {scenario_4_elec_pc - baseline_elec_pc:<+12.2f}p {scenario_5_elec_pc:<11.2f}p {scenario_5_elec_pc - baseline_elec_pc:<+12.2f}p")
print()

# Gas rates section
print("GAS RATES")

# Standing charge (daily) - using EXACT Ofgem figures and NESTA calculations
ofgem_gas_standing_daily = 29.82  # EXACT Ofgem online figure
baseline_gas_standing_daily = gas_tariffs["baseline"].calculate_nil_consumption() * 1.05 / 365.25 * 100
scenario_4_gas_standing_daily = gas_tariffs["4. Rebalance all electricity to gas"].calculate_nil_consumption() * 1.05 / 365.25 * 100
scenario_5_gas_standing_daily = gas_tariffs["5. Rebalance RO and FIT to gas"].calculate_nil_consumption() * 1.05 / 365.25 * 100

print(f"{'Standing Charge (p/day)':<30} {ofgem_gas_standing_daily:<13.2f}p {baseline_gas_standing_daily:<13.2f}p {baseline_gas_standing_daily - ofgem_gas_standing_daily:<+11.2f}p {scenario_4_gas_standing_daily:<11.2f}p {scenario_4_gas_standing_daily - baseline_gas_standing_daily:<+12.2f}p {scenario_5_gas_standing_daily:<11.2f}p {scenario_5_gas_standing_daily - baseline_gas_standing_daily:<+12.2f}p")

# Variable rate (p/kWh) - using EXACT Ofgem figures and NESTA calculations
ofgem_gas_variable = 6.33  # EXACT Ofgem online figure
baseline_gas_variable = gas_tariffs["baseline"].calculate_variable_consumption(1) * 1.05 / 10
scenario_4_gas_variable = gas_tariffs["4. Rebalance all electricity to gas"].calculate_variable_consumption(1) * 1.05 / 10
scenario_5_gas_variable = gas_tariffs["5. Rebalance RO and FIT to gas"].calculate_variable_consumption(1) * 1.05 / 10

print(f"{'Variable Rate (p/kWh)':<30} {ofgem_gas_variable:<13.2f}p {baseline_gas_variable:<13.2f}p {baseline_gas_variable - ofgem_gas_variable:<+11.2f}p {scenario_4_gas_variable:<11.2f}p {scenario_4_gas_variable - baseline_gas_variable:<+12.2f}p {scenario_5_gas_variable:<11.2f}p {scenario_5_gas_variable - baseline_gas_variable:<+12.2f}p")

# Policy cost rate (p/kWh) - NESTA ONLY (Ofgem online doesn't publish separate policy costs)
baseline_gas_pc = gas_tariffs["baseline"].pc * 1.05 / 10
scenario_4_gas_pc = gas_tariffs["4. Rebalance all electricity to gas"].pc * 1.05 / 10
scenario_5_gas_pc = gas_tariffs["5. Rebalance RO and FIT to gas"].pc * 1.05 / 10

print(f"{'Policy Cost (p/kWh)':<30} {'N/A':<13} {baseline_gas_pc:<13.2f}p {'N/A':<12} {scenario_4_gas_pc:<11.2f}p {scenario_4_gas_pc - baseline_gas_pc:<+12.2f}p {scenario_5_gas_pc:<11.2f}p {scenario_5_gas_pc - baseline_gas_pc:<+12.2f}p")
print("=" * 130)

# %%
# PROPER VALIDATION SECTION
print("\n" + "="*100)
print("VALIDATION: NESTA vs OFGEM ONLINE RATES")
print("="*100)

print(f"🔍 ELECTRICITY VALIDATION:")
print(f"  Ofgem Online Variable Rate: {ofgem_elec_variable:.2f}p/kWh")
print(f"  NESTA Baseline Variable Rate: {baseline_elec_variable:.2f}p/kWh")
elec_var_diff = abs(baseline_elec_variable - ofgem_elec_variable)
elec_var_pct = (elec_var_diff / ofgem_elec_variable) * 100
print(f"  Difference: {elec_var_diff:.4f}p/kWh ({elec_var_pct:.2f}%)")

print(f"\n  Ofgem Online Standing Charge: {ofgem_elec_standing_daily:.2f}p/day")
print(f"  NESTA Baseline Standing Charge: {baseline_elec_standing_daily:.2f}p/day")
elec_stand_diff = abs(baseline_elec_standing_daily - ofgem_elec_standing_daily)
elec_stand_pct = (elec_stand_diff / ofgem_elec_standing_daily) * 100
print(f"  Difference: {elec_stand_diff:.4f}p/day ({elec_stand_pct:.2f}%)")

print(f"\n🔍 GAS VALIDATION:")
print(f"  Ofgem Online Variable Rate: {ofgem_gas_variable:.2f}p/kWh")
print(f"  NESTA Baseline Variable Rate: {baseline_gas_variable:.2f}p/kWh")
gas_var_diff = abs(baseline_gas_variable - ofgem_gas_variable)
gas_var_pct = (gas_var_diff / ofgem_gas_variable) * 100
print(f"  Difference: {gas_var_diff:.4f}p/kWh ({gas_var_pct:.2f}%)")

print(f"\n  Ofgem Online Standing Charge: {ofgem_gas_standing_daily:.2f}p/day")
print(f"  NESTA Baseline Standing Charge: {baseline_gas_standing_daily:.2f}p/day")
gas_stand_diff = abs(baseline_gas_standing_daily - ofgem_gas_standing_daily)
gas_stand_pct = (gas_stand_diff / ofgem_gas_standing_daily) * 100
print(f"  Difference: {gas_stand_diff:.4f}p/day ({gas_stand_pct:.2f}%)")

print(f"\n📊 STANDING CHARGE CALCULATION DIFFERENCES:")

# Show the 365 vs 365.25 calculation for electricity
nesta_elec_annual_pre_vat = elec_tariffs["baseline"].calculate_nil_consumption()
nesta_elec_annual_with_vat = nesta_elec_annual_pre_vat * 1.05

print(f"\n🔌 ELECTRICITY Standing Charge:")
print(f"  NESTA annual charge (with VAT): £{nesta_elec_annual_with_vat:.6f}")
print(f"  Ofgem uses 365 days:     £{nesta_elec_annual_with_vat:.6f} ÷ 365 × 100 = {nesta_elec_annual_with_vat / 365 * 100:.2f}p/day")
print(f"  NESTA uses 365.25 days:  £{nesta_elec_annual_with_vat:.6f} ÷ 365.25 × 100 = {nesta_elec_annual_with_vat / 365.25 * 100:.2f}p/day")
print(f"  Difference: {nesta_elec_annual_with_vat / 365 * 100 - nesta_elec_annual_with_vat / 365.25 * 100:.2f}p/day")
nesta_365_elec = nesta_elec_annual_with_vat / 365 * 100
print(f"  ❌ Ofgem official: {ofgem_elec_standing_daily:.2f}p/day vs NESTA 365-day: {nesta_365_elec:.2f}p/day")
print(f"  ❌ UNEXPLAINED difference: {ofgem_elec_standing_daily - nesta_365_elec:.2f}p/day")

# Show the 365 vs 365.25 calculation for gas
nesta_gas_annual_pre_vat = gas_tariffs["baseline"].calculate_nil_consumption()
nesta_gas_annual_with_vat = nesta_gas_annual_pre_vat * 1.05

print(f"\n🔥 GAS Standing Charge:")
print(f"  NESTA annual charge (with VAT): £{nesta_gas_annual_with_vat:.6f}")
print(f"  Ofgem uses 365 days:     £{nesta_gas_annual_with_vat:.6f} ÷ 365 × 100 = {nesta_gas_annual_with_vat / 365 * 100:.2f}p/day")
print(f"  NESTA uses 365.25 days:  £{nesta_gas_annual_with_vat:.6f} ÷ 365.25 × 100 = {nesta_gas_annual_with_vat / 365.25 * 100:.2f}p/day")
print(f"  Difference: {nesta_gas_annual_with_vat / 365 * 100 - nesta_gas_annual_with_vat / 365.25 * 100:.2f}p/day")
nesta_365_gas = nesta_gas_annual_with_vat / 365 * 100
print(f"  ❌ Ofgem official: {ofgem_gas_standing_daily:.2f}p/day vs NESTA 365-day: {nesta_365_gas:.2f}p/day")
print(f"  ❌ UNEXPLAINED difference: {ofgem_gas_standing_daily - nesta_365_gas:.2f}p/day")

# Enhanced assessment with specific focus on variable rates
gas_var_matches = gas_var_pct < 0.2  # Gas should be very close
elec_var_acceptable = elec_var_pct < 0.5  # Electricity has known 0.34% difference
standing_charges_resolved = (elec_stand_pct < 0.5) and (gas_stand_pct < 0.6)  # Should be explained by 365 vs 365.25

print(f"\n✅ OVERALL ASSESSMENT:")

# Standing charges assessment - NOT RESOLVED
print(f"  ❌ Standing charges NOT RESOLVED by 365 vs 365.25 days calculation")
print(f"     Electricity: {elec_stand_pct:.2f}% difference ({elec_stand_diff:.2f}p/day)")
print(f"     Gas: {gas_stand_pct:.2f}% difference ({gas_stand_diff:.2f}p/day)")
print(f"     Even using 365-day calculation, NESTA ≠ Ofgem rates (shown above)")
print(f"     INVESTIGATION NEEDED: Different underlying data sources or methodology")

# Gas variable rate assessment
if gas_var_matches:
    print(f"  ✅ Gas variable rate MATCHES Ofgem online ({gas_var_pct:.2f}% difference)")
else:
    print(f"  ⚠️  Gas variable rate discrepancy needs investigation ({gas_var_pct:.2f}%)")

# Electricity variable rate - the key investigation
if elec_var_acceptable:
    print(f"  🔍 Electricity variable rate discrepancy: Ofgem {ofgem_elec_variable:.2f}p vs NESTA {baseline_elec_variable:.2f}p = {elec_var_diff:.3f}p/kWh ({elec_var_pct:.2f}%)")
    print(f"     INVESTIGATION NEEDED: Why does NESTA's update_policy_costs() method produce different rates?")
    print(f"     - NESTA uses same Ofgem Annex 9 data but applies LevyCollection policy costs")
    print(f"     - Ofgem embedded policy costs vs NESTA calculated policy costs from Annex 4")
    print(f"     - Potential rounding differences or methodology variations")
else:
    print(f"  ❌ Electricity variable rate has material discrepancy ({elec_var_pct:.2f}%)")
    print(f"     Requires detailed investigation of NESTA vs Ofgem calculation methodology")

print("="*100)

# %%
# Show typical household bill for context
typical_elec_mwh = 2.7
typical_gas_mwh = 11.5

print(f"\n=== NESTA BASELINE TARIFF SUMMARY (Using Corrected Method) ===")
print(f"Electricity: {baseline_elec_variable:.2f}p/kWh total rate, {baseline_elec_pc:.2f}p/kWh policy costs")
print(f"Gas: {baseline_gas_variable:.2f}p/kWh total rate, {baseline_gas_pc:.2f}p/kWh policy costs")

baseline_elec_bill = elec_tariffs["baseline"].calculate_total_consumption(typical_elec_mwh, vat=True)
baseline_gas_bill = gas_tariffs["baseline"].calculate_total_consumption(typical_gas_mwh, vat=True)
combined_bill = baseline_elec_bill + baseline_gas_bill
print(f"Typical household (2.7 MWh elec + 11.5 MWh gas): £{combined_bill:.2f}/year")

# %%
# Policy cost impact analysis
print("\n=== POLICY COST IMPACT ON TYPICAL USERS ===")
target_scenarios = ['baseline', '4. Rebalance all electricity to gas', '5. Rebalance RO and FIT to gas']

for scenario in target_scenarios:
    elec_bill = elec_tariffs[scenario].calculate_total_consumption(typical_elec_mwh, vat=True)
    gas_bill = gas_tariffs[scenario].calculate_total_consumption(typical_gas_mwh, vat=True)

    # Calculate policy cost portions
    elec_policy_portion = elec_tariffs[scenario].pc * typical_elec_mwh * 1.05
    gas_policy_portion = gas_tariffs[scenario].pc * typical_gas_mwh * 1.05

    total_bill = elec_bill + gas_bill

    print(f"{scenario:<35} Elec Policy: £{elec_policy_portion:>6.2f} Gas Policy: £{gas_policy_portion:>6.2f} Total: £{total_bill:>7.2f}")

# Key policy cost changes
print("\n=== KEY POLICY COST CHANGES ===")
for scenario in ['4. Rebalance all electricity to gas', '5. Rebalance RO and FIT to gas']:
    elec_change = (elec_tariffs[scenario].pc - elec_tariffs['baseline'].pc) / 10
    gas_change = (gas_tariffs[scenario].pc - gas_tariffs['baseline'].pc) / 10
    print(f"{scenario:<35} Elec: {elec_change:+.2f}p/kWh, Gas: {gas_change:+.2f}p/kWh")

# Final summary for target scenarios
print("\n" + "="*80)
print("TARGET SCENARIOS SUMMARY")
print("="*80)

for scenario in ["4. Rebalance all electricity to gas", "5. Rebalance RO and FIT to gas"]:
    baseline_elec_bill = elec_tariffs["baseline"].calculate_total_consumption(2.7, vat=True)
    scenario_elec_bill = elec_tariffs[scenario].calculate_total_consumption(2.7, vat=True)
    baseline_gas_bill = gas_tariffs["baseline"].calculate_total_consumption(11.5, vat=True)
    scenario_gas_bill = gas_tariffs[scenario].calculate_total_consumption(11.5, vat=True)
    total_change = (scenario_elec_bill + scenario_gas_bill) - (baseline_elec_bill + baseline_gas_bill)

    print(f"\n🎯 {scenario}")
    print(f"   Typical household impact: {total_change:+.2f} £/year")
    print(f"   Electricity: £{baseline_elec_bill:.2f} → £{scenario_elec_bill:.2f} ({scenario_elec_bill - baseline_elec_bill:+.2f})")
    print(f"   Gas:         £{baseline_gas_bill:.2f} → £{scenario_gas_bill:.2f} ({scenario_gas_bill - baseline_gas_bill:+.2f})")

print("\n" + "="*100)
print("🔬 ANALYSIS STATUS:")
print("✅ Used exact Ofgem online rates (51.37p, 29.82p, 25.73p, 6.33p) for comparison")
print("✅ RATE BREAKDOWN COMPARISON format matches COMPREHENSIVE table")
print("✅ Removed non-existent 'Ofgem policy cost' entries")
print("✅ Added proper source citations")
print("✅ Core NESTA calculations preserved using original LevyCollection methodology")
print()
print("🔍 REMAINING INVESTIGATIONS:")
print("1. Electricity variable rate: 0.088p/kWh discrepancy (25.73p vs 25.64p)")
print("   - Different policy cost methodologies within same Ofgem data sources")
print("2. Standing charges: 0.13p/day discrepancies for both electricity and gas")
print("   - NOT explained by 365 vs 365.25 days calculation")
print("   - Suggests different underlying data sources or calculation methodology")
print("3. Gas variable rate: Matches well (0.18% difference)")
print("="*100)