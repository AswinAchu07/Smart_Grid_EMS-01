"""Forecasting request and response Pydantic schemas.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.core.constants import TargetType, ForecastingModelType


class ForecastRequest(BaseModel):
    """Payload to request a forecast."""
    target_type: TargetType = Field(default=TargetType.SOLAR, description="Target: 'solar' or 'load'")
    model_type: ForecastingModelType = Field(default=ForecastingModelType.XGBOOST, description="Model algorithm")
    horizon_hours: int = Field(default=24, ge=1, le=168, description="Forecast horizon steps (1 to 168 hours)")
    start_time: Optional[str] = Field(default=None, description="Optional starting timestamp filter")


class ForecastDataPointSchema(BaseModel):
    step: int
    timestamp: str
    predicted_value: float
    actual_value: Optional[float] = None
    p10: Optional[float] = None
    p50: Optional[float] = None
    p90: Optional[float] = None


class ForecastResponse(BaseModel):
    target_type: str
    model_name: str
    horizon_hours: int
    data_points: List[ForecastDataPointSchema]
    metrics: Optional[Dict[str, float]] = None


class ModelMetricsResponse(BaseModel):
    target_type: str
    models: Dict[str, Dict[str, Any]]


class ShapGlobalImportanceItem(BaseModel):
    feature: str
    importance: float


class ShapLocalAttributionItem(BaseModel):
    feature: str
    value: float
    shap_value: float
    direction: str


class ShapExplanationResponse(BaseModel):
    target_type: str
    model_name: str
    base_value: float
    predicted_value: float
    sample_index: int
    global_importances: List[ShapGlobalImportanceItem]
    local_attributions: List[ShapLocalAttributionItem]
    has_native_shap: bool

