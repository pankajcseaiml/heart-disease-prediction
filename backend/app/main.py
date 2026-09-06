import os
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, File, Form, Header, HTTPException, Security, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from app.db.models import get_recent_predictions, init_tables, save_prediction
from app.db.session import get_connection, get_db
from app.schemas.predict import PredictionResponse
from app.services.pipeline import run_prediction

app = FastAPI(
    title="Heart Disease Early Risk Prediction API",
    version="1.0.0",
    description="Multimodal (X-ray + clinical) explainable heart disease risk API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    with get_connection() as conn:
        init_tables(conn)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "heart-disease-prediction-api"}


@app.post("/predict", response_model=PredictionResponse)
async def predict(
    xray: UploadFile = File(...),
    clinical_data: str = Form(...),
) -> PredictionResponse:
    try:
        response = run_prediction(xray_bytes=await xray.read(), clinical_json=clinical_data)
        
        # Persist prediction to database
        try:
            with get_db() as conn:
                save_prediction(
                    conn=conn,
                    risk_percentage=response.risk_percentage,
                    risk_category=response.risk_category,
                    confidence=response.confidence,
                    clinical_score=response.clinical_score,
                    image_score=response.image_score,
                    fusion_score=response.fusion_score,
                    explanation=response.explanation,
                    normalized_inputs=response.normalized_inputs,
                    feature_importance=[item.model_dump() for item in response.feature_importance],
                )
        except Exception as db_err:
            # Non-fatal log so prediction still returns if DB write fails
            print(f"[!] Warning: Failed to persist prediction record to DB: {db_err}")

        return response
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal error: {exc}") from exc


@app.get("/history")
def history(limit: int = 20) -> List[Dict[str, Any]]:
    """Retrieve recent predictions from the database."""
    try:
        with get_connection() as conn:
            return get_recent_predictions(conn=conn, limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

