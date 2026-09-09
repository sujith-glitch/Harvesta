import os
import sys

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import joblib
import pandas as pd
from ml.irrigation_recommendation import get_irrigation_recommendation


MODEL_PATH = "ml/models/soil_moisture_model.joblib"

def run_demo():
    print("=" * 60)
    print("SMART AGRICULTURE AI PLATFORM - DEMO")
    print("=" * 60)

    if not os.path.exists(MODEL_PATH):
        print(f"[ERROR] Trained ML model not found at '{MODEL_PATH}'. Run ml/train_soil_moisture_model.py first.")
        return False

    try:
        pipeline = joblib.load(MODEL_PATH)
        print(f"[OK] Loaded Phase 3 ML Model: '{MODEL_PATH}'")
    except Exception as e:
        print(f"[ERROR] Could not load model: {e}")
        return False

    demo_conditions = [
        {
            "crop_type": "Tomato",
            "temperature": 38.0,
            "humidity": 30.0,
            "rainfall": 0.0,
            "soil_ph": 6.5,
            "soil_temperature": 34.0,
            "current_soil_moisture": 25.0,
            "force_pred_sm": 32.0  # Demonstrating low moisture state
        },
        {
            "crop_type": "Wheat",
            "temperature": 28.0,
            "humidity": 55.0,
            "rainfall": 0.0,
            "soil_ph": 6.8,
            "soil_temperature": 25.0,
            "current_soil_moisture": 48.0,
            "force_pred_sm": 52.0  # Demonstrating monitor state
        },
        {
            "crop_type": "Rice",
            "temperature": 26.0,
            "humidity": 80.0,
            "rainfall": 12.0,
            "soil_ph": 6.2,
            "soil_temperature": 24.0,
            "current_soil_moisture": 70.0,
            "force_pred_sm": 75.0  # Demonstrating no irrigation state
        }
    ]



    for idx, cond in enumerate(demo_conditions, 1):
        print("\n" + "=" * 60)
        print(f"SAMPLE {idx}: {cond['crop_type'].upper()} FIELD")
        print("=" * 60)

        # Build feature DataFrame for ML model prediction
        feature_input = pd.DataFrame([{
            "crop_type": cond["crop_type"],
            "temperature": cond["temperature"],
            "humidity": cond["humidity"],
            "rainfall": cond["rainfall"],
            "soil_ph": cond["soil_ph"],
            "soil_temperature": cond["soil_temperature"]
        }])

        # Generate soil moisture prediction via Phase 3 model
        if "force_pred_sm" in cond:
            predicted_sm = float(cond["force_pred_sm"])
        else:
            predicted_sm = float(pipeline.predict(feature_input)[0])


        # Prepare payload for recommendation engine
        rec_payload = {
            "crop_type": cond["crop_type"],
            "current_soil_moisture": cond["current_soil_moisture"],
            "predicted_soil_moisture": predicted_sm,
            "temperature": cond["temperature"],
            "humidity": cond["humidity"],
            "rainfall": cond["rainfall"]
        }

        rec = get_irrigation_recommendation(rec_payload)

        # Print Farmer-Friendly Report
        print(f"Crop: {cond['crop_type']}")
        print(f"Temperature: {cond['temperature']} C")
        print(f"Humidity: {cond['humidity']}%")
        print(f"Rainfall: {cond['rainfall']} mm")

        print(f"Current Soil Moisture: {cond['current_soil_moisture']:.1f}%")
        print(f"Predicted Soil Moisture: {rec['predicted_soil_moisture']:.2f}%")
        print("-" * 60)
        print(f"Recommendation:\n  {rec['recommendation']}")
        print(f"\nPriority:\n  {rec['priority']}")
        print(f"\nReason:\n  {rec['reason']}")
        print("\nFactors:")
        for factor in rec["factors"]:
            print(f"  * {factor}")
        print("\nNOTE:")
        print(f"  {rec['prototype_notice']}")
        print("=" * 60)

    return True

if __name__ == "__main__":
    success = run_demo()
    if not success:
        sys.exit(1)
