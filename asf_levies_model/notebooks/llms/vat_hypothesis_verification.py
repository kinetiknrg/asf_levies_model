#!/usr/bin/env python
"""
PURPOSE: Verify if VAT explains the 5% discrepancy
DEPENDENCIES: Mathematical verification
DATA SOURCES: Published rates vs Annex 9 values
CREATED: VAT hypothesis testing
CONSTITUTIONAL COMPLIANCE: Principles 1,2 - Real data validation
"""

print("💡 VAT HYPOTHESIS VERIFICATION")
print("=" * 50)

# UK domestic energy VAT rate
VAT_RATE = 1.05  # 5% VAT

print(f"\nUK Domestic Energy VAT Rate: 5%")
print(f"Multiplier: {VAT_RATE}")

print("\n📊 TESTING WITH KNOWN VALUES:")

# From Annex 9 Tab 1a (likely ex-VAT)
nil_ex_vat = 186.60
typical_ex_vat = 964.54

# Calculate rates ex-VAT
standing_ex_vat = nil_ex_vat / 365 * 100  # pence per day
unit_ex_vat = (typical_ex_vat - nil_ex_vat) / 3.1 / 10  # pence per kWh

print(f"\nAnnex 9 Tab 1a values (assumed ex-VAT):")
print(f"Standing charge: {standing_ex_vat:.2f}p/day")
print(f"Unit rate: {unit_ex_vat:.2f}p/kWh")

# Apply VAT
standing_inc_vat = standing_ex_vat * VAT_RATE
unit_inc_vat = unit_ex_vat * VAT_RATE

print(f"\nAfter applying 5% VAT:")
print(f"Standing charge: {standing_inc_vat:.2f}p/day")
print(f"Unit rate: {unit_inc_vat:.2f}p/kWh")

# Published values for comparison
print(f"\nPublished Ofgem values (inc VAT):")
print(f"Standing charge: 53.68p/day")
print(f"Unit rate: 26.35p/kWh")

# Calculate match percentage
standing_match = (standing_inc_vat / 53.68) * 100
unit_match = (unit_inc_vat / 26.35) * 100

print(f"\nMatch percentage:")
print(f"Standing: {standing_match:.1f}%")
print(f"Unit: {unit_match:.1f}%")

print("\n✅ CONCLUSION:")
if 99 < standing_match < 101 and 99 < unit_match < 101:
    print("VAT PERFECTLY EXPLAINS THE DISCREPANCY!")
else:
    print("VAT explains most but not all of the discrepancy")

print("\n🔍 DETAILED BREAKDOWN:")
print(f"\nStanding charge calculation:")
print(f"£{nil_ex_vat} ÷ 365 × 100 = {standing_ex_vat:.2f}p/day (ex-VAT)")
print(f"{standing_ex_vat:.2f}p × 1.05 = {standing_inc_vat:.2f}p/day (inc-VAT)")
print(f"Published: 53.68p/day")
print(f"Remaining gap: {53.68 - standing_inc_vat:.2f}p ({((53.68/standing_inc_vat)-1)*100:.1f}%)")

print(f"\nUnit rate calculation:")
print(f"(£{typical_ex_vat} - £{nil_ex_vat}) ÷ 3.1 ÷ 10 = {unit_ex_vat:.2f}p/kWh (ex-VAT)")
print(f"{unit_ex_vat:.2f}p × 1.05 = {unit_inc_vat:.2f}p/kWh (inc-VAT)")
print(f"Published: 26.35p/kWh")
print(f"Remaining gap: {26.35 - unit_inc_vat:.2f}p ({((26.35/unit_inc_vat)-1)*100:.1f}%)")

print("\n📝 VERIFICATION WITH TAB 1c DATA:")
# Tab 1c values
nil_1c = 186.60
typical_1c = 864.16

standing_1c_ex = nil_1c / 365 * 100
unit_1c_ex = (typical_1c - nil_1c) / 2.7 / 10

standing_1c_inc = standing_1c_ex * VAT_RATE
unit_1c_inc = unit_1c_ex * VAT_RATE

print(f"\nTab 1c (model uses):")
print(f"Ex-VAT: {standing_1c_ex:.2f}p/day standing, {unit_1c_ex:.2f}p/kWh unit")
print(f"Inc-VAT: {standing_1c_inc:.2f}p/day standing, {unit_1c_inc:.2f}p/kWh unit")

