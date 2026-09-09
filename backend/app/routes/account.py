"""Farmer profile and application preference endpoints."""

from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import AppPreference, FarmerProfile, User
from backend.app.services.analytics_service import AnalyticsService
from backend.app.services.auth_service import get_current_user


router = APIRouter(prefix="/api/account", tags=["Farmer Account"])


class ProfileUpdate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    phone: Optional[str] = Field(None, max_length=30)
    address: Optional[str] = Field(None, max_length=500)
    district: Optional[str] = Field(None, max_length=150)
    state: Optional[str] = Field(None, max_length=150)
    country: Optional[str] = Field(None, max_length=150)
    bio: Optional[str] = Field(None, max_length=1000)
    primary_crop: Optional[str] = Field(None, max_length=150)
    experience_years: Optional[int] = Field(None, ge=0, le=100)
    avatar_color: str = Field("#A6BC12", pattern=r"^#[0-9A-Fa-f]{6}$")

    @field_validator("phone", "address", "district", "state", "country", "bio", "primary_crop")
    @classmethod
    def clean_optional_text(cls, value):
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class PreferenceUpdate(BaseModel):
    language: Optional[Literal["en", "ta", "hi", "te", "kn", "ml"]] = None
    theme: Optional[Literal["light", "dark", "system"]] = None
    compact_mode: Optional[bool] = None
    reduce_motion: Optional[bool] = None
    voice_enabled: Optional[bool] = None
    voice_auto_speak: Optional[bool] = None


def _profile_payload(user: User, profile: Optional[FarmerProfile]):
    details = profile.to_dict() if profile else {
        "phone": None,
        "address": None,
        "district": None,
        "state": None,
        "country": None,
        "bio": None,
        "primary_crop": None,
        "experience_years": None,
        "avatar_color": "#A6BC12",
        "updated_at": None,
    }
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": getattr(user, "role", "farmer"),
        "is_verified": user.is_verified,
        "member_since": user.created_at.isoformat() if isinstance(user.created_at, datetime) else str(user.created_at),
        **details,
    }


@router.get("/profile", status_code=status.HTTP_200_OK)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(FarmerProfile).filter(FarmerProfile.user_id == current_user.id).first()
    return _profile_payload(current_user, profile)


@router.put("/profile", status_code=status.HTTP_200_OK)
def update_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(FarmerProfile).filter(FarmerProfile.user_id == current_user.id).first()
    if profile is None:
        profile = FarmerProfile(user_id=current_user.id)
        db.add(profile)

    current_user.full_name = payload.full_name.strip()
    for field_name in (
        "phone", "address", "district", "state", "country", "bio",
        "primary_crop", "experience_years", "avatar_color",
    ):
        setattr(profile, field_name, getattr(payload, field_name))
    db.commit()
    db.refresh(profile)

    AnalyticsService.log_activity_event(
        db=db,
        event_name="profile_updated",
        user_id=current_user.id,
        feature="account",
    )
    return _profile_payload(current_user, profile)


@router.get("/preferences", status_code=status.HTTP_200_OK)
def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    preference = db.query(AppPreference).filter(AppPreference.user_id == current_user.id).first()
    if preference:
        return preference.to_dict()
    return {
        "language": "en",
        "theme": "light",
        "compact_mode": False,
        "reduce_motion": False,
        "voice_enabled": True,
        "voice_auto_speak": True,
        "updated_at": None,
    }


@router.put("/preferences", status_code=status.HTTP_200_OK)
def update_preferences(
    payload: PreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    preference = db.query(AppPreference).filter(AppPreference.user_id == current_user.id).first()
    if preference is None:
        preference = AppPreference(user_id=current_user.id)
        db.add(preference)

    updates = payload.model_dump(exclude_none=True)
    for field_name, value in updates.items():
        setattr(preference, field_name, value)
    db.commit()
    db.refresh(preference)

    AnalyticsService.log_activity_event(
        db=db,
        event_name="app_preferences_updated",
        user_id=current_user.id,
        feature="settings",
        metadata={"changed": sorted(updates.keys())},
    )
    return preference.to_dict()
