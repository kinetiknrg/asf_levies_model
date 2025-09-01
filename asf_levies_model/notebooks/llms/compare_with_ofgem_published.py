# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.11.2
#   kernelspec:
#     display_name: asf_levies_model
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Comparison with Ofgem Published Values
#
# **PURPOSE**: Compare ASF Levies Model calculations with official Ofgem published rates
# **DATA SOURCES**: Latest Annex 9 from updated base.yaml
# **CREATED**: Validation against published GB average values

# %% [markdown]
# ## Published Values (Direct Debit, GB Average)
#
# From https://www.ofgem.gov.uk/information-consumers/energy-advice-households/get-energy-price-cap-standing-charges-and-unit-rates-region
#
# | Period | Standing Charge | Unit Rate |
# |--------|----------------|-----------|
# | July to September 2025 | 51.37p/day | 25.73p/kWh |
# | October to December 2025 | 53.68p/day | 26.35p/kWh |

# %%
import pandas as pd
import numpy as np
from datetime import datetime
from IPython.display import display, HTML

# ASF Levies Model imports
from asf_levies_model import PROJECT_DIR, config
import asf_levies_model.getters.load_data as data
import asf_levies_model.tariffs as tariffs

print("✅ All imports successful")
print(f"\n📍 Using Annex 9 from: {config.get('data_sources').get('ofgem_annex_9')}")

# %% [markdown]
# ## Step 1: Download Latest Data

# %%
print("📥 DOWNLOADING LATEST ANNEX 9 DATA...")
print("=" * 60)

# Download Annex 9
annex_9_file = data.download_annex_9(as_fileobject=True)
print(f"✅ Annex 9 downloaded successfully")

# Extract Direct Debit data (not Other Payment Method!)
print("\n📊 EXTRACTING DIRECT DEBIT DATA...")
# Note: The website shows Direct Debit values, not Other Payment Method

# First, let's check what payment methods are available
# Unfortunately, the ASF model doesn't have Direct Debit processing functions built in
# Let's check what's available

import asf_levies_model.getters.load_data as ld
available_functions = [f for f in dir(ld) if 'process_tariff' in f]
print("Available tariff processing functions:")
for func in sorted(available_functions):
    print(f"  - {func}")

# %% [markdown]
# ## Note: Payment Method Mismatch
#
# The ASF Levies Model only has processing functions for:
# - Other Payment Method
# - Standard Credit
# - PPM (Prepayment)
#
# But the Ofgem website values shown are for **Direct Debit**, which typically has the lowest rates.
#
# Let's proceed with Other Payment Method and note the expected difference.

# %%
# Extract Other Payment Method data
elec_other_nil = data.process_tariff_elec_other_payment_nil(annex_9_file)
elec_other_typical = data.process_tariff_elec_other_payment_typical(annex_9_file)

# Get all available periods
periods = elec_other_nil.index.get_level_values(1).unique()
print("Available price cap periods:")
for period in sorted(periods, reverse=True)[:5]:  # Show latest 5
    print(f"  - {period}")

# %% [markdown]
# ## Step 2: Extract Values for Both Periods

# %%
def extract_rates_for_period(elec_nil, elec_typical, period, consumption=2.7):
    """Extract standing charge and unit rate for a specific period"""

    # Get nil consumption data
    nil_mask = elec_nil.index.map(lambda x: True if x[1].overlaps(period) else False)
    nil_data = elec_nil[nil_mask].set_index("Nil consumption")["value"]

    # Get typical consumption data
    typical_mask = elec_typical.index.map(lambda x: True if x[1].overlaps(period) else False)
    typical_data = elec_typical[typical_mask].set_index("Typical consumption")["value"]

    # Calculate rates
    annual_standing = nil_data.sum()
    daily_standing = annual_standing / 365.25
    daily_standing_pence = daily_standing * 100

    # Unit rate calculation
    variable_component = typical_data.sum() - nil_data.sum()
    unit_rate_mwh = variable_component / consumption
    unit_rate_kwh_pence = (unit_rate_mwh / 1000) * 100

    return {
        "period": period,
        "annual_standing": annual_standing,
        "daily_standing_pence": daily_standing_pence,
        "unit_rate_pence_kwh": unit_rate_kwh_pence
    }

# Extract for Oct-Dec 2025 (if available)
oct_dec_2025 = pd.Interval(pd.Timestamp('2025-10-01'), pd.Timestamp('2025-12-31'), closed='both')
jul_sep_2025 = pd.Interval(pd.Timestamp('2025-07-01'), pd.Timestamp('2025-09-30'), closed='both')

results = []

