"""[UNIT TEST] Machine learning forecasters and metric calculations.
"""

import pytest
import numpy as np
import pandas as pd
from app.ml.metrics import evaluate_forecasting_metrics
from app.ml.solar.models import RidgeSolarModel, RandomForestSolarModel, XGBoostSolarModel
from app.ml.load.models import RidgeLoadModel, RandomForestLoadModel, XGBoostLoadModel


def test_metrics_evaluation_zero_tolerance():
    """Verify MAPE handles zero night-time values gracefully without zero-division explosion."""
    y_true = np.array([0.0, 0.0, 1.0, 2.0, 3.0])
    y_pred = np.array([0.01, 0.0, 1.1, 1.9, 3.2])

    metrics = evaluate_forecasting_metrics(y_true, y_pred, epsilon=0.05)
    assert metrics["mae"] > 0
    assert metrics["rmse"] > 0
    assert metrics["mape"] < 20.0
    assert metrics["r2"] > 0.90


def test_solar_models_fit_and_predict():
    """Verify Solar models train on dummy data and strictly enforce non-negative predictions."""
    X = pd.DataFrame({
        "hour": [0, 6, 12, 18, 23],
        "hour_sin": [0.0, 1.0, 0.0, -1.0, 0.0],
        "solar_power_kw_lag_1": [0.0, 0.1, 4.0, 0.5, 0.0],
        "solar_power_kw_lag_24": [0.0, 0.1, 4.2, 0.6, 0.0],
    })
    y = pd.Series([0.0, 0.2, 4.5, 0.6, 0.0])

    for ModelClass in [RidgeSolarModel, RandomForestSolarModel, XGBoostSolarModel]:
        model = ModelClass()
        model.fit(X, y)
        preds = model.predict(X)
        assert len(preds) == len(X)
        assert (preds >= 0.0).all()
        # Night hour 0 and 23 should be 0.0
        assert preds[0] == 0.0
        assert preds[-1] == 0.0
