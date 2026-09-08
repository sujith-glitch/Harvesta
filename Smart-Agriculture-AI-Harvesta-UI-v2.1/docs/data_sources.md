# Data Sources & Metadata Documentation 🌾📊

This document provides complete documentation for development datasets and planned real-world data source integrations for the **Smart Agriculture AI Platform**.

---

## 1. Synthetic IoT Sensor Dataset

> [!IMPORTANT]
> **SYNTHETIC / SIMULATED DATA NOTICE**: This dataset is programmatically generated for local software architecture development and testing. It does **NOT** contain live readings from physical IoT hardware.

### Dataset Overview
- **File Location**: [data/sample/iot_sensor_data.csv](file:///c:/Users/sujit_a01ggsb/Downloads/Smart-Agriculture-AI/data/sample/iot_sensor_data.csv)
- **Processed Clean Location**: [data/processed/iot_sensor_data_clean.csv](file:///c:/Users/sujit_a01ggsb/Downloads/Smart-Agriculture-AI/data/processed/iot_sensor_data_clean.csv)
- **Record Count**: 1,000 hourly sequential records
- **Farms Included**: `FARM001`, `FARM002`, `FARM003`, `FARM004`, `FARM005`
- **Crops Represented**: Rice, Tomato, Maize, Cotton, Wheat

### Schema & Data Dictionary

| Column Name | Data Type | Units / Format | Description | Realistic Range |
| :--- | :--- | :--- | :--- | :--- |
| `timestamp` | `datetime` | `YYYY-MM-DD HH:MM:SS` | Timestamp of simulated sensor reading | Sequential hourly |
| `farm_id` | `string` | Identifier | Unique farm parcel ID | `FARM001` - `FARM005` |
| `crop_type` | `string` | Categorical | Active crop species planted | Rice, Tomato, Maize, Cotton, Wheat |
| `soil_moisture` | `float` | Percentage (`%`) | Volumetric soil water content | `15.0%` to `85.0%` |
| `temperature` | `float` | Celsius (`°C`) | Ambient air temperature | `12.0°C` to `42.0°C` |
| `humidity` | `float` | Percentage (`%`) | Relative atmospheric humidity | `30.0%` to `95.0%` |
| `rainfall` | `float` | Millimeters (`mm`) | Hourly precipitation depth | `0.0mm` to `45.0mm` |
| `soil_ph` | `float` | pH scale (`0-14`) | Soil acidity / alkalinity | `5.5` to `7.8` |
| `soil_temperature`| `float` | Celsius (`°C`) | Soil temperature at root depth | `10.0°C` to `35.0°C` |

### Generation Methodology & Physical Correlations
The dataset is generated via `ml/generate_synthetic_data.py` using physical domain rules:
1. **Diurnal Temperature Cycle**: Ambient temperature follows a 24-hour sinusoidal wave peaking at 15:00.
2. **Thermal Lag**: `soil_temperature` tracks ambient air temperature with root-zone thermal inertia.
3. **Hydrological Dynamics**: `soil_moisture` recharges during rainfall events (`+0.75 * rainfall_mm`) and depletes exponentially based on temperature evapotranspiration.
4. **Acidity Stability**: `soil_ph` stays around crop-specific baseline optimal ranges with realistic sensor variance.

### Limitations
- Does not model extreme microclimate anomalies or localized sensor calibration drifts.
- Simplified soil moisture depletion curve compared to multi-depth soil physics.

---

## 2. Crop Reference Dataset

> [!NOTE]
> **DEVELOPMENT REFERENCE DISCLAIMER**: This dataset contains baseline agronomic guidelines used for developing rule-based decision support logic. It should not be used as professional agricultural advice.

### Dataset Overview
- **File Location**: [data/sample/crop_reference_data.csv](file:///c:/Users/sujit_a01ggsb/Downloads/Smart-Agriculture-AI/data/sample/crop_reference_data.csv)
- **Record Count**: 5 crop species

### Schema & Data Dictionary

| Column Name | Meaning | Units |
| :--- | :--- | :--- |
| `crop_type` | Name of crop species | Text |
| `optimal_temperature_min` | Minimum recommended growth temperature | Celsius (`°C`) |
| `optimal_temperature_max` | Maximum recommended growth temperature | Celsius (`°C`) |
| `optimal_humidity_min` | Minimum recommended relative humidity | Percentage (`%`) |
| `optimal_humidity_max` | Maximum recommended relative humidity | Percentage (`%`) |
| `optimal_soil_ph_min` | Minimum recommended soil pH | pH scale |
| `optimal_soil_ph_max` | Maximum recommended soil pH | pH scale |
| `water_requirement` | General crop irrigation demand category | Low / Medium / High |
| `growth_period_days` | Total days from planting to harvest | Days |

---

## 3. Future Planned Real Data Integrations

The following external public data sources will be integrated in subsequent project phases:

### 1. PlantVillage Dataset
- **Purpose**: Computer vision model training for leaf crop disease detection.
- **Official Public Repository**: [https://github.com/spMohanty/PlantVillage-Dataset](https://github.com/spMohanty/PlantVillage-Dataset)
- **Scale**: Contains 54,306 images covering 14 crop species and 26 specific plant diseases.

### 2. FAOSTAT (Food and Agriculture Organization)
- **Purpose**: Global crop yield statistics and regional agricultural benchmark metrics.
- **Official Source**: [https://www.fao.org/faostat/](https://www.fao.org/faostat/)

### 3. Open Weather APIs (Future Phase)
- **Purpose**: Real-time localized weather forecasting and historical precipitation tracking.
- *Status: Planned for future API phase.*

### 4. Satellite Imagery (Future Phase)
- **Purpose**: Sentinel-2 / Landsat multispectral imagery for calculating Normalized Difference Vegetation Index (NDVI).
- *Status: Planned for future phase.*
