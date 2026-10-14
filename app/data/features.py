"""Feature engineering for Solar PV and Electricity Load time-series forecasting.
"""

from typing import List, Tuple, Optional
import pandas as pd
import numpy as np


class FeatureEngineer:
    """Extracts cyclic time features, calendar indicators, autoregressive lags, and rolling statistics."""

    @staticmethod
    def create_cyclic_and_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
        """Generate cyclic trigonometric encodings and calendar features from timestamp."""
        df_feat = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df_feat["timestamp"]):
            df_feat["timestamp"] = pd.to_datetime(df_feat["timestamp"])

        dt = df_feat["timestamp"].dt
        hour = dt.hour
        day_of_week = dt.weekday
        day_of_year = dt.dayofyear
        month = dt.month

        # Cyclic Trigonometric encodings
        df_feat["hour_sin"] = np.sin(2 * np.pi * hour / 24.0)
        df_feat["hour_cos"] = np.cos(2 * np.pi * hour / 24.0)
        df_feat["dow_sin"] = np.sin(2 * np.pi * day_of_week / 7.0)
        df_feat["dow_cos"] = np.cos(2 * np.pi * day_of_week / 7.0)
        df_feat["doy_sin"] = np.sin(2 * np.pi * day_of_year / 365.25)
        df_feat["doy_cos"] = np.cos(2 * np.pi * day_of_year / 365.25)
        df_feat["month_sin"] = np.sin(2 * np.pi * month / 12.0)
        df_feat["month_cos"] = np.cos(2 * np.pi * month / 12.0)

        # Calendar categorical features
        df_feat["hour"] = hour
        df_feat["weekday"] = day_of_week
        df_feat["month"] = month
        df_feat["is_weekend"] = (day_of_week >= 5).astype(int)
        df_feat["is_peak_hours"] = ((hour >= 16) & (hour <= 21)).astype(int)

        # HVAC temperature triggers
        if "temperature_c" in df_feat.columns:
            temp = df_feat["temperature_c"]
            df_feat["cooling_degree_metric"] = np.maximum(0.0, temp - 24.0)
            df_feat["heating_degree_metric"] = np.maximum(0.0, 15.0 - temp)

        return df_feat

    @staticmethod
    def create_lag_and_rolling_features(
        df: pd.DataFrame,
        target_col: str,
        lags: List[int] = [1, 2, 3, 24, 48, 168],
        rolling_windows: List[int] = [6, 24],
    ) -> pd.DataFrame:
        """Create autoregressive lag and rolling window features for a specific target series."""
        df_feat = df.copy()

        # Lag features
        for lag in lags:
            df_feat[f"{target_col}_lag_{lag}"] = df_feat[target_col].shift(lag)

        # Rolling statistics (using shift(1) to avoid data leakage from current timestep)
        shifted = df_feat[target_col].shift(1)
        for window in rolling_windows:
            df_feat[f"{target_col}_roll_mean_{window}"] = shifted.rolling(window=window, min_periods=1).mean()
            df_feat[f"{target_col}_roll_std_{window}"] = shifted.rolling(window=window, min_periods=1).std().fillna(0.0)
            df_feat[f"{target_col}_roll_max_{window}"] = shifted.rolling(window=window, min_periods=1).max()
            df_feat[f"{target_col}_roll_min_{window}"] = shifted.rolling(window=window, min_periods=1).min()

        return df_feat

    @classmethod
    def prepare_feature_dataset(
        def_cls,
        df: pd.DataFrame,
        target_col: str,
        lags: List[int] = [1, 2, 3, 24, 48, 168],
        rolling_windows: List[int] = [6, 24],
        drop_na: bool = True,
    ) -> Tuple[pd.DataFrame, List[str]]:
        """End-to-end feature pipeline generating complete feature matrix and feature column names."""
        # 1. Cyclic & calendar features
        df_proc = def_cls.create_cyclic_and_calendar_features(df)

        # 2. Lag and rolling statistics for target series
        df_proc = def_cls.create_lag_and_rolling_features(
            df_proc, target_col=target_col, lags=lags, rolling_windows=rolling_windows
        )

        # Also add weather rolling features if available
        if "irradiance_ghi_wm2" in df_proc.columns:
            df_proc["ghi_lag_24"] = df_proc["irradiance_ghi_wm2"].shift(24)
        if "temperature_c" in df_proc.columns:
            df_proc["temp_lag_24"] = df_proc["temperature_c"].shift(24)

        if drop_na:
            df_proc = df_proc.dropna().reset_index(drop=True)

        # Exclude non-feature columns
        exclude_cols = [
            "timestamp",
            "solar_power_kw",
            "load_power_kw",
            "grid_import_price",
            "grid_export_price",
        ]
        feature_cols = [c for c in df_proc.columns if c not in exclude_cols]

        return df_proc, feature_cols
