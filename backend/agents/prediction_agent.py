from typing import Dict, Any, List
import time
from datetime import datetime, timedelta
from backend.agents.state import CareCoordState

class PredictionAgent:
    """
    ML Resource Demand Prediction Agent for CareCoord LangGraph Orchestration.
    Queries trained machine learning models to forecast patient arrivals,
    emergency workloads, bed occupancy, and appointment demand.
    """

    def __init__(self, name: str = "Prediction Agent"):
        self.name = name

    def process_node(self, state: CareCoordState) -> CareCoordState:
        """LangGraph node execution handler."""
        from backend.tools import prediction_tools
        state["current_agent"] = self.name
        start_time = time.time()

        parsed = state.get("workflow_request", {})
        query = (parsed.get("reason") or state.get("original_request", "")).lower()
        dept = parsed.get("department") or "Cardiology"

        # Determine target forecast date (default: tomorrow)
        forecast_dt = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")

        # Determine prediction focus
        if "bed" in query or "occupancy" in query:
            res = prediction_tools.predict_bed_occupancy(department=dept, forecast_date=forecast_dt)
            summary = (
                f"Predicted {res['predicted_occupied_beds']}/{res['total_beds']} beds occupied in {dept} "
                f"({round(res['occupancy_rate'] * 100)}% utilization, {res['estimated_available_beds']} beds available) on {res['forecast_date']}."
            )
        elif "emergency" in query or "er" in query or "trauma" in query:
            res = prediction_tools.predict_emergency_demand(department=dept, forecast_date=forecast_dt)
            summary = f"Predicted {res['predicted_value']} emergency cases in {dept} on {res['forecast_date']}."
        elif "appointment" in query or "booking" in query:
            res = prediction_tools.predict_appointment_demand(department=dept, forecast_date=forecast_dt)
            summary = f"Predicted {res['predicted_value']} appointments in {dept} on {res['forecast_date']}."
        elif "arrival" in query or "patient" in query:
            res = prediction_tools.predict_patient_arrivals(department=dept, forecast_date=forecast_dt)
            summary = f"Predicted {res['predicted_value']} patient arrivals in {dept} on {res['forecast_date']}."
        else:
            # General resource forecast
            res = prediction_tools.get_resource_forecast(department=dept, forecast_date=forecast_dt)
            summary = (
                f"Resource forecast for {dept} on {res['forecast_date']}: "
                f"Arrivals={res['predicted_arrivals']}, Emergencies={res['predicted_emergencies']}, "
                f"Occupied Beds={res['predicted_occupied_beds']}/{res.get('total_beds', 10)}."
            )

        elapsed_ms = int((time.time() - start_time) * 1000)

        state["prediction_result"] = {
            "agent": self.name,
            "status": "success",
            "summary": summary,
            "data": res
        }

        # Track execution in state
        if "executed_agents" not in state or state["executed_agents"] is None:
            state["executed_agents"] = []
        if self.name not in state["executed_agents"]:
            state["executed_agents"].append(self.name)

        # Append execution event log
        log_entry = {
            "timestamp": time.strftime("%H:%M:%S"),
            "agent_name": self.name,
            "node_name": "ml_prediction",
            "event_type": "ml_resource_forecasting",
            "status": "success",
            "tool_name": "prediction_tools.get_resource_forecast",
            "execution_time_ms": elapsed_ms,
            "details": {
                "summary": summary,
                "department": dept,
                "forecast_date": res.get("forecast_date", forecast_dt)
            }
        }
        if "execution_log" not in state or state["execution_log"] is None:
            state["execution_log"] = []
        state["execution_log"].append(log_entry)

        return state
