# %%
import pandas as pd

from datetime import datetime

from asf_levies_model import PROJECT_DIR

import asf_levies_model.getters.load_data as data
import asf_levies_model.levies as levies
import asf_levies_model.tariffs as tariffs

# %%
"""
Setting up Levies and LevyCollection
"""

# %%
# Get Annex 4
fileobject = data.download_annex_4(as_fileobject=True)

# %%
# Denominator values from Desnz subnational consumption domestic data, 2023
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
total_supply_elec = (
    249_044_438  # DESNZ GB total electricity consumption - all meters (2023)
)
unscaled_fit = levies.FIT.from_dataframe(
    data.process_data_FIT(fileobject),
)
exempt_eii_supply = unscaled_fit.ExemptSupplyEII
fit_scaling_factor = supply_elec / (total_supply_elec - exempt_eii_supply)

# %%
# Scaling factor for estimating domestic share of NCC revenue
unscaled_ncc = levies.NCC.from_dataframe(
    data.process_data_NCC(fileobject),
)
ncc_eligible_supply = unscaled_ncc.EligibleDemand
ncc_scaling_factor = supply_elec / ncc_eligible_supply

# %%
# Instantiate LevyCollection with scaled levies

list_levies = [
    levies.RO.from_dataframe(data.process_data_RO(fileobject), denominator=supply_elec),
    levies.AAHEDC.from_dataframe(
        data.process_data_AAHEDC(fileobject), denominator=supply_elec
    ),
    levies.GGL.from_dataframe(
        data.process_data_GGL(fileobject), denominator=customers_gas
    ),
    levies.WHD.from_dataframe(
        data.process_data_WHD(fileobject),
        customers_gas=customers_gas,
        customers_elec=customers_elec,
    ),
    levies.ECO4.from_dataframe(data.process_data_ECO(fileobject)),  # Split ECO
    levies.GBIS.from_dataframe(data.process_data_ECO(fileobject)),  # Split ECO
    levies.FIT.from_dataframe(
        data.process_data_FIT(fileobject),
        scaling_factor=fit_scaling_factor,
    ),
    levies.NCC.from_dataframe(
        data.process_data_NCC(fileobject), scaling_factor=ncc_scaling_factor
    ),
]


pc = levies.LevyCollection("Policy Costs", "pc", list_levies, denominator_values)

# Rebalance to denominators
pc = pc.rebalance_to_denominators()

# %%
"""
Setting up Tariffs
"""

# %%
# Get Annex 9
fileobject = data.download_annex_9(as_fileobject=True)

# %%
# Other Payment Method Tariffs
other_gas_tariff = tariffs.GasOtherPayment.from_dataframe(
    data.process_tariff_gas_other_payment_nil(fileobject),
    data.process_tariff_gas_other_payment_typical(fileobject),
)
other_electricity_tariff = tariffs.ElectricityOtherPayment.from_dataframe(
    data.process_tariff_elec_other_payment_nil(fileobject),
    data.process_tariff_elec_other_payment_typical(fileobject),
)


# Update policy costs with denominator rebalanced policy costs
other_gas_tariff = other_gas_tariff.update_policy_costs(pc)
other_electricity_tariff = other_electricity_tariff.update_policy_costs(pc)

# Check values
other_gas_tariff.calculate_total_consumption(
    11.5, vat=True
) + other_electricity_tariff.calculate_total_consumption(2.7, vat=True)

# %%
# Standard Credit Tariffs
credit_gas_tariff = tariffs.GasStandardCredit.from_dataframe(
    data.process_tariff_gas_standard_credit_nil(fileobject),
    data.process_tariff_gas_standard_credit_typical(fileobject),
)
credit_electricity_tariff = tariffs.ElectricityStandardCredit.from_dataframe(
    data.process_tariff_elec_standard_credit_nil(fileobject),
    data.process_tariff_elec_standard_credit_typical(fileobject),
)


