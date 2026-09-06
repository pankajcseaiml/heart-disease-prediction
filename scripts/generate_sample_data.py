"""Synthetic Sample Data Generator for Heart Disease Prediction.

Generates:
1. Synthetic Chest X-ray images (PNG format) simulating normal and abnormal opacity.
2. Clinical patient test payloads covering Low, Medium, and High risk profiles.
Ensures clean-clone environments can execute full end-to-end integration tests autonomously.
"""

import json
from pathlib import Path
import numpy as np
from PIL import Image

ROOT_DIR = Path(__file__).resolve().parent.parent
SAMPLE_DIR = ROOT_DIR / "data" / "sample_data"


def generate_synthetic_xray(dest_path: Path, abnormal: bool = False) -> Path:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    # Create 224x224 grayscale synthetic X-ray representation
    arr = np.zeros((224, 224), dtype=np.uint8)
    
    # Outer ribcage/background gradient
    y, x = np.ogrid[:224, :224]
    center_y, center_x = 112, 112
    dist_from_center = np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
    base = np.clip(180 - dist_from_center * 0.8, 30, 200).astype(np.uint8)
    arr[:] = base

    # Lung field dark zones (bilateral)
    left_lung = ((x - 70) ** 2 / (35 ** 2) + (y - 110) ** 2 / (60 ** 2)) <= 1.0
    right_lung = ((x - 154) ** 2 / (35 ** 2) + (y - 110) ** 2 / (60 ** 2)) <= 1.0
    arr[left_lung] = 40
    arr[right_lung] = 40

    # Cardiac silhouette (central opacity)
    cardiac = ((x - 115) ** 2 / (30 ** 2) + (y - 130) ** 2 / (40 ** 2)) <= 1.0
    if abnormal:
        # Enlarged silhouette / central congestion
        cardiac = ((x - 118) ** 2 / (45 ** 2) + (y - 130) ** 2 / (50 ** 2)) <= 1.0
        arr[cardiac] = 220
    else:
        arr[cardiac] = 160

    img = Image.fromarray(arr, mode="L")
    img.save(dest_path, format="PNG")
    return dest_path


def generate_clinical_samples() -> Path:
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    samples = {
        "low_risk": {
            "age": 28,
            "systolic_bp": 115,
            "cholesterol": 160,
            "fasting_blood_sugar": 85,
            "ecg_abnormality": 0,
            "bmi": 21.5,
            "smoking": 0,
            "physical_inactivity": 0,
            "family_history": 0,
        },
        "medium_risk": {
            "age": 52,
            "systolic_bp": 140,
            "cholesterol": 220,
            "fasting_blood_sugar": 125,
            "ecg_abnormality": 0,
            "bmi": 28.0,
            "smoking": 1,
            "physical_inactivity": 1,
            "family_history": 0,
        },
        "high_risk": {
            "age": 68,
            "systolic_bp": 175,
            "cholesterol": 310,
            "fasting_blood_sugar": 180,
            "ecg_abnormality": 1,
            "bmi": 34.5,
            "smoking": 1,
            "physical_inactivity": 1,
            "family_history": 1,
        },
    }

    json_path = SAMPLE_DIR / "clinical_samples.json"
    json_path.write_text(json.dumps(samples, indent=2), encoding="utf-8")
    return json_path


def generate_all_samples():
    print(f"[*] Generating synthetic test fixtures in: {SAMPLE_DIR}")
    xray_normal = generate_synthetic_xray(SAMPLE_DIR / "sample_normal_xray.png", abnormal=False)
    xray_abnormal = generate_synthetic_xray(SAMPLE_DIR / "sample_abnormal_xray.png", abnormal=True)
    json_path = generate_clinical_samples()
    print(f"[+] Created synthetic normal X-ray: {xray_normal}")
    print(f"[+] Created synthetic abnormal X-ray: {xray_abnormal}")
    print(f"[+] Created clinical profiles JSON: {json_path}")


if __name__ == "__main__":
    generate_all_samples()
