"""Model explainability and SHAP attribution service for Solar and Load forecasting.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

try:
    # pyrefly: ignore [missing-import]
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False


class ModelExplainer:
    """Computes global feature attributions and local SHAP waterfall decompositions."""

    @classmethod
    def explain_model(
        cls,
        model: Any,
        X_sample: pd.DataFrame,
        feature_names: Optional[List[str]] = None,
        max_display_features: int = 10,
        local_sample_idx: int = 0,
    ) -> Dict[str, Any]:
        """Generate both global feature importance and local sample SHAP decomposition."""
        if feature_names is None:
            feature_names = list(X_sample.columns)

        X_df = X_sample[feature_names].copy()
        n_samples = len(X_df)

        # Detect underlying estimator
        estimator = getattr(model, "model", model)

        # 1. Calculate SHAP values
        shap_values_matrix = None
        base_value = float(np.mean(getattr(model, "predict", lambda x: [0.0])(X_df)))

        if HAS_SHAP:
            try:
                # TreeExplainer for XGBoost and Random Forest
                explainer = shap.TreeExplainer(estimator)
                raw_shap = explainer.shap_values(X_df)
                if isinstance(raw_shap, list):
                    raw_shap = raw_shap[0]
                shap_values_matrix = np.array(raw_shap)
                if hasattr(explainer, "expected_value"):
                    exp_val = explainer.expected_value
                    if isinstance(exp_val, (list, np.ndarray)):
                        base_value = float(exp_val[0])
                    else:
                        base_value = float(exp_val)
            except Exception:
                shap_values_matrix = None

        # Fallback if SHAP tree explainer not applicable (e.g. linear model or exception)
        if shap_values_matrix is None:
            if hasattr(estimator, "feature_importances_"):
                importances = estimator.feature_importances_
            elif hasattr(estimator, "coef_"):
                coefs = np.ravel(estimator.coef_)
                importances = np.abs(coefs) * np.std(X_df.values, axis=0)
            else:
                importances = np.ones(len(feature_names)) / len(feature_names)

            # Normalize importances
            sum_imp = float(np.sum(importances))
            if sum_imp > 0:
                importances = importances / sum_imp

            # Create synthetic local deviation proportional to feature deviation from mean
            x_centered = (X_df.values - np.mean(X_df.values, axis=0))
            shap_values_matrix = x_centered * importances

        # 2. Global Feature Importance (Mean Absolute SHAP)
        mean_abs_shap = np.mean(np.abs(shap_values_matrix), axis=0)
        sorted_indices = np.argsort(mean_abs_shap)[::-1]

        global_features = []
        for idx in sorted_indices[:max_display_features]:
            global_features.append({
                "feature": feature_names[idx],
                "importance": round(float(mean_abs_shap[idx]), 4),
            })

        # 3. Local Explanation for selected sample
        valid_idx = max(0, min(n_samples - 1, local_sample_idx))
        sample_row = X_df.iloc[valid_idx]
        sample_shap = shap_values_matrix[valid_idx]

        local_sorted_idx = np.argsort(np.abs(sample_shap))[::-1]
        local_attributions = []
        for idx in local_sorted_idx[:max_display_features]:
            local_attributions.append({
                "feature": feature_names[idx],
                "value": round(float(sample_row.iloc[idx]), 4),
                "shap_value": round(float(sample_shap[idx]), 4),
                "direction": "increases_prediction" if sample_shap[idx] >= 0 else "decreases_prediction",
            })

        predicted_val = base_value + float(np.sum(sample_shap))

        return {
            "base_value": round(base_value, 4),
            "predicted_value": round(predicted_val, 4),
            "sample_index": valid_idx,
            "global_importances": global_features,
            "local_attributions": local_attributions,
            "has_native_shap": HAS_SHAP,
        }
