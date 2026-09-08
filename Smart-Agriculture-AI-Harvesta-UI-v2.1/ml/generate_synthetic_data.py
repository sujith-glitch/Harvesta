"""
Synthetic IoT Sensor Data Generator for Smart Agriculture AI Platform.

NOTE: THIS DATASET CONTAINS SYNTHETIC / SIMULATED DATA FOR DEVELOPMENT PURPOSES ONLY.
IT DOES NOT REPRESENT REAL PHYSICAL SENSOR READINGS OR REAL-WORLD FARM LOCATIONS.
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_iot_sensor_data(num_records=1000, output_path="../data/sample/iot_sensor_data.csv"):
    np.random.seed(42)
    random.seed(42)

    farms = ["FARM001", "FARM002", "FARM003", "FARM004", "FARM005"]
    farm_crop_map = {
        "FARM001": "Rice",
        "FARM002": "Tomato",
        "FARM003": "Maize",
        "FARM004": "Cotton",
        "FARM005": "Wheat"
    }

    base_ph_map = {
        "Rice": 6.2,
        "Tomato": 6.5,
        "Maize": 6.8,
        "Cotton": 7.1,
        "Wheat": 6.4
    }

    start_time = datetime(2026, 1, 1, 0, 0, 0)
    data = []

    # Current state tracking per farm
    farm_moisture = {farm: random.uniform(45.0, 65.0) for farm in farms}

    for i in range(num_records):
        timestamp = start_time + timedelta(hours=i)
        hour = timestamp.hour
        day_of_year = timestamp.timetuple().tm_yday

        # Pick farm round-robin or randomly
        farm_id = farms[i % len(farms)]
        crop_type = farm_crop_map[farm_id]

        # Diurnal temperature cycle: coolest around 5 AM, warmest around 3 PM (15:00)
        diurnal = 8.0 * np.sin((hour - 9) * np.pi / 12.0)
        temp_base = 25.0 + diurnal + np.random.normal(0, 1.5)
        temperature = round(float(np.clip(temp_base, 12.0, 42.0)), 2)

        # Soil temperature lags ambient temp
        soil_temp = round(float(np.clip(temperature * 0.85 + 3.0 + np.random.normal(0, 0.5), 10.0, 35.0)), 2)

        # Rainfall simulation: ~8% chance of rain event
        rain_event = np.random.random() < 0.08
        if rain_event:
            rainfall = round(float(np.random.exponential(scale=8.0) + 1.0), 2)
            rainfall = min(rainfall, 45.0)
        else:
            rainfall = 0.0

        # Humidity: inversely proportional to temp, increased by rainfall
        humidity_base = 85.0 - (temperature - 15.0) * 1.8 + (rainfall * 0.5) + np.random.normal(0, 2.0)
        humidity = round(float(np.clip(humidity_base, 30.0, 95.0)), 2)

        # Soil moisture physics correlation
        current_m = farm_moisture[farm_id]
        if rainfall > 0:
            current_m += rainfall * 0.75
        else:
            # Evapotranspiration depletion based on temperature
            current_m -= 0.15 + max(0, (temperature - 22.0) * 0.05)
        
        # Clip soil moisture to realistic bounds [15%, 85%]
        current_m = round(float(np.clip(current_m, 15.0, 85.0)), 2)
        farm_moisture[farm_id] = current_m
        soil_moisture = current_m

        # Soil pH: stable per crop with minor noise
        soil_ph = round(float(np.clip(base_ph_map[crop_type] + np.random.normal(0, 0.08), 5.5, 7.8)), 2)

        data.append({
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "farm_id": farm_id,
            "crop_type": crop_type,
            "soil_moisture": soil_moisture,
            "temperature": temperature,
            "humidity": humidity,
            "rainfall": rainfall,
            "soil_ph": soil_ph,
            "soil_temperature": soil_temp
        })

    df = pd.DataFrame(data)

    # Make directory if not exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} synthetic records in '{output_path}'.")
    return df

if __name__ == "__main__":
    generate_iot_sensor_data()
