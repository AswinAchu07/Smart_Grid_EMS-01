"""Physics-informed battery degradation and State of Health (SOH) model.

Implements:
1. ASTM E1049-85 Rainflow Cycle Counting algorithm to extract discrete stress cycles from SOC trajectories.
2. Wöhler-like empirical cycle fatigue curve (DOD-dependent capacity fade).
3. Arrhenius-based calendar aging model with temperature and average SOC stress.
4. Cumulative State of Health (SOH) estimation and Remaining Useful Life (RUL) projection.
"""

from typing import List, Dict, Any, Tuple, Optional
import math
import numpy as np

try:
    import rainflow
    HAS_RAINFLOW = True
except ImportError:
    HAS_RAINFLOW = False


class RainflowCycleExtractor:
    """Extracts stress cycles and depth-of-discharge (DOD) from continuous SOC time series."""

    @staticmethod
    def _fallback_rainflow_count(series: List[float]) -> List[Tuple[float, float]]:
        """Pure-Python implementation of peak-valley filtering and simplified range counting."""
        if len(series) < 2:
            return []

        # 1. Filter consecutive duplicates and find turning points
        reversals = [series[0]]
        for i in range(1, len(series) - 1):
            d1 = series[i] - reversals[-1]
            d2 = series[i + 1] - series[i]
            if (d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0):
                reversals.append(series[i])
        reversals.append(series[-1])

        # 2. Extract ranges
        cycles = []
        for i in range(len(reversals) - 1):
            rng = abs(reversals[i + 1] - reversals[i])
            if rng > 1e-4:
                cycles.append((rng, 0.5))
        return cycles

    @classmethod
    def count_cycles(cls, soc_history: List[float]) -> List[Tuple[float, float]]:
        """Returns a list of (dod_range, cycle_count) tuples."""
        if not soc_history or len(soc_history) < 2:
            return []

        if HAS_RAINFLOW:
            try:
                raw_cycles = list(rainflow.count_cycles(soc_history))
                # Ensure values are within [0, 1] range
                return [(float(min(1.0, max(0.0, rng))), float(cnt)) for rng, cnt in raw_cycles if rng > 1e-4]
            except Exception:
                pass
        return cls._fallback_rainflow_count(soc_history)


