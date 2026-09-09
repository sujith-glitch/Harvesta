"""
Data Validation Script for Smart Agriculture AI Platform.
Verifies structure, completeness, and value ranges of the IoT sensor dataset.

Runnable from project root:
    python ml/data_validation.py
"""

import os
import sys
import pandas as pd

REQUIRED_COLUMNS = [
    "timestamp",
    "farm_id",
    "crop_type",
    "soil_moisture",
    "temperature",
    "humidity",
    "rainfall",
    "soil_ph",
    "soil_temperature"
]

EXPECTED_ROW_COUNT = 1000

NUMERIC_RANGES = {
    "soil_moisture": (0.0, 100.0),
    "temperature": (-10.0, 60.0),
    "humidity": (0.0, 100.0),
    "rainfall": (0.0, 500.0),
    "soil_ph": (0.0, 14.0),
    "soil_temperature": (-10.0, 60.0)
}

def validate_dataset(filepath="data/sample/iot_sensor_data.csv"):
    print("=" * 60)
    print("SMART AGRICULTURE AI PLATFORM - DATA VALIDATION")
    print("=" * 60)
    print(f"Target File: {filepath}")

    if not os.path.exists(filepath):
        print(f"[FAIL] File does not exist at '{filepath}'")
        return False

    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        print(f"[FAIL] Could not read CSV file. Error: {e}")
        return False

    validation_passed = True

    # 1. Check Row Count
    actual_rows = len(df)
    print(f"\n1. Row Count Check:")
    print(f"   Expected: {EXPECTED_ROW_COUNT} | Actual: {actual_rows}")
    if actual_rows != EXPECTED_ROW_COUNT:
        print(f"   ⚠️ WARNING: Row count mismatch (expected {EXPECTED_ROW_COUNT}, got {actual_rows})")
        validation_passed = False
    else:
        print("   ✓ Row count check PASSED")

    # 2. Check Required Columns
    print(f"\n2. Required Columns Check:")
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        print(f"   ❌ Missing columns: {missing_cols}")
        validation_passed = False
    else:
        print("   ✓ All required columns present")

    # 3. Check Missing Values
    print(f"\n3. Missing Values Check:")
    null_counts = df.isnull().sum()
    total_nulls = null_counts.sum()
    if total_nulls > 0:
        print(f"   ❌ Found {total_nulls} missing values:")
        for col, count in null_counts.items():
            if count > 0:
                print(f"      - {col}: {count}")
        validation_passed = False
    else:
        print("   ✓ Zero missing values found")

    # 4. Check Duplicate Rows
    print(f"\n4. Duplicate Rows Check:")
    duplicate_count = df.duplicated().sum()
    if duplicate_count > 0:
        print(f"   ❌ Found {duplicate_count} duplicate rows")
        validation_passed = False
    else:
        print("   ✓ Zero duplicate rows found")

    # 5. Check Numeric Ranges
    print(f"\n5. Numeric Range Bounds Check:")
    for col, (min_val, max_val) in NUMERIC_RANGES.items():
        if col in df.columns:
            actual_min = df[col].min()
            actual_max = df[col].max()
            if actual_min < min_val or actual_max > max_val:
                print(f"   ❌ Range violation for '{col}': [{actual_min}, {actual_max}] outside allowed [{min_val}, {max_val}]")
                validation_passed = False
            else:
                print(f"   ✓ '{col}': range [{actual_min:.2f}, {actual_max:.2f}] is valid (allowed [{min_val}, {max_val}])")

    # 6. Basic Statistics Summary
    print(f"\n6. Summary Statistics:")
    numeric_cols = list(NUMERIC_RANGES.keys())
    stats_df = df[numeric_cols].agg(['mean', 'std', 'min', 'max']).T
    print(stats_df.to_string())

    print("\n" + "=" * 60)
    if validation_passed:
        print("✅ OVERALL DATA VALIDATION STATUS: PASSED")
        print("=" * 60)
        return True
    else:
        print("❌ OVERALL DATA VALIDATION STATUS: FAILED")
        print("=" * 60)
        return False

if __name__ == "__main__":
    filepath = "data/sample/iot_sensor_data.csv"
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    
    success = validate_dataset(filepath)
    if not success:
        sys.exit(1)
