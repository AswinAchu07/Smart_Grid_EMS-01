"""Probabilistic and Quantile Forecasting (P10, P50, P90) for Smart Grid EMS.

Provides confidence ribbons quantifying operational uncertainty for Solar PV generation
and Electricity Load demand.
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd


class QuantileForecaster:
    """Computes calibrated P10 (10th percentile), P50 (median), and P90 (90th percentile) forecast envelopes."""

    @classmethod
    def compute_solar_quantiles(
        cls,
        point_predictions: np.ndarray,
        hours: Optional[np.ndarray] = None,
        cloud_cover: Optional[np.ndarray] = None,
    ) -> Dict[str, np.ndarray]:
        """Compute physically-bounded Solar PV quantiles (P10, P50, P90).

        Parameters
        ----------
        point_predictions : np.ndarray
            Predicted solar power in kW.
        hours : Optional[np.ndarray]
            Hour of day (0-23).
        cloud_cover : Optional[np.ndarray]
            Cloud cover percentage (0-100%).

        Returns
        -------
        Dict[str, np.ndarray]
            Dictionary containing 'p10', 'p50', 'p90' arrays in kW.
        """
        n = len(point_predictions)
        preds = np.maximum(0.0, np.array(point_predictions, dtype=float))

        # Solar uncertainty scales with daytime irradiance and cloud transients
        # Clear noon has low relative error; partly cloudy has high variance
        relative_sigma = np.full(n, 0.15)
        if cloud_cover is not None and len(cloud_cover) == n:
            c = np.array(cloud_cover) / 100.0
            # Higher variance under intermediate cloud cover (broken clouds)
            relative_sigma = 0.08 + 0.28 * np.sin(np.pi * c)

        sigma = preds * relative_sigma + 0.02 * (preds > 0.05)

        # 10th and 90th percentiles using z = 1.282 for 80% coverage interval [P10, P90]
        z = 1.282
        p10 = np.maximum(0.0, preds - z * sigma)
        p50 = preds
        p90 = preds + z * sigma

        # Night zero enforcement
        if hours is not None and len(hours) == n:
            night_mask = (hours < 6) | (hours > 19)
            p10[night_mask] = 0.0
            p50[night_mask] = 0.0
            p90[night_mask] = 0.0

        # Enforce zero when median is 0
        zero_mask = preds <= 0.001
        p10[zero_mask] = 0.0
        p50[zero_mask] = 0.0
        p90[zero_mask] = 0.0

        # Monotonic sorting to ensure P10 <= P50 <= P90
        p10 = np.minimum(p10, p50)
        p90 = np.maximum(p90, p50)

        return {
            "p10": np.round(p10, 3),
            "p50": np.round(p50, 3),
            "p90": np.round(p90, 3),
        }

    @classmethod
    def compute_load_quantiles(
        cls,
        point_predictions: np.ndarray,
        hours: Optional[np.ndarray] = None,
        is_weekend: Optional[np.ndarray] = None,
    ) -> Dict[str, np.ndarray]:
        """Compute calibrated Electricity Load demand quantiles (P10, P50, P90).

        Parameters
        ----------
        point_predictions : np.ndarray
            Predicted load demand in kW.
        hours : Optional[np.ndarray]
            Hour of day (0-23).
        is_weekend : Optional[np.ndarray]
            Boolean flag for weekend days.

        Returns
        -------
        Dict[str, np.ndarray]
            Dictionary containing 'p10', 'p50', 'p90' arrays in kW.
        """
        n = len(point_predictions)
        preds = np.maximum(0.1, np.array(point_predictions, dtype=float))

        # Diurnal load uncertainty: higher variance during peak cooking/HVAC hours (18:00 - 22:00)
        relative_sigma = np.full(n, 0.10)
        if hours is not None and len(hours) == n:
            peak_mask = (hours >= 17) & (hours <= 22)
            sleep_mask = (hours >= 1) & (hours <= 5)
            relative_sigma[peak_mask] = 0.16
            relative_sigma[sleep_mask] = 0.06

        sigma = preds * relative_sigma

        z = 1.282  # 80% confidence interval
        p10 = np.maximum(0.05, preds - z * sigma)
        p50 = preds
        p90 = preds + z * sigma

        # Monotonicity check
        p10 = np.minimum(p10, p50)
        p90 = np.maximum(p90, p50)

        return {
            "p10": np.round(p10, 3),
            "p50": np.round(p50, 3),
            "p90": np.round(p90, 3),
        }
