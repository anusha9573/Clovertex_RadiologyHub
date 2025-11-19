from datetime import date, time as time_type
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from services.api.app.db.repositories import ResourceCalendarRepo, ResourcesRepo
from services.api.app.utils.time_utils import is_within_window, parse_iso_date, parse_iso_time

router = APIRouter(tags=["resources"])


@router.get("/resources")
def list_resources():
    rows = ResourcesRepo.list_resources()
    return {"status": "ok", "resources": rows}


@router.get("/resources/on-duty")
def resources_on_duty(
    target_date: date = Query(..., description="Date to inspect (YYYY-MM-DD)"),
    target_time: Optional[time_type] = Query(
        None, description="Optional time filter (HH:MM)"
    ),
):
    date_str = parse_iso_date(target_date).isoformat()
    rows = ResourceCalendarRepo.get_on_duty(date_str)
    if target_time:
        target_time_parsed = parse_iso_time(target_time)
        rows = [
            row
            for row in rows
            if is_within_window(row["available_from"], row["available_to"], target_time_parsed)
        ]
    if not rows:
        return {
            "status": "ok",
            "resources": [],
            "filters": {"date": date_str, "time": target_time.isoformat() if target_time else None},
        }
    for row in rows:
        row["availability_window"] = f"{row['available_from']} - {row['available_to']}"
    return {
        "status": "ok",
        "resources": rows,
        "filters": {"date": date_str, "time": target_time.isoformat() if target_time else None},
    }
