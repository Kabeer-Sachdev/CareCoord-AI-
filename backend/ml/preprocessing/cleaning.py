import pandas as pd
from typing import Dict, Any

class DataCleaner:
    @staticmethod
    def clean(df: pd.DataFrame) -> pd.DataFrame:
        """
        Cleans operational time-series data:
        1. Removes exact duplicate records
        2. Fills or drops missing critical values
        3. Asserts non-negative bounds on operational metrics
        """
        df = df.copy()

        # Remove duplicate rows
        df = df.drop_duplicates(subset=["date", "department"]).reset_index(drop=True)

        # Ensure numeric fields are non-negative
        numeric_cols = [
            "patient_arrivals", "appointment_count", "emergency_cases",
            "available_doctors", "occupied_beds", "available_beds", "total_beds"
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
                df[col] = df[col].clip(lower=0)

        # Bound bed occupancy rate between 0.0 and 1.0
        if "bed_occupancy_rate" in df.columns:
            df["bed_occupancy_rate"] = df["bed_occupancy_rate"].clip(lower=0.0, upper=1.0)

        return df

    @staticmethod
    def get_summary_stats(df: pd.DataFrame) -> Dict[str, Any]:
        """Returns sanity check statistics on dataset health."""
        return {
            "total_records": len(df),
            "date_range": [str(df["date"].min().date()), str(df["date"].max().date())],
            "departments": list(df["department"].unique()),
            "missing_values": int(df.isnull().sum().sum()),
            "duplicates": int(df.duplicated(subset=["date", "department"]).sum())
        }
