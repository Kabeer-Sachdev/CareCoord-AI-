import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Any

DEPARTMENT_MAPPING = {
    "Cardiology": 0,
    "Neurology": 1,
    "Orthopedics": 2,
    "General Medicine": 3,
    "Emergency Medicine": 4,
    "Pediatrics": 5,
    "Dermatology": 6
}

FEATURE_COLUMNS = [
    "dept_code",
    "day_of_week",
    "is_weekend",
    "month",
    "day",
    "total_beds",
    "arrivals_lag_1d",
    "arrivals_lag_7d",
    "arrivals_rolling_7d",
    "emergency_lag_1d",
    "emergency_lag_7d",
    "emergency_rolling_7d",
    "occupied_beds_lag_1d",
    "occupied_beds_lag_7d",
    "occupied_beds_rolling_7d",
    "appointments_lag_1d",
    "appointments_lag_7d",
    "appointments_rolling_7d"
]

class FeatureEngineer:
    @staticmethod
    def build_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        Engineers temporal, lag, rolling, and categorical features
        strictly utilizing past information to prevent data leakage.
        """
        df = df.copy()
        df = df.sort_values(by=["department", "date"]).reset_index(drop=True)

        # Department Code Encoding
        df["dept_code"] = df["department"].map(DEPARTMENT_MAPPING).fillna(0).astype(int)

        # Ensure calendar features
        if "day_of_week" not in df.columns:
            df["day_of_week"] = df["date"].dt.dayofweek
        if "is_weekend" not in df.columns:
            df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
        if "month" not in df.columns:
            df["month"] = df["date"].dt.month
        if "day" not in df.columns:
            df["day"] = df["date"].dt.day

        # Lag and Rolling Features per Department
        # Shift(1) guarantees no future data leakage
        grouped = df.groupby("department")

        # Arrivals features
        df["arrivals_lag_1d"] = grouped["patient_arrivals"].shift(1)
        df["arrivals_lag_7d"] = grouped["patient_arrivals"].shift(7)
        df["arrivals_rolling_7d"] = grouped["patient_arrivals"].shift(1).rolling(7, min_periods=1).mean()

        # Emergency features
        df["emergency_lag_1d"] = grouped["emergency_cases"].shift(1)
        df["emergency_lag_7d"] = grouped["emergency_cases"].shift(7)
        df["emergency_rolling_7d"] = grouped["emergency_cases"].shift(1).rolling(7, min_periods=1).mean()

        # Occupied Beds features
        df["occupied_beds_lag_1d"] = grouped["occupied_beds"].shift(1)
        df["occupied_beds_lag_7d"] = grouped["occupied_beds"].shift(7)
        df["occupied_beds_rolling_7d"] = grouped["occupied_beds"].shift(1).rolling(7, min_periods=1).mean()

        # Appointments features
        df["appointments_lag_1d"] = grouped["appointment_count"].shift(1)
        df["appointments_lag_7d"] = grouped["appointment_count"].shift(7)
        df["appointments_rolling_7d"] = grouped["appointment_count"].shift(1).rolling(7, min_periods=1).mean()

        # Backward fill the initial 7 days of lags per department using the first available value
        df = df.groupby("department", group_keys=False).apply(lambda group: group.bfill().ffill())

        # Sort back to chronological date order
        df = df.sort_values(by=["date", "department"]).reset_index(drop=True)
        return df

    @staticmethod
    def chronological_split(
        df: pd.DataFrame,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Splits dataset chronologically into Train (70%), Validation (15%), and Test (15%) sets.
        Avoids random splitting to maintain temporal integrity.
        """
        dates = sorted(df["date"].unique())
        n_dates = len(dates)

        train_end_idx = int(n_dates * train_ratio)
        val_end_idx = int(n_dates * (train_ratio + val_ratio))

        train_dates = dates[:train_end_idx]
        val_dates = dates[train_end_idx:val_end_idx]
        test_dates = dates[val_end_idx:]

        train_df = df[df["date"].isin(train_dates)].copy()
        val_df = df[df["date"].isin(val_dates)].copy()
        test_df = df[df["date"].isin(test_dates)].copy()

        return train_df, val_df, test_df
