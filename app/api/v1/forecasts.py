"""Forecasting API endpoints for Solar PV generation and Electricity Load demand.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.constants import TargetType, ForecastingModelType, UserRole
from app.db.session import get_db
from app.db.models import User
from app.api.deps import get_current_user_optional, require_role
from app.schemas.forecast import ForecastResponse, ModelMetricsResponse, ShapExplanationResponse
from app.services.forecast_service import ForecastService

router = APIRouter(prefix="/forecasts", tags=["Forecasting"])
forecast_service = ForecastService()



@router.post("/solar", response_model=ForecastResponse)
def get_solar_forecast(
    model_type: ForecastingModelType = Query(default=ForecastingModelType.XGBOOST),
    horizon_hours: int = Query(default=24, ge=1, le=168),
    start_time: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    """Generate Solar PV generation forecast using specified ML architecture."""
    return forecast_service.generate_forecast(
        target_type=TargetType.SOLAR,
        model_type=model_type,
        horizon_hours=horizon_hours,
        start_time=start_time,
        db=db,
        user=user,
    )


@router.post("/load", response_model=ForecastResponse)
def get_load_forecast(
    model_type: ForecastingModelType = Query(default=ForecastingModelType.XGBOOST),
    horizon_hours: int = Query(default=24, ge=1, le=168),
    start_time: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    """Generate Electricity Load demand forecast using specified ML architecture."""
    return forecast_service.generate_forecast(
        target_type=TargetType.LOAD,
        model_type=model_type,
        horizon_hours=horizon_hours,
        start_time=start_time,
        db=db,
        user=user,
    )


@router.get("/solar/models", response_model=ModelMetricsResponse)
def get_solar_model_benchmarks():
    """Retrieve comparative accuracy metrics (MAE, RMSE, MAPE, R2) across all 4 Solar ML models."""
    res = forecast_service.get_all_model_benchmarks(target_type=TargetType.SOLAR)
    return ModelMetricsResponse(**res)


@router.get("/load/models", response_model=ModelMetricsResponse)
def get_load_model_benchmarks():
    """Retrieve comparative accuracy metrics (MAE, RMSE, MAPE, R2) across all 4 Load ML models."""
    res = forecast_service.get_all_model_benchmarks(target_type=TargetType.LOAD)
    return ModelMetricsResponse(**res)


@router.post("/solar/explain", response_model=ShapExplanationResponse)
def explain_solar_forecast(
    model_type: ForecastingModelType = Query(default=ForecastingModelType.XGBOOST),
    sample_index: int = Query(default=0, ge=0, le=99),
):
    """Retrieve SHAP TreeExplainer feature attributions for Solar PV forecasting model."""
    res = forecast_service.explain_forecast(
        target_type=TargetType.SOLAR,
        model_type=model_type,
        sample_index=sample_index,
    )
    return ShapExplanationResponse(**res)


@router.post("/load/explain", response_model=ShapExplanationResponse)
def explain_load_forecast(
    model_type: ForecastingModelType = Query(default=ForecastingModelType.XGBOOST),
    sample_index: int = Query(default=0, ge=0, le=99),
):
    """Retrieve SHAP TreeExplainer feature attributions for Electricity Load demand forecasting model."""
    res = forecast_service.explain_forecast(
        target_type=TargetType.LOAD,
        model_type=model_type,
        sample_index=sample_index,
    )
    return ShapExplanationResponse(**res)

