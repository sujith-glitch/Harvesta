"""
FastAPI AI Route for Irrigation Recommendation & Weather-Integrated Field Analysis.
"""

import json
import logging
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from backend.app.database import get_db
from backend.app.models import User, FieldAnalysisHistory
from backend.app.services.ai_service import AIService
from backend.app.services.field_analysis_service import FieldAnalysisService
from backend.app.services.auth_service import get_current_user
from backend.app.services.analytics_service import AnalyticsService
from backend.app.services.notification_service import NotificationService

router = APIRouter(prefix="/api/ai", tags=["AI Recommendation Engine"])

SUPPORTED_CROPS = {"Rice", "Tomato", "Maize", "Cotton", "Wheat"}

class CropTypeEnum(str, Enum):
    RICE = "Rice"
    TOMATO = "Tomato"
    MAIZE = "Maize"
    COTTON = "Cotton"
    WHEAT = "Wheat"

# --- Phase 6 Irrigation Recommendation Models ---
class IrrigationRecommendationRequest(BaseModel):
    crop_type: str = Field(..., description="Crop type name. Supported crops: Rice, Tomato, Maize, Cotton, Wheat")
    temperature: float = Field(..., ge=-50.0, le=70.0, description="Ambient air temperature in Celsius")
    humidity: float = Field(..., ge=0.0, le=100.0, description="Relative humidity percentage (0-100)")
    rainfall: float = Field(..., ge=0.0, description="Precipitation in mm (must not be negative)")
    current_soil_moisture: float = Field(..., ge=0.0, le=100.0, description="Current soil moisture percentage (0-100)")
    soil_ph: float = Field(..., ge=0.0, le=14.0, description="Soil pH level (0-14)")
    soil_temperature: float = Field(..., ge=-50.0, le=70.0, description="Soil temperature in Celsius")

    @field_validator("crop_type")
    @classmethod
    def validate_crop_type(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("crop_type must be a non-empty string.")
        
        normalized = v.strip().title()
        for crop in SUPPORTED_CROPS:
            if crop.lower() == normalized.lower():
                return crop
        
        allowed_str = ", ".join(sorted(SUPPORTED_CROPS))
        raise ValueError(f"Unsupported crop_type '{v}'. Supported crops are: {allowed_str}")


class InputDataResponse(BaseModel):
    temperature: float
    humidity: float
    rainfall: float
    current_soil_moisture: float
    soil_ph: float
    soil_temperature: float

class PredictionResponse(BaseModel):
    soil_moisture: float

class RecommendationDetailsResponse(BaseModel):
    status: str
    priority: str
    reason: str
    factors: List[str]

class IrrigationRecommendationResponse(BaseModel):
    crop_type: str
    input: InputDataResponse
    prediction: PredictionResponse
    recommendation: RecommendationDetailsResponse
    prototype_notice: str


# --- Phase 8/10 Field Analysis Models ---
class FieldAnalysisRequest(BaseModel):
    crop_type: str = Field(..., description="Crop type name. Supported crops: Rice, Tomato, Maize, Cotton, Wheat")
    current_soil_moisture: float = Field(..., ge=0.0, le=100.0, description="Current soil moisture percentage (0-100)")
    soil_ph: float = Field(..., ge=0.0, le=14.0, description="Soil pH level (0-14)")
    soil_temperature: float = Field(..., ge=-50.0, le=70.0, description="Soil temperature in Celsius")
    location_text: Optional[str] = Field(None, description="Human-readable farm location (e.g., 'Coimbatore, Tamil Nadu')")

    @field_validator("crop_type")
    @classmethod
    def validate_crop_type(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("crop_type must be a non-empty string.")
        
        normalized = v.strip().title()
        for crop in SUPPORTED_CROPS:
            if crop.lower() == normalized.lower():
                return crop
        
        allowed_str = ", ".join(sorted(SUPPORTED_CROPS))
        raise ValueError(f"Unsupported crop_type '{v}'. Supported crops are: {allowed_str}")


class LocationResponse(BaseModel):
    location_text: Optional[str] = None

class WeatherResponse(BaseModel):
    temperature: float
    humidity: float
    precipitation: float
    wind_speed: float

class SoilResponse(BaseModel):
    current_soil_moisture: float
    soil_ph: float
    soil_temperature: float

class AnalysisResponse(BaseModel):
    status: str
    priority: str
    reason: str
    factors: List[str]

class FieldAnalysisResponse(BaseModel):
    history_id: Optional[int] = None
    location: LocationResponse
    weather: WeatherResponse
    soil: SoilResponse
    analysis: AnalysisResponse
    prototype_notice: str


# --- Endpoints ---

@router.post(
    "/irrigation-recommendation",
    response_model=IrrigationRecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Explainable Irrigation Recommendation",
    description="Accepts environmental & soil metrics, calculates ML soil moisture prediction, and returns actionable farmer recommendations."
)
def get_recommendation(request_data: IrrigationRecommendationRequest):
    try:
        payload = request_data.model_dump()
        result = AIService.generate_irrigation_recommendation(payload)
        return result
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the recommendation."
        )


@router.post(
    "/field-analysis",
    response_model=FieldAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Weather-Integrated Field Analysis (Authenticated & Persisted)",
    description="Fetches live real weather for specified coordinates, computes explainable analysis, and saves record to database for authenticated farmer."
)
def analyze_field(
    request_data: FieldAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        payload = request_data.model_dump()
        result = FieldAnalysisService.analyze_field(payload)

        # Automatically save field analysis result to DB history for current_user
        factors_json = json.dumps(result["analysis"]["factors"])
        history_record = FieldAnalysisHistory(
            user_id=current_user.id,
            crop_type=payload["crop_type"],
            latitude=None,  # No longer collected from farmer
            longitude=None,  # No longer collected from farmer
            current_soil_moisture=payload["current_soil_moisture"],
            soil_ph=payload["soil_ph"],
            soil_temperature=payload["soil_temperature"],
            weather_temperature=result["weather"]["temperature"],
            weather_humidity=result["weather"]["humidity"],
            weather_precipitation=result["weather"]["precipitation"],
            weather_wind_speed=result["weather"]["wind_speed"],
            recommendation_status=result["analysis"]["status"],
            priority=result["analysis"]["priority"],
            reason=result["analysis"]["reason"],
            factors=factors_json,
            created_at=datetime.utcnow()
        )

        db.add(history_record)
        db.commit()
        db.refresh(history_record)

        AnalyticsService.log_activity_event(
            db=db,
            event_name="field_analysis_run",
            user_id=current_user.id,
            feature="irrigation_ai",
            metadata={
                "crop_type": payload["crop_type"],
                "recommendation_status": result["analysis"]["status"],
                "priority": result["analysis"]["priority"],
            },
        )

        # Trigger irrigation alert if action is recommended or priority is elevated
        try:
            if result["analysis"]["status"] != "NO_IRRIGATION" or result["analysis"]["priority"] in ["MEDIUM", "HIGH"]:
                NotificationService.generate_irrigation_alert(
                    db=db,
                    user=current_user,
                    crop_type=payload["crop_type"],
                    recommendation_status=result["analysis"]["status"],
                    priority=result["analysis"]["priority"],
                    reason=result["analysis"]["reason"],
                )
            
            # Evaluate weather metrics for potential advisory alerts
            NotificationService.generate_weather_advisory(
                db=db,
                user=current_user,
                weather_data=result.get("weather", {}),
            )
        except Exception as alert_err:
            logger.warning(f"Non-blocking notification trigger error: {alert_err}")

        result["history_id"] = history_record.id
        return result

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected field analysis error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected internal error occurred during field analysis. Please try again later."
        )
