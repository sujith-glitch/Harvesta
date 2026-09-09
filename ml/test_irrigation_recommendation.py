import os
import sys

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ml.irrigation_recommendation import get_irrigation_recommendation


def run_scenario_tests():
    print("=" * 70)
    print("TESTING IRRIGATION RECOMMENDATION ENGINE SCENARIOS")
    print("=" * 70)

    all_passed = True

    # Test Scenario 1: Very Low Moisture, No Rainfall, High Temp -> IRRIGATION_REQUIRED
    print("\n[SCENARIO 1] Very Low Soil Moisture + High Temp + Zero Rain")
    scenario_1_inputs = [
        {"crop_type": "Tomato", "current_soil_moisture": 32.0, "predicted_soil_moisture": 30.0, "temperature": 34.0, "humidity": 45.0, "rainfall": 0.0},
        {"crop_type": "Rice", "current_soil_moisture": 40.0, "predicted_soil_moisture": 42.0, "temperature": 33.0, "humidity": 50.0, "rainfall": 0.0},
        {"crop_type": "Maize", "current_soil_moisture": 28.0, "predicted_soil_moisture": 29.0, "temperature": 31.0, "humidity": 40.0, "rainfall": 0.0}
    ]

    for data in scenario_1_inputs:
        res = get_irrigation_recommendation(data)
        status = "PASSED" if res["recommendation"] == "IRRIGATION_REQUIRED" else "FAILED"
        if status == "FAILED":
            all_passed = False
        print(f"  [{status}] Crop: {data['crop_type']:<8} | Expected: IRRIGATION_REQUIRED | Got: {res['recommendation']} ({res['priority']} Priority)")

    # Test Scenario 2: Moderate Soil Moisture, Low/No Rainfall -> MONITOR
    print("\n[SCENARIO 2] Moderate Soil Moisture + No Rain")
    scenario_2_inputs = [
        {"crop_type": "Tomato", "current_soil_moisture": 52.0, "predicted_soil_moisture": 55.0, "temperature": 26.0, "humidity": 65.0, "rainfall": 0.0},
        {"crop_type": "Rice", "current_soil_moisture": 60.0, "predicted_soil_moisture": 62.0, "temperature": 25.0, "humidity": 70.0, "rainfall": 0.0},
        {"crop_type": "Maize", "current_soil_moisture": 50.0, "predicted_soil_moisture": 52.0, "temperature": 24.0, "humidity": 60.0, "rainfall": 0.0}
    ]

    for data in scenario_2_inputs:
        res = get_irrigation_recommendation(data)
        status = "PASSED" if res["recommendation"] == "MONITOR" else "FAILED"
        if status == "FAILED":
            all_passed = False
        print(f"  [{status}] Crop: {data['crop_type']:<8} | Expected: MONITOR             | Got: {res['recommendation']} ({res['priority']} Priority)")

    # Test Scenario 3: High Soil Moisture + Recent Rainfall -> NO_IRRIGATION_NEEDED
    print("\n[SCENARIO 3] High Soil Moisture OR Recent Rainfall")
    scenario_3_inputs = [
        {"crop_type": "Tomato", "current_soil_moisture": 75.0, "predicted_soil_moisture": 78.0, "temperature": 24.0, "humidity": 80.0, "rainfall": 0.0},
        {"crop_type": "Rice", "current_soil_moisture": 50.0, "predicted_soil_moisture": 52.0, "temperature": 22.0, "humidity": 85.0, "rainfall": 15.0},
        {"crop_type": "Maize", "current_soil_moisture": 70.0, "predicted_soil_moisture": 72.0, "temperature": 23.0, "humidity": 75.0, "rainfall": 5.0}
    ]


    for data in scenario_3_inputs:
        res = get_irrigation_recommendation(data)
        status = "PASSED" if res["recommendation"] == "NO_IRRIGATION_NEEDED" else "FAILED"
        if status == "FAILED":
            all_passed = False
        print(f"  [{status}] Crop: {data['crop_type']:<8} | Expected: NO_IRRIGATION_NEEDED| Got: {res['recommendation']} ({res['priority']} Priority)")

    print("\n" + "=" * 70)
    if all_passed:
        print("ALL SCENARIO TESTS PASSED SUCCESSFULLY!")
        print("=" * 70)
        return True
    else:
        print("SOME SCENARIO TESTS FAILED.")
        print("=" * 70)
        return False

if __name__ == "__main__":
    success = run_scenario_tests()
    if not success:
        sys.exit(1)
