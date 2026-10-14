"""[INTEGRATION TEST] Multi-day simulation engine execution and strategy comparisons.
"""

import pytest
import pandas as pd
from app.data.synthetic_generator import generate_synthetic_dataset
from app.simulation.engine import SimulationEngine
from app.simulation.evaluator import PerformanceEvaluator
from app.battery.model import Battery
from app.core.constants import EMSStrategy


def test_multi_day_simulation_runs():
    """Verify 7-day (168 hours) simulation across Unmanaged, Rule-Based, and Optimization strategies."""
    df = generate_synthetic_dataset(periods=168, seed=42)

    # 1. Unmanaged
    eng_unm = SimulationEngine(battery=Battery())
    sum_unm = eng_unm.run_unmanaged(df)
    assert sum_unm.total_steps == 168
    assert sum_unm.strategy == EMSStrategy.UNMANAGED.value

    # 2. Rule-Based
    eng_rb = SimulationEngine(battery=Battery())
    sum_rb = eng_rb.run_rule_based(df)
    assert sum_rb.total_steps == 168
    assert sum_rb.strategy == EMSStrategy.RULE_BASED.value

    # 3. Optimization
    eng_opt = SimulationEngine(battery=Battery())
    sum_opt = eng_opt.run_optimization(df)
    assert sum_opt.total_steps == 168
    assert sum_opt.strategy == EMSStrategy.OPTIMIZATION.value

    # Optimization should achieve lower cost than unmanaged baseline
    assert sum_opt.total_cost < sum_unm.total_cost

    # Comparative evaluation
    comparison = PerformanceEvaluator.compare_strategies(sum_unm, sum_rb, sum_opt)
    assert comparison["savings_vs_unmanaged_usd"] > 0
    assert comparison["savings_vs_unmanaged_pct"] > 0
    assert len(comparison["comparison_table"]) == 3
