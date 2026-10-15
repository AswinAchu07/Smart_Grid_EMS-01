"""Unit tests for Live Weather and Real-Time Solar PV Service.
"""

import pytest
from app.services.weather_service import WeatherService


def test_preset_cities_availability():
    """Verify preset global smart grid cities contain valid coordinates."""
    cities = WeatherService.get_preset_cities()
    assert len(cities) >= 8
    for c in cities:
        assert "name" in c
        assert -90.0 <= c["latitude"] <= 90.0
        assert -180.0 <= c["longitude"] <= 180.0


def test_irradiance_to_pv_conversion_physics():
    """Verify conversion formula obeys zero night irradiance and temperature derating."""
    # Nighttime (GHI = 0) must produce 0 kW
    p_night = WeatherService.convert_irradiance_to_pv_power(ghi_w_m2=0.0, temp_c=25.0, pv_capacity_kw=5.0)
    assert p_night == 0.0

    # STC conditions (1000 W/m² @ 25°C) for 5 kW system with 96% inverter efficiency
    p_stc = WeatherService.convert_irradiance_to_pv_power(ghi_w_m2=1000.0, temp_c=25.0, pv_capacity_kw=5.0)
    assert 3.5 <= p_stc <= 5.2

    # Higher temperature (e.g. 45°C ambient) should produce lower power due to thermal derating
    p_hot = WeatherService.convert_irradiance_to_pv_power(ghi_w_m2=1000.0, temp_c=45.0, pv_capacity_kw=5.0)
    assert p_hot < p_stc


def test_weather_forecast_data_structure():
    """Verify forecast returns all hourly dimensions correctly."""
    forecast = WeatherService.get_live_forecast(latitude=28.6139, longitude=77.2090, pv_capacity_kw=5.0, forecast_days=1)
    assert "hourly" in forecast
    h = forecast["hourly"]
    assert "time" in h
    assert "temperature_c" in h
    assert "ghi_w_m2" in h
    assert "estimated_solar_kw" in h
    assert len(h["time"]) >= 24
    assert len(h["estimated_solar_kw"]) == len(h["time"])