# Update policy costs with denominator rebalanced policy costs
credit_gas_tariff = credit_gas_tariff.update_policy_costs(pc)
credit_electricity_tariff = credit_electricity_tariff.update_policy_costs(pc)

# Check values
credit_gas_tariff.calculate_total_consumption(
    11.5, vat=True
) + credit_electricity_tariff.calculate_total_consumption(2.7, vat=True)

# %%
# PPM Tariffs
ppm_gas_tariff = tariffs.GasPPM.from_dataframe(
    data.process_tariff_gas_ppm_nil(fileobject),
    data.process_tariff_gas_ppm_typical(fileobject),
)
ppm_electricity_tariff = tariffs.ElectricityPPM.from_dataframe(
    data.process_tariff_elec_ppm_nil(fileobject),
    data.process_tariff_elec_ppm_typical(fileobject),
)


# Update policy costs with denominator rebalanced policy costs
ppm_gas_tariff = ppm_gas_tariff.update_policy_costs(pc)
ppm_electricity_tariff = ppm_electricity_tariff.update_policy_costs(pc)

# Check values
ppm_gas_tariff.calculate_total_consumption(
    11.5, vat=True
) + ppm_electricity_tariff.calculate_total_consumption(2.7, vat=True)

# %%
"""
Display Detailed Tariff Rates - Other Payment Method
"""

print("="*60)
print("OTHER PAYMENT METHOD TARIFF RATES")
print("="*60)

# Electricity Tariff Components
print("\n🔌 ELECTRICITY (Single-Rate) - Other Payment Method")
print("-" * 50)
print("FIXED COMPONENTS (£/year):")
print(f"  Direct Fuel (Standing):     £{other_electricity_tariff.df_nil:.2f}")
print(f"  Network Costs (Standing):   £{other_electricity_tariff.nc_nil:.2f}")
print(f"  Policy Costs (Standing):    £{other_electricity_tariff.pc_nil:.2f}")
print(f"  Operating Costs (Standing): £{other_electricity_tariff.oc_nil:.2f}")
print(f"  Other Fixed Components:     £{(other_electricity_tariff.calculate_nil_consumption() - other_electricity_tariff.df_nil - other_electricity_tariff.nc_nil - other_electricity_tariff.pc_nil - other_electricity_tariff.oc_nil):.2f}")
print(f"  → TOTAL STANDING CHARGE:    £{other_electricity_tariff.calculate_nil_consumption():.2f}/year")

print(f"\nVARIABLE COMPONENTS (£/MWh):")
print(f"  Direct Fuel (Unit):         £{other_electricity_tariff.df:.2f}/MWh")
print(f"  Network Costs (Unit):       £{other_electricity_tariff.nc:.2f}/MWh")
print(f"  Policy Costs (Unit):        £{other_electricity_tariff.pc:.2f}/MWh")
print(f"  Operating Costs (Unit):     £{other_electricity_tariff.oc:.2f}/MWh")
print(f"  Other Variable Components:  £{(other_electricity_tariff.calculate_variable_consumption(1.0) - other_electricity_tariff.df - other_electricity_tariff.nc - other_electricity_tariff.pc - other_electricity_tariff.oc):.2f}/MWh")
print(f"  → TOTAL UNIT RATE:          £{other_electricity_tariff.calculate_variable_consumption(1.0):.2f}/MWh")

# Convert to pence/kWh for comparison with Ofgem data
unit_rate_p_kwh = other_electricity_tariff.calculate_variable_consumption(1.0) / 10
standing_charge_p_day = other_electricity_tariff.calculate_nil_consumption() / 365.25 * 100
print(f"\n📊 OFGEM FORMAT:")
print(f"  Unit Rate:        {unit_rate_p_kwh:.2f}p/kWh")
print(f"  Standing Charge:  {standing_charge_p_day:.2f}p/day")

