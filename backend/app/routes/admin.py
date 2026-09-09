"""
FastAPI Router for Admin & Company Analytics.
All endpoints require authenticated user with role='admin'.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import User
from backend.app.services.auth_service import require_admin_user
from backend.app.services.admin_analytics_service import AdminAnalyticsService
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/api/admin", tags=["Company Admin & Analytics"])


@router.get("/data-inventory", status_code=status.HTTP_200_OK, summary="List Stored Company Datasets")
def get_data_inventory(
    current_admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
):
    return AdminAnalyticsService.get_data_inventory(db)


@router.get("/data/{dataset}", status_code=status.HTTP_200_OK, summary="Browse an Approved Stored Dataset")
def get_dataset_records(
    dataset: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
):
    try:
        result = AdminAnalyticsService.get_dataset_records(db, dataset, limit, offset)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    AuditService.log_audit_event(
        db=db,
        action="admin_dataset_viewed",
        entity_type="dataset",
        user_id=current_admin.id,
        status="SUCCESS",
        metadata={"dataset": dataset, "limit": limit, "offset": offset},
    )
    return result


@router.get(
    "/overview",
    status_code=status.HTTP_200_OK,
    summary="Get Platform-Wide Executive Analytics Overview"
)
def get_admin_overview(
    current_admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db)
):
    """
    Returns platform-wide KPIs, active user counts, feature usage breakdown, and engagement metrics.
    Requires role='admin'.
    """
    return AdminAnalyticsService.get_overview_metrics(db)


@router.get(
    "/users",
    status_code=status.HTTP_200_OK,
    summary="List Registered Users with Activity Context"
)
def list_admin_users(
    limit: int = Query(50, ge=1, le=100, description="Page limit (1-100)"),
    offset: int = Query(0, ge=0, description="Offset index"),
    search: Optional[str] = Query(None, description="Filter by name or email"),
    role: Optional[str] = Query(None, description="Filter by role ('farmer', 'admin')"),
    current_admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db)
):
    """
    Returns a paginated list of user accounts with activity stats.
    Passwords and token hashes are strictly excluded.
    Requires role='admin'.
    """
    return AdminAnalyticsService.get_users_list(
        db=db,
        limit=limit,
        offset=offset,
        search=search,
        role=role,
    )


@router.get(
    "/activity",
    status_code=status.HTTP_200_OK,
    summary="Query Paginated Activity Events"
)
def list_activity_events(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    feature: Optional[str] = Query(None, description="Filter by feature domain"),
    event_name: Optional[str] = Query(None, description="Filter by event name"),
    current_admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db)
):
    """
    Returns paginated platform activity event telemetry.
    Requires role='admin'.
    """
    return AdminAnalyticsService.get_activity_events(
        db=db,
        limit=limit,
        offset=offset,
        feature=feature,
        event_name=event_name,
    )


@router.get(
    "/audit-logs",
    status_code=status.HTTP_200_OK,
    summary="Query Paginated Security Audit Logs"
)
def list_audit_logs(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    action: Optional[str] = Query(None, description="Filter by action type"),
    current_admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db)
):
    """
    Returns paginated administrative and security audit events.
    Requires role='admin'.
    """
    return AdminAnalyticsService.get_audit_logs(
        db=db,
        limit=limit,
        offset=offset,
        action=action,
    )


@router.get(
    "/sessions",
    status_code=status.HTTP_200_OK,
    summary="Query Paginated User Session Telemetry"
)
def list_sessions(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    active_only: bool = Query(False, description="Filter to ongoing active sessions only"),
    current_admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db)
):
    """
    Returns paginated session telemetry records.
    Requires role='admin'.
    """
    return AdminAnalyticsService.get_sessions(
        db=db,
        limit=limit,
        offset=offset,
        active_only=active_only,
    )
