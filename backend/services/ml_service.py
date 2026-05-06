"""
============================================
ML Prediction Service
============================================
Service layer for the ML outbreak prediction model.
Used by Flask routes for risk prediction.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.utils.logger import app_logger


class MLService:
    """
    Service class for ML-based outbreak prediction.
    Wraps the prediction module for use by Flask routes.
    """
    
    def __init__(self):
        """Initialize with lazy model loading."""
        self._model_loaded = False
        self.logger = app_logger
    
    def predict(self, sensor_data: dict) -> dict:
        """
        Predict disease outbreak risk from sensor data.
        
        Args:
            sensor_data: Dict with water quality readings
            
        Returns:
            Prediction results including risk levels and actions
        """
        try:
            from models.ml.predict import predict_risk
            result = predict_risk(sensor_data)
            self._model_loaded = True
            
            self.logger.info(
                f"Prediction: Risk={result['overall_risk']} | "
                f"Model={result.get('model_used', 'N/A')}"
            )
            
            return result
            
        except FileNotFoundError:
            self.logger.warning("ML model not trained yet, returning demo prediction")
            return self._demo_prediction(sensor_data)
        except Exception as e:
            self.logger.error(f"Prediction error: {e}")
            return {"error": str(e)}
    
    def batch_predict(self, data_list: list) -> list:
        """
        Make predictions for multiple inputs.
        
        Args:
            data_list: List of sensor data dicts
            
        Returns:
            List of prediction results
        """
        return [self.predict(data) for data in data_list]
    
    def _demo_prediction(self, sensor_data: dict) -> dict:
        """
        Generate a demo prediction when the model isn't trained yet.
        Uses simple rule-based logic for demonstration.
        
        Args:
            sensor_data: Dict with sensor readings
            
        Returns:
            Demo prediction result
        """
        # Simple rule-based risk assessment for demo
        risk_score = 0
        
        ph = sensor_data.get("ph_level", 7.0)
        if ph < 6.0 or ph > 9.0:
            risk_score += 30
        elif ph < 6.5 or ph > 8.5:
            risk_score += 15
        
        turbidity = sensor_data.get("turbidity_ntu", 5)
        if turbidity > 20:
            risk_score += 25
        elif turbidity > 10:
            risk_score += 15
        
        bacteria = sensor_data.get("bacteria_count_cfu_ml", 100)
        if bacteria > 1000:
            risk_score += 30
        elif bacteria > 500:
            risk_score += 20
        
        contaminant = sensor_data.get("contaminant_level_ppm", 10)
        if contaminant > 50:
            risk_score += 25
        elif contaminant > 30:
            risk_score += 15
        
        lead = sensor_data.get("lead_concentration", 0)
        if lead > 0.015:
            risk_score += 20
        
        sanitation = sensor_data.get("sanitation_coverage", 80)
        if sanitation < 40:
            risk_score += 15
        
        # Determine risk level
        if risk_score >= 70:
            overall_risk = "HIGH"
        elif risk_score >= 40:
            overall_risk = "MEDIUM"
        else:
            overall_risk = "LOW"
        
        risk_colors = {"LOW": "#27ae60", "MEDIUM": "#f39c12", "HIGH": "#e74c3c"}
        
        # Generate demo predictions
        predictions = {
            "cholera_cases_per_100000": {
                "predicted_cases": round(risk_score * 1.5, 2),
                "risk_level": "HIGH" if risk_score > 60 else "MEDIUM" if risk_score > 30 else "LOW",
                "thresholds": {"low": 10, "medium": 50, "high": 100},
            },
            "typhoid_cases_per_100000": {
                "predicted_cases": round(risk_score * 2.0, 2),
                "risk_level": "HIGH" if risk_score > 50 else "MEDIUM" if risk_score > 25 else "LOW",
                "thresholds": {"low": 20, "medium": 80, "high": 150},
            },
            "diarrheal_cases_per_100000": {
                "predicted_cases": round(risk_score * 5.0, 2),
                "risk_level": "HIGH" if risk_score > 40 else "MEDIUM" if risk_score > 20 else "LOW",
                "thresholds": {"low": 50, "medium": 200, "high": 500},
            },
        }
        
        actions = []
        if overall_risk == "HIGH":
            actions = [
                "🚨 IMMEDIATE: Issue public health advisory",
                "🏥 Deploy emergency medical teams",
                "💧 Distribute water purification supplies",
            ]
        elif overall_risk == "MEDIUM":
            actions = [
                "⚠️ Increase water quality monitoring",
                "💊 Prepare medical supply inventory",
                "📋 Review sanitation infrastructure",
            ]
        else:
            actions = [
                "✅ Continue routine monitoring",
                "📊 Document readings for trends",
            ]
        
        return {
            "predictions": predictions,
            "overall_risk": overall_risk,
            "risk_color": risk_colors[overall_risk],
            "suggested_actions": actions,
            "feature_importance": {
                "bacteria_count_cfu_ml": 0.18,
                "contaminant_level_ppm": 0.15,
                "turbidity_ntu": 0.13,
                "ph_level": 0.11,
                "lead_concentration": 0.10,
                "sanitation_coverage": 0.09,
                "dissolved_oxygen_mg_l": 0.07,
                "access_to_clean_water": 0.06,
                "rainfall": 0.04,
                "temperature": 0.03,
                "population_density": 0.02,
                "nitrate_levels": 0.02,
            },
            "model_used": "Demo (Rule-based) - Train model for accurate predictions",
            "input_data": sensor_data,
            "is_demo": True,
        }
    
    @property
    def is_model_available(self) -> bool:
        """Check if the trained ML model is available."""
        from config.settings import ML_CONFIG
        return ML_CONFIG["model_path"].exists()


# Singleton service instance
ml_service = MLService()
