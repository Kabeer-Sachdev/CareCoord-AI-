import numpy as np

class BaselineMovingAverageModel:
    """
    Operational Baseline Model:
    Forecasts target using the 7-day rolling average or lag-1 historical value.
    Provides a standardized benchmark for comparing ML improvements.
    """
    def __init__(self, fallback_col_idx: int = -1):
        self.name = "BaselineMovingAverage"
        self.fallback_col_idx = fallback_col_idx
        self.default_val = 10.0

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.default_val = float(np.mean(y)) if len(y) > 0 else 10.0
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        # If lag-1 / rolling column is available, use it; else fallback to mean
        if X.shape[1] > 0 and self.fallback_col_idx != -1:
            preds = X[:, self.fallback_col_idx].copy()
            # Replace NaNs or zeros with default_val
            preds = np.nan_to_num(preds, nan=self.default_val)
            return preds
        return np.full(shape=(len(X),), fill_value=self.default_val)
