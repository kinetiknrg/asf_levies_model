# Pattern Comparison Summary: ASF Levies Model

## Executive Summary

The ASF Levies Model code is consistent and well-structured, but there's a critical data source mismatch between what the model uses and what appears in the Ofgem screenshots.

## Pattern Confirmation

### 1. Data Flow Pattern (Consistent across all code)

**Original Developer's Pattern (`testing_tariff_update.py`):**
```python
# Step 1: Download Annex 9
fileobject = data.download_annex_9(as_fileobject=True)

# Step 2: Process nil and typical data
other_electricity_tariff = tariffs.ElectricityOtherPayment.from_dataframe(
    data.process_tariff_elec_other_payment_nil(fileobject),
    data.process_tariff_elec_other_payment_typical(fileobject),
)

# Step 3: Update policy costs
other_electricity_tariff = other_electricity_tariff.update_policy_costs(pc)
```

**LLM Diagnostic Pattern (identical):**
```python
# Same 3-step process
baseline_elec_tariff = tariffs.ElectricityOtherPayment.from_dataframe(
    elec_other_nil, elec_other_typical
)
baseline_elec_tariff = baseline_elec_tariff.update_policy_costs(pc)
```

### 2. Core Calculation in `tariffs.py` (Line 849)

```python
typical_df = (typical_df - nil_df.fillna(0)) / typical_consumption
```

This formula is correct: `Unit Rate = (Typical Annual Bill - Nil Annual Bill) / Typical Consumption`

### 3. Data Extraction Pattern in `load_data.py`

All tariff processing functions follow this pattern:
```python
def process_tariff_[fuel]_[payment_method]_[consumption_type]:
    return _process_tariff(payment_method, consumption_type, fuel_type, fileobject)
    
def _process_tariff:
    return _tidy_tariff_table(_extract_tariff_table(...))
    
def _extract_tariff_table:
    # Extracts from Tab "1c Consumption adjusted levels"
```

## Critical Finding: Tab Reference Discrepancy

### Model Uses:
- **Tab 1c: "Consumption adjusted levels"**
  - Nil: £186.60 ✅
  - Typical: £864.16 ❌

### Screenshots Show:
- **Tab 1a: "Levelised DTC"** (GB average)
  - Nil: £186.60 ✅
  - Typical: £964.54 ✅

### Impact:
- £100 difference in typical consumption bill
- Affects unit rate by approximately 3.7p/kWh
- Standing charge calculations are correct (both tabs have same nil value)

## Why Different Tabs?

**Tab 1a (Levelised DTC):**
- Contains GB average values
- Direct match to published Ofgem rates
- Likely the "official" published values

**Tab 1c (Consumption adjusted levels):**
- Contains adjusted values (possibly regional weightings?)
- Used consistently throughout the codebase
- May be the "working" values for calculations

## Recommendations

1. **Immediate**: Add documentation explaining why Tab 1c is used instead of Tab 1a
2. **Investigation**: Determine if Tab 1c applies regional adjustments that explain the £100 difference
3. **Validation**: Create tests comparing Tab 1a (published) vs Tab 1c (model) values
4. **Enhancement**: Add option to select which tab to use for validation purposes

## Code Quality Assessment

✅ **Strengths:**
- Consistent patterns throughout
- Clear separation of concerns
- Proper abstraction layers
- No hard-coded values in core logic

⚠️ **Potential Issues:**
- Tab selection is buried deep in `_extract_tariff_table`
- No documentation explaining tab choice
- Discrepancy with published values not flagged

The code follows best practices and is NOT defective - but it uses a different data source than expected, which explains the discrepancy with published Ofgem values.