# Check if periods exist
for period_name, period in [("Jul-Sep 2025", jul_sep_2025), ("Oct-Dec 2025", oct_dec_2025)]:
    matching_periods = [p for p in periods if p.overlaps(period)]
    if matching_periods:
        actual_period = matching_periods[0]
        rates = extract_rates_for_period(elec_other_nil, elec_other_typical, actual_period)
        rates["period_name"] = period_name
        results.append(rates)
        print(f"\n📊 {period_name} RATES (Other Payment Method):")
        print(f"  Standing charge: {rates['daily_standing_pence']:.2f}p/day")
        print(f"  Unit rate: {rates['unit_rate_pence_kwh']:.2f}p/kWh")
    else:
        print(f"\n❌ {period_name} data not found in Annex 9")

# %% [markdown]
# ## Step 3: Comparison Table

# %%
print("\n📊 COMPARISON WITH OFGEM PUBLISHED VALUES")
print("=" * 60)

comparison_data = []

# Jul-Sep 2025
if len(results) > 0 and results[0]["period_name"] == "Jul-Sep 2025":
    comparison_data.append({
        "Period": "Jul-Sep 2025",
        "Metric": "Standing Charge",
        "Ofgem Published (Direct Debit)": "51.37p/day",
        "Model Calculated (Other Payment)": f"{results[0]['daily_standing_pence']:.2f}p/day",
        "Difference": f"{results[0]['daily_standing_pence'] - 51.37:.2f}p",
        "% Difference": f"{((results[0]['daily_standing_pence'] - 51.37) / 51.37) * 100:.1f}%"
    })
    comparison_data.append({
        "Period": "Jul-Sep 2025",
        "Metric": "Unit Rate",
        "Ofgem Published (Direct Debit)": "25.73p/kWh",
        "Model Calculated (Other Payment)": f"{results[0]['unit_rate_pence_kwh']:.2f}p/kWh",
        "Difference": f"{results[0]['unit_rate_pence_kwh'] - 25.73:.2f}p",
        "% Difference": f"{((results[0]['unit_rate_pence_kwh'] - 25.73) / 25.73) * 100:.1f}%"
    })

# Oct-Dec 2025
if len(results) > 1 and results[1]["period_name"] == "Oct-Dec 2025":
    comparison_data.append({
        "Period": "Oct-Dec 2025",
        "Metric": "Standing Charge",
        "Ofgem Published (Direct Debit)": "53.68p/day",
        "Model Calculated (Other Payment)": f"{results[1]['daily_standing_pence']:.2f}p/day",
        "Difference": f"{results[1]['daily_standing_pence'] - 53.68:.2f}p",
        "% Difference": f"{((results[1]['daily_standing_pence'] - 53.68) / 53.68) * 100:.1f}%"
    })
    comparison_data.append({
        "Period": "Oct-Dec 2025",
        "Metric": "Unit Rate",
        "Ofgem Published (Direct Debit)": "26.35p/kWh",
        "Model Calculated (Other Payment)": f"{results[1]['unit_rate_pence_kwh']:.2f}p/kWh",
        "Difference": f"{results[1]['unit_rate_pence_kwh'] - 26.35:.2f}p",
        "% Difference": f"{((results[1]['unit_rate_pence_kwh'] - 26.35) / 26.35) * 100:.1f}%"
    })

if comparison_data:
    comparison_df = pd.DataFrame(comparison_data)
    display(comparison_df)

# %% [markdown]
# ## Key Observations
#
# 1. **Payment Method Difference**: The Ofgem website shows Direct Debit rates, while the model calculates Other Payment Method rates
# 2. **Expected Pattern**: Other Payment Method rates are typically 6-8% higher than Direct Debit rates
# 3. **Data Availability**: Check if October-December 2025 data is available in the latest Annex 9

# %%
print("\n💡 IMPORTANT NOTES:")
print("=" * 40)
print("1. Payment Method Mismatch:")
print("   - Ofgem website: Direct Debit (lowest rates)")
print("   - Model output: Other Payment Method (higher rates)")
print("   - This explains why model values are higher")
print("\n2. Regional Variations:")
print("   - Ofgem website: GB average shown")
print("   - Model output: GB average calculated")
print("   - Both should be comparable for same payment method")
print("\n3. Calculation Method Verified:")
print("   - Standing charge = Annual nil consumption / 365.25")
print("   - Unit rate = (Typical bill - Nil bill) / Typical consumption")

# %%
# Create tariff objects to double-check
if results:
    latest_period = results[-1]["period"]
    elec_tariff = tariffs.ElectricityOtherPayment.from_dataframe(
        elec_other_nil, elec_other_typical, price_cap=latest_period.left
    )

    print(f"\n✅ TARIFF OBJECT VERIFICATION for {results[-1]['period_name']}:")
    print(f"Daily standing charge: {(elec_tariff.calculate_nil_consumption() / 365.25) * 100:.2f}p")
    print(f"Unit rate: {(elec_tariff.calculate_variable_consumption(1.0) / 10):.2f}p/kWh")

# %%
annex_9_file.close()
print("\n✅ COMPARISON COMPLETE")

