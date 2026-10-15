"""Battery storage status and hardware configuration endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User
from app.api.deps import get_current_user_optional, require_role
from app.core.constants import UserRole
from app.schemas.battery import (
    BatteryConfigCreate,
    BatteryConfigResponse,
    BatteryStatusResponse,
    BatteryDegradationRequest,
    BatteryDegradationResponse,
)
from app.services.battery_service import BatteryService

router = APIRouter(prefix="/battery", tags=["Battery Storage"])


@router.get("/status", response_model=BatteryStatusResponse)
def get_battery_status():
    """Retrieve real-time operational status, SOC fraction, stored energy, and cycle count."""
    return BatteryService.get_status()


@router.post("/configure", response_model=BatteryConfigResponse, status_code=status.HTTP_201_CREATED)
def configure_battery(
    config_in: BatteryConfigCreate,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    """Create and set active battery hardware parameters (capacity, SOC bounds, efficiencies)."""
    return BatteryService.create_config(db=db, config_in=config_in, user=user)


@router.get("/list", response_model=List[BatteryConfigResponse])
def list_battery_configurations(
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    """List all available battery hardware profiles."""
    return BatteryService.get_configs(db=db, user=user)


@router.post("/degradation", response_model=BatteryDegradationResponse)
def evaluate_battery_degradation(payload: BatteryDegradationRequest):
    """Run ASTM E1049-85 Rainflow cycle counting, SOH fade, and remaining useful life assessment."""
    result = BatteryService.evaluate_degradation(
        soc_trajectory=payload.soc_trajectory,
        capacity_kwh=payload.capacity_kwh,
        initial_soh=payload.initial_soh,
        dt_hours=payload.dt_hours,
        temp_celsius=payload.temp_celsius,
    )
    return BatteryDegradationResponse(**result)

