"""
============================================
Flask Application - Main Entry Point
============================================
Starts the Flask backend server with all routes registered.

Usage:
    python backend/app.py

Endpoints:
    POST /predict-image     → YOLO detection
    POST /predict-risk      → ML outbreak prediction
    POST /send-alert        → Manual alert trigger
    GET  /alerts/history    → Alert history
    GET  /alerts/stats      → Alert statistics
    GET  /models            → Available YOLO models
    GET  /model-status      → ML model status
    GET  /health            → Health check
"""

import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from config.settings import FLASK_CONFIG
from backend.routes.detection import detection_bp
from backend.routes.prediction import prediction_bp
from backend.routes.alerts import alerts_bp
from backend.routes.surveillance import surveillance_bp
from backend.routes.auth import auth_bp
from backend.routes.api_data import api_data_bp
from backend.database.schema import init_db, seed_demo_data
from backend.utils.logger import app_logger


def create_app():
    """
    Flask application factory.
    Creates and configures the Flask app with all blueprints.
    
    Returns:
        Configured Flask application
    """
    app = Flask(
        __name__,
        static_folder=str(PROJECT_ROOT / "frontend" / "build"),
        static_url_path=""
    )
    
    # Configuration
    app.config["SECRET_KEY"] = FLASK_CONFIG["secret_key"]
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max upload
    
    # Enable CORS for React frontend
    # In production, set ALLOWED_ORIGINS env var to comma-separated list of allowed URLs
    _raw_origins = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:5000,http://127.0.0.1:3000"
    )
    allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

    CORS(app, resources={
        r"/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
        }
    })
    
    # Initialize database
    init_db()
    seed_demo_data()
    
    # Register route blueprints
    app.register_blueprint(detection_bp)
    app.register_blueprint(prediction_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(surveillance_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_data_bp)
    
    # ============================================
    # Core Routes
    # ============================================
    
    @app.route("/health", methods=["GET"])
    def health_check():
        """Health check endpoint."""
        return jsonify({
            "status": "ok",
            "service": "Waterborne Disease Prediction API",
            "version": "1.0.0",
        }), 200
    
    @app.route("/api/info", methods=["GET"])
    def api_info():
        """Get API information and available endpoints."""
        return jsonify({
            "name": "AI Waterborne Disease Monitoring API",
            "version": "1.0.0",
            "endpoints": {
                "POST /predict-image": "YOLO image detection",
                "POST /predict-image/all": "Run all YOLO models on image",
                "POST /predict-risk": "ML outbreak risk prediction",
                "POST /predict-risk/batch": "Batch risk prediction",
                "POST /send-alert": "Trigger manual alert",
                "GET /models": "List available YOLO models",
                "GET /model-status": "ML model training status",
                "GET /alerts/history": "Alert history",
                "GET /alerts/stats": "Alert statistics",
                "GET /health": "Health check",
            },
        }), 200
    
    # Serve React frontend (production build)
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):
        """Serve React frontend in production mode."""
        build_dir = PROJECT_ROOT / "frontend" / "build"
        
        if build_dir.exists():
            file_path = build_dir / path
            if file_path.exists() and file_path.is_file():
                return send_from_directory(str(build_dir), path)
            return send_from_directory(str(build_dir), "index.html")
        else:
            return jsonify({
                "message": "API is running. Frontend not built.",
                "hint": "cd frontend && npm run build",
                "api_docs": "GET /api/info",
            }), 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Endpoint not found", "hint": "GET /api/info for available endpoints"}), 404
    
    @app.errorhandler(413)
    def too_large(e):
        return jsonify({"error": "File too large", "max_size": "16MB"}), 413
    
    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500
    
    app_logger.info("Flask application created successfully")
    
    return app


# ============================================
# Run the application
# ============================================

if __name__ == "__main__":
    app = create_app()
    
    print("=" * 60)
    print("  WATERBORNE DISEASE PREDICTION API")
    print("=" * 60)
    print(f"  URL:    http://localhost:{FLASK_CONFIG['port']}")
    print(f"  Info:   http://localhost:{FLASK_CONFIG['port']}/api/info")
    print(f"  Health: http://localhost:{FLASK_CONFIG['port']}/health")
    print(f"  Debug:  {FLASK_CONFIG['debug']}")
    print("=" * 60)
    
    app.run(
        host=FLASK_CONFIG["host"],
        port=FLASK_CONFIG["port"],
        debug=FLASK_CONFIG["debug"],
    )
