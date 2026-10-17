"""
VitaVerse - Local Python API Backend
====================================
Project: VitaVerse — AI-Driven Personalized Virtual Reality for Comfort and Distraction in Palliative Care
Phase: Phase 1 Prototype

FastAPI service providing real-time comfort classification and scene mapping for the Unity VR client.
Runs strictly on localhost (127.0.0.1:8000) using local machine-learning inference.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field, field_validator
import pandas as pd
import joblib

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "ml", "comfort_model.joblib")
METADATA_PATH = os.path.join(BASE_DIR, "ml", "model_metadata.json")

# Mapping from ML comfort classification to Unity scene preset
CLASS_TO_SCENE_MAP = {
    "calm": "Pool",
    "adjust": "Beach",
    "support": "Home"
}

SCENE_DESCRIPTIONS = {
    "Pool": "Tranquil Pool - Soothing crystal azure waters, gentle ripple reflections, open daylight ambiance.",
    "Beach": "Umhlanga Beach Sunrise - Coastal ocean waves, golden sunrise horizon, refreshing coastal breeze.",
    "Home": "Kerala Heritage Home - Authentic teakwood architecture, courtyard natural daylight, tranquil grounded shelter."
}

# In-memory model and metadata storage
app_state = {
    "model": None,
    "metadata": None,
    "is_ready": False,
    "startup_time": None
}

def load_model_and_metadata():
    """Load machine learning model and metadata into memory."""
    if app_state["model"] is not None and app_state["metadata"] is not None:
        return

    app_state["startup_time"] = datetime.now().isoformat()
    if os.path.exists(MODEL_PATH):
        try:
            app_state["model"] = joblib.load(MODEL_PATH)
            print(f"[Backend] Loaded trained ML model from: {MODEL_PATH}")
        except Exception as e:
            print(f"[Backend ERROR] Failed to load model file: {e}")
            app_state["model"] = None
    else:
        print(f"[Backend WARNING] Model file not found at: {MODEL_PATH}")
        app_state["model"] = None

    if os.path.exists(METADATA_PATH):
        try:
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                app_state["metadata"] = json.load(f)
            print(f"[Backend] Loaded model metadata from: {METADATA_PATH}")
        except Exception as e:
            print(f"[Backend WARNING] Failed to read metadata: {e}")
            app_state["metadata"] = None

    app_state["is_ready"] = (app_state["model"] is not None)

# Eager load on module initialization
load_model_and_metadata()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure model and metadata are ready on server startup."""
    print("[Backend] Initializing VitaVerse Local API...")
    load_model_and_metadata()
    yield
    print("[Backend] Shutting down VitaVerse Local API...")

app = FastAPI(
    title="VitaVerse Local API",
    description="Local AI inference backend for Comfort Classification in Palliative VR",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Unity Editor, WebGL, and local testing clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# Request & Response Schemas
# ---------------------------------------------------------

class PatientInput(BaseModel):
    spo2: float = Field(
        ...,
        description="Oxygen saturation percentage (%): 70.0 - 100.0",
        examples=[98.0]
    )
    hr: float = Field(
        ...,
        description="Heart rate in beats per minute (bpm): 30.0 - 220.0",
        examples=[72.0]
    )
    hrv: float = Field(
        ...,
        description="Heart rate variability in milliseconds (ms): 1.0 - 250.0",
        examples=[65.0]
    )

    @field_validator("spo2")
    @classmethod
    def validate_spo2(cls, v: float) -> float:
        if v < 70.0 or v > 100.0:
            raise ValueError(f"SpO2 value ({v}%) out of physiological bounds [70.0, 100.0].")
        return round(float(v), 2)

    @field_validator("hr")
    @classmethod
    def validate_hr(cls, v: float) -> float:
        if v < 30.0 or v > 220.0:
            raise ValueError(f"Heart rate value ({v} bpm) out of physiological bounds [30.0, 220.0].")
        return round(float(v), 2)

    @field_validator("hrv")
    @classmethod
    def validate_hrv(cls, v: float) -> float:
        if v < 1.0 or v > 250.0:
            raise ValueError(f"HRV value ({v} ms) out of physiological bounds [1.0, 250.0].")
        return round(float(v), 2)

class PredictionResponse(BaseModel):
    comfort_class: str
    scene: str
    scene_description: str
    confidence: float
    probabilities: Dict[str, float]
    demo_only: bool = True
    message: str
    safety_advisory: Optional[str] = None
    timestamp: str

# ---------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------

@app.get("/", summary="API Root & Status")
async def root():
    """Returns basic service information and endpoint links."""
    return {
        "project": "VitaVerse — AI-Driven Personalized VR for Comfort in Palliative Care",
        "phase": "Phase 1: AI-Based Comfort Classification and Static VR Environment",
        "status": "online",
        "model_loaded": app_state["model"] is not None,
        "docs_url": "/docs",
        "demo_dashboard_url": "/demo",
        "endpoints": {
            "health": "/health",
            "predict": "/predict (POST)",
            "scenarios": "/scenarios (GET)",
            "metadata": "/metadata (GET)"
        },
        "disclaimer": "Academic research prototype. Synthetic demonstration model only."
    }

@app.get("/health", summary="Readiness & Health Check")
async def health_check():
    """Readiness endpoint to verify model status."""
    if not app_state["is_ready"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not loaded. Run train_model.py to generate comfort_model.joblib."
        )
    return {
        "status": "healthy",
        "model_loaded": True,
        "model_type": "RandomForestClassifier",
        "features": ["spo2", "hr", "hrv"],
        "classes": list(CLASS_TO_SCENE_MAP.keys()),
        "startup_time": app_state["startup_time"]
    }

@app.get("/metadata", summary="Model Training Metadata")
async def get_metadata():
    """Returns detailed training metadata and performance metrics."""
    if app_state["metadata"] is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model metadata file not found. Run train_model.py first."
        )
    return app_state["metadata"]

