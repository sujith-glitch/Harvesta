"""
Phase 2 Test Suite: Farm & Crop Management.

Covers:
1.  Create farm
2.  Get own farms
3.  Update own farm
4.  Delete own farm
5.  Create crop
6.  Get own crops
7.  Update own crop
8.  Delete own crop
9.  Unauthorized farm access (401 / 403 / 404)
10. Unauthorized crop access (401 / 403 / 404)
11. Existing authentication still works
12. Existing field analysis works without coordinates
13. Existing analysis history still works
"""

import os
import sys
import uuid
from unittest.mock import patch

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.email_service import EmailService
from backend.app.services.weather_service import WeatherService

client = TestClient(app)

MOCK_WEATHER_DATA = {
    "temperature": 30.5,
    "humidity": 55.0,
    "precipitation": 0.0,
    "wind_speed": 10.0
}


def create_verified_user_and_get_headers(email_prefix: str = "farm_user"):
    """Signup -> verify-email -> login; returns Bearer auth headers."""
    email = f"{email_prefix}_{uuid.uuid4().hex[:6]}@example.com"
    password = "password123"

    with patch.object(EmailService, 'send_verification_email') as mock_send:
        mock_send.return_value = True
        signup_res = client.post("/api/auth/signup", json={
            "email": email,
            "full_name": "Farm Tester"
        })
        assert signup_res.status_code == 201
        raw_token = mock_send.call_args[0][2]

    verify_res = client.post("/api/auth/verify-email", json={"token": raw_token, "password": password})
    assert verify_res.status_code == 200

    login_res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login_res.status_code == 200
    return {"Authorization": f"Bearer {login_res.json()['access_token']}"}


def make_farm_payload(name: str = "Green Valley Farm"):
    return {
        "name": name,
        "location": "Salem",
        "district": "Salem District",
        "state": "Tamil Nadu",
        "country": "India",
        "size": 12.5,
        "soil_type": "Loamy",
        "farming_method": "Organic",
        "description": "A test farm with mixed cultivation."
    }


def create_farm_for_user(headers) -> dict:
    res = client.post("/api/farms", json=make_farm_payload(), headers=headers)
    assert res.status_code == 201
    return res.json()


# ---------------------------------------------------------------------------
# Farm CRUD
# ---------------------------------------------------------------------------

