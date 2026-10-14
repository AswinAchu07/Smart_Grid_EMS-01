"""[UNIT TEST] Strict physical power conservation and energy balance checks.
"""

import pytest
import numpy as np
from app.battery.model import Battery
from app.ems.rule_based import RuleBasedEMS
from app.optimization.lp_solver import OptimizationEMS


def test_rule_based_energy_balance_matrix():
    """Verify exact power conservation across 100 diverse random test operating points."""
    np.random.seed(42)
    solar_points = np.random.uniform(0.0, 10.0, size=100)
    load_points = np.random.uniform(0.5, 8.0, size=100)

    bat = Battery(capacity_kwh=10.0, initial_soc=0.5)

    for solar, load in zip(solar_points, load_points):
        dec = RuleBasedEMS.step(
            solar_kw=solar,
            load_kw=load,
            battery=bat,
            import_price=0.18,
            export_price=0.08,
            dt_hours=1.0,
        )

        sources = dec.solar_kw + dec.battery_to_load_kw + dec.grid_import_kw
        sinks = dec.load_kw + dec.solar_to_battery_kw + dec.grid_export_kw

        # Tolerance 1e-5 kW
        assert abs(sources - sinks) < 1e-5
        assert dec.energy_balance_error < 1e-5
        assert 0.15 <= dec.resulting_soc <= 0.95


def test_optimization_energy_balance():
    """Verify power balance across a multi-step MILP horizon."""
    solar_seq = [0.0, 0.0, 1.2, 4.5, 6.0, 5.2, 3.1, 0.5, 0.0, 0.0]
    load_seq = [1.5, 1.2, 2.0, 3.5, 4.0, 3.8, 4.5, 5.0, 3.0, 2.0]

    bat = Battery(capacity_kwh=10.0, initial_soc=0.5)
    opt_res = OptimizationEMS.optimize_horizon(
        solar_forecast=solar_seq,
        load_forecast=load_seq,
        battery_initial=bat,
    )

    assert opt_res.is_feasible is True
    for dec in opt_res.decisions:
        sources = dec.solar_kw + dec.battery_to_load_kw + dec.grid_import_kw
        sinks = dec.load_kw + dec.solar_to_battery_kw + dec.grid_export_kw
        assert abs(sources - sinks) < 1e-4
        assert 0.15 <= dec.resulting_soc <= 0.95
