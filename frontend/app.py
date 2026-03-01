import base64
import json
from io import BytesIO

import pandas as pd
import requests
import streamlit as st
from PIL import Image

API_URL = st.sidebar.text_input("Backend API URL", value="http://127.0.0.1:8000")

st.set_page_config(page_title="Heart Disease Risk Predictor", layout="wide")
st.title("AI Heart Disease Early Risk Prediction")
st.caption("Clinical decision support only. Not a standalone diagnosis.")

with st.form("prediction_form"):
    st.subheader("Patient Clinical Inputs")
    col1, col2, col3 = st.columns(3)

    with col1:
        age = st.number_input("Age", 18, 100, 45)
        systolic_bp = st.number_input("Systolic BP", 80, 220, 130)
        cholesterol = st.number_input("Cholesterol", 100, 400, 200)

    with col2:
        fasting_blood_sugar = st.number_input("Fasting Blood Sugar", 70, 250, 110)
        ecg_abnormality = st.selectbox("ECG Abnormality", [0, 1], format_func=lambda x: "Yes" if x else "No")
        bmi = st.number_input("BMI", 12.0, 60.0, 25.0)

    with col3:
        smoking = st.selectbox("Smoking", [0, 1], format_func=lambda x: "Yes" if x else "No")
        physical_inactivity = st.selectbox("Physical Inactivity", [0, 1], format_func=lambda x: "Yes" if x else "No")
        family_history = st.selectbox("Family History", [0, 1], format_func=lambda x: "Yes" if x else "No")

    st.subheader("Chest X-ray")
    xray_file = st.file_uploader("Upload X-ray image", type=["png", "jpg", "jpeg"])

    submitted = st.form_submit_button("Predict Risk")

if submitted:
    if not xray_file:
        st.error("Please upload a chest X-ray image.")
    else:
        clinical_data = {
            "age": age,
            "systolic_bp": systolic_bp,
            "cholesterol": cholesterol,
            "fasting_blood_sugar": fasting_blood_sugar,
            "ecg_abnormality": ecg_abnormality,
            "bmi": bmi,
            "smoking": smoking,
            "physical_inactivity": physical_inactivity,
            "family_history": family_history,
        }

        files = {"xray": (xray_file.name, xray_file.getvalue(), xray_file.type or "image/png")}
        data = {"clinical_data": json.dumps(clinical_data)}

        try:
            response = requests.post(f"{API_URL}/predict", files=files, data=data, timeout=30)
            response.raise_for_status()
            result = response.json()
        except requests.RequestException as exc:
            st.error(f"Failed to call backend API: {exc}")
            st.stop()

        st.success("Prediction completed")

        k1, k2, k3 = st.columns(3)
        k1.metric("Risk", f"{result['risk_percentage']}%")
        k2.metric("Category", result["risk_category"])
        k3.metric("Confidence", result["confidence"])

        st.write(result["explanation"])

        left, right = st.columns(2)

        with left:
            st.subheader("Original X-ray")
            st.image(Image.open(BytesIO(xray_file.getvalue())), use_container_width=True)

        with right:
            st.subheader("Highlighted X-ray")
            overlay_bytes = base64.b64decode(result["heatmap_image_base64"])
            st.image(Image.open(BytesIO(overlay_bytes)), use_container_width=True)

        st.subheader("Top Clinical Feature Importance")
        importance_df = pd.DataFrame(result["feature_importance"])
        st.bar_chart(importance_df.set_index("feature"))

        st.subheader("Model Component Scores")
        component_df = pd.DataFrame(
            {
                "component": ["Clinical", "X-ray", "Fusion"],
                "score": [result["clinical_score"], result["image_score"], result["fusion_score"]],
            }
        )
        st.bar_chart(component_df.set_index("component"))
