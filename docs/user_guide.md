# User & Presentation Guide

## 1. Quickstart Guide

### 1.1 Prerequisites
- Python 3.12+ (tested with Python 3.13)
- Pip package manager

### 1.2 Installation
```bash
git clone <repository_url>
cd smart_grid_ems
pip install -r requirements.txt
```

### 1.3 Running the FastAPI REST Backend
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Navigate to `http://localhost:8000/docs` to test endpoints interactively.

### 1.4 Running the Streamlit Dashboard
```bash
streamlit run dashboard/app.py
```
Open `http://localhost:8501` in your browser.

### 1.5 Executing Automated Pytest Suite
```bash
python -m pytest -v --tb=short
```

---

## 2. Demonstration & Viva Walkthrough Steps

### Step 1: System Overview & Architecture
1. Launch the Streamlit dashboard (`http://localhost:8501`).
2. Show the **Overview Page** (`1_Overview.py`):
   - Highlight the end-to-end architecture diagram.
   - Explain the 10 kWh battery hardware limits and TOU pricing structure.

### Step 2: Solar & Load ML Forecasting
1. Open `2_Solar_Forecast.py` and `3_Load_Forecast.py`:
   - Switch between **Persistence Baseline**, **Ridge Regression**, **Random Forest**, and **XGBoost**.
   - Show the holdout benchmark table demonstrating how XGBoost achieves superior accuracy (\(R^2 > 0.88\), \(MAE < 0.27\text{ kW}\)).
   - Point out zero night-time solar forcing.

### Step 3: Battery Hardware Dynamics
1. Open `4_Battery_Status.py`:
   - Inspect the real-time SOC gauge.
   - Show the 7-day SOC trajectory curve bounded strictly between 15% and 95%.

### Step 4: Power Flow & Sankey Diagram
1. Open `5_Energy_Flow.py`:
   - Show the **Stacked Area Chart** demonstrating load satisfaction.
   - Show the **Sankey Flow Diagram** displaying total period energy distribution.
   - Use the **Interactive Single-Step Dispatch Simulator** to test surplus and deficit conditions.

### Step 5: MILP Optimization & TOU Arbitrage
1. Open `6_Optimization_EMS.py`:
   - Explain how the MILP optimizer charges during off-peak hours (\$0.10/kWh) and discharges during expensive peak hours (\$0.35/kWh) to minimize operating cost.

### Step 6: Benchmark Comparison & Financial Savings
1. Open `7_Analytics_and_Comparison.py`:
   - Present the comparative performance table:
     - Unmanaged Base System (No Battery)
     - Rule-Based EMS (Baseline)
     - Optimization EMS (Proposed System)
   - Show financial cost savings ($ and %) and peak shaving reductions.
   - Download the generated CSV report for the project submission.
