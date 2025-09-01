#!/usr/bin/env python
"""
PURPOSE: Complete step-by-step trace from Annex 9 source data to final VAT-inclusive rates
DEPENDENCIES: Core ASF levies model modules
DATA SOURCES: Ofgem Annex 9, Annex 4 (levies)
CREATED: Comprehensive pipeline documentation
CONSTITUTIONAL COMPLIANCE: Principles 1,2,4,5 - Real data, line-by-line explanation
"""

import pandas as pd
import numpy as np
from datetime import datetime
import asf_levies_model.getters.load_data as data
import asf_levies_model.tariffs as tariffs
import asf_levies_model.levies as levies
from asf_levies_model import config

print("📊 COMPLETE DATA PIPELINE TRACE: SOURCE TO VAT-INCLUSIVE RATES")
print("=" * 70)
print(f"Execution time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# UK VAT rate for domestic energy
VAT_RATE = 1.05

print("\n🔧 CONFIGURATION:")
print(f"VAT Rate: 5% (multiplier: {VAT_RATE})")
print(f"Focus: Electricity, Other Payment Method, Single-rate")
print(f"Target Period: Latest available (will be Oct-Dec 2025)")

# ============================================================================
print("\n" + "="*70)
print("STEP 1: DOWNLOAD SOURCE DATA")
print("="*70)

print("\n📥 Downloading Ofgem Annexes...")
annex_9 = data.download_annex_9(as_fileobject=True)
annex_4 = data.download_annex_4(as_fileobject=True)
print("✅ Annex 9 downloaded (tariff components)")
print("✅ Annex 4 downloaded (levy costs)")

# ============================================================================
print("\n" + "="*70)
print("STEP 2: EXTRACT RAW TARIFF DATA FROM ANNEX 9")
print("="*70)

print("\n📋 Processing Tab '1c Consumption adjusted levels'...")
elec_other_nil = data.process_tariff_elec_other_payment_nil(annex_9)
elec_other_typical = data.process_tariff_elec_other_payment_typical(annex_9)

print(f"\nExtracted data shapes:")
print(f"- Nil consumption data: {elec_other_nil.shape}")
print(f"- Typical consumption data: {elec_other_typical.shape}")

# Get latest period data
latest_period = elec_other_nil.index.max()
print(f"\nLatest period: {latest_period[1]}")

# Suppress performance warnings for MultiIndex access
import warnings
with warnings.catch_warnings():
    warnings.filterwarnings('ignore', message='.*indexing past lexsort depth.*')
    nil_latest = elec_other_nil.loc[latest_period]
    typical_latest = elec_other_typical.loc[latest_period]

# Show raw values
print("\n📊 RAW VALUES (Tab 1c, Ex-VAT):")
print(f"Nil consumption annual bill: £{nil_latest['value'].sum():.2f}")
print(f"Typical consumption annual bill: £{typical_latest['value'].sum():.2f}")
print(f"Typical consumption level: 2.7 MWh (2,700 kWh)")

# ============================================================================
print("\n" + "="*70)
print("STEP 3: EXTRACT LEVY DATA FROM ANNEX 4")
print("="*70)

print("\n📋 Loading levy costs...")
levy_data = {}
levy_types = ['ECO', 'WHD', 'GGL', 'AAHEDC', 'FIT', 'RO']

for levy_type in levy_types:
    levy_func = getattr(data, f'process_data_{levy_type}')
    levy_data[levy_type] = levy_func(annex_4)
    print(f"✅ {levy_type} levy data loaded")

# Try to load NCC if available
try:
    levy_data['NCC'] = data.process_data_NCC(annex_4)
    print(f"✅ NCC levy data loaded")
except:
    print("ℹ️ NCC data not available in this Annex 4")

# ============================================================================
print("\n" + "="*70)
print("STEP 4: CREATE TARIFF OBJECTS")
print("="*70)

print("\n🏗️ Creating ElectricityOtherPayment tariff object...")
elec_tariff = tariffs.ElectricityOtherPayment.from_dataframe(
    elec_other_nil,
    elec_other_typical
)

print("\n📊 TARIFF COMPONENTS (Ex-VAT):")
print(f"Standing charge components (£/year):")
print(f"  Direct fuel (DF): £{elec_tariff.df_nil:.2f}")
print(f"  Capacity market (CM): £{elec_tariff.cm_nil:.2f}")
print(f"  Policy costs (PC): £{elec_tariff.pc_nil:.2f}")
print(f"  Network costs (NC): £{elec_tariff.nc_nil:.2f}")
print(f"  Operating costs (OC): £{elec_tariff.oc_nil:.2f}")
print(f"  TOTAL NIL: £{elec_tariff.calculate_nil_consumption():.2f}")

print(f"\nUnit rate components (£/MWh):")
print(f"  Direct fuel (DF): £{elec_tariff.df:.2f}")
print(f"  Capacity market (CM): £{elec_tariff.cm:.2f}")
print(f"  Policy costs (PC): £{elec_tariff.pc:.2f}")
print(f"  Network costs (NC): £{elec_tariff.nc:.2f}")
print(f"  Operating costs (OC): £{elec_tariff.oc:.2f}")

# ============================================================================
print("\n" + "="*70)
print("STEP 5: CALCULATE RATES (EX-VAT)")
print("="*70)

# Standing charge calculation
standing_annual = elec_tariff.calculate_nil_consumption()
standing_daily = standing_annual / 365 * 100  # Convert to pence per day

print(f"\n📐 Standing Charge Calculation:")
print(f"Annual nil consumption: £{standing_annual:.2f}")
print(f"Daily rate: £{standing_annual:.2f} ÷ 365 × 100 = {standing_daily:.2f}p/day")

# Unit rate calculation
typical_annual = elec_tariff.calculate_total_consumption(consumption=2.7)
unit_rate_mwh = (typical_annual - standing_annual) / 2.7
unit_rate_kwh = unit_rate_mwh / 10

print(f"\n📐 Unit Rate Calculation:")
print(f"Typical annual bill (2.7 MWh): £{typical_annual:.2f}")
print(f"Annual consumption cost: £{typical_annual:.2f} - £{standing_annual:.2f} = £{typical_annual - standing_annual:.2f}")
print(f"Unit rate: £{typical_annual - standing_annual:.2f} ÷ 2.7 MWh = £{unit_rate_mwh:.2f}/MWh")
print(f"Unit rate: £{unit_rate_mwh:.2f} ÷ 10 = {unit_rate_kwh:.2f}p/kWh")

# ============================================================================
print("\n" + "="*70)
print("STEP 6: APPLY VAT (5%)")
print("="*70)

standing_inc_vat = standing_daily * VAT_RATE
unit_inc_vat = unit_rate_kwh * VAT_RATE

print(f"\n💷 VAT Application:")
print(f"Standing charge: {standing_daily:.2f}p × 1.05 = {standing_inc_vat:.2f}p/day (inc VAT)")
print(f"Unit rate: {unit_rate_kwh:.2f}p × 1.05 = {unit_inc_vat:.2f}p/kWh (inc VAT)")

# ============================================================================
print("\n" + "="*70)
print("STEP 7: CREATE LEVY COLLECTION")
print("="*70)

print("\n🏗️ Creating individual levy objects...")

# Set up denominators (from testing_tariff_update.py pattern)
supply_elec = 96_517_461  # MWh
supply_gas = 266_505_188  # MWh
customers_gas = 24_605_467
customers_elec = 29_239_936

denominator_values = {
    "denominator_elec": supply_elec,
    "denominator_gas": supply_gas,
}

# Scaling factors
fit_eligible_supply = 249_044_438  # DESNZ GB total electricity consumption
fit_scaling_factor = supply_elec / fit_eligible_supply

# NCC scaling factor (if NCC data exists)
ncc_scaling_factor = 1.0  # Default if NCC not available
if 'NCC' in levy_data:
    unscaled_ncc = levies.NCC.from_dataframe(levy_data['NCC'])
    ncc_eligible_supply = unscaled_ncc.EligibleDemand
    ncc_scaling_factor = supply_elec / ncc_eligible_supply

# Create individual levy objects
# Note: Using default "LATEST" price cap period
list_levies = [
    levies.RO.from_dataframe(levy_data['RO'], denominator=supply_elec),
    levies.AAHEDC.from_dataframe(levy_data['AAHEDC'], denominator=supply_elec),
    levies.GGL.from_dataframe(levy_data['GGL'], denominator=customers_gas),
    levies.WHD.from_dataframe(levy_data['WHD'],
                             customers_gas=customers_gas,
                             customers_elec=customers_elec),
    levies.ECO.from_dataframe(levy_data['ECO']),
    levies.FIT.from_dataframe(levy_data['FIT'],
                             scaling_factor=fit_scaling_factor),
]

# Add NCC if available
if 'NCC' in levy_data:
    list_levies.append(
        levies.NCC.from_dataframe(levy_data['NCC'], scaling_factor=ncc_scaling_factor)
    )

# Create LevyCollection
pc = levies.LevyCollection("Policy Costs", "pc", list_levies, denominator_values)
print("✅ LevyCollection created")

print("\n📊 LEVY BREAKDOWN (Policy Costs):")
for levy in pc.levies:
    elec_var = levy.electricity_variable_rate or 0
    elec_fix = levy.electricity_fixed_rate or 0
    print(f"{levy.short_name:8} - Variable: £{elec_var:6.2f}/MWh, Fixed: £{elec_fix:6.2f}/year")

# ============================================================================
print("\n" + "="*70)
print("STEP 8: UPDATE TARIFF WITH POLICY COSTS")
print("="*70)

print("\n🔄 Updating tariff with levy collection...")
elec_tariff_updated = elec_tariff.update_policy_costs(pc)
print("✅ Tariff updated with current policy costs")

# Verify the update
print(f"\nPolicy costs in tariff:")
print(f"  PC nil (standing): £{elec_tariff_updated.pc_nil:.2f}/year")
print(f"  PC variable (unit): £{elec_tariff_updated.pc:.2f}/MWh")

# ============================================================================
print("\n" + "="*70)
print("FINAL SUMMARY")
print("="*70)

print("\n📊 COMPLETE PIPELINE RESULTS:")
print("\n1️⃣ SOURCE DATA (Annex 9, Tab 1c):")
print(f"   Nil: £{nil_latest['value'].sum():.2f} annual")
print(f"   Typical: £{typical_latest['value'].sum():.2f} annual at 2.7 MWh")

print("\n2️⃣ TARIFF OBJECT TOTALS (Ex-VAT):")
print(f"   Standing: £{standing_annual:.2f} annual = {standing_daily:.2f}p/day")
print(f"   Unit: £{unit_rate_mwh:.2f}/MWh = {unit_rate_kwh:.2f}p/kWh")

print("\n3️⃣ FINAL RATES (Inc 5% VAT):")
print(f"   Standing: {standing_inc_vat:.2f}p/day")
print(f"   Unit: {unit_inc_vat:.2f}p/kWh")

print("\n4️⃣ COMPARISON WITH PUBLISHED (Oct-Dec 2025):")
print(f"   Published: 53.68p/day, 26.35p/kWh")
print(f"   Model Inc VAT: {standing_inc_vat:.2f}p/day, {unit_inc_vat:.2f}p/kWh")

# Calculate differences
standing_diff = abs(standing_inc_vat - 53.68)
unit_diff = abs(unit_inc_vat - 26.35)

print(f"\n   Differences:")
if standing_diff < 0.01:
    print(f"   Standing: ✅ {standing_diff:.2f}p/day")
else:
    print(f"   Standing: ❌ {standing_diff:.2f}p/day ({standing_diff/53.68*100:.1f}%)")

if unit_diff < 0.01:
    print(f"   Unit: ✅ {unit_diff:.2f}p/kWh")
else:
    print(f"   Unit: ❌ {unit_diff:.2f}p/kWh ({unit_diff/26.35*100:.1f}%)")

print(f"\n   Note: Differences due to Tab 1c (2.7 MWh) vs Tab 1a (3.1 MWh)")

print("\n5️⃣ DATA FLOW SUMMARY:")
print("   Annex 9 (Tab 1c) → Tariff Components → Ex-VAT Rates → +5% VAT → Final Rates")
print("   Annex 4 → Levy Data → LevyCollection → Update Tariff Policy Costs")

print("\n✅ PIPELINE TRACE COMPLETE")
print("Ready for rebalancing scenarios with VAT-inclusive calculations")
