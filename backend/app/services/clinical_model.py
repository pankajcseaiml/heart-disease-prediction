from typing import Dict, List, Tuple

# Higher values increase risk.
WEIGHTS = {
    "age": 0.12,
    "systolic_bp": 0.14,
    "cholesterol": 0.12,
    "fasting_blood_sugar": 0.1,
    "ecg_abnormality": 0.15,
    "bmi": 0.1,
    "smoking": 0.1,
    "physical_inactivity": 0.09,
    "family_history": 0.08,
}


def predict_clinical_risk(normalized_inputs: Dict[str, float]) -> Tuple[float, List[Tuple[str, float]]]:
    score = 0.0
    contributions: List[Tuple[str, float]] = []

    for feature, weight in WEIGHTS.items():
        contribution = normalized_inputs[feature] * weight
        score += contribution
        contributions.append((feature, contribution))

    score = max(0.0, min(1.0, score))
    contributions.sort(key=lambda x: x[1], reverse=True)
    return score, contributions
