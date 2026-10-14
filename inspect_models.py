"""Inspect and view the internal parameters, feature importances, and metrics
of the trained .joblib machine learning models in VS Code.

Usage in VS Code Terminal:
    python inspect_models.py
"""

import os
import joblib
import pandas as pd

def inspect_saved_models():
    print("=" * 70)
    print("🔍 SMART GRID EMS - MACHINE LEARNING MODEL INSPECTOR")
    print("=" * 70)

    # 1. Solar Models Inspection
    solar_dir = os.path.join("models", "saved", "solar")
    print(f"\n☀️  SOLAR FORECASTING MODELS ({solar_dir}):")
    print("-" * 70)
    if os.path.exists(solar_dir):
        for fname in sorted(os.listdir(solar_dir)):
            if fname.endswith(".joblib"):
                fpath = os.path.join(solar_dir, fname)
                size_kb = os.path.getsize(fpath) / 1024
                model_obj = joblib.load(fpath)
                print(f"\n📦 File: {fname} ({size_kb:.1f} KB)")
                print(f"   Type: {type(model_obj).__name__}")
                
                # Check for feature importances / params
                if hasattr(model_obj, "feature_names_in_"):
                    print(f"   Features ({len(model_obj.feature_names_in_)}): {list(model_obj.feature_names_in_)}")
                if hasattr(model_obj, "feature_importances_"):
                    top_feats = sorted(
                        zip(getattr(model_obj, "feature_names_in_", range(len(model_obj.feature_importances_))), model_obj.feature_importances_),
                        key=lambda x: x[1],
                        reverse=True
                    )[:5]
                    print(f"   Top 5 Important Features: {top_feats}")
                if hasattr(model_obj, "get_params"):
                    params = model_obj.get_params()
                    key_params = {k: v for k, v in list(params.items())[:6]}
                    print(f"   Hyperparameters: {key_params}")

    # 2. Load Models Inspection
    load_dir = os.path.join("models", "saved", "load")
    print(f"\n\n💡 ELECTRICITY LOAD FORECASTING MODELS ({load_dir}):")
    print("-" * 70)
    if os.path.exists(load_dir):
        for fname in sorted(os.listdir(load_dir)):
            if fname.endswith(".joblib"):
                fpath = os.path.join(load_dir, fname)
                size_kb = os.path.getsize(fpath) / 1024
                model_obj = joblib.load(fpath)
                print(f"\n📦 File: {fname} ({size_kb:.1f} KB)")
                print(f"   Type: {type(model_obj).__name__}")
                
                if hasattr(model_obj, "feature_names_in_"):
                    print(f"   Features ({len(model_obj.feature_names_in_)}): {list(model_obj.feature_names_in_)}")
                if hasattr(model_obj, "feature_importances_"):
                    top_feats = sorted(
                        zip(getattr(model_obj, "feature_names_in_", range(len(model_obj.feature_importances_))), model_obj.feature_importances_),
                        key=lambda x: x[1],
                        reverse=True
                    )[:5]
                    print(f"   Top 5 Important Features: {top_feats}")
                if hasattr(model_obj, "get_params"):
                    params = model_obj.get_params()
                    key_params = {k: v for k, v in list(params.items())[:6]}
                    print(f"   Hyperparameters: {key_params}")

    print("\n" + "=" * 70)
    print("✅ Model Inspection Complete!")
    print("=" * 70)

if __name__ == "__main__":
    inspect_saved_models()
