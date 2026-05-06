# 🌊 AquaCare — Waterborne Disease Monitoring & Outbreak Prediction

> AI-powered system for water quality monitoring, contamination detection, and disease outbreak prediction using Computer Vision (YOLOv8) and Machine Learning.

---

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│  React UI   │────▶│  Flask API   │────▶│  YOLO Models   │
│  Dashboard  │◀────│  Backend     │────▶│  ML Model      │
└─────────────┘     └──────────────┘     └────────────────┘
                           │                      │
                    ┌──────▼──────┐         ┌─────▼─────┐
                    │ Alert Svc   │         │  Datasets  │
                    │ (Twilio)    │         │  (CSV/IMG) │
                    └─────────────┘         └───────────┘
```

---

## 📁 Project Structure

```
waterborne_disease_prediction_model/
├── config/                  # Centralized configuration
│   └── settings.py          # All paths, models, thresholds
├── datasets/                # Dataset preparation scripts
│   ├── download_dataset.py  # Auto-download from Kaggle/GDrive
│   ├── prepare_all_datasets.py  # ONE command to prepare all
│   ├── augmentation.py      # Albumentations pipeline
│   ├── synthetic_data.py    # OpenCV synthetic generation
│   └── annotation_guide.md  # How to annotate for YOLO
├── models/
│   ├── yolo/                # YOLOv8 detection pipeline
│   │   ├── train_yolo.py    # Training script
│   │   ├── inference.py     # Run predictions
│   │   └── model_loader.py  # Dynamic model loading
│   ├── ml/                  # ML outbreak prediction
│   │   ├── eda.py           # Exploratory Data Analysis
│   │   ├── feature_engineering.py
│   │   ├── train_ml_model.py # Train RF/XGBoost
│   │   └── predict.py       # Risk prediction
│   └── weights/             # Saved model weights
├── backend/                 # Flask REST API
│   ├── app.py               # Main Flask application
│   ├── routes/              # API endpoints
│   │   ├── detection.py     # POST /predict-image
│   │   ├── prediction.py    # POST /predict-risk
│   │   └── alerts.py        # POST /send-alert
│   └── services/            # Business logic
│       ├── yolo_service.py
│       ├── ml_service.py
│       └── alert_service.py
├── frontend/                # React dashboard
│   ├── src/
│   │   ├── App.js           # Main app with tab navigation
│   │   ├── components/      # UI components
│   │   │   ├── Dashboard.js
│   │   │   ├── ImageUpload.js
│   │   │   ├── RiskPrediction.js
│   │   │   └── AlertPanel.js
│   │   └── services/api.js  # API client
│   └── package.json
├── requirements.txt         # Python dependencies
├── .env.example             # Environment template
└── README.md
```

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.9+ installed
- Node.js 18+ installed
- pip and npm available

### Step 1: Clone & Setup

```bash
cd d:\waterborne_disease_prediction_model

# Create Python virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Mac/Linux

# Install Python dependencies
pip install -r requirements.txt
```

### Step 2: Download the CSV Dataset

Download the dataset from Google Drive:
- **Link:** https://drive.google.com/file/d/1j1gpnsXFDpgUDPy9vry6uI4HP0p8sl3T/view
- **Save to:** `datasets/raw/east_region_india_water_disease_cleaned.csv`

Or run the automated downloader:
```bash
python datasets/download_dataset.py
```

### Step 3: Prepare YOLO Datasets

```bash
python datasets/prepare_all_datasets.py
```

This ONE command will:
- Download all datasets
- Organize into YOLO format (images/train, images/val, labels/train, labels/val)
- Create demo datasets for testing
- Generate YAML config files

### Step 4: Run EDA (Exploratory Data Analysis)

```bash
python models/ml/eda.py
```

Generates distribution plots, correlation heatmaps, and statistics in `outputs/eda/`.

### Step 5: Train ML Model

```bash
python models/ml/train_ml_model.py
```

Trains Random Forest + XGBoost, saves the best model, generates:
- Feature importance plots
- Prediction vs actual plots
- Risk classification demo

### Step 6: Train YOLO Models (Optional)

```bash
# Train a specific model
python models/yolo/train_yolo.py --model algal_bloom --epochs 50

# Train all models
python models/yolo/train_yolo.py --all --epochs 30
```

### Step 7: Start Flask Backend

```bash
python backend/app.py
```

Server starts at: http://localhost:5000

### Step 8: Start React Frontend

```bash
cd frontend
npm install
npm start
```

Frontend starts at: http://localhost:3000

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/predict-image` | Upload image for YOLO detection |
| `POST` | `/predict-risk` | ML outbreak risk prediction |
| `POST` | `/send-alert` | Trigger manual alert |
| `GET`  | `/models` | List available YOLO models |
| `GET`  | `/model-status` | ML model training status |
| `GET`  | `/alerts/history` | Get alert history |
| `GET`  | `/alerts/stats` | Alert statistics |
| `GET`  | `/health` | Health check |

