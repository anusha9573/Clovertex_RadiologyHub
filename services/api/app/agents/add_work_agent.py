# services/api/app/agents/add_work_agent.py
import time
from datetime import datetime, time as dt_time
from typing import Union

from services.api.app.agents.base_agent import BaseAgent
from services.api.app.db.repositories import WorkRequestsRepo


class AddWorkAgent(BaseAgent):
    def run(self, input_data: dict) -> dict:
        # Validate required fields
        for k in ("work_type", "description", "priority", "scheduled_date", "scheduled_time"):
            if k not in input_data:
                raise ValueError(f"{k} is required")
        scheduled_timestamp = self._compose_timestamp(
            input_data["scheduled_date"], input_data["scheduled_time"]
        )
        # Create deterministic id for reproducibility (timestamp + random small int)
        work_id = f"W{int(time.time() * 1000)}"
        record = {
            "work_id": work_id,
            "work_type": input_data["work_type"],
            "description": input_data["description"],
            "priority": int(input_data["priority"]),
            "scheduled_timestamp": scheduled_timestamp,
            "status": "pending",
            "assigned_to": None,
        }
        WorkRequestsRepo.create_work_request(record)
        serialized = {**record, "scheduled_timestamp": scheduled_timestamp.isoformat()}
        return {"work_id": work_id, **serialized}

    @staticmethod
    def _compose_timestamp(
        scheduled_date: Union[str, datetime],
        scheduled_time: Union[str, dt_time],
    ) -> datetime:
        if isinstance(scheduled_date, datetime):
            base_date = scheduled_date.date()
        else:
            base_date = datetime.strptime(str(scheduled_date), "%Y-%m-%d").date()

        if isinstance(scheduled_time, dt_time):
            t = scheduled_time
        else:
            try:
                t = datetime.strptime(str(scheduled_time), "%H:%M:%S").time()
            except ValueError:
                t = datetime.strptime(str(scheduled_time), "%H:%M").time()

        return datetime.combine(base_date, t)
