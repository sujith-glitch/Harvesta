"""
AI Service layer connecting Phase 3 Soil Moisture ML Model and Phase 4 Recommendation Engine.
"""

import os
import sys
import logging
import joblib
import pandas as pd

# Add workspace root to sys.path if not present so ml module imports work
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from ml.irrigation_recommendation import get_irrigation_recommendation

logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(WORKSPACE_ROOT, "ml", "models", "soil_moisture_model.joblib")
CROP_REF_PATH = os.path.join(WORKSPACE_ROOT, "data", "sample", "crop_reference_data.csv")

class AIService:
    _model = None

    @classmethod
    def get_model(cls):
        """Loads and caches the Phase 3 ML Model once."""
        if cls._model is None:
            if not os.path.exists(MODEL_PATH):
                logger.error("ML model file missing at expected path.")
                raise FileNotFoundError("Soil moisture ML model file is not available.")
            try:
                cls._model = joblib.load(MODEL_PATH)
                logger.info("Successfully loaded ML model into AIService.")
            except Exception as e:
                logger.error(f"Error loading ML model: {e}")
                raise RuntimeError("Failed to load soil moisture ML model.")
        return cls._model

    @classmethod
    def generate_irrigation_recommendation(cls, input_data: dict) -> dict:
        """
        Processes environmental and soil input, performs ML prediction,
        and generates explainable irrigation recommendation.
        """
        # Ensure model is loaded
        try:
            model = cls.get_model()
        except Exception as e:
            raise RuntimeError(f"Service error: {str(e)}")

        # Verify crop reference file availability check
        if not os.path.exists(CROP_REF_PATH):
            logger.warning("Crop reference data file is missing.")

        crop_type = input_data.get("crop_type")
        temperature = float(input_data.get("temperature"))
        humidity = float(input_data.get("humidity"))
        rainfall = float(input_data.get("rainfall"))
        current_sm = float(input_data.get("current_soil_moisture"))
        soil_ph = float(input_data.get("soil_ph"))
        soil_temp = float(input_data.get("soil_temperature"))

        # Build feature DataFrame for ML model prediction
        feature_df = pd.DataFrame([{
            "crop_type": crop_type,
            "temperature": temperature,
            "humidity": humidity,
            "rainfall": rainfall,
            "soil_ph": soil_ph,
            "soil_temperature": soil_temp
        }])

        # Generate soil moisture prediction
        try:
            pred_array = model.predict(feature_df)
            predicted_sm = float(pred_array[0])
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise RuntimeError("Model prediction failed due to internal calculation error.")

        # Prepare payload for irrigation recommendation engine
        rec_payload = {
            "crop_type": crop_type,
            "current_soil_moisture": current_sm,
            "predicted_soil_moisture": predicted_sm,
            "temperature": temperature,
            "humidity": humidity,
            "rainfall": rainfall
        }

        try:
            rec_result = get_irrigation_recommendation(rec_payload)
        except Exception as e:
            logger.error(f"Recommendation engine failed: {e}")
            raise RuntimeError("Irrigation recommendation engine encountered an error.")

        # Construct final standardized API response
        return {
            "crop_type": crop_type,
            "input": {
                "temperature": temperature,
                "humidity": humidity,
                "rainfall": rainfall,
                "current_soil_moisture": current_sm,
                "soil_ph": soil_ph,
                "soil_temperature": soil_temp
            },
            "prediction": {
                "soil_moisture": round(predicted_sm, 2)
            },
            "recommendation": {
                "status": rec_result.get("recommendation", "MONITOR"),
                "priority": rec_result.get("priority", "MEDIUM"),
                "reason": rec_result.get("reason", ""),
                "factors": rec_result.get("factors", [])
            },
            "prototype_notice": "This prediction and recommendation are based on development/synthetic data and are not professional agronomic advice."
        }
