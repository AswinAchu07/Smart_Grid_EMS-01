"""Training script for Electricity Load forecasting models.
"""

from typing import Dict, Any, Tuple
import os
import pandas as pd
from app.data.pipeline import SmartGridDataPipeline
from app.ml.load.models import (
    PersistenceLoadModel,
    RidgeLoadModel,
    RandomForestLoadModel,
    XGBoostLoadModel,
)


def train_load_models(
    data_path: str = "data/sample/smart_grid_data.csv",
    save_dir: str = "models/saved/load",
) -> Dict[str, Dict[str, Any]]:
    """Train all 4 load forecasting models, evaluate on test set, and save artifacts."""
    pipeline = SmartGridDataPipeline(data_path=data_path)
    train_df, val_df, test_df, feature_cols = pipeline.run_pipeline(
        target_col="load_power_kw", default_save_path=data_path
    )

    X_train = train_df[feature_cols]
    y_train = train_df["load_power_kw"]
    X_val = val_df[feature_cols]
    y_val = val_df["load_power_kw"]
    X_test = test_df[feature_cols]
    y_test = test_df["load_power_kw"]

    models = [
        PersistenceLoadModel(),
        RidgeLoadModel(),
        RandomForestLoadModel(),
        XGBoostLoadModel(),
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
        save_path = os.path.join(save_dir, f"load_{model.model_name.lower()}.joblib")
        model.save(save_path)

        results[model.model_name] = {
            "validation_metrics": val_metrics,
            "test_metrics": test_metrics,
            "artifact_path": save_path,
        }

    return results


if __name__ == "__main__":
    metrics = train_load_models()
    for m_name, res in metrics.items():
        print(f"Load Model: {m_name} -> Test Metrics: {res['test_metrics']}")
