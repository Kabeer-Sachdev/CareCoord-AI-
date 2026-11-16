import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from backend.ml.prediction.model_loader import ModelLoader
from backend.ml.preprocessing.feature_engineering import FEATURE_COLUMNS, DEPARTMENT_MAPPING
from backend.ml.preprocessing.data_loader import load_operational_data

DEPARTMENT_BEDS = {
    "Cardiology": 12,
    "Neurology": 8,
    "Orthopedics": 8,
    "General Medicine": 15,
    "Emergency Medicine": 10,
    "Pediatrics": 6,
    "Dermatology": 2
}

class PredictionService:
    def __init__(self):
        self._history_df: Optional[pd.DataFrame] = None

    def _get_history(self) -> pd.DataFrame:
        if self._history_df is None:
            self._history_df = load_operational_data()
        return self._history_df

    def _construct_features(self, department: str, target_dt: datetime) -> np.ndarray:
        """
        Builds a single-row feature vector conforming strictly to FEATURE_COLUMNS.
        Extracts recent history lags without lookahead bias.
        """
        history = self._get_history()
        dept_history = history[history["department"] == department].sort_values("date").reset_index(drop=True)

        dept_code = DEPARTMENT_MAPPING.get(department, 0)
        total_beds = DEPARTMENT_BEDS.get(department, 10)
        dow = target_dt.weekday()
        is_weekend = int(dow >= 5)
        month = target_dt.month
        day = target_dt.day

        # Compute lag and rolling values from most recent records
        if len(dept_history) >= 7:
            recent_7 = dept_history.tail(7)
            recent_1 = dept_history.iloc[-1]

            arr_lag_1 = float(recent_1["patient_arrivals"])
            arr_lag_7 = float(dept_history.iloc[-7]["patient_arrivals"])
            arr_roll_7 = float(recent_7["patient_arrivals"].mean())

            er_lag_1 = float(recent_1["emergency_cases"])
            er_lag_7 = float(dept_history.iloc[-7]["emergency_cases"])
            er_roll_7 = float(recent_7["emergency_cases"].mean())

            occ_lag_1 = float(recent_1["occupied_beds"])
            occ_lag_7 = float(dept_history.iloc[-7]["occupied_beds"])
            occ_roll_7 = float(recent_7["occupied_beds"].mean())

            appt_lag_1 = float(recent_1["appointment_count"])
            appt_lag_7 = float(dept_history.iloc[-7]["appointment_count"])
            appt_roll_7 = float(recent_7["appointment_count"].mean())
        else:
            # Fallbacks if historical depth is minimal
            arr_lag_1, arr_lag_7, arr_roll_7 = 20.0, 20.0, 20.0
            er_lag_1, er_lag_7, er_roll_7 = 5.0, 5.0, 5.0
            occ_lag_1, occ_lag_7, occ_roll_7 = 6.0, 6.0, 6.0
            appt_lag_1, appt_lag_7, appt_roll_7 = 12.0, 12.0, 12.0

        vector = [
            dept_code,
            dow,
            is_weekend,
            month,
            day,
            total_beds,
            arr_lag_1,
            arr_lag_7,
            arr_roll_7,
            er_lag_1,
            er_lag_7,
            er_roll_7,
            occ_lag_1,
            occ_lag_7,
            occ_roll_7,
            appt_lag_1,
            appt_lag_7,
            appt_roll_7
        ]
        return np.array([vector])

    def predict_patient_arrivals(self, department: str, forecast_date: Optional[str] = None) -> Dict[str, Any]:
        """Predicts expected patient arrivals for a given department and date."""
        target_dt = datetime.strptime(forecast_date, "%Y-%m-%d") if forecast_date else (datetime.utcnow() + timedelta(days=1))
        date_str = target_dt.strftime("%Y-%m-%d")

        model_payload = ModelLoader.load_model("patient_arrivals")
        if not model_payload:
            raise RuntimeError("Patient arrivals model artifact not found.")

        X = self._construct_features(department, target_dt)
        raw_pred = float(model_payload["model"].predict(X)[0])
        predicted_val = max(1, int(round(raw_pred)))

        rmse = model_payload["test_metrics"]["rmse"]
        lower_bound = max(0, int(round(predicted_val - 1.28 * rmse))) # ~80% prediction interval
        upper_bound = int(round(predicted_val + 1.28 * rmse))

        return {
            "prediction_type": "patient_arrivals",
            "department": department,
            "forecast_date": date_str,
            "predicted_value": predicted_val,
            "interval_lower": lower_bound,
            "interval_upper": upper_bound,
            "unit": "patients",
            "model_name": model_payload["model_name"],
            "model_version": model_payload["version"],
            "test_mae": model_payload["test_metrics"]["mae"],
            "test_r2": model_payload["test_metrics"]["r2"],
            "prediction_status": "available",
            "data_type": "synthetic_operational"
        }

    def predict_emergency_demand(self, department: str, forecast_date: Optional[str] = None) -> Dict[str, Any]:
        """Predicts expected emergency request volume for a department and date."""
        target_dt = datetime.strptime(forecast_date, "%Y-%m-%d") if forecast_date else (datetime.utcnow() + timedelta(days=1))
        date_str = target_dt.strftime("%Y-%m-%d")

        model_payload = ModelLoader.load_model("emergency_cases")
        if not model_payload:
            raise RuntimeError("Emergency demand model artifact not found.")

        X = self._construct_features(department, target_dt)
        raw_pred = float(model_payload["model"].predict(X)[0])
        predicted_val = max(0, int(round(raw_pred)))

        rmse = model_payload["test_metrics"]["rmse"]
        lower_bound = max(0, int(round(predicted_val - 1.28 * rmse)))
        upper_bound = int(round(predicted_val + 1.28 * rmse))

        # Alert evaluation
        alert = None
        if department == "Emergency Medicine" and predicted_val >= 35:
            alert = "HIGH EMERGENCY SURGE WARNING: Predicted emergency volume exceeds 35 cases."
        elif predicted_val >= 10:
            alert = "ELEVATED EMERGENCY DEMAND: Triage staff notification recommended."

        return {
            "prediction_type": "emergency_demand",
            "department": department,
            "forecast_date": date_str,
            "predicted_value": predicted_val,
            "interval_lower": lower_bound,
            "interval_upper": upper_bound,
            "unit": "emergency_cases",
            "alert": alert,
            "model_name": model_payload["model_name"],
            "model_version": model_payload["version"],
            "test_mae": model_payload["test_metrics"]["mae"],
            "test_r2": model_payload["test_metrics"]["r2"],
            "prediction_status": "available",
            "data_type": "synthetic_operational"
        }

    def predict_bed_occupancy(self, department: str, forecast_date: Optional[str] = None) -> Dict[str, Any]:
        """Estimates occupied beds, available beds, and utilization rate."""
        target_dt = datetime.strptime(forecast_date, "%Y-%m-%d") if forecast_date else (datetime.utcnow() + timedelta(days=1))
        date_str = target_dt.strftime("%Y-%m-%d")

        model_payload = ModelLoader.load_model("occupied_beds")
        if not model_payload:
            raise RuntimeError("Bed occupancy model artifact not found.")

        X = self._construct_features(department, target_dt)
        raw_pred = float(model_payload["model"].predict(X)[0])
        total_beds = DEPARTMENT_BEDS.get(department, 10)
        occupied = min(total_beds, max(0, int(round(raw_pred))))
        available = max(0, total_beds - occupied)
        occupancy_rate = round(occupied / max(1, total_beds), 4)

        alert = None
        if occupancy_rate >= 0.85:
            alert = f"HIGH BED OCCUPANCY ALERT: Predicted utilization in {department} is {round(occupancy_rate * 100)}% (>{85}% threshold)."
        elif occupancy_rate >= 0.75:
            alert = f"ELEVATED BED UTILIZATION: Predicted occupancy is {round(occupancy_rate * 100)}%."

        return {
            "prediction_type": "bed_occupancy",
            "department": department,
            "forecast_date": date_str,
            "predicted_occupied_beds": occupied,
            "estimated_available_beds": available,
            "total_beds": total_beds,
            "occupancy_rate": occupancy_rate,
            "alert": alert,
            "model_name": model_payload["model_name"],
            "model_version": model_payload["version"],
            "test_mae": model_payload["test_metrics"]["mae"],
            "test_r2": model_payload["test_metrics"]["r2"],
            "prediction_status": "available",
            "data_type": "synthetic_operational"
        }

    def predict_appointment_demand(self, department: str, forecast_date: Optional[str] = None) -> Dict[str, Any]:
        """Predicts expected outpatient appointment bookings."""
        target_dt = datetime.strptime(forecast_date, "%Y-%m-%d") if forecast_date else (datetime.utcnow() + timedelta(days=1))
        date_str = target_dt.strftime("%Y-%m-%d")

        model_payload = ModelLoader.load_model("appointment_count")
        if not model_payload:
            raise RuntimeError("Appointment demand model artifact not found.")

        X = self._construct_features(department, target_dt)
        raw_pred = float(model_payload["model"].predict(X)[0])
        predicted_val = max(0, int(round(raw_pred)))

        rmse = model_payload["test_metrics"]["rmse"]
        lower_bound = max(0, int(round(predicted_val - 1.28 * rmse)))
        upper_bound = int(round(predicted_val + 1.28 * rmse))

        return {
            "prediction_type": "appointment_demand",
            "department": department,
            "forecast_date": date_str,
            "predicted_value": predicted_val,
            "interval_lower": lower_bound,
            "interval_upper": upper_bound,
            "unit": "appointments",
            "model_name": model_payload["model_name"],
            "model_version": model_payload["version"],
            "test_mae": model_payload["test_metrics"]["mae"],
            "test_r2": model_payload["test_metrics"]["r2"],
            "prediction_status": "available",
            "data_type": "synthetic_operational"
        }

    def get_forecast_overview(self, forecast_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Aggregates multi-target forecasts across all hospital departments
        for executive hospital operations command center.
        """
        target_dt = datetime.strptime(forecast_date, "%Y-%m-%d") if forecast_date else (datetime.utcnow() + timedelta(days=1))
        date_str = target_dt.strftime("%Y-%m-%d")

        department_forecasts = []
        total_arrivals = 0
        total_emergencies = 0
        total_appointments = 0
        total_occupied_beds = 0
        total_beds = 0
        alerts = []

        for dept_name in DEPARTMENT_MAPPING.keys():
            arr = self.predict_patient_arrivals(dept_name, date_str)
            er = self.predict_emergency_demand(dept_name, date_str)
            bed = self.predict_bed_occupancy(dept_name, date_str)
            appt = self.predict_appointment_demand(dept_name, date_str)

            total_arrivals += arr["predicted_value"]
            total_emergencies += er["predicted_value"]
            total_appointments += appt["predicted_value"]
            total_occupied_beds += bed["predicted_occupied_beds"]
            total_beds += bed["total_beds"]

            if er.get("alert"):
                alerts.append(er["alert"])
            if bed.get("alert"):
                alerts.append(bed["alert"])

            department_forecasts.append({
                "department": dept_name,
                "predicted_arrivals": arr["predicted_value"],
                "predicted_emergencies": er["predicted_value"],
                "predicted_appointments": appt["predicted_value"],
                "predicted_occupied_beds": bed["predicted_occupied_beds"],
                "estimated_available_beds": bed["estimated_available_beds"],
                "total_beds": bed["total_beds"],
                "occupancy_rate": bed["occupancy_rate"]
            })

        overall_occupancy_rate = round(total_occupied_beds / max(1, total_beds), 4)

        return {
            "forecast_date": date_str,
            "total_predicted_arrivals": total_arrivals,
            "total_predicted_emergencies": total_emergencies,
            "total_predicted_appointments": total_appointments,
            "total_occupied_beds": total_occupied_beds,
            "total_available_beds": total_beds - total_occupied_beds,
            "total_beds": total_beds,
            "hospital_occupancy_rate": overall_occupancy_rate,
            "operational_alerts": alerts,
            "department_breakdown": department_forecasts,
            "forecast_generated_at": datetime.utcnow().isoformat(),
            "data_type": "synthetic_operational"
        }

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Returns the persisted evaluation comparison report."""
        report_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "artifacts",
            "model_metrics.json"
        )
        if os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"error": "Model metrics report not yet generated."}

# Global singleton instance
prediction_service = PredictionService()
