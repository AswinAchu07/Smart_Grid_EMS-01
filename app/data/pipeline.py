"""Complete data pipeline orchestration for loading, preprocessing, and preparing ML matrices.
"""

from typing import Tuple, List, Optional, Dict
import os
import pandas as pd
from app.data.synthetic_generator import generate_synthetic_dataset
from app.data.preprocessor import DataPreprocessor
from app.data.features import FeatureEngineer


_RAW_DATA_CACHE: Dict[str, pd.DataFrame] = {}
_PIPELINE_CACHE: Dict[Tuple, Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, List[str]]] = {}


class SmartGridDataPipeline:
    """Orchestrates data ingestion, validation, cleaning, feature engineering, and dataset splitting."""

    def __init__(self, data_path: Optional[str] = None):
        self.data_path = data_path
        self.preprocessor = DataPreprocessor()
        self.feature_engineer = FeatureEngineer()

    def get_or_create_raw_data(self, default_save_path: str = "data/sample/smart_grid_data.csv") -> pd.DataFrame:
        """Load dataset from file path if it exists, or generate a realistic synthetic dataset."""
        target_path = self.data_path or default_save_path

        if target_path in _RAW_DATA_CACHE:
            return _RAW_DATA_CACHE[target_path].copy()

        if target_path and os.path.exists(target_path):
            df = pd.read_csv(target_path)
        else:
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            df = generate_synthetic_dataset(save_path=target_path)

        _RAW_DATA_CACHE[target_path] = df
        return df.copy()

    def run_pipeline(
        self,
        target_col: str,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        default_save_path: str = "data/sample/smart_grid_data.csv",
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, List[str]]:
        """Execute full data pipeline: Ingestion -> Cleaning -> Splitting -> Feature Engineering.

        Returns
        -------
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, List[str]]
            (train_feat_df, val_feat_df, test_feat_df, feature_cols)
        """
        cache_key = (
            target_col,
            train_ratio,
            val_ratio,
            default_save_path,
            self.data_path,
        )
        if cache_key in _PIPELINE_CACHE:
            cached_train, cached_val, cached_test, cached_cols = _PIPELINE_CACHE[cache_key]
            return cached_train.copy(), cached_val.copy(), cached_test.copy(), list(cached_cols)

        # 1. Ingestion
        df_raw = self.get_or_create_raw_data(default_save_path=default_save_path)

        # 2. Validation & Preprocessing
        self.preprocessor.validate_schema(df_raw)
        df_clean = self.preprocessor.clean_and_normalize(df_raw)

        # 3. Chronological Split (prevents future leakage)
        train_raw, val_raw, test_raw = self.preprocessor.chronological_split(
            df_clean, train_ratio=train_ratio, val_ratio=val_ratio
        )

        # 4. Feature Engineering on full cleaned data then sliced to preserve lag continuity
        df_feat, feature_cols = self.feature_engineer.prepare_feature_dataset(
            df_clean, target_col=target_col, drop_na=True
        )

        # Slice features according to split dates
        train_end_ts = train_raw["timestamp"].max()
        val_end_ts = val_raw["timestamp"].max()

        train_feat = df_feat[df_feat["timestamp"] <= train_end_ts].reset_index(drop=True)
        val_feat = df_feat[
            (df_feat["timestamp"] > train_end_ts) & (df_feat["timestamp"] <= val_end_ts)
        ].reset_index(drop=True)
        test_feat = df_feat[df_feat["timestamp"] > val_end_ts].reset_index(drop=True)

        _PIPELINE_CACHE[cache_key] = (train_feat, val_feat, test_feat, feature_cols)
        return train_feat.copy(), val_feat.copy(), test_feat.copy(), list(feature_cols)
