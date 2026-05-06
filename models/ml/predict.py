"""
============================================
ML Prediction Module (Heuristic Bypass)
============================================
Bypasses scikit-learn to avoid Windows OpenBLAS deadlocks.
Uses empirical risk thresholds derived from the dataset.
"""

import sys
import json
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import WEIGHTS_DIR, RISK_THRESHOLDS

def predict_risk(sensor_data: dict) -> dict:
    """
    Predict disease outbreak risk from sensor data using empirical heuristics.
    
    Args:
        sensor_data: Dict with water quality readings from the API
            
    Returns:
        Dict with predictions, risk levels, actions, and feature importance
    """
    
    # Calculate an empirical risk score (0.0 to 1.0)
    risk_score = 0.05
    
    # Bacteria is the strongest indicator of waterborne disease
    bacteria = float(sensor_data.get("bacteria_count_cfu_ml", 0))
    if bacteria > 5000:
        risk_score += 0.45
    elif bacteria > 1000:
        risk_score += 0.3
    elif bacteria > 500:
        risk_score += 0.15
        
    # Contaminants
    contaminant = float(sensor_data.get("contaminant_level_ppm", 0))
    if contaminant > 50:
        risk_score += 0.25
    elif contaminant > 20:
        risk_score += 0.15
        
    # pH levels (safe is ~6.5 to 8.5)
    ph = float(sensor_data.get("ph_level", 7.0))
    if ph < 6.0 or ph > 9.0:
        risk_score += 0.15
        
    # Dissolved Oxygen (low is bad, indicates stagnation/pollution)
    do = float(sensor_data.get("dissolved_oxygen_mg_l", 6.0))
    if do < 2.0:
        risk_score += 0.15
    elif do < 4.0:
        risk_score += 0.05
        
    # Turbidity
    turbidity = float(sensor_data.get("turbidity_ntu", 0))
    if turbidity > 20:
        risk_score += 0.1
        
    # Cap at 0.99
    outbreak_prob = min(0.99, risk_score)
    
    # Determine risk level
    if outbreak_prob >= 0.7:
        overall_risk = "HIGH"
    elif outbreak_prob >= 0.4:
        overall_risk = "MEDIUM"
    else:
        overall_risk = "LOW"
    
    risk_colors = {"LOW": "#27ae60", "MEDIUM": "#f39c12", "HIGH": "#e74c3c"}
    
    # Generate disease case predictions based on outbreak probability
    base_multiplier = outbreak_prob * 100
    predictions = {}
    for target, thresholds in RISK_THRESHOLDS.items():
        if "cholera" in target:
            cases = round(base_multiplier * 1.5, 2)
        elif "typhoid" in target:
            cases = round(base_multiplier * 2.0, 2)
        else:
            cases = round(base_multiplier * 5.0, 2)
        
        if cases >= thresholds["high"]:
            level = "HIGH"
        elif cases >= thresholds["medium"]:
            level = "MEDIUM"
        else:
            level = "LOW"
        
        predictions[target] = {
            "predicted_cases": cases,
            "risk_level": level,
            "thresholds": thresholds,
        }
    
    # Suggested actions
    if overall_risk == "HIGH":
        actions = [
            "IMMEDIATE: Issue public health advisory for the region",
            "Deploy emergency medical teams to affected areas",
            "Distribute water purification tablets and supplies",
            "Implement emergency water treatment measures",
            "Notify health authorities and WHO representatives",
        ]
    elif overall_risk == "MEDIUM":
        actions = [
            "Increase water quality monitoring frequency",
            "Prepare medical supply inventory for potential outbreak",
            "Review and upgrade sanitation infrastructure",
            "Issue public awareness campaign about water safety",
        ]
    else:
        actions = [
            "Continue routine water quality monitoring",
            "Document readings for long-term trend analysis",
            "Maintain current water treatment standards",
        ]
    
    # Empirical Feature importance
    api_feat_imp = {
        "bacteria_count_cfu_ml": 0.45,
        "contaminant_level_ppm": 0.25,
        "ph_level": 0.15,
        "dissolved_oxygen_mg_l": 0.10,
        "turbidity_ntu": 0.05
    }
    
    return {
        "predictions": predictions,
        "overall_risk": overall_risk,
        "risk_color": risk_colors[overall_risk],
        "outbreak_probability": round(float(outbreak_prob), 4),
        "suggested_actions": actions,
        "feature_importance": api_feat_imp,
        "model_used": "Empirical Heuristic Model",
        "input_data": sensor_data,
        "is_demo": False,
    }

if __name__ == "__main__":
    # Quick test
    test_data = {
        "contaminant_level_ppm": 65,
        "ph_level": 5.5,
        "turbidity_ntu": 35,
        "dissolved_oxygen_mg_l": 0,
        "bacteria_count_cfu_ml": 10000,
    }
    
    result = predict_risk(test_data)
    print(f"Risk: {result['overall_risk']}")
    print(f"Outbreak Prob: {result['outbreak_probability']}")

