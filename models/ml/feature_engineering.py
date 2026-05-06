"""
============================================
Feature Engineering Module
============================================
Processes raw features for the ML outbreak prediction model.
Handles column mapping, scaling, and feature transformations.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import joblib

from config.settings import ML_CONFIG, COLUMN_MAPPING, WEIGHTS_DIR


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map various column naming conventions to standardized names.
    
    Handles differences like:
    - "contaminant level (ppm)" → "contaminant_level_ppm"
    - "pH level" → "ph_level"
    - etc.
    
    Args:
        df: Raw DataFrame
        
    Returns:
        DataFrame with standardized column names
    """
    new_columns = {}
    for col in df.columns:
        col_stripped = col.strip()
        col_lower = col_stripped.lower()
        
        matched = False
        for key, value in COLUMN_MAPPING.items():
            if key.lower() == col_lower:
                new_columns[col] = value
                matched = True
                break
        
        if not matched:
            # Fuzzy matching: check if key is contained in column name
            for key, value in COLUMN_MAPPING.items():
                if key.lower() in col_lower or col_lower in key.lower():
                    new_columns[col] = value
                    matched = True
                    break
        
        if not matched:
            clean = col_stripped.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_").replace(",", "")
            new_columns[col] = clean
    
    return df.rename(columns=new_columns)


def extract_features(df: pd.DataFrame) -> tuple:
    """
    Extract input features and target variables from the dataset.
    
    Args:
        df: DataFrame with standardized column names
        
    Returns:
        Tuple of (X features DataFrame, y targets DataFrame, feature_names, target_names)
    """
    # Find available feature columns
    available_features = []
    for feat in ML_CONFIG["input_features"]:
        if feat in df.columns:
            available_features.append(feat)
        else:
            print(f"  ⚠️  Feature not found: {feat}")
    
    # Find available target columns
    available_targets = []
    for target in ML_CONFIG["target_variables"]:
        if target in df.columns:
            available_targets.append(target)
        else:
            print(f"  ⚠️  Target not found: {target}")
    
    if not available_features:
        raise ValueError("No input features found in dataset! Check column names.")
    
    if not available_targets:
        raise ValueError("No target variables found in dataset! Check column names.")
    
    print(f"  📋 Input features ({len(available_features)}): {available_features}")
    print(f"  🎯 Target variables ({len(available_targets)}): {available_targets}")
    
    X = df[available_features].copy()
    y = df[available_targets].copy()
    
    return X, y, available_features, available_targets


def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create additional engineered features to improve model performance.
    
    New features:
    - water_quality_index: Composite score from multiple parameters
    - contamination_risk_score: Combined contamination indicator
    - infrastructure_score: Sanitation + clean water access
    
    Args:
        df: DataFrame with standardized columns
        
    Returns:
        DataFrame with additional engineered features
    """
    df = df.copy()
    
    # Water Quality Index (composite of key parameters)
    if all(col in df.columns for col in ["ph_level", "turbidity_ntu", "dissolved_oxygen_mg_l"]):
        # Normalize each parameter to 0-1 and combine
        ph_score = 1 - abs(df["ph_level"] - 7.0) / 7.0  # Ideal pH is 7
        turb_score = 1 - (df["turbidity_ntu"] / df["turbidity_ntu"].max())  # Lower is better
        do_score = df["dissolved_oxygen_mg_l"] / df["dissolved_oxygen_mg_l"].max()  # Higher is better
        
        df["water_quality_index"] = (ph_score + turb_score + do_score) / 3
        print("  🔧 Added: water_quality_index")
    
    # Contamination Risk Score
    if all(col in df.columns for col in ["contaminant_level_ppm", "bacteria_count_cfu_ml", "lead_concentration"]):
        cont_norm = df["contaminant_level_ppm"] / df["contaminant_level_ppm"].max()
        bact_norm = df["bacteria_count_cfu_ml"] / df["bacteria_count_cfu_ml"].max()
        lead_norm = df["lead_concentration"] / df["lead_concentration"].max()
        
        df["contamination_risk_score"] = (cont_norm + bact_norm + lead_norm) / 3
        print("  🔧 Added: contamination_risk_score")
    
    # Infrastructure Score
    if all(col in df.columns for col in ["sanitation_coverage", "access_to_clean_water"]):
        df["infrastructure_score"] = (df["sanitation_coverage"] + df["access_to_clean_water"]) / 2
        print("  🔧 Added: infrastructure_score")
    
    # Environmental Risk
    if all(col in df.columns for col in ["rainfall", "temperature", "population_density"]):
        rain_norm = df["rainfall"] / df["rainfall"].max()
        temp_norm = df["temperature"] / df["temperature"].max()
        pop_norm = df["population_density"] / df["population_density"].max()
        
        df["environmental_risk"] = (rain_norm + temp_norm + pop_norm) / 3
        print("  🔧 Added: environmental_risk")
    
    return df


def scale_features(X: pd.DataFrame, fit: bool = True, scaler_path: Path = None) -> tuple:
    """
    Scale features using StandardScaler.
    
    Args:
        X: Feature DataFrame
        fit: If True, fit the scaler; if False, load existing
        scaler_path: Path to save/load the scaler
        
    Returns:
        Tuple of (scaled array, scaler)
    """
    if scaler_path is None:
        scaler_path = ML_CONFIG["scaler_path"]
    
    if fit:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Save scaler for later use
        Path(scaler_path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(scaler, scaler_path)
        print(f"  💾 Scaler saved: {scaler_path}")
    else:
        if not Path(scaler_path).exists():
            raise FileNotFoundError(f"Scaler not found: {scaler_path}")
        scaler = joblib.load(scaler_path)
        X_scaled = scaler.transform(X)
    
    return X_scaled, scaler


def prepare_prediction_input(data: dict) -> np.ndarray:
    """
    Prepare a single prediction input from raw sensor data.
    
    This is used by the Flask API to process incoming prediction requests.
    
    Args:
        data: Dict with sensor readings, e.g.:
              {"ph_level": 7.2, "turbidity_ntu": 15, ...}
              
    Returns:
        Scaled feature array ready for prediction
    """
    # Create DataFrame from input
    df = pd.DataFrame([data])
    
    # Standardize column names
    df = standardize_columns(df)
    
    # Add engineered features
    df = add_engineered_features(df)
    
    # Extract features in correct order
    features = ML_CONFIG["input_features"]
    available = [f for f in features if f in df.columns]
    
    # Fill missing features with 0
    for f in features:
        if f not in df.columns:
            df[f] = 0
    
    X = df[features].values
    
    # Scale using saved scaler
    scaler_path = ML_CONFIG["scaler_path"]
    if Path(scaler_path).exists():
        scaler = joblib.load(scaler_path)
        X = scaler.transform(X)
    
    return X
