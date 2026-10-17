# VitaVerse — Phase 1 Complete

## AI-Based Comfort Classification & Immersive 360° VR Panoramas in Unity

> **Project Title:** VitaVerse — AI-Driven Personalized Virtual Reality for Comfort and Distraction in Palliative Care  
> **Course:** Final Year B.Tech in Artificial Intelligence and Data Science  
> **Phase:** Phase 1 — **COMPLETED**  
> **Unity Version:** Unity 6 (`6000.6.6f1`)  
> **Platform:** Windows 10 / 11 (100% Free & Local — Zero Cloud, Zero Paid APIs)

---

## 1. What Was Done (Phase 1)

| # | Deliverable | Status |
|---|---|---|
| 1 | Synthetic physiological dataset (2,400 records, 3 classes) | ✅ Done |
| 2 | RandomForestClassifier training pipeline with evaluation metrics | ✅ Done |
| 3 | Serialized model (`comfort_model.joblib`) + metadata JSON | ✅ Done |
| 4 | FastAPI REST backend (`/predict`, `/health`, `/scenarios`, `/metadata`, `/demo`) | ✅ Done |
| 5 | Input validation with physiological bounds checking | ✅ Done |
| 6 | Safety advisory system (SpO₂ < 92% or HR outside safe range) | ✅ Done |
| 7 | Interactive web test dashboard at `/demo` | ✅ Done |
| 8 | Unity 6 VR client with 360° equirectangular panoramic skybox | ✅ Done |
| 9 | Three HDR-tonemapped 360° panorama environments (Pool, Beach, Home) | ✅ Done |
| 10 | Glassmorphic Healthcare HUD with vitals, scenarios, and status | ✅ Done |
| 11 | Unity ↔ Python API HTTP communication | ✅ Done |
| 12 | One-click Unity scene setup via Editor menu | ✅ Done |
| 13 | VR Camera Controller (mouse drag 360° + keyboard) | ✅ Done |
| 14 | Procedural fallback sky generator if panoramas are missing | ✅ Done |
| 15 | Automated test suite (9 tests) | ✅ Done |
| 16 | One-click `.bat` launchers for training, server, and tests | ✅ Done |

---

## 2. Project Structure & File Descriptions

