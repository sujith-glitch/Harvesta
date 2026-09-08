import os
import sys

# Ensure workspace root is in sys.path for pytest module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from ml.irrigation_recommendation import get_irrigation_recommendation


def test_valid_input_structure():
    """Test that valid input returns full expected schema keys."""
    sample_input = {
        "crop_type": "Tomato",
        "current_soil_moisture": 40.0,
        "predicted_soil_moisture": 38.0,
        "temperature": 28.0,
        "humidity": 60.0,
        "rainfall": 0.0
    }
    result = get_irrigation_recommendation(sample_input)
    assert isinstance(result, dict)
    assert "recommendation" in result
    assert "priority" in result
    assert "predicted_soil_moisture" in result
    assert "current_soil_moisture" in result
    assert "reason" in result
    assert "factors" in result
    assert "prototype_notice" in result
    assert result["recommendation"] in ["IRRIGATION_REQUIRED", "MONITOR", "NO_IRRIGATION_NEEDED"]
    assert result["priority"] in ["HIGH", "MEDIUM", "LOW"]

def test_missing_input_handling():
    """Test that engine handles missing input values cleanly with defaults."""
    result = get_irrigation_recommendation({})
    assert isinstance(result, dict)
    assert "recommendation" in result
    assert result["recommendation"] in ["IRRIGATION_REQUIRED", "MONITOR", "NO_IRRIGATION_NEEDED"]

def test_invalid_crop_handling():
    """Test that engine handles unknown/invalid crop names safely."""
    sample_input = {
        "crop_type": "UnknownDragonFruit",
        "current_soil_moisture": 30.0,
        "predicted_soil_moisture": 25.0,
        "temperature": 35.0,
        "humidity": 40.0,
        "rainfall": 0.0
    }
    result = get_irrigation_recommendation(sample_input)
    assert result["recommendation"] == "IRRIGATION_REQUIRED"
    assert result["priority"] in ["HIGH", "MEDIUM"]

def test_low_moisture_scenario():
    """Test low moisture scenario triggers IRRIGATION_REQUIRED."""
    sample_input = {
        "crop_type": "Tomato",
        "current_soil_moisture": 25.0,
        "predicted_soil_moisture": 28.0,
        "temperature": 32.0,
        "humidity": 45.0,
        "rainfall": 0.0
    }
    result = get_irrigation_recommendation(sample_input)
    assert result["recommendation"] == "IRRIGATION_REQUIRED"
    assert result["priority"] == "HIGH"
    assert len(result["factors"]) > 0

def test_moderate_moisture_scenario():
    """Test moderate moisture scenario triggers MONITOR."""
    sample_input = {
        "crop_type": "Tomato",
        "current_soil_moisture": 52.0,
        "predicted_soil_moisture": 55.0,
        "temperature": 25.0,
        "humidity": 65.0,
        "rainfall": 0.0
    }
    result = get_irrigation_recommendation(sample_input)
    assert result["recommendation"] == "MONITOR"
    assert result["priority"] in ["LOW", "MEDIUM"]

def test_high_moisture_rainfall_scenario():
    """Test high moisture and recent rain triggers NO_IRRIGATION_NEEDED."""
    sample_input = {
        "crop_type": "Rice",
        "current_soil_moisture": 50.0,
        "predicted_soil_moisture": 52.0,
        "temperature": 24.0,
        "humidity": 80.0,
        "rainfall": 15.0
    }
    result = get_irrigation_recommendation(sample_input)
    assert result["recommendation"] == "NO_IRRIGATION_NEEDED"
    assert result["priority"] == "LOW"
    assert "rainfall" in result["reason"].lower()
