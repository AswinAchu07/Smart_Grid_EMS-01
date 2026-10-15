"""Unit tests for Model Explainability and SHAP Attribution.
"""

import pytest
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import xgboost as xgb
from app.ml.explainability import ModelExplainer


def test_tree_explainer_with_xgboost():
    """Verify SHAP attribution outputs on XGBoost model."""
    np.random.seed(42)
    X = pd.DataFrame(np.random.randn(60, 4), columns=["ghi", "lag_1", "hour_sin", "temp"])
    y = X["ghi"] * 2.5 + X["lag_1"] * 0.8 + np.random.randn(60) * 0.1

    model = xgb.XGBRegressor(n_estimators=10, random_state=42)
    model.fit(X, y)

    res = ModelExplainer.explain_model(
        model=model,
        X_sample=X,
        feature_names=list(X.columns),
        local_sample_idx=0,
    )

    assert "global_importances" in res
    assert "local_attributions" in res
    assert len(res["global_importances"]) == 4
    # GHI should be top feature
    top_feat = res["global_importances"][0]["feature"]
    assert top_feat == "ghi"
    assert res["base_value"] is not None
    assert res["predicted_value"] is not None


def test_tree_explainer_with_random_forest():
    """Verify attribution outputs on Random Forest model."""
    X = pd.DataFrame(np.random.randn(40, 3), columns=["f1", "f2", "f3"])
    y = X["f1"] * 3.0

    rf = RandomForestRegressor(n_estimators=10, random_state=42)
    rf.fit(X, y)

    res = ModelExplainer.explain_model(model=rf, X_sample=X, feature_names=list(X.columns))
    assert len(res["global_importances"]) == 3
    assert res["global_importances"][0]["feature"] == "f1"
