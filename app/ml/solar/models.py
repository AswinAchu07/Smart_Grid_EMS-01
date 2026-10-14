"""Solar PV Forecasting model architectures.
"""

from typing import List, Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import xgboost as xgb

from app.ml.base import BaseForecaster
from app.core.constants import ForecastingModelType


class PersistenceSolarModel(BaseForecaster):
    """Naive 24-hour persistence baseline for solar PV generation."""

    def __init__(self):
        super().__init__(model_name=ForecastingModelType.PERSISTENCE.value, target_name="solar_power_kw")

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "PersistenceSolarModel":
        self.feature_names = list(X.columns)
        self.is_fitted = True
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        # Use lag_24 if available, otherwise return 0
        if "solar_power_kw_lag_24" in X.columns:
            preds = X["solar_power_kw_lag_24"].values
        elif "solar_power_kw_lag_1" in X.columns:
            preds = X["solar_power_kw_lag_1"].values
        else:
            preds = np.zeros(len(X))
        return np.maximum(0.0, preds)


class RidgeSolarModel(BaseForecaster):
    """Ridge Linear Regression model with feature scaling for Solar PV forecasting."""

    def __init__(self, alpha: float = 1.0):
        super().__init__(model_name=ForecastingModelType.LINEAR_RIDGE.value, target_name="solar_power_kw")
        self.alpha = alpha
        self.scaler = StandardScaler()
        self.model = Ridge(alpha=self.alpha, random_state=42)

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "RidgeSolarModel":
        self.feature_names = list(X.columns)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y.values)
        self.is_fitted = True
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before calling predict.")
        X_sub = X[self.feature_names]
        X_scaled = self.scaler.transform(X_sub)
        preds = self.model.predict(X_scaled)
        # Apply physical zero clipping and night-time zero forcing
        preds = np.maximum(0.0, preds)
        if "hour" in X_sub.columns:
            night_mask = (X_sub["hour"] < 6) | (X_sub["hour"] > 19)
            preds[night_mask] = 0.0
        return preds


class RandomForestSolarModel(BaseForecaster):
    """Random Forest Regressor for non-linear Solar PV forecasting."""

    def __init__(self, n_estimators: int = 100, max_depth: int = 12):
        super().__init__(model_name=ForecastingModelType.RANDOM_FOREST.value, target_name="solar_power_kw")
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=42,
            n_jobs=-1,
        )

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "RandomForestSolarModel":
        self.feature_names = list(X.columns)
        self.model.fit(X[self.feature_names], y.values)
        self.is_fitted = True
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before calling predict.")
        X_sub = X[self.feature_names]
        preds = self.model.predict(X_sub)
        preds = np.maximum(0.0, preds)
        if "hour" in X_sub.columns:
            night_mask = (X_sub["hour"] < 6) | (X_sub["hour"] > 19)
            preds[night_mask] = 0.0
        return preds


class XGBoostSolarModel(BaseForecaster):
    """XGBoost Gradient Boosted Trees for Solar PV forecasting."""

    def __init__(self, n_estimators: int = 150, max_depth: int = 6, learning_rate: float = 0.05):
        super().__init__(model_name=ForecastingModelType.XGBOOST.value, target_name="solar_power_kw")
        self.model = xgb.XGBRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            random_state=42,
            n_jobs=-1,
            verbosity=0,
        )

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "XGBoostSolarModel":
        self.feature_names = list(X.columns)
        self.model.fit(X[self.feature_names], y.values)
        self.is_fitted = True
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before calling predict.")
        X_sub = X[self.feature_names]
        preds = self.model.predict(X_sub)
        preds = np.maximum(0.0, preds)
        if "hour" in X_sub.columns:
            night_mask = (X_sub["hour"] < 6) | (X_sub["hour"] > 19)
            preds[night_mask] = 0.0
        return preds


def get_solar_model(model_type: str) -> BaseForecaster:
    """Factory function for solar forecasting models."""
    model_type = model_type.upper()
    if model_type == ForecastingModelType.PERSISTENCE.value:
        return PersistenceSolarModel()
    elif model_type == ForecastingModelType.LINEAR_RIDGE.value:
        return RidgeSolarModel()
    elif model_type == ForecastingModelType.RANDOM_FOREST.value:
        return RandomForestSolarModel()
    elif model_type == ForecastingModelType.XGBOOST.value:
        return XGBoostSolarModel()
    else:
        raise ValueError(f"Unknown solar model type: {model_type}")
