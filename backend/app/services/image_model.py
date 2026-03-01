from io import BytesIO
from typing import Tuple

import numpy as np
from PIL import Image


def _to_grayscale_array(xray_bytes: bytes) -> np.ndarray:
    try:
        image = Image.open(BytesIO(xray_bytes)).convert("L").resize((224, 224))
    except Exception as exc:
        raise ValueError("Unable to decode X-ray image") from exc
    return np.asarray(image, dtype=np.float32) / 255.0


def predict_image_risk(xray_bytes: bytes) -> Tuple[float, np.ndarray]:
    image_arr = _to_grayscale_array(xray_bytes)

    # Proxy signal: lower contrast and higher central opacity trend to higher risk.
    contrast = float(image_arr.std())
    center = image_arr[72:152, 72:152].mean()
    periphery = np.concatenate(
        [
            image_arr[:40, :].ravel(),
            image_arr[-40:, :].ravel(),
            image_arr[:, :40].ravel(),
            image_arr[:, -40:].ravel(),
        ]
    ).mean()
    opacity_delta = max(0.0, float(center - periphery))

    score = 0.6 * opacity_delta + 0.4 * max(0.0, 0.25 - contrast)
    score = max(0.0, min(1.0, score * 2.0))

    return score, image_arr
