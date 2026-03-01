import base64
from io import BytesIO

import numpy as np
from PIL import Image


def build_heatmap_overlay(gray_image: np.ndarray) -> str:
    # Simple intensity-based saliency proxy for explainable visualization.
    centered = gray_image - gray_image.mean()
    positive = np.clip(centered, 0, None)
    if positive.max() > 0:
        positive = positive / positive.max()

    base_rgb = np.stack([gray_image, gray_image, gray_image], axis=-1)
    heat = np.zeros_like(base_rgb)
    heat[..., 0] = positive  # red channel highlight

    overlay = np.clip((0.75 * base_rgb) + (0.55 * heat), 0, 1)
    overlay_img = Image.fromarray((overlay * 255).astype(np.uint8))

    buffer = BytesIO()
    overlay_img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def build_explanation_text(risk_category: str, top_features: list[str], image_score: float) -> str:
    features_text = ", ".join(top_features[:3]) if top_features else "clinical indicators"
    image_phrase = "moderate" if image_score < 0.66 else "strong"
    return (
        f"Predicted {risk_category} risk. Key drivers: {features_text}. "
        f"X-ray analysis contributed {image_phrase} evidence to the final risk estimate."
    )
