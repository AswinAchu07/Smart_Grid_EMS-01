"""Rule-Based Energy Management System heuristic baseline algorithm.
"""

from typing import Dict, Any
from dataclasses import dataclass
from app.battery.model import Battery


@dataclass
class EMSDispatchDecision:
    """Dataclass holding all power flows and states for a single timestep dispatch decision."""
    solar_kw: float
    load_kw: float
    solar_to_load_kw: float
    solar_to_battery_kw: float
    solar_to_grid_kw: float
    battery_to_load_kw: float
    grid_import_kw: float
    grid_export_kw: float
    resulting_soc: float
    cost: float
    energy_balance_error: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "solar_kw": round(self.solar_kw, 4),
            "load_kw": round(self.load_kw, 4),
            "solar_to_load_kw": round(self.solar_to_load_kw, 4),
            "solar_to_battery_kw": round(self.solar_to_battery_kw, 4),
            "solar_to_grid_kw": round(self.solar_to_grid_kw, 4),
            "battery_to_load_kw": round(self.battery_to_load_kw, 4),
            "grid_import_kw": round(self.grid_import_kw, 4),
            "grid_export_kw": round(self.grid_export_kw, 4),
            "soc": round(self.resulting_soc, 4),
            "resulting_soc": round(self.resulting_soc, 4),
            "cost": round(self.cost, 4),
            "energy_balance_error": round(self.energy_balance_error, 8),
        }


class RuleBasedEMS:
    """Heuristic rule-based energy management system.

    Prioritizes:
    1. Direct Solar PV to Load self-consumption.
    2. Surplus Solar -> Battery charging (up to max_charge and max_soc).
    3. Residual Surplus Solar -> Grid export.
    4. Deficit -> Battery discharging (up to max_discharge and min_soc).
    5. Residual Deficit -> Grid import.
    """

    @staticmethod
    def step(
        solar_kw: float,
        load_kw: float,
        battery: Battery,
        import_price: float = 0.18,
        export_price: float = 0.08,
        dt_hours: float = 1.0,
    ) -> EMSDispatchDecision:
        """Execute one timestep of heuristic dispatch and update battery state."""
        solar_kw = max(0.0, float(solar_kw))
        load_kw = max(0.0, float(load_kw))

        if solar_kw >= load_kw:
            # Solar Surplus
            solar_to_load = load_kw
            surplus = solar_kw - load_kw

            max_charge = battery.get_max_charge_power(dt_hours=dt_hours)
            solar_to_battery = min(surplus, max_charge)
            solar_to_grid = surplus - solar_to_battery

            battery_to_load = 0.0
            grid_import = 0.0
            grid_export = solar_to_grid

            # Apply battery charge
            _, _, resulting_soc = battery.step(
                charge_kw=solar_to_battery, discharge_kw=0.0, dt_hours=dt_hours
            )
        else:
            # Solar Deficit
            solar_to_load = solar_kw
            deficit = load_kw - solar_kw

            max_discharge = battery.get_max_discharge_power(dt_hours=dt_hours)
            battery_to_load = min(deficit, max_discharge)
            grid_import = deficit - battery_to_load

            solar_to_battery = 0.0
            solar_to_grid = 0.0
            grid_export = 0.0

            # Apply battery discharge
            _, _, resulting_soc = battery.step(
                charge_kw=0.0, discharge_kw=battery_to_load, dt_hours=dt_hours
            )

        # Physical Energy Balance Check:
        sources = solar_kw + battery_to_load + grid_import
        sinks = load_kw + solar_to_battery + grid_export
        balance_error = abs(sources - sinks)

        # Cost calculation
        step_cost = (grid_import * import_price - grid_export * export_price) * dt_hours

        return EMSDispatchDecision(
            solar_kw=solar_kw,
            load_kw=load_kw,
            solar_to_load_kw=solar_to_load,
            solar_to_battery_kw=solar_to_battery,
            solar_to_grid_kw=solar_to_grid,
            battery_to_load_kw=battery_to_load,
            grid_import_kw=grid_import,
            grid_export_kw=grid_export,
            resulting_soc=resulting_soc,
            cost=step_cost,
            energy_balance_error=balance_error,
        )
