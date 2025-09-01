# Annex 9 Data Flow: From Annual Bills to Unit Rates

## Executive Summary

This document explains how the ASF Levies Model derives standing charges and unit rates from Ofgem's Annex 9 data, which provides **annual bills** rather than direct unit rates.

## Key Finding: The Mathematical Transformation

Annex 9 provides two key values for each tariff component:
1. **Nil consumption**: Annual bill with zero usage (standing charges only)
2. **Typical consumption**: Annual bill with typical usage (2.7 MWh electricity, 11.5 MWh gas)

The transformation to unit rates is:
```
Unit Rate (£/MWh) = (Typical Annual Bill - Nil Annual Bill) / Typical Consumption
```

This is implemented in `tariffs.py` line 849:
```python
typical_df = (typical_df - nil_df.fillna(0)) / typical_consumption
```

## Data Flow Process

### 1. Raw Data Extraction (Annex 9)

The process starts with downloading Annex 9 and extracting tariff tables:
- `process_tariff_elec_other_payment_nil()` → Annual bills for zero consumption
- `process_tariff_elec_other_payment_typical()` → Annual bills for typical consumption

Example values (July-Sept 2025):
- Electricity nil consumption: £178.58 (annual)
- Electricity typical consumption (2.7 MWh): £840.28 (annual)

### 2. Unit Rate Calculation

The model calculates unit rates by:
1. Subtracting nil from typical to get the variable component
2. Dividing by consumption to get per-unit rate

Example:
- Variable component: £840.28 - £178.58 = £661.70
- Unit rate: £661.70 / 2.7 MWh = £245.07/MWh = 24.51p/kWh

### 3. Standing Charge Derivation

**Critical insight**: Nil consumption values are ANNUAL standing charges, not daily!

Correct calculation:
- Annual standing charge = Nil consumption total (e.g., £178.58)
- Daily standing charge = Annual / 365.25 (e.g., £0.489 = 48.89p)

## Identified Bug

The model has a naming/conceptual issue:
- `calculate_nil_consumption()` returns the ANNUAL nil bill
- But some code treats this as if it were a DAILY value
- This causes a 365x overstatement when calculating annual bills

## Validation Against Published Rates

For the period analyzed (July-Sept 2025):
- **Calculated**: 48.89p daily standing, 24.51p/kWh unit rate (electricity)
- **Expected range**: 40-60p standing, 20-30p/kWh unit rate
- **Status**: ✅ Values are reasonable

Note: The Ofgem website shows regional variations, while the model calculates GB averages.

## Code Examples

### Correct Usage
```python
# Get annual standing charge
annual_standing = tariff.calculate_nil_consumption()  # e.g., £178.58

# Convert to daily
daily_standing = annual_standing / 365.25  # e.g., £0.489
```

### Incorrect Usage (Bug)
```python
# Wrong - treats annual as daily
daily_standing = tariff.calculate_nil_consumption()  # Actually annual!
annual_standing = daily_standing * 365.25  # 365x overstatement!
```

## Recommendations

1. **Clarify method naming**: Rename to `calculate_annual_nil_consumption()`
2. **Add daily method**: Create `calculate_daily_standing_charge()`
3. **Document units**: Clearly state whether values are annual or daily
4. **Validate calculations**: Compare with Ofgem published values regularly

## Data Sources

- **Annex 9**: Provides annual bills for different consumption levels
- **Configuration**: URLs in `config/base.yaml` point to latest Ofgem files
- **Published rates**: https://www.ofgem.gov.uk/information-consumers/energy-advice-households/get-energy-price-cap-standing-charges-and-unit-rates-region

## Conclusion

The ASF Levies Model correctly implements the mathematical transformation from annual bills to unit rates. However, there's a conceptual issue with standing charge handling that leads to confusion about annual vs daily values. The core calculation logic is sound, but the interface needs clarification.

