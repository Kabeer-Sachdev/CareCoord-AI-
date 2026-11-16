import os
import joblib
from typing import Dict, Any, Optional

class ModelLoader:
    _models_cache: Dict[str, Any] = {}

    @classmethod
    def get_models_dir(cls) -> str:
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(current_dir, "artifacts", "models")

    @classmethod
    def load_model(cls, target: str) -> Optional[Dict[str, Any]]:
        """
        Loads a trained model artifact (.joblib) for a specific target.
        Caches in memory to ensure fast sub-millisecond inference.
        """
        if target in cls._models_cache:
            return cls._models_cache[target]

        target_file_map = {
            "patient_arrivals": "patient_arrivals_model.joblib",
            "emergency_cases": "emergency_demand_model.joblib",
            "occupied_beds": "bed_occupancy_model.joblib",
            "appointment_count": "appointment_demand_model.joblib"
        }

        filename = target_file_map.get(target)
        if not filename:
            return None

        filepath = os.path.join(cls.get_models_dir(), filename)
        if not os.path.exists(filepath):
            # Retrain if missing
            from backend.ml.training.train_models import train_and_evaluate_all_models
            train_and_evaluate_all_models()

        if os.path.exists(filepath):
            payload = joblib.load(filepath)
            cls._models_cache[target] = payload
            return payload

        return None

    @classmethod
    def clear_cache(cls):
        cls._models_cache.clear()
