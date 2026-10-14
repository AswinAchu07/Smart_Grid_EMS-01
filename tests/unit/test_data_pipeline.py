"""[UNIT TEST] Data pipeline, preprocessing, feature engineering, and zero-leakage splitting.
"""

import pytest
import pandas as pd
import numpy as np
from app.data.synthetic_generator import generate_synthetic_dataset
from app.data.preprocessor import DataPreprocessor
from app.data.features import FeatureEngineer


def test_synthetic_generator_properties():
    """Verify synthetic dataset generator shapes, column names, and non-negativity."""
    df = generate_synthetic_dataset(periods=168, seed=42)
    assert len(df) == 168
    assert "solar_power_kw" in df.columns
    assert "load_power_kw" in df.columns
    assert "irradiance_ghi_wm2" in df.columns
    assert (df["solar_power_kw"] >= 0.0).all()
    assert (df["load_power_kw"] >= 0.0).all()


def test_preprocessor_missing_and_duplicate_handling():
    """Verify interpolation of missing values and deduplication of timestamps."""
    raw_data = {
        "timestamp": [
            "2024-01-01 00:00:00",
            "2024-01-01 00:00:00",  # Duplicate
            "2024-01-01 01:00:00",
            "2024-01-01 03:00:00",  # Gap at 02:00:00
        ],
        "solar_power_kw": [0.0, 0.0, 0.0, 0.2],
        "load_power_kw": [1.5, 1.5, np.nan, 2.0],
        "temperature_c": [15.0, 15.0, 14.5, 14.0],
        "humidity_pct": [60.0, 60.0, 62.0, 65.0],
        "wind_speed_ms": [2.0, 2.0, 2.5, 3.0],
        "cloud_cover": [0.1, 0.1, 0.2, 0.3],
        "irradiance_ghi_wm2": [0.0, 0.0, 0.0, 50.0],
    }
    df_raw = pd.DataFrame(raw_data)
    preprocessor = DataPreprocessor()
    df_clean = preprocessor.clean_and_normalize(df_raw)

    # Should have 4 rows for 00:00, 01:00, 02:00, 03:00
    assert len(df_clean) == 4
    assert not df_clean.isna().any().any()


def test_chronological_split_prevents_leakage():
    """Verify that train, validation, and test datasets have strictly non-overlapping chronological boundaries."""
    df = generate_synthetic_dataset(periods=1000)
    train_df, val_df, test_df = DataPreprocessor.chronological_split(df, train_ratio=0.7, val_ratio=0.15)

    assert len(train_df) == 700
    assert len(val_df) == 150
    assert len(test_df) == 150

    # Ensure max train timestamp is strictly before min val timestamp
    assert train_df["timestamp"].max() < val_df["timestamp"].min()
    assert val_df["timestamp"].max() < test_df["timestamp"].min()


def test_feature_engineering_cyclic_and_lags():
    """Verify trigonometric feature encodings and autoregressive lags."""
    df = generate_synthetic_dataset(periods=200)
    df_feat, feat_cols = FeatureEngineer.prepare_feature_dataset(df, target_col="solar_power_kw")

    assert "hour_sin" in df_feat.columns
    assert "hour_cos" in df_feat.columns
    assert "solar_power_kw_lag_1" in df_feat.columns
    assert "solar_power_kw_lag_24" in df_feat.columns
    assert "solar_power_kw_roll_mean_24" in df_feat.columns
    assert not df_feat.isna().any().any()
