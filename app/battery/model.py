"""Physics-based Battery Energy Storage System (BESS) state simulation model.
"""

from typing import Dict, Any, Tuple, Optional, List
from app.battery.constraints import BatteryConstraints


class Battery:
    """Simulates electrochemical battery state of charge (SOC), power limits, and efficiency losses."""

    def __init__(
        self,
        capacity_kwh: float = 10.0,
        initial_soc: float = 0.50,
        min_soc: float = 0.15,
        max_soc: float = 0.95,
        max_charge_power_kw: float = 5.0,
        max_discharge_power_kw: float = 5.0,
        charge_efficiency: float = 0.95,
        discharge_efficiency: float = 0.95,
        initial_soh: float = 1.0,
    ):
        BatteryConstraints.validate_config(
            capacity_kwh=capacity_kwh,
            min_soc=min_soc,
            max_soc=max_soc,
            max_charge_power_kw=max_charge_power_kw,
            max_discharge_power_kw=max_discharge_power_kw,
            charge_efficiency=charge_efficiency,
            discharge_efficiency=discharge_efficiency,
        )

        self.capacity_kwh = float(capacity_kwh)
        self.min_soc = float(min_soc)
        self.max_soc = float(max_soc)
        self.max_charge_power_kw = float(max_charge_power_kw)
        self.max_discharge_power_kw = float(max_discharge_power_kw)
        self.charge_efficiency = float(charge_efficiency)
        self.discharge_efficiency = float(discharge_efficiency)

        # Initial SOC initialization bounded within limits
        self.soc = float(min(max(initial_soc, self.min_soc), self.max_soc))
        self.soh = float(min(1.0, max(0.0, initial_soh)))
        self.total_charged_kwh: float = 0.0
        self.total_discharged_kwh: float = 0.0
        self.soc_history: list[float] = [self.soc]


    @property
    def stored_energy_kwh(self) -> float:
        """Currently stored usable energy in kWh."""
        return self.soc * self.capacity_kwh

    @property
    def usable_capacity_kwh(self) -> float:
        """Total usable energy capacity between min_soc and max_soc in kWh."""
        return (self.max_soc - self.min_soc) * self.capacity_kwh

    def get_max_charge_power(self, dt_hours: float = 1.0) -> float:
        """Calculate maximum allowable charging power (kW) at the terminals for timestep dt."""
        if self.soc >= self.max_soc:
            return 0.0
        # Energy room to max_soc
        energy_room_kwh = (self.max_soc - self.soc) * self.capacity_kwh
        # Terminal power needed to deliver this internal energy room
        power_limit_soc = energy_room_kwh / (self.charge_efficiency * dt_hours)
        return float(min(self.max_charge_power_kw, max(0.0, power_limit_soc)))

    def get_max_discharge_power(self, dt_hours: float = 1.0) -> float:
        """Calculate maximum allowable discharge power (kW) deliverable at terminals for timestep dt."""
        if self.soc <= self.min_soc:
            return 0.0
        # Usable energy above min_soc
        usable_energy_kwh = (self.soc - self.min_soc) * self.capacity_kwh
        # Terminal power delivered accounting for internal discharge losses
        power_limit_soc = (usable_energy_kwh * self.discharge_efficiency) / dt_hours
        return float(min(self.max_discharge_power_kw, max(0.0, power_limit_soc)))

    def step(
        self,
        charge_kw: float = 0.0,
        discharge_kw: float = 0.0,
        dt_hours: float = 1.0,
    ) -> Tuple[float, float, float]:
        """Apply charge/discharge power over dt_hours and update SOC according to conservation laws.

        Returns
        -------
        Tuple[float, float, float]
            (actual_charge_kw, actual_discharge_kw, updated_soc)
        """
        # Validate inputs
        BatteryConstraints.validate_action(charge_kw=charge_kw, discharge_kw=discharge_kw)

        # Enforce physical ceilings
        max_ch = self.get_max_charge_power(dt_hours=dt_hours)
        max_dis = self.get_max_discharge_power(dt_hours=dt_hours)

        actual_ch = min(max(0.0, charge_kw), max_ch)
        actual_dis = min(max(0.0, discharge_kw), max_dis)

        # Update SOC state equation
        # SOC_next = SOC_t + (P_ch * eta_ch * dt)/C - (P_dis * dt) / (eta_dis * C)
        delta_soc_ch = (actual_ch * self.charge_efficiency * dt_hours) / self.capacity_kwh
        delta_soc_dis = (actual_dis * dt_hours) / (self.discharge_efficiency * self.capacity_kwh)

        self.soc = float(min(max(self.soc + delta_soc_ch - delta_soc_dis, self.min_soc), self.max_soc))

        self.total_charged_kwh += actual_ch * dt_hours
        self.total_discharged_kwh += actual_dis * dt_hours
        self.soc_history.append(self.soc)

        return actual_ch, actual_dis, self.soc

    def evaluate_degradation(
        self,
        dt_hours: float = 1.0,
        temp_celsius: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Compute ASTM E1049-85 Rainflow & physics degradation assessment over accumulated history."""
        from app.battery.degradation import BatteryDegradationModel

        model = BatteryDegradationModel(
            nominal_capacity_kwh=self.capacity_kwh,
            ambient_temp_celsius=25.0 if temp_celsius is None else temp_celsius,
        )
        report = model.evaluate_soc_trajectory(
            soc_trajectory=self.soc_history,
            dt_hours=dt_hours,
            initial_soh=self.soh,
            temp_celsius=temp_celsius,
        )
        self.soh = report["final_soh"]
        return report

    def get_status(self) -> Dict[str, Any]:
        """Return comprehensive telemetry snapshot of the battery."""
        return {
            "capacity_kwh": self.capacity_kwh,
            "soh": round(self.soh, 4),
            "soh_pct": round(self.soh * 100.0, 2),
            "effective_capacity_kwh": round(self.capacity_kwh * self.soh, 3),
            "soc": round(self.soc, 4),
            "soc_pct": round(self.soc * 100.0, 2),
            "stored_energy_kwh": round(self.stored_energy_kwh, 3),
            "min_soc": self.min_soc,
            "max_soc": self.max_soc,
            "max_charge_power_kw": self.max_charge_power_kw,
            "max_discharge_power_kw": self.max_discharge_power_kw,
            "charge_efficiency": self.charge_efficiency,
            "discharge_efficiency": self.discharge_efficiency,
            "total_charged_kwh": round(self.total_charged_kwh, 3),
            "total_discharged_kwh": round(self.total_discharged_kwh, 3),
            "equivalent_cycles": round(self.total_discharged_kwh / max(1.0, self.capacity_kwh), 2),
        }

