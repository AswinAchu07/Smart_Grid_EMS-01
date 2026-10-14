"""Mixed-Integer Linear Programming (MILP) Optimal Energy Dispatch Solver using PuLP.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np
import importlib
import pulp

from app.battery.model import Battery
from app.ems.rule_based import RuleBasedEMS, EMSDispatchDecision

# If the running process loaded an incompatible PuLP version before downgrade, dynamically reload 2.9.0
if not hasattr(pulp.LpVariable, "dicts") or getattr(pulp, "__version__", "").startswith("4."):
    try:
        pulp = importlib.reload(pulp)
    except Exception:
        pass


def _create_lp_dict(name: str, indices, lowBound=None, upBound=None, cat=None):
    """Safely create indexed LpVariable dictionary across any PuLP version."""
    if hasattr(pulp.LpVariable, "dicts"):
        kwargs = {}
        if lowBound is not None:
            kwargs["lowBound"] = lowBound
        if upBound is not None:
            kwargs["upBound"] = upBound
        if cat is not None:
            kwargs["cat"] = cat
        return pulp.LpVariable.dicts(name, indices, **kwargs)
    return {
        i: pulp.LpVariable(
            f"{name}_{i}",
            lowBound=lowBound,
            upBound=upBound,
            cat=cat or pulp.LpContinuous,
        )
        for i in indices
    }


@dataclass
class OptimizationResult:
    """Stores the complete optimization outcome across a multi-step horizon."""
    status: str
    is_feasible: bool
    total_cost: float
    decisions: List[EMSDispatchDecision]
    soc_trajectory: List[float]
    solver_message: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "is_feasible": self.is_feasible,
            "total_cost": round(self.total_cost, 4),
            "decisions": [d.to_dict() for d in self.decisions],
            "soc_trajectory": [round(s, 4) for s in self.soc_trajectory],
            "solver_message": self.solver_message,
        }


class OptimizationEMS:
    """Formulates and solves a horizon-based MILP cost-minimization problem.

    Minimizes total electricity import cost minus solar export revenue and battery degradation,
    while fulfilling 100% of load, obeying battery dynamics, and leveraging time-of-use tariffs.
    """

    @classmethod
    def optimize_horizon(
        cls,
        solar_forecast: List[float],
        load_forecast: List[float],
        battery_initial: Battery,
        import_prices: Optional[List[float]] = None,
        export_prices: Optional[List[float]] = None,
        degradation_cost: float = 0.005,
        dt_hours: float = 1.0,
    ) -> OptimizationResult:
        """Solve optimal dispatch over horizon T. Fallbacks gracefully to Rule-Based EMS if needed."""
        T = len(solar_forecast)
        if T == 0 or len(load_forecast) != T:
            raise ValueError(f"Solar and load forecasts must have equal non-zero length, got {T} and {len(load_forecast)}")

        # Default flat tariffs if not provided
        if import_prices is None or len(import_prices) != T:
            import_prices = [0.18] * T
        if export_prices is None or len(export_prices) != T:
            export_prices = [0.08] * T

        cap = battery_initial.capacity_kwh
        eta_ch = battery_initial.charge_efficiency
        eta_dis = battery_initial.discharge_efficiency
        soc_min = battery_initial.min_soc
        soc_max = battery_initial.max_soc
        p_ch_max = battery_initial.max_charge_power_kw
        p_dis_max = battery_initial.max_discharge_power_kw
        soc_0 = battery_initial.soc

        # 1. Initialize PuLP Model
        model = pulp.LpProblem("SmartGrid_EMS_Optimal_Dispatch", pulp.LpMinimize)

        # 2. Decision Variables
        p_s_load = _create_lp_dict("s_load", range(T), lowBound=0)
        p_s_bat = _create_lp_dict("s_bat", range(T), lowBound=0, upBound=p_ch_max)
        p_s_grid = _create_lp_dict("s_grid", range(T), lowBound=0)
        p_bat_load = _create_lp_dict("bat_load", range(T), lowBound=0, upBound=p_dis_max)
        p_grid_load = _create_lp_dict("grid_load", range(T), lowBound=0)
        u_ch = _create_lp_dict("u_ch", range(T), cat=pulp.LpBinary)
        u_dis = _create_lp_dict("u_dis", range(T), cat=pulp.LpBinary)
        soc = _create_lp_dict("soc", range(T), lowBound=soc_min, upBound=soc_max)

        # 3. Objective Function: Minimize Net Import Cost + Battery Cycling Cost
        cost_terms = []
        for t in range(T):
            grid_import_total = p_grid_load[t]
            grid_export_total = p_s_grid[t]
            cycling_penalty = degradation_cost * (p_s_bat[t] + p_bat_load[t])
            cost_terms.append(
                (import_prices[t] * grid_import_total - export_prices[t] * grid_export_total + cycling_penalty) * dt_hours
            )
        model += pulp.lpSum(cost_terms)

        # 4. Constraints
        for t in range(T):
            S_t = max(0.0, float(solar_forecast[t]))
            L_t = max(0.0, float(load_forecast[t]))

            # Load Fulfillment: Solar + Battery + Grid = Total Load
            model += (p_s_load[t] + p_bat_load[t] + p_grid_load[t] == L_t, f"LoadBalance_{t}")

            # Strict Solar Allocation: Solar to Load + Solar to Battery + Solar to Grid = S_t
            model += (p_s_load[t] + p_s_bat[t] + p_s_grid[t] == S_t, f"SolarSupply_{t}")

            # Power Ratings & Binary Mutual Exclusivity
            model += (p_s_bat[t] <= p_ch_max * u_ch[t], f"MaxChargePower_{t}")
            model += (p_bat_load[t] <= p_dis_max * u_dis[t], f"MaxDischargePower_{t}")
            model += (u_ch[t] + u_dis[t] <= 1, f"MutualExclusivity_{t}")

            # SOC Dynamic Continuity
            if t == 0:
                prev_soc = soc_0
            else:
                prev_soc = soc[t - 1]

            delta_soc = (p_s_bat[t] * eta_ch * dt_hours) / cap - (p_bat_load[t] * dt_hours) / (eta_dis * cap)
            model += (soc[t] == prev_soc + delta_soc, f"SOC_Dynamics_{t}")

        # 5. Solve MILP
        solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=15)
        model.solve(solver)
        status_str = pulp.LpStatus[model.status]

        # 6. Process Output / Fallback
        if status_str in ["Optimal", "Feasible"]:
            decisions = []
            soc_traj = []
            running_cost = 0.0

            for t in range(T):
                s_l = float(p_s_load[t].varValue or 0.0)
                s_b = float(p_s_bat[t].varValue or 0.0)
                s_g = float(p_s_grid[t].varValue or 0.0)
                b_l = float(p_bat_load[t].varValue or 0.0)
                g_l = float(p_grid_load[t].varValue or 0.0)
                s_soc = float(soc[t].varValue or 0.0)

                g_imp = g_l
                g_exp = s_g
                step_c = (g_imp * import_prices[t] - g_exp * export_prices[t]) * dt_hours
                running_cost += step_c

                sources = float(solar_forecast[t]) + b_l + g_imp
                sinks = float(load_forecast[t]) + s_b + g_exp
                bal_err = abs(sources - sinks)

                dec = EMSDispatchDecision(
                    solar_kw=float(solar_forecast[t]),
                    load_kw=float(load_forecast[t]),
                    solar_to_load_kw=s_l,
                    solar_to_battery_kw=s_b,
                    solar_to_grid_kw=s_g,
                    battery_to_load_kw=b_l,
                    grid_import_kw=g_imp,
                    grid_export_kw=g_exp,
                    resulting_soc=s_soc,
                    cost=step_c,
                    energy_balance_error=bal_err,
                )
                decisions.append(dec)
                soc_traj.append(s_soc)

            return OptimizationResult(
                status=status_str,
                is_feasible=True,
                total_cost=running_cost,
                decisions=decisions,
                soc_trajectory=soc_traj,
                solver_message=f"Optimal schedule determined successfully ({status_str}).",
            )
        else:
            # Fallback to Rule-Based EMS step-by-step
            sim_battery = Battery(
                capacity_kwh=cap,
                initial_soc=soc_0,
                min_soc=soc_min,
                max_soc=soc_max,
                max_charge_power_kw=p_ch_max,
                max_discharge_power_kw=p_dis_max,
                charge_efficiency=eta_ch,
                discharge_efficiency=eta_dis,
            )
            fallback_decisions = []
            fallback_soc = []
            total_fallback_cost = 0.0

            for t in range(T):
                dec = RuleBasedEMS.step(
                    solar_kw=float(solar_forecast[t]),
                    load_kw=float(load_forecast[t]),
                    battery=sim_battery,
                    import_price=import_prices[t],
                    export_price=export_prices[t],
                    dt_hours=dt_hours,
                )
                fallback_decisions.append(dec)
                fallback_soc.append(dec.resulting_soc)
                total_fallback_cost += dec.cost

            return OptimizationResult(
                status=f"Fallback ({status_str})",
                is_feasible=False,
                total_cost=total_fallback_cost,
                decisions=fallback_decisions,
                soc_trajectory=fallback_soc,
                solver_message=f"MILP solver status '{status_str}'; executed resilient Rule-Based EMS fallback.",
            )