# Gas Tariff Components
print("\n🔥 GAS - Other Payment Method")
print("-" * 50)
print("FIXED COMPONENTS (£/year):")
print(f"  Direct Fuel (Standing):     £{other_gas_tariff.df_nil:.2f}")
print(f"  Network Costs (Standing):   £{other_gas_tariff.nc_nil:.2f}")
print(f"  Policy Costs (Standing):    £{other_gas_tariff.pc_nil:.2f}")
print(f"  Operating Costs (Standing): £{other_gas_tariff.oc_nil:.2f}")
print(f"  Other Fixed Components:     £{(other_gas_tariff.calculate_nil_consumption() - other_gas_tariff.df_nil - other_gas_tariff.nc_nil - other_gas_tariff.pc_nil - other_gas_tariff.oc_nil):.2f}")
print(f"  → TOTAL STANDING CHARGE:    £{other_gas_tariff.calculate_nil_consumption():.2f}/year")

print(f"\nVARIABLE COMPONENTS (£/MWh):")
print(f"  Direct Fuel (Unit):         £{other_gas_tariff.df:.2f}/MWh")
print(f"  Network Costs (Unit):       £{other_gas_tariff.nc:.2f}/MWh")
print(f"  Policy Costs (Unit):        £{other_gas_tariff.pc:.2f}/MWh")
print(f"  Operating Costs (Unit):     £{other_gas_tariff.oc:.2f}/MWh")
print(f"  Other Variable Components:  £{(other_gas_tariff.calculate_variable_consumption(1.0) - other_gas_tariff.df - other_gas_tariff.nc - other_gas_tariff.pc - other_gas_tariff.oc):.2f}/MWh")
print(f"  → TOTAL UNIT RATE:          £{other_gas_tariff.calculate_variable_consumption(1.0):.2f}/MWh")

# Convert to pence/kWh for comparison
gas_unit_rate_p_kwh = other_gas_tariff.calculate_variable_consumption(1.0) / 10
gas_standing_charge_p_day = other_gas_tariff.calculate_nil_consumption() / 365.25 * 100
print(f"\n📊 OFGEM FORMAT:")
print(f"  Unit Rate:        {gas_unit_rate_p_kwh:.2f}p/kWh")
print(f"  Standing Charge:  {gas_standing_charge_p_day:.2f}p/day")

# Typical Bill Calculation
print("\n" + "="*60)
print("TYPICAL HOUSEHOLD BILL (Other Payment Method)")
print("="*60)
elec_bill = other_electricity_tariff.calculate_total_consumption(2.7, vat=True)
gas_bill = other_gas_tariff.calculate_total_consumption(11.5, vat=True)
total_bill = elec_bill + gas_bill

print(f"Electricity (2.7 MWh):  £{elec_bill:.2f}/year")
print(f"Gas (11.5 MWh):         £{gas_bill:.2f}/year")
print(f"TOTAL DUAL FUEL:        £{total_bill:.2f}/year")
print(f"Monthly equivalent:     £{total_bill/12:.2f}/month")

# %%
"""
Confirm Price Cap Period and Regional Analysis
"""

print("="*70)
print("PRICE CAP PERIOD & REGIONAL ANALYSIS")
print("="*70)

# Check which price cap period is being used
print(f"📅 PRICE CAP PERIOD: {other_electricity_tariff.price_cap_period}")
print(f"📍 CURRENT DATA SOURCE: GB Average (from Annex 9)")

# Extract South East specific data
print(f"\n🎯 EXTRACTING SOUTH EAST REGIONAL RATES...")

