import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

DEPARTMENTS = [
    {"name": "Cardiology", "base_arrivals": 22, "total_beds": 12, "emergency_ratio": 0.25, "appt_ratio": 0.65},
    {"name": "Neurology", "base_arrivals": 16, "total_beds": 8, "emergency_ratio": 0.20, "appt_ratio": 0.70},
    {"name": "Orthopedics", "base_arrivals": 20, "total_beds": 8, "emergency_ratio": 0.15, "appt_ratio": 0.75},
    {"name": "General Medicine", "base_arrivals": 30, "total_beds": 15, "emergency_ratio": 0.30, "appt_ratio": 0.60},
    {"name": "Emergency Medicine", "base_arrivals": 35, "total_beds": 10, "emergency_ratio": 0.85, "appt_ratio": 0.10},
    {"name": "Pediatrics", "base_arrivals": 18, "total_beds": 6, "emergency_ratio": 0.20, "appt_ratio": 0.70},
    {"name": "Dermatology", "base_arrivals": 14, "total_beds": 2, "emergency_ratio": 0.05, "appt_ratio": 0.90}
]

def generate_operational_dataset(
    start_date: str = "2026-05-15",
    days: int = 180,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generates a realistic, synthetic historical operational time-series dataset.
    Incorporates day-of-week trends, department-specific resource constraints,
    seasonal noise, and bed occupancy dynamics.
    """
    np.random.seed(seed)
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    
    records = []

    for d_idx in range(days):
        current_date = start_dt + timedelta(days=d_idx)
        date_str = current_date.strftime("%Y-%m-%d")
        dow = current_date.weekday() # 0 = Monday, 6 = Sunday
        is_weekend = int(dow >= 5)

        # Day-of-week multiplier: Higher on Monday/Tuesday, lower on weekends for elective care
        dow_mult = {0: 1.25, 1: 1.15, 2: 1.05, 3: 1.0, 4: 0.95, 5: 0.65, 6: 0.55}[dow]
        # Emergency multiplier is elevated on weekends
        er_dow_mult = 1.25 if is_weekend else 0.95

        for dept in DEPARTMENTS:
            dept_name = dept["name"]
            base_arr = dept["base_arrivals"]
            total_beds = dept["total_beds"]

            # Calculate patient arrivals
            if dept_name == "Emergency Medicine":
                mean_arrivals = base_arr * er_dow_mult
            else:
                mean_arrivals = base_arr * dow_mult

            noise = np.random.normal(0, 2.5)
            patient_arrivals = max(3, int(round(mean_arrivals + noise)))

            # Calculate appointments
            if dept_name == "Emergency Medicine":
                appointment_count = max(0, int(round(patient_arrivals * dept["appt_ratio"] + np.random.normal(0, 1))))
            else:
                appt_mean = patient_arrivals * dept["appt_ratio"]
                appointment_count = max(1, int(round(appt_mean + np.random.normal(0, 2))))

            # Calculate emergency cases
            er_mean = patient_arrivals * dept["emergency_ratio"] * (er_dow_mult if is_weekend else 1.0)
            emergency_cases = max(0, int(round(er_mean + np.random.normal(0, 1.5))))

            # Active/available doctors (varies between weekday & weekend)
            base_docs = 4 if total_beds >= 10 else 2
            available_doctors = max(1, base_docs - 1 if is_weekend else base_docs + np.random.choice([0, 1]))

            # Bed occupancy dynamics
            # Emergency + Inpatient arrivals drive occupied beds
            if total_beds > 0:
                base_occ_ratio = min(0.95, max(0.40, (patient_arrivals / (base_arr * 1.5)) * 0.75 + np.random.normal(0, 0.08)))
                occupied_beds = min(total_beds, max(1, int(round(total_beds * base_occ_ratio))))
                available_beds = total_beds - occupied_beds
                bed_occupancy_rate = round(occupied_beds / total_beds, 4)
            else:
                occupied_beds = 0
                available_beds = 0
                bed_occupancy_rate = 0.0

            records.append({
                "date": date_str,
                "day_of_week": dow,
                "is_weekend": is_weekend,
                "month": current_date.month,
                "day": current_date.day,
                "department": dept_name,
                "patient_arrivals": patient_arrivals,
                "appointment_count": appointment_count,
                "emergency_cases": emergency_cases,
                "available_doctors": available_doctors,
                "occupied_beds": occupied_beds,
                "available_beds": available_beds,
                "total_beds": total_beds,
                "bed_occupancy_rate": bed_occupancy_rate,
                "data_type": "synthetic_operational"
            })

    df = pd.DataFrame(records)
    return df

def save_dataset_and_metadata():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "hospital_operations.csv")
    meta_path = os.path.join(current_dir, "dataset_metadata.json")

    df = generate_operational_dataset(start_date="2026-05-15", days=184)
    df.to_csv(csv_path, index=False)
    print(f"Generated operational dataset: {len(df)} records saved to {csv_path}")

    metadata = {
        "dataset_name": "CareCoord Synthetic Hospital Operations Time-Series",
        "description": "Historical daily operational resource tracking across 7 hospital departments for machine learning forecasting. Contains no Personal Identifiable Information (PII).",
        "record_count": len(df),
        "start_date": df["date"].min(),
        "end_date": df["date"].max(),
        "departments": list(df["department"].unique()),
        "features": list(df.columns),
        "data_classification": "SYNTHETIC_OPERATIONAL",
        "is_real_hospital_data": False,
        "generation_timestamp": datetime.utcnow().isoformat(),
        "prediction_targets": [
            "patient_arrivals",
            "emergency_cases",
            "occupied_beds",
            "appointment_count"
        ]
    }

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Dataset metadata saved to {meta_path}")

if __name__ == "__main__":
    save_dataset_and_metadata()
