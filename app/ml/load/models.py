"""Electricity Load Forecasting model architectures.
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


class PersistenceLoadModel(BaseForecaster):
    """Naive 24-hour / weekly persistence baseline for electricity load."""

    def __init__(self):
        super().__init__(model_name=ForecastingModelType.PERSISTENCE.value, target_name="load_power_kw")

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "PersistenceLoadModel":
        self.feature_names = list(X.columns)
        self.is_fitted = True
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if "load_power_kw_lag_24" in X.columns:
            preds = X["load_power_kw_lag_24"].values
        elif "load_power_kw_lag_1" in X.columns:
            preds = X["load_power_kw_lag_1"].values
        else:
            preds = np.full(len(X), 2.0)
        return np.maximum(0.2, preds)


class RidgeLoadModel(BaseForecaster):
    """Ridge Linear Regression model with feature scaling for electricity load forecasting."""

    def __init__(self, alpha: float = 1.0):
        super().__init__(model_name=ForecastingModelType.LINEAR_RIDGE.value, target_name="load_power_kw")
        self.alpha = alpha
        self.scaler = StandardScaler()
        self.model = Ridge(alpha=self.alpha, random_state=42)

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "RidgeLoadModel":
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
        return np.maximum(0.2, preds)


class RandomForestLoadModel(BaseForecaster):
    """Random Forest Regressor for non-linear load forecasting."""

    def __init__(self, n_estimators: int = 100, max_depth: int = 12):
        super().__init__(model_name=ForecastingModelType.RANDOM_FOREST.value, target_name="load_power_kw")
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=42,
            n_jobs=-1,
        )

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "RandomForestLoadModel":
        self.feature_names = list(X.columns)
        self.model.fit(X[self.feature_names], y.values)
        self.is_fitted = True
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before calling predict.")
        X_sub = X[self.feature_names]
        preds = self.model.predict(X_sub)
        return np.maximum(0.2, preds)


class XGBoostLoadModel(BaseForecaster):
    """XGBoost Gradient Boosted Trees for electricity demand forecasting."""

    def __init__(self, n_estimators: int = 150, max_depth: int = 6, learning_rate: float = 0.05):
        super().__init__(model_name=ForecastingModelType.XGBOOST.value, target_name="load_power_kw")
        self.model = xgb.XGBRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            random_state=42,
            n_jobs=-1,
            verbosity=0,
        )

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "XGBoostLoadModel":
        self.feature_names = list(X.columns)
        self.model.fit(X[self.feature_names], y.values)
        self.is_fitted = True
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before calling predict.")
        X_sub = X[self.feature_names]
        preds = self.model.predict(X_sub)
        return np.maximum(0.2, preds)


def get_load_model(model_type: str) -> BaseForecaster:
    """Factory function for load forecasting models."""
    model_type = model_type.upper()
    if model_type == ForecastingModelType.PERSISTENCE.value:
        return PersistenceLoadModel()
    elif model_type == ForecastingModelType.LINEAR_RIDGE.value:
        return RidgeLoadModel()
    elif model_type == ForecastingModelType.RANDOM_FOREST.value:
        return RandomForestLoadModel()
    elif model_type == ForecastingModelType.XGBOOST.value:
        return XGBoostLoadModel()
    else:
        raise ValueError(f"Unknown load model type: {model_type}")
