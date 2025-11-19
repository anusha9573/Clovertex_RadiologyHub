from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Dict, Optional


def parse_time_window(start_str: str, end_str: str) -> tuple[time, time]:
    start = _parse_time(start_str)
    end = _parse_time(end_str)
    return start, end


def _parse_time(value: str) -> time:
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(value, fmt).time()
        except ValueError:
            continue
    raise ValueError(f"Unable to parse time value: {value}")


def _role_match_score(candidate_specialty: Optional[str], required_specialty: Optional[str]) -> float:
    if not candidate_specialty or not required_specialty:
        return 0.0
    if candidate_specialty == required_specialty:
        return 1.0
    if required_specialty != "General_Radiologist" and candidate_specialty == "General_Radiologist":
        return 0.5
    return 0.4


def _skill_score(skill_level: Optional[int]) -> float:
    if not skill_level:
        return 0.0
    return max(0.0, min(skill_level, 5)) / 5.0


def _experience_score(total_cases: Optional[int]) -> float:
    if not total_cases:
        return 0.0
    return min(total_cases, 400) / 400.0


def _availability_score(start: time, end: time, scheduled_t: time) -> float:
    if start <= scheduled_t <= end:
        span = datetime.combine(datetime.today(), end) - datetime.combine(datetime.today(), start)
        hours = span.total_seconds() / 3600.0
        return min(1.0, max(0.5, hours / 12.0))
    return 0.0


def _workload_score(current_workload: Optional[int]) -> float:
    if current_workload is None:
        return 0.8
    return max(0.0, 1.0 - min(current_workload, 12) / 12.0)


def compute_candidate_score(
    candidate: Dict,
    calendar_entry: Dict,
    scheduled_dt: datetime,
    required_specialty: Optional[str],
    priority: int,
) -> Dict:
    role = _role_match_score(candidate.get("specialty"), required_specialty)
    skill = _skill_score(candidate.get("skill_level"))
    experience = _experience_score(candidate.get("total_cases_handled"))
    start_time, end_time = parse_time_window(
        calendar_entry["available_from"], calendar_entry["available_to"]
    )
    availability = _availability_score(start_time, end_time, scheduled_dt.time())
    workload = _workload_score(calendar_entry.get("current_workload"))
    priority_bonus = 0.15 * max(1, min(priority, 5)) / 5.0

    score = (
        0.25 * role
        + 0.20 * skill
        + 0.20 * experience
        + 0.20 * availability
        + 0.15 * workload
        + priority_bonus
    )

    return {
        "score": round(score, 4),
        "breakdown": {
            "role": round(role, 4),
            "skill": round(skill, 4),
            "experience": round(experience, 4),
            "availability": round(availability, 4),
            "workload": round(workload, 4),
            "priority_bonus": round(priority_bonus, 4),
        },
        "availability_window": f"{calendar_entry['available_from']} - {calendar_entry['available_to']}",
        "current_workload": calendar_entry.get("current_workload"),
    }

