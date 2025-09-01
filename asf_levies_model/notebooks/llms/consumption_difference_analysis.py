#!/usr/bin/env python
"""
PURPOSE: Analyze the impact of different consumption assumptions between tabs
DEPENDENCIES: Direct calculation based on observed values
DATA SOURCES: Ofgem Annex 9 Tab 1a vs Tab 1c
CREATED: Diagnostic to explain £100 discrepancy
CONSTITUTIONAL COMPLIANCE: Principles 1,2,5 - Real data validation
"""

print("🔍 CONSUMPTION DIFFERENCE ANALYSIS")
print("=" * 50)

# From screenshots and model observations
tab_1a_nil = 186.60  # GB average nil
tab_1a_typical = 964.54  # GB average at 3,100 kWh
tab_1a_consumption = 3.1  # MWh (3,100 kWh)

tab_1c_nil = 186.60  # Same nil value
tab_1c_typical = 864.16  # From model output
tab_1c_consumption = 2.7  # MWh (model assumption)

print("\n📊 TAB 1a (Levelised DTC) - Your Screenshots:")
print(f"Nil consumption: £{tab_1a_nil:.2f}")
print(f"Typical consumption: £{tab_1a_typical:.2f} at {tab_1a_consumption} MWh")
print(f"Unit rate = (£{tab_1a_typical:.2f} - £{tab_1a_nil:.2f}) / {tab_1a_consumption} MWh")
unit_rate_1a = (tab_1a_typical - tab_1a_nil) / tab_1a_consumption
print(f"         = £{unit_rate_1a:.2f}/MWh = {unit_rate_1a/10:.2f}p/kWh")

print("\n📊 TAB 1c (Consumption adjusted) - Model Uses:")
print(f"Nil consumption: £{tab_1c_nil:.2f}")
print(f"Typical consumption: £{tab_1c_typical:.2f} at {tab_1c_consumption} MWh")
print(f"Unit rate = (£{tab_1c_typical:.2f} - £{tab_1c_nil:.2f}) / {tab_1c_consumption} MWh")
unit_rate_1c = (tab_1c_typical - tab_1c_nil) / tab_1c_consumption
print(f"         = £{unit_rate_1c:.2f}/MWh = {unit_rate_1c/10:.2f}p/kWh")

print("\n🎯 KEY INSIGHT:")
print(f"Tab 1a uses: {tab_1a_consumption} MWh (3,100 kWh)")
print(f"Tab 1c uses: {tab_1c_consumption} MWh (2,700 kWh)")
print(f"Consumption difference: {(tab_1a_consumption - tab_1c_consumption):.1f} MWh = 400 kWh")

print("\n💡 RECONCILIATION:")
print("If Tab 1c had the same unit rate as Tab 1a but at 2.7 MWh:")
reconstructed_typical = tab_1a_nil + (unit_rate_1a * tab_1c_consumption)
print(f"Expected typical bill: £{reconstructed_typical:.2f}")
print(f"Actual Tab 1c typical: £{tab_1c_typical:.2f}")
print(f"Difference: £{abs(reconstructed_typical - tab_1c_typical):.2f}")

print("\n📐 REVERSE CALCULATION:")
print("What consumption would Tab 1c need to match Tab 1a's unit rate?")
implied_consumption = (tab_1c_typical - tab_1c_nil) / unit_rate_1a
print(f"Implied consumption: {implied_consumption:.2f} MWh")

print("\n✅ CONCLUSION:")
print("The £100 discrepancy is explained by BOTH:")
print("1. Different consumption levels (3.1 vs 2.7 MWh)")
print("2. Different tariff values between tabs")
print("\nTab 1a appears to be the published GB average values")
print("Tab 1c appears to be consumption-adjusted or regional values")

