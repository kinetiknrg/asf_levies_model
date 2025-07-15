#!/usr/bin/env python3
"""
Diagnostic script to examine Excel file structure and find missing columns
"""

import pandas as pd
from asf_levies_model.getters.load_data import _get_excel_sheet_names
import warnings
warnings.filterwarnings('ignore')

def examine_excel_structure():
    # Path to the downloaded file
    excel_file = "inputs/data/raw/20250714_ofgem_annex_9.xlsx"

    print("🔍 EXAMINING EXCEL FILE STRUCTURE")
    print("=" * 50)

    # Get all sheet names
    print("\n📋 Available sheets:")
    sheets = _get_excel_sheet_names(excel_file)
    for i, sheet in enumerate(sheets, 1):
        print(f"  {i:2d}. {sheet}")

    # Look for tariff-related sheets
    tariff_sheets = [s for s in sheets if any(term in s.lower() for term in ['tariff', 'electricity', 'gas', 'standard', 'credit'])]

    print(f"\n⚡ Potential tariff-related sheets ({len(tariff_sheets)}):")
    for sheet in tariff_sheets:
        print(f"  - {sheet}")

    # Examine a few key sheets in detail
    key_sheets_to_examine = tariff_sheets[:3] if tariff_sheets else sheets[:3]

    print(f"\n🔬 DETAILED EXAMINATION")
    print("=" * 50)

    missing_columns = ['IC', 'CO', 'DRC']
    available_columns = ['DF', 'CM', 'AA', 'PC', 'NC', 'OC', 'SMNCC', 'PAAC', 'PAP', 'EBIT', 'HAP']

    found_missing = {}

    for sheet_name in key_sheets_to_examine:
        print(f"\n📊 Sheet: {sheet_name}")
        print("-" * 30)

        try:
            # Read the sheet
            df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
            print(f"  Shape: {df.shape}")

            # Look for our target columns in the entire sheet
            sheet_text = df.astype(str).values.flatten()
            sheet_content = ' '.join(sheet_text).upper()

            # Check for missing columns
            for col in missing_columns:
                if col in sheet_content:
                    # Find the exact location
                    locations = []
                    for i, row in df.iterrows():
                        for j, cell in row.items():
                            if str(cell).strip().upper() == col:
                                locations.append(f"Row {i+1}, Col {j+1}")

                    if locations:
                        print(f"  ✅ Found '{col}' at: {', '.join(locations[:3])}")
                        found_missing[col] = (sheet_name, locations)
                    else:
                        print(f"  ⚠️  '{col}' found in text but not as distinct cell")
                else:
                    print(f"  ❌ '{col}' not found")

            # Check for available columns
            available_in_sheet = []
            for col in available_columns:
                if col in sheet_content:
                    available_in_sheet.append(col)

            if available_in_sheet:
                print(f"  📍 Available columns: {', '.join(available_in_sheet)}")

            # Show some sample data structure
            print(f"  📄 Sample content (first 5x5):")
            sample = df.iloc[:5, :5].fillna('').astype(str)
            for i, row in sample.iterrows():
                row_str = ' | '.join([cell[:10].ljust(10) for cell in row])
                print(f"    {row_str}")

        except Exception as e:
            print(f"  ❌ Error reading sheet: {e}")

    print(f"\n🎯 SUMMARY")
    print("=" * 50)
    print(f"Missing columns that were found:")
    for col, (sheet, locations) in found_missing.items():
        print(f"  ✅ {col}: Found in '{sheet}' at {locations[0]}")

    not_found = [col for col in missing_columns if col not in found_missing]
    if not_found:
        print(f"Still missing: {', '.join(not_found)}")

    return found_missing, sheets

if __name__ == "__main__":
    examine_excel_structure()