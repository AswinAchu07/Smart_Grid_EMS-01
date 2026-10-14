"""Validation and constraints enforcement for Battery Energy Storage Systems (BESS).
"""

from typing import Tuple


class BatteryConstraints:
    """Validates physical parameters and operational bounds for battery storage."""

    @staticmethod
    def validate_config(
        capacity_kwh: float,
        min_soc: float,
        max_soc: float,
        max_charge_power_kw: float,
        max_discharge_power_kw: float,
        charge_efficiency: float,
        discharge_efficiency: float,
    ) -> bool:
        """Validate that all battery hardware configuration parameters satisfy physical constraints."""
        if capacity_kwh <= 0.0:
            raise ValueError(f"Battery capacity must be strictly positive, got {capacity_kwh} kWh.")
        if not (0.0 <= min_soc < max_soc <= 1.0):
            raise ValueError(f"Invalid SOC bounds: min_soc={min_soc}, max_soc={max_soc}. Must satisfy 0 <= min < max <= 1.")
        if max_charge_power_kw <= 0.0 or max_discharge_power_kw <= 0.0:
            raise ValueError("Max charge and discharge power ratings must be strictly positive.")
        if not (0.5 <= charge_efficiency <= 1.0) or not (0.5 <= discharge_efficiency <= 1.0):
            raise ValueError("Efficiencies must be between 0.50 (50%) and 1.00 (100%).")
        return True

    @staticmethod
    def validate_action(
        charge_kw: float,
        discharge_kw: float,
        tolerance: float = 1e-6,
    ) -> bool:
        """Ensure no negative power and no simultaneous charging and discharging."""
        if charge_kw < -tolerance or discharge_kw < -tolerance:
            raise ValueError(f"Negative power flow detected: charge={charge_kw} kW, discharge={discharge_kw} kW.")
        if charge_kw > tolerance and discharge_kw > tolerance:
            raise ValueError(
                f"Simultaneous charging and discharging is physically forbidden: charge={charge_kw} kW, discharge={discharge_kw} kW."
            )
        return True
