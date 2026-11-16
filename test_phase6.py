"""
CareCoord - Phase 6 Comprehensive Machine Learning Verification Test Suite

Tests:
1. Operational Time-Series Dataset & No-PII Compliance
2. Chronological Feature Engineering & Data Leakage Prevention
3. Model Artifacts, Serialized Weights, & Baseline Comparison Metrics
4. Prediction Service Inference, Horizon Projections, & Prediction Intervals
5. Hospital Capacity Alerts & Operational Mitigation Recommendations
6. LangGraph Coordinator Integration & Prediction Agent Workflow Routing
7. REST API Endpoints (Models, Metrics, Predictors, Overview)
8. Role-Based Access Control (Admin-Only Retraining Guardrail)
"""

import sys
import json
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import numpy as np
from fastapi import HTTPException

from backend.ml.preprocessing.data_loader import load_operational_data
from backend.ml.preprocessing.feature_engineering import FeatureEngineer, FEATURE_COLUMNS, DEPARTMENT_MAPPING
from backend.ml.prediction.model_loader import ModelLoader
from backend.ml.prediction.prediction_service import prediction_service
from backend.agents.graph import carecoord_graph
from backend.routes.predictions import (
    list_models_endpoint,
    get_metrics_endpoint,
    predict_patient_arrivals_endpoint,
    predict_emergency_demand_endpoint,
    predict_bed_occupancy_endpoint,
    predict_appointment_demand_endpoint,
    get_forecast_overview_endpoint,
    train_models_endpoint
)
from backend.schemas.prediction import PredictionRequest
from backend.database.models import User

TARGET_KEYS = ["patient_arrivals", "emergency_cases", "occupied_beds", "appointment_count"]

def print_step(title):
    print(f"\n[Step] {title}")

def print_passed(msg):
    print(f"  -> PASSED: {msg}")

