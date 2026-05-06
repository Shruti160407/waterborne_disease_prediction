"""
============================================
Logging Utility
============================================
Provides colored, structured logging for the entire application.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

try:
    import colorlog
    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False


def setup_logger(name: str = "waterborne", level: str = "INFO", log_file: str = None):
    """
    Create a configured logger with colored console output and optional file output.
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional path to log file
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler with colors
    if HAS_COLORLOG:
        console_handler = colorlog.StreamHandler()
        console_handler.setFormatter(colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s [%(levelname)-8s]%(reset)s %(blue)s%(name)s%(reset)s: %(message)s",
            datefmt="%H:%M:%S",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            }
        ))
    else:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
            datefmt="%H:%M:%S"
        ))
    
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(str(log_path))
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        logger.addHandler(file_handler)
    
    return logger


# Create default application logger
app_logger = setup_logger("waterborne", "INFO")


class RequestLogger:
    """
    Middleware-style logger for tracking API requests.
    Logs request method, path, status code, and response time.
    """
    
    def __init__(self):
        self.logger = setup_logger("api.requests", "INFO")
        self.request_count = 0
    
    def log_request(self, method: str, path: str, status_code: int, 
                    duration_ms: float, extra: dict = None):
        """Log an API request."""
        self.request_count += 1
        
        status_emoji = "✅" if status_code < 400 else "⚠️" if status_code < 500 else "❌"
        
        msg = f"{status_emoji} {method} {path} → {status_code} ({duration_ms:.1f}ms)"
        
        if extra:
            msg += f" | {extra}"
        
        if status_code < 400:
            self.logger.info(msg)
        elif status_code < 500:
            self.logger.warning(msg)
        else:
            self.logger.error(msg)
    
    def log_alert(self, alert_type: str, risk_level: str, message: str):
        """Log an alert trigger."""
        self.logger.warning(f"🚨 ALERT [{alert_type}] Risk={risk_level}: {message}")


# Create default request logger
request_logger = RequestLogger()
