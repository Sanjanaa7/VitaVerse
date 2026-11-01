"""
VitaVerse - Local Python API Backend
=====================================
Project: VitaVerse — AI-Driven Personalized Virtual Reality for Comfort and Distraction in Palliative Care
Phase: Phase 2 — Dual-Screen Clinician Console + SHAP Explainability + 7 Panorama Environments

FastAPI service providing real-time comfort classification, SHAP explanations,
and dual-screen browser control for the Unity VR client.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
import re
import shutil

from fastapi import FastAPI, HTTPException, Request, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
import pandas as pd
import joblib

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH    = os.path.join(BASE_DIR, "ml", "comfort_model.joblib")
METADATA_PATH = os.path.join(BASE_DIR, "ml", "model_metadata.json")
STATIC_DIR    = os.path.join(BASE_DIR, "backend", "static")
UPLOADS_DIR   = os.path.join(STATIC_DIR, "uploads")
UNITY_PANORAMA_DIR = os.path.join(BASE_DIR, "unity", "VitaVerseVR", "Assets", "Panoramas")
UNITY_MEMORY_AUDIO_DIR = os.path.join(BASE_DIR, "unity", "VitaVerseVR", "Assets", "Resources", "Audio", "MemoryAudio")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(UNITY_MEMORY_AUDIO_DIR, exist_ok=True)

# ── All 7 panorama environments ────────────────────────────────────────────
ALL_ENVIRONMENTS = {
    "Pool": {
        "comfort_class": "calm",
        "file": "pool_360.jpg",
        "display_name": "Tranquil Pool",
        "description": "Crystal azure waters, bright daylight. Deep parasympathetic relaxation.",
        "emoji": "🏊"
    },
    "Beach": {
        "comfort_class": "adjust",
        "file": "beach_360.jpg",
        "display_name": "Umhlanga Beach Sunrise",
        "description": "Golden sunrise coastal panorama. Gentle sensory recalibration.",
        "emoji": "🏖️"
    },
    "Home": {
        "comfort_class": "support",
        "file": "home_360.jpg",
        "display_name": "Kerala Heritage Home",
        "description": "Warm teakwood architecture, tranquil courtyard. Low-stimulation refuge.",
        "emoji": "🏠"
    },
    "BlueLagoon": {
        "comfort_class": "calm",
        "file": "blue_lagoon_4k.exr",
        "display_name": "Blue Lagoon",
        "description": "Serene tropical lagoon. Crystal water and soft light for deep relaxation.",
        "emoji": "🌊"
    },
    "MistyPines": {
        "comfort_class": "support",
        "file": "misty_pines_4k.exr",
        "display_name": "Misty Pine Forest",
        "description": "Quiet misty woodland. Grounding natural refuge for elevated stress.",
        "emoji": "🌲"
    },
    "NightSky": {
        "comfort_class": "adjust",
        "file": "rogland_clear_night_4k.exr",
        "display_name": "Rogaland Night Sky",
        "description": "Vast starfield over Norwegian landscape. Awe-inducing open expanse.",
        "emoji": "🌌"
    },
    "SunsetFire": {
        "comfort_class": "adjust",
        "file": "the_sky_is_on_fire_4k.exr",
        "display_name": "Sky on Fire Sunset",
        "description": "Dramatic fiery horizon. Warm stimulating transition environment.",
        "emoji": "🔥"
    }
}

# ── Backwards-compatible scene map (keeps all existing tests passing) ──────
CLASS_TO_SCENE_MAP = {
    "calm":    "Pool",
    "adjust":  "Beach",
    "support": "Home"
}

SCENE_DESCRIPTIONS = {k: v["description"] for k, v in ALL_ENVIRONMENTS.items()}

# ── Live sync state — polled by Unity VR client ────────────────────────────
active_environment_state: Dict[str, Any] = {
    "scene_name":          "Pool",
    "comfort_class":       "calm",
    "scene_file":          "pool_360.jpg",
    "display_name":        "Tranquil Pool",
    "photo_url":           "http://127.0.0.1:8000/static/pool_360.jpg",
    "confidence":          0.98,
    "shap_explanation":    {"spo2": 0.0, "hr": 0.0, "hrv": 0.0},
    "memory_audio_active": False,
    "memory_audio_url":    "",
    "memory_audio_title":  "",
    "timestamp":           datetime.now().isoformat()
}

# ── Memory Audio Therapy State ─────────────────────────────────────────────
memory_audio_state: Dict[str, Any] = {
    "active":    False,
    "filename":  "",
    "title":     "",
    "audio_url": ""
}

# ── Session log (last 20 predictions) ─────────────────────────────────────
session_log: List[Dict[str, Any]] = []

# ── In-memory app state ────────────────────────────────────────────────────
app_state = {"model": None, "metadata": None, "is_ready": False, "startup_time": None}


def load_model_and_metadata():
    if app_state["model"] is not None and app_state["metadata"] is not None:
        return
    app_state["startup_time"] = datetime.now().isoformat()
    if os.path.exists(MODEL_PATH):
        try:
            app_state["model"] = joblib.load(MODEL_PATH)
            print(f"[Backend] Loaded trained ML model from: {MODEL_PATH}")
        except Exception as e:
            print(f"[Backend ERROR] Failed to load model: {e}")
    else:
        print(f"[Backend WARNING] Model not found at: {MODEL_PATH}")
    if os.path.exists(METADATA_PATH):
        try:
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                app_state["metadata"] = json.load(f)
            print(f"[Backend] Loaded model metadata from: {METADATA_PATH}")
        except Exception as e:
            print(f"[Backend WARNING] Failed to read metadata: {e}")
    app_state["is_ready"] = (app_state["model"] is not None)


load_model_and_metadata()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Backend] Initializing VitaVerse Phase 2 API...")
    load_model_and_metadata()
    yield
    print("[Backend] Shutting down VitaVerse API...")


app = FastAPI(
    title="VitaVerse Local API",
    description="Phase 2 — Dual-Screen Clinician Console + SHAP Explainability",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files and uploads over local HTTP
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ── Schemas ────────────────────────────────────────────────────────────────

class PatientInput(BaseModel):
    spo2: float = Field(..., description="SpO2 (%): 70–100", examples=[98.0])
    hr:   float = Field(..., description="Heart rate (bpm): 30–220", examples=[72.0])
    hrv:  float = Field(..., description="HRV (ms): 1–250", examples=[65.0])

    @field_validator("spo2")
    @classmethod
    def validate_spo2(cls, v):
        if not (70.0 <= v <= 100.0):
            raise ValueError(f"SpO2 ({v}%) out of bounds [70, 100].")
        return round(float(v), 2)

    @field_validator("hr")
    @classmethod
    def validate_hr(cls, v):
        if not (30.0 <= v <= 220.0):
            raise ValueError(f"HR ({v} bpm) out of bounds [30, 220].")
        return round(float(v), 2)

    @field_validator("hrv")
    @classmethod
    def validate_hrv(cls, v):
        if not (1.0 <= v <= 250.0):
            raise ValueError(f"HRV ({v} ms) out of bounds [1, 250].")
        return round(float(v), 2)


class PredictionResponse(BaseModel):
    comfort_class:     str
    scene:             str
    scene_description: str
    confidence:        float
    probabilities:     Dict[str, float]
    shap_explanation:  Optional[Dict[str, float]] = None
    all_scenes_for_class: List[str] = []
    demo_only:         bool = True
    message:           str
    safety_advisory:   Optional[str] = None
    timestamp:         str


class SetActiveEnvironmentPayload(BaseModel):
    scene_name:    str
    comfort_class: str
    scene_file:    Optional[str] = None
    photo_url:     Optional[str] = None
    display_name:  Optional[str] = None
    confidence:    Optional[float] = 1.0


class MemoryAudioTogglePayload(BaseModel):
    active: bool


# ── Endpoints ──────────────────────────────────────────────────────────────

@app.get("/", summary="API Root & Status")
async def root():
    return {
        "project":  "VitaVerse — AI-Driven Personalized VR for Comfort in Palliative Care",
        "phase":    "Phase 2: Dual-Screen Clinician Console + SHAP Explainability",
        "status":   "online",
        "model_loaded": app_state["model"] is not None,
        "shap_available": SHAP_AVAILABLE,
        "environments": len(ALL_ENVIRONMENTS),
        "docs_url":  "/docs",
        "demo_dashboard_url": "/demo",
        "endpoints": {
            "health":   "/health",
            "predict":  "/predict (POST)",
            "scenarios": "/scenarios (GET)",
            "metadata": "/metadata (GET)",
            "environments": "/environments (GET)",
            "active_environment": "/active-environment (GET/POST)",
            "session_log": "/session-log (GET)"
        },
        "disclaimer": "Academic research prototype. Synthetic demonstration model only."
    }


@app.get("/health", summary="Readiness Check")
async def health_check():
    if not app_state["is_ready"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded. Run train_model.py first."
        )
    return {
        "status": "healthy",
        "model_loaded": True,
        "model_type": "RandomForestClassifier",
        "features": ["spo2", "hr", "hrv"],
        "classes": list(CLASS_TO_SCENE_MAP.keys()),
        "shap_available": SHAP_AVAILABLE,
        "startup_time": app_state["startup_time"]
    }


@app.get("/metadata", summary="Model Training Metadata")
async def get_metadata():
    if app_state["metadata"] is None:
        raise HTTPException(status_code=404, detail="Metadata not found. Run train_model.py first.")
    return app_state["metadata"]


@app.get("/environments", summary="All 7 Panorama Environments")
async def get_environments():
    return {"environments": ALL_ENVIRONMENTS, "count": len(ALL_ENVIRONMENTS)}


@app.get("/scenarios", summary="Simulated Demonstration Scenarios")
async def get_scenarios():
    return {
        "disclaimer": "Simulated demonstration scenarios. Not actual patient records.",
        "scenarios": [
            {
                "id": "scenario_calm",
                "title": "Scenario 1: Stable & Relaxed",
                "spo2": 98.0, "hr": 68.0, "hrv": 75.0,
                "expected_class": "calm",
                "expected_scene": "Pool",
                "notes": "Optimal SpO2, relaxed resting HR, high HRV. Mapped to Tranquil Pool."
            },
            {
                "id": "scenario_adjust",
                "title": "Scenario 2: Mild Physiological Fluctuation",
                "spo2": 94.5, "hr": 88.0, "hrv": 38.0,
                "expected_class": "adjust",
                "expected_scene": "Beach",
                "notes": "Mild autonomic arousal. Mapped to Umhlanga Beach Sunrise."
            },
            {
                "id": "scenario_support",
                "title": "Scenario 3: Elevated Stress / Sensory Support Needed",
                "spo2": 91.0, "hr": 112.0, "hrv": 19.0,
                "expected_class": "support",
                "expected_scene": "Home",
                "notes": "Low HRV, elevated HR, borderline SpO2. Mapped to Kerala Heritage Home."
            }
        ]
    }


@app.get("/session-log", summary="Session Log")
async def get_session_log():
    return {"session_log": session_log, "count": len(session_log)}


@app.get("/active-environment", summary="Get Active Scene (polled by Unity VR)")
async def get_active_environment():
    return active_environment_state


@app.post("/active-environment", summary="Set Active Scene (called by browser console)")
async def set_active_environment(payload: SetActiveEnvironmentPayload):
    env_info = ALL_ENVIRONMENTS.get(payload.scene_name, {})
    file_name = payload.scene_file or env_info.get("file", "pool_360.jpg")
    active_environment_state["scene_name"]    = payload.scene_name
    active_environment_state["comfort_class"] = payload.comfort_class
    active_environment_state["scene_file"]    = file_name
    active_environment_state["display_name"]  = payload.display_name or env_info.get("display_name", payload.scene_name)
    active_environment_state["photo_url"]     = payload.photo_url or f"http://127.0.0.1:8000/static/uploads/{file_name}"
    active_environment_state["confidence"]    = payload.confidence or 1.0
    active_environment_state["timestamp"]     = datetime.now().isoformat()
    return active_environment_state


@app.post("/upload-panorama", summary="Upload Custom 360° Photo for Unity VR")
async def upload_panorama(
    file: UploadFile = File(...),
    comfort_class: str = Form("calm"),
    title: Optional[str] = Form(None)
):
    """
    Clinician/User uploads an equirectangular 360° photo (.jpg, .jpeg, .png, .exr).
    Saves it locally, mirrors to Unity Assets/Panoramas folder, and syncs immediately to Unity VR.
    """
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".exr"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{ext}'. Please upload an equirectangular 360° file (.jpg, .jpeg, .png, or .exr)."
        )

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    safe_name = re.sub(r'[^a-zA-Z0-9_\.-]', '_', file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_filename = f"custom_{timestamp}_{safe_name}"

    # 1. Save to backend static uploads
    upload_path = os.path.join(UPLOADS_DIR, clean_filename)
    with open(upload_path, "wb") as f:
        f.write(content)

    # 2. Mirror into Unity Assets/Panoramas directory if present
    if os.path.isdir(UNITY_PANORAMA_DIR):
        unity_path = os.path.join(UNITY_PANORAMA_DIR, clean_filename)
        try:
            with open(unity_path, "wb") as f:
                f.write(content)
            print(f"[Upload] Mirrored custom photo to Unity Assets: {unity_path}")
        except Exception as e:
            print(f"[Upload Warning] Failed to copy to Unity folder: {e}")

    display_title = title.strip() if title and title.strip() else f"Custom: {file.filename}"
    photo_url = f"http://127.0.0.1:8000/static/uploads/{clean_filename}"

    # Register in dynamic ALL_ENVIRONMENTS
    ALL_ENVIRONMENTS[clean_filename] = {
        "comfort_class": comfort_class,
        "file": clean_filename,
        "display_name": display_title,
        "description": "Custom clinician/patient uploaded 360° personal therapeutic environment.",
        "emoji": "📷"
    }

    # Set active environment immediately
    active_environment_state["scene_name"]    = clean_filename
    active_environment_state["comfort_class"] = comfort_class
    active_environment_state["scene_file"]    = clean_filename
    active_environment_state["display_name"]  = display_title
    active_environment_state["photo_url"]     = photo_url
    active_environment_state["confidence"]    = 1.0
    active_environment_state["timestamp"]     = datetime.now().isoformat()

    return {
        "status": "success",
        "message": f"Custom 360° photo '{display_title}' uploaded and streaming to Unity VR.",
        "scene_name": clean_filename,
        "display_name": display_title,
        "comfort_class": comfort_class,
        "scene_file": clean_filename,
        "file": clean_filename,
        "photo_url": photo_url
    }


@app.delete("/custom-panorama/{filename}", summary="Delete Custom 360° Photo")
@app.post("/delete-panorama/{filename}", summary="Delete Custom 360° Photo")
async def delete_custom_panorama(filename: str):
    """
    Safely deletes a clinician/user uploaded custom 360° photo.
    Enforces safety check: only files starting with 'custom_' can be deleted.
    Removes the file from backend storage and Unity Assets, updates the registry,
    and resets Unity VR back to default Pool if the deleted scene was active.
    """
    clean_filename = os.path.basename(filename)
    if not clean_filename.startswith("custom_"):
        raise HTTPException(
            status_code=400,
            detail="Safety restriction: only custom uploaded panoramas (starting with 'custom_') can be deleted."
        )

    # 1. Remove from backend uploads folder
    upload_file_path = os.path.join(UPLOADS_DIR, clean_filename)
    if os.path.exists(upload_file_path):
        try:
            os.remove(upload_file_path)
        except Exception as e:
            print(f"[Delete Error] Backend file: {e}")

    # 2. Remove from Unity Assets/Panoramas folder
    if os.path.isdir(UNITY_PANORAMA_DIR):
        unity_file_path = os.path.join(UNITY_PANORAMA_DIR, clean_filename)
        unity_meta_path = os.path.join(UNITY_PANORAMA_DIR, f"{clean_filename}.meta")
        if os.path.exists(unity_file_path):
            try:
                os.remove(unity_file_path)
            except Exception as e:
                print(f"[Delete Error] Unity file: {e}")
        if os.path.exists(unity_meta_path):
            try:
                os.remove(unity_meta_path)
            except Exception:
                pass

    # 3. Remove from environment dictionary
    ALL_ENVIRONMENTS.pop(clean_filename, None)

    # 4. If this scene was currently active in VR, reset to default Pool
    reset_to_default = False
    if active_environment_state.get("scene_file") == clean_filename or active_environment_state.get("scene_name") == clean_filename:
        pool_info = ALL_ENVIRONMENTS.get("Pool", {})
        active_environment_state["scene_name"]    = "Pool"
        active_environment_state["comfort_class"] = "calm"
        active_environment_state["scene_file"]    = pool_info.get("file", "pool_360.jpg")
        active_environment_state["display_name"]  = pool_info.get("display_name", "Tranquil Pool")
        active_environment_state["photo_url"]     = "http://127.0.0.1:8000/static/pool_360.jpg"
        active_environment_state["confidence"]    = 0.98
        active_environment_state["timestamp"]     = datetime.now().isoformat()
        reset_to_default = True

    return {
        "status": "success",
        "message": f"Successfully deleted custom photo '{clean_filename}'.",
        "file": clean_filename,
        "reset_to_default": reset_to_default,
        "active_scene": active_environment_state["scene_name"]
    }


# ── Memory Audio Therapy Endpoints ─────────────────────────────────────────

@app.get("/memory-audio", summary="Get Memory Audio Therapy state")
async def get_memory_audio():
    return memory_audio_state


@app.post("/upload-memory-audio", summary="Upload Memory Audio Therapy track")
async def upload_memory_audio(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None)
):
    """
    Clinician/User uploads a personal memory audio file (.mp3, .wav, .ogg, .m4a).
    Saves locally, mirrors into Unity Assets, and syncs to Unity VR to play across all scenarios.
    """
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".mp3", ".wav", ".ogg", ".m4a"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format '{ext}'. Please upload an audio file (.mp3, .wav, .ogg, or .m4a)."
        )

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded audio file is empty.")

    safe_name = re.sub(r'[^a-zA-Z0-9_\.-]', '_', file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_filename = f"memory_{timestamp}_{safe_name}"

    # 1. Save in backend static uploads
    upload_path = os.path.join(UPLOADS_DIR, clean_filename)
    with open(upload_path, "wb") as f:
        f.write(content)

    # 2. Mirror into Unity Assets
    if os.path.isdir(UNITY_MEMORY_AUDIO_DIR):
        unity_path = os.path.join(UNITY_MEMORY_AUDIO_DIR, clean_filename)
        try:
            with open(unity_path, "wb") as f:
                f.write(content)
            print(f"[Upload] Mirrored memory audio to Unity: {unity_path}")
        except Exception as e:
            print(f"[Upload Warning] Failed to mirror memory audio: {e}")

    display_title = title.strip() if title and title.strip() else file.filename
    audio_url = f"http://127.0.0.1:8000/static/uploads/{clean_filename}"

    memory_audio_state["active"]    = True
    memory_audio_state["filename"]  = clean_filename
    memory_audio_state["title"]     = display_title
    memory_audio_state["audio_url"] = audio_url

    active_environment_state["memory_audio_active"] = True
    active_environment_state["memory_audio_url"]    = audio_url
    active_environment_state["memory_audio_title"]  = display_title
    active_environment_state["timestamp"]           = datetime.now().isoformat()

    return {
        "status": "success",
        "message": f"Memory audio therapy track '{display_title}' uploaded and active.",
        "filename": clean_filename,
        "title": display_title,
        "audio_url": audio_url,
        "active": True
    }


@app.post("/memory-audio/toggle", summary="Toggle Memory Audio Therapy on/off")
async def toggle_memory_audio(payload: MemoryAudioTogglePayload):
    if not memory_audio_state.get("filename"):
        raise HTTPException(status_code=400, detail="No memory audio track has been uploaded.")

    memory_audio_state["active"] = payload.active
    active_environment_state["memory_audio_active"] = payload.active
    active_environment_state["timestamp"]           = datetime.now().isoformat()

    return {
        "status": "success",
        "active": memory_audio_state["active"],
        "title": memory_audio_state["title"]
    }


@app.delete("/memory-audio", summary="Delete Memory Audio Therapy track")
@app.post("/delete-memory-audio", summary="Delete Memory Audio Therapy track")
async def delete_memory_audio():
    clean_filename = memory_audio_state.get("filename", "")
    if clean_filename:
        # Remove from backend uploads
        upload_file_path = os.path.join(UPLOADS_DIR, clean_filename)
        if os.path.exists(upload_file_path):
            try:
                os.remove(upload_file_path)
            except Exception as e:
                print(f"[Delete Error] Backend audio file: {e}")

        # Remove from Unity Assets
        if os.path.isdir(UNITY_MEMORY_AUDIO_DIR):
            unity_file_path = os.path.join(UNITY_MEMORY_AUDIO_DIR, clean_filename)
            unity_meta_path = os.path.join(UNITY_MEMORY_AUDIO_DIR, f"{clean_filename}.meta")
            if os.path.exists(unity_file_path):
                try:
                    os.remove(unity_file_path)
                except Exception:
                    pass
            if os.path.exists(unity_meta_path):
                try:
                    os.remove(unity_meta_path)
                except Exception:
                    pass

    memory_audio_state["active"]    = False
    memory_audio_state["filename"]  = ""
    memory_audio_state["title"]     = ""
    memory_audio_state["audio_url"] = ""

    active_environment_state["memory_audio_active"] = False
    active_environment_state["memory_audio_url"]    = ""
    active_environment_state["memory_audio_title"]  = ""
    active_environment_state["timestamp"]           = datetime.now().isoformat()

    return {
        "status": "success",
        "message": "Memory audio therapy track successfully deleted. Restored standard environment sound."
    }


@app.post("/predict", response_model=PredictionResponse, summary="Predict Comfort Level")
async def predict_comfort(payload: PatientInput):
    if app_state["model"] is None:
        raise HTTPException(status_code=503, detail="Model not loaded.")

    input_df = pd.DataFrame([{"spo2": payload.spo2, "hr": payload.hr, "hrv": payload.hrv}])

    try:
        model        = app_state["model"]
        prediction   = model.predict(input_df)[0]
        probabilities = model.predict_proba(input_df)[0]
        class_prob_map = {
            str(cls): round(float(prob), 4)
            for cls, prob in zip(model.classes_, probabilities)
        }
        confidence = round(float(max(probabilities)), 4)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {e}")

    # SHAP explanation
    shap_explanation = {"spo2": 0.0, "hr": 0.0, "hrv": 0.0}
    if SHAP_AVAILABLE:
        try:
            explainer   = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(input_df)
            class_idx   = list(model.classes_).index(prediction)
            feature_names = ["spo2", "hr", "hrv"]
            if isinstance(shap_values, list):
                vals = shap_values[class_idx][0]
            elif hasattr(shap_values, "ndim") and shap_values.ndim == 3:
                vals = shap_values[0, :, class_idx]
            else:
                vals = shap_values[0]
            total = sum(abs(v) for v in vals) or 1.0
            for i, fname in enumerate(feature_names):
                shap_explanation[fname] = round(float(vals[i] / total * 100), 2)
        except Exception as e:
            print(f"[SHAP Warning] {e}")

    scene      = CLASS_TO_SCENE_MAP.get(prediction, "Pool")
    scene_desc = SCENE_DESCRIPTIONS.get(scene, "")
    env_info   = ALL_ENVIRONMENTS.get(scene, ALL_ENVIRONMENTS["Pool"])
    all_scenes_for_class = [k for k, v in ALL_ENVIRONMENTS.items() if v["comfort_class"] == prediction]

    # Update active state for Unity polling
    active_environment_state["scene_name"]       = scene
    active_environment_state["comfort_class"]    = prediction
    active_environment_state["scene_file"]       = env_info["file"]
    active_environment_state["display_name"]     = env_info["display_name"]
    active_environment_state["confidence"]       = confidence
    active_environment_state["shap_explanation"] = shap_explanation
    active_environment_state["timestamp"]        = datetime.now().isoformat()

    # Safety advisory
    safety_advisory = None
    if payload.spo2 < 92.0:
        safety_advisory = (
            f"⚠ SAFETY ALERT: SpO2 ({payload.spo2}%) below 92%. "
            "Clinical evaluation recommended immediately."
        )
    elif payload.hr > 120.0 or payload.hr < 45.0:
        safety_advisory = (
            f"⚠ SAFETY ALERT: HR ({payload.hr} bpm) outside safe limits. "
            "Verify vital signs with clinical staff."
        )

    # Append to session log
    log_entry = {
        "time":          datetime.now().strftime("%H:%M:%S"),
        "spo2":          payload.spo2,
        "hr":            payload.hr,
        "hrv":           payload.hrv,
        "comfort_class": prediction,
        "scene":         scene,
        "confidence":    f"{confidence*100:.1f}%",
        "shap_top":      max(shap_explanation, key=lambda k: abs(shap_explanation[k]))
    }
    session_log.append(log_entry)
    if len(session_log) > 20:
        session_log.pop(0)

    return PredictionResponse(
        comfort_class=prediction,
        scene=scene,
        scene_description=scene_desc,
        confidence=confidence,
        probabilities=class_prob_map,
        shap_explanation=shap_explanation,
        all_scenes_for_class=all_scenes_for_class,
        demo_only=True,
        message="Experimental prediction using synthetic demonstration data.",
        safety_advisory=safety_advisory,
        timestamp=datetime.now().isoformat()
    )


# ── Dual-Screen Clinician Console ──────────────────────────────────────────

@app.get("/console", response_class=HTMLResponse, summary="Clinician VR Console")
@app.get("/demo",    response_class=HTMLResponse, summary="Clinician VR Console")
async def demo_dashboard():
    html_content = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>VitaVerse — Hospital Clinician VR Console</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root {
      --bg: #090e17;
      --surface: #0f172a;
      --card-bg: #141e33;
      --card-border: rgba(148, 163, 184, 0.14);
      --accent-blue: #0284c7;
      --accent-cyan: #06b6d4;
      --calm: #10b981;
      --calm-bg: rgba(16, 185, 129, 0.12);
      --adjust: #f59e0b;
      --adjust-bg: rgba(245, 158, 11, 0.12);
      --support: #8b5cf6;
      --support-bg: rgba(139, 92, 246, 0.12);
      --alert-red: #ef4444;
      --text-main: #f1f5f9;
      --text-muted: #94a3b8;
      --text-dim: #64748b;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg);
      color: var(--text-main);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      font-size: 13px;
      line-height: 1.5;
      padding: 16px;
      min-height: 100vh;
    }
    .app-container {
      max-width: 1440px;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    /* ── Hospital Telemetry Header ── */
    .hospital-header {
      background: var(--surface);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 12px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
    }
    .hospital-brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .cross-icon {
      width: 34px;
      height: 34px;
      border-radius: 8px;
      background: linear-gradient(135deg, #0284c7, #06b6d4);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
      font-weight: 900;
      color: #fff;
      box-shadow: 0 0 14px rgba(6, 182, 212, 0.35);
    }
    .brand-title {
      font-size: 1.05rem;
      font-weight: 700;
      letter-spacing: 0.3px;
      color: #fff;
    }
    .brand-sub {
      font-size: 0.72rem;
      color: var(--text-muted);
      letter-spacing: 0.5px;
      text-transform: uppercase;
    }
    .meta-pills {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }
    .meta-pill {
      background: rgba(30, 41, 59, 0.75);
      border: 1px solid var(--card-border);
      border-radius: 6px;
      padding: 4px 10px;
      font-size: 0.75rem;
      color: var(--text-muted);
      font-variant-numeric: tabular-nums;
    }
    .meta-pill strong { color: #e2e8f0; }
    .status-live {
      display: flex;
      align-items: center;
      gap: 6px;
      background: rgba(16, 185, 129, 0.15);
      border: 1px solid rgba(16, 185, 129, 0.35);
      color: #34d399;
      font-weight: 700;
    }
    .live-pulse {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #10b981;
      animation: pulse 1.6s infinite ease-in-out;
    }
    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.35; transform: scale(0.85); }
    }

    /* ── Main Clinical Grid ── */
    .clinical-grid {
      display: grid;
      grid-template-columns: 360px 1fr;
      gap: 16px;
      align-items: start;
    }
    @media (max-width: 1080px) {
      .clinical-grid { grid-template-columns: 1fr; }
    }

    /* ── Cards ── */
    .card {
      background: var(--surface);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 16px;
    }
    .card-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 14px;
      padding-bottom: 8px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }
    .card-title {
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      color: var(--text-muted);
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .card-tag {
      font-size: 0.68rem;
      padding: 2px 7px;
      border-radius: 4px;
      background: rgba(2, 132, 199, 0.18);
      color: #38bdf8;
      font-weight: 600;
      text-transform: uppercase;
    }

    /* ── Vitals Monitor Tiles ── */
    .vital-tile {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 12px 14px;
      margin-bottom: 10px;
      position: relative;
      overflow: hidden;
    }
    .vital-tile::before {
      content: "";
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: 4px;
    }
    .vital-tile.spo2-tile::before { background: #06b6d4; }
    .vital-tile.hr-tile::before   { background: #f43f5e; }
    .vital-tile.hrv-tile::before  { background: #10b981; }

    .vital-top {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      margin-bottom: 4px;
    }
    .vital-label {
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
    }
    .vital-norm {
      font-size: 0.68rem;
      color: var(--text-dim);
    }
    .vital-num-row {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      margin-bottom: 6px;
    }
    .vital-val {
      font-size: 1.6rem;
      font-weight: 800;
      font-variant-numeric: tabular-nums;
      letter-spacing: -0.5px;
    }
    .spo2-val { color: #38bdf8; }
    .hr-val   { color: #fb7185; }
    .hrv-val  { color: #34d399; }
    .vital-unit {
      font-size: 0.78rem;
      color: var(--text-muted);
      font-weight: 600;
      margin-left: 3px;
    }

    input[type="range"] {
      width: 100%;
      height: 6px;
      border-radius: 3px;
      background: #1e293b;
      outline: none;
      accent-color: #0284c7;
      cursor: pointer;
    }

    /* ── Buttons ── */
    .btn-row {
      display: flex;
      gap: 8px;
      margin-top: 14px;
    }
    .btn {
      padding: 10px 14px;
      border-radius: 6px;
      border: none;
      font-size: 0.82rem;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.15s;
    }
    .btn-primary {
      flex: 1;
      background: linear-gradient(135deg, #0284c7, #2563eb);
      color: #fff;
      box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3);
    }
    .btn-primary:hover {
      opacity: 0.92;
      transform: translateY(-1px);
    }
    .btn-secondary {
      background: #1e293b;
      color: #94a3b8;
    }
    .btn-secondary:hover { background: #334155; color: #fff; }

    /* ── Preset Scenarios ── */
    .scenario-btn {
      width: 100%;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 10px 12px;
      margin-bottom: 8px;
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      align-items: center;
      transition: all 0.15s;
      text-align: left;
    }
    .scenario-btn:hover {
      border-color: #0284c7;
      background: rgba(2, 132, 199, 0.08);
    }
    .sc-info strong {
      display: block;
      color: #f1f5f9;
      font-size: 0.78rem;
    }
    .sc-info span {
      font-size: 0.7rem;
      color: var(--text-muted);
    }
    .sc-tag {
      font-size: 0.68rem;
      font-weight: 800;
      padding: 3px 8px;
      border-radius: 4px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .sc-calm    { background: var(--calm-bg);    color: #34d399; }
    .sc-adjust  { background: var(--adjust-bg);  color: #fbbf24; }
    .sc-support { background: var(--support-bg); color: #c084fc; }

    /* ── Safety Alert Banner ── */
    .safety-banner {
      margin-top: 12px;
      padding: 10px 12px;
      border-radius: 6px;
      background: rgba(239, 68, 68, 0.15);
      border: 1px solid rgba(239, 68, 68, 0.4);
      color: #fca5a5;
      font-size: 0.75rem;
      font-weight: 600;
      display: none;
      line-height: 1.4;
    }

    /* ── Right Column: AI Diagnosis + Explainability ── */
    .right-stack {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .diagnosis-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }
    @media (max-width: 860px) {
      .diagnosis-row { grid-template-columns: 1fr; }
    }

    /* Diagnosis Status Card */
    .status-card {
      background: var(--surface);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      position: relative;
    }
    .status-card.calm    { border-color: rgba(16, 185, 129, 0.4); }
    .status-card.adjust  { border-color: rgba(245, 158, 11, 0.4); }
    .status-card.support { border-color: rgba(139, 92, 246, 0.4); }

    .state-badge-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }
    .state-badge {
      font-size: 1.4rem;
      font-weight: 900;
      letter-spacing: 0.8px;
      text-transform: uppercase;
    }
    .state-badge.calm    { color: #34d399; }
    .state-badge.adjust  { color: #fbbf24; }
    .state-badge.support { color: #c084fc; }

    .confidence-meter {
      background: #1e293b;
      border-radius: 4px;
      height: 6px;
      overflow: hidden;
      margin-top: 6px;
      margin-bottom: 4px;
    }
    .confidence-fill {
      height: 100%;
      background: linear-gradient(90deg, #0284c7, #10b981);
      width: 98%;
      transition: width 0.3s ease;
    }

    .active-scene-box {
      margin-top: 12px;
      padding: 10px 12px;
      border-radius: 6px;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .active-scene-label {
      font-size: 0.7rem;
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .active-scene-name {
      font-size: 0.95rem;
      font-weight: 700;
      color: #e2e8f0;
    }
    .headset-tag {
      font-size: 0.68rem;
      padding: 2px 7px;
      border-radius: 4px;
      background: rgba(16, 185, 129, 0.15);
      color: #34d399;
      font-weight: 700;
    }

    /* SHAP Feature Bars */
    .shap-bars {
      display: flex;
      flex-direction: column;
      gap: 10px;
      margin-top: 8px;
    }
    .shap-item-row {
      display: flex;
      justify-content: space-between;
      font-size: 0.75rem;
      margin-bottom: 3px;
    }
    .shap-bar-bg {
      background: #1e293b;
      border-radius: 4px;
      height: 7px;
      overflow: hidden;
    }
    .shap-bar-fill {
      height: 100%;
      border-radius: 4px;
      transition: width 0.3s ease;
    }
    .bar-spo2 { background: #06b6d4; }
    .bar-hr   { background: #f43f5e; }
    .bar-hrv  { background: #10b981; }

    /* ── Environment Selector Tiers ── */
    .tier-header {
      font-size: 0.72rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      color: var(--text-muted);
      margin: 12px 0 8px 0;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .tier-header:first-of-type { margin-top: 4px; }
    .env-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
      gap: 10px;
    }
    .env-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 12px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: all 0.15s ease;
      position: relative;
    }
    .env-card:hover {
      border-color: #38bdf8;
      background: #16243f;
    }
    .env-card.active-calm {
      border-color: #10b981;
      box-shadow: 0 0 10px rgba(16, 185, 129, 0.25);
    }
    .env-card.active-adjust {
      border-color: #f59e0b;
      box-shadow: 0 0 10px rgba(245, 158, 11, 0.25);
    }
    .env-card.active-support {
      border-color: #8b5cf6;
      box-shadow: 0 0 10px rgba(139, 92, 246, 0.25);
    }

    .env-top-line {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 6px;
    }
    .env-title-group {
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .env-emoji { font-size: 1.1rem; }
    .env-name {
      font-size: 0.84rem;
      font-weight: 700;
      color: #f8fafc;
    }
    .env-class-pill {
      font-size: 0.62rem;
      font-weight: 800;
      padding: 2px 5px;
      border-radius: 3px;
      text-transform: uppercase;
    }
    .pill-calm    { background: var(--calm-bg);    color: #34d399; }
    .pill-adjust  { background: var(--adjust-bg);  color: #fbbf24; }
    .pill-support { background: var(--support-bg); color: #c084fc; }

    .env-desc {
      font-size: 0.72rem;
      color: var(--text-muted);
      margin-bottom: 10px;
      line-height: 1.35;
      min-height: 38px;
    }
    .env-btn {
      width: 100%;
      padding: 7px 10px;
      background: rgba(2, 132, 199, 0.15);
      border: 1px solid rgba(2, 132, 199, 0.35);
      border-radius: 5px;
      color: #38bdf8;
      font-size: 0.74rem;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.15s;
    }
    .env-btn:hover {
      background: rgba(2, 132, 199, 0.3);
      color: #fff;
    }
    .env-card.active-calm .env-btn,
    .env-card.active-adjust .env-btn,
    .env-card.active-support .env-btn {
      background: #0284c7;
      color: #fff;
      border-color: #0284c7;
    }
    .env-delete-btn {
      padding: 7px 10px;
      background: rgba(239, 68, 68, 0.15);
      border: 1px solid rgba(239, 68, 68, 0.35);
      border-radius: 5px;
      color: #fca5a5;
      font-size: 0.74rem;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.15s;
    }
    .env-delete-btn:hover {
      background: #dc2626;
      color: #fff;
      border-color: #dc2626;
    }

    /* ── Telemetry Session Log Table ── */
    .log-card {
      background: var(--surface);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 16px;
      overflow-x: auto;
    }
    .log-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.75rem;
      min-width: 680px;
    }
    .log-table th {
      text-align: left;
      padding: 8px 10px;
      color: var(--text-dim);
      font-size: 0.68rem;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }
    .log-table td {
      padding: 7px 10px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
      color: #cbd5e1;
      font-variant-numeric: tabular-nums;
    }
    .log-table tr:hover { background: rgba(30, 41, 59, 0.5); }
    .log-badge {
      font-size: 0.65rem;
      font-weight: 800;
      padding: 2px 6px;
      border-radius: 4px;
      text-transform: uppercase;
    }
  </style>
</head>
<body>
<div class="app-container">

  <!-- ── Hospital Telemetry Header ── -->
  <header class="hospital-header">
    <div class="hospital-brand">
      <div class="cross-icon">✚</div>
      <div>
        <div class="brand-title">VitaVerse Clinical Console</div>
        <div class="brand-sub">AI-Driven Personalized VR Palliative Care System · Phase 2</div>
      </div>
    </div>
    <div class="meta-pills">
      <div class="meta-pill">Patient: <strong>#VV-4029</strong></div>
      <div class="meta-pill">Unit: <strong>Palliative Care VR-3</strong></div>
      <div class="meta-pill">Server: <strong>127.0.0.1:8000</strong></div>
      <div class="meta-pill status-live">
        <span class="live-pulse"></span>
        <span id="unitySyncLabel">Unity VR Synced</span>
      </div>
    </div>
  </header>

  <!-- ── Main Grid ── -->
  <div class="clinical-grid">

    <!-- ── Left Column: Telemetry Controls ── -->
    <div class="left-stack" style="display:flex; flex-direction:column; gap:16px;">

      <!-- Patient Vitals Tile -->
      <div class="card">
        <div class="card-head">
          <span class="card-title">Patient Biofeedback Telemetry</span>
          <span class="card-tag">Lead II Active</span>
        </div>

        <!-- SpO2 -->
        <div class="vital-tile spo2-tile">
          <div class="vital-top">
            <span class="vital-label">SpO₂ Oxygen Saturation</span>
            <span class="vital-norm">Normal: 95 – 100%</span>
          </div>
          <div class="vital-num-row">
            <div><span class="vital-val spo2-val" id="spo2Val">98.0</span><span class="vital-unit">%</span></div>
            <span style="font-size:0.7rem; color:#38bdf8; font-weight:600;">Optimal</span>
          </div>
          <input type="range" id="spo2" min="70" max="100" step="0.5" value="98.0" oninput="updateVital('spo2')">
        </div>

        <!-- Heart Rate -->
        <div class="vital-tile hr-tile">
          <div class="vital-top">
            <span class="vital-label">Heart Rate (Pulse)</span>
            <span class="vital-norm">Resting: 60 – 100 bpm</span>
          </div>
          <div class="vital-num-row">
            <div><span class="vital-val hr-val" id="hrVal">72</span><span class="vital-unit">bpm</span></div>
            <span style="font-size:0.7rem; color:#fb7185; font-weight:600;">Sinus Rhythm</span>
          </div>
          <input type="range" id="hr" min="40" max="180" step="1" value="72" oninput="updateVital('hr')">
        </div>

        <!-- HRV -->
        <div class="vital-tile hrv-tile">
          <div class="vital-top">
            <span class="vital-label">Heart Rate Variability</span>
            <span class="vital-norm">Autonomic Tone</span>
          </div>
          <div class="vital-num-row">
            <div><span class="vital-val hrv-val" id="hrvVal">65</span><span class="vital-unit">ms</span></div>
            <span style="font-size:0.7rem; color:#34d399; font-weight:600;">Balanced</span>
          </div>
          <input type="range" id="hrv" min="5" max="180" step="1" value="65" oninput="updateVital('hrv')">
        </div>

        <!-- Controls -->
        <div class="btn-row">
          <button class="btn btn-primary" onclick="analyze()">Analyze &amp; Stream to VR ▶</button>
          <button class="btn btn-secondary" onclick="resetForm()">Reset</button>
        </div>

        <!-- Safety Alert -->
        <div id="safetyAlert" class="safety-banner"></div>
      </div>

      <!-- Quick Preset Profiles -->
      <div class="card">
        <div class="card-head">
          <span class="card-title">Simulated Patient Profiles</span>
          <span class="card-tag">Presets</span>
        </div>

        <button class="scenario-btn" onclick="loadScenario(98, 68, 75)">
          <div class="sc-info">
            <strong>Scenario 1: Stable &amp; Relaxed</strong>
            <span>SpO₂ 98.0% · HR 68 bpm · HRV 75 ms</span>
          </div>
          <span class="sc-tag sc-calm">CALM</span>
        </button>

        <button class="scenario-btn" onclick="loadScenario(94.5, 88, 38)">
          <div class="sc-info">
            <strong>Scenario 2: Mild Autonomic Fluctuation</strong>
            <span>SpO₂ 94.5% · HR 88 bpm · HRV 38 ms</span>
          </div>
          <span class="sc-tag sc-adjust">ADJUST</span>
        </button>

        <button class="scenario-btn" onclick="loadScenario(90, 112, 19)">
          <div class="sc-info">
            <strong>Scenario 3: Elevated Stress / Distress</strong>
            <span>SpO₂ 90.0% · HR 112 bpm · HRV 19 ms</span>
          </div>
          <span class="sc-tag sc-support">SUPPORT</span>
        </button>
      </div>

      <!-- Custom 360° Photo Upload Card -->
      <div class="card">
        <div class="card-head">
          <span class="card-title">Upload Custom 360° Photo</span>
          <span class="card-tag">Patient Horizon</span>
        </div>

        <form id="uploadForm" onsubmit="handleUpload(event)" style="display:flex; flex-direction:column; gap:9px;">
          <div>
            <label style="font-size:0.7rem; color:var(--text-muted); font-weight:700; display:block; margin-bottom:4px; text-transform:uppercase;">
              360° Panorama File (.jpg, .png, .exr):
            </label>
            <input type="file" id="customFile" accept=".jpg,.jpeg,.png,.exr" required
                   style="font-size:0.74rem; color:#cbd5e1; width:100%; padding:6px; background:var(--card-bg); border:1px solid var(--card-border); border-radius:5px;">
          </div>

          <div>
            <label style="font-size:0.7rem; color:var(--text-muted); font-weight:700; display:block; margin-bottom:4px; text-transform:uppercase;">
              Environment Label:
            </label>
            <input type="text" id="customTitle" placeholder="e.g. Patient's Garden / Childhood Veranda"
                   style="font-size:0.75rem; color:#fff; width:100%; padding:7px 9px; background:var(--card-bg); border:1px solid var(--card-border); border-radius:5px; outline:none;">
          </div>

          <div>
            <label style="font-size:0.7rem; color:var(--text-muted); font-weight:700; display:block; margin-bottom:4px; text-transform:uppercase;">
              Therapeutic Comfort Tier:
            </label>
            <select id="customComfortClass"
                    style="font-size:0.75rem; color:#f1f5f9; width:100%; padding:7px 9px; background:var(--card-bg); border:1px solid var(--card-border); border-radius:5px; outline:none;">
              <option value="calm">🟢 Tier 1: Calm / Relaxation</option>
              <option value="adjust">🟡 Tier 2: Adjust / Recalibration</option>
              <option value="support">🟣 Tier 3: Support / Grounded Refuge</option>
            </select>
          </div>

          <button type="submit" id="uploadSubmitBtn" class="btn btn-primary" style="margin-top:4px;">
            Upload &amp; Stream to VR Headset ▶
          </button>
          <div id="uploadFeedback" style="font-size:0.72rem; font-weight:600; display:none; padding:7px 9px; border-radius:4px; text-align:center;"></div>
        </form>
      </div>

      <!-- Memory Audio Therapy Card -->
      <div class="card" id="memoryAudioCard">
        <div class="card-head">
          <span class="card-title">Memory Audio Therapy</span>
          <span class="card-tag" style="background:rgba(217,70,239,0.15); color:#e879f9; border-color:rgba(217,70,239,0.3);">Reminiscence Audio</span>
        </div>
        <div style="font-size:0.71rem; color:var(--text-muted); line-height:1.35; margin-bottom:8px;">
          Upload a patient's personal voice recording, prayer, or calming music. When enabled, it plays with every scenario regardless of environment.
        </div>

        <!-- Upload Form -->
        <form id="memoryAudioForm" onsubmit="handleMemoryAudioUpload(event)" style="display:flex; flex-direction:column; gap:8px;">
          <div>
            <label style="font-size:0.68rem; color:var(--text-muted); font-weight:700; display:block; margin-bottom:3px; text-transform:uppercase;">
              Audio File (.mp3, .wav, .m4a):
            </label>
            <input type="file" id="memoryAudioFile" accept=".mp3,.wav,.ogg,.m4a" required
                   style="font-size:0.73rem; color:#cbd5e1; width:100%; padding:5px; background:var(--card-bg); border:1px solid var(--card-border); border-radius:5px;">
          </div>

          <div>
            <label style="font-size:0.68rem; color:var(--text-muted); font-weight:700; display:block; margin-bottom:3px; text-transform:uppercase;">
              Track Label / Description:
            </label>
            <input type="text" id="memoryAudioTitle" placeholder="e.g. Family Voice / Calming Hymn"
                   style="font-size:0.73rem; color:#fff; width:100%; padding:6px 8px; background:var(--card-bg); border:1px solid var(--card-border); border-radius:5px; outline:none;">
          </div>

          <button type="submit" id="memoryAudioSubmitBtn" class="btn" style="background:#a21caf; border-color:#c026d3; color:#fff; font-size:0.74rem; padding:8px; margin-top:2px;">
            ♫ Upload &amp; Play Memory Audio
          </button>
        </form>

        <!-- Active Track Box -->
        <div id="memoryAudioActiveBox" style="display:none; margin-top:10px; padding:9px; background:rgba(162,28,175,0.12); border:1px solid rgba(192,38,211,0.3); border-radius:6px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <div style="display:flex; align-items:center; gap:6px;">
              <span style="font-size:1.1rem;">🎧</span>
              <div>
                <div id="memoryTrackName" style="font-size:0.74rem; font-weight:700; color:#f0abfc;">Track Name</div>
                <div id="memoryTrackStatus" style="font-size:0.67rem; color:#d8b4fe;">Playing across all environments</div>
              </div>
            </div>
            <span id="memoryTrackBadge" style="font-size:0.65rem; padding:2px 6px; border-radius:10px; background:rgba(34,197,94,0.2); color:#4ade80; border:1px solid rgba(34,197,94,0.4); font-weight:700;">ACTIVE</span>
          </div>

          <div style="display:flex; gap:6px; margin-top:6px;">
            <button type="button" id="memoryToggleBtn" onclick="toggleMemoryAudio()" style="flex:1; font-size:0.72rem; padding:5px 8px; border-radius:4px; font-weight:600; cursor:pointer; background:#334155; color:#fff; border:1px solid #475569;">
              ⏸ Mute Memory Audio
            </button>
            <button type="button" onclick="deleteMemoryAudio()" style="font-size:0.72rem; padding:5px 8px; border-radius:4px; font-weight:600; cursor:pointer; background:rgba(239,68,68,0.15); color:#f87171; border:1px solid rgba(239,68,68,0.35);" title="Delete memory audio track">
              ✕ Delete
            </button>
          </div>
        </div>

        <div id="memoryAudioFeedback" style="font-size:0.72rem; font-weight:600; display:none; padding:6px 8px; border-radius:4px; text-align:center; margin-top:6px;"></div>
      </div>

    </div>

    <!-- ── Right Column: AI Diagnosis + Environments ── -->
    <div class="right-stack">

      <!-- Diagnosis & SHAP Row -->
      <div class="diagnosis-row">

        <!-- Comfort Classification State -->
        <div class="status-card calm" id="statusCard">
          <div>
            <div class="card-head" style="margin-bottom:8px; padding-bottom:6px;">
              <span class="card-title">AI Comfort Assessment</span>
              <span class="card-tag" id="confTag">Confidence: 98.4%</span>
            </div>
            <div class="state-badge-row">
              <span class="state-badge calm" id="comfortBadge">CALM</span>
              <span style="font-size:0.75rem; color:var(--text-muted);" id="tierLabel">Tier 1: Relaxation</span>
            </div>
            <div class="confidence-meter">
              <div class="confidence-fill" id="confBar" style="width: 98%;"></div>
            </div>
          </div>

          <div class="active-scene-box">
            <div>
              <div class="active-scene-label">Now Active in VR Headset:</div>
              <div class="active-scene-name" id="activeSceneName">Tranquil Pool</div>
              <div id="activeAudioStatus" style="font-size:0.75rem; color:#38bdf8; margin-top:3px; display:flex; align-items:center; gap:4px; font-weight:500;">
                <span>🔊</span> <span id="activeAudioText">Pool water sound playing</span>
              </div>
            </div>
            <span class="headset-tag">● Live In Headset</span>
          </div>
        </div>

        <!-- SHAP Feature Attribution -->
        <div class="card">
          <div class="card-head">
            <span class="card-title">Explainable AI (SHAP Attribution)</span>
            <span class="card-tag">Model Drivers</span>
          </div>

          <div class="shap-bars">
            <div>
              <div class="shap-item-row">
                <span style="color:#06b6d4; font-weight:600;">SpO₂ Saturation</span>
                <span id="shapSpo2Val" style="font-weight:700;">28.7%</span>
              </div>
              <div class="shap-bar-bg"><div class="shap-bar-fill bar-spo2" id="shapSpo2Bar" style="width:28.7%;"></div></div>
            </div>

            <div>
              <div class="shap-item-row">
                <span style="color:#f43f5e; font-weight:600;">Heart Rate (Pulse)</span>
                <span id="shapHrVal" style="font-weight:700;">34.8%</span>
              </div>
              <div class="shap-bar-bg"><div class="shap-bar-fill bar-hr" id="shapHrBar" style="width:34.8%;"></div></div>
            </div>

            <div>
              <div class="shap-item-row">
                <span style="color:#10b981; font-weight:600;">Heart Rate Variability (HRV)</span>
                <span id="shapHrvVal" style="font-weight:700;">36.5%</span>
              </div>
              <div class="shap-bar-bg"><div class="shap-bar-fill bar-hrv" id="shapHrvBar" style="width:36.5%;"></div></div>
            </div>
          </div>

          <div id="shapSummary" style="font-size:0.72rem; color:var(--text-muted); margin-top:10px; line-height:1.4;">
            Primary physiological driver: <strong>HRV (36.5%)</strong> reflects healthy autonomic parasympathetic tone.
          </div>
        </div>

      </div>

      <!-- 360° VR Therapeutic Environments -->
      <div class="card">
        <div class="card-head" style="margin-bottom:6px;">
          <span class="card-title">Clinical 360° VR Therapeutic Environments</span>
          <span class="card-tag">Dual-Screen Remote Override</span>
        </div>

        <!-- Tier 1: Calm -->
        <div class="tier-header"><span style="color:#10b981;">●</span> Tier 1: Deep Relaxation (Parasympathetic Stabilization)</div>
        <div class="env-grid" id="envGridCalm"></div>

        <!-- Tier 2: Adjust -->
        <div class="tier-header"><span style="color:#f59e0b;">●</span> Tier 2: Sensory Recalibration (Mild Restlessness)</div>
        <div class="env-grid" id="envGridAdjust"></div>

        <!-- Tier 3: Support -->
        <div class="tier-header"><span style="color:#8b5cf6;">●</span> Tier 3: Grounded Sanctuary (High Stress Support)</div>
        <div class="env-grid" id="envGridSupport"></div>
      </div>

    </div>

  </div>

  <!-- ── Telemetry Session Audit Log ── -->
  <div class="log-card">
    <div class="card-head" style="margin-bottom:8px; padding-bottom:6px;">
      <span class="card-title">Clinical Telemetry Session Log</span>
      <span class="card-tag">Real-Time Audit Trail</span>
    </div>
    <table class="log-table">
      <thead>
        <tr>
          <th>Time</th>
          <th>SpO₂</th>
          <th>Pulse (HR)</th>
          <th>HRV</th>
          <th>Classification</th>
          <th>Therapeutic Environment</th>
          <th>Confidence</th>
          <th>Primary SHAP Driver</th>
        </tr>
      </thead>
      <tbody id="logTbody">
        <tr>
          <td colspan="8" style="text-align:center; color:var(--text-dim); padding:14px;">No session events recorded yet. Click "Analyze &amp; Stream to VR" to record.</td>
        </tr>
      </tbody>
    </table>
  </div>

</div>

<script>
// ── State ─────────────────────────────────────────────────────────────
let allEnvironments = {};
let activeSceneName = "Pool";

// ── Audio Soundscapes Mapping (Friendly Clinical Names) ───────────────
const envAudioMap = {
  "Pool": "Pool water sound playing",
  "Beach": "Beach sound playing",
  "BlueLagoon": "Beach sound playing",
  "NightSky": "Sky sound playing",
  "SunsetFire": "Sky sound playing",
  "Home": "Birds chirping sound playing",
  "MistyPines": "Winter forest sound playing"
};

// ── Vitals Sliders ───────────────────────────────────────────────────
function updateVital(id) {
  const v = parseFloat(document.getElementById(id).value);
  document.getElementById(id + 'Val').textContent = (id === 'spo2') ? v.toFixed(1) : Math.round(v);
}

function loadScenario(spo2, hr, hrv) {
  document.getElementById('spo2').value = spo2;
  document.getElementById('hr').value = hr;
  document.getElementById('hrv').value = hrv;
  updateVital('spo2');
  updateVital('hr');
  updateVital('hrv');
  analyze();
}

function resetForm() {
  loadScenario(98.0, 72, 65);
}

// ── Load All Environments ─────────────────────────────────────────────
async function loadEnvironments() {
  try {
    const res = await fetch('/environments');
    const data = await res.json();
    allEnvironments = data.environments || {};
    renderEnvironments();
  } catch (err) {
    console.error("Could not load environments:", err);
  }
}

function renderEnvironments() {
  const calmContainer    = document.getElementById('envGridCalm');
  const adjustContainer  = document.getElementById('envGridAdjust');
  const supportContainer = document.getElementById('envGridSupport');

  calmContainer.innerHTML    = '';
  adjustContainer.innerHTML  = '';
  supportContainer.innerHTML = '';

  for (const [key, env] of Object.entries(allEnvironments)) {
    const card = document.createElement('div');
    const isActive = (key === activeSceneName);
    const cls = env.comfort_class;
    card.className = `env-card ${isActive ? 'active-' + cls : ''}`;
    card.id = `card-${key}`;

    const isCustom = key.startsWith("custom_") || (env.file && env.file.startsWith("custom_"));
    const deleteBtn = isCustom ? `
      <button class="env-delete-btn" title="Delete custom uploaded photo" onclick="deleteCustomPhoto(event, '${key}')">
        ✕ Delete
      </button>
    ` : '';

    const audioText = envAudioMap[key];
    const soundIndicator = (isActive && audioText) ? `
      <div style="font-size:0.72rem; color:#38bdf8; margin-top:5px; display:inline-flex; align-items:center; gap:4px; font-weight:600; background:rgba(56,189,248,0.12); padding:2px 7px; border-radius:4px; border:1px solid rgba(56,189,248,0.25);">
        <span>🔊</span> <span>${audioText}</span>
      </div>
    ` : '';

    card.innerHTML = `
      <div>
        <div class="env-top-line">
          <div class="env-title-group">
            <span class="env-emoji">${env.emoji || '🌿'}</span>
            <span class="env-name">${env.display_name}</span>
          </div>
          <span class="env-class-pill pill-${cls}">${cls.toUpperCase()}</span>
        </div>
        <div class="env-desc">${env.description}</div>
        ${soundIndicator}
      </div>
      <div style="display:flex; gap:6px; margin-top:6px;">
        <button class="env-btn" style="flex:1;" onclick="streamEnvironment('${key}', '${cls}', '${env.file}', '${env.display_name}')">
          ${isActive ? '● Streaming In VR' : '▶ Stream to VR'}
        </button>
        ${deleteBtn}
      </div>
    `;

    if (cls === 'calm') calmContainer.appendChild(card);
    else if (cls === 'adjust') adjustContainer.appendChild(card);
    else if (cls === 'support') supportContainer.appendChild(card);
  }
}

// ── Stream Environment ────────────────────────────────────────────────
async function streamEnvironment(sceneName, comfortClass, sceneFile, displayName) {
  try {
    const res = await fetch('/active-environment', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        scene_name: sceneName,
        comfort_class: comfortClass,
        scene_file: sceneFile,
        confidence: 1.0
      })
    });
    if (res.ok) {
      applyActiveEnvironment(sceneName, comfortClass, displayName, 1.0);
    }
  } catch (err) {
    console.error("Error setting active environment:", err);
  }
}

function applyActiveEnvironment(sceneName, comfortClass, displayName, confidence) {
  activeSceneName = sceneName;
  document.getElementById('activeSceneName').textContent = displayName || sceneName;

  // Update Ambient Sound Indicator
  const audioStatusEl = document.getElementById('activeAudioStatus');
  const audioTextEl = document.getElementById('activeAudioText');
  if (audioStatusEl && audioTextEl) {
    if (memoryAudioState && memoryAudioState.active && memoryAudioState.title) {
      audioStatusEl.style.display = "flex";
      audioTextEl.textContent = `Memory Audio Therapy: ${memoryAudioState.title} (Playing with scenario)`;
    } else {
      const audioText = envAudioMap[sceneName] || "";
      if (audioText) {
        audioStatusEl.style.display = "flex";
        audioTextEl.textContent = audioText;
      } else {
        audioStatusEl.style.display = "none";
      }
    }
  }

  // Update Status Card
  const card = document.getElementById('statusCard');
  card.className = `status-card ${comfortClass}`;

  const badge = document.getElementById('comfortBadge');
  badge.textContent = comfortClass.toUpperCase();
  badge.className = `state-badge ${comfortClass}`;

  const tierMap = {
    calm: "Tier 1: Relaxation",
    adjust: "Tier 2: Recalibration",
    support: "Tier 3: Refuge"
  };
  document.getElementById('tierLabel').textContent = tierMap[comfortClass] || "";
  document.getElementById('confTag').textContent = `Confidence: ${(confidence * 100).toFixed(1)}%`;
  document.getElementById('confBar').style.width = `${Math.min(100, Math.max(10, confidence * 100))}%`;

  renderEnvironments();
}

// ── Analyze Vitals ────────────────────────────────────────────────────
async function analyze() {
  const spo2 = parseFloat(document.getElementById('spo2').value);
  const hr   = parseFloat(document.getElementById('hr').value);
  const hrv  = parseFloat(document.getElementById('hrv').value);

  try {
    const res = await fetch('/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ spo2, hr, hrv })
    });

    if (!res.ok) {
      const err = await res.json();
      alert("Validation Error: " + JSON.stringify(err.detail));
      return;
    }

    const data = await res.json();

    // Update state & UI
    const envInfo = allEnvironments[data.scene] || {};
    applyActiveEnvironment(data.scene, data.comfort_class, envInfo.display_name || data.scene, data.confidence);

    // Update SHAP
    if (data.shap_explanation) {
      updateShap(data.shap_explanation, data.comfort_class);
    }

    // Safety Alert
    const alertBox = document.getElementById('safetyAlert');
    if (data.safety_advisory) {
      alertBox.textContent = data.safety_advisory;
      alertBox.style.display = 'block';
    } else {
      alertBox.style.display = 'none';
    }

    // Refresh Log
    refreshLog();
  } catch (err) {
    console.error("Inference request error:", err);
  }
}

function updateShap(shap, comfortClass) {
  const spo2Val = Math.abs(shap.spo2 || 0);
  const hrVal   = Math.abs(shap.hr || 0);
  const hrvVal  = Math.abs(shap.hrv || 0);

  document.getElementById('shapSpo2Val').textContent = `${spo2Val.toFixed(1)}%`;
  document.getElementById('shapHrVal').textContent   = `${hrVal.toFixed(1)}%`;
  document.getElementById('shapHrvVal').textContent  = `${hrvVal.toFixed(1)}%`;

  document.getElementById('shapSpo2Bar').style.width = `${Math.min(100, spo2Val)}%`;
  document.getElementById('shapHrBar').style.width   = `${Math.min(100, hrVal)}%`;
  document.getElementById('shapHrvBar').style.width  = `${Math.min(100, hrvVal)}%`;

  let topFeature = "HRV";
  let maxVal = hrvVal;
  if (spo2Val > maxVal) { topFeature = "SpO₂ Saturation"; maxVal = spo2Val; }
  if (hrVal > maxVal)   { topFeature = "Heart Rate"; maxVal = hrVal; }

  const driverNotes = {
    calm: "reflects balanced parasympathetic relaxation tone.",
    adjust: "triggered sensory recalibration threshold.",
    support: "detected significant physiological load requiring quiet grounding refuge."
  };

  document.getElementById('shapSummary').innerHTML =
    `Primary physiological driver: <strong>${topFeature} (${maxVal.toFixed(1)}%)</strong> ` +
    (driverNotes[comfortClass] || "influenced AI classification.");
}

// ── Session Log ───────────────────────────────────────────────────────
async function refreshLog() {
  try {
    const res = await fetch('/session-log');
    const data = await res.json();
    const log = data.session_log || [];
    const tbody = document.getElementById('logTbody');

    if (!log.length) return;
    tbody.innerHTML = '';

    const badgeCls = { calm: 'sc-calm', adjust: 'sc-adjust', support: 'sc-support' };

    [...log].reverse().slice(0, 10).forEach(entry => {
      const tr = document.createElement('tr');
      const bCls = badgeCls[entry.comfort_class] || 'sc-calm';
      tr.innerHTML = `
        <td style="color:var(--text-muted); font-weight:600;">${entry.time}</td>
        <td><strong style="color:#38bdf8;">${entry.spo2}%</strong></td>
        <td><strong style="color:#fb7185;">${entry.hr} bpm</strong></td>
        <td><strong style="color:#34d399;">${entry.hrv} ms</strong></td>
        <td><span class="log-badge ${bCls}">${entry.comfort_class.toUpperCase()}</span></td>
        <td style="font-weight:600; color:#f1f5f9;">${entry.scene}</td>
        <td>${entry.confidence}</td>
        <td style="color:#38bdf8; font-weight:600;">${entry.shap_top.toUpperCase()}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {}
}

// ── Custom 360° Photo Upload ──────────────────────────────────────────
async function handleUpload(e) {
  e.preventDefault();
  const fileInput  = document.getElementById('customFile');
  const titleInput = document.getElementById('customTitle');
  const classInput = document.getElementById('customComfortClass');
  const feedback   = document.getElementById('uploadFeedback');
  const btn        = document.getElementById('uploadSubmitBtn');

  if (!fileInput.files.length) {
    alert("Please select a 360° image file (.jpg, .jpeg, .png, or .exr).");
    return;
  }

  const formData = new FormData();
  formData.append('file', fileInput.files[0]);
  formData.append('comfort_class', classInput.value);
  formData.append('title', titleInput.value);

  btn.disabled = true;
  btn.textContent = "Uploading & Mirroring to VR...";
  feedback.style.display = "block";
  feedback.style.background = "rgba(2, 132, 199, 0.2)";
  feedback.style.color = "#38bdf8";
  feedback.textContent = "Transmitting 360° file to backend...";

  try {
    const res = await fetch('/upload-panorama', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Upload failed");
    }

    const data = await res.json();
    feedback.style.background = "rgba(16, 185, 129, 0.2)";
    feedback.style.color = "#34d399";
    feedback.textContent = `✓ Uploaded! Now streaming "${data.display_name}" to VR headset.`;

    await loadEnvironments();
    applyActiveEnvironment(data.scene_name, data.comfort_class, data.display_name, 1.0);
    fileInput.value = "";
    titleInput.value = "";
  } catch (err) {
    feedback.style.background = "rgba(239, 68, 68, 0.2)";
    feedback.style.color = "#fca5a5";
    feedback.textContent = "Upload Error: " + err.message;
  } finally {
    btn.disabled = false;
    btn.textContent = "Upload & Stream to VR Headset ▶";
  }
}

async function deleteCustomPhoto(e, filename) {
  e.stopPropagation();
  if (!confirm(`Delete custom 360° photo "${filename}"?\nThis removes it from the VR headset and server.`)) {
    return;
  }

  try {
    const res = await fetch(`/custom-panorama/${encodeURIComponent(filename)}`, {
      method: 'DELETE'
    });

    if (!res.ok) {
      const err = await res.json();
      alert("Delete Error: " + (err.detail || "Could not delete"));
      return;
    }

    const data = await res.json();
    if (data.reset_to_default) {
      applyActiveEnvironment("Pool", "calm", "Tranquil Pool", 0.98);
    }
    await loadEnvironments();
  } catch (err) {
    alert("Network error: " + err.message);
  }
}

// ── Memory Audio Therapy Functions ──────────────────────────────────
let memoryAudioState = { active: false, filename: "", title: "", audio_url: "" };

async function loadMemoryAudioState() {
  try {
    const res = await fetch('/memory-audio');
    if (res.ok) {
      memoryAudioState = await res.json();
      updateMemoryAudioUI();
    }
  } catch (err) {
    console.error("Error loading memory audio state:", err);
  }
}

function updateMemoryAudioUI() {
  const box = document.getElementById('memoryAudioActiveBox');
  const trackName = document.getElementById('memoryTrackName');
  const trackBadge = document.getElementById('memoryTrackBadge');
  const toggleBtn = document.getElementById('memoryToggleBtn');
  const trackStatus = document.getElementById('memoryTrackStatus');
  const audioTextEl = document.getElementById('activeAudioText');

  if (memoryAudioState && memoryAudioState.filename) {
    box.style.display = 'block';
    trackName.textContent = memoryAudioState.title || memoryAudioState.filename;
    if (memoryAudioState.active) {
      trackBadge.textContent = 'PLAYING';
      trackBadge.style.background = 'rgba(34,197,94,0.2)';
      trackBadge.style.color = '#4ade80';
      trackBadge.style.borderColor = 'rgba(34,197,94,0.4)';
      toggleBtn.textContent = '⏸ Mute Memory Audio';
      trackStatus.textContent = 'Playing across all environments';
      if (audioTextEl) {
        audioTextEl.textContent = `Memory Audio Therapy: ${memoryAudioState.title} (Playing with scenario)`;
      }
    } else {
      trackBadge.textContent = 'MUTED';
      trackBadge.style.background = 'rgba(148,163,184,0.2)';
      trackBadge.style.color = '#94a3b8';
      trackBadge.style.borderColor = 'rgba(148,163,184,0.4)';
      toggleBtn.textContent = '▶ Play Memory Audio';
      trackStatus.textContent = 'Muted — standard environment sounds playing';
      const audioText = envAudioMap[activeSceneName] || "";
      if (audioTextEl && audioText) {
        audioTextEl.textContent = audioText;
      }
    }
  } else {
    box.style.display = 'none';
  }
}

async function handleMemoryAudioUpload(e) {
  e.preventDefault();
  const fileInput  = document.getElementById('memoryAudioFile');
  const titleInput = document.getElementById('memoryAudioTitle');
  const feedback   = document.getElementById('memoryAudioFeedback');
  const btn        = document.getElementById('memoryAudioSubmitBtn');

  if (!fileInput.files.length) {
    alert("Please select an audio file (.mp3, .wav, .ogg, or .m4a).");
    return;
  }

  const formData = new FormData();
  formData.append('file', fileInput.files[0]);
  formData.append('title', titleInput.value);

  btn.disabled = true;
  btn.textContent = "Uploading & Mirroring to VR...";
  feedback.style.display = "block";
  feedback.style.background = "rgba(162, 28, 175, 0.2)";
  feedback.style.color = "#e879f9";
  feedback.textContent = "Transmitting memory audio to backend & VR...";

  try {
    const res = await fetch('/upload-memory-audio', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Upload failed");
    }

    const data = await res.json();
    feedback.style.background = "rgba(16, 185, 129, 0.2)";
    feedback.style.color = "#34d399";
    feedback.textContent = `✓ Uploaded! "${data.title}" is now playing with all scenarios.`;

    memoryAudioState = {
      active: true,
      filename: data.filename,
      title: data.title,
      audio_url: data.audio_url
    };
    updateMemoryAudioUI();
    fileInput.value = "";
    titleInput.value = "";
  } catch (err) {
    feedback.style.background = "rgba(239, 68, 68, 0.2)";
    feedback.style.color = "#fca5a5";
    feedback.textContent = "Upload Error: " + err.message;
  } finally {
    btn.disabled = false;
    btn.textContent = "♫ Upload & Play Memory Audio";
  }
}

async function toggleMemoryAudio() {
  const newActive = !memoryAudioState.active;
  try {
    const res = await fetch('/memory-audio/toggle', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ active: newActive })
    });
    if (res.ok) {
      const data = await res.json();
      memoryAudioState.active = data.active;
      updateMemoryAudioUI();
    }
  } catch (err) {
    alert("Error toggling memory audio: " + err.message);
  }
}

async function deleteMemoryAudio() {
  if (!confirm("Delete this memory audio therapy track?\nStandard environment ambient sound will be restored.")) {
    return;
  }
  try {
    const res = await fetch('/memory-audio', { method: 'DELETE' });
    if (res.ok) {
      memoryAudioState = { active: false, filename: "", title: "", audio_url: "" };
      updateMemoryAudioUI();
      const feedback = document.getElementById('memoryAudioFeedback');
      feedback.style.display = "block";
      feedback.style.background = "rgba(239, 68, 68, 0.15)";
      feedback.style.color = "#fca5a5";
      feedback.textContent = "Memory audio track deleted. Restored environment ambient sound.";
      setTimeout(() => { feedback.style.display = "none"; }, 4000);
    }
  } catch (err) {
    alert("Error deleting memory audio: " + err.message);
  }
}

// ── Startup ───────────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', async () => {
  await loadEnvironments();
  await loadMemoryAudioState();
  analyze();
  setInterval(refreshLog, 4000);
});
</script>
</body>
</html>"""
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    import uvicorn
    print("[Backend] Starting VitaVerse Phase 2 API on http://127.0.0.1:8000...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