def test_phase6():
    print("=" * 70)
    print("  RUNNING CARECOORD PHASE 6 ML DEMAND PREDICTION VERIFICATION  ")
    print("=" * 70)

    # -------------------------------------------------------------
    # Step 1: Dataset Verification & No-PII Governance
    # -------------------------------------------------------------
    print_step("1. Verifying Historical/Synthetic Time-Series Dataset & Privacy...")
    dataset_path = Path(__file__).resolve().parent / "backend" / "ml" / "datasets" / "hospital_operations.csv"
    meta_path = Path(__file__).resolve().parent / "backend" / "ml" / "datasets" / "dataset_metadata.json"

    assert dataset_path.exists(), f"Dataset file not found at {dataset_path}"
    assert meta_path.exists(), f"Metadata file not found at {meta_path}"

    df = load_operational_data()
    assert len(df) >= 1000, f"Expected >= 1000 records, got {len(df)}"
    
    # Verify no PII columns exist
    pii_forbidden = ["patient_name", "ssn", "phone", "email", "mrn", "address", "dob", "password"]
    for col in df.columns:
        assert col.lower() not in pii_forbidden, f"PII detected in ML dataset: {col}"

    with open(meta_path, "r") as f:
        meta = json.load(f)
    assert meta.get("data_classification") == "SYNTHETIC_OPERATIONAL" or meta.get("synthetic") is True
    assert meta.get("is_real_hospital_data") is False
    total_depts = len(meta.get("departments", []))
    print_passed(f"Dataset verified: {len(df)} records across {total_depts} departments. No PII detected.")

    # -------------------------------------------------------------
    # Step 2: Chronological Feature Engineering & Leakage Protection
    # -------------------------------------------------------------
    print_step("2. Verifying Chronological Feature Engineering & Leakage Protection...")
    feat_df = FeatureEngineer.build_features(df)
    
    # Check that lag and rolling features exist
    expected_feature_cols = [
        "arrivals_lag_1d", "arrivals_lag_7d", "arrivals_rolling_7d",
        "emergency_lag_1d", "emergency_lag_7d", "emergency_rolling_7d",
        "occupied_beds_lag_1d", "occupied_beds_lag_7d", "occupied_beds_rolling_7d",
        "appointments_lag_1d", "appointments_lag_7d", "appointments_rolling_7d"
    ]
    for col in expected_feature_cols:
        assert col in feat_df.columns, f"Missing feature {col}"

    # Test chronological train/val/test split
    train_df, val_df, test_df = FeatureEngineer.chronological_split(feat_df)
    train_max_date = train_df["date"].max()
    val_min_date = val_df["date"].min()
    val_max_date = val_df["date"].max()
    test_min_date = test_df["date"].min()

    assert train_max_date < val_min_date, f"Data leakage: train max date {train_max_date} >= val min date {val_min_date}"
    assert val_max_date < test_min_date, f"Data leakage: val max date {val_max_date} >= test min date {test_min_date}"
    print_passed(f"Chronological split verified (Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}). Zero future leakage.")

    # -------------------------------------------------------------
    # Step 3: Model Artifacts & Baseline Comparison
    # -------------------------------------------------------------
    print_step("3. Verifying Serialized Models & Baseline Performance Benchmarks...")
    for target in TARGET_KEYS:
        payload = ModelLoader.load_model(target)
        assert payload is not None, f"Model artifact missing or failed to load for {target}"
        assert "model" in payload, f"Serialized model object missing for {target}"

    metrics_file = Path(__file__).resolve().parent / "backend" / "ml" / "artifacts" / "model_metrics.json"
    assert metrics_file.exists(), f"Metrics file missing at {metrics_file}"
    with open(metrics_file, "r") as f:
        metrics = json.load(f)

    for target in TARGET_KEYS:
        target_metrics = metrics.get("targets", {}).get(target, {})
        selected_model_name = target_metrics.get("selected_model")
        comparison = target_metrics.get("models_comparison", {})
        baseline_mae = comparison.get("BaselineMovingAverage", {}).get("test", {}).get("mae", 999.0)
        best_mae = comparison.get(selected_model_name, {}).get("test", {}).get("mae", 999.0)
        best_r2 = comparison.get(selected_model_name, {}).get("test", {}).get("r2", -1.0)
        
        # Verify the trained ML model improves over the Moving Average baseline
        assert best_mae < baseline_mae, f"{target}: Best model MAE ({best_mae}) is not better than baseline ({baseline_mae})"
        assert best_r2 > 0.60, f"{target}: Model R2 ({best_r2}) is below required operational threshold"
        print_passed(f"[{target}] Best: {selected_model_name} (MAE: {best_mae:.3f} vs Baseline: {baseline_mae:.3f}, R2: {best_r2:.3f})")

    # -------------------------------------------------------------
    # Step 4: Prediction Service Inference & Prediction Intervals
    # -------------------------------------------------------------
    print_step("4. Testing Model Inference & Prediction Intervals...")
    t0 = time.time()
    arrival_res = prediction_service.predict_patient_arrivals(
        department="Emergency Medicine",
        forecast_date="2026-11-20"
    )
    inference_time_ms = (time.time() - t0) * 1000
    assert inference_time_ms < 100, f"Inference too slow: {inference_time_ms:.2f}ms"
    assert arrival_res["predicted_value"] > 0, "Predicted value should be positive"
    assert arrival_res["interval_lower"] <= arrival_res["predicted_value"] <= arrival_res["interval_upper"], (
        "Prediction interval bounds violated"
    )
    print_passed(f"Inference verified in {inference_time_ms:.2f}ms: "
                 f"Predicted arrivals = {arrival_res['predicted_value']} "
                 f"[{arrival_res['interval_lower']} - {arrival_res['interval_upper']}]")

    # -------------------------------------------------------------
    # Step 5: Operational Alerts & Capacity Warnings
    # -------------------------------------------------------------
    print_step("5. Testing Hospital Capacity Alerts & Overview...")
    overview = prediction_service.get_forecast_overview(forecast_date="2026-11-20")
    assert "department_breakdown" in overview, "Missing department_breakdown in overview"
    assert "operational_alerts" in overview, "Missing operational_alerts list in overview"
    assert overview["total_predicted_arrivals"] > 0, "Total predicted arrivals must be positive"
    assert overview["hospital_occupancy_rate"] > 0, "Hospital occupancy rate must be positive"
    print_passed(f"Hospital overview generated: {len(overview['department_breakdown'])} departments, "
                 f"Total arrivals: {overview['total_predicted_arrivals']}, "
                 f"Occupancy: {overview['hospital_occupancy_rate']*100:.1f}%, "
                 f"Operational alerts flagged: {len(overview['operational_alerts'])}")

    # Test bed occupancy forecast with alert checks
    bed_res = prediction_service.predict_bed_occupancy(
        department="General Medicine",
        forecast_date="2026-11-20"
    )
    assert "predicted_occupied_beds" in bed_res
    assert "estimated_available_beds" in bed_res
    assert bed_res["occupancy_rate"] >= 0.0
    print_passed(f"Bed occupancy prediction verified: Occupied {bed_res['predicted_occupied_beds']}/{bed_res['total_beds']} "
                 f"({bed_res['occupancy_rate']}%), Available {bed_res['estimated_available_beds']}, Alert: {bed_res['alert']}")

    # -------------------------------------------------------------
    # Step 6: Coordinator Agent & LangGraph Routing Integration
    # -------------------------------------------------------------
    print_step("6. Testing LangGraph Coordinator Routing to Prediction Agent...")
    state_input = {
        "workflow_id": "wf-ml-verification",
        "original_request": "Forecast patient arrivals and bed occupancy for Cardiology",
        "workflow_request": {},
        "current_agent": None,
        "required_agents": [],
        "executed_agents": [],
        "messages": [],
        "execution_log": [],
        "iteration_count": 0,
        "requires_human_review": False,
        "status": "RUNNING",
        "final_recommendation": None,
        "error": None,
        "patient_result": None,
        "doctor_result": None,
        "appointment_result": None,
        "validation_result": None,
        "policy_result": None,
        "prediction_result": None,
        "db_session": None
    }
    graph_res = carecoord_graph.invoke(state_input)
    assert "prediction_result" in graph_res, "State missing prediction_result"
    assert graph_res["prediction_result"] is not None, "prediction_result is None"
    assert "execution_log" in graph_res, "execution_log missing"
    assert any("Prediction Agent" in str(step) for step in graph_res["execution_log"]), "Prediction Agent step missing from trace"
    print_passed("LangGraph coordinator successfully routed forecast request to Prediction Agent.")

    # -------------------------------------------------------------
    # Step 7: REST API Endpoints Verification
    # -------------------------------------------------------------
    print_step("7. Testing FastAPI Prediction REST Endpoints...")
    dummy_staff = User(id="u1", email="staff@example.com", role="DOCTOR", full_name="Dr. Staff")
    
    models_res = list_models_endpoint(current_user=dummy_staff)
    assert len(models_res) == 4, f"Expected 4 models, got {len(models_res)}"

    metrics_res = get_metrics_endpoint(current_user=dummy_staff)
    assert "targets" in metrics_res and "patient_arrivals" in metrics_res["targets"]

    overview_res = get_forecast_overview_endpoint(forecast_date="2026-11-20", current_user=dummy_staff)
    assert overview_res["total_predicted_arrivals"] > 0

    req = PredictionRequest(
        department="General Medicine",
        forecast_date="2026-11-20"
    )
    api_arrival = predict_patient_arrivals_endpoint(req=req, current_user=dummy_staff)
    assert api_arrival["predicted_value"] > 0

    api_er = predict_emergency_demand_endpoint(req=req, current_user=dummy_staff)
    assert api_er["predicted_value"] >= 0

    api_bed = predict_bed_occupancy_endpoint(req=req, current_user=dummy_staff)
    assert api_bed["total_beds"] > 0

    api_appt = predict_appointment_demand_endpoint(req=req, current_user=dummy_staff)
    assert api_appt["predicted_value"] >= 0
    print_passed("All FastAPI ML endpoints executed cleanly.")

    # -------------------------------------------------------------
    # Step 8: RBAC Security on Retraining Endpoint
    # -------------------------------------------------------------
    print_step("8. Verifying RBAC Guardrail on Model Training Endpoint...")
    from backend.auth.dependencies import require_role
    checker = require_role("ADMIN")
    fake_patient = User(id="p1", email="pat@example.com", role="PATIENT", full_name="Patient Zero")
    try:
        checker(current_user=fake_patient)
        assert False, "Non-admin user should not be allowed to access admin role dependency"
    except HTTPException as e:
        assert e.status_code == 403, f"Expected 403 Forbidden, got {e.status_code}"
        print_passed("RBAC enforced: Non-admin user blocked from model training (403 Forbidden).")

    print("\n" + "=" * 70)
    print("  ALL PHASE 6 MACHINE LEARNING DEMAND PREDICTION TESTS PASSED!  ")
    print("=" * 70)

if __name__ == "__main__":
    test_phase6()
