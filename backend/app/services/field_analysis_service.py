"""
Field Analysis Service combining real weather data with farmer-provided soil data.
Implements explicit model safety compatibility layer for Phase 3 synthetic ML model vs Phase 4 explainable decision engine.
"""

import os
import sys
import logging
from typing import Dict, Any

# Ensure workspace root is in sys.path for ml imports
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from backend.app.services.weather_service import WeatherService
from ml.irrigation_recommendation import get_irrigation_recommendation

logger = logging.getLogger(__name__)

PROTOTYPE_NOTICE_FIELD_ANALYSIS = (
    "PROTOTYPE NOTICE: Real weather integration is active for rule-based decision support. "
    "The Phase 3 soil moisture model was trained on synthetic data; therefore, live real-weather feeds "
    "are processed through the validated explainable recommendation engine rather than direct synthetic ML model inference."
)

class FieldAnalysisService:
    @staticmethod
    def analyze_field(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combines live weather data with user-provided soil information
        and calculates explainable irrigation recommendations.
        Location is now a human-readable text field; lat/lon are internal only.
        """
        crop_type = str(payload.get("crop_type", "Tomato")).strip()
        location_text = payload.get("location_text") or "India"
        current_sm = float(payload.get("current_soil_moisture"))
        soil_ph = float(payload.get("soil_ph"))
        soil_temp = float(payload.get("soil_temperature"))

        # Internal default coordinates for weather (Salem, Tamil Nadu)
        # These are NOT exposed to the farmer UI
        internal_lat = float(payload.get("_internal_lat", 11.6643))
        internal_lon = float(payload.get("_internal_lon", 78.1460))

        # 1. Fetch Real Weather Data using internal coordinates
        weather_data = WeatherService.get_current_weather(internal_lat, internal_lon)
        
        temperature = weather_data["temperature"]
        humidity = weather_data["humidity"]
        precipitation = weather_data["precipitation"]
        wind_speed = weather_data["wind_speed"]

        # 2. Safety Compatibility Layer & Recommendation Generation
        # Note: Phase 3 ML model was trained on synthetic data. Real weather input has different characteristics.
        # Direct ML prediction is not validated on live weather feeds.
        # We pass real weather metrics + soil moisture into the Phase 4 explainable recommendation logic.
        rec_payload = {
            "crop_type": crop_type,
            "current_soil_moisture": current_sm,
            "predicted_soil_moisture": current_sm,  # Uses farmer current soil moisture as reference
            "temperature": temperature,
            "humidity": humidity,
            "rainfall": precipitation
        }

        try:
            rec_result = get_irrigation_recommendation(rec_payload)
        except Exception as e:
            logger.error(f"Error executing irrigation recommendation logic: {e}")
            raise RuntimeError("Failed to compute field analysis recommendation.")

        # Additional domain factor for wind speed if elevated
        factors = list(rec_result.get("factors", []))
        if wind_speed >= 20.0:
            factors.append(f"Elevated wind speed ({wind_speed:.1f} km/h) increases surface soil moisture evaporation rate.")

        status = rec_result.get("recommendation", "MONITOR")
        priority = rec_result.get("priority", "MEDIUM")
        reason = rec_result.get("reason", "")

        return {
            "location": {
                "location_text": location_text
            },
            "weather": {
                "temperature": temperature,
                "humidity": humidity,
                "precipitation": precipitation,
                "wind_speed": wind_speed
            },
            "soil": {
                "current_soil_moisture": current_sm,
                "soil_ph": soil_ph,
                "soil_temperature": soil_temp
            },
            "analysis": {
                "status": status,
                "priority": priority,
                "reason": reason,
                "factors": factors
            },
            "prototype_notice": PROTOTYPE_NOTICE_FIELD_ANALYSIS
        }
