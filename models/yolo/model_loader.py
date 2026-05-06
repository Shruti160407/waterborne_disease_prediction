"""
============================================
YOLO Model Loader
============================================
Dynamic model loader for serving multiple YOLO models.
Used by the Flask backend to load models on demand.
"""

import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from config.settings import YOLO_MODELS, WEIGHTS_DIR


class YOLOModelLoader:
    """
    Manages loading and caching of multiple YOLO models.
    
    Models are loaded lazily (on first use) and cached in memory
    to avoid reloading for subsequent predictions.
    
    Usage:
        loader = YOLOModelLoader()
        model, classes = loader.get_model("algal_bloom")
        results = model.predict(image)
    """
    
    def __init__(self):
        """Initialize the model loader with empty cache."""
        self._models = {}  # Cache loaded models
        self._available_models = list(YOLO_MODELS.keys())
    
    def get_model(self, model_name: str):
        """
        Get a YOLO model by name. Loads from disk if not cached.
        
        Args:
            model_name: Key from YOLO_MODELS config
            
        Returns:
            Tuple of (YOLO model, list of class names)
            
        Raises:
            ValueError: If model name is not recognized
        """
        if model_name not in YOLO_MODELS:
            raise ValueError(
                f"Unknown model: {model_name}. "
                f"Available: {self._available_models}"
            )
        
        if model_name not in self._models:
            self._load_model(model_name)
        
        return self._models[model_name], YOLO_MODELS[model_name]["classes"]
    
    def _load_model(self, model_name: str):
        """
        Load a YOLO model from weights file.
        
        Args:
            model_name: Key from YOLO_MODELS config
        """
        from ultralytics import YOLO
        
        weights_path = WEIGHTS_DIR / f"{model_name}_best.pt"
        
        if weights_path.exists():
            print(f"  🧠 Loading model: {model_name} from {weights_path}")
            self._models[model_name] = YOLO(str(weights_path))
        else:
            print(f"  ⚠️  No trained weights for {model_name}. Using YOLOv8n.")
            self._models[model_name] = YOLO("yolov8n.pt")
    
    def is_loaded(self, model_name: str) -> bool:
        """Check if a model is currently loaded in memory."""
        return model_name in self._models
    
    def unload_model(self, model_name: str):
        """Unload a model from memory to free resources."""
        if model_name in self._models:
            del self._models[model_name]
            print(f"  🗑️  Unloaded model: {model_name}")
    
    def unload_all(self):
        """Unload all models from memory."""
        self._models.clear()
        print("  🗑️  All models unloaded")
    
    @property
    def available_models(self) -> list:
        """Get list of available model names."""
        return self._available_models
    
    @property
    def loaded_models(self) -> list:
        """Get list of currently loaded model names."""
        return list(self._models.keys())
    
    def get_model_info(self, model_name: str) -> dict:
        """
        Get information about a model.
        
        Args:
            model_name: Key from YOLO_MODELS config
            
        Returns:
            Dict with model information
        """
        if model_name not in YOLO_MODELS:
            return {"error": f"Unknown model: {model_name}"}
        
        config = YOLO_MODELS[model_name]
        weights_path = WEIGHTS_DIR / f"{model_name}_best.pt"
        
        return {
            "name": config["name"],
            "model_key": model_name,
            "classes": config["classes"],
            "num_classes": len(config["classes"]),
            "weights_exist": weights_path.exists(),
            "weights_path": str(weights_path),
            "loaded": self.is_loaded(model_name),
        }
    
    def get_all_info(self) -> dict:
        """Get information about all available models."""
        return {
            name: self.get_model_info(name) 
            for name in self._available_models
        }


# Singleton instance for the application
model_loader = YOLOModelLoader()
