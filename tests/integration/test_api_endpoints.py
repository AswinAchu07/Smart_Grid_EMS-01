"""[INTEGRATION TEST] FastAPI REST Endpoints validation, serialization, and status codes.
"""

import pytest
from fastapi.testclient import TestClient


def test_health_check_endpoint(client: TestClient):
    """Verify GET /api/v1/health returns 200 and healthy payload."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_forecasts_api_endpoints(client: TestClient):
    """Verify POST /api/v1/forecasts/solar and /load return valid forecast structures."""
    # Solar
    res_solar = client.post("/api/v1/forecasts/solar?horizon_hours=12")
    assert res_solar.status_code == 200
    solar_data = res_solar.json()
    assert solar_data["target_type"] == "solar"
    assert len(solar_data["data_points"]) == 12

    # Load
    res_load = client.post("/api/v1/forecasts/load?horizon_hours=12")
    assert res_load.status_code == 200
    load_data = res_load.json()
    assert load_data["target_type"] == "load"
    assert len(load_data["data_points"]) == 12


def test_model_benchmarks_api_endpoints(client: TestClient):
    """Verify GET /api/v1/forecasts/solar/models and /load/models."""
    res_solar_models = client.get("/api/v1/forecasts/solar/models")
    assert res_solar_models.status_code == 200
    assert "XGBOOST" in res_solar_models.json()["models"]

    res_load_models = client.get("/api/v1/forecasts/load/models")
    assert res_load_models.status_code == 200
    assert "XGBOOST" in res_load_models.json()["models"]


def test_battery_api_endpoints(client: TestClient):
    """Verify GET /api/v1/battery/status and POST /api/v1/battery/configure."""
    res_status = client.get("/api/v1/battery/status")
    assert res_status.status_code == 200
    data = res_status.json()
    assert "soc" in data
    assert "capacity_kwh" in data

    # Configure
    config_payload = {
        "name": "Test 15kWh Battery",
        "capacity_kwh": 15.0,
        "initial_soc": 0.60,
        "min_soc": 0.10,
        "max_soc": 0.90,
        "max_charge_power_kw": 6.0,
        "max_discharge_power_kw": 6.0,
        "charge_efficiency": 0.94,
        "discharge_efficiency": 0.94,
    }
    res_conf = client.post("/api/v1/battery/configure", json=config_payload)
    assert res_conf.status_code == 201
    assert res_conf.json()["capacity_kwh"] == 15.0


def test_ems_decision_endpoint(client: TestClient):
    """Verify POST /api/v1/ems/decision."""
    payload = {
        "solar_kw": 5.0,
        "load_kw": 2.5,
        "current_soc": 0.5,
        "import_price": 0.18,
        "export_price": 0.08,
        "battery_capacity_kwh": 10.0,
    }
    res = client.post("/api/v1/ems/decision", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["solar_to_load_kw"] == 2.5
    assert data["solar_to_battery_kw"] > 0.0
    assert data["energy_balance_error"] < 1e-4


def test_optimization_run_endpoint(client: TestClient):
    """Verify POST /api/v1/optimization/run."""
    payload = {
        "solar_forecast": [0.0, 1.0, 4.0, 5.0, 2.0, 0.0],
        "load_forecast": [1.5, 2.0, 3.0, 3.5, 4.0, 2.5],
        "initial_soc": 0.5,
        "battery_capacity_kwh": 10.0,
    }
    res = client.post("/api/v1/optimization/run", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_feasible"] is True
    assert len(data["decisions"]) == 6


def test_simulation_run_and_retrieve_endpoint(client: TestClient):
    """Verify POST /api/v1/simulation/run and GET /api/v1/simulation/{id}."""
    sim_req = {
        "strategy": "OPTIMIZATION",
        "duration_hours": 24,
        "initial_soc": 0.5,
        "save_to_db": True,
    }
    res = client.post("/api/v1/simulation/run", json=sim_req)
    assert res.status_code == 200
    sim_data = res.json()
    assert sim_data["id"] is not None
    sim_id = sim_data["id"]

    # Retrieve
    res_get = client.get(f"/api/v1/simulation/{sim_id}")
    assert res_get.status_code == 200
    assert res_get.json()["total_steps"] == 24


def test_analytics_endpoints(client: TestClient):
    """Verify GET /api/v1/analytics/summary and /comparison."""
    res_sum = client.get("/api/v1/analytics/summary")
    assert res_sum.status_code == 200
    assert "latest_strategy_comparison" in res_sum.json()

    res_comp = client.get("/api/v1/analytics/comparison?duration_hours=48")
    assert res_comp.status_code == 200
    assert "comparison_table" in res_comp.json()
