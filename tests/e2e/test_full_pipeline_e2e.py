"""[E2E TEST] Complete end-to-end integration across the entire system pipeline:

Data Ingestion & Cleaning
    ↓
ML Solar & Load Forecasting
    ↓
Battery Physical Model & SOC Dynamics
    ↓
Rule-Based EMS & MILP Optimization
    ↓
Microgrid Power Flow & Energy Conservation
    ↓
Database Transaction & Persistence
    ↓
FastAPI REST API Verification
"""

import pytest
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from app.data.synthetic_generator import generate_synthetic_dataset
from app.data.preprocessor import DataPreprocessor
from app.data.features import FeatureEngineer
from app.ml.solar.models import XGBoostSolarModel
from app.ml.load.models import XGBoostLoadModel
from app.battery.model import Battery
from app.optimization.lp_solver import OptimizationEMS
from app.simulation.engine import SimulationEngine
from app.simulation.evaluator import PerformanceEvaluator
from app.core.constants import EMSStrategy


def test_full_deterministic_pipeline_e2e(client: TestClient, admin_auth_headers):
    """End-to-End verification of the complete smart grid energy management pipeline."""
    # =========================================================================
    # Step 1: Deterministic Data Generation & Ingestion
    # =========================================================================
    periods = 720  # 30 full days of deterministic hourly test data
    raw_df = generate_synthetic_dataset(
        start_date="2024-06-01 00:00:00",
        periods=periods,
        pv_capacity_kw=6.0,
        seed=100,
    )
    assert len(raw_df) == periods
    assert "solar_power_kw" in raw_df.columns
    assert "load_power_kw" in raw_df.columns

    # =========================================================================
    # Step 2: Data Preprocessing & Leakage-Free Chronological Splitting
    # =========================================================================
    preprocessor = DataPreprocessor()
    df_clean = preprocessor.clean_and_normalize(raw_df)
    train_df, val_df, test_df = preprocessor.chronological_split(df_clean, train_ratio=0.6, val_ratio=0.2)

    assert len(train_df) > 0
    assert len(val_df) > 0
    assert len(test_df) > 0
    assert train_df["timestamp"].max() < val_df["timestamp"].min() < test_df["timestamp"].min()

    # =========================================================================
    # Step 3: Feature Engineering & ML Forecasting Model Training
    # =========================================================================
    # Solar features
    df_solar_feat, solar_feat_cols = FeatureEngineer.prepare_feature_dataset(df_clean, target_col="solar_power_kw")
    train_solar = df_solar_feat[df_solar_feat["timestamp"] <= train_df["timestamp"].max()]
    test_solar = df_solar_feat[df_solar_feat["timestamp"] >= test_df["timestamp"].min()]

    solar_model = XGBoostSolarModel(n_estimators=50, max_depth=4)
    solar_model.fit(train_solar[solar_feat_cols], train_solar["solar_power_kw"])
    solar_preds = solar_model.predict(test_solar[solar_feat_cols])

    # Load features
    df_load_feat, load_feat_cols = FeatureEngineer.prepare_feature_dataset(df_clean, target_col="load_power_kw")
    train_load = df_load_feat[df_load_feat["timestamp"] <= train_df["timestamp"].max()]
    test_load = df_load_feat[df_load_feat["timestamp"] >= test_df["timestamp"].min()]

    load_model = XGBoostLoadModel(n_estimators=50, max_depth=4)
    load_model.fit(train_load[load_feat_cols], train_load["load_power_kw"])
    load_preds = load_model.predict(test_load[load_feat_cols])

    assert len(solar_preds) == len(test_solar)
    assert len(load_preds) == len(test_load)
    assert (solar_preds >= 0.0).all()
    assert (load_preds >= 0.2).all()

    # =========================================================================
    # Step 4: Battery Model & Physical Bounds Verification
    # =========================================================================
    bat = Battery(
        capacity_kwh=10.0,
        initial_soc=0.50,
        min_soc=0.15,
        max_soc=0.95,
        max_charge_power_kw=5.0,
        max_discharge_power_kw=5.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
    )
    assert bat.soc == 0.50
    assert bat.get_max_charge_power() <= 5.0
    assert bat.get_max_discharge_power() <= 5.0

    # =========================================================================
    # Step 5: Optimization EMS Execution & Feasibility
    # =========================================================================
    horizon_len = min(24, len(solar_preds))
    solar_horizon = [float(v) for v in solar_preds[:horizon_len]]
    load_horizon = [float(v) for v in load_preds[:horizon_len]]
    prices_horizon = [0.10 if (h < 7 or h >= 23) else (0.35 if 16 <= h < 21 else 0.18) for h in range(horizon_len)]

    opt_result = OptimizationEMS.optimize_horizon(
        solar_forecast=solar_horizon,
        load_forecast=load_horizon,
        battery_initial=bat,
        import_prices=prices_horizon,
    )

    assert opt_result.is_feasible is True
    assert len(opt_result.decisions) == horizon_len

    # =========================================================================
    # Step 6: Power Conservation & Physical Energy Balance Check Across All Steps
    # =========================================================================
    for dec in opt_result.decisions:
        sources = dec.solar_kw + dec.battery_to_load_kw + dec.grid_import_kw
        sinks = dec.load_kw + dec.solar_to_battery_kw + dec.grid_export_kw
        assert abs(sources - sinks) < 1e-4, f"Energy conservation violated: sources={sources}, sinks={sinks}"

        # SOC strictly within bounds
        assert 0.15 <= dec.resulting_soc <= 0.95

        # No simultaneous charging and discharging
        assert not (dec.solar_to_battery_kw > 1e-4 and dec.battery_to_load_kw > 1e-4)

    # =========================================================================
    # Step 7: Multi-Strategy Simulation & Comparative Financial Savings
    # =========================================================================
    sim_eval_df = test_df.iloc[:horizon_len].reset_index(drop=True)
    engine_unm = SimulationEngine(battery=Battery())
    sum_unm = engine_unm.run_unmanaged(sim_eval_df)

    engine_rb = SimulationEngine(battery=Battery())
    sum_rb = engine_rb.run_rule_based(sim_eval_df)

    engine_opt = SimulationEngine(battery=Battery())
    sum_opt = engine_opt.run_optimization(sim_eval_df)

    comp_report = PerformanceEvaluator.compare_strategies(sum_unm, sum_rb, sum_opt)
    assert comp_report["opt_total_cost"] <= comp_report["unm_total_cost"]

    # =========================================================================
    # Step 8: FastAPI REST API Request & Response Schema Validation
    # =========================================================================
    # Configure battery via API
    bat_config_res = client.post(
        "/api/v1/battery/configure",
        json={
            "name": "E2E Verified Battery",
            "capacity_kwh": 10.0,
            "initial_soc": 0.50,
            "min_soc": 0.15,
            "max_soc": 0.95,
            "max_charge_power_kw": 5.0,
            "max_discharge_power_kw": 5.0,
            "charge_efficiency": 0.95,
            "discharge_efficiency": 0.95,
        },
        headers=admin_auth_headers,
    )
    assert bat_config_res.status_code == 201

    # Trigger simulation via API
    api_sim_res = client.post(
        "/api/v1/simulation/run",
        json={
            "strategy": "OPTIMIZATION",
            "duration_hours": 24,
            "initial_soc": 0.50,
            "save_to_db": True,
        },
        headers=admin_auth_headers,
    )
    assert api_sim_res.status_code == 200
    sim_json = api_sim_res.json()
    assert sim_json["id"] is not None
    assert sim_json["total_steps"] == 24
    assert len(sim_json["records"]) == 24

    # Verify persisted record retrieval from DB
    retrieved_res = client.get(f"/api/v1/simulation/{sim_json['id']}")
    assert retrieved_res.status_code == 200
    assert retrieved_res.json()["id"] == sim_json["id"]

    # Verify analytics endpoint
    analytics_res = client.get("/api/v1/analytics/summary")
    assert analytics_res.status_code == 200
    assert analytics_res.json()["total_simulations_run"] >= 1
