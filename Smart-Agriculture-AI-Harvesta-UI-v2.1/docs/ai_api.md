# Smart Agriculture AI Platform - AI Recommendation API Specification

## Endpoint Overview

The AI Recommendation API connects the Phase 3 Soil Moisture Machine Learning model (`soil_moisture_model.joblib`) and the Phase 4 explainable Irrigation Recommendation Engine to provide actionable water management advice for farmers.

- **Endpoint Path**: `/api/ai/irrigation-recommendation`
- **HTTP Method**: `POST`
- **Content-Type**: `application/json`

---

## Request Schema

### Request Body JSON (`IrrigationRecommendationRequest`)

| Field | Type | Required | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| `crop_type` | `string` | Yes | Must be one of `Rice`, `Tomato`, `Maize`, `Cotton`, `Wheat` | Target crop type |
| `temperature` | `number` | Yes | `-50.0` to `70.0` | Ambient air temperature in °C |
| `humidity` | `number` | Yes | `0.0` to `100.0` | Atmospheric relative humidity percentage |
| `rainfall` | `number` | Yes | `>= 0.0` | Recent precipitation volume in mm |
| `current_soil_moisture` | `number` | Yes | `0.0` to `100.0` | Measured root-zone soil moisture percentage |
| `soil_ph` | `number` | Yes | `0.0` to `14.0` | Measured soil pH level |
| `soil_temperature` | `number` | Yes | `-50.0` to `70.0` | Soil temperature in °C |

#### Example Request JSON

```json
{
  "crop_type": "Tomato",
  "temperature": 32.0,
  "humidity": 60.0,
  "rainfall": 0.0,
  "current_soil_moisture": 35.0,
  "soil_ph": 6.5,
  "soil_temperature": 30.0
}
```

---

## Response Schema

### Response Body JSON (`IrrigationRecommendationResponse`)

| Field | Type | Description |
| :--- | :--- | :--- |
| `crop_type` | `string` | Normalized crop name evaluated |
| `input` | `object` | Echoed environmental & soil input parameters |
| `prediction` | `object` | Container for ML model output (`soil_moisture` float percentage) |
| `recommendation` | `object` | Structured recommendation (`status`, `priority`, `reason`, `factors`) |
| `prototype_notice` | `string` | Disclaimer note indicating prototype status |

#### Recommendation Statuses

- `IRRIGATION_REQUIRED`: Active watering required to prevent crop stress.
- `MONITOR`: Moisture acceptable or natural rain expected; observe closely.
- `NO_IRRIGATION_NEEDED`: Moisture levels optimal or excessive; no watering needed.

#### Priority Levels

- `HIGH`: Urgent attention needed (e.g. low soil moisture + high ambient temperatures).
- `MEDIUM`: Standard observation / routine scheduling.
- `LOW`: Optimal conditions or sufficient soil water reserve.

#### Example Response JSON (`HTTP 200 OK`)

```json
{
  "crop_type": "Tomato",
  "input": {
    "temperature": 32.0,
    "humidity": 60.0,
    "rainfall": 0.0,
    "current_soil_moisture": 35.0,
    "soil_ph": 6.5,
    "soil_temperature": 30.0
  },
  "prediction": {
    "soil_moisture": 72.20
  },
  "recommendation": {
    "status": "IRRIGATION_REQUIRED",
    "priority": "HIGH",
    "reason": "Predicted soil moisture (72.20%) is below the minimum threshold (45.0%) for Tomato. Elevated temperature (32.0 C) increases crop water stress.",
    "factors": [
      "Predicted soil moisture is 72.20% (Current: 35.00%).",
      "Target crop 'Tomato' has a 'Medium' water requirement (Low threshold: 45.0%, High threshold: 68.0%).",
      "High ambient temperature (32.0 C) accelerates evapotranspiration."
    ]
  },
  "prototype_notice": "This prediction and recommendation are based on development/synthetic data and are not professional agronomic advice."
}
```

---

## Input Validation & Error Responses

The backend utilizes Pydantic data validation. If input fails validation rules, the API responds with HTTP 422 Unprocessable Entity.

### Validation Failure (`HTTP 422 Unprocessable Entity`)

Returned when fields are missing, out of numeric ranges, or an unsupported crop type is provided.

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "crop_type"],
      "msg": "Value error, Unsupported crop_type 'Banana'. Supported crops are: Cotton, Maize, Rice, Tomato, Wheat",
      "input": "Banana"
    }
  ]
}
```

### Internal Server Error (`HTTP 500 Internal Server Error`)

Returned if model loading or recommendation processing fails internally. Internal stack traces and file system paths are omitted from API responses for security.

```json
{
  "detail": "Soil moisture ML model file is not available."
}
```

---

## Prototype Limitations & Disclaimers

> [!NOTE]
> This endpoint uses a machine learning model trained on prototype synthetic IoT sensor data and reference agronomic tables. Recommendations are provided for platform architecture demonstration and development purposes only, and do not replace certified professional agronomic or extension service advice.
