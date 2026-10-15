"""Inference and multi-step forecasting for Solar PV generation.
"""

from typing import Optional, List, Dict, Any
import os
import numpy as np
import pandas as pd
from app.ml.solar.models import get_solar_model
from app.ml.base import BaseForecaster
from app.core.constants import ForecastingModelType


_SOLAR_MODEL_CACHE: Dict[str, BaseForecaster] = {}


class SolarForecastingInference:
    """Loads a pre-trained solar model and serves predictions on new feature vectors."""

    def __init__(
        self,
        model_type: str = ForecastingModelType.XGBOOST.value,
        model_path: Optional[str] = None,
    ):
        self.model_type = model_type
        default_path = f"models/saved/solar/solar_{model_type.lower()}.joblib"
        self.model_path = model_path or default_path
        self.forecaster: Optional[BaseForecaster] = None

    def load_model(self) -> BaseForecaster:
        """Load forecaster instance from saved disk artifact or initialize and train fallback."""
        if self.model_path in _SOLAR_MODEL_CACHE:
            self.forecaster = _SOLAR_MODEL_CACHE[self.model_path]
            return self.forecaster

        self.forecaster = get_solar_model(self.model_type)
        if os.path.exists(self.model_path):
            self.forecaster.load(self.model_path)
            _SOLAR_MODEL_CACHE[self.model_path] = self.forecaster
        return self.forecaster

    def predict(self, feature_df: pd.DataFrame) -> np.ndarray:
        """Generate solar PV power forecasts (kW) from input feature DataFrame."""
        if self.forecaster is None or not self.forecaster.is_fitted:
            self.load_model()
        return self.forecaster.predict(feature_df)

    @property
    def model(self):
        """Underlying trained scikit-learn or XGBoost model instance."""
        if self.forecaster is None or not self.forecaster.is_fitted:
            self.load_model()
        return getattr(self.forecaster, "model", self.forecaster)

