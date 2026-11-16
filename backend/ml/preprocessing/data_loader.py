import os
import pandas as pd
from typing import Optional

def load_operational_data(csv_path: Optional[str] = None) -> pd.DataFrame:
    """
    Loads historical operational hospital records from CSV.
    If the file does not exist, generates it using generate_dataset.
    """
    if csv_path is None:
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        csv_path = os.path.join(current_dir, "datasets", "hospital_operations.csv")

    if not os.path.exists(csv_path):
        from backend.ml.datasets.generate_dataset import save_dataset_and_metadata
        save_dataset_and_metadata()

    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(by=["date", "department"]).reset_index(drop=True)
    return df
