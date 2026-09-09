"""
Data Preprocessing Script for Smart Agriculture AI Platform.
Cleans raw/sample IoT sensor data and outputs cleaned dataset to data/processed/.

Runnable from project root:
    python ml/preprocess_data.py
"""

import os
import sys
import pandas as pd

def preprocess_iot_data(input_path="data/sample/iot_sensor_data.csv", output_path="data/processed/iot_sensor_data_clean.csv"):
    print("=" * 60)
    print("⚙️ SMART AGRICULTURE AI PLATFORM - DATA PREPROCESSING")
    print("=" * 60)
    print(f"Input Dataset:  {input_path}")
    print(f"Output Dataset: {output_path}")

    if not os.path.exists(input_path):
        print(f"❌ ERROR: Input file '{input_path}' not found.")
        return False

    # 1. Load Data
    df = pd.read_csv(input_path)
    initial_count = len(df)
    print(f"\n1. Loaded {initial_count} raw records.")

    # 2. Convert Timestamp to Datetime
    print("2. Converting timestamp column to datetime format...")
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # 3. Handle Duplicate Records
    duplicates_before = df.duplicated().sum()
    if duplicates_before > 0:
        df = df.drop_duplicates().reset_index(drop=True)
        print(f"   Removed {duplicates_before} duplicate records.")
    else:
        print("   ✓ No duplicate records found.")

    # 4. Handle Missing Values Safely
    missing_before = df.isnull().sum().sum()
    if missing_before > 0:
        print(f"   Handling {missing_before} missing values...")
        # Sort chronologically by farm and timestamp before forward filling
        df = df.sort_values(by=["farm_id", "timestamp"]).reset_index(drop=True)
        
        # Numeric columns get forward filled then median filled
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        df[numeric_cols] = df.groupby('farm_id')[numeric_cols].ffill()
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())

        # Drop any remaining unfillable nulls
        df = df.dropna().reset_index(drop=True)
        print(f"   ✓ Missing values resolved.")
    else:
        print("   ✓ Zero missing values detected.")

    # 5. Sort chronologically
    df = df.sort_values(by="timestamp").reset_index(drop=True)

    # 6. Save Processed Clean Dataset
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    final_count = len(df)

    print(f"\n3. Preprocessing Complete:")
    print(f"   - Initial rows: {initial_count}")
    print(f"   - Final cleaned rows: {final_count}")
    print(f"   - Clean dataset saved to: '{output_path}'")
    print("=" * 60)
    print("✅ DATA PREPROCESSING SUCCESSFUL")
    print("=" * 60)
    return True

if __name__ == "__main__":
    input_path = "data/sample/iot_sensor_data.csv"
    output_path = "data/processed/iot_sensor_data_clean.csv"
    
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]

    success = preprocess_iot_data(input_path, output_path)
    if not success:
        sys.exit(1)
