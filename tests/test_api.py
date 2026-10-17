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
