"""Pytest fixtures for unit, integration, and e2e test suites.
"""

import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.battery.model import Battery
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.db.models import User, BatteryConfig
from app.core.constants import UserRole

# In-memory SQLite with StaticPool for test isolation
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_data_and_models():
    """Ensure data directory and sample dataset exist before tests."""
    os.makedirs("data/sample", exist_ok=True)
    os.makedirs("models/saved/solar", exist_ok=True)
    os.makedirs("models/saved/load", exist_ok=True)


@pytest.fixture(scope="function")
def db_session():
    """Create fresh database tables for each test function and teardown afterwards."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        # Seed test admin & viewer with genuine bcrypt hashes
        admin = User(
            email="testadmin@smartgrid.com",
            hashed_password=get_password_hash("AdminSecurePassword123!"),
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        viewer = User(
            email="testviewer@smartgrid.com",
            hashed_password=get_password_hash("ViewerSecurePassword123!"),
            role=UserRole.VIEWER.value,
            is_active=True,
        )
        session.add(admin)
        session.add(viewer)
        session.commit()
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, base_url="http://test") as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_auth_headers():
    """Bearer token headers for ADMIN role."""
    token = create_access_token(subject="testadmin@smartgrid.com", role=UserRole.ADMIN.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def viewer_auth_headers():
    """Bearer token headers for VIEWER role."""
    token = create_access_token(subject="testviewer@smartgrid.com", role=UserRole.VIEWER.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def standard_battery():
    """Standard 10kWh test battery."""
    return Battery(
        capacity_kwh=10.0,
        initial_soc=0.50,
        min_soc=0.15,
        max_soc=0.95,
        max_charge_power_kw=5.0,
        max_discharge_power_kw=5.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
    )
