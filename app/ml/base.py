"""Abstract Base Forecaster class for Solar PV and Load time-series forecasting.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timezone

from app.ml.metrics import evaluate_forecasting_metrics


class BaseForecaster(ABC):
    """Abstract Base Class providing a unified interface for all forecasting models."""

    def __init__(self, model_name: str, target_name: str):
        self.model_name = model_name
        self.target_name = target_name
        self.feature_names: List[str] = []
        self.model: Any = None
        self.scaler: Any = None
        self.is_fitted: bool = False
        self.trained_at: Optional[str] = None
        self.metrics: Dict[str, float] = {}

    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series) -> "BaseForecaster":
        """Train the model on features X and target series y."""
        pass

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Generate predictions for feature matrix X."""
        pass

    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """Evaluate the model and store performance metrics."""
        preds = self.predict(X)
        self.metrics = evaluate_forecasting_metrics(y_true=y.values, y_pred=preds)
        return self.metrics

    def save(self, filepath: str) -> str:
        """Serialize model artifact and metadata to disk."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        artifact = {
            "model_name": self.model_name,
            "target_name": self.target_name,
            "feature_names": self.feature_names,
            "model": self.model,
            "scaler": self.scaler,
            "is_fitted": self.is_fitted,
            "trained_at": self.trained_at or datetime.now(timezone.utc).isoformat(),
            "metrics": self.metrics,
        }
        joblib.dump(artifact, filepath)
        return filepath

    def load(self, filepath: str) -> "BaseForecaster":
        """Deserialize model artifact and restore model state."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model artifact not found at {filepath}")
        artifact = joblib.load(filepath)
        self.model_name = artifact["model_name"]
        self.target_name = artifact["target_name"]
        self.feature_names = artifact["feature_names"]
        self.model = artifact["model"]
        self.scaler = artifact.get("scaler")
        self.is_fitted = artifact["is_fitted"]
        self.trained_at = artifact.get("trained_at")
        self.metrics = artifact.get("metrics", {})
        return self
