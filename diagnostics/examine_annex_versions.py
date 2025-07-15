#!/usr/bin/env python3
"""
Script to examine all Annex file versions and add them to context window
Updated to examine the correct sheet: "1c Consumption adjusted levels"
"""

import pandas as pd
from asf_levies_model.getters.load_data import _get_excel_sheet_names
import warnings
import os
warnings.filterwarnings('ignore')

def examine_all_annex_files():
    """Examine all Annex files and display their structure for context"""

    data_dir = "inputs/data/raw/"

    # Find all Annex files
    annex_files = []
    for filename in os.listdir(data_dir):
        if filename.endswith('.xlsx') and ('annex' in filename.lower() or 'levelisation' in filename.lower()):
            annex_files.append(filename)

    annex_files.sort()  # Sort for consistent ordering

    print("🗂️  ANNEX FILE VERSIONS ANALYSIS - CORRECT SHEET")
    print("=" * 60)
    print(f"Found {len(annex_files)} Annex files:")

    for i, filename in enumerate(annex_files, 1):
        size = os.path.getsize(os.path.join(data_dir, filename))
        print(f"  {i}. {filename} ({size/1024:.0f}KB)")

    # Target the correct sheet where the code expects data
    target_sheet = "1c Consumption adjusted levels"

    # Examine each file
    target_columns = ['IC', 'CO', 'DRC']  # Missing columns
    known_columns = ['DF', 'CM', 'AA', 'PC', 'NC', 'OC', 'SMNCC', 'PAAC', 'PAP', 'EBIT', 'HAP']

    file_analysis = {}

    for filename in annex_files:
        filepath = os.path.join(data_dir, filename)
        print(f"\n📄 ANALYZING: {filename}")
        print("=" * 60)

        try:
            # Get sheet names
            sheets = _get_excel_sheet_names(filepath)
            print(f"📋 Total sheets: {len(sheets)}")

            # Check if target sheet exists
            target_sheet_exists = target_sheet in sheets
            consumption_sheets = [s for s in sheets if 'consumption' in s.lower()]

            print(f"🎯 Target sheet '{target_sheet}': {'✅ Found' if target_sheet_exists else '❌ Missing'}")
            if consumption_sheets:
                print(f"📋 Consumption-related sheets: {consumption_sheets}")

            if target_sheet_exists:
                print(f"\n🔬 DETAILED EXAMINATION: '{target_sheet}'")
                print("-" * 50)

                try:
                    # Read the sheet
                    df = pd.read_excel(filepath, sheet_name=target_sheet, header=None)
                    print(f"Shape: {df.shape}")

                    # Convert to string and search for columns
                    sheet_content = df.astype(str).values.flatten()
                    sheet_text = ' '.join(sheet_content).upper()

                    # Check for target columns
                    found_targets = []
                    for col in target_columns:
                        if col in sheet_text:
                            # Find exact locations
                            locations = []
                            for i, row in df.iterrows():
                                for j, cell in row.items():
                                    if str(cell).strip().upper() == col:
                                        locations.append((i+1, j+1))

                            if locations:
                                found_targets.append((col, locations[:5]))  # Show more locations
                                print(f"  ✅ {col}: Found at rows {[loc[0] for loc in locations[:5]]}")
                            else:
                                print(f"  ⚠️  '{col}' found in text but not as distinct cell")
                        else:
                            print(f"  ❌ '{col}' not found anywhere")

                    # Check for known columns
                    found_known = []
                    for col in known_columns:
                        if col in sheet_text:
                            found_known.append(col)

                    print(f"  📍 Known columns found: {', '.join(found_known)} ({len(found_known)}/{len(known_columns)})")

                    # Show sample structure around rows with our target columns
                    if found_targets:
                        print(f"\n📄 Sample data around target columns:")
                        for col, locations in found_targets:
                            if locations:
                                row_idx = locations[0][0] - 1  # Convert to 0-based
                                start_row = max(0, row_idx - 3)
                                end_row = min(len(df), row_idx + 4)
                                sample = df.iloc[start_row:end_row, :min(15, df.shape[1])]

                                print(f"\n  {col} context (rows {start_row+1}-{end_row}):")
                                for idx, (i, row) in enumerate(sample.iterrows()):
                                    marker = ">>> " if i == row_idx else "    "
                                    row_str = ' | '.join([str(cell)[:10].ljust(10) for cell in row])
                                    print(f"  {marker}{row_str}")
                    else:
                        # Show sample of the sheet structure anyway
                        print(f"\n📄 Sample sheet structure (first 10x10):")
                        sample = df.iloc[:10, :10].fillna('')
                        for i, row in sample.iterrows():
                            row_str = ' | '.join([str(cell)[:10].ljust(10) for cell in row])
                            print(f"    {row_str}")

                    # Store analysis results
                    file_analysis[filename] = {
                        'sheets': sheets,
                        'target_sheet_exists': target_sheet_exists,
                        'found_targets': found_targets,
                        'found_known': found_known,
                        'shape': df.shape,
                        'consumption_sheets': consumption_sheets
                    }

                except Exception as e:
                    print(f"  ❌ Error examining sheet '{target_sheet}': {e}")
                    # Try to examine any consumption-related sheet as fallback
                    if consumption_sheets:
                        fallback_sheet = consumption_sheets[0]
                        print(f"  🔄 Trying fallback sheet: '{fallback_sheet}'")
                        try:
                            df_fallback = pd.read_excel(filepath, sheet_name=fallback_sheet, header=None)
                            print(f"  📊 Fallback sheet shape: {df_fallback.shape}")
                        except Exception as e2:
                            print(f"  ❌ Fallback also failed: {e2}")
            else:
                print(f"  ⚠️  Target sheet '{target_sheet}' not found")
                print(f"  📋 Available sheets: {sheets}")

        except Exception as e:
            print(f"  ❌ Error analyzing file: {e}")

    # Summary comparison
    print(f"\n🎯 SUMMARY COMPARISON - '{target_sheet}' SHEET")
    print("=" * 60)

    for filename, analysis in file_analysis.items():
        if analysis.get('target_sheet_exists'):
        found_target_names = [item[0] for item in analysis.get('found_targets', [])]
        missing_targets = [col for col in target_columns if col not in found_target_names]

        print(f"\n📊 {filename}:")
        print(f"  ✅ Has target columns: {', '.join(found_target_names) if found_target_names else 'None'}")
        print(f"  ❌ Missing columns: {', '.join(missing_targets) if missing_targets else 'None'}")
        print(f"  📍 Known columns: {len(analysis.get('found_known', []))}/{len(known_columns)}")
            print(f"  📏 Sheet size: {analysis.get('shape', 'Unknown')}")
        else:
            print(f"\n📊 {filename}: ❌ Target sheet missing")

    # Overall summary
    files_with_target_sheet = sum(1 for a in file_analysis.values() if a.get('target_sheet_exists'))
    files_with_all_targets = sum(1 for a in file_analysis.values()
                               if len(a.get('found_targets', [])) == len(target_columns))

    print(f"\n📈 OVERALL SUMMARY:")
    print(f"  📁 Files with target sheet: {files_with_target_sheet}/{len(file_analysis)}")
    print(f"  ✅ Files with all target columns: {files_with_all_targets}/{len(file_analysis)}")

    return file_analysis

if __name__ == "__main__":
    examine_all_annex_files()