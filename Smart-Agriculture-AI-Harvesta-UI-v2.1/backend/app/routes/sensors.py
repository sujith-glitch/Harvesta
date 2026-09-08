"""Secure registration and ingestion API for future physical farm sensors."""

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Farm, SensorDevice, SensorReading, User
from backend.app.services.analytics_service import AnalyticsService
from backend.app.services.audit_service import AuditService
from backend.app.services.auth_service import get_current_user


router = APIRouter(prefix="/api/sensors", tags=["Farm Sensors & IoT"])


def _hash_device_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


class SensorDeviceCreate(BaseModel):
    farm_id: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=255)
    device_type: str = Field(default="esp32_gateway", min_length=2, max_length=100)
    firmware_version: Optional[str] = Field(default=None, max_length=100)


class SensorReadingIn(BaseModel):
    device_uid: str = Field(min_length=8, max_length=100)
    recorded_at: Optional[datetime] = None
    soil_moisture: Optional[float] = Field(default=None, ge=0, le=100)
    soil_temperature: Optional[float] = Field(default=None, ge=-50, le=100)
    air_temperature: Optional[float] = Field(default=None, ge=-50, le=100)
    air_humidity: Optional[float] = Field(default=None, ge=0, le=100)
    soil_ph: Optional[float] = Field(default=None, ge=0, le=14)
    nitrogen: Optional[float] = Field(default=None, ge=0)
    phosphorus: Optional[float] = Field(default=None, ge=0)
    potassium: Optional[float] = Field(default=None, ge=0)
    rainfall: Optional[float] = Field(default=None, ge=0)
    battery_level: Optional[float] = Field(default=None, ge=0, le=100)


@router.post("/devices", status_code=status.HTTP_201_CREATED, summary="Register a Farm Sensor Gateway")
def register_sensor_device(
    payload: SensorDeviceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farm = db.query(Farm).filter(Farm.id == payload.farm_id, Farm.user_id == current_user.id).first()
    if not farm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found.")

    raw_key = f"harvesta_device_{secrets.token_urlsafe(32)}"
    device = SensorDevice(
        user_id=current_user.id,
        farm_id=farm.id,
        device_uid=f"harvesta-{uuid.uuid4().hex[:16]}",
        name=payload.name.strip(),
        device_type=payload.device_type.strip(),
        firmware_version=payload.firmware_version.strip() if payload.firmware_version else None,
        status="registered",
        api_key_hash=_hash_device_key(raw_key),
    )
    db.add(device)
    db.commit()
    db.refresh(device)

    AnalyticsService.log_activity_event(
        db=db,
        event_name="sensor_device_registered",
        user_id=current_user.id,
        feature="sensors",
        metadata={"device_id": device.id, "farm_id": farm.id, "device_type": device.device_type},
    )
    AuditService.log_audit_event(
        db=db,
        action="sensor_device_registered",
        entity_type="sensor_device",
        user_id=current_user.id,
        entity_id=device.id,
        status="SUCCESS",
    )

    result = device.to_dict()
    result.update({
        "device_key": raw_key,
        "device_key_notice": "Save this key now. Only its secure hash is stored and the raw key will not be shown again.",
    })
    return result


@router.get("/devices", summary="List My Registered Sensor Gateways")
def list_sensor_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    devices = (
        db.query(SensorDevice)
        .filter(SensorDevice.user_id == current_user.id)
        .order_by(SensorDevice.created_at.desc())
        .all()
    )
    return {"devices": [device.to_dict() for device in devices], "total": len(devices)}


@router.post("/devices/{device_id}/rotate-key", summary="Rotate a Sensor Gateway Key")
def rotate_sensor_device_key(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    device = (
        db.query(SensorDevice)
        .filter(SensorDevice.id == device_id, SensorDevice.user_id == current_user.id)
        .first()
    )
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor device not found.")

    raw_key = f"harvesta_device_{secrets.token_urlsafe(32)}"
    device.api_key_hash = _hash_device_key(raw_key)
    device.updated_at = datetime.utcnow()
    db.commit()
    AuditService.log_audit_event(
        db=db,
        action="sensor_device_key_rotated",
        entity_type="sensor_device",
        user_id=current_user.id,
        entity_id=device.id,
        status="SUCCESS",
    )
    return {
        "device_id": device.id,
        "device_uid": device.device_uid,
        "device_key": raw_key,
        "device_key_notice": "Replace the old key on the device now; it is no longer valid.",
    }


@router.post("/ingest", status_code=status.HTTP_201_CREATED, summary="Ingest a Sensor Reading")
def ingest_sensor_reading(
    payload: SensorReadingIn,
    x_device_key: str = Header(..., alias="X-Device-Key"),
    db: Session = Depends(get_db),
):
    device = db.query(SensorDevice).filter(SensorDevice.device_uid == payload.device_uid).first()
    supplied_hash = _hash_device_key(x_device_key.strip())
    if not device or not hmac.compare_digest(device.api_key_hash, supplied_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid sensor device credentials.")
    if device.status == "disabled":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sensor device is disabled.")

    metric_names = {
        "soil_moisture", "soil_temperature", "air_temperature", "air_humidity", "soil_ph",
        "nitrogen", "phosphorus", "potassium", "rainfall", "battery_level",
    }
    metrics = {name: getattr(payload, name) for name in metric_names if getattr(payload, name) is not None}
    if not metrics:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one sensor metric is required.")

    now = datetime.utcnow()
    reading = SensorReading(
        device_id=device.id,
        user_id=device.user_id,
        farm_id=device.farm_id,
        recorded_at=payload.recorded_at or now,
        raw_payload=metrics,
        source="device",
        **metrics,
    )
    device.last_seen_at = now
    device.status = "online"
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return {"status": "accepted", "reading": reading.to_dict()}


@router.get("/readings", summary="Read My Farm Sensor History")
def list_sensor_readings(
    farm_id: Optional[int] = Query(default=None, gt=0),
    device_id: Optional[int] = Query(default=None, gt=0),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(SensorReading).filter(SensorReading.user_id == current_user.id)
    if farm_id is not None:
        query = query.filter(SensorReading.farm_id == farm_id)
    if device_id is not None:
        query = query.filter(SensorReading.device_id == device_id)
    total = query.count()
    readings = query.order_by(SensorReading.recorded_at.desc()).offset(offset).limit(limit).all()
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "readings": [reading.to_dict() for reading in readings],
    }
