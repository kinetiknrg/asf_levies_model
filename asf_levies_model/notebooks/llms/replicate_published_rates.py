#!/usr/bin/env python
"""
PURPOSE: Attempt to replicate published Ofgem rates using Tab 1a data
DEPENDENCIES: Direct Excel reading to access Tab 1a
DATA SOURCES: Ofgem Annex 9 Tab 1a (Levelised DTC)
CREATED: Diagnostic to match published values
CONSTITUTIONAL COMPLIANCE: Principles 1,2,5 - Real data validation
"""

import pandas as pd
import asf_levies_model.getters.load_data as data
from asf_levies_model.getters.load_data import _get_raw_dataframe_annex9

print("🎯 REPLICATING PUBLISHED OFGEM RATES")
print("=" * 50)

# Published values for comparison
print("\n📊 PUBLISHED OFGEM VALUES (Direct Debit, GB Average):")
print("Jul-Sep 2025: 51.37p/day standing, 25.73p/kWh unit")
print("Oct-Dec 2025: 53.68p/day standing, 26.35p/kWh unit")

# Download Annex 9
annex_9 = data.download_annex_9(as_fileobject=True)

# Try to read Tab 1a directly
print("\n🔍 EXTRACTING TAB 1a DATA (Levelised DTC)...")
try:
    # Read the specific sheet
    tab_1a = _get_raw_dataframe_annex9(annex_9, "1a Levelised DTC")
    print(f"Tab 1a shape: {tab_1a.shape}")

    # Find GB average section for Other Payment Method
    # Looking for the pattern shown in screenshots
    print("\n📋 SEARCHING FOR GB AVERAGE VALUES...")

    # Try to find nil and typical rows
    # Based on screenshot structure, look for "Nil kWh" and "m (3,100 kWh)"

    # First, let's see what the dataframe looks like
    print("\nFirst 50 rows of Tab 1a:")
    print(tab_1a.head(50))

except Exception as e:
    print(f"Error reading Tab 1a: {e}")

print("\n💡 MANUAL CALCULATION FROM SCREENSHOT VALUES:")
print("Using Tab 1a values from your screenshots...")

# From screenshots - Oct-Dec 2025 period
nil_1a = 186.60  # GB average nil
typical_1a = 964.54  # GB average at 3,100 kWh

print(f"\nTab 1a values (Oct-Dec 2025):")
print(f"Nil: £{nil_1a:.2f}")
print(f"Typical (3,100 kWh): £{typical_1a:.2f}")

# Calculate rates
standing_daily = nil_1a / 365 * 100  # Convert to pence
unit_rate = (typical_1a - nil_1a) / 3.1 / 10  # £/MWh to p/kWh

print(f"\nCALCULATED RATES:")
print(f"Standing charge: {standing_daily:.2f}p/day")
print(f"Unit rate: {unit_rate:.2f}p/kWh")

print(f"\nCOMPARISON WITH PUBLISHED:")
print(f"Standing: {standing_daily:.2f}p/day vs 53.68p/day published")
print(f"Unit: {unit_rate:.2f}p/kWh vs 26.35p/kWh published")

print("\n🔍 INVESTIGATING DISCREPANCY...")
print("Even with Tab 1a data, we get:")
print("- Standing: 51.12p/day (not 53.68p/day)")
print("- Unit: 25.09p/kWh (not 26.35p/kWh)")

print("\n📐 PAYMENT METHOD ADJUSTMENT?")
print("Published rates are for Direct Debit")
print("Annex 9 'Other Payment Method' might need adjustment")

# Estimate adjustment factor
standing_factor = 53.68 / 51.12
unit_factor = 26.35 / 25.09

print(f"\nImplied adjustment factors:")
print(f"Standing: {standing_factor:.3f} ({(standing_factor-1)*100:.1f}% higher)")
print(f"Unit: {unit_factor:.3f} ({(unit_factor-1)*100:.1f}% higher)")

print("\n🤔 POSSIBLE EXPLANATIONS:")
print("1. Payment method adjustment (~5% for credit vs direct debit)")
print("2. Additional adjustments not visible in Annex 9")
print("3. Different rounding methodology")
print("4. Time period differences (snapshot vs average)")

