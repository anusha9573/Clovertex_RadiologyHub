# services/api/app/agents/availability_checker_agent.py
from datetime import datetime

from services.api.app.agents.base_agent import BaseAgent
from services.api.app.db.repositories import ResourceCalendarRepo
from services.api.app.utils.scoring import compute_candidate_score, parse_time_window


class AvailabilityCheckerAgent(BaseAgent):
    def run(self, input_data: dict) -> dict:
        candidates = input_data.get("candidates", [])
        if not candidates:
            return {
                "work_id": input_data.get("work_id"),
                "scored_candidates": [],
                "work_type": input_data.get("work_type"),
                "priority": input_data.get("priority", 1),
                "scheduled_timestamp": input_data.get("scheduled_timestamp"),
            }

        scheduled_ts = input_data.get("scheduled_timestamp")
        if not scheduled_ts:
            raise ValueError("scheduled_timestamp missing from pipeline context")

        scheduled_dt = (
            scheduled_ts if isinstance(scheduled_ts, datetime) else datetime.fromisoformat(scheduled_ts)
        )
        scheduled_date = scheduled_dt.date().isoformat()

        priority = int(input_data.get("priority", 1))
        work_type = input_data.get("work_type")
        required_specialty = input_data.get("required_specialty")

        resource_ids = [c["resource_id"] for c in candidates]
        calendars = ResourceCalendarRepo.get_calendars_for_resources_on_date(
            resource_ids, scheduled_date
        )

        scored = []
        for candidate in candidates:
            matches = calendars.get(candidate["resource_id"], [])
            entry = self._find_matching_entry(matches, scheduled_dt)
            if not entry:
                continue
            entry_dict = entry if isinstance(entry, dict) else dict(entry)

            score_payload = compute_candidate_score(
                candidate=candidate,
                calendar_entry=entry_dict,
                scheduled_dt=scheduled_dt,
                required_specialty=required_specialty,
                priority=priority,
            )

            scored.append(
                {
                    **candidate,
                    **score_payload,
                    "calendar_id": entry_dict["calendar_id"],
                    "scheduled_timestamp": scheduled_dt.isoformat(),
                }
            )

        scored.sort(key=lambda x: x["score"], reverse=True)
        return {
            "work_id": input_data.get("work_id"),
            "scored_candidates": scored,
            "work_type": work_type,
            "priority": priority,
            "scheduled_timestamp": scheduled_dt.isoformat(),
        }

    @staticmethod
    def _find_matching_entry(entries, scheduled_dt: datetime):
        if not entries:
            return None
        scheduled_time = scheduled_dt.time()
        for entry in entries:
            start, end = parse_time_window(entry["available_from"], entry["available_to"])
            if start <= scheduled_time <= end:
                return entry
        return None
