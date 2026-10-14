"""Energy Management System single-step dispatch decision endpoints.
"""

from fastapi import APIRouter
from app.schemas.ems import EMSStepRequest, EMSStepResponse
from app.services.ems_service import EMSService

router = APIRouter(prefix="/ems", tags=["Energy Management System"])


@router.post("/decision", response_model=EMSStepResponse)
def get_ems_decision(request_data: EMSStepRequest):
    """Compute instantaneous power dispatch flows (solar-to-load, solar-to-battery, battery-to-load, grid import/export)."""
    return EMSService.get_single_step_decision(request_data)
