from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/predict", response_model=PredictionResponse)
async def predict(
    xray: UploadFile = File(...),
    clinical_data: str = Form(...),
) -> PredictionResponse:
    try:
        return run_prediction(xray_bytes=await xray.read(), clinical_json=clinical_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal error: {exc}") from exc