@app.get("/scenarios", summary="Simulated Demonstration Scenarios")
async def get_scenarios():
    """Returns preset simulated patient profiles for easy demonstration."""
    return {
        "disclaimer": "Simulated demonstration scenarios. Not actual patient records.",
        "scenarios": [
            {
                "id": "scenario_calm",
                "title": "Scenario 1: Stable & Relaxed",
                "spo2": 98.0,
                "hr": 68.0,
                "hrv": 75.0,
                "expected_class": "calm",
                "expected_scene": "Pool",
                "notes": "Optimal SpO2, relaxed resting heart rate, high heart rate variability. Mapped to Tranquil Pool."
            },
            {
                "id": "scenario_adjust",
                "title": "Scenario 2: Mild Physiological Fluctuation",
                "spo2": 94.5,
                "hr": 88.0,
                "hrv": 38.0,
                "expected_class": "adjust",
                "expected_scene": "Beach",
                "notes": "Mild autonomic arousal or restlessness; moderate HRV shift. Mapped to Umhlanga Beach Sunrise."
            },
            {
                "id": "scenario_support",
                "title": "Scenario 3: Elevated Stress / Sensory Support Needed",
                "spo2": 91.0,
                "hr": 112.0,
                "hrv": 19.0,
                "expected_class": "support",
                "expected_scene": "Home",
                "notes": "Low HRV, elevated heart rate, borderline SpO2 requiring quiet low-stimulation Kerala Heritage Home."
            }
        ]
    }

@app.post("/predict", response_model=PredictionResponse, summary="Predict Comfort Level and Map VR Scene")
async def predict_comfort(payload: PatientInput):
    """
    Accepts patient physiological readings (SpO2, HR, HRV),
    executes Scikit-learn classification, and maps output to a calming Unity environment.
    """
    if app_state["model"] is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model file not loaded. Please verify ml/comfort_model.joblib exists."
        )

    # Prepare DataFrame for scikit-learn
    input_df = pd.DataFrame([{
        "spo2": payload.spo2,
        "hr": payload.hr,
        "hrv": payload.hrv
    }])

    try:
        model = app_state["model"]
        prediction = model.predict(input_df)[0]
        probabilities = model.predict_proba(input_df)[0]
        class_prob_map = {
            str(cls_name): round(float(prob), 4)
            for cls_name, prob in zip(model.classes_, probabilities)
        }
        confidence = round(float(max(probabilities)), 4)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error during model execution: {str(e)}"
        )

    scene = CLASS_TO_SCENE_MAP.get(prediction, "Pool")
    scene_desc = SCENE_DESCRIPTIONS.get(scene, "Static calming environment.")

    # Physiological safety assessment (independent of AI classification)
    safety_advisory = None
    if payload.spo2 < 92.0:
        safety_advisory = (
            f"SAFETY ALERT: SpO2 reading ({payload.spo2}%) is below 92%. "
            "Prompt clinical evaluation by palliative healthcare staff is recommended."
        )
    elif payload.hr > 120.0 or payload.hr < 45.0:
        safety_advisory = (
            f"SAFETY ALERT: Heart rate ({payload.hr} bpm) is outside customary resting limits. "
            "Verify patient vital signs with primary medical staff."
        )

    return PredictionResponse(
        comfort_class=prediction,
        scene=scene,
        scene_description=scene_desc,
        confidence=confidence,
        probabilities=class_prob_map,
        demo_only=True,
        message="Experimental prediction using synthetic demonstration data.",
        safety_advisory=safety_advisory,
        timestamp=datetime.now().isoformat()
    )

