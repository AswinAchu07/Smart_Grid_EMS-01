"""Unit tests for ASTM E1049-85 Rainflow cycle counting and battery degradation.
"""

import pytest
import numpy as np
from app.battery.degradation import RainflowCycleExtractor, BatteryDegradationModel
from app.battery.model import Battery


def test_rainflow_cycle_extraction():
    """Verify Rainflow extraction on synthetic peak-valley SOC profile."""
    soc_series = [0.5, 0.9, 0.2, 0.8, 0.4, 0.5]
    cycles = RainflowCycleExtractor.count_cycles(soc_series)
    assert len(cycles) > 0
    for dod, count in cycles:
        assert 0.0 <= dod <= 1.0
        assert count in [0.5, 1.0]


def test_battery_degradation_wohler_and_calendar():
    """Verify Wöhler fatigue damage increases with DOD and Arrhenius with temperature."""
    model_25c = BatteryDegradationModel(ambient_temp_celsius=25.0)
    model_45c = BatteryDegradationModel(ambient_temp_celsius=45.0)

    # Deeper DOD should result in fewer cycles to failure (higher damage)
    n_shallow = model_25c.cycles_to_failure(dod=0.20)
    n_deep = model_25c.cycles_to_failure(dod=0.80)
    assert n_shallow > n_deep

    d_shallow = model_25c.calculate_cycle_damage(dod=0.20)
    d_deep = model_25c.calculate_cycle_damage(dod=0.80)
    assert d_deep > d_shallow

    # 45°C ambient temperature should accelerate calendar aging vs 25°C
    cal_25 = model_25c.calculate_calendar_damage(duration_hours=100.0, mean_soc=0.6)
    cal_45 = model_45c.calculate_calendar_damage(duration_hours=100.0, mean_soc=0.6, temp_celsius=45.0)
    assert cal_45 > cal_25


def test_evaluate_soc_trajectory():
    """Verify full evaluation report metrics and bounds."""
    model = BatteryDegradationModel(nominal_capacity_kwh=10.0)
    soc_traj = [0.5 + 0.3 * np.sin(2 * np.pi * i / 24.0) for i in range(48)]

    report = model.evaluate_soc_trajectory(soc_traj, dt_hours=1.0, initial_soh=1.0)
    assert report["initial_soh"] == 1.0
    assert 0.8 <= report["final_soh"] <= 1.0
    assert report["soh_loss_pct"] >= 0.0
    assert report["projected_rul_years"] > 0.0
    assert "0-20%" in report["dod_histogram"]
    assert report["equivalent_full_cycles"] > 0.0


def test_battery_model_degradation_integration():
    """Verify Battery class evaluates degradation over live operational history."""
    bat = Battery(capacity_kwh=10.0, initial_soc=0.5)
    for _ in range(5):
        bat.step(charge_kw=3.0, dt_hours=1.0)
        bat.step(discharge_kw=3.0, dt_hours=1.0)

    report = bat.evaluate_degradation(dt_hours=1.0)
    assert report["final_soh"] <= 1.0
    assert bat.soh == report["final_soh"]
    assert bat.get_status()["soh"] == pytest.approx(report["final_soh"], abs=1e-4)

