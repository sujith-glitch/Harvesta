from ml.dataset_registry import load_dataset, validate_dataset

def test_registered_samples_load():
    assert len(load_dataset("weather_history")) > 0
    assert len(load_dataset("soil_crop_suitability")) > 0

def test_validation_reports_missing_columns():
    errors = validate_dataset("weather_history", __import__("pandas").DataFrame({"date": ["2026-01-01"]}))
    assert any("missing columns" in error for error in errors)
