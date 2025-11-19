from datetime import date, time

from services.api.app.agents.availability_checker_agent import AvailabilityCheckerAgent
from services.api.app.controllers.assignment_controller import AssignmentController
from services.api.app.db.repositories import ResourceCalendarRepo, WorkRequestsRepo


def test_availability_excludes_out_of_shift(sqlite_database):
    checker = AvailabilityCheckerAgent()
    result = checker.run(
        {
            "work_id": "test",
            "candidates": [
                {
                    "resource_id": "R001",
                    "name": "Dr. John Smith",
                    "specialty": "General_Radiologist",
                    "skill_level": 4,
                    "total_cases_handled": 178,
                }
            ],
            "priority": 3,
            "work_type": "CT_Scan_Chest",
            "scheduled_timestamp": "2024-11-10T05:00:00",
            "required_specialty": "General_Radiologist",
        }
    )
    assert result["scored_candidates"] == []


def test_priority_impacts_score(sqlite_database):
    checker = AvailabilityCheckerAgent()
    base_input = {
        "work_id": "test",
        "candidates": [
            {
                "resource_id": "R001",
                "name": "Dr. John Smith",
                "specialty": "General_Radiologist",
                "skill_level": 4,
                "total_cases_handled": 178,
            }
        ],
        "work_type": "CT_Scan_Chest",
        "scheduled_timestamp": "2024-11-10T09:00:00",
        "required_specialty": "General_Radiologist",
    }

    low_priority = checker.run({**base_input, "priority": 1})
    high_priority = checker.run({**base_input, "priority": 5})

    assert len(low_priority["scored_candidates"]) == 1
    assert len(high_priority["scored_candidates"]) == 1
    assert (
        high_priority["scored_candidates"][0]["score"]
        > low_priority["scored_candidates"][0]["score"]
    )


def test_assignment_updates_db_and_workload(sqlite_database):
    controller = AssignmentController()
    payload = {
        "work_type": "MRI_Brain",
        "description": "Emergency stroke protocol",
        "priority": 5,
        "scheduled_date": date(2024, 11, 10).isoformat(),
        "scheduled_time": time(9, 0).isoformat(),
    }
    add_result = controller.add_work(payload)
    work_id = add_result["work_id"]

    analysis = controller.analyzer.run({"work_id": work_id})
    found = controller.finder.run(analysis)
    scored = controller.checker.run(found)
    top = scored["scored_candidates"][0]
    calendar_id = top["calendar_id"]
    resource_id = top["resource_id"]
    date_str = payload["scheduled_date"]

    cal_entries = ResourceCalendarRepo.get_calendars_for_resources_on_date(
        [resource_id], date_str
    )
    before = next(
        entry
        for entry in cal_entries.get(resource_id, [])
        if entry["calendar_id"] == calendar_id
    )
    before_workload = before["current_workload"]

    assignment = controller.assign(work_id, llm_provider="template")

    status = WorkRequestsRepo.get_work_by_id(work_id)
    assert status["status"] == "assigned"
    assert status["assigned_to"] == assignment["assigned_to"]

    cal_entries_after = ResourceCalendarRepo.get_calendars_for_resources_on_date(
        [resource_id], date_str
    )
    after = next(
        entry
        for entry in cal_entries_after.get(resource_id, [])
        if entry["calendar_id"] == calendar_id
    )
    assert after["current_workload"] == before_workload + 1

