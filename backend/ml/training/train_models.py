import os
import sys
from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from backend.ml.preprocessing.data_loader import load_operational_data
from backend.ml.preprocessing.cleaning import DataCleaner
from backend.ml.preprocessing.feature_engineering import FeatureEngineer, FEATURE_COLUMNS, DEPARTMENT_MAPPING
from backend.ml.models.base_model import BaselineMovingAverageModel
from backend.ml.evaluation.metrics import calculate_regression_metrics

PREDICTION_TARGETS = [
    {
        "target": "patient_arrivals",
        "name": "Patient Arrival Prediction",
        "baseline_col": "arrivals_rolling_7d",
        "artifact_file": "patient_arrivals_model.joblib"
    },
    {
        "target": "emergency_cases",
        "name": "Emergency Demand Prediction",
        "baseline_col": "emergency_rolling_7d",
        "artifact_file": "emergency_demand_model.joblib"
    },
    {
        "target": "occupied_beds",
        "name": "Bed Occupancy Prediction",
        "baseline_col": "occupied_beds_rolling_7d",
        "artifact_file": "bed_occupancy_model.joblib"
    },
    {
        "target": "appointment_count",
        "name": "Appointment Demand Prediction",
        "baseline_col": "appointments_rolling_7d",
        "artifact_file": "appointment_demand_model.joblib"
    }
]

def train_and_evaluate_all_models(save_artifacts: bool = True) -> dict:
    """
    Executes the complete ML training, evaluation, comparison and serialization pipeline:
    1. Loads and cleans operational data
    2. Builds lag and rolling features
    3. Chronological train/val/test splitting (70% / 15% / 15%)
    4. Compares Baseline, Random Forest, and Gradient Boosting models
    5. Evaluates metrics (MAE, RMSE, R2, MAPE)
    6. Serializes winning models with metadata
    """
    print("=" * 75)
    print("CareCoord Phase 6 - Hospital Resource Demand ML Training Pipeline")
    print("=" * 75)

    # 1. Load & Clean Data
    raw_df = load_operational_data()
    clean_df = DataCleaner.clean(raw_df)
    print(f"[Data] Loaded {len(clean_df)} operational records from {clean_df['date'].min().date()} to {clean_df['date'].max().date()}")

    # 2. Feature Engineering
    feat_df = FeatureEngineer.build_features(clean_df)
    train_df, val_df, test_df = FeatureEngineer.chronological_split(feat_df, train_ratio=0.70, val_ratio=0.15)

    print(f"[Split] Chronological Split: Train={len(train_df)} | Val={len(val_df)} | Test={len(test_df)} records")

    artifacts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "artifacts")
    models_dir = os.path.join(artifacts_dir, "models")
    os.makedirs(models_dir, exist_ok=True)

    metrics_report = {
        "training_timestamp": datetime.utcnow().isoformat(),
        "total_records": len(clean_df),
        "train_records": len(train_df),
        "val_records": len(val_df),
        "test_records": len(test_df),
        "feature_columns": FEATURE_COLUMNS,
        "departments": list(DEPARTMENT_MAPPING.keys()),
        "targets": {}
    }

    print("\n" + "-" * 75)
    print(f"{'Target':<22} | {'Model':<20} | {'Test MAE':<10} | {'Test RMSE':<10} | {'Test R²':<8}")
    print("-" * 75)

    X_train = train_df[FEATURE_COLUMNS].values
    X_val = val_df[FEATURE_COLUMNS].values
    X_test = test_df[FEATURE_COLUMNS].values

    for cfg in PREDICTION_TARGETS:
        target = cfg["target"]
        target_name = cfg["name"]
        baseline_col_idx = FEATURE_COLUMNS.index(cfg["baseline_col"])

        y_train = train_df[target].values
        y_val = val_df[target].values
        y_test = test_df[target].values

        # Model 1: Baseline Moving Average
        baseline = BaselineMovingAverageModel(fallback_col_idx=baseline_col_idx)
        baseline.fit(X_train, y_train)
        pred_base_val = baseline.predict(X_val)
        pred_base_test = baseline.predict(X_test)
        metrics_base_val = calculate_regression_metrics(y_val, pred_base_val)
        metrics_base_test = calculate_regression_metrics(y_test, pred_base_test)

        # Model 2: Random Forest Regressor
        rf = RandomForestRegressor(
            n_estimators=100,
            max_depth=8,
            min_samples_split=4,
            random_state=42,
            n_jobs=-1
        )
        rf.fit(X_train, y_train)
        pred_rf_val = rf.predict(X_val)
        pred_rf_test = rf.predict(X_test)
        metrics_rf_val = calculate_regression_metrics(y_val, pred_rf_val)
        metrics_rf_test = calculate_regression_metrics(y_test, pred_rf_test)

        # Model 3: Gradient Boosting Regressor
        gb = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.08,
            max_depth=4,
            subsample=0.85,
            random_state=42
        )
        gb.fit(X_train, y_train)
        pred_gb_val = gb.predict(X_val)
        pred_gb_test = gb.predict(X_test)
        metrics_gb_val = calculate_regression_metrics(y_val, pred_gb_val)
        metrics_gb_test = calculate_regression_metrics(y_test, pred_gb_test)

        # Compare on Validation MAE to select winner
        candidate_models = [
            ("BaselineMovingAverage", baseline, metrics_base_val, metrics_base_test),
            ("RandomForestRegressor", rf, metrics_rf_val, metrics_rf_test),
            ("GradientBoostingRegressor", gb, metrics_gb_val, metrics_gb_test)
        ]

        # Select model with lowest validation MAE
        candidate_models.sort(key=lambda x: x[2]["mae"])
        best_name, best_model, best_val_m, best_test_m = candidate_models[0]

        # Print comparison rows
        for name, _, _, test_m in candidate_models:
            is_win = " *" if name == best_name else ""
            print(f"{target:<22} | {name + is_win:<20} | {test_m['mae']:<10} | {test_m['rmse']:<10} | {test_m['r2']:<8}")

        # Save artifacts
        if save_artifacts and best_name != "BaselineMovingAverage":
            artifact_path = os.path.join(models_dir, cfg["artifact_file"])
            payload = {
                "model": best_model,
                "model_name": best_name,
                "target": target,
                "target_name": target_name,
                "features": FEATURE_COLUMNS,
                "version": "1.0",
                "validation_metrics": best_val_m,
                "test_metrics": best_test_m,
                "trained_at": datetime.utcnow().isoformat()
            }
            joblib.dump(payload, artifact_path)

        metrics_report["targets"][target] = {
            "target_name": target_name,
            "selected_model": best_name,
            "artifact_file": cfg["artifact_file"],
            "models_comparison": {
                "BaselineMovingAverage": {"val": metrics_base_val, "test": metrics_base_test},
                "RandomForestRegressor": {"val": metrics_rf_val, "test": metrics_rf_test},
                "GradientBoostingRegressor": {"val": metrics_gb_val, "test": metrics_gb_test}
            },
            "selected_metrics": {
                "validation": best_val_m,
                "test": best_test_m
            }
        }

    # Save metrics JSON report
    report_file = os.path.join(artifacts_dir, "model_metrics.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(metrics_report, f, indent=2)

    print("-" * 75)
    print(f"(* indicates winning model selected on validation set)")
    print(f"Model artifacts and evaluation report successfully persisted to:\n  - {models_dir}\n  - {report_file}")
    print("=" * 75)

    return metrics_report

if __name__ == "__main__":
    train_and_evaluate_all_models()
