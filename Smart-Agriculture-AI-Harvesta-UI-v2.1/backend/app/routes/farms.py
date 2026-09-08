"""
FastAPI Router for Farm and Crop Management.

All queries are strictly scoped to the authenticated user:
- 401 when unauthenticated (via get_current_user dependency).
- 404 when the resource does not exist.
- 403 when the resource exists but belongs to another user.
"""

from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import User, Farm, Crop
from backend.app.services.auth_service import get_current_user
from backend.app.services.analytics_service import AnalyticsService
from backend.app.services.audit_service import AuditService

router = APIRouter(tags=["Farm Management"])

GROWTH_STAGES = {"Seedling", "Vegetative", "Flowering", "Fruiting", "Maturity", "Harvested"}
HEALTH_STATUSES = {"Healthy", "Needs Attention", "Critical"}


# --- Schemas ---

class FarmCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Farm name")
    location: Optional[str] = Field(None, max_length=255, description="Village / town / area")
    district: Optional[str] = Field(None, max_length=255)
    state: Optional[str] = Field(None, max_length=255)
    country: Optional[str] = Field(None, max_length=255)
    size: Optional[float] = Field(None, gt=0, description="Farm size in acres")
    soil_type: Optional[str] = Field(None, max_length=100)
    farming_method: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=2000)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Farm name must be a non-empty string.")
        return v


class FarmUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    district: Optional[str] = Field(None, max_length=255)
    state: Optional[str] = Field(None, max_length=255)
    country: Optional[str] = Field(None, max_length=255)
    size: Optional[float] = Field(None, gt=0)
    soil_type: Optional[str] = Field(None, max_length=100)
    farming_method: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=2000)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Farm name must be a non-empty string.")
        return v


class CropCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Crop name")
    variety: Optional[str] = Field(None, max_length=255)
    planting_date: Optional[date] = None
    expected_harvest_date: Optional[date] = None
    growth_stage: Optional[str] = Field(None, max_length=100)
    health_status: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=2000)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Crop name must be a non-empty string.")
        return v

    @field_validator("growth_stage")
    @classmethod
    def validate_growth_stage(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return None
        normalized = v.strip().title()
        for stage in GROWTH_STAGES:
            if stage.lower() == normalized.lower():
                return stage
        allowed_str = ", ".join(sorted(GROWTH_STAGES))
        raise ValueError(f"Unsupported growth_stage '{v}'. Allowed values: {allowed_str}")

    @field_validator("health_status")
    @classmethod
    def validate_health_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return None
        normalized = v.strip().title()
        for status_value in HEALTH_STATUSES:
            if status_value.lower() == normalized.lower():
                return status_value
        allowed_str = ", ".join(HEALTH_STATUSES)
        raise ValueError(f"Unsupported health_status '{v}'. Allowed values: {allowed_str}")


class CropUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    variety: Optional[str] = Field(None, max_length=255)
    planting_date: Optional[date] = None
    expected_harvest_date: Optional[date] = None
    growth_stage: Optional[str] = Field(None, max_length=100)
    health_status: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=2000)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Crop name must be a non-empty string.")
        return v

    @field_validator("growth_stage")
    @classmethod
    def validate_growth_stage(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return None
        normalized = v.strip().title()
        for stage in GROWTH_STAGES:
            if stage.lower() == normalized.lower():
                return stage
        allowed_str = ", ".join(sorted(GROWTH_STAGES))
        raise ValueError(f"Unsupported growth_stage '{v}'. Allowed values: {allowed_str}")

    @field_validator("health_status")
    @classmethod
    def validate_health_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return None
        normalized = v.strip().title()
        for status_value in HEALTH_STATUSES:
            if status_value.lower() == normalized.lower():
                return status_value
        allowed_str = ", ".join(HEALTH_STATUSES)
        raise ValueError(f"Unsupported health_status '{v}'. Allowed values: {allowed_str}")


# --- Serializers ---

def serialize_farm(farm: Farm) -> dict:
    return {
        "id": farm.id,
        "user_id": farm.user_id,
        "name": farm.name,
        "location": farm.location,
        "district": farm.district,
        "state": farm.state,
        "country": farm.country,
        "size": farm.size,
        "soil_type": farm.soil_type,
        "farming_method": farm.farming_method,
        "description": farm.description,
        "crop_count": len(farm.crops) if farm.crops else 0,
        "created_at": farm.created_at.isoformat() if isinstance(farm.created_at, datetime) else str(farm.created_at),
        "updated_at": farm.updated_at.isoformat() if isinstance(farm.updated_at, datetime) else str(farm.updated_at),
    }


def serialize_crop(crop: Crop) -> dict:
    return {
        "id": crop.id,
        "farm_id": crop.farm_id,
        "name": crop.name,
        "variety": crop.variety,
        "planting_date": crop.planting_date.date().isoformat() if isinstance(crop.planting_date, datetime) else (crop.planting_date.isoformat() if isinstance(crop.planting_date, date) else None),
        "expected_harvest_date": crop.expected_harvest_date.date().isoformat() if isinstance(crop.expected_harvest_date, datetime) else (crop.expected_harvest_date.isoformat() if isinstance(crop.expected_harvest_date, date) else None),
        "growth_stage": crop.growth_stage,
        "health_status": crop.health_status,
        "notes": crop.notes,
        "created_at": crop.created_at.isoformat() if isinstance(crop.created_at, datetime) else str(crop.created_at),
        "updated_at": crop.updated_at.isoformat() if isinstance(crop.updated_at, datetime) else str(crop.updated_at),
    }


def _date_to_datetime(d: Optional[date]) -> Optional[datetime]:
    return datetime(d.year, d.month, d.day) if d is not None else None


# --- Ownership helpers ---

def _get_owned_farm_or_error(farm_id: int, current_user: User, db: Session) -> Farm:
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found."
        )
    if farm.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this farm."
        )
    return farm