# Get raw South East data
def extract_south_east_tariff_data(fileobject, fuel_type, consumption_type):
    """Extract South East specific tariff data from Annex 9"""
    # Get the raw dataframe
    df = data._get_raw_dataframe_annex9("Consumption adjusted levels", fileobject)

    # Extract Other Payment Method section
    payment_method = "Other Payment Method"
    start_index = df.index[df["Historical level tables"] == payment_method].tolist()[0]

    # Find end of section (look for next payment method)
    try:
        next_payment_start = df.index[df["Historical level tables"] == "Standard Credit"].tolist()[0]
        end_index = next_payment_start - 1
    except:
        end_index = len(df)

    # Isolate Other Payment Method section
    payment_df = df.iloc[start_index:end_index, :].copy()
    payment_df = payment_df.dropna(axis="index", how="all").dropna(axis="columns", how="all").reset_index(drop=True)

    # Forward fill column names
    payment_df = payment_df.ffill(axis="columns").infer_objects(copy=False)

    # Find fuel type columns
    fuel_columns = []
    for column in payment_df.columns:
        if payment_df[column].str.contains(fuel_type, na=False, regex=False).any():
            fuel_columns.append(column)

    if not fuel_columns:
        return None

    fuel_df = payment_df[fuel_columns]

    # Find consumption type section
    start_consumption = fuel_df.index[fuel_df[fuel_columns[0]] == consumption_type].tolist()
    if not start_consumption:
        return None
    start_consumption = start_consumption[0]

    # Extract the consumption section (next 20 rows should cover all regions)
    consumption_df = fuel_df.iloc[start_consumption:start_consumption+25, :].copy()
    consumption_df.columns = consumption_df.iloc[0]
    consumption_df = consumption_df.iloc[1:]

    # Find South East row
    south_east_mask = consumption_df[consumption_type].str.contains("South East", na=False, regex=False)
    if south_east_mask.any():
        return consumption_df[south_east_mask].iloc[0]
    else:
        return None

# Reopen fileobject for South East extraction
fileobject = data.download_annex_9(as_fileobject=True)

# Extract South East electricity data
se_elec_nil = extract_south_east_tariff_data(fileobject, "Electricity: Single-Rate Metering Arrangement", "Nil consumption")
se_elec_typical = extract_south_east_tariff_data(fileobject, "Electricity: Single-Rate Metering Arrangement", "Typical consumption")

# Extract South East gas data
se_gas_nil = extract_south_east_tariff_data(fileobject, "Gas", "Nil consumption")
se_gas_typical = extract_south_east_tariff_data(fileobject, "Gas", "Typical consumption")

# Initialize variables for comparison
se_elec_unit_pence = "N/A"
se_elec_standing_pence = "N/A"
se_gas_unit_pence = "N/A"
se_gas_standing_pence = "N/A"

if se_elec_nil is not None and se_elec_typical is not None:
    try:
        print("✅ South East electricity data found")
        # Calculate South East electricity rates
        se_elec_standing = float(se_elec_nil.iloc[1])  # Second column has the £ values
        se_elec_typical_bill = float(se_elec_typical.iloc[1])
        se_elec_unit_cost = (se_elec_typical_bill - se_elec_standing) / 2.7  # 2.7 MWh typical
        se_elec_unit_pence = se_elec_unit_cost / 10  # Convert to pence/kWh
        se_elec_standing_pence = se_elec_standing / 365.25 * 100  # Convert to pence/day

        print(f"🔌 SOUTH EAST ELECTRICITY (Other Payment Method):")
        print(f"   Unit Rate:        {se_elec_unit_pence:.2f}p/kWh")
        print(f"   Standing Charge:  {se_elec_standing_pence:.2f}p/day")
    except Exception as e:
        print(f"❌ Error processing South East electricity data: {e}")
        se_elec_unit_pence = "Error"
        se_elec_standing_pence = "Error"
else:
    print("❌ Could not extract South East electricity data")

if se_gas_nil is not None and se_gas_typical is not None:
    try:
        print("✅ South East gas data found")
        # Calculate South East gas rates
        se_gas_standing = float(se_gas_nil.iloc[1])  # Second column has the £ values
        se_gas_typical_bill = float(se_gas_typical.iloc[1])
        se_gas_unit_cost = (se_gas_typical_bill - se_gas_standing) / 11.5  # 11.5 MWh typical
        se_gas_unit_pence = se_gas_unit_cost / 10  # Convert to pence/kWh
        se_gas_standing_pence = se_gas_standing / 365.25 * 100  # Convert to pence/day

        print(f"🔥 SOUTH EAST GAS (Other Payment Method):")
        print(f"   Unit Rate:        {se_gas_unit_pence:.2f}p/kWh")
        print(f"   Standing Charge:  {se_gas_standing_pence:.2f}p/day")
    except Exception as e:
        print(f"❌ Error processing South East gas data: {e}")
        se_gas_unit_pence = "Error"
        se_gas_standing_pence = "Error"
