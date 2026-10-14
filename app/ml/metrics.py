"""Evaluation metrics for time-series forecasting models.
"""

from typing import Dict, Any
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def evaluate_forecasting_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    epsilon: float = 0.05,
) -> Dict[str, float]:
    """Calculate MAE, RMSE, MAPE (with near-zero thresholding), sMAPE, and R² score.

    Parameters
    ----------
    y_true : np.ndarray
        Ground truth observations
    y_pred : np.ndarray
        Model forecast predictions
    epsilon : float
        Threshold for MAPE non-zero filter (default 0.05 kW)

    Returns
    -------
    Dict[str, float]
        Dictionary of computed metric values
    """
    y_t = np.asarray(y_true, dtype=float).flatten()
    y_p = np.asarray(y_pred, dtype=float).flatten()

    mae = float(mean_absolute_error(y_t, y_p))
    rmse = float(np.sqrt(mean_squared_error(y_t, y_p)))
    r2 = float(r2_score(y_t, y_p))

    # MAPE computed on significant values (y_true > epsilon) to avoid zero-division exploding
    mask = y_t > epsilon
    if np.sum(mask) > 0:
        mape = float(np.mean(np.abs((y_t[mask] - y_p[mask]) / y_t[mask])) * 100.0)
    else:
        mape = 0.0

    # Symmetric MAPE (sMAPE)
    denominator = (np.abs(y_t) + np.abs(y_p)) / 2.0 + 1e-6
    smape = float(np.mean(np.abs(y_p - y_t) / denominator) * 100.0)

    return {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "mape": round(mape, 2),
        "smape": round(smape, 2),
        "r2": round(r2, 4),
    }