```
VitaVerse/
│
├── README.md                    ← This file
├── requirements.txt             ← Python packages needed (pip install -r)
├── run_backend.bat              ← Double-click to start FastAPI server on localhost:8000
├── train_model.bat              ← Double-click to generate dataset + train ML model
├── run_tests.bat                ← Double-click to run all automated tests
│
├── data/
│   └── synthetic_demo_data.csv  ← 2,400 synthetic patient records
│                                   Columns: spo2, hr, hrv, comfort_class
│                                   800 records per class (calm, adjust, support)
│                                   Generated using Gaussian distributions with sensor noise
│
├── ml/
│   ├── generate_demo_data.py    ← Creates synthetic physiological data
│   │                               Uses numpy normal distributions for each class
│   │                               Adds sensor noise, clips to physiological bounds
│   │                               Outputs: data/synthetic_demo_data.csv
│   │
│   ├── train_model.py           ← Trains the RandomForestClassifier
│   │                               80/20 stratified train-test split
│   │                               Evaluates accuracy, F1-score, confusion matrix
│   │                               Outputs: comfort_model.joblib + model_metadata.json
│   │
│   ├── comfort_model.joblib     ← Trained model binary file (~579 KB)
│   │                               Loaded by the FastAPI backend for inference
│   │
│   └── model_metadata.json      ← Training results: accuracy (97.29%), F1 (0.9729),
│                                   confusion matrix, feature importances, bounds
│
├── backend/
│   ├── __init__.py              ← Python package marker
│   │
│   ├── main.py                  ← FastAPI application (661 lines), contains:
│   │                               • PatientInput schema with Pydantic validators
│   │                               • POST /predict — runs ML inference, maps to scene
│   │                               • GET /health — checks if model is loaded
│   │                               • GET /scenarios — returns 3 demo patient profiles
│   │                               • GET /metadata — returns training metrics
│   │                               • GET /demo — interactive web dashboard (HTML/CSS/JS)
│   │                               • Safety advisory logic (SpO₂ < 92%, HR outliers)
│   │                               • CORS middleware for Unity HTTP requests
│   │
│   └── requirements.txt         ← Backend-specific dependency list
│
├── tests/
│   ├── test_model.py            ← ML pipeline tests (3 tests):
│   │                               • Validates dataset shape, columns, bounds, balance
│   │                               • Verifies .joblib file loads correctly
│   │                               • Checks predictions on known input scenarios
│   │
│   └── test_api.py              ← API integration tests (6 tests):
│                                   • Root, health, scenarios, metadata endpoints
│                                   • Correct classification for calm/adjust/support
│                                   • Validation errors for out-of-range & missing fields
│
└── unity/
    └── VitaVerseVR/              ← Unity 6 Project (6000.6.6f1)
        ├── ProjectSettings/
        │   └── ProjectVersion.txt
        │
        └── Assets/
            ├── Panoramas/
            │   ├── pool_360.jpg           ← 4096×2048 — Tranquil Pool (calm)
            │   │                             Tonemapped from pool_8k.exr (HDR source)
            │   ├── beach_360.jpg          ← 4096×2048 — Umhlanga Beach Sunrise (adjust)
            │   │                             Tonemapped from umhlanga_sunrise_8k.exr
            │   ├── home_360.jpg           ← 3840×1920 — Kerala Heritage Home (support)
            │   │                             Source: VirtualTourEasy (Bfn4KNHKvK)
            │   ├── pool_8k.exr            ← 8K HDR source (~73 MB)
            │   ├── umhlanga_sunrise_8k.exr ← 8K HDR source (~70 MB)
            │   └── README.txt             ← Panorama mapping notes
            │
            └── Scripts/
                ├── ComfortManager.cs      ← Master coordinator
                │                             Bridges HUD ↔ API ↔ Scene switching
                │                             Receives prediction result, triggers
                │                             environment switch + HUD update
                │
                ├── ApiConnectionManager.cs ← HTTP client for localhost:8000
                │                             Sends UnityWebRequest to /health and /predict
                │                             Parses JSON, handles errors (422, 503, timeout)
                │
                ├── SceneEnvironmentManager.cs ← 360° panorama manager
                │                                Maps comfort class → panorama texture
                │                                Applies Skybox/Panoramic shader
                │                                Sets lighting, fog, ambient per environment
                │                                Auto-loads JPGs from Assets/Panoramas/
                │
                ├── HealthcareHUD.cs        ← Glassmorphic UI (built at runtime)
                │                             Vital sign sliders (SpO₂, HR, HRV)
                │                             Predict button, 3 scenario pills
                │                             Comfort badge, safety banner, status bar
                │                             Animated heart pulse, [H] hide/show
                │
                ├── VRCameraController.cs   ← 360° camera controller
                │                             Mouse drag + Arrow/WASD keys
                │                             Full 360° yaw, ±75° pitch
                │                             [R] reset view, smooth interpolation
                │
                ├── PanoramicSkyGenerator.cs ← Procedural fallback sky generator
                │                             Creates 360° panoramas if JPGs are missing
                │                             Uses Rayleigh scattering, mountain silhouettes
                │
                ├── UIAssetGenerator.cs     ← Runtime UI texture generator
                │                             Creates rounded rects, glow borders, circles
                │                             No paid assets needed
                │
                └── Editor/
                    └── VitaVerseSceneSetup.cs ← Adds "VitaVerse → Auto-Setup Scene"
                                                 menu for one-click scene construction
```

---

## 3. How to Run on Another System

### Step 1 — Install Python

