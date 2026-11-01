"""
VitaVerse - Synthetic Demonstration Data Generator
==================================================
Project: VitaVerse — AI-Driven Personalized Virtual Reality for Comfort and Distraction in Palliative Care
Phase: Phase 1 Prototype

IMPORTANT NOTICE / CLINICAL DISCLAIMER:
This script generates ARTIFICIAL DEMONSTRATION DATA for academic research and software prototyping.
This dataset is NOT derived from real clinical trials or validated patient records.
It must NOT be used for clinical decision-making, medical diagnosis, or treatment planning.
"""

import os
import argparse
import numpy as np
import pandas as pd

# Default bounds for physiological parameters
BOUNDS = {
    "spo2": (70.0, 100.0),
    "hr": (40.0, 180.0),
    "hrv": (5.0, 200.0)
}

def generate_synthetic_patient_data(n_samples: int = 2400, random_state: int = 42) -> pd.DataFrame:
    """
    Generate synthetic physiological readings mapped to three demonstration comfort classes:
      - 'calm': Stable SpO2 (96-99%), resting HR (60-80 bpm), healthy HRV (50-100 ms)
      - 'adjust': Moderate SpO2 (93-96%), mild HR elevation (80-100 bpm), moderate HRV (30-50 ms)
      - 'support': Compromised SpO2 (<93%), elevated HR (>100 bpm), or depressed HRV (<30 ms)

    Args:
        n_samples: Total number of synthetic records to generate.
        random_state: Seed for reproducibility.

    Returns:
        pd.DataFrame containing ['spo2', 'hr', 'hrv', 'comfort_class']
    """
    rng = np.random.RandomState(random_state)
    n_per_class = n_samples // 3

    # 1. Calm Class
    # Patient is in a stable, comfortable physiological state
    calm_spo2 = rng.normal(loc=97.5, scale=1.0, size=n_per_class)
    calm_hr = rng.normal(loc=68.0, scale=5.0, size=n_per_class)
    calm_hrv = rng.normal(loc=72.0, scale=12.0, size=n_per_class)
    calm_labels = ["calm"] * n_per_class

    # 2. Adjust Class
    # Patient shows mild autonomic fluctuations or mild discomfort
    adjust_spo2 = rng.normal(loc=94.5, scale=1.2, size=n_per_class)
    adjust_hr = rng.normal(loc=88.0, scale=6.0, size=n_per_class)
    adjust_hrv = rng.normal(loc=38.0, scale=6.0, size=n_per_class)
    adjust_labels = ["adjust"] * n_per_class

    # 3. Support Class (Low-Stimulation Needed)
    # Patient shows signs of physiological strain or low autonomic variability
    # Sub-case A: Tachycardia + Low HRV
    n_support_a = n_per_class // 2
    support_a_spo2 = rng.normal(loc=93.0, scale=2.0, size=n_support_a)
    support_a_hr = rng.normal(loc=112.0, scale=8.0, size=n_support_a)
    support_a_hrv = rng.normal(loc=20.0, scale=5.0, size=n_support_a)

    # Sub-case B: Hypoxemia / Low SpO2 strain
    n_support_b = n_per_class - n_support_a
    support_b_spo2 = rng.normal(loc=89.5, scale=2.5, size=n_support_b)
    support_b_hr = rng.normal(loc=95.0, scale=10.0, size=n_support_b)
    support_b_hrv = rng.normal(loc=24.0, scale=6.0, size=n_support_b)

    support_spo2 = np.concatenate([support_a_spo2, support_b_spo2])
    support_hr = np.concatenate([support_a_hr, support_b_hr])
    support_hrv = np.concatenate([support_a_hrv, support_b_hrv])
    support_labels = ["support"] * n_per_class

    # Combine all records
    spo2 = np.concatenate([calm_spo2, adjust_spo2, support_spo2])
    hr = np.concatenate([calm_hr, adjust_hr, support_hr])
    hrv = np.concatenate([calm_hrv, adjust_hrv, support_hrv])
    labels = calm_labels + adjust_labels + support_labels

    # Add minor measurement noise (simulating realistic sensor fluctuation)
    spo2 += rng.normal(loc=0.0, scale=0.3, size=len(spo2))
    hr += rng.normal(loc=0.0, scale=1.5, size=len(hr))
    hrv += rng.normal(loc=0.0, scale=2.0, size=len(hrv))

    # Clip to clinically plausible bounds
    spo2 = np.clip(np.round(spo2, 1), BOUNDS["spo2"][0], BOUNDS["spo2"][1])
    hr = np.clip(np.round(hr, 1), BOUNDS["hr"][0], BOUNDS["hr"][1])
    hrv = np.clip(np.round(hrv, 1), BOUNDS["hrv"][0], BOUNDS["hrv"][1])

    df = pd.DataFrame({
        "spo2": spo2,
        "hr": hr,
        "hrv": hrv,
        "comfort_class": labels
    })

    # Shuffle dataset
    df = df.sample(frac=1.0, random_state=random_state).reset_index(drop=True)
    return df

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic demonstration physiological dataset.")
    parser.add_argument("--samples", type=int, default=2400, help="Number of records to generate.")
    parser.add_argument("--output", type=str, default=None, help="Output CSV path.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = args.output or os.path.join(base_dir, "data", "synthetic_demo_data.csv")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df = generate_synthetic_patient_data(n_samples=args.samples, random_state=args.seed)
    df.to_csv(output_path, index=False)

    print("=" * 65)
    print(" VitaVerse - Synthetic Demo Data Generator")
    print("=" * 65)
    print(f"Generated {len(df)} synthetic patient records.")
    print(f"Saved to: {output_path}")
    print("\nClass distribution:")
    print(df["comfort_class"].value_counts().to_string())
    print("\nSummary statistics:")
    print(df.groupby("comfort_class").mean().round(2).to_string())
    print("=" * 65)
    print("NOTICE: Artificial demonstration data. Not for clinical use.")
    print("=" * 65)

if __name__ == "__main__":
    main()
