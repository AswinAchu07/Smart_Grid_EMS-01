"""[UNIT TEST] Optimization-based EMS (MILP) solver feasibility and cost minimization.
"""

import pytest
from app.battery.model import Battery
from app.optimization.lp_solver import OptimizationEMS


def test_optimization_solver_24h_feasibility():
    """Verify MILP solver executes smoothly and returns optimal feasible schedule."""
    solar_24h = [0.0]*6 + [0.5, 1.5, 3.5, 5.0, 5.5, 5.0, 3.8, 2.0, 0.5] + [0.0]*9
    load_24h = [1.5, 1.2, 1.1, 1.0, 1.2, 2.0, 3.5, 3.0, 2.5, 2.8, 3.0, 3.2, 3.0, 3.5, 4.0, 5.2, 5.8, 5.5, 4.2, 3.5, 2.8, 2.2, 1.8, 1.5]
    # TOU prices: peak at hours 16-20 ($0.35), standard ($0.18), off-peak ($0.10)
    prices = [0.10]*7 + [0.18]*9 + [0.35]*5 + [0.18]*3

    bat = Battery(capacity_kwh=10.0, initial_soc=0.50)
    res = OptimizationEMS.optimize_horizon(
        solar_forecast=solar_24h,
        load_forecast=load_24h,
        battery_initial=bat,
        import_prices=prices,
    )

    assert res.is_feasible is True
    assert len(res.decisions) == 24
    assert len(res.soc_trajectory) == 24

    for dec in res.decisions:
        # Check no simultaneous charge & discharge
        assert not (dec.solar_to_battery_kw > 1e-4 and dec.battery_to_load_kw > 1e-4)
        # Check bounds
        assert 0.15 <= dec.resulting_soc <= 0.95


def test_optimization_fallback_on_empty_horizon():
    """Verify error handling on degenerate inputs."""
    bat = Battery(capacity_kwh=10.0)
    with pytest.raises(ValueError):
        OptimizationEMS.optimize_horizon(
            solar_forecast=[],
            load_forecast=[],
            battery_initial=bat,
        )
