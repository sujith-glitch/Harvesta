"""
Model Training Script for Crop Disease Vision AI.
Trains a lightweight, fast, CPU-friendly image classifier,
evaluates validation performance, and persists artifacts to ml/models/.
"""

import json
import os
import sys
import datetime
import joblib
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from ml.disease.prepare_dataset import prepare_dataset_splits

MODEL_SAVE_PATH = os.path.join(WORKSPACE_ROOT, "ml", "models", "crop_disease_model.joblib")
METADATA_SAVE_PATH = os.path.join(WORKSPACE_ROOT, "ml", "models", "crop_disease_metadata.json")


def train_model():
    print("--- 1. Generating & Loading Dataset Splits ---")
    X_train, y_train, X_val, y_val, X_test, y_test, classes = prepare_dataset_splits(samples_per_class=120)

    print("\n--- 2. Building Model Architecture ---")
    # Multi-Layer Neural Network with StandardScaler and Early Stopping
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", MLPClassifier(
            hidden_layer_sizes=(128, 64),
            activation="relu",
            solver="adam",
            alpha=0.001,
            batch_size=32,
            learning_rate_init=0.002,
            max_iter=300,
            random_state=42,
            early_stopping=True,
            validation_fraction=0.1,
            n_iter_no_change=15,
        )),
    ])

    print("Training crop disease classification model...")
    pipeline.fit(X_train, y_train)

    print("\n--- 3. Evaluating Model ---")
    train_preds = pipeline.predict(X_train)
    val_preds = pipeline.predict(X_val)
    test_preds = pipeline.predict(X_test)

    train_acc = float(accuracy_score(y_train, train_preds))
    val_acc = float(accuracy_score(y_val, val_preds))
    test_acc = float(accuracy_score(y_test, test_preds))
    test_f1_macro = float(f1_score(y_test, test_preds, average="macro"))

    print(f"Training Accuracy:   {train_acc * 100:.2f}%")
    print(f"Validation Accuracy: {val_acc * 100:.2f}%")
    print(f"Test Set Accuracy:   {test_acc * 100:.2f}%")
    print(f"Test Macro F1-Score: {test_f1_macro:.4f}")

    print("\nDetailed Classification Report on Held-Out Test Set:")
    report_dict = classification_report(y_test, test_preds, target_names=classes, output_dict=True)
    print(classification_report(y_test, test_preds, target_names=classes))

    print("\n--- 4. Saving Model Artifacts ---")
    os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)
    joblib.dump(pipeline, MODEL_SAVE_PATH)
    print(f"Model saved to: {MODEL_SAVE_PATH}")

    metadata = {
        "model_version": "harvesta-disease-vision-v1.0",
        "model_type": "StandardScaler + MultiLayerPerceptron (128, 64)",
        "training_date": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "dataset_reference": "Synthetic development images using a 10-class taxonomy inspired by PlantVillage; not trained on the official PlantVillage photographs",
        "input_size": [128, 128],
        "feature_count": int(X_train.shape[1]),
        "total_samples": len(y_train) + len(y_val) + len(y_test),
        "train_samples": len(y_train),
        "val_samples": len(y_val),
        "test_samples": len(y_test),
        "metrics": {
            "train_accuracy": round(train_acc, 4),
            "val_accuracy": round(val_acc, 4),
            "test_accuracy": round(test_acc, 4),
            "test_f1_macro": round(test_f1_macro, 4),
        },
        "classes": classes,
        "per_class_metrics": {
            cls: {
                "precision": round(report_dict[cls]["precision"], 4),
                "recall": round(report_dict[cls]["recall"], 4),
                "f1_score": round(report_dict[cls]["f1-score"], 4),
                "support": report_dict[cls]["support"],
            }
            for cls in classes if cls in report_dict
        },
        "disclaimer": "Prototype performance measured only on synthetic development images. Not validated for real-field diagnosis or chemical treatment decisions."
    }

    with open(METADATA_SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved to: {METADATA_SAVE_PATH}")

    return pipeline, metadata


if __name__ == "__main__":
    train_model()
