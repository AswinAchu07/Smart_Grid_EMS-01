# REST API Reference Documentation

Base URL: `http://localhost:8000/api/v1`  
Interactive OpenAPI UI: `http://localhost:8000/docs`  
ReDoc UI: `http://localhost:8000/redoc`

---

## 1. Authentication Endpoints

### `POST /auth/register`
Register a new user account.
- **Request Body**: `UserCreate` (`email`, `password`, `role`)
- **Response**: `201 Created` with `UserResponse`

### `POST /auth/login` & `POST /auth/login/json`
Authenticate and obtain a signed JWT Bearer Token.
- **Request Body**: `UserLogin` (`email`, `password`)
- **Response**: `200 OK` with `Token` (`access_token`, `token_type`, `expires_in_minutes`, `role`)

### `GET /users/me`
Retrieve currently authenticated user profile.
- **Headers**: `Authorization: Bearer <token>`
- **Response**: `200 OK` with `UserResponse`

---

## 2. Forecasting Endpoints

### `POST /forecasts/solar`
Generate solar PV generation forecast.
- **Query Params**:
  - `model_type`: `XGBOOST` | `RANDOM_FOREST` | `LINEAR_RIDGE` | `PERSISTENCE`
  - `horizon_hours`: `1` to `168` (default: 24)
- **Response**: `200 OK` with `ForecastResponse` (`target_type`, `model_name`, `data_points`, `metrics`)

### `POST /forecasts/load`
Generate electricity demand forecast.
- **Query Params**: `model_type`, `horizon_hours`
- **Response**: `200 OK` with `ForecastResponse`

### `GET /forecasts/solar/models` & `GET /forecasts/load/models`
Retrieve holdout test benchmarks across all 4 candidate models.
- **Response**: `200 OK` with `ModelMetricsResponse` (`mae`, `rmse`, `mape`, `smape`, `r2`)

---

## 3. Battery Storage Endpoints

### `GET /battery/status`
Retrieve live operational telemetry of active battery storage system.
- **Response**: `200 OK` with `BatteryStatusResponse` (`soc`, `capacity_kwh`, `stored_energy_kwh`, `max_charge_power_kw`, `equivalent_cycles`)

### `POST /battery/configure`
Create or update active battery hardware parameters.
- **Request Body**: `BatteryConfigCreate`
- **Response**: `201 Created` with `BatteryConfigResponse`

---

## 4. Energy Management & Optimization Endpoints

### `POST /ems/decision`
Execute instantaneous single-timestep Rule-Based EMS dispatch.
- **Request Body**: `EMSStepRequest` (`solar_kw`, `load_kw`, `current_soc`, `import_price`, `export_price`)
- **Response**: `200 OK` with `EMSStepResponse` (`solar_to_load_kw`, `solar_to_battery_kw`, `grid_import_kw`, `grid_export_kw`, `resulting_soc`, `cost`)

### `POST /optimization/run`
Execute multi-period MILP cost-optimal dispatch solver (PuLP).
- **Request Body**: `OptimizationRequest` (`solar_forecast`, `load_forecast`, `initial_soc`, `import_prices`)
- **Response**: `200 OK` with `OptimizationResponse` (`status`, `is_feasible`, `total_cost`, `decisions`, `soc_trajectory`)

---

## 5. Simulation & Analytics Endpoints

### `POST /simulation/run`
Execute multi-day microgrid time-series simulation.
- **Request Body**: `SimulationRequest` (`strategy`, `duration_hours`, `initial_soc`, `save_to_db`)
- **Response**: `200 OK` with `SimulationResponse`

### `GET /analytics/comparison`
Compute comparative financial savings and technical benchmarks between Unmanaged, Rule-Based, and Optimization strategies.
- **Query Params**: `duration_hours` (default: 168)
- **Response**: `200 OK` with `StrategyComparisonResponse`
