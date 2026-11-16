import os
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database.models import User
from backend.auth.dependencies import get_current_user, require_role
from backend.services.audit_service import log_audit
from backend.ml.prediction.prediction_service import prediction_service
from backend.ml.prediction.model_loader import ModelLoader
from backend.ml.training.train_models import train_and_evaluate_all_models
from backend.schemas.prediction import (
    PredictionRequest,
    PatientArrivalsResponse,
    EmergencyDemandResponse,
    BedOccupancyResponse,
    AppointmentDemandResponse,
    ForecastOverviewResponse
)

router = APIRouter(prefix="/api/ml", tags=["Machine Learning Resource Prediction"])

@router.post("/train", summary="Train or retrain all operational ML models (Admin Only)")
def train_models_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN"))
):
    """
    Executes chronological model training, baseline comparisons, and model artifact serialization.
    Restricted to hospital administrators.
    """
    try:
        report = train_and_evaluate_all_models(save_artifacts=True)
        ModelLoader.clear_cache()

        log_audit(
            db=db,
            user=current_user,
            action="TRAIN_ML_MODELS",
            entity_type="ML_MODEL",
            entity_id="ALL_TARGETS",
            metadata={
                "timestamp": report["training_timestamp"],
                "train_records": report["train_records"],
                "test_records": report["test_records"]
            }
        )
        return {
            "message": "ML models trained and evaluated successfully.",
            "metrics": report
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model training failed: {str(exc)}"
        )

@router.get("/models", summary="List trained models and active versions")
def list_models_endpoint(current_user: User = Depends(get_current_user)):
    """Lists loaded models and their metadata."""
    targets = ["patient_arrivals", "emergency_cases", "occupied_beds", "appointment_count"]
    results = []
    try:
        for t in targets:
            payload = ModelLoader.load_model(t)
            if payload:
                results.append({
                    "target": payload["target"],
                    "target_name": payload["target_name"],
                    "model_name": payload["model_name"],
                    "version": payload["version"],
                    "trained_at": payload["trained_at"],
                    "validation_mae": payload["validation_metrics"]["mae"],
                    "test_mae": payload["test_metrics"]["mae"],
                    "test_r2": payload["test_metrics"]["r2"]
                })
    except Exception:
        pass
    return results

@router.get("/metrics", summary="Get model evaluation and comparison metrics")
def get_metrics_endpoint(current_user: User = Depends(get_current_user)):
    """Returns baseline vs candidate model performance tables."""
    try:
        return prediction_service.get_metrics_summary()
    except Exception:
        return {}

@router.post("/predict/patient-arrivals", response_model=PatientArrivalsResponse)
def predict_patient_arrivals_endpoint(
    req: PredictionRequest,
    current_user: User = Depends(get_current_user)
):
    """Predicts expected patient arrivals for a department on a specified date."""
    try:
        return prediction_service.predict_patient_arrivals(
            department=req.department,
            forecast_date=req.forecast_date
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@router.post("/predict/emergency-demand", response_model=EmergencyDemandResponse)
def predict_emergency_demand_endpoint(
    req: PredictionRequest,
    current_user: User = Depends(get_current_user)
):
    """Predicts expected emergency request workload for a department on a specified date."""
    try:
        return prediction_service.predict_emergency_demand(
            department=req.department,
            forecast_date=req.forecast_date
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@router.post("/predict/bed-occupancy", response_model=BedOccupancyResponse)
def predict_bed_occupancy_endpoint(
    req: PredictionRequest,
    current_user: User = Depends(get_current_user)
):
    """Predicts future occupied beds, available beds, and utilization percentage."""
    try:
        return prediction_service.predict_bed_occupancy(
            department=req.department,
            forecast_date=req.forecast_date
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@router.post("/predict/appointment-demand", response_model=AppointmentDemandResponse)
def predict_appointment_demand_endpoint(
    req: PredictionRequest,
    current_user: User = Depends(get_current_user)
):
    """Predicts outpatient appointment volume for a department on a specified date."""
    try:
        return prediction_service.predict_appointment_demand(
            department=req.department,
            forecast_date=req.forecast_date
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@router.get("/forecast/overview", response_model=ForecastOverviewResponse)
def get_forecast_overview_endpoint(
    forecast_date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Returns aggregated hospital-wide predictive resource forecast across all departments."""
    try:
        return prediction_service.get_forecast_overview(forecast_date=forecast_date)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
