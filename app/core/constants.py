"""System-wide enums and domain constants.
"""

from enum import Enum


class UserRole(str, Enum):
    """Role-Based Access Control roles."""
    ADMIN = "ADMIN"
    RESEARCHER = "RESEARCHER"
    VIEWER = "VIEWER"


class EMSStrategy(str, Enum):
    """Supported Energy Management System strategies."""
    RULE_BASED = "RULE_BASED"
    OPTIMIZATION = "OPTIMIZATION"
    UNMANAGED = "UNMANAGED"


class ForecastingModelType(str, Enum):
    """Supported ML forecasting model architectures."""
    PERSISTENCE = "PERSISTENCE"
    LINEAR_RIDGE = "LINEAR_RIDGE"
    RANDOM_FOREST = "RANDOM_FOREST"
    XGBOOST = "XGBOOST"


class TargetType(str, Enum):
    """Forecasting target time series."""
    SOLAR = "solar"
    LOAD = "load"


class EnergyFlowDirection(str, Enum):
    """Energy flow pathway categories."""
    SOLAR_TO_LOAD = "solar_to_load"
    SOLAR_TO_BATTERY = "solar_to_battery"
    SOLAR_TO_GRID = "solar_to_grid"
    BATTERY_TO_LOAD = "battery_to_load"
    GRID_TO_LOAD = "grid_to_load"
    GRID_TO_BATTERY = "grid_to_battery"
    BATTERY_TO_GRID = "battery_to_grid"
