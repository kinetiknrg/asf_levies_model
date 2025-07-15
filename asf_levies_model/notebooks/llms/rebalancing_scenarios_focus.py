# %%
"""
CORE REBALANCING SCENARIOS ANALYSIS
Focus on the two key scenarios from the research:
- Scenario 4: All levies rebalanced from electricity to gas
- Scenario 5: RO/FiT only rebalanced from electricity to gas
"""

import pandas as pd
import copy
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
)

from asf_levies_model.levies import RO, AAHEDC, GGL, WHD, ECO, FIT
from asf_levies_model.tariffs import ElectricityOtherPayment, GasOtherPayment
from asf_levies_model.summary import create_scenario_weights_dict, set_common_denominators

# %%
"""
1. SETUP BASELINE LEVIES (Researcher's Exact Approach)
"""

print("🏗️ SETTING UP BASELINE LEVIES")
print("="*50)

# Denominator values from researcher's code
supply_elec = 94_200_366
supply_gas = 265_197_947
customers_gas = 24_503_683
customers_elec = 29_078_770

# FIT scaling factor (researcher's exact calculation)
total_supply_elec = 250_020_739
exempt_eii_supply = 9_417_916
fit_scaling_factor = supply_elec / (total_supply_elec - exempt_eii_supply)

print(f"📊 Denominators:")
print(f"   Electricity supply: {supply_elec:,}")
print(f"   Gas supply: {supply_gas:,}")
print(f"   FIT scaling factor: {fit_scaling_factor:.6f}")

