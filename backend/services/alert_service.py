"""
============================================
Alert Service
============================================
Handles SMS alerts via Twilio and in-app notifications.
Triggers when risk is HIGH or dangerous detections occur.
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from config.settings import TWILIO_CONFIG
from backend.utils.logger import app_logger, request_logger


class AlertService:
    """
    Service for sending alerts when dangerous conditions are detected.
    Supports SMS (via Twilio) and in-app notifications.
    """
    
    def __init__(self):
        """Initialize alert service."""
        self.logger = app_logger
        self.alert_history = []  # In-memory alert storage
        self._twilio_client = None
        self._twilio_available = False
        self._init_twilio()
    
    def _init_twilio(self):
        """Initialize Twilio client if credentials are available."""
        try:
            if TWILIO_CONFIG["account_sid"] and TWILIO_CONFIG["auth_token"]:
                from twilio.rest import Client
                self._twilio_client = Client(
                    TWILIO_CONFIG["account_sid"],
                    TWILIO_CONFIG["auth_token"]
                )
                self._twilio_available = True
                self.logger.info("Twilio SMS service initialized")
            else:
                self.logger.info("Twilio credentials not configured - SMS disabled")
        except ImportError:
            self.logger.info("Twilio package not installed - SMS disabled")
        except Exception as e:
            self.logger.warning(f"Twilio init failed: {e}")
    
    def send_alert(self, risk_level: str, message: str, 
                   alert_type: str = "risk", details: dict = None) -> dict:
        """
        Send an alert based on risk level.
        
        Args:
            risk_level: "LOW", "MEDIUM", or "HIGH"
            message: Alert message text
            alert_type: Type of alert ("risk", "detection", "manual")
            details: Additional alert details
            
        Returns:
            Dict with alert status and ID
        """
        alert = {
            "id": f"alert_{len(self.alert_history) + 1:04d}",
            "timestamp": datetime.now().isoformat(),
            "risk_level": risk_level,
            "alert_type": alert_type,
            "message": message,
            "details": details or {},
            "sms_sent": False,
            "sms_status": None,
        }
        
        # Log the alert
        request_logger.log_alert(alert_type, risk_level, message)
        
        # Send SMS for HIGH and MEDIUM risk
        if risk_level in ("HIGH", "MEDIUM") and self._twilio_available:
            sms_result = self._send_sms(risk_level, message)
            alert["sms_sent"] = sms_result.get("success", False)
            alert["sms_status"] = sms_result.get("status", "failed")
        elif risk_level in ("HIGH", "MEDIUM"):
            alert["sms_status"] = "twilio_not_configured"
            self.logger.info("SMS alert skipped - Twilio not configured")
        
        # Store in history
        self.alert_history.append(alert)
        
        # Keep only last 100 alerts
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]
        
        return {
            "status": "sent",
            "alert_id": alert["id"],
            "risk_level": risk_level,
            "sms_sent": alert["sms_sent"],
            "timestamp": alert["timestamp"],
        }
    
    def _send_sms(self, risk_level: str, message: str) -> dict:
        """
        Send SMS via Twilio (with timeout to avoid blocking).
        
        Args:
            risk_level: Risk level for the alert
            message: Alert message
            
        Returns:
            Dict with SMS send result
        """
        if not self._twilio_available:
            return {"success": False, "status": "twilio_not_available"}
        
        import threading
        
        result_holder = {"success": False, "status": "timeout"}
        
        def _do_send():
            try:
                sms_body = (
                    f"WATERBORNE DISEASE ALERT\n\n"
                    f"Risk Level: {risk_level}\n"
                    f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                    f"{message}\n\n"
                    f"Take immediate action. Check dashboard for details."
                )
                
                sms_message = self._twilio_client.messages.create(
                    body=sms_body,
                    from_=TWILIO_CONFIG["phone_number"],
                    to=TWILIO_CONFIG["alert_phone"]
                )
                
                self.logger.info(f"SMS sent: SID={sms_message.sid}")
                result_holder["success"] = True
                result_holder["status"] = "sent"
                result_holder["sid"] = sms_message.sid
                
            except Exception as e:
                self.logger.error(f"SMS failed: {e}")
                result_holder["status"] = f"failed: {str(e)}"
        
        # Run with 5-second timeout so it never blocks the response
        t = threading.Thread(target=_do_send, daemon=True)
        t.start()
        t.join(timeout=5)
        
        if t.is_alive():
            self.logger.warning("SMS send timed out after 5s - continuing without blocking")
            return {"success": False, "status": "timeout_non_blocking"}
        
        return result_holder
    
    def check_and_alert(self, prediction_result: dict) -> dict:
        """
        Automatically check prediction results and trigger alerts if needed.
        
        This is called after every prediction to check if an alert
        should be sent.
        
        Args:
            prediction_result: Result from the ML prediction service
            
        Returns:
            Alert result if alert was triggered, None otherwise
        """
        risk_level = prediction_result.get("overall_risk", "LOW")
        
        if risk_level == "HIGH":
            # Build detailed message
            predictions = prediction_result.get("predictions", {})
            high_risks = []
            
            for disease, info in predictions.items():
                if isinstance(info, dict) and info.get("risk_level") == "HIGH":
                    cases = info.get("predicted_cases", "N/A")
                    high_risks.append(f"{disease.replace('_', ' ')}: {cases} cases")
            
            message = "HIGH RISK detected!\n" + "\n".join(high_risks)
            
            return self.send_alert(
                risk_level="HIGH",
                message=message,
                alert_type="auto_prediction",
                details=prediction_result.get("input_data", {})
            )
        
        return None
    
    def check_detection_alert(self, detection_result: dict) -> dict:
        """
        Check YOLO detection results for dangerous findings.
        
        Args:
            detection_result: Result from YOLO detection service
            
        Returns:
            Alert result if dangerous detection found, None otherwise
        """
        if detection_result.get("is_dangerous", False):
            dangerous = [d for d in detection_result.get("detections", [])
                        if d.get("confidence", 0) > 0.5]
            
            if dangerous:
                classes = [d["class"] for d in dangerous[:3]]
                message = f"Dangerous contamination detected: {', '.join(classes)}"
                
                return self.send_alert(
                    risk_level="HIGH",
                    message=message,
                    alert_type="detection",
                    details={"detections": dangerous}
                )
        
        return None
    
    def get_alert_history(self, limit: int = 20) -> list:
        """
        Get recent alert history.
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            List of recent alerts (newest first)
        """
        return list(reversed(self.alert_history[-limit:]))
    
    def get_stats(self) -> dict:
        """Get alert statistics."""
        total = len(self.alert_history)
        high = sum(1 for a in self.alert_history if a["risk_level"] == "HIGH")
        medium = sum(1 for a in self.alert_history if a["risk_level"] == "MEDIUM")
        sms_sent = sum(1 for a in self.alert_history if a["sms_sent"])
        
        return {
            "total_alerts": total,
            "high_risk_alerts": high,
            "medium_risk_alerts": medium,
            "sms_sent": sms_sent,
            "twilio_configured": self._twilio_available,
        }


# Singleton service instance
alert_service = AlertService()
