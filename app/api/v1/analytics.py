"""System analytics and strategy comparison endpoints.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analytics import (
    AnalyticsSummaryResponse,
    StrategyComparisonResponse,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])
analytics_service = AnalyticsService()


@router.get("/summary", response_model=AnalyticsSummaryResponse)
def get_analytics_summary(db: Session = Depends(get_db)):
    """Retrieve aggregate system metrics and benchmark performance results."""
    return analytics_service.get_system_summary(db=db)


@router.get("/comparison", response_model=StrategyComparisonResponse)
def get_strategy_comparison(duration_hours: int = Query(default=168, ge=24, le=720)):
    """Compute detailed financial savings and technical comparison between EMS strategies."""
    return analytics_service.get_benchmark_comparison(duration_hours=duration_hours)
