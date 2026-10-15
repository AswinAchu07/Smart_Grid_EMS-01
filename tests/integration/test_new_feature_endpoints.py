"""Integration tests for new standout API endpoints:
1. Battery Degradation & Rainflow
2. Live Global Weather API
3. SHAP Model Explainability
4. Quantile Data Points
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_battery_degradation_endpoint():
    """Verify POST /api/v1/battery/degradation returns valid physics metrics."""
    payload = {
        "soc_trajectory": [0.5, 0.8, 0.3, 0.9, 0.4, 0.7, 0.5],
        "capacity_kwh": 10.0,
        "initial_soh": 1.0,
        "dt_hours": 1.0,
        "temp_celsius": 28.0,
    }
    response = client.post("/api/v1/battery/degradation", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "final_soh" in data
    assert 0.8 <= data["final_soh"] <= 1.0
    assert "projected_rul_years" in data
    assert "dod_histogram" in data
    assert "equivalent_full_cycles" in data


def test_weather_cities_endpoint():
    """Verify GET /api/v1/weather/cities returns global benchmark locations."""
    response = client.get("/api/v1/weather/cities")
    assert response.status_code == 200
    cities = response.json()
    assert isinstance(cities, list)
    assert len(cities) >= 8
    assert any(c["name"] == "New Delhi" for c in cities)


def test_weather_forecast_endpoint():
    """Verify POST /api/v1/weather/forecast returns hourly solar generation."""
    payload = {
        "latitude": 28.6139,
        "longitude": 77.2090,
        "pv_capacity_kw": 5.0,
        "forecast_days": 1,
    }
    response = client.post("/api/v1/weather/forecast", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["latitude"] == 28.6139
    assert "hourly" in data
    assert len(data["hourly"]["estimated_solar_kw"]) >= 24


def test_solar_and_load_explain_endpoints():
    """Verify POST /api/v1/forecasts/solar/explain and /load/explain endpoints."""
    # Solar explain
    resp_solar = client.post("/api/v1/forecasts/solar/explain?model_type=XGBOOST&sample_index=12")
    assert resp_solar.status_code == 200
    data_solar = resp_solar.json()
    assert "global_importances" in data_solar
    assert "local_attributions" in data_solar
    assert len(data_solar["global_importances"]) > 0

    # Load explain
    resp_load = client.post("/api/v1/forecasts/load/explain?model_type=XGBOOST&sample_index=18")
    assert resp_load.status_code == 200
    data_load = resp_load.json()
    assert "global_importances" in data_load
    assert "local_attributions" in data_load
    assert len(data_load["global_importances"]) > 0


def test_forecast_endpoint_includes_quantiles():
    """Verify POST /api/v1/forecasts/solar includes p10, p50, p90 in data points."""
    resp = client.post("/api/v1/forecasts/solar?model_type=XGBOOST&horizon_hours=24")
    assert resp.status_code == 200
    data = resp.json()
    dp = data["data_points"][12]  # midday
    assert "p10" in dp
    assert "p50" in dp
    assert "p90" in dp
    assert dp["p10"] is not None
    assert dp["p10"] <= dp["p50"] <= dp["p90"]
