"""Security and ownership tests for the future physical sensor API."""

import uuid

from fastapi.testclient import TestClient

from backend.app.database import SessionLocal
from backend.app.main import app
from backend.app.models import Farm, SensorDevice, SensorReading, User
from backend.app.services.auth_service import AuthService


client = TestClient(app)


def create_farmer_with_farm(prefix: str):
    db = SessionLocal()
    try:
        user = User(
            email=f"{prefix}_{uuid.uuid4().hex[:8]}@example.com",
            full_name="Sensor Farmer",
            hashed_password=AuthService.hash_password("password123"),
            role="farmer",
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        farm = Farm(user_id=user.id, name=f"{prefix} Farm")
        db.add(farm)
        db.commit()
        db.refresh(farm)
        headers = {"Authorization": f"Bearer {AuthService.create_access_token(user.id, user.email)}"}
        return user.id, farm.id, headers
    finally:
        db.close()


def test_sensor_endpoints_require_farmer_authentication():
    assert client.get("/api/sensors/devices").status_code == 401
    assert client.get("/api/sensors/readings").status_code == 401
    assert client.post("/api/sensors/devices", json={"farm_id": 1, "name": "Gateway"}).status_code == 401


def test_sensor_registration_ingestion_and_history_are_owner_scoped():
    owner_id, owner_farm_id, owner_headers = create_farmer_with_farm("sensor_owner")
    _, other_farm_id, other_headers = create_farmer_with_farm("sensor_other")

    cross_farm = client.post(
        "/api/sensors/devices",
        json={"farm_id": other_farm_id, "name": "Wrong Farm Gateway"},
        headers=owner_headers,
    )
    assert cross_farm.status_code == 404

    registered = client.post(
        "/api/sensors/devices",
        json={"farm_id": owner_farm_id, "name": "Field ESP32", "firmware_version": "1.0.0"},
        headers=owner_headers,
    )
    assert registered.status_code == 201
    device = registered.json()
    assert device["device_key"].startswith("harvesta_device_")
    assert device["device_uid"].startswith("harvesta-")
    raw_key = device["device_key"]

    db = SessionLocal()
    try:
        stored = db.query(SensorDevice).filter(SensorDevice.id == device["id"]).first()
        assert stored.user_id == owner_id
        assert stored.api_key_hash != raw_key
        assert len(stored.api_key_hash) == 64
    finally:
        db.close()

    listed = client.get("/api/sensors/devices", headers=owner_headers).json()["devices"]
    assert any(item["id"] == device["id"] for item in listed)
    assert all("device_key" not in item and "api_key_hash" not in item for item in listed)
    assert client.get("/api/sensors/devices", headers=other_headers).json()["total"] == 0

    payload = {
        "device_uid": device["device_uid"],
        "soil_moisture": 42.5,
        "soil_temperature": 27.1,
        "air_temperature": 31.2,
        "air_humidity": 64.0,
        "soil_ph": 6.7,
        "nitrogen": 82.0,
        "phosphorus": 38.0,
        "potassium": 55.0,
        "battery_level": 91.0,
    }
    assert client.post("/api/sensors/ingest", json=payload, headers={"X-Device-Key": "wrong"}).status_code == 401
    accepted = client.post("/api/sensors/ingest", json=payload, headers={"X-Device-Key": raw_key})
    assert accepted.status_code == 201
    assert accepted.json()["reading"]["soil_moisture"] == 42.5

    history = client.get("/api/sensors/readings", headers=owner_headers)
    assert history.status_code == 200
    assert history.json()["total"] == 1
    assert history.json()["readings"][0]["farm_id"] == owner_farm_id
    assert client.get("/api/sensors/readings", headers=other_headers).json()["total"] == 0

    db = SessionLocal()
    try:
        assert db.query(SensorReading).filter(SensorReading.user_id == owner_id).count() == 1
    finally:
        db.close()


def test_rotated_sensor_key_invalidates_previous_key():
    _, farm_id, headers = create_farmer_with_farm("sensor_rotate")
    device = client.post(
        "/api/sensors/devices",
        json={"farm_id": farm_id, "name": "Rotating Gateway"},
        headers=headers,
    ).json()
    old_key = device["device_key"]
    rotated = client.post(f"/api/sensors/devices/{device['id']}/rotate-key", headers=headers)
    assert rotated.status_code == 200
    new_key = rotated.json()["device_key"]
    assert new_key != old_key

    payload = {"device_uid": device["device_uid"], "soil_moisture": 50.0}
    assert client.post("/api/sensors/ingest", json=payload, headers={"X-Device-Key": old_key}).status_code == 401
    assert client.post("/api/sensors/ingest", json=payload, headers={"X-Device-Key": new_key}).status_code == 201
