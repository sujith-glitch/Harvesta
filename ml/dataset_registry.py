"""Load and validate the small, provenance-tracked development datasets."""
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "manifests" / "datasets.json"

def _manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))

def load_dataset(name: str) -> pd.DataFrame:
    entry = _manifest().get(name)
    if not entry:
        raise KeyError(f"Unknown dataset: {name}")
    frame = pd.read_csv(ROOT / entry["file"])
    errors = validate_dataset(name, frame)
    if errors:
        raise ValueError("; ".join(errors))
    return frame

def validate_dataset(name: str, frame: pd.DataFrame) -> list[str]:
    entry = _manifest().get(name)
    if not entry:
        return [f"Unknown dataset: {name}"]
    errors = []
    missing = [field for field in entry["fields"] if field not in frame.columns]
    if missing:
        errors.append(f"missing columns: {', '.join(missing)}")
    if frame.empty:
        errors.append("dataset is empty")
    if frame.isna().any().any():
        errors.append("dataset contains missing values")
    return errors
