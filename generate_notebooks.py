"""Generator for standard Jupyter Notebooks (.ipynb JSON format).
"""

import json
import os

def make_cell(cell_type: str, source: str):
    return {
        "cell_type": cell_type,
        "metadata": {},
        "source": [line + "\n" for line in source.split("\n")[:-1]] + [source.split("\n")[-1]] if source else [],
        **({"execution_count": None, "outputs": []} if cell_type == "code" else {})
    }

def make_notebook(cells):
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.12.0"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }

os.makedirs("notebooks", exist_ok=True)

# 1. EDA Notebook
nb1_cells = [
    make_cell("markdown", "# 01 - Exploratory Data Analysis (EDA) for Smart Grid Microgrid\n\nThis notebook analyzes the physical correlations, diurnal cycles, seasonal patterns, and distributions of:\n1. Solar Irradiance (GHI) and Solar PV Generation\n2. Electricity Load Demand Profiles\n3. Ambient Temperature, Cloud Cover, and Humidity\n4. Time-of-Use (TOU) Pricing Structures"),
    make_cell("code", "import sys\nsys.path.append('..')\nimport pandas as pd\nimport numpy as np\nimport matplotlib.pyplot as plt\n\nfrom app.data.synthetic_generator import generate_synthetic_dataset\nfrom app.data.preprocessor import DataPreprocessor\n\ndf = generate_synthetic_dataset(periods=8760)\nprint('Dataset shape:', df.shape)\ndf.head()"),
    make_cell("code", "# Summary Statistics\ndf.describe()"),
    make_cell("code", "# 24-Hour Diurnal Profile Analysis\ndf['hour'] = pd.to_datetime(df['timestamp']).dt.hour\nhourly_avg = df.groupby('hour')[['solar_power_kw', 'load_power_kw', 'temperature_c', 'irradiance_ghi_wm2']].mean()\nhourly_avg.plot(figsize=(12, 6), grid=True, title='Average Diurnal Profiles')\nplt.xlabel('Hour of Day')\nplt.ylabel('Magnitude')\nplt.show()")
]
with open("notebooks/01_exploratory_data_analysis.ipynb", "w") as f:
    json.dump(make_notebook(nb1_cells), f, indent=2)

# 2. Solar Training Notebook
nb2_cells = [
    make_cell("markdown", "# 02 - Solar PV Generation Forecasting Model Training & Evaluation\n\nTrains and evaluates 4 forecasting models:\n- **Persistence (Baseline)**\n- **Ridge Linear Regression**\n- **Random Forest Regressor**\n- **XGBoost Regressor**\n\nStrict chronological train/test split is enforced to avoid data leakage."),
    make_cell("code", "import sys\nsys.path.append('..')\nimport pandas as pd\nfrom app.ml.solar.train import train_solar_models\n\nresults = train_solar_models(data_path='../data/sample/smart_grid_data.csv', save_dir='../models/saved/solar')\nfor m_name, res in results.items():\n    print(f'Model: {m_name}')\n    print('Validation Metrics:', res['validation_metrics'])\n    print('Test Metrics:', res['test_metrics'])\n    print('-'*50)"),
]
with open("notebooks/02_solar_forecasting_training.ipynb", "w") as f:
    json.dump(make_notebook(nb2_cells), f, indent=2)

# 3. Load Training Notebook
nb3_cells = [
    make_cell("markdown", "# 03 - Electricity Demand (Load) Forecasting Model Training\n\nTrains and evaluates 4 forecasting architectures on electrical load demand."),
    make_cell("code", "import sys\nsys.path.append('..')\nimport pandas as pd\nfrom app.ml.load.train import train_load_models\n\nresults = train_load_models(data_path='../data/sample/smart_grid_data.csv', save_dir='../models/saved/load')\nfor m_name, res in results.items():\n    print(f'Model: {m_name}')\n    print('Validation Metrics:', res['validation_metrics'])\n    print('Test Metrics:', res['test_metrics'])\n    print('-'*50)"),
]
with open("notebooks/03_load_forecasting_training.ipynb", "w") as f:
    json.dump(make_notebook(nb3_cells), f, indent=2)

# 4. Simulation & Benchmark Notebook
nb4_cells = [
    make_cell("markdown", "# 04 - Microgrid Simulation & Strategy Benchmarking\n\nCompares:\n1. **Unmanaged Base System**\n2. **Rule-Based EMS (Baseline)**\n3. **Optimization EMS (Proposed ML + PuLP MILP)**"),
    make_cell("code", "import sys\nsys.path.append('..')\nimport pandas as pd\nfrom app.services.analytics_service import AnalyticsService\n\nsvc = AnalyticsService(data_path='../data/sample/smart_grid_data.csv')\ncomp = svc.get_benchmark_comparison(duration_hours=168)\n\nprint('=== Comparative Performance Table ===')\ndf_comp = pd.DataFrame(comp.comparison_table)\nprint(df_comp.to_string(index=False))\n\nprint(f'\\nOptimization Financial Savings vs Unmanaged: ${comp.savings_vs_unmanaged_usd:.2f} ({comp.savings_vs_unmanaged_pct:.1f}%)')\nprint(f'Optimization Financial Savings vs Rule-Based: ${comp.savings_vs_rule_based_usd:.2f} ({comp.savings_vs_rule_based_pct:.1f}%)')\nprint(f'Peak Demand Reduction: {comp.peak_demand_reduction_pct:.1f}%')"),
]
with open("notebooks/04_ems_simulation_comparison.ipynb", "w") as f:
    json.dump(make_notebook(nb4_cells), f, indent=2)

print("All 4 Jupyter notebooks successfully created.")
