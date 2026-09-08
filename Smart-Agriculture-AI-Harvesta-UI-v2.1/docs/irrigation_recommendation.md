# Explainable Irrigation Recommendation Engine Documentation 🌾🤖

> [!IMPORTANT]
> **DEVELOPMENT PROTOTYPE DISCLAIMER**: This irrigation recommendation engine uses synthetic and development datasets to demonstrate software architecture and decision-tree logic. It is **NOT** scientifically validated for real-world agricultural decision-making or commercial farm irrigation advice.

---

## 1. Purpose
The Irrigation Recommendation Engine bridges environmental observation data, Phase 3 machine learning predictions, and crop reference guidelines into transparent, explainable recommendations for farmers.

## 2. Inputs
The engine accepts the following parameters:
- `crop_type`: Active crop species (`Rice`, `Tomato`, `Maize`, `Cotton`, `Wheat`)
- `current_soil_moisture`: Current volumetric soil moisture reading (%)
- `predicted_soil_moisture`: Phase 3 ML model predicted soil moisture (%)
- `temperature`: Ambient air temperature (°C)
- `humidity`: Relative atmospheric humidity (%)
- `rainfall`: Precipitation depth (mm)

## 3. Outputs
The engine returns a structured JSON-compatible dictionary:
```json
{
  "recommendation": "IRRIGATION_REQUIRED",
  "priority": "HIGH",
  "predicted_soil_moisture": 32.5,
  "current_soil_moisture": 30.0,
  "reason": "Predicted soil moisture (32.50%) is below the minimum optimal threshold (45.00%) for Tomato.",
  "factors": [
    "Predicted moisture 32.50% is lower than minimum optimal threshold 45.00%.",
    "No significant recent rainfall (0.0mm) to replenish soil water.",
    "High ambient temperature (34.0°C) accelerates evapotranspiration."
  ],
  "prototype_notice": "This is a prototype recommendation based on development/synthetic data."
}
```

## 4. Recommendation States & Priorities
- **States**:
  1. `IRRIGATION_REQUIRED` — Soil moisture is below crop-specific minimum threshold without natural rain replenishment.
  2. `MONITOR` — Soil moisture is in an intermediate range or recent rain is expected to recharge the root zone.
  3. `NO_IRRIGATION_NEEDED` — Soil moisture is at optimal capacity or sufficient precipitation has occurred.
- **Priorities**: `HIGH`, `MEDIUM`, `LOW`

## 5. Prototype Decision Logic
The decision rules follow an explicit conditional tree:

```text
[Input Data] ──► Read Crop Reference (water_requirement)
                      │
        ┌─────────────┴─────────────┐
   Rainfall >= 5mm?              Rainfall < 5mm?
        │                               │
  Predicted SM >= Threshold-5?   Predicted SM < Low Threshold?
    ├── Yes: NO_IRRIGATION_NEEDED  ├── Yes: IRRIGATION_REQUIRED (Priority HIGH/MEDIUM)
    └── No:  MONITOR               ├── Mid: MONITOR (Priority MEDIUM/LOW)
                                   └── High: NO_IRRIGATION_NEEDED (Priority LOW)
```

## 6. Threshold Assumptions
Base volumetric soil moisture thresholds derived from prototype assumptions:
- **High Water Requirement** (e.g., Rice): Low Threshold = `55.0%`, High Threshold = `75.0%`
- **Medium Water Requirement** (e.g., Tomato, Maize, Cotton): Low Threshold = `45.0%`, High Threshold = `68.0%`
- **Low Water Requirement** (e.g., Wheat): Low Threshold = `35.0%`, High Threshold = `60.0%`

## 7. How Rainfall Affects the Decision
- Precipitation $\ge$ 5.0mm reduces irrigation urgency because natural water recharge is actively taking place.
- Prevents unnecessary over-watering and root rot risks during rain events.

## 8. How Temperature Affects the Decision
- High temperatures ($\ge$ 30.0°C) accelerate evapotranspiration rates.
- When moisture is low and temperature is high, the urgency priority escalates from `MEDIUM` to `HIGH`.

## 9. How Crop Water Requirement Is Considered
- The engine dynamically queries [crop_reference_data.csv](file:///c:/Users/sujit_a01ggsb/Downloads/Smart-Agriculture-AI/data/sample/crop_reference_data.csv) to adapt low/high moisture thresholds according to the crop species.

## 10. Example Scenarios
1. **Low Moisture / High Temp (Tomato)**: `current_sm=32%`, `predicted_sm=30%`, `temp=34°C`, `rain=0mm` $\rightarrow$ `IRRIGATION_REQUIRED` (Priority: `HIGH`)
2. **Moderate Moisture (Wheat)**: `current_sm=52%`, `predicted_sm=55%`, `temp=22°C`, `rain=0mm` $\rightarrow$ `MONITOR` (Priority: `LOW`)
3. **Recent Rain (Rice)**: `current_sm=45%`, `predicted_sm=48%`, `temp=24°C`, `rain=15mm` $\rightarrow$ `NO_IRRIGATION_NEEDED` (Priority: `LOW`)

## 11. Limitations
- Does not account for soil texture classes (clay, sand, loam).
- Does not model evapotranspiration curves over multiple future days.

## 12. Why This Is Not Professional Agronomic Advice
- Built on synthetic development datasets and simplified static threshold rules. Real-world farms require professional agronomic field assessments and calibrated physical hardware sensors.

## 13. Future Improvements
- Multi-day weather forecast integration via OpenWeather API.
- Satellite-derived soil moisture indices (NDWI/SMAP).
- Soil texture parameter integration.
