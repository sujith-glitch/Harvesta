"""
Explainable Irrigation Recommendation Engine for Smart Agriculture AI Platform.

Translates environmental conditions, current soil moisture, predicted soil moisture,
and crop reference data into transparent, explainable farmer recommendations.

States:
  1. IRRIGATION_REQUIRED
  2. MONITOR
  3. NO_IRRIGATION_NEEDED

Runnable from project root:
    python ml/irrigation_recommendation.py
"""

import os
import sys
import pandas as pd

CROP_REF_PATH = "data/sample/crop_reference_data.csv"
PROTOTYPE_NOTICE = "This is a prototype recommendation based on development/synthetic data."

# Base threshold assumptions per water requirement level
WATER_REQ_THRESHOLDS = {
    "High": {"low": 55.0, "high": 75.0},
    "Medium": {"low": 45.0, "high": 68.0},
    "Low": {"low": 35.0, "high": 60.0}
}

def load_crop_reference_data(filepath=CROP_REF_PATH):
    """Loads crop reference dataset if available."""
    if os.path.exists(filepath):
        try:
            return pd.read_csv(filepath)
        except Exception:
            return None
    return None

def get_irrigation_recommendation(input_data):
    """
    Generates an explainable irrigation recommendation based on environmental
    features, current/predicted soil moisture, and crop specifications.
    
    Returns a dictionary with recommendation, priority, metrics, reason, and factors.
    """
    # 1. Extract & Sanitize Inputs
    if not isinstance(input_data, dict):
        input_data = {}

    crop_type = str(input_data.get("crop_type", "Tomato")).strip()
    current_sm = float(input_data.get("current_soil_moisture", 50.0))
    predicted_sm = float(input_data.get("predicted_soil_moisture", 50.0))
    temperature = float(input_data.get("temperature", 25.0))
    humidity = float(input_data.get("humidity", 60.0))
    rainfall = float(input_data.get("rainfall", 0.0))

    # 2. Look up Crop Reference Data
    crop_ref_df = load_crop_reference_data()
    water_req = "Medium"
    growth_days = None

    if crop_ref_df is not None and "crop_type" in crop_ref_df.columns:
        matching = crop_ref_df[crop_ref_df["crop_type"].str.lower() == crop_type.lower()]
        if not matching.empty:
            water_req = matching.iloc[0].get("water_requirement", "Medium")
            growth_days = matching.iloc[0].get("growth_period_days", None)

    thresholds = WATER_REQ_THRESHOLDS.get(water_req, WATER_REQ_THRESHOLDS["Medium"])
    low_thresh = thresholds["low"]
    high_thresh = thresholds["high"]

    # 3. Decision Logic & Rule Evaluation
    factors = []
    recommendation = "MONITOR"
    priority = "MEDIUM"
    reason = ""

    # Evaluate Moisture Level
    effective_sm = min(current_sm, predicted_sm)
    
    # Factor logging
    factors.append(f"Predicted soil moisture is {predicted_sm:.2f}% (Current: {current_sm:.2f}%).")
    factors.append(f"Target crop '{crop_type}' has a '{water_req}' water requirement (Low threshold: {low_thresh:.1f}%, High threshold: {high_thresh:.1f}%).")

    if rainfall >= 5.0:
        factors.append(f"Recent precipitation of {rainfall:.1f}mm will naturally recharge root-zone soil moisture.")
        if predicted_sm >= low_thresh - 5.0:
            recommendation = "NO_IRRIGATION_NEEDED"
            priority = "LOW"
            reason = f"Natural rainfall of {rainfall:.1f}mm provides sufficient moisture recharge. Additional irrigation is not recommended."
        else:
            recommendation = "MONITOR"
            priority = "MEDIUM"
            reason = f"Soil moisture is low ({predicted_sm:.2f}%), but recent rainfall of {rainfall:.1f}mm is expected to replenish soil water. Monitor soil levels before irrigating."

    elif predicted_sm < low_thresh:
        # Moisture is below recommended threshold without rain
        recommendation = "IRRIGATION_REQUIRED"
        
        if temperature >= 30.0 or current_sm < 30.0:
            priority = "HIGH"
            reason = f"Predicted soil moisture ({predicted_sm:.2f}%) is below the minimum threshold ({low_thresh:.1f}%) for {crop_type}. Elevated temperature ({temperature:.1f} C) increases crop water stress."
            factors.append(f"High ambient temperature ({temperature:.1f} C) accelerates evapotranspiration.")

        else:
            priority = "MEDIUM"
            reason = f"Predicted soil moisture ({predicted_sm:.2f}%) is below the minimum optimal threshold ({low_thresh:.1f}%) for {crop_type}."

        if humidity < 40.0:
            factors.append(f"Low relative atmospheric humidity ({humidity:.1f}%) increases crop transpiration demand.")

    elif predicted_sm >= high_thresh:
        recommendation = "NO_IRRIGATION_NEEDED"
        priority = "LOW"
        reason = f"Soil moisture ({predicted_sm:.2f}%) is at or above optimal capacity ({high_thresh:.1f}%). No additional watering required."
        factors.append(f"Soil moisture reserves ({predicted_sm:.2f}%) are well within optimal bounds.")

    else:
        # Intermediate range
        recommendation = "MONITOR"
        if temperature >= 32.0:
            priority = "MEDIUM"
            reason = f"Soil moisture ({predicted_sm:.2f}%) is in an acceptable range ({low_thresh:.1f}% - {high_thresh:.1f}%), but warm weather ({temperature:.1f} C) requires close observation."
            factors.append(f"Warm weather ({temperature:.1f} C) may deplete moisture quickly.")

        else:
            priority = "LOW"
            reason = f"Soil moisture ({predicted_sm:.2f}%) is within satisfactory bounds for {crop_type}. Continue routine monitoring."

    # 4. Construct Structured Output Response
    output = {
        "recommendation": recommendation,
        "priority": priority,
        "predicted_soil_moisture": round(predicted_sm, 2),
        "current_soil_moisture": round(current_sm, 2),
        "reason": reason,
        "factors": factors,
        "prototype_notice": PROTOTYPE_NOTICE
    }

    return output

if __name__ == "__main__":
    # Quick standalone test
    sample_input = {
        "crop_type": "Tomato",
        "current_soil_moisture": 35.0,
        "predicted_soil_moisture": 38.0,
        "temperature": 32.0,
        "humidity": 55.0,
        "rainfall": 0.0
    }
    res = get_irrigation_recommendation(sample_input)
    print("Sample Recommendation Result:")
    import json
    print(json.dumps(res, indent=2))
