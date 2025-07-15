#!/usr/bin/env python3
"""
Test to prove the column access vs fillna timing issue
"""

import pandas as pd
from asf_levies_model.getters.load_data import process_tariff_elec_standard_credit_nil

def test_column_access_issue():
    print("🔬 TESTING COLUMN ACCESS vs FILLNA TIMING")
    print("=" * 50)

    # Get the actual dataframe
    df = process_tariff_elec_standard_credit_nil()
    print(f"DataFrame shape: {df.shape}")
    print(f"Available columns: {list(df['Nil consumption'].unique())}")

    # Simulate the processing that happens in from_dataframe
    nil_price_cap = df.index.max()[1]
    processed_df = (
        df.loc[
            lambda df: df.index.map(
                lambda x: True if x[1].overlaps(nil_price_cap) else False
            )
        ]
        .set_index("Nil consumption")
        .loc[:, "value"]
    )

    print(f"\nProcessed dataframe index: {processed_df.index.tolist()}")

    # Test 1: Direct column access (this should fail)
    print(f"\n🧪 Test 1: Direct column access")
    try:
        ic_value = processed_df["IC"]
        print(f"  ✅ IC accessed directly: {ic_value}")
    except KeyError as e:
        print(f"  ❌ KeyError on direct access: {e}")

    # Test 2: fillna approach (this should work)
    print(f"\n🧪 Test 2: fillna approach")
    try:
        df_with_fillna = processed_df.fillna(0)
        print(f"  ✅ fillna(0) works, shape: {df_with_fillna.shape}")
        print(f"  📊 Sample values: {dict(df_with_fillna.head())}")
    except Exception as e:
        print(f"  ❌ Error with fillna: {e}")

    # Test 3: .get() approach (this should work)
    print(f"\n🧪 Test 3: .get() approach")
    try:
        ic_value_get = processed_df.get("IC", 0.0)
        co_value_get = processed_df.get("CO", 0.0)
        drc_value_get = processed_df.get("DRC", 0.0)
        print(f"  ✅ IC via .get(): {ic_value_get}")
        print(f"  ✅ CO via .get(): {co_value_get}")
        print(f"  ✅ DRC via .get(): {drc_value_get}")
    except Exception as e:
        print(f"  ❌ Error with .get(): {e}")

    # Test 4: Working columns
    print(f"\n🧪 Test 4: Known working columns")
    try:
        df_value = processed_df["DF"]
        cm_value = processed_df["CM"]
        print(f"  ✅ DF works: {df_value}")
        print(f"  ✅ CM works: {cm_value}")
    except Exception as e:
        print(f"  ❌ Error with working columns: {e}")

    print(f"\n🎯 CONCLUSION:")
    print(f"The original code expected missing VALUES, not missing COLUMNS.")
    print(f"Solution: Use .get() for potentially missing columns before fillna.")

if __name__ == "__main__":
    test_column_access_issue()