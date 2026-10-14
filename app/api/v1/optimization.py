"""MILP Optimization dispatch endpoints.
"""

from fastapi import APIRouter
from app.schemas.ems import OptimizationRequest, OptimizationResponse
from app.services.ems_service import EMSService

router = APIRouter(prefix="/optimization", tags=["Optimization EMS"])


@router.post("/run", response_model=OptimizationResponse)
def run_optimization(request_data: OptimizationRequest):
    """Execute PuLP MILP solver to find cost-optimal multi-period energy schedule."""
    return EMSService.run_optimization(request_data)
