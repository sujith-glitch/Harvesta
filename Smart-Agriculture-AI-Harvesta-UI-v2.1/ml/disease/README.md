# Crop Disease Vision ML Pipeline

This directory contains the training and evaluation pipeline for the **Smart Agriculture AI Harvesta Crop Disease Screening Feature (Phase D)**.

---

## 1. Directory Structure

```
ml/disease/
  ├── prepare_dataset.py       # Image feature extraction and reproducible dataset generator
  ├── train_disease_model.py   # Training script (MLP / StandardScaler pipeline with early stopping)
  ├── evaluate_disease_model.py# Model evaluation & confusion matrix reporter
  ├── disease_metadata.json    # 10-class metadata & agronomic recommendation mapping
  └── README.md                # Documentation & usage instructions
```

---

## 2. Dataset Reference & Licensing

The class taxonomy and feature representations are modeled on the **PlantVillage Crop Disease Benchmark Dataset** (Penn State University / David Hughes & Marcel Salathé, distributed under the **Creative Commons Attribution-ShareAlike 4.0 International (CC-BY-SA 4.0)** license).

---

## 3. Supported Prototype Classes (10 Classes)

| # | Class Key | Crop | Condition | Urgency |
|---|---|---|---|---|
| 1 | `Tomato___Healthy` | Tomato | Healthy | Low |
| 2 | `Tomato___Early_Blight` | Tomato | Early Blight (*Alternaria solani*) | Medium |
| 3 | `Tomato___Late_Blight` | Tomato | Late Blight (*Phytophthora infestans*) | High |
| 4 | `Tomato___Leaf_Mold` | Tomato | Leaf Mold (*Passalora fulva*) | Medium |
| 5 | `Potato___Healthy` | Potato | Healthy | Low |
| 6 | `Potato___Early_Blight` | Potato | Early Blight (*Alternaria solani*) | Medium |
| 7 | `Potato___Late_Blight` | Potato | Late Blight (*Phytophthora infestans*) | High |
| 8 | `Corn___Healthy` | Maize | Healthy | Low |
| 9 | `Corn___Common_Rust` | Maize | Common Rust (*Puccinia sorghi*) | Medium |
| 10| `Pepper___Healthy` | Pepper | Healthy | Low |

---

## 4. Running Training & Evaluation

To train the vision model artifact and generate evaluation metrics:

```bash
python ml/disease/train_disease_model.py
```

To evaluate the trained model on held-out test splits:

```bash
python ml/disease/evaluate_disease_model.py
```

Artifacts are saved directly into:
- `ml/models/crop_disease_model.joblib`
- `ml/models/crop_disease_metadata.json`
