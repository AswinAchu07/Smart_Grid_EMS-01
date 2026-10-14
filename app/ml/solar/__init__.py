"""Solar PV forecasting models, training routines, and inference.
"""

from app.ml.solar.models import (
    PersistenceSolarModel,
    RidgeSolarModel,
    RandomForestSolarModel,
    XGBoostSolarModel,
    get_solar_model,
)

__all__ = [
    "PersistenceSolarModel",
    "RidgeSolarModel",
    "RandomForestSolarModel",
    "XGBoostSolarModel",
    "get_solar_model",
]