def test_create_farm():
    """1. Authenticated user can create a farm; no lat/lon anywhere."""
    headers = create_verified_user_and_get_headers("create_farm")
    body = create_farm_payload = {
        **make_farm_payload(),
    }
    assert "latitude" not in body
    assert "longitude" not in body

    res = client.post("/api/farms", json=body, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Green Valley Farm"
    assert data["location"] == "Salem"
    assert data["district"] == "Salem District"
    assert data["state"] == "Tamil Nadu"
    assert data["country"] == "India"
    assert data["size"] == 12.5
    assert data["soil_type"] == "Loamy"
    assert data["farming_method"] == "Organic"
    assert data["crop_count"] == 0
    assert "id" in data


def test_get_own_farms_only():
    """2. GET /api/farms returns only the authenticated user's farms."""
    headers_a = create_verified_user_and_get_headers("list_farm_a")
    headers_b = create_verified_user_and_get_headers("list_farm_b")

    farm_a = create_farm_for_user(headers_a)
    create_farm_for_user(headers_b)

    res = client.get("/api/farms", headers=headers_a)
    assert res.status_code == 200
    farms = res.json()
    assert len(farms) >= 1
    assert all(f["user_id"] == farm_a["user_id"] for f in farms)
    assert any(f["id"] == farm_a["id"] for f in farms)


def test_update_own_farm():
    """3. PUT /api/farms/{id} updates fields of own farm."""
    headers = create_verified_user_and_get_headers("update_farm")
    farm = create_farm_for_user(headers)

    update_res = client.put(f"/api/farms/{farm['id']}", json={
        "name": "Renamed Farm",
        "size": 20.0,
        "soil_type": "Clay"
    }, headers=headers)
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["name"] == "Renamed Farm"
    assert data["size"] == 20.0
    assert data["soil_type"] == "Clay"
    # Untouched fields remain intact
    assert data["location"] == "Salem"


def test_delete_own_farm():
    """4. DELETE /api/farms/{id} removes own farm; subsequent reads return 404."""
    headers = create_verified_user_and_get_headers("delete_farm")
    farm = create_farm_for_user(headers)

    del_res = client.delete(f"/api/farms/{farm['id']}", headers=headers)
    assert del_res.status_code == 200

    get_res = client.get(f"/api/farms/{farm['id']}", headers=headers)
    assert get_res.status_code == 404


def test_delete_farm_cascades_crops():
    """Deleting a farm removes its crops too (ORM cascade)."""
    headers = create_verified_user_and_get_headers("cascade_farm")
    farm = create_farm_for_user(headers)

    crop_res = client.post(f"/api/farms/{farm['id']}/crops", json={"name": "Tomato"}, headers=headers)
    assert crop_res.status_code == 201
    crop_id = crop_res.json()["id"]

    del_res = client.delete(f"/api/farms/{farm['id']}", headers=headers)
    assert del_res.status_code == 200

    crop_res = client.get(f"/api/crops/{crop_id}", headers=headers)
    assert crop_res.status_code == 404


# ---------------------------------------------------------------------------
# Crop CRUD
# ---------------------------------------------------------------------------

def test_create_crop():
    """5. POST /api/farms/{farm_id}/crops adds a crop to own farm."""
    headers = create_verified_user_and_get_headers("create_crop")
    farm = create_farm_for_user(headers)

    payload = {
        "name": "Tomato",
        "variety": "Roma",
        "planting_date": "2026-01-15",
        "expected_harvest_date": "2026-04-30",
        "growth_stage": "Fruiting",
        "health_status": "Healthy",
        "notes": "Drip irrigated."
    }
    res = client.post(f"/api/farms/{farm['id']}/crops", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Tomato"
    assert data["variety"] == "Roma"
    assert data["planting_date"] == "2026-01-15"
    assert data["expected_harvest_date"] == "2026-04-30"
    assert data["growth_stage"] == "Fruiting"
    assert data["health_status"] == "Healthy"
    assert data["farm_id"] == farm["id"]


def test_create_crop_invalid_growth_stage_rejected():
    """Crop validation rejects unsupported growth stage values."""
    headers = create_verified_user_and_get_headers("invalid_stage")
    farm = create_farm_for_user(headers)

    res = client.post(f"/api/farms/{farm['id']}/crops", json={
        "name": "Rice",
        "growth_stage": "Flying"
    }, headers=headers)
    assert res.status_code == 422


def test_get_own_crops():
    """6. GET /api/farms/{farm_id}/crops lists crops of own farm."""
    headers = create_verified_user_and_get_headers("list_crops")
    farm = create_farm_for_user(headers)

    client.post(f"/api/farms/{farm['id']}/crops", json={"name": "Tomato"}, headers=headers)
    client.post(f"/api/farms/{farm['id']}/crops", json={"name": "Rice"}, headers=headers)

    res = client.get(f"/api/farms/{farm['id']}/crops", headers=headers)
    assert res.status_code == 200
    crops = res.json()
    assert len(crops) == 2
    assert {c["name"] for c in crops} == {"Tomato", "Rice"}


def test_update_own_crop():
    """7. PUT /api/crops/{id} updates own crop."""
    headers = create_verified_user_and_get_headers("update_crop")
    farm = create_farm_for_user(headers)

    crop_res = client.post(f"/api/farms/{farm['id']}/crops", json={"name": "Chili"}, headers=headers)
    crop_id = crop_res.json()["id"]

    upd_res = client.put(f"/api/crops/{crop_id}", json={
        "health_status": "Needs Attention",
        "growth_stage": "Flowering",
        "expected_harvest_date": "2026-09-01"
    }, headers=headers)
    assert upd_res.status_code == 200
    data = upd_res.json()
    assert data["health_status"] == "Needs Attention"
    assert data["growth_stage"] == "Flowering"
    assert data["expected_harvest_date"] == "2026-09-01"
    assert data["name"] == "Chili"


def test_delete_own_crop():
    """8. DELETE /api/crops/{id} removes own crop."""
    headers = create_verified_user_and_get_headers("delete_crop")
    farm = create_farm_for_user(headers)

    crop_res = client.post(f"/api/farms/{farm['id']}/crops", json={"name": "Wheat"}, headers=headers)
    crop_id = crop_res.json()["id"]

    del_res = client.delete(f"/api/crops/{crop_id}", headers=headers)
    assert del_res.status_code == 200

    get_res = client.get(f"/api/crops/{crop_id}", headers=headers)
    assert get_res.status_code == 404


# ---------------------------------------------------------------------------
# Authorization & scoping
# ---------------------------------------------------------------------------

def test_unauthenticated_farm_access_rejected():
    """9a. All farm endpoints require authentication -> 401."""
    assert client.get("/api/farms").status_code == 401
    assert client.get("/api/farms/1").status_code == 401
    assert client.post("/api/farms", json=make_farm_payload()).status_code == 401
    assert client.put("/api/farms/1", json={}).status_code == 401
    assert client.delete("/api/farms/1").status_code == 401
    assert client.get("/api/farms/1/crops").status_code == 401
    assert client.post("/api/farms/1/crops", json={"name": "Rice"}).status_code == 401
    assert client.get("/api/crops/1").status_code == 401
    assert client.put("/api/crops/1", json={}).status_code == 401
    assert client.delete("/api/crops/1").status_code == 401


def test_unauthorized_farm_access_blocked():
    """9b. User B cannot access/update/delete User A's farm -> 403 (not leaked as 404)."""
    headers_a = create_verified_user_and_get_headers("own_farm_a")
    headers_b = create_verified_user_and_get_headers("other_farm_b")
    farm_a = create_farm_for_user(headers_a)

    assert client.get(f"/api/farms/{farm_a['id']}", headers=headers_b).status_code == 403
    assert client.put(f"/api/farms/{farm_a['id']}", json={"name": "Hijacked"}, headers=headers_b).status_code == 403
    assert client.delete(f"/api/farms/{farm_a['id']}", headers=headers_b).status_code == 403
    assert client.get(f"/api/farms/{farm_a['id']}/crops", headers=headers_b).status_code == 403
    assert client.post(f"/api/farms/{farm_a['id']}/crops", json={"name": "Rice"}, headers=headers_b).status_code == 403

    # Farm A owner retains access.
    assert client.get(f"/api/farms/{farm_a['id']}", headers=headers_a).status_code == 200


def test_unauthorized_crop_access_blocked():
    """10. User B cannot access/update/delete User A's crop -> 403; missing ids -> 404."""
    headers_a = create_verified_user_and_get_headers("own_crop_a")
    headers_b = create_verified_user_and_get_headers("other_crop_b")
    farm_a = create_farm_for_user(headers_a)

    crop_res = client.post(f"/api/farms/{farm_a['id']}/crops", json={"name": "Maize"}, headers=headers_a)
    crop_id = crop_res.json()["id"]

    assert client.get(f"/api/crops/{crop_id}", headers=headers_b).status_code == 403
    assert client.put(f"/api/crops/{crop_id}", json={"name": "Stolen"}, headers=headers_b).status_code == 403
    assert client.delete(f"/api/crops/{crop_id}", headers=headers_b).status_code == 403

    # Non-existent resources -> 404 for the rightful owner.
    assert client.get("/api/farms/99999999", headers=headers_a).status_code == 404
    assert client.get("/api/crops/99999999", headers=headers_a).status_code == 404


def test_crop_of_other_users_farm_not_accessible_via_crop_id():
    """Crop IDs cannot be used to bypass farm ownership."""
    headers_a = create_verified_user_and_get_headers("bypass_a")
    headers_b = create_verified_user_and_get_headers("bypass_b")
    farm_b = create_farm_for_user(headers_b)

    # B adds a crop to their OWN farm.
    crop_res = client.post(f"/api/farms/{farm_b['id']}/crops", json={"name": "Cotton"}, headers=headers_b)
    crop_id = crop_res.json()["id"]

    # A tries to modify B's crop directly by ID -> blocked.
    assert client.put(f"/api/crops/{crop_id}", json={"notes": "hax"}, headers=headers_a).status_code == 403


# ---------------------------------------------------------------------------
# Existing functionality compatibility
# ---------------------------------------------------------------------------

def test_existing_authentication_still_works():
    """11. Login + protected profile endpoint keep working after Phase 2 changes."""
    headers = create_verified_user_and_get_headers("auth_compat")
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["is_verified"] is True


def test_existing_field_analysis_without_coordinates():
    """12. Field analysis works with no latitude/longitude provided at all."""
    headers = create_verified_user_and_get_headers("analysis_compat")
    payload = {
        "crop_type": "Tomato",
        "current_soil_moisture": 35.0,
        "soil_ph": 6.5,
        "soil_temperature": 30.0
    }
    with patch.object(WeatherService, 'get_current_weather', return_value=MOCK_WEATHER_DATA):
        res = client.post("/api/ai/field-analysis", json=payload, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data["history_id"], int)
        assert "latitude" not in data["location"]
        assert "longitude" not in data["location"]


def test_existing_analysis_history_still_works():
    """13. Analysis history save/list/get/delete flow is unaffected."""
    headers = create_verified_user_and_get_headers("history_compat")

    payload = {
        "crop_type": "Rice",
        "weather": {"temperature": 28.0, "humidity": 75.0, "precipitation": 5.0, "wind_speed": 8.0},
        "soil": {"current_soil_moisture": 50.0, "soil_ph": 6.8, "soil_temperature": 26.0},
        "analysis": {
            "status": "NO_IRRIGATION_NEEDED",
            "priority": "LOW",
            "reason": "Recent rain.",
            "factors": ["Rainfall received."]
        }
    }
    create_res = client.post("/api/history/field-analysis", json=payload, headers=headers)
    assert create_res.status_code == 201

    list_res = client.get("/api/history/field-analysis", headers=headers)
    assert list_res.status_code == 200
    assert any(item["crop_type"] == "Rice" for item in list_res.json())


def test_dashboard_home_endpoint():
    """Phase 2I: dashboard home aggregates farm summary, crop health and recent analyses."""
    headers = create_verified_user_and_get_headers("home_dash")
    farm = create_farm_for_user(headers)

    client.post(f"/api/farms/{farm['id']}/crops", json={
        "name": "Tomato", "health_status": "Healthy"
    }, headers=headers)
    client.post(f"/api/farms/{farm['id']}/crops", json={
        "name": "Rice", "health_status": "Needs Attention"
    }, headers=headers)
    client.post(f"/api/farms/{farm['id']}/crops", json={
        "name": "Chili", "health_status": "Healthy",
        "expected_harvest_date": "2026-12-01"
    }, headers=headers)

    res = client.get("/api/dashboard/home", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["farm"]["id"] == farm["id"]
    assert data["total_crops"] == 3
    # (100 + 55 + 100) / 3 = 85
    assert data["overall_health_percent"] == 85
    assert {c["name"] for c in data["recent_crops"]} == {"Tomato", "Rice", "Chili"}
    assert [c["name"] for c in data["upcoming_harvests"]] == ["Chili"]

    unauth_res = client.get("/api/dashboard/home")
    assert unauth_res.status_code == 401
