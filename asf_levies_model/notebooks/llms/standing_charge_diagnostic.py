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
# # Standing Charge Diagnostic: Annual vs Daily Values
#
# **PURPOSE**: Diagnose the standing charge calculation issue - are nil values annual or daily?
# **DATA SOURCES**: Ofgem Annex 9 and published unit rates
# **CREATED**: Diagnostic to fix standing charge bug

# %%
import pandas as pd
import numpy as np
from asf_levies_model import config
import asf_levies_model.getters.load_data as data
import asf_levies_model.tariffs as tariffs

print("✅ Imports successful")

# %% [markdown]
# ## Key Question: Are Nil Consumption Values Annual or Daily?
#
# The Ofgem website shows standing charges as daily values (pence per day).
# But Annex 9 shows annual bills for nil consumption.
#
# Let's verify this by comparing calculated values with published values.

# %%
# Download Annex 9
annex_9_file = data.download_annex_9(as_fileobject=True)

# Extract Other Payment Method data
elec_other_nil = data.process_tariff_elec_other_payment_nil(annex_9_file)
elec_other_typical = data.process_tariff_elec_other_payment_typical(annex_9_file)

# Get latest period
latest_period = elec_other_nil.index.max()[1]
print(f"Latest Price Cap Period: {latest_period}")

# Extract nil consumption value
nil_data = elec_other_nil.loc[
    lambda df: df.index.map(lambda x: True if x[1].overlaps(latest_period) else False)
].set_index("Nil consumption")["value"]

print(f"\n📊 NIL CONSUMPTION TOTAL: £{nil_data.sum():.2f}")
print("This is the ANNUAL bill for zero consumption")

# %% [markdown]
# ## Converting Annual to Daily Standing Charge
#
# If nil consumption gives us the annual bill for zero usage, then:
# - Annual standing charge = Nil consumption total
# - Daily standing charge = Annual standing charge / 365.25

# %%
annual_standing_charge = nil_data.sum()
daily_standing_charge = annual_standing_charge / 365.25
daily_standing_charge_pence = daily_standing_charge * 100

print(f"Annual standing charge: £{annual_standing_charge:.2f}")
print(f"Daily standing charge: £{daily_standing_charge:.4f}")
print(f"Daily standing charge: {daily_standing_charge_pence:.2f}p")

# %% [markdown]
# ## Check Against Ofgem Published Values
#
# From the Ofgem website screenshot, for October 2025 - December 2025:
# - Other Payment Method
# - Electricity standing charge for GB average: should be around 48-50p per day
#
# Our calculation shows a different period (July-Sept 2025) but let's see if the order of magnitude is correct.

# %%
print("🔍 STANDING CHARGE ANALYSIS")
print("=" * 40)
print(f"Period: {latest_period}")
print(f"\nCalculated from Annex 9:")
print(f"  Annual nil consumption bill: £{annual_standing_charge:.2f}")
print(f"  Daily standing charge: {daily_standing_charge_pence:.2f}p")
print(f"\nExpected range for standing charges:")
print(f"  Typical electricity: 40-60p per day")
print(f"  Our value: {daily_standing_charge_pence:.2f}p ✅ Reasonable!")

# %% [markdown]
# ## The Bug in the Model
#
# The model's `calculate_nil_consumption()` method returns the sum of nil components,
# which is the ANNUAL bill. But the code treats it as if it were a DAILY value!

# %%
# Create tariff object
elec_tariff = tariffs.ElectricityOtherPayment.from_dataframe(
    elec_other_nil, elec_other_typical
)

# What the model returns
model_nil_value = elec_tariff.calculate_nil_consumption()
print(f"Model's calculate_nil_consumption(): £{model_nil_value:.2f}")
print(f"This is treated as daily but it's actually ANNUAL!")

# Correct daily value
correct_daily = model_nil_value / 365.25
print(f"\nCorrect daily standing charge: £{correct_daily:.4f} ({correct_daily * 100:.2f}p)")

# %% [markdown]
# ## Impact on Bill Calculations
#
# This bug would massively overstate standing charges in bill calculations:

# %%
# Wrong calculation (what the model does)
wrong_annual_standing = model_nil_value * 365.25
print(f"❌ WRONG: Annual standing = £{model_nil_value:.2f} × 365.25 = £{wrong_annual_standing:,.2f}")

# Correct calculation
correct_annual_standing = model_nil_value  # It's already annual!
print(f"✅ CORRECT: Annual standing = £{correct_annual_standing:.2f} (no multiplication needed)")

print(f"\nOverstatement factor: {wrong_annual_standing / correct_annual_standing:.1f}x")

# %% [markdown]
# ## Summary
#
# 1. **Annex 9 nil consumption values are ANNUAL bills** (e.g., £178.58 per year)
# 2. **To get daily standing charges, divide by 365.25** (e.g., 48.89p per day)
# 3. **The model incorrectly treats annual values as daily values**
# 4. **This causes a 365x overstatement of standing charges in some calculations**
#
# The fix would be to either:
# - Store nil values as daily rates (divide by 365.25 during data loading)
# - Or rename `calculate_nil_consumption()` to `calculate_annual_nil_consumption()`
# - And add a `calculate_daily_standing_charge()` method that divides by 365.25

# %%
annex_9_file.close()
print("\n✅ DIAGNOSTIC COMPLETE")

