# Smart Agriculture AI Platform - Data Directory Guide 📁

This directory contains datasets used by the Smart Agriculture AI Platform divided into three structured subdirectories:

---

## 📂 Subdirectory Overview

### 1. `data/raw/`
- **Purpose**: Storage location for original, unmodified data downloaded from external APIs or sensors.
- **Rule**: Files placed in `raw/` must remain read-only and never be manually altered or overwritten.

### 2. `data/processed/`
- **Purpose**: Stores cleaned, imputed, transformed, and feature-engineered datasets produced by scripts in `ml/preprocess_data.py`.
- **Primary File**:
  - `data/processed/iot_sensor_data_clean.csv` - Cleaned sensor dataset ready for feature building and modeling.

### 3. `data/sample/`
- **Purpose**: Lightweight synthetic and reference datasets used for local offline development and testing.
- **Key Files**:
  - `data/sample/iot_sensor_data.csv` - 1,000 synthetic IoT sensor records.
  - `data/sample/crop_reference_data.csv` - Agronomic baseline growth requirements for Rice, Tomato, Maize, Cotton, and Wheat.

---

> [!NOTE]
> All sample datasets in `data/sample/` are synthetic/simulated for software architecture development.
