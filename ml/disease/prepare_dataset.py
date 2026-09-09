"""
Dataset Preparation & Feature Extraction Pipeline for Crop Disease Vision AI.
Generates reproducible representative leaf feature distributions for the 10 prototype classes,
applies spatial-color moments, texture gradients, and partitions into train/val/test splits.
"""

import json
import os
import sys
import numpy as np
from PIL import Image

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

IMAGE_SIZE = (128, 128)
RANDOM_SEED = 42


def extract_image_features(image_obj: Image.Image) -> np.ndarray:
    """
    Extracts spatial-color moments, HSV distributions, and texture edge features from a PIL Image.
    Returns a standardized 1D numpy array.
    """
    img = image_obj.convert("RGB").resize(IMAGE_SIZE, Image.Resampling.BILINEAR)
    arr = np.array(img, dtype=np.float32) / 255.0  # (128, 128, 3)

    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

    features = []

    # 1. Global Channel Statistics (mean, std, min, max, median, 25th, 75th percentiles)
    for ch in (r, g, b):
        features.extend([
            float(np.mean(ch)),
            float(np.std(ch)),
            float(np.min(ch)),
            float(np.max(ch)),
            float(np.median(ch)),
            float(np.percentile(ch, 25)),
            float(np.percentile(ch, 75)),
        ])

    # 2. Vegetation & Chlorophyll Indices
    # Excess Green: 2G - R - B
    exg = 2.0 * g - r - b
    features.extend([float(np.mean(exg)), float(np.std(exg)), float(np.percentile(exg, 10)), float(np.percentile(exg, 90))])

    # Normalized Difference Green-Red Index (NGRDI): (G - R) / (G + R + 1e-6)
    ngrdi = (g - r) / (g + r + 1e-6)
    features.extend([float(np.mean(ngrdi)), float(np.std(ngrdi)), float(np.percentile(ngrdi, 10)), float(np.percentile(ngrdi, 90))])

    # Chlorophyll index: G / (R + 1e-6)
    ci = g / (r + 1e-6)
    features.extend([float(np.mean(ci)), float(np.std(ci))])

    # 3. Spatial Color Grids (4x4 sub-regions for localized lesion detection)
    grid_h, grid_w = 4, 4
    h_step, w_step = 128 // grid_h, 128 // grid_w
    for i in range(grid_h):
        for j in range(grid_w):
            sub_r = r[i * h_step:(i + 1) * h_step, j * w_step:(j + 1) * w_step]
            sub_g = g[i * h_step:(i + 1) * h_step, j * w_step:(j + 1) * w_step]
            sub_b = b[i * h_step:(i + 1) * h_step, j * w_step:(j + 1) * w_step]
            sub_exg = exg[i * h_step:(i + 1) * h_step, j * w_step:(j + 1) * w_step]

            features.extend([
                float(np.mean(sub_r)),
                float(np.std(sub_r)),
                float(np.mean(sub_g)),
                float(np.std(sub_g)),
                float(np.mean(sub_b)),
                float(np.std(sub_b)),
                float(np.mean(sub_exg)),
                float(np.std(sub_exg)),
            ])

    # 4. Edge & Gradient Texture Analysis (Approximated 2D gradient magnitude)
    gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
    grad_x = np.diff(gray, axis=1)
    grad_y = np.diff(gray, axis=0)
    mag_x = np.abs(grad_x)
    mag_y = np.abs(grad_y)

    features.extend([
        float(np.mean(mag_x)),
        float(np.std(mag_x)),
        float(np.max(mag_x)),
        float(np.percentile(mag_x, 90)),
        float(np.mean(mag_y)),
        float(np.std(mag_y)),
        float(np.max(mag_y)),
        float(np.percentile(mag_y, 90)),
    ])

    # 5. Color Histogram Bins (8 bins per channel)
    hist_r, _ = np.histogram(r, bins=8, range=(0.0, 1.0), density=True)
    hist_g, _ = np.histogram(g, bins=8, range=(0.0, 1.0), density=True)
    hist_b, _ = np.histogram(b, bins=8, range=(0.0, 1.0), density=True)
    features.extend([float(v) for v in hist_r])
    features.extend([float(v) for v in hist_g])
    features.extend([float(v) for v in hist_b])

    return np.array(features, dtype=np.float32)


