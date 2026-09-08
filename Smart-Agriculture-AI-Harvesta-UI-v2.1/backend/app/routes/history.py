"""
FastAPI Router for Farmer Field Analysis History Management.
Strictly enforces authenticated user ownership on all endpoints.
"""

import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import User, FieldAnalysisHistory
from backend.app.services.auth_service import get_current_user
from backend.app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/history", tags=["Field Analysis History"])

# --- Request & Response Models ---

class LocationInput(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_text: Optional[str] = None

class WeatherInput(BaseModel):
    temperature: float
    humidity: float
    precipitation: float
    wind_speed: float

class SoilInput(BaseModel):
    current_soil_moisture: float
    soil_ph: float
    soil_temperature: float

class AnalysisDetails(BaseModel):
    status: str
    priority: str
    reason: str
    factors: List[str]

class CreateHistoryRequest(BaseModel):
    crop_type: str = Field(..., description="Crop species name")
    location: Optional[LocationInput] = None
    weather: WeatherInput
    soil: SoilInput
    analysis: AnalysisDetails

class HistoryItemResponse(BaseModel):
    id: int
    user_id: int
    crop_type: str
    location: Optional[LocationInput] = None
    weather: WeatherInput
    soil: SoilInput
    analysis: AnalysisDetails
    created_at: str


@router.post(
    "/field-analysis",
    response_model=HistoryItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save Field Analysis Record"
)
def save_field_analysis(
    payload: CreateHistoryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Saves a field analysis result to DB for current_user.
    Strictly uses authenticated current_user.id.
    """
    factors_json = json.dumps(payload.analysis.factors)

    loc = payload.location or LocationInput()
    history_record = FieldAnalysisHistory(
        user_id=current_user.id,  # Server-side user binding
        crop_type=payload.crop_type,
        latitude=loc.latitude,
        longitude=loc.longitude,
        current_soil_moisture=payload.soil.current_soil_moisture,
        soil_ph=payload.soil.soil_ph,
        soil_temperature=payload.soil.soil_temperature,
        weather_temperature=payload.weather.temperature,
        weather_humidity=payload.weather.humidity,
        weather_precipitation=payload.weather.precipitation,
        weather_wind_speed=payload.weather.wind_speed,
        recommendation_status=payload.analysis.status,
        priority=payload.analysis.priority,
        reason=payload.analysis.reason,
        factors=factors_json,
        created_at=datetime.utcnow()
    )

    db.add(history_record)
    db.commit()
    db.refresh(history_record)

    return history_record.to_dict()


@router.get(
    "/field-analysis",
    response_model=List[HistoryItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Authenticated User's Analysis History"
)
def get_user_history(
    limit: int = Query(50, ge=1, le=100, description="Max items to return (1-100)"),
    offset: int = Query(0, ge=0, description="Offset index"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns only the authenticated user's field analysis history records,
    sorted newest first.
    """
    records = (
        db.query(FieldAnalysisHistory)
        .filter(FieldAnalysisHistory.user_id == current_user.id)
        .order_by(FieldAnalysisHistory.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [record.to_dict() for record in records]


@router.get(
    "/field-analysis/{analysis_id}",
    response_model=HistoryItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Single Field Analysis Record"
)
def get_analysis_by_id(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves single analysis record by ID.
    Enforces user ownership: returns HTTP 404 if record does not exist or belongs to another user.
    """
    record = (
        db.query(FieldAnalysisHistory)
        .filter(
            FieldAnalysisHistory.id == analysis_id,
            FieldAnalysisHistory.user_id == current_user.id
        )
        .first()
    )

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field analysis record not found."
        )

    return record.to_dict()


@router.delete(
    "/field-analysis/{analysis_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Single Field Analysis Record"
)
def delete_analysis_by_id(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deletes single analysis record owned by current_user.
    Returns HTTP 404 if record does not exist or belongs to another user.
    """
    record = (
        db.query(FieldAnalysisHistory)
        .filter(
            FieldAnalysisHistory.id == analysis_id,
            FieldAnalysisHistory.user_id == current_user.id
        )
        .first()
    )

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field analysis record not found."
        )

    crop_type = record.crop_type
    db.delete(record)
    db.commit()

    AnalyticsService.log_activity_event(
        db=db,
        event_name="history_record_deleted",
        user_id=current_user.id,
        feature="history",
        metadata={"record_id": analysis_id, "crop_type": crop_type},
    )

    return {
        "status": "deleted",
        "id": analysis_id,
        "message": "Field analysis record deleted successfully."
    }
