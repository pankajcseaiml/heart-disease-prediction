# Heart Disease Early Risk Prediction (End-to-End)

This project is a multimodal AI-style decision support system that combines:
- Chest X-ray image analysis
- Clinical data analysis

It returns:
- Risk percentage
- Risk category (Low/Medium/High)
- Highlighted X-ray
- Top feature importance
- Human-readable explanation

## Architecture
- `backend/`: FastAPI API for prediction pipeline
- `frontend/`: Streamlit web app

## 1) Run Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check:
```powershell
curl http://127.0.0.1:8000/health
```

## 2) Run Frontend

Open a second terminal:

```powershell
cd frontend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Then open the URL shown by Streamlit (usually `http://localhost:8501`).

## API Contract
`POST /predict` multipart form data:
- `xray`: image file (`png/jpg/jpeg`)
- `clinical_data`: JSON string containing:
  - `age`
  - `systolic_bp`
  - `cholesterol`
  - `fasting_blood_sugar`
  - `ecg_abnormality` (0/1)
  - `bmi`
  - `smoking` (0/1)
  - `physical_inactivity` (0/1)
  - `family_history` (0/1)

## Important Note
This baseline implementation provides a **workable full-stack prototype** for demonstration and integration.
It is not a medical-grade diagnostic model and must be clinically validated before real use.