### Example: Predict Risk
```bash
curl -X POST http://localhost:5000/predict-risk \
  -H "Content-Type: application/json" \
  -d '{
    "contaminant_level_ppm": 45.5,
    "ph_level": 6.2,
    "turbidity_ntu": 18.3,
    "dissolved_oxygen_mg_l": 4.5,
    "nitrate_levels": 12.0,
    "lead_concentration": 0.02,
    "bacteria_count_cfu_ml": 750,
    "rainfall": 180.0,
    "temperature": 32.0,
    "sanitation_coverage": 45.0,
    "population_density": 850.0,
    "access_to_clean_water": 55.0
  }'
```

### Example: Detect Image
```bash
curl -X POST http://localhost:5000/predict-image \
  -F "image=@sample_water.jpg" \
  -F "model=water_contamination" \
  -F "confidence=0.25"
```

---

## 🧠 Models

### YOLO Detection Models (5 models)
| Model | Classes | Use Case |
|-------|---------|----------|
| Algal Bloom | harmful_algae, green_algae, blue_green_algae, red_tide | Satellite/water images |
| Fish Disease | epizootic_ulcerative, bacterial_infection, fungal_infection, healthy | Fish images |
| Malaria | parasitized, uninfected | Microscope cell images |
| Micro-Pathogens | e_coli, cholera_vibrio, giardia, cryptosporidium, rotavirus | Microscope images |
| Water Contamination | contaminated, clean, industrial_waste, sewage, chemical_spill | Water sample images |

### ML Prediction Model
- **Algorithm:** Random Forest / XGBoost (best selected automatically)
- **Input:** 12 water quality parameters
- **Output:** Cholera, Typhoid, Diarrheal cases per 100,000
- **Risk Levels:** LOW / MEDIUM / HIGH
- **Explainability:** Feature importance rankings

---

## 📊 Dataset Sources

| Dataset | Source | Purpose |
|---------|--------|---------|
| Water Disease CSV | Google Drive (provided) | ML outbreak prediction |
| Water Quality Images | Kaggle | Water contamination detection |
| Malaria Cell Images | Kaggle | Malaria parasite detection |
| Fish Disease | Kaggle | Fish disease detection |
| Algal Bloom | Kaggle | Algal bloom detection |

**Dataset Size Guide:**
- **Demo:** 25-50 images/class (pipeline testing)
- **Recommended:** 200-500 images/class (academic projects)
- **Production:** 1,000-5,000 images/class (real deployment)

---

## 🚨 Alert System

Alerts are triggered automatically when:
- ML prediction returns **HIGH** risk
- YOLO detects **dangerous** contamination with >50% confidence

**SMS Alerts (Twilio):**
1. Create free account at [twilio.com](https://www.twilio.com/try-twilio)
2. Copy `.env.example` to `.env`
3. Fill in Twilio credentials
4. HIGH risk alerts will send SMS automatically

---

## 📋 Commands Cheat Sheet

```bash
# === Setup ===
pip install -r requirements.txt          # Install Python deps
cd frontend && npm install               # Install React deps

# === Data ===
python datasets/download_dataset.py      # Download datasets
python datasets/prepare_all_datasets.py  # Prepare everything

# === EDA & ML ===
python models/ml/eda.py                  # Run EDA
python models/ml/train_ml_model.py       # Train ML model
python models/ml/predict.py              # Demo prediction

# === YOLO ===
python models/yolo/train_yolo.py --model water_contamination --epochs 50
python models/yolo/train_yolo.py --all --epochs 30
python models/yolo/inference.py --model water_contamination --image sample.jpg
python models/yolo/inference.py --model malaria --camera 0

# === Run System ===
python backend/app.py                    # Start backend (port 5000)
cd frontend && npm start                 # Start frontend (port 3000)
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Object Detection | YOLOv8 (Ultralytics) |
| ML Prediction | Scikit-learn, XGBoost |
| Backend | Flask, Flask-CORS |
| Frontend | React, Recharts |
| Alerts | Twilio SMS API |
| Data Processing | Pandas, NumPy |
| Visualization | Matplotlib, Seaborn |
| Augmentation | Albumentations, OpenCV |

---

## 📄 License

This project is developed for academic purposes (B.Tech Final Year Project).

---

