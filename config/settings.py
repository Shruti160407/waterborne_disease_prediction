"""
============================================
Global Settings & Configuration
============================================
Centralized configuration for the entire system.
All paths, thresholds, and model parameters are defined here.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ---- Base Paths ----
BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "datasets"
RAW_DATA_DIR = DATASET_DIR / "raw"
MODELS_DIR = BASE_DIR / "models"
WEIGHTS_DIR = MODELS_DIR / "weights"
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"
YOLO_CONFIG_DIR = DATASET_DIR / "yolo_configs"

# ---- Dataset Paths ----
CSV_DATASET_PATH = RAW_DATA_DIR / "nort-east_region_india_water_disease_cleaned.csv"
YOLO_DATASET_BASE = DATASET_DIR / "yolo_data"

# ---- YOLO Configuration ----
YOLO_MODELS = {
    "algal_bloom": {
        "name": "Algal Bloom Detection",
        "config": YOLO_CONFIG_DIR / "algal_bloom.yaml",
        "weights": WEIGHTS_DIR / "algal_bloom_best.pt",
        "classes": ["harmful_algae", "green_algae", "blue_green_algae", "red_tide"],
    },
    "fish_disease": {
        "name": "Fish Disease Detection",
        "config": YOLO_CONFIG_DIR / "fish_disease.yaml",
        "weights": WEIGHTS_DIR / "fish_disease_best.pt",
        "classes": ["epizootic_ulcerative", "bacterial_infection", "fungal_infection", "healthy"],
    },
    "malaria": {
        "name": "Malaria Parasite Detection",
        "config": YOLO_CONFIG_DIR / "malaria.yaml",
        "weights": WEIGHTS_DIR / "malaria_best.pt",
        "classes": ["parasitized", "uninfected"],
    },
    "micro_pathogens": {
        "name": "Micro-Pathogens Detection",
        "config": YOLO_CONFIG_DIR / "micro_pathogens.yaml",
        "weights": WEIGHTS_DIR / "micro_pathogens_best.pt",
        "classes": ["e_coli", "cholera_vibrio", "giardia", "cryptosporidium", "rotavirus"],
    },
    "water_contamination": {
        "name": "Water Contamination Detection",
        "config": YOLO_CONFIG_DIR / "water_contamination.yaml",
        "weights": WEIGHTS_DIR / "water_contamination_best.pt",
        "classes": ["contaminated_water", "clean_water", "foam_scum", "floating_debris", "oil_spill", "sewage", "algae_bloom", "industrial_waste", "turbid_water"],
    },
}

# ---- ML Model Configuration ----
ML_CONFIG = {
    "input_features": [
        "contaminant_level_ppm",
        "ph_level",
        "turbidity_ntu",
        "dissolved_oxygen_mg_l",
        "nitrate_levels",
        "lead_concentration",
        "bacteria_count_cfu_ml",
        "rainfall",
        "temperature",
        "sanitation_coverage",
        "population_density",
        "access_to_clean_water",
    ],
    "target_variables": [
        "cholera_cases_per_100000",
        "typhoid_cases_per_100000",
        "diarrheal_cases_per_100000",
    ],
    "model_path": WEIGHTS_DIR / "outbreak_model.pkl",
    "scaler_path": WEIGHTS_DIR / "feature_scaler.pkl",
}

# ---- Column Name Mapping ----
# Maps various possible column names to our standardized names
COLUMN_MAPPING = {
    # Contaminant level
    "contaminant level (ppm)": "contaminant_level_ppm",
    "contaminant_level_ppm": "contaminant_level_ppm",
    "contaminant level": "contaminant_level_ppm",
    "contaminant_level_(ppm)": "contaminant_level_ppm",
    # pH level
    "ph level": "ph_level",
    "ph_level": "ph_level",
    "pH level": "ph_level",
    "ph": "ph_level",
    # Turbidity
    "turbidity (ntu)": "turbidity_ntu",
    "turbidity_ntu": "turbidity_ntu",
    "turbidity (NTU)": "turbidity_ntu",
    "turbidity": "turbidity_ntu",
    "turbidity_(ntu)": "turbidity_ntu",
    # Dissolved oxygen
    "dissolved oxygen (mg/l)": "dissolved_oxygen_mg_l",
    "dissolved_oxygen_mg_l": "dissolved_oxygen_mg_l",
    "dissolved oxygen (mg/L)": "dissolved_oxygen_mg_l",
    "dissolved_oxygen": "dissolved_oxygen_mg_l",
    "dissolved oxygen": "dissolved_oxygen_mg_l",
    "dissolved_oxygen_(mg/l)": "dissolved_oxygen_mg_l",
    # Nitrate
    "nitrate levels": "nitrate_levels",
    "nitrate_levels": "nitrate_levels",
    "nitrate": "nitrate_levels",
    "nitrate_level": "nitrate_levels",
    # Lead
    "lead concentration": "lead_concentration",
    "lead_concentration": "lead_concentration",
    "lead": "lead_concentration",
    # Bacteria count
    "bacteria count (cfu/ml)": "bacteria_count_cfu_ml",
    "bacteria_count_cfu_ml": "bacteria_count_cfu_ml",
    "bacteria count (CFU/mL)": "bacteria_count_cfu_ml",
    "bacteria_count": "bacteria_count_cfu_ml",
    "bacteria count": "bacteria_count_cfu_ml",
    "bacteria_count_(cfu/ml)": "bacteria_count_cfu_ml",
    # Rainfall
    "rainfall": "rainfall",
    "rainfall_mm": "rainfall",
    "rainfall (mm)": "rainfall",
    # Temperature
    "temperature": "temperature",
    "temperature_c": "temperature",
    "temperature (°c)": "temperature",
    "temperature (c)": "temperature",
    # Sanitation
    "sanitation coverage": "sanitation_coverage",
    "sanitation_coverage": "sanitation_coverage",
    "sanitation coverage (%)": "sanitation_coverage",
    "sanitation_coverage_%": "sanitation_coverage",
    # Population density
    "population density": "population_density",
    "population_density": "population_density",
    "population density (per km²)": "population_density",
    # Access to clean water
    "access to clean water": "access_to_clean_water",
    "access_to_clean_water": "access_to_clean_water",
    "access to clean water (%)": "access_to_clean_water",
    "clean_water_access": "access_to_clean_water",
    # Cholera
    "cholera cases per 100,000": "cholera_cases_per_100000",
    "cholera_cases_per_100000": "cholera_cases_per_100000",
    "cholera cases per 100000": "cholera_cases_per_100000",
    "cholera_cases": "cholera_cases_per_100000",
    "cholera cases": "cholera_cases_per_100000",
    # Typhoid
    "typhoid cases per 100,000": "typhoid_cases_per_100000",
    "typhoid_cases_per_100000": "typhoid_cases_per_100000",
    "typhoid cases per 100000": "typhoid_cases_per_100000",
    "typhoid_cases": "typhoid_cases_per_100000",
    "typhoid cases": "typhoid_cases_per_100000",
    # Diarrheal
    "diarrheal cases per 100,000": "diarrheal_cases_per_100000",
    "diarrheal_cases_per_100000": "diarrheal_cases_per_100000",
    "diarrheal cases per 100000": "diarrheal_cases_per_100000",
    "diarrheal_cases": "diarrheal_cases_per_100000",
    "diarrheal cases": "diarrheal_cases_per_100000",
}

# ---- Risk Thresholds ----
RISK_THRESHOLDS = {
    "cholera_cases_per_100000": {"low": 10, "medium": 50, "high": 100},
    "typhoid_cases_per_100000": {"low": 20, "medium": 80, "high": 150},
    "diarrheal_cases_per_100000": {"low": 50, "medium": 200, "high": 500},
}

# ---- Twilio Configuration ----
TWILIO_CONFIG = {
    "account_sid": os.getenv("TWILIO_ACCOUNT_SID", ""),
    "auth_token": os.getenv("TWILIO_AUTH_TOKEN", ""),
    "phone_number": os.getenv("TWILIO_PHONE_NUMBER", ""),
    "alert_phone": os.getenv("ALERT_PHONE_NUMBER", ""),
}

# ---- Flask Configuration ----
FLASK_CONFIG = {
    "host": os.getenv("FLASK_HOST", "0.0.0.0"),
    "port": int(os.getenv("FLASK_PORT", 5000)),
    # Default to False for production safety; set FLASK_DEBUG=True locally
    "debug": os.getenv("FLASK_DEBUG", "False").lower() == "true",
    # No hardcoded fallback — must be set via environment variable in production
    "secret_key": os.getenv("SECRET_KEY", "dev-only-insecure-key-change-me"),
}

# Guard: warn loudly if running in production without a proper secret key
if not os.getenv("FLASK_DEBUG", "False").lower() == "true" and \
   FLASK_CONFIG["secret_key"] == "dev-only-insecure-key-change-me":
    import warnings
    warnings.warn(
        "WARNING: SECRET_KEY is not set via environment variable! "
        "Set SECRET_KEY before deploying to production.",
        stacklevel=2,
    )

# ---- Create directories on import ----
for directory in [RAW_DATA_DIR, WEIGHTS_DIR, YOLO_DATASET_BASE, YOLO_CONFIG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
