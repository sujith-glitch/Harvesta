"""
FastAPI Router for Farmer Dashboard Summary Metrics.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.database import get_db
from backend.app.models import User, FieldAnalysisHistory, Farm, Crop
from backend.app.services.auth_service import get_current_user
from backend.app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/dashboard", tags=["Farmer Dashboard"])

class DashboardSummaryResponse(BaseModel):
    total_analyses: int
    irrigation_required_count: int
    monitor_count: int
    no_irrigation_needed_count: int
    high_priority_count: int
    latest_analysis_timestamp: Optional[str] = None


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Authenticated User's Dashboard Summary Statistics"
)
def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Computes summary metrics for the authenticated farmer:
    - total analyses
    - irrigation required count
    - monitor count
    - no irrigation needed count
    - high priority count
    - latest analysis timestamp
    """
    user_records = db.query(FieldAnalysisHistory).filter(FieldAnalysisHistory.user_id == current_user.id)

    total_analyses = user_records.count()

    irrigation_required_count = user_records.filter(
        func.upper(FieldAnalysisHistory.recommendation_status) == "IRRIGATION_REQUIRED"
    ).count()

    monitor_count = user_records.filter(
        func.upper(FieldAnalysisHistory.recommendation_status) == "MONITOR"
    ).count()

    no_irrigation_needed_count = user_records.filter(
        func.upper(FieldAnalysisHistory.recommendation_status) == "NO_IRRIGATION_NEEDED"
    ).count()

    high_priority_count = user_records.filter(
        func.upper(FieldAnalysisHistory.priority) == "HIGH"
    ).count()

    latest_record = user_records.order_by(FieldAnalysisHistory.created_at.desc()).first()
    latest_timestamp = latest_record.created_at.isoformat() if latest_record else None

    return {
        "total_analyses": total_analyses,
        "irrigation_required_count": irrigation_required_count,
        "monitor_count": monitor_count,
        "no_irrigation_needed_count": no_irrigation_needed_count,
        "high_priority_count": high_priority_count,
        "latest_analysis_timestamp": latest_timestamp
    }


# --- Phase 2: Farm/Crop home overview ---

HEALTH_WEIGHTS = {
    "healthy": 100.0,
    "needs attention": 55.0,
    "critical": 15.0,
}


def _serialize_crop_brief(crop: Crop) -> Dict[str, Any]:
    return {
        "id": crop.id,
        "farm_id": crop.farm_id,
        "name": crop.name,
        "variety": crop.variety,
        "growth_stage": crop.growth_stage,
        "health_status": crop.health_status or "Healthy",
        "planting_date": crop.planting_date.date().isoformat() if crop.planting_date else None,
        "expected_harvest_date": crop.expected_harvest_date.date().isoformat() if crop.expected_harvest_date else None,
    }


def _serialize_analysis_brief(record: FieldAnalysisHistory) -> Dict[str, Any]:
    return {
        "id": record.id,
        "crop_type": record.crop_type,
        "status": record.recommendation_status,
        "priority": record.priority,
        "created_at": record.created_at.isoformat() if hasattr(record.created_at, "isoformat") else str(record.created_at),
    }


@router.get(
    "/home",
    status_code=status.HTTP_200_OK,
    summary="Get Authenticated User's Home Overview (farm, crops, upcoming harvests, recent analyses)"
)
def get_dashboard_home(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Aggregated home-screen payload for the authenticated farmer:
    - primary farm summary
    - crop summary (count + overall health percentage)
    - recent crop activity
    - upcoming harvests (soonest expected harvest dates)
    - recent field analyses
    """
    farm = (
        db.query(Farm)
        .filter(Farm.user_id == current_user.id)
        .order_by(Farm.created_at.asc())
        .first()
    )

    crops: List[Crop] = []
    if farm:
        crops = (
            db.query(Crop)
            .filter(Crop.farm_id == farm.id)
            .order_by(Crop.created_at.desc())
            .all()
        )

    total_crops = len(crops)

    # Overall health % from simple health-status weighting.
    overall_health_percent = None
    scored: List[float] = []
    for c in crops:
        weight = HEALTH_WEIGHTS.get((c.health_status or "").strip().lower())
        if weight is not None:
            scored.append(weight)
    if scored:
        overall_health_percent = round(sum(scored) / len(scored))

    # Upcoming harvests: soonest expected harvest dates first.
    with_harvest = [c for c in crops if c.expected_harvest_date is not None]
    upcoming = sorted(with_harvest, key=lambda c: c.expected_harvest_date)[:3]

    # Recent field analyses for this user.
    recent_records = (
        db.query(FieldAnalysisHistory)
        .filter(FieldAnalysisHistory.user_id == current_user.id)
        .order_by(FieldAnalysisHistory.created_at.desc())
        .limit(3)
        .all()
    )

    farm_payload = None
    if farm:
        farm_payload = {
            "id": farm.id,
            "name": farm.name,
            "location": farm.location,
            "district": farm.district,
            "state": farm.state,
            "size": farm.size,
            "soil_type": farm.soil_type,
            "farming_method": farm.farming_method,
        }

    AnalyticsService.log_activity_event(
        db=db,
        event_name="dashboard_view",
        user_id=current_user.id,
        feature="dashboard",
    )

    return {
        "farm": farm_payload,
        "total_crops": total_crops,
        "overall_health_percent": overall_health_percent,
        "recent_crops": [_serialize_crop_brief(c) for c in crops[:5]],
        "upcoming_harvests": [_serialize_crop_brief(c) for c in upcoming],
        "recent_analyses": [_serialize_analysis_brief(r) for r in recent_records],
    }
