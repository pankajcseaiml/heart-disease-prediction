from app.schemas.predict import FeatureImportance, PredictionResponse
from app.services.clinical_model import predict_clinical_risk
from app.services.explainer import build_explanation_text, build_heatmap_overlay
from app.services.fusion_model import fuse_scores, to_confidence, to_risk_category
from app.services.image_model import predict_image_risk
from app.services.preprocess import parse_and_normalize_clinical_data


def run_prediction(xray_bytes: bytes, clinical_json: str) -> PredictionResponse:
    normalized_inputs = parse_and_normalize_clinical_data(clinical_json)
    clinical_score, contributions = predict_clinical_risk(normalized_inputs)
    image_score, gray_image = predict_image_risk(xray_bytes)

    fusion_score = fuse_scores(clinical_score=clinical_score, image_score=image_score)
    risk_category = to_risk_category(fusion_score)
    confidence = to_confidence(fusion_score)

    top_importance = [
        FeatureImportance(feature=feature, contribution=round(contribution, 4))
        for feature, contribution in contributions[:5]
    ]

    explanation = build_explanation_text(
        risk_category=risk_category,
        top_features=[item.feature for item in top_importance],
        image_score=image_score,
    )

    return PredictionResponse(
        risk_percentage=round(fusion_score * 100, 2),
        risk_category=risk_category,
        confidence=round(confidence, 3),
        feature_importance=top_importance,
        clinical_score=round(clinical_score, 4),
        image_score=round(image_score, 4),
        fusion_score=round(fusion_score, 4),
        explanation=explanation,
        heatmap_image_base64=build_heatmap_overlay(gray_image),
        normalized_inputs={k: round(v, 4) for k, v in normalized_inputs.items()},
    )
