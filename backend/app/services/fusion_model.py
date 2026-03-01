def fuse_scores(clinical_score: float, image_score: float) -> float:
    # Slightly prioritize clinical data in this baseline implementation.
    score = (0.58 * clinical_score) + (0.42 * image_score)
    return max(0.0, min(1.0, score))


def to_risk_category(fusion_score: float) -> str:
    if fusion_score < 0.33:
        return "Low"
    if fusion_score < 0.66:
        return "Medium"
    return "High"


def to_confidence(fusion_score: float) -> float:
    # Confidence increases with distance from decision center.
    distance = abs(fusion_score - 0.5)
    return min(0.98, 0.5 + distance)
