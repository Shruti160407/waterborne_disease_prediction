"""
============================================
ML Model Training (Adapted for Actual Dataset)
============================================
Trains on the actual CSV with columns:
  Features: temperature, pH, turbidity, dissolved_oxygen, nitrate, 
            coliform_total, coliform_fecal, conductivity, TDS, etc.
  Targets:  outbreak_risk (0/1), risk_score (0-1)

Usage:
    python models/ml/train_ml_model.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
import joblib
import json
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    classification_report, accuracy_score, f1_score,
    mean_squared_error, r2_score, confusion_matrix
)

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

from config.settings import CSV_DATASET_PATH, WEIGHTS_DIR, ML_CONFIG


# ---- Feature columns from actual dataset ----
ACTUAL_FEATURES = [
    "Contaminant Level (ppm)", "pH Level", "Turbidity (NTU)", "Dissolved Oxygen (mg/L)",
    "Nitrate Level (mg/L)", "Lead Concentration (µg/L)", "Bacteria Count (CFU/mL)",
    "Access to Clean Water (% of Population)", "Sanitation Coverage (% of Population)",
    "Rainfall (mm per year)", "Temperature (°C)", "Population Density (people per km²)"
]

# Map from the actual CSV column names to our standardized API input names
REVERSE_COLUMN_MAP = {
    "Contaminant Level (ppm)": "contaminant_level_ppm",
    "pH Level": "ph_level",
    "Turbidity (NTU)": "turbidity_ntu",
    "Dissolved Oxygen (mg/L)": "dissolved_oxygen_mg_l",
    "Nitrate Level (mg/L)": "nitrate_levels",
    "Lead Concentration (µg/L)": "lead_concentration",
    "Bacteria Count (CFU/mL)": "bacteria_count_cfu_ml",
    "Sanitation Coverage (% of Population)": "sanitation_coverage",
    "Population Density (people per km²)": "population_density",
    "Access to Clean Water (% of Population)": "access_to_clean_water",
    "Rainfall (mm per year)": "rainfall",
    "Temperature (°C)": "temperature"
}


def load_and_prepare_data():
    """Load CSV and prepare features/targets."""
    print("=" * 60)
    print("  ML MODEL TRAINING")
    print("=" * 60)
    
    if not CSV_DATASET_PATH.exists():
        print(f"ERROR: CSV not found at {CSV_DATASET_PATH}")
        print("Please place the dataset in datasets/raw/")
        return None, None, None, None

    df = pd.read_csv(str(CSV_DATASET_PATH))
    print(f"Dataset loaded: {df.shape[0]} rows x {df.shape[1]} columns")
    print(f"Columns: {list(df.columns)}")
    
    # Select features that exist in the dataset
    available_features = [f for f in ACTUAL_FEATURES if f in df.columns]
    print(f"Using features: {available_features}")
    
    # Target: outbreak_risk (classification)
    if "outbreak_risk" not in df.columns:
        print("WARNING: 'outbreak_risk' column not found. Creating from target proxy.")
        # Create an outbreak_risk label based on bacteria count and contaminant level
        def determine_risk(row):
            if row.get("Bacteria Count (CFU/mL)", 0) > 1000 or row.get("Contaminant Level (ppm)", 0) > 20:
                return 1
            return 0
            
        df["outbreak_risk"] = df.apply(determine_risk, axis=1)
    
    # Drop rows with NaN in features or target
    subset = df[available_features + ["outbreak_risk"]].dropna()
    print(f"After dropping NaN: {subset.shape[0]} rows")
    
    X = subset[available_features].values
    y = subset["outbreak_risk"].values
    
    print(f"Class distribution: {dict(zip(*np.unique(y, return_counts=True)))}")
    
    return X, y, available_features, df


def train_models(X, y, feature_names):
    """Train multiple models and select the best one."""
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\nTrain: {X_train.shape[0]} samples | Test: {X_test.shape[0]} samples")
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train models
    models = {}
    
    # 1. Random Forest
    print("\n--- Training Random Forest ---")
    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        class_weight="balanced",
        n_jobs=1  # Set to 1 to avoid Windows thread deadlocks in prediction
    )
    rf.fit(X_train_scaled, y_train)
    rf_pred = rf.predict(X_test_scaled)
    rf_acc = accuracy_score(y_test, rf_pred)
    rf_f1 = f1_score(y_test, rf_pred, average="weighted")
    models["RandomForest"] = {"model": rf, "accuracy": rf_acc, "f1": rf_f1}
    print(f"  Accuracy: {rf_acc:.4f} | F1: {rf_f1:.4f}")
    
    # 2. Gradient Boosting
    print("\n--- Training Gradient Boosting ---")
    gb = GradientBoostingClassifier(
        n_estimators=150,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
    )
    gb.fit(X_train_scaled, y_train)
    gb_pred = gb.predict(X_test_scaled)
    gb_acc = accuracy_score(y_test, gb_pred)
    gb_f1 = f1_score(y_test, gb_pred, average="weighted")
    models["GradientBoosting"] = {"model": gb, "accuracy": gb_acc, "f1": gb_f1}
    print(f"  Accuracy: {gb_acc:.4f} | F1: {gb_f1:.4f}")
    
    # 3. XGBoost (if available)
    if HAS_XGB:
        print("\n--- Training XGBoost ---")
        xgb = XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            use_label_encoder=False,
            eval_metric="logloss",
        )
        xgb.fit(X_train_scaled, y_train)
        xgb_pred = xgb.predict(X_test_scaled)
        xgb_acc = accuracy_score(y_test, xgb_pred)
        xgb_f1 = f1_score(y_test, xgb_pred, average="weighted")
        models["XGBoost"] = {"model": xgb, "accuracy": xgb_acc, "f1": xgb_f1}
        print(f"  Accuracy: {xgb_acc:.4f} | F1: {xgb_f1:.4f}")
    
    # Select best model
    best_name = max(models, key=lambda k: models[k]["f1"])
    best_model = models[best_name]["model"]
    best_acc = models[best_name]["accuracy"]
    best_f1 = models[best_name]["f1"]
    
    print(f"\n{'=' * 40}")
    print(f"  BEST MODEL: {best_name}")
    print(f"  Accuracy:   {best_acc:.4f}")
    print(f"  F1 Score:   {best_f1:.4f}")
    print(f"{'=' * 40}")
    
    # Feature importance
    if hasattr(best_model, "feature_importances_"):
        importances = best_model.feature_importances_
        feat_imp = sorted(
            zip(feature_names, importances),
            key=lambda x: x[1], reverse=True
        )
        print("\nFeature Importance:")
        for name, imp in feat_imp:
            bar = "#" * int(imp * 100)
            print(f"  {name:25s} {imp:.4f} {bar}")
    
    # Detailed report
    best_pred = best_model.predict(X_test_scaled)
    print("\nClassification Report:")
    print(classification_report(y_test, best_pred, target_names=["No Outbreak", "Outbreak"]))
    
    return best_model, scaler, best_name, feature_names


def save_model(model, scaler, model_name, feature_names):
    """Save trained model, scaler, and metadata."""
    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save model
    model_path = WEIGHTS_DIR / "outbreak_model.pkl"
    joblib.dump(model, str(model_path))
    print(f"\nModel saved: {model_path}")
    
    # Save scaler
    scaler_path = WEIGHTS_DIR / "feature_scaler.pkl"
    joblib.dump(scaler, str(scaler_path))
    print(f"Scaler saved: {scaler_path}")
    
    # Save metadata
    metadata = {
        "model_type": model_name,
        "feature_names": feature_names,
        "feature_count": len(feature_names),
        "reverse_column_map": REVERSE_COLUMN_MAP,
    }
    
    if hasattr(model, "feature_importances_"):
        metadata["feature_importance"] = {
            name: float(imp) for name, imp in 
            zip(feature_names, model.feature_importances_)
        }
    
    meta_path = WEIGHTS_DIR / "model_metadata.json"
    with open(str(meta_path), "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved: {meta_path}")


def main():
    """Full training pipeline."""
    # Load data
    X, y, feature_names, df = load_and_prepare_data()
    if X is None:
        return
    
    # Train
    model, scaler, model_name, features = train_models(X, y, feature_names)
    
    # Save
    save_model(model, scaler, model_name, features)
    
    # Quick demo prediction
    print("\n" + "=" * 60)
    print("  DEMO PREDICTION")
    print("=" * 60)
    
    # Use a sample from the dataset
    sample = X[0:1]
    sample_scaled = scaler.transform(sample)
    pred = model.predict(sample_scaled)
    proba = model.predict_proba(sample_scaled) if hasattr(model, "predict_proba") else None
    
    print(f"  Sample features: {dict(zip(feature_names, sample[0]))}")
    print(f"  Prediction: {'OUTBREAK RISK' if pred[0] == 1 else 'NO OUTBREAK'}")
    if proba is not None:
        print(f"  Probability: No Outbreak={proba[0][0]:.3f}, Outbreak={proba[0][1]:.3f}")
    
    print("\nTraining complete! Model is ready for predictions.")
    print("Restart Flask backend to use the trained model.")


if __name__ == "__main__":
    main()
