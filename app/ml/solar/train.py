"""Training script for Solar PV forecasting models.
"""

from typing import Dict, Any, Tuple
import os
import pandas as pd
from app.data.pipeline import SmartGridDataPipeline
from app.ml.solar.models import (
    PersistenceSolarModel,
    RidgeSolarModel,
    RandomForestSolarModel,
    XGBoostSolarModel,
)


def train_solar_models(
    data_path: str = "data/sample/smart_grid_data.csv",
    save_dir: str = "models/saved/solar",
) -> Dict[str, Dict[str, Any]]:
    """Train all 4 solar forecasting models, evaluate on test set, and save artifacts."""
    pipeline = SmartGridDataPipeline(data_path=data_path)
    train_df, val_df, test_df, feature_cols = pipeline.run_pipeline(
        target_col="solar_power_kw", default_save_path=data_path
    )

    X_train = train_df[feature_cols]
    y_train = train_df["solar_power_kw"]
    X_val = val_df[feature_cols]
    y_val = val_df["solar_power_kw"]
    X_test = test_df[feature_cols]
    y_test = test_df["solar_power_kw"]

    models = [
        PersistenceSolarModel(),
        RidgeSolarModel(),
        RandomForestSolarModel(),
        XGBoostSolarModel(),
    ]

    os.makedirs(save_dir, exist_ok=True)
    results = {}

    for model in models:
        # Fit on training data
        model.fit(X_train, y_train)

        # Evaluate on validation and test data
        val_metrics = model.evaluate(X_val, y_val)
        test_metrics = model.evaluate(X_test, y_test)

        # Save model artifact
        save_path = os.path.join(save_dir, f"solar_{model.model_name.lower()}.joblib")
        model.save(save_path)

        results[model.model_name] = {
            "validation_metrics": val_metrics,
            "test_metrics": test_metrics,
            "artifact_path": save_path,
        }

    return results


if __name__ == "__main__":
    metrics = train_solar_models()
    for m_name, res in metrics.items():
        print(f"Solar Model: {m_name} -> Test Metrics: {res['test_metrics']}")
