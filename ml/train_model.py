"""
VitaVerse - Machine Learning Model Trainer
==========================================
Project: VitaVerse — AI-Driven Personalized Virtual Reality for Comfort and Distraction in Palliative Care
Phase: Phase 1 Prototype

This script trains a Scikit-learn RandomForestClassifier on synthetic physiological data.
Outputs:
  - ml/comfort_model.joblib: Serialized trained model
  - ml/model_metadata.json: Performance metrics, feature schema, class mappings, and clinical disclaimer
"""

import os
import json
import argparse
from datetime import datetime
import numpy as np
import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report,
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix
)

# Relative import or fallback for standalone execution
try:
    from ml.generate_demo_data import generate_synthetic_patient_data
except ImportError:
    from generate_demo_data import generate_synthetic_patient_data

FEATURE_NAMES = ["spo2", "hr", "hrv"]
CLASS_TO_SCENE_MAP = {
    "calm": "Garden",
    "adjust": "Forest",
    "support": "LowStimulation"
}

CLINICAL_DISCLAIMER = (
    "EXPERIMENTAL PROTOTYPE NOTICE: This machine learning model was trained strictly on "
    "synthetic, artificially generated demonstration data for academic engineering purposes. "
    "It has NOT been validated with real patient clinical trials and does NOT measure true subjective "
    "patient comfort, nor does it diagnose distress or medical emergency. Do not use for medical decision-making."
)

def train_and_evaluate(
    data_path: str,
    model_output_path: str,
    metadata_output_path: str,
    random_state: int = 42
):
    """
    Trains a RandomForestClassifier on patient physiological data,
    evaluates on a held-out test set, and saves model and metadata.
    """
    # 1. Load or generate dataset
    if os.path.exists(data_path):
        print(f"[Dataset] Loading existing dataset from: {data_path}")
        df = pd.read_csv(data_path)
    else:
        print(f"[Dataset] No existing CSV found at {data_path}. Generating reproducible synthetic dataset...")
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        df = generate_synthetic_patient_data(n_samples=2400, random_state=random_state)
        df.to_csv(data_path, index=False)
        print(f"[Dataset] Generated and saved {len(df)} records to: {data_path}")

    # Validate columns
    missing_cols = [c for c in FEATURE_NAMES + ["comfort_class"] if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Dataset is missing required columns: {missing_cols}")

    X = df[FEATURE_NAMES]
    y = df["comfort_class"]

    # 2. Train/Test Split (80% train, 20% test, stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=random_state, stratify=y
    )

    print(f"\n[Training] Training set size: {len(X_train)} samples")
    print(f"[Evaluation] Test set size: {len(X_test)} samples")

    # 3. Model Initialization and Fitting
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=6,
        min_samples_split=4,
        random_state=random_state,
        class_weight="balanced"
    )
    clf.fit(X_train, y_train)

    # 4. Evaluation
    y_pred = clf.predict(X_test)
    y_pred_proba = clf.predict_proba(X_test)

    acc = accuracy_score(y_test, y_pred)
    prec, rec, f1, _ = precision_recall_fscore_support(y_test, y_pred, average="weighted")
    class_labels = sorted(list(clf.classes_))
    conf_matrix = confusion_matrix(y_test, y_pred, labels=class_labels).tolist()

    report_dict = classification_report(y_test, y_pred, target_names=class_labels, output_dict=True)
    report_text = classification_report(y_test, y_pred, target_names=class_labels)

    feature_importances = {
        name: float(round(imp, 4))
        for name, imp in zip(FEATURE_NAMES, clf.feature_importances_)
    }

    print("\n" + "=" * 65)
    print(" MODEL EVALUATION RESULTS (SYNTHETIC BENCHMARK)")
    print("=" * 65)
    print(report_text)
    print(f"Overall Accuracy:  {acc * 100:.2f}%")
    print(f"Weighted F1-Score: {f1:.4f}")
    print("\nConfusion Matrix (Rows=True, Cols=Pred):")
    print(f"Labels: {class_labels}")
    for row in conf_matrix:
        print(f"  {row}")
    print(f"\nFeature Importances: {feature_importances}")
    print("=" * 65)

    # 5. Persist Model and Metadata
    os.makedirs(os.path.dirname(model_output_path), exist_ok=True)
    joblib.dump(clf, model_output_path)
    print(f"[Artifact] Saved trained model to: {model_output_path}")

    metadata = {
        "model_name": "VitaVerse Comfort Classifier (Phase 1)",
        "model_type": "RandomForestClassifier",
        "training_timestamp": datetime.now().isoformat(),
        "features": FEATURE_NAMES,
        "classes": class_labels,
        "class_to_scene_map": CLASS_TO_SCENE_MAP,
        "feature_importances": feature_importances,
        "metrics": {
            "accuracy": float(round(acc, 4)),
            "weighted_precision": float(round(prec, 4)),
            "weighted_recall": float(round(rec, 4)),
            "weighted_f1": float(round(f1, 4)),
            "confusion_matrix": conf_matrix,
            "detailed_report": report_dict
        },
        "parameter_bounds": {
            "spo2": {"min": 70.0, "max": 100.0, "unit": "%"},
            "hr": {"min": 40.0, "max": 180.0, "unit": "bpm"},
            "hrv": {"min": 5.0, "max": 200.0, "unit": "ms"}
        },
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "disclaimer": CLINICAL_DISCLAIMER
    }

    with open(metadata_output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"[Artifact] Saved model metadata to: {metadata_output_path}")
    print("[Success] Model pipeline training complete.")

def main():
    parser = argparse.ArgumentParser(description="Train VitaVerse comfort classification model.")
    parser.add_argument("--data", type=str, default=None, help="Path to input CSV dataset.")
    parser.add_argument("--model-out", type=str, default=None, help="Output path for .joblib model.")
    parser.add_argument("--meta-out", type=str, default=None, help="Output path for metadata JSON.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = args.data or os.path.join(base_dir, "data", "synthetic_demo_data.csv")
    model_output_path = args.model_out or os.path.join(base_dir, "ml", "comfort_model.joblib")
    metadata_output_path = args.meta_out or os.path.join(base_dir, "ml", "model_metadata.json")

    train_and_evaluate(
        data_path=data_path,
        model_output_path=model_output_path,
        metadata_output_path=metadata_output_path,
        random_state=args.seed
    )

if __name__ == "__main__":
    main()
