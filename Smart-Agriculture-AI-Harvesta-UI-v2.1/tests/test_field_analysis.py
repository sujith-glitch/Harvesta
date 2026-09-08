import os
import sys
import json
import uuid
from unittest.mock import patch, MagicMock

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.weather_service import WeatherService
from backend.app.services.email_service import EmailService
from backend.app.services.field_analysis_service import FieldAnalysisService

client = TestClient(app)

MOCK_OPEN_METEO_RESPONSE = {
    "current": {
        "temperature_2m": 31.5,
        "relative_humidity_2m": 58.0,
        "precipitation": 0.0,
        "wind_speed_10m": 12.4
    }
}

MOCK_WEATHER_DATA = {
    "temperature": 31.5,
    "humidity": 58.0,
    "precipitation": 0.0,
    "wind_speed": 12.4
}

def get_auth_headers(email: str = None):
    """Helper to get authentication headers for field analysis tests.

    Uses a unique email per call so repeated runs against the persistent
    SQLite database never collide with an already-registered account.
    Follows the current auth flow: signup -> verify-email -> login.
    """
    if email is None:
        email = f"field_test_user_{uuid.uuid4().hex[:6]}@example.com"
    password = "password123"

    with patch.object(EmailService, 'send_verification_email') as mock_send:
        mock_send.return_value = True
        signup_res = client.post("/api/auth/signup", json={
            "email": email,
            "full_name": "Field Tester"
        })
        assert signup_res.status_code == 201
        raw_token = mock_send.call_args[0][2]

    verify_res = client.post("/api/auth/verify-email", json={"token": raw_token, "password": password})
    assert verify_res.status_code == 200

    login_res = client.post("/api/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_res.status_code == 200

    return {"Authorization": f"Bearer {login_res.json()['access_token']}"}


def test_weather_service_mocked():
    """Verify WeatherService parses raw Open-Meteo API response correctly."""
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = json.dumps(MOCK_OPEN_METEO_RESPONSE).encode('utf-8')
    mock_response.__enter__.return_value = mock_response

    with patch('urllib.request.urlopen', return_value=mock_response):
        weather = WeatherService.get_current_weather(11.6643, 78.1460)
        assert weather["temperature"] == 31.5
        assert weather["humidity"] == 58.0
        assert weather["precipitation"] == 0.0
        assert weather["wind_speed"] == 12.4


def test_get_current_weather_endpoint():
    """Verify GET /api/weather/current returns HTTP 200 and formatted weather JSON."""
    with patch.object(WeatherService, 'get_current_weather', return_value=MOCK_WEATHER_DATA):
        response = client.get("/api/weather/current?latitude=11.6643&longitude=78.1460")
        assert response.status_code == 200
        data = response.json()
        assert data["latitude"] == 11.6643
        assert data["longitude"] == 78.1460
        assert "weather" in data
        assert data["weather"]["temperature"] == 31.5
        assert data["weather"]["humidity"] == 58.0


def test_post_field_analysis_endpoint_success():
    """Verify POST /api/ai/field-analysis returns structured field analysis JSON for authenticated user."""
    headers = get_auth_headers()
    payload = {
        "crop_type": "Tomato",
        "current_soil_moisture": 35.0,
        "soil_ph": 6.5,
        "soil_temperature": 30.0
    }

    with patch.object(WeatherService, 'get_current_weather', return_value=MOCK_WEATHER_DATA):
        response = client.post("/api/ai/field-analysis", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()

        # Check main keys
        assert "history_id" in data
        assert "location" in data
        # Phase 2A: farmer-facing coordinates are removed entirely.
        assert "latitude" not in data["location"]
        assert "longitude" not in data["location"]

        assert "weather" in data
        assert data["weather"]["temperature"] == 31.5
        assert data["weather"]["humidity"] == 58.0

        assert "soil" in data
        assert data["soil"]["current_soil_moisture"] == 35.0

        assert "analysis" in data
        assert data["analysis"]["status"] in ["IRRIGATION_REQUIRED", "MONITOR", "NO_IRRIGATION_NEEDED"]

        assert "prototype_notice" in data


def test_field_analysis_validation_invalid_crop():
    """Verify POST /api/ai/field-analysis returns 422 for unsupported crop."""
    headers = get_auth_headers()
    payload = {
        "crop_type": "Banana",
        "current_soil_moisture": 35.0,
        "soil_ph": 6.5,
        "soil_temperature": 30.0
    }
    response = client.post("/api/ai/field-analysis", json=payload, headers=headers)
    assert response.status_code == 422


def test_field_analysis_ignores_legacy_coordinates():
    """Phase 2A: legacy latitude/longitude payloads are accepted-but-ignored (no 422, no coordinates echoed)."""
    headers = get_auth_headers()
    payload = {
        "crop_type": "Tomato",
        "latitude": 120.0,
        "longitude": 78.1460,
        "current_soil_moisture": 35.0,
        "soil_ph": 6.5,
        "soil_temperature": 30.0
    }

    with patch.object(WeatherService, 'get_current_weather', return_value=MOCK_WEATHER_DATA):
        response = client.post("/api/ai/field-analysis", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "latitude" not in data.get("location", {})
        assert "longitude" not in data.get("location", {})


def test_field_analysis_validation_invalid_soil_moisture():
    """Verify POST /api/ai/field-analysis returns 422 for moisture out of range [0, 100]."""
    headers = get_auth_headers()
    payload = {
        "crop_type": "Tomato",
        "current_soil_moisture": 150.0,
        "soil_ph": 6.5,
        "soil_temperature": 30.0
    }
    response = client.post("/api/ai/field-analysis", json=payload, headers=headers)
    assert response.status_code == 422
