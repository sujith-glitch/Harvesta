"""
FastAPI Router for Farmer Notification Center & Preferences.
Enforces strict authenticated user ownership across all notification endpoints.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import User
from backend.app.services.auth_service import get_current_user
from backend.app.services.notification_service import NotificationService

router = APIRouter(prefix="/api/notifications", tags=["Notifications & Alerts"])


class UpdatePreferencesRequest(BaseModel):
    email_enabled: Optional[bool] = None
    irrigation_alerts: Optional[bool] = None
    disease_alerts: Optional[bool] = None
    security_alerts: Optional[bool] = None
    weather_alerts: Optional[bool] = None


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Get Authenticated User's Notifications"
)
def get_notifications(
    limit: int = Query(50, ge=1, le=100, description="Page limit"),
    offset: int = Query(0, ge=0, description="Offset index"),
    unread_only: bool = Query(False, description="Filter to unread notifications only"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns paginated notifications belonging exclusively to the authenticated user.
    """
    return NotificationService.get_paginated_notifications(
        db=db,
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/unread-count",
    status_code=status.HTTP_200_OK,
    summary="Get Unread Notification Count"
)
def get_unread_notification_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the total unread notification count for the authenticated farmer.
    """
    count = NotificationService.get_unread_count(db=db, user_id=current_user.id)
    return {"unread_count": count}


@router.patch(
    "/{notification_id}/read",
    status_code=status.HTTP_200_OK,
    summary="Mark Single Notification As Read"
)
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Marks a single notification as read. Returns 404 if notification doesn't exist or is owned by another user.
    """
    notification = NotificationService.mark_as_read(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id,
    )
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        )
    return notification.to_dict()


@router.post(
    "/mark-all-read",
    status_code=status.HTTP_200_OK,
    summary="Mark All Notifications As Read"
)
def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Marks all unread notifications belonging to the authenticated user as read.
    """
    updated_count = NotificationService.mark_all_as_read(db=db, user_id=current_user.id)
    return {
        "status": "success",
        "updated_count": updated_count,
        "message": f"Marked {updated_count} notifications as read.",
    }


@router.get(
    "/preferences",
    status_code=status.HTTP_200_OK,
    summary="Get Notification Preferences"
)
def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the authenticated user's notification preferences, initializing defaults if missing.
    """
    pref = NotificationService.get_or_create_preferences(db=db, user_id=current_user.id)
    return pref.to_dict()


@router.put(
    "/preferences",
    status_code=status.HTTP_200_OK,
    summary="Update Notification Preferences"
)
def update_preferences(
    payload: UpdatePreferencesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Updates the authenticated farmer's notification preference flags.
    """
    pref = NotificationService.update_preferences(
        db=db,
        user_id=current_user.id,
        email_enabled=payload.email_enabled,
        irrigation_alerts=payload.irrigation_alerts,
        disease_alerts=payload.disease_alerts,
        security_alerts=payload.security_alerts,
        weather_alerts=payload.weather_alerts,
    )
    return pref.to_dict()
