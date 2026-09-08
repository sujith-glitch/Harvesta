# Crop Disease Vision Model Architecture & Performance

This document describes the computer vision architecture, feature extraction pipeline, evaluation metrics, and inference serialization for **Harvesta Disease Vision AI v1.0**.

---

## 1. Vision Architecture Overview

The Harvesta Disease Vision model utilizes a lightweight, CPU-efficient, high-performance hybrid architecture combining **Spatial-Spectral Color Moments, Vegetation Indices, Texture Gradients, and a Multi-Layer Perceptron (MLP)** classifier.

```
Uploaded Leaf Image (JPEG / PNG / WebP)
  │
  ▼
[ 1. ImageStorageService ] ── Security & Integrity Verification (<=5MB, RGB conversion)
  │
  ▼
[ 2. Feature Extraction ] ── 191 Normalized Feature Vector:
    ├── Global Channel Stats (Mean, Std, Median, 25th/75th Percentiles for R, G, B)
    ├── Vegetation Indices (Excess Green ExG, NGRDI, Chlorophyll Index)
    ├── 4x4 Spatial Sub-Region Moments (128 features across local quadrants)
    ├── Edge Gradient Texture Statistics (Sobel-approximated gradient magnitude & energy)
    └── 8-bin Color Histograms per Channel (24 features)
  │
  ▼
[ 3. StandardScaler Pipeline ] ── Zero-mean, unit-variance normalization
  │
  ▼
[ 4. Multi-Layer Perceptron ] ── Hidden Layers: (128, 64) with ReLU & Adam Optimizer
  │
  ▼
[ 5. Calibrated Probabilities ] ── Top Class, Confidence (0-100%), Top-3 Candidates
```

---

## 2. Benchmark Metrics on Held-Out Test Split

| Metric | Score | Note |
|---|---|---|
| **Test Accuracy** | **71.67% - 77.50%** | Held-out unseen synthetic benchmark images |
| **Test Macro F1** | **0.6919** | Balanced across all 10 prototype classes |
| **Inference Latency** | **< 35 ms** | Fast CPU execution without GPU dependency |
| **Model Size** | **~250 KB** | Ultra-lightweight `.joblib` serialization |

---

## 3. Artifact Files & Locations

- **Model Binary**: `ml/models/crop_disease_model.joblib`
- **Model Metadata**: `ml/models/crop_disease_metadata.json`
- **Class Ontology & Recommendations**: `ml/disease/disease_metadata.json`
- **Training Pipeline**: `ml/disease/train_disease_model.py`
- **Evaluation Pipeline**: `ml/disease/evaluate_disease_model.py`

---

## 4. Production Serving & Thread Safety

- Model is initialized once via singleton pattern in `DiseaseService.initialize()` upon application startup.
- In-memory inference is thread-safe for concurrent FastAPI worker processes.
- Future upgrades can drop in deep PyTorch / MobileNetV4 weights by updating `DiseaseService.predict_image()` without altering downstream database schemas or frontend interfaces.
