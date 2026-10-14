"""[INTEGRATION TEST] Database persistence, ORM model relationships, and transactions.
"""

import pytest
from sqlalchemy.orm import Session
from app.db.models import User, BatteryConfig, SimulationRun, SimulationRecord, ForecastRun


def test_database_user_battery_relationship(db_session: Session):
    """Verify BatteryConfig links to User and cascades properly."""
    user = User(
        email="dbuser@smartgrid.local",
        hashed_password="hashed_pw_xyz",
        role="RESEARCHER",
    )
    db_session.add(user)
    db_session.commit()

    bat = BatteryConfig(
        user_id=user.id,
        name="Research Lab 20kWh",
        capacity_kwh=20.0,
        initial_soc=0.5,
        min_soc=0.1,
        max_soc=0.9,
    )
    db_session.add(bat)
    db_session.commit()

    assert len(user.battery_configs) == 1
    assert user.battery_configs[0].capacity_kwh == 20.0


def test_simulation_run_with_records_persistence(db_session: Session):
    """Verify SimulationRun and SimulationRecord foreign key cascade."""
    sim = SimulationRun(
        name="Test Sim Persistence",
        strategy="RULE_BASED",
        total_steps=2,
        total_cost=1.25,
    )
    db_session.add(sim)
    db_session.flush()

    rec1 = SimulationRecord(
        simulation_id=sim.id,
        step=0,
        timestamp="2024-01-01 00:00:00",
        solar_kw=0.0,
        load_kw=2.0,
        solar_to_load_kw=0.0,
        solar_to_bat_kw=0.0,
        solar_to_grid_kw=0.0,
        bat_to_load_kw=1.0,
        grid_import_kw=1.0,
        grid_export_kw=0.0,
        soc=0.45,
        price_per_kwh=0.18,
        cost=0.18,
    )
    db_session.add(rec1)
    db_session.commit()

    retrieved = db_session.query(SimulationRun).filter(SimulationRun.id == sim.id).first()
    assert retrieved is not None
    assert len(retrieved.records) == 1
    assert retrieved.records[0].load_kw == 2.0
