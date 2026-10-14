"""Data validation, cleaning, missing-value interpolation, and chronological splitting.
"""

from typing import Tuple, Optional, List
import pandas as pd
import numpy as np


class DataPreprocessor:
    """Preprocesses raw time-series smart grid datasets ensuring data integrity and zero leakage."""

    REQUIRED_COLUMNS = [
        "timestamp",
        "solar_power_kw",
        "load_power_kw",
        "temperature_c",
        "humidity_pct",
        "wind_speed_ms",
        "cloud_cover",
        "irradiance_ghi_wm2",
    ]

    PHYSICAL_BOUNDS = {
        "solar_power_kw": (0.0, 100.0),
        "load_power_kw": (0.0, 100.0),
        "temperature_c": (-50.0, 60.0),
        "humidity_pct": (0.0, 100.0),
        "wind_speed_ms": (0.0, 75.0),
        "cloud_cover": (0.0, 1.0),
        "irradiance_ghi_wm2": (0.0, 1500.0),
        "grid_import_price": (0.0, 10.0),
        "grid_export_price": (0.0, 10.0),
    }

    def __init__(self, freq: str = "1h"):
        self.freq = freq

    def validate_schema(self, df: pd.DataFrame) -> bool:
        """Validate that all mandatory columns are present in the DataFrame."""
        missing = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns in dataset: {missing}")
        return True

    def clean_and_normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean raw DataFrame, handle duplicates, sort timestamps, interpolate missing, and apply physical bounds."""
        df_clean = df.copy()

        # 1. Parse and ensure datetime
        if not pd.api.types.is_datetime64_any_dtype(df_clean["timestamp"]):
            df_clean["timestamp"] = pd.to_datetime(df_clean["timestamp"], errors="coerce")

        # Drop invalid timestamps
        df_clean = df_clean.dropna(subset=["timestamp"])

        # 2. Sort chronologically
        df_clean = df_clean.sort_values("timestamp")

        # 3. Handle duplicate timestamps by averaging numeric columns
        if df_clean["timestamp"].duplicated().any():
            df_clean = df_clean.groupby("timestamp", as_index=False).mean()

        # 4. Set timestamp index and reindex to complete hourly grid
        df_clean = df_clean.set_index("timestamp")
        full_idx = pd.date_range(start=df_clean.index.min(), end=df_clean.index.max(), freq=self.freq)
        df_clean = df_clean.reindex(full_idx)
        df_clean.index.name = "timestamp"

        # 5. Handle missing values via time-based linear interpolation with forward/backward fallback
        df_clean = df_clean.interpolate(method="time", limit_direction="both")
        df_clean = df_clean.bfill().ffill()

        # 6. Apply physical bound clipping
        for col, (min_val, max_val) in self.PHYSICAL_BOUNDS.items():
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].clip(lower=min_val, upper=max_val)

        # 7. Add default tariff prices if missing
        if "grid_import_price" not in df_clean.columns:
            df_clean["grid_import_price"] = 0.18
        if "grid_export_price" not in df_clean.columns:
            df_clean["grid_export_price"] = 0.08

        return df_clean.reset_index()

    @staticmethod
    def chronological_split(
        df: pd.DataFrame,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Split time-series data chronologically to strictly avoid future data leakage.

        Parameters
        ----------
        df : pd.DataFrame
            Preprocessed DataFrame with chronological sorting
        train_ratio : float
            Proportion of data for training (e.g. 0.70)
        val_ratio : float
            Proportion of data for validation (e.g. 0.15)

        Returns
        -------
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
            (train_df, val_df, test_df)
        """
        n = len(df)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))

        train_df = df.iloc[:train_end].copy().reset_index(drop=True)
        val_df = df.iloc[train_end:val_end].copy().reset_index(drop=True)
        test_df = df.iloc[val_end:].copy().reset_index(drop=True)

        return train_df, val_df, test_df