class BatteryDegradationModel:
    """Physics-informed degradation and SOH life assessment for Lithium-ion cells.

    Attributes
    ----------
    nominal_cycles_80dod : float
        Rated cycle life at 80% Depth-of-Discharge (e.g., 4000 cycles for modern LFP/NMC).
    nominal_cost_per_kwh : float
        Replacement capital cost per kWh ($/kWh), default $250.
    eol_soh_threshold : float
        End of Life SOH threshold where battery is deemed retired, standard 0.80 (80%).
    arrhenius_activation_energy : float
        Activation energy Ea in J/mol for Li-ion calendar aging (~31.5 kJ/mol).
    """

    def __init__(
        self,
        nominal_cycles_80dod: float = 4000.0,
        fatigue_exponent: float = 1.6,
        nominal_cost_per_kwh: float = 250.0,
        eol_soh_threshold: float = 0.80,
        ambient_temp_celsius: float = 25.0,
        nominal_capacity_kwh: float = 10.0,
    ):
        self.nominal_cycles_80dod = float(nominal_cycles_80dod)
        self.b = float(fatigue_exponent)
        self.nominal_cost_per_kwh = float(nominal_cost_per_kwh)
        self.eol_soh_threshold = float(eol_soh_threshold)
        self.ambient_temp_celsius = float(ambient_temp_celsius)
        self.nominal_capacity_kwh = float(nominal_capacity_kwh)

        # Precompute reference fatigue constant: N_fail(0.8) = a * (0.8)^(-b)
        # Hence a = nominal_cycles_80dod * (0.8^b)
        self.a = self.nominal_cycles_80dod * (0.80 ** self.b)

    def cycles_to_failure(self, dod: float) -> float:
        """Estimate cycles to EOL (20% capacity loss) for a given Depth-of-Discharge (DOD)."""
        dod_clamped = max(0.01, min(1.0, dod))
        # Power law relationship: N = a * DOD^(-b)
        return float(self.a * (dod_clamped ** (-self.b)))

    def calculate_cycle_damage(self, dod: float, cycle_count: float = 1.0) -> float:
        """Fraction of total battery fatigue life consumed by this cycle."""
        n_fail = self.cycles_to_failure(dod)
        return float(cycle_count / max(1.0, n_fail))

    def calculate_calendar_damage(
        self,
        duration_hours: float,
        mean_soc: float = 0.50,
        temp_celsius: Optional[float] = None,
    ) -> float:
        """Calculate calendar aging damage over duration_hours using Arrhenius kinetics and SOC stress."""
        t_c = self.ambient_temp_celsius if temp_celsius is None else temp_celsius
        t_kelvin = t_c + 273.15
        t_ref_kelvin = 298.15  # 25°C

        # Arrhenius thermal acceleration factor (Ea/R ~ 3788 K)
        arrhenius_factor = math.exp(3788.0 * (1.0 / t_ref_kelvin - 1.0 / t_kelvin))

        # SOC stress factor (SEI passivation layer growth accelerates above 60% SOC)
        soc_factor = math.exp(0.8 * (max(0.0, min(1.0, mean_soc)) - 0.5))

        # Baseline calendar rate: ~2% capacity fade per year (8760 hours) at 25°C and 50% SOC
        hourly_cal_base_rate = (0.02 / 8760.0) / (1.0 - self.eol_soh_threshold)
        return float(hourly_cal_base_rate * duration_hours * arrhenius_factor * soc_factor)

    def evaluate_soc_trajectory(
        self,
        soc_trajectory: List[float],
        dt_hours: float = 1.0,
        initial_soh: float = 1.0,
        temp_celsius: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Perform comprehensive ASTM E1049-85 Rainflow & physics degradation assessment.

        Parameters
        ----------
        soc_trajectory : List[float]
            Chronological SOC series bounded between 0.0 and 1.0.
        dt_hours : float
            Timestep size in hours.
        initial_soh : float
            State of Health prior to trajectory (1.0 = brand new 100%).
        temp_celsius : Optional[float]
            Ambient operating temperature.

        Returns
        -------
        Dict[str, Any]
            Full physics diagnostics including SOH fade, RUL, DOD histogram, and economic cost.
        """
        if not soc_trajectory or len(soc_trajectory) < 2:
            return {
                "initial_soh": initial_soh,
                "final_soh": initial_soh,
                "soh_loss_pct": 0.0,
                "cyclic_damage": 0.0,
                "calendar_damage": 0.0,
                "total_damage": 0.0,
                "cycle_count_half": 0,
                "cycle_count_full": 0,
                "equivalent_full_cycles": 0.0,
                "economic_degradation_cost": 0.0,
                "projected_rul_years": 15.0,
                "dod_histogram": {},
            }

        # 1. Rainflow Cycle Extraction
        cycles = RainflowCycleExtractor.count_cycles(soc_trajectory)

        # 2. Cyclic Fatigue Damage
        cyclic_damage = 0.0
        dod_bins = {
            "0-20%": 0.0,
            "20-40%": 0.0,
            "40-60%": 0.0,
            "60-80%": 0.0,
            "80-100%": 0.0,
        }
        half_cycles = 0
        full_cycles = 0

        for dod, count in cycles:
            damage = self.calculate_cycle_damage(dod, count)
            cyclic_damage += damage

            if count < 0.9:
                half_cycles += 1
            else:
                full_cycles += 1

            dod_pct = dod * 100.0
            if dod_pct < 20.0:
                dod_bins["0-20%"] += count
            elif dod_pct < 40.0:
                dod_bins["20-40%"] += count
            elif dod_pct < 60.0:
                dod_bins["40-60%"] += count
            elif dod_pct < 80.0:
                dod_bins["60-80%"] += count
            else:
                dod_bins["80-100%"] += count

        # 3. Calendar Aging Damage
        duration_hours = len(soc_trajectory) * dt_hours
        mean_soc = float(np.mean(soc_trajectory))
        calendar_damage = self.calculate_calendar_damage(
            duration_hours=duration_hours,
            mean_soc=mean_soc,
            temp_celsius=temp_celsius,
        )

        # Total battery degradation (fraction of lifetime to 80% EOL)
        total_damage = cyclic_damage + calendar_damage

        # Actual capacity loss percentage (out of nominal capacity)
        # At total_damage = 1.0, 20% capacity is lost (EOL)
        soh_loss_fraction = total_damage * (1.0 - self.eol_soh_threshold)
        final_soh = max(0.0, initial_soh - soh_loss_fraction)

        # Equivalent Full Cycles (EFC)
        efc = sum(dod * count for dod, count in cycles)

        # Economic degradation cost ($)
        # Total battery capital value = capacity_kwh * cost_per_kwh
        replacement_value = self.nominal_capacity_kwh * self.nominal_cost_per_kwh
        economic_cost = total_damage * replacement_value * (1.0 - self.eol_soh_threshold)

        # Projected Remaining Useful Life (RUL) in years
        # If running at this hourly rate
        if total_damage > 1e-7 and duration_hours > 0:
            damage_per_hour = total_damage / duration_hours
            remaining_damage_to_eol = max(0.0, 1.0 - (1.0 - final_soh) / (1.0 - self.eol_soh_threshold))
            rul_hours = remaining_damage_to_eol / damage_per_hour
            rul_years = min(25.0, rul_hours / 8760.0)
        else:
            rul_years = 20.0

        return {
            "initial_soh": round(initial_soh, 5),
            "final_soh": round(final_soh, 5),
            "final_soh_pct": round(final_soh * 100.0, 2),
            "soh_loss_pct": round(soh_loss_fraction * 100.0, 4),
            "cyclic_damage": round(cyclic_damage, 6),
            "calendar_damage": round(calendar_damage, 6),
            "total_damage": round(total_damage, 6),
            "cycle_count_half": half_cycles,
            "cycle_count_full": full_cycles,
            "equivalent_full_cycles": round(efc, 2),
            "economic_degradation_cost": round(economic_cost, 4),
            "projected_rul_years": round(rul_years, 1),
            "dod_histogram": {k: round(v, 1) for k, v in dod_bins.items()},
            "mean_soc_pct": round(mean_soc * 100.0, 1),
            "duration_hours": duration_hours,
        }
