from typing import Dict, List

from pydantic import BaseModel, Field


class FeatureImportance(BaseModel):
    feature: str
    contribution: float


class PredictionResponse(BaseModel):
    risk_percentage: float = Field(..., ge=0, le=100)
    risk_category: str
    confidence: float = Field(..., ge=0, le=1)
    feature_importance: List[FeatureImportance]
    clinical_score: float = Field(..., ge=0, le=1)
    image_score: float = Field(..., ge=0, le=1)
    fusion_score: float = Field(..., ge=0, le=1)
    explanation: str
    heatmap_image_base64: str
    normalized_inputs: Dict[str, float]