# ---------------------------------------------------------
# Optional Local Web Test Dashboard
# ---------------------------------------------------------

@app.get("/demo", response_class=HTMLResponse, summary="Interactive Web Test Dashboard")
async def demo_dashboard():
    """Serves a local testing dashboard to demonstrate API & environment switching."""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>VitaVerse — Phase 1 Test Dashboard</title>
  <style>
    :root {
      --bg-dark: #0f172a;
      --card-bg: rgba(30, 41, 59, 0.85);
      --border-color: rgba(255, 255, 255, 0.1);
      --accent-calm: #10b981;
      --accent-adjust: #0284c7;
      --accent-support: #f59e0b;
      --accent-danger: #ef4444;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body {
      background: radial-gradient(circle at 50% 20%, #1e293b 0%, #090d16 100%);
      color: var(--text-main);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 30px 15px;
    }
    .container { max-width: 960px; width: 100%; }
    .header { text-align: center; margin-bottom: 25px; }
    .header h1 { font-size: 2rem; font-weight: 700; letter-spacing: -0.5px; background: linear-gradient(135deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .header p { color: var(--text-muted); font-size: 0.95rem; margin-top: 6px; }
    .disclaimer-banner {
      background: rgba(245, 158, 11, 0.15);
      border: 1px solid rgba(245, 158, 11, 0.4);
      border-radius: 8px;
      padding: 10px 16px;
      color: #fde68a;
      font-size: 0.85rem;
      margin-bottom: 25px;
      text-align: center;
    }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
    @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
    .card {
      background: var(--card-bg);
      backdrop-filter: blur(12px);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 24px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
    }
    .card h2 { font-size: 1.25rem; margin-bottom: 16px; color: #e2e8f0; display: flex; align-items: center; justify-content: space-between; }
    .status-badge {
      font-size: 0.75rem;
      padding: 3px 10px;
      border-radius: 12px;
      background: rgba(16, 185, 129, 0.2);
      color: #34d399;
      border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .field-group { margin-bottom: 16px; }
    .field-group label { display: flex; justify-content: space-between; font-size: 0.88rem; color: var(--text-muted); margin-bottom: 6px; }
    .field-group .val { color: #38bdf8; font-weight: 600; }
    .field-group input[type="range"] {
      width: 100%;
      height: 6px;
      border-radius: 4px;
      background: #334155;
      outline: none;
      accent-color: #38bdf8;
    }
    .field-group input[type="number"] {
      width: 100%;
      padding: 8px 12px;
      background: #1e293b;
      border: 1px solid #475569;
      border-radius: 6px;
      color: #fff;
      font-size: 0.95rem;
    }
    .btn-row { display: flex; gap: 10px; margin-top: 15px; }
    button {
      flex: 1;
      padding: 10px 16px;
      border: none;
      border-radius: 8px;
      font-weight: 600;
      font-size: 0.9rem;
      cursor: pointer;
      transition: all 0.2s;
    }
    .btn-primary { background: linear-gradient(135deg, #0284c7, #2563eb); color: white; }
    .btn-primary:hover { opacity: 0.9; transform: translateY(-1px); }
    .btn-secondary { background: #334155; color: #cbd5e1; }
    .btn-secondary:hover { background: #475569; }
    .scenarios-box { margin-top: 16px; padding-top: 16px; border-top: 1px solid #334155; }
    .scenarios-box p { font-size: 0.8rem; color: var(--text-muted); margin-bottom: 8px; }
    .scenario-btn {
      width: 100%;
      text-align: left;
      padding: 8px 12px;
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 6px;
      color: #cbd5e1;
      font-size: 0.82rem;
      margin-bottom: 6px;
      cursor: pointer;
    }
    .scenario-btn:hover { border-color: #38bdf8; color: #fff; }
    
    /* Result preview card */
    .result-display {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 20px;
      border-radius: 10px;
      margin-bottom: 16px;
      transition: background 0.4s ease;
      text-align: center;
    }
    .result-display.calm { background: linear-gradient(135deg, rgba(16,185,129,0.2), rgba(6,78,59,0.3)); border: 1px solid rgba(16,185,129,0.4); }
    .result-display.adjust { background: linear-gradient(135deg, rgba(2,132,199,0.2), rgba(12,74,110,0.3)); border: 1px solid rgba(2,132,199,0.4); }
    .result-display.support { background: linear-gradient(135deg, rgba(245,158,11,0.2), rgba(120,53,15,0.3)); border: 1px solid rgba(245,158,11,0.4); }
    
    .comfort-badge { font-size: 1.6rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
    .scene-name { font-size: 1.1rem; color: #93c5fd; font-weight: 600; }
    .confidence { font-size: 0.85rem; color: var(--text-muted); margin-top: 6px; }
    
    .scene-preview-box {
      height: 140px;
      border-radius: 8px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      position: relative;
      overflow: hidden;
      border: 1px solid var(--border-color);
      margin-bottom: 16px;
      transition: all 0.4s ease;
    }
    .scene-preview-box.Pool {
      background: linear-gradient(180deg, #38bdf8 0%, #0284c7 60%, #0369a1 100%);
      color: #f0f9ff;
    }
    .scene-preview-box.Beach {
      background: linear-gradient(180deg, #fed7aa 0%, #fb923c 40%, #0284c7 100%);
      color: #fff;
    }
    .scene-preview-box.Home {
      background: linear-gradient(180deg, #d97706 0%, #92400e 40%, #451a03 100%);
      color: #fef3c7;
    }
    .safety-alert {
      background: rgba(239, 68, 68, 0.2);
      border: 1px solid rgba(239, 68, 68, 0.5);
      color: #fca5a5;
      padding: 10px 14px;
      border-radius: 8px;
      font-size: 0.85rem;
      margin-top: 12px;
      display: none;
    }
    .footer { text-align: center; color: var(--text-muted); font-size: 0.8rem; margin-top: 30px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>VitaVerse — Comfort Classifier</h1>
      <p>AI-Driven VR Comfort Classification in Palliative Care (Phase 1 Local Test Console)</p>
    </div>

    <div class="disclaimer-banner">
      <strong>RESEARCH PROTOTYPE NOTICE:</strong> Synthetic demonstration model only. Not calibrated for medical diagnosis or clinical care decisions.
    </div>

    <div class="grid">
      <!-- Input Panel -->
      <div class="card">
        <h2>
          <span>Patient Parameters</span>
          <span class="status-badge" id="apiStatus">API Online</span>
        </h2>

        <div class="field-group">
          <label>SpO₂ Oxygen Saturation (%): <span class="val" id="spo2Val">98.0</span></label>
          <input type="range" id="spo2" min="70" max="100" step="0.5" value="98.0" oninput="updateVal('spo2')">
        </div>

        <div class="field-group">
          <label>Heart Rate (BPM): <span class="val" id="hrVal">72.0</span></label>
          <input type="range" id="hr" min="40" max="180" step="1" value="72.0" oninput="updateVal('hr')">
        </div>

        <div class="field-group">
          <label>Heart Rate Variability - HRV (ms): <span class="val" id="hrvVal">65.0</span></label>
          <input type="range" id="hrv" min="5" max="180" step="1" value="65.0" oninput="updateVal('hrv')">
        </div>

        <div class="btn-row">
          <button class="btn-primary" onclick="predictComfort()">Predict Comfort Level</button>
          <button class="btn-secondary" onclick="resetForm()">Reset</button>
        </div>

        <div class="scenarios-box">
          <p>Quick Test Scenarios (Simulated):</p>
          <button class="scenario-btn" onclick="loadScenario(98, 68, 75)">Scenario 1: Calm Patient (SpO₂: 98%, HR: 68, HRV: 75ms)</button>
          <button class="scenario-btn" onclick="loadScenario(94.5, 88, 38)">Scenario 2: Mild Fluctuation (SpO₂: 94.5%, HR: 88, HRV: 38ms)</button>
          <button class="scenario-btn" onclick="loadScenario(90, 112, 19)">Scenario 3: Sensory Support Needed (SpO₂: 90%, HR: 112, HRV: 19ms)</button>
        </div>
      </div>

      <!-- Result / VR Environment Mapping Panel -->
      <div class="card">
        <h2>
          <span>VR Environment Mapping</span>
          <span style="font-size:0.8rem; color:var(--text-muted);">Unity VR Target</span>
        </h2>

        <div class="result-display calm" id="resultDisplay">
          <div class="comfort-badge" id="comfortBadge">CALM</div>
          <div class="scene-name" id="sceneName">Environment: Tranquil Pool</div>
          <div class="confidence" id="confText">Confidence: 98.4%</div>
        </div>

        <div class="scene-preview-box Pool" id="scenePreview">
          <h3 id="previewTitle" style="font-size:1.2rem; font-weight:700;">Tranquil Pool</h3>
          <p id="previewSubtitle" style="font-size:0.85rem; opacity:0.9; text-align:center; padding:0 15px;">
            Soothing crystal azure waters, gentle ripple reflections, open daylight ambiance.
          </p>
        </div>

        <div id="safetyAlert" class="safety-alert"></div>

        <div style="font-size:0.8rem; color:var(--text-muted); margin-top:14px; line-height:1.4;">
          <strong>Target Unity Client:</strong> Running on <code>http://127.0.0.1:8000/predict</code>.<br>
          Environments: <code>calm → Pool</code> | <code>adjust → Beach</code> | <code>support → Home</code>.
        </div>
      </div>
    </div>

    <div class="footer">
      VitaVerse Phase 1 — B.Tech Artificial Intelligence & Data Science Final Year Project
    </div>
  </div>

  <script>
    function updateVal(id) {
      document.getElementById(id + 'Val').textContent = parseFloat(document.getElementById(id).value).toFixed(1);
    }

    function resetForm() {
      document.getElementById('spo2').value = 98.0;
      document.getElementById('hr').value = 72.0;
      document.getElementById('hrv').value = 65.0;
      updateVal('spo2');
      updateVal('hr');
      updateVal('hrv');
      predictComfort();
    }

    function loadScenario(spo2, hr, hrv) {
      document.getElementById('spo2').value = spo2;
      document.getElementById('hr').value = hr;
      document.getElementById('hrv').value = hrv;
      updateVal('spo2');
      updateVal('hr');
      updateVal('hrv');
      predictComfort();
    }

    async function predictComfort() {
      const spo2 = parseFloat(document.getElementById('spo2').value);
      const hr = parseFloat(document.getElementById('hr').value);
      const hrv = parseFloat(document.getElementById('hrv').value);

      try {
        const res = await fetch('/predict', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ spo2, hr, hrv })
        });

        if (!res.ok) {
          const err = await res.json();
          alert('Validation Error: ' + JSON.stringify(err.detail));
          return;
        }

        const data = await res.json();
        renderResult(data);
      } catch (e) {
        document.getElementById('apiStatus').textContent = 'API Offline';
        document.getElementById('apiStatus').style.color = '#ef4444';
      }
    }

    function renderResult(data) {
      const cls = data.comfort_class;
      const scene = data.scene;
      
      const badge = document.getElementById('comfortBadge');
      badge.textContent = cls.toUpperCase();
      
      const sceneName = document.getElementById('sceneName');
      sceneName.textContent = 'Environment: ' + scene;

      const confText = document.getElementById('confText');
      confText.textContent = 'Confidence: ' + (data.confidence * 100).toFixed(1) + '%';

      const resBox = document.getElementById('resultDisplay');
      resBox.className = 'result-display ' + cls;

      const previewBox = document.getElementById('scenePreview');
      previewBox.className = 'scene-preview-box ' + scene;
      document.getElementById('previewTitle').textContent = scene === 'Pool' ? 'Tranquil Pool' : (scene === 'Beach' ? 'Umhlanga Beach Sunrise' : 'Kerala Heritage Home');
      document.getElementById('previewSubtitle').textContent = data.scene_description;

      const safetyBox = document.getElementById('safetyAlert');
      if (data.safety_advisory) {
        safetyBox.textContent = data.safety_advisory;
        safetyBox.style.display = 'block';
      } else {
        safetyBox.style.display = 'none';
      }
    }

    // Initial check on page load
    window.onload = function() {
      predictComfort();
    };
  </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    print("[Backend] Starting local Uvicorn server on http://127.0.0.1:8000...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