def generate_synthetic_leaf_sample(class_name: str, rng: np.random.RandomState) -> Image.Image:
    """
    Synthesizes a representative leaf image with class-specific spectral profiles and lesion morphology.
    Used for local reproducible prototype training and benchmark testing.
    """
    arr = np.zeros((128, 128, 3), dtype=np.float32)

    # Base leaf background color (varying shades of green)
    if "Healthy" in class_name:
        if "Tomato" in class_name:
            base_r, base_g, base_b = rng.uniform(0.12, 0.22), rng.uniform(0.55, 0.75), rng.uniform(0.10, 0.20)
        elif "Potato" in class_name:
            base_r, base_g, base_b = rng.uniform(0.14, 0.24), rng.uniform(0.50, 0.70), rng.uniform(0.12, 0.22)
        elif "Corn" in class_name:
            base_r, base_g, base_b = rng.uniform(0.18, 0.28), rng.uniform(0.60, 0.80), rng.uniform(0.15, 0.25)
        else: # Pepper
            base_r, base_g, base_b = rng.uniform(0.10, 0.20), rng.uniform(0.58, 0.78), rng.uniform(0.08, 0.18)
    else:
        # Diseased leaves have higher brown/yellow components and lower green
        if "Early_Blight" in class_name:
            base_r, base_g, base_b = rng.uniform(0.35, 0.50), rng.uniform(0.38, 0.52), rng.uniform(0.15, 0.28)
        elif "Late_Blight" in class_name:
            base_r, base_g, base_b = rng.uniform(0.22, 0.35), rng.uniform(0.25, 0.38), rng.uniform(0.18, 0.30)
        elif "Leaf_Mold" in class_name:
            base_r, base_g, base_b = rng.uniform(0.40, 0.55), rng.uniform(0.45, 0.60), rng.uniform(0.12, 0.25)
        elif "Common_Rust" in class_name:
            base_r, base_g, base_b = rng.uniform(0.48, 0.65), rng.uniform(0.32, 0.45), rng.uniform(0.10, 0.22)
        else:
            base_r, base_g, base_b = rng.uniform(0.30, 0.45), rng.uniform(0.40, 0.55), rng.uniform(0.15, 0.25)

    arr[:, :, 0] = base_r + rng.normal(0, 0.03, (128, 128))
    arr[:, :, 1] = base_g + rng.normal(0, 0.03, (128, 128))
    arr[:, :, 2] = base_b + rng.normal(0, 0.03, (128, 128))

    # Add disease-specific lesion spots
    if "Early_Blight" in class_name:
        # Concentric dark brown spots with yellow halos
        num_lesions = rng.randint(3, 8)
        for _ in range(num_lesions):
            cx, cy = rng.randint(20, 108), rng.randint(20, 108)
            radius = rng.randint(8, 18)
            y, x = np.ogrid[:128, :128]
            dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            # Halo (yellow)
            halo_mask = (dist >= radius * 0.7) & (dist <= radius * 1.3)
            arr[halo_mask, 0] = np.clip(arr[halo_mask, 0] + 0.3, 0, 1)
            arr[halo_mask, 1] = np.clip(arr[halo_mask, 1] + 0.25, 0, 1)
            # Core (dark brown)
            core_mask = dist < radius * 0.7
            arr[core_mask, 0] = 0.25 + rng.uniform(-0.05, 0.05)
            arr[core_mask, 1] = 0.15 + rng.uniform(-0.03, 0.03)
            arr[core_mask, 2] = 0.08 + rng.uniform(-0.02, 0.02)

    elif "Late_Blight" in class_name:
        # Irregular water-soaked dark patches
        num_patches = rng.randint(2, 6)
        for _ in range(num_patches):
            cx, cy = rng.randint(15, 110), rng.randint(15, 110)
            radius = rng.randint(12, 26)
            y, x = np.ogrid[:128, :128]
            dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            mask = dist < radius
            arr[mask, 0] = 0.18 + rng.uniform(-0.04, 0.04)
            arr[mask, 1] = 0.20 + rng.uniform(-0.04, 0.04)
            arr[mask, 2] = 0.15 + rng.uniform(-0.03, 0.03)

    elif "Common_Rust" in class_name:
        # Multiple small reddish-cinnamon pustules
        num_pustules = rng.randint(20, 50)
        for _ in range(num_pustules):
            cx, cy = rng.randint(10, 118), rng.randint(10, 118)
            radius = rng.randint(2, 5)
            y, x = np.ogrid[:128, :128]
            dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            mask = dist < radius
            arr[mask, 0] = 0.72 + rng.uniform(-0.08, 0.08)
            arr[mask, 1] = 0.30 + rng.uniform(-0.05, 0.05)
            arr[mask, 2] = 0.08 + rng.uniform(-0.03, 0.03)

    elif "Leaf_Mold" in class_name:
        # Diffuse olive-yellow velvety patches
        num_spots = rng.randint(4, 10)
        for _ in range(num_spots):
            cx, cy = rng.randint(15, 110), rng.randint(15, 110)
            radius = rng.randint(10, 20)
            y, x = np.ogrid[:128, :128]
            dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            mask = dist < radius
            arr[mask, 0] = np.clip(arr[mask, 0] + 0.25, 0, 1)
            arr[mask, 1] = np.clip(arr[mask, 1] + 0.15, 0, 1)
            arr[mask, 2] = np.clip(arr[mask, 2] - 0.05, 0, 1)

    arr = np.clip(arr * 255.0, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGB")


def prepare_dataset_splits(samples_per_class: int = 120):
    """
    Generates feature matrices and labels partitioned into deterministic 80/10/10 splits.
    """
    meta_path = os.path.join(os.path.dirname(__file__), "disease_metadata.json")
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    classes = meta["classes"]
    rng = np.random.RandomState(RANDOM_SEED)

    X_list = []
    y_list = []

    print(f"Generating feature dataset across {len(classes)} classes ({samples_per_class} samples/class)...")

    for class_idx, class_name in enumerate(classes):
        for _ in range(samples_per_class):
            img = generate_synthetic_leaf_sample(class_name, rng)
            feats = extract_image_features(img)
            X_list.append(feats)
            y_list.append(class_idx)

    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.int64)

    # Shuffle indices
    indices = np.arange(len(y))
    rng.shuffle(indices)
    X, y = X[indices], y[indices]

    # Split: 80% train, 10% val, 10% test
    n_total = len(y)
    n_train = int(n_total * 0.8)
    n_val = int(n_total * 0.1)

    X_train, y_train = X[:n_train], y[:n_train]
    X_val, y_val = X[n_train:n_train + n_val], y[n_train:n_train + n_val]
    X_test, y_test = X[n_train + n_val:], y[n_train + n_val:]

    print(f"Dataset split complete: Train={len(y_train)}, Val={len(y_val)}, Test={len(y_test)} (Total={n_total})")
    print(f"Feature vector dimensionality: {X.shape[1]}")

    return X_train, y_train, X_val, y_val, X_test, y_test, classes


if __name__ == "__main__":
    prepare_dataset_splits()
