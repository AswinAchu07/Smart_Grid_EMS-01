"""Pydantic schemas for Live Global Weather and Real-Time Solar PV Telemetry.
"""

from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class WeatherCityPreset(BaseModel):
    name: str
    country: str
    latitude: float
    longitude: float
    elevation_m: Optional[float] = None
    timezone: str = "auto"


class LiveWeatherHourly(BaseModel):
    time: List[str]
    temperature_c: List[float]
    cloud_cover_pct: List[float]
    ghi_w_m2: List[float]
    estimated_solar_kw: List[float]


class LiveWeatherForecastRequest(BaseModel):
    latitude: float = Field(default=28.6139, ge=-90.0, le=90.0, description="Latitude")
    longitude: float = Field(default=77.2090, ge=-180.0, le=180.0, description="Longitude")
    pv_capacity_kw: float = Field(default=5.0, gt=0, description="PV System Capacity in kW")
    forecast_days: int = Field(default=2, ge=1, le=7, description="Number of days to forecast")


class LiveWeatherForecastResponse(BaseModel):
    city_name: Optional[str] = None
    latitude: float
    longitude: float
    elevation_m: float
    timezone: str
    pv_capacity_kw: float
    current_temp_c: float
    current_cloud_cover_pct: float
    current_ghi_w_m2: float
    current_estimated_pv_kw: float
    hourly: LiveWeatherHourly
    source: str = "Open-Meteo Global Numerical Weather Model"
