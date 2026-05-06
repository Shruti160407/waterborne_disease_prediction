"""
============================================
Alert Routes - /send-alert
============================================
Flask routes for alert management.
"""

import sys
from pathlib import Path
from flask import Blueprint, request, jsonify
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.services.alert_service import alert_service
from backend.utils.logger import request_logger

alerts_bp = Blueprint("alerts", __name__)


@alerts_bp.route("/send-alert", methods=["POST"])
def send_alert():
    """
    Manually send an alert.
    
    Expects JSON:
    {
        "risk_level": "HIGH",
        "message": "Alert message text",
        "alert_type": "manual"  (optional)
    }
    """
    start_time = time.time()
    
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    
    risk_level = data.get("risk_level", "MEDIUM")
    message = data.get("message", "Manual alert triggered")
    alert_type = data.get("alert_type", "manual")
    
    if risk_level not in ["LOW", "MEDIUM", "HIGH"]:
        return jsonify({"error": "risk_level must be LOW, MEDIUM, or HIGH"}), 400
    
    try:
        result = alert_service.send_alert(risk_level, message, alert_type, data.get("details"))
        
        duration = (time.time() - start_time) * 1000
        request_logger.log_request("POST", "/send-alert", 200, duration,
                                   {"risk": risk_level})
        
        return jsonify(result), 200
        
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        request_logger.log_request("POST", "/send-alert", 500, duration)
        return jsonify({"error": str(e)}), 500


@alerts_bp.route("/alerts/history", methods=["GET"])
def get_history():
    """Get alert history."""
    limit = request.args.get("limit", 20, type=int)
    history = alert_service.get_alert_history(limit)
    return jsonify({"alerts": history, "count": len(history)}), 200


@alerts_bp.route("/alerts/stats", methods=["GET"])
def get_stats():
    """Get alert statistics."""
    stats = alert_service.get_stats()
    return jsonify(stats), 200
