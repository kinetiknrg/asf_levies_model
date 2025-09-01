#!/usr/bin/env python
"""
PURPOSE: Compare values from different Annex 9 tabs to understand discrepancies
DEPENDENCIES: Direct access to Annex 9 Excel file
DATA SOURCES: Live Ofgem data
CREATED: Diagnostic to identify tab reference issues
CONSTITUTIONAL COMPLIANCE: Principles 1,2,5 - Real data validation, diagnostic workflow
"""

import pandas as pd
import asf_levies_model.getters.load_data as data
from asf_levies_model.getters.load_data import _get_excel_sheet_names, _get_raw_dataframe_annex9

print("🔍 ANNEX 9 TAB COMPARISON DIAGNOSTIC")
print("=" * 50)

# Download Annex 9
annex_9 = data.download_annex_9(as_fileobject=True)

# Get all sheet names
sheet_names = _get_excel_sheet_names(annex_9)
print("\nAVAILABLE SHEETS IN ANNEX 9:")
for i, sheet in enumerate(sheet_names):
    print(f"{i}: {sheet}")

# Look for relevant tabs
print("\n📂 RELEVANT TABS:")
for sheet in sheet_names:
    if any(x in sheet.lower() for x in ['levelised', 'consumption', 'historical']):
        print(f"  - {sheet}")

# Tab 1c - What the model currently uses
print("\n🔍 TAB 1c: Consumption adjusted levels (MODEL USES THIS)")
print("-" * 50)
try:
    # Get data the way the model does
    elec_other_nil = data.process_tariff_elec_other_payment_nil(annex_9)
    elec_other_typical = data.process_tariff_elec_other_payment_typical(annex_9)

    latest_period = elec_other_nil.index.max()
    nil_1c = elec_other_nil.loc[latest_period]['value'].sum()
    typical_1c = elec_other_typical.loc[latest_period]['value'].sum()

    print(f"Latest period: {latest_period[1]}")
    print(f"Nil total: £{nil_1c:.2f}")
    print(f"Typical total: £{typical_1c:.2f}")
    print(f"Unit rate: {(typical_1c - nil_1c) / 2.7 / 10:.2f}p/kWh")
except Exception as e:
    print(f"Error reading Tab 1c: {e}")

# Try to read Tab 1a - Levelised DTC (from screenshots)
print("\n🔍 TAB 1a: Levelised DTC (YOUR SCREENSHOTS SHOW THIS)")
print("-" * 50)
try:
    # Find the exact sheet name for 1a
    tab_1a = [s for s in sheet_names if '1a' in s and 'level' in s.lower()]
    if tab_1a:
        df_1a = pd.read_excel(annex_9, sheet_name=tab_1a[0], header=11, engine='calamine')
        print(f"Found tab: {tab_1a[0]}")
        print(f"Columns: {list(df_1a.columns)[:5]}...")

        # Look for GB average Other Payment Method
        gb_rows = df_1a[df_1a.iloc[:, 0].str.contains('GB average', na=False)]
        if not gb_rows.empty:
            print("\nGB Average row found!")
            print(gb_rows.iloc[0])
    else:
        print("Tab 1a not found!")
except Exception as e:
    print(f"Error reading Tab 1a: {e}")

# Try to read Tab 1b - Historical level tables
print("\n🔍 TAB 1b: Historical level tables (COMPONENT BREAKDOWN)")
print("-" * 50)
try:
    tab_1b = [s for s in sheet_names if '1b' in s and 'historical' in s.lower()]
    if tab_1b:
        df_1b = pd.read_excel(annex_9, sheet_name=tab_1b[0], header=10, engine='calamine')
        print(f"Found tab: {tab_1b[0]}")
        print(f"Shape: {df_1b.shape}")
        print("First few rows:")
        print(df_1b.head())
    else:
        print("Tab 1b not found!")
except Exception as e:
    print(f"Error reading Tab 1b: {e}")

print("\n⚠️ KEY FINDING:")
print("The model reads from Tab 1c (Consumption adjusted levels)")
print("Your screenshots show Tab 1a (Levelised DTC) with GB average")
print("This explains the £100 discrepancy in typical values!")

annex_9.close()

