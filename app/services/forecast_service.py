"""Service managing ML forecasting, inference, and model evaluation metrics.
"""

from typing import Optional, Dict, Any, List
import os
import pandas as pd
from sqlalchemy.orm import Session

from app.core.constants import TargetType, ForecastingModelType
from app.data.pipeline import SmartGridDataPipeline
from app.ml.solar.train import train_solar_models
from app.ml.solar.predict import SolarForecastingInference
from app.ml.load.train import train_load_models
from app.ml.load.predict import LoadForecastingInference
from app.ml.metrics import evaluate_forecasting_metrics
from app.schemas.forecast import ForecastResponse, ForecastDataPointSchema
from app.db.models import ForecastRun, ForecastDataPoint, User


class ForecastService:
    """Coordinates data preparation, ML inference, and DB persistence for Solar & Load forecasts."""

    def __init__(self, data_path: str = "data/sample/smart_grid_data.csv"):
        self.data_path = data_path
        self.pipeline = SmartGridDataPipeline(data_path=data_path)

    def ensure_models_trained(self, target_type: str) -> None:
        """Verify model artifacts exist on disk, or trigger training."""
        if target_type == TargetType.SOLAR.value:
            artifact = "models/saved/solar/solar_xgboost.joblib"
            if not os.path.exists(artifact):
                train_solar_models(data_path=self.data_path)
        else:
            artifact = "models/saved/load/load_xgboost.joblib"
            if not os.path.exists(artifact):
                train_load_models(data_path=self.data_path)

    def generate_forecast(
        self,
        target_type: TargetType,
        model_type: ForecastingModelType,
        horizon_hours: int = 24,
        start_time: Optional[str] = None,
        db: Optional[Session] = None,
        user: Optional[User] = None,
    ) -> ForecastResponse:
        """Run ML inference for target series and compute evaluation against actuals."""
        self.ensure_models_trained(target_type.value)

        target_col = "solar_power_kw" if target_type == TargetType.SOLAR else "load_power_kw"
        train_df, val_df, test_df, feature_cols = self.pipeline.run_pipeline(
            target_col=target_col, default_save_path=self.data_path
        )

        # Use test set slice for evaluation and display
        eval_slice = test_df.copy()
        if start_time and "timestamp" in eval_slice.columns:
            filtered = eval_slice[eval_slice["timestamp"] >= pd.to_datetime(start_time)]
            if len(filtered) >= horizon_hours:
                eval_slice = filtered

        eval_slice = eval_slice.iloc[:horizon_hours].reset_index(drop=True)
        X_eval = eval_slice[feature_cols]
        actuals = eval_slice[target_col].values

        if target_type == TargetType.SOLAR:
            infer = SolarForecastingInference(model_type=model_type.value)
        else:
            infer = LoadForecastingInference(model_type=model_type.value)

        preds = infer.predict(X_eval)
        metrics = evaluate_forecasting_metrics(y_true=actuals, y_pred=preds)

        # Compute P10, P50, P90 probabilistic confidence intervals
        from app.ml.quantile import QuantileForecaster
        hours = eval_slice["hour"].values if "hour" in eval_slice.columns else None
        clouds = eval_slice["cloud_cover"].values if "cloud_cover" in eval_slice.columns else None

        if target_type == TargetType.SOLAR:
            q_dict = QuantileForecaster.compute_solar_quantiles(
                point_predictions=preds, hours=hours, cloud_cover=clouds
            )
        else:
            q_dict = QuantileForecaster.compute_load_quantiles(
                point_predictions=preds, hours=hours
            )

        data_points = []
        for i in range(len(eval_slice)):
            ts_str = str(eval_slice.loc[i, "timestamp"]) if "timestamp" in eval_slice.columns else f"T+{i}"
            data_points.append(
                ForecastDataPointSchema(
                    step=i,
                    timestamp=ts_str,
                    predicted_value=round(float(preds[i]), 3),
                    actual_value=round(float(actuals[i]), 3),
                    p10=round(float(q_dict["p10"][i]), 3),
                    p50=round(float(q_dict["p50"][i]), 3),
                    p90=round(float(q_dict["p90"][i]), 3),
                )
            )

        # Persist to database if session provided
        if db:
            run_record = ForecastRun(

                user_id=user.id if user else None,
                target_type=target_type.value,
                model_name=model_type.value,
                horizon_hours=horizon_hours,
                mae=metrics["mae"],
                rmse=metrics["rmse"],
                mape=metrics["mape"],
                r2=metrics["r2"],
            )
            db.add(run_record)
            db.flush()

            for dp in data_points:
                dp_record = ForecastDataPoint(
                    forecast_id=run_record.id,
                    step=dp.step,
                    timestamp=dp.timestamp,
                    actual_value=dp.actual_value,
                    predicted_value=dp.predicted_value,
                )
                db.add(dp_record)
            db.commit()

        return ForecastResponse(
            target_type=target_type.value,
            model_name=model_type.value,
            horizon_hours=horizon_hours,
            data_points=data_points,
            metrics=metrics,
        )

    def get_all_model_benchmarks(self, target_type: TargetType) -> Dict[str, Any]:
        """Evaluate all 4 candidate models against the holdout test set."""
        target_col = "solar_power_kw" if target_type == TargetType.SOLAR else "load_power_kw"
        train_df, val_df, test_df, feature_cols = self.pipeline.run_pipeline(
            target_col=target_col, default_save_path=self.data_path
        )
        X_test = test_df[feature_cols]
        y_test = test_df[target_col]

        models = [
            ForecastingModelType.PERSISTENCE,
            ForecastingModelType.LINEAR_RIDGE,
            ForecastingModelType.RANDOM_FOREST,
            ForecastingModelType.XGBOOST,
        ]

        benchmarks = {}
        for m in models:
            if target_type == TargetType.SOLAR:
                infer = SolarForecastingInference(model_type=m.value)
            else:
                infer = LoadForecastingInference(model_type=m.value)

            preds = infer.predict(X_test)
            benchmarks[m.value] = evaluate_forecasting_metrics(y_true=y_test.values, y_pred=preds)

        return {
            "target_type": target_type.value,
            "models": benchmarks,
        }

    def explain_forecast(
        self,
        target_type: TargetType,
        model_type: ForecastingModelType = ForecastingModelType.XGBOOST,
        sample_index: int = 0,
    ) -> Dict[str, Any]:
        """Compute SHAP global importance and local waterfall decomposition."""
        from app.ml.explainability import ModelExplainer

        self.ensure_models_trained(target_type.value)
        target_col = "solar_power_kw" if target_type == TargetType.SOLAR else "load_power_kw"
        train_df, val_df, test_df, feature_cols = self.pipeline.run_pipeline(
            target_col=target_col, default_save_path=self.data_path
        )
        if target_type == TargetType.SOLAR:
            infer = SolarForecastingInference(model_type=model_type.value)
        else:
            infer = LoadForecastingInference(model_type=model_type.value)

        explanation = ModelExplainer.explain_model(
            model=infer.model,
            X_sample=test_df[feature_cols].iloc[:100],
            feature_names=feature_cols,
            local_sample_idx=sample_index,
        )
        explanation["target_type"] = target_type.value
        explanation["model_name"] = model_type.value
        return explanation

