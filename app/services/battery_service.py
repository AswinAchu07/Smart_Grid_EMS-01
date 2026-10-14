"""Service managing battery hardware configurations and operational state.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models import BatteryConfig, User
from app.schemas.battery import (
    BatteryConfigCreate,
    BatteryConfigUpdate,
    BatteryConfigResponse,
    BatteryStatusResponse,
)
from app.battery.model import Battery

# Default in-memory active battery instance
_active_battery = Battery()


class BatteryService:
    """Manages CRUD operations for battery profiles and live physical battery simulation."""

    @staticmethod
    def get_live_battery() -> Battery:
        """Get current live in-memory Battery instance."""
        global _active_battery
        return _active_battery

    @staticmethod
    def set_live_battery(battery: Battery) -> None:
        """Set current live in-memory Battery instance."""
        global _active_battery
        _active_battery = battery

    @classmethod
    def get_status(cls) -> BatteryStatusResponse:
        """Return current status of active battery instance."""
        bat = cls.get_live_battery()
        status = bat.get_status()
        return BatteryStatusResponse(**status)

    @classmethod
    def create_config(cls, db: Session, config_in: BatteryConfigCreate, user: Optional[User] = None) -> BatteryConfig:
        """Create and persist a new battery hardware profile in DB."""
        db_config = BatteryConfig(
            user_id=user.id if user else None,
            name=config_in.name,
            capacity_kwh=config_in.capacity_kwh,
            initial_soc=config_in.initial_soc,
            min_soc=config_in.min_soc,
            max_soc=config_in.max_soc,
            max_charge_power_kw=config_in.max_charge_power_kw,
            max_discharge_power_kw=config_in.max_discharge_power_kw,
            charge_efficiency=config_in.charge_efficiency,
            discharge_efficiency=config_in.discharge_efficiency,
        )
        db.add(db_config)
        db.commit()
        db.refresh(db_config)

        # Update active in-memory instance
        new_bat = Battery(
            capacity_kwh=db_config.capacity_kwh,
            initial_soc=db_config.initial_soc,
            min_soc=db_config.min_soc,
            max_soc=db_config.max_soc,
            max_charge_power_kw=db_config.max_charge_power_kw,
            max_discharge_power_kw=db_config.max_discharge_power_kw,
            charge_efficiency=db_config.charge_efficiency,
            discharge_efficiency=db_config.discharge_efficiency,
        )
        cls.set_live_battery(new_bat)
        return db_config

    @classmethod
    def get_configs(cls, db: Session, user: Optional[User] = None) -> List[BatteryConfig]:
        """Fetch all stored battery configurations."""
        query = db.query(BatteryConfig).filter(BatteryConfig.is_active == True)
        if user and user.role != "ADMIN":
            query = query.filter((BatteryConfig.user_id == user.id) | (BatteryConfig.user_id == None))
        return query.all()
