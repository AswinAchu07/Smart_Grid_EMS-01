"""FastAPI Application Entry Point for Smart Grid Solar PV and Battery EMS.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.core.security import get_password_hash
from app.core.constants import UserRole
from app.db.session import engine, SessionLocal
from app.db.base import Base
from app.db.models import User, BatteryConfig

# Import API Routers
from app.api.v1.auth import router as auth_router
from app.api.v1.forecasts import router as forecasts_router
from app.api.v1.battery import router as battery_router
from app.api.v1.ems import router as ems_router
from app.api.v1.optimization import router as optimization_router
from app.api.v1.simulation import router as simulation_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.health import router as health_router
from app.api.v1.weather import router as weather_router



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events: create tables and seed default users."""
    # 1. Create DB tables
    Base.metadata.create_all(bind=engine)

    # 2. Seed default admin and researcher users if not present
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.email == settings.DEFAULT_ADMIN_EMAIL).first()
        if not admin_user:
            admin = User(
                email=settings.DEFAULT_ADMIN_EMAIL,
                hashed_password=get_password_hash(settings.DEFAULT_ADMIN_PASSWORD),
                role=UserRole.ADMIN.value,
                is_active=True,
            )
            db.add(admin)

        # Seed researcher user
        researcher_email = "researcher@smartgrid.com"
        res_user = db.query(User).filter(User.email == researcher_email).first()
        if not res_user:
            researcher = User(
                email=researcher_email,
                hashed_password=get_password_hash("ResearcherSecure123!"),
                role=UserRole.RESEARCHER.value,
                is_active=True,
            )
            db.add(researcher)

        # Seed default battery profile
        default_bat = db.query(BatteryConfig).filter(BatteryConfig.name == "Default 10kWh Li-ion").first()
        if not default_bat:
            bat = BatteryConfig(
                name="Default 10kWh Li-ion",
                capacity_kwh=settings.DEFAULT_BATTERY_CAPACITY_KWH,
                initial_soc=0.50,
                min_soc=settings.DEFAULT_BATTERY_MIN_SOC,
                max_soc=settings.DEFAULT_BATTERY_MAX_SOC,
                max_charge_power_kw=settings.DEFAULT_BATTERY_MAX_CHARGE_KW,
                max_discharge_power_kw=settings.DEFAULT_BATTERY_MAX_DISCHARGE_KW,
                charge_efficiency=settings.DEFAULT_BATTERY_CHARGE_EFF,
                discharge_efficiency=settings.DEFAULT_BATTERY_DISCHARGE_EFF,
                is_active=True,
            )
            db.add(bat)

        db.commit()
    finally:
        db.close()

    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Production-grade ML-Based Solar PV & Battery Energy Management System (EMS) REST API. "
        "Provides Solar & Load forecasting, physical battery state dynamics, rule-based & MILP optimization dispatch."
    ),
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Sub-Routers
app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(forecasts_router, prefix=settings.API_V1_STR)
app.include_router(battery_router, prefix=settings.API_V1_STR)
app.include_router(ems_router, prefix=settings.API_V1_STR)
app.include_router(optimization_router, prefix=settings.API_V1_STR)
app.include_router(simulation_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)
app.include_router(weather_router, prefix=settings.API_V1_STR)



@app.get("/", include_in_schema=False)
def root_redirect():
    """Redirect root to OpenAPI interactive documentation."""
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
