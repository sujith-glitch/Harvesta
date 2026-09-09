import os
import sys

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_endpoint_still_returns_200():
    """Verify that GET /api/health returns HTTP 200 OK and expected body."""
    response = client.get("/api/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "ok"
    assert json_data["service"] == "Smart Agriculture AI Platform"


def test_valid_irrigation_recommendation_request():
    """Verify that POST /api/ai/irrigation-recommendation returns HTTP 200 with complete response structure."""
    payload = {
        "crop_type": "Tomato",
        "temperature": 32.0,
        "humidity": 60.0,
        "rainfall": 0.0,
        "current_soil_moisture": 35.0,
        "soil_ph": 6.5,
        "soil_temperature": 30.0
    }
    response = client.post("/api/ai/irrigation-recommendation", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    
    # Check top-level keys
    assert "crop_type" in data
    assert data["crop_type"] == "Tomato"
    assert "input" in data
    assert "prediction" in data
    assert "recommendation" in data
    assert "prototype_notice" in data
    
    # Check prediction numeric field
    assert "soil_moisture" in data["prediction"]
    assert isinstance(data["prediction"]["soil_moisture"], (int, float))
    
    # Check recommendation required fields
    rec = data["recommendation"]
    assert "status" in rec
    assert rec["status"] in ["IRRIGATION_REQUIRED", "MONITOR", "NO_IRRIGATION_NEEDED"]
    assert "priority" in rec
    assert rec["priority"] in ["HIGH", "MEDIUM", "LOW"]
    assert "reason" in rec
    assert isinstance(rec["reason"], str)
    assert "factors" in rec
    assert isinstance(rec["factors"], list)


def test_invalid_crop_type_validation():
    """Verify that an unsupported crop_type returns HTTP 422 validation error."""
    payload = {
        "crop_type": "Banana",
        "temperature": 32.0,
        "humidity": 60.0,
        "rainfall": 0.0,
        "current_soil_moisture": 35.0,
        "soil_ph": 6.5,
        "soil_temperature": 30.0
    }
    response = client.post("/api/ai/irrigation-recommendation", json=payload)
    assert response.status_code == 422


def test_negative_rainfall_validation():
    """Verify that negative rainfall returns HTTP 422 validation error."""
    payload = {
        "crop_type": "Tomato",
        "temperature": 32.0,
        "humidity": 60.0,
        "rainfall": -10.0,
        "current_soil_moisture": 35.0,
        "soil_ph": 6.5,
        "soil_temperature": 30.0
    }
    response = client.post("/api/ai/irrigation-recommendation", json=payload)
    assert response.status_code == 422


def test_invalid_humidity_validation():
    """Verify that humidity > 100 or < 0 returns HTTP 422 validation error."""
    payload_high = {
        "crop_type": "Tomato",
        "temperature": 32.0,
        "humidity": 150.0,
        "rainfall": 0.0,
        "current_soil_moisture": 35.0,
        "soil_ph": 6.5,
        "soil_temperature": 30.0
    }
    response_high = client.post("/api/ai/irrigation-recommendation", json=payload_high)
    assert response_high.status_code == 422

    payload_low = {
        "crop_type": "Tomato",
        "temperature": 32.0,
        "humidity": -5.0,
        "rainfall": 0.0,
        "current_soil_moisture": 35.0,
        "soil_ph": 6.5,
        "soil_temperature": 30.0
    }
    response_low = client.post("/api/ai/irrigation-recommendation", json=payload_low)
    assert response_low.status_code == 422
