"""Service delivering high-level analytics, benchmark comparisons, and system KPIs.
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.battery.model import Battery
from app.data.pipeline import SmartGridDataPipeline
from app.simulation.engine import SimulationEngine
from app.simulation.evaluator import PerformanceEvaluator
from app.schemas.analytics import (
    AnalyticsSummaryResponse,
    StrategyComparisonResponse,
)
from app.db.models import SimulationRun, ForecastRun, BatteryConfig


class AnalyticsService:
    """Delivers end-to-end benchmark comparison and system-wide statistics."""

    def __init__(self, data_path: str = "data/sample/smart_grid_data.csv"):
        self.data_path = data_path
        self.pipeline = SmartGridDataPipeline(data_path=data_path)

    def get_benchmark_comparison(self, duration_hours: int = 168) -> StrategyComparisonResponse:
        """Run all 3 strategies on the same test slice and compute comparative metrics."""
        raw_df = self.pipeline.get_or_create_raw_data()
        df_clean = self.pipeline.preprocessor.clean_and_normalize(raw_df)
        train_df, val_df, test_df = self.pipeline.preprocessor.chronological_split(df_clean)

        sim_df = test_df.iloc[:duration_hours].reset_index(drop=True)

        # 1. Unmanaged
        eng_unm = SimulationEngine(battery=Battery())
        sum_unm = eng_unm.run_unmanaged(sim_df)

        # 2. Rule-Based
        eng_rb = SimulationEngine(battery=Battery())
        sum_rb = eng_rb.run_rule_based(sim_df)

        # 3. Optimization
        eng_opt = SimulationEngine(battery=Battery())
        sum_opt = eng_opt.run_optimization(sim_df)

        comp_dict = PerformanceEvaluator.compare_strategies(
            unmanaged=sum_unm,
            rule_based=sum_rb,
            optimized=sum_opt,
        )

        return StrategyComparisonResponse(**comp_dict)

    def get_system_summary(self, db: Optional[Session] = None) -> AnalyticsSummaryResponse:
        """Return global platform metrics and latest strategy comparison."""
        total_sims = 0
        total_forecasts = 0
        total_batteries = 1

        if db:
            total_sims = db.query(SimulationRun).count()
            total_forecasts = db.query(ForecastRun).count()
            total_batteries = max(1, db.query(BatteryConfig).count())

        comp = self.get_benchmark_comparison(duration_hours=168)

        return AnalyticsSummaryResponse(
            total_simulations_run=total_sims,
            total_forecasts_generated=total_forecasts,
            configured_batteries=total_batteries,
            latest_strategy_comparison=comp,
        )