1. Download **Python 3.10, 3.11, or 3.12** from [python.org/downloads](https://www.python.org/downloads/)
2. Run installer — **check "Add python.exe to PATH"**
3. Verify in PowerShell:
   ```powershell
   python --version
   ```

### Step 2 — Install Unity Hub & Unity Editor

1. Download **Unity Hub** from [unity.com/download](https://unity.com/download)
2. Install Unity Hub → Sign in (free account)
3. Go to **Installs** tab → **Install Editor**
4. Select **Unity 6 (6000.x.x)** or **Unity 2022.3 LTS**
   - Project was built on `6000.6.6f1` but works with 2021.3+

### Step 3 — Download the Project

**Option A:** Click **Code → Download ZIP** on GitHub, then extract it

**Option B:**
```powershell
git clone <repository-url>
cd VitaVerse
```

### Step 4 — Install Python Dependencies

```powershell
cd VitaVerse
pip install -r requirements.txt
```

This installs: `fastapi`, `uvicorn`, `scikit-learn`, `pandas`, `numpy`, `joblib`, `pytest`, `requests`

### Step 5 — Train the ML Model

Double-click **`train_model.bat`** or run:
```powershell
python ml/generate_demo_data.py
python ml/train_model.py
```

This generates 2,400 records and trains the model (~97% accuracy).

### Step 6 — Run Tests (Optional)

```powershell
python -m pytest tests/ -v
```

All 9 tests should pass.

### Step 7 — Start the Backend Server

Double-click **`run_backend.bat`** or run:
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

**Keep this terminal open** — Unity connects to it.

### Step 8 — Open Unity Project

1. Open **Unity Hub** → **Projects** → **Add project from disk**
2. Select: `VitaVerse/unity/VitaVerseVR`
3. Click **Open** (first load takes 2–5 minutes)

### Step 9 — Setup the Scene

In Unity top menu:
```
VitaVerse → Auto-Setup Scene (One-Click)
```

### Step 10 — Play

1. Confirm backend terminal is running
2. Click **▶ Play** in Unity
3. Use the scenario buttons on the HUD to test:
   - **Scenario 1** → `calm` → Tranquil Pool panorama
   - **Scenario 2** → `adjust` → Beach Sunrise panorama
   - **Scenario 3** → `support` → Kerala Home panorama

**Controls:**

| Key | Action |
|---|---|
| Click & Drag | Look around 360° |
| Arrow Keys / WASD | Pan and tilt |
| R | Reset view |
| H | Hide/show HUD |
| Escape | Pause session |

---

## 4. Dataset

The file `data/synthetic_demo_data.csv` contains **2,400 artificially generated** patient records. This is **NOT real clinical data**.

### Columns

| Column | Type | Unit | Range | Description |
|---|---|---|---|---|
| `spo2` | float | % | 70–100 | Blood oxygen saturation |
| `hr` | float | bpm | 40–180 | Heart rate |
| `hrv` | float | ms | 5–200 | Heart rate variability |
| `comfort_class` | string | — | calm / adjust / support | Target label |

### How the Data is Generated

Each class uses **Gaussian (normal) distributions** with different centers:

**Calm** (800 records) — stable, comfortable patient:
```
SpO₂ ~ Normal(mean=97.5, std=1.0)
HR   ~ Normal(mean=68.0,  std=5.0)
HRV  ~ Normal(mean=72.0,  std=12.0)
```

**Adjust** (800 records) — mild restlessness:
```
SpO₂ ~ Normal(mean=94.5, std=1.2)
HR   ~ Normal(mean=88.0,  std=6.0)
HRV  ~ Normal(mean=38.0,  std=6.0)
```

**Support** (800 records) — two sub-populations combined:
```
Sub-A (Tachycardia):
    SpO₂ ~ Normal(mean=93.0, std=2.0)
    HR   ~ Normal(mean=112.0, std=8.0)
    HRV  ~ Normal(mean=20.0,  std=5.0)

Sub-B (Hypoxemia):
    SpO₂ ~ Normal(mean=89.5, std=2.5)
    HR   ~ Normal(mean=95.0,  std=10.0)
    HRV  ~ Normal(mean=24.0,  std=6.0)
```

After generation, **sensor noise** is added (SpO₂ ±0.3, HR ±1.5, HRV ±2.0) and values are **clipped** to physiological bounds.

---

## 5. How the Classification Works

### Algorithm

**Scikit-learn RandomForestClassifier** — an ensemble of 100 decision trees.

### Model Parameters

| Parameter | Value |
|---|---|
| `n_estimators` | 100 (number of trees) |
| `max_depth` | 6 |
| `min_samples_split` | 4 |
| `class_weight` | balanced |
| `random_state` | 42 |

### How It Classifies

1. **Input:** 3 features → `[SpO₂, HR, HRV]`

2. **Each tree** makes an independent decision by following learned rules:
   ```
   Example tree node: "Is HRV ≤ 45 ms?"
       YES → lean toward "adjust" or "support"
       NO  → lean toward "calm"
   ```

3. **Majority vote** — all 100 trees vote, the most common answer wins:
   ```
   Prediction = mode(tree₁, tree₂, ..., tree₁₀₀)
   ```

4. **Confidence** — fraction of trees agreeing:
   ```
   Confidence = (votes for winning class) / 100
   ```

5. **Probabilities** for each class:
   ```
   P(calm)    = trees voting calm / 100
   P(adjust)  = trees voting adjust / 100
   P(support) = trees voting support / 100
   ```

### Feature Importances

How much each vital sign contributes to decisions:

| Feature | Importance | Meaning |
|---|---|---|
| HRV | 38.2% | Most discriminative — low HRV strongly indicates "support" |
| HR | 31.8% | Elevated HR correlates with "adjust" and "support" |
| SpO₂ | 30.0% | Low SpO₂ separates "support" from others |

### Evaluation Results (on 480 test samples)

| Metric | Value |
|---|---|
| Accuracy | 97.29% |
| Weighted F1-Score | 0.9729 |
| Weighted Precision | 0.9731 |
| Weighted Recall | 0.9729 |

### Per-Class Performance

| Class | Precision | Recall | F1-Score |
|---|---|---|---|
| calm | 1.00 | 0.99 | 0.997 |
| adjust | 0.97 | 0.95 | 0.959 |
| support | 0.95 | 0.98 | 0.963 |

### Confusion Matrix

```
                Predicted
             adjust  calm  support
Actual adjust  [152     0      8]
       calm    [  1   159      0]
       support [  4     0    156]
```

---

## 6. Workflow

```
User clicks Scenario       Unity sends HTTP POST       Python backend runs
button on Healthcare  ───▶  to localhost:8000/predict  ───▶  RandomForest model
HUD (or adjusts           with {spo2, hr, hrv}            on the 3 features
sliders manually)                                              │
                                                               ▼
Unity switches 360°    ◀───  JSON response with         Classification result:
panorama skybox              comfort_class, scene,       "calm" / "adjust" /
+ updates lighting           confidence, advisory        "support"
+ updates HUD badge
```

### Classification → Scene Mapping

| Predicted Class | Scene Name | Panorama File | What the Patient Sees |
|---|---|---|---|
| `calm` | Tranquil Pool | `pool_360.jpg` | Crystal azure water, bright daylight |
| `adjust` | Umhlanga Beach Sunrise | `beach_360.jpg` | Golden sunrise over ocean waves |
| `support` | Kerala Heritage Home | `home_360.jpg` | Teakwood architecture, courtyard light |

---

## 7. 360° Panorama Environments

Three equirectangular panorama images projected onto Unity's `Skybox/Panoramic` shader. The user is placed at the center and can look in any direction.

### Pool (Calm)

| Property | Value |
|---|---|
| File | `pool_360.jpg` (4096 × 2048) |
| Source | `pool_8k.exr` — tonemapped 8K HDR |
| Lighting | Bright white, intensity 1.15 |
| Fog | Light aqua, density 0.0015 |
| Purpose | Relaxation for stable patients |

### Beach (Adjust)

| Property | Value |
|---|---|
| File | `beach_360.jpg` (4096 × 2048) |
| Source | `umhlanga_sunrise_8k.exr` — Poly Haven HDR |
| Lighting | Warm golden, intensity 1.25 |
| Fog | Marine haze, density 0.0018 |
| Purpose | Sensory recalibration for restlessness |

### Home (Support)

| Property | Value |
|---|---|
| File | `home_360.jpg` (3840 × 1920) |
| Source | [VirtualTourEasy](https://viewer.virtualtoureasy.com/?r=Bfn4KNHKvK) |
| Lighting | Warm amber, intensity 0.65 |
| Fog | Dense warm, density 0.003 |
| Purpose | Low-stimulation refuge for elevated stress |

---

## 8. Safety & Disclaimer

> **⚠️ ACADEMIC PROTOTYPE — NOT A MEDICAL DEVICE**
>
> This is a B.Tech Final Year Project. The model was trained on **synthetic data only**. It has NOT been clinically validated and must NOT replace medical judgment.
