"""
============================================
Prediction Routes - /predict-risk
============================================
Flask routes for ML outbreak prediction.
"""

import sys
from pathlib import Path
from flask import Blueprint, request, jsonify
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.services.ml_service import ml_service
from backend.services.alert_service import alert_service
from backend.utils.logger import request_logger
from backend.database.mongodb import mongo_db
from datetime import datetime

prediction_bp = Blueprint("prediction", __name__)


@prediction_bp.route("/predict-risk", methods=["POST"])
def predict_risk():
    """
    Predict disease outbreak risk from water quality sensor data.
    
    Expects JSON body with water quality parameters:
    {
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
    }
    
    Returns:
        JSON with risk predictions, suggested actions, and feature importance
    """
    start_time = time.time()
    
    # Validate request
    if not request.is_json:
        return jsonify({
            "error": "Request must be JSON",
            "hint": "Set Content-Type: application/json"
        }), 400
    
    sensor_data = request.get_json()
    
    if not sensor_data:
        return jsonify({"error": "Empty request body"}), 400
    
    # Validate required fields (warn if missing, don't fail)
    expected_fields = [
        "contaminant_level_ppm", "ph_level", "turbidity_ntu",
        "dissolved_oxygen_mg_l", "nitrate_levels", "lead_concentration",
        "bacteria_count_cfu_ml", "rainfall", "temperature",
        "sanitation_coverage", "population_density", "access_to_clean_water"
    ]
    
    # Also accept various naming conventions
    field_aliases = {
        "contaminant_level": "contaminant_level_ppm",
        "ph": "ph_level",
        "turbidity": "turbidity_ntu",
        "dissolved_oxygen": "dissolved_oxygen_mg_l",
        "nitrate": "nitrate_levels",
        "lead": "lead_concentration",
        "bacteria_count": "bacteria_count_cfu_ml",
        "bacteria": "bacteria_count_cfu_ml",
        "sanitation": "sanitation_coverage",
        "population": "population_density",
        "clean_water": "access_to_clean_water",
    }
    
    # Map aliases to standard names
    normalized = {}
    for key, value in sensor_data.items():
        standard_key = field_aliases.get(key, key)
        normalized[standard_key] = value
    
    missing = [f for f in expected_fields if f not in normalized]
    if missing:
        # Don't fail, just warn
        pass
    
    try:
        # Run prediction
        result = ml_service.predict(normalized)
        
        if "error" in result:
            duration = (time.time() - start_time) * 1000
            request_logger.log_request("POST", "/predict-risk", 500, duration)
            return jsonify(result), 500
        
        # Auto-alert check (non-blocking)
        try:
            alert_result = alert_service.check_and_alert(result)
            if alert_result:
                result["alert_triggered"] = alert_result
        except Exception as alert_err:
            print(f"[WARN] Alert check failed (non-blocking): {alert_err}")
            
        # Store in MongoDB (non-blocking)
        try:
            if mongo_db.is_connected():
                pred_record = {
                    "input_data": normalized,
                    "overall_risk": result.get("overall_risk", "LOW"),
                    "risk_score": result.get("risk_score", 0.0),
                    "predictions": result.get("predictions", {}),
                    "created_at": datetime.utcnow()
                }
                mongo_db.db.predictions.insert_one(pred_record)
        except Exception as db_err:
            print(f"[WARN] MongoDB insert failed (non-blocking): {db_err}")
        
        duration = (time.time() - start_time) * 1000
        request_logger.log_request("POST", "/predict-risk", 200, duration,
                                   {"risk": result.get("overall_risk", "N/A")})
        
        return jsonify(result), 200
        
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        request_logger.log_request("POST", "/predict-risk", 500, duration, {"error": str(e)})
        return jsonify({"error": str(e)}), 500


@prediction_bp.route("/predict-risk/batch", methods=["POST"])
def predict_risk_batch():
    """
    Batch prediction for multiple sensor data inputs.
    
    Expects JSON array of sensor data objects.
    """
    start_time = time.time()
    
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data_list = request.get_json()
    
    if not isinstance(data_list, list):
        return jsonify({"error": "Expected JSON array"}), 400
    
    try:
        results = ml_service.batch_predict(data_list)
        
        duration = (time.time() - start_time) * 1000
        request_logger.log_request("POST", "/predict-risk/batch", 200, duration,
                                   {"count": len(results)})
        
        return jsonify({"results": results, "count": len(results)}), 200
        
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        request_logger.log_request("POST", "/predict-risk/batch", 500, duration)
        return jsonify({"error": str(e)}), 500


@prediction_bp.route("/model-status", methods=["GET"])
def model_status():
    """Check if the ML model is trained and available."""
    return jsonify({
        "model_available": ml_service.is_model_available,
        "message": "Model ready" if ml_service.is_model_available else "Model not trained. Run train_ml_model.py"
    }), 200