# %%
# Create baseline levies
fileobject = download_annex_4(as_fileobject=True)
levies = [
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

print(f"\n✅ Loaded {len(levies)} levies:")
for levy in levies:
    print(f"   - {levy.name} ({levy.short_name}): £{levy.revenue:,.0f}")

# %%
# Create denominators dictionary
denominators = set_common_denominators(
    levies, supply_elec, supply_gas, customers_gas, customers_elec
)

# Status quo weights
status_quo = create_scenario_weights_dict(levies)

# Update WHD weights (researcher's exact approach)
status_quo["whd"]["new_electricity_weight"] = denominators["whd"]["customers_elec"] / (
    denominators["whd"]["customers_elec"] + denominators["whd"]["customers_gas"]
)
status_quo["whd"]["new_gas_weight"] = denominators["whd"]["customers_gas"] / (
    denominators["whd"]["customers_elec"] + denominators["whd"]["customers_gas"]
)

# Rebalance to denominators
levies = [
    levy.rebalance_levy(
        **status_quo.get(levy.short_name), **denominators.get(levy.short_name)
    )
    for levy in levies
]

print(f"\n💷 Baseline total levy cost (typical household): £{sum([levy.calculate_levy(2.7, 11.5, True, True) for levy in levies]):.2f}/year")

# %%
"""
2. DEFINE THE TWO KEY REBALANCING SCENARIOS
"""

print("\n🎯 DEFINING KEY REBALANCING SCENARIOS")
print("="*50)

# SCENARIO 4: All electricity levies → gas (researcher's exact weights)
scenario_4_weights = create_scenario_weights_dict(levies)

for levy in [levy for levy in levies if levy.electricity_weight > 0]:
    scenario_4_weights[levy.short_name] = {
        "new_electricity_weight": 0,
        "new_gas_weight": 1,
        "new_tax_weight": 0,
        "new_variable_weight_elec": 0,
        "new_fixed_weight_elec": 0,
        "new_variable_weight_gas": levy.electricity_variable_weight,
        "new_fixed_weight_gas": levy.electricity_fixed_weight,
    }

print("📋 SCENARIO 4: All electricity levies → gas")
affected_levies_4 = [levy.short_name for levy in levies if levy.electricity_weight > 0]
print(f"   Affects: {', '.join(affected_levies_4)}")

# SCENARIO 5: RO and FIT only → gas (researcher's exact weights)
scenario_5_weights = create_scenario_weights_dict(levies)

for levy in [levy for levy in levies if levy.short_name in ["ro", "fit"]]:
    scenario_5_weights[levy.short_name] = {
        "new_electricity_weight": 0,
        "new_gas_weight": 1,
        "new_tax_weight": 0,
        "new_variable_weight_elec": 0,
        "new_fixed_weight_elec": 0,
        "new_variable_weight_gas": levy.electricity_variable_weight,
        "new_fixed_weight_gas": levy.electricity_fixed_weight,
    }

print("📋 SCENARIO 5: RO and FiT only → gas")
affected_levies_5 = ["ro", "fit"]
print(f"   Affects: {', '.join(affected_levies_5)}")

# %%
"""
3. CREATE REBALANCED LEVIES FOR EACH SCENARIO
"""

print("\n⚖️ CREATING REBALANCED LEVIES")
print("="*50)

def rebalance_levies(original_levies, scenario_weights, denominators, scenario_name):
    """Rebalance levies according to scenario weights"""
    rebalanced = []
    for levy in original_levies:
        weights = scenario_weights.get(levy.short_name, {})
        denom = denominators.get(levy.short_name, {})
        rebalanced_levy = levy.rebalance_levy(**weights, **denom)
        rebalanced.append(rebalanced_levy)
    return rebalanced

# Create scenario levy sets
scenario_4_levies = rebalance_levies(levies, scenario_4_weights, denominators, "Scenario 4")
scenario_5_levies = rebalance_levies(levies, scenario_5_weights, denominators, "Scenario 5")

print("✅ Scenarios created:")
print(f"   Scenario 4 total: £{sum([levy.calculate_levy(2.7, 11.5, True, True) for levy in scenario_4_levies]):.2f}/year")
print(f"   Scenario 5 total: £{sum([levy.calculate_levy(2.7, 11.5, True, True) for levy in scenario_5_levies]):.2f}/year")

# %%
"""
4. CREATE TARIFFS FOR EACH SCENARIO
"""

print("\n🧾 CREATING TARIFFS")
print("="*50)

# Load tariff data
fileobject = download_annex_9(as_fileobject=True)
elec_nil = process_tariff_elec_other_payment_nil(fileobject)
elec_typical = process_tariff_elec_other_payment_typical(fileobject)
gas_nil = process_tariff_gas_other_payment_nil(fileobject)
gas_typical = process_tariff_gas_other_payment_typical(fileobject)
fileobject.close()

# Create tariff objects
tariffs = {}

scenarios = {
    "Baseline": levies,
    "Scenario 4 (All → Gas)": scenario_4_levies,
    "Scenario 5 (RO/FiT → Gas)": scenario_5_levies
}

for scenario_name, scenario_levies in scenarios.items():
    # Create electricity tariff
    elec_tariff = ElectricityOtherPayment.from_dataframe(elec_nil, elec_typical)
    elec_tariff.name = f"{scenario_name} - Electricity"

    # Create gas tariff
    gas_tariff = GasOtherPayment.from_dataframe(gas_nil, gas_typical)
    gas_tariff.name = f"{scenario_name} - Gas"

    # Update policy costs with rebalanced levies
    elec_tariff.pc_nil = sum([levy.calculate_levy(0, 0, True, False) for levy in scenario_levies])
    elec_tariff.pc = sum([levy.calculate_levy(1, 0, False, False) for levy in scenario_levies])
    gas_tariff.pc_nil = sum([levy.calculate_levy(0, 0, False, True) for levy in scenario_levies])
    gas_tariff.pc = sum([levy.calculate_levy(0, 1, False, False) for levy in scenario_levies])

    tariffs[scenario_name] = {
        "electricity": elec_tariff,
        "gas": gas_tariff
    }

print("✅ Tariffs created and policy costs updated for all scenarios")

# %%
"""
5. RESULTS ANALYSIS
"""

print("\n📊 SCENARIO COMPARISON RESULTS")
print("="*70)

results = []

for scenario_name, scenario_tariffs in tariffs.items():
    elec_tariff = scenario_tariffs["electricity"]
    gas_tariff = scenario_tariffs["gas"]

    # Calculate rates
    elec_unit_rate = elec_tariff.calculate_variable_consumption(1.0) / 10  # p/kWh
    elec_standing = elec_tariff.calculate_nil_consumption() / 365.25 * 100  # p/day
    gas_unit_rate = gas_tariff.calculate_variable_consumption(1.0) / 10  # p/kWh
    gas_standing = gas_tariff.calculate_nil_consumption() / 365.25 * 100  # p/day

    # Calculate bills
    elec_bill = elec_tariff.calculate_total_consumption(2.7, vat=True)
    gas_bill = gas_tariff.calculate_total_consumption(11.5, vat=True)
    total_bill = elec_bill + gas_bill

    # Electricity to gas ratio
    ratio = elec_unit_rate / gas_unit_rate

    results.append({
        "Scenario": scenario_name,
        "Elec Unit (p/kWh)": elec_unit_rate,
        "Elec Standing (p/day)": elec_standing,
        "Gas Unit (p/kWh)": gas_unit_rate,
        "Gas Standing (p/day)": gas_standing,
        "Elec Bill (£/year)": elec_bill,
        "Gas Bill (£/year)": gas_bill,
        "Total Bill (£/year)": total_bill,
        "Elec:Gas Ratio": ratio
    })

# Display results
results_df = pd.DataFrame(results)
print(results_df.round(2).to_string(index=False))

# %%
"""
6. KEY IMPACTS SUMMARY
"""

print("\n\n🎯 KEY IMPACTS SUMMARY")
print("="*70)

baseline = results_df[results_df["Scenario"] == "Baseline"].iloc[0]
scenario_4 = results_df[results_df["Scenario"] == "Scenario 4 (All → Gas)"].iloc[0]
scenario_5 = results_df[results_df["Scenario"] == "Scenario 5 (RO/FiT → Gas)"].iloc[0]

print("📋 BASELINE (Current System):")
print(f"   Electricity: {baseline['Elec Unit (p/kWh)']:.2f}p/kWh, {baseline['Elec Standing (p/day)']:.2f}p/day")
print(f"   Gas: {baseline['Gas Unit (p/kWh)']:.2f}p/kWh, {baseline['Gas Standing (p/day)']:.2f}p/day")
print(f"   Electricity:Gas Ratio: {baseline['Elec:Gas Ratio']:.2f}:1")
print(f"   Typical Bill: £{baseline['Total Bill (£/year)']:.2f}/year")

print(f"\n🔄 SCENARIO 4 - All Levies → Gas:")
print(f"   Electricity: {scenario_4['Elec Unit (p/kWh)']:.2f}p/kWh ({scenario_4['Elec Unit (p/kWh)'] - baseline['Elec Unit (p/kWh)']:.2f})")
print(f"   Gas: {scenario_4['Gas Unit (p/kWh)']:.2f}p/kWh (+{scenario_4['Gas Unit (p/kWh)'] - baseline['Gas Unit (p/kWh)']:.2f})")
print(f"   Electricity:Gas Ratio: {scenario_4['Elec:Gas Ratio']:.2f}:1 (from {baseline['Elec:Gas Ratio']:.2f}:1)")
print(f"   Bill Change: {scenario_4['Total Bill (£/year)'] - baseline['Total Bill (£/year)']:+.2f}/year")

print(f"\n🎯 SCENARIO 5 - RO/FiT Only → Gas:")
print(f"   Electricity: {scenario_5['Elec Unit (p/kWh)']:.2f}p/kWh ({scenario_5['Elec Unit (p/kWh)'] - baseline['Elec Unit (p/kWh)']:.2f})")
print(f"   Gas: {scenario_5['Gas Unit (p/kWh)']:.2f}p/kWh (+{scenario_5['Gas Unit (p/kWh)'] - baseline['Gas Unit (p/kWh)']:.2f})")
print(f"   Electricity:Gas Ratio: {scenario_5['Elec:Gas Ratio']:.2f}:1 (from {baseline['Elec:Gas Ratio']:.2f}:1)")
print(f"   Bill Change: {scenario_5['Total Bill (£/year)'] - baseline['Total Bill (£/year)']:+.2f}/year")

print(f"\n💡 IMPACT ON ELECTRICITY:GAS RATIO:")
print(f"   Current: {baseline['Elec:Gas Ratio']:.2f}:1")
print(f"   All → Gas: {scenario_4['Elec:Gas Ratio']:.2f}:1 ({((scenario_4['Elec:Gas Ratio'] - baseline['Elec:Gas Ratio']) / baseline['Elec:Gas Ratio'] * 100):+.1f}%)")
print(f"   RO/FiT → Gas: {scenario_5['Elec:Gas Ratio']:.2f}:1 ({((scenario_5['Elec:Gas Ratio'] - baseline['Elec:Gas Ratio']) / baseline['Elec:Gas Ratio'] * 100):+.1f}%)")

# %%