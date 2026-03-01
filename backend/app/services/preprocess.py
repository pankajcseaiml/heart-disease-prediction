import json
from typing import Dict

REQUIRED_FIELDS = [
    "age",
    "systolic_bp",
    "cholesterol",
    "fasting_blood_sugar",
    "ecg_abnormality",
    "bmi",
    "smoking",
    "physical_inactivity",
    "family_history",
]


RANGES = {
    "age": (18, 100),
    "systolic_bp": (80, 220),
    "cholesterol": (100, 400),
    "fasting_blood_sugar": (70, 250),
    "ecg_abnormality": (0, 1),
    "bmi": (12, 60),
    "smoking": (0, 1),
    "physical_inactivity": (0, 1),
    "family_history": (0, 1),
}


def parse_and_normalize_clinical_data(clinical_json: str) -> Dict[str, float]:
    try:
        raw = json.loads(clinical_json)
    except json.JSONDecodeError as exc:
        raise ValueError("clinical_data must be valid JSON") from exc

    missing = [field for field in REQUIRED_FIELDS if field not in raw]
    if missing:
        raise ValueError(f"Missing required clinical fields: {', '.join(missing)}")

    normalized: Dict[str, float] = {}
    for field, (min_v, max_v) in RANGES.items():
        value = float(raw[field])
        if value < min_v or value > max_v:
            raise ValueError(f"{field} must be between {min_v} and {max_v}")
        normalized[field] = (value - min_v) / (max_v - min_v)

    return normalized
