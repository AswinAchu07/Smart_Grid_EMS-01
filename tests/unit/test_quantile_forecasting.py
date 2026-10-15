"""Unit tests for Probabilistic Quantile Forecasting (P10, P50, P90).
"""

import pytest
import numpy as np
from app.ml.quantile import QuantileForecaster


def test_solar_quantile_properties():
    """Verify solar quantiles enforce non-negativity, monotonicity, and night zeros."""
    preds = np.array([0.0, 0.0, 1.2, 3.5, 4.2, 2.8, 0.5, 0.0])
    hours = np.array([2, 5, 8, 12, 14, 16, 18, 22])

    q_dict = QuantileForecaster.compute_solar_quantiles(point_predictions=preds, hours=hours)
    p10 = q_dict["p10"]
    p50 = q_dict["p50"]
    p90 = q_dict["p90"]

    # 1. Monotonic ordering: P10 <= P50 <= P90
    assert np.all(p10 <= p50)
    assert np.all(p50 <= p90)

    # 2. Non-negativity
    assert np.all(p10 >= 0.0)

    # 3. Nighttime zero clamping
    assert p10[0] == 0.0 and p50[0] == 0.0 and p90[0] == 0.0
    assert p10[-1] == 0.0 and p50[-1] == 0.0 and p90[-1] == 0.0

    # 4. Daytime spread
    noon_idx = 3
    assert p10[noon_idx] < p50[noon_idx] < p90[noon_idx]


def test_load_quantile_properties():
    """Verify load quantiles enforce monotonicity and non-negativity."""
    preds = np.array([1.2, 1.0, 1.5, 2.8, 3.6, 2.4])
    hours = np.array([2, 5, 10, 15, 20, 23])

    q_dict = QuantileForecaster.compute_load_quantiles(point_predictions=preds, hours=hours)
    p10 = q_dict["p10"]
    p50 = q_dict["p50"]
    p90 = q_dict["p90"]

    assert np.all(p10 <= p50)
    assert np.all(p50 <= p90)
    assert np.all(p10 > 0.0)
