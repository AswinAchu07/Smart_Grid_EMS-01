"""Live Weather and Real-Time Solar PV generation REST API endpoints.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Query
from app.schemas.weather import (
    LiveWeatherForecastRequest,
    LiveWeatherForecastResponse,
    WeatherCityPreset,
)
from app.services.weather_service import WeatherService

router = APIRouter(prefix="/weather", tags=["Live Global Weather"])


@router.get("/cities", response_model=List[WeatherCityPreset])
def get_preset_cities():
    """Retrieve list of pre-configured global smart grid benchmark cities."""
    return WeatherService.get_preset_cities()


@router.post("/forecast", response_model=LiveWeatherForecastResponse)
def get_live_weather_forecast(payload: LiveWeatherForecastRequest):
    """Fetch live global weather telemetry and physics-derived solar PV generation curve."""
    data = WeatherService.get_live_forecast(
        latitude=payload.latitude,
        longitude=payload.longitude,
        pv_capacity_kw=payload.pv_capacity_kw,
        forecast_days=payload.forecast_days,
    )
    return LiveWeatherForecastResponse(**data)