else:
    print("❌ Could not extract South East gas data")

print(f"\n📊 COMPARISON - GB AVERAGE vs SOUTH EAST:")
print(f"Electricity Unit Rate:    {unit_rate_p_kwh:.2f}p/kWh (GB) vs {se_elec_unit_pence}p/kWh (SE)")
print(f"Electricity Standing:     {standing_charge_p_day:.2f}p/day (GB) vs {se_elec_standing_pence}p/day (SE)")
print(f"Gas Unit Rate:            {gas_unit_rate_p_kwh:.2f}p/kWh (GB) vs {se_gas_unit_pence}p/kWh (SE)")
print(f"Gas Standing:             {gas_standing_charge_p_day:.2f}p/day (GB) vs {se_gas_standing_pence}p/day (SE)")

# Debug: Let's see what regional data is actually available
print(f"\n🔍 DEBUG: Available Regional Data Structure:")
try:
    df_debug = data._get_raw_dataframe_annex9("Consumption adjusted levels", fileobject)
    # Find Other Payment Method section
    start_idx = df_debug.index[df_debug["Historical level tables"] == "Other Payment Method"].tolist()[0]
    debug_section = df_debug.iloc[start_idx:start_idx+50, :5]  # First 5 columns, 50 rows
    print("First few rows of Other Payment Method section:")
    print(debug_section.head(20))
except Exception as e:
    print(f"Debug failed: {e}")

# %%
"""
DIAGNOSTIC: What does the working code actually do?
"""

print("🔍 DIAGNOSTIC: Understanding the Working Code Path")
print("="*60)

# 1. What tab does the working code target?
print("1. Checking what _get_raw_dataframe_annex9 targets:")
fileobject = data.download_annex_9(as_fileobject=True)

# Check what sheets exist
try:
    import zipfile
    import re
    with zipfile.ZipFile(fileobject, "r") as zip_ref:
        xml = zip_ref.read("xl/workbook.xml").decode("utf-8")
    sheets = []
    for s_tag in re.findall("<sheet [^>]*", xml):
        sheets.append(re.search('name="[^"]*', s_tag).group(0)[6:])
    print(f"   Available sheets: {sheets}")
    fileobject.seek(0)  # Reset fileobject
except Exception as e:
    print(f"   Could not read sheets: {e}")

# 2. What does process_tariff_elec_other_payment_nil actually extract?
print("\n2. What does process_tariff_elec_other_payment_nil() return?")
nil_data = data.process_tariff_elec_other_payment_nil(fileobject)
print(f"   Columns: {list(nil_data.columns)}")
print(f"   Index levels: {nil_data.index.names}")
print(f"   Shape: {nil_data.shape}")
print(f"   Index sample: {nil_data.index[:3].tolist()}")

# 3. What does process_tariff_elec_other_payment_typical actually extract?
print("\n3. What does process_tariff_elec_other_payment_typical() return?")
fileobject.seek(0)
typical_data = data.process_tariff_elec_other_payment_typical(fileobject)
print(f"   Columns: {list(typical_data.columns)}")
print(f"   Index levels: {typical_data.index.names}")
print(f"   Shape: {typical_data.shape}")
print(f"   Index sample: {typical_data.index[:3].tolist()}")

# 4. Show actual data structure
print("\n4. Sample of actual working data:")
print("   Nil data:")
print(nil_data.head())
print("   Typical data:")
print(typical_data.head())

fileobject.close()
