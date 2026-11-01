"""
VitaVerse - Unit Tests for Machine Learning Pipeline
====================================================
Tests dataset generation, model training, persistence, and inference.
"""

import os
import pytest
import pandas as pd
import numpy as np
import joblib

from ml.generate_demo_data import generate_synthetic_patient_data, BOUNDS
from ml.train_model import FEATURE_NAMES, CLASS_TO_SCENE_MAP

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "ml", "comfort_model.joblib")
METADATA_PATH = os.path.join(BASE_DIR, "ml", "model_metadata.json")

def test_generate_synthetic_patient_data():
    """Verify synthetic dataset properties, columns, bounds, and balance."""
    df = generate_synthetic_patient_data(n_samples=300, random_state=123)
    assert len(df) == 300
    assert set(FEATURE_NAMES + ["comfort_class"]).issubset(set(df.columns))

    # Verify physiological bounds
    assert df["spo2"].min() >= BOUNDS["spo2"][0]
    assert df["spo2"].max() <= BOUNDS["spo2"][1]
    assert df["hr"].min() >= BOUNDS["hr"][0]
    assert df["hr"].max() <= BOUNDS["hr"][1]
    assert df["hrv"].min() >= BOUNDS["hrv"][0]
    assert df["hrv"].max() <= BOUNDS["hrv"][1]

    # Verify all 3 classes exist
    unique_classes = set(df["comfort_class"].unique())
    assert unique_classes == {"calm", "adjust", "support"}

def test_model_file_exists_and_loads():
    """Verify trained model joblib file exists and can be loaded."""
    assert os.path.exists(MODEL_PATH), "Model artifact comfort_model.joblib missing."
    model = joblib.load(MODEL_PATH)
    assert hasattr(model, "predict"), "Loaded object is not a valid scikit-learn estimator."
    assert hasattr(model, "classes_"), "Model does not possess class attributes."
    assert set(model.classes_) == {"adjust", "calm", "support"}

def test_model_inference_predictions():
    """Verify model produces expected classifications on known prototypical scenarios."""
    model = joblib.load(MODEL_PATH)

    # 1. Prototypical calm: high SpO2, relaxed HR, high HRV
    calm_input = pd.DataFrame([{"spo2": 98.0, "hr": 68.0, "hrv": 75.0}])
    pred_calm = model.predict(calm_input)[0]
    assert pred_calm == "calm"
    assert CLASS_TO_SCENE_MAP[pred_calm] == "Garden"

    # 2. Prototypical adjust: moderate SpO2, elevated HR, moderate HRV
    adjust_input = pd.DataFrame([{"spo2": 94.5, "hr": 88.0, "hrv": 38.0}])
    pred_adjust = model.predict(adjust_input)[0]
    assert pred_adjust == "adjust"
    assert CLASS_TO_SCENE_MAP[pred_adjust] == "Forest"

    # 3. Prototypical support: elevated HR, depressed HRV
    support_input = pd.DataFrame([{"spo2": 90.0, "hr": 115.0, "hrv": 18.0}])
    pred_support = model.predict(support_input)[0]
    assert pred_support == "support"
    assert CLASS_TO_SCENE_MAP[pred_support] == "LowStimulation"
