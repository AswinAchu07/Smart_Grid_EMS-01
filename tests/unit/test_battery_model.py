"""[UNIT TEST] Battery electrochemical model, physical constraints, and SOC updates.
"""

import pytest
from app.battery.model import Battery
from app.battery.constraints import BatteryConstraints


def test_battery_initialization():
    """Verify default initialization parameters and SOC calculation."""
    bat = Battery(capacity_kwh=10.0, initial_soc=0.50)
    assert bat.capacity_kwh == 10.0
    assert bat.soc == 0.50
    assert bat.stored_energy_kwh == 5.0
    assert bat.min_soc == 0.15
    assert bat.max_soc == 0.95


def test_battery_invalid_configurations():
    """Verify rejection of non-physical battery parameters."""
    with pytest.raises(ValueError, match="strictly positive"):
        Battery(capacity_kwh=-5.0)

    with pytest.raises(ValueError, match="Invalid SOC bounds"):
        Battery(capacity_kwh=10.0, min_soc=0.8, max_soc=0.2)

    with pytest.raises(ValueError, match="Efficiencies must be between"):
        Battery(capacity_kwh=10.0, charge_efficiency=1.5)


def test_battery_charging_within_limits(standard_battery):
    """Verify normal charging increases SOC correctly according to efficiency equation."""
    actual_ch, actual_dis, new_soc = standard_battery.step(charge_kw=2.0, discharge_kw=0.0, dt_hours=1.0)
    assert actual_ch == 2.0
    assert actual_dis == 0.0
    assert pytest.approx(new_soc, 1e-4) == 0.69
    assert standard_battery.total_charged_kwh == 2.0


def test_battery_discharging_within_limits(standard_battery):
    """Verify normal discharging decreases SOC correctly accounting for discharge efficiency."""
    actual_ch, actual_dis, new_soc = standard_battery.step(charge_kw=0.0, discharge_kw=1.9, dt_hours=1.0)
    assert actual_ch == 0.0
    assert actual_dis == 1.9
    assert pytest.approx(new_soc, 1e-4) == 0.30
    assert standard_battery.total_discharged_kwh == 1.9


def test_battery_max_soc_clamping():
    """Verify that charging is clamped when battery reaches max_soc (95%)."""
    bat = Battery(capacity_kwh=10.0, initial_soc=0.90, max_soc=0.95, charge_efficiency=1.0)
    max_ch = bat.get_max_charge_power(dt_hours=1.0)
    assert pytest.approx(max_ch, 1e-4) == 0.50

    actual_ch, _, new_soc = bat.step(charge_kw=5.0, discharge_kw=0.0, dt_hours=1.0)
    assert pytest.approx(actual_ch, 1e-4) == 0.50
    assert pytest.approx(new_soc, 1e-4) == 0.95


def test_battery_min_soc_clamping():
    """Verify that discharging is clamped when battery reaches min_soc (15%)."""
    bat = Battery(capacity_kwh=10.0, initial_soc=0.20, min_soc=0.15, discharge_efficiency=1.0)
    max_dis = bat.get_max_discharge_power(dt_hours=1.0)
    assert pytest.approx(max_dis, 1e-4) == 0.50

    _, actual_dis, new_soc = bat.step(charge_kw=0.0, discharge_kw=5.0, dt_hours=1.0)
    assert pytest.approx(actual_dis, 1e-4) == 0.50
    assert pytest.approx(new_soc, 1e-4) == 0.15


def test_battery_max_power_limits():
    """Verify power rate limits are strictly enforced regardless of huge requests."""
    bat = Battery(capacity_kwh=100.0, initial_soc=0.50, max_charge_power_kw=10.0, max_discharge_power_kw=8.0)
    max_ch = bat.get_max_charge_power(dt_hours=1.0)
    assert max_ch <= 10.0

    max_dis = bat.get_max_discharge_power(dt_hours=1.0)
    assert max_dis <= 8.0


def test_forbid_simultaneous_charging_and_discharging(standard_battery):
    """Verify simultaneous charge and discharge triggers an error."""
    with pytest.raises(ValueError, match="Simultaneous charging and discharging"):
        standard_battery.step(charge_kw=2.0, discharge_kw=2.0)