def _get_owned_crop_or_error(crop_id: int, current_user: User, db: Session) -> Crop:
    crop = (
        db.query(Crop)
        .join(Farm, Crop.farm_id == Farm.id)
        .filter(Crop.id == crop_id)
        .first()
    )
    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop not found."
        )
    if crop.farm.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this crop."
        )
    return crop


# --- Farm Endpoints ---

@router.post(
    "/api/farms",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Farm for the authenticated user"
)
def create_farm(
    payload: FarmCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    farm = Farm(
        user_id=current_user.id,
        name=payload.name,
        location=payload.location,
        district=payload.district,
        state=payload.state,
        country=payload.country,
        size=payload.size,
        soil_type=payload.soil_type,
        farming_method=payload.farming_method,
        description=payload.description,
    )
    db.add(farm)
    db.commit()
    db.refresh(farm)

    AnalyticsService.log_activity_event(
        db=db,
        event_name="farm_created",
        user_id=current_user.id,
        feature="farms",
        metadata={"farm_id": farm.id, "farm_name": farm.name, "size": farm.size},
    )

    return serialize_farm(farm)


@router.get(
    "/api/farms",
    status_code=status.HTTP_200_OK,
    summary="List all Farms owned by the authenticated user"
)
def list_farms(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    farms = (
        db.query(Farm)
        .filter(Farm.user_id == current_user.id)
        .order_by(Farm.created_at.asc())
        .all()
    )
    return [serialize_farm(farm) for farm in farms]


@router.get(
    "/api/farms/{farm_id}",
    status_code=status.HTTP_200_OK,
    summary="Get a single Farm owned by the authenticated user"
)
def get_farm(
    farm_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    farm = _get_owned_farm_or_error(farm_id, current_user, db)
    return serialize_farm(farm)


@router.put(
    "/api/farms/{farm_id}",
    status_code=status.HTTP_200_OK,
    summary="Update a Farm owned by the authenticated user"
)
def update_farm(
    farm_id: int,
    payload: FarmUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    farm = _get_owned_farm_or_error(farm_id, current_user, db)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(farm, field, value)

    farm.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(farm)
    return serialize_farm(farm)


@router.delete(
    "/api/farms/{farm_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a Farm owned by the authenticated user (cascades its crops)"
)
def delete_farm(
    farm_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    farm = _get_owned_farm_or_error(farm_id, current_user, db)
    farm_name = farm.name
    db.delete(farm)
    db.commit()

    AnalyticsService.log_activity_event(
        db=db,
        event_name="farm_deleted",
        user_id=current_user.id,
        feature="farms",
        metadata={"farm_id": farm_id, "farm_name": farm_name},
    )
    AuditService.log_audit_event(
        db=db,
        action="farm_deleted",
        entity_type="farm",
        user_id=current_user.id,
        entity_id=farm_id,
        status="SUCCESS",
        metadata={"farm_name": farm_name},
    )

    return {
        "status": "deleted",
        "id": farm_id,
        "message": "Farm deleted successfully."
    }


# --- Crop Endpoints (nested under farms) ---

@router.post(
    "/api/farms/{farm_id}/crops",
    status_code=status.HTTP_201_CREATED,
    summary="Add a Crop to a Farm owned by the authenticated user"
)
def create_crop(
    farm_id: int,
    payload: CropCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    farm = _get_owned_farm_or_error(farm_id, current_user, db)

    crop = Crop(
        farm_id=farm.id,
        name=payload.name,
        variety=payload.variety,
        planting_date=_date_to_datetime(payload.planting_date),
        expected_harvest_date=_date_to_datetime(payload.expected_harvest_date),
        growth_stage=payload.growth_stage,
        health_status=payload.health_status,
        notes=payload.notes,
    )
    db.add(crop)
    db.commit()
    db.refresh(crop)

    AnalyticsService.log_activity_event(
        db=db,
        event_name="crop_created",
        user_id=current_user.id,
        feature="crops",
        metadata={"crop_id": crop.id, "crop_name": crop.name, "farm_id": farm_id},
    )

    return serialize_crop(crop)


@router.get(
    "/api/farms/{farm_id}/crops",
    status_code=status.HTTP_200_OK,
    summary="List all Crops in a Farm owned by the authenticated user"
)
def list_crops(
    farm_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    farm = _get_owned_farm_or_error(farm_id, current_user, db)
    crops = (
        db.query(Crop)
        .filter(Crop.farm_id == farm.id)
        .order_by(Crop.created_at.desc())
        .all()
    )
    return [serialize_crop(crop) for crop in crops]


@router.get(
    "/api/crops/{crop_id}",
    status_code=status.HTTP_200_OK,
    summary="Get a single Crop owned by the authenticated user"
)
def get_crop(
    crop_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    crop = _get_owned_crop_or_error(crop_id, current_user, db)
    return serialize_crop(crop)


@router.put(
    "/api/crops/{crop_id}",
    status_code=status.HTTP_200_OK,
    summary="Update a Crop owned by the authenticated user"
)
def update_crop(
    crop_id: int,
    payload: CropUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    crop = _get_owned_crop_or_error(crop_id, current_user, db)

    update_data = payload.model_dump(exclude_unset=True)
    if "planting_date" in update_data:
        update_data["planting_date"] = _date_to_datetime(update_data["planting_date"])
    if "expected_harvest_date" in update_data:
        update_data["expected_harvest_date"] = _date_to_datetime(update_data["expected_harvest_date"])

    for field, value in update_data.items():
        setattr(crop, field, value)

    crop.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(crop)
    return serialize_crop(crop)


@router.delete(
    "/api/crops/{crop_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a Crop owned by the authenticated user"
)
def delete_crop(
    crop_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    crop = _get_owned_crop_or_error(crop_id, current_user, db)
    db.delete(crop)
    db.commit()
    return {
        "status": "deleted",
        "id": crop_id,
        "message": "Crop deleted successfully."
    }
