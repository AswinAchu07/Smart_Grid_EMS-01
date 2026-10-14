"""[UNIT TEST] Rule-Based EMS heuristic dispatch logic under diverse grid conditions.
"""

import pytest
from app.battery.model import Battery
from app.ems.rule_based import RuleBasedEMS


def test_rule_based_solar_surplus_charges_battery():
    """Solar (6kW) > Load (2kW): Supply 2kW to load, charge battery with remaining 4kW."""
    bat = Battery(capacity_kwh=10.0, initial_soc=0.50, max_charge_power_kw=5.0)
    dec = RuleBasedEMS.step(
        solar_kw=6.0,
        load_kw=2.0,
        battery=bat,
        import_price=0.18,
        export_price=0.08,
    )

    assert dec.solar_to_load_kw == 2.0
    assert pytest.approx(dec.solar_to_battery_kw, 1e-4) == 4.0
    assert pytest.approx(dec.solar_to_grid_kw, 1e-4) == 0.0
    assert dec.battery_to_load_kw == 0.0
    assert dec.grid_import_kw == 0.0
    assert dec.grid_export_kw == 0.0
    # Added energy = 4.0 * 0.95 = 3.8 kWh -> SOC = 0.50 + 0.38 = 0.88
    assert pytest.approx(dec.resulting_soc, 1e-4) == 0.88


def test_rule_based_solar_surplus_battery_full_exports_grid():
    """Solar (6kW) > Load (2kW) with full battery: Export entire 4kW surplus to grid."""
    bat = Battery(capacity_kwh=10.0, initial_soc=0.95, max_soc=0.95)
    dec = RuleBasedEMS.step(
        solar_kw=6.0,
        load_kw=2.0,
        battery=bat,
        import_price=0.18,
        export_price=0.08,
    )

    assert dec.solar_to_load_kw == 2.0
    assert dec.solar_to_battery_kw == 0.0
    assert dec.solar_to_grid_kw == 4.0
    assert dec.grid_export_kw == 4.0
    assert dec.grid_import_kw == 0.0
    assert dec.resulting_soc == 0.95
    # Export revenue = 4.0 kW * $0.08 = -$0.32
    assert pytest.approx(dec.cost, 1e-4) == -0.32


def test_rule_based_solar_deficit_discharges_battery():
    """Solar (1kW) < Load (4kW): Deficit 3kW covered by battery discharging."""
    bat = Battery(capacity_kwh=10.0, initial_soc=0.80, max_discharge_power_kw=5.0)
    dec = RuleBasedEMS.step(
        solar_kw=1.0,
        load_kw=4.0,
        battery=bat,
        import_price=0.18,
        export_price=0.08,
    )

    assert dec.solar_to_load_kw == 1.0
    assert dec.battery_to_load_kw == 3.0
    assert dec.grid_import_kw == 0.0
    assert dec.grid_export_kw == 0.0
    assert dec.solar_to_battery_kw == 0.0


def test_rule_based_solar_deficit_empty_battery_imports_grid():
    """Solar (0kW) < Load (3kW) with empty battery (min_soc): 100% grid import."""
    bat = Battery(capacity_kwh=10.0, initial_soc=0.15, min_soc=0.15)
    dec = RuleBasedEMS.step(
        solar_kw=0.0,
        load_kw=3.0,
        battery=bat,
        import_price=0.20,
        export_price=0.08,
    )

    assert dec.solar_to_load_kw == 0.0
    assert dec.battery_to_load_kw == 0.0
    assert dec.grid_import_kw == 3.0
    assert dec.cost == 3.0 * 0.20
    assert dec.resulting_soc == 0.15
