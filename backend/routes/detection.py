"""
============================================
Detection Routes - /predict-image
============================================
Flask routes for YOLO image detection.
"""

import sys
from pathlib import Path
from flask import Blueprint, request, jsonify
from datetime import datetime
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.services.yolo_service import yolo_service
from backend.services.alert_service import alert_service
from backend.utils.logger import request_logger
from backend.database.mongodb import mongo_db

detection_bp = Blueprint("detection", __name__)


@detection_bp.route("/predict-image", methods=["POST"])
def predict_image():
    """
    Run YOLO detection on an uploaded image.
    
    Expects:
        - File upload with key "image"
        - Optional form field "model" (default: "water_contamination")
        - Optional form field "confidence" (default: 0.25)
    
    Returns:
        JSON with detection results
    """
    start_time = time.time()
    
    # Validate request
    if "image" not in request.files:
        return jsonify({"error": "No image file provided", "hint": "Send file with key 'image'"}), 400
    
    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400
    
    # Get parameters
    model_name = request.form.get("model", "water_contamination")
    conf_threshold = float(request.form.get("confidence", 0.25))
    
    # Validate model name
    available = yolo_service.get_available_models()
    valid_models = [m["key"] for m in available]
    
    if model_name not in valid_models:
        return jsonify({
            "error": f"Invalid model: {model_name}",
            "available_models": valid_models
        }), 400
    
    try:
        # Read image bytes
        image_bytes = file.read()
        
        # Run detection
        result = yolo_service.detect_from_bytes(image_bytes, model_name, conf_threshold)
        
        # Check if alert should be triggered
        alert_result = alert_service.check_detection_alert(result)
        if alert_result:
            result["alert"] = alert_result
            
        # Store in MongoDB
        if mongo_db.is_connected():
            det_record = {
                "model": model_name,
                "total_detections": result.get("total_detections", 0),
                "risk_level": result.get("risk_level", "LOW"),
                "detections": result.get("detections", []),
                "is_dangerous": result.get("is_dangerous", False),
                "created_at": datetime.utcnow()
            }
            mongo_db.db.detections.insert_one(det_record)
        
        duration = (time.time() - start_time) * 1000
        request_logger.log_request("POST", "/predict-image", 200, duration,
                                   {"model": model_name, "detections": result["total_detections"]})
        
        return jsonify(result), 200
        
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        request_logger.log_request("POST", "/predict-image", 500, duration, {"error": str(e)})
        return jsonify({"error": str(e)}), 500


@detection_bp.route("/predict-image/all", methods=["POST"])
def predict_image_all_models():
    """
    Run ALL YOLO models on an uploaded image.
    Returns comprehensive detection results from every model.
    """
    start_time = time.time()
    
    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400
    
    file = request.files["image"]
    conf_threshold = float(request.form.get("confidence", 0.25))
    
    try:
        image_bytes = file.read()
        results = yolo_service.detect_all_models(image_bytes, conf_threshold)
        
        # Aggregate dangerous findings
        all_dangerous = any(r.get("is_dangerous", False) for r in results.values() 
                          if isinstance(r, dict))
        
        duration = (time.time() - start_time) * 1000
        request_logger.log_request("POST", "/predict-image/all", 200, duration)
        
        return jsonify({
            "results": results,
            "any_dangerous": all_dangerous,
            "timestamp": datetime.now().isoformat(),
        }), 200
        
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        request_logger.log_request("POST", "/predict-image/all", 500, duration)
        return jsonify({"error": str(e)}), 500


@detection_bp.route("/models", methods=["GET"])
def get_models():
    """Get list of available YOLO detection models."""
    models = yolo_service.get_available_models()
    return jsonify({"models": models}), 200
