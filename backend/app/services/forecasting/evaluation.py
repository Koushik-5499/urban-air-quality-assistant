"""Time-series model evaluation engine calculating MAE, RMSE, MAPE, and horizon errors."""

import math
from dataclasses import dataclass, field

from app.services.forecasting.data_preparation import DatasetSplits
from app.services.forecasting.models.base import BaseForecastModel
from app.services.forecasting.models.persistence import PersistenceModel


@dataclass
class HorizonEvaluation:
    """Evaluation metrics for a specific forecast horizon."""

    horizon_hours: int
    sample_count: int
    mae: float
    rmse: float
    mape: float | None = None


@dataclass
class EvaluationReport:
    """
    Comprehensive out-of-sample evaluation report comparing model against persistence baseline.
    """

    model_name: str
    model_version: str
    sample_count: int
    overall_mae: float
    overall_rmse: float
    overall_mape: float | None
    horizon_metrics: list[HorizonEvaluation] = field(default_factory=list)
    baseline_mae: float = 0.0
    baseline_rmse: float = 0.0
    improvement_vs_baseline_pct: float = 0.0
    is_statistically_sound: bool = True
    notes: str = ""


class ForecastEvaluator:
    """Evaluates time-series models on hold-out validation and test sets without data leakage."""

    @staticmethod
    def calculate_mae(actuals: list[float], predictions: list[float]) -> float:
        """Mean Absolute Error."""
        if not actuals or len(actuals) != len(predictions):
            return 0.0
        return round(sum(abs(a - p) for a, p in zip(actuals, predictions)) / float(len(actuals)), 2)

    @staticmethod
    def calculate_rmse(actuals: list[float], predictions: list[float]) -> float:
        """Root Mean Squared Error."""
        if not actuals or len(actuals) != len(predictions):
            return 0.0
        mse = sum((a - p) ** 2 for a, p in zip(actuals, predictions)) / float(len(actuals))
        return round(math.sqrt(mse), 2)

    @staticmethod
    def calculate_mape(actuals: list[float], predictions: list[float]) -> float | None:
        """Mean Absolute Percentage Error safely handling zero or near-zero observations."""
        if not actuals or len(actuals) != len(predictions):
            return None
        percentage_errors = [abs(a - p) / max(a, 1.0) for a, p in zip(actuals, predictions)]
        return round((sum(percentage_errors) / float(len(actuals))) * 100.0, 2)

    @classmethod
    def evaluate_model(
        cls,
        model: BaseForecastModel,
        splits: DatasetSplits,
        horizons: list[int] | None = None,
    ) -> EvaluationReport:
        """Fit model on training split and evaluate out-of-sample performance on test split."""
        eval_horizons = horizons or [1, 6, 12, 24]
        test_y = splits.test_values
        test_n = len(test_y)

        if test_n == 0:
            return EvaluationReport(
                model_name=model.name,
                model_version=model.version,
                sample_count=0,
                overall_mae=0.0,
                overall_rmse=0.0,
                overall_mape=None,
                is_statistically_sound=False,
                notes="Test split is empty. Cannot evaluate out-of-sample forecast accuracy.",
            )

        # 1. Fit target model on training data
        model.fit(splits.train_values, splits.train_timestamps)
        predictions = model.predict(test_n)

        # 2. Fit and predict baseline (Persistence) on the same dataset
        baseline = PersistenceModel()
        baseline.fit(splits.train_values, splits.train_timestamps)
        baseline_preds = baseline.predict(test_n)

        overall_mae = cls.calculate_mae(test_y, predictions)
        overall_rmse = cls.calculate_rmse(test_y, predictions)
        overall_mape = cls.calculate_mape(test_y, predictions)

        baseline_mae = cls.calculate_mae(test_y, baseline_preds)
        baseline_rmse = cls.calculate_rmse(test_y, baseline_preds)

        # Percent improvement over baseline (positive = model is better than baseline)
        if baseline_mae > 0:
            improvement = round(((baseline_mae - overall_mae) / baseline_mae) * 100.0, 1)
        else:
            improvement = 0.0

        # 3. Calculate per-horizon error metrics
        horizon_evals: list[HorizonEvaluation] = []
        for h in eval_horizons:
            if h <= test_n:
                h_actuals = test_y[:h]
                h_preds = predictions[:h]
                h_mae = cls.calculate_mae(h_actuals, h_preds)
                h_rmse = cls.calculate_rmse(h_actuals, h_preds)
                h_mape = cls.calculate_mape(h_actuals, h_preds)
                horizon_evals.append(
                    HorizonEvaluation(
                        horizon_hours=h,
                        sample_count=h,
                        mae=h_mae,
                        rmse=h_rmse,
                        mape=h_mape,
                    )
                )

        return EvaluationReport(
            model_name=model.name,
            model_version=model.version,
            sample_count=test_n,
            overall_mae=overall_mae,
            overall_rmse=overall_rmse,
            overall_mape=overall_mape,
            horizon_metrics=horizon_evals,
            baseline_mae=baseline_mae,
            baseline_rmse=baseline_rmse,
            improvement_vs_baseline_pct=improvement,
            is_statistically_sound=test_n >= 6,
            notes=(
                f"Evaluated on {test_n} hold-out points. "
                f"Baseline MAE: {baseline_mae}, Model MAE: {overall_mae} "
                f"({improvement:+}% improvement)."
            ),
        )
