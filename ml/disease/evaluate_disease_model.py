"""
Model Evaluation Script for Crop Disease Vision AI.
Loads trained model artifact, evaluates on held-out test splits,
and reports confusion matrix and confidence metrics.
"""

import json
import os
import sys
import joblib
import numpy as np
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from ml.disease.prepare_dataset import prepare_dataset_splits

MODEL_SAVE_PATH = os.path.join(WORKSPACE_ROOT, "ml", "models", "crop_disease_model.joblib")
METADATA_SAVE_PATH = os.path.join(WORKSPACE_ROOT, "ml", "models", "crop_disease_metadata.json")


def evaluate():
    if not os.path.exists(MODEL_SAVE_PATH):
        print(f"Error: Model not found at {MODEL_SAVE_PATH}. Run train_disease_model.py first.")
        return

    print("Loading model and metadata...")
    model = joblib.load(MODEL_SAVE_PATH)
    with open(METADATA_SAVE_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)

    _, _, _, _, X_test, y_test, classes = prepare_dataset_splits(samples_per_class=120)

    preds = model.predict(X_test)
    probas = model.predict_proba(X_test)

    acc = accuracy_score(y_test, preds)
    confidences = np.max(probas, axis=1)

    print("\n=======================================================")
    print(f"Model Version:          {meta['model_version']}")
    print(f"Test Accuracy:          {acc * 100:.2f}%")
    print(f"Mean Prediction Conf.:  {np.mean(confidences) * 100:.2f}%")
    print(f"Min Prediction Conf.:   {np.min(confidences) * 100:.2f}%")
    print("=======================================================\n")

    print("Classification Report:")
    print(classification_report(y_test, preds, target_names=classes))

    print("\nConfusion Matrix:")
    cm = confusion_matrix(y_test, preds)
    print(cm)

    return acc, cm


if __name__ == "__main__":
    evaluate()
