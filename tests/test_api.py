"""
VitaVerse - Unit and Integration Tests for Local FastAPI Service
================================================================
Tests endpoints, validation constraints, and scene mapping logic.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_api_root():
    """Verify root endpoint responds with project metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "VitaVerse" in data["project"]
    assert data["model_loaded"] is True

def test_health_check():
    """Verify health endpoint indicates readiness."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert "RandomForestClassifier" in data["model_type"]

def test_get_scenarios():
    """Verify scenarios endpoint returns demonstration patient profiles."""
    response = client.get("/scenarios")
    assert response.status_code == 200
    data = response.json()
    assert "scenarios" in data
    assert len(data["scenarios"]) == 3

def test_get_metadata():
    """Verify metadata endpoint returns metrics and clinical disclaimer."""
    response = client.get("/metadata")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "disclaimer" in data
    assert "accuracy" in data["metrics"]

def test_predict_calm():
    """Verify prediction for relaxed patient parameters."""
    payload = {"spo2": 98.0, "hr": 68.0, "hrv": 75.0}
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["comfort_class"] == "calm"
    assert data["scene"] == "Pool"
    assert data["demo_only"] is True
    assert data["confidence"] > 0.6

def test_predict_adjust():
    """Verify prediction for mild autonomic fluctuation."""
    payload = {"spo2": 94.5, "hr": 88.0, "hrv": 38.0}
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["comfort_class"] == "adjust"
    assert data["scene"] == "Beach"

def test_predict_support_and_safety_alert():
    """Verify prediction for distressed patient triggers Home and advisory."""
    payload = {"spo2": 89.0, "hr": 115.0, "hrv": 18.0}
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["comfort_class"] == "support"
    assert data["scene"] == "Home"
    # Should include safety alert due to SpO2 < 92%
    assert data["safety_advisory"] is not None
    assert "SAFETY ALERT" in data["safety_advisory"]

def test_validation_error_invalid_spo2():
    """Verify out-of-range SpO2 is rejected with HTTP 422 Unprocessable Entity."""
    # SpO2 cannot exceed 100%
    payload = {"spo2": 115.0, "hr": 70.0, "hrv": 50.0}
    response = client.post("/predict", json=payload)
    assert response.status_code == 422

    # SpO2 cannot be below 70% in this model
    payload_low = {"spo2": 55.0, "hr": 70.0, "hrv": 50.0}
    response_low = client.post("/predict", json=payload_low)
    assert response_low.status_code == 422

def test_validation_error_missing_fields():
    """Verify missing fields return validation error."""
    payload = {"spo2": 98.0}
    response = client.post("/predict", json=payload)
    assert response.status_code == 422

def test_active_environment_get():
    """Verify GET /active-environment returns current scene state."""
    response = client.get("/active-environment")
    assert response.status_code == 200
    data = response.json()
    assert "scene_name" in data
    assert "comfort_class" in data
    assert "scene_file" in data
    assert "timestamp" in data

def test_active_environment_set():
    """Verify POST /active-environment updates the active scene."""
    payload = {
        "scene_name": "BlueLagoon",
        "comfort_class": "calm",
        "scene_file": "blue_lagoon_4k.exr",
        "confidence": 0.95
    }
    response = client.post("/active-environment", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["scene_name"] == "BlueLagoon"
    assert data["comfort_class"] == "calm"
    # Reset back to Pool
    client.post("/active-environment", json={
        "scene_name": "Pool", "comfort_class": "calm", "scene_file": "pool_360.jpg"
    })

def test_get_all_environments():
    """Verify /environments returns all 7 panorama environments."""
    response = client.get("/environments")
    assert response.status_code == 200
    data = response.json()
    assert "environments" in data
    assert data["count"] == 7
    env = data["environments"]
    assert "Pool" in env
    assert "Beach" in env
    assert "Home" in env
    assert "BlueLagoon" in env
    assert "MistyPines" in env
    assert "NightSky" in env
    assert "SunsetFire" in env

def test_predict_returns_shap():
    """Verify /predict response includes SHAP explanation dict."""
    payload = {"spo2": 98.0, "hr": 68.0, "hrv": 75.0}
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "shap_explanation" in data
    shap = data["shap_explanation"]
    assert isinstance(shap, dict)
    assert "spo2" in shap
    assert "hr" in shap
    assert "hrv" in shap

def test_predict_returns_all_scenes_for_class():
    """Verify /predict returns alternative scenes for the predicted class."""
    payload = {"spo2": 98.0, "hr": 68.0, "hrv": 75.0}
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "all_scenes_for_class" in data
    assert isinstance(data["all_scenes_for_class"], list)
    assert len(data["all_scenes_for_class"]) >= 1

def test_session_log():
    """Verify /session-log returns a list after predictions."""
    # Make a prediction first
    client.post("/predict", json={"spo2": 98.0, "hr": 68.0, "hrv": 75.0})
    response = client.get("/session-log")
    assert response.status_code == 200
    data = response.json()
    assert "session_log" in data
    assert isinstance(data["session_log"], list)
    assert len(data["session_log"]) >= 1

def test_upload_panorama_success():
    """Verify clinician can upload an equirectangular 360 photo and it becomes active."""
    dummy_image = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00"
    files = {"file": ("test_garden_360.jpg", dummy_image, "image/jpeg")}
    data = {"comfort_class": "calm", "title": "Patient Childhood Garden"}
    response = client.post("/upload-panorama", files=files, data=data)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert "Patient Childhood Garden" in res_data["display_name"]
    assert "photo_url" in res_data

    # Check active-environment sync
    sync_resp = client.get("/active-environment")
    assert sync_resp.status_code == 200
    sync_data = sync_resp.json()
    assert sync_data["comfort_class"] == "calm"
    assert sync_data["display_name"] == "Patient Childhood Garden"

def test_upload_panorama_invalid_format():
    """Verify uploading non-image format is rejected."""
    dummy_text = b"this is not an image"
    files = {"file": ("malicious.txt", dummy_text, "text/plain")}
    response = client.post("/upload-panorama", files=files, data={"comfort_class": "calm"})
    assert response.status_code == 400

def test_delete_custom_panorama_success():
    """Verify uploaded custom panorama can be deleted and resets to Pool if active."""
    dummy_image = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00"
    files = {"file": ("temporary_custom.jpg", dummy_image, "image/jpeg")}
    up_resp = client.post("/upload-panorama", files=files, data={"comfort_class": "calm", "title": "Temp Custom"})
    assert up_resp.status_code == 200
    file_key = up_resp.json()["file"]

    # Verify present
    env_resp = client.get("/environments")
    assert file_key in env_resp.json()["environments"]

    # Delete it
    del_resp = client.delete(f"/custom-panorama/{file_key}")
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "success"
    assert del_resp.json()["reset_to_default"] is True

    # Verify removed from environments
    env_resp2 = client.get("/environments")
    assert file_key not in env_resp2.json()["environments"]

    # Verify active state fell back to Pool
    sync_resp = client.get("/active-environment")
    assert sync_resp.json()["scene_name"] == "Pool"

def test_delete_non_custom_rejected():
    """Verify safety guard prevents deleting predefined default scenes like Pool or Beach."""
    del_resp = client.delete("/custom-panorama/pool_360.jpg")
    assert del_resp.status_code == 400
    assert "Safety restriction" in del_resp.json()["detail"]

def test_memory_audio_flow_upload_toggle_delete():
    """Verify memory audio therapy upload, active sync, toggle on/off, and deletion."""
    dummy_mp3 = b"ID3\x03\x00\x00\x00\x00\x00\x00dummy-mp3-audio-content"
    files = {"file": ("family_prayer.mp3", dummy_mp3, "audio/mpeg")}
    data = {"title": "Grandmother's Prayer"}
    
    # 1. Upload
    up_resp = client.post("/upload-memory-audio", files=files, data=data)
    assert up_resp.status_code == 200
    res = up_resp.json()
    assert res["status"] == "success"
    assert res["active"] is True
    assert res["title"] == "Grandmother's Prayer"
    assert "audio_url" in res

    # 2. Verify state and active-environment sync
    st_resp = client.get("/memory-audio")
    assert st_resp.status_code == 200
    assert st_resp.json()["active"] is True
    assert st_resp.json()["title"] == "Grandmother's Prayer"

    sync_resp = client.get("/active-environment")
    assert sync_resp.status_code == 200
    assert sync_resp.json()["memory_audio_active"] is True
    assert "family_prayer" in sync_resp.json()["memory_audio_url"]

    # 3. Toggle Mute / Unmute
    tog_resp = client.post("/memory-audio/toggle", json={"active": False})
    assert tog_resp.status_code == 200
    assert tog_resp.json()["active"] is False
    assert client.get("/active-environment").json()["memory_audio_active"] is False

    tog_resp2 = client.post("/memory-audio/toggle", json={"active": True})
    assert tog_resp2.status_code == 200
    assert tog_resp2.json()["active"] is True
    assert client.get("/active-environment").json()["memory_audio_active"] is True

    # 4. Delete
    del_resp = client.delete("/memory-audio")
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "success"

    # Verify reset
    assert client.get("/memory-audio").json()["active"] is False
    assert client.get("/memory-audio").json()["filename"] == ""
    assert client.get("/active-environment").json()["memory_audio_active"] is False

def test_memory_audio_invalid_format():
    """Verify non-audio files are rejected for memory audio therapy."""
    files = {"file": ("document.pdf", b"%PDF-1.4", "application/pdf")}
    resp = client.post("/upload-memory-audio", files=files, data={"title": "Test"})
    assert resp.status_code == 400
    assert "Unsupported audio format" in resp.json()["detail"]
