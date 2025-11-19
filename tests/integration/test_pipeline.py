from datetime import date, time

from services.api.app.controllers.assignment_controller import AssignmentController


def test_full_pipeline_assignment(sqlite_database):
    controller = AssignmentController()
    add_result = controller.add_work(
        {
            "work_type": "MRI_Brain",
            "description": "Acute neuro case",
            "priority": 5,
            "scheduled_date": date.today().isoformat(),
            "scheduled_time": time(9, 30).isoformat(),
        }
    )
    work_id = add_result["work_id"]

    assignment = controller.assign(work_id, llm_provider="template")
    assert assignment["assigned_to"] is not None
    status = controller.fetch_status(work_id)
    assert status["status"] == "assigned"
    assert status["assigned_to"] == assignment["assigned_to"]

