# ML-Based Solar PV and Battery Energy Management System for Smart Grid

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-FF4B4B.svg?logo=streamlit)](https://streamlit.io/)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.0%2B-EB5424.svg)](https://xgboost.readthedocs.io/)
[![Tests](https://img.shields.io/badge/Tests-38%20Passed-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python-first **B.Tech Final-Year Capstone Project** in Smart Grid, Solar PV Generation, Battery Energy Storage Systems (BESS), Machine Learning Forecasting, and Mixed-Integer Linear Programming (MILP) Optimal Energy Dispatch.

---

## 🏛️ System Architecture

```mermaid
graph TD
    subgraph Data Layer
        DS[Synthetic Generator / Historical CSV] --> DI[Data Ingestion & Cleaning]
        DI --> FE[Feature Engineering: Cyclic Sin/Cos, Lags, Rolling Stats]
    end

    subgraph Machine Learning Layer
        FE --> SF[Solar Forecaster<br/>Baseline | Ridge | RF | XGBoost]
        FE --> LF[Load Forecaster<br/>Baseline | Ridge | RF | XGBoost]
    end

    subgraph Physical Systems & Constraints
        SF & LF --> EMS_CTRL[EMS Controller]
        BAT[10 kWh Li-ion Battery Model<br/>SOC: 15% - 95%, Eff: 95%] <--> EMS_CTRL
        
        EMS_CTRL --> RB_EMS[Rule-Based Heuristic EMS]
        EMS_CTRL --> OPT_EMS[MILP Optimization EMS<br/>PuLP Cost Minimizer]
    end

    subgraph Simulation & Evaluation
        RB_EMS & OPT_EMS --> SIM[Simulation Engine]
        SIM --> EVAL[Evaluator: Savings, Self-Consumption, Peak Shaving]
    end

    subgraph Presentation & API Layer
        DB[(PostgreSQL / SQLite Database)] <--> API[FastAPI Backend + JWT RBAC]
        SIM --> API
        EVAL --> API
        API <--> DASH[Streamlit + Plotly Interactive UI]
    end
```

---

## ✨ Key Features

1. **High-Fidelity Synthetic Dataset Generator**:
   - Generates 8,760 hours (1 full year) of realistic hourly smart grid telemetry.
   - Clear-sky solar irradiance model with beta-distributed cloud attenuation.
   - Diurnal and seasonal load profiles with occupancy shifts and HVAC temperature sensitivity.
   - Multi-tier Time-of-Use (TOU) electricity pricing.

2. **Machine Learning Forecasting Pipeline**:
   - 4 Candidate Architectures: **Persistence Baseline**, **Ridge Linear Regression**, **Random Forest**, and **XGBoost Regressor**.
   - Feature Engineering: Cyclic \(\sin/\cos\) hour/day encodings, autoregressive lag features (\(t-1, t-2, t-24, t-48, t-168\)), rolling mean and standard deviation.
   - Strict chronological train/validation/test splits preventing future data leakage.
   - Evaluation metrics: MAE, RMSE, MAPE (with \(\epsilon = 0.05\text{ kW}\) handling), sMAPE, and \(R^2\).

3. **Physics-Based Battery Storage Model**:
   - Dynamic State of Charge (SOC) tracking strictly bounded within safe hardware limits (\(15\% \le SOC \le 95\%\)).
   - Sub-efficiency losses: \(95\%\) charge efficiency and \(95\%\) discharge efficiency (\(\approx 90.25\%\) roundtrip).
   - Enforces physical power ratings (\(5.0\text{ kW}\) max charge/discharge) and forbids simultaneous charging and discharging.

4. **Energy Management Systems (EMS)**:
   - **Rule-Based Heuristic EMS (Baseline)**: Prioritizes direct solar self-consumption, surplus battery charging, and grid backup.
   - **Optimization EMS (Proposed MILP System)**: Mixed-Integer Linear Programming formulation via PuLP minimizing electricity import cost and battery degradation under TOU tariffs.
   - **Strict Physical Power Conservation**: Verifies \(\text{Sources} = \text{Sinks}\) with error \(< 10^{-5}\text{ kW}\) at every single timestep.

5. **FastAPI RESTful Backend**:
   - Production-grade async API with OpenAPI 3.0 interactive documentation (`/docs`, `/redoc`).
   - JWT token authentication with Role-Based Access Control (`ADMIN`, `RESEARCHER`, `VIEWER`).
   - Dual-mode database layer: Zero-setup SQLite locally with automatic fallback or PostgreSQL in production.

6. **Interactive Streamlit Analytical Dashboard**:
   - **Page 1: Overview**: System architecture, key specifications, and summary KPIs.
   - **Page 2: Solar Forecast**: Model comparison, horizon slider, and error metrics.
   - **Page 3: Load Forecast**: Diurnal demand curves, actuals vs predictions.
   - **Page 4: Battery Status**: Real-time SOC gauge, usable energy, and cycle count.
   - **Page 5: Energy Flow**: Stacked area balance chart, Sankey flow diagram, and interactive dispatch calculator.
   - **Page 6: Optimization EMS**: 24-hour day-ahead TOU tariff arbitrage schedule.
   - **Page 7: Benchmark Analytics**: Multi-strategy comparison table, financial savings, peak shaving, and CSV report export.

---

## 🚀 Quickstart Guide

### 1. Installation
```bash
# Clone the repository
git clone <repository_url>
cd smart_grid_ems

# Install dependencies
pip install -r requirements.txt
```

### 2. Train ML Models
```bash
python -m app.ml.solar.train
python -m app.ml.load.train
```

### 3. Run FastAPI Backend
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Open [http://localhost:8000/docs](http://localhost:8000/docs) to view the interactive API Swagger UI.

### 4. Run Streamlit Dashboard
```bash
streamlit run dashboard/app.py
```
Open [http://localhost:8501](http://localhost:8501) in your web browser.

### 5. Run Test Suite
```bash
python -m pytest -v --tb=short
```

---

## 📊 Experimental Results Summary

Holdout Test Benchmark Results (\(1,314\) unseen test hours):

### Solar PV Forecasting Accuracy:
| Model | MAE (kW) | RMSE (kW) | MAPE (%) | \(R^2\) Score |
| :--- | :--- | :--- | :--- | :--- |
| **XGBoost (Proposed)** | **0.0055** | **0.0109** | **0.67%** | **0.9999** |
| Random Forest | 0.0059 | 0.0131 | 0.73% | 0.9999 |
| Ridge Regression | 0.0146 | 0.0265 | 1.63% | 0.9995 |
| Persistence Baseline | 0.0444 | 0.0999 | 5.65% | 0.9926 |

### Electricity Load Forecasting Accuracy:
| Model | MAE (kW) | RMSE (kW) | MAPE (%) | \(R^2\) Score |
| :--- | :--- | :--- | :--- | :--- |
| **XGBoost (Proposed)** | **0.2686** | **0.3443** | **9.06%** | **0.8815** |
| Random Forest | 0.2909 | 0.3728 | 9.65% | 0.8611 |
| Ridge Regression | 0.3408 | 0.4291 | 11.90% | 0.8160 |
| Persistence Baseline | 0.4616 | 0.6137 | 16.00% | 0.6236 |

### Microgrid 7-Day Strategy Comparison:
| Strategy | Total Cost ($) | Grid Import (kWh) | Grid Export (kWh) | Peak Demand (kW) | Self-Consumption (%) | Savings vs Baseline |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Unmanaged (No Battery)** | \$86.42 | 480.1 | 240.5 | 6.85 kW | 41.2% | Baseline |
| **Rule-Based EMS** | \$58.15 | 322.8 | 83.2 | 4.20 kW | 79.6% | **32.7%** |
| **Optimization EMS (MILP)** | **\$49.30** | **274.0** | **34.4** | **3.80 kW** | **91.6%** | **42.9%** |

---

## 📂 Project Structure

```
smart_grid_ems/
├── app/
│   ├── api/
│   │   ├── deps.py               # Authentication & RBAC dependencies
│   │   └── v1/                   # REST API V1 endpoints
│   ├── battery/
│   │   ├── model.py              # Battery electrochemical model
│   │   └── constraints.py        # Physical constraints & bounds
│   ├── core/
│   │   ├── config.py             # Pydantic Settings
│   │   ├── constants.py          # Enums & constants
│   │   └── security.py           # Bcrypt & JWT token utilities
│   ├── data/
│   │   ├── synthetic_generator.py# Realistic smart grid data generator
│   │   ├── preprocessor.py       # Cleaning & chronological splitting
│   │   ├── features.py           # Trigonometric & lag feature engineering
│   │   └── pipeline.py           # Data pipeline orchestrator
│   ├── db/
│   │   ├── base.py               # SQLAlchemy DeclarativeBase
│   │   ├── session.py            # Database session generator
│   │   └── models.py             # ORM models (User, Battery, Simulation, etc.)
│   ├── ems/
│   │   └── rule_based.py         # Rule-Based heuristic EMS
│   ├── ml/
│   │   ├── base.py               # BaseForecaster abstract class
│   │   ├── metrics.py            # MAE, RMSE, MAPE, sMAPE, R2 evaluator
│   │   ├── solar/                # Solar training, models & inference
│   │   └── load/                 # Load training, models & inference
│   ├── optimization/
│   │   └── lp_solver.py          # PuLP MILP Cost Minimization Solver
│   ├── schemas/                  # Pydantic request & response schemas
│   ├── services/                 # Business logic service layer
│   ├── simulation/
│   │   ├── engine.py             # Multi-period simulation runner
│   │   └── evaluator.py          # Financial & technical KPI evaluator
│   └── main.py                   # FastAPI Application Entry Point
├── dashboard/
│   ├── app.py                    # Streamlit Dashboard main app
│   ├── components/               # Reusable Plotly charts & KPI cards
│   └── pages/                    # 7 Analytical Dashboard Pages
├── data/sample/                  # Sample CSV smart grid datasets
├── docs/                         # In-depth architectural & mathematical docs
├── models/saved/                 # Pre-trained ML model joblib artifacts
├── notebooks/                    # 4 Jupyter Demonstration Notebooks
├── tests/
│   ├── unit/                     # Battery, Energy Balance, ML, EMS tests
│   ├── integration/              # Simulation, DB, API, Auth RBAC tests
│   └── e2e/                      # Full pipeline End-to-End integration test
├── Dockerfile                    # Containerization specification
├── docker-compose.yml            # Multi-container orchestration
├── requirements.txt              # Core project dependencies
└── README.md                     # Project documentation
```

---

## 📜 License
This project is licensed under the MIT License - see the LICENSE file for details.
