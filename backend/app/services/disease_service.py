"""
Crop Disease Vision AI Service.
Handles singleton model loading, image feature extraction, inference execution,
and structured agronomic recommendation formatting.
"""

import json
import os
import sys
import logging
from typing import Dict, Any, List, Optional
from PIL import Image
import numpy as np
import joblib

logger = logging.getLogger(__name__)

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from ml.disease.prepare_dataset import extract_image_features

MODEL_PATH = os.path.join(WORKSPACE_ROOT, "ml", "models", "crop_disease_model.joblib")
METADATA_PATH = os.path.join(WORKSPACE_ROOT, "ml", "disease", "disease_metadata.json")


class DiseaseService:
    _model = None
    _metadata = None
    _classes = None

    @classmethod
    def initialize(cls):
        """
        Loads model and metadata into memory (singleton).
        """
        if cls._model is None:
            if not os.path.exists(MODEL_PATH):
                raise RuntimeError(f"Crop disease vision model artifact not found at {MODEL_PATH}.")
            
            logger.info(f"Loading Crop Disease Vision model from {MODEL_PATH}...")
            cls._model = joblib.load(MODEL_PATH)

        if cls._metadata is None:
            if not os.path.exists(METADATA_PATH):
                raise RuntimeError(f"Crop disease metadata not found at {METADATA_PATH}.")
            
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                cls._metadata = json.load(f)
            cls._classes = cls._metadata["classes"]

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        if cls._metadata is None:
            cls.initialize()
        return cls._metadata

    @classmethod
    def predict_image(cls, image: Image.Image) -> Dict[str, Any]:
        """
        Executes vision inference on a PIL Image.
        Returns top prediction, confidence, recommendations, and candidate probabilities.
        """
        if cls._model is None:
            cls.initialize()

        # Extract normalized 1D spatial-color and texture feature vector
        features = extract_image_features(image)
        feature_matrix = np.expand_dims(features, axis=0)

        # Run inference
        probs = cls._model.predict_proba(feature_matrix)[0]
        top_idx = int(np.argmax(probs))
        top_class = cls._classes[top_idx]
        confidence = float(probs[top_idx])
        confidence_threshold = float(os.getenv("DISEASE_MIN_ACTION_CONFIDENCE", "0.65"))
        needs_review = confidence < confidence_threshold

        # Get candidate top 3 predictions
        top_indices = np.argsort(probs)[::-1][:3]
        top_predictions = [
            {
                "class_key": cls._classes[idx],
                "label": cls._metadata["disease_info"].get(cls._classes[idx], {}).get("display_name", cls._classes[idx]),
                "confidence": round(float(probs[idx]), 4),
            }
            for idx in top_indices
        ]

        info = cls._metadata["disease_info"].get(top_class, {
            "display_name": top_class.replace("___", " - "),
            "crop": top_class.split("___")[0],
            "disease": top_class.split("___")[1] if "___" in top_class else "Unknown",
            "is_healthy": "Healthy" in top_class,
            "urgency": "LOW" if "Healthy" in top_class else "MEDIUM",
            "description": "Visual screening prediction.",
            "recommendations": ["Consult local agricultural advisor."],
        })

        rec_text = " ".join(info.get("recommendations", []))

        recommendations = info.get("recommendations", [])
        description = info.get("description", "")
        if needs_review:
            description = (
                "The image does not match one supported prototype class with enough confidence. "
                "Retake a clear photo and request human review. " + description
            )
            recommendations = [
                "Retake the photo in daylight with one affected leaf filling most of the frame.",
                "Do not apply treatment based on this uncertain screening result.",
                "Ask a local agronomist or extension officer to inspect persistent or spreading symptoms.",
            ]

        return {
            "class_key": top_class,
            "display_name": info.get("display_name", top_class),
            "predicted_crop": info.get("crop", "Unknown"),
            "predicted_disease": info.get("disease", "Unknown"),
            "is_healthy": info.get("is_healthy", False),
            "urgency": "REVIEW" if needs_review else info.get("urgency", "LOW"),
            "confidence": round(confidence, 4),
            "confidence_threshold": confidence_threshold,
            "screening_status": "review_required" if needs_review else "candidate_match",
            "description": description,
            "recommendations": recommendations,
            "recommendation_summary": " ".join(recommendations),
            "top_predictions": top_predictions,
            "model_version": cls._metadata.get("model_version", "harvesta-disease-vision-v1.0"),
            "disclaimer": cls._metadata.get("disclaimer", ""),
        }
